"""
Canh gac cho cau truc HAI NHANH: loi_chung / adhd.

Flowy da chuyen toan bo phan khiem thi sang thu muc `phan_khiem_thi/` o
goc repo - KHONG xoa, chi cat ra khoi duong chay chinh.

Hai module tung nam trong `khiemthi/` chuyen sang `loi_chung/` thay vi
cat ra: `vio.py` (SimulatedVIO la cong cu chay test cho chinh loi chung
- test_core, test_bridge va tools/phone_sim deu can) va `arcore.py`
(ban tham chieu cua toan toa do ma ArMath.kt ben Android dich tu do).

--------------------------------------------------------------------
LOI DA TUNG LOT QUA BO TEST
--------------------------------------------------------------------

Sau khi tach ba nhanh, `run_bridge.py` van con dong:

    from wayfinding import shapes

Dang import nay KHONG bi bo test bat, vi khong test nao chay
`run_bridge.py` - va no chi hong khi nguoi dung go lenh chay that.

Cac test duoi bat dung loai loi do: chung IMPORT tung chuong trinh chay
va kiem chieu phu thuoc giua ba nhanh.
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GOC))

# Chi con MOT chuong trinh chay o he thong chinh. Sau cai con lai da
# sang phan_khiem_thi/ - van chay duoc tu do, nhung khong thuoc duong
# chay cua Flowy nen khong kiem o day.
CHUONG_TRINH = ["run_flowy"]


@pytest.mark.parametrize("ten", CHUONG_TRINH)
def test_moi_chuong_trinh_chay_import_duoc(ten: str):
    """
    Chi can import duoc la du bat het loi duong dan module. Khong chay
    `main()` vi no se mo cong mang va cho mai.
    """
    importlib.import_module(ten)


def test_khong_con_import_thang_tu_gói_wayfinding():
    """
    `from wayfinding import X` khong con hop le: moi module gio nam
    trong mot trong ba nhanh con.
    """
    for ten in CHUONG_TRINH:
        cay = ast.parse((GOC / f"{ten}.py").read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            if isinstance(n, ast.ImportFrom) and n.module == "wayfinding":
                pytest.fail(f"{ten}.py con `from wayfinding import "
                            f"{', '.join(a.name for a in n.names)}`")


def test_loi_chung_KHONG_phu_thuoc_hai_nhanh_kia():
    """
    Chieu phu thuoc phai mot chieu: adhd -> loi_chung, khiemthi ->
    loi_chung.

    Vi pham dieu nay lam hai che do dinh vao nhau, va sua mot ben se vo
    tinh lam hong ben kia - dung thu ma viec tach ba nhanh sinh ra de
    tranh.
    """
    thu_muc = GOC / "wayfinding" / "loi_chung"
    for p in thu_muc.glob("*.py"):
        s = p.read_text(encoding="utf-8")
        for xau in ("from ..adhd", "from ..khiemthi",
                    "wayfinding.adhd", "wayfinding.khiemthi"):
            assert xau not in s, f"loi_chung/{p.name} phu thuoc nguoc: {xau}"


@pytest.mark.parametrize("nhanh", ["loi_chung", "adhd"])
def test_moi_nhanh_co_goi_hop_le(nhanh: str):
    assert (GOC / "wayfinding" / nhanh / "__init__.py").is_file()


def test_adhd_khong_phu_thuoc_phan_da_cat_ra():
    """
    `adhd/` khong duoc import gi tu `phan_khiem_thi/`.

    Vi pham dieu nay lam he thong chinh dinh vao thu muc da cat ra, va
    viec cat mat y nghia - sua mot ben lai lam hong ben kia.
    """
    for p in (GOC / "wayfinding" / "adhd").glob("*.py"):
        noi_dung = p.read_text(encoding="utf-8")
        for xau in ("khiemthi", "phan_khiem_thi"):
            assert xau not in noi_dung, f"adhd/{p.name} phu thuoc: {xau}"


# --------------------------------------------------------------------
# RANH GIOI DU LIEU: HAI MODULE CHI SONG O PHIA DIEN THOAI
# --------------------------------------------------------------------
#
# Bang trong `loi_chung/bridge.py` liet ke nhung thu KHONG BAO GIO duoc
# di qua cau noi. Hai trong so do la ten cac loi nhac nguoi dung tu dat,
# va nhat ky cam xuc.
#
# Nen `nhacviec.py` va `nhatky.py` khong duoc noi vao `run_flowy.py`.
# Chung chay tron ven tren may nguoi dung; ban Python o day la ban goc
# de doi chieu, va ban iOS hien thuc lai dung logic do.
#
# Day la thu rat de vo tinh pha: them mot dong import cho tien la du. Ma
# hong kieu do khong lam test nao khac do, va cung khong lam app sap -
# no chi lang le dua du lieu ca nhan len duong truyen.

CHI_O_DIEN_THOAI = ("nhacviec", "nhatky")


@pytest.mark.parametrize("ten_module", CHI_O_DIEN_THOAI)
def test_module_chi_o_dien_thoai_KHONG_duoc_noi_vao_cau_noi(ten_module: str):
    """Cau noi khong duoc biet den hai module nay."""
    for p in (GOC / "wayfinding" / "loi_chung").glob("*.py"):
        s = p.read_text(encoding="utf-8")
        assert f"import {ten_module}" not in s, f"loi_chung/{p.name}"
        assert f"adhd.{ten_module}" not in s, f"loi_chung/{p.name}"


@pytest.mark.parametrize("ten_module", CHI_O_DIEN_THOAI)
def test_module_chi_o_dien_thoai_KHONG_duoc_noi_vao_runner(ten_module: str):
    """
    Kiem bang cay cu phap chu khong bang tim chuoi: mot cau chu thich
    nhac ten module la hop le, mot lenh import thi khong.
    """
    for ten in CHUONG_TRINH:
        cay = ast.parse((GOC / f"{ten}.py").read_text(encoding="utf-8"))
        for n in ast.walk(cay):
            if isinstance(n, ast.ImportFrom):
                goi = n.module or ""
                if goi.endswith(ten_module):
                    pytest.fail(f"{ten}.py import {goi}")
                if goi.endswith("adhd") and any(a.name == ten_module
                                                for a in n.names):
                    pytest.fail(f"{ten}.py import {ten_module}")
            elif isinstance(n, ast.Import):
                for a in n.names:
                    assert not a.name.endswith(ten_module), f"{ten}.py"
