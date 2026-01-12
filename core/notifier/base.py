# -*- coding: utf-8 -*-
"""
通知器抽象基类

定义所有通知器必须实现的接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseNotifier(ABC):
    """
    通知器抽象基类
    
    所有具体的通知器（Webhook、邮件等）都必须继承此类
    并实现 send() 方法。
    """
    
    @abstractmethod
    def send(self, message: Dict[str, Any]) -> bool:
        """
        发送通知
        
        Args:
            message: 消息内容字典
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @property
    @abstractmethod
    def enabled(self) -> bool:
        """
        通知器是否启用
        
        Returns:
            bool: 是否启用
        """
        pass
