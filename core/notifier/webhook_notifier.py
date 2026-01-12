# -*- coding: utf-8 -*-
"""
Webhook 通知模块

通过 HTTP Webhook 发送通知消息。
当前支持飞书格式，可扩展支持其他平台。
"""

import json
import logging
import requests
from typing import Dict, Any

from core.notifier.base import BaseNotifier
from core.notifier.message_builder import MessageBuilder

logger = logging.getLogger(__name__)


class WebhookNotifier(BaseNotifier):
    """
    Webhook 通知器
    
    通过 HTTP POST 请求向 Webhook URL 发送通知。
    当前实现飞书消息格式，后续可扩展其他平台。
    
    Attributes:
        url (str): Webhook URL
        title (str): 消息标题
        color (str): 卡片颜色
        footer (str): 页脚文本
        message_builder (MessageBuilder): 消息构建器
    """
    
    def __init__(self, webhook_config: Dict[str, Any]):
        """
        初始化 Webhook 通知器
        
        Args:
            webhook_config: webhook 配置字典
        """
        self._enabled = webhook_config.get('enabled', False)
        self.url = webhook_config.get('url', '')
        self.title = webhook_config.get('title', '🎉 任务完成通知')
        self.color = webhook_config.get('color', 'green')
        self.footer = webhook_config.get('footer', '此消息由TaskNya发送')
        self.message_builder = MessageBuilder(webhook_config)
    
    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self.url)
    
    def send(self, training_info: Dict[str, Any]) -> bool:
        """
        发送通知
        
        Args:
            training_info: 任务信息字典
            
        Returns:
            bool: 发送是否成功
        """
        if not self.enabled:
            logger.info("Webhook通知已禁用或URL为空")
            return False
        
        # 构建消息内容
        content = self.message_builder.build_message_content(training_info)
        
        # 构建飞书消息格式
        message = self._build_feishu_message(content)
        
        try:
            response = requests.post(
                self.url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(message),
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("成功发送通知到飞书")
                return True
            else:
                logger.error(f"发送通知失败: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("发送通知超时")
            return False
        except Exception as e:
            logger.error(f"发送通知时发生异常: {str(e)}")
            return False
    
    def _build_feishu_message(self, content: str) -> Dict[str, Any]:
        """
        构建飞书消息格式
        
        Args:
            content: 消息正文内容
            
        Returns:
            飞书消息字典
        """
        return {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": self.title
                    },
                    "template": self.color
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": content
                        }
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": self.footer
                            }
                        ]
                    }
                ]
            }
        }
