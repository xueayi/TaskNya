# TaskNya 测试清单

## 按需模块显示

- [ ] enabled=false 的检测方法卡片初始隐藏【手动】
- [ ] 点击"添加检测方法"显示对应卡片【手动】
- [ ] 点击卡片移除按钮隐藏并取消 enabled【手动】
- [ ] 通知渠道同理：初始隐藏/添加/移除【手动】
- [ ] 保存配置后刷新，可见状态与 enabled 一致【手动】

## +号输入模式

- [ ] 触发关键词：添加/删除行正常工作【手动】
- [ ] 排除关键词：添加/删除行正常工作【手动】
- [ ] 操作建议：键值对行添加/删除正常【手动】
- [ ] 保存后加载配置，行数据正确恢复【手动】
- [ ] 收集的数据格式正确（数组/字典）【pytest: test_config.py】

## 企业微信一致性

- [ ] title/footer 字段在 UI 中显示【手动】
- [ ] 保存/加载正确持久化 title/footer【手动】
- [ ] markdown 模式推送包含标题和页脚【pytest: test_wecom_notifier.py】
- [ ] text 模式推送包含标题和页脚【pytest: test_wecom_notifier.py】

## 换行符全链路

- [ ] 通用 Webhook 字段编辑器：含 \n 的值正确显示为 \n 字面量【手动】
- [ ] 字段编辑器中输入 \n，保存后重新加载仍为 \n【手动】
- [ ] 通用 Webhook 预览中换行正确渲染【手动】
- [ ] 飞书/企微/邮件 textarea 多行文本保存/加载完整【手动】
- [ ] YAML 文件中多行字符串使用 block scalar【手动】

## 卡片预览

- [ ] 飞书预览：颜色条随 color 选择变化【手动】
- [ ] 飞书预览：标题/内容/页脚实时更新【手动】
- [ ] 企业微信预览：标题/内容/页脚实时更新【手动】
- [ ] 自定义文本 template 模式预览替换默认内容【手动】
- [ ] 自定义文本 append 模式预览追加内容【手动】
- [ ] ${var} 变量在预览中被示例值替换【手动】

## CLI 手动触发

- [ ] `python main.py --trigger` 使用默认配置发送通知【手动】
- [ ] `--trigger --config` 使用指定配置【手动】
- [ ] `--trigger --message "test"` 消息出现在通知中【手动】
- [ ] 各通道（飞书/企微/邮件/通用webhook）均正确发送【pytest: test_custom_text.py】

## HTTP 轮询检测

- [ ] HttpMonitor 状态码匹配时触发【pytest: test_http_monitor.py（待创建）】
- [ ] HttpMonitor 关键词匹配时触发【pytest: test_http_monitor.py】
- [ ] HttpMonitor 状态码不匹配时不触发【pytest: test_http_monitor.py】
- [ ] HttpMonitor 请求失败时不触发【pytest: test_http_monitor.py】
- [ ] HttpMonitor enabled=false 时不执行请求【pytest: test_http_monitor.py】

## API 被动触发

- [ ] CLI 模式启动后端口可达【手动】
- [ ] POST /trigger 返回 200 并发送通知【手动】
- [ ] GET /health 返回健康状态【手动】
- [ ] auth_token 验证生效（无 token 返回 401）【手动】
- [ ] Web UI 模式 POST /api/trigger 可用【手动】
- [ ] 自定义 payload 中的 message/project_name 生效【手动】

## 通知发送

- [ ] 飞书 Webhook 正确构建卡片 JSON【pytest: test_webhook_standard.py】
- [ ] 企业微信 markdown/text 格式正确【pytest: test_wecom_notifier.py】
- [ ] 邮件 HTML 模板渲染正确【pytest: test_email_notifier.py】
- [ ] 通用 Webhook 变量替换正确【pytest: test_notifier.py】
- [ ] 自定义文本 template/append 模式【pytest: test_custom_text.py】

## 脚本与文档

- [ ] `run_monitor.sh` 交互选择配置文件【手动】
- [ ] `run_monitor.sh --config` 直接指定配置【手动】
- [ ] `manage_webui.sh start/stop/status` 正常工作【手动】
- [ ] docs/cli_usage.md 命令示例可执行【手动】

## UI 美化

- [ ] 卡片 hover 动效正常【手动】
- [ ] 表单控件样式统一【手动】
- [ ] 响应式布局（移动端）正常【手动】
- [ ] 暗色主题下预览区可读【手动】
