"""
CANH GAC HOP DONG JSON giua laptop va dien thoai.

--------------------------------------------------------------------
VI SAO BAI TEST NAY CAN TON TAI
--------------------------------------------------------------------

Hai ben duoc viet bang hai ngon ngu, trong hai thu muc, va khong co
trinh bien dich nao noi chung. Doi `nhip_ms` thanh `nhipMs` ben Python
la mot thao tac an toan tuyet doi theo moi bo test hien co - va no lam
dien thoai roi ve nhip mac dinh, im lang, mai mai.

Do dung la loai loi da tung lot qua o `run_bridge.py` (xem
`test_cau_truc_nhanh.py`): khong test nao chay chuong trinh do, nen mot
dong import chet nam yen cho toi luc nguoi dung go lenh chay that.

Nen file nay khoa TEN TRUONG, khong khoa gia tri. No la ban hop dong
duoc viet duoi dang co the chay.

--------------------------------------------------------------------
PHIA KIA CUA HOP DONG
--------------------------------------------------------------------

Ben Kotlin doc dung nhung ten nay o:

    android/app/src/main/java/vn/adc2026/wayfinding/Payload.kt

Sua danh sach o day thi PHAI sua ca ben do. Doi lai, bai test nay bat
duoc nua kia cua loi: no khong the biet Kotlin doc gi, nhung no bao cho
nguoi sua biet rang co mot ben kia.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GOC))

from wayfinding.loi_chung.bridge import (      # noqa: E402
    LENH_BAT_DAU,
    LENH_HOP_LE,
    LENH_KET_THUC,
    LENH_TAM_DUNG,
    LENH_TIEP_TUC,
    LENH_XONG_BUOC,
    BridgeReply,
    PhoneUpdate,
    parse_update,
)

# Truong dien thoai GUI LEN. Kotlin sinh chung trong `Payload.buildUpdate`.
TRUONG_GUI_LEN = (
    "t", "tren_man_hinh", "cham_nhan_vat", "voice", "lenh", "noi_dung",
    "battery", "thermal", "lich_su",
    "gio_hen", "uoc_phut", "muc_nhac",
)

# Truong laptop TRA VE. Kotlin doc chung trong `Payload.parseReply`.
TRUONG_TRA_VE = (
    "say", "haptic", "am", "ban", "tu_the", "hoi", "listen",
    "con_lai_giay", "tong_giay", "nhip_ms", "xong_phien", "ten_viec",
    "viec_gi", "khi_nao", "o_dau", "cac_buoc", "chi_so_buoc",
    "trong_phien", "tam_dung", "da_lam_giay", "gio_hen", "uoc_phut",
    "goi_y_phut", "muc_nhac",
)

# Nhung thu KHONG BAO GIO duoc di qua cau noi. Xem bang o dau
# `bridge.py`, va hai bai test canh gac trong `test_cau_truc_nhanh.py`.
CAM_MANG = (
    "nhat_ky", "ghi_chu", "the_nao", "cam_xuc",
    "loi_nhac", "ten_thuoc", "thuoc", "lieu", "trieu_chung",
)


# ================================================================
# Chieu len: dien thoai -> laptop
# ================================================================

@pytest.mark.parametrize("ten", TRUONG_GUI_LEN)
def test_truong_gui_len_duoc_doc(ten: str):
    """Moi ten trong hop dong phai co cho nhan o `PhoneUpdate`."""
    assert hasattr(PhoneUpdate(), ten), ten


def test_goi_tin_day_du_doc_duoc_het():
    """Chay that `parse_update` tren mot goi tin nhu Kotlin se gui."""
    upd = parse_update({
        "t": 1234.5,
        "tren_man_hinh": False,
        "cham_nhan_vat": True,
        "voice": "sau bữa tối",
        "lenh": LENH_BAT_DAU,
        "noi_dung": "viết báo cáo",
        "battery": 55.0,
        "thermal": 31.5,
        "lich_su": {"viết báo cáo": [{"uoc": 20.0, "that": 35.0}]},
    })
    assert upd.t == 1234.5
    assert upd.tren_man_hinh is False
    assert upd.cham_nhan_vat is True
    assert upd.voice == "sau bữa tối"
    assert upd.lenh == LENH_BAT_DAU
    assert upd.noi_dung == "viết báo cáo"
    assert upd.lich_su is not None


def test_goi_tin_rong_van_doc_duoc():
    """
    Mot goi tin loi khong duoc phep dung ca phien lam viec cua nguoi
    dung. Moi truong deu co gia tri mac dinh.
    """
    upd = parse_update({})
    assert upd.tren_man_hinh is True
    assert upd.cham_nhan_vat is False
    assert upd.voice is None
    assert upd.lenh is None


def test_truong_hong_thi_bo_qua_chu_khong_no():
    upd = parse_update({
        "t": "khong phai so",
        "tren_man_hinh": "khong phai bool",
        "lenh": "lenh khong co that",
        "voice": 12345,
    })
    assert upd.t is None
    assert upd.tren_man_hinh is True     # giu mac dinh
    assert upd.lenh is None
    assert upd.voice is None


@pytest.mark.parametrize("lenh", [LENH_BAT_DAU, LENH_XONG_BUOC,
                                  LENH_TAM_DUNG, LENH_TIEP_TUC,
                                  LENH_KET_THUC])
def test_moi_lenh_deu_hop_le(lenh: str):
    """Kotlin co hang so cho tung lenh nay - xem `Payload.LENH_*`."""
    assert lenh in LENH_HOP_LE
    assert parse_update({"lenh": lenh}).lenh == lenh


# ================================================================
# Chieu ve: laptop -> dien thoai
# ================================================================

@pytest.mark.parametrize("ten", TRUONG_TRA_VE)
def test_truong_tra_ve_co_trong_json(ten: str):
    """Moi ten trong hop dong phai co mat o `to_json()`."""
    assert ten in BridgeReply().to_json(), ten


def test_khong_co_truong_thua_trong_json():
    """
    Chieu nguoc lai cung phai khoa: them mot truong ma quen sua ben
    Kotlin thi truong do khong bao gio duoc doc, va khong ai biet.
    """
    thua = set(BridgeReply().to_json()) - set(TRUONG_TRA_VE)
    assert not thua, f"truong moi chua khai bao o hop dong: {thua}"


def test_json_tra_ve_serialise_duoc():
    """
    `json.dumps` phai chay - mot gia tri khong serialise duoc se lam
    server tra loi 500 va dien thoai mat ket noi ma khong biet vi sao.
    """
    tra = BridgeReply(say="Xong việc rồi.", hoi="Bạn định làm gì?",
                      ten_viec="viết báo cáo", xong_phien=True,
                      con_lai_giay=90.0, tong_giay=1800.0)
    lai = json.loads(json.dumps(tra.to_json(), ensure_ascii=False))
    assert lai["say"] == "Xong việc rồi."
    assert lai["ten_viec"] == "viết báo cáo"
    assert lai["xong_phien"] is True


def test_mac_dinh_an_toan():
    """Goi tin thieu truong phai cho dien thoai hanh vi vo hai."""
    d = BridgeReply().to_json()
    assert d["say"] is None
    assert d["hoi"] is None
    assert d["listen"] is False
    assert d["xong_phien"] is False
    assert d["ban"] == "binh_thuong"
    assert d["tu_the"] == 0
    assert d["nhip_ms"] == 500


def test_dong_ho_lam_tron_mot_chu_so():
    """
    Lam tron o day chu khong o Kotlin: mot cho lam tron thi chi co mot
    cho sai duoc.
    """
    d = BridgeReply(con_lai_giay=90.456, tong_giay=1800.999).to_json()
    assert d["con_lai_giay"] == 90.5
    assert d["tong_giay"] == 1801.0


# ================================================================
# Ranh gioi du lieu
# ================================================================

@pytest.mark.parametrize("cam", CAM_MANG)
def test_hop_dong_khong_mang_du_lieu_ca_nhan(cam: str):
    """
    Bang o dau `bridge.py` liet ke thu khong bao gio duoc len duong
    truyen. Bai test nay bat luc co ai them mot truong nhu vay.

    `lich_su` la ngoai le CO KIEM SOAT va da nam trong hop dong: chi
    lich su cua dung mot cong viec dang lam, gui di roi thoi.
    """
    for ten in TRUONG_GUI_LEN + TRUONG_TRA_VE:
        assert cam not in ten, f"truong `{ten}` mang du lieu bi cam"


def test_reply_khong_co_truong_nao_ngoai_hop_dong():
    """Kiem ca tren dataclass, khong chi tren `to_json()`."""
    truong = set(BridgeReply().__dataclass_fields__)
    assert truong == set(TRUONG_TRA_VE), truong ^ set(TRUONG_TRA_VE)


def test_update_khong_co_truong_nao_ngoai_hop_dong():
    truong = set(PhoneUpdate().__dataclass_fields__)
    assert truong == set(TRUONG_GUI_LEN), truong ^ set(TRUONG_GUI_LEN)


# ================================================================
# O y dinh con thieu: HIEN, nhung khong DOC LEN
# ================================================================

def test_o_con_thieu_duoc_gui_ve_de_hien():
    """
    Mo app ra ma man hinh trong tron thi nguoi dung khong biet go gi.
    Nen cau hoi cho o dang thieu duoc gui ve ngay tu goi tin dau.
    """
    sys.path.insert(0, str(GOC))
    from run_flowy import Flowy                      # noqa: E402
    from wayfinding.adhd import phien                # noqa: E402

    app = Flowy()
    tra = app.buoc(PhoneUpdate(t=0.0))
    assert tra.hoi == phien.CAU_HOI[phien.ThieuO.VIEC_GI]


def test_o_con_thieu_KHONG_bat_micro():
    """
    Day la duong ranh cua NHAN_VAT_BRIEF muc 2.4: mot dong chu tren man
    hinh la thu dong; mot cau doc len la app bat chuyen.

    `listen` tat nghia la dien thoai chi HIEN cau do. Xem
    `MainActivity.nhan()` - no doc `hoi` len chi khi `listen` bat.
    """
    sys.path.insert(0, str(GOC))
    from run_flowy import Flowy                      # noqa: E402

    tra = Flowy().buoc(PhoneUpdate(t=0.0))
    assert tra.hoi is not None
    assert tra.listen is False


def test_cau_hoi_doi_theo_o_dang_thieu():
    sys.path.insert(0, str(GOC))
    from run_flowy import Flowy                      # noqa: E402
    from wayfinding.adhd import phien                # noqa: E402

    app = Flowy()
    app.buoc(PhoneUpdate(t=0.0, voice="viết báo cáo"))
    tra = app.buoc(PhoneUpdate(t=1.0))
    assert tra.hoi == phien.CAU_HOI[phien.ThieuO.KHI_NAO]

    app.buoc(PhoneUpdate(t=2.0, voice="sau bữa tối"))
    tra = app.buoc(PhoneUpdate(t=3.0))
    assert tra.hoi == phien.CAU_HOI[phien.ThieuO.O_DAU]


def test_cu_cham_VAN_bat_micro():
    """Cu cham la loi moi de app len tieng - do khong duoc mat di."""
    sys.path.insert(0, str(GOC))
    from run_flowy import Flowy                      # noqa: E402

    tra = Flowy().buoc(PhoneUpdate(t=0.0, cham_nhan_vat=True))
    assert tra.hoi is not None
    assert tra.listen is True


# ================================================================
# Truong them cho giao dien v2
# ================================================================

def test_truong_v2_doc_duoc():
    upd = parse_update({"gio_hen": 840, "uoc_phut": 25, "muc_nhac": "it"})
    assert upd.gio_hen == 840.0
    assert upd.uoc_phut == 25.0
    assert upd.muc_nhac == "it"


def test_gio_hen_am_la_bo_gio_hen():
    assert parse_update({"gio_hen": -1}).gio_hen == -1.0


@pytest.mark.parametrize("hong", [
    {"gio_hen": 1440}, {"gio_hen": True}, {"gio_hen": "14:00"},
    {"uoc_phut": 0}, {"uoc_phut": -5}, {"uoc_phut": False},
    {"muc_nhac": "rat_nhieu"},
])
def test_truong_v2_hong_thi_bo_qua(hong):
    upd = parse_update(hong)
    assert upd.gio_hen is None and upd.uoc_phut is None
    assert upd.muc_nhac is None


def test_viec_moi_la_lenh_hop_le():
    from wayfinding.loi_chung.bridge import LENH_VIEC_MOI
    assert parse_update({"lenh": LENH_VIEC_MOI}).lenh == LENH_VIEC_MOI
