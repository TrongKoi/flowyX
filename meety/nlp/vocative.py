"""Nhận diện danh tính người nói từ cách xưng hô tiếng Việt.

Vì sao module này tồn tại
-------------------------
Groq Whisper không tách người nói, nên transcript đi từ đường audio chỉ có
một nhãn ``SPEAKER_00`` duy nhất. Không có tên người thì mọi công việc trong
biên bản đều rơi về "chưa phân công" — biên bản gần như vô dụng.

Diarization âm học thật (pyannote) cần GPU và chạy rất chậm trên CPU. Nhưng
tiếng Việt có một đặc điểm khai thác được miễn phí: **người Việt gọi tên nhau
liên tục trong cuộc họp**. "Anh Tuấn cập nhật giúp em", "Chị Lan bên QA thì
sao ạ" — mỗi câu như vậy là một phiếu bầu danh tính cho người nói ngay sau đó.

Toàn bộ module là Python thuần: không gọi LLM, không tốn quota, chạy được
offline, và kiểm thử được tất định.

Bốn luật bỏ phiếu
-----------------
1. **Tự xưng** ("em là Minh") — mạnh nhất, gần như chắc chắn.
2. **Được gọi tên** ("Anh Tuấn cập nhật giúp em") — người nói ở lượt kế tiếp
   rất có khả năng chính là Tuấn.
3. **Phiếu chống** — người vừa gọi tên ai đó thì gần như chắc chắn KHÔNG phải
   người đó. Luật này quan trọng không kém luật 2 vì nó loại trừ nhanh.
4. **Suy ra bằng loại trừ** — còn đúng một speaker chưa gán và một người chưa
   được gán thì ghép nốt.

Nguyên tắc bao trùm: **thà không gán còn hơn gán sai.** Gán nhầm người cho một
cam kết là lỗi tệ hơn nhiều so với để nguyên nhãn ``SPEAKER_02``.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

__all__ = [
    "HONORIFICS",
    "VocativeMention",
    "SpeakerVotes",
    "VocativeResult",
    "detect_mentions",
    "collect_votes",
    "assign_speakers",
    "SELF_INTRO_SCORE",
    "ADDRESSED_NEXT_SCORE",
    "ADDRESSED_SKIP_SCORE",
    "ADDRESSED_FAR_SCORE",
    "ADDRESSEE_SEARCH_WINDOW",
    "SPEAKER_IS_NOT_ADDRESSEE_PENALTY",
    "MIN_CONFIDENT_SCORE",
    "WEAK_EVIDENCE_SCORE",
]

# --------------------------------------------------------------------------- #
# Trọng số bỏ phiếu
# --------------------------------------------------------------------------- #

SELF_INTRO_SCORE: float = 5.0
"""Tự giới thiệu là tín hiệu mạnh nhất: "em là Minh" gần như không thể sai."""

ADDRESSED_NEXT_SCORE: float = 3.0
"""Người được gọi tên thường đáp lời ngay. Mạnh, nhưng không tuyệt đối vì
người gọi có thể nói tiếp vài câu trước khi người kia trả lời."""

ADDRESSED_SKIP_SCORE: float = 1.5
"""Phiếu cho người nói khác thứ hai sau lời gọi tên."""

ADDRESSED_FAR_SCORE: float = 0.75
"""Phiếu yếu nhất, cho người nói khác thứ ba — vẫn đủ để phá thế hoà."""

ADDRESSEE_SEARCH_WINDOW: int = 6
"""Số lượt nói tối đa nhìn về phía sau để tìm người đáp lời."""

SPEAKER_IS_NOT_ADDRESSEE_PENALTY: float = -2.5
"""Phiếu chống: người đang gọi tên X thì không phải là X. Rất ít khi sai."""

MIN_CONFIDENT_SCORE: float = 2.5
"""Ngưỡng cho lượt ghép thứ nhất. Dưới mức này thì chưa đủ căn cứ."""

WEAK_EVIDENCE_SCORE: float = 1.0
"""Ngưỡng cho lượt ghép thứ hai, CHỈ áp dụng khi biết trước danh sách tham dự.

Khi không gian tên đã bị giới hạn còn vài người, một phiếu yếu vẫn là bằng
chứng dùng được — rủi ro gán bừa thấp hơn hẳn so với lúc phải đoán từ một
tập tên mở."""

ELIMINATION_CONFIDENCE: float = 0.72
"""Độ tin cậy cho suy luận bằng loại trừ — thấp hơn hẳn bằng chứng trực tiếp."""


# --------------------------------------------------------------------------- #
# Từ vựng xưng hô
# --------------------------------------------------------------------------- #

HONORIFICS: tuple[str, ...] = (
    "anh", "chị", "em", "bạn", "cô", "chú", "bác", "sếp", "thầy", "cô giáo",
    "ông", "bà", "cậu", "dì", "mợ",
)
"""Các tiền tố xưng hô đứng trước tên riêng trong tiếng Việt."""

_SELF_PRONOUNS: tuple[str, ...] = (
    "em", "mình", "tôi", "tớ", "anh", "chị", "con", "cháu",
)

# Từ đứng sau tiền tố xưng hô nhưng KHÔNG phải tên riêng. Thiếu danh sách này,
# "anh em", "các bạn", "chị ấy" đều bị nhận nhầm thành tên người.
#
# Danh sách cố ý GIỮ NGUYÊN DẤU. Bỏ dấu trước khi so khớp sẽ gây va chạm tai
# hại giữa tên người và hư từ: "Minh" đụng "mình", "Thị" đụng "thì", "Hằng"
# đụng "hằng". Tiếng Việt phân biệt nghĩa bằng thanh điệu, nên bước chuẩn hoá
# hữu ích ở chỗ khác lại phá hỏng đúng phép so sánh này.
_STOPWORDS_AFTER_HONORIFIC: frozenset[str] = frozenset(
    {
        "em", "ấy", "ta", "này", "đó", "kia", "nó", "họ", "mình", "chúng",
        "mọi", "các", "những", "bạn", "anh", "chị", "cô", "chú", "bác",
        "ơi", "à", "ừ", "nhé", "nha", "thế", "gì", "sao", "với", "cũng",
        "thì", "là", "mà", "và", "hay", "hoặc", "nè", "đây", "được",
        "không", "chưa", "rồi", "sẽ", "đang", "đã", "cần", "phải",
        "nên", "muốn", "biết", "thấy", "nghĩ", "nói", "làm", "đi", "đến",
        "về", "cho", "từ", "trong", "ngoài", "trên", "dưới", "sau", "trước",
        "ai", "nào", "bên", "vẫn", "còn", "vừa", "mới", "ừm", "vâng", "dạ",
    }
)

# --------------------------------------------------------------------------- #
# Biểu thức chính quy
# --------------------------------------------------------------------------- #

def _strip_accents(text: str) -> str:
    """Bỏ dấu để so khớp danh sách chặn một cách ổn định."""
    decomposed = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", stripped)


_HONORIFIC_GROUP = "|".join(sorted(HONORIFICS, key=len, reverse=True))

# Mẫu tự xưng chạy trên văn bản ĐÃ BỎ DẤU (để khớp được cả "là" lẫn "la" do
# ASR đôi khi trả về thiếu dấu), nên chính danh sách đại từ cũng phải ở dạng
# bỏ dấu. Dùng bản có dấu ở đây sẽ khiến mẫu không bao giờ khớp.
_SELF_GROUP = "|".join(
    sorted({_strip_accents(p) for p in _SELF_PRONOUNS}, key=len, reverse=True)
)

# Tên riêng tiếng Việt: chữ cái đầu viết hoa. Không dùng lớp ký tự kiểu
# [A-ZÀ-Ỹ] vì dải Unicode À-Ỹ bao gồm cả chữ thường tiếng Việt (đ, ố, ề...),
# khiến "điểm" và "đối" bị nhận nhầm thành tên riêng. Dùng \w rồi lọc bằng
# str.isupper() của Python, vốn hiểu Unicode đúng.
_NAME_TOKEN = r"(?P<name>\w+(?:\s+\w+){0,2})"

_VOCATIVE_PATTERN = re.compile(
    rf"\b(?P<honorific>{_HONORIFIC_GROUP})\s+{_NAME_TOKEN}",
    re.IGNORECASE | re.UNICODE,
)

_SELF_INTRO_PATTERN = re.compile(
    rf"\b(?P<pronoun>{_SELF_GROUP})\s+(?:la|ten\s+la|ten)\s+{_NAME_TOKEN}",
    re.IGNORECASE | re.UNICODE,
)

_WORD_PATTERN = re.compile(r"\w+", re.UNICODE)


def _looks_like_proper_noun(token: str) -> bool:
    """Một từ có phải tên riêng không.

    Ba điều kiện: viết hoa chữ đầu, không viết hoa toàn bộ (loại "API", "QA"),
    và không nằm trong danh sách hư từ hay theo sau tiền tố xưng hô.
    """
    if len(token) < 2:
        return False
    if not token[0].isupper() or token.isupper():
        return False
    # So khớp giữ nguyên dấu — xem ghi chú ở _STOPWORDS_AFTER_HONORIFIC.
    return token.lower() not in _STOPWORDS_AFTER_HONORIFIC


def _clean_name(raw: str) -> str | None:
    """Cắt cụm sau tiền tố xưng hô thành tên riêng, hoặc trả ``None``.

    "Tuấn cập nhật giúp em" phải cho ra "Tuấn": lấy các từ viết hoa liên tiếp
    ngay đầu cụm rồi dừng ngay khi gặp từ thường.
    """
    tokens = _WORD_PATTERN.findall(raw)
    kept: list[str] = []
    for token in tokens:
        if _looks_like_proper_noun(token):
            kept.append(token)
        else:
            break
    if not kept:
        return None
    return " ".join(kept)


# --------------------------------------------------------------------------- #
# Kiểu dữ liệu
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class VocativeMention:
    """Một lần một cái tên được nhắc tới trong transcript."""

    name: str
    segment_id: str
    segment_index: int
    speaker_label: str
    kind: str
    """``"vocative"`` (gọi tên người khác) hoặc ``"self_intro"`` (tự xưng)."""

    def __str__(self) -> str:
        return f"{self.name} ({self.kind} @ {self.segment_id})"


@dataclass(slots=True)
class SpeakerVotes:
    """Bảng điểm của một nhãn speaker."""

    label: str
    scores: dict[str, float] = field(default_factory=dict)
    evidence: dict[str, list[str]] = field(default_factory=dict)
    kinds: dict[str, set[str]] = field(default_factory=dict)
    """Loại phiếu đã đóng góp cho mỗi tên.

    Ghi nhận tường minh thay vì suy ngược từ điểm số: nhiều phiếu "được gọi
    tên" cộng lại có thể vượt trọng số của một phiếu "tự xưng", khiến việc
    đoán loại phiếu từ tổng điểm cho ra kết quả sai.
    """

    def add(
        self,
        name: str,
        points: float,
        segment_id: str | None = None,
        kind: str | None = None,
    ) -> None:
        self.scores[name] = self.scores.get(name, 0.0) + points
        if kind:
            self.kinds.setdefault(name, set()).add(kind)
        if segment_id and points > 0:
            self.evidence.setdefault(name, [])
            if segment_id not in self.evidence[name]:
                self.evidence[name].append(segment_id)

    def best(self) -> tuple[str, float] | None:
        if not self.scores:
            return None
        name, score = max(self.scores.items(), key=lambda pair: pair[1])
        return (name, score) if score > 0 else None

    def is_ruled_out(self, name: str) -> bool:
        """Bằng chứng đã phủ định khả năng nhãn này mang tên đó chưa.

        Phiếu chống ("người gọi tên X không phải X") gần như không bao giờ
        sai, nên một điểm số âm là căn cứ loại trừ đáng tin.
        """
        return self.scores.get(name, 0.0) < 0

    def margin(self) -> float:
        """Khoảng cách giữa ứng viên đầu và ứng viên thứ hai.

        Khoảng cách sát nhau nghĩa là bằng chứng chưa đủ phân định, dù điểm
        tuyệt đối có cao đến đâu.
        """
        positive = sorted(
            (s for s in self.scores.values() if s > 0), reverse=True
        )
        if not positive:
            return 0.0
        if len(positive) == 1:
            return positive[0]
        return positive[0] - positive[1]


@dataclass(slots=True)
class VocativeResult:
    """Kết quả gán danh tính cho toàn bộ nhãn speaker."""

    assignments: dict[str, str] = field(default_factory=dict)
    confidences: dict[str, float] = field(default_factory=dict)
    methods: dict[str, str] = field(default_factory=dict)
    evidence: dict[str, list[str]] = field(default_factory=dict)
    mentions: list[VocativeMention] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)

    @property
    def discovered_names(self) -> set[str]:
        """Mọi tên xuất hiện trong transcript, kể cả tên không gán được."""
        return {mention.name for mention in self.mentions}

    def summary(self) -> str:
        if not self.assignments:
            return "Không gán được nhãn speaker nào."
        parts = [
            f"{label} -> {name} ({self.confidences.get(label, 0):.0%}, "
            f"{self.methods.get(label, '?')})"
            for label, name in sorted(self.assignments.items())
        ]
        return " | ".join(parts)


# --------------------------------------------------------------------------- #
# Bước 1 — Dò tên được nhắc tới
# --------------------------------------------------------------------------- #


def detect_mentions(
    segments: Sequence[Mapping[str, object]],
    *,
    known_names: Iterable[str] | None = None,
) -> list[VocativeMention]:
    """Quét transcript, tìm mọi lần một cái tên được nhắc tới.

    Args:
        segments: Dãy segment, mỗi phần tử cần có ``id``, ``index``,
            ``speaker_label`` và ``text``.
        known_names: Danh sách người tham dự nếu biết trước. Có nó thì mọi
            tên lạ bị loại ngay, giúp thu hẹp bài toán rất nhiều.

    Returns:
        Danh sách ``VocativeMention`` theo thứ tự xuất hiện.
    """
    allowed: set[str] | None = None
    if known_names is not None:
        allowed = {_strip_accents(str(n)) for n in known_names}

    mentions: list[VocativeMention] = []

    for segment in segments:
        text = str(segment.get("text", ""))
        segment_id = str(segment.get("id", ""))
        segment_index = int(segment.get("index", 0) or 0)
        speaker_label = str(segment.get("speaker_label", ""))

        for match in _SELF_INTRO_PATTERN.finditer(_normalise_for_self_intro(text)):
            name = _resolve_match_name(text, match)
            if name is None or not _is_allowed(name, allowed):
                continue
            mentions.append(
                VocativeMention(
                    name=name,
                    segment_id=segment_id,
                    segment_index=segment_index,
                    speaker_label=speaker_label,
                    kind="self_intro",
                )
            )

        for match in _VOCATIVE_PATTERN.finditer(text):
            name = _clean_name(match.group("name"))
            if name is None or not _is_allowed(name, allowed):
                continue
            mentions.append(
                VocativeMention(
                    name=name,
                    segment_id=segment_id,
                    segment_index=segment_index,
                    speaker_label=speaker_label,
                    kind="vocative",
                )
            )

    return mentions


def _normalise_for_self_intro(text: str) -> str:
    """Bỏ dấu phần hư từ để mẫu tự xưng khớp được cả "là" lẫn "la".

    Giữ nguyên chữ hoa để bước lấy tên vẫn nhận ra danh từ riêng.
    """
    decomposed = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", stripped)


def _resolve_match_name(original: str, match: re.Match[str]) -> str | None:
    """Lấy tên từ văn bản GỐC dựa trên vị trí khớp ở văn bản đã bỏ dấu.

    Bỏ dấu không làm đổi số ký tự (chuẩn hoá NFD rồi lọc dấu tổ hợp rồi NFC),
    nên chỉ số ký tự vẫn ánh xạ được về chuỗi gốc và ta giữ được dấu tiếng
    Việt trong tên.
    """
    start, end = match.span("name")
    if end <= len(original):
        return _clean_name(original[start:end])
    return _clean_name(match.group("name"))


def _is_allowed(name: str, allowed: set[str] | None) -> bool:
    if allowed is None:
        return True
    return _strip_accents(name) in allowed


# --------------------------------------------------------------------------- #
# Bước 2 — Bỏ phiếu
# --------------------------------------------------------------------------- #


def collect_votes(
    segments: Sequence[Mapping[str, object]],
    mentions: Sequence[VocativeMention],
) -> dict[str, SpeakerVotes]:
    """Quy các lần nhắc tên thành bảng điểm cho từng nhãn speaker."""
    labels = [str(s.get("speaker_label", "")) for s in segments]
    votes: dict[str, SpeakerVotes] = {
        label: SpeakerVotes(label=label) for label in dict.fromkeys(labels) if label
    }

    position_of: dict[str, int] = {
        str(segment.get("id", "")): index for index, segment in enumerate(segments)
    }

    for mention in mentions:
        if mention.kind == "self_intro":
            # Người tự giới thiệu chính là người đang nói.
            if mention.speaker_label in votes:
                votes[mention.speaker_label].add(
                    mention.name,
                    SELF_INTRO_SCORE,
                    mention.segment_id,
                    kind="self_intro",
                )
            continue

        # Luật phiếu chống: người gọi tên X thì không phải X.
        if mention.speaker_label in votes:
            votes[mention.speaker_label].add(
                mention.name, SPEAKER_IS_NOT_ADDRESSEE_PENALTY
            )

        index = position_of.get(mention.segment_id)
        if index is None:
            continue

        _spread_addressee_votes(segments, votes, mention, index)

    return votes


def _spread_addressee_votes(
    segments: Sequence[Mapping[str, object]],
    votes: dict[str, SpeakerVotes],
    mention: VocativeMention,
    index: int,
) -> None:
    """Rải phiếu cho các lượt nói kế tiếp, trọng số giảm dần.

    Người được gọi tên KHÔNG phải lúc nào cũng đáp ngay. Trong cuộc họp thật,
    thường có người khác chen vào trước: "Khoan anh Hùng ơi..." rồi Tuấn nói
    xen một câu, mãi hai lượt sau Hùng mới trả lời.

    Vì vậy phiếu được rải cho vài người nói khác nhau kế tiếp với trọng số
    giảm dần, thay vì dồn hết cho lượt liền sau. Cơ chế ghép cặp độc quyền ở
    bước sau sẽ tự phân xử: người đã có bằng chứng mạnh cho tên khác sẽ nhường
    lại cái tên này cho ứng viên còn lại.
    """
    seen_labels: set[str] = {mention.speaker_label}
    weights = (ADDRESSED_NEXT_SCORE, ADDRESSED_SKIP_SCORE, ADDRESSED_FAR_SCORE)
    rank = 0

    for offset in range(1, ADDRESSEE_SEARCH_WINDOW + 1):
        target = index + offset
        if target >= len(segments) or rank >= len(weights):
            break

        target_label = str(segments[target].get("speaker_label", ""))
        if not target_label or target_label in seen_labels:
            continue

        seen_labels.add(target_label)
        votes[target_label].add(
            mention.name,
            weights[rank],
            str(segments[target].get("id", "")),
            kind="vocative",
        )
        rank += 1


# --------------------------------------------------------------------------- #
# Bước 3 — Ghép cặp
# --------------------------------------------------------------------------- #


def assign_speakers(
    segments: Sequence[Mapping[str, object]],
    *,
    known_names: Iterable[str] | None = None,
    min_score: float = MIN_CONFIDENT_SCORE,
) -> VocativeResult:
    """Gán danh tính cho các nhãn speaker dựa trên cách xưng hô.

    Thuật toán chạy ba lượt, mỗi lượt nới lỏng hơn lượt trước:

    1. **Bằng chứng mạnh** — ghép tham lam các cặp đạt ``min_score``.
    2. **Bằng chứng yếu** — chỉ khi biết trước danh sách tham dự: chấp nhận
       điểm thấp hơn, vì không gian tên đã bị giới hạn nên rủi ro gán bừa
       thấp hơn hẳn.
    3. **Loại trừ** — còn đúng một nhãn và một tên chưa dùng thì ghép nốt.

    Args:
        segments: Dãy segment có ``id``, ``index``, ``speaker_label``, ``text``.
        known_names: Danh sách người tham dự nếu biết trước.
        min_score: Ngưỡng điểm cho lượt ghép thứ nhất.

    Returns:
        ``VocativeResult``. Nhãn nào không đủ tin cậy sẽ nằm trong
        ``unresolved`` và **không** xuất hiện trong ``assignments``.
    """
    mentions = detect_mentions(segments, known_names=known_names)
    votes = collect_votes(segments, mentions)
    result = VocativeResult(mentions=list(mentions))

    taken_labels: set[str] = set()
    taken_names: set[str] = set()

    _greedy_match(votes, result, taken_labels, taken_names, threshold=min_score)

    if known_names is not None:
        _greedy_match(
            votes,
            result,
            taken_labels,
            taken_names,
            threshold=WEAK_EVIDENCE_SCORE,
            allowed_names={str(n) for n in known_names},
        )
        _assign_by_elimination(votes, known_names, result, taken_labels, taken_names)

    result.unresolved = sorted(
        label for label in votes if label not in result.assignments
    )
    return result


def _greedy_match(
    votes: Mapping[str, SpeakerVotes],
    result: VocativeResult,
    taken_labels: set[str],
    taken_names: set[str],
    *,
    threshold: float,
    allowed_names: set[str] | None = None,
) -> None:
    """Ghép tham lam theo điểm giảm dần, mỗi nhãn và mỗi tên chỉ dùng một lần.

    Tính độc quyền là điều làm thuật toán này hoạt động: khi hai nhãn cùng
    tranh một cái tên, nhãn có bằng chứng mạnh hơn thắng, và nhãn thua tự
    động nhường lại cái tên đó — mở đường cho nó nhận một tên khác ở lượt sau.
    """
    candidates: list[tuple[float, float, str, str]] = []

    for label, vote in votes.items():
        if label in taken_labels:
            continue
        for name, score in vote.scores.items():
            if score < threshold or name in taken_names:
                continue
            if allowed_names is not None and name not in allowed_names:
                continue
            candidates.append((score, vote.margin(), label, name))

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)

    for score, _margin, label, name in candidates:
        if label in taken_labels or name in taken_names:
            continue
        taken_labels.add(label)
        taken_names.add(name)
        result.assignments[label] = name
        result.confidences[label] = _score_to_confidence(score)
        result.methods[label] = _method_for(votes[label], name)
        result.evidence[label] = votes[label].evidence.get(name, [])


def _method_for(vote: SpeakerVotes, name: str) -> str:
    """Loại bằng chứng mạnh nhất đã dẫn tới phép gán này."""
    kinds = vote.kinds.get(name, set())
    return "self_intro" if "self_intro" in kinds else "vocative"


def _score_to_confidence(score: float) -> float:
    """Quy điểm bỏ phiếu về khoảng 0–1 để hiển thị.

    Thang bão hoà: điểm càng cao càng tiệm cận 0,95 chứ không bao giờ đạt 1,0.
    Đây là suy luận gián tiếp, không phải nhận dạng giọng nói, nên không có
    lý do gì để tuyên bố chắc chắn tuyệt đối.
    """
    return round(min(0.95, 0.55 + 0.08 * score), 2)


def _assign_by_elimination(
    votes: Mapping[str, SpeakerVotes],
    known_names: Iterable[str] | None,
    result: VocativeResult,
    taken_labels: set[str],
    taken_names: set[str],
) -> None:
    """Còn đúng một nhãn và một tên chưa dùng thì ghép nốt.

    Chỉ áp dụng khi biết trước danh sách người tham dự và số lượng khớp nhau.
    Đây là suy luận gián tiếp nên độ tin cậy được đặt thấp hơn hẳn.
    """
    if known_names is None:
        return

    remaining_labels = [label for label in votes if label not in taken_labels]
    remaining_names = [str(n) for n in known_names if str(n) not in taken_names]

    if len(remaining_labels) != 1 or len(remaining_names) != 1:
        return

    label, name = remaining_labels[0], remaining_names[0]

    # Không gán nếu chính bằng chứng đã phủ định khả năng này.
    if votes[label].scores.get(name, 0.0) < 0:
        return

    result.assignments[label] = name
    result.confidences[label] = ELIMINATION_CONFIDENCE
    result.methods[label] = "attendee_list_elimination"
    result.evidence[label] = []
