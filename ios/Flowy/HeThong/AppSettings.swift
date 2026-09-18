import SwiftUI

/// Cai dat luu giua cac lan mo app. Ban Swift cua `AppSettings.kt`.
final class AppSettings: ObservableObject {

    enum CheDo: String, CaseIterable, Identifiable {
        case theoMay = "theo_may", sang, toi
        var id: String { rawValue }
        var nhan: String {
            switch self {
            case .theoMay: return "Theo máy"
            case .sang: return "Sáng"
            case .toi: return "Tối"
            }
        }
        var scheme: ColorScheme? {
            switch self {
            case .theoMay: return nil
            case .sang: return .light
            case .toi: return .dark
            }
        }
    }

    enum PhanHoi: String, CaseIterable, Identifiable {
        case caHai = "ca_hai", chiTieng = "chi_am_thanh", chiRung = "chi_rung"
        var id: String { rawValue }
        var nhan: String {
            switch self {
            case .caHai: return "Đọc lên và rung"
            case .chiTieng: return "Chỉ đọc lên"
            case .chiRung: return "Chỉ rung, không đọc"
            }
        }
    }

    /// ================================================================
    /// PHONG CHU (v5) - BA lua chon, khong phai mot cong tac
    /// ================================================================
    ///
    /// v4 chi co cong tac "font de doc" bat/tat Lexend. v5 mo ra ba
    /// phong vi khong co phong nao tot cho tat ca:
    ///
    ///   lexend  - mac dinh. Duoc thiet ke de giam tai doc, do rong
    ///             ky tu rong hon Inter mot chut.
    ///   andika  - cua SIL, cho nguoi kho doc: chu cai de phan biet
    ///             (a/o, b/d/p/q khac han nhau).
    ///   inter   - net trung tinh, gon, cho nguoi thay Lexend qua rong.
    ///   heThong - phong cua may, cho nguoi da chinh o Cai dat iOS.
    ///
    /// Atkinson Hyperlegible Next BI LOAI sau khi do bang fontTools:
    /// thieu 50 trong 74 ky tu tieng Viet co dau ma app can. OpenDyslexic
    /// cung vay. Chi tiet trong docs/GIAO_DIEN_V5.md muc 3.
    enum KieuChu: String, CaseIterable, Identifiable {
        case lexend, andika, inter, heThong = "he_thong"
        var id: String { rawValue }
        var nhan: String {
            switch self {
            case .lexend: return "Lexend"
            case .andika: return "Andika"
            case .inter: return "Inter"
            case .heThong: return "Của máy"
            }
        }
        /// Ten day du cua phong trong bundle. `nil` = dung phong he thong.
        ///
        /// Andika cua SIL KHONG co ban SemiBold - chi Regular va Bold. Goi
        /// "Andika-SemiBold" thi UIKit khong tim thay va lang le roi ve
        /// phong he thong, nen phai tra ve dung ten co that.
        func ten(dam: Bool) -> String? {
            switch self {
            case .lexend: return dam ? "Lexend-SemiBold" : "Lexend-Regular"
            case .andika: return dam ? "Andika-Bold" : "Andika-Regular"
            case .inter: return dam ? "Inter-SemiBold" : "Inter-Regular"
            case .heThong: return nil
            }
        }
    }

    private let d = UserDefaults.standard

    /// Dia chi laptop - CHI dung khi test va demo.
    @Published var serverUrl: String { didSet { d.set(serverUrl, forKey: "server_url") } }
    /// 0,7 .. 2,0. 1,0 = toc do mac dinh cua he thong.
    @Published var tocDoDoc: Double { didSet { d.set(tocDoDoc, forKey: "speech_rate") } }
    @Published var phanHoi: PhanHoi { didSet { d.set(phanHoi.rawValue, forKey: "feedback_mode") } }
    @Published var cheDo: CheDo { didSet { d.set(cheDo.rawValue, forKey: "giao_dien") } }
    /// Font Lexend. Mac dinh TAT - font he thong la thu nguoi dung quen.
    @Published var fontDeDoc: Bool { didSet { d.set(fontDeDoc, forKey: "font_de_doc") } }
    @Published var mucNhac: MucNhac { didSet { d.set(mucNhac.rawValue, forKey: "muc_nhac") } }

    // ---- v5 ----

    @Published var kieuChu: KieuChu { didSet { d.set(kieuChu.rawValue, forKey: "kieu_chu") } }
    /// 0,90 .. 1,15. Nhan len co chu cua he thong, KHONG thay the no:
    /// nguoi da phong to chu trong Cai dat iOS van duoc phong to them.
    @Published var coChu: Double { didSet { d.set(coChu, forKey: "co_chu") } }
    /// 0 tat, 1 nhe, 2 vua, 3 manh. Xem `Rung`.
    @Published var mucRung: Int { didSet { d.set(mucRung, forKey: "muc_rung") } }
    /// "" theo may, "vi", "en".
    @Published var ngonNgu: String { didSet { d.set(ngonNgu, forKey: "ngon_ngu") } }

    init() {
        serverUrl = d.string(forKey: "server_url") ?? "http://192.168.1.100:8765"
        let r = d.double(forKey: "speech_rate")
        tocDoDoc = r > 0 ? r : 1.2
        phanHoi = PhanHoi(rawValue: d.string(forKey: "feedback_mode") ?? "") ?? .caHai
        cheDo = CheDo(rawValue: d.string(forKey: "giao_dien") ?? "") ?? .theoMay
        // v4: Lexend MAC DINH BAT (nguoi dung van tat duoc).
        fontDeDoc = d.object(forKey: "font_de_doc") as? Bool ?? true
        mucNhac = MucNhac(rawValue: d.string(forKey: "muc_nhac") ?? "") ?? .vua

        // v5. `fontDeDoc` cu duoc doc mot lan de nguoi dung da tat Lexend
        // o ban v4 khong bi doi nguoc lai khi cap nhat app.
        if let k = d.string(forKey: "kieu_chu") {
            kieuChu = KieuChu(rawValue: k) ?? .lexend
        } else {
            kieuChu = (d.object(forKey: "font_de_doc") as? Bool ?? true) ? .lexend : .heThong
        }
        let c = d.double(forKey: "co_chu")
        coChu = c > 0 ? c : 1.0
        mucRung = d.object(forKey: "muc_rung") == nil ? 2 : d.integer(forKey: "muc_rung")
        ngonNgu = d.string(forKey: "ngon_ngu") ?? ""
    }

    var docLen: Bool { phanHoi != .chiRung }
    var rung: Bool { phanHoi != .chiTieng }
}
