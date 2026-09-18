"""
CANH GAC CAU CHU - hai nhom quy tac, deu la rang buoc cung.

--------------------------------------------------------------------
NHOM 1: DAU TIENG VIET
--------------------------------------------------------------------

Ma nguon va chu thich viet KHONG dau (lua chon ve kieu code). Nhung moi
chuoi SE DUOC DOC LEN thi bat buoc co dau day du.

Bo doc tieng Viet doc "Dang chay" thanh mot chuoi am vo nghia: khong co
dau thi khong xac dinh duoc thanh dieu. Bo dau o day la lam hong dung
thu duy nhat nguoi dung nhan duoc qua tai.

--------------------------------------------------------------------
NHOM 2: BON QUY TAC TRANH DIEN THIET BI Y TE
--------------------------------------------------------------------

Xem docs/FLOWY_THIET_KE.md muc 4. Tom tat ly do:

Huong dan "General Wellness: Policy for Low Risk Devices" cua FDA (ban
06/01/2026) neu dich danh nhung thu lam san pham roi vao dien thiet bi y
te chiu quan ly. Trong do co: nhac ten benh cu the (va "ADHD" duoc neu
lam vi du), cau chan doan, nguong lam sang, va huong dan dieu tri.

Ranh gioi do nam o CAU CHU nhieu hon o ma nguon. Nen no phai duoc kiem
tu dong, giong het cach dau tieng Viet duoc kiem - neu khong thi mot cau
vo tinh viet sai se di thang ra ban nop.

Bon quy tac:

    1. Khong chuoi nao chua ten benh
    2. Khong cau nao khang dinh ve tinh trang nguoi dung
    3. Khong con so nao duoc goi la diem so hay muc do
    4. Khong cau nao hua hen hieu qua dieu tri

--------------------------------------------------------------------
KIEM CA HAI CHIEU
--------------------------------------------------------------------

Chi kiem dau ra cua ham thi bo sot nhung chuoi nam trong nhanh khong
duoc chay toi. Nen file nay kiem CA HAI:

    a) Quet chuoi trong MA NGUON cua moi module
    b) Chay that cac ham sinh cau, roi kiem ket qua

Cach (a) bat duoc chuoi chet; cach (b) bat duoc chuoi ghep tu nhieu
manh.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GOC))

from wayfinding.adhd import dongvien, mach, meety, timeblind   # noqa: E402

DAU = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
          "ùúủũụưừứửữựỳýỷỹỵđ")

# Mot cau tieng Viet tu 4 tu tro len gan nhu khong the khong co lay MOT
# dau nao. Cau ngan thi khong du bang chung, va bao dong gia se lam
# nguoi ta tat test nay di - luc do no thanh vo dung.
#
# Da tung thu cach liet ke "am tiet bat buoc co dau" va no bao dong gia
# ngay: "thang" trong "Cau thang" la tu viet dung. Tieng Viet co qua
# nhieu tu hop le khong dau nen moi danh sach kieu do deu sai.
MIN_TU_DE_XET = 4


def co_dau(s: str) -> bool:
    return any(c in DAU for c in s.lower())


def mat_dau(s: str) -> bool:
    """Chuoi nay co phai tieng Viet bi mat dau khong.

    Chi dem cac tu co TU HAI CHU CAI tro len. Mot tu mot chu cai khong
    the la am tiet tieng Viet bi mat dau: moi tu mot chu cai cua tieng
    Viet ("ý", "ở", "à") deu mang dau ngay trong chinh chu cai do, nen
    `co_dau` da bat duoc roi.

    Khong dem chung thi tranh duoc bao dong gia o cac chuoi DINH DANG.
    "%Y-%m-%d %H:%M" tach ra thanh nam tu mot chu cai va bi bao la mot
    cau tieng Viet mat dau - no khong phai cau noi, va cung khong phai
    tieng Viet.
    """
    tu = [t for t in "".join(c if c.isalnum() else " " for c in s).split()
          if sum(ch.isalpha() for ch in t) >= 2]
    if len(tu) < MIN_TU_DE_XET:
        return False
    return not co_dau(s)


def _id_docstring(cay: ast.AST) -> set[int]:
    """Danh dau cac nut la DOCSTRING, de bo qua khi quet.

    Nhan dien theo CAU TRUC cu phap - lenh dau tien cua module, lop, hay
    ham - chu khong theo do dai hay so dong.

    Ban dau toi doan bang do dai ("docstring thi dai va nhieu dong") va
    no bo sot ngay: mot docstring ngan gon mot dong thi ngan hon nguong
    nen lot qua, roi bai test bao no la cau noi mat dau. Cau truc cu
    phap thi khong doan gi ca.
    """
    ra: set[int] = set()
    for n in ast.walk(cay):
        if not isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef,
                              ast.AsyncFunctionDef)):
            continue
        if (n.body and isinstance(n.body[0], ast.Expr)
                and isinstance(n.body[0].value, ast.Constant)
                and isinstance(n.body[0].value.value, str)):
            ra.add(id(n.body[0].value))
    return ra


def chuoi_trong(duong_dan: Path) -> list[str]:
    """Moi chuoi SE DOC LEN trong mot tep Python.

    Doc bang cay cu phap chu khong bang bieu thuc chinh quy: chuoi nhieu
    dong, chuoi f, va chuoi noi nhau deu duoc lay dung.

    Bo qua docstring (tai lieu cho nguoi doc ma nguon, viet khong dau la
    dung quy uoc) va chu thich (khong nam trong cay cu phap nen tu dong
    khong co).
    """
    cay = ast.parse(duong_dan.read_text(encoding="utf-8"))
    bo_qua = _id_docstring(cay)
    ra: list[str] = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            if id(n) not in bo_qua:
                ra.append(n.value)
        elif isinstance(n, ast.JoinedStr):           # chuoi f
            ra.append("".join(p.value for p in n.values
                              if isinstance(p, ast.Constant)
                              and isinstance(p.value, str)))
    return ra


MODULE = sorted((GOC / "wayfinding" / "adhd").glob("*.py"))


# ==================================================================
# NHOM 1: dau tieng Viet
# ==================================================================

def test_bo_do_bat_duoc_cau_mat_dau():
    """
    Chinh cai thuoc do phai duoc do. Mot bo do noi long qua tay thi ca
    nhom kiem tra ben duoi im lang ma khong ai biet.
    """
    assert mat_dau("Ban dang lam do bao cao")
    assert mat_dau("Con mot buoc nua la xong")
    assert mat_dau("Da toi gio uong nuoc roi")


def test_bo_do_KHONG_bat_duoc_cau_mat_dau_MOT_PHAN():
    """
    Gioi han da biet, ghi lai de khong ai tuong nham.

    `co_dau` chi hoi "co lay MOT dau nao khong". Mot cau con lai dung
    dau o vai tu thi lot qua. Nguong do la co y: bo do chat hon tung
    bao dong gia lien tuc, va mot bai test hay bao dong gia se bi tat
    di - luc do no thanh vo dung.

    Cho cai nay duoc bat la o `test_khong_chuoi_nao_vi_pham_quy_tac_y_te`
    va o mat nguoi doc review.
    """
    assert not mat_dau("Đã tới giờ uong nuoc roi")


def test_bo_do_khong_bao_dong_gia():
    assert not mat_dau("Bạn đang làm dở báo cáo.")
    assert not mat_dau("Còn một bước nữa.")
    assert not mat_dau("")
    assert not mat_dau("xong_buoc")               # ten ky thuat, hai tu
    assert not mat_dau("%Y-%m-%d %H:%M")          # chuoi dinh dang
    assert not mat_dau("%d/%m/%Y %H:%M:%S")


@pytest.mark.parametrize("tep", MODULE, ids=lambda p: p.name)
def test_chuoi_trong_ma_nguon_khong_mat_dau(tep: Path):
    """Quet moi chuoi hang so trong module sinh cau noi."""
    for s in chuoi_trong(tep):
        assert not mat_dau(s), f"{tep.name}: {s!r}"


def test_cau_neo_gio_co_dau():
    bay_gio = 13 * 60 + 48
    for gio_hen in (14 * 60, 13 * 60 + 50, 13 * 60 + 58, 15 * 60):
        kh = timeblind.tinh(6.0, bay_gio, gio_hen)
        s = timeblind.cau(kh, "Phòng 6.04", bay_gio, "Lớp học")
        assert co_dau(s) and not mat_dau(s), s


def test_cau_nhac_gio_co_dau():
    bo = timeblind.BoNhacGio(14 * 60)
    s = bo.cap_nhat(13 * 60 + 55, buoc_con_lai=2)
    assert s and co_dau(s)


def test_cau_giu_mach_co_dau():
    cd = mach.ViecDangLam(ten_viec="Phòng 6.04", muc_dich="nộp đơn xin nghỉ")
    for s in (mach.cau_hoi_muc_dich(),
              mach.cau_xong_viec(cd),
              mach.cau_khoi_phuc(cd, chi_dan="Rẽ phải.", buoc_con_lai=2)):
        assert co_dau(s) and not mat_dau(s), s


def test_cau_dong_vien_co_dau():
    for cau in dongvien.CAU.values():
        assert cau == "" or co_dau(cau), cau


def test_cau_loi_meety_co_dau(tmp_path: Path):
    """Cau bao loi cung duoc doc len, nen cung phai co dau."""
    kq = meety.goi(tmp_path / "khong-co", tmp_path / "x.vtt", "2026-09-15")
    assert kq.ok is False
    assert co_dau(kq.loi_doc) and not mat_dau(kq.loi_doc)


# ==================================================================
# NHOM 2: bon quy tac tranh dien thiet bi y te
# ==================================================================

# Quy tac 1 - ten benh.
#
# "ADHD" duoc FDA neu DICH DANH lam vi du ve nhan benh lam san pham roi
# vao dien quan ly. Ba tu con lai la cach goi tieng Viet cua cung mot
# thu.
#
# Luu y: cam o CHUOI SE DOC LEN, khong cam o chu thich va tai lieu. Noi
# ve ADHD trong docs/ va trong bai thuyet trinh la binh thuong - van de
# chi nam o tuyen bo ve muc dich su dung cua san pham.
TEN_BENH = ("adhd", "rối loạn", "tăng động", "giảm chú ý", "bệnh lý")

# Quy tac 2 - khang dinh ve tinh trang nguoi dung.
#
# "Hom nay ban mat tap trung hon" la mot cau chan doan tra hinh: app
# khong biet dieu do, va noi ra la vuot qua vai tro cua no.
KHANG_DINH = ("bạn đang bị", "bạn bị", "tình trạng của bạn",
              "triệu chứng của bạn", "bạn mất tập trung",
              "bạn kém tập trung")

# Quy tac 3 - diem so va muc do.
#
# Cham diem la buoc dau cua danh gia lam sang. App ghi lai, khong danh
# gia.
DIEM_SO = ("điểm số", "mức độ nặng", "thang điểm", "chỉ số tập trung")

# Quy tac 4 - hua hen hieu qua dieu tri.
HUA_HEN = ("điều trị", "chữa", "cải thiện triệu chứng", "khỏi bệnh",
           "liệu pháp")


@pytest.mark.parametrize("tep", MODULE, ids=lambda p: p.name)
@pytest.mark.parametrize("nhom,tu_cam", [
    ("ten benh", TEN_BENH),
    ("khang dinh tinh trang", KHANG_DINH),
    ("diem so", DIEM_SO),
    ("hua hen dieu tri", HUA_HEN),
])
def test_khong_chuoi_nao_vi_pham_quy_tac_y_te(tep: Path, nhom: str,
                                              tu_cam: tuple[str, ...]):
    """
    Quet chuoi SE DOC LEN trong tung module.

    `chuoi_trong()` da bo qua docstring va chu thich: chung la tai lieu
    cho nguoi doc ma nguon, khong phai cau noi voi nguoi dung, nen duoc
    phep nhac ten benh de giai thich ly do thiet ke.
    """
    for s in chuoi_trong(tep):
        thap = s.lower()
        for tu in tu_cam:
            assert tu not in thap, f"{tep.name} vi pham [{nhom}]: {s!r}"


def test_cau_sinh_ra_luc_chay_cung_khong_vi_pham():
    """
    Chieu thu hai: chay that cac ham sinh cau roi kiem ket qua.

    Cach quet ma nguon bo sot chuoi ghep tu nhieu manh - vi du mot cau
    noi + mot ten viec do nguoi dung nhap. Bai nay bat duoc loai do.
    """
    bay_gio = 13 * 60 + 48
    cd = mach.ViecDangLam(ten_viec="Phòng 6.04", muc_dich="nộp đơn")
    cau_ra = [
        timeblind.cau(timeblind.tinh(6.0, bay_gio, 14 * 60),
                      "Phòng 6.04", bay_gio, "Lớp học"),
        mach.cau_hoi_muc_dich(),
        mach.cau_xong_viec(cd),
        mach.cau_khoi_phuc(cd, chi_dan="Rẽ phải.", buoc_con_lai=2),
        meety.cau_dang_chay(),
        *[c for c in dongvien.CAU.values() if c],
    ]
    cam = TEN_BENH + KHANG_DINH + DIEM_SO + HUA_HEN
    for s in cau_ra:
        thap = s.lower()
        for tu in cam:
            assert tu not in thap, f"cau sinh luc chay vi pham: {s!r}"


def test_danh_sach_tu_cam_khong_rong():
    """Canh gac cho chinh bo canh gac.

    Neu ai do lam rong mot danh sach thi moi bai tren van xanh ma khong
    con kiem gi ca - loai hong im lang te nhat.
    """
    for ten, ds in (("TEN_BENH", TEN_BENH), ("KHANG_DINH", KHANG_DINH),
                    ("DIEM_SO", DIEM_SO), ("HUA_HEN", HUA_HEN)):
        assert len(ds) >= 3, ten
