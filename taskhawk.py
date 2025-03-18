import os
import time
import requests
import json
import argparse
import logging
import yaml
import subprocess
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("monitor.log"), 
                              logging.StreamHandler()])
logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    "monitor": {
        "project_name": "深度学习训练",
        "check_interval": 5,
        "timeout": None,
        "logprint": 60,
        
        # 文件检查
        "check_file_enabled": True,
        "check_file_path": "./output/model_final.pth",
        
        # 日志检查
        "check_log_enabled": False,
        "check_log_path": "./logs/training.log",
        "check_log_markers": ["Training completed", "任务完成"],
        
        # GPU功耗检查
        "check_gpu_power_enabled": False,
        "check_gpu_power_threshold": 50.0,
        "check_gpu_power_gpu_ids": "all",
        "check_gpu_power_consecutive_checks": 3
    },
    
    "webhook": {
        "enabled": True,
        "url": "",
        "title": "🎉 深度学习训练完成通知",
        "color": "green",
        "include_project_name": True,
        "include_project_name_title":"训练项目",

        "include_start_time": True,
        "include_start_time_title":"训练开始",

        "include_end_time": True,
        "include_end_time_title": "训练结束时间",

        "include_method": True,
        "include_method_title":"系统判断依据",

        "include_duration": True,
        "include_duration_title":"总耗时",

        "include_hostname": True,
        "include_hostname_title":"主机名",

        "include_gpu_info": True,
        "include_gpu_info_title":"GPU信息",

        "footer": "此消息由自动监控系统发送"
    }
}

class TrainingMonitor:
    def __init__(self, config_path=None):
        """
        初始化任务监控器
        
        Args:
            config_path (str, optional): 配置文件路径
        """
        # 加载配置，如果没有指定配置文件，使用默认配置
        self.config = self._load_config(config_path) if config_path else DEFAULT_CONFIG
        self.start_time = datetime.now()
        self.low_power_count = 0
        
    def _load_config(self, config_path):
        """
        加载配置文件，并与默认配置合并
        
        Args:
            config_path (str): 配置文件路径
            
        Returns:
            dict: 配置参数
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                user_config = yaml.safe_load(file)
                logger.info("成功加载配置文件")
                
                # 合并配置，确保所有必需的参数都存在
                config = DEFAULT_CONFIG.copy()
                
                # 更新监控配置
                if user_config.get('monitor'):
                    config['monitor'].update(user_config['monitor'])
                
                # 更新webhook配置
                if user_config.get('webhook'):
                    config['webhook'].update(user_config['webhook'])
                
                return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            logger.info("使用默认配置")
            return DEFAULT_CONFIG
        
    def is_training_complete(self):
        """
        检查任务是否完成
        
        Returns:
            bool: 任务是否完成
        """
        # 方法1: 检查特定文件是否存在
        if self.config['monitor']['check_file_enabled']:
            file_path = self.config['monitor']['check_file_path']
            if os.path.exists(file_path):
                logger.info(f"找到指定文件: {file_path}")
                return True, "目标文件检测"
                
        # 方法2: 检查日志文件中是否包含完成标记
        if self.config['monitor']['check_log_enabled']:
            log_path = self.config['monitor']['check_log_path']
            markers = self.config['monitor']['check_log_markers']
            
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for marker in markers:
                            if marker in content:
                                logger.info(f"在日志中发现完成标记: {marker}")
                                return True ,"日志检测"
                except Exception as e:
                    logger.error(f"读取日志文件失败: {str(e)}")
                            
        # 方法3: 检查GPU功耗是否低于阈值
        if self.config['monitor']['check_gpu_power_enabled']:
            threshold = self.config['monitor']['check_gpu_power_threshold']
            gpu_ids = self.config['monitor']['check_gpu_power_gpu_ids']
            consecutive_checks = self.config['monitor']['check_gpu_power_consecutive_checks']
            overtime = self.config['monitor']['check_interval']
            
            if self._check_gpu_power_below_threshold(threshold, gpu_ids):
                self.low_power_count += 1
                logger.info(f"GPU功耗低于阈值次数: [{self.low_power_count}/{consecutive_checks}]")
                if self.low_power_count >= consecutive_checks:
                    logger.info(f"GPU功耗已连续{consecutive_checks}次低于阈值{threshold}W，判定任务完成")
                    return True ,f"GPU功耗检测"
            else:
                # 重置计数器
                self.low_power_count = 0
                
        return False, "未完成任务"
    
    def _check_gpu_power_below_threshold(self, threshold, gpu_ids):
        """
        检查GPU功耗是否低于阈值
        
        Args:
            threshold (float): 功耗阈值(瓦特)
            gpu_ids (str): GPU ID，'all'表示所有GPU
            
        Returns:
            bool: 是否所有指定GPU的功耗都低于阈值
        """
        try:
            # 使用nvidia-smi获取GPU功耗信息
            output = subprocess.check_output(
                ['nvidia-smi', '--query-gpu=index,power.draw', '--format=csv,noheader,nounits'],
                universal_newlines=True
            )
            
            # 解析输出
            gpu_power_info = {}
            for line in output.strip().split('\n'):
                if ',' in line:  # 确保行格式正确
                    idx, power = line.split(',')
                    gpu_power_info[int(idx.strip())] = float(power.strip())
                
            logger.debug(f"当前GPU功耗: {gpu_power_info}")
            
            # 确定要检查的GPU列表
            if gpu_ids == 'all':
                check_gpus = list(gpu_power_info.keys())
            else:
                if isinstance(gpu_ids, list):
                    check_gpus = [int(gid) for gid in gpu_ids]
                else:
                    check_gpus = [int(gpu_ids)]
            
            # 检查所有指定GPU的功耗是否都低于阈值
            for gpu_id in check_gpus:
                if gpu_id in gpu_power_info:
                    power = gpu_power_info[gpu_id]
                    if power >= threshold:
                        logger.debug(f"GPU {gpu_id} 功耗 {power}W 高于阈值 {threshold}W")
                        return False
                        
            # 所有GPU功耗都低于阈值
            return True
            
        except Exception as e:
            logger.error(f"检查GPU功耗失败: {str(e)}")
            return False
        
    def send_notification(self, training_info):
        """
        发送通知到飞书
        
        Args:
            training_info (dict): 任务信息
        
        Returns:
            bool: 发送是否成功
        """
        # 如果webhook未启用或URL为空，则跳过
        if not self.config['webhook']['enabled'] or not self.config['webhook']['url']:
            logger.info("Webhook通知已禁用或URL为空")
            return False
            
        # 构建内容项
        content_items = []
        if self.config['webhook']['include_project_name']:
            content_items.append(f"- {training_info['project_name_title']}: {training_info['project_name']}")
        if self.config['webhook']['include_start_time']:
            content_items.append(f"- {training_info['start_time_title']}: {training_info['start_time']}")
        if self.config['webhook']['include_end_time']:
            content_items.append(f"- {training_info['end_time_title']}: {training_info['end_time']}")
        if self.config['webhook']['include_method']:
            content_items.append(f"- {training_info['method_title']}: {training_info['method']}")
        if self.config['webhook']['include_duration']:
            content_items.append(f"- {training_info['duration_title']}: {training_info['duration']}")
        if self.config['webhook']['include_hostname']:
            content_items.append(f"- {training_info['hostname_title']}: {training_info['hostname']}")
        if self.config['webhook']['include_gpu_info']:
            content_items.append(f"- {training_info['gpu_info_title']}: {training_info['gpu_info']}")
        
        # 确保至少有一个内容项
        if not content_items:
            content_items.append(f"- 任务项目: {training_info['project_name']}")
            content_items.append(f"- 总耗时: {training_info['duration']}")
        
        content = "**模型任务已完成！**\n\n" + "\n".join(content_items)
        
        # 构建飞书消息
        message = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": self.config['webhook']['title']
                    },
                    "template": self.config['webhook']['color']
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": content
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": self.config['webhook']['footer']
                            }
                        ]
                    }
                ]
            }
        }
        
        try:
            response = requests.post(
                self.config['webhook']['url'],
                headers={"Content-Type": "application/json"},
                data=json.dumps(message)
            )
            
            if response.status_code == 200:
                logger.info("成功发送通知到飞书")
                return True
            else:
                logger.error(f"发送通知失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"发送通知时发生异常: {str(e)}")
            return False
            
    def get_gpu_info(self):
        """
        获取GPU信息
        
        Returns:
            str: GPU信息描述
        """
        try:
            output = subprocess.check_output(
                ['nvidia-smi', '--query-gpu=name,memory.used,memory.total', '--format=csv,noheader'],
                universal_newlines=True
            )
            #return output.strip().replace('\n', '; ')
            gpu_list = output.strip().split('\n')
            formatted_info = []
            for gpu in gpu_list:
                name, mem_used, mem_total = gpu.split(',')
                formatted_info.append(f" {name} | 已用显存: {mem_used} MiB / {mem_total} MiB")
            return ";".join(formatted_info)
        except Exception as e:
            logger.error(f"获取GPU信息失败: {str(e)}")
            return "无法获取GPU信息"
            
    def start_monitoring(self):
        """
        开始监控任务进程
        """
        project_name = self.config['monitor']['project_name']
        check_interval = self.config['monitor']['check_interval']
        logprint = self.config['monitor']['logprint']
        timeout = self.config['monitor']['timeout']

        project_name_title = self.config['webhook']['include_project_name_title']
        start_time_title = self.config['webhook']['include_start_time_title']
        end_time_title = self.config['webhook']['include_end_time_title']
        method_title = self.config['webhook']['include_method_title']
        duration_title = self.config['webhook']['include_duration_title']
        hostname_title = self.config['webhook']['include_hostname_title']
        gpu_info_title = self.config['webhook']['include_gpu_info_title']
        
        logger.info(f"开始监控任务进程: {project_name}")
        
        elapsed_time = 0
        while True:
            flag, method = self.is_training_complete()
            if flag:
                end_time = datetime.now()
                duration = end_time - self.start_time
                
                # 准备任务信息
                training_info = {
                    "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "duration": str(duration).split('.')[0],  # 格式化为 HH:MM:SS
                    "project_name": project_name,
                    "hostname": os.uname().nodename if hasattr(os, 'uname') else os.environ.get('COMPUTERNAME', 'Unknown'),
                    "gpu_info": self.get_gpu_info(),
                    "method": method,

                    "project_name_title": project_name_title,
                    "start_time_title": start_time_title,
                    "end_time_title": end_time_title,
                    "method_title": method_title,
                    "duration_title": duration_title,
                    "hostname_title": hostname_title,
                    "gpu_info_title": gpu_info_title,
                }
                
                logger.info(f"任务已完成！总耗时: {training_info['duration']}")
                self.send_notification(training_info)
                break
                
            time.sleep(check_interval)
            elapsed_time += check_interval
            
            # 如果设置了超时且已超时，则退出
            if timeout and elapsed_time >= timeout:
                logger.warning(f"监控超时，已等待 {elapsed_time} 秒")
                break
                
            # 定期输出监控状态
            if elapsed_time % logprint == 0:
                logger.info(f"监控仍在进行中，已等待 {elapsed_time} 秒")

def main():
    parser = argparse.ArgumentParser(description="深度学习任务监控和通知系统")
    parser.add_argument("--config", help="配置文件路径")
    
    args = parser.parse_args()
    
    monitor = TrainingMonitor(config_path=args.config)
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
