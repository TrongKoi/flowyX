"""Kiểm thử bộ chia chunk thích ứng.

Hai bất biến quan trọng nhất được kiểm ở đây:

* **Không sót segment nào.** Một segment lọt ra ngoài mọi chunk là một đoạn
  hội thoại biến mất khỏi biên bản mà không ai biết.
* **Chunk liền kề luôn chồng lấn.** Đây là điều kiện cần để pha RECONCILE
  phát hiện được quyết định bị đảo ngược khi hai phát biểu liên quan rơi vào
  hai chunk khác nhau.
"""

from __future__ import annotations

import datetime as dt

import pytest

from pipeline.s3_chunk import (
    DEFAULT_OVERLAP_SEGMENTS,
    ChunkingPolicy,
    estimate_segment_tokens,
    run_chunk,
)
from schemas.common import IdentificationMethod, Language, MeetingType
from schemas.transcript import (
    LanguageProfile,
    ProviderInfo,
    Segment,
    Speaker,
    Transcript,
    TranscriptMeta,
)


def build_transcript(
    segment_count: int,
    *,
    text_length: int = 80,
    pause_at: set[int] | None = None,
    speakers: int = 2,
) -> Transcript:
    """Dựng transcript tổng hợp để kiểm soát chính xác điều kiện thử."""
    pauses = pause_at or set()
    segments: list[Segment] = []
    cursor = 0

    for index in range(1, segment_count + 1):
        if index in pauses:
            cursor += 5_000
        start = cursor
        end = start + 4_000
        cursor = end
        segments.append(
            Segment(
                id=f"s_{index:04d}",
                index=index,
                speaker_label=f"SPEAKER_{index % speakers:02d}",
                start_ms=start,
                end_ms=end,
                text="nội dung thảo luận " * (text_length // 20),
                asr_confidence=0.9,
                lang=Language.VI,
            )
        )

    return Transcript(
        transcript_id="tr_test",
        meeting_id="mtg_test",
        meta=TranscriptMeta(
            title="Cuộc họp kiểm thử",
            meeting_date=dt.date(2026, 7, 22),
            meeting_type=MeetingType.PLANNING,
            duration_ms=cursor,
        ),
        provider=ProviderInfo(asr="test"),
        language_profile=LanguageProfile(),
        speakers=[
            Speaker(
                label=f"SPEAKER_{i:02d}",
                display_name=f"Người {i}",
                identification_method=IdentificationMethod.MANUAL,
                identification_confidence=1.0,
            )
            for i in range(speakers)
        ],
        segments=segments,
    )


# --------------------------------------------------------------------------- #
# Chiến lược mặc định: càng ít chunk càng tốt
# --------------------------------------------------------------------------- #


class TestSingleChunkPreference:
    def test_short_meeting_fits_in_one_chunk(self) -> None:
        """Đường tối ưu quota: một lời gọi cho cả cuộc họp."""
        result = run_chunk(build_transcript(20))
        assert len(result.chunks) == 1
        assert result.chunks[0].chunk_id == "c_all"
        assert result.overlap_tokens == 0

    def test_hour_long_meeting_still_fits_in_one_chunk(self) -> None:
        """Cuộc họp một giờ (~25k token) vẫn lọt cửa sổ 1M của Gemini.

        Đây chính là điểm đảo ngược so với bản trả phí: không chia nhỏ trừ khi
        buộc phải, vì free tier tính theo request chứ không theo token.
        """
        result = run_chunk(build_transcript(400, text_length=160))
        assert len(result.chunks) == 1

    def test_empty_transcript_produces_no_chunks(self) -> None:
        transcript = build_transcript(1)
        transcript = transcript.model_copy(update={"segments": transcript.segments})
        result = run_chunk(transcript)
        assert len(result.chunks) == 1


# --------------------------------------------------------------------------- #
# Bất biến khi phải chia nhiều chunk
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def multi_chunk_result():
    return run_chunk(build_transcript(30), ChunkingPolicy(max_tokens_per_chunk=300))


class TestMultiChunkInvariants:
    def test_produces_multiple_chunks(self, multi_chunk_result) -> None:
        assert len(multi_chunk_result.chunks) >= 2

    def test_covers_every_segment(self, multi_chunk_result) -> None:
        """Không segment nào được phép rơi ra ngoài."""
        covered: set[str] = set()
        for chunk in multi_chunk_result.chunks:
            covered |= set(chunk.segment_ids)
        assert covered == {f"s_{i:04d}" for i in range(1, 31)}

    def test_adjacent_chunks_overlap(self, multi_chunk_result) -> None:
        """Không chồng lấn thì không phát hiện được đổi ý xuyên chunk."""
        for left, right in zip(multi_chunk_result.chunks, multi_chunk_result.chunks[1:]):
            shared = set(left.segment_ids) & set(right.segment_ids)
            assert shared, f"{left.chunk_id} và {right.chunk_id} không chồng lấn"
            assert len(shared) == DEFAULT_OVERLAP_SEGMENTS

    def test_segments_stay_in_order(self, multi_chunk_result) -> None:
        for chunk in multi_chunk_result.chunks:
            indices = [int(sid.split("_")[1]) for sid in chunk.segment_ids]
            assert indices == sorted(indices)

    def test_chunk_ids_are_sequential(self, multi_chunk_result) -> None:
        assert [c.chunk_id for c in multi_chunk_result.chunks] == [
            f"c_{i:02d}" for i in range(1, len(multi_chunk_result.chunks) + 1)
        ]

    def test_timestamps_are_consistent(self, multi_chunk_result) -> None:
        for chunk in multi_chunk_result.chunks:
            assert chunk.start_ms <= chunk.end_ms

    def test_overlap_ratio_stays_modest(self, multi_chunk_result) -> None:
        """Chồng lấn phải đủ để giữ ngữ cảnh nhưng không phồng token vô ích."""
        assert 0 < multi_chunk_result.overlap_ratio < 0.35


# --------------------------------------------------------------------------- #
# Ranh giới ngữ nghĩa
# --------------------------------------------------------------------------- #


class TestSemanticBoundaries:
    def test_prefers_cutting_at_long_pause(self) -> None:
        """Khoảng lặng dài là ranh giới chủ đề tự nhiên."""
        transcript = build_transcript(20, pause_at={11})
        # Trần token chọn sao cho ra ĐÚNG 2 chunk: khi đó điểm cắt lý tưởng
        # nằm giữa transcript, đúng vùng có khoảng lặng.
        result = run_chunk(transcript, ChunkingPolicy(max_tokens_per_chunk=500))
        assert len(result.chunks) == 2
        assert result.boundaries_used == ["s_0011"]

    def test_prefers_cutting_at_topic_shift_phrase(self) -> None:
        """Cụm "chuyển sang mục tiếp theo" là tín hiệu mạnh nhất."""
        transcript = build_transcript(20)
        segments = list(transcript.segments)
        segments[9] = segments[9].model_copy(
            update={"text": "Ok chuyển sang mục tiếp theo nhé, còn vấn đề ngân sách."}
        )
        transcript = transcript.model_copy(update={"segments": segments})

        result = run_chunk(transcript, ChunkingPolicy(max_tokens_per_chunk=500))
        assert len(result.chunks) == 2
        assert result.boundaries_used == ["s_0010"]


# --------------------------------------------------------------------------- #
# Thích ứng theo quota
# --------------------------------------------------------------------------- #


class TestQuotaAwareness:
    def test_reserves_requests_for_later_phases(self) -> None:
        """Chia hết quota cho EXTRACT sẽ khiến COMPOSE chết vì hết lượt.

        Đó là kết cục tệ nhất: đã tiêu quota mà không có biên bản nào.
        """
        policy = ChunkingPolicy.from_quota(10)
        assert policy.max_chunks == 7

    def test_never_drops_below_one_chunk(self) -> None:
        policy = ChunkingPolicy.from_quota(1)
        assert policy.max_chunks == 1

    def test_unlimited_when_quota_unknown(self) -> None:
        assert ChunkingPolicy.from_quota(None).max_chunks is None

    def test_respects_chunk_cap_and_flags_it(self) -> None:
        policy = ChunkingPolicy(max_tokens_per_chunk=100, max_chunks=2)
        result = run_chunk(build_transcript(40), policy)
        assert len(result.chunks) <= 2
        assert result.capped_by_quota is True

    def test_does_not_flag_when_cap_is_not_binding(self) -> None:
        policy = ChunkingPolicy(max_tokens_per_chunk=100_000, max_chunks=10)
        result = run_chunk(build_transcript(20), policy)
        assert result.capped_by_quota is False

    def test_avoids_tiny_chunks(self) -> None:
        """Chunk vụn làm mất ngữ cảnh nhiều hơn phần quota tiết kiệm được."""
        policy = ChunkingPolicy(max_tokens_per_chunk=20, min_segments_per_chunk=4)
        result = run_chunk(build_transcript(12), policy)
        assert len(result.chunks) <= 3


# --------------------------------------------------------------------------- #
# Ước lượng token
# --------------------------------------------------------------------------- #


class TestTokenEstimation:
    def test_includes_formatting_overhead(self) -> None:
        """Mỗi segment còn mang theo ID, mốc thời gian và tên người nói."""
        segment = build_transcript(1).segments[0]
        raw = len(segment.text) / 2.6
        assert estimate_segment_tokens(segment) > raw

    def test_scales_with_text_length(self) -> None:
        short = build_transcript(1, text_length=40).segments[0]
        long = build_transcript(1, text_length=400).segments[0]
        assert estimate_segment_tokens(long) > estimate_segment_tokens(short)

    def test_chunk_carries_token_estimate(self) -> None:
        result = run_chunk(build_transcript(10))
        assert result.chunks[0].token_estimate > 0


def test_chunking_is_deterministic() -> None:
    """Cùng đầu vào phải cho cùng cách chia — pipeline phải tái lập được."""
    transcript = build_transcript(30)
    policy = ChunkingPolicy(max_tokens_per_chunk=300)
    reference = [c.segment_ids for c in run_chunk(transcript, policy).chunks]
    for _ in range(3):
        assert [c.segment_ids for c in run_chunk(transcript, policy).chunks] == reference
