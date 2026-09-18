#!/usr/bin/env python3
"""Sinh trang xem biên bản tự chứa — mở bằng cách nháy đúp, không cần gì cả.

Công cụ này làm gì
------------------
Nhét dữ liệu của **một cuộc họp bất kỳ** vào ``frontend/preview/template.html``
rồi ghi ra một file HTML duy nhất. Không phụ thuộc file ngoài, không cần
server, không cần npm. Gửi qua Zalo cho đồng nghiệp xem cũng được.

Vì sao là một file chứ không phải hai
-------------------------------------
Bản đầu tiên tách dữ liệu ra ``_data.js`` cho gọn. Nó hỏng ngay lần dùng
đầu tiên: mở file HTML ở nơi không có file dữ liệu bên cạnh thì
``window.__TRANSCRIPT__`` là ``undefined``, và người dùng nhận được một màn
hình trắng với lỗi ``Cannot read properties of undefined`` trong console —
không nói được gì về nguyên nhân thật.

Bài học: với thứ dùng để **xem thử và gửi đi**, mỗi file phụ thêm vào là
thêm một cách để nó không chạy trên máy người khác.

Ba cách dùng
------------
Xem dữ liệu mẫu (mặc định)::

    python tools/build_preview.py

Xem cuộc họp bạn vừa chạy — đây mới là cách dùng chính::

    python tools/build_preview.py \\
        --minutes data/artifacts/mtg_20260810_kickoff/minutes_final.json \\
        --transcript data/artifacts/mtg_20260810_kickoff/transcript_chunked.json \\
        --out bien_ban_kickoff.html

Tự dò artifact mới nhất::

    python tools/build_preview.py --latest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEMPLATE = ROOT / "frontend" / "preview" / "template.html"
PLACEHOLDER = "/*__DATA_PLACEHOLDER__*/"

DEFAULT_MINUTES = ROOT / "frontend" / "src" / "mocks" / "golden_minutes.json"
DEFAULT_TRANSCRIPT = ROOT / "frontend" / "src" / "mocks" / "sample_transcript.json"


def _find_latest(artifact_root: Path) -> tuple[Path, Path] | None:
    """Tìm cuộc họp chạy gần nhất có đủ biên bản và transcript."""
    if not artifact_root.is_dir():
        return None

    candidates = [
        folder
        for folder in artifact_root.iterdir()
        if folder.is_dir() and (folder / "minutes_final.json").is_file()
    ]
    if not candidates:
        return None

    newest = max(candidates, key=lambda f: (f / "minutes_final.json").stat().st_mtime)

    # Ưu tiên bản đã chia chunk vì nó là transcript mà pipeline thật sự dùng
    # để trích xuất — evidence ID trỏ vào đúng bộ segment này.
    for name in ("transcript_chunked.json", "transcript_diarized.json", "transcript.json"):
        transcript = newest / name
        if transcript.is_file():
            return newest / "minutes_final.json", transcript
    return None


def _check_evidence(minutes: dict, transcript: dict) -> list[str]:
    """Kiểm tra mọi bằng chứng trỏ vào segment có thật.

    Nếu lệch, cơ chế truy vết sẽ im lặng không phản hồi khi bấm — mà đó là
    tính năng cốt lõi. Thà cảnh báo lúc sinh trang còn hơn để người dùng
    bấm vào một nút chết rồi tự hỏi mình làm sai ở đâu.
    """
    known = {segment["id"] for segment in transcript.get("segments", [])}
    referenced: set[str] = set()

    for group in ("decisions", "action_items", "risks", "metrics", "open_questions"):
        for item in minutes.get(group, []):
            referenced.update(item.get("evidence_segment_ids", []))
    for chapter in minutes.get("chapters", []):
        for point in chapter.get("discussion_points", []):
            referenced.update(point.get("evidence_segment_ids", []))

    problems: list[str] = []
    missing = referenced - known
    if missing:
        problems.append(
            f"{len(missing)} bằng chứng trỏ vào segment không có trong transcript: "
            f"{', '.join(sorted(missing)[:6])}. "
            "Nhiều khả năng biên bản và transcript đến từ hai lần chạy khác nhau."
        )
    if not referenced:
        problems.append("Biên bản không có bằng chứng nào — cơ chế truy vết sẽ trống.")
    return problems


def build(minutes_path: Path, transcript_path: Path, out_path: Path) -> int:
    for path in (TEMPLATE, minutes_path, transcript_path):
        if not path.is_file():
            print(f"Không tìm thấy: {path}", file=sys.stderr)
            return 1

    minutes = json.loads(minutes_path.read_text(encoding="utf-8"))
    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))

    for problem in _check_evidence(minutes, transcript):
        print(f"  Cảnh báo: {problem}", file=sys.stderr)

    payload = (
        f"window.__MINUTES__ = {json.dumps(minutes, ensure_ascii=False)};\n"
        f"window.__TRANSCRIPT__ = {json.dumps(transcript, ensure_ascii=False)};"
    )

    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        print(f"Template thiếu {PLACEHOLDER}", file=sys.stderr)
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(template.replace(PLACEHOLDER, payload), encoding="utf-8")

    size_kb = out_path.stat().st_size / 1024
    print(f"Đã ghi {out_path}  ({size_kb:.0f} KB, tự chứa)")
    print(f"  Cuộc họp : {minutes['meta']['meeting_title']}")
    print(f"  Nội dung : {len(transcript['segments'])} lượt nói, "
          f"{len(minutes['decisions'])} quyết định, {len(minutes['action_items'])} công việc")
    print("\nMở bằng cách nháy đúp file. Không cần cài gì thêm.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sinh trang xem biên bản tự chứa")
    parser.add_argument("--minutes", type=Path, help="File minutes_final.json")
    parser.add_argument("--transcript", type=Path, help="File transcript của cùng lần chạy")
    parser.add_argument(
        "--latest", action="store_true", help="Tự dò cuộc họp chạy gần nhất trong data/artifacts"
    )
    parser.add_argument(
        "--out", type=Path, default=ROOT / "frontend" / "preview" / "bien_ban.html"
    )
    parser.add_argument(
        "--open", action="store_true", dest="open_browser",
        help="Mở luôn bằng trình duyệt mặc định sau khi sinh xong",
    )
    args = parser.parse_args(argv)

    if args.latest:
        found = _find_latest(ROOT / "data" / "artifacts")
        if found is None:
            print(
                "Không tìm thấy artifact nào trong data/artifacts.\n"
                "Chạy pipeline trước, hoặc bỏ --latest để xem dữ liệu mẫu.",
                file=sys.stderr,
            )
            return 1
        minutes, transcript = found
        print(f"Dùng cuộc họp mới nhất: {minutes.parent.name}")
    else:
        minutes = args.minutes or DEFAULT_MINUTES
        transcript = args.transcript or DEFAULT_TRANSCRIPT

    code = build(minutes, transcript, args.out)
    if code == 0 and args.open_browser:
        import webbrowser
        webbrowser.open(args.out.resolve().as_uri())
    return code


if __name__ == "__main__":
    raise SystemExit(main())
