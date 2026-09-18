"""Quy đổi biểu thức thời gian tương đối tiếng Việt sang ngày tuyệt đối.

Module này cố ý là Python thuần (stdlib + một enum dùng chung), KHÔNG gọi LLM.

Lý do: LLM tính toán ngày tháng sai một cách *âm thầm* — nó trả về một ngày
trông hợp lý nhưng lệch, và không có cách nào viết test hồi quy cho hành vi
phi tất định đó. ``datetime`` thì không bao giờ sai. Mỗi phép tính chuyển
được từ LLM sang Python vừa tiết kiệm một request quota vừa loại bỏ một
nguồn phi tất định khỏi pipeline.

Nguyên tắc thiết kế quan trọng nhất
-----------------------------------
Khi biểu thức quá mơ hồ để xác định MỘT ngày cụ thể ("tuần sau", "đầu tháng
8", "sau Tết"), hàm trả về ``None`` kèm rule ``TOO_VAGUE``. Đây là hành vi
ĐÚNG, không phải thất bại: bịa ra một deadline không ai nói tệ hơn nhiều so
với việc để trống cho người dùng tự điền.

Ví dụ
-----
>>> import datetime as dt
>>> anchor = dt.date(2026, 7, 22)          # Thứ Tư
>>> resolve_vietnamese_date("thứ 3 tuần sau", anchor).date
datetime.date(2026, 7, 28)
>>> resolve_vietnamese_date("đầu tháng 8", anchor).date is None
True
"""

from __future__ import annotations

import calendar
import datetime as dt
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Final, Pattern

from schemas.common import Confidence

__all__ = [
    "ResolutionRule",
    "DateResolution",
    "resolve_vietnamese_date",
    "normalize_vietnamese",
    "this_week_weekday",
    "next_week_weekday",
    "this_week_weekday_smart",
    "MAX_PLAUSIBLE_HORIZON_DAYS",
]


# --------------------------------------------------------------------------- #
# Hằng số
# --------------------------------------------------------------------------- #

MAX_PLAUSIBLE_HORIZON_DAYS: Final[int] = 365
"""Deadline xa hơn mốc này gần như chắc chắn là lỗi quy đổi, không phải ý định thật."""

MONDAY: Final[int] = 0
TUESDAY: Final[int] = 1
WEDNESDAY: Final[int] = 2
THURSDAY: Final[int] = 3
FRIDAY: Final[int] = 4
SATURDAY: Final[int] = 5
SUNDAY: Final[int] = 6

WEEKDAY_NAMES: Final[dict[int, str]] = {
    MONDAY: "monday",
    TUESDAY: "tuesday",
    WEDNESDAY: "wednesday",
    THURSDAY: "thursday",
    FRIDAY: "friday",
    SATURDAY: "saturday",
    SUNDAY: "sunday",
}

VIETNAMESE_WEEKDAY_OFFSET: Final[int] = 2
"""Trong tiếng Việt "thứ 2" là Monday, nên ``weekday_index = so_thu - 2``.

Đây là cái bẫy kinh điển của bài toán này: lệch một đơn vị ở đây làm sai
TOÀN BỘ deadline trong hệ thống, và lỗi đó rất khó phát hiện bằng mắt vì
kết quả vẫn là một ngày trông hợp lý.
"""


# --------------------------------------------------------------------------- #
# Kiểu trả về
# --------------------------------------------------------------------------- #


class ResolutionRule(str, Enum):
    """Luật đã được áp dụng. Luôn được trả về, kể cả khi không ra ngày."""

    NOT_MENTIONED = "NOT_MENTIONED"
    ABSOLUTE_DATE = "ABSOLUTE_DATE"
    OFFSET_DAYS = "OFFSET_DAYS"
    THIS_WEEK_WEEKDAY = "THIS_WEEK_WEEKDAY"
    NEXT_WEEK_WEEKDAY = "NEXT_WEEK_WEEKDAY"
    THIS_WEEK_WEEKDAY_SMART = "THIS_WEEK_WEEKDAY_SMART"
    LAST_DAY_OF_MONTH = "LAST_DAY_OF_MONTH"
    LAST_DAY_OF_NEXT_MONTH = "LAST_DAY_OF_NEXT_MONTH"
    TOO_VAGUE = "TOO_VAGUE"
    UNPARSEABLE = "UNPARSEABLE"
    REJECTED_PAST_DATE = "REJECTED_PAST_DATE"
    REJECTED_IMPLAUSIBLE = "REJECTED_IMPLAUSIBLE"


@dataclass(frozen=True, slots=True)
class DateResolution:
    """Kết quả quy đổi.

    ``date is None`` không đồng nghĩa với lỗi — đọc ``rule`` để biết lý do:
    không ai nhắc tới (``NOT_MENTIONED``), quá mơ hồ (``TOO_VAGUE``), hay
    kết quả bị loại vì vô lý (``REJECTED_*``).
    """

    date: dt.date | None
    rule: ResolutionRule
    confidence: Confidence | None = None
    raw: str | None = None
    detail: str | None = None
    note: str | None = None

    @property
    def is_resolved(self) -> bool:
        return self.date is not None

    @property
    def rule_display(self) -> str:
        """Chuỗi để ghi vào trường ``due_resolution_rule`` của biên bản.

        Ví dụ: ``"NEXT_WEEK_WEEKDAY(tuesday)"``.
        """
        if self.detail:
            return f"{self.rule.value}({self.detail})"
        return self.rule.value

    def to_dict(self) -> dict[str, object]:
        return {
            "date": self.date.isoformat() if self.date else None,
            "rule": self.rule_display,
            "confidence": self.confidence.value if self.confidence else None,
            "raw": self.raw,
            "note": self.note,
        }


# --------------------------------------------------------------------------- #
# Chuẩn hoá văn bản
# --------------------------------------------------------------------------- #

_COMBINING_MARKS: Final[Pattern[str]] = re.compile(r"[\u0300-\u036f]")
_WHITESPACE: Final[Pattern[str]] = re.compile(r"\s+")

_ALIASES: Final[tuple[tuple[Pattern[str], str], ...]] = (
    (re.compile(r"\bt([2-7])\b"), r"thu \1"),
    (re.compile(r"\bthu\s*([2-7])\b"), r"thu \1"),
    (re.compile(r"\bcn\b"), "chu nhat"),
    (re.compile(r"\bchunhat\b"), "chu nhat"),
    (re.compile(r"\bhai\b(?=\s*tuan)"), "2"),
)


def normalize_vietnamese(text: str) -> str:
    """Đưa văn bản về dạng ASCII thường, không dấu, để khớp regex ổn định.

    Nhờ bỏ dấu, cùng một mẫu regex khớp được cả "thứ 3" lẫn "thu 3" — người
    dùng gõ thiếu dấu hoặc ASR trả về thiếu dấu đều xử lý được như nhau.
    """
    lowered = text.lower().replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", lowered)
    stripped = _COMBINING_MARKS.sub("", decomposed)
    recomposed = unicodedata.normalize("NFC", stripped)
    collapsed = _WHITESPACE.sub(" ", recomposed).strip()

    for pattern, replacement in _ALIASES:
        collapsed = pattern.sub(replacement, collapsed)

    return collapsed


def _weekday_from_vietnamese(token: str) -> int:
    """Chuyển "thu 3" / "chu nhat" thành chỉ số weekday của Python."""
    token = token.strip()
    if token.startswith("chu nhat"):
        return SUNDAY
    match = re.search(r"([2-7])", token)
    if match is None:
        raise ValueError(f"Không nhận ra thứ trong tiếng Việt: {token!r}")
    return int(match.group(1)) - VIETNAMESE_WEEKDAY_OFFSET


# --------------------------------------------------------------------------- #
# Hàm tính ngày (đơn vị nhỏ nhất, test riêng được)
# --------------------------------------------------------------------------- #


def this_week_weekday(target_weekday: int, anchor: dt.date) -> dt.date:
    """Ngày ``target_weekday`` trong tuần chứa ``anchor``.

    Tuần bắt đầu từ Thứ Hai theo quy ước Việt Nam (và ISO-8601).
    """
    monday = anchor - dt.timedelta(days=anchor.weekday())
    return monday + dt.timedelta(days=target_weekday)


def next_week_weekday(target_weekday: int, anchor: dt.date) -> dt.date:
    """Ngày ``target_weekday`` trong tuần kế tiếp tuần chứa ``anchor``."""
    return this_week_weekday(target_weekday, anchor) + dt.timedelta(days=7)


def this_week_weekday_smart(target_weekday: int, anchor: dt.date) -> dt.date:
    """Lần xuất hiện kế tiếp của ``target_weekday``, không rơi vào quá khứ.

    Dùng cho cách nói không kèm định tính tuần: "trước thứ 6" nói vào Thứ Tư
    nghĩa là Thứ Sáu tuần này; nói vào Thứ Bảy thì phải là Thứ Sáu tuần sau.
    """
    candidate = this_week_weekday(target_weekday, anchor)
    if candidate <= anchor:
        candidate += dt.timedelta(days=7)
    return candidate


def _last_day_of_month(anchor: dt.date, month_offset: int = 0) -> dt.date:
    year = anchor.year + (anchor.month - 1 + month_offset) // 12
    month = (anchor.month - 1 + month_offset) % 12 + 1
    return dt.date(year, month, calendar.monthrange(year, month)[1])


def _build_absolute_date(
    day: int, month: int, year_token: str | None, anchor: dt.date
) -> dt.date | None:
    """Dựng ngày tuyệt đối từ dạng dd/mm hoặc dd/mm/yyyy.

    Không có năm thì suy ra: nếu ngày đã trôi qua so với ``anchor``, hiểu là
    năm sau (nói "ngày 5/1" vào tháng 7 nghĩa là tháng 1 năm tới).
    """
    if year_token:
        year = int(year_token)
        if year < 100:
            year += 2000
    else:
        year = anchor.year

    try:
        candidate = dt.date(year, month, day)
    except ValueError:
        return None

    if year_token is None and candidate < anchor:
        try:
            candidate = dt.date(year + 1, month, day)
        except ValueError:
            return None

    return candidate


# --------------------------------------------------------------------------- #
# Bảng luật
# --------------------------------------------------------------------------- #

_Handler = Callable[[re.Match[str], dt.date], DateResolution]


def _vague(reason: str) -> _Handler:
    def handler(match: re.Match[str], anchor: dt.date) -> DateResolution:
        return DateResolution(
            date=None,
            rule=ResolutionRule.TOO_VAGUE,
            confidence=None,
            detail=reason,
            note="Biểu thức chỉ một khoảng thời gian, không xác định được một ngày cụ thể.",
        )

    return handler


def _offset_days(days: int) -> _Handler:
    def handler(match: re.Match[str], anchor: dt.date) -> DateResolution:
        return DateResolution(
            date=anchor + dt.timedelta(days=days),
            rule=ResolutionRule.OFFSET_DAYS,
            confidence=Confidence.HIGH,
            detail=f"{days:+d}",
        )

    return handler


def _fixed_weekday(target: int, *, next_week: bool) -> _Handler:
    def handler(match: re.Match[str], anchor: dt.date) -> DateResolution:
        resolved = (
            next_week_weekday(target, anchor)
            if next_week
            else this_week_weekday(target, anchor)
        )
        rule = (
            ResolutionRule.NEXT_WEEK_WEEKDAY
            if next_week
            else ResolutionRule.THIS_WEEK_WEEKDAY
        )
        return DateResolution(
            date=resolved,
            rule=rule,
            confidence=Confidence.HIGH,
            detail=WEEKDAY_NAMES[target],
        )

    return handler


def _named_weekday(*, next_week: bool, smart: bool, confidence: Confidence) -> _Handler:
    def handler(match: re.Match[str], anchor: dt.date) -> DateResolution:
        target = _weekday_from_vietnamese(match.group("weekday"))
        if next_week:
            resolved = next_week_weekday(target, anchor)
            rule = ResolutionRule.NEXT_WEEK_WEEKDAY
        elif smart:
            resolved = this_week_weekday_smart(target, anchor)
            rule = ResolutionRule.THIS_WEEK_WEEKDAY_SMART
        else:
            resolved = this_week_weekday(target, anchor)
            rule = ResolutionRule.THIS_WEEK_WEEKDAY
        return DateResolution(
            date=resolved,
            rule=rule,
            confidence=confidence,
            detail=WEEKDAY_NAMES[target],
        )

    return handler


def _month_end(offset: int) -> _Handler:
    def handler(match: re.Match[str], anchor: dt.date) -> DateResolution:
        rule = (
            ResolutionRule.LAST_DAY_OF_MONTH
            if offset == 0
            else ResolutionRule.LAST_DAY_OF_NEXT_MONTH
        )
        return DateResolution(
            date=_last_day_of_month(anchor, offset),
            rule=rule,
            confidence=Confidence.HIGH,
        )

    return handler


def _absolute_date(confidence: Confidence) -> _Handler:
    def handler(match: re.Match[str], anchor: dt.date) -> DateResolution:
        resolved = _build_absolute_date(
            day=int(match.group("day")),
            month=int(match.group("month")),
            year_token=match.groupdict().get("year"),
            anchor=anchor,
        )
        if resolved is None:
            return DateResolution(
                date=None,
                rule=ResolutionRule.UNPARSEABLE,
                note="Ngày tháng không hợp lệ trên lịch.",
            )
        return DateResolution(
            date=resolved,
            rule=ResolutionRule.ABSOLUTE_DATE,
            confidence=confidence,
        )

    return handler


_WEEKDAY_TOKEN = r"(?P<weekday>thu [2-7]|chu nhat)"

_RULES: Final[tuple[tuple[Pattern[str], _Handler], ...]] = (
    # --- Nhóm 1: ngày tuyệt đối (ưu tiên cao nhất, ít mơ hồ nhất) ---
    (
        re.compile(
            r"\bngay\s+(?P<day>\d{1,2})\s*[/-]\s*(?P<month>\d{1,2})"
            r"(?:\s*[/-]\s*(?P<year>\d{2,4}))?"
        ),
        _absolute_date(Confidence.HIGH),
    ),
    (
        re.compile(
            r"\b(?P<day>\d{1,2})\s*/\s*(?P<month>\d{1,2})"
            r"(?:\s*/\s*(?P<year>\d{2,4}))?\b"
        ),
        _absolute_date(Confidence.MEDIUM),
    ),
    # --- Nhóm 2: mốc luôn mơ hồ, phải chặn TRƯỚC các luật khoảng thời gian ---
    (re.compile(r"\b(sau|truoc|ra)\s+tet\b"), _vague("tet")),
    (re.compile(r"\b(asap|khan cap|cang som cang tot|som nhat co the)\b"), _vague("urgency_not_date")),
    (re.compile(r"\bkhi nao\s+\w+|luc nao\s+\w+|bao gio\s+\w+"), _vague("conditional")),
    (re.compile(r"\bnay mai\b|\bsap toi\b|\bthoi gian toi\b|\bsom\b"), _vague("indefinite_soon")),
    # --- Nhóm 3: lệch ngày so với ngày họp ---
    (re.compile(r"\bhom nay\b"), _offset_days(0)),
    (re.compile(r"\bngay mai\b|\bmai\b"), _offset_days(1)),
    (re.compile(r"\bngay kia\b|\bngay mot\b"), _offset_days(2)),
    (re.compile(r"\bhom qua\b"), _offset_days(-1)),
    # --- Nhóm 4: đầu/cuối tuần (phải đứng TRƯỚC luật "tuan sau" mơ hồ) ---
    (re.compile(r"\bcuoi tuan (sau|toi)\b"), _fixed_weekday(SUNDAY, next_week=True)),
    (re.compile(r"\bcuoi tuan( nay)?\b"), _fixed_weekday(SUNDAY, next_week=False)),
    (re.compile(r"\bdau tuan (sau|toi)\b"), _fixed_weekday(MONDAY, next_week=True)),
    (re.compile(r"\bdau tuan( nay)?\b"), _fixed_weekday(MONDAY, next_week=False)),
    # --- Nhóm 5: thứ trong tuần, có định tính tuần ---
    (
        re.compile(rf"{_WEEKDAY_TOKEN}\s+tuan (sau|toi)\b"),
        _named_weekday(next_week=True, smart=False, confidence=Confidence.HIGH),
    ),
    (
        re.compile(rf"{_WEEKDAY_TOKEN}\s+tuan nay\b"),
        _named_weekday(next_week=False, smart=True, confidence=Confidence.HIGH),
    ),
    # --- Nhóm 6: thứ trong tuần, không định tính (suy ra lần kế tiếp) ---
    (
        re.compile(rf"\b(truoc|vao|den|trong|ngay)\s+{_WEEKDAY_TOKEN}"),
        _named_weekday(next_week=False, smart=True, confidence=Confidence.HIGH),
    ),
    (
        re.compile(rf"{_WEEKDAY_TOKEN}"),
        _named_weekday(next_week=False, smart=True, confidence=Confidence.MEDIUM),
    ),
    # --- Nhóm 7: tháng ---
    (re.compile(r"\bcuoi thang (sau|toi)\b"), _month_end(1)),
    (re.compile(r"\bcuoi thang( nay)?\b"), _month_end(0)),
    (re.compile(r"\b(dau|giua|trong) thang\b"), _vague("month_part")),
    (re.compile(r"\bthang (sau|toi|\d{1,2})\b"), _vague("whole_month")),
    # --- Nhóm 8: khoảng thời gian tuần, luôn mơ hồ ---
    (re.compile(r"\btuan (sau|toi)\b"), _vague("whole_week")),
    (re.compile(r"\b(trong|cuoi cung trong)? ?tuan nay\b"), _vague("whole_week")),
    (re.compile(r"\btrong tuan\b"), _vague("whole_week")),
    (re.compile(r"\b\d+\s*(tuan|thang|ngay)\s+nua\b"), _vague("relative_duration")),
)


# --------------------------------------------------------------------------- #
# API chính
# --------------------------------------------------------------------------- #


def resolve_vietnamese_date(
    due_raw: str | None,
    anchor_date: dt.date,
    *,
    allow_past: bool = False,
    max_horizon_days: int = MAX_PLAUSIBLE_HORIZON_DAYS,
) -> DateResolution:
    """Quy đổi một biểu thức thời gian tiếng Việt thành ngày tuyệt đối.

    Args:
        due_raw: Chuỗi NGUYÊN VĂN như đã nói trong cuộc họp ("cuối tuần này").
            ``None`` nghĩa là không ai nhắc tới mốc thời gian nào.
        anchor_date: Ngày diễn ra cuộc họp. Mọi biểu thức tương đối đều quy
            chiếu về mốc này.
        allow_past: Nếu ``False`` (mặc định), ngày rơi vào quá khứ bị loại vì
            gần như luôn là lỗi quy đổi chứ không phải ý định thật.
        max_horizon_days: Ngưỡng trên để loại kết quả vô lý.

    Returns:
        ``DateResolution``. Luôn kiểm tra ``.date is None`` trước khi dùng —
        ``None`` là kết quả hợp lệ và thường xuyên đúng.
    """
    if due_raw is None or not due_raw.strip():
        return DateResolution(
            date=None,
            rule=ResolutionRule.NOT_MENTIONED,
            raw=due_raw,
            note="Không ai nêu mốc thời gian. Không được suy diễn.",
        )

    text = normalize_vietnamese(due_raw)

    for pattern, handler in _RULES:
        match = pattern.search(text)
        if match is None:
            continue

        result = handler(match, anchor_date)
        result = DateResolution(
            date=result.date,
            rule=result.rule,
            confidence=result.confidence,
            raw=due_raw,
            detail=result.detail,
            note=result.note,
        )

        if result.date is None:
            return result

        if not allow_past and result.date < anchor_date:
            return DateResolution(
                date=None,
                rule=ResolutionRule.REJECTED_PAST_DATE,
                raw=due_raw,
                detail=result.rule_display,
                note=(
                    f"Quy đổi ra {result.date.isoformat()}, sớm hơn ngày họp "
                    f"{anchor_date.isoformat()}. Loại bỏ vì gần như chắc chắn là lỗi."
                ),
            )

        if (result.date - anchor_date).days > max_horizon_days:
            return DateResolution(
                date=None,
                rule=ResolutionRule.REJECTED_IMPLAUSIBLE,
                raw=due_raw,
                detail=result.rule_display,
                note=(
                    f"Quy đổi ra {result.date.isoformat()}, xa hơn "
                    f"{max_horizon_days} ngày so với ngày họp."
                ),
            )

        return result

    return DateResolution(
        date=None,
        rule=ResolutionRule.UNPARSEABLE,
        raw=due_raw,
        note="Không khớp luật nào. Giữ nguyên due_raw để người dùng tự quyết.",
    )
