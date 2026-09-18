import Foundation

/// SO BIEN BAN - khop Android `SoBienBan.kt`.
/// Hai duong vao: ghi tay, hoac nhap `_minutes.json` cua Meety.
/// Mot duong ra: Word hai ban (`khoiDocx`).
final class SoBienBan: ObservableObject {
    struct BienBan: Codable, Identifiable, Equatable {
        var id = UUID()
        var luc: Date
        var ten: String
        var daChot: String = ""
        var viec: [String] = []
        var tomTat: [String] = []
        var nguoiDu: [String] = []
        var cauHoi: [String] = []
        var thoiLuongPhut: Int?
        var nguon: String = "tay"

        var ngayDoc: String {
            let f = DateFormatter(); f.locale = Locale(identifier: "vi_VN"); f.dateFormat = "dd/MM · HH:mm"
            return f.string(from: luc)
        }
    }

    static let minKyTu = 3
    private static let khoa = "flowy_bien_ban"
    @Published private(set) var danhSach: [BienBan] = []

    init() {
        if let data = UserDefaults.standard.data(forKey: Self.khoa),
           let d = try? JSONDecoder().decode([BienBan].self, from: data) { danhSach = d }
    }

    @discardableResult
    func them(_ b: BienBan) -> Bool {
        var b = b
        b.ten = b.ten.trimmingCharacters(in: .whitespacesAndNewlines)
        guard b.ten.count >= Self.minKyTu else { return false }
        let sach: ([String]) -> [String] = { $0.map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty } }
        b.viec = sach(b.viec); b.tomTat = sach(b.tomTat); b.nguoiDu = sach(b.nguoiDu); b.cauHoi = sach(b.cauHoi)
        danhSach.append(b)
        luu(); return true
    }

    func xoa(_ id: UUID) -> (BienBan, Int)? {
        guard let i = danhSach.firstIndex(where: { $0.id == id }) else { return nil }
        let b = danhSach.remove(at: i); luu(); return (b, i)
    }

    func chen(_ b: BienBan, tai i: Int) { danhSach.insert(b, at: min(max(i, 0), danhSach.count)); luu() }

    private func luu() {
        if let data = try? JSONEncoder().encode(danhSach) { UserDefaults.standard.set(data, forKey: Self.khoa) }
    }

    /// Doc `StructuredMinutes` cua Meety. Bo quyet dinh da bi thay the.
    static func tuMeety(_ data: Data) -> BienBan? {
        guard let o = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let meta = o["meta"] as? [String: Any],
              let ten = (meta["meeting_title"] as? String)?.trimmingCharacters(in: .whitespaces), !ten.isEmpty
        else { return nil }
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; f.locale = Locale(identifier: "en_US_POSIX")
        let luc = (meta["date"] as? String).flatMap { f.date(from: $0) } ?? Date()
        let nguoi = (meta["attendees"] as? [[String: Any]] ?? []).compactMap { $0["display_name"] as? String }
        let chot = (o["decisions"] as? [[String: Any]] ?? []).compactMap { d -> String? in
            if let s = d["superseded_by"] as? String, !s.isEmpty { return nil }
            if ["rejected", "superseded", "reverted"].contains(d["status"] as? String ?? "") { return nil }
            return d["statement"] as? String
        }
        let viec = (o["action_items"] as? [[String: Any]] ?? []).compactMap { v -> String? in
            guard let task = v["task"] as? String, !task.isEmpty else { return nil }
            var s = ""
            if let a = v["assignee"] as? String, !a.isEmpty { s += "\(a): " }
            s += task
            if let h = (v["due_date"] as? String) ?? (v["due_raw"] as? String), !h.isEmpty { s += " (hạn \(h))" }
            return s
        }
        let hoi = (o["open_questions"] as? [[String: Any]] ?? []).compactMap { $0["question"] as? String }
        let tldr = ((o["executive_summary"] as? [String: Any])?["tldr"] as? [String]) ?? []
        let tl = meta["duration_minutes"] as? Int
        return BienBan(luc: luc, ten: ten, daChot: chot.joined(separator: "\n"), viec: viec, tomTat: tldr,
                       nguoiDu: nguoi, cauHoi: hoi, thoiLuongPhut: (tl ?? 0) > 0 ? tl : nil, nguon: "meety")
    }

    /// Noi dung Word: viec can LAM truoc, dieu da NOI sau. Cung thu tu voi Android.
    static func khoiDocx(_ b: BienBan) -> [DocxViet.Khoi] {
        var k: [DocxViet.Khoi] = [.tieuDe(b.ten)]
        let f = DateFormatter(); f.dateFormat = "dd/MM/yyyy"
        var info = ["Ngày \(f.string(from: b.luc))"]
        if let t = b.thoiLuongPhut { info.append("\(t) phút") }
        if !b.nguoiDu.isEmpty { info.append("Người dự: " + b.nguoiDu.joined(separator: ", ")) }
        k.append(.chuNho(info.joined(separator: "  ·  ")))
        if !b.tomTat.isEmpty { k.append(.noiBat("Tóm tắt", b.tomTat)) }
        if !b.viec.isEmpty { k.append(.noiBat("Việc cần làm", b.viec)) }
        let chot = b.daChot.components(separatedBy: "\n").map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
        if !chot.isEmpty { k.append(.muc("Đã chốt")); k += chot.map { .gachDau($0) } }
        if !b.cauHoi.isEmpty { k.append(.muc("Câu hỏi còn mở")); k += b.cauHoi.map { .gachDau($0) } }
        k.append(.chuNho(b.nguon == "meety" ? "Tạo từ Meety qua FlowyX" : "Ghi tay trên FlowyX"))
        return k
    }
}
