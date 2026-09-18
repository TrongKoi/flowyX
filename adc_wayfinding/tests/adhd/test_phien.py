"""
Kiem lop phien lam viec va y dinh thuc thi.

Bai quan trong nhat: KHONG cho tao y dinh khi thieu mot trong ba o.
Rang buoc do nghe phien nhung no chinh la can thiep - mot y dinh mo ho
la thu khong khoi dong duoc.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wayfinding.adhd.phien import (            # noqa: E402
    CAU_HOI,
    MIN_KY_TU,
    Phien,
    ThieuO,
    YDinh,
    goi_y_buoc_dau,
    tao_y_dinh,
    thieu_gi,
)

DAU = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
          "ùúủũụưừứửữựỳýỷỹỵđ")


def co_dau(s: str) -> bool:
    return any(c in DAU for c in s.lower())


def _y_dinh() -> YDinh:
    return YDinh(viec_gi="viết báo cáo",
                 khi_nao="sau bữa tối",
                 o_dau="bàn học")


# ------------------------------------------------- ba o bat buoc

def test_du_ba_o_thi_tao_duoc():
    y = tao_y_dinh("viết báo cáo", "sau bữa tối", "bàn học")
    assert y is not None
    assert y.viec_gi == "viết báo cáo"


@pytest.mark.parametrize("thieu", ["viec_gi", "khi_nao", "o_dau"])
def test_thieu_bat_ky_o_nao_thi_KHONG_tao_duoc(thieu: str):
    """
    Day la bai quan trong nhat cua file.

    Thieu mot o la y dinh van mo ho, va y dinh mo ho chinh la thu khong
    khoi dong duoc. Cho luu la bo qua can thiep.
    """
    o = {"viec_gi": "viết báo cáo", "khi_nao": "sau bữa tối",
         "o_dau": "bàn học"}
    o[thieu] = None
    assert tao_y_dinh(**o) is None


def test_thieu_gi_bao_dung_o_nao_thieu():
    assert thieu_gi(None, "sau bữa tối", "bàn học") == [ThieuO.VIEC_GI]
    assert thieu_gi("viết", None, None) == [ThieuO.KHI_NAO, ThieuO.O_DAU]
    assert thieu_gi("viết báo cáo", "sau bữa tối", "bàn học") == []


def test_chuoi_qua_ngan_tinh_la_chua_nhap():
    """
    Nguoi dung lam bam mot tieng, hoac micro bat duoc tieng on. Luu lai
    roi doc len sau se thanh mot cau vo nghia.
    """
    assert tao_y_dinh("à", "sau bữa tối", "bàn học") is None
    assert tao_y_dinh("   ", "sau bữa tối", "bàn học") is None


def test_khoang_trang_thua_bi_cat():
    y = tao_y_dinh("  viết báo cáo  ", " sau bữa tối ", " bàn học ")
    assert y.viec_gi == "viết báo cáo" and y.o_dau == "bàn học"


def test_moi_o_co_mot_cau_hoi_rieng():
    """
    Hoi rieng tung o chu khong gop mot o to: mot o to thi nguoi dung
    viet mot cau mo ho vao do, va ta quay ve diem xuat phat.
    """
    assert set(CAU_HOI) == set(ThieuO)
    for cau in CAU_HOI.values():
        assert co_dau(cau) and cau.endswith("?")


def test_cau_y_dinh_co_du_ba_thanh_phan():
    s = _y_dinh().cau()
    assert "sau bữa tối" in s and "viết báo cáo" in s and "bàn học" in s


def test_cau_y_dinh_co_dau():
    assert co_dau(_y_dinh().cau())


# ------------------------------------------------- goi y buoc dau

def test_cau_goi_y_hoi_MOT_buoc_va_ep_no_nho():
    """
    Khong hoi "chia viec nay ra di" - do la mot viec nua phai lam.
    """
    s = goi_y_buoc_dau()
    assert co_dau(s) and s.endswith("?")
    assert "nhỏ nhất" in s
    assert "ngay bây giờ" in s


# ------------------------------------------------- cac buoc

def test_them_buoc_va_dem_con_lai():
    p = Phien(y_dinh=_y_dinh())
    assert p.them_buoc("mở tệp lên") is True
    assert p.them_buoc("viết một câu") is True
    assert p.con_lai == 2
    assert p.buoc_hien_tai == "mở tệp lên"


def test_buoc_qua_ngan_bi_tu_choi():
    p = Phien(y_dinh=_y_dinh())
    assert p.them_buoc("à") is False
    assert p.them_buoc("") is False
    assert p.buoc == []


def test_xong_buoc_tien_tung_buoc_mot():
    p = Phien(y_dinh=_y_dinh())
    p.them_buoc("mở tệp lên")
    p.them_buoc("viết một câu")

    assert p.xong_buoc() is True
    assert p.chi_so == 1 and p.con_lai == 1
    assert p.buoc_hien_tai == "viết một câu"


def test_het_buoc_thi_xong():
    p = Phien(y_dinh=_y_dinh())
    p.them_buoc("mở tệp lên")
    assert p.xong is False
    p.xong_buoc()
    assert p.xong is True
    assert p.buoc_hien_tai is None
    assert p.con_lai == 0


def test_goi_them_khi_da_het_buoc_thi_tra_False():
    p = Phien(y_dinh=_y_dinh())
    p.them_buoc("mở tệp lên")
    p.xong_buoc()
    assert p.xong_buoc() is False


def test_phien_chua_co_buoc_nao_thi_chua_xong():
    """
    Mot phien khong buoc nao khong phai la mot phien da hoan thanh -
    de nham hai thu nay se khen mot viec chua bat dau.
    """
    p = Phien(y_dinh=_y_dinh())
    assert p.xong is False


def test_ghi_lai_thoi_diem_ket_thuc():
    p = Phien(y_dinh=_y_dinh())
    p.them_buoc("mở tệp lên")
    assert p.ket_thuc_luc is None
    p.xong_buoc()
    assert p.ket_thuc_luc is not None


def test_da_lam_giay_dung_lai_khi_xong():
    """Sau khi xong thi so giay khong tang nua."""
    p = Phien(y_dinh=_y_dinh(), bat_dau_luc=time.time() - 10.0)
    p.them_buoc("mở tệp lên")
    p.xong_buoc()
    a = p.da_lam_giay
    time.sleep(0.05)
    assert p.da_lam_giay == pytest.approx(a, abs=1e-6)


def test_khong_co_ham_nhay_toi_buoc_N():
    """
    Khoa lai mot quyet dinh thiet ke: chi tien MOT buoc moi lan.

    Nhay qua buoc la mat luon phan hoi cua nhung buoc bi bo, ma phan hoi
    tung buoc chinh la co che chong te liet.
    """
    assert not hasattr(Phien, "nhay_toi")
    assert not hasattr(Phien, "dat_chi_so")


# ------------------------------------------------- cau bat dau

def test_cau_bat_dau_neu_co_buoc_thi_noi_buoc_dau():
    p = Phien(y_dinh=_y_dinh())
    p.them_buoc("mở tệp lên")
    s = p.cau_bat_dau()
    assert "mở tệp lên" in s and co_dau(s)


def test_cau_bat_dau_khong_co_buoc_van_dung_duoc():
    s = Phien(y_dinh=_y_dinh()).cau_bat_dau()
    assert co_dau(s) and "bàn học" in s


# ------------------------------------------------- khong cham diem

def test_phien_KHONG_co_diem_so_hay_xep_loai():
    """
    Cham diem la buoc dau cua danh gia lam sang - ranh gioi khong duoc
    vuot. Xem docs/FLOWY_THIET_KE.md muc 4.4.
    """
    p = Phien(y_dinh=_y_dinh())
    for xau in ("diem", "score", "xep_loai", "muc_do", "danh_gia"):
        assert not any(xau in ten for ten in dir(p)), xau


# ------------------------------------------- nguoi dung tu dung

def test_phien_KHONG_BUOC_van_ket_thuc_duoc():
    """
    Duong di thuong gap nhat: noi viec gi / khi nao / o dau, bat dau,
    lam, roi bam Ket thuc. Khong buoc nao ca.

    Truoc khi co `ket_thuc()`, `xong` cua mot phien nhu vay khong bao gio
    thanh True - va nut Ket thuc im lang khong lam gi. Loi do chi lo ra
    khi chay that dau-cuoi, khong bai test don le nao bat duoc.
    """
    p = Phien(y_dinh=YDinh("viết báo cáo", "sau bữa tối",
                                       "bàn học"))
    assert not p.xong
    p.ket_thuc()
    assert p.xong


def test_phien_moi_tao_chua_phai_la_xong():
    """Mot phien vua tao, chua co buoc nao, khong phai phien da xong."""
    p = Phien(y_dinh=YDinh("viết báo cáo", "sau bữa tối",
                                       "bàn học"))
    assert not p.xong


def test_ket_thuc_khi_con_buoc_chua_danh_dau():
    """
    Nguoi dung biet ro hon app ve viec ho da lam xong hay chua. Bat ho
    danh dau tung buoc con lai truoc khi duoc dung la viec vo nghia.
    """
    p = Phien(y_dinh=YDinh("viết báo cáo", "sau bữa tối",
                                       "bàn học"))
    p.them_buoc("mở tệp lên")
    p.them_buoc("viết một câu")
    p.ket_thuc()
    assert p.xong


def test_ket_thuc_dong_dau_thoi_gian():
    p = Phien(y_dinh=YDinh("viết báo cáo", "sau bữa tối",
                                       "bàn học"))
    assert p.ket_thuc_luc is None
    p.ket_thuc()
    assert p.ket_thuc_luc is not None


def test_ket_thuc_hai_lan_khong_doi_dau_thoi_gian():
    """Thoi luong ghi lai phai la lan dung dau tien."""
    p = Phien(y_dinh=YDinh("viết báo cáo", "sau bữa tối",
                                       "bàn học"))
    p.ket_thuc()
    luc = p.ket_thuc_luc
    p.ket_thuc()
    assert p.ket_thuc_luc == luc
