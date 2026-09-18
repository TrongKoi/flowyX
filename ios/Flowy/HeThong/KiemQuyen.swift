import AVFoundation
import Speech
import UIKit
import UserNotifications

/// Kiem tra quyen - ban Swift cua `KiemQuyen.kt`.
///
/// Moi quyen thieu lam hong mot tinh nang theo cach IM LANG. Man hinh nay
/// noi ro tung quyen de lam gi, va cham vao dong thieu thi xin hoac mo
/// Cai dat. Thieu quyen nao app van chay - khong chan gi ca.
///
/// Khong danh dau @MainActor: cac ham hoi quyen cua iOS goi lai tren luong
/// bat ky. Moi lan doi `ds` deu dua ve luong chinh bang tay.
final class KiemQuyen: ObservableObject {

    enum Loai: String, Identifiable {
        case thongBao, micro, nhanDang, giongViet
        var id: String { rawValue }
    }

    struct Muc: Identifiable {
        let loai: Loai
        let ten: String
        let deLamGi: String
        let daCo: Bool
        /// Chua hoi lan nao -> cham vao la hien hop thoai he thong.
        let chuaHoi: Bool
        var id: String { loai.rawValue }
    }

    @Published private(set) var ds: [Muc] = []

    func lamMoi() {
        UNUserNotificationCenter.current().getNotificationSettings { [weak self] st in
            let tb = st.authorizationStatus
            DispatchQueue.main.async {
                guard let self else { return }
                let mic = AVAudioSession.sharedInstance().recordPermission
                let sr = SFSpeechRecognizer.authorizationStatus()
                self.ds = [
                    Muc(loai: .thongBao, ten: "Thông báo",
                        deLamGi: "Để lời nhắc hiện ra khi bạn đang ở app khác.",
                        daCo: tb == .authorized || tb == .provisional,
                        chuaHoi: tb == .notDetermined),
                    Muc(loai: .micro, ten: "Micro",
                        deLamGi: "Để trả lời bằng giọng nói thay vì gõ.",
                        daCo: mic == .granted, chuaHoi: mic == .undetermined),
                    Muc(loai: .nhanDang, ten: "Nhận dạng giọng nói",
                        deLamGi: "Để hiểu câu bạn nói. Chạy trên máy khi iOS hỗ trợ.",
                        daCo: sr == .authorized, chuaHoi: sr == .notDetermined),
                    Muc(loai: .giongViet, ten: "Giọng đọc tiếng Việt",
                        deLamGi: "Cài đặt → Trợ năng → Nội dung được đọc → Giọng nói → Tiếng Việt.",
                        daCo: Speaker.coGiongViet, chuaHoi: false),
                ]
            }
        }
    }

    var conThieu: Int { ds.filter { !$0.daCo }.count }

    func xuLy(_ m: Muc) {
        guard !m.daCo else { return }
        switch m.loai {
        case .thongBao where m.chuaHoi:
            BaoGio.xinQuyen { [weak self] _ in self?.lamMoi() }
        case .micro where m.chuaHoi:
            AVAudioSession.sharedInstance().requestRecordPermission { [weak self] _ in
                DispatchQueue.main.async { self?.lamMoi() }
            }
        case .nhanDang where m.chuaHoi:
            SFSpeechRecognizer.requestAuthorization { [weak self] _ in
                DispatchQueue.main.async { self?.lamMoi() }
            }
        default:
            // Da tu choi, hoac la giong doc: iOS khong cho mo thang trang
            // tai giong, nen mo trang Cai dat cua app.
            if let url = URL(string: UIApplication.openSettingsURLString) {
                UIApplication.shared.open(url)
            }
        }
    }
}
