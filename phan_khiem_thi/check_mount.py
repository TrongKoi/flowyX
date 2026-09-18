#!/usr/bin/env python3
"""
Kiem tra CACH DEO dien thoai - chong rung.

Phat hien: dien thoai treo tren day deo la mot CON LAC DON. Tan so dao
dong rieng cua no o chieu dai day thong thuong (25-45cm) TRUNG voi nhip
lac nguoi khi di bo. Day deo tu do khong giam rung ma KHUECH DAI no.

Day la ly do "deo day thong thuong quanh co" - thu de nghi den nhat -
lai la thiet ke sai cho bai toan nay.

Chay:
    python3 tools/check_mount.py
    python3 tools/check_mount.py --length 0.30
    python3 tools/check_mount.py --length 0.30 --two-point
    python3 tools/check_mount.py --cadence 95      # nguoi di cham
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wayfinding.khiemthi.stabilize import (                        # noqa: E402
    blur_from_rotation, gait_sway_band, gyro_limit_for, mount_advice,
    pendulum_frequency, resonance_risk,
)


def bar(ratio: float, width: int = 24) -> str:
    filled = int(round(max(0.0, min(1.0, ratio)) * width))
    return "#" * filled + "." * (width - filled)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--length", type=float, default=0.30,
                    help="chieu dai day deo, met")
    ap.add_argument("--two-point", action="store_true",
                    help="da neo hai diem (co day thun vong quanh than)")
    ap.add_argument("--cadence", type=float, default=110.0,
                    help="nhip buoc, buoc moi phut")
    ap.add_argument("--exposure", type=float, default=16.0,
                    help="thoi gian phoi sang, ms")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--fov", type=float, default=62.0)
    args = ap.parse_args()

    lo, hi = gait_sway_band(args.cadence)

    print("=" * 66)
    print("  KIEM TRA CACH DEO DIEN THOAI")
    print("=" * 66)

    print(f"\n1. NHIP DI BO {args.cadence:.0f} buoc/phut")
    print(f"   Than nguoi lac ngang o {lo:.2f} - {hi:.2f} Hz")
    print("   (lac ngang xay ra moi CHU KY buoc, tuc bang nua nhip chan)")

    print("\n2. TAN SO DAO DONG CUA DAY DEO")
    print("   Chi phu thuoc CHIEU DAI, khong phu thuoc khoi luong.")
    print("   Nen treo them vat nang cho 'on dinh hon' la vo ich.\n")
    for L in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.45):
        f = pendulum_frequency(L)
        risk = resonance_risk(L, args.cadence)
        mark = " <-- day cua ban" if abs(L - args.length) < 0.026 else ""
        flag = "CONG HUONG" if risk > 0.6 else "gan vung nguy hiem" \
            if risk > 0.25 else "an toan"
        print(f"   {L * 100:4.0f} cm  {f:5.2f} Hz  [{bar(risk, 16)}] "
              f"{flag}{mark}")

    print(f"\n3. DANH GIA CACH DEO HIEN TAI")
    print(f"   {mount_advice(args.length, args.two_point, args.cadence)}")

    print("\n4. BA CACH KHAC PHUC, xep theo hieu qua tren chi phi")
    print("   1. NEO HAI DIEM (tot nhat, gan nhu 0 dong)")
    print("      Them mot day thun vong quanh than, keo may ap vao nguc.")
    print("      Con lac can MOT diem treo duy nhat de dao dong; co diem")
    print("      neo thu hai thi mode con lac bien mat hoan toan.")
    print("      Vat tu: day thun ban to, hoac day ngang cua ba lo cu.")
    print("   2. DEM XOP GIUA MAY VA NGUC (0 dong)")
    print("      Ma sat giua xop va ao tieu tan nang luong dao dong.")
    print("   3. RUT NGAN DAY XUONG <= 15 cm (0 dong)")
    print("      Dua tan so len tren 1.29 Hz, tach khoi vung nhip di.")
    print("      Chi dung khi khong the lam cach 1.")

    limit = gyro_limit_for(7.0, args.exposure, args.width, args.fov)
    print(f"\n5. NGUONG LOC KHUNG HINH")
    print(f"   Voi phoi sang {args.exposure:.0f} ms, van toc goc toi da con")
    print(f"   giu duoc do nhoe duoi 7 px la {limit:.0f} do/giay.")
    print(f"   Dat MotionGate(limit_dps={limit:.0f}) de bo cac khung hinh")
    print("   chup trong luc dang xoay nhanh - re hon do do net rat nhieu.")

    for dps in (10, 25, 50, 100):
        blur = blur_from_rotation(dps, args.exposure, args.width, args.fov)
        verdict = "dat" if blur <= 7.0 else "NHOE"
        print(f"     xoay {dps:3d} do/giay -> nhoe {blur:5.1f} px  {verdict}")

    print("\n" + "=" * 66)
    print("  Con so tren la tinh toan. Van phai di thu that roi dem so")
    print("  khung hinh bat duoc ma, truoc va sau khi neo hai diem.")
    print("=" * 66 + "\n")


if __name__ == "__main__":
    main()
