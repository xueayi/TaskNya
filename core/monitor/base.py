# -*- coding: utf-8 -*-
"""
监控器抽象基类

定义所有监控器必须实现的接口。
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional


class BaseMonitor(ABC):
    """
    监控器抽象基类
    
    所有具体的监控器（文件监控、日志监控、GPU监控等）都必须继承此类
    并实现 check() 方法和 name 属性。
    """
    
    @abstractmethod
    def check(self) -> Tuple[bool, str, Optional[str]]:
        """
        执行监控检查
        
        Returns:
            Tuple[bool, str, Optional[str]]: 
                - bool: 是否满足触发条件
                - str: 触发方式描述（如 "目标文件检测"、"日志检测" 等）
                - Optional[str]: 触发详情（如具体的文件路径、关键词等）
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        监控器名称
        
        Returns:
            str: 监控器的唯一标识名称
        """
        pass
    
    @property
    @abstractmethod
    def enabled(self) -> bool:
        """
        监控器是否启用
        
        Returns:
            bool: 是否启用
        """
        pass
