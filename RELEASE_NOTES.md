## v1.3.1 更新日志

### Bug 修复

- **修复 CLI `--message` 文本未填充到 `${detail}` 变量**：`build_training_info` 之前仅在「日志检测」「目标文件检测」时保存 detail，手动触发时 `${detail}` 为空；现已始终写入
- **修复下拉菜单被配置框遮盖**：`.card` 的 `overflow: hidden` 导致「添加检测方法」和「添加通知渠道」的下拉菜单在模块为空时被裁剪，改为 `overflow: visible` 并补偿圆角

### 改进

- **移除无效的 `anime_quote_enabled` 配置字段**：该字段从未被代码读取，语录功能由模板中是否包含 `${anime_quote}` 占位符自动驱动；已从默认配置、所有预设模板和测试文件中清除
- **WebUI 支持加载预设模板**：点击「加载配置」弹窗新增 `configs/templates/` 预设模板区域，加载模板不覆盖 default.yaml
- **启动脚本支持自定义端口**：`start_webui.bat`、`manage_webui.sh`、`run_monitor.sh` 均支持通过参数指定端口，启动时打印访问 URL
- **缺省配置修正**：所有通知渠道默认关闭（`webhook`、`email` 原为 `True`），清理占位示例数据
- **静态资源缓存清除**：CSS/JS 引用添加 `?v={{ version }}`，版本更新后自动加载最新文件

### 文档

- `cli_usage.md`：补充端口参数用法、`--message` 与 `${detail}` 的关联说明
- `inline_variables.md`：`${detail}` 说明中补充 CLI `--message` 来源
- `README.md`：新增自定义端口启动示例

---

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
