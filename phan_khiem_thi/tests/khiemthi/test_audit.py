"""
Kiem thu KICH BAN F - khao sat do tiep can cua toa nha.

Cong cu nay sinh ra CON SO de tra loi cau hoi "ai bo tien, bao nhieu".
Neu no bao 100% do phu tren mot toa nha thuc su co diem mu thi no dang
tao cam giac an tam gia - nguy hiem hon la khong co gi.

Nen phan lon test o day dung ban do CO TINH THUA MOC NEO, va doi hoi
cong cu phai tim ra dung cho thieu.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wayfinding.khiemthi.audit import (
    COST_PER_MARKER_VND, anchor_nodes, audit_floor, coverage_ratio,
    distance_from_anchors, find_gaps, sample_coverage, suggest_markers,
)
from wayfinding.loi_chung.floormap import load_map
from wayfinding.loi_chung.localizer import Confidence

MAP = ROOT / "config" / "map_floor3.json"


def hanh_lang_dai(n_nodes=9, spacing=12.0, markers=("0",)) -> dict:
    """
    Mot hanh lang thang dai, chi co moc neo o mot dau.

    Dau kia se la diem mu - do la thu cong cu phai tim ra.
    """
    nodes = [{"id": f"N{i}", "x": i * spacing, "y": 0.0,
              "name": f"Diem {i}", "landmark": "Cot vuong so duoc"}
             for i in range(n_nodes)]
    edges = [{"from": f"N{i}", "to": f"N{i+1}"} for i in range(n_nodes - 1)]
    mk = {}
    for m in markers:
        idx = int(m)
        mk[f"1{m}"] = {"x": idx * spacing, "y": 0.9, "theta": -90}
    return {"markers": mk, "rooms": {}, "nodes": nodes, "edges": edges}


def load(tmp_path, data):
    p = tmp_path / "m.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return load_map(p)


# ------------------------- khoang cach tren do thi -------------------------

def test_khoang_cach_tinh_theo_duong_di_khong_phai_duong_chim_bay():
    """
    Sai so tich luy theo QUANG DUONG DI. Mot phong cach moc 3m duong
    chim bay nhung phai di vong 40m thi van la diem mu.
    """
    fm = load_map(MAP)
    dist = distance_from_anchors(fm, {"A"})
    assert dist["A"] == pytest.approx(0.0)
    assert dist["R16"] > 30.0            # phai di vong ca hanh lang


def test_nut_co_moc_neo_thi_khoang_cach_bang_khong():
    fm = load_map(MAP)
    sources = anchor_nodes(fm)
    dist = distance_from_anchors(fm, sources)
    for s in sources:
        assert dist[s] == pytest.approx(0.0)


def test_moc_neo_duoc_gan_vao_nut_gan_nhat():
    """Moc neo nam tren TUONG, lech khoi tim hanh lang - phai gan dung nut."""
    fm = load_map(MAP)
    assert "A" in anchor_nodes(fm)


# ------------------------- do phu -------------------------

def test_ban_do_that_co_do_phu_cao():
    fm = load_map(MAP)
    assert audit_floor(fm).coverage > 0.9


def test_hanh_lang_dai_thieu_moc_thi_do_phu_thap(tmp_path):
    """Day la phep kiem tra quan trong nhat: phai TIM RA duoc diem mu."""
    fm = load(tmp_path, hanh_lang_dai())
    report = audit_floor(fm, max_markers=0)
    assert report.coverage < 0.5


def test_them_moc_thi_do_phu_tang(tmp_path):
    it_moc = load(tmp_path, hanh_lang_dai(markers=("0",)))
    nhieu_moc = load(tmp_path, hanh_lang_dai(markers=("0", "4", "8")))
    assert audit_floor(nhieu_moc, max_markers=0).coverage > \
           audit_floor(it_moc, max_markers=0).coverage


def test_do_phu_dem_dung_ty_le():
    from wayfinding.khiemthi.audit import SamplePoint

    pts = [SamplePoint("a", "b", 0.0, 0, 0, 0, Confidence.HIGH),
           SamplePoint("a", "b", 0.5, 0, 0, 0, Confidence.HIGH),
           SamplePoint("a", "b", 1.0, 0, 0, 0, Confidence.LOW)]
    assert coverage_ratio(pts) == pytest.approx(2 / 3)


def test_khong_co_diem_ray_thi_do_phu_bang_khong():
    assert coverage_ratio([]) == 0.0


def test_do_phu_dung_dung_mo_hinh_do_tin_cay(tmp_path):
    """
    Mo hinh do tin cay phai GIONG HET localizer.py. Lech hai noi thi bao
    cao noi mot dang ma he thong chay mot dang.
    """
    fm = load(tmp_path, hanh_lang_dai(n_nodes=6, spacing=10.0))
    samples = sample_coverage(fm, {"N0"}, drift_rate=0.025)
    for s in samples:
        drift = 0.025 * s.dist_to_anchor
        expect = (Confidence.HIGH if drift < 1.0
                  else Confidence.MEDIUM if drift < 3.0 else Confidence.LOW)
        assert s.confidence is expect


# ------------------------- doan mat do tin cay -------------------------

def test_tim_ra_doan_mat_do_tin_cay(tmp_path):
    fm = load(tmp_path, hanh_lang_dai())
    report = audit_floor(fm, max_markers=0)
    assert report.gaps


def test_doan_te_nhat_duoc_xep_len_dau(tmp_path):
    fm = load(tmp_path, hanh_lang_dai())
    gaps = audit_floor(fm, max_markers=0).gaps
    assert gaps[0].worst_distance >= gaps[-1].worst_distance


def test_doan_mat_do_tin_cay_mo_ta_duoc(tmp_path):
    fm = load(tmp_path, hanh_lang_dai())
    report = audit_floor(fm, max_markers=0)
    text = report.gaps[0].describe(fm)
    assert "Diem" in text and "m" in text


def test_ban_do_du_moc_thi_khong_co_doan_nao(tmp_path):
    fm = load(tmp_path, hanh_lang_dai(n_nodes=4, spacing=6.0,
                                      markers=("0", "1", "2", "3")))
    assert find_gaps(fm, sample_coverage(fm, anchor_nodes(fm))) == []


# ------------------------- de xuat dan ma -------------------------

def test_de_xuat_dan_ma_khi_thieu(tmp_path):
    fm = load(tmp_path, hanh_lang_dai())
    suggestions, _ = suggest_markers(fm, target=0.95, max_markers=10)
    assert suggestions


def test_moi_ma_de_xuat_deu_cai_thien_do_phu(tmp_path):
    """Tham lam nhung khong duoc de xuat ma vo ich."""
    fm = load(tmp_path, hanh_lang_dai())
    suggestions, _ = suggest_markers(fm, target=0.95, max_markers=10)
    for s in suggestions:
        assert s.gain > 0


def test_do_phu_tang_dan_qua_tung_de_xuat(tmp_path):
    fm = load(tmp_path, hanh_lang_dai())
    suggestions, _ = suggest_markers(fm, target=0.95, max_markers=10)
    covs = [s.coverage_after for s in suggestions]
    assert covs == sorted(covs)


def test_dat_muc_tieu_thi_dung_de_xuat(tmp_path):
    fm = load(tmp_path, hanh_lang_dai())
    it, _ = suggest_markers(fm, target=0.5, max_markers=10)
    nhieu, _ = suggest_markers(fm, target=0.98, max_markers=10)
    assert len(it) < len(nhieu)


def test_ton_trong_gioi_han_so_ma(tmp_path):
    fm = load(tmp_path, hanh_lang_dai(n_nodes=20, spacing=15.0))
    suggestions, _ = suggest_markers(fm, target=0.99, max_markers=3)
    assert len(suggestions) <= 3


def test_ban_do_da_du_thi_khong_de_xuat_gi():
    fm = load_map(MAP)
    suggestions, _ = suggest_markers(fm, target=0.9)
    assert suggestions == []


# ------------------------- chi phi -------------------------

def test_chi_phi_tinh_theo_so_ma(tmp_path):
    fm = load(tmp_path, hanh_lang_dai())
    report = audit_floor(fm, max_markers=5)
    assert report.cost_vnd == len(report.suggestions) * COST_PER_MARKER_VND


def test_chi_phi_bang_khong_khi_khong_can_dan_them():
    report = audit_floor(load_map(MAP), target=0.9)
    assert report.cost_vnd == 0


def test_gio_cong_tinh_theo_so_ma(tmp_path):
    fm = load(tmp_path, hanh_lang_dai())
    report = audit_floor(fm, max_markers=5)
    assert report.minutes > 0
    assert report.minutes == len(report.suggestions) * 5


def test_chi_phi_van_rat_re(tmp_path):
    """
    Luan diem chinh khi pitch: lam ca mot tang tiep can duoc chi ton
    vai chuc nghin. Neu con so nay bi tinh sai thi lap luan sup.
    """
    fm = load(tmp_path, hanh_lang_dai(n_nodes=20, spacing=15.0))
    report = audit_floor(fm, max_markers=10)
    assert report.cost_vnd < 200_000


# ------------------------- thieu bien va canh bao -------------------------

def test_phat_hien_nguy_hiem_chua_canh_bao(tmp_path):
    data = hanh_lang_dai(n_nodes=3, spacing=5.0)
    data["nodes"][1]["name"] = "Chan cau thang bo"
    fm = load(tmp_path, data)
    assert audit_floor(fm, max_markers=0).hazards_without_warning


def test_khong_bao_khi_da_co_canh_bao(tmp_path):
    data = hanh_lang_dai(n_nodes=3, spacing=5.0)
    data["nodes"][1]["name"] = "Chan cau thang bo"
    for e in data["edges"]:
        e["hazard"] = "Cau thang xuong ben trai"
    fm = load(tmp_path, data)
    assert audit_floor(fm, max_markers=0).hazards_without_warning == []


def test_phat_hien_phong_thieu_bien(tmp_path):
    data = hanh_lang_dai(n_nodes=3, spacing=5.0)
    data["nodes"][2]["name"] = "Phong 3.20"
    fm = load(tmp_path, data)
    assert audit_floor(fm, max_markers=0).rooms_without_signs


def test_khong_bao_khi_phong_da_co_bien(tmp_path):
    data = hanh_lang_dai(n_nodes=3, spacing=5.0)
    data["nodes"][2]["name"] = "Phong 3.20"
    data["rooms"] = {"3.20": {"x": 10.0, "y": 0.9, "theta": -90}}
    fm = load(tmp_path, data)
    assert audit_floor(fm, max_markers=0).rooms_without_signs == []
