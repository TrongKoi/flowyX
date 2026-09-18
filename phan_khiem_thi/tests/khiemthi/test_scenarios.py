"""
Kiem thu KICH BAN D (thiet bi man hinh cam ung) va KICH BAN E (so tan).

Hai kich ban nay deu dung lai loi da co, nen test o day tap trung vao
phan MOI: cach dien dat huong so voi moc so duoc, va luat loai thang may
khi so tan.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.loi_chung.floormap import load_map
from wayfinding.khiemthi.panel import (
    AT_MARKER_M, Button, PanelSession, PanelSpec, describe_layout,
    format_offset, guide_to, list_buttons, load_panels, nearest_button,
)
from wayfinding.loi_chung.routing import (
    build_evacuation_route, build_route, shortest_path, shortest_path_multi,
)

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "config" / "map_floor3.json"
PANELS = ROOT / "config" / "panels.json"


def demo_spec() -> PanelSpec:
    return PanelSpec(
        appliance="May in thu nghiem",
        marker_id="40",
        marker_size_m=0.06,
        buttons=[
            Button("Sao chep", 0.045, 0.085),
            Button("Quet", 0.115, 0.085),
            Button("Bat dau", 0.230, -0.010, note="Nut lon nhat"),
            Button("Huy", 0.160, -0.010, danger=True),
        ],
    )


# ================= KICH BAN D =================

# ------------------------- dien dat huong -------------------------

def test_huong_phai_va_len():
    text = format_offset(0.045, 0.085)
    assert "sang phai" in text and "len" in text


def test_huong_trai_va_xuong():
    text = format_offset(-0.03, -0.02)
    assert "sang trai" in text and "xuong" in text


def test_noi_ngang_truoc_doc_sau():
    """Giu thu tu co dinh giup nguoi dung quen nhanh."""
    text = format_offset(0.05, 0.03)
    assert text.index("phai") < text.index("len")


def test_lech_qua_nho_thi_noi_ngay_tai_ma():
    text = format_offset(0.002, -0.003)
    assert text == "ngay tai ma"


def test_chi_lech_mot_truc_thi_khong_noi_truc_kia():
    text = format_offset(0.05, 0.0)
    assert "sang phai" in text
    assert "len" not in text and "xuong" not in text


def test_lam_tron_khong_gia_vo_chinh_xac():
    """
    Nguoi dung khong the do chinh xac hon 0.5cm bang ngon tay. Noi
    "4 phay 37 xentimet" la gia vo chinh xac va lam nguoi nghe met.
    """
    text = format_offset(0.0437, 0.0)
    assert "37" not in text and "43" not in text


def test_so_tron_khong_co_phan_thap_phan():
    assert "4 xentimet" in format_offset(0.04, 0.0)


def test_nua_xentimet_doc_duoc():
    text = format_offset(0.045, 0.0)
    assert "phay" in text and "5" in text


def test_nguong_at_marker_hop_ly():
    assert format_offset(AT_MARKER_M * 0.5, 0.0) == "ngay tai ma"
    assert format_offset(AT_MARKER_M * 2, 0.0) != "ngay tai ma"


# ------------------------- huong dan tim nut -------------------------

def test_huong_dan_bat_dau_tu_ma():
    """Ma la moc so duoc - moi huong dan phai neo vao no."""
    text = guide_to(demo_spec(), "Sao chep")
    assert "ngon tay len ma" in text
    assert "Sao chep" in text


def test_khong_phan_biet_hoa_thuong():
    assert "Sao chep" in guide_to(demo_spec(), "sao chep")
    assert "Sao chep" in guide_to(demo_spec(), "SAO CHEP")


def test_go_thieu_van_tim_duoc():
    spec = PanelSpec("X", "1", 0.05, [Button("Mot mat hai mat", 0.1, 0.0)])
    assert "Mot mat hai mat" in guide_to(spec, "hai mat")


def test_nut_khong_ton_tai_thi_liet_ke_cac_nut_co():
    text = guide_to(demo_spec(), "Fax")
    assert "Khong co nut" in text
    assert "Sao chep" in text and "Quet" in text


def test_ghi_chu_cua_nut_duoc_doc_kem():
    assert "Nut lon nhat" in guide_to(demo_spec(), "Bat dau")


def test_canh_bao_nut_nguy_hiem():
    assert "can trong" in guide_to(demo_spec(), "Huy")


def test_canh_bao_khi_hai_nut_sat_nhau():
    spec = PanelSpec("X", "1", 0.05, [
        Button("A", 0.05, 0.0),
        Button("B", 0.06, 0.0),        # cach 1cm
    ])
    assert "sat ben canh" in guide_to(spec, "A")


def test_khong_canh_bao_khi_cac_nut_cach_xa():
    spec = PanelSpec("X", "1", 0.05, [
        Button("A", 0.02, 0.0),
        Button("B", 0.20, 0.0),
    ])
    assert "sat ben canh" not in guide_to(spec, "A")


# ------------------------- mo ta bang -------------------------

def test_mo_ta_bang_co_so_nut():
    text = describe_layout(demo_spec())
    assert "4 nut" in text and "May in thu nghiem" in text


def test_mo_ta_bang_dem_so_hang():
    text = describe_layout(demo_spec())
    assert "hang" in text


def test_mo_ta_bang_neu_ten_nut_nguy_hiem():
    assert "Huy" in describe_layout(demo_spec())


def test_liet_ke_nut_theo_thu_tu_tren_xuong():
    text = list_buttons(demo_spec())
    assert text.index("Sao chep") < text.index("Bat dau")


def test_nut_gan_nhat():
    btn, d = nearest_button(demo_spec(), 0.047, 0.083)
    assert btn.name == "Sao chep" and d < 0.01


# ------------------------- doc file mo ta -------------------------

def test_doc_file_panels_that():
    panels = load_panels(PANELS)
    assert len(panels) >= 3
    assert all(p.buttons for p in panels.values())


def test_moi_panel_tra_cuu_duoc_theo_ma():
    panels = load_panels(PANELS)
    for marker_id, spec in panels.items():
        assert spec.marker_id == marker_id


def test_tu_choi_bang_khong_co_nut(tmp_path):
    f = tmp_path / "p.json"
    f.write_text(json.dumps({"panels": [
        {"appliance": "X", "marker_id": "9", "buttons": []}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="khong co nut"):
        load_panels(f)


def test_tu_choi_hai_nut_trung_ten(tmp_path):
    f = tmp_path / "p.json"
    f.write_text(json.dumps({"panels": [{
        "appliance": "X", "marker_id": "9", "buttons": [
            {"name": "Bat dau", "x": 0.01, "y": 0.0},
            {"name": "bat dau", "x": 0.05, "y": 0.0}]}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="trung ten"):
        load_panels(f)


def test_tu_choi_hai_nut_cung_toa_do(tmp_path):
    """Hai nut o dung mot cho la loi do dac, khong phai thiet ke."""
    f = tmp_path / "p.json"
    f.write_text(json.dumps({"panels": [{
        "appliance": "X", "marker_id": "9", "buttons": [
            {"name": "A", "x": 0.05, "y": 0.02},
            {"name": "B", "x": 0.05, "y": 0.02}]}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="cung mot toa do"):
        load_panels(f)


# ------------------------- phien lam viec -------------------------

def test_nhan_ra_thiet_bi_khi_thay_ma():
    s = PanelSession(panels=load_panels(PANELS))
    text = s.on_marker("40")
    assert text and "May in" in text


def test_khong_gioi_thieu_lai_cung_thiet_bi():
    """Doc lai moi khung hinh se lam nguoi dung tat he thong di."""
    s = PanelSession(panels=load_panels(PANELS))
    assert s.on_marker("40") is not None
    for _ in range(5):
        assert s.on_marker("40") is None


def test_ma_la_thi_bo_qua():
    s = PanelSession(panels=load_panels(PANELS))
    assert s.on_marker("999") is None
    assert s.current is None


def test_hoi_truoc_khi_thay_ma_thi_bao_chua_nhan_ra():
    s = PanelSession(panels=load_panels(PANELS))
    assert "Chua nhan ra thiet bi" in s.ask("Bat dau")


def test_doi_thiet_bi_thi_gioi_thieu_lai():
    s = PanelSession(panels=load_panels(PANELS))
    s.on_marker("40")
    text = s.on_marker("41")
    assert text and "ca phe" in text.lower()


def test_reset_quen_thiet_bi():
    s = PanelSession(panels=load_panels(PANELS))
    s.on_marker("40")
    s.reset()
    assert s.current is None
    assert s.on_marker("40") is not None


# ================= KICH BAN E =================

def test_ban_do_co_loi_thoat_hiem():
    fm = load_map(MAP)
    assert fm.exits, "Ban do phai khai bao loi thoat hiem"
    for ex in fm.exits:
        assert ex in fm.nodes


def test_so_tan_chon_loi_thoat_gan_nhat():
    fm = load_map(MAP)
    tu_tay = build_evacuation_route(fm, "A")
    tu_dong = build_evacuation_route(fm, "R16")
    assert tu_tay.destination.id == "EX1"
    assert tu_dong.destination.id == "EX2"


def test_so_tan_ngan_hon_di_toi_loi_thoat_xa():
    fm = load_map(MAP)
    gan = build_evacuation_route(fm, "R16")
    xa = build_route(fm, "R16", "EX1")
    assert gan.total_length < xa.total_length


def test_so_tan_giu_duoc_canh_bao_nguy_hiem():
    """Bac hut truoc cua thoat hiem van phai duoc canh bao."""
    fm = load_map(MAP)
    route = build_evacuation_route(fm, "A")
    assert any(leg.hazard for leg in route.legs)


def test_loai_canh_thang_may_khi_so_tan(tmp_path):
    """
    Khi bao chay thang may bi khoa tu dong. Di toi do roi ket lai la
    tinh huong nguy hiem that su, nen phai loai han khoi tuyen.
    """
    m = {
        "markers": {"1": {"x": 0.0, "y": 0.0, "theta": 0}},
        "nodes": [
            {"id": "P", "x": 0.0, "y": 0.0, "name": "Phong"},
            {"id": "L", "x": 2.0, "y": 0.0, "name": "Thang may"},
            {"id": "S", "x": 20.0, "y": 0.0, "name": "Cau thang bo"},
            {"id": "E", "x": 21.0, "y": 0.0, "name": "Loi thoat"},
        ],
        "edges": [
            {"from": "P", "to": "L"},
            {"from": "L", "to": "E", "is_lift": True},   # duong ngan, qua thang may
            {"from": "P", "to": "S"},
            {"from": "S", "to": "E"},                    # duong dai, cau thang bo
        ],
        "exits": ["E"],
    }
    f = tmp_path / "m.json"
    f.write_text(json.dumps(m), encoding="utf-8")
    fm = load_map(f)

    # Binh thuong: duoc di thang may, duong ngan
    thuong = build_route(fm, "P", "E")
    thuong_ids = [thuong.legs[0].frm.id] + [leg.to.id for leg in thuong.legs]
    assert "L" in thuong_ids

    # So tan: phai vong qua cau thang bo
    so_tan = build_evacuation_route(fm, "P", avoid_lifts=True)
    ids = [so_tan.legs[0].frm.id] + [leg.to.id for leg in so_tan.legs]
    assert "L" not in ids, "Tuyen so tan van di qua thang may"
    assert "S" in ids


def test_cho_phep_thang_may_khi_tat_luat():
    m = {
        "markers": {"1": {"x": 0.0, "y": 0.0, "theta": 0}},
        "nodes": [
            {"id": "P", "x": 0.0, "y": 0.0, "name": "Phong"},
            {"id": "L", "x": 2.0, "y": 0.0, "name": "Thang may"},
            {"id": "E", "x": 3.0, "y": 0.0, "name": "Loi thoat"},
        ],
        "edges": [{"from": "P", "to": "L"},
                  {"from": "L", "to": "E", "is_lift": True}],
        "exits": ["E"],
    }
    f = Path(__file__).parent / "_tmp_lift.json"
    f.write_text(json.dumps(m), encoding="utf-8")
    try:
        fm = load_map(f)
        assert build_evacuation_route(fm, "P", avoid_lifts=True) is None
        assert build_evacuation_route(fm, "P", avoid_lifts=False) is not None
    finally:
        f.unlink()


def test_khong_co_loi_thoat_thi_tra_ve_none():
    fm = load_map(MAP)
    fm.exits = []
    assert build_evacuation_route(fm, "A") is None


def test_dang_dung_ngay_loi_thoat():
    fm = load_map(MAP)
    assert build_evacuation_route(fm, "EX1") is None   # khong con chang nao


def test_tu_choi_loi_thoat_khong_co_that(tmp_path):
    m = {
        "markers": {"1": {"x": 0.0, "y": 0.0, "theta": 0}},
        "nodes": [{"id": "P", "x": 0.0, "y": 0.0, "name": "Phong"}],
        "edges": [],
        "exits": ["KHONG_TON_TAI"],
    }
    f = tmp_path / "m.json"
    f.write_text(json.dumps(m), encoding="utf-8")
    with pytest.raises(ValueError, match="Loi thoat hiem"):
        load_map(f)


# ------------------------- dinh tuyen nhieu dich -------------------------

def test_multi_goal_chon_dich_gan_nhat():
    fm = load_map(MAP)
    path = shortest_path_multi(fm, "R16", ["EX1", "EX2"])
    assert path[-1] == "EX2"


def test_multi_goal_khong_co_dich_nao_ton_tai():
    fm = load_map(MAP)
    assert shortest_path_multi(fm, "A", ["KHONG_CO"]) is None


# ================= KICH BAN B - tim cho ngoi hot-desk =================

from wayfinding.khiemthi.desk import (                                    # noqa: E402
    Desk, DeskSession, describe_desk, load_desks,
)

DESKS = ROOT / "config" / "desks.json"


def _session(person="Nam", day="2026-09-21"):
    return DeskSession(desk_map=load_desks(DESKS), person=person, day=day)


def test_doc_file_ban_that():
    dm = load_desks(DESKS)
    assert len(dm.desks) >= 6
    assert len(dm.by_marker) == len(dm.desks)


def test_tu_choi_hai_ban_dung_chung_ma(tmp_path):
    """Hai ban cung ma thi he thong se xac nhan nham ban - phai bat som."""
    f = tmp_path / "d.json"
    f.write_text(json.dumps({"desks": [
        {"desk_id": "A", "marker_id": "50"},
        {"desk_id": "B", "marker_id": "50"}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="hai ban"):
        load_desks(f)


def test_tu_choi_dat_ban_khong_ton_tai(tmp_path):
    f = tmp_path / "d.json"
    f.write_text(json.dumps({
        "desks": [{"desk_id": "A", "marker_id": "50"}],
        "bookings": [{"day": "2026-09-21",
                      "assignments": {"Nam": "KHONG_CO"}}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="khong co trong danh sach"):
        load_desks(f)


def test_tu_choi_hai_nguoi_cung_mot_ban(tmp_path):
    """Loi dat cho - hai nguoi se cung den mot cho."""
    f = tmp_path / "d.json"
    f.write_text(json.dumps({
        "desks": [{"desk_id": "A", "marker_id": "50"}],
        "bookings": [{"day": "2026-09-21",
                      "assignments": {"Nam": "A", "Lan": "A"}}]}),
        encoding="utf-8")
    with pytest.raises(ValueError, match="bi dat cho ca"):
        load_desks(f)


def test_bat_dau_bao_ban_hom_nay():
    s = _session()
    text = s.start()
    assert "D-02" in text and "cua so phia dong" in text


def test_bat_dau_kem_moc_so_duoc():
    """Khong co moc so duoc thi nguoi dung khong tu tim den noi duoc."""
    s = _session()
    assert "tuong kinh" in s.start()


def test_khong_co_dat_cho_thi_noi_that():
    s = _session(person="KhongCoTenNay")
    text = s.start()
    assert "Khong tim thay dat cho" in text


def test_ngay_khong_co_lich_thi_noi_that():
    s = _session(day="2030-01-01")
    assert "Khong tim thay dat cho" in s.start()


def test_xac_nhan_khi_cham_dung_ban():
    """
    Day la phan quan trong nhat: nguoi khiem thi khong the liec mot cai
    de biet minh co ngoi nham ban khong.
    """
    s = _session()
    s.start()
    text = s.on_marker("51")            # D-02
    assert "Dung roi" in text and "D-02" in text
    assert s.confirmed


def test_canh_bao_khi_cham_ban_nguoi_khac():
    s = _session()
    s.start()
    text = s.on_marker("53")            # D-04, cua Lan
    assert "khong phai ban cua ban" in text
    assert "Lan" in text                # noi ro ban nay cua ai
    assert "D-02" in text               # va nhac lai ban dung


def test_khong_lap_lai_xac_nhan():
    s = _session()
    s.start()
    assert s.on_marker("51") is not None
    for _ in range(5):
        assert s.on_marker("51") is None


def test_khong_lap_lai_canh_bao_cung_mot_ban():
    s = _session()
    s.start()
    assert s.on_marker("53") is not None
    assert s.on_marker("53") is None


def test_ma_khong_thuoc_ban_nao_thi_bo_qua():
    """Ma dan tuong dung de chi duong - khong duoc nham la ban."""
    s = _session()
    s.start()
    assert s.on_marker("10") is None    # ma chi duong tren tuong


def test_cham_ban_truoc_khi_hoi_van_mo_ta_duoc():
    s = _session()
    text = s.on_marker("51")
    assert text and "D-02" in text


def test_nhac_lai_ban_hom_nay():
    s = _session()
    s.start()
    assert "D-02" in s.repeat()


def test_ban_doi_theo_ngay():
    """Hot-desk nghia la moi ngay mot cho - phai lay dung ngay."""
    thu_hai = _session(day="2026-09-21").start()
    thu_ba = _session(day="2026-09-22").start()
    assert "D-02" in thu_hai
    assert "D-05" in thu_ba


def test_ban_co_dinh_van_hoat_dong():
    s = _session(person="Minh", day="2026-09-22")
    assert "D-06" in s.start()


def test_ghi_chu_cua_ban_duoc_doc_kem():
    s = _session(person="Nam", day="2026-09-22")   # D-05, khu yen tinh
    assert "yen lang" in s.start().lower()


def test_reset_quen_ban_da_chon():
    s = _session()
    s.start()
    s.on_marker("51")
    s.reset()
    assert s.target is None and not s.confirmed


def test_mo_ta_ban_gon_gang():
    d = Desk(desk_id="D-09", marker_id="59", zone="khu bep",
             landmark="Ban canh tu lanh", note="Co o dien duoi ban")
    text = describe_desk(d)
    assert "D-09" in text and "khu bep" in text and "tu lanh" in text


# ================= NHIEU TANG =================
#
# So tan that gan nhu luon phai XUONG TANG. Truoc khi co phan nay, kich
# ban E chi tim duoc loi thoat tren cung mot tang - tuc la vo dung o moi
# toa nha cao hon mot tang.

from wayfinding.loi_chung.guidance import GuidanceEngine                   # noqa: E402
from wayfinding.loi_chung.localizer import Confidence, Fix                 # noqa: E402
from wayfinding.loi_chung.geometry import Pose2D                           # noqa: E402


def toa_nha_hai_tang() -> dict:
    """Tang 3 co phong, tang tret co loi thoat. Noi bang cau thang va thang may."""
    return {
        "markers": {
            "10": {"x": 0.0, "y": 0.9, "theta": -90},
            "11": {"x": 12.0, "y": 0.9, "theta": -90},
            "12": {"x": 12.0, "y": -19.1, "theta": 90},
        },
        "nodes": [
            {"id": "P", "x": 0.0, "y": 0.0, "floor": 3,
             "name": "Phong 3.12", "landmark": "Bien chu noi ben phai cua"},
            {"id": "S3", "x": 12.0, "y": 0.0, "floor": 3,
             "name": "Chan cau thang tang 3", "landmark": "Tay vin kim loai"},
            {"id": "L3", "x": 6.0, "y": 0.0, "floor": 3,
             "name": "Thang may tang 3", "landmark": "Nut bam ngang nguc"},
            {"id": "S0", "x": 12.0, "y": -20.0, "floor": 0,
             "name": "Chan cau thang tang tret", "landmark": "Tay vin kim loai"},
            {"id": "L0", "x": 6.0, "y": -20.0, "floor": 0,
             "name": "Thang may tang tret", "landmark": "Nut bam ngang nguc"},
            {"id": "EX", "x": 16.0, "y": -20.0, "floor": 0,
             "name": "Loi thoat ra duong", "landmark": "Cua day thanh ngang"},
        ],
        "edges": [
            {"from": "P", "to": "L3"},
            {"from": "L3", "to": "S3"},
            {"from": "S3", "to": "S0", "is_stairs": True,
             "hazard": "Cau thang bo, bam tay vin ben phai"},
            {"from": "L3", "to": "L0", "is_lift": True},
            {"from": "S0", "to": "EX"},
            {"from": "L0", "to": "EX"},
        ],
        "exits": ["EX"],
        "ground_floor": 0,
    }


def _load_tmp(tmp_path, data):
    p = tmp_path / "m.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return load_map(p)


def test_ban_do_nhan_biet_nhieu_tang(tmp_path):
    fm = _load_tmp(tmp_path, toa_nha_hai_tang())
    assert fm.multi_floor
    assert load_map(MAP).multi_floor is False       # ban do cu van mot tang


def test_ban_do_mot_tang_van_chay_binh_thuong():
    """Them truong 'floor' khong duoc lam hong ban do da co."""
    fm = load_map(MAP)
    assert all(n.floor == 0 for n in fm.nodes.values())
    assert build_route(fm, "A", "R12") is not None


def test_so_tan_xuong_duoc_tang_tret(tmp_path):
    """Truoc khi co phan nay, kich ban E vo dung o toa nha nhieu tang."""
    fm = _load_tmp(tmp_path, toa_nha_hai_tang())
    route = build_evacuation_route(fm, "P")
    assert route is not None
    assert route.destination.id == "EX"
    assert route.destination.floor == fm.ground_floor
    assert route.crosses_floors


def test_so_tan_di_cau_thang_khong_di_thang_may(tmp_path):
    """Bao chay thi thang may khoa - di toi do roi ket lai la nguy hiem that."""
    fm = _load_tmp(tmp_path, toa_nha_hai_tang())
    route = build_evacuation_route(fm, "P", avoid_lifts=True)
    ids = [route.legs[0].frm.id] + [l.to.id for l in route.legs]
    assert "S0" in ids
    assert "L0" not in ids


def test_chang_xuong_tang_bao_dung_so_tang(tmp_path):
    fm = _load_tmp(tmp_path, toa_nha_hai_tang())
    route = build_evacuation_route(fm, "P")
    xuong = [l for l in route.legs if l.floor_change]
    assert xuong and xuong[0].floor_change == -3


def test_uu_tien_loi_thoat_o_tang_tret(tmp_path):
    """Loi thoat o tang tren van la loi thoat, nhung ra mat dat moi an toan."""
    data = toa_nha_hai_tang()
    data["nodes"].append({"id": "EX3", "x": 14.0, "y": 0.0, "floor": 3,
                          "name": "Loi thoat tang 3", "landmark": "Cua day"})
    data["edges"].append({"from": "S3", "to": "EX3"})
    data["exits"] = ["EX", "EX3"]
    fm = _load_tmp(tmp_path, data)
    route = build_evacuation_route(fm, "P")
    assert route.destination.id == "EX"        # khong phai EX3 du gan hon


def test_khong_xuong_duoc_thi_chap_nhan_loi_thoat_tang_tren(tmp_path):
    """Cau thang bi chan thi van phai co duong ra, con hon khong co gi."""
    data = toa_nha_hai_tang()
    data["nodes"].append({"id": "EX3", "x": 14.0, "y": 0.0, "floor": 3,
                          "name": "Loi thoat tang 3", "landmark": "Cua day"})
    data["edges"] = [e for e in data["edges"]
                     if not (e["from"] == "S3" and e["to"] == "S0")]
    data["edges"].append({"from": "S3", "to": "EX3"})
    data["exits"] = ["EX", "EX3"]
    fm = _load_tmp(tmp_path, data)
    route = build_evacuation_route(fm, "P", avoid_lifts=True)
    assert route is not None and route.destination.id == "EX3"


# ------------------------- chi dan khi doi tang -------------------------

def _fix_at(x, y, conf=Confidence.HIGH):
    return Fix(pose=Pose2D(x, y, 0.0), confidence=conf, drift_estimate=0.1,
               distance_since_fix=2.0, last_anchor="10",
               last_anchor_source="ocr")


def test_chi_dan_bao_khi_phai_xuong_tang(tmp_path):
    """
    Doi tang la diem quyet dinh quan trong nhat: buoc nham mot bac cau
    thang nguy hiem hon han re nham mot nga re.
    """
    fm = _load_tmp(tmp_path, toa_nha_hai_tang())
    route = build_evacuation_route(fm, "P")
    guide = GuidanceEngine(route)

    said = []
    for leg_i, leg in enumerate(route.legs):
        guide.leg_index = leg_i
        guide._done_thresholds.clear()
        ins = guide._on_route(_fix_at(leg.to.x, leg.to.y))
        if ins:
            said.append(ins.text)

    text = " ".join(said)
    assert "xuống 3 tầng" in text
    assert "cầu thang bộ" in text


def test_chi_dan_phan_biet_thang_may_va_cau_thang(tmp_path):
    fm = _load_tmp(tmp_path, toa_nha_hai_tang())
    route = build_evacuation_route(fm, "P", avoid_lifts=False)
    guide = GuidanceEngine(route)
    said = []
    for leg_i, leg in enumerate(route.legs):
        guide.leg_index = leg_i
        guide._done_thresholds.clear()
        ins = guide._on_route(_fix_at(leg.to.x, leg.to.y))
        if ins:
            said.append(ins.text)
    text = " ".join(said)
    assert "thang máy" in text or "cầu thang" in text


def test_chi_dan_doi_tang_kem_canh_bao_nguy_hiem(tmp_path):
    fm = _load_tmp(tmp_path, toa_nha_hai_tang())
    route = build_evacuation_route(fm, "P")
    guide = GuidanceEngine(route)
    stair_leg = next(i for i, l in enumerate(route.legs) if l.floor_change)
    guide.leg_index = stair_leg
    ins = guide._on_route(_fix_at(route.legs[stair_leg].to.x,
                                  route.legs[stair_leg].to.y))
    assert ins and "tay vin" in ins.text.lower()


def test_chi_dan_doi_tang_la_khan_cap_khi_den_noi(tmp_path):
    """
    Chi dan phat theo ba nguong 10 -> 5 -> 2 met khi nguoi dung tien lai
    gan. Chi cau CUOI CUNG (den noi roi) moi la khan cap va cat loi.
    """
    fm = _load_tmp(tmp_path, toa_nha_hai_tang())
    route = build_evacuation_route(fm, "P")
    guide = GuidanceEngine(route)
    stair_leg = next(i for i, l in enumerate(route.legs) if l.floor_change)
    guide.leg_index = stair_leg
    leg = route.legs[stair_leg]

    ins = None
    for _ in range(3):                       # di qua ca ba nguong
        got = guide._on_route(_fix_at(leg.to.x, leg.to.y))
        if got:
            ins = got

    assert ins is not None
    assert "ngay bây giờ" in ins.text
    assert ins.urgent and ins.haptic == "double_repeat"
