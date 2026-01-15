# -*- coding: utf-8 -*-
"""
消息构建器模块

根据配置和任务信息构建通知消息,支持Markdown和HTML格式。
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime


class MessageBuilder:
    """
    消息构建器
    
    根据 webhook 配置和任务信息构建通知消息内容。
    """
    
    def __init__(self, webhook_config: Dict[str, Any]):
        """
        初始化消息构建器
        
        Args:
            webhook_config: webhook 配置字典
        """
        self.config = webhook_config
    
    def build_training_info(self, 
                            start_time: datetime,
                            end_time: datetime,
                            project_name: str,
                            method: str,
                            detail: Optional[str] = None,
                            gpu_info: Optional[str] = None) -> Dict[str, Any]:
        """
        构建任务信息字典
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            project_name: 项目名称
            method: 触发方式
            detail: 触发详情
            gpu_info: GPU 信息
            
        Returns:
            任务信息字典
        """
        duration = end_time - start_time
        
        # 获取主机名
        if hasattr(os, 'uname'):
            hostname = os.uname().nodename
        else:
            hostname = os.environ.get('COMPUTERNAME', 'Unknown')
        
        training_info = {
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": str(duration).split('.')[0],
            "project_name": project_name,
            "hostname": hostname,
            "method": method,
            
            # 标题配置
            "project_name_title": self.config.get('include_project_name_title', '训练项目'),
            "start_time_title": self.config.get('include_start_time_title', '训练开始'),
            "end_time_title": self.config.get('include_end_time_title', '训练结束时间'),
            "method_title": self.config.get('include_method_title', '系统判断依据'),
            "duration_title": self.config.get('include_duration_title', '总耗时'),
            "hostname_title": self.config.get('include_hostname_title', '主机名'),
            "gpu_info_title": self.config.get('include_gpu_info_title', 'GPU信息'),
        }
        
        # 根据触发方式添加详情
        if method == "日志检测" and detail:
            training_info["keyword"] = detail
            training_info["keyword_title"] = "触发关键词"
        
        if method == "目标文件检测" and detail:
            training_info["target_file"] = detail
            training_info["target_file_title"] = "检测到的文件"
        
        # 添加 GPU 信息
        if gpu_info:
            training_info["gpu_info"] = gpu_info
        
        return training_info
    
    def _format_report_summary(self, report: Dict[str, Any]) -> str:
        """
        格式化报告摘要信息
        
        Args:
            report: 报告数据字典
            
        Returns:
            格式化的摘要文本
        """
        parts = []
        if report.get('added_count', 0) > 0:
            parts.append(f"新增 {report['added_count']} 项")
        if report.get('removed_count', 0) > 0:
            parts.append(f"删除 {report['removed_count']} 项")
        if report.get('modified_count', 0) > 0:
            parts.append(f"修改 {report['modified_count']} 项")
        return ", ".join(parts) if parts else "无变化"
    
    def _format_file_list_markdown(self, files: List[Dict[str, Any]], max_items: int = 10) -> str:
        """
        格式化文件列表为Markdown格式
        
        Args:
            files: 文件信息列表
            max_items: 最多显示的文件数量
            
        Returns:
            Markdown格式的文件列表
        """
        if not files:
            return "无"
        
        lines = []
        for i, f in enumerate(files[:max_items]):
            size_text = f"[{f['size_str']}]" if not f.get('is_dir', False) else "[目录]"
            action_text = f" 💡{f['action']}" if f.get('action') else ""
            lines.append(f"{i+1}. {f['path']} {size_text}{action_text}")
        
        if len(files) > max_items:
            lines.append(f"... 等共 {len(files)} 项")
        
        return "\n".join(lines)
    
    def build_message_content(self, training_info: Dict[str, Any]) -> str:
        """
        构建消息内容文本(Markdown格式)
        
        Args:
            training_info: 任务信息字典
            
        Returns:
            格式化的消息内容
        """
        content_items = []
        
        if self.config.get('include_project_name', True):
            content_items.append(
                f"**{training_info['project_name_title']}**: {training_info['project_name']}"
            )
        
        if self.config.get('include_start_time', True):
            content_items.append(
                f"**{training_info['start_time_title']}**: {training_info['start_time']}"
            )
        
        if self.config.get('include_end_time', True):
            content_items.append(
                f"**{training_info['end_time_title']}**: {training_info['end_time']}"
            )
        
        if self.config.get('include_method', True):
            content_items.append(
                f"**{training_info['method_title']}**: {training_info['method']}"
            )
        
        # 可选字段
        if 'keyword' in training_info and training_info['keyword']:
            content_items.append(
                f"**{training_info['keyword_title']}**: {training_info['keyword']}"
            )
        
        if 'target_file' in training_info and training_info['target_file']:
            content_items.append(
                f"**{training_info['target_file_title']}**: {training_info['target_file']}"
            )
        
        # 目录监控报告数据
        if 'report' in training_info and training_info['report']:
            report = training_info['report']
            if self.config.get('include_report_summary', True):
                summary = self._format_report_summary(report)
                content_items.append(f"**变化统计**: {summary}")
            
            if self.config.get('include_report_details', True):
                if report.get('added_files'):
                    content_items.append(f"\n**新增文件**:\n{self._format_file_list_markdown(report['added_files'])}")
                if report.get('removed_files'):
                    content_items.append(f"\n**删除文件**:\n{self._format_file_list_markdown(report['removed_files'])}")
                if report.get('modified_files'):
                    content_items.append(f"\n**修改文件**:\n{self._format_file_list_markdown(report['modified_files'])}")
            
            if self.config.get('include_report_actions', True) and report.get('actions'):
                actions_text = ", ".join(report['actions'])
                content_items.append(f"**建议操作**: {actions_text}")
        
        if self.config.get('include_duration', True):
            content_items.append(
                f"**{training_info['duration_title']}**: {training_info['duration']}"
            )
        
        if self.config.get('include_hostname', True):
            content_items.append(
                f"**{training_info['hostname_title']}**: {training_info['hostname']}"
            )
        
        if self.config.get('include_gpu_info', True) and 'gpu_info' in training_info:
            content_items.append(
                f"**{training_info['gpu_info_title']}**:\n{training_info['gpu_info']}"
            )
        
        # 确保至少有一个内容项
        if not content_items:
            content_items.append(f"**任务项目**: {training_info['project_name']}")
            content_items.append(f"**总耗时**: {training_info['duration']}")
        
        return "**任务已完成！**\n\n" + "\n".join(content_items)
    
    def build_html_content(self, training_info: Dict[str, Any]) -> str:
        """
        构建HTML格式的消息内容(用于邮件)
        
        Args:
            training_info: 任务信息字典
            
        Returns:
            HTML格式的消息内容
        """
        html_parts = []
        
        # HTML头部和样式
        html_parts.append("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 24px; }
        .content { background: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }
        .info-item { margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #667eea; }
        .info-label { font-weight: bold; color: #667eea; }
        .file-list { background: white; padding: 15px; margin: 10px 0; border-radius: 4px; }
        .file-item { padding: 5px 0; border-bottom: 1px solid #eee; }
        .file-item:last-child { border-bottom: none; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 12px; margin-right: 5px; }
        .badge-add { background: #d4edda; color: #155724; }
        .badge-remove { background: #f8d7da; color: #721c24; }
        .badge-modify { background: #fff3cd; color: #856404; }
        .summary { background: #e7f3ff; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .footer { text-align: center; color: #999; font-size: 12px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 任务完成通知</h1>
        </div>
        <div class="content">
""")
        
        # 基本信息
        if self.config.get('include_project_name', True):
            html_parts.append(f"""
            <div class="info-item">
                <span class="info-label">{training_info['project_name_title']}:</span> {training_info['project_name']}
            </div>
""")
        
        if self.config.get('include_start_time', True):
            html_parts.append(f"""
            <div class="info-item">
                <span class="info-label">{training_info['start_time_title']}:</span> {training_info['start_time']}
            </div>
""")
        
        if self.config.get('include_end_time', True):
            html_parts.append(f"""
            <div class="info-item">
                <span class="info-label">{training_info['end_time_title']}:</span> {training_info['end_time']}
            </div>
""")
        
        if self.config.get('include_method', True):
            html_parts.append(f"""
            <div class="info-item">
                <span class="info-label">{training_info['method_title']}:</span> {training_info['method']}
            </div>
""")
        
        # 可选字段
        if 'keyword' in training_info and training_info['keyword']:
            html_parts.append(f"""
            <div class="info-item">
                <span class="info-label">{training_info['keyword_title']}:</span> {training_info['keyword']}
            </div>
""")
        
        if 'target_file' in training_info and training_info['target_file']:
            html_parts.append(f"""
            <div class="info-item">
                <span class="info-label">{training_info['target_file_title']}:</span> {training_info['target_file']}
            </div>
""")
        
        # 目录监控报告数据
        if 'report' in training_info and training_info['report']:
            report = training_info['report']
            
            if self.config.get('include_report_summary', True):
                summary = self._format_report_summary(report)
                html_parts.append(f"""
            <div class="summary">
                <strong>📊 变化统计:</strong> {summary}
            </div>
""")
            
            if self.config.get('include_report_details', True):
                # 新增文件
                if report.get('added_files'):
                    html_parts.append('<div class="file-list"><strong>📥 新增文件:</strong>')
                    for i, f in enumerate(report['added_files'][:10]):
                        size_text = f['size_str'] if not f.get('is_dir', False) else "目录"
                        action_text = f" 💡{f['action']}" if f.get('action') else ""
                        html_parts.append(f'<div class="file-item"><span class="badge badge-add">新增</span>{f["path"]} ({size_text}){action_text}</div>')
                    if len(report['added_files']) > 10:
                        html_parts.append(f'<div class="file-item">... 等共 {len(report["added_files"])} 项</div>')
                    html_parts.append('</div>')
                
                # 删除文件
                if report.get('removed_files'):
                    html_parts.append('<div class="file-list"><strong>🗑️ 删除文件:</strong>')
                    for i, f in enumerate(report['removed_files'][:10]):
                        size_text = f['size_str'] if not f.get('is_dir', False) else "目录"
                        action_text = f" 💡{f['action']}" if f.get('action') else ""
                        html_parts.append(f'<div class="file-item"><span class="badge badge-remove">删除</span>{f["path"]} ({size_text}){action_text}</div>')
                    if len(report['removed_files']) > 10:
                        html_parts.append(f'<div class="file-item">... 等共 {len(report["removed_files"])} 项</div>')
                    html_parts.append('</div>')
                
                # 修改文件
                if report.get('modified_files'):
                    html_parts.append('<div class="file-list"><strong>✏️ 修改文件:</strong>')
                    for i, f in enumerate(report['modified_files'][:10]):
                        size_text = f['size_str'] if not f.get('is_dir', False) else "目录"
                        action_text = f" 💡{f['action']}" if f.get('action') else ""
                        html_parts.append(f'<div class="file-item"><span class="badge badge-modify">修改</span>{f["path"]} ({size_text}){action_text}</div>')
                    if len(report['modified_files']) > 10:
                        html_parts.append(f'<div class="file-item">... 等共 {len(report["modified_files"])} 项</div>')
                    html_parts.append('</div>')
            
            if self.config.get('include_report_actions', True) and report.get('actions'):
                actions_text = ", ".join(report['actions'])
                html_parts.append(f"""
            <div class="info-item">
                <span class="info-label">💡 建议操作:</span> {actions_text}
            </div>
""")
        
        if self.config.get('include_duration', True):
            html_parts.append(f"""
            <div class="info-item">
                <span class="info-label">{training_info['duration_title']}:</span> {training_info['duration']}
            </div>
""")
        
        if self.config.get('include_hostname', True):
            html_parts.append(f"""
            <div class="info-item">
                <span class="info-label">{training_info['hostname_title']}:</span> {training_info['hostname']}
            </div>
""")
        
        if self.config.get('include_gpu_info', True) and 'gpu_info' in training_info:
            gpu_info_html = training_info['gpu_info'].replace('\n', '<br>')
            html_parts.append(f"""
            <div class="info-item">
                <span class="info-label">{training_info['gpu_info_title']}:</span><br>{gpu_info_html}
            </div>
""")
        
        # HTML尾部
        html_parts.append("""
        </div>
        <div class="footer">
            <p>此邮件由 TaskNya 自动发送</p>
        </div>
    </div>
</body>
</html>
""")
        
        return "".join(html_parts)
