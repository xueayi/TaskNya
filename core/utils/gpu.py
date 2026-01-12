# -*- coding: utf-8 -*-
"""
GPU 工具模块

提供 GPU 信息获取相关的工具函数。
"""

import subprocess
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def get_gpu_info() -> str:
    """
    获取 GPU 详细信息
    
    Returns:
        str: 格式化的 GPU 信息描述
    """
    try:
        output = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=index,name,memory.used,memory.total,power.draw,temperature.gpu', 
             '--format=csv,noheader,nounits'],
            universal_newlines=True
        )
        
        gpu_list = output.strip().split('\n')
        formatted_info = []
        
        for gpu in gpu_list:
            parts = [x.strip() for x in gpu.split(',')]
            if len(parts) >= 6:
                idx, name, mem_used, mem_total, power, temp = parts[:6]
                gpu_info = f"GPU {idx} ({name}):\n"
                gpu_info += f"- 功耗: {power}W\n"
                gpu_info += f"- 温度: {temp}°C\n"
                gpu_info += f"- 显存: {mem_used}/{mem_total}MB"
                formatted_info.append(gpu_info)
        
        return "\n".join(formatted_info) if formatted_info else "无法解析GPU信息"
        
    except (subprocess.SubprocessError, FileNotFoundError):
        return "未检测到NVIDIA显卡或nvidia-smi不可用"
    except Exception as e:
        logger.error(f"获取GPU信息失败: {str(e)}")
        return "无法获取GPU信息"


def get_gpu_power_info() -> Optional[Dict[int, float]]:
    """
    获取 GPU 功耗信息
    
    Returns:
        Dict[int, float]: GPU ID 到功耗的映射，如果获取失败则返回 None
    """
    try:
        output = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=index,power.draw', '--format=csv,noheader,nounits'],
            universal_newlines=True
        )
        
        gpu_power_info = {}
        for line in output.strip().split('\n'):
            if ',' in line:
                idx, power = line.split(',')
                gpu_power_info[int(idx.strip())] = float(power.strip())
        
        return gpu_power_info
        
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.warning("未检测到NVIDIA显卡或nvidia-smi不可用")
        return None
    except Exception as e:
        logger.error(f"获取GPU功耗信息失败: {str(e)}")
        return None
