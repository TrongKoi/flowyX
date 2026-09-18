"""Định tuyến lai và đối soát — chạy song song mô hình cục bộ với API.

Bài toán thật
-------------
Câu hỏi "mô hình cục bộ đã đủ tốt để thay API chưa?" không trả lời được bằng
cảm tính, cũng không bằng điểm benchmark chung chung. Nó chỉ trả lời được bằng
cách chạy cả hai trên **chính dữ liệu cuộc họp của tổ chức này** rồi đo độ
lệch ở những thứ thực sự quan trọng.

Ba chế độ
---------
``primary``   — chỉ chạy provider chính. Mặc định, dùng cho vận hành thật.
``shadow``    — chạy chính, đồng thời chạy phụ ở nền để đo. Kết quả trả về
                **luôn là của provider chính**; provider phụ không ảnh hưởng
                gì tới thứ người dùng thấy. Đây là chế độ để thu số liệu mà
                không đánh cược vào mô hình chưa được kiểm chứng.
``consensus`` — chạy cả hai, hợp nhất, và **hạ điểm tin cậy ở những mục hai
                bên bất đồng**. Dùng khi cần độ chắc chắn cao hơn tốc độ.

Đo cái gì
---------
Không đo "giống nhau bao nhiêu phần trăm" — con số đó vô nghĩa vì hai mô hình
diễn đạt khác nhau cho cùng một ý. Đo ba thứ có hậu quả thật:

1. **Quyết định bị bỏ sót** — mô hình phụ không thấy quyết định mà mô hình
   chính thấy. Đây là lỗi nặng nhất: biên bản thiếu quyết định thì vô dụng.
2. **Người nhận việc khác nhau** — hai bên gán việc cho hai người khác nhau.
   Lỗi nguy hiểm nhất của sản phẩm này.
3. **Mục bịa** — mô hình phụ tạo ra mục không có dẫn chứng, hoặc trích câu
   không có trong bản thoại.

Ba con số đó cho biết mô hình cục bộ *hỏng ở đâu*, chứ không chỉ *hỏng bao
nhiêu* — và đó mới là thứ dùng được để quyết định fine-tune tiếp hay chưa.
"""

from __future__ import annotations

import concurrent.futures
import dataclasses
import logging
import re
import time
from typing import Any, Sequence

from ai.agent import AgentResult, MeetingAgent
from providers.base import LLMProvider, ProviderError

logger = logging.getLogger(__name__)

__all__ = ["ConsensusEngine", "ComparisonReport", "compare_results"]


@dataclasses.dataclass(slots=True)
class ComparisonReport:
    """Kết quả đối soát giữa hai provider trên cùng một bản thoại."""

    primary: str
    secondary: str
    decisions_primary: int
    decisions_secondary: int
    decisions_matched: int
    decisions_missed_by_secondary: list[str]
    decisions_only_in_secondary: list[str]
    actions_primary: int
    actions_secondary: int
    actions_matched: int
    assignee_conflicts: list[dict]
    ungrounded_secondary: int
    quote_failures_secondary: int
    confidence_primary: int
    confidence_secondary: int
    latency_primary_ms: int
    latency_secondary_ms: int
    verdict: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class ConsensusEngine:
    """Chạy một hoặc hai agent theo chế độ đã chọn."""

    MODES = ("primary", "shadow", "consensus")

    def __init__(
        self,
        primary: LLMProvider,
        secondary: LLMProvider | None = None,
        *,
        mode: str = "primary",
        secondary_timeout: float = 600.0,
    ) -> None:
        if mode not in self.MODES:
            raise ValueError(f"Chế độ phải thuộc {self.MODES}, nhận được {mode!r}")
        if mode != "primary" and secondary is None:
            raise ValueError(f"Chế độ {mode!r} cần provider thứ hai")
        self.primary = primary
        self.secondary = secondary
        self.mode = mode
        self.secondary_timeout = secondary_timeout

    # -- Đường chạy chính -------------------------------------------------- #

    def run(self, transcript: dict[str, Any]) -> dict[str, Any]:
        if self.mode == "primary":
            result, ms = _timed(lambda: MeetingAgent(self.primary).run(transcript))
            return {"mode": "primary", "result": result.to_dict(),
                    "latency_ms": ms, "comparison": None}

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            f_primary = pool.submit(_timed, lambda: MeetingAgent(self.primary).run(transcript))
            f_secondary = pool.submit(_timed, lambda: MeetingAgent(self.secondary).run(transcript))

            primary_result, ms_primary = f_primary.result()
            try:
                secondary_result, ms_secondary = f_secondary.result(
                    timeout=self.secondary_timeout)
            except (concurrent.futures.TimeoutError, ProviderError, Exception) as exc:  # noqa: BLE001
                # Provider phụ hỏng KHÔNG được làm hỏng kết quả người dùng nhận.
                # Đó là toàn bộ lý do chế độ shadow tồn tại.
                logger.warning("Provider phụ %s thất bại: %s", getattr(self.secondary, "key", "?"), exc)
                return {"mode": self.mode, "result": primary_result.to_dict(),
                        "latency_ms": ms_primary, "comparison": None,
                        "secondary_error": str(exc)}

        report = compare_results(primary_result, secondary_result, ms_primary, ms_secondary)

        if self.mode == "shadow":
            # Kết quả trả về nguyên vẹn của provider chính. Provider phụ chỉ để đo.
            return {"mode": "shadow", "result": primary_result.to_dict(),
                    "latency_ms": ms_primary, "comparison": report.to_dict(),
                    "secondary_result": secondary_result.to_dict()}

        merged = self._merge(primary_result, secondary_result, report)
        return {"mode": "consensus", "result": merged,
                "latency_ms": max(ms_primary, ms_secondary),
                "comparison": report.to_dict()}

    # -- Hợp nhất ---------------------------------------------------------- #

    @staticmethod
    def _merge(primary: AgentResult, secondary: AgentResult,
               report: ComparisonReport) -> dict[str, Any]:
        """Hợp nhất hai kết quả, đánh dấu chỗ bất đồng.

        Nguyên tắc: **provider chính là nguồn chân lý về NỘI DUNG**; provider
        phụ chỉ được phép làm một việc — bật cờ nghi ngờ. Cho phép provider phụ
        ghi đè nội dung nghĩa là để mô hình yếu hơn sửa mô hình mạnh hơn.

        Mục hai bên đồng ý → ``agreement: "both"``, tin cậy giữ nguyên.
        Mục chỉ một bên thấy → ``agreement: "primary_only"``, hạ tin cậy.
        Người nhận việc lệch → ``agreement: "conflict"``, hạ mạnh và cảnh báo.
        """
        merged = primary.to_dict()
        sec_decisions = [_norm(d.get("statement", "")) for d in secondary.decisions]
        sec_actions = {_norm(a.get("task", "")): a for a in secondary.actions}

        for d in merged["decisions"]:
            d["agreement"] = ("both" if _best_match(_norm(d.get("statement", "")), sec_decisions)
                              else "primary_only")

        conflicts = {c["task"] for c in report.assignee_conflicts}
        for a in merged["actions"]:
            key = _norm(a.get("task", ""))
            hit = _best_match(key, list(sec_actions))
            if not hit:
                a["agreement"] = "primary_only"
                continue
            other = sec_actions[hit]
            if a.get("task") in conflicts:
                a["agreement"] = "conflict"
                a["secondary_assignee"] = other.get("assignee")
            else:
                a["agreement"] = "both"

        # Hạ điểm theo mức bất đồng — người đọc phải thấy được sự thiếu chắc chắn.
        penalty = (
            sum(1 for d in merged["decisions"] if d["agreement"] == "primary_only") * 3
            + sum(1 for a in merged["actions"] if a["agreement"] == "primary_only") * 3
            + len(report.assignee_conflicts) * 10
        )
        conf = dict(merged["confidence"])
        conf["consensus_penalty"] = penalty
        conf["score"] = max(0, conf["score"] - penalty)
        conf["tone"] = ("jade" if conf["score"] >= 85
                        else "amber" if conf["score"] >= 70 else "coral")
        merged["confidence"] = conf
        merged["consensus"] = {
            "secondary_provider": secondary.provider,
            "verdict": report.verdict,
            "assignee_conflicts": report.assignee_conflicts,
        }
        return merged


# ===========================================================================
#  Đối soát
# ===========================================================================

def compare_results(primary: AgentResult, secondary: AgentResult,
                    ms_primary: int = 0, ms_secondary: int = 0) -> ComparisonReport:
    p_dec = [d.get("statement", "") for d in primary.decisions]
    s_dec = [d.get("statement", "") for d in secondary.decisions]
    p_norm = [_norm(x) for x in p_dec]
    s_norm = [_norm(x) for x in s_dec]

    matched_dec = sum(1 for x in p_norm if _best_match(x, s_norm))
    missed = [orig for orig, n in zip(p_dec, p_norm) if not _best_match(n, s_norm)]
    extra = [orig for orig, n in zip(s_dec, s_norm) if not _best_match(n, p_norm)]

    s_by_task = {_norm(a.get("task", "")): a for a in secondary.actions}
    matched_act = 0
    conflicts: list[dict] = []
    for a in primary.actions:
        key = _norm(a.get("task", ""))
        hit = _best_match(key, list(s_by_task))
        if not hit:
            continue
        matched_act += 1
        other = s_by_task[hit]
        pa, sa = a.get("assignee"), other.get("assignee")
        # Chỉ tính là xung đột khi CẢ HAI đều gán tên và tên khác nhau.
        # Một bên để trống là "thận trọng", không phải "sai".
        if pa and sa and _norm(pa) != _norm(sa):
            conflicts.append({"task": a.get("task"), "primary": pa, "secondary": sa})

    ungrounded = sum(secondary.dropped.values())
    quote_fail = sum(
        1 for x in list(secondary.decisions) + list(secondary.actions)
        if x.get("quote_verified") is False)

    recall = matched_dec / len(p_dec) if p_dec else 1.0
    if conflicts:
        verdict = ("Chưa thay được API: có bất đồng về người nhận việc — "
                   "đây là loại lỗi nguy hiểm nhất, phải bằng 0 mới tính tiếp.")
    elif recall < 0.7:
        verdict = (f"Chưa thay được API: mô hình phụ bỏ sót {len(missed)}/{len(p_dec)} "
                   f"quyết định.")
    elif quote_fail or ungrounded:
        verdict = (f"Gần đạt: không bỏ sót quyết định, nhưng còn {quote_fail} câu trích "
                   f"không khớp bản thoại và {ungrounded} mục thiếu dẫn chứng.")
    else:
        verdict = ("Đạt trên mẫu này: không bỏ sót quyết định, không lệch người nhận việc, "
                   "mọi mục đều có dẫn chứng. Cần lặp lại trên ít nhất 20 cuộc họp "
                   "trước khi kết luận.")

    return ComparisonReport(
        primary=primary.provider, secondary=secondary.provider,
        decisions_primary=len(p_dec), decisions_secondary=len(s_dec),
        decisions_matched=matched_dec,
        decisions_missed_by_secondary=missed, decisions_only_in_secondary=extra,
        actions_primary=len(primary.actions), actions_secondary=len(secondary.actions),
        actions_matched=matched_act, assignee_conflicts=conflicts,
        ungrounded_secondary=ungrounded, quote_failures_secondary=quote_fail,
        confidence_primary=primary.confidence.get("score", 0),
        confidence_secondary=secondary.confidence.get("score", 0),
        latency_primary_ms=ms_primary, latency_secondary_ms=ms_secondary,
        verdict=verdict,
    )


# -- Tiện ích ---------------------------------------------------------------- #

def _timed(fn):
    t0 = time.perf_counter()
    out = fn()
    return out, int((time.perf_counter() - t0) * 1000)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", str(text).lower())).strip()


def _best_match(needle: str, haystack: Sequence[str], threshold: float = 0.55) -> str | None:
    """Khớp mờ bằng Jaccard trên tập từ.

    Không dùng so khớp chính xác: hai mô hình diễn đạt khác nhau cho cùng một
    quyết định là chuyện bình thường, và coi đó là "bỏ sót" sẽ cho ra số liệu
    bi quan sai lệch. Ngưỡng 0.55 chọn theo kinh nghiệm — đủ chặt để không gộp
    nhầm hai quyết định khác nhau, đủ lỏng để chấp nhận cách diễn đạt khác.
    """
    if not needle:
        return None
    a = set(needle.split())
    best, best_score = None, 0.0
    for cand in haystack:
        b = set(cand.split())
        if not b:
            continue
        score = len(a & b) / len(a | b)
        if score > best_score:
            best, best_score = cand, score
    return best if best_score >= threshold else None
