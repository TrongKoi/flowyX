"""Test tích hợp — từ một file có thật ngoài đời tới biên bản hoàn chỉnh.

Vì sao test này tồn tại
-----------------------
``test_pipeline_e2e.py`` bắt đầu từ ``sample_transcript.json``, một file
chúng ta tự soạn đúng chuẩn nội bộ. Nó chứng minh pipeline đúng, nhưng
không chứng minh được rằng có **đường vào** nào từ thế giới thật.

Test này khoá lại đường đó: một file WebVTT y hệt thứ Zoom xuất ra, đi qua
đủ sáu pha, phải cho ra cùng một biên bản với cùng điểm grounding. Nếu ai đó
sửa parser làm lệch một mốc thời gian hay đổi thứ tự nhãn speaker, test này
đỏ trước khi người dùng phát hiện.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from core.cache import LLMCache
from pipeline.s0_ingest import IngestPolicy, run_ingest
from pipeline.s2_diarize import run_diarize
from pipeline.s3_chunk import ChunkingPolicy, run_chunk
from pipeline.s4_extract import run_extract
from pipeline.s5_reconcile import run_reconcile
from pipeline.s6_compose import run_compose
from pipeline.s7_validate import run_validate
from providers.base import LLMRunner
from providers.llm.mock import MockLLMProvider
from schemas.common import MeetingType
from schemas.minutes import StructuredMinutes
from schemas.reconciled import MeetingAnchor
from schemas.transcript import TranscriptMeta

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
VTT_FILE = FIXTURES / "ingest" / "zoom_sprint23.vtt"
MEETING_DATE = dt.date(2026, 7, 22)  # Thứ Tư


@pytest.fixture(scope="module")
def minutes(tmp_path_factory: pytest.TempPathFactory) -> StructuredMinutes:
    """Chạy trọn pipeline từ file VTT, không đi vòng qua JSON nội bộ."""
    meta = TranscriptMeta(
        title="Sprint 23 Review & Chốt release v2.4",
        meeting_date=MEETING_DATE,
        meeting_type=MeetingType.PLANNING,
        duration_ms=0,
    )
    outcome = run_ingest(
        VTT_FILE,
        meta=meta,
        meeting_id="mtg_20260722_sprint24",
        policy=IngestPolicy(merge_gap_ms=0),
    )

    transcript = run_diarize(outcome.transcript).transcript
    chunking = run_chunk(transcript, ChunkingPolicy.from_quota(None))
    transcript = transcript.model_copy(update={"chunks": chunking.chunks})

    anchor = MeetingAnchor(meeting_date=transcript.meta.meeting_date)
    cache = LLMCache(tmp_path_factory.mktemp("cache") / "test.db")
    runner = LLMRunner(
        [MockLLMProvider(FIXTURES / "mock_llm")], cache=cache, quota=None
    )

    extraction = run_extract(transcript, anchor, runner)
    facts = run_reconcile(extraction.extractions, transcript, anchor, runner)
    draft = run_compose(facts, transcript, runner)
    validated = run_validate(draft, transcript)

    cache.close()
    return validated.minutes


def test_grounding_hoan_hao_tu_file_vtt(minutes: StructuredMinutes) -> None:
    """Bằng chứng phải trỏ về đúng segment do parser dựng ra."""
    assert minutes.validation is not None
    assert minutes.validation.grounding_score == pytest.approx(1.0)


def test_moi_lop_kiem_chung_deu_qua(minutes: StructuredMinutes) -> None:
    assert minutes.validation is not None
    failed = [
        name for name, check in minutes.validation.checks.items() if not check.passed
    ]
    assert failed == []


def test_supersession_van_dung_qua_duong_vtt(minutes: StructuredMinutes) -> None:
    """Cạm bẫy T1 — chỉ còn một quyết định release hiệu lực."""
    active = [d for d in minutes.active_decisions if "release" in d.statement.lower()]
    assert len(active) == 1
    assert active[0].target_date == dt.date(2026, 7, 28)


def test_ten_nguoi_noi_lay_tu_file_vtt(minutes: StructuredMinutes) -> None:
    """Zoom đã ghi sẵn tên — không cần đoán qua xưng hô, không cần audio."""
    assignees = {a.assignee for a in minutes.action_items if a.assignee}
    assert assignees <= {"Hùng", "Tuấn", "Lan", "Minh"}
    assert {"Tuấn", "Lan", "Minh"} <= assignees


def test_khong_ton_them_request_nao_cho_pha_ingest(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Pha INGEST phải là 100% Python — 0 quota, chạy vô hạn lần."""
    meta = TranscriptMeta(
        title="Sprint 23",
        meeting_date=MEETING_DATE,
        meeting_type=MeetingType.PLANNING,
        duration_ms=0,
    )
    provider = MockLLMProvider(FIXTURES / "mock_llm")
    run_ingest(VTT_FILE, meta=meta, meeting_id="mtg_test", policy=IngestPolicy())
    assert provider.calls == []
