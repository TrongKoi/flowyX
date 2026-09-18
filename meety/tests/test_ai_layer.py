"""Kiểm thử tầng AI — agent, thu dữ liệu chưng cất, đối soát hai mô hình.

Ba nhóm, mỗi nhóm nhắm vào một lời hứa mà tầng này đưa ra:

  1. **Agent không được để lọt nội dung bịa.** Chốt chặn bằng Python phải chạy
     kể cả khi mô hình lờ hết prompt. Test ở đây dùng một provider giả CỐ Ý
     trả về rác — dẫn chứng trỏ tới đoạn không tồn tại, câu trích không có
     trong bản thoại, người nhận việc không dự họp.
  2. **Ẩn danh phải thật sự ẩn.** Tệp huấn luyện sẽ được copy đi nhiều nơi;
     mọi bản sao phải đã sạch.
  3. **Đối soát phải đo đúng thứ có hậu quả.** "Giống nhau 80%" là con số vô
     nghĩa; "bỏ sót 2 quyết định, lệch 1 người nhận việc" mới dùng được.

    pytest tests/test_ai_layer.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from ai.agent import (
    AgentResult,
    ExtractedActions,
    ExtractedDecisions,
    MeetingAgent,
    _clean_assignees,
    _prune_ungrounded,
    _verify_quotes,
    score_confidence,
)
from ai.collector import DataCollector, PIIMap, anonymise_text
from ai.consensus import ConsensusEngine, compare_results
from providers.base import LLMProvider, LLMResponse

ROOT = Path(__file__).resolve().parents[1]


# ===========================================================================
#  Provider giả — điều khiển được đầu ra để dựng đúng tình huống cần thử
# ===========================================================================

class ScriptedProvider(LLMProvider):
    """Trả về payload đã định sẵn theo thứ tự lược đồ được hỏi."""

    name = "scripted"

    def __init__(self, model: str = "test", **payloads):
        self.model = model
        self.payloads = payloads
        self.calls: list[str] = []

    def generate_json(self, prompt, schema, *, system=None, temperature=0.0,
                      max_output_tokens=None) -> LLMResponse:
        key = schema.__name__
        self.calls.append(key)
        payload = self.payloads.get(key, {})
        if callable(payload):
            payload = payload(prompt)
        return LLMResponse(payload=payload, raw_text=json.dumps(payload, ensure_ascii=False),
                           input_tokens=10, output_tokens=10)


TRANSCRIPT = {
    "meeting_id": "mtg_test",
    "speakers": [
        {"label": "SPEAKER_00", "display_name": "Nguyễn Anh Tuấn"},
        {"label": "SPEAKER_01", "display_name": "Trần Thị Lan"},
    ],
    "segments": [
        {"id": "s_0001", "speaker_label": "SPEAKER_00", "start_ms": 0, "end_ms": 5000,
         "text": "Chốt là sprint sau ưu tiên sửa luồng thanh toán."},
        {"id": "s_0002", "speaker_label": "SPEAKER_01", "start_ms": 6000, "end_ms": 11000,
         "text": "Chị nhận phần viết lại bộ test thanh toán, xong trước thứ sáu."},
        {"id": "s_0003", "speaker_label": "SPEAKER_00", "start_ms": 12000, "end_ms": 17000,
         "text": "Còn phần tài liệu thì chưa ai nhận.", "is_low_quality": True},
    ],
}


# ===========================================================================
#  1 · Chốt chặn chống bịa
# ===========================================================================

def test_prune_removes_items_pointing_at_nonexistent_segments():
    items = [
        {"statement": "Có thật", "evidence_segment_ids": ["s_0001"]},
        {"statement": "Bịa", "evidence_segment_ids": ["s_9999"]},
        {"statement": "Không có dẫn chứng", "evidence_segment_ids": []},
        {"statement": "Nửa thật", "evidence_segment_ids": ["s_0002", "s_8888"]},
    ]
    kept, dropped = _prune_ungrounded(items, {"s_0001", "s_0002", "s_0003"})
    assert dropped == 2
    assert [k["statement"] for k in kept] == ["Có thật", "Nửa thật"]
    # Mục nửa thật phải bị cắt bỏ phần dẫn chứng giả, không giữ lại
    assert kept[1]["evidence_segment_ids"] == ["s_0002"]


def test_verify_quotes_flags_invented_quotes():
    items = [
        {"quote": "Chốt là sprint sau ưu tiên sửa luồng thanh toán"},
        {"quote": "Câu này chưa ai từng nói trong cuộc họp"},
        {"quote": ""},
    ]
    out = _verify_quotes(items, TRANSCRIPT["segments"])
    assert out[0]["quote_verified"] is True
    assert out[1]["quote_verified"] is False
    assert out[2]["quote_verified"] is False


def test_verify_quotes_tolerates_punctuation_and_case():
    """Mô hình hay đổi dấu câu; đó không phải bịa."""
    items = [{"quote": "CHỐT LÀ SPRINT SAU, ưu tiên sửa luồng thanh toán!!!"}]
    assert _verify_quotes(items, TRANSCRIPT["segments"])[0]["quote_verified"] is True


def test_clean_assignees_drops_people_not_in_the_meeting():
    speakers = {"SPEAKER_00": "Nguyễn Anh Tuấn", "SPEAKER_01": "Trần Thị Lan"}
    actions = [
        {"task": "A", "assignee": "Trần Thị Lan"},
        {"task": "B", "assignee": "Lan"},               # tên riêng, vẫn khớp
        {"task": "C", "assignee": "Phạm Văn Không Có"},  # không dự họp
        {"task": "D", "assignee": None},
    ]
    out = _clean_assignees(actions, speakers)
    assert out[0]["assignee"] == "Trần Thị Lan"
    assert out[1]["assignee"] == "Lan"
    assert out[2]["assignee"] is None and out[2]["assignee_rejected"] is True
    assert out[3]["assignee"] is None


def test_agent_survives_a_provider_that_ignores_every_rule():
    """Mô hình trả về rác hoàn toàn → agent phải lọc sạch, không ném lỗi.

    Đây là phép kiểm quan trọng nhất của file: prompt có thể bị lờ đi, nhưng
    chốt chặn bằng Python thì không.
    """
    junk = ScriptedProvider(
        DistilledPoints={"points": [
            {"text": "Điểm bịa", "topic": "x", "evidence_segment_ids": ["s_7777"]},
            {"text": "Điểm thật", "topic": "y", "evidence_segment_ids": ["s_0001"]},
        ]},
        ExtractedDecisions={"decisions": [
            {"statement": "Quyết định bịa hoàn toàn", "quote": "Không ai nói câu này",
             "evidence_segment_ids": ["s_0001"], "decided_by": "Người Không Tồn Tại"},
            {"statement": "Quyết định không dẫn chứng", "quote": "x",
             "evidence_segment_ids": ["s_5555"]},
        ]},
        ExtractedActions={"actions": [
            {"task": "Việc gán sai người", "assignee": "Đỗ Văn Lạ", "quote": "y",
             "evidence_segment_ids": ["s_0002"], "commitment_strength": "firm"},
        ]},
    )
    result = MeetingAgent(junk).run(TRANSCRIPT)

    assert len(result.points) == 1, "điểm không có dẫn chứng thật phải bị loại"
    assert result.dropped["points"] == 1
    assert len(result.decisions) == 1, "quyết định dẫn chứng giả phải bị loại"
    assert result.decisions[0]["quote_verified"] is False, "câu trích bịa phải bị gắn cờ"
    assert result.actions[0]["assignee"] is None, "người không dự họp phải bị gỡ"
    assert result.actions[0]["assignee_rejected"] is True
    # Rác nhiều thì điểm tin cậy phải xuống thấp
    assert result.confidence["score"] < 60, result.confidence


def test_agent_reports_provider_and_token_usage():
    p = ScriptedProvider(model="m1", DistilledPoints={"points": []},
                         ExtractedDecisions={"decisions": []},
                         ExtractedActions={"actions": []})
    r = MeetingAgent(p).run(TRANSCRIPT)
    assert r.provider == "scripted/m1"
    assert r.llm_calls == 3, "một lượt nén + hai lượt trích xuất"
    assert r.input_tokens > 0 and r.output_tokens > 0


def test_agent_chunks_long_transcripts():
    """Bản thoại dài phải chia nhiều lượt gọi, cắt theo ĐOẠN chứ không theo ký tự."""
    long_tx = {
        "meeting_id": "m", "speakers": TRANSCRIPT["speakers"],
        "segments": [{"id": f"s_{i:04d}", "speaker_label": "SPEAKER_00",
                      "start_ms": i * 1000, "end_ms": i * 1000 + 900, "text": f"Câu {i}"}
                     for i in range(1, 501)],
    }
    p = ScriptedProvider(DistilledPoints={"points": []},
                         ExtractedDecisions={"decisions": []},
                         ExtractedActions={"actions": []})
    MeetingAgent(p, max_segments_per_call=220).run(long_tx)
    assert p.calls.count("DistilledPoints") == 3      # 500 đoạn / 220
    assert p.calls.count("ExtractedDecisions") == 1


def test_agent_rejects_empty_transcript():
    from providers.base import ProviderError
    p = ScriptedProvider()
    with pytest.raises(ProviderError):
        MeetingAgent(p).run({"segments": []})


def test_confidence_formula_matches_the_one_on_screen():
    """Cùng công thức đang hiển thị cho người dùng, không được lệch."""
    segments = [{"id": "s1", "is_low_quality": True}, {"id": "s2"}]
    actions = [{"assignee": None}, {"assignee": "A"}, {"quote_verified": False}]
    decisions = [{"quote_verified": True}]
    c = score_confidence(decisions, actions, segments, {})
    # 100 − (1 thoại mờ × 5) − (2 chưa gán × 8) − (1 ảo giác × 15) = 64
    assert c["deducted"] == 5 + 16 + 15
    assert c["score"] == 64
    assert c["tone"] == "coral"


def test_confidence_never_leaves_zero_to_hundred():
    segments = [{"id": f"s{i}", "is_low_quality": True} for i in range(40)]
    c = score_confidence([], [], segments, {})
    assert c["score"] == 0 and c["raw"] < 0 and c["floored"] is True


# ===========================================================================
#  2 · Ẩn danh dữ liệu chưng cất
# ===========================================================================

@pytest.mark.parametrize("text,kind", [
    ("Gửi mail cho an.nguyen@congty.vn nhé", "EMAIL"),
    ("Gọi số 0912 345 678 đi", "ĐIỆN_THOẠI"),
    ("Số +84 912345678 cũng được", "ĐIỆN_THOẠI"),
    ("Xem tại https://drive.google.com/file/abc?token=xyz", "LIÊN_KẾT"),
    ("Chuyển vào tài khoản 19001234567890", "SỐ_TÀI_KHOẢN"),
    ("CCCD của em là 001234567890", "CCCD"),
])
def test_pii_patterns_are_masked(text, kind):
    pii = PIIMap()
    out = anonymise_text(text, pii)
    assert kind in "".join(pii._map.values()) or f"[{kind}" in out, out
    # dữ liệu gốc không được còn sót
    for token in ["an.nguyen@congty.vn", "0912 345 678", "drive.google.com",
                  "19001234567890", "001234567890"]:
        if token in text:
            assert token not in out, f"{token} còn nguyên trong: {out}"


def test_same_person_gets_same_token_within_one_meeting():
    """Nếu mỗi lần thay một mã khác, quan hệ giữa các lượt nói biến mất và mẫu
    huấn luyện mất phần lớn giá trị."""
    pii = PIIMap()
    names = ["Nguyễn Anh Tuấn"]
    a = anonymise_text("Anh Tuấn nói vậy", pii, names)
    b = anonymise_text("Nguyễn Anh Tuấn đồng ý", pii, names)
    assert "[NGƯỜI_1]" in a and "[NGƯỜI_1]" in b


def test_longer_names_masked_before_shorter():
    """Không có thứ tự này, "Nguyễn Văn An" thành "[NGƯỜI_1] Văn An"."""
    pii = PIIMap()
    out = anonymise_text("Nguyễn Văn An và An cùng làm", pii,
                         ["Nguyễn Văn An", "An"])
    assert "Nguyễn" not in out and "Văn" not in out


def test_url_masked_before_phone_pattern_eats_it():
    pii = PIIMap()
    out = anonymise_text("https://x.vn/2026/08/12345678", pii)
    assert out.count("[") == 1, f"URL bị cắt vụn: {out}"


def test_collector_disabled_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("MEETY_COLLECT_TRAINING", raising=False)
    c = DataCollector(tmp_path / "d.jsonl")
    assert c.enabled is False
    res = c.collect(meeting_id="m", transcript=TRANSCRIPT, minutes={"meta": {}})
    assert res["written"] is False
    assert not (tmp_path / "d.jsonl").exists()


def test_collector_writes_anonymised_record(tmp_path):
    minutes = {
        "meta": {"meeting_title": "Họp thử", "attendees": [
            {"display_name": "Nguyễn Anh Tuấn"}, {"display_name": "Trần Thị Lan"}]},
        "executive_summary": {"tldr": ["Nguyễn Anh Tuấn nhận việc, mail tuan@congty.vn"]},
        "decisions": [{"statement": "Chốt X", "decided_by": "Trần Thị Lan",
                       "quote": "Chị Lan chốt", "evidence_segment_ids": ["s_0001"]}],
        "action_items": [{"task": "Làm Y", "assignee": "Nguyễn Anh Tuấn",
                          "quote": "Anh Tuấn nhận", "evidence_segment_ids": ["s_0002"]}],
    }
    c = DataCollector(tmp_path / "d.jsonl", enabled=True)
    res = c.collect(meeting_id="mtg_bi_mat", transcript=TRANSCRIPT, minutes=minutes,
                    approved_by="u_123")
    assert res["written"] is True

    raw = (tmp_path / "d.jsonl").read_text(encoding="utf-8")
    rec = json.loads(raw)
    assert "instruction" in rec and "input" in rec and "output" in rec

    # Không tên thật, không email, không id cuộc họp thật ở bất kỳ đâu
    assert "Nguyễn Anh Tuấn" not in raw
    assert "Trần Thị Lan" not in raw
    assert "tuan@congty.vn" not in raw
    assert "mtg_bi_mat" not in raw, "id cuộc họp truy ngược được về tổ chức"
    assert "u_123" not in raw, "id người duyệt phải băm"
    assert "[NGƯỜI_" in raw

    assert rec["meta"]["approved"] is True
    assert rec["meta"]["n_decisions"] == 1


def test_collector_output_keeps_only_learnable_fields(tmp_path):
    """Siêu dữ liệu vận hành không phải thứ mô hình phải đoán."""
    minutes = {
        "meta": {"meeting_title": "T", "attendees": []},
        "executive_summary": {"tldr": ["a"]},
        "decisions": [{"statement": "S", "quote": "q", "evidence_segment_ids": [],
                       "id": "d_001", "timestamp_ms": 1234, "review_state": "ai_generated"}],
        "action_items": [],
        "pipeline": {"llm_provider": "gemini", "cost_usd": 0.01},
    }
    c = DataCollector(tmp_path / "d.jsonl", enabled=True)
    out = json.loads(c.build_record(meeting_id="m", transcript=TRANSCRIPT,
                                    minutes=minutes)["output"])
    assert set(out) == {"executive_summary", "decisions", "action_items"}
    assert "id" not in out["decisions"][0]
    assert "timestamp_ms" not in out["decisions"][0]


def test_collector_never_raises_on_bad_input(tmp_path):
    c = DataCollector(tmp_path / "d.jsonl", enabled=True)
    for bad in [None, {}, {"meta": None}, {"decisions": "không phải danh sách"}]:
        res = c.collect(meeting_id="m", transcript=TRANSCRIPT, minutes=bad)
        assert isinstance(res, dict) and "written" in res


def test_dataset_stats_and_split(tmp_path):
    c = DataCollector(tmp_path / "d.jsonl", enabled=True)
    minutes = {"meta": {"meeting_title": "T", "attendees": []},
               "executive_summary": {"tldr": []}, "decisions": [], "action_items": []}
    for i in range(12):
        c.collect(meeting_id=f"m{i}", transcript=TRANSCRIPT, minutes=minutes)
    st = c.stats()
    assert st["samples"] == 12 and st["approved_samples"] == 12
    assert st["ready_for_finetune"] is False
    assert "Cần thêm" in st["note"]

    split = c.export_train_val(tmp_path / "out", val_ratio=0.25)
    assert split["train"] + split["val"] == split["deduped"]
    assert (tmp_path / "out" / "train.jsonl").exists()


def test_dataset_dedupes_identical_samples(tmp_path):
    c = DataCollector(tmp_path / "d.jsonl", enabled=True)
    minutes = {"meta": {"meeting_title": "T", "attendees": []},
               "executive_summary": {"tldr": ["x"]}, "decisions": [], "action_items": []}
    for _ in range(5):
        c.collect(meeting_id="cùng-một-cuộc-họp", transcript=TRANSCRIPT, minutes=minutes)
    assert c.stats()["samples"] == 5
    assert c.stats()["unique"] == 1, "cùng nội dung phải cho cùng sample_id"


# ===========================================================================
#  3 · Đối soát hai mô hình
# ===========================================================================

def _result(provider="a/1", decisions=(), actions=(), dropped=0, conf=90) -> AgentResult:
    return AgentResult(
        points=[], decisions=list(decisions), actions=list(actions),
        confidence={"score": conf}, provider=provider, llm_calls=3,
        input_tokens=1, output_tokens=1,
        dropped={"points": 0, "decisions": dropped, "actions": 0})


def test_comparison_detects_missed_decisions():
    primary = _result(decisions=[
        {"statement": "Chốt ngân sách 450 triệu cho thử nghiệm Đà Nẵng"},
        {"statement": "Tách database staging sang sprint 26"},
    ])
    secondary = _result(provider="b/1", decisions=[
        {"statement": "Chốt ngân sách 450 triệu cho thử nghiệm Đà Nẵng"},
    ])
    rep = compare_results(primary, secondary)
    assert rep.decisions_matched == 1
    assert len(rep.decisions_missed_by_secondary) == 1
    assert "bỏ sót" in rep.verdict


def test_comparison_tolerates_different_wording():
    """Hai mô hình diễn đạt khác nhau cho cùng một quyết định là bình thường."""
    primary = _result(decisions=[{"statement": "Chốt ngân sách 450 triệu cho Đà Nẵng"}])
    secondary = _result(provider="b/1",
                        decisions=[{"statement": "Ngân sách Đà Nẵng chốt ở mức 450 triệu"}])
    assert compare_results(primary, secondary).decisions_matched == 1


def test_comparison_flags_assignee_conflict_as_worst_case():
    primary = _result(actions=[{"task": "Viết bộ test thanh toán", "assignee": "Lan"}])
    secondary = _result(provider="b/1",
                        actions=[{"task": "Viết bộ test thanh toán", "assignee": "Tuấn"}])
    rep = compare_results(primary, secondary)
    assert len(rep.assignee_conflicts) == 1
    assert rep.assignee_conflicts[0]["primary"] == "Lan"
    assert "nguy hiểm nhất" in rep.verdict


def test_one_side_leaving_assignee_blank_is_not_a_conflict():
    """Để trống là thận trọng, không phải sai."""
    primary = _result(actions=[{"task": "Viết tài liệu", "assignee": "Lan"}])
    secondary = _result(provider="b/1", actions=[{"task": "Viết tài liệu", "assignee": None}])
    assert compare_results(primary, secondary).assignee_conflicts == []


def test_verdict_is_positive_only_when_everything_lines_up():
    same = [{"statement": "Chốt phương án A"}]
    acts = [{"task": "Làm việc B", "assignee": "Lan", "quote_verified": True}]
    rep = compare_results(_result(decisions=same, actions=acts),
                          _result(provider="b/1", decisions=same, actions=acts))
    assert "Đạt trên mẫu này" in rep.verdict
    assert "20 cuộc họp" in rep.verdict, "phải nhắc rằng một mẫu chưa kết luận được"


def test_shadow_mode_returns_primary_result_untouched():
    """Toàn bộ lý do chế độ shadow tồn tại: mô hình phụ không đụng vào đầu ra."""
    good = ScriptedProvider(model="chinh", DistilledPoints={"points": [
        {"text": "T", "topic": "x", "evidence_segment_ids": ["s_0001"]}]},
        ExtractedDecisions={"decisions": [
            {"statement": "Quyết định thật", "quote": "Chốt là sprint sau ưu tiên sửa luồng thanh toán",
             "evidence_segment_ids": ["s_0001"]}]},
        ExtractedActions={"actions": []})
    bad = ScriptedProvider(model="phu", DistilledPoints={"points": []},
                           ExtractedDecisions={"decisions": []},
                           ExtractedActions={"actions": []})
    out = ConsensusEngine(good, bad, mode="shadow").run(TRANSCRIPT)
    assert out["mode"] == "shadow"
    assert len(out["result"]["decisions"]) == 1
    assert out["comparison"]["decisions_missed_by_secondary"] == ["Quyết định thật"]


def test_shadow_survives_a_crashing_secondary():
    class Boom(LLMProvider):
        name, model = "boom", "1"
        def generate_json(self, *a, **k):
            raise RuntimeError("mô hình cục bộ chết")

    good = ScriptedProvider(model="chinh", DistilledPoints={"points": []},
                            ExtractedDecisions={"decisions": []},
                            ExtractedActions={"actions": []})
    out = ConsensusEngine(good, Boom(), mode="shadow").run(TRANSCRIPT)
    assert out["result"] is not None, "provider phụ chết không được làm hỏng kết quả"
    assert "secondary_error" in out


def test_consensus_mode_marks_disagreement_and_lowers_confidence():
    p = ScriptedProvider(model="chinh", DistilledPoints={"points": []},
        ExtractedDecisions={"decisions": [
            {"statement": "Chỉ mô hình chính thấy", "quote": "Chốt là sprint sau ưu tiên sửa luồng thanh toán",
             "evidence_segment_ids": ["s_0001"]}]},
        ExtractedActions={"actions": []})
    q = ScriptedProvider(model="phu", DistilledPoints={"points": []},
                         ExtractedDecisions={"decisions": []},
                         ExtractedActions={"actions": []})
    out = ConsensusEngine(p, q, mode="consensus").run(TRANSCRIPT)
    assert out["result"]["decisions"][0]["agreement"] == "primary_only"
    assert out["result"]["confidence"]["consensus_penalty"] > 0
    assert out["result"]["consensus"]["secondary_provider"] == "scripted/phu"


def test_consensus_never_lets_secondary_overwrite_content():
    """Mô hình yếu hơn chỉ được bật cờ nghi ngờ, không được sửa nội dung."""
    p = ScriptedProvider(model="chinh", DistilledPoints={"points": []},
        ExtractedDecisions={"decisions": [
            {"statement": "Nội dung của mô hình chính", "quote": "Chốt là sprint sau ưu tiên sửa luồng thanh toán",
             "evidence_segment_ids": ["s_0001"]}]},
        ExtractedActions={"actions": []})
    q = ScriptedProvider(model="phu", DistilledPoints={"points": []},
        ExtractedDecisions={"decisions": [
            {"statement": "Nội dung của mô hình phụ", "quote": "x",
             "evidence_segment_ids": ["s_0002"]}]},
        ExtractedActions={"actions": []})
    out = ConsensusEngine(p, q, mode="consensus").run(TRANSCRIPT)
    statements = [d["statement"] for d in out["result"]["decisions"]]
    assert statements == ["Nội dung của mô hình chính"]


def test_engine_rejects_bad_mode_and_missing_secondary():
    p = ScriptedProvider()
    with pytest.raises(ValueError):
        ConsensusEngine(p, mode="khong-ton-tai")
    with pytest.raises(ValueError):
        ConsensusEngine(p, mode="shadow")


def test_primary_mode_makes_no_second_call():
    p = ScriptedProvider(DistilledPoints={"points": []},
                         ExtractedDecisions={"decisions": []},
                         ExtractedActions={"actions": []})
    out = ConsensusEngine(p, mode="primary").run(TRANSCRIPT)
    assert out["comparison"] is None
    assert out["mode"] == "primary" and "latency_ms" in out


# ===========================================================================
#  4 · Provider cục bộ
# ===========================================================================

def test_local_provider_parses_json_wrapped_in_code_fence():
    from providers.llm.local import _parse_json_lenient
    assert _parse_json_lenient('```json\n{"a": 1}\n```') == {"a": 1}
    assert _parse_json_lenient('Đây là kết quả:\n{"a": 2}') == {"a": 2}
    assert _parse_json_lenient('{"a": 3}') == {"a": 3}


def test_local_provider_returns_none_on_unfixable_output():
    from providers.llm.local import _parse_json_lenient
    assert _parse_json_lenient("không có json ở đây") is None
    assert _parse_json_lenient('["mảng chứ không phải object"]') is None
    assert _parse_json_lenient("") is None


def test_local_provider_rejects_unknown_dialect(monkeypatch):
    from providers.base import ProviderError
    from providers.llm.local import LocalLLMProvider
    with pytest.raises(ProviderError):
        LocalLLMProvider(dialect="sai-be-ret")


def test_local_provider_health_reports_failure_without_raising(monkeypatch):
    from providers.llm.local import LocalLLMProvider
    p = LocalLLMProvider(base_url="http://127.0.0.1:1", model="x")
    h = p.health()
    assert h["ok"] is False and "error" in h
