"""Schema cho đầu ra pha EXTRACT (Map) — sự kiện thô trích từ một chunk.

Khác biệt cố ý so với ``schemas/minutes.py``: ở đây ``evidence_segment_ids``
khai là ``list[str]`` thay vì ``SegmentId`` có ràng buộc pattern.

Lý do rất thực dụng: nếu ràng buộc pattern ngay tại tầng parse, chỉ cần LLM
gõ sai MỘT ID là toàn bộ payload của chunk bị từ chối và ta mất trắng một
request quota. Thay vào đó, ``s4_extract`` lọc từng ID theo tập segment có
thật của chunk và chỉ loại bỏ những mục không còn bằng chứng nào — hỏng một
mục thay vì hỏng cả chunk.
"""

from __future__ import annotations

from pydantic import Field

from schemas.common import (
    CommitmentStrength,
    Confidence,
    DecisionStatus,
    Priority,
    Severity,
    StrictModel,
)

__all__ = [
    "RawDiscussionPoint",
    "RawDecision",
    "RawActionItem",
    "RawRisk",
    "RawMetric",
    "RawOpenQuestion",
    "ExtractionNotes",
    "ChunkExtraction",
]


class _RawItem(StrictModel):
    """Base cho mọi mục do LLM trích xuất."""

    evidence_segment_ids: list[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.MEDIUM


class RawDiscussionPoint(_RawItem):
    point: str = Field(min_length=1, max_length=400)
    speakers: list[str] = Field(default_factory=list)


class RawDecision(_RawItem):
    statement: str = Field(min_length=1, max_length=300)
    status: DecisionStatus = DecisionStatus.TENTATIVE
    decided_by: str | None = None
    alternatives_considered: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    quote: str | None = Field(default=None, max_length=200)


class RawActionItem(_RawItem):
    """Công việc được trích xuất.

    ``assignee_raw`` và ``due_raw`` giữ NGUYÊN VĂN như đã nói trong cuộc họp.
    Việc phân giải sang ``person_id`` và ngày tuyệt đối là trách nhiệm của pha
    RECONCILE, không phải của LLM ở pha này — tách bạch như vậy để mỗi pha chỉ
    có một nhiệm vụ và sai sót dễ khoanh vùng.
    """

    task: str = Field(min_length=1, max_length=300)
    assignee_raw: str | None = None
    due_raw: str | None = None
    commitment_strength: CommitmentStrength = CommitmentStrength.TENTATIVE
    priority: Priority = Priority.UNSPECIFIED
    quote: str | None = Field(default=None, max_length=200)


class RawRisk(_RawItem):
    risk: str = Field(min_length=1, max_length=300)
    severity: Severity = Severity.UNSPECIFIED
    raised_by: str | None = None
    mitigation: str | None = Field(default=None, max_length=300)


class RawMetric(_RawItem):
    label: str = Field(min_length=1, max_length=100)
    value_raw: str = Field(min_length=1, max_length=60)
    period: str | None = None


class RawOpenQuestion(_RawItem):
    question: str = Field(min_length=1, max_length=250)
    asked_by: str | None = None


class ExtractionNotes(StrictModel):
    """Van xả cho sự không chắc chắn.

    Cho model một nơi hợp pháp để nói "tôi không biết" là kỹ thuật chống
    hallucination rẻ và hiệu quả: nếu không có chỗ này, áp lực phải điền đầy
    mọi trường sẽ đẩy model sang suy diễn.
    """

    audio_quality_issues: list[str] = Field(default_factory=list, max_length=5)
    ambiguities: list[str] = Field(default_factory=list, max_length=5)


class ChunkExtraction(StrictModel):
    """Toàn bộ sự kiện trích được từ một chunk. Mảng rỗng là kết quả hợp lệ."""

    chunk_id: str = ""
    topic: str | None = Field(default=None, max_length=120)
    discussion_points: list[RawDiscussionPoint] = Field(default_factory=list, max_length=8)
    decisions: list[RawDecision] = Field(default_factory=list, max_length=10)
    action_items: list[RawActionItem] = Field(default_factory=list, max_length=20)
    risks: list[RawRisk] = Field(default_factory=list, max_length=10)
    metrics: list[RawMetric] = Field(default_factory=list, max_length=15)
    open_questions: list[RawOpenQuestion] = Field(default_factory=list, max_length=10)
    extraction_notes: ExtractionNotes = Field(default_factory=ExtractionNotes)

    def iter_items(self) -> list[_RawItem]:
        return [
            *self.discussion_points,
            *self.decisions,
            *self.action_items,
            *self.risks,
            *self.metrics,
            *self.open_questions,
        ]
