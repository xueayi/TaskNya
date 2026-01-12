# Utils Module
"""工具模块"""

from core.utils.gpu import get_gpu_info, get_gpu_power_info
from core.utils.logger import setup_logger
from core.utils.anime_quote import get_anime_quote, AnimeQuoteService

__all__ = [
    'get_gpu_info',
    'get_gpu_power_info',
    'setup_logger',
    'get_anime_quote',
    'AnimeQuoteService',
]
