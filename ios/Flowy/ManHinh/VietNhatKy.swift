import SwiftUI

/// VIET NHAT KY - trang giay trong, toan man hinh.
/// Khong mat chu: Xong hay Quay lai deu LUU; nhap tu luu khi roi man hinh.
struct VietNhatKy: View {
    let muc: SoNhatKy.Muc?

    @EnvironmentObject var so: SoNhatKy
    @Environment(\.dismiss) private var dong
    @FocusState private var dangGo: Bool

    @State private var noiDung = ""
    @State private var theNao = ""

    private static let khoaNhap = "flowy_nhat_ky_nhap"
    private static let khoaTheNao = "flowy_nhat_ky_nhap_the_nao"

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    Text(ngay()).chu(13).foregroundColor(Mau.chuPhu)
                    TextField("Hôm nay thế nào?", text: $noiDung, axis: .vertical)
                        .chu(18).foregroundColor(Mau.chu)
                        .lineSpacing(6)
                        .focused($dangGo)
                        .frame(minHeight: 320, alignment: .topLeading)
                        .padding(.vertical, 12)
                    Rectangle().fill(Mau.vien).frame(height: 1)
                    TextField("Bạn thấy thế nào? (không bắt buộc)", text: $theNao)
                        .chu(15).foregroundColor(Mau.chu).frame(minHeight: 52)
                }
                .padding(16)
            }
            .background(Mau.nen.ignoresSafeArea())
            .navigationTitle(muc == nil ? "Viết nhật ký" : "Sửa nhật ký")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) { Button("Quay lại") { luuVaDong() } }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Xong") { luuVaDong() }.chu(16, dam: true)
                }
            }
        }
        .onAppear {
            if let m = muc { noiDung = m.noiDung; theNao = m.theNao ?? "" }
            else {
                noiDung = UserDefaults.standard.string(forKey: Self.khoaNhap) ?? ""
                theNao = UserDefaults.standard.string(forKey: Self.khoaTheNao) ?? ""
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { dangGo = true }
        }
        .onDisappear {
            if muc == nil {
                UserDefaults.standard.removeObject(forKey: Self.khoaNhap)
                UserDefaults.standard.removeObject(forKey: Self.khoaTheNao)
            }
        }
        .onChange(of: noiDung) { v in
            if muc == nil { UserDefaults.standard.set(v, forKey: Self.khoaNhap) }
        }
        .onChange(of: theNao) { v in
            if muc == nil { UserDefaults.standard.set(v, forKey: Self.khoaTheNao) }
        }
    }

    private func luuVaDong() {
        let tn = theNao.trimmingCharacters(in: .whitespacesAndNewlines)
        let daLuu: Bool
        if let m = muc { daLuu = so.sua(m.id, noiDung: noiDung, theNao: tn.isEmpty ? nil : tn) }
        else { daLuu = so.ghi(noiDung, theNao: tn.isEmpty ? nil : tn) }
        if daLuu { Rung.xong() }
        dong()
    }

    private func ngay() -> String {
        let f = DateFormatter(); f.locale = Locale(identifier: "vi_VN"); f.dateFormat = "EEEE, dd/MM/yyyy"
        let s = f.string(from: muc?.luc ?? Date())
        return s.prefix(1).uppercased() + s.dropFirst()
    }
}
