#!/usr/bin/env python3
"""
KICH BAN D - dung thiet bi man hinh cam ung.

Huong camera vao ma dan tren may in / may pha ca phe / lo vi song, nghe
gioi thieu bang, roi hoi tung nut.

Y tuong cot loi: chinh tam ma la MOC SO DUOC. Vi tri cac nut co dinh so
voi ma, nen huong dan tro thanh "dat ngon tay len ma, roi truot sang
phai 4 phay 5 xentimet". Khong phu thuoc uoc luong tu the von nhieu
nhieu, va nguoi dung tu kiem chung duoc bang tay.

VAT TU: nho dan mot mieng xop tron duong kinh 1cm vao dung tam ma. Ma in
tren giay khong so thay duoc - thieu buoc nay thi ca kich ban vo nghia.

Chay:
    python3 run_panel.py --demo             # khong can camera
    python3 run_panel.py                    # webcam
    python3 run_panel.py --speak --show
"""

from __future__ import annotations

import argparse
import sys

from wayfinding.khiemthi.panel import PanelSession, load_panels
from wayfinding.loi_chung.speech import AsyncSpeech, ConsoleSpeech


def make_speaker(use_tts: bool):
    backend = ConsoleSpeech()
    if use_tts:
        try:
            from wayfinding.loi_chung.speech import Pyttsx3Speech
            backend = Pyttsx3Speech(rate=210)
        except Exception as e:                        # noqa: BLE001
            print(f"(khong dung duoc TTS: {e} - in ra man hinh)")
    return AsyncSpeech(backend)


def interactive(session: PanelSession, speaker) -> None:
    """Vong hoi dap: go ten nut de duoc huong dan."""
    print("\nGo ten nut de duoc huong dan. "
          "'l' doc lai bang, 'q' thoat.\n")
    try:
        while True:
            raw = input("> ").strip()
            if raw.lower() in ("q", "quit", "thoat"):
                break
            # Cau tra loi KHONG duoc bo: nguoi dung vua hoi thi phai nghe
            # duoc. Khac han chi dan dieu huong, vi chi dan cu het gia tri
            # con cau tra loi thi khong.
            if raw.lower() in ("l", "list"):
                speaker.speak_and_wait(session.repeat_layout())
                continue
            if raw:
                speaker.speak_and_wait(session.ask(raw))
    except (EOFError, KeyboardInterrupt):
        pass


def run_demo(args) -> None:
    speaker = make_speaker(args.speak)
    session = PanelSession(panels=load_panels(args.panels))

    print("Che do demo: gia lap camera doc duoc ma.")
    print(f"Cac thiet bi da khai bao: "
          f"{', '.join(p.appliance for p in session.panels.values())}\n")

    marker = args.marker or next(iter(session.panels))
    intro = session.on_marker(marker)
    if intro is None:
        sys.exit(f"Ma '{marker}' khong thuoc thiet bi nao trong {args.panels}")
    speaker.speak_and_wait(intro)

    try:
        interactive(session, speaker)
    finally:
        speaker.close()


def run_camera(args) -> None:
    """
    Che do camera da GO BO cung voi lop ArUco.

    Kich ban nay tung dua vao mot ma dan TREN TUNG THIET BI de biet dang
    dung may vi song hay may in nao. Ma dan len thiet bi cu the la de
    nghi hop ly hon nhieu so voi dan khap toa nha - nhung lop nhan dien
    ArUco da bi go khoi ma nguon, nen che do nay khong con chan de.

    Che do --demo van chay day du: no nhan ma so thiet bi truc tiep, va
    do la phan co gia tri that cua kich ban (doc bang dieu khien thanh
    tieng), khong phai phan nhan dien.
    """
    sys.exit(
        "Che do camera da go cung voi lop ArUco.\n"
        "Dung: python3 run_panel.py --demo --marker <ma-thiet-bi>"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panels", default="config/panels.json")
    ap.add_argument("--marker", help="ma so thiet bi, dung voi --demo")
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--speak", action="store_true")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    if args.demo:
        run_demo(args)
    else:
        run_camera(args)


if __name__ == "__main__":
    main()
