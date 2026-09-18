"""
Kiem lop neo lo trinh vao gio that.

Bai kiem quan trong nhat o day khong phai phep tinh - ma la CAU NOI:
moi truong hop deu phai ket thuc bang mot viec cu the phai lam. Cau
kieu "sắp trễ rồi" ma khong kem hanh dong la vo dung, no chi them lo au
ma khong giam duoc gi.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.adhd.timeblind import (            # noqa: E402
    DEM_KHOI_DONG_PHUT,
    DEM_TY_LE,
    MOC_NHAC_PHUT,
    BoNhacGio,
    Muc,
    cau,
    dem_an_toan,
    gio_doc,
    phut_trong_ngay,
    tinh,
)

DAU = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
          "ùúủũụưừứửữựỳýỷỹỵđ")


def co_dau(s: str) -> bool:
    return any(c in DAU for c in s.lower())


def H(gio: float, phut: float = 0.0) -> float:
    """Gio:phut -> phut tinh tu nua dem. Cho test doc de hon."""
    return gio * 60.0 + phut


# ------------------------------------------------------------- dem

def test_dem_co_ca_phan_ty_le_lan_phan_hang_so():
    """
    Hai nguon tre khac nhau nen phai co hai thanh phan.

    Chi ty le thi tuyen ngan gan nhu khong co dem; chi hang so thi
    tuyen dai bi dem thieu.
    """
    assert dem_an_toan(0.0) == pytest.approx(DEM_KHOI_DONG_PHUT)
    assert dem_an_toan(10.0) == pytest.approx(10.0 * DEM_TY_LE
                                              + DEM_KHOI_DONG_PHUT)


def test_dem_lam_tuyen_dai_ton_nhieu_hon_tuyen_ngan():
    assert dem_an_toan(30.0) > dem_an_toan(5.0)


def test_khong_bao_gio_neo_dung_khop_gio_den():
    """
    uoc_phut() la thoi gian TRUNG BINH. Neo dung khop la cam chac tre
    mot nua so lan.
    """
    kh = tinh(phut_di=6.0, gio_bay_gio=H(13, 48), gio_hen=H(14))
    assert kh.phut_can > kh.phut_di


# ------------------------------------------------------- phan muc

def test_con_nhieu_thoi_gian_thi_muc_SOM():
    kh = tinh(phut_di=6.0, gio_bay_gio=H(13, 0), gio_hen=H(14))
    assert kh.muc is Muc.SOM


def test_vai_phut_nua_thi_muc_SAP_DEN_GIO():
    kh = tinh(phut_di=6.0, gio_bay_gio=H(13, 48), gio_hen=H(14))
    assert kh.muc is Muc.SAP_DEN_GIO


def test_duoi_nguong_an_toan_thi_muc_DI_NGAY():
    # 13:50 -> con 10 phut toi gio, can 8,7 phut => con 1,3 phut truoc
    # khi phai di, duoi nguong 2 phut.
    kh = tinh(phut_di=6.0, gio_bay_gio=H(13, 50), gio_hen=H(14))
    assert kh.muc is Muc.DI_NGAY


def test_khong_con_kip_thi_muc_DA_TRE():
    kh = tinh(phut_di=6.0, gio_bay_gio=H(13, 58), gio_hen=H(14))
    assert kh.muc is Muc.DA_TRE
    assert kh.tre_bao_nhieu_phut > 0


def test_con_kip_thi_tre_bao_nhieu_phut_bang_khong():
    kh = tinh(phut_di=6.0, gio_bay_gio=H(13, 0), gio_hen=H(14))
    assert kh.tre_bao_nhieu_phut == 0.0


# ------------------------------------------------------- cau noi

@pytest.mark.parametrize("phut_bat_dau", [0, 40, 48, 52, 58, 61])
def test_moi_cau_deu_co_dau_tieng_viet(phut_bat_dau: int):
    """Chuoi nay se duoc DOC LEN. Mat dau la doc ra am vo nghia."""
    bay_gio = H(13, phut_bat_dau)
    kh = tinh(phut_di=6.0, gio_bay_gio=bay_gio, gio_hen=H(14))
    assert co_dau(cau(kh, "phòng 6.04", bay_gio, "Lớp học"))


@pytest.mark.parametrize("phut_bat_dau", [0, 48, 52, 58])
def test_moi_cau_deu_ket_thuc_bang_mot_viec_PHAI_LAM(phut_bat_dau: int):
    """
    Yeu cau cung: khong duoc co cau nao chi neu tinh trang ma khong
    neu hanh dong. "Sắp trễ rồi" la vi du cua cai KHONG duoc phep.
    """
    bay_gio = H(13, phut_bat_dau)
    kh = tinh(phut_di=6.0, gio_bay_gio=bay_gio, gio_hen=H(14))
    s = cau(kh, "phòng 6.04", bay_gio, "Lớp học").lower()
    assert any(k in s for k in ("cần", "nên", "bắt tay vào", "làm tiếp")), s


def test_cau_neo_du_ba_moc_thoi_gian():
    """Gio hen, thoi gian di, va gio hien tai - thieu mot la van troi noi."""
    bay_gio = H(13, 48)
    kh = tinh(phut_di=6.0, gio_bay_gio=bay_gio, gio_hen=H(14))
    s = cau(kh, "phòng 6.04", bay_gio, "Lớp học")
    assert "14 giờ" in s           # gio hen
    assert "6 phút" in s           # thoi gian di
    assert "13 giờ 48" in s        # bay gio


def test_cau_khi_da_tre_noi_ro_muon_bao_nhieu_va_lam_gi():
    """Khong duoc mo ho. Phai co con so, va phai co viec lam tiep."""
    bay_gio = H(14, 5)
    kh = tinh(phut_di=6.0, gio_bay_gio=bay_gio, gio_hen=H(14))
    s = cau(kh, "phòng 6.04", bay_gio, "Lớp học")
    assert "muộn" in s and "phút" in s
    assert "làm tiếp" in s or "bắt tay vào" in s


def test_khong_co_ten_su_kien_thi_cau_van_dung_duoc():
    """Khong moc su kien thi noi thang la can xong luc may gio."""
    bay_gio = H(13, 48)
    kh = tinh(phut_di=6.0, gio_bay_gio=bay_gio, gio_hen=H(14))
    s = cau(kh, "viết báo cáo", bay_gio)
    assert co_dau(s)
    assert "Cần xong lúc" in s
    assert "báo cáo" in s


def test_co_ten_su_kien_thi_dung_ten_do_lam_moc():
    bay_gio = H(13, 48)
    kh = tinh(phut_di=6.0, gio_bay_gio=bay_gio, gio_hen=H(14))
    s = cau(kh, "viết báo cáo", bay_gio, "Hạn nộp")
    assert "Hạn nộp lúc 14 giờ" in s
    assert "bắt đầu lúc" not in s, "doc go voi mot han chot"


# ------------------------------------------------- dinh dang gio

def test_gio_doc_khong_dung_dau_hai_cham():
    """Bo doc tieng Viet doc "14:00" khong on dinh."""
    assert ":" not in gio_doc(H(14))
    assert gio_doc(H(14)) == "14 giờ"
    assert gio_doc(H(13, 48)) == "13 giờ 48"


def test_gio_doc_lam_tron_len_qua_gio_khong_ra_60_phut():
    """13 giờ 59,7 phải thành 14 giờ, không phải "13 giờ 60"."""
    assert gio_doc(H(13, 59) + 0.7) == "14 giờ"


def test_phut_trong_ngay_nam_trong_mot_ngay():
    v = phut_trong_ngay()
    assert 0.0 <= v < 1440.0


# --------------------------------------------- nhac trong luc di

def test_moi_moc_chi_bao_dung_mot_lan():
    """Lap lai cung mot moc la nguon lam phien lon nhat."""
    bo = BoNhacGio(gio_hen=H(14))
    assert bo.cap_nhat(H(13, 50)) is not None      # moc 10 phut
    assert bo.cap_nhat(H(13, 50)) is None
    assert bo.cap_nhat(H(13, 51)) is None


def test_nhac_luon_co_con_so_PHUT():
    """
    Day la ly do lop nay ton tai. "Còn 2 bước" tra loi CON BAO XA;
    no khong tra loi CON KIP KHONG.
    """
    bo = BoNhacGio(gio_hen=H(14))
    s = bo.cap_nhat(H(13, 55), buoc_con_lai=2)
    assert s is not None and "phút" in s


def test_nhac_co_the_kem_so_chang_nhung_phut_la_chinh():
    bo = BoNhacGio(gio_hen=H(14))
    s = bo.cap_nhat(H(13, 57), buoc_con_lai=2)
    assert "phút" in s and "2 bước" in s


def test_khong_co_so_chang_thi_van_nhac_duoc():
    bo = BoNhacGio(gio_hen=H(14))
    s = bo.cap_nhat(H(13, 57))
    assert s is not None and "bước" not in s


def test_chua_toi_moc_nao_thi_im_lang():
    bo = BoNhacGio(gio_hen=H(14))
    assert bo.cap_nhat(H(13, 30)) is None


def test_qua_gio_hen_thi_bao_mot_lan_roi_thoi():
    """Bao mai thi thanh trach moc - dieu phai tranh tuyet doi."""
    bo = BoNhacGio(gio_hen=H(14))
    s = bo.cap_nhat(H(14, 3))
    assert s is not None and "quá giờ" in s
    assert bo.cap_nhat(H(14, 5)) is None


def test_qua_gio_hen_thi_khong_trach_moc():
    """
    ADHD thuong di kem nhay cam voi that bai. Mot cau trach moc se lam
    nguoi dung tranh mo app - nguoc hoan toan voi muc dich.
    """
    bo = BoNhacGio(gio_hen=H(14))
    s = bo.cap_nhat(H(14, 3)).lower()
    for xau in ("đáng lẽ", "lẽ ra", "tại sao", "lại trễ", "không nên"):
        assert xau not in s


def test_nhay_qua_nhieu_moc_mot_luc_khong_noi_don_dap():
    """
    Mat song mot luc roi co lai: khong duoc doc lien tiep bon cau nhac
    cua bon moc da qua.
    """
    bo = BoNhacGio(gio_hen=H(14))
    dau = bo.cap_nhat(H(13, 59))
    assert dau is not None
    assert bo.cap_nhat(H(13, 59)) is None


def test_moc_nhac_thua_dan_ve_cuoi():
    """Cang gan gio thi mot phut cang dang gia."""
    m = sorted(MOC_NHAC_PHUT, reverse=True)
    khoang = [m[i] - m[i + 1] for i in range(len(m) - 1)]
    assert khoang == sorted(khoang, reverse=True), m


def test_con_qua_lau_thi_khong_doc_so_phut_dem_nguoc():
    """
    "Còn 821 phút nữa" dung ve so hoc nhung vo dung ve thuc te.

    Qua mot nguong thi mot moc tren dong ho de nam hon han mot con so
    dem nguoc.
    """
    bay_gio = H(0, 17)
    kh = tinh(phut_di=1.0, gio_bay_gio=bay_gio, gio_hen=H(14))
    s = cau(kh, "Phòng 3.12", bay_gio, "Lớp học")
    assert "phút nữa" not in s
    assert "13 giờ" in s          # van phai noi moc phai di


def test_con_vua_phai_thi_VAN_doc_so_phut():
    """Duoi nguong thi con so dem nguoc van de nam hon gio dong ho."""
    bay_gio = H(13, 30)
    kh = tinh(phut_di=6.0, gio_bay_gio=bay_gio, gio_hen=H(14))
    assert "phút nữa" in cau(kh, "Phòng 3.12", bay_gio, "Lớp học")
