"""
Chong rung - phan cung va phan mem.

--------------------------------------------------------------------
PHAT HIEN QUAN TRONG: day deo tu do bi CONG HUONG voi nhip di bo
--------------------------------------------------------------------

Dien thoai treo tren day deo co la mot CON LAC DON. Tan so dao dong
rieng cua no chi phu thuoc vao CHIEU DAI day, khong phu thuoc khoi luong:

    f = (1 / 2*pi) * sqrt(g / L)

    day 15 cm -> 1.29 Hz
    day 25 cm -> 1.00 Hz
    day 35 cm -> 0.84 Hz
    day 45 cm -> 0.74 Hz

Khi di bo, than nguoi lac ngang o khoang 0.85-1.00 Hz (bang mot nua nhip
buoc chan 1.7-2.0 Hz).

Hai con so nay TRUNG NHAU o chieu dai day thong thuong. Nghia la day deo
tu do khong nhung khong giam rung, ma con KHUECH DAI no - dung dinh nghia
cua cong huong. Cang di cang lac manh.

Do la ly do "deo day thong thuong quanh co" la thiet ke sai cho bai toan
nay, du no la thu de nghi den nhat.

--------------------------------------------------------------------
BA CACH KHAC PHUC, xep theo hieu qua tren chi phi
--------------------------------------------------------------------

1. NEO HAI DIEM (tot nhat, gan nhu 0 dong)
   Them mot day thun vong quanh than, keo dien thoai ap vao nguc. Con
   lac can mot diem treo duy nhat de dao dong; co diem neo thu hai thi
   mode con lac BIEN MAT hoan toan, khong con gi de cong huong.
   Vat tu: mot day thun ban to, hoac day deo ngang cua ba lo cu.

2. DEM XOP GIUA MAY VA NGUC (0 dong)
   Ma sat giua xop va ao tieu tan nang luong dao dong. Day la giam chan,
   khong phai loai bo - nhung ket hop voi (1) thi rat hieu qua.
   Vat tu: mieng xop cat tu bao bi.

3. RUT NGAN DAY XUONG <= 15 cm (0 dong)
   Dua tan so rieng len 1.29 Hz, tach khoi vung 0.85-1.00 Hz cua nhip di.
   Chi dung khi khong the lam (1). Van kem hon han neo hai diem.

KHONG nen: treo them vat nang cho "on dinh hon". Chu ky con lac KHONG
phu thuoc khoi luong, nen lam vay chi moi co ma khong giam duoc lac.

--------------------------------------------------------------------
PHAN MEM trong module nay
--------------------------------------------------------------------

Phan cung giam rung, phan mem CHON ra nhung khung hinh net trong so
nhung khung hinh con lai. Hai co che bo tro nhau:

  SharpnessGate - do do net bang phuong sai Laplace, bo khung hinh nhoe
  MotionGate    - dung con quay hoi chuyen, bo khung hinh chup luc dang
                  xoay nhanh. Re hon nhieu so voi do do net, vi khong
                  phai xu ly anh.

Ca hai deu KHONG lam cham he thong: chung BO BOT viec, khong them viec.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

import numpy as np

G = 9.81

# Nguong van toc goc (do/giay) tren nguong nay thi khung hinh gan nhu
# chac chan nhoe, khong can do do net nua - bo thang cho re.
DEFAULT_GYRO_LIMIT = 35.0

# Do net duoi ty le nay so voi muc tot nhat gan day thi coi la nhoe.
DEFAULT_SHARPNESS_RATIO = 0.45


# ====================================================================
# Vat ly cach deo
# ====================================================================

def pendulum_frequency(length_m: float) -> float:
    """Tan so dao dong rieng cua dien thoai treo tren day, don vi Hz."""
    if length_m <= 0:
        return float("inf")            # neo cung, khong co mode con lac
    return math.sqrt(G / length_m) / (2.0 * math.pi)


def gait_sway_band(cadence_spm: float = 110.0) -> tuple[float, float]:
    """
    Dai tan so lac ngang than khi di bo.

    Lac ngang xay ra MOI CHU KY BUOC, tuc bang mot nua nhip buoc chan.
    """
    step_hz = cadence_spm / 60.0
    sway = step_hz / 2.0
    return sway * 0.9, sway * 1.15


def resonance_risk(length_m: float, cadence_spm: float = 110.0) -> float:
    """
    Muc do cong huong, 0 = an toan, 1 = cong huong hoan toan.

    Nam TRONG dai lac cua nhip di thi rui ro toi da, khong phan biet
    gan hay xa tam dai - cong huong xay ra tren ca dai chu khong chi o
    dung tam. Ra ngoai dai thi giam dan.

    Nhip di cua moi nguoi moi khac, va nguoi khiem thi thuong di cham
    hon, nen dai nay chi la uoc luong. Khi nghi ngo thi coi la co rui ro.
    """
    f = pendulum_frequency(length_m)
    if not math.isfinite(f):
        return 0.0                     # neo cung, khong co mode con lac

    lo, hi = gait_sway_band(cadence_spm)
    if lo <= f <= hi:
        return 1.0

    width = max(hi - lo, 1e-6)
    gap = (lo - f) if f < lo else (f - hi)
    return max(0.0, 1.0 - gap / width)


def mount_advice(length_m: float, two_point: bool,
                 cadence_spm: float = 110.0) -> str:
    """Mot cau danh gia cach deo hien tai."""
    if two_point:
        return ("Neo hai diem - khong con mode con lac. Day la cach deo "
                "dung, khong can chinh gi them.")

    risk = resonance_risk(length_m, cadence_spm)
    f = pendulum_frequency(length_m)
    if risk > 0.6:
        return (f"NGUY HIEM: day {length_m * 100:.0f}cm dao dong {f:.2f} Hz, "
                "trung voi nhip lac nguoi khi di bo. Day deo dang KHUECH DAI "
                "rung. Them mot day thun vong quanh than.")
    if risk > 0.25:
        return (f"Can chinh: day {length_m * 100:.0f}cm ({f:.2f} Hz) gan vung "
                "cong huong. Nen neo hai diem, hoac rut ngan xuong duoi 15cm.")
    return (f"Chap nhan duoc: day {length_m * 100:.0f}cm ({f:.2f} Hz) nam "
            "ngoai vung cong huong. Neo hai diem van tot hon.")


# ====================================================================
# Do do net
# ====================================================================

def sharpness(frame: np.ndarray) -> float:
    """
    Do do net bang phuong sai cua Laplace.

    Anh net co nhieu bien sac -> Laplace bien thien manh -> phuong sai
    lon. Anh nhoe thi bien bi trai ra -> phuong sai nho.

    Day la thuoc do TUONG DOI: gia tri tuyet doi phu thuoc noi dung anh,
    nen phai so voi cac khung hinh gan do chu khong so voi hang so.
    """
    import cv2

    gray = frame
    if frame.ndim == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


@dataclass
class SharpnessGate:
    """
    Bo khung hinh nhoe, giu khung hinh net.

    Nguong TU DIEU CHINH theo muc do net tot nhat gan day, vi gia tri
    tuyet doi cua phuong sai Laplace phu thuoc vao noi dung anh: hanh
    lang tuong tron cho gia tri thap han so voi cho co nhieu do dac.
    Dat nguong cung se hoac bo het, hoac khong bo gi.
    """

    window: int = 20
    ratio: float = DEFAULT_SHARPNESS_RATIO
    warmup: int = 5                    # so khung hinh dau, chua du de danh gia

    _recent: deque = field(default_factory=lambda: deque(maxlen=20))
    seen: int = 0
    rejected: int = 0

    def __post_init__(self) -> None:
        self._recent = deque(maxlen=self.window)

    def accept(self, value: float) -> bool:
        """Nhan mot gia tri do net, tra ve co dung khung hinh nay khong."""
        self._recent.append(value)
        self.seen += 1

        if self.seen <= self.warmup:
            return True                # chua du du lieu, dung tam de khong bo sot

        best = max(self._recent)
        if best <= 0:
            return True
        ok = value >= best * self.ratio
        if not ok:
            self.rejected += 1
        return ok

    def accept_frame(self, frame: np.ndarray) -> bool:
        return self.accept(sharpness(frame))

    @property
    def reject_ratio(self) -> float:
        return self.rejected / self.seen if self.seen else 0.0

    def reset(self) -> None:
        self._recent.clear()
        self.seen = 0
        self.rejected = 0


# ====================================================================
# Cong chuyen dong
# ====================================================================

@dataclass
class MotionGate:
    """
    Bo khung hinh chup trong luc dang xoay nhanh.

    Re hon SharpnessGate rat nhieu vi khong phai xu ly anh - chi doc mot
    con so tu con quay hoi chuyen. Nen chay cong nay TRUOC, roi chi
    nhung khung hinh qua duoc moi dem di do do net.

    Nguong mac dinh 35 do/giay tuong ung voi nhoe khoang mot nua o cua
    ma o thoi gian phoi sang 16ms.
    """

    limit_dps: float = DEFAULT_GYRO_LIMIT
    seen: int = 0
    rejected: int = 0

    def accept(self, gyro_dps: float) -> bool:
        self.seen += 1
        ok = abs(gyro_dps) <= self.limit_dps
        if not ok:
            self.rejected += 1
        return ok

    def accept_vector(self, wx: float, wy: float, wz: float) -> bool:
        return self.accept(math.sqrt(wx * wx + wy * wy + wz * wz))

    @property
    def reject_ratio(self) -> float:
        return self.rejected / self.seen if self.seen else 0.0

    def reset(self) -> None:
        self.seen = 0
        self.rejected = 0


def blur_from_rotation(gyro_dps: float, exposure_ms: float,
                       width_px: int, fov_deg: float) -> float:
    """Do nhoe tinh bang pixel, do xoay camera trong luc mo cua chap."""
    px_per_deg = width_px / fov_deg
    return abs(gyro_dps) * (exposure_ms / 1000.0) * px_per_deg


def gyro_limit_for(max_blur_px: float, exposure_ms: float,
                   width_px: int, fov_deg: float) -> float:
    """Van toc goc toi da con giu duoc do nhoe duoi nguong cho phep."""
    px_per_deg = width_px / fov_deg
    if exposure_ms <= 0 or px_per_deg <= 0:
        return float("inf")
    return max_blur_px / (px_per_deg * (exposure_ms / 1000.0))


# ====================================================================
# Chon khung hinh net nhat trong mot chum
# ====================================================================

@dataclass
class BestOfBurst:
    """
    Giu lai khung hinh NET NHAT trong mot chum ngan.

    Voi nguoi run tay, cac khung hinh net va nhoe xen ke nhau. Thay vi
    xu ly khung hinh nao cung duoc, gom vai khung roi chi xu ly cai net
    nhat - vua nhanh hon vua chinh xac hon.

    Danh doi la DO TRE: chum 3 khung o 30 fps them khoang 100ms. Chap
    nhan duoc voi toc do di bo, va van con xa nguong nguy hiem.
    """

    size: int = 3
    _buffer: list = field(default_factory=list)

    def push(self, frame, score: float):
        """
        Them mot khung hinh. Tra ve khung net nhat khi chum day, None
        neu chua du.
        """
        self._buffer.append((score, frame))
        if len(self._buffer) < self.size:
            return None
        best = max(self._buffer, key=lambda x: x[0])
        self._buffer.clear()
        return best[1]

    def flush(self):
        """Lay khung net nhat trong chum dang do dang, neu co."""
        if not self._buffer:
            return None
        best = max(self._buffer, key=lambda x: x[0])
        self._buffer.clear()
        return best[1]

    def reset(self) -> None:
        self._buffer.clear()
