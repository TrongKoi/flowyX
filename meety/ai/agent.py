"""Meety Intelligence Agent — chuỗi prompt chuyên biệt cho biên bản cuộc họp.

Quan hệ với ``pipeline/``
-------------------------
Pipeline sáu pha hiện có (``s2_diarize`` → ``s7_validate``) vẫn là đường chạy
chính thức: nó có cache, quota, artifact từng pha, và 419 phép kiểm bao quanh.
Agent này **không thay thế** nó.

Agent tồn tại để trả lời một câu hỏi khác: *"nếu chỉ có một transcript và một
mô hình bất kỳ, ta rút ra được gì?"* — dùng cho ba việc:

* chạy đối soát giữa mô hình cục bộ và API (``ConsensusEngine``),
* làm chuẩn đánh giá khi thử mô hình mới,
* làm đường chạy gọn cho bản on-prem không cần toàn bộ pipeline.

Bốn mắt xích, không phải một prompt to
--------------------------------------
Kinh nghiệm rút ra từ chính dự án này: gộp mọi việc vào một prompt là cách
nhanh nhất để mô hình bịa. Chuỗi bốn bước, mỗi bước một việc:

1. ``distill``    — nén transcript thành các mệnh đề có mốc thời gian.
2. ``decisions``  — chỉ tìm quyết định, kèm câu nói gốc.
3. ``actions``    — chỉ tìm cam kết và người nhận.
4. ``score``      — chấm độ tin cậy, **chạy bằng Python**, không gọi mô hình.

Bước 4 cố ý không dùng LLM. Hỏi mô hình "anh có chắc không" là hỏi sai đối
tượng: nó sẽ trả lời theo giọng điệu của câu hỏi. Độ tin cậy phải tính từ
những thứ đếm được — dẫn chứng có tồn tại không, người nhận việc có trong danh
sách tham dự không, câu trích có khớp transcript không.

Ràng buộc chống bịa
-------------------
Mọi lược đồ đều bắt buộc ``evidence_segment_ids``. Mệnh đề nào không trỏ được
về đoạn thoại có thật sẽ bị ``_prune_ungrounded`` loại bỏ *sau khi* mô hình
trả lời. Đây là chốt chặn cuối: prompt có thể bị lờ đi, kiểm tra bằng Python
thì không.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import re
from typing import Any, Iterable, Sequence

from pydantic import BaseModel, Field

from providers.base import LLMProvider, LLMResponse, ProviderError

logger = logging.getLogger(__name__)

__all__ = [
    "MeetingAgent",
    "AgentResult",
    "DistilledPoints",
    "ExtractedDecisions",
    "ExtractedActions",
]


# ===========================================================================
#  Lược đồ đầu ra — Structured Output
# ===========================================================================

class DistilledPoint(BaseModel):
    """Một mệnh đề đã nén, giữ nguyên mốc dẫn chứng."""
    text: str = Field(description="Nội dung cô đọng, một câu, tiếng Việt")
    topic: str = Field(description="Chủ đề ngắn gọn, 2-4 từ")
    evidence_segment_ids: list[str] = Field(
        description="Mã các đoạn thoại làm căn cứ, lấy nguyên văn từ transcript")


class DistilledPoints(BaseModel):
    points: list[DistilledPoint] = Field(default_factory=list)


class ExtractedDecision(BaseModel):
    statement: str = Field(description="Quyết định đã chốt, viết đầy đủ, tự đứng một mình được")
    decided_by: str | None = Field(default=None, description="Tên người chốt, null nếu không rõ")
    quote: str = Field(description="Câu nói gốc, trích nguyên văn từ transcript")
    evidence_segment_ids: list[str] = Field(default_factory=list)
    supersedes_hint: str | None = Field(
        default=None,
        description="Nếu quyết định này thay thế một quyết định trước đó, ghi nội dung cũ")


class ExtractedDecisions(BaseModel):
    decisions: list[ExtractedDecision] = Field(default_factory=list)


class ExtractedAction(BaseModel):
    task: str = Field(description="Việc cần làm, viết ở dạng động từ + đối tượng")
    assignee: str | None = Field(
        default=None,
        description="Tên người nhận việc. Để null nếu KHÔNG ai nhận rõ ràng. "
                    "Tuyệt đối không suy đoán.")
    quote: str = Field(description="Câu nói gốc, trích nguyên văn")
    due_raw: str | None = Field(default=None, description="Cụm chỉ thời hạn theo lời nói")
    commitment_strength: str = Field(
        default="tentative",
        description="firm nếu người nói cam kết dứt khoát; tentative nếu mới ở mức dự kiến")
    evidence_segment_ids: list[str] = Field(default_factory=list)


class ExtractedActions(BaseModel):
    actions: list[ExtractedAction] = Field(default_factory=list)


@dataclasses.dataclass(slots=True)
class AgentResult:
    """Kết quả một lượt chạy agent, kèm số liệu để đối soát."""
    points: list[dict]
    decisions: list[dict]
    actions: list[dict]
    confidence: dict[str, Any]
    provider: str
    llm_calls: int
    input_tokens: int
    output_tokens: int
    dropped: dict[str, int]           # số mục bị loại vì không có dẫn chứng

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


# ===========================================================================
#  Agent
# ===========================================================================

SYSTEM = (
    "Bạn là trợ lý ghi biên bản cuộc họp cho doanh nghiệp Việt Nam. "
    "Bạn chỉ được dùng thông tin có trong bản thoại được cung cấp. "
    "Nếu bản thoại không nói rõ điều gì, bạn để trống hoặc null — "
    "tuyệt đối không suy đoán, không bổ sung kiến thức bên ngoài. "
    "Mọi mệnh đề bạn đưa ra phải kèm mã đoạn thoại làm căn cứ. "
    "Chỉ trả về JSON đúng lược đồ, không kèm lời dẫn."
)


class MeetingAgent:
    """Chuỗi prompt bốn bước chạy trên bất kỳ ``LLMProvider`` nào."""

    def __init__(self, provider: LLMProvider, *, max_segments_per_call: int = 220) -> None:
        self.provider = provider
        # Cắt theo số đoạn chứ không theo ký tự: cắt giữa một lượt nói làm mất
        # ngữ cảnh của chính lượt đó, và đó là chỗ mô hình bắt đầu bịa.
        self.max_segments = max_segments_per_call

    # -- Đường chạy chính ------------------------------------------------- #

    def run(self, transcript: dict[str, Any]) -> AgentResult:
        segments = transcript.get("segments") or []
        if not segments:
            raise ProviderError("Bản thoại rỗng, không có gì để phân tích")

        valid_ids = {s["id"] for s in segments}
        speakers = _speaker_names(transcript)
        calls = tok_in = tok_out = 0

        points: list[dict] = []
        for chunk in _chunks(segments, self.max_segments):
            resp = self._ask(self._prompt_distill(chunk, speakers), DistilledPoints)
            calls += 1
            tok_in += resp.input_tokens
            tok_out += resp.output_tokens
            points.extend(resp.payload.get("points") or [])

        points, dropped_points = _prune_ungrounded(points, valid_ids)
        digest = _points_digest(points, segments)

        d_resp = self._ask(self._prompt_decisions(digest, speakers), ExtractedDecisions)
        a_resp = self._ask(self._prompt_actions(digest, speakers), ExtractedActions)
        calls += 2
        tok_in += d_resp.input_tokens + a_resp.input_tokens
        tok_out += d_resp.output_tokens + a_resp.output_tokens

        decisions, dropped_d = _prune_ungrounded(d_resp.payload.get("decisions") or [], valid_ids)
        actions, dropped_a = _prune_ungrounded(a_resp.payload.get("actions") or [], valid_ids)

        decisions = _verify_quotes(decisions, segments)
        actions = _verify_quotes(actions, segments)
        actions = _clean_assignees(actions, speakers)

        return AgentResult(
            points=points,
            decisions=decisions,
            actions=actions,
            confidence=score_confidence(decisions, actions, segments, speakers),
            provider=self.provider.key,
            llm_calls=calls,
            input_tokens=tok_in,
            output_tokens=tok_out,
            dropped={"points": dropped_points, "decisions": dropped_d, "actions": dropped_a},
        )

    def _ask(self, prompt: str, schema: type[BaseModel]) -> LLMResponse:
        return self.provider.generate_json(prompt, schema, system=SYSTEM, temperature=0.0)

    # -- Prompt ----------------------------------------------------------- #

    @staticmethod
    def _prompt_distill(segments: Sequence[dict], speakers: dict[str, str]) -> str:
        body = _render(segments, speakers)
        return (
            "Dưới đây là một phần bản thoại cuộc họp. Hãy nén lại thành các mệnh đề "
            "cô đọng, mỗi mệnh đề một ý.\n\n"
            "Quy tắc:\n"
            "- Bỏ hết lời chào, câu đệm, đoạn lạc đề.\n"
            "- Giữ nguyên con số và tên riêng đúng như trong thoại.\n"
            "- Mỗi mệnh đề phải kèm mã đoạn (ví dụ s_0007) lấy từ bản thoại.\n"
            "- Không thêm bất cứ điều gì bản thoại không nói.\n\n"
            f"BẢN THOẠI:\n{body}"
        )

    @staticmethod
    def _prompt_decisions(digest: str, speakers: dict[str, str]) -> str:
        names = ", ".join(sorted(set(speakers.values()))) or "(chưa rõ)"
        return (
            "Từ các mệnh đề dưới đây, hãy tìm CÁC QUYẾT ĐỊNH ĐÃ CHỐT.\n\n"
            "Quyết định là điều nhóm đã thống nhất và sẽ hành động theo. "
            "KHÔNG phải quyết định: ý kiến cá nhân, đề xuất chưa ai đồng ý, "
            "câu hỏi bỏ ngỏ, việc hoãn lại để bàn sau.\n\n"
            "Quy tắc:\n"
            "- `quote` phải trích NGUYÊN VĂN một câu có trong bản thoại.\n"
            "- `decided_by` chỉ điền khi rõ ai chốt; không rõ thì null.\n"
            "- Nếu một quyết định thay thế quyết định trước đó trong cùng cuộc họp, "
            "ghi nội dung cũ vào `supersedes_hint`.\n"
            f"- Người tham dự: {names}\n\n"
            f"CÁC MỆNH ĐỀ:\n{digest}"
        )

    @staticmethod
    def _prompt_actions(digest: str, speakers: dict[str, str]) -> str:
        names = ", ".join(sorted(set(speakers.values()))) or "(chưa rõ)"
        return (
            "Từ các mệnh đề dưới đây, hãy tìm CÁC CÔNG VIỆC CẦN LÀM SAU CUỘC HỌP.\n\n"
            "Quy tắc về người nhận việc — đây là phần quan trọng nhất:\n"
            "- Chỉ điền `assignee` khi bản thoại nói RÕ ai nhận "
            "(người đó tự nhận, hoặc được giao đích danh và không phản đối).\n"
            "- Việc được nêu ra mà KHÔNG ai nhận thì để `assignee` là null. "
            "Để trống là câu trả lời đúng, không phải thiếu sót.\n"
            "- Tuyệt đối không suy đoán theo kiểu 'việc này thuộc chuyên môn của X'.\n"
            "- `assignee` phải là một trong những người có mặt, viết đúng như trong thoại.\n\n"
            "Quy tắc về mức cam kết:\n"
            "- `firm`: người nói cam kết dứt khoát ('em làm', 'anh nhận', 'sẽ xong trước thứ 6').\n"
            "- `tentative`: mới ở mức dự kiến ('để em xem lại', 'chắc là', 'cố gắng').\n\n"
            f"Người tham dự: {names}\n\n"
            f"CÁC MỆNH ĐỀ:\n{digest}"
        )


# ===========================================================================
#  Chốt chặn bằng Python — chạy SAU khi mô hình trả lời
# ===========================================================================

def _prune_ungrounded(items: Iterable[dict], valid_ids: set[str]) -> tuple[list[dict], int]:
    """Loại mọi mục không trỏ được về đoạn thoại có thật.

    Prompt có thể bị lờ đi; phép kiểm này thì không. Một mệnh đề dẫn chứng tới
    ``s_9999`` trong khi transcript chỉ có tới ``s_0042`` là dấu hiệu mô hình
    đang bịa — và mệnh đề đó bị bỏ, không được đưa vào biên bản.
    """
    kept, dropped = [], 0
    for item in items:
        ids = [i for i in (item.get("evidence_segment_ids") or []) if i in valid_ids]
        if not ids:
            dropped += 1
            continue
        item["evidence_segment_ids"] = ids
        kept.append(item)
    return kept, dropped


def _verify_quotes(items: list[dict], segments: Sequence[dict]) -> list[dict]:
    """Đánh dấu câu trích không khớp bản thoại.

    Không xoá mục — câu trích lệch vài chữ vẫn có thể là mệnh đề đúng. Nhưng
    phải gắn cờ để tầng trên hạ điểm tin cậy và người đọc biết mà rà lại.
    """
    haystack = " ".join(s.get("text", "") for s in segments)
    flat = _flatten(haystack)
    for item in items:
        q = _flatten(item.get("quote") or "")
        item["quote_verified"] = bool(q) and q in flat
    return items


def _clean_assignees(actions: list[dict], speakers: dict[str, str]) -> list[dict]:
    """Xoá tên người nhận không có trong danh sách tham dự.

    Gán việc cho một cái tên không dự họp gần như luôn là mô hình bịa. Thà để
    trống và bật cảnh báo còn hơn — gán sai người cho một cam kết là loại lỗi
    nguy hiểm nhất của sản phẩm này.
    """
    known = {_flatten(n) for n in speakers.values() if n}
    known_last = {_flatten(n).split()[-1] for n in speakers.values() if n}
    for a in actions:
        who = _flatten(a.get("assignee") or "")
        if not who:
            a["assignee"] = None
            continue
        if who in known or (who.split() and who.split()[-1] in known_last):
            continue
        logger.info("Bỏ người nhận việc không có trong danh sách tham dự: %r", a.get("assignee"))
        a["assignee"] = None
        a["assignee_rejected"] = True
    return actions


def score_confidence(
    decisions: Sequence[dict],
    actions: Sequence[dict],
    segments: Sequence[dict],
    speakers: dict[str, str],
) -> dict[str, Any]:
    """Chấm độ tin cậy bằng Python — tất định, 0 quota, chạy lại vô hạn lần.

    Cùng công thức đang hiển thị trên giao diện:

        100 − (Thoại mờ × 5) − (Chưa gán người làm × 8) − (Rủi ro ảo giác × 15)

    "Rủi ro ảo giác" ở đây được đo cụ thể: số mục có câu trích KHÔNG tìm thấy
    trong bản thoại, cộng số mục bị gỡ tên người nhận vì người đó không dự họp.
    """
    low_quality = sum(1 for s in segments if s.get("is_low_quality"))
    unassigned = sum(1 for a in actions if not a.get("assignee"))
    hallucination = (
        sum(1 for x in list(decisions) + list(actions) if x.get("quote_verified") is False)
        + sum(1 for a in actions if a.get("assignee_rejected"))
    )
    deducted = low_quality * 5 + unassigned * 8 + hallucination * 15
    raw = 100 - deducted
    return {
        "score": max(0, min(100, raw)),
        "raw": raw,
        "deducted": deducted,
        "floored": raw < 0,
        "detail": {
            "transcript_gaps": low_quality,
            "ambiguous_assignee": unassigned,
            "hallucination_risk": hallucination,
        },
        "tone": "jade" if raw >= 85 else "amber" if raw >= 70 else "coral",
    }


# ===========================================================================
#  Tiện ích
# ===========================================================================

def _speaker_names(transcript: dict[str, Any]) -> dict[str, str]:
    out = {}
    for s in transcript.get("speakers") or []:
        label = s.get("label") or s.get("speaker_label")
        name = s.get("display_name") or label
        if label:
            out[label] = name
    return out


def _chunks(segments: Sequence[dict], size: int):
    for i in range(0, len(segments), size):
        yield segments[i:i + size]


def _render(segments: Sequence[dict], speakers: dict[str, str]) -> str:
    lines = []
    for s in segments:
        who = speakers.get(s.get("speaker_label", ""), s.get("speaker_label", "?"))
        mark = "  [nghe không rõ]" if s.get("is_low_quality") else ""
        lines.append(f"[{s['id']}] {who}: {s.get('text', '')}{mark}")
    return "\n".join(lines)


def _points_digest(points: Sequence[dict], segments: Sequence[dict]) -> str:
    """Bản nén đưa vào hai bước sau.

    Hai bước cuối KHÔNG thấy transcript gốc — chỉ thấy các mệnh đề đã nén và
    đã được kiểm dẫn chứng. Đó là cùng nguyên tắc "tách Extract khỏi Compose"
    của pipeline: bước sau không có nguyên liệu để bịa thêm.
    """
    by_id = {s["id"]: s for s in segments}
    lines = []
    for p in points:
        ids = p.get("evidence_segment_ids") or []
        stamp = ""
        if ids and ids[0] in by_id:
            ms = by_id[ids[0]].get("start_ms", 0)
            stamp = f" (phút {ms // 60000}:{ms % 60000 // 1000:02d})"
        lines.append(f"- [{','.join(ids)}]{stamp} {p.get('text', '')}")
    return "\n".join(lines)


def _flatten(text: str) -> str:
    """Chuẩn hoá để so khớp câu trích: bỏ dấu câu, gộp khoảng trắng, về chữ thường."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", str(text).lower())).strip()
