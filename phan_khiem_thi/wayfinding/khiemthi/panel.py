"""
KICH BAN D - dung thiet bi man hinh cam ung.

Rao can noi lam viec: may in, may pha ca phe, lo vi song trong van phong
gio deu la man cam ung phang. Khong nut bam, khong phan hoi xuc giac,
khong doc duoc bang man hinh doc. Nhan vien khiem thi hoan toan khong
dung duoc - va day la rao can rat cu the, de demo, de giam khao hinh dung.

--------------------------------------------------------------------
Y TUONG COT LOI: dan MOT ma len thiet bi, va chinh ma do lam MOC SO DUOC
--------------------------------------------------------------------

Vi tri cac nut tren mot bang dieu khien la CO DINH so voi ma. Nen sau
khi biet day la thiet bi nao, huong dan tro thanh:

    "Dat ngon tay len ma, roi truot sang phai 4 phay 5 xentimet."

Cach nay co ba diem manh so voi bam theo ngon tay bang camera:

  1. Khong phu thuoc uoc luong tu the von nhieu nhieu. Camera chi can
     DOC RA ma la thiet bi nao; phan huong dan la so do co dinh, khong
     doi theo goc nhin hay anh sang.
  2. Nguoi dung TU KIEM CHUNG duoc bang tay, dung tinh than moc so duoc
     o Muc 13 - ho khong phai tin suong vao he thong.
  3. Chay duoc ca khi camera da roi khoi bang, vi so do da nam trong dau.

LUU Y VE VAT TU: ma in tren giay THUONG KHONG SO THAY DUOC. Phai dan
them mot mieng xop tron hoac mieng dan noi vao dung tam ma. Loai xop dan
tuong cat tron duong kinh 1cm la du, gia khong dang ke. Thieu buoc nay
thi ca kich ban vo nghia - nguoi dung khong tim duoc goc toa do.

He toa do bang dieu khien: goc la TAM MA, truc x sang PHAI, truc y LEN,
don vi MET. Nhin truc dien vao bang.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

# Duoi nguong nay thi coi nhu nam ngay tai ma, khong can noi huong.
AT_MARKER_M = 0.012

# Lam tron ve boi so nay. Nguoi dung khong the do chinh xac hon 0.5cm
# bang ngon tay, nen noi "4 phay 5" la du, noi "4 phay 37" la gia vo
# chinh xac va lam nguoi nghe met.
ROUND_TO_M = 0.005

# Hai nut gan nhau hon nguong nay thi phai canh bao, vi nguoi dung rat
# de bam nham sang nut ben canh.
CROWDED_M = 0.02


@dataclass(frozen=True)
class Button:
    """Mot nut tren bang, toa do tinh tu TAM MA, don vi met."""

    name: str
    x: float
    y: float
    note: str | None = None          # vd "nhan giu 2 giay"
    danger: bool = False             # vd nut xoa het, nut nuoc soi

    @property
    def distance(self) -> float:
        return math.hypot(self.x, self.y)


@dataclass
class PanelSpec:
    """Mot bang dieu khien da duoc do va ghi lai."""

    appliance: str
    marker_id: str
    marker_size_m: float
    buttons: list[Button] = field(default_factory=list)
    notes: str | None = None

    def find(self, name: str) -> Button | None:
        """Tim nut theo ten, khong phan biet hoa thuong va dau cach."""
        key = _norm(name)
        for b in self.buttons:
            if _norm(b.name) == key:
                return b
        # Cho phep go thieu: "sao chep" khop "Sao chep 1 mat"
        matches = [b for b in self.buttons if key and key in _norm(b.name)]
        return matches[0] if len(matches) == 1 else None

    def neighbours(self, btn: Button, within: float = CROWDED_M) -> list[Button]:
        return [
            b for b in self.buttons
            if b is not btn and math.hypot(b.x - btn.x, b.y - btn.y) <= within
        ]


def _norm(s: str) -> str:
    return " ".join(str(s).lower().split())


# --------------------------------------------------------------------
# Doc file mo ta bang
# --------------------------------------------------------------------

def load_panels(path: str | Path) -> dict[str, PanelSpec]:
    """
    Doc file mo ta cac bang dieu khien, tra ve dict theo ma so.

    Do bang thuoc roi nhap tay, y het cach dung ban do tang o Muc 9.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    panels: dict[str, PanelSpec] = {}

    for item in data.get("panels", []):
        buttons = [
            Button(
                name=b["name"],
                x=float(b["x"]),
                y=float(b["y"]),
                note=b.get("note"),
                danger=bool(b.get("danger", False)),
            )
            for b in item.get("buttons", [])
        ]
        spec = PanelSpec(
            appliance=item["appliance"],
            marker_id=str(item["marker_id"]),
            marker_size_m=float(item.get("marker_size_m", 0.08)),
            buttons=buttons,
            notes=item.get("notes"),
        )
        _validate(spec)
        panels[spec.marker_id] = spec
    return panels


def _validate(spec: PanelSpec) -> None:
    if not spec.buttons:
        raise ValueError(f"Bang '{spec.appliance}' khong co nut nao.")

    seen: set[str] = set()
    for b in spec.buttons:
        key = _norm(b.name)
        if key in seen:
            raise ValueError(
                f"Bang '{spec.appliance}' co hai nut trung ten: '{b.name}'"
            )
        seen.add(key)

    # Hai nut o dung mot cho la loi do dac, khong phai thiet ke
    for i, a in enumerate(spec.buttons):
        for b in spec.buttons[i + 1:]:
            if math.hypot(a.x - b.x, a.y - b.y) < 0.001:
                raise ValueError(
                    f"Bang '{spec.appliance}': nut '{a.name}' va '{b.name}' "
                    "cung mot toa do - kiem tra lai so do."
                )


# --------------------------------------------------------------------
# Dien dat huong
# --------------------------------------------------------------------

def _cm(metres: float) -> str:
    """Doi ra xentimet, doc duoc bang tieng Viet."""
    rounded = round(metres / ROUND_TO_M) * ROUND_TO_M
    cm = abs(rounded) * 100.0
    if abs(cm - round(cm)) < 0.05:
        return f"{int(round(cm))}"
    return f"{cm:.1f}".replace(".", " phay ")


def format_offset(dx: float, dy: float) -> str:
    """
    Doi do lech thanh cau noi duoc.

    Noi PHAI/TRAI truoc roi LEN/XUONG sau, vi tay nguoi di ngang de hon
    di doc, va giu thu tu co dinh giup nguoi dung quen nhanh.
    """
    parts: list[str] = []

    if abs(dx) >= AT_MARKER_M:
        parts.append(f"sang {'phai' if dx > 0 else 'trai'} {_cm(dx)} xentimet")
    if abs(dy) >= AT_MARKER_M:
        parts.append(f"{'len' if dy > 0 else 'xuong'} {_cm(dy)} xentimet")

    if not parts:
        return "ngay tai ma"
    return ", roi ".join(parts)


def describe_layout(spec: PanelSpec) -> str:
    """Mot cau tom tat ca bang, doc khi vua nhan ra thiet bi."""
    n = len(spec.buttons)
    rows = _count_rows(spec.buttons)
    shape = f"{n} nut"
    if rows > 1:
        shape += f", xep khoang {rows} hang"
    text = f"{spec.appliance}. Bang co {shape}."

    dangerous = [b.name for b in spec.buttons if b.danger]
    if dangerous:
        text += f" Luu y nut can than: {', '.join(dangerous)}."
    if spec.notes:
        text += f" {spec.notes}"
    return text


def _count_rows(buttons: list[Button], tol: float = 0.015) -> int:
    """Dem so hang bang cach gom cac nut co cung do cao."""
    rows: list[float] = []
    for b in sorted(buttons, key=lambda x: -x.y):
        if not any(abs(b.y - r) <= tol for r in rows):
            rows.append(b.y)
    return len(rows)


def guide_to(spec: PanelSpec, button_name: str) -> str:
    """Huong dan tim mot nut, tinh tu tam ma."""
    btn = spec.find(button_name)
    if btn is None:
        names = ", ".join(b.name for b in spec.buttons)
        return (f"Khong co nut nao ten '{button_name}'. "
                f"Bang nay co: {names}.")

    text = (f"Dat ngon tay len ma, roi truot "
            f"{format_offset(btn.x, btn.y)}. Do la nut {btn.name}.")

    if btn.note:
        text += f" {btn.note}."

    near = spec.neighbours(btn)
    if near:
        text += (f" Can than, nut {near[0].name} nam rat sat ben canh.")
    if btn.danger:
        text += " Day la nut can can trong."
    return text


def list_buttons(spec: PanelSpec) -> str:
    """Doc het ten cac nut, theo thu tu tren xuong duoi trai sang phai."""
    ordered = sorted(spec.buttons, key=lambda b: (-b.y, b.x))
    return "Cac nut tren bang: " + ", ".join(b.name for b in ordered) + "."


def nearest_button(spec: PanelSpec, x: float, y: float) -> tuple[Button, float]:
    """Nut gan mot diem nhat, kem khoang cach. Dung khi ra tinh nang do tay."""
    best = min(spec.buttons, key=lambda b: math.hypot(b.x - x, b.y - y))
    return best, math.hypot(best.x - x, best.y - y)


# --------------------------------------------------------------------
# Phien lam viec voi mot bang
# --------------------------------------------------------------------

@dataclass
class PanelSession:
    """
    Trang thai khi nguoi dung dang dung mot thiet bi.

    Vong doi: chua thay ma -> nhan ra thiet bi -> huong dan tung nut.
    Chi doc gioi thieu MOT LAN cho moi thiet bi, khong doc lai moi khung
    hinh - cung nguyen tac chong lap voi Announcer.
    """

    panels: dict[str, PanelSpec]
    current: PanelSpec | None = None
    _announced: set[str] = field(default_factory=set)

    def on_marker(self, marker_id: str) -> str | None:
        """
        Goi khi camera doc duoc mot ma.

        Tra ve cau gioi thieu neu vua nhan ra thiet bi moi, None neu van
        la thiet bi cu (de khong doc lai lien tuc).
        """
        key = str(marker_id)
        spec = self.panels.get(key)
        if spec is None:
            return None                       # ma khong thuoc thiet bi nao

        if self.current is spec and key in self._announced:
            return None

        self.current = spec
        self._announced.add(key)
        return describe_layout(spec) + " " + list_buttons(spec)

    def ask(self, button_name: str) -> str:
        if self.current is None:
            return ("Chua nhan ra thiet bi nao. "
                    "Hay huong camera vao ma dan tren bang.")
        return guide_to(self.current, button_name)

    def repeat_layout(self) -> str:
        if self.current is None:
            return "Chua nhan ra thiet bi nao."
        return describe_layout(self.current) + " " + list_buttons(self.current)

    def reset(self) -> None:
        self.current = None
        self._announced.clear()
