"""
NEO LO TRINH VAO GIO THAT - chong mu thoi gian.

--------------------------------------------------------------------
VI SAO LA MODULE RIENG, KHONG NHET VAO preview.py
--------------------------------------------------------------------

`preview.py` tra loi cau hoi "chia thong tin the nao de nguoi dung nho
duoc" - no la lop QUAN LY TAI NHAN THUC, va no khong biet gi ve dong
ho.

Module nay tra loi mot cau hoi khac han: "bay gio la may gio, va dieu
do nghia la gi voi nguoi dung". No can trang thai rieng (gio hen), co
cac moc bao phai nho da bao chua, va co logic doi giong khi sap tre.
Tron hai thu vao mot file se lam ca hai kho doc.

Ranh gioi: `preview.uoc_phut()` cho ra MOT CON SO (mat bao nhieu phut).
Module nay nhan con so do va bien no thanh MOT CAU CO MOC.

--------------------------------------------------------------------
"MU THOI GIAN" LA GI, VA CAI GI THAT SU PHAI SUA
--------------------------------------------------------------------

Kho cam nhan thoi gian troi qua, va kho uoc luong mot viec mat bao lau.
Hau qua thuc te la di tre kinh nien - khong phai vi khong quan tam.

Diem then chot: cau "khoang 4 phut" KHONG giai quyet gi ca. No la mot
khoang thoi gian TROI NOI, va no van doi nguoi dung tu lam phep cong
trong dau: "bay gio may gio? cong 4 phut la may gio? so voi gio vao
lop thi sao?" Ba phep tinh do chinh la thu ma nguoi mu thoi gian kho
lam.

Nen module nay lam ho ba phep tinh do, va tra ve mot cau chi con MOT
thong tin phai hanh dong:

    "Lớp học bắt đầu lúc 14 giờ. Viết báo cáo mất khoảng 6 phút.
     Bây giờ là 13 giờ 48 - bạn cần bắt tay vào trong 6 phút nữa."

--------------------------------------------------------------------
DON VI: PHUT TINH TU NUA DEM
--------------------------------------------------------------------

Moi phep tinh trong file nay dung "phut tinh tu nua dem" (0..1440),
kieu float. Khong dung epoch, khong dung datetime.

Ly do: lam vay thi toan bo logic kiem thu duoc bang so thuan, khong
phu thuoc mui gio hay ngay he cua may chay test. Chuyen doi tu dong ho
that nam o `phut_trong_ngay()`, dung mot cho duy nhat o ranh gioi.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from enum import Enum

# --------------------------------------------------------------------
# DEM AN TOAN
# --------------------------------------------------------------------
#
# `uoc_phut()` cho ra thoi gian TRUNG BINH, khong phai toi thieu. Neo
# dung khop vao gio den la cam chac tre mot nua so lan.
#
# Dem gom HAI phan vi co hai nguon tre khac nhau:
#
#   ty le  - tre tich luy theo quang duong: di cham hon uoc luong, dung
#            lai tranh nguoi, doc bien sai roi phai quay lai. Cang di xa
#            cang nhieu co hoi lech, nen phan nay PHAI ty le thuan.
#
#   hang so- chi phi khoi dong co dinh: tim cua ra khoi phong dang ngoi,
#            dinh huong lan dau, lan re dau tien. Phan nay KHONG doi
#            theo do dai tuyen - di 20 m hay 200 m thi buoc ra khoi
#            phong van ton chung ay.
#
# Chi dung ty le thi tuyen ngan gan nhu khong co dem. Chi dung hang so
# thi tuyen dai bi dem thieu. Nen phai co ca hai.
DEM_TY_LE = 0.20
DEM_KHOI_DONG_PHUT = 1.5

# Duoi nguong nay thi doi giong sang DI NGAY.
#
# Khong dat thap hon: nguoi dung con phai NGHE het cau, hieu, roi dung
# day. Bao "con 30 giay" thi cau bao chinh no da an het thoi gian.
NGUONG_GAP_PHUT = 2.0

# Tren nguong nay thi chua can giuc gi ca - noi gio phai di la du.
NGUONG_SOM_PHUT = 10.0

# Tren nguong nay thi KHONG doc so phut nua, chi noi gio phai di.
#
# "Còn 821 phút nữa" dung ve so hoc nhung vo dung ve thuc te: khong ai
# hinh dung duoc 821 phut la bao lau. Qua mot nguong thi mot moc tren
# dong ho ("13 giờ 57") de nam hon han mot con so dem nguoc.
NGUONG_DOC_SO_PHUT = 120.0

# Cac moc nhac trong luc dang di, tinh bang phut con lai TOI GIO HEN.
#
# Thua dan ve cuoi: cang gan gio thi mot phut cang dang gia, nen nhac
# day hon. Nhac deu nhau thi vua on o doan dau vua thua o doan cuoi.
MOC_NHAC_PHUT = (10.0, 5.0, 3.0, 1.0)


class Muc(str, Enum):
    """Muc do gap, suy tu thoi gian con lai TRUOC KHI PHAI KHOI HANH."""

    SOM = "som"            # con nhieu thoi gian
    SAP_DEN_GIO = "sap"    # trong khoang vai phut nua
    DI_NGAY = "di_ngay"    # duoi nguong an toan
    DA_TRE = "da_tre"      # di ngay bay gio cung toi muon


@dataclass(frozen=True)
class KeHoach:
    """Ket qua tinh toan. Thuan so - viec dat cau nam o `cau()`."""

    gio_hen: float             # phut tinh tu nua dem, thoi diem can co mat
    phut_di: float             # uoc luong tho tu uoc_phut()
    phut_dem: float            # dem an toan da cong them
    phut_can: float            # phut_di + phut_dem
    phut_toi_gio_hen: float    # tu bay gio toi gio hen
    phut_truoc_khi_di: float   # con bao lau nua thi PHAI khoi hanh
    gio_phai_di: float         # moc khoi hanh, phut tinh tu nua dem
    muc: Muc

    @property
    def tre_bao_nhieu_phut(self) -> float:
        """So phut se toi muon neu di ngay bay gio. 0 neu con kip."""
        return max(0.0, -self.phut_truoc_khi_di)


# --------------------------------------------------------------------
# chuyen doi va dinh dang
# --------------------------------------------------------------------


# ------------------------------------------------------------------
# Uoc thoi gian di - chuyen tu preview.py sang
# ------------------------------------------------------------------
#
# Ham nay TRUOC DAY nam trong `preview.py`, nhung no khong thuoc y tuong
# "doc lo trinh theo khoi". No la bo UOC LUONG THOI GIAN, va chinh la
# dau vao cua ca lop chong mu thoi gian - `tinh()` ben duoi khong chay
# duoc neu thieu no.
#
# Khi `preview.py` duoc cat sang `thu_nghiem/` (xem README o do), ham nay
# phai o lai. Nham cho se lam sap tru cot chinh cua che do ADHD.

# Toc do di bo trung binh cua nguoi khiem thi dung gay, met/giay.
#
# Cham hon nguoi sang mat dang ke: gay can thoi gian quet, va moi lan
# re can dung lai de dinh huong.
TOC_DO_M_S = 0.8

# Thoi gian cong them cho moi lan re, giay.
GIAY_MOI_LAN_RE = 3.0

# Thoi gian cong them cho moi lan doi tang, giay. Gom ca goi thang may,
# cho, vao cabin, va di chuyen.
GIAY_MOI_TANG = 25.0


def _la_lan_re(leg) -> bool:
    t = getattr(leg, "turn_at_end", None)
    return t is not None and abs(t) > 20.0


def uoc_phut(route) -> float:
    """
    Uoc thoi gian di, phut.

    Khong chi lay quang duong chia toc do: moi lan re phai dung lai dinh
    huong, va moi lan doi tang ton them nhieu thoi gian hon ca doan
    hanh lang dan toi no.
    """
    if route is None or not route.legs:
        return 0.0
    giay = route.total_length / TOC_DO_M_S
    giay += sum(GIAY_MOI_LAN_RE for l in route.legs if _la_lan_re(l))
    giay += sum(GIAY_MOI_TANG for l in route.legs if l.floor_change)
    return giay / 60.0

def phut_trong_ngay(epoch: float | None = None) -> float:
    """Dong ho that -> phut tinh tu nua dem.

    Day la RANH GIOI duy nhat giua module nay va thoi gian thuc. Moi
    ham khac chi lam viec voi so.
    """
    t = time.localtime(epoch if epoch is not None else time.time())
    return t.tm_hour * 60.0 + t.tm_min + t.tm_sec / 60.0


def gio_doc(phut: float) -> str:
    """Phut tinh tu nua dem -> chuoi DOC LEN duoc.

    Tra "14 giờ" chu khong phai "14:00": bo doc tieng Viet doc dau hai
    cham khong on dinh, co bo doc thanh "mười bốn không không".
    """
    phut = phut % 1440.0
    h = int(phut // 60)
    m = int(round(phut - h * 60))
    if m == 60:                       # lam tron len qua gio
        h, m = (h + 1) % 24, 0
    return f"{h} giờ" if m == 0 else f"{h} giờ {m:02d}"


def _so_phut(x: float) -> str:
    """Lam tron LEN. Bao thieu thi nguy hiem hon bao thua."""
    return str(max(1, int(math.ceil(x - 1e-9))))


# --------------------------------------------------------------------
# tinh toan
# --------------------------------------------------------------------

def dem_an_toan(phut_di: float) -> float:
    """Dem cong them vao uoc luong tho. Xem ghi chu dau file."""
    return phut_di * DEM_TY_LE + DEM_KHOI_DONG_PHUT


def tinh(phut_di: float, gio_bay_gio: float, gio_hen: float) -> KeHoach:
    """
    Neo mot lo trinh vao gio that.

    `phut_di`    - uoc luong tho, lay tu `preview.uoc_phut()`
    `gio_bay_gio`- phut tinh tu nua dem
    `gio_hen`    - phut tinh tu nua dem, thoi diem CAN CO MAT
    """
    phut_dem = dem_an_toan(phut_di)
    phut_can = phut_di + phut_dem
    phut_toi_gio_hen = gio_hen - gio_bay_gio
    phut_truoc_khi_di = phut_toi_gio_hen - phut_can

    if phut_truoc_khi_di < 0.0:
        muc = Muc.DA_TRE
    elif phut_truoc_khi_di < NGUONG_GAP_PHUT:
        muc = Muc.DI_NGAY
    elif phut_truoc_khi_di <= NGUONG_SOM_PHUT:
        muc = Muc.SAP_DEN_GIO
    else:
        muc = Muc.SOM

    return KeHoach(
        gio_hen=gio_hen,
        phut_di=phut_di,
        phut_dem=phut_dem,
        phut_can=phut_can,
        phut_toi_gio_hen=phut_toi_gio_hen,
        phut_truoc_khi_di=phut_truoc_khi_di,
        gio_phai_di=gio_hen - phut_can,
        muc=muc,
    )


# --------------------------------------------------------------------
# dat cau
# --------------------------------------------------------------------

def cau(kh: KeHoach, ten_cong_viec: str, gio_bay_gio: float,
        ten_su_kien: str | None = None) -> str:
    """
    Cau neo day du, doc luc bat dau mot cong viec co gio han.

    Hai ten, dung dung cho:
      `ten_cong_viec` - viec nguoi dung sap lam ("viết báo cáo")
      `ten_su_kien`   - moc phai xong truoc ("Lớp học", "Hạn nộp")

    `ten_su_kien` khong co thi noi
    trong tinh hon nhung van du thong tin.

    MOI truong hop deu ket thuc bang MOT viec phai lam. Day la yeu cau
    cung: cau kieu "sắp trễ rồi" ma khong kem hanh dong cu the la vo
    dung - no chi them lo au ma khong giam duoc gi.
    """
    # "Han nop luc 15 gio" doc tu nhien hon "Han nop bat dau luc 15 gio".
    # Khong co ten su kien thi noi thang la can xong luc may gio.
    moc = (f"{ten_su_kien} lúc {gio_doc(kh.gio_hen)}"
           if ten_su_kien else f"Cần xong lúc {gio_doc(kh.gio_hen)}")
    dau = (f"{moc}. "
           f"{ten_cong_viec.capitalize()} mất khoảng "
           f"{_so_phut(kh.phut_di)} phút. "
           f"Bây giờ là {gio_doc(gio_bay_gio)}")

    if kh.muc is Muc.DA_TRE:
        return (f"{dau}. Bắt tay vào ngay bây giờ thì vẫn muộn khoảng "
                f"{_so_phut(kh.tre_bao_nhieu_phut)} phút. Bạn cứ làm tiếp, "
                f"và báo trước là mình cần thêm thời gian.")
    if kh.muc is Muc.DI_NGAY:
        return f"{dau}. Bạn cần bắt tay vào ngay bây giờ để kịp."
    if kh.muc is Muc.SAP_DEN_GIO:
        return (f"{dau} - bạn cần bắt tay vào trong "
                f"{_so_phut(kh.phut_truoc_khi_di)} phút nữa.")
    if kh.phut_truoc_khi_di > NGUONG_DOC_SO_PHUT:
        return f"{dau}. Bạn cần bắt tay vào lúc {gio_doc(kh.gio_phai_di)}."
    return (f"{dau}. Bạn cần bắt tay vào lúc {gio_doc(kh.gio_phai_di)}, "
            f"tức là còn {_so_phut(kh.phut_truoc_khi_di)} phút nữa.")


# --------------------------------------------------------------------
# nhac trong luc dang di
# --------------------------------------------------------------------

class BoNhacGio:
    """
    Nhac theo MOC THOI GIAN CON LAI trong luc dang di.

    Vi sao can rieng cai nay, khi `guidance.py` da noi "còn 2 bước":

    Nguoi mu thoi gian co the di dung tien do ve KHOANG CACH ma khong
    he co khai niem no tuong ung voi bao nhieu phut. "Còn 2 bước" tra
    loi cau hoi CON BAO XA; no khong tra loi CON KIP KHONG. Hai cau hoi
    khac nhau, va cau thu hai moi la cau gay lo au.

    Nen moi lan nhac deu phai co con so PHUT. Chang duong la thong tin
    kem theo, khong phai thong tin chinh.

    Moi moc chi bao DUNG MOT LAN. Lap lai cung mot moc la nguon lam
    phien lon nhat cua moi he thong nhac gio.
    """

    def __init__(self, gio_hen: float, moc: tuple[float, ...] = MOC_NHAC_PHUT):
        self.gio_hen = gio_hen
        self._moc = tuple(sorted(moc, reverse=True))
        self._da_bao: set[float] = set()
        self._da_bao_tre = False

    def cap_nhat(self, gio_bay_gio: float,
                 buoc_con_lai: int | None = None) -> str | None:
        """Tra cau can noi, hoac None neu chua toi moc nao."""
        con = self.gio_hen - gio_bay_gio

        if con < 0.0:
            if self._da_bao_tre:
                return None
            self._da_bao_tre = True
            return (f"Đã quá giờ hẹn {_so_phut(-con)} phút. "
                    f"Bạn cứ đi tiếp, sắp tới nơi rồi.")

        chua_bao = [m for m in self._moc if con <= m and m not in self._da_bao]
        if not chua_bao:
            return None

        # Danh dau HET cac moc da qua, khong chi moc vua khop.
        #
        # Neu chi danh dau mot moc thi lan goi ngay sau se khop moc ke
        # tiep va doc LAI gan nhu y nguyen cau vua roi. O moc 10-5-3-1,
        # mot nguoi dung con 1 phut se nghe bon cau gan giong het nhau
        # doc lien tiep.
        #
        # Canh nay xay ra that: mat song WiFi mot luc roi co lai, hoac
        # app vao nen roi quay ra - luc do nhieu moc da troi qua cung
        # mot luc.
        self._da_bao.update(chua_bao)

        cau_moc = f"Còn {_so_phut(con)} phút nữa tới giờ."
        if buoc_con_lai is not None and buoc_con_lai > 0:
            return f"{cau_moc} Bạn còn {buoc_con_lai} bước."
        return cau_moc
