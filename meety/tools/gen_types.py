#!/usr/bin/env python3
"""Sinh TypeScript interface từ Pydantic schema — nguồn sự thật là backend.

Vì sao không gõ tay
-------------------
Cách thông thường là mở ``schemas/minutes.py`` ra rồi gõ lại thành
TypeScript. Cách đó hỏng theo đúng một kiểu, luôn luôn: ai đó đổi backend,
quên đổi frontend, và **TypeScript vẫn biên dịch sạch** vì nó chỉ biết cái
interface đã gõ tay chứ không biết dữ liệu thật. Lỗi rơi xuống lúc chạy,
dưới dạng ``undefined`` ở một chỗ chẳng liên quan.

Sinh tự động biến sai lệch đó thành lỗi biên dịch. Chạy ``--check`` trong
test khiến việc sửa backend mà quên chạy lại bộ sinh trở thành test đỏ.

Một chi tiết dễ sai
-------------------
JSON Schema đánh dấu trường có giá trị mặc định là **không bắt buộc**. Nhưng
backend luôn dùng ``model_dump(mode="json")`` không kèm ``exclude_none``,
nên mọi trường **đều có mặt** trong JSON gửi đi. Nếu để chúng thành optional
(``field?: T``) thì frontend sẽ rải đầy kiểm tra ``undefined`` vô nghĩa và
che mất chỗ ``null`` thật sự có ý nghĩa — như ``assignee: null`` nghĩa là
"không ai nhận việc", một thông tin quan trọng chứ không phải thiếu dữ liệu.

Vì vậy mọi trường đều bắt buộc; chỉ những trường thật sự nhận ``None`` mới
mang ``| null``.

Cách dùng::

    python tools/gen_types.py                  # ghi ra frontend/src/types/
    python tools/gen_types.py --check          # chỉ kiểm tra, không ghi
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.minutes import StructuredMinutes  # noqa: E402
from schemas.transcript import Transcript  # noqa: E402

HEADER = """// ============================================================================
//  KHÔNG SỬA FILE NÀY BẰNG TAY
//
//  Sinh tự động từ Pydantic schema của backend:
//    schemas/minutes.py, schemas/transcript.py, schemas/common.py
//
//  Sinh lại:      python tools/gen_types.py
//  Kiểm tra sync: python tools/gen_types.py --check
//
//  Mọi trường đều bắt buộc vì backend dùng model_dump(mode="json") không
//  kèm exclude_none — mọi trường đều có mặt trong JSON. `| null` chỉ xuất
//  hiện ở nơi giá trị null MANG Ý NGHĨA (ví dụ assignee: null = chưa ai nhận).
// ============================================================================

"""

_PRIMITIVES: dict[str, str] = {
    "string": "string",
    "integer": "number",
    "number": "number",
    "boolean": "boolean",
    "null": "null",
}


def _ts_type(node: dict[str, Any]) -> str:
    """Đổi một node JSON Schema thành biểu thức kiểu TypeScript."""
    if "$ref" in node:
        return node["$ref"].rsplit("/", 1)[-1]

    if "anyOf" in node or "oneOf" in node:
        options = node.get("anyOf") or node["oneOf"]
        parts = [_ts_type(option) for option in options]
        # Gộp trùng nhưng giữ thứ tự, và luôn đẩy `null` xuống cuối cho dễ đọc.
        seen: list[str] = []
        for part in parts:
            if part not in seen:
                seen.append(part)
        if "null" in seen:
            seen.remove("null")
            seen.append("null")
        return " | ".join(seen)

    if "enum" in node:
        return " | ".join(f'"{value}"' for value in node["enum"])

    kind = node.get("type")

    if kind == "array":
        items = node.get("items")
        if not items:
            return "unknown[]"
        inner = _ts_type(items)
        return f"({inner})[]" if "|" in inner else f"{inner}[]"

    if kind == "object":
        extra = node.get("additionalProperties")
        if isinstance(extra, dict):
            return f"Record<string, {_ts_type(extra)}>"
        return "Record<string, unknown>"

    if isinstance(kind, list):
        return " | ".join(_PRIMITIVES.get(k, "unknown") for k in kind)

    return _PRIMITIVES.get(kind, "unknown")


def _doc_comment(node: dict[str, Any], indent: str) -> list[str]:
    pieces: list[str] = []
    description = (node.get("description") or "").strip()
    if description:
        pieces.extend(description.splitlines())

    fmt = node.get("format")
    if fmt in {"date", "date-time"}:
        pieces.append(f"Chuỗi ISO {'YYYY-MM-DD' if fmt == 'date' else 'ISO-8601'}.")

    for key, label in (("minimum", "tối thiểu"), ("maximum", "tối đa")):
        if key in node:
            pieces.append(f"Giá trị {label}: {node[key]}.")

    if not pieces:
        return []
    if len(pieces) == 1:
        return [f"{indent}/** {pieces[0]} */"]
    body = [f"{indent} * {line}" for line in pieces]
    return [f"{indent}/**", *body, f"{indent} */"]


def _render_enum(name: str, node: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.extend(_doc_comment(node, ""))
    values = " | ".join(f'"{value}"' for value in node["enum"])
    lines.append(f"export type {name} = {values};")
    return "\n".join(lines)


def _render_interface(name: str, node: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.extend(_doc_comment(node, ""))
    lines.append(f"export interface {name} {{")

    for field, spec in node.get("properties", {}).items():
        lines.extend(_doc_comment(spec, "  "))
        lines.append(f"  {field}: {_ts_type(spec)};")

    lines.append("}")
    return "\n".join(lines)


def _render_model(root_name: str, schema: dict[str, Any]) -> tuple[list[str], set[str]]:
    blocks: list[str] = []
    defs = schema.get("$defs", {})

    for name in sorted(defs):
        node = defs[name]
        blocks.append(
            _render_enum(name, node) if "enum" in node else _render_interface(name, node)
        )

    blocks.append(_render_interface(root_name, schema))
    return blocks, set(defs)


def build_source() -> str:
    """Dựng nội dung file ``meeting.ts``."""
    minutes_blocks, minutes_defs = _render_model(
        "StructuredMinutes", StructuredMinutes.model_json_schema()
    )
    transcript_blocks, transcript_defs = _render_model(
        "Transcript", Transcript.model_json_schema()
    )

    # Hai schema dùng chung nhiều enum trong schemas/common.py. Khai trùng sẽ
    # làm TypeScript báo lỗi định danh trùng lặp, nên chỉ giữ bản đầu tiên.
    shared = minutes_defs & transcript_defs
    kept_transcript = [
        block
        for block in transcript_blocks
        if not any(
            block.startswith((f"export type {n} ", f"export interface {n} "))
            or f"\nexport type {n} =" in block
            or f"\nexport interface {n} " in block
            for n in shared
        )
    ]

    parts = [
        HEADER,
        "// ---------------------------------------------------------------------------\n"
        "//  BIÊN BẢN — schemas/minutes.py\n"
        "// ---------------------------------------------------------------------------\n",
        "\n\n".join(minutes_blocks),
        "\n// ---------------------------------------------------------------------------\n"
        "//  TRANSCRIPT — schemas/transcript.py\n"
        f"//  (bỏ qua {len(shared)} kiểu dùng chung đã khai ở trên)\n"
        "// ---------------------------------------------------------------------------\n",
        "\n\n".join(kept_transcript),
        _render_helpers(),
    ]
    return "\n".join(parts) + "\n"


def _render_helpers() -> str:
    """Vài kiểu chỉ frontend cần — không sinh từ backend nên viết tay ở đây."""
    return '''
// ---------------------------------------------------------------------------
//  KIỂU CHỈ FRONTEND DÙNG
//  Không có đối ứng ở backend nên viết tay. Giữ tách bạch với phần sinh tự
//  động ở trên để lần sinh lại không xoá mất.
// ---------------------------------------------------------------------------

/** Các pha của pipeline, khớp với Stage trong pipeline/orchestrator.py */
export type Stage =
  | "diarize"
  | "chunk"
  | "extract"
  | "reconcile"
  | "compose"
  | "validate";

/** Trạng thái một pha, khớp với StageStatus trong orchestrator.py */
export type StageStatus =
  | "started"
  | "done"
  | "skipped"
  | "restored"
  | "failed";

/** Sự kiện tiến độ do orchestrator phát ra trong lúc chạy. */
export interface StageEvent {
  stage: Stage;
  status: StageStatus;
  message: string;
  elapsed_ms: number;
  detail: Record<string, unknown>;
}

/** Mọi thực thể mang bằng chứng đều có hình dạng này. */
export interface HasEvidence {
  evidence: string[];
}

/** Trạng thái chọn dùng chung giữa ba cột của màn hình Review. */
export interface TraceSelection {
  /** ID của mục đang chọn ở cột giữa (vd "a_001"). */
  itemId: string | null;
  /** Các segment ID cần highlight ở cột trái. */
  segmentIds: string[];
  /** Mốc thời gian để nhảy audio tới, tính bằng mili giây. */
  seekMs: number | null;
}
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("frontend/src/types/meeting.ts"),
        help="Nơi ghi file TypeScript",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Chỉ kiểm tra file đã đồng bộ với schema, không ghi đè",
    )
    args = parser.parse_args(argv)

    source = build_source()

    if args.check:
        if not args.out.is_file():
            print(f"Chưa có {args.out}. Chạy: python tools/gen_types.py", file=sys.stderr)
            return 1
        current = args.out.read_text(encoding="utf-8")
        if current != source:
            print(
                f"{args.out} đã lệch khỏi Pydantic schema.\n"
                "Backend đã đổi mà TypeScript chưa sinh lại. Chạy:\n"
                "  python tools/gen_types.py",
                file=sys.stderr,
            )
            return 1
        print(f"{args.out} khớp với schema backend.")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(source, encoding="utf-8")
    lines = source.count("\n")
    exports = source.count("export interface ") + source.count("export type ")
    print(f"Đã ghi {args.out} — {exports} kiểu, {lines} dòng")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
