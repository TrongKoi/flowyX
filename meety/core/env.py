"""Nạp bí mật từ file ``.env`` vào tiến trình đang chạy — và chỉ tiến trình đó.

Vì sao có module này
--------------------
Trước đó, cách duy nhất để đưa API key vào chương trình là tự đặt biến môi
trường trong PowerShell. Cách đó có ba vấn đề thật:

1. **Dễ đặt nhầm phạm vi.** ``setx`` ghi vào registry Windows, key tồn tại
   vĩnh viễn cho mọi tiến trình của mọi ứng dụng — kể cả sau khi bạn xoá
   project. Người ta hay dùng ``setx`` vì nó "đỡ phải gõ lại".
2. **Key lọt vào lịch sử shell.** ``$env:GEMINI_API_KEY = "AQ.Ab8..."`` được
   PowerShell lưu vào ``ConsoleHost_history.txt`` dưới dạng văn bản thuần.
3. **Key hiện trên màn hình.** Chỉ cần một lần chia sẻ màn hình hoặc một
   screenshot là lộ.

Đọc thẳng từ file giải quyết cả ba: key chỉ nằm trong ``.env`` (đã bị
``.gitignore`` chặn), chỉ được nạp vào **tiến trình hiện tại**, và biến mất
khi chương trình kết thúc.

Vì sao không dùng ``python-dotenv``
-----------------------------------
Project cố ý chỉ phụ thuộc 5 gói. Việc cần làm ở đây là đọc một file văn bản
vài dòng — thêm một gói bên thứ ba chỉ để làm việc đó là cái giá không đáng,
nhất là với một gói nằm trên đường đi của **bí mật**. Ít mã bên thứ ba chạm
vào API key thì càng tốt.

Nguyên tắc: biến môi trường có sẵn LUÔN thắng ``.env``
------------------------------------------------------
Nếu ``GEMINI_API_KEY`` đã tồn tại trong môi trường, module này không ghi đè.
Đó là quy ước chuẩn: nó cho phép CI và container tiêm bí mật theo cách của
chúng mà không cần sửa file, và cho phép bạn tạm ghi đè một key cho đúng một
lần chạy.
"""

from __future__ import annotations

import logging
import os
import stat
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = [
    "load_dotenv",
    "mask_secret",
    "check_permissions",
    "SECRET_KEYS",
    "WINDOWS_HARDEN_COMMAND",
]

SECRET_KEYS: frozenset[str] = frozenset({"GEMINI_API_KEY", "GROQ_API_KEY", "GOOGLE_API_KEY"})
"""Các biến được coi là bí mật — không bao giờ in ra nguyên vẹn."""

_EXPORT_PREFIX = "export "


def mask_secret(value: str) -> str:
    """Che một bí mật để in ra an toàn.

    Giữ lại 4 ký tự đầu và 4 ký tự cuối để bạn còn đối chiếu được "đúng key
    mình vừa tạo không", nhưng không đủ để ai đó dùng lại.

    >>> mask_secret("gsk_1234567890abcdefXYZ")
    'gsk_...fXYZ (22 ký tự)'
    """
    if not value:
        return "(rỗng)"
    if len(value) <= 12:
        return f"(quá ngắn — {len(value)} ký tự)"
    return f"{value[:4]}...{value[-4:]} ({len(value)} ký tự)"


def _parse_value(raw: str) -> str:
    """Tách giá trị thật ra khỏi ngoặc bao quanh và chú thích cuối dòng.

    Thứ tự xử lý ở đây quan trọng và dễ làm sai. Nếu bỏ ngoặc trước rồi mới
    cắt chú thích, thì ``"gsk_abc"  # ghi chú`` sẽ không khớp cặp ngoặc (ký
    tự cuối là ``ú`` chứ không phải ``"``) nên ngoặc còn nguyên, và key gửi
    đi kèm dấu ``"`` — API trả về 401 với thông báo chẳng liên quan gì tới
    nguyên nhân thật.

    Nhưng cắt chú thích trước cũng sai: một bí mật hoàn toàn có thể chứa
    ``" #"``. Cách đúng là xét ngoặc trước — nếu giá trị mở bằng ngoặc thì
    mọi thứ tới ngoặc đóng là giá trị, phần sau bỏ hết; nếu không có ngoặc
    thì mới cắt ở ``" #"``.
    """
    value = raw.strip()
    if not value:
        return ""

    quote = value[0]
    if quote in {'"', "'"}:
        closing = value.find(quote, 1)
        if closing != -1:
            return value[1:closing]
        # Ngoặc mở mà không đóng: coi như người dùng gõ thiếu, bỏ ngoặc mở.
        return value[1:].strip()

    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    return value.strip()


def load_dotenv(path: Path | str = ".env", *, override: bool = False) -> dict[str, str]:
    """Đọc ``.env`` và nạp vào ``os.environ`` của tiến trình hiện tại.

    Args:
        path: Đường dẫn file ``.env``.
        override: Cho phép ghi đè biến môi trường đã tồn tại. Mặc định
            ``False`` — biến có sẵn luôn thắng.

    Returns:
        Bảng các cặp khoá/giá trị đã **thực sự** nạp. Khoá bị bỏ qua vì đã
        có sẵn trong môi trường sẽ không xuất hiện ở đây.

    Không có file thì trả về bảng rỗng và không báo lỗi: chạy ``--mock``
    không cần key nào, và bắt buộc phải có ``.env`` sẽ làm hỏng đường đó.
    """
    env_path = Path(path)
    if not env_path.is_file():
        logger.debug("Không có %s, bỏ qua bước nạp bí mật.", env_path)
        return {}

    loaded: dict[str, str] = {}

    for number, raw in enumerate(
        env_path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(_EXPORT_PREFIX):
            line = line[len(_EXPORT_PREFIX) :].lstrip()

        name, separator, value = line.partition("=")
        if not separator:
            logger.warning("%s dòng %d: thiếu dấu '=', bỏ qua.", env_path, number)
            continue

        name = name.strip()
        if not name:
            continue

        value = _parse_value(value)

        if not value:
            logger.warning(
                "%s dòng %d: %s chưa có giá trị. Điền key vào rồi chạy lại.",
                env_path, number, name,
            )
            continue

        if name in os.environ and not override:
            logger.debug("%s đã có sẵn trong môi trường, giữ nguyên.", name)
            continue

        os.environ[name] = value
        loaded[name] = value

    if loaded:
        summary = ", ".join(
            f"{k}={mask_secret(v)}" if k in SECRET_KEYS else k
            for k, v in sorted(loaded.items())
        )
        logger.info("Đã nạp %d biến từ %s: %s", len(loaded), env_path, summary)

    return loaded


WINDOWS_HARDEN_COMMAND = (
    'icacls "{path}" /inheritance:r /grant:r "$($env:USERNAME):(M)"'
)
"""Lệnh khoá quyền đọc ``.env`` trên Windows.

Hai chi tiết ở đây đều là bẫy thật, không phải chuộng hình thức.

**Vì sao ``$($env:USERNAME)`` chứ không phải ``$env:USERNAME``.** PowerShell
cho phép dấu hai chấm trong đường dẫn biến (đó là cách ``$env:``, ``$global:``
hoạt động), nên trong chuỗi ``"$env:USERNAME:(M)"`` bộ phân tích nuốt luôn
dấu hai chấm thứ hai và đi tìm biến tên ``env:USERNAME:``. Biến đó không tồn
tại nên nó nở ra chuỗi rỗng, và icacls chỉ nhận được ``(M)`` — báo lỗi
``Invalid parameter``. Bọc trong ``$(...)`` hoặc ``${env:USERNAME}`` thì bộ
phân tích biết chỗ kết thúc.

**Vì sao ``(M)`` chứ không phải ``(R,W)``.** Quyền ``W`` không bao gồm xoá.
Nhiều trình soạn thảo — kể cả Notepad bản mới và VS Code khi bật lưu nguyên
tử — lưu file bằng cách ghi file tạm rồi thay thế, nên thiếu quyền xoá sẽ
làm việc sửa ``.env`` thất bại với thông báo khó hiểu. ``(M)`` là Modify:
đọc, ghi, xoá, nhưng không đổi được quyền hay chủ sở hữu.
"""


def _windows_inheritance_present(path: Path) -> bool | None:
    """Kiểm tra file còn thừa kế quyền từ thư mục cha không.

    Trả về ``None`` khi không kết luận được (thiếu ``icacls``, hết thời gian
    chờ). Dò ký tự cờ ``(I)`` trong kết quả của ``icacls`` thay vì đọc tên
    nhóm: tên nhóm bị dịch theo ngôn ngữ Windows, còn cờ thì không.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["icacls", str(path)],
            capture_output=True, text=True, timeout=15, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0 or not result.stdout:
        return None
    return "(I)" in result.stdout


def check_permissions(path: Path | str = ".env") -> list[str]:
    """Cảnh báo nếu file ``.env`` đang để lỏng quyền đọc.

    Trên Linux/macOS đọc trực tiếp bit quyền. Trên Windows mô hình quyền là
    ACL nên ``stat`` không nói lên điều gì — ở đó hỏi ``icacls`` và **chỉ**
    cảnh báo khi file thật sự còn thừa kế quyền, để người đã khoá rồi không
    bị nhắc lại ở mỗi lần chạy.
    """
    env_path = Path(path)
    if not env_path.is_file():
        return []

    warnings: list[str] = []

    if sys.platform == "win32":
        inherited = _windows_inheritance_present(env_path)
        if inherited is False:
            return []
        prefix = (
            "Không kiểm tra được quyền của .env"
            if inherited is None
            else ".env đang thừa kế quyền từ thư mục cha nên tài khoản khác có "
            "thể đọc được"
        )
        warnings.append(
            f"{prefix}. Giới hạn quyền chỉ cho tài khoản của bạn:\n"
            f"  {WINDOWS_HARDEN_COMMAND.format(path=env_path)}"
        )
        return warnings

    mode = env_path.stat().st_mode
    if mode & (stat.S_IRGRP | stat.S_IROTH):
        warnings.append(
            f"{env_path} đang cho phép người dùng khác đọc. Sửa bằng: "
            f"chmod 600 {env_path}"
        )
    return warnings
