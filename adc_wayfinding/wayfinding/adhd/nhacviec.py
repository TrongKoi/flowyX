"""
LOI NHAC THEO GIO - do nguoi dung tu dat ten.

--------------------------------------------------------------------
DAY LA NHOM RUI RO PHAP LY CAO NHAT, VA CACH GO NO
--------------------------------------------------------------------

Huong dan "General Wellness: Policy for Low Risk Devices" cua FDA (ban
06/01/2026) neu DICH DANH "nhac thuoc hoac theo doi trieu chung gan voi
chan doan" la thu lam san pham roi vao dien thiet bi y te chiu quan ly.

Cach go khong phai la bo tinh nang, ma la DOI CHO QUYET DINH:

    App cung cap NANG LUC. Nguoi dung quyet dinh dung vao viec gi.

Nen module nay la mot bo nhac theo gio HOAN TOAN CHUNG. No khong biet,
khong hoi, va khong suy dien ve chan doan.

--------------------------------------------------------------------
MODULE NAY CHAY O PHIA DIEN THOAI
--------------------------------------------------------------------

Xem bang trong `loi_chung/bridge.py`: ten cac loi nhac nguoi dung tu dat
la thu KHONG BAO GIO duoc di qua cau noi.

Nen bo nhac nay khong duoc noi vao `run_flowy.py`. No song tron ven tren
may nguoi dung. Ban Python o day la BAN GOC de doi chieu - no chay duoc,
co test day du, va ban iOS hien thuc lai dung logic nay.

Do la ly do module chi cung cap phep tinh va cau truc, khong cung cap
duong mang nao.

--------------------------------------------------------------------
BON THU KHONG LAM, VA VI SAO
--------------------------------------------------------------------

    khong lam                     | vi sao
    ------------------------------|--------------------------------
    danh muc thuoc, ten hoat chat | biet ten thuoc la biet chan doan
    tinh lieu, nhac theo phac do  | do la huong dan dieu tri
    dem "ty le tuan thu"          | do la theo doi de quan ly benh
    canh bao bo lieu              | do la canh bao lam sang

Dieu thu ba dang chu y nhat: module nay KHONG GHI NHAN nguoi dung co
lam theo loi nhac hay khong. Khong co truong `da_lam`, khong co thong
ke.

Do la lua chon co chu dinh, khong phai thieu sot. Mot bo nhac co dem ty
le tuan thu la mot he theo doi; mot bo nhac khong dem chi la mot cai
dong ho biet noi.

--------------------------------------------------------------------
VA CO MOT LY DO THUC TE NUA
--------------------------------------------------------------------

Bang research cua nhom: mot thu nghiem ngau nhien tren 73 nguoi lon
trong 3 thang cho thay mot app nhac thuoc KHONG cai thien co y nghia chi
so so huu thuoc.

Tuc la ngay ca khi bo qua phan phap ly, viec dem tuan thu cung khong
chung minh duoc la co tac dung. Bo no di la bo mot thu vua rui ro vua
chua co bang chung.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Ten ngan hon nay coi nhu chua nhap. Cung nguong voi `phien.MIN_KY_TU`.
MIN_KY_TU = 3

# Loi nhac den han roi bao nhieu phut thi thoi, coi nhu da lo.
#
# Khong bao mai: mot loi nhac hien lien tuc se bi tat di, va luc do moi
# loi nhac khac cung mat theo.
CUA_SO_PHUT = 30.0


@dataclass(frozen=True)
class LoiNhac:
    """
    Mot loi nhac. `ten` la chuoi TU DO - nguoi dung go gi cung duoc.

    Module khong phan tich chuoi nay, khong doi chieu voi danh muc nao,
    va khong luu y nghia nao khac ngoai chinh chuoi do.
    """

    ten: str
    gio: float              # phut tinh tu nua dem
    lap_lai_hang_ngay: bool = True

    def cau(self) -> str:
        """Cau doc len. Chi nhac lai dung ten nguoi dung da dat."""
        return f"Đã tới giờ: {self.ten}."


@dataclass
class SoNhac:
    """Danh sach loi nhac, va viec theo doi cai nao da bao roi."""

    danh_sach: list[LoiNhac] = field(default_factory=list)

    # Chi so cac loi nhac DA BAO trong ngay hom nay.
    #
    # Day la thu duy nhat module ghi nho ve qua khu, va no chi de tranh
    # bao hai lan. No KHONG phai ban ghi ve hanh vi nguoi dung.
    _da_bao: set[int] = field(default_factory=set, repr=False)
    _ngay: str | None = field(default=None, repr=False)

    def them(self, ten: str, gio: float,
             lap_lai_hang_ngay: bool = True) -> bool:
        """Them mot loi nhac. Tra False neu ten qua ngan hoac gio sai."""
        if not ten or len(ten.strip()) < MIN_KY_TU:
            return False
        if not (0.0 <= gio < 1440.0):
            return False
        self.danh_sach.append(LoiNhac(ten=ten.strip(), gio=float(gio),
                                      lap_lai_hang_ngay=lap_lai_hang_ngay))
        return True

    def xoa(self, chi_so: int) -> bool:
        if not (0 <= chi_so < len(self.danh_sach)):
            return False
        self.danh_sach.pop(chi_so)
        self._da_bao = {i if i < chi_so else i - 1
                        for i in self._da_bao if i != chi_so}
        return True

    def den_han(self, bay_gio: float, ngay: str) -> LoiNhac | None:
        """
        Loi nhac can bao ngay bay gio, hoac None.

        `ngay` dang "2026-09-15". Sang ngay moi thi cac loi nhac lap lai
        duoc bao lai - nen phai biet hom nay la ngay nao.
        """
        if ngay != self._ngay:
            self._ngay = ngay
            self._da_bao.clear()

        for i, ln in enumerate(self.danh_sach):
            if i in self._da_bao:
                continue
            tre = bay_gio - ln.gio
            if 0.0 <= tre <= CUA_SO_PHUT:
                self._da_bao.add(i)
                return ln
        return None

    # ---------------------------------------------- luu va doc
    #
    # Module KHONG tu ghi ra dia. Ten loi nhac la noi dung ca nhan, va
    # nguoi dung co the dat ten bat cu gi - ke ca thu rieng tu nhat.
    # Dien thoai so huu tep luu; xem docs/FLOWY_THIET_KE.md muc 7.3.

    def to_json(self) -> list[dict]:
        return [{"ten": ln.ten, "gio": ln.gio,
                 "lap_lai": ln.lap_lai_hang_ngay}
                for ln in self.danh_sach]

    @staticmethod
    def from_json(d: list) -> "SoNhac":
        """So hong thi bat dau lai tu trong, khong lam sap app."""
        so = SoNhac()
        if not isinstance(d, list):
            return so
        for m in d:
            if not isinstance(m, dict):
                continue
            try:
                so.them(str(m["ten"]), float(m["gio"]),
                        bool(m.get("lap_lai", True)))
            except (KeyError, TypeError, ValueError):
                continue
        return so
