"""Kiểm thử Meeting-Bench — bộ chấm điểm biên bản (Hạng mục 13).

Bộ chấm điểm mà sai thì nguy hiểm hơn không có: nó sẽ khiến người ta chọn
nhầm mô hình một cách tự tin. Nên nó phải được kiểm bằng những trường hợp mà
"gần đúng" là không chấp nhận được.
"""

from __future__ import annotations

import pytest

from ai.meeting_evaluator import (
    MATCH_THRESHOLD,
    WEIGHTS,
    compare_models,
    evaluate_dataset,
    evaluate_minutes,
)

TX = {"segments": [{"id": "s_0001"}, {"id": "s_0002"}, {"id": "s_0003"}]}


def _minutes(decisions=(), actions=()):
    return {
        "decisions": [{"statement": d, "evidence_segment_ids": ["s_0001"]}
                      for d in decisions],
        "action_items": [{"task": t, "assignee": a, "due_date": d,
                          "evidence_segment_ids": ["s_0002"]}
                         for t, a, d in actions],
    }


def test_perfect_match_scores_one():
    m = _minutes(["Chốt ngân sách 450 triệu"], [("Gửi kế hoạch", "Nam", "2026-08-25")])
    s = evaluate_minutes(m, m, transcript=TX)
    assert s.overall == pytest.approx(1.0)
    assert s.assignee_errors == [] and s.hallucinations == []


def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_assignee_weighted_highest():
    """Gán sai người là lỗi nguy hiểm nhất — trọng số phải phản ánh điều đó."""
    assert WEIGHTS["assignees"] == max(WEIGHTS.values())


def test_missed_decision_is_caught():
    expected = _minutes(["Chốt ngân sách 450 triệu", "Hoãn tuyển người miền Trung"])
    produced = _minutes(["Chốt ngân sách 450 triệu"])
    s = evaluate_minutes(produced, expected, transcript=TX)
    assert s.metrics["decisions"].recall == pytest.approx(0.5)
    assert len(s.metrics["decisions"].missed) == 1
    assert any("Bỏ sót" in n for n in s.notes)


def test_different_wording_still_matches():
    expected = _minutes(["Chốt ngân sách 450 triệu cho Đà Nẵng"])
    produced = _minutes(["Ngân sách Đà Nẵng chốt ở mức 450 triệu"])
    s = evaluate_minutes(produced, expected, transcript=TX)
    assert s.metrics["decisions"].recall == 1.0


def test_unrelated_statement_does_not_match():
    expected = _minutes(["Chốt ngân sách 450 triệu cho Đà Nẵng"])
    produced = _minutes(["Tuyển thêm hai kỹ sư backend trong quý sau"])
    s = evaluate_minutes(produced, expected, transcript=TX)
    assert s.metrics["decisions"].matched == 0
    assert len(s.metrics["decisions"].spurious) == 1


def test_wrong_assignee_flagged_with_detail():
    expected = _minutes(actions=[("Viết bộ test thanh toán", "Lan", None)])
    produced = _minutes(actions=[("Viết bộ test thanh toán", "Tuấn", None)])
    s = evaluate_minutes(produced, expected, transcript=TX)
    assert s.metrics["assignees"].recall == 0.0
    err = s.assignee_errors[0]
    assert err["kind"] == "gán sai người"
    assert err["expected"] == "Lan" and err["got"] == "Tuấn"
    assert any("nguy hiểm nhất" in n for n in s.notes)


def test_leaving_blank_when_truth_is_blank_is_correct():
    """Mô hình thận trọng phải được điểm cao hơn mô hình đoán bừa.

    Nếu chấm ngược lại, ta đang tự huấn luyện mình chọn nhầm mô hình.
    """
    expected = _minutes(actions=[("Dọn dữ liệu cũ", None, None)])
    produced = _minutes(actions=[("Dọn dữ liệu cũ", None, None)])
    s = evaluate_minutes(produced, expected, transcript=TX)
    assert s.metrics["assignees"].recall == 1.0
    assert s.assignee_errors == []


def test_guessing_a_name_when_truth_is_blank_is_penalised():
    expected = _minutes(actions=[("Dọn dữ liệu cũ", None, None)])
    produced = _minutes(actions=[("Dọn dữ liệu cũ", "Tuấn", None)])
    s = evaluate_minutes(produced, expected, transcript=TX)
    assert s.assignee_errors[0]["kind"] == "gán thừa"
    assert any("suy đoán" in n for n in s.notes)


def test_due_date_tolerates_one_day():
    expected = _minutes(actions=[("Gửi kế hoạch", "Nam", "2026-08-25")])
    near = _minutes(actions=[("Gửi kế hoạch", "Nam", "2026-08-26")])
    far = _minutes(actions=[("Gửi kế hoạch", "Nam", "2026-08-30")])
    assert evaluate_minutes(near, expected, transcript=TX).metrics["due_dates"].recall == 1.0
    s = evaluate_minutes(far, expected, transcript=TX)
    assert s.metrics["due_dates"].recall == 0.0
    assert s.due_errors[0]["lech_ngay"] == 5


def test_no_due_on_both_sides_is_not_counted():
    m = _minutes(actions=[("Việc không hạn", "Nam", None)])
    s = evaluate_minutes(m, m, transcript=TX)
    assert s.metrics["due_dates"].expected == 0
    assert s.metrics["due_dates"].recall == 1.0


def test_hallucination_detected_and_penalised():
    expected = _minutes(["Chốt A"])
    produced = {"decisions": [{"statement": "Chốt A",
                               "evidence_segment_ids": ["s_9999"]}],
                "action_items": []}
    s = evaluate_minutes(produced, expected, transcript=TX)
    assert s.hallucinations
    assert s.overall < 1.0, "bịa dẫn chứng phải bị phạt vào điểm tổng"


def test_hallucination_needs_transcript_to_detect():
    produced = {"decisions": [{"statement": "X", "evidence_segment_ids": ["s_9999"]}],
                "action_items": []}
    s = evaluate_minutes(produced, _minutes(["X"]), transcript=None)
    assert s.hallucinations == [], "không có bản thoại thì không kết luận được"


def test_empty_produced_scores_zero_recall():
    expected = _minutes(["A", "B"], [("T", "N", None)])
    s = evaluate_minutes({"decisions": [], "action_items": []}, expected, transcript=TX)
    assert s.metrics["decisions"].recall == 0.0
    assert s.metrics["actions"].recall == 0.0
    assert s.overall == pytest.approx(0.0), (
        "biên bản rỗng phải được 0 điểm — không làm gì không thể hơn làm sai")


def test_dataset_verdict_blocks_on_wrong_assignee():
    cases = [
        {"produced": _minutes(["A"], [("T", "Tuấn", None)]),
         "expected": _minutes(["A"], [("T", "Lan", None)]),
         "transcript": TX, "meeting_id": "m1"},
    ]
    r = evaluate_dataset(cases)
    assert r["wrong_assignees"] == 1
    assert r["verdict"].startswith("KHÔNG ĐẠT")


def test_dataset_verdict_requires_more_samples_even_when_perfect():
    m = _minutes(["A"], [("T", "Lan", None)])
    cases = [{"produced": m, "expected": m, "transcript": TX} for _ in range(3)]
    r = evaluate_dataset(cases)
    assert r["overall"] == pytest.approx(1.0)
    assert "20 cuộc họp" in r["verdict"], "một mẫu đẹp chưa kết luận được gì"


def test_empty_dataset_does_not_crash():
    r = evaluate_dataset([])
    assert r["n"] == 0 and r["overall"] == 0.0


def test_compare_models_refuses_to_recommend_unsafe_winner():
    """Mô hình điểm cao nhất mà gán sai người thì KHÔNG được khuyến nghị.

    Điểm trung bình cao che được một lỗi chết người — đó là lý do không bao
    giờ xếp hạng chỉ bằng một con số.
    """
    # "manh" bắt đủ mọi quyết định và mọi việc, chỉ sai đúng một người nhận.
    # "an_toan" bỏ sót gần hết nhưng không gán sai ai.
    truth = _minutes(["A", "B", "C", "D", "E"],
                     [("T1", "Lan", None), ("T2", "Nam", None), ("T3", "Mai", None)])
    strong_but_wrong = {
        "produced": _minutes(["A", "B", "C", "D", "E"],
                             [("T1", "Tuấn", None), ("T2", "Nam", None), ("T3", "Mai", None)]),
        "expected": truth, "transcript": TX}
    weak_but_safe = {
        "produced": _minutes(["A"], [("T1", "Lan", None)]),
        "expected": truth, "transcript": TX}
    r = compare_models({"manh": [strong_but_wrong], "an_toan": [weak_but_safe]})
    assert r["best_by_score"] == "manh"
    assert r["recommended"] == "an_toan"
    assert "không khuyến nghị" in r["note"]


def test_compare_models_ranks_by_overall():
    truth = _minutes(["A", "B"], [("T", "Lan", None)])
    good = {"produced": truth, "expected": truth, "transcript": TX}
    bad = {"produced": _minutes([], []), "expected": truth, "transcript": TX}
    r = compare_models({"tot": [good], "te": [bad]})
    assert r["ranking"][0]["model"] == "tot"
    assert r["recommended"] == "tot"


def test_match_threshold_is_documented_value():
    assert 0.4 <= MATCH_THRESHOLD <= 0.7, "ngưỡng quá lỏng hoặc quá chặt"
