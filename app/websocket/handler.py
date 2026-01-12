# -*- coding: utf-8 -*-
"""
WebSocket 处理模块

管理 WebSocket 连接、消息广播和日志推送。
"""

import json
import queue
import logging
import time
import threading
from datetime import datetime
from typing import Set, Any


class WebSocketLogHandler(logging.Handler):
    """
    日志处理器，将日志消息发送到队列
    
    用于在 WebSocket 中实时推送日志消息。
    """
    
    def __init__(self, message_queue: queue.Queue):
        """
        初始化日志处理器
        
        Args:
            message_queue: 消息队列
        """
        super().__init__()
        self.message_queue = message_queue
    
    def emit(self, record):
        """发送日志记录到队列"""
        try:
            log_entry = self.format(record)
            self.message_queue.put(log_entry)
        except Exception:
            self.handleError(record)


class WebSocketManager:
    """
    WebSocket 连接管理器
    
    管理所有 WebSocket 客户端连接，提供消息广播功能。
    
    Attributes:
        clients (Set): 连接的客户端集合
        message_queue (Queue): 消息队列
    """
    
    def __init__(self):
        """初始化 WebSocket 管理器"""
        self.clients: Set[Any] = set()
        self.message_queue = queue.Queue()
        self._lock = threading.Lock()
    
    def add_client(self, ws):
        """
        添加客户端
        
        Args:
            ws: WebSocket 连接对象
        """
        with self._lock:
            self.clients.add(ws)
    
    def remove_client(self, ws):
        """
        移除客户端
        
        Args:
            ws: WebSocket 连接对象
        """
        with self._lock:
            self.clients.discard(ws)
    
    def broadcast(self, message_type: str, data: Any):
        """
        广播消息给所有客户端
        
        Args:
            message_type: 消息类型
            data: 消息数据
        """
        message = json.dumps({
            'type': message_type,
            'data': data
        })
        
        dead_clients = set()
        
        with self._lock:
            for client in self.clients:
                try:
                    client.send(message)
                except Exception:
                    dead_clients.add(client)
            
            # 移除断开的客户端
            self.clients -= dead_clients
    
    def broadcast_status(self, status: str):
        """
        广播状态变更
        
        Args:
            status: 状态字符串 ('running' 或 'stopped')
        """
        message = {
            'type': 'status',
            'data': {'status': status}
        }
        self.message_queue.put(message)
    
    def handle_connection(self, ws, get_monitor_status):
        """
        处理 WebSocket 连接
        
        Args:
            ws: WebSocket 连接对象
            get_monitor_status: 获取监控状态的回调函数
        """
        logger = logging.getLogger(__name__)
        
        if not ws.connected:
            logger.warning("WebSocket连接未成功建立")
            return
        
        self.add_client(ws)
        last_ping = datetime.now()
        connection_active = True
        
        try:
            # 发送初始状态
            status = get_monitor_status()
            try:
                ws.send(json.dumps({
                    'type': 'status',
                    'data': {'status': status}
                }))
            except Exception as e:
                logger.error(f"发送初始状态失败: {str(e)}")
                return
            
            while connection_active and ws.connected:
                try:
                    # 心跳检测
                    now = datetime.now()
                    if (now - last_ping).total_seconds() > 30:
                        try:
                            ws.send(json.dumps({'type': 'ping'}))
                            last_ping = now
                        except Exception as e:
                            logger.warning(f"WebSocket心跳检测失败: {str(e)}")
                            break
                    
                    # 处理消息队列
                    messages_processed = 0
                    max_messages_per_batch = 10
                    
                    while messages_processed < max_messages_per_batch:
                        try:
                            log_message = self.message_queue.get_nowait()
                            
                            if not ws.connected:
                                break
                            
                            try:
                                if isinstance(log_message, dict) and log_message.get('type') == 'status':
                                    ws.send(json.dumps(log_message))
                                else:
                                    ws.send(json.dumps({
                                        'type': 'log',
                                        'message': log_message
                                    }))
                                messages_processed += 1
                            except Exception as e:
                                logger.error(f"发送消息失败: {str(e)}")
                                connection_active = False
                                break
                                
                        except queue.Empty:
                            break
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"消息处理循环出错: {str(e)}")
                    if not ws.connected:
                        break
                        
        except Exception as e:
            logger.error(f"WebSocket连接处理出错: {str(e)}")
        finally:
            self.remove_client(ws)
            if ws.connected:
                try:
                    ws.close()
                except Exception:
                    pass
            logger.info("WebSocket连接已清理完成")
    
    def get_log_handler(self) -> WebSocketLogHandler:
        """
        获取日志处理器
        
        Returns:
            配置好的日志处理器
        """
        handler = WebSocketLogHandler(self.message_queue)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        return handler
