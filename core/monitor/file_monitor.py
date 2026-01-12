# -*- coding: utf-8 -*-
"""
文件监控模块

检测指定文件是否存在，支持检测文件创建和删除。
"""

import os
import time
import logging
from typing import Tuple, Optional, Dict, Any

from core.monitor.base import BaseMonitor

logger = logging.getLogger(__name__)


class FileMonitor(BaseMonitor):
    """
    文件存在监控器
    
    当指定的文件状态发生变化时（创建或删除），视为任务完成。
    支持二次确认机制，避免误触发。
    
    Attributes:
        file_path (str): 要监控的文件路径
        detect_deletion (bool): 是否检测文件删除
        recheck_delay (int): 二次检查延迟（秒）
        _enabled (bool): 是否启用此监控器
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化文件监控器
        
        Args:
            config: monitor 配置字典，需包含:
                - check_file_enabled: 是否启用
                - check_file_path: 文件路径
                - check_file_detect_deletion: 是否检测删除
                - check_file_recheck_delay: 二次检查延迟（秒）
        """
        self._enabled = config.get('check_file_enabled', False)
        self.file_path = config.get('check_file_path', '')
        self.detect_deletion = config.get('check_file_detect_deletion', False)
        self.recheck_delay = config.get('check_file_recheck_delay', 0)
        
        # 状态跟踪
        self._initial_exists: Optional[bool] = None  # 初始状态
        self._pending_trigger: Optional[str] = None  # 待确认的触发类型
        self._pending_timestamp: Optional[float] = None  # 待确认的时间戳
        self._initialized = False
    
    @property
    def name(self) -> str:
        return "文件监控"
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def check(self) -> Tuple[bool, str, Optional[str]]:
        """
        检查目标文件状态
        
        支持两种触发模式：
        1. 文件创建（默认）：文件从不存在变为存在
        2. 文件删除：文件从存在变为不存在（需开启 detect_deletion）
        
        Returns:
            Tuple[bool, str, Optional[str]]:
                - bool: 是否触发
                - str: 触发方式描述
                - Optional[str]: 文件路径
        """
        if not self._enabled:
            return False, "未启用", None
            
        if not self.file_path:
            logger.warning("文件监控已启用但未设置文件路径")
            return False, "未设置路径", None
        
        # 初始化：记录文件初始状态
        if not self._initialized:
            self._initial_exists = os.path.exists(self.file_path)
            self._initialized = True
            logger.info(f"文件监控初始化: {self.file_path}, 初始存在: {self._initial_exists}")
            return False, "初始化中", None
        
        current_exists = os.path.exists(self.file_path)
        
        # 检测文件创建
        if current_exists and not self._initial_exists:
            return self._handle_trigger("created", "目标文件检测", self.file_path)
        
        # 检测文件删除
        if self.detect_deletion and not current_exists and self._initial_exists:
            return self._handle_trigger("deleted", "文件删除检测", self.file_path)
        
        # 无变化时重置待确认状态
        if self._pending_trigger is not None:
            # 如果状态回退（如文件又消失或又出现），重置
            expected_exists = self._pending_trigger == "created"
            if current_exists != expected_exists:
                logger.info("文件状态回退，重置待确认状态")
                self._pending_trigger = None
                self._pending_timestamp = None
        
        return False, "未完成", None
    
    def _handle_trigger(self, trigger_type: str, method: str, detail: str) -> Tuple[bool, str, Optional[str]]:
        """
        处理触发事件（含二次确认）
        
        Args:
            trigger_type: 触发类型 (created/deleted)
            method: 方法名称
            detail: 详情
            
        Returns:
            触发结果元组
        """
        if self.recheck_delay <= 0:
            # 不需要二次确认
            logger.info(f"触发: {method} - {detail}")
            self._initial_exists = os.path.exists(self.file_path)  # 更新状态
            return True, method, detail
        
        # 需要二次确认
        if self._pending_trigger is None:
            # 首次检测到变化
            self._pending_trigger = trigger_type
            self._pending_timestamp = time.time()
            logger.info(f"检测到 {trigger_type}，等待 {self.recheck_delay} 秒进行二次确认")
            return False, "等待二次确认", None
        
        # 检查是否到达二次确认时间
        if time.time() - self._pending_timestamp < self.recheck_delay:
            return False, "等待二次确认", None
        
        # 二次确认：检查触发类型是否一致
        if self._pending_trigger == trigger_type:
            logger.info(f"二次确认通过: {method}")
            self._pending_trigger = None
            self._pending_timestamp = None
            self._initial_exists = os.path.exists(self.file_path)  # 更新状态
            return True, method, detail
        else:
            # 触发类型改变，重置
            logger.info("二次确认失败：触发类型改变")
            self._pending_trigger = trigger_type
            self._pending_timestamp = time.time()
            return False, "触发类型改变", None
    
    def reset(self):
        """重置监控状态"""
        self._initial_exists = None
        self._pending_trigger = None
        self._pending_timestamp = None
        self._initialized = False

