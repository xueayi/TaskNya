# 🐈 TaskNya - 实时任务监控系统

![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg) 
![License](https://img.shields.io/badge/License-MIT-green.svg) 
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)  

**TaskNya** 是一个通用的任务监控与通知工具，适用于 **深度学习训练、服务器任务、批处理脚本、日志监控、资源管理等**。  
它能够 **检测任务完成状态**（基于文件、日志、GPU 资源），并通过 **Webhook** 发送通知到 **任意支持 Webhook 的平台**（如 飞书、钉钉、Slack、Discord、Teams 等）。  

---

## ✨ 主要功能  

- [x] **文件检测**：当指定的文件生成后，触发通知（适用于模型训练完成、数据处理完成等）。  
- [x] **日志检测**：当日志文件中出现指定关键字时，触发通知（适用于日志分析、异常监控等）。  
- [x] **GPU 资源检测**：当 GPU 功耗持续低于阈值时，触发通知（适用于深度学习训练结束检测）。  
- [x] **Webhook 通知**：支持 **飞书、钉钉、Slack、Discord、Teams** 等平台，可自定义通知内容。  
- [x] **可自定义配置**：支持 **YAML 配置文件**，可调整检测规则和通知格式。  
- [ ] web GUI界面
- [ ] examples不同场景范例
- [ ] docker
- [ ] Pypl
- [ ] Windows环境适配
- [ ] 邮箱推送支持
- [ ] 企业微信推送支持
- [ ] 更多可选触发条件预设
---

## 🚀 安装  

```bash
git clone https://github.com/xueayi/TaskNya.git  
cd TaskNya  
pip install -r requirements.txt  
```

> **依赖环境：** Python 3.7 及以上
> 
> **GPU监测：** 需要在有NVIDIA显卡的Linux环境下运行

---

## 📌 使用方法  

### 1️⃣ **直接运行**  

```bash
python TaskNya.py
```
脚本中已有默认配置

### 2️⃣ **通过配置文件运行**

```bash
python TaskNya.py --config config.yaml
```
其中 `config.yaml` 是你的自定义配置文件。
当然，你也可以把脚本嵌入到其他程序中来联合使用。

<img src="images/实际使用截图.png" alt="TaskNya">
<img src="images/飞书推送.jpg" alt="TaskNya" height="1000" style="display: block; margin: auto;">

### 3️⃣ **示例配置文件 (`config.yaml`)**  

```yaml
# 深度学习任务监控配置文件
monitor:
  # 基本配置
  project_name: "深度学习训练"     # 项目名称
  check_interval: 5               # 检查间隔(秒)
  logprint: 60                     # 日志打印间隔（秒）
  timeout: None                   # 监控超时时间(秒)，设为null则无限等待
  
  # 文件检查配置
  check_file_enabled: true         # 是否启用文件检查
  check_file_path: "./output/model_final.pth"  # 要检查的文件路径
  
  # 日志检查配置
  check_log_enabled: false          # 是否启用日志检查
  check_log_path: "./logs/training.log"  # 日志文件路径
  check_log_markers:               # 完成标记列表
    - "Training completed"
    - "任务完成"
    - "训练完成"
    - "Epoch [300/300]"
  
  # GPU功耗检查配置
  check_gpu_power_enabled: false   # 是否启用GPU功耗检查
  check_gpu_power_threshold: 50.0  # 功耗阈值(瓦特)
  check_gpu_power_gpu_ids: "all"   # 可以是数字、列表[0,1]或"all"
  check_gpu_power_consecutive_checks: 3  # 连续几次检测低于阈值才判定完成

# 飞书webhook配置
webhook:
  enabled: true                    # 是否启用webhook通知
  url: "https://open.feishu.cn/open-apis/bot/v2/hook/yoururl"  # webhook URL
  
  # 消息配置
  title: "🎉 深度学习训练完成通知"  # 消息标题
  color: "green"                   # 卡片颜色: green, blue, red, grey, turquoise
  
  # 要包含的信息项
  include_project_name: true                # 包含项目名称
  include_project_name_title: "训练项目"       # 包含项目名称
  include_start_time: true                  # 包含开始时间
  include_start_time_title: "训练开始"    # 包含开始时间
  include_end_time: true                    # 包含结束时间
  include_end_time_title: "训练结束时间"      # 包含结束时间
  include_method: true                      # 包含判断方法
  include_method_title: "系统判断依据"        # 包含判断方法
  include_duration: true                    # 包含任务时长
  include_duration_title: "总耗时"           # 包含任务时长
  include_hostname: true                    # 包含主机名
  include_hostname_title: "主机名"           # 包含主机名
  include_gpu_info: true                    # 包含GPU信息，需要在有NVIDIA显卡的Linux环境下运行
  include_gpu_info_title: "GPU信息"          # 包含GPU信息，需要在有NVIDIA显卡的Linux环境下运行

  footer: "此消息由TaskNya发送"  # 页脚信息

```

---

## ⚙️ 配置参数详解  

### `monitor` 监控参数  

| 参数 | 说明 | 示例值 |
|------|------|-------|
| `project_name` | 任务名称 | `"深度学习训练"` |
| `check_interval` | 监控间隔（秒） | `5` |
| `logprint` | 日志打印间隔（秒） | `60` |
| `timeout` | 监控超时时间（秒），`null` 表示无超时 | `3600` |
| `check_file_enabled` | 是否启用文件监控，可配置为任务完成的产物文件 | `true` |
| `check_file_path` | 需要检测的文件路径 | `"./output/completed.flag"` |
| `check_log_enabled` | 是否启用日志监控，启用后可以监测指定任务的日志文件，出现关键词则判定为任务完成 | `true` |
| `check_log_path` | 需要检测的日志文件路径 | `"./logs/task.log"` |
| `check_log_markers` | 任务完成的日志关键词 | `["任务已完成", "Task Finished"]` |
| `check_gpu_power_enabled` | 是否启用 GPU 功耗监控 | `true` |
| `check_gpu_power_threshold` | GPU 功耗低于此值（W）时触发 | `50.0` |
| `check_gpu_power_gpu_ids` | 监测的 GPU ID（`all` 或 ID 列表），多块GPU时修改，一般保持默认 | `"all"` |
| `check_gpu_power_consecutive_checks` | 连续低于功耗阈值的次数，连续低于阈值后判定为任务完成 | `3` |

### `webhook` 通知参数  

| 参数 | 说明 | 示例值 |
|------|------|-------|
| `enabled` | 是否启用 Webhook | `true` |
| `url` | Webhook 地址（可用于飞书、钉钉、Slack 等） | `"https://webhook.example.com"` |
| `title` | 通知标题 | `"🎉 任务完成通知"` |
| `color` | 通知颜色（仅适用于部分平台） | `"green"` |
| `include_project_name` | 是否包含项目名称 | `true` |
| `include_start_time` | 是否包含任务开始时间 | `true` |
| `include_end_time` | 是否包含任务结束时间 | `true` |
| `include_method` | 是否包含触发通知的方法（文件、日志、GPU 监测等） | `true` |
| `include_duration` | 是否包含任务运行时长 | `true` |
| `include_hostname` | 是否包含主机名 | `true` |
| `include_gpu_info` | 是否包含 GPU 信息，需要在有NVIDIA显卡的Linux环境下才能显示 | `true` |
| `footer` | 通知底部文本 | `"本消息由 TaskNya 自动发送"` |

---

## 🖥️ 适用场景  

🔹 **深度学习任务监控**：监测任务完成（如模型训练），自动通知用户  
🔹 **日志分析任务**：检查目标任务日志中是否包含特定标记，并触发消息通知  
🔹 **批处理任务**：当数据处理、转换或导出完成时自动通知  
🔹 **服务器资源监控**：检测多块 GPU 资源利用情况，判断任务是否完成  
🔹 **任意定制任务**：可根据业务需求扩展，监控任何能满足触发条件的任务  

---

## 🔧 开发 & 贡献  

欢迎贡献代码！请先 fork 项目，然后提交 Pull Request 😃  
如果你喜欢该项目的话欢迎添加star！ ⭐

---

## 📄 许可证  

MIT License - 你可以自由使用和修改本项目。  

---
