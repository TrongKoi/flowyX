"""
Tach vat can khoi mat san bang HINH HOC, khong dung nhan dien.

--------------------------------------------------------------------
VI SAO CAN LOP NAY
--------------------------------------------------------------------

Bo nhan dien do vat (ML Kit, Vision) duoc huan luyen tren anh tieu
dung: san pham, do an, cay canh, quan ao. No tim nhung khoi GON,
DUNG THANG, CO VAN. Ba loai vat sau no gan nhu khong bao gio thay:

  - dang que: cot den, chan ban, gay. Dien tich qua nho, diem
    "objectness" khong dat nguong de xuat.
  - vat nghieng: hop bao vuong goc khong khop, diem tut manh.
  - khoi hinh hoc tron: kim tu thap, hop lap phuong. Khong co mau
    tuong duong trong du lieu huan luyen.

Khong tinh chinh tham so nao lam ML Kit thay duoc cot den. Do la gioi
han cua mo hinh, khong phai cua cau hinh.

Nhung DO SAU thi khong quan tam hinh dang. Mot kim tu thap cach 1,2 m
chi la may o doc ra 1,2 m. Mot cot den la mot cot o gan. Mot tam van
nghieng la mot dai o gan dan.

Nen lop nay dao nguoc vai tro:

    do sau        -> TIM ra vat      (luon chay, khong bo sot)
    nhan dien     -> GOI TEN vat     (chay khi co, thieu cung khong sao)

--------------------------------------------------------------------
CACH LAM: BO MAT SAN DI
--------------------------------------------------------------------

Camera cao h met, chuc xuong goc alpha. Tia di qua hang r cua luoi
hop voi phuong ngang goc:

    beta(r) = alpha + (r_giua - 0.5) * fov_doc

Neu tia do cham san thi khoang cach THANG tu camera toi diem san do:

    d_san(r) = h / sin(beta)          (chi dung khi beta > 0)

O nao do duoc GAN HON d_san(r) dang ke thi co thu gi do nhô len khoi
san - bat ke thu do hinh gi. O nao XA HON dang ke thi la ho, bac tut
xuong, hoac tia khong cham san.

Hang nam tren duong chan troi (beta <= 0) khong cat san. Bat cu thu gi
do duoc o day deu la vat can theo dinh nghia: khong co gi duoc phep
nam ngang tam dau.

--------------------------------------------------------------------
DO PHAN GIAI LUOI: RANG BUOC THAT SU
--------------------------------------------------------------------

Luoi 4 cot chia 65 do thanh 4 o, moi o 16,25 do. Mot cot den 8 cm o
cu ly 2 m chi choán 2,29 do - tuc 14% cua mot o. Lay TRUNG VI o do thi
cot den bien mat hoan toan.

    vat                  goc     % cua o (4 cot)   % cua o (16 cot)
    cot den 8cm @2m     2,29         14%               56%
    chan ban 4cm @1,5m  1,53          9%               38%
    gay 3cm @1m         1,72         11%               42%
    canh kim tu thap    4,30         26%              106%

Trung vi chi "thay" thu choán tren 50% o. Nen 4 cot lam MOI vat tren
vo hinh, va do la ly do that su khien nguoi dung bao "khong detect
duoc dang que".

Hai thay doi di kem lop nay, o phia DepthSampler.kt:
  - luoi 4x3 -> 16x12
  - gop o bang PHAN VI 20 thay vi trung vi

Phan vi 20 la diem can giua: vat choán tren 20% o thi lo ra, con mot
diem nhieu don le (1/N so mau) thi khong keo duoc. Lay hang MIN thi
mot diem nhieu doc ra 0,2 m se sinh canh bao ma khong co gi ca.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from ..loi_chung.depth import DepthGrid, MIN_CONFIDENCE, Zone

# Chuc xuong bao nhieu do, va camera cao bao nhieu. Mac dinh khop voi
# profile.py; nguoi goi nen truyen gia tri that cua nguoi dung.
TILT_DOWN_DEG = 20.0
CAMERA_H_M = 1.30
FOV_V_DEG = 48.0
FOV_H_DEG = 65.0

# O phai gan hon mat san bao nhieu thi moi tinh la vat.
# Dung CA hai nguong: ty le bat duoc vat o xa, tuyet doi tranh bao
# nhang o gan noi ty le 15% chi con vai centimet.
SAN_TOL_REL = 0.15
SAN_TOL_ABS_M = 0.25

# Cum nho hon nay thi coi la nhieu, khong bao.
MIN_O_MOI_CUM = 2

# Xa hon nay thi khong con dang quan tam.
XA_NHAT_M = 5.0


class Dang(str, Enum):
    """Hinh dang tho cua mot cum, suy tu kich thuoc THAT chu khong
    phai ty le diem anh."""

    COT = "cot"              # hep va cao: cot den, chan ban, gay
    BAC_THAP = "bac_thap"    # thap, sat san: bac, go, vat nam
    TUONG = "tuong"          # rong va cao: tuong, tu, cua dong
    TREN_CAO = "tren_cao"    # chi o tren, duoi trong: bien treo, canh cay
    KHOI = "khoi"            # con lai


@dataclass(frozen=True)
class Cum:
    """Mot vat can tim duoc bang hinh hoc."""

    dang: Dang
    khoang_cach_m: float      # diem gan nhat cua cum
    bearing_deg: float        # am la ben trai
    rong_m: float
    cao_tu_m: float           # day cum, tinh tu mat san
    cao_den_m: float          # dinh cum, tinh tu mat san
    so_o: int
    zone: Zone

    @property
    def ben(self) -> str:
        if self.bearing_deg < -8.0:
            return "trái"
        if self.bearing_deg > 8.0:
            return "phải"
        return "trước mặt"


def goc_hang(row: int, rows: int, tilt_down_deg: float = TILT_DOWN_DEG,
             fov_v_deg: float = FOV_V_DEG) -> float:
    """Goc chuc xuong cua tia di qua giua hang `row`, tinh bang do.

    Duong so 0. So am nghia la tia huong LEN tren duong chan troi.
    """
    frac = (row + 0.5) / rows
    return tilt_down_deg + (frac - 0.5) * fov_v_deg


def depth_san(row: int, rows: int, camera_h: float = CAMERA_H_M,
              tilt_down_deg: float = TILT_DOWN_DEG,
              fov_v_deg: float = FOV_V_DEG) -> float | None:
    """Khoang cach toi diem MAT SAN ma hang nay nhin thay.

    Tra None khi tia khong cham san - hang nam tren duong chan troi.
    Khi do moi thu do duoc deu la vat can.
    """
    beta = math.radians(goc_hang(row, rows, tilt_down_deg, fov_v_deg))
    if beta <= 1e-6:
        return None
    return camera_h / math.sin(beta)


def _la_vat(d: float, conf: float, d_san: float | None) -> bool:
    """O nay co thu gi nho len khoi san khong."""
    if conf < MIN_CONFIDENCE or not math.isfinite(d) or d <= 0.0:
        return False                      # khong do duoc -> khong ket luan
    if d > XA_NHAT_M:
        return False
    if d_san is None:
        return True                       # tren duong chan troi
    nguong = max(SAN_TOL_ABS_M, d_san * SAN_TOL_REL)
    return d < d_san - nguong


def _cum_lien_thong(mask: list[list[bool]]) -> list[list[tuple[int, int]]]:
    """Gom cac o ke nhau (4 huong) thanh tung cum."""
    rows = len(mask)
    cols = len(mask[0]) if rows else 0
    da_xet = [[False] * cols for _ in range(rows)]
    cum: list[list[tuple[int, int]]] = []

    for r in range(rows):
        for c in range(cols):
            if not mask[r][c] or da_xet[r][c]:
                continue
            # Duyet theo chieu rong bang ngan xep, khong de quy: luoi
            # 32x24 co the cho chuoi de quy dai hon gioi han Python.
            ngan = [(r, c)]
            da_xet[r][c] = True
            nhom: list[tuple[int, int]] = []
            while ngan:
                y, x = ngan.pop()
                nhom.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if (0 <= ny < rows and 0 <= nx < cols
                            and mask[ny][nx] and not da_xet[ny][nx]):
                        da_xet[ny][nx] = True
                        ngan.append((ny, nx))
            cum.append(nhom)
    return cum


# Day cum cao hon nguong nay thi GAY TRANG KHONG VOI TOI. Gay quet sat
# san, nen moi thu khong cham san deu nam trong vung mu cua no. Dat o
# 1,00 m chu khong phai 1,40 m: vat ngang tam nguc cung la vat dam vao.
TREO_M = 1.00


def _phan_dang(rong_m: float, cao_tu_m: float, cao_den_m: float) -> Dang:
    """Goi ten hinh dang tu kich thuoc THAT, khong phai ty le o luoi.

    Dung kich thuoc that vi cung mot vat o xa chiem it o hon o gan -
    ty le o luoi doi theo cu ly, kich thuoc that thi khong.
    """
    cao = cao_den_m - cao_tu_m

    if cao_tu_m >= TREO_M:
        return Dang.TREN_CAO

    # Cot nhan dien bang TY LE cao tren rong, khong phai chieu cao
    # tuyet doi. Ly do: chan cot nam sat san, ma o sat san thi do sau
    # cua cot va cua san gan bang nhau - phan duoi cua cot bi hoa vao
    # san va khong lo ra. Nen mot cot den cao 2 m chi hien ra chung
    # 0,6-0,7 m phan giua. Doi chieu cao tuyet doi thi bo sot het.
    if rong_m <= 0.30 and cao >= 0.40 and cao >= 2.5 * rong_m:
        return Dang.COT
    if cao_den_m <= 0.45:
        return Dang.BAC_THAP
    if rong_m >= 0.80 and cao_den_m >= 1.50:
        return Dang.TUONG
    return Dang.KHOI


def tim(grid: DepthGrid, camera_h: float = CAMERA_H_M,
        tilt_down_deg: float = TILT_DOWN_DEG,
        fov_v_deg: float = FOV_V_DEG,
        fov_h_deg: float = FOV_H_DEG,
        min_o: int = MIN_O_MOI_CUM) -> list[Cum]:
    """Tim moi vat can trong luoi do sau, khong can biet no la gi.

    Tra ve danh sach da sap xep, GAN NHAT TRUOC.
    """
    rows, cols = grid.rows, grid.cols

    d_san_hang = [depth_san(r, rows, camera_h, tilt_down_deg, fov_v_deg)
                  for r in range(rows)]

    mask = [[False] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            d, conf = grid.at(r, c)
            mask[r][c] = _la_vat(d, conf, d_san_hang[r])

    ra: list[Cum] = []
    for nhom in _cum_lien_thong(mask):
        if len(nhom) < min_o:
            continue

        sau = [grid.at(r, c)[0] for r, c in nhom]
        gan_nhat = min(sau)

        cot = [c for _, c in nhom]
        hang = [r for r, _ in nhom]
        c0, c1 = min(cot), max(cot)
        r0, r1 = min(hang), max(hang)

        # Be rong that: goc ma cum choán, nhan voi cu ly.
        goc_rong = math.radians((c1 - c0 + 1) / cols * fov_h_deg)
        rong_m = 2.0 * gan_nhat * math.tan(goc_rong / 2.0)

        # Chieu cao that: diem tren tia o goc beta, cach d met, nam
        # duoi camera d*sin(beta). Camera cao camera_h nen do cao so
        # voi san la camera_h - d*sin(beta).
        b_tren = math.radians(goc_hang(r0, rows, tilt_down_deg, fov_v_deg))
        b_duoi = math.radians(goc_hang(r1, rows, tilt_down_deg, fov_v_deg))
        cao_den = camera_h - gan_nhat * math.sin(b_tren)
        cao_tu = camera_h - gan_nhat * math.sin(b_duoi)
        cao_tu, cao_den = min(cao_tu, cao_den), max(cao_tu, cao_den)
        cao_tu = max(0.0, cao_tu)

        giua_cot = (c0 + c1) / 2.0
        bearing = (giua_cot + 0.5 - cols / 2.0) / cols * fov_h_deg

        ra.append(Cum(
            dang=_phan_dang(rong_m, cao_tu, cao_den),
            khoang_cach_m=round(gan_nhat, 2),
            bearing_deg=round(bearing, 1),
            rong_m=round(rong_m, 2),
            cao_tu_m=round(cao_tu, 2),
            cao_den_m=round(cao_den, 2),
            so_o=len(nhom),
            zone=grid.zone_of(int(sum(hang) / len(hang))),
        ))

    ra.sort(key=lambda o: o.khoang_cach_m)
    return ra


TEN_DANG = {
    Dang.COT: "cột",
    Dang.BAC_THAP: "vật thấp",
    Dang.TUONG: "vật lớn",
    Dang.TREN_CAO: "vật ngang tầm đầu",
    Dang.KHOI: "vật cản",
}


def mo_ta(c: Cum) -> str:
    """Cau noi cho mot cum. Co dau day du - day la chuoi DOC LEN.

    So doc bang dau PHAY thap phan ("1,2 mét") vi do la cach doc tieng
    Viet. Chi doi dung con so, khong .replace() ca cau - cau khac co
    the co dau cham that.
    """
    so = f"{c.khoang_cach_m:.1f}".replace(".", ",")
    if c.dang is Dang.TREN_CAO:
        # Noi ro TAM CAO nao, vi nguoi dung phan ung khac nhau: ngang
        # nguc thi nghieng nguoi tranh, ngang dau thi phai cui. Noi
        # chung chung "vat tren cao" khong du de chon dong tac.
        tam = "ngang tầm đầu" if c.cao_tu_m >= 1.40 else "ngang tầm ngực"
        return f"Coi chừng vật {tam} {c.ben}, cách {so} mét"
    return f"{TEN_DANG[c.dang].capitalize()} {c.ben}, cách {so} mét"
