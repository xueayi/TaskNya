# TaskNya 模块开发指南

## 1. 开发环境设置

### 1.1 Python环境
- Python 3.8+
- 建议使用虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 1.2 依赖安装
```bash
pip install -r requirements.txt
# 可选：安装开发依赖
pip install pytest pytest-cov flake8 black
```

## 2. 代码规范

### 2.1 Python代码规范
- 遵循PEP 8规范
- 使用black进行代码格式化
- 使用flake8进行代码检查
- 最大行长度：120字符
- 缩进：4个空格

### 2.2 注释规范
```python
def function_name(param1: type, param2: type) -> return_type:
    """
    函数功能简述

    Args:
        param1 (type): 参数1描述
        param2 (type): 参数2描述

    Returns:
        return_type: 返回值描述

    Raises:
        ExceptionType: 异常描述
    """
    pass
```

### 2.3 类型注解
```python
from typing import List, Dict, Optional

def process_data(data: List[str], config: Dict[str, any]) -> Optional[str]:
    pass
```

## 3. 模块开发指南

### 3.1 监控模块开发
1. 在 `app/core/monitor/` 下创建新的监控类
2. 继承 `BaseMonitor` 抽象类
3. 实现必要的抽象方法

```python
from abc import ABC, abstractmethod

class BaseMonitor(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def check_status(self):
        pass
```

### 3.2 通知模块开发
1. 在 `app/core/notification/` 下创建新的通知类
2. 继承 `NotificationBase` 抽象类
3. 实现 `send` 方法

```python
class NotificationBase(ABC):
    @abstractmethod
    def send(self, message: dict) -> bool:
        pass
```

### 3.3 配置模块扩展
1. 在 `app/core/utils/config.py` 中添加新的配置项
2. 更新配置验证逻辑
3. 在 `default.yaml` 中添加默认值

## 4. 测试指南

### 4.1 单元测试
```python
import pytest

def test_monitor_function():
    monitor = YourMonitor()
    assert monitor.check_status() == expected_result
```

### 4.2 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_monitor.py

# 生成覆盖率报告
pytest --cov=app tests/
```

## 5. 调试指南

### 5.1 日志使用
```python
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

def your_function():
    logger.debug("调试信息")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息")
```

### 5.2 调试工具
- 使用 pdb/ipdb 进行断点调试
- 使用 logging 模块记录详细日志
- 使用 print 语句（仅用于临时调试）

## 6. 发布流程

### 6.1 代码提交
1. 创建功能分支
2. 编写代码和测试
3. 运行测试确保通过
4. 提交代码并创建PR

### 6.2 版本发布
1. 更新版本号
2. 更新CHANGELOG.md
3. 合并到main分支
4. 创建版本标签

## 7. 常见问题

### 7.1 配置问题
- 配置文件路径问题
- 配置验证失败
- 配置加载错误

### 7.2 监控问题
- 文件权限问题
- GPU访问失败
- 日志文件读取错误

### 7.3 通知问题
- Webhook URL无效
- 网络连接失败
- 消息格式错误 