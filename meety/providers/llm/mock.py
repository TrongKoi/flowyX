"""Provider LLM giả lập, đọc phản hồi đóng hộp từ file fixture.

Mục đích không phải để "giả vờ chạy được". Trong kiến trúc này, phần lớn
logic dễ sai nằm ở Python chứ không ở LLM: hoà giải thời gian, quy tắc ưu
tiên khi đổi ý, quy đổi ngày tiếng Việt, tám lớp kiểm chứng grounding.

Bằng cách cố định đầu ra của LLM, ta kiểm thử được toàn bộ phần đó một cách
**tất định** và **không tốn quota** — chạy được hàng trăm lần trong CI. Đây
là cách duy nhất để viết test hồi quy cho một pipeline có thành phần phi
tất định.

Provider này cũng dùng được cho ``main.py --mock`` khi bạn chưa có API key.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from providers.base import LLMProvider, LLMResponse, ProviderError

logger = logging.getLogger(__name__)

__all__ = ["MockLLMProvider", "DEFAULT_FIXTURE_DIR"]

DEFAULT_FIXTURE_DIR = Path("tests/fixtures/mock_llm")

_CHUNK_ID_PATTERN = re.compile(r'chunk_id="([^"]+)"')


class MockLLMProvider(LLMProvider):
    """Trả phản hồi đã ghi sẵn, định tuyến theo schema được yêu cầu."""

    name = "mock"
    model = "mock"

    def __init__(
        self,
        fixture_dir: Path | str = DEFAULT_FIXTURE_DIR,
        *,
        strict: bool = True,
    ) -> None:
        self.fixture_dir = Path(fixture_dir)
        self.strict = strict
        self.calls: list[tuple[str, str]] = []

    def generate_json(
        self,
        prompt: str,
        schema: type[BaseModel],
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_output_tokens: int | None = None,
    ) -> LLMResponse:
        fixture_name = self._route(prompt, schema)
        self.calls.append((schema.__name__, fixture_name))

        path = self.fixture_dir / f"{fixture_name}.json"
        if not path.exists():
            if self.strict:
                raise ProviderError(
                    f"Thiếu fixture {path}. Provider mock chỉ trả lời được các "
                    "lời gọi đã ghi sẵn — thêm file này hoặc dùng provider thật."
                )
            return LLMResponse(payload=self._empty_payload(schema), model=self.model)

        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        logger.info("MOCK %s -> %s", schema.__name__, path.name)

        return LLMResponse(
            payload=payload,
            raw_text=json.dumps(payload, ensure_ascii=False),
            input_tokens=len(prompt) // 3,
            output_tokens=len(json.dumps(payload)) // 3,
            model=self.model,
        )

    def _route(self, prompt: str, schema: type[BaseModel]) -> str:
        """Chọn fixture theo schema, riêng pha EXTRACT thì theo cả chunk_id."""
        name = schema.__name__

        if name == "ChunkExtraction":
            match = _CHUNK_ID_PATTERN.search(prompt)
            chunk_id = match.group(1) if match else "c_all"
            return f"extract_{chunk_id}"

        if name == "TopicGrouping":
            return "topic_grouping"

        if name == "ComposedProse":
            return "compose"

        return f"generic_{name.lower()}"

    @staticmethod
    def _empty_payload(schema: type[BaseModel]) -> dict[str, Any]:
        """Payload rỗng hợp lệ, để kiểm thử nhánh suy giảm có kiểm soát."""
        if schema.__name__ == "ComposedProse":
            return {"tldr": ["Không có nội dung."], "paragraphs": [], "chapters": []}
        if schema.__name__ == "TopicGrouping":
            return {"groups": []}
        return {}
