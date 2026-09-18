import SwiftUI

/// MAN HINH LICH - ban Swift cua `LichActivity.kt`.
///
/// iPhone: dai tuan ngang o tren, dong thoi gian ben duoi.
/// iPad: tuan dung doc ben trai, ngay ben phai.
///
/// Khoi DAI HON thi viec LAU HON. Vach "Bay gio" neo ca ngay vao dong ho
/// that; khoang trong >= 15 phut duoc ghi ra - thoi gian nhin thay duoc.
struct ManHinhLich: View {
    @EnvironmentObject var lich: SoLich
    @EnvironmentObject var settings: AppSettings
    @EnvironmentObject var focus: FocusModel
    @EnvironmentObject var tienDo: SoTienDo
    @EnvironmentObject var ht: HoanTacModel
    @Binding var tab: TabV4
    @Binding var moCaiDat: Bool
    @Environment(\.horizontalSizeClass) private var sizeClass

    @State private var ngayChon = SoLich.homNay()
    @State private var dangSua: KeHoach?
    @State private var taoMoi = false
    @State private var thaoTac: KeHoach?

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
            ThanhTieuDeTab(moCaiDat: $moCaiDat) { EmptyView() }
            Group {
                if sizeClass == .regular {
                    HStack(alignment: .top, spacing: 24) {
                        ScrollView { daiTuan(doc: true) }.frame(width: 240)
                        khoiNgay
                    }
                } else {
                    VStack(spacing: 10) {
                        daiTuan(doc: false)
                        khoiNgay
                    }
                }
            }
            .padding(.horizontal, sizeClass == .regular ? 28 : 16)
            .background(Mau.nen.ignoresSafeArea())
            }
            .background(Mau.nen.ignoresSafeArea())
            .navigationTitle(tieuDeThang)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItemGroup(placement: .navigationBarLeading) {
                    Button { ngayChon -= 7 } label: { Image(systemName: "chevron.left") }
                        .accessibilityLabel("Tuần trước")
                    Button { ngayChon += 7 } label: { Image(systemName: "chevron.right") }
                        .accessibilityLabel("Tuần sau")
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Hôm nay") { ngayChon = SoLich.homNay() }
                }
            }
        }
        .sheet(isPresented: $taoMoi) {
            SuaKeHoach(keHoach: nil, ngayMacDinh: ngayChon)
                .environmentObject(lich).environmentObject(settings)
        }
        .sheet(item: $dangSua) { kh in
            SuaKeHoach(keHoach: kh, ngayMacDinh: kh.ngay)
                .environmentObject(lich).environmentObject(settings)
        }
        .confirmationDialog(thaoTac.map { "\($0.emoji)  \($0.ten)" } ?? "",
                            isPresented: Binding(get: { thaoTac != nil }, set: { if !$0 { thaoTac = nil } }),
                            titleVisibility: .visible, presenting: thaoTac) { kh in
            // v4: "Đánh dấu xong" va "Xoá" da co ngay tren the (ô tròn, vuốt)
            // - khong lap lai o day.
            let xong = lich.daXong.contains(Lich.khoaXong(kh.id, ngayChon))
            if ngayChon == SoLich.homNay() && !xong {
                Button("Bắt đầu việc này") { focus.batDauTuKeHoach(kh); tab = .focus }
            }
            Button("Sửa") { dangSua = kh }
            Button("Huỷ", role: .cancel) {}
        }
    }

    private var tieuDeThang: String {
        let t = Lich.ngayThang(ngayChon)
        return "Tháng \(t.thang), \(t.nam)"
    }

    // MARK: Dai tuan

    @ViewBuilder
    private func daiTuan(doc: Bool) -> some View {
        let homNay = SoLich.homNay()
        let dau = Lich.dauTuan(ngayChon)
        let layout = doc ? AnyLayout(VStackLayout(spacing: 6)) : AnyLayout(HStackLayout(spacing: 4))
        layout {
            ForEach(0..<7, id: \.self) { i in
                let ngay = dau + i
                let chon = ngay == ngayChon
                let soViec = Lich.trongNgay(lich.danhSach, ngay).count
                Button { ngayChon = ngay } label: {
                    let noiDung = Group {
                        Text(Lich.tenThuNgan[i]).chu(13).foregroundColor(Mau.chuPhu)
                        Text("\(Lich.ngayThang(ngay).ngay)").chu(19, dam: true)
                            .foregroundColor(ngay == homNay ? Mau.nhan : Mau.chu)
                        Text(soViec == 0 ? " " : (doc ? "\(soViec) việc" : "•"))
                            .chu(doc ? 13 : 16).foregroundColor(Mau.nhan)
                    }
                    Group {
                        if doc { HStack(spacing: 10) { noiDung; Spacer() } }
                        else { VStack(spacing: 2) { noiDung } }
                    }
                    .padding(.horizontal, doc ? 14 : 2).padding(.vertical, 8)
                    .frame(maxWidth: .infinity, minHeight: doc ? 52 : 72)
                    .background(RoundedRectangle(cornerRadius: 16).fill(chon ? Mau.nhanNhat : Mau.the))
                    .overlay(RoundedRectangle(cornerRadius: 16)
                        .stroke(chon ? Mau.nhan : Mau.vien, lineWidth: chon ? 2 : 1))
                }
                .buttonStyle(.plain)
                .accessibilityLabel(Lich.tenNgay(ngay, homNay: homNay) + (soViec > 0 ? ", \(soViec) kế hoạch" : ", trống"))
                .accessibilityAddTraits(chon ? .isSelected : [])
            }
        }
    }

    // MARK: Ngay

    private var khoiNgay: some View {
        let ds = Lich.trongNgay(lich.danhSach, ngayChon)
        return VStack(alignment: .leading, spacing: 4) {
            Text(Lich.tenNgay(ngayChon, homNay: SoLich.homNay()))
                .chu(22, dam: true, theo: .title3).foregroundColor(Mau.chu)
                .accessibilityAddTraits(.isHeader)
            if !ds.isEmpty {
                Text("\(ds.count) kế hoạch · \(Lich.moTaPhut(ds.reduce(0) { $0 + $1.thoiLuong }))")
                    .chu(14).foregroundColor(Mau.chuPhu)
            }
            if ds.isEmpty {
                Spacer()
                Text("Ngày này còn trống.\nThêm một việc nhỏ thôi cũng được.")
                    .chu(16).foregroundColor(Mau.chuPhu).multilineTextAlignment(.center)
                    .frame(maxWidth: .infinity)
                Spacer()
            } else {
                dongThoiGian(ds)
            }
            Button("+ Thêm kế hoạch") { taoMoi = true }
                .buttonStyle(NutChinhStyle()).chu(18, dam: true)
                .padding(.vertical, 8)
        }
    }

    private func dongThoiGian(_ ds: [KeHoach]) -> some View {
        ScrollViewReader { cuon in
            // List (khong phai ScrollView): `swipeActions` chi chay trong List.
            DanhSachPhang {
                TimelineView(.everyMinute) { _ in
                    let laHomNay = ngayChon == SoLich.homNay()
                    let bayGio = laHomNay ? SoLich.bayGio() - SoLich.homNay() * 1440 : -1
                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(Array(ds.enumerated()), id: \.element.id) { i, kh in
                            if laHomNay && bayGio < kh.batDau && (i == 0 || bayGio >= ds[i - 1].batDau) {
                                vachBayGio(bayGio).id("bay_gio")
                            }
                            if i > 0 {
                                let trong = kh.batDau - ds[..<i].map(\.ketThuc).max()!
                                if trong >= 15 {
                                    Text("Trống \(Lich.moTaPhut(trong))").chu(13)
                                        .foregroundColor(Mau.chuPhu).padding(.leading, 64)
                                }
                            }
                            hangKeHoach(kh)
                        }
                        if laHomNay && bayGio >= (ds.last?.batDau ?? 0) {
                            vachBayGio(bayGio).id("bay_gio")
                        }
                    }
                    .padding(.vertical, 8)
                }
                .hangTron(tren: 0, duoi: 0)
            }
            .onAppear { withAnimation { cuon.scrollTo("bay_gio", anchor: .center) } }
        }
    }

    private func vachBayGio(_ phut: Int) -> some View {
        HStack(spacing: 8) {
            Text("Bây giờ \(Lich.gioPhut(phut))").chu(13, dam: true).foregroundColor(Mau.nhan)
            Rectangle().fill(Mau.nhan).frame(height: 2)
        }
        .accessibilityLabel("Bây giờ là \(Lich.gioPhut(phut))")
    }

    private func doiXong(_ kh: KeHoach) {
        lich.doiXong(kh.id, ngay: ngayChon)
        if lich.daXong.contains(Lich.khoaXong(kh.id, ngayChon)) && ngayChon == SoLich.homNay() { tienDo.ghi() }
    }

    /// Xoa NGAY, Hoan tac 5 giay - khong hop thoai xac nhan.
    private func xoa(_ kh: KeHoach) {
        Rung.xong()
        let dauXong = lich.daXong.filter { $0.hasPrefix(kh.id + "|") }
        lich.xoa(kh.id)
        ht.hien(kh.lapLai == .khong ? "Đã xoá “\(kh.ten)”" : "Đã xoá “\(kh.ten)” và mọi lần lặp") {
            lich.khoiPhuc(kh, daXong: dauXong)
        }
    }

    private func hangKeHoach(_ kh: KeHoach) -> some View {
        let xong = lich.daXong.contains(Lich.khoaXong(kh.id, ngayChon))
        let phu = ([Lich.moTaPhut(kh.thoiLuong), kh.oDau, kh.lapLai == .khong ? nil : kh.lapLai.moTa]
            .compactMap { $0 }).joined(separator: " · ")
        return HStack(alignment: .top, spacing: 8) {
            VStack(alignment: .leading, spacing: 2) {
                Text(Lich.gioPhut(kh.batDau)).chu(15, dam: true).foregroundColor(Mau.chu)
                Text(Lich.gioPhut(kh.ketThuc)).chu(13).foregroundColor(Mau.chuPhu)
            }
            .frame(width: 56, alignment: .leading)

            Button { thaoTac = kh } label: {
                HStack(spacing: 10) {
                    OTron(xong: xong) { doiXong(kh) }
                    VStack(alignment: .leading, spacing: 2) {
                        Text(kh.ten).chu(17, dam: true).foregroundColor(Mau.chu)
                            .multilineTextAlignment(.leading)
                        Text(phu).chu(14).foregroundColor(Mau.chu)
                        if !kh.nhacTruoc.isEmpty {
                            Text("🔔 " + kh.nhacTruoc.sorted(by: >).map(Lich.moTaNhac).joined(separator: ", "))
                                .chu(13).foregroundColor(Mau.chuPhu)
                        }
                    }
                    Spacer(minLength: 0)
                }
                .padding(.horizontal, 14).padding(.vertical, 12)
                // Cao theo thoi luong, co tran de khong chiem ca man hinh.
                .frame(maxWidth: .infinity, minHeight: CGFloat(min(max(Double(kh.thoiLuong) * 1.4, 64), 220)),
                       alignment: .leading)
                .background(RoundedRectangle(cornerRadius: 18, style: .continuous).fill(Mau.buoc[kh.mau % 5]))
                .opacity(xong ? 0.55 : 1)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("\(Lich.gioPhut(kh.batDau)) đến \(Lich.gioPhut(kh.ketThuc)), \(kh.ten), \(phu)\(xong ? ", đã xong" : "")")
            .accessibilityActions {
                Button(xong ? "Bỏ đánh dấu xong" : "Đánh dấu xong") { doiXong(kh) }
                Button("Xoá") { xoa(kh) }
            }
        }
        .swipeActions(edge: .leading, allowsFullSwipe: true) {
            Button(role: .destructive) { xoa(kh) } label: { Label("Xoá", systemImage: "trash") }
        }
        .swipeActions(edge: .trailing, allowsFullSwipe: true) {
            Button { doiXong(kh) } label: { Label(xong ? "Bỏ xong" : "Xong", systemImage: "checkmark") }
                .tint(Mau.nhan)
        }
    }
}
