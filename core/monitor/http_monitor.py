# -*- coding: utf-8 -*-
"""
HTTP 轮询监控模块

定时发送 HTTP 请求，根据响应状态码和内容判断是否触发通知。
"""

import json
import logging
from typing import Tuple, Optional, Dict, Any

import requests

from core.monitor.base import BaseMonitor

logger = logging.getLogger(__name__)


class HttpMonitor(BaseMonitor):

    def __init__(self, config: Dict[str, Any]):
        self._enabled = config.get('check_http_enabled', False)
        self.url = config.get('check_http_url', '')
        self.method = config.get('check_http_method', 'GET').upper()
        self.headers = config.get('check_http_headers', {})
        self.body = config.get('check_http_body', '')
        self.expected_status = config.get('check_http_expected_status', 200)
        self.expected_keywords = config.get('check_http_expected_keywords', [])
        self.timeout = config.get('check_http_timeout', 10)

    @property
    def name(self) -> str:
        return "HTTP轮询监控"

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self.url)

    def check(self) -> Tuple[bool, str, Optional[str]]:
        if not self.enabled:
            return False, "未启用", None

        try:
            kwargs = {
                'headers': self.headers,
                'timeout': self.timeout,
            }

            if self.method in ('POST', 'PUT', 'PATCH') and self.body:
                try:
                    kwargs['json'] = json.loads(self.body)
                except (json.JSONDecodeError, TypeError):
                    kwargs['data'] = self.body

            response = requests.request(self.method, self.url, **kwargs)

            status_match = (response.status_code == self.expected_status)
            if not status_match:
                logger.debug(
                    "HTTP 状态码不匹配: 期望 %s, 实际 %s",
                    self.expected_status,
                    response.status_code,
                )
                return False, "状态码不匹配", None

            if self.expected_keywords:
                response_text = response.text
                for keyword in self.expected_keywords:
                    if keyword in response_text:
                        detail = (
                            f"HTTP {self.method} {self.url} -> {response.status_code}, "
                            f"关键词: {keyword}"
                        )
                        logger.info("HTTP 检测触发: %s", detail)
                        return True, "HTTP轮询检测", detail
                logger.debug("HTTP 响应中未找到期望关键词")
                return False, "关键词不匹配", None

            detail = f"HTTP {self.method} {self.url} -> {response.status_code}"
            logger.info("HTTP 检测触发: %s", detail)
            return True, "HTTP轮询检测", detail

        except requests.exceptions.Timeout:
            logger.debug("HTTP 请求超时: %s", self.url)
            return False, "请求超时", None
        except requests.exceptions.ConnectionError:
            logger.debug("HTTP 连接失败: %s", self.url)
            return False, "连接失败", None
        except Exception as e:
            logger.error("HTTP 检测异常: %s", str(e))
            return False, "检测异常", None

    def reset(self):
        pass
