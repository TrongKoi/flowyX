"""Pha 5 — VALIDATE: tám lớp kiểm chứng chống hallucination.

Toàn bộ tám lớp chạy bằng Python thuần, dùng ``difflib`` của thư viện chuẩn.
Không phụ thuộc ngoài, **không tốn một token nào**.

Đó không phải chi tiết phụ mà là quyết định thiết kế trung tâm của bản 0
đồng: vì pha này miễn phí và tất định, bạn có thể chạy nó vô hạn lần khi
tinh chỉnh prompt, và nó cho cùng một kết quả mỗi lần — điều kiện cần để
viết test hồi quy.

Nguyên tắc xử lý khi phát hiện vấn đề, xếp theo mức độ:

* **Loại bỏ mục** — khi bằng chứng không tồn tại hoặc trích dẫn không khớp.
  Không có bằng chứng thì mục đó không được phép tồn tại.
* **Xoá trường** — khi một trường đơn lẻ bị bịa (assignee lạ, ngày không có
  nguồn) nhưng phần còn lại của mục vẫn có căn cứ.
* **Hạ confidence** — khi bằng chứng yếu chứ không sai.

Bất đối xứng có chủ ý: với action item và decision, **precision quan trọng
hơn recall**. Bỏ sót một việc thì người dùng bổ sung, hơi phiền. Bịa ra một
việc không ai nói thì họ mất niềm tin vào toàn bộ hệ thống.
"""

from __future__ import annotations

import datetime as dt
import logging
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from schemas.common import Confidence, DecisionStatus, Severity, WarningCode
from schemas.minutes import (
    QualityWarning,
    StructuredMinutes,
    ValidationCheck,
    ValidationReport,
)
from schemas.transcript import Transcript

logger = logging.getLogger(__name__)

__all__ = [
    "VALIDATOR_VERSION",
    "ValidationOutcome",
    "run_validate",
    "QUOTE_REJECT_THRESHOLD",
    "QUOTE_SUSPICIOUS_THRESHOLD",
]

VALIDATOR_VERSION = "1.0.0"

QUOTE_REJECT_THRESHOLD = 0.70
"""Dưới ngưỡng này, trích dẫn coi như không có trong transcript -> loại mục."""

QUOTE_SUSPICIOUS_THRESHOLD = 0.85
"""Trong khoảng 0.70-0.85: nghi ngờ -> hạ confidence và gắn cờ cần review."""

ASSIGNEE_MATCH_THRESHOLD = 0.85

MAX_HORIZON_DAYS = 365

GROUNDING_PASS_THRESHOLD = 0.90
"""Điểm grounding dưới ngưỡng này thì chuyển sang trạng thái cần người duyệt."""

# Từ viết hoa hợp lệ trong văn xuôi mà không phải tên người tham dự.
_PROSE_ALLOWLIST = frozenset(
    {
        "Apple", "Google", "Android", "iOS", "API", "QA", "RC", "UI", "UX",
        "CI", "CD", "Sprint", "Backlog", "Staging", "Release", "Deploy",
        "Store", "Marketing", "Product", "Backend", "Frontend", "Mobile",
    }
)


@dataclass(slots=True)
class ValidationOutcome:
    """Kết quả kiểm chứng kèm biên bản đã được làm sạch."""

    minutes: StructuredMinutes
    report: ValidationReport
    rejected: list[str] = field(default_factory=list)
    downgraded: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.report.grounding_score >= GROUNDING_PASS_THRESHOLD


def _normalise(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())


def _partial_ratio(needle: str, haystack: str) -> float:
    """Tỉ lệ khớp của chuỗi ngắn với đoạn khớp nhất trong chuỗi dài.

    Thay thế ``rapidfuzz.partial_ratio`` bằng ``difflib`` để không thêm phụ
    thuộc ngoài — module này phải chạy được ở mọi môi trường, kể cả on-prem.
    """
    small, large = _normalise(needle), _normalise(haystack)
    if not small or not large:
        return 0.0
    if small in large:
        return 1.0
    if len(small) >= len(large):
        return SequenceMatcher(None, small, large).ratio()

    window = len(small)
    best = 0.0
    step = max(1, window // 4)
    for start in range(0, len(large) - window + 1, step):
        score = SequenceMatcher(None, small, large[start : start + window]).ratio()
        best = max(best, score)
        if best >= 0.99:
            break
    return best


def _extract_numbers(text: str) -> set[str]:
    """Lấy mọi con số, chuẩn hoá dấu thập phân để so khớp Việt–Anh."""
    return {
        token.replace(",", ".").rstrip(".")
        for token in re.findall(r"\d+(?:[.,]\d+)?", text)
    }


def run_validate(
    minutes: StructuredMinutes,
    transcript: Transcript,
    *,
    strict: bool = True,
) -> ValidationOutcome:
    """Chạy tám lớp kiểm chứng và trả về biên bản đã làm sạch.

    Args:
        minutes: Biên bản do pha COMPOSE lắp ráp.
        transcript: Nguồn sự thật để đối chiếu mọi mệnh đề.
        strict: Khi ``False``, chỉ hạ confidence thay vì loại bỏ mục — dùng
            cho việc gỡ lỗi prompt, không dùng cho sản phẩm.

    Returns:
        ``ValidationOutcome`` chứa biên bản đã lọc và báo cáo chi tiết.
    """
    checks: dict[str, ValidationCheck] = {}
    rejected: list[str] = []
    downgraded: list[str] = []
    warnings: list[QualityWarning] = []

    segment_index = transcript.segment_index
    valid_ids = set(segment_index)
    attendee_names = {a.display_name for a in minutes.meta.attendees}

    total_items = sum(1 for _ in minutes.iter_grounded_items())

    checks["evidence_ids_exist"] = _check_evidence_ids(
        minutes, valid_ids, rejected, warnings, strict
    )
    checks["quotes_match_transcript"] = _check_quotes(
        minutes, transcript, rejected, downgraded, warnings, strict
    )
    checks["assignees_in_attendees"] = _check_assignees(
        minutes, attendee_names, warnings
    )
    checks["dates_within_valid_range"] = _check_dates(minutes, warnings)
    checks["supersession_integrity"] = _check_supersession(minutes, warnings)
    checks["numbers_are_grounded"] = _check_numbers(
        minutes, transcript, downgraded, warnings
    )
    checks["prose_entities_known"] = _check_prose_entities(
        minutes, attendee_names, transcript, warnings
    )
    checks["evidence_quality"] = _check_evidence_quality(
        minutes, segment_index, downgraded, warnings
    )

    minutes.quality_report.warnings = [*minutes.quality_report.warnings, *warnings]
    grounding_score = 1.0 - (len(set(rejected)) / total_items) if total_items else 1.0

    if grounding_score < GROUNDING_PASS_THRESHOLD or warnings:
        minutes.quality_report.needs_human_review = True
    if grounding_score < GROUNDING_PASS_THRESHOLD:
        minutes.quality_report.overall_confidence = Confidence.LOW

    report = ValidationReport(
        validated_at=dt.datetime.now(dt.timezone.utc),
        validator_version=VALIDATOR_VERSION,
        schema_valid=True,
        checks=checks,
        grounding_score=round(max(0.0, min(1.0, grounding_score)), 3),
        items_rejected=sorted(set(rejected)),
        items_downgraded=sorted(set(downgraded)),
        llm_judge_invoked=False,
    )
    minutes.validation = report

    logger.info(
        "VALIDATE xong: grounding=%.2f, loại %d mục, hạ cấp %d mục, %d cảnh báo",
        report.grounding_score, len(report.items_rejected),
        len(report.items_downgraded), len(warnings),
    )
    return ValidationOutcome(
        minutes=minutes, report=report, rejected=rejected, downgraded=downgraded
    )


def _item_id(item: object, fallback: str) -> str:
    return str(getattr(item, "id", None) or fallback)


def _filter_collection(minutes: StructuredMinutes, doomed: set[int]) -> None:
    """Loại các mục bị đánh dấu, nhận diện theo ``id()`` của đối tượng."""
    for name in (
        "discussion_points", "decisions", "action_items",
        "risks", "metrics", "open_questions",
    ):
        items = getattr(minutes, name)
        setattr(minutes, name, [i for i in items if id(i) not in doomed])


# --------------------------------------------------------------------------- #
# Lớp 1 — Bằng chứng phải tồn tại
# --------------------------------------------------------------------------- #


def _check_evidence_ids(
    minutes: StructuredMinutes,
    valid_ids: set[str],
    rejected: list[str],
    warnings: list[QualityWarning],
    strict: bool,
) -> ValidationCheck:
    """Chốt chặn quan trọng nhất: LLM bịa segment ID nghĩa là bịa nội dung."""
    checked = failed = 0
    doomed: set[int] = set()

    for position, item in enumerate(minutes.iter_grounded_items()):
        checked += 1
        item_id = _item_id(item, f"item_{position}")
        phantom = [e for e in item.evidence_segment_ids if e not in valid_ids]

        if not phantom:
            continue

        surviving = [e for e in item.evidence_segment_ids if e in valid_ids]
        failed += 1

        if surviving:
            item.evidence_segment_ids = surviving
            warnings.append(
                QualityWarning(
                    code=WarningCode.TRANSCRIPT_GAPS,
                    message=f"Bỏ {len(phantom)} segment ID không tồn tại: {phantom[:3]}",
                    affected_items=[item_id],
                    severity=Severity.LOW,
                )
            )
        elif strict:
            doomed.add(id(item))
            rejected.append(item_id)
            warnings.append(
                QualityWarning(
                    code=WarningCode.CONFLICTING_STATEMENTS,
                    message="Loại mục vì toàn bộ bằng chứng dẫn tới segment không tồn tại.",
                    affected_items=[item_id],
                    severity=Severity.HIGH,
                )
            )

    if doomed:
        _filter_collection(minutes, doomed)

    return ValidationCheck(
        passed=failed == 0,
        checked=checked,
        failed=failed,
        detail="Mọi evidence_segment_ids phải trỏ tới segment có thật",
    )


# --------------------------------------------------------------------------- #
# Lớp 2 — Trích dẫn phải khớp transcript
# --------------------------------------------------------------------------- #


def _check_quotes(
    minutes: StructuredMinutes,
    transcript: Transcript,
    rejected: list[str],
    downgraded: list[str],
    warnings: list[QualityWarning],
    strict: bool,
) -> ValidationCheck:
    checked = failed = 0
    doomed: set[int] = set()
    worst = 1.0

    for position, item in enumerate(minutes.iter_grounded_items()):
        quote = getattr(item, "quote", None)
        if not quote:
            continue

        checked += 1
        item_id = _item_id(item, f"item_{position}")
        haystack = transcript.evidence_text(item.evidence_segment_ids)
        score = _partial_ratio(quote, haystack)
        worst = min(worst, score)

        if score < QUOTE_REJECT_THRESHOLD:
            failed += 1
            if strict:
                doomed.add(id(item))
                rejected.append(item_id)
            warnings.append(
                QualityWarning(
                    code=WarningCode.CONFLICTING_STATEMENTS,
                    message=(
                        f"Trích dẫn không tìm thấy trong transcript "
                        f"(độ khớp {score:.0%}): {quote[:60]}"
                    ),
                    affected_items=[item_id],
                    severity=Severity.HIGH,
                )
            )
        elif score < QUOTE_SUSPICIOUS_THRESHOLD:
            failed += 1
            item.confidence = Confidence.LOW
            downgraded.append(item_id)
            warnings.append(
                QualityWarning(
                    code=WarningCode.LOW_AUDIO_QUALITY,
                    message=f"Trích dẫn chỉ khớp {score:.0%} với transcript.",
                    affected_items=[item_id],
                    severity=Severity.LOW,
                )
            )

    if doomed:
        _filter_collection(minutes, doomed)

    return ValidationCheck(
        passed=failed == 0,
        checked=checked,
        failed=failed,
        detail=f"Độ khớp thấp nhất: {worst:.0%}" if checked else "Không có trích dẫn",
    )


# --------------------------------------------------------------------------- #
# Lớp 3 — Người nhận việc phải có thật
# --------------------------------------------------------------------------- #


def _check_assignees(
    minutes: StructuredMinutes,
    attendee_names: set[str],
    warnings: list[QualityWarning],
) -> ValidationCheck:
    """Chặn lỗi bịa người: "anh Nam bên DevOps" khi không có ai tên Nam."""
    checked = failed = 0

    for action in minutes.action_items:
        if action.assignee is None:
            continue
        checked += 1

        if action.assignee in attendee_names:
            continue

        best = max(
            (_partial_ratio(action.assignee, name) for name in attendee_names),
            default=0.0,
        )
        if best >= ASSIGNEE_MATCH_THRESHOLD:
            continue

        failed += 1
        original = action.assignee
        action.assignee = None
        action.assignee_person_id = None
        action.needs_review = True
        warnings.append(
            QualityWarning(
                code=WarningCode.HALLUCINATED_ASSIGNEE,
                message=(
                    f'"{original}" không có trong danh sách người tham dự. '
                    "Đã xoá thay vì đoán người thay thế."
                ),
                affected_items=[action.id],
                severity=Severity.HIGH,
            )
        )

    return ValidationCheck(
        passed=failed == 0,
        checked=checked,
        failed=failed,
        detail="Assignee phải nằm trong danh sách người tham dự",
    )


# --------------------------------------------------------------------------- #
# Lớp 4 — Ngày phải hợp lý và có nguồn
# --------------------------------------------------------------------------- #


def _check_dates(
    minutes: StructuredMinutes, warnings: list[QualityWarning]
) -> ValidationCheck:
    """Có ``due_date`` mà không có ``due_raw`` là dấu hiệu bịa ngày rõ ràng."""
    meeting_date = minutes.meta.date
    checked = failed = 0

    for action in minutes.action_items:
        if action.due_date is None:
            continue
        checked += 1

        problem: str | None = None
        if not action.due_raw:
            problem = "có due_date nhưng không ai nêu mốc thời gian nào"
        elif action.due_date < meeting_date:
            problem = f"hạn {action.due_date.isoformat()} nằm trước ngày họp"
        elif (action.due_date - meeting_date).days > MAX_HORIZON_DAYS:
            problem = f"hạn {action.due_date.isoformat()} xa hơn một năm"

        if problem is None:
            continue

        failed += 1
        action.due_date = None
        action.needs_review = True
        warnings.append(
            QualityWarning(
                code=WarningCode.FABRICATED_DUE_DATE,
                message=f"Đã xoá hạn của công việc: {problem}.",
                affected_items=[action.id],
                severity=Severity.MEDIUM,
            )
        )

    return ValidationCheck(
        passed=failed == 0,
        checked=checked,
        failed=failed,
        detail="due_date phải có due_raw làm nguồn và nằm trong tương lai hợp lý",
    )


# --------------------------------------------------------------------------- #
# Lớp 5 — Toàn vẹn quan hệ thay thế
# --------------------------------------------------------------------------- #


def _check_supersession(
    minutes: StructuredMinutes, warnings: list[QualityWarning]
) -> ValidationCheck:
    """Bắt lỗi map-reduce ngây thơ: hai quyết định mâu thuẫn cùng có hiệu lực."""
    by_id = {d.id: d for d in minutes.decisions}
    checked = failed = 0

    for decision in minutes.decisions:
        if decision.supersedes:
            checked += 1
            target = by_id.get(decision.supersedes)
            if target is None:
                failed += 1
                warnings.append(
                    QualityWarning(
                        code=WarningCode.CONFLICTING_STATEMENTS,
                        message=f"Quyết định {decision.id} thay thế một ID không tồn tại.",
                        affected_items=[decision.id],
                        severity=Severity.HIGH,
                    )
                )
                continue

            if target.status is not DecisionStatus.REJECTED:
                failed += 1
                warnings.append(
                    QualityWarning(
                        code=WarningCode.CONFLICTING_STATEMENTS,
                        message=(
                            f"{target.id} bị {decision.id} thay thế nhưng vẫn ở "
                            "trạng thái còn hiệu lực."
                        ),
                        affected_items=[decision.id, target.id],
                        severity=Severity.HIGH,
                    )
                )

            if (
                target.timestamp_ms is not None
                and decision.timestamp_ms is not None
                and target.timestamp_ms >= decision.timestamp_ms
            ):
                failed += 1
                warnings.append(
                    QualityWarning(
                        code=WarningCode.AMBIGUOUS_SUPERSESSION,
                        message=(
                            f"{decision.id} thay thế {target.id} nhưng lại xảy ra "
                            "trước nó — sai chiều thời gian."
                        ),
                        affected_items=[decision.id, target.id],
                        severity=Severity.HIGH,
                    )
                )

        if decision.status is DecisionStatus.REJECTED and not decision.superseded_by:
            checked += 1
            failed += 1
            warnings.append(
                QualityWarning(
                    code=WarningCode.CONFLICTING_STATEMENTS,
                    message=f"{decision.id} bị loại nhưng không rõ vì quyết định nào.",
                    affected_items=[decision.id],
                    severity=Severity.MEDIUM,
                )
            )

    return ValidationCheck(
        passed=failed == 0,
        checked=checked,
        failed=failed,
        detail="Quan hệ thay thế phải nhất quán hai chiều và đúng chiều thời gian",
    )


# --------------------------------------------------------------------------- #
# Lớp 6 — Con số phải có trong transcript
# --------------------------------------------------------------------------- #


def _check_numbers(
    minutes: StructuredMinutes,
    transcript: Transcript,
    downgraded: list[str],
    warnings: list[QualityWarning],
) -> ValidationCheck:
    """Bắt lỗi "làm tròn cho đẹp": transcript nói 2.3% mà biên bản ghi 2%."""
    source_numbers = _extract_numbers(transcript.full_text)
    checked = failed = 0

    for metric in minutes.metrics:
        for number in _extract_numbers(metric.value_raw):
            checked += 1
            if number in source_numbers:
                continue
            failed += 1
            metric.confidence = Confidence.LOW
            downgraded.append(metric.id)
            warnings.append(
                QualityWarning(
                    code=WarningCode.UNGROUNDED_NUMBER,
                    message=(
                        f'Con số {number} trong chỉ số "{metric.label}" không '
                        "xuất hiện trong transcript."
                    ),
                    affected_items=[metric.id],
                    severity=Severity.MEDIUM,
                )
            )

    return ValidationCheck(
        passed=failed == 0,
        checked=checked,
        failed=failed,
        detail="Mọi con số trong chỉ số phải xuất hiện nguyên vẹn trong transcript",
    )


# --------------------------------------------------------------------------- #
# Lớp 7 — Văn xuôi không được thêm thực thể lạ
# --------------------------------------------------------------------------- #


def _capitalised_tokens_mid_sentence(parts: list[str]) -> set[str]:
    """Lấy các từ viết hoa KHÔNG đứng đầu câu, xét từng đoạn văn riêng biệt.

    Ba cạm bẫy được xử lý ở đây:

    1. Không dùng lớp ký tự kiểu ``[A-ZÀ-Ỹ]``. Dải Unicode ``À-Ỹ`` bao gồm cả
       chữ thường tiếng Việt (``đ``, ``ố``, ``ề``...), nên biểu thức đó khớp
       nhầm "điểm" và "đối" thành tên riêng. Dùng ``str.isupper()`` của Python
       vì nó hiểu Unicode đúng.
    2. Tiếng Việt viết hoa đầu câu như mọi ngôn ngữ Latin, nên "Phân công
       và..." sẽ cho "Phân" là tên riêng nếu không loại từ đầu câu. Chỉ xét
       các từ nằm GIỮA câu — đó mới thực sự là tín hiệu của danh từ riêng.
    3. Phải xét TỪNG đoạn riêng, không nối chung rồi mới tách câu. Tiêu đề
       chương và dòng tl;dr thường không có dấu chấm cuối, nên khi nối lại
       chúng dính vào câu trước và từ mở đầu của chúng mất vị trí đầu câu.
    """
    found: set[str] = set()

    for part in parts:
        for sentence in re.split(r"[.!?;:\n]+", part):
            tokens = re.findall(r"\w+", sentence.strip(), flags=re.UNICODE)
            for token in tokens[1:]:
                if len(token) >= 3 and token[0].isupper() and not token.isupper():
                    found.add(token)

    return found


def _check_prose_entities(
    minutes: StructuredMinutes,
    attendee_names: set[str],
    transcript: Transcript,
    warnings: list[QualityWarning],
) -> ValidationCheck:
    """Pha COMPOSE chỉ được diễn đạt lại, không được thêm người hay tổ chức mới."""
    prose_parts = [
        *minutes.executive_summary.tldr,
        *minutes.executive_summary.paragraphs,
        *[c.summary for c in minutes.chapters],
        *[c.title for c in minutes.chapters],
    ]

    known = {n.lower() for n in attendee_names}
    known |= {g.lower() for g in transcript.meta.glossary}
    known |= {a.lower() for a in _PROSE_ALLOWLIST}
    transcript_lower = transcript.full_text.lower()

    unknown = {
        token
        for token in _capitalised_tokens_mid_sentence(prose_parts)
        if token.lower() not in known and token.lower() not in transcript_lower
    }

    if unknown:
        warnings.append(
            QualityWarning(
                code=WarningCode.UNKNOWN_ENTITY_IN_PROSE,
                message=(
                    "Văn xuôi nhắc tới thực thể không có trong transcript: "
                    + ", ".join(sorted(unknown)[:5])
                ),
                affected_items=[],
                severity=Severity.MEDIUM,
            )
        )

    return ValidationCheck(
        passed=not unknown,
        checked=len(prose_parts),
        failed=len(unknown),
        detail="Tên riêng giữa câu phải truy được về transcript",
    )


# --------------------------------------------------------------------------- #
# Lớp 8 — Chất lượng của chính bằng chứng
# --------------------------------------------------------------------------- #


def _check_evidence_quality(
    minutes: StructuredMinutes,
    segment_index: dict[str, object],
    downgraded: list[str],
    warnings: list[QualityWarning],
) -> ValidationCheck:
    """Không cho phép cam kết chỉ dựa trên segment nhiễu hoặc nói chồng.

    Một quyết định mà toàn bộ bằng chứng đều nằm ở đoạn âm thanh kém thì
    không thể tin được, dù LLM có tự tin đến đâu.
    """
    checked = failed = 0

    for item in (*minutes.decisions, *minutes.action_items):
        checked += 1
        segments = [segment_index[e] for e in item.evidence_segment_ids
                    if e in segment_index]
        if not segments:
            continue

        if all(not getattr(s, "is_trustworthy", True) for s in segments):
            failed += 1
            item.confidence = Confidence.LOW
            downgraded.append(item.id)
            if hasattr(item, "needs_review"):
                item.needs_review = True
            warnings.append(
                QualityWarning(
                    code=WarningCode.LOW_AUDIO_QUALITY,
                    message=(
                        "Toàn bộ bằng chứng của mục này nằm ở đoạn âm thanh kém "
                        "hoặc có người nói chồng."
                    ),
                    affected_items=[item.id],
                    severity=Severity.MEDIUM,
                )
            )

    return ValidationCheck(
        passed=failed == 0,
        checked=checked,
        failed=failed,
        detail="Quyết định và công việc không được chỉ dựa trên segment kém tin cậy",
    )
