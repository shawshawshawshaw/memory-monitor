#!/usr/bin/env python3
"""内存监控报警工具 - 主程序"""
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from memory_monitor import MemoryMonitor, ProcessMemoryInfo
from config import MEMORY_THRESHOLD, MONITOR_INTERVAL

class MemoryAlertApp:
    def __init__(self, root):
        self.root = root
        self.root.title("内存监控报警工具")
        self.root.geometry("800x600")
        self.monitor = MemoryMonitor()
        self.selected_pid = None
        self.alert_shown = False
        self.setup_ui()
        self.start_monitoring()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 系统内存状态
        status_frame = ttk.LabelFrame(main_frame, text="系统内存状态", padding="5")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mem_label = ttk.Label(status_frame, text="系统内存: 计算中...", font=("", 14))
        self.mem_label.pack(side=tk.LEFT, padx=10)
        
        self.status_label = ttk.Label(status_frame, text="状态: 正常", font=("", 14), foreground="green")
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # 进程列表
        list_frame = ttk.LabelFrame(main_frame, text="内存占用TOP进程 (双击查看走势)", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("pid", "name", "percent", "mb")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        self.tree.heading("pid", text="PID")
        self.tree.heading("name", text="进程名")
        self.tree.heading("percent", text="内存占比(%)")
        self.tree.heading("mb", text="内存(MB)")
        self.tree.column("pid", width=80)
        self.tree.column("name", width=200)
        self.tree.column("percent", width=100)
        self.tree.column("mb", width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", self.on_process_select)
        
        # 走势图
        chart_frame = ttk.LabelFrame(main_frame, text="内存走势图", padding="5")
        chart_frame.pack(fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(8, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def start_monitoring(self):
        """开始监控"""
        self.update_data()
    
    def update_data(self):
        """更新监控数据"""
        mem_percent = self.monitor.get_system_memory()
        processes = self.monitor.get_top_processes(15)
        self.monitor.update_process_history(processes)
        
        # 更新系统内存显示
        self.mem_label.config(text=f"系统内存: {mem_percent:.1f}%")
        
        # 检查报警条件
        alerts = []
        if mem_percent >= MEMORY_THRESHOLD:
            alerts.append(f"系统内存使用率达到 {mem_percent:.1f}%!")
            self.status_label.config(text="状态: 警告!", foreground="red")
        else:
            self.status_label.config(text="状态: 正常", foreground="green")
        
        # 检测内存突变
        spike_procs = self.monitor.detect_memory_spike(processes)
        for proc in spike_procs:
            alerts.append(f"进程 [{proc.name}] (PID:{proc.pid}) 内存突变! 当前: {proc.memory_percent:.1f}%")
        
        # 显示报警
        if alerts and not self.alert_shown:
            self.show_alert(alerts, spike_procs + ([processes[0]] if mem_percent >= MEMORY_THRESHOLD else []))
        elif not alerts:
            self.alert_shown = False
        
        # 更新进程列表
        self.update_process_list(processes, spike_procs)
        
        # 更新走势图
        self.update_chart()
        
        # 继续监控
        self.root.after(MONITOR_INTERVAL, self.update_data)
    
    def update_process_list(self, processes, spike_procs):
        """更新进程列表"""
        spike_pids = {p.pid for p in spike_procs}
        for item in self.tree.get_children():
            self.tree.delete(item)
        for proc in processes:
            tags = ("spike",) if proc.pid in spike_pids else ()
            self.tree.insert("", tk.END, values=(
                proc.pid, proc.name, f"{proc.memory_percent:.2f}", f"{proc.memory_mb:.1f}"
            ), tags=tags)
        self.tree.tag_configure("spike", background="#ffcccc")
    
    def update_chart(self):
        """更新走势图"""
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
        """显示报警弹窗"""
        self.alert_shown = True
        msg = "内存报警!\n\n" + "\n".join(alerts)
        if problem_procs:
            msg += "\n\n异常进程详情:\n"
            for p in problem_procs[:3]:
                msg += f"  - {p.name} (PID:{p.pid}): {p.memory_percent:.1f}% ({p.memory_mb:.0f}MB)\n"
        messagebox.showwarning("内存报警", msg)
    
    def on_process_select(self, event):
        """双击进程查看走势"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.selected_pid = int(item['values'][0])
        else:
            self.selected_pid = None
        self.update_chart()


def main():
    root = tk.Tk()
    app = MemoryAlertApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
