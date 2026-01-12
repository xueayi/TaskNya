#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TaskNya Web 界面启动程序

提供 Web 界面用于配置和控制监控任务。

使用方法:
    python webui.py              # 正常模式
    python webui.py --debug      # 调试模式
    python webui.py --port 8080  # 指定端口

环境变量:
    TASKNYA_DEBUG=1      # 启用调试模式
    TASKNYA_PORT=8080    # 指定端口
    TASKNYA_HOST=0.0.0.0 # 指定主机地址
"""

import os
import sys
import logging
import argparse

# 添加项目根目录到 Python 路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)



def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='TaskNya Web 界面',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python webui.py              # 使用默认配置启动
  python webui.py --debug      # 启用调试模式
  python webui.py --port 8080  # 使用端口 8080
  python webui.py -d -p 8080   # 调试模式 + 自定义端口
        """
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='启用调试模式（自动重载、详细错误信息、DEBUG 日志）'
    )
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=None,
        help='Web 服务端口（默认: 5000）'
    )
    parser.add_argument(
        '--host',
        type=str,
        default=None,
        help='Web 服务主机地址（默认: 0.0.0.0）'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细日志（不开启完整调试模式）'
    )
    return parser.parse_args()


def get_config(args):
    """
    获取配置，优先级：命令行参数 > 环境变量 > 默认值
    
    Args:
        args: 解析后的命令行参数
        
    Returns:
        dict: 配置字典
    """
    # 调试模式
    debug = args.debug or os.environ.get('TASKNYA_DEBUG', '').lower() in ('1', 'true', 'yes')
    
    # 端口
    port = args.port or int(os.environ.get('TASKNYA_PORT', '5000'))
    
    # 主机
    host = args.host or os.environ.get('TASKNYA_HOST', '0.0.0.0')
    
    # 详细日志
    verbose = args.verbose or debug
    
    return {
        'debug': debug,
        'port': port,
        'host': host,
        'verbose': verbose
    }


def setup_logging(debug: bool, verbose: bool):
    """
    配置日志系统
    
    Args:
        debug: 是否为调试模式
        verbose: 是否显示详细日志
    """
    # 设置日志级别
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    
    # 配置根日志器
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 调整 Werkzeug 日志级别
    if not debug:
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
    else:
        logging.getLogger('werkzeug').setLevel(logging.INFO)


def print_startup_info(config: dict):
    """
    打印启动信息
    
    Args:
        config: 配置字典
    """
    print("=" * 50)
    print("  TaskNya Web 界面")
    print("=" * 50)
    
    if config['debug']:
        print("  ⚠️  调试模式已启用")
        print("     - 自动重载: 开启")
        print("     - 详细错误: 开启")
        print("     - 日志级别: DEBUG")
    
    print(f"\n  访问地址: http://{config['host']}:{config['port']}")
    if config['host'] == '0.0.0.0':
        print(f"  本地访问: http://localhost:{config['port']}")
    
    print("\n  按 Ctrl+C 停止服务")
    print("=" * 50)


def main():
    """主函数"""
    # 解析参数
    args = parse_args()
    config = get_config(args)
    
    # 确保工作目录是项目根目录
    os.chdir(PROJECT_ROOT)
    
    # 配置日志
    setup_logging(config['debug'], config['verbose'])
    
    # 打印启动信息
    print_startup_info(config)
    
    # 导入并启动 Flask 应用
    from app import app
    
    try:
        app.run(
            debug=config['debug'],
            host=config['host'],
            port=config['port'],
            use_reloader=config['debug'],  # 调试模式下启用自动重载
            threaded=True  # 启用多线程处理请求
        )
    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except Exception as e:
        logging.error(f"启动失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()