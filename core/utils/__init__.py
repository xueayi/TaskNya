# Utils Module
"""工具模块"""

from core.utils.gpu import get_gpu_info, get_gpu_power_info
from core.utils.logger import setup_logger

__all__ = [
    'get_gpu_info',
    'get_gpu_power_info',
    'setup_logger',
]
