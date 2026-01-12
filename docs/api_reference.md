# TaskNya API 接口说明

## 1. Web API 接口

### 1.1 配置管理接口

#### GET /api/config
获取当前配置信息

**响应示例：**
```json
{
  "monitor": {
    "project_name": "深度学习训练",
    "check_interval": 5,
    "check_file_enabled": true,
    "check_file_path": "./output/model_final.pth"
  },
  "webhook": {
    "enabled": true,
    "url": "https://webhook.example.com/hook"
  }
}
```

#### POST /api/config/apply
应用新的配置

**请求体：**
```json
{
  "config": {
    "monitor": {...},
    "webhook": {...}
  }
}
```

**响应：**
```json
{
  "status": "success",
  "message": "配置已应用"
}
```

#### GET /api/configs
获取可用配置文件列表

**响应：**
```json
["default.yaml", "my_config_20240101.yaml"]
```

#### POST /api/config/save
保存配置到文件

**请求体：**
```json
{
  "name": "my_config",
  "config": {...}
}
```

**响应：**
```json
{
  "status": "success",
  "message": "配置已保存",
  "filename": "my_config_20240101_120000.yaml"
}
```

#### GET /api/config/load/{filename}
加载指定配置文件

**响应：**
```json
{
  "status": "success",
  "config": {...}
}
```

---

### 1.2 监控控制接口

#### POST /api/monitor/start
启动监控

**响应：**
```json
{
  "status": "success",
  "message": "监控程序已启动"
}
```

#### POST /api/monitor/stop
停止监控

**响应：**
```json
{
  "status": "success",
  "message": "监控程序已停止"
}
```

#### GET /api/monitor/status
获取监控状态

**响应：**
```json
{
  "status": "running",
  "running": true
}
```

---

## 2. WebSocket 接口

### 2.1 连接地址
```
ws://localhost:5000/ws
```

### 2.2 消息类型

#### 日志消息
```json
{
  "type": "log",
  "message": "2024-01-01 12:00:00 - INFO - 开始监控任务..."
}
```

#### 状态消息
```json
{
  "type": "status",
  "data": {
    "status": "running"
  }
}
```

#### 心跳消息
```json
{
  "type": "ping"
}
```

---

## 3. 核心模块接口

### 3.1 TrainingMonitor 类

监控程序的核心门面类，提供以下方法：

```python
from main import TrainingMonitor

# 初始化
monitor = TrainingMonitor(config_path='config.yaml')

# 属性
monitor.config       # 配置字典
monitor.start_time   # 监控开始时间
monitor.should_stop  # 停止检查回调函数
```

#### is_training_complete()
检查任务是否完成

```python
flag, method, detail = monitor.is_training_complete()
# flag: bool - 是否完成
# method: str - 触发方式 ("目标文件检测"/"日志检测"/"GPU功耗检测")
# detail: str - 详细信息
```

#### send_notification(training_info)
发送通知

```python
success = monitor.send_notification({
    'project_name': '我的项目',
    'duration': '2:30:00',
    ...
})
```

#### get_gpu_info()
获取 GPU 信息

```python
info_str = monitor.get_gpu_info()
# 返回格式化的 GPU 信息字符串
```

#### start_monitoring()
启动监控（阻塞直到任务完成或超时）

```python
monitor.start_monitoring()
```

---

### 3.2 ConfigManager 类

配置管理器，负责配置的加载、保存、合并和验证。

```python
from core.config import ConfigManager

manager = ConfigManager(config_dir='./configs')

# 加载配置
config = manager.load_config('my_config.yaml')

# 保存配置
manager.save_config(config, 'backup.yaml')

# 合并配置
merged = ConfigManager.merge_config(user_config, default_config)

# 验证配置
is_valid = ConfigManager.validate_config(config)

# 列出配置文件
configs = manager.list_configs()
```

---

### 3.3 监控器类

所有监控器继承自 `BaseMonitor` 抽象基类：

```python
from core.monitor import FileMonitor, LogMonitor, GpuMonitor, MonitorManager

# 创建监控器
file_monitor = FileMonitor(config['monitor'])
log_monitor = LogMonitor(config['monitor'])
gpu_monitor = GpuMonitor(config['monitor'])

# 执行检查
triggered, method, detail = file_monitor.check()

# 使用管理器统一管理
manager = MonitorManager(config)
triggered, method, detail = manager.check()  # 任一触发返回 True
```

---

### 3.4 通知器类

```python
from core.notifier import WebhookNotifier, MessageBuilder

# 消息构建器
builder = MessageBuilder(config['webhook'])
training_info = builder.build_training_info(
    start_time=start,
    end_time=end,
    project_name='项目名',
    method='文件检测'
)

# Webhook 通知器
notifier = WebhookNotifier(config['webhook'])
success = notifier.send(training_info)
```

---

## 4. 错误响应

### 4.1 HTTP 状态码

| 状态码 | 说明                           |
| ------ | ------------------------------ |
| 200    | 请求成功                       |
| 400    | 请求参数错误（如配置验证失败） |
| 404    | 资源不存在（如配置文件不存在） |
| 500    | 服务器内部错误                 |

### 4.2 错误响应格式

```json
{
  "status": "error",
  "message": "错误描述信息"
}
```

---

## 5. 调试接口说明

### 5.1 日志级别

在调试模式下，可以使用以下日志级别：

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("调试信息 - 仅在 DEBUG 级别显示")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 5.2 开启详细日志

在配置中启用：

```yaml
monitor:
  logprint: 10  # 每 10 秒输出一次状态日志
```

或在代码中：

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```