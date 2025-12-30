import SwiftUI

struct SettingsView: View {
    @ObservedObject var config: Config
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        VStack(spacing: 16) {
            Text("设置").font(.headline)
            
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text("内存报警阈值:")
                    Slider(value: $config.memoryThreshold, in: 50...100, step: 1)
                    Text("\(Int(config.memoryThreshold))%").frame(width: 40)
                }
                
                HStack {
                    Text("突变报警阈值:")
                    Slider(value: $config.memorySpikeThreshold, in: 5...50, step: 1)
                    Text("\(Int(config.memorySpikeThreshold))%").frame(width: 40)
                }
                
                HStack {
                    Text("监控间隔(秒):")
                    Slider(value: $config.monitorInterval, in: 1...10, step: 0.5)
                    Text("\(String(format: "%.1f", config.monitorInterval))").frame(width: 40)
                }
            }
            .padding()
            
            Button("关闭") { dismiss() }
                .keyboardShortcut(.defaultAction)
        }
        .padding()
        .frame(width: 320)
    }
}
