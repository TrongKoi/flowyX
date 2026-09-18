"""
Kiem lop tach vat can bang hinh hoc.

Bai kiem quan trong nhat o day la ba dang vat ma ML Kit KHONG thay
duoc: cot/que, vat nghieng, va khoi hinh hoc. Neu mot trong ba bai do
do thi lop nay khong giai quyet duoc van de sinh ra no.
"""

from __future__ import annotations

import math

import pytest

from wayfinding.loi_chung.depth import DepthGrid, Zone
from wayfinding.khiemthi.shapes import (
    CAMERA_H_M,
    FOV_V_DEG,
    TILT_DOWN_DEG,
    Cum,
    Dang,
    TREO_M,
    depth_san,
    goc_hang,
    mo_ta,
    tim,
)

COLS, ROWS = 16, 12


def _luoi_san_trong(cols: int = COLS, rows: int = ROWS) -> list[float]:
    """Luoi ma moi o deu dung bang khoang cach mat san - tuc san trong.

    Hang tren duong chan troi khong cham san; cho 0 do sau va se bi
    danh dau do tin cay 0 o ham duoi.
    """
    ra = []
    for r in range(rows):
        d = depth_san(r, rows)
        ra.extend([d if d is not None else 0.0] * cols)
    return ra


def _grid(depth: list[float], conf: list[float] | None = None) -> DepthGrid:
    if conf is None:
        # O nao do sau 0 thi coi nhu khong do duoc.
        conf = [0.0 if d <= 0.0 else 0.9 for d in depth]
    return DepthGrid(cols=COLS, rows=ROWS,
                     depth=tuple(depth), confidence=tuple(conf))


def _dat(depth: list[float], r0: int, r1: int, c0: int, c1: int,
         d: float) -> None:
    """Dat mot vat khoi hop vao luoi."""
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            depth[r * COLS + c] = d


# ----------------------------------------------------------------- san


def test_san_trong_thi_khong_bao_gi():
    """Hanh lang trong phai im lang tuyet doi.

    Bai nay quan trong ngang bai phat hien duoc vat: mot lop bao nhang
    lien tuc thi nguoi dung tat app, va luc do ty le bo sot thanh 100%.
    """
    assert tim(_grid(_luoi_san_trong())) == []


def test_o_khong_do_duoc_khong_thanh_vat():
    """Do tin cay thap khong duoc coi la co vat.

    Nguoc lai voi quy tac cua depth.py - o do CHUA_BIET phai duoc bao
    o dai SAN. O day thi khac: khong do duoc thi khong DUNG len duoc
    hinh dang, nen im thay vi doan bua.
    """
    d = _luoi_san_trong()
    _dat(d, 6, 9, 6, 9, 1.0)              # rat gan, nhung...
    conf = [0.9] * (COLS * ROWS)
    for r in range(6, 10):
        for c in range(6, 10):
            conf[r * COLS + c] = 0.1      # ...khong dang tin
    assert tim(_grid(d, conf)) == []


# -------------------------------------------------- ba dang ML Kit bo sot


def test_dang_que_duoc_phat_hien():
    """Cot den hep: ML Kit khong thay, hinh hoc phai thay.

    Mot cot rong ~0,1 m o 2 m choán khoang 1 cot cua luoi 16.
    """
    d = _luoi_san_trong()
    # cot chay tu san len qua tam nguc, chi 1 cot luoi
    for r in range(3, 11):
        d[r * COLS + 8] = 2.0
    cum = tim(_grid(d))

    assert cum, "cot den bi bo sot hoan toan"
    assert cum[0].dang is Dang.COT
    assert cum[0].khoang_cach_m == pytest.approx(2.0, abs=0.05)


def test_khoi_kim_tu_thap_duoc_phat_hien():
    """Kim tu thap: khong co mau tuong duong trong du lieu huan luyen
    cua ML Kit, nhung do sau van doc ra binh thuong."""
    d = _luoi_san_trong()
    # mat cat tam giac: cang len cao cang hep
    for i, r in enumerate(range(11, 6, -1)):
        rong = 5 - i
        if rong < 1:
            break
        _dat(d, r, r, 8 - rong // 2, 8 + rong // 2, 1.8)
    cum = tim(_grid(d))

    assert cum, "khoi kim tu thap bi bo sot"
    assert cum[0].khoang_cach_m == pytest.approx(1.8, abs=0.05)


def test_vat_nghieng_duoc_phat_hien():
    """Tam van dua nghieng: hop bao vuong goc khong khop nen ML Kit
    tut diem, nhung do sau bien thien deu - hinh hoc khong he kho."""
    d = _luoi_san_trong()
    for i, r in enumerate(range(10, 4, -1)):
        c = 5 + i
        if c >= COLS:
            break
        _dat(d, r, r, c, c + 1, 1.5 + i * 0.12)
    cum = tim(_grid(d))

    assert cum, "vat nghieng bi bo sot"
    assert cum[0].khoang_cach_m < 2.0


# ------------------------------------------------------------ phan dang


def test_vat_khong_cham_san_vao_vung_mu_cua_gay():
    """Day la dung thu gay trang khong cham toi, nen phai goi rieng.

    Gay quet sat san. Bat cu vat nao co DAY cao hon ~1 m deu nam ngoai
    tam quet cua no - ke ca khi chua toi tam dau.
    """
    d = _luoi_san_trong()
    _dat(d, 0, 2, 7, 10, 2.0)             # cao, khong cham xuong duoi
    cum = tim(_grid(d))

    assert cum
    assert cum[0].dang is Dang.TREN_CAO
    assert cum[0].cao_tu_m >= TREO_M
    assert "Coi chừng" in mo_ta(cum[0])


def test_cau_noi_phan_biet_tam_nguc_va_tam_dau():
    """Hai tam cao doi hoi hai dong tac khac nhau: nghieng nguoi, va
    cui dau. Noi chung chung thi nguoi dung khong chon duoc."""
    nguc = Cum(dang=Dang.TREN_CAO, khoang_cach_m=2.0, bearing_deg=0.0,
               rong_m=0.5, cao_tu_m=1.10, cao_den_m=1.35, so_o=8,
               zone=Zone.CAO)
    dau = Cum(dang=Dang.TREN_CAO, khoang_cach_m=2.0, bearing_deg=0.0,
              rong_m=0.5, cao_tu_m=1.60, cao_den_m=1.90, so_o=8,
              zone=Zone.CAO)

    assert "ngang tầm ngực" in mo_ta(nguc)
    assert "ngang tầm đầu" in mo_ta(dau)


def test_vat_thap_sat_san():
    d = _luoi_san_trong()
    _dat(d, ROWS - 2, ROWS - 1, 6, 11, 1.2)
    cum = tim(_grid(d))

    assert cum
    assert cum[0].dang in (Dang.BAC_THAP, Dang.KHOI)
    assert cum[0].cao_den_m < 1.0


def test_hai_vat_tach_thanh_hai_cum():
    """Hai cot cach nhau phai la hai cum, khong dinh thanh mot."""
    d = _luoi_san_trong()
    for r in range(4, 11):
        d[r * COLS + 2] = 2.0
        d[r * COLS + 13] = 3.0
    cum = tim(_grid(d))

    assert len(cum) == 2
    assert cum[0].khoang_cach_m < cum[1].khoang_cach_m   # gan nhat truoc
    assert cum[0].ben == "trái"
    assert cum[1].ben == "phải"


def test_sap_xep_gan_nhat_truoc():
    d = _luoi_san_trong()
    for r in range(5, 10):
        d[r * COLS + 1] = 3.5
        d[r * COLS + 14] = 1.1
    cum = tim(_grid(d))
    assert [c.khoang_cach_m for c in cum] == sorted(
        c.khoang_cach_m for c in cum)


def test_nhieu_mot_o_bi_bo_qua():
    """Mot o le loi la nhieu, khong phai vat."""
    d = _luoi_san_trong()
    d[7 * COLS + 9] = 0.8
    assert tim(_grid(d)) == []


# ------------------------------------------------------------- hinh hoc


def test_duong_chan_troi_khong_cham_san():
    """Hang nhin len tren khong co giao diem voi san."""
    assert depth_san(0, 12, tilt_down_deg=0.0) is None
    assert goc_hang(0, 12, tilt_down_deg=0.0) < 0


def test_cong_thuc_depth_san_khop_luong_giac():
    beta = math.radians(goc_hang(8, 12))
    assert depth_san(8, 12) == pytest.approx(CAMERA_H_M / math.sin(beta))


def test_do_phan_giai_tho_lam_cot_vo_hinh():
    """Khoa lai ly do phai nang luoi len 16 cot.

    Cung mot cot den, luoi 4 cot khong tach noi khoi san vi vat khong
    choán du mot o. Neu ai do ha luoi ve 4 cot thi bai nay do.
    """
    rows = 12
    d4 = []
    for r in range(rows):
        v = depth_san(r, rows)
        d4.extend([v if v is not None else 0.0] * 4)
    g4 = DepthGrid(cols=4, rows=rows, depth=tuple(d4),
                   confidence=tuple(0.0 if x <= 0 else 0.9 for x in d4))
    assert tim(g4) == []                  # san trong, dung

    # Bay gio them cot den o luoi 16 cot -> phai thay
    d16 = _luoi_san_trong()
    for r in range(3, 11):
        d16[r * COLS + 8] = 2.0
    assert tim(_grid(d16)), "luoi 16 cot phai thay duoc cot den"


def test_cau_noi_dung_dau_phay_thap_phan():
    c = Cum(dang=Dang.KHOI, khoang_cach_m=1.25, bearing_deg=0.0,
            rong_m=0.5, cao_tu_m=0.2, cao_den_m=1.0, so_o=6,
            zone=Zone.XA)
    s = mo_ta(c)
    assert "1,2" in s and "1.2" not in s


# --------------------------------------------------- co duoc GOI khong

def test_run_bridge_co_goi_lop_hinh_hoc():
    """Doc ma nguon runner de chac lop nay duoc noi vao duong chay that.

    Khac han cac bai tren: chung kiem lop nay co DUNG khong, bai nay
    kiem no co duoc DUNG DEN khong. Repo nay da tung co mot lop moc neo
    viet xong, co 28 test xanh, ma khong runner nao goi toi - xem PR #18.
    """
    from pathlib import Path

    src = (Path(__file__).resolve().parents[2] / "run_bridge.py").read_text(
        encoding="utf-8")
    assert "from wayfinding.khiemthi import shapes" in src, "runner chua import"
    assert "shapes.tim(" in src, "runner import nhung khong goi tim()"
    assert "shapes.mo_ta(" in src, "tim duoc vat nhung khong noi ra"


def test_cau_canh_bao_deu_co_dau_tieng_viet():
    """Moi chuoi lop nay sinh ra deu la chuoi DOC LEN.

    Bo doc tieng Viet doc "Cot ben trai" thanh am vo nghia. Bai nay
    khoa lai ca bang TEN_DANG lan cau hoan chinh.
    """
    from wayfinding.khiemthi.shapes import TEN_DANG

    # Kiem bang "co ky tu ngoai ASCII", KHONG phai bang mot danh sach
    # dau liet ke san.
    #
    # Ban dau bai nay liet ke "ăâàáảãạêèéế..." va bao dong gia ngay voi
    # "cột", "thấp", "lớn" - vi ộ, ấ, ớ khong nam trong danh sach. Tieng
    # Viet co qua nhieu to hop nguyen am voi dau; danh sach viet tay
    # nao cung thieu.
    #
    # Cach nay dung duoc o day vi ca nam nhan deu CHAC CHAN phai co dau.
    # Khong dung duoc cho chuoi bat ky - "Cầu thang" co tu "thang" viet
    # dung ma khong dau.
    for ten in TEN_DANG.values():
        assert any(ord(k) > 127 for k in ten), f"{ten!r} mat dau"

    c = Cum(dang=Dang.COT, khoang_cach_m=2.0, bearing_deg=-20.0,
            rong_m=0.1, cao_tu_m=0.3, cao_den_m=1.2, so_o=6, zone=Zone.XA)
    assert "Cột" in mo_ta(c) and "trái" in mo_ta(c)
