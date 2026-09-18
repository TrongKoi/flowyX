"""Schema cho ``StructuredMinutes`` — hợp đồng giữa tầng LLM và phần còn lại.

Sáu nguyên tắc thiết kế được cưỡng chế bằng code trong module này:

1. ``extra="forbid"`` ở mọi cấp — chặn LLM tự thêm trường.
2. Mọi mục trích xuất BẮT BUỘC có ``evidence_segment_ids`` không rỗng —
   không bằng chứng thì không tồn tại.
3. ``None`` là giá trị hợp lệ và có "van xả" (``ambiguities``) — model phải
   có đường thoát hợp pháp thay vì buộc phải bịa.
4. Dùng ``Enum`` thay vì free text ở mọi chỗ có thể.
5. Giới hạn độ dài tường minh — chặn model lan man.
6. ``confidence`` ở cấp từng mục, không phải cấp tài liệu.
"""

from __future__ import annotations

import datetime as dt
from typing import Iterator

from pydantic import Field, model_validator

from schemas.common import (
    ActionStatus,
    CommitmentStrength,
    Confidence,
    ConsensusLevel,
    DecisionStatus,
    IdentificationMethod,
    Language,
    MeetingType,
    Priority,
    ReviewState,
    RiskStatus,
    SegmentId,
    Self,
    Severity,
    StrictModel,
    WarningCode,
)

__all__ = [
    "Grounded",
    "Attendee",
    "MinutesMeta",
    "ExecutiveSummary",
    "Chapter",
    "DiscussionPoint",
    "Objection",
    "Decision",
    "ActionItem",
    "Risk",
    "Metric",
    "OpenQuestion",
    "NextMeeting",
    "QualityWarning",
    "QualityReport",
    "ValidationCheck",
    "ValidationReport",
    "PipelineInfo",
    "StructuredMinutes",
]


class Grounded(StrictModel):
    """Base cho mọi mục phải có bằng chứng.

    ``min_length=1`` trên ``evidence_segment_ids`` là chốt chặn chống
    hallucination quan trọng nhất ở tầng schema: một mục không dẫn được về
    segment nào trong transcript thì không được phép tồn tại.
    """

    evidence_segment_ids: list[SegmentId] = Field(min_length=1)
    confidence: Confidence = Confidence.MEDIUM
    timestamp_ms: int | None = Field(default=None, ge=0)

    @property
    def is_uncertain(self) -> bool:
        return self.confidence is Confidence.LOW


class Attendee(StrictModel):
    person_id: str | None = None
    display_name: str = Field(min_length=1, max_length=100)
    speaker_label: str | None = None
    role: str | None = Field(default=None, max_length=100)
    talk_time_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    identification_method: IdentificationMethod = IdentificationMethod.UNIDENTIFIED


class MinutesMeta(StrictModel):
    meeting_title: str = Field(min_length=1, max_length=200)
    date: dt.date
    duration_minutes: int = Field(ge=0)
    meeting_type: MeetingType = MeetingType.OTHER
    language: Language = Language.VI
    attendees: list[Attendee] = Field(default_factory=list)

    @property
    def attendee_names(self) -> set[str]:
        return {a.display_name for a in self.attendees}


class ExecutiveSummary(StrictModel):
    """Phần duy nhất lãnh đạo thực sự đọc — mỗi gạch đầu dòng phải đứng độc lập."""

    tldr: list[str] = Field(min_length=1, max_length=5)
    paragraphs: list[str] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def _check_lengths(self) -> Self:
        for line in self.tldr:
            if len(line) > 180:
                raise ValueError(f"Dòng tl;dr vượt 180 ký tự: {line[:60]}...")
        for para in self.paragraphs:
            if len(para) > 800:
                raise ValueError("Đoạn văn tóm tắt vượt 800 ký tự")
        return self


class Chapter(StrictModel):
    """Chương có mốc thời gian, vừa để điều hướng vừa là đơn vị chunk ngữ nghĩa."""

    title: str = Field(min_length=1, max_length=120)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    summary: str = Field(max_length=600)
    consensus_level: ConsensusLevel = ConsensusLevel.UNSPECIFIED

    @model_validator(mode="after")
    def _check_time_order(self) -> Self:
        if self.end_ms < self.start_ms:
            raise ValueError(f"Chương {self.title!r}: end_ms < start_ms")
        return self


class DiscussionPoint(Grounded):
    point: str = Field(min_length=1, max_length=400)
    speakers: list[str] = Field(default_factory=list)


class Objection(StrictModel):
    """Ý kiến phản đối được ghi nhận trước khi chốt — phần cốt lõi của hồ sơ quyết định."""

    by: str | None = None
    person_id: str | None = None
    reason: str = Field(min_length=1, max_length=300)
    evidence_segment_ids: list[SegmentId] = Field(default_factory=list)


class Decision(Grounded):
    """Một quyết định, kèm quan hệ thay thế nếu bị đảo ngược trong cuộc họp.

    Quyết định bị đảo KHÔNG bị xoá mà chỉ chuyển ``status`` thành ``REJECTED``
    và liên kết ``superseded_by``. Giữ lại lịch sử là điều kiện để trả lời
    câu hỏi "6 tháng trước tại sao mình lại chọn phương án đó".
    """

    id: str = Field(min_length=1)
    statement: str = Field(min_length=1, max_length=300)
    status: DecisionStatus
    decided_by: str | None = None
    decided_by_person_id: str | None = None
    rationale: str | None = Field(default=None, max_length=400)
    alternatives_considered: list[str] = Field(default_factory=list, max_length=5)
    objections: list[Objection] = Field(default_factory=list, max_length=5)
    supersedes: str | None = None
    superseded_by: str | None = None
    target_date: dt.date | None = None
    quote: str | None = Field(default=None, max_length=200)
    display_hint: str | None = None
    review_state: ReviewState = ReviewState.AI_GENERATED

    @model_validator(mode="after")
    def _rejected_needs_reason(self) -> Self:
        if self.status is DecisionStatus.REJECTED and not self.superseded_by:
            raise ValueError(
                f"Quyết định {self.id} bị loại nhưng không nêu quyết định nào thay thế nó"
            )
        if self.supersedes and self.supersedes == self.id:
            raise ValueError(f"Quyết định {self.id} không thể tự thay thế chính nó")
        return self

    @property
    def is_active(self) -> bool:
        return self.status is DecisionStatus.DECIDED


class ActionItem(Grounded):
    """Công việc được giao, thực thể có vòng đời riêng sống xuyên cuộc họp.

    Luôn giữ ``assignee_raw`` và ``due_raw`` (nguyên văn như đã nói) bên cạnh
    giá trị đã phân giải. Người dùng cần đối chiếu được với thứ họ thực sự
    nghe thấy, và bước validate cần chúng để phát hiện ngày bịa.
    """

    id: str = Field(min_length=1)
    task: str = Field(min_length=1, max_length=300)
    assignee: str | None = None
    assignee_raw: str | None = None
    assignee_person_id: str | None = None
    due_date: dt.date | None = None
    due_raw: str | None = None
    due_resolution_rule: str | None = None
    commitment_strength: CommitmentStrength = CommitmentStrength.TENTATIVE
    priority: Priority = Priority.UNSPECIFIED
    status: ActionStatus = ActionStatus.OPEN
    depends_on: list[str] = Field(default_factory=list)
    related_decision_id: str | None = None
    carried_over_from: str | None = None
    quote: str | None = Field(default=None, max_length=200)
    needs_review: bool = False
    review_state: ReviewState = ReviewState.AI_GENERATED

    @model_validator(mode="after")
    def _due_date_must_have_source(self) -> Self:
        """Có ``due_date`` mà không có ``due_raw`` là dấu hiệu LLM tự bịa ngày.

        Không ai nói deadline thì trường này phải để trống. Bịa ra một mốc
        thời gian nghe hợp lý là loại hallucination nguy hiểm nhất của bài
        toán này, vì nó trông không giống lỗi.
        """
        if self.due_date is not None and not self.due_raw:
            raise ValueError(
                f"Action item {self.id}: có due_date ({self.due_date}) nhưng "
                "không có due_raw. Không ai nêu mốc thời gian trong cuộc họp."
            )
        return self

    @property
    def is_unassigned(self) -> bool:
        return self.assignee is None and self.assignee_person_id is None


class Risk(Grounded):
    id: str = Field(min_length=1)
    risk: str = Field(min_length=1, max_length=300)
    severity: Severity = Severity.UNSPECIFIED
    raised_by: str | None = None
    raised_by_person_id: str | None = None
    mitigation: str | None = Field(default=None, max_length=300)
    status: RiskStatus = RiskStatus.OPEN


class Metric(Grounded):
    """Một con số được nêu trong cuộc họp.

    ``value_raw`` giữ NGUYÊN VĂN. Không tự quy đổi đơn vị, không làm tròn:
    transcript nói "2.3%" thì biên bản phải ghi "2.3%", không phải "2%".
    Đây cũng là trường mà bước validate đối chiếu ngược với transcript.
    """

    id: str = Field(min_length=1)
    label: str = Field(min_length=1, max_length=100)
    value_raw: str = Field(min_length=1, max_length=60)
    value_normalized: float | None = None
    unit: str | None = None
    period: str | None = None
    trend: str | None = None


class OpenQuestion(Grounded):
    id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=250)
    asked_by: str | None = None
    deferred_to: str | None = None


class NextMeeting(StrictModel):
    when_raw: str | None = None
    when_date: dt.date | None = None
    resolution_rule: str | None = None
    proposed_agenda: list[str] = Field(default_factory=list)
    evidence_segment_ids: list[SegmentId] = Field(default_factory=list)


class QualityWarning(StrictModel):
    """Cảnh báo hướng người dùng tới đúng chỗ cần kiểm tra lại.

    Một hệ thống dám nói "tôi không chắc về mục này" đáng tin hơn nhiều một
    hệ thống luôn trả về kết quả bóng bẩy như nhau.
    """

    code: WarningCode
    message: str = Field(min_length=1, max_length=250)
    affected_items: list[str] = Field(default_factory=list)
    severity: Severity = Severity.MEDIUM


class QualityReport(StrictModel):
    overall_confidence: Confidence = Confidence.MEDIUM
    needs_human_review: bool = False
    warnings: list[QualityWarning] = Field(default_factory=list)

    @property
    def warning_codes(self) -> set[WarningCode]:
        return {w.code for w in self.warnings}

    def has(self, code: WarningCode) -> bool:
        return code in self.warning_codes


class ValidationCheck(StrictModel):
    passed: bool
    checked: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    detail: str | None = None


class ValidationReport(StrictModel):
    """Kết quả tầng kiểm chứng — gần như toàn bộ chạy bằng Python, 0 quota."""

    validated_at: dt.datetime | None = None
    validator_version: str = "1.0.0"
    schema_valid: bool = True
    checks: dict[str, ValidationCheck] = Field(default_factory=dict)
    grounding_score: float = Field(default=1.0, ge=0.0, le=1.0)
    items_rejected: list[str] = Field(default_factory=list)
    items_downgraded: list[str] = Field(default_factory=list)
    llm_judge_invoked: bool = False


class PipelineInfo(StrictModel):
    """Ghi vết để tái lập kết quả và truy nguồn gốc lỗi khi có khiếu nại."""

    asr_provider: str | None = None
    llm_provider: str | None = None
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    total_llm_requests: int = Field(default=0, ge=0)
    total_tokens_estimate: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0)


class StructuredMinutes(StrictModel):
    """Đầu ra cuối cùng của pipeline.

    Đây là DỮ LIỆU, không phải tài liệu. File DOCX/PDF/Markdown chỉ là các
    *view* được render từ đối tượng này — đổi template không cần gọi lại LLM.
    """

    minutes_id: str = Field(min_length=1)
    meeting_id: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    generated_at: dt.datetime | None = None
    pipeline: PipelineInfo = Field(default_factory=PipelineInfo)

    meta: MinutesMeta
    executive_summary: ExecutiveSummary
    chapters: list[Chapter] = Field(default_factory=list)
    discussion_points: list[DiscussionPoint] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)
    next_meeting: NextMeeting | None = None

    quality_report: QualityReport = Field(default_factory=QualityReport)
    validation: ValidationReport | None = None

    # -- Kiểm tra toàn vẹn nội bộ ------------------------------------------ #

    @model_validator(mode="after")
    def _check_unique_ids(self) -> Self:
        for name, items in (
            ("decisions", self.decisions),
            ("action_items", self.action_items),
            ("risks", self.risks),
            ("metrics", self.metrics),
            ("open_questions", self.open_questions),
        ):
            ids = [item.id for item in items]
            if len(ids) != len(set(ids)):
                duplicates = sorted({i for i in ids if ids.count(i) > 1})
                raise ValueError(f"ID trùng trong {name}: {duplicates}")
        return self

    @model_validator(mode="after")
    def _check_supersession_integrity(self) -> Self:
        """Quan hệ thay thế phải nhất quán hai chiều và đúng chiều thời gian.

        Đây là nơi bắt lỗi map-reduce ngây thơ: nếu hai quyết định mâu thuẫn
        cùng ở trạng thái ``DECIDED``, biên bản sẽ nói với người đọc hai điều
        trái ngược nhau mà không chỉ ra cái nào còn hiệu lực.
        """
        by_id = {d.id: d for d in self.decisions}

        for decision in self.decisions:
            if decision.supersedes:
                target = by_id.get(decision.supersedes)
                if target is None:
                    raise ValueError(
                        f"Quyết định {decision.id} thay thế {decision.supersedes} "
                        "nhưng ID đó không tồn tại"
                    )
                if target.status is not DecisionStatus.REJECTED:
                    raise ValueError(
                        f"Quyết định {target.id} bị {decision.id} thay thế "
                        f"nhưng status vẫn là {target.status.value}"
                    )
                if target.superseded_by != decision.id:
                    raise ValueError(
                        f"Quan hệ thay thế không nhất quán hai chiều giữa "
                        f"{decision.id} và {target.id}"
                    )
                if (
                    target.timestamp_ms is not None
                    and decision.timestamp_ms is not None
                    and target.timestamp_ms >= decision.timestamp_ms
                ):
                    raise ValueError(
                        f"Quyết định {decision.id} thay thế {target.id} nhưng lại "
                        "xảy ra TRƯỚC nó — sai chiều thời gian"
                    )

            if decision.superseded_by and decision.superseded_by not in by_id:
                raise ValueError(
                    f"Quyết định {decision.id} trỏ tới {decision.superseded_by} "
                    "nhưng ID đó không tồn tại"
                )
        return self

    @model_validator(mode="after")
    def _check_dependency_references(self) -> Self:
        action_ids = {a.id for a in self.action_items}
        decision_ids = {d.id for d in self.decisions}

        for action in self.action_items:
            unknown = [dep for dep in action.depends_on if dep not in action_ids]
            if unknown:
                raise ValueError(
                    f"Action item {action.id} phụ thuộc công việc không tồn tại: {unknown}"
                )
            if action.id in action.depends_on:
                raise ValueError(f"Action item {action.id} phụ thuộc chính nó")
            if (
                action.related_decision_id
                and action.related_decision_id not in decision_ids
            ):
                raise ValueError(
                    f"Action item {action.id} trỏ tới quyết định không tồn tại: "
                    f"{action.related_decision_id}"
                )
        return self

    # -- Truy vấn tiện dụng ------------------------------------------------- #

    def iter_grounded_items(self) -> Iterator[Grounded]:
        """Duyệt mọi mục mang bằng chứng — dùng cho tầng grounding validator."""
        yield from self.discussion_points
        yield from self.decisions
        yield from self.action_items
        yield from self.risks
        yield from self.metrics
        yield from self.open_questions

    @property
    def active_decisions(self) -> list[Decision]:
        """Chỉ các quyết định còn hiệu lực. Đây là thứ được render ra biên bản."""
        return [d for d in self.decisions if d.is_active]

    @property
    def superseded_decisions(self) -> list[Decision]:
        return [d for d in self.decisions if d.status is DecisionStatus.REJECTED]

    @property
    def unassigned_actions(self) -> list[ActionItem]:
        return [a for a in self.action_items if a.is_unassigned]

    @property
    def items_needing_review(self) -> list[str]:
        flagged = [a.id for a in self.action_items if a.needs_review]
        flagged += [
            getattr(item, "id")
            for item in self.iter_grounded_items()
            if item.is_uncertain and hasattr(item, "id")
        ]
        return sorted(set(flagged))

    @property
    def all_evidence_ids(self) -> set[str]:
        ids: set[str] = set()
        for item in self.iter_grounded_items():
            ids.update(item.evidence_segment_ids)
        return ids
