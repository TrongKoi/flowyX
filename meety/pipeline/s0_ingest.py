"""Pha 0 — INGEST: biến một file có thật ngoài đời thành ``Transcript``.

Vì sao pha này tồn tại
----------------------
Trước khi có nó, toàn bộ pipeline chỉ nhận được đúng MỘT loại đầu vào: file
JSON đúng chuẩn ``schemas/transcript.py``, tức là một file phải viết tay.
Mọi thứ phía sau — 255 test, điểm grounding 1.00, 12 cạm bẫy — đều đo trên
một transcript do chính chúng ta soạn ra. Cái phễu không có miệng.

Pha này mở miệng phễu cho bốn nguồn có thật:

===============  ====================================================
Nguồn            Đặc điểm
===============  ====================================================
WebVTT (.vtt)    Zoom / Google Meet / Teams xuất ra. **Có sẵn tên
                 người nói** đính kèm từng lượt thoại.
SubRip (.srt)    Kết quả của hầu hết công cụ phụ đề và một số bản
                 xuất từ Teams.
Văn bản (.txt)   Người dùng dán từ Zoom chat, Word, hoặc gõ tay.
JSON gốc         Định dạng nội bộ, giữ nguyên đường cũ.
===============  ====================================================

Đòn bẩy lớn nhất của hệ 0 đồng nằm ở dòng đầu bảng
--------------------------------------------------
Nút thắt tài nguyên của cả dự án là **8 giờ audio/ngày từ Groq**, không phải
Gemini. Mà Zoom, Meet và Teams đều cho tải transcript về **miễn phí, không
giới hạn, kèm sẵn tên người nói**.

Nghĩa là đường VTT vừa bỏ qua hoàn toàn nút thắt Groq, vừa cho kết quả tách
người nói **tốt hơn** đường audio: Groq Whisper không làm diarization, nên
một file audio đi vào sẽ ra transcript một-nhãn-duy-nhất, và khi đó
``s2_diarize`` không có ranh giới lượt nói để bỏ phiếu — mọi công việc trong
biên bản rơi hết về "chưa phân công".

Ranh giới trách nhiệm
---------------------
Pha này **không đoán nội dung**. Nó chỉ chuẩn hoá cấu trúc, và khi không
chắc thì hạ ``asr_confidence`` rồi ghi cảnh báo, chứ không tự bịa. Nguyên
tắc "thà giữ nhãn thô còn hơn gán sai tên" của ``s2_diarize`` được giữ
nguyên ở đây.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence

from schemas.common import IdentificationMethod, Language
from schemas.transcript import (
    LanguageProfile,
    ProviderInfo,
    Segment,
    Speaker,
    Transcript,
    TranscriptMeta,
    TranscriptQuality,
)

logger = logging.getLogger(__name__)

__all__ = [
    "SourceFormat",
    "read_source_text",
    "RawCue",
    "IngestPolicy",
    "IngestWarning",
    "IngestReport",
    "IngestOutcome",
    "detect_format",
    "doc_docx",
    "parse_webvtt",
    "parse_srt",
    "parse_plain_text",
    "merge_cues",
    "run_ingest",
    "TEXT_SUFFIXES",
]

TEXT_SUFFIXES: frozenset[str] = frozenset({".vtt", ".srt", ".txt", ".md", ".json"})
"""Các đuôi file mà pha INGEST xử lý được mà không cần gọi mạng."""


# --------------------------------------------------------------------------- #
# Kiểu dữ liệu
# --------------------------------------------------------------------------- #


class SourceFormat(str, Enum):
    """Định dạng nguồn đã nhận ra."""

    NATIVE_JSON = "native_json"
    WEBVTT = "webvtt"
    SRT = "srt"
    PLAIN_TEXT = "plain_text"


@dataclass(slots=True)
class RawCue:
    """Một lượt thoại thô, chưa qua chuẩn hoá.

    ``speaker`` là ``None`` khi nguồn không đính kèm tên — trường hợp này
    phải giữ ``None`` chứ không được điền giá trị mặc định, vì phía sau cần
    phân biệt "không biết tên" với "biết là một người".
    """

    start_ms: int
    end_ms: int
    text: str
    speaker: str | None = None
    line_number: int = 0

    @property
    def duration_ms(self) -> int:
        return max(0, self.end_ms - self.start_ms)


@dataclass(frozen=True, slots=True)
class IngestPolicy:
    """Tham số điều khiển việc gộp lượt thoại và ngưỡng cảnh báo.

    Mặc định được chọn theo hành vi thật của Zoom: Zoom cắt cue rất vụn, mỗi
    cue thường 1–3 giây. Một cuộc họp 60 phút cho ra 800–1.200 cue. Nếu ánh
    xạ thẳng cue thành segment thì:

    * mỗi mệnh đề trong biên bản dẫn chứng 5–10 segment ID thay vì 1–2,
    * số token cho riêng phần đánh dấu ID tăng gấp nhiều lần,
    * và validator ở ``s7`` phải khớp quote qua ranh giới câu bị cắt vụn.

    Gộp các cue liền nhau của cùng một người là bước rẻ nhất để tránh cả ba.
    """

    merge_gap_ms: int = 2_000
    """Khoảng lặng tối đa còn cho phép gộp hai cue liền nhau."""

    max_segment_chars: int = 400
    """Trần độ dài một segment sau khi gộp — giữ để dẫn chứng còn đủ hẹp."""

    max_segment_ms: int = 60_000
    """Trần thời lượng một segment sau khi gộp."""

    words_per_minute: int = 140
    """Tốc độ nói dùng để suy ra mốc thời gian khi nguồn không có timestamp."""

    min_duration_ms: int = 60_000
    """Dưới mốc này thì cảnh báo cuộc họp quá ngắn."""

    long_gap_ms: int = 30_000
    """Khoảng lặng bị coi là bất thường, dấu hiệu ghi âm bị đứt."""


@dataclass(frozen=True, slots=True)
class IngestWarning:
    """Một phát hiện của bước tiền kiểm.

    Cố ý dùng mã riêng chứ không dùng ``WarningCode`` của biên bản: đây là
    vấn đề của **file đầu vào**, người dùng sửa được bằng cách xuất lại file,
    khác hẳn cảnh báo về nội dung cuộc họp.
    """

    code: str
    message: str
    severity: str = "medium"

    def __str__(self) -> str:
        return f"[{self.severity}] {self.code}: {self.message}"


@dataclass(slots=True)
class IngestReport:
    """Kết quả tiền kiểm, in ra cho người dùng trước khi đốt quota.

    Đây là cổng B9 trong blueprint: chặn sớm một file rác để không tốn STT và
    LLM rồi mới phát hiện biên bản vô nghĩa.
    """

    source_format: SourceFormat
    source_name: str
    checksum: str
    cue_count: int = 0
    segment_count: int = 0
    speaker_count: int = 0
    named_speaker_count: int = 0
    duration_ms: int = 0
    total_chars: int = 0
    silence_ms: int = 0
    warnings: list[IngestWarning] = field(default_factory=list)

    @property
    def has_speaker_names(self) -> bool:
        return self.named_speaker_count > 0

    @property
    def speech_ratio(self) -> float:
        if self.duration_ms <= 0:
            return 1.0
        return max(0.0, min(1.0, 1.0 - self.silence_ms / self.duration_ms))

    @property
    def blocking(self) -> list[IngestWarning]:
        """Cảnh báo nghiêm trọng tới mức nên dừng lại hỏi người dùng."""
        return [w for w in self.warnings if w.severity == "high"]

    def summary(self) -> str:
        minutes = self.duration_ms / 60_000
        names = (
            f"{self.named_speaker_count}/{self.speaker_count} có tên"
            if self.speaker_count
            else "chưa có người nói"
        )
        return (
            f"{self.source_format.value}: {self.cue_count} lượt thoại -> "
            f"{self.segment_count} segment, {names}, {minutes:.1f} phút"
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "source_format": self.source_format.value,
            "source_name": self.source_name,
            "checksum": self.checksum,
            "cue_count": self.cue_count,
            "segment_count": self.segment_count,
            "speaker_count": self.speaker_count,
            "named_speaker_count": self.named_speaker_count,
            "duration_ms": self.duration_ms,
            "total_chars": self.total_chars,
            "silence_ms": self.silence_ms,
            "speech_ratio": round(self.speech_ratio, 4),
            "warnings": [
                {"code": w.code, "severity": w.severity, "message": w.message}
                for w in self.warnings
            ],
        }


@dataclass(slots=True)
class IngestOutcome:
    """Transcript đã chuẩn hoá kèm báo cáo tiền kiểm."""

    transcript: Transcript
    report: IngestReport


# --------------------------------------------------------------------------- #
# Nhận dạng định dạng
# --------------------------------------------------------------------------- #

_TIMECODE_VTT = re.compile(
    r"(?P<start>(?:\d+:)?\d{1,2}:\d{2}[.,]\d{1,3})\s*-->\s*"
    r"(?P<end>(?:\d+:)?\d{1,2}:\d{2}[.,]\d{1,3})"
)
_TIMECODE_LOOSE = re.compile(
    r"(?P<start>(?:\d+:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)\s*-->\s*"
    r"(?P<end>(?:\d+:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)"
)
_VOICE_SPAN = re.compile(r"<v(?:\.[^\s>]+)*\s+([^>]+)>(.*?)(?:</v>|$)", re.DOTALL)
_ANY_TAG = re.compile(r"</?[cvibu](?:\.[^\s>]*)?(?:\s[^>]*)?>|</[cvibu]>")
_SRT_INDEX = re.compile(r"^\d+$")

# Dau mo dau caption bao "doi nguoi noi" - khong mang noi dung.
_CAPTION_PREFIX = re.compile(r"^(?:>{2,}|[-–—•])\s*")
# "[Ten] noi dung" hoac "(Ten) noi dung"
_BRACKET_SPEAKER = re.compile(r"^[\[(](?P<name>[^\])]{1,60})[\])]\s*:?\s*(?P<body>.*)$", re.DOTALL)
# "Ten (00:12:34): noi dung" - moc thoi gian trong ngoac, roi moi toi
# dau hai cham. Phai co mau rieng: `partition(":")` cat ngay tai dau hai
# cham DAU TIEN, ma dau do nam trong chinh moc thoi gian.
_NAME_TIMESTAMP = re.compile(
    r"^(?P<name>[^:()]{1,60}?)\s*\([\d:.,\s\-]+\)\s*:\s*(?P<body>.*)$", re.DOTALL
)
# "Ten - noi dung" / "Ten — noi dung"
_DASH_SPEAKER = re.compile(r"^(?P<name>[^\-–—]{1,60}?)\s+[-–—]\s+(?P<body>.+)$", re.DOTALL)


_BOM_ENCODINGS: tuple[tuple[bytes, str], ...] = (
    (b"\xef\xbb\xbf", "utf-8-sig"),
    (b"\xff\xfe\x00\x00", "utf-32-le"),
    (b"\x00\x00\xfe\xff", "utf-32-be"),
    (b"\xff\xfe", "utf-16-le"),
    (b"\xfe\xff", "utf-16-be"),
)
"""Bảng mã nhận ra được từ BOM. Thứ tự quan trọng: BOM của UTF-32-LE bắt đầu
bằng đúng hai byte của UTF-16-LE, nên phải thử bản dài trước."""

_FALLBACK_ENCODINGS: tuple[str, ...] = ("utf-8", "cp1258", "cp1252", "latin-1")
"""Chuỗi thử khi không có BOM.

``cp1258`` là bảng mã tiếng Việt của Windows — hiếm nhưng vẫn gặp ở file cũ.
``latin-1`` đứng cuối vì nó **không bao giờ thất bại**: mọi chuỗi byte đều
giải mã được. Nó là lưới an toàn để chương trình không sập, đổi lại chữ có
dấu sẽ sai. Cảnh báo được ghi lại khi phải dùng tới nó.
"""


# Chữ ký ZIP. Mọi file .docx đều là một kho ZIP bắt đầu bằng bốn byte này.
_ZIP_MAGIC = b"PK\x03\x04"


def doc_docx(path: Path) -> str:
    """Rút văn bản từ một file ``.docx`` (mục 8.1).

    ``.docx`` là một kho ZIP chứa ``word/document.xml``. Hàm này mở kho,
    đọc đúng file đó, rồi lấy nội dung từng thẻ ``<w:p>`` (một đoạn) ghép
    lại thành các dòng.

    **Vì sao không dùng ``python-docx``.** Thư viện đó kéo theo ``lxml``,
    một gói có phần biên dịch sẵn theo từng nền tảng. Meety hiện chạy
    được chỉ với thư viện chuẩn, và giữ được điều đó nghĩa là ai clone
    repo về cũng chạy được ngay — không có bước "cài đặt thất bại trên
    máy của tôi" vào đúng hôm trước ngày thi.

    Thứ cần ở đây cũng rất hẹp: lấy ra dòng chữ, không phải giữ định dạng.
    Biên bản họp dán vào Word vẫn là ``Tên: nội dung`` trên từng dòng, và
    parser văn bản thuần đã biết đọc dạng đó.

    **Cách đọc đoạn.** Mỗi ``<w:p>`` là một đoạn; văn bản nằm rải trong
    nhiều thẻ ``<w:t>`` bên trong nó, vì Word cắt đoạn thành nhiều "run"
    mỗi khi định dạng đổi — chỉ cần in đậm một chữ giữa câu là câu đó vỡ
    làm ba. Nên phải ghép mọi ``<w:t>`` trong cùng một ``<w:p>`` lại, nếu
    không thì một câu sẽ thành ba dòng và người nói ở đầu câu bị rớt.

    ``<w:tab>`` và ``<w:br>`` đổi thành khoảng trắng và xuống dòng, để
    bảng đơn giản không bị dính chữ vào nhau.
    """
    import xml.etree.ElementTree as ET
    import zipfile

    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    try:
        with zipfile.ZipFile(path) as kho:
            xml = kho.read("word/document.xml")
    except KeyError as exc:
        raise ValueError(
            f"{path.name} là file ZIP nhưng không chứa word/document.xml — "
            "có thể là .zip thường hoặc .docx hỏng."
        ) from exc
    except zipfile.BadZipFile as exc:
        raise ValueError(f"{path.name} không mở được như một file .docx.") from exc

    goc = ET.fromstring(xml)
    dong: list[str] = []
    for doan in goc.iter(f"{W}p"):
        phan: list[str] = []
        for o in doan.iter():
            if o.tag == f"{W}t":
                phan.append(o.text or "")
            elif o.tag == f"{W}tab":
                phan.append(" ")
            elif o.tag == f"{W}br":
                phan.append("\n")
        cau = "".join(phan).strip()
        if cau:
            dong.append(cau)
    return "\n".join(dong)


def read_source_text(path: Path) -> tuple[str, str]:
    """Đọc file transcript, tự dò bảng mã.

    Vì sao không dùng thẳng ``read_text(encoding="utf-8-sig")``: Zoom trên
    Windows đôi khi xuất VTT dạng **UTF-16 LE có BOM**. Đọc bằng UTF-8 sẽ ném
    ``UnicodeDecodeError: invalid start byte`` ngay ở byte đầu tiên — một
    thông báo không gợi ý gì về nguyên nhân, khiến người dùng đi nghi ngờ file
    hỏng trong khi file hoàn toàn bình thường.

    Returns:
        Cặp ``(nội dung, tên bảng mã đã dùng)``.
    """
    raw = path.read_bytes()

    # .docx trước mọi thứ khác: nó là ZIP, nên mọi bước dò bảng mã bên
    # dưới đều vô nghĩa với nó. Nhận theo NỘI DUNG (chữ ký ZIP) chứ không
    # chỉ theo đuôi file, cùng lý do với `detect_format`.
    if raw.startswith(_ZIP_MAGIC) and path.suffix.lower() in (".docx", ".docm"):
        return doc_docx(path), "docx"

    for bom, encoding in _BOM_ENCODINGS:
        if raw.startswith(bom):
            return raw.decode(encoding, errors="replace"), encoding

    # UTF-16 KHÔNG có BOM. Không bắt được ca này thì UTF-8 vẫn "thành công" —
    # byte NUL là ký tự UTF-8 hợp lệ — và trả về một chuỗi đầy ký tự NUL xen
    # kẽ. Parser không tìm thấy cue nào, còn người dùng nhận được thông báo
    # "không đọc được lượt thoại" mà không hiểu vì sao, vì file mở bằng
    # Notepad trông vẫn bình thường.
    sample = raw[:4096]
    if sample and sample.count(0) > len(sample) * 0.25:
        even_nulls = sum(1 for i in range(0, len(sample) - 1, 2) if sample[i + 1] == 0)
        encoding = "utf-16-le" if even_nulls > len(sample) // 4 else "utf-16-be"
        return raw.decode(encoding, errors="replace"), f"{encoding} (không BOM)"

    for encoding in _FALLBACK_ENCODINGS:
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue

    # Không tới được vì latin-1 luôn thành công, nhưng giữ cho rõ ý định.
    return raw.decode("utf-8", errors="replace"), "utf-8/replace"


def detect_format(text: str, *, suffix: str = "") -> SourceFormat:
    """Nhận dạng định dạng theo NỘI DUNG, đuôi file chỉ là gợi ý phụ.

    Đuôi file không đáng tin: người dùng hay đổi tên ``.vtt`` thành ``.txt``
    khi gửi qua email, và trình duyệt hay tải WebVTT về với đuôi ``.txt``.
    """
    head = text.lstrip("\ufeff").lstrip()

    if head.startswith("{") or head.startswith("["):
        return SourceFormat.NATIVE_JSON
    if head.upper().startswith("WEBVTT"):
        return SourceFormat.WEBVTT

    lines = [line.strip() for line in head.splitlines()]
    has_timecode = any(_TIMECODE_VTT.search(line) for line in lines[:400])

    if has_timecode:
        # Phân biệt SRT với VTT: SRT dùng dấu PHẨY cho mili giây và có dòng
        # số thứ tự ngay trước mỗi mốc thời gian.
        for index, line in enumerate(lines):
            match = _TIMECODE_VTT.search(line)
            if not match:
                continue
            comma_ms = "," in match.group("start")
            numbered = index > 0 and bool(_SRT_INDEX.match(lines[index - 1]))
            if comma_ms or numbered:
                return SourceFormat.SRT
            return SourceFormat.WEBVTT

    if suffix.lower() == ".srt":
        return SourceFormat.SRT
    if suffix.lower() == ".vtt":
        return SourceFormat.WEBVTT
    return SourceFormat.PLAIN_TEXT


# --------------------------------------------------------------------------- #
# Bộ phân tích timestamp
# --------------------------------------------------------------------------- #


def _parse_timecode(value: str) -> int:
    """Đổi ``HH:MM:SS.mmm`` hoặc ``MM:SS,mmm`` thành mili giây."""
    cleaned = value.strip().replace(",", ".")
    if "." in cleaned:
        clock, _, fraction = cleaned.partition(".")
        # Zoom ghi 3 chữ số, một số công cụ ghi 2. Đệm phải để "5" thành 500ms.
        milliseconds = int((fraction + "000")[:3])
    else:
        clock, milliseconds = cleaned, 0

    parts = [int(p) for p in clock.split(":")]
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours, (minutes, seconds) = 0, parts
    else:
        raise ValueError(f"Mốc thời gian không hợp lệ: {value!r}")

    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + milliseconds


# --------------------------------------------------------------------------- #
# Tách tên người nói khỏi nội dung
# --------------------------------------------------------------------------- #

_NAME_MAX_WORDS = 6
_NAME_MAX_CHARS = 48

_NON_NAME_PREFIXES: frozenset[str] = frozenset(
    {
        "agenda",
        "chu thich",
        "chu y",
        "ghi chu",
        "http",
        "https",
        "ket luan",
        "luu y",
        "muc tieu",
        "ngay",
        "nguoi tham du",
        "note",
        "noi dung",
        "thanh phan",
        "thoi gian",
        "tieu de",
        "tom tat",
        "van de",
        "dia diem",
    }
)
"""Tiền tố hay đứng trước dấu hai chấm trong biên bản nhưng KHÔNG phải tên.

Danh sách này so khớp sau khi bỏ dấu, khác với danh sách chặn trong
``nlp/vocative.py`` — ở đó phải giữ dấu vì phân biệt "Minh" với "mình".
Ở đây các cụm đều là từ ghép nhiều âm tiết nên không có nguy cơ đụng tên
riêng, và bỏ dấu giúp bắt được cả trường hợp người dùng gõ thiếu dấu.
"""


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return stripped.replace("đ", "d").replace("Đ", "D")


def _looks_like_name(candidate: str) -> bool:
    """Cụm trước dấu hai chấm có giống tên người không.

    Đây là chỗ dễ sai nhất của việc đọc transcript dạng văn bản: câu tiếng
    Việt bình thường cũng chứa dấu hai chấm ("Kết luận: lùi release"). Bộ
    lọc dưới đây cố ý CHẶT — bỏ sót một tên chỉ làm mất một phần thông tin
    gán người, còn nhận nhầm một mệnh đề thành tên sẽ đẻ ra speaker ma và
    phá vỡ toàn bộ phần trích xuất công việc.
    """
    name = candidate.strip()
    if not (0 < len(name) <= _NAME_MAX_CHARS):
        return False
    if len(name.split()) > _NAME_MAX_WORDS:
        return False
    if any(char in name for char in ".,;!?/\\|@#(){}[]<>\"'"):
        return False
    if any(char.isdigit() for char in name):
        return False

    folded = _strip_accents(name).lower().strip()
    if folded in _NON_NAME_PREFIXES:
        return False
    if any(folded.startswith(prefix + " ") for prefix in _NON_NAME_PREFIXES):
        return False

    # Tên người luôn có ít nhất một chữ cái viết hoa. Dùng ``str.isupper()``
    # chứ không dùng dải Unicode ``[A-ZÀ-Ỹ]``: dải đó BAO GỒM cả chữ thường
    # có dấu (đ, ố, ề) nên nhận nhầm hàng loạt.
    return any(char.isupper() for char in name)


def _split_speaker(text: str) -> tuple[str | None, str]:
    """Tách ``"Tên: nội dung"`` thành ``("Tên", "nội dung")``.

    Trả về ``(None, text)`` khi không tìm thấy tên đáng tin.

    Bản trước chỉ nhận đúng hai kiểu: thẻ ``<v Tên>`` của Teams và
    ``Tên: nội dung``. Mọi kiểu khác rơi hết xuống ``(None, text)``, nên
    ``speaker_count`` bị quy về 1 và cổng B9 chặn cả file — một file
    transcript hoàn toàn bình thường bị từ chối vì phần mềm xuất nó dùng
    dấu ``>>`` thay vì dấu hai chấm trần.

    Bốn kiểu được thêm, đều lấy từ file thật:

    ``>> Tên: nội dung``
        Zoom và phụ đề trực tiếp. Dấu ``>>`` là quy ước caption cho
        "đổi người nói".

    ``[Tên] nội dung`` / ``(Tên) nội dung``
        Nhiều công cụ chép lời tự động, và cả bản xuất của Otter.

    ``- Tên: nội dung``
        Bản xuất dạng danh sách.

    ``Tên - nội dung`` / ``Tên — nội dung``
        Gạch ngang thay dấu hai chấm. Chỉ nhận khi vế trái ngắn và trông
        như tên, vì gạch ngang xuất hiện rất nhiều trong câu bình thường.
    """
    stripped = text.strip()

    # Teams dùng thẻ voice span thay vì dấu hai chấm.
    voice = _VOICE_SPAN.match(stripped)
    if voice:
        return voice.group(1).strip() or None, voice.group(2).strip()

    # Dấu mở đầu của caption: ">>", ">>>", "-", "–", "•". Bỏ đi rồi xét
    # tiếp như thường — chúng chỉ báo "đổi người nói", không mang nội dung.
    stripped = _CAPTION_PREFIX.sub("", stripped, count=1).strip()

    # "[Tên] nội dung" và "(Tên) nội dung".
    bracket = _BRACKET_SPEAKER.match(stripped)
    if bracket:
        candidate = bracket.group("name").strip()
        if _looks_like_name(candidate):
            return candidate, bracket.group("body").strip()

    # Dạng "Tên (00:12:34): nội dung".
    #
    # Phải xử lý TRƯỚC ``partition(":")``. Bản cũ để nó rơi xuống
    # ``partition`` và tự tin rằng ``re.sub`` sẽ gỡ phần ngoặc ra — nhưng
    # ``partition`` cắt tại dấu hai chấm ĐẦU TIÊN, mà dấu đó nằm ngay
    # trong mốc thời gian: ``"Khôi (00"`` / ``"12:34): nội dung"``. Vế
    # trái không còn dấu ngoặc đóng nên ``re.sub`` không khớp gì cả, và
    # cả dòng rơi về ``(None, text)``. Kiểu này có trong bản xuất của
    # Zoom, nên mọi file Zoom đều bị quy về một người nói.
    stamped = _NAME_TIMESTAMP.match(stripped)
    if stamped:
        candidate = stamped.group("name").strip()
        if _looks_like_name(candidate):
            return candidate, stamped.group("body").strip()

    head, separator, tail = stripped.partition(":")
    if separator:
        candidate = re.sub(r"\((?:[^()]*)\)\s*$", "", head).strip()
        if _looks_like_name(candidate):
            return candidate, tail.strip()
        return None, stripped

    # "Tên - nội dung" / "Tên — nội dung".
    #
    # Nguy hiểm hơn hai kiểu trên vì gạch ngang có mặt khắp nơi trong câu
    # tiếng Việt, nên siết thêm: vế trái tối đa bốn từ và không kết thúc
    # bằng dấu câu. "Khôi — tôi nghĩ nên hoãn" nhận; "chúng ta nên chốt —
    # nhưng chờ Huy" không.
    dash = _DASH_SPEAKER.match(stripped)
    if dash:
        candidate = dash.group("name").strip()
        if len(candidate.split()) <= 4 and _looks_like_name(candidate):
            return candidate, dash.group("body").strip()

    return None, stripped


# --------------------------------------------------------------------------- #
# Parser WebVTT
# --------------------------------------------------------------------------- #


def parse_webvtt(text: str) -> list[RawCue]:
    """Đọc WebVTT của Zoom, Google Meet và Microsoft Teams.

    Ba nền tảng ghi tên người nói theo ba kiểu khác nhau; hàm này nhận cả ba
    và bỏ qua các khối ``NOTE``/``STYLE``/``REGION`` mà chuẩn cho phép.
    """
    cues: list[RawCue] = []
    lines = text.lstrip("\ufeff").splitlines()

    index = 0
    total = len(lines)
    while index < total:
        line = lines[index].strip()

        if not line or line.upper().startswith("WEBVTT"):
            index += 1
            continue

        if line.upper().startswith(("NOTE", "STYLE", "REGION")):
            index += 1
            while index < total and lines[index].strip():
                index += 1
            continue

        match = _TIMECODE_VTT.search(line)
        if not match:
            index += 1
            continue

        start_ms = _parse_timecode(match.group("start"))
        end_ms = _parse_timecode(match.group("end"))
        line_number = index + 1

        index += 1
        body: list[str] = []
        while index < total and lines[index].strip():
            if _TIMECODE_VTT.search(lines[index]):
                break
            body.append(lines[index].strip())
            index += 1

        payload = " ".join(body).strip()
        if not payload:
            continue

        speaker, content = _split_speaker(payload)
        content = _ANY_TAG.sub("", content).strip()
        if content:
            cues.append(
                RawCue(
                    start_ms=start_ms,
                    end_ms=max(end_ms, start_ms),
                    text=content,
                    speaker=speaker,
                    line_number=line_number,
                )
            )

    return cues


# --------------------------------------------------------------------------- #
# Parser SubRip
# --------------------------------------------------------------------------- #


def parse_srt(text: str) -> list[RawCue]:
    """Đọc SubRip. Khác VTT ở dấu phẩy cho mili giây và dòng số thứ tự."""
    cues: list[RawCue] = []
    lines = text.lstrip("\ufeff").splitlines()

    index = 0
    total = len(lines)
    while index < total:
        line = lines[index].strip()
        match = _TIMECODE_VTT.search(line)
        if not match:
            index += 1
            continue

        start_ms = _parse_timecode(match.group("start"))
        end_ms = _parse_timecode(match.group("end"))
        line_number = index + 1

        index += 1
        body: list[str] = []
        while index < total and lines[index].strip():
            if _TIMECODE_VTT.search(lines[index]):
                break
            if _SRT_INDEX.match(lines[index].strip()) and index + 1 < total:
                if _TIMECODE_VTT.search(lines[index + 1]):
                    break
            body.append(lines[index].strip())
            index += 1

        payload = " ".join(body).strip()
        if not payload:
            continue

        speaker, content = _split_speaker(payload)
        content = _ANY_TAG.sub("", content).strip()
        if content:
            cues.append(
                RawCue(
                    start_ms=start_ms,
                    end_ms=max(end_ms, start_ms),
                    text=content,
                    speaker=speaker,
                    line_number=line_number,
                )
            )

    return cues


# --------------------------------------------------------------------------- #
# Parser văn bản thuần
# --------------------------------------------------------------------------- #

_LEADING_TIMESTAMP = re.compile(
    r"^[\[\(]?\s*(?P<time>(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?)\s*[\]\)]?\s*[-–—]?\s*"
)


def parse_plain_text(text: str, *, policy: IngestPolicy | None = None) -> list[RawCue]:
    """Đọc transcript dạng văn bản, có hoặc không có mốc thời gian.

    Ba dạng được nhận:

    * ``[00:12:34] Tuấn: nội dung`` — dạng Zoom chat và hầu hết công cụ ghi
    * ``Tuấn: nội dung`` — dạng gõ tay, không có mốc thời gian
    * ``nội dung`` — dòng nối tiếp, quy về người nói của dòng trước

    Khi không có mốc thời gian, thời lượng được **suy ra** từ số từ và tốc
    độ nói giả định. Con số đó không dùng để phát audio mà chỉ để giữ THỨ TỰ
    thời gian — thứ mà quy tắc supersession ở ``s5_reconcile`` phụ thuộc vào.
    Cảnh báo ``SYNTHETIC_TIMESTAMPS`` được ghi lại để không ai nhầm nó với
    mốc thời gian thật.
    """
    rules = policy or IngestPolicy()

    # Lượt 1 — tách tên và mốc thời gian, chưa quyết định thời lượng.
    parsed: list[tuple[int, int | None, str | None, str]] = []
    last_speaker: str | None = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(("#", "---", "===", ">")):
            continue

        explicit_ms: int | None = None
        stamp = _LEADING_TIMESTAMP.match(line)
        if stamp:
            explicit_ms = _parse_timecode(stamp.group("time"))
            line = line[stamp.end() :].strip()
            if not line:
                continue

        speaker, content = _split_speaker(line)
        if speaker is None and last_speaker is not None:
            speaker = last_speaker
        if speaker is not None:
            last_speaker = speaker

        content = content.strip()
        if content:
            parsed.append((line_number, explicit_ms, speaker, content))

    # Cắt bỏ phần đầu tài liệu. Các dòng trước người nói ĐẦU TIÊN là tiêu đề,
    # thời gian, địa điểm — không phải lời thoại. Để chúng lọt vào transcript
    # thì chúng sẽ bị gán cho một người nào đó và trở thành bằng chứng giả cho
    # các mệnh đề trong biên bản.
    first_named = next(
        (i for i, (_, _, speaker, _) in enumerate(parsed) if speaker is not None),
        None,
    )
    if first_named:
        dropped = [item[3] for item in parsed[:first_named]]
        logger.debug("Bỏ %d dòng tiêu đề đầu tài liệu: %s", len(dropped), dropped)
        parsed = parsed[first_named:]

    # Lượt 2 — suy ra thời lượng, rồi kẹp lại theo mốc của lượt kế tiếp.
    cues: list[RawCue] = []
    cursor_ms = 0
    for line_number, explicit_ms, speaker, content in parsed:
        start_ms = cursor_ms if explicit_ms is None else max(explicit_ms, 0)
        spoken_ms = _estimate_duration_ms(content, rules.words_per_minute)
        end_ms = start_ms + spoken_ms
        cursor_ms = end_ms
        cues.append(
            RawCue(
                start_ms=start_ms,
                end_ms=end_ms,
                text=content,
                speaker=speaker,
                line_number=line_number,
            )
        )

    for current, following in zip(cues, cues[1:]):
        if following.start_ms > current.start_ms:
            current.end_ms = min(current.end_ms, following.start_ms)

    return cues


def _estimate_duration_ms(text: str, words_per_minute: int) -> int:
    words = max(1, len(text.split()))
    return max(1_000, int(words / words_per_minute * 60_000))


# --------------------------------------------------------------------------- #
# Gộp lượt thoại
# --------------------------------------------------------------------------- #


def merge_cues(cues: Sequence[RawCue], policy: IngestPolicy) -> list[RawCue]:
    """Gộp các cue liền nhau của cùng một người thành lượt thoại trọn vẹn.

    KHÔNG BAO GIỜ gộp qua ranh giới người nói: làm vậy sẽ gán phát biểu của
    người này cho người kia, đúng loại lỗi mà blueprint xếp là nguy hiểm
    nhất trong toàn hệ thống.
    """
    if not cues:
        return []

    merged: list[RawCue] = [
        RawCue(
            start_ms=cues[0].start_ms,
            end_ms=cues[0].end_ms,
            text=cues[0].text,
            speaker=cues[0].speaker,
            line_number=cues[0].line_number,
        )
    ]

    for cue in cues[1:]:
        current = merged[-1]
        joinable = (
            cue.speaker == current.speaker
            and cue.start_ms - current.end_ms <= policy.merge_gap_ms
            and len(current.text) + len(cue.text) + 1 <= policy.max_segment_chars
            and cue.end_ms - current.start_ms <= policy.max_segment_ms
        )
        if joinable:
            current.text = f"{current.text} {cue.text}".strip()
            current.end_ms = max(current.end_ms, cue.end_ms)
            continue

        merged.append(
            RawCue(
                start_ms=cue.start_ms,
                end_ms=max(cue.end_ms, cue.start_ms),
                text=cue.text,
                speaker=cue.speaker,
                line_number=cue.line_number,
            )
        )

    return merged


# --------------------------------------------------------------------------- #
# Dựng Transcript
# --------------------------------------------------------------------------- #


UNKNOWN_LABEL = "SPEAKER_UNKNOWN"
"""Nhãn riêng cho lời thoại không xác định được người nói.

Cố ý KHÔNG dồn về ``SPEAKER_00``. Nếu dồn, mọi câu không rõ người nói sẽ
được quy cho người xuất hiện đầu tiên — đúng loại lỗi mà blueprint xếp là
nguy hiểm nhất: gán sai người cho một cam kết. Một nhãn riêng khiến chỗ
không biết vẫn hiện ra là không biết.
"""


def _assign_labels(cues: Sequence[RawCue]) -> tuple[dict[str, str], list[str]]:
    """Ánh xạ tên người nói thành nhãn ``SPEAKER_00`` theo thứ tự xuất hiện.

    Giữ cả nhãn thô lẫn tên hiển thị là yêu cầu của schema: người dùng gán
    lại tên về sau mà không phá vỡ liên kết ``person_id``.
    """
    order: dict[str, str] = {}
    per_cue: list[str] = []

    for cue in cues:
        if cue.speaker is None:
            per_cue.append(UNKNOWN_LABEL)
            continue
        key = cue.speaker.strip()
        if key not in order:
            order[key] = f"SPEAKER_{len(order):02d}"
        per_cue.append(order[key])

    # Không có tên nào trong cả file: đây là transcript một khối, dùng nhãn
    # thô tuần tự thay vì nhãn "không biết" — không biết TÊN khác với không
    # biết có mấy người.
    if not order:
        return {}, ["SPEAKER_00"] * len(cues)

    return order, per_cue


def _detect_language_profile(cues: Sequence[RawCue]) -> LanguageProfile:
    """Đoán ngôn ngữ bằng mật độ dấu tiếng Việt — 100% Python, 0 quota."""
    text = " ".join(cue.text for cue in cues)
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return LanguageProfile()

    accented = sum(1 for c in letters if _strip_accents(c) != c)
    ratio = accented / len(letters)

    words = [w.strip(".,!?;:()\"'") for w in text.split()]
    ascii_words = [
        w for w in words if w and w.isascii() and w.isalpha() and len(w) > 2
    ]
    code_switching = len(ascii_words) >= 3 and ratio > 0.02

    if ratio < 0.01:
        return LanguageProfile(primary=Language.EN, code_switching=False)

    return LanguageProfile(
        primary=Language.VI,
        secondary=[Language.EN] if code_switching else [],
        code_switching=code_switching,
    )


def _build_segments(
    cues: Sequence[RawCue], labels: Sequence[str], *, confidence: float
) -> list[Segment]:
    segments: list[Segment] = []
    for position, (cue, label) in enumerate(zip(cues, labels), start=1):
        segments.append(
            Segment(
                id=f"s_{position:04d}",
                index=position,
                speaker_label=label,
                start_ms=cue.start_ms,
                end_ms=max(cue.end_ms, cue.start_ms),
                text=cue.text,
                text_raw=cue.text,
                asr_confidence=confidence,
            )
        )
    return segments


def _build_speakers(
    name_to_label: dict[str, str], segments: Sequence[Segment], duration_ms: int
) -> list[Speaker]:
    label_to_name = {label: name for name, label in name_to_label.items()}
    labels = sorted({segment.speaker_label for segment in segments})

    speakers: list[Speaker] = []
    for position, label in enumerate(labels):
        talk_ms = sum(s.duration_ms for s in segments if s.speaker_label == label)
        pct = round(talk_ms / duration_ms * 100, 2) if duration_ms else 0.0
        name = label_to_name.get(label)

        speakers.append(
            Speaker(
                label=label,
                person_id=f"p_{position + 1:03d}" if name else None,
                display_name=name,
                # Tên đến từ hồ sơ người tham dự của chính nền tảng họp, tức
                # là do người thật khai báo chứ không phải hệ thống suy đoán.
                # Đánh dấu MANUAL cũng khiến ``s2_diarize`` bỏ qua đúng cách
                # thay vì chạy lại phép đoán xưng hô lên dữ liệu đã chắc chắn.
                identification_method=(
                    IdentificationMethod.MANUAL
                    if name
                    else IdentificationMethod.UNIDENTIFIED
                ),
                identification_confidence=0.95 if name else 0.0,
                talk_time_ms=talk_ms,
                talk_time_pct=min(100.0, pct),
            )
        )

    return speakers


# --------------------------------------------------------------------------- #
# Tiền kiểm chất lượng
# --------------------------------------------------------------------------- #


def _run_quality_checks(
    report: IngestReport,
    cues: Sequence[RawCue],
    segments: Sequence[Segment],
    policy: IngestPolicy,
    *,
    synthetic_timestamps: bool,
) -> None:
    """Cổng chất lượng B9 — chặn file rác TRƯỚC khi tiêu quota.

    Không có bước này thì một file hỏng vẫn chạy hết pipeline, tiêu 3 request
    Gemini và trả về một biên bản trông có vẻ đúng nhưng rỗng nội dung.
    """
    if report.speaker_count <= 1:
        # CẢNH BÁO, KHÔNG CHẶN (mục 8.3).
        #
        # Trước đây đây là ``severity="high"``, nên ``report.blocking``
        # khác rỗng và CLI dừng ngay trước khi gọi LLM — không có
        # ``_minutes.json`` nào được ghi ra.
        #
        # Nhưng "chỉ một người nói" hầu như luôn là chuyện ĐỊNH DẠNG chứ
        # không phải file hỏng: bản xuất không gắn nhãn người nói, hoặc
        # gắn theo kiểu mà bộ tách chưa biết. Và kể cả khi đúng là một
        # người thật — ghi âm ghi chú cá nhân, bài giảng — thì đó vẫn là
        # đầu vào hợp lệ, vẫn trích được việc cần làm.
        #
        # Cái giá của hai hướng sai không cân nhau: chặn nhầm thì mất
        # trắng cả buổi họp; chạy tiếp thì tốn thêm vài request và người
        # dùng vẫn thấy cảnh báo trong báo cáo tiền kiểm.
        report.warnings.append(
            IngestWarning(
                code="SINGLE_SPEAKER",
                severity="medium",
                message=(
                    "Chỉ nhận ra một người nói, nên cam kết sẽ không quy được "
                    "về ai. Vẫn chạy tiếp. Muốn quy trách nhiệm rõ ràng thì "
                    "xuất transcript kèm tên người nói từ Zoom/Meet/Teams, "
                    "hoặc khai báo --attendees."
                ),
            )
        )

    orphan_count = sum(1 for s in segments if s.speaker_label == UNKNOWN_LABEL)
    if orphan_count and report.named_speaker_count:
        report.warnings.append(
            IngestWarning(
                code="UNATTRIBUTED_SPEECH",
                severity="medium",
                message=(
                    f"{orphan_count} đoạn không xác định được người nói, đã để "
                    f"nhãn {UNKNOWN_LABEL}. Chúng vẫn vào biên bản làm nội dung "
                    "nhưng sẽ không được dùng để quy trách nhiệm cho ai."
                ),
            )
        )

    if not report.has_speaker_names:
        report.warnings.append(
            IngestWarning(
                code="NO_SPEAKER_NAMES",
                severity="medium",
                message=(
                    "Nguồn không đính kèm tên người nói. Pha DIARIZE sẽ phải "
                    "đoán qua xưng hô, độ chính xác thấp hơn đáng kể."
                ),
            )
        )

    if synthetic_timestamps:
        report.warnings.append(
            IngestWarning(
                code="SYNTHETIC_TIMESTAMPS",
                severity="low",
                message=(
                    "Nguồn không có mốc thời gian; mốc trong transcript được "
                    "suy ra từ số từ. Thứ tự thời gian vẫn đúng nên quy tắc "
                    "supersession chạy được, nhưng không dùng để tua audio."
                ),
            )
        )

    if report.duration_ms < policy.min_duration_ms:
        report.warnings.append(
            IngestWarning(
                code="MEETING_TOO_SHORT",
                severity="medium",
                message=(
                    f"Cuộc họp chỉ dài {report.duration_ms / 1000:.0f} giây. "
                    "Nhiều khả năng file bị cắt hoặc xuất thiếu."
                ),
            )
        )

    if len(segments) < 3:
        # Chỉ chặn khi KHÔNG dựng được segment nào — lúc đó thật sự không
        # có gì để đưa cho LLM. Một hai segment vẫn là nội dung: cuộc họp
        # đứng ba phút, hay một ghi chú thoại, đều rơi vào đây.
        report.warnings.append(
            IngestWarning(
                code="TOO_FEW_SEGMENTS",
                severity="high" if not segments else "medium",
                message=(
                    f"Chỉ dựng được {len(segments)} segment. Kiểm tra lại định "
                    "dạng file đầu vào."
                ),
            )
        )

    gaps = [
        segments[i + 1].start_ms - segments[i].end_ms for i in range(len(segments) - 1)
    ]
    long_gaps = [g for g in gaps if g >= policy.long_gap_ms]
    report.silence_ms = sum(g for g in gaps if g > 0)

    if long_gaps:
        report.warnings.append(
            IngestWarning(
                code="LONG_SILENCE_GAPS",
                severity="low",
                message=(
                    f"{len(long_gaps)} khoảng lặng dài hơn "
                    f"{policy.long_gap_ms // 1000} giây, tổng "
                    f"{sum(long_gaps) / 1000:.0f} giây. Có thể ghi âm bị đứt "
                    "quãng hoặc transcript xuất thiếu đoạn."
                ),
            )
        )

    zero_length = sum(1 for s in segments if s.duration_ms == 0)
    if zero_length and zero_length >= len(segments) * 0.1:
        report.warnings.append(
            IngestWarning(
                code="ZERO_LENGTH_SEGMENTS",
                severity="medium",
                message=(
                    f"{zero_length} segment có thời lượng bằng 0 — mốc kết thúc "
                    "nằm trước mốc bắt đầu trong file nguồn. Tỉ lệ nói của "
                    "những người này sẽ bị tính thiếu."
                ),
            )
        )

    out_of_order = sum(
        1 for i in range(len(segments) - 1) if segments[i + 1].start_ms < segments[i].start_ms
    )
    if out_of_order:
        report.warnings.append(
            IngestWarning(
                code="TIMESTAMPS_OUT_OF_ORDER",
                severity="medium",
                message=(
                    f"{out_of_order} segment có mốc thời gian lùi so với segment "
                    "trước. Quy tắc 'phát biểu sau đè phát biểu trước' có thể sai."
                ),
            )
        )

    if report.total_chars < 200:
        # Ngưỡng 200 ký tự là ước lượng, không phải ranh giới thật: một
        # buổi đứng nhanh có thể chỉ 150 ký tự mà vẫn có đủ một quyết định
        # và hai đầu việc. Chặn cứng ở đó là vứt đi những buổi họp ngắn —
        # đúng loại mà người ADHD hay quên nhất.
        report.warnings.append(
            IngestWarning(
                code="LOW_TEXT_VOLUME",
                severity="high" if report.total_chars == 0 else "medium",
                message=(
                    f"Chỉ có {report.total_chars} ký tự nội dung. Quá ít để "
                    "trích xuất quyết định và công việc."
                ),
            )
        )


def _find_duplicate(checksum: str, artifact_root: Path | None) -> str | None:
    """Tìm cuộc họp đã nạp cùng nội dung — chống chạy lại tốn quota.

    Quét file ``ingest.json`` trong thư mục artifact thay vì thêm bảng SQLite:
    ít bề mặt thay đổi hơn, và artifact vốn đã là nguồn sự thật của checkpoint.
    """
    if artifact_root is None or not artifact_root.exists():
        return None

    for path in sorted(artifact_root.glob("*/ingest.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("checksum") == checksum:
            return path.parent.name
    return None


# --------------------------------------------------------------------------- #
# Điểm vào
# --------------------------------------------------------------------------- #


def run_ingest(
    source: Path | str,
    *,
    meta: TranscriptMeta,
    meeting_id: str,
    text: str | None = None,
    policy: IngestPolicy | None = None,
    artifact_root: Path | None = None,
) -> IngestOutcome:
    """Chuẩn hoá một file bất kỳ thành ``Transcript`` hợp lệ.

    Args:
        source: Đường dẫn file nguồn. Dùng để lấy đuôi file và tên hiển thị.
        meta: Metadata cuộc họp. ``duration_ms`` sẽ được ghi đè bằng thời
            lượng đo được từ chính transcript.
        meeting_id: Định danh cuộc họp, dùng đặt tên ``transcript_id``.
        text: Nội dung file nếu đã đọc sẵn. Bỏ trống thì hàm tự đọc từ đĩa.
        policy: Tham số gộp lượt thoại và ngưỡng cảnh báo.
        artifact_root: Thư mục artifact, dùng để phát hiện file trùng.

    Returns:
        ``IngestOutcome`` gồm transcript đã chuẩn hoá và báo cáo tiền kiểm.

    Raises:
        ValueError: Khi không dựng được segment nào từ nguồn.
    """
    rules = policy or IngestPolicy()
    path = Path(source)
    if text is not None:
        payload, encoding = text, "cung cấp sẵn"
    else:
        payload, encoding = read_source_text(path)

    checksum = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    source_format = detect_format(payload, suffix=path.suffix)

    report = IngestReport(
        source_format=source_format,
        source_name=path.name,
        checksum=checksum,
    )
    if encoding in {"latin-1", "utf-8/replace"}:
        report.warnings.append(
            IngestWarning(
                code="UNCERTAIN_ENCODING",
                severity="medium",
                message=(
                    f"Không nhận ra bảng mã, phải đọc bằng {encoding}. Chữ có "
                    "dấu nhiều khả năng bị sai. Lưu lại file dưới dạng UTF-8 "
                    "rồi chạy lại."
                ),
            )
        )
    elif encoding not in {"utf-8", "utf-8-sig", "cung cấp sẵn"}:
        logger.info("Đọc %s bằng bảng mã %s", path.name, encoding)

    if source_format is SourceFormat.NATIVE_JSON:
        transcript = Transcript.model_validate(json.loads(payload))
        report.cue_count = len(transcript.segments)
        report.segment_count = len(transcript.segments)
        report.speaker_count = len(transcript.speakers)
        report.named_speaker_count = sum(
            1 for s in transcript.speakers if s.display_name
        )
        report.duration_ms = transcript.meta.duration_ms
        report.total_chars = sum(len(s.text) for s in transcript.segments)
        return IngestOutcome(transcript=transcript, report=report)

    parsers = {
        SourceFormat.WEBVTT: parse_webvtt,
        SourceFormat.SRT: parse_srt,
    }
    if source_format in parsers:
        cues = parsers[source_format](payload)
    else:
        cues = parse_plain_text(payload, policy=rules)

    if not cues:
        raise ValueError(
            f"Không đọc được lượt thoại nào từ {path.name} "
            f"(nhận dạng là {source_format.value}). Kiểm tra lại định dạng file."
        )

    report.cue_count = len(cues)
    synthetic = source_format is SourceFormat.PLAIN_TEXT and not any(
        _LEADING_TIMESTAMP.match(line.strip()) for line in payload.splitlines()
    )

    merged = merge_cues(cues, rules)
    name_to_label, labels = _assign_labels(merged)

    # Nguồn văn bản không có chỉ số chất lượng ASR. Hạ nhẹ confidence để
    # phản ánh việc chưa kiểm chứng được, thay vì mặc định 1.0 cho oai.
    confidence = 0.95 if source_format is not SourceFormat.PLAIN_TEXT else 0.85

    segments = _build_segments(merged, labels, confidence=confidence)
    duration_ms = max(segment.end_ms for segment in segments)
    speakers = _build_speakers(name_to_label, segments, duration_ms)

    report.segment_count = len(segments)
    report.speaker_count = len(speakers)
    report.named_speaker_count = sum(1 for s in speakers if s.display_name)
    report.duration_ms = duration_ms
    report.total_chars = sum(len(s.text) for s in segments)

    _run_quality_checks(
        report, merged, segments, rules, synthetic_timestamps=synthetic
    )

    duplicate = _find_duplicate(checksum, artifact_root)
    if duplicate and duplicate != meeting_id:
        report.warnings.append(
            IngestWarning(
                code="DUPLICATE_SOURCE",
                severity="low",
                message=(
                    f"Nội dung này đã được nạp trước đó ở cuộc họp {duplicate}. "
                    "Dùng lại artifact cũ sẽ không tốn quota."
                ),
            )
        )

    quality = TranscriptQuality(
        low_confidence_segment_count=sum(1 for s in segments if s.is_low_quality),
        speech_ratio=round(report.speech_ratio, 4),
        overall_score=_overall_score(report),
    )

    transcript = Transcript(
        transcript_id=f"tr_{meeting_id}_v1",
        meeting_id=meeting_id,
        version=1,
        meta=meta.model_copy(update={"duration_ms": duration_ms}),
        provider=ProviderInfo(
            asr=f"import/{source_format.value}",
            diarization=(
                f"import/{source_format.value}" if report.has_speaker_names else None
            ),
            post_process="s0_ingest",
        ),
        language_profile=_detect_language_profile(merged),
        quality=quality,
        speakers=speakers,
        segments=segments,
    )

    logger.info("INGEST: %s", report.summary())
    for warning in report.warnings:
        logger.warning("INGEST %s", warning)

    return IngestOutcome(transcript=transcript, report=report)


def _overall_score(report: IngestReport) -> float:
    """Điểm chất lượng tổng hợp, trừ dần theo mức nghiêm trọng của cảnh báo."""
    penalties = {"high": 0.25, "medium": 0.10, "low": 0.03}
    score = 1.0
    for warning in report.warnings:
        score -= penalties.get(warning.severity, 0.05)
    return round(max(0.0, min(1.0, score)), 4)


def write_ingest_report(path: Path, report: IngestReport) -> Path:
    """Ghi báo cáo tiền kiểm ra đĩa để lần nạp sau phát hiện được trùng lặp."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path
