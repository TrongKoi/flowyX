"""
CAU HOI DUNG LUC - phan giao duc tam ly, nhung khong phai bai giang.

--------------------------------------------------------------------
VI SAO KHONG LAM THU VIEN BAI VIET
--------------------------------------------------------------------

Huong hien nhien cho nhom "giao duc tam ly va ky nang CBT" la mot muc
bai viet, hoac mot khoa hoc chia chuong.

Tai lieu CBT cho nguoi lon noi thang dieu nguoc lai: nguoi den hoc
thuong da "biet phai lam gi, nhung kho lam duoc".

Tuc day la VAN DE THUC THI, khong phai van de kien thuc. Mot thu vien
bai viet giai mot van de khong ton tai - va con to ra la giai roi.

Te hon nua: doc bai viet la mot viec de lam VA co cam giac nhu dang co
gang. No la cho tron hoan hao khoi chinh viec can lam.

--------------------------------------------------------------------
NEN KY NANG DUOC NHUNG VAO DUNG PHUT CAN DEN NO
--------------------------------------------------------------------

Cung mot noi dung, nhung khong phai o chuong 3, ma o dung phut nguoi
dung dang ket:

    chuong "chia nho cong viec"   ->  "Bước nhỏ nhất bạn làm được ngay
                                       bây giờ là gì?" - hoi khi dang ket
    chuong "y dinh thuc thi"      ->  ba o khi nao/o dau/viec gi trong
                                       `phien.py`
    chuong "doi chieu uoc luong"  ->  cau trong `thoiluong.py`

Bai hoc duoc day mot lan; cau hoi dung luc duoc tra loi moi lan.

--------------------------------------------------------------------
HOI, KHONG KHUYEN
--------------------------------------------------------------------

Moi chuoi trong module nay ket thuc bang dau hoi. Do la mot rang buoc
co test canh gac, khong phai mot so thich van phong.

Cau hoi de lai quyen quyet dinh cho nguoi dung. Loi khuyen lay no di, va
mot app lay quyen quyet dinh cua nguoi dung ve viec ho nen lam gi voi
suc khoe cua ho la mot app khac han ve mat phap ly.

Bon quy tac viet o docs/FLOWY_THIET_KE.md muc 4.4 ap dung cho ca file
nay, va `tests/loi_chung/test_cau_chu.py` quet no tu dong.

--------------------------------------------------------------------
VA APP VAN KHONG CHU DONG BAT CHUYEN
--------------------------------------------------------------------

Day la cho de nham nhat trong ca buoc nay.

docs/NHAN_VAT_BRIEF.md muc 2.4: nhan vat chi tuong tac khi duoc cham.
Nhung dung luc can hoi nhat - luc nguoi dung dang ket - ho lai it kha
nang chu dong cham vao nhat.

Cach go: tach hai thu ra.

    net mat diu xuong   thu dong. Nhin thay duoc, khong doi hoi gi.
                        Day la thu bo do ket o duoi lam.
    cau hoi             CHI khi duoc cham. No doi mot cau tra loi.

Net mat diu xuong la mot loi moi nhin thay duoc ma khong phai la bat
chuyen. Nguoi dung cham thi moi co cau hoi.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# Bao lau o mot buoc thi coi la dang ket.
#
# De rong: nhieu viec that su mat hon 15 phut cho mot buoc, va goi mot
# nguoi dang lam duoc viec la "dang ket" thi te hon la im lang.
#
# Con so nay chi doi NET MAT nhan vat. No khong lam app len tieng, nen
# doan nham o day tra gia rat nhe.
KET_LAU_GIAY = 900.0

# Bao nhieu lan roi khoi app trong mot phien thi coi la dang bi keo di.
SO_LAN_ROI_DANG_KE = 3


class LucNao(str, Enum):
    """Cac phut ma mot cau hoi co cho dung."""

    CHUA_BAT_DAU = "chua_bat_dau"      # da co y dinh, chua dong tay
    DANG_KET = "dang_ket"              # lau roi van o buoc do
    BI_KEO_DI = "bi_keo_di"            # roi khoi app nhieu lan
    VUA_XONG = "vua_xong"              # xong roi, con nhin lai duoc


# Cau hoi theo tung luc.
#
# Nhieu hon mot cau moi luc, vi cung mot cau hoi lap lai lan thu nam se
# thanh tieng on. Doi cau theo vong - xem `BoCauHoi` ben duoi.
CAU_HOI: dict[LucNao, tuple[str, ...]] = {
    LucNao.CHUA_BAT_DAU: (
        "Việc đầu tiên bạn chạm tay vào sẽ là gì?",
        "Bạn cần gì ở trước mặt để bắt đầu?",
        "Hai phút đầu tiên sẽ trông như thế nào?",
    ),
    LucNao.DANG_KET: (
        "Bước nhỏ nhất bạn làm được ngay bây giờ là gì?",
        "Bước này có chia nhỏ thêm được nữa không?",
        "Chỗ nào trong bước này đang khó đi tiếp?",
        "Nếu làm phần dễ nhất trước thì sao?",
    ),
    LucNao.BI_KEO_DI: (
        "Có gì quanh bạn đang kéo sự chú ý đi không?",
        "Bạn có cần tắt bớt thứ gì không?",
        "Chỗ nào yên hơn chỗ bạn đang ngồi không?",
    ),
    LucNao.VUA_XONG: (
        "Việc này hoá ra dễ hơn hay khó hơn bạn nghĩ?",
        "Có gì lần này khác với lần trước không?",
        "Lần sau bạn muốn bắt đầu bằng bước nào?",
    ),
}


def cau(luc: LucNao, lan: int = 0) -> str:
    """Cau hoi cho mot luc. `lan` xoay vong trong danh sach."""
    ds = CAU_HOI[luc]
    return ds[lan % len(ds)]


@dataclass
class BoCauHoi:
    """Chon cau hoi, va nho cau nao da hoi de khong lap lien tiep."""

    _lan: dict[LucNao, int] = field(default_factory=dict, repr=False)

    def hoi(self, luc: LucNao) -> str:
        n = self._lan.get(luc, 0)
        self._lan[luc] = n + 1
        return cau(luc, n)


@dataclass
class BoDoKet:
    """
    Do xem nguoi dung co dang ket o mot buoc khong.

    Ket qua CHI dung de doi net mat nhan vat. No khong lam app len tieng
    - xem phan dau file.
    """

    _buoc: int | None = field(default=None, repr=False)
    _tu_luc: float | None = field(default=None, repr=False)
    _so_lan_roi: int = field(default=0, repr=False)

    def sang_buoc(self, chi_so: int, t: float) -> None:
        """Bao rang nguoi dung vua sang mot buoc khac."""
        if chi_so != self._buoc:
            self._buoc = chi_so
            self._tu_luc = t

    def roi_di(self) -> None:
        """Bao rang app vua ra khoi tien canh."""
        self._so_lan_roi += 1

    def dang_ket(self, t: float) -> bool:
        if self._tu_luc is None:
            return False
        return (t - self._tu_luc) >= KET_LAU_GIAY

    @property
    def bi_keo_di(self) -> bool:
        return self._so_lan_roi >= SO_LAN_ROI_DANG_KE

    def luc_nen_hoi(self, t: float, da_bat_dau: bool,
                    da_xong: bool) -> LucNao:
        """
        Luc nao dang dung nhat cho cau hoi tiep theo.

        Luon tra ve mot gia tri: nguoi dung da cham vao nhan vat, nen
        phai co cau tra loi. Im lang o day la mot cu cham bi lo.
        """
        if da_xong:
            return LucNao.VUA_XONG
        if not da_bat_dau:
            return LucNao.CHUA_BAT_DAU
        if self.dang_ket(t):
            return LucNao.DANG_KET
        if self.bi_keo_di:
            return LucNao.BI_KEO_DI
        return LucNao.DANG_KET
