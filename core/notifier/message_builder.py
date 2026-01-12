# -*- coding: utf-8 -*-
"""
消息构建器模块

根据配置和任务信息构建通知消息。
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime


class MessageBuilder:
    """
    消息构建器
    
    根据 webhook 配置和任务信息构建通知消息内容。
    """
    
    def __init__(self, webhook_config: Dict[str, Any]):
        """
        初始化消息构建器
        
        Args:
            webhook_config: webhook 配置字典
        """
        self.config = webhook_config
    
    def build_training_info(self, 
                            start_time: datetime,
                            end_time: datetime,
                            project_name: str,
                            method: str,
                            detail: Optional[str] = None,
                            gpu_info: Optional[str] = None) -> Dict[str, Any]:
        """
        构建任务信息字典
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            project_name: 项目名称
            method: 触发方式
            detail: 触发详情
            gpu_info: GPU 信息
            
        Returns:
            任务信息字典
        """
        duration = end_time - start_time
        
        # 获取主机名
        if hasattr(os, 'uname'):
            hostname = os.uname().nodename
        else:
            hostname = os.environ.get('COMPUTERNAME', 'Unknown')
        
        training_info = {
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": str(duration).split('.')[0],
            "project_name": project_name,
            "hostname": hostname,
            "method": method,
            
            # 标题配置
            "project_name_title": self.config.get('include_project_name_title', '训练项目'),
            "start_time_title": self.config.get('include_start_time_title', '训练开始'),
            "end_time_title": self.config.get('include_end_time_title', '训练结束时间'),
            "method_title": self.config.get('include_method_title', '系统判断依据'),
            "duration_title": self.config.get('include_duration_title', '总耗时'),
            "hostname_title": self.config.get('include_hostname_title', '主机名'),
            "gpu_info_title": self.config.get('include_gpu_info_title', 'GPU信息'),
        }
        
        # 根据触发方式添加详情
        if method == "日志检测" and detail:
            training_info["keyword"] = detail
            training_info["keyword_title"] = "触发关键词"
        
        if method == "目标文件检测" and detail:
            training_info["target_file"] = detail
            training_info["target_file_title"] = "检测到的文件"
        
        # 添加 GPU 信息
        if gpu_info:
            training_info["gpu_info"] = gpu_info
        
        return training_info
    
    def build_message_content(self, training_info: Dict[str, Any]) -> str:
        """
        构建消息内容文本
        
        Args:
            training_info: 任务信息字典
            
        Returns:
            格式化的消息内容
        """
        content_items = []
        
        if self.config.get('include_project_name', True):
            content_items.append(
                f"**{training_info['project_name_title']}**: {training_info['project_name']}"
            )
        
        if self.config.get('include_start_time', True):
            content_items.append(
                f"**{training_info['start_time_title']}**: {training_info['start_time']}"
            )
        
        if self.config.get('include_end_time', True):
            content_items.append(
                f"**{training_info['end_time_title']}**: {training_info['end_time']}"
            )
        
        if self.config.get('include_method', True):
            content_items.append(
                f"**{training_info['method_title']}**: {training_info['method']}"
            )
        
        # 可选字段
        if 'keyword' in training_info and training_info['keyword']:
            content_items.append(
                f"**{training_info['keyword_title']}**: {training_info['keyword']}"
            )
        
        if 'target_file' in training_info and training_info['target_file']:
            content_items.append(
                f"**{training_info['target_file_title']}**: {training_info['target_file']}"
            )
        
        if self.config.get('include_duration', True):
            content_items.append(
                f"**{training_info['duration_title']}**: {training_info['duration']}"
            )
        
        if self.config.get('include_hostname', True):
            content_items.append(
                f"**{training_info['hostname_title']}**: {training_info['hostname']}"
            )
        
        if self.config.get('include_gpu_info', True) and 'gpu_info' in training_info:
            content_items.append(
                f"**{training_info['gpu_info_title']}**:\n{training_info['gpu_info']}"
            )
        
        # 确保至少有一个内容项
        if not content_items:
            content_items.append(f"**任务项目**: {training_info['project_name']}")
            content_items.append(f"**总耗时**: {training_info['duration']}")
        
        return "**任务已完成！**\n\n" + "\n".join(content_items)
