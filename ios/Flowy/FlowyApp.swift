import SwiftUI
import UserNotifications

@main
struct FlowyApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var delegate
    @StateObject private var settings: AppSettings
    @StateObject private var model: FlowyModel
    @StateObject private var focus = FocusModel()
    @StateObject private var tienDo = SoTienDo()
    @StateObject private var bienBan = SoBienBan()
    @StateObject private var hoanTac = HoanTacModel()
    @Environment(\.scenePhase) private var phase

    init() {
        let s = AppSettings()
        _settings = StateObject(wrappedValue: s)
        _model = StateObject(wrappedValue: FlowyModel(settings: s))
    }

    var body: some Scene {
        WindowGroup {
            GocApp()
                .environmentObject(settings)
                .environmentObject(model)
                .environmentObject(model.soLich)
                .environmentObject(model.soNhatKy)
                .environmentObject(focus)
                .environmentObject(tienDo)
                .environmentObject(bienBan)
                .environmentObject(hoanTac)
                // v4: chi theo che do Sang/Toi cua may - khong co nut doi.
                .tint(Mau.chuLienKet)
                .onAppear {
                    BaoGio.xinQuyen()
                    BaoLich.datLai(model.soLich)
                    ChuyenLoiNhac.chayMotLan(soNhac: model.soNhac, lich: model.soLich)
                    tienDo.diemDanh()
                }
                .onChange(of: phase) { p in
                    if p == .active {
                        // Tu diem danh: mo app la duoc tinh vao chuoi ngay.
                        tienDo.diemDanh()
                        BaoLich.datLai(model.soLich)
                    }
                }
        }
    }
}

/// KHUNG APP v4: nam tab, thanh tab tu ve (pill + nhan chu, xem
/// `ThanhTabDuoi`), Cai dat mo tu icon co dinh tren MOI tab.
struct GocApp: View {
    @EnvironmentObject var settings: AppSettings
    @State private var tab = TabV4.keHoach
    @State private var moCaiDat = false

    var body: some View {
        VStack(spacing: 0) {
            ZStack {
                switch tab {
                case .keHoach: ManHinhKeHoach(tab: $tab, moCaiDat: $moCaiDat)
                case .lich: ManHinhLich(tab: $tab, moCaiDat: $moCaiDat)
                case .focus: ManHinhFocus(moCaiDat: $moCaiDat)
                case .nhatKy: ManHinhNhatKy(moCaiDat: $moCaiDat)
                case .bienBan: ManHinhBienBan(moCaiDat: $moCaiDat)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            ThanhTabDuoi(tab: $tab)
        }
        .background(Mau.nen.ignoresSafeArea())
        // Thanh Hoan tac / thong bao: NGAY TREN thanh tab, khong che noi dung.
        .overlay(alignment: .bottom) { ThanhHoanTac().padding(.bottom, 72) }
        .sheet(isPresented: $moCaiDat) { ManHinhCaiDat() }
        .onReceive(NotificationCenter.default.publisher(for: .flowyMoTabFocus)) { _ in
            tab = .focus
        }
    }
}

extension Notification.Name {
    static let flowyMoTabFocus = Notification.Name("flowy_mo_tab_focus")
}

final class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        return true
    }

    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                willPresent notification: UNNotification,
                                withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([.banner, .sound, .list])
    }

    /// Cham thong bao het gio Focus -> mo dung tab Focus, khong de nguoi
    /// dung "ket" o mot man hinh khong lien quan.
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                didReceive response: UNNotificationResponse,
                                withCompletionHandler completionHandler: @escaping () -> Void) {
        if response.notification.request.content.userInfo["mo_tab"] as? String == "focus" {
            NotificationCenter.default.post(name: .flowyMoTabFocus, object: nil)
        }
        completionHandler()
    }
}
