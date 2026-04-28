# TaskNya CLI 使用指南

## 启动监控

```bash
python main.py                              # 默认配置 configs/default.yaml
python main.py --config configs/my.yaml     # 指定配置
```

## 手动触发通知

跳过检测流程，直接发送一次通知（用于测试通知渠道）。

```bash
python main.py --trigger                           # 默认配置
python main.py --trigger --config configs/my.yaml  # 指定配置
python main.py --trigger --message "部署完成"       # 自定义消息
```

## Web UI

```bash
python webui.py                     # 默认端口 9870
python webui.py --port 8080         # 自定义端口
python webui.py --debug             # 调试模式
```

## 后台运行（Linux/macOS）

```bash
bash manage_webui.sh start          # 启动
bash manage_webui.sh stop           # 停止
bash manage_webui.sh restart        # 重启
bash manage_webui.sh status         # 查看状态
```

## 快捷启动脚本

```bash
bash run_monitor.sh                 # 交互选择配置文件
bash run_monitor.sh --config my.yaml  # 直接指定
```

## 被动触发（API 端口）

在配置中启用 `check_api_enabled` 后，CLI 模式自动监听 9870 端口。

```bash
# 触发通知
curl -X POST http://localhost:9870/trigger

# 带认证和自定义消息
curl -X POST http://localhost:9870/trigger \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "CI/CD 部署完成", "project_name": "MyApp"}'

# 健康检查
curl http://localhost:9870/health
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
