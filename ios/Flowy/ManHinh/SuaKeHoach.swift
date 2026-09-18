import SwiftUI

/// TAO / SUA KE HOACH (v4).
///
/// - Bat dau VA ket thuc deu tu chon (DatePicker gio). Thoi luong tu tinh.
///   Chip nhanh (+15 +30...) chi la loi tat dat Ket thuc, khong phai gioi han.
/// - Lap lai theo THU cu the (T2, T5...).
/// - Nhac tuy y: chip mau san + "Tuỳ chỉnh" (so + phut/gio/ngay, toi da 7 ngay).
/// - Uu tien Cao / Vua / Thap.
///
/// Moi hang dung `HangCaiDat` - khuon chung, khong hang nao lech duoc.
struct SuaKeHoach: View {
    let keHoach: KeHoach?
    let ngayMacDinh: Int

    @EnvironmentObject var lich: SoLich
    @Environment(\.dismiss) private var dong

    @State private var ten = ""
    @State private var emoji = Lich.emoji[0]
    @State private var mau = 0
    @State private var ngay = Date()
    @State private var batDau = Date()
    @State private var ketThuc = Date()
    @State private var lapLai = LapLai.khong
    @State private var thuLap: Set<Int> = []
    @State private var nhac: Set<Int> = [15, 0]
    @State private var uuTien = UuTien.vua
    @State private var oDau = ""
    @State private var loiTen = false
    @State private var hoiXoa = false
    @State private var nhapNhac = false
    @State private var soNhac = 20
    @State private var donViNhac = 0

    private var phutBatDau: Int { phut(batDau) }
    private var phutKetThuc: Int { phut(ketThuc) }
    private var thoiLuong: Int { Lich.thoiLuongGiua(phutBatDau, phutKetThuc) }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    HStack(spacing: 10) {
                        Text(emoji).font(.system(size: 26))
                            .frame(width: 56, height: 56)
                            .background(RoundedRectangle(cornerRadius: 16).fill(Mau.the))
                        TextField("Tên kế hoạch", text: $ten)
                            .chu(18).foregroundColor(Mau.chu)
                            .padding(.horizontal, 14).frame(height: 56)
                            .background(RoundedRectangle(cornerRadius: 16).fill(Mau.the))
                            .overlay(RoundedRectangle(cornerRadius: 16).stroke(loiTen ? Mau.cam : Mau.vien, lineWidth: loiTen ? 2 : 1))
                            .onChange(of: ten) { _ in loiTen = false }
                    }
                    if loiTen {
                        Text("Cần ít nhất \(Lich.minKyTu) ký tự để sau này bạn còn nhận ra.")
                            .chu(13).foregroundColor(Mau.chu).padding(.leading, 66)
                    }

                    // Uu tien
                    VStack(alignment: .leading, spacing: 4) {
                        HangCaiDat(icon: "flag", nhan: "Ưu tiên")
                        HStack(spacing: 8) {
                            ForEach(UuTien.allCases) { u in
                                ChipChon(nhan: u.nhan, chon: uuTien == u, cham: Mau.uuTien(u), gian: true) { uuTien = u }
                            }
                        }
                    }.the()

                    // Thoi gian
                    VStack(alignment: .leading, spacing: 0) {
                        DatePicker(selection: $ngay, displayedComponents: .date) {
                            nhanHang("calendar", "Ngày")
                        }
                        .datePickerStyle(.compact).frame(minHeight: 56).tint(Mau.chuLienKet)
                        vach
                        DatePicker(selection: $batDau, displayedComponents: .hourAndMinute) {
                            nhanHang("clock", "Bắt đầu")
                        }
                        .datePickerStyle(.compact).frame(minHeight: 56).tint(Mau.chuLienKet)
                        .onChange(of: batDau) { moi in
                            // Doi bat dau thi GIU thoi luong: ket thuc di theo.
                            ketThuc = moi.addingTimeInterval(TimeInterval(thoiLuongCu * 60))
                        }
                        vach
                        DatePicker(selection: $ketThuc, displayedComponents: .hourAndMinute) {
                            nhanHang("clock", phutKetThuc <= phutBatDau ? "Kết thúc (hôm sau)" : "Kết thúc")
                        }
                        .datePickerStyle(.compact).frame(minHeight: 56).tint(Mau.chuLienKet)
                        .onChange(of: ketThuc) { _ in thoiLuongCu = thoiLuong }

                        Text("Kéo dài \(Lich.moTaPhut(thoiLuong))")
                            .chu(13).foregroundColor(Mau.chuPhu).padding(.top, 8).padding(.leading, 32)
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 8) {
                                ForEach(Lich.mucThoiLuong, id: \.self) { p in
                                    ChipChon(nhan: "+\(Lich.moTaPhut(p))", chon: thoiLuong == p) {
                                        ketThuc = batDau.addingTimeInterval(TimeInterval(p * 60))
                                        thoiLuongCu = p
                                    }
                                }
                            }.padding(.vertical, 6)
                        }
                    }.the()

                    // Lap lai
                    VStack(alignment: .leading, spacing: 8) {
                        HangCaiDat(icon: "repeat", nhan: "Lặp lại")
                        HStack(spacing: 8) {
                            ForEach([LapLai.khong, .hangNgay, .theoThu], id: \.self) { l in
                                ChipChon(nhan: l.moTa, chon: lapLai == l, gian: true) {
                                    lapLai = l
                                    if l == .theoThu && thuLap.isEmpty { thuLap = [Lich.thu(SoLich.ngayCua(ngay))] }
                                }
                            }
                        }
                        if lapLai == .theoThu {
                            HStack(spacing: 6) {
                                ForEach(0..<7, id: \.self) { t in
                                    let chon = thuLap.contains(t)
                                    Button {
                                        Rung.nhe()
                                        // Luon con it nhat MOT thu.
                                        if chon { if thuLap.count > 1 { thuLap.remove(t) } } else { thuLap.insert(t) }
                                    } label: {
                                        Text(Lich.tenThuNgan[t]).chu(13, dam: chon)
                                            .foregroundColor(chon ? Mau.chuTrenNhan : Mau.chu)
                                            .frame(maxWidth: .infinity, minHeight: 42)
                                            .background(Circle().fill(chon ? Mau.nhan : Mau.nen))
                                            .overlay(Circle().stroke(chon ? Mau.nhanVien : Mau.vien, lineWidth: 1))
                                    }
                                    .buttonStyle(.plain)
                                    .accessibilityLabel(Lich.tenThu[t] + (chon ? ", đang chọn" : ""))
                                }
                            }
                            Text(Lich.moTaLapLai(taoKeHoach(ten: "x")))
                                .chu(13).foregroundColor(Mau.chuPhu)
                                .frame(maxWidth: .infinity, alignment: .center)
                        }
                    }.the()

                    // Nhac
                    VStack(alignment: .leading, spacing: 8) {
                        HangCaiDat(icon: "bell", nhan: "Nhắc tôi",
                                   giaTri: nhac.isEmpty ? "Không nhắc" : nil)
                        if !nhac.isEmpty {
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 8) {
                                    ForEach(nhac.sorted(by: >), id: \.self) { p in
                                        ChipChon(nhan: "\(Lich.moTaNhac(p))  ✕", chon: true) { nhac.remove(p) }
                                            .accessibilityLabel("Bỏ mốc nhắc \(Lich.moTaNhac(p))")
                                    }
                                }.padding(.vertical, 4)
                            }
                        }
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 8) {
                                ForEach(Lich.mucNhac.filter { !nhac.contains($0) }, id: \.self) { p in
                                    ChipChon(nhan: "+ \(Lich.moTaNhac(p))") { nhac.insert(p) }
                                }
                                ChipChon(nhan: "Tuỳ chỉnh…") { nhapNhac = true }
                            }.padding(.vertical, 4)
                        }
                        Text("Nhắc trước và nhắc đúng giờ là hai mốc riêng. Bỏ hết thì không nhắc.")
                            .chu(12).foregroundColor(Mau.chuPhu)
                    }.the()

                    // Bieu tuong va mau
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Biểu tượng").chu(15, dam: true).foregroundColor(Mau.chu)
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 6) {
                                ForEach(Lich.emoji, id: \.self) { e in
                                    ChipChon(nhan: e, chon: e == emoji) { emoji = e }
                                }
                            }.padding(.vertical, 4)
                        }
                        HStack(spacing: 12) {
                            ForEach(0..<5, id: \.self) { i in
                                Button { Rung.nhe(); mau = i } label: {
                                    Circle().fill(Mau.buoc[i])
                                        .overlay(Circle().stroke(i == mau ? Mau.chu : Mau.vien, lineWidth: i == mau ? 3 : 1))
                                        .frame(width: 44, height: 44)
                                        .overlay(i == mau ? Image(systemName: "checkmark").foregroundColor(Mau.chu) : nil)
                                }
                                .buttonStyle(.plain)
                                .accessibilityLabel("Màu \(i + 1)" + (i == mau ? ", đang chọn" : ""))
                            }
                        }
                    }.the()

                    VStack(alignment: .leading, spacing: 6) {
                        HangCaiDat(icon: "mappin", nhan: "Ở đâu (không bắt buộc)")
                        TextField("Ví dụ: bàn học", text: $oDau)
                            .chu(16).foregroundColor(Mau.chu)
                            .padding(.horizontal, 14).frame(height: 50)
                            .background(RoundedRectangle(cornerRadius: 14).fill(Mau.nen))
                            .overlay(RoundedRectangle(cornerRadius: 14).stroke(Mau.vien, lineWidth: 1))
                    }.the()

                    Button("Lưu kế hoạch") { luu() }
                        .buttonStyle(NutChinhStyle()).chu(18, dam: true).padding(.top, 8)
                }
                .padding(16)
            }
            .background(Mau.nen.ignoresSafeArea())
            .navigationTitle(keHoach == nil ? "Kế hoạch mới" : "Sửa kế hoạch")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) { Button("Quay lại") { dong() } }
                if keHoach != nil {
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button("Xoá", role: .destructive) { hoiXoa = true }
                    }
                }
            }
            .alert("Xoá kế hoạch này?", isPresented: $hoiXoa) {
                Button("Xoá", role: .destructive) { if let k = keHoach { lich.xoa(k.id); dong() } }
                Button("Huỷ", role: .cancel) {}
            } message: {
                if keHoach?.lapLai != .khong { Text("Kế hoạch lặp lại: xoá sẽ bỏ mọi lần của nó.") }
            }
            .alert("Nhắc trước bao lâu?", isPresented: $nhapNhac) {
                TextField("Số", value: $soNhac, format: .number).keyboardType(.numberPad)
                Button("Thêm") {
                    let heSo = [1, 60, 1440][donViNhac]
                    nhac.insert(min(max(soNhac, 1) * heSo, Lich.nhacToiDa))
                }
                Button("Huỷ", role: .cancel) {}
            } message: {
                Text("Đơn vị: \(["phút", "giờ", "ngày"][donViNhac]). Xa nhất 7 ngày.")
            }
        }
        .onAppear { nap() }
    }

    @State private var thoiLuongCu = 30

    private var vach: some View {
        Rectangle().fill(Mau.vien).frame(height: 1).padding(.leading, 32)
    }

    private func nhanHang(_ icon: String, _ nhan: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon).font(.system(size: 17))
                .frame(width: 20, height: 20).foregroundColor(Mau.chuPhu)
            Text(nhan).chu(15).foregroundColor(Mau.chu)
        }
    }

    private func phut(_ d: Date) -> Int {
        let c = Calendar.current.dateComponents([.hour, .minute], from: d)
        return (c.hour ?? 0) * 60 + (c.minute ?? 0)
    }

    private func nap() {
        guard let k = keHoach else {
            ngay = SoLich.sangDate(max(ngayMacDinh, SoLich.homNay()) * 1440)
            let bay = SoLich.bayGio()
            let phutTron = min(((bay % 1440) / 15 + 2) * 15, 23 * 60 + 15)
            batDau = SoLich.sangDate(SoLich.ngayCua(ngay) * 1440 + phutTron)
            ketThuc = batDau.addingTimeInterval(30 * 60)
            thoiLuongCu = 30
            return
        }
        ten = k.ten; emoji = k.emoji; mau = k.mau; uuTien = k.uuTien
        ngay = SoLich.sangDate(k.ngay * 1440)
        batDau = SoLich.sangDate(k.ngay * 1440 + k.batDau)
        ketThuc = batDau.addingTimeInterval(TimeInterval(k.thoiLuong * 60))
        thoiLuongCu = k.thoiLuong
        lapLai = k.lapLai == .hangTuan ? .theoThu : k.lapLai
        thuLap = k.lapLai == .hangTuan ? [Lich.thu(k.ngay)] : k.thuLap
        nhac = Set(k.nhacTruoc)
        oDau = k.oDau ?? ""
    }

    private func taoKeHoach(ten t: String) -> KeHoach {
        KeHoach(id: keHoach?.id ?? UUID().uuidString, ten: t, emoji: emoji, mau: mau,
                ngay: SoLich.ngayCua(ngay), batDau: phutBatDau, thoiLuong: thoiLuong,
                lapLai: lapLai, nhacTruoc: nhac.sorted(by: >),
                oDau: oDau.trimmingCharacters(in: .whitespaces).isEmpty ? nil : oDau,
                thuLap: lapLai == .theoThu ? thuLap : [], uuTien: uuTien)
    }

    private func luu() {
        let t = ten.trimmingCharacters(in: .whitespacesAndNewlines)
        guard t.count >= Lich.minKyTu else { loiTen = true; return }
        lich.luu(taoKeHoach(ten: t))
        Rung.xong()
        dong()
    }
}
