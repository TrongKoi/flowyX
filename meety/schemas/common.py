"""Kiểu dữ liệu và enum dùng chung cho toàn bộ hệ thống.

Module này cố ý KHÔNG import bất cứ thứ gì ngoài stdlib và pydantic, để
`nlp/` có thể dùng lại các enum ở đây mà vẫn chạy được hoàn toàn offline.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# --------------------------------------------------------------------------- #
# Tương thích phiên bản Python
# --------------------------------------------------------------------------- #

try:
    from typing import Self
except ImportError:  # pragma: no cover - chỉ chạy trên Python 3.10
    # ``typing.Self`` chỉ có từ Python 3.11. Trên 3.10 lấy từ
    # ``typing_extensions`` — không phải cài thêm gì, vì pydantic đã bắt buộc
    # phụ thuộc vào gói này (``typing-extensions>=4.14.1``).
    #
    # Toàn bộ project lấy ``Self`` qua module này thay vì import trực tiếp từ
    # ``typing``, để chỗ xử lý tương thích chỉ nằm ở một nơi duy nhất.
    from typing_extensions import Self

__all__ = [
    "Self",
    "SegmentId",
    "SEGMENT_ID_PATTERN",
    "Confidence",
    "Language",
    "MeetingType",
    "IdentificationMethod",
    "DecisionStatus",
    "CommitmentStrength",
    "ActionStatus",
    "Priority",
    "Severity",
    "RiskStatus",
    "ConsensusLevel",
    "ReviewState",
    "WarningCode",
    "StrictModel",
]

# --------------------------------------------------------------------------- #
# Kiểu định danh
# --------------------------------------------------------------------------- #

SEGMENT_ID_PATTERN = r"^s_\d{4,}$"
"""ID segment cố ý NGẮN và tuần tự (``s_0142``) thay vì UUID.

LLM phải xuất lại chính ID này trong trường ``evidence_segment_ids``; ID dài
vừa tốn token vừa làm tăng tỉ lệ model gõ sai.
"""

SegmentId = Annotated[str, Field(pattern=SEGMENT_ID_PATTERN)]


# --------------------------------------------------------------------------- #
# Enum nghiệp vụ
# --------------------------------------------------------------------------- #


class Confidence(str, Enum):
    """Độ tin cậy ở cấp từng mục, không phải cấp tài liệu."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Language(str, Enum):
    VI = "vi"
    EN = "en"
    MIXED = "mixed"


class MeetingType(str, Enum):
    STANDUP = "standup"
    RETRO = "retro"
    PLANNING = "planning"
    REVIEW = "review"
    CLIENT = "client"
    BOARD = "board"
    ONE_ON_ONE = "1on1"
    INTERVIEW = "interview"
    OTHER = "other"


class IdentificationMethod(str, Enum):
    """Cách hệ thống gán tên cho một speaker thô."""

    MANUAL = "manual"
    CALENDAR = "calendar"
    VOCATIVE = "vocative"
    SELF_INTRO = "self_intro"
    VOICEPRINT = "voiceprint"
    ATTENDEE_LIST_ELIMINATION = "attendee_list_elimination"
    UNIDENTIFIED = "unidentified"


class DecisionStatus(str, Enum):
    DECIDED = "decided"
    TENTATIVE = "tentative"
    DEFERRED = "deferred"
    REJECTED = "rejected"


class CommitmentStrength(str, Enum):
    """Phân biệt cam kết chắc chắn với đề xuất chưa chốt.

    Rất quan trọng với văn hoá giao tiếp gián tiếp: "để em xem lại rồi báo anh"
    là ``TENTATIVE``, không phải ``FIRM``.
    """

    FIRM = "firm"
    TENTATIVE = "tentative"
    PROPOSED = "proposed"


class ActionStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"
    CARRIED_OVER = "carried_over"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNSPECIFIED = "unspecified"


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNSPECIFIED = "unspecified"


class RiskStatus(str, Enum):
    OPEN = "open"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    CLOSED = "closed"


class ConsensusLevel(str, Enum):
    ALIGNED = "aligned"
    DEBATED = "debated"
    UNRESOLVED = "unresolved"
    UNSPECIFIED = "unspecified"


class ReviewState(str, Enum):
    """Phục vụ vòng lặp phản hồi: diff giữa bản AI và bản người duyệt."""

    AI_GENERATED = "ai_generated"
    HUMAN_EDITED = "human_edited"
    HUMAN_CONFIRMED = "human_confirmed"
    REJECTED = "rejected"


class WarningCode(str, Enum):
    LOW_AUDIO_QUALITY = "LOW_AUDIO_QUALITY"
    UNIDENTIFIED_SPEAKERS = "UNIDENTIFIED_SPEAKERS"
    AMBIGUOUS_ASSIGNEE = "AMBIGUOUS_ASSIGNEE"
    HALLUCINATED_ASSIGNEE = "HALLUCINATED_ASSIGNEE"
    NO_EXPLICIT_DECISIONS = "NO_EXPLICIT_DECISIONS"
    HEAVY_OVERLAP = "HEAVY_OVERLAP"
    TRANSCRIPT_GAPS = "TRANSCRIPT_GAPS"
    CONFLICTING_STATEMENTS = "CONFLICTING_STATEMENTS"
    POSSIBLE_TRUNCATION = "POSSIBLE_TRUNCATION"
    SUPERSEDED_DEPENDENCY = "SUPERSEDED_DEPENDENCY"
    AMBIGUOUS_SUPERSESSION = "AMBIGUOUS_SUPERSESSION"
    LOW_COMMITMENT_STRENGTH = "LOW_COMMITMENT_STRENGTH"
    FABRICATED_DUE_DATE = "FABRICATED_DUE_DATE"
    UNGROUNDED_NUMBER = "UNGROUNDED_NUMBER"
    UNKNOWN_ENTITY_IN_PROSE = "UNKNOWN_ENTITY_IN_PROSE"
    DATE_IN_PAST = "DATE_IN_PAST"
    DATE_IMPLAUSIBLE = "DATE_IMPLAUSIBLE"


# --------------------------------------------------------------------------- #
# Base model
# --------------------------------------------------------------------------- #


class StrictModel(BaseModel):
    """Base cho mọi schema.

    ``extra="forbid"`` tương đương ``additionalProperties: false`` trong JSON
    Schema: chặn LLM tự "sáng tác" thêm trường ngoài hợp đồng đã khai báo.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=False,
        str_strip_whitespace=True,
        frozen=False,
    )
