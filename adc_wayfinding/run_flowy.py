#!/usr/bin/env python3
"""
Chay Flowy - dien thoai lam MAN HINH va DAU VAO, laptop lam BO NAO.

Chay:
    python3 run_flowy.py
    python3 run_flowy.py --gio-hen 14:00 --viec "Nop bao cao"

Roi mo dia chi hien tren man hinh tren dien thoai.

Kiem thu KHONG CAN dien thoai:
    python3 run_flowy.py                    # cua so 1
    python3 tools/phone_sim_flowy.py        # cua so 2

--------------------------------------------------------------------
VONG LAP NAY LAM GI
--------------------------------------------------------------------

Bon viec, theo dung thu tu uu tien khi nhieu viec cung muon len tieng:

    1. Tra loi cu cham vao nhan vat   - nguoi dung vua hoi, phai tra loi
    2. Dung lai ngu canh sau phan tam - cau nay bi nuot thi mat han
    3. Phan hoi xong buoc             - rung nhe, khong phai cau noi
    4. Nhac moc thoi gian             - qua bo dem chong lap

--------------------------------------------------------------------
NHAN VAT KHONG BAO GIO CHU DONG BAT CHUYEN
--------------------------------------------------------------------

Xem docs/NHAN_VAT_BRIEF.md muc 2.4. Cu cham la loi moi DUY NHAT de app
len tieng voi mot cau hoi.

Phan biet hai thu de lan:

    doi net mat  - thu dong, phan anh su kien, khong doi hoi gi
    tuong tac    - CHI khi duoc cham, va no doi mot cau tra loi

Nen khi nguoi dung ket lau o mot buoc, app chi DIU NET MAT. No khong noi
gi ca. Nguoi dung cham vao thi moi co cau hoi - va cau hoi do tuy luc ho
dang ket, dang bi keo di, hay vua xong. Xem `adhd/cauhoi.py`.

--------------------------------------------------------------------
LAPTOP KHONG GHI GI XUONG DIA
--------------------------------------------------------------------

Xem docs/FLOWY_THIET_KE.md muc 7.3. Du lieu ca nhan o lai tren may nguoi
dung; laptop chi la bo nao tam thoi. Co mot bai test canh gac dieu nay.

Ngoai le duy nhat: `--chuoi` ghi so ngay di dung gio, va do la mot con
so dem, khong phai noi dung ca nhan.
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path

from wayfinding.loi_chung.announce import ReplyComposer
from wayfinding.loi_chung.bridge import (LENH_BAT_DAU, LENH_KET_THUC,
                                         LENH_TAM_DUNG, LENH_TIEP_TUC,
                                         LENH_VIEC_MOI, LENH_XONG_BUOC,
                                         MUC_NHAC_MOC, BridgeReply,
                                         BridgeServer, PhoneUpdate)
from wayfinding.loi_chung.speech import HAPTIC_PATTERNS
from wayfinding.adhd import (cauhoi, dongvien, mach, phien, thoiluong,
                             timeblind)

# --------------------------------------------------------------------
# NHIP GUI GOI TIN
# --------------------------------------------------------------------
#
# Thay cho `power.py` cua ban dieu huong - lop do nhan `gan_nhat_m` va
# `da_di_m`, deu la so lieu cua he dan duong, nen khong chuyen sang day
# duoc.
#
# Flowy khong co viec nang nao chay moi goi tin, nen quy tac chi con mot
# dong: dang lam viec thi gui day hon, khong thi gui thua. Muc dich la
# tiet kiem pin, khong phai giam do tre.
NHIP_DANG_LAM_MS = 500
NHIP_RANH_MS = 2000

# Net mat diu xuong giu bao lau roi tro ve binh thuong, giay.
#
# Du lau de nguoi dung ngang len la con thay, va du ngan de no khong
# thanh net mat mac dinh. Mot net mat thong cam dinh lai vinh vien thi
# luc that su can no khong ai thay khac biet.
GIU_NET_MAT_S = 25.0


def _doc_gio(s: str | None) -> float | None:
    """GIO:PHUT -> phut tinh tu nua dem. Sai dinh dang thi tra None."""
    if not s:
        return None
    try:
        gio, phut = s.split(":")
        g, ph = int(gio), int(phut)
    except (ValueError, AttributeError):
        return None
    if not (0 <= g < 24 and 0 <= ph < 60):
        return None
    return g * 60.0 + ph


class Flowy:
    """
    Trang thai mot phien, va quy tac quyet dinh noi gi.

    Tach khoi `main()` de kiem thu duoc ma khong can mo cong mang.
    """

    def __init__(self, gio_hen: float | None = None, ten_viec: str = "",
                 muc_dich: str = "", duong_dan_chuoi: Path | None = None):
        self.gio_hen = gio_hen
        self.ten_viec = ten_viec
        self.muc_dich = muc_dich or None

        # Ten MOC phai xong truoc ("Lớp học", "Hạn nộp") - khac voi ten
        # cong viec. Chua co duong nhap rieng nen tam de trong.
        self.ten_su_kien: str | None = None

        # So thoi luong do DIEN THOAI so huu. Laptop nhan phan can cho
        # lan tinh nay roi thoi - no khong ghi gi xuong dia.
        self.so_thoi_luong = thoiluong.SoThoiLuong()
        self.uoc_nguoi_dung: float | None = None

        # Y dinh thuc thi dang gom. Ba o, hoi tung o mot.
        self._nhap: dict[str, str | None] = {
            "viec_gi": ten_viec or None, "khi_nao": None, "o_dau": None}
        self.phien: phien.Phien | None = None

        self.theo_mach = mach.BoTheoMach()
        self.bo_cau_hoi = cauhoi.BoCauHoi()
        self.bo_do_ket = cauhoi.BoDoKet()
        self.bo_phan_hoi = dongvien.BoPhanHoi()
        self.bo_tu_the = dongvien.BoDoiTuThe()
        self.trang_thai_ban = dongvien.TrangThai.BINH_THUONG

        self.muc_nhac = "vua"
        self.bo_nhac = (timeblind.BoNhacGio(gio_hen, MUC_NHAC_MOC[self.muc_nhac])
                        if gio_hen is not None else None)

        # Tam dung. Giu TRANG THAI qua cac goi tin - ban truoc chi coi
        # `tam_dung` la tin hieu cua dung mot goi tin, nen nut Tam dung
        # (neu co) chi co tac dung trong nua giay.
        self.dang_tam_dung = False
        self._tam_dung_tu: float | None = None
        self._tong_tam_dung = 0.0

        # Buoc nguoi dung noi TRUOC khi bam Bat dau. Ban truoc bo roi
        # chung: du ba o roi ma chua co phien thi cau noi khong di dau.
        self._buoc_cho: list[str] = []
        self.composer = ReplyComposer()

        self._duong_dan_chuoi = duong_dan_chuoi
        self.so_chuoi = (dongvien.SoChuoi.doc(duong_dan_chuoi)
                         if duong_dan_chuoi else dongvien.SoChuoi())
        self._da_bao_xong = False

        # App co o tien canh o goi tin TRUOC. Can de biet luc nao la
        # canh RA KHOI app, chu khong phai dang o ngoai.
        self._tren_man_hinh_truoc = True

        # Net mat diu xuong GIU DEN LUC NAO. None la khong diu.
        #
        # Phai co han: mot net mat thong cam dinh lai vinh vien sau mot
        # lan phan tam thi khong con nghia gi nua - no thanh net mat mac
        # dinh, va luc that su can no thi khong ai thay khac biet.
        self._diu_den: float | None = None

    # ---------------------------------------------- gom y dinh

    @property
    def dang_gom_y_dinh(self) -> bool:
        return self.phien is None

    def _o_con_thieu(self) -> phien.ThieuO | None:
        thieu = phien.thieu_gi(self._nhap["viec_gi"], self._nhap["khi_nao"],
                               self._nhap["o_dau"])
        return thieu[0] if thieu else None

    def _nhan_loi_noi(self, loi: str) -> None:
        """Gan cau vua noi vao o dang con thieu.

        Gan theo THU TU o thieu chu khong bat nguoi dung noi ro dang
        "khi nao la ...". Ho dang bi kep; bat ho nho cu phap la them mot
        viec nua phai lam.
        """
        o = self._o_con_thieu()
        if o is not None:
            self._nhap[o.value] = loi
            return
        # Da du ba o -> cau nay la mot BUOC.
        if self.phien is not None and not self.phien.xong:
            self.phien.them_buoc(loi)
        elif self.phien is None and len(loi.strip()) >= phien.MIN_KY_TU:
            self._buoc_cho.append(loi.strip())

    # ---------------------------------------------- moi goi tin

    def buoc(self, upd: PhoneUpdate) -> BridgeReply:
        """Xu ly mot goi tin, tra ve cau tra loi cho dien thoai."""
        gio = upd.t if upd.t is not None else time.time()
        tra = BridgeReply()

        if upd.lich_su is not None:
            self.so_thoi_luong = thoiluong.SoThoiLuong.from_json(upd.lich_su)

        # --- cai dat tu man hinh chinh ---
        if upd.muc_nhac is not None and upd.muc_nhac != self.muc_nhac:
            self.muc_nhac = upd.muc_nhac
            self.dat_gio_hen(self.gio_hen)          # dung lai bo nhac
        if upd.gio_hen is not None:
            self.dat_gio_hen(None if upd.gio_hen < 0 else upd.gio_hen)
        if upd.uoc_phut is not None:
            self.uoc_nguoi_dung = upd.uoc_phut

        if upd.voice:
            self._nhan_loi_noi(upd.voice)

        # --- lenh tu nut bam ---
        vua_bat_dau = False
        if upd.lenh == LENH_BAT_DAU:
            chua_co_phien = self.phien is None
            self._bat_dau(upd.noi_dung)
            vua_bat_dau = chua_co_phien and self.phien is not None
        elif upd.lenh == LENH_XONG_BUOC and self.phien:
            self.phien.xong_buoc()
        elif upd.lenh == LENH_TAM_DUNG:
            self._tam_dung(gio)
        elif upd.lenh == LENH_TIEP_TUC:
            self._tiep_tuc(gio)
        elif upd.lenh == LENH_VIEC_MOI:
            self._viec_moi()
        elif upd.lenh == LENH_KET_THUC and self.phien:
            self._tiep_tuc(gio)
            # Danh dau not cac buoc con lai de moi buoc van co phan hoi
            # cua no, ROI tuyen bo xong.
            #
            # Goi `ket_thuc()` la bat buoc, khong phai cho chac: rat
            # nhieu phien khong co buoc nao, va voi chung thi vong lap
            # tren khong chay lan nao.
            while self.phien.xong_buoc():
                pass
            self.phien.ket_thuc()

        dang_lam = bool(self.phien and not self.phien.xong
                        and upd.tren_man_hinh
                        and not self.dang_tam_dung)

        # --- dut mach vi phan tam ---
        #
        # Tin hieu la app RA KHOI TIEN CANH, khong phai chuyen dong. Mo
        # app khac chinh la dinh nghia thuc te cua "bi sao nhang" o boi
        # canh nay, va no chinh xac hon do chuyen dong nhieu.
        vua_quay_lai = self.theo_mach.cap_nhat(gio, dang_di=dang_lam)

        if self._tren_man_hinh_truoc and not upd.tren_man_hinh:
            self.bo_do_ket.roi_di()
        self._tren_man_hinh_truoc = upd.tren_man_hinh

        if self.phien is not None:
            self.bo_do_ket.sang_buoc(self.phien.chi_so, gio)

        # --- nhan vat: net mat va tu the ---
        self.bo_tu_the.cap_nhat(gio, dang_tap_trung=dang_lam)
        tra.tu_the = self.bo_tu_the.tu_the

        # --- ket lau: net mat diu xuong, VA KHONG GI KHAC ---
        #
        # Day la cach duy nhat app to ra rang no thay nguoi dung dang
        # ket, ma van khong chu dong bat chuyen (NHAN_VAT_BRIEF muc 2.4).
        # Mot net mat khong doi hoi cau tra loi nao; nguoi dung cham vao
        # thi moi co cau hoi.
        self._cap_nhat_net_mat(gio)

        # --- 1. cu cham: loi moi DUY NHAT de app len tieng ---
        if upd.cham_nhan_vat:
            tra.hoi = self._cau_khi_duoc_cham(gio)
            tra.listen = True

        # --- 2. dung lai ngu canh sau phan tam ---
        elif vua_quay_lai and self.phien:
            self._diu(gio, dongvien.phan_ung(vua_khoi_phuc=True).trang_thai)
            tra.say = mach.cau_khoi_phuc(
                mach.ViecDangLam(ten_viec=self.phien.y_dinh.viec_gi),
                chi_dan=self.phien.buoc_hien_tai,
                buoc_con_lai=self.phien.con_lai)

        # --- 3. phan hoi xong buoc ---
        thuong = (self.bo_phan_hoi.xong_buoc(self.phien.chi_so)
                  if self.phien else None)
        if thuong is not None:
            tra.am = thuong.am
            if tra.haptic is None:
                tra.haptic = thuong.haptic

        # --- cau mo dau: neo vao gio that, doi chieu uoc luong ---
        #
        # `cau_mo_dau()` la can thiep chinh cua lop chong mu thoi gian
        # (FLOWY_THIET_KE muc 3.1), nhung ban truoc KHONG GOI no o dau ca:
        # bam Bat dau xong app im lang. Day la phan hoi cho mot hanh dong
        # nguoi dung vua lam, nen khong pham muc 2.4 cua NHAN_VAT_BRIEF.
        #
        # Nhuong cho cu cham va cau dung lai ngu canh neu trung nhip.
        if vua_bat_dau and tra.say is None:
            tra.say = self.cau_mo_dau()

        # --- xong ca phien ---
        if self.phien and self.phien.xong and not self._da_bao_xong:
            self._da_bao_xong = True
            tra.say = self._cau_xong()
            # Dien thoai so huu so thoi luong, nen no phai biet luc nay
            # de ghi lai. Bat dung mot lan, cung nhip voi cau noi.
            tra.xong_phien = True

        # --- 4. nhac moc thoi gian, qua bo dem chong lap ---
        elif tra.say is None and self.bo_nhac is not None and dang_lam:
            nhac = self.bo_nhac.cap_nhat(
                timeblind.phut_trong_ngay(),
                buoc_con_lai=self.phien.con_lai if self.phien else None)
            chon = self.composer.compose(now=gio, gap_text=nhac)
            if chon is not None:
                tra.say = chon.text

        # Ten viec gui ve NGAY KHI BIET, khong doi co phien.
        #
        # Dien thoai chi gui lich su thoi luong cua dung viec co ten nay.
        # Truoc day ten chi ve sau khi phien bat dau - tuc la luc bam Bat
        # dau, laptop chua co lich su nao, va `cau_mo_dau()` khong bao gio
        # noi duoc "nhung lan truoc viec nay mat khoang X phut".
        if self.phien is not None:
            tra.ten_viec = self.phien.y_dinh.viec_gi
        elif self._nhap["viec_gi"]:
            tra.ten_viec = self._nhap["viec_gi"]
        # --- o y dinh con thieu: HIEN, nhung khong doc len ---
        #
        # Mo app ra ma man hinh trong tron thi nguoi dung khong biet go
        # gi. Nhung nhan vat cung khong duoc chu dong bat chuyen
        # (NHAN_VAT_BRIEF muc 2.4).
        #
        # Duong ranh nam giua HIEN va DOC: mot dong chu tren man hinh la
        # nhan cua o dang nhap, thu dong, khong doi hoi gi. Mot cau doc
        # len la app bat chuyen.
        #
        # Nen `hoi` duoc dat, con `listen` thi khong - va dien thoai chi
        # doc `hoi` len khi `listen` bat. Xem `MainActivity.nhan()`.
        if tra.hoi is None and self.dang_gom_y_dinh:
            o = self._o_con_thieu()
            if o is not None:
                tra.hoi = phien.CAU_HOI[o]

        tra.ban = self.trang_thai_ban.value
        tra.nhip_ms = NHIP_DANG_LAM_MS if dang_lam else NHIP_RANH_MS
        self._dat_dong_ho(tra)
        self._dien_trang_thai(tra, gio)
        return tra

    # ---------------------------------------------- phan phu

    def _bat_dau(self, noi_dung: str | None) -> None:
        # Dang co phien chua xong -> bam Bat dau lan nua KHONG tao phien
        # moi. Ban truoc thay phien cu bang phien moi, mat het cac buoc.
        if self.phien is not None and not self.phien.xong:
            if noi_dung:
                self._nhan_loi_noi(noi_dung)
            return
        if noi_dung:
            self._nhan_loi_noi(noi_dung)
        y = phien.tao_y_dinh(self._nhap["viec_gi"], self._nhap["khi_nao"],
                             self._nhap["o_dau"])
        if y is None:
            return          # con thieu o -> chua bat dau duoc
        self.phien = phien.Phien(y_dinh=y, gio_hen=self.gio_hen)
        for b in self._buoc_cho:
            self.phien.them_buoc(b)
        self._buoc_cho = []
        # Lam lai cung viec sau khi xong: phien moi phai bao xong duoc.
        self._da_bao_xong = False
        self.dang_tam_dung = False
        self._tam_dung_tu = None
        self._tong_tam_dung = 0.0

    # ---------------------------------------------- cai dat, tam dung

    def dat_gio_hen(self, gio_hen: float | None) -> None:
        """Dat hoac bo gio hen. Dung lai bo nhac theo muc nhac hien tai.

        Dung lai thay vi sua bo cu: moc da bao cua gio hen cu khong con
        nghia gi voi gio hen moi.
        """
        self.gio_hen = gio_hen
        self.bo_nhac = (timeblind.BoNhacGio(gio_hen, MUC_NHAC_MOC[self.muc_nhac])
                        if gio_hen is not None else None)
        if self.phien is not None:
            self.phien.gio_hen = gio_hen

    def _tam_dung(self, gio: float) -> None:
        if self.phien is None or self.phien.xong or self.dang_tam_dung:
            return
        self.dang_tam_dung = True
        self._tam_dung_tu = gio

    def _tiep_tuc(self, gio: float) -> None:
        if not self.dang_tam_dung:
            return
        if self._tam_dung_tu is not None:
            self._tong_tam_dung += max(0.0, gio - self._tam_dung_tu)
        self.dang_tam_dung = False
        self._tam_dung_tu = None

    def _viec_moi(self) -> None:
        """Bo y dinh dang gom va phien cu, bat dau gom mot viec khac.

        Ban truoc KHONG co duong nay: xong mot viec thi ba o y dinh van
        day, va bam Bat dau lai la lam lai dung viec cu.
        """
        self._nhap = {"viec_gi": None, "khi_nao": None, "o_dau": None}
        self.phien = None
        self._buoc_cho = []
        self.uoc_nguoi_dung = None
        self._da_bao_xong = False
        self.dang_tam_dung = False
        self._tam_dung_tu = None
        self._tong_tam_dung = 0.0
        self.trang_thai_ban = dongvien.TrangThai.BINH_THUONG
        self._diu_den = None

    def da_lam_that_giay(self, gio: float | None = None) -> float:
        """Thoi gian da lam, TRU thoi gian tam dung."""
        if self.phien is None:
            return 0.0
        dung = self._tong_tam_dung
        if self.dang_tam_dung and self._tam_dung_tu is not None and gio is not None:
            dung += max(0.0, gio - self._tam_dung_tu)
        return max(0.0, self.phien.da_lam_giay - dung)

    def _dien_trang_thai(self, tra: BridgeReply, gio: float) -> None:
        """Trang thai cho ba khoi co dinh cua giao dien v2."""
        tra.viec_gi = self._nhap["viec_gi"]
        tra.khi_nao = self._nhap["khi_nao"]
        tra.o_dau = self._nhap["o_dau"]
        if self.phien is not None:
            tra.cac_buoc = list(self.phien.buoc)
            tra.chi_so_buoc = self.phien.chi_so
            tra.trong_phien = not self.phien.xong
            tra.da_lam_giay = self.da_lam_that_giay(gio)
        else:
            tra.cac_buoc = list(self._buoc_cho)
        tra.tam_dung = self.dang_tam_dung
        # "HH:MM" de HIEN, khong phai `gio_doc` (dang de doc len).
        tra.gio_hen = (None if self.gio_hen is None else
                       f"{int(self.gio_hen // 60):02d}:{int(self.gio_hen % 60):02d}")
        tra.uoc_phut = self.uoc_nguoi_dung
        viec = self._nhap["viec_gi"]
        tra.goi_y_phut = self.so_thoi_luong.uoc_luong(viec) if viec else None
        tra.muc_nhac = self.muc_nhac

    def cau_mo_dau(self) -> str | None:
        """Cau neo lo trinh vao gio that, doc luc vua bat dau phien.

        Ba manh, theo thu tu quan trong:
          1. doi chieu uoc luong lan truoc voi thuc te  <- can thiep
          2. cau neo vao dong ho
          3. y dinh va buoc dau

        Manh 1 dung truoc vi no la thu duy nhat HUAN LUYEN cam nhan thoi
        gian; hai manh sau chi la thong tin.
        """
        if self.phien is None:
            return None
        viec = self.phien.y_dinh.viec_gi
        manh: list[str] = []

        doi_chieu = self.so_thoi_luong.cau_doi_chieu(viec)
        if doi_chieu:
            manh.append(doi_chieu)

        uoc = self.so_thoi_luong.uoc_luong(viec) or self.uoc_nguoi_dung
        if uoc is not None and self.gio_hen is not None:
            kh = timeblind.tinh(uoc, timeblind.phut_trong_ngay(),
                                self.gio_hen)
            manh.append(timeblind.cau(kh, viec, timeblind.phut_trong_ngay(),
                                      self.ten_su_kien))
        else:
            goi_y = self.so_thoi_luong.cau_goi_y(viec)
            if goi_y:
                manh.append(goi_y)

        manh.append(self.phien.cau_bat_dau())
        return " ".join(manh)

    def _diu(self, gio: float,
             net: dongvien.TrangThai = dongvien.TrangThai.THONG_CAM) -> None:
        """Diu net mat, va hen gio go ra."""
        self.trang_thai_ban = net
        self._diu_den = gio + GIU_NET_MAT_S

    def _cap_nhat_net_mat(self, gio: float) -> None:
        """Diu net mat khi dang ket, va go ra khi het han.

        Chi dung toi net mat BINH_THUONG. Nguoi dung vua xong viec dang
        o net VUI hay TU_HAO thi bo do ket khong duoc phep dam len - neu
        khong, phan thuong bien mat sau nua giay.
        """
        if self.bo_do_ket.dang_ket(gio):
            if self.trang_thai_ban == dongvien.TrangThai.BINH_THUONG:
                self._diu(gio)
            else:
                # Van dang ket thi gia han, khong de net mat tu go ra
                # trong luc tinh hinh chua doi.
                self._diu_den = gio + GIU_NET_MAT_S
            return

        if self._diu_den is not None and gio >= self._diu_den:
            self._diu_den = None
            if self.trang_thai_ban == dongvien.TrangThai.THONG_CAM:
                self.trang_thai_ban = dongvien.TrangThai.BINH_THUONG

    def _cau_khi_duoc_cham(self, gio: float) -> str:
        """Cham vao nhan vat gan nhu luon la luc nguoi dung dang kep.

        Chua du ba o y dinh thi hoi o con thieu - do la viec dang do, va
        bo qua no de hoi chuyen khac la bo roi nguoi dung giua chung.

        Du ba o roi thi cau hoi tuy LUC: dang ket, bi keo di, hay vua
        xong deu can mot cau khac nhau. Xem `adhd/cauhoi.py`.
        """
        if self.dang_gom_y_dinh:
            o = self._o_con_thieu()
            if o is not None:
                return phien.CAU_HOI[o]

        luc = self.bo_do_ket.luc_nen_hoi(
            gio,
            da_bat_dau=self.phien is not None,
            da_xong=bool(self.phien and self.phien.xong))
        return self.bo_cau_hoi.hoi(luc)

    def _cau_xong(self) -> str:
        # Ghi lai thoi luong THAT de lan sau khong phai doan nua. Day la
        # ca co che hoc cua lop chong mu thoi gian.
        self.so_thoi_luong.ghi(self.phien.y_dinh.viec_gi,
                               that_phut=self.da_lam_that_giay() / 60.0,
                               uoc_phut=self.uoc_nguoi_dung)

        cau = mach.cau_xong_viec(mach.ViecDangLam(
            ten_viec=self.phien.y_dinh.viec_gi, muc_dich=self.muc_dich))

        # Xong viec thi net mat tich cuc, CO HAY KHONG co gio hen.
        #
        # Phan lon phien khong hen gio. Neu chi doi net mat khi co gio
        # hen thi da so lan lam xong deu khong duoc ghi nhan gi - va luc
        # do "xong viec" va "bo do" trong giong het nhau tren man hinh.
        self.trang_thai_ban = dongvien.TrangThai.VUI
        self._diu_den = None

        if self.gio_hen is not None:
            dung_gio = timeblind.phut_trong_ngay() <= self.gio_hen
            n = self.so_chuoi.ghi(time.strftime("%Y-%m-%d"), dung_gio)
            pu = dongvien.phan_ung(toi_dich=True, dung_gio=dung_gio,
                                   chuoi_ngay=n)
            self.trang_thai_ban = pu.trang_thai
            if pu.cau:
                cau += " " + pu.cau
        return cau

    def _dat_dong_ho(self, tra: BridgeReply) -> None:
        """So lieu cho dong ho truc quan tren dien thoai."""
        if self.phien is None or self.gio_hen is None:
            return
        con = (self.gio_hen - timeblind.phut_trong_ngay()) * 60.0
        tong = max(con, self.phien.da_lam_giay + max(con, 0.0))
        tra.con_lai_giay = max(0.0, con)
        tra.tong_giay = max(1.0, tong)

    def luu_chuoi(self) -> None:
        if self._duong_dan_chuoi:
            self.so_chuoi.luu(self._duong_dan_chuoi)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gio-hen", help="gio can xong, dang GIO:PHUT (vd 14:00)")
    ap.add_argument("--viec", default="", help="ten viec, de san cho o dau")
    ap.add_argument("--muc-dich", default="",
                    help="lam viec nay de lam gi - nhac lai luc xong")
    ap.add_argument("--chuoi", default="config/chuoi.json",
                    help="so ghi so ngay lam xong dung gio")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()

    gio_hen = _doc_gio(args.gio_hen)
    if args.gio_hen and gio_hen is None:
        print(f"(khong doc duoc gio hen {args.gio_hen!r}, can dang GIO:PHUT "
              f"vd 14:00 - chay tiep khong co moc gio)")

    app = Flowy(gio_hen=gio_hen, ten_viec=args.viec,
                muc_dich=args.muc_dich, duong_dan_chuoi=Path(args.chuoi))

    server = BridgeServer(on_update=app.buoc, port=args.port)
    server.start()

    print(f"Dien thoai tro toi:  {server.url}")
    print(f"Kiem thu khong can dien thoai:")
    print(f"   python3 tools/phone_sim_flowy.py --url {server.url}\n")
    if gio_hen is not None:
        print(f"Gio can xong: {timeblind.gio_doc(gio_hen)}\n")
    print("Ctrl+C de dung.\n")

    stop = {"now": False}

    def handle_sigint(_sig, _frm):
        stop["now"] = True

    signal.signal(signal.SIGINT, handle_sigint)
    try:
        while not stop["now"]:
            time.sleep(0.2)
    finally:
        server.stop()
        app.luu_chuoi()
        if app.so_chuoi.chuoi:
            print(f"\nChuoi dung gio: {app.so_chuoi.chuoi} ngay")
        print(f"Goi tin nhan  : {server.packets}")


if __name__ == "__main__":
    main()
