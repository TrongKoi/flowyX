"""
GOI MEETY - tom tat bien ban cuoc hop.

--------------------------------------------------------------------
MEETY LA MOT DU AN RIENG, KHONG PHAI THU VIEN
--------------------------------------------------------------------

`meeting-minutes-ai-demo` la mot chuong trinh Python doc lap co giao
dien dong lenh rieng. No KHONG phai thu vien de `import` vao day.

Nen ranh gioi la TIEN TRINH CON:

    BoussoleX  --(ghi transcript ra file)-->  main.py cua Meety
               <--(doc JSON ket qua)--------

Khong copy code cua Meety vao repo nay, khong viet lai logic cua no.
Doi ben cham nhau dung mot cho: dong lenh vao, tep JSON ra.

Ly do khong chi la ve sach se. Meety co pipeline rieng, co so kiem
quota, co bo kiem chung noi dung - copy mot manh vao day la copy mot
manh da chet, va lan sau Meety sua thi ban o day khong sua theo.

--------------------------------------------------------------------
CHAY OFFLINE CHO DEMO
--------------------------------------------------------------------

Duong day du can GROQ_API_KEY (nhan dien giong noi) va GEMINI_API_KEY
(trich xuat noi dung). Ca hai deu la phu thuoc mang, va demo truc tiep
truoc giam khao KHONG NEN phu thuoc mang.

Hai duong tranh:

    --skip-stt   transcript co san (Zoom/Meet/Teams deu cho tai .vtt
                 mien phi) -> bo han khau nhan dien giong noi
    --mock       dung bo sinh gia lap trong Meety -> khong goi mang gi

Da chay thu that: `--input sample_transcript.json --skip-stt --mock`
cho ra bien ban day du, 0 dong, khong can API key nao.

--------------------------------------------------------------------
LOI PHAI NOI RA, KHONG DUOC TREO IM LANG
--------------------------------------------------------------------

Nguoi dung khong nhin man hinh cho tien do. Moi duong that bai o day
deu phai tra ve mot cau TIENG VIET CO DAU de doc len, khong duoc nem
ngoai le len tren roi de app dung hinh.
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

# Meety co the mat vai chuc giay toi vai phut o duong day du. Cat qua
# som la giet mot tien trinh sap xong; cat qua muon la de nguoi dung
# doi vo vong. 5 phut la moc cho duong that; demo dung --mock thi xong
# trong vai giay.
TIMEOUT_S = 300.0

# Doc bao nhieu y trong tldr truoc khi hoi co nghe tiep khong.
#
# Cung nguyen tac voi preview.py: tri nho lam viec giu duoc khoang bon
# don vi. Doc lien mot mach nam y thi nguoi nghe mat phan giua - dung
# nhom nguoi tinh nang nay phuc vu.
Y_MOI_LAN = 2


@dataclass(frozen=True)
class BienBan:
    """Ket qua da doc tu JSON cua Meety."""

    tldr: list[str] = field(default_factory=list)
    chuong: list[dict] = field(default_factory=list)
    duong_dan: Path | None = None

    @property
    def co_noi_dung(self) -> bool:
        return bool(self.tldr or self.chuong)


@dataclass(frozen=True)
class KetQua:
    """
    Ket qua mot lan goi.

    Khong nem ngoai le: ben goi nam trong vong lap thoi gian thuc, va
    mot ngoai le lot ra se lam dung ca phien chi duong dang chay.
    """

    ok: bool
    bien_ban: BienBan | None = None
    loi_doc: str | None = None          # cau TIENG VIET de doc len


def _loi(cau: str) -> KetQua:
    return KetQua(ok=False, loi_doc=cau)


# Meety nam NGAY TRONG REPO, o thu muc `meety/` ngang hang
# `adc_wayfinding/`. Chep han ma nguon vao thay vi doi nguoi dung cai
# rieng: luc demo khong con phu thuoc may co cai dat dung hay khong.
#
# Da cat bo `frontend/`, `server/`, `run_server.py` cua Meety - chung
# dung de hien bien ban tren web, ma o day ta KHONG hien UI: Meety xuat
# thang ra tep .md/.docx cho nguoi dung doc.
THU_MUC_MEETY_MAC_DINH = Path(__file__).resolve().parents[3] / "meety"


def lenh(thu_muc: Path, transcript: Path, ngay: str,
         mock: bool = True, skip_stt: bool = True,
         dinh_dang: str = "json,md", thu_muc_ra: Path | None = None,
         tieu_de: str = "") -> list[str]:
    """
    Dung dong lenh goi Meety.

    Tach rieng ra de kiem duoc MA LENH ma khong phai chay that - xem
    tests/adhd/test_meety.py.

    `dinh_dang` mac dinh "json,md": JSON de he thong doc va noi `tldr`
    len, Markdown de NGUOI DUNG doc lai sau. Day la yeu cau san pham -
    khong hien bien ban tren giao dien, ma xuat ra tep.
    """
    ra = ["python", str(thu_muc / "main.py"),
          "--input", str(transcript),
          "--date", ngay,
          "--format", dinh_dang]
    if thu_muc_ra is not None:
        ra += ["--output", str(thu_muc_ra)]
    if tieu_de:
        ra += ["--title", tieu_de]
    if skip_stt:
        ra.append("--skip-stt")
    if mock:
        ra.append("--mock")
    return ra


def doc_ket_qua(duong_dan: Path) -> BienBan:
    """
    Doc tep JSON Meety sinh ra.

    LUU Y ve so do du lieu: `tldr` KHONG nam o cap mot. No nam trong
    `executive_summary.tldr`, va no la MOT DANH SACH cau, khong phai
    mot cau. Tuong tu, khong co truong `paragraphs` - phan noi dung
    chia theo `chapters`.

    Da kiem tren ket qua that cua Meety, khong doan tu tai lieu.
    """
    d = json.loads(duong_dan.read_text(encoding="utf-8"))
    es = d.get("executive_summary") or {}
    tldr = es.get("tldr") or []
    if isinstance(tldr, str):          # phong khi Meety doi sang mot chuoi
        tldr = [tldr]
    return BienBan(tldr=list(tldr),
                   chuong=list(d.get("chapters") or []),
                   duong_dan=duong_dan)


def _moi_nhat(thu_muc: Path, sau: float) -> Path | None:
    """Tep bien ban moi nhat sinh ra SAU moc thoi gian cho truoc.

    Khong doc stdout de lay duong dan: chuoi in ra la giao dien cho
    NGUOI doc, Meety doi cach in mot chut la lop nay hong im lang.
    Moc thoi gian thi khong phu thuoc cach trinh bay.
    """
    xuat = thu_muc / "data" / "exports"
    if not xuat.is_dir():
        return None
    ung = [p for p in xuat.glob("*minutes.json")
           if p.stat().st_mtime >= sau - 1.0]
    return max(ung, key=lambda p: p.stat().st_mtime) if ung else None


def goi(thu_muc_meety: str | Path, transcript: str | Path, ngay: str,
        mock: bool = True, timeout_s: float = TIMEOUT_S,
        chay=subprocess.run) -> KetQua:
    """
    Goi Meety mot lan. KHONG BAO GIO nem ngoai le.

    `chay` tach ra lam tham so de test thay duoc bang ban gia lap -
    khong test nao duoc goi that ra tien trinh con hay ra mang.
    """
    thu_muc = Path(thu_muc_meety)
    tep = Path(transcript)

    if not (thu_muc / "main.py").is_file():
        return _loi("Không tìm thấy Meety. Kiểm tra lại đường dẫn tới "
                    "thư mục Meety trong cài đặt.")
    if not tep.is_file():
        return _loi("Không tìm thấy tệp bản ghi cuộc họp.")

    bat_dau = time.time()
    try:
        kq = chay(lenh(thu_muc, tep, ngay, mock=mock),
                  cwd=str(thu_muc), capture_output=True,
                  # PHAI ep utf-8 kem errors="replace".
                  #
                  # `text=True` mot minh se giai ma stdout bang bang ma
                  # cua HE DIEU HANH. Tren Windows tieng Viet do thuong
                  # la cp1258, ma Meety in ra tieng Viet co dau - gap
                  # byte ngoai bang la nem UnicodeDecodeError NGAY TRONG
                  # subprocess.run, truoc khi ham nay kip xu ly gi.
                  #
                  # Da gap that khi chay thu voi Meety that:
                  #   UnicodeDecodeError: 'charmap' codec can't decode
                  #   byte 0x8d ... cp1258.py
                  #
                  # Loi do se lot qua moi menh de except ben duoi va pha
                  # dung hop dong "khong bao gio nem" cua lop nay.
                  encoding="utf-8", errors="replace",
                  timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return _loi("Meety chạy quá lâu nên tôi đã dừng lại. "
                    "Bạn thử lại với bản ghi ngắn hơn.")
    except FileNotFoundError:
        return _loi("Máy chưa cài Python cho Meety, nên không chạy được "
                    "phần tóm tắt cuộc họp.")
    except OSError:
        return _loi("Không chạy được Meety trên máy này.")
    except Exception:                      # noqa: BLE001
        # Bat het la CO Y, khong phai cau tha.
        #
        # Hop dong cua lop nay la KHONG BAO GIO NEM: ben goi nam trong
        # vong lap thoi gian thuc, va mot ngoai le lot ra se lam dung ca
        # phien chi duong dang chay - dung luc nguoi dung dang di.
        #
        # Meety la tien trinh NGOAI, do dai ngoai le no co the gay ra
        # khong the liet ke het truoc duoc. Nen o dung ranh gioi nay,
        # doi moi thu la xau nhat ve mot cau doc duoc la dung.
        return _loi("Có lỗi khi gọi Meety. Bản ghi vẫn được giữ nguyên.")

    if getattr(kq, "returncode", 1) != 0:
        return _loi("Meety báo lỗi khi tóm tắt. Bản ghi vẫn được giữ "
                    "nguyên, bạn thử lại sau.")

    ra = _moi_nhat(thu_muc, bat_dau)
    if ra is None:
        return _loi("Meety chạy xong nhưng không tạo ra biên bản nào.")

    try:
        bb = doc_ket_qua(ra)
    except (OSError, ValueError):
        return _loi("Biên bản Meety tạo ra bị lỗi định dạng, không đọc được.")

    if not bb.co_noi_dung:
        return _loi("Biên bản trống. Có thể bản ghi quá ngắn hoặc không "
                    "có lời nói nào.")
    return KetQua(ok=True, bien_ban=bb)


# --------------------------------------------------------------------
# doc len
# --------------------------------------------------------------------

def cau_dang_chay() -> str:
    """Noi NGAY khi bat dau, vi viec nay ton vai chuc giay toi vai phut.

    Im lang trong luc cho se bi hieu la app treo - nguoi dung khong
    nhin man hinh de biet co thanh tien do.
    """
    return "Đang tóm tắt cuộc họp. Việc này mất một lúc, tôi sẽ báo khi xong."


def cau_tom_tat(bb: BienBan, tu_y: int = 0, moi_lan: int = Y_MOI_LAN) -> str:
    """
    Doc tldr theo khoi, khong doc lien mot mach.

    `tu_y` la chi so y bat dau. Tra cau da kem loi moi nghe tiep neu
    con y chua doc.
    """
    if not bb.tldr:
        return "Biên bản không có phần tóm tắt."

    khoi = bb.tldr[tu_y:tu_y + moi_lan]
    if not khoi:
        return "Hết phần tóm tắt."

    s = " ".join(khoi)
    con = len(bb.tldr) - (tu_y + len(khoi))
    if tu_y == 0:
        s = f"Đã tóm tắt xong. {s}"
    if con > 0:
        s += f" Còn {con} ý nữa. Bạn muốn nghe tiếp không?"
    return s


# --------------------------------------------------------------------
# luu lai de tra cuu
# --------------------------------------------------------------------

def ghi_so(so: Path, bb: BienBan, luc: float,
           muc_dich: str | None = None, ten_viec: str | None = None) -> None:
    """
    Ghi mot dong vao so bien ban, kem thoi diem va muc dich chuyen di.

    MUC DO: day la ban luu DON GIAN, dang noi them vao cuoi tep. No du
    de sau nay tra lai bang cach doc het so va loc theo `ten_viec` hay
    `muc_dich` - nhung chua co lop tra cuu nao viet san. Voi so luong
    cuoc hop cua mot nguoi dung thi doc het tep la du nhanh; neu sau
    nay can nhanh hon thi thay bang SQLite, khong phai sua cho nao
    khac vi hop dong chi la "ghi mot ban ghi".
    """
    ban_ghi = {
        "luc": luc,
        "muc_dich": muc_dich,
        "ten_viec": ten_viec,
        "tldr": bb.tldr[:1],
        "duong_dan": str(bb.duong_dan) if bb.duong_dan else None,
    }
    cu: list[dict] = []
    if so.is_file():
        try:
            cu = json.loads(so.read_text(encoding="utf-8"))
            if not isinstance(cu, list):
                cu = []
        except (OSError, ValueError):
            cu = []        # so hong thi bat dau lai, khong lam sap app
    cu.append(ban_ghi)
    so.parent.mkdir(parents=True, exist_ok=True)
    so.write_text(json.dumps(cu, ensure_ascii=False, indent=1),
                  encoding="utf-8")
