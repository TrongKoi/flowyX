import Foundation

/// Nhat ky - cua nguoi dung, va app KHONG DIEN GIAI no.
/// Ban Swift cua `SoNhatKy.kt`: khong trung binh, khong xu huong, khong
/// bieu do. Chi sap theo thoi gian va in ra. KHONG len duong truyen.
final class SoNhatKy: ObservableObject {

    struct Muc: Codable, Identifiable, Equatable {
        var id = UUID()
        var luc: Date
        var noiDung: String
        /// Ho thay the nao, bang CHU cua ho - khong phai thang diem.
        var theNao: String?

        var dong: String {
            let f = DateFormatter()
            f.locale = Locale(identifier: "en_US_POSIX")
            f.dateFormat = "yyyy-MM-dd HH:mm"
            let gio = f.string(from: luc)
            if let theNao { return "\(gio)  [\(theNao)] \(noiDung)" }
            return "\(gio)  \(noiDung)"
        }
    }

    static let minKyTu = 2
    /// Gioi han RIENG TU: mot quyen so khong gioi han la mot ho so vo han.
    static let toiDa = 500
    private static let khoa = "flowy_nhat_ky"

    @Published private(set) var muc: [Muc] = []

    init() {
        if let data = UserDefaults.standard.data(forKey: Self.khoa),
           let d = try? JSONDecoder().decode([Muc].self, from: data) {
            muc = d
        }
    }

    @discardableResult
    func ghi(_ noiDung: String, theNao: String?) -> Bool {
        let nd = noiDung.trimmingCharacters(in: .whitespacesAndNewlines)
        guard nd.count >= Self.minKyTu else { return false }
        let tn = theNao?.trimmingCharacters(in: .whitespacesAndNewlines)
        muc.append(Muc(luc: Date(), noiDung: nd, theNao: (tn?.isEmpty ?? true) ? nil : tn))
        if muc.count > Self.toiDa { muc.removeFirst(muc.count - Self.toiDa) }
        luu()
        return true
    }

    /// Quyen xoa la mot phan cua quyen so huu.
    func xoa(_ id: UUID) {
        muc.removeAll { $0.id == id }
        luu()
    }

    /// Dat lai mot muc vua xoa - nut Hoan tac.
    func chen(_ m: Muc, tai i: Int) {
        muc.insert(m, at: min(max(i, 0), muc.count))
        luu()
    }

    @discardableResult
    func sua(_ id: UUID, noiDung: String, theNao: String?) -> Bool {
        let nd = noiDung.trimmingCharacters(in: .whitespacesAndNewlines)
        guard nd.count >= Self.minKyTu, let i = muc.firstIndex(where: { $0.id == id }) else { return false }
        let tn = theNao?.trimmingCharacters(in: .whitespacesAndNewlines)
        muc[i].noiDung = nd
        muc[i].theNao = (tn?.isEmpty ?? true) ? nil : tn
        luu()
        return true
    }

    func xuatVanBan() -> String {
        muc.isEmpty ? "" : muc.map(\.dong).joined(separator: "\n") + "\n"
    }

    private func luu() {
        if let data = try? JSONEncoder().encode(muc) {
            UserDefaults.standard.set(data, forKey: Self.khoa)
        }
    }
}
