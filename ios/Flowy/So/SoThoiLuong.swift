import Foundation

/// So thoi luong - ban Swift cua `SoThoiLuong.kt` / `adhd/thoiluong.py`.
///
/// So nay nam TREN MAY. Chi lich su cua DUNG viec dang lam duoc gui len
/// laptop, gui roi thoi - xem bang o dau `bridge.py`.
final class SoThoiLuong {

    static let soLanXet = 5
    private static let khoa = "flowy_thoi_luong"

    private(set) var banGhi: [String: [LanDoJSON]] = [:]

    init() {
        if let data = UserDefaults.standard.data(forKey: Self.khoa),
           let d = try? JSONDecoder().decode([String: [LanDoJSON]].self, from: data) {
            banGhi = d.filter { !$0.value.isEmpty }
        }
    }

    func ghi(_ tenViec: String, thatPhut: Double, uocPhut: Double?) {
        guard !tenViec.trimmingCharacters(in: .whitespaces).isEmpty, thatPhut > 0 else { return }
        banGhi[tenViec, default: []].append(LanDoJSON(uoc: uocPhut, that: thatPhut))
        luu()
    }

    /// Trung vi cac lan gan nhat. Trung vi, KHONG phai trung binh.
    func uocLuong(_ tenViec: String) -> Double? {
        guard let lan = banGhi[tenViec], !lan.isEmpty else { return nil }
        let x = lan.suffix(Self.soLanXet).map(\.that).sorted()
        let g = x.count / 2
        return x.count % 2 == 1 ? x[g] : (x[g - 1] + x[g]) / 2
    }

    /// Dung phan cua MOT viec, de gui len.
    func motViec(_ tenViec: String) -> [String: [LanDoJSON]]? {
        guard let lan = banGhi[tenViec] else { return nil }
        return [tenViec: lan]
    }

    private func luu() {
        if let data = try? JSONEncoder().encode(banGhi) {
            UserDefaults.standard.set(data, forKey: Self.khoa)
        }
    }
}
