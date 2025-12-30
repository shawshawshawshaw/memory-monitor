import SwiftUI
import Charts

struct ContentView: View {
    @StateObject private var monitor = MemoryMonitor()
    @StateObject private var config = Config.shared
    @State private var showingTree = true
    @State private var showSettings = false
    @State private var selectedPid: Int32? = nil
    
    var body: some View {
        VStack(spacing: 0) {
            systemStatusView
            Divider()
            processListView
            Divider()
            chartView
            if !monitor.alerts.isEmpty {
                alertsView
            }
        }
        .frame(width: 420, height: 520)
        .onAppear { monitor.startMonitoring() }
        .onDisappear { monitor.stopMonitoring() }
        .sheet(isPresented: $showSettings) {
            SettingsView(config: config)
        }
    }
    
    private var statusColor: Color {
        monitor.systemMemoryPercent >= config.memoryThreshold ? .red : .green
    }
    
    private var systemStatusView: some View {
        HStack {
            VStack(alignment: .leading) {
                Text("系统内存").font(.headline)
                Text("\(String(format: "%.1f", monitor.systemMemoryPercent))%")
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(statusColor)
            }
            Spacer()
            VStack {
                Circle().fill(statusColor).frame(width: 12, height: 12)
                Text(monitor.systemMemoryPercent >= config.memoryThreshold ? "警告" : "正常")
                    .font(.caption2)
            }
            Button(action: { showSettings = true }) {
                Image(systemName: "gearshape").font(.title3)
            }.buttonStyle(.plain)
        }
        .padding(10)
        .background(Color(NSColor.controlBackgroundColor))
    }
    
    private var processListView: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("进程内存占用").font(.subheadline).fontWeight(.medium)
                if selectedPid != nil {
                    Button("清除选择") { selectedPid = nil }.font(.caption2)
                }
                Spacer()
                Toggle("合并", isOn: $showingTree).toggleStyle(.switch).controlSize(.small)
            }
            .padding(.horizontal, 10).padding(.top, 6)
            
            List {
                if showingTree {
                    ForEach(monitor.processGroups.prefix(10)) { group in
                        GroupRow(group: group, selectedPid: $selectedPid)
                    }
                } else {
                    ForEach(monitor.processGroups.flatMap { $0.processes }.prefix(15)) { proc in
                        ProcessRow(process: proc, isSelected: selectedPid == proc.pid)
                            .onTapGesture { selectedPid = proc.pid }
                    }
                }
            }
            .listStyle(.inset)
        }
        .frame(height: 200)
    }
    
    private var chartView: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(selectedPid != nil ? "进程内存走势" : "系统内存走势")
                    .font(.subheadline).fontWeight(.medium)
                if let pid = selectedPid, let name = monitor.getProcessName(pid) {
                    Text("- \(name)").font(.caption).foregroundColor(.secondary)
                }
            }
            .padding(.horizontal, 10).padding(.top, 6)
            
            Chart {
                if let pid = selectedPid {
                    let history = monitor.getProcessHistory(pid)
                    ForEach(0..<history.count, id: \.self) { index in
                        LineMark(x: .value("时间", index), y: .value("内存", history[index].percent))
                            .foregroundStyle(.orange)
                    }
                } else {
                    ForEach(0..<monitor.systemHistory.count, id: \.self) { index in
                        LineMark(x: .value("时间", index), y: .value("内存", monitor.systemHistory[index]))
                            .foregroundStyle(.blue)
                    }
                    RuleMark(y: .value("阈值", config.memoryThreshold))
                        .foregroundStyle(.red)
                        .lineStyle(StrokeStyle(dash: [5, 5]))
                }
            }
            .chartYScale(domain: 0...100)
            .chartYAxis { AxisMarks(position: .leading) }
            .padding(.horizontal, 10).padding(.bottom, 8)
        }
        .frame(height: 150)
        .background(Color(NSColor.controlBackgroundColor))
    }
    
    private var alertsView: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill").foregroundColor(.red).font(.caption)
                Text("报警").font(.caption).fontWeight(.medium)
            }
            ForEach(monitor.alerts, id: \.self) { alert in
                Text("• \(alert)").foregroundColor(.red).font(.caption2)
            }
        }
        .padding(8)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.red.opacity(0.1))
    }
}

struct GroupRow: View {
    let group: ProcessGroup
    @Binding var selectedPid: Int32?
    @State private var isExpanded = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(alignment: .center) {
                Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                    .font(.system(size: 10)).foregroundColor(.secondary)
                    .frame(width: 12)
                Text(group.baseName).fontWeight(.medium)
                if group.processCount > 1 {
                    Text("(\(group.processCount))").foregroundColor(.secondary).font(.caption)
                }
                Spacer()
                VStack(alignment: .trailing) {
                    Text("\(String(format: "%.1f", group.totalMemoryPercent))%").fontWeight(.semibold)
                    Text("\(String(format: "%.0f", group.totalMemoryMB)) MB").font(.caption).foregroundColor(.secondary)
                }
            }
            .contentShape(Rectangle())
            .onTapGesture(count: 2) { isExpanded.toggle() }
            
            if isExpanded {
                ForEach(group.processes) { proc in
                    HStack {
                        VStack(alignment: .leading) {
                            Text(proc.name).font(.callout)
                            Text("PID: \(proc.pid)").font(.caption2).foregroundColor(.secondary)
                        }
                        Spacer()
                        VStack(alignment: .trailing) {
                            Text("\(String(format: "%.2f", proc.memoryPercent))%").font(.callout)
                            Text("\(String(format: "%.1f", proc.memoryMB)) MB").font(.caption2).foregroundColor(.secondary)
                        }
                    }
                    .padding(.vertical, 2)
                    .padding(.leading, 40)
                    .background(selectedPid == proc.pid ? Color.accentColor.opacity(0.2) : Color.clear)
                    .cornerRadius(4)
                    .contentShape(Rectangle())
                    .onTapGesture { selectedPid = proc.pid }
                }
            }
        }
    }
}

struct ProcessRow: View {
    let process: ProcessMemoryInfo
    var isSelected: Bool = false
    
    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(process.name)
                Text("PID: \(process.pid)").font(.caption).foregroundColor(.secondary)
            }
            Spacer()
            VStack(alignment: .trailing) {
                Text("\(String(format: "%.2f", process.memoryPercent))%")
                Text("\(String(format: "%.1f", process.memoryMB)) MB").font(.caption).foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 2)
        .background(isSelected ? Color.accentColor.opacity(0.2) : Color.clear)
        .cornerRadius(4)
    }
}
