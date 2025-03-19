# TaskNya 项目结构说明

## 1. 目录结构

```
TaskNya/
├── app/                      # Web应用主目录
│   ├── __init__.py
│   ├── app.py               # Flask应用主文件
│   ├── static/              # 静态文件
│   │   ├── css/            # 样式文件
│   │   ├── js/             # JavaScript文件
│   │   └── images/         # 图片资源
│   └── templates/          # HTML模板
│       └── index.html      # 主页面模板
├── configs/                 # 配置文件目录
│   └── default.yaml        # 默认配置文件
├── logs/                   # 日志目录
│   ├── monitor.log        # 监控程序日志
│   └── webui.log         # Web界面日志
├── main.py                # 监控程序主文件
├── webui.py              # Web界面启动程序
└── requirements.txt      # 依赖文件

## 2. 核心文件说明

### 2.1 main.py
监控程序的核心实现，包含以下主要功能：
- 配置文件加载和解析
- 文件监控实现
- 日志监控实现
- GPU资源监控实现
- Webhook通知实现

### 2.2 webui.py
Web界面的入口文件，负责：
- 启动Flask Web服务
- WebSocket连接管理
- 配置文件管理
- 监控任务控制

### 2.3 app/app.py
Flask应用的核心实现，包含：
- Web路由定义
- API接口实现
- WebSocket处理
- 配置文件操作

### 2.4 app/templates/index.html
Web界面的主要模板文件，实现：
- 配置表单
- 监控控制
- 日志显示
- WebSocket通信

## 3. 配置文件

### 3.1 default.yaml
默认配置文件，定义了：
- 监控参数
- 通知设置
- 界面选项

### 3.2 自定义配置
用户可以在configs目录下创建自定义配置文件，支持：
- 多配置方案
- 实时切换
- 动态加载

## 4. 日志文件

### 4.1 monitor.log
记录监控程序的运行日志：
- 监控状态
- 触发事件
- 错误信息

### 4.2 webui.log
记录Web界面的操作日志：
- 用户操作
- 配置变更
- 系统事件 