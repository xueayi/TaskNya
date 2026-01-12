# -*- coding: utf-8 -*-
"""
GPU 工具模块测试

测试 GPU 信息获取功能。
"""

import pytest
from unittest.mock import patch, MagicMock

from core.utils import get_gpu_info, get_gpu_power_info


class TestGpuUtils:
    """GPU 工具函数测试"""
    
    def test_get_gpu_info_success(self):
        """测试成功获取 GPU 信息"""
        mock_output = "0, NVIDIA GeForce RTX 3080, 2048, 10240, 150, 65\n"
        
        with patch('subprocess.check_output', return_value=mock_output):
            info = get_gpu_info()
            
            assert "GPU 0" in info
            assert "RTX 3080" in info
            assert "150W" in info
            assert "65°C" in info
    
    def test_get_gpu_info_multiple_gpus(self):
        """测试多 GPU 信息获取"""
        mock_output = "0, NVIDIA A100, 1024, 40960, 200, 55\n1, NVIDIA A100, 2048, 40960, 180, 52\n"
        
        with patch('subprocess.check_output', return_value=mock_output):
            info = get_gpu_info()
            
            assert "GPU 0" in info
            assert "GPU 1" in info
    
    def test_get_gpu_info_nvidia_not_available(self):
        """测试无 NVIDIA 显卡时的处理"""
        with patch('subprocess.check_output', side_effect=FileNotFoundError):
            info = get_gpu_info()
            
            assert "未检测到NVIDIA显卡" in info or "不可用" in info
    
    def test_get_gpu_info_parse_error(self):
        """测试解析错误处理"""
        mock_output = "invalid output format"
        
        with patch('subprocess.check_output', return_value=mock_output):
            info = get_gpu_info()
            
            # 应该返回某种错误提示或空信息
            assert info is not None
    
    def test_get_gpu_power_info_success(self):
        """测试成功获取功耗信息"""
        mock_output = "0, 45.00\n1, 30.00\n"
        
        with patch('subprocess.check_output', return_value=mock_output):
            power_info = get_gpu_power_info()
            
            assert power_info is not None
            assert power_info[0] == 45.0
            assert power_info[1] == 30.0
    
    def test_get_gpu_power_info_nvidia_not_available(self):
        """测试无 NVIDIA 显卡时返回 None"""
        with patch('subprocess.check_output', side_effect=FileNotFoundError):
            power_info = get_gpu_power_info()
            
            assert power_info is None
    
    def test_get_gpu_power_info_parse_error(self):
        """测试解析错误返回 None"""
        mock_output = "invalid"
        
        with patch('subprocess.check_output', return_value=mock_output):
            power_info = get_gpu_power_info()
            
            # 应该返回空字典或 None
            assert power_info is not None
            assert len(power_info) == 0
