"""
Kiem thu viec chon cau noi khi nhieu kenh cung muon noi.

File nay sinh ra tu mot loi that da xay ra: hai kenh dung chung mot bo
dem chong lap nen chung LUAN PHIEN lam moi lan nhau va noi khong dut.
Nguoi dung nghe hai cau thay nhau mai.

Loi do khong lo ra trong test don vi vi no chi xuat hien khi hai kenh
cung hoat dong, va logic thi nam trong mot script khong goi duoc tu
test. Tach ra module rieng chinh la de viet duoc nhung ca kiem thu
duoi day.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.loi_chung.announce import ReplyComposer

NAV = "Con khoang 5 met nua re phai."
NAV2 = "Re phai ngay bay gio."
HAZ = "Vat can ben phai, cach 1,1 met."
MU = "Khong quan sat duoc mat dat phia truoc. Hay dung gay xac nhan."


# ------------------------------------------------------------------
# Uu tien
# ------------------------------------------------------------------

def test_im_lang_khi_khong_co_gi_de_noi():
    assert ReplyComposer().compose(now=0.0) is None


def test_chuong_ngai_gap_cat_ngang_chi_duong():
    """Vap nga la hau qua tuc thi; re nham thi con sua duoc."""
    c = ReplyComposer()
    got = c.compose(now=0.0, chi_dan_text=NAV, gap_text=HAZ,
                    gap_urgent=True)
    assert got.channel == "nguy_hiem"
    assert got.text == HAZ
    assert got.haptic == "double_repeat"


def test_chi_duong_thang_chuong_ngai_khong_gap():
    c = ReplyComposer()
    got = c.compose(now=0.0, chi_dan_text=NAV, gap_text=MU,
                    gap_urgent=False)
    assert got.channel == "chi_dan"


def test_chuong_ngai_khong_gap_duoc_noi_khi_khong_co_chi_dan():
    """
    Canh bao "khong quan sat duoc mat dat" roi vao muc uu tien thap
    nhat, nhung TUYET DOI khong duoc nuot mat - do la luc he thong
    dang mu.
    """
    c = ReplyComposer()
    got = c.compose(now=0.0, gap_text=MU, gap_urgent=False)
    assert got.channel == "chuong_ngai"
    assert got.text == MU


# ------------------------------------------------------------------
# Chong lap - phan tung co loi
# ------------------------------------------------------------------

def test_chi_duong_khong_lap_lai():
    c = ReplyComposer()
    assert c.compose(now=0.0, chi_dan_text=NAV) is not None
    assert c.compose(now=0.1, chi_dan_text=NAV) is None


def test_chi_duong_khan_cap_van_duoc_lap_lai():
    c = ReplyComposer()
    assert c.compose(now=0.0, chi_dan_text=NAV, chi_dan_urgent=True) is not None
    assert c.compose(now=0.1, chi_dan_text=NAV, chi_dan_urgent=True) is not None


def test_doi_cau_chi_duong_thi_noi_ngay():
    c = ReplyComposer()
    c.compose(now=0.0, chi_dan_text=NAV)
    assert c.compose(now=0.1, chi_dan_text=NAV2) is not None


def test_HAI_KENH_KHONG_LUAN_PHIEN_NHAU():
    """
    Ca kiem thu quan trong nhat trong file - dung loi da xay ra.

    Truoc day hai kenh dung chung mot bo dem: chi duong noi thi bo dem
    thanh cau chi duong, roi canh bao thay khac nen noi, roi chi duong
    lai thay khac nen noi lai... lap vo han.

    Dung phai la: moi cau noi DUNG MOT LAN, roi im.
    """
    c = ReplyComposer()
    said = []
    for i in range(8):
        got = c.compose(now=i * 0.2, chi_dan_text=NAV,
                        gap_text=MU, gap_urgent=False)
        if got:
            said.append(got.channel)

    assert said == ["chi_dan", "chuong_ngai"], (
        f"Phai noi moi kenh dung mot lan roi im, nhung nhan duoc {said}"
    )


def test_chuong_ngai_duoc_nhac_lai_sau_mot_khoang():
    """
    San bong khong doc duoc do sau la TRANG THAI keo dai ca hanh lang.
    Noi mot lan roi im mai thi nguoi dung quen mat he thong dang mu -
    nhung nhac moi khung hinh thi ho tat he thong. Nen nhac thua.
    """
    c = ReplyComposer(calm_repeat_s=20.0)
    assert c.compose(now=0.0, gap_text=MU) is not None
    assert c.compose(now=10.0, gap_text=MU) is None
    assert c.compose(now=21.0, gap_text=MU) is not None


def test_nguy_hiem_duoc_nhac_lai_day_hon():
    """Nguoi dung dang tien ve phia no, nen phai nhac day hon."""
    c = ReplyComposer(urgent_repeat_s=4.0, calm_repeat_s=20.0)
    assert c.compose(now=0.0, gap_text=HAZ, gap_urgent=True) is not None
    assert c.compose(now=2.0, gap_text=HAZ, gap_urgent=True) is None
    assert c.compose(now=5.0, gap_text=HAZ, gap_urgent=True) is not None


def test_nguy_hiem_khong_de_chi_duong_chen_vao_giua():
    """
    Trong luc cho nhac lai canh bao nguy hiem, KHONG duoc quay ra noi
    chi dan duong: nguoi dung dang di ve phia vat can.
    """
    c = ReplyComposer(urgent_repeat_s=4.0)
    c.compose(now=0.0, gap_text=HAZ, gap_urgent=True)
    got = c.compose(now=1.0, chi_dan_text=NAV, gap_text=HAZ,
                    gap_urgent=True)
    assert got is None


def test_doi_canh_bao_thi_noi_ngay_khong_cho_het_khoang():
    c = ReplyComposer(urgent_repeat_s=4.0)
    c.compose(now=0.0, gap_text=HAZ, gap_urgent=True)
    got = c.compose(now=0.5, gap_text="Vat can ben trai, cach 0,8 met.",
                    gap_urgent=True)
    assert got is not None


def test_reset_xoa_het_bo_dem():
    c = ReplyComposer()
    c.compose(now=0.0, chi_dan_text=NAV)
    c.reset()
    assert c.compose(now=0.1, chi_dan_text=NAV) is not None
