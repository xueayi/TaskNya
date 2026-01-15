# -*- coding: utf-8 -*-
"""
邮件通知器单元测试
"""

import pytest
from unittest.mock import patch, MagicMock
from core.notifier.email_notifier import EmailNotifier

@pytest.fixture
def email_config():
    return {
        "enabled": True,
        "smtp_server": "smtp.test.com",
        "smtp_port": 465,
        "smtp_user": "test@test.com",
        "smtp_password": "password",
        "sender": "test@test.com",
        "recipient": "recipient@test.com",
        "use_ssl": True,
        "title": "测试邮件",
        "footer": "测试页脚"
    }

class TestEmailNotifier:
    """EmailNotifier 测试"""
    
    def test_enabled_property(self, email_config):
        """测试 enabled 属性"""
        notifier = EmailNotifier(email_config)
        assert notifier.enabled is True
        
        # 测试缺少配置
        config_missing = email_config.copy()
        config_missing['smtp_server'] = ''
        notifier = EmailNotifier(config_missing)
        assert notifier.enabled is False
        
        # 测试禁用
        config_disabled = email_config.copy()
        config_disabled['enabled'] = False
        notifier = EmailNotifier(config_disabled)
        assert notifier.enabled is False

    @patch('smtplib.SMTP_SSL')
    def test_send_success(self, mock_smtp_ssl, email_config):
        """测试发送成功"""
        # 更加健壮的 mock 设置
        mock_server = MagicMock()
        mock_smtp_ssl.return_value = mock_server
        mock_server.__enter__.return_value = mock_server
        
        notifier = EmailNotifier(email_config)
        training_info = {
            'project_name': '测试项目',
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
        
        result = notifier.send(training_info)
        
        assert result is True
        # 检查是否调用了登录和发送
        mock_server.login.assert_called_with(email_config['smtp_user'], email_config['smtp_password'])
        assert mock_server.sendmail.called
        
    @patch('smtplib.SMTP_SSL')
    def test_send_failure(self, mock_smtp_ssl, email_config):
        """测试发送失败"""
        mock_smtp_ssl.side_effect = Exception("SMTP error")
        
        notifier = EmailNotifier(email_config)
        training_info = {
            'project_name': '测试项目',
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
        result = notifier.send(training_info)
        
        assert result is False

    @patch('smtplib.SMTP')
    def test_send_no_ssl(self, mock_smtp, email_config):
        """测试非 SSL 发送"""
        email_config['use_ssl'] = False
        email_config['smtp_port'] = 25
        
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        notifier = EmailNotifier(email_config)
        training_info = {
            'project_name': '测试项目',
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
        result = notifier.send(training_info)
        
        assert result is True
        mock_smtp.assert_called_with(email_config['smtp_server'], 25, timeout=30)
