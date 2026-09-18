"""Kiểm thử end-to-end pipeline trên cuộc họp mẫu, dùng LLM giả lập.

Vì phản hồi LLM được cố định bằng fixture, mọi test ở đây **tất định** và
**không tốn quota** — chạy được hàng trăm lần trong CI.

Điều đó không làm giảm giá trị của chúng: phần lớn logic dễ sai của hệ thống
nằm ở Python chứ không ở LLM. Hoà giải thời gian, quy tắc ưu tiên khi đổi ý,
quy đổi ngày tiếng Việt, khớp tên, tám lớp kiểm chứng — tất cả đều được kiểm
thử thật ở đây.

Mỗi cạm bẫy là một test RIÊNG chứ không gộp vào một test lớn. Khi sửa prompt
và thấy 3/12 test đỏ, bạn biết ngay hỏng ở đâu; một test lớn chỉ nói "sai".
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from core.cache import LLMCache
from pipeline.s4_extract import run_extract
from pipeline.s5_reconcile import run_reconcile
from pipeline.s6_compose import run_compose
from pipeline.s7_validate import run_validate
from providers.base import LLMRunner
from providers.llm.mock import MockLLMProvider
from schemas.common import CommitmentStrength, Confidence, DecisionStatus, WarningCode
from schemas.minutes import StructuredMinutes
from schemas.reconciled import MeetingAnchor
from schemas.transcript import Transcript

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
MEETING_DATE = dt.date(2026, 7, 22)  # Thứ Tư


@pytest.fixture(scope="module")
def transcript() -> Transcript:
    return Transcript.model_validate_json(
        (FIXTURES / "sample_transcript.json").read_text(encoding="utf-8")
    )


@pytest.fixture(scope="module")
def minutes(transcript: Transcript, tmp_path_factory: pytest.TempPathFactory) -> StructuredMinutes:
    """Chạy trọn pipeline MỘT lần, dùng chung cho mọi test trong module."""
    anchor = MeetingAnchor(meeting_date=transcript.meta.meeting_date)
    cache = LLMCache(tmp_path_factory.mktemp("cache") / "test.db")
    runner = LLMRunner(
        [MockLLMProvider(FIXTURES / "mock_llm")], cache=cache, quota=None
    )

    extraction = run_extract(transcript, anchor, runner)
    facts = run_reconcile(extraction.extractions, transcript, anchor, runner)
    draft = run_compose(facts, transcript, runner)
    outcome = run_validate(draft, transcript)

    cache.close()
    return outcome.minutes


def _action(minutes: StructuredMinutes, keyword: str):
    """Tìm công việc theo từ khoá, đòi hỏi khớp DUY NHẤT.

    Yêu cầu duy nhất là có chủ ý: từ khoá "social" xuất hiện trong cả công
    việc fix staging lẫn công việc kiểm thử, nên một helper lấy phần tử đầu
    tiên sẽ âm thầm test nhầm đối tượng.
    """
    matches = [a for a in minutes.action_items if keyword.lower() in a.task.lower()]
    assert len(matches) == 1, (
        f"Từ khoá {keyword!r} khớp {len(matches)} công việc, cần đúng 1: "
        + str([a.task for a in matches])
    )
    return matches[0]


# --------------------------------------------------------------------------- #
# T1 & T8 — Đảo ngược quyết định và hệ quả lan truyền
# --------------------------------------------------------------------------- #


class TestSupersession:
    def test_t1_exactly_one_active_release_decision(self, minutes: StructuredMinutes) -> None:
        """Map-Reduce ngây thơ sẽ để CẢ HAI ngày release cùng có hiệu lực."""
        release = [d for d in minutes.decisions if "release" in d.statement.lower()]
        active = [d for d in release if d.status is DecisionStatus.DECIDED]
        assert len(active) == 1, (
            f"Có {len(active)} quyết định release cùng hiệu lực — "
            "quy tắc ưu tiên thời gian đã thất bại"
        )

    def test_t6_active_decision_carries_resolved_date(self, minutes: StructuredMinutes) -> None:
        """"thứ 3 tuần sau" tính từ Thứ Tư 22/07 là 28/07."""
        active = minutes.active_decisions[0]
        assert active.target_date == dt.date(2026, 7, 28)

    def test_superseded_decision_kept_as_history(self, minutes: StructuredMinutes) -> None:
        """Quyết định bị đảo KHÔNG bị xoá — lịch sử là dữ liệu có giá trị."""
        rejected = minutes.superseded_decisions
        assert len(rejected) == 1
        assert rejected[0].target_date == dt.date(2026, 7, 26)
        assert rejected[0].display_hint == "history_only"

    def test_supersession_relationship_is_bidirectional(self, minutes: StructuredMinutes) -> None:
        by_id = {d.id: d for d in minutes.decisions}
        for decision in minutes.decisions:
            if decision.supersedes:
                target = by_id[decision.supersedes]
                assert target.superseded_by == decision.id
                assert target.status is DecisionStatus.REJECTED
                assert (target.timestamp_ms or 0) < (decision.timestamp_ms or 0)

    def test_t8_superseded_dependency_is_flagged(self, minutes: StructuredMinutes) -> None:
        """Cam kết đưa ra khi quyết định cũ còn hiệu lực phải được cảnh báo.

        Đây là lỗi tinh vi nhất: hệ thống im lặng xuất ra deadline 24/07 dựa
        trên lịch release 26/07 vốn đã bị lùi sang 28/07.
        """
        assert minutes.quality_report.has(WarningCode.SUPERSEDED_DEPENDENCY)
        store = _action(minutes, "store")
        assert store.needs_review is True
        assert store.related_decision_id is not None


# --------------------------------------------------------------------------- #
# T2, T3, T4 — Cam kết và người nhận việc
# --------------------------------------------------------------------------- #


class TestCommitments:
    def test_t2_hedged_commitment_is_tentative(self, minutes: StructuredMinutes) -> None:
        """"Để anh xem lại rồi báo em sau" KHÔNG phải cam kết chắc chắn."""
        query = _action(minutes, "query")
        assert query.commitment_strength is CommitmentStrength.TENTATIVE
        assert query.due_date is None, "Đã bịa deadline cho một cam kết mơ hồ"
        assert query.assignee == "Tuấn"

    def test_t3_explicit_commitment_is_firm(self, minutes: StructuredMinutes) -> None:
        """"Em nhận phần submit store, xong trước thứ 6" là cam kết rõ ràng."""
        store = _action(minutes, "store")
        assert store.commitment_strength is CommitmentStrength.FIRM
        assert store.due_date == dt.date(2026, 7, 24)
        assert store.assignee == "Minh", "Không tách được tên trong 'em (Minh)'"

    def test_t4_unassigned_task_stays_unassigned(self, minutes: StructuredMinutes) -> None:
        """"Cái đó phải fix gấp" — không ai nhận. Không được đoán người hợp lý nhất."""
        staging = _action(minutes, "staging")
        assert staging.assignee is None
        assert staging.assignee_person_id is None
        assert staging.needs_review is True
        assert minutes.quality_report.has(WarningCode.AMBIGUOUS_ASSIGNEE)

    def test_no_hallucinated_assignees(self, minutes: StructuredMinutes) -> None:
        known = {a.display_name for a in minutes.meta.attendees}
        for action in minutes.action_items:
            if action.assignee is not None:
                assert action.assignee in known


# --------------------------------------------------------------------------- #
# T5, T6, T7 — Quy đổi thời gian
# --------------------------------------------------------------------------- #


class TestDateResolution:
    def test_t5_this_weekend_resolves_to_sunday(self, minutes: StructuredMinutes) -> None:
        social = _action(minutes, "đăng nhập bằng social")
        assert social.due_date == dt.date(2026, 7, 26)

    def test_t7_vague_expressions_stay_null(self, minutes: StructuredMinutes) -> None:
        """"tuần sau" là một TUẦN, không phải một NGÀY."""
        assert minutes.next_meeting is not None
        assert minutes.next_meeting.when_date is None
        assert minutes.next_meeting.when_raw is not None

    def test_every_due_date_has_a_source(self, minutes: StructuredMinutes) -> None:
        """Có due_date mà không có due_raw nghĩa là ngày đó bị bịa."""
        for action in minutes.action_items:
            if action.due_date is not None:
                assert action.due_raw, f"{action.id}: due_date không có nguồn"

    def test_no_due_date_before_meeting(self, minutes: StructuredMinutes) -> None:
        for action in minutes.action_items:
            if action.due_date is not None:
                assert action.due_date >= MEETING_DATE


# --------------------------------------------------------------------------- #
# T9, T10, T11, T12 — Speaker, nhiễu, code-switching, con số
# --------------------------------------------------------------------------- #


class TestTranscriptHandling:
    def test_t9_speakers_are_named(self, minutes: StructuredMinutes) -> None:
        assert len(minutes.meta.attendees) == 4
        for attendee in minutes.meta.attendees:
            assert attendee.display_name != attendee.speaker_label
        assert {a.display_name for a in minutes.meta.attendees} == {
            "Hùng", "Tuấn", "Lan", "Minh"
        }

    def test_t10_noisy_segment_is_flagged(self, minutes: StructuredMinutes) -> None:
        assert minutes.quality_report.has(WarningCode.TRANSCRIPT_GAPS)

    def test_t11_english_terms_are_not_translated(self, minutes: StructuredMinutes) -> None:
        """Người Việt gọi là "staging", không phải "môi trường thử nghiệm"."""
        blob = " ".join(
            [
                *minutes.executive_summary.tldr,
                *minutes.executive_summary.paragraphs,
                *[a.task for a in minutes.action_items],
            ]
        ).lower()
        for term in ("staging", "release", "query"):
            assert term in blob, f"Thuật ngữ {term!r} đã bị dịch mất"

    def test_t12_decimal_numbers_preserved_exactly(self, minutes: StructuredMinutes) -> None:
        """2.3% không được làm tròn thành 2%."""
        values = {m.value_raw for m in minutes.metrics}
        assert any("2.3" in v for v in values)
        assert any("4.1" in v for v in values)


# --------------------------------------------------------------------------- #
# Kiểm chứng grounding và ngân sách quota
# --------------------------------------------------------------------------- #


class TestValidation:
    def test_all_eight_checks_pass(self, minutes: StructuredMinutes) -> None:
        assert minutes.validation is not None
        failed = [n for n, c in minutes.validation.checks.items() if not c.passed]
        assert not failed, f"Các lớp kiểm chứng thất bại: {failed}"

    def test_grounding_score_is_perfect_on_clean_input(self, minutes: StructuredMinutes) -> None:
        assert minutes.validation is not None
        assert minutes.validation.grounding_score >= 0.95

    def test_every_item_has_real_evidence(self, minutes: StructuredMinutes) -> None:
        valid = {s.id for s in _load_transcript().segments}
        for item in minutes.iter_grounded_items():
            assert item.evidence_segment_ids
            for evidence_id in item.evidence_segment_ids:
                assert evidence_id in valid

    def test_needs_human_review_when_warnings_exist(self, minutes: StructuredMinutes) -> None:
        assert minutes.quality_report.warnings
        assert minutes.quality_report.needs_human_review is True

    def test_pipeline_stays_within_request_budget(
        self, transcript: Transcript, tmp_path: Path
    ) -> None:
        """Cuộc họp 2 chunk phải xong trong tối đa 4 request LLM.

        Ngân sách này là ràng buộc thiết kế của bản 0 đồng: 2 lời gọi EXTRACT
        + 1 gom nhóm + 1 COMPOSE. Pha VALIDATE tốn 0 request vì chạy hoàn
        toàn bằng Python.
        """
        anchor = MeetingAnchor(meeting_date=transcript.meta.meeting_date)
        cache = LLMCache(tmp_path / "budget.db", enabled=False)
        runner = LLMRunner(
            [MockLLMProvider(FIXTURES / "mock_llm")], cache=cache, quota=None
        )

        extraction = run_extract(transcript, anchor, runner)
        facts = run_reconcile(extraction.extractions, transcript, anchor, runner)
        draft = run_compose(facts, transcript, runner)
        run_validate(draft, transcript)
        cache.close()

        assert runner.request_count <= 4, (
            f"Dùng {runner.request_count} request cho một cuộc họp 2 chunk"
        )


def _load_transcript() -> Transcript:
    return Transcript.model_validate_json(
        (FIXTURES / "sample_transcript.json").read_text(encoding="utf-8")
    )


# --------------------------------------------------------------------------- #
# Suy giảm có kiểm soát
# --------------------------------------------------------------------------- #


class TestGracefulDegradation:
    def test_phantom_evidence_ids_are_dropped(
        self, transcript: Transcript, tmp_path: Path
    ) -> None:
        """LLM bịa segment ID thì mục đó bị loại, không làm hỏng cả chunk."""
        from schemas.extraction import ChunkExtraction, RawActionItem

        extraction = ChunkExtraction(
            chunk_id="c_01",
            action_items=[
                RawActionItem(
                    task="Việc có thật",
                    evidence_segment_ids=["s_0003", "s_9999"],
                ),
                RawActionItem(
                    task="Việc bịa hoàn toàn",
                    evidence_segment_ids=["s_8888"],
                ),
            ],
        )
        from pipeline.s4_extract import ExtractionResult, _sanitise_evidence

        result = ExtractionResult()
        _sanitise_evidence(extraction, {s.id for s in transcript.segments}, result)

        assert len(extraction.action_items) == 1
        assert extraction.action_items[0].task == "Việc có thật"
        assert extraction.action_items[0].evidence_segment_ids == ["s_0003"]
        assert len(result.dropped_items) == 1

    def test_compose_failure_falls_back_to_template(
        self, transcript: Transcript, tmp_path: Path
    ) -> None:
        """LLM hỏng ở pha COMPOSE vẫn phải giao được biên bản đúng dữ kiện.

        Thà giao bản mộc mạc còn hơn màn hình trắng sau khi đã tiêu quota cho
        các pha trước.
        """
        anchor = MeetingAnchor(meeting_date=transcript.meta.meeting_date)
        cache = LLMCache(tmp_path / "degraded.db", enabled=False)
        working = LLMRunner(
            [MockLLMProvider(FIXTURES / "mock_llm")], cache=cache, quota=None
        )

        extraction = run_extract(transcript, anchor, working)
        facts = run_reconcile(extraction.extractions, transcript, anchor, working)

        broken = LLMRunner(
            [MockLLMProvider(tmp_path / "khong-ton-tai")], cache=cache, quota=None
        )
        draft = run_compose(facts, transcript, broken)
        cache.close()

        assert draft.executive_summary.tldr
        assert len(draft.action_items) == len(facts.action_items)
        assert len(draft.decisions) == len(facts.decisions)


# --------------------------------------------------------------------------- #
# Bất biến của kiến trúc
# --------------------------------------------------------------------------- #


def test_compose_prompt_never_contains_transcript(transcript: Transcript) -> None:
    """Bất biến chống hallucination quan trọng nhất của toàn hệ thống.

    Pha COMPOSE chỉ được nhìn thấy dữ kiện đã hoà giải. Nếu transcript thô lọt
    vào prompt này, model lại có nguyên liệu để suy diễn và toàn bộ lợi ích
    của việc tách Extract khỏi Compose bị vô hiệu.
    """
    from pipeline.s6_compose import build_compose_prompt

    anchor = MeetingAnchor(meeting_date=transcript.meta.meeting_date)
    cache = LLMCache(":memory:", enabled=False)
    runner = LLMRunner(
        [MockLLMProvider(FIXTURES / "mock_llm")], cache=cache, quota=None
    )
    extraction = run_extract(transcript, anchor, runner)
    facts = run_reconcile(extraction.extractions, transcript, anchor, runner)
    prompt = build_compose_prompt(facts, transcript)
    cache.close()

    verbatim = [
        "Ok mọi người mình bắt đầu nhé",
        "Anh Tuấn cập nhật giúp em phần backend",
        "8 giây thì không acceptable rồi",
    ]
    for line in verbatim:
        assert line not in prompt, f"Transcript thô đã lọt vào prompt COMPOSE: {line!r}"

    for segment in transcript.segments:
        assert segment.id not in prompt
