#!/usr/bin/env python3
"""内存监控报警工具 - PySide6主程序"""
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QGroupBox, QMessageBox)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from memory_monitor import MemoryMonitor
from config import MEMORY_THRESHOLD, MONITOR_INTERVAL


class MemoryAlertApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.monitor = MemoryMonitor()
        self.selected_pid = None
        self.alert_shown = False
        self.init_ui()
        self.start_monitoring()
    
    def init_ui(self):
        self.setWindowTitle("内存监控报警工具")
        self.setGeometry(100, 100, 850, 650)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 状态栏
        status_group = QGroupBox("系统内存状态")
        status_layout = QHBoxLayout(status_group)
        self.mem_label = QLabel("系统内存: 计算中...")
        self.mem_label.setStyleSheet("font-size: 16px;")
        self.status_label = QLabel("状态: 正常")
        self.status_label.setStyleSheet("font-size: 16px; color: green;")
        status_layout.addWidget(self.mem_label)
        status_layout.addStretch()
        status_layout.addWidget(self.status_label)
        layout.addWidget(status_group)
        
        # 进程列表
        list_group = QGroupBox("内存占用TOP进程 (双击查看走势)")
        list_layout = QVBoxLayout(list_group)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["PID", "进程名", "内存占比(%)", "内存(MB)"])
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 250)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 120)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.on_process_select)
        list_layout.addWidget(self.table)
        layout.addWidget(list_group)
        
        # 走势图
        chart_group = QGroupBox("内存走势图")
        chart_layout = QVBoxLayout(chart_group)
        self.fig = Figure(figsize=(8, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        chart_layout.addWidget(self.canvas)
        layout.addWidget(chart_group)
    
    def start_monitoring(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(MONITOR_INTERVAL)
        self.update_data()
    
    def update_data(self):
        mem_percent = self.monitor.get_system_memory()
        processes = self.monitor.get_top_processes(15)
        self.monitor.update_process_history(processes)
        
        self.mem_label.setText(f"系统内存: {mem_percent:.1f}%")
        
        alerts = []
        if mem_percent >= MEMORY_THRESHOLD:
            alerts.append(f"系统内存使用率达到 {mem_percent:.1f}%!")
            self.status_label.setText("状态: 警告!")
            self.status_label.setStyleSheet("font-size: 16px; color: red;")
        else:
            self.status_label.setText("状态: 正常")
            self.status_label.setStyleSheet("font-size: 16px; color: green;")
        
        spike_procs = self.monitor.detect_memory_spike(processes)
        for proc in spike_procs:
            alerts.append(f"进程 [{proc.name}] (PID:{proc.pid}) 内存突变! 当前: {proc.memory_percent:.1f}%")
        
        if alerts and not self.alert_shown:
            self.show_alert(alerts, spike_procs + ([processes[0]] if mem_percent >= MEMORY_THRESHOLD else []))
        elif not alerts:
            self.alert_shown = False
        
        self.update_process_list(processes, spike_procs)
        self.update_chart()
    
    def update_process_list(self, processes, spike_procs):
        spike_pids = {p.pid for p in spike_procs}
        self.table.setRowCount(len(processes))
        for i, proc in enumerate(processes):
            self.table.setItem(i, 0, QTableWidgetItem(str(proc.pid)))
            self.table.setItem(i, 1, QTableWidgetItem(proc.name))
            self.table.setItem(i, 2, QTableWidgetItem(f"{proc.memory_percent:.2f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{proc.memory_mb:.1f}"))
            if proc.pid in spike_pids:
                for j in range(4):
                    self.table.item(i, j).setBackground(QColor(255, 200, 200))
    
    def update_chart(self):
        self.ax.clear()
        if self.selected_pid:
            history = self.monitor.get_process_history(self.selected_pid)
            if history:
                values = [h['percent'] for h in history]
                self.ax.plot(values, 'b-', linewidth=2)
                self.ax.set_title(f"进程 {history[-1]['name']} (PID:{self.selected_pid}) 内存走势")
                self.ax.set_ylabel("内存占比 (%)")
        else:
            history = self.monitor.get_system_history()
            if history:
                self.ax.plot(history, 'g-', linewidth=2)
                self.ax.axhline(y=MEMORY_THRESHOLD, color='r', linestyle='--', label=f'报警阈值({MEMORY_THRESHOLD}%)')
                self.ax.legend()
            self.ax.set_title("系统内存走势")
            self.ax.set_ylabel("内存使用率 (%)")
        self.ax.set_xlabel("时间点")
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
    
    def show_alert(self, alerts, problem_procs):
        self.alert_shown = True
        msg = "内存报警!\n\n" + "\n".join(alerts)
        if problem_procs:
            msg += "\n\n异常进程详情:\n"
            for p in problem_procs[:3]:
                msg += f"  - {p.name} (PID:{p.pid}): {p.memory_percent:.1f}%\n"
        QMessageBox.warning(self, "内存报警", msg)
    
    def on_process_select(self, index):
        row = index.row()
        pid_item = self.table.item(row, 0)
        if pid_item:
            self.selected_pid = int(pid_item.text())
            self.update_chart()


def main():
    app = QApplication(sys.argv)
    window = MemoryAlertApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
