"""
Kiem bo nhac theo gio.

Bai quan trong nhat khong phai la bo nhac keu dung gio - ma la nhung
thu no KHONG lam. Xem `nhacviec.py` phan dau: bon thu khong lam, va vi
sao moi thu do lam san pham roi vao dien thiet bi y te.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wayfinding.adhd.nhacviec import (    # noqa: E402
    CUA_SO_PHUT,
    MIN_KY_TU,
    LoiNhac,
    SoNhac,
)

DAU = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
          "ùúủũụưừứửữựỳýỷỹỵđ")
HOM_NAY = "2026-09-15"
MAI = "2026-09-16"


def co_dau(s: str) -> bool:
    return any(c in DAU for c in s.lower())


# ------------------------------------------------- them va xoa

def test_them_roi_co_trong_danh_sach():
    so = SoNhac()
    assert so.them("uống nước", 8 * 60.0)
    assert len(so.danh_sach) == 1
    assert so.danh_sach[0].ten == "uống nước"


def test_ten_qua_ngan_thi_khong_nhan():
    so = SoNhac()
    assert not so.them("a" * (MIN_KY_TU - 1), 8 * 60.0)
    assert not so.them("   ", 8 * 60.0)
    assert not so.them("", 8 * 60.0)
    assert so.danh_sach == []


def test_gio_ngoai_mot_ngay_thi_khong_nhan():
    so = SoNhac()
    assert not so.them("việc gì đó", -1.0)
    assert not so.them("việc gì đó", 1440.0)
    assert so.danh_sach == []


def test_ten_duoc_cat_khoang_trang_thua():
    so = SoNhac()
    so.them("   uống nước   ", 8 * 60.0)
    assert so.danh_sach[0].ten == "uống nước"


def test_xoa_dung_muc():
    so = SoNhac()
    so.them("việc sáng", 8 * 60.0)
    so.them("việc trưa", 12 * 60.0)
    assert so.xoa(0)
    assert [ln.ten for ln in so.danh_sach] == ["việc trưa"]


def test_xoa_chi_so_sai_thi_khong_lam_gi():
    so = SoNhac()
    so.them("việc sáng", 8 * 60.0)
    assert not so.xoa(5)
    assert not so.xoa(-1)
    assert len(so.danh_sach) == 1


def test_xoa_roi_thi_muc_con_lai_van_bao_duoc():
    """
    Chi so `_da_bao` phai truot theo khi mot muc bi xoa. Neu khong,
    xoa muc dau se lam muc thu hai bi coi nhu da bao roi.
    """
    so = SoNhac()
    so.them("việc sáng", 8 * 60.0)
    so.them("việc trưa", 12 * 60.0)
    so.den_han(8 * 60.0, HOM_NAY)          # bao muc 0
    so.xoa(0)
    assert so.den_han(12 * 60.0, HOM_NAY).ten == "việc trưa"


# ------------------------------------------------- den han

def test_dung_gio_thi_bao():
    so = SoNhac()
    so.them("uống nước", 8 * 60.0)
    ln = so.den_han(8 * 60.0, HOM_NAY)
    assert ln is not None and ln.ten == "uống nước"


def test_chua_toi_gio_thi_im():
    so = SoNhac()
    so.them("uống nước", 8 * 60.0)
    assert so.den_han(8 * 60.0 - 1.0, HOM_NAY) is None


def test_tre_trong_cua_so_thi_van_bao():
    """Nguoi dung mo app muon vai phut van con kip nhac."""
    so = SoNhac()
    so.them("uống nước", 8 * 60.0)
    assert so.den_han(8 * 60.0 + CUA_SO_PHUT - 1.0, HOM_NAY) is not None


def test_tre_qua_cua_so_thi_THOI():
    """
    Khong bao mai. Mot loi nhac hien lien tuc se bi tat di, va luc do
    moi loi nhac khac cung mat theo.
    """
    so = SoNhac()
    so.them("uống nước", 8 * 60.0)
    assert so.den_han(8 * 60.0 + CUA_SO_PHUT + 1.0, HOM_NAY) is None


def test_bao_roi_thi_khong_bao_lai_trong_ngay():
    so = SoNhac()
    so.them("uống nước", 8 * 60.0)
    assert so.den_han(8 * 60.0, HOM_NAY) is not None
    assert so.den_han(8 * 60.0 + 1.0, HOM_NAY) is None


def test_sang_ngay_moi_thi_bao_lai():
    so = SoNhac()
    so.them("uống nước", 8 * 60.0)
    so.den_han(8 * 60.0, HOM_NAY)
    assert so.den_han(8 * 60.0, MAI) is not None


def test_nhieu_loi_nhac_thi_bao_tung_cai():
    so = SoNhac()
    so.them("việc sáng", 8 * 60.0)
    so.them("việc trưa", 12 * 60.0)
    assert so.den_han(8 * 60.0, HOM_NAY).ten == "việc sáng"
    assert so.den_han(12 * 60.0, HOM_NAY).ten == "việc trưa"


def test_so_trong_thi_khong_co_gi_de_bao():
    assert SoNhac().den_han(8 * 60.0, HOM_NAY) is None


# ------------------------------------------------- cau noi

def test_cau_co_dau_va_nhac_dung_ten_nguoi_dung_dat():
    ln = LoiNhac(ten="uống nước", gio=8 * 60.0)
    s = ln.cau()
    assert co_dau(s)
    assert "uống nước" in s


def test_cau_KHONG_them_loi_khuyen_nao():
    """
    App nhac dung cai nguoi dung bao no nhac, va khong noi gi them. Mot
    cau nhu "nho uong du nuoc nhe" la loi khuyen suc khoe.
    """
    s = LoiNhac(ten="uống nước", gio=8 * 60.0).cau().lower()
    for xau in ("nên", "nhớ", "đừng quên", "hãy", "tốt cho"):
        assert xau not in s, s


# ------------------------------- nhung thu module KHONG duoc co

def test_KHONG_dem_ty_le_tuan_thu():
    """
    Mot bo nhac co dem ty le tuan thu la mot he theo doi de quan ly
    benh; mot bo nhac khong dem chi la mot cai dong ho biet noi.

    Xem `nhacviec.py` phan dau ve ca ly do phap ly lan ly do thuc te -
    mot thu nghiem 73 nguoi cho thay viec dem nay khong co tac dung.
    """
    so = SoNhac()
    so.them("uống nước", 8 * 60.0)
    for ten in ("ty_le", "tuan_thu", "da_lam", "thong_ke", "diem",
                "bo_lo", "diem_danh"):
        assert not hasattr(so, ten), ten
        assert not hasattr(so.danh_sach[0], ten), ten


def test_KHONG_co_khai_niem_lieu_luong():
    so = SoNhac()
    so.them("uống nước", 8 * 60.0)
    for ten in ("lieu", "so_vien", "ham_luong", "don_vi", "thuoc"):
        assert not hasattr(so.danh_sach[0], ten), ten


def test_ten_la_chuoi_TU_DO_khong_doi_chieu_danh_muc_nao():
    """
    Module khong duoc biet ten nguoi dung go la gi. Biet ten thuoc la
    biet chan doan.
    """
    so = SoNhac()
    for ten in ("uống nước", "gọi mẹ", "xyzzy", "tưới cây", "!!!???"):
        assert so.them(ten, 9 * 60.0), ten
    assert len(so.danh_sach) == 5


def test_module_KHONG_tu_ghi_ra_dia():
    """
    Ten loi nhac la noi dung ca nhan - xem docs/FLOWY_THIET_KE.md muc
    7.3, va bang trong loi_chung/bridge.py.
    """
    src = (Path(__file__).resolve().parents[2] / "wayfinding" / "adhd"
           / "nhacviec.py").read_text(encoding="utf-8")
    for xau in ("open(", "write_text", "Path(", "os.path", "pathlib"):
        assert xau not in src, f"module tu ghi ra dia: {xau}"


def test_module_KHONG_goi_mang():
    """Ten loi nhac khong duoc di dau ca - ke ca qua cau noi."""
    src = (Path(__file__).resolve().parents[2] / "wayfinding" / "adhd"
           / "nhacviec.py").read_text(encoding="utf-8")
    for xau in ("import socket", "urllib", "requests", "http"):
        assert xau not in src, f"module goi mang: {xau}"


# ------------------------------------------------- luu va doc

def test_luu_roi_doc_lai_giu_nguyen():
    so = SoNhac()
    so.them("uống nước", 8 * 60.0)
    so.them("gọi mẹ", 19 * 60.0, lap_lai_hang_ngay=False)
    lai = SoNhac.from_json(so.to_json())
    assert [ln.ten for ln in lai.danh_sach] == ["uống nước", "gọi mẹ"]
    assert lai.danh_sach[1].lap_lai_hang_ngay is False


def test_so_hong_thi_bat_dau_lai_chu_khong_lam_sap():
    assert SoNhac.from_json(None).danh_sach == []
    assert SoNhac.from_json({"x": 1}).danh_sach == []
    assert SoNhac.from_json([{"thieu_khoa": 1}]).danh_sach == []


def test_muc_hong_le_khong_lam_mat_muc_con_lai():
    so = SoNhac.from_json([
        {"ten": "việc sáng", "gio": 480.0},
        {"hong": True},
        {"ten": "việc trưa", "gio": 720.0}])
    assert [ln.ten for ln in so.danh_sach] == ["việc sáng", "việc trưa"]


def test_doc_lai_KHONG_mang_theo_cai_da_bao():
    """
    Mo lai app khong duoc lam mat cac loi nhac trong ngay. Nhung cung
    khong duoc mang theo ban ghi ve viec da bao nhung gi - do la du lieu
    ve hanh vi, va so nay khong giu no.
    """
    so = SoNhac()
    so.them("uống nước", 8 * 60.0)
    so.den_han(8 * 60.0, HOM_NAY)
    d = so.to_json()
    assert all("da_bao" not in m and "bao_roi" not in m for m in d)
    lai = SoNhac.from_json(d)
    assert lai.den_han(8 * 60.0, HOM_NAY) is not None
