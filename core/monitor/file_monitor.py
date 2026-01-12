# -*- coding: utf-8 -*-
"""
文件监控模块

检测指定文件是否存在。
"""

import os
import logging
from typing import Tuple, Optional, Dict, Any

from core.monitor.base import BaseMonitor

logger = logging.getLogger(__name__)


class FileMonitor(BaseMonitor):
    """
    文件存在监控器
    
    当指定的文件存在时，视为任务完成。
    
    Attributes:
        file_path (str): 要监控的文件路径
        _enabled (bool): 是否启用此监控器
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化文件监控器
        
        Args:
            config: monitor 配置字典，需包含:
                - check_file_enabled: 是否启用
                - check_file_path: 文件路径
        """
        self._enabled = config.get('check_file_enabled', False)
        self.file_path = config.get('check_file_path', '')
    
    @property
    def name(self) -> str:
        return "文件监控"
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def check(self) -> Tuple[bool, str, Optional[str]]:
        """
        检查目标文件是否存在
        
        Returns:
            Tuple[bool, str, Optional[str]]:
                - bool: 文件是否存在
                - str: "目标文件检测"
                - Optional[str]: 文件路径
        """
        if not self._enabled:
            return False, "未启用", None
            
        if not self.file_path:
            logger.warning("文件监控已启用但未设置文件路径")
            return False, "未设置路径", None
            
        if os.path.exists(self.file_path):
            logger.info(f"找到指定文件: {self.file_path}")
            return True, "目标文件检测", self.file_path
            
        return False, "未完成", None
