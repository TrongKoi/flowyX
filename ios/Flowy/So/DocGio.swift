import Foundation

/// Chu nguoi dung go -> phut trong ngay. Ban Swift cua `DocGio.kt`.
///
/// Tren iOS o nhap gio chinh la `DatePicker`, nen lop nay chu yeu dung de
/// doc lai chuoi "HH:MM" laptop gui ve. Nhan "14:00", "1400", "930",
/// "14h30", "14.30".
enum DocGio {

    static func doc(_ s: String?) -> Double? {
        guard let s else { return nil }
        let t = s.trimmingCharacters(in: .whitespaces).lowercased()
        if t.isEmpty { return nil }

        // Co dau phan cach.
        let mau = #"^(\d{1,2})\s*[:.hg ]\s*(\d{0,2})\s*(p|ph|phut|phút)?$"#
        if let re = try? NSRegularExpression(pattern: mau),
           let m = re.firstMatch(in: t, range: NSRange(t.startIndex..., in: t)),
           let rGio = Range(m.range(at: 1), in: t) {
            let g = Int(t[rGio]) ?? -1
            let chuoiPhut = Range(m.range(at: 2), in: t).map { String(t[$0]) } ?? ""
            // "14:5" co the la 14:05 hoac 14:50 - khong doan.
            if chuoiPhut.count == 1 { return nil }
            return hopLe(g, Int(chuoiPhut) ?? 0)
        }

        guard !t.isEmpty, t.unicodeScalars.allSatisfy({ ("0"..."9").contains($0) }) else {
            return nil
        }
        let so = Array(t)
        switch so.count {
        case 1, 2: return hopLe(Int(t) ?? -1, 0)
        case 3: return hopLe(Int(String(so[0])) ?? -1, Int(String(so[1...])) ?? -1)
        case 4: return hopLe(Int(String(so[0...1])) ?? -1, Int(String(so[2...])) ?? -1)
        default: return nil
        }
    }

    static func hien(_ phut: Double) -> String {
        String(format: "%02d:%02d", Int(phut) / 60, Int(phut) % 60)
    }

    private static func hopLe(_ g: Int, _ p: Int) -> Double? {
        (0...23).contains(g) && (0...59).contains(p) ? Double(g * 60 + p) : nil
    }
}
