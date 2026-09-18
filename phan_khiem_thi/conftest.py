"""
Noi hai goc goi `wayfinding` lai de phan da cat ra van chay duoc.

--------------------------------------------------------------------
VAN DE
--------------------------------------------------------------------

Sau khi tach, ma nguon nam o hai cho:

    adc_wayfinding/wayfinding/loi_chung/    <- he thong chinh cua Flowy
    phan_khiem_thi/wayfinding/khiemthi/     <- phan da cat ra

Python khong cho hai thu muc cung ten `wayfinding` la MOT goi: cai nao
tim thay truoc thi thang, cai kia coi nhu khong ton tai. Nen
`wayfinding.khiemthi` va `wayfinding.loi_chung` khong bao gio cung nhin
thay nhau.

--------------------------------------------------------------------
CACH LAM
--------------------------------------------------------------------

Nap goi `wayfinding` tu he thong chinh truoc, roi NOI THEM duong dan
cua thu muc nay vao `__path__` cua no. Python tim module con theo danh
sach do, nen sau buoc nay ca hai nhanh deu tim duoc.

Day la cach re nhat de giu phan da cat ra VAN CHAY DUOC ma khong phai
sua lai duong dan import trong hang chuc file.

--------------------------------------------------------------------
VI SAO KHONG SUA IMPORT CHO GON HON
--------------------------------------------------------------------

Doi `wayfinding.khiemthi.X` thanh `khiemthi.X` trong moi file se lam
thu muc nay TU CHUA - dep hon that. Nhung luc do no lech han voi ban
dang chay o repo OpticGuard, va moi lan doi chieu hai ben deu phai dich
trong dau.

Giu nguyen duong dan import thi hai ben van la cung mot ma nguon.
"""

from __future__ import annotations

import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent
CHINH = GOC.parent / "adc_wayfinding"

# He thong chinh phai vao truoc: `wayfinding/__init__.py` that nam o do.
if str(CHINH) not in sys.path:
    sys.path.insert(0, str(CHINH))
if str(GOC) not in sys.path:
    sys.path.insert(0, str(GOC))

import wayfinding  # noqa: E402

_them = str(GOC / "wayfinding")
if _them not in wayfinding.__path__:
    wayfinding.__path__.append(_them)


# --------------------------------------------------------------------
# Bon bai kiem "runner co GOI lop nay khong"
# --------------------------------------------------------------------
#
# Chung doc ma nguon `run_bridge.py` va doi thay lop khiem thi duoc noi
# vao. O Flowy thi khong - do chinh la thu vua cat di.
#
# Khong xoa chung, va cung khong sua file: giu nguyen de hai repo van la
# cung mot ma nguon. Chi bo qua kem ly do, va ly do do noi ro nen tim ban
# chay duoc o dau.
BO_QUA = {
    "test_khong_thoat_khi_thieu_tep_hieu_chinh",
    "test_khong_con_tham_so_camera_mo_coi",
    "test_run_bridge_co_goi_lop_hinh_hoc",
    "test_runner_co_truyen_known_signs",
}

LY_DO = ("Kiem run_bridge.py co noi lop khiem thi khong. Flowy da cat "
         "lop do ra, nen bai nay khong the xanh o day. Ban chay duoc "
         "nam o repo OpticGuard.")


def pytest_collection_modifyitems(config, items):
    import pytest
    for item in items:
        ten = item.name.split("[")[0]
        if ten in BO_QUA:
            item.add_marker(pytest.mark.skip(reason=LY_DO))
