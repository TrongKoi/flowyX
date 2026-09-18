"""
Kiem thu lop nhan dien do vat.

Trong tam KHONG phai "co nhan ra khong" - viec do bo nhan dien cua nen
tang lo. Trong tam la CHON NOI GI: mot hanh lang cho ra hang chuc nhan
moi khung hinh, va noi het chung ra la bien he thong thanh may ke lien
mieng roi bi tat di.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.loi_chung.depth import DepthGrid
from wayfinding.loi_chung.objects import (MIN_DIEM, Muc, VatNhinThay, cau_canh_bao,
                                ghep, khoang_cach_cua, mo_ta)

COLS, ROWS = 4, 3


def g(d: float = 5.0, conf: float = 0.9) -> DepthGrid:
    return DepthGrid(cols=COLS, rows=ROWS,
                     depth=tuple([d] * 12), confidence=tuple([conf] * 12))


def vat(nhan: str, diem: float = 0.9,
        x0: float = 0.3, x1: float = 0.7) -> VatNhinThay:
    return VatNhinThay(nhan=nhan, diem=diem, x0=x0, y0=0.3, x1=x1, y1=0.8)


# ------------------------------------------------------------------
# Loc - phan quan trong nhat
# ------------------------------------------------------------------

def test_diem_thap_thi_bo_qua():
    """Nhan sai o day thanh cau noi sai, ma nguoi dung khong kiem lai duoc."""
    assert ghep([vat("chair", diem=MIN_DIEM - 0.1)], g(1.5)) == []


def test_nhan_la_thi_im_lang():
    """Khong co trong tu dien thi khong noi - khong doan ten."""
    assert ghep([vat("aardvark")], g(1.5)) == []


def test_vat_xa_khong_phai_can_duong():
    """Cai ghe o cuoi hanh lang khong phai chuong ngai."""
    assert ghep([vat("chair")], g(8.0)) == []


def test_vat_gan_la_can_duong():
    ds = ghep([vat("chair")], g(1.2))
    assert len(ds) == 1 and ds[0].muc is Muc.CAN_DUONG


def test_nguoi_duoc_ha_nguong():
    """
    Bao nham co nguoi chi hoi ngai. Khong bao ma dam vao thi nguy hiem.
    Danh doi co chu dich.
    """
    assert ghep([vat("person", diem=0.45)], g(1.5)) != []
    assert ghep([vat("chair", diem=0.45)], g(1.5)) == []


# ------------------------------------------------------------------
# Khong co do sau thi khong duoc canh bao va cham
# ------------------------------------------------------------------

def test_khong_co_do_sau_thi_khong_canh_bao_vat_can():
    """
    Bo nhan dien noi "co cai ghe" nhung khong biet cach bao xa. Canh
    bao sai cu ly con te hon khong canh bao.
    """
    assert ghep([vat("chair")], None) == []


def test_o_khong_dang_tin_thi_khong_tinh_khoang_cach():
    assert khoang_cach_cua(vat("chair"), g(1.0, conf=0.1)) is None


def test_moc_duong_van_noi_duoc_khi_khong_co_do_sau():
    """Cua va thang may co trong ban do, khong can do sau de huu ich."""
    ds = ghep([vat("door")], None)
    assert len(ds) == 1 and ds[0].muc is Muc.MOC_DUONG


# ------------------------------------------------------------------
# Khoang cach lay MEP GAN NHAT
# ------------------------------------------------------------------

def test_lay_o_gan_nhat_trong_hop_bao():
    """
    Cai can biet la mep gan nhat cua vat - do moi la cho nguoi dung dam
    vao. Trung vi cua mot cai ban dai se cho ra khoang cach toi giua
    ban, trong khi goc ban da o ngay truoc chan.
    """
    d = [5.0] * 12
    d[5] = 0.8                       # mot o rat gan trong hop bao
    grid = DepthGrid(COLS, ROWS, tuple(d), tuple([0.9] * 12))
    assert khoang_cach_cua(vat("table", x0=0.0, x1=1.0), grid) == pytest.approx(0.8)


# ------------------------------------------------------------------
# Uu tien
# ------------------------------------------------------------------

def test_can_duong_xep_truoc_moc_duong():
    ds = ghep([vat("door", x0=0.0, x1=0.3), vat("chair", x0=0.4, x1=0.6)], g(1.5))
    assert ds[0].muc is Muc.CAN_DUONG


def test_chi_noi_MOT_cau_moi_khung_hinh():
    """
    Muoi vat trong khung hinh van chi ra mot cau. Doc het la bien he
    thong thanh may ke lien mieng.
    """
    nhieu = [vat("chair"), vat("table"), vat("trash can"),
             vat("backpack"), vat("box")]
    cau = cau_canh_bao(nhieu, g(1.2))
    assert cau is not None and cau.count(".") == 1


def test_moc_duong_khong_tu_dong_noi():
    """Cua thi khong phai chuong ngai - khong cat ngang de bao."""
    assert cau_canh_bao([vat("door")], g(2.0)) is None


def test_khong_co_gi_thi_im_lang():
    assert cau_canh_bao([], g(5.0)) is None


# ------------------------------------------------------------------
# Cau noi
# ------------------------------------------------------------------

def test_cau_noi_co_dau_tieng_viet():
    """Chuoi duoc doc len - bo doc tieng Viet can dau day du."""
    cau = cau_canh_bao([vat("chair")], g(1.2))
    dau = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
              "ùúủũụưừứửữựỳýỷỹỵđ")
    assert any(c in dau for c in cau.lower())


def test_cau_noi_neu_ro_LA_CAI_GI():
    """
    Biet do la cai ghe hay mot nguoi thi nguoi dung xu ly khac han -
    ghe thi di vong, nguoi thi len tieng.
    """
    assert "ghế" in cau_canh_bao([vat("chair")], g(1.2))
    assert "người" in cau_canh_bao([vat("person")], g(1.2))


def test_cau_noi_dung_dau_phay_thap_phan():
    """Doc tieng Viet thi 1,2 met chu khong phai 1.2 met."""
    assert "1,2" in cau_canh_bao([vat("chair")], g(1.2))


@pytest.mark.parametrize("x0,x1,mong", [
    (0.0, 0.2, "bên trái"),
    (0.8, 1.0, "bên phải"),
    (0.45, 0.55, "phía trước"),
])
def test_noi_dung_ben(x0: float, x1: float, mong: str):
    assert mong in cau_canh_bao([vat("chair", x0=x0, x1=x1)], g(1.2))


def test_vat_hep_van_lay_duoc_khoang_cach():
    """
    Luoi 4x3 co tam o tai x = 0,125 / 0,375 / 0,625 / 0,875. Mot cot den
    hep (hop bao 0,45-0,55) khong chua tam o nao.

    Kiem theo tam o se lam vat hep khong bao gio co khoang cach, va vi
    khong co khoang cach thi bi bo qua hoan toan - cot den giua hanh
    lang la dung loai vat can nguy hiem nhat.
    """
    hep = VatNhinThay("chair", 0.9, x0=0.45, y0=0.4, x1=0.55, y1=0.6)
    assert khoang_cach_cua(hep, g(1.1)) == pytest.approx(1.1)
    assert cau_canh_bao([hep], g(1.1)) is not None
