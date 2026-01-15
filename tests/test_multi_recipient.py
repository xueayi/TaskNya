# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch, MagicMock
from core.notifier.email_notifier import EmailNotifier

class TestEmailNotifierMultiRecipient(unittest.TestCase):
    def setUp(self):
        self.config = {
            'enabled': True,
            'smtp_server': 'smtp.test.com',
            'smtp_port': 465,
            'smtp_user': 'test@test.com',
            'smtp_password': 'password',
            'sender': 'sender@test.com',
            'recipient': 'user1@test.com, user2@test.com; user3@test.com',
            'use_ssl': True,
            'title': 'Test Title',
            'footer': 'Test Footer'
        }

    @patch('smtplib.SMTP_SSL')
    def test_multi_recipient_parsing(self, mock_smtp):
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        notifier = EmailNotifier(self.config)
        training_info = {
            'project_name': 'Test Project',
            'start_time': '2026-01-15 10:00:00',
            'end_time': '2026-01-15 10:30:00',
            'duration': '0:30:00',
            'method': 'Test',
            'hostname': 'test-host',
            'project_name_title': 'Project',
            'start_time_title': 'Start',
            'end_time_title': 'End',
            'method_title': 'Method',
            'duration_title': 'Duration',
            'hostname_title': 'Host',
            'gpu_info_title': 'GPU'
        }
        
        result = notifier.send(training_info)
        
        self.assertTrue(result)
        
        # 验证解析后的收件人列表
        expected_recipients = ['user1@test.com', 'user2@test.com', 'user3@test.com']
        
        # 检查 sendmail 调用
        # args[0] 是 sender, args[1] 是 recipients 列表, args[2] 是 msg 字符串
        args, kwargs = mock_server.sendmail.call_args
        self.assertEqual(args[1], expected_recipients)
        
        # 验证邮件头中的 To
        msg_str = args[2]
        self.assertIn('To: user1@test.com, user2@test.com, user3@test.com', msg_str)

if __name__ == '__main__':
    unittest.main()
