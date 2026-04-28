# -*- coding: utf-8 -*-
"""
API 被动触发服务

在 CLI 模式下启动轻量 HTTP 服务器，接收外部 POST 请求直接触发通知。
"""

import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class TriggerHandler(BaseHTTPRequestHandler):
    """处理触发请求的 HTTP handler"""

    def do_POST(self):
        if self.path != '/api/trigger':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not Found"}')
            return

        auth_token = self.server.auth_token
        if auth_token:
            auth_header = self.headers.get('Authorization', '')
            if auth_header != f'Bearer {auth_token}':
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b'{"error": "Unauthorized"}')
                return

        content_length = int(self.headers.get('Content-Length', 0))
        body = {}
        if content_length > 0:
            try:
                raw = self.rfile.read(content_length)
                body = json.loads(raw.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        try:
            callback = self.server.trigger_callback
            if callback:
                callback(body)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(
                json.dumps({"status": "ok", "message": "通知已触发"}).encode('utf-8')
            )
        except Exception as e:
            logger.error("触发回调执行失败: %s", e)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def do_GET(self):
        """健康检查"""
        if self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        logger.debug("API触发服务: %s", format % args)


class ApiTriggerServer:
    """API 触发服务管理器"""

    def __init__(
        self,
        port: int,
        auth_token: str = "",
        trigger_callback: Optional[Callable] = None,
    ):
        self.port = port
        self.auth_token = auth_token
        self.trigger_callback = trigger_callback
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """启动 API 触发服务"""
        try:
            self._server = HTTPServer(('0.0.0.0', self.port), TriggerHandler)
            self._server.auth_token = self.auth_token
            self._server.trigger_callback = self.trigger_callback

            self._thread = threading.Thread(
                target=self._server.serve_forever, daemon=True
            )
            self._thread.start()
            logger.info("API 触发服务已启动，监听端口: %s", self.port)
            logger.info("触发地址: POST http://0.0.0.0:%s/api/trigger", self.port)
        except OSError as e:
            logger.error(
                "API 触发服务启动失败（端口 %s 可能被占用）: %s", self.port, e
            )

    def stop(self):
        """停止 API 触发服务"""
        if self._server:
            self._server.shutdown()
            logger.info("API 触发服务已停止")
