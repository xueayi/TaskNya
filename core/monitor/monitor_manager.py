# -*- coding: utf-8 -*-
"""
监控管理器模块

组合多个监控器，提供统一的监控检测接口。
"""

import logging
from typing import Tuple, Optional, Dict, Any, List

from core.monitor.base import BaseMonitor
from core.monitor.file_monitor import FileMonitor
from core.monitor.log_monitor import LogMonitor
from core.monitor.gpu_monitor import GpuMonitor
from core.monitor.directory_monitor import DirectoryMonitor

logger = logging.getLogger(__name__)


class MonitorManager:
    """
    监控管理器
    
    组合多个监控器，任一监控器触发即视为任务完成（或逻辑）。
    
    Attributes:
        monitors (List[BaseMonitor]): 监控器列表
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化监控管理器
        
        根据配置创建并注册所有监控器。
        
        Args:
            config: 完整配置字典，包含 monitor 部分
        """
        monitor_config = config.get('monitor', {})
        
        self.monitors: List[BaseMonitor] = [
            FileMonitor(monitor_config),
            LogMonitor(monitor_config),
            GpuMonitor(monitor_config),
            DirectoryMonitor(monitor_config),
        ]
        
        # 记录启用的监控器
        enabled_monitors = [m.name for m in self.monitors if m.enabled]
        if enabled_monitors:
            logger.info(f"已启用的监控器: {', '.join(enabled_monitors)}")
        else:
            logger.warning("没有启用任何监控器")
    
    def check(self) -> Tuple[bool, str, Optional[str]]:
        """
        执行所有启用的监控器检查
        
        任一监控器触发即返回成功（或逻辑）。
        
        Returns:
            Tuple[bool, str, Optional[str]]:
                - bool: 是否有监控器触发
                - str: 触发的监控器名称/方式
                - Optional[str]: 触发详情
        """
        for monitor in self.monitors:
            if not monitor.enabled:
                continue
                
            triggered, method, detail = monitor.check()
            if triggered:
                return True, method, detail
        
        return False, "未完成任务", None
    
    def get_monitor(self, name: str) -> Optional[BaseMonitor]:
        """
        根据名称获取监控器
        
        Args:
            name: 监控器名称
            
        Returns:
            监控器实例，如果不存在则返回 None
        """
        for monitor in self.monitors:
            if monitor.name == name:
                return monitor
        return None
    
    def reset(self):
        """重置所有监控器状态"""
        for monitor in self.monitors:
            if hasattr(monitor, 'reset'):
                monitor.reset()
            if hasattr(monitor, 'reset_position'):
                monitor.reset_position()
