# -*- coding: utf-8 -*-
"""
默认配置定义模块

包含 TaskNya 所有配置项的默认值。
"""

# 默认配置
DEFAULT_CONFIG = {
    "monitor": {
        "project_name": "监控任务",
        "check_interval": 60,
        "timeout": None,
        "logprint": 60,
        
        # 单文件感知
        "check_file_enabled": False,
        "check_file_path": "/tmp/test_file.txt",
        "check_file_detect_deletion": True,  # 是否检测文件删除
        "check_file_recheck_delay": 0,  # 二次检查延迟（秒），0=禁用
        
        # 日志检查
        "check_log_enabled": False,
        "check_log_path": "/tmp/test.log",
        "check_log_markers": ["完成", "done"],
        "check_log_mode": "full",  # 日志检测模式 ("full" 或 "incremental")
        
        # GPU功耗检查
        "check_gpu_power_enabled": False,
        "check_gpu_power_threshold": 50.0,
        "check_gpu_power_gpu_ids": "all",
        "check_gpu_power_consecutive_checks": 3,
        "check_gpu_power_trigger_mode": "below",  # 触发模式: "below" 低于阈值, "above" 高于阈值
        
        # 多文件感知（目录监控）
        "check_directory_enabled": False,
        "check_directory_path": "C:\\Users\\",
        "check_directory_include_folders": False,  # 是否检测文件夹变化
        "check_directory_exclude_keywords": ["年报", "测试用素材", "往期周报", "视频模板"],  # 排除路径关键词
        "check_directory_report_path": "",  # 报告路径，None=扫描目录下
        "check_directory_recheck_delay": 20,  # 二次检查延迟（秒）
        "check_directory_action_keywords": {
            "准备压制视频了哦(๑•̀ㅂ•́)ﻭ✧": ["无字幕"],
            "压制视频已上传(◦˙▽˙◦)": ["x264"],
            "字幕准备就绪ヾ(≧▽≦*)o": ["已校"],
            "视频工程文件已上传(◦˙▽˙◦)": ["已复制"],
            "视频组件已上传o((^▽^))o": ["片头", "片尾"],
            "请注意校对字幕(✿◡‿◡)": ["未校"],
            "音频缩混已上传(๑˃̵ᴗ˂̵)ﻭ": ["缩混"]
        },
        "check_directory_detect_added": True,    # 检测新增
        "check_directory_detect_removed": False,  # 检测删除
        "check_directory_detect_modified": False, # 检测修改（默认关闭，防噪）
        "check_directory_continuous_mode": True,  # 持续监控模式：触发通知后继续运行
    },
    
    "webhook": {
        "enabled": True,
        "url": "https://test.webhook.url/hook",
        "title": "测试通知",
        "color": "green",
        "include_project_name": True,
        "include_project_name_title": "项目",

        "include_start_time": True,
        "include_start_time_title": "开始",

        "include_end_time": True,
        "include_end_time_title": "结束",

        "include_method": True,
        "include_method_title": "方式",

        "include_duration": True,
        "include_duration_title": "耗时",

        "include_hostname": True,
        "include_hostname_title": "主机",

        "include_gpu_info": False,
        "include_gpu_info_title": "GPU",
        
        # 目录监控报告显示选项
        "include_report_summary": True,    # 显示报告摘要统计
        "include_report_details": True,    # 显示详细文件列表
        "include_report_actions": True,    # 显示建议操作

        "footer": "测试消息"
    },
    
    # 通用 Webhook 配置
    "generic_webhook": {
        "enabled": False,
        "url": "http://xxxx.xxx.xxxx:10010/send",
        "method": "POST",  # POST, PUT, GET, DELETE
        "headers": {
            "Authorization": "Bearer xxxxxxxx",
            "Content-Type": "application/json"
        },
        "body": "{\n  \"content\": \"[ ${project_name} ]\\n----------------------------\\n触发方式: ${method}\\n触发详情: ${detail}\\n----------------------------\\n[ 数据统计 ]\\n报告统计: ${report_summary}\\n变更列表: ${report_change_list}\\n提示: ${report_actions}\\n----------------------------\\n详情查看: https://xxxx.xxxx.xxxx:xxxx\\n\\n${anime_quote}\\n[ 来自 XiaoXue-TaskNya 推送 ]\",\n  \"umo\": \"飘雪:GroupMessage:xxxxxxxx\",\n  \"message_type\": \"text\"\n}",
        "retry_count": 2,  # 重试次数 0-5
        "timeout": 10,  # 请求超时（秒）
        "anime_quote_enabled": True,  # 是否在消息中追加二次元语录
    },
    
    "email": {
        "enabled": True,
        "smtp_server": "smtp.qq.com",
        "smtp_port": 465,
        "smtp_user": "",
        "smtp_password": "",  # 授权码或密码
        "sender": "",         # 发件人地址，通常同 smtp_user
        "recipient": "",      # 收件人地址
        "use_ssl": True,
        "title": "🎉 TaskNya 任务完成通知",
        "footer": "此邮件由 TaskNya 自动发送",
        
        # 内容显示选项(与webhook共享MessageBuilder配置)
        "include_project_name": True,
        "include_start_time": True,
        "include_end_time": True,
        "include_method": True,
        "include_duration": True,
        "include_hostname": True,
        "include_gpu_info": True,
        
        # 目录监控报告显示选项
        "include_report_summary": True,    # 显示报告摘要统计
        "include_report_details": True,    # 显示详细文件列表
        "include_report_actions": True,    # 显示建议操作
    }
}

