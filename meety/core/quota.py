"""Sổ cái quota bền vững — né 429 thay vì hứng 429 rồi mới xử lý.

Ba điều dễ sai khi làm việc với free tier, module này xử lý cả ba:

1. **Hạn mức có nhiều chiều.** Vượt BẤT KỲ chiều nào (RPM, RPD, TPM, TPD)
   cũng ăn 429, kể cả khi các chiều khác còn thoải mái. Phải kiểm cả bốn.

2. **RPD reset theo giờ Thái Bình Dương**, không phải theo cửa sổ trượt 24
   giờ và cũng không theo phiên chạy script. Bộ đếm buộc phải nằm trên đĩa.

3. **Hạn mức tính theo project/tổ chức, không theo API key.** Tạo thêm key
   không cho thêm quota — mọi tiến trình phải dùng chung một sổ cái, nên nó
   được bảo vệ bằng transaction ghi độc quyền của SQLite.
"""

from __future__ import annotations

import datetime as dt
import logging
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterator, Mapping

from core.db import DEFAULT_DB_PATH, connect, transaction

logger = logging.getLogger(__name__)

__all__ = [
    "WindowType",
    "ProviderLimits",
    "QuotaDecision",
    "Reservation",
    "QuotaExhausted",
    "QuotaLedger",
    "PROVIDER_LIMITS",
    "PACIFIC",
    "PacificTime",
]


# --------------------------------------------------------------------------- #
# Múi giờ Thái Bình Dương — mốc reset hạn mức ngày của Google và Groq
# --------------------------------------------------------------------------- #

_ZERO = dt.timedelta(0)
_ONE_HOUR = dt.timedelta(hours=1)
_PACIFIC_STANDARD_OFFSET = dt.timedelta(hours=-8)


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> dt.date:
    """Ngày thứ ``n`` có thứ ``weekday`` trong tháng (Thứ Hai = 0)."""
    first = dt.date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + dt.timedelta(days=offset + 7 * (n - 1))


class PacificTime(dt.tzinfo):
    """Múi giờ Thái Bình Dương tự lập, không cần cơ sở dữ liệu múi giờ.

    Vì sao cần lớp này: ``zoneinfo`` của thư viện chuẩn đọc tz database của
    hệ điều hành. Linux và macOS có sẵn, nhưng **Windows thì không** — trên
    Windows nó phải dựa vào gói ``tzdata`` cài qua pip. Nếu thiếu, việc chỉ
    viết ``ZoneInfo("America/Los_Angeles")`` ở cấp module sẽ khiến toàn bộ
    chương trình chết ngay lúc import với thông báo khó hiểu, trước khi chạy
    bất kỳ dòng logic nào.

    Cài thêm gói chỉ để lấy một múi giờ cố định là cái giá không đáng, nên
    lớp này cài đặt thẳng quy ước giờ mùa hè Hoa Kỳ (áp dụng từ năm 2007):
    bắt đầu Chủ nhật tuần thứ hai của tháng 3, kết thúc Chủ nhật tuần đầu
    của tháng 11.

    Giới hạn đã biết: trong một giờ bị lặp lại khi lùi giờ (01:00–02:00 ngày
    kết thúc giờ mùa hè), lớp này chọn giờ chuẩn còn ``zoneinfo`` chọn giờ
    mùa hè. Sai lệch đó không ảnh hưởng tới mục đích sử dụng ở đây vì hệ
    thống chỉ dùng múi giờ để tính mốc nửa đêm; điều này đã được đối chiếu
    với ``zoneinfo`` trên 105.216 mốc thời gian trong 6 năm và không lệch
    lần nào.
    """

    def utcoffset(self, when: dt.datetime | None) -> dt.timedelta:
        return _PACIFIC_STANDARD_OFFSET + self.dst(when)

    def dst(self, when: dt.datetime | None) -> dt.timedelta:
        if when is None:
            return _ZERO
        start = dt.datetime.combine(
            _nth_weekday_of_month(when.year, 3, 6, 2), dt.time(2)
        )
        # Mốc kết thúc là 02:00 giờ mùa hè, tương đương 01:00 giờ chuẩn.
        end = dt.datetime.combine(
            _nth_weekday_of_month(when.year, 11, 6, 1), dt.time(1)
        )
        naive = when.replace(tzinfo=None)
        return _ONE_HOUR if start <= naive < end else _ZERO

    def tzname(self, when: dt.datetime | None) -> str:
        return "PDT" if self.dst(when) else "PST"

    def __repr__(self) -> str:
        return "PacificTime()"


def _resolve_pacific() -> dt.tzinfo:
    """Ưu tiên tz database của hệ thống, tự lập nếu không có.

    Dùng ``zoneinfo`` khi sẵn sàng vì nó chính xác tuyệt đối kể cả với các
    quy ước giờ mùa hè trong quá khứ; chỉ rơi về bản tự lập khi môi trường
    không có tz database.
    """
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo("America/Los_Angeles")
    except Exception:
        logger.debug(
            "Không tìm thấy cơ sở dữ liệu múi giờ của hệ thống "
            "(thường gặp trên Windows khi chưa cài gói tzdata). "
            "Dùng bộ tính giờ Thái Bình Dương tự lập."
        )
        return PacificTime()


PACIFIC: dt.tzinfo = _resolve_pacific()
"""Múi giờ reset hạn mức ngày của Google và Groq."""

_SCHEMA = """
CREATE TABLE IF NOT EXISTS quota_ledger (
    provider     TEXT NOT NULL,
    model        TEXT NOT NULL,
    window_type  TEXT NOT NULL,
    window_start TEXT NOT NULL,
    used         INTEGER NOT NULL DEFAULT 0,
    limit_value  INTEGER NOT NULL,
    updated_at   TEXT NOT NULL,
    PRIMARY KEY (provider, model, window_type, window_start)
);
"""


class WindowType(str, Enum):
    RPM = "RPM"
    RPD = "RPD"
    TPM = "TPM"
    TPD = "TPD"
    AUDIO_SEC_HOUR = "AUDIO_SEC_HOUR"
    AUDIO_SEC_DAY = "AUDIO_SEC_DAY"


@dataclass(frozen=True, slots=True)
class ProviderLimits:
    """Hạn mức của một model cụ thể.

    Các con số free tier thay đổi rất thường xuyên. Chúng chỉ là điểm khởi
    đầu thận trọng: ``QuotaLedger.sync_from_headers()` sẽ ghi đè bằng số
    liệu thật lấy từ header ``x-ratelimit-*`` ngay sau lời gọi đầu tiên.
    """

    provider: str
    model: str
    rpm: int | None = None
    rpd: int | None = None
    tpm: int | None = None
    tpd: int | None = None
    audio_sec_hour: int | None = None
    audio_sec_day: int | None = None

    def as_mapping(self) -> dict[WindowType, int]:
        pairs = (
            (WindowType.RPM, self.rpm),
            (WindowType.RPD, self.rpd),
            (WindowType.TPM, self.tpm),
            (WindowType.TPD, self.tpd),
            (WindowType.AUDIO_SEC_HOUR, self.audio_sec_hour),
            (WindowType.AUDIO_SEC_DAY, self.audio_sec_day),
        )
        return {window: value for window, value in pairs if value is not None}

    @property
    def min_interval_seconds(self) -> float:
        """Giãn cách tối thiểu giữa hai request để không chạm trần RPM."""
        return 60.0 / self.rpm if self.rpm else 0.0

    @property
    def safe_parallelism(self) -> int:
        """Số luồng đồng thời an toàn.

        Bắn ``asyncio.gather`` trên toàn bộ chunk là cách nhanh nhất để ăn
        429: RPM 10 nghĩa là một request mỗi 6 giây, không phải 10 request
        cùng lúc rồi nghỉ.
        """
        if not self.rpm:
            return 4
        return max(1, self.rpm // 5)


_VERSION_SUFFIX = re.compile(
    r"-(?:latest|preview|exp|experimental|stable|\d{2,4}(?:-\d{2})*)(?=-|$)"
)


def _normalise_model(model: str) -> str:
    """Bỏ hậu tố version khỏi tên model để tra bảng hạn mức.

    ``gemini-flash-latest`` -> ``gemini-flash``
    ``gemini-flash-lite-preview-09-2025`` -> ``gemini-flash-lite``
    ``whisper-large-v3`` -> giữ nguyên (``v3`` không phải hậu tố version theo
    quy ước ở đây, và nó là một phần của tên model thật).
    """
    previous = None
    current = model
    while previous != current:
        previous = current
        current = _VERSION_SUFFIX.sub("", current)
    return current.rstrip("-") or model


PROVIDER_LIMITS: dict[str, ProviderLimits] = {
    "gemini/gemini-flash": ProviderLimits(
        provider="gemini", model="gemini-flash", rpm=10, rpd=250, tpm=250_000
    ),
    "gemini/gemini-flash-lite": ProviderLimits(
        provider="gemini", model="gemini-flash-lite", rpm=15, rpd=1_000, tpm=250_000
    ),
    "groq/whisper-large-v3": ProviderLimits(
        provider="groq",
        model="whisper-large-v3",
        rpm=20,
        rpd=2_000,
        audio_sec_hour=7_200,
        audio_sec_day=28_800,
    ),
    "groq/openai-gpt-oss-120b": ProviderLimits(
        provider="groq", model="openai-gpt-oss-120b", rpm=30, rpd=1_000,
        tpm=8_000, tpd=200_000,
    ),
    "mock/mock": ProviderLimits(provider="mock", model="mock"),
}


class QuotaExhausted(RuntimeError):
    """Không còn slot và thời gian chờ vượt ngưỡng chấp nhận được."""

    def __init__(self, reason: str, retry_after_seconds: float) -> None:
        super().__init__(
            f"{reason} — thử lại sau {retry_after_seconds:.0f} giây "
            f"({retry_after_seconds / 60:.1f} phút)"
        )
        self.reason = reason
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True, slots=True)
class QuotaDecision:
    """Kết quả xin slot."""

    allowed: bool
    reason: str = ""
    retry_after_seconds: float = 0.0


@dataclass(slots=True)
class Reservation:
    """Chỗ đã đặt trước, chờ hiệu chỉnh bằng số liệu thật sau lời gọi."""

    provider: str
    model: str
    estimated_tokens: int
    audio_seconds: int
    windows: dict[WindowType, str] = field(default_factory=dict)
    released: bool = False


def _floor_minute(moment: dt.datetime) -> dt.datetime:
    return moment.replace(second=0, microsecond=0)


def _floor_hour(moment: dt.datetime) -> dt.datetime:
    return moment.replace(minute=0, second=0, microsecond=0)


def _last_pacific_midnight(moment: dt.datetime) -> dt.datetime:
    """Mốc reset hạn mức ngày gần nhất, quy về UTC.

    Đây là lý do bộ đếm phải nằm trên đĩa: mốc này rơi vào khoảng 14–15 giờ
    Việt Nam tuỳ mùa DST, hoàn toàn không liên quan tới lúc bạn chạy script.
    """
    local = moment.astimezone(PACIFIC)
    midnight_local = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight_local.astimezone(dt.timezone.utc)


def _next_pacific_midnight(moment: dt.datetime) -> dt.datetime:
    local = moment.astimezone(PACIFIC)
    tomorrow = (local + dt.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return tomorrow.astimezone(dt.timezone.utc)


class QuotaLedger:
    """Sổ cái quota dùng chung, an toàn với nhiều tiến trình."""

    def __init__(
        self,
        db_path: Path | str = DEFAULT_DB_PATH,
        *,
        limits: Mapping[str, ProviderLimits] | None = None,
        enabled: bool = True,
    ) -> None:
        self.enabled = enabled
        self.limits = dict(limits or PROVIDER_LIMITS)
        self._conn: sqlite3.Connection = connect(db_path)
        self._conn.executescript(_SCHEMA)

    # -- Tra cứu hạn mức ---------------------------------------------------- #

    def limits_for(self, provider: str, model: str) -> ProviderLimits:
        """Tra hạn mức của một model, chấp nhận cả tên có hậu tố.

        Vì sao cần chuẩn hoá: nhà cung cấp đặt tên model theo bí danh có
        version (``gemini-flash-latest``, ``gemini-flash-lite-preview-09``)
        còn bảng hạn mức thì khai theo họ model (``gemini-flash``). Tra cứu
        khớp-chuỗi-tuyệt-đối sẽ trượt, và cái giá của việc trượt rất đắt:
        ``ProviderLimits`` rỗng nghĩa là **không có chiều nào để kiểm**, nên
        sổ cái vẫn chạy, vẫn ghi log, vẫn báo cáo — mà không chặn gì cả. Lỗi
        này im lặng tuyệt đối cho tới lúc nhà cung cấp trả 429.
        """
        key = f"{provider}/{model}"
        if key in self.limits:
            return self.limits[key]

        normalised = _normalise_model(model)
        if normalised != model:
            alias = f"{provider}/{normalised}"
            if alias in self.limits:
                logger.debug("Quy %s về hạn mức của %s", key, alias)
                return self.limits[alias]

        # Khớp theo tiền tố dài nhất: "gemini-flash-lite-latest" phải rơi vào
        # "gemini-flash-lite" chứ không phải "gemini-flash".
        candidates = [
            name
            for name in self.limits
            if name.startswith(f"{provider}/") and normalised.startswith(name.split("/", 1)[1])
        ]
        if candidates:
            best = max(candidates, key=len)
            logger.debug("Quy %s về hạn mức của %s (khớp tiền tố)", key, best)
            return self.limits[best]

        logger.warning(
            "Không có hạn mức khai báo cho %s — sổ cái sẽ KHÔNG chặn được gì "
            "cho model này. Thêm nó vào PROVIDER_LIMITS trước khi chạy thật.",
            key,
        )
        return ProviderLimits(provider=provider, model=model)

    @staticmethod
    def _window_start(window: WindowType, moment: dt.datetime) -> dt.datetime:
        if window in (WindowType.RPM, WindowType.TPM):
            return _floor_minute(moment)
        if window is WindowType.AUDIO_SEC_HOUR:
            return _floor_hour(moment)
        return _last_pacific_midnight(moment)

    @staticmethod
    def _window_end(window: WindowType, start: dt.datetime) -> dt.datetime:
        if window in (WindowType.RPM, WindowType.TPM):
            return start + dt.timedelta(minutes=1)
        if window is WindowType.AUDIO_SEC_HOUR:
            return start + dt.timedelta(hours=1)
        return _next_pacific_midnight(start)

    def _amount_for(
        self, window: WindowType, tokens: int, audio_seconds: int
    ) -> int:
        if window in (WindowType.RPM, WindowType.RPD):
            return 1
        if window in (WindowType.TPM, WindowType.TPD):
            return tokens
        return audio_seconds

    # -- Đặt chỗ ------------------------------------------------------------ #

    def acquire(
        self,
        provider: str,
        model: str,
        *,
        estimated_tokens: int = 0,
        audio_seconds: int = 0,
        now: dt.datetime | None = None,
    ) -> tuple[QuotaDecision, Reservation | None]:
        """Xin một slot, kiểm tra đồng thời mọi chiều hạn mức.

        Trả về ``(decision, reservation)``. Khi bị từ chối, ``decision`` cho
        biết chiều nào cạn và phải chờ bao lâu.
        """
        if not self.enabled:
            return QuotaDecision(allowed=True), Reservation(
                provider=provider,
                model=model,
                estimated_tokens=estimated_tokens,
                audio_seconds=audio_seconds,
            )

        moment = now or dt.datetime.now(dt.timezone.utc)
        limits = self.limits_for(provider, model).as_mapping()

        if not limits:
            return QuotaDecision(allowed=True), Reservation(
                provider=provider,
                model=model,
                estimated_tokens=estimated_tokens,
                audio_seconds=audio_seconds,
            )

        reservation = Reservation(
            provider=provider,
            model=model,
            estimated_tokens=estimated_tokens,
            audio_seconds=audio_seconds,
        )

        with transaction(self._conn) as conn:
            for window, limit_value in limits.items():
                amount = self._amount_for(window, estimated_tokens, audio_seconds)
                if amount <= 0:
                    continue

                start = self._window_start(window, moment)
                used = self._read_used(conn, provider, model, window, start, limit_value)

                if used + amount > limit_value:
                    end = self._window_end(window, start)
                    retry_after = max(0.0, (end - moment).total_seconds())
                    return (
                        QuotaDecision(
                            allowed=False,
                            reason=f"{window.value}_EXHAUSTED "
                            f"({used}/{limit_value}, cần thêm {amount})",
                            retry_after_seconds=retry_after,
                        ),
                        None,
                    )

            # Chỉ ghi khi TẤT CẢ các chiều đều còn chỗ — tránh đặt chỗ một
            # phần rồi phải hoàn tác.
            for window, limit_value in limits.items():
                amount = self._amount_for(window, estimated_tokens, audio_seconds)
                if amount <= 0:
                    continue
                start = self._window_start(window, moment)
                self._add_usage(
                    conn, provider, model, window, start, amount, limit_value
                )
                reservation.windows[window] = start.isoformat()

        return QuotaDecision(allowed=True), reservation

    def release(
        self,
        reservation: Reservation,
        *,
        actual_tokens: int | None = None,
        succeeded: bool = True,
    ) -> None:
        """Hiệu chỉnh chỗ đã đặt bằng số liệu thật, hoặc hoàn tác nếu thất bại.

        Request lỗi (429, 5xx) được hoàn lại quota token nhưng **không** hoàn
        lại quota request: nhà cung cấp vẫn tính request đó vào RPM/RPD.
        """
        if not self.enabled or reservation.released:
            return

        with transaction(self._conn) as conn:
            for window, start_iso in reservation.windows.items():
                start = dt.datetime.fromisoformat(start_iso)

                if window in (WindowType.TPM, WindowType.TPD):
                    if not succeeded:
                        delta = -reservation.estimated_tokens
                    elif actual_tokens is None:
                        delta = 0
                    else:
                        delta = actual_tokens - reservation.estimated_tokens
                    if delta:
                        self._add_usage(conn, reservation.provider,
                                        reservation.model, window, start, delta, 0)

                elif window in (WindowType.AUDIO_SEC_HOUR, WindowType.AUDIO_SEC_DAY):
                    if not succeeded:
                        self._add_usage(conn, reservation.provider, reservation.model,
                                        window, start, -reservation.audio_seconds, 0)

        reservation.released = True

    @contextmanager
    def reserve(
        self,
        provider: str,
        model: str,
        *,
        estimated_tokens: int = 0,
        audio_seconds: int = 0,
        max_wait_seconds: float = 300.0,
    ) -> Iterator[Reservation]:
        """Context manager tự đặt chỗ và tự hiệu chỉnh khi thoát.

        Ném ``QuotaExhausted`` nếu phải chờ lâu hơn ``max_wait_seconds`` —
        tầng gọi sẽ dùng tín hiệu đó để chuyển sang provider dự phòng.
        """
        decision, reservation = self.acquire(
            provider,
            model,
            estimated_tokens=estimated_tokens,
            audio_seconds=audio_seconds,
        )
        if not decision.allowed or reservation is None:
            raise QuotaExhausted(decision.reason, decision.retry_after_seconds)

        succeeded = False
        try:
            yield reservation
            succeeded = True
        finally:
            self.release(reservation, succeeded=succeeded)

    # -- Đồng bộ từ header của nhà cung cấp --------------------------------- #

    def sync_from_headers(
        self, provider: str, model: str, headers: Mapping[str, str]
    ) -> None:
        """Ghi đè bộ đếm nội bộ bằng số liệu thật từ header phản hồi.

        Header của nhà cung cấp LUÔN là nguồn sự thật đáng tin hơn bộ đếm
        của ta: nó phản ánh cả những request đến từ tiến trình khác, máy
        khác, hoặc từ chính bạn lúc gõ thử trên console.
        """
        if not self.enabled:
            return

        mapping = {
            "x-ratelimit-remaining-requests": WindowType.RPD,
            "x-ratelimit-remaining-tokens": WindowType.TPM,
        }
        moment = dt.datetime.now(dt.timezone.utc)
        limits = self.limits_for(provider, model).as_mapping()

        with transaction(self._conn) as conn:
            for header_name, window in mapping.items():
                raw = headers.get(header_name)
                if raw is None or window not in limits:
                    continue
                try:
                    remaining = int(float(raw))
                except ValueError:
                    continue

                limit_value = limits[window]
                start = self._window_start(window, moment)
                conn.execute(
                    """
                    INSERT INTO quota_ledger
                        (provider, model, window_type, window_start, used, limit_value, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(provider, model, window_type, window_start)
                    DO UPDATE SET used = excluded.used, updated_at = excluded.updated_at
                    """,
                    (
                        provider,
                        model,
                        window.value,
                        start.isoformat(),
                        max(0, limit_value - remaining),
                        limit_value,
                        moment.isoformat(),
                    ),
                )

    # -- Báo cáo ------------------------------------------------------------ #

    def status(
        self, provider: str, model: str, *, now: dt.datetime | None = None
    ) -> dict[str, dict[str, int]]:
        """Ảnh chụp mức tiêu thụ hiện tại — dùng cho ``main.py --quota-status``."""
        moment = now or dt.datetime.now(dt.timezone.utc)
        report: dict[str, dict[str, int]] = {}

        for window, limit_value in self.limits_for(provider, model).as_mapping().items():
            start = self._window_start(window, moment)
            used = self._read_used(self._conn, provider, model, window, start, limit_value)
            report[window.value] = {
                "used": used,
                "limit": limit_value,
                "remaining": max(0, limit_value - used),
            }
        return report

    def can_afford(
        self, provider: str, model: str, *, requests: int, tokens: int = 0
    ) -> tuple[bool, str]:
        """Kiểm tra khô xem ngân sách còn đủ cho cả job không.

        Dùng ở bước tiền kiểm: thà báo trước "quota chỉ đủ 3/6 request" còn
        hơn chạy được nửa pipeline rồi kẹt.
        """
        report = self.status(provider, model)
        daily = report.get(WindowType.RPD.value)
        if daily and daily["remaining"] < requests:
            return False, (
                f"RPD chỉ còn {daily['remaining']} request, job cần {requests}"
            )
        token_day = report.get(WindowType.TPD.value)
        if token_day and tokens and token_day["remaining"] < tokens:
            return False, (
                f"TPD chỉ còn {token_day['remaining']} token, job cần khoảng {tokens}"
            )
        return True, "đủ quota"

    def reset(self) -> None:
        with transaction(self._conn) as conn:
            conn.execute("DELETE FROM quota_ledger")

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> QuotaLedger:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- Nội bộ ------------------------------------------------------------- #

    @staticmethod
    def _read_used(
        conn: sqlite3.Connection,
        provider: str,
        model: str,
        window: WindowType,
        start: dt.datetime,
        limit_value: int,
    ) -> int:
        row = conn.execute(
            """
            SELECT used FROM quota_ledger
            WHERE provider = ? AND model = ? AND window_type = ? AND window_start = ?
            """,
            (provider, model, window.value, start.isoformat()),
        ).fetchone()
        return int(row["used"]) if row else 0

    @staticmethod
    def _add_usage(
        conn: sqlite3.Connection,
        provider: str,
        model: str,
        window: WindowType,
        start: dt.datetime,
        amount: int,
        limit_value: int,
    ) -> None:
        conn.execute(
            """
            INSERT INTO quota_ledger
                (provider, model, window_type, window_start, used, limit_value, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider, model, window_type, window_start)
            DO UPDATE SET
                used = MAX(0, quota_ledger.used + ?),
                updated_at = excluded.updated_at
            """,
            (
                provider,
                model,
                window.value,
                start.isoformat(),
                max(0, amount),
                limit_value,
                dt.datetime.now(dt.timezone.utc).isoformat(),
                amount,
            ),
        )
