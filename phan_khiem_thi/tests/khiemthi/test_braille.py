"""
Kiem thu lop xac nhan bang bien chu noi.

Gom hai ca nghiem thu cua dac ta muc 4.3, cong cac ca cho HAI LOP PHONG
THU ma dac ta goc chua co - doc lai xac nhan, va kiem ban kinh.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.khiemthi.braille import (BAN_KINH_HOP_LY_M, ChoXacNhan, LoiMoi,
                                MocBraille, chuan_hoa_so, nen_moi,
                                nghe_so_phong, xac_nhan)
from wayfinding.loi_chung.geometry import Pose2D


# ------------------------------------------------------------------
# Ban do gia lap, dung dung so cua dac ta 4.3
# ------------------------------------------------------------------

class _Nut:
    def __init__(self, x: float, y: float):
        self.x, self.y = x, y


class _BanDoGia:
    """Phong 604 tai (12,0; 4,0) - dung ca nghiem thu cua dac ta."""

    rooms = {"604": None, "3.12": None}

    def room_node(self, phong: str):
        return {"604": _Nut(12.0, 4.0),
                "3.12": _Nut(24.0, 12.9)}.get(phong)


BD = _BanDoGia()


# ------------------------------------------------------------------
# Chuan hoa so tieng Viet
# ------------------------------------------------------------------

@pytest.mark.parametrize("cau,mong", [
    ("sáu lẻ tư", "604"),              # cach doc pho bien nhat
    ("sáu trăm lẻ bốn", "604"),
    ("sáu không bốn", "604"),
    ("604", "604"),                    # ASR tra thang chu so
    ("ba chấm mười hai", "3.12"),
    ("ba chấm một hai", "3.12"),
    ("mười hai", "12"),
    ("hai mươi", "20"),
    ("hai mươi mốt", "21"),
])
def test_chuan_hoa_so(cau: str, mong: str):
    assert chuan_hoa_so(cau) == mong


def test_muoi_va_muoi_phan_biet_bang_ngu_canh():
    """
    Bo dau xong thi 'muoi' (10) va 'muoi' (chuc) trung nhau. Day la cho
    de sai nhat trong ca module.
    """
    assert chuan_hoa_so("mười hai") == "12"     # dau chuoi -> 10
    assert chuan_hoa_so("hai mươi") == "20"     # sau chu so -> hang chuc


@pytest.mark.parametrize("cau", ["xin chào", "", "   ", "ừ thì"])
def test_khong_ra_so_thi_tra_None(cau: str):
    """Im lang con hon doan - nguyen tac 1.1."""
    assert chuan_hoa_so(cau) is None


# ------------------------------------------------------------------
# Nghiem thu cua dac ta 4.3
# ------------------------------------------------------------------

def test_nghiem_thu_phong_co_trong_ban_do():
    """
    Dac ta: floor_map co phong 604 tai (12,0; 4,0); dau vao giong noi
    'sau le tu'; ky vong moc tai dung toa do do, tin cay HIGH.
    """
    cho = nghe_so_phong("sáu lẻ tư", Pose2D(11.0, 4.0, 0.0), BD)
    assert isinstance(cho, ChoXacNhan)
    assert cho.phong == "604"
    assert (cho.x, cho.y) == (12.0, 4.0)

    moc = xac_nhan("đúng", cho, Pose2D(11.0, 4.0, 0.0))
    assert isinstance(moc, MocBraille)
    assert moc.confidence == "HIGH"
    assert moc.kind == "braille"
    assert (moc.x, moc.y) == (12.0, 4.0)


def test_nghiem_thu_phong_khong_co_trong_ban_do():
    """Dac ta: 'chin chin chin' -> None kem mot cau bao loi."""
    ra = nghe_so_phong("chín chín chín", Pose2D(11.0, 4.0, 0.0), BD)
    assert isinstance(ra, str)
    assert "Không tìm thấy" in ra


# ------------------------------------------------------------------
# LOP PHONG THU 1 - doc lai xac nhan
# ------------------------------------------------------------------

def test_khong_tra_moc_ngay_ma_phai_doc_lai():
    """
    Buoc nghe KHONG duoc tra moc. Loi ASR phai lo ra truoc khi pose bi
    sua - do la ly do ton tai cua lop nay.
    """
    ra = nghe_so_phong("sáu lẻ tư", Pose2D(11.0, 4.0, 0.0), BD)
    assert not isinstance(ra, MocBraille)
    assert isinstance(ra, ChoXacNhan)
    assert "604" in ra.text and "đúng không" in ra.text


def test_nguoi_dung_phu_dinh_thi_khong_co_moc():
    cho = nghe_so_phong("sáu lẻ tư", Pose2D(11.0, 4.0, 0.0), BD)
    assert xac_nhan("không phải", cho, Pose2D(11.0, 4.0, 0.0)) is None


def test_im_lang_thi_khong_co_moc():
    """Nguoi dung LUON duoc phep tu choi. Im lang la mot cau tra loi."""
    cho = nghe_so_phong("sáu lẻ tư", Pose2D(11.0, 4.0, 0.0), BD)
    assert xac_nhan("", cho, Pose2D(11.0, 4.0, 0.0)) is None


def test_tra_loi_mo_ho_coi_nhu_khong_dong_y():
    """Khong ro thi khong sua pose - nguyen tac 1.1."""
    cho = nghe_so_phong("sáu lẻ tư", Pose2D(11.0, 4.0, 0.0), BD)
    assert xac_nhan("ờ thì", cho, Pose2D(11.0, 4.0, 0.0)) is None


# ------------------------------------------------------------------
# LOP PHONG THU 2 - kiem ban kinh
# ------------------------------------------------------------------

def test_phong_qua_xa_thi_tu_choi_du_da_dong_y():
    """
    Ca ma lop 1 KHONG bat duoc: nguoi dung doc dung, nghe dung, dong y
    dung - nhung uoc tinh vi tri dang o rat xa phong do. Luc do hoac
    ASR sai hoac VIO da troi qua nhieu, va ca hai deu khong nen
    teleport pose.
    """
    cho = nghe_so_phong("sáu lẻ tư", Pose2D(11.0, 4.0, 0.0), BD)
    xa = Pose2D(12.0 + BAN_KINH_HOP_LY_M + 5.0, 4.0, 0.0)
    ra = xac_nhan("đúng", cho, xa)
    assert isinstance(ra, str)
    assert "quá xa" in ra


def test_trong_ban_kinh_thi_chap_nhan():
    cho = nghe_so_phong("sáu lẻ tư", Pose2D(11.0, 4.0, 0.0), BD)
    gan = Pose2D(12.0 + BAN_KINH_HOP_LY_M - 1.0, 4.0, 0.0)
    assert isinstance(xac_nhan("đúng", cho, gan), MocBraille)


def test_moc_qua_ca_hai_lop_moi_duoc_vuot_nguong_nhay():
    """
    Chi moc da qua CA HAI lop moi duoc phep sua pose vuot nguong nhay
    thong thuong. Day la dac quyen nguy hiem nhat trong he.
    """
    cho = nghe_so_phong("sáu lẻ tư", Pose2D(11.0, 4.0, 0.0), BD)
    moc = xac_nhan("đúng", cho, Pose2D(11.0, 4.0, 0.0))
    assert moc.vuot_nguong_nhay is True


# ------------------------------------------------------------------
# Khi nao moi hoi
# ------------------------------------------------------------------

def test_chi_moi_khi_dang_lac():
    """Dang dinh vi tot thi khong hoi - khong duoc bien thanh thu phien."""
    assert nen_moi(Pose2D(12.0, 4.0, 0.0), False, BD) is None


def test_chi_moi_khi_gan_mot_cua_da_biet():
    """Giua hanh lang thi khong co bien de so."""
    assert nen_moi(Pose2D(100.0, 100.0, 0.0), True, BD) is None


def test_moi_khi_lac_va_gan_cua():
    loi = nen_moi(Pose2D(12.5, 4.0, 0.0), True, BD)
    assert isinstance(loi, LoiMoi)
    # Phai neu ro BEN NAO va TAM CAO NAO - nguoi dung khong nhin thay
    assert "bên phải" in loi.text.lower()
    assert "tầm tay" in loi.text.lower()


def test_cau_moi_co_dau_tieng_viet():
    """Cau nay duoc doc len, nen bat buoc co dau."""
    loi = nen_moi(Pose2D(12.5, 4.0, 0.0), True, BD)
    dau = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
              "ùúủũụưừứửữựỳýỷỹỵđ")
    assert any(c in dau for c in loi.text.lower())


# ------------------------------------------------------------------
# "khong" - so 0 hay tu phu dinh
# ------------------------------------------------------------------

@pytest.mark.parametrize("cau", [
    "không nghe rõ gì",
    "không phải",
    "không biết",
    "không",
])
def test_tu_phu_dinh_khong_bi_hieu_thanh_so_0(cau: str):
    """
    Loi nguy hiem nhat cua lop nay neu lam au: "khong" vua la SO 0 vua
    la tu PHU DINH. Tinh no la so thi moi cau TU CHOI cua nguoi dung
    deu bien thanh mot lan khai bao so phong.
    """
    assert chuan_hoa_so(cau) is None


def test_so_that_co_chu_so_khong_van_doc_duoc():
    """Chan tu phu dinh nhung khong duoc bo sot so that co chu so 0."""
    assert chuan_hoa_so("sáu không bốn") == "604"
    assert chuan_hoa_so("ba không hai") == "302"
