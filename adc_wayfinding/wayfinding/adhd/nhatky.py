"""
NHAT KY - cua nguoi dung, va app KHONG DIEN GIAI no.

--------------------------------------------------------------------
RANH GIOI: GHI CHEP KHAC THEO DOI
--------------------------------------------------------------------

Khac biet quyet dinh ca phan phap ly lan phan thiet ke nam o mot cho:

    ghi chep   nguoi dung viet, doc lai, va tu rut ra ket luan
    theo doi   app do luong, cham diem, va rut ra ket luan HO nguoi dung

Cai thu nhat la mot quyen so. Cai thu hai la mot thiet bi y te.

Huong dan General Wellness cua FDA (ban 06/01/2026) neu dich danh "theo
doi trieu chung gan voi chan doan". Chu khoa la GAN VOI CHAN DOAN: cho
nao app quy mot ghi chep ve mot thang do lam sang, cho do no vuot ranh.

--------------------------------------------------------------------
NEN MODULE NAY KHONG CO PHEP TINH NAO
--------------------------------------------------------------------

Khong trung binh, khong xu huong, khong "tuan nay ban kem hon tuan
truoc". Khong co ham nao tra ve mot con so tong hop. Co mot bai test
canh gac dieu do.

    khong lam                        | vi sao
    ---------------------------------|------------------------------
    thang do lam sang (ASRS, DIVA)   | do la cong cu chan doan
    cham diem, tinh tong             | diem so la mot ket luan
    ve bieu do xu huong              | bieu do cung la mot ket luan
    goi y "ban nen..."               | do la loi khuyen lam sang

Thu duy nhat module lam voi noi dung nguoi dung viet la SAP XEP THEO
THOI GIAN va IN RA. Dung nhu mot quyen so.

--------------------------------------------------------------------
CAM XUC GHI BANG CHU CUA NGUOI DUNG, KHONG PHAI THANG DIEM
--------------------------------------------------------------------

Thang 1-5 tien cho app hon nhieu: de luu, de ve bieu do. Do chinh xac
la ly do khong dung no.

Mot con so chi co ich khi co gi do cong no lai - ma cong lai chinh la
thu khong duoc lam. Nen o day `the_nao` la CHU, do nguoi dung tu chon.
"met", "on", "nhu bi keo tung manh" deu hop le nhu nhau.

Chu cung trung thuc hon voi cai duoc ghi. "3 tren 5" gia vo la mot phep
do; "sang thi on, chieu thi khong" la thu nguoi dung that su biet.

--------------------------------------------------------------------
XUAT TEP: NGUOI DUNG TU LAM, VA APP KHONG GUI CHO AI
--------------------------------------------------------------------

Xem docs/FLOWY_THIET_KE.md muc 4.3(b). `xuat_van_ban()` tra ve mot
CHUOI. No khong mo tep, khong goi mang, va khong biet tep se di dau.

Nguoi dung co the muon dua so nay cho bac si - do la viec cua ho, va no
huu ich. Nhung buoc "gui" phai nam trong tay ho, khong nam trong code.

Xem them: module nay chay o PHIA DIEN THOAI, giong `nhacviec.py`. Bang
trong `loi_chung/bridge.py` ghi ro nhat ky cam xuc khong duoc di qua cau
noi.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

# Ghi chep ngan hon nay coi nhu bam nham.
MIN_KY_TU = 2

# Toi da bao nhieu muc giu lai.
#
# Khong phai gioi han ky thuat ma la gioi han RIENG TU: mot quyen so
# khong gioi han la mot ho so dai vo han ve mot nguoi. Cu hon nay thi
# muc cu nhat roi ra - nguoi dung xuat tep truoc neu muon giu.
TOI_DA_MUC = 500


@dataclass(frozen=True)
class Muc:
    """Mot muc nhat ky. Ca hai truong deu la CHU cua nguoi dung."""

    luc: float                  # giay, gio he thong
    noi_dung: str
    the_nao: str | None = None  # ho cam thay the nao, bang chu cua ho

    def dong(self) -> str:
        """Mot dong trong ban xuat. Khong them nhan xet nao."""
        gio = time.strftime("%Y-%m-%d %H:%M", time.localtime(self.luc))
        if self.the_nao:
            return f"{gio}  [{self.the_nao}] {self.noi_dung}"
        return f"{gio}  {self.noi_dung}"


@dataclass
class SoNhatKy:
    """Cac muc, theo thu tu viet. Khong co gi khac."""

    muc: list[Muc] = field(default_factory=list)

    def ghi(self, noi_dung: str, the_nao: str | None = None,
            luc: float | None = None) -> bool:
        """Them mot muc. Tra False neu noi dung rong."""
        if not noi_dung or len(noi_dung.strip()) < MIN_KY_TU:
            return False
        self.muc.append(Muc(
            luc=time.time() if luc is None else float(luc),
            noi_dung=noi_dung.strip(),
            the_nao=(the_nao.strip() or None) if the_nao else None))
        if len(self.muc) > TOI_DA_MUC:
            del self.muc[:-TOI_DA_MUC]
        return True

    def xoa(self, chi_so: int) -> bool:
        """Nguoi dung phai xoa duoc bat cu muc nao, bat cu luc nao.

        Quyen xoa la mot phan cua quyen so huu. Mot quyen so khong xe
        duoc trang la mot ho so.
        """
        if not (0 <= chi_so < len(self.muc)):
            return False
        self.muc.pop(chi_so)
        return True

    def xoa_het(self) -> None:
        self.muc.clear()

    def gan_day(self, so_muc: int = 10) -> list[Muc]:
        """Vai muc gan nhat, de nguoi dung DOC LAI - khong de app doc."""
        if so_muc <= 0:
            return []
        return list(self.muc[-so_muc:])

    # ---------------------------------------------- xuat

    def xuat_van_ban(self) -> str:
        """
        Toan bo so, dang van ban thuan.

        Tra ve CHUOI. Khong mo tep, khong goi mang. Nguoi dung quyet dinh
        chuoi nay di dau - ke ca khi cau tra loi la khong di dau ca.

        Van ban thuan chu khong phai dinh dang rieng: nguoi dung phai doc
        duoc so cua chinh ho ma khong can app nay.
        """
        dong = [m.dong() for m in self.muc]
        return "\n".join(dong) + ("\n" if dong else "")

    # ---------------------------------------------- luu va doc

    def to_json(self) -> list[dict]:
        return [{"luc": m.luc, "noi_dung": m.noi_dung, "the_nao": m.the_nao}
                for m in self.muc]

    @staticmethod
    def from_json(d: list) -> "SoNhatKy":
        """So hong thi bat dau lai tu trong, khong lam sap app."""
        so = SoNhatKy()
        if not isinstance(d, list):
            return so
        for m in d:
            if not isinstance(m, dict):
                continue
            try:
                so.ghi(str(m["noi_dung"]),
                       the_nao=(str(m["the_nao"])
                                if m.get("the_nao") else None),
                       luc=float(m["luc"]))
            except (KeyError, TypeError, ValueError):
                continue
        return so
