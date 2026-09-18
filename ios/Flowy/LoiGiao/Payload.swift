import Foundation

// MARK: - Hop dong JSON voi laptop
//
// Ban Swift cua `android/.../Payload.kt`. Ten truong phai KHOP
// `adc_wayfinding/wayfinding/loi_chung/bridge.py` - co bai test
// `tests/loi_chung/test_hop_dong.py` khoa danh sach ten ben Python.
//
// Sua ten o day ma khong sua ben Python thi app KHONG sap - no chi lang
// le mat truong do. Nen moi ten nam trong CodingKeys, doc duoc bang mat.

enum Lenh {
    static let batDau = "bat_dau"
    static let xongBuoc = "xong_buoc"
    static let tamDung = "tam_dung"
    static let tiepTuc = "tiep_tuc"
    static let ketThuc = "ket_thuc"
    static let viecMoi = "viec_moi"
}

enum MucNhac: String, CaseIterable, Identifiable {
    case it, vua, nhieu
    var id: String { rawValue }
    var nhan: String {
        switch self {
        case .it: return "Ít"
        case .vua: return "Vừa"
        case .nhieu: return "Nhiều"
        }
    }
}

/// Mot lan do trong so thoi luong, dang JSON ma Python doc.
struct LanDoJSON: Codable, Equatable {
    var uoc: Double?
    var that: Double
}

/// Goi tin dien thoai gui len.
///
/// Truong nil KHONG duoc ghi ra (encodeIfPresent) - dung nhu ban Kotlin.
struct PhoneUpdate: Encodable {
    var t: Double
    var trenManHinh: Bool
    var chamNhanVat: Bool = false
    var voice: String? = nil
    var lenh: String? = nil
    var noiDung: String? = nil
    var battery: Double? = nil
    /// Lich su cua DUNG MOT viec dang lam. Khong bao gio ca so.
    var lichSu: [String: [LanDoJSON]]? = nil
    /// Phut tinh tu nua dem. Am = bo gio hen.
    var gioHen: Double? = nil
    var uocPhut: Double? = nil
    var mucNhac: String? = nil

    enum CodingKeys: String, CodingKey {
        case t
        case trenManHinh = "tren_man_hinh"
        case chamNhanVat = "cham_nhan_vat"
        case voice, lenh
        case noiDung = "noi_dung"
        case battery
        case lichSu = "lich_su"
        case gioHen = "gio_hen"
        case uocPhut = "uoc_phut"
        case mucNhac = "muc_nhac"
    }
}

/// Cau tra loi cua laptop.
///
/// Doc LONG TAY: truong thieu hoac sai kieu thi lay mac dinh, khong nem
/// loi. Mot goi tin hong khong duoc phep dung ca phien lam viec.
struct Reply: Decodable, Equatable {
    var say: String? = nil
    var haptic: String? = nil
    var am: String? = nil
    var ban: String = "binh_thuong"
    var tuThe: Int = 0
    var hoi: String? = nil
    var listen: Bool = false
    var conLaiGiay: Double? = nil
    var tongGiay: Double? = nil
    var nhipMs: Int = 500
    var xongPhien: Bool = false
    var tenViec: String? = nil

    // giao dien v2
    var viecGi: String? = nil
    var khiNao: String? = nil
    var oDau: String? = nil
    var cacBuoc: [String] = []
    var chiSoBuoc: Int = 0
    var trongPhien: Bool = false
    var tamDung: Bool = false
    var daLamGiay: Double? = nil
    var gioHen: String? = nil
    var uocPhut: Double? = nil
    var goiYPhut: Double? = nil
    var mucNhac: String = "vua"

    init() {}

    enum CodingKeys: String, CodingKey {
        case say, haptic, am, ban, hoi, listen
        case tuThe = "tu_the"
        case conLaiGiay = "con_lai_giay"
        case tongGiay = "tong_giay"
        case nhipMs = "nhip_ms"
        case xongPhien = "xong_phien"
        case tenViec = "ten_viec"
        case viecGi = "viec_gi"
        case khiNao = "khi_nao"
        case oDau = "o_dau"
        case cacBuoc = "cac_buoc"
        case chiSoBuoc = "chi_so_buoc"
        case trongPhien = "trong_phien"
        case tamDung = "tam_dung"
        case daLamGiay = "da_lam_giay"
        case gioHen = "gio_hen"
        case uocPhut = "uoc_phut"
        case goiYPhut = "goi_y_phut"
        case mucNhac = "muc_nhac"
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        func s(_ k: CodingKeys) -> String? { (try? c.decodeIfPresent(String.self, forKey: k)) ?? nil }
        func d(_ k: CodingKeys) -> Double? { (try? c.decodeIfPresent(Double.self, forKey: k)) ?? nil }
        func i(_ k: CodingKeys) -> Int? {
            if let v = (try? c.decodeIfPresent(Int.self, forKey: k)) ?? nil { return v }
            return d(k).map { Int($0) }
        }
        func b(_ k: CodingKeys) -> Bool { ((try? c.decodeIfPresent(Bool.self, forKey: k)) ?? nil) ?? false }

        say = s(.say); haptic = s(.haptic); am = s(.am)
        ban = s(.ban) ?? "binh_thuong"
        tuThe = i(.tuThe) ?? 0
        hoi = s(.hoi); listen = b(.listen)
        conLaiGiay = d(.conLaiGiay); tongGiay = d(.tongGiay)
        nhipMs = i(.nhipMs) ?? 500
        xongPhien = b(.xongPhien); tenViec = s(.tenViec)
        viecGi = s(.viecGi); khiNao = s(.khiNao); oDau = s(.oDau)
        cacBuoc = ((try? c.decodeIfPresent([String].self, forKey: .cacBuoc)) ?? nil) ?? []
        chiSoBuoc = i(.chiSoBuoc) ?? 0
        trongPhien = b(.trongPhien); tamDung = b(.tamDung)
        daLamGiay = d(.daLamGiay); gioHen = s(.gioHen)
        uocPhut = d(.uocPhut); goiYPhut = d(.goiYPhut)
        mucNhac = s(.mucNhac) ?? "vua"
    }
}
