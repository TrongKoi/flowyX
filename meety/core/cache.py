"""Cache kết quả LLM theo băm nội dung — công cụ tiết kiệm quota số một.

Với hệ 0 đồng, vòng lặp phát triển thực tế là: chỉnh prompt COMPOSE, chạy
lại, xem kết quả, chỉnh tiếp. Không có cache, mỗi vòng lặp đốt lại toàn bộ
request của các pha phía trước dù chúng không hề đổi.

Khoá cache = sha256 của (tên pha + phiên bản prompt + nội dung prompt +
chữ ký schema + model). Bất kỳ thành phần nào đổi thì khoá đổi, nên cache
không bao giờ trả về kết quả cũ cho một prompt mới — đây là điều kiện để
cache an toàn khi lặp prompt.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.db import DEFAULT_DB_PATH, connect, transaction

__all__ = ["CacheKey", "CacheStats", "LLMCache"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS llm_cache (
    cache_key      TEXT PRIMARY KEY,
    phase          TEXT NOT NULL,
    model          TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    payload        TEXT NOT NULL,
    tokens         INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT NOT NULL,
    hit_count      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_llm_cache_phase ON llm_cache(phase);
CREATE INDEX IF NOT EXISTS idx_llm_cache_created ON llm_cache(created_at);
"""


@dataclass(frozen=True, slots=True)
class CacheKey:
    """Khoá cache đã băm, kèm siêu dữ liệu để tra cứu và dọn dẹp."""

    digest: str
    phase: str
    model: str
    prompt_version: str

    @classmethod
    def build(
        cls,
        *,
        phase: str,
        prompt: str,
        model: str,
        prompt_version: str = "v0",
        schema_signature: str = "",
        extra: dict[str, Any] | None = None,
    ) -> CacheKey:
        material = json.dumps(
            {
                "phase": phase,
                "prompt": prompt,
                "model": model,
                "prompt_version": prompt_version,
                "schema": schema_signature,
                "extra": extra or {},
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
        return cls(
            digest=digest,
            phase=phase,
            model=model,
            prompt_version=prompt_version,
        )


@dataclass(slots=True)
class CacheStats:
    hits: int = 0
    misses: int = 0
    writes: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def summary(self) -> str:
        return (
            f"cache: {self.hits} hit / {self.misses} miss "
            f"({self.hit_rate:.0%}), {self.writes} ghi mới"
        )


class LLMCache:
    """Kho lưu kết quả LLM bền vững trên đĩa.

    Ví dụ:
        >>> cache = LLMCache(":memory:")
        >>> key = CacheKey.build(phase="extract", prompt="xin chào", model="m")
        >>> cache.get(key) is None
        True
        >>> _ = cache.set(key, {"ok": True})
        >>> cache.get(key)
        {'ok': True}
    """

    def __init__(
        self,
        db_path: Path | str = DEFAULT_DB_PATH,
        *,
        enabled: bool = True,
        ttl_days: int = 30,
    ) -> None:
        self.enabled = enabled
        self.ttl_days = ttl_days
        self.stats = CacheStats()
        self._conn: sqlite3.Connection = connect(db_path)
        self._conn.executescript(_SCHEMA)

    def get(self, key: CacheKey) -> dict[str, Any] | None:
        """Trả về payload đã cache, hoặc ``None`` nếu chưa có / đã hết hạn."""
        if not self.enabled:
            self.stats.misses += 1
            return None

        row = self._conn.execute(
            "SELECT payload, created_at FROM llm_cache WHERE cache_key = ?",
            (key.digest,),
        ).fetchone()

        if row is None:
            self.stats.misses += 1
            return None

        created = dt.datetime.fromisoformat(row["created_at"])
        age_days = (dt.datetime.now(dt.timezone.utc) - created).days
        if age_days > self.ttl_days:
            self.delete(key)
            self.stats.misses += 1
            return None

        with transaction(self._conn) as conn:
            conn.execute(
                "UPDATE llm_cache SET hit_count = hit_count + 1 WHERE cache_key = ?",
                (key.digest,),
            )

        self.stats.hits += 1
        return json.loads(row["payload"])

    def set(self, key: CacheKey, payload: dict[str, Any], *, tokens: int = 0) -> bool:
        """Lưu payload. Trả về ``False`` nếu cache đang tắt."""
        if not self.enabled:
            return False

        with transaction(self._conn) as conn:
            conn.execute(
                """
                INSERT INTO llm_cache
                    (cache_key, phase, model, prompt_version, payload, tokens, created_at, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(cache_key) DO UPDATE SET
                    payload = excluded.payload,
                    tokens = excluded.tokens,
                    created_at = excluded.created_at
                """,
                (
                    key.digest,
                    key.phase,
                    key.model,
                    key.prompt_version,
                    json.dumps(payload, ensure_ascii=False),
                    tokens,
                    dt.datetime.now(dt.timezone.utc).isoformat(),
                ),
            )
        self.stats.writes += 1
        return True

    def delete(self, key: CacheKey) -> None:
        with transaction(self._conn) as conn:
            conn.execute("DELETE FROM llm_cache WHERE cache_key = ?", (key.digest,))

    def clear(self, *, phase: str | None = None) -> int:
        """Xoá cache. Giới hạn theo pha nếu cần lặp lại đúng một bước."""
        with transaction(self._conn) as conn:
            if phase:
                cursor = conn.execute("DELETE FROM llm_cache WHERE phase = ?", (phase,))
            else:
                cursor = conn.execute("DELETE FROM llm_cache")
        return cursor.rowcount

    def purge_expired(self) -> int:
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=self.ttl_days)
        with transaction(self._conn) as conn:
            cursor = conn.execute(
                "DELETE FROM llm_cache WHERE created_at < ?", (cutoff.isoformat(),)
            )
        return cursor.rowcount

    def size(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM llm_cache").fetchone()
        return int(row["n"])

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> LLMCache:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
