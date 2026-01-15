# -*- coding: utf-8 -*-
"""
邮件通知模块

通过 SMTP 发送通知邮件。
"""

import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.header import Header
from typing import Dict, Any

from core.notifier.base import BaseNotifier
from core.notifier.message_builder import MessageBuilder

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """
    邮件通知器
    
    使用 SMTP 发送任务完成通知邮件。
    
    Attributes:
        server (str): SMTP 服务器地址
        port (int): SMTP 端口
        user (str): SMTP 用户名
        password (str): SMTP 密码或授权码
        sender (str): 发件人邮箱
        recipient (str): 收件人邮箱
        use_ssl (bool): 是否使用 SSL
        title (str): 邮件标题
        footer (str): 邮件页脚
    """
    
    def __init__(self, email_config: Dict[str, Any]):
        """
        初始化邮件通知器
        
        Args:
            email_config: 邮件配置字典
        """
        self._enabled = email_config.get('enabled', False)
        self.server = email_config.get('smtp_server', '')
        self.port = int(email_config.get('smtp_port', 465))
        self.user = email_config.get('smtp_user', '')
        self.password = email_config.get('smtp_password', '')
        self.sender = email_config.get('sender', self.user)
        self.recipient = email_config.get('recipient', '')
        self.use_ssl = email_config.get('use_ssl', True)
        self.title = email_config.get('title', '🎉 TaskNya 任务完成通知')
        self.footer = email_config.get('footer', '此邮件由 TaskNya 自动发送')
        
        # 内部使用 Webhook 的 MessageBuilder 来生成文本内容
        # 虽然我们不是 Webhook，但 MessageBuilder 生成的 MD 文本也适合邮件正文
        self.message_builder = MessageBuilder(email_config)
    
    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self.server) and bool(self.user) and bool(self.recipient)
    
    def send(self, training_info: Dict[str, Any]) -> bool:
        """
        发送邮件通知
        
        Args:
            training_info: 任务信息字典
            
        Returns:
            bool: 发送是否成功
        """
        if not self.enabled:
            logger.info("邮件通知已禁用或配置不完整")
            return False
        
        # 构建HTML格式的邮件内容
        html_content = self.message_builder.build_html_content(training_info)
        
        # 解析收件人列表 (支持逗号或分号分隔)
        recipients = [r.strip() for r in self.recipient.replace(';', ',').split(',') if r.strip()]
        if not recipients:
            logger.warning("没有有效的邮件收件人地址")
            return False
            
        # 创建HTML邮件
        msg = MIMEText(html_content, 'html', 'utf-8')
        msg['From'] = self.sender
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = Header(self.title, 'utf-8')

        
        try:
            context = ssl.create_default_context()
            
            if self.use_ssl:
                logger.debug(f"正在通过 SSL 连接到 {self.server}:{self.port}...")
                server = smtplib.SMTP_SSL(self.server, self.port, context=context, timeout=30)
            else:
                logger.debug(f"正在连接到 {self.server}:{self.port}...")
                server = smtplib.SMTP(self.server, self.port, timeout=30)
            
            try:
                server.ehlo()
                
                if not self.use_ssl:
                    # 如果不是 SSL 连接，尝试升级到 STARTTLS
                    if server.has_extn("STARTTLS"):
                        logger.debug("正在发送 STARTTLS...")
                        server.starttls(context=context)
                        server.ehlo()
                
                if self.user and self.password:
                    logger.debug(f"正在登录 SMTP 用户: {self.user}...")
                    server.login(self.user, self.password)
                
                server.sendmail(self.sender, recipients, msg.as_string())
                logger.info(f"成功发送通知邮件到 {', '.join(recipients)}")
                return True
                
            finally:
                # 确保正确关闭连接,忽略关闭时的异常
                try:
                    server.quit()
                except Exception:
                    pass  # 忽略quit时的异常,邮件已发送成功
                
        except smtplib.SMTPException as e:
            logger.error(f"SMTP 错误: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"发送邮件时发生异常: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
