# -*- coding: utf-8 -*-
"""
WebSocket 模块测试

测试 WebSocket 管理器和消息处理。
"""

import pytest
import queue
import logging
from unittest.mock import MagicMock, patch
import json

from app.websocket import WebSocketManager, WebSocketLogHandler


class TestWebSocketLogHandler:
    """WebSocket 日志处理器测试"""
    
    def test_emit_success(self):
        """测试日志消息发送到队列"""
        msg_queue = queue.Queue()
        handler = WebSocketLogHandler(msg_queue)
        handler.setFormatter(logging.Formatter('%(message)s'))
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='测试消息',
            args=(),
            exc_info=None
        )
        
        handler.emit(record)
        
        assert not msg_queue.empty()
        message = msg_queue.get()
        assert '测试消息' in message
    
    def test_emit_error_handling(self):
        """测试错误处理"""
        # 创建一个会抛异常的队列
        msg_queue = MagicMock()
        msg_queue.put.side_effect = Exception("Queue error")
        
        handler = WebSocketLogHandler(msg_queue)
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='测试',
            args=(),
            exc_info=None
        )
        
        # 不应该抛出异常
        handler.emit(record)


class TestWebSocketManager:
    """WebSocket 管理器测试"""
    
    def test_add_remove_client(self):
        """测试添加和移除客户端"""
        manager = WebSocketManager()
        
        mock_client = MagicMock()
        
        manager.add_client(mock_client)
        assert mock_client in manager.clients
        
        manager.remove_client(mock_client)
        assert mock_client not in manager.clients
    
    def test_remove_nonexistent_client(self):
        """测试移除不存在的客户端"""
        manager = WebSocketManager()
        mock_client = MagicMock()
        
        # 不应该抛出异常
        manager.remove_client(mock_client)
    
    def test_broadcast(self):
        """测试消息广播"""
        manager = WebSocketManager()
        
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        
        manager.add_client(mock_client1)
        manager.add_client(mock_client2)
        
        manager.broadcast('test', {'key': 'value'})
        
        mock_client1.send.assert_called_once()
        mock_client2.send.assert_called_once()
        
        # 验证消息格式
        sent_msg = mock_client1.send.call_args[0][0]
        data = json.loads(sent_msg)
        assert data['type'] == 'test'
        assert data['data']['key'] == 'value'
    
    def test_broadcast_removes_dead_clients(self):
        """测试广播时移除断开的客户端"""
        manager = WebSocketManager()
        
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        mock_client2.send.side_effect = Exception("Connection closed")
        
        manager.add_client(mock_client1)
        manager.add_client(mock_client2)
        
        manager.broadcast('test', {})
        
        # client2 应该被移除
        assert mock_client1 in manager.clients
        assert mock_client2 not in manager.clients
    
    def test_broadcast_status(self):
        """测试状态广播"""
        manager = WebSocketManager()
        
        manager.broadcast_status('running')
        
        assert not manager.message_queue.empty()
        message = manager.message_queue.get()
        assert message['type'] == 'status'
        assert message['data']['status'] == 'running'
    
    def test_get_log_handler(self):
        """测试获取日志处理器"""
        manager = WebSocketManager()
        
        handler = manager.get_log_handler()
        
        assert isinstance(handler, WebSocketLogHandler)
        assert handler.message_queue is manager.message_queue
    
    def test_handle_connection_not_connected(self):
        """测试处理未连接的 WebSocket"""
        manager = WebSocketManager()
        
        mock_ws = MagicMock()
        mock_ws.connected = False
        
        manager.handle_connection(mock_ws, lambda: 'stopped')
        
        assert mock_ws not in manager.clients


class TestMonitorState:
    """监控状态管理器测试"""
    
    def test_is_running_false_initially(self):
        """测试初始状态为未运行"""
        from app.app import MonitorState
        
        ws_manager = WebSocketManager()
        state = MonitorState(ws_manager)
        
        assert state.is_running() is False
    
    def test_start_stop(self):
        """测试启动和停止"""
        from app.app import MonitorState
        
        ws_manager = WebSocketManager()
        state = MonitorState(ws_manager)
        
        # Mock _run_monitor 以避免实际运行
        with patch.object(state, '_run_monitor'):
            state.start()
            # 由于线程立即结束，is_running 可能返回 False
            # 这里主要测试不抛异常
            
            state.stop()
            assert state.is_running() is False
