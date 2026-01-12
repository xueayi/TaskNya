# -*- coding: utf-8 -*-
"""
pytest 配置文件

包含测试用的 fixtures 和配置。
"""

import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def project_root():
    """项目根目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def temp_dir():
    """创建临时目录，测试后自动清理"""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def temp_config_file(temp_dir):
    """创建临时配置文件"""
    config_content = """
monitor:
  project_name: "测试项目"
  check_interval: 1
  timeout: 10
  logprint: 5
  check_file_enabled: true
  check_file_path: "./test_output.txt"
  check_log_enabled: false
  check_gpu_power_enabled: false

webhook:
  enabled: false
  url: ""
"""
    config_path = os.path.join(temp_dir, 'test_config.yaml')
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    return config_path


@pytest.fixture
def temp_log_file(temp_dir):
    """创建临时日志文件"""
    log_path = os.path.join(temp_dir, 'test.log')
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("程序启动\n")
        f.write("正在处理...\n")
    return log_path


@pytest.fixture
def test_config():
    """测试用配置字典"""
    return {
        "monitor": {
            "project_name": "监控任务",
            "check_interval": 60,
            "timeout": 0,
            "logprint": 60,
            "check_file_enabled": True,
            "check_file_path": "/tmp/test_file.txt",
            "check_log_enabled": True,
            "check_log_path": "/tmp/test.log",
            "check_log_markers": ["完成", "done"],
            "check_log_mode": "full",
            "check_gpu_power_enabled": False,
            "check_gpu_power_threshold": 50.0,
            "check_gpu_power_gpu_ids": "all",
            "check_gpu_power_consecutive_checks": 3
        },
        "webhook": {
            "enabled": True,
            "url": "https://test.webhook.url/hook",
            "title": "测试通知",
            "color": "green",
            "include_project_name": True,
            "include_project_name_title": "项目",
            "include_start_time": True,
            "include_start_time_title": "开始",
            "include_end_time": True,
            "include_end_time_title": "结束",
            "include_method": True,
            "include_method_title": "方式",
            "include_duration": True,
            "include_duration_title": "耗时",
            "include_hostname": True,
            "include_hostname_title": "主机",
            "include_gpu_info": False,
            "include_gpu_info_title": "GPU",
            "footer": "测试消息"
        }
    }


@pytest.fixture
def mock_nvidia_smi():
    """Mock nvidia-smi 命令输出"""
    mock_output = "0, 45.00\n1, 30.00\n"
    with patch('subprocess.check_output', return_value=mock_output):
        yield


@pytest.fixture
def mock_nvidia_smi_high_power():
    """Mock nvidia-smi 高功耗输出"""
    mock_output = "0, 150.00\n1, 180.00\n"
    with patch('subprocess.check_output', return_value=mock_output):
        yield


@pytest.fixture
def mock_requests_post():
    """Mock requests.post"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"ok": true}'
    
    with patch('requests.post', return_value=mock_response) as mock_post:
        yield mock_post


@pytest.fixture
def mock_requests_post_failure():
    """Mock requests.post 失败"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = 'Internal Server Error'
    
    with patch('requests.post', return_value=mock_response) as mock_post:
        yield mock_post
