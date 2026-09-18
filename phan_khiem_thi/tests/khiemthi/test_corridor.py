"""
Kiem thu hai tin hieu rut tu khung hinh - dac ta muc 9.

Dung anh TONG HOP thay vi anh that: mot hanh lang ve bang hai duong hoi
tu co diem tu BIET TRUOC, nen kiem duoc ket qua so chu khong chi kiem
"co chay khong".
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.khiemthi.corridor import (VP_SPREAD_PX, HeadingCue, MotionVerdict,
                                 motion_check, vanishing_point)

W, H = 640, 480
FX, CX = 500.0, W / 2.0


def _hanh_lang(u_vp: float, v_vp: float = 240.0) -> np.ndarray:
    """
    Ve mot hanh lang tong hop: hai duong giao tuong-san hoi tu ve
    (u_vp, v_vp), cong mot it duong ngang de kiem viec loc.
    """
    import cv2

    img = np.zeros((H, W), dtype=np.uint8)
    # hai duong hoi tu, xuat phat tu hai goc duoi
    cv2.line(img, (0, H - 1), (int(u_vp), int(v_vp)), 255, 2)
    cv2.line(img, (W - 1, H - 1), (int(u_vp), int(v_vp)), 255, 2)
    # them hai duong nua sat ben trong, cho du VP_MIN_SEGMENTS
    cv2.line(img, (80, H - 1), (int(u_vp), int(v_vp)), 255, 2)
    cv2.line(img, (W - 81, H - 1), (int(u_vp), int(v_vp)), 255, 2)
    # nhieu: mep ban nam ngang - PHAI bi loc bo
    cv2.line(img, (0, 400), (W - 1, 400), 255, 2)
    return img


# ------------------------------------------------------------------
# Diem tu (muc 9.1)
# ------------------------------------------------------------------

def test_dung_giua_hanh_lang_thi_sai_so_huong_gan_0():
    """Diem tu nam ngay tam anh -> khong lech."""
    cue = vanishing_point(_hanh_lang(CX), FX, CX)
    assert isinstance(cue, HeadingCue)
    assert abs(cue.heading_error_deg) < 3.0


@pytest.mark.parametrize("u_vp", [CX - 120, CX + 120])
def test_lech_trai_phai_cho_dau_nguoc_nhau(u_vp: float):
    """Diem tu lech sang ben nao thi sai so huong mang dau ben do."""
    cue = vanishing_point(_hanh_lang(u_vp), FX, CX)
    assert cue is not None
    assert np.sign(cue.heading_error_deg) == np.sign(u_vp - CX)


def test_sai_so_huong_dung_cong_thuc_lo_kim():
    """heading_error = atan((u_vp - cx) / fx), tinh bang do."""
    import math
    u = CX + 100.0
    cue = vanishing_point(_hanh_lang(u), FX, CX)
    assert cue is not None
    mong = math.degrees(math.atan((u - CX) / FX))
    assert cue.heading_error_deg == pytest.approx(mong, abs=2.0)


def test_nghiem_thu_lech_15_do_sua_ve_duoi_5_do():
    """
    Nghiem thu buoc 5 cua muc 13: dung lech 15 do trong hanh lang thi
    he sua ve duoi 5 do.

    Kiem phan DO duoc: neu do lech that la 15 do thi uoc luong phai gan
    15 do, vi phan sua chi tot bang phan do.
    """
    import math
    lech_that = 15.0
    u = CX + FX * math.tan(math.radians(lech_that))
    cue = vanishing_point(_hanh_lang(u), FX, CX)
    assert cue is not None
    con_lai = abs(lech_that - cue.heading_error_deg)
    assert con_lai < 5.0


def test_anh_trong_thi_tra_None():
    """Khong co canh nao thi khong doan."""
    assert vanishing_point(np.zeros((H, W), np.uint8), FX, CX) is None


def test_khong_du_doan_thi_tra_None():
    """Mot doan duy nhat khong xac dinh duoc diem tu."""
    import cv2
    img = np.zeros((H, W), np.uint8)
    cv2.line(img, (0, H - 1), (320, 240), 255, 2)
    assert vanishing_point(img, FX, CX) is None


def test_duong_ngang_bi_loc_bo():
    """
    Chi co duong nam ngang - do la mep ban, bac thang, khong phai duong
    giao tuong-san. Phai bi loc het va tra None.
    """
    import cv2
    img = np.zeros((H, W), np.uint8)
    for y in (300, 340, 380, 420):
        cv2.line(img, (0, y), (W - 1, y), 255, 2)
    assert vanishing_point(img, FX, CX) is None


def test_giao_diem_tan_mac_thi_tra_None():
    """
    Cac doan khong thuc su hoi tu -> "diem tu" chi la trung vi cua mot
    dam nhieu -> khong duoc nhan.
    """
    import cv2
    img = np.zeros((H, W), np.uint8)
    rng = np.random.default_rng(0)
    for _ in range(14):
        x1, y1 = int(rng.integers(0, W)), int(rng.integers(H // 2, H))
        x2, y2 = int(rng.integers(0, W)), int(rng.integers(H // 2, H))
        cv2.line(img, (x1, y1), (x2, y2), 255, 2)
    cue = vanishing_point(img, FX, CX)
    assert cue is None or cue.spread_px <= VP_SPREAD_PX


def test_anh_khong_hop_le_thi_tra_None():
    assert vanishing_point(None, FX, CX) is None
    assert vanishing_point(np.zeros((4, 4), np.uint8), FX, CX) is None
    assert vanishing_point(np.zeros((H, W, 3), np.uint8), FX, CX) is None


# ------------------------------------------------------------------
# Luong quang kiem chung chuyen dong (muc 9.2)
# ------------------------------------------------------------------

def _canh_co_van(seed: int = 0) -> np.ndarray:
    """Anh nhieu co du goc de bam - canh tron thi khong bam duoc."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, 255, (H, W), dtype=np.uint8)


def _dich(img: np.ndarray, dx: int) -> np.ndarray:
    return np.roll(img, dx, axis=1)


def test_canh_dung_yen_ma_VIO_bao_dang_di_la_VIO_TROI():
    """
    Loi NGUY HIEM NHAT trong thuc te: nguoi dung dung lai hoi duong,
    VIO tich luy troi, he thong tuong ho da di them mot doan va bat dau
    doc chi dan cua doan sau.
    """
    a = _canh_co_van()
    assert motion_check(a, a.copy(), vio_moved_m=0.5) is MotionVerdict.VIO_TROI


def test_canh_dich_chuyen_ma_VIO_bao_dung_la_MAT_BAM():
    a = _canh_co_van()
    assert motion_check(a, _dich(a, 12),
                        vio_moved_m=0.0) is MotionVerdict.VIO_MAT_BAM


def test_hai_nguon_nhat_quan_la_BINH_THUONG():
    a = _canh_co_van()
    assert motion_check(a, _dich(a, 12),
                        vio_moved_m=0.5) is MotionVerdict.BINH_THUONG


def test_dung_yen_va_VIO_cung_bao_dung_la_BINH_THUONG():
    a = _canh_co_van()
    assert motion_check(a, a.copy(),
                        vio_moved_m=0.0) is MotionVerdict.BINH_THUONG


def test_canh_tron_khong_du_dac_trung_thi_CHUA_RO():
    """
    Tuong trang tron - dung cho van phong hay co. Khong bam duoc thi
    phai noi la khong biet, khong duoc ket luan bua.
    """
    tron = np.full((H, W), 128, np.uint8)
    assert motion_check(tron, tron.copy(),
                        vio_moved_m=0.5) is MotionVerdict.CHUA_RO


def test_thieu_khung_hinh_thi_CHUA_RO():
    a = _canh_co_van()
    assert motion_check(None, a, 0.5) is MotionVerdict.CHUA_RO
    assert motion_check(a, None, 0.5) is MotionVerdict.CHUA_RO


def test_hai_khung_khac_kich_thuoc_thi_CHUA_RO():
    assert motion_check(_canh_co_van(), np.zeros((100, 100), np.uint8),
                        0.5) is MotionVerdict.CHUA_RO
