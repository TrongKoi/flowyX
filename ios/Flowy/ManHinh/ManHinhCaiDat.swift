import SwiftUI

/// CAI DAT - ban Swift cua `CaiDatActivity.kt`.
struct ManHinhCaiDat: View {
    @EnvironmentObject var m: FlowyModel
    @EnvironmentObject var settings: AppSettings
    @StateObject private var quyen = KiemQuyen()
    @Environment(\.scenePhase) private var phase

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("http://192.168.1.100:8765", text: $settings.serverUrl)
                        .keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled()
                    NavigationLink("Phiên có laptop (thử nghiệm)") {
                        ManHinhChinh().onAppear { m.batDauChay() }
                    }
                } header: { Text("Laptop (chỉ dùng khi test và demo)") } footer: {
                    Text("Vòng làm việc từng bước có laptop. Tab Tập trung không cần phần này.")
                }

                Section {
                    Text("Flowy theo chế độ Sáng/Tối của máy. Muốn đổi, vào Cài đặt của máy → Màn hình.")
                        .font(.footnote).foregroundColor(Mau.chuPhu)
                    Toggle(isOn: $settings.fontDeDoc) {
                        VStack(alignment: .leading) {
                            Text("Chữ dễ đọc (Lexend)")
                            Text("Nét chữ rộng, dễ phân biệt. Có đủ dấu tiếng Việt.")
                                .font(.footnote).foregroundColor(Mau.chuPhu)
                        }
                    }
                    .tint(Mau.nhan)
                } header: { Text("Giao diện") }

                Section("Giọng đọc và rung") {
                    Picker("Phản hồi", selection: $settings.phanHoi) {
                        ForEach(AppSettings.PhanHoi.allCases) { Text($0.nhan).tag($0) }
                    }
                    VStack(alignment: .leading) {
                        Text("Tốc độ đọc: \(String(format: "%.1f", settings.tocDoDoc).replacingOccurrences(of: ".", with: ","))")
                        Slider(value: $settings.tocDoDoc, in: 0.7...2.0, step: 0.1).tint(Mau.nhan)
                    }
                    Button("Nghe thử") { m.thuGiong() }
                }

                Section {
                    ForEach(quyen.ds) { q in
                        Button { quyen.xuLy(q) } label: {
                            HStack(alignment: .top, spacing: 12) {
                                Image(systemName: q.daCo ? "checkmark.circle.fill" : "exclamationmark.circle")
                                    .foregroundColor(q.daCo ? Mau.nhan : Mau.dhSapDen)
                                    .font(.title3)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(q.ten).foregroundColor(Mau.chu)
                                    Text(q.deLamGi).font(.footnote).foregroundColor(Mau.chuPhu)
                                }
                            }
                        }
                        .disabled(q.daCo)
                        .accessibilityLabel("\(q.ten), \(q.daCo ? "đã có" : "chưa có"). \(q.deLamGi)")
                    }
                } header: {
                    Text("Kiểm tra quyền")
                } footer: {
                    Text(quyen.conThieu == 0 ? "Đã đủ. Không cần làm gì thêm."
                         : "Chạm vào một dòng chưa có để bật. Thiếu thì app vẫn chạy, chỉ mất đúng phần đó.")
                }

                Section {
                    Text("Font Lexend © The Lexend Project Authors, giấy phép SIL Open Font License 1.1.")
                        .font(.footnote).foregroundColor(Mau.chuPhu)
                }
            }
            .scrollContentBackground(.hidden)
            .background(Mau.nen.ignoresSafeArea())
            .navigationTitle("Cài đặt")
        }
        .onAppear { quyen.lamMoi() }
        .onChange(of: phase) { p in if p == .active { quyen.lamMoi() } }
    }
}
