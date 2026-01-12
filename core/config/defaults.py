# -*- coding: utf-8 -*-
"""
默认配置定义模块

包含 TaskNya 所有配置项的默认值。
"""

# 默认配置
DEFAULT_CONFIG = {
    "monitor": {
        "project_name": "深度学习训练",
        "check_interval": 5,
        "timeout": None,
        "logprint": 60,
        
        # 单文件感知
        "check_file_enabled": True,
        "check_file_path": "./output/model_final.pth",
        "check_file_detect_deletion": False,  # 是否检测文件删除
        "check_file_recheck_delay": 0,  # 二次检查延迟（秒），0=禁用
        
        # 日志检查
        "check_log_enabled": False,
        "check_log_path": "./logs/training.log",
        "check_log_markers": ["Training completed", "训练完成"],
        "check_log_mode": "full",  # 日志检测模式 ("full" 或 "incremental")
        
        # GPU功耗检查
        "check_gpu_power_enabled": False,
        "check_gpu_power_threshold": 50.0,
        "check_gpu_power_gpu_ids": "all",
        "check_gpu_power_consecutive_checks": 3,
        "check_gpu_power_trigger_mode": "below",  # 触发模式: "below" 低于阈值, "above" 高于阈值
        
        # 多文件感知（目录监控）
        "check_directory_enabled": False,
        "check_directory_path": "",
        "check_directory_include_folders": False,  # 是否检测文件夹变化
        "check_directory_exclude_keywords": [],  # 排除路径关键词
        "check_directory_report_path": None,  # 报告路径，None=扫描目录下
        "check_directory_recheck_delay": 5,  # 二次检查延迟（秒）
        "check_directory_action_keywords": {
            "备份": ["重要", "backup"],
            "检查": ["error", "warn"],
            "发布": ["release", "dist"]
        },
        "check_directory_detect_added": True,    # 检测新增
        "check_directory_detect_removed": True,  # 检测删除
        "check_directory_detect_modified": False, # 检测修改（默认关闭，防噪）
    },
    
    "webhook": {
        "enabled": True,
        "url": "https://open.feishu.cn/open-apis/bot/v2/hook/yoururl",
        "title": "🎉 任务完成通知",
        "color": "green",
        "include_project_name": True,
        "include_project_name_title": "训练项目",

        "include_start_time": True,
        "include_start_time_title": "训练开始",

        "include_end_time": True,
        "include_end_time_title": "训练结束时间",

        "include_method": True,
        "include_method_title": "系统判断依据",

        "include_duration": True,
        "include_duration_title": "总耗时",

        "include_hostname": True,
        "include_hostname_title": "主机名",

        "include_gpu_info": True,
        "include_gpu_info_title": "GPU信息",

        "footer": "此消息由TaskNya发送"
    },
    
    # 通用 Webhook 配置
    "generic_webhook": {
        "enabled": False,
        "url": "",
        "method": "POST",  # POST, PUT, GET, DELETE
        "headers": {"Content-Type": "application/json"},
        "body": "",  # 自定义 Body 模板
        "builtin_template": None,  # 内置模板: astrbot, text, json, discord
        "retry_count": 0,  # 重试次数 0-5
        "timeout": 10,  # 请求超时（秒）
        "anime_quote_enabled": False,  # 是否在消息中追加二次元语录
        
        # AstrBot 简易模式
        "astrbot_mode": False,  # 开启后直接填写内容即可
        "astrbot_umo": "",  # AstrBot UMO 参数，如 "机器人名:GroupMessage:1067617112"
        "astrbot_header": "文件变动",  # 通知表头
        "astrbot_content": "",  # 通知主内容
        "astrbot_extra": "",  # 其他内容（可选）
        "astrbot_include_quote": True,  # 是否追加二次元语录
    }
}

