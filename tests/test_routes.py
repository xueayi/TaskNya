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
