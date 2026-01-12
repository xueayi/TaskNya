# -*- coding: utf-8 -*-
"""
配置模块测试

测试 ConfigManager 类的各项功能。
"""

import os
import pytest
import tempfile
import yaml

from core.config import ConfigManager, DEFAULT_CONFIG


class TestConfigManager:
    """ConfigManager 类测试"""
    
    def test_load_config_success(self, temp_config_file):
        """测试正常加载配置文件"""
        manager = ConfigManager()
        config = manager.load_config(temp_config_file)
        
        assert config is not None
        assert 'monitor' in config
        assert 'webhook' in config
        assert config['monitor']['project_name'] == '测试项目'
    
    def test_load_config_not_found(self, temp_dir):
        """测试配置文件不存在的处理"""
        manager = ConfigManager()
        non_existent_path = os.path.join(temp_dir, 'not_exist.yaml')
        
        config = manager.load_config(non_existent_path)
        
        # 应该返回默认配置
        assert config is not None
        assert config['monitor']['project_name'] == DEFAULT_CONFIG['monitor']['project_name']
    
    def test_load_config_invalid_yaml(self, temp_dir):
        """测试无效 YAML 格式处理"""
        # 创建无效 YAML 文件
        invalid_path = os.path.join(temp_dir, 'invalid.yaml')
        with open(invalid_path, 'w') as f:
            f.write("invalid: yaml: content: [}")
        
        manager = ConfigManager()
        config = manager.load_config(invalid_path)
        
        # 应该返回默认配置
        assert config is not None
        assert 'monitor' in config
    
    def test_save_config(self, temp_dir):
        """测试配置保存功能"""
        manager = ConfigManager(config_dir=temp_dir)
        
        test_config = {
            'monitor': {'project_name': '保存测试'},
            'webhook': {'enabled': False}
        }
        
        result = manager.save_config(test_config, 'saved.yaml')
        
        assert result is True
        assert os.path.exists(os.path.join(temp_dir, 'saved.yaml'))
        
        # 验证保存内容
        with open(os.path.join(temp_dir, 'saved.yaml'), 'r', encoding='utf-8') as f:
            saved = yaml.safe_load(f)
        assert saved['monitor']['project_name'] == '保存测试'
    
    def test_merge_config(self):
        """测试用户配置与默认配置合并"""
        user_config = {
            'monitor': {
                'project_name': '用户项目',
                'check_interval': 10
            }
        }
        
        merged = ConfigManager.merge_config(user_config, DEFAULT_CONFIG)
        
        # 用户值应覆盖默认值
        assert merged['monitor']['project_name'] == '用户项目'
        assert merged['monitor']['check_interval'] == 10
        
        # 未指定的值应使用默认值
        assert merged['monitor']['timeout'] == DEFAULT_CONFIG['monitor']['timeout']
        assert 'webhook' in merged
    
    def test_merge_config_empty_user(self):
        """测试空用户配置的合并"""
        merged = ConfigManager.merge_config(None, DEFAULT_CONFIG)
        
        assert merged == DEFAULT_CONFIG
    
    def test_validate_config_valid(self, test_config):
        """测试有效配置验证"""
        result = ConfigManager.validate_config(test_config)
        
        assert result is True
    
    def test_validate_config_invalid(self):
        """测试无效配置验证"""
        invalid_config = {
            'monitor': {
                'check_interval': 'not_a_number'  # 应该是整数
            }
        }
        
        result = ConfigManager.validate_config(invalid_config)
        
        assert result is False
    
    def test_list_configs(self, temp_dir):
        """测试列出配置文件"""
        manager = ConfigManager(config_dir=temp_dir)
        
        # 创建一些配置文件
        for name in ['config1.yaml', 'config2.yaml', 'other.txt']:
            with open(os.path.join(temp_dir, name), 'w') as f:
                f.write('')
        
        configs = manager.list_configs()
        
        assert 'config1.yaml' in configs
        assert 'config2.yaml' in configs
        assert 'other.txt' not in configs
