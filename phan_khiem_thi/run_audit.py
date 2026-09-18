#!/usr/bin/env python3
"""
KICH BAN F - bao cao khao sat do tiep can cua toa nha.

Doi goc nhin: bon kich ban kia trang bi cho CA NHAN, kich ban nay lam
cho TOA NHA tiep can duoc. Bao cao nay tra loi truc tiep cau hoi ma
giam khao chac chan hoi - ai bo tien, va bao nhieu.

Chay:
    python3 run_audit.py
    python3 run_audit.py --map config/map_floor3.json --target 0.98
    python3 run_audit.py --markdown > khaosat.md
"""

from __future__ import annotations

import argparse
import sys

from wayfinding.khiemthi.audit import (
    COST_PER_MARKER_VND, MINUTES_PER_MARKER, audit_floor,
)
from wayfinding.loi_chung.floormap import load_map
from wayfinding.loi_chung.localizer import Confidence


def bar(ratio: float, width: int = 30) -> str:
    filled = int(round(ratio * width))
    return "#" * filled + "." * (width - filled)


def plain(fm, report, target: float) -> None:
    print(f"\nKHAO SAT DO TIEP CAN — {fm.floor}")
    print("=" * 66)

    counts = {c: 0 for c in Confidence}
    for s in report.samples:
        counts[s.confidence] += 1
    total = max(len(report.samples), 1)

    print(f"\n1. DO PHU HIEN TAI: {report.coverage:.0%}")
    print(f"   [{bar(report.coverage)}]")
    print(f"\n   Do tin cay tren {total} diem doc theo cac loi di:")
    for c, label in ((Confidence.HIGH, "Cao — chi duong day du"),
                     (Confidence.MEDIUM, "Trung binh — khong canh bao nguy hiem"),
                     (Confidence.LOW, "Thap — tu choi chi duong")):
        n = counts[c]
        print(f"     {label:42s} {n:4d} diem  ({n / total:4.0%})")

    if report.gaps:
        print(f"\n2. {len(report.gaps)} DOAN THIEU DO TIN CAY")
        for g in report.gaps[:6]:
            print(f"   - {g.describe(fm)}")
        if len(report.gaps) > 6:
            print(f"   ... con {len(report.gaps) - 6} doan nua")
    else:
        print("\n2. KHONG CO DOAN NAO THIEU DO TIN CAY")

    if report.suggestions:
        print(f"\n3. DE XUAT DAN THEM {len(report.suggestions)} MA")
        for i, s in enumerate(report.suggestions, 1):
            a = fm.nodes[s.near_edge[0]].name
            b = fm.nodes[s.near_edge[1]].name
            print(f"   {i}. Toa do ({s.x:.1f}, {s.y:.1f}) — tren doan {a} - {b}")
            print(f"      do phu {s.coverage_before:.0%} -> "
                  f"{s.coverage_after:.0%}  (+{s.gain:.0%})")
        print(f"\n   Do phu sau khi dan: {report.coverage_after:.0%} "
              f"(muc tieu {target:.0%})")
    else:
        print(f"\n3. KHONG CAN DAN THEM MA — da dat muc tieu {target:.0%}")

    print("\n4. CHI PHI TRIEN KHAI")
    print(f"   Vat tu   : {report.cost_vnd:,} dong "
          f"({len(report.suggestions)} ma x {COST_PER_MARKER_VND:,} dong)")
    print(f"   Gio cong : {report.minutes} phut "
          f"({MINUTES_PER_MARKER} phut moi ma, gom do toa do)")
    print("   Van hanh : 0 dong/nam — khong pin, khong dien, khong bao tri")

    if report.rooms_without_signs:
        print(f"\n5. {len(report.rooms_without_signs)} PHONG CHUA KHAI BAO BIEN SO")
        for name in report.rooms_without_signs[:8]:
            print(f"   - {name}")
        print("   Bien so phong la lop dinh vi KHONG TON CHI PHI trien khai —")
        print("   bo sot la bo phi thu da co san.")

    if report.hazards_without_warning:
        print(f"\n6. {len(report.hazards_without_warning)} DOAN NGUY HIEM "
              "CHUA GHI CANH BAO")
        for name in report.hazards_without_warning:
            print(f"   - {name}")
        print("   He thong se KHONG canh bao o nhung doan nay.")

    print("\n" + "=" * 66)


def markdown(fm, report, target: float) -> None:
    print(f"## Khao sat do tiep can — {fm.floor}\n")
    print(f"**Do phu hien tai:** {report.coverage:.0%}  ")
    print(f"**Do phu sau de xuat:** {report.coverage_after:.0%}  ")
    print(f"**Chi phi:** {report.cost_vnd:,} dong, {report.minutes} phut\n")

    if report.suggestions:
        print("| # | Toa do | Do phu truoc | Do phu sau |")
        print("|---|---|---|---|")
        for i, s in enumerate(report.suggestions, 1):
            print(f"| {i} | ({s.x:.1f}, {s.y:.1f}) | "
                  f"{s.coverage_before:.0%} | {s.coverage_after:.0%} |")
        print()

    if report.gaps:
        print("### Doan thieu do tin cay\n")
        for g in report.gaps[:8]:
            print(f"- {g.describe(fm)}")
        print()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default="config/map_floor3.json")
    ap.add_argument("--target", type=float, default=0.95,
                    help="do phu muc tieu, vd 0.95")
    ap.add_argument("--max-markers", type=int, default=10)
    ap.add_argument("--drift", type=float, default=None,
                    help="ty le troi do duoc; mac dinh lay tu localizer")
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args()

    try:
        fm = load_map(args.map)
    except (ValueError, FileNotFoundError) as e:
        sys.exit(f"Khong doc duoc ban do: {e}")

    kw = {}
    if args.drift is not None:
        kw["drift_rate"] = args.drift

    report = audit_floor(fm, target=args.target,
                         max_markers=args.max_markers, **kw)
    (markdown if args.markdown else plain)(fm, report, args.target)


if __name__ == "__main__":
    main()
