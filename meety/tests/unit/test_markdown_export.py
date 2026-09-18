"""Kiểm thử kết xuất biên bản Markdown.

Trọng tâm không phải "có đẹp không" mà là **không mất thông tin và không bịa
thêm thông tin**: mọi quyết định, công việc, cảnh báo phải xuất hiện đúng như
trong ``StructuredMinutes``, và chỗ thiếu dữ liệu phải được ghi rõ là thiếu
thay vì để trống.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from exporters.markdown import render_markdown, write_markdown
from schemas.minutes import StructuredMinutes

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture(scope="module")
def minutes() -> StructuredMinutes:
    """Biên bản mẫu dựng từ chính pipeline, không phải dữ liệu viết tay."""
    from core.cache import LLMCache
    from pipeline.s4_extract import run_extract
    from pipeline.s5_reconcile import run_reconcile
    from pipeline.s6_compose import run_compose
    from pipeline.s7_validate import run_validate
    from providers.base import LLMRunner
    from providers.llm.mock import MockLLMProvider
    from schemas.reconciled import MeetingAnchor
    from schemas.transcript import Transcript

    transcript = Transcript.model_validate_json(
        (FIXTURES / "sample_transcript.json").read_text(encoding="utf-8")
    )
    anchor = MeetingAnchor(meeting_date=transcript.meta.meeting_date)
    cache = LLMCache(":memory:", enabled=False)
    runner = LLMRunner(
        [MockLLMProvider(FIXTURES / "mock_llm")], cache=cache, quota=None
    )

    extraction = run_extract(transcript, anchor, runner)
    facts = run_reconcile(extraction.extractions, transcript, anchor, runner)
    draft = run_compose(facts, transcript, runner)
    outcome = run_validate(draft, transcript)
    cache.close()
    return outcome.minutes


@pytest.fixture(scope="module")
def document(minutes: StructuredMinutes) -> str:
    return render_markdown(minutes)


# --------------------------------------------------------------------------- #
# Cấu trúc
# --------------------------------------------------------------------------- #


class TestStructure:
    def test_has_title_and_meeting_name(
        self, document: str, minutes: StructuredMinutes
    ) -> None:
        assert document.startswith("# BIÊN BẢN CUỘC HỌP")
        assert minutes.meta.meeting_title in document

    @pytest.mark.parametrize(
        "heading",
        [
            "## 1. Thành phần tham dự",
            "## 2. Tóm tắt nhanh",
            "## 3. Các quyết định",
            "## 4. Công việc được giao",
            "## 5. Số liệu được nêu",
            "## 6. Rủi ro và vướng mắc",
        ],
    )
    def test_contains_expected_sections(self, document: str, heading: str) -> None:
        assert heading in document

    def test_ends_with_newline(self, document: str) -> None:
        assert document.endswith("\n")

    def test_tables_are_well_formed(self, document: str) -> None:
        """Mỗi bảng phải có dòng phân cách ngay sau dòng tiêu đề."""
        lines = document.splitlines()
        for index, line in enumerate(lines[:-1]):
            if line.startswith("| ") and not line.startswith("|---"):
                following = lines[index + 1]
                if following.startswith("|---"):
                    assert line.count("|") == following.count("|")


# --------------------------------------------------------------------------- #
# Không mất thông tin
# --------------------------------------------------------------------------- #


class TestCompleteness:
    def test_every_action_item_appears(
        self, document: str, minutes: StructuredMinutes
    ) -> None:
        for action in minutes.action_items:
            assert action.id in document, f"Thiếu công việc {action.id}"

    def test_every_active_decision_appears(
        self, document: str, minutes: StructuredMinutes
    ) -> None:
        for decision in minutes.active_decisions:
            assert decision.statement[:40] in document

    def test_superseded_decision_is_kept_as_history(
        self, document: str, minutes: StructuredMinutes
    ) -> None:
        """Người đọc cần biết lịch sử đổi ý, không chỉ kết quả cuối."""
        assert "đã được thay đổi trong cuộc họp" in document
        for decision in minutes.superseded_decisions:
            assert decision.statement[:40] in document

    def test_every_attendee_appears(
        self, document: str, minutes: StructuredMinutes
    ) -> None:
        for attendee in minutes.meta.attendees:
            assert attendee.display_name in document

    def test_all_warnings_appear(
        self, document: str, minutes: StructuredMinutes
    ) -> None:
        for warning in minutes.quality_report.warnings:
            assert warning.code.value in document

    def test_metric_values_are_verbatim(
        self, document: str, minutes: StructuredMinutes
    ) -> None:
        """Con số phải giữ nguyên văn, không làm tròn cho đẹp."""
        for metric in minutes.metrics:
            assert metric.value_raw in document


# --------------------------------------------------------------------------- #
# Xử lý chỗ thiếu thông tin
# --------------------------------------------------------------------------- #


class TestMissingInformation:
    def test_unassigned_task_is_marked_explicitly(
        self, document: str, minutes: StructuredMinutes
    ) -> None:
        """Ô trống khiến người đọc tưởng là sót định dạng."""
        if minutes.unassigned_actions:
            assert "Chưa phân công" in document

    def test_missing_deadline_is_marked_explicitly(
        self, document: str, minutes: StructuredMinutes
    ) -> None:
        if any(a.due_date is None for a in minutes.action_items):
            assert "Chưa xác định" in document

    def test_flags_items_needing_review(
        self, document: str, minutes: StructuredMinutes
    ) -> None:
        if any(a.needs_review for a in minutes.action_items):
            assert "cần rà soát lại" in document

    def test_warns_that_document_is_machine_generated(self, document: str) -> None:
        assert "tự động" in document


# --------------------------------------------------------------------------- #
# Tuỳ chọn hiển thị
# --------------------------------------------------------------------------- #


class TestOptions:
    def test_can_hide_history(self, minutes: StructuredMinutes) -> None:
        output = render_markdown(minutes, include_history=False)
        assert "đã được thay đổi trong cuộc họp" not in output

    def test_can_hide_quality_section(self, minutes: StructuredMinutes) -> None:
        output = render_markdown(minutes, include_quality=False)
        assert "Ghi chú về độ tin cậy" not in output

    def test_can_hide_evidence_ids(self, minutes: StructuredMinutes) -> None:
        """Tắt dẫn chứng khi gửi biên bản ra ngoài tổ chức."""
        output = render_markdown(minutes, include_evidence=False)
        assert "Dẫn chứng" not in output

    def test_evidence_shown_by_default(self, document: str) -> None:
        assert "Dẫn chứng" in document


# --------------------------------------------------------------------------- #
# Ghi file
# --------------------------------------------------------------------------- #


class TestWriteFile:
    def test_writes_utf8_file(
        self, minutes: StructuredMinutes, tmp_path: Path
    ) -> None:
        """Mã trang mặc định trên Windows không biểu diễn được tiếng Việt."""
        destination = write_markdown(minutes, tmp_path / "sub" / "bien_ban.md")
        assert destination.exists()
        content = destination.read_text(encoding="utf-8")
        assert "BIÊN BẢN CUỘC HỌP" in content
        assert "Tuấn" in content

    def test_creates_parent_directories(
        self, minutes: StructuredMinutes, tmp_path: Path
    ) -> None:
        destination = write_markdown(minutes, tmp_path / "a" / "b" / "c.md")
        assert destination.parent.is_dir()


# --------------------------------------------------------------------------- #
# An toàn định dạng
# --------------------------------------------------------------------------- #


def test_pipe_characters_are_escaped(minutes: StructuredMinutes) -> None:
    """Dấu gạch đứng trong nội dung sẽ phá vỡ bảng Markdown nếu không thoát."""
    tampered = minutes.model_copy(deep=True)
    tampered.action_items[0].task = "Sửa lỗi A | B | C"
    output = render_markdown(tampered)

    table_lines = [
        line for line in output.splitlines()
        if line.startswith("| `a_") and "Sửa lỗi" in line
    ]
    assert table_lines
    assert "\\|" in table_lines[0]


def test_render_is_deterministic(minutes: StructuredMinutes) -> None:
    assert render_markdown(minutes) == render_markdown(minutes)


def test_render_does_not_mutate_input(minutes: StructuredMinutes) -> None:
    before = json.loads(minutes.model_dump_json())
    render_markdown(minutes)
    assert json.loads(minutes.model_dump_json()) == before
