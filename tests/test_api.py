# -*- coding: utf-8 -*-
"""
Web API 测试

测试 Flask 应用的 API 接口。
"""

import os
import sys
import pytest
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import app


@pytest.fixture
def client():
    """Flask 测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def runner():
    """Flask CLI 运行器"""
    return app.test_cli_runner()


class TestConfigAPI:
    """配置 API 测试"""
    
    def test_get_config(self, client):
        """测试 GET /api/config"""
        response = client.get('/api/config')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'monitor' in data or data is None
    
    def test_apply_config(self, client, test_config):
        """测试 POST /api/config/apply"""
        response = client.post(
            '/api/config/apply',
            data=json.dumps({'config': test_config}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_apply_config_invalid(self, client):
        """测试应用无效配置"""
        invalid_config = {
            'monitor': {
                'check_interval': 'not_a_number'
            }
        }
        
        response = client.post(
            '/api/config/apply',
            data=json.dumps({'config': invalid_config}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_list_configs(self, client):
        """测试 GET /api/configs"""
        response = client.get('/api/configs')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_save_config(self, client, test_config):
        """测试 POST /api/config/save"""
        response = client.post(
            '/api/config/save',
            data=json.dumps({
                'name': 'test_save',
                'config': test_config
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_save_config_empty_name(self, client, test_config):
        """测试保存空名称配置"""
        response = client.post(
            '/api/config/save',
            data=json.dumps({
                'name': '',
                'config': test_config
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestMonitorAPI:
    """监控 API 测试"""
    
    def test_start_monitor(self, client):
        """测试 POST /api/monitor/start"""
        response = client.post('/api/monitor/start')
        
        # 可能成功启动或已在运行
        assert response.status_code in [200, 400]
    
    def test_stop_monitor(self, client):
        """测试 POST /api/monitor/stop"""
        response = client.post('/api/monitor/stop')
        
        # 可能成功停止或未在运行
        assert response.status_code in [200, 400]
    
    def test_start_stop_cycle(self, client):
        """测试启动-停止周期"""
        # 先尝试停止（确保干净状态）
        client.post('/api/monitor/stop')
        
        # 启动
        start_response = client.post('/api/monitor/start')
        if start_response.status_code == 200:
            # 如果启动成功，尝试停止
            import time
            time.sleep(1)  # 等待线程启动
            
            stop_response = client.post('/api/monitor/stop')
            assert stop_response.status_code == 200


class TestIndexPage:
    """主页测试"""
    
    def test_index_page(self, client):
        """测试主页访问"""
        response = client.get('/')
        
        assert response.status_code == 200
        # 检查返回的是 HTML
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data
    
    def test_index_page_content(self, client):
        """测试主页内容"""
        response = client.get('/')
        
        # 检查页面包含关键元素
        html = response.data.decode('utf-8')
        assert 'TaskNya' in html or 'tasknya' in html.lower()
