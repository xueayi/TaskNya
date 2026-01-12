# -*- coding: utf-8 -*-
"""
配置管理模块

提供配置文件的加载、保存、合并和验证功能。
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from copy import deepcopy

from core.config.defaults import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    配置管理器
    
    负责配置文件的加载、保存、合并和验证。
    
    Attributes:
        config_dir (str): 配置文件目录路径
        default_config_path (str): 默认配置文件路径
    """
    
    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为项目根目录下的 configs/
        """
        if config_dir is None:
            # 默认配置目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_dir = os.path.join(project_root, 'configs')
        
        self.config_dir = config_dir
        self.default_config_path = os.path.join(config_dir, 'default.yaml')
        
        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)
    
    def load_config(self, config_path: str = None) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径，默认为 default.yaml
            
        Returns:
            配置字典，如果加载失败则返回默认配置
        """
        if config_path is None:
            config_path = self.default_config_path
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                logger.info(f"成功加载配置文件: {config_path}")
                
                # 与默认配置合并
                return self.merge_config(user_config, DEFAULT_CONFIG)
                
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return deepcopy(DEFAULT_CONFIG)
        except yaml.YAMLError as e:
            logger.error(f"配置文件格式错误: {str(e)}")
            return deepcopy(DEFAULT_CONFIG)
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return deepcopy(DEFAULT_CONFIG)
    
    def save_config(self, config: Dict[str, Any], filename: str = None) -> bool:
        """
        保存配置到文件
        
        Args:
            config: 配置字典
            filename: 文件名（不含路径），默认为 default.yaml
            
        Returns:
            保存是否成功
        """
        if filename is None:
            filename = 'default.yaml'
            
        file_path = os.path.join(self.config_dir, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"配置已保存到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False
    
    @staticmethod
    def merge_config(user_config: Dict[str, Any], 
                     default_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        合并用户配置与默认配置
        
        用户配置会覆盖默认配置中的对应值，
        但默认配置中存在而用户配置中不存在的值会被保留。
        
        Args:
            user_config: 用户配置
            default_config: 默认配置，如果不提供则使用 DEFAULT_CONFIG
            
        Returns:
            合并后的配置
        """
        if default_config is None:
            default_config = DEFAULT_CONFIG
            
        result = deepcopy(default_config)
        
        if user_config is None:
            return result
        
        # 合并 monitor 配置
        if 'monitor' in user_config and user_config['monitor']:
            result['monitor'].update(user_config['monitor'])
        
        # 合并 webhook 配置
        if 'webhook' in user_config and user_config['webhook']:
            result['webhook'].update(user_config['webhook'])
        
        # 合并 generic_webhook 配置
        if 'generic_webhook' in user_config and user_config['generic_webhook']:
            result['generic_webhook'].update(user_config['generic_webhook'])
        
        return result
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """
        验证配置数据的类型
        
        Args:
            config: 配置字典
            
        Returns:
            配置是否有效
        """
        try:
            monitor = config.get('monitor', {})
            
            # 验证并转换数值类型
            if 'check_interval' in monitor:
                monitor['check_interval'] = int(monitor['check_interval'])
            if 'logprint' in monitor:
                monitor['logprint'] = int(monitor['logprint'])
            if 'timeout' in monitor and monitor['timeout'] is not None and monitor['timeout'] != 'None':
                monitor['timeout'] = int(monitor['timeout'])
            if 'check_gpu_power_threshold' in monitor:
                monitor['check_gpu_power_threshold'] = float(monitor['check_gpu_power_threshold'])
            if 'check_gpu_power_consecutive_checks' in monitor:
                monitor['check_gpu_power_consecutive_checks'] = int(monitor['check_gpu_power_consecutive_checks'])
            if 'check_directory_recheck_delay' in monitor:
                monitor['check_directory_recheck_delay'] = int(monitor['check_directory_recheck_delay'])
            
            # 验证 webhook 配置
            webhook = config.get('webhook', {})
            if 'enabled' in webhook:
                webhook['enabled'] = bool(webhook['enabled'])
                
            return True
            
        except (ValueError, TypeError) as e:
            logger.error(f"配置验证失败: {str(e)}")
            return False
    
    def list_configs(self) -> list:
        """
        列出所有已保存的配置文件
        
        Returns:
            配置文件名列表
        """
        configs = []
        if os.path.exists(self.config_dir):
            for filename in os.listdir(self.config_dir):
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    configs.append(filename)
        return configs
