import SwiftUI

/// MAN HINH HOM NAY - ban Swift cua `activity_main.xml`.
///
/// iPhone: mot cot. iPad (size class regular): hai cot - trai la thu LIEC
/// MOT CAI LA THAY (thoi gian, ke hoach tiep theo), phai la thu de lam.
struct ManHinhChinh: View {
    @EnvironmentObject var m: FlowyModel
    @EnvironmentObject var settings: AppSettings
    @Environment(\.horizontalSizeClass) private var sizeClass

    @State private var hoiViecMoi = false
    @State private var chonGioHen = false
    @State private var chonUoc = false
    @State private var nhapUoc = false
    @State private var soUoc = ""

    var body: some View {
        NavigationStack {
            Group {
                if sizeClass == .regular {
                    HStack(alignment: .top, spacing: 24) {
                        ScrollView {
                            VStack(spacing: 16) { khoiThoiGian; TheTiepTheo() }.padding(.bottom, 24)
                        }
                        .frame(maxWidth: 380)
                        ScrollView {
                            VStack(spacing: 16) {
                                khoiYDinh; khoiHoi; khoiBuoc; khoiHanhDong
                            }.padding(.bottom, 24)
                        }
                    }
                    .padding(.horizontal, 28)
                } else {
                    ScrollView {
                        VStack(spacing: 12) {
                            TheTiepTheo()
                            khoiYDinh; khoiHoi; khoiThoiGian; khoiBuoc; khoiHanhDong
                        }
                        .padding(.horizontal, 16).padding(.bottom, 24)
                    }
                    .scrollDismissesKeyboard(.interactively)
                }
            }
            .background(Mau.nen.ignoresSafeArea())
            .navigationTitle("Flowy")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Text(m.trangThai).chu(12).foregroundColor(Mau.chuPhu).lineLimit(1)
                        .frame(maxWidth: 220, alignment: .trailing)
                }
            }
        }
        .sheet(isPresented: $chonGioHen) { ChonGioHen().environmentObject(m).environmentObject(settings) }
        .confirmationDialog("Việc này bạn nghĩ mất bao lâu?", isPresented: $chonUoc, titleVisibility: .visible) {
            ForEach([5, 10, 15, 25, 45, 60], id: \.self) { p in
                Button("\(p) phút") { m.datUoc(Double(p)) }
            }
            Button("Số khác") { soUoc = ""; nhapUoc = true }
            Button("Huỷ", role: .cancel) {}
        } message: {
            Text("Không cần đúng. Lần sau Flowy sẽ cho bạn thấy thực tế mất bao lâu.")
        }
        .alert("Số phút", isPresented: $nhapUoc) {
            TextField("Ví dụ 20", text: $soUoc).keyboardType(.numberPad)
            Button("Lưu") { if let n = Int(soUoc), (1...1440).contains(n) { m.datUoc(Double(n)) } }
            Button("Huỷ", role: .cancel) {}
        }
        .alert("Bỏ việc này và bắt đầu gom một việc khác?", isPresented: $hoiViecMoi) {
            Button("Việc mới") { m.viecMoi() }
            Button("Huỷ", role: .cancel) {}
        }
    }

    // MARK: Y dinh

    private var khoiYDinh: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                NhanKhoi(chu: "Việc đang làm")
                Spacer()
                Button("Việc mới") {
                    if m.tra.trongPhien || m.tra.viecGi != nil { hoiViecMoi = true } else { m.viecMoi() }
                }
                .chu(15).foregroundColor(Mau.nhan).frame(minHeight: 44)
            }
            Text(m.tra.viecGi ?? "Chưa có việc nào")
                .chu(19, dam: true)
                .foregroundColor(m.tra.viecGi == nil ? Mau.chuPhu : Mau.chu)
            Text("\(m.tra.khiNao ?? "—") · \(m.tra.oDau ?? "—")")
                .chu(15).foregroundColor(Mau.chuPhu)
        }
        .the()
    }

    // MARK: Cau hoi + o nhap

    private var khoiHoi: some View {
        VStack(alignment: .leading, spacing: 8) {
            if !m.cauHoi.isEmpty {
                Text(m.cauHoi).chu(22, dam: true, theo: .title3).foregroundColor(Mau.chu)
                    .accessibilityAddTraits(.isHeader)
            }
            HStack(spacing: 8) {
                TextField(m.duYDinh ? "Thêm một bước nhỏ" : "Trả lời ở đây", text: $m.oTraLoi)
                    .chu(17)
                    .submitLabel(.send)
                    .onSubmit { m.guiLoiGo() }
                    .padding(.horizontal, 16)
                    .frame(minHeight: 52)
                    .background(RoundedRectangle(cornerRadius: 14).fill(Mau.the))
                    .overlay(RoundedRectangle(cornerRadius: 14).stroke(Mau.vien, lineWidth: 1.5))
                Button { m.nghe() } label: {
                    Image(systemName: m.dangNghe ? "waveform" : "mic.fill")
                }
                .buttonStyle(NutPhuStyle()).frame(width: 56)
                .accessibilityLabel(m.dangNghe ? "Đang nghe" : "Nói")
                Button("Gửi") { m.guiLoiGo() }.buttonStyle(NutPhuStyle()).frame(width: 72)
            }
        }
    }

    // MARK: Khoi 1 - thoi gian

    private var khoiThoiGian: some View {
        let r = m.tra
        return VStack(spacing: 8) {
            NhanKhoi(chu: "Thời gian").frame(maxWidth: .infinity, alignment: .leading)
            VongThoiGian(conLai: r.conLaiGiay, tong: r.tongGiay)
                .frame(height: sizeClass == .regular ? 240 : 150)
            Text(r.conLaiGiay.map { "còn \(Int(($0 / 60).rounded(.up))) phút" } ?? "Chưa có giờ hẹn")
                .chu(17).foregroundColor(Mau.chu)
            Text(dongGoiY).chu(14).foregroundColor(Mau.chuPhu).frame(minHeight: 20)
            HStack(spacing: 8) {
                Button(r.gioHen.map { "Hẹn \($0)" } ?? "Đặt giờ hẹn") { chonGioHen = true }
                    .buttonStyle(NutPhuStyle())
                Button(r.uocPhut.map { "Ước \(Int($0.rounded())) phút" } ?? "Ước lượng") { chonUoc = true }
                    .buttonStyle(NutPhuStyle())
            }
            .chu(15)
        }
        .the()
    }

    private var dongGoiY: String {
        let r = m.tra
        if r.tamDung { return "Đang tạm dừng" }
        if r.trongPhien, let g = r.daLamGiay { return "Đã làm \(Int((g / 60).rounded())) phút" }
        if let p = r.goiYPhut { return "Những lần trước: khoảng \(Int(p.rounded())) phút" }
        return ""
    }

    // MARK: Khoi 2 - buoc

    private var khoiBuoc: some View {
        let r = m.tra
        let conBuoc = r.chiSoBuoc < r.cacBuoc.count
        let hienTai: String = {
            if r.trongPhien && conBuoc { return r.cacBuoc[r.chiSoBuoc] }
            if r.trongPhien { return r.viecGi ?? "—" }
            if !r.cacBuoc.isEmpty && !conBuoc { return "Xong hết các bước." }
            return "—"
        }()
        return VStack(alignment: .leading, spacing: 8) {
            NhanKhoi(chu: "Bước hiện tại")
            Text(hienTai).chu(sizeClass == .regular ? 30 : 24, dam: true, theo: .title2)
                .foregroundColor(Mau.chu)
            if r.cacBuoc.isEmpty {
                Text("Chưa có bước nào. Gõ một bước nhỏ ở ô trên, ví dụ: mở tệp lên.")
                    .chu(15).foregroundColor(Mau.chuPhu)
            } else {
                ForEach(Array(r.cacBuoc.enumerated()), id: \.offset) { i, ten in
                    let xong = r.trongPhien && i < r.chiSoBuoc
                    let dangLam = r.trongPhien && i == r.chiSoBuoc
                    KhoiMau(chiSoMau: i, vienNhan: dangLam, mo: xong) {
                        AnyView(Text(xong ? "✓  \(ten)" : ten)
                            .chu(dangLam ? 17 : 15, dam: dangLam).foregroundColor(Mau.chu))
                    }
                    .accessibilityLabel(xong ? "Đã xong: \(ten)" : (dangLam ? "Đang làm: \(ten)" : ten))
                }
            }
            Divider().overlay(Mau.vien).padding(.vertical, 4)
            HStack(spacing: 10) {
                Text(m.cauNoi.isEmpty ? "Bị kẹt? Bấm Gợi ý, Flowy sẽ hỏi một câu nhỏ." : m.cauNoi)
                    .chu(15).foregroundColor(m.cauNoi.isEmpty ? Mau.chuPhu : Mau.chu)
                    .frame(maxWidth: .infinity, alignment: .leading)
                Button("Gợi ý") { m.goiY() }.buttonStyle(NutPhuStyle()).frame(width: 96).chu(15)
            }
        }
        .the()
    }

    // MARK: Nut

    private var khoiHanhDong: some View {
        let r = m.tra
        let nhan: String = {
            switch m.nutChinh {
            case .batDau: return "Bắt đầu"
            case .xongBuoc: return "Xong bước"
            case .xongViec: return "Xong việc"
            case .tiepTuc: return "Tiếp tục"
            }
        }()
        return VStack(spacing: 10) {
            Button(nhan) { m.bamNutChinh() }.buttonStyle(NutChinhStyle()).chu(18, dam: true)
            HStack(spacing: 8) {
                Button(r.tamDung ? "Tiếp tục" : "Tạm dừng") { m.tamDungHoacTiepTuc() }
                    .buttonStyle(NutPhuStyle()).disabled(!r.trongPhien)
                Button("Kết thúc") { m.ketThuc() }
                    .buttonStyle(NutPhuStyle()).disabled(!r.trongPhien)
            }
            .chu(15)
            HStack(spacing: 6) {
                NhanKhoi(chu: "Nhắc giờ")
                ForEach(MucNhac.allCases) { muc in
                    Chip(nhan: muc.nhan, chon: settings.mucNhac == muc) { m.doiMucNhac(muc) }
                        .frame(maxWidth: .infinity)
                }
            }
        }
    }
}

/// The ke hoach tiep theo hom nay. An khi dang trong phien hoac het viec.
struct TheTiepTheo: View {
    @EnvironmentObject var m: FlowyModel
    @EnvironmentObject var lich: SoLich

    var body: some View {
        TimelineView(.periodic(from: .now, by: 30)) { _ in
            let bay = SoLich.bayGio()
            if !m.tra.trongPhien,
               let kh = Lich.tiepTheo(lich.danhSach, bayGio: bay, daXong: lich.daXong) {
                let phut = bay - SoLich.homNay() * 1440
                HStack(spacing: 10) {
                    Text(kh.emoji).font(.system(size: 26))
                        .frame(width: 48, height: 48)
                        .background(Circle().fill(Mau.buoc[kh.mau % 5]))
                    VStack(alignment: .leading, spacing: 2) {
                        Text(kh.batDau <= phut
                             ? "Đang diễn ra · đến \(Lich.gioPhut(kh.ketThuc))"
                             : "Tiếp theo · \(Lich.gioPhut(kh.batDau)) (còn \(Lich.moTaPhut(kh.batDau - phut)))")
                            .chu(13).foregroundColor(Mau.chuPhu)
                        Text(kh.ten).chu(17, dam: true).foregroundColor(Mau.chu).lineLimit(2)
                    }
                    Spacer(minLength: 4)
                    Button("Bắt đầu") { m.batDauTuKeHoach(kh) }
                        .buttonStyle(NutPhuStyle()).frame(width: 104).chu(15)
                }
                .the(12)
                .accessibilityElement(children: .combine)
            }
        }
    }
}

/// Chon gio hen bang DatePicker cua iOS - khong phai go tay.
struct ChonGioHen: View {
    @EnvironmentObject var m: FlowyModel
    @Environment(\.dismiss) private var dong
    @State private var gio = Date().addingTimeInterval(30 * 60)

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                DatePicker("Giờ hẹn", selection: $gio, displayedComponents: .hourAndMinute)
                    .datePickerStyle(.wheel)
                    .labelsHidden()
                    .environment(\.locale, Locale(identifier: "vi_VN"))
                Button("Lưu giờ hẹn") {
                    let c = Calendar.current.dateComponents([.hour, .minute], from: gio)
                    m.datGioHen(Double((c.hour ?? 0) * 60 + (c.minute ?? 0)))
                    dong()
                }
                .buttonStyle(NutChinhStyle())
                if m.tra.gioHen != nil {
                    Button("Bỏ giờ hẹn") { m.datGioHen(nil); dong() }.buttonStyle(NutPhuStyle())
                }
                Spacer()
            }
            .padding(20)
            .background(Mau.nen.ignoresSafeArea())
            .navigationTitle("Giờ cần xong")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Huỷ") { dong() } } }
        }
        .presentationDetents([.medium])
        .onAppear {
            if let s = m.tra.gioHen, let p = DocGio.doc(s) {
                gio = Calendar.current.date(bySettingHour: Int(p) / 60, minute: Int(p) % 60,
                                            second: 0, of: Date()) ?? gio
            }
        }
    }
}
