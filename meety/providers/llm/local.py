"""Provider cho mô hình chạy tại chỗ — Ollama và mọi endpoint tương thích OpenAI.

Vì sao lớp này tồn tại
----------------------
Ba lý do, xếp theo mức độ thật của vấn đề:

1. **Quota.** Free tier Gemini hết là cả hệ thống đứng. Mô hình cục bộ không
   có hạn mức, chỉ có tốc độ.
2. **Dữ liệu.** Có khách hàng sẽ không bao giờ chấp nhận transcript cuộc họp
   nội bộ rời khỏi máy chủ của họ. Không có đường chạy tại chỗ thì không bán
   được cho nhóm đó, bất kể sản phẩm tốt đến đâu.
3. **Đích đến của việc chưng cất.** ``DataCollector`` gom cặp
   ``transcript → biên bản đã duyệt`` để fine-tune. Mô hình fine-tune xong
   phải chạy được ở đâu đó — chỗ đó là đây.

Điều KHÔNG được tự lừa mình
---------------------------
Llama-3-8B chạy trên máy để bàn **không** ngang Gemini Flash ở việc trích xuất
cam kết từ hội thoại tiếng Việt pha tiếng Anh. Nó kém hơn rõ rệt, đặc biệt ở
pha RECONCILE. Lớp này không phải để thay thế ngay, mà để:

* chạy song song đối soát (xem ``ConsensusEngine``),
* làm chỗ hạ cánh cho mô hình đã fine-tune,
* làm đường lùi khi API chết hẳn.

Hai cách nói chuyện
-------------------
``ollama``  — API gốc của Ollama, có ``format`` nhận JSON Schema (từ 0.5.0).
``openai``  — ``/v1/chat/completions``, dùng cho vLLM, LM Studio, llama.cpp
              server, hoặc chính OpenAI/Anthropic qua proxy tương thích.

Cả hai đều gọi bằng ``urllib`` của thư viện chuẩn. Dự án cố ý giữ ít phụ
thuộc; thêm ``openai`` SDK chỉ để POST một JSON là không đáng.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

from pydantic import BaseModel

from providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderError,
    RateLimitError,
    estimate_tokens,
)

logger = logging.getLogger(__name__)

__all__ = ["LocalLLMProvider"]

DEFAULT_TIMEOUT = 300.0     # mô hình cục bộ chậm hơn API rất nhiều


class LocalLLMProvider(LLMProvider):
    """Gọi mô hình chạy tại chỗ, ép đầu ra theo JSON Schema khi backend hỗ trợ."""

    name = "local"

    def __init__(
        self,
        model: str | None = None,
        *,
        base_url: str | None = None,
        dialect: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        api_key: str | None = None,
    ) -> None:
        self.model = model or os.environ.get("LOCAL_LLM_MODEL", "llama3.1:8b")
        self.base_url = (base_url or os.environ.get("LOCAL_LLM_URL",
                                                    "http://localhost:11434")).rstrip("/")
        self.dialect = (dialect or os.environ.get("LOCAL_LLM_DIALECT", "ollama")).lower()
        if self.dialect not in {"ollama", "openai"}:
            raise ProviderError(
                f"LOCAL_LLM_DIALECT phải là 'ollama' hoặc 'openai', nhận được {self.dialect!r}")
        self.timeout = timeout
        # vLLM và LM Studio thường không cần khoá; OpenAI thật thì cần.
        self.api_key = api_key or os.environ.get("LOCAL_LLM_API_KEY", "")

    # -- Giao diện chung ------------------------------------------------- #

    def generate_json(
        self,
        prompt: str,
        schema: type[BaseModel],
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_output_tokens: int | None = None,
    ) -> LLMResponse:
        json_schema = schema.model_json_schema()
        if self.dialect == "ollama":
            raw, usage = self._call_ollama(prompt, json_schema, system, temperature,
                                           max_output_tokens)
        else:
            raw, usage = self._call_openai(prompt, json_schema, schema.__name__, system,
                                           temperature, max_output_tokens)

        payload = _parse_json_lenient(raw)
        if payload is None:
            raise ProviderError(
                f"{self.key} trả về thứ không phải JSON. "
                f"120 ký tự đầu: {raw[:120]!r}"
            )
        return LLMResponse(
            payload=payload,
            raw_text=raw,
            input_tokens=usage.get("in", estimate_tokens(prompt + (system or ""))),
            output_tokens=usage.get("out", estimate_tokens(raw)),
        )

    # -- Ollama ----------------------------------------------------------- #

    def _call_ollama(self, prompt, json_schema, system, temperature, max_tokens):
        body: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            # Ollama ≥ 0.5 nhận thẳng JSON Schema ở trường `format` và ép
            # bộ giải mã đi theo. Đây là ép định dạng thật, không phải xin xỏ
            # trong prompt — đúng yêu cầu của LLMProvider.
            "format": json_schema,
            "options": {"temperature": temperature},
        }
        if system:
            body["system"] = system
        if max_tokens:
            body["options"]["num_predict"] = max_tokens

        data = self._post(f"{self.base_url}/api/generate", body)
        raw = data.get("response", "")
        usage = {
            "in": data.get("prompt_eval_count", 0) or estimate_tokens(prompt),
            "out": data.get("eval_count", 0) or estimate_tokens(raw),
        }
        return raw, usage

    # -- Tương thích OpenAI ----------------------------------------------- #

    def _call_openai(self, prompt, json_schema, schema_name, system, temperature, max_tokens):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            # `json_schema` là dạng ép chặt; server không hỗ trợ sẽ báo lỗi và
            # ta lùi về `json_object` ở dưới. Không im lặng bỏ qua ràng buộc.
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "schema": json_schema, "strict": True},
            },
        }
        if max_tokens:
            body["max_tokens"] = max_tokens

        try:
            data = self._post(f"{self.base_url}/v1/chat/completions", body)
        except ProviderError as exc:
            if "response_format" not in str(exc) and "json_schema" not in str(exc):
                raise
            logger.warning("%s không hỗ trợ json_schema, lùi về json_object", self.key)
            body["response_format"] = {"type": "json_object"}
            # Không còn ép được bằng bộ giải mã thì phải nói rõ trong prompt.
            body["messages"][-1]["content"] = (
                prompt + "\n\nChỉ trả về JSON hợp lệ theo đúng lược đồ sau, "
                "không kèm giải thích:\n" + json.dumps(json_schema, ensure_ascii=False)
            )
            data = self._post(f"{self.base_url}/v1/chat/completions", body)

        raw = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        usage_raw = data.get("usage") or {}
        usage = {
            "in": usage_raw.get("prompt_tokens", 0) or estimate_tokens(prompt),
            "out": usage_raw.get("completion_tokens", 0) or estimate_tokens(raw),
        }
        return raw, usage

    # -- HTTP ------------------------------------------------------------- #

    def _post(self, url: str, body: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:400]
            if exc.code == 429:
                raise RateLimitError(f"{self.key} báo quá tải: {detail}") from exc
            raise ProviderError(f"{self.key} lỗi HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(
                f"Không kết nối được tới {self.base_url}. "
                f"Máy chủ mô hình cục bộ đã chạy chưa? (ollama serve). Chi tiết: {exc.reason}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise ProviderError(f"{self.key} trả về thứ không phải JSON") from exc

    # -- Tiện ích --------------------------------------------------------- #

    def health(self) -> dict[str, Any]:
        """Kiểm nhanh xem máy chủ mô hình có sống không, dùng cho endpoint chẩn đoán."""
        try:
            url = (f"{self.base_url}/api/tags" if self.dialect == "ollama"
                   else f"{self.base_url}/v1/models")
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if self.dialect == "ollama":
                models = [m.get("name") for m in data.get("models", [])]
            else:
                models = [m.get("id") for m in data.get("data", [])]
            return {"ok": True, "url": self.base_url, "dialect": self.dialect,
                    "models": models, "configured_model": self.model,
                    "model_present": self.model in models}
        except Exception as exc:                      # noqa: BLE001
            return {"ok": False, "url": self.base_url, "dialect": self.dialect,
                    "error": str(exc)}


def _parse_json_lenient(raw: str) -> dict[str, Any] | None:
    """Bóc JSON ra khỏi những thứ mô hình nhỏ hay kèm thêm.

    Mô hình 7-8B thường bọc JSON trong ```json, hoặc thêm một câu dẫn trước.
    Đó là lý do hàm này tồn tại. Nó KHÔNG sửa JSON hỏng — chỉ tìm khối JSON
    trong đống chữ. Hỏng thật thì trả None để bên gọi biết mà đổi provider.
    """
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1] if "```" in text[3:] else text[3:]
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
        text = text.strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(text[start:end + 1])
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return None
