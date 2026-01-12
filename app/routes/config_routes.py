# -*- coding: utf-8 -*-
"""
配置管理 API 路由

提供配置的获取、保存、加载、应用等接口。
"""

import os
import yaml
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

# 导入核心模块
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.config import ConfigManager

logger = logging.getLogger(__name__)

# 创建蓝图
config_bp = Blueprint('config', __name__, url_prefix='/api')

# 路径配置
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'configs')
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, 'default.yaml')

# 配置管理器实例
_config_manager = ConfigManager(config_dir=CONFIG_DIR)


@config_bp.route('/config', methods=['GET'])
def get_config():
    """
    获取当前配置
    
    Returns:
        JSON: 当前配置字典
    """
    config = _config_manager.load_config()
    return jsonify(config)


@config_bp.route('/configs', methods=['GET'])
def list_configs():
    """
    列出所有保存的配置文件
    
    Returns:
        JSON: 配置文件名列表
    """
    configs = _config_manager.list_configs()
    return jsonify(configs)


@config_bp.route('/config/save', methods=['POST'])
def save_config():
    """
    保存配置到新文件
    
    Request Body:
        name: 配置名称
        config: 配置字典
        
    Returns:
        JSON: 保存结果
    """
    try:
        data = request.json
        config_name = data.get('name', '').strip()
        config_data = data.get('config', {})
        
        if not config_name:
            return jsonify({
                'status': 'error',
                'message': '配置名称不能为空'
            }), 400
        
        # 验证配置
        if not ConfigManager.validate_config(config_data):
            return jsonify({
                'status': 'error',
                'message': '配置数据类型无效'
            }), 400
        
        # 清理文件名
        safe_name = "".join(c for c in config_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            return jsonify({
                'status': 'error',
                'message': '配置名称包含无效字符'
            }), 400
        
        # 添加时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_name}_{timestamp}.yaml"
        
        if _config_manager.save_config(config_data, filename):
            # 同时更新默认配置
            _config_manager.save_config(config_data, 'default.yaml')
            
            return jsonify({
                'status': 'success',
                'message': '配置已保存',
                'filename': filename
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '保存配置失败'
            }), 500
            
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@config_bp.route('/config/load/<filename>', methods=['GET'])
def load_saved_config(filename):
    """
    加载指定配置文件
    
    Args:
        filename: 配置文件名
        
    Returns:
        JSON: 加载的配置
    """
    try:
        config_path = os.path.join(CONFIG_DIR, filename)
        config = _config_manager.load_config(config_path)
        
        if config:
            # 同时更新默认配置
            _config_manager.save_config(config, 'default.yaml')
            logger.info(f"已加载配置: {filename}")
            
            return jsonify({
                'status': 'success',
                'config': config
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '无法加载配置文件'
            }), 404
            
    except Exception as e:
        logger.error(f"加载配置失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@config_bp.route('/config/apply', methods=['POST'])
def apply_config():
    """
    应用配置（更新默认配置文件）
    
    Request Body:
        config: 配置字典
        
    Returns:
        JSON: 应用结果
    """
    try:
        data = request.json
        config_data = data.get('config', {})
        
        # 验证配置
        if not ConfigManager.validate_config(config_data):
            return jsonify({
                'status': 'error',
                'message': '配置数据类型无效'
            }), 400
        
        # 保存到默认配置
        if _config_manager.save_config(config_data, 'default.yaml'):
            logger.info("已应用新配置")
            return jsonify({
                'status': 'success',
                'message': '配置已应用'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '应用配置失败'
            }), 500
            
    except Exception as e:
        logger.error(f"应用配置失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
