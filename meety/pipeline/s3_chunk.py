"""Pha 3 — CHUNK: chia transcript thành các đoạn cho pha EXTRACT.

Đảo ngược nguyên tắc so với bản trả phí
---------------------------------------
Ở hệ tính tiền theo token, ta chia nhỏ chunk để dùng model rẻ cho phần dễ.
Ở free tier thì **nút thắt là số request, không phải token**: một lời gọi
5.000 token và một lời gọi 40.000 token tốn quota **như nhau**.

Vì vậy mục tiêu ở đây là **tối thiểu hoá số chunk**, không phải tối ưu kích
thước chunk. Với context 1M token của Gemini, cuộc họp một giờ (~25.000
token) lọt gọn trong một lời gọi duy nhất.

Chồng lấn là bắt buộc, không phải để cho chắc
---------------------------------------------
Mỗi chunk mang theo vài segment cuối của chunk trước. Đây là **điều kiện cần**
để phát hiện đổi ý (supersession): nếu phút 12 chốt "release 26/07" rơi vào
chunk 1 và phút 48 "lùi sang 28/07" rơi vào chunk 2, mà hai chunk được trích
xuất độc lập, thì pha RECONCILE sẽ nhận hai quyết định không biết cái nào
liên quan cái nào. Chồng lấn giữ lại sợi dây ngữ cảnh đó.

Ranh giới cắt theo ngữ nghĩa
----------------------------
Không cắt giữa câu hay giữa lượt nói. Điểm cắt được chọn ở nơi có tín hiệu
chuyển chủ đề tự nhiên: khoảng nghỉ dài, đổi người nói, hoặc cụm từ báo hiệu
("chuyển sang mục tiếp theo", "còn vấn đề nữa là").
"""

from __future__ import annotations

import logging
import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Sequence

from schemas.transcript import Segment, Transcript, TranscriptChunk

logger = logging.getLogger(__name__)

__all__ = [
    "ChunkingPolicy",
    "ChunkingResult",
    "run_chunk",
    "estimate_segment_tokens",
    "DEFAULT_OVERLAP_SEGMENTS",
    "TOPIC_SHIFT_MARKERS",
]

DEFAULT_OVERLAP_SEGMENTS: int = 2
"""Số segment chồng lấn ở mép mỗi chunk. Hai là đủ để giữ ngữ cảnh mà không
làm phồng đáng kể số token."""

VIETNAMESE_CHARS_PER_TOKEN: float = 2.6
"""Hệ số ước lượng token cho tiếng Việt.

Tiếng Việt tốn nhiều token hơn tiếng Anh cho cùng lượng thông tin. Con số này
thận trọng có chủ ý: ước lượng thừa chỉ khiến ta chia thêm một chunk, còn
ước lượng thiếu thì gãy giữa chừng vì vượt cửa sổ ngữ cảnh.
"""

LONG_PAUSE_MS: int = 2_000
"""Khoảng lặng đủ dài để coi là ranh giới chủ đề tự nhiên."""

TOPIC_SHIFT_MARKERS: tuple[str, ...] = (
    "chuyen sang",
    "tiep theo",
    "muc tiep",
    "van de tiep",
    "con van de",
    "con vu",
    "qua phan",
    "sang phan",
    "bay gio",
    "tiep den",
    "ngoai ra",
    "cuoi cung",
    "tom lai",
    "quay lai",
    "noi ve",
    "ban ve",
)
"""Cụm từ báo hiệu người nói đang chuyển chủ đề — điểm cắt lý tưởng."""


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", stripped)).strip()


def estimate_segment_tokens(segment: Segment) -> int:
    """Ước lượng số token của một segment, cộng phần chi phí định dạng.

    Mỗi segment khi vào prompt còn mang theo ID, mốc thời gian và tên người
    nói (``[s_0142] (10:23) Chị Lan: ...``). Phần này khoảng 12 token và
    không nhỏ khi cộng dồn qua hàng trăm segment.
    """
    return int(len(segment.text) / VIETNAMESE_CHARS_PER_TOKEN) + 12


@dataclass(frozen=True, slots=True)
class ChunkingPolicy:
    """Ràng buộc chi phối cách chia chunk."""

    max_tokens_per_chunk: int = 120_000
    """Trần token cho một chunk.

    Đặt rất cao có chủ ý: Gemini Flash có cửa sổ 1M token, nên với gần như
    mọi cuộc họp thực tế, giá trị này không bao giờ bị chạm và toàn bộ
    transcript đi trong MỘT lời gọi — phương án tiết kiệm quota nhất.
    """

    max_chunks: int | None = None
    """Trần số chunk, thường lấy từ số request còn lại trong ngày."""

    overlap_segments: int = DEFAULT_OVERLAP_SEGMENTS
    min_segments_per_chunk: int = 3

    @classmethod
    def from_quota(
        cls,
        remaining_requests: int | None,
        *,
        reserved_for_other_phases: int = 3,
        max_tokens_per_chunk: int = 120_000,
    ) -> ChunkingPolicy:
        """Dựng chính sách từ quota còn lại.

        Ba request được để dành cho các pha sau (gom nhóm chủ đề, viết văn
        xuôi, và một suất dự phòng). Chia hết quota cho pha EXTRACT sẽ khiến
        pipeline chết ở bước COMPOSE — tệ hơn nhiều so với chunk to hơn một
        chút, vì lúc đó ta đã tiêu quota mà không có biên bản nào.
        """
        budget: int | None = None
        if remaining_requests is not None:
            budget = max(1, remaining_requests - reserved_for_other_phases)

        return cls(max_tokens_per_chunk=max_tokens_per_chunk, max_chunks=budget)


@dataclass(slots=True)
class ChunkingResult:
    chunks: list[TranscriptChunk] = field(default_factory=list)
    total_tokens: int = 0
    overlap_tokens: int = 0
    boundaries_used: list[str] = field(default_factory=list)
    capped_by_quota: bool = False

    @property
    def overlap_ratio(self) -> float:
        return self.overlap_tokens / self.total_tokens if self.total_tokens else 0.0

    def summary(self) -> str:
        note = " (bị giới hạn bởi quota)" if self.capped_by_quota else ""
        return (
            f"{len(self.chunks)} chunk, ~{self.total_tokens:,} token, "
            f"chồng lấn {self.overlap_ratio:.0%}{note}"
        )


def run_chunk(
    transcript: Transcript,
    policy: ChunkingPolicy | None = None,
) -> ChunkingResult:
    """Chia transcript thành các chunk cho pha EXTRACT.

    Args:
        transcript: Transcript đã qua diarize.
        policy: Ràng buộc token và quota. Mặc định ưu tiên một chunk duy nhất.

    Returns:
        ``ChunkingResult``. Với đa số cuộc họp, kết quả là **một chunk** —
        đó là đường đi tối ưu nhất về quota.
    """
    rules = policy or ChunkingPolicy()
    segments = transcript.segments

    if not segments:
        return ChunkingResult()

    token_counts = [estimate_segment_tokens(segment) for segment in segments]
    total_tokens = sum(token_counts)

    chunk_count = _decide_chunk_count(total_tokens, len(segments), rules)

    if chunk_count <= 1:
        logger.info(
            "CHUNK: toàn bộ transcript đi trong 1 lời gọi (~%s token)",
            f"{total_tokens:,}",
        )
        # Đặt tên riêng cho trường hợp một chunk: nó mang ngữ nghĩa khác hẳn
        # ("toàn bộ transcript") và giúp phân biệt ngay trong log, artifact,
        # cũng như khoá cache.
        return ChunkingResult(
            chunks=[_build_chunk("c_all", segments)],
            total_tokens=total_tokens,
            boundaries_used=[],
        )

    cut_points = _choose_cut_points(segments, token_counts, chunk_count, rules)
    chunks, overlap_tokens, boundaries = _assemble(
        segments, token_counts, cut_points, rules
    )

    capped = (
        rules.max_chunks is not None
        and chunk_count >= rules.max_chunks
        and math.ceil(total_tokens / rules.max_tokens_per_chunk) > rules.max_chunks
    )

    result = ChunkingResult(
        chunks=chunks,
        total_tokens=total_tokens,
        overlap_tokens=overlap_tokens,
        boundaries_used=boundaries,
        capped_by_quota=capped,
    )
    logger.info("CHUNK: %s", result.summary())
    if capped:
        logger.warning(
            "Quota chỉ cho phép %d chunk, thấp hơn mức lý tưởng. Mỗi chunk sẽ "
            "to hơn bình thường; nếu vượt cửa sổ ngữ cảnh, hãy chạy lại sau "
            "khi quota reset.",
            rules.max_chunks,
        )
    return result


# --------------------------------------------------------------------------- #
# Quyết định số chunk
# --------------------------------------------------------------------------- #


def _decide_chunk_count(
    total_tokens: int, segment_count: int, rules: ChunkingPolicy
) -> int:
    """Số chunk cần dùng — càng ít càng tốt.

    Chỉ chia nhỏ khi thực sự vượt trần token. Đây chính là chỗ đảo ngược so
    với bản trả phí: ở đó ta chia nhỏ để tiết kiệm tiền, ở đây ta gộp to để
    tiết kiệm request.
    """
    needed = max(1, math.ceil(total_tokens / rules.max_tokens_per_chunk))

    if rules.max_chunks is not None:
        needed = min(needed, max(1, rules.max_chunks))

    # Không tạo chunk nhỏ hơn ngưỡng tối thiểu — chunk vụn làm mất ngữ cảnh
    # nhiều hơn phần quota tiết kiệm được.
    max_by_segments = max(1, segment_count // rules.min_segments_per_chunk)
    return max(1, min(needed, max_by_segments))


# --------------------------------------------------------------------------- #
# Chọn điểm cắt theo ngữ nghĩa
# --------------------------------------------------------------------------- #


def _choose_cut_points(
    segments: Sequence[Segment],
    token_counts: Sequence[int],
    chunk_count: int,
    rules: ChunkingPolicy,
) -> list[int]:
    """Chọn ``chunk_count - 1`` vị trí cắt, ưu tiên ranh giới ngữ nghĩa.

    Trước hết tính các vị trí lý tưởng theo token, rồi dịch mỗi vị trí về
    ranh giới ngữ nghĩa gần nhất trong một cửa sổ tìm kiếm.
    """
    total = sum(token_counts)
    target = total / chunk_count

    scores = _boundary_scores(segments)
    window = max(2, len(segments) // (chunk_count * 4))

    cut_points: list[int] = []
    running = 0
    ideal_index = 1

    for index, count in enumerate(token_counts):
        running += count
        if ideal_index >= chunk_count:
            break
        if running < target * ideal_index:
            continue

        best = _best_boundary_near(
            index, scores, window, exclude=cut_points, rules=rules,
            segment_count=len(segments), chunk_index=ideal_index,
            chunk_count=chunk_count,
        )
        if best is not None:
            cut_points.append(best)
        ideal_index += 1

    return sorted(set(cut_points))


def _boundary_scores(segments: Sequence[Segment]) -> list[float]:
    """Chấm điểm "đây có phải chỗ chuyển chủ đề không" cho từng vị trí.

    Điểm cao nghĩa là cắt ở đây ít làm đứt mạch nhất.
    """
    scores = [0.0] * len(segments)

    for index in range(1, len(segments)):
        current, previous = segments[index], segments[index - 1]
        score = 0.0

        pause = current.start_ms - previous.end_ms
        if pause >= LONG_PAUSE_MS:
            score += 3.0
        elif pause >= LONG_PAUSE_MS // 2:
            score += 1.0

        if current.speaker_label != previous.speaker_label:
            score += 1.0

        opening = _strip_accents(current.text[:60])
        if any(marker in opening for marker in TOPIC_SHIFT_MARKERS):
            score += 4.0

        scores[index] = score

    return scores


def _best_boundary_near(
    index: int,
    scores: Sequence[float],
    window: int,
    *,
    exclude: Sequence[int],
    rules: ChunkingPolicy,
    segment_count: int,
    chunk_index: int,
    chunk_count: int,
) -> int | None:
    """Ranh giới ngữ nghĩa tốt nhất quanh vị trí lý tưởng.

    Khi hoà điểm, ưu tiên vị trí gần điểm lý tưởng nhất để các chunk không bị
    lệch kích thước quá nhiều.
    """
    low = max(rules.min_segments_per_chunk, index - window)
    high = min(segment_count - rules.min_segments_per_chunk, index + window)
    if low > high:
        return index if 0 < index < segment_count else None

    best_index: int | None = None
    best_key: tuple[float, int] | None = None

    for candidate in range(low, high + 1):
        if candidate in exclude:
            continue
        key = (scores[candidate], -abs(candidate - index))
        if best_key is None or key > best_key:
            best_key, best_index = key, candidate

    return best_index


# --------------------------------------------------------------------------- #
# Lắp ráp chunk kèm chồng lấn
# --------------------------------------------------------------------------- #


def _assemble(
    segments: Sequence[Segment],
    token_counts: Sequence[int],
    cut_points: Sequence[int],
    rules: ChunkingPolicy,
) -> tuple[list[TranscriptChunk], int, list[str]]:
    """Dựng chunk từ các điểm cắt, thêm chồng lấn ở mép trái.

    Chunk đầu tiên không có chồng lấn vì không có gì phía trước nó.
    """
    starts = [0, *cut_points]
    ends = [*cut_points, len(segments)]

    chunks: list[TranscriptChunk] = []
    overlap_tokens = 0
    boundaries: list[str] = []

    for order, (start, end) in enumerate(zip(starts, ends)):
        overlap_start = start
        if order > 0 and rules.overlap_segments > 0:
            overlap_start = max(0, start - rules.overlap_segments)
            overlap_tokens += sum(token_counts[overlap_start:start])
            boundaries.append(segments[start].id)

        window = segments[overlap_start:end]
        if not window:
            continue
        chunks.append(_build_chunk(f"c_{order + 1:02d}", window))

    return chunks, overlap_tokens, boundaries


def _build_chunk(chunk_id: str, segments: Sequence[Segment]) -> TranscriptChunk:
    return TranscriptChunk(
        chunk_id=chunk_id,
        segment_ids=[segment.id for segment in segments],
        start_ms=segments[0].start_ms,
        end_ms=segments[-1].end_ms,
        token_estimate=sum(estimate_segment_tokens(s) for s in segments),
    )
