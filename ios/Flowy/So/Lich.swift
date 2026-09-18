import Foundation

// MARK: - Lich kieu Tiimo - ban Swift cua `Lich.kt`
//
// Cung thuat toan, cung cach bieu dien: ngay = so ngay tu 1970-01-01 theo
// GIO DIA PHUONG, phut = phut tu nua dem. Doi sang Date o `SoLich`.
//
// Lich song tron tren may, KHONG di qua cau noi. Ten ke hoach chi thanh
// `viec_gi` khi nguoi dung bam "Bat dau viec nay".

enum LapLai: String, Codable, CaseIterable, Identifiable {
    case khong = "KHONG", hangNgay = "HANG_NGAY", hangTuan = "HANG_TUAN", theoThu = "THEO_THU"
    var id: String { rawValue }
    var moTa: String {
        switch self {
        case .khong: return "Không lặp"
        case .hangNgay: return "Hằng ngày"
        case .hangTuan: return "Hằng tuần"
        case .theoThu: return "Theo thứ"
        }
    }
}

/// Uu tien - KHOP Android `UuTien`. Khong co "khan cap".
enum UuTien: String, Codable, CaseIterable, Identifiable {
    case cao = "CAO", vua = "VUA", thap = "THAP"
    var id: String { rawValue }
    var nhan: String {
        switch self { case .cao: return "Cao"; case .vua: return "Vừa"; case .thap: return "Thấp" }
    }
    var thuTu: Int { switch self { case .cao: return 0; case .vua: return 1; case .thap: return 2 } }
}

struct KeHoach: Codable, Identifiable, Equatable {
    var id: String
    var ten: String
    var emoji: String
    /// 0...4 - chi so vao `Mau.buoc`.
    var mau: Int
    var ngay: Int
    var batDau: Int
    var thoiLuong: Int
    var lapLai: LapLai
    /// Nhac truoc bao nhieu phut. 0 = dung gio. Toi da 7 ngay.
    var nhacTruoc: [Int]
    var oDau: String?
    /// Chi dung khi lapLai = .theoThu. 0 = Thu Hai ... 6 = Chu Nhat.
    var thuLap: Set<Int>
    var uuTien: UuTien

    var ketThuc: Int { batDau + thoiLuong }

    init(id: String = UUID().uuidString, ten: String, emoji: String = "📝", mau: Int = 0,
         ngay: Int, batDau: Int, thoiLuong: Int = 30, lapLai: LapLai = .khong,
         nhacTruoc: [Int] = [15, 0], oDau: String? = nil, thuLap: Set<Int> = [], uuTien: UuTien = .vua) {
        self.id = id; self.ten = ten; self.emoji = emoji; self.mau = mau; self.ngay = ngay
        self.batDau = batDau; self.thoiLuong = thoiLuong; self.lapLai = lapLai
        self.nhacTruoc = nhacTruoc; self.oDau = oDau; self.thuLap = thuLap; self.uuTien = uuTien
    }

    /// Doc tay: du lieu tu ban truoc KHONG co thuLap / uuTien. Codable tu sinh
    /// se nem loi khi thieu khoa va lam MAT CA LICH.
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decodeIfPresent(String.self, forKey: .id) ?? UUID().uuidString
        ten = try c.decode(String.self, forKey: .ten)
        emoji = try c.decodeIfPresent(String.self, forKey: .emoji) ?? "📝"
        mau = try c.decodeIfPresent(Int.self, forKey: .mau) ?? 0
        ngay = try c.decode(Int.self, forKey: .ngay)
        batDau = try c.decode(Int.self, forKey: .batDau)
        thoiLuong = try c.decodeIfPresent(Int.self, forKey: .thoiLuong) ?? 30
        lapLai = (try? c.decodeIfPresent(LapLai.self, forKey: .lapLai)) ?? .khong
        nhacTruoc = try c.decodeIfPresent([Int].self, forKey: .nhacTruoc) ?? [15, 0]
        oDau = try c.decodeIfPresent(String.self, forKey: .oDau)
        thuLap = Set((try c.decodeIfPresent([Int].self, forKey: .thuLap) ?? []).filter { (0...6).contains($0) })
        uuTien = (try? c.decodeIfPresent(UuTien.self, forKey: .uuTien)) ?? .vua
    }
}

struct LanNhac: Equatable {
    let keHoach: KeHoach
    let ngayDienRa: Int
    let truoc: Int
    let phutTuyetDoi: Int
}

enum Lich {

    static let minKyTu = 3
    static let mucNhac = [0, 5, 15, 30, 60, 24 * 60]
    /// Nhac tuy chinh xa nhat: 7 ngay.
    static let nhacToiDa = 7 * 24 * 60
    static let mucThoiLuong = [15, 30, 45, 60, 90]
    static let emoji = ["📝", "📚", "💻", "🧹", "🍳", "🏃", "💊", "🛒", "📞", "🚿", "😴", "🎧"]
    static let tenThuNgan = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    static let tenThu = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

    static func coTrongNgay(_ kh: KeHoach, _ ngay: Int) -> Bool {
        switch kh.lapLai {
        case .khong: return ngay == kh.ngay
        case .hangNgay: return ngay >= kh.ngay
        case .hangTuan: return ngay >= kh.ngay && (ngay - kh.ngay) % 7 == 0
        case .theoThu:
            let t: Set<Int> = kh.thuLap.isEmpty ? [thu(kh.ngay)] : kh.thuLap
            return ngay >= kh.ngay && t.contains(thu(ngay))
        }
    }

    static func trongNgay(_ ds: [KeHoach], _ ngay: Int) -> [KeHoach] {
        ds.filter { coTrongNgay($0, ngay) }
            .sorted { ($0.batDau, $0.ten) < ($1.batDau, $1.ten) }
    }

    static func lanNhacToi(_ ds: [KeHoach], bayGio: Int, soNgay: Int = 8, toiDa: Int = 48) -> [LanNhac] {
        let homNay = chiaSan(bayGio, 1440)
        let het = bayGio + soNgay * 1440
        var ra: [LanNhac] = []
        // Nhac truoc toi 7 ngay: xet them bay nhieu ngay phia sau.
        let ngayThem = ((ds.flatMap { $0.nhacTruoc }.max() ?? 0) + 1439) / 1440
        for ngay in homNay...(homNay + soNgay + ngayThem + 1) {
            for kh in ds where coTrongNgay(kh, ngay) {
                for truoc in Set(kh.nhacTruoc) {
                    let luc = ngay * 1440 + kh.batDau - truoc
                    if luc > bayGio && luc <= het {
                        ra.append(LanNhac(keHoach: kh, ngayDienRa: ngay, truoc: truoc, phutTuyetDoi: luc))
                    }
                }
            }
        }
        return Array(ra.sorted { $0.phutTuyetDoi < $1.phutTuyetDoi }.prefix(toiDa))
    }

    static func tiepTheo(_ ds: [KeHoach], bayGio: Int, daXong: Set<String>) -> KeHoach? {
        let ngay = chiaSan(bayGio, 1440)
        let phut = bayGio - ngay * 1440
        return trongNgay(ds, ngay)
            .filter { !daXong.contains(khoaXong($0.id, ngay)) }
            .first { $0.ketThuc > phut }
    }

    static func khoaXong(_ id: String, _ ngay: Int) -> String { "\(id)|\(ngay)" }

    // MARK: Cau chu

    static func cauNhac(_ ln: LanNhac) -> String {
        let kh = ln.keHoach
        let gio = gioPhut(kh.batDau)
        if ln.truoc == 0 { return "Đến giờ rồi: \(kh.ten)." }
        if ln.truoc >= 24 * 60 { return "Ngày mai lúc \(gio): \(kh.ten)." }
        return "Còn \(moTaPhut(ln.truoc)) nữa, lúc \(gio): \(kh.ten)."
    }

    static func moTaNhac(_ truoc: Int) -> String {
        if truoc == 0 { return "Đúng giờ" }
        if truoc % 1440 == 0 { return "\(truoc / 1440) ngày trước" }
        if truoc % 60 == 0 { return "\(truoc / 60) giờ trước" }
        return "\(moTaPhut(truoc)) trước"
    }

    /// "T2, T5 hằng tuần" - doc duoc ngay.
    static func moTaLapLai(_ kh: KeHoach) -> String {
        switch kh.lapLai {
        case .theoThu:
            let t: Set<Int> = kh.thuLap.isEmpty ? [thu(kh.ngay)] : kh.thuLap
            return t.count == 7 ? "Hằng ngày" : t.sorted().map { tenThuNgan[$0] }.joined(separator: ", ") + " hằng tuần"
        case .hangTuan: return tenThuNgan[thu(kh.ngay)] + " hằng tuần"
        default: return kh.lapLai.moTa
        }
    }

    /// Uu tien cao truoc, roi theo gio, roi theo ten.
    static func theoUuTien(_ ds: [KeHoach]) -> [KeHoach] {
        ds.sorted { ($0.uuTien.thuTu, $0.batDau, $0.ten) < ($1.uuTien.thuTu, $1.batDau, $1.ten) }
    }

    /// Ket thuc <= bat dau nghia la qua nua dem.
    static func thoiLuongGiua(_ batDau: Int, _ ketThuc: Int) -> Int {
        let d = ketThuc - batDau
        return d > 0 ? d : d + 1440
    }

    static func moTaPhut(_ phut: Int) -> String {
        if phut < 60 { return "\(phut) phút" }
        if phut % 60 == 0 { return "\(phut / 60) giờ" }
        return "\(phut / 60) giờ \(phut % 60) phút"
    }

    static func gioPhut(_ phut: Int) -> String {
        let p = ((phut % 1440) + 1440) % 1440
        return String(format: "%02d:%02d", p / 60, p % 60)
    }

    // MARK: Ngay (Howard Hinnant)

    static func chiaSan(_ a: Int, _ b: Int) -> Int { Int((Double(a) / Double(b)).rounded(.down)) }

    static func tuNgayThang(_ nam: Int, _ thang: Int, _ ngay: Int) -> Int {
        let y = thang <= 2 ? nam - 1 : nam
        let era = chiaSan(y, 400)
        let yoe = y - era * 400
        let mp = (thang + 9) % 12
        let doy = (153 * mp + 2) / 5 + ngay - 1
        let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy
        return era * 146097 + doe - 719468
    }

    static func ngayThang(_ soNgay: Int) -> (nam: Int, thang: Int, ngay: Int) {
        let z = soNgay + 719468
        let era = chiaSan(z, 146097)
        let doe = z - era * 146097
        let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365
        let doy = doe - (365 * yoe + yoe / 4 - yoe / 100)
        let mp = (5 * doy + 2) / 153
        let d = doy - (153 * mp + 2) / 5 + 1
        let m = mp < 10 ? mp + 3 : mp - 9
        return (yoe + era * 400 + (m <= 2 ? 1 : 0), m, d)
    }

    /// 0 = Thu Hai ... 6 = Chu Nhat.
    static func thu(_ soNgay: Int) -> Int { ((soNgay + 3) % 7 + 7) % 7 }
    static func dauTuan(_ soNgay: Int) -> Int { soNgay - thu(soNgay) }

    static func tenNgay(_ soNgay: Int, homNay: Int) -> String {
        let t = ngayThang(soNgay)
        let ten: String
        switch soNgay - homNay {
        case 0: ten = "Hôm nay"
        case 1: ten = "Ngày mai"
        case -1: ten = "Hôm qua"
        default: ten = tenThu[thu(soNgay)]
        }
        return "\(ten), \(t.ngay)/\(t.thang)"
    }
}

// MARK: - So lich tren may

final class SoLich: ObservableObject {

    private static let khoa = "flowy_lich"
    private static let khoaXong = "flowy_lich_xong"

    @Published private(set) var danhSach: [KeHoach] = []
    @Published private(set) var daXong: Set<String> = []

    init() {
        let d = UserDefaults.standard
        if let data = d.data(forKey: Self.khoa),
           let ds = try? JSONDecoder().decode([KeHoach].self, from: data) {
            danhSach = ds
        }
        daXong = Set(d.stringArray(forKey: Self.khoaXong) ?? [])
    }

    func luu(_ kh: KeHoach) {
        if let i = danhSach.firstIndex(where: { $0.id == kh.id }) { danhSach[i] = kh }
        else { danhSach.append(kh) }
        ghi()
    }

    func xoa(_ id: String) {
        danhSach.removeAll { $0.id == id }
        daXong = daXong.filter { !$0.hasPrefix(id + "|") }
        ghi()
    }

    func doiXong(_ id: String, ngay: Int) {
        let k = Lich.khoaXong(id, ngay)
        if daXong.contains(k) { daXong.remove(k) } else { daXong.insert(k) }
        ghi()
    }

    func tim(_ id: String?) -> KeHoach? { danhSach.first { $0.id == id } }

    /// Hoan tac xoa: dat lai ke hoach VA cac dau da xong cua no.
    func khoiPhuc(_ kh: KeHoach, daXong dx: Set<String>) {
        danhSach.append(kh)
        daXong.formUnion(dx)
        ghi()
    }

    private func ghi() {
        let homNay = Self.homNay()
        // Chi giu dau tich 60 ngay - khong phai lich su hanh vi.
        daXong = daXong.filter { (Int($0.split(separator: "|").last ?? "") ?? 0) >= homNay - 60 }
        let d = UserDefaults.standard
        if let data = try? JSONEncoder().encode(danhSach) { d.set(data, forKey: Self.khoa) }
        d.set(Array(daXong), forKey: Self.khoaXong)
        BaoLich.datLai(self)
    }

    // MARK: Doi gio dia phuong

    static func ngayCua(_ date: Date) -> Int {
        let c = Calendar.current.dateComponents([.year, .month, .day], from: date)
        return Lich.tuNgayThang(c.year ?? 1970, c.month ?? 1, c.day ?? 1)
    }

    static func homNay() -> Int { ngayCua(Date()) }

    static func bayGio() -> Int {
        let now = Date()
        let c = Calendar.current.dateComponents([.hour, .minute], from: now)
        return ngayCua(now) * 1440 + (c.hour ?? 0) * 60 + (c.minute ?? 0)
    }

    static func sangDate(_ phutTuyetDoi: Int) -> Date {
        let ngay = Lich.chiaSan(phutTuyetDoi, 1440)
        let phut = phutTuyetDoi - ngay * 1440
        let t = Lich.ngayThang(ngay)
        var c = DateComponents()
        c.year = t.nam; c.month = t.thang; c.day = t.ngay
        c.hour = phut / 60; c.minute = phut % 60
        return Calendar.current.date(from: c) ?? Date()
    }
}
