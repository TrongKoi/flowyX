"""
Kiem thu lop boc giong noi chay tren luong nen.

No sinh ra tu mot loi: viec CHAM chay dong bo trong vong lap thoi gian
thuc. Xem issue #9.

Truoc day file nay con kiem `AsyncRoomSignReader` (doc bien chu bang
OCR). Lop do da di theo phan dieu huong.

Test o day chu yeu do THOI GIAN, nen nguong duoc dat rat rong de khong
vo tren may cham hoac khi may dang ban.
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.loi_chung.speech import AsyncSpeech, ConsoleSpeech

W, H = 640, 480
BOX = [[100, 100], [300, 100], [300, 160], [100, 160]]


# ------------------------------------------------------------------
# AsyncSpeech - issue #9
# ------------------------------------------------------------------

class SlowSpeech:
    """Backend gia lap TTS that: moi cau mat 0.3 giay."""

    def __init__(self, delay: float = 0.3):
        self.delay = delay
        self.spoken: list[str] = []
        self.stops = 0

    def speak(self, text: str) -> None:
        time.sleep(self.delay)
        self.spoken.append(text)

    def stop(self) -> None:
        self.stops += 1


class BrokenSpeech:
    def speak(self, text: str) -> None:
        raise RuntimeError("TTS hong")

    def stop(self) -> None:
        raise RuntimeError("stop hong")


def test_speak_khong_chan_luong_goi():
    """Loi chinh cua issue #9: runAndWait() khoa vong lap camera."""
    slow = SlowSpeech(delay=0.5)
    a = AsyncSpeech(slow)
    try:
        t0 = time.time()
        a.speak("cau dai")
        elapsed = time.time() - t0
        assert elapsed < 0.1, f"speak() chan luong {elapsed:.2f}s"
    finally:
        a.close()


def test_hang_doi_giu_cau_moi_bo_cau_cu():
    """Chi dan dieu huong cu khong con dang doc - phai bo, khong xep hang."""
    slow = SlowSpeech(delay=0.3)
    a = AsyncSpeech(slow, queue_size=1)
    try:
        a.speak("cau 1")          # luong nen nhan ngay
        time.sleep(0.05)
        a.speak("cau 2")          # vao hang doi
        a.speak("cau 3")          # day cau 2 ra
        time.sleep(1.0)
        assert "cau 1" in slow.spoken
        assert "cau 3" in slow.spoken
        assert "cau 2" not in slow.spoken
    finally:
        a.close()


def test_stop_huy_cau_cho_nhung_khong_huy_cau_nop_sau():
    """
    Day la ly do dung so hieu the he thay vi mot co bao don gian.

    Voi co bao, stop() se lam RO cau ke tiep bi bo oan - dung loi de
    mat mot canh bao nguy hiem.
    """
    slow = SlowSpeech(delay=0.3)
    a = AsyncSpeech(slow, queue_size=2)
    try:
        a.speak("cau 1")
        time.sleep(0.05)
        a.speak("se bi huy")
        a.stop()
        a.speak("phai duoc doc")
        time.sleep(1.2)
        assert "se bi huy" not in slow.spoken
        assert "phai duoc doc" in slow.spoken
        assert slow.stops >= 1
    finally:
        a.close()


def test_loi_tts_khong_lam_sap_app():
    a = AsyncSpeech(BrokenSpeech())
    try:
        a.speak("bat ky")
        a.stop()
        time.sleep(0.2)
        a.speak("van song")
        time.sleep(0.2)
    finally:
        a.close()


def test_speak_sau_khi_close_khong_no():
    a = AsyncSpeech(ConsoleSpeech())
    a.close()
    a.speak("sau khi dong")      # khong duoc nem loi
