"""Kết xuất ``StructuredMinutes`` thành biên bản Markdown.

Nguyên tắc thiết kế
-------------------
Biên bản là **view** được render từ dữ liệu, không phải bản thân dữ liệu.
Module này thuần tuý định dạng: nó không gọi LLM, không suy diễn, không thêm
bất kỳ thông tin nào không có sẵn trong ``StructuredMinutes``. Đổi cách trình
bày không tốn một request nào.

Ba lựa chọn trình bày đáng chú ý
--------------------------------
1. **Quyết định đã bị thay thế vẫn được ghi lại**, trong mục lịch sử riêng.
   Người đọc cần biết "ban đầu chốt 26/07, sau đổi sang 28/07" — chỉ hiển thị
   kết quả cuối làm mất mạch lý do.
2. **Chỗ thiếu thông tin được ghi rõ là thiếu**: "Chưa phân công", "Chưa xác
   định". Ô trống trong bảng khiến người đọc tưởng là sót định dạng.
3. **Cảnh báo chất lượng nằm ngay trong biên bản**, không giấu xuống phụ lục.
   Một biên bản dám nói "mục này cần kiểm tra lại" đáng tin hơn một biên bản
   trình bày mọi thứ với cùng một vẻ chắc chắn.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from schemas.common import (
    ActionStatus,
    CommitmentStrength,
    Confidence,
    ConsensusLevel,
    DecisionStatus,
    Priority,
    RiskStatus,
    Severity,
)
from schemas.minutes import ActionItem, Decision, StructuredMinutes

__all__ = ["render_markdown", "write_markdown"]

WEEKDAY_VI: dict[int, str] = {
    0: "Thứ Hai",
    1: "Thứ Ba",
    2: "Thứ Tư",
    3: "Thứ Năm",
    4: "Thứ Sáu",
    5: "Thứ Bảy",
    6: "Chủ Nhật",
}

COMMITMENT_VI: dict[CommitmentStrength, str] = {
    CommitmentStrength.FIRM: "Cam kết chắc chắn",
    CommitmentStrength.TENTATIVE: "Dự kiến",
    CommitmentStrength.PROPOSED: "Mới đề xuất",
}

PRIORITY_VI: dict[Priority, str] = {
    Priority.HIGH: "Cao",
    Priority.MEDIUM: "Trung bình",
    Priority.LOW: "Thấp",
    Priority.UNSPECIFIED: "Chưa xác định",
}

SEVERITY_VI: dict[Severity, str] = {
    Severity.HIGH: "Cao",
    Severity.MEDIUM: "Trung bình",
    Severity.LOW: "Thấp",
    Severity.UNSPECIFIED: "Chưa xác định",
}

RISK_STATUS_VI: dict[RiskStatus, str] = {
    RiskStatus.OPEN: "Chưa xử lý",
    RiskStatus.MITIGATED: "Đã có hướng xử lý",
    RiskStatus.ACCEPTED: "Chấp nhận rủi ro",
    RiskStatus.CLOSED: "Đã đóng",
}

ACTION_STATUS_VI: dict[ActionStatus, str] = {
    ActionStatus.OPEN: "Chưa bắt đầu",
    ActionStatus.IN_PROGRESS: "Đang làm",
    ActionStatus.DONE: "Hoàn thành",
    ActionStatus.CANCELLED: "Đã huỷ",
    ActionStatus.CARRIED_OVER: "Chuyển tiếp",
}

CONSENSUS_VI: dict[ConsensusLevel, str] = {
    ConsensusLevel.ALIGNED: "Thống nhất",
    ConsensusLevel.DEBATED: "Có tranh luận",
    ConsensusLevel.UNRESOLVED: "Chưa ngã ngũ",
    ConsensusLevel.UNSPECIFIED: "",
}

CONFIDENCE_VI: dict[Confidence, str] = {
    Confidence.HIGH: "Cao",
    Confidence.MEDIUM: "Trung bình",
    Confidence.LOW: "Thấp",
}

SEVERITY_ORDER: dict[Severity, int] = {
    Severity.HIGH: 0,
    Severity.MEDIUM: 1,
    Severity.LOW: 2,
    Severity.UNSPECIFIED: 3,
}

NOT_ASSIGNED = "_Chưa phân công_"
NOT_SPECIFIED = "_Chưa xác định_"


def render_markdown(
    minutes: StructuredMinutes,
    *,
    include_history: bool = True,
    include_quality: bool = True,
    include_evidence: bool = True,
) -> str:
    """Dựng nội dung Markdown của biên bản.

    Args:
        minutes: Biên bản đã qua kiểm chứng.
        include_history: Có ghi lại các quyết định đã bị thay thế không.
        include_quality: Có kèm mục cảnh báo và kiểm chứng không.
        include_evidence: Có ghi mã segment làm dẫn chứng không. Bật khi biên
            bản còn ở giai đoạn review, tắt khi gửi ra ngoài.

    Returns:
        Chuỗi Markdown hoàn chỉnh.
    """
    blocks: list[str] = [
        _header(minutes),
        _attendees(minutes),
        _executive_summary(minutes),
        _decisions(minutes, include_history=include_history),
        _action_items(minutes, include_evidence=include_evidence),
        _metrics(minutes),
        _risks(minutes),
        _open_questions(minutes),
        _next_meeting(minutes),
        _chapters(minutes),
    ]

    if include_quality:
        blocks.append(_quality(minutes))

    blocks.append(_footer(minutes))

    return "\n\n".join(block for block in blocks if block).rstrip() + "\n"


def write_markdown(
    minutes: StructuredMinutes,
    path: Path | str,
    **options: bool,
) -> Path:
    """Ghi biên bản ra file ``.md``.

    Luôn ghi bằng UTF-8 tường minh: mã trang mặc định trên Windows không biểu
    diễn được tiếng Việt và sẽ làm hỏng file.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_markdown(minutes, **options), encoding="utf-8")
    return destination


# --------------------------------------------------------------------------- #
# Tiện ích định dạng
# --------------------------------------------------------------------------- #


def _escape(text: str) -> str:
    """Vô hiệu hoá ký tự có nghĩa trong bảng Markdown."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _format_date(value: dt.date | None) -> str:
    if value is None:
        return NOT_SPECIFIED
    return f"{value.strftime('%d/%m/%Y')} ({WEEKDAY_VI[value.weekday()]})"


def _format_date_short(value: dt.date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else NOT_SPECIFIED


def _format_timestamp(milliseconds: int | None) -> str:
    if milliseconds is None:
        return ""
    seconds = milliseconds // 1000
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _evidence_note(item: object, enabled: bool) -> str:
    if not enabled:
        return ""
    ids = getattr(item, "evidence_segment_ids", []) or []
    return f"`{', '.join(ids[:4])}`" if ids else ""


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return ""
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Các mục của biên bản
# --------------------------------------------------------------------------- #


def _header(minutes: StructuredMinutes) -> str:
    meta = minutes.meta
    lines = [
        f"# BIÊN BẢN CUỘC HỌP",
        "",
        f"## {meta.meeting_title}",
        "",
        f"- **Ngày họp:** {_format_date(meta.date)}",
        f"- **Thời lượng:** {meta.duration_minutes} phút",
        f"- **Loại cuộc họp:** {meta.meeting_type.value}",
        f"- **Số người tham dự:** {len(meta.attendees)}",
    ]

    if minutes.quality_report.needs_human_review:
        lines += [
            "",
            "> **Biên bản này do hệ thống tự động lập và cần người rà soát "
            "trước khi ban hành.** Các mục cần chú ý được đánh dấu bên dưới.",
        ]

    return "\n".join(lines)


def _attendees(minutes: StructuredMinutes) -> str:
    if not minutes.meta.attendees:
        return ""

    rows = [
        [
            _escape(a.display_name),
            _escape(a.role or "—"),
            f"{a.talk_time_pct:.0f}%" if a.talk_time_pct else "—",
        ]
        for a in sorted(
            minutes.meta.attendees, key=lambda x: x.talk_time_pct, reverse=True
        )
    ]

    return "## 1. Thành phần tham dự\n\n" + _table(
        ["Họ tên", "Vai trò", "Tỉ lệ phát biểu"], rows
    )


def _executive_summary(minutes: StructuredMinutes) -> str:
    summary = minutes.executive_summary
    lines = ["## 2. Tóm tắt nhanh", ""]
    lines += [f"- {line}" for line in summary.tldr]

    if summary.paragraphs:
        lines.append("")
        lines += [f"{paragraph}\n" for paragraph in summary.paragraphs]

    return "\n".join(lines).rstrip()


def _decisions(minutes: StructuredMinutes, *, include_history: bool) -> str:
    active = minutes.active_decisions
    lines = ["## 3. Các quyết định", ""]

    if not active:
        lines.append(
            "_Cuộc họp không đi đến quyết định chính thức nào._"
        )
    else:
        for order, decision in enumerate(active, start=1):
            lines += _decision_block(order, decision)

    if include_history:
        history = minutes.superseded_decisions
        if history:
            lines += [
                "",
                "### Các quyết định đã được thay đổi trong cuộc họp",
                "",
                "_Ghi lại để theo dõi diễn biến; các mục dưới đây **không còn "
                "hiệu lực**._",
                "",
            ]
            for decision in history:
                replacement = decision.superseded_by or "—"
                lines.append(
                    f"- ~~{_escape(decision.statement)}~~ "
                    f"(thay bằng quyết định `{replacement}` "
                    f"lúc {_format_timestamp(decision.timestamp_ms)})"
                )

    return "\n".join(lines)


def _decision_block(order: int, decision: Decision) -> list[str]:
    lines = [f"**{order}. {_escape(decision.statement)}**", ""]

    details: list[str] = []
    if decision.target_date:
        details.append(f"Mốc thời gian: **{_format_date_short(decision.target_date)}**")
    if decision.decided_by:
        details.append(f"Người kết luận: {_escape(decision.decided_by)}")
    if decision.timestamp_ms is not None:
        details.append(f"Thời điểm: {_format_timestamp(decision.timestamp_ms)}")
    if decision.status is not DecisionStatus.DECIDED:
        details.append(f"Trạng thái: {decision.status.value}")

    if details:
        lines += [f"- {item}" for item in details]

    if decision.rationale:
        lines.append(f"- Lý do: {_escape(decision.rationale)}")

    if decision.alternatives_considered:
        lines.append("- Phương án đã cân nhắc:")
        lines += [
            f"    - {_escape(option)}" for option in decision.alternatives_considered
        ]

    if decision.objections:
        lines.append("- Ý kiến phản đối được ghi nhận:")
        for objection in decision.objections:
            who = f"{_escape(objection.by)}: " if objection.by else ""
            lines.append(f"    - {who}{_escape(objection.reason)}")

    if decision.quote:
        lines += ["", f"  > {_escape(decision.quote)}"]

    lines.append("")
    return lines


def _action_items(minutes: StructuredMinutes, *, include_evidence: bool) -> str:
    if not minutes.action_items:
        return "## 4. Công việc được giao\n\n_Không có công việc nào được giao._"

    headers = ["#", "Nội dung công việc", "Người phụ trách", "Hạn hoàn thành",
               "Mức cam kết", "Ưu tiên"]
    if include_evidence:
        headers.append("Dẫn chứng")

    rows: list[list[str]] = []
    for action in _sorted_actions(minutes.action_items):
        flag = " ⚠️" if action.needs_review else ""
        row = [
            f"`{action.id}`",
            _escape(action.task) + flag,
            _escape(action.assignee) if action.assignee else NOT_ASSIGNED,
            _due_cell(action),
            COMMITMENT_VI[action.commitment_strength],
            PRIORITY_VI[action.priority],
        ]
        if include_evidence:
            row.append(_evidence_note(action, True))
        rows.append(row)

    lines = ["## 4. Công việc được giao", "", _table(headers, rows)]

    flagged = [a for a in minutes.action_items if a.needs_review]
    if flagged:
        lines += [
            "",
            f"⚠️ **{len(flagged)} công việc cần rà soát lại** trước khi giao "
            "chính thức (thiếu người phụ trách, thiếu hạn, hoặc mức cam kết "
            "chưa rõ ràng).",
        ]

    unassigned = minutes.unassigned_actions
    if unassigned:
        lines += [
            "",
            "**Chưa có người phụ trách:** "
            + ", ".join(f"`{a.id}`" for a in unassigned),
        ]

    return "\n".join(lines)


def _sorted_actions(actions: list[ActionItem]) -> list[ActionItem]:
    """Sắp xếp: có hạn lên trước theo thứ tự thời gian, chưa có hạn xuống cuối.

    Người đọc quan tâm nhất tới việc sắp đến hạn, nên chúng phải nằm trên đầu.
    """
    return sorted(
        actions,
        key=lambda a: (a.due_date is None, a.due_date or dt.date.max, a.id),
    )


def _due_cell(action: ActionItem) -> str:
    if action.due_date:
        return f"**{_format_date_short(action.due_date)}**"
    if action.due_raw:
        # Nêu nguyên văn cách nói trong cuộc họp thay vì bỏ trống: "cuối tháng"
        # là thông tin thật, chỉ chưa đủ cụ thể để quy về một ngày.
        return f"_{_escape(action.due_raw)}_ (chưa rõ ngày)"
    return NOT_SPECIFIED


def _metrics(minutes: StructuredMinutes) -> str:
    if not minutes.metrics:
        return ""

    rows = [
        [
            _escape(metric.label),
            f"**{_escape(metric.value_raw)}**",
            _escape(metric.period or "—"),
            _escape(metric.trend or "—"),
        ]
        for metric in minutes.metrics
    ]

    return "## 5. Số liệu được nêu\n\n" + _table(
        ["Chỉ số", "Giá trị", "Kỳ", "Xu hướng"], rows
    )


def _risks(minutes: StructuredMinutes) -> str:
    if not minutes.risks:
        return ""

    ordered = sorted(
        minutes.risks, key=lambda r: SEVERITY_ORDER.get(r.severity, 9)
    )
    rows = [
        [
            _escape(risk.risk),
            SEVERITY_VI[risk.severity],
            _escape(risk.raised_by or "—"),
            _escape(risk.mitigation or "—"),
            RISK_STATUS_VI[risk.status],
        ]
        for risk in ordered
    ]

    return "## 6. Rủi ro và vướng mắc\n\n" + _table(
        ["Nội dung", "Mức độ", "Người nêu", "Hướng xử lý", "Trạng thái"], rows
    )


def _open_questions(minutes: StructuredMinutes) -> str:
    if not minutes.open_questions:
        return ""

    lines = ["## 7. Vấn đề còn để ngỏ", ""]
    for question in minutes.open_questions:
        parts = [f"- {_escape(question.question)}"]
        extra: list[str] = []
        if question.asked_by:
            extra.append(f"nêu bởi {_escape(question.asked_by)}")
        if question.deferred_to:
            extra.append(f"hoãn sang {_escape(question.deferred_to)}")
        if extra:
            parts.append(f" _({'; '.join(extra)})_")
        lines.append("".join(parts))

    return "\n".join(lines)


def _next_meeting(minutes: StructuredMinutes) -> str:
    meeting = minutes.next_meeting
    if meeting is None:
        return ""

    lines = ["## 8. Cuộc họp tiếp theo", ""]

    if meeting.when_date:
        lines.append(f"- **Thời gian:** {_format_date(meeting.when_date)}")
    elif meeting.when_raw:
        lines.append(
            f"- **Thời gian:** _{_escape(meeting.when_raw)}_ (chưa chốt ngày cụ thể)"
        )
    else:
        lines.append(f"- **Thời gian:** {NOT_SPECIFIED}")

    if meeting.proposed_agenda:
        lines += ["- **Nội dung dự kiến:**"]
        lines += [f"    - {_escape(item)}" for item in meeting.proposed_agenda]

    return "\n".join(lines)


def _chapters(minutes: StructuredMinutes) -> str:
    if not minutes.chapters:
        return ""

    lines = ["## 9. Diễn biến theo chủ đề", ""]
    for chapter in minutes.chapters:
        consensus = CONSENSUS_VI.get(chapter.consensus_level, "")
        badge = f" — _{consensus}_" if consensus else ""
        lines += [
            f"### {_format_timestamp(chapter.start_ms)}–"
            f"{_format_timestamp(chapter.end_ms)} · {_escape(chapter.title)}{badge}",
            "",
            chapter.summary,
            "",
        ]

    return "\n".join(lines).rstrip()


def _quality(minutes: StructuredMinutes) -> str:
    report = minutes.quality_report
    validation = minutes.validation

    lines = ["## 10. Ghi chú về độ tin cậy", ""]
    lines.append(
        f"- **Mức tin cậy tổng thể:** "
        f"{CONFIDENCE_VI.get(report.overall_confidence, '—')}"
    )

    if validation:
        lines.append(f"- **Điểm truy vết dẫn chứng:** {validation.grounding_score:.2f}")
        failed = [name for name, check in validation.checks.items() if not check.passed]
        if failed:
            lines.append(f"- **Kiểm tra chưa đạt:** {', '.join(failed)}")
        else:
            lines.append(
                f"- **Kiểm tra tự động:** đạt toàn bộ "
                f"{len(validation.checks)}/{len(validation.checks)} lớp"
            )

    if report.warnings:
        lines += ["", "### Các điểm cần rà soát", ""]
        rows = [
            [
                SEVERITY_VI[warning.severity],
                f"`{warning.code.value}`",
                _escape(warning.message),
                ", ".join(f"`{i}`" for i in warning.affected_items[:4]) or "—",
            ]
            for warning in sorted(
                report.warnings, key=lambda w: SEVERITY_ORDER.get(w.severity, 9)
            )
        ]
        lines.append(_table(["Mức độ", "Mã", "Nội dung", "Liên quan"], rows))

    return "\n".join(lines)


def _footer(minutes: StructuredMinutes) -> str:
    pipeline = minutes.pipeline
    generated = minutes.generated_at or dt.datetime.now(dt.timezone.utc)

    parts = [
        "---",
        "",
        f"_Biên bản được lập tự động lúc "
        f"{generated.astimezone().strftime('%H:%M %d/%m/%Y')}._",
    ]

    details: list[str] = []
    if pipeline.asr_provider:
        details.append(f"phiên âm: `{pipeline.asr_provider}`")
    if pipeline.llm_provider:
        details.append(f"phân tích: `{pipeline.llm_provider}`")
    if pipeline.total_llm_requests:
        details.append(f"{pipeline.total_llm_requests} lượt gọi mô hình")

    if details:
        parts.append(f"_Nguồn xử lý: {' · '.join(details)}._")

    parts.append(
        f"_Mã biên bản: `{minutes.minutes_id}` · phiên bản {minutes.version}._"
    )

    return "\n".join(parts)
