"""
GIU MACH CONG VIEC - muc dich va khoi phuc sau phan tam.

--------------------------------------------------------------------
HAI VIEC, MOT SOI CHI
--------------------------------------------------------------------

Module nay giu MOT thu: soi chi noi "toi dang lam gi, de lam gi". Hai
tinh nang deu la hai dau cua soi chi do.

  nho muc dich   - hoi mot cau luc dat viec, nhac lai luc xong
  khoi phuc mach - dung yen lau roi di lai thi DUNG LAI ngu canh truoc

Vi sao gop mot file: ca hai deu doc cung mot mieng du lieu (`muc_dich`)
va deu vo nghia neu thieu no. Tach ra hai file se thanh hai file cung
so huu mot bien.

--------------------------------------------------------------------
VI SAO KHOI PHUC MACH LA TINH NANG, KHONG PHAI TRUONG HOP HIEM
--------------------------------------------------------------------

Dung lai giua duong - noi chuyen, nhin dien thoai, nghi ra viec khac -
roi quen mat dang di dau va de lam gi, la chuyen xay ra HANG NGAY voi
nguoi ADHD, khong phai su co.

Hanh vi mac dinh cua moi he chi duong la: nguoi dung dung lai, he thong
im; nguoi dung di lai, he thong noi "rẽ phải". Cau do gia dinh nguoi
dung VAN CON giu ngu canh trong dau. Voi dung nhom nguoi ma san pham
nay phuc vu, gia dinh do sai.

Nen cau dau tien sau mot khoang dung lau PHAI co du ba phan:

    (a) dang lam gi      -> "Bạn đang làm dở bài tập chương 3"
    (b) de lam gi        -> "để nộp đơn xin nghỉ"
    (c) viec ngay truoc mat -> "Còn 2 bước. Rẽ phải ở đây."

Bo (a) hoac (b) di thi quay ve dung hanh vi ma tinh nang nay sinh ra de
sua. Rut gon la hong.

--------------------------------------------------------------------
NGUONG 90 GIAY
--------------------------------------------------------------------

Duoi nguong nay thi dung lai la chuyen binh thuong trong luc di: cho
thang may, nhuong duong, chinh lai day deo. Dung lai ba chuc giay
khong lam ai quen minh dang di dau.

Tren nguong thi da du lau de mach bi dut. Con so nay NEN do lai bang
nguoi dung that - no la uoc luong, khong phai ket qua thuc nghiem.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Dung yen lau hon nguong nay thi coi la da dut mach.
NGUONG_PHAN_TAM_S = 90.0

# Tu choi tra loi cau hoi muc dich. Nhan ra de KHONG hoi lai.
TU_CHOI = ("không", "thôi", "bỏ qua", "khỏi", "không cần", "kệ")

# Cau tra loi ngan hon nay coi nhu khong phai muc dich that.
#
# Nguoi dung lam bam mot tieng, hoac bo nhan dang giong noi bat duoc
# tieng on, se ra mot chuoi mot hai ky tu. Luu no lai roi doc lai luc
# toi noi se thanh mot cau vo nghia.
MIN_KY_TU_MUC_DICH = 3


@dataclass
class ViecDangLam:
    """Mot chuyen di, kem muc dich neu nguoi dung co noi."""

    ten_viec: str
    muc_dich: str | None = None
    da_hoi_muc_dich: bool = False


def cau_hoi_muc_dich() -> str:
    """Hoi mot lan, khong bat buoc tra loi."""
    return "Bạn tới đó để làm gì?"


def nhan_muc_dich(cd: ViecDangLam, loi_noi: str | None) -> bool:
    """
    Ghi nhan cau tra loi. Tra True neu da luu duoc mot muc dich.

    Dau vao khong dung duoc - im lang, tu choi, hoac qua ngan - deu
    danh dau DA HOI roi thoi. Hoi lai la lam phien, va lam phien thi
    nguoi dung tat tinh nang.
    """
    cd.da_hoi_muc_dich = True
    if not loi_noi:
        return False

    tho = loi_noi.strip()
    if len(tho) < MIN_KY_TU_MUC_DICH:
        return False
    if tho.lower() in TU_CHOI:
        return False

    cd.muc_dich = tho
    return True


def cau_xong_viec(cd: ViecDangLam) -> str:
    """
    Cau bao da toi dich.

    Co muc dich thi nhac lai - day la luc no huu ich nhat, vi nguoi
    dung vua di mot quang va rat co the da quen. Khong co thi noi gon,
    KHONG de cho trong va khong hoi lai.
    """
    if cd.muc_dich:
        return f"Xong {cd.ten_viec} rồi. Bạn làm việc này để {cd.muc_dich}."
    return f"Xong {cd.ten_viec} rồi."


def cau_khoi_phuc(cd: ViecDangLam, chi_dan: str | None = None,
                  buoc_con_lai: int | None = None) -> str:
    """
    Cau dau tien sau mot khoang dung lau. Phai dung lai ngu canh.

    Ba phan theo dung thu tu: dang di dau, de lam gi, roi moi toi viec
    truoc mat. Dao thu tu se lam phan chi dan bi troi noi giua mot cau
    dai - ma chi dan la thu duy nhat can hanh dong ngay.
    """
    phan = [f"Bạn đang làm dở {cd.ten_viec}"]
    if cd.muc_dich:
        phan.append(f" để {cd.muc_dich}")
    phan.append(".")

    if buoc_con_lai is not None and buoc_con_lai > 0:
        phan.append(f" Còn {buoc_con_lai} bước.")
    if chi_dan:
        phan.append(f" {chi_dan}")
    return "".join(phan)


@dataclass
class BoTheoMach:
    """
    Theo doi dut mach: dung yen lau, roi di lai.

    Khong tu do gi ca - no nhan vao ket luan "dang di hay dung yen" tu
    ben ngoai. Ly do: `power.py` da co san bo phat hien dung yen, va
    hai cho cung do mot thu se lech nhau roi sinh loi kho tim.
    """

    nguong_s: float = NGUONG_PHAN_TAM_S
    _yen_tu: float | None = field(default=None, repr=False)
    _dang_yen: bool = field(default=False, repr=False)

    def cap_nhat(self, t: float, dang_di: bool) -> bool:
        """
        Tra True DUNG MOT LAN, tai khoanh khac vua di lai sau khi dung
        lau hon nguong.

        `t` tinh bang giay. `dang_di` do ben goi quyet dinh.

        ----------------------------------------------------------------
        DO CA O LUC QUAY LAI, KHONG CHI O LUC DANG VANG
        ----------------------------------------------------------------

        Ban dau lop nay chi bat `_dang_yen` khi nhan duoc MOT GOI TIN NUA
        trong luc vang. Voi ban dieu huong do la dung: dien thoai deo
        tren nguc, luon gui.

        Voi Flowy thi khong. "Vang" o day nghia la NGUOI DUNG DA MO APP
        KHAC, va he dieu hanh hoan toan co the treo tien trinh nay trong
        suot khoang do - khong mot goi tin nao duoc gui.

        Ket qua la truong hop CAN NHAT lai la truong hop im lang: di
        cang lau, cang it kha nang co goi tin giua chung, cang chac chan
        khong co cau dung lai ngu canh nao.

        Nen goi tin dau tien khi quay lai cung phai duoc do.
        """
        if not dang_di:
            if self._yen_tu is None:
                self._yen_tu = t
            elif t - self._yen_tu >= self.nguong_s:
                self._dang_yen = True
            return False

        # dang di
        du_lau = (self._yen_tu is not None
                  and t - self._yen_tu >= self.nguong_s)
        vua_dut_mach = self._dang_yen or du_lau
        self._yen_tu = None
        self._dang_yen = False
        return vua_dut_mach

    @property
    def dang_dut_mach(self) -> bool:
        """Da dung du lau de coi la dut mach, va van dang dung."""
        return self._dang_yen
