"""
Kiem cac cau hoi dung luc.

Hai rang buoc duoc canh gac o day:

    1. moi chuoi la mot CAU HOI, khong phai loi khuyen
    2. bo do ket chi doi NET MAT, khong bao gio lam app len tieng
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wayfinding.adhd import phien          # noqa: E402
from wayfinding.adhd.cauhoi import (       # noqa: E402
    CAU_HOI,
    KET_LAU_GIAY,
    SO_LAN_ROI_DANG_KE,
    BoCauHoi,
    BoDoKet,
    LucNao,
    cau,
)

DAU = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
          "ùúủũụưừứửữựỳýỷỹỵđ")

MOI_CAU = [c for ds in CAU_HOI.values() for c in ds]


def co_dau(s: str) -> bool:
    return any(c in DAU for c in s.lower())


# ------------------------------------------------- cach viet

def test_moi_luc_deu_co_cau_hoi():
    """Cham vao nhan vat ma khong co gi de noi la mot cu cham bi lo."""
    for luc in LucNao:
        assert CAU_HOI.get(luc), luc


def test_moi_luc_co_HON_MOT_cau():
    """Cung mot cau lap lai lan thu nam se thanh tieng on."""
    for luc, ds in CAU_HOI.items():
        assert len(ds) >= 2, luc


def test_moi_chuoi_la_mot_CAU_HOI():
    """
    Cau hoi de lai quyen quyet dinh cho nguoi dung; loi khuyen lay no
    di. Day la rang buoc, khong phai so thich van phong.
    """
    for c in MOI_CAU:
        assert c.rstrip().endswith("?"), c


def test_moi_chuoi_co_dau_tieng_viet():
    for c in MOI_CAU:
        assert co_dau(c), c


def test_KHONG_cau_nao_la_menh_lenh():
    """
    "Hay chia nho cong viec ra" la mot chi thi. "Buoc nay co chia nho
    them duoc nua khong?" de nguoi dung tu tra loi.
    """
    for c in MOI_CAU:
        thap = c.lower()
        for xau in ("hãy ", "bạn nên", "bạn phải", "đừng ", "cần phải"):
            assert xau not in thap, c


def test_KHONG_cau_nao_ket_luan_ve_nguoi_dung():
    for c in MOI_CAU:
        thap = c.lower()
        for xau in ("bạn đang bị", "bạn bị", "bạn mất tập trung",
                    "bạn kém", "bạn hay", "bạn luôn", "vấn đề của bạn"):
            assert xau not in thap, c


def test_khong_co_cau_trung_lap_giua_cac_luc():
    assert len(set(MOI_CAU)) == len(MOI_CAU)


def test_cau_go_te_liet_TRUNG_voi_ban_trong_phien():
    """
    `phien.goi_y_buoc_dau()` va cau dau cua luc DANG_KET la cung mot
    cau hoi. Hai ban lech nhau thi nguoi dung nghe hai cach hoi khac
    nhau cho cung mot tinh huong.
    """
    assert phien.goi_y_buoc_dau() in CAU_HOI[LucNao.DANG_KET]


# ------------------------------------------------- xoay vong

def test_cau_xoay_vong_theo_lan():
    ds = CAU_HOI[LucNao.DANG_KET]
    for i in range(len(ds) * 2):
        assert cau(LucNao.DANG_KET, i) == ds[i % len(ds)]


def test_bo_cau_hoi_khong_lap_lien_tiep():
    bo = BoCauHoi()
    ds = CAU_HOI[LucNao.DANG_KET]
    thay = [bo.hoi(LucNao.DANG_KET) for _ in range(len(ds))]
    assert len(set(thay)) == len(ds)


def test_moi_luc_dem_rieng():
    """Hoi mot cau o luc nay khong duoc lam nhay cau o luc khac."""
    bo = BoCauHoi()
    bo.hoi(LucNao.DANG_KET)
    bo.hoi(LucNao.DANG_KET)
    assert bo.hoi(LucNao.BI_KEO_DI) == CAU_HOI[LucNao.BI_KEO_DI][0]


# ------------------------------------------------- bo do ket

def test_chua_bat_dau_buoc_nao_thi_chua_ket():
    assert not BoDoKet().dang_ket(1000.0)


def test_o_mot_buoc_qua_lau_thi_la_dang_ket():
    bo = BoDoKet()
    bo.sang_buoc(0, 1000.0)
    assert not bo.dang_ket(1000.0 + KET_LAU_GIAY - 1.0)
    assert bo.dang_ket(1000.0 + KET_LAU_GIAY)


def test_sang_buoc_moi_thi_dong_ho_chay_lai():
    bo = BoDoKet()
    bo.sang_buoc(0, 1000.0)
    bo.sang_buoc(1, 1000.0 + KET_LAU_GIAY - 1.0)
    assert not bo.dang_ket(1000.0 + KET_LAU_GIAY)


def test_bao_lai_cung_mot_buoc_thi_dong_ho_KHONG_chay_lai():
    """
    Moi goi tin deu bao so buoc hien tai. Neu moi lan bao deu dat lai
    dong ho thi khong bao gio do duoc gi.
    """
    bo = BoDoKet()
    bo.sang_buoc(0, 1000.0)
    for t in range(1000, 1000 + int(KET_LAU_GIAY), 60):
        bo.sang_buoc(0, float(t))
    assert bo.dang_ket(1000.0 + KET_LAU_GIAY)


def test_roi_khoi_app_du_nhieu_lan_thi_la_bi_keo_di():
    bo = BoDoKet()
    for _ in range(SO_LAN_ROI_DANG_KE - 1):
        bo.roi_di()
    assert not bo.bi_keo_di
    bo.roi_di()
    assert bo.bi_keo_di


# ------------------------------------------------- chon luc

def test_chua_bat_dau_thi_hoi_ve_viec_bat_dau():
    bo = BoDoKet()
    assert bo.luc_nen_hoi(0.0, da_bat_dau=False,
                          da_xong=False) == LucNao.CHUA_BAT_DAU


def test_xong_roi_thi_hoi_ve_lan_vua_xong():
    bo = BoDoKet()
    assert bo.luc_nen_hoi(0.0, da_bat_dau=True,
                          da_xong=True) == LucNao.VUA_XONG


def test_xong_duoc_xet_TRUOC_ca_dang_ket():
    """Xong roi thi khong con ket nua, du dong ho noi gi."""
    bo = BoDoKet()
    bo.sang_buoc(0, 0.0)
    assert bo.luc_nen_hoi(KET_LAU_GIAY * 2, da_bat_dau=True,
                          da_xong=True) == LucNao.VUA_XONG


def test_dang_ket_duoc_xet_truoc_bi_keo_di():
    """
    Nguoi dung ket o buoc VA roi ra ngoai nhieu lan thuong la cung mot
    chuyen: ho ket nen ho roi ra. Hoi ve cai buoc dang ket thi gan goc
    hon la hoi ve moi truong.
    """
    bo = BoDoKet()
    bo.sang_buoc(0, 0.0)
    for _ in range(SO_LAN_ROI_DANG_KE):
        bo.roi_di()
    assert bo.luc_nen_hoi(KET_LAU_GIAY, da_bat_dau=True,
                          da_xong=False) == LucNao.DANG_KET


def test_bi_keo_di_ma_chua_ket_lau_thi_hoi_ve_moi_truong():
    bo = BoDoKet()
    bo.sang_buoc(0, 0.0)
    for _ in range(SO_LAN_ROI_DANG_KE):
        bo.roi_di()
    assert bo.luc_nen_hoi(10.0, da_bat_dau=True,
                          da_xong=False) == LucNao.BI_KEO_DI


def test_dang_lam_binh_thuong_van_co_cau_de_hoi():
    """
    Nguoi dung cham vao nhan vat la ho dang muon gi do. Im lang o day
    la mot cu cham bi lo - nen luon co mot cau.
    """
    bo = BoDoKet()
    bo.sang_buoc(0, 0.0)
    luc = bo.luc_nen_hoi(10.0, da_bat_dau=True, da_xong=False)
    assert isinstance(luc, LucNao)
    assert CAU_HOI[luc]
