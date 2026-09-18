"""
Kiem thu lop moc neo bang BIEN CHU san co.

Lop nay sinh ra tu mot rang buoc thuc te: mentor khong cho dan ma giay
len tuong RMIT. Ma nga re va cau thang thi khong co so phong de doc -
dung nhung cho ma chi sai la nguy hiem nhat.

Loi giai: theo quy dinh phong chay, nga re va cau thang LUON co bien
thoat hiem. Do la bien toa nha da co san, khong phai dan them gi.

Cai gia phai tra, va cung la trong tam cua file test nay: moi bien
thoat hiem deu ghi GIONG HET nhau. Doc duoc chu "LOI THOAT" khong cho
biet dang dung truoc tam nao - dung loi nham lan tri giac. Neo nham
sang dau kia toa nha nguy hiem hon nhieu so voi bo qua mot lan neo
dung, nen khi khong du chac he thong phai TU CHOI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.loi_chung.anchors import RoomSignReader, sign_texts
from wayfinding.loi_chung.floormap import SignAnchor, load_map
from wayfinding.loi_chung.geometry import Pose2D
from wayfinding.loi_chung.localizer import Localizer
from wayfinding.loi_chung.signtext import edit_distance, find_matches, matches, normalize

W, H = 640, 480
BOX = [[100, 100], [300, 100], [300, 160], [100, 160]]


class FakeOCR:
    """Gia lap easyocr: luon tra ve dung mot doan chu."""

    def __init__(self, text: str, conf: float = 0.95):
        self.text = text
        self.conf = conf

    def readtext(self, frame):
        return [(BOX, self.text, self.conf)]


def _frame():
    return np.zeros((H, W, 3), np.uint8)


# ------------------------------------------------------------------
# Chuan hoa chu
# ------------------------------------------------------------------

def test_bo_dau_tieng_viet():
    assert normalize("Lối thoát hiểm") == "LOITHOATHIEM"
    assert normalize("LỐI THOÁT") == "LOITHOAT"


def test_chu_d_gach_ngang():
    """Chu D gach ngang la ky tu rieng, khong phai to hop dau."""
    assert normalize("Đường thoát nạn") == "DUONGTHOATNAN"
    assert normalize("đi") == "DI"


def test_bo_khoang_trang_va_dau_cau():
    """OCR hay them hoac nuot khoang trang, nen bo han cho chac."""
    assert normalize("Phòng  họp 3.12") == normalize("Phòng họp 3.12")
    assert normalize("LOI - THOAT") == normalize("LOI THOAT")


def test_chuoi_rong():
    assert normalize("") == ""
    assert not matches("", "LỐI THOÁT")
    assert not matches("LỐI THOÁT", "")


# ------------------------------------------------------------------
# So khop co dung sai
# ------------------------------------------------------------------

def test_khop_du_mat_dau():
    """May OCR doc bien tieng Viet thuong rung mat dau."""
    assert matches("LOI THOAT", "LỐI THOÁT")


def test_khop_khi_ocr_nham_vai_ky_tu():
    assert matches("L0I THOAT", "LỐI THOÁT")      # nham O voi so 0
    assert matches("LOI THOATT", "LỐI THOÁT")     # thua mot ky tu


def test_khop_khi_ocr_dinh_them_chu_ben_canh():
    """Bien thuong nam canh chu khac tren cung mot tam."""
    assert matches("EXIT - LỐI THOÁT", "LỐI THOÁT")


def test_khong_khop_chu_khac_han():
    assert not matches("THANG MAY", "LỐI THOÁT")
    assert not matches("LOI VAO", "LỐI THOÁT")


def test_chuoi_ngan_phai_khop_tuyet_doi():
    """
    "A3" va "A4" chi cach nhau mot ky tu. Cho dung sai o chuoi ngan la
    bien mot tam bien thanh tam khac.
    """
    assert matches("A3", "A3")
    assert not matches("A4", "A3")
    assert not matches("B3", "A3")


def test_edit_distance_dung_som():
    """Ham chay tren moi ket qua OCR moi khung hinh, phai thoat nhanh."""
    assert edit_distance("abc", "abc", cap=2) == 0
    assert edit_distance("abc", "abd", cap=2) == 1
    assert edit_distance("abc", "xyzuvw", cap=2) > 2


def test_find_matches_tra_ve_moi_ung_vien():
    """Diem mau chot: nhieu tam bien co the ghi giong het nhau."""
    signs = {
        "exit-dong": "LỐI THOÁT",
        "exit-tay": "LỐI THOÁT",
        "tang": "TẦNG 3",
    }
    assert set(find_matches("LOI THOAT", signs)) == {"exit-dong", "exit-tay"}
    assert find_matches("TANG 3", signs) == ["tang"]
    assert find_matches("QUẢNG CÁO", signs) == []


# ------------------------------------------------------------------
# Doc ban do
# ------------------------------------------------------------------

def _write_map(tmp_path, signs: dict) -> str:
    data = {
        "floor": "test",
        "markers": {},
        "rooms": {"3.12": {"x": 24.0, "y": 12.9, "theta": -90}},
        "signs": signs,
        "nodes": [
            {"id": "A", "x": 0.0, "y": 0.0, "name": "Thang may"},
            {"id": "B", "x": 18.5, "y": 0.0, "name": "Nga re dong"},
            {"id": "C", "x": 24.0, "y": 12.0, "name": "Phong 3.12"},
        ],
        "edges": [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"},
        ],
    }
    p = tmp_path / "map.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def test_ban_do_cu_khong_co_signs_van_doc_duoc(tmp_path):
    """
    Khong duoc lam vo cac ban do da soan truoc do.

    Co y dung ban do tu dung trong test chu KHONG dung
    config/map_floor3.json: file do gio da co muc signs, nen no khong
    con kiem tra duoc dieu ta muon kiem tra nua.
    """
    data = json.loads(Path(_write_map(tmp_path, {})).read_text(encoding="utf-8"))
    del data["signs"]
    p = tmp_path / "cu.json"
    p.write_text(json.dumps(data), encoding="utf-8")

    fm = load_map(str(p))
    assert fm.signs == {}
    assert len(fm.rooms) > 0


def test_doc_duoc_muc_signs(tmp_path):
    fm = load_map(_write_map(tmp_path, {
        "exit-b": {"x": 18.5, "y": 0.9, "theta": -90, "text": "LỐI THOÁT"},
    }))
    assert set(fm.signs) == {"exit-b"}
    s = fm.signs["exit-b"]
    assert s.text == "LỐI THOÁT"
    assert (s.x, s.y) == (18.5, 0.9)


def test_bien_thieu_truong_text_bi_bao_loi(tmp_path):
    """Thieu chu thi khong doi chieu duoc, phai bao ngay luc nap ban do."""
    with pytest.raises(ValueError, match="text"):
        load_map(_write_map(tmp_path, {
            "exit-b": {"x": 18.5, "y": 0.9, "theta": -90},
        }))


# ------------------------------------------------------------------
# Doc bien tu khung hinh
# ------------------------------------------------------------------

SIGNS = {
    "exit-dong": "LỐI THOÁT",
    "exit-tay": "LỐI THOÁT",
    "tang-3": "TẦNG 3",
}


def _reader(text: str):
    return RoomSignReader(
        known_rooms={"3.12"},
        every_n_frames=1,
        reader=FakeOCR(text),
        known_signs=SIGNS,
    )


def test_doc_duoc_bien_chu():
    got = _reader("LỐI THOÁT").detect(_frame())
    assert len(got) == 1
    assert got[0].source == "sign"
    assert got[0].key == "LOITHOAT"


def test_key_la_chu_da_chuan_hoa():
    """
    SightingFilter dem "thay cung mot key N khung lien tiep". Neu key
    la chu THO thi OCR doc lech mot lan la bo dem ve 0, va gan nhu
    khong bao gio du 3 lan lien.
    """
    a = _reader("LỐI THOÁT").detect(_frame())[0]
    b = _reader("LOI THOAT").detect(_frame())[0]
    assert a.key == b.key


def test_so_phong_duoc_uu_tien_hon_bien_chu():
    """So phong duy nhat trong tang nen dang tin hon han."""
    got = _reader("3.12").detect(_frame())
    assert len(got) == 1
    assert got[0].source == "ocr"


def test_bo_qua_chu_khong_co_trong_ban_do():
    assert _reader("QUẢNG CÁO").detect(_frame()) == []


def test_bien_chu_kem_tin_hon_so_phong():
    """Chu trung nhau nen phai xep sau khi chon moc tot nhat."""
    sign = _reader("LỐI THOÁT").detect(_frame())[0]
    room = _reader("3.12").detect(_frame())[0]
    assert sign.quality < room.quality


def test_khong_khai_bao_signs_thi_khong_doc_bien_chu():
    r = RoomSignReader(known_rooms={"3.12"}, every_n_frames=1,
                       reader=FakeOCR("LỐI THOÁT"))
    assert r.detect(_frame()) == []


# ------------------------------------------------------------------
# Go nhap nhang - phan quan trong nhat
# ------------------------------------------------------------------

def _localizer(tmp_path, signs: dict) -> Localizer:
    return Localizer(load_map(_write_map(tmp_path, signs)))


def test_bien_duy_nhat_thi_dung_ngay(tmp_path):
    loc = _localizer(tmp_path, {
        "tang-3": {"x": 1.0, "y": 0.9, "theta": -90, "text": "TẦNG 3"},
    })
    assert loc._resolve_sign("TANG3") is not None


def test_bien_trung_chu_bi_tu_choi_khi_chua_dinh_vi(tmp_path):
    """
    Chua biet dang o dau thi khong co can cu chon tam nao. Doan bua co
    50% sai, va mot lan neo sai lam hong ca tuyen duong.
    """
    loc = _localizer(tmp_path, {
        "exit-dong": {"x": 18.5, "y": 0.9, "theta": -90, "text": "LỐI THOÁT"},
        "exit-tay": {"x": 40.0, "y": 0.9, "theta": -90, "text": "LỐI THOÁT"},
    })
    assert loc._last_xy is None
    assert loc._resolve_sign("LOITHOAT") is None
    assert loc.ambiguous_signs == 1


def test_bien_trung_chu_chon_duoc_khi_da_biet_vi_tri(tmp_path):
    loc = _localizer(tmp_path, {
        "exit-dong": {"x": 18.5, "y": 0.9, "theta": -90, "text": "LỐI THOÁT"},
        "exit-tay": {"x": 40.0, "y": 0.9, "theta": -90, "text": "LỐI THOÁT"},
    })
    loc._last_xy = (18.0, 0.0)          # dang dung gan bien phia dong
    pose = loc._resolve_sign("LOITHOAT")
    assert pose is not None
    assert pose.x == pytest.approx(18.5)


def test_tu_choi_khi_hai_bien_gan_bang_nhau(tmp_path):
    """
    Dung giua hai bien trung chu thi khong tam nao gan hon han. Chon
    bua la 50% sai - phai tu choi.
    """
    loc = _localizer(tmp_path, {
        "exit-a": {"x": 10.0, "y": 0.0, "theta": -90, "text": "LỐI THOÁT"},
        "exit-b": {"x": 14.0, "y": 0.0, "theta": -90, "text": "LỐI THOÁT"},
    })
    loc._last_xy = (12.0, 0.0)          # cach deu ca hai
    assert loc._resolve_sign("LOITHOAT") is None
    assert loc.ambiguous_signs == 1


def test_tu_choi_khi_ung_vien_gan_nhat_van_qua_xa(tmp_path):
    """
    Camera doc duoc bien o cu ly 1-2m. Neu tam gan nhat cach uoc luong
    hien tai 30m thi hoac uoc luong sai, hoac day la tam khac chua co
    trong ban do. Ca hai truong hop deu khong duoc neo.
    """
    loc = _localizer(tmp_path, {
        "exit-a": {"x": 40.0, "y": 0.0, "theta": -90, "text": "LỐI THOÁT"},
        "exit-b": {"x": 60.0, "y": 0.0, "theta": -90, "text": "LỐI THOÁT"},
    })
    loc._last_xy = (0.0, 0.0)
    assert loc._resolve_sign("LOITHOAT") is None


def test_chu_khong_co_trong_ban_do_tra_ve_none(tmp_path):
    loc = _localizer(tmp_path, {
        "exit-a": {"x": 10.0, "y": 0.0, "theta": -90, "text": "LỐI THOÁT"},
    })
    loc._last_xy = (10.0, 0.0)
    assert loc._resolve_sign("THANGMAY") is None


def test_ban_do_khong_co_signs_tra_ve_none(tmp_path):
    loc = _localizer(tmp_path, {})
    loc._last_xy = (0.0, 0.0)
    assert loc._resolve_sign("LOITHOAT") is None


def test_reset_xoa_bo_dem_nhap_nhang(tmp_path):
    loc = _localizer(tmp_path, {
        "exit-a": {"x": 10.0, "y": 0.0, "theta": -90, "text": "LỐI THOÁT"},
        "exit-b": {"x": 14.0, "y": 0.0, "theta": -90, "text": "LỐI THOÁT"},
    })
    loc._last_xy = (12.0, 0.0)
    loc._resolve_sign("LOITHOAT")
    assert loc.ambiguous_signs == 1
    loc.reset()
    assert loc.ambiguous_signs == 0


# ------------------------------------------------------------------
# Lop bien chu co THUC SU duoc noi vao he thong khong
#
# Nhom test nay ton tai vi mot loi that: lop bien chu tung duoc them vao
# kem 28 test day du, nhung KHONG runner nao truyen known_signs - nen no
# la ma chet suot mot thoi gian. Test don vi deu xanh, ma tinh nang thi
# khong bao gio chay duoc.
#
# Test don vi kiem tra "code co dung khong". Nhom nay kiem tra "code co
# duoc GOI khong" - hai cau hoi khac nhau.
# ------------------------------------------------------------------

def test_sign_texts_lay_dung_chu_tu_ban_do(tmp_path):
    fm = load_map(_write_map(tmp_path, {
        "exit-a": {"x": 10.0, "y": 0.0, "theta": -90, "text": "LỐI THOÁT"},
        "tang": {"x": 1.0, "y": 0.0, "theta": -90, "text": "TẦNG 3"},
    }))
    assert sign_texts(fm) == {"exit-a": "LỐI THOÁT", "tang": "TẦNG 3"}


def test_sign_texts_an_toan_voi_ban_do_khong_co_signs(tmp_path):
    data = json.loads(Path(_write_map(tmp_path, {})).read_text(encoding="utf-8"))
    del data["signs"]
    p = tmp_path / "cu.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    assert sign_texts(load_map(str(p))) == {}


def test_ban_do_mau_co_bien_de_doc():
    """Ban do mau phai co san vai tam bien, neu khong thi demo khong chay."""
    fm = load_map("config/map_floor3.json")
    assert len(sign_texts(fm)) >= 1


@pytest.mark.parametrize("runner", ["run_live.py", "run_bridge.py"])
def test_runner_co_truyen_known_signs(runner):
    """
    Doc thang ma nguon cua runner.

    Kieu test nay hoi la, nhung no bat dung loai loi da xay ra: tinh
    nang co day du test ma khong runner nao goi toi.
    """
    src = Path(__file__).resolve().parents[2] / runner
    text = src.read_text(encoding="utf-8")
    assert "known_signs=sign_texts(fm)" in text, (
        f"{runner} khong truyen known_signs - lop bien chu se khong bao gio "
        f"duoc doc, va nga re se mat moc neo"
    )


# ------------------------------------------------------------------
# Khoang cach toi bien: mo hinh camera lo kim
#
# Truoc day khoang cach duoc DOAN bang mot cong thuc kinh nghiem voi
# hang so 0.35 khong co co so vat ly, dua tren BE RONG chu - ma be rong
# thi phu thuoc so ky tu, nen "P.312" va "PHONG HOP LON" cho ra hai ket
# qua khac han du cung khoang cach.
#
# Gio la mot phep DO, dung dung cach NaviLens do khoang cach toi ma cua
# ho. Tieu cu thi ARCore/ARKit cho san luc chay.
# ------------------------------------------------------------------

from wayfinding.loi_chung.anchors import sign_distance, sign_heights   # noqa: E402


def _box(h_px: float, w_px: float = 200.0):
    return [[100, 100], [100 + w_px, 100], [100 + w_px, 100 + h_px], [100, 100 + h_px]]


def test_cang_xa_thi_chu_cang_nho():
    gan = sign_distance(_box(120), 640, text_h=0.09, focal_px=1400)
    xa = sign_distance(_box(40), 640, text_h=0.09, focal_px=1400)
    assert xa > gan


def test_khoang_cach_dung_cong_thuc_lo_kim():
    """d = f x H / h. Chu cao 0,09m, tieu cu 1400, chu chiem 126 diem anh."""
    assert sign_distance(_box(126), 640, text_h=0.09,
                         focal_px=1400) == pytest.approx(1.0, abs=0.01)


def test_be_rong_khong_anh_huong_khi_co_chieu_cao():
    """
    Diem mau chot. Bien "P.312" va bien "PHONG HOP LON" co be rong khac
    han nhau nhung chu cao bang nhau - cung khoang cach thi phai ra
    cung ket qua.
    """
    ngan = sign_distance(_box(126, w_px=90), 640, text_h=0.09, focal_px=1400)
    dai = sign_distance(_box(126, w_px=520), 640, text_h=0.09, focal_px=1400)
    assert ngan == pytest.approx(dai)


def test_thieu_tieu_cu_thi_quay_ve_cong_thuc_cu():
    """Ban do cu va ban mo phong khong co tieu cu, van phai chay duoc."""
    assert sign_distance(_box(126), 640) > 0


def test_thieu_chieu_cao_chu_thi_quay_ve_cong_thuc_cu():
    assert sign_distance(_box(126), 640, focal_px=1400) > 0


def test_chu_qua_nho_khong_lam_no():
    assert sign_distance(_box(0.5), 640, text_h=0.09, focal_px=1400) > 0


def test_ket_qua_bi_chan_trong_khoang_hop_ly():
    """OCR doc nham mot vet ban nho xiu khong duoc bien thanh 500 met."""
    assert sign_distance(_box(2), 640, text_h=0.09, focal_px=1400) <= 8.0


def test_sign_heights_chi_lay_tam_co_khai_bao(tmp_path):
    fm = load_map(_write_map(tmp_path, {
        "co": {"x": 1.0, "y": 0.0, "theta": 90, "text": "LỐI THOÁT", "text_h": 0.09},
        "khong": {"x": 5.0, "y": 0.0, "theta": 90, "text": "TẦNG 3"},
    }))
    assert sign_heights(fm) == {"co": 0.09}


def test_reader_dung_chieu_cao_khi_co():
    """Co chieu cao thi khoang cach phai khac han luc khong co."""
    r = RoomSignReader(known_rooms=set(), every_n_frames=1,
                       reader=FakeOCR("LỐI THOÁT"),
                       known_signs={"e": "LỐI THOÁT"},
                       sign_heights={"e": 0.09})
    r.focal_px = 1400.0
    co = r.detect(_frame())[0].distance

    r2 = RoomSignReader(known_rooms=set(), every_n_frames=1,
                        reader=FakeOCR("LỐI THOÁT"),
                        known_signs={"e": "LỐI THOÁT"})
    khong = r2.detect(_frame())[0].distance
    assert co != pytest.approx(khong)


def test_bridge_doc_duoc_tieu_cu():
    from wayfinding.loi_chung.bridge import parse_update
    upd = parse_update({"pose": {"x": 0.0, "y": 0.0, "theta": 0.0},
                        "intrinsics": {"fx": 1400.0, "fy": 1410.0}})
    assert upd.focal_px == pytest.approx(1410.0)


def test_bridge_khong_co_tieu_cu_thi_la_none():
    from wayfinding.loi_chung.bridge import parse_update
    assert parse_update({"pose": {"x": 0.0, "y": 0.0, "theta": 0.0}}).focal_px is None
