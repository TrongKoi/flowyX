"""
Dau ra giong noi va rung.

Ba luu y ma doi thuong bo sot (Muc 14):
  - Toc do doc: nguoi dung screen reader quen toc do NHANH hon nhieu so
    voi nguoi sang mat tuong. Mac dinh nen nhanh hon muc ban thay
    thoai mai, va phai cho chinh duoc.
  - Cat loi: khi co chi dan quan trong hon, phai cat cau dang doc do.
    Dung xep hang doi doc het.
  - Khong lap: cung mot cau khong duoc doc lai trong vai giay, neu
    khong he thong tro nen kho chiu va nguoi dung se tat di.
"""

from __future__ import annotations

import queue
import threading
import time
from typing import Protocol

# Tu vung rung - Muc 14 cua tai lieu.
# Dien thoai chi co MOT motor rung, nen dung SO NHIP thay cho vi tri.
HAPTIC_PATTERNS: dict[str, list[int]] = {
    "one_pulse": [120],                        # 1 nhip = re trai
    "two_pulse": [120, 80, 120],               # 2 nhip = re phai
    "three_pulse": [100, 60, 100, 60, 100],    # 3 nhip = da toi dich
    "long_buzz": [600],                        # rung dai = di lac
    "double_repeat": [200, 100, 200],          # canh bao nguy hiem
    # Xong mot chang. NHE va NGAN co y: day la loi khen, khong phai
    # canh bao. Rung manh bang canh bao nguy hiem se lam nguoi dung
    # giat minh va hoc sai y nghia cua ma rung.
    "xong_buoc": [40, 60, 40],
}


class SpeechBackend(Protocol):
    def speak(self, text: str) -> None: ...
    def stop(self) -> None: ...


class ConsoleSpeech:
    """Backend in ra man hinh - dung de phat trien va kiem thu."""

    def speak(self, text: str) -> None:
        print(f"[NOI] {text}")

    def stop(self) -> None:
        pass


class Pyttsx3Speech:
    """Backend doc thanh tieng that. Nap muon vi pyttsx3 co the chua cai."""

    def __init__(self, rate: int = 210):
        import pyttsx3

        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)

    def speak(self, text: str) -> None:
        self._engine.say(text)
        self._engine.runAndWait()

    def stop(self) -> None:
        self._engine.stop()


class AsyncSpeech:
    """
    Boc mot backend dong bo, chay no tren luong nen.

    Ly do ton tai (issue #9): Pyttsx3Speech.speak() goi runAndWait(),
    ham nay KHOA luong den khi doc xong ca cau - vai giay. Dat trong
    vong lap xu ly camera cua run_live.py thi toan bo pipeline dung lai
    dung luc nguoi dung dang di. Di bo 1.4 m/s, mot cau 3 giay la 4 met
    khong co dinh vi.

    Hang doi CO Y giu rat ngan (mac dinh 1). Chi dan dieu huong cu
    khong con dang doc nua - co cau moi thi bo cau cu, dung xep hang.

    Cat loi dung so hieu the he (epoch) thay vi mot co bao don gian:
    stop() tang epoch, cac cau da nam trong hang doi truoc do bi bo,
    con cau nop SAU khi stop() van duoc doc binh thuong.
    """

    def __init__(self, backend: SpeechBackend, queue_size: int = 1):
        self._backend = backend
        self._q: queue.Queue = queue.Queue(maxsize=max(1, queue_size))
        self._lock = threading.Lock()
        self._epoch = 0
        self._closed = False
        self._thread = threading.Thread(
            target=self._worker, name="speech", daemon=True
        )
        self._thread.start()

    # ---------- luong nen ----------

    def _worker(self) -> None:
        while True:
            item = self._q.get()
            if item is None:
                break
            epoch, text, done = item
            try:
                with self._lock:
                    if epoch < self._epoch:
                        continue      # da bi stop() huy truoc khi kip doc
                try:
                    self._backend.speak(text)
                except Exception:
                    # Loi TTS tuyet doi khong duoc lam sap he thong dieu huong.
                    pass
            finally:
                if done is not None:
                    done.set()

    # ---------- giao dien SpeechBackend ----------

    def speak(self, text: str) -> None:
        """Khong bao gio chan luong goi. Hang doi day thi bo cau CU."""
        if self._closed:
            return
        with self._lock:
            item = (self._epoch, text, None)
        while True:
            try:
                self._q.put_nowait(item)
                return
            except queue.Full:
                try:
                    dropped = self._q.get_nowait()   # bo cau cu nhat
                    if dropped is not None and dropped[2] is not None:
                        dropped[2].set()             # dung de ai do cho mai
                except queue.Empty:
                    return

    def speak_and_wait(self, text: str, timeout: float = 30.0) -> bool:
        """
        Doc va CHO doc xong. Cau nay khong bao gio bi bo.

        Dung cho hoi dap (kich ban C va D): nguoi dung hoi mot cau va
        PHAI nghe duoc cau tra loi. Bo cau tra loi di la sai han - khac
        han chi dan dieu huong, vi chi dan cu khong con gia tri con cau
        tra loi thi co.

        Van chay tren luong nen, nen khong bao gio co hai luong cung goi
        vao TTS mot luc.
        """
        if self._closed:
            return False
        done = threading.Event()
        with self._lock:
            item = (self._epoch, text, done)
        self._q.put(item)                    # CHO cho tới khi co cho
        return done.wait(timeout=timeout)

    def stop(self) -> None:
        """Cat cau dang doc va huy nhung cau dang cho."""
        with self._lock:
            self._epoch += 1
        while True:
            try:
                pending = self._q.get_nowait()
                if pending is not None and pending[2] is not None:
                    pending[2].set()         # dung de ai do cho mai
            except queue.Empty:
                break
        try:
            self._backend.stop()
        except Exception:
            pass

    def close(self, timeout: float = 2.0) -> None:
        """Dong luong nen. Goi khi thoat chuong trinh."""
        if self._closed:
            return
        self._closed = True
        try:
            self._q.put_nowait(None)
        except queue.Full:
            try:
                dropped = self._q.get_nowait()
                if dropped is not None and dropped[2] is not None:
                    dropped[2].set()
                self._q.put_nowait(None)
            except (queue.Empty, queue.Full):
                pass
        self._thread.join(timeout=timeout)


class Announcer:
    """
    Quan ly viec phat chi dan: chong lap, cat loi, va gui ma rung.
    """

    def __init__(
        self,
        backend: SpeechBackend | None = None,
        min_gap: float = 4.0,
        haptic_sink=None,
    ):
        self.backend = backend or ConsoleSpeech()
        self.min_gap = min_gap
        self.haptic_sink = haptic_sink or self._print_haptic
        self._last_text: str | None = None
        self._last_time = 0.0

    def _print_haptic(self, pattern: str) -> None:
        ms = HAPTIC_PATTERNS.get(pattern)
        if ms:
            print(f"[RUNG] {pattern} {ms}")

    def announce(self, instruction, now: float | None = None) -> bool:
        """
        Phat mot chi dan. Tra ve True neu that su da phat.

        Tra ve False khi bi chan vi trung lap - de goi tang tren biet.
        """
        if instruction is None:
            return False

        t = time.time() if now is None else now
        same = instruction.text == self._last_text
        # Chi dan khan cap duoc cat loi, nhung VAN phai chong lap - chi
        # voi khoang cach ngan hon. Neu khong, canh bao khan se lap vo han
        # va nguoi dung se tat he thong di.
        gap = self.min_gap * 0.4 if instruction.urgent else self.min_gap

        if same and (t - self._last_time) < gap:
            return False

        if instruction.urgent:
            self.backend.stop()

        self._last_text = instruction.text
        self._last_time = t

        self.backend.speak(instruction.text)
        if instruction.haptic:
            self.haptic_sink(instruction.haptic)
        return True

    def reset(self) -> None:
        self._last_text = None
        self._last_time = 0.0
