"""Adapter Groq Whisper — provider ASR chính của bản POC 0 đồng.

Vì sao Groq ``whisper-large-v3`` chứ không phải ``turbo``: hạn mức free tier
của hai model **giống hệt nhau** (cùng giây audio, cùng RPD), nên không có
lý do gì hy sinh chất lượng tiếng Việt để đổi lấy tốc độ mà bạn không phải
trả tiền. Bản ``turbo`` là distilled và kém rõ rệt trên ngôn ngữ không phải
tiếng Anh.

Ba tham số quyết định chất lượng với audio họp tiếng Việt có chêm tiếng Anh
được đặt ở ``TranscribeOptions`` và giải thích ngay tại chỗ.
"""

from __future__ import annotations

import datetime as dt
import logging
import math
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from providers.base import (
    ASRProvider,
    ProviderError,
    RateLimitError,
    TranscriptionResult,
    merge_headers,
)
from schemas.common import IdentificationMethod, Language
from schemas.transcript import (
    HIGH_NO_SPEECH_THRESHOLD,
    LOW_LOGPROB_THRESHOLD,
    LanguageProfile,
    ProviderInfo,
    Segment,
    Speaker,
    Transcript,
    TranscriptMeta,
    TranscriptQuality,
    Word,
)

logger = logging.getLogger(__name__)

__all__ = [
    "TranscribeOptions",
    "GroqWhisperProvider",
    "build_transcript",
    "DEFAULT_MODEL",
    "DEFAULT_GLOSSARY",
]

DEFAULT_MODEL = "whisper-large-v3"

MAX_UPLOAD_BYTES = 24 * 1024 * 1024
"""Ngưỡng an toàn dưới giới hạn upload của free tier (~25MB)."""

CHUNK_SECONDS = 600
"""Độ dài mỗi đoạn khi phải chia nhỏ file. 10 phút là cân bằng tốt giữa số
request tiêu tốn và rủi ro mất ngữ cảnh ở mép."""

CHUNK_OVERLAP_SECONDS = 2
"""Chồng lấn nhỏ để không cắt mất từ nằm đúng ranh giới."""

DEFAULT_GLOSSARY: tuple[str, ...] = (
    "deploy", "staging", "backlog", "sprint", "release", "API", "index",
    "cache", "QA", "RC", "timeout", "rollback", "campaign", "store",
    "build", "merge", "submit", "review", "scope", "deadline",
)


@dataclass(slots=True)
class TranscribeOptions:
    """Cấu hình gọi Whisper, tối ưu cho audio họp tiếng Việt."""

    language: str = "vi"
    """Đặt cứng ``vi`` chứ không để tự nhận diện.

    Auto-detect trên audio hỗn hợp Việt–Anh khiến Whisper nhảy ngôn ngữ giữa
    chừng và đôi khi chuyển sang chế độ *dịch* thay vì *phiên âm*.
    """

    glossary: tuple[str, ...] = DEFAULT_GLOSSARY
    """Đòn bẩy chất lượng rẻ nhất trong toàn hệ thống.

    Whisper dùng ``prompt`` làm ngữ cảnh giải mã, nên đưa danh sách thuật ngữ
    tiếng Anh và tên nhân sự vào đây giảm mạnh lỗi phiên âm danh từ riêng —
    thứ quan trọng hơn WER tổng thể cho bài toán biên bản.
    """

    speaker_names: tuple[str, ...] = ()
    temperature: float = 0.0
    """Chống ảo giác của Whisper trên các đoạn im lặng."""

    max_upload_bytes: int = MAX_UPLOAD_BYTES
    chunk_seconds: int = CHUNK_SECONDS

    def build_prompt(self) -> str:
        terms = [*self.glossary, *self.speaker_names]
        if not terms:
            return ""
        return (
            "Cuộc họp công việc bằng tiếng Việt, có chêm thuật ngữ tiếng Anh. "
            "Các từ thường xuất hiện: " + ", ".join(terms) + "."
        )


@dataclass(slots=True)
class _AudioChunk:
    path: Path
    offset_seconds: float
    temporary: bool = False


class GroqWhisperProvider(ASRProvider):
    """Adapter cho Groq Speech-to-Text.

    SDK được import trễ để module vẫn dùng được (cho ``build_transcript``)
    trên máy chưa cài ``groq``.
    """

    name = "groq"

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        timeout_seconds: float = 300.0,
    ) -> None:
        try:
            from groq import Groq
        except ImportError as exc:
            raise ProviderError("Chưa cài SDK Groq. Chạy: pip install groq") from exc

        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ProviderError(
                "Thiếu GROQ_API_KEY. Lấy khoá miễn phí tại "
                "https://console.groq.com/keys rồi đặt vào file .env"
            )

        self.model = model
        self._client = Groq(api_key=key, timeout=timeout_seconds)

    def transcribe(
        self,
        audio_path: str,
        *,
        language: str = "vi",
        prompt: str | None = None,
        temperature: float = 0.0,
        options: TranscribeOptions | None = None,
    ) -> TranscriptionResult:
        """Phiên âm file audio, tự chia nhỏ nếu vượt giới hạn upload."""
        opts = options or TranscribeOptions(
            language=language, temperature=temperature
        )
        source = Path(audio_path)
        if not source.exists():
            raise ProviderError(f"Không tìm thấy file audio: {source}")

        effective_prompt = prompt if prompt is not None else opts.build_prompt()

        segments: list[dict[str, Any]] = []
        words: list[dict[str, Any]] = []
        texts: list[str] = []
        headers: dict[str, str] = {}
        duration = 0.0
        detected_language = opts.language

        for chunk in self._split_if_needed(source, opts):
            try:
                raw = self._transcribe_one(chunk.path, opts, effective_prompt)
            finally:
                if chunk.temporary:
                    chunk.path.unlink(missing_ok=True)

            headers = raw.get("_headers", headers)
            detected_language = raw.get("language", detected_language)
            texts.append((raw.get("text") or "").strip())
            duration = max(
                duration, chunk.offset_seconds + float(raw.get("duration") or 0.0)
            )

            for seg in raw.get("segments") or []:
                shifted = dict(seg)
                shifted["start"] = float(seg.get("start", 0.0)) + chunk.offset_seconds
                shifted["end"] = float(seg.get("end", 0.0)) + chunk.offset_seconds
                segments.append(shifted)

            for word in raw.get("words") or []:
                shifted = dict(word)
                shifted["start"] = float(word.get("start", 0.0)) + chunk.offset_seconds
                shifted["end"] = float(word.get("end", 0.0)) + chunk.offset_seconds
                words.append(shifted)

        segments.sort(key=lambda s: s["start"])
        words.sort(key=lambda w: w["start"])

        return TranscriptionResult(
            text=" ".join(t for t in texts if t),
            language=detected_language,
            duration_seconds=duration,
            segments=segments,
            words=words,
            model=self.model,
            headers=headers,
        )

    def _transcribe_one(
        self, path: Path, opts: TranscribeOptions, prompt: str
    ) -> dict[str, Any]:
        try:
            with path.open("rb") as handle:
                response = self._client.audio.transcriptions.create(
                    file=(path.name, handle.read()),
                    model=self.model,
                    language=opts.language,
                    prompt=prompt or None,
                    temperature=opts.temperature,
                    response_format="verbose_json",
                    timestamp_granularities=["word", "segment"],
                )
        except Exception as exc:
            raise self._translate_error(exc) from exc

        if hasattr(response, "model_dump"):
            payload = response.model_dump()
        elif isinstance(response, dict):
            payload = dict(response)
        else:
            payload = {
                "text": getattr(response, "text", ""),
                "language": getattr(response, "language", opts.language),
                "duration": getattr(response, "duration", 0.0),
                "segments": getattr(response, "segments", []) or [],
                "words": getattr(response, "words", []) or [],
            }

        payload["_headers"] = merge_headers(getattr(response, "_headers", None))
        return payload

    def _split_if_needed(
        self, source: Path, opts: TranscribeOptions
    ) -> Iterator[_AudioChunk]:
        """Chia file thành các đoạn vừa giới hạn upload.

        Đây là chia theo DUNG LƯỢNG file, không phải theo quota: hạn mức của
        Groq tính bằng giây audio, nên chia nhỏ không làm tốn thêm quota
        audio, chỉ tốn thêm request (vốn rất dư dả ở 2.000 RPD).
        """
        size = source.stat().st_size
        if size <= opts.max_upload_bytes:
            yield _AudioChunk(path=source, offset_seconds=0.0)
            return

        if shutil.which("ffmpeg") is None:
            raise ProviderError(
                f"File {source.name} nặng {size / 1e6:.0f}MB, vượt giới hạn upload "
                f"{opts.max_upload_bytes / 1e6:.0f}MB, nhưng không tìm thấy ffmpeg "
                "để chia nhỏ. Cài ffmpeg hoặc nén audio xuống mono 16kHz trước."
            )

        duration = _probe_duration(source)
        parts = math.ceil(duration / opts.chunk_seconds)
        logger.info(
            "File %s dài %.0fs, chia thành %d đoạn", source.name, duration, parts
        )

        tmpdir = Path(tempfile.mkdtemp(prefix="whisper_chunks_"))
        try:
            for index in range(parts):
                start = max(0.0, index * opts.chunk_seconds - CHUNK_OVERLAP_SECONDS)
                target = tmpdir / f"part_{index:03d}.wav"
                _extract_segment(source, target, start, opts.chunk_seconds
                                 + CHUNK_OVERLAP_SECONDS)
                yield _AudioChunk(path=target, offset_seconds=start, temporary=True)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @staticmethod
    def _translate_error(exc: Exception) -> ProviderError:
        message = str(exc)
        status = getattr(exc, "status_code", None)
        if status == 429 or "429" in message or "rate limit" in message.lower():
            return RateLimitError(
                f"Groq chạm hạn mức: {message[:200]}", retry_after_seconds=60.0
            )
        return ProviderError(f"Groq lỗi: {message[:300]}")


def _probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise ProviderError(f"Không đọc được độ dài của {path.name}") from exc


def _extract_segment(source: Path, target: Path, start: float, length: float) -> None:
    """Trích một đoạn và chuẩn hoá luôn về mono 16kHz.

    Chuẩn hoá ngay tại đây vừa giảm dung lượng upload vừa cải thiện độ chính
    xác — Whisper vốn được huấn luyện trên audio 16kHz.
    """
    subprocess.run(
        [
            "ffmpeg", "-nostdin", "-y", "-loglevel", "error",
            "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(source),
            "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(target),
        ],
        check=True,
        capture_output=True,
    )


def build_transcript(
    result: TranscriptionResult,
    *,
    meeting_id: str,
    transcript_id: str,
    meta: TranscriptMeta,
    speaker_label: str = "SPEAKER_00",
) -> Transcript:
    """Dựng ``Transcript`` từ đầu ra thô của ASR.

    Lưu ý về phạm vi: hàm này gán MỘT nhãn speaker duy nhất cho toàn bộ
    segment. Groq Whisper không làm diarization, nên bước tách người nói
    (``pipeline/s2_diarize.py``) là một pha riêng chưa nằm trong phạm vi
    tuần 2–3. Cho tới khi có nó, biên bản vẫn đầy đủ nội dung nhưng chưa
    quy được phát biểu về từng người.

    Ba trường metadata của Whisper được dùng làm bộ lọc chất lượng ngay tại
    đây, hoàn toàn miễn phí và trước khi động tới bất kỳ LLM nào.
    """
    segments: list[Segment] = []
    logprobs: list[float] = []
    dropped = 0

    for index, raw in enumerate(result.segments, start=1):
        text = (raw.get("text") or "").strip()
        if not text:
            continue

        no_speech = float(raw.get("no_speech_prob") or 0.0)
        if no_speech > HIGH_NO_SPEECH_THRESHOLD:
            # Nhiều khả năng là ảo giác của Whisper trên đoạn im lặng.
            dropped += 1
            continue

        avg_logprob = float(raw.get("avg_logprob") or 0.0)
        logprobs.append(avg_logprob)
        low_quality = avg_logprob < LOW_LOGPROB_THRESHOLD

        start_ms = int(float(raw.get("start", 0.0)) * 1000)
        end_ms = int(float(raw.get("end", 0.0)) * 1000)

        segments.append(
            Segment(
                id=f"s_{len(segments) + 1:04d}",
                index=len(segments) + 1,
                speaker_label=speaker_label,
                start_ms=start_ms,
                end_ms=max(end_ms, start_ms),
                text=text,
                text_raw=text,
                lang=Language.MIXED,
                asr_confidence=_logprob_to_confidence(avg_logprob),
                no_speech_prob=no_speech,
                words=_words_within(result.words, start_ms, end_ms),
                is_low_quality=low_quality,
            )
        )

    if not segments:
        raise ProviderError(
            "Không trích được segment nào có nội dung. File có thể gần như im "
            "lặng, hoặc không phải bản ghi cuộc họp."
        )

    total_ms = sum(s.duration_ms for s in segments)
    speaker = Speaker(
        label=speaker_label,
        identification_method=IdentificationMethod.UNIDENTIFIED,
        talk_time_ms=total_ms,
        talk_time_pct=100.0,
    )

    return Transcript(
        transcript_id=transcript_id,
        meeting_id=meeting_id,
        created_at=dt.datetime.now(dt.timezone.utc),
        meta=meta,
        provider=ProviderInfo(asr=f"groq/{result.model}"),
        language_profile=LanguageProfile(
            primary=Language.VI, secondary=[Language.EN], code_switching=True
        ),
        quality=TranscriptQuality(
            avg_logprob_mean=sum(logprobs) / len(logprobs) if logprobs else None,
            low_confidence_segment_count=sum(1 for s in segments if s.is_low_quality),
            speech_ratio=_speech_ratio(segments, result.duration_seconds),
            overall_score=_overall_score(logprobs, dropped, len(segments)),
        ),
        speakers=[speaker],
        segments=segments,
    )


def _logprob_to_confidence(avg_logprob: float) -> float:
    """Quy ``avg_logprob`` (thang âm) về khoảng 0–1 cho dễ hiển thị."""
    return max(0.0, min(1.0, math.exp(avg_logprob)))


def _words_within(
    words: list[dict[str, Any]], start_ms: int, end_ms: int
) -> list[Word]:
    result: list[Word] = []
    for raw in words:
        word_start = int(float(raw.get("start", 0.0)) * 1000)
        if start_ms <= word_start <= end_ms:
            word_end = int(float(raw.get("end", 0.0)) * 1000)
            result.append(
                Word(
                    word=str(raw.get("word", "")).strip() or "…",
                    start_ms=word_start,
                    end_ms=max(word_end, word_start),
                )
            )
    return result


def _speech_ratio(segments: list[Segment], duration_seconds: float) -> float:
    if duration_seconds <= 0:
        return 1.0
    spoken = sum(s.duration_ms for s in segments) / 1000.0
    return max(0.0, min(1.0, spoken / duration_seconds))


def _overall_score(logprobs: list[float], dropped: int, kept: int) -> float:
    if not logprobs:
        return 0.0
    mean = sum(logprobs) / len(logprobs)
    base = max(0.0, min(1.0, math.exp(mean)))
    penalty = dropped / max(1, dropped + kept)
    return round(max(0.0, base * (1.0 - penalty)), 3)
