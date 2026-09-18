"""
Kiem thu chong rung (stabilize.py).

Hai nhom:
  - Vat ly cach deo: kiem tra cong thuc con lac va canh bao cong huong.
  - Loc khung hinh: kiem tra cong do net va cong chuyen dong that su bo
    duoc khung hinh nhoe ma khong bo nham khung hinh net.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.khiemthi.stabilize import (
    BestOfBurst, DEFAULT_GYRO_LIMIT, MotionGate, SharpnessGate,
    blur_from_rotation, gait_sway_band, gyro_limit_for, mount_advice,
    pendulum_frequency, resonance_risk, sharpness,
)

W, H = 640, 480


def textured(seed=3):
    rng = np.random.default_rng(seed)
    img = np.full((H, W), 40, dtype=np.uint8)
    for _ in range(150):
        x = int(rng.integers(20, W - 20))
        y = int(rng.integers(20, H - 20))
        img[y - 5:y + 5, x - 5:x + 5] = 235
    return img


def blurred(img, k=15):
    return cv2.GaussianBlur(img, (k, k), 0)


# ==================== vat ly cach deo ====================

def test_con_lac_ngan_dao_dong_nhanh_hon():
    assert pendulum_frequency(0.15) > pendulum_frequency(0.45)


def test_cong_thuc_con_lac_dung():
    f = pendulum_frequency(0.25)
    assert f == pytest.approx(math.sqrt(9.81 / 0.25) / (2 * math.pi))
    assert f == pytest.approx(1.00, abs=0.02)


def test_khoi_luong_khong_anh_huong():
    """
    Chu ky con lac KHONG phu thuoc khoi luong - nen treo them vat nang
    cho 'on dinh hon' la vo ich, chi moi co them.
    Ham chi nhan chieu dai, day la cach ma hoa dieu do vao API.
    """
    import inspect

    params = inspect.signature(pendulum_frequency).parameters
    assert list(params) == ["length_m"]


def test_neo_cung_thi_khong_co_mode_con_lac():
    assert pendulum_frequency(0.0) == float("inf")


def test_dai_lac_khi_di_bo_bang_nua_nhip_buoc():
    lo, hi = gait_sway_band(120.0)      # 2 buoc/giay
    assert lo < 1.0 < hi                # lac ngang ~1 Hz


def test_day_25_35cm_roi_dung_vung_cong_huong():
    """
    Phat hien chinh: day deo do dai thong thuong CONG HUONG voi nhip di.

    Kiem tra bang SO SANH chu khong bang mot nguong tuy tien: day deo
    thong thuong phai rui ro hon han day rat ngan va neo cung.
    """
    thong_thuong = max(resonance_risk(0.25), resonance_risk(0.35))
    rat_ngan = resonance_risk(0.08)

    assert thong_thuong > 0.4
    assert thong_thuong > rat_ngan * 3
    assert resonance_risk(0.0) == 0.0

    # Va tan so that su nam trong dai lac khi di bo
    lo, hi = gait_sway_band()
    assert lo <= pendulum_frequency(0.25) <= hi or \
           lo <= pendulum_frequency(0.35) <= hi


def test_day_rat_ngan_thoat_vung_cong_huong():
    assert resonance_risk(0.10) < resonance_risk(0.30)


def test_neo_cung_khong_co_rui_ro_cong_huong():
    assert resonance_risk(0.0) == 0.0


def test_loi_khuyen_canh_bao_day_dai_tu_do():
    text = mount_advice(0.30, two_point=False)
    assert "NGUY HIEM" in text or "Can chinh" in text
    assert "day thun" in text or "15cm" in text


def test_loi_khuyen_chap_nhan_neo_hai_diem():
    text = mount_advice(0.30, two_point=True)
    assert "khong con mode con lac" in text
    assert "NGUY HIEM" not in text


def test_loi_khuyen_neu_ro_con_so():
    text = mount_advice(0.35, two_point=False)
    assert "35cm" in text and "Hz" in text


# ==================== do do net ====================

def test_anh_net_cho_diem_cao_hon_anh_nhoe():
    img = textured()
    assert sharpness(img) > sharpness(blurred(img))


def test_cang_nhoe_diem_cang_thap():
    img = textured()
    assert sharpness(blurred(img, 9)) > sharpness(blurred(img, 25))


def test_do_net_chay_duoc_voi_anh_mau():
    img = cv2.cvtColor(textured(), cv2.COLOR_GRAY2BGR)
    assert sharpness(img) > 0


def test_anh_tron_cho_diem_gan_khong():
    assert sharpness(np.full((H, W), 128, np.uint8)) < 1.0


# ==================== cong do net ====================

def test_cong_do_net_cho_qua_giai_doan_khoi_dong():
    """Chua du du lieu thi khong duoc bo, tranh bo sot luc vua bat dau."""
    gate = SharpnessGate(warmup=5)
    for _ in range(5):
        assert gate.accept(10.0)
    assert gate.rejected == 0


def test_cong_do_net_bo_khung_hinh_nhoe():
    gate = SharpnessGate(warmup=2, ratio=0.5)
    for _ in range(4):
        gate.accept(100.0)
    assert not gate.accept(10.0)        # qua nhoe so voi muc gan day


def test_cong_do_net_giu_khung_hinh_net():
    gate = SharpnessGate(warmup=2, ratio=0.5)
    for _ in range(4):
        gate.accept(100.0)
    assert gate.accept(95.0)


def test_cong_do_net_tu_dieu_chinh_theo_canh():
    """
    Hanh lang tuong tron cho gia tri do net thap han. Nguong cung se bo
    het o do; nguong tu dieu chinh thi van hoat dong.
    """
    gate = SharpnessGate(warmup=2, ratio=0.5)
    for _ in range(6):                  # canh toi, gia tri thap
        gate.accept(8.0)
    assert gate.accept(7.0)             # van la net so voi boi canh do


def test_cong_do_net_lam_viec_voi_anh_that():
    img = textured()
    gate = SharpnessGate(warmup=3, ratio=0.5)
    for _ in range(5):
        gate.accept_frame(img)
    assert not gate.accept_frame(blurred(img, 25))


def test_cong_do_net_thong_ke_ty_le_bo():
    gate = SharpnessGate(warmup=1, ratio=0.5)
    gate.accept(100.0)
    for _ in range(3):
        gate.accept(1.0)
    assert gate.reject_ratio > 0.5


def test_cong_do_net_reset():
    gate = SharpnessGate(warmup=1)
    gate.accept(100.0)
    gate.accept(1.0)
    gate.reset()
    assert gate.seen == 0 and gate.rejected == 0


# ==================== cong chuyen dong ====================

def test_cong_chuyen_dong_bo_khi_xoay_nhanh():
    gate = MotionGate(limit_dps=30.0)
    assert gate.accept(10.0)
    assert not gate.accept(80.0)


def test_cong_chuyen_dong_khong_phan_biet_chieu_xoay():
    gate = MotionGate(limit_dps=30.0)
    assert gate.accept(-10.0)
    assert not gate.accept(-80.0)


def test_cong_chuyen_dong_nhan_vector_ba_truc():
    gate = MotionGate(limit_dps=30.0)
    assert gate.accept_vector(3.0, 4.0, 0.0)       # do lon 5
    assert not gate.accept_vector(30.0, 40.0, 0.0)  # do lon 50


def test_cong_chuyen_dong_re_hon_do_do_net():
    """
    Cong chuyen dong chi doc mot con so, khong xu ly anh. Nen chay no
    TRUOC de bot viec cho buoc do do net.
    """
    import inspect

    src = inspect.getsource(MotionGate.accept)
    assert "cv2" not in src and "Laplacian" not in src


# ==================== nhoe do xoay ====================

def test_nhoe_ty_le_thuan_voi_van_toc_goc():
    a = blur_from_rotation(10.0, 16.0, 1280, 62.0)
    b = blur_from_rotation(20.0, 16.0, 1280, 62.0)
    assert b == pytest.approx(2 * a)


def test_nhoe_ty_le_thuan_voi_thoi_gian_phoi_sang():
    a = blur_from_rotation(20.0, 8.0, 1280, 62.0)
    b = blur_from_rotation(20.0, 16.0, 1280, 62.0)
    assert b == pytest.approx(2 * a)


def test_nguong_gyro_va_do_nhoe_la_hai_chieu_nguoc_nhau():
    limit = gyro_limit_for(7.0, 16.0, 1280, 62.0)
    assert blur_from_rotation(limit, 16.0, 1280, 62.0) == pytest.approx(7.0)


def test_nguong_mac_dinh_hop_ly_o_16ms():
    """Nguong mac dinh phai tuong ung voi do nhoe chap nhan duoc."""
    blur = blur_from_rotation(DEFAULT_GYRO_LIMIT, 16.0, 1280, 62.0)
    assert 5.0 < blur < 15.0


def test_phoi_sang_ngan_cho_phep_xoay_nhanh_hon():
    """Day la ly do rut ngan phoi sang la don bay manh nhat."""
    assert gyro_limit_for(7.0, 4.0, 1280, 62.0) > \
           gyro_limit_for(7.0, 33.0, 1280, 62.0)


# ==================== chon khung net nhat ====================

def test_chum_tra_ve_khung_net_nhat():
    burst = BestOfBurst(size=3)
    assert burst.push("nhoe", 1.0) is None
    assert burst.push("net", 100.0) is None
    assert burst.push("hoi nhoe", 20.0) == "net"


def test_chum_reset_sau_moi_lan_tra_ve():
    burst = BestOfBurst(size=2)
    burst.push("a", 1.0)
    assert burst.push("b", 2.0) == "b"
    assert burst.push("c", 1.0) is None      # chum moi bat dau lai


def test_chum_flush_lay_khung_dang_do_dang():
    burst = BestOfBurst(size=5)
    burst.push("a", 1.0)
    burst.push("b", 9.0)
    assert burst.flush() == "b"
    assert burst.flush() is None


def test_chum_kich_thuoc_mot_thi_tra_ve_ngay():
    burst = BestOfBurst(size=1)
    assert burst.push("a", 1.0) == "a"


def test_chum_giup_nguoi_run_tay():
    """
    Voi nguoi run tay, khung hinh net va nhoe xen ke. Gom chum roi chon
    cai net nhat cho ket qua tot hon han xu ly khung hinh bat ky.
    """
    burst = BestOfBurst(size=3)
    frames = [("f1", 5.0), ("f2", 90.0), ("f3", 8.0),
              ("f4", 6.0), ("f5", 85.0), ("f6", 7.0)]
    picked = [burst.push(f, s) for f, s in frames]
    chosen = [p for p in picked if p is not None]
    assert chosen == ["f2", "f5"]
