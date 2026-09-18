import UserNotifications

/// Thong bao cho ke hoach trong lich - ban Swift cua `LichBao.kt`.
///
/// iOS gioi han 64 thong bao cho. Loi nhac hang ngay dung toi da 32, lich
/// dung toi da 30 lan GAN NHAT trong 8 ngay. Moi lan mo app hoac sua lich
/// thi tinh lai - ke hoach lap lai van co thong bao mai.
enum BaoLich {

    static let tienTo = "flowy-lich-"
    static let toiDa = 30

    static func datLai(_ so: SoLich) {
        let ds = Lich.lanNhacToi(so.danhSach, bayGio: SoLich.bayGio(), toiDa: toiDa)
            .filter { !so.daXong.contains(Lich.khoaXong($0.keHoach.id, $0.ngayDienRa)) }
        let tt = UNUserNotificationCenter.current()
        tt.getPendingNotificationRequests { cho in
            tt.removePendingNotificationRequests(
                withIdentifiers: cho.map(\.identifier).filter { $0.hasPrefix(tienTo) })
            for (i, ln) in ds.enumerated() {
                let nd = UNMutableNotificationContent()
                nd.title = "\(ln.keHoach.emoji) Lịch"
                nd.body = Lich.cauNhac(ln)
                nd.sound = .default
                nd.userInfo = ["ke_hoach": ln.keHoach.id]
                let c = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute],
                                                        from: SoLich.sangDate(ln.phutTuyetDoi))
                let kh = UNCalendarNotificationTrigger(dateMatching: c, repeats: false)
                tt.add(UNNotificationRequest(identifier: "\(tienTo)\(i)", content: nd, trigger: kh))
            }
        }
    }
}
