"""
Cau noi dien thoai <-> laptop qua WiFi.

Dien thoai lam MAN HINH va DAU VAO, laptop lam BO NAO:

    dien thoai  --su kien nguoi dung-->  laptop
    laptop      --cau noi + trang thai->  dien thoai

--------------------------------------------------------------------
VI SAO CON CAU NOI, KHI BAN CHINH CHAY TREN IOS
--------------------------------------------------------------------

Laptop la moi truong PHAT TRIEN, khong phai mot phan cua san pham.

Loi quyet dinh viet bang Python de sua thuat toan va chay lai bo test
trong vai giay, thay vi build lai app moi lan doi mot nguong. Ban iOS
chay cung loi do va khong can laptop.

Noi thang dieu nay khi trinh bay. Giau thi bi tru diem nang hon nhieu
so voi thua nhan.

--------------------------------------------------------------------
RANH GIOI DU LIEU - BAT BUOC
--------------------------------------------------------------------

Xem docs/FLOWY_THIET_KE.md muc 7.3. Tom tat:

Du lieu suc khoe la du lieu ca nhan NHAY CAM theo Luat Bao ve du lieu
ca nhan 2025. Phan nang nhat cua luat roi vao viec chuyen du lieu cho
ben thu ba. Nen quyet dinh la: du lieu o lai tren may nguoi dung.

Cau noi chi mang TRANG THAI TAM THOI:

    duoc mang            | KHONG BAO GIO duoc mang
    ---------------------|---------------------------------
    dang lam viec gi     | nhat ky cam xuc
    con bao nhieu phut   | ghi chu ve trieu chung
    lenh hien thi        | ten cac loi nhac nguoi dung tu dat
    cau noi, ma rung     | so thoi luong (lich su lam viec)

Va laptop KHONG GHI GI XUONG DIA. No la bo nao tam thoi, khong phai
kho luu tru. Co mot bai test canh gac dieu nay.

Chi dung thu vien chuan cua Python - khong can cai them gi.
"""

from __future__ import annotations

import json
import sys
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

# --------------------------------------------------------------------
# Lenh dien thoai gui len
# --------------------------------------------------------------------
#
# Chuoi thuan thay vi Enum: goi tin la JSON, va mot chuoi sai chinh ta
# thi de thay hon mot so thu tu sai.

LENH_BAT_DAU = "bat_dau"        # bat dau mot phien lam viec
LENH_XONG_BUOC = "xong_buoc"    # danh dau xong buoc hien tai
LENH_TAM_DUNG = "tam_dung"      # nguoi dung tu bam tam dung
LENH_TIEP_TUC = "tiep_tuc"
LENH_KET_THUC = "ket_thuc"
LENH_VIEC_MOI = "viec_moi"      # xoa y dinh cu, gom mot viec khac

LENH_HOP_LE = (LENH_BAT_DAU, LENH_XONG_BUOC, LENH_TAM_DUNG,
               LENH_TIEP_TUC, LENH_KET_THUC, LENH_VIEC_MOI)

# Muc nhac - docs/UIUX_QUYET_DINH.md cau 4. Doi muc la MOT lan cham tren
# man hinh chinh, nen gia tri di theo moi goi tin nguoi dung doi.
MUC_NHAC_MOC = {
    "it": (5.0, 1.0),
    "vua": (10.0, 5.0, 3.0, 1.0),
    "nhieu": (15.0, 10.0, 5.0, 3.0, 2.0, 1.0),
}


@dataclass
class PhoneUpdate:
    """Mot goi tin tu dien thoai.

    Khac han ban dieu huong: khong con tu the, do sau, hay anh. Dien
    thoai gio chi bao SU KIEN NGUOI DUNG va vai chi so may.
    """

    # Thoi diem may gui, giay. De trong thi ben nhan tu lay gio may chu.
    t: float | None = None

    # App co dang o TIEN CANH khong.
    #
    # Day la tin hieu phan tam CHINH, thay cho tin hieu chuyen dong cua
    # ban dieu huong. Nguoi dung mo app khac chinh la dinh nghia thuc te
    # cua "bi sao nhang" trong boi canh nay - va no chinh xac hon do
    # chuyen dong nhieu.
    tren_man_hinh: bool = True

    # Nguoi dung vua CHAM vao nhan vat dong hanh.
    #
    # Nhan vat khong bao gio chu dong bat chuyen (xem
    # docs/luu-tru/NHAN_VAT_BRIEF.md muc 2.4). Cu cham nay la loi moi DUY NHAT
    # de app len tieng.
    cham_nhan_vat: bool = False

    # Cau nguoi dung vua noi, dien thoai da nhan dang san.
    voice: str | None = None

    # Nut nguoi dung vua bam, va chuoi di kem (ten viec, ten buoc).
    lenh: str | None = None
    noi_dung: str | None = None

    battery: float | None = None      # phan tram pin
    thermal: float | None = None      # nhiet do may, do C

    # Lich su thoi luong cua CONG VIEC DANG LAM, do dien thoai gui len.
    #
    # Dien thoai so huu tep luu, laptop chi muon phan can cho lan tinh
    # nay. Xem docs/FLOWY_THIET_KE.md muc 7.3 - laptop khong ghi gi
    # xuong dia, nen no khong the tu giu lich su nay.
    lich_su: dict | None = None

    # ---- ba truong them cho giao dien v2 (16/09) ----
    #
    # Truoc day gio hen chi dat duoc bang `--gio-hen` tren laptop, va
    # nguoi dung khong co cho nao nhap uoc luong - nen dong ho gan nhu
    # khong bao gio hien, va cau doi chieu uoc luong khong bao gio co.

    # Gio hen, PHUT tinh tu nua dem. So AM nghia la bo gio hen.
    gio_hen: float | None = None

    # Nguoi dung uoc viec nay mat bao nhieu phut. Ghi lai de LAN SAU doi
    # chieu voi thoi luong that - xem FLOWY_THIET_KE muc 3.1.
    uoc_phut: float | None = None

    # "it" | "vua" | "nhieu". Xem MUC_NHAC_MOC.
    muc_nhac: str | None = None


@dataclass
class BridgeReply:
    """Tra ve cho dien thoai."""

    say: str | None = None
    haptic: str | None = None

    # Am ngan phat kem, khong phai giong noi. Ten thuan - dien thoai tu
    # chon cao do, vi cao do la chuyen cua thiet bi phat.
    am: str | None = None

    # Trang thai nhan vat: "binh_thuong", "vui", "thong_cam", "tu_hao".
    # BON gia tri, BA trong so do tich cuc - khong co gia tri nao the
    # hien buon hay that vong. Xem dongvien.py ve ly do.
    ban: str = "binh_thuong"

    # Chi so tu the "dang ban" cua nhan vat. Dien thoai doi hinh khi so
    # nay doi. Doi THUA va roi rac, khong phai hoat hinh chay lien tuc -
    # xem docs/luu-tru/NHAN_VAT_BRIEF.md muc 2.6.
    tu_the: int = 0

    # Cau hoi dang cho nguoi dung tra loi. Khac `say` o cho no DOI mot
    # cau tra loi.
    hoi: str | None = None

    # Bao dien thoai bat micro.
    #
    # Mot co ro rang thay vi de dien thoai doan tu noi dung cau noi: so
    # chuoi thi doi mot chu trong ma la hong lop nghe, ma hong im lang.
    listen: bool = False

    # Cho dong ho truc quan. None nghia la khong hien dong ho.
    con_lai_giay: float | None = None
    tong_giay: float | None = None

    # Nhip dien thoai NEN gui goi tin, mili giay.
    nhip_ms: int = 500

    # Phien vua ket thuc o goi tin NAY. Bat dung MOT lan.
    #
    # Dien thoai so huu so thoi luong (muc 7.3), nen no phai biet luc
    # nao mot phien xong de ghi lai thoi luong that. Khong co co nay thi
    # no phai doan tu cau noi - ma doan tu cau noi la hong ngay lan dau
    # ai do sua cau chu.
    xong_phien: bool = False

    # Ten cong viec cua phien dang chay, de dien thoai biet ghi so vao
    # muc nao.
    #
    # Day la ten chinh nguoi dung vua go len, nen gui nguoc ve khong lam
    # lo them gi. Bang o dau file cam mang LICH SU lam viec qua cau noi,
    # khong cam ten viec dang lam - dong dau cot ben trai ghi ro.
    ten_viec: str | None = None

    # ---- trang thai cho giao dien v2 (16/09) ----
    #
    # Giao dien moi co ba khoi CO DINH: thoi gian, buoc hien tai, ban dong
    # hanh. Truoc day dien thoai khong biet y dinh da gom duoc gi hay dang
    # o buoc nao, nen khong ve duoc khoi nao ngoai dong ho.
    #
    # Tat ca la noi dung nguoi dung VUA go len cho viec DANG LAM - cot
    # trai cua bang o dau file. Khong co gi thuoc cot phai.

    # Ba o y dinh thuc thi da gom duoc. None = con trong.
    viec_gi: str | None = None
    khi_nao: str | None = None
    o_dau: str | None = None

    # Cac buoc cua phien, va chi so buoc dang lam (== len = xong het).
    cac_buoc: list | None = None
    chi_so_buoc: int = 0

    # Co phien dang chay (da bat dau, chua xong).
    trong_phien: bool = False
    tam_dung: bool = False

    # So giay THAT da lam, da tru thoi gian tam dung. Dien thoai ghi so
    # thoi luong bang con so nay khi `xong_phien` bat.
    da_lam_giay: float | None = None

    # "HH:MM" hoac None. Hien lai tren nut dat gio hen.
    gio_hen: str | None = None

    # Uoc luong nguoi dung vua nhap, va goi y tu lich su (trung vi).
    uoc_phut: float | None = None
    goi_y_phut: float | None = None

    muc_nhac: str = "vua"

    def to_json(self) -> dict:
        return {
            "say": self.say,
            "haptic": self.haptic,
            "am": self.am,
            "ban": self.ban,
            "tu_the": self.tu_the,
            "hoi": self.hoi,
            "listen": self.listen,
            "con_lai_giay": (None if self.con_lai_giay is None
                             else round(self.con_lai_giay, 1)),
            "tong_giay": (None if self.tong_giay is None
                          else round(self.tong_giay, 1)),
            "nhip_ms": self.nhip_ms,
            "xong_phien": self.xong_phien,
            "ten_viec": self.ten_viec,
            "viec_gi": self.viec_gi,
            "khi_nao": self.khi_nao,
            "o_dau": self.o_dau,
            "cac_buoc": list(self.cac_buoc) if self.cac_buoc else [],
            "chi_so_buoc": self.chi_so_buoc,
            "trong_phien": self.trong_phien,
            "tam_dung": self.tam_dung,
            "da_lam_giay": (None if self.da_lam_giay is None
                            else round(self.da_lam_giay, 1)),
            "gio_hen": self.gio_hen,
            "uoc_phut": self.uoc_phut,
            "goi_y_phut": (None if self.goi_y_phut is None
                           else round(self.goi_y_phut, 1)),
            "muc_nhac": self.muc_nhac,
        }


def parse_update(payload: dict) -> PhoneUpdate:
    """Doc goi tin JSON tu dien thoai.

    Moi truong deu co gia tri mac dinh, va truong hong thi bo qua chu
    khong lam sap: mot goi tin loi khong duoc phep dung ca phien lam
    viec cua nguoi dung.
    """
    upd = PhoneUpdate()

    t = payload.get("t")
    if isinstance(t, (int, float)):
        upd.t = float(t)

    if isinstance(payload.get("tren_man_hinh"), bool):
        upd.tren_man_hinh = payload["tren_man_hinh"]
    if isinstance(payload.get("cham_nhan_vat"), bool):
        upd.cham_nhan_vat = payload["cham_nhan_vat"]

    v = payload.get("voice")
    if isinstance(v, str) and v.strip():
        upd.voice = v.strip()

    lenh = payload.get("lenh")
    if isinstance(lenh, str) and lenh in LENH_HOP_LE:
        upd.lenh = lenh
    nd = payload.get("noi_dung")
    if isinstance(nd, str) and nd.strip():
        upd.noi_dung = nd.strip()

    ls = payload.get("lich_su")
    if isinstance(ls, dict):
        upd.lich_su = ls

    for ten in ("battery", "thermal"):
        gt = payload.get(ten)
        if isinstance(gt, (int, float)):
            setattr(upd, ten, float(gt))

    # bool la con cua int trong Python - loai ra, `true` khong phai gio.
    gh = payload.get("gio_hen")
    if isinstance(gh, (int, float)) and not isinstance(gh, bool):
        if gh < 0 or 0 <= gh < 1440:
            upd.gio_hen = float(gh)

    uoc = payload.get("uoc_phut")
    if isinstance(uoc, (int, float)) and not isinstance(uoc, bool):
        if 0 < uoc <= 24 * 60:
            upd.uoc_phut = float(uoc)

    muc = payload.get("muc_nhac")
    if isinstance(muc, str) and muc in MUC_NHAC_MOC:
        upd.muc_nhac = muc

    return upd


# --------------------------------------------------------------------

class BridgeServer:
    """
    May chu HTTP nhan du lieu tu dien thoai.

    Dung HTTP thay vi WebSocket vi de debug hon nhieu: co the thu bang
    curl hoac trinh duyet, va Android goi duoc bang thu vien chuan.
    10 goi/giay la du cho toc do di bo.

    Cach dung:
        server = BridgeServer(on_update=my_handler, port=8765)
        server.start()
        ...
        server.stop()
    """

    def __init__(
        self,
        on_update: Callable[[PhoneUpdate], BridgeReply],
        on_session: Callable[[str, str], dict] | None = None,
        host: str = "0.0.0.0",
        port: int = 8765,
        verbose: bool = False,
        max_pending: int = 2,
    ):
        self.on_update = on_update
        self.on_session = on_session
        self.host = host
        self.port = port
        self.verbose = verbose
        self.max_pending = max_pending
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.packets = 0
        self.skipped = 0
        self.last_battery: float | None = None

        # ThreadingHTTPServer chay MOI ket noi tren MOT LUONG RIENG, nen
        # on_update co the bi goi dong thoi. Cac doi tuong trang thai
        # (Localizer, GuidanceEngine, SightingFilter, RunRecorder) deu
        # KHONG an toan da luong: doc-sua-ghi dong thoi lam mat cap nhat
        # va lam hong vi tri - dung loai loi "tu tin noi sai" ma ca thiet
        # ke dang phong. Khoa o day de moi noi dung BridgeServer deu an
        # toan, thay vi bat tung cho goi tu nho.
        self._state_lock = threading.Lock()
        self._pending_lock = threading.Lock()
        self._pending = 0
        self._last_reply: dict | None = None

    # ---------- vong doi ----------

    def start(self) -> None:
        handler = _make_handler(self)
        self._httpd = _Server((self.host, self.port), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever,
                                        daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None

    @property
    def url(self) -> str:
        return f"http://{local_ip()}:{self.port}"

    # ---------- xu ly ----------

    def handle_update(self, payload: dict) -> dict:
        """
        Xu ly mot goi tin, tuan tu hoa va co GIOI HAN HANG DOI.

        Neu da co qua nhieu goi dang cho, goi moi bi BO QUA va tra ve
        cau tra loi gan nhat. Voi bai toan chi duong thoi gian thuc,
        xu ly tu the MOI NHAT quan trong hon xu ly du moi tu the: xep
        hang khong gioi han se lam do tre tang dan cho toi khi chi dan
        den sau khi nguoi dung da di qua cho re.
        """
        with self._pending_lock:
            if self._pending >= self.max_pending:
                self.skipped += 1
                # Neu chua co cau tra loi nao de dung lai, tra ve trang
                # thai "chua biet" - dung thu can noi luc chua dinh vi
                # duoc. Gioi han hang doi KHONG duoc phu thuoc vao viec
                # da co bo nho dem hay chua, neu khong thi dung luc khoi
                # dong - luc de nghen nhat - lai xep hang vo han.
                stale = dict(self._last_reply or BridgeReply().to_json())
                stale["stale"] = True
                stale["say"] = None       # khong doc lai cau cu
                stale["haptic"] = None
                return stale
            self._pending += 1

        try:
            with self._state_lock:
                upd = parse_update(payload)
                self.packets += 1
                if upd.battery is not None:
                    self.last_battery = upd.battery
                reply = self.on_update(upd).to_json()
                self._last_reply = reply
                return reply
        finally:
            with self._pending_lock:
                self._pending -= 1

    def handle_session(self, payload: dict) -> dict:
        if self.on_session is None:
            return {"ok": False, "error": "server khong ho tro doi tuyen"}
        return self.on_session(payload.get("start", ""), payload.get("goal", ""))


class _Server(ThreadingHTTPServer):
    """
    ThreadingHTTPServer voi hang doi ket noi lon hon.

    Mac dinh cua socketserver chi la 5. Khi dien thoai mo lai ket noi
    lien tuc (WiFi chap chon, hoac client khong tai su dung ket noi),
    hang doi 5 bi tran va he dieu hanh RESET ket noi - dien thoai nhan
    duoc loi ngay giua luc dang dan duong.
    """

    request_queue_size = 64
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        """Dien thoai dong ket noi giua chung khong phai loi server.

        WiFi chap chon, app chuyen sang nen, hoac client dong socket
        thay vi tra ve be ket noi - tat ca deu lam luong dang doc bi
        ConnectionResetError. Mac dinh cua socketserver IN CA VET NGAN
        XEP ra stderr cho moi lan nhu vay.

        O 8 goi/giay, mot phut WiFi chap chon in ra hang tram vet.
        Ghi stderr la thao tac DONG BO - no chan chinh luong dang phuc
        vu. Nen dong tracebacks khong chi la on mat: no lam cham dung
        cai vong lap phai chay deu.

        Loi mang thi im. Moi loi khac van in - do moi la loi that.
        """
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionResetError, ConnectionAbortedError,
                            BrokenPipeError, TimeoutError)):
            if self.verbose_errors:
                print(f"[bridge] {client_address[0]} ngat ket noi: "
                      f"{type(exc).__name__}", file=sys.stderr)
            return
        super().handle_error(request, client_address)

    # Bat len khi can soi loi mang. Mac dinh tat.
    verbose_errors = False


def _make_handler(server: BridgeServer):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):     # tat log mac dinh, qua on
            if server.verbose:
                super().log_message(fmt, *args)

        def _send(self, code: int, obj: dict) -> None:
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> dict:
            n = int(self.headers.get("Content-Length", 0))
            if not n:
                return {}
            try:
                return json.loads(self.rfile.read(n).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return {}

        def do_OPTIONS(self):                  # noqa: N802
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "POST, GET")
            self.end_headers()

        def do_GET(self):                      # noqa: N802
            if self.path in ("/", "/health"):
                self._send(200, {"ok": True, "packets": server.packets,
                                 "battery": server.last_battery})
            else:
                self._send(404, {"ok": False})

        def do_POST(self):                     # noqa: N802
            payload = self._read_json()
            try:
                if self.path == "/update":
                    self._send(200, server.handle_update(payload))
                elif self.path == "/session":
                    self._send(200, server.handle_session(payload))
                else:
                    self._send(404, {"ok": False})
            except Exception as e:             # noqa: BLE001
                # Khong bao gio de server chet giua demo
                self._send(500, {"ok": False, "error": str(e)})

    return Handler


def local_ip() -> str:
    """Dia chi IP tren mang LAN, de go vao dien thoai."""
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))            # khong gui gi that
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()
