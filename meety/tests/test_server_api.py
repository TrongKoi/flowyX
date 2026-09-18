"""Kiểm thử đầu-cuối cho máy chủ web.

Chạy trên ``TestClient`` của FastAPI nên không cần mở cổng thật. Mỗi lần chạy
dùng một file SQLite tạm riêng, nên không đụng vào ``data/app.db`` của bạn.

    pytest tests/test_server_api.py -v
"""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytest.importorskip("fastapi", reason="cần: pip install -r requirements.txt")
from fastapi.testclient import TestClient  # noqa: E402

from server import security, store  # noqa: E402

H = {"X-Requested-With": "Meety"}       # header chống CSRF, mọi lệnh ghi đều cần


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Máy chủ với DB tạm và thư mục tải lên tạm."""
    store.close_all()
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "test.db")

    from server import app as app_module
    monkeypatch.setattr(app_module, "UPLOAD_DIR", tmp_path / "uploads")

    from server import jobs
    monkeypatch.setattr(jobs, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(jobs, "ARTIFACT_ROOT", tmp_path / "artifacts")

    with TestClient(app_module.app) as c:
        yield c
    store.close_all()


def _register(c, email="an@congty.vn", password="mat-khau-manh-123"):
    r = c.post("/api/auth/register", headers=H, json={
        "email": email, "password": password,
        "display_name": "Nguyễn Văn An", "role_title": "Trưởng nhóm",
    })
    assert r.status_code == 201, r.text
    return r.json()


# -- Sức khoẻ -------------------------------------------------------------- #

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


# -- Đăng ký / đăng nhập --------------------------------------------------- #

def test_register_then_me(client):
    data = _register(client)
    assert data["user"]["email"] == "an@congty.vn"
    assert data["mfa_required"] is False

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["display_name"] == "Nguyễn Văn An"
    # tài khoản mới phải có sẵn 4 không gian dự án
    assert len(me.json()["workspaces"]) == 4


def test_register_rejects_duplicate_email(client):
    _register(client)
    r = client.post("/api/auth/register", headers=H, json={
        "email": "an@congty.vn", "password": "mat-khau-khac-456", "display_name": "Người khác"})
    assert r.status_code == 409


def test_register_rejects_short_password(client):
    r = client.post("/api/auth/register", headers=H, json={
        "email": "b@congty.vn", "password": "ngan", "display_name": "B"})
    assert r.status_code == 422


def test_csrf_header_required(client):
    """Thiếu header chống CSRF thì lệnh ghi phải bị chặn."""
    r = client.post("/api/auth/register", json={
        "email": "c@congty.vn", "password": "mat-khau-manh-123", "display_name": "C"})
    assert r.status_code == 403


def test_login_wrong_password(client):
    _register(client)
    client.post("/api/auth/logout", headers=H)
    r = client.post("/api/auth/login", headers=H,
                    json={"email": "an@congty.vn", "password": "sai-mat-khau"})
    assert r.status_code == 401
    # Thông báo không được tiết lộ email nào có tồn tại
    assert "mật khẩu" in r.json()["error"].lower()


def test_login_unknown_email_same_error(client):
    r = client.post("/api/auth/login", headers=H,
                    json={"email": "khongco@congty.vn", "password": "gi-do-1234"})
    assert r.status_code == 401


def test_logout_kills_session(client):
    _register(client)
    assert client.post("/api/auth/logout", headers=H).status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_anonymous_cannot_list_meetings(client):
    assert client.get("/api/meetings").status_code == 401


# -- Xác thực hai lớp ------------------------------------------------------ #

def test_full_2fa_cycle(client):
    _register(client)

    setup = client.post("/api/auth/2fa/setup", headers=H).json()
    secret = setup["secret"]
    assert setup["uri"].startswith("otpauth://totp/")

    # mã sai thì không bật được
    assert client.post("/api/auth/2fa/enable", headers=H, json={"code": "000000"}).status_code == 401

    ok = client.post("/api/auth/2fa/enable", headers=H,
                     json={"code": security.totp_now(secret)})
    assert ok.status_code == 200 and ok.json()["totp_enabled"] is True

    # đăng nhập lại: phải bị chặn ở bước 2FA
    client.post("/api/auth/logout", headers=H)
    login = client.post("/api/auth/login", headers=H,
                        json={"email": "an@congty.vn", "password": "mat-khau-manh-123"})
    assert login.json()["mfa_required"] is True

    # phiên chưa qua 2FA không được đụng vào dữ liệu
    assert client.get("/api/meetings").status_code == 403

    bad = client.post("/api/auth/2fa/verify", headers=H, json={"code": "123456"})
    assert bad.status_code == 401

    good = client.post("/api/auth/2fa/verify", headers=H,
                       json={"code": security.totp_now(secret)})
    assert good.status_code == 200
    assert client.get("/api/meetings").status_code == 200

    # tắt 2FA cũng phải nhập mã
    assert client.post("/api/auth/2fa/disable", headers=H,
                       json={"code": "000000"}).status_code == 401
    off = client.post("/api/auth/2fa/disable", headers=H,
                      json={"code": security.totp_now(secret)})
    assert off.json()["totp_enabled"] is False


def test_totp_accepts_clock_drift_one_step(client):
    secret = security.new_totp_secret()
    import time
    now = time.time()
    assert security.totp_verify(secret, security.totp_now(secret, now - 30), now)
    assert security.totp_verify(secret, security.totp_now(secret, now + 30), now)
    # lệch hai chu kỳ thì phải từ chối
    assert not security.totp_verify(secret, security.totp_now(secret, now + 90), now)


# -- Cài đặt --------------------------------------------------------------- #

def test_update_profile(client):
    _register(client)
    r = client.patch("/api/settings/profile", headers=H, json={
        "display_name": "Trần Thu Hà", "role_title": "Giám đốc sản phẩm",
        "avatar_color": "#2B4ACB"})
    assert r.status_code == 200
    assert r.json()["user"]["display_name"] == "Trần Thu Hà"
    assert r.json()["user"]["avatar_color"] == "#2B4ACB"


def test_profile_rejects_bad_color(client):
    _register(client)
    r = client.patch("/api/settings/profile", headers=H, json={"avatar_color": "xanh lá"})
    assert r.status_code == 422


def test_change_password_revokes_other_sessions(client):
    _register(client)
    # mở thêm một phiên nữa từ "thiết bị khác"
    other = TestClient(client.app)
    other.post("/api/auth/login", headers=H,
               json={"email": "an@congty.vn", "password": "mat-khau-manh-123"})
    assert other.get("/api/auth/me").status_code == 200

    bad = client.post("/api/settings/password", headers=H, json={
        "current_password": "sai", "new_password": "mat-khau-moi-789"})
    assert bad.status_code == 401

    r = client.post("/api/settings/password", headers=H, json={
        "current_password": "mat-khau-manh-123", "new_password": "mat-khau-moi-789"})
    assert r.status_code == 200 and r.json()["signed_out_sessions"] >= 1

    # phiên kia phải chết, phiên hiện tại phải sống
    assert other.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me").status_code == 200

    # mật khẩu cũ không dùng được nữa
    client.post("/api/auth/logout", headers=H)
    assert client.post("/api/auth/login", headers=H, json={
        "email": "an@congty.vn", "password": "mat-khau-manh-123"}).status_code == 401
    assert client.post("/api/auth/login", headers=H, json={
        "email": "an@congty.vn", "password": "mat-khau-moi-789"}).status_code == 200


# -- Cuộc họp -------------------------------------------------------------- #

def test_new_account_has_sample_meeting(client):
    _register(client)
    r = client.get("/api/meetings")
    assert r.status_code == 200
    meetings = r.json()["meetings"]
    assert len(meetings) >= 1
    assert meetings[0]["kind"] == "sample"
    assert meetings[0]["minutes"]["meta"]["meeting_title"]


def test_meeting_detail_and_approve(client):
    _register(client)
    mid = client.get("/api/meetings").json()["meetings"][0]["id"]

    d = client.get(f"/api/meetings/{mid}")
    assert d.status_code == 200
    assert d.json()["transcript"]["segments"]

    a = client.patch(f"/api/meetings/{mid}/status", headers=H, json={"status": "approved"})
    assert a.status_code == 200
    assert client.get(f"/api/meetings/{mid}").json()["status"] == "approved"


def test_speaker_map_roundtrip(client):
    _register(client)
    mid = client.get("/api/meetings").json()["meetings"][0]["id"]
    mapping = {"SPEAKER_00": {"name": "Bùi Quang Hùng", "role": "Giám đốc"}}
    r = client.put(f"/api/meetings/{mid}/speakers", headers=H, json={"mapping": mapping})
    assert r.status_code == 200
    assert client.get(f"/api/meetings/{mid}").json()["speaker_map"] == mapping


def test_cannot_touch_other_users_meeting(client):
    _register(client)
    mid = client.get("/api/meetings").json()["meetings"][0]["id"]
    client.post("/api/auth/logout", headers=H)
    _register(client, email="ke@khac.vn")
    assert client.get(f"/api/meetings/{mid}").status_code == 404
    assert client.patch(f"/api/meetings/{mid}/status", headers=H,
                        json={"status": "approved"}).status_code == 404


def test_upload_rejects_bad_extension(client):
    _register(client)
    r = client.post("/api/meetings/upload", headers=H,
                    files={"file": ("virus.exe", b"MZ", "application/octet-stream")})
    assert r.status_code == 415


def test_upload_rejects_empty_file(client):
    _register(client)
    r = client.post("/api/meetings/upload", headers=H,
                    files={"file": ("rong.vtt", b"", "text/vtt")})
    assert r.status_code == 400


def test_upload_runs_pipeline_end_to_end(client, monkeypatch):
    """Tải transcript mẫu lên, chờ pipeline chạy xong, kiểm biên bản có thật.

    Ép dùng bản LLM giả lập để kiểm thử không tốn quota và không cần mạng.
    """
    from server import jobs
    monkeypatch.setattr(jobs, "mock_needed", lambda: True)

    _register(client)
    source = ROOT / "frontend" / "src" / "mocks" / "sample_transcript.json"
    payload = source.read_bytes()

    r = client.post("/api/meetings/upload", headers=H,
                    files={"file": ("hop_thu_nghiem.json", payload, "application/json")},
                    data={"title": "Cuộc họp thử nghiệm", "meeting_date": "2026-07-22"})
    assert r.status_code == 202, r.text
    mid = r.json()["meeting_id"]

    import time
    for _ in range(120):                       # tối đa 60 giây
        job = client.get(f"/api/meetings/{mid}/job").json()
        if job["state"] in ("done", "error"):
            break
        time.sleep(0.5)

    assert job["state"] == "done", job.get("error")
    assert job["percent"] == 100

    detail = client.get(f"/api/meetings/{mid}").json()
    minutes = detail["minutes"]
    assert minutes is not None
    assert minutes["meta"]["meeting_title"] == "Cuộc họp thử nghiệm"
    assert "executive_summary" in minutes
    assert isinstance(minutes.get("action_items"), list)

    # xong việc thì phải có thông báo
    notifs = client.get("/api/notifications").json()
    assert any("sẵn sàng" in n["title"] for n in notifs["items"])


# -- Thông báo ------------------------------------------------------------- #

def test_notifications_crud(client):
    _register(client)
    items = client.get("/api/notifications").json()
    assert items["unread"] >= 1

    nid = items["items"][0]["id"]
    assert client.delete(f"/api/notifications/{nid}", headers=H).status_code == 200
    assert all(n["id"] != nid for n in client.get("/api/notifications").json()["items"])

    assert client.post("/api/notifications/read", headers=H).status_code == 200
    assert client.get("/api/notifications").json()["unread"] == 0

    client.delete("/api/notifications", headers=H)
    assert client.get("/api/notifications").json()["items"] == []


def test_delete_missing_notification_is_404(client):
    _register(client)
    assert client.delete("/api/notifications/khong-co", headers=H).status_code == 404


# -- Tầng bảo mật ---------------------------------------------------------- #

def test_password_hash_is_salted():
    a = security.hash_password("cung-mot-mat-khau")
    b = security.hash_password("cung-mot-mat-khau")
    assert a != b                                    # muối khác nhau mỗi lần
    assert security.verify_password("cung-mot-mat-khau", a)
    assert security.verify_password("cung-mot-mat-khau", b)
    assert not security.verify_password("khac", a)


def test_session_token_stored_hashed(client):
    _register(client)
    token = client.cookies.get("meety_session")
    rows = store.db().execute("SELECT token_hash FROM sessions").fetchall()
    assert rows
    # token thô tuyệt đối không được nằm trong DB
    assert all(r["token_hash"] != token for r in rows)
    assert any(r["token_hash"] == security.hash_token(token) for r in rows)


# ===========================================================================
#  Phân quyền Owner / Member và gán công việc
# ===========================================================================

def _owner_with_meeting(c):
    """Trả về (meeting_id, email chủ). Chủ có sẵn một biên bản mẫu."""
    _register(c, email="chu@congty.vn")
    mid = c.get("/api/meetings").json()["meetings"][0]["id"]
    return mid


def test_creator_becomes_owner(client):
    mid = _owner_with_meeting(client)
    d = client.get(f"/api/meetings/{mid}").json()
    assert d["my_role"] == "owner"
    members = d["members"]
    assert len(members) == 1
    assert members[0]["role"] == "owner"
    assert members[0]["email"] == "chu@congty.vn"


def test_invite_existing_user_grants_read_access(client):
    mid = _owner_with_meeting(client)

    guest = TestClient(client.app)
    guest.post("/api/auth/register", headers=H, json={
        "email": "khach@congty.vn", "password": "mat-khau-khach-123",
        "display_name": "Lê Thị Khách"})

    # chưa mời thì không thấy gì
    assert guest.get(f"/api/meetings/{mid}").status_code == 404

    r = client.post(f"/api/meetings/{mid}/members", headers=H,
                    json={"email": "khach@congty.vn"})
    assert r.status_code == 201
    assert len(r.json()["members"]) == 2

    # mời rồi thì đọc được, và biết mình là thành viên
    d = guest.get(f"/api/meetings/{mid}")
    assert d.status_code == 200
    assert d.json()["my_role"] == "member"
    assert d.json()["minutes"] is not None

    # cuộc họp được mời phải hiện trong danh sách của khách
    lst = guest.get("/api/meetings").json()["meetings"]
    assert any(m["id"] == mid and m["my_role"] == "member" for m in lst)


def test_member_cannot_write_anything(client):
    mid = _owner_with_meeting(client)
    guest = TestClient(client.app)
    guest.post("/api/auth/register", headers=H, json={
        "email": "khach@congty.vn", "password": "mat-khau-khach-123",
        "display_name": "Lê Thị Khách"})
    client.post(f"/api/meetings/{mid}/members", headers=H, json={"email": "khach@congty.vn"})

    assert guest.patch(f"/api/meetings/{mid}/status", headers=H,
                       json={"status": "approved"}).status_code == 403
    assert guest.put(f"/api/meetings/{mid}/speakers", headers=H,
                     json={"mapping": {}}).status_code == 403
    assert guest.delete(f"/api/meetings/{mid}", headers=H).status_code == 403
    assert guest.post(f"/api/meetings/{mid}/members", headers=H,
                      json={"email": "them@congty.vn"}).status_code == 403
    assert guest.post(f"/api/meetings/{mid}/tasks/auto-assign", headers=H).status_code == 403


def test_stranger_gets_404_not_403(client):
    """Người ngoài phải nhận 404: 403 là xác nhận cuộc họp có tồn tại."""
    mid = _owner_with_meeting(client)
    stranger = TestClient(client.app)
    stranger.post("/api/auth/register", headers=H, json={
        "email": "nguoila@congty.vn", "password": "mat-khau-la-1234",
        "display_name": "Người Lạ"})
    assert stranger.get(f"/api/meetings/{mid}").status_code == 404
    assert stranger.get(f"/api/meetings/{mid}/members").status_code == 404


def test_invite_email_without_account_then_they_register(client):
    """Mời người chưa có tài khoản — đây là trường hợp thường gặp, không phải lệ."""
    mid = _owner_with_meeting(client)
    r = client.post(f"/api/meetings/{mid}/members", headers=H,
                    json={"email": "chuacotk@congty.vn", "display_name": "Chưa Có TK"})
    assert r.status_code == 201
    pending = [m for m in r.json()["members"] if m["email"] == "chuacotk@congty.vn"][0]
    assert pending["user_id"] is None and pending["accepted"] is False

    later = TestClient(client.app)
    later.post("/api/auth/register", headers=H, json={
        "email": "chuacotk@congty.vn", "password": "mat-khau-moi-1234",
        "display_name": "Chưa Có TK"})
    # đăng ký xong là thấy ngay cuộc họp đã được mời
    assert later.get(f"/api/meetings/{mid}").status_code == 200
    assert any("được mời" in n["title"] for n in later.get("/api/notifications").json()["items"])


def test_invite_is_idempotent(client):
    mid = _owner_with_meeting(client)
    client.post(f"/api/meetings/{mid}/members", headers=H, json={"email": "a@b.vn"})
    r = client.post(f"/api/meetings/{mid}/members", headers=H, json={"email": "a@b.vn"})
    assert r.status_code == 201
    assert len([m for m in r.json()["members"] if m["email"] == "a@b.vn"]) == 1


def test_owner_cannot_be_removed(client):
    mid = _owner_with_meeting(client)
    owner_id = client.get(f"/api/meetings/{mid}").json()["members"][0]["id"]
    assert client.delete(f"/api/meetings/{mid}/members/{owner_id}",
                         headers=H).status_code == 400


def test_manual_assign_and_unassign(client):
    mid = _owner_with_meeting(client)
    inv = client.post(f"/api/meetings/{mid}/members", headers=H,
                      json={"email": "nguoinhan@congty.vn", "display_name": "Người Nhận"})
    member_id = [m for m in inv.json()["members"] if m["role"] == "member"][0]["id"]

    detail = client.get(f"/api/meetings/{mid}").json()
    task_id = detail["minutes"]["action_items"][0]["id"]

    r = client.put(f"/api/meetings/{mid}/tasks/{task_id}/assignee", headers=H,
                   json={"member_id": member_id})
    assert r.status_code == 200
    assert r.json()["assignments"][task_id]["member_id"] == member_id
    assert r.json()["assignments"][task_id]["source"] == "manual"

    # bỏ gán lại
    r = client.put(f"/api/meetings/{mid}/tasks/{task_id}/assignee", headers=H,
                   json={"member_id": None})
    assert r.json()["assignments"][task_id]["member_id"] is None


def test_assign_rejects_outsider_and_unknown_task(client):
    mid = _owner_with_meeting(client)
    task_id = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"][0]["id"]
    assert client.put(f"/api/meetings/{mid}/tasks/{task_id}/assignee", headers=H,
                      json={"member_id": "mb_khong_ton_tai"}).status_code == 400
    assert client.put(f"/api/meetings/{mid}/tasks/khong-co/assignee", headers=H,
                      json={"member_id": None}).status_code == 404


def test_assignment_does_not_mutate_minutes(client):
    """Việc gán của con người KHÔNG được ghi đè lên bằng chứng của mô hình."""
    mid = _owner_with_meeting(client)
    before = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"]
    inv = client.post(f"/api/meetings/{mid}/members", headers=H,
                      json={"email": "x@y.vn", "display_name": "X Y"})
    member_id = [m for m in inv.json()["members"] if m["role"] == "member"][0]["id"]
    client.put(f"/api/meetings/{mid}/tasks/{before[0]['id']}/assignee", headers=H,
               json={"member_id": member_id})
    after = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"]
    assert after == before


def test_auto_assign_matches_name_from_transcript(client):
    """Mời đúng người có tên trùng với người nhận việc → tự gán."""
    mid = _owner_with_meeting(client)
    tasks = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"]
    named = next((t for t in tasks if t.get("assignee")), None)
    assert named, "biên bản mẫu phải có ít nhất một việc đã có người nhận"

    r = client.post(f"/api/meetings/{mid}/members", headers=H,
                    json={"email": "trung.ten@congty.vn", "display_name": named["assignee"]})
    assert r.json()["auto_assigned"] >= 1
    assigned = r.json()["assignments"][named["id"]]
    assert assigned["source"] == "auto"


def test_auto_assign_skips_ambiguous_names(client):
    """Hai người cùng tên thì KHÔNG gán — thà để trống còn hơn gán sai người."""
    mid = _owner_with_meeting(client)
    tasks = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"]
    named = next(t for t in tasks if t.get("assignee"))

    client.post(f"/api/meetings/{mid}/members", headers=H,
                json={"email": "nguoi1@congty.vn", "display_name": named["assignee"]})
    # gỡ kết quả gán tự động vừa rồi để thử lại trong tình huống hai người trùng tên
    client.put(f"/api/meetings/{mid}/tasks/{named['id']}/assignee", headers=H,
               json={"member_id": None})
    from server import store as st
    st.db().execute("DELETE FROM task_assignments WHERE meeting_id = ?", (mid,))
    client.post(f"/api/meetings/{mid}/members", headers=H,
                json={"email": "nguoi2@congty.vn", "display_name": named["assignee"]})

    r = client.post(f"/api/meetings/{mid}/tasks/auto-assign", headers=H)
    assert named["id"] not in r.json()["assignments"]


def test_removing_member_clears_their_tasks(client):
    mid = _owner_with_meeting(client)
    inv = client.post(f"/api/meetings/{mid}/members", headers=H,
                      json={"email": "roi@congty.vn", "display_name": "Sắp Rời"})
    member_id = [m for m in inv.json()["members"] if m["role"] == "member"][0]["id"]
    task_id = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"][0]["id"]
    client.put(f"/api/meetings/{mid}/tasks/{task_id}/assignee", headers=H,
               json={"member_id": member_id})

    r = client.delete(f"/api/meetings/{mid}/members/{member_id}", headers=H)
    assert r.status_code == 200
    # việc phải quay về chưa gán, không được trỏ tới người đã rời
    assert r.json()["assignments"].get(task_id, {}).get("member_id") is None


def test_assigned_member_gets_notified(client):
    mid = _owner_with_meeting(client)
    guest = TestClient(client.app)
    guest.post("/api/auth/register", headers=H, json={
        "email": "duocgiao@congty.vn", "password": "mat-khau-giao-123",
        "display_name": "Được Giao"})
    inv = client.post(f"/api/meetings/{mid}/members", headers=H,
                      json={"email": "duocgiao@congty.vn"})
    member_id = [m for m in inv.json()["members"] if m["role"] == "member"][0]["id"]
    task_id = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"][0]["id"]
    client.put(f"/api/meetings/{mid}/tasks/{task_id}/assignee", headers=H,
               json={"member_id": member_id})
    titles = [n["title"] for n in guest.get("/api/notifications").json()["items"]]
    assert any("giao một công việc" in t for t in titles)


# ===========================================================================
#  Bài toán 3 · Trạng thái và mức ưu tiên công việc
# ===========================================================================

def _task_id(c, mid):
    return c.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"][0]["id"]


def test_task_defaults_to_todo_medium(client):
    mid = _owner_with_meeting(client)
    tid = _task_id(client, mid)
    r = client.patch(f"/api/meetings/{mid}/tasks/{tid}", headers=H, json={"status": "done"})
    assert r.status_code == 200
    rec = r.json()["assignments"][tid]
    assert rec["status"] == "done"
    assert rec["priority"] == "medium", "mặc định phải là medium, không phải None"


def test_task_status_and_priority_are_independent(client):
    mid = _owner_with_meeting(client)
    tid = _task_id(client, mid)
    client.patch(f"/api/meetings/{mid}/tasks/{tid}", headers=H, json={"priority": "high"})
    r = client.patch(f"/api/meetings/{mid}/tasks/{tid}", headers=H,
                     json={"status": "in_progress"})
    rec = r.json()["assignments"][tid]
    assert rec["priority"] == "high", "đổi trạng thái không được xoá mức ưu tiên"
    assert rec["status"] == "in_progress"


def test_task_fields_do_not_clear_assignee(client):
    mid = _owner_with_meeting(client)
    tid = _task_id(client, mid)
    inv = client.post(f"/api/meetings/{mid}/members", headers=H, json={"email": "tv@c.vn"})
    member = [m for m in inv.json()["members"] if m["role"] == "member"][0]["id"]
    client.put(f"/api/meetings/{mid}/tasks/{tid}/assignee", headers=H,
               json={"member_id": member})
    r = client.patch(f"/api/meetings/{mid}/tasks/{tid}", headers=H, json={"status": "done"})
    assert r.json()["assignments"][tid]["member_id"] == member


@pytest.mark.parametrize("body", [{"status": "DONE"}, {"status": "xong"},
                                  {"priority": "urgent"}, {"priority": "1"}])
def test_task_fields_reject_invalid_values(client, body):
    mid = _owner_with_meeting(client)
    tid = _task_id(client, mid)
    assert client.patch(f"/api/meetings/{mid}/tasks/{tid}", headers=H,
                        json=body).status_code == 422


def test_assignee_can_change_status_but_not_priority(client):
    """Người làm biết việc xong chưa; mức ưu tiên là phán đoán quản lý."""
    mid = _owner_with_meeting(client)
    tid = _task_id(client, mid)
    guest = TestClient(client.app)
    guest.post("/api/auth/register", headers=H, json={
        "email": "nguoilam@congty.vn", "password": "mat-khau-lam-2026",
        "display_name": "Người Làm"})
    inv = client.post(f"/api/meetings/{mid}/members", headers=H,
                      json={"email": "nguoilam@congty.vn"})
    member = [m for m in inv.json()["members"] if m["role"] == "member"][0]["id"]

    # chưa được giao → không đổi được gì
    assert guest.patch(f"/api/meetings/{mid}/tasks/{tid}", headers=H,
                       json={"status": "done"}).status_code == 403

    client.put(f"/api/meetings/{mid}/tasks/{tid}/assignee", headers=H,
               json={"member_id": member})
    assert guest.patch(f"/api/meetings/{mid}/tasks/{tid}", headers=H,
                       json={"status": "done"}).status_code == 200
    assert guest.patch(f"/api/meetings/{mid}/tasks/{tid}", headers=H,
                       json={"priority": "high"}).status_code == 403


def test_task_stats_counts_across_meetings(client):
    mid = _owner_with_meeting(client)
    tasks = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"]
    client.patch(f"/api/meetings/{mid}/tasks/{tasks[0]['id']}", headers=H,
                 json={"status": "done"})
    stats = client.get("/api/meetings").json()["task_stats"]
    assert stats["done"] == 1
    assert set(stats) == {"todo", "in_progress", "done"}


def test_task_fields_on_unknown_task(client):
    mid = _owner_with_meeting(client)
    assert client.patch(f"/api/meetings/{mid}/tasks/khong-co", headers=H,
                        json={"status": "done"}).status_code == 404


# ===========================================================================
#  Bài toán 8 · Phê duyệt và xuất Word
# ===========================================================================

def test_approve_records_who_and_when(client):
    mid = _owner_with_meeting(client)
    r = client.post(f"/api/meetings/{mid}/approve", headers=H, json={"approve": True})
    assert r.status_code == 200 and r.json()["status"] == "approved"
    assert r.json()["approved_by"] == "Nguyễn Văn An"
    assert r.json()["approved_at"]

    d = client.get(f"/api/meetings/{mid}").json()
    assert d["status"] == "approved" and d["approved_by"] == "Nguyễn Văn An"


def test_unapprove_clears_the_record(client):
    mid = _owner_with_meeting(client)
    client.post(f"/api/meetings/{mid}/approve", headers=H, json={"approve": True})
    r = client.post(f"/api/meetings/{mid}/approve", headers=H, json={"approve": False})
    assert r.json()["status"] == "pending"
    d = client.get(f"/api/meetings/{mid}").json()
    assert d["approved_by"] is None and d["approved_at"] is None


def test_member_cannot_approve(client):
    mid = _owner_with_meeting(client)
    guest = TestClient(client.app)
    guest.post("/api/auth/register", headers=H, json={
        "email": "tv@congty.vn", "password": "mat-khau-tv-2026", "display_name": "TV"})
    client.post(f"/api/meetings/{mid}/members", headers=H, json={"email": "tv@congty.vn"})
    assert guest.post(f"/api/meetings/{mid}/approve", headers=H,
                      json={"approve": True}).status_code == 403


def test_approval_collects_training_sample_only_when_enabled(client, tmp_path, monkeypatch):
    from ai.collector import DataCollector
    from server import app as app_module

    from ai.learning_collector import LearningCollector
    col = DataCollector(tmp_path / "train.jsonl", enabled=True)
    monkeypatch.setattr(app_module, "_collector_singleton", col)
    # Vòng lặp học dùng singleton riêng bọc quanh DataCollector — phải thay cả
    # hai, nếu không endpoint phê duyệt vẫn ghi vào tệp thật.
    monkeypatch.setattr(app_module, "_learner_singleton",
                        LearningCollector(edit_log=tmp_path / "edits.jsonl", dataset=col))

    mid = _owner_with_meeting(client)
    r = client.post(f"/api/meetings/{mid}/approve", headers=H, json={"approve": True})
    assert r.json()["training_sample"]["written"] is True
    assert (tmp_path / "train.jsonl").exists()

    # tệp phải sạch tên thật
    raw = (tmp_path / "train.jsonl").read_text(encoding="utf-8")
    assert "[NGƯỜI_" in raw


def test_export_docx_is_a_real_word_file(client):
    import io
    import zipfile

    mid = _owner_with_meeting(client)
    r = client.get(f"/api/meetings/{mid}/export.docx")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument")
    assert ".docx" in r.headers["content-disposition"]

    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert z.testzip() is None
    assert "word/document.xml" in z.namelist()
    assert "[Content_Types].xml" in z.namelist()

    import xml.dom.minidom as md
    doc = z.read("word/document.xml").decode("utf-8")
    md.parseString(doc)                       # ném lỗi nếu XML hỏng
    assert "BIÊN BẢN CUỘC HỌP" in doc
    assert "THÀNH PHẦN THAM DỰ" in doc
    assert "PHÂN CÔNG CÔNG VIỆC" in doc


def test_export_docx_shows_approval_and_assignments(client):
    import io
    import zipfile

    mid = _owner_with_meeting(client)
    tid = _task_id(client, mid)
    inv = client.post(f"/api/meetings/{mid}/members", headers=H,
                      json={"email": "nguoinhan@c.vn", "display_name": "Người Nhận Việc"})
    member = [m for m in inv.json()["members"] if m["role"] == "member"][0]["id"]
    client.put(f"/api/meetings/{mid}/tasks/{tid}/assignee", headers=H,
               json={"member_id": member})
    client.post(f"/api/meetings/{mid}/approve", headers=H, json={"approve": True})

    r = client.get(f"/api/meetings/{mid}/export.docx")
    doc = zipfile.ZipFile(io.BytesIO(r.content)).read("word/document.xml").decode("utf-8")
    assert "Người Nhận Việc" in doc, "người được gán tay phải vào bảng phân công"
    assert "ĐÃ PHÊ DUYỆT" in doc
    assert "Nguyễn Văn An" in doc


def test_export_docx_marks_unassigned_tasks_loudly(client):
    import io
    import zipfile

    mid = _owner_with_meeting(client)
    doc = zipfile.ZipFile(io.BytesIO(
        client.get(f"/api/meetings/{mid}/export.docx").content)
    ).read("word/document.xml").decode("utf-8")
    if "CHƯA PHÂN CÔNG" in doc:
        assert "chưa có người nhận" in doc, "phải có dòng cảnh báo, không chỉ ô trống"


def test_member_can_export_but_stranger_cannot(client):
    mid = _owner_with_meeting(client)
    guest = TestClient(client.app)
    guest.post("/api/auth/register", headers=H, json={
        "email": "tv@congty.vn", "password": "mat-khau-tv-2026", "display_name": "TV"})
    stranger = TestClient(client.app)
    stranger.post("/api/auth/register", headers=H, json={
        "email": "la@congty.vn", "password": "mat-khau-la-2026", "display_name": "Lạ"})
    client.post(f"/api/meetings/{mid}/members", headers=H, json={"email": "tv@congty.vn"})

    assert guest.get(f"/api/meetings/{mid}/export.docx").status_code == 200
    assert stranger.get(f"/api/meetings/{mid}/export.docx").status_code == 404


def test_export_docx_rejects_unprocessed_meeting(client):
    _register(client)
    store.create_meeting(client.get("/api/auth/me").json()["user"]["id"],
                         meeting_id="mtg_chua_xong", title="Chưa xong",
                         meeting_date="2026-08-01", minutes=None, transcript=None)
    assert client.get("/api/meetings/mtg_chua_xong/export.docx").status_code == 409


# ===========================================================================
#  Bài toán 10 · Meety Intelligence
# ===========================================================================

def test_ai_status_reports_providers_and_dataset(client):
    _register(client)
    r = client.get("/api/ai/status")
    assert r.status_code == 200
    body = r.json()
    assert set(body["providers"]) == {"gemini", "groq", "local"}
    assert "ok" in body["providers"]["local"]
    assert "samples" in body["distillation"]
    assert body["modes"] == ["primary", "shadow", "consensus"]


def test_ai_analyze_runs_agent_on_transcript(client, monkeypatch):
    from server import jobs
    monkeypatch.setattr(jobs, "mock_needed", lambda: True)
    mid = _owner_with_meeting(client)
    r = client.post(f"/api/meetings/{mid}/ai/analyze", headers=H, json={"mode": "primary"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mode"] == "primary"
    assert "confidence" in body["result"]
    assert "latency_ms" in body


def test_ai_analyze_is_owner_only(client):
    mid = _owner_with_meeting(client)
    guest = TestClient(client.app)
    guest.post("/api/auth/register", headers=H, json={
        "email": "tv@congty.vn", "password": "mat-khau-tv-2026", "display_name": "TV"})
    client.post(f"/api/meetings/{mid}/members", headers=H, json={"email": "tv@congty.vn"})
    assert guest.post(f"/api/meetings/{mid}/ai/analyze", headers=H,
                      json={"mode": "primary"}).status_code == 403


@pytest.mark.parametrize("mode", ["turbo", "", "PRIMARY"])
def test_ai_analyze_rejects_unknown_mode(client, mode):
    mid = _owner_with_meeting(client)
    assert client.post(f"/api/meetings/{mid}/ai/analyze", headers=H,
                       json={"mode": mode}).status_code == 422


def test_dataset_endpoint_is_authenticated(client):
    anon = TestClient(client.app)
    assert anon.get("/api/ai/dataset").status_code == 401
    _register(client)
    assert client.get("/api/ai/dataset").status_code == 200


# ===========================================================================
#  Hạng mục 5 · Đồng chủ toạ và chuyển quyền
# ===========================================================================

def _invite(c, mid, email="tv@congty.vn", name="Thành Viên"):
    guest = TestClient(c.app)
    guest.post("/api/auth/register", headers=H, json={
        "email": email, "password": "mat-khau-tv-2026", "display_name": name})
    inv = c.post(f"/api/meetings/{mid}/members", headers=H, json={"email": email})
    member_id = [m for m in inv.json()["members"] if m["email"] == email][0]["id"]
    return guest, member_id


def test_promote_to_co_owner_grants_admin_rights(client):
    mid = _owner_with_meeting(client)
    guest, member_id = _invite(client, mid)

    assert guest.post(f"/api/meetings/{mid}/members", headers=H,
                      json={"email": "them@c.vn"}).status_code == 403

    r = client.patch(f"/api/meetings/{mid}/members/{member_id}/role", headers=H,
                     json={"role": "co_owner"})
    assert r.status_code == 200
    assert guest.get(f"/api/meetings/{mid}").json()["my_role"] == "co_owner"

    # đủ quyền quản trị
    assert guest.post(f"/api/meetings/{mid}/members", headers=H,
                      json={"email": "them@c.vn"}).status_code == 201
    assert guest.post(f"/api/meetings/{mid}/approve", headers=H,
                      json={"approve": True}).status_code == 200
    tid = _task_id(client, mid)
    assert guest.delete(f"/api/meetings/{mid}/tasks/{tid}", headers=H).status_code == 200


def test_co_owner_cannot_transfer_ownership(client):
    """Nếu được, hai đồng chủ toạ có thể lần lượt tước quyền của nhau."""
    mid = _owner_with_meeting(client)
    guest, member_id = _invite(client, mid)
    client.patch(f"/api/meetings/{mid}/members/{member_id}/role", headers=H,
                 json={"role": "co_owner"})
    owner_mb = [m for m in client.get(f"/api/meetings/{mid}/members").json()["members"]
                if m["role"] == "owner"][0]["id"]
    assert guest.post(f"/api/meetings/{mid}/members/{owner_mb}/transfer",
                      headers=H).status_code == 403


def test_demote_co_owner_back_to_member(client):
    mid = _owner_with_meeting(client)
    guest, member_id = _invite(client, mid)
    client.patch(f"/api/meetings/{mid}/members/{member_id}/role", headers=H,
                 json={"role": "co_owner"})
    client.patch(f"/api/meetings/{mid}/members/{member_id}/role", headers=H,
                 json={"role": "member"})
    assert guest.get(f"/api/meetings/{mid}").json()["my_role"] == "member"
    assert guest.post(f"/api/meetings/{mid}/approve", headers=H,
                      json={"approve": True}).status_code == 403


def test_cannot_set_role_owner_through_role_endpoint(client):
    mid = _owner_with_meeting(client)
    _guest, member_id = _invite(client, mid)
    assert client.patch(f"/api/meetings/{mid}/members/{member_id}/role", headers=H,
                        json={"role": "owner"}).status_code == 422


def test_transfer_ownership_demotes_old_owner_to_co_owner(client):
    """Chủ cũ KHÔNG bị đẩy xuống member: người vừa bàn giao mất quyền sửa thứ
    mình tạo ra là chuyện gây hoảng, và gần như không phải ý định của ai."""
    mid = _owner_with_meeting(client)
    guest, member_id = _invite(client, mid)
    r = client.post(f"/api/meetings/{mid}/members/{member_id}/transfer", headers=H)
    assert r.status_code == 200

    assert guest.get(f"/api/meetings/{mid}").json()["my_role"] == "owner"
    assert client.get(f"/api/meetings/{mid}").json()["my_role"] == "co_owner"
    # chủ cũ vẫn quản trị được
    assert client.post(f"/api/meetings/{mid}/approve", headers=H,
                       json={"approve": True}).status_code == 200
    # nhưng không chuyển quyền lại được nữa
    owner_mb = [m for m in client.get(f"/api/meetings/{mid}/members").json()["members"]
                if m["role"] == "co_owner"][0]["id"]
    assert client.post(f"/api/meetings/{mid}/members/{owner_mb}/transfer",
                       headers=H).status_code == 403


def test_cannot_transfer_to_pending_invite(client):
    mid = _owner_with_meeting(client)
    inv = client.post(f"/api/meetings/{mid}/members", headers=H,
                      json={"email": "chuacotk@congty.vn"})
    pending = [m for m in inv.json()["members"] if m["email"] == "chuacotk@congty.vn"][0]
    assert client.post(f"/api/meetings/{mid}/members/{pending['id']}/transfer",
                       headers=H).status_code == 400


# ===========================================================================
#  Hạng mục 4 · Hạn chót, xoá việc, thêm việc thủ công
# ===========================================================================

def test_due_override_does_not_touch_minutes(client):
    mid = _owner_with_meeting(client)
    tid = _task_id(client, mid)
    before = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"]

    r = client.patch(f"/api/meetings/{mid}/tasks/{tid}/due", headers=H,
                     json={"due_date": "2026-12-31"})
    assert r.status_code == 200
    assert r.json()["assignments"][tid]["due_override"] == "2026-12-31"
    after = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"]
    assert after == before, "hạn do người sửa không được ghi đè bằng chứng của mô hình"


def test_due_can_be_cleared(client):
    mid = _owner_with_meeting(client)
    tid = _task_id(client, mid)
    client.patch(f"/api/meetings/{mid}/tasks/{tid}/due", headers=H,
                 json={"due_date": "2026-12-31"})
    r = client.patch(f"/api/meetings/{mid}/tasks/{tid}/due", headers=H, json={"due_date": None})
    assert r.json()["assignments"][tid]["due_override"] is None


@pytest.mark.parametrize("bad", ["31/12/2026", "2026-13-01", "hôm nay", "20261231"])
def test_due_rejects_bad_format(client, bad):
    mid = _owner_with_meeting(client)
    tid = _task_id(client, mid)
    assert client.patch(f"/api/meetings/{mid}/tasks/{tid}/due", headers=H,
                        json={"due_date": bad}).status_code == 422


def test_assignee_can_edit_own_due_but_not_others(client):
    mid = _owner_with_meeting(client)
    tid = _task_id(client, mid)
    guest, member_id = _invite(client, mid)
    assert guest.patch(f"/api/meetings/{mid}/tasks/{tid}/due", headers=H,
                       json={"due_date": "2026-12-31"}).status_code == 403
    client.put(f"/api/meetings/{mid}/tasks/{tid}/assignee", headers=H,
               json={"member_id": member_id})
    assert guest.patch(f"/api/meetings/{mid}/tasks/{tid}/due", headers=H,
                       json={"due_date": "2026-12-31"}).status_code == 200


def test_delete_task_is_soft_and_reversible(client):
    mid = _owner_with_meeting(client)
    tid = _task_id(client, mid)
    r = client.delete(f"/api/meetings/{mid}/tasks/{tid}", headers=H)
    assert r.status_code == 200
    assert r.json()["assignments"][tid]["deleted"] is True
    # biên bản gốc vẫn còn việc đó — xoá cứng là mất dấu vết mô hình bắt nhầm
    assert any(t["id"] == tid
               for t in client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"])
    r = client.post(f"/api/meetings/{mid}/tasks/{tid}/restore", headers=H)
    assert r.json()["assignments"][tid]["deleted"] is False


def test_member_cannot_delete_task(client):
    mid = _owner_with_meeting(client)
    tid = _task_id(client, mid)
    guest, _ = _invite(client, mid)
    assert guest.delete(f"/api/meetings/{mid}/tasks/{tid}", headers=H).status_code == 403


def test_manual_task_needs_no_evidence(client):
    mid = _owner_with_meeting(client)
    r = client.post(f"/api/meetings/{mid}/tasks", headers=H, json={
        "task": "Gửi báo giá cho khách hàng A", "due_date": "2026-09-01",
        "priority": "high"})
    assert r.status_code == 201
    tid = r.json()["task_id"]
    assert tid.startswith("mt_"), "id phải phân biệt được với việc do mô hình rút ra"

    tasks = r.json()["manual_tasks"]
    added = [t for t in tasks if t["id"] == tid][0]
    assert added["task"] == "Gửi báo giá cho khách hàng A"
    assert added["evidence_segment_ids"] == []
    assert added["due_date"] == "2026-09-01"
    assert r.json()["assignments"][tid]["priority"] == "high"


def test_manual_task_appears_in_detail_and_can_be_deleted(client):
    mid = _owner_with_meeting(client)
    tid = client.post(f"/api/meetings/{mid}/tasks", headers=H,
                      json={"task": "Việc thêm tay"}).json()["task_id"]
    d = client.get(f"/api/meetings/{mid}").json()
    assert any(t["id"] == tid for t in d["manual_tasks"])
    client.delete(f"/api/meetings/{mid}/tasks/{tid}", headers=H)
    assert not any(t["id"] == tid
                   for t in client.get(f"/api/meetings/{mid}").json()["manual_tasks"])


def test_manual_task_rejects_outsider_assignee(client):
    mid = _owner_with_meeting(client)
    assert client.post(f"/api/meetings/{mid}/tasks", headers=H, json={
        "task": "X", "member_id": "mb_khong_ton_tai"}).status_code == 400


def test_manual_task_notifies_assignee(client):
    mid = _owner_with_meeting(client)
    guest, member_id = _invite(client, mid)
    client.post(f"/api/meetings/{mid}/tasks", headers=H,
                json={"task": "Việc giao tay", "member_id": member_id})
    titles = [n["title"] for n in guest.get("/api/notifications").json()["items"]]
    assert any("giao một công việc" in t for t in titles)


def test_member_only_sees_tasks_assigned_to_them(client):
    """Lọc ở tầng giao diện, nhưng API phải trả đủ để giao diện lọc được."""
    mid = _owner_with_meeting(client)
    guest, member_id = _invite(client, mid)
    tid = _task_id(client, mid)
    client.put(f"/api/meetings/{mid}/tasks/{tid}/assignee", headers=H,
               json={"member_id": member_id})
    d = guest.get(f"/api/meetings/{mid}").json()
    assert d["assignments"][tid]["member_id"] == member_id


# ===========================================================================
#  Hạng mục 8 · Phát lại ghi âm
# ===========================================================================

def test_audio_info_reports_absence_clearly(client):
    mid = _owner_with_meeting(client)
    r = client.get(f"/api/meetings/{mid}/audio/info")
    assert r.status_code == 200
    assert r.json()["available"] is False
    assert "bản thoại" in r.json()["reason"], "phải nói VÌ SAO, không chỉ nói không có"


def test_audio_404_when_no_file(client):
    mid = _owner_with_meeting(client)
    assert client.get(f"/api/meetings/{mid}/audio").status_code == 404


def test_audio_range_requests(client, tmp_path):
    """Tua được là nhờ 206 Partial Content. Không có nó, kéo thanh trượt về
    giữa bài thì trình duyệt phát lại từ đầu."""
    mid = _owner_with_meeting(client)
    audio = tmp_path / "uploads" / "hop.mp3"
    audio.parent.mkdir(parents=True, exist_ok=True)
    payload = bytes(range(256)) * 40          # 10 240 byte
    audio.write_bytes(payload)
    store.set_audio_path(mid, str(audio))

    full = client.get(f"/api/meetings/{mid}/audio")
    assert full.status_code == 200
    assert full.headers["accept-ranges"] == "bytes"
    assert full.headers["content-type"] == "audio/mpeg"
    assert full.content == payload

    part = client.get(f"/api/meetings/{mid}/audio", headers={"Range": "bytes=100-199"})
    assert part.status_code == 206
    assert part.headers["content-range"] == f"bytes 100-199/{len(payload)}"
    assert part.content == payload[100:200]

    # `bytes=-N` nghĩa là N byte CUỐI — hiểu nhầm chỗ này làm hỏng việc dò
    # metadata ở cuối tệp .mp4, và đó là lúc trình duyệt báo duration Infinity.
    tail = client.get(f"/api/meetings/{mid}/audio", headers={"Range": "bytes=-50"})
    assert tail.status_code == 206
    assert tail.content == payload[-50:]

    openended = client.get(f"/api/meetings/{mid}/audio", headers={"Range": "bytes=10000-"})
    assert openended.status_code == 206
    assert openended.content == payload[10000:]

    bad = client.get(f"/api/meetings/{mid}/audio", headers={"Range": "bytes=999999-"})
    assert bad.status_code == 416
    assert bad.headers["content-range"] == f"bytes */{len(payload)}"


def test_audio_permission_and_path_guard(client, tmp_path):
    mid = _owner_with_meeting(client)
    audio = tmp_path / "uploads" / "hop.mp3"
    audio.parent.mkdir(parents=True, exist_ok=True)
    audio.write_bytes(b"x" * 1000)
    store.set_audio_path(mid, str(audio))

    guest, _ = _invite(client, mid)
    assert guest.get(f"/api/meetings/{mid}/audio").status_code == 200

    stranger = TestClient(client.app)
    stranger.post("/api/auth/register", headers=H, json={
        "email": "la@congty.vn", "password": "mat-khau-la-2026", "display_name": "Lạ"})
    assert stranger.get(f"/api/meetings/{mid}/audio").status_code == 404

    # đường dẫn thoát khỏi thư mục cho phép phải bị chặn, kể cả khi nằm trong DB
    store.set_audio_path(mid, "../../etc/passwd")
    assert client.get(f"/api/meetings/{mid}/audio").status_code == 404


# ===========================================================================
#  Ma trận phân quyền 3 tầng  (Bài toán 3)
# ===========================================================================

def test_permission_matrix_is_exhaustive():
    """Mọi hành động xuất hiện ở bất kỳ vai trò nào đều phải có thông báo lỗi.

    Thiếu thông báo thì người dùng nhận câu mặc định "bạn không có quyền" —
    câu đó buộc họ đi hỏi mới biết mình thiếu gì.
    """
    from server.store import PERMISSIONS, PERMISSION_MESSAGES
    every = set().union(*PERMISSIONS.values())
    missing = every - set(PERMISSION_MESSAGES) - {"update_own_status"}
    assert not missing, f"thiếu thông báo cho: {missing}"


def test_role_hierarchy_is_strictly_nested_except_promote():
    """Co-host phải là tập con của owner. Member là tập con của co-host."""
    from server.store import PERMISSIONS
    assert PERMISSIONS["co_owner"] < PERMISSIONS["owner"]
    assert PERMISSIONS["member"] < PERMISSIONS["co_owner"]


def test_co_host_cannot_escalate_or_shrink_others():
    """Ba điều co-host tuyệt đối không được làm."""
    from server.store import has_permission
    for action in ("transfer_ownership", "demote_co_host", "remove_member"):
        assert not has_permission("co_owner", action), action
    assert has_permission("co_owner", "promote_co_host"), (
        "mở rộng thì được — thêm co-host không tạo ra cuộc đua nào")


def _three_tier(client):
    """Dựng sẵn: owner + co-host + member trên cùng một cuộc họp."""
    mid = _owner_with_meeting(client)
    co, co_id = _invite(client, mid, "cohost@congty.vn", "Đồng Chủ Toạ")
    mem, mem_id = _invite(client, mid, "thanhvien@congty.vn", "Thành Viên")
    client.patch(f"/api/meetings/{mid}/members/{co_id}/role", headers=H,
                 json={"role": "co_owner"})
    return mid, co, co_id, mem, mem_id


def test_co_host_cannot_demote_another_co_host(client):
    """Nếu được, hai co-host bãi nhiệm lẫn nhau và ai bấm trước thì thắng."""
    mid, co, _co_id, _mem, mem_id = _three_tier(client)
    _co2, co2_id = _invite(client, mid, "cohost2@congty.vn", "Đồng Chủ Toạ 2")
    client.patch(f"/api/meetings/{mid}/members/{co2_id}/role", headers=H,
                 json={"role": "co_owner"})

    r = co.patch(f"/api/meetings/{mid}/members/{co2_id}/role", headers=H,
                 json={"role": "member"})
    assert r.status_code == 403
    assert "chủ toạ" in r.json()["error"].lower()
    # vai trò không đổi
    roles = {m["id"]: m["role"] for m in client.get(
        f"/api/meetings/{mid}/members").json()["members"]}
    assert roles[co2_id] == "co_owner"


def test_co_host_cannot_remove_anyone(client):
    mid, co, _co_id, _mem, mem_id = _three_tier(client)
    assert co.delete(f"/api/meetings/{mid}/members/{mem_id}",
                     headers=H).status_code == 403
    assert len(client.get(f"/api/meetings/{mid}/members").json()["members"]) == 3


def test_co_host_can_promote_another_member(client):
    mid, co, _co_id, _mem, mem_id = _three_tier(client)
    r = co.patch(f"/api/meetings/{mid}/members/{mem_id}/role", headers=H,
                 json={"role": "co_owner"})
    assert r.status_code == 200
    roles = {m["id"]: m["role"] for m in r.json()["members"]}
    assert roles[mem_id] == "co_owner"


def test_co_host_keeps_task_and_approval_rights(client):
    mid, co, _co_id, _mem, mem_id = _three_tier(client)
    tid = _task_id(client, mid)
    assert co.put(f"/api/meetings/{mid}/tasks/{tid}/assignee", headers=H,
                  json={"member_id": mem_id}).status_code == 200
    assert co.post(f"/api/meetings/{mid}/approve", headers=H,
                   json={"approve": True}).status_code == 200
    assert co.post(f"/api/meetings/{mid}/tasks", headers=H,
                   json={"task": "Việc do đồng chủ toạ thêm"}).status_code == 201
    assert co.delete(f"/api/meetings/{mid}/tasks/{tid}", headers=H).status_code == 200


def test_member_has_no_permission_button_at_all(client):
    mid, _co, co_id, mem, mem_id = _three_tier(client)
    for method, path, body in [
        ("patch", f"/api/meetings/{mid}/members/{co_id}/role", {"role": "member"}),
        ("post", f"/api/meetings/{mid}/members/{co_id}/transfer", None),
        ("delete", f"/api/meetings/{mid}/members/{co_id}", None),
        ("post", f"/api/meetings/{mid}/members", {"email": "x@y.vn"}),
    ]:
        r = (getattr(mem, method)(path, headers=H, json=body) if body
             else getattr(mem, method)(path, headers=H))
        assert r.status_code == 403, f"{method} {path} → {r.status_code}"


def test_detail_returns_permission_list_per_role(client):
    """Frontend đọc danh sách này thay vì tự suy từ tên vai trò."""
    mid, co, _co_id, mem, _mem_id = _three_tier(client)
    owner_perms = set(client.get(f"/api/meetings/{mid}").json()["permissions"])
    co_perms = set(co.get(f"/api/meetings/{mid}").json()["permissions"])
    mem_perms = set(mem.get(f"/api/meetings/{mid}").json()["permissions"])

    assert "transfer_ownership" in owner_perms
    assert "transfer_ownership" not in co_perms
    assert "demote_co_host" not in co_perms
    assert "promote_co_host" in co_perms
    assert mem_perms == {"update_own_status"}


def test_error_message_names_who_can_do_it(client):
    mid, co, _co_id, _mem, _mem_id = _three_tier(client)
    owner_mb = [m for m in client.get(f"/api/meetings/{mid}/members").json()["members"]
                if m["role"] == "owner"][0]["id"]
    r = co.post(f"/api/meetings/{mid}/members/{owner_mb}/transfer", headers=H)
    assert r.status_code == 403
    assert "Chỉ chủ toạ" in r.json()["error"], "phải nói AI làm được, không nói suông"


# ===========================================================================
#  Đồng bộ gán việc giữa hai tài khoản  (Bài toán 4)
# ===========================================================================

def test_assign_returns_200_and_persists_immediately(client):
    """Triệu chứng cũ: báo lỗi quyền nhưng dữ liệu vẫn lưu. Phải là 200 + lưu."""
    mid = _owner_with_meeting(client)
    guest, member_id = _invite(client, mid)
    tid = _task_id(client, mid)

    r = client.put(f"/api/meetings/{mid}/tasks/{tid}/assignee", headers=H,
                   json={"member_id": member_id})
    assert r.status_code == 200
    assert r.json()["assignments"][tid]["member_id"] == member_id
    # đọc lại từ máy chủ bằng phiên KHÁC — không dựa vào state của người gán
    assert guest.get(f"/api/meetings/{mid}").json()["assignments"][tid]["member_id"] == member_id


def test_member_sees_task_assigned_to_them_right_away(client):
    """Triệu chứng cũ: bên Member hoàn toàn không thấy task nào."""
    mid = _owner_with_meeting(client)
    guest, member_id = _invite(client, mid)
    tid = _task_id(client, mid)
    client.put(f"/api/meetings/{mid}/tasks/{tid}/assignee", headers=H,
               json={"member_id": member_id})

    d = guest.get(f"/api/meetings/{mid}").json()
    mine = [m for m in d["members"] if m["email"] == "tv@congty.vn"][0]
    assert mine["id"] == member_id, "id thành viên phải khớp giữa hai phiên"
    assigned = [t for t, a in d["assignments"].items() if a["member_id"] == mine["id"]]
    assert tid in assigned


def test_member_id_is_stable_across_sessions(client):
    """Sai lệch id giữa hai phiên là nguồn của lỗi 'member không thấy task'."""
    mid = _owner_with_meeting(client)
    guest, member_id = _invite(client, mid)
    from_owner = [m for m in client.get(f"/api/meetings/{mid}/members").json()["members"]
                  if m["email"] == "tv@congty.vn"][0]["id"]
    from_member = [m for m in guest.get(f"/api/meetings/{mid}/members").json()["members"]
                   if m["email"] == "tv@congty.vn"][0]["id"]
    assert from_owner == from_member == member_id


def test_manual_task_assigned_to_member_is_visible_to_them(client):
    mid = _owner_with_meeting(client)
    guest, member_id = _invite(client, mid)
    r = client.post(f"/api/meetings/{mid}/tasks", headers=H,
                    json={"task": "Việc giao riêng", "member_id": member_id})
    tid = r.json()["task_id"]
    d = guest.get(f"/api/meetings/{mid}").json()
    assert any(t["id"] == tid for t in d["manual_tasks"])
    assert d["assignments"][tid]["member_id"] == member_id


def test_member_can_update_own_task_status_only(client):
    mid = _owner_with_meeting(client)
    guest, member_id = _invite(client, mid)
    tasks = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"]
    mine_id, other_id = tasks[0]["id"], tasks[1]["id"]
    client.put(f"/api/meetings/{mid}/tasks/{mine_id}/assignee", headers=H,
               json={"member_id": member_id})

    assert guest.patch(f"/api/meetings/{mid}/tasks/{mine_id}", headers=H,
                       json={"status": "in_progress"}).status_code == 200
    assert guest.patch(f"/api/meetings/{mid}/tasks/{mine_id}", headers=H,
                       json={"status": "done"}).status_code == 200
    assert guest.patch(f"/api/meetings/{mid}/tasks/{other_id}", headers=H,
                       json={"status": "done"}).status_code == 403
    assert guest.patch(f"/api/meetings/{mid}/tasks/{mine_id}", headers=H,
                       json={"priority": "high"}).status_code == 403
