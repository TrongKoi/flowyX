"""
NGUOI TRONG VONG LAP - he thong huong dan, nguoi dung doc bien chu noi.

--------------------------------------------------------------------
VI SAO KHONG GIAI MA BRAILLE BANG CAMERA
--------------------------------------------------------------------

Cham braille duong kinh 1,5mm, khoang cach tam 2,5mm. Can ~5 px/cham
de tach duoc cham co/khong, tuc anh 640px chi doc noi trong 0,15m va
anh 1920px trong 0,45m.

Them ba rao can nua:

  1. O FocusMode.FIXED thi 0,15-0,45m nam ngoai vung net.
  2. Braille khong co tuong phan mau - cham noi va nen cung mau, cung
     chat lieu. Camera chi thay cham nho DO BONG, nen phu thuoc hoan
     toan vao huong den. Den tran chieu thang tu tren xuong thi gan
     nhu khong co bong.
  3. Nguoi dung phai gio camera cach bien 20cm va giu vuong goc -
     trong khi khong nhin thay bien o dau.

Diem 3 la cho lap luan tu sup do: O CU LY 20CM THI TAY NGUOI DUNG DA
CHAM DUOC BIEN ROI. Ma cham chinh la cong dung cua braille.

Nen module nay lam nguoc lai: he thong noi bien o dau, NGUOI DUNG doc,
va he thong dung ket qua do lam moc.

    He thong:   "Ben phai ban, ngang tam tay, co bien chu noi."
    Nguoi dung: [so bien] "sau le tu"
    He thong:   "Phong 604, dung khong a?"
    Nguoi dung: "dung"
    He thong:   "Da xac nhan vi tri."

Ton trong ky nang nguoi dung thay vi thay the no: ta bu dung phan ho
thieu (biet minh o dau trong toa nha) va dung dung phan ho gioi hon may
(doc braille).

--------------------------------------------------------------------
HAI LOP PHONG THU - VA VI SAO CAN CA HAI
--------------------------------------------------------------------

Dac ta goc gan cho lop nay do tin cay HIGH voi ly do "nguoi doc braille
bang tay khong nham". Dieu do DUNG, nhung no bo qua mot mat xich:

    nguoi so bien  ->  nguoi NOI  ->  ASR  ->  chuan hoa so

Khau ASR tieng Viet trong hanh lang on hoan toan co the bien "sau le
tu" thanh "sau le tam". Ma dac ta lai cho moc nay VUOT nguong nhay
thong thuong - nghia la MOT loi ASR don le du de day pose di rat xa,
khong co gi chan lai.

Vi vay co hai lop:

  1. DOC LAI XAC NHAN. He thong nhac lai so phong va cho nguoi dung
     dong y. Loi ASR lo ra ngay o buoc nay, truoc khi sua pose.

  2. KIEM BAN KINH. Toa do phong phai nam trong ban kinh hop ly so voi
     uoc tinh hien tai. Khong dat thi TU CHOI - luc do hoac ASR sai,
     hoac VIO da troi qua xa, va ca hai truong hop deu khong nen
     teleport pose.

Lop 2 con bat duoc truong hop lop 1 khong bat duoc: nguoi dung doc
dung, nghe dung, dong y dung - nhung dang o mot tang khac voi tang he
thong tuong.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..loi_chung.geometry import Pose2D

# Cua so cho nguoi dung tra loi, giay.
CUA_SO_TRA_LOI_S = 10.0

# Im lang thi khong hoi lai trong bao lau. Khong duoc bien thanh thu
# phien - nguoi dung co quyen tu choi, va tu choi nhieu lan.
IM_LANG_NGHI_S = 60.0

# Chi moi khi he thong dang lac: gan mot cua da biet trong ban do.
GAN_CUA_M = 2.0

# So chu so toi thieu de coi la mot so phong. Xem chu thich trong
# chuan_hoa_so() ve tu "khong".
MIN_CHU_SO = 2

# LOP PHONG THU 2 - ban kinh toi da giua phong duoc xac nhan va uoc
# tinh hien tai.
#
# !!! GIA TRI TAM - CAN DO LAI TREN THUC DIA !!!
#
# Con so dung phai suy ra tu DO TROI VIO THAT tren quang 50m, va viec
# do do chua lam (xem SPEC muc 14). 12m la uoc luong tho: VIO trong
# nha troi 1-3% quang duong, nen sau 50m di lai khong neo duoc thi sai
# so co the toi 1,5m; 12m cho bien rong rai cho truong hop xau ma van
# chan duoc loi ASR doc nham sang mot phong o dau kia hanh lang.
#
# Do xong thi sua o day, va chi o day.
BAN_KINH_HOP_LY_M = 12.0

# ------------------------------------------------------------------
# Chuan hoa so tieng Viet
# ------------------------------------------------------------------

_CHU_SO = {
    "khong": "0", "ko": "0", "linh": "0", "le": "0",
    "mot": "1", "mot.": "1", "mo t": "1",
    "hai": "2", "ba": "3",
    "bon": "4", "tu": "4",
    "nam": "5", "lam": "5", "nham": "5",
    "sau": "6",
    "bay": "7", "bo y": "7", "bay.": "7",
    "tam": "8", "chin": "9",
}

# "mot" doc bien the khi dung sau "muoi": hai muoi MOT
_BIEN_THE = {"mot": "1", "tu": "4", "lam": "5"}

_BO_DAU = str.maketrans(
    "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
    "ùúủũụưừứửữựỳýỷỹỵđ",
    "a" * 17 + "e" * 11 + "i" * 5 + "o" * 17 + "u" * 11 + "y" * 5 + "d")


def _bo_dau(s: str) -> str:
    return s.lower().translate(_BO_DAU)


def _rut_gon(s: str) -> str:
    """Bo dau cham va gach de '3.12' va '312' so duoc voi nhau."""
    return "".join(c for c in s if c.isdigit())


def chuan_hoa_so(cau: str) -> str | None:
    """
    Doi cau noi tieng Viet thanh chuoi chu so.

        "sau le tu"          -> "604"
        "sau tram le bon"    -> "604"
        "sau khong bon"      -> "604"
        "ba cham muoi hai"   -> "3.12"
        "604"                -> "604"

    Tra None neu khong rut ra duoc chu so nao - im lang con hon doan.
    """
    if not cau or not cau.strip():
        return None

    tho = _bo_dau(cau)
    tho = "".join(c if (c.isalnum() or c in ". ") else " " for c in tho)
    tu = tho.split()

    ra: list[str] = []
    cho_thay: bool = False        # chu so ke tiep se THAY cho so cuoi

    for t in tu:
        if t.isdigit():                       # ASR tra thang chu so
            ra.extend(t)
            cho_thay = False
            continue

        if t in ("cham", "phay", "chan", "."):
            ra.append(".")
            cho_thay = False
            continue

        if t == "tram":                       # "sau tram le bon"
            continue                          # khong sinh chu so nao

        if t == "muoi":
            # Bo dau xong thi "muoi" (10) va "muoi" (chuc) TRUNG NHAU,
            # nen phai doan bang ngu canh:
            #
            #   "muoi hai"  -> dung dau chuoi -> 10 roi thay -> 12
            #   "hai muoi"  -> sau mot chu so -> hang chuc   -> 20
            if not ra or ra[-1] == ".":
                ra.extend(["1", "0"])     # muoi: 10, 11, 12...
            else:
                ra.append("0")            # muoi: 20, 30, 40...
            cho_thay = True
            continue

        if t in _CHU_SO:
            d = _CHU_SO[t]
            if cho_thay and ra:
                ra[-1] = _BIEN_THE.get(t, d)
            else:
                ra.append(d)
            cho_thay = False
            continue

        # Tu khong phai so thi bo qua, khong lam hong phan da rut duoc.

    chuoi = "".join(ra).strip(".")
    if not any(c.isdigit() for c in chuoi):
        return None

    # "khong" vua nghia la SO 0 vua la tu PHU DINH, va tu phu dinh thi
    # pho bien hon nhieu: "khong nghe ro gi", "khong phai", "khong
    # biet". Neu tinh no la so thi moi cau tu choi cua nguoi dung deu
    # bien thanh mot lan khai bao so phong - dung kieu loi nguy hiem
    # nhat o lop nay.
    #
    # So phong luon co it nhat hai chu so, nen doi hoi toi thieu hai la
    # chan duoc ca ho "khong ..." ma khong bo sot so that nao.
    if len(_rut_gon(chuoi)) < MIN_CHU_SO:
        return None

    return chuoi


# ------------------------------------------------------------------
# Ket qua tung buoc
# ------------------------------------------------------------------

@dataclass(frozen=True)
class LoiMoi:
    """Cau he thong noi de moi nguoi dung so bien."""

    text: str
    het_han_s: float = CUA_SO_TRA_LOI_S


@dataclass(frozen=True)
class ChoXacNhan:
    """Da nghe ra mot so phong, dang doc lai de nguoi dung xac nhan."""

    phong: str
    x: float
    y: float
    text: str                    # cau doc lai


@dataclass(frozen=True)
class MocBraille:
    """Moc da qua ca hai lop phong thu."""

    phong: str
    x: float
    y: float
    confidence: str = "HIGH"
    kind: str = "braille"

    # Nguon dang tin nhat trong he - duoc phep sua pose vuot nguong
    # nhay thong thuong. Chi dat True SAU khi qua ca hai lop.
    vuot_nguong_nhay: bool = True


# ------------------------------------------------------------------
# Ba buoc
# ------------------------------------------------------------------

def nen_moi(pose: Pose2D | None, confidence_thap: bool, floor_map,
            gan_cua_m: float = GAN_CUA_M) -> LoiMoi | None:
    """
    Buoc 1 - co nen moi nguoi dung so bien khong.

    Chi moi khi he thong DANG LAC va dang o gan mot cua da biet. Moi
    lung tung o giua hanh lang thi khong co bien de so, va chi lam
    nguoi dung mat tin.
    """
    if pose is None or not confidence_thap:
        return None

    gan = None
    for phong in getattr(floor_map, "rooms", {}):
        nut = floor_map.room_node(phong)
        if nut is None:
            continue
        d = math.hypot(nut.x - pose.x, nut.y - pose.y)
        if d <= gan_cua_m and (gan is None or d < gan[1]):
            gan = (phong, d)

    if gan is None:
        return None

    return LoiMoi(
        text="Bên phải bạn, ngang tầm tay, có biển chữ nổi. "
             "Hãy sờ và đọc số phòng.")


def nghe_so_phong(cau: str, pose: Pose2D | None,
                  floor_map) -> ChoXacNhan | str | None:
    """
    Buoc 2 - nghe so phong, tra ve cau DOC LAI de xac nhan.

    Day la LOP PHONG THU 1. Khong tra moc ngay: loi ASR phai lo ra
    truoc khi pose bi sua.

    Tra:
      ChoXacNhan  - nghe ra so, co trong ban do, dang cho dong y
      str         - cau bao loi de noi (khong co phong do)
      None        - khong nghe ra so nao
    """
    so = chuan_hoa_so(cau)
    if so is None:
        return None

    muc = _rut_gon(so)
    for phong in getattr(floor_map, "rooms", {}):
        if _rut_gon(phong) != muc:
            continue
        nut = floor_map.room_node(phong)
        if nut is None:
            continue
        return ChoXacNhan(
            phong=phong, x=nut.x, y=nut.y,
            text=f"Phòng {phong}, đúng không ạ?")

    return "Không tìm thấy phòng đó trong bản đồ."


_DONG_Y = {"dung", "dung roi", "phai", "vang", "u", "co", "ok", "okay",
           "chinh xac", "dung vay", "yes"}
_TU_CHOI = {"khong", "khong phai", "sai", "ko", "no", "chua dung"}


def xac_nhan(tra_loi: str, cho: ChoXacNhan, pose: Pose2D | None,
             ban_kinh_m: float = BAN_KINH_HOP_LY_M) -> MocBraille | str | None:
    """
    Buoc 3 - nguoi dung dong y, roi kiem ban kinh.

    LOP PHONG THU 1 dong lai o day (co dong y khong), va LOP PHONG THU
    2 chay ngay sau (toa do co hop ly khong).

    Tra:
      MocBraille - qua ca hai lop, duoc phep sua pose vuot nguong
      str        - cau bao ly do tu choi
      None       - nguoi dung khong dong y, im lang bo qua
    """
    tho = _bo_dau(tra_loi or "").strip()
    tho = " ".join(tho.split())

    if tho in _TU_CHOI or any(tho.startswith(t + " ") for t in _TU_CHOI):
        return None
    if not (tho in _DONG_Y or any(tho.startswith(t + " ") for t in _DONG_Y)):
        return None                       # khong ro thi coi nhu khong dong y

    # --- LOP PHONG THU 2 ---
    if pose is not None:
        d = math.hypot(cho.x - pose.x, cho.y - pose.y)
        if d > ban_kinh_m:
            return (f"Phòng {cho.phong} cách vị trí ước tính quá xa. "
                    "Chưa xác nhận được, hãy thử lại.")

    return MocBraille(phong=cho.phong, x=cho.x, y=cho.y)
