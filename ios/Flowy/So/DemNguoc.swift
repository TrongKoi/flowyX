import Foundation

/// DONG HO DEM NGUOC - khop Android `DemNguoc.kt`.
///
/// Chi dem NGUOC, 1...120 phut. Luu MOC KET THUC (Date), khong dem ngam:
/// app bi dong, may khoa man hinh - so con lai luon tinh lai tu moc.
struct DemNguoc: Codable, Equatable {
    static let toiDaPhut = 120
    static let nhanh = [5, 10, 15, 25, 45, 60, 90, 120]

    var tongGiay: Double = 25 * 60
    var ketThucLuc: Date?
    var conLaiKhiDung: Double?

    var dangChay: Bool { ketThucLuc != nil }
    var dangDung: Bool { conLaiKhiDung != nil }
    var chuaBatDau: Bool { !dangChay && !dangDung }

    func conLai(_ bay: Date = Date()) -> Double {
        if let k = ketThucLuc { return max(0, k.timeIntervalSince(bay)) }
        if let c = conLaiKhiDung { return c }
        return tongGiay
    }
    func tyLe(_ bay: Date = Date()) -> Double { tongGiay <= 0 ? 0 : min(1, max(0, conLai(bay) / tongGiay)) }
    func daHet(_ bay: Date = Date()) -> Bool { dangChay && conLai(bay) == 0 }
    func daLamPhut(_ bay: Date = Date()) -> Double { (tongGiay - conLai(bay)) / 60 }

    static func kep(_ phut: Int) -> Int { min(max(phut, 1), toiDaPhut) }

    func datThoiLuong(_ phut: Int) -> DemNguoc {
        guard chuaBatDau else { return self }
        var d = self; d.tongGiay = Double(Self.kep(phut) * 60); return d
    }
    func batDau(_ bay: Date = Date()) -> DemNguoc {
        var d = self
        if dangChay { return d }
        if let c = conLaiKhiDung { d.ketThucLuc = bay.addingTimeInterval(c); d.conLaiKhiDung = nil }
        else { d.ketThucLuc = bay.addingTimeInterval(tongGiay) }
        return d
    }
    func tamDung(_ bay: Date = Date()) -> DemNguoc {
        guard dangChay else { return self }
        var d = self; d.conLaiKhiDung = conLai(bay); d.ketThucLuc = nil; return d
    }
    func datLai() -> DemNguoc { DemNguoc(tongGiay: tongGiay) }
    func themPhut(_ phut: Int, _ bay: Date = Date()) -> DemNguoc {
        if chuaBatDau { return datThoiLuong(Int(tongGiay / 60) + phut) }
        let con = conLai(bay)
        let moi = min(con + Double(phut * 60), Double(Self.toiDaPhut * 60))
        var d = self
        d.tongGiay += moi - con
        if let k = ketThucLuc { d.ketThucLuc = k.addingTimeInterval(moi - con) } else { d.conLaiKhiDung = moi }
        return d
    }

    /// "mm:ss" duoi mot gio, "h:mm:ss" tu mot gio. Lam tron LEN.
    static func dinhDang(_ giay: Double) -> String {
        let g = Int(giay.rounded(.up))
        let h = g / 3600, m = (g % 3600) / 60, s = g % 60
        return h > 0 ? String(format: "%d:%02d:%02d", h, m, s) : String(format: "%02d:%02d", m, s)
    }
}
