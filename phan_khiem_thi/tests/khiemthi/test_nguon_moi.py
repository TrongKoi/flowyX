"""
Kiem thu hai nguon moc moi duoc noi vao Localizer: L1 braille va L4
khop ban nen.

Nguyen tac 1.3 noi moi nguon vi tri phai di qua DUNG MOT CONG. Cac test
duoi kiem dung dieu do: khong nguon nao ghi thang vao pose, tat ca nop
AnchorSighting va chiu kiem tra cua Localizer.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.loi_chung.anchors import AnchorSighting
from wayfinding.loi_chung.floormap import load_map
from wayfinding.loi_chung.geometry import Pose2D
from wayfinding.loi_chung.localizer import Localizer

MAP = Path(__file__).resolve().parents[2] / "config" / "map_floor3.json"


@pytest.fixture
def loc() -> Localizer:
    return Localizer(load_map(MAP))


def _moc(source: str, key: str, x: float, y: float,
         theta: float = 0.0) -> AnchorSighting:
    return AnchorSighting(key=key, source=source,
                          world_pose=Pose2D(x, y, theta),
                          cam_from_anchor=Pose2D(0.0, 0.0, 0.0),
                          distance=0.0, quality=1.0)


# ------------------------------------------------------------------
# L4 - khop ban nen
# ------------------------------------------------------------------

def test_nguon_backdrop_dat_duoc_vi_tri(loc: Localizer):
    sp = Pose2D(1.0, 1.0, 0.0)
    assert loc.apply_anchor(_moc("backdrop", "7,0,6", 7.5, 0.5), sp)
    fix = loc.update(sp)
    assert fix is not None
    assert fix.pose.x == pytest.approx(7.5)
    assert fix.pose.y == pytest.approx(0.5)


def test_backdrop_khong_co_world_pose_thi_bi_tu_choi(loc: Localizer):
    """
    O luoi ban nen khong phai muc trong ban do, nen khong tra cuu duoc.
    Thieu toa do thi phai tu choi, khong duoc doan.
    """
    s = AnchorSighting(key="7,0,6", source="backdrop",
                       cam_from_anchor=Pose2D(0.0, 0.0, 0.0),
                       distance=0.0, quality=0.5)
    assert not loc.apply_anchor(s, Pose2D(1.0, 1.0, 0.0))


def test_backdrop_van_chiu_kiem_tra_buoc_nhay(loc: Localizer):
    """
    L4 KHONG duoc vuot nguong nhay - chi L1 braille moi duoc. Ban nen
    quet mot lan roi lech dan theo thoi gian, nen no khong du tin cay
    de ghi de len vi tri dang co.
    """
    sp = Pose2D(0.0, 0.0, 0.0)
    assert loc.apply_anchor(_moc("backdrop", "a", 5.0, 0.0), sp)
    loc.update(sp)
    # Nhay 40m trong khi chua di met nao -> phai bi tu choi
    assert not loc.apply_anchor(_moc("backdrop", "b", 45.0, 0.0), sp)


# ------------------------------------------------------------------
# L1 - braille
# ------------------------------------------------------------------

def test_braille_duoc_vuot_nguong_nhay(loc: Localizer):
    """
    Nguon dang tin nhat trong he. An toan duoc vi no DA qua hai lop
    phong thu trong braille.py truoc khi toi day.
    """
    sp = Pose2D(0.0, 0.0, 0.0)
    assert loc.apply_anchor(_moc("braille", "3.12", 5.0, 0.0), sp)
    loc.update(sp)
    # Cung buoc nhay 40m ma L4 bi tu choi -> L1 phai duoc chap nhan
    assert loc.apply_anchor(_moc("braille", "3.14", 45.0, 0.0), sp)


def test_braille_giu_nguyen_huong(loc: Localizer):
    """
    Nguoi dung dung canh cua nhung quay mat huong nao thi khong biet.
    Bat huong theo `theta` cua tam bien se lam lech ca he.
    """
    sp = Pose2D(0.0, 0.0, 30.0)
    loc.apply_anchor(_moc("braille", "3.12", 5.0, 0.0, theta=30.0), sp)
    fix = loc.update(sp)
    assert fix.pose.theta == pytest.approx(30.0, abs=0.5)


def test_braille_khong_co_world_pose_thi_tra_cuu_ban_do(loc: Localizer):
    """Van tuong thich: khong dua toa do thi tra cuu bang so phong."""
    s = AnchorSighting(key="3.12", source="braille",
                       cam_from_anchor=Pose2D(0.0, 0.0, 0.0),
                       distance=0.0, quality=1.0)
    assert loc.apply_anchor(s, Pose2D(0.0, 0.0, 0.0))


def test_so_phong_la_thi_tu_choi(loc: Localizer):
    s = AnchorSighting(key="999", source="braille",
                       cam_from_anchor=Pose2D(0.0, 0.0, 0.0),
                       distance=0.0, quality=1.0)
    assert not loc.apply_anchor(s, Pose2D(0.0, 0.0, 0.0))


# ------------------------------------------------------------------
# L5 - sua rieng huong
# ------------------------------------------------------------------

def test_apply_heading_chi_doi_huong(loc: Localizer):
    sp = Pose2D(5.0, 3.0, 10.0)
    loc.apply_anchor(_moc("backdrop", "a", 5.0, 3.0, theta=10.0), sp)
    truoc = loc.update(sp)

    assert loc.apply_heading(40.0, sp)
    sau = loc.update(sp)

    assert sau.pose.theta == pytest.approx(40.0, abs=0.5)
    assert sau.pose.x == pytest.approx(truoc.pose.x)
    assert sau.pose.y == pytest.approx(truoc.pose.y)


def test_apply_heading_truoc_khi_dinh_vi_thi_khong_lam_gi(loc: Localizer):
    """Chua co he quy chieu thi khong co gi de xoay."""
    assert not loc.apply_heading(40.0, Pose2D(0.0, 0.0, 0.0))


def test_nguon_cu_khong_doi_hanh_vi(loc: Localizer):
    """
    Them truong world_pose va hai nguon moi KHONG duoc lam doi cach
    nguon cu hoat dong.
    """
    s = AnchorSighting(key="3.12", source="ocr",
                       cam_from_anchor=Pose2D(1.0, 0.0, 180.0),
                       distance=1.0, quality=0.9)
    assert s.world_pose is None
    assert loc.apply_anchor(s, Pose2D(0.0, 0.0, 0.0))
