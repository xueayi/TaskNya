# -*- coding: utf-8 -*-
"""
二次元语录模块

提供动漫经典台词的获取功能，支持多种 API 源。
设计为可扩展架构，方便未来切换或添加新的 API 提供商。
"""

import logging
import random
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)


class QuoteProvider(ABC):
    """
    语录提供者抽象基类
    
    所有语录 API 提供者都需要继承此类并实现 get_quote 方法。
    """
    
    @abstractmethod
    def get_quote(self) -> Optional[str]:
        """
        获取一条语录
        
        Returns:
            格式化的语录字符串，如 "台词——《作品名》"。
            如果获取失败返回 None。
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """提供者名称"""
        pass


class HitokotoProvider(QuoteProvider):
    """
    一言 API (hitokoto.cn) 提供者
    
    API 文档: https://developer.hitokoto.cn/
    """
    
    API_URL = "https://v1.hitokoto.cn/"
    
    # 类型映射: a=动画, b=漫画, c=游戏, d=文学, e=原创, f=网络, g=其他, h=影视, i=诗词, j=网易云, k=哲学, l=抖机灵
    DEFAULT_TYPES = ["a", "b", "c", "h"]  # 默认只获取动画、漫画、游戏、影视类型
    
    def __init__(self, types: list = None, timeout: int = 5):
        """
        初始化一言 API 提供者
        
        Args:
            types: 语录类型列表，参见 API 文档
            timeout: 请求超时时间（秒）
        """
        self.types = types or self.DEFAULT_TYPES
        self.timeout = timeout
    
    @property
    def name(self) -> str:
        return "hitokoto"
    
    def get_quote(self) -> Optional[str]:
        """从一言 API 获取语录"""
        try:
            # 随机选择一个类型
            params = {"c": random.choice(self.types)}
            
            response = requests.get(
                self.API_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            quote = data.get("hitokoto", "")
            source = data.get("from", "")
            from_who = data.get("from_who", "")
            
            if quote:
                # 格式化输出
                result = quote
                if source:
                    result += f"——《{source}》"
                if from_who:
                    result += f" {from_who}"
                return result
                
        except requests.exceptions.Timeout:
            logger.warning("一言 API 请求超时")
        except requests.exceptions.RequestException as e:
            logger.warning(f"一言 API 请求失败: {e}")
        except Exception as e:
            logger.error(f"获取一言语录时发生错误: {e}")
        
        return None


class FallbackProvider(QuoteProvider):
    """
    内置静态语录提供者
    
    作为 fallback 使用，当在线 API 不可用时返回内置语录。
    """
    
    # 内置经典动漫语录
    QUOTES = [
        ("正因不完美，人才可爱。", "钢之炼金术师"),
        ("不管前方的路有多苦，只要走的方向正确，不管多么崎岖不平，都比站在原地更接近幸福。", "千与千寻"),
        ("人们之所以能够心怀希望，是因为他们看不见死亡。", "死神"),
        ("如果不能带着微笑战斗，就无法成为真正的强者。", "航海王"),
        ("我是要成为海贼王的男人！", "航海王"),
        ("真相只有一个！", "名侦探柯南"),
        ("我是决不会输的，因为我肩负着伙伴的梦想！", "航海王"),
        ("无论怎样都要活下去！", "进击的巨人"),
        ("能够遇见你，真是太好了。", "夏目友人帐"),
        ("比自己、比梦想更重要的东西，永远存在着。", "灌篮高手"),
        ("只有你能决定你成为什么样的人。", "疯狂动物城"),
        ("坚持不懈地努力，就一定能创造奇迹。", "排球少年"),
        ("勇往直前的人，绝不会孤单。", "火影忍者"),
        ("我不会放弃的，因为我是永不言败的！", "鸣人"),
        ("痛苦可以承受，快乐更加难得。", "秒速五厘米"),
        ("只要出发，就能到达。", "言叶之庭"),
        ("不想让别人看到自己的泪水，就只能变得更强。", "网球王子"),
        ("人类的赞歌是勇气的赞歌！", "JOJO的奇妙冒险"),
        ("梦想不是用来实现的，是用来追逐的。", "火影忍者"),
        ("所谓的强大，是永不放弃自己想要保护的东西。", "银魂"),
    ]
    
    @property
    def name(self) -> str:
        return "fallback"
    
    def get_quote(self) -> Optional[str]:
        """从内置列表随机获取语录"""
        quote, source = random.choice(self.QUOTES)
        return f"{quote}——《{source}》"


class AnimeQuoteService:
    """
    二次元语录服务
    
    管理多个语录提供者，提供统一的获取接口。
    支持主提供者和 fallback 机制。
    
    Example:
        >>> service = AnimeQuoteService()
        >>> quote = service.get_quote()
        >>> print(quote)
        "正因不完美，人才可爱。——《钢之炼金术师》"
    """
    
    # 支持的提供者映射
    PROVIDERS: Dict[str, type] = {
        "hitokoto": HitokotoProvider,
        "fallback": FallbackProvider,
    }
    
    def __init__(self, 
                 primary_provider: str = "hitokoto",
                 fallback_provider: str = "fallback",
                 provider_config: Dict[str, Any] = None):
        """
        初始化语录服务
        
        Args:
            primary_provider: 主要提供者名称
            fallback_provider: 备用提供者名称
            provider_config: 提供者配置字典
        """
        self.provider_config = provider_config or {}
        
        # 初始化提供者
        self._primary = self._create_provider(primary_provider)
        self._fallback = self._create_provider(fallback_provider)
    
    def _create_provider(self, name: str) -> Optional[QuoteProvider]:
        """创建提供者实例"""
        provider_class = self.PROVIDERS.get(name)
        if provider_class:
            config = self.provider_config.get(name, {})
            return provider_class(**config)
        logger.warning(f"未知的语录提供者: {name}")
        return None
    
    def get_quote(self) -> str:
        """
        获取一条语录
        
        首先尝试主提供者，失败时使用 fallback。
        
        Returns:
            格式化的语录字符串
        """
        # 尝试主提供者
        if self._primary:
            quote = self._primary.get_quote()
            if quote:
                return quote
        
        # 使用 fallback
        if self._fallback:
            quote = self._fallback.get_quote()
            if quote:
                return quote
        
        # 最后的保底
        return "路漫漫其修远兮，吾将上下而求索。——《离骚》"
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        注册新的语录提供者
        
        Args:
            name: 提供者名称
            provider_class: 提供者类（需继承 QuoteProvider）
        """
        if not issubclass(provider_class, QuoteProvider):
            raise TypeError("provider_class 必须继承 QuoteProvider")
        cls.PROVIDERS[name] = provider_class


# 便捷函数
_default_service: Optional[AnimeQuoteService] = None


def get_anime_quote() -> str:
    """
    获取一条二次元语录（便捷函数）
    
    使用默认配置的服务实例获取语录。
    
    Returns:
        格式化的语录字符串，如 "台词——《作品名》"
    """
    global _default_service
    if _default_service is None:
        _default_service = AnimeQuoteService()
    return _default_service.get_quote()
