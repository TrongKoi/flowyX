"""
Chon cau nao duoc noi, khi nhieu kenh cung muon noi.

--------------------------------------------------------------------
VI SAO PHAI TACH RIENG RA MOT MODULE
--------------------------------------------------------------------

Logic nay tung nam trong run_bridge.py va da co mot loi that: hai kenh
DUNG CHUNG mot bo dem chong lap, nen chung luan phien lam moi lan nhau
va noi khong dut.

    chi duong noi        -> bo dem = cau chi duong
    chuong ngai thay khac -> noi     -> bo dem = canh bao
    chi duong thay khac   -> noi lai -> bo dem = cau chi duong
    ... lap vo han

Nguoi dung nghe hai cau thay nhau mai. Loi khong lo ra trong test don
vi vi no chi xuat hien khi hai kenh cung hoat dong, va logic thi nam
trong mot script khong goi duoc tu test.

Tach ra day de test duoc, va de loi do khong tai dien.

--------------------------------------------------------------------
BA MUC UU TIEN
--------------------------------------------------------------------

    1. Chuong ngai GAP        vap nga la hau qua tuc thi
    2. Chi dan duong          re nham thi con sua duoc
    3. Chuong ngai KHONG GAP  noi khi con cho trong

Muc 3 ton tai vi mot canh bao quan trong roi vao day: "khong quan sat
duoc mat dat phia truoc". No khong gap - khong nen cat ngang lenh re -
nhung tuyet doi khong duoc nuot mat, vi do la luc he thong dang mu.
"""

from __future__ import annotations

from dataclasses import dataclass

# Khoang nhac lai cua kenh chuong ngai, giay.
#
# Nguy hiem thi nhac day hon - nguoi dung dang tien ve phia no. Canh
# bao binh thuong thi thua, vi phan lon la TRANG THAI KEO DAI chu khong
# phai su kien moi: san bong khong doc duoc do sau thi keo dai ca hanh
# lang, va nhac moi khung hinh se lam nguoi dung tat he thong.
URGENT_REPEAT_S = 4.0
CALM_REPEAT_S = 20.0


@dataclass(frozen=True)
class Spoken:
    """Ket qua chon: noi cau gi, kem ma rung, va tu kenh nao."""

    text: str
    haptic: str | None
    channel: str          # "nguy_hiem" | "chi_dan" | "chuong_ngai"


class ReplyComposer:
    """
    Gop hai kenh thanh mot cau noi, moi kenh mot bo dem chong lap RIENG.

    Bo dem rieng la diem mau chot. Xem phan dau file.
    """

    def __init__(self,
                 urgent_repeat_s: float = URGENT_REPEAT_S,
                 calm_repeat_s: float = CALM_REPEAT_S):
        self.urgent_repeat_s = urgent_repeat_s
        self.calm_repeat_s = calm_repeat_s
        self._last_chi_dan: str | None = None
        self._last_gap: str | None = None
        self._last_gap_at = 0.0

    def compose(
        self,
        now: float,
        chi_dan_text: str | None = None,
        chi_dan_haptic: str | None = None,
        chi_dan_urgent: bool = False,
        gap_text: str | None = None,
        gap_urgent: bool = False,
    ) -> Spoken | None:
        """
        Chon cau duoc noi o khung hinh nay, hoac None neu nen im lang.

        Im lang la ket qua HOP LE va pho bien nhat - noi lien tuc thi
        nguoi dung tat he thong, va luc do khong con gi bao ve ho nua.
        """
        # --- muc 1: chuong ngai gap ---
        if gap_text and gap_urgent:
            if self._gap_due(gap_text, now, self.urgent_repeat_s):
                self._mark_gap(gap_text, now)
                return Spoken(gap_text, "double_repeat", "nguy_hiem")
            return None          # da noi roi, va no van dang gap

        # --- muc 2: chi dan duong ---
        if chi_dan_text and (chi_dan_text != self._last_chi_dan or chi_dan_urgent):
            self._last_chi_dan = chi_dan_text
            return Spoken(chi_dan_text, chi_dan_haptic, "chi_dan")

        # --- muc 3: chuong ngai khong gap ---
        if gap_text and self._gap_due(gap_text, now, self.calm_repeat_s):
            self._mark_gap(gap_text, now)
            return Spoken(gap_text, None, "chuong_ngai")

        return None

    # ---------- noi bo ----------

    def _gap_due(self, text: str, now: float, repeat_s: float) -> bool:
        if text != self._last_gap:
            return True
        return now - self._last_gap_at >= repeat_s

    def _mark_gap(self, text: str, now: float) -> None:
        self._last_gap = text
        self._last_gap_at = now

    def reset(self) -> None:
        self._last_chi_dan = None
        self._last_gap = None
        self._last_gap_at = 0.0
