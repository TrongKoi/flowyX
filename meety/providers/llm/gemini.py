"""Adapter Google Gemini — provider LLM chính của bản POC 0 đồng.

Vì sao chọn Gemini cho tầng suy luận:

* ``responseSchema`` ép JSON ngay ở tầng giải mã. Đây là khác biệt bản chất
  so với việc viết "hãy trả về JSON" trong prompt: model **không thể** sinh
  ra cấu trúc sai, thay vì chỉ *thường* sinh đúng.
* Context 1M token khiến cả cuộc họp lọt vào một lời gọi, cho phép gộp chunk
  to và giảm mạnh số request — thứ thực sự khan hiếm ở free tier.
* Hạn mức tính theo request/token, tách khỏi hạn mức tính theo giây audio của
  Groq. Hai cái túi riêng biệt nghĩa là phiên âm không ăn vào quota suy luận.

Cảnh báo quyền riêng tư
-----------------------
Free tier của AI Studio có thể dùng prompt và phản hồi để cải thiện sản
phẩm. Với ứng dụng mà đầu vào là nội dung họp nội bộ, đây không phải chi
tiết nhỏ. Dùng dữ liệu mẫu để demo; với dữ liệu thật hãy bật redaction hoặc
chạy chế độ ``--offline``.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from pydantic import BaseModel

from providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderError,
    RateLimitError,
    merge_headers,
)

logger = logging.getLogger(__name__)

__all__ = [
    "GeminiProvider",
    "SchemaRejectedError",
    "to_gemini_schema",
    "diagnose_schema",
    "DEFAULT_MODEL",
]

DEFAULT_MODEL = "gemini-flash-latest"

# Gemini chỉ chấp nhận một tập con của JSON Schema (theo chuẩn OpenAPI 3.0).
# Mọi khoá ngoài danh sách này phải bị loại bỏ, nếu không API trả 400.
_ALLOWED_SCHEMA_KEYS = frozenset(
    {
        "type",
        "format",
        "description",
        "nullable",
        "enum",
        "items",
        "properties",
        "required",
        "propertyOrdering",
        "minItems",
        "maxItems",
        "anyOf",
    }
)

# Các ràng buộc dưới đây bị Gemini từ chối. Bỏ chúng khỏi schema gửi đi
# KHÔNG làm mất kiểm soát: Pydantic vẫn kiểm tra đầy đủ ở phía ta ngay khi
# nhận phản hồi, và pha VALIDATE còn kiểm tra thêm một lớp nữa.
_DROPPED_SCHEMA_KEYS = frozenset(
    {
        "additionalProperties",
        "pattern",
        "minLength",
        "maxLength",
        "default",
        "title",
        "const",
        "allOf",
        "oneOf",
        "$schema",
        "$defs",
        "$ref",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minimum",
        "maximum",
    }
)


def to_gemini_schema(
    model: type[BaseModel], *, max_description_chars: int = 180
) -> dict[str, Any]:
    """Chuyển JSON Schema của Pydantic sang định dạng ``responseSchema``.

    Bốn phép biến đổi cần thiết:

    1. **Nội tuyến ``$ref``/``$defs``** — Gemini không giải tham chiếu.
    2. **``anyOf: [T, null]`` thành ``T`` kèm ``nullable: true``** — đây là
       cách Pydantic biểu diễn ``T | None``, và cũng là cách ta cho model một
       đường thoát hợp pháp thay vì buộc phải bịa giá trị.
    3. **Loại các khoá không được hỗ trợ** để tránh lỗi 400.
    4. **Cắt gọn ``description``** — Pydantic lấy nguyên docstring của class
       làm mô tả. Với schema có hàng chục trường lồng nhau, các docstring dài
       bơm phồng phần input của MỌI request; ở free tier tính theo token thì
       đó là lãng phí thuần tuý.
    """
    raw = model.model_json_schema()
    defs: dict[str, Any] = raw.get("$defs", {})
    return _convert_node(raw, defs, depth=0, max_description_chars=max_description_chars)


def _shorten_description(text: Any, limit: int) -> str | None:
    """Giữ lại câu đầu của docstring, cắt phần diễn giải dài phía sau."""
    if not isinstance(text, str):
        return None
    first_block = text.strip().split("\n\n", 1)[0]
    collapsed = " ".join(first_block.split())
    if len(collapsed) <= limit:
        return collapsed or None
    return collapsed[: limit - 1].rstrip() + "…"


def _convert_node(
    node: Any, defs: dict[str, Any], depth: int, max_description_chars: int
) -> Any:
    if depth > 30:
        raise ProviderError("Schema lồng quá sâu, nghi ngờ tham chiếu vòng")

    if not isinstance(node, dict):
        return node

    node = _resolve_ref(node, defs)

    if "anyOf" in node:
        collapsed = _collapse_nullable_union(node, defs, depth, max_description_chars)
        if collapsed is not None:
            return collapsed

    result: dict[str, Any] = {}

    for key, value in node.items():
        if key in _DROPPED_SCHEMA_KEYS or key not in _ALLOWED_SCHEMA_KEYS:
            continue

        if key == "description":
            shortened = _shorten_description(value, max_description_chars)
            if shortened:
                result["description"] = shortened

        elif key == "properties" and isinstance(value, dict):
            converted = {
                name: _convert_node(sub, defs, depth + 1, max_description_chars)
                for name, sub in value.items()
            }
            result["properties"] = converted
            # propertyOrdering giúp model sinh trường theo đúng thứ tự khai
            # báo, làm đầu ra ổn định hơn giữa các lần chạy.
            result["propertyOrdering"] = list(converted.keys())

        elif key == "items":
            result["items"] = _convert_node(value, defs, depth + 1, max_description_chars)

        elif key == "anyOf" and isinstance(value, list):
            result["anyOf"] = [
                _convert_node(sub, defs, depth + 1, max_description_chars)
                for sub in value
            ]

        else:
            result[key] = value

    if "type" not in result and "anyOf" not in result:
        result["type"] = "object" if "properties" in result else "string"

    if result.get("type") == "object" and "properties" not in result:
        result["type"] = "string"
        result.pop("required", None)
        result.pop("propertyOrdering", None)

    return result


def _resolve_ref(node: dict[str, Any], defs: dict[str, Any]) -> dict[str, Any]:
    """Nội tuyến ``$ref`` và ``allOf`` một phần tử do Pydantic sinh ra."""
    if "$ref" in node:
        target = _lookup_ref(node["$ref"], defs)
        merged = dict(target)
        for key, value in node.items():
            if key != "$ref":
                merged.setdefault(key, value)
        return merged

    all_of = node.get("allOf")
    if isinstance(all_of, list) and len(all_of) == 1:
        merged = dict(_resolve_ref(all_of[0], defs))
        for key, value in node.items():
            if key != "allOf":
                merged.setdefault(key, value)
        return merged

    return node


def _lookup_ref(ref: str, defs: dict[str, Any]) -> dict[str, Any]:
    name = ref.rsplit("/", 1)[-1]
    if name not in defs:
        raise ProviderError(f"Không giải được tham chiếu schema: {ref}")
    return defs[name]


def _collapse_nullable_union(
    node: dict[str, Any], defs: dict[str, Any], depth: int, max_description_chars: int
) -> dict[str, Any] | None:
    """Gộp ``T | None`` thành ``T`` kèm ``nullable: true``."""
    variants = node.get("anyOf", [])
    non_null = [v for v in variants if _resolve_ref(v, defs).get("type") != "null"]
    has_null = len(non_null) < len(variants)

    if not has_null or len(non_null) != 1:
        return None

    collapsed = _convert_node(non_null[0], defs, depth + 1, max_description_chars)
    if isinstance(collapsed, dict):
        collapsed["nullable"] = True
        if "description" in node and "description" not in collapsed:
            shortened = _shorten_description(node["description"], max_description_chars)
            if shortened:
                collapsed["description"] = shortened
    return collapsed


class SchemaRejectedError(ProviderError):
    """Gemini từ chối ``responseSchema`` (HTTP 400).

    Lỗi này gần như luôn do bất đồng giữa JSON Schema của Pydantic và tập con
    OpenAPI mà Gemini chấp nhận, chứ không phải do prompt. Nó mang theo chẩn
    đoán cụ thể vì thông điệp gốc của API thường chỉ nói "Invalid JSON
    payload" mà không chỉ ra trường nào có vấn đề.
    """

    def __init__(self, message: str, schema_name: str, diagnosis: str) -> None:
        super().__init__(message)
        self.schema_name = schema_name
        self.diagnosis = diagnosis


def diagnose_schema(schema: dict[str, Any], *, path: str = "$") -> list[str]:
    """Tìm các cấu trúc mà Gemini nhiều khả năng từ chối.

    Chạy trước khi gọi API để đổi một lỗi 400 mơ hồ thành thông báo chỉ đúng
    trường có vấn đề. Danh sách trả về rỗng nghĩa là schema trông hợp lệ.
    """
    problems: list[str] = []

    if not isinstance(schema, dict):
        return problems

    for key in schema:
        if key not in _ALLOWED_SCHEMA_KEYS:
            problems.append(f"{path}: còn khoá không được hỗ trợ {key!r}")

    node_type = schema.get("type")

    if node_type == "object":
        properties = schema.get("properties")
        if not properties:
            problems.append(f"{path}: kiểu object nhưng không khai báo properties")
        else:
            for name, child in properties.items():
                problems.extend(diagnose_schema(child, path=f"{path}.{name}"))

        required = schema.get("required", [])
        unknown = [r for r in required if r not in (schema.get("properties") or {})]
        if unknown:
            problems.append(f"{path}: required trỏ tới trường không tồn tại {unknown}")

    elif node_type == "array":
        items = schema.get("items")
        if items is None:
            problems.append(f"{path}: kiểu array nhưng thiếu items")
        else:
            problems.extend(diagnose_schema(items, path=f"{path}[]"))

    elif node_type is None and "anyOf" not in schema:
        problems.append(f"{path}: thiếu khai báo type")

    if "enum" in schema and node_type not in (None, "string"):
        problems.append(f"{path}: enum chỉ dùng được với type='string'")

    return problems


class GeminiProvider(LLMProvider):
    """Adapter cho Google Gemini qua SDK ``google-genai``.

    SDK được import trễ (bên trong ``__init__``) để module này vẫn import
    được trên máy chưa cài gói — cần thiết cho việc chạy pipeline ở chế độ
    mock hoặc offline mà không phải cài toàn bộ phụ thuộc.
    """

    name = "gemini"

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        timeout_seconds: float = 120.0,
        max_output_tokens: int = 8192,
    ) -> None:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ProviderError(
                "Chưa cài SDK Gemini. Chạy: pip install google-genai"
            ) from exc

        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get(
            "GOOGLE_API_KEY"
        )
        if not key:
            raise ProviderError(
                "Thiếu GEMINI_API_KEY. Lấy khoá miễn phí tại "
                "https://aistudio.google.com/apikey rồi đặt vào file .env"
            )

        self.model = model
        self.max_output_tokens = max_output_tokens
        self._types = types
        self._client = genai.Client(
            api_key=key,
            http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000)),
        )

    def generate_json(
        self,
        prompt: str,
        schema: type[BaseModel],
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_output_tokens: int | None = None,
    ) -> LLMResponse:
        gemini_schema = to_gemini_schema(schema)

        config = self._types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=gemini_schema,
            max_output_tokens=max_output_tokens or self.max_output_tokens,
            system_instruction=system,
        )

        try:
            response = self._client.models.generate_content(
                model=self.model, contents=prompt, config=config
            )
        except Exception as exc:
            if _is_schema_rejection(exc):
                raise self._schema_error(exc, schema, gemini_schema) from exc
            raise self._translate_error(exc) from exc

        text = (getattr(response, "text", "") or "").strip()
        if not text:
            raise ProviderError(
                "Gemini trả về nội dung rỗng. Thường do bộ lọc an toàn chặn, "
                "hoặc do max_output_tokens quá nhỏ cho schema này."
            )

        payload = self._parse_json(text)
        usage = getattr(response, "usage_metadata", None)

        return LLMResponse(
            payload=payload,
            raw_text=text,
            input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
            output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
            headers=merge_headers(getattr(response, "response_headers", None)),
            model=self.model,
        )

    @staticmethod
    def _schema_error(
        exc: Exception, model: type[BaseModel], gemini_schema: dict[str, Any]
    ) -> SchemaRejectedError:
        """Biến lỗi 400 mơ hồ thành chẩn đoán chỉ đúng trường có vấn đề."""
        problems = diagnose_schema(gemini_schema)

        if problems:
            diagnosis = "Phát hiện các vấn đề trong schema:\n" + "\n".join(
                f"  - {problem}" for problem in problems[:8]
            )
        else:
            diagnosis = (
                "Bộ chuyển schema không tìm thấy vấn đề rõ ràng. Nhiều khả năng "
                "Gemini vừa siết thêm ràng buộc mới.\n"
                "  Cách xử lý theo thứ tự:\n"
                "  1. Chạy lại với --verbose để xem schema đã gửi đi.\n"
                "  2. Bỏ bớt trường lồng sâu nhất trong schema rồi thử lại.\n"
                "  3. Tạm chuyển sang --mock để pipeline không bị chặn."
            )

        return SchemaRejectedError(
            f"Gemini từ chối schema của {model.__name__} (HTTP 400).\n"
            f"{diagnosis}\n"
            f"Thông điệp gốc: {str(exc)[:300]}",
            schema_name=model.__name__,
            diagnosis=diagnosis,
        )

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """Đọc JSON, gỡ rào ``` nếu model vẫn bọc dù đã bật response_mime_type."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.rstrip().endswith("```"):
                cleaned = cleaned.rstrip()[:-3]

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ProviderError(
                f"Gemini trả về JSON không hợp lệ tại vị trí {exc.pos}: "
                f"{cleaned[:200]}"
            ) from exc

        if not isinstance(parsed, dict):
            raise ProviderError(
                f"Gemini trả về {type(parsed).__name__} thay vì object JSON"
            )
        return parsed

    @staticmethod
    def _translate_error(exc: Exception) -> ProviderError:
        """Quy lỗi của SDK về hai loại mà ``LLMRunner`` biết cách xử lý."""
        message = str(exc)
        lowered = message.lower()
        status = getattr(exc, "code", None) or getattr(exc, "status_code", None)

        is_rate_limit = (
            status == 429
            or "429" in message
            or "resource_exhausted" in lowered
            or "quota" in lowered
            or "rate limit" in lowered
        )

        if is_rate_limit:
            return RateLimitError(
                f"Gemini chạm hạn mức: {message[:200]}",
                retry_after_seconds=_extract_retry_after(message),
            )
        return ProviderError(f"Gemini lỗi: {message[:300]}")


def _is_schema_rejection(exc: Exception) -> bool:
    """Lỗi này có phải do Gemini từ chối responseSchema không.

    Phân biệt với các lỗi 400 khác (prompt quá dài, tham số sai) để không đưa
    ra chẩn đoán schema cho một vấn đề hoàn toàn khác.
    """
    message = str(exc).lower()
    status = getattr(exc, "code", None) or getattr(exc, "status_code", None)

    is_bad_request = status == 400 or "400" in message or "invalid_argument" in message
    if not is_bad_request:
        return False

    schema_markers = (
        "schema", "response_schema", "responseschema", "invalid json payload",
        "unknown name", "proto field", "cannot find field",
    )
    return any(marker in message for marker in schema_markers)


def _extract_retry_after(message: str) -> float:
    """Lấy ``retryDelay`` từ thông điệp lỗi, mặc định 60 giây."""
    import re

    match = re.search(r"retry\w*delay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)", message, re.I)
    if match:
        return float(match.group(1))
    return 60.0
