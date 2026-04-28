# 内联变量参考

[项目主页](https://github.com/xueayi/TaskNya) · [GitHub Pages 本文档](https://xueayi.github.io/TaskNya/inline_variables) · [用户指南](user_guide.md) · [开发手册](DEVELOPMENT.md) · [API 参考](api_reference.md) · [多平台通知配置](notification_setup.md)

TaskNya 在**通用 Webhook** 的 Body（JSON）以及部分渠道的**自定义文本**中，支持使用 `${变量名}` 形式的内联占位符。系统在发送前会将占位符替换为本次触发的实际内容。

---

## 语法说明

- **写法**：一律使用 `${变量名}`，例如 `${project_name}`、`${duration}`。
- **大小写**：变量名区分大小写，须与下表完全一致。
- **`${anime_quote}`**：仅当模板字符串中**包含**该占位符时，程序才会请求 [Hitokoto（一言）](https://developer.hitokoto.cn/) API 获取语录；未使用时不会发起网络请求。
- **目录监控 / 无报告数据时**：与报告相关的变量会退化为空字符串或 `无`（与实现一致），不会在 JSON 中留下未替换的 `${...}`。

---

## 变量一览

| 变量 | 说明 |
|------|------|
| `${project_name}` | 项目名称 |
| `${start_time}` | 开始时间，格式 `YYYY-MM-DD HH:MM:SS` |
| `${end_time}` | 结束时间，格式 `YYYY-MM-DD HH:MM:SS` |
| `${duration}` | 总耗时，格式 `H:MM:SS`（与 `timedelta` 字符串表示一致，不含微秒） |
| `${method}` | 触发方式，例如：`目标文件检测`、`GPU功耗检测`、`日志检测`、`目录变化检测` |
| `${hostname}` | 主机名（Linux 为 `uname` 节点名，Windows 为环境变量 `COMPUTERNAME`） |
| `${gpu_info}` | GPU 信息（若本次上下文未采集则可能为空） |
| `${detail}` | 触发详情；**目录变化检测**且存在报告时，会与报告摘要语义对齐（多文件感知场景下常作为简短摘要） |
| `${anime_quote}` | 二次元语录；见上文「仅当模板包含时才请求 API」 |
| `${report_summary}` | 目录报告统计摘要（如「新增 x 项, 删除 y 项」） |
| `${report_total}` | 变化总数（数值的字符串形式） |
| `${report_scan_path}` | 扫描路径 |
| `${report_timestamp}` | 报告时间戳 |
| `${report_added_count}` | 新增文件数 |
| `${report_removed_count}` | 删除文件数 |
| `${report_modified_count}` | 修改文件数 |
| `${report_change_list}` | 变更文件列表（**新增 + 删除**，带 `[新增]` / `[删除]` 等标记；条数较多时可能截断并附带「等共 n 项」） |
| `${report_added_list}` | 新增文件列表 |
| `${report_removed_list}` | 删除文件列表 |
| `${report_modified_list}` | 修改文件列表 |
| `${report_actions}` | 建议操作（多条时用 `, ` 连接） |

---

## 适用渠道

| 渠道 | 是否可用 `${...}` | 说明 |
|------|-------------------|------|
| **通用 Webhook** | 是 | 可在 Body 的 **任意 JSON 字符串字段** 中使用；最终会序列化为合法 JSON 发出。 |
| **飞书** | 条件可用 | 需在界面中**开启自定义文本**后，在自定义内容里使用变量。 |
| **企业微信** | 条件可用 | 同上，**自定义文本**开启时可用。 |
| **邮件** | 条件可用 | 同上，**自定义标题/正文等自定义文本**开启时可用（具体以 Web 界面选项为准）。 |

未开启自定义文本时，飞书 / 企业微信 / 邮件通常使用内置固定模板，此时不会按你的 `${...}` 模板渲染。

---

## 示例

### 1. 通用 Webhook：纯 JSON 消息体

```json
{
  "text": "[${project_name}] 已完成",
  "meta": {
    "method": "${method}",
    "duration": "${duration}",
    "host": "${hostname}"
  },
  "footer": "${anime_quote}"
}
```

发送前会被替换为真实字符串；若包含 `${anime_quote}`，则 `footer` 会填入一言返回的语录。

### 2. 目录监控：附带报告摘要与变更列表

```json
{
  "title": "${project_name} · 目录变化",
  "summary": "${report_summary}",
  "total": "${report_total}",
  "path": "${report_scan_path}",
  "changes": "${report_change_list}",
  "suggestion": "${report_actions}"
}
```

适合推送到自建服务或类 Slack 的 Incoming Webhook，由对端再格式化展示。

### 3. 飞书 / 企业微信 / 邮件（自定义文本）

在对应渠道的「自定义内容」文本框中，可直接写多行模板，例如：

```text
[ ${project_name} ]
----------------------------
触发方式: ${method}
开始: ${start_time}
结束: ${end_time}
耗时: ${duration}
主机: ${hostname}
详情: ${detail}
----------------------------
[ 目录报告 ]
${report_summary}
变更列表:
${report_change_list}
建议: ${report_actions}
----------------------------
${anime_quote}
```

平台若支持 Markdown，可自行加入平台所需的 Markdown 语法（以各平台限制为准）。

---

## 相关代码

变量上下文与替换逻辑见 `core/notifier/generic_webhook_notifier.py` 中的 `_build_context` 与 `_replace_variables`；其他渠道若支持自定义模板，通常复用同一套 `${...}` 约定。
