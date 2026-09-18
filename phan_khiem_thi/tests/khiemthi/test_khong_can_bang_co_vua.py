"""
Canh gac: he thong phai CHAY NGAY, khong doi tep hieu chinh camera.

--------------------------------------------------------------------
LOI DA TUNG CO THAT TRONG REPO
--------------------------------------------------------------------

`run_live.py` THOAT HAN neu khong tim thay `camera.npz`:

    if not Path(args.camera).exists():
        sys.exit("Khong tim thay camera.npz. Chay truoc: calibrate.py")
    K = dist = None        # <- ngay dong duoi, KHONG DUNG DEN

Tuc la no doi mot tep roi bo qua chinh tep do. Hau qua: ai muon chay thu
cung phai in mot BANG CO VUA ra giay truoc - rao can lon cho mot thu
khong con duoc dung den.

Tep hieu chinh khong con can vi:

    duong dien thoai  ->  ARCore/ARKit cho san thong so noi tai
    duong webcam      ->  uoc tieu cu tu goc nhin ngang

Cac test duoi khoa ca hai chieu: khong co tep thi van chay, co tep thi
gia tri trong tep duoc uu tien.
"""

from __future__ import annotations

import ast
import math
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GOC))

from wayfinding.loi_chung.anchors import (FOV_NGANG_MAC_DINH, sign_distance,
                                uoc_focal_px)


# ------------------------------------------------------------------
# Khong con cho nao CHAN khoi dong vi thieu tep hieu chinh
# ------------------------------------------------------------------

@pytest.mark.parametrize("ten", ["run_live.py", "run_bridge.py", "run_panel.py"])
def test_khong_thoat_khi_thieu_tep_hieu_chinh(ten: str):
    """
    Khong chuong trinh chay nao duoc `sys.exit` chi vi thieu camera.npz.

    Kiem bang cach doc CAY CU PHAP: tim moi loi goi sys.exit nam trong
    mot nhanh `if` co nhac toi tep hieu chinh.
    """
    cay = ast.parse((GOC / ten).read_text(encoding="utf-8"))

    for n in ast.walk(cay):
        if not isinstance(n, ast.If):
            continue
        dieu_kien = ast.unparse(n.test)
        if "camera" not in dieu_kien or "exists" not in dieu_kien:
            continue
        for x in ast.walk(n):
            if (isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                    and x.func.attr == "exit"):
                pytest.fail(f"{ten} van thoat khi thieu tep hieu chinh")


def test_khong_con_tham_so_camera_mo_coi():
    """
    `--camera` trong run_bridge va run_panel la di san tu thoi ArUco.

    Giu mot tham so khong con tac dung nao te hon la bo han: nguoi dung
    se tuong minh phai chuan bi tep do.
    """
    for ten in ("run_bridge.py", "run_panel.py"):
        assert "--camera" not in (GOC / ten).read_text(encoding="utf-8"), ten


# ------------------------------------------------------------------
# Uoc tieu cu tu goc nhin
# ------------------------------------------------------------------

def test_uoc_focal_dung_cong_thuc_lo_kim():
    """f = (chieu_rong / 2) / tan(FOV / 2)"""
    mong = 1280 / (2 * math.tan(math.radians(65.0 / 2)))
    assert uoc_focal_px(1280, 65.0) == pytest.approx(mong)


def test_tieu_cu_ty_le_thuan_voi_chieu_rong():
    """Cung mot camera, anh rong gap doi thi tieu cu tinh bang px gap doi."""
    assert uoc_focal_px(1280) == pytest.approx(2 * uoc_focal_px(640))


def test_goc_nhin_rong_hon_cho_tieu_cu_ngan_hon():
    assert uoc_focal_px(1280, 90.0) < uoc_focal_px(1280, 50.0)


@pytest.mark.parametrize("rong", [0, -10])
def test_chieu_rong_vo_ly_khong_lam_sap(rong: int):
    assert uoc_focal_px(rong) == 0.0


@pytest.mark.parametrize("fov", [0.0, 180.0, 1000.0, -5.0])
def test_goc_nhin_vo_ly_khong_lam_sap(fov: float):
    """Gia tri bien bi kep lai thay vi chia cho 0 hoac cho so am."""
    assert uoc_focal_px(1280, fov) > 0.0


def test_fov_mac_dinh_nam_trong_khoang_thuc_te():
    """Camera sau dien thoai 62-70 do, webcam laptop 60-65."""
    assert 55.0 <= FOV_NGANG_MAC_DINH <= 75.0


# ------------------------------------------------------------------
# Tieu cu uoc luong PHAI dung duoc de do khoang cach that
# ------------------------------------------------------------------

def _hop(h_px: float, rong_px: int = 200):
    """Hop bao cao h_px diem anh."""
    return [[100, 100], [100 + rong_px, 100],
            [100 + rong_px, 100 + h_px], [100, 100 + h_px]]


@pytest.mark.parametrize("that_m", [1.0, 2.0, 3.0])
def test_do_duoc_khoang_cach_bang_tieu_cu_uoc(that_m: float):
    """
    Bien cao 100mm, dat o khoang cach biet truoc. Do lai bang cong thuc
    lo kim voi tieu cu UOC LUONG - sai so phai nho.

    Day moi la diem quan trong: uoc luong khong chi "khong lam sap" ma
    phai thuc su DUNG DUOC.
    """
    rong_khung = 1280
    f = uoc_focal_px(rong_khung)
    cao_that = 0.10
    h_px = f * cao_that / that_m

    do_duoc = sign_distance(_hop(h_px), rong_khung,
                            text_h=cao_that, focal_px=f)
    assert do_duoc == pytest.approx(that_m, rel=0.02)


def test_thieu_tieu_cu_thi_roi_ve_cong_thuc_cu_chu_khong_sap():
    """Suy giam em: khong co tieu cu thi van tra ve mot con so dung duoc."""
    d = sign_distance(_hop(60), 1280)
    assert 0.0 < d < 10.0
