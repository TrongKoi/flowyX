"""Kiểm thử bộ tính múi giờ Thái Bình Dương tự lập.

Lớp ``PacificTime`` tồn tại để hệ thống chạy được trên Windows mà không cần
cài gói ``tzdata``. Vì nó thay thế một thành phần của thư viện chuẩn, nó
phải được đối chiếu trực tiếp với ``zoneinfo`` — và quan trọng hơn, phải
được kiểm thử trong đúng điều kiện thiếu tz database.

Nghịch lý của chính file này
----------------------------
Phép đối chiếu cần ``zoneinfo`` để làm đáp án chuẩn, nhưng môi trường mà
``PacificTime`` sinh ra để phục vụ lại chính là môi trường **không có**
``zoneinfo`` dùng được. Nên các test đối chiếu phải tự bỏ qua khi thiếu tz
database, còn các test về bản thân ``PacificTime`` thì luôn chạy.

Phân biệt quan trọng: ``import zoneinfo`` **luôn thành công** từ Python 3.9
vì đó là thư viện chuẩn. Thứ thiếu trên Windows là **cơ sở dữ liệu** múi
giờ, và nó chỉ báo lỗi lúc ``ZoneInfo("America/Los_Angeles")`` được gọi.
Kiểm tra bằng ``pytest.importorskip("zoneinfo")`` là kiểm nhầm chỗ.
"""

from __future__ import annotations

import datetime as dt

import pytest

from core.quota import PacificTime, QuotaLedger, WindowType, _nth_weekday_of_month

FALLBACK = PacificTime()

try:
    from zoneinfo import ZoneInfo

    REAL: "ZoneInfo | None" = ZoneInfo("America/Los_Angeles")
    TZDATA_REASON = ""
except Exception as exc:  # ZoneInfoNotFoundError, hoặc bất kỳ lỗi nạp nào
    REAL = None
    TZDATA_REASON = (
        "Không có cơ sở dữ liệu múi giờ của hệ thống — thường gặp trên Windows. "
        "Chạy `python -m pip install tzdata` để bật nhóm test đối chiếu này. "
        f"Chi tiết: {exc}"
    )

needs_tzdata = pytest.mark.skipif(REAL is None, reason=TZDATA_REASON)


class TestNthWeekday:
    def test_second_sunday_of_march(self) -> None:
        assert _nth_weekday_of_month(2026, 3, 6, 2) == dt.date(2026, 3, 8)
        assert _nth_weekday_of_month(2027, 3, 6, 2) == dt.date(2027, 3, 14)

    def test_first_sunday_of_november(self) -> None:
        assert _nth_weekday_of_month(2026, 11, 6, 1) == dt.date(2026, 11, 1)
        assert _nth_weekday_of_month(2027, 11, 6, 1) == dt.date(2027, 11, 7)

    def test_result_is_always_the_requested_weekday(self) -> None:
        for year in range(2024, 2031):
            for month in range(1, 13):
                for weekday in range(7):
                    result = _nth_weekday_of_month(year, month, weekday, 1)
                    assert result.weekday() == weekday
                    assert result.month == month


class TestOffsetMatchesZoneinfo:
    @pytest.mark.parametrize(
        "moment, expected_hours",
        [
            (dt.datetime(2026, 1, 15, 12, tzinfo=dt.timezone.utc), -8),
            (dt.datetime(2026, 7, 22, 12, tzinfo=dt.timezone.utc), -7),
            (dt.datetime(2026, 3, 7, 12, tzinfo=dt.timezone.utc), -8),
            (dt.datetime(2026, 3, 9, 12, tzinfo=dt.timezone.utc), -7),
            (dt.datetime(2026, 10, 31, 12, tzinfo=dt.timezone.utc), -7),
            (dt.datetime(2026, 11, 2, 12, tzinfo=dt.timezone.utc), -8),
        ],
    )
    def test_known_offsets(self, moment: dt.datetime, expected_hours: int) -> None:
        assert moment.astimezone(FALLBACK).utcoffset() == dt.timedelta(
            hours=expected_hours
        )

    @needs_tzdata
    def test_matches_zoneinfo_every_six_hours_for_six_years(self) -> None:
        """Đối chiếu toàn diện, bỏ qua giờ bị lặp khi lùi giờ.

        Trong khoảng 01:00–02:00 của ngày kết thúc giờ mùa hè, cùng một giờ
        đồng hồ xuất hiện hai lần. ``zoneinfo`` chọn lần đầu (giờ mùa hè),
        bản tự lập chọn giờ chuẩn. Sai lệch này không ảnh hưởng tới việc tính
        mốc nửa đêm nên được chấp nhận có ý thức.
        """
        moment = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)
        end = dt.datetime(2030, 1, 1, tzinfo=dt.timezone.utc)
        mismatches: list[dt.datetime] = []

        while moment < end:
            local = moment.astimezone(REAL)
            is_ambiguous_hour = local.month == 11 and local.hour == 1
            if not is_ambiguous_hour:
                if moment.astimezone(REAL).utcoffset() != moment.astimezone(
                    FALLBACK
                ).utcoffset():
                    mismatches.append(moment)
            moment += dt.timedelta(hours=6)

        assert not mismatches, f"Lệch so với zoneinfo tại: {mismatches[:5]}"

    def test_tzname_reports_correct_abbreviation(self) -> None:
        winter = dt.datetime(2026, 1, 15, 12, tzinfo=dt.timezone.utc)
        summer = dt.datetime(2026, 7, 15, 12, tzinfo=dt.timezone.utc)
        assert winter.astimezone(FALLBACK).tzname() == "PST"
        assert summer.astimezone(FALLBACK).tzname() == "PDT"


class TestQuotaWindowsAreIdentical:
    """Bất biến thực sự quan trọng: mốc reset quota phải trùng khít.

    Hệ thống chỉ dùng múi giờ cho đúng một việc — xác định nửa đêm giờ Thái
    Bình Dương. Nếu phép tính đó khớp với ``zoneinfo`` thì bản tự lập là
    thay thế an toàn, bất kể vài khác biệt ở giờ bị lặp.
    """

    @staticmethod
    def _last_midnight(moment: dt.datetime, tz: dt.tzinfo) -> dt.datetime:
        local = moment.astimezone(tz)
        midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
        return midnight.astimezone(dt.timezone.utc)

    @staticmethod
    def _next_midnight(moment: dt.datetime, tz: dt.tzinfo) -> dt.datetime:
        local = moment.astimezone(tz)
        tomorrow = (local + dt.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return tomorrow.astimezone(dt.timezone.utc)

    @needs_tzdata
    def test_daily_reset_boundaries_match_zoneinfo(self) -> None:
        moment = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
        end = dt.datetime(2029, 1, 1, tzinfo=dt.timezone.utc)
        mismatches: list[dt.datetime] = []

        while moment < end:
            if self._last_midnight(moment, REAL) != self._last_midnight(
                moment, FALLBACK
            ) or self._next_midnight(moment, REAL) != self._next_midnight(
                moment, FALLBACK
            ):
                mismatches.append(moment)
            moment += dt.timedelta(hours=3)

        assert not mismatches, f"Mốc reset quota lệch tại: {mismatches[:5]}"


class TestWorksWithoutTimezoneDatabase:
    """Kiểm thử trong đúng điều kiện gây lỗi trên Windows."""

    def test_quota_ledger_runs_without_system_tz_database(self) -> None:
        import zoneinfo

        original_paths = tuple(zoneinfo.TZPATH)
        try:
            zoneinfo.reset_tzpath([])
            # Bỏ đường dẫn thôi là chưa đủ: ZoneInfo giữ cache các múi giờ đã
            # nạp, nên nếu không xoá cache thì lần gọi sau vẫn thành công và
            # bài kiểm thử này sẽ không tái hiện được lỗi trên Windows.
            zoneinfo.ZoneInfo.clear_cache()

            from core.quota import ProviderLimits, QuotaLedger, _resolve_pacific

            tz = _resolve_pacific()
            assert isinstance(tz, PacificTime), (
                "Không có tz database mà vẫn không rơi về bản tự lập"
            )

            ledger = QuotaLedger(
                ":memory:",
                limits={
                    "t/m": ProviderLimits(provider="t", model="m", rpm=2, rpd=5)
                },
            )
            first, _ = ledger.acquire("t", "m")
            second, _ = ledger.acquire("t", "m")
            third, _ = ledger.acquire("t", "m")
            ledger.close()

            assert first.allowed and second.allowed
            assert not third.allowed
            assert "RPM" in third.reason
        finally:
            zoneinfo.reset_tzpath(original_paths)
            zoneinfo.ZoneInfo.clear_cache()


# --------------------------------------------------------------------------- #
# Chuẩn hoá tên model — khoá lại lỗi sổ cái quota bị vô hiệu
# --------------------------------------------------------------------------- #


class TestModelAliasResolution:
    """Bí danh model phải quy được về hạn mức đã khai.

    Lỗi gốc: ``main.py`` mặc định dùng ``gemini-flash-latest`` nhưng bảng
    hạn mức khai ``gemini-flash``. Tra cứu trượt trả về ``ProviderLimits``
    rỗng — không có chiều nào để kiểm, nên sổ cái chạy mà không chặn gì.
    Im lặng tuyệt đối cho tới lúc nhà cung cấp trả 429 giữa chừng.
    """

    def test_hau_to_latest_quy_ve_ho_model(self, tmp_path) -> None:
        with QuotaLedger(tmp_path / "q.db") as quota:
            limits = quota.limits_for("gemini", "gemini-flash-latest")
            assert limits.as_mapping()[WindowType.RPD] == 250

    def test_flash_lite_khong_bi_nham_sang_flash(self, tmp_path) -> None:
        """Khớp tiền tố phải chọn khoá DÀI NHẤT, không phải khoá đầu tiên."""
        with QuotaLedger(tmp_path / "q.db") as quota:
            limits = quota.limits_for("gemini", "gemini-flash-lite-latest")
            assert limits.as_mapping()[WindowType.RPD] == 1_000

    def test_hau_to_preview_co_ngay_thang(self, tmp_path) -> None:
        with QuotaLedger(tmp_path / "q.db") as quota:
            limits = quota.limits_for("gemini", "gemini-flash-lite-preview-09-2025")
            assert limits.as_mapping()[WindowType.RPD] == 1_000

    def test_ten_model_that_khong_bi_cat(self, tmp_path) -> None:
        """``whisper-large-v3``: ``v3`` là một phần của tên, không phải version."""
        with QuotaLedger(tmp_path / "q.db") as quota:
            limits = quota.limits_for("groq", "whisper-large-v3")
            assert limits.as_mapping()[WindowType.AUDIO_SEC_DAY] == 28_800

    def test_so_cai_thuc_su_chan_voi_ten_mac_dinh_cua_main(self, tmp_path) -> None:
        """Phép thử hồi quy trực tiếp cho lỗi gốc."""
        with QuotaLedger(tmp_path / "q.db") as quota:
            blocked_at = None
            for index in range(50):
                decision, reservation = quota.acquire(
                    "gemini", "gemini-flash-latest", estimated_tokens=1_000
                )
                if not decision.allowed:
                    blocked_at = index
                    break
                if reservation is not None:
                    quota.release(reservation, succeeded=True, actual_tokens=1_000)
            assert blocked_at == 10  # đúng trần RPM của gemini-flash

    def test_model_la_hoan_toan_van_chay_nhung_canh_bao(self, tmp_path) -> None:
        with QuotaLedger(tmp_path / "q.db") as quota:
            limits = quota.limits_for("gemini", "mot-model-chua-tung-co")
            assert limits.as_mapping() == {}
