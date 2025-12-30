import Foundation

struct ProcessMemoryInfo: Identifiable, Hashable {
    let id: Int32
    var pid: Int32 { id }
    let name: String
    let parentPid: Int32
    var memoryPercent: Double
    var memoryMB: Double
    var children: [ProcessMemoryInfo] = []
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
    
    static func == (lhs: ProcessMemoryInfo, rhs: ProcessMemoryInfo) -> Bool {
        lhs.id == rhs.id
    }
}

struct ProcessGroup: Identifiable, Hashable {
    let id: String
    let baseName: String
    var processes: [ProcessMemoryInfo]
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
    
    static func == (lhs: ProcessGroup, rhs: ProcessGroup) -> Bool {
        lhs.id == rhs.id
    }
    
    var totalMemoryPercent: Double {
        processes.reduce(0) { $0 + $1.memoryPercent }
    }
    
    var totalMemoryMB: Double {
        processes.reduce(0) { $0 + $1.memoryMB }
    }
    
    var processCount: Int {
        processes.count
    }
}

struct MemoryHistory {
    var name: String
    var percent: Double
    var mb: Double
    var timestamp: Date
}
