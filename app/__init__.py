# App Package
"""TaskNya Flask Web 应用包"""


def get_app():
    """延迟导入 app，避免循环导入"""
    from app.app import app
    return app


def get_create_app():
    """延迟导入 create_app，避免循环导入"""
    from app.app import create_app
    return create_app


# 为了向后兼容，在模块级别也提供 app
# 注意：这会在首次导入时创建应用实例
try:
    from app.app import app, create_app
except ImportError:
    app = None
    create_app = None

__all__ = ['app', 'create_app', 'get_app', 'get_create_app']
