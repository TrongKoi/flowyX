"""
PHIEN LAM VIEC - y dinh thuc thi va cac buoc nho.

--------------------------------------------------------------------
Y DINH THUC THI: BA O BAT BUOC
--------------------------------------------------------------------

Tai lieu CBT cho nguoi lon ADHD neu cong thuc: mot y dinh thuc thi phai
noi ro CHINH XAC KHI NAO va O DAU viec se dien ra. Vi du trong tai lieu:

    "Sau bua toi thu Ba, toi se danh 15 phut hoan thanh ban ghi suy nghi
     tai ban bep."

Ba thanh phan: KHI NAO + O DAU + VIEC GI.

Nen khi nguoi dung them mot viec, module nay KHONG CHO LUU neu thieu mot
o nao. Rang buoc do nghe phien, va no chinh la can thiep:

    Mot y dinh mo ho la thu khong khoi dong duoc. Buoc nguoi dung lam no
    cu the TRUOC, la go te liet truoc khi no kip hinh thanh.

Day cung la ly do module nay khong co ham "them viec nhanh". Them nhanh
thi ra mot dong chu mo ho, va mot dong chu mo ho khong phai la mot viec
lam duoc.

--------------------------------------------------------------------
BUOC DAU PHAI NHO TOI MUC BUON CUOI
--------------------------------------------------------------------

Buoc dau khong phai "viet mo bai" ma "mo tep len".

Ly do: phan kho nhat cua te liet la VUOT QUA BUOC DAU. Mot buoc dau lon
thi chinh no lai la mot te liet nho. Con mot buoc dau tam thuong thi
khong con gi de so, va lam xong no la da o trong viec roi.

Module nay khong ep duoc dieu do - no khong biet "mo tep len" nho hon
"viet mo bai". Nhung `goi_y_buoc_dau()` hoi nguoi dung dung cau hoi do,
va do la thu re nhat lam duoc.

--------------------------------------------------------------------
KHONG DIEN GIAI, KHONG CHAM DIEM
--------------------------------------------------------------------

Module nay ghi lai nhung gi nguoi dung nhap, va dem xem den buoc thu
may. No khong danh gia, khong xep loai, khong so sanh giua cac phien.

Xem docs/FLOWY_THIET_KE.md muc 4.4 ve ly do: cham diem la buoc dau cua
danh gia lam sang, va do la ranh gioi khong duoc vuot.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum

# Cau tra loi ngan hon nay coi nhu chua nhap.
#
# Nguoi dung lam bam mot tieng, hoac bo nhan dang giong noi bat duoc
# tieng on, se ra mot chuoi mot hai ky tu. Luu no lai roi doc len sau
# se thanh mot cau vo nghia. Cung nguong voi `mach.MIN_KY_TU_MUC_DICH`.
MIN_KY_TU = 3


class ThieuO(str, Enum):
    """O nao con thieu trong y dinh thuc thi."""

    KHI_NAO = "khi_nao"
    O_DAU = "o_dau"
    VIEC_GI = "viec_gi"


# Cau hoi cho tung o. Hoi rieng tung cai chu khong gop mot o to: mot o
# to thi nguoi dung viet mot cau mo ho vao do, va ta quay ve diem xuat
# phat.
CAU_HOI = {
    ThieuO.VIEC_GI: "Bạn định làm gì?",
    ThieuO.KHI_NAO: "Khi nào bạn sẽ làm?",
    ThieuO.O_DAU: "Bạn sẽ làm ở đâu?",
}


@dataclass(frozen=True)
class YDinh:
    """Mot y dinh thuc thi hoan chinh."""

    viec_gi: str
    khi_nao: str
    o_dau: str

    def cau(self) -> str:
        """Doc lai y dinh thanh mot cau.

        Doc lai la mot phan cua can thiep, khong phai trang tri: nghe
        chinh minh noi ra mot ke hoach cu the khac han voi nghi ve no.
        """
        return f"{self.khi_nao}, bạn sẽ {self.viec_gi} tại {self.o_dau}."


def thieu_gi(viec_gi: str | None, khi_nao: str | None,
             o_dau: str | None) -> list[ThieuO]:
    """Liet ke cac o con thieu. Rong nghia la du."""
    ra = []
    for o, gt in ((ThieuO.VIEC_GI, viec_gi),
                  (ThieuO.KHI_NAO, khi_nao),
                  (ThieuO.O_DAU, o_dau)):
        if gt is None or len(gt.strip()) < MIN_KY_TU:
            ra.append(o)
    return ra


def tao_y_dinh(viec_gi: str | None, khi_nao: str | None,
               o_dau: str | None) -> YDinh | None:
    """Tao y dinh, hoac None neu chua du ba o.

    Tra None chu khong nem ngoai le: thieu o la chuyen BINH THUONG trong
    luc nguoi dung dang nhap dan, khong phai loi.
    """
    if thieu_gi(viec_gi, khi_nao, o_dau):
        return None
    return YDinh(viec_gi=viec_gi.strip(),      # type: ignore[union-attr]
                 khi_nao=khi_nao.strip(),      # type: ignore[union-attr]
                 o_dau=o_dau.strip())          # type: ignore[union-attr]


def goi_y_buoc_dau() -> str:
    """Cau hoi go te liet, hoi dung luc nguoi dung dang kep.

    Khong hoi "chia viec nay ra di" - do la mot viec nua phai lam. Hoi
    dung MOT buoc, va ep no nho.
    """
    return "Bước nhỏ nhất bạn làm được ngay bây giờ là gì?"


@dataclass
class Phien:
    """Mot phien lam viec dang chay."""

    y_dinh: YDinh
    buoc: list[str] = field(default_factory=list)
    _chi_so: int = field(default=0, repr=False)
    bat_dau_luc: float = field(default_factory=time.time)
    ket_thuc_luc: float | None = None

    # Gio can xong, phut tinh tu nua dem. None nghia la khong hen gio -
    # va luc do lop neo thoi gian khong len tieng.
    gio_hen: float | None = None

    # Nguoi dung TU TUYEN BO la xong.
    #
    # Khac voi viec di het cac buoc: rat nhieu phien khong co buoc nao
    # ca - nguoi dung noi viec gi / khi nao / o dau, bat dau, lam, roi
    # bam Ket thuc. Do la duong di thuong gap nhat.
    #
    # Khong co co nay thi `xong` cua mot phien khong buoc KHONG BAO GIO
    # thanh True, va nut Ket thuc im lang khong lam gi.
    _da_tuyen_bo_xong: bool = field(default=False, repr=False)

    @property
    def buoc_hien_tai(self) -> str | None:
        if 0 <= self._chi_so < len(self.buoc):
            return self.buoc[self._chi_so]
        return None

    @property
    def chi_so(self) -> int:
        return self._chi_so

    @property
    def con_lai(self) -> int:
        return max(0, len(self.buoc) - self._chi_so)

    @property
    def xong(self) -> bool:
        """Phien da xong chua.

        Hai duong dan toi day:

            di het cac buoc      -> `xong_buoc()` goi den buoc cuoi
            tu tuyen bo la xong  -> `ket_thuc()`

        Dieu kien `bool(self.buoc)` o duong dau la co y: mot phien vua
        tao, chua co buoc nao, khong phai la mot phien da xong.
        """
        if self._da_tuyen_bo_xong:
            return True
        return self._chi_so >= len(self.buoc) and bool(self.buoc)

    def ket_thuc(self) -> None:
        """Nguoi dung bam Ket thuc.

        Dung ngay, ke ca khi con buoc chua danh dau. Ho biet ro hon app
        ve viec ho da lam xong hay chua, va bat ho danh dau tung buoc
        con lai truoc khi duoc dung la mot viec vo nghia.
        """
        self._da_tuyen_bo_xong = True
        if self.ket_thuc_luc is None:
            self.ket_thuc_luc = time.time()

    def them_buoc(self, ten: str) -> bool:
        """Them mot buoc. Tra False neu chuoi qua ngan."""
        if not ten or len(ten.strip()) < MIN_KY_TU:
            return False
        self.buoc.append(ten.strip())
        return True

    def xong_buoc(self) -> bool:
        """Danh dau xong buoc hien tai. Tra False neu khong con buoc nao.

        Chi tien MOT buoc moi lan goi. Khong co ham "nhay toi buoc N":
        nhay qua buoc la mat luon phan hoi cua nhung buoc bi bo, ma phan
        hoi tung buoc chinh la co che.
        """
        if self._chi_so >= len(self.buoc):
            return False
        self._chi_so += 1
        if self.xong and self.ket_thuc_luc is None:
            self.ket_thuc_luc = time.time()
        return True

    @property
    def da_lam_giay(self) -> float:
        """So giay da bo ra cho phien nay."""
        het = self.ket_thuc_luc if self.ket_thuc_luc else time.time()
        return max(0.0, het - self.bat_dau_luc)

    def cau_bat_dau(self) -> str:
        """Cau doc luc bat dau phien."""
        if self.buoc:
            return f"{self.y_dinh.cau()} Bước đầu: {self.buoc[0]}."
        return self.y_dinh.cau()
