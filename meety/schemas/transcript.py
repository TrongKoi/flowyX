"""Schema cho artifact Transcript — tầng dữ liệu nền của toàn hệ thống.

``Transcript`` là artifact bền vững ĐẦU TIÊN của pipeline và là nơi mọi
``evidence_segment_ids`` trỏ về. Nó bất biến và có version: người dùng sửa
transcript sẽ sinh ra v2 chứ không ghi đè v1, cho phép chạy lại các pha
phía sau mà không phải trả lại tiền STT (khoản đắt nhất trong pipeline).
"""

from __future__ import annotations

import datetime as dt

from pydantic import Field, model_validator

from schemas.common import (
    Confidence,
    IdentificationMethod,
    Language,
    MeetingType,
    SegmentId,
    Self,
    StrictModel,
)

__all__ = [
    "Word",
    "Segment",
    "Speaker",
    "TranscriptQuality",
    "TranscriptChunk",
    "ProviderInfo",
    "LanguageProfile",
    "TranscriptMeta",
    "Transcript",
    "LOW_LOGPROB_THRESHOLD",
    "HIGH_NO_SPEECH_THRESHOLD",
]

# Ngưỡng lọc dựa trên metadata do Whisper trả về. Đây là "grounding check
# tầng 0": hoàn toàn miễn phí, chạy trước khi động tới bất kỳ LLM nào.
LOW_LOGPROB_THRESHOLD: float = -0.7
"""Dưới ngưỡng này, segment bị coi là kém tin cậy và hạ confidence mọi mục trích xuất từ nó."""

HIGH_NO_SPEECH_THRESHOLD: float = 0.6
"""Trên ngưỡng này, segment nhiều khả năng là ảo giác của Whisper trên đoạn im lặng."""


class Word(StrictModel):
    """Một từ kèm mốc thời gian, dùng để align diarization và highlight audio."""

    word: str = Field(min_length=1)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _check_time_order(self) -> Self:
        if self.end_ms < self.start_ms:
            raise ValueError(
                f"Từ {self.word!r}: end_ms ({self.end_ms}) < start_ms ({self.start_ms})"
            )
        return self


class Segment(StrictModel):
    """Đơn vị nguyên tử của hệ thống — mọi bằng chứng đều trỏ về đây.

    Giữ đồng thời ``text`` (đã hậu xử lý) và ``text_raw`` (nguyên bản từ ASR).
    Bản thô cần cho việc debug và cho phép chạy lại bước hậu xử lý mà không
    phải gọi lại STT.
    """

    id: SegmentId
    index: int = Field(ge=1)
    speaker_label: str = Field(min_length=1)
    person_id: str | None = None
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    text: str = Field(min_length=1)
    text_raw: str | None = None
    lang: Language = Language.VI
    asr_confidence: float = Field(ge=0.0, le=1.0)
    no_speech_prob: float | None = Field(default=None, ge=0.0, le=1.0)
    words: list[Word] = Field(default_factory=list)
    is_overlapped: bool = False
    is_low_quality: bool = False

    @model_validator(mode="after")
    def _check_time_order(self) -> Self:
        if self.end_ms < self.start_ms:
            raise ValueError(
                f"Segment {self.id}: end_ms ({self.end_ms}) < start_ms ({self.start_ms})"
            )
        return self

    @property
    def duration_ms(self) -> int:
        """Dùng ``property`` chứ không phải ``computed_field``.

        Dữ liệu suy ra được thì không lưu xuống đĩa: ``computed_field`` sẽ
        xuất trường này khi serialize nhưng ``extra="forbid"`` lại từ chối nó
        khi đọc vào, làm vỡ vòng lặp ghi/đọc artifact của cơ chế ``--resume``.
        """
        return self.end_ms - self.start_ms

    @property
    def is_trustworthy(self) -> bool:
        """Segment có đủ tin cậy để làm bằng chứng cho một cam kết không.

        Segment chồng lấn hoặc chất lượng thấp không được dùng làm bằng chứng
        DUY NHẤT cho một Decision hay Action Item.
        """
        return not self.is_low_quality and not self.is_overlapped


class Speaker(StrictModel):
    """Một người nói, kèm cách hệ thống nhận ra danh tính của họ.

    Giữ cả ``label`` (nhãn thô, không đổi) và ``person_id`` (ánh xạ có thể
    sửa) để người dùng gán lại tên mà không phá vỡ liên kết dữ liệu.
    """

    label: str = Field(min_length=1)
    person_id: str | None = None
    display_name: str | None = None
    role: str | None = None
    identification_method: IdentificationMethod = IdentificationMethod.UNIDENTIFIED
    identification_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_for_identification: list[SegmentId] = Field(default_factory=list)
    talk_time_ms: int = Field(default=0, ge=0)
    talk_time_pct: float = Field(default=0.0, ge=0.0, le=100.0)

    @model_validator(mode="after")
    def _identified_speaker_needs_name(self) -> Self:
        if (
            self.identification_method is not IdentificationMethod.UNIDENTIFIED
            and not self.display_name
        ):
            raise ValueError(
                f"Speaker {self.label}: đã nhận diện bằng "
                f"{self.identification_method.value} nhưng thiếu display_name"
            )
        return self

    @property
    def needs_manual_assignment(self) -> bool:
        """Dưới ngưỡng tin cậy thì giữ nhãn thô — gán sai tên tệ hơn không gán."""
        return (
            self.identification_method is IdentificationMethod.UNIDENTIFIED
            or self.identification_confidence < 0.60
        )


class TranscriptQuality(StrictModel):
    """Chỉ số chất lượng từ bước tiền kiểm, hiển thị được cho người dùng."""

    avg_logprob_mean: float | None = None
    low_confidence_segment_count: int = Field(default=0, ge=0)
    estimated_snr_db: float | None = None
    speech_ratio: float = Field(default=1.0, ge=0.0, le=1.0)
    overall_score: float = Field(default=1.0, ge=0.0, le=1.0)


class TranscriptChunk(StrictModel):
    """Một đoạn được đưa vào pha EXTRACT.

    Các chunk cố ý CHỒNG LẤN nhau vài segment ở mép. Đây không phải để cho
    chắc: không có overlap thì không phát hiện được quyết định bị đảo ngược
    khi hai phát biểu liên quan rơi vào hai chunk khác nhau.
    """

    chunk_id: str = Field(min_length=1)
    segment_ids: list[SegmentId] = Field(min_length=1)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    token_estimate: int = Field(default=0, ge=0)


class ProviderInfo(StrictModel):
    """Ghi lại nhà cung cấp đã dùng — bắt buộc để truy vết nguồn gốc lỗi."""

    asr: str = Field(min_length=1)
    diarization: str | None = None
    post_process: str | None = None


class LanguageProfile(StrictModel):
    primary: Language = Language.VI
    secondary: list[Language] = Field(default_factory=list)
    code_switching: bool = False


class TranscriptMeta(StrictModel):
    """Metadata cuộc họp.

    ``meeting_date`` và ``timezone`` là BẮT BUỘC: chúng là mốc neo để quy đổi
    mọi biểu thức thời gian tương đối ("thứ 3 tuần sau"). Thiếu mốc neo thì
    toàn bộ deadline trong biên bản trở nên vô nghĩa.
    """

    title: str = Field(min_length=1, max_length=200)
    meeting_date: dt.date
    timezone: str = "Asia/Ho_Chi_Minh"
    meeting_type: MeetingType = MeetingType.OTHER
    duration_ms: int = Field(ge=0)
    glossary: list[str] = Field(default_factory=list)

    @property
    def weekday(self) -> str:
        """Suy ra từ ``meeting_date``, cố ý KHÔNG lưu xuống đĩa (xem ``Segment.duration_ms``)."""
        return self.meeting_date.strftime("%A")


class Transcript(StrictModel):
    """Artifact transcript hoàn chỉnh, bất biến và có version."""

    transcript_id: str = Field(min_length=1)
    meeting_id: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    created_at: dt.datetime | None = None
    meta: TranscriptMeta
    provider: ProviderInfo
    language_profile: LanguageProfile = Field(default_factory=LanguageProfile)
    quality: TranscriptQuality = Field(default_factory=TranscriptQuality)
    speakers: list[Speaker] = Field(min_length=1)
    segments: list[Segment] = Field(min_length=1)
    chunks: list[TranscriptChunk] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_referential_integrity(self) -> Self:
        segment_ids = [s.id for s in self.segments]
        unique_ids = set(segment_ids)
        if len(segment_ids) != len(unique_ids):
            duplicates = {i for i in segment_ids if segment_ids.count(i) > 1}
            raise ValueError(f"Segment ID bị trùng: {sorted(duplicates)}")

        labels = {s.label for s in self.speakers}
        if len(labels) != len(self.speakers):
            raise ValueError("Speaker label bị trùng")

        for segment in self.segments:
            if segment.speaker_label not in labels:
                raise ValueError(
                    f"Segment {segment.id} trỏ tới speaker không tồn tại: "
                    f"{segment.speaker_label}"
                )

        for chunk in self.chunks:
            unknown = [sid for sid in chunk.segment_ids if sid not in unique_ids]
            if unknown:
                raise ValueError(
                    f"Chunk {chunk.chunk_id} chứa segment không tồn tại: {unknown}"
                )

        for speaker in self.speakers:
            unknown = [
                sid
                for sid in speaker.evidence_for_identification
                if sid not in unique_ids
            ]
            if unknown:
                raise ValueError(
                    f"Speaker {speaker.label} dẫn chứng segment không tồn tại: {unknown}"
                )

        return self

    # -- Truy vấn tiện dụng cho tầng validator ------------------------------ #

    @property
    def segment_index(self) -> dict[str, Segment]:
        """Bảng tra cứu O(1) — dùng cho mọi kiểm tra grounding."""
        return {s.id: s for s in self.segments}

    @property
    def speaker_index(self) -> dict[str, Speaker]:
        return {s.label: s for s in self.speakers}

    @property
    def known_person_names(self) -> set[str]:
        """Tập tên hợp lệ. Assignee nằm ngoài tập này là dấu hiệu hallucination."""
        return {s.display_name for s in self.speakers if s.display_name}

    @property
    def full_text(self) -> str:
        return " ".join(s.text for s in self.segments)

    def get_segments(self, segment_ids: list[str]) -> list[Segment]:
        """Lấy các segment theo ID, giữ nguyên thứ tự yêu cầu, bỏ qua ID lạ."""
        index = self.segment_index
        return [index[sid] for sid in segment_ids if sid in index]

    def evidence_text(self, segment_ids: list[str]) -> str:
        """Ghép text của các segment được dẫn chứng, để đối chiếu với quote."""
        return " ".join(s.text for s in self.get_segments(segment_ids))

    def earliest_timestamp_ms(self, segment_ids: list[str]) -> int | None:
        """Mốc thời gian sớm nhất trong tập bằng chứng.

        Đây là giá trị dùng để sắp xếp các mục theo thời gian ở pha
        RECONCILE — nền tảng của quy tắc "phát biểu sau đè phát biểu trước".
        """
        segments = self.get_segments(segment_ids)
        return min((s.start_ms for s in segments), default=None)
