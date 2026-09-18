#!/usr/bin/env python3
"""Tự kiểm tra môi trường trước khi chạy pipeline.

Đặt file này CẠNH main.py rồi chạy::

    python doctor.py

Script chỉ dùng thư viện chuẩn nên chạy được kể cả khi chưa cài gì.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

REQUIRED_PACKAGES: list[tuple[str, str, str]] = [
    ("pydantic", "pydantic>=2.9", "bắt buộc — toàn bộ schemas/"),
    ("pytest", "pytest>=8.0", "chỉ cần khi chạy test"),
    ("google.genai", "google-genai>=1.0", "chỉ cần khi KHÔNG dùng --mock"),
    ("groq", "groq>=0.11", "chỉ cần khi phiên âm từ file audio"),
]

REQUIRED_LAYOUT: list[str] = [
    "main.py",
    "DOC_TRUOC_TIEN.md",
    "tai_lieu_goc/01_Blueprint_San_pham.md",
    "tai_lieu_goc/02_Backend_Design_0d.md",
    "tai_lieu_goc/00_Ban_giao_backend_core.md",
    "core/cache.py",
    "core/quota.py",
    "core/db.py",
    "core/env.py",
    "core/logging.py",
    "pipeline/orchestrator.py",
    "nlp/vn_dates.py",
    "nlp/vocative.py",
    "schemas/common.py",
    "schemas/transcript.py",
    "schemas/minutes.py",
    "schemas/extraction.py",
    "schemas/reconciled.py",
    "providers/base.py",
    "providers/llm/gemini.py",
    "providers/llm/mock.py",
    "providers/asr/groq_whisper.py",
    "pipeline/s0_ingest.py",
    "pipeline/s2_diarize.py",
    "pipeline/s3_chunk.py",
    "pipeline/s4_extract.py",
    "pipeline/s5_reconcile.py",
    "pipeline/s6_compose.py",
    "pipeline/s7_validate.py",
    "exporters/markdown.py",
    "tests/fixtures/sample_transcript.json",
    "tests/fixtures/mock_llm/extract_c_01.json",
    "tests/fixtures/mock_llm/extract_c_02.json",
    "tests/fixtures/mock_llm/topic_grouping.json",
    "tests/fixtures/mock_llm/compose.json",
    "tests/fixtures/mock_llm/extract_c_all.json",
    "tests/unit/test_vn_dates.py",
    "tests/unit/test_vocative.py",
    "tests/unit/test_chunk.py",
    "tests/unit/test_markdown_export.py",
    "tests/unit/test_ingest.py",
    "tests/unit/test_env.py",
    "tests/unit/test_logging.py",
    "tests/unit/test_orchestrator.py",
    "tests/unit/test_frontend_contract.py",
    "tools/kichban_kickoff.json",
    "tools/make_test_audio.py",
    "tools/gen_types.py",
    "frontend/src/types/meeting.ts",
    "frontend/src/mocks/golden_minutes.json",
    "frontend/preview/template.html",
    "frontend/preview/template_columns.html",
    "frontend/preview/template_light_scroll.html",
    "frontend/preview/template_dark_dock.html",
    "frontend/preview/template_odylytics.html",
    "frontend/preview/template_mmai_soft.html",
    "tools/build_preview.py",
    "tests/integration/test_pipeline_e2e.py",
    "tests/integration/test_ingest_e2e.py",
    "tests/fixtures/ingest/zoom_sprint23.vtt",
    "tests/fixtures/ingest/teams_standup.vtt",
    "tests/fixtures/ingest/meet_review.srt",
    "tests/fixtures/ingest/plain_planning.txt",
    "tests/fixtures/ingest/plain_no_timestamp.txt",
]

OK = "  [OK]  "
BAD = "  [LỖI] "
WARN = "  [!]   "


def check_python_version() -> bool:
    print("\n1. PHIÊN BẢN PYTHON")
    print(f"     Đang chạy: {sys.version.split()[0]}")
    print(f"     Đường dẫn: {sys.executable}")

    if sys.version_info < (3, 10):
        print(f"{BAD}Cần Python 3.10 trở lên (code dùng cú pháp `X | None`).")
        return False

    print(f"{OK}Phiên bản phù hợp.")

    if sys.version_info >= (3, 14):
        print(
            "     Lưu ý: Python 3.14 còn rất mới. Nếu `pip install` báo lỗi biên dịch,\n"
            "     nhiều khả năng gói chưa có bản dựng sẵn cho phiên bản này —\n"
            "     cài thêm Python 3.12 rồi tạo venv bằng nó là cách nhanh nhất."
        )

    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv:
        print(f"{OK}Đang chạy trong môi trường ảo.")
    else:
        print(
            f"{WARN}Đang chạy bằng Python hệ thống, KHÔNG phải môi trường ảo.\n"
            "     Cài thư viện thẳng vào Python hệ thống sẽ trộn lẫn với các dự án\n"
            "     khác và rất khó gỡ về sau. Tạo môi trường ảo trước:\n"
            "       python -m venv .venv\n"
            "       .\\.venv\\Scripts\\Activate.ps1      (PowerShell)\n"
            "       source .venv/bin/activate          (macOS/Linux)"
        )

    print(
        "     Lưu ý: nếu máy có nhiều bản Python, luôn dùng `python -m pip install`"
        "\n     thay vì `pip install` để gói được cài đúng bản đang chạy."
    )
    return True


def check_timezone_database() -> bool:
    """Kiểm tra tz database — điểm chết thầm lặng trên Windows."""
    print("\n2. CƠ SỞ DỮ LIỆU MÚI GIỜ")
    try:
        from zoneinfo import ZoneInfo

        ZoneInfo("America/Los_Angeles")
    except Exception as exc:
        print(f"{WARN}{type(exc).__name__}: {exc}")
        print(
            "     Không sao: core/quota.py có sẵn bộ tính giờ Thái Bình Dương"
            "\n     tự lập nên vẫn chạy bình thường mà không cần gói tzdata."
        )
        return True

    print(f"{OK}Tra cứu được múi giờ America/Los_Angeles.")
    return True


def check_encoding() -> bool:
    """Kiểm tra mã hoá — nguồn lỗi khó đoán nhất trên Windows tiếng Việt."""
    import locale

    print("\n3. MÃ HOÁ VĂN BẢN")
    preferred = locale.getpreferredencoding(False)
    stdout_encoding = getattr(sys.stdout, "encoding", "?")
    utf8_mode = bool(getattr(sys.flags, "utf8_mode", 0))

    print(f"     Mã trang mặc định: {preferred}")
    print(f"     Encoding stdout  : {stdout_encoding}")
    print(f"     Chế độ UTF-8     : {'bật' if utf8_mode else 'tắt'}")

    healthy = True

    requirements = ROOT / "requirements.txt"
    if requirements.exists():
        raw = requirements.read_bytes()
        try:
            raw.decode(preferred)
            print(f"{OK}pip đọc được requirements.txt bằng {preferred}.")
        except UnicodeDecodeError as exc:
            healthy = False
            print(f"{BAD}pip KHÔNG đọc được requirements.txt bằng {preferred}:")
            print(f"          {exc}")
            print(
                "     pip đọc file này bằng mã trang hệ điều hành chứ không phải"
                "\n     UTF-8, nên file chỉ được chứa ký tự ASCII."
            )

    if not utf8_mode and preferred.lower() not in {"utf-8", "utf8", "cp65001"}:
        print(
            f"{WARN}Nên bật chế độ UTF-8 để tránh lỗi khi chuyển hướng kết quả"
            "\n     ra file (main.py in các ký tự như ✓, █ mà mã trang cũ không có)."
        )
        print("     PowerShell:  $env:PYTHONUTF8 = '1'")

    return healthy


def check_packages() -> list[str]:
    print("\n4. THƯ VIỆN")
    missing: list[str] = []

    for module_name, package_spec, note in REQUIRED_PACKAGES:
        try:
            found = importlib.util.find_spec(module_name) is not None
        except (ImportError, ValueError):
            found = False

        if found:
            print(f"{OK}{module_name:16s} — {note}")
        else:
            print(f"{WARN}{module_name:16s} — thiếu ({note})")
            missing.append(package_spec)

    return missing


def check_layout() -> list[str]:
    """Kiểm tra cấu trúc thư mục — nguyên nhân của ModuleNotFoundError."""
    print("\n5. CẤU TRÚC THƯ MỤC")
    print(f"     Thư mục gốc: {ROOT}")

    missing = [path for path in REQUIRED_LAYOUT if not (ROOT / path).exists()]

    if not missing:
        print(f"{OK}Đủ {len(REQUIRED_LAYOUT)} file/thư mục cần thiết.")
        return []

    print(f"{BAD}Thiếu {len(missing)}/{len(REQUIRED_LAYOUT)} mục:")
    for path in missing:
        print(f"          {path}")

    stray = sorted(
        p.name
        for p in ROOT.glob("*.py")
        if p.name not in {"main.py", "doctor.py"}
    )
    if stray:
        print(
            f"\n{WARN}Có file .py nằm sai chỗ ở thư mục gốc: {', '.join(stray[:8])}"
        )
        print("     Chúng phải nằm trong thư mục con tương ứng (core/, nlp/, ...).")

    return missing


def check_imports() -> bool:
    print("\n6. THỬ IMPORT")
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    modules = (
        "schemas.common",
        "nlp.vn_dates",
        "nlp.vocative",
        "core.env",
        "core.logging",
        "pipeline.orchestrator",
        "core.cache",
        "core.quota",
        "pipeline.s0_ingest",
        "pipeline.s2_diarize",
        "pipeline.s3_chunk",
        "exporters.markdown",
    )
    for module_name in modules:
        try:
            __import__(module_name)
        except Exception as exc:
            print(f"{BAD}{module_name}: {type(exc).__name__}: {exc}")
            return False
        print(f"{OK}{module_name}")
    return True


def main() -> int:
    print("=" * 62)
    print("  KIỂM TRA MÔI TRƯỜNG — Hệ thống Tóm tắt Cuộc họp")
    print("=" * 62)

    version_ok = check_python_version()
    timezone_ok = check_timezone_database()
    encoding_ok = check_encoding()
    missing_packages = check_packages()
    missing_files = check_layout()

    imports_ok = False
    if not missing_files:
        imports_ok = check_imports()
    else:
        print("\n6. THỬ IMPORT")
        print(f"{WARN}Bỏ qua vì cấu trúc thư mục chưa đủ.")

    print("\n" + "=" * 62)

    if missing_files:
        print("\nVIỆC CẦN LÀM — sắp xếp lại thư mục:")
        print("  Mọi file phải nằm đúng vị trí, CẠNH main.py. Ví dụ đúng:")
        print("    D:\\Meeting Minutes AI\\main.py")
        print("    D:\\Meeting Minutes AI\\core\\cache.py")
        print("    D:\\Meeting Minutes AI\\schemas\\common.py")

    if missing_packages or not timezone_ok:
        install = list(missing_packages)
        if not timezone_ok:
            install.insert(0, "tzdata")
        print("\nVIỆC CẦN LÀM — cài thư viện:")
        print(f"  python -m pip install {' '.join(install)}")

    if (
        not (missing_files or missing_packages)
        and timezone_ok
        and encoding_ok
        and imports_ok
    ):
        print("\nMôi trường sẵn sàng. Chạy thử:")
        print(
            "  python main.py --input tests/fixtures/sample_transcript.json"
            " --skip-stt --date 2026-07-22 --mock"
        )
        return 0

    print()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
