# TaskNya API 参考

[项目主页](../README.md) | [用户指南](user_guide.md) | [CLI 使用指南](cli_usage.md) | [开发手册](DEVELOPMENT.md)

> 版本: 1.2.0
> 更新日期: 2026-04-28

---

## 目录

- [Web REST API](#1-web-rest-api)
    - [配置管理](#11-配置管理)
    - [监控控制](#12-监控控制)
    - [手动触发通知](#13-手动触发通知)
- [WebSocket 实时推送](#2-websocket-接口)
- [CLI 被动触发 API](#3-cli-被动触发-api)
- [核心类接口 (Python)](#4-核心模块接口)

---

## 1. Web REST API

基础 URL: `http://<host>:9870/api`

### 1.1 配置管理

#### `GET /api/config`

获取后端当前的完整配置字典。

**响应示例:**

```json
{"status": "success", "config": {"monitor": {...}, "webhook": {...}, ...}}
```

#### `POST /api/config/apply`

实时应用传入的配置（写入 `default.yaml`）。

**请求体:**

```json
{"config": {"monitor": {...}, "webhook": {...}, ...}}
```

#### `GET /api/configs`

列出 `configs/` 目录下所有 `.yaml` 文件名。

**响应示例:**

```json
["default.yaml", "my_project.yaml"]
```

#### `POST /api/config/save`

将配置持久化到指定文件。

**请求体:**

```json
{"name": "config_name", "config": {"monitor": {...}, ...}}
```

#### `GET /api/config/load/<filename>`

从指定文件加载配置并返回。

**响应示例:**

```json
{"status": "success", "config": {...}}
```

#### `DELETE /api/config/delete/<filename>`

删除指定配置文件（`default.yaml` 除外）。

---

### 1.2 监控控制

#### `POST /api/monitor/start`

启动监控后台任务。

**响应示例:**

```json
{"status": "success", "message": "监控已启动"}
```

#### `POST /api/monitor/stop`

停止当前的监控任务。

#### `GET /api/monitor/status`

获取当前监控器的运行状态。

**响应示例:**

```json
{"status": "running", "running": true}
```

---

### 1.3 手动触发通知

#### `POST /api/trigger`

跳过检测流程，直接向所有已启用的通知渠道发送通知。适用于 Web UI 手动触发或外部系统集成。

> Web UI 和 CLI 模式使用统一路径 `/api/trigger`，请求体和认证方式完全相同。
> Web UI 模式下随服务自动可用；CLI 模式需在配置中启用 `check_api_enabled`。

**请求头（可选）:**

```
Authorization: Bearer <token>
```

> 仅当配置了 `monitor.check_api_auth_token` 时需要。

**请求体（可选）:**

```json
{
    "message": "自定义消息内容",
    "project_name": "项目名称"
}
```

- `message` — 触发详情，默认 `"Web UI 手动触发通知"`
- `project_name` — 覆盖配置中的项目名称

**响应示例:**

```json
{
    "status": "success",
    "message": "通知已触发",
    "results": {
        "webhook": true,
        "email": true,
        "wecom": true,
        "generic_webhook": true
    }
}
```

**curl 示例:**

```bash
# 触发通知
curl -X POST http://localhost:9870/api/trigger \
  -H "Content-Type: application/json" \
  -d '{"message": "手动测试"}'

# 带认证
curl -X POST http://localhost:9870/api/trigger \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{"message": "手动测试", "project_name": "MyProject"}'
```

---

## 2. WebSocket 接口

用于前端实时获取监控日志和状态变更。

- **Endpoint**: `ws://<host>:9870/ws`
- **消息格式**: JSON

### 2.1 推送消息类型

| 类型 | 示例 | 场景 |
| :--- | :--- | :--- |
| `log` | `{"type": "log", "message": "..."}` | 监控进度/检测日志 |
| `status` | `{"type": "status", "data": {"status": "running"}}` | 任务起止状态同步 |
| `ping` | `{"type": "ping"}` | 心跳保活 |

---

## 3. CLI 被动触发 API

当配置中启用 `check_api_enabled` 后，CLI 模式（`main.py`）会在指定端口启动轻量 HTTP 服务，接收外部请求直接触发通知。

- **默认端口**: `9870`（配置项 `check_api_port`）
- **路径与 Web UI 完全一致**：`/api/trigger`、`/api/health`

### 3.1 触发通知

#### `POST /api/trigger`

请求格式与 [1.3 手动触发通知](#13-手动触发通知) 完全相同。

**响应:**

```json
{"status": "ok", "message": "通知已触发"}
```

**错误响应:**

| 状态码 | 含义 |
| :--- | :--- |
| 401 | Token 认证失败 |
| 404 | 路径不存在 |
| 500 | 回调执行异常 |

### 3.2 健康检查

#### `GET /api/health`

**响应:**

```json
{"status": "ok"}
```

**curl 示例:**

```bash
# 触发通知（CLI 和 Web UI 路径相同）
curl -X POST http://localhost:9870/api/trigger \
  -H "Content-Type: application/json" \
  -d '{"message": "训练完成"}'

# 健康检查
curl http://localhost:9870/api/health
```

---

## 4. 核心模块接口

如果你希望将 TaskNya 作为库集成到自己的脚本中，可以调用以下核心类。

### 4.1 `MonitorManager`

监控逻辑的聚合者，负责按需调用各监控器并返回检测结果。

```python
from core.monitor import MonitorManager

manager = MonitorManager(config['monitor'])
triggered, method, detail = manager.check()
```

内置监控器：

| 监控器 | 配置前缀 | 说明 |
| :--- | :--- | :--- |
| `FileMonitor` | `check_file_*` | 单文件存在/删除检测 |
| `LogMonitor` | `check_log_*` | 日志关键词检测（全量/增量） |
| `GpuMonitor` | `check_gpu_power_*` | GPU 功耗阈值检测 |
| `DirectoryMonitor` | `check_directory_*` | 目录文件变化检测 |
| `HttpMonitor` | `check_http_*` | HTTP 轮询检测 |

### 4.2 `ApiTriggerServer`

CLI 模式下的被动触发 HTTP 服务。

```python
from core.monitor.api_trigger import ApiTriggerServer

server = ApiTriggerServer(
    port=9870,
    auth_token="optional_token",
    trigger_callback=lambda body: print(body),
)
server.start()
# ... 后续逻辑 ...
server.stop()
```

### 4.3 `ConfigManager`

配置系统门面，支持加载、保存、合并与校验。

```python
from core.config import ConfigManager, DEFAULT_CONFIG

manager = ConfigManager(config_dir="./configs")
config = manager.load_config()
full_config = manager.merge_config(user_data, DEFAULT_CONFIG)
```

### 4.4 通知器

所有通知器继承相同接口，通过 `.send(training_info)` 发送通知。

```python
from core.notifier import WebhookNotifier, EmailNotifier, WeComNotifier, GenericWebhookNotifier

notifier = WebhookNotifier(config['webhook'])
if notifier.enabled:
    success = notifier.send(training_info)
```

| 通知器 | 配置节 | 说明 |
| :--- | :--- | :--- |
| `WebhookNotifier` | `webhook` | 飞书机器人（Interactive 卡片/Text） |
| `EmailNotifier` | `email` | SMTP 邮件通知 |
| `WeComNotifier` | `wecom` | 企业微信群机器人 |
| `GenericWebhookNotifier` | `generic_webhook` | 通用 HTTP Webhook |

---

## 5. 响应规范

所有 Web REST API 均返回标准 JSON 结构：

- **成功**: `{"status": "success", ...}`
- **失败**: `{"status": "error", "message": "Reason"}`

HTTP 状态码：

| 状态码 | 含义 |
| :--- | :--- |
| 200 | 操作成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

*更多底层细节请参考代码中的 Docstrings。*
