# -*- coding: utf-8 -*-
"""
目录监控模块（多文件感知）

递归监控指定目录中的文件变化，支持二次确认和报告生成。
"""

import os
import time
import logging
from datetime import datetime
from typing import Tuple, Optional, Dict, Any, List, Set
from dataclasses import dataclass, field

from core.monitor.base import BaseMonitor

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """文件信息"""
    path: str
    name: str
    size: int
    mtime: float
    is_dir: bool
    
    @property
    def mtime_str(self) -> str:
        """格式化的修改时间"""
        return datetime.fromtimestamp(self.mtime).strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def size_str(self) -> str:
        """格式化的文件大小"""
        if self.is_dir:
            return "<目录>"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.size < 1024:
                return f"{self.size:.1f} {unit}"
            self.size /= 1024
        return f"{self.size:.1f} TB"


@dataclass
class FileChange:
    """文件变化信息"""
    change_type: str  # "added", "removed", "modified"
    file_info: FileInfo
    suggested_action: str = ""


@dataclass
class DirectorySnapshot:
    """目录快照"""
    scan_time: datetime
    files: Dict[str, FileInfo] = field(default_factory=dict)


class DirectoryMonitor(BaseMonitor):
    """
    目录监控器（多文件感知）
    
    递归扫描目录变化，支持二次确认和报告生成。
    
    Attributes:
        scan_path (str): 扫描路径
        include_folders (bool): 是否检测文件夹变化
        exclude_keywords (list): 排除路径关键词
        report_path (str): 报告保存路径
        recheck_delay (int): 二次检查延迟秒数
        action_keywords (dict): 操作建议关键词组
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化目录监控器
        
        Args:
            config: monitor 配置字典
        """
        self._enabled = config.get('check_directory_enabled', False)
        self.scan_path = config.get('check_directory_path', '')
        self.include_folders = config.get('check_directory_include_folders', False)
        self.exclude_keywords = config.get('check_directory_exclude_keywords', [])
        self.report_path = config.get('check_directory_report_path', None)
        try:
            self.recheck_delay = int(config.get('check_directory_recheck_delay', 5))
        except (ValueError, TypeError):
            self.recheck_delay = 5
        self.action_keywords = config.get('check_directory_action_keywords', {})
        if not isinstance(self.action_keywords, dict):
            self.action_keywords = {}
        
        # 检测类型开关
        self.detect_added = config.get('check_directory_detect_added', True)
        self.detect_removed = config.get('check_directory_detect_removed', True)
        self.detect_modified = config.get('check_directory_detect_modified', False)
        
        # 持续监控模式：触发通知后继续运行
        self.continuous_mode = config.get('check_directory_continuous_mode', False)
        
        # 状态
        self._last_snapshot: Optional[DirectorySnapshot] = None
        self._pending_changes: Optional[List[FileChange]] = None
        self._pending_timestamp: Optional[float] = None
        self._initialized = False
        self._last_report_data: Optional[Dict[str, Any]] = None  # 用于通知变量
    
    @property
    def name(self) -> str:
        return "目录监控"
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def check(self) -> Tuple[bool, str, Optional[str]]:
        """
        检查目录变化
        
        Returns:
            Tuple[bool, str, Optional[str]]:
                - bool: 是否检测到变化（二次确认后）
                - str: "目录变化检测"
                - Optional[str]: 变化详情
        """
        if not self._enabled:
            return False, "未启用", None
        
        if not self.scan_path or not os.path.exists(self.scan_path):
            logger.warning(f"目录监控路径不存在: {self.scan_path}")
            return False, "路径不存在", None
        
        # 初始化快照
        if not self._initialized:
            self._initialize_snapshot()
            return False, "初始化中", None
        
        # 扫描当前状态
        current_snapshot = self._scan_directory()
        
        # 检测变化
        changes = self._detect_changes(self._last_snapshot, current_snapshot)
        
        if not changes:
            # 无变化，重置待确认状态
            self._pending_changes = None
            self._pending_timestamp = None
            return False, "未完成", None
        
        # 有变化，检查是否需要二次确认
        if self.recheck_delay > 0:
            if self._pending_changes is None:
                # 首次检测到变化，记录并等待
                self._pending_changes = changes
                self._pending_timestamp = time.time()
                logger.info(f"检测到 {len(changes)} 处变化，等待 {self.recheck_delay} 秒进行二次确认")
                return False, "等待二次确认", None
            else:
                # 检查是否到达二次确认时间
                if time.time() - self._pending_timestamp < self.recheck_delay:
                    return False, "等待二次确认", None
                
                # 二次确认：检查变化是否一致
                if self._changes_match(self._pending_changes, changes):
                    # 变化一致，确认触发
                    logger.info(f"二次确认通过，共 {len(changes)} 处变化")
                    self._last_snapshot = current_snapshot
                    self._pending_changes = None
                    self._pending_timestamp = None
                    
                    # 生成报告
                    report = self._generate_report(changes)
                    return True, "目录变化检测", report
                else:
                    # 变化不一致，重新等待
                    logger.info("二次确认变化不一致，继续监控")
                    self._pending_changes = changes
                    self._pending_timestamp = time.time()
                    return False, "变化不稳定", None
        else:
            # 不需要二次确认，直接触发
            self._last_snapshot = current_snapshot
            report = self._generate_report(changes)
            return True, "目录变化检测", report
    
    def _initialize_snapshot(self):
        """初始化目录快照"""
        logger.info(f"初始化目录监控: {self.scan_path}")
        self._last_snapshot = self._scan_directory()
        self._initialized = True
        logger.info(f"初始快照包含 {len(self._last_snapshot.files)} 个文件/目录")
    
    def _scan_directory(self) -> DirectorySnapshot:
        """
        递归扫描目录
        
        Returns:
            目录快照
        """
        snapshot = DirectorySnapshot(scan_time=datetime.now())
        
        try:
            for root, dirs, files in os.walk(self.scan_path):
                # 检查是否排除
                if self._should_exclude(root):
                    dirs[:] = []  # 不再递归
                    continue
                
                # 处理目录
                if self.include_folders:
                    for dir_name in dirs:
                        if self._should_exclude(dir_name):
                            continue
                        dir_path = os.path.join(root, dir_name)
                        rel_path = os.path.relpath(dir_path, self.scan_path)
                        try:
                            stat = os.stat(dir_path)
                            snapshot.files[rel_path] = FileInfo(
                                path=rel_path,
                                name=dir_name,
                                size=0,
                                mtime=stat.st_mtime,
                                is_dir=True
                            )
                        except OSError:
                            pass
                
                # 处理文件
                for file_name in files:
                    if self._should_exclude(file_name):
                        continue
                    file_path = os.path.join(root, file_name)
                    rel_path = os.path.relpath(file_path, self.scan_path)
                    try:
                        stat = os.stat(file_path)
                        snapshot.files[rel_path] = FileInfo(
                            path=rel_path,
                            name=file_name,
                            size=stat.st_size,
                            mtime=stat.st_mtime,
                            is_dir=False
                        )
                    except OSError:
                        pass
                        
        except Exception as e:
            logger.error(f"扫描目录失败: {e}")
        
        return snapshot
    
    def _should_exclude(self, path: str) -> bool:
        """检查路径是否应被排除"""
        for keyword in self.exclude_keywords:
            if keyword.lower() in path.lower():
                return True
        return False
    
    def _detect_changes(self, 
                        old_snapshot: DirectorySnapshot,
                        new_snapshot: DirectorySnapshot) -> List[FileChange]:
        """
        检测两个快照之间的差异
        
        Args:
            old_snapshot: 旧快照
            new_snapshot: 新快照
            
        Returns:
            变化列表
        """
        changes = []
        old_files = old_snapshot.files
        new_files = new_snapshot.files
        
        # 检测新增文件
        if self.detect_added:
            for path, info in new_files.items():
                if path not in old_files:
                    action = self._suggest_action(info.name, "added")
                    changes.append(FileChange("added", info, action))
        
        # 检测删除文件
        if self.detect_removed:
            for path, info in old_files.items():
                if path not in new_files:
                    action = self._suggest_action(info.name, "removed")
                    changes.append(FileChange("removed", info, action))
        
        # 检测修改文件（大小或时间变化）
        if self.detect_modified:
            for path, new_info in new_files.items():
                if path in old_files:
                    old_info = old_files[path]
                    if old_info.size != new_info.size or old_info.mtime != new_info.mtime:
                        action = self._suggest_action(new_info.name, "modified")
                        changes.append(FileChange("modified", new_info, action))
        
        return changes
    
    def _changes_match(self, 
                       changes1: List[FileChange],
                       changes2: List[FileChange]) -> bool:
        """
        检查两组变化是否一致
        
        Args:
            changes1: 第一组变化
            changes2: 第二组变化
            
        Returns:
            是否一致
        """
        if len(changes1) != len(changes2):
            return False
        
        paths1 = {(c.change_type, c.file_info.path) for c in changes1}
        paths2 = {(c.change_type, c.file_info.path) for c in changes2}
        
        return paths1 == paths2
    
    def _suggest_action(self, filename: str, change_type: str) -> str:
        """
        根据关键词匹配建议操作
        
        Args:
            filename: 文件名
            change_type: 变化类型
            
        Returns:
            建议操作
        """
        filename_lower = filename.lower()
        
        for action, keywords in self.action_keywords.items():
            if isinstance(keywords, list):
                for keyword in keywords:
                    if keyword.lower() in filename_lower:
                        return action
            elif isinstance(keywords, str):
                if keywords.lower() in filename_lower:
                    return action
        
        return ""
    
    def _generate_report(self, changes: List[FileChange]) -> str:
        """
        生成变化报告
        
        Args:
            changes: 变化列表
            
        Returns:
            报告内容
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 分类统计
        added = [c for c in changes if c.change_type == "added"]
        removed = [c for c in changes if c.change_type == "removed"]
        modified = [c for c in changes if c.change_type == "modified"]
        
        # 收集所有建议
        unique_actions = sorted(list(set(c.suggested_action for c in changes if c.suggested_action)))

        # 保存结构化数据用于通知变量
        self._last_report_data = {
            "timestamp": timestamp,
            "scan_path": self.scan_path,
            "total_changes": len(changes),
            "added_count": len(added),
            "removed_count": len(removed),
            "modified_count": len(modified),
            "added_files": [self._format_file_info(c) for c in added],
            "removed_files": [self._format_file_info(c) for c in removed],
            "modified_files": [self._format_file_info(c) for c in modified],
            "all_changes": [self._format_file_info(c) for c in changes],
            "summary": f"新增 {len(added)}, 删除 {len(removed)}, 修改 {len(modified)}",
            "actions": unique_actions,
        }
        
        lines = [
            f"=== 目录变化报告 ===",
            f"时间: {timestamp}",
            f"路径: {self.scan_path}",
            f"变化统计: {self._last_report_data['summary']}",
            ""
        ]
        
        # 详细变化
        change_type_names = {"added": "📥 新增", "removed": "🗑️ 删除", "modified": "✏️ 修改"}
        
        for change in changes:
            type_name = change_type_names.get(change.change_type, change.change_type)
            info = change.file_info
            
            line = f"{type_name} {info.path}"
            if not info.is_dir:
                line += f" ({info.size_str})"
            line += f" - {info.mtime_str}"
            
            if change.suggested_action:
                line += f" 💡{change.suggested_action}"
            
            lines.append(line)
        
        lines.append("")
        
        report = "\n".join(lines)
        
        # 保存报告到文件
        self._save_report(report)
        
        return report
    
    def _format_file_info(self, change: FileChange) -> Dict[str, Any]:
        """格式化文件变化信息为字典"""
        info = change.file_info
        return {
            "type": change.change_type,
            "path": info.path,
            "name": info.name,
            "size": info.size if not info.is_dir else 0,
            "size_str": info.size_str,
            "mtime": info.mtime_str,
            "is_dir": info.is_dir,
            "action": change.suggested_action,
        }
    
    def get_report_data(self) -> Optional[Dict[str, Any]]:
        """获取最后一次报告的结构化数据"""
        return self._last_report_data
    
    def _save_report(self, report: str):
        """保存报告到文件"""
        try:
            # 确定报告路径
            if self.report_path:
                report_file = self.report_path
            else:
                report_file = os.path.join(self.scan_path, "tasknya_monitor_report.txt")
            
            # 追加写入
            with open(report_file, 'a', encoding='utf-8') as f:
                f.write(report)
                f.write("\n\n")
            
            logger.info(f"报告已保存到: {report_file}")
            
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    def reset(self):
        """重置监控状态"""
        self._last_snapshot = None
        self._pending_changes = None
        self._pending_timestamp = None
        self._initialized = False
