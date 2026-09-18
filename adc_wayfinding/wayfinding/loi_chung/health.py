"""
Theo doi SUC KHOE HE THONG trong luc dang chay.

Hai kieu hong AM THAM ma nguoi khiem thi khong the tu phat hien:

  1. HET PIN. Nguoi sang mat liec man hinh la biet. Nguoi khiem thi thi
     khong - dien thoai tat giua duong la ho ket lai o mot noi khong quen.
     Phai canh bao SOM va theo nguong, du de con quay ve hoac tim nguoi.

  2. CAMERA BI LECH. Dien thoai xoay tren day deo, camera chuc xuong san.
     He thong khong bao loi gi ca - no chi lang le khong bat duoc ma nao
     nua, va nguoi dung chi nghe "chua xac dinh duoc vi tri" mai ma khong
     hieu tai sao. Day la loi hay gap nhat khi demo.

Ca hai deu la loi HE THONG chu khong phai loi dieu huong, nen tach rieng
khoi guidance.py: chung phai duoc noi ra ke ca khi dang khong dan duong.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

# Nguong canh bao pin, tinh bang phan tram. Canh bao som de con kip quay
# ve, khong phai de bao "sap het" khi da qua muon.
BATTERY_LEVELS = (30.0, 15.0, 5.0)

# So khung hinh dung de danh gia ty le bat duoc moc neo
HEALTH_WINDOW = 150

# Phai bat duoc it nhat bao nhieu moc neo thi moi coi la "da tung khoe"
HEALTHY_MIN_HITS = 3

# Ty le bat duoc tut xuong duoi nguong nay sau khi da tung khoe = nghi ngo
COLLAPSE_RATIO = 0.15


@dataclass
class BatteryMonitor:
    """
    Canh bao pin theo nguong, moi nguong noi DUNG MOT LAN.

    Noi lai lien tuc thi nguoi dung se tat di, va lan sau canh bao that
    su quan trong cung bi bo qua.
    """

    levels: tuple[float, ...] = BATTERY_LEVELS
    _announced: set[float] = field(default_factory=set)
    last_percent: float | None = None

    def update(self, percent: float | None) -> str | None:
        """Tra ve cau can noi, hoac None neu chua den nguong nao moi."""
        if percent is None:
            return None
        self.last_percent = percent

        # Lay nguong KHAN CAP NHAT da vuot qua, khong phai nguong cao nhat.
        # Tut thang tu 80% xuong 4% thi phai doc canh bao cua muc 5%, chu
        # khong phai doc canh bao muc 30% roi lan sau moi doc muc 15%.
        crossed = [lv for lv in self.levels if percent <= lv]
        if not crossed:
            return None

        level = min(crossed)
        if level in self._announced:
            return None

        # Danh dau ca cac nguong CAO HON la da qua, de khong noi don
        for lv in self.levels:
            if lv >= level:
                self._announced.add(lv)
        return self._message(level, percent)

    def _message(self, level: float, percent: float) -> str:
        if level <= 5.0:
            return (f"Pin con {percent:.0f} phan tram. He thong sap tat. "
                    "Hay dung lai o cho an toan va nho nguoi ho tro.")
        if level <= 15.0:
            return (f"Pin con {percent:.0f} phan tram. Nen ket thuc tuyen "
                    "duong hien tai va cam sac.")
        return f"Pin con {percent:.0f} phan tram."

    def reset(self) -> None:
        self._announced.clear()
        self.last_percent = None


@dataclass
class DetectionHealth:
    """
    Phat hien viec nhan dien SUP DO giua chung.

    Nguyen tac: chi canh bao khi truoc do DA TUNG bat duoc moc neo deu
    dan roi dot ngot mat han. Neu ngay tu dau da khong bat duoc gi thi
    do la van de lap dat (goc camera, kich thuoc ma) chu khong phai
    thiet bi bi lech giua duong - hai tinh huong can hai cau khac nhau.
    """

    window: int = HEALTH_WINDOW
    _recent: deque = field(default_factory=lambda: deque(maxlen=HEALTH_WINDOW))
    _was_healthy: bool = False
    _warned: bool = False
    total_hits: int = 0
    total_frames: int = 0

    def __post_init__(self) -> None:
        self._recent = deque(maxlen=self.window)

    def update(self, saw_anchor: bool) -> str | None:
        self._recent.append(bool(saw_anchor))
        self.total_frames += 1
        if saw_anchor:
            self.total_hits += 1

        hits = sum(self._recent)

        # Danh dau da tung khoe, de phan biet "hong giua chung" voi
        # "lap dat sai tu dau"
        if hits >= HEALTHY_MIN_HITS:
            self._was_healthy = True
            self._warned = False
            return None

        if len(self._recent) < self.window:
            return None                    # chua du du lieu de ket luan

        ratio = hits / len(self._recent)
        if self._was_healthy and ratio < COLLAPSE_RATIO and not self._warned:
            self._warned = True
            return ("Da mot luc khong doc duoc moc nao. Kiem tra xem dien "
                    "thoai co bi xoay lech tren day deo khong.")
        return None

    @property
    def hit_ratio(self) -> float:
        return self.total_hits / self.total_frames if self.total_frames else 0.0

    def reset(self) -> None:
        self._recent.clear()
        self._was_healthy = False
        self._warned = False
        self.total_hits = 0
        self.total_frames = 0


@dataclass
class SystemHealth:
    """Gom cac bo theo doi lai mot cho, de vong lap chinh goi mot lan."""

    battery: BatteryMonitor = field(default_factory=BatteryMonitor)
    detection: DetectionHealth = field(default_factory=DetectionHealth)

    def update(self, saw_anchor: bool = False,
               battery_percent: float | None = None) -> list[str]:
        """
        Tra ve danh sach cau can noi, uu tien pin truoc.

        Pin len truoc vi no la rang buoc CUNG: het pin thi moi thu khac
        vo nghia, con camera lech thi con sua duoc tai cho.
        """
        out = []
        msg = self.battery.update(battery_percent)
        if msg:
            out.append(msg)
        msg = self.detection.update(saw_anchor)
        if msg:
            out.append(msg)
        return out

    def reset(self) -> None:
        self.battery.reset()
        self.detection.reset()
