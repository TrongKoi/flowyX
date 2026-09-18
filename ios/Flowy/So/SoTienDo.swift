import Foundation

/// SO TIEN DO - khop Android `SoTienDo.kt`.
///
/// Dem so viec xong theo ngay + ghi NGAY MO APP (tu diem danh, v4). Chuoi
/// ngay tinh ca ngay chi mo app; khong dut khi hom nay chua lam gi.
final class SoTienDo: ObservableObject {
    static let giuNgay = 400
    private static let khoaViec = "flowy_tien_do_theo_ngay"
    private static let khoaMo = "flowy_tien_do_ngay_mo"

    @Published private(set) var theoNgay: [String: Int] = [:]
    @Published private(set) var ngayMo: Set<String> = []

    init() {
        let d = UserDefaults.standard
        theoNgay = (d.dictionary(forKey: Self.khoaViec) as? [String: Int]) ?? [:]
        ngayMo = Set(d.stringArray(forKey: Self.khoaMo) ?? [])
    }

    /// Cho test: khong doc UserDefaults.
    init(theoNgay: [String: Int], ngayMo: Set<String>) {
        self.theoNgay = theoNgay; self.ngayMo = ngayMo
    }

    func ghi(_ ngay: String = SoTienDo.homNay()) {
        theoNgay[ngay, default: 0] += 1
        luu()
    }

    /// Goi moi khi app hien len. Goi nhieu lan trong ngay khong sao.
    @discardableResult
    func diemDanh(_ ngay: String = SoTienDo.homNay()) -> Bool {
        let moi = ngayMo.insert(ngay).inserted
        if moi { luu() }
        return moi
    }

    func soViec(_ ngay: String) -> Int { theoNgay[ngay] ?? 0 }
    var tongSoViec: Int { theoNgay.values.reduce(0, +) }
    func coHoatDong(_ ngay: String) -> Bool { soViec(ngay) > 0 || ngayMo.contains(ngay) }

    func chuoi(tu ngay: Date = Date()) -> Int {
        var c = ngay
        if !coHoatDong(Self.ngayCua(c)) {
            c = Self.lui(c)
            if !coHoatDong(Self.ngayCua(c)) { return 0 }
        }
        var n = 0
        while coHoatDong(Self.ngayCua(c)) { n += 1; c = Self.lui(c) }
        return n
    }

    /// Bay ngay ket thuc o hom nay: (nhan thu, co hoat dong).
    func tuan(tu ngay: Date = Date()) -> [(String, Bool)] {
        let ten = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"]
        return (0..<7).reversed().map { i in
            let d = Calendar.current.date(byAdding: .day, value: -i, to: ngay) ?? ngay
            return (ten[Calendar.current.component(.weekday, from: d) - 1], coHoatDong(Self.ngayCua(d)))
        }
    }

    private func luu() {
        if theoNgay.count > Self.giuNgay {
            for k in theoNgay.keys.sorted().prefix(theoNgay.count - Self.giuNgay) { theoNgay[k] = nil }
        }
        if ngayMo.count > Self.giuNgay {
            ngayMo.subtract(ngayMo.sorted().prefix(ngayMo.count - Self.giuNgay))
        }
        let d = UserDefaults.standard
        d.set(theoNgay, forKey: Self.khoaViec)
        d.set(Array(ngayMo), forKey: Self.khoaMo)
    }

    static func ngayCua(_ d: Date) -> String {
        let c = Calendar.current.dateComponents([.year, .month, .day], from: d)
        return String(format: "%04d-%02d-%02d", c.year ?? 1970, c.month ?? 1, c.day ?? 1)
    }
    static func homNay() -> String { ngayCua(Date()) }
    private static func lui(_ d: Date) -> Date { Calendar.current.date(byAdding: .day, value: -1, to: d) ?? d }
}
