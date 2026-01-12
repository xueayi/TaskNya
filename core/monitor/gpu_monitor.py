# -*- coding: utf-8 -*-
"""
GPU 功耗监控模块

检测 GPU 功耗是否持续低于指定阈值。
"""

import subprocess
import logging
from typing import Tuple, Optional, Dict, Any, List, Union

from core.monitor.base import BaseMonitor

logger = logging.getLogger(__name__)


class GpuMonitor(BaseMonitor):
    """
    GPU 功耗监控器
    
    当 GPU 功耗连续多次低于/高于指定阈值时，视为任务完成。
    
    Attributes:
        threshold (float): 功耗阈值（瓦特）
        gpu_ids (Union[str, List[int]]): 要监控的 GPU ID
        consecutive_checks (int): 需要连续满足条件的次数
        trigger_mode (str): 触发模式 ("below" 或 "above")
        low_power_count (int): 当前连续满足条件的次数
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 GPU 监控器
        
        Args:
            config: monitor 配置字典，需包含:
                - check_gpu_power_enabled: 是否启用
                - check_gpu_power_threshold: 功耗阈值
                - check_gpu_power_gpu_ids: GPU ID ("all" 或 列表)
                - check_gpu_power_consecutive_checks: 连续检测次数
                - check_gpu_power_trigger_mode: 触发模式 ("below" 或 "above")
        """
        self._enabled = config.get('check_gpu_power_enabled', False)
        self.threshold = config.get('check_gpu_power_threshold', 50.0)
        self.gpu_ids = config.get('check_gpu_power_gpu_ids', 'all')
        self.consecutive_checks = config.get('check_gpu_power_consecutive_checks', 3)
        self.trigger_mode = config.get('check_gpu_power_trigger_mode', 'below')
        self.low_power_count = 0
    
    @property
    def name(self) -> str:
        return "GPU功耗监控"
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def check(self) -> Tuple[bool, str, Optional[str]]:
        """
检查 GPU 功耗是否满足触发条件
        
        Returns:
            Tuple[bool, str, Optional[str]]:
                - bool: 是否连续多次满足条件
                - str: "GPU功耗检测"
                - Optional[str]: None
        """
        if not self._enabled:
            return False, "未启用", None
        
        mode_desc = "低于" if self.trigger_mode == "below" else "高于"
            
        try:
            if self._check_power_threshold():
                self.low_power_count += 1
                logger.info(f"GPU功耗{mode_desc}阈值次数: [{self.low_power_count}/{self.consecutive_checks}]")
                
                if self.low_power_count >= self.consecutive_checks:
                    logger.info(f"GPU功耗已连续{self.consecutive_checks}次{mode_desc}阈值{self.threshold}W，判定任务完成")
                    return True, "GPU功耗检测", None
            else:
                # 重置计数器
                self.low_power_count = 0
                
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("未检测到NVIDIA显卡或nvidia-smi不可用，跳过GPU功耗检查")
            
        return False, "未完成", None
    
    def _check_power_threshold(self) -> bool:
        """
        检查 GPU 功耗是否满足阈值条件
        
        Returns:
            bool: 是否所有指定 GPU 的功耗都满足条件
        """
        try:
            output = subprocess.check_output(
                ['nvidia-smi', '--query-gpu=index,power.draw', '--format=csv,noheader,nounits'],
                universal_newlines=True
            )
            
            # 解析输出
            gpu_power_info = {}
            for line in output.strip().split('\n'):
                if ',' in line:
                    idx, power = line.split(',')
                    gpu_power_info[int(idx.strip())] = float(power.strip())
            
            logger.debug(f"当前GPU功耗: {gpu_power_info}")
            
            # 确定要检查的 GPU 列表
            check_gpus = self._get_gpu_list(gpu_power_info)
            
            # 检查所有指定 GPU 的功耗是否都满足条件
            for gpu_id in check_gpus:
                if gpu_id in gpu_power_info:
                    power = gpu_power_info[gpu_id]
                    if self.trigger_mode == "below":
                        if power >= self.threshold:
                            logger.debug(f"GPU {gpu_id} 功耗 {power}W 不低于阈值 {self.threshold}W")
                            return False
                    else:  # above
                        if power <= self.threshold:
                            logger.debug(f"GPU {gpu_id} 功耗 {power}W 不高于阈值 {self.threshold}W")
                            return False
            
            return True
            
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("未检测到NVIDIA显卡或nvidia-smi不可用")
            return False
        except Exception as e:
            logger.error(f"检查GPU功耗失败: {str(e)}")
            return False
    
    def _get_gpu_list(self, gpu_power_info: Dict[int, float]) -> List[int]:
        """
        获取要检查的 GPU 列表
        
        Args:
            gpu_power_info: GPU 功耗信息字典
            
        Returns:
            GPU ID 列表
        """
        if self.gpu_ids == 'all':
            return list(gpu_power_info.keys())
        elif isinstance(self.gpu_ids, list):
            return [int(gid) for gid in self.gpu_ids]
        else:
            return [int(self.gpu_ids)]
    
    def reset(self):
        """重置计数器"""
        self.low_power_count = 0
