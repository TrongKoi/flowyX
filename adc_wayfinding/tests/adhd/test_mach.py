"""
Kiem lop giu mach chuyen di.

Bai quan trong nhat: cau khoi phuc phai co DU BA PHAN. Rut gon con
moi chi dan la quay ve dung hanh vi ma tinh nang nay sinh ra de sua.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.adhd.mach import (                  # noqa: E402
    NGUONG_PHAN_TAM_S,
    BoTheoMach,
    ViecDangLam,
    cau_hoi_muc_dich,
    cau_khoi_phuc,
    cau_xong_viec,
    nhan_muc_dich,
)

DAU = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
          "ùúủũụưừứửữựỳýỷỹỵđ")


def co_dau(s: str) -> bool:
    return any(c in DAU for c in s.lower())


def _cd(muc_dich: str | None = None) -> ViecDangLam:
    return ViecDangLam(ten_viec="phòng 6.04", muc_dich=muc_dich)


# ------------------------------------------------- nho muc dich

def test_cau_hoi_co_dau_va_khong_ep_tra_loi():
    s = cau_hoi_muc_dich()
    assert co_dau(s)
    assert "?" in s


def test_luu_duoc_muc_dich_nguoi_dung_noi():
    cd = _cd()
    assert nhan_muc_dich(cd, "nộp đơn xin nghỉ") is True
    assert cd.muc_dich == "nộp đơn xin nghỉ"


def test_im_lang_thi_khong_luu_va_khong_hoi_lai():
    cd = _cd()
    assert nhan_muc_dich(cd, None) is False
    assert cd.muc_dich is None
    assert cd.da_hoi_muc_dich is True, "phai danh dau da hoi de khong hoi lai"


@pytest.mark.parametrize("loi", ["không", "thôi", "bỏ qua", "Khỏi", "kệ"])
def test_tu_choi_thi_khong_luu(loi: str):
    cd = _cd()
    assert nhan_muc_dich(cd, loi) is False
    assert cd.muc_dich is None


def test_tra_loi_qua_ngan_khong_duoc_coi_la_muc_dich():
    """
    Nguoi dung lam bam mot tieng, hoac micro bat duoc tieng on. Luu lai
    roi doc lai luc toi noi se thanh mot cau vo nghia.
    """
    cd = _cd()
    assert nhan_muc_dich(cd, "à") is False
    assert cd.muc_dich is None


def test_khoang_trang_thua_bi_cat():
    cd = _cd()
    nhan_muc_dich(cd, "   họp nhóm   ")
    assert cd.muc_dich == "họp nhóm"


# ------------------------------------------------- cau toi noi

def test_toi_noi_co_muc_dich_thi_nhac_lai():
    """Day la luc muc dich huu ich nhat - nguoi dung vua di mot quang."""
    s = cau_xong_viec(_cd("nộp đơn xin nghỉ"))
    assert "phòng 6.04" in s and "nộp đơn xin nghỉ" in s


def test_toi_noi_khong_co_muc_dich_thi_noi_gon():
    """Khong duoc de cho trong, khong duoc hoi lai."""
    s = cau_xong_viec(_cd())
    assert "phòng 6.04" in s
    assert "để" not in s
    assert "?" not in s


def test_cau_xong_viec_co_dau():
    assert co_dau(cau_xong_viec(_cd("họp nhóm")))


# --------------------------------------------- cau khoi phuc mach

def test_cau_khoi_phuc_co_DU_BA_PHAN():
    """
    (a) dang di dau, (b) de lam gi, (c) viec truoc mat.

    Day la bai kiem quan trong nhat cua file. Thieu mot phan la quay ve
    dung hanh vi can sua.
    """
    s = cau_khoi_phuc(_cd("nộp đơn xin nghỉ"),
                      chi_dan="Rẽ phải ở đây.", buoc_con_lai=2)
    assert "phòng 6.04" in s          # (a)
    assert "nộp đơn xin nghỉ" in s    # (b)
    assert "Rẽ phải ở đây." in s      # (c)


def test_khoi_phuc_dat_chi_dan_o_CUOI_cau():
    """
    Chi dan la thu duy nhat can hanh dong ngay. Dat no giua mot cau dai
    se lam no bi troi noi.
    """
    s = cau_khoi_phuc(_cd("họp nhóm"), chi_dan="Rẽ trái.", buoc_con_lai=1)
    assert s.rstrip().endswith("Rẽ trái.")


def test_khoi_phuc_khong_co_muc_dich_thi_bo_phan_do():
    s = cau_khoi_phuc(_cd(), chi_dan="Đi thẳng.", buoc_con_lai=3)
    assert "phòng 6.04" in s and "Đi thẳng." in s
    assert " để " not in s


def test_khoi_phuc_khong_co_chi_dan_van_dung_ngu_canh():
    """Chua co chi dan moi thi van phai noi dang di dau va de lam gi."""
    s = cau_khoi_phuc(_cd("họp nhóm"))
    assert "phòng 6.04" in s and "họp nhóm" in s


def test_cau_khoi_phuc_co_dau():
    assert co_dau(cau_khoi_phuc(_cd("họp nhóm"), chi_dan="Rẽ phải."))


# ------------------------------------------------- phat hien dut mach

def test_dung_ngan_khong_tinh_la_dut_mach():
    """Cho thang may, nhuong duong, chinh day deo - chuyen binh thuong."""
    bo = BoTheoMach()
    assert bo.cap_nhat(0.0, dang_di=True) is False
    assert bo.cap_nhat(10.0, dang_di=False) is False
    assert bo.cap_nhat(40.0, dang_di=False) is False
    assert bo.cap_nhat(50.0, dang_di=True) is False


def test_dung_lau_roi_di_lai_thi_bao_dut_mach():
    bo = BoTheoMach()
    bo.cap_nhat(0.0, dang_di=True)
    bo.cap_nhat(10.0, dang_di=False)
    bo.cap_nhat(10.0 + NGUONG_PHAN_TAM_S + 1, dang_di=False)
    assert bo.cap_nhat(10.0 + NGUONG_PHAN_TAM_S + 2, dang_di=True) is True


def test_chi_bao_DUNG_MOT_LAN():
    """Bao moi khung hinh sau do se thanh doc lap vo han."""
    bo = BoTheoMach()
    bo.cap_nhat(0.0, dang_di=False)
    bo.cap_nhat(200.0, dang_di=False)
    assert bo.cap_nhat(201.0, dang_di=True) is True
    assert bo.cap_nhat(202.0, dang_di=True) is False
    assert bo.cap_nhat(203.0, dang_di=True) is False


def test_dang_dung_lau_thi_bao_trang_thai_nhung_chua_phat_cau():
    """
    Cau khoi phuc chi co nghia khi nguoi dung DA di lai. Doc no trong
    luc ho van dang dung la noi vao khong khi.
    """
    bo = BoTheoMach()
    bo.cap_nhat(0.0, dang_di=False)
    assert bo.cap_nhat(200.0, dang_di=False) is False
    assert bo.dang_dut_mach is True


def test_dut_mach_nhieu_lan_trong_mot_chuyen_di():
    bo = BoTheoMach()
    bo.cap_nhat(0.0, dang_di=False)
    bo.cap_nhat(200.0, dang_di=False)
    assert bo.cap_nhat(201.0, dang_di=True) is True

    bo.cap_nhat(300.0, dang_di=False)
    bo.cap_nhat(500.0, dang_di=False)
    assert bo.cap_nhat(501.0, dang_di=True) is True


def test_nguong_doi_duoc():
    """Con so 90 giay la uoc luong, phai do lai bang nguoi dung that."""
    bo = BoTheoMach(nguong_s=10.0)
    bo.cap_nhat(0.0, dang_di=False)
    bo.cap_nhat(11.0, dang_di=False)
    assert bo.cap_nhat(12.0, dang_di=True) is True


# ------------------------------------------- co duoc GOI khong

def test_run_flowy_co_goi_lop_ADHD():
    """
    Doc ma nguon runner de chac hai lop nay duoc noi vao duong chay.

    Repo nay da tung co mot lop moc neo viet xong, 28 test xanh, ma
    khong runner nao goi toi - xem PR #18. Bai nay de chuyen do khong
    lap lai.
    """
    src = (Path(__file__).resolve().parents[2] / "run_flowy.py").read_text(
        encoding="utf-8")
    # Kiem THEO TEN MODULE, khong theo nguyen van dong import: them mot
    # module nua vao cung dong import la chuyen binh thuong, va mot bai
    # test do vi ly do do chi day nguoi ta di sua test.
    assert "import" in src and "mach" in src and "timeblind" in src
    assert "mach.cau_khoi_phuc(" in src, "khong dung lai ngu canh sau phan tam"
    assert "mach.cau_xong_viec(" in src, "khong nhac muc dich luc toi noi"
    assert "timeblind.tinh(" in src, "khong neo lo trinh vao gio that"
    assert "bo_nhac.cap_nhat(" in src, "khong nhac theo moc thoi gian"


def test_cau_khoi_phuc_duoc_dat_TRUOC_bo_dem_chong_lap():
    """
    Cau khoi phuc gan voi mot khoanh khac cu the. Dua qua bo dem chong
    lap se lam no bi nuot, va nguoi dung mat dung cau can nhat.
    """
    src = (Path(__file__).resolve().parents[2] / "run_flowy.py").read_text(
        encoding="utf-8")

    # Cau khoi phuc gan thang vao `tra.say`, con bo dem chong lap chi
    # chay o nhanh `elif tra.say is None` phia sau. Thu tu do la thu
    # bao dam cau khoi phuc khong bao gio bi nuot.
    i_khoi_phuc = src.index("tra.say = mach.cau_khoi_phuc(")
    i_composer = src.index("self.composer.compose(")
    assert i_khoi_phuc < i_composer, "cau khoi phuc dat SAU bo dem"
    assert "elif tra.say is None" in src, "bo dem khong nhuong duong"


# ------------------- vang mat ma KHONG co goi tin nao

def test_dut_mach_khi_CHI_co_mot_goi_tin_luc_vang():
    """
    "Vang" o Flowy nghia la nguoi dung da mo app khac, va he dieu hanh
    co the treo tien trinh trong suot khoang do.

    Truong hop CAN cau dung lai ngu canh nhat lai la truong hop it goi
    tin nhat: di cang lau, cang it kha nang co goi tin giua chung.
    """
    bo = BoTheoMach()
    assert not bo.cap_nhat(0.0, dang_di=True)
    assert not bo.cap_nhat(1.0, dang_di=False)       # goi tin vang DUY NHAT
    assert bo.cap_nhat(1.0 + NGUONG_PHAN_TAM_S, dang_di=True)


def test_vang_chua_du_lau_thi_khong_tinh_la_dut_mach():
    """Liec sang app khac vai giay khong phai la mat mach."""
    bo = BoTheoMach()
    bo.cap_nhat(0.0, dang_di=True)
    bo.cap_nhat(1.0, dang_di=False)
    assert not bo.cap_nhat(1.0 + NGUONG_PHAN_TAM_S - 1.0, dang_di=True)


def test_chi_bao_dut_mach_MOT_lan():
    """Bao hai lan la doc cau dung lai ngu canh hai lan lien tiep."""
    bo = BoTheoMach()
    bo.cap_nhat(0.0, dang_di=True)
    bo.cap_nhat(1.0, dang_di=False)
    assert bo.cap_nhat(1.0 + NGUONG_PHAN_TAM_S, dang_di=True)
    assert not bo.cap_nhat(2.0 + NGUONG_PHAN_TAM_S, dang_di=True)


def test_van_bat_duoc_khi_co_nhieu_goi_tin_luc_vang():
    """Duong cu phai con nguyen - dien thoai van gui khi chay nen."""
    bo = BoTheoMach()
    bo.cap_nhat(0.0, dang_di=True)
    for t in range(1, int(NGUONG_PHAN_TAM_S) + 5, 2):
        bo.cap_nhat(float(t), dang_di=False)
    assert bo.cap_nhat(NGUONG_PHAN_TAM_S + 10.0, dang_di=True)
