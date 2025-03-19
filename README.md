# 🐈 TaskNya - 实时任务监控系统

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg) 
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
- [x] **Web界面**：提供直观的Web配置界面，可实时修改和应用配置。
- [ ] examples不同场景范例
- [ ] docker
- [ ] Pypl
- [ ] Windows环境适配
- [ ] 邮箱推送支持
- [ ] 企业微信推送支持
- [ ] 更多可选触发条件预设

---

## 🚀 安装  

### 1. 克隆项目
```bash
git clone https://github.com/xueayi/TaskNya.git  
cd TaskNya  
```

### 2. 安装依赖
```bash
# 安装基本依赖
pip install -r requirements.txt

# 如果需要GPU监控功能（仅适用于有NVIDIA显卡的环境）
pip install nvidia-ml-py3==7.352.0
```

> **环境要求：**
> - Python 3.8 及以上
> - GPU监控功能需要NVIDIA显卡和nvidia-smi工具（可选）

---

## 📌 使用方法  

### 1️⃣ **命令行方式**  

```bash
# 使用默认配置运行
python main.py

# 使用自定义配置文件运行
python main.py --config config.yaml
```

### 2️⃣ **Web界面方式（推荐）**

```bash
# 启动Web界面
python webui.py

# 或者直接双击 start_webui.bat（Windows）
```

Web界面功能：
- 📝 实时配置修改
- 🔄 保存/加载多个配置方案
- 📊 实时监控状态和日志显示
- 🎛️ 直观的控制面板

访问 `http://localhost:5000` 即可打开Web界面。

> **端口冲突解决方案：**
> 1. 如果5000端口被占用，可以通过以下方式修改端口：
>    ```bash
>    # Linux/Mac
>    export FLASK_RUN_PORT=5001
>    python webui.py
>    
>    # Windows (PowerShell)
>    $env:FLASK_RUN_PORT=5001
>    python webui.py
>    
>    # Windows (CMD)
>    set FLASK_RUN_PORT=5001
>    python webui.py
>    ```
> 2. 或者直接修改 `webui.py` 中的端口配置：
>    ```python
>    if __name__ == '__main__':
>        app.run(host='0.0.0.0', port=5001)
>    ```
> 3. 常见端口冲突原因：
>    - Windows系统的IIS服务
>    - 其他Web应用
>    - Docker容器
>    - 开发服务器

### 3️⃣ **配置文件说明**

配置文件使用YAML格式，分为 `monitor` 和 `webhook` 两个主要部分。每个配置项都有详细的说明和默认值。

1. **基础配置**
```yaml
monitor:
  # 项目基本信息
  project_name: "深度学习训练"     # 项目名称，将显示在通知消息中
  check_interval: 5              # 检查间隔(秒)，每隔多少秒检查一次任务状态
  logprint: 60                  # 日志打印间隔（秒），每隔多少秒在日志中打印一次状态
  timeout: None                 # 监控超时时间(秒)，设为null则无限等待，到期后自动停止监控
```

2. **文件监控配置**
```yaml
monitor:
  # 文件检查配置
  check_file_enabled: true                        # 是否启用文件检查
  check_file_path: "./output/model_final.pth"     # 要检查的文件路径，支持相对路径和绝对路径
                                                 # 当此文件出现时，视为任务完成
```

3. **日志监控配置**
```yaml
monitor:
  # 日志检查配置
  check_log_enabled: true                         # 是否启用日志检查
  check_log_path: "./logs/training.log"           # 日志文件路径，支持相对路径和绝对路径
  check_log_markers:                             # 完成标记列表，当日志中出现以下任一关键词时，视为任务完成
    - "Training completed"                        # 英文完成标记
    - "任务完成"                                   # 中文完成标记
    - "训练完成"                                   # 训练完成标记
    - "Epoch [300/300]"                          # 特定轮次标记
```

4. **GPU监控配置**（可选功能）
```yaml
monitor:
  # GPU功耗检查配置
  check_gpu_power_enabled: false                  # 是否启用GPU功耗检查
  check_gpu_power_threshold: 50.0                 # 功耗阈值(瓦特)，当GPU功耗低于此值时可能表示训练完成
  check_gpu_power_gpu_ids: "all"                 # 监控的GPU ID，可以是以下格式：
                                                 # - "all": 监控所有GPU
                                                 # - 单个数字，如：0
                                                 # - 列表，如：[0,1]
  check_gpu_power_consecutive_checks: 3           # 连续检测次数，连续N次低于阈值才判定为完成
                                                 # 避免临时的功耗波动导致误判
```

5. **Webhook通知配置**
```yaml
webhook:
  enabled: true                                   # 是否启用webhook通知
  url: "your_webhook_url"                        # webhook URL，支持各种平台：
                                                # - 飞书: https://open.feishu.cn/open-apis/bot/v2/hook/xxx
                                                # - 钉钉: https://oapi.dingtalk.com/robot/send?access_token=xxx
                                                # - Slack: https://hooks.slack.com/services/xxx
                                                # - Discord: https://discord.com/api/webhooks/xxx
  
  # 消息样式配置
  title: "🎉 深度学习训练完成通知"                    # 消息标题
  color: "green"                                 # 卡片颜色，支持：
                                                # - green: 绿色（成功）
                                                # - blue: 蓝色（信息）
                                                # - red: 红色（错误）
                                                # - grey: 灰色（默认）
                                                # - turquoise: 青色
  
  # 消息内容配置（每一项都可以自定义是否显示和显示的标题）
  include_project_name: true                     # 是否显示项目名称
  include_project_name_title: "训练项目"           # 项目名称的显示标题
  
  include_start_time: true                       # 是否显示开始时间
  include_start_time_title: "训练开始"            # 开始时间的显示标题
  
  include_end_time: true                         # 是否显示结束时间
  include_end_time_title: "训练结束时间"           # 结束时间的显示标题
  
  include_method: true                           # 是否显示触发方式
  include_method_title: "系统判断依据"             # 触发方式的显示标题
  
  include_duration: true                         # 是否显示持续时间
  include_duration_title: "总耗时"                # 持续时间的显示标题
  
  include_hostname: true                         # 是否显示主机名
  include_hostname_title: "主机名"                # 主机名的显示标题
  
  include_gpu_info: true                         # 是否显示GPU信息
  include_gpu_info_title: "GPU信息"              # GPU信息的显示标题

  footer: "此消息由TaskNya发送"                    # 页脚信息，显示在通知底部
```

配置文件说明：
1. 所有路径支持相对路径和绝对路径，建议使用相对路径
2. GPU监控功能需要NVIDIA显卡支持
3. 时间相关的配置单位均为秒
4. Webhook支持所有标准的Webhook接口，可以根据实际需求调整消息格式

### 4️⃣ **目录结构**

```
TaskNya/
├── app/                      # Web应用目录
│   ├── app.py               # Flask应用主文件
│   ├── static/              # 静态文件
│   └── templates/           # 模板文件
├── configs/                 # 配置文件目录
│   └── default.yaml        # 默认配置文件
├── logs/                   # 日志目录
│   ├── monitor.log        # 监控程序日志
│   └── webui.log         # Web界面日志
├── main.py                # 监控程序主文件
├── webui.py              # Web界面启动程序
├── start_webui.bat       # Windows快捷启动脚本
└── requirements.txt      # 依赖文件
```

---

## ⚠️ 注意事项

1. **GPU监控功能**
   - 仅在有NVIDIA显卡的环境下可用
   - 需要安装 `nvidia-ml-py3` 包
   - 无NVIDIA显卡时此功能会自动禁用

2. **Web界面使用**
   - 配置修改后需点击"应用当前配置"才会生效
   - 可以保存多个配置方案，方便切换
   - 日志面板实时显示监控状态

3. **文件路径**
   - 配置文件中的路径都相对于项目根目录
   - 建议使用相对路径，除非有特殊需求

4. **监控逻辑**
   - 多个监控条件是"或"的关系
   - 任一条件满足即触发通知
   - GPU功耗检测需要连续多次低于阈值

5. **日志文件**
   - `monitor.log`: 记录监控程序的运行日志
   - `webui.log`: 记录Web界面的操作日志
   - 日志文件会自动创建在 `logs` 目录下

6. **配置文件**
   - 默认配置保存在 `configs/default.yaml`
   - 自定义配置保存在 `configs` 目录下
   - 支持通过Web界面管理配置

---

## 🔧 开发 & 贡献  

欢迎贡献代码！请先 fork 项目，然后提交 Pull Request 😃  
如果你喜欢该项目的话欢迎添加star！ ⭐

---

## 📄 许可证  

MIT License - 你可以自由使用和修改本项目。  

---
