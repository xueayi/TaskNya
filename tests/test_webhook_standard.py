# -*- coding: utf-8 -*-
import json
import pytest
from unittest.mock import MagicMock, patch

from core.notifier.generic_webhook_notifier import GenericWebhookNotifier

class TestGenericWebhookNotifier:
    
    @pytest.fixture
    def config(self):
        return {
            "enabled": True,
            "url": "http://example.com/webhook",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": "",
            "builtin_template": None,
            "retry_count": 0,
            "timeout": 5,
            "anime_quote_enabled": False,
            "astrbot_mode": False
        }

    @pytest.fixture
    def training_info(self):
        return {
            "project_name": "TestProject",
            "start_time": "2023-01-01 10:00:00",
            "end_time": "2023-01-01 10:05:00",
            "duration": "0:05:00",
            "method": "文件检测",
            "hostname": "TestHost",
            "gpu_info": "GPU: 0%",
            "detail": "output.txt"
        }

    def test_init_defaults(self):
        notifier = GenericWebhookNotifier({})
        assert not notifier.enabled
        assert notifier.method == "POST"
        
    def test_send_basic(self, config, training_info):
        notifier = GenericWebhookNotifier(config)
        
        with patch('requests.request') as mock_request:
            mock_request.return_value.status_code = 200
            
            success = notifier.send(training_info)
            
            assert success
            mock_request.assert_called_once()
            args, kwargs = mock_request.call_args
            assert args[0] == "POST"
            assert kwargs['url'] == "http://example.com/webhook"
            
            body = json.loads(kwargs['data'])
            assert "TestProject" in body['content']

    def test_variables_replacement(self, config, training_info):
        config["body"] = '{"message": "Project ${project_name} finished in ${duration}"}'
        notifier = GenericWebhookNotifier(config)
        
        with patch('requests.request') as mock_request:
            mock_request.return_value.status_code = 200
            notifier.send(training_info)
            
            kwargs = mock_request.call_args[1]
            body = json.loads(kwargs['data'])
            assert body['message'] == "Project TestProject finished in 0:05:00"

    def test_astrbot_mode(self, config, training_info):
        config["astrbot_mode"] = True
        config["astrbot_umo"] = "Bot:Group:123"
        config["astrbot_content"] = "Project ${project_name} Done"
        notifier = GenericWebhookNotifier(config)
        
        with patch('requests.request') as mock_request:
            mock_request.return_value.status_code = 200
            notifier.send(training_info)
            
            kwargs = mock_request.call_args[1]
            body = json.loads(kwargs['data'])
            
            # AstrBot specific fields
            assert body['umo'] == "Bot:Group:123"
            assert body['message_type'] == "text"
            # Check content formatting
            assert "📢 [ 文件变动 ]" in body['content']
            assert "Project TestProject Done" in body['content']
            assert "━━━━━━━━━━━━━━" in body['content']

    def test_directory_report_variables(self, config):
        """测试目录监控报告变量"""
        config["body"] = '{"summary": "${report_summary}", "added": "${report_added_list}", "actions": "${report_actions}"}'
        notifier = GenericWebhookNotifier(config)
        
        # 模拟包含 report 的 training_info
        info = {
            "project_name": "Test",
            "report": {
                "summary": "新增 1, 删除 0",
                "total_changes": 1,
                "added_count": 1,
                "added_files": [
                    {"path": "new_file.txt", "size_str": "1 KB", "action": "备份", "is_dir": False}
                ],
                "removed_files": [],
                "modified_files": [],
                "actions": ["备份"]
            }
        }
        
        with patch('requests.request') as mock_request:
            mock_request.return_value.status_code = 200
            notifier.send(info)
            
            kwargs = mock_request.call_args[1]
            body = json.loads(kwargs['data'])
            
            assert body['summary'] == "新增 1, 删除 0"
            assert "new_file.txt" in body['added']
            assert "备份" not in body['added']  # 确认已从中移除
            assert body['actions'] == "备份"  # 确认在聚合变量中
