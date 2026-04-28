# -*- coding: utf-8 -*-
"""
企业微信 Webhook 通知器单元测试
"""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from core.notifier.wecom_notifier import WeComNotifier


@pytest.fixture
def wecom_config_base():
    """企业微信测试用基础配置（与 conftest test_config 中 webhook 风格一致）"""
    return {
        "enabled": True,
        "url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test-key",
        "msg_type": "markdown",
        "custom_text_enabled": False,
        "custom_text_mode": "template",
        "custom_text": "",
        "title": "",
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
        "footer": "",
    }


@pytest.fixture
def training_info():
    """简单训练信息字典（与 test_email_notifier 等一致的结构）"""
    return {
        "project_name": "测试项目",
        "start_time": "2024-01-01 10:00:00",
        "end_time": "2024-01-01 12:00:00",
        "duration": "2:00:00",
        "hostname": "test-host",
        "method": "文件检测",
        "project_name_title": "项目",
        "start_time_title": "开始",
        "end_time_title": "结束",
        "method_title": "方式",
        "duration_title": "耗时",
        "hostname_title": "主机",
        "gpu_info_title": "GPU",
    }


def _decode_post_body(mock_post):
    kwargs = mock_post.call_args.kwargs
    raw = kwargs.get("data")
    if raw is None and mock_post.call_args[1]:
        raw = mock_post.call_args[1].get("data")
    return json.loads(raw)


class TestWeComNotifier:
    """WeComNotifier 测试"""

    def test_wecom_disabled(self, wecom_config_base):
        """禁用时 enabled 为 False"""
        cfg = {**wecom_config_base, "enabled": False}
        notifier = WeComNotifier(cfg)
        assert notifier.enabled is False

    def test_wecom_empty_url(self, wecom_config_base):
        """URL 为空时 enabled 为 False"""
        cfg = {**wecom_config_base, "url": ""}
        notifier = WeComNotifier(cfg)
        assert notifier.enabled is False

    @patch("core.notifier.wecom_notifier.requests.post")
    def test_wecom_send_markdown_success(
        self, mock_post, wecom_config_base, training_info
    ):
        """markdown 模式发送成功（200 + errcode:0）"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errcode": 0}
        mock_post.return_value = mock_resp

        notifier = WeComNotifier(wecom_config_base)
        assert notifier.send(training_info) is True
        mock_post.assert_called_once()
        sent = _decode_post_body(mock_post)
        assert sent["msgtype"] == "markdown"
        assert "测试项目" in sent["markdown"]["content"]

    @patch("core.notifier.wecom_notifier.requests.post")
    def test_wecom_send_text_success(
        self, mock_post, wecom_config_base, training_info
    ):
        """text 模式发送成功"""
        cfg = {**wecom_config_base, "msg_type": "text"}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errcode": 0}
        mock_post.return_value = mock_resp

        notifier = WeComNotifier(cfg)
        assert notifier.send(training_info) is True
        sent = _decode_post_body(mock_post)
        assert sent["msgtype"] == "text"
        assert "测试项目" in sent["text"]["content"]

    @patch("core.notifier.wecom_notifier.requests.post")
    def test_wecom_send_failure(self, mock_post, wecom_config_base, training_info):
        """服务端返回错误 errcode"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errcode": 93000, "errmsg": "invalid"}
        mock_post.return_value = mock_resp

        notifier = WeComNotifier(wecom_config_base)
        assert notifier.send(training_info) is False

    @patch("core.notifier.wecom_notifier.requests.post")
    def test_wecom_send_timeout(self, mock_post, wecom_config_base, training_info):
        """超时处理"""
        mock_post.side_effect = requests.exceptions.Timeout()

        notifier = WeComNotifier(wecom_config_base)
        assert notifier.send(training_info) is False

    @patch("core.notifier.wecom_notifier.requests.post")
    def test_wecom_custom_text_template(
        self, mock_post, wecom_config_base, training_info
    ):
        """自定义文本 template 模式"""
        cfg = {
            **wecom_config_base,
            "custom_text_enabled": True,
            "custom_text_mode": "template",
            "custom_text": "自定义模板: ${project_name}",
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errcode": 0}
        mock_post.return_value = mock_resp

        notifier = WeComNotifier(cfg)
        assert notifier.send(training_info) is True
        content = _decode_post_body(mock_post)["markdown"]["content"]
        assert content == "自定义模板: 测试项目"

    @patch("core.notifier.wecom_notifier.requests.post")
    def test_wecom_custom_text_append(
        self, mock_post, wecom_config_base, training_info
    ):
        """自定义文本 append 模式"""
        cfg = {
            **wecom_config_base,
            "custom_text_enabled": True,
            "custom_text_mode": "append",
            "custom_text": "追加一行",
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errcode": 0}
        mock_post.return_value = mock_resp

        notifier = WeComNotifier(cfg)
        assert notifier.send(training_info) is True
        content = _decode_post_body(mock_post)["markdown"]["content"]
        assert content.endswith("追加一行")
        assert "追加一行" in content
        assert "测试项目" in content

    @patch("core.notifier.wecom_notifier.get_anime_quote", return_value="测试二次元语录")
    @patch("core.notifier.wecom_notifier.requests.post")
    def test_wecom_anime_quote_auto_detect(
        self, mock_post, _mock_quote, wecom_config_base, training_info
    ):
        """自定义文本中包含 ${anime_quote} 时自动获取"""
        cfg = {
            **wecom_config_base,
            "custom_text_enabled": True,
            "custom_text_mode": "template",
            "custom_text": "名言: ${anime_quote}",
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errcode": 0}
        mock_post.return_value = mock_resp

        notifier = WeComNotifier(cfg)
        assert notifier.send(training_info) is True
        content = _decode_post_body(mock_post)["markdown"]["content"]
        assert "测试二次元语录" in content

    @patch("core.notifier.wecom_notifier.requests.post")
    def test_wecom_variable_replacement(
        self, mock_post, wecom_config_base, training_info
    ):
        """${var} 变量替换正确"""
        cfg = {
            **wecom_config_base,
            "custom_text_enabled": True,
            "custom_text_mode": "template",
            "custom_text": "${project_name}|${hostname}|${duration}|${method}",
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errcode": 0}
        mock_post.return_value = mock_resp

        notifier = WeComNotifier(cfg)
        assert notifier.send(training_info) is True
        content = _decode_post_body(mock_post)["markdown"]["content"]
        assert content == "测试项目|test-host|2:00:00|文件检测"

    @patch("core.notifier.wecom_notifier.requests.post")
    def test_wecom_title_footer_markdown(
        self, mock_post, wecom_config_base, training_info
    ):
        """markdown 模式下标题与页脚包装"""
        cfg = {
            **wecom_config_base,
            "title": "任务完成通知",
            "footer": "来自 TaskNya",
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errcode": 0}
        mock_post.return_value = mock_resp

        notifier = WeComNotifier(cfg)
        assert notifier.send(training_info) is True
        content = _decode_post_body(mock_post)["markdown"]["content"]
        assert content.startswith("## 任务完成通知\n\n")
        assert "来自 TaskNya" in content
