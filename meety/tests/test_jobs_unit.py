"""Kiểm thử tầng chạy việc nền (`server/jobs.py`) và chỗ nó nối vào pipeline.

Đây là tầng ít được soi nhất nhưng lại là chỗ ba thứ gặp nhau: HTTP, luồng
nền, và pipeline sáu pha. Bốn nhóm câu hỏi:

  1. **Ánh xạ pha.** Danh sách pha hiển thị cho người dùng có khớp với
     `STAGE_ORDER` thật của orchestrator không? Lệch một cái là thanh tiến
     trình nói dối.
  2. **Đường thất bại.** Pipeline nổ giữa chừng thì job phải báo `error` kèm
     lý do, phải bắn thông báo, và **không** được để lại biên bản dở dang.
  3. **Chọn nhà cung cấp.** Thiếu API key thì phải lùi về bản giả lập và nói
     thẳng, không được im lặng giả vờ chạy thật.
  4. **Đầu-cuối.** Nạp transcript thật, chạy hết, kiểm biên bản có dẫn chứng.

    pytest tests/test_jobs_unit.py -v
"""

from __future__ import annotations

import json
import threading
import time
from datetime import date
from pathlib import Path

import pytest

from server import jobs, security, store

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "frontend" / "src" / "mocks" / "sample_transcript.json"


@pytest.fixture()
def env(tmp_path, monkeypatch):
    store.close_all()
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "jobs.db")
    monkeypatch.setattr(jobs, "DB_PATH", tmp_path / "jobs.db")
    monkeypatch.setattr(jobs, "ARTIFACT_ROOT", tmp_path / "artifacts")
    monkeypatch.setattr(jobs, "UPLOAD_ROOT", tmp_path / "uploads")
    store.db()
    user = store.create_user(email="chu@congty.vn", display_name="Chủ Việc",
                             password_hash=security.hash_password("mat-khau-1234"))
    yield user, tmp_path
    with jobs._lock:
        jobs._jobs.clear()
    store.close_all()


def _wait(meeting_id, timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = jobs.get_job(meeting_id)
        if job and job.state in ("done", "error"):
            return job
        time.sleep(0.2)
    raise AssertionError(f"job không kết thúc sau {timeout}s")


def _copy_sample(tmp_path, name="hop.json"):
    dest = tmp_path / name
    dest.write_bytes(SAMPLE.read_bytes())
    return dest


# ===========================================================================
#  1 · Ánh xạ pha
# ===========================================================================

def test_stage_names_cover_every_orchestrator_stage():
    """Mỗi pha thật của orchestrator phải có tên tiếng Việt để hiển thị.

    Thiếu một cái thì thanh tiến trình sẽ nhảy qua nó mà không ai biết — người
    dùng thấy tiến trình đứng im rồi vọt, và tưởng hệ thống treo.
    """
    from pipeline.orchestrator import STAGE_ORDER
    for stage in STAGE_ORDER:
        key = stage.value if hasattr(stage, "value") else str(stage)
        assert key in jobs.STAGE_VI, f"pha {key} chưa có tên hiển thị"
        assert key in jobs.STAGE_COST, f"pha {key} chưa ghi chi phí quota"


def test_stage_sequence_matches_display_dicts():
    assert list(jobs.STAGE_VI) == jobs.STAGE_SEQUENCE
    assert set(jobs.STAGE_COST) == set(jobs.STAGE_VI)


def test_stage_order_puts_ingest_and_stt_first():
    """s0/s1 cố ý nằm NGOÀI orchestrator, nhưng vẫn phải hiện đầu danh sách."""
    assert jobs.STAGE_SEQUENCE[:2] == ["ingest", "stt"]
    assert jobs.STAGE_SEQUENCE[-1] == "validate"


def test_cost_labels_are_honest_about_quota():
    """Ba pha gọi mô hình đúng bằng 3 request — con số này phải khớp thực tế."""
    paid = [k for k, v in jobs.STAGE_COST.items() if "request" in v]
    assert set(paid) == {"extract", "reconcile", "compose"}
    assert jobs.STAGE_COST["stt"] == "Groq Whisper"
    free = [k for k, v in jobs.STAGE_COST.items() if v == "0 quota"]
    assert set(free) == {"ingest", "diarize", "chunk", "validate"}


def test_job_snapshot_shape(env):
    """Giao diện đọc đúng các khoá này."""
    job = jobs.Job(meeting_id="m1", user_id="u1", title="T")
    job.stages = jobs._fresh_stages()
    snap = job.snapshot()
    for key in ["meeting_id", "title", "state", "stage_index", "percent", "stages", "error"]:
        assert key in snap
    assert len(snap["stages"]) == 8
    assert all(set(s) == {"key", "name", "cost", "state"} for s in snap["stages"])


def test_percent_is_monotonic_and_bounded(env):
    job = jobs.Job(meeting_id="m1", user_id="u1", title="T")
    job.stages = jobs._fresh_stages()
    seen = []
    for key in jobs.STAGE_SEQUENCE:
        jobs._mark(job, key, "running")
        seen.append(job.snapshot()["percent"])
        jobs._mark(job, key, "done")
        seen.append(job.snapshot()["percent"])
    assert seen == sorted(seen), f"tiến độ đi lùi: {seen}"
    assert all(0 <= p <= 100 for p in seen)
    job.state = "done"
    assert job.snapshot()["percent"] == 100


def test_mark_skipped_advances_like_done(env):
    """Bỏ qua pha nhận dạng giọng nói (nguồn .vtt) không được làm kẹt tiến độ."""
    job = jobs.Job(meeting_id="m1", user_id="u1", title="T")
    job.stages = jobs._fresh_stages()
    jobs._mark(job, "ingest", "done")
    jobs._mark(job, "stt", "skipped")
    assert job.stage_index == 2


def test_mark_unknown_stage_is_ignored(env):
    job = jobs.Job(meeting_id="m1", user_id="u1", title="T")
    job.stages = jobs._fresh_stages()
    jobs._mark(job, "pha-khong-ton-tai", "done")
    assert job.stage_index == -1


# ===========================================================================
#  2 · Chọn nhà cung cấp
# ===========================================================================

def test_mock_needed_reflects_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert jobs.mock_needed() is True
    monkeypatch.setenv("GEMINI_API_KEY", "AIza-gia-lap")
    assert jobs.mock_needed() is False


def test_providers_pick_mock_when_asked():
    from providers.llm.mock import MockLLMProvider
    assert isinstance(jobs._providers(True)[0], MockLLMProvider)


def test_providers_pick_gemini_when_not_mock(monkeypatch):
    """Không ở chế độ giả lập thì phải dùng Gemini — hoặc nói rõ vì sao không thể.

    Máy chưa cài SDK là chuyện thường (dự án cố ý giữ ít phụ thuộc). Điều bắt
    buộc là thông báo phải chỉ đúng lệnh cần chạy, chứ không phải một
    ImportError trần trụi trong log của luồng nền.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "AIza-gia-lap")
    from providers.base import ProviderError
    try:
        provider = jobs._providers(False)[0]
    except ProviderError as exc:
        assert "pip install" in str(exc), f"thiếu hướng dẫn khắc phục: {exc}"
        pytest.skip("máy này chưa cài SDK Gemini")
    from providers.llm.gemini import GeminiProvider
    assert isinstance(provider, GeminiProvider)


def test_missing_sdk_surfaces_as_job_error_not_silent(env, monkeypatch):
    """Thiếu SDK giữa chừng phải thành job `error` có lý do, không treo mãi."""
    user, tmp = env
    from providers.base import ProviderError

    def no_sdk(_mock):
        raise ProviderError("Chưa cài SDK Gemini. Chạy: pip install google-genai")

    monkeypatch.setattr(jobs, "_providers", no_sdk)
    job = jobs.start_job(user_id=user["id"], source_path=_copy_sample(tmp),
                         title="Thiếu SDK", meeting_date=date(2026, 7, 22), use_mock=False)
    done = _wait(job.meeting_id, timeout=60)
    assert done.state == "error"
    assert "pip install" in done.error


# ===========================================================================
#  3 · Chạy đầu-cuối
# ===========================================================================

def test_full_run_produces_grounded_minutes(env):
    user, tmp = env
    src = _copy_sample(tmp)
    job = jobs.start_job(user_id=user["id"], source_path=src, title="Họp kiểm thử",
                         meeting_date=date(2026, 7, 22), use_mock=True)
    done = _wait(job.meeting_id)
    assert done.state == "done", done.error

    row = store.get_meeting_row(job.meeting_id)
    minutes = row["minutes"]
    assert minutes is not None
    assert minutes["meta"]["meeting_title"] == "Họp kiểm thử"
    assert row["job_state"] == "done"

    # Mọi dẫn chứng phải trỏ tới đoạn thoại CÓ THẬT — đây là lời hứa cốt lõi
    # của sản phẩm, không phải chi tiết phụ.
    seg_ids = {s["id"] for s in row["transcript"]["segments"]}
    for group in ("decisions", "action_items"):
        for item in minutes.get(group, []):
            for ev in item.get("evidence_segment_ids", []):
                assert ev in seg_ids, f"{item['id']} dẫn chứng tới đoạn không tồn tại: {ev}"


def test_owner_is_registered_at_job_start(env):
    user, tmp = env
    job = jobs.start_job(user_id=user["id"], source_path=_copy_sample(tmp),
                         title="T", meeting_date=date(2026, 7, 22), use_mock=True)
    members = store.list_members(job.meeting_id)
    assert len(members) == 1 and members[0]["role"] == "owner"
    assert members[0]["user_id"] == user["id"]
    _wait(job.meeting_id)


def test_user_title_beats_title_inside_file(env):
    """Người dùng vừa gõ tiêu đề — bỏ qua thứ họ nhập là cách khiến họ tưởng nút hỏng."""
    user, tmp = env
    embedded = json.loads(SAMPLE.read_text(encoding="utf-8"))["meta"]["title"]
    job = jobs.start_job(user_id=user["id"], source_path=_copy_sample(tmp),
                         title="Tiêu đề người dùng gõ", meeting_date=date(2026, 7, 22),
                         use_mock=True)
    _wait(job.meeting_id)
    got = store.get_meeting_row(job.meeting_id)["minutes"]["meta"]["meeting_title"]
    assert got == "Tiêu đề người dùng gõ" != embedded


def test_notification_sent_on_success(env):
    user, tmp = env
    job = jobs.start_job(user_id=user["id"], source_path=_copy_sample(tmp),
                         title="Có thông báo", meeting_date=date(2026, 7, 22), use_mock=True)
    _wait(job.meeting_id)
    titles = [n["title"] for n in store.list_notifications(user["id"])]
    assert any("sẵn sàng" in t for t in titles), titles


def test_auto_assign_runs_after_pipeline(env):
    """Người nạp trùng tên với người nhận việc → phải được gán sẵn khi mở ra."""
    user, tmp = env
    minutes = json.loads(SAMPLE.read_text(encoding="utf-8"))
    job = jobs.start_job(user_id=user["id"], source_path=_copy_sample(tmp),
                         title="Gán tự động", meeting_date=date(2026, 7, 22), use_mock=True)
    _wait(job.meeting_id)
    row = store.get_meeting_row(job.meeting_id)
    named = [t for t in row["minutes"].get("action_items", []) if t.get("assignee")]
    assignments = store.list_assignments(job.meeting_id)
    # Chỉ khẳng định khi tên người nhận trùng với tên chủ cuộc họp.
    for t in named:
        if t["assignee"].lower().split()[-1] == "việc":     # "Chủ Việc"
            assert t["id"] in assignments
            assert assignments[t["id"]]["source"] == "auto"


def test_artifacts_written_to_disk(env):
    """Artifact từng pha phải nằm trên đĩa — đó là thứ cho phép chạy lại
    mà không tốn lại quota."""
    user, tmp = env
    job = jobs.start_job(user_id=user["id"], source_path=_copy_sample(tmp),
                         title="T", meeting_date=date(2026, 7, 22), use_mock=True)
    _wait(job.meeting_id)
    files = list((tmp / "artifacts").rglob("*.json"))
    assert files, "không có artifact nào được ghi"


def test_two_jobs_can_run_at_the_same_time(env):
    user, tmp = env
    a = jobs.start_job(user_id=user["id"], source_path=_copy_sample(tmp, "a.json"),
                       title="Việc A", meeting_date=date(2026, 7, 22), use_mock=True)
    b = jobs.start_job(user_id=user["id"], source_path=_copy_sample(tmp, "b.json"),
                       title="Việc B", meeting_date=date(2026, 7, 23), use_mock=True)
    assert a.meeting_id != b.meeting_id
    ja, jb = _wait(a.meeting_id), _wait(b.meeting_id)
    assert ja.state == "done" and jb.state == "done", (ja.error, jb.error)
    assert store.get_meeting_row(a.meeting_id)["minutes"]["meta"]["meeting_title"] == "Việc A"
    assert store.get_meeting_row(b.meeting_id)["minutes"]["meta"]["meeting_title"] == "Việc B"


def test_job_registry_is_thread_safe(env):
    """Nhiều luồng cùng đọc/ghi sổ job không được làm hỏng nó."""
    errors = []

    def spam(i):
        try:
            for k in range(20):
                job = jobs.Job(meeting_id=f"m{i}_{k}", user_id="u", title="T")
                with jobs._lock:
                    jobs._jobs[job.meeting_id] = job
                jobs.get_job(f"m{i}_{k}")
        except Exception as e:                     # noqa: BLE001
            errors.append(repr(e))

    ts = [threading.Thread(target=spam, args=(i,)) for i in range(6)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=10)
    assert not errors, errors
    assert len(jobs._jobs) == 120


# ===========================================================================
#  4 · Đường thất bại
# ===========================================================================

def test_unreadable_source_marks_job_error(env):
    user, tmp = env
    bad = tmp / "hong.json"
    bad.write_text("{ đây không phải json hợp lệ", encoding="utf-8")
    job = jobs.start_job(user_id=user["id"], source_path=bad, title="Hỏng",
                         meeting_date=date(2026, 7, 22), use_mock=True)
    done = _wait(job.meeting_id, timeout=60)
    assert done.state == "error"
    assert done.error, "phải nói được vì sao hỏng"
    assert store.get_meeting_row(job.meeting_id)["job_state"] == "error"


def test_failed_job_leaves_no_half_written_minutes(env):
    """Biên bản dở dang tệ hơn không có biên bản: người đọc không biết nó thiếu."""
    user, tmp = env
    bad = tmp / "hong.vtt"
    bad.write_text("không phải vtt", encoding="utf-8")
    job = jobs.start_job(user_id=user["id"], source_path=bad, title="Hỏng",
                         meeting_date=date(2026, 7, 22), use_mock=True)
    _wait(job.meeting_id, timeout=60)
    row = store.get_meeting_row(job.meeting_id)
    assert row["minutes"] is None


def test_failed_job_notifies_user(env):
    user, tmp = env
    bad = tmp / "hong.json"
    bad.write_text("{{{", encoding="utf-8")
    job = jobs.start_job(user_id=user["id"], source_path=bad, title="Thất bại",
                         meeting_date=date(2026, 7, 22), use_mock=True)
    _wait(job.meeting_id, timeout=60)
    titles = [n["title"] for n in store.list_notifications(user["id"])]
    assert any("thất bại" in t.lower() for t in titles), titles


def test_missing_file_does_not_hang(env):
    user, tmp = env
    job = jobs.start_job(user_id=user["id"], source_path=tmp / "khong-co.vtt",
                         title="Thiếu tệp", meeting_date=date(2026, 7, 22), use_mock=True)
    done = _wait(job.meeting_id, timeout=60)
    assert done.state == "error"


def test_pipeline_failure_is_reported_not_swallowed(env, monkeypatch):
    """Orchestrator trả về thất bại → job phải chuyển sang error, không 'done'."""
    user, tmp = env

    class FakeResult:
        succeeded = False
        failed_stage = type("S", (), {"value": "extract"})()
        error = "mô phỏng lỗi ở pha trích xuất"
        minutes = None
        transcript = None

    monkeypatch.setattr(jobs, "run_pipeline", lambda *a, **k: FakeResult())
    job = jobs.start_job(user_id=user["id"], source_path=_copy_sample(tmp),
                         title="Lỗi giữa chừng", meeting_date=date(2026, 7, 22), use_mock=True)
    done = _wait(job.meeting_id, timeout=60)
    assert done.state == "error"
    assert "EXTRACT" in (done.error or "") or "extract" in (done.error or "")
    assert store.get_meeting_row(job.meeting_id)["minutes"] is None


def test_exception_inside_pipeline_becomes_error_state(env, monkeypatch):
    user, tmp = env

    def boom(*a, **k):
        raise RuntimeError("hết hạn mức Gemini")

    monkeypatch.setattr(jobs, "run_pipeline", boom)
    job = jobs.start_job(user_id=user["id"], source_path=_copy_sample(tmp),
                         title="Nổ", meeting_date=date(2026, 7, 22), use_mock=True)
    done = _wait(job.meeting_id, timeout=60)
    assert done.state == "error"
    assert "hết hạn mức" in done.error


def test_meeting_row_exists_before_pipeline_finishes(env):
    """Bản ghi phải có ngay từ đầu, để giao diện hiện được thẻ "đang xử lý"."""
    user, tmp = env
    job = jobs.start_job(user_id=user["id"], source_path=_copy_sample(tmp),
                         title="Sớm", meeting_date=date(2026, 7, 22), use_mock=True)
    row = store.get_meeting_row(job.meeting_id)
    assert row is not None
    assert row["title"] == "Sớm"
    assert row["job_state"] in ("queued", "running", "done")
    _wait(job.meeting_id)


def test_get_job_returns_none_for_unknown(env):
    assert jobs.get_job("khong-co-job-nay") is None
