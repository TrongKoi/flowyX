import SwiftUI
import UniformTypeIdentifiers

/// TAB BIEN BAN (v4) - noi voi loi Meety, xuat Word hai ban.
/// App KHONG mang giao dien Meety vao: chi doc tep `_minutes.json` do
/// `python main.py` tao ra tren laptop. Khong co tep thi ghi tay.
struct ManHinhBienBan: View {
    @EnvironmentObject var so: SoBienBan
    @EnvironmentObject var lich: SoLich
    @EnvironmentObject var ht: HoanTacModel
    @Binding var moCaiDat: Bool

    @State private var ghiTay = false
    @State private var moTep = false
    @State private var xuatTep: TepDocx?
    @State private var tenXuat = "bien-ban"
    @State private var hoiHoSo: SoBienBan.BienBan?

    var body: some View {
        VStack(spacing: 0) {
            ThanhTieuDeTab(moCaiDat: $moCaiDat) { EmptyView() }
            DanhSachPhang {
                Text("Biên bản").chu(24, dam: true, theo: .title2).foregroundColor(Mau.chu)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .accessibilityAddTraits(.isHeader).hangTron(tren: 0)

                Text("Có bản ghi âm hoặc transcript? Chạy Meety trên laptop rồi mở tệp _minutes.json ở đây. Không có thì ghi tay.")
                    .chu(13).foregroundColor(Mau.chu)
                    .padding(16).frame(maxWidth: .infinity, alignment: .leading)
                    .background(RoundedRectangle(cornerRadius: 20, style: .continuous).fill(Mau.nhanNhat))
                    .hangTron()

                HStack(spacing: 8) {
                    Button("Nhập từ Meety") { Rung.nhe(); moTep = true }
                        .buttonStyle(NutPhuStyle()).chu(15)
                    Button("Ghi tay") { Rung.nhe(); ghiTay = true }
                        .buttonStyle(NutPhuStyle()).chu(15)
                }
                .hangTron()

                Text("CÁC BIÊN BẢN").chu(12, dam: true).foregroundColor(Mau.chuPhu)
                    .frame(maxWidth: .infinity, alignment: .leading).hangTron(tren: 12, duoi: 2)

                if so.danhSach.isEmpty {
                    KhoiTrong(chu: "Chưa có biên bản nào.").hangTron()
                } else {
                    ForEach(so.danhSach.reversed()) { b in the(b).hangTron() }
                }
            }
        }
        .background(Mau.nen.ignoresSafeArea())
        .sheet(isPresented: $ghiTay) { GhiBienBan() }
        .fileImporter(isPresented: $moTep, allowedContentTypes: [.json, .plainText, .data]) { kq in
            guard case .success(let url) = kq else { return }
            let mo = url.startAccessingSecurityScopedResource()
            defer { if mo { url.stopAccessingSecurityScopedResource() } }
            guard let data = try? Data(contentsOf: url), let b = SoBienBan.tuMeety(data) else {
                ht.hien("Tệp này không phải biên bản Meety.")
                return
            }
            so.them(b); Rung.xong(); ht.hien("Đã nhập “\(b.ten)”")
        }
        .confirmationDialog("Xuất bản nào?", isPresented: Binding(get: { hoiHoSo != nil },
                                                                  set: { if !$0 { hoiHoSo = nil } }),
                            titleVisibility: .visible, presenting: hoiHoSo) { b in
            Button("Bản tiêu chuẩn — Times New Roman, để gửi và lưu hồ sơ") { xuat(b, .tieuChuan) }
            Button("Bản dễ đọc — chữ rộng, giãn dòng, nền kem, câu ngắn") { xuat(b, .deDoc) }
            Button("Huỷ", role: .cancel) {}
        }
        .fileExporter(isPresented: Binding(get: { xuatTep != nil }, set: { if !$0 { xuatTep = nil } }),
                      document: xuatTep, contentType: .docx, defaultFilename: tenXuat) { kq in
            if case .success = kq { Rung.xong(); ht.hien("Đã xuất tệp Word.") }
            else { ht.hien("Không xuất được tệp.") }
        }
    }

    private func the(_ b: SoBienBan.BienBan) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(b.ngayDoc + (b.nguon == "meety" ? "  ·  Meety" : "")).chu(12).foregroundColor(Mau.chuPhu)
            Text(b.ten).chu(16, dam: true).foregroundColor(Mau.chu)
            if let dong = b.tomTat.first ?? b.daChot.components(separatedBy: "\n").first(where: { !$0.isEmpty }) {
                Text(dong).chu(13).foregroundColor(Mau.chu).lineLimit(3)
            }
            if !b.viec.isEmpty {
                Text("VIỆC CẦN LÀM · \(b.viec.count)").chu(12, dam: true).foregroundColor(Mau.cam).padding(.top, 6)
                ForEach(b.viec.prefix(4), id: \.self) { v in
                    HStack(spacing: 8) {
                        Text(v).chu(13.5).foregroundColor(Mau.chu)
                        Spacer(minLength: 0)
                        Button("Thêm vào lịch") { vaoLich(v) }
                            .chu(12).foregroundColor(Mau.chu)
                            .padding(.horizontal, 11).frame(height: 36)
                            .background(Capsule().fill(Mau.nen))
                    }
                    .padding(.top, 4)
                }
            }
            Button("Xuất Word") { Rung.nhe(); hoiHoSo = b }
                .buttonStyle(NutPhuStyle()).chu(15).padding(.top, 10)
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 18, style: .continuous).fill(Mau.the))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Mau.vien, lineWidth: 1))
        .swipeActions(edge: .leading, allowsFullSwipe: true) {
            Button(role: .destructive) { xoa(b) } label: { Label("Xoá", systemImage: "trash") }
        }
        .accessibilityActions { Button("Xoá") { xoa(b) } }
    }

    private func xuat(_ b: SoBienBan.BienBan, _ hoSo: DocxViet.HoSo) {
        let ten = b.ten.lowercased().replacingOccurrences(of: "[^\\p{L}\\p{N}]+", with: "-",
                                                          options: .regularExpression)
        tenXuat = "bien-ban-" + ten.trimmingCharacters(in: CharacterSet(charactersIn: "-")).prefix(40)
            + (hoSo == .deDoc ? "-de-doc" : "")
        xuatTep = TepDocx(data: DocxViet.tao(tieuDe: b.ten, khoi: SoBienBan.khoiDocx(b), hoSo: hoSo))
    }

    private func vaoLich(_ ten: String) {
        Rung.xong()
        let bay = SoLich.bayGio() % 1440
        lich.luu(KeHoach(ten: String(ten.prefix(80)), ngay: SoLich.homNay(),
                         batDau: min((bay / 60 + 1) * 60, 23 * 60), thoiLuong: 30, uuTien: .cao))
        ht.hien("Đã thêm vào lịch hôm nay.")
    }

    private func xoa(_ b: SoBienBan.BienBan) {
        Rung.xong()
        guard let (ban, i) = so.xoa(b.id) else { return }
        ht.hien("Đã xoá “\(ban.ten)”") { so.chen(ban, tai: i) }
    }
}

/// GHI BIEN BAN TAY - duong du phong khi khong co tep ghi am.
struct GhiBienBan: View {
    @EnvironmentObject var so: SoBienBan
    @Environment(\.dismiss) private var dong
    @State private var ten = ""
    @State private var nguoi = ""
    @State private var chot = ""
    @State private var viec = ""
    @State private var hoi = ""
    @State private var loi = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    o("Tên cuộc họp", "", $ten, nhieuDong: false)
                    if loi { Text("Cần ít nhất 3 ký tự.").chu(13).foregroundColor(Mau.chu) }
                    o("Người dự (tuỳ chọn)", "Cách nhau bằng dấu phẩy", $nguoi, nhieuDong: false)
                    o("Đã chốt (tuỳ chọn)", "Mỗi dòng một ý", $chot, nhieuDong: true)
                    o("Việc cần làm (tuỳ chọn)", "Ví dụ: Minh: gửi báo giá trước thứ 6", $viec, nhieuDong: true)
                    o("Câu hỏi còn mở (tuỳ chọn)", "Mỗi dòng một câu", $hoi, nhieuDong: true)
                    Button("Lưu biên bản") { luu() }
                        .buttonStyle(NutChinhStyle()).chu(18, dam: true).padding(.top, 20)
                }
                .padding(16)
            }
            .background(Mau.nen.ignoresSafeArea())
            .navigationTitle("Ghi tay")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .navigationBarLeading) { Button("Quay lại") { dong() } } }
        }
    }

    private func o(_ nhan: String, _ goiY: String, _ chu: Binding<String>, nhieuDong: Bool) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(nhan).chu(15, dam: true).foregroundColor(Mau.chu).padding(.top, 18)
            TextField(goiY, text: chu, axis: nhieuDong ? .vertical : .horizontal)
                .chu(16).foregroundColor(Mau.chu)
                .lineLimit(nhieuDong ? 3... : 1...1)
                .padding(.horizontal, 14).padding(.vertical, 12)
                .frame(minHeight: 52, alignment: .topLeading)
                .background(RoundedRectangle(cornerRadius: 14).fill(Mau.the))
                .overlay(RoundedRectangle(cornerRadius: 14).stroke(Mau.vien, lineWidth: 1))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func luu() {
        let ok = so.them(SoBienBan.BienBan(
            luc: Date(), ten: ten, daChot: chot,
            viec: viec.components(separatedBy: "\n"),
            nguoiDu: nguoi.components(separatedBy: CharacterSet(charactersIn: ",\n")),
            cauHoi: hoi.components(separatedBy: "\n")))
        if ok { Rung.xong(); dong() } else { loi = true }
    }
}
