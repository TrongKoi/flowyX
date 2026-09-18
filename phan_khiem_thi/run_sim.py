#!/usr/bin/env python3
"""
Chay thu toan bo pipeline BANG MO PHONG - khong can camera.

Day la thu nen chay DAU TIEN. No kiem chung tim duong, sinh cau chi dan,
mo hinh do tin cay va co che phuc hoi khi di lac, ma khong phu thuoc vao
phan cung hay hieu chinh camera.

Mo phong theo doi dong thoi tu the THAT va tu the VIO CO TROI, roi tinh
xem camera thuc su nhin thay moc neo o dau - dung nhu ngoai doi thuc.

Chay:
    python3 run_sim.py
    python3 run_sim.py --to R16 --drift 0.06
    python3 run_sim.py --detour            # kiem thu co che phuc hoi
    python3 run_sim.py --no-anchors        # xem do tin cay suy giam
"""

from __future__ import annotations

import argparse

from wayfinding.loi_chung.anchors import AnchorSighting
from wayfinding.loi_chung.floormap import load_map
from wayfinding.loi_chung.geometry import (
    Pose2D, angle_diff, bearing, decompose, inv_se2,
)
from wayfinding.loi_chung.guidance import GuidanceEngine
from wayfinding.loi_chung.localizer import Localizer
from wayfinding.loi_chung.routing import build_route
from wayfinding.loi_chung.speech import Announcer, ConsoleSpeech
from wayfinding.loi_chung.vio import SimulatedVIO

STEP_M = 0.5              # moi buoc mo phong di 0.5 met
TICK_SECONDS = 0.4        # dong ho gia lap, de Announcer chong lap dung
VIEW_RANGE = 4.0          # camera nhin thay ma trong pham vi bao nhieu met
VIEW_ANGLE = 55.0         # va trong goc nhin bao nhieu do


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default="config/map_floor3.json")
    ap.add_argument("--start", default="A")
    ap.add_argument("--to", default="R12")
    ap.add_argument("--drift", type=float, default=0.025)
    ap.add_argument("--detour", action="store_true")
    ap.add_argument("--no-anchors", action="store_true")
    args = ap.parse_args()

    fm = load_map(args.map)
    print(f"Ban do: {fm.floor}")
    print(f"  {len(fm.signs)} bien chu, {len(fm.rooms)} bien so phong, "
          f"{len(fm.nodes)} nut, {len(fm.edges)} canh\n")

    route = build_route(fm, args.start, args.to)
    if route is None:
        raise SystemExit(f"Khong tim duoc duong tu {args.start} toi {args.to}")

    names = [route.legs[0].frm.name] + [l.to.name for l in route.legs]
    print("Tuyen: " + " -> ".join(names))
    print(f"Tong chieu dai: {route.total_length:.1f} met\n" + "-" * 64)

    vio = SimulatedVIO(drift_rate=args.drift, seed=42)
    start_node = fm.nodes[args.start]
    vio.place(start_node.x, start_node.y, route.legs[0].heading)

    loc = Localizer(fm, drift_rate=args.drift)
    guide = GuidanceEngine(route)
    announcer = Announcer(backend=ConsoleSpeech(), min_gap=5.0)

    clock = 0.0
    detour_done = False
    travelled = 0.0
    target_idx = 0
    max_error = 0.0
    err = 0.0

    for _ in range(600):
        clock += TICK_SECONDS

        # --- cam nhan: co nhin thay moc neo nao khong ---
        if not args.no_anchors:
            sighting = _visible_anchor(fm, vio.true_pose())
            if sighting and loc.apply_anchor(sighting, vio.pose()):
                print(f"[NEO] {sighting.source} '{sighting.key}' "
                      f"cach {sighting.distance:.1f}m - xoa sai so tich luy")

        # --- dinh vi ---
        fix = loc.update(vio.pose())
        if fix:
            err = _dist(fix.pose.xy, vio.true_pose().xy)
            max_error = max(max_error, err)

        # --- chi dan ---
        instruction = guide.step(fix)
        if announcer.announce(instruction, now=clock) and fix:
            print(f"      uoc tinh ({fix.pose.x:5.1f},{fix.pose.y:5.1f})  "
                  f"that ({vio.true_pose().x:5.1f},{vio.true_pose().y:5.1f})  "
                  f"sai {err:.2f}m  tin cay={fix.confidence.value:12s} "
                  f"tu moc cuoi {fix.distance_since_fix:4.1f}m")

        if guide.state.value == "da_toi":
            break

        if fix and loc.should_warn_stale():
            print(f"[NOI] Da di {fix.distance_since_fix:.0f} met tu moc cuoi, "
                  "do tin cay dang giam.")

        # --- di chuyen ---
        if fix is None:
            vio.turn(20)                      # quay tim moc
            continue

        if args.detour and not detour_done and travelled > 6.0:
            print("\n>>> Mo phong: nguoi dung di lech khoi tuyen\n")
            vio.turn(75)
            for _ in range(10):
                vio.step(STEP_M)
            detour_done = True
            travelled += 5.0
            continue

        target_idx = _steer(vio, route, target_idx)
        vio.step(STEP_M)
        travelled += STEP_M

    print("-" * 64)
    print(f"Trang thai cuoi : {guide.state.value}")
    print(f"Quang duong di  : {travelled:.1f} m "
          f"(tuyen dai {route.total_length:.1f} m)")
    print(f"Sai so dinh vi lon nhat: {max_error:.2f} m")


# ------------------------------------------------------------------
# Mo phong cam nhan
# ------------------------------------------------------------------

def _visible_anchor(fm, true_pose: Pose2D) -> AnchorSighting | None:
    """
    Camera co nhin thay moc neo nao khong, va neu co thi thay o dau.

    Tinh tu the tuong doi THAT giua camera va moc, bang phep bien doi
    NGUOC voi cai Localizer dung - nen day la phep kiem tra that su
    chu khong phai tu chung minh.
    """
    T_world_cam = true_pose.as_matrix()
    best = None

    for key, pose, source in _all_anchors(fm):
        d = _dist(true_pose.xy, pose.xy)
        if d > VIEW_RANGE or d < 0.15:
            continue
        seen_at = bearing(true_pose.xy, pose.xy)
        if abs(angle_diff(seen_at, true_pose.theta)) > VIEW_ANGLE:
            continue                       # ngoai goc nhin camera

        rel = decompose(inv_se2(T_world_cam) @ pose.as_matrix())
        cand = AnchorSighting(
            key=key, source=source,
            cam_from_anchor=Pose2D(*rel),
            distance=d,
            quality=round(max(0.0, 1.0 - d / VIEW_RANGE), 3),
        )
        if best is None or cand.distance < best.distance:
            best = cand
    return best


def _all_anchors(fm):
    for k, p in fm.markers.items():
        yield k, p, "ocr"
    for k, p in fm.rooms.items():
        yield k, p, "ocr"


def _steer(vio, route, target_idx: int) -> int:
    """
    Lai nguoi dung mo phong bam theo tuyen.

    Bam theo THU TU chang, khong dung 'chang gan nhat' - o goc re, hai
    chang gan bang nhau nen chon nham se khien nguoi di vong tron.
    Tra ve chi so chang muc tieu da cap nhat.
    """
    if target_idx >= len(route.legs):
        return target_idx

    target = route.legs[target_idx].to
    if _dist(vio.true_pose().xy, target.xy) < 1.0:
        target_idx += 1                      # da toi nut nay, sang nut sau
        if target_idx >= len(route.legs):
            return target_idx
        target = route.legs[target_idx].to

    want = bearing(vio.true_pose().xy, target.xy)
    err = angle_diff(want, vio.true_pose().theta)
    if abs(err) > 3:
        vio.turn(max(-30.0, min(30.0, err)))
    return target_idx


def _dist(a, b) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


if __name__ == "__main__":
    main()
