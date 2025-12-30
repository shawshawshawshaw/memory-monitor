# 内存监控报警工具

一款简约的 macOS 桌面内存监控工具，支持系统内存报警和进程内存突变检测。

## 功能特性

- 实时监控系统内存使用率
- 显示内存占用 TOP 进程列表
- 检测进程内存短时间内突变
- 点击进程查看内存走势图
- macOS 原生通知报警
- 可自定义报警阈值

## 安装

```bash
cd /Users/haws/Desktop/xiangmu/内存监控报警

# 创建虚拟环境
python3 -m venv venv

# 安装依赖
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install PySide6
```

## 运行

```bash
./run.sh
```

## 使用说明

### 主界面

| 区域 | 说明 |
|------|------|
| 顶部 | 显示系统内存使用率，超阈值变红 |
| ⚙ 按钮 | 打开设置面板 |
| 进程列表 | 显示内存占用最高的进程 |
| 走势图 | 默认显示系统内存，点击进程切换 |

### 设置选项

- **系统内存报警阈值**: 默认 95%，超过此值触发报警
- **进程突变阈值**: 默认 20%，进程内存短时间变化超过此比例触发报警

### 报警机制

报警通过 macOS 系统通知显示在屏幕右上角，触发条件：

1. 系统内存使用率 >= 设定阈值
2. 某进程内存短时间内变化超过突变阈值

## 文件结构

```
内存监控报警/
├── main_simple.py    # 主程序
├── memory_monitor.py # 内存监控模块
├── notifier.py       # macOS 通知模块
├── config.py         # 默认配置
├── run.sh            # 启动脚本
└── venv/             # Python 虚拟环境
```

## 配置文件

用户设置保存在 `user_config.json`，可手动编辑：

```json
{
  "threshold": 95,
  "spike_threshold": 20,
  "interval": 2000
}
```

| 参数 | 说明 |
|------|------|
| threshold | 系统内存报警阈值 (%) |
| spike_threshold | 进程突变阈值 (%) |
| interval | 监控刷新间隔 (毫秒) |
