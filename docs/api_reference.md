# TaskNya API 接口说明

## 1. Web API 接口

### 1.1 配置管理接口

#### GET /api/config
获取当前配置信息
- 响应：当前配置的JSON对象

#### POST /api/config/apply
应用新的配置
- 请求体：配置的JSON对象
- 响应：成功/失败状态

#### GET /api/config/list
获取可用配置文件列表
- 响应：配置文件列表

#### POST /api/config/save
保存当前配置
- 请求体：配置名称
- 响应：成功/失败状态

### 1.2 监控控制接口

#### POST /api/monitor/start
启动监控
- 响应：成功/失败状态

#### POST /api/monitor/stop
停止监控
- 响应：成功/失败状态

#### GET /api/monitor/status
获取监控状态
- 响应：当前监控状态

### 1.3 系统信息接口

#### GET /api/system/gpu
获取GPU信息
- 响应：GPU状态信息

## 2. WebSocket 接口

### 2.1 日志推送
- 路径：/ws/logs
- 功能：实时推送监控日志
- 消息格式：
  ```json
  {
    "type": "log",
    "content": "日志内容",
    "level": "info/warning/error",
    "timestamp": "时间戳"
  }
  ```

### 2.2 状态更新
- 路径：/ws/status
- 功能：推送监控状态更新
- 消息格式：
  ```json
  {
    "type": "status",
    "monitoring": true/false,
    "last_check": "最后检查时间",
    "trigger_type": "触发类型"
  }
  ```

## 3. 监控核心接口

### 3.1 TrainingMonitor 类
监控程序的核心类，提供以下方法：

#### start_monitoring()
启动监控任务
- 参数：无
- 返回：无

#### stop_monitoring()
停止监控任务
- 参数：无
- 返回：无

#### is_training_complete()
检查训练是否完成
- 参数：无
- 返回：bool，是否完成

#### check_file_exists()
检查目标文件是否存在
- 参数：无
- 返回：bool，文件是否存在

#### check_log_markers()
检查日志中是否包含完成标记
- 参数：无
- 返回：bool，是否找到标记

#### check_gpu_power()
检查GPU功耗是否低于阈值
- 参数：无
- 返回：bool，是否低于阈值

### 3.2 NotificationManager 类
通知管理类，处理消息发送：

#### send_notification()
发送通知
- 参数：
  - message: dict，消息内容
  - type: str，消息类型
- 返回：bool，发送是否成功

## 4. 错误代码说明

### 4.1 HTTP状态码
- 200: 请求成功
- 400: 请求参数错误
- 404: 资源不存在
- 500: 服务器内部错误

### 4.2 自定义错误码
- 1001: 配置验证失败
- 1002: 配置保存失败
- 2001: 监控启动失败
- 2002: 监控停止失败
- 3001: GPU信息获取失败
- 3002: 文件访问失败
- 3003: 日志读取失败 