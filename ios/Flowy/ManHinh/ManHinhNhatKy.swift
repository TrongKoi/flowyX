import SwiftUI
import UniformTypeIdentifiers

/// TAB NHAT KY (v4): loi nhan doi moi ngay, chuoi ngay tu diem danh,
/// bay cham deu tam, vuot de xoa, chon muc de xuat Word.
struct ManHinhNhatKy: View {
    @EnvironmentObject var so: SoNhatKy
    @EnvironmentObject var tienDo: SoTienDo
    @EnvironmentObject var ht: HoanTacModel
    @Binding var moCaiDat: Bool

    @State private var viet = false
    @State private var sua: SoNhatKy.Muc?
    @State private var dangChon = false
    @State private var daChon: Set<UUID> = []
    @State private var hoSo = DocxViet.HoSo.deDoc
    @State private var xuatTep: TepDocx?

    var body: some View {
        VStack(spacing: 0) {
            ThanhTieuDeTab(moCaiDat: $moCaiDat) { EmptyView() }
            DanhSachPhang {
                Text("Nhật ký").chu(24, dam: true, theo: .title2).foregroundColor(Mau.chu)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .accessibilityAddTraits(.isHeader).hangTron(tren: 0)

                loiNhan.hangTron()
                tomTat.hangTron()
                bayNgay.hangTron()

                if !dangChon {
                    Button("Viết nhật ký") { Rung.nhe(); viet = true }
                        .buttonStyle(NutChinhStyle()).chu(17, dam: true).hangTron(tren: 10)
                }

                HStack {
                    Text("Các mục").chu(13, dam: true).foregroundColor(Mau.chuPhu)
                    Spacer()
                    if !so.muc.isEmpty {
                        Button(dangChon ? "Huỷ" : "Chọn để xuất") {
                            Rung.nhe(); dangChon.toggle(); daChon = []
                        }
                        .chu(14, dam: true).foregroundColor(Mau.chuLienKet).frame(minHeight: 44)
                    }
                }
                .hangTron(tren: 12, duoi: 2)

                if dangChon { thanhXuat.hangTron() }

                if so.muc.isEmpty {
                    KhoiTrong(chu: "Chưa có ghi chép nào.\nViết một dòng thôi cũng được.").hangTron()
                } else {
                    ForEach(so.muc.reversed()) { m in the(m).hangTron() }
                }
            }
        }
        .background(Mau.nen.ignoresSafeArea())
        .fullScreenCover(isPresented: $viet) { VietNhatKy(muc: nil) }
        .fullScreenCover(item: $sua) { m in VietNhatKy(muc: m) }
        .fileExporter(isPresented: Binding(get: { xuatTep != nil }, set: { if !$0 { xuatTep = nil } }),
                      document: xuatTep, contentType: .docx, defaultFilename: tenTep()) { kq in
            if case .success = kq {
                Rung.xong(); ht.hien("Đã xuất \(daChon.count) mục ra Word.")
                dangChon = false; daChon = []
            } else {
                ht.hien("Không xuất được tệp.")
            }
        }
    }

    // MARK: - Cac khoi

    private var loiNhan: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("LỜI NHẮN HÔM NAY").chu(12, dam: true).foregroundColor(Mau.chuPhu)
            Text(LoiNhanNgay.cua(soNgay: SoLich.homNay())).chu(16).foregroundColor(Mau.chu)
        }
        .padding(16).frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 20, style: .continuous).fill(Mau.nhanNhat))
        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).stroke(Mau.nhanVien, lineWidth: 1))
    }

    /// So CAN GIUA trong o cao co dinh 88 - khop ban sua cua Android.
    private var tomTat: some View {
        VStack(spacing: 6) {
            HStack(spacing: 0) {
                oSo("\(tienDo.chuoi())", "Chuỗi ngày", Mau.cam)
                Rectangle().fill(Mau.vien).frame(width: 1, height: 56)
                oSo("\(tienDo.tongSoViec)", "Việc đã xong", Mau.chu)
            }
            Text("Mỗi ngày bạn mở Flowy đều được tính.").chu(12).foregroundColor(Mau.chuPhu)
        }
        .the()
    }

    private func oSo(_ so: String, _ nhan: String, _ mau: Color) -> some View {
        VStack(spacing: 6) {
            Text(so).chu(34, dam: true, theo: .largeTitle).foregroundColor(mau)
            Text(nhan).chu(12).foregroundColor(Mau.chuPhu)
        }
        .frame(maxWidth: .infinity, minHeight: 88)
        .accessibilityElement()
        .accessibilityLabel("\(nhan): \(so)")
    }

    /// Bay cham: MOI cham cung mot khuon 32x32 giua mot cot deu nhau.
    private var bayNgay: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("BẢY NGÀY GẦN ĐÂY").chu(12, dam: true).foregroundColor(Mau.chuPhu)
            HStack(spacing: 0) {
                ForEach(Array(tienDo.tuan().enumerated()), id: \.offset) { _, ngay in
                    VStack(spacing: 6) {
                        ZStack {
                            Circle().fill(ngay.1 ? Mau.cam : Mau.dhRanh)
                            if ngay.1 {
                                Image(systemName: "checkmark").font(.system(size: 13, weight: .bold))
                                    .foregroundColor(Mau.the)
                            }
                        }
                        .frame(width: 32, height: 32)
                        Text(ngay.0).chu(11).foregroundColor(Mau.chuPhu)
                    }
                    .frame(maxWidth: .infinity)
                    .accessibilityElement()
                    .accessibilityLabel("\(ngay.0): \(ngay.1 ? "có hoạt động" : "không có")")
                }
            }
        }
        .the()
    }

    private var thanhXuat: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Đã chọn \(daChon.count) mục").chu(13).foregroundColor(Mau.chuPhu)
            HStack(spacing: 8) {
                ChipChon(nhan: "Bản dễ đọc", chon: hoSo == .deDoc, gian: true) { hoSo = .deDoc }
                ChipChon(nhan: "Bản tiêu chuẩn", chon: hoSo == .tieuChuan, gian: true) { hoSo = .tieuChuan }
            }
            HStack(spacing: 8) {
                Button(daChon.count == so.muc.count ? "Bỏ chọn" : "Chọn tất cả") {
                    daChon = daChon.count == so.muc.count ? [] : Set(so.muc.map(\.id))
                }
                .buttonStyle(NutPhuStyle()).chu(15)
                Button("Xuất Word") { xuat() }
                    .buttonStyle(NutChinhStyle()).chu(15, dam: true)
                    .disabled(daChon.isEmpty)
            }
        }
        .the()
    }

    private func the(_ m: SoNhatKy.Muc) -> some View {
        HStack(alignment: .top, spacing: 8) {
            if dangChon {
                Image(systemName: daChon.contains(m.id) ? "checkmark.circle.fill" : "circle")
                    .font(.system(size: 22)).foregroundColor(daChon.contains(m.id) ? Mau.cam : Mau.chuPhu)
                    .frame(width: 44, height: 44)
            }
            VStack(alignment: .leading, spacing: 6) {
                Text(ngayGio(m.luc)).chu(12).foregroundColor(Mau.chuPhu)
                if let tn = m.theNao {
                    Text(tn).chu(12).foregroundColor(Mau.chu)
                        .padding(.horizontal, 10).padding(.vertical, 4)
                        .background(Capsule().fill(Mau.nen))
                }
                Text(m.noiDung).chu(15).foregroundColor(Mau.chu).lineLimit(6)
            }
            Spacer(minLength: 0)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 18, style: .continuous).fill(Mau.the))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Mau.vien, lineWidth: 1))
        .contentShape(Rectangle())
        .onTapGesture {
            if dangChon {
                Rung.nhe()
                if daChon.contains(m.id) { daChon.remove(m.id) } else { daChon.insert(m.id) }
            } else { sua = m }
        }
        .swipeActions(edge: .leading, allowsFullSwipe: true) {
            Button(role: .destructive) { xoa(m) } label: { Label("Xoá", systemImage: "trash") }
        }
        .accessibilityElement(children: .combine)
        .accessibilityActions { Button("Xoá") { xoa(m) } }
    }

    // MARK: -

    private func xoa(_ m: SoNhatKy.Muc) {
        Rung.xong()
        let i = so.muc.firstIndex(where: { $0.id == m.id }) ?? so.muc.count
        so.xoa(m.id)
        ht.hien("Đã xoá một mục nhật ký") { so.chen(m, tai: i) }
    }

    private func xuat() {
        let muc = so.muc.filter { daChon.contains($0.id) }.sorted { $0.luc < $1.luc }
        var k: [DocxViet.Khoi] = [.tieuDe("Nhật ký FlowyX"), .chuNho("\(muc.count) mục · xuất từ FlowyX")]
        for m in muc {
            k.append(.muc(ngayGio(m.luc)))
            if let tn = m.theNao { k.append(.noiBat("Cảm thấy", [tn])) }
            k += m.noiDung.components(separatedBy: "\n")
                .map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
                .map { DocxViet.Khoi.doan($0) }
        }
        xuatTep = TepDocx(data: DocxViet.tao(tieuDe: "Nhật ký FlowyX", khoi: k, hoSo: hoSo))
    }

    private func tenTep() -> String {
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"
        return "nhat-ky-flowyx-\(f.string(from: Date()))" + (hoSo == .deDoc ? "-de-doc" : "")
    }

    private func ngayGio(_ d: Date) -> String {
        let f = DateFormatter(); f.locale = Locale(identifier: "vi_VN"); f.dateFormat = "EEEE, dd/MM · HH:mm"
        let s = f.string(from: d)
        return s.prefix(1).uppercased() + s.dropFirst()
    }
}

/// Tep .docx de dua cho trinh chon noi luu cua he thong.
struct TepDocx: FileDocument {
    static var readableContentTypes: [UTType] { [.docx] }
    var data: Data
    init(data: Data) { self.data = data }
    init(configuration: ReadConfiguration) throws {
        data = configuration.file.regularFileContents ?? Data()
    }
    func fileWrapper(configuration: WriteConfiguration) throws -> FileWrapper { FileWrapper(regularFileWithContents: data) }
}

extension UTType {
    static let docx = UTType(importedAs: "org.openxmlformats.wordprocessingml.document")
}
