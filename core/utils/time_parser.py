# -*- coding: utf-8 -*-
"""
时间字符串解析工具

支持将时分秒格式的字符串解析为秒数。
"""

import re
from typing import Union, Optional


def parse_time_to_seconds(time_str: Union[str, int, float]) -> int:
    """
    解析时间字符串为秒数
    
    支持格式：
    - 纯数字: "300" 或 300 -> 300秒
    - 时分秒: "1h30m5s" -> 5405秒
    - 时分: "1h30m" -> 5400秒
    - 分秒: "30m5s" -> 1805秒
    - 单独时: "2h" -> 7200秒
    - 单独分: "30m" -> 1800秒
    - 单独秒: "45s" -> 45秒
    
    Args:
        time_str: 时间字符串或数字
        
    Returns:
        int: 秒数
        
    Raises:
        ValueError: 无法解析的格式
        
    Examples:
        >>> parse_time_to_seconds("1h30m")
        5400
        >>> parse_time_to_seconds(60)
        60
        >>> parse_time_to_seconds("5m30s")
        330
    """
    # 如果已经是数字，直接返回
    if isinstance(time_str, (int, float)):
        return int(time_str)
    
    # 转换为字符串并去除空白
    time_str = str(time_str).strip().lower()
    
    # 空字符串返回0
    if not time_str:
        return 0
    
    # 尝试直接解析为数字
    try:
        return int(float(time_str))
    except ValueError:
        pass
    
    # 解析时分秒格式
    total_seconds = 0
    
    # 匹配 h, m, s 各部分
    pattern = r'(?:(\d+(?:\.\d+)?)\s*h)?\s*(?:(\d+(?:\.\d+)?)\s*m)?\s*(?:(\d+(?:\.\d+)?)\s*s)?'
    match = re.match(pattern, time_str)
    
    if match:
        hours = match.group(1)
        minutes = match.group(2)
        seconds = match.group(3)
        
        if hours:
            total_seconds += int(float(hours) * 3600)
        if minutes:
            total_seconds += int(float(minutes) * 60)
        if seconds:
            total_seconds += int(float(seconds))
        
        # 如果成功解析到任何值，返回结果
        if hours or minutes or seconds:
            return total_seconds
    
    # 无法解析
    raise ValueError(f"无法解析时间格式: '{time_str}'。支持格式: 纯数字(秒)、1h30m、30m5s 等")


def format_seconds_to_time(seconds: int) -> str:
    """
    将秒数格式化为可读的时间字符串
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化的时间字符串
        
    Examples:
        >>> format_seconds_to_time(5400)
        "1h30m"
        >>> format_seconds_to_time(90)
        "1m30s"
    """
    if seconds < 60:
        return f"{seconds}s"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 and hours == 0:  # 有小时时通常不显示秒
        parts.append(f"{secs}s")
    
    return "".join(parts) if parts else "0s"
