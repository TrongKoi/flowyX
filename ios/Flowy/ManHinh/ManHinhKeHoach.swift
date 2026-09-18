import SwiftUI

/// TAB KE HOACH (v4) - man hinh mo dau. Gop "Loi nhac" vao day.
/// Thu tu: tom tat + uu tien -> Tiep theo -> danh sach theo uu tien -> nut.
/// Mat doc tu tren xuong gap "hom nay nang hay nhe" TRUOC moi nut bam.
struct ManHinhKeHoach: View {
    @EnvironmentObject var lich: SoLich
    @EnvironmentObject var focus: FocusModel
    @EnvironmentObject var ht: HoanTacModel
    @EnvironmentObject var tienDo: SoTienDo
    @Binding var tab: TabV4
    @Binding var moCaiDat: Bool

    @State private var dangSua: KeHoach?
    @State private var taoMoi = false

    private var homNay: Int { SoLich.homNay() }
    private var ds: [KeHoach] { Lich.trongNgay(lich.danhSach, homNay) }
    private var phutBayGio: Int { SoLich.bayGio() - homNay * 1440 }

    var body: some View {
        VStack(spacing: 0) {
            ThanhTieuDeTab(moCaiDat: $moCaiDat) { EmptyView() }
            DanhSachPhang {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Kế hoạch hôm nay").chu(24, dam: true, theo: .title2)
                        .foregroundColor(Mau.chu).accessibilityAddTraits(.isHeader)
                    Text(ngayDoc()).chu(13).foregroundColor(Mau.chuPhu)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .hangTron(tren: 0)

                tomTat.hangTron()
                tiepTheo.hangTron()
                danhSach

                VStack(spacing: 10) {
                    Button("+ Thêm kế hoạch") { Rung.nhe(); taoMoi = true }
                        .buttonStyle(NutChinhStyle()).chu(17, dam: true)
                    Button("Xem lịch tuần") { Rung.nhe(); tab = .lich }
                        .buttonStyle(NutPhuStyle()).chu(16)
                    Text("Mẹo: vuốt trái để đánh dấu xong, vuốt phải để xoá.")
                        .chu(12).foregroundColor(Mau.chuPhu)
                }
                .padding(.top, 8)
                .hangTron(duoi: 24)
            }
        }
        .background(Mau.nen.ignoresSafeArea())
        .sheet(isPresented: $taoMoi) { SuaKeHoach(keHoach: nil, ngayMacDinh: homNay) }
        .sheet(item: $dangSua) { kh in SuaKeHoach(keHoach: kh, ngayMacDinh: kh.ngay) }
    }

    // MARK: - Tom tat + uu tien

    private var tomTat: some View {
        let xong = ds.filter { lich.daXong.contains(Lich.khoaXong($0.id, homNay)) }.count
        let con = ds.filter { !lich.daXong.contains(Lich.khoaXong($0.id, homNay)) && $0.ketThuc > phutBayGio }.count
        let tong = ds.reduce(0) { $0 + $1.thoiLuong }
        return VStack(spacing: 14) {
            HStack(spacing: 0) {
                oSo("\(ds.count)", "việc")
                oSo(tong == 0 ? "0" : gonThoiLuong(tong), "tổng thời gian")
                oSo("\(con)", "còn lại")
            }
            HStack(spacing: 8) {
                ForEach(UuTien.allCases) { u in
                    let n = ds.filter { $0.uuTien == u }.count
                    HStack(spacing: 6) {
                        Circle().fill(Mau.uuTien(u)).frame(width: 10, height: 10)
                        Text("\(u.nhan) · \(n)").chu(13).foregroundColor(Mau.chu)
                    }
                    .frame(maxWidth: .infinity, minHeight: 40)
                    .background(Capsule().fill(Mau.nen))
                    .accessibilityElement()
                    .accessibilityLabel("Ưu tiên \(u.nhan): \(n) việc")
                }
            }
        }
        .the()
        .accessibilityElement(children: .contain)
        .accessibilityHint("Hôm nay \(ds.count) việc, đã xong \(xong)")
    }

    private func oSo(_ so: String, _ nhan: String) -> some View {
        VStack(spacing: 4) {
            Text(so).chu(22, dam: true, theo: .title3).foregroundColor(Mau.chu)
            Text(nhan).chu(12).foregroundColor(Mau.chuPhu)
        }
        .frame(maxWidth: .infinity)
        .accessibilityElement()
        .accessibilityLabel("\(nhan): \(so)")
    }

    // MARK: - Tiep theo

    @ViewBuilder
    private var tiepTheo: some View {
        if let kh = Lich.tiepTheo(lich.danhSach, bayGio: SoLich.bayGio(), daXong: lich.daXong) {
            VStack(alignment: .leading, spacing: 4) {
                Text(kh.batDau <= phutBayGio ? "ĐANG DIỄN RA" : "TIẾP THEO · \(Lich.gioPhut(kh.batDau))")
                    .chu(12, dam: true).foregroundColor(Mau.cam)
                Text("\(kh.emoji)  \(kh.ten)").chu(17, dam: true).foregroundColor(Mau.chu)
                Text("\(Lich.gioPhut(kh.batDau)) – \(Lich.gioPhut(kh.ketThuc)) · \(Lich.moTaPhut(kh.thoiLuong))")
                    .chu(13).foregroundColor(Mau.chuPhu)
                Button("Bắt đầu việc này") {
                    Rung.nhe(); focus.batDauTuKeHoach(kh); tab = .focus
                }
                .buttonStyle(NutChinhStyle()).chu(16, dam: true).padding(.top, 8)
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 20, style: .continuous).fill(Mau.the))
            .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).stroke(Mau.cam, lineWidth: 2))
        }
    }

    // MARK: - Danh sach theo uu tien

    @ViewBuilder
    private var danhSach: some View {
        if ds.isEmpty {
            Text("Việc hôm nay").chu(13, dam: true).foregroundColor(Mau.chuPhu)
                .frame(maxWidth: .infinity, alignment: .leading).hangTron(duoi: 2)
            KhoiTrong(chu: "Hôm nay chưa có kế hoạch nào.\nThêm một việc nhỏ thôi cũng được.").hangTron()
        } else {
            ForEach(UuTien.allCases) { u in
                let nhom = Lich.theoUuTien(ds).filter { $0.uuTien == u }
                if !nhom.isEmpty {
                    Text("ƯU TIÊN \(u.nhan.uppercased())").chu(12, dam: true)
                        .foregroundColor(Mau.chuPhu)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .hangTron(tren: 12, duoi: 2)
                    ForEach(nhom) { kh in the(kh).hangTron() }
                }
            }
        }
    }

    private func the(_ kh: KeHoach) -> some View {
        let xong = lich.daXong.contains(Lich.khoaXong(kh.id, homNay))
        return HStack(spacing: 8) {
            OTron(xong: xong) { doiXong(kh) }
            VStack(alignment: .leading, spacing: 4) {
                Text("\(kh.emoji)  \(kh.ten)").chu(15, dam: true)
                    .foregroundColor(xong ? Mau.chuPhu : Mau.chu)
                    .strikethrough(xong)
                Text([("\(Lich.gioPhut(kh.batDau))–\(Lich.gioPhut(kh.ketThuc))"),
                      Lich.moTaPhut(kh.thoiLuong),
                      kh.lapLai == .khong ? nil : Lich.moTaLapLai(kh)]
                    .compactMap { $0 }.joined(separator: " · "))
                    .chu(12).foregroundColor(Mau.chuPhu)
            }
            Spacer(minLength: 0)
            RoundedRectangle(cornerRadius: 3).fill(Mau.uuTien(kh.uuTien)).frame(width: 6, height: 30)
        }
        .padding(.vertical, 10).padding(.horizontal, 12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 18, style: .continuous).fill(Mau.the))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Mau.vien, lineWidth: 1))
        .contentShape(Rectangle())
        .onTapGesture { dangSua = kh }
        // Vuot PHAI = xoa (canh trai), vuot TRAI = xong. Giong Android.
        .swipeActions(edge: .leading, allowsFullSwipe: true) {
            Button(role: .destructive) { xoa(kh) } label: { Label("Xoá", systemImage: "trash") }
        }
        .swipeActions(edge: .trailing, allowsFullSwipe: true) {
            Button { doiXong(kh) } label: { Label(xong ? "Bỏ xong" : "Xong", systemImage: "checkmark") }
                .tint(Mau.nhan)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(kh.ten), \(Lich.gioPhut(kh.batDau)) đến \(Lich.gioPhut(kh.ketThuc)), ưu tiên \(kh.uuTien.nhan)\(xong ? ", đã xong" : "")")
        .accessibilityActions {
            Button(xong ? "Bỏ đánh dấu xong" : "Đánh dấu xong") { doiXong(kh) }
            Button("Xoá") { xoa(kh) }
            Button("Sửa") { dangSua = kh }
        }
    }

    private func doiXong(_ kh: KeHoach) {
        lich.doiXong(kh.id, ngay: homNay)
        if lich.daXong.contains(Lich.khoaXong(kh.id, homNay)) { tienDo.ghi() }
    }

    private func xoa(_ kh: KeHoach) {
        Rung.xong()
        let dauXong = lich.daXong.filter { $0.hasPrefix(kh.id + "|") }
        lich.xoa(kh.id)
        ht.hien("Đã xoá “\(kh.ten)”") { lich.khoiPhuc(kh, daXong: dauXong) }
    }

    private func ngayDoc() -> String {
        let f = DateFormatter(); f.locale = Locale(identifier: "vi_VN"); f.dateFormat = "EEEE, d 'tháng' M"
        return f.string(from: Date()).prefix(1).uppercased() + f.string(from: Date()).dropFirst()
    }

    private func gonThoiLuong(_ phut: Int) -> String {
        if phut < 60 { return "\(phut)′" }
        return phut % 60 == 0 ? "\(phut / 60)g" : "\(phut / 60)g\(phut % 60)"
    }
}
