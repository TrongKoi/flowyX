"""Adapter Layer — biên giới duy nhất của hệ thống chạm tới mạng.

Pipeline không bao giờ ``import google.genai`` hay ``import groq`` trực tiếp.
Với hệ 0 đồng, đây không phải sự cầu kỳ kiến trúc: bạn sẽ chuyển provider
liên tục mỗi khi ăn 429, và tier on-prem sau này cũng cắm vào đúng interface
này mà không phải sửa một dòng nào trong ``pipeline/``.

``LLMRunner`` là nơi gộp bốn cơ chế thành một lời gọi duy nhất:
cache → quota → retry có backoff → chuyển provider dự phòng.
"""

from __future__ import annotations

import abc
import dataclasses
import json
import logging
import random
import time
from typing import Any, Mapping, Sequence, TypeVar

from pydantic import BaseModel, ValidationError

from core.cache import CacheKey, LLMCache
from core.quota import QuotaExhausted, QuotaLedger

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

__all__ = [
    "LLMResponse",
    "TranscriptionResult",
    "LLMProvider",
    "ASRProvider",
    "ProviderError",
    "RateLimitError",
    "AllProvidersExhausted",
    "LLMRunner",
    "estimate_tokens",
]


def estimate_tokens(text: str) -> int:
    """Ước lượng token thô cho văn bản tiếng Việt.

    Tiếng Việt tốn nhiều token hơn tiếng Anh cho cùng lượng thông tin. Hệ số
    ~2,6 ký tự/token là con số thận trọng dùng để ĐẶT CHỖ quota trước khi
    gọi; số liệu thật sẽ được hiệu chỉnh lại sau khi có phản hồi.
    """
    return max(1, int(len(text) / 2.6))


@dataclasses.dataclass(slots=True)
class LLMResponse:
    payload: dict[str, Any]
    raw_text: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    headers: dict[str, str] = dataclasses.field(default_factory=dict)
    model: str = ""
    from_cache: bool = False

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclasses.dataclass(slots=True)
class TranscriptionResult:
    """Đầu ra thô của ASR, trước khi dựng thành ``Transcript``."""

    text: str
    language: str
    duration_seconds: float
    segments: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    words: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    model: str = ""
    headers: dict[str, str] = dataclasses.field(default_factory=dict)


class ProviderError(RuntimeError):
    """Lỗi chung của nhà cung cấp."""


class RateLimitError(ProviderError):
    """Nhà cung cấp trả 429."""

    def __init__(self, message: str, retry_after_seconds: float = 60.0) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class AllProvidersExhausted(RuntimeError):
    """Mọi provider trong chuỗi dự phòng đều không dùng được."""


class LLMProvider(abc.ABC):
    """Giao diện tối thiểu mà mọi backend LLM phải thoả mãn."""

    name: str = "unknown"
    model: str = "unknown"

    @abc.abstractmethod
    def generate_json(
        self,
        prompt: str,
        schema: type[BaseModel],
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_output_tokens: int | None = None,
    ) -> LLMResponse:
        """Sinh JSON tuân thủ ``schema``.

        Bản cài đặt PHẢI ép định dạng ở tầng giải mã (structured output /
        constrained decoding) chứ không chỉ yêu cầu "hãy trả JSON" trong
        prompt — đó là khác biệt giữa đảm bảo và hy vọng.
        """

    @property
    def key(self) -> str:
        return f"{self.name}/{self.model}"

    def close(self) -> None:
        """Giải phóng tài nguyên. Mặc định không làm gì."""


class ASRProvider(abc.ABC):
    """Giao diện tối thiểu cho backend nhận dạng giọng nói."""

    name: str = "unknown"
    model: str = "unknown"

    @abc.abstractmethod
    def transcribe(
        self,
        audio_path: str,
        *,
        language: str = "vi",
        prompt: str | None = None,
        temperature: float = 0.0,
    ) -> TranscriptionResult:
        """Chuyển audio thành văn bản kèm mốc thời gian cấp từ."""

    @property
    def key(self) -> str:
        return f"{self.name}/{self.model}"

    def close(self) -> None:
        """Giải phóng tài nguyên. Mặc định không làm gì."""


class LLMRunner:
    """Gọi LLM có kiểm soát quota, cache, retry và chuyển provider.

    Thứ tự thử, cố ý đi từ rẻ nhất tới đắt nhất:

    1. **Cache** — hoàn toàn miễn phí. Chạy lại pipeline khi debug tốn 0 quota.
    2. **Provider chính** kèm đặt chỗ quota trước khi gọi.
    3. **Retry** với backoff mũ + jitter khi gặp 429 hoặc lỗi tạm thời.
    4. **Provider dự phòng** khi provider hiện tại cạn quota.
    """

    def __init__(
        self,
        providers: Sequence[LLMProvider],
        *,
        cache: LLMCache | None = None,
        quota: QuotaLedger | None = None,
        max_retries: int = 3,
        max_wait_seconds: float = 120.0,
        sleeper: Any = time.sleep,
    ) -> None:
        if not providers:
            raise ValueError("LLMRunner cần ít nhất một provider")
        self.providers = list(providers)
        self.cache = cache
        self.quota = quota
        self.max_retries = max_retries
        self.max_wait_seconds = max_wait_seconds
        self._sleep = sleeper
        self.request_count = 0
        self.token_count = 0
        self.cache_hits = 0

    def run(
        self,
        *,
        phase: str,
        prompt: str,
        schema: type[T],
        prompt_version: str = "v0",
        system: str | None = None,
        temperature: float = 0.0,
        cache_extra: dict[str, Any] | None = None,
    ) -> T:
        """Chạy một bước LLM và trả về đối tượng Pydantic đã được kiểm tra."""
        schema_signature = json.dumps(
            schema.model_json_schema(), sort_keys=True, ensure_ascii=False
        )

        for provider in self.providers:
            cache_key = CacheKey.build(
                phase=phase,
                prompt=(system or "") + "\n" + prompt,
                model=provider.key,
                prompt_version=prompt_version,
                schema_signature=schema_signature,
                extra=cache_extra,
            )

            if self.cache is not None:
                cached = self.cache.get(cache_key)
                if cached is not None:
                    self.cache_hits += 1
                    logger.info("[%s] cache hit (%s)", phase, provider.key)
                    return schema.model_validate(cached)

            try:
                response = self._call_with_retry(
                    provider=provider,
                    phase=phase,
                    prompt=prompt,
                    schema=schema,
                    system=system,
                    temperature=temperature,
                )
            except (QuotaExhausted, RateLimitError) as exc:
                logger.warning(
                    "[%s] %s không dùng được (%s), chuyển provider dự phòng",
                    phase,
                    provider.key,
                    exc,
                )
                continue
            except ProviderError as exc:
                logger.warning("[%s] %s lỗi: %s", phase, provider.key, exc)
                continue

            try:
                result = schema.model_validate(response.payload)
            except ValidationError as exc:
                logger.warning(
                    "[%s] %s trả JSON sai schema: %s",
                    phase,
                    provider.key,
                    str(exc)[:200],
                )
                continue

            if self.cache is not None and not response.from_cache:
                self.cache.set(cache_key, response.payload, tokens=response.total_tokens)

            return result

        raise AllProvidersExhausted(
            f"Pha {phase!r}: đã thử {len(self.providers)} provider, không cái nào "
            "trả về kết quả hợp lệ. Kiểm tra quota bằng `python main.py --quota-status`."
        )

    def _call_with_retry(
        self,
        *,
        provider: LLMProvider,
        phase: str,
        prompt: str,
        schema: type[BaseModel],
        system: str | None,
        temperature: float,
    ) -> LLMResponse:
        estimated = estimate_tokens((system or "") + prompt)
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            reservation = None
            if self.quota is not None:
                decision, reservation = self.quota.acquire(
                    provider.name, provider.model, estimated_tokens=estimated
                )
                if not decision.allowed:
                    if decision.retry_after_seconds > self.max_wait_seconds:
                        raise QuotaExhausted(
                            decision.reason, decision.retry_after_seconds
                        )
                    logger.info(
                        "[%s] chờ %.0fs cho %s (%s)",
                        phase,
                        decision.retry_after_seconds,
                        provider.key,
                        decision.reason,
                    )
                    self._sleep(decision.retry_after_seconds + random.uniform(0, 2))
                    continue

            try:
                response = provider.generate_json(
                    prompt, schema, system=system, temperature=temperature
                )
            except RateLimitError as exc:
                last_error = exc
                if self.quota is not None and reservation is not None:
                    self.quota.release(reservation, succeeded=False)
                    self.quota.sync_from_headers(
                        provider.name, provider.model, getattr(exc, "headers", {}) or {}
                    )
                wait = min(
                    exc.retry_after_seconds or 2**attempt, self.max_wait_seconds
                )
                logger.info("[%s] 429 từ %s, chờ %.0fs", phase, provider.key, wait)
                self._sleep(wait + random.uniform(0, 2))
                continue
            except ProviderError as exc:
                last_error = exc
                if self.quota is not None and reservation is not None:
                    self.quota.release(reservation, succeeded=False)
                if attempt == self.max_retries:
                    raise
                self._sleep(2**attempt + random.uniform(0, 2))
                continue

            if self.quota is not None and reservation is not None:
                self.quota.release(
                    reservation, actual_tokens=response.total_tokens, succeeded=True
                )
                self.quota.sync_from_headers(
                    provider.name, provider.model, response.headers
                )

            self.request_count += 1
            self.token_count += response.total_tokens
            return response

        raise ProviderError(
            f"{provider.key} thất bại sau {self.max_retries} lần thử: {last_error}"
        )

    def pace(self, seconds: float) -> None:
        """Giãn cách giữa các request để không chạm trần RPM."""
        if seconds > 0:
            self._sleep(seconds)

    def stats(self) -> dict[str, int]:
        return {
            "llm_requests": self.request_count,
            "llm_tokens": self.token_count,
            "cache_hits": self.cache_hits,
        }


def merge_headers(raw: Mapping[str, Any] | None) -> dict[str, str]:
    """Chuẩn hoá header về chữ thường để tra cứu ổn định giữa các SDK."""
    if not raw:
        return {}
    return {str(k).lower(): str(v) for k, v in raw.items()}
