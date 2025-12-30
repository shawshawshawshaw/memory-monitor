#!/usr/bin/env python3
"""内存监控报警工具 - 简约版"""
import sys
import json
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QDialog,
    QSpinBox, QFormLayout, QDialogButtonBox)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from memory_monitor import MemoryMonitor
from notifier import send_notification

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'user_config.json')

def load_config():
    default = {'threshold': 95, 'spike_threshold': 20, 'interval': 2000}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return {**default, **json.load(f)}
        except:
            pass
    return default

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f)


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(280, 150)
        layout = QFormLayout(self)
        
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(50, 99)
        self.threshold_spin.setValue(config['threshold'])
        layout.addRow("系统内存报警阈值(%):", self.threshold_spin)
        
        self.spike_spin = QSpinBox()
        self.spike_spin.setRange(5, 100)
        self.spike_spin.setValue(config['spike_threshold'])
        layout.addRow("进程突变阈值(%):", self.spike_spin)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def get_values(self):
        return {'threshold': self.threshold_spin.value(), 
                'spike_threshold': self.spike_spin.value()}


class MemoryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.monitor = MemoryMonitor()
        self.selected_pid = None
        self.alert_cooldown = 0
        self.init_ui()
        self.start_monitoring()
    
    def init_ui(self):
        self.setWindowTitle("内存监控")
        self.setFixedSize(360, 420)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 顶部状态栏
        top = QHBoxLayout()
        self.mem_label = QLabel("系统: --%")
        self.mem_label.setFont(QFont("", 13, QFont.Bold))
        top.addWidget(self.mem_label)
        top.addStretch()
        
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(28, 28)
        settings_btn.clicked.connect(self.open_settings)
        top.addWidget(settings_btn)
        layout.addLayout(top)
        
        # 进程列表
        list_label = QLabel("进程列表 (点击查看走势)")
        list_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(list_label)
        
        self.proc_list = QListWidget()
        self.proc_list.setFixedHeight(140)
        self.proc_list.setStyleSheet("QListWidget { font-size: 12px; }")
        self.proc_list.itemClicked.connect(self.on_item_click)
        layout.addWidget(self.proc_list)
        
        # 走势图
        self.chart_label = QLabel("系统内存走势")
        self.chart_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.chart_label)
        
        self.fig = Figure(figsize=(3.4, 1.8), dpi=100)
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.15)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
    
    def start_monitoring(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(self.config['interval'])
        self.update_data()
    
    def update_data(self):
        mem_percent = self.monitor.get_system_memory()
        processes = self.monitor.get_top_processes(10)
        self.monitor.update_process_history(processes)
        
        # 更新状态
        color = "red" if mem_percent >= self.config['threshold'] else "#333"
        self.mem_label.setText(f"系统: {mem_percent:.1f}%")
        self.mem_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
        
        # 检测报警
        if self.alert_cooldown > 0:
            self.alert_cooldown -= 1
        else:
            self.check_alerts(mem_percent, processes)
        
        self.update_list(processes)
        self.update_chart()
    
    def check_alerts(self, mem_percent, processes):
        alerts = []
        if mem_percent >= self.config['threshold']:
            alerts.append(f"系统内存 {mem_percent:.1f}%")
        
        spike_procs = self.monitor.detect_memory_spike(processes, self.config['spike_threshold'])
        for p in spike_procs[:2]:
            alerts.append(f"{p.name} 内存突变")
        
        if alerts:
            send_notification("内存报警", " | ".join(alerts))
            self.alert_cooldown = 15
    
    def update_list(self, processes):
        current_row = self.proc_list.currentRow()
        self.proc_list.clear()
        for p in processes:
            item = QListWidgetItem(f"{p.name:<20} {p.memory_percent:>5.1f}%")
            item.setData(Qt.UserRole, p.pid)
            self.proc_list.addItem(item)
        if current_row >= 0 and current_row < self.proc_list.count():
            self.proc_list.setCurrentRow(current_row)
    
    def update_chart(self):
        self.ax.clear()
        if self.selected_pid:
            history = self.monitor.get_process_history(self.selected_pid)
            if history:
                self.ax.plot([h['percent'] for h in history], 'b-', lw=1.5)
        else:
            history = self.monitor.get_system_history()
            if history:
                self.ax.plot(history, 'g-', lw=1.5)
                self.ax.axhline(y=self.config['threshold'], color='r', ls='--', lw=1)
        self.ax.set_ylabel('%', fontsize=9)
        self.ax.tick_params(labelsize=8)
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
    
    def on_item_click(self, item):
        self.selected_pid = item.data(Qt.UserRole)
        name = item.text().split()[0]
        self.chart_label.setText(f"{name} 内存走势")
        self.update_chart()
    
    def open_settings(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            vals = dlg.get_values()
            self.config.update(vals)
            save_config(self.config)


def main():
    app = QApplication(sys.argv)
    window = MemoryApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
