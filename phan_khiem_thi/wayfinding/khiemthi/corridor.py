"""
Hai tin hieu rut ra tu chinh khung hinh - dac ta muc 9.

Ca hai deu muon tu Project Guideline, vốn bam mot vach son duoi dat.
Trong nha khong co vach son, nhung hanh lang cho ta thu tuong duong:
DUONG GIAO TUONG-SAN o hai ben hoi tu ve mot diem tu.

--------------------------------------------------------------------
VI SAO MODULE NAY DUOC PHEP IMPORT OPENCV
--------------------------------------------------------------------

Nguyen tac 1.4 cam lõi (Localizer, Router, Depth, Backdrop, Announce)
import OpenCV. Module nay KHONG thuoc lõi - no la lop thi giac, cung
hang voi `anchors.py`, va trong bang chuyen ngu no thuoc nhom "khong
port" (ban dien thoai se dung ML Kit / Vision thay the).

Dau ra cua no thi thuan so, va do moi la thu di vao lõi.

--------------------------------------------------------------------
HAI TIN HIEU, HAI MUC DICH KHAC HAN
--------------------------------------------------------------------

    diem tu      -> SUA HUONG    (lop L5, chi sua theta, khong sua x,y)
    luong quang  -> BAT LOI VIO  (khong dinh vi gi ca)

Tin hieu thu hai khong gop mot chut nao vao viec biet minh o dau. No
ton tai de bat mot loi cu the va rat nguy hiem: nguoi dung DUNG LAI hoi
duong, VIO tich luy troi, va he thong tuong ho da di them 5 met.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- diem tu (muc 9.1) ---

# Bo doan gan ngang: do la mep ban, bac thang, duong ke ngang - khong
# phai duong giao tuong-san
VP_MIN_ANGLE_DEG = 10.0

# Bo doan gan doc: khung cua, canh tu - chung khong hoi tu
VP_MAX_ANGLE_DEG = 80.0

# Can it nhat bao nhieu doan dong gop thi ket qua moi dang tin
VP_MIN_SEGMENTS = 4

# Cac giao diem phai tum tum lai. Tan mac hon nguong nay nghia la chung
# khong thuc su hoi tu ve mot diem - co the dang nhin vao mot khong
# gian mo chu khong phai hanh lang.
VP_SPREAD_PX = 60.0

# --- luong quang (muc 9.2) ---

# Duoi nguong nay coi nhu canh dung yen, don vi diem anh moi khung
FLOW_STILL_PX = 0.8

# Tren nguong nay coi nhu canh dang dich chuyen manh
FLOW_MOVING_PX = 2.5

# VIO bao da di xa hon bao nhieu met thi moi coi la "bao dang di"
VIO_MOVED_M = 0.05


@dataclass(frozen=True)
class HeadingCue:
    """
    Sai so huong so voi truc hanh lang - lop L5.

    CHI sua theta. Khong noi gi ve x, y, va khong duoc dung de sua
    chung: diem tu cho biet minh dang quay lech bao nhieu so voi truc
    hanh lang, chu khong cho biet dang o doan nao cua hanh lang.
    """

    heading_error_deg: float
    u_vp: float
    v_vp: float
    n_segments: int
    spread_px: float
    confidence: str = "MEDIUM"


class MotionVerdict(str, Enum):
    """Ket luan khi doi chieu luong quang voi VIO."""

    BINH_THUONG = "binh_thuong"      # hai nguon nhat quan
    VIO_TROI = "vio_troi"            # canh dung yen ma VIO bao dang di
    VIO_MAT_BAM = "vio_mat_bam"      # canh dich chuyen ma VIO bao dung
    CHUA_RO = "chua_ro"              # khong du dac trung de ket luan


def _goc_doan(x1: float, y1: float, x2: float, y2: float) -> float:
    """Goc cua mot doan so voi phuong ngang, do, trong [-90, 90]."""
    return math.degrees(math.atan2(y2 - y1, x2 - x1 + 1e-12))


def _giao_diem(a, b) -> tuple[float, float] | None:
    """Giao diem cua hai doan thang, coi nhu duong thang vo han."""
    x1, y1, x2, y2 = a
    x3, y3, x4, y4 = b
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-9:
        return None                       # song song
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) -
          (x1 - x2) * (x3 * y4 - y3 * x4)) / den
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) -
          (y1 - y2) * (x3 * y4 - y3 * x4)) / den
    return (px, py)


def vanishing_point(gray: np.ndarray, fx: float, cx: float,
                    min_segments: int = VP_MIN_SEGMENTS,
                    spread_max_px: float = VP_SPREAD_PX) -> HeadingCue | None:
    """
    Sai so huong so voi truc hanh lang, suy tu diem tu.

    Chi xet NUA DUOI khung hinh: duong giao tuong-san nam o do. Nua tren
    day den tran, bien treo, khung cua - toan thu hoi tu theo kieu khac
    va chi lam nhieu.

    Tra None khi khong du bang chung. KHONG DOAN - nguyen tac 1.1.
    """
    import cv2                            # noqa: PLC0415 - xem docstring dau file

    if gray is None or gray.ndim != 2 or gray.size == 0:
        return None

    h, w = gray.shape
    if h < 8 or w < 8:
        return None

    # --- 1. chi nua duoi ---
    y0 = h // 2
    duoi = gray[y0:, :]

    # --- 2. do canh roi Hough ---
    canh = cv2.Canny(duoi, 50, 150)
    doan = cv2.HoughLinesP(canh, 1, np.pi / 180, threshold=40,
                           minLineLength=max(20, w // 12), maxLineGap=10)
    if doan is None:
        return None

    # --- 3. bo doan gan ngang va gan doc ---
    #
    # reshape(-1, 4) chu khong phai doan[:, 0, :]: OpenCV 4.x tra
    # (N, 1, 4) con OpenCV 5 tra (N, 4). Chi so cung se chet tren mot
    # trong hai ban. Cung loi da tung lam calibrate.py chet - xem PR #14.
    giu = []
    for d in doan.reshape(-1, 4):
        x1, y1, x2, y2 = (float(v) for v in d)
        g = abs(_goc_doan(x1, y1, x2, y2))
        if g < VP_MIN_ANGLE_DEG or g > VP_MAX_ANGLE_DEG:
            continue
        giu.append((x1, y1 + y0, x2, y2 + y0))   # tra ve toa do khung day du

    if len(giu) < min_segments:
        return None

    # --- 4. giao diem tung cap, lay trung vi ---
    gd = []
    for i in range(len(giu)):
        for j in range(i + 1, len(giu)):
            p = _giao_diem(giu[i], giu[j])
            if p is not None:
                gd.append(p)
    if not gd:
        return None

    us = np.array([p[0] for p in gd], dtype=float)
    vs = np.array([p[1] for p in gd], dtype=float)
    u_vp, v_vp = float(np.median(us)), float(np.median(vs))

    # Do tan mac: neu cac giao diem khong tum lai thi chung khong thuc
    # su hoi tu ve mot diem, va "diem tu" tinh duoc chi la trung vi cua
    # mot dam nhieu.
    spread = float(np.median(np.hypot(us - u_vp, vs - v_vp)))
    if spread > spread_max_px:
        return None

    # --- 5. sai so huong ---
    err = math.degrees(math.atan((u_vp - cx) / fx)) if fx else 0.0

    return HeadingCue(heading_error_deg=err, u_vp=u_vp, v_vp=v_vp,
                      n_segments=len(giu), spread_px=spread)


def motion_check(truoc: np.ndarray | None, sau: np.ndarray | None,
                 vio_moved_m: float,
                 still_px: float = FLOW_STILL_PX,
                 moving_px: float = FLOW_MOVING_PX) -> MotionVerdict:
    """
    Doi chieu luong quang voi quang duong VIO bao, de BAT LOI VIO.

    Khong dung de dinh vi. Ba truong hop can bat:

        luong ~ 0, VIO bao dang di   -> VIO_TROI      (nguy hiem nhat)
        luong lon, VIO bao dung yen  -> VIO_MAT_BAM
        luong lon, VIO bao dang di   -> BINH_THUONG

    Truong hop dau la loi nguy hiem nhat trong thuc te: nguoi dung dung
    lai hoi duong, VIO tich luy troi, he thong tuong ho da di them 5 met
    va bat dau doc chi dan cua doan sau.
    """
    import cv2                            # noqa: PLC0415

    if truoc is None or sau is None:
        return MotionVerdict.CHUA_RO
    if truoc.ndim != 2 or sau.ndim != 2 or truoc.shape != sau.shape:
        return MotionVerdict.CHUA_RO

    goc = cv2.goodFeaturesToTrack(truoc, maxCorners=120, qualityLevel=0.01,
                                  minDistance=8)
    if goc is None or len(goc) < 6:
        return MotionVerdict.CHUA_RO      # canh tron, khong du dac trung

    moi, ok, _ = cv2.calcOpticalFlowPyrLK(truoc, sau, goc, None)
    if moi is None or ok is None:
        return MotionVerdict.CHUA_RO

    ok = ok.reshape(-1).astype(bool)
    if int(ok.sum()) < 6:
        return MotionVerdict.CHUA_RO

    a = goc.reshape(-1, 2)[ok]
    b = moi.reshape(-1, 2)[ok]
    do_lon = float(np.median(np.hypot(*(b - a).T)))

    vio_di = vio_moved_m > VIO_MOVED_M

    if do_lon < still_px and vio_di:
        return MotionVerdict.VIO_TROI
    if do_lon > moving_px and not vio_di:
        return MotionVerdict.VIO_MAT_BAM
    return MotionVerdict.BINH_THUONG
