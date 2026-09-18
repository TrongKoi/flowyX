"""
KICH BAN F - cong cu khao sat cho bo phan quan ly toa nha.

Rao can noi lam viec: khong ai biet toa nha kem tiep can o CHO NAO. Bo
phan hanh chinh muon cai thien cung khong biet bat dau tu dau, va khong
co so lieu de xin ngan sach.

Day la kich ban DOI GOC NHIN: bon kich ban kia trang bi cho CA NHAN,
kich ban nay lam cho TOA NHA tiep can duoc. No cung tra loi truc tiep
cau hoi ma giam khao chac chan hoi - ai bo tien, va bao nhieu.

--------------------------------------------------------------------
CACH DO DO PHU
--------------------------------------------------------------------

Sai so cua he thong tich luy theo QUANG DUONG DI ke tu moc neo gan nhat,
khong phai theo khoang cach duong chim bay. Mot cai phong cach moc neo
3m duong chim bay nhung phai di vong 40m thi van la diem mu.

Nen do do phu bang khoang cach TREN DO THI:
  1. Chay Dijkstra da nguon tu tat ca cac moc neo.
  2. Ray diem doc theo tung canh, moi diem tinh khoang cach toi moc gan
     nhat theo duong di that.
  3. Doi ra do tin cay bang dung mo hinh o localizer.py.

Do phu = ty le diem dat do tin cay CAO.

--------------------------------------------------------------------
CACH DE XUAT DAN THEM MA
--------------------------------------------------------------------

Tham lam: dan mot ma vao dung diem te nhat, tinh lai do phu, lap lai.
Cach nay khong toi uu tuyet doi nhung cho ket qua rat gan, va quan trong
hon la GIAI THICH DUOC: "dan ma o day vi day la cho te nhat".
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

from ..loi_chung.floormap import FloorMap
from ..loi_chung.localizer import DEFAULT_DRIFT_RATE, Confidence

# Khoang cach giua cac diem ray doc theo canh, don vi met.
SAMPLE_STEP_M = 1.0

# Chi phi vat tu mot ma, dong. Giay in cong bang keo giay.
COST_PER_MARKER_VND = 10_000

# Thoi gian dan mot ma, phut. Gom do toa do va ghi vao ban do.
MINUTES_PER_MARKER = 5


@dataclass
class SamplePoint:
    """Mot diem ray tren tuyen di, kem do tin cay dat duoc o do."""

    edge_from: str
    edge_to: str
    t: float                      # vi tri tren canh, 0..1
    x: float
    y: float
    dist_to_anchor: float         # khoang cach TREN DO THI toi moc gan nhat
    confidence: Confidence


@dataclass
class Gap:
    """Mot doan lien tuc bi mat do tin cay."""

    edge_from: str
    edge_to: str
    length_m: float
    worst_distance: float
    worst_xy: tuple[float, float]

    def describe(self, fm: FloorMap) -> str:
        a = fm.nodes[self.edge_from].name
        b = fm.nodes[self.edge_to].name
        return (f"Doan {a} - {b}: {self.length_m:.0f}m khong du do tin cay, "
                f"xa moc nhat {self.worst_distance:.0f}m")


@dataclass
class Suggestion:
    """Mot ma de xuat dan them."""

    x: float
    y: float
    near_edge: tuple[str, str]
    coverage_before: float
    coverage_after: float

    @property
    def gain(self) -> float:
        return self.coverage_after - self.coverage_before


@dataclass
class AuditReport:
    coverage: float                          # ty le diem dat do tin cay cao
    samples: list[SamplePoint] = field(default_factory=list)
    gaps: list[Gap] = field(default_factory=list)
    rooms_without_signs: list[str] = field(default_factory=list)
    hazards_without_warning: list[str] = field(default_factory=list)
    suggestions: list[Suggestion] = field(default_factory=list)

    @property
    def cost_vnd(self) -> int:
        return len(self.suggestions) * COST_PER_MARKER_VND

    @property
    def minutes(self) -> int:
        return len(self.suggestions) * MINUTES_PER_MARKER

    @property
    def coverage_after(self) -> float:
        return (self.suggestions[-1].coverage_after
                if self.suggestions else self.coverage)


# --------------------------------------------------------------------
# Khoang cach tren do thi tu cac moc neo
# --------------------------------------------------------------------

def anchor_nodes(fm: FloorMap, extra: list[tuple[float, float]] | None = None
                 ) -> set[str]:
    """Cac nut co moc neo o gan. Moc neo nam tren tuong, gan mot nut."""
    ids: set[str] = set()
    poses = [p.xy for p in fm.markers.values()]
    poses += [p.xy for p in fm.rooms.values()]
    poses += list(extra or [])

    for xy in poses:
        node = fm.node_at(xy, tol=2.0)
        if node is not None:
            ids.add(node.id)
    return ids


def distance_from_anchors(fm: FloorMap,
                          sources: set[str]) -> dict[str, float]:
    """Dijkstra da nguon: khoang cach tu moi nut toi moc neo gan nhat."""
    dist = {n: math.inf for n in fm.nodes}
    pq: list[tuple[float, str]] = []
    for s in sources:
        if s in dist:
            dist[s] = 0.0
            heapq.heappush(pq, (0.0, s))

    adj: dict[str, list[tuple[str, float]]] = {n: [] for n in fm.nodes}
    for e in fm.edges:
        adj[e.frm].append((e.to, e.length))
        adj[e.to].append((e.frm, e.length))

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def _confidence_for(distance: float, drift_rate: float) -> Confidence:
    """Dung dung mo hinh o localizer.py de khong bi lech hai noi."""
    drift = drift_rate * distance
    if drift < 1.0:
        return Confidence.HIGH
    if drift < 3.0:
        return Confidence.MEDIUM
    return Confidence.LOW


def sample_coverage(fm: FloorMap, sources: set[str],
                    drift_rate: float = DEFAULT_DRIFT_RATE,
                    step: float = SAMPLE_STEP_M) -> list[SamplePoint]:
    """Ray diem doc theo moi canh va tinh do tin cay dat duoc o tung diem."""
    dist = distance_from_anchors(fm, sources)
    out: list[SamplePoint] = []

    for e in fm.edges:
        a, b = fm.nodes[e.frm], fm.nodes[e.to]
        n = max(2, int(e.length / step) + 1)
        for i in range(n):
            t = i / (n - 1)
            # Di tu dau nao gan moc hon
            d = min(dist[e.frm] + t * e.length,
                    dist[e.to] + (1.0 - t) * e.length)
            out.append(SamplePoint(
                edge_from=e.frm, edge_to=e.to, t=t,
                x=a.x + t * (b.x - a.x),
                y=a.y + t * (b.y - a.y),
                dist_to_anchor=d,
                confidence=_confidence_for(d, drift_rate),
            ))
    return out


def coverage_ratio(samples: list[SamplePoint]) -> float:
    if not samples:
        return 0.0
    good = sum(1 for s in samples if s.confidence is Confidence.HIGH)
    return good / len(samples)


# --------------------------------------------------------------------
# Tim doan mat do tin cay
# --------------------------------------------------------------------

def find_gaps(fm: FloorMap, samples: list[SamplePoint]) -> list[Gap]:
    """Gom cac diem lien tuc khong dat do tin cay cao thanh tung doan."""
    gaps: list[Gap] = []
    by_edge: dict[tuple[str, str], list[SamplePoint]] = {}
    for s in samples:
        by_edge.setdefault((s.edge_from, s.edge_to), []).append(s)

    for (frm, to), pts in by_edge.items():
        pts.sort(key=lambda p: p.t)
        edge = fm.edge_between(frm, to)
        if edge is None:
            continue

        run: list[SamplePoint] = []
        for p in pts + [None]:                     # None de dong doan cuoi
            bad = p is not None and p.confidence is not Confidence.HIGH
            if bad:
                run.append(p)
                continue
            if len(run) >= 2:
                worst = max(run, key=lambda q: q.dist_to_anchor)
                length = (run[-1].t - run[0].t) * edge.length
                gaps.append(Gap(
                    edge_from=frm, edge_to=to,
                    length_m=length,
                    worst_distance=worst.dist_to_anchor,
                    worst_xy=(worst.x, worst.y),
                ))
            run = []

    gaps.sort(key=lambda g: g.worst_distance, reverse=True)
    return gaps


# --------------------------------------------------------------------
# De xuat dan them ma
# --------------------------------------------------------------------

def suggest_markers(fm: FloorMap, target: float = 0.95,
                    max_markers: int = 10,
                    drift_rate: float = DEFAULT_DRIFT_RATE
                    ) -> tuple[list[Suggestion], list[SamplePoint]]:
    """
    Tham lam: dan ma vao dung diem te nhat, tinh lai, lap lai.

    Khong toi uu tuyet doi nhung ket qua rat gan, va quan trong hon la
    GIAI THICH DUOC voi bo phan quan ly: dan o day vi day la cho te nhat.
    """
    extra: list[tuple[float, float]] = []
    suggestions: list[Suggestion] = []

    sources = anchor_nodes(fm, extra)
    samples = sample_coverage(fm, sources, drift_rate)
    cov = coverage_ratio(samples)

    for _ in range(max_markers):
        if cov >= target:
            break

        worst = max(samples, key=lambda s: s.dist_to_anchor)
        if worst.dist_to_anchor <= 0:
            break

        extra.append((worst.x, worst.y))
        new_sources = anchor_nodes(fm, extra)
        new_samples = sample_coverage(fm, new_sources, drift_rate)
        new_cov = coverage_ratio(new_samples)

        if new_cov <= cov + 1e-9:
            break                          # khong cai thien duoc nua

        suggestions.append(Suggestion(
            x=worst.x, y=worst.y,
            near_edge=(worst.edge_from, worst.edge_to),
            coverage_before=cov, coverage_after=new_cov,
        ))
        samples, cov = new_samples, new_cov

    return suggestions, samples


# --------------------------------------------------------------------
# Khao sat day du
# --------------------------------------------------------------------

def audit_floor(fm: FloorMap, target: float = 0.95,
                max_markers: int = 10,
                drift_rate: float = DEFAULT_DRIFT_RATE) -> AuditReport:
    sources = anchor_nodes(fm)
    samples = sample_coverage(fm, sources, drift_rate)
    cov = coverage_ratio(samples)

    suggestions, _ = suggest_markers(fm, target, max_markers, drift_rate)

    # Phong khong co bien de doc bang OCR - lop dinh vi khong ton chi phi
    rooms_missing = [
        n.name for n in fm.nodes.values()
        if _looks_like_room(n.name) and not _has_sign(fm, n)
    ]

    # Canh di ngang nguy hiem ma khong ghi canh bao
    hazards_missing = [
        f"{fm.nodes[e.frm].name} - {fm.nodes[e.to].name}"
        for e in fm.edges
        if _touches_stairs(fm, e) and not e.hazard
    ]

    return AuditReport(
        coverage=cov,
        samples=samples,
        gaps=find_gaps(fm, samples),
        rooms_without_signs=rooms_missing,
        hazards_without_warning=hazards_missing,
        suggestions=suggestions,
    )


def _looks_like_room(name: str) -> bool:
    low = name.lower()
    return "phong" in low and "hop" not in low[:4]


def _has_sign(fm: FloorMap, node) -> bool:
    for pose in fm.rooms.values():
        if math.dist(node.xy, pose.xy) <= 2.0:
            return True
    return False


def _touches_stairs(fm: FloorMap, edge) -> bool:
    """
    Canh nay co di ngang cau thang khong.

    Phai loai "thang may": no chua chu "thang" nhung khong phai cau
    thang. Bao dong gia lam bao cao mat tin cay.
    """
    if edge.is_stairs:
        return True
    for nid in (edge.frm, edge.to):
        low = fm.nodes[nid].name.lower()
        if "thang may" in low or "lift" in low or "elevator" in low:
            continue
        if "thang" in low or "bac " in low:
            return True
    return False
