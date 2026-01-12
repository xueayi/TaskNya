# -*- coding: utf-8 -*-
"""
日志监控模块

检测日志文件中是否包含指定的完成标记。
支持全量检测和增量检测两种模式。
"""

import os
import logging
from typing import Tuple, Optional, Dict, Any, List

from core.monitor.base import BaseMonitor

logger = logging.getLogger(__name__)


class LogMonitor(BaseMonitor):
    """
    日志关键词监控器
    
    当日志文件中出现指定的关键词时，视为任务完成。
    支持两种检测模式：
    - full: 每次检测都读取整个日志文件
    - incremental: 只读取上次检测后新增的内容
    
    Attributes:
        log_path (str): 日志文件路径
        markers (List[str]): 完成标记关键词列表
        mode (str): 检测模式 ("full" 或 "incremental")
        last_position (int): 增量模式下记录的文件位置
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化日志监控器
        
        Args:
            config: monitor 配置字典，需包含:
                - check_log_enabled: 是否启用
                - check_log_path: 日志文件路径
                - check_log_markers: 完成标记列表
                - check_log_mode: 检测模式 ("full" 或 "incremental")
        """
        self._enabled = config.get('check_log_enabled', False)
        self.log_path = config.get('check_log_path', '')
        self.markers = config.get('check_log_markers', [])
        self.mode = config.get('check_log_mode', 'full')
        self.last_position = 0
        
        # 如果是增量模式，初始化文件位置
        if self._enabled and self.mode == 'incremental':
            self._init_position()
    
    def _init_position(self):
        """初始化日志文件位置（增量模式）"""
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, os.SEEK_END)
                    self.last_position = f.tell()
                    logger.info(f"初始化日志文件位置: {self.last_position} 字节")
            except Exception as e:
                logger.error(f"初始化日志文件位置失败: {str(e)}")
    
    @property
    def name(self) -> str:
        return "日志监控"
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def check(self) -> Tuple[bool, str, Optional[str]]:
        """
        检查日志文件中是否包含完成标记
        
        Returns:
            Tuple[bool, str, Optional[str]]:
                - bool: 是否找到完成标记
                - str: "日志检测"
                - Optional[str]: 找到的关键词
        """
        if not self._enabled:
            return False, "未启用", None
            
        if not os.path.exists(self.log_path):
            return False, "文件不存在", None
            
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                if self.mode == 'incremental':
                    # 增量检测模式
                    content = self._read_incremental(f)
                    if content is None:
                        return False, "无新内容", None
                else:
                    # 全量检测模式
                    content = f.read()
                
                # 在内容中查找标记
                for marker in self.markers:
                    if marker in content:
                        logger.info(f"在日志中发现完成标记: {marker}")
                        return True, "日志检测", marker
                        
        except Exception as e:
            logger.error(f"读取日志文件失败: {str(e)}")
            
        return False, "未完成", None
    
    def _read_incremental(self, f) -> Optional[str]:
        """
        增量读取日志文件
        
        Args:
            f: 文件对象
            
        Returns:
            新增的内容，如果没有新增则返回 None
        """
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        
        if file_size > self.last_position:
            f.seek(self.last_position)
            content = f.read()
            self.last_position = file_size
            logger.debug(f"检测日志增量内容: {len(content)} 字节")
            return content
        
        return None
    
    def reset_position(self):
        """重置日志文件位置（用于重新开始监控）"""
        self.last_position = 0
        if self.mode == 'incremental':
            self._init_position()
