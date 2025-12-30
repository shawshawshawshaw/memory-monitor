# 内存监控报警工具

## 版本历史

### v2.0 - Swift版本 (当前)
- 使用SwiftUI重写，原生macOS应用
- **新功能：进程合并统计** - 同名/相关进程自动合并显示（如Chrome多进程）
- 支持展开查看进程树详情
- 实时内存走势图（Swift Charts）
- 系统内存报警和进程内存突变检测
- macOS原生通知

### v1.0 - Python版本 (备份于 python_v1.0_backup/)
- 基于Tkinter/matplotlib的GUI
- 系统内存监控和报警
- 进程内存突变检测
- 依赖: psutil, matplotlib, terminal-notifier

## 运行方式

### Swift版本
```bash
cd MemoryMonitor
swift build
.build/debug/MemoryMonitor
```

### Python版本
```bash
cd python_v1.0_backup
pip install -r requirements.txt
python main.py
```
