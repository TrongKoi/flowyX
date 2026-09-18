"""
Kiem thu lop L4 - dung ban nen depth lam nguon vi tri (dac ta muc 10).

Ca nghiem thu cua dac ta 10.2 dung nguyen van: hanh lang thang 20m co
mot hoc tuong o met thu 7.

    - quan sat lay tai met 7  -> khop dung o do
    - quan sat lay tai met 3  -> KY VONG None

Ca thu hai quan trong hon ca thu nhat. Doan o mot doan hanh lang deu
tam tap chinh la kieu loi ma lop nay phai tu choi.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.khiemthi.backdrop import (MATCH_MARGIN_M, MATCH_MAX_ERR_M, Backdrop,
                                 BackdropFix)
from wayfinding.loi_chung.depth import DepthGrid
from wayfinding.loi_chung.geometry import Pose2D

COLS, ROWS = 4, 3
N = COLS * ROWS

# Hanh lang thang: tuong hai ben, phia truoc thong
THANG = [3.0, 6.0, 6.0, 3.0] * ROWS

# Cho co hoc tuong: tuong ben TRAI lui vao, nen depth phia do DAI hon.
#
# Hoc phai phu it nhat MOT NUA so o thi moi lo ra duoc - xem
# test_dac_trung_nho_hon_mot_nua_luoi_thi_vo_hinh ben duoi.
HOC = [5.2, 5.2, 6.0, 3.0] * ROWS


def g(depth: list[float], conf: float = 0.9) -> DepthGrid:
    return DepthGrid(cols=COLS, rows=ROWS,
                     depth=tuple(depth), confidence=tuple([conf] * N))


def _hanh_lang_20m() -> Backdrop:
    """
    Quet mot hanh lang thang doc truc x, tu met 0 den met 19.

    Moi met la mot o (cell_m mac dinh 1,0). Met thu 7 co hoc tuong.
    """
    bd = Backdrop()
    for m in range(20):
        pose = Pose2D(float(m) + 0.5, 0.5, 0.0)
        bd.observe(pose, g(HOC if m == 7 else THANG))
    return bd


# ------------------------------------------------------------------
# Ca 1 cua dac ta 10.2 - cho co net dac trung
# ------------------------------------------------------------------

def test_khop_dung_o_co_hoc_tuong():
    """Quan sat lay tai met 7 - ky vong khop dung o do."""
    bd = _hanh_lang_20m()
    fix = bd.match(Pose2D(7.5, 0.5, 0.0), g(HOC))

    assert isinstance(fix, BackdropFix)
    assert fix.x == pytest.approx(7.5)
    assert fix.err_m < MATCH_MAX_ERR_M


def test_khop_van_chay_khi_VIO_da_troi_vai_met():
    """
    Cong dung that cua lop nay: VIO da troi, va ban nen keo lai.

    Uoc tinh lech 3m so voi thuc te, nhung o co hoc tuong van la o duy
    nhat khop - nen van tim ra.
    """
    bd = _hanh_lang_20m()
    fix = bd.match(Pose2D(4.5, 0.5, 0.0), g(HOC), sigma_m=3.0)

    assert isinstance(fix, BackdropFix)
    assert fix.x == pytest.approx(7.5)


# ------------------------------------------------------------------
# Ca 2 cua dac ta 10.2 - doan deu, PHAI tu choi
# ------------------------------------------------------------------

def test_doan_hanh_lang_deu_thi_tra_None():
    """
    Ca quan trong nhat trong ca tep nay.

    Quan sat lay tai met 3 - doan thang deu, khong co net dac trung.
    Hang chuc o trong ban nen khop gan bang nhau, nen khong biet minh o
    o nao. DOAN LA TE HON KHONG SUA - nguyen tac 1.1.
    """
    bd = _hanh_lang_20m()
    assert bd.match(Pose2D(3.5, 0.5, 0.0), g(THANG)) is None


def test_nhap_nhang_thi_tu_choi_chu_khong_chon_bua():
    """
    Neu khong co quy tac "hon han o nhi" thi ham se chon bua mot o
    trong so hang chuc o khop bang nhau, va tra ve mot vi tri SAI voi
    ve ngoai tu tin. Do la cach hong nguy hiem nhat.
    """
    bd = _hanh_lang_20m()
    ra = bd.match(Pose2D(10.5, 0.5, 0.0), g(THANG))
    assert ra is None


# ------------------------------------------------------------------
# Cac dieu kien an toan khac
# ------------------------------------------------------------------

def test_khong_tim_toan_tang():
    """
    Chi tim quanh uoc tinh VIO. O co hoc tuong nam o met 7; dung o met
    19 thi no NGOAI ban kinh tim, nen khong duoc khop toi.
    """
    bd = _hanh_lang_20m()
    fix = bd.match(Pose2D(19.5, 0.5, 0.0), g(HOC), sigma_m=1.0)
    assert fix is None or fix.x != pytest.approx(7.5)


def test_huong_khac_han_thi_khong_khop():
    """Cung mot cho nhung quay mat huong khac thi thay canh khac han."""
    bd = _hanh_lang_20m()
    assert bd.match(Pose2D(7.5, 0.5, 180.0), g(HOC)) is None


def test_chua_quet_gi_thi_tra_None():
    assert Backdrop().match(Pose2D(7.5, 0.5, 0.0), g(HOC)) is None


def test_luoi_khac_kich_thuoc_thi_tra_None():
    """Khong so sanh duoc thi khong duoc doan."""
    bd = _hanh_lang_20m()
    khac = DepthGrid(cols=3, rows=3, depth=tuple([3.0] * 9),
                     confidence=tuple([0.9] * 9))
    assert bd.match(Pose2D(7.5, 0.5, 0.0), khac) is None


def test_tin_cay_khong_bao_gio_la_HIGH():
    """
    L4 khong bao gio duoc vuot quyen L1/L2. Ban nen quet mot lan roi
    lech dan theo thoi gian - ban ghe bi dich, cua mo dong, nguoi dung.
    """
    bd = _hanh_lang_20m()
    fix = bd.match(Pose2D(7.5, 0.5, 0.0), g(HOC))
    assert fix.confidence in ("MEDIUM", "LOW")


def test_o_CHUA_BIET_khong_duoc_tinh_vao_sai_lech():
    """
    O khong dang tin thi con so depth la rac. Tinh no vao sai lech se
    lam hong diem cua ung vien dung.
    """
    bd = _hanh_lang_20m()
    conf = [0.9] * N
    for i in (0, 1, 2, 3):
        conf[i] = 0.1                     # mot dai khong doc duoc
    mo = DepthGrid(cols=COLS, rows=ROWS,
                   depth=tuple(HOC), confidence=tuple(conf))
    fix = bd.match(Pose2D(7.5, 0.5, 0.0), mo)
    assert fix is None or fix.x == pytest.approx(7.5)


def test_qua_it_o_hop_le_thi_tra_None():
    """Duoi MIN_OVERLAP_CELLS thi khong du bang chung de ket luan."""
    bd = _hanh_lang_20m()
    conf = [0.1] * N
    conf[0] = 0.9                         # chi mot o dang tin
    mo = DepthGrid(cols=COLS, rows=ROWS,
                   depth=tuple(HOC), confidence=tuple(conf))
    assert bd.match(Pose2D(7.5, 0.5, 0.0), mo) is None


# ------------------------------------------------------------------
# Gioi han da biet cua cach cham diem bang trung vi
# ------------------------------------------------------------------

def test_dac_trung_nho_hon_mot_nua_luoi_thi_vo_hinh():
    """
    Ghi lai mot GIOI HAN THAT, khong phai loi.

    Trung vi chi "thay" duoc dac trung phu tren MOT NUA so o hop le.
    Mot hoc tuong nho chi lam doi 3 trong 12 o thi trung vi van bang 0,
    va o co hoc cho diem y het o hanh lang thuong.

    Danh doi co chu dich: doi lay kha nang chong nhieu (mot nguoi dung
    chan vai o khong pha duoc diem). Huong sua neu thuc dia bo lo qua
    nhieu cho la TANG DO PHAN GIAI LUOI, khong phai doi sang trung binh.

    Test nay ton tai de nguoi sau khong mat mot buoi debug tim xem
    "sao khop khong ra" - cau tra loi nam o day.
    """
    nho = [3.0, 6.0, 6.0, 5.2] * ROWS        # chi 3/12 o khac THANG
    bd = Backdrop()
    for m in range(20):
        bd.observe(Pose2D(float(m) + 0.5, 0.5, 0.0),
                   g(nho if m == 7 else THANG))

    # Dung ngay tai o co dac trung, quan sat dung y hinh dang do -
    # van khong khop duoc, vi trung vi khong phan biet noi.
    assert bd.match(Pose2D(7.5, 0.5, 0.0), g(nho)) is None
