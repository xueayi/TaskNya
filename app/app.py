# -*- coding: utf-8 -*-
"""
TaskNya Flask Web 应用

提供 Web 界面和 API 接口。
"""

import os
import sys
import threading
import logging
from importlib.util import spec_from_file_location, module_from_spec

from flask import Flask, render_template
from flask_sock import Sock

# 确保能导入项目模块（必须在导入本地模块之前）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 现在可以安全导入本地模块
from core.config import ConfigManager

# 路径配置
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'configs')
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, 'default.yaml')
MAIN_SCRIPT_PATH = os.path.join(PROJECT_ROOT, 'main.py')
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')

# 确保必要目录存在
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


class MonitorState:
    """
    监控状态管理器
    
    管理监控线程的生命周期和状态。
    """
    
    def __init__(self, ws_manager):
        """
        初始化监控状态管理器
        
        Args:
            ws_manager: WebSocket 管理器实例
        """
        self.thread = None
        self.stop_event = threading.Event()
        self.ws_manager = ws_manager
        self._lock = threading.Lock()
    
    def is_running(self) -> bool:
        """检查监控是否正在运行"""
        with self._lock:
            return self.thread is not None and self.thread.is_alive()
    
    def start(self):
        """启动监控"""
        with self._lock:
            if self.thread and self.thread.is_alive():
                return False
            
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run_monitor)
            self.thread.daemon = True
            self.thread.start()
            
            # 广播状态变更
            self.ws_manager.broadcast_status('running')
            return True
    
    def stop(self, timeout: float = 5.0) -> bool:
        """
        停止监控
        
        Args:
            timeout: 等待超时时间
            
        Returns:
            是否成功停止
        """
        with self._lock:
            if not self.thread or not self.thread.is_alive():
                return True
            
            self.stop_event.set()
        
        self.thread.join(timeout=timeout)
        
        with self._lock:
            if self.thread.is_alive():
                return False
            
            self.thread = None
            self.ws_manager.broadcast_status('stopped')
            return True
    
    def _run_monitor(self):
        """运行监控程序"""
        logger = logging.getLogger(__name__)
        
        try:
            # 动态导入 main.py
            spec = spec_from_file_location("monitor_main", MAIN_SCRIPT_PATH)
            module = module_from_spec(spec)
            sys.modules["monitor_main"] = module
            spec.loader.exec_module(module)
            
            # 创建监控器实例
            monitor = module.TrainingMonitor(config_path=DEFAULT_CONFIG_PATH)
            
            # 注入停止检查函数
            monitor.should_stop = lambda: self.stop_event.is_set()
            
            logger.info("开始监控任务...")
            monitor.start_monitoring()
            
        except Exception as e:
            logger.error(f"监控程序出错: {str(e)}")
        finally:
            self.stop_event.clear()
            self.ws_manager.broadcast_status('stopped')


def create_app():
    """
    创建并配置 Flask 应用
    
    Returns:
        配置好的 Flask 应用实例
    """
    # 在函数内部导入，避免循环导入
    from app.routes import config_bp, monitor_bp
    from app.routes.monitor_routes import init_monitor_state
    from app.websocket import WebSocketManager
    
    app = Flask(__name__)
    sock = Sock(app)
    
    # 创建 WebSocket 管理器
    ws_manager = WebSocketManager()
    
    # 配置日志
    _setup_logging(ws_manager)
    
    # 创建监控状态管理器
    monitor_state = MonitorState(ws_manager)
    
    # 初始化路由模块的监控状态
    init_monitor_state(monitor_state)
    
    # 注册蓝图
    app.register_blueprint(config_bp)
    app.register_blueprint(monitor_bp)
    
    # 配置管理器
    config_manager = ConfigManager(config_dir=CONFIG_DIR)
    
    # 主页路由
    @app.route('/')
    def index():
        """主页路由"""
        config = config_manager.load_config()
        status = 'running' if monitor_state.is_running() else 'stopped'
        return render_template('index.html', config=config, initial_status=status)
    
    # WebSocket 路由
    @sock.route('/ws')
    def handle_websocket(ws):
        """处理 WebSocket 连接"""
        ws_manager.handle_connection(
            ws, 
            lambda: 'running' if monitor_state.is_running() else 'stopped'
        )
    
    # 存储到 app 上下文
    app.ws_manager = ws_manager
    app.monitor_state = monitor_state
    app.config_manager = config_manager
    
    return app


def _setup_logging(ws_manager):
    """
    配置日志系统
    
    Args:
        ws_manager: WebSocket 管理器
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除已有处理器
    logger.handlers.clear()
    
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # WebSocket 处理器
    ws_handler = ws_manager.get_log_handler()
    logger.addHandler(ws_handler)
    
    # 文件处理器
    log_file = os.path.join(LOG_DIR, 'webui.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    app.run(debug=True, port=5000)