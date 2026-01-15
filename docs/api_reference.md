# TaskNya API 参考

[项目主页](../README.md) | [用户指南](user_guide.md) | [开发手册](DEVELOPMENT.md)

> 版本: 2.1.0  
> 更新日期: 2026-01-15

---

## 目录

- [Web REST API](#1-web-rest-api)
    - [配置管理](#11-配置管理)
    - [监控状态控制](#12-监控控制)
- [WebSocket 实时推送](#2-websocket-接口)
- [核心类接口 (Python)](#3-核心模块接口)

---

## 1. Web REST API

基础 URL: `http://<host>:<port>/api`

### 1.1 配置管理

#### `GET /config`
获取后端当前正在运行的完整配置字典。

#### `POST /config/apply`
实时应用传入的配置，不保存到磁盘。
- **Payload**: `{"config": { ... }}`

#### `GET /configs`
列出 `configs/` 目录下所有的 `.yaml` 文件名。

#### `POST /config/save`
将当前配置持久化到磁盘。
- **Payload**: `{"name": "config_name", "config": { ... }}`

#### `GET /config/load/<filename>`
从指定文件加载配置。

---

### 1.2 监控控制

#### `POST /monitor/start`
初始化并启动监控后台任务。

#### `POST /monitor/stop`
强制停止当前的监控任务。

#### `GET /monitor/status`
获取当前监控器的活跃状态。
- **Response**: `{"status": "running" | "stopped", "running": bool}`

---

## 2. WebSocket 接口

用于前端实时获取监控日志和状态变更。

- **Endpoint**: `/ws`
- **消息格式**: JSON

### 2.1 推送消息类型

| 类型 | 示例 | 场景 |
| :--- | :--- | :--- |
| `log` | `{"type": "log", "message": "..."}` | 监控进度更新 |
| `status` | `{"type": "status", "data": {"status": "running"}}` | 任务起止状态同步 |
| `ping` | `{"type": "ping"}` | 心跳包 |

---

## 3. 核心模块接口

如果你希望将 TaskNya 作为库集成到自己的脚本中，可以调用以下核心类。

### 3.1 `MonitorManager`
监控逻辑的聚合者，负责按需调用各监控器。

```python
from core.monitor import MonitorManager
manager = MonitorManager(config)
triggered, method, detail = manager.check()
```

### 3.2 `ConfigManager`
配置系统的门面，支持合并与校验。

```python
from core.config import ConfigManager, DEFAULT_CONFIG
manager = ConfigManager(config_dir="./configs")
# 自动补全缺失字段
full_config = manager.merge_config(user_data, DEFAULT_CONFIG)
```

---

## 4. 响应规范

所有接口均返回标准 JSON 结构：

- **成功**: `{"status": "success", "data": ...}`
- **失败**: `{"status": "error", "message": "Reason"}`

---

*更多底层细节请参考代码中的 Docstrings。*