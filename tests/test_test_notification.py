# -*- coding: utf-8 -*-
"""
各通知器在测试模式（enabled=True）下缺少关键配置时的行为单元测试。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.notifier.webhook_notifier import WebhookNotifier
from core.notifier.email_notifier import EmailNotifier
from core.notifier.wecom_notifier import WeComNotifier
from core.notifier.generic_webhook_notifier import GenericWebhookNotifier


def test_webhook_notifier_enabled_but_no_url():
    """Webhook：配置 enabled=True 但 url 为空时，enabled 属性应为 False"""
    notifier = WebhookNotifier({"enabled": True, "url": ""})
    assert notifier._enabled is True
    assert notifier.enabled is False


def test_email_notifier_enabled_but_incomplete():
    """邮件：enabled=True 但缺少 smtp_server 时，enabled 属性应为 False"""
    notifier = EmailNotifier(
        {
            "enabled": True,
            "smtp_server": "",
            "smtp_user": "u@example.com",
            "recipient": "r@example.com",
        }
    )
    assert notifier._enabled is True
    assert notifier.enabled is False


def test_wecom_notifier_enabled_but_no_url():
    """企业微信：enabled=True 但 url 为空时，enabled 属性应为 False"""
    notifier = WeComNotifier({"enabled": True, "url": ""})
    assert notifier._enabled is True
    assert notifier.enabled is False


def test_generic_webhook_notifier_enabled_but_no_url():
    """通用 Webhook：enabled=True 但 url 为空时，enabled 属性应为 False"""
    notifier = GenericWebhookNotifier({"enabled": True, "url": ""})
    assert notifier._enabled is True
    assert notifier.enabled is False
