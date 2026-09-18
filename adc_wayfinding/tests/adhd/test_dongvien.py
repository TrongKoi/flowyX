"""
Kiem lop phan hoi tich cuc va ban dong hanh.

Bai quan trong nhat file nay khong phai mot bai chuc nang ma la mot
bai RANG BUOC: khong duoc co trang thai tieu cuc nao. ADHD thuong di
kem nhay cam voi that bai, va mot nhan vat to ra that vong se lam
nguoi dung tranh mo app - luc do moi tinh nang khac deu thanh vo dung.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.adhd.dongvien import (               # noqa: E402
    AM_TOI_DICH,
    AM_XONG_BUOC,
    CAU,
    CHUOI_TOI_THIEU,
    HAPTIC_XONG_BUOC,
    BoPhanHoi,
    SoChuoi,
    TrangThai,
    phan_ung,
)
from wayfinding.loi_chung.speech import HAPTIC_PATTERNS   # noqa: E402

DAU = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
          "ùúủũụưừứửữựỳýỷỹỵđ")


def co_dau(s: str) -> bool:
    return any(c in DAU for c in s.lower())


# ------------------------------------------------- xong chang

def test_sang_chang_moi_thi_bao_mot_lan():
    bo = BoPhanHoi()
    assert bo.xong_buoc(0) is None          # lan dau chi ghi nhan
    assert bo.xong_buoc(0) is None
    ph = bo.xong_buoc(1)
    assert ph is not None
    assert ph.haptic == HAPTIC_XONG_BUOC and ph.am == AM_XONG_BUOC


def test_van_o_chang_cu_thi_im_lang():
    """Bao moi khung hinh se thanh rung lien tuc."""
    bo = BoPhanHoi()
    bo.xong_buoc(0)
    bo.xong_buoc(1)
    assert bo.xong_buoc(1) is None
    assert bo.xong_buoc(1) is None


def test_di_lac_rot_ve_chang_truoc_thi_KHONG_khen():
    """
    Chi so GIAM khong phai thanh tuu gi, va cang khong phai luc de khen.
    """
    bo = BoPhanHoi()
    bo.xong_buoc(0)
    bo.xong_buoc(2)
    assert bo.xong_buoc(1) is None


def test_lac_roi_quay_lai_thi_khen_lai_khi_vuot_qua():
    bo = BoPhanHoi()
    bo.xong_buoc(0)
    bo.xong_buoc(2)
    bo.xong_buoc(1)                          # di lac
    assert bo.xong_buoc(2) is not None       # vuot lai


def test_phan_hoi_xong_buoc_KHONG_co_cau_noi():
    """
    Mot cai rung dung luc tot hon mot cau noi: no khong chiem kenh tai
    va khong cat ngang dong suy nghi.
    """
    bo = BoPhanHoi()
    bo.xong_buoc(0)
    assert bo.xong_buoc(1).cau is None


def test_ma_rung_xong_buoc_co_that_trong_bang_ma():
    """Ma khong co trong bang thi dien thoai im lang - hong khong tieng."""
    assert HAPTIC_XONG_BUOC in HAPTIC_PATTERNS


def test_rung_xong_buoc_NHE_hon_rung_canh_bao():
    """
    Day la loi khen, khong phai canh bao. Rung manh bang canh bao nguy
    hiem se lam nguoi dung giat minh va hoc sai y nghia cua ma rung.
    """
    khen = sum(HAPTIC_PATTERNS[HAPTIC_XONG_BUOC])
    nguy = sum(HAPTIC_PATTERNS["double_repeat"])
    assert khen < nguy


# ------------------------------------------- ban dong hanh

def test_toi_dich_dung_gio_thi_vui():
    ph = phan_ung(toi_dich=True, dung_gio=True)
    assert ph.trang_thai is TrangThai.VUI
    assert ph.am == AM_TOI_DICH and co_dau(ph.cau)


def test_vua_khoi_phuc_thi_thong_cam_chu_khong_trach():
    ph = phan_ung(vua_khoi_phuc=True)
    assert ph.trang_thai is TrangThai.THONG_CAM
    assert co_dau(ph.cau)


def test_khoi_phuc_KHONG_phat_am_thanh():
    """
    Nguoi dung vua bi phan tam va dang duoc dung lai ngu canh. Them mot
    tieng dong la them mot thu phai xu ly, dung luc ho can it thu phai
    xu ly nhat.
    """
    assert phan_ung(vua_khoi_phuc=True).am is None


def test_chuoi_ngay_du_dai_thi_tu_hao():
    ph = phan_ung(toi_dich=True, dung_gio=True, chuoi_ngay=CHUOI_TOI_THIEU)
    assert ph.trang_thai is TrangThai.TU_HAO
    assert str(CHUOI_TOI_THIEU) in ph.cau


def test_chuoi_uu_tien_cao_hon_toi_dich_thuong():
    """Chuoi hiem hon nen dat cao hon."""
    ph = phan_ung(toi_dich=True, dung_gio=True, chuoi_ngay=10)
    assert ph.trang_thai is TrangThai.TU_HAO


def test_khong_co_su_kien_gi_thi_binh_thuong():
    ph = phan_ung()
    assert ph.trang_thai is TrangThai.BINH_THUONG
    assert ph.am is None and ph.cau in (None, "")


# ----------------------- RANG BUOC: khong co trang thai tieu cuc

def test_toi_dich_MUON_khong_sinh_trang_thai_tieu_cuc():
    """
    Im lang o day la co y: khong khen mot viec khong xay ra, nhung
    tuyet doi khong trach.
    """
    ph = phan_ung(toi_dich=True, dung_gio=False)
    assert ph.trang_thai is TrangThai.BINH_THUONG


def test_KHONG_co_trang_thai_buon_hay_that_vong_nao():
    """
    Rang buoc cung cua module. Neu ai do them mot trang thai tieu cuc
    thi bai nay do ngay, va comment nay giai thich vi sao khong duoc.
    """
    xau = ("buon", "that_vong", "thatvong", "tiec", "trach", "te", "kem")
    for tt in TrangThai:
        assert not any(x in tt.value for x in xau), tt


def test_khong_cau_nao_trach_moc_nguoi_dung():
    for tt, cau in CAU.items():
        s = cau.lower()
        for xau in ("đáng lẽ", "lẽ ra", "tại sao", "lại trễ", "không nên",
                    "đừng", "thất vọng"):
            assert xau not in s, (tt, cau)


@pytest.mark.parametrize("tt", list(TrangThai))
def test_moi_cau_deu_co_dau_hoac_rong(tt: TrangThai):
    """Chuoi nay se duoc DOC LEN. Rong thi khong doc, con lai phai co dau."""
    s = CAU[tt]
    assert s == "" or co_dau(s)


# ------------------------------------------------- chuoi ngay

def test_ngay_dau_tien_dung_gio_cho_chuoi_mot():
    so = SoChuoi()
    assert so.ghi("2026-09-15", dung_gio=True) == 1


def test_nhieu_ngay_lien_tiep_thi_chuoi_tang():
    so = SoChuoi()
    so.ghi("2026-09-13", True)
    so.ghi("2026-09-14", True)
    assert so.ghi("2026-09-15", True) == 3


def test_mot_ngay_tre_thi_chuoi_ve_khong():
    so = SoChuoi()
    so.ghi("2026-09-13", True)
    so.ghi("2026-09-14", True)
    assert so.ghi("2026-09-15", False) == 0


def test_cung_mot_ngay_ghi_nhieu_lan_chi_tinh_mot():
    """
    Dem theo chuyen di se thuong nguoi di nhieu va phat nguoi di it, ma
    so chuyen di mot ngay khong noi len dieu gi ve viec giu gio.
    """
    so = SoChuoi()
    so.ghi("2026-09-15", True)
    assert so.ghi("2026-09-15", True) == 1
    assert so.ghi("2026-09-15", False) == 1, "ghi lai khong duoc xoa chuoi"


def test_luu_va_doc_lai_giu_nguyen(tmp_path: Path):
    p = tmp_path / "chuoi.json"
    so = SoChuoi()
    so.ghi("2026-09-14", True)
    so.ghi("2026-09-15", True)
    so.luu(p)
    assert SoChuoi.doc(p).chuoi == 2


def test_so_chua_co_thi_bat_dau_tu_khong(tmp_path: Path):
    assert SoChuoi.doc(tmp_path / "chua-co.json").chuoi == 0


def test_so_hong_thi_bat_dau_lai_chu_khong_lam_sap(tmp_path: Path):
    """Mat chuoi la phien toai; app khong chay duoc la mot loi."""
    p = tmp_path / "hong.json"
    p.write_text("{khong phai json", encoding="utf-8")
    assert SoChuoi.doc(p).chuoi == 0


def test_json_doc_duoc_bang_mat_thuong(tmp_path: Path):
    p = tmp_path / "c.json"
    so = SoChuoi()
    so.ghi("2026-09-15", True)
    so.luu(p)
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["ngay_cuoi"] == "2026-09-15" and d["chuoi"] == 1


# ------------------------------------------- co duoc GOI khong

def test_run_flowy_co_goi_lop_phan_hoi():
    src = (Path(__file__).resolve().parents[2] / "run_flowy.py").read_text(
        encoding="utf-8")
    assert "dongvien" in src, "runner chua import lop phan hoi"
    assert "xong_buoc(" in src, "khong phat phan hoi khi xong chang"
    assert "dongvien.phan_ung(" in src, "ban dong hanh khong duoc goi"
