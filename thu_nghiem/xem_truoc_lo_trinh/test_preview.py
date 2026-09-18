"""
Kiem thu lop xem truoc hanh trinh.

Trong tam KHONG phai "co doc duoc lo trinh khong" - ma la KHONG DOC QUA
NHIEU MOT LUC. Doc ca lo trinh mot mach se vuot dung luong tri nho lam
viec, va lam kho dung nhom nguoi ma tinh nang nay dinh phuc vu.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.loi_chung.floormap import load_map
from wayfinding.adhd.preview import (TOI_DA_MOI_CAU, PhienXemTruoc,
                                cau_chang, cau_tom_tat,
                                tom_tat, uoc_phut)
from wayfinding.loi_chung.routing import build_route

MAP = Path(__file__).resolve().parents[2] / "config" / "map_floor3.json"

DAU = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
          "ùúủũụưừứửữựỳýỷỹỵđ")


@pytest.fixture(scope="module")
def fm():
    return load_map(MAP)


@pytest.fixture
def route(fm):
    return build_route(fm, "A", "R12")


# ------------------------------------------------------------------
# Tom tat - MOT cau, duoi bon don vi thong tin
# ------------------------------------------------------------------

def test_tom_tat_la_mot_cau(route):
    c = cau_tom_tat(route)
    assert c is not None and c.count(".") <= 2


def test_tom_tat_khong_qua_bon_don_vi(route):
    """
    Gioi han Cowan la bon don vi. Vuot qua thi nguoi dung mat phan giua,
    va do la dung nhom nguoi tinh nang nay phuc vu.
    """
    c = cau_tom_tat(route)
    so_don_vi = c.count(",") + 1
    assert so_don_vi <= TOI_DA_MOI_CAU


def test_tom_tat_co_dau_tieng_viet(route):
    assert any(ch in DAU for ch in cau_tom_tat(route).lower())


def test_tom_tat_noi_SO_LUONG_chu_khong_phai_chi_tiet(route):
    """
    "Con ba chang nua" huu ich hon "re phai roi di thang roi re trai":
    no cho nguoi dung mot cai KHUNG de gan thong tin vao.
    """
    c = cau_tom_tat(route)
    assert "phút" in c
    assert "rẽ trái" not in c and "rẽ phải" not in c


def test_nguy_hiem_duoc_neu_NGAY_o_tom_tat(fm):
    """
    Khong doi nguoi dung hoi tiep moi noi - ho co the khong hoi.
    """
    r = build_route(fm, "A", "R12")
    if any(l.hazard for l in r.legs):
        assert "chú ý" in cau_tom_tat(r)


def test_tuyen_rong_tra_None():
    assert cau_tom_tat(None) is None
    assert tom_tat(None) is None


# ------------------------------------------------------------------
# Uoc thoi gian
# ------------------------------------------------------------------

def test_uoc_phut_duong_tinh(route):
    assert uoc_phut(route) > 0


def test_doi_tang_ton_them_thoi_gian(fm):
    """
    Moi lan doi tang ton nhieu thoi gian hon ca doan hanh lang dan toi
    no: goi thang may, cho, vao cabin, di chuyen.
    """
    r = build_route(fm, "A", "R12")
    thuan_quang_duong = r.total_length / 0.8 / 60.0
    assert uoc_phut(r) > thuan_quang_duong


# ------------------------------------------------------------------
# Tung chang - luon noi CON BAO NHIEU
# ------------------------------------------------------------------

def test_moi_chang_noi_con_bao_nhieu(route):
    """
    Con so o cuoi cau khong phai trang tri: no cho nguoi dung biet minh
    dang o dau trong hanh trinh, va do la thu giam lo au.
    """
    for i in range(len(route.legs)):
        c = cau_chang(route, i)
        assert "Còn" in c or "chặng cuối" in c


def test_chang_cuoi_noi_ro_la_cuoi(route):
    assert "chặng cuối" in cau_chang(route, len(route.legs) - 1)


def test_chang_ngoai_pham_vi_tra_None(route):
    assert cau_chang(route, -1) is None
    assert cau_chang(route, 999) is None


def test_chang_co_dau_tieng_viet(route):
    assert any(ch in DAU for ch in cau_chang(route, 0).lower())


# ------------------------------------------------------------------
# Phien xem truoc - doc THEO YEU CAU
# ------------------------------------------------------------------

def test_bat_dau_chi_doc_tom_tat(route):
    """
    KHONG doc ca lo trinh mot mach. Day la diem thiet ke quan trong
    nhat cua module nay.
    """
    p = PhienXemTruoc(route)
    dau = p.bat_dau()
    for l in route.legs[1:]:
        assert l.to.name not in dau


def test_bat_dau_co_moi_nghe_tiep(route):
    assert "không?" in PhienXemTruoc(route).bat_dau()


def test_tiep_doc_tung_chang_mot(route):
    p = PhienXemTruoc(route)
    p.bat_dau()
    dem = 0
    while (c := p.tiep()) is not None:
        dem += 1
        assert c.count(".") <= 3        # mot chang = mot cau ngan
    assert dem == len(route.legs)


def test_het_chang_thi_tra_None(route):
    p = PhienXemTruoc(route)
    p.bat_dau()
    while p.tiep() is not None:
        pass
    assert p.tiep() is None


def test_lap_lai_doc_lai_chang_vua_roi(route):
    """
    Nguoi co kho khan ve tri nho lam viec se bo lo mot cau va KHONG the
    tua vao viec doc lai man hinh nhu nguoi sang mat.
    """
    p = PhienXemTruoc(route)
    p.bat_dau()
    a = p.tiep()
    assert p.lap_lai() == a


def test_lap_lai_truoc_khi_bat_dau_tra_tom_tat(route):
    assert "Lộ trình" in PhienXemTruoc(route).lap_lai()
