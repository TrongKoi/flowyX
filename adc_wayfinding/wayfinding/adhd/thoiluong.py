"""
SO THOI LUONG - hoc tu chinh nguoi dung, thay vi tin loi ho uoc.

--------------------------------------------------------------------
VI SAO KHONG HOI ROI TIN
--------------------------------------------------------------------

Cach hien nhien la hoi "viec nay mat bao lau?" roi dung con so do.

Nhung uoc luong sai thoi luong CHINH LA trieu chung can chua. Hoi roi
tin la xay ngay tren cho dang gay.

Nen module nay lam ba giai doan:

    lan 1    Nguoi dung uoc. Ghi lai ca con so do, VA do thoi gian that.
    lan 2    Noi ra khoang cach: "Lan truoc ban uoc 20 phut, thuc te 35."
             -> chinh cau nay la can thiep, khong phai cai dong ho
    lan 3+   Dung so do that, nguoi dung chi xac nhan.

Cau o lan 2 lam duoc thu ma mot dong ho dem nguoc khong lam duoc: no
HUAN LUYEN cam nhan thoi gian bang chinh du lieu cua nguoi dung.

Day cung la "co che hoc" ma cac khao sat noi phan lon app ADHD dang
thieu - chung dung yen sau lan cai dat dau.

--------------------------------------------------------------------
TRUNG VI, KHONG PHAI TRUNG BINH
--------------------------------------------------------------------

Mot lan bi gian doan bat thuong - mat dien, co nguoi goi - keo trung
binh lech han. Trung vi bo qua cac lan ca biet do.

Cung ly do da dung o `backdrop.py` cua ban dieu huong, va o
`DepthSampler` ben Android.

--------------------------------------------------------------------
MODULE NAY KHONG TU GHI RA DIA
--------------------------------------------------------------------

Xem docs/FLOWY_THIET_KE.md muc 7.3: du lieu ca nhan o lai tren may
nguoi dung, va laptop khong ghi gi xuong dia.

Ten cong viec la noi dung ca nhan. Nen module nay chi cung cap CAU TRUC
va PHEP TINH; viec luu nam o phia dien thoai. `to_json()` va
`from_json()` co san de dien thoai tu luu va gui lai phan can thiet.

Day khong phai su can trong thua: mot so ghi "toi hay mat 3 tieng cho
viec dang le 30 phut" la thu rat rieng tu.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Lay trung vi cua toi da bay nhieu lan gan nhat.
#
# Du de loc ca biet, va du ngan de theo kip khi nguoi dung that su nhanh
# len o mot loai viec. Lay het lich su thi mot thang sau van bi keo boi
# nhung lan vung ve dau tien.
SO_LAN_XET = 5

# Chenh lech duoi muc nay thi khong noi gi.
#
# Uoc 20 thuc te 22 la uoc DUNG. Noi ra mot chenh lech khong dang ke se
# lam cau canh bao mat gia tri o nhung lan that su lech nhieu.
CHENH_DANG_KE_PHUT = 5.0


@dataclass(frozen=True)
class LanDo:
    """Mot lan lam viec da xong."""

    uoc_phut: float | None      # nguoi dung uoc bao nhieu. None = khong uoc
    that_phut: float            # do duoc bao nhieu


@dataclass
class SoThoiLuong:
    """Lich su thoi luong, theo tung ten cong viec."""

    ban_ghi: dict[str, list[LanDo]] = field(default_factory=dict)

    # ------------------------------------------------ ghi va doc

    def ghi(self, ten_viec: str, that_phut: float,
            uoc_phut: float | None = None) -> None:
        """Ghi mot lan da xong."""
        if not ten_viec or that_phut <= 0:
            return
        self.ban_ghi.setdefault(ten_viec, []).append(
            LanDo(uoc_phut=uoc_phut, that_phut=float(that_phut)))

    def so_lan(self, ten_viec: str) -> int:
        return len(self.ban_ghi.get(ten_viec, ()))

    def uoc_luong(self, ten_viec: str) -> float | None:
        """Thoi luong nen dung cho lan toi. None neu chua co so lieu."""
        lan = self.ban_ghi.get(ten_viec)
        if not lan:
            return None
        gan_day = sorted(d.that_phut for d in lan[-SO_LAN_XET:])
        giua = len(gan_day) // 2
        if len(gan_day) % 2:
            return gan_day[giua]
        return (gan_day[giua - 1] + gan_day[giua]) / 2.0

    # ------------------------------------------------ cau noi

    def cau_doi_chieu(self, ten_viec: str) -> str | None:
        """
        Cau noi ra khoang cach giua uoc luong va thuc te cua LAN TRUOC.

        Tra None khi khong co gi dang noi: chua co lich su, lan truoc
        khong uoc, hoac uoc gan dung.

        Cau nay chi NEU SO LIEU, khong ket luan gi ve nguoi dung. "Ban
        hay uoc thieu" la mot nhan xet ve tinh cach; "lan truoc 20, thuc
        te 35" la mot con so ho tu doi chieu duoc.
        """
        lan = self.ban_ghi.get(ten_viec)
        if not lan:
            return None
        cuoi = lan[-1]
        if cuoi.uoc_phut is None:
            return None
        chenh = abs(cuoi.that_phut - cuoi.uoc_phut)
        if chenh < CHENH_DANG_KE_PHUT:
            return None
        return (f"Lần trước bạn ước {_phut(cuoi.uoc_phut)} phút, "
                f"thực tế {_phut(cuoi.that_phut)} phút.")

    def cau_goi_y(self, ten_viec: str) -> str | None:
        """Cau de nghi dung so do that cho lan nay."""
        u = self.uoc_luong(ten_viec)
        if u is None:
            return None
        return f"Những lần trước việc này mất khoảng {_phut(u)} phút."

    # ------------------------------------------------ luu va doc

    def to_json(self) -> dict:
        return {ten: [{"uoc": d.uoc_phut, "that": d.that_phut} for d in ds]
                for ten, ds in self.ban_ghi.items()}

    @staticmethod
    def from_json(d: dict) -> "SoThoiLuong":
        """So hong thi bat dau lai tu trong, khong lam sap app.

        Mat lich su la mot phien toai; app khong chay duoc la mot loi.
        """
        so = SoThoiLuong()
        if not isinstance(d, dict):
            return so
        for ten, ds in d.items():
            if not isinstance(ten, str) or not isinstance(ds, list):
                continue
            ra = []
            for m in ds:
                try:
                    that = float(m["that"])
                except (KeyError, TypeError, ValueError):
                    continue
                uoc = m.get("uoc")
                ra.append(LanDo(
                    uoc_phut=float(uoc) if isinstance(uoc, (int, float))
                    else None,
                    that_phut=that))
            if ra:
                so.ban_ghi[ten] = ra
        return so


def _phut(x: float) -> str:
    """Lam tron ve phut. Nua phut khong giup nguoi dung hinh dung hon."""
    return str(max(1, int(round(x))))
