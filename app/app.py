from flask import Flask, render_template, request, jsonify, send_file
from flask_sock import Sock
import yaml
import os
import json
import sys
import threading
import queue
import logging
from datetime import datetime
from importlib.util import spec_from_file_location, module_from_spec

app = Flask(__name__)
sock = Sock(app)

# 配置文件路径
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'configs')
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, 'default.yaml')
MAIN_SCRIPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'main.py')
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')

# 确保必要的目录存在
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 全局变量
monitor_thread = None
monitor_stop_event = threading.Event()
log_queue = queue.Queue()
clients = set()

class WebSocketHandler(logging.Handler):
    def emit(self, record):
        try:
            log_entry = self.format(record)
            log_queue.put(log_entry)
        except Exception:
            self.handleError(record)

# 配置日志处理
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# WebSocket处理器
ws_handler = WebSocketHandler()
ws_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(ws_handler)

# 文件处理器
file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'webui.log'), encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

def load_config(config_path=DEFAULT_CONFIG_PATH):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        return None

def save_config(config_data, filename):
    """保存配置到文件"""
    file_path = os.path.join(CONFIG_DIR, filename)
    try:
        # 保存到指定文件
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True)
            
        # 同时更新主配置文件
        with open(DEFAULT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True)
            
        logger.info(f"配置已保存到: {filename}")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return False

def validate_config(config_data):
    """验证配置数据的类型"""
    try:
        monitor = config_data.get('monitor', {})
        
        # 验证并转换数值类型
        if 'check_interval' in monitor:
            monitor['check_interval'] = int(monitor['check_interval'])
        if 'logprint' in monitor:
            monitor['logprint'] = int(monitor['logprint'])
        if 'timeout' in monitor and monitor['timeout'] is not None:
            monitor['timeout'] = int(monitor['timeout'])
        if 'check_gpu_power_threshold' in monitor:
            monitor['check_gpu_power_threshold'] = float(monitor['check_gpu_power_threshold'])
        if 'check_gpu_power_consecutive_checks' in monitor:
            monitor['check_gpu_power_consecutive_checks'] = int(monitor['check_gpu_power_consecutive_checks'])
            
        return True
    except (ValueError, TypeError) as e:
        return False

def broadcast_message(message_type, data):
    """广播消息给所有WebSocket客户端"""
    message = json.dumps({
        'type': message_type,
        'data': data
    })
    dead_clients = set()
    
    for client in clients:
        try:
            client.send(message)
        except Exception:
            dead_clients.add(client)
    
    # 移除断开的客户端
    clients.difference_update(dead_clients)

def run_monitor():
    """运行监控程序"""
    try:
        # 动态导入main.py
        spec = spec_from_file_location("monitor_main", MAIN_SCRIPT_PATH)
        module = module_from_spec(spec)
        sys.modules["monitor_main"] = module
        spec.loader.exec_module(module)
        
        # 加载当前配置
        config = load_config()
        if not config:
            logger.error("无法加载配置文件")
            return
        
        # 创建监控器实例
        monitor = module.TrainingMonitor(config_path=DEFAULT_CONFIG_PATH)
        
        # 设置停止事件检查
        def check_stop():
            return monitor_stop_event.is_set()
        
        # 注入停止检查函数
        monitor.should_stop = check_stop
        
        # 开始监控
        logger.info("开始监控任务...")
        monitor.start_monitoring()
        
    except Exception as e:
        logger.error(f"监控程序出错: {str(e)}")
    finally:
        monitor_stop_event.clear()
        broadcast_message('status', {'status': 'stopped'})

@app.route('/')
def index():
    """主页路由"""
    config = load_config()
    # 检查监控状态
    status = 'running' if (monitor_thread and monitor_thread.is_alive()) else 'stopped'
    return render_template('index.html', config=config, initial_status=status)

@sock.route('/ws')
def handle_websocket(ws):
    """处理WebSocket连接"""
    clients.add(ws)
    try:
        # 发送初始状态（只在连接建立时发送一次）
        status = 'running' if (monitor_thread and monitor_thread.is_alive()) else 'stopped'
        ws.send(json.dumps({
            'type': 'status',
            'data': {'status': status}
        }))
        
        while True:
            # 从日志队列获取消息并发送
            try:
                while True:
                    log_message = log_queue.get_nowait()
                    if isinstance(log_message, dict) and log_message.get('type') == 'status':
                        # 状态变更消息
                        ws.send(json.dumps(log_message))
                    else:
                        # 普通日志消息
                        ws.send(json.dumps({
                            'type': 'log',
                            'message': log_message
                        }))
            except queue.Empty:
                pass
            
            # 等待一小段时间
            ws.sleep(0.1)
    except Exception:
        pass
    finally:
        clients.remove(ws)

def broadcast_status_change(status):
    """广播状态变更消息"""
    message = {
        'type': 'status',
        'data': {'status': status}
    }
    log_queue.put(message)

@app.route('/api/monitor/start', methods=['POST'])
def start_monitor():
    """启动监控"""
    global monitor_thread
    
    if monitor_thread and monitor_thread.is_alive():
        return jsonify({
            'status': 'error',
            'message': '监控程序已在运行'
        }), 400
    
    try:
        # 确保配置文件存在
        if not os.path.exists(DEFAULT_CONFIG_PATH):
            return jsonify({
                'status': 'error',
                'message': '配置文件不存在'
            }), 400
            
        monitor_stop_event.clear()
        monitor_thread = threading.Thread(target=run_monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 广播状态变更
        broadcast_status_change('running')
        logger.info("监控程序已启动")
        
        return jsonify({
            'status': 'success',
            'message': '监控程序已启动'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/monitor/stop', methods=['POST'])
def stop_monitor():
    """停止监控"""
    global monitor_thread
    
    if not monitor_thread or not monitor_thread.is_alive():
        return jsonify({
            'status': 'error',
            'message': '监控程序未在运行'
        }), 400
    
    try:
        monitor_stop_event.set()
        monitor_thread.join(timeout=5)
        
        if monitor_thread.is_alive():
            return jsonify({
                'status': 'error',
                'message': '停止监控程序失败'
            }), 500
        
        monitor_thread = None
        # 广播状态变更
        broadcast_status_change('stopped')
        logger.info("监控程序已停止")
        
        return jsonify({
            'status': 'success',
            'message': '监控程序已停止'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置API"""
    config = load_config()
    return jsonify(config)

@app.route('/api/config/save', methods=['POST'])
def save_config_api():
    """保存配置API"""
    try:
        data = request.json
        config_name = data.get('name', '').strip()
        config_data = data.get('config', {})
        
        if not config_name:
            return jsonify({
                'status': 'error',
                'message': '配置名称不能为空'
            }), 400
            
        # 验证配置数据类型
        if not validate_config(config_data):
            return jsonify({
                'status': 'error',
                'message': '配置数据类型无效'
            }), 400
            
        # 清理文件名，移除不安全字符
        safe_name = "".join(c for c in config_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            return jsonify({
                'status': 'error',
                'message': '配置名称包含无效字符'
            }), 400
            
        # 添加时间戳后缀以避免重名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_name}_{timestamp}.yaml"
        
        if save_config(config_data, filename):
            # 同时更新主配置文件
            with open(DEFAULT_CONFIG_PATH, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True)
            
            return jsonify({
                'status': 'success',
                'message': '配置已保存',
                'filename': filename
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '保存配置失败'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/configs', methods=['GET'])
def list_configs():
    """列出所有保存的配置"""
    configs = []
    for filename in os.listdir(CONFIG_DIR):
        if filename.endswith('.yaml'):
            configs.append(filename)
    return jsonify(configs)

@app.route('/api/config/load/<filename>', methods=['GET'])
def load_saved_config(filename):
    """加载保存的配置"""
    try:
        config_path = os.path.join(CONFIG_DIR, filename)
        config = load_config(config_path)
        if config:
            # 加载后同时更新主配置文件
            with open(DEFAULT_CONFIG_PATH, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
            logger.info(f"已加载配置: {filename}")
            return jsonify({
                'status': 'success',
                'config': config
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '无法加载配置文件'
            }), 404
    except Exception as e:
        logger.error(f"加载配置失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/config/apply', methods=['POST'])
def apply_config():
    """应用当前配置"""
    try:
        data = request.json
        config_data = data.get('config', {})
        
        # 验证配置数据类型
        if not validate_config(config_data):
            return jsonify({
                'status': 'error',
                'message': '配置数据类型无效'
            }), 400
            
        # 更新主配置文件
        with open(DEFAULT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True)
            
        logger.info("已应用新配置")
        return jsonify({
            'status': 'success',
            'message': '配置已应用'
        })
    except Exception as e:
        logger.error(f"应用配置失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 