# Routes Package
"""Flask 路由模块"""

from app.routes.config_routes import config_bp
from app.routes.monitor_routes import monitor_bp

__all__ = ['config_bp', 'monitor_bp']
