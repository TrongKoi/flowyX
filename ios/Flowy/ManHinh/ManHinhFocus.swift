import SwiftUI

/// TAB FOCUS (v4) - dong ho dem nguoc, chay HAN tren may.
/// Khong o nhap bat buoc: vao la bam Bat dau duoc ngay. Ten viec, buoc dau,
/// ly do nam o man "Go roi" (nut + tren thanh tieu de) va deu tuy chon.
struct ManHinhFocus: View {
    @EnvironmentObject var focus: FocusModel
    @EnvironmentObject var lich: SoLich
    @EnvironmentObject var tienDo: SoTienDo
    @EnvironmentObject var ht: HoanTacModel
    @Binding var moCaiDat: Bool

    @State private var moGoRoi = false
    @State private var nhip = Date()
    private let dongHo = Timer.publish(every: 0.5, on: .main, in: .common).autoconnect()
    private let soThoiLuong = SoThoiLuong()

    var body: some View {
        VStack(spacing: 0) {
            ThanhTieuDeTab(moCaiDat: $moCaiDat) {
                Button { Rung.nhe(); moGoRoi = true } label: {
                    Label("Gỡ rối", systemImage: "plus")
                        .chu(14, dam: true).foregroundColor(Mau.chu)
                        .padding(.horizontal, 12).frame(height: 36)
                        .background(Capsule().fill(Mau.nen))
                        .overlay(Capsule().stroke(Mau.vien, lineWidth: 1))
                }
                .accessibilityLabel("Gỡ rối để bắt đầu: vài câu hỏi tuỳ chọn trước khi hẹn giờ")
            }
            ScrollView {
                VStack(spacing: 12) {
                    Text(focus.laNghi ? "Đang nghỉ" : "Tập trung")
                        .chu(24, dam: true, theo: .title2).foregroundColor(Mau.chu)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .accessibilityAddTraits(.isHeader)
                    Text(focus.ten.map { "Đang làm: \($0)" } ?? "Chưa đặt tên việc — không sao cả.")
                        .chu(14).foregroundColor(focus.ten == nil ? Mau.chuPhu : Mau.chu)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    if focus.ketQuaPhut != nil { theKetQua }
                    if let b = focus.buocDau, focus.ketQuaPhut == nil {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("BƯỚC ĐẦU TIÊN").chu(12, dam: true).foregroundColor(Mau.cam)
                            Text(b).chu(16).foregroundColor(Mau.chu)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(16)
                        .background(RoundedRectangle(cornerRadius: 20, style: .continuous).fill(Mau.the))
                        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).stroke(Mau.cam, lineWidth: 2))
                    }

                    VongTapTrung(conLaiPhut: focus.dem.conLai(nhip) / 60,
                                 nhanChinh: DemNguoc.dinhDang(focus.dem.conLai(nhip)),
                                 nhanPhu: nhanPhu,
                                 tyLe: focus.dem.tyLe(nhip),
                                 choKeo: focus.dem.chuaBatDau) { p in
                        focus.dem = focus.dem.datThoiLuong(p)
                    }
                    .padding(.horizontal, 20)

                    Text(focus.dem.dangChay ? "Hết giờ lúc \(gioKetThuc)" : " ")
                        .chu(13).foregroundColor(Mau.chuPhu)

                    if focus.dem.chuaBatDau { chipNhanh }

                    Button(nutChinh) { Rung.nhe(); focus.tamDungHoacTiep() }
                        .buttonStyle(NutChinhStyle()).chu(18, dam: true)

                    if !focus.dem.chuaBatDau {
                        HStack(spacing: 8) {
                            Button("+5 phút") { Rung.nhe(); focus.themPhut(5) }
                                .buttonStyle(NutPhuStyle()).chu(15)
                            Button("Dừng lại") { dungLai() }
                                .buttonStyle(NutPhuStyle()).chu(15)
                        }
                    }
                }
                .padding(.horizontal, 16).padding(.bottom, 24)
            }
        }
        .background(Mau.nen.ignoresSafeArea())
        .onReceive(dongHo) { t in
            nhip = t
            if focus.kiemHetGio(lich: lich, tienDo: tienDo, thoiLuong: soThoiLuong) { Rung.xong() }
        }
        .fullScreenCover(isPresented: $moGoRoi) {
            ManHinhGoRoi { ten, buoc, lyDo, phut in
                focus.ten = ten; focus.buocDau = buoc; focus.lyDo = lyDo
                if focus.dem.chuaBatDau { focus.dem = focus.dem.datThoiLuong(phut) }
                focus.laNghi = false
                focus.batDau()
            }
        }
    }

    private var nhanPhu: String {
        if focus.dem.chuaBatDau { return "Xoay vòng để đặt giờ" }
        return focus.dem.dangDung ? "đang tạm dừng" : "còn lại"
    }

    private var nutChinh: String {
        focus.dem.dangChay ? "Tạm dừng" : (focus.dem.dangDung ? "Tiếp tục" : "Bắt đầu")
    }

    private var gioKetThuc: String {
        guard let k = focus.dem.ketThucLuc else { return "" }
        let f = DateFormatter(); f.dateFormat = "HH:mm"
        return f.string(from: k)
    }

    private var chipNhanh: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(DemNguoc.nhanh, id: \.self) { p in
                    ChipChon(nhan: p < 60 ? "\(p)′" : (p % 60 == 0 ? "\(p / 60)h" : "\(p / 60)h\(p % 60)"),
                             chon: Int(focus.dem.tongGiay / 60) == p) {
                        focus.dem = focus.dem.datThoiLuong(p)
                    }
                    .accessibilityLabel(Lich.moTaPhut(p))
                }
            }
            .padding(.vertical, 2)
        }
    }

    private var theKetQua: some View {
        let phut = Int((focus.ketQuaPhut ?? 0).rounded())
        return VStack(alignment: .leading, spacing: 8) {
            Text(focus.laNghi ? "Hết giờ nghỉ" : "Hết giờ rồi").chu(17, dam: true).foregroundColor(Mau.chu)
            Text(focus.laNghi ? "Sẵn sàng thì bắt đầu phiên mới. Chưa thì cứ nghỉ thêm."
                 : "Bạn đã tập trung \(phut) phút.")
                .chu(14).foregroundColor(Mau.chu)
            if let l = focus.lyDo, !focus.laNghi {
                Text("Để: \(l)").chu(13).foregroundColor(Mau.chuPhu)
            }
            HStack(spacing: 8) {
                if focus.laNghi {
                    Button("Bắt đầu phiên mới") {
                        focus.laNghi = false; focus.ketQuaPhut = nil
                        focus.dem = DemNguoc().datThoiLuong(25)
                    }.buttonStyle(NutPhuStyle()).chu(15)
                } else {
                    Button("Nghỉ 5 phút") {
                        focus.laNghi = true; focus.ketQuaPhut = nil
                        focus.dem = DemNguoc().datThoiLuong(5); focus.batDau()
                    }.buttonStyle(NutPhuStyle()).chu(15)
                    Button("Làm thêm 10 phút") {
                        focus.ketQuaPhut = nil
                        focus.dem = DemNguoc().datThoiLuong(10); focus.batDau()
                    }.buttonStyle(NutPhuStyle()).chu(15)
                }
            }
            Button("Xong, đóng lại") { focus.ketQuaPhut = nil }
                .chu(14).foregroundColor(Mau.chuLienKet).frame(minHeight: 44)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 20, style: .continuous).fill(Mau.nhanNhat))
        .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).stroke(Mau.nhanVien, lineWidth: 1))
    }

    private func dungLai() {
        Rung.nhe()
        let truoc = focus.dem
        focus.dem = focus.dem.datLai()
        focus.huyChuong()
        ht.hien("Đã dừng hẹn giờ") { focus.dem = truoc; if truoc.dangChay { focus.batDau() } }
    }
}
