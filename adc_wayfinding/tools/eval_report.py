#!/usr/bin/env python3
"""
Sinh BANG NGHIEM THU tu cac lan chay da ghi - Giai doan 4, Muc 17.

Bang nay di thang vao slide. Giam khao se hoi "neu no chi sai thi sao"
- cau tra loi tot nhat la mot bang so lieu that.

Chay:
    python3 tools/eval_report.py runs.json
    python3 tools/eval_report.py runs.json --markdown > ketqua.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wayfinding.loi_chung.metrics import check_targets, summarize   # noqa: E402

MARK = {True: "DAT", False: "CHUA DAT", None: "CHUA DO"}


def fmt(value, key: str) -> str:
    if value is None:
        return "chua do"
    if key == "arrival_rate":
        return f"{value * 100:.0f}%"
    if key in ("position_error_p95", "max_gap_m"):
        return f"{value:.2f} m"
    if key == "battery_hours":
        return f"{value:.1f} gio"
    if key == "time_ratio":
        return f"{value:.2f}x"
    return f"{value:.2f}"


def plain(summary: dict) -> None:
    print(f"\nTong hop {summary.get('runs', 0)} lan chay\n" + "=" * 62)
    rows = check_targets(summary)
    w = max(len(label) for _k, label, _g, _t, _p in rows)
    for key, label, got, target, passed in rows:
        print(f"  {label:<{w}}  {fmt(got, key):>12}  "
              f"{target:>8}  {MARK[passed]}")

    print("\nSo lieu bo sung")
    print(f"  Sai so dinh vi trung binh : "
          f"{fmt(summary.get('position_error_mean'), 'position_error_p95')}")
    print(f"  Quang duong dai nhat khong gap moc : "
          f"{fmt(summary.get('max_gap_m'), 'max_gap_m')}")
    print(f"  So lan neo trung binh moi tuyen    : "
          f"{summary.get('anchors_per_run', 0):.1f}")

    missing = [label for _k, label, _g, _t, p in rows if p is None]
    if missing:
        print("\nCHUA DO - phai noi that khi pitch, khong duoc de trong:")
        for m in missing:
            print(f"  - {m}")


def markdown(summary: dict) -> None:
    print(f"### Ket qua nghiem thu ({summary.get('runs', 0)} lan chay)\n")
    print("| Chi so | Do duoc | Muc tieu | Ket luan |")
    print("|---|---|---|---|")
    for key, label, got, target, passed in check_targets(summary):
        print(f"| {label} | {fmt(got, key)} | {target} | {MARK[passed]} |")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", help="file JSON do RunRecorder.save() sinh ra")
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args()

    path = Path(args.runs)
    if not path.exists():
        sys.exit(f"Khong tim thay {path}. Chay run_bridge.py --record truoc.")

    records = json.loads(path.read_text(encoding="utf-8"))
    if not records:
        sys.exit("File rong - chua co lan chay nao.")

    summary = summarize(records)
    (markdown if args.markdown else plain)(summary)


if __name__ == "__main__":
    main()
