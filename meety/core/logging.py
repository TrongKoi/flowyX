"""Cấu hình log cho pipeline — che bí mật, ghi ra file, xoay vòng.

Ba việc module này giải quyết
-----------------------------
**1. API key lọt vào log.** Thư viện bên thứ ba đôi khi đưa cả URL hoặc
header vào thông báo lỗi. Một lần bật ``--verbose`` rồi dán log lên đâu đó
để hỏi là key đi theo. Bộ lọc ở đây quét mọi bản ghi log và thay key bằng
dạng che, ngay cả khi key đến từ mã mà ta không kiểm soát.

**2. Nội dung cuộc họp lọt vào log.** Với transcript mẫu thì vô hại. Với
cuộc họp thật thì file log trở thành bản sao không được bảo vệ của dữ liệu
nhạy cảm nhất trong hệ thống. Mặc định các bản ghi ở mức DEBUG có khả năng
chứa nội dung sẽ bị cắt ngắn; muốn xem đầy đủ phải bật cờ có ý thức.

**3. Không có log lưu lại.** Trước đó log chỉ ra ``stderr`` rồi biến mất.
Khi một lần chạy thật hỏng giữa chừng — mà đó là lúc cần log nhất — không
còn gì để đọc.

Vì sao che chứ không cấm ghi
----------------------------
Cách an toàn tuyệt đối là không ghi gì. Nhưng khi Gemini trả HTTP 400 vì
schema sai, thứ duy nhất giúp bạn tìm ra nguyên nhân là log. Nên lựa chọn ở
đây là: **ghi đủ để gỡ lỗi, che đủ để chia sẻ được**. Sau khi lọc, file log
có thể gửi cho người khác xem mà không lộ key.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import re
from pathlib import Path

__all__ = [
    "SecretRedactingFilter",
    "configure_logging",
    "register_secret",
    "redact",
]

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Groq: gsk_ + 52 ký tự base62
    re.compile(r"\bgsk_[A-Za-z0-9]{20,}"),
    # Google API key kiểu cũ
    re.compile(r"\bAIza[A-Za-z0-9_\-]{20,}"),
    # Google AI Studio kiểu mới
    re.compile(r"\bAQ\.[A-Za-z0-9_\-]{20,}"),
    # OpenAI-compatible, phòng khi thêm nhà cung cấp khác
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),
)

_KNOWN_SECRETS: set[str] = set()
"""Bí mật đã biết, đăng ký lúc chạy.

Cần cả danh sách này lẫn các mẫu regex ở trên. Regex bắt được key có định
dạng quen thuộc kể cả khi ta chưa từng thấy nó; danh sách bắt được key mà
nhà cung cấp đặt theo định dạng ta chưa lường trước. Thiếu một trong hai là
có lỗ.
"""

_MAX_DEBUG_CHARS = 300
"""Trần độ dài bản ghi DEBUG khi chưa bật ghi nội dung đầy đủ."""


def register_secret(value: str) -> None:
    """Đăng ký một bí mật để bộ lọc che nó ở mọi nơi.

    Bỏ qua chuỗi quá ngắn: che một chuỗi 6 ký tự sẽ khớp nhầm vào văn bản
    bình thường và làm log không đọc được.
    """
    if value and len(value) >= 12:
        _KNOWN_SECRETS.add(value)


def _mask(value: str) -> str:
    return f"{value[:4]}...{value[-4:]}" if len(value) > 12 else "***"


def redact(text: str) -> str:
    """Thay mọi bí mật trong một chuỗi bằng dạng che."""
    for secret in _KNOWN_SECRETS:
        if secret in text:
            text = text.replace(secret, _mask(secret))
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(lambda m: _mask(m.group(0)), text)
    return text


class SecretRedactingFilter(logging.Filter):
    """Che bí mật và cắt ngắn bản ghi DEBUG dài.

    Lọc ở tầng ``Filter`` chứ không ở tầng ``Formatter`` là có chủ đích: bộ
    lọc chạy cho **mọi** handler, kể cả handler do thư viện bên thứ ba gắn
    thêm về sau. Đặt ở formatter thì chỉ handler của ta được bảo vệ.
    """

    def __init__(self, *, allow_full_content: bool = False) -> None:
        super().__init__()
        self.allow_full_content = allow_full_content

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except (TypeError, ValueError):
            # Tham số định dạng sai — để logging tự báo lỗi theo cách của nó.
            return True

        cleaned = redact(message)

        if (
            not self.allow_full_content
            and record.levelno <= logging.DEBUG
            and len(cleaned) > _MAX_DEBUG_CHARS
        ):
            omitted = len(cleaned) - _MAX_DEBUG_CHARS
            cleaned = (
                f"{cleaned[:_MAX_DEBUG_CHARS]}... "
                f"[cắt {omitted} ký tự — dùng --log-full-content để xem đủ]"
            )

        if cleaned != message:
            # Ghi đè msg và xoá args: nếu giữ args, handler sẽ nội suy lại và
            # bí mật quay về nguyên vẹn.
            record.msg = cleaned
            record.args = ()
        return True


def configure_logging(
    *,
    verbose: bool = False,
    log_file: Path | None = None,
    allow_full_content: bool = False,
    max_bytes: int = 2_000_000,
    backup_count: int = 3,
) -> SecretRedactingFilter:
    """Dựng cấu hình log cho toàn tiến trình.

    Args:
        verbose: Bật mức DEBUG thay vì INFO.
        log_file: Ghi thêm ra file, xoay vòng khi vượt ``max_bytes``.
        allow_full_content: Cho phép bản ghi DEBUG dài đi qua nguyên vẹn.
            Bí mật vẫn bị che — cờ này chỉ nới phần cắt ngắn.
        max_bytes: Ngưỡng xoay vòng file log.
        backup_count: Số file log cũ giữ lại.

    Returns:
        Bộ lọc đã gắn, để nơi gọi đăng ký thêm bí mật về sau.
    """
    level = logging.DEBUG if verbose else logging.INFO
    redactor = SecretRedactingFilter(allow_full_content=allow_full_content)

    # Đăng ký key đang có trong môi trường ngay lúc dựng log, để chúng được
    # che kể cả khi lọt ra từ traceback của thư viện bên thứ ba.
    for name in ("GEMINI_API_KEY", "GROQ_API_KEY", "GOOGLE_API_KEY"):
        register_secret(os.environ.get(name, ""))

    root = logging.getLogger()
    root.setLevel(level)
    for existing in list(root.handlers):
        root.removeHandler(existing)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)-7s %(name)s: %(message)s"))
    console.addFilter(redactor)
    root.addHandler(console)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        rotating = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        rotating.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-7s %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        rotating.addFilter(redactor)
        root.addHandler(rotating)

    # Thư viện HTTP nói rất nhiều ở mức DEBUG và hay đưa cả URL kèm tham số
    # truy vấn vào log. Ghìm chúng lại một mức.
    for noisy in ("httpx", "httpcore", "urllib3", "google", "groq", "asyncio"):
        logging.getLogger(noisy).setLevel(max(level, logging.WARNING))

    return redactor
