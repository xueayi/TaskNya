# -*- coding: utf-8 -*-
"""
监控控制 API 路由

提供监控的启动、停止等控制接口。
"""

import os
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

from core.config import ConfigManager
from core.notifier import (
    WebhookNotifier,
    GenericWebhookNotifier,
    EmailNotifier,
    WeComNotifier,
    MessageBuilder,
)

logger = logging.getLogger(__name__)

# 创建蓝图
monitor_bp = Blueprint('monitor', __name__, url_prefix='/api/monitor')
trigger_bp = Blueprint('trigger', __name__, url_prefix='/api')

# 路径配置
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'configs')
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, 'default.yaml')
MAIN_SCRIPT_PATH = os.path.join(PROJECT_ROOT, 'main.py')

# 全局状态（由 app.py 的 MonitorState 管理）
# 这里定义占位函数，实际由 app.py 初始化时注入
_monitor_state = None


def init_monitor_state(state):
    """
    初始化监控状态管理器
    
    Args:
        state: MonitorState 实例
    """
    global _monitor_state
    _monitor_state = state


@monitor_bp.route('/start', methods=['POST'])
def start_monitor():
    """
    启动监控
    
    Returns:
        JSON: 启动结果
    """
    if _monitor_state is None:
        return jsonify({
            'status': 'error',
            'message': '监控状态未初始化'
        }), 500
    
    if _monitor_state.is_running():
        return jsonify({
            'status': 'error',
            'message': '监控程序已在运行'
        }), 400
    
    try:
        if not os.path.exists(DEFAULT_CONFIG_PATH):
            return jsonify({
                'status': 'error',
                'message': '配置文件不存在'
            }), 400
        
        _monitor_state.start()
        logger.info("监控程序已启动")
        
        return jsonify({
            'status': 'success',
            'message': '监控程序已启动'
        })
        
    except Exception as e:
        logger.error(f"启动监控失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@monitor_bp.route('/stop', methods=['POST'])
def stop_monitor():
    """
    停止监控
    
    Returns:
        JSON: 停止结果
    """
    if _monitor_state is None:
        return jsonify({
            'status': 'error',
            'message': '监控状态未初始化'
        }), 500
    
    if not _monitor_state.is_running():
        return jsonify({
            'status': 'error',
            'message': '监控程序未在运行'
        }), 400
    
    try:
        success = _monitor_state.stop()
        
        if success:
            logger.info("监控程序已停止")
            return jsonify({
                'status': 'success',
                'message': '监控程序已停止'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '停止监控程序失败'
            }), 500
            
    except Exception as e:
        logger.error(f"停止监控失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@monitor_bp.route('/status', methods=['GET'])
def get_status():
    """
    获取监控状态
    
    Returns:
        JSON: 当前监控状态
    """
    if _monitor_state is None:
        return jsonify({
            'status': 'unknown',
            'running': False
        })
    
    return jsonify({
        'status': 'running' if _monitor_state.is_running() else 'stopped',
        'running': _monitor_state.is_running()
    })


@trigger_bp.route('/test-notification/<channel>', methods=['POST'])
def test_notification(channel):
    """
    测试指定通知渠道（无视 enabled 状态，使用请求体中的配置）

    URL 参数:
        channel: webhook | generic_webhook | email | wecom

    Body JSON:
        { "config": { ... 完整表单配置 ... } }
    """
    valid_channels = {'webhook', 'generic_webhook', 'email', 'wecom'}
    if channel not in valid_channels:
        return jsonify({
            'status': 'error',
            'message': f'无效的通知渠道: {channel}，可选: {", ".join(valid_channels)}'
        }), 400

    body = request.get_json(silent=True) or {}
    form_config = body.get('config', {})

    channel_config = dict(form_config.get(channel, {}))
    if not channel_config:
        config_manager = ConfigManager(config_dir=CONFIG_DIR)
        saved = config_manager.load_config()
        channel_config = dict(saved.get(channel, {}))

    channel_config['enabled'] = True

    webhook_config = form_config.get('webhook', channel_config)

    now = datetime.now()
    msg_builder = MessageBuilder(webhook_config if channel != 'generic_webhook' else channel_config)
    project_name = form_config.get('monitor', {}).get('project_name', '测试项目')
    training_info = msg_builder.build_training_info(
        start_time=now,
        end_time=now,
        project_name=project_name,
        method="测试发送",
        detail="通知渠道测试消息",
        gpu_info=None,
    )

    channel_names = {
        'webhook': '飞书 Webhook',
        'generic_webhook': '通用 Webhook',
        'email': '邮件',
        'wecom': '企业微信',
    }

    try:
        notifier_classes = {
            'webhook': WebhookNotifier,
            'generic_webhook': GenericWebhookNotifier,
            'email': EmailNotifier,
            'wecom': WeComNotifier,
        }

        notifier = notifier_classes[channel](channel_config)

        if not notifier.enabled:
            missing = []
            if channel == 'webhook' and not channel_config.get('url'):
                missing.append('Webhook URL')
            elif channel == 'generic_webhook' and not channel_config.get('url'):
                missing.append('Webhook URL')
            elif channel == 'email':
                if not channel_config.get('smtp_server'):
                    missing.append('SMTP 服务器')
                if not channel_config.get('smtp_user'):
                    missing.append('SMTP 用户名')
                if not channel_config.get('recipient'):
                    missing.append('收件人')
            elif channel == 'wecom' and not channel_config.get('url'):
                missing.append('Webhook URL')

            hint = f'缺少必要配置: {", ".join(missing)}' if missing else '配置不完整'
            return jsonify({
                'status': 'error',
                'message': f'{channel_names[channel]}测试失败: {hint}'
            }), 400

        success = notifier.send(training_info)

        if success:
            return jsonify({
                'status': 'success',
                'message': f'{channel_names[channel]}测试发送成功'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'{channel_names[channel]}测试发送失败，请检查日志'
            }), 500

    except Exception as e:
        logger.error(f"测试通知发送异常: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'{channel_names[channel]}测试异常: {str(e)}'
        }), 500


@trigger_bp.route('/trigger', methods=['POST'])
def trigger_notification():
    """
    手动触发通知

    接受 JSON body（可选）:
    {
        "message": "自定义消息",
        "project_name": "项目名"
    }
    """
    if _monitor_state is None:
        return jsonify({'status': 'error', 'message': '监控服务未初始化'}), 500

    body = request.get_json(silent=True) or {}

    config_manager = ConfigManager(config_dir=CONFIG_DIR)
    config = config_manager.load_config()

    auth_token = config.get('monitor', {}).get('check_api_auth_token', '')
    if auth_token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header != f'Bearer {auth_token}':
            return jsonify({'status': 'error', 'message': '认证失败'}), 401

    try:
        now = datetime.now()
        project_name = body.get('project_name', config['monitor']['project_name'])
        message = body.get('message', 'Web UI 手动触发通知')

        msg_builder = MessageBuilder(config.get('webhook', {}))
        training_info = msg_builder.build_training_info(
            start_time=now,
            end_time=now,
            project_name=project_name,
            method="手动触发",
            detail=message,
            gpu_info=None,
        )

        results = {}

        webhook = WebhookNotifier(config.get('webhook', {}))
        if webhook.enabled:
            results['webhook'] = webhook.send(training_info)

        generic = GenericWebhookNotifier(config.get('generic_webhook', {}))
        if generic.enabled:
            results['generic_webhook'] = generic.send(training_info)

        email = EmailNotifier(config.get('email', {}))
        if email.enabled:
            results['email'] = email.send(training_info)

        wecom = WeComNotifier(config.get('wecom', {}))
        if wecom.enabled:
            results['wecom'] = wecom.send(training_info)

        return jsonify({
            'status': 'success',
            'message': '通知已触发',
            'results': results,
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
