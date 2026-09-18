"""
KICH BAN B - tim cho ngoi hot-desk.

Rao can noi lam viec: van phong hot-desk pha huy TINH DU DOAN DUOC - thu
ma nguoi khiem thi phu thuoc vao nhieu nhat. Moi ngay mot cho ngoi khac,
do dac nguoi khac de lung tung, va khong ai nghi den viec bao cho ho biet
hom nay ngoi o dau.

Day la kich ban RE NHAT trong sau kich ban: dung lai khoi moc neo va khoi
giong noi y nguyen, KHONG can tim duong dai vi cac ban thuong nam trong
cung mot khu.

Cai moi chi co hai thu:
  1. DAT CHO - ai ngoi ban nao hom nay
  2. XAC NHAN - "day dung la ban cua ban" khi doc duoc ma tren ban

Diem thu hai moi la phan quan trong. Nguoi khiem thi khong the liec mot
cai de biet minh ngoi nham ban nguoi khac. Mot cau xac nhan ro rang khi
cham dung ban la thu bien he thong tu "co ve dung" thanh "chac chan dung".
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Desk:
    """Mot ban lam viec, danh dau bang mot ma dan tren mat ban."""

    desk_id: str
    marker_id: str
    zone: str = ""                     # khu vuc, vd "khu cua so phia dong"
    landmark: str | None = None        # moc SO DUOC de tu xac nhan
    note: str | None = None            # vd "ban dieu chinh do cao duoc"
    fixed_for: str | None = None       # nguoi duoc dat co dinh, neu co


@dataclass
class DeskBooking:
    """Dat cho cua mot ngay."""

    day: str                           # dinh dang ISO, vd 2026-09-21
    assignments: dict[str, str] = field(default_factory=dict)   # nguoi -> ban


@dataclass
class DeskMap:
    desks: dict[str, Desk]             # theo desk_id
    by_marker: dict[str, Desk]         # theo ma so
    bookings: dict[str, DeskBooking]   # theo ngay

    def desk_of(self, person: str, day: str) -> Desk | None:
        booking = self.bookings.get(day)
        if booking is None:
            return None
        desk_id = booking.assignments.get(person)
        return self.desks.get(desk_id) if desk_id else None

    def who_is_at(self, desk_id: str, day: str) -> str | None:
        booking = self.bookings.get(day)
        if booking is None:
            return None
        for person, did in booking.assignments.items():
            if did == desk_id:
                return person
        return None


def load_desks(path: str | Path) -> DeskMap:
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    desks: dict[str, Desk] = {}
    by_marker: dict[str, Desk] = {}
    for item in data.get("desks", []):
        desk = Desk(
            desk_id=str(item["desk_id"]),
            marker_id=str(item["marker_id"]),
            zone=item.get("zone", ""),
            landmark=item.get("landmark"),
            note=item.get("note"),
            fixed_for=item.get("fixed_for"),
        )
        if desk.marker_id in by_marker:
            raise ValueError(
                f"Ma {desk.marker_id} duoc dung cho hai ban: "
                f"{by_marker[desk.marker_id].desk_id} va {desk.desk_id}"
            )
        desks[desk.desk_id] = desk
        by_marker[desk.marker_id] = desk

    if not desks:
        raise ValueError("Khong co ban nao trong file.")

    bookings: dict[str, DeskBooking] = {}
    for item in data.get("bookings", []):
        day = str(item["day"])
        assignments = {str(k): str(v) for k, v in item.get("assignments", {}).items()}
        for person, desk_id in assignments.items():
            if desk_id not in desks:
                raise ValueError(
                    f"Ngay {day}: '{person}' duoc dat ban '{desk_id}' "
                    "khong co trong danh sach ban."
                )
        # Hai nguoi cung mot ban la loi dat cho, phai bat som
        seen: dict[str, str] = {}
        for person, desk_id in assignments.items():
            if desk_id in seen:
                raise ValueError(
                    f"Ngay {day}: ban '{desk_id}' bi dat cho ca "
                    f"'{seen[desk_id]}' va '{person}'."
                )
            seen[desk_id] = person
        bookings[day] = DeskBooking(day=day, assignments=assignments)

    return DeskMap(desks=desks, by_marker=by_marker, bookings=bookings)


# --------------------------------------------------------------------

def describe_desk(desk: Desk) -> str:
    """Mo ta mot ban de nguoi dung biet duong tim."""
    parts = [f"Ban {desk.desk_id}"]
    if desk.zone:
        parts.append(f"o {desk.zone}")
    text = ", ".join(parts) + "."
    if desk.landmark:
        text += f" {desk.landmark}."
    if desk.note:
        text += f" {desk.note}."
    return text


@dataclass
class DeskSession:
    """
    Trang thai khi nguoi dung dang di tim cho ngoi.

    Vong doi: hoi ban hom nay -> di tim -> cham ma tren ban -> xac nhan.
    """

    desk_map: DeskMap
    person: str
    day: str = field(default_factory=lambda: date.today().isoformat())
    target: Desk | None = None
    confirmed: bool = False
    _announced: set[str] = field(default_factory=set)

    def start(self) -> str:
        """Cau dau tien: hom nay ngoi o dau."""
        desk = self.desk_map.desk_of(self.person, self.day)
        if desk is None:
            return (f"Khong tim thay dat cho cho {self.person} ngay "
                    f"{self.day}. Hay hoi bo phan hanh chinh.")
        self.target = desk
        return "Hom nay ban ngoi o " + describe_desk(desk)

    def on_marker(self, marker_id: str) -> str | None:
        """
        Goi khi camera doc duoc ma tren mat ban.

        Day la phan quan trong nhat cua kich ban: nguoi khiem thi khong
        the liec mot cai de biet minh ngoi nham ban nguoi khac.
        """
        key = str(marker_id)
        desk = self.desk_map.by_marker.get(key)
        if desk is None:
            return None                       # ma khong thuoc ban nao

        if self.target is None:
            return f"Day la {describe_desk(desk)}"

        if desk.desk_id == self.target.desk_id:
            if self.confirmed:
                return None                   # da xac nhan roi, khong lap
            self.confirmed = True
            text = f"Dung roi. Day la ban {desk.desk_id} cua ban hom nay."
            if desk.note:
                text += f" {desk.note}."
            return text

        # Ngoi nham ban nguoi khac - phai noi ro va noi ngay
        if key in self._announced:
            return None
        self._announced.add(key)

        occupant = self.desk_map.who_is_at(desk.desk_id, self.day)
        text = f"Day la ban {desk.desk_id}, khong phai ban cua ban."
        if occupant:
            text += f" Ban nay hom nay la cua {occupant}."
        text += f" Ban cua ban la {self.target.desk_id}"
        if self.target.zone:
            text += f", o {self.target.zone}"
        text += "."
        return text

    def repeat(self) -> str:
        if self.target is None:
            return self.start()
        return "Ban cua ban hom nay: " + describe_desk(self.target)

    def reset(self) -> None:
        self.target = None
        self.confirmed = False
        self._announced.clear()
