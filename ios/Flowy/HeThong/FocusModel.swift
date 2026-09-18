import SwiftUI
import UserNotifications

/// TRANG THAI TAB FOCUS - khop Android `TrangThaiFocus` + `FocusBao`.
/// Luu trong UserDefaults, song qua dong app. Chuong het gio la mot
/// UNNotification dat vao dung moc ket thuc.
final class FocusModel: ObservableObject {
    @Published var dem = DemNguoc() { didSet { luu() } }
    @Published var ten: String? { didSet { luu() } }
    @Published var buocDau: String? { didSet { luu() } }
    @Published var lyDo: String? { didSet { luu() } }
    @Published var keHoachId: String? { didSet { luu() } }
    @Published var laNghi = false { didSet { luu() } }
    /// Phien vua het: so phut da lam. Con gia tri thi hien the ket qua.
    @Published var ketQuaPhut: Double? { didSet { luu() } }

    private static let khoa = "flowy_focus"
    private static let maBao = "flowy-focus-het-gio"
    private var dangNap = false

    private struct Luu: Codable {
        var dem: DemNguoc; var ten: String?; var buocDau: String?; var lyDo: String?
        var keHoachId: String?; var laNghi: Bool; var ketQuaPhut: Double?
    }

    init() {
        dangNap = true
        if let d = UserDefaults.standard.data(forKey: Self.khoa), let l = try? JSONDecoder().decode(Luu.self, from: d) {
            dem = l.dem; ten = l.ten; buocDau = l.buocDau; lyDo = l.lyDo
            keHoachId = l.keHoachId; laNghi = l.laNghi; ketQuaPhut = l.ketQuaPhut
        }
        dangNap = false
    }

    private func luu() {
        guard !dangNap else { return }
        let l = Luu(dem: dem, ten: ten, buocDau: buocDau, lyDo: lyDo, keHoachId: keHoachId, laNghi: laNghi, ketQuaPhut: ketQuaPhut)
        if let d = try? JSONEncoder().encode(l) { UserDefaults.standard.set(d, forKey: Self.khoa) }
    }

    func batDau() {
        dem = dem.batDau(); ketQuaPhut = nil
        datChuong()
    }

    func tamDungHoacTiep() {
        if dem.dangChay { dem = dem.tamDung(); huyChuong() } else { batDau() }
    }

    func themPhut(_ p: Int) { dem = dem.themPhut(p); datChuong() }

    func batDauTuKeHoach(_ kh: KeHoach) {
        dem = DemNguoc().datThoiLuong(min(kh.thoiLuong, DemNguoc.toiDaPhut))
        ten = kh.ten; buocDau = nil; lyDo = nil; keHoachId = kh.id; laNghi = false
        batDau()
    }

    /// Goi moi nhip. Tra ve true neu VUA het gio (de man hinh rung + ghi so).
    func kiemHetGio(lich: SoLich, tienDo: SoTienDo, thoiLuong: SoThoiLuong) -> Bool {
        guard dem.daHet() else { return false }
        let phut = dem.daLamPhut()
        if !laNghi {
            tienDo.ghi()
            if let t = ten { thoiLuong.ghi(t, thatPhut: phut, uocPhut: dem.tongGiay / 60) }
            if let id = keHoachId {
                let homNay = SoLich.homNay()
                if !lich.daXong.contains(Lich.khoaXong(id, homNay)) { lich.doiXong(id, ngay: homNay) }
            }
        }
        dem = dem.datLai(); ketQuaPhut = phut
        huyChuong()
        return true
    }

    private func datChuong() {
        huyChuong()
        guard let luc = dem.ketThucLuc, luc > Date() else { return }
        let nd = UNMutableNotificationContent()
        nd.title = laNghi ? "Hết giờ nghỉ" : "Hết giờ rồi"
        nd.body = "Chạm để mở Flowy."
        nd.sound = .default
        nd.userInfo = ["mo_tab": "focus"]
        let kh = UNTimeIntervalNotificationTrigger(timeInterval: max(1, luc.timeIntervalSinceNow), repeats: false)
        UNUserNotificationCenter.current().add(UNNotificationRequest(identifier: Self.maBao, content: nd, trigger: kh))
    }

    func huyChuong() {
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [Self.maBao])
    }
}

/// GOP LOI NHAC VAO KE HOACH - chay mot lan (khop Android `ChuyenLoiNhac`).
enum ChuyenLoiNhac {
    private static let khoa = "flowy_v4_da_gop_loi_nhac"
    static func chayMotLan(soNhac: SoNhac, lich: SoLich) {
        let d = UserDefaults.standard
        guard !d.bool(forKey: khoa) else { return }
        let homNay = SoLich.homNay()
        for ln in soNhac.danhSach {
            lich.luu(KeHoach(ten: ln.ten, emoji: "🔔", ngay: homNay, batDau: min(max(Int(ln.gio), 0), 1439),
                             thoiLuong: 15, lapLai: ln.lapLai ? .hangNgay : .khong, nhacTruoc: [0]))
        }
        if !soNhac.danhSach.isEmpty { soNhac.xoaHet(); BaoGio.datLai(soNhac) }
        d.set(true, forKey: khoa)
    }
}

/// THANH HOAN TAC 5 GIAY + THONG BAO NGAN - dung chung moi tab.
final class HoanTacModel: ObservableObject {
    struct Bao: Identifiable { let id = UUID(); let chu: String; let hoanTac: (() -> Void)? }
    @Published var bao: Bao?

    func hien(_ chu: String, hoanTac: (() -> Void)? = nil) {
        let b = Bao(chu: chu, hoanTac: hoanTac)
        withAnimation(.easeOut(duration: 0.15)) { bao = b }
        DispatchQueue.main.asyncAfter(deadline: .now() + (hoanTac == nil ? 2.5 : 5)) { [weak self] in
            if self?.bao?.id == b.id { withAnimation { self?.bao = nil } }
        }
    }
}
