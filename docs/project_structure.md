# TaskNya 项目结构说明

## 1. 目录结构

```
TaskNya/
├── core/                         # 核心业务逻辑模块
│   ├── __init__.py              # 模块入口
│   ├── config/                  # 配置管理模块
│   │   ├── __init__.py
│   │   ├── config_manager.py    # 配置管理器类
│   │   └── defaults.py          # 默认配置定义
│   ├── monitor/                 # 监控模块
│   │   ├── __init__.py
│   │   ├── base.py              # 监控器抽象基类
│   │   ├── file_monitor.py      # 文件存在监控
│   │   ├── log_monitor.py       # 日志关键词监控
│   │   ├── gpu_monitor.py       # GPU 功耗监控
│   │   └── monitor_manager.py   # 监控器管理器
│   ├── notifier/                # 通知模块
│   │   ├── __init__.py
│   │   ├── base.py              # 通知器抽象基类
│   │   ├── message_builder.py   # 消息构建器
│   │   └── webhook_notifier.py  # Webhook 通知器
│   └── utils/                   # 工具模块
│       ├── __init__.py
│       ├── gpu.py               # GPU 工具函数
│       └── logger.py            # 日志配置
├── app/                         # Flask Web 应用
│   ├── __init__.py              # 包入口
│   ├── app.py                   # Flask 应用主文件
│   ├── routes/                  # API 路由模块
│   │   ├── __init__.py
│   │   ├── config_routes.py     # 配置 API 路由
│   │   └── monitor_routes.py    # 监控 API 路由
│   ├── websocket/               # WebSocket 模块
│   │   ├── __init__.py
│   │   └── handler.py           # WebSocket 管理器
│   ├── static/                  # 静态文件
│   │   ├── css/                 # 样式文件
│   │   └── js/                  # JavaScript 文件
│   └── templates/               # HTML 模板
│       └── index.html           # 主页面模板
├── tests/                       # 测试套件
│   ├── __init__.py
│   ├── conftest.py              # pytest 配置和 fixtures
│   ├── test_config.py           # 配置模块测试
│   ├── test_monitors.py         # 监控模块测试
│   ├── test_notifier.py         # 通知模块测试
│   ├── test_integration.py      # 集成测试
│   ├── test_api.py              # Web API 测试
│   ├── test_utils.py            # 工具模块测试
│   ├── test_websocket.py        # WebSocket 测试
│   └── test_routes.py           # 路由测试
├── configs/                     # 配置文件目录
│   └── default.yaml             # 默认配置文件
├── logs/                        # 日志目录
│   ├── monitor.log              # 监控程序日志
│   └── webui.log                # Web 界面日志
├── docs/                        # 文档目录
│   ├── DEVELOPMENT.md           # 开发手册
│   ├── api_reference.md         # API 接口说明
│   ├── module_guide.md          # 模块开发指南
│   └── project_structure.md     # 项目结构说明（本文档）
├── main.py                      # CLI 监控程序入口
├── webui.py                     # Web 界面启动程序
├── start_webui.bat              # Windows 启动脚本
├── requirements.txt             # Python 依赖
├── Dockerfile                   # Docker 配置
└── docker-compose.yaml          # Docker Compose 配置
```

## 2. 核心模块说明

### 2.1 core/ - 核心业务逻辑

核心模块采用模块化设计，各模块职责清晰：

| 模块 | 职责 |
|------|------|
| `config/` | 配置文件的加载、保存、合并和验证 |
| `monitor/` | 各种监控器的实现（文件/日志/GPU） |
| `notifier/` | 通知消息的构建和发送 |
| `utils/` | GPU 工具函数和日志配置 |

### 2.2 app/ - Web 应用

Flask Web 应用模块化结构：

| 模块 | 职责 |
|------|------|
| `routes/` | RESTful API 路由定义 |
| `websocket/` | WebSocket 连接管理和消息广播 |
| `static/` | CSS、JavaScript 等静态资源 |
| `templates/` | Jinja2 HTML 模板 |

### 2.3 tests/ - 测试套件

完整的测试覆盖，包括单元测试和集成测试：

```bash
# 运行所有测试
pytest tests/ -v

# 查看覆盖率
pytest tests/ --cov=core --cov=app
```

## 3. 入口文件说明

### 3.1 main.py

命令行监控程序入口，提供 `TrainingMonitor` 类：

```python
from main import TrainingMonitor

monitor = TrainingMonitor(config_path='config.yaml')
monitor.start_monitoring()
```

命令行使用：

```bash
# 默认配置
python main.py

# 自定义配置
python main.py --config my_config.yaml
```

### 3.2 webui.py

Web 界面启动程序：

```bash
# 启动 Web 界面
python webui.py

# 或使用批处理脚本
.\start_webui.bat  # Windows
./start_webui.sh   # Linux
```

启动后访问：http://localhost:5000

## 4. 配置文件

### 4.1 default.yaml

默认配置文件，定义所有配置项的默认值：

```yaml
monitor:
  project_name: "深度学习训练"
  check_interval: 5
  check_file_enabled: true
  check_file_path: "./output/model_final.pth"
  # ... 更多配置

webhook:
  enabled: true
  url: "https://your-webhook-url"
  # ... 更多配置
```

### 4.2 自定义配置

用户可以在 `configs/` 目录下创建自定义配置：

- 支持多配置方案
- 通过 Web 界面实时切换
- 自动合并默认配置

## 5. 日志文件

### 5.1 monitor.log

监控程序运行日志：
- 监控状态变更
- 触发事件记录
- 错误和警告信息

### 5.2 webui.log

Web 界面操作日志：
- API 请求记录
- 配置变更记录
- WebSocket 连接状态

## 6. 调试模式

### 6.1 命令行方式

```bash
# 启用调试模式
python webui.py --debug
python webui.py -d

# 调试模式 + 自定义端口
python webui.py -d -p 8080

# 仅显示详细日志
python webui.py --verbose
```

### 6.2 环境变量方式

```bash
# Windows
set TASKNYA_DEBUG=1
python webui.py

# Linux/Mac
export TASKNYA_DEBUG=1
python webui.py
```

### 6.3 调试模式功能

| 功能 | 正常模式 | 调试模式 |
|------|----------|----------|
| 自动重载 | ❌ | ✅ |
| 详细错误 | ❌ | ✅ |
| 交互式调试器 | ❌ | ✅ |
| 日志级别 | WARNING | DEBUG |

### 6.4 日志级别配置

```python
import logging

# 设置全局日志级别
logging.getLogger().setLevel(logging.DEBUG)

# 或在代码中
from core.utils import setup_logger
logger = setup_logger('my_module', level=logging.DEBUG)
```