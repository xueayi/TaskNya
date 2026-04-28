# 多平台通知配置汇总

[项目主页](https://github.com/xueayi/TaskNya) · [用户指南](user_guide.md) · [内联变量参考](inline_variables.md) · [开发手册](DEVELOPMENT.md) · [API 参考](api_reference.md)

本文汇总在 TaskNya 中接入各通知渠道的要点。完成平台侧配置后，在 TaskNya Web 后台填入 URL、密钥或 SMTP 参数即可。需要自定义文案时，可使用 [内联变量参考](inline_variables.md) 中的 `${变量名}`。

---

## 1. 飞书 · 群机器人 Webhook

**官方文档**：[添加群机器人 / 自定义机器人](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot)

### 简要步骤

1. 打开目标飞书群，进入 **群设置**。
2. 找到 **群机器人** → **添加机器人** → 选择 **自定义机器人**（或通过应用目录添加支持 Webhook 的机器人）。
3. 按提示设置机器人名称、描述等，完成安全策略（如签名校验、IP 等，按需配置）。
4. 创建完成后复制 **Webhook 地址**（`https://open.feishu.cn/open-apis/bot/v2/hook/...`）。

### 在 TaskNya 中填写

1. 打开 TaskNya Web 界面，进入通知 / 飞书相关配置区。
2. 将 **Webhook URL** 粘贴到对应输入框。
3. 若飞书侧启用了 **签名校验**，在 TaskNya 中填写与官方文档一致的 **Secret**，以便生成正确的 `timestamp` / `sign`。
4. 保存并 **应用配置**。需要完全自定义正文时，开启自定义文本并参考 [内联变量参考](inline_variables.md)。

---

## 2. 企业微信 · 群机器人消息推送

**官方文档**：[群机器人配置说明](https://developer.work.weixin.qq.com/document/path/91770)

### 简要步骤

1. 在企业微信 **内部群** 中，点击群聊右上角 **…** → **群机器人** → **添加机器人**。
2. 设置机器人名称，创建后复制 **Webhook 地址**（`https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...`）。

### 消息格式

企业微信群机器人支持多种 `msgtype`，常见包括：

- **text**：纯文本，适合简洁告警。
- **markdown**：`markdown` 类型内容，适合结构化标题、列表（具体支持的 Markdown 子集以企业微信文档为准）。

TaskNya 中根据所选类型填写或选择对应模板；若使用自定义文本，可同时使用 `${...}` 变量（见 [内联变量参考](inline_variables.md)）。

### 在 TaskNya 中填写

将 Webhook URL 填入企业微信通知配置项；如启用加签，按企业微信说明在 TaskNya 中配置密钥。保存后应用配置并做一次测试推送（若有测试功能）。

---

## 3. QQ · 通过 Astrbot 插件（push_lite）

**插件仓库**：[Raven95676/astrbot_plugin_push_lite](https://github.com/Raven95676/astrbot_plugin_push_lite)

### 流程概述

1. **部署 [Astrbot](https://github.com/AstrBotDevs/AstrBot)**（或与该插件兼容的运行环境），完成基础与会话配置。
2. 按插件说明安装 **push_lite**，配置允许的推送目标（如群号、好友、UniMessage 路由等，以插件 README 为准）。
3. 插件通常提供 **HTTP 接收端**；将 TaskNya 的 **通用 Webhook** 指向该地址，并在 Body 中按插件要求的 JSON 字段构造内容（可从插件文档复制示例）。

### 与 TaskNya 对接

使用 **通用 Webhook**：URL、Method、Headers 与 Body 与 push_lite 文档保持一致；Body 中任意字符串字段均可嵌入 `${project_name}`、`${duration}` 等变量，见 [内联变量参考](inline_variables.md)。

---

## 4. 邮件 · SMTP

TaskNya 通过 **SMTP** 发信。大部分邮箱需使用 **授权码 / 应用专用密码**，而非网页登录密码。

### 常用邮箱 SMTP 参考

| 服务商 | SMTP 服务器 | 端口（常见） | 加密 | 备注 |
|--------|-------------|--------------|------|------|
| QQ 邮箱 | `smtp.qq.com` | `465`（SSL）或 `587`（STARTTLS） | SSL/TLS | 开启 POP3/SMTP 服务后在邮箱设置中生成 **授权码** |
| 163 邮箱 | `smtp.163.com` | `465` 或 `587` | SSL/TLS | 客户端登录需 **授权码**（设置 → POP3/SMTP/IMAP） |
| Gmail | `smtp.gmail.com` | `465`（SSL）或 `587`（STARTTLS） | SSL/TLS | 需开启两步验证并使用 **应用专用密码**（Google 账户 → 安全性） |

具体端口与「是否必须为 TLS」以各服务商最新说明为准；若连接失败，优先检查防火墙、端口与加密方式是否与 TaskNya 中选项一致。

### 在 TaskNya 中填写

在邮件通知配置中填写：**SMTP 地址、端口、发件邮箱、用户名（常与邮箱相同）、密码/授权码、收件人**，以及是否使用 SSL/TLS。自定义主题或正文时同样可使用 `${...}` 变量。

---

## 5. 通用 Webhook

适用于任意可通过 **HTTP/HTTPS** 接收 JSON（或你自定义 Method/Body）的系统：自建服务、钉钉自定义机器人（若支持）、IFTTT、Home Assistant、n8n 等。

### 配置要点

1. 在 TaskNya 中启用 **通用 Webhook**，填写目标 **URL**、**HTTP 方法**（如 `POST`）、**Headers**（常见为 `Content-Type: application/json`）。
2. **Body** 使用 JSON 字符串；所有字符串值内均可使用 `${变量名}`，见 [内联变量参考](inline_variables.md)。
3. 按需设置超时与重试次数，避免对端短暂不可用导致漏报。

---

## 延伸阅读

- 变量与示例：[内联变量参考](inline_variables.md)
- 安装与检测逻辑：[用户指南](user_guide.md)
