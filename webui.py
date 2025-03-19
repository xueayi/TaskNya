import os
import sys
import logging

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# 过滤掉Werkzeug的WebSocket日志
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# 导入Flask应用
from app import app

if __name__ == '__main__':
    # 确保工作目录是项目根目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("启动TaskNya Web界面...")
    print("请在浏览器中访问: http://localhost:5000")
    
    # 启动Flask应用
    app.run(debug=False, port=5000) 