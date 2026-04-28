# -*- coding: utf-8 -*-
"""
自定义文本（模板变量、飞书/邮件）相关测试
"""

from unittest.mock import patch

from core.notifier.email_notifier import EmailNotifier
from core.notifier.message_builder import MessageBuilder
from core.notifier.webhook_notifier import WebhookNotifier


def _sample_training_info():
    """最小可用的 training_info，供 build_context / 通知正文使用"""
    return {
        "project_name": "测试项目",
        "start_time": "2024-01-01 10:00:00",
        "end_time": "2024-01-01 11:00:00",
        "duration": "1:00:00",
        "method": "日志检测",
        "hostname": "test-host",
        "gpu_info": "",
        "detail": "keyword-hit",
        "project_name_title": "训练项目",
        "start_time_title": "训练开始",
        "end_time_title": "训练结束时间",
        "method_title": "系统判断依据",
        "duration_title": "总耗时",
        "hostname_title": "主机名",
        "gpu_info_title": "GPU信息",
    }


class TestCustomText:
    """自定义文本功能测试"""

    def test_message_builder_replace_variables(self):
        """测试变量替换基本功能"""
        template = "项目: ${project_name}, 主机: ${hostname}"
        context = {
            "project_name": "P1",
            "hostname": "h1",
            "anime_quote": "",
        }
        out = MessageBuilder.replace_variables(template, context)
        assert out == "项目: P1, 主机: h1"

    def test_message_builder_replace_unknown_variable(self):
        """未知变量应保留原样"""
        template = "已知: ${project_name}, 未知: ${not_a_real_key}"
        context = {"project_name": "X", "anime_quote": ""}
        out = MessageBuilder.replace_variables(template, context)
        assert out == "已知: X, 未知: ${not_a_real_key}"

    def test_message_builder_anime_quote_auto_detect(self):
        """包含 ${anime_quote} 时自动获取"""
        with patch(
            "core.notifier.message_builder.get_anime_quote",
            return_value="今日の勝利者はこの俺だ",
        ) as mock_quote:
            template = "名言: ${anime_quote}"
            out = MessageBuilder.replace_variables(template, {})
            mock_quote.assert_called_once()
        assert out == "名言: 今日の勝利者はこの俺だ"

    def test_message_builder_no_anime_quote(self):
        """不包含 ${anime_quote} 时不请求"""
        with patch(
            "core.notifier.message_builder.get_anime_quote",
        ) as mock_quote:
            template = "只有 ${project_name}"
            _ = MessageBuilder.replace_variables(
                template, {"project_name": "Y", "anime_quote": ""}
            )
            mock_quote.assert_not_called()

    def test_webhook_custom_text_template_mode(self):
        """飞书自定义文本 template 模式"""
        cfg = {
            "enabled": True,
            "url": "https://example.com/hook",
            "custom_text_enabled": True,
            "custom_text_mode": "template",
            "custom_text": "自定义: ${project_name} @ ${hostname}",
        }
        notifier = WebhookNotifier(cfg)
        content = notifier._build_content(_sample_training_info())
        assert "自定义: 测试项目 @ test-host" in content
        assert "**任务已完成！**" not in content

    def test_webhook_custom_text_append_mode(self):
        """飞书自定义文本 append 模式"""
        cfg = {
            "enabled": True,
            "url": "https://example.com/hook",
            "include_project_name": True,
            "custom_text_enabled": True,
            "custom_text_mode": "append",
            "custom_text": "尾部: ${method}",
        }
        notifier = WebhookNotifier(cfg)
        content = notifier._build_content(_sample_training_info())
        assert "**任务已完成！**" in content
        assert "尾部: 日志检测" in content
        assert content.index("**任务已完成！**") < content.index("尾部: 日志检测")

    def test_email_custom_text_template_mode(self):
        """邮件自定义文本 template 模式"""
        cfg = {
            "enabled": True,
            "smtp_server": "smtp.example.com",
            "smtp_user": "a@b.com",
            "recipient": "to@b.com",
            "custom_text_enabled": True,
            "custom_text_mode": "template",
            "custom_text": "邮件模板: ${project_name}",
        }
        notifier = EmailNotifier(cfg)
        html = notifier._build_email_content(_sample_training_info())
        assert "<html><body><pre>" in html
        assert "</pre></body></html>" in html
        assert "邮件模板: 测试项目" in html
        # template 模式应仅为 pre 包裹的自定义文本，不含完整 HTML 卡片结构
        assert 'class="header"' not in html
