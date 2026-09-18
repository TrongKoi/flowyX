"""
Ghi va tinh SAU CHI SO NGHIEM THU - Muc 17 cua tai lieu, Giai doan 4.

Co so lieu that la thu phan biet mot bai pitch nghiem tuc voi mot bai
noi suong. Giam khao se hoi "neu no chi sai thi sao" - cau tra loi tot
nhat la mot bang ket qua do duoc, khong phai mot loi hua.

Nguyen tac: DINH NGHIA NGUONG TRUOC khi do, khong dinh nghia sau khi
thay ket qua.
"""

from __future__ import annotations

from typing import Any

import json
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Nguong muc tieu - Muc 17. Chot truoc, khong sua sau khi thay so lieu.
TARGETS = {
    "arrival_rate":        (">=", 0.90, "Ty le toi dich"),
    "strays_per_run":      ("<=", 1.0,  "So lan di lac moi tuyen"),
    "time_ratio":          ("<=", 2.0,  "Thoi gian so voi nguoi dan sang mat"),
    "interventions":       ("==", 0.0,  "So lan can nguoi can thiep"),
    "position_error_p95":  ("<=", 1.5,  "Sai so dinh vi (p95, met)"),
    "battery_hours":       (">=", 2.0,  "Thoi luong pin (gio)"),

    # --- lop phat hien chuong ngai ---
    #
    # Tach RIENG hai loai loi vi hau qua khac han nhau, va danh doi
    # giua chung la quyet dinh THIET KE chu khong phai quyet dinh ky
    # thuat. Giam khao se hoi.
    #
    #   Bo sot  -> nguoi dung vap nga. NGHIEM TRONG.
    #   Bao thua -> nguoi dung mat tin, roi TAT he thong. Hong hoan toan.
    #
    # Nen phai do CA HAI. Do mot minh ty le phat hien la tu lua minh:
    # bao moi khung hinh thi ty le phat hien 100%, va khong ai dung noi.
    "missed_obstacles":    ("==", 0.0,  "Bo sot vat cao tren 15cm trong 2m"),
    "false_alarms_per_min": ("<=", 1.0, "Bao dong gia moi phut, hanh lang trong"),
    "alert_latency_ms":    ("<=", 400.0, "Do tre canh bao (p95, ms)"),
}


@dataclass
class RunRecord:
    """Mot lan chay thu."""

    route: str
    tester: str = ""
    blindfolded: bool = False
    arrived: bool = False
    strays: int = 0                       # so lan lech khoi tuyen qua 3m
    interventions: int = 0                # so lan nguoi di kem phai nhac
    duration_s: float = 0.0
    baseline_s: float | None = None       # thoi gian khi co nguoi dan
    route_length_m: float = 0.0
    travelled_m: float = 0.0
    position_errors: list[float] = field(default_factory=list)
    battery_start: float | None = None
    battery_end: float | None = None
    anchors_seen: int = 0
    max_gap_m: float = 0.0                # quang duong dai nhat khong gap moc
    notes: str = ""
    timestamp: float = field(default_factory=time.time)

    @property
    def time_ratio(self) -> float | None:
        if not self.baseline_s or self.duration_s <= 0:
            return None
        return self.duration_s / self.baseline_s

    @property
    def detour_ratio(self) -> float | None:
        """Di dai hon tuyen bao nhieu lan - dau hieu lac duong am tham."""
        if self.route_length_m <= 0:
            return None
        return self.travelled_m / self.route_length_m


class RunRecorder:
    """
    Ghi lai mot lan chay thu trong luc dang chay.

    Dung trong run_live.py va run_bridge.py de moi lan di thu deu sinh
    ra so lieu, thay vi phai nho lai sau.
    """

    def __init__(self, route_name: str, route_length_m: float,
                 tester: str = "", blindfolded: bool = False):
        self.rec = RunRecord(
            route=route_name,
            route_length_m=route_length_m,
            tester=tester,
            blindfolded=blindfolded,
        )
        self._t0 = time.time()
        self._was_off_route = False
        self._last_fix_distance = 0.0

    def on_fix(self, fix, truth_xy: tuple[float, float] | None = None) -> None:
        if fix is None:
            return
        if truth_xy is not None:
            err = ((fix.pose.x - truth_xy[0]) ** 2 +
                   (fix.pose.y - truth_xy[1]) ** 2) ** 0.5
            self.rec.position_errors.append(err)
        self.rec.max_gap_m = max(self.rec.max_gap_m, fix.distance_since_fix)

    def on_anchor(self) -> None:
        self.rec.anchors_seen += 1

    def on_state(self, state: str) -> None:
        """Dem lan di lac: chi dem khi CHUYEN sang trang thai lac."""
        off = state == "di_lac"
        if off and not self._was_off_route:
            self.rec.strays += 1
        self._was_off_route = off
        if state == "da_toi":
            self.rec.arrived = True

    def on_intervention(self) -> None:
        self.rec.interventions += 1

    def on_travel(self, meters: float) -> None:
        self.rec.travelled_m += meters

    def set_battery(self, start: float | None = None,
                    end: float | None = None) -> None:
        if start is not None:
            self.rec.battery_start = start
        if end is not None:
            self.rec.battery_end = end

    def finish(self, notes: str = "") -> RunRecord:
        self.rec.duration_s = time.time() - self._t0
        self.rec.notes = notes
        return self.rec

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        runs = []
        if p.exists():
            try:
                runs = json.loads(p.read_text(encoding="utf-8"))
            except ValueError:
                runs = []
        runs.append(asdict(self.rec))
        p.write_text(json.dumps(runs, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        return p


# --------------------------------------------------------------------

def percentile(values: list[float], q: float) -> float | None:
    """Phan vi thu q (0..1). Dung p95 chu khong dung max, vi max qua nhay cam."""
    if not values:
        return None
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    idx = q * (len(s) - 1)
    lo, hi = int(idx), min(int(idx) + 1, len(s) - 1)
    frac = idx - lo
    return s[lo] * (1 - frac) + s[hi] * frac


def summarize(records: list[RunRecord | dict]) -> dict:
    """Tong hop nhieu lan chay thanh sau chi so."""
    recs = [r if isinstance(r, RunRecord) else RunRecord(**r) for r in records]
    if not recs:
        return {}

    errors: list[float] = []
    for r in recs:
        errors.extend(r.position_errors)

    ratios = [r.time_ratio for r in recs if r.time_ratio is not None]

    battery_hours = None
    for r in recs:
        if (r.battery_start is not None and r.battery_end is not None
                and r.duration_s > 0):
            used = r.battery_start - r.battery_end
            if used > 0.5:
                # Ngoai suy tu 100% xuong 20% (nguong dung duoc)
                hours = (r.duration_s / 3600.0) * (80.0 / used)
                battery_hours = hours if battery_hours is None else min(
                    battery_hours, hours)

    return {
        "runs": len(recs),
        "arrival_rate": sum(1 for r in recs if r.arrived) / len(recs),
        "strays_per_run": statistics.mean(r.strays for r in recs),
        "interventions": statistics.mean(r.interventions for r in recs),
        "time_ratio": statistics.mean(ratios) if ratios else None,
        "position_error_p95": percentile(errors, 0.95),
        "position_error_mean": statistics.mean(errors) if errors else None,
        "battery_hours": battery_hours,
        "max_gap_m": max(r.max_gap_m for r in recs),
        "anchors_per_run": statistics.mean(r.anchors_seen for r in recs),
    }


def check_targets(summary: dict) -> list[tuple[str, str, Any, Any, bool | None]]:
    """
    Doi chieu ket qua voi nguong muc tieu.

    Tra ve danh sach (khoa, mo ta, gia tri do duoc, nguong, dat/khong).
    Gia tri None nghia la CHUA DO - phai noi that la chua do, khong
    duoc de trong roi ngu y la dat.
    """
    out = []
    for key, (op, target, label) in TARGETS.items():
        got = summary.get(key)
        if got is None:
            passed = None
        elif op == ">=":
            passed = got >= target
        elif op == "<=":
            passed = got <= target
        else:
            passed = abs(got - target) < 1e-9
        out.append((key, label, got, f"{op} {target}", passed))
    return out
