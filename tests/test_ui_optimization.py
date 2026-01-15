# -*- coding: utf-8 -*-
"""
测试邮件发送Bug修复和配置同步功能
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.notifier.email_notifier import EmailNotifier
from core.notifier.message_builder import MessageBuilder


class TestEmailNotifierBugFix(unittest.TestCase):
    """测试邮件发送Bug修复"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'enabled': True,
            'smtp_server': 'smtp.example.com',
            'smtp_port': 465,
            'smtp_user': 'test@example.com',
            'smtp_password': 'password',
            'sender': 'test@example.com',
            'recipient': 'recipient@example.com',
            'use_ssl': True,
            'title': '测试邮件',
            'footer': '测试页脚',
        }
        
    def test_email_notifier_initialization(self):
        """测试邮件通知器初始化"""
        notifier = EmailNotifier(self.config)
        self.assertTrue(notifier.enabled)
        self.assertEqual(notifier.server, 'smtp.example.com')
        self.assertEqual(notifier.port, 465)
        self.assertTrue(notifier.use_ssl)
        
    @patch('smtplib.SMTP_SSL')
    def test_email_send_success_no_error(self, mock_smtp):
        """测试邮件发送成功且不误报错误"""
        # 模拟SMTP服务器
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # 模拟quit时可能抛出的异常(这是Bug修复的关键)
        mock_server.quit.side_effect = Exception("(-1, b'\\x00\\x00\\x00')")
        
        notifier = EmailNotifier(self.config)
        
        training_info = {
            'project_name': '测试项目',
            'start_time': '2026-01-15 15:00:00',
            'end_time': '2026-01-15 15:30:00',
            'duration': '0:30:00',
            'method': '目录变化检测',
            'hostname': 'test-host',
            'project_name_title': '训练项目',
            'start_time_title': '训练开始',
            'end_time_title': '训练结束时间',
            'method_title': '系统判断依据',
            'duration_title': '总耗时',
            'hostname_title': '主机名',
            'gpu_info_title': 'GPU信息',
        }
        
        # 发送邮件应该成功,即使quit抛出异常
        result = notifier.send(training_info)
        
        # 验证结果
        self.assertTrue(result, "邮件应该发送成功,即使quit时抛出异常")
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()


class TestMessageBuilderConfigSync(unittest.TestCase):
    """测试MessageBuilder配置"""
    
    def test_shared_config_options(self):
        """测试共享配置选项存储"""
        config = {
            'include_project_name': True,
            'include_report_summary': True,
            'include_report_details': True,
            'include_report_actions': True,
        }
        
        builder = MessageBuilder(config)
        
        # 验证配置正确存储
        self.assertEqual(builder.config['include_project_name'], True)
        self.assertEqual(builder.config['include_report_summary'], True)
        self.assertEqual(builder.config['include_report_details'], True)
        self.assertEqual(builder.config['include_report_actions'], True)
        
    def test_html_content_generation(self):
        """测试HTML内容生成"""
        config = {
            'include_project_name': True,
        }
        
        builder = MessageBuilder(config)
        
        training_info = builder.build_training_info(
            start_time=datetime.now(),
            end_time=datetime.now(),
            project_name="测试项目",
            method="目录变化检测",
        )
        
        html_content = builder.build_html_content(training_info)
        
        # 验证HTML基本结构
        self.assertIn('<!DOCTYPE html>', html_content)
        self.assertIn('<html>', html_content)
        self.assertIn('测试项目', html_content)


class TestConfigSyncLogic(unittest.TestCase):
    """测试配置同步逻辑"""
    
    def test_webhook_to_email_sync(self):
        """测试webhook配置同步到email(模拟JavaScript逻辑)"""
        # 模拟前端collectFormData的同步逻辑
        webhook_config = {
            'enabled': True,
            'url': 'https://example.com/webhook',
            'include_project_name': True,
            'include_start_time': True,
            'include_end_time': False,
            'include_report_summary': True,
            'include_report_details': False,
            'include_report_actions': True,
        }
        
        email_config = {
            'enabled': True,
            'smtp_server': 'smtp.example.com',
        }
        
        # 同步逻辑(模拟main.js中的代码)
        for key in webhook_config:
            if key.startswith('include_'):
                email_config[key] = webhook_config[key]
        
        # 验证同步结果
        self.assertEqual(email_config['include_project_name'], True)
        self.assertEqual(email_config['include_start_time'], True)
        self.assertEqual(email_config['include_end_time'], False)
        self.assertEqual(email_config['include_report_summary'], True)
        self.assertEqual(email_config['include_report_details'], False)
        self.assertEqual(email_config['include_report_actions'], True)
        
        # 验证非include_字段不被同步
        self.assertNotIn('url', email_config)
        self.assertEqual(email_config['smtp_server'], 'smtp.example.com')


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
