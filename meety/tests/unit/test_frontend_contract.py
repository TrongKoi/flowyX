"""Test khoá hợp đồng dữ liệu giữa backend và frontend.

Vấn đề mà nhóm test này ngăn chặn
----------------------------------
Frontend đọc JSON do backend sinh ra. Nếu ai đó đổi tên một trường trong
Pydantic mà quên sinh lại TypeScript, **cả hai phía vẫn biên dịch sạch**:
Python không biết TypeScript tồn tại, còn TypeScript chỉ kiểm tra theo cái
interface đã có chứ không kiểm tra dữ liệu thật. Lỗi rơi xuống lúc chạy,
dưới dạng ``undefined`` ở một chỗ chẳng liên quan tới thay đổi ban đầu.

Test ở đây biến sai lệch đó thành test đỏ ngay tại lúc sửa backend.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.gen_types import build_source

ROOT = Path(__file__).resolve().parents[2]
TS_FILE = ROOT / "frontend" / "src" / "types" / "meeting.ts"
MOCK_DIR = ROOT / "frontend" / "src" / "mocks"


class TestTypeScriptSync:
    def test_file_typescript_ton_tai(self) -> None:
        assert TS_FILE.is_file(), "Chạy: python tools/gen_types.py"

    def test_typescript_khop_voi_pydantic(self) -> None:
        """Đây là test quan trọng nhất của cả file.

        Đỏ nghĩa là backend đã đổi mà frontend chưa biết. Cách sửa luôn là
        chạy lại bộ sinh, không bao giờ là sửa tay file .ts.
        """
        assert TS_FILE.read_text(encoding="utf-8") == build_source(), (
            "frontend/src/types/meeting.ts đã lệch khỏi Pydantic schema.\n"
            "Chạy: python tools/gen_types.py"
        )

    def test_khong_khai_trung_dinh_danh(self) -> None:
        """Hai schema dùng chung enum ở schemas/common.py.

        Khai trùng làm TypeScript báo lỗi định danh trùng lặp — mà lỗi đó chỉ
        lộ ra khi chạy tsc, tức là sau khi đã commit.
        """
        source = build_source()
        names: list[str] = []
        for line in source.splitlines():
            for prefix in ("export interface ", "export type "):
                if line.startswith(prefix):
                    names.append(line[len(prefix) :].split()[0].rstrip("{"))
        assert len(names) == len(set(names)), (
            f"Định danh khai trùng: {sorted({n for n in names if names.count(n) > 1})}"
        )

    def test_khong_con_kieu_unknown_o_truong_quan_trong(self) -> None:
        """``unknown`` nghĩa là bộ chuyển đổi gặp cấu trúc nó chưa hiểu."""
        source = build_source()
        offenders = [
            line.strip()
            for line in source.splitlines()
            if ": unknown;" in line and "detail" not in line
        ]
        assert not offenders, f"Trường chưa dịch được kiểu: {offenders}"

    def test_truong_nullable_giu_duoc_y_nghia(self) -> None:
        """``assignee: null`` nghĩa là CHƯA AI NHẬN — không phải thiếu dữ liệu.

        Nếu bộ sinh biến nó thành ``assignee?: string`` thì frontend mất khả
        năng phân biệt "chưa ai nhận" với "backend quên gửi".
        """
        source = build_source()
        assert "assignee: string | null;" in source
        assert "due_date: string | null;" in source
        assert "assignee?:" not in source


class TestMockData:
    """Dữ liệu mẫu cho frontend phải luôn hợp lệ với schema hiện tại."""

    def test_golden_minutes_ton_tai_va_doc_duoc(self) -> None:
        path = MOCK_DIR / "golden_minutes.json"
        assert path.is_file()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["validation"]["grounding_score"] == 1.0

    def test_golden_minutes_hop_le_voi_schema(self) -> None:
        from schemas.minutes import StructuredMinutes

        payload = json.loads(
            (MOCK_DIR / "golden_minutes.json").read_text(encoding="utf-8")
        )
        StructuredMinutes.model_validate(payload)

    def test_transcript_mau_hop_le_voi_schema(self) -> None:
        from schemas.transcript import Transcript

        payload = json.loads(
            (MOCK_DIR / "sample_transcript.json").read_text(encoding="utf-8")
        )
        Transcript.model_validate(payload)

    def test_moi_bang_chung_tro_ve_segment_co_that(self) -> None:
        """Điều kiện tiên quyết để cơ chế truy vết chạy được.

        Cột giữa hiển thị thẻ ``[s_0012]``; người dùng bấm vào và cột trái
        phải cuộn tới đúng segment đó. Một ID trỏ vào hư không sẽ biến tính
        năng cốt lõi thành nút bấm không phản hồi.
        """
        minutes = json.loads(
            (MOCK_DIR / "golden_minutes.json").read_text(encoding="utf-8")
        )
        transcript = json.loads(
            (MOCK_DIR / "sample_transcript.json").read_text(encoding="utf-8")
        )
        known = {segment["id"] for segment in transcript["segments"]}

        referenced: set[str] = set()
        for group in ("decisions", "action_items", "risks", "metrics", "open_questions"):
            for item in minutes.get(group, []):
                referenced.update(item.get("evidence_segment_ids", []))
        for chapter in minutes.get("chapters", []):
            for point in chapter.get("discussion_points", []):
                referenced.update(point.get("evidence_segment_ids", []))

        assert referenced, "Không có bằng chứng nào — cơ chế truy vết vô nghĩa"
        assert referenced <= known, f"Bằng chứng trỏ vào segment không tồn tại: {referenced - known}"

    def test_moi_muc_deu_co_moc_thoi_gian_de_nhay_audio(self) -> None:
        minutes = json.loads(
            (MOCK_DIR / "golden_minutes.json").read_text(encoding="utf-8")
        )
        for item in minutes["action_items"] + minutes["decisions"]:
            assert item["timestamp_ms"] is None or item["timestamp_ms"] >= 0
