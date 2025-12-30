import SwiftUI
import Charts
import AppKit

@main
struct MemoryMonitorApp: App {
    @StateObject private var monitor = MemoryMonitor()
    
    init() {
        let m = MemoryMonitor()
        _monitor = StateObject(wrappedValue: m)
        m.startMonitoring()
    }
    
    var body: some Scene {
        WindowGroup {
            MainContentView(monitor: monitor)
        }
        .windowResizability(.contentSize)
        
        MenuBarExtra("\(String(format: "%.1f", monitor.systemMemoryPercent))%") {
            Text("内存: \(String(format: "%.1f", monitor.systemMemoryPercent))%")
            Divider()
            Button("退出") { NSApplication.shared.terminate(nil) }
        }
    }
}

struct MainContentView: View {
    @ObservedObject var monitor: MemoryMonitor
    @StateObject private var config = Config.shared
    @State private var showingTree = true
    @State private var showSettings = false
    @State private var selectedPid: Int32? = nil
    
    var body: some View {
        VStack(spacing: 0) {
            systemStatusView
            processListView
            Divider()
            chartView
            if !monitor.alerts.isEmpty { alertsView }
        }
        .frame(width: 400, height: 460)
        .onDisappear { monitor.stopMonitoring() }
        .sheet(isPresented: $showSettings) { SettingsView(config: config) }
    }
    
    private var statusColor: Color {
        monitor.systemMemoryPercent >= config.memoryThreshold ? .red : .green
    }
    
    private var systemStatusView: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("系统内存").font(.subheadline)
                Text("\(String(format: "%.1f", monitor.systemMemoryPercent))%")
                    .font(.system(size: 22, weight: .bold))
                    .foregroundColor(statusColor)
            }
            Spacer()
            Circle().fill(statusColor).frame(width: 10, height: 10)
            Text(monitor.systemMemoryPercent >= config.memoryThreshold ? "警告" : "正常")
                .font(.caption2)
            Button(action: { openActivityMonitor() }) {
                Image(systemName: "list.bullet.rectangle").font(.body)
            }.buttonStyle(.plain).help("打开活动监视器")
            Button(action: { showSettings = true }) {
                Image(systemName: "gearshape").font(.body)
            }.buttonStyle(.plain).help("设置")
        }
        .padding(.horizontal, 10).padding(.vertical, 6)
    }
    
    private func openActivityMonitor() {
        if let url = NSWorkspace.shared.urlForApplication(withBundleIdentifier: "com.apple.ActivityMonitor") {
            NSWorkspace.shared.openApplication(at: url, configuration: NSWorkspace.OpenConfiguration())
        }
    }
    
    private var processListView: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack {
                Text("进程内存占用").font(.caption).fontWeight(.medium)
                if selectedPid != nil {
                    Button("清除") { selectedPid = nil }.font(.caption2)
                }
                Spacer()
                Toggle("合并", isOn: $showingTree).toggleStyle(.switch).controlSize(.mini)
            }
            .padding(.horizontal, 10)
            
            List {
                if showingTree {
                    ForEach(monitor.processGroups.prefix(10)) { group in
                        GroupRow(group: group, selectedPid: $selectedPid)
                    }
                } else {
                    ForEach(monitor.processGroups.flatMap { $0.processes }.prefix(15)) { proc in
                        ProcessRow(process: proc, isSelected: selectedPid == proc.pid)
                            .contentShape(Rectangle())
                            .onTapGesture { selectedPid = proc.pid }
                    }
                }
            }
            .listStyle(.plain)
        }
        .frame(height: 200)
    }
    
    private var chartView: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack {
                Text(selectedPid != nil ? "进程走势" : "系统走势").font(.caption).fontWeight(.medium)
                if let pid = selectedPid, let name = monitor.getProcessName(pid) {
                    Text("- \(name)").font(.caption2).foregroundColor(.secondary)
                }
            }
            .padding(.horizontal, 10).padding(.top, 4)
            
            Chart {
                if let pid = selectedPid {
                    let history = monitor.getProcessHistory(pid)
                    ForEach(0..<history.count, id: \.self) { i in
                        LineMark(x: .value("T", i), y: .value("M", history[i].percent))
                            .foregroundStyle(.orange)
                    }
                } else {
                    ForEach(0..<monitor.systemHistory.count, id: \.self) { i in
                        LineMark(x: .value("T", i), y: .value("M", monitor.systemHistory[i]))
                            .foregroundStyle(.blue)
                    }
                    RuleMark(y: .value("阈值", config.memoryThreshold))
                        .foregroundStyle(.red).lineStyle(StrokeStyle(dash: [5, 5]))
                }
            }
            .chartYScale(domain: 0...100)
            .chartYAxis { AxisMarks(position: .leading) }
            .padding(.horizontal, 8).padding(.bottom, 6)
        }
        .frame(height: 140)
    }
    
    private var alertsView: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill").foregroundColor(.red).font(.caption2)
                Text("报警").font(.caption2).fontWeight(.medium)
            }
            ForEach(monitor.alerts, id: \.self) { alert in
                Text("• \(alert)").foregroundColor(.red).font(.caption2)
            }
        }
        .padding(6)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.red.opacity(0.1))
    }
}
