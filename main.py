# -*- coding: utf-8 -*-
"""
TaskNya 监控程序主入口

提供命令行接口和向后兼容的 TrainingMonitor 类。
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime

# 确保能够导入 core 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import ConfigManager, DEFAULT_CONFIG
from core.monitor import MonitorManager
from core.notifier import WebhookNotifier, MessageBuilder
from core.utils import get_gpu_info, setup_logger
from core.utils.logger import get_default_log_path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_default_log_path('monitor.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TrainingMonitor:
    """
    任务监控器
    
    用于监控深度学习训练等长时间运行的任务，
    支持文件检测、日志检测、GPU功耗检测等多种触发条件。
    
    这是一个向后兼容的门面类，内部使用重构后的模块化组件。
    
    Attributes:
        config (dict): 配置字典
        start_time (datetime): 监控开始时间
        should_stop (callable): 停止检查回调函数
    
    Example:
        >>> monitor = TrainingMonitor(config_path='config.yaml')
        >>> monitor.start_monitoring()
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化任务监控器
        
        Args:
            config_path (str, optional): 配置文件路径。
                如果不提供，将使用默认配置。
        """
        # 加载配置
        self._config_manager = ConfigManager()
        self.config = self._config_manager.load_config(config_path)
        
        # 初始化组件
        self._monitor_manager = MonitorManager(self.config)
        self._notifier = WebhookNotifier(self.config.get('webhook', {}))
        self._message_builder = MessageBuilder(self.config.get('webhook', {}))
        
        # 状态
        self.start_time = datetime.now()
        self.should_stop = lambda: False  # 默认的停止检查函数
        
        # 为向后兼容保留的属性
        self.low_power_count = 0
        self.last_log_position = 0
    
    def _load_config(self, config_path: str) -> dict:
        """
        加载配置文件（向后兼容方法）
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        return self._config_manager.load_config(config_path)
    
    def is_training_complete(self):
        """
        检查任务是否完成
        
        Returns:
            tuple: (是否完成, 触发方式, 详情)
        """
        return self._monitor_manager.check()
    
    def _check_gpu_power_below_threshold(self, threshold: float, gpu_ids) -> bool:
        """
        检查GPU功耗是否低于阈值（向后兼容方法）
        
        Args:
            threshold: 功耗阈值
            gpu_ids: GPU ID
            
        Returns:
            是否低于阈值
        """
        gpu_monitor = self._monitor_manager.get_monitor("GPU功耗监控")
        if gpu_monitor:
            return gpu_monitor._check_power_below_threshold()
        return False
    
    def send_notification(self, training_info: dict) -> bool:
        """
        发送通知
        
        Args:
            training_info: 任务信息
            
        Returns:
            是否发送成功
        """
        return self._notifier.send(training_info)
    
    def get_gpu_info(self) -> str:
        """
        获取GPU信息
        
        Returns:
            GPU信息字符串
        """
        return get_gpu_info()
    
    def start_monitoring(self):
        """
        开始监控任务进程
        
        这是主监控循环，会阻塞直到任务完成、超时或被停止。
        """
        project_name = self.config['monitor']['project_name']
        check_interval = self.config['monitor']['check_interval']
        logprint = self.config['monitor']['logprint']
        timeout = self.config['monitor']['timeout']
        
        logger.info(f"开始监控任务进程: {project_name}")
        
        elapsed_time = 0
        while not self.should_stop():
            flag, method, detail = self.is_training_complete()
            
            if flag:
                end_time = datetime.now()
                
                # 准备任务信息
                training_info = self._message_builder.build_training_info(
                    start_time=self.start_time,
                    end_time=end_time,
                    project_name=project_name,
                    method=method,
                    detail=detail,
                    gpu_info=self.get_gpu_info() if self._should_include_gpu_info(method) else None
                )
                
                logger.info(f"任务已完成！总耗时: {training_info['duration']}")
                self.send_notification(training_info)
                break
            
            time.sleep(check_interval)
            elapsed_time += check_interval
            
            # 超时检查
            if timeout and elapsed_time >= timeout:
                logger.warning(f"监控超时，已等待 {elapsed_time} 秒")
                break
            
            # 定期输出状态
            if elapsed_time % logprint == 0:
                logger.info(f"监控仍在进行中，已等待 {elapsed_time} 秒")
                self._log_monitor_status()
    
    def _should_include_gpu_info(self, method: str) -> bool:
        """
        判断是否需要包含GPU信息
        
        Args:
            method: 触发方式
            
        Returns:
            是否包含GPU信息
        """
        return (method == "GPU功耗检测" or 
                self.config['monitor'].get('check_gpu_power_enabled', False))
    
    def _log_monitor_status(self):
        """输出当前监控状态到日志"""
        if self.config['monitor'].get('check_log_enabled', False):
            log_mode = self.config['monitor'].get('check_log_mode', 'full')
            mode_str = "全量检测" if log_mode == 'full' else "增量检测"
            logger.info(f"日志检测模式: {mode_str}")


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description="TaskNya - 任务监控和通知系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 使用默认配置
  python main.py --config my.yaml   # 使用自定义配置
        """
    )
    parser.add_argument(
        "--config", 
        help="配置文件路径（YAML格式）",
        default=None
    )
    
    args = parser.parse_args()
    
    monitor = TrainingMonitor(config_path=args.config)
    monitor.start_monitoring()


if __name__ == "__main__":
    main()
