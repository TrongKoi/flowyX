"""Kết nối SQLite dùng chung cho ``core/cache.py`` và ``core/quota.py``.

Vì sao SQLite chứ không phải Redis + Celery: với POC low-traffic, Redis là
một tiến trình nữa để cài, chạy và hỏng. SQLite là một file, backup bằng
lệnh ``cp``, và quan trọng nhất — nó **bền vững qua các lần khởi động lại**.

Tính bền vững đó không phải tiện nghi: hạn mức RPD của nhà cung cấp reset
theo giờ Thái Bình Dương chứ không theo phiên chạy script. Giữ bộ đếm quota
trong RAM nghĩa là mỗi lần bạn Ctrl-C rồi chạy lại là mất dấu, và request
đầu tiên sau đó ăn ngay 429.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

__all__ = ["DEFAULT_DB_PATH", "connect", "transaction"]

DEFAULT_DB_PATH = Path("data/app.db")


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Mở kết nối SQLite đã bật WAL và khoá ngoại.

    ``isolation_level=None`` tắt chế độ tự mở transaction của Python, để
    ``transaction()`` bên dưới kiểm soát tường minh bằng ``BEGIN IMMEDIATE``.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        path,
        timeout=30.0,
        check_same_thread=False,
        isolation_level=None,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Transaction ghi độc quyền.

    ``BEGIN IMMEDIATE`` giành khoá ghi ngay từ đầu thay vì chờ tới câu lệnh
    ghi đầu tiên. Với sổ cái quota, đây là điều kiện để hai worker không cùng
    đọc "còn 1 request" rồi cùng tiêu nó.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
