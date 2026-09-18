"""Thu thập dữ liệu chưng cất — cặp ``transcript thật → biên bản người đã duyệt``.

Ý tưởng
-------
Mỗi lần chủ cuộc họp sửa rồi phê duyệt một biên bản, họ vừa tạo ra một mẫu
huấn luyện chất lượng cao mà không hề biết: đầu vào là bản thoại thật, đầu ra
là biên bản **đã được người có trách nhiệm xác nhận là đúng**. Đó là loại dữ
liệu đắt nhất trong huấn luyện mô hình, và ở đây nó sinh ra như một sản phẩm
phụ của việc dùng sản phẩm.

Gom đủ vài trăm cặp như vậy là có thể fine-tune một mô hình nhỏ (LoRA trên
Llama-3-8B hoặc Qwen-7B) chạy tại chỗ — không còn phụ thuộc API, và quan
trọng hơn: mô hình đó học đúng văn phong biên bản của chính tổ chức này.

Ba điều bắt buộc, không phải tuỳ chọn
-------------------------------------
1. **Chỉ lấy biên bản đã PHÊ DUYỆT.** Biên bản chờ duyệt là ý kiến của mô
   hình, chưa ai xác nhận. Huấn luyện trên đó là dạy mô hình lặp lại lỗi của
   chính nó — sai lệch tự khuếch đại qua từng vòng.
2. **Ẩn danh trước khi ghi xuống đĩa.** Không phải sau, không phải lúc dùng.
   Tệp ``.jsonl`` sẽ được copy đi copy lại, đưa lên máy huấn luyện, có khi lên
   cả dịch vụ đám mây. Mọi bản sao đều phải đã sạch.
3. **Người dùng phải bật.** Mặc định TẮT. Bật bằng ``MEETY_COLLECT_TRAINING=1``.
   Thu thập dữ liệu cuộc họp mà không hỏi là chuyện không được làm, kể cả khi
   đã ẩn danh.

Ẩn danh tới đâu là đủ
---------------------
Module này che email, số điện thoại, số tài khoản, URL có token, và tên riêng
đã biết (lấy từ danh sách tham dự). Nó **không** phải là bộ ẩn danh hoàn hảo —
không có bộ nào hoàn hảo. Tên người lạ nhắc thoáng qua trong hội thoại vẫn có
thể lọt. Vì vậy tệp sinh ra phải được coi là **dữ liệu nội bộ**, không phải dữ
liệu công khai. Nói khác đi là nói sai.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)

__all__ = ["DataCollector", "anonymise_text", "PIIMap"]

DEFAULT_PATH = Path("data/training/finetune_dataset.jsonl")

INSTRUCTION = (
    "Bạn là trợ lý ghi biên bản cuộc họp. Từ bản thoại dưới đây, hãy trích xuất "
    "quyết định, công việc kèm người nhận, và tóm tắt điều hành. Chỉ dùng thông "
    "tin có trong bản thoại; chỗ nào không rõ thì để trống."
)

# -- Mẫu nhận diện thông tin cá nhân ---------------------------------------- #

RE_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
# Số điện thoại Việt Nam: 0xx hoặc +84, cho phép dấu cách/chấm/gạch xen giữa.
RE_PHONE = re.compile(r"(?<!\d)(?:\+?84|0)(?:[\s.-]?\d){8,10}(?!\d)")
RE_URL = re.compile(r"https?://\S+")
# Số tài khoản / thẻ: dãy 9-19 chữ số, có thể nhóm bằng dấu cách hoặc gạch.
RE_ACCOUNT = re.compile(r"(?<!\d)(?:\d[\s-]?){9,19}(?!\d)")
RE_ID_CARD = re.compile(r"\b\d{9}\b|\b\d{12}\b")


class PIIMap:
    """Bảng thay thế nhất quán trong phạm vi MỘT cuộc họp.

    "Nguyễn Văn An" luôn thành ``NGƯỜI_1`` trong cùng một mẫu, để mô hình vẫn
    học được rằng *cùng một người* nói ở nhiều chỗ khác nhau. Nếu mỗi lần thay
    một mã khác nhau thì quan hệ giữa các lượt nói biến mất, và mẫu huấn luyện
    mất phần lớn giá trị.

    Bảng KHÔNG được dùng chung giữa các cuộc họp: ``NGƯỜI_1`` ở cuộc họp A và
    ``NGƯỜI_1`` ở cuộc họp B là hai người khác nhau, và đó là điều ta muốn —
    không ai ghép lại được danh tính xuyên các mẫu.
    """

    def __init__(self, salt: str = "") -> None:
        self._map: dict[str, str] = {}
        self._counters: dict[str, int] = {}
        self.salt = salt

    def token(self, kind: str, original: str) -> str:
        key = f"{kind}:{original.strip().lower()}"
        if key not in self._map:
            self._counters[kind] = self._counters.get(kind, 0) + 1
            self._map[key] = f"[{kind}_{self._counters[kind]}]"
        return self._map[key]

    @property
    def size(self) -> int:
        return len(self._map)

    def summary(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for key in self._map:
            kind = key.split(":", 1)[0]
            out[kind] = out.get(kind, 0) + 1
        return out


def anonymise_text(text: str, pii: PIIMap, names: Iterable[str] = ()) -> str:
    """Che thông tin cá nhân trong một đoạn văn bản.

    Thứ tự quan trọng: URL trước, vì URL chứa dấu chấm và chữ số dễ bị các mẫu
    sau bắt nhầm. Số tài khoản đặt sau số điện thoại vì mẫu tài khoản rộng hơn
    và sẽ nuốt luôn số điện thoại nếu chạy trước.
    """
    if not text:
        return text
    out = str(text)

    out = RE_URL.sub(lambda m: pii.token("LIÊN_KẾT", m.group()), out)
    out = RE_EMAIL.sub(lambda m: pii.token("EMAIL", m.group()), out)
    out = RE_PHONE.sub(lambda m: pii.token("ĐIỆN_THOẠI", m.group()), out)
    out = RE_ID_CARD.sub(lambda m: pii.token("CCCD", m.group()), out)
    out = RE_ACCOUNT.sub(lambda m: pii.token("SỐ_TÀI_KHOẢN", m.group()), out)

    # Tên riêng: thay theo danh sách tham dự, dài trước ngắn sau để "Nguyễn Văn
    # An" không bị cắt thành "[NGƯỜI_1] Văn An" bởi lượt khớp "Nguyễn".
    for name in sorted({n for n in names if n and len(n.strip()) >= 2},
                       key=len, reverse=True):
        token = pii.token("NGƯỜI", name)
        out = re.sub(rf"\b{re.escape(name.strip())}\b", token, out)
        parts = name.strip().split()
        if len(parts) > 1:
            # Tiếng Việt gọi nhau bằng tên riêng cuối; phải che cả dạng đó.
            out = re.sub(rf"\b{re.escape(parts[-1])}\b", token, out)
    return out


class DataCollector:
    """Ghi cặp huấn luyện xuống ``finetune_dataset.jsonl``.

    Định dạng mỗi dòng theo chuẩn Instruction–Input–Output mà hầu hết công cụ
    fine-tune (Axolotl, LLaMA-Factory, Unsloth, HuggingFace TRL) đọc được trực
    tiếp, không cần chuyển đổi.
    """

    def __init__(self, path: Path | str | None = None, *, enabled: bool | None = None) -> None:
        self.path = Path(path or os.environ.get("MEETY_TRAINING_PATH", DEFAULT_PATH))
        if enabled is None:
            enabled = os.environ.get("MEETY_COLLECT_TRAINING", "").strip().lower() in {
                "1", "true", "yes", "on"}
        self.enabled = bool(enabled)
        self._lock = threading.Lock()

    # -- Ghi -------------------------------------------------------------- #

    def collect(
        self,
        *,
        meeting_id: str,
        transcript: dict[str, Any],
        minutes: dict[str, Any],
        approved_by: str | None = None,
        source: str = "human_approved",
    ) -> dict[str, Any]:
        """Ghi một cặp huấn luyện. Trả về báo cáo cho tầng gọi.

        Không ném lỗi ra ngoài: thu thập dữ liệu là việc phụ, không được phép
        làm hỏng luồng phê duyệt của người dùng.
        """
        if not self.enabled:
            return {"written": False, "reason": "chưa bật MEETY_COLLECT_TRAINING"}
        try:
            record = self.build_record(
                meeting_id=meeting_id, transcript=transcript, minutes=minutes,
                approved_by=approved_by, source=source)
        except Exception as exc:                       # noqa: BLE001
            logger.warning("Không dựng được mẫu huấn luyện cho %s: %s", meeting_id, exc)
            return {"written": False, "reason": str(exc)}

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(record, ensure_ascii=False)
            with self._lock, self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            logger.warning("Không ghi được tệp huấn luyện: %s", exc)
            return {"written": False, "reason": str(exc)}

        return {
            "written": True,
            "path": str(self.path),
            "sample_id": record["meta"]["sample_id"],
            "pii_masked": record["meta"]["pii_masked"],
            "total_samples": self.count(),
        }

    def build_record(
        self,
        *,
        meeting_id: str,
        transcript: dict[str, Any],
        minutes: dict[str, Any],
        approved_by: str | None = None,
        source: str = "human_approved",
    ) -> dict[str, Any]:
        """Dựng một mẫu đã ẩn danh. Tách riêng để kiểm thử được mà không cần ghi đĩa."""
        names = [
            s.get("display_name") for s in (transcript.get("speakers") or [])
            if s.get("display_name") and not str(s["display_name"]).startswith("SPEAKER_")
        ]
        for a in (minutes.get("meta", {}).get("attendees") or []):
            if a.get("display_name"):
                names.append(a["display_name"])

        pii = PIIMap(salt=meeting_id)
        # Ẩn danh CẢ NHÃN người nói, không chỉ nội dung câu. Bản đầu chỉ che
        # phần text và để nguyên tên ở đầu dòng — tức là tên thật của toàn bộ
        # người dự họp nằm nguyên trong tệp huấn luyện, ở vị trí dễ trích xuất
        # nhất. Bộ kiểm thử bắt được đúng chỗ này.
        input_text = "\n".join(
            f"[{s['id']}] {anonymise_text(_label(s, transcript), pii, names)}: "
            f"{anonymise_text(s.get('text', ''), pii, names)}"
            for s in (transcript.get("segments") or [])
        )
        output = _clean_minutes(minutes, pii, names)

        # Băm nội dung để phát hiện trùng lặp khi gộp nhiều tệp từ nhiều máy.
        digest = hashlib.sha256(
            (input_text + json.dumps(output, ensure_ascii=False, sort_keys=True)
             ).encode("utf-8")).hexdigest()[:16]

        return {
            "instruction": INSTRUCTION,
            "input": input_text,
            "output": json.dumps(output, ensure_ascii=False, indent=None),
            "meta": {
                "sample_id": digest,
                # KHÔNG lưu meeting_id thật: nó truy ngược được về đúng cuộc họp
                # và đúng tổ chức. Băm một chiều là đủ để loại trùng.
                "meeting_ref": hashlib.sha256(meeting_id.encode()).hexdigest()[:12],
                "source": source,
                "approved": source == "human_approved",
                "approver_ref": (hashlib.sha256(approved_by.encode()).hexdigest()[:12]
                                 if approved_by else None),
                "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "n_segments": len(transcript.get("segments") or []),
                "n_decisions": len(minutes.get("decisions") or []),
                "n_actions": len(minutes.get("action_items") or []),
                "pii_masked": pii.summary(),
                "schema_version": 1,
            },
        }

    # -- Đọc -------------------------------------------------------------- #

    def count(self) -> int:
        if not self.path.exists():
            return 0
        try:
            with self.path.open(encoding="utf-8") as fh:
                return sum(1 for line in fh if line.strip())
        except OSError:
            return 0

    def stats(self) -> dict[str, Any]:
        """Thống kê tập dữ liệu, dùng cho endpoint theo dõi tiến độ chưng cất."""
        if not self.path.exists():
            return {"enabled": self.enabled, "path": str(self.path), "samples": 0,
                    "ready_for_finetune": False}
        n = approved = seg = 0
        seen: set[str] = set()
        try:
            with self.path.open(encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    n += 1
                    meta = rec.get("meta", {})
                    approved += bool(meta.get("approved"))
                    seg += meta.get("n_segments", 0)
                    seen.add(meta.get("sample_id", ""))
        except OSError as exc:
            return {"enabled": self.enabled, "path": str(self.path), "error": str(exc)}
        return {
            "enabled": self.enabled,
            "path": str(self.path),
            "samples": n,
            "unique": len(seen),
            "approved_samples": approved,
            "avg_segments": round(seg / n, 1) if n else 0,
            # Ngưỡng kinh nghiệm cho LoRA trên mô hình 7-8B ở một tác vụ hẹp.
            # Dưới mức này thì fine-tune thường tệ hơn prompt tốt.
            "ready_for_finetune": approved >= 200,
            "note": ("Đủ mẫu để thử LoRA" if approved >= 200
                     else f"Cần thêm {200 - approved} biên bản đã phê duyệt nữa"),
        }

    def export_train_val(self, out_dir: Path | str, val_ratio: float = 0.1) -> dict[str, Any]:
        """Tách tập huấn luyện / kiểm định, loại trùng theo ``sample_id``.

        Tách theo thứ tự thời gian chứ không xáo ngẫu nhiên: mẫu mới nhất làm
        tập kiểm định. Xáo ngẫu nhiên với dữ liệu có tính thời gian sẽ cho điểm
        đánh giá đẹp hơn thực tế, vì mô hình đã thấy các cuộc họp cùng chuỗi.
        """
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        rows, seen = [], set()
        if self.path.exists():
            with self.path.open(encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    sid = rec.get("meta", {}).get("sample_id")
                    if sid and sid in seen:
                        continue
                    seen.add(sid)
                    rows.append(rec)
        cut = max(1, int(len(rows) * (1 - val_ratio))) if rows else 0
        train, val = rows[:cut], rows[cut:]
        for name, part in (("train.jsonl", train), ("val.jsonl", val)):
            with (out_dir / name).open("w", encoding="utf-8") as fh:
                for r in part:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        return {"train": len(train), "val": len(val), "dir": str(out_dir),
                "deduped": len(seen)}


# -- Nội bộ ------------------------------------------------------------------ #

def _label(segment: dict, transcript: dict) -> str:
    for s in transcript.get("speakers") or []:
        if s.get("label") == segment.get("speaker_label"):
            return s.get("display_name") or s.get("label") or "?"
    return segment.get("speaker_label", "?")


def _clean_minutes(minutes: dict[str, Any], pii: PIIMap, names: list[str]) -> dict[str, Any]:
    """Rút phần biên bản dùng làm nhãn huấn luyện, đã ẩn danh.

    Chỉ giữ những trường mô hình cần học sinh ra. Bỏ hết siêu dữ liệu vận hành
    (id, timestamp, tên nhà cung cấp, chi phí) — chúng không phải thứ mô hình
    phải đoán, và giữ lại chỉ làm nhiễu tín hiệu huấn luyện.
    """
    def clean(x):
        return anonymise_text(x, pii, names) if isinstance(x, str) else x

    return {
        "executive_summary": {
            "tldr": [clean(t) for t in (minutes.get("executive_summary", {}).get("tldr") or [])],
        },
        "decisions": [
            {
                "statement": clean(d.get("statement")),
                "decided_by": clean(d.get("decided_by")),
                "quote": clean(d.get("quote")),
                "evidence_segment_ids": d.get("evidence_segment_ids") or [],
                "supersedes": d.get("supersedes"),
            }
            for d in (minutes.get("decisions") or [])
        ],
        "action_items": [
            {
                "task": clean(a.get("task")),
                "assignee": clean(a.get("assignee")),
                "quote": clean(a.get("quote")),
                "due_date": a.get("due_date"),
                "commitment_strength": a.get("commitment_strength"),
                "evidence_segment_ids": a.get("evidence_segment_ids") or [],
            }
            for a in (minutes.get("action_items") or [])
        ],
    }
