# -*- coding: utf-8 -*-
"""
企业微信 Webhook 通知模块

通过企业微信群机器人 Webhook 发送通知。
支持 text 和 markdown 两种消息格式。
"""

import json
import logging
import re
from typing import Dict, Any

import requests

from core.notifier.base import BaseNotifier
from core.notifier.message_builder import MessageBuilder
from core.utils.anime_quote import get_anime_quote

logger = logging.getLogger(__name__)


class WeComNotifier(BaseNotifier):
    """
    企业微信 Webhook 通知器

    通过 HTTP POST 向企业微信群机器人 Webhook URL 发送通知。
    支持 text（纯文本）和 markdown 消息格式。
    """

    def __init__(self, wecom_config: Dict[str, Any]):
        self._enabled = wecom_config.get('enabled', False)
        self.url = wecom_config.get('url', '')
        self.msg_type = wecom_config.get('msg_type', 'markdown')
        self.custom_text_enabled = wecom_config.get('custom_text_enabled', False)
        self.custom_text_mode = wecom_config.get('custom_text_mode', 'template')
        self.custom_text = wecom_config.get('custom_text', '')
        self.message_builder = MessageBuilder(wecom_config)

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self.url)

    def send(self, training_info: Dict[str, Any]) -> bool:
        if not self.enabled:
            logger.info("企业微信通知已禁用或 URL 为空")
            return False

        content = self._build_content(training_info)
        message = self._build_wecom_message(content)

        try:
            response = requests.post(
                self.url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(message),
                timeout=10
            )

            if response.status_code == 200:
                resp_data = response.json()
                if resp_data.get("errcode", 0) == 0:
                    logger.info("成功发送通知到企业微信")
                    return True
                else:
                    logger.error(f"企业微信返回错误: {resp_data}")
                    return False
            else:
                logger.error(f"企业微信请求失败: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.Timeout:
            logger.error("企业微信通知发送超时")
            return False
        except Exception as e:
            logger.error(f"企业微信通知发送异常: {str(e)}")
            return False

    def _build_content(self, training_info: Dict[str, Any]) -> str:
        if self.custom_text_enabled and self.custom_text:
            context = self._build_context(training_info)
            custom = self._replace_variables(self.custom_text, context)

            if self.custom_text_mode == 'template':
                return custom
            else:
                default_content = self.message_builder.build_message_content(training_info)
                return default_content + "\n\n" + custom
        else:
            return self.message_builder.build_message_content(training_info)

    def _build_wecom_message(self, content: str) -> Dict[str, Any]:
        if self.msg_type == 'text':
            return {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
        else:
            return {
                "msgtype": "markdown",
                "markdown": {
                    "content": content
                }
            }

    def _build_context(self, training_info: Dict[str, Any]) -> Dict[str, str]:
        context = {
            "project_name": training_info.get("project_name", ""),
            "start_time": training_info.get("start_time", ""),
            "end_time": training_info.get("end_time", ""),
            "duration": training_info.get("duration", ""),
            "method": training_info.get("method", ""),
            "hostname": training_info.get("hostname", ""),
            "gpu_info": training_info.get("gpu_info", ""),
            "detail": training_info.get("detail", ""),
        }

        report = training_info.get("report", {})
        if report:
            context.update({
                "report_summary": report.get("summary", ""),
                "report_actions": ", ".join(report.get("actions", [])),
            })
            if report.get("summary"):
                context["detail"] = report["summary"]
        else:
            context["report_summary"] = "无"
            context["report_actions"] = "无"

        # 自动检测是否需要二次元语录
        if self.custom_text and '${anime_quote}' in self.custom_text:
            context["anime_quote"] = get_anime_quote()
        else:
            context["anime_quote"] = ""

        return context

    @staticmethod
    def _replace_variables(template: str, context: Dict[str, str]) -> str:
        def replace(match):
            var_name = match.group(1)
            return str(context.get(var_name, match.group(0)))
        return re.sub(r'\$\{(\w+)\}', replace, template)
