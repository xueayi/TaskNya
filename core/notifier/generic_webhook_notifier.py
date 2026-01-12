# -*- coding: utf-8 -*-
"""
通用 Webhook 通知模块

支持多种 HTTP 方法和自定义模板的通用 Webhook 通知器。
可配置重试机制和变量替换。
"""

import json
import logging
import re
import time
from typing import Dict, Any, Optional, List

import requests

from core.notifier.base import BaseNotifier
from core.utils.anime_quote import get_anime_quote

logger = logging.getLogger(__name__)


class GenericWebhookNotifier(BaseNotifier):
    """
    通用 Webhook 通知器
    
    支持 POST/PUT/GET/DELETE 请求，自定义 Headers 和 Body，
    以及变量替换和内置模板。
    
    支持的变量:
        - ${project_name}: 项目名称
        - ${start_time}: 开始时间
        - ${end_time}: 结束时间
        - ${duration}: 持续时长
        - ${method}: 触发方式
        - ${hostname}: 主机名
        - ${gpu_info}: GPU 信息
        - ${detail}: 触发详情
        - ${anime_quote}: 二次元语录
    
    Attributes:
        url (str): Webhook URL
        method (str): HTTP 方法
        headers (dict): 请求头
        body_template (str): Body 模板
        retry_count (int): 重试次数
    """
    
    # HTTP 方法白名单
    ALLOWED_METHODS = ["POST", "PUT", "GET", "DELETE", "PATCH"]
    
    # 内置模板
    BUILTIN_TEMPLATES = {
        "astrbot": {
            "description": "AstrBot Webhook 格式",
            "body": {
                "content": "[ 任务完成通知 ]\n----------------------------\n项目: ${project_name}\n开始: ${start_time}\n结束: ${end_time}\n耗时: ${duration}\n触发: ${method}\n----------------------------\n${anime_quote}\n\n[ 来自 TaskNya 推送 ]",
                "umo": "${astrbot_umo}",
                "message_type": "text"
            }
        },
        "text": {
            "description": "简单文本格式",
            "body": {
                "content": "[TaskNya] 项目 ${project_name} 已完成，耗时 ${duration}，触发方式: ${method}"
            }
        },
        "json": {
            "description": "通用 JSON 格式",
            "body": {
                "event": "task_complete",
                "project": "${project_name}",
                "start_time": "${start_time}",
                "end_time": "${end_time}",
                "duration": "${duration}",
                "method": "${method}",
                "hostname": "${hostname}"
            }
        },
        "discord": {
            "description": "Discord Webhook 格式",
            "body": {
                "content": "**🎉 任务完成通知**\n\n**项目**: ${project_name}\n**耗时**: ${duration}\n**触发**: ${method}\n\n> ${anime_quote}"
            }
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化通用 Webhook 通知器
        
        Args:
            config: 配置字典，包含:
                - enabled: 是否启用
                - url: Webhook URL
                - method: HTTP 方法 (POST/PUT/GET/DELETE)
                - headers: 请求头字典
                - body: 自定义 Body (字符串或字典)
                - builtin_template: 内置模板名
                - retry_count: 重试次数 (0-5)
                - timeout: 请求超时（秒）
                - anime_quote_enabled: 是否启用二次元语录
                - astrbot_mode: AstrBot 简易模式开关
                - astrbot_umo: AstrBot UMO 参数
                - astrbot_content: AstrBot 简易模式内容
        """
        self._enabled = config.get('enabled', False)
        self.url = config.get('url', '')
        self.method = config.get('method', 'POST').upper()
        self.headers = config.get('headers', {'Content-Type': 'application/json'})
        self.body_template = config.get('body', '')
        self.builtin_template = config.get('builtin_template', None)
        self.retry_count = min(max(config.get('retry_count', 0), 0), 5)
        self.timeout = config.get('timeout', 10)
        self.anime_quote_enabled = config.get('anime_quote_enabled', False)
        
        # AstrBot 简易模式
        self.astrbot_mode = config.get('astrbot_mode', False)
        self.astrbot_umo = config.get('astrbot_umo', '')
        self.astrbot_header = config.get('astrbot_header', '文件变动')
        self.astrbot_content = config.get('astrbot_content', '')
        self.astrbot_extra = config.get('astrbot_extra', '')
        self.astrbot_include_quote = config.get('astrbot_include_quote', True)
        
        # 验证 HTTP 方法
        if self.method not in self.ALLOWED_METHODS:
            logger.warning(f"不支持的 HTTP 方法 '{self.method}'，已回退到 POST")
            self.method = "POST"
        
        # 解析 headers（可能是字符串格式的 JSON）
        if isinstance(self.headers, str):
            try:
                self.headers = json.loads(self.headers)
            except json.JSONDecodeError:
                logger.warning("Headers 格式无效，使用默认值")
                self.headers = {'Content-Type': 'application/json'}
    
    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self.url)
    
    def send(self, training_info: Dict[str, Any]) -> bool:
        """
        发送通知
        
        Args:
            training_info: 任务信息字典
            
        Returns:
            bool: 发送是否成功
        """
        if not self.enabled:
            logger.info("通用 Webhook 通知已禁用或 URL 为空")
            return False
        
        # 构建变量上下文
        context = self._build_context(training_info)
        
        # 获取 Body 内容
        body = self._get_body(context)
        
        # 执行请求（带重试）
        return self._send_with_retry(body)
    
    def _build_context(self, training_info: Dict[str, Any]) -> Dict[str, str]:
        """
        构建变量替换上下文
        
        Args:
            training_info: 任务信息字典
            
        Returns:
            变量上下文字典
        """
        context = {
            "project_name": training_info.get("project_name", ""),
            "start_time": training_info.get("start_time", ""),
            "end_time": training_info.get("end_time", ""),
            "duration": training_info.get("duration", ""),
            "method": training_info.get("method", ""),
            "hostname": training_info.get("hostname", ""),
            "gpu_info": training_info.get("gpu_info", ""),
            "detail": training_info.get("detail", ""),
            # AstrBot 特定参数
            "astrbot_umo": self.astrbot_umo,
        }
        
        # 处理报告数据（多文件感知）
        report = training_info.get("report", {})
        if report:
            context.update({
                "report_summary": report.get("summary", ""),
                "report_total": str(report.get("total_changes", 0)),
                "report_scan_path": report.get("scan_path", ""),
                "report_timestamp": report.get("timestamp", ""),
                "report_added_count": str(report.get("added_count", 0)),
                "report_removed_count": str(report.get("removed_count", 0)),
                "report_modified_count": str(report.get("modified_count", 0)),
                "report_actions": ", ".join(report.get("actions", [])),
            })
            
            # 格式化文件列表
            context["report_added_list"] = self._format_file_list(report.get("added_files", []))
            context["report_removed_list"] = self._format_file_list(report.get("removed_files", []))
            context["report_modified_list"] = self._format_file_list(report.get("modified_files", []))
            
            # 合并新增和删除的列表 (用户需求)
            changes = []
            for f in report.get("added_files", []):
                f_copy = f.copy()
                f_copy['tag'] = "[新增]"
                changes.append(f_copy)
            for f in report.get("removed_files", []):
                f_copy = f.copy()
                f_copy['tag'] = "[删除]"
                changes.append(f_copy)
            context["report_change_list"] = self._format_file_list(changes)
            
            # 目录监控时，detail 优先显示统计信息
            if report.get("summary"):
                context["detail"] = report["summary"]
        else:
            # 默认空值
            for key in ["report_summary", "report_total", "report_scan_path", "report_timestamp", 
                        "report_added_count", "report_removed_count", "report_modified_count", "report_actions",
                        "report_added_list", "report_removed_list", "report_modified_list", "report_change_list"]:
                context[key] = "无" if "list" not in key else ""

        # 添加二次元语录
        if self.anime_quote_enabled:
            context["anime_quote"] = get_anime_quote()
        else:
            context["anime_quote"] = ""
        
        return context

    def _format_file_list(self, files: List[Dict[str, Any]]) -> str:
        """格式化文件列表为字符串"""
        if not files:
            return "无"
            
        lines = []
        for i, f in enumerate(files[:10]):  # 最多显示10个
            tag = f.get('tag', "") + " " if f.get('tag') else ""
            size_text = f"[{f['size_str']}]" if not f['is_dir'] else "[DIR]"
            lines.append(f"{i+1}. {tag}{f['path']} {size_text}")
        
        if len(files) > 10:
            lines.append(f"... 等共 {len(files)} 项")
            
        return "\n".join(lines)
    
    def _get_body(self, context: Dict[str, str]) -> str:
        """
        获取请求 Body
        
        Args:
            context: 变量上下文
            
        Returns:
            JSON 格式的 Body 字符串
        """
        body_dict = None
        
        # AstrBot 简易模式优先
        if self.astrbot_mode:
            # 使用用户要求的预设格式
            content_parts = []
            
            # 表头
            header = self._replace_variables(self.astrbot_header, context)
            content_parts.append(f"📢 [ {header} ]")
            content_parts.append("----------------------------")
            
            # 通知内容
            if self.astrbot_content:
                main_content = self._replace_variables(self.astrbot_content, context)
                content_parts.append(main_content)
            else:
                # 默认内容
                content_parts.append(f"📋 项目: {context.get('project_name', '')}")
                content_parts.append(f"⏱️ 耗时: {context.get('duration', '')}")
                content_parts.append(f"🔍 触发: {context.get('method', '')}")
                
                # 如果有报告摘要
                if context.get("report_summary") and context["report_summary"] != "无":
                    content_parts.append(f"📊 统计: {context['report_summary']}")
            
            content_parts.append("----------------------------")
            
            # 其他内容（如有）
            if self.astrbot_extra:
                extra_content = self._replace_variables(self.astrbot_extra, context)
                content_parts.append(extra_content)
                content_parts.append("")
            
            # 二次元语录
            if self.astrbot_include_quote:
                quote = get_anime_quote()
                if quote:
                    content_parts.append(f'"{quote}"')
            
            # content_parts.append("[ TaskNya ]")  # 底部签名可选，保持简洁可移除或保留
            
            body_dict = {
                "content": "\n".join(content_parts),
                "umo": self.astrbot_umo,
                "message_type": "text"
            }
        # 使用内置模板
        elif self.builtin_template and self.builtin_template in self.BUILTIN_TEMPLATES:
            template = self.BUILTIN_TEMPLATES[self.builtin_template]
            body_dict = template["body"].copy()
        # 使用自定义模板
        elif self.body_template:
            if isinstance(self.body_template, str):
                try:
                    body_dict = json.loads(self.body_template)
                except json.JSONDecodeError:
                    # 如果不是 JSON，直接作为内容
                    body_dict = {"content": self.body_template}
            else:
                body_dict = self.body_template
        else:
            # 默认使用简单格式
            body_dict = {
                "content": "[TaskNya] 项目 ${project_name} 已完成，耗时 ${duration}"
            }
        
        # 递归替换变量
        body_dict = self._replace_variables_in_dict(body_dict, context)
        
        return json.dumps(body_dict, ensure_ascii=False)
    
    def _replace_variables(self, template: str, context: Dict[str, str]) -> str:
        """
        替换模板中的变量
        
        Args:
            template: 模板字符串
            context: 变量上下文
            
        Returns:
            替换后的字符串
        """
        def replace(match):
            var_name = match.group(1)
            return str(context.get(var_name, match.group(0)))
        
        return re.sub(r'\$\{(\w+)\}', replace, template)
    
    def _replace_variables_in_dict(self, obj: Any, context: Dict[str, str]) -> Any:
        """
        递归替换字典/列表中的变量
        
        Args:
            obj: 要处理的对象
            context: 变量上下文
            
        Returns:
            替换后的对象
        """
        if isinstance(obj, str):
            return self._replace_variables(obj, context)
        elif isinstance(obj, dict):
            return {k: self._replace_variables_in_dict(v, context) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_variables_in_dict(item, context) for item in obj]
        else:
            return obj
    
    def _send_with_retry(self, body: str) -> bool:
        """
        带重试的请求发送
        
        Args:
            body: 请求 Body
            
        Returns:
            是否成功
        """
        last_error = None
        
        for attempt in range(self.retry_count + 1):
            try:
                success = self._do_send(body)
                if success:
                    return True
                    
                # 非成功响应，准备重试
                if attempt < self.retry_count:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.info(f"请求失败，{wait_time} 秒后重试 ({attempt + 1}/{self.retry_count})")
                    time.sleep(wait_time)
                    
            except Exception as e:
                last_error = e
                if attempt < self.retry_count:
                    wait_time = 2 ** attempt
                    logger.warning(f"请求异常: {e}，{wait_time} 秒后重试 ({attempt + 1}/{self.retry_count})")
                    time.sleep(wait_time)
        
        if last_error:
            logger.error(f"通用 Webhook 发送失败: {last_error}")
        return False
    
    def _do_send(self, body: str) -> bool:
        """
        执行实际的 HTTP 请求
        
        Args:
            body: 请求 Body
            
        Returns:
            是否成功 (2xx 响应)
        """
        try:
            # 根据 HTTP 方法选择请求方式
            request_kwargs = {
                "url": self.url,
                "headers": self.headers,
                "timeout": self.timeout,
            }
            
            # GET 和 DELETE 通常不带 body
            if self.method in ["POST", "PUT", "PATCH"]:
                request_kwargs["data"] = body.encode('utf-8')
            
            response = requests.request(self.method, **request_kwargs)
            
            if 200 <= response.status_code < 300:
                logger.info(f"通用 Webhook 发送成功 ({response.status_code})")
                return True
            else:
                logger.warning(f"通用 Webhook 响应异常: {response.status_code} - {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("通用 Webhook 请求超时")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"通用 Webhook 连接错误: {e}")
            raise
        except requests.exceptions.SSLError as e:
            logger.error(f"通用 Webhook SSL 错误: {e}")
            raise
        except Exception as e:
            logger.error(f"通用 Webhook 发送异常: {e}")
            raise
    
    @classmethod
    def get_builtin_templates(cls) -> Dict[str, str]:
        """
        获取所有内置模板的描述
        
        Returns:
            {模板名: 描述} 的字典
        """
        return {
            name: template["description"]
            for name, template in cls.BUILTIN_TEMPLATES.items()
        }
    
    @classmethod
    def get_supported_variables(cls) -> List[str]:
        """
        获取支持的变量列表
        
        Returns:
            变量名列表
        """
        return [
            "project_name",
            "start_time",
            "end_time",
            "duration",
            "method",
            "hostname",
            "gpu_info",
            "detail",
            "anime_quote",
            "astrbot_umo",
            "report_summary",
            "report_change_list",
            "report_actions",
            "report_added_list",
            "report_removed_list",
            "report_modified_list"
        ]
