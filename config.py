# 配置参数
MEMORY_THRESHOLD = 95  # 系统内存报警阈值(%)
MEMORY_SPIKE_THRESHOLD = 20  # 进程内存突变阈值(%)，短时间内变化超过此值报警
MONITOR_INTERVAL = 2000  # 监控间隔(毫秒)
HISTORY_LENGTH = 60  # 保存历史数据点数量（用于绘制走势图）
SPIKE_CHECK_WINDOW = 5  # 检测内存突变的时间窗口（数据点数量）
