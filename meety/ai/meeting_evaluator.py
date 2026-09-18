"""Meeting-Bench — chấm điểm biên bản do AI sinh so với bản người đã duyệt.

Bộ này trả lời một câu hỏi mà không ai trả lời được bằng cảm tính: *"mô hình
nào tóm tắt cuộc họp của TỔ CHỨC NÀY chuẩn hơn?"*

Về nguồn cảm hứng — nói cho đúng
--------------------------------
Đề bài mô tả ``deepseek-ai/deepseek-harness`` là "bộ khung đánh giá benchmark
tương tự lm-evaluation-harness". **Điều đó không đúng.** Repo đó là một
*agent harness*: bộ khung chạy tác tử theo kiến trúc plugin, dựng trên kernel
Cordis, viết bằng TypeScript/Node, có Web UI riêng. "Harness" ở đó nghĩa là
"bộ khung vận hành tác tử", không phải "bộ khung chấm điểm".

Module này vì thế lấy cảm hứng từ ``EleutherAI/lm-evaluation-harness`` — nơi
thật sự đặt ra khuôn mẫu cho việc chấm điểm mô hình:

* mỗi **task** là một bộ (dữ liệu vào, đáp án chuẩn, hàm chấm);
* các **metric** tách rời khỏi mô hình, nên đổi mô hình không phải sửa thước đo;
* kết quả **tái lập được**: cùng đầu vào cho cùng điểm số, không phụ thuộc
  ngày chạy hay tâm trạng người chấm.

Điều bộ này KHÔNG làm
---------------------
Không dùng LLM để chấm LLM. Cách đó ("LLM-as-judge") phổ biến vì dễ, nhưng nó
thiên vị mô hình cùng họ với giám khảo, và điểm số đổi giữa hai lần chạy cùng
một dữ liệu. Mọi thước đo ở đây là hàm thuần Python — chạy lại một nghìn lần
cho một nghìn kết quả giống nhau, và không tốn một đồng quota nào.

Bốn thước đo, mỗi cái đo một loại hỏng khác nhau
-----------------------------------------------
================  ==========================================================
Quyết định        Bỏ sót quyết định → biên bản vô dụng
Công việc         Bỏ sót việc → không ai làm
Người nhận việc   Gán sai người → loại lỗi nguy hiểm nhất
Hạn chót          Sai ngày → trễ deadline mà không ai biết
================  ==========================================================

Điểm tổng có trọng số lệch hẳn về *người nhận việc*: một biên bản đủ mọi
quyết định nhưng gán nhầm người còn tệ hơn biên bản thiếu một mục.
"""

from __future__ import annotations

import dataclasses
import json
import re
import statistics
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Sequence

__all__ = [
    "evaluate_minutes",
    "evaluate_dataset",
    "MeetingScore",
    "MetricResult",
    "compare_models",
]

# Trọng số điểm tổng. Cộng lại bằng 1.0.
WEIGHTS = {
    "decisions": 0.30,
    "actions": 0.25,
    "assignees": 0.30,     # cao nhất, có lý do — xem phần đầu file
    "due_dates": 0.15,
}

# Ngưỡng khớp mờ giữa hai câu. Hai mô hình diễn đạt khác nhau cho cùng một
# quyết định là chuyện bình thường; so khớp chính xác sẽ cho điểm bi quan sai.
MATCH_THRESHOLD = 0.55


@dataclasses.dataclass(slots=True)
class MetricResult:
    """Một thước đo, kèm đủ số liệu để tự tính lại precision/recall."""

    name: str
    matched: int
    expected: int
    produced: int
    missed: list[str]
    spurious: list[str]

    @property
    def recall(self) -> float:
        """Bắt được bao nhiêu phần trong những gì đáng lẽ phải bắt."""
        return self.matched / self.expected if self.expected else 1.0

    @property
    def precision(self) -> float:
        """Trong những gì đã bắt, bao nhiêu phần là thật."""
        return self.matched / self.produced if self.produced else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d.update(recall=round(self.recall, 4), precision=round(self.precision, 4),
                 f1=round(self.f1, 4))
        return d


@dataclasses.dataclass(slots=True)
class MeetingScore:
    """Kết quả chấm một cuộc họp."""

    meeting_id: str
    overall: float
    metrics: dict[str, MetricResult]
    assignee_errors: list[dict]
    due_errors: list[dict]
    hallucinations: list[str]
    notes: list[str]

    applicable: list[str] = dataclasses.field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "meeting_id": self.meeting_id,
            "applicable_metrics": self.applicable,
            "overall": round(self.overall, 4),
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "assignee_errors": self.assignee_errors,
            "due_errors": self.due_errors,
            "hallucinations": self.hallucinations,
            "notes": self.notes,
        }


# ===========================================================================
#  Khớp mờ
# ===========================================================================

def _norm(text: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", str(text or "").lower())).strip()


def _similarity(a: str, b: str) -> float:
    """Jaccard trên tập từ.

    Chọn Jaccard thay vì so khớp chuỗi con hay Levenshtein vì hai lý do: nó
    không phạt việc đảo trật tự từ (tiếng Việt cho phép đảo rất nhiều), và nó
    không thưởng cho câu dài — mô hình viết dài dòng không được điểm cao hơn.
    """
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _match_lists(produced: Sequence[str], expected: Sequence[str],
                 threshold: float = MATCH_THRESHOLD) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """Ghép cặp tham lam theo độ tương đồng giảm dần.

    Ghép tham lam chứ không ghép tối ưu (Hungarian): với vài chục mục thì kết
    quả gần như giống nhau, mà thuật toán tối ưu khiến điểm số khó giải thích
    khi có tranh chấp. Ở đây "vì sao mục này ghép với mục kia" phải nhìn là
    hiểu, vì con người sẽ đọc báo cáo này để quyết định đổi mô hình.
    """
    pairs: list[tuple[float, int, int]] = []
    for i, p in enumerate(produced):
        for j, e in enumerate(expected):
            score = _similarity(_norm(p), _norm(e))
            if score >= threshold:
                pairs.append((score, i, j))
    pairs.sort(reverse=True)

    used_p: set[int] = set()
    used_e: set[int] = set()
    matched: list[tuple[int, int]] = []
    for _score, i, j in pairs:
        if i in used_p or j in used_e:
            continue
        used_p.add(i)
        used_e.add(j)
        matched.append((i, j))

    missed = [j for j in range(len(expected)) if j not in used_e]
    spurious = [i for i in range(len(produced)) if i not in used_p]
    return matched, missed, spurious


# ===========================================================================
#  Thước đo
# ===========================================================================

def _decisions(produced: dict, expected: dict) -> MetricResult:
    p = [d.get("statement", "") for d in (produced.get("decisions") or [])
         if not d.get("superseded_by")]
    e = [d.get("statement", "") for d in (expected.get("decisions") or [])
         if not d.get("superseded_by")]
    matched, missed, spurious = _match_lists(p, e)
    return MetricResult("decisions", len(matched), len(e), len(p),
                        [e[j] for j in missed], [p[i] for i in spurious])


def _actions(produced: dict, expected: dict) -> MetricResult:
    p = [a.get("task", "") for a in (produced.get("action_items") or [])]
    e = [a.get("task", "") for a in (expected.get("action_items") or [])]
    matched, missed, spurious = _match_lists(p, e)
    return MetricResult("actions", len(matched), len(e), len(p),
                        [e[j] for j in missed], [p[i] for i in spurious])


def _assignees(produced: dict, expected: dict) -> tuple[MetricResult, list[dict]]:
    """Chấm người nhận việc, chỉ trên những việc đã ghép được.

    Quan trọng: **để trống khi bản chuẩn cũng để trống là ĐÚNG**, không phải
    thiếu sót. Một mô hình thận trọng để trống chỗ không rõ phải được điểm cao
    hơn mô hình đoán bừa — nếu chấm ngược lại thì ta đang huấn luyện chính
    mình chọn nhầm mô hình.
    """
    pa = produced.get("action_items") or []
    ea = expected.get("action_items") or []
    matched, _missed, _spurious = _match_lists(
        [a.get("task", "") for a in pa], [a.get("task", "") for a in ea])

    correct = 0
    errors: list[dict] = []
    for i, j in matched:
        got, want = _norm(pa[i].get("assignee")), _norm(ea[j].get("assignee"))
        if got == want:
            correct += 1
        elif not got and want:
            errors.append({"task": ea[j].get("task"), "expected": ea[j].get("assignee"),
                           "got": None, "kind": "bỏ trống"})
        elif got and not want:
            errors.append({"task": ea[j].get("task"), "expected": None,
                           "got": pa[i].get("assignee"), "kind": "gán thừa"})
        else:
            errors.append({"task": ea[j].get("task"), "expected": ea[j].get("assignee"),
                           "got": pa[i].get("assignee"), "kind": "gán sai người"})
    n = len(matched)
    # Bẫy: nếu KHÔNG ghép được cặp nào, `expected = 0` và recall/precision đều
    # trả 1.0 theo quy ước "không có gì để sai". Với thước đo phụ thuộc vào
    # thước đo khác thì quy ước đó sai nguy hiểm: một mô hình trả về RỖNG sẽ
    # được điểm tuyệt đối ở cả `assignees` lẫn `due_dates`, tức là 0.45 điểm
    # tổng cho việc không làm gì. Không làm gì phải bị điểm 0, không phải điểm
    # cao hơn làm sai.
    if not n and ea:
        return (MetricResult("assignees", 0, len(ea), 0,
                             [a.get("task", "") for a in ea], []), errors)
    return (MetricResult("assignees", correct, n, n, [], []), errors)


def _due_dates(produced: dict, expected: dict) -> tuple[MetricResult, list[dict]]:
    """Chấm hạn chót, chấp nhận lệch tối đa MỘT ngày.

    Lệch một ngày thường là do quy ước "cuối tuần này" — hiểu là thứ 6 hay
    chủ nhật đều có lý. Lệch hai ngày trở lên là hiểu sai lời nói.
    """
    pa = produced.get("action_items") or []
    ea = expected.get("action_items") or []
    matched, _m, _s = _match_lists([a.get("task", "") for a in pa],
                                   [a.get("task", "") for a in ea])
    correct = 0
    errors: list[dict] = []
    counted = 0
    for i, j in matched:
        got, want = pa[i].get("due_date"), ea[j].get("due_date")
        if not want and not got:
            continue                       # cả hai đều không có hạn: không tính
        counted += 1
        if got == want:
            correct += 1
            continue
        delta = _day_delta(got, want)
        if delta is not None and delta <= 1:
            correct += 1
            continue
        errors.append({"task": ea[j].get("task"), "expected": want, "got": got,
                       "lech_ngay": delta})
    # Cùng lý do như `_assignees`: không ghép được việc nào thì không được
    # coi là "không có gì để sai".
    if not matched and any(a.get("due_date") for a in ea):
        n_due = sum(1 for a in ea if a.get("due_date"))
        return (MetricResult("due_dates", 0, n_due, 0, [], []), errors)
    return (MetricResult("due_dates", correct, counted, counted, [], []), errors)


def _day_delta(a: str | None, b: str | None) -> int | None:
    try:
        return abs((date.fromisoformat(str(a)) - date.fromisoformat(str(b))).days)
    except (TypeError, ValueError):
        return None


def _hallucinations(produced: dict, transcript: dict | None) -> list[str]:
    """Mục dẫn chứng tới đoạn thoại không tồn tại.

    Đây là thước đo tuyệt đối, không cần bản chuẩn: hoặc đoạn đó có trong bản
    thoại, hoặc không.
    """
    if not transcript:
        return []
    valid = {s.get("id") for s in (transcript.get("segments") or [])}
    if not valid:
        return []
    out = []
    for group in ("decisions", "action_items"):
        for item in produced.get(group) or []:
            ids = item.get("evidence_segment_ids") or []
            if ids and not any(i in valid for i in ids):
                out.append(item.get("statement") or item.get("task") or item.get("id", "?"))
    return out


# ===========================================================================
#  Chấm điểm
# ===========================================================================

def evaluate_minutes(produced: dict, expected: dict, *,
                     transcript: dict | None = None,
                     meeting_id: str = "") -> MeetingScore:
    """Chấm một biên bản AI so với bản người đã duyệt."""
    dec = _decisions(produced, expected)
    act = _actions(produced, expected)
    asg, asg_errors = _assignees(produced, expected)
    due, due_errors = _due_dates(produced, expected)
    metrics = {"decisions": dec, "actions": act, "assignees": asg, "due_dates": due}

    # Chỉ tính những thước đo THỰC SỰ áp dụng được, rồi chuẩn hoá lại trọng số.
    #
    # Cuộc họp mà bản chuẩn không có hạn chót nào thì `due_dates` không đo được
    # gì. Cho nó điểm 1.0 là tặng không 0.15 điểm cho mọi mô hình, kể cả mô
    # hình trả về rỗng; cho nó 0 là phạt oan. Bỏ ra ngoài rồi chia lại là cách
    # duy nhất không thiên vị bên nào.
    applicable = {k: m for k, m in metrics.items() if m.expected > 0}
    if applicable:
        total_w = sum(WEIGHTS[k] for k in applicable)
        overall = sum(applicable[k].f1 * WEIGHTS[k] for k in applicable) / total_w
    else:
        overall = 1.0 if not any(produced.get(g) for g in ("decisions", "action_items")) else 0.0
    halluc = _hallucinations(produced, transcript)
    if halluc:
        # Bịa dẫn chứng là lỗi khác loại với bỏ sót: nó phá lời hứa cốt lõi
        # của sản phẩm ("mọi mệnh đề đều truy về được câu nói gốc"). Phạt
        # thẳng vào điểm tổng chứ không để lẫn vào các thước đo khác.
        overall *= max(0.0, 1 - 0.1 * len(halluc))

    notes: list[str] = []
    if dec.missed:
        notes.append(f"Bỏ sót {len(dec.missed)} quyết định — biên bản thiếu quyết định "
                     f"thì mất phần lớn giá trị.")
    if any(e["kind"] == "gán sai người" for e in asg_errors):
        n = sum(1 for e in asg_errors if e["kind"] == "gán sai người")
        notes.append(f"Gán sai người ở {n} công việc — đây là loại lỗi nguy hiểm nhất, "
                     f"phải bằng 0 mới tính đến chuyện thay mô hình.")
    if any(e["kind"] == "gán thừa" for e in asg_errors):
        notes.append("Có việc mô hình tự gán người trong khi bản chuẩn để trống — "
                     "dấu hiệu mô hình đang suy đoán.")
    if halluc:
        notes.append(f"{len(halluc)} mục dẫn chứng tới đoạn thoại không tồn tại.")
    if not notes:
        notes.append("Không phát hiện lỗi thuộc bốn nhóm đang đo.")

    return MeetingScore(meeting_id=meeting_id or produced.get("meeting_id", ""),
                        overall=overall, metrics=metrics, assignee_errors=asg_errors,
                        due_errors=due_errors, hallucinations=halluc, notes=notes,
                        applicable=sorted(applicable))


def evaluate_dataset(cases: Iterable[dict]) -> dict[str, Any]:
    """Chấm nhiều cuộc họp, tổng hợp lại.

    Mỗi phần tử: ``{"produced": {...}, "expected": {...}, "transcript": {...}}``
    """
    scores = [
        evaluate_minutes(c["produced"], c["expected"],
                         transcript=c.get("transcript"),
                         meeting_id=c.get("meeting_id", ""))
        for c in cases
    ]
    if not scores:
        return {"n": 0, "overall": 0.0, "cases": [],
                "verdict": "Chưa có mẫu nào để chấm."}

    def avg(fn):
        return round(statistics.fmean(fn(s) for s in scores), 4)

    overall = avg(lambda s: s.overall)
    by_metric = {k: {"f1": avg(lambda s, k=k: s.metrics[k].f1),
                     "recall": avg(lambda s, k=k: s.metrics[k].recall),
                     "precision": avg(lambda s, k=k: s.metrics[k].precision)}
                 for k in WEIGHTS}
    wrong_people = sum(1 for s in scores
                       for e in s.assignee_errors if e["kind"] == "gán sai người")
    halluc = sum(len(s.hallucinations) for s in scores)

    if wrong_people:
        verdict = (f"KHÔNG ĐẠT: gán sai người ở {wrong_people} công việc trên "
                   f"{len(scores)} cuộc họp. Chỉ số này phải bằng 0.")
    elif halluc:
        verdict = f"KHÔNG ĐẠT: còn {halluc} mục bịa dẫn chứng."
    elif by_metric["decisions"]["recall"] < 0.8:
        verdict = (f"CHƯA ĐẠT: chỉ bắt được "
                   f"{by_metric['decisions']['recall'] * 100:.0f}% số quyết định.")
    elif overall >= 0.85:
        verdict = (f"ĐẠT trên {len(scores)} mẫu (điểm {overall:.2f}). "
                   f"Cần ít nhất 20 cuộc họp đa dạng trước khi kết luận.")
    else:
        verdict = f"GẦN ĐẠT: điểm tổng {overall:.2f}, chưa tới ngưỡng 0.85."

    return {"n": len(scores), "overall": overall, "by_metric": by_metric,
            "wrong_assignees": wrong_people, "hallucinations": halluc,
            "verdict": verdict, "cases": [s.to_dict() for s in scores]}


def compare_models(runs: dict[str, list[dict]]) -> dict[str, Any]:
    """Chấm nhiều mô hình trên cùng bộ dữ liệu rồi xếp hạng.

    ``runs``: ``{"gemini": [case, ...], "local": [case, ...]}``

    Đây là thứ trả lời câu "có nên thay API bằng mô hình cục bộ chưa" —
    trên chính dữ liệu của tổ chức này, không phải benchmark chung chung.
    """
    results = {name: evaluate_dataset(cases) for name, cases in runs.items()}
    ranked = sorted(results.items(), key=lambda kv: kv[1]["overall"], reverse=True)
    best = ranked[0][0] if ranked else None

    # Mô hình có điểm cao nhất VẪN không được chọn nếu còn gán sai người.
    # Điểm trung bình cao che được một lỗi chết người, và đó là lý do không
    # bao giờ xếp hạng chỉ bằng một con số.
    safe = [n for n, r in ranked if r["wrong_assignees"] == 0]
    return {
        "results": results,
        "ranking": [{"model": n, "overall": r["overall"],
                     "wrong_assignees": r["wrong_assignees"]} for n, r in ranked],
        "best_by_score": best,
        "recommended": safe[0] if safe else None,
        "note": ("Mô hình điểm cao nhất còn gán sai người — không khuyến nghị dùng, "
                 "bất kể điểm tổng."
                 if best and results[best]["wrong_assignees"]
                 else "Mô hình khuyến nghị là mô hình điểm cao nhất trong nhóm "
                      "không gán sai người nào."),
    }


# ===========================================================================
#  Chạy từ dòng lệnh
# ===========================================================================

def _load_cases(path: Path) -> list[dict]:
    cases = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def main(argv: Sequence[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="Meeting-Bench — chấm điểm biên bản AI so với bản người đã duyệt")
    ap.add_argument("cases", type=Path,
                    help="tệp .jsonl, mỗi dòng {produced, expected, transcript}")
    ap.add_argument("--json", action="store_true", help="in kết quả dạng JSON")
    args = ap.parse_args(argv)

    if not args.cases.exists():
        print(f"Không có tệp {args.cases}")
        return 1
    report = evaluate_dataset(_load_cases(args.cases))

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"\n  MEETING-BENCH · {report['n']} cuộc họp")
    print("  " + "=" * 56)
    print(f"  Điểm tổng: {report['overall']:.3f}\n")
    print(f"  {'Thước đo':<16}{'F1':>8}{'Recall':>10}{'Precision':>12}")
    print("  " + "-" * 46)
    vi = {"decisions": "Quyết định", "actions": "Công việc",
          "assignees": "Người nhận", "due_dates": "Hạn chót"}
    for k, m in report["by_metric"].items():
        print(f"  {vi[k]:<16}{m['f1']:>8.3f}{m['recall']:>10.3f}{m['precision']:>12.3f}")
    print()
    if report["wrong_assignees"]:
        print(f"  ! Gán sai người: {report['wrong_assignees']} chỗ")
    if report["hallucinations"]:
        print(f"  ! Bịa dẫn chứng: {report['hallucinations']} chỗ")
    print(f"\n  {report['verdict']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
