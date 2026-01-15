# -*- coding: utf-8 -*-
"""
通知功能测试脚本

测试邮件HTML格式和目录监控报告数据的显示
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.notifier.message_builder import MessageBuilder
from core.notifier.email_notifier import EmailNotifier
from core.notifier.webhook_notifier import WebhookNotifier


def test_message_builder_with_report():
    """测试MessageBuilder处理目录监控报告数据"""
    print("=" * 60)
    print("测试 MessageBuilder 报告数据支持")
    print("=" * 60)
    
    config = {
        'include_project_name': True,
        'include_start_time': True,
        'include_end_time': True,
        'include_method': True,
        'include_duration': True,
        'include_hostname': True,
        'include_gpu_info': False,
        'include_report_summary': True,
        'include_report_details': True,
        'include_report_actions': True,
    }
    
    builder = MessageBuilder(config)
    
    # 构建测试数据
    training_info = builder.build_training_info(
        start_time=datetime.now(),
        end_time=datetime.now(),
        project_name="测试项目",
        method="目录变化检测",
        detail="检测到文件变化"
    )
    
    # 添加模拟的报告数据
    training_info['report'] = {
        'timestamp': '2026-01-15 15:30:00',
        'scan_path': 'D:\\test\\path',
        'total_changes': 5,
        'added_count': 3,
        'removed_count': 1,
        'modified_count': 1,
        'added_files': [
            {'path': 'file1.txt', 'size_str': '1.2 MB', 'is_dir': False, 'action': '备份'},
            {'path': 'file2.py', 'size_str': '5.3 KB', 'is_dir': False, 'action': ''},
            {'path': 'folder1', 'size_str': '', 'is_dir': True, 'action': ''},
        ],
        'removed_files': [
            {'path': 'old_file.log', 'size_str': '100 KB', 'is_dir': False, 'action': ''},
        ],
        'modified_files': [
            {'path': 'config.yaml', 'size_str': '2.1 KB', 'is_dir': False, 'action': '检查'},
        ],
        'summary': '新增 3, 删除 1, 修改 1',
        'actions': ['备份', '检查'],
    }
    
    # 测试Markdown格式
    print("\n--- Markdown格式 ---")
    markdown_content = builder.build_message_content(training_info)
    print(markdown_content)
    
    # 测试HTML格式
    print("\n--- HTML格式 (前200字符) ---")
    html_content = builder.build_html_content(training_info)
    print(html_content[:200] + "...")
    print(f"\nHTML总长度: {len(html_content)} 字符")
    
    # 保存HTML到文件以便查看
    test_html_path = os.path.join(os.path.dirname(__file__), 'test_email.html')
    with open(test_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"\n完整HTML已保存到: {test_html_path}")
    
    print("\n✅ MessageBuilder测试完成")


def test_email_notifier_html():
    """测试EmailNotifier的HTML格式(不实际发送)"""
    print("\n" + "=" * 60)
    print("测试 EmailNotifier HTML格式")
    print("=" * 60)
    
    config = {
        'enabled': False,  # 不实际发送
        'smtp_server': 'smtp.example.com',
        'smtp_port': 465,
        'smtp_user': 'test@example.com',
        'smtp_password': 'password',
        'sender': 'test@example.com',
        'recipient': 'recipient@example.com',
        'use_ssl': True,
        'title': '🎉 TaskNya 任务完成通知',
        'footer': '此邮件由 TaskNya 自动发送',
        'include_report_summary': True,
        'include_report_details': True,
        'include_report_actions': True,
    }
    
    notifier = EmailNotifier(config)
    print(f"EmailNotifier已初始化 (enabled={notifier.enabled})")
    print("✅ EmailNotifier配置测试完成")


def test_webhook_notifier_markdown():
    """测试WebhookNotifier的Markdown格式(不实际发送)"""
    print("\n" + "=" * 60)
    print("测试 WebhookNotifier Markdown格式")
    print("=" * 60)
    
    config = {
        'enabled': False,  # 不实际发送
        'url': 'https://example.com/webhook',
        'title': '🎉 任务完成通知',
        'color': 'green',
        'footer': '此消息由TaskNya发送',
        'include_report_summary': True,
        'include_report_details': True,
        'include_report_actions': True,
    }
    
    notifier = WebhookNotifier(config)
    print(f"WebhookNotifier已初始化 (enabled={notifier.enabled})")
    print("✅ WebhookNotifier配置测试完成")


if __name__ == '__main__':
    print("\n开始通知功能测试...\n")
    
    test_message_builder_with_report()
    test_email_notifier_html()
    test_webhook_notifier_markdown()
    
    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)
