"""Pha 4 — COMPOSE: sinh văn xuôi TỪ dữ kiện đã hoà giải.

Đây là điểm mấu chốt chống hallucination của toàn hệ thống, và nó được cưỡng
chế bằng **kiến trúc** chứ không bằng lời dặn trong prompt:

* Đầu vào của pha này chỉ là ``ReconciledFacts.fact_digest()`` — JSON đã qua
  kiểm chứng. Transcript thô **không** được đưa vào.
* Đầu ra của LLM bị giới hạn ở ``ComposedProse``: chỉ có ``tldr``,
  ``paragraphs`` và ``chapters``. Không có trường nào để ghi một action item,
  một deadline, hay một quyết định mới.
* ``StructuredMinutes`` được lắp ráp bằng Python: tầng sự kiện **sao chép
  nguyên vẹn** từ ``ReconciledFacts``, phần văn xuôi lấy từ LLM.

Kết quả là model không thể bịa sự kiện mới vì nó không có nguyên liệu để bịa
và cũng không có chỗ để ghi. Nhiệm vụ của nó thu hẹp từ "hiểu rồi viết"
xuống chỉ còn "viết" — dễ hơn nhiều bậc và tỉ lệ lỗi thấp hơn hẳn.
"""

from __future__ import annotations

import datetime as dt
import logging

from providers.base import LLMRunner
from schemas.common import Confidence, ConsensusLevel, MeetingType
from schemas.minutes import (
    Attendee,
    Chapter,
    ExecutiveSummary,
    MinutesMeta,
    PipelineInfo,
    QualityReport,
    StructuredMinutes,
)
from schemas.reconciled import ComposedProse, ReconciledFacts
from schemas.transcript import Transcript

logger = logging.getLogger(__name__)

__all__ = ["PROMPT_VERSION", "run_compose", "build_compose_prompt"]

PROMPT_VERSION = "compose.vi.v1.0"

SYSTEM_PROMPT = """\
Bạn là thư ký cuộc họp chuyên nghiệp. Bạn nhận một tập DỮ KIỆN ĐÃ ĐƯỢC XÁC
MINH và viết thành phần văn xuôi của biên bản cuộc họp tiếng Việt.

RÀNG BUỘC TUYỆT ĐỐI:
Bạn CHỈ được dùng thông tin có trong dữ kiện đầu vào. Bạn KHÔNG có quyền
truy cập transcript gốc. Nếu một chi tiết không có trong đầu vào thì nó
KHÔNG TỒN TẠI — không được thêm vào để câu văn tròn trịa hơn.

Không thêm câu chuyển tiếp mang tính suy diễn ("sau khi thảo luận sôi nổi",
"các thành viên đều đồng tình", "không khí cuộc họp tích cực"). Chỉ diễn đạt
lại dữ kiện.

VĂN PHONG:
- Tiếng Việt trang trọng, khách quan, ngôi thứ ba, thể trần thuật.
- Câu ngắn, rõ, không hoa mỹ. Đây là văn bản để tra cứu, không phải để đọc chơi.
- GIỮ NGUYÊN thuật ngữ tiếng Anh phổ biến trong ngành (deploy, staging,
  release, sprint, backlog, timeout...). KHÔNG dịch cưỡng ép.
- Không dùng ngôi thứ nhất, không dùng câu cảm thán.

CẤU TRÚC:
- tldr: 3-5 gạch đầu dòng, mỗi dòng tối đa 25 từ và phải ĐỨNG ĐỘC LẬP —
  người chỉ đọc phần này vẫn nắm được mọi điều quan trọng.
- paragraphs: 1-2 đoạn, mỗi đoạn 3-5 câu.
- chapters: chia cuộc họp theo chủ đề, mỗi chương 2-4 câu tóm tắt.
  consensus_level phản ánh mức đồng thuận: "aligned" khi không có phản đối,
  "debated" khi có objections được ghi nhận, "unresolved" khi vấn đề bị hoãn.

XỬ LÝ THIẾU THÔNG TIN:
- Không rõ người phụ trách -> viết "chưa phân công".
- Không có deadline -> viết "chưa xác định".
- Không có quyết định nào -> nêu rõ "cuộc họp không đi đến quyết định chính
  thức nào". KHÔNG nâng một thảo luận thành quyết định.
- Quyết định có status "rejected" là quyết định ĐÃ BỊ THAY THẾ. Chỉ nhắc tới
  nó như bối cảnh của quyết định thay thế, KHÔNG trình bày như đang có hiệu lực."""


def build_compose_prompt(facts: ReconciledFacts, transcript: Transcript) -> str:
    """Dựng prompt COMPOSE — chỉ chứa dữ kiện, tuyệt đối không có transcript."""
    import json

    digest = facts.fact_digest()
    chapters_hint = [
        {
            "start_ms": chunk.start_ms,
            "end_ms": chunk.end_ms,
            "segment_count": len(chunk.segment_ids),
        }
        for chunk in transcript.chunks
    ]

    return "\n".join(
        [
            "# BỐI CẢNH",
            facts.anchor.as_prompt_context(),
            f"Tiêu đề: {transcript.meta.title}",
            f"Loại cuộc họp: {transcript.meta.meeting_type.value}",
            f"Thời lượng: {transcript.meta.duration_ms // 60000} phút",
            f"Người tham dự: "
            + ", ".join(
                str(s.display_name) for s in transcript.speakers if s.display_name
            ),
            "",
            "# KHUNG THỜI GIAN CHO CHAPTERS",
            "Đặt start_ms/end_ms của các chương trong phạm vi "
            f"0 đến {transcript.meta.duration_ms} mili giây.",
            json.dumps(chapters_hint, ensure_ascii=False),
            "",
            "# DỮ KIỆN ĐÃ XÁC MINH",
            "(đây là TOÀN BỘ thông tin bạn có — không có nguồn nào khác)",
            json.dumps(digest, ensure_ascii=False, indent=2),
            "",
            "# YÊU CẦU",
            "Viết phần văn xuôi của biên bản dựa trên đúng các dữ kiện trên.",
        ]
    )


def run_compose(
    facts: ReconciledFacts,
    transcript: Transcript,
    runner: LLMRunner,
    *,
    pipeline_info: PipelineInfo | None = None,
) -> StructuredMinutes:
    """Sinh văn xuôi rồi lắp ráp ``StructuredMinutes`` hoàn chỉnh."""
    prompt = build_compose_prompt(facts, transcript)

    try:
        prose = runner.run(
            phase="compose",
            prompt=prompt,
            schema=ComposedProse,
            prompt_version=PROMPT_VERSION,
            system=SYSTEM_PROMPT,
        )
    except Exception as exc:
        logger.warning(
            "COMPOSE thất bại (%s). Suy giảm có kiểm soát: dựng tóm tắt bằng "
            "khuôn mẫu từ chính dữ kiện đã hoà giải.",
            exc,
        )
        prose = _fallback_prose(facts)

    chapters = _clamp_chapters(prose.to_chapters(), transcript.meta.duration_ms)
    if not chapters:
        chapters = _fallback_chapters(facts, transcript)

    return StructuredMinutes(
        minutes_id=f"min_{facts.meeting_id}_v1",
        meeting_id=facts.meeting_id,
        version=1,
        generated_at=dt.datetime.now(dt.timezone.utc),
        pipeline=pipeline_info or PipelineInfo(),
        meta=_build_meta(facts, transcript),
        executive_summary=ExecutiveSummary(
            tldr=prose.tldr[:5], paragraphs=prose.paragraphs[:3]
        ),
        chapters=chapters,
        # Tầng sự kiện sao chép NGUYÊN VẸN từ ReconciledFacts.
        # LLM ở pha này không có đường nào chạm vào các trường dưới đây.
        discussion_points=facts.discussion_points,
        decisions=facts.decisions,
        action_items=facts.action_items,
        risks=facts.risks,
        metrics=facts.metrics,
        open_questions=facts.open_questions,
        next_meeting=facts.next_meeting,
        quality_report=QualityReport(
            overall_confidence=_overall_confidence(facts),
            needs_human_review=_needs_review(facts),
            warnings=facts.warnings,
        ),
    )


def _build_meta(facts: ReconciledFacts, transcript: Transcript) -> MinutesMeta:
    return MinutesMeta(
        meeting_title=transcript.meta.title,
        date=facts.anchor.meeting_date,
        duration_minutes=round(transcript.meta.duration_ms / 60000),
        meeting_type=transcript.meta.meeting_type or MeetingType.OTHER,
        language=transcript.language_profile.primary,
        attendees=[
            Attendee(
                person_id=speaker.person_id,
                display_name=str(speaker.display_name or speaker.label),
                speaker_label=speaker.label,
                role=speaker.role,
                talk_time_pct=speaker.talk_time_pct,
                identification_method=speaker.identification_method,
            )
            for speaker in transcript.speakers
        ],
    )


def _clamp_chapters(chapters: list[Chapter], duration_ms: int) -> list[Chapter]:
    """Ép mốc thời gian chương về phạm vi hợp lệ.

    LLM thường sinh mốc thời gian sai lệch, nên Python kẹp lại thay vì tin.
    Chương nào vượt hoàn toàn ra ngoài thời lượng cuộc họp sẽ bị loại.
    """
    clamped: list[Chapter] = []
    for chapter in chapters:
        start = max(0, min(chapter.start_ms, duration_ms))
        end = max(start, min(chapter.end_ms or duration_ms, duration_ms))
        if start >= duration_ms and duration_ms > 0:
            continue
        clamped.append(
            Chapter(
                title=chapter.title,
                summary=chapter.summary,
                start_ms=start,
                end_ms=end,
                consensus_level=chapter.consensus_level,
            )
        )
    return clamped


def _fallback_prose(facts: ReconciledFacts) -> ComposedProse:
    """Tóm tắt bằng khuôn mẫu khi LLM không dùng được.

    Suy giảm có kiểm soát: thà giao một biên bản mộc mạc nhưng đúng dữ kiện
    còn hơn trả về màn hình trắng sau khi đã tiêu quota cho các pha trước.
    """
    lines: list[str] = []

    for decision in facts.active_decisions[:3]:
        lines.append(f"Đã chốt: {decision.statement}")

    for action in facts.action_items[:3]:
        who = action.assignee or "chưa phân công"
        when = action.due_date.isoformat() if action.due_date else "chưa xác định"
        lines.append(f"Công việc: {action.task} — {who}, hạn {when}")

    if not lines:
        lines.append("Cuộc họp không đi đến quyết định chính thức nào.")

    return ComposedProse(tldr=lines[:5], paragraphs=[], chapters=[])


def _fallback_chapters(
    facts: ReconciledFacts, transcript: Transcript
) -> list[Chapter]:
    """Một chương bao trọn cuộc họp, để biên bản không rỗng phần điều hướng."""
    return [
        Chapter(
            title=transcript.meta.title,
            summary=(
                f"Cuộc họp ghi nhận {len(facts.active_decisions)} quyết định và "
                f"{len(facts.action_items)} công việc được giao."
            ),
            start_ms=0,
            end_ms=transcript.meta.duration_ms,
            consensus_level=ConsensusLevel.UNSPECIFIED,
        )
    ]


def _overall_confidence(facts: ReconciledFacts) -> Confidence:
    items = [
        *facts.decisions, *facts.action_items, *facts.risks, *facts.metrics
    ]
    if not items:
        return Confidence.LOW
    if any(item.confidence is Confidence.LOW for item in items):
        return Confidence.LOW
    if any(item.confidence is Confidence.MEDIUM for item in items):
        return Confidence.MEDIUM
    return Confidence.HIGH


def _needs_review(facts: ReconciledFacts) -> bool:
    return bool(
        facts.warnings
        or facts.unresolved_conflicts
        or any(action.needs_review for action in facts.action_items)
    )
