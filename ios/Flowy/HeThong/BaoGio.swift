import UserNotifications

/// Chuong cho loi nhac - ban Swift cua `BaoGio.kt`.
///
/// iOS don gian hon Android o cho nay: thong bao lich co san he thong
/// giu qua khoi dong lai may, va khong can quyen "bao thuc chinh xac".
/// Chi can quyen thong bao.
///
/// Gioi han cua iOS: toi da 64 thong bao cho. Flowy dat toi da 32.
enum BaoGio {

    static let tienTo = "flowy-nhac-"
    static let toiDa = 32

    static func xinQuyen(_ xong: ((Bool) -> Void)? = nil) {
        UNUserNotificationCenter.current()
            .requestAuthorization(options: [.alert, .sound]) { ok, _ in
                DispatchQueue.main.async { xong?(ok) }
            }
    }

    /// Huy het roi dat lai theo so. Danh sach ngan - khong can tinh chenh lech.
    static func datLai(_ so: SoNhac) {
        let tt = UNUserNotificationCenter.current()
        tt.getPendingNotificationRequests { cho in
            let cu = cho.map(\.identifier).filter { $0.hasPrefix(tienTo) }
            tt.removePendingNotificationRequests(withIdentifiers: cu)

            for ln in so.danhSach.prefix(toiDa) {
                let nd = UNMutableNotificationContent()
                nd.title = "Lời nhắc"
                // Chi dung chu nguoi dung tu dat, khong them chu nao.
                nd.body = ln.ten
                nd.sound = .default

                var gio = DateComponents()
                gio.hour = Int(ln.gio) / 60
                gio.minute = Int(ln.gio) % 60
                let kh = UNCalendarNotificationTrigger(dateMatching: gio, repeats: ln.lapLai)
                tt.add(UNNotificationRequest(identifier: tienTo + ln.id.uuidString,
                                             content: nd, trigger: kh))
            }
        }
    }
}
