import SwiftUI
import UIKit

/// Trang thai man hinh chinh va vong gui goi tin.
///
/// Ban Swift cua `MainActivity.kt`. Cung ba viec, cung ranh gioi:
///
///     1. gui SU KIEN NGUOI DUNG len cau noi
///     2. hien va doc len nhung gi cau noi tra ve
///     3. GIU cac so cua rieng may nay
///
/// KHONG co quy tac nao cua Flowy o day - khi nao hoi gi, khi nao doi net
/// mat, the nao la ket - tat ca nam o `run_flowy.py`, cung logic voi ban
/// Android.
///
/// Moi thao tac tren lop nay deu chay tren LUONG CHINH: nut bam, va cau tra
/// loi (BridgeClient da dua ve main truoc khi goi).
final class FlowyModel: ObservableObject {

    // MARK: Hien thi

    @Published private(set) var tra = Reply()
    @Published var cauHoi = ""
    @Published private(set) var cauNoi = ""
    @Published private(set) var trangThai = ""
    @Published var oTraLoi = ""
    @Published private(set) var dangNghe = false

    // MARK: Phu thuoc

    let settings: AppSettings
    let soNhac = SoNhac()
    let soNhatKy = SoNhatKy()
    let soLich = SoLich()

    /// Tab dang mo. Lich doi sang tab Hom nay khi bat dau mot ke hoach.
    @Published var tab: Tab = .homNay
    enum Tab: Hashable { case homNay, lich, so, caiDat }
    private let soThoiLuong = SoThoiLuong()
    private let speaker = Speaker()
    private let voice = VoiceInput()
    private var bridge: BridgeClient?
    private var urlLucNoi = ""

    // MARK: Trang thai gui

    /// Co MOT LAN cho cu cham. Nhan vat khong bao gio chu dong bat chuyen.
    private var chamNhanVat = false
    private var loiChoGui: String?
    private var lenhChoGui: (String, String?)?
    private var gioHenChoGui: Double?
    private var uocChoGui: Double?

    private var trenManHinh = true
    private var tenViecDangLam: String?
    private var uocDaGui: Double?
    private var batDau: Date?
    private var hoiTuCham = false

    /// Chuoi goi dien san y dinh tu ke hoach - xem `batDauTuKeHoach`.
    private struct GoiCho { var lenh: String?; var voice: String?; var gioHen: Double?; var uoc: Double? }
    private var hangDoiKeHoach: [GoiCho] = []
    private var choTraLoiHangDoiTu: Date?

    private var nhipMs = 500
    private var hen: DispatchWorkItem?
    private var dangChay = false

    init(settings: AppSettings) {
        self.settings = settings
        trangThai = settings.serverUrl.isEmpty
            ? "Chưa có địa chỉ laptop. Mở Cài đặt để nhập."
            : "Sẵn sàng. Chạm vào bạn đồng hành khi bạn muốn hỏi."
    }

    // MARK: - Vong doi

    func batDauChay() {
        speaker.tocDo = settings.tocDoDoc
        if bridge == nil || settings.serverUrl != urlLucNoi { noiLai() }
        batVongLap()
        BaoGio.datLai(soNhac)
        BaoLich.datLai(soLich)
    }

    /// Ra khoi tien canh CHINH LA tin hieu phan tam - van gui tiep.
    func datTienCanh(_ tren: Bool) {
        trenManHinh = tren
        if tren {
            speaker.tocDo = settings.tocDoDoc
            if settings.serverUrl != urlLucNoi { noiLai() }
            guiNgay()
        }
    }

    private func noiLai() {
        urlLucNoi = settings.serverUrl
        bridge?.close()
        bridge = BridgeClient(
            baseUrl: settings.serverUrl,
            onReply: { [weak self] r in self?.nhan(r) },
            onError: { [weak self] loi in self?.trangThai = "Lỗi mạng: \(loi)" })
        trangThai = bridge == nil
            ? "Địa chỉ laptop chưa đúng. Ví dụ: http://192.168.1.100:8765"
            : "Đã nối với laptop."
    }

    private func batVongLap() {
        guard !dangChay else { return }
        dangChay = true
        lapLai()
    }

    private func lapLai() {
        guiMotGoi()
        let h = DispatchWorkItem { [weak self] in self?.lapLai() }
        hen = h
        DispatchQueue.main.asyncAfter(deadline: .now() + .milliseconds(nhipMs), execute: h)
    }

    /// Gui ngay, khong doi het nhip - luc ranh nhip la 2 giay.
    func guiNgay() {
        guard dangChay else { return }
        hen?.cancel()
        lapLai()
    }

    private func guiMotGoi() {
        guard let bridge else { return }

        // Mot o y dinh moi goi, doi tra loi (hoac 3 giay) roi gui o sau.
        var cho: GoiCho?
        if !hangDoiKeHoach.isEmpty,
           choTraLoiHangDoiTu.map({ Date().timeIntervalSince($0) > 3 }) ?? true {
            cho = hangDoiKeHoach.removeFirst()
            choTraLoiHangDoiTu = Date()
        }

        let lenh: (String, String?)?
        if let l = cho?.lenh { lenh = (l, nil) } else { lenh = lenhChoGui; lenhChoGui = nil }
        let voice = cho?.voice ?? (cho?.lenh == nil ? layVaXoa(&loiChoGui) : nil)
        let gioHen = cho?.gioHen ?? layVaXoa(&gioHenChoGui)
        let uoc = cho?.uoc ?? layVaXoa(&uocChoGui)
        let cham = layVaXoa(&chamNhanVat)
        // Goi co thao tac nguoi dung thi khong duoc mat - xem BridgeClient.
        let quanTrong = cho != nil || lenh != nil || voice != nil || cham || gioHen != nil || uoc != nil

        // Chi lich su cua DUNG viec dang lam - bang o dau bridge.py.
        let lichSu = tenViecDangLam.flatMap { soThoiLuong.motViec($0) }

        bridge.send(PhoneUpdate(
            t: Date().timeIntervalSince1970,
            trenManHinh: trenManHinh,
            chamNhanVat: cham,
            voice: voice,
            lenh: lenh?.0,
            noiDung: lenh?.1,
            battery: mucPin(),
            lichSu: lichSu,
            gioHen: gioHen,
            uocPhut: uoc,
            mucNhac: settings.mucNhac.rawValue), quanTrong: quanTrong)
    }

    private func layVaXoa<T>(_ x: inout T?) -> T? { defer { x = nil }; return x }
    private func layVaXoa(_ x: inout Bool) -> Bool { defer { x = false }; return x }

    private func mucPin() -> Double? {
        UIDevice.current.isBatteryMonitoringEnabled = true
        let p = UIDevice.current.batteryLevel
        return p >= 0 ? Double(p * 100) : nil
    }

    // MARK: - Nhan cau tra loi

    private func nhan(_ r: Reply) {
        nhipMs = min(max(r.nhipMs, 100), 10_000)
        if choTraLoiHangDoiTu != nil {
            choTraLoiHangDoiTu = nil
            if !hangDoiKeHoach.isEmpty { DispatchQueue.main.async { self.guiNgay() } }
        }
        if let ten = r.tenViec { tenViecDangLam = ten }

        if let say = r.say {
            cauNoi = say
            if settings.docLen { speaker.say(say, urgent: false) }
        }

        if let hoi = r.hoi {
            // HIEN luon; DOC LEN chi sau mot cu cham (NHAN_VAT_BRIEF 2.4).
            cauHoi = hoi
            hoiTuCham = r.listen
            if r.listen && settings.docLen { speaker.say(hoi, urgent: true) }
        } else if !hoiTuCham {
            cauHoi = ""
        }

        if settings.rung { speaker.vibrate(r.haptic) }
        speaker.playAm(r.am)
        if r.listen { nghe() }

        if r.xongPhien { ghiThoiLuong(r) }

        tra = r
        kiemLoiNhac()
    }

    private func ghiThoiLuong(_ r: Reply) {
        guard let ten = tenViecDangLam else { return }
        let phut: Double
        if let giay = r.daLamGiay {
            phut = giay / 60
        } else if let batDau {
            phut = Date().timeIntervalSince(batDau) / 60
        } else {
            return
        }
        soThoiLuong.ghi(ten, thatPhut: phut, uocPhut: uocDaGui)
        batDau = nil
        uocDaGui = nil
    }

    private func kiemLoiNhac() {
        guard let ln = soNhac.denHan() else { return }
        cauNoi = ln.cau
        if settings.docLen { speaker.say(ln.cau, urgent: true) }
    }

    // MARK: - Thao tac cua nguoi dung

    enum NutChinh { case batDau, xongBuoc, xongViec, tiepTuc }

    var nutChinh: NutChinh {
        if tra.tamDung { return .tiepTuc }
        if tra.trongPhien { return tra.chiSoBuoc < tra.cacBuoc.count ? .xongBuoc : .xongViec }
        return .batDau
    }

    var duYDinh: Bool { tra.viecGi != nil && tra.khiNao != nil && tra.oDau != nil }

    func bamNutChinh() {
        switch nutChinh {
        case .tiepTuc: guiLenh(Lenh.tiepTuc)
        case .xongBuoc: guiLenh(Lenh.xongBuoc)
        case .xongViec: guiLenh(Lenh.ketThuc)
        case .batDau:
            // Chu trong o tra loi di kem: nguoi dung hay go o cuoi roi bam
            // thang Bat dau.
            let chu = oTraLoi.trimmingCharacters(in: .whitespacesAndNewlines)
            oTraLoi = ""
            batDau = Date()
            guiLenh(Lenh.batDau, chu.isEmpty ? nil : chu)
        }
    }

    func tamDungHoacTiepTuc() {
        guard tra.trongPhien else { return }
        guiLenh(tra.tamDung ? Lenh.tiepTuc : Lenh.tamDung)
    }

    func ketThuc() {
        if tra.trongPhien { guiLenh(Lenh.ketThuc) }
    }

    func viecMoi() {
        guiLenh(Lenh.viecMoi)
        tenViecDangLam = nil
        uocDaGui = nil
        batDau = nil
        hoiTuCham = false
        cauNoi = ""
    }

    /// Nut Goi y - loi moi DUY NHAT de app doc len mot cau hoi. Thay cho
    /// cu cham nhan vat (da bo). Truong goi tin van ten `cham_nhan_vat`.
    func goiY() {
        chamNhanVat = true
        guiNgay()
    }

    /// Bat dau phien tu ke hoach: viec_moi -> ten (+ gio hen, uoc luong)
    /// -> "luc HH:MM" -> noi lam. Xem `MainActivity.batDauTuKeHoach`.
    func batDauTuKeHoach(_ kh: KeHoach) {
        hangDoiKeHoach = [
            GoiCho(lenh: Lenh.viecMoi),
            GoiCho(voice: kh.ten, gioHen: kh.ketThuc < 1440 ? Double(kh.ketThuc) : nil,
                   uoc: Double(kh.thoiLuong)),
            GoiCho(voice: "lúc \(Lich.gioPhut(kh.batDau))"),
        ]
        if let o = kh.oDau { hangDoiKeHoach.append(GoiCho(voice: o)) }
        tenViecDangLam = kh.ten
        uocDaGui = Double(kh.thoiLuong)
        batDau = nil
        hoiTuCham = false
        cauNoi = ""
        choTraLoiHangDoiTu = nil
        tab = .homNay
        guiNgay()
    }

    func guiLoiGo() {
        let chu = oTraLoi.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !chu.isEmpty else { return }
        oTraLoi = ""
        loiChoGui = chu
        cauHoi = ""
        hoiTuCham = false
        guiNgay()
    }

    func datGioHen(_ phut: Double?) {
        gioHenChoGui = phut ?? -1
        guiNgay()
    }

    func datUoc(_ phut: Double) {
        uocDaGui = phut
        uocChoGui = phut
        guiNgay()
    }

    func doiMucNhac(_ m: MucNhac) {
        settings.mucNhac = m
        guiNgay()
    }

    /// Nghe mot cau. Van luon co o go ben canh.
    func nghe() {
        guard !dangNghe else { return }
        guard VoiceInput.coQuyen else {
            VoiceInput.xinQuyen { [weak self] ok in
                if ok { self?.nghe() }
                else { self?.trangThai = "Cần quyền micro và nhận dạng giọng nói. Bạn vẫn gõ được ở ô bên cạnh." }
            }
            return
        }
        guard voice.available else {
            trangThai = "Máy chưa nghe được. Bạn gõ vào ô bên cạnh nhé."
            return
        }
        speaker.stop()
        dangNghe = true
        voice.listenOnce { [weak self] kq in
            guard let self else { return }
            self.dangNghe = false
            if let kq {
                self.loiChoGui = kq
                self.cauHoi = ""
                self.hoiTuCham = false
                self.guiNgay()
            } else {
                self.trangThai = "Máy chưa nghe được. Bạn gõ vào ô bên cạnh nhé."
            }
        }
    }

    func thuGiong() {
        speaker.tocDo = settings.tocDoDoc
        speaker.say("Xin chào. Đây là tốc độ đọc hiện tại.", urgent: true)
    }

    func lichNhacDoi() { BaoGio.datLai(soNhac) }
}
