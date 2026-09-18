"""
Kiem thu lop phat hien chuong ngai bang do sau, va ban nen.

Trong tam cua file nay la HAI dieu de sai nhat:

1. Vung do sau khong dang tin phai la "khong biet", TUYET DOI khong
   duoc coi la "trong". Do sau dung tu chuyen dong yeu o dung nhung cho
   van phong hay co - tuong trang tron, nguoc sang, san bong - va coi
   nham mot mang tuong thanh loi di trong la dung kieu loi ca he thong
   dang phong.

2. Ban nen phai lay do sau LON NHAT tung thay, khong phai trung binh.
   Vat tam thoi chi lam do sau ngan lai, nen lay gia tri lon nhat thi
   tu dong loai bo nhung thu di ngang qua trong luc quet.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.khiemthi.backdrop import Backdrop, Place
from wayfinding.loi_chung.depth import (CLEAR_M, Cell, DepthGrid, Novelty, Zone,
                              bearing_of, classify_cell, describe, scan)
from wayfinding.loi_chung.geometry import Pose2D
from wayfinding.loi_chung.profile import floor_coverage, tilt_for_blind_zone

COLS, ROWS = 4, 3


def grid(depth, conf=0.9) -> DepthGrid:
    """Luoi 4x3; `depth` la danh sach 12 so hoac mot so dung chung."""
    if isinstance(depth, (int, float)):
        depth = [float(depth)] * (COLS * ROWS)
    if isinstance(conf, (int, float)):
        conf = [float(conf)] * (COLS * ROWS)
    return DepthGrid(cols=COLS, rows=ROWS,
                     depth=tuple(depth), confidence=tuple(conf))


# ------------------------------------------------------------------
# Luoi
# ------------------------------------------------------------------

def test_luoi_sai_so_o_bi_bao_loi():
    with pytest.raises(ValueError, match="can 12 gia tri"):
        DepthGrid(cols=4, rows=3, depth=(1.0,) * 5, confidence=(1.0,) * 5)


def test_chia_dai_theo_ty_le_khong_theo_so_hang():
    """Luoi 3 hang va luoi 6 hang deu phai chia dung ba dai."""
    g3 = grid(5.0)
    assert g3.zone_of(0) is Zone.CAO
    assert g3.zone_of(1) is Zone.XA
    assert g3.zone_of(2) is Zone.SAN

    g6 = DepthGrid(cols=2, rows=6, depth=(5.0,) * 12, confidence=(0.9,) * 12)
    assert g6.zone_of(0) is Zone.CAO
    assert g6.zone_of(5) is Zone.SAN


def test_doc_duoc_goi_tin_khong_co_do_tin_cay():
    g = DepthGrid.from_payload({"cols": 2, "rows": 1, "depth": [1.0, 2.0]})
    assert g.confidence == (1.0, 1.0)


def test_huong_cua_cot():
    assert bearing_of(0, 4) < 0          # cot ngoai cung trai
    assert bearing_of(3, 4) > 0          # cot ngoai cung phai
    assert bearing_of(0, 1) == 0.0       # mot cot thi la thang truoc


# ------------------------------------------------------------------
# Phan loai o - phan quan trong nhat ve an toan
# ------------------------------------------------------------------

def test_o_xa_la_trong():
    assert classify_cell(CLEAR_M + 1.0, 0.9) is Cell.TRONG


def test_o_gan_la_co_vat():
    assert classify_cell(1.2, 0.9) is Cell.CO_VAT


def test_do_tin_cay_thap_la_chua_biet_du_do_sau_bao_xa():
    """
    Day la ca kiem thu quan trong nhat trong file.

    Mot mang tuong trang tron co the cho do sau bao 10 met voi do tin
    cay 0,1. Coi do la "trong" nghia la day nguoi dung di thang vao
    tuong.
    """
    assert classify_cell(10.0, 0.1) is Cell.CHUA_BIET
    assert classify_cell(10.0, 0.9) is Cell.TRONG


def test_do_sau_vo_cuc_hoac_nan_la_chua_biet():
    assert classify_cell(math.inf, 0.9) is Cell.CHUA_BIET
    assert classify_cell(math.nan, 0.9) is Cell.CHUA_BIET


# ------------------------------------------------------------------
# Quet moi nguy
# ------------------------------------------------------------------

def test_hanh_lang_trong_khong_bao_gi():
    assert scan(grid(9.0)) == []


def test_vat_can_gan_tam_san_la_gap():
    d = [9.0] * 12
    d[11] = 1.1
    hz = scan(grid(d))
    assert len(hz) == 1
    assert hz[0].zone is Zone.SAN
    assert hz[0].urgent


def test_vat_xa_thi_bao_truoc_chu_khong_gap():
    d = [9.0] * 12
    d[11] = 2.5
    hz = scan(grid(d))
    assert len(hz) == 1 and not hz[0].urgent


def test_vat_ngoai_nguong_canh_bao_thi_bo_qua():
    d = [9.0] * 12
    d[11] = 3.5
    assert scan(grid(d)) == []


def test_moi_dai_chi_bao_mot_moi_nguy():
    """Bao het moi o thi thanh doc mot danh sach dai, khong dung duoc."""
    d = [9.0] * 12
    d[8] = d[9] = d[10] = 1.2
    hz = scan(grid(d))
    assert len(hz) == 1


def test_bao_thu_gan_nhat_trong_dai():
    d = [9.0] * 12
    d[8] = 2.0
    d[10] = 1.1
    hz = scan(grid(d))
    assert hz[0].distance == pytest.approx(1.1)


def test_moi_nguy_gap_duoc_xep_truoc():
    d = [9.0] * 12
    d[1] = 2.8        # dai CAO, xa
    d[11] = 1.0       # dai SAN, gan
    hz = scan(grid(d))
    assert hz[0].urgent and hz[0].zone is Zone.SAN


def test_huong_trai_phai_dung():
    d = [9.0] * 12
    d[8] = 1.0        # cot 0, hang duoi
    assert scan(grid(d))[0].side == "bên trái"
    d = [9.0] * 12
    d[11] = 1.0       # cot 3
    assert scan(grid(d))[0].side == "bên phải"


def test_khong_tin_cay_o_dai_san_thi_phai_bao():
    c = [0.9] * 12
    for i in (8, 9, 10, 11):
        c[i] = 0.1
    hz = scan(grid(10.0, c))
    assert len(hz) == 1
    assert hz[0].state is Cell.CHUA_BIET
    assert "gậy" in describe(hz[0])


def test_khong_tin_cay_o_dai_cao_thi_bo_qua():
    """Mot mang tran nha khong doc duoc do sau thi khong dang bao."""
    c = [0.9] * 12
    for i in (0, 1, 2, 3):
        c[i] = 0.1
    assert scan(grid(10.0, c)) == []


def test_cau_noi_tam_cao_khac_tam_san():
    """
    Dai CAO la KHOANG TRONG CUA GAY TRANG - phai noi ro tam cao de
    nguoi dung biet day khong phai thu ho quet duoc bang gay.
    """
    d = [9.0] * 12
    d[1] = 1.3
    cao = describe(scan(grid(d))[0])
    d = [9.0] * 12
    d[9] = 1.3
    san = describe(scan(grid(d))[0])
    assert "ngực" in cao
    assert "ngực" not in san


def test_cau_noi_dung_dau_phay_thap_phan():
    """Doc tieng Viet thi 1,3 met chu khong phai 1.3 met."""
    d = [9.0] * 12
    d[9] = 1.3
    assert "1,3" in describe(scan(grid(d))[0])


# ------------------------------------------------------------------
# Ban nen
# ------------------------------------------------------------------

POSE = Pose2D(2.0, 3.0, 90.0)


def _scanned(depth=3.0, times=3) -> Backdrop:
    bd = Backdrop()
    for _ in range(times):
        bd.observe(POSE, grid(depth))
    return bd


def test_chua_quet_thi_khong_doan_la_tam_thoi():
    """
    Khong co nen de so thi khong the ket luan. Doan bua o day nghia la
    bao dong gia lien tuc o moi cho chua quet.
    """
    bd = Backdrop()
    d = [9.0] * 12
    d[5] = 1.0
    assert bd.refine(POSE, grid(d))[5] is Novelty.KHONG_RO


def test_vat_khop_nen_la_co_dinh():
    bd = _scanned(3.0)
    assert bd.refine(POSE, grid(3.0))[0] is Novelty.CO_DINH


def test_vat_gan_hon_nen_la_tam_thoi():
    bd = _scanned(3.0)
    d = [3.0] * 12
    d[5] = 1.2
    assert bd.refine(POSE, grid(d))[5] is Novelty.TAM_THOI


def test_chenh_lech_nho_khong_bi_coi_la_vat_la():
    """Nhieu do sau vai chuc centimet la binh thuong."""
    bd = _scanned(3.0)
    d = [3.0] * 12
    d[5] = 2.8
    assert bd.refine(POSE, grid(d))[5] is Novelty.CO_DINH


def test_ban_nen_lay_gia_tri_LON_NHAT():
    """
    Diem thiet ke quan trong nhat cua ban nen.

    Trong luc quet, mot nguoi di ngang qua che mat buc tuong. Neu ban
    nen lay trung binh thi nguoi do bi ghi thanh mot buc tuong gia, va
    ve sau buc tuong that se bi bao la "vat tam thoi" mai mai.
    """
    bd = Backdrop()
    bd.observe(POSE, grid(3.0))      # thay tuong
    bd.observe(POSE, grid(1.0))      # co nguoi di ngang qua
    bd.observe(POSE, grid(3.0))      # nguoi di khoi
    assert bd.expected(POSE)[0] == pytest.approx(3.0)
    # Va buc tuong that van duoc goi dung la co dinh
    assert bd.refine(POSE, grid(3.0))[0] is Novelty.CO_DINH


def test_o_khong_tin_cay_khong_duoc_ghi_vao_nen():
    bd = Backdrop()
    bd.observe(POSE, grid(3.0))
    bd.observe(POSE, grid(9.0, conf=0.1))     # do sau xau, tin cay thap
    assert bd.expected(POSE)[0] == pytest.approx(3.0)


def test_quay_mat_huong_khac_la_o_khac():
    bd = _scanned(3.0)
    khac = Pose2D(2.0, 3.0, -90.0)
    assert bd.expected(khac) is None


def test_doi_kich_thuoc_luoi_bi_bao_loi():
    bd = _scanned(3.0)
    khac = DepthGrid(cols=2, rows=2, depth=(1.0,) * 4, confidence=(0.9,) * 4)
    with pytest.raises(ValueError, match="khong so sanh duoc"):
        bd.observe(POSE, khac)


# ------------------------------------------------------------------
# Dia diem danh dau - 'marker' moi thay ma dan tuong
# ------------------------------------------------------------------

def test_danh_dau_dia_diem():
    bd = Backdrop()
    p = bd.mark("Bàn của tôi", POSE, note="cạnh cửa sổ")
    assert p.name == "Bàn của tôi"
    assert bd.places == [p]


def test_dia_diem_phai_co_ten():
    with pytest.raises(ValueError, match="ten"):
        Backdrop().mark("   ", POSE)


def test_tim_dia_diem_gan_nhat():
    bd = Backdrop()
    bd.mark("Bàn A", Pose2D(0.0, 0.0, 0.0))
    bd.mark("Bàn B", Pose2D(10.0, 0.0, 0.0))
    assert bd.nearest_place(Pose2D(0.5, 0.0, 0.0)).name == "Bàn A"
    assert bd.nearest_place(Pose2D(5.0, 0.0, 0.0)) is None


def test_luu_va_nap_lai_giu_nguyen(tmp_path):
    bd = _scanned(3.0)
    bd.mark("Phòng họp", POSE, note="cửa mở vào trong")
    f = tmp_path / "nen.json"
    bd.save(f)

    lai = Backdrop.load(f)
    assert lai.scanned_cells == bd.scanned_cells
    assert lai.expected(POSE)[0] == pytest.approx(3.0)
    assert lai.places[0].name == "Phòng họp"
    assert lai.places[0].note == "cửa mở vào trong"
    # Va van phan loai dung sau khi nap lai
    d = [3.0] * 12
    d[5] = 1.2
    assert lai.refine(POSE, grid(d))[5] is Novelty.TAM_THOI


# ------------------------------------------------------------------
# Hinh hoc goc chuc - vung mu duoi chan
# ------------------------------------------------------------------

def test_chuc_nhieu_thi_vung_mu_hep_lai():
    assert floor_coverage(1.27, 30).blind_zone < floor_coverage(1.27, 20).blind_zone


def test_chuc_it_thi_nhin_qua_duong_chan_troi():
    """Nhin qua chan troi moi thay duoc vat ngang nguc va ngang dau."""
    assert floor_coverage(1.27, 20).sees_horizon
    assert not floor_coverage(1.27, 30).sees_horizon


def test_nguoi_cao_hon_co_vung_mu_rong_hon():
    assert floor_coverage(1.39, 20).blind_zone > floor_coverage(1.05, 20).blind_zone


def test_goc_chuc_qua_nho_thi_bao_loi():
    with pytest.raises(ValueError, match="khong cham san"):
        floor_coverage(1.27, -30)


def test_tilt_for_blind_zone_dao_nguoc_dung_floor_coverage():
    t = tilt_for_blind_zone(1.27, 0.8)
    assert floor_coverage(1.27, t).blind_zone == pytest.approx(0.8, abs=1e-6)


def test_chuc_20_do_cho_vung_mu_hon_mot_met():
    """
    Ghi lai con so THAT, vi tai lieu doi huong ghi nham.

    Tai lieu de xuat "chuc 20-25 do cho vung mu khoang nua met". Tinh
    lai bang chinh cong thuc cua tai lieu thi vung mu la 1,1-1,3m - sai
    khoang 2,5 lan. De vung mu that su bang 0,5m thi phai chuc toi 44
    do, va luc do mat han kha nang thay vat ngang dau.

    Ket luan 20-25 do van dung, nhung ly do khac: 1,1-1,3m xap xi tam
    quet cua gay trang, nen hai cong cu vua khop nhau chu khong chong
    len nhau hay bo trong khoang nao.
    """
    assert floor_coverage(1.27, 20).blind_zone == pytest.approx(1.32, abs=0.02)
    assert floor_coverage(1.27, 25).blind_zone == pytest.approx(1.10, abs=0.02)
    assert tilt_for_blind_zone(1.27, 0.5) == pytest.approx(44.5, abs=0.3)


# ------------------------------------------------------------------
# Hai truc doc lap - ly do tach Cell khoi Novelty
# ------------------------------------------------------------------
#
# Enum phang cu KHONG bieu dien duoc dong thoi hai cau tra loi. Cac
# test duoi khoa chat dieu do lai.


def test_mot_o_vua_CO_VAT_vua_CO_DINH():
    """
    Cot nha trong hanh lang da quet: vua "co vat" (do sau gan) vua
    "co dinh" (khop ban nen). Enum phang cu buoc phai chon mot trong
    hai va lam mat cau tra loi kia.
    """
    bd = _scanned(2.0)
    g = grid(2.0)
    assert classify_cell(*g.at(0, 0)) is Cell.CO_VAT       # truc do sau
    assert bd.refine(POSE, g)[0] is Novelty.CO_DINH        # truc ban nen


def test_o_TRONG_khong_co_ket_luan_ve_ban_nen():
    """Khong co gi thi khong co gi de doi chieu."""
    bd = _scanned(9.0)
    assert bd.refine(POSE, grid(9.0))[0] is Novelty.KHONG_RO


def test_o_CHUA_BIET_khong_duoc_doi_chieu_ban_nen():
    """
    So do da khong dang tin thi doi chieu no la vo nghia - va nguy
    hiem, vi se sinh ra ket luan "co dinh" tu mot con so rac.
    """
    bd = _scanned(3.0)
    assert bd.refine(POSE, grid(1.0, conf=0.1))[0] is Novelty.KHONG_RO


def test_hazard_mac_dinh_KHONG_RO():
    """
    `scan()` khong biet gi ve ban nen nen khong duoc phep ket luan.
    Mac dinh phai la KHONG_RO, khong phai CO_DINH.
    """
    d = [9.0] * 12
    d[9] = 1.2
    assert scan(grid(d))[0].novelty is Novelty.KHONG_RO


def test_KHONG_RO_van_phai_duoc_canh_bao():
    """
    Chua quet cho nay khong co nghia la an toan. Moi nguy van phai
    sinh ra binh thuong, chi la khong noi them duoc "vat la".
    """
    bd = Backdrop()                       # chua quet gi ca
    d = [9.0] * 12
    d[9] = 1.2
    hz = scan(grid(d))
    assert hz and hz[0].state is Cell.CO_VAT
    assert bd.refine(POSE, grid(d))[9] is Novelty.KHONG_RO
