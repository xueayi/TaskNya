# TaskNya CLI 使用指南

## 启动监控

```bash
python main.py                              # 默认配置 configs/default.yaml
python main.py --config configs/my.yaml     # 指定配置
```

## 手动触发

`--trigger` 会**跳过全部监控逻辑**，不向监控器轮询检测；而是按当前配置**直接走一遍「发送通知」流程**，效果类似任务被判定为结束时的一次性通知。**只会向配置文件里「已启用」的通知渠道投递**（飞书 Webhook、通用 Webhook、邮件、企业微信等，依你在 YAML 中的开关为准）。

适合在流水线、运维脚本或本机场景中，在**无须常驻监控进程**的前提下发一次通知，例如：**部署上线完成**、里程碑节点、或对「整套已启用渠道的正式通知链路」做一次手动物理触发。

```bash
python main.py --trigger                           # 默认配置
python main.py --trigger --config configs/my.yaml  # 指定配置
python main.py --trigger --message "部署完成"       # 自定义消息文案
python main.py --trigger --config prod.yaml --message "训练任务已由 CI 收口"
```

> **`--message` 与内联变量**：`--message` 的文本会填充到 `${detail}` 变量中。如果你的通用 Webhook Body 模板中使用了 `${detail}`，它将显示 `--message` 的内容；其他渠道（飞书/企业微信/邮件）如果启用了自定义文本且使用了 `${detail}`，同样可以展示该消息。详见 [内联变量参考](inline_variables.md)。

## 测试通知渠道

`--test-channel` 用于**单独调试某一类通知渠道的连通性与展示效果**。程序不会启动监控循环，只对选中的渠道（或全部）做一次测试投递。

**参数取值**（任选其一）：

| 取值 | 说明 |
|------|------|
| `webhook` | 飞书 Webhook |
| `generic_webhook` | 通用 Webhook |
| `email` | 邮件（SMTP） |
| `wecom` | 企业微信 |
| `all` | 以上渠道各测一遍（配置了才会实际发送对应渠道） |

**行为要点**：

- **与「启用」开关无关**：测试路径会按需临时视为已启用，**只要在配置里填好了该渠道的必填项**，就会尝试发送；便于在渠道尚未勾选「启用」时先验收。
- 可配合 **`--message`** 自定义测试文案（未指定时使用内置默认测试说明）。
- 可配合 **`--config`** 指定 YAML，与启动监控、手动触发一致。

**示例**：

```bash
# 使用默认 configs/default.yaml，仅测飞书
python main.py --test-channel webhook

# 指定配置文件，测通用 Webhook
python main.py --test-channel generic_webhook --config configs/staging.yaml

# 测邮件，并自定义正文
python main.py --test-channel email --message "SMTP 与模板自检"

# 测企业微信
python main.py --test-channel wecom

# 依次测试（配置里写全了的）所有渠道
python main.py --test-channel all

# 组合：自定义配置 + 自定义消息 + 全渠道冒烟
python main.py --test-channel all --config configs/prod.yaml --message "生产环境渠道连通性检查"
```

在 **Web UI** 中，各通知区块旁有 **「测试」** 按钮：会用**当前表单里已填写的配置**发起一次测试请求（通过 `/api/test-notification/<channel>`），**无需先点击保存**；与 CLI 的 `--test-channel` 目的一致，只是配置来源为页面表单而非 YAML 文件。

## Web UI

```bash
python webui.py                     # 默认端口 9870
python webui.py --port 8080         # 自定义端口
python webui.py --debug             # 调试模式
```

## 后台运行（Linux/macOS）

```bash
bash manage_webui.sh start          # 默认端口 9870 启动
bash manage_webui.sh start 8080     # 指定端口 8080 启动
bash manage_webui.sh stop           # 停止
bash manage_webui.sh restart        # 重启（默认端口）
bash manage_webui.sh restart 8080   # 指定端口重启
bash manage_webui.sh status         # 查看状态
```

## Windows 启动

```bash
start_webui.bat                     # 默认端口 9870
start_webui.bat 8080                # 指定端口 8080
```

## 快捷启动脚本

```bash
bash run_monitor.sh                       # 交互选择配置文件
bash run_monitor.sh --config my.yaml      # 直接指定
bash run_monitor.sh --port 8080           # 指定 API 触发端口
```

## 被动触发（API 端口）

在配置中启用 `check_api_enabled` 后，CLI 模式自动监听指定端口（默认 9870）。路径与 Web UI 模式完全一致。

```bash
# 触发通知
curl -X POST http://localhost:9870/api/trigger \
  -H "Content-Type: application/json" \
  -d '{"message": "训练完成"}'

# 带认证
curl -X POST http://localhost:9870/api/trigger \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "CI/CD 部署完成", "project_name": "MyApp"}'

# 健康检查
curl http://localhost:9870/api/health
```

## Docker

```bash
docker compose up -d                # 启动
docker compose down                 # 停止
docker compose logs -f              # 查看日志
```

## 配置文件

所有功能通过 YAML 配置文件驱动，与 Web UI 使用相同的配置格式。

- 默认配置: `configs/default.yaml`
- 可通过 Web UI 创建配置后，用 `--config` 在 CLI 中加载
