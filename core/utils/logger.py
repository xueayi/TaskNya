# -*- coding: utf-8 -*-
"""
日志配置模块

提供统一的日志配置功能。
"""

import os
import logging
from typing import Optional


def setup_logger(
    name: str = None,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_format: str = '%(asctime)s - %(levelname)s - %(message)s'
) -> logging.Logger:
    """
    设置并返回一个配置好的 logger
    
    Args:
        name: logger 名称，默认为 root logger
        level: 日志级别
        log_file: 日志文件路径，如果提供则同时输出到文件
        log_format: 日志格式
        
    Returns:
        配置好的 logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 移除已有的处理器，避免重复
    logger.handlers.clear()
    
    formatter = logging.Formatter(log_format)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了日志文件）
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_default_log_path(filename: str = 'monitor.log') -> str:
    """
    获取默认日志文件路径
    
    Args:
        filename: 日志文件名
        
    Returns:
        完整的日志文件路径
    """
    # 项目根目录下的 logs 文件夹
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, filename)
