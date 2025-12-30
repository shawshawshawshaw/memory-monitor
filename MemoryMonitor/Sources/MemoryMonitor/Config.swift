import Foundation

class Config: ObservableObject {
    static let shared = Config()
    
    @Published var memoryThreshold: Double {
        didSet { UserDefaults.standard.set(memoryThreshold, forKey: "memoryThreshold") }
    }
    @Published var memorySpikeThreshold: Double {
        didSet { UserDefaults.standard.set(memorySpikeThreshold, forKey: "memorySpikeThreshold") }
    }
    @Published var monitorInterval: TimeInterval {
        didSet { UserDefaults.standard.set(monitorInterval, forKey: "monitorInterval") }
    }
    
    static var historyLength: Int = 60
    static var spikeCheckWindow: Int = 5
    
    private init() {
        let defaults = UserDefaults.standard
        memoryThreshold = defaults.object(forKey: "memoryThreshold") as? Double ?? 95.0
        memorySpikeThreshold = defaults.object(forKey: "memorySpikeThreshold") as? Double ?? 20.0
        monitorInterval = defaults.object(forKey: "monitorInterval") as? TimeInterval ?? 2.0
    }
}
