"""
Kiem so thoi luong.

Bai quan trong nhat: cau doi chieu chi NEU SO LIEU, khong ket luan gi
ve nguoi dung. "Ban hay uoc thieu" la nhan xet ve tinh cach; "lan truoc
20, thuc te 35" la con so ho tu doi chieu duoc.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wayfinding.adhd.thoiluong import (       # noqa: E402
    CHENH_DANG_KE_PHUT,
    SO_LAN_XET,
    SoThoiLuong,
)

DAU = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
          "ùúủũụưừứửữựỳýỷỹỵđ")
VIEC = "viết báo cáo"


def co_dau(s: str) -> bool:
    return any(c in DAU for c in s.lower())


# ------------------------------------------------- uoc luong

def test_chua_co_so_lieu_thi_khong_uoc_duoc():
    """Chua biet thi noi khong biet, khong doan."""
    assert SoThoiLuong().uoc_luong(VIEC) is None


def test_mot_lan_thi_dung_luon_lan_do():
    so = SoThoiLuong()
    so.ghi(VIEC, that_phut=35.0, uoc_phut=20.0)
    assert so.uoc_luong(VIEC) == 35.0


def test_dung_TRUNG_VI_chu_khong_phai_trung_binh():
    """
    Mot lan bi gian doan bat thuong keo trung binh lech han. Trung vi
    bo qua cac lan ca biet do.
    """
    so = SoThoiLuong()
    for p in (30.0, 32.0, 31.0, 300.0):        # 300 la lan mat dien
        so.ghi(VIEC, that_phut=p)
    tv = so.uoc_luong(VIEC)
    assert tv == pytest.approx(31.5)           # trung binh se la 98,25


def test_chi_xet_may_lan_gan_nhat():
    """
    Lay het lich su thi mot thang sau van bi keo boi nhung lan vung ve
    dau tien.
    """
    so = SoThoiLuong()
    for _ in range(10):
        so.ghi(VIEC, that_phut=120.0)          # nhung lan dau, rat cham
    for _ in range(SO_LAN_XET):
        so.ghi(VIEC, that_phut=20.0)           # gio da nhanh
    assert so.uoc_luong(VIEC) == 20.0


def test_moi_viec_mot_lich_su_rieng():
    so = SoThoiLuong()
    so.ghi("viết báo cáo", that_phut=40.0)
    so.ghi("dọn phòng", that_phut=15.0)
    assert so.uoc_luong("viết báo cáo") == 40.0
    assert so.uoc_luong("dọn phòng") == 15.0


def test_ghi_du_lieu_vo_nghia_thi_bo_qua():
    so = SoThoiLuong()
    so.ghi("", that_phut=30.0)
    so.ghi(VIEC, that_phut=0.0)
    so.ghi(VIEC, that_phut=-5.0)
    assert so.ban_ghi == {}


# ------------------------------------------- cau doi chieu

def test_cau_doi_chieu_neu_ca_hai_con_so():
    so = SoThoiLuong()
    so.ghi(VIEC, that_phut=35.0, uoc_phut=20.0)
    s = so.cau_doi_chieu(VIEC)
    assert s and "20" in s and "35" in s and co_dau(s)


def test_uoc_gan_dung_thi_IM_LANG():
    """
    Noi ra mot chenh lech khong dang ke se lam cau canh bao mat gia tri
    o nhung lan that su lech nhieu.
    """
    so = SoThoiLuong()
    so.ghi(VIEC, that_phut=22.0, uoc_phut=20.0)
    assert so.cau_doi_chieu(VIEC) is None


def test_lech_dung_bang_nguong_thi_im_lang():
    so = SoThoiLuong()
    so.ghi(VIEC, that_phut=20.0 + CHENH_DANG_KE_PHUT - 0.1, uoc_phut=20.0)
    assert so.cau_doi_chieu(VIEC) is None


def test_khong_uoc_thi_khong_co_gi_de_doi_chieu():
    so = SoThoiLuong()
    so.ghi(VIEC, that_phut=35.0)
    assert so.cau_doi_chieu(VIEC) is None


def test_uoc_THUA_cung_duoc_noi_ra():
    """
    Uoc 60 ma lam xong trong 20 cung la uoc sai, va biet dieu do cung
    huu ich - no la ly do nguoi dung tri hoan mot viec that ra nhanh.
    """
    so = SoThoiLuong()
    so.ghi(VIEC, that_phut=20.0, uoc_phut=60.0)
    s = so.cau_doi_chieu(VIEC)
    assert s and "60" in s and "20" in s


def test_cau_doi_chieu_KHONG_ket_luan_ve_nguoi_dung():
    """
    Chi neu so lieu. Khong duoc co nhan xet ve tinh cach hay thoi quen -
    do la mot buoc sang danh gia, va app khong o vi tri do.
    """
    so = SoThoiLuong()
    so.ghi(VIEC, that_phut=35.0, uoc_phut=20.0)
    s = so.cau_doi_chieu(VIEC).lower()
    for xau in ("bạn hay", "bạn thường", "bạn luôn", "bạn kém",
                "đáng lẽ", "lẽ ra", "sai"):
        assert xau not in s, s


def test_cau_goi_y_co_dau():
    so = SoThoiLuong()
    so.ghi(VIEC, that_phut=35.0)
    assert co_dau(so.cau_goi_y(VIEC))


def test_chua_co_lich_su_thi_khong_goi_y():
    assert SoThoiLuong().cau_goi_y(VIEC) is None


# ------------------------------------------------- luu va doc

def test_luu_roi_doc_lai_giu_nguyen():
    so = SoThoiLuong()
    so.ghi(VIEC, that_phut=35.0, uoc_phut=20.0)
    so.ghi(VIEC, that_phut=30.0)
    lai = SoThoiLuong.from_json(so.to_json())
    assert lai.uoc_luong(VIEC) == so.uoc_luong(VIEC)
    assert lai.cau_doi_chieu(VIEC) == so.cau_doi_chieu(VIEC)


def test_so_hong_thi_bat_dau_lai_chu_khong_lam_sap():
    """Mat lich su la phien toai; app khong chay duoc la mot loi."""
    assert SoThoiLuong.from_json(None).ban_ghi == {}
    assert SoThoiLuong.from_json({"x": "khong phai danh sach"}).ban_ghi == {}
    assert SoThoiLuong.from_json({"x": [{"thieu_khoa": 1}]}).ban_ghi == {}


def test_ban_ghi_hong_le_khong_lam_mat_ca_muc():
    """Mot ban ghi hong khong duoc keo theo nhung ban ghi con lai."""
    so = SoThoiLuong.from_json(
        {VIEC: [{"that": 30.0}, {"hong": True}, {"that": 40.0}]})
    assert so.so_lan(VIEC) == 2


# ------------------------------------- khong tu ghi ra dia

def test_module_KHONG_tu_ghi_ra_dia():
    """
    Ten cong viec la noi dung ca nhan. Laptop khong duoc ghi no xuong
    dia - xem docs/FLOWY_THIET_KE.md muc 7.3.

    Module chi cung cap cau truc va phep tinh; viec luu nam o phia dien
    thoai.
    """
    src = (Path(__file__).resolve().parents[2] / "wayfinding" / "adhd"
           / "thoiluong.py").read_text(encoding="utf-8")
    for xau in ("open(", "write_text", "Path(", "os.path", "pathlib"):
        assert xau not in src, f"module tu ghi ra dia: {xau}"
