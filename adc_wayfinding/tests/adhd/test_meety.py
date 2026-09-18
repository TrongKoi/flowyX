"""
Kiem lop goi Meety.

--------------------------------------------------------------------
KHONG TEST NAO O DAY DUOC GOI THAT
--------------------------------------------------------------------

Khong goi tien trinh con that, khong goi mang, khong doi Meety da cai
san tren may chay test. Toan bo duong goi di qua tham so `chay` - mot
ham gia lap thay cho `subprocess.run`.

Ly do: bo test phai chay duoc tren may bat ky, kem ca may CI khong co
Meety. Mot test "chi xanh khi may co cai Meety" la mot test se bi tat
di, va test bi tat thi bang khong co.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.adhd.meety import (                 # noqa: E402
    BienBan,
    cau_dang_chay,
    cau_tom_tat,
    doc_ket_qua,
    ghi_so,
    goi,
    lenh,
)

DAU = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
          "ùúủũụưừứửữựỳýỷỹỵđ")


def co_dau(s: str) -> bool:
    return any(c in DAU for c in s.lower())


KET_QUA_MAU = {
    "executive_summary": {
        "tldr": [
            "Bản 2.4 lùi từ 26/07 sang 28/07 do QA chưa xong.",
            "API thanh toán đã lên staging.",
            "Crash rate giảm từ 4,1% xuống 2,3%.",
        ]
    },
    "chapters": [
        {"title": "Tiến độ backend", "summary": "API thanh toán xong."},
    ],
}


@pytest.fixture
def meety_gia(tmp_path: Path) -> Path:
    """Mot thu muc trong giong Meety: co main.py va data/exports."""
    (tmp_path / "main.py").write_text("# gia lap\n", encoding="utf-8")
    (tmp_path / "data" / "exports").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def transcript(tmp_path: Path) -> Path:
    p = tmp_path / "hop.vtt"
    p.write_text("WEBVTT\n\n00:00.000 --> 00:02.000\nXin chào.\n",
                 encoding="utf-8")
    return p


def _chay_thanh_cong(meety: Path, noi_dung: dict = KET_QUA_MAU):
    """Gia lap subprocess.run: ghi ra tep ket qua roi bao thanh cong."""
    def _chay(cmd, **kw):
        ra = meety / "data" / "exports" / "mtg_test_minutes.json"
        ra.write_text(json.dumps(noi_dung, ensure_ascii=False),
                      encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return _chay


# ------------------------------------------------------- dong lenh

def test_dong_lenh_dung_dang_meety_mong_doi(tmp_path: Path):
    c = lenh(tmp_path, tmp_path / "a.vtt", "2026-09-15")
    assert c[0] == "python"
    assert c[1].endswith("main.py")
    assert "--input" in c and "--date" in c
    assert c[c.index("--date") + 1] == "2026-09-15"


def test_mac_dinh_co_mock_va_skip_stt(tmp_path: Path):
    """Demo truc tiep khong duoc phu thuoc API key hay mang."""
    c = lenh(tmp_path, tmp_path / "a.vtt", "2026-09-15")
    assert "--mock" in c and "--skip-stt" in c


def test_tat_duoc_mock_cho_duong_that(tmp_path: Path):
    c = lenh(tmp_path, tmp_path / "a.vtt", "2026-09-15", mock=False)
    assert "--mock" not in c


# ------------------------------------------------- duong thanh cong

def test_goi_thanh_cong_tra_ve_bien_ban(meety_gia: Path, transcript: Path):
    kq = goi(meety_gia, transcript, "2026-09-15",
             chay=_chay_thanh_cong(meety_gia))
    assert kq.ok and kq.bien_ban is not None
    assert len(kq.bien_ban.tldr) == 3


def test_goi_chay_dung_trong_thu_muc_meety(meety_gia: Path, transcript: Path):
    """Meety ghi ket qua theo duong dan TUONG DOI, nen cwd phai dung."""
    thay = {}

    def _chay(cmd, **kw):
        thay.update(kw)
        return _chay_thanh_cong(meety_gia)(cmd, **kw)

    goi(meety_gia, transcript, "2026-09-15", chay=_chay)
    assert Path(thay["cwd"]) == meety_gia


def test_goi_co_dat_timeout(meety_gia: Path, transcript: Path):
    """Khong duoc cho vo han - app se treo im lang."""
    thay = {}

    def _chay(cmd, **kw):
        thay.update(kw)
        return _chay_thanh_cong(meety_gia)(cmd, **kw)

    goi(meety_gia, transcript, "2026-09-15", timeout_s=42.0, chay=_chay)
    assert thay["timeout"] == 42.0


def test_chi_lay_bien_ban_sinh_ra_TRONG_lan_chay_nay(meety_gia: Path,
                                                     transcript: Path):
    """Ket qua cu con sot lai khong duoc nham la ket qua moi."""
    cu = meety_gia / "data" / "exports" / "cu_minutes.json"
    cu.write_text(json.dumps({"executive_summary": {"tldr": ["Cũ."]}}),
                  encoding="utf-8")
    import os
    os.utime(cu, (time.time() - 9999, time.time() - 9999))

    kq = goi(meety_gia, transcript, "2026-09-15",
             chay=_chay_thanh_cong(meety_gia))
    assert kq.ok and kq.bien_ban.tldr[0] != "Cũ."


# ------------------------------------------------------- duong loi

def test_khong_co_meety_thi_bao_bang_LOI_DOC_chu_khong_nem_ngoai_le(
        tmp_path: Path, transcript: Path):
    """
    Yeu cau cung: ben goi nam trong vong lap thoi gian thuc. Mot ngoai
    le lot ra se lam dung ca phien chi duong dang chay.
    """
    kq = goi(tmp_path / "khong-ton-tai", transcript, "2026-09-15")
    assert kq.ok is False
    assert kq.loi_doc and co_dau(kq.loi_doc)


def test_khong_co_transcript_thi_bao_ro(meety_gia: Path, tmp_path: Path):
    kq = goi(meety_gia, tmp_path / "khong-co.vtt", "2026-09-15")
    assert kq.ok is False and co_dau(kq.loi_doc)


def test_meety_tra_ma_loi_thi_bao_ro(meety_gia: Path, transcript: Path):
    def _hong(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 1, "", "traceback...")

    kq = goi(meety_gia, transcript, "2026-09-15", chay=_hong)
    assert kq.ok is False and co_dau(kq.loi_doc)


def test_timeout_thi_bao_ro_chu_khong_treo(meety_gia: Path, transcript: Path):
    def _lau(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, 1.0)

    kq = goi(meety_gia, transcript, "2026-09-15", chay=_lau)
    assert kq.ok is False
    assert "quá lâu" in kq.loi_doc


def test_khong_co_python_thi_bao_ro(meety_gia: Path, transcript: Path):
    def _khong_co(cmd, **kw):
        raise FileNotFoundError("python")

    kq = goi(meety_gia, transcript, "2026-09-15", chay=_khong_co)
    assert kq.ok is False and co_dau(kq.loi_doc)


def test_chay_xong_nhung_khong_ra_tep_nao(meety_gia: Path, transcript: Path):
    def _im(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, "", "")

    kq = goi(meety_gia, transcript, "2026-09-15", chay=_im)
    assert kq.ok is False and co_dau(kq.loi_doc)


def test_json_hong_thi_bao_ro(meety_gia: Path, transcript: Path):
    def _hong_json(cmd, **kw):
        (meety_gia / "data" / "exports" / "x_minutes.json").write_text(
            "{khong phai json", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    kq = goi(meety_gia, transcript, "2026-09-15", chay=_hong_json)
    assert kq.ok is False and "định dạng" in kq.loi_doc


def test_bien_ban_trong_thi_bao_ro(meety_gia: Path, transcript: Path):
    kq = goi(meety_gia, transcript, "2026-09-15",
             chay=_chay_thanh_cong(meety_gia, {"executive_summary": {}}))
    assert kq.ok is False and co_dau(kq.loi_doc)


# --------------------------------------------------- so do du lieu

def test_tldr_nam_trong_executive_summary_chu_khong_phai_cap_mot(
        tmp_path: Path):
    """
    So do that cua Meety KHONG co `tldr` hay `paragraphs` o cap mot.
    Bai nay khoa lai dieu do de khong ai sua nham theo tri nho.
    """
    p = tmp_path / "m.json"
    p.write_text(json.dumps(KET_QUA_MAU, ensure_ascii=False),
                 encoding="utf-8")
    bb = doc_ket_qua(p)
    assert bb.tldr and bb.chuong


def test_tldr_la_mot_chuoi_thi_van_doc_duoc(tmp_path: Path):
    """Phong khi Meety doi kieu tra ve."""
    p = tmp_path / "m.json"
    p.write_text(json.dumps({"executive_summary": {"tldr": "Một ý."}},
                            ensure_ascii=False), encoding="utf-8")
    assert doc_ket_qua(p).tldr == ["Một ý."]


# ------------------------------------------------------- doc len

def test_cau_dang_chay_co_dau_va_bao_se_lau():
    s = cau_dang_chay()
    assert co_dau(s) and ("một lúc" in s or "lâu" in s)


def test_doc_theo_khoi_chu_khong_doc_mot_mach():
    """Cung nguyen tac voi preview.py: tri nho lam viec co han."""
    bb = BienBan(tldr=[f"Ý {i}." for i in range(5)])
    s = cau_tom_tat(bb, tu_y=0)
    assert "Ý 0." in s and "Ý 1." in s
    assert "Ý 4." not in s


def test_con_y_thi_moi_nghe_tiep():
    bb = BienBan(tldr=[f"Ý {i}." for i in range(5)])
    assert "nghe tiếp" in cau_tom_tat(bb, tu_y=0)


def test_het_y_thi_khong_moi_nua():
    bb = BienBan(tldr=["Ý 1.", "Ý 2."])
    assert "nghe tiếp" not in cau_tom_tat(bb, tu_y=0)


def test_doc_qua_cuoi_thi_bao_het():
    bb = BienBan(tldr=["Ý 1."])
    assert "Hết" in cau_tom_tat(bb, tu_y=5)


def test_khong_co_tom_tat_thi_van_noi_duoc():
    assert co_dau(cau_tom_tat(BienBan()))


# --------------------------------------------------------- ghi so

def test_ghi_so_noi_them_chu_khong_de_len(tmp_path: Path):
    so = tmp_path / "so.json"
    bb = BienBan(tldr=["Ý một."])
    ghi_so(so, bb, luc=1.0, muc_dich="họp nhóm", ten_viec="phòng 6.04")
    ghi_so(so, bb, luc=2.0, muc_dich="nộp đơn", ten_viec="phòng 3.12")
    assert len(json.loads(so.read_text(encoding="utf-8"))) == 2


def test_ghi_so_giu_muc_dich_va_dich_de_sau_tra_lai(tmp_path: Path):
    so = tmp_path / "so.json"
    ghi_so(so, BienBan(tldr=["Ý."]), luc=1.0,
           muc_dich="họp nhóm", ten_viec="phòng 6.04")
    d = json.loads(so.read_text(encoding="utf-8"))[0]
    assert d["muc_dich"] == "họp nhóm" and d["ten_viec"] == "phòng 6.04"


def test_so_hong_thi_bat_dau_lai_chu_khong_lam_sap(tmp_path: Path):
    so = tmp_path / "so.json"
    so.write_text("{khong phai danh sach", encoding="utf-8")
    ghi_so(so, BienBan(tldr=["Ý."]), luc=1.0)
    assert len(json.loads(so.read_text(encoding="utf-8"))) == 1


def test_ep_utf8_khi_doc_dau_ra_cua_meety(meety_gia: Path, transcript: Path):
    """
    `text=True` mot minh se giai ma bang bang ma he dieu hanh. Tren
    Windows tieng Viet (cp1258) thi dau ra co dau cua Meety lam
    subprocess.run nem UnicodeDecodeError - da gap that khi chay thu.
    """
    thay = {}

    def _chay(cmd, **kw):
        thay.update(kw)
        return _chay_thanh_cong(meety_gia)(cmd, **kw)

    goi(meety_gia, transcript, "2026-09-15", chay=_chay)
    assert thay.get("encoding") == "utf-8"
    assert thay.get("errors") == "replace"


def test_ngoai_le_la_khong_bao_gio_lot_ra(meety_gia: Path, transcript: Path):
    """
    Hop dong cung cua lop nay. Ben goi nam trong vong lap thoi gian
    thuc; mot ngoai le lot ra se lam dung ca phien chi duong.
    """
    def _no_tung(cmd, **kw):
        raise RuntimeError("thu gi do khong doan truoc duoc")

    kq = goi(meety_gia, transcript, "2026-09-15", chay=_no_tung)
    assert kq.ok is False and co_dau(kq.loi_doc)


# ------------------------------------------------------------------
# Meety nam TRONG repo, va xuat ra TEP chu khong hien UI
# ------------------------------------------------------------------

def test_meety_nam_trong_repo():
    """
    Chep han ma nguon Meety vao thay vi doi nguoi dung cai rieng: luc
    demo khong con phu thuoc may co cai dat dung hay khong.
    """
    from wayfinding.adhd.meety import THU_MUC_MEETY_MAC_DINH
    assert THU_MUC_MEETY_MAC_DINH.is_dir()
    assert (THU_MUC_MEETY_MAC_DINH / "main.py").is_file()


def test_mac_dinh_xuat_ca_json_lan_markdown():
    """
    JSON de he thong doc va noi `tldr` len; Markdown de NGUOI DUNG doc
    lai sau. Day la yeu cau san pham - khong hien bien ban tren giao
    dien ma xuat ra tep.
    """
    from pathlib import Path
    from wayfinding.adhd.meety import lenh
    ra = lenh(Path("/x"), Path("/y.vtt"), "2026-09-14")
    assert "--format" in ra
    assert ra[ra.index("--format") + 1] == "json,md"


def test_chon_duoc_thu_muc_ra_va_tieu_de():
    from pathlib import Path
    from wayfinding.adhd.meety import lenh
    thu_muc_ra = Path("/bienban")
    ra = lenh(Path("/x"), Path("/y.vtt"), "2026-09-14",
              thu_muc_ra=thu_muc_ra, tieu_de="Họp nhóm")

    # So voi str(Path(...)) chu KHONG go cung "/bienban": tren Windows
    # str(Path("/bienban")) ra "ienban".
    assert ra[ra.index("--output") + 1] == str(thu_muc_ra)
    assert ra[ra.index("--title") + 1] == "Họp nhóm"


def test_khong_con_goi_server_web_cua_meety():
    """
    Da cat `frontend/`, `server/`, `run_server.py` cua Meety khoi repo.
    Neu co ai noi lai bang HTTP, test nay bao ngay.
    """
    from pathlib import Path
    from wayfinding.adhd.meety import lenh
    ra = " ".join(lenh(Path("/x"), Path("/y.vtt"), "2026-09-14"))
    assert "run_server" not in ra and "http" not in ra
