"""Pha 2 — DIARIZE: gán danh tính cho các nhãn speaker thô.

Vị trí trong pipeline
---------------------
Đứng giữa phiên âm (s1) và chia chunk (s3). Đầu vào là ``Transcript`` với
nhãn thô (``SPEAKER_00``, ``SPEAKER_01``...); đầu ra là ``Transcript`` mới
với ``person_id`` và ``display_name`` đã điền.

Vì sao pha này quan trọng hơn vẻ ngoài
--------------------------------------
Không có tên người thì ``resolve_person`` ở pha RECONCILE không có gì để
khớp, nên **mọi công việc trong biên bản đều rơi về "chưa phân công"**. Biên
bản vẫn đủ nội dung nhưng mất hoàn toàn giá trị thực thi — không ai biết
mình phải làm gì.

Ba tầng nhận diện, chạy tuần tự
-------------------------------
1. **Nhãn có sẵn** — nếu transcript đã mang tên (do người dùng nhập, hoặc do
   ghi âm đa kênh), giữ nguyên và không làm gì thêm.
2. **Xưng hô tiếng Việt** — khai thác việc người Việt gọi tên nhau liên tục
   trong cuộc họp. Chi tiết ở ``nlp/vocative.py``. Hoàn toàn miễn phí.
3. **Loại trừ** — còn đúng một nhãn và một người chưa ghép thì ghép nốt.

Nguyên tắc bao trùm: **thà giữ nhãn thô còn hơn gán sai tên.** Một biên bản
ghi "SPEAKER_02 nhận việc" thì người đọc biết là cần kiểm tra lại; một biên
bản ghi nhầm "Tuấn nhận việc" thì không ai phát hiện ra cho tới khi muộn.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Sequence

from nlp.vocative import VocativeResult, assign_speakers
from schemas.common import IdentificationMethod
from schemas.transcript import Segment, Speaker, Transcript

logger = logging.getLogger(__name__)

__all__ = [
    "DiarizationResult",
    "run_diarize",
    "parse_attendee_hints",
    "AttendeeHint",
]

_METHOD_MAP: dict[str, IdentificationMethod] = {
    "self_intro": IdentificationMethod.SELF_INTRO,
    "vocative": IdentificationMethod.VOCATIVE,
    "attendee_list_elimination": IdentificationMethod.ATTENDEE_LIST_ELIMINATION,
    "manual": IdentificationMethod.MANUAL,
}


@dataclass(frozen=True, slots=True)
class AttendeeHint:
    """Một người tham dự do người dùng khai báo trước.

    Biết trước danh sách này biến bài toán từ "đoán tên từ không gian mở"
    thành "ghép cặp giữa N nhãn và N người" — dễ hơn nhiều bậc và cho phép
    hạ ngưỡng chấp nhận bằng chứng.
    """

    name: str
    role: str | None = None
    person_id: str | None = None

    def resolved_id(self, index: int) -> str:
        return self.person_id or f"p_{index + 1:03d}"


@dataclass(slots=True)
class DiarizationResult:
    """Transcript đã gán tên, kèm số liệu để đánh giá độ tin cậy."""

    transcript: Transcript
    vocative: VocativeResult | None = None
    resolved_labels: list[str] = field(default_factory=list)
    unresolved_labels: list[str] = field(default_factory=list)
    skipped: bool = False

    @property
    def coverage(self) -> float:
        """Tỉ lệ nhãn speaker đã gán được tên."""
        total = len(self.resolved_labels) + len(self.unresolved_labels)
        return len(self.resolved_labels) / total if total else 0.0

    def summary(self) -> str:
        if self.skipped:
            return "Transcript đã có tên người nói, bỏ qua pha diarize."
        return (
            f"Gán được {len(self.resolved_labels)}/"
            f"{len(self.resolved_labels) + len(self.unresolved_labels)} nhãn "
            f"({self.coverage:.0%})"
        )


def parse_attendee_hints(raw: str | None) -> list[AttendeeHint]:
    """Đọc chuỗi người tham dự từ dòng lệnh.

    Định dạng: ``"Hùng:Product Lead,Tuấn:Backend,Lan:QA"``. Phần vai trò là
    tuỳ chọn, nên ``"Hùng,Tuấn,Lan"`` cũng hợp lệ.

    >>> [h.name for h in parse_attendee_hints("Hùng:PM,Tuấn")]
    ['Hùng', 'Tuấn']
    """
    if not raw or not raw.strip():
        return []

    hints: list[AttendeeHint] = []
    for index, chunk in enumerate(raw.split(",")):
        piece = chunk.strip()
        if not piece:
            continue
        name, _, role = piece.partition(":")
        name = name.strip()
        if not name:
            continue
        hints.append(
            AttendeeHint(
                name=name,
                role=role.strip() or None,
                person_id=f"p_{index + 1:03d}",
            )
        )
    return hints


def run_diarize(
    transcript: Transcript,
    *,
    attendees: Sequence[AttendeeHint] | None = None,
    force: bool = False,
) -> DiarizationResult:
    """Gán tên cho các nhãn speaker của transcript.

    Args:
        transcript: Transcript đầu vào, có thể đã hoặc chưa có tên.
        attendees: Danh sách người tham dự nếu biết trước.
        force: Chạy lại kể cả khi transcript đã có tên. Dùng khi muốn ghi đè
            kết quả gán trước đó.

    Returns:
        ``DiarizationResult`` chứa transcript mới. Transcript gốc **không bị
        thay đổi** — mọi artifact trong hệ thống đều bất biến.
    """
    hints = list(attendees or [])

    if not force and _already_named(transcript):
        logger.info("Transcript đã có tên người nói, bỏ qua pha diarize.")
        return DiarizationResult(
            transcript=transcript,
            resolved_labels=[s.label for s in transcript.speakers],
            skipped=True,
        )

    if _is_single_speaker(transcript):
        logger.warning(
            "Transcript chỉ có một nhãn speaker duy nhất — nguồn ASR không "
            "tách người nói. Xưng hô không đủ để chia lượt, nên chỉ gán tên "
            "khi có đúng một người tham dự được khai báo."
        )
        return _handle_single_speaker(transcript, hints)

    payload = [
        {
            "id": segment.id,
            "index": segment.index,
            "speaker_label": segment.speaker_label,
            "text": segment.text,
        }
        for segment in transcript.segments
    ]

    known_names = [hint.name for hint in hints] or None
    vocative = assign_speakers(payload, known_names=known_names)

    logger.info(
        "DIARIZE: dò được %d lần nhắc tên, gán %d/%d nhãn",
        len(vocative.mentions),
        len(vocative.assignments),
        len(transcript.speakers),
    )
    for label, name in sorted(vocative.assignments.items()):
        logger.info(
            "  %s -> %s (%.0f%%, %s)",
            label, name, vocative.confidences[label] * 100, vocative.methods[label],
        )
    for label in vocative.unresolved:
        logger.warning("  %s -> chưa xác định được, giữ nguyên nhãn thô", label)

    return _build_result(transcript, vocative, hints)


# --------------------------------------------------------------------------- #
# Nội bộ
# --------------------------------------------------------------------------- #


def _already_named(transcript: Transcript) -> bool:
    """Transcript đã có tên cho MỌI speaker chưa."""
    return all(
        speaker.display_name and speaker.display_name != speaker.label
        for speaker in transcript.speakers
    )


def _is_single_speaker(transcript: Transcript) -> bool:
    return len({segment.speaker_label for segment in transcript.segments}) <= 1


def _handle_single_speaker(
    transcript: Transcript, hints: Sequence[AttendeeHint]
) -> DiarizationResult:
    """Xử lý trường hợp ASR không tách người nói.

    Chỉ gán tên khi có đúng một người tham dự — mọi trường hợp khác đều là
    phỏng đoán vô căn cứ. Đây là giới hạn thật của việc dùng Groq Whisper,
    không phải khiếm khuyết của thuật toán xưng hô: không có ranh giới lượt
    nói thì không có gì để bỏ phiếu cho.
    """
    label = transcript.speakers[0].label if transcript.speakers else "SPEAKER_00"

    if len(hints) == 1:
        return _build_result(
            transcript,
            _single_assignment(label, hints[0].name),
            hints,
        )

    return DiarizationResult(
        transcript=transcript,
        unresolved_labels=[label],
    )


def _single_assignment(label: str, name: str) -> VocativeResult:
    result = VocativeResult()
    result.assignments[label] = name
    result.confidences[label] = 0.80
    result.methods[label] = "manual"
    result.evidence[label] = []
    return result


def _build_result(
    transcript: Transcript,
    vocative: VocativeResult,
    hints: Sequence[AttendeeHint],
) -> DiarizationResult:
    """Dựng transcript mới với tên đã gán. Bản gốc giữ nguyên."""
    hint_by_name = {_normalise(hint.name): hint for hint in hints}
    person_ids = _allocate_person_ids(vocative, hints)

    speakers: list[Speaker] = []
    resolved: list[str] = []
    unresolved: list[str] = []

    for speaker in transcript.speakers:
        name = vocative.assignments.get(speaker.label)

        if name is None:
            unresolved.append(speaker.label)
            speakers.append(
                speaker.model_copy(
                    update={
                        "person_id": None,
                        "display_name": None,
                        "identification_method": IdentificationMethod.UNIDENTIFIED,
                        "identification_confidence": 0.0,
                        "evidence_for_identification": [],
                    }
                )
            )
            continue

        resolved.append(speaker.label)
        hint = hint_by_name.get(_normalise(name))
        method_key = vocative.methods.get(speaker.label, "vocative")

        speakers.append(
            speaker.model_copy(
                update={
                    "person_id": person_ids[speaker.label],
                    "display_name": name,
                    "role": hint.role if hint else speaker.role,
                    "identification_method": _METHOD_MAP.get(
                        method_key, IdentificationMethod.VOCATIVE
                    ),
                    "identification_confidence": vocative.confidences.get(
                        speaker.label, 0.0
                    ),
                    "evidence_for_identification": vocative.evidence.get(
                        speaker.label, []
                    ),
                }
            )
        )

    segments: list[Segment] = [
        segment.model_copy(
            update={"person_id": person_ids.get(segment.speaker_label)}
        )
        for segment in transcript.segments
    ]

    updated = transcript.model_copy(
        update={
            "version": transcript.version + 1,
            "speakers": speakers,
            "segments": segments,
            "provider": transcript.provider.model_copy(
                update={"diarization": "nlp.vocative/v1"}
            ),
        }
    )

    return DiarizationResult(
        transcript=updated,
        vocative=vocative,
        resolved_labels=resolved,
        unresolved_labels=unresolved,
    )


def _allocate_person_ids(
    vocative: VocativeResult, hints: Sequence[AttendeeHint]
) -> dict[str, str]:
    """Cấp ``person_id`` ổn định cho từng nhãn đã gán được tên.

    Ưu tiên ID do người dùng khai báo để liên kết được với dữ liệu bên ngoài
    (Jira, Slack); nếu không có thì sinh ID tuần tự.
    """
    hint_by_name = {_normalise(hint.name): hint for hint in hints}
    mapping: dict[str, str] = {}

    for order, (label, name) in enumerate(sorted(vocative.assignments.items())):
        hint = hint_by_name.get(_normalise(name))
        mapping[label] = hint.resolved_id(order) if hint else f"p_{order + 1:03d}"

    return mapping


def _normalise(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", stripped)).strip()
