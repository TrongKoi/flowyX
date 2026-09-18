"""Pha 3 — RECONCILE (Reduce): hoà giải các mảnh trích xuất thành một sự thật.

Nguyên tắc phân công của pha này: **LLM đề xuất, Python phán quyết.**

LLM chỉ được hỏi đúng một câu — "những quyết định nào dưới đây nói về cùng
một vấn đề?" — vì đó là câu hỏi cần hiểu ngôn ngữ. Mọi thứ còn lại (so sánh
mốc thời gian, quy đổi ngày, khớp tên, khử trùng lặp) đều là logic tất định
và được làm bằng Python.

Lý do không giao phần đó cho LLM có hai mặt. Về chất lượng: LLM tính ngày
sai một cách *âm thầm*, cho ra một ngày trông hợp lý nhưng lệch, và không
thể viết test hồi quy cho hành vi phi tất định. Về chi phí: mỗi phép tính
chuyển sang Python là một request quota tiết kiệm được — với free tier, đó
là tài nguyên khan hiếm nhất.

Lỗi mà pha này tồn tại để sửa
-----------------------------
Map-Reduce ngây thơ xử lý các chunk độc lập rồi gộp lại, nên khi phút 12
chốt "release 26/07" và phút 48 đổi thành "lùi sang 28/07", biên bản sẽ
chứa **cả hai** như hai quyết định song song. Người đọc không biết cái nào
còn hiệu lực. Đây là loại lỗi tinh vi vì kết quả vẫn trông chỉn chu.
"""

from __future__ import annotations

import datetime as dt
import logging
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from pydantic import BaseModel, Field

from nlp.vn_dates import ResolutionRule, resolve_vietnamese_date
from providers.base import LLMRunner
from schemas.common import (
    ActionStatus,
    CommitmentStrength,
    Confidence,
    DecisionStatus,
    Priority,
    RiskStatus,
    Severity,
    StrictModel,
    WarningCode,
)
from schemas.extraction import ChunkExtraction
from schemas.minutes import (
    ActionItem,
    Decision,
    DiscussionPoint,
    Metric,
    NextMeeting,
    Objection,
    OpenQuestion,
    QualityWarning,
    Risk,
)
from schemas.reconciled import DeduplicationEntry, MeetingAnchor, ReconciledFacts
from schemas.transcript import Transcript

logger = logging.getLogger(__name__)

__all__ = [
    "PROMPT_VERSION",
    "TopicGroup",
    "TopicGrouping",
    "run_reconcile",
    "resolve_person",
]

PROMPT_VERSION = "reconcile.vi.v1.1"

SIMILARITY_THRESHOLD = 0.72
"""Ngưỡng coi hai phát biểu là trùng nội dung khi đã có chung bằng chứng."""

AMBIGUOUS_SUPERSESSION_WINDOW_MS = 15_000
"""Hai quyết định cách nhau dưới ngưỡng này nhiều khả năng là một người đang
nói dở câu, không phải đổi ý. Hạ confidence và gắn cờ thay vì im lặng."""

HONORIFICS = ("anh", "chị", "chi", "em", "bạn", "ban", "cô", "co", "chú",
              "chu", "sếp", "sep", "bác", "bac")


class TopicGroup(StrictModel):
    """Một nhóm quyết định cùng bàn về một vấn đề."""

    topic: str = Field(default="", max_length=120)
    decision_ids: list[str] = Field(default_factory=list)


class TopicGrouping(BaseModel):
    """Đầu ra duy nhất mà LLM được phép sinh ở pha này.

    Phạm vi hẹp là có chủ ý: model không có trường nào để sửa nội dung một
    quyết định, đổi ngày, hay thêm mục mới. Nó chỉ được gom nhóm.
    """

    groups: list[TopicGroup] = Field(default_factory=list)


SYSTEM_PROMPT = """\
Bạn là bộ phân nhóm chủ đề. Đầu vào là danh sách các quyết định được nêu
trong CÙNG MỘT cuộc họp, kèm mốc thời gian.

Nhiệm vụ DUY NHẤT: gom các quyết định NÓI VỀ CÙNG MỘT VẤN ĐỀ CẦN QUYẾT vào
chung một nhóm.

Quy tắc:
- "Cùng một vấn đề" nghĩa là chúng loại trừ nhau: không thể cùng đúng một
  lúc. Ví dụ "release ngày 26/07" và "lùi release sang 28/07" cùng bàn về
  NGÀY PHÁT HÀNH nên thuộc một nhóm.
- Quyết định về hai chủ đề khác nhau thì thuộc hai nhóm khác nhau, kể cả khi
  chúng liên quan tới nhau.
- Mỗi decision_id phải xuất hiện ĐÚNG MỘT LẦN trong toàn bộ kết quả.
- Quyết định đứng riêng vẫn tạo thành một nhóm một phần tử.
- KHÔNG sửa nội dung, KHÔNG thêm quyết định mới, KHÔNG bỏ sót decision_id nào.

Bạn KHÔNG cần phán xét cái nào đúng hay cái nào còn hiệu lực. Việc đó do
thuật toán phía sau xử lý theo thứ tự thời gian."""


@dataclass(slots=True)
class _Counter:
    """Sinh ID tuần tự ngắn gọn cho các thực thể sau hoà giải."""

    prefix: str
    value: int = 0

    def next(self) -> str:
        self.value += 1
        return f"{self.prefix}{self.value:03d}"


@dataclass(slots=True)
class _ReconcileState:
    warnings: list[QualityWarning] = field(default_factory=list)
    dedup_log: list[DeduplicationEntry] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)

    def warn(
        self,
        code: WarningCode,
        message: str,
        affected: list[str],
        severity: Severity = Severity.MEDIUM,
    ) -> None:
        self.warnings.append(
            QualityWarning(
                code=code, message=message[:250],
                affected_items=affected, severity=severity,
            )
        )


# --------------------------------------------------------------------------- #
# Chuẩn hoá và so khớp (Python thuần, 0 quota)
# --------------------------------------------------------------------------- #


def _normalise(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, _normalise(left), _normalise(right)).ratio()


def _name_candidates(raw_name: str) -> list[str]:
    """Sinh các ứng viên tên từ chuỗi nguyên văn.

    Cách gọi trong cuộc họp thường gói tên thật vào ngoặc đơn: LLM trích ra
    ``"em (Minh)"`` cho câu "Em nhận phần submit store". Nếu chỉ bỏ ngoặc rồi
    cắt tiền tố xưng hô thì còn lại chuỗi rỗng và ta mất luôn người nhận việc
    — nên phần trong ngoặc cũng là một ứng viên hợp lệ.
    """
    candidates: list[str] = []

    inside = re.findall(r"\(([^)]*)\)", raw_name)
    outside = _strip_honorifics(re.sub(r"\([^)]*\)", " ", raw_name))

    if outside:
        candidates.append(outside)
    for fragment in inside:
        cleaned = _strip_honorifics(fragment)
        if cleaned:
            candidates.append(cleaned)

    return candidates


def _strip_honorifics(name: str) -> str:
    """Bỏ tiền tố xưng hô để so khớp tên.

    "anh Tuấn", "Tuấn", "bạn Tuấn" đều trỏ về cùng một người — nhưng chỉ khi
    danh sách tham dự có đúng một Tuấn.
    """
    tokens = name.strip().split()
    while tokens and tokens[0].lower().strip(".,") in HONORIFICS:
        tokens.pop(0)
    return " ".join(tokens).strip(" .,:")


def resolve_person(
    raw_name: str | None, transcript: Transcript
) -> tuple[str | None, str | None, Confidence]:
    """Khớp tên nguyên văn với danh sách người tham dự.

    Trả về ``(display_name, person_id, confidence)``. Không khớp được thì trả
    ``(None, None, LOW)`` — **không đoán**. Gán sai người cho một cam kết là
    lỗi tệ hơn nhiều so với để trống.
    """
    if not raw_name:
        return None, None, Confidence.LOW

    speakers = [s for s in transcript.speakers if s.display_name]
    best_fuzzy: tuple[float, object] | None = None

    for candidate in _name_candidates(raw_name):
        exact = [
            s for s in speakers
            if _normalise(str(s.display_name)) == _normalise(candidate)
        ]
        if len(exact) == 1:
            return exact[0].display_name, exact[0].person_id, Confidence.HIGH
        if len(exact) > 1:
            # Hai người trùng tên: KHÔNG gộp, để bước sau gắn cờ.
            return None, None, Confidence.LOW

        for speaker in speakers:
            score = _similarity(str(speaker.display_name), candidate)
            if best_fuzzy is None or score > best_fuzzy[0]:
                best_fuzzy = (score, speaker)

    if best_fuzzy and best_fuzzy[0] >= 0.85:
        return best_fuzzy[1].display_name, best_fuzzy[1].person_id, Confidence.MEDIUM

    return None, None, Confidence.LOW


# --------------------------------------------------------------------------- #
# API chính
# --------------------------------------------------------------------------- #


def run_reconcile(
    extraction_results: list[ChunkExtraction],
    transcript: Transcript,
    anchor: MeetingAnchor,
    runner: LLMRunner,
    *,
    group_topics: bool = True,
) -> ReconciledFacts:
    """Hoà giải toàn bộ mảnh trích xuất thành một tầng sự kiện nhất quán."""
    state = _ReconcileState()

    decisions = _collect_decisions(extraction_results, transcript, anchor, state)
    actions = _collect_actions(extraction_results, transcript, anchor, state)
    risks = _collect_risks(extraction_results, transcript, state)
    metrics = _collect_metrics(extraction_results, transcript, state)
    points = _collect_points(extraction_results, transcript, state)
    questions = _collect_questions(extraction_results, transcript, state)

    if group_topics and len(decisions) > 1:
        groups = _group_decisions(decisions, runner)
    else:
        groups = [[d.id] for d in decisions]

    _apply_temporal_priority(decisions, groups, state)
    _propagate_supersession(decisions, actions, state)
    _flag_quality_issues(extraction_results, actions, state)

    next_meeting = _collect_next_meeting(extraction_results, transcript, anchor)

    return ReconciledFacts(
        reconcile_id=f"rec_{transcript.meeting_id}_v1",
        meeting_id=transcript.meeting_id,
        anchor=anchor,
        discussion_points=points,
        decisions=decisions,
        action_items=actions,
        risks=risks,
        metrics=metrics,
        open_questions=questions,
        next_meeting=next_meeting,
        warnings=state.warnings,
        deduplication_log=state.dedup_log,
        unresolved_conflicts=state.conflicts,
    )


# --------------------------------------------------------------------------- #
# Thu thập và khử trùng lặp
# --------------------------------------------------------------------------- #


def _timestamp_of(transcript: Transcript, evidence: list[str]) -> int:
    """Mốc thời gian của một mục = segment bằng chứng SỚM NHẤT.

    Đây là giá trị nền tảng cho toàn bộ quy tắc ưu tiên thời gian bên dưới.
    """
    return transcript.earliest_timestamp_ms(evidence) or 0


def _merge_duplicates(
    candidates: list[tuple[object, list[str], int]],
    text_of: object,
    state: _ReconcileState,
    label: str,
) -> list[tuple[object, list[str], int]]:
    """Gộp các mục trùng do chunk chồng lấn sinh ra.

    Hai mục được coi là trùng khi vừa **chung ít nhất một segment bằng
    chứng** vừa **nội dung tương đồng cao**. Chỉ dùng một trong hai điều kiện
    là không đủ: cùng segment có thể chứa hai việc khác nhau, còn nội dung
    giống nhau có thể là hai lần nhắc ở hai thời điểm khác nhau.
    """
    survivors: list[tuple[object, list[str], int]] = []

    for item, evidence, timestamp in candidates:
        text = str(text_of(item))
        matched = False

        for index, (kept_item, kept_evidence, kept_ts) in enumerate(survivors):
            shares_evidence = bool(set(evidence) & set(kept_evidence))
            if not shares_evidence:
                continue
            if _similarity(text, str(text_of(kept_item))) < SIMILARITY_THRESHOLD:
                continue

            merged_evidence = sorted(set(kept_evidence) | set(evidence))
            survivors[index] = (kept_item, merged_evidence, min(kept_ts, timestamp))
            state.dedup_log.append(
                DeduplicationEntry(
                    action="merged",
                    kept=text[:60],
                    affected=sorted(set(evidence) - set(kept_evidence)),
                    reason=f"{label} trùng do chunk chồng lấn",
                )
            )
            matched = True
            break

        if not matched:
            survivors.append((item, sorted(set(evidence)), timestamp))

    return survivors


def _collect_decisions(
    results: list[ChunkExtraction],
    transcript: Transcript,
    anchor: MeetingAnchor,
    state: _ReconcileState,
) -> list[Decision]:
    raw = [
        (d, d.evidence_segment_ids, _timestamp_of(transcript, d.evidence_segment_ids))
        for extraction in results
        for d in extraction.decisions
    ]
    raw.sort(key=lambda triple: triple[2])
    merged = _merge_duplicates(raw, lambda d: d.statement, state, "Quyết định")

    counter = _Counter("d_")
    decisions: list[Decision] = []

    for item, evidence, timestamp in merged:
        name, person_id, _ = resolve_person(item.decided_by, transcript)

        # Quyết định thường mang một mốc thời gian ngay trong nội dung
        # ("lùi release sang thứ 3 tuần sau"). Quy đổi nó ở đây, bằng cùng
        # thuật toán tất định dùng cho deadline của công việc, để biên bản
        # nêu được ngày cụ thể thay vì chỉ lặp lại cách nói tương đối.
        target = resolve_vietnamese_date(item.statement, anchor.meeting_date)

        decisions.append(
            Decision(
                id=counter.next(),
                statement=item.statement,
                status=item.status,
                decided_by=name or item.decided_by,
                decided_by_person_id=person_id,
                target_date=target.date,
                alternatives_considered=item.alternatives_considered[:5],
                objections=[
                    Objection(reason=text[:300]) for text in item.objections[:5]
                ],
                quote=item.quote,
                evidence_segment_ids=evidence,
                confidence=item.confidence,
                timestamp_ms=timestamp,
            )
        )
    return decisions


def _collect_actions(
    results: list[ChunkExtraction],
    transcript: Transcript,
    anchor: MeetingAnchor,
    state: _ReconcileState,
) -> list[ActionItem]:
    raw = [
        (a, a.evidence_segment_ids, _timestamp_of(transcript, a.evidence_segment_ids))
        for extraction in results
        for a in extraction.action_items
    ]
    raw.sort(key=lambda triple: triple[2])
    merged = _merge_duplicates(raw, lambda a: a.task, state, "Công việc")

    counter = _Counter("a_")
    actions: list[ActionItem] = []

    for item, evidence, timestamp in merged:
        action_id = counter.next()
        name, person_id, assignee_confidence = resolve_person(
            item.assignee_raw, transcript
        )

        # Quy đổi ngày bằng thuật toán tất định, KHÔNG hỏi LLM.
        resolution = resolve_vietnamese_date(item.due_raw, anchor.meeting_date)
        due_date = resolution.date

        if item.due_raw and due_date is None:
            rejected_rules = (
                ResolutionRule.REJECTED_PAST_DATE,
                ResolutionRule.REJECTED_IMPLAUSIBLE,
            )
            if resolution.rule in rejected_rules:
                code, severity = WarningCode.DATE_IMPLAUSIBLE, Severity.MEDIUM
            else:
                code, severity = WarningCode.LOW_COMMITMENT_STRENGTH, Severity.LOW
            state.warn(
                code,
                f'Không quy đổi được mốc "{item.due_raw}" thành ngày cụ thể '
                f"({resolution.rule.value}). Giữ nguyên văn để người dùng tự xác định.",
                [action_id],
                severity,
            )

        needs_review = (
            item.assignee_raw is not None and person_id is None
        ) or item.commitment_strength is CommitmentStrength.TENTATIVE

        if item.assignee_raw and name is None:
            state.warn(
                WarningCode.AMBIGUOUS_ASSIGNEE,
                f'Không khớp được "{item.assignee_raw}" với người tham dự nào. '
                "Để trống thay vì đoán.",
                [action_id],
                Severity.MEDIUM,
            )
        elif item.assignee_raw is None:
            state.warn(
                WarningCode.AMBIGUOUS_ASSIGNEE,
                "Công việc không được giao cho ai trong cuộc họp. "
                "Cần xác định người phụ trách.",
                [action_id],
                Severity.HIGH,
            )
            needs_review = True

        actions.append(
            ActionItem(
                id=action_id,
                task=item.task,
                assignee=name,
                assignee_raw=item.assignee_raw,
                assignee_person_id=person_id,
                due_date=due_date,
                due_raw=item.due_raw,
                due_resolution_rule=resolution.rule_display,
                commitment_strength=item.commitment_strength,
                priority=item.priority,
                status=ActionStatus.OPEN,
                quote=item.quote,
                evidence_segment_ids=evidence,
                confidence=_downgrade_if(item.confidence, assignee_confidence),
                timestamp_ms=timestamp,
                needs_review=needs_review,
            )
        )
    return actions


def _downgrade_if(base: Confidence, assignee: Confidence) -> Confidence:
    """Không chắc về người nhận việc thì cả mục cũng không thể chắc."""
    order = [Confidence.LOW, Confidence.MEDIUM, Confidence.HIGH]
    return order[min(order.index(base), order.index(assignee))]


def _collect_risks(
    results: list[ChunkExtraction], transcript: Transcript, state: _ReconcileState
) -> list[Risk]:
    raw = [
        (r, r.evidence_segment_ids, _timestamp_of(transcript, r.evidence_segment_ids))
        for extraction in results
        for r in extraction.risks
    ]
    raw.sort(key=lambda triple: triple[2])
    merged = _merge_duplicates(raw, lambda r: r.risk, state, "Rủi ro")

    counter = _Counter("r_")
    risks: list[Risk] = []
    for item, evidence, timestamp in merged:
        name, person_id, _ = resolve_person(item.raised_by, transcript)
        risks.append(
            Risk(
                id=counter.next(),
                risk=item.risk,
                severity=item.severity,
                raised_by=name or item.raised_by,
                raised_by_person_id=person_id,
                mitigation=item.mitigation,
                status=RiskStatus.MITIGATED if item.mitigation else RiskStatus.OPEN,
                evidence_segment_ids=evidence,
                confidence=item.confidence,
                timestamp_ms=timestamp,
            )
        )
    return risks


def _collect_metrics(
    results: list[ChunkExtraction], transcript: Transcript, state: _ReconcileState
) -> list[Metric]:
    raw = [
        (m, m.evidence_segment_ids, _timestamp_of(transcript, m.evidence_segment_ids))
        for extraction in results
        for m in extraction.metrics
    ]
    raw.sort(key=lambda triple: triple[2])
    merged = _merge_duplicates(
        raw, lambda m: f"{m.label} {m.value_raw}", state, "Chỉ số"
    )

    counter = _Counter("m_")
    return [
        Metric(
            id=counter.next(),
            label=item.label,
            value_raw=item.value_raw,
            value_normalized=_parse_number(item.value_raw),
            unit=_detect_unit(item.value_raw),
            period=item.period,
            evidence_segment_ids=evidence,
            confidence=item.confidence,
            timestamp_ms=timestamp,
        )
        for item, evidence, timestamp in merged
    ]


def _parse_number(value_raw: str) -> float | None:
    """Đọc con số đầu tiên. Giữ nguyên ``value_raw``, chỉ thêm dạng số hoá.

    Dấu thập phân của Việt Nam là dấu PHẨY. Nhầm lẫn ở đây gây sai lệch tài
    chính nghiêm trọng, nên chỉ coi phẩy là thập phân khi theo sau đúng 1–2
    chữ số, còn lại hiểu là dấu phân cách hàng nghìn.
    """
    match = re.search(r"-?\d+(?:[.,]\d+)?", value_raw)
    if not match:
        return None
    token = match.group(0)
    if "," in token and re.fullmatch(r"-?\d+,\d{1,2}", token):
        token = token.replace(",", ".")
    else:
        token = token.replace(",", "")
    try:
        return float(token)
    except ValueError:
        return None


def _detect_unit(value_raw: str) -> str | None:
    lowered = value_raw.lower()
    for needle, unit in (
        ("%", "percent"), ("giây", "second"), ("phút", "minute"),
        ("giờ", "hour"), ("ngày", "day"), ("tỉ", "billion"),
        ("tỷ", "billion"), ("triệu", "million"),
    ):
        if needle in lowered:
            return unit
    return None


def _collect_points(
    results: list[ChunkExtraction], transcript: Transcript, state: _ReconcileState
) -> list[DiscussionPoint]:
    raw = [
        (p, p.evidence_segment_ids, _timestamp_of(transcript, p.evidence_segment_ids))
        for extraction in results
        for p in extraction.discussion_points
    ]
    raw.sort(key=lambda triple: triple[2])
    merged = _merge_duplicates(raw, lambda p: p.point, state, "Ý thảo luận")
    return [
        DiscussionPoint(
            point=item.point,
            speakers=item.speakers,
            evidence_segment_ids=evidence,
            confidence=item.confidence,
            timestamp_ms=timestamp,
        )
        for item, evidence, timestamp in merged
    ]


def _collect_questions(
    results: list[ChunkExtraction], transcript: Transcript, state: _ReconcileState
) -> list[OpenQuestion]:
    raw = [
        (q, q.evidence_segment_ids, _timestamp_of(transcript, q.evidence_segment_ids))
        for extraction in results
        for q in extraction.open_questions
    ]
    raw.sort(key=lambda triple: triple[2])
    merged = _merge_duplicates(raw, lambda q: q.question, state, "Câu hỏi mở")

    counter = _Counter("q_")
    questions: list[OpenQuestion] = []
    for item, evidence, timestamp in merged:
        name, _, _ = resolve_person(item.asked_by, transcript)
        questions.append(
            OpenQuestion(
                id=counter.next(),
                question=item.question,
                asked_by=name or item.asked_by,
                evidence_segment_ids=evidence,
                confidence=item.confidence,
                timestamp_ms=timestamp,
            )
        )
    return questions


def _collect_next_meeting(
    results: list[ChunkExtraction],
    transcript: Transcript,
    anchor: MeetingAnchor,
) -> NextMeeting | None:
    """Dò cuộc họp tiếp theo từ các câu hỏi bị hoãn.

    Quan trọng: mốc thời gian được dò trong SEGMENT TRANSCRIPT GỐC chứ không
    chỉ trong nội dung câu hỏi đã trích xuất. Câu "cái đó để bàn sau, tuần sau
    họp lại" được LLM cô đọng thành câu hỏi "Có cần migrate dữ liệu cũ hay
    không?", làm mất luôn cụm "tuần sau" — thông tin vẫn còn nguyên trong
    segment và ta lấy lại từ đó.
    """
    agenda: list[str] = []
    evidence: list[str] = []
    when_raw: str | None = None

    followup_markers = ("tuần sau", "tuần tới", "họp lại", "bàn sau", "lần sau")

    for extraction in results:
        for question in extraction.open_questions:
            agenda.append(question.question)
            evidence.extend(question.evidence_segment_ids)

            if when_raw is not None:
                continue

            haystack = " ".join(
                [
                    question.question.lower(),
                    transcript.evidence_text(question.evidence_segment_ids).lower(),
                ]
            )
            for marker in followup_markers:
                if marker in haystack:
                    when_raw = marker
                    break

    if not agenda:
        return None

    resolution = resolve_vietnamese_date(when_raw, anchor.meeting_date)
    return NextMeeting(
        when_raw=when_raw,
        when_date=resolution.date,
        resolution_rule=resolution.rule_display,
        proposed_agenda=agenda[:5],
        evidence_segment_ids=sorted(set(evidence)),
    )


# --------------------------------------------------------------------------- #
# Gom nhóm chủ đề (lời gọi LLM DUY NHẤT của pha này)
# --------------------------------------------------------------------------- #


def _group_decisions(decisions: list[Decision], runner: LLMRunner) -> list[list[str]]:
    listing = "\n".join(
        f"- {d.id} (phút {d.timestamp_ms // 60000:02d}:"
        f"{(d.timestamp_ms or 0) // 1000 % 60:02d}): {d.statement}"
        for d in decisions
    )
    prompt = (
        "Gom các quyết định sau theo vấn đề mà chúng cùng bàn tới.\n\n"
        f"{listing}\n\n"
        "Mỗi decision_id phải xuất hiện đúng một lần trong kết quả."
    )

    try:
        grouping = runner.run(
            phase="reconcile_grouping",
            prompt=prompt,
            schema=TopicGrouping,
            prompt_version=PROMPT_VERSION,
            system=SYSTEM_PROMPT,
        )
    except Exception as exc:
        logger.warning(
            "Gom nhóm chủ đề thất bại (%s). Suy giảm có kiểm soát: coi mỗi "
            "quyết định là một nhóm riêng, không áp supersession.",
            exc,
        )
        return [[d.id] for d in decisions]

    known = {d.id for d in decisions}
    groups: list[list[str]] = []
    seen: set[str] = set()

    for group in grouping.groups:
        members = [i for i in group.decision_ids if i in known and i not in seen]
        if members:
            seen.update(members)
            groups.append(members)

    # LLM bỏ sót ID nào thì đưa về nhóm riêng — không để mất dữ liệu.
    for decision in decisions:
        if decision.id not in seen:
            groups.append([decision.id])

    return groups


# --------------------------------------------------------------------------- #
# Quy tắc ưu tiên thời gian
# --------------------------------------------------------------------------- #


def _apply_temporal_priority(
    decisions: list[Decision], groups: list[list[str]], state: _ReconcileState
) -> None:
    """Trong mỗi nhóm, phát biểu SAU đè phát biểu TRƯỚC.

    Mục bị đè KHÔNG bị xoá: nó chuyển sang ``REJECTED`` và giữ liên kết hai
    chiều với mục thay thế. Giữ lịch sử là điều kiện để sau này trả lời được
    "tại sao hồi đó mình lại đổi ý".
    """
    by_id = {d.id: d for d in decisions}

    for member_ids in groups:
        if len(member_ids) < 2:
            continue

        members = sorted(
            (by_id[i] for i in member_ids if i in by_id),
            key=lambda d: d.timestamp_ms or 0,
        )
        active = [d for d in members if d.status is not DecisionStatus.REJECTED]
        if len(active) < 2:
            continue

        winner = active[-1]

        for loser in active[:-1]:
            # Thứ tự gán ở đây quan trọng: ``validate_assignment=True`` khiến
            # validator của Decision chạy ngay tại mỗi phép gán, và nó đòi hỏi
            # một mục REJECTED phải nêu được quyết định nào thay thế nó. Vì
            # vậy ``superseded_by`` phải được đặt TRƯỚC ``status``.
            loser.superseded_by = winner.id
            loser.status = DecisionStatus.REJECTED
            loser.display_hint = "history_only"

            if not any(
                _similarity(loser.statement, existing) >= SIMILARITY_THRESHOLD
                for existing in winner.alternatives_considered
            ):
                # Chỉ ghi thêm khi LLM chưa nêu phương án này. Không kiểm tra
                # thì quyết định bị thay thế sẽ xuất hiện hai lần trong biên
                # bản với hai cách diễn đạt gần giống nhau.
                winner.alternatives_considered = [
                    *winner.alternatives_considered, loser.statement
                ][:5]

            state.dedup_log.append(
                DeduplicationEntry(
                    action="superseded",
                    kept=winner.id,
                    affected=[loser.id],
                    reason=(
                        f"Ưu tiên thời gian: {winner.timestamp_ms}ms > "
                        f"{loser.timestamp_ms}ms, cùng chủ đề"
                    ),
                )
            )

            gap = (winner.timestamp_ms or 0) - (loser.timestamp_ms or 0)
            if gap < AMBIGUOUS_SUPERSESSION_WINDOW_MS:
                winner.confidence = Confidence.MEDIUM
                state.warn(
                    WarningCode.AMBIGUOUS_SUPERSESSION,
                    f"Hai quyết định cách nhau chỉ {gap / 1000:.0f} giây. Có thể "
                    "là một người đang nói dở câu chứ không phải đổi ý.",
                    [winner.id, loser.id],
                    Severity.MEDIUM,
                )

        winner.supersedes = active[-2].id
        winner.status = DecisionStatus.DECIDED


def _propagate_supersession(
    decisions: list[Decision], actions: list[ActionItem], state: _ReconcileState
) -> None:
    """Gắn cờ các cam kết được đưa ra khi một quyết định đã bị đảo còn hiệu lực.

    Đây là bước hay bị bỏ sót nhất. Ví dụ trong cuộc họp mẫu: cam kết "submit
    store trước thứ 6" được đưa ra lúc 02:33, nằm giữa quyết định release
    26/07 (02:18) và quyết định lùi sang 28/07 (03:28). Deadline đó có thể
    không còn phù hợp, nhưng không có bước này thì hệ thống sẽ im lặng xuất
    ra một mốc sai ngữ cảnh.
    """
    by_id = {d.id: d for d in decisions}

    for rejected in decisions:
        if rejected.status is not DecisionStatus.REJECTED or not rejected.superseded_by:
            continue

        replacement = by_id.get(rejected.superseded_by)
        if replacement is None:
            continue

        window_start = rejected.timestamp_ms or 0
        window_end = replacement.timestamp_ms or 0

        for action in actions:
            timestamp = action.timestamp_ms or 0
            if not (window_start <= timestamp <= window_end):
                continue
            if action.due_date is None:
                continue

            action.needs_review = True
            action.related_decision_id = rejected.id
            state.warn(
                WarningCode.SUPERSEDED_DEPENDENCY,
                f"Cam kết được đưa ra khi quyết định {rejected.id} còn hiệu lực, "
                f"sau đó bị {replacement.id} thay thế. Mốc "
                f"{action.due_date.isoformat()} có thể cần điều chỉnh.",
                [action.id, rejected.id, replacement.id],
                Severity.MEDIUM,
            )


def _flag_quality_issues(
    results: list[ChunkExtraction], actions: list[ActionItem], state: _ReconcileState
) -> None:
    """Chuyển ghi chú của LLM và tín hiệu cam kết yếu thành cảnh báo có mã."""
    for extraction in results:
        for issue in extraction.extraction_notes.audio_quality_issues:
            state.warn(WarningCode.TRANSCRIPT_GAPS, issue, [], Severity.LOW)
        for ambiguity in extraction.extraction_notes.ambiguities:
            state.conflicts.append(ambiguity)

    for action in actions:
        if action.commitment_strength is CommitmentStrength.TENTATIVE:
            state.warn(
                WarningCode.LOW_COMMITMENT_STRENGTH,
                f'Công việc "{action.task[:60]}" mới ở mức cam kết dự kiến, '
                "chưa phải cam kết chắc chắn.",
                [action.id],
                Severity.MEDIUM,
            )
