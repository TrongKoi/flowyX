"""Unit test cho bộ quy đổi ngày tương đối tiếng Việt.

Đây là file test cần viết ĐẦU TIÊN của toàn dự án. Lý do: một lỗi lệch một
đơn vị trong ánh xạ "thứ 2 = Monday" sẽ làm sai TOÀN BỘ deadline trong hệ
thống, và kết quả sai vẫn là một ngày trông hoàn toàn hợp lý nên không thể
phát hiện bằng mắt khi review biên bản.

Toàn bộ test ở đây chạy offline, không gọi API, không tốn quota.
"""

from __future__ import annotations

import datetime as dt

import pytest

from nlp.vn_dates import (
    DateResolution,
    ResolutionRule,
    next_week_weekday,
    normalize_vietnamese,
    resolve_vietnamese_date,
    this_week_weekday,
    this_week_weekday_smart,
)
from schemas.common import Confidence

# Ngày họp trong test case mẫu: Thứ Tư 22/07/2026.
#
#   T2 20/07 | T3 21/07 | T4 22/07 (HỌP) | T5 23/07 | T6 24/07 | T7 25/07 | CN 26/07
#   Tuần sau: T2 27/07 | T3 28/07 | T4 29/07 | ...
ANCHOR = dt.date(2026, 7, 22)


def R(raw: str | None, anchor: dt.date = ANCHOR) -> DateResolution:
    """Bí danh ngắn cho hàm cần test."""
    return resolve_vietnamese_date(raw, anchor)


# --------------------------------------------------------------------------- #
# Kiểm tra tiền đề của bộ test
# --------------------------------------------------------------------------- #


def test_anchor_is_wednesday() -> None:
    """Mọi kỳ vọng bên dưới đều dựa trên giả định này."""
    assert ANCHOR.weekday() == 2
    assert ANCHOR.strftime("%A") == "Wednesday"


# --------------------------------------------------------------------------- #
# Bốn luật chính theo bản thiết kế
# --------------------------------------------------------------------------- #


class TestCoreRules:
    """Bốn luật được nêu đích danh trong Backend Design v1.0."""

    def test_truoc_thu_6_gives_this_week_friday(self) -> None:
        result = R("trước thứ 6")
        assert result.date == dt.date(2026, 7, 24)
        assert result.rule is ResolutionRule.THIS_WEEK_WEEKDAY_SMART
        assert result.detail == "friday"
        assert result.date.weekday() == 4

    def test_cuoi_tuan_nay_gives_this_week_sunday(self) -> None:
        result = R("cuối tuần này")
        assert result.date == dt.date(2026, 7, 26)
        assert result.rule is ResolutionRule.THIS_WEEK_WEEKDAY
        assert result.date.weekday() == 6

    def test_thu_3_tuan_sau_gives_next_week_tuesday(self) -> None:
        result = R("thứ 3 tuần sau")
        assert result.date == dt.date(2026, 7, 28)
        assert result.rule is ResolutionRule.NEXT_WEEK_WEEKDAY
        assert result.detail == "tuesday"
        assert result.date.weekday() == 1

    @pytest.mark.parametrize(
        "raw", ["tuần sau", "đầu tháng 8", "sau Tết", "trong tuần"]
    )
    def test_vague_expressions_return_none(self, raw: str) -> None:
        """MƠ HỒ PHẢI TRẢ NONE. Đây là hành vi đúng, không phải thất bại.

        Bịa ra một deadline không ai nói tệ hơn nhiều so với để trống.
        """
        result = R(raw)
        assert result.date is None, f"{raw!r} lẽ ra phải trả None, nhận {result.date}"
        assert result.rule is ResolutionRule.TOO_VAGUE
        assert result.confidence is None


# --------------------------------------------------------------------------- #
# Ánh xạ thứ trong tuần
# --------------------------------------------------------------------------- #


class TestVietnameseWeekdayMapping:
    """Bẫy kinh điển: "thứ 2" là Monday, KHÔNG phải Tuesday."""

    @pytest.mark.parametrize(
        "raw, expected_weekday",
        [
            ("thứ 2 tuần sau", 0),
            ("thứ 3 tuần sau", 1),
            ("thứ 4 tuần sau", 2),
            ("thứ 5 tuần sau", 3),
            ("thứ 6 tuần sau", 4),
            ("thứ 7 tuần sau", 5),
            ("chủ nhật tuần sau", 6),
        ],
    )
    def test_weekday_index(self, raw: str, expected_weekday: int) -> None:
        result = R(raw)
        assert result.date is not None
        assert result.date.weekday() == expected_weekday

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("thứ 2 tuần sau", dt.date(2026, 7, 27)),
            ("thứ 3 tuần sau", dt.date(2026, 7, 28)),
            ("thứ 6 tuần sau", dt.date(2026, 7, 31)),
            ("chủ nhật tuần sau", dt.date(2026, 8, 2)),
        ],
    )
    def test_next_week_exact_dates(self, raw: str, expected: dt.date) -> None:
        assert R(raw).date == expected


# --------------------------------------------------------------------------- #
# Suy luận "lần kế tiếp" khi không định tính tuần
# --------------------------------------------------------------------------- #


class TestSmartWeekdayResolution:
    """Thứ đã trôi qua trong tuần phải nhảy sang tuần sau, không lùi về quá khứ."""

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("trước thứ 5", dt.date(2026, 7, 23)),
            ("trước thứ 6", dt.date(2026, 7, 24)),
            ("trước thứ 7", dt.date(2026, 7, 25)),
            ("trước Chủ nhật", dt.date(2026, 7, 26)),
        ],
    )
    def test_upcoming_weekday_stays_in_this_week(
        self, raw: str, expected: dt.date
    ) -> None:
        assert R(raw).date == expected

    @pytest.mark.parametrize("raw", ["thứ 2", "thứ 3", "trước thứ 2", "vào thứ 3"])
    def test_past_weekday_rolls_to_next_week(self, raw: str) -> None:
        """Thứ 2 và thứ 3 đã qua khi họp vào thứ 4."""
        result = R(raw)
        assert result.date is not None
        assert result.date > ANCHOR
        assert (result.date - ANCHOR).days <= 7

    def test_same_weekday_as_anchor_rolls_forward(self) -> None:
        """"thứ 4" nói vào chính thứ 4 nghĩa là thứ 4 tuần sau."""
        result = R("trước thứ 4")
        assert result.date == dt.date(2026, 7, 29)


# --------------------------------------------------------------------------- #
# Lệch ngày và mốc tháng
# --------------------------------------------------------------------------- #


class TestDayOffsetsAndMonths:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("hôm nay", dt.date(2026, 7, 22)),
            ("ngày mai", dt.date(2026, 7, 23)),
            ("ngày kia", dt.date(2026, 7, 24)),
        ],
    )
    def test_day_offsets(self, raw: str, expected: dt.date) -> None:
        assert R(raw).date == expected

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("cuối tháng", dt.date(2026, 7, 31)),
            ("cuối tháng này", dt.date(2026, 7, 31)),
            ("cuối tháng sau", dt.date(2026, 8, 31)),
        ],
    )
    def test_month_end(self, raw: str, expected: dt.date) -> None:
        assert R(raw).date == expected

    def test_month_end_handles_february(self) -> None:
        """Tháng 2 năm 2028 là năm nhuận — 29 ngày."""
        assert R("cuối tháng", dt.date(2028, 2, 10)).date == dt.date(2028, 2, 29)

    def test_month_end_crosses_year_boundary(self) -> None:
        assert R("cuối tháng sau", dt.date(2026, 12, 5)).date == dt.date(2027, 1, 31)

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("cuối tuần sau", dt.date(2026, 8, 2)),
            ("đầu tuần sau", dt.date(2026, 7, 27)),
        ],
    )
    def test_week_boundaries(self, raw: str, expected: dt.date) -> None:
        assert R(raw).date == expected


# --------------------------------------------------------------------------- #
# Ngày tuyệt đối
# --------------------------------------------------------------------------- #


class TestAbsoluteDates:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("ngày 30/7", dt.date(2026, 7, 30)),
            ("ngày 5/8", dt.date(2026, 8, 5)),
            ("ngày 15/09/2026", dt.date(2026, 9, 15)),
            ("30/7", dt.date(2026, 7, 30)),
            ("01/12/2026", dt.date(2026, 12, 1)),
        ],
    )
    def test_absolute_parsing(self, raw: str, expected: dt.date) -> None:
        assert R(raw).date == expected

    def test_day_month_order_is_vietnamese(self) -> None:
        """Việt Nam dùng dd/mm, không phải mm/dd."""
        assert R("ngày 3/8").date == dt.date(2026, 8, 3)

    def test_year_inferred_forward_when_date_already_passed(self) -> None:
        """"ngày 5/1" nói vào tháng 7 nghĩa là tháng 1 năm sau."""
        assert R("ngày 5/1").date == dt.date(2027, 1, 5)

    def test_invalid_calendar_date_is_rejected(self) -> None:
        result = R("ngày 31/2")
        assert result.date is None
        assert result.rule is ResolutionRule.UNPARSEABLE


# --------------------------------------------------------------------------- #
# Biểu thức mơ hồ — nhóm test quan trọng nhất về mặt chống hallucination
# --------------------------------------------------------------------------- #


class TestVagueExpressions:
    @pytest.mark.parametrize(
        "raw",
        [
            "tuần sau",
            "tuần tới",
            "trong tuần",
            "tuần này",
            "đầu tháng 8",
            "đầu tháng",
            "giữa tháng",
            "tháng sau",
            "sau Tết",
            "trước Tết",
            "ra Tết",
            "sớm nhất có thể",
            "càng sớm càng tốt",
            "sắp tới",
            "thời gian tới",
            "khi nào xong",
            "lúc nào rảnh",
            "asap",
            "khẩn cấp",
            "3 tuần nữa",
            "2 tháng nữa",
        ],
    )
    def test_vague_returns_none_with_too_vague_rule(self, raw: str) -> None:
        result = R(raw)
        assert result.date is None, f"{raw!r} lẽ ra phải trả None"
        assert result.rule is ResolutionRule.TOO_VAGUE
        assert result.raw == raw

    def test_urgency_words_are_not_dates(self) -> None:
        """"gấp"/"asap" là ĐỘ ƯU TIÊN, không phải mốc thời gian."""
        for raw in ["asap", "càng sớm càng tốt"]:
            assert R(raw).date is None

    def test_vague_result_carries_explanation(self) -> None:
        result = R("tuần sau")
        assert result.note is not None
        assert result.detail == "whole_week"


# --------------------------------------------------------------------------- #
# Đầu vào rỗng và không phân tích được
# --------------------------------------------------------------------------- #


class TestNullAndUnparseable:
    @pytest.mark.parametrize("raw", [None, "", "   ", "\n\t"])
    def test_empty_input_is_not_mentioned(self, raw: str | None) -> None:
        """Không ai nêu deadline khác về ngữ nghĩa với nêu nhưng mơ hồ."""
        result = R(raw)
        assert result.date is None
        assert result.rule is ResolutionRule.NOT_MENTIONED

    @pytest.mark.parametrize(
        "raw", ["xyz không phải ngày", "làm cho xong đi", "hỏi anh Tuấn"]
    )
    def test_unrecognised_text_returns_unparseable(self, raw: str) -> None:
        result = R(raw)
        assert result.date is None
        assert result.rule is ResolutionRule.UNPARSEABLE
        assert result.raw == raw


# --------------------------------------------------------------------------- #
# Kiểm tra tính hợp lý
# --------------------------------------------------------------------------- #


class TestSanityGuards:
    @pytest.mark.parametrize(
        "raw",
        ["hôm nay", "ngày mai", "thứ 2", "thứ 3", "cuối tuần này", "trước thứ 6"],
    )
    def test_never_returns_past_date(self, raw: str) -> None:
        result = R(raw)
        assert result.date is None or result.date >= ANCHOR

    def test_yesterday_is_rejected_as_past(self) -> None:
        result = R("hôm qua")
        assert result.date is None
        assert result.rule is ResolutionRule.REJECTED_PAST_DATE
        assert result.note is not None

    def test_past_date_allowed_when_explicitly_enabled(self) -> None:
        """Cờ ``allow_past`` phục vụ việc phân tích cuộc họp trong quá khứ."""
        result = resolve_vietnamese_date("hôm qua", ANCHOR, allow_past=True)
        assert result.date == dt.date(2026, 7, 21)

    def test_absurdly_far_date_is_rejected(self) -> None:
        result = resolve_vietnamese_date(
            "ngày 15/09/2026", ANCHOR, max_horizon_days=7
        )
        assert result.date is None
        assert result.rule is ResolutionRule.REJECTED_IMPLAUSIBLE


# --------------------------------------------------------------------------- #
# Chuẩn hoá văn bản
# --------------------------------------------------------------------------- #


class TestNormalization:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("thứ 3 tuần sau", dt.date(2026, 7, 28)),
            ("thu 3 tuan sau", dt.date(2026, 7, 28)),
            ("THỨ 3 TUẦN SAU", dt.date(2026, 7, 28)),
            ("t3 tuần sau", dt.date(2026, 7, 28)),
            ("Thứ  3   tuần   sau", dt.date(2026, 7, 28)),
        ],
    )
    def test_accent_case_and_spacing_are_tolerated(
        self, raw: str, expected: dt.date
    ) -> None:
        """ASR hay trả về thiếu dấu; cùng một mẫu phải khớp được mọi biến thể."""
        assert R(raw).date == expected

    @pytest.mark.parametrize(
        "raw, expected",
        [("chủ nhật tuần sau", dt.date(2026, 8, 2)), ("CN tuần sau", dt.date(2026, 8, 2))],
    )
    def test_sunday_aliases(self, raw: str, expected: dt.date) -> None:
        assert R(raw).date == expected

    def test_normalize_strips_diacritics_and_lowercases(self) -> None:
        assert normalize_vietnamese("Thứ Ba Tuần Sau") == "thu ba tuan sau"
        assert normalize_vietnamese("  ĐẦU   tháng  ") == "dau thang"

    def test_expressions_embedded_in_sentence(self) -> None:
        """LLM đôi khi trả về cả cụm thay vì chỉ mốc thời gian."""
        assert R("làm xong trước thứ 6 nhé").date == dt.date(2026, 7, 24)
        assert R("nộp vào cuối tuần này").date == dt.date(2026, 7, 26)


# --------------------------------------------------------------------------- #
# Tính tất định trên mọi ngày neo
# --------------------------------------------------------------------------- #


class TestDeterminismAcrossAnchors:
    @pytest.mark.parametrize("anchor_day", range(20, 27))
    def test_cuoi_tuan_nay_always_lands_on_sunday(self, anchor_day: int) -> None:
        """Bất kể họp ngày nào trong tuần, "cuối tuần này" luôn là Chủ nhật tuần đó."""
        anchor = dt.date(2026, 7, anchor_day)
        result = R("cuối tuần này", anchor)
        assert result.date is not None
        assert result.date.weekday() == 6
        assert 0 <= (result.date - anchor).days < 7

    @pytest.mark.parametrize("anchor_day", range(20, 27))
    def test_next_week_tuesday_always_falls_in_the_following_week(
        self, anchor_day: int
    ) -> None:
        """Kết quả luôn là Thứ Ba của tuần lịch KẾ TIẾP tuần chứa ngày họp.

        Lưu ý khoảng cách theo ngày KHÔNG cố định: họp Chủ nhật 26/07 thì
        "thứ 3 tuần sau" chỉ cách 2 ngày, còn họp Thứ Hai 20/07 thì cách 8
        ngày. Bất biến đúng là quan hệ tuần lịch, không phải số ngày.
        """
        anchor = dt.date(2026, 7, anchor_day)
        result = R("thứ 3 tuần sau", anchor)
        assert result.date is not None
        assert result.date.weekday() == 1

        next_week_monday = anchor - dt.timedelta(days=anchor.weekday()) + dt.timedelta(days=7)
        assert next_week_monday <= result.date < next_week_monday + dt.timedelta(days=7)
        assert result.date > anchor

    @pytest.mark.parametrize("anchor_day", range(20, 27))
    def test_smart_weekday_never_lands_in_the_past(self, anchor_day: int) -> None:
        anchor = dt.date(2026, 7, anchor_day)
        for raw in ["trước thứ 2", "trước thứ 5", "trước Chủ nhật"]:
            result = R(raw, anchor)
            assert result.date is None or result.date > anchor

    def test_resolution_is_idempotent(self) -> None:
        """Cùng đầu vào phải luôn cho cùng đầu ra — pipeline phải tái lập được."""
        for _ in range(5):
            assert R("thứ 3 tuần sau").date == dt.date(2026, 7, 28)


# --------------------------------------------------------------------------- #
# Hàm tính ngày ở mức đơn vị
# --------------------------------------------------------------------------- #


class TestWeekdayHelpers:
    def test_this_week_weekday_uses_monday_as_week_start(self) -> None:
        assert this_week_weekday(0, ANCHOR) == dt.date(2026, 7, 20)
        assert this_week_weekday(6, ANCHOR) == dt.date(2026, 7, 26)

    def test_next_week_weekday_is_exactly_seven_days_later(self) -> None:
        for weekday in range(7):
            delta = next_week_weekday(weekday, ANCHOR) - this_week_weekday(
                weekday, ANCHOR
            )
            assert delta.days == 7

    def test_smart_rolls_forward_only_when_needed(self) -> None:
        assert this_week_weekday_smart(4, ANCHOR) == dt.date(2026, 7, 24)
        assert this_week_weekday_smart(0, ANCHOR) == dt.date(2026, 7, 27)
        assert this_week_weekday_smart(2, ANCHOR) == dt.date(2026, 7, 29)


# --------------------------------------------------------------------------- #
# Hợp đồng của kiểu trả về
# --------------------------------------------------------------------------- #


class TestDateResolutionContract:
    def test_confidence_is_present_only_when_resolved(self) -> None:
        assert R("thứ 3 tuần sau").confidence is Confidence.HIGH
        assert R("tuần sau").confidence is None
        assert R(None).confidence is None

    def test_rule_display_includes_weekday_detail(self) -> None:
        assert R("thứ 3 tuần sau").rule_display == "NEXT_WEEK_WEEKDAY(tuesday)"
        assert R("cuối tuần này").rule_display == "THIS_WEEK_WEEKDAY(sunday)"
        assert R("cuối tháng").rule_display == "LAST_DAY_OF_MONTH"

    def test_is_resolved_flag(self) -> None:
        assert R("ngày mai").is_resolved is True
        assert R("tuần sau").is_resolved is False

    def test_raw_input_is_preserved_for_audit(self) -> None:
        """``due_raw`` phải giữ nguyên văn để người dùng đối chiếu được."""
        assert R("Cuối Tuần Này").raw == "Cuối Tuần Này"

    def test_to_dict_is_json_serialisable(self) -> None:
        import json

        payload = R("thứ 3 tuần sau").to_dict()
        assert json.loads(json.dumps(payload))["date"] == "2026-07-28"
        assert payload["confidence"] == "high"

    def test_result_is_immutable(self) -> None:
        import dataclasses

        result = R("ngày mai")
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.date = dt.date(2030, 1, 1)  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# Các mốc lấy từ transcript mẫu trong bản thiết kế
# --------------------------------------------------------------------------- #


class TestGoldenMeetingExpressions:
    """Toàn bộ biểu thức thời gian xuất hiện trong cuộc họp mẫu Sprint 23."""

    @pytest.mark.parametrize(
        "raw, expected, source_segment",
        [
            ("cuối tuần này", dt.date(2026, 7, 26), "s_0012"),
            ("trước thứ 6", dt.date(2026, 7, 24), "s_0013"),
            ("thứ 3 tuần sau", dt.date(2026, 7, 28), "s_0017"),
            ("trước Chủ nhật", dt.date(2026, 7, 26), "s_0019"),
        ],
    )
    def test_resolvable_expressions(
        self, raw: str, expected: dt.date, source_segment: str
    ) -> None:
        result = R(raw)
        assert result.date == expected, f"Sai ở {source_segment}: {raw!r}"

    @pytest.mark.parametrize(
        "raw, source_segment", [("đầu tháng 8", "s_0012"), ("tuần sau", "s_0020")]
    )
    def test_vague_expressions_stay_null(self, raw: str, source_segment: str) -> None:
        assert R(raw).date is None, f"Đã bịa ngày cho {source_segment}: {raw!r}"
