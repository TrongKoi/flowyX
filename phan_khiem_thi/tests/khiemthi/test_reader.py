"""
Kiem thu KICH BAN C - doc bien, tai lieu, bang trang.

Trong tam: thu tu doc va co che on dinh. Hai cho nay sai thi he thong
doc ra mot mo chu lung tung, hoac doc lai lien tuc moi khi nguoi dung
nhuc nhich camera - ca hai deu lam he thong khong dung duoc.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wayfinding.khiemthi.reader import (
    CONF_DOUBTFUL, DocumentReader, ReadState, TextBlock, chunk_lines,
    describe_confidence, group_into_lines, reading_order, split_columns,
)

W = 1280


def blk(text, x0, y0, x1, y1, conf=0.9):
    """Mot o van ban, dinh dang giong easyocr tra ve."""
    return ([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], text, conf)


def blocks(*items):
    return [TextBlock.from_ocr(i) for i in items]


# ------------------------- gom dong -------------------------

def test_gom_cac_o_cung_dong():
    bs = blocks(
        blk("Phong", 100, 100, 200, 140),
        blk("hop", 210, 102, 280, 138),
        blk("3.12", 290, 100, 360, 140),
    )
    lines = group_into_lines(bs)
    assert len(lines) == 1
    assert [b.text for b in lines[0]] == ["Phong", "hop", "3.12"]


def test_tach_dong_khac_nhau():
    bs = blocks(
        blk("Dong mot", 100, 100, 300, 140),
        blk("Dong hai", 100, 200, 300, 240),
    )
    assert len(group_into_lines(bs)) == 2


def test_xep_trai_sang_phai_du_dau_vao_lon_xon():
    """OCR tra ve khong theo thu tu nao - phai tu xep lai."""
    bs = blocks(
        blk("ba", 300, 100, 360, 140),
        blk("mot", 100, 100, 160, 140),
        blk("hai", 200, 100, 260, 140),
    )
    lines = group_into_lines(bs)
    assert [b.text for b in lines[0]] == ["mot", "hai", "ba"]


def test_xep_tren_xuong_duoi():
    bs = blocks(
        blk("duoi", 100, 300, 200, 340),
        blk("tren", 100, 100, 200, 140),
        blk("giua", 100, 200, 200, 240),
    )
    assert reading_order(bs, W) == ["tren", "giua", "duoi"]


def test_chu_hoa_thuong_van_cung_mot_dong():
    """Mep tren khac nhau nhung tam gan nhau - phai coi la cung dong."""
    bs = blocks(
        blk("HOP", 100, 96, 180, 144),      # chu hoa, cao hon
        blk("luc", 190, 106, 250, 138),     # chu thuong, thap hon
    )
    assert len(group_into_lines(bs)) == 1


# ------------------------- bo cuc nhieu cot -------------------------

def test_nhan_biet_hai_cot():
    """
    Doc ngang qua hai cot thi cau chu tron vao nhau va vo nghia.
    Phai doc het cot trai roi moi sang cot phai.
    """
    bs = []
    for i in range(4):
        y = 100 + i * 60
        bs.append(blk(f"trai{i}", 60, y, 300, y + 40))
        bs.append(blk(f"phai{i}", 800, y, 1040, y + 40))
    order = reading_order(blocks(*bs), W)
    assert order == ["trai0", "trai1", "trai2", "trai3",
                     "phai0", "phai1", "phai2", "phai3"]


def test_mot_cot_khong_bi_tach_nham():
    bs = []
    for i in range(4):
        y = 100 + i * 60
        bs.append(blk(f"dong{i} noi dung binh thuong", 60, y, 900, y + 40))
    lines = group_into_lines(blocks(*bs))
    assert len(split_columns(lines, W)) == 1


def test_qua_it_dong_thi_khong_ket_luan_cot():
    bs = blocks(
        blk("trai", 60, 100, 300, 140),
        blk("phai", 800, 100, 1040, 140),
    )
    lines = group_into_lines(bs)
    assert len(split_columns(lines, W)) == 1


# ------------------------- chia doan -------------------------

def test_chia_doan_theo_do_dai():
    lines = [f"dong so {i} co mot it noi dung de dai ra" for i in range(12)]
    chunks = chunk_lines(lines, max_chars=100)
    assert len(chunks) > 1
    assert all(len(c) < 260 for c in chunks)


def test_van_ban_ngan_chi_mot_doan():
    assert len(chunk_lines(["Phong hop 3.12"], max_chars=180)) == 1


def test_khong_mat_chu_khi_chia_doan():
    lines = [f"dong{i}" for i in range(20)]
    joined = " ".join(chunk_lines(lines, max_chars=50))
    for ln in lines:
        assert ln in joined


# ------------------------- do tin cay -------------------------

def test_canh_bao_khi_chu_qua_mo():
    bs = blocks(blk("mo qua", 100, 100, 300, 140, conf=0.2),
                blk("cung mo", 100, 200, 300, 240, conf=0.25))
    warning, mean = describe_confidence(bs)
    assert warning is not None and "khong ro" in warning
    assert mean < CONF_DOUBTFUL


def test_khong_canh_bao_khi_chu_ro():
    bs = blocks(blk("ro rang", 100, 100, 300, 140, conf=0.95))
    warning, mean = describe_confidence(bs)
    assert warning is None and mean > 0.9


def test_canh_bao_nhe_khi_mot_phan_khong_chac():
    bs = blocks(
        blk("ro", 100, 100, 300, 140, conf=0.95),
        blk("ro nua", 100, 200, 300, 240, conf=0.92),
        blk("mo", 100, 300, 300, 340, conf=0.30),
    )
    warning, _ = describe_confidence(bs)
    assert warning is not None and "khong chac" in warning


# ------------------------- co che on dinh -------------------------

def test_khong_doc_ngay_khung_hinh_dau():
    """
    Doc ngay khi vua thay chu se lam he thong doc lai lien tuc moi khi
    nguoi dung nhuc nhich camera.
    """
    r = DocumentReader(stable_frames=3)
    res = r.observe([blk("Phong hop 3.12", 100, 100, 400, 150)], W)
    assert res.say is None
    assert res.state is ReadState.SETTLING


def test_doc_sau_khi_du_khung_hinh_on_dinh():
    r = DocumentReader(stable_frames=3)
    items = [blk("Phong hop 3.12", 100, 100, 400, 150)]
    assert r.observe(items, W).say is None
    assert r.observe(items, W).say is None
    res = r.observe(items, W)
    assert res.say is not None and "3.12" in res.say
    assert res.state is ReadState.READING


def test_khong_doc_lai_cung_mot_noi_dung():
    r = DocumentReader(stable_frames=2)
    items = [blk("Phong hop 3.12", 100, 100, 400, 150)]
    r.observe(items, W)
    assert r.observe(items, W).say is not None      # lan doc dau
    for _ in range(5):
        assert r.observe(items, W).say is None      # khong doc lai


def test_van_ban_doi_thi_doc_lai():
    r = DocumentReader(stable_frames=2)
    a = [blk("Van ban mot", 100, 100, 400, 150)]
    b = [blk("Van ban hai", 100, 100, 400, 150)]
    r.observe(a, W)
    assert r.observe(a, W).say is not None
    r.observe(b, W)
    res = r.observe(b, W)
    assert res.say is not None and "hai" in res.say


def test_bo_dem_on_dinh_reset_khi_hinh_doi():
    """Camera rung lam chu nhay lien tuc - khong duoc doc bua."""
    r = DocumentReader(stable_frames=3)
    a = [blk("mot", 100, 100, 400, 150)]
    b = [blk("hai", 100, 100, 400, 150)]
    assert r.observe(a, W).say is None
    assert r.observe(b, W).say is None
    assert r.observe(a, W).say is None
    assert r.observe(b, W).say is None


def test_khong_thay_chu_thi_ve_trang_thai_cho():
    r = DocumentReader(stable_frames=2)
    items = [blk("Xin chao", 100, 100, 400, 150)]
    r.observe(items, W)
    r.observe(items, W)
    res = r.observe([], W)
    assert res.state is ReadState.IDLE and res.say is None


# ------------------------- dieu huong -------------------------

def _reader_with_chunks():
    r = DocumentReader(stable_frames=1, max_chars=40)
    items = [blk(f"dong so {i} noi dung", 100, 100 + i * 60, 600, 140 + i * 60)
             for i in range(8)]
    r.observe(items, W)
    return r


def test_di_chuyen_qua_lai_giua_cac_doan():
    r = _reader_with_chunks()
    assert r.total() > 1
    first = r.index
    nxt = r.next_chunk()
    assert r.index == first + 1 and nxt.say
    prv = r.prev_chunk()
    assert r.index == first and prv.say


def test_bao_khi_het_van_ban():
    r = _reader_with_chunks()
    for _ in range(50):
        res = r.next_chunk()
    assert "het van ban" in res.say.lower()


def test_bao_khi_dang_o_doan_dau():
    r = _reader_with_chunks()
    res = r.prev_chunk()
    assert "doan dau" in res.say.lower()


def test_doc_lai_doan_hien_tai():
    r = _reader_with_chunks()
    r.next_chunk()
    a = r.repeat().say
    b = r.repeat().say
    assert a == b


def test_dieu_huong_khi_chua_co_van_ban():
    r = DocumentReader()
    assert "Chua doc duoc" in r.next_chunk().say
    assert "Chua doc duoc" in r.repeat().say


def test_reset_quen_van_ban_cu():
    r = _reader_with_chunks()
    r.reset()
    assert r.chunks == [] and r.state is ReadState.IDLE


# ------------------------------------------------------------------
# Chiu duoc RUNG TAY
#
# Run Parkinson o tan so 4-6 Hz, chu yeu o tay va chan, xuat hien o
# khoang 70-75% nguoi benh. Camera deo nguc bi anh huong it hon tay,
# nhung van du de mot so khung hinh bi nhoe.
#
# Nhoe lam OCR doc lech vai ky tu. Neu co che on dinh doi cac khung
# hinh LIEN TIEP giong het nhau thi chi mot khung hinh nhoe cung dua
# bo dem ve 0 - va he thong KHONG BAO GIO doc duoc cho nguoi run tay.
# ------------------------------------------------------------------

def _sign(text):
    return [blk(text, 100, 100, 500, 150)]


def test_doc_duoc_du_co_khung_hinh_nhoe_xen_ke():
    """Khung hinh nhoe xen ke khong duoc chan viec doc."""
    r = DocumentReader(stable_frames=3, window=8)
    good = _sign("Phong hop 3.12")
    blurry = _sign("Ph0ng h0p 3.l2")        # OCR doc lech vi nhoe

    spoken = []
    for frame in [good, blurry, good, good, blurry, good]:
        res = r.observe(frame, W)
        if res.say:
            spoken.append(res.say)

    assert spoken, "Nguoi run tay khong bao gio doc duoc"
    assert "3.12" in spoken[0]
    assert len(spoken) == 1, "Doc lai nhieu lan cung mot noi dung"


def test_khung_hinh_nhoe_khong_dua_bo_dem_ve_khong():
    """Day chinh la loi cu: mot khung hinh nhoe lam mat het tien do."""
    r = DocumentReader(stable_frames=3, window=8)
    good = _sign("Bien so phong 3.14")
    blurry = _sign("Bien s0 ph0ng 3.l4")

    r.observe(good, W)
    r.observe(good, W)
    r.observe(blurry, W)                     # nhoe giua chung
    res = r.observe(good, W)                 # da du 3 ban tot trong cua so
    assert res.say is not None


def test_nhieu_qua_nang_thi_van_khong_doc_bua():
    """
    Chiu nhieu KHONG duoc bien thanh doc bua. Neu moi khung hinh mot
    khac thi khong co ban nao dat da so - phai im lang.
    """
    r = DocumentReader(stable_frames=3, window=8)
    res = None
    for i in range(8):
        res = r.observe(_sign(f"noi dung khac nhau {i}"), W)
    assert res.say is None
    assert res.state is ReadState.SETTLING


def test_van_chuyen_nhanh_sang_van_ban_moi():
    """
    Chiu nhieu khong duoc lam cham viec chuyen sang van ban moi: khi
    camera that su quay sang cho khac, cac khung hinh moi nhat quan
    voi nhau nen phai nhan ngay.
    """
    r = DocumentReader(stable_frames=3, window=8)
    a = _sign("Van ban A")
    b = _sign("Van ban B")

    for _ in range(4):
        r.observe(a, W)
    assert r.chunks and "A" in r.chunks[0]

    res = None
    for _ in range(3):                       # dung bang stable_frames
        res = r.observe(b, W)
    assert res.say is not None and "B" in res.say


def test_cua_so_lon_hon_thi_chiu_nhieu_tot_hon():
    """Cua so rong hon chiu duoc ty le khung hinh nhoe cao hon."""
    pattern = ["good", "bad1", "good", "bad2", "good"]
    frames = [_sign("Phong 3.12") if p == "good" else _sign(f"Ph0ng {p}")
              for p in pattern]

    hep = DocumentReader(stable_frames=3, window=3)
    rong = DocumentReader(stable_frames=3, window=8)

    res_hep = res_rong = None
    for f in frames:
        res_hep = hep.observe(f, W)
        res_rong = rong.observe(f, W)

    assert res_rong.say is not None
    assert res_hep.say is None
