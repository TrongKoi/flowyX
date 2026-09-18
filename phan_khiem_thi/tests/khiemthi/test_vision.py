"""
Kiem thu lop THI GIAC - doc bien so phong bang OCR.

Cac test cua lop ma ArUco da bi go cung voi chinh lop do: khong con dan
ma len tuong nen lop nhan dien ma khong con duong chay nao. Giu lai test
cho code da xoa chi lam bo test phinh ra ma khong bao ve gi.

Lich su day du xem docs/THAYDOI_2026-09-12.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.loi_chung.anchors import RoomSignReader

W, H = 1280, 720

# ------------------------------------------------------------------
# Lop OCR - dung reader gia de khong phai cai easyocr khi chay test
# ------------------------------------------------------------------

class FakeOCR:
    def __init__(self, results):
        self._results = results

    def readtext(self, frame):
        return self._results


def test_ocr_accepts_known_room():
    box = [[100, 100], [300, 100], [300, 160], [100, 160]]
    reader = RoomSignReader(
        known_rooms={"3.12"},
        every_n_frames=1,
        reader=FakeOCR([(box, "3.12", 0.95)]),
    )
    found = reader.detect(np.zeros((H, W, 3), np.uint8))
    assert len(found) == 1
    assert found[0].key == "3.12" and found[0].source == "ocr"


def test_ocr_rejects_unknown_room():
    """So phong khong co trong ban do phai bi bo, khong duoc lam sap."""
    box = [[100, 100], [300, 100], [300, 160], [100, 160]]
    reader = RoomSignReader(
        known_rooms={"3.12"},
        every_n_frames=1,
        reader=FakeOCR([(box, "9.99", 0.95)]),
    )
    assert reader.detect(np.zeros((H, W, 3), np.uint8)) == []


def test_ocr_rejects_low_confidence():
    box = [[100, 100], [300, 100], [300, 160], [100, 160]]
    reader = RoomSignReader(
        known_rooms={"3.12"},
        min_conf=0.75,
        every_n_frames=1,
        reader=FakeOCR([(box, "3.12", 0.40)]),
    )
    assert reader.detect(np.zeros((H, W, 3), np.uint8)) == []


def test_ocr_throttles_to_every_n_frames():
    """OCR cham nen phai bo bot khung hinh, neu khong tut fps."""
    box = [[100, 100], [300, 100], [300, 160], [100, 160]]
    reader = RoomSignReader(
        known_rooms={"3.12"},
        every_n_frames=5,
        reader=FakeOCR([(box, "3.12", 0.95)]),
    )
    frame = np.zeros((H, W, 3), np.uint8)
    hits = sum(1 for _ in range(20) if reader.detect(frame))
    assert hits == 4          # 20 khung hinh / moi 5 khung
