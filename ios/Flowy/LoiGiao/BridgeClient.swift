import Foundation

/// Gui goi tin len laptop tren luong nen.
///
/// Hai loai goi, giong ban Kotlin:
///
///     quan trong (lenh, loi noi, Goi y, gio hen...) -> xep hang, KHONG mat
///     thuong (chi trang thai)                       -> chi giu cai moi nhat
///
/// Ban dau chi giu MOT goi cho gui: mang cham thi goi thuong cua nhip sau
/// de mat goi "Xong buoc" nguoi dung vua bam.
///
/// Laptop CHI dung khi test va demo. Ban chay hoan toan tren may se bo lop
/// nay; giao dien khong phai doi vi no chi doc `Reply`.
final class BridgeClient {

    private let lock = NSLock()
    private var hangQuanTrong: [Data] = []
    private var goiThuong: Data?
    private var dangGui = false
    private var loiLienTiep = 0
    private var dong = false

    private let url: URL
    private let session: URLSession
    private let onReply: (Reply) -> Void
    private let onError: (String) -> Void

    init?(baseUrl: String,
          onReply: @escaping (Reply) -> Void,
          onError: @escaping (String) -> Void) {
        var goc = baseUrl.trimmingCharacters(in: .whitespacesAndNewlines)
        while goc.hasSuffix("/") { goc.removeLast() }
        guard let u = URL(string: goc + "/update"), u.scheme != nil, u.host != nil else {
            return nil
        }
        url = u
        let cfg = URLSessionConfiguration.ephemeral
        cfg.timeoutIntervalForRequest = 2
        cfg.timeoutIntervalForResource = 3
        cfg.waitsForConnectivity = false
        session = URLSession(configuration: cfg)
        self.onReply = onReply
        self.onError = onError
    }

    func send(_ goi: PhoneUpdate, quanTrong: Bool = false) {
        guard let body = try? JSONEncoder().encode(goi) else { return }
        lock.lock()
        if dong { lock.unlock(); return }
        if quanTrong {
            if hangQuanTrong.count < 32 { hangQuanTrong.append(body) }
        } else {
            goiThuong = body
        }
        if dangGui { lock.unlock(); return }
        dangGui = true
        lock.unlock()
        bom()
    }

    func close() {
        lock.lock(); dong = true; hangQuanTrong = []; goiThuong = nil; lock.unlock()
        session.invalidateAndCancel()
    }

    private func bom() {
        lock.lock()
        let body: Data
        if dong {
            dangGui = false; lock.unlock(); return
        } else if !hangQuanTrong.isEmpty {
            body = hangQuanTrong.removeFirst()
        } else if let g = goiThuong {
            body = g; goiThuong = nil
        } else {
            dangGui = false; lock.unlock(); return
        }
        lock.unlock()

        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json; charset=utf-8", forHTTPHeaderField: "Content-Type")
        req.httpBody = body

        session.dataTask(with: req) { [weak self] data, resp, err in
            guard let self else { return }
            let ma = (resp as? HTTPURLResponse)?.statusCode ?? 0
            if let data, err == nil, (200..<300).contains(ma) {
                self.loiLienTiep = 0
                let tra = (try? JSONDecoder().decode(Reply.self, from: data)) ?? Reply()
                DispatchQueue.main.async { self.onReply(tra) }
            } else {
                self.loiLienTiep += 1
                // Bao o lan 3 va thua dan - khong lam ngap dong trang thai.
                if self.loiLienTiep == 3 || self.loiLienTiep % 25 == 0 {
                    let cau = err?.localizedDescription ?? "HTTP \(ma)"
                    DispatchQueue.main.async { self.onError(cau) }
                }
            }
            self.bom()
        }.resume()
    }
}
