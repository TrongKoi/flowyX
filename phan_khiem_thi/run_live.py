#!/usr/bin/env python3
"""
Chay that voi webcam - GIAI DOAN 1, moc 12/9 cua lo trinh.

Muc tieu: di that trong hanh lang voi laptop va webcam, nghe duoc chi
dan dung. Giu ban nay chay duoc lam PHUONG AN DEMO DU PHONG, doc lap
voi viec app dien thoai co kip hay khong.

Chuan bi truoc khi chay:
  1. Do toa do bien chu (bien tang, bien thoat hiem, so phong) bang
     thuoc, nhap vao config/map_floor3.json
  2. python3 tools/validate_map.py config/map_floor3.json --strict

KHONG can hieu chinh camera bang bang co vua, va KHONG can in ma dan
len tuong. Tieu cu duoc uoc tu goc nhin ngang; moc neo la bien chu san
co trong toa nha. Hai rang buoc do da bo tu dot go ArUco.

Chay:
    python3 run_live.py --to R12
    python3 run_live.py --to R12 --speak           # doc thanh tieng that
    python3 run_live.py --to R12 --show            # hien khung hinh (de debug)

LUU Y ve VIO: tren laptop khong co ARCore, nen dung MonocularVIO - do
chuyen dong tho tu webcam. No troi nhanh hon ARCore that nhieu va khong
biet ty le. Du de chung minh nguyen ly, KHONG du de dung that. Ban that
phai chay ARCore tren dien thoai (Muc 15).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from wayfinding.loi_chung.anchors import (AsyncRoomSignReader, RoomSignReader,
                                SightingFilter, sign_heights, sign_texts,
                                uoc_focal_px)
from wayfinding.loi_chung.floormap import load_map
from wayfinding.loi_chung.geometry import Pose2D
from wayfinding.loi_chung.guidance import GuidanceEngine, Instruction
from wayfinding.loi_chung.health import SystemHealth
from wayfinding.loi_chung.localizer import InstructionKind, Localizer
from wayfinding.loi_chung.routing import build_route
from wayfinding.loi_chung.session import SessionRecorder, summarize_session
from wayfinding.khiemthi.stabilize import BestOfBurst, SharpnessGate, sharpness
from wayfinding.loi_chung.speech import Announcer, AsyncSpeech, ConsoleSpeech
from wayfinding.loi_chung.vio import MonocularVIO


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default="config/map_floor3.json")
    ap.add_argument("--camera", default="camera.npz")
    ap.add_argument("--start", default="A")
    ap.add_argument("--to", required=True)
    ap.add_argument("--marker-size", type=float, default=0.20,
                    help="canh ma DO THAT sau khi in, don vi met")
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--speak", action="store_true", help="doc thanh tieng that")
    ap.add_argument("--show", action="store_true", help="hien khung hinh de debug")
    ap.add_argument("--ocr", action="store_true", help="bat lop OCR (cham)")
    ap.add_argument("--record", metavar="FILE",
                    help="ghi lai buoi di thu de phat lai sau (.jsonl)")
    ap.add_argument("--save-images", action="store_true",
                    help="ghi kem anh - nang hon nhung chay lai duoc ca "
                         "phan nhan dien")
    ap.add_argument("--tester", default="", help="ten nguoi di thu, de ghi lai")
    ap.add_argument("--no-vio", action="store_true",
                    help="CHE DO CHI DUNG MA: bo VIO, chi dinh vi khi nhin "
                         "thay ma. On dinh nhat cho lan chay that dau tien")
    ap.add_argument("--burst", type=int, default=1,
                    help="gom N khung hinh roi chi xu ly cai NET NHAT")
    ap.add_argument("--sharp-ratio", type=float, default=0.0,
                    help="bo khung hinh nhoe hon ty le nay so voi muc net "
                         "nhat gan day (0 = tat)")
    args = ap.parse_args()

    # --- nap cau hinh ---
    #
    # KHONG con doi camera.npz. Truoc day cho nay THOAT HAN neu thieu tep
    # hieu chinh, trong khi ngay dong duoi lai dat K = dist = None va
    # khong dung den chung - tuc la doi mot tep roi bo qua chinh tep do.
    #
    # Hieu chinh bang BANG CO VUA la rao can that su lon cho viec chi
    # muon chay thu, va no khong con can thiet:
    #
    #   duong dien thoai  -> ARCore/ARKit cho san thong so noi tai
    #   duong webcam      -> uoc tieu cu tu goc nhin (uoc_focal_px)
    #
    # Ai can do chinh xac hon van chay tools/calibrate.py duoc, va gia
    # tri trong tep se duoc UU TIEN hon uoc luong.
    focal_px = None
    if Path(args.camera).exists():
        try:
            cam = np.load(args.camera)
            focal_px = float(cam["K"][0, 0])
            print(f"Tieu cu tu {args.camera}: {focal_px:.0f} px")
        except (OSError, KeyError, IndexError, ValueError) as e:
            print(f"Khong doc duoc {args.camera} ({e}), se uoc tu goc nhin.")

    fm = load_map(args.map)
    route = build_route(fm, args.start, args.to)
    if route is None:
        sys.exit(f"Khong tim duoc duong tu {args.start} toi {args.to}")

    names = [route.legs[0].frm.name] + [l.to.name for l in route.legs]
    print("Tuyen: " + " -> ".join(names))
    print(f"Tong chieu dai: {route.total_length:.1f} met")
    print("Nhan Q de thoat.\n")

    # --- dung cac khoi ---
    if not args.ocr:
        print("CANH BAO: khong bat lop moc neo nao. Them --ocr de doc "
              "bien so phong va bien chu san co trong toa nha.")
    # OCR chay tren luong nen: easyocr mat 0.5-2 giay moi lan goi,
    # chay dong bo trong vong lap nay se keo tut fps. Xem issue #10.
    # Truyen ca known_signs, neu khong thi lop bien chu (bien thoat hiem,
    # so tang) khong bao gio duoc doc - dung lop thay the ArUco o nga re.
    doc_bien = RoomSignReader(
        set(fm.rooms),
        known_signs=sign_texts(fm),
        sign_heights=sign_heights(fm),
    ) if args.ocr else None
    ocr = AsyncRoomSignReader(doc_bien) if doc_bien is not None else None
    filt = SightingFilter(required=3)

    # CHE DO CHI DUNG MA: bo VIO han. Chi biet vi tri dung luc nhin thay
    # ma, giua cac ma thi noi that la chua chac. Kem chinh xac hon nhung
    # ON DINH NHAT - khong co gi de troi, khong co ty le de hieu chinh.
    # Nen dung che do nay cho lan chay that DAU TIEN, roi moi bat VIO.
    vio = None if args.no_vio else MonocularVIO()

    loc = Localizer(fm)
    guide = GuidanceEngine(route)

    # Loc khung hinh nhoe. Voi nguoi run tay hoac day deo con lac lac,
    # cac khung hinh net va nhoe xen ke nhau - chon cai net nhat trong
    # mot chum cho ket qua tot hon han xu ly khung hinh bat ky.
    burst = BestOfBurst(size=args.burst) if args.burst > 1 else None
    sharp_gate = (SharpnessGate(ratio=args.sharp_ratio)
                  if args.sharp_ratio > 0 else None)

    # Theo doi suc khoe he thong: pin va viec nhan dien sup do giua chung.
    # Ca hai deu hong AM THAM - nguoi khiem thi khong tu phat hien duoc.
    health = SystemHealth()

    recorder = None
    if args.record:
        recorder = SessionRecorder(
            args.record,
            meta={"route": f"{args.start}->{args.to}", "map": args.map,
                  "tester": args.tester, "marker_size": args.marker_size,
                  "no_vio": args.no_vio},
            save_images=args.save_images,
        )
        print(f"Dang ghi buoi di thu vao {args.record}")

    backend = ConsoleSpeech()
    if args.speak:
        try:
            from wayfinding.loi_chung.speech import Pyttsx3Speech
            # Boc trong AsyncSpeech: runAndWait() khoa luong den khi doc
            # xong ca cau, dat trong vong lap camera thi pipeline dung
            # vai giay dung luc nguoi dung dang di. Xem issue #9.
            backend = AsyncSpeech(Pyttsx3Speech(rate=210))
        except Exception as e:                       # noqa: BLE001
            print(f"Khong dung duoc TTS ({e}), quay ve in ra man hinh.")
    announcer = Announcer(backend=backend, min_gap=5.0)

    cap = cv2.VideoCapture(args.device)
    if not cap.isOpened():
        sys.exit(f"Khong mo duoc camera {args.device}")

    scale_calibrated = False
    last_anchor_xy = None
    t0 = time.time()
    frames = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frames += 1

            # Tieu cu: uu tien tep hieu chinh, khong co thi uoc tu goc
            # nhin. Dat MOT LAN sau khung hinh dau, vi truoc do chua biet
            # chieu rong that cua khung hinh.
            if doc_bien is not None and doc_bien.focal_px is None:
                doc_bien.focal_px = focal_px or uoc_focal_px(frame.shape[1])
                nguon = "tep hieu chinh" if focal_px else "uoc tu goc nhin"
                print(f"Tieu cu: {doc_bien.focal_px:.0f} px ({nguon})")

            # --- 0. loc khung hinh nhoe ---
            sharp = None
            if sharp_gate is not None or burst is not None:
                sharp = sharpness(frame)
            if sharp_gate is not None and not sharp_gate.accept(sharp):
                continue                      # nhoe qua, bo di cho re
            if burst is not None:
                picked = burst.push(frame, sharp)
                if picked is None:
                    continue                  # chua du chum
                frame = picked

            # --- 1. do chuyen dong ---
            # Che do chi dung ma thi khong co VIO: tu the phien luon la
            # goc toa do, nen vi tri chi cap nhat khi bat duoc ma.
            session_pose = Pose2D(0.0, 0.0, 0.0) if vio is None \
                else vio.update(frame)

            # --- 2. tim moc neo ---
            sightings = []
            if ocr is not None:
                sightings += ocr.detect(frame)

            if sightings:
                best = max(sightings, key=lambda s: s.quality)
                if filt.accept(best.key):
                    if loc.apply_anchor(best, session_pose):
                        print(f"[NEO] {best.source} '{best.key}' "
                              f"cach {best.distance:.1f}m  q={best.quality}")

                        # Hieu chinh ty le VIO bang khoang cach that
                        # giua hai moc neo lien tiep.
                        fix_now = loc.update(session_pose)
                        if fix_now and last_anchor_xy and not scale_calibrated:
                            true_d = ((fix_now.pose.x - last_anchor_xy[0]) ** 2 +
                                      (fix_now.pose.y - last_anchor_xy[1]) ** 2) ** 0.5
                            if true_d > 2.0:
                                print(f"      (goi y: hieu chinh ty le VIO "
                                      f"voi {true_d:.1f}m)")
                                scale_calibrated = True
                        if fix_now:
                            last_anchor_xy = fix_now.pose.xy

            # --- 3. dinh vi ---
            fix = loc.update(session_pose)

            # --- 4. chi dan ---
            instruction = guide.step(fix)
            announcer.announce(instruction)

            # --- 4b. suc khoe he thong ---
            # Canh bao pin va camera lech la thong tin HE THONG, phai noi
            # duoc ke ca khi dang khong dan duong. Dung kind=INFO nen
            # khong bi mo hinh do tin cay chan lai.
            for msg in health.update(saw_anchor=bool(sightings)):
                announcer.announce(Instruction(text=msg,
                                               kind=InstructionKind.INFO))

            if recorder is not None:
                recorder.log(frame_index=frames, sightings=sightings,
                             session_pose=session_pose, fix=fix,
                             instruction=instruction, sharpness=sharp,
                             frame=frame if args.save_images else None)

            if fix and loc.should_warn_stale():
                print(f"[NOI] Da di {fix.distance_since_fix:.0f} met tu moc cuoi, "
                      "do tin cay dang giam.")

            if guide.state.value == "da_toi":
                print("\nDa toi dich.")
                break

            # --- 5. hien thi de debug (nguoi dung cuoi KHONG can) ---
            if args.show:
                _draw_debug(frame, fix, sightings, guide)
                cv2.imshow("wayfinding (debug)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            elif cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        pass
    finally:
        # Dong luong nen truoc khi thoat, tranh cat ngang cau dang doc.
        for worker in (ocr, backend):
            if hasattr(worker, "close"):
                worker.close()
        cap.release()
        cv2.destroyAllWindows()
        dt = time.time() - t0
        print(f"\n{frames} khung hinh trong {dt:.1f}s "
              f"({frames / max(dt, 1e-6):.1f} fps)")

        if sharp_gate is not None and sharp_gate.seen:
            print(f"Bo vi nhoe: {sharp_gate.rejected}/{sharp_gate.seen} "
                  f"({sharp_gate.reject_ratio:.0%})")

        if recorder is not None:
            recorder.close(summary={"frames": frames,
                                    "duration_s": round(dt, 1)})
            print(f"Da ghi {recorder.count} khung hinh vao {args.record}")
            print(f"\nXem lai bang:")
            print(f"  python3 tools/replay.py {args.record}")
            print(f"  python3 tools/replay.py {args.record} --timeline")
            print(f"  python3 tools/replay.py {args.record} --gaps")


def _draw_debug(frame, fix, sightings, guide) -> None:
    """
    Khung hinh chi de LAP TRINH VIEN debug.

    Nguoi dung cuoi la nguoi khiem thi - giao dien nhin hoan toan vo
    nghia voi ho. Ban that chay nen, tat man hinh (Muc 15).
    """
    y = 26
    if fix:
        cv2.putText(frame, f"({fix.pose.x:.1f}, {fix.pose.y:.1f}) "
                           f"{fix.pose.theta:.0f}deg", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        y += 26
        cv2.putText(frame, f"tin cay: {fix.confidence.value}  "
                           f"troi~{fix.drift_estimate:.1f}m", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    else:
        cv2.putText(frame, "CHUA DINH VI", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    y += 26
    cv2.putText(frame, f"trang thai: {guide.state.value}", (10, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    for s in sightings:
        y += 24
        cv2.putText(frame, f"{s.source}:{s.key} {s.distance:.1f}m", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 160, 0), 2)


if __name__ == "__main__":
    main()
