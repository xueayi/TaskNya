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
        
        # 日志检查
        "check_log_enabled": False,
        "check_log_path": "./logs/training.log",
        "check_log_markers": ["Training completed", "训练完成"],
        "check_log_mode": "full",  # 日志检测模式 ("full" 或 "incremental")
        
        # GPU功耗检查
        "check_gpu_power_enabled": False,
        "check_gpu_power_threshold": 50.0,
        "check_gpu_power_gpu_ids": "all",
        "check_gpu_power_consecutive_checks": 3
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
    }
}
