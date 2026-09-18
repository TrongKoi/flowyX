import Foundation

/// Loi nhac theo gio, do nguoi dung tu dat ten. Ban Swift cua `SoNhac.kt`.
///
/// Khong danh muc thuoc, khong tinh lieu, khong dem "ty le tuan thu",
/// khong canh bao bo lo - xem `adhd/nhacviec.py` ve ly do.
/// So nay KHONG BAO GIO len duong truyen.
final class SoNhac: ObservableObject {

    struct LoiNhac: Codable, Identifiable, Equatable {
        var id = UUID()
        var ten: String
        /// Phut tinh tu nua dem.
        var gio: Double
        var lapLai: Bool = true

        var cau: String { "Đã tới giờ: \(ten)." }
        var gioPhut: String { DocGio.hien(gio) }
    }

    static let minKyTu = 3
    static let cuaSoPhut = 30.0
    private static let khoa = "flowy_nhac"

    @Published private(set) var danhSach: [LoiNhac] = []

    /// Id da bao hom nay - chi de khong bao hai lan, KHONG luu xuong dia.
    private var daBao: Set<UUID> = []
    private var ngay = ""

    init() {
        if let data = UserDefaults.standard.data(forKey: Self.khoa),
           let d = try? JSONDecoder().decode([LoiNhac].self, from: data) {
            danhSach = d
        }
    }

    @discardableResult
    func them(ten: String, gio: Double) -> Bool {
        let t = ten.trimmingCharacters(in: .whitespacesAndNewlines)
        guard t.count >= Self.minKyTu, gio >= 0, gio < 1440 else { return false }
        danhSach.append(LoiNhac(ten: t, gio: gio))
        danhSach.sort { $0.gio < $1.gio }
        luu()
        return true
    }

    /// v4: loi nhac da gop vao Ke hoach - xoa sau khi chuyen xong.
    func xoaHet() {
        danhSach.removeAll()
        luu()
    }

    func xoa(_ id: UUID) {
        danhSach.removeAll { $0.id == id }
        daBao.remove(id)
        luu()
    }

    /// Loi nhac can bao ngay bay gio (khi app dang mo), hoac nil.
    func denHan(bayGio: Date = Date()) -> LoiNhac? {
        let cal = Calendar.current
        let c = cal.dateComponents([.year, .month, .day, .hour, .minute], from: bayGio)
        let homNay = "\(c.year ?? 0)-\(c.month ?? 0)-\(c.day ?? 0)"
        if homNay != ngay { ngay = homNay; daBao.removeAll() }
        let phut = Double((c.hour ?? 0) * 60 + (c.minute ?? 0))
        for ln in danhSach where !daBao.contains(ln.id) {
            let tre = phut - ln.gio
            if tre >= 0 && tre <= Self.cuaSoPhut {
                daBao.insert(ln.id)
                return ln
            }
        }
        return nil
    }

    private func luu() {
        if let data = try? JSONEncoder().encode(danhSach) {
            UserDefaults.standard.set(data, forKey: Self.khoa)
        }
    }
}
