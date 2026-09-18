import SwiftUI
import UIKit

// MARK: - Bang mau giao dien v2, huong C
//
// CUNG ma mau voi `android/app/src/main/res/values(-night)/colors.xml`.
// Doi mot mau thi doi ca hai ben. Da do tuong phan WCAG - xem file Android.

extension UIColor {
    convenience init(hex: UInt32) {
        self.init(red: CGFloat((hex >> 16) & 0xFF) / 255,
                  green: CGFloat((hex >> 8) & 0xFF) / 255,
                  blue: CGFloat(hex & 0xFF) / 255, alpha: 1)
    }
}

extension Color {
    /// Mau tu doi theo sang/toi.
    static func hai(_ sang: UInt32, _ toi: UInt32) -> Color {
        Color(UIColor { tc in
            tc.userInterfaceStyle == .dark ? UIColor(hex: toi) : UIColor(hex: sang)
        })
    }
}

/// ====================================================================
/// BANG MAU FlowyX v5 - KHOP TUNG MA voi Android
/// ====================================================================
///
/// Nguon su that la `android/app/src/main/res/values/colors.xml` va
/// `values-night/colors.xml`. Doi o mot ben thi doi ca ben kia; ly do
/// tung quyet dinh nam o docs/GIAO_DIEN_V5.md muc 1.
///
/// BAN SANG (giu nguyen tu v4): vang va cam la MAT NEN, navy la MUC.
///
/// BAN TOI - "MUC DEM", viet lai han o v5:
///
/// Ban v4 chi la ban sang bi lam toi di: van mot nen gan den (#17161F)
/// voi vang cam giu nguyen vai tro. Ket qua la mot giao dien khong co
/// tinh cach rieng, va mau nhan vang van doi cho kieu nen sang.
///
/// v5 DOI VAI TRO chu khong chi doi do sang:
///
///   · NEN thanh xanh muc (#121320) - khong phai xam trung tinh. The
///     noi len bang cach xanh HON nen (#1B1C2B), khong phai sang hon.
///   · MAU TUONG TAC thanh tim nhat (#A99BF0). O ban sang, mau tuong
///     tac la navy tram; o nen muc, navy bien mat, nen no nhuong cho
///     tim - cung ho mau nhung song duoc tren nen toi.
///   · VANG giam bao hoa va toi lai (#F2B742): vang nguyen ban #FFD400
///     tren nen muc cho do choi 14:1, cham vao la nhuc mat luc dem.
///   · Mau khang dinh / phu dinh KHONG dao: xanh va do o ban toi sang
///     hon han ban sang (#5FBF98, #E2705E), vi mau bao hoa cao tren nen
///     toi bi nhoe vien ra.
///
/// Tat ca deu da do tuong phan WCAG - xem bang trong GIAO_DIEN_V5.md.
enum Mau {
    static let nen = Color.hai(0xFEF4EF, 0x121320)
    static let the = Color.hai(0xFFFFFF, 0x1B1C2B)
    static let the2 = Color.hai(0xFFFFFF, 0x24263A)
    static let the3 = Color.hai(0xFFFFFF, 0x2D3050)
    static let vien = Color.hai(0xEDE4DD, 0x3A3D58)
    static let chu = Color.hai(0x2D2A42, 0xE8E6F0)
    static let chuPhu = Color.hai(0x8A8798, 0xA3A1B8)
    /// Mau tuong tac: navy tram o ban sang, tim nhat o ban toi.
    static let chuLienKet = Color.hai(0x57536E, 0xA99BF0)
    static let nhan = Color.hai(0xFFD400, 0xF2B742)
    static let chuTrenNhan = Color.hai(0x2D2A42, 0x17161F)
    static let nhanNhat = Color.hai(0xFFF8E1, 0x2B2517)
    static let nhanVien = Color.hai(0xF5DE8A, 0x6B5726)
    static let cam = Color.hai(0xF58A07, 0xF0844A)
    static let camNhat = Color.hai(0xFFF1E2, 0x2E2118)
    static let dhConNhieu = Color.hai(0x2D2A42, 0x8F8CE0)
    static let dhSapDen = Color.hai(0xFFD400, 0xF2B742)
    static let dhDiNgay = Color.hai(0xF58A07, 0xF0844A)
    static let dhRanh = Color.hai(0xE8E0D8, 0x2A2C42)
    static let uuCao = Color.hai(0xF58A07, 0xF0844A)
    static let uuVua = Color.hai(0xFFD400, 0xF2B742)
    static let uuThap = Color.hai(0xC9C2D6, 0x6C6A85)
    static let tabPill = Color.hai(0xFFF1C2, 0x332F52)
    static let tabChon = Color.hai(0x2D2A42, 0xE8E6F0)

    /// Ghim (vuot phai). Tim, de khong lan voi vang/cam cua thuong hieu.
    static let ghim = Color.hai(0x7C6BD8, 0xA99BF0)
    static let ghimNhat = Color.hai(0xEFECFC, 0x262445)
    /// Xong (vuot trai, nut xanh) va Xoa (vuot trai, nut do).
    static let xanhXong = Color.hai(0x2E7D62, 0x5FBF98)
    static let doXoa = Color.hai(0xC0392B, 0xE2705E)

    static let buoc: [Color] = [
        .hai(0xFFF8E1, 0x2A2618), .hai(0xFFF1E2, 0x2E2319), .hai(0xF3EFF6, 0x242641),
        .hai(0xFDF2EC, 0x2A2340), .hai(0xF6F0E6, 0x26273A),
    ]
    static func uuTien(_ u: UuTien) -> Color {
        switch u { case .cao: return uuCao; case .vua: return uuVua; case .thap: return uuThap }
    }

    /// Tam kinh cua thanh tab - CO do trong, nen phai dung UIColor rieng.
    /// Khop `kinh_nen` / `kinh_sang` ben Android.
    static func kinhNen(_ toi: Bool) -> Color {
        toi ? Color(red: 0x1B / 255.0, green: 0x1C / 255.0, blue: 0x2B / 255.0).opacity(0.92)
            : Color(red: 0xFD / 255.0, green: 0xFB / 255.0, blue: 0xF6 / 255.0).opacity(0.94)
    }
    static func kinhSang(_ toi: Bool) -> Color {
        Color.white.opacity(toi ? 0.12 : 0.70)
    }
}

/// ====================================================================
/// RUNG - BON NAC, KHOP `Rung.kt` ben Android
/// ====================================================================
///
/// v4 co ba muc co dinh va mot cong tac bat/tat. v5 doi thanh BON NAC
/// nguoi dung tu keo trong Cai dat (0 tat, 1 nhe, 2 vua, 3 manh), vi
/// nguong cam nhan rung chenh nhau rat nhieu giua nguoi va giua may -
/// cai "vua" tren iPhone 15 la cai gan nhu khong thay tren mot may cu.
///
/// Khac Android o CACH thuc hien, giong o KET QUA:
///
///   Android dat thang bien do 0-255 cho `VibrationEffect`.
///   iOS khong cho dat bien do o API cong khai, nen bon nac anh xa sang
///   bon kieu phan hoi co san (.soft / .light / .medium / .rigid) -
///   day la cach duy nhat lay duoc bon muc manh khac nhau ma khong dung
///   Core Haptics (Core Haptics can mot engine phai giu song, ton pin,
///   va khong chay tren iPhone 8 tro xuong).
enum Rung {

    /// 0 tat, 1 nhe, 2 vua, 3 manh. Doc thang tu UserDefaults de dung
    /// duoc ca o noi khong co EnvironmentObject.
    private static var nac: Int {
        let d = UserDefaults.standard
        return d.object(forKey: "muc_rung") == nil ? 2 : d.integer(forKey: "muc_rung")
    }

    private static var tatVCaiDat: Bool {
        UserDefaults.standard.string(forKey: "feedback_mode") == AppSettings.PhanHoi.chiTieng.rawValue
    }

    private static func kieu(_ nangThem: Int) -> UIImpactFeedbackGenerator.FeedbackStyle? {
        switch min(3, max(0, nac + nangThem)) {
        case 0: return nil
        case 1: return .soft
        case 2: return .light
        default: return .medium
        }
    }

    /// Cham chip, doi tab, mo mot man hinh.
    static func nhe() { rung(0) }
    /// Qua mot moc khi xoay dong ho, qua mot tab khi keo thanh tab.
    static func tich() {
        guard !tatVCaiDat, nac > 0 else { return }
        UISelectionFeedbackGenerator().selectionChanged()
    }
    /// Xong viec, luu, het gio, vuot xoa - nac manh hon mot bac.
    static func xong() {
        guard !tatVCaiDat, nac > 0 else { return }
        UINotificationFeedbackGenerator().notificationOccurred(.success)
    }

    static func rung(_ nangThem: Int = 0) {
        guard !tatVCaiDat, let k = kieu(nangThem) else { return }
        UIImpactFeedbackGenerator(style: k).impactOccurred()
    }

    /// Rung MANH DAN khi keo vanh dong ho: cang gan dinh cang ro.
    /// `tyLe` 0...1. Khop `Rung.luyTien` ben Android.
    static func luyTien(_ tyLe: Double) {
        guard !tatVCaiDat, nac > 0, let k = kieu(0) else { return }
        let g = UIImpactFeedbackGenerator(style: k)
        // 0,4 ... 1,0: duoi 0,4 thi khong con la mot cu cham ma la mot
        // tieng u, nguoi dung khong dem duoc nua.
        g.impactOccurred(intensity: CGFloat(0.4 + 0.6 * min(1, max(0, tyLe))))
    }

    /// Chuoi rung an mung khi het phien tap trung. Hai nhip, khong phai
    /// mot hoi dai - mot hoi dai o tui quan doc nhu mot cuoc goi den.
    static func anMung() {
        guard !tatVCaiDat, nac > 0 else { return }
        rung(1)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.12) { rung(1) }
    }
}

struct ChuModifier: ViewModifier {
    @EnvironmentObject var settings: AppSettings
    /// Doc de SwiftUI ve lai khi nguoi dung doi co chu trong iOS.
    @Environment(\.dynamicTypeSize) private var coChuHeThong
    let co: CGFloat
    let dam: Bool
    let theo: Font.TextStyle

    /// Co chu cuoi cung = co goc x he so nguoi dung keo trong Cai dat.
    ///
    /// NHAN chu khong THAY THE co chu he thong: `relativeTo` / UIFontMetrics
    /// van lam viec cua no, nen nguoi da phong to chu trong Cai dat iOS duoc
    /// phong to THEM, chu khong bi ep ve mot co co dinh.
    @ViewBuilder
    func body(content: Content) -> some View {
        let coCuoi = co * CGFloat(settings.coChu)
        if let ten = settings.kieuChu.ten(dam: dam) {
            content.font(.custom(ten, size: coCuoi, relativeTo: theo))
        } else {
            // Co chu co dinh nhung van CO GIAN theo cai dat Co chu cua iOS.
            let goc = UIFont.systemFont(ofSize: coCuoi, weight: dam ? .semibold : .regular)
            content.font(Font(UIFontMetrics(forTextStyle: Self.kieuUIKit(theo)).scaledFont(for: goc)))
        }
    }

    private static func kieuUIKit(_ t: Font.TextStyle) -> UIFont.TextStyle {
        switch t {
        case .largeTitle: return .largeTitle
        case .title: return .title1
        case .title2: return .title2
        case .title3: return .title3
        case .headline: return .headline
        case .subheadline: return .subheadline
        case .callout: return .callout
        case .footnote: return .footnote
        case .caption: return .caption1
        case .caption2: return .caption2
        default: return .body
        }
    }
}

extension View {
    func chu(_ co: CGFloat, dam: Bool = false, theo: Font.TextStyle = .body) -> some View {
        modifier(ChuModifier(co: co, dam: dam, theo: theo))
    }

    /// The bo goc - nen cua moi khoi.
    func the(_ dem: CGFloat = 16) -> some View {
        self.padding(dem)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 20, style: .continuous).fill(Mau.the))
            .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous)
                .stroke(Mau.vien, lineWidth: 1))
    }
}

/// Nut chinh 56 pt. Mot man hinh chi co MOT nut nay.
struct NutChinhStyle: ButtonStyle {
    @Environment(\.isEnabled) var bat
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .frame(maxWidth: .infinity, minHeight: 56)
            .foregroundColor(bat ? Mau.chuTrenNhan : Mau.chuPhu)
            .background(RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(bat ? Mau.nhan : Mau.vien))
            .opacity(configuration.isPressed ? 0.85 : 1)
    }
}

/// Nut phu vien mong.
struct NutPhuStyle: ButtonStyle {
    @Environment(\.isEnabled) var bat
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding(.horizontal, 14)
            .frame(maxWidth: .infinity, minHeight: 48)
            .foregroundColor(Mau.chu)
            .background(RoundedRectangle(cornerRadius: 14, style: .continuous)
                .fill(configuration.isPressed ? Mau.vien : Mau.the))
            .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous)
                .stroke(Mau.vien, lineWidth: 1.5))
            .opacity(bat ? 1 : 0.45)
    }
}
