# -*- coding: utf-8 -*-
"""
通知模块测试

测试消息构建和 Webhook 通知功能。
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from core.notifier import MessageBuilder, WebhookNotifier


class TestMessageBuilder:
    """消息构建器测试"""
    
    def test_message_builder_basic(self, test_config):
        """测试基本消息构建"""
        builder = MessageBuilder(test_config['webhook'])
        
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 12, 30, 0)
        
        info = builder.build_training_info(
            start_time=start,
            end_time=end,
            project_name="测试项目",
            method="目标文件检测"
        )
        
        assert info['project_name'] == "测试项目"
        assert info['method'] == "目标文件检测"
        assert info['duration'] == "2:30:00"
        assert info['start_time'] == "2024-01-01 10:00:00"
    
    def test_message_builder_all_fields(self, test_config):
        """测试包含所有字段的消息"""
        builder = MessageBuilder(test_config['webhook'])
        
        start = datetime.now()
        end = datetime.now()
        
        info = builder.build_training_info(
            start_time=start,
            end_time=end,
            project_name="完整测试",
            method="日志检测",
            detail="训练完成",
            gpu_info="GPU 0: TEST"
        )
        
        assert 'keyword' in info
        assert info['keyword'] == "训练完成"
        assert 'gpu_info' in info
    
    def test_message_builder_optional_fields(self, test_config):
        """测试可选字段的处理"""
        builder = MessageBuilder(test_config['webhook'])
        
        start = datetime.now()
        end = datetime.now()
        
        # 文件检测类型
        info = builder.build_training_info(
            start_time=start,
            end_time=end,
            project_name="文件测试",
            method="目标文件检测",
            detail="/path/to/file.pth"
        )
        
        assert 'target_file' in info
        assert info['target_file'] == "/path/to/file.pth"
        assert 'keyword' not in info
    
    def test_build_message_content(self, test_config):
        """测试消息内容构建"""
        builder = MessageBuilder(test_config['webhook'])
        
        training_info = {
            'project_name': '测试',
            'start_time': '2024-01-01 10:00:00',
            'end_time': '2024-01-01 12:00:00',
            'duration': '2:00:00',
            'hostname': 'test-host',
            'method': '文件检测',
            'project_name_title': '项目',
            'start_time_title': '开始',
            'end_time_title': '结束',
            'method_title': '方式',
            'duration_title': '耗时',
            'hostname_title': '主机',
            'gpu_info_title': 'GPU'
        }
        
        content = builder.build_message_content(training_info)
        
        assert "任务已完成" in content
        assert "测试" in content
        assert "2:00:00" in content


class TestWebhookNotifier:
    """Webhook 通知器测试"""
    
    def test_webhook_notifier_success(self, test_config, mock_requests_post):
        """测试 Webhook 发送成功"""
        notifier = WebhookNotifier(test_config['webhook'])
        
        training_info = {
            'project_name': '测试',
            'start_time': '2024-01-01 10:00:00',
            'end_time': '2024-01-01 12:00:00',
            'duration': '2:00:00',
            'hostname': 'test',
            'method': '文件检测',
            'project_name_title': '项目',
            'start_time_title': '开始',
            'end_time_title': '结束',
            'method_title': '方式',
            'duration_title': '耗时',
            'hostname_title': '主机',
            'gpu_info_title': 'GPU'
        }
        
        result = notifier.send(training_info)
        
        assert result is True
        mock_requests_post.assert_called_once()
    
    def test_webhook_notifier_failure(self, test_config, mock_requests_post_failure):
        """测试 Webhook 发送失败处理"""
        notifier = WebhookNotifier(test_config['webhook'])
        
        training_info = {
            'project_name': '测试',
            'start_time': '2024-01-01 10:00:00',
            'end_time': '2024-01-01 12:00:00',
            'duration': '1:00:00',
            'hostname': 'test',
            'method': '文件检测',
            'project_name_title': '项目',
            'start_time_title': '开始',
            'end_time_title': '结束',
            'method_title': '方式',
            'duration_title': '耗时',
            'hostname_title': '主机',
            'gpu_info_title': 'GPU'
        }
        
        result = notifier.send(training_info)
        
        assert result is False
    
    def test_webhook_notifier_disabled(self):
        """测试 Webhook 禁用时的行为"""
        config = {
            'enabled': False,
            'url': 'https://test.url'
        }
        notifier = WebhookNotifier(config)
        
        assert notifier.enabled is False
        
        result = notifier.send({})
        assert result is False
    
    def test_webhook_notifier_empty_url(self):
        """测试 URL 为空时的行为"""
        config = {
            'enabled': True,
            'url': ''
        }
        notifier = WebhookNotifier(config)
        
        assert notifier.enabled is False
    
    def test_webhook_notifier_timeout(self, test_config):
        """测试请求超时处理"""
        import requests
        
        notifier = WebhookNotifier(test_config['webhook'])
        
        training_info = {
            'project_name': 'test',
            'start_time': '2024-01-01 10:00:00',
            'end_time': '2024-01-01 12:00:00',
            'duration': '2:00:00',
            'hostname': 'test',
            'method': '文件检测',
            'project_name_title': '项目',
            'start_time_title': '开始',
            'end_time_title': '结束',
            'method_title': '方式',
            'duration_title': '耗时',
            'hostname_title': '主机',
            'gpu_info_title': 'GPU'
        }
        
        with patch('requests.post', side_effect=requests.exceptions.Timeout):
            result = notifier.send(training_info)
            assert result is False
    
    def test_build_feishu_message(self, test_config):
        """测试飞书消息格式构建"""
        notifier = WebhookNotifier(test_config['webhook'])
        
        message = notifier._build_feishu_message("测试内容")
        
        assert message['msg_type'] == 'interactive'
        assert 'card' in message
        assert message['card']['header']['title']['content'] == test_config['webhook']['title']
