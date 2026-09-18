"""Schema cho đầu ra pha RECONCILE và pha COMPOSE.

``ReconciledFacts`` cố ý tái sử dụng chính các kiểu ``Decision``,
``ActionItem``, ``Risk``... của ``schemas/minutes.py`` thay vì định nghĩa
một bộ kiểu song song.

Đây là quyết định thiết kế then chốt: nhờ vậy, việc lắp ráp
``StructuredMinutes`` ở pha COMPOSE trở thành phép sao chép nguyên vẹn tầng
sự kiện, cộng thêm phần văn xuôi. LLM ở pha COMPOSE **không có đường nào**
để sửa đổi một sự kiện — nó chỉ được sinh ra ``ComposedProse``.
"""

from __future__ import annotations

import datetime as dt

from pydantic import Field

from schemas.common import ConsensusLevel, StrictModel
from schemas.minutes import (
    ActionItem,
    Chapter,
    Decision,
    DiscussionPoint,
    Metric,
    NextMeeting,
    OpenQuestion,
    QualityWarning,
    Risk,
)

__all__ = [
    "MeetingAnchor",
    "DeduplicationEntry",
    "ReconciledFacts",
    "ComposedChapter",
    "ComposedProse",
]


class MeetingAnchor(StrictModel):
    """Mốc neo thời gian. Thiếu nó thì mọi deadline tương đối đều vô nghĩa."""

    meeting_date: dt.date
    timezone: str = "Asia/Ho_Chi_Minh"

    @property
    def weekday(self) -> str:
        return self.meeting_date.strftime("%A")

    @property
    def week_start(self) -> dt.date:
        return self.meeting_date - dt.timedelta(days=self.meeting_date.weekday())

    @property
    def week_end(self) -> dt.date:
        return self.week_start + dt.timedelta(days=6)

    @property
    def next_week_start(self) -> dt.date:
        return self.week_start + dt.timedelta(days=7)

    def as_prompt_context(self) -> str:
        return (
            f"Ngày họp: {self.meeting_date.isoformat()} ({self.weekday}), "
            f"múi giờ {self.timezone}. "
            f"Tuần chứa ngày họp: {self.week_start.isoformat()} đến "
            f"{self.week_end.isoformat()}. "
            f"Tuần sau bắt đầu từ {self.next_week_start.isoformat()}."
        )


class DeduplicationEntry(StrictModel):
    """Nhật ký một thao tác hoà giải, để người dùng truy được vì sao dữ liệu đổi."""

    action: str
    kept: str
    affected: list[str] = Field(default_factory=list)
    reason: str = ""


class ReconciledFacts(StrictModel):
    """Tầng sự kiện đã hoà giải — nguồn sự thật duy nhất cho biên bản.

    Mọi thứ trong đây đã được: khử trùng lặp, phân giải thực thể, quy đổi ngày
    tương đối sang ngày tuyệt đối, và áp quy tắc ưu tiên thời gian cho các
    quyết định mâu thuẫn.
    """

    reconcile_id: str
    meeting_id: str
    anchor: MeetingAnchor

    discussion_points: list[DiscussionPoint] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)
    next_meeting: NextMeeting | None = None

    warnings: list[QualityWarning] = Field(default_factory=list)
    deduplication_log: list[DeduplicationEntry] = Field(default_factory=list)
    unresolved_conflicts: list[str] = Field(default_factory=list)

    @property
    def active_decisions(self) -> list[Decision]:
        return [d for d in self.decisions if d.is_active]

    def fact_digest(self) -> dict[str, object]:
        """Bản rút gọn đưa vào prompt COMPOSE.

        Chỉ chứa dữ kiện đã xác minh, KHÔNG chứa transcript thô. Model không
        thể bịa sự kiện mới vì nó không có nguyên liệu nào để bịa.
        """
        return {
            "decisions": [
                {
                    "id": d.id,
                    "statement": d.statement,
                    "status": d.status.value,
                    "decided_by": d.decided_by,
                    "target_date": d.target_date.isoformat() if d.target_date else None,
                    "alternatives_considered": d.alternatives_considered,
                    "objections": [
                        {"by": o.by, "reason": o.reason} for o in d.objections
                    ],
                    "supersedes": d.supersedes,
                    "timestamp_ms": d.timestamp_ms,
                }
                for d in self.decisions
            ],
            "action_items": [
                {
                    "id": a.id,
                    "task": a.task,
                    "assignee": a.assignee,
                    "due_date": a.due_date.isoformat() if a.due_date else None,
                    "due_raw": a.due_raw,
                    "commitment_strength": a.commitment_strength.value,
                    "timestamp_ms": a.timestamp_ms,
                }
                for a in self.action_items
            ],
            "discussion_points": [
                {
                    "point": p.point,
                    "speakers": p.speakers,
                    "timestamp_ms": p.timestamp_ms,
                }
                for p in self.discussion_points
            ],
            "risks": [
                {"id": r.id, "risk": r.risk, "severity": r.severity.value,
                 "raised_by": r.raised_by, "status": r.status.value}
                for r in self.risks
            ],
            "metrics": [
                {"id": m.id, "label": m.label, "value_raw": m.value_raw,
                 "period": m.period, "trend": m.trend}
                for m in self.metrics
            ],
            "open_questions": [
                {"id": q.id, "question": q.question, "asked_by": q.asked_by,
                 "deferred_to": q.deferred_to}
                for q in self.open_questions
            ],
        }


class ComposedChapter(StrictModel):
    """Chương do LLM sinh. Mốc thời gian do Python gán lại sau, không tin LLM."""

    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(max_length=600)
    start_ms: int = Field(default=0, ge=0)
    end_ms: int = Field(default=0, ge=0)
    consensus_level: ConsensusLevel = ConsensusLevel.UNSPECIFIED


class ComposedProse(StrictModel):
    """Toàn bộ những gì pha COMPOSE được phép sinh ra — chỉ văn xuôi.

    Phạm vi hẹp này chính là cơ chế chống hallucination: model không có
    trường nào để ghi vào một action item hay một deadline mới.
    """

    tldr: list[str] = Field(min_length=1, max_length=5)
    paragraphs: list[str] = Field(default_factory=list, max_length=3)
    chapters: list[ComposedChapter] = Field(default_factory=list, max_length=12)

    def to_chapters(self) -> list[Chapter]:
        return [
            Chapter(
                title=c.title,
                summary=c.summary,
                start_ms=c.start_ms,
                end_ms=max(c.end_ms, c.start_ms),
                consensus_level=c.consensus_level,
            )
            for c in self.chapters
        ]
