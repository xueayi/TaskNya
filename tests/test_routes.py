# -*- coding: utf-8 -*-
"""
路由模块测试

测试配置和监控路由。
"""

import os
import sys
import pytest
import json
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app_client(temp_dir):
    """创建测试客户端"""
    from app.app import create_app
    
    # 设置临时配置目录
    os.environ['TASKNYA_CONFIG_DIR'] = temp_dir
    
    app = create_app()
    app.config['TESTING'] = True
    
    # 创建默认配置
    default_config = {
        'monitor': {
            'project_name': '测试项目',
            'check_interval': 5,
            'check_file_enabled': True,
            'check_file_path': '/tmp/test.txt'
        },
        'webhook': {
            'enabled': False
        }
    }
    
    import yaml
    config_path = os.path.join(temp_dir, 'default.yaml')
    os.makedirs(temp_dir, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, allow_unicode=True)
    
    with app.test_client() as client:
        yield client


class TestConfigRoutes:
    """配置路由测试"""
    
    def test_get_config(self, app_client):
        """测试获取配置"""
        response = app_client.get('/api/config')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'monitor' in data
    
    def test_list_configs(self, app_client):
        """测试列出配置"""
        response = app_client.get('/api/configs')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_save_config_success(self, app_client, test_config):
        """测试保存配置成功"""
        response = app_client.post(
            '/api/config/save',
            data=json.dumps({
                'name': 'test_config',
                'config': test_config
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_save_config_empty_name(self, app_client, test_config):
        """测试空名称保存失败"""
        response = app_client.post(
            '/api/config/save',
            data=json.dumps({
                'name': '',
                'config': test_config
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_save_config_invalid_name(self, app_client, test_config):
        """测试无效名称保存失败"""
        response = app_client.post(
            '/api/config/save',
            data=json.dumps({
                'name': '!!!###',
                'config': test_config
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_apply_config_success(self, app_client, test_config):
        """测试应用配置成功"""
        response = app_client.post(
            '/api/config/apply',
            data=json.dumps({
                'config': test_config
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_apply_config_invalid(self, app_client):
        """测试应用无效配置"""
        response = app_client.post(
            '/api/config/apply',
            data=json.dumps({
                'config': {
                    'monitor': {
                        'check_interval': 'invalid'
                    }
                }
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestMonitorRoutes:
    """监控路由测试"""
    
    def test_get_status(self, app_client):
        """测试获取状态"""
        response = app_client.get('/api/monitor/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert 'running' in data
    
    def test_start_monitor(self, app_client):
        """测试启动监控"""
        response = app_client.post('/api/monitor/start')
        
        # 可能成功或失败，取决于配置
        assert response.status_code in [200, 400, 500]
    
    def test_stop_monitor_not_running(self, app_client):
        """测试停止未运行的监控"""
        response = app_client.post('/api/monitor/stop')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'


class TestIndexRoute:
    """主页路由测试"""
    
    def test_index_page_loads(self, app_client):
        """测试主页加载"""
        response = app_client.get('/')
        
        assert response.status_code == 200
    
    def test_index_page_content(self, app_client):
        """测试主页内容"""
        response = app_client.get('/')
        
        html = response.data.decode('utf-8')
        # 应该包含 HTML 结构
        assert '<html' in html or '<!DOCTYPE' in html


class TestNotificationTestRoutes:
    """通知渠道测试 API：POST /api/test-notification 加渠道名路径参数"""

    def test_test_notification_invalid_channel(self, app_client):
        """无效渠道名应返回 400"""
        response = app_client.post(
            "/api/test-notification/not_a_channel",
            data=json.dumps({"config": {"monitor": {"project_name": "测试"}}}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "无效的通知渠道" in data["message"]

    def test_test_notification_webhook_missing_url(self, app_client):
        """webhook 缺少 URL 时应返回 400 并提示 Webhook URL"""
        response = app_client.post(
            "/api/test-notification/webhook",
            data=json.dumps(
                {
                    "config": {
                        "webhook": {"url": ""},
                        "monitor": {"project_name": "测试"},
                    }
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "Webhook URL" in data["message"] or "缺少必要配置" in data["message"]

    def test_test_notification_email_missing_config(self, app_client):
        """email 缺少必要配置时应返回 400"""
        response = app_client.post(
            "/api/test-notification/email",
            data=json.dumps(
                {
                    "config": {
                        "email": {
                            "smtp_user": "user@example.com",
                            "recipient": "to@example.com",
                        },
                        "monitor": {"project_name": "测试"},
                    }
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "SMTP 服务器" in data["message"]

    def test_test_notification_webhook_success(self, app_client, mock_requests_post):
        """有效 webhook 配置且 requests.post 成功时应返回 200"""
        response = app_client.post(
            "/api/test-notification/webhook",
            data=json.dumps(
                {
                    "config": {
                        "webhook": {
                            "url": "https://example.com/feishu-hook",
                            "title": "测试",
                        },
                        "monitor": {"project_name": "测试"},
                    }
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        mock_requests_post.assert_called()

    def test_test_notification_generic_webhook_success(self, app_client):
        """有效 generic_webhook 配置时应返回 200（实现使用 requests.request）"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        with patch("requests.request", return_value=mock_response) as mock_req:
            response = app_client.post(
                "/api/test-notification/generic_webhook",
                data=json.dumps(
                    {
                        "config": {
                            "generic_webhook": {
                                "url": "https://example.com/generic-hook",
                                "method": "POST",
                            },
                            "monitor": {"project_name": "测试"},
                        }
                    }
                ),
                content_type="application/json",
            )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        mock_req.assert_called()
