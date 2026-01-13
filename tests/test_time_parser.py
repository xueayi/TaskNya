# -*- coding: utf-8 -*-
"""
时间解析工具测试

测试 time_parser 模块的功能。
"""

import pytest
from core.utils.time_parser import parse_time_to_seconds, format_seconds_to_time


class TestParseTimeToSeconds:
    """测试 parse_time_to_seconds 函数"""
    
    def test_pure_integer(self):
        """测试纯整数输入"""
        assert parse_time_to_seconds(60) == 60
        assert parse_time_to_seconds(0) == 0
        assert parse_time_to_seconds(3600) == 3600
    
    def test_pure_float(self):
        """测试浮点数输入"""
        assert parse_time_to_seconds(60.5) == 60
        assert parse_time_to_seconds(90.9) == 90
    
    def test_string_number(self):
        """测试纯数字字符串"""
        assert parse_time_to_seconds("60") == 60
        assert parse_time_to_seconds("3600") == 3600
        assert parse_time_to_seconds("  120  ") == 120
    
    def test_hours_format(self):
        """测试小时格式"""
        assert parse_time_to_seconds("1h") == 3600
        assert parse_time_to_seconds("2h") == 7200
        assert parse_time_to_seconds("1H") == 3600  # 大小写不敏感
    
    def test_minutes_format(self):
        """测试分钟格式"""
        assert parse_time_to_seconds("30m") == 1800
        assert parse_time_to_seconds("5m") == 300
        assert parse_time_to_seconds("1M") == 60  # 大小写不敏感
    
    def test_seconds_format(self):
        """测试秒格式"""
        assert parse_time_to_seconds("45s") == 45
        assert parse_time_to_seconds("90s") == 90
    
    def test_hours_minutes_format(self):
        """测试时分格式"""
        assert parse_time_to_seconds("1h30m") == 5400
        assert parse_time_to_seconds("2h15m") == 8100
        assert parse_time_to_seconds("1h 30m") == 5400  # 支持空格
    
    def test_minutes_seconds_format(self):
        """测试分秒格式"""
        assert parse_time_to_seconds("5m30s") == 330
        assert parse_time_to_seconds("1m5s") == 65
    
    def test_full_format(self):
        """测试完整时分秒格式"""
        assert parse_time_to_seconds("1h30m5s") == 5405
        assert parse_time_to_seconds("2h0m30s") == 7230
    
    def test_empty_string(self):
        """测试空字符串返回0"""
        assert parse_time_to_seconds("") == 0
        assert parse_time_to_seconds("  ") == 0
    
    def test_invalid_format_raises(self):
        """测试无效格式抛出异常"""
        with pytest.raises(ValueError):
            parse_time_to_seconds("invalid")
        with pytest.raises(ValueError):
            parse_time_to_seconds("abc123")


class TestFormatSecondsToTime:
    """测试 format_seconds_to_time 函数"""
    
    def test_seconds_only(self):
        """测试纯秒数"""
        assert format_seconds_to_time(45) == "45s"
        assert format_seconds_to_time(0) == "0s"
    
    def test_minutes_only(self):
        """测试分钟（无余秒）"""
        assert format_seconds_to_time(60) == "1m"
        assert format_seconds_to_time(300) == "5m"
    
    def test_minutes_and_seconds(self):
        """测试分秒组合"""
        assert format_seconds_to_time(90) == "1m30s"
        assert format_seconds_to_time(65) == "1m5s"
    
    def test_hours_only(self):
        """测试小时（无余分秒）"""
        assert format_seconds_to_time(3600) == "1h"
        assert format_seconds_to_time(7200) == "2h"
    
    def test_hours_and_minutes(self):
        """测试时分组合"""
        assert format_seconds_to_time(5400) == "1h30m"
        assert format_seconds_to_time(8100) == "2h15m"
    
    def test_hours_minutes_no_seconds(self):
        """测试有时分时不显示秒"""
        # 当有小时时，通常不显示秒
        assert format_seconds_to_time(3661) == "1h1m"  # 1小时1分1秒 -> 1h1m


class TestRoundTrip:
    """测试解析和格式化的往返一致性"""
    
    def test_parse_format_consistency(self):
        """测试格式化后再解析能得到相同值"""
        values = [60, 300, 3600, 5400, 90, 7200]
        for val in values:
            formatted = format_seconds_to_time(val)
            parsed = parse_time_to_seconds(formatted)
            # 由于格式化可能丢失秒（当有小时时），只验证特定情况
            if val < 3600 or val % 60 == 0:
                assert parsed == val, f"Failed for {val}: formatted='{formatted}', parsed={parsed}"
