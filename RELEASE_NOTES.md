## v1.3.0 更新日志

### Bug 修复

- **修复监控程序因 timeout 类型错误而意外退出**：YAML 中 `timeout: None`（大写字符串）导致 `int >= str` 比较报错，现在 `validate_config` 会自动将 `'None'` / 空字符串 / `0` 归一化为 Python `None`，并在 `load_config` 后自动执行校验

### 新功能

- **通知渠道独立测试（Web UI + CLI）**
  - 每个通知渠道（飞书 / 通用 Webhook / 邮件 / 企业微信）的卡片头部新增「测试」按钮，使用当前表单填写的配置即可发送测试，无需先保存
  - 新增 API 端点 `POST /api/test-notification/<channel>`，可在渠道未启用时独立测试连通性
  - CLI 新增 `--test-channel` 参数，支持 `webhook` / `generic_webhook` / `email` / `wecom` / `all`，并可搭配 `--message` 和 `--config`
  - `--trigger` 的帮助文本已修正，明确其为「一次性手动触发」语义

- **通用 Webhook 请求头编辑器**
  - 请求头从纯 JSON 文本框升级为「字段编辑器 / 原始 JSON」双模式切换，与请求体编辑器保持一致的交互体验

- **时间输入现代化**
  - 检查间隔、日志打印间隔、监控持续时间三项输入从纯文本改为「数值 + 单位下拉」组合控件，支持秒/分/时切换
  - 输入时实时显示换算结果（如 `5 分 = 300 秒`），加载配置时自动反推最优单位

### 文档

- 更新 `docs/cli_usage.md`：区分手动触发（`--trigger`，一次性向已启用渠道发送）与测试渠道（`--test-channel`，独立调试各渠道）
- 更新 `docs/DEVELOPMENT.md`：新增「版本号管理与发布流程」章节，说明 VERSION 文件、Git tag 触发 CI/CD、发布步骤

### 测试

- 新增 23 个测试用例（timeout 归一化 5 项、测试通知 API 5 项、notifier 配置验证 4 项、时间解析等）
- 全部测试通过
