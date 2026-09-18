"""Bộ ghi nhận học hỏi — vòng lặp 4 bước của Agent tự học.

Module này là **tên gọi chính thức** theo kiến trúc hạng mục 13. Nó bọc quanh
``ai/collector.py`` (đã có, lo phần ẩn danh và ghi ``.jsonl``) và thêm phần
còn thiếu: **Bước 2 — ghi nhận sự khác biệt giữa bản AI tạo và bản người sửa**.

Vì sao Diff quan trọng hơn chính bản cuối
-----------------------------------------
Bản biên bản đã duyệt cho biết *câu trả lời đúng là gì*. Nhưng Diff cho biết
*mô hình sai ở đâu* — và đó mới là thứ dạy được.

Ví dụ: nếu 40 lần người dùng đều phải sửa hạn chót từ "thứ 6" thành ngày cụ
thể, thì vấn đề không nằm ở dữ liệu huấn luyện chung chung mà ở đúng một kỹ
năng: quy đổi cụm chỉ thời gian tương đối. Biết điều đó thì sửa được bằng
prompt trong một buổi chiều, không cần fine-tune gì cả.

Vòng lặp bốn bước
-----------------
1. **Trích xuất đa nguồn** — pipeline/agent dùng API mạnh dựng bản nháp.
2. **Người trong vòng lặp** — Owner sửa task, sửa hạn, xoá việc thừa, phê
   duyệt. Mỗi thao tác đó gọi ``record_edit()`` ở đây.
3. **Sinh dữ liệu chưng cất** — lúc phê duyệt, ``DataCollector.collect()``
   đóng gói cặp (bản thoại → biên bản chuẩn) đã ẩn danh.
4. **Tiến hoá mô hình** — đủ mẫu thì fine-tune mô hình cục bộ; dùng
   ``ai/meeting_evaluator.py`` chấm điểm trước khi tin.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai.collector import DataCollector, PIIMap, anonymise_text

logger = logging.getLogger(__name__)

__all__ = ["LearningCollector", "EDIT_KINDS"]

DEFAULT_EDIT_LOG = Path("data/training/human_edits.jsonl")

# Mỗi loại sửa ứng với một kỹ năng cụ thể của mô hình. Phân loại để về sau
# thống kê được "mô hình yếu nhất ở khâu nào", thay vì chỉ biết "hay bị sửa".
EDIT_KINDS = {
    "assignee_changed": "Đổi người nhận việc — mô hình gán sai hoặc bỏ trống",
    "assignee_filled": "Điền người vào việc mô hình để trống",
    "due_changed": "Sửa hạn chót — mô hình quy đổi sai cụm chỉ thời gian",
    "task_deleted": "Xoá việc — mô hình bắt nhầm, đây không phải cam kết",
    "task_added": "Thêm việc — mô hình bỏ sót",
    "priority_changed": "Đổi mức ưu tiên — mô hình không đoán được, đúng như thiết kế",
    "status_changed": "Đổi trạng thái — vận hành bình thường, không phải lỗi mô hình",
    "speaker_renamed": "Sửa tên người nói — nhận dạng sai",
    "approved": "Phê duyệt biên bản",
}

# Những loại KHÔNG phải tín hiệu lỗi mô hình. Đếm chúng vào thống kê chất
# lượng sẽ làm mô hình trông tệ hơn thực tế.
NOT_MODEL_ERRORS = {"status_changed", "priority_changed", "approved"}


class LearningCollector:
    """Ghi nhật ký sửa của con người, và đóng gói dữ liệu chưng cất khi duyệt."""

    def __init__(self, *, edit_log: Path | str | None = None,
                 dataset: DataCollector | None = None) -> None:
        self.edit_log = Path(edit_log or DEFAULT_EDIT_LOG)
        self.dataset = dataset or DataCollector()
        self._lock = threading.Lock()

    # -- Bước 2: ghi nhận sửa ------------------------------------------- #

    def record_edit(self, *, meeting_id: str, kind: str, before: Any = None,
                    after: Any = None, task_id: str | None = None,
                    context: str | None = None) -> dict[str, Any]:
        """Ghi một thao tác sửa. Không bao giờ ném lỗi ra ngoài.

        Ghi nhật ký là việc phụ; nó không được phép làm hỏng thao tác mà người
        dùng đang thực hiện. Cùng nguyên tắc đã áp cho thông báo trong
        ``server/jobs.py``.
        """
        if not self.dataset.enabled:
            return {"logged": False, "reason": "chưa bật MEETY_COLLECT_TRAINING"}
        if kind not in EDIT_KINDS:
            return {"logged": False, "reason": f"loại sửa lạ: {kind}"}
        try:
            pii = PIIMap(salt=meeting_id)
            record = {
                # Băm id: nhật ký này đi kèm tập huấn luyện, không được truy
                # ngược về đúng cuộc họp nào của tổ chức nào.
                "meeting_ref": _ref(meeting_id),
                "task_ref": _ref(task_id) if task_id else None,
                "kind": kind,
                "is_model_error": kind not in NOT_MODEL_ERRORS,
                "before": anonymise_text(str(before), pii) if before is not None else None,
                "after": anonymise_text(str(after), pii) if after is not None else None,
                "context": anonymise_text(context, pii) if context else None,
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            self.edit_log.parent.mkdir(parents=True, exist_ok=True)
            with self._lock, self.edit_log.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            return {"logged": True, "kind": kind}
        except Exception as exc:                      # noqa: BLE001
            logger.warning("Không ghi được nhật ký sửa: %s", exc)
            return {"logged": False, "reason": str(exc)}

    # -- Bước 3: đóng gói khi phê duyệt ---------------------------------- #

    def on_approved(self, *, meeting_id: str, transcript: dict, minutes: dict,
                    approved_by: str | None = None) -> dict[str, Any]:
        self.record_edit(meeting_id=meeting_id, kind="approved")
        return self.dataset.collect(meeting_id=meeting_id, transcript=transcript,
                                    minutes=minutes, approved_by=approved_by,
                                    source="human_approved")

    # -- Đọc lại: mô hình yếu nhất ở khâu nào ---------------------------- #

    def weakness_report(self) -> dict[str, Any]:
        """Thống kê loại sửa nào hay xảy ra nhất.

        Đây là thứ dùng được ngay, trước cả khi đủ mẫu để fine-tune: nó chỉ
        đúng kỹ năng cần sửa bằng prompt.
        """
        counts: dict[str, int] = {}
        total = errors = 0
        if self.edit_log.exists():
            try:
                with self.edit_log.open(encoding="utf-8") as fh:
                    for line in fh:
                        if not line.strip():
                            continue
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        total += 1
                        kind = rec.get("kind", "?")
                        counts[kind] = counts.get(kind, 0) + 1
                        if rec.get("is_model_error"):
                            errors += 1
            except OSError as exc:
                return {"error": str(exc)}

        ranked = sorted(((k, n) for k, n in counts.items() if k not in NOT_MODEL_ERRORS),
                        key=lambda kv: kv[1], reverse=True)
        top = ranked[0] if ranked else None
        return {
            "enabled": self.dataset.enabled,
            "edit_log": str(self.edit_log),
            "total_edits": total,
            "model_errors": errors,
            "by_kind": [{"kind": k, "n": n, "meaning": EDIT_KINDS.get(k, "")}
                        for k, n in sorted(counts.items(), key=lambda kv: -kv[1])],
            "weakest_skill": ({"kind": top[0], "n": top[1],
                               "meaning": EDIT_KINDS.get(top[0], "")} if top else None),
            "advice": (
                f"Người dùng sửa nhiều nhất ở khâu: {EDIT_KINDS.get(top[0], top[0])}. "
                f"Thử chỉnh prompt cho khâu này trước khi nghĩ tới fine-tune — "
                f"rẻ hơn nhiều và thường đủ."
                if top else
                "Chưa đủ dữ liệu sửa để kết luận mô hình yếu ở đâu."),
            "dataset": self.dataset.stats(),
        }


def _ref(value: str) -> str:
    import hashlib
    return hashlib.sha256(str(value).encode()).hexdigest()[:12]
