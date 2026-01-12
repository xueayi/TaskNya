# -*- coding: utf-8 -*-
"""
集成测试

测试完整的监控流程和向后兼容性。
"""

import os
import pytest
import time
import threading
from datetime import datetime
from unittest.mock import patch, MagicMock

# 导入主模块
from main import TrainingMonitor


class TestIntegration:
    """集成测试"""
    
    def test_full_monitoring_flow_file(self, temp_dir, test_config):
        """测试文件监控完整流程"""
        # 设置测试文件路径
        test_file = os.path.join(temp_dir, 'model_final.pth')
        test_config['monitor']['check_file_path'] = test_file
        test_config['monitor']['check_file_enabled'] = True
        test_config['monitor']['check_log_enabled'] = False
        test_config['monitor']['check_gpu_power_enabled'] = False
        test_config['monitor']['check_interval'] = 1
        test_config['monitor']['timeout'] = 10
        test_config['webhook']['enabled'] = False
        
        # 创建配置文件
        import yaml
        config_path = os.path.join(temp_dir, 'test_config.yaml')
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f, allow_unicode=True)
        
        # 创建监控器
        monitor = TrainingMonitor(config_path=config_path)
        
        # 在后台线程中创建触发文件
        def create_file():
            time.sleep(2)
            with open(test_file, 'w') as f:
                f.write('model data')
        
        file_thread = threading.Thread(target=create_file)
        file_thread.start()
        
        # 验证监控检测
        start_time = time.time()
        triggered = False
        while time.time() - start_time < 5:
            flag, method, detail = monitor.is_training_complete()
            if flag:
                triggered = True
                assert method == "目标文件检测"
                break
            time.sleep(0.5)
        
        file_thread.join()
        assert triggered is True
    
    def test_full_monitoring_flow_log(self, temp_dir, test_config):
        """测试日志监控完整流程"""
        # 设置测试日志路径
        log_file = os.path.join(temp_dir, 'train.log')
        
        # 创建初始日志
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("开始训练...\n")
        
        test_config['monitor']['check_file_enabled'] = False
        test_config['monitor']['check_log_enabled'] = True
        test_config['monitor']['check_log_path'] = log_file
        test_config['monitor']['check_log_markers'] = ['训练完成', 'DONE']
        test_config['monitor']['check_log_mode'] = 'full'
        test_config['monitor']['check_gpu_power_enabled'] = False
        test_config['webhook']['enabled'] = False
        
        # 创建配置文件
        import yaml
        config_path = os.path.join(temp_dir, 'test_config.yaml')
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f, allow_unicode=True)
        
        monitor = TrainingMonitor(config_path=config_path)
        
        # 追加完成标记
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("Epoch 100/100\n")
            f.write("训练完成\n")
        
        # 验证检测
        flag, method, detail = monitor.is_training_complete()
        
        assert flag is True
        assert method == "日志检测"
        assert detail == "训练完成"


class TestBackwardCompatibility:
    """向后兼容性测试"""
    
    def test_training_monitor_backward_compat(self, temp_config_file):
        """测试 TrainingMonitor 类向后兼容性"""
        # 测试基本初始化
        monitor = TrainingMonitor(config_path=temp_config_file)
        
        # 验证必要的属性存在
        assert hasattr(monitor, 'config')
        assert hasattr(monitor, 'start_time')
        assert hasattr(monitor, 'should_stop')
        assert hasattr(monitor, 'low_power_count')
        
        # 验证必要的方法存在
        assert callable(monitor.is_training_complete)
        assert callable(monitor.send_notification)
        assert callable(monitor.get_gpu_info)
        assert callable(monitor.start_monitoring)
    
    def test_config_structure(self, temp_config_file):
        """测试配置结构保持一致"""
        monitor = TrainingMonitor(config_path=temp_config_file)
        
        # 验证配置结构
        assert 'monitor' in monitor.config
        assert 'webhook' in monitor.config
        
        # 验证 monitor 配置项
        assert 'project_name' in monitor.config['monitor']
        assert 'check_interval' in monitor.config['monitor']
        assert 'check_file_enabled' in monitor.config['monitor']
    
    def test_should_stop_callback(self, temp_config_file):
        """测试停止回调功能"""
        monitor = TrainingMonitor(config_path=temp_config_file)
        
        # 默认不停止
        assert monitor.should_stop() is False
        
        # 设置停止回调
        stop_flag = True
        monitor.should_stop = lambda: stop_flag
        assert monitor.should_stop() is True
    
    def test_default_config_fallback(self):
        """测试使用默认配置"""
        # 不提供配置文件
        with patch('core.config.config_manager.ConfigManager.load_config') as mock_load:
            from core.config import DEFAULT_CONFIG
            mock_load.return_value = DEFAULT_CONFIG.copy()
            
            monitor = TrainingMonitor()
            
            assert monitor.config['monitor']['project_name'] == DEFAULT_CONFIG['monitor']['project_name']
