"""Xuất một biên bản Meety ra HAI tệp Word: bản tiêu chuẩn và bản dễ đọc.

Đây là cách FlowyX dùng lõi Meety mà không cần giao diện web của Meety:

    # 1. Chạy pipeline từ transcript Zoom/Meet/Teams (hoặc ghi âm)
    python main.py --input cuoc_hop.vtt --date 2026-09-17 --mock

    # 2. Xuất Word hai bản từ tệp _minutes.json vừa có
    python xuat_word.py output/<id>_minutes.json

    # 3. (tuỳ chọn) Chép _minutes.json sang điện thoại, mở trong tab Biên bản
    #    của FlowyX -> app xuất Word được ngay trên máy.

Chỉ dùng thư viện chuẩn: không cần pydantic hay khoá API cho bước này.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from exporters.docx import build_docx
from exporters.docx_de_doc import build_docx_de_doc


def xuat(duong_dan: Path, thu_muc: Path | None = None) -> tuple[Path, Path]:
    minutes = json.loads(duong_dan.read_text(encoding="utf-8"))
    thu_muc = thu_muc or duong_dan.parent
    thu_muc.mkdir(parents=True, exist_ok=True)
    goc = duong_dan.stem.removesuffix("_minutes")
    chuan = thu_muc / f"{goc}_bien_ban.docx"
    de_doc = thu_muc / f"{goc}_bien_ban_de_doc.docx"
    chuan.write_bytes(build_docx(minutes))
    de_doc.write_bytes(build_docx_de_doc(minutes))
    return chuan, de_doc


def main() -> int:
    ap = argparse.ArgumentParser(description="Xuất biên bản Meety ra Word: bản tiêu chuẩn + bản dễ đọc")
    ap.add_argument("minutes_json", type=Path, help="tệp <id>_minutes.json do main.py tạo")
    ap.add_argument("--out", type=Path, default=None, help="thư mục ghi tệp (mặc định: cạnh tệp JSON)")
    a = ap.parse_args()
    if not a.minutes_json.is_file():
        print(f"Không thấy tệp: {a.minutes_json}", file=sys.stderr)
        return 2
    try:
        chuan, de_doc = xuat(a.minutes_json, a.out)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Tệp không phải biên bản Meety hợp lệ: {e}", file=sys.stderr)
        return 1
    print(f"Bản tiêu chuẩn : {chuan}")
    print(f"Bản dễ đọc     : {de_doc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
