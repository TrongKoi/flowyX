#!/usr/bin/env python3
"""
KICH BAN C - doc bien, tai lieu, bang trang.

Huong camera vao to giay hoac bang trang, nghe doc len. Dieu huong theo
doan bang phim, vi doc lien mot trang A4 mat vai phut va nguoi nghe
khong the quay lai doan vua roi.

Phim:
    n / Space  doan tiep theo
    p          doan truoc
    r          doc lai doan hien tai
    a          doc lai tu dau (quen van ban cu)
    q          thoat

Chay:
    python3 run_reader.py                       # webcam
    python3 run_reader.py --image to_roi.jpg    # tu mot anh co san
    python3 run_reader.py --speak               # doc thanh tieng that
    python3 run_reader.py --demo                # khong can camera lan easyocr

Kich ban nay dung lai gan nhu toan bo loi da co: khoi OCR chinh la lop
dinh vi chinh cua kich ban A, va khoi giong noi da co san chong lap va
cat loi. Cai moi chi la thu tu doc, chia doan, va co che on dinh.
"""

from __future__ import annotations

import argparse
import sys

from wayfinding.khiemthi.reader import DocumentReader, ReadState
from wayfinding.loi_chung.speech import AsyncSpeech, ConsoleSpeech

DEMO_PAGE = [
    ([[80, 60], [520, 60], [520, 110], [80, 110]], "THONG BAO HOP", 0.96),
    ([[80, 140], [640, 140], [640, 185], [80, 185]],
     "Phong hop 3.12, tang 3, toa nha 2.", 0.93),
    ([[80, 200], [700, 200], [700, 245], [80, 245]],
     "Thoi gian: 9 gio sang thu Hai ngay 21 thang 9.", 0.91),
    ([[80, 260], [720, 260], [720, 305], [80, 305]],
     "Noi dung: ra soat tien do va phan cong cong viec tuan toi.", 0.89),
    ([[80, 320], [660, 320], [660, 365], [80, 365]],
     "De nghi cac bo phan chuan bi bao cao truoc mot ngay.", 0.90),
    ([[80, 380], [600, 380], [600, 425], [80, 425]],
     "Lien he: phong hanh chinh, so noi bo 1234.", 0.88),
]


def make_speaker(use_tts: bool):
    backend = ConsoleSpeech()
    if use_tts:
        try:
            from wayfinding.loi_chung.speech import Pyttsx3Speech
            backend = Pyttsx3Speech(rate=210)
        except Exception as e:                       # noqa: BLE001
            print(f"(khong dung duoc TTS: {e} - in ra man hinh)")
    return AsyncSpeech(backend)


def say(speaker, result, wait: bool = False) -> None:
    """
    wait=True cho cac lenh nguoi dung vua bam: cau tra loi khong duoc bo.
    wait=False cho phan doc tu dong trong vong lap camera, de khong chan.
    """
    if not result.say:
        return
    if wait:
        speaker.speak_and_wait(result.say)
    else:
        speaker.speak(result.say)


def run_demo(args) -> None:
    """Chay thu khong can camera lan easyocr - de kiem tra logic."""
    speaker = make_speaker(args.speak)
    reader = DocumentReader(stable_frames=args.stable, max_chars=args.chars)

    print("Che do demo: dung mot trang van ban dung san.\n")
    for _ in range(reader.stable_frames):
        res = reader.observe(DEMO_PAGE, 1280)
    say(speaker, res)
    print(f"\nDa chia thanh {reader.total()} doan.")
    print("Go n / p / r / a / q roi Enter.\n")

    try:
        while True:
            key = input("> ").strip().lower()
            if key in ("q", "quit"):
                break
            if key in ("n", ""):
                say(speaker, reader.next_chunk(), wait=True)
            elif key == "p":
                say(speaker, reader.prev_chunk(), wait=True)
            elif key == "r":
                say(speaker, reader.repeat(), wait=True)
            elif key == "a":
                reader.reset()
                for _ in range(reader.stable_frames):
                    res = reader.observe(DEMO_PAGE, 1280)
                say(speaker, res)
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        speaker.close()


def run_camera(args) -> None:
    import cv2

    from wayfinding.loi_chung.anchors import RoomSignReader

    speaker = make_speaker(args.speak)
    reader = DocumentReader(stable_frames=args.stable, max_chars=args.chars)

    # Dung lai bo nap easyocr cua khoi OCR, khong viet lai
    ocr = RoomSignReader(known_rooms=set(), every_n_frames=1)
    engine = ocr._ensure_reader()

    if args.image:
        frame = cv2.imread(args.image)
        if frame is None:
            sys.exit(f"Khong doc duoc anh {args.image}")
        results = engine.readtext(frame)
        for _ in range(reader.stable_frames):
            res = reader.observe(results, frame.shape[1])
        say(speaker, res)
        print(f"\nDa chia thanh {reader.total()} doan. "
              "Go n / p / r / q roi Enter.\n")
        try:
            while True:
                key = input("> ").strip().lower()
                if key == "q":
                    break
                if key in ("n", ""):
                    say(speaker, reader.next_chunk(), wait=True)
                elif key == "p":
                    say(speaker, reader.prev_chunk(), wait=True)
                elif key == "r":
                    say(speaker, reader.repeat(), wait=True)
        except (EOFError, KeyboardInterrupt):
            pass
        finally:
            speaker.close()
        return

    cap = cv2.VideoCapture(args.device)
    if not cap.isOpened():
        sys.exit(f"Khong mo duoc camera {args.device}")

    print("Huong camera vao van ban. Giu yen vai giay de he thong on dinh.")
    print("Phim: n tiep, p lui, r doc lai, a lam moi, q thoat.\n")

    frame_i = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_i += 1

            # OCR rat cham - chi chay moi vai khung hinh
            if frame_i % args.every == 0:
                results = engine.readtext(frame)
                res = reader.observe(results, frame.shape[1])
                say(speaker, res)
                if res.state is ReadState.SETTLING:
                    print("  (dang on dinh...)", end="\r")

            if args.show:
                cv2.putText(frame, f"{reader.state.value}  "
                                   f"doan {reader.index + 1}/{max(1, reader.total())}",
                            (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0, 255, 0), 2)
                cv2.imshow("reader (debug)", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key in (ord("n"), ord(" ")):
                say(speaker, reader.next_chunk(), wait=True)
            elif key == ord("p"):
                say(speaker, reader.prev_chunk(), wait=True)
            elif key == ord("r"):
                say(speaker, reader.repeat(), wait=True)
            elif key == ord("a"):
                reader.reset()
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        speaker.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true",
                    help="chay thu khong can camera lan easyocr")
    ap.add_argument("--image", help="doc tu mot file anh thay vi webcam")
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--speak", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--stable", type=int, default=3,
                    help="so khung hinh on dinh truoc khi doc")
    ap.add_argument("--chars", type=int, default=180,
                    help="do dai toi da moi doan")
    ap.add_argument("--every", type=int, default=8,
                    help="chay OCR moi bao nhieu khung hinh")
    args = ap.parse_args()

    if args.demo:
        run_demo(args)
    else:
        run_camera(args)


if __name__ == "__main__":
    main()
