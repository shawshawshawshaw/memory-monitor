import Foundation
import Darwin

class MemoryMonitor: ObservableObject {
    @Published var systemMemoryPercent: Double = 0
    @Published var processGroups: [ProcessGroup] = []
    @Published var systemHistory: [Double] = []
    @Published var alerts: [String] = []
    
    private var processHistory: [Int32: [MemoryHistory]] = [:]
    private var timer: Timer?
    private let config = Config.shared
    
    func startMonitoring() {
        updateData()
        timer = Timer.scheduledTimer(withTimeInterval: config.monitorInterval, repeats: true) { [weak self] _ in
            self?.updateData()
        }
    }
    
    func stopMonitoring() {
        timer?.invalidate()
        timer = nil
    }
    
    func updateData() {
        systemMemoryPercent = getSystemMemory()
        systemHistory.append(systemMemoryPercent)
        if systemHistory.count > Config.historyLength {
            systemHistory.removeFirst()
        }
        
        let processes = getProcessList()
        processGroups = groupProcesses(processes)
        updateProcessHistory(processes)
        checkAlerts(processes)
    }
    
    private func getSystemMemory() -> Double {
        var stats = vm_statistics64()
        var count = mach_msg_type_number_t(MemoryLayout<vm_statistics64>.size / MemoryLayout<integer_t>.size)
        let result = withUnsafeMutablePointer(to: &stats) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                host_statistics64(mach_host_self(), HOST_VM_INFO64, $0, &count)
            }
        }
        
        guard result == KERN_SUCCESS else { return 0 }
        
        let pageSize = Double(vm_kernel_page_size)
        let active = Double(stats.active_count) * pageSize
        let inactive = Double(stats.inactive_count) * pageSize
        let wired = Double(stats.wire_count) * pageSize
        let compressed = Double(stats.compressor_page_count) * pageSize
        
        let used = active + wired + compressed
        let total = used + Double(stats.free_count) * pageSize + inactive
        
        return (used / total) * 100
    }
    
    private func getProcessList() -> [ProcessMemoryInfo] {
        var processes: [ProcessMemoryInfo] = []
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/bin/ps")
        task.arguments = ["-axo", "pid,ppid,rss,%mem,comm"]
        
        let pipe = Pipe()
        task.standardOutput = pipe
        task.standardError = FileHandle.nullDevice
        
        do {
            try task.run()
            task.waitUntilExit()
            
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            if let output = String(data: data, encoding: .utf8) {
                let lines = output.components(separatedBy: "\n").dropFirst()
                for line in lines {
                    if let proc = parseProcessLine(line) {
                        processes.append(proc)
                    }
                }
            }
        } catch {
            print("Error getting process list: \(error)")
        }
        
        return processes.sorted { $0.memoryPercent > $1.memoryPercent }
    }
    
    private func parseProcessLine(_ line: String) -> ProcessMemoryInfo? {
        let parts = line.split(separator: " ", omittingEmptySubsequences: true)
        guard parts.count >= 5,
              let pid = Int32(parts[0]),
              let ppid = Int32(parts[1]),
              let rss = Double(parts[2]),
              let memPercent = Double(parts[3]) else {
            return nil
        }
        
        let name = parts.dropFirst(4).joined(separator: " ")
        let memoryMB = rss / 1024.0
        
        guard memPercent > 0.1 else { return nil }
        
        return ProcessMemoryInfo(
            id: pid,
            name: String(name.split(separator: "/").last ?? Substring(name)),
            parentPid: ppid,
            memoryPercent: memPercent,
            memoryMB: memoryMB
        )
    }
    
    private func groupProcesses(_ processes: [ProcessMemoryInfo]) -> [ProcessGroup] {
        var groups: [String: [ProcessMemoryInfo]] = [:]
        
        for proc in processes {
            let baseName = getBaseName(proc.name)
            if groups[baseName] == nil {
                groups[baseName] = []
            }
            groups[baseName]?.append(proc)
        }
        
        return groups.map { key, value in
            ProcessGroup(id: key, baseName: key, processes: value)
        }.sorted { $0.totalMemoryPercent > $1.totalMemoryPercent }
    }
    
    private func getBaseName(_ name: String) -> String {
        var baseName = name
            .replacingOccurrences(of: " Helper", with: "")
            .replacingOccurrences(of: " (GPU)", with: "")
            .replacingOccurrences(of: " (Renderer)", with: "")
            .replacingOccurrences(of: " Web Content", with: "")
        
        if baseName.contains("Google Chrome") { baseName = "Google Chrome" }
        else if baseName.contains("Safari") { baseName = "Safari" }
        else if baseName.contains("Firefox") { baseName = "Firefox" }
        else if baseName.contains("Code") || baseName.contains("Electron") { baseName = "VS Code" }
        else if baseName.contains("Slack") { baseName = "Slack" }
        else if baseName.contains("Discord") { baseName = "Discord" }
        else if baseName.contains("Xcode") { baseName = "Xcode" }
        
        return baseName
    }
    
    private func updateProcessHistory(_ processes: [ProcessMemoryInfo]) {
        for proc in processes {
            if processHistory[proc.pid] == nil {
                processHistory[proc.pid] = []
            }
            processHistory[proc.pid]?.append(MemoryHistory(
                name: proc.name,
                percent: proc.memoryPercent,
                mb: proc.memoryMB,
                timestamp: Date()
            ))
            if let count = processHistory[proc.pid]?.count, count > Config.historyLength {
                processHistory[proc.pid]?.removeFirst()
            }
        }
    }
    
    func getProcessHistory(_ pid: Int32) -> [MemoryHistory] {
        return processHistory[pid] ?? []
    }
    
    func getProcessName(_ pid: Int32) -> String? {
        return processHistory[pid]?.last?.name
    }
    
    private func checkAlerts(_ processes: [ProcessMemoryInfo]) {
        alerts.removeAll()
        
        if systemMemoryPercent >= config.memoryThreshold {
            alerts.append("系统内存使用率达到 \(String(format: "%.1f", systemMemoryPercent))%!")
        }
        
        for proc in processes.prefix(10) {
            if let history = processHistory[proc.pid], history.count >= Config.spikeCheckWindow {
                let oldValues = history.suffix(Config.spikeCheckWindow).dropLast()
                let avgOld = oldValues.reduce(0) { $0 + $1.percent } / Double(oldValues.count)
                if avgOld > 0 {
                    let change = ((proc.memoryPercent - avgOld) / avgOld) * 100
                    if change > config.memorySpikeThreshold {
                        alerts.append("进程 [\(proc.name)] 内存突变! 当前: \(String(format: "%.1f", proc.memoryPercent))%")
                    }
                }
            }
        }
    }
}
