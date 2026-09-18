"""
Kiem chinh VONG LAP - `run_flowy.py`.

--------------------------------------------------------------------
VI SAO FILE NAY CAN TON TAI
--------------------------------------------------------------------

Cac bai test kia kiem tung module rieng. Nhung ba loi duoi day khong
nam trong module nao ca - chung nam o CHO GHEP giua cac module, va ca
ba deu lot qua 380 bai test truoc do:

    1. bam Ket thuc o mot phien khong co buoc nao thi khong gi xay ra
    2. net mat `thong_cam` dinh lai vinh vien sau mot lan phan tam
    3. xong viec ma khong hen gio thi net mat khong doi

Ca ba chi lo ra khi chay that dau-cuoi. Nen o day kiem chinh `Flowy`,
qua dung cua vao ma dien thoai dung: `buoc(PhoneUpdate)`.
"""

from __future__ import annotations

import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

from run_flowy import GIU_NET_MAT_S, Flowy               # noqa: E402
from wayfinding.adhd import cauhoi, dongvien, mach       # noqa: E402
from wayfinding.loi_chung.bridge import (                # noqa: E402
    LENH_BAT_DAU,
    LENH_KET_THUC,
    LENH_TAM_DUNG,
    LENH_TIEP_TUC,
    LENH_VIEC_MOI,
    LENH_XONG_BUOC,
    PhoneUpdate,
)

T = 1000.0


def moi(**kw) -> Flowy:
    """Mot app da du ba o y dinh va da bat dau phien."""
    app = Flowy(**kw)
    app.buoc(PhoneUpdate(t=T, voice="viết báo cáo"))
    app.buoc(PhoneUpdate(t=T + 1, voice="sau bữa tối"))
    app.buoc(PhoneUpdate(t=T + 2, voice="bàn học"))
    app.buoc(PhoneUpdate(t=T + 3, lenh=LENH_BAT_DAU))
    return app


# ================================================================
# Ket thuc mot phien khong co buoc nao
# ================================================================

def test_ket_thuc_phien_KHONG_BUOC_van_bao_xong():
    """
    Duong di thuong gap nhat: noi viec gi / khi nao / o dau, bat dau,
    lam, roi bam Ket thuc. Khong buoc nao ca.

    Truoc khi co `Phien.ket_thuc()`, nut nay im lang khong lam gi.
    """
    app = moi()
    tra = app.buoc(PhoneUpdate(t=T + 10, lenh=LENH_KET_THUC))
    assert tra.xong_phien is True
    assert tra.say is not None


def test_ket_thuc_bao_xong_DUNG_MOT_LAN():
    """
    Dien thoai ghi so thoi luong khi thay co nay. Bat hai lan la ghi
    hai ban ghi cho cung mot lan lam viec.
    """
    app = moi()
    assert app.buoc(PhoneUpdate(t=T + 10, lenh=LENH_KET_THUC)).xong_phien
    assert not app.buoc(PhoneUpdate(t=T + 11)).xong_phien
    assert not app.buoc(PhoneUpdate(t=T + 12, lenh=LENH_KET_THUC)).xong_phien


def test_ket_thuc_khi_con_buoc_chua_danh_dau():
    app = moi()
    app.phien.them_buoc("mở tệp lên")
    app.phien.them_buoc("viết một câu")
    assert app.buoc(PhoneUpdate(t=T + 10, lenh=LENH_KET_THUC)).xong_phien


def test_di_het_cac_buoc_cung_bao_xong():
    """Duong kia phai con nguyen."""
    app = moi()
    app.phien.them_buoc("mở tệp lên")
    tra = app.buoc(PhoneUpdate(t=T + 10, lenh=LENH_XONG_BUOC))
    assert tra.xong_phien is True


# ================================================================
# Ten viec gui ve cho dien thoai ghi so
# ================================================================

def test_ten_viec_duoc_gui_ve_khi_co_phien():
    """Dien thoai can ten nay de biet ghi so vao muc nao."""
    app = moi()
    assert app.buoc(PhoneUpdate(t=T + 4)).ten_viec == "viết báo cáo"


def test_chua_co_phien_thi_khong_co_ten_viec():
    assert Flowy().buoc(PhoneUpdate(t=T)).ten_viec is None


def test_ten_viec_giu_nguyen_dau_tieng_viet():
    """
    Mat dau o day la dien thoai ghi so vao mot muc KHAC, va lich su
    thoi luong tach lam doi ma khong ai thay.
    """
    app = Flowy()
    app.buoc(PhoneUpdate(t=T, voice="viết báo cáo cuối kỳ"))
    app.buoc(PhoneUpdate(t=T + 1, voice="sau bữa tối"))
    app.buoc(PhoneUpdate(t=T + 2, voice="bàn học"))
    app.buoc(PhoneUpdate(t=T + 3, lenh=LENH_BAT_DAU))
    assert app.buoc(PhoneUpdate(t=T + 4)).ten_viec == "viết báo cáo cuối kỳ"


# ================================================================
# Net mat
# ================================================================

def test_diu_net_mat_khi_vua_quay_lai_sau_phan_tam():
    app = moi()
    app.buoc(PhoneUpdate(t=T + 10, tren_man_hinh=False))
    tra = app.buoc(PhoneUpdate(t=T + 10 + mach.NGUONG_PHAN_TAM_S + 1))
    assert tra.ban == dongvien.TrangThai.THONG_CAM.value
    assert tra.say is not None


def test_net_mat_diu_KHONG_dinh_lai_vinh_vien():
    """
    Mot net mat thong cam dinh lai mai thi khong con nghia gi nua - no
    thanh net mat mac dinh, va luc that su can no thi khong ai thay
    khac biet.
    """
    app = moi()
    app.buoc(PhoneUpdate(t=T + 10, tren_man_hinh=False))
    quay_lai = T + 10 + mach.NGUONG_PHAN_TAM_S + 1
    assert app.buoc(PhoneUpdate(t=quay_lai)).ban == "thong_cam"

    sau = app.buoc(PhoneUpdate(t=quay_lai + GIU_NET_MAT_S + 1))
    assert sau.ban == "binh_thuong"


def test_net_mat_diu_GIU_du_lau_de_nhin_thay():
    """Go ra ngay goi tin sau la nguoi dung khong kip thay gi."""
    app = moi()
    app.buoc(PhoneUpdate(t=T + 10, tren_man_hinh=False))
    quay_lai = T + 10 + mach.NGUONG_PHAN_TAM_S + 1
    app.buoc(PhoneUpdate(t=quay_lai))
    giua = app.buoc(PhoneUpdate(t=quay_lai + GIU_NET_MAT_S / 2))
    assert giua.ban == "thong_cam"


def test_ket_lau_thi_diu_net_mat_va_KHONG_noi_gi():
    """
    Day la cach duy nhat app to ra rang no thay nguoi dung dang ket, ma
    van khong chu dong bat chuyen (NHAN_VAT_BRIEF muc 2.4).
    """
    app = moi()
    tra = app.buoc(PhoneUpdate(t=T + 4 + cauhoi.KET_LAU_GIAY))
    assert tra.ban == "thong_cam"
    assert tra.say is None
    assert tra.hoi is None


def test_van_dang_ket_thi_net_mat_KHONG_tu_go_ra():
    """Tinh hinh chua doi thi net mat khong duoc doi."""
    app = moi()
    t = T + 4 + cauhoi.KET_LAU_GIAY
    app.buoc(PhoneUpdate(t=t))
    assert app.buoc(PhoneUpdate(t=t + GIU_NET_MAT_S + 1)).ban == "thong_cam"


def test_xong_buoc_thi_het_ket_va_net_mat_tro_lai():
    """
    Xong mot buoc la het ket, nhung net mat khong lat lai ngay: no giu
    het han roi moi tro ve. Lat trong nua giay la mot cai nhap nhay o
    goc mat, dung thu ma ban mo ta nhan vat cam.
    """
    app = moi()
    app.phien.them_buoc("mở tệp lên")
    app.phien.them_buoc("viết một câu")
    t = T + 4 + cauhoi.KET_LAU_GIAY
    assert app.buoc(PhoneUpdate(t=t)).ban == "thong_cam"

    # vua xong buoc: het ket, nhung net mat con trong han
    assert app.buoc(PhoneUpdate(t=t + 1, lenh=LENH_XONG_BUOC)).ban == "thong_cam"

    # het han thi tro ve binh thuong
    assert app.buoc(PhoneUpdate(t=t + 1 + GIU_NET_MAT_S)).ban == "binh_thuong"


def test_xong_viec_KHONG_HEN_GIO_van_doi_net_mat_tich_cuc():
    """
    Phan lon phien khong hen gio. Neu chi doi net mat khi co gio hen thi
    da so lan lam xong deu khong duoc ghi nhan gi - va luc do "xong
    viec" voi "bo do" trong giong het nhau tren man hinh.
    """
    app = moi()
    tra = app.buoc(PhoneUpdate(t=T + 10, lenh=LENH_KET_THUC))
    assert tra.ban in ("vui", "tu_hao")


def test_bo_do_ket_KHONG_dam_len_net_mat_vua_xong():
    """Phan thuong bien mat sau nua giay thi khong con la phan thuong."""
    app = moi()
    t = T + 4 + cauhoi.KET_LAU_GIAY
    app.buoc(PhoneUpdate(t=t))                       # dang ket
    tra = app.buoc(PhoneUpdate(t=t + 1, lenh=LENH_KET_THUC))
    assert tra.ban in ("vui", "tu_hao")
    # va no o lai, khong bi bo do ket keo ve thong_cam
    assert app.buoc(PhoneUpdate(t=t + 2)).ban in ("vui", "tu_hao")


# ================================================================
# Nhip gui goi tin
# ================================================================

def test_dang_lam_thi_nhip_day_hon():
    app = moi()
    assert app.buoc(PhoneUpdate(t=T + 4)).nhip_ms == 500


def test_ra_khoi_app_thi_nhip_gian_ra():
    """Tiet kiem pin, khong phai giam do tre."""
    app = moi()
    assert app.buoc(PhoneUpdate(t=T + 4, tren_man_hinh=False)).nhip_ms == 2000


def test_chua_bat_dau_thi_nhip_gian_ra():
    assert Flowy().buoc(PhoneUpdate(t=T)).nhip_ms == 2000


# ================================================================
# Cau mo dau luc bam Bat dau
# ================================================================

def test_bam_bat_dau_thi_CO_CAU_MO_DAU():
    """
    `cau_mo_dau()` tung duoc viet ma khong ai goi - bam Bat dau xong app
    im lang, va cau chong mu thoi gian o muc 3.1 khong bao gio duoc noi.
    """
    app = Flowy()
    app.buoc(PhoneUpdate(t=T, voice="viết báo cáo"))
    app.buoc(PhoneUpdate(t=T + 1, voice="sau bữa tối"))
    app.buoc(PhoneUpdate(t=T + 2, voice="bàn học"))
    tra = app.buoc(PhoneUpdate(t=T + 3, lenh=LENH_BAT_DAU))
    assert tra.say is not None
    assert "viết báo cáo" in tra.say


def test_cau_mo_dau_CHI_MOT_LAN():
    """Bam Bat dau lan nua khi dang lam thi khong doc lai tu dau."""
    app = moi()
    assert app.buoc(PhoneUpdate(t=T + 4, lenh=LENH_BAT_DAU)).say is None


def test_chua_du_y_dinh_thi_bat_dau_KHONG_noi_gi():
    app = Flowy()
    app.buoc(PhoneUpdate(t=T, voice="viết báo cáo"))
    tra = app.buoc(PhoneUpdate(t=T + 1, lenh=LENH_BAT_DAU))
    assert app.phien is None
    assert tra.say is None


def test_cau_mo_dau_co_doi_chieu_khi_co_lich_su():
    """Lan truoc uoc 20, that 35 -> cau doi chieu phai dung dau."""
    app = Flowy()
    app.so_thoi_luong.ghi("viết báo cáo", that_phut=35.0, uoc_phut=20.0)
    app.buoc(PhoneUpdate(t=T, voice="viết báo cáo"))
    app.buoc(PhoneUpdate(t=T + 1, voice="sau bữa tối"))
    app.buoc(PhoneUpdate(t=T + 2, voice="bàn học"))
    tra = app.buoc(PhoneUpdate(t=T + 3, lenh=LENH_BAT_DAU))
    assert tra.say.startswith("Lần trước bạn ước 20 phút")


def test_ten_viec_ve_TRUOC_khi_bat_dau_de_dien_thoai_gui_lich_su():
    """
    Dien thoai can ten viec de gui lich su CUA DUNG VIEC DO len truoc
    khi bam Bat dau - neu khong, cau goi y thoi luong khong bao gio co.
    """
    app = Flowy()
    tra = app.buoc(PhoneUpdate(t=T, voice="viết báo cáo"))
    assert tra.ten_viec == "viết báo cáo"


def test_lich_su_gui_truoc_thi_cau_mo_dau_co_goi_y():
    app = Flowy()
    app.buoc(PhoneUpdate(t=T, voice="viết báo cáo"))
    app.buoc(PhoneUpdate(t=T + 1, voice="sau bữa tối"))
    # Dang ma bridge.py doc ra tu goi tin: dict, khong phai chuoi.
    ls = {"viết báo cáo": [{"uoc": None, "that": 30.0}]}
    app.buoc(PhoneUpdate(t=T + 2, voice="bàn học", lich_su=ls))
    tra = app.buoc(PhoneUpdate(t=T + 3, lenh=LENH_BAT_DAU, lich_su=ls))
    assert "30 phút" in tra.say


# ================================================================
# Giao dien v2: trang thai cho ba khoi co dinh
# ================================================================

def test_y_dinh_gom_duoc_gui_ve_de_hien():
    app = Flowy()
    app.buoc(PhoneUpdate(t=T, voice="viết báo cáo"))
    tra = app.buoc(PhoneUpdate(t=T + 1, voice="sau bữa tối"))
    assert tra.viec_gi == "viết báo cáo"
    assert tra.khi_nao == "sau bữa tối"
    assert tra.o_dau is None
    assert tra.trong_phien is False


def test_buoc_noi_TRUOC_khi_bat_dau_khong_bi_mat():
    app = Flowy()
    for i, c in enumerate(["viết báo cáo", "sau bữa tối", "bàn học",
                           "mở tệp lên"]):
        app.buoc(PhoneUpdate(t=T + i, voice=c))
    tra = app.buoc(PhoneUpdate(t=T + 5, lenh=LENH_BAT_DAU))
    assert tra.cac_buoc == ["mở tệp lên"]
    assert tra.trong_phien is True
    assert "Bước đầu: mở tệp lên" in tra.say


def test_bam_bat_dau_lan_hai_KHONG_mat_buoc():
    app = moi()
    app.phien.them_buoc("mở tệp lên")
    app.buoc(PhoneUpdate(t=T + 5, lenh=LENH_BAT_DAU))
    assert app.phien.buoc == ["mở tệp lên"]


def test_gio_hen_dat_tu_dien_thoai():
    app = moi()
    tra = app.buoc(PhoneUpdate(t=T + 5, gio_hen=14 * 60))
    assert tra.gio_hen == "14:00"
    assert app.bo_nhac is not None
    tra = app.buoc(PhoneUpdate(t=T + 6, gio_hen=-1))
    assert tra.gio_hen is None
    assert app.bo_nhac is None


def test_muc_nhac_doi_moc_cua_bo_nhac():
    app = moi(gio_hen=14 * 60)
    tra = app.buoc(PhoneUpdate(t=T + 5, muc_nhac="it"))
    assert tra.muc_nhac == "it"
    assert app.bo_nhac._moc == (5.0, 1.0)


def test_uoc_luong_duoc_ghi_vao_so_khi_xong():
    app = moi()
    app.buoc(PhoneUpdate(t=T + 5, uoc_phut=20))
    app.buoc(PhoneUpdate(t=T + 6, lenh=LENH_KET_THUC))
    lan = app.so_thoi_luong.to_json()["viết báo cáo"][-1]
    assert lan["uoc"] == 20.0


def test_tam_dung_GIU_trang_thai_qua_nhieu_goi_tin():
    app = moi()
    app.buoc(PhoneUpdate(t=T + 5, lenh=LENH_TAM_DUNG))
    tra = app.buoc(PhoneUpdate(t=T + 6))
    assert tra.tam_dung is True
    assert tra.nhip_ms == 2000          # khong con dang lam
    tra = app.buoc(PhoneUpdate(t=T + 20, lenh=LENH_TIEP_TUC))
    assert tra.tam_dung is False
    assert app._tong_tam_dung == 15.0


def test_viec_moi_xoa_y_dinh_va_bao_xong_lai_duoc():
    app = moi()
    assert app.buoc(PhoneUpdate(t=T + 5, lenh=LENH_KET_THUC)).xong_phien
    tra = app.buoc(PhoneUpdate(t=T + 6, lenh=LENH_VIEC_MOI))
    assert tra.viec_gi is None and app.phien is None
    for i, c in enumerate(["đọc sách", "tối nay", "phòng khách"]):
        app.buoc(PhoneUpdate(t=T + 10 + i, voice=c))
    app.buoc(PhoneUpdate(t=T + 20, lenh=LENH_BAT_DAU))
    assert app.buoc(PhoneUpdate(t=T + 21, lenh=LENH_KET_THUC)).xong_phien


def test_lam_lai_cung_viec_sau_khi_xong_van_bao_xong():
    """Ban truoc `_da_bao_xong` dinh True mai mai sau phien dau."""
    app = moi()
    assert app.buoc(PhoneUpdate(t=T + 5, lenh=LENH_KET_THUC)).xong_phien
    app.buoc(PhoneUpdate(t=T + 6, lenh=LENH_BAT_DAU))
    assert app.buoc(PhoneUpdate(t=T + 7, lenh=LENH_KET_THUC)).xong_phien
