# TaskNya 模块开发指南

## 1. 开发环境设置

### 1.1 Python 环境
- Python 3.8+
- 建议使用虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 1.2 依赖安装

```bash
# 安装运行依赖
pip install -r requirements.txt

# 安装开发依赖
pip install pytest pytest-cov flake8 black
```

---

## 2. 代码规范

### 2.1 Python 代码规范
- 遵循 PEP 8 规范
- 使用 black 进行代码格式化
- 使用 flake8 进行代码检查
- 最大行长度：120 字符
- 缩进：4 个空格

### 2.2 注释规范

```python
def function_name(param1: str, param2: int) -> bool:
    """
    函数功能简述

    Args:
        param1: 参数1描述
        param2: 参数2描述

    Returns:
        返回值描述

    Raises:
        ExceptionType: 异常描述
    """
    pass
```

### 2.3 类型注解

```python
from typing import List, Dict, Optional, Tuple

def process_data(
    data: List[str], 
    config: Dict[str, any]
) -> Optional[Tuple[bool, str]]:
    pass
```

---

## 3. 模块开发指南

### 3.1 添加新的监控器

1. 在 `core/monitor/` 下创建新文件
2. 继承 `BaseMonitor` 抽象类
3. 实现必要的抽象方法

```python
# core/monitor/process_monitor.py
from typing import Tuple, Optional, Dict, Any
from core.monitor.base import BaseMonitor

class ProcessMonitor(BaseMonitor):
    """进程监控器"""
    
    def __init__(self, config: Dict[str, Any]):
        self._enabled = config.get('check_process_enabled', False)
        self.process_name = config.get('check_process_name', '')
    
    @property
    def name(self) -> str:
        return "进程监控"
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def check(self) -> Tuple[bool, str, Optional[str]]:
        """
        检查进程是否结束
        
        Returns:
            Tuple[bool, str, Optional[str]]:
                - bool: 是否触发
                - str: 触发方式
                - Optional[str]: 详细信息
        """
        if not self._enabled:
            return False, "未启用", None
        
        # 实现检测逻辑
        import subprocess
        try:
            result = subprocess.run(
                ['pgrep', '-f', self.process_name],
                capture_output=True
            )
            if result.returncode != 0:
                return True, "进程监控", f"进程 {self.process_name} 已结束"
        except Exception:
            pass
        
        return False, "未完成", None
```

4. 在 `core/monitor/__init__.py` 中导出

```python
from core.monitor.process_monitor import ProcessMonitor
__all__.append('ProcessMonitor')
```

5. 在 `MonitorManager` 中注册（可选）

```python
# core/monitor/monitor_manager.py
self.monitors = [
    FileMonitor(monitor_config),
    LogMonitor(monitor_config),
    GpuMonitor(monitor_config),
    ProcessMonitor(monitor_config),  # 新增
]
```

---

### 3.2 添加新的通知器

1. 在 `core/notifier/` 下创建新文件
2. 继承 `BaseNotifier` 抽象类
3. 实现 `send` 方法

```python
# core/notifier/email_notifier.py
import smtplib
from email.mime.text import MIMEText
from typing import Dict, Any
from core.notifier.base import BaseNotifier

class EmailNotifier(BaseNotifier):
    """邮件通知器"""
    
    def __init__(self, config: Dict[str, Any]):
        self._enabled = config.get('email_enabled', False)
        self.smtp_server = config.get('smtp_server', '')
        self.smtp_port = config.get('smtp_port', 587)
        self.sender = config.get('sender', '')
        self.password = config.get('password', '')
        self.recipients = config.get('recipients', [])
    
    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self.smtp_server)
    
    def send(self, message: Dict[str, Any]) -> bool:
        """发送邮件通知"""
        if not self.enabled:
            return False
        
        try:
            msg = MIMEText(self._format_message(message), 'html', 'utf-8')
            msg['Subject'] = f"任务完成: {message.get('project_name', '未知')}"
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.recipients)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False
    
    def _format_message(self, message: Dict[str, Any]) -> str:
        """格式化邮件内容"""
        return f"""
        <h2>任务完成通知</h2>
        <p>项目: {message.get('project_name')}</p>
        <p>耗时: {message.get('duration')}</p>
        <p>触发方式: {message.get('method')}</p>
        """
```

---

### 3.3 配置模块扩展

1. 在 `core/config/defaults.py` 中添加默认配置

```python
DEFAULT_CONFIG = {
    "monitor": {
        # 现有配置...
        "check_process_enabled": False,
        "check_process_name": "",
    },
    "webhook": {
        # 现有配置...
    },
    "email": {  # 新增邮件配置
        "email_enabled": False,
        "smtp_server": "",
        "smtp_port": 587,
        "sender": "",
        "password": "",
        "recipients": []
    }
}
```

2. 在 `ConfigManager.validate_config` 中添加验证逻辑

---

## 4. 测试指南

### 4.1 单元测试

```python
# tests/test_process_monitor.py
import pytest
from unittest.mock import patch
from core.monitor.process_monitor import ProcessMonitor

class TestProcessMonitor:
    
    def test_process_not_found(self):
        """测试进程不存在时触发"""
        config = {
            'check_process_enabled': True,
            'check_process_name': 'nonexistent_process'
        }
        monitor = ProcessMonitor(config)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            triggered, method, detail = monitor.check()
            
            assert triggered is True
            assert method == "进程监控"
    
    def test_disabled(self):
        """测试禁用状态"""
        config = {'check_process_enabled': False}
        monitor = ProcessMonitor(config)
        
        assert monitor.enabled is False
```

### 4.2 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_monitors.py

# 运行特定测试类
pytest tests/test_monitors.py::TestProcessMonitor

# 生成覆盖率报告
pytest tests/ --cov=core --cov=app --cov-report=html
```

---

## 5. 调试指南

### 5.1 调试模式

#### 启用 Flask 调试模式

```python
# webui.py 或 app/app.py
app.run(debug=True, port=5000)
```

#### 环境变量方式

```bash
# Windows
set FLASK_DEBUG=1
set FLASK_ENV=development
python webui.py

# Linux/Mac
export FLASK_DEBUG=1
export FLASK_ENV=development
python webui.py
```

#### 调试模式功能

| 功能 | 说明 |
|------|------|
| 自动重载 | 代码修改后自动重启服务 |
| 详细错误 | 显示完整的错误堆栈信息 |
| 交互式调试器 | 在错误页面可直接调试 |
| DEBUG 日志 | 自动启用 DEBUG 级别日志 |

---

### 5.2 日志使用

```python
import logging
from core.utils import setup_logger

# 方式1：使用模块日志
logger = logging.getLogger(__name__)
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")

# 方式2：使用统一日志配置
logger = setup_logger(
    name='my_module',
    level=logging.DEBUG,
    log_file='./logs/my_module.log'
)
```

---

### 5.3 断点调试

#### 使用 pdb

```python
import pdb

def my_function():
    x = 10
    pdb.set_trace()  # 程序会在此暂停
    y = x * 2
    return y
```

#### 使用 ipdb（增强版）

```bash
pip install ipdb
```

```python
import ipdb

def my_function():
    ipdb.set_trace()  # 更友好的调试界面
```

#### 使用 breakpoint()（Python 3.7+）

```python
def my_function():
    x = 10
    breakpoint()  # 自动使用配置的调试器
    y = x * 2
```

---

### 5.4 远程调试

#### 使用 debugpy（VS Code）

```python
import debugpy

debugpy.listen(("0.0.0.0", 5678))
print("等待调试器连接...")
debugpy.wait_for_client()
```

---

## 6. 发布流程

### 6.1 代码提交

1. 创建功能分支
   ```bash
   git checkout -b feature/new-feature
   ```

2. 编写代码和测试

3. 运行测试确保通过
   ```bash
   pytest tests/ -v
   ```

4. 代码格式化
   ```bash
   black core/ app/ tests/
   flake8 core/ app/ tests/
   ```

5. 提交代码并创建 PR
   ```bash
   git add .
   git commit -m "feat: 添加新功能"
   git push origin feature/new-feature
   ```

### 6.2 版本发布

1. 更新版本号
2. 更新 CHANGELOG.md
3. 合并到 main 分支
4. 创建版本标签
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

---

## 7. 常见问题

### 7.1 配置问题

| 问题 | 解决方案 |
|------|----------|
| 配置文件不存在 | 检查 `configs/default.yaml` 是否存在 |
| 配置验证失败 | 检查配置项类型是否正确 |
| 配置不生效 | 确保使用 `/api/config/apply` 应用配置 |

### 7.2 监控问题

| 问题 | 解决方案 |
|------|----------|
| 文件权限问题 | 确保有读取目标文件的权限 |
| GPU 访问失败 | 检查 `nvidia-smi` 是否可用 |
| 日志文件读取错误 | 检查日志文件路径和编码 |

### 7.3 通知问题

| 问题 | 解决方案 |
|------|----------|
| Webhook URL 无效 | 验证 URL 格式和可达性 |
| 网络连接失败 | 检查网络和防火墙设置 |
| 消息格式错误 | 检查消息内容是否符合平台要求 |

### 7.4 调试问题

| 问题 | 解决方案 |
|------|----------|
| 调试模式不生效 | 检查 `FLASK_DEBUG` 环境变量 |
| 日志不显示 | 检查日志级别设置 |
| 断点不工作 | 确保使用正确的调试器 |