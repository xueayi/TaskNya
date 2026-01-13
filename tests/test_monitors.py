# -*- coding: utf-8 -*-
"""
监控模块测试

测试各种监控器的功能。
"""

import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock

from core.monitor import FileMonitor, LogMonitor, GpuMonitor, MonitorManager


class TestFileMonitor:
    """文件监控器测试"""
    
    def test_file_monitor_file_create_detection(self, temp_dir):
        """测试文件创建检测（新行为：初始不存在 -> 创建）"""
        test_file = os.path.join(temp_dir, 'model.pth')
        
        config = {
            'check_file_enabled': True,
            'check_file_path': test_file
        }
        monitor = FileMonitor(config)
        
        # 第一次调用：初始化
        triggered, method, detail = monitor.check()
        assert triggered is False
        assert method == "初始化中"
        
        # 第二次调用：文件仍不存在
        triggered, method, detail = monitor.check()
        assert triggered is False
        
        # 创建文件
        with open(test_file, 'w') as f:
            f.write('test')
        
        # 第三次调用：检测到文件创建
        triggered, method, detail = monitor.check()
        assert triggered is True
        assert method == "目标文件检测"
        assert detail == test_file
    
    def test_file_monitor_file_not_exists(self, temp_dir):
        """测试文件始终不存在时的检测"""
        config = {
            'check_file_enabled': True,
            'check_file_path': os.path.join(temp_dir, 'not_exist.pth')
        }
        monitor = FileMonitor(config)
        
        # 初始化
        triggered, _, _ = monitor.check()
        assert triggered is False
        
        # 后续检查
        triggered, method, detail = monitor.check()
        assert triggered is False
    
    def test_file_monitor_disabled(self):
        """测试禁用状态"""
        config = {
            'check_file_enabled': False,
            'check_file_path': '/some/path'
        }
        monitor = FileMonitor(config)
        
        assert monitor.enabled is False
        triggered, _, _ = monitor.check()
        assert triggered is False
    
    def test_file_monitor_deletion_detection(self, temp_dir):
        """测试文件删除检测"""
        test_file = os.path.join(temp_dir, 'existing.pth')
        
        # 先创建文件
        with open(test_file, 'w') as f:
            f.write('test')
        
        config = {
            'check_file_enabled': True,
            'check_file_path': test_file,
            'check_file_detect_deletion': True
        }
        monitor = FileMonitor(config)
        
        # 初始化
        triggered, _, _ = monitor.check()
        assert triggered is False
        assert monitor._initial_exists is True
        
        # 删除文件
        os.remove(test_file)
        
        # 检测到删除
        triggered, method, detail = monitor.check()
        assert triggered is True
        assert method == "文件删除检测"


class TestLogMonitor:
    """日志监控器测试"""
    
    def test_log_monitor_marker_found_full(self, temp_dir):
        """测试全量模式下关键词检测"""
        # 创建包含标记的日志文件
        log_file = os.path.join(temp_dir, 'train.log')
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("开始训练...\n")
            f.write("Epoch 1/100\n")
            f.write("训练完成\n")
        
        config = {
            'check_log_enabled': True,
            'check_log_path': log_file,
            'check_log_markers': ['训练完成', 'done'],
            'check_log_mode': 'full'
        }
        monitor = LogMonitor(config)
        
        triggered, method, detail = monitor.check()
        
        assert triggered is True
        assert method == "日志检测"
        assert detail == "训练完成"
    
    def test_log_monitor_marker_found_incremental(self, temp_dir):
        """测试增量模式下关键词检测"""
        log_file = os.path.join(temp_dir, 'train.log')
        
        # 初始内容
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("开始训练...\n")
        
        config = {
            'check_log_enabled': True,
            'check_log_path': log_file,
            'check_log_markers': ['训练完成'],
            'check_log_mode': 'incremental'
        }
        monitor = LogMonitor(config)
        
        # 第一次检查，无新内容
        triggered, _, _ = monitor.check()
        assert triggered is False
        
        # 追加完成标记
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("训练完成\n")
        
        # 再次检查
        triggered, method, detail = monitor.check()
        assert triggered is True
        assert detail == "训练完成"
    
    def test_log_monitor_marker_not_found(self, temp_dir):
        """测试无关键词时的处理"""
        log_file = os.path.join(temp_dir, 'train.log')
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("正在训练中...\n")
        
        config = {
            'check_log_enabled': True,
            'check_log_path': log_file,
            'check_log_markers': ['完成', 'done'],
            'check_log_mode': 'full'
        }
        monitor = LogMonitor(config)
        
        triggered, _, _ = monitor.check()
        
        assert triggered is False
    
    def test_log_monitor_file_not_exists(self):
        """测试日志文件不存在"""
        config = {
            'check_log_enabled': True,
            'check_log_path': '/not/exist/log.txt',
            'check_log_markers': ['完成'],
            'check_log_mode': 'full'
        }
        monitor = LogMonitor(config)
        
        triggered, _, _ = monitor.check()
        
        assert triggered is False


class TestGpuMonitor:
    """GPU 功耗监控器测试"""
    
    def test_gpu_monitor_below_threshold(self):
        """测试 GPU 功耗低于阈值"""
        config = {
            'check_gpu_power_enabled': True,
            'check_gpu_power_threshold': 50.0,
            'check_gpu_power_gpu_ids': 'all',
            'check_gpu_power_consecutive_checks': 2
        }
        monitor = GpuMonitor(config)
        
        # Mock nvidia-smi 输出低功耗
        with patch('subprocess.check_output', return_value="0, 30.00\n1, 25.00\n"):
            # 第一次检测
            triggered, _, _ = monitor.check()
            assert triggered is False  # 还未达到连续次数
            assert monitor.low_power_count == 1
            
            # 第二次检测
            triggered, method, _ = monitor.check()
            assert triggered is True  # 达到连续次数
            assert method == "GPU功耗检测"
    
    def test_gpu_monitor_above_threshold(self):
        """测试 GPU 功耗高于阈值"""
        config = {
            'check_gpu_power_enabled': True,
            'check_gpu_power_threshold': 50.0,
            'check_gpu_power_gpu_ids': 'all',
            'check_gpu_power_consecutive_checks': 3
        }
        monitor = GpuMonitor(config)
        
        with patch('subprocess.check_output', return_value="0, 150.00\n"):
            triggered, _, _ = monitor.check()
            assert triggered is False
            assert monitor.low_power_count == 0
    
    def test_gpu_monitor_consecutive_checks(self):
        """测试连续检测逻辑"""
        config = {
            'check_gpu_power_enabled': True,
            'check_gpu_power_threshold': 50.0,
            'check_gpu_power_gpu_ids': 'all',
            'check_gpu_power_consecutive_checks': 3
        }
        monitor = GpuMonitor(config)
        
        with patch('subprocess.check_output') as mock_output:
            # 两次低功耗
            mock_output.return_value = "0, 30.00\n"
            monitor.check()
            monitor.check()
            assert monitor.low_power_count == 2
            
            # 一次高功耗，计数器重置
            mock_output.return_value = "0, 100.00\n"
            monitor.check()
            assert monitor.low_power_count == 0
    
    def test_gpu_monitor_trigger_mode_above(self):
        """测试 trigger_mode='above' - 功耗高于阈值时触发"""
        config = {
            'check_gpu_power_enabled': True,
            'check_gpu_power_threshold': 100.0,
            'check_gpu_power_trigger_mode': 'above',  # 高于阈值触发
            'check_gpu_power_gpu_ids': 'all',
            'check_gpu_power_consecutive_checks': 2
        }
        monitor = GpuMonitor(config)
        
        # Mock nvidia-smi 输出高功耗
        with patch('subprocess.check_output', return_value="0, 150.00\n1, 180.00\n"):
            # 第一次检测
            triggered, _, _ = monitor.check()
            assert triggered is False  # 还未达到连续次数
            assert monitor.low_power_count == 1
            
            # 第二次检测
            triggered, method, _ = monitor.check()
            assert triggered is True  # 达到连续次数
            assert method == "GPU功耗检测"
    
    def test_gpu_monitor_trigger_mode_above_not_triggered(self):
        """测试 trigger_mode='above' - 功耗低于阈值时不触发"""
        config = {
            'check_gpu_power_enabled': True,
            'check_gpu_power_threshold': 100.0,
            'check_gpu_power_trigger_mode': 'above',
            'check_gpu_power_gpu_ids': 'all',
            'check_gpu_power_consecutive_checks': 2
        }
        monitor = GpuMonitor(config)
        
        # Mock nvidia-smi 输出低功耗
        with patch('subprocess.check_output', return_value="0, 50.00\n"):
            triggered, _, _ = monitor.check()
            assert triggered is False
            assert monitor.low_power_count == 0
    
    def test_gpu_monitor_nvidia_not_available(self):
        """测试无 NVIDIA 显卡时的处理"""
        config = {
            'check_gpu_power_enabled': True,
            'check_gpu_power_threshold': 50.0,
            'check_gpu_power_gpu_ids': 'all',
            'check_gpu_power_consecutive_checks': 3
        }
        monitor = GpuMonitor(config)
        
        with patch('subprocess.check_output', side_effect=FileNotFoundError):
            triggered, _, _ = monitor.check()
            assert triggered is False


class TestMonitorManager:
    """监控管理器测试"""
    
    def test_monitor_manager_any_trigger(self, temp_dir, test_config):
        """测试监控管理器"或"逻辑"""
        test_file = os.path.join(temp_dir, 'trigger.txt')
        
        test_config['monitor']['check_file_path'] = test_file
        test_config['monitor']['check_log_enabled'] = False
        test_config['monitor']['check_gpu_power_enabled'] = False
        test_config['monitor']['check_directory_enabled'] = False
        
        manager = MonitorManager(test_config)
        
        # 第一次调用：初始化
        triggered, _, _ = manager.check()
        assert triggered is False
        
        # 创建触发文件
        with open(test_file, 'w') as f:
            f.write('done')
        
        # 再次检查
        triggered, method, _ = manager.check()
        
        assert triggered is True
        assert "文件" in method or "目标" in method
    
    def test_monitor_manager_no_trigger(self, test_config):
        """测试无触发时的行为"""
        test_config['monitor']['check_file_path'] = '/not/exist/file'
        test_config['monitor']['check_log_enabled'] = False
        test_config['monitor']['check_gpu_power_enabled'] = False
        
        manager = MonitorManager(test_config)
        
        triggered, _, _ = manager.check()
        
        assert triggered is False
    
    def test_monitor_manager_get_monitor(self, test_config):
        """测试获取特定监控器"""
        manager = MonitorManager(test_config)
        
        file_monitor = manager.get_monitor("文件监控")
        assert file_monitor is not None
        
        log_monitor = manager.get_monitor("日志监控")
        assert log_monitor is not None
        
        invalid = manager.get_monitor("不存在的监控器")
        assert invalid is None
