#!/usr/bin/env python3
"""内存监控核心模块"""
import psutil
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Optional
from config import HISTORY_LENGTH, SPIKE_CHECK_WINDOW, MEMORY_SPIKE_THRESHOLD

@dataclass
class ProcessMemoryInfo:
    pid: int
    name: str
    memory_percent: float
    memory_mb: float

class MemoryMonitor:
    def __init__(self):
        self.process_history: Dict[int, deque] = defaultdict(
            lambda: deque(maxlen=HISTORY_LENGTH)
        )
        self.system_history: deque = deque(maxlen=HISTORY_LENGTH)
    
    def get_system_memory(self) -> float:
        """获取系统内存使用百分比"""
        mem = psutil.virtual_memory()
        percent = mem.percent
        self.system_history.append(percent)
        return percent
    
    def get_top_processes(self, limit: int = 10) -> List[ProcessMemoryInfo]:
        """获取内存占用最高的进程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
            try:
                info = proc.info
                if info['memory_percent'] and info['memory_percent'] > 0.1:
                    memory_mb = info['memory_info'].rss / (1024 * 1024) if info['memory_info'] else 0
                    processes.append(ProcessMemoryInfo(
                        pid=info['pid'],
                        name=info['name'] or 'Unknown',
                        memory_percent=info['memory_percent'],
                        memory_mb=memory_mb
                    ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        processes.sort(key=lambda x: x.memory_percent, reverse=True)
        return processes[:limit]
    
    def update_process_history(self, processes: List[ProcessMemoryInfo]):
        """更新进程内存历史记录"""
        for proc in processes:
            self.process_history[proc.pid].append({
                'name': proc.name,
                'percent': proc.memory_percent,
                'mb': proc.memory_mb
            })
    
    def detect_memory_spike(self, processes: List[ProcessMemoryInfo], spike_threshold: float = None) -> List[ProcessMemoryInfo]:
        """检测内存突变的进程"""
        if spike_threshold is None:
            spike_threshold = MEMORY_SPIKE_THRESHOLD
        spike_processes = []
        for proc in processes:
            history = self.process_history.get(proc.pid)
            if history and len(history) >= SPIKE_CHECK_WINDOW:
                old_values = list(history)[-SPIKE_CHECK_WINDOW:-1]
                if old_values:
                    avg_old = sum(h['percent'] for h in old_values) / len(old_values)
                    if avg_old > 0:
                        change_percent = ((proc.memory_percent - avg_old) / avg_old) * 100
                        if change_percent > spike_threshold:
                            spike_processes.append(proc)
        return spike_processes
    
    def get_process_history(self, pid: int) -> List[dict]:
        """获取指定进程的内存历史"""
        return list(self.process_history.get(pid, []))
    
    def get_system_history(self) -> List[float]:
        """获取系统内存历史"""
        return list(self.system_history)
