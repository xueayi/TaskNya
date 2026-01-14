# -*- coding: utf-8 -*-
import os
import time
import threading
import pytest
from main import TrainingMonitor
from core.config import DEFAULT_CONFIG

def test_monitor_stop_responsiveness():
    """测试监控程序是否能响应停止信号"""
    # 使用一个小时间片作为检查间隔
    config = DEFAULT_CONFIG.copy()
    config['monitor']['check_interval'] = 5  # 5秒检查一次
    config['monitor']['logprint'] = 1
    config['monitor']['project_name'] = "TestStop"
    config['monitor']['check_file_enabled'] = False
    config['monitor']['check_log_enabled'] = False
    config['monitor']['check_gpu_power_enabled'] = False
    config['monitor']['check_directory_enabled'] = False
    
    # 强制不启用任何监控器，这样 check() 会立即返回 False
    
    monitor = TrainingMonitor()
    monitor.config = config
    
    # 模拟停止信号
    stop_flag = False
    def should_stop_stub():
        return stop_flag
    
    monitor.should_stop = should_stop_stub
    
    # 在线程中运行监控
    monitor_thread = threading.Thread(target=monitor.start_monitoring)
    monitor_thread.start()
    
    # 等待一会确保它在运行
    time.sleep(1)
    assert monitor_thread.is_alive()
    
    # 发送停止信号
    start_time = time.time()
    stop_flag = True
    
    # 等待监控线程退出
    monitor_thread.join(timeout=3)
    end_time = time.time()
    
    # 验证是否及时停止（应该在 3 秒内停止，尽管 check_interval 是 5 秒）
    assert not monitor_thread.is_alive(), "监控线程未能在超时时间内停止"
    assert end_time - start_time < 3, f"停止响应太慢: {end_time - start_time}s"

if __name__ == "__main__":
    pytest.main([__file__])
