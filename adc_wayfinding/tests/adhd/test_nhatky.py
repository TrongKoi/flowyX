"""
Kiem so nhat ky.

Bai quan trong nhat: module nay KHONG CO PHEP TINH NAO tren noi dung
nguoi dung viet. Cho nao app quy ghi chep ve mot con so tong hop, cho
do no thanh mot cong cu theo doi - xem `nhatky.py` phan dau.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wayfinding.adhd.nhatky import (      # noqa: E402
    TOI_DA_MUC,
    Muc,
    SoNhatKy,
)

# 2026-09-15 09:30 gio dia phuong, tinh nguoc ra giay he thong. Dung gio
# do hai chieu de khong phu thuoc mui gio may chay test.
import time                               # noqa: E402

LUC = time.mktime((2026, 9, 15, 9, 30, 0, 0, 0, -1))


# ------------------------------------------------- ghi

def test_ghi_roi_co_trong_so():
    so = SoNhatKy()
    assert so.ghi("hôm nay khó vào việc", luc=LUC)
    assert len(so.muc) == 1
    assert so.muc[0].noi_dung == "hôm nay khó vào việc"


def test_noi_dung_rong_thi_khong_nhan():
    so = SoNhatKy()
    assert not so.ghi("")
    assert not so.ghi("   ")
    assert not so.ghi("a")
    assert so.muc == []


def test_the_nao_la_CHU_khong_phai_so():
    """
    Thang 1-5 tien cho app hon, va do chinh la ly do khong dung no: mot
    con so chi co ich khi co gi do cong no lai, ma cong lai la thu
    khong duoc lam.
    """
    so = SoNhatKy()
    for chu in ("mệt", "ổn", "như bị kéo từng mảnh", "không biết"):
        so.ghi("ghi chú", the_nao=chu, luc=LUC)
    assert [m.the_nao for m in so.muc] == [
        "mệt", "ổn", "như bị kéo từng mảnh", "không biết"]


def test_the_nao_de_trong_cung_duoc():
    so = SoNhatKy()
    so.ghi("chỉ muốn ghi lại thôi", luc=LUC)
    assert so.muc[0].the_nao is None


def test_the_nao_toan_khoang_trang_coi_nhu_khong_co():
    so = SoNhatKy()
    so.ghi("ghi chú", the_nao="   ", luc=LUC)
    assert so.muc[0].the_nao is None


def test_giu_dung_thu_tu_viet():
    so = SoNhatKy()
    for i in range(5):
        so.ghi(f"muc {i}", luc=LUC + i)
    assert [m.noi_dung for m in so.muc] == [f"muc {i}" for i in range(5)]


def test_qua_gioi_han_thi_muc_cu_nhat_roi_ra():
    """
    Gioi han nay la gioi han RIENG TU, khong phai gioi han ky thuat:
    mot quyen so khong gioi han la mot ho so dai vo han ve mot nguoi.
    """
    so = SoNhatKy()
    for i in range(TOI_DA_MUC + 10):
        so.ghi(f"muc {i}", luc=LUC + i)
    assert len(so.muc) == TOI_DA_MUC
    assert so.muc[0].noi_dung == "muc 10"
    assert so.muc[-1].noi_dung == f"muc {TOI_DA_MUC + 9}"


# ------------------------------------------------- xoa

def test_nguoi_dung_xoa_duoc_bat_cu_muc_nao():
    """Quyen xoa la mot phan cua quyen so huu."""
    so = SoNhatKy()
    for i in range(3):
        so.ghi(f"muc {i}", luc=LUC + i)
    assert so.xoa(1)
    assert [m.noi_dung for m in so.muc] == ["muc 0", "muc 2"]


def test_xoa_chi_so_sai_thi_khong_lam_gi():
    so = SoNhatKy()
    so.ghi("muc", luc=LUC)
    assert not so.xoa(9)
    assert not so.xoa(-1)
    assert len(so.muc) == 1


def test_xoa_het_duoc():
    so = SoNhatKy()
    for i in range(5):
        so.ghi(f"muc {i}", luc=LUC + i)
    so.xoa_het()
    assert so.muc == []


# ------------------------------------------------- doc lai

def test_gan_day_tra_ve_cac_muc_moi_nhat():
    so = SoNhatKy()
    for i in range(10):
        so.ghi(f"muc {i}", luc=LUC + i)
    assert [m.noi_dung for m in so.gan_day(3)] == ["muc 7", "muc 8", "muc 9"]


def test_gan_day_it_hon_so_yeu_cau_thi_tra_het():
    so = SoNhatKy()
    so.ghi("muc duy nhat", luc=LUC)
    assert len(so.gan_day(10)) == 1


def test_gan_day_so_khong_hoac_am_thi_tra_rong():
    so = SoNhatKy()
    so.ghi("muc", luc=LUC)
    assert so.gan_day(0) == []
    assert so.gan_day(-1) == []


def test_gan_day_tra_BAN_SAO_khong_phai_so_goc():
    """Sua danh sach tra ve khong duoc dong toi so that."""
    so = SoNhatKy()
    so.ghi("muc", luc=LUC)
    ds = so.gan_day(5)
    ds.clear()
    assert len(so.muc) == 1


# ------------------------------------------------- xuat

def test_dong_co_gio_va_noi_dung():
    d = Muc(luc=LUC, noi_dung="hôm nay khó vào việc").dong()
    assert "2026-09-15" in d
    assert "09:30" in d
    assert "hôm nay khó vào việc" in d


def test_dong_co_the_nao_khi_nguoi_dung_ghi():
    d = Muc(luc=LUC, noi_dung="ghi chú", the_nao="mệt").dong()
    assert "mệt" in d


def test_xuat_gom_moi_muc_theo_thu_tu():
    so = SoNhatKy()
    for i in range(3):
        so.ghi(f"muc {i}", luc=LUC + i * 60)
    dong = so.xuat_van_ban().strip().split("\n")
    assert len(dong) == 3
    assert "muc 0" in dong[0] and "muc 2" in dong[2]


def test_so_trong_thi_xuat_ra_chuoi_rong():
    assert SoNhatKy().xuat_van_ban() == ""


def test_xuat_TRA_VE_CHUOI_chu_khong_ghi_tep():
    """
    Nguoi dung quyet dinh chuoi nay di dau - ke ca khi cau tra loi la
    khong di dau ca. Xem docs/FLOWY_THIET_KE.md muc 4.3(b).
    """
    so = SoNhatKy()
    so.ghi("muc", luc=LUC)
    assert isinstance(so.xuat_van_ban(), str)


def test_ban_xuat_KHONG_co_nhan_xet_nao_cua_app():
    """Ban xuat la so cua nguoi dung, khong phai bao cao cua app."""
    so = SoNhatKy()
    so.ghi("hôm nay khó vào việc", the_nao="mệt", luc=LUC)
    s = so.xuat_van_ban().lower()
    for xau in ("tổng", "trung bình", "xu hướng", "nhận xét", "kết luận",
                "điểm", "so với", "tuần này", "bạn nên"):
        assert xau not in s, s


# ------------------------------ nhung thu module KHONG duoc co

def test_KHONG_co_phep_tinh_tong_hop_nao():
    """
    Khong trung binh, khong xu huong, khong "tuan nay ban kem hon tuan
    truoc". Cho nao app quy mot ghi chep ve mot thang do lam sang, cho
    do no vuot ranh gioi thiet bi y te.
    """
    so = SoNhatKy()
    so.ghi("muc", the_nao="mệt", luc=LUC)
    for ten in ("trung_binh", "diem", "cham_diem", "tong", "xu_huong",
                "thong_ke", "muc_do", "danh_gia", "bieu_do", "phan_tich"):
        assert not hasattr(so, ten), ten


def test_muc_KHONG_co_truong_diem_so():
    m = Muc(luc=LUC, noi_dung="muc")
    for ten in ("diem", "muc_do", "thang", "so_diem", "nang_nhe"):
        assert not hasattr(m, ten), ten


def test_module_KHONG_tu_ghi_ra_dia():
    """
    Nhat ky cam xuc la du lieu ca nhan nhay cam. Xem bang trong
    loi_chung/bridge.py: no khong duoc di qua cau noi, va laptop khong
    ghi gi xuong dia.
    """
    src = (Path(__file__).resolve().parents[2] / "wayfinding" / "adhd"
           / "nhatky.py").read_text(encoding="utf-8")
    for xau in ("open(", "write_text", "Path(", "os.path", "pathlib"):
        assert xau not in src, f"module tu ghi ra dia: {xau}"


def test_module_KHONG_goi_mang():
    """App khong gui nhat ky cho ai. Buoc do nam trong tay nguoi dung."""
    src = (Path(__file__).resolve().parents[2] / "wayfinding" / "adhd"
           / "nhatky.py").read_text(encoding="utf-8")
    for xau in ("import socket", "urllib", "requests", "http"):
        assert xau not in src, f"module goi mang: {xau}"


# ------------------------------------------------- luu va doc

def test_luu_roi_doc_lai_giu_nguyen():
    so = SoNhatKy()
    so.ghi("muc mot", the_nao="mệt", luc=LUC)
    so.ghi("muc hai", luc=LUC + 60)
    lai = SoNhatKy.from_json(so.to_json())
    assert [m.noi_dung for m in lai.muc] == ["muc mot", "muc hai"]
    assert lai.muc[0].the_nao == "mệt"
    assert lai.muc[1].the_nao is None
    assert lai.muc[0].luc == LUC


def test_so_hong_thi_bat_dau_lai_chu_khong_lam_sap():
    assert SoNhatKy.from_json(None).muc == []
    assert SoNhatKy.from_json({"x": 1}).muc == []
    assert SoNhatKy.from_json([{"thieu_khoa": 1}]).muc == []


def test_muc_hong_le_khong_lam_mat_muc_con_lai():
    so = SoNhatKy.from_json([
        {"luc": LUC, "noi_dung": "muc mot"},
        {"hong": True},
        {"luc": LUC + 60, "noi_dung": "muc hai"}])
    assert [m.noi_dung for m in so.muc] == ["muc mot", "muc hai"]
