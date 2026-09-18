"""Kiểm thử validate đầu vào, giá trị biên và hợp đồng HTTP.

Ba câu hỏi ở đây, khác hẳn với bộ bảo mật:

  1. Dữ liệu **sai kiểu hoặc sai định dạng** có bị chặn ở đúng tầng không, và
     trả 422 chứ không phải 500?
  2. Giá trị **ngay sát biên** (dài đúng giới hạn, dài hơn một ký tự, rỗng,
     bằng 0) xử lý ra sao?
  3. Máy chủ có giữ đúng **hợp đồng HTTP** không: mã trạng thái, phương thức
     không hỗ trợ, đường dẫn lạ, JSON hỏng?

Một API trả 500 cho đầu vào rác không chỉ xấu — nó nói cho người dò biết chỗ
nào chưa được kiểm, và log đầy stack trace thật.

    pytest tests/test_api_validation.py -v
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("fastapi", reason="cần: pip install -r requirements.txt")
from fastapi.testclient import TestClient  # noqa: E402

from server import security, store  # noqa: E402

H = {"X-Requested-With": "Meety"}
PW = "mat-khau-manh-2026"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store.close_all()
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "val.db")
    from server import app as app_module
    monkeypatch.setattr(app_module, "UPLOAD_DIR", tmp_path / "uploads")
    from server import jobs
    monkeypatch.setattr(jobs, "DB_PATH", tmp_path / "val.db")
    monkeypatch.setattr(jobs, "ARTIFACT_ROOT", tmp_path / "artifacts")
    monkeypatch.setattr(jobs, "mock_needed", lambda: True)
    with TestClient(app_module.app) as c:
        yield c
    store.close_all()


def _reg(c, email="a@congty.vn"):
    return c.post("/api/auth/register", headers=H,
                  json={"email": email, "password": PW, "display_name": "Người Dùng"})


def _mid(c):
    return c.get("/api/meetings").json()["meetings"][0]["id"]


# ===========================================================================
#  Đăng ký — email và mật khẩu
# ===========================================================================

@pytest.mark.parametrize("email", [
    "khong-co-a-cong", "@thieu-ten.vn", "ten@", "ten@@hai-cong.vn",
    "ten cach@congty.vn", "", "   ", "ten@khong-co-cham",
    "a" * 300 + "@congty.vn",
])
def test_register_rejects_malformed_email(client, email):
    r = client.post("/api/auth/register", headers=H,
                    json={"email": email, "password": PW, "display_name": "X"})
    assert r.status_code == 422, f"{email!r} lọt qua"


@pytest.mark.parametrize("email", [
    "ten.co.cham@congty.vn", "ten+nhan@congty.vn", "ten_gach@con-gty.vn",
    "so123@congty.com.vn", "A@b.vn",
])
def test_register_accepts_valid_email_shapes(client, email):
    r = client.post("/api/auth/register", headers=H,
                    json={"email": email, "password": PW, "display_name": "X"})
    assert r.status_code == 201, f"{email!r} bị chặn oan: {r.text}"
    client.post("/api/auth/logout", headers=H)


def test_password_length_boundaries(client):
    """8 ký tự phải qua, 7 phải trượt — kiểm đúng ở biên chứ không quanh biên."""
    assert client.post("/api/auth/register", headers=H, json={
        "email": "bay@congty.vn", "password": "1234567", "display_name": "X"}
    ).status_code == 422
    assert client.post("/api/auth/register", headers=H, json={
        "email": "tam@congty.vn", "password": "12345678", "display_name": "X"}
    ).status_code == 201


def test_password_upper_boundary(client):
    assert client.post("/api/auth/register", headers=H, json={
        "email": "dai@congty.vn", "password": "x" * 200, "display_name": "X"}
    ).status_code == 201
    assert client.post("/api/auth/register", headers=H, json={
        "email": "quadai@congty.vn", "password": "x" * 201, "display_name": "X"}
    ).status_code == 422


def test_display_name_boundaries(client):
    assert client.post("/api/auth/register", headers=H, json={
        "email": "a@congty.vn", "password": PW, "display_name": "N" * 80}
    ).status_code == 201
    assert client.post("/api/auth/register", headers=H, json={
        "email": "b@congty.vn", "password": PW, "display_name": "N" * 81}
    ).status_code == 422
    assert client.post("/api/auth/register", headers=H, json={
        "email": "c@congty.vn", "password": PW, "display_name": ""}
    ).status_code == 422


def test_missing_required_fields(client):
    for body in [{}, {"email": "a@b.vn"}, {"password": PW},
                 {"email": "a@b.vn", "password": PW}]:
        r = client.post("/api/auth/register", headers=H, json=body)
        assert r.status_code == 422, body


def test_wrong_types_rejected(client):
    for body in [
        {"email": 123, "password": PW, "display_name": "X"},
        {"email": "a@b.vn", "password": ["danh", "sach"], "display_name": "X"},
        {"email": "a@b.vn", "password": PW, "display_name": {"khoa": "gia tri"}},
        {"email": None, "password": PW, "display_name": "X"},
    ]:
        assert client.post("/api/auth/register", headers=H, json=body).status_code == 422


def test_extra_fields_are_ignored_not_fatal(client):
    r = client.post("/api/auth/register", headers=H, json={
        "email": "a@congty.vn", "password": PW, "display_name": "X",
        "truong_la": "gia tri", "is_admin": True})
    assert r.status_code == 201
    assert "truong_la" not in r.json()["user"]


def test_broken_json_body(client):
    r = client.post("/api/auth/register", headers={**H, "Content-Type": "application/json"},
                    content="{khong phai json")
    assert r.status_code == 422


def test_empty_body_where_json_required(client):
    r = client.post("/api/auth/register", headers={**H, "Content-Type": "application/json"},
                    content="")
    assert r.status_code == 422


# ===========================================================================
#  Cài đặt cá nhân
# ===========================================================================

@pytest.mark.parametrize("color", ["xanh", "#GGG", "#12345", "#1234567",
                                   "rgb(1,2,3)", "", "#12 34 56"])
def test_avatar_color_must_be_hex(client, color):
    _reg(client)
    assert client.patch("/api/settings/profile", headers=H,
                        json={"avatar_color": color}).status_code == 422


@pytest.mark.parametrize("color", ["#12735B", "#abcdef", "#ABCDEF", "#000000", "#FfFfFf"])
def test_avatar_color_accepts_valid_hex(client, color):
    _reg(client)
    r = client.patch("/api/settings/profile", headers=H, json={"avatar_color": color})
    assert r.status_code == 200 and r.json()["user"]["avatar_color"] == color


def test_profile_partial_update_leaves_others_alone(client):
    _reg(client)
    client.patch("/api/settings/profile", headers=H,
                 json={"display_name": "Tên A", "role_title": "Chức A"})
    client.patch("/api/settings/profile", headers=H, json={"display_name": "Tên B"})
    me = client.get("/api/auth/me").json()["user"]
    assert me["display_name"] == "Tên B" and me["role_title"] == "Chức A"


def test_empty_patch_is_a_no_op_not_an_error(client):
    _reg(client)
    before = client.get("/api/auth/me").json()["user"]
    assert client.patch("/api/settings/profile", headers=H, json={}).status_code == 200
    assert client.get("/api/auth/me").json()["user"] == before


def test_prefs_merge_instead_of_replace(client):
    """Ghi đè cả khối `prefs` sẽ xoá mất tuỳ chọn mà client không gửi lần này."""
    _reg(client)
    client.patch("/api/settings/profile", headers=H, json={"prefs": {"co_chu": "lon"}})
    client.patch("/api/settings/profile", headers=H, json={"prefs": {"gom_nhom": "kind"}})
    prefs = client.get("/api/auth/me").json()["user"]["prefs"]
    assert prefs == {"co_chu": "lon", "gom_nhom": "kind"}


def test_new_password_length_enforced(client):
    _reg(client)
    r = client.post("/api/settings/password", headers=H,
                    json={"current_password": PW, "new_password": "ngan"})
    assert r.status_code == 422


def test_password_change_to_same_value_still_works(client):
    """Không cấm — nhưng phải đá các phiên khác đúng như mọi lần đổi."""
    _reg(client)
    other = TestClient(client.app)
    other.post("/api/auth/login", headers=H, json={"email": "a@congty.vn", "password": PW})
    r = client.post("/api/settings/password", headers=H,
                    json={"current_password": PW, "new_password": PW})
    assert r.status_code == 200
    assert other.get("/api/auth/me").status_code == 401


# ===========================================================================
#  Cuộc họp và trạng thái
# ===========================================================================

@pytest.mark.parametrize("status", ["APPROVED", "duyet", "", "done", "approved ", "1"])
def test_meeting_status_enum_enforced(client, status):
    _reg(client)
    mid = _mid(client)
    assert client.patch(f"/api/meetings/{mid}/status", headers=H,
                        json={"status": status}).status_code == 422


def test_meeting_status_accepts_both_valid_values(client):
    _reg(client)
    mid = _mid(client)
    for s in ["approved", "pending", "approved"]:
        assert client.patch(f"/api/meetings/{mid}/status", headers=H,
                            json={"status": s}).status_code == 200
        assert client.get(f"/api/meetings/{mid}").json()["status"] == s


def test_speaker_map_accepts_empty_and_nested_null(client):
    _reg(client)
    mid = _mid(client)
    assert client.put(f"/api/meetings/{mid}/speakers", headers=H,
                      json={"mapping": {}}).status_code == 200
    assert client.put(f"/api/meetings/{mid}/speakers", headers=H,
                      json={"mapping": {"SPEAKER_00": {"name": "A", "role": None}}}
                      ).status_code == 200


def test_speaker_map_rejects_wrong_shape(client):
    _reg(client)
    mid = _mid(client)
    for bad in [{"mapping": "chuoi"}, {"mapping": ["danh", "sach"]},
                {"mapping": {"S0": "khong-phai-dict"}}, {}]:
        assert client.put(f"/api/meetings/{mid}/speakers", headers=H,
                          json=bad).status_code == 422, bad


def test_invite_rejects_malformed_email(client):
    _reg(client)
    mid = _mid(client)
    for bad in ["khong-hop-le", "", "@x.vn", "a@b"]:
        assert client.post(f"/api/meetings/{mid}/members", headers=H,
                           json={"email": bad}).status_code == 422, bad


def test_assign_body_accepts_explicit_null(client):
    """`member_id: null` là "cố ý bỏ trống", khác với "thiếu trường"."""
    _reg(client)
    mid = _mid(client)
    task = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"][0]["id"]
    assert client.put(f"/api/meetings/{mid}/tasks/{task}/assignee", headers=H,
                      json={"member_id": None}).status_code == 200
    assert client.put(f"/api/meetings/{mid}/tasks/{task}/assignee", headers=H,
                      json={}).status_code == 200


# ===========================================================================
#  Tải tệp lên
# ===========================================================================

@pytest.mark.parametrize("name", ["a.exe", "a.zip", "a.docx", "a", "a.mp3.exe", "a.MP33"])
def test_upload_rejects_unsupported_extension(client, name):
    _reg(client)
    r = client.post("/api/meetings/upload", headers=H,
                    files={"file": (name, b"noi dung", "application/octet-stream")})
    assert r.status_code == 415, name


@pytest.mark.parametrize("name", ["a.vtt", "a.VTT", "a.Srt", "a.mp3", "a.M4A", "a.json", "a.txt"])
def test_upload_extension_check_is_case_insensitive(client, name):
    _reg(client)
    r = client.post("/api/meetings/upload", headers=H,
                    files={"file": (name, b"WEBVTT\n", "text/plain")},
                    data={"meeting_date": "2026-08-01"})
    assert r.status_code == 202, f"{name} → {r.status_code}: {r.text[:120]}"


def test_upload_rejects_empty_file(client):
    _reg(client)
    r = client.post("/api/meetings/upload", headers=H,
                    files={"file": ("rong.vtt", b"", "text/vtt")})
    assert r.status_code == 400
    from server import app as app_module
    assert not list(app_module.UPLOAD_DIR.glob("*")), "tệp rỗng vẫn bị ghi xuống đĩa"


@pytest.mark.parametrize("date", ["01-08-2026", "2026/08/01", "hôm nay",
                                  "2026-13-01", "2026-08-32", "20260801",
                                  "2026-W31-1", "2026-8-1", " 2026-08-01x"])
def test_upload_rejects_bad_date(client, date):
    _reg(client)
    r = client.post("/api/meetings/upload", headers=H,
                    files={"file": ("a.vtt", b"WEBVTT\n", "text/vtt")},
                    data={"meeting_date": date})
    assert r.status_code == 400, date


def test_upload_defaults_to_today_when_date_missing(client):
    from datetime import date as d
    _reg(client)
    r = client.post("/api/meetings/upload", headers=H,
                    files={"file": ("a.vtt", b"WEBVTT\n", "text/vtt")})
    assert r.status_code == 202
    mid = r.json()["meeting_id"]
    assert client.get(f"/api/meetings/{mid}").json()["date"] == d.today().isoformat()


def test_upload_title_defaults_to_filename(client):
    _reg(client)
    r = client.post("/api/meetings/upload", headers=H,
                    files={"file": ("hop_ban_giao.vtt", b"WEBVTT\n", "text/vtt")},
                    data={"meeting_date": "2026-08-01"})
    mid = r.json()["meeting_id"]
    assert "hop ban giao" in client.get(f"/api/meetings/{mid}").json()["title"]


def test_upload_size_limit_enforced(client, monkeypatch):
    from server import app as app_module
    monkeypatch.setattr(app_module, "MAX_UPLOAD_MB", 1)
    _reg(client)
    r = client.post("/api/meetings/upload", headers=H,
                    files={"file": ("to.vtt", b"x" * (2 * 1024 * 1024), "text/vtt")})
    assert r.status_code == 413
    assert not list(app_module.UPLOAD_DIR.glob("*")), "tệp quá cỡ vẫn nằm lại trên đĩa"


def test_upload_without_file_part(client):
    _reg(client)
    assert client.post("/api/meetings/upload", headers=H,
                       data={"title": "T"}).status_code == 422


# ===========================================================================
#  Hợp đồng HTTP
# ===========================================================================

def test_unknown_route_returns_404_json(client):
    r = client.get("/api/khong-co-duong-nay")
    assert r.status_code == 404


def test_method_not_allowed(client):
    _reg(client)
    assert client.delete("/api/auth/me", headers=H).status_code == 405
    assert client.get("/api/auth/login").status_code == 405
    assert client.put("/api/notifications", headers=H).status_code == 405


def test_health_needs_no_auth(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["ok"] is True


def test_openapi_schema_is_served(client):
    r = client.get("/api/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert spec["info"]["title"] == "Meety"
    assert "/api/meetings" in spec["paths"]


def test_job_status_for_unknown_meeting(client):
    _reg(client)
    assert client.get("/api/meetings/khong-co/job").status_code == 404


def test_delete_meeting_twice(client):
    _reg(client)
    mid = _mid(client)
    assert client.delete(f"/api/meetings/{mid}", headers=H).status_code == 200
    assert client.delete(f"/api/meetings/{mid}", headers=H).status_code == 404


def test_very_long_path_param_does_not_crash(client):
    _reg(client)
    assert client.get("/api/meetings/" + "x" * 3000).status_code in (404, 414)


def test_meeting_list_shape_is_stable(client):
    """Frontend đọc đúng các khoá này — đổi tên khoá là làm hỏng giao diện."""
    _reg(client)
    row = client.get("/api/meetings").json()["meetings"][0]
    for key in ["id", "ws", "kind", "status", "job_state", "title", "date",
                "minutes", "my_role", "members", "assignments", "speaker_map"]:
        assert key in row, f"thiếu khoá {key}"


def test_meeting_detail_shape_is_stable(client):
    _reg(client)
    mid = _mid(client)
    d = client.get(f"/api/meetings/{mid}").json()
    for key in ["id", "ws", "kind", "status", "job_state", "title", "date",
                "minutes", "transcript", "speaker_map", "my_role",
                "members", "assignments"]:
        assert key in d, f"thiếu khoá {key}"
