"""
XEM TRUOC HANH TRINH - biet truoc dieu gi sap xay ra.

--------------------------------------------------------------------
VI SAO CAN LOP NAY
--------------------------------------------------------------------

Nguoi tu ky gap kho khan khi lap ke hoach va sap xep thu tu hanh trinh,
nhat la khi co nhieu buoc, nhieu thay doi, hoac ap luc thoi gian. Va
TINH DU DOAN DUOC lam giam lo au - biet truoc dieu gi sap xay ra la mot
trong nhung ho tro hieu qua nhat.

Voi ADHD thi co che ro hon: kho khan ve TRI NHO LAM VIEC lam viec theo
cac chi dan nhieu buoc tro nen kho khan.

Nguoi khiem thi cung huong loi: biet truoc co may lan re thi do phai
giu con so do trong dau suot ca chang duong.

--------------------------------------------------------------------
CAI BAY: DOC CA LO TRINH MOT LUOT LA PHAN TAC DUNG
--------------------------------------------------------------------

Diem thiet ke quan trong nhat cua module nay, va no NGUOC voi truc giac.

Nghien cuu ve do dai mo ta lo trinh bang loi cho thay: gioi han dung
luong cua tri nho lam viec bang loi anh huong TRUC TIEP toi viec nho va
lam theo mo ta lo trinh. Vuot qua gioi han do dan toi kho nho cac moc,
cac lan re, hoac chi dan quan trong.

Ve con so: nghien cuu cu cho rang nguoi ta nho duoc khoang bay don vi,
nhung nghien cuu sau chi ra gioi han chinh xac hon la BA DEN NAM, va
Cowan tong hop du lieu de de xuat BON don vi la hop ly nhat.

Nghia la: doc mot tuyen 6 chang lien mach se VUOT gioi han, va nguoi co
ADHD - von da yeu o khau nay - se mat phan giua. Tinh nang dinh giup ho
lai lam kho ho.

Nen module nay chia khoi va doc THEO YEU CAU:

    muc 0   tom tat mot cau      "Bon lan re, mot lan thang may, 4 phut."
    muc 1   tung chang, moi lan mot chang, nguoi dung tu hoi tiep
    luon    noi ro CON BAO NHIEU - do la thu giam lo au, khong phai
            chi tiet

--------------------------------------------------------------------
NOI SO LUONG TRUOC, CHI TIET SAU
--------------------------------------------------------------------

"Con ba chang nua" huu ich hon "re phai roi di thang roi re trai".

Cau dau cho nguoi dung mot cai KHUNG de gan thong tin vao, va mot cach
biet minh dang o dau trong hanh trinh. Cau sau bat ho nho ba thu cung
luc ma khong biet con bao nhieu nua.
"""

from __future__ import annotations

from dataclasses import dataclass

# So don vi thong tin toi da trong MOT cau doc len.
#
# Bon la gioi han Cowan de xuat. Dat cao hon thi cau noi vuot dung luong
# tri nho lam viec, va nguoi dung mat phan giua - dung nhom nguoi ma
# tinh nang nay dinh phuc vu.
TOI_DA_MOI_CAU = 4

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


@dataclass(frozen=True)
class TomTat:
    """Tom tat mot tuyen duong - MOT cau, duoi bon don vi thong tin."""

    so_chang: int
    so_lan_re: int
    so_lan_doi_tang: int
    do_dai_m: float
    phut: float
    co_nguy_hiem: bool


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


def tom_tat(route) -> TomTat | None:
    """Rut mot tuyen duong thanh cac con so de sinh cau tom tat."""
    if route is None or not route.legs:
        return None
    return TomTat(
        so_chang=len(route.legs),
        so_lan_re=sum(1 for l in route.legs if _la_lan_re(l)),
        so_lan_doi_tang=sum(1 for l in route.legs if l.floor_change),
        do_dai_m=route.total_length,
        phut=uoc_phut(route),
        co_nguy_hiem=any(l.hazard for l in route.legs),
    )


def cau_tom_tat(route) -> str | None:
    """
    MOT cau tom tat ca hanh trinh, duoi bon don vi thong tin.

    Day la cau DAU TIEN nguoi dung nghe, va thuong la cau duy nhat ho
    can. No cho ho mot cai khung de gan thong tin vao.
    """
    t = tom_tat(route)
    if t is None:
        return None

    phan: list[str] = []
    if t.so_lan_re:
        phan.append(f"{t.so_lan_re} lần rẽ")
    if t.so_lan_doi_tang:
        phan.append(f"{t.so_lan_doi_tang} lần đổi tầng")
    phan.append(f"khoảng {t.phut:.0f} phút")

    cau = "Lộ trình: " + ", ".join(phan) + "."
    if t.co_nguy_hiem:
        # Nguy hiem phai duoc neu NGAY o cau tom tat, khong doi nguoi
        # dung hoi tiep - ho co the khong hoi.
        cau += " Có một đoạn cần chú ý."
    return cau


def cau_chang(route, i: int) -> str | None:
    """
    Mot chang, mot cau. Luon noi ro CON BAO NHIEU CHANG NUA.

    Con so o cuoi cau khong phai trang tri: no cho nguoi dung biet minh
    dang o dau trong hanh trinh, va do la thu giam lo au chu khong phai
    chi tiet duong di.
    """
    if route is None or not (0 <= i < len(route.legs)):
        return None

    leg = route.legs[i]
    phan: list[str] = []

    if leg.floor_change:
        huong = "lên" if leg.floor_change > 0 else "xuống"
        so = abs(leg.floor_change)
        bang = "thang máy" if leg.edge.is_lift else "cầu thang bộ"
        phan.append(f"Đi {huong} {so} tầng bằng {bang}")
    else:
        phan.append(f"Đi thẳng khoảng {leg.length:.0f} mét")

    phan.append(f"tới {leg.to.name}")
    cau = " ".join(phan) + "."

    if leg.hazard:
        cau += f" Lưu ý: {leg.hazard}."

    con = len(route.legs) - i - 1
    cau += f" Còn {con} chặng." if con else " Đó là chặng cuối."
    return cau


class PhienXemTruoc:
    """
    Mot luot xem truoc, doc theo yeu cau.

    Nguoi dung nghe cau tom tat truoc. Muon biet them thi hoi tiep, moi
    lan mot chang. Khong hoi thi thoi - va do la truong hop PHO BIEN
    NHAT, hoan toan hop le.

    Giu trang thai giua cac luot vi nguoi dung co the hoi "tiep" nhieu
    lan, va he thong phai biet dang o chang nao.
    """

    def __init__(self, route):
        self.route = route
        self._i = -1                # -1 = chua doc chang nao

    @property
    def da_het(self) -> bool:
        return self.route is None or self._i >= len(self.route.legs) - 1

    def bat_dau(self) -> str | None:
        """Cau dau tien: tom tat ca hanh trinh."""
        self._i = -1
        c = cau_tom_tat(self.route)
        if c is None:
            return None
        return c + " Bạn muốn nghe chi tiết không?"

    def tiep(self) -> str | None:
        """Chang ke tiep. Tra None khi da het."""
        if self.da_het:
            return None
        self._i += 1
        return cau_chang(self.route, self._i)

    def lap_lai(self) -> str | None:
        """
        Doc lai chang vua roi.

        Can co: nguoi co kho khan ve tri nho lam viec se bo lo mot cau va
        KHONG the tua vao viec doc lai man hinh nhu nguoi sang mat.
        """
        if self._i < 0:
            return self.bat_dau()
        return cau_chang(self.route, self._i)
