"""
PHAN HOI TICH CUC - xong chang, va ban dong hanh.

--------------------------------------------------------------------
HAI VIEC, MOT NGUYEN TAC CHUNG
--------------------------------------------------------------------

    xong chang      -> phan hoi CAM GIAC tuc thi (rung nhe + am ngan)
    ban dong hanh   -> mot icon doi trang thai theo su kien

Ca hai deu la lop dat LEN TREN co che da co. Chung khong tao ra khai
niem moi nao: "chang" van la `route.legs` nhu cu, va cac su kien deu
do lop khac sinh ra. Module nay chi quyet dinh PHAN UNG.

--------------------------------------------------------------------
VI SAO CHIA NHO NHIEM VU LAI QUAN TRONG
--------------------------------------------------------------------

Te liet truoc nhiem vu (task paralysis) la khi mot viec trong qua lon
nen khong bat dau duoc. Cach go thong thuong la chia nho ra, va danh
dau tung phan xong.

Mot lo trinh VON DA duoc chia san thanh cac chang. Nen o day khong can
thiet ke lai gi ca - chi can lam cho moi chang xong CO CAM GIAC la
xong. Mot cai rung nhe dung luc lam viec do tot hon mot cau noi dai,
vi no khong chiem kenh tai va khong cat ngang dong suy nghi.

--------------------------------------------------------------------
RANG BUOC CUNG: KHONG CO TRANG THAI TIEU CUC
--------------------------------------------------------------------

Ban dong hanh KHONG BAO GIO co trang thai buon, that vong, hay trach
moc - ke ca khi nguoi dung tre gio, di lac, hay bo do chuyen di.

Day khong phai lua chon ve giong dieu. ADHD thuong di kem NHAY CAM VOI
SU TU CHOI / THAT BAI: mot nhan vat to ra that vong se lam nguoi dung
TRANH MO APP, va luc do moi tinh nang khac deu thanh vo dung, ke ca
nhung tinh nang dang chay tot.

Nen bo trang thai o duoi chi co ba muc tich cuc va mot muc trung tinh.
Co test khoa dieu nay.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Ma rung cho "xong mot chang". Nhe va ngan - day la loi khen, khong
# phai canh bao. Xem HAPTIC_PATTERNS trong speech.py.
HAPTIC_XONG_BUOC = "xong_buoc"

# Am ngan phat kem. Ten thuan, dien thoai tu chon cao do.
AM_XONG_BUOC = "tach"
AM_TOI_DICH = "hoan_thanh"

# Bao nhieu ngay di dung gio lien tiep thi goi la mot chuoi.
#
# Ba la con so co y chon thap: chuoi dai qua thi phan lon nguoi dung
# khong bao gio cham toi, va mot phan thuong khong bao gio nhan duoc
# thi khong phai phan thuong.
CHUOI_TOI_THIEU = 3


class TrangThai(str, Enum):
    """
    Trang thai ban dong hanh.

    BON gia tri, va ba trong so do la tich cuc. KHONG co gia tri nao
    the hien buon hay that vong - xem ghi chu dau file.
    """

    BINH_THUONG = "binh_thuong"    # mac dinh, khong co su kien gi
    VUI = "vui"                    # toi dich dung gio
    THONG_CAM = "thong_cam"        # vua khoi phuc mach sau phan tam
    TU_HAO = "tu_hao"              # chuoi ngay di dung gio


# Cau di kem tung trang thai. Ngan - day la phu hoa, khong phai thong
# tin dan duong.
CAU = {
    TrangThai.VUI: "Xong đúng giờ rồi.",
    TrangThai.THONG_CAM: "Không sao, mình đi tiếp nhé.",
    TrangThai.TU_HAO: "Bạn đã xong đúng giờ {n} ngày liền.",
    TrangThai.BINH_THUONG: "",
}


@dataclass(frozen=True)
class PhanHoi:
    """Mot lan phan hoi. Truong nao None thi khong phat gi o kenh do."""

    haptic: str | None = None
    am: str | None = None
    cau: str | None = None
    trang_thai: TrangThai = TrangThai.BINH_THUONG


@dataclass
class BoPhanHoi:
    """
    Theo doi tien do chang va sinh phan hoi.

    Khong tu doc `guide` - ben goi truyen `leg_index` vao. Ly do giong
    voi `mach.py`: hai cho cung theo doi mot thu se lech nhau.
    """

    _chang_truoc: int | None = field(default=None, repr=False)

    def xong_buoc(self, leg_index: int) -> PhanHoi | None:
        """
        Goi moi khung hinh. Tra phan hoi DUNG MOT LAN khi sang chang moi.

        Chi bao khi chi so TANG. Di lac rot ve chang truoc thi khong
        phai thanh tuu gi, va cang khong phai luc de khen.
        """
        truoc = self._chang_truoc
        self._chang_truoc = leg_index
        if truoc is None or leg_index <= truoc:
            return None
        return PhanHoi(haptic=HAPTIC_XONG_BUOC, am=AM_XONG_BUOC)


# --------------------------------------------------------------------
# ban dong hanh
# --------------------------------------------------------------------

def phan_ung(toi_dich: bool = False, dung_gio: bool = False,
             vua_khoi_phuc: bool = False, chuoi_ngay: int = 0) -> PhanHoi:
    """
    Trang thai ban dong hanh theo su kien vua xay ra.

    Thu tu uu tien: chuoi ngay > toi dich dung gio > vua khoi phuc.
    Chuoi dat cao nhat vi no hiem nhat.

    Toi dich MUON thi tra ve BINH_THUONG - khong phai trang thai buon.
    Im lang o day la co y: khong khen mot viec khong xay ra, nhung cung
    tuyet doi khong trach.
    """
    if toi_dich and dung_gio and chuoi_ngay >= CHUOI_TOI_THIEU:
        return PhanHoi(am=AM_TOI_DICH,
                       cau=CAU[TrangThai.TU_HAO].format(n=chuoi_ngay),
                       trang_thai=TrangThai.TU_HAO)
    if toi_dich and dung_gio:
        return PhanHoi(am=AM_TOI_DICH, cau=CAU[TrangThai.VUI],
                       trang_thai=TrangThai.VUI)
    if vua_khoi_phuc:
        # KHONG co am thanh o day.
        #
        # Nguoi dung vua bi phan tam va dang duoc dung lai ngu canh -
        # them mot tieng dong nua la them mot thu phai xu ly, dung luc
        # ho dang can it thu phai xu ly nhat.
        return PhanHoi(cau=CAU[TrangThai.THONG_CAM],
                       trang_thai=TrangThai.THONG_CAM)
    return PhanHoi()


# --------------------------------------------------------------------
# chuoi ngay di dung gio
# --------------------------------------------------------------------

@dataclass
class SoChuoi:
    """
    Dem so ngay di dung gio lien tiep.

    Luu theo NGAY, khong theo tung chuyen di: di tre mot chuyen trong
    ngay khong xoa ca ngay, va di dung mười chuyen trong mot ngay cung
    chi tinh mot.

    Ly do: dem theo chuyen di se thuong nguoi di nhieu va phat nguoi di
    it, ma so chuyen di mot ngay thi khong noi len dieu gi ve viec giu
    gio.
    """

    ngay_cuoi: str | None = None       # dang "2026-09-15"
    chuoi: int = 0

    def ghi(self, ngay: str, dung_gio: bool) -> int:
        """Ghi ket qua mot ngay. Tra do dai chuoi sau khi ghi."""
        if ngay == self.ngay_cuoi:
            return self.chuoi          # ngay nay da ghi roi

        if not dung_gio:
            self.ngay_cuoi = ngay
            self.chuoi = 0
            return 0

        self.chuoi = self.chuoi + 1 if self.ngay_cuoi is not None else 1
        self.ngay_cuoi = ngay
        return self.chuoi

    # --- luu va doc ---

    def to_json(self) -> dict:
        return {"ngay_cuoi": self.ngay_cuoi, "chuoi": self.chuoi}

    @staticmethod
    def from_json(d: dict) -> "SoChuoi":
        return SoChuoi(ngay_cuoi=d.get("ngay_cuoi"),
                       chuoi=int(d.get("chuoi") or 0))

    def luu(self, duong_dan: Path) -> None:
        duong_dan.parent.mkdir(parents=True, exist_ok=True)
        duong_dan.write_text(json.dumps(self.to_json(), ensure_ascii=False),
                             encoding="utf-8")

    @staticmethod
    def doc(duong_dan: Path) -> "SoChuoi":
        """So hong hoac chua co thi bat dau lai tu 0, khong lam sap app.

        Mat chuoi la mot phien toai; app khong chay duoc la mot loi.
        """
        try:
            return SoChuoi.from_json(
                json.loads(duong_dan.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError):
            return SoChuoi()


# --------------------------------------------------------------------
# TU THE "DANG BAN" CUA NHAN VAT
# --------------------------------------------------------------------
#
# Nhan vat khong ngoi im nhu tuong. Body doubling that la vay: nguoi
# ngoi canh ban o thu vien khong nhin ban - ho lam viec cua ho, va su
# co mat co tac dung chinh vi ho dang ban.
#
# Nhung doi tu the phai ROI RAC, khong phai hoat hinh chay lien tuc:
# chuyen dong lap lai trong tam nhin ngoai vi la nguon phan tam, ma day
# la app cho nguoi kho tap trung.
#
# Xem docs/NHAN_VAT_BRIEF.md muc 2.4 va 2.6.

# Khoang cach doi tu the, giay. Ngau nhien trong khoang chu khong deu:
# mot nhip deu dan tu no thanh cai dong ho, va nguoi dung se bat dau
# cho nhip tiep theo thay vi lam viec.
DOI_TU_THE_RANH_S = (180.0, 480.0)      # 3-8 phut, luc binh thuong

# Khi nguoi dung DANG TAP TRUNG thi gian ra.
#
# Day la dong dieu hoa nhin thay duoc: nhan vat di theo nhip cua nguoi
# dung thay vi ap nhip cua no len ho.
DOI_TU_THE_TAP_TRUNG_S = (480.0, 900.0)  # 8-15 phut

SO_TU_THE = 4


@dataclass
class BoDoiTuThe:
    """
    Quyet dinh khi nao nhan vat doi sang tu the khac.

    Khong tu doc dong ho - ben goi truyen `t` vao. Cung ly do voi
    `mach.BoTheoMach`: hai cho cung do mot thu se lech nhau.
    """

    so_tu_the: int = SO_TU_THE
    _tu_the: int = field(default=0, repr=False)
    _doi_luc: float | None = field(default=None, repr=False)
    _hat: int = field(default=12345, repr=False)

    @property
    def tu_the(self) -> int:
        return self._tu_the

    def _ngau_nhien(self, a: float, b: float) -> float:
        """So ngau nhien trong khoang, dung bo sinh rieng.

        Khong dung `random` toan cuc: mot module khac gieo lai hat giong
        se lam nhip cua nhan vat doi theo, va do la loai phu thuoc am
        rat kho tim.
        """
        self._hat = (1103515245 * self._hat + 12345) % (2 ** 31)
        return a + (b - a) * (self._hat / (2 ** 31))

    def cap_nhat(self, t: float, dang_tap_trung: bool) -> bool:
        """Goi moi goi tin. Tra True DUNG MOT LAN khi vua doi tu the."""
        if self._doi_luc is None:
            self._doi_luc = t + self._ngau_nhien(*DOI_TU_THE_RANH_S)
            return False

        if t < self._doi_luc:
            return False

        # Doi sang tu the KHAC tu the hien tai. Doi vao chinh no thi
        # nguoi dung khong thay gi, va lan doi do bi phi.
        if self.so_tu_the > 1:
            buoc = 1 + int(self._ngau_nhien(0, self.so_tu_the - 1))
            self._tu_the = (self._tu_the + buoc) % self.so_tu_the

        ranh = (DOI_TU_THE_TAP_TRUNG_S if dang_tap_trung
                else DOI_TU_THE_RANH_S)
        self._doi_luc = t + self._ngau_nhien(*ranh)
        return True
