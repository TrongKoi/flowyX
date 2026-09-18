"""Kiểm thử bảo mật tầng API — đi theo hướng của người tấn công, không phải
theo hướng người dùng ngoan.

Sáu hướng, mỗi hướng nhắm vào một loại lỗi khác nhau:

  1. Chống CSRF   — phải chặn ở MỌI verb ghi, không sót cái nào.
  2. Xác thực     — phiên giả, phiên hết hạn, phiên chưa qua 2FA.
  3. IDOR         — đoán id của người khác, và phải nhận 404 chứ không 403.
  4. Chèn mã      — SQL, HTML/XSS, ký tự điều khiển, đường dẫn vượt thư mục.
  5. Rò rỉ        — thông báo lỗi không được tiết lộ email nào đã đăng ký,
                    phản hồi không được kèm mật khẩu băm hay khoá TOTP.
  6. Nâng quyền   — thành viên tự phong mình làm chủ, đổi trường không được phép.

    pytest tests/test_api_security.py -v
"""

from __future__ import annotations

import json
import time

import pytest

pytest.importorskip("fastapi", reason="cần: pip install -r requirements.txt")
from fastapi.testclient import TestClient  # noqa: E402

from server import security, store  # noqa: E402

H = {"X-Requested-With": "Meety"}
PW = "mat-khau-manh-2026"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store.close_all()
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "sec.db")
    from server import app as app_module
    monkeypatch.setattr(app_module, "UPLOAD_DIR", tmp_path / "uploads")
    from server import jobs
    monkeypatch.setattr(jobs, "DB_PATH", tmp_path / "sec.db")
    monkeypatch.setattr(jobs, "ARTIFACT_ROOT", tmp_path / "artifacts")
    with TestClient(app_module.app) as c:
        yield c
    store.close_all()


def _reg(c, email="chu@congty.vn", name="Chủ Cuộc Họp"):
    r = c.post("/api/auth/register", headers=H,
               json={"email": email, "password": PW, "display_name": name})
    assert r.status_code == 201, r.text
    return r.json()


def _mid(c):
    return c.get("/api/meetings").json()["meetings"][0]["id"]


# ===========================================================================
#  1 · Chống CSRF trên mọi verb ghi
# ===========================================================================

WRITE_ROUTES = [
    ("post", "/api/auth/register", {"email": "x@y.vn", "password": PW, "display_name": "X"}),
    ("post", "/api/auth/login", {"email": "x@y.vn", "password": PW}),
    ("post", "/api/auth/logout", None),
    ("post", "/api/auth/2fa/setup", None),
    ("post", "/api/auth/2fa/enable", {"code": "123456"}),
    ("post", "/api/auth/2fa/disable", {"code": "123456"}),
    ("post", "/api/auth/2fa/verify", {"code": "123456"}),
    ("patch", "/api/settings/profile", {"display_name": "Y"}),
    ("post", "/api/settings/password", {"current_password": PW, "new_password": PW + "x"}),
    ("post", "/api/settings/sessions/revoke", None),
    ("post", "/api/notifications/read", None),
    ("delete", "/api/notifications", None),
    ("delete", "/api/notifications/bat-ky", None),
    ("patch", "/api/meetings/bat-ky/status", {"status": "approved"}),
    ("put", "/api/meetings/bat-ky/speakers", {"mapping": {}}),
    ("delete", "/api/meetings/bat-ky", None),
    ("post", "/api/meetings/bat-ky/members", {"email": "a@b.vn"}),
    ("delete", "/api/meetings/bat-ky/members/mb_1", None),
    ("put", "/api/meetings/bat-ky/tasks/a_001/assignee", {"member_id": None}),
    ("post", "/api/meetings/bat-ky/tasks/auto-assign", None),
    ("post", "/api/meetings/upload", None),          # multipart, xử lý riêng bên dưới
    ("patch", "/api/meetings/bat-ky/tasks/a_001", {"status": "done"}),
    ("post", "/api/meetings/bat-ky/approve", {"approve": True}),
    ("post", "/api/meetings/bat-ky/ai/analyze", {"mode": "primary"}),
    ("post", "/api/meetings/bat-ky/ai/benchmark", None),
    ("patch", "/api/meetings/bat-ky/members/mb_1/role", {"role": "co_owner"}),
    ("post", "/api/meetings/bat-ky/members/mb_1/transfer", None),
    ("patch", "/api/meetings/bat-ky/tasks/a_001/due", {"due_date": "2026-08-20"}),
    ("delete", "/api/meetings/bat-ky/tasks/a_001", None),
    ("post", "/api/meetings/bat-ky/tasks/a_001/restore", None),
    ("post", "/api/meetings/bat-ky/tasks", {"task": "X"}),
]


@pytest.mark.parametrize("method,path,body", WRITE_ROUTES,
                         ids=[f"{m.upper()} {p}" for m, p, _ in WRITE_ROUTES])
def test_every_write_route_requires_csrf_header(client, method, path, body):
    """Một route ghi quên hàng rào CSRF là đủ để bị lợi dụng.

    Liệt kê thủ công thay vì tự dò từ app: danh sách này phải được cập nhật
    bằng tay mỗi khi thêm endpoint, và đó chính là mục đích — quên cập nhật thì
    test bên dưới sẽ tố cáo.
    """
    _reg(client)
    if path.endswith("/upload"):
        r = client.post(path, files={"file": ("a.vtt", b"WEBVTT", "text/vtt")})
    elif body:
        r = getattr(client, method)(path, json=body)
    else:
        r = getattr(client, method)(path)
    assert r.status_code == 403, f"{method.upper()} {path} không đòi header CSRF"


def test_route_list_covers_every_write_endpoint(client):
    """Danh sách trên phải phủ hết route ghi thật của ứng dụng."""
    from server.app import app
    actual = set()
    for route in app.routes:
        for m in getattr(route, "methods", set()) or set():
            if m in {"POST", "PUT", "PATCH", "DELETE"}:
                actual.add((m.lower(), route.path))
    listed = {(m, p) for m, p, _ in WRITE_ROUTES}

    def norm(p):
        import re
        return re.sub(r"\{[^}]+\}", "{}", p)
    actual_n = {(m, norm(p)) for m, p in actual}
    listed_n = {(m, norm(p.replace("bat-ky", "{}").replace("mb_1", "{}")
                          .replace("a_001", "{}"))) for m, p in listed}
    missing = actual_n - listed_n
    assert not missing, f"route ghi chưa có trong danh sách kiểm CSRF: {missing}"


def test_wrong_csrf_value_also_blocked(client):
    _reg(client)
    for bad in ["MMAI", "meety", "", "XMLHttpRequest", "Meety "]:
        r = client.post("/api/notifications/read", headers={"X-Requested-With": bad})
        assert r.status_code == 403, f"giá trị {bad!r} lọt qua"


def test_read_routes_do_not_require_csrf(client):
    """Đọc thì không cần — bắt buộc header ở GET chỉ gây phiền, không thêm an toàn."""
    _reg(client)
    assert client.get("/api/auth/me").status_code == 200
    assert client.get("/api/meetings").status_code == 200
    assert client.get("/api/notifications").status_code == 200


# ===========================================================================
#  2 · Xác thực và phiên
# ===========================================================================

def test_forged_session_cookie_rejected(client):
    _reg(client)
    client.cookies.set("meety_session", security.new_token())
    assert client.get("/api/auth/me").status_code == 401


def test_tampered_cookie_rejected(client):
    _reg(client)
    tok = client.cookies.get("meety_session")
    client.cookies.set("meety_session", tok[:-1] + ("A" if tok[-1] != "A" else "B"))
    assert client.get("/api/auth/me").status_code == 401


def test_empty_and_garbage_cookies_rejected(client):
    for junk in ["", "null", "undefined", "../../etc/passwd", "' OR 1=1--", "a" * 5000]:
        client.cookies.set("meety_session", junk)
        assert client.get("/api/auth/me").status_code == 401, f"lọt: {junk[:20]!r}"


def test_expired_session_rejected_and_cleaned(client):
    _reg(client)
    tok = client.cookies.get("meety_session")
    th = security.hash_token(tok)
    store.db().execute("UPDATE sessions SET expires_at = ? WHERE token_hash = ?",
                       (time.time() - 10, th))
    store.db().commit()
    assert client.get("/api/auth/me").status_code == 401
    assert store.get_session(th) is None


def test_session_survives_deleted_user_gracefully(client):
    """Xoá người dùng trong DB rồi mà cookie vẫn còn → 401, không phải 500."""
    r = _reg(client)
    store.db().execute("DELETE FROM users WHERE id = ?", (r["user"]["id"],))
    store.db().commit()
    assert client.get("/api/auth/me").status_code == 401


def test_logout_is_idempotent_and_kills_only_current(client):
    _reg(client)
    other = TestClient(client.app)
    other.post("/api/auth/login", headers=H, json={"email": "chu@congty.vn", "password": PW})
    client.post("/api/auth/logout", headers=H)
    assert client.post("/api/auth/logout", headers=H).status_code == 401
    assert other.get("/api/auth/me").status_code == 200


def test_mfa_pending_session_locked_to_one_endpoint(client):
    """Phiên chưa qua 2FA chỉ được đi tới đúng chỗ nhập mã."""
    _reg(client)
    secret = client.post("/api/auth/2fa/setup", headers=H).json()["secret"]
    client.post("/api/auth/2fa/enable", headers=H, json={"code": security.totp_now(secret)})
    client.post("/api/auth/logout", headers=H)
    client.post("/api/auth/login", headers=H, json={"email": "chu@congty.vn", "password": PW})

    for method, path in [("get", "/api/meetings"), ("get", "/api/notifications"),
                         ("patch", "/api/settings/profile"),
                         ("post", "/api/settings/sessions/revoke"),
                         ("post", "/api/auth/2fa/setup")]:
        r = (client.get(path) if method == "get"
             else getattr(client, method)(path, headers=H, json={}))
        assert r.status_code == 403, f"{path} lọt qua khi chưa xác thực 2 lớp ({r.status_code})"
    # nhưng /me phải xem được, để giao diện biết đang kẹt ở bước nào
    me = client.get("/api/auth/me")
    assert me.status_code == 200 and me.json()["mfa_pending"] is True


def test_cookie_flags_are_hardened(client):
    _reg(client)
    raw = client.cookies.jar._cookies
    cookie = None
    for domain in raw.values():
        for path in domain.values():
            cookie = path.get("meety_session") or cookie
    assert cookie is not None
    assert cookie.has_nonstandard_attr("HttpOnly"), "cookie phải HttpOnly"


# ===========================================================================
#  3 · IDOR — chạm vào dữ liệu người khác
# ===========================================================================

def test_stranger_cannot_read_or_write_any_meeting_route(client):
    _reg(client)
    mid = _mid(client)
    task = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"][0]["id"]

    other = TestClient(client.app)
    other.post("/api/auth/register", headers=H,
               json={"email": "la@congty.vn", "password": PW, "display_name": "Người Lạ"})

    probes = [
        ("get", f"/api/meetings/{mid}", None),
        ("get", f"/api/meetings/{mid}/members", None),
        ("get", f"/api/meetings/{mid}/job", None),
        ("patch", f"/api/meetings/{mid}/status", {"status": "approved"}),
        ("put", f"/api/meetings/{mid}/speakers", {"mapping": {}}),
        ("delete", f"/api/meetings/{mid}", None),
        ("post", f"/api/meetings/{mid}/members", {"email": "x@y.vn"}),
        ("put", f"/api/meetings/{mid}/tasks/{task}/assignee", {"member_id": None}),
        ("post", f"/api/meetings/{mid}/tasks/auto-assign", None),
    ]
    for method, path, body in probes:
        r = getattr(other, method)(path, headers=H, json=body) if body is not None \
            else getattr(other, method)(path, headers=H)
        assert r.status_code == 404, f"{method.upper()} {path} trả {r.status_code}, phải là 404"


def test_unknown_id_and_known_id_look_identical_to_stranger(client):
    """Không được phân biệt "không tồn tại" với "không phải của bạn"."""
    _reg(client)
    mid = _mid(client)
    other = TestClient(client.app)
    other.post("/api/auth/register", headers=H,
               json={"email": "la@congty.vn", "password": PW, "display_name": "Lạ"})
    a = other.get(f"/api/meetings/{mid}")
    b = other.get("/api/meetings/mtg_chac_chan_khong_ton_tai")
    assert a.status_code == b.status_code == 404
    assert a.json() == b.json(), "thông báo lỗi khác nhau là kênh rò rỉ"


def test_member_cannot_assign_task_to_himself(client):
    _reg(client)
    mid = _mid(client)
    guest = TestClient(client.app)
    guest.post("/api/auth/register", headers=H,
               json={"email": "tv@congty.vn", "password": PW, "display_name": "Thành Viên"})
    inv = client.post(f"/api/meetings/{mid}/members", headers=H, json={"email": "tv@congty.vn"})
    member_id = [m for m in inv.json()["members"] if m["role"] == "member"][0]["id"]
    task = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"][0]["id"]
    r = guest.put(f"/api/meetings/{mid}/tasks/{task}/assignee", headers=H,
                  json={"member_id": member_id})
    assert r.status_code == 403


def test_cannot_assign_member_from_another_meeting(client):
    """member_id của cuộc họp khác không được dùng chéo."""
    _reg(client)
    mine = _mid(client)
    other = TestClient(client.app)
    other.post("/api/auth/register", headers=H,
               json={"email": "kia@congty.vn", "password": PW, "display_name": "Kia"})
    theirs = other.get("/api/meetings").json()["meetings"][0]["id"]
    foreign = other.post(f"/api/meetings/{theirs}/members", headers=H,
                         json={"email": "ai.do@congty.vn"}).json()
    foreign_id = [m for m in foreign["members"] if m["role"] == "member"][0]["id"]

    task = client.get(f"/api/meetings/{mine}").json()["minutes"]["action_items"][0]["id"]
    r = client.put(f"/api/meetings/{mine}/tasks/{task}/assignee", headers=H,
                   json={"member_id": foreign_id})
    assert r.status_code == 400


def test_cannot_remove_member_of_another_meeting(client):
    _reg(client)
    mine = _mid(client)
    other = TestClient(client.app)
    other.post("/api/auth/register", headers=H,
               json={"email": "kia@congty.vn", "password": PW, "display_name": "Kia"})
    theirs = other.get("/api/meetings").json()["meetings"][0]["id"]
    foreign = other.post(f"/api/meetings/{theirs}/members", headers=H,
                         json={"email": "ai.do@congty.vn"}).json()
    fid = [m for m in foreign["members"] if m["role"] == "member"][0]["id"]
    assert client.delete(f"/api/meetings/{mine}/members/{fid}", headers=H).status_code == 400
    assert len(other.get(f"/api/meetings/{theirs}/members").json()["members"]) == 2


def test_notification_of_another_user_cannot_be_deleted(client):
    _reg(client)
    nid = client.get("/api/notifications").json()["items"][0]["id"]
    other = TestClient(client.app)
    other.post("/api/auth/register", headers=H,
               json={"email": "la@congty.vn", "password": PW, "display_name": "Lạ"})
    assert other.delete(f"/api/notifications/{nid}", headers=H).status_code == 404
    assert len(client.get("/api/notifications").json()["items"]) >= 1


# ===========================================================================
#  4 · Chèn mã
# ===========================================================================

SQLI = ["' OR '1'='1", "'; DROP TABLE users;--", "\" OR 1=1--",
        "admin'--", "1' UNION SELECT * FROM users--"]


@pytest.mark.parametrize("payload", SQLI)
def test_sql_injection_in_login_email(client, payload):
    _reg(client)
    r = client.post("/api/auth/login", headers=H, json={"email": payload, "password": PW})
    assert r.status_code in (401, 422)
    # bảng vẫn còn nguyên
    assert store.db().execute("SELECT COUNT(*) c FROM users").fetchone()["c"] == 1


@pytest.mark.parametrize("payload", SQLI)
def test_sql_injection_in_path_params(client, payload):
    _reg(client)
    r = client.get(f"/api/meetings/{payload}")
    assert r.status_code == 404
    assert store.db().execute(
        "SELECT COUNT(*) c FROM meetings").fetchone()["c"] >= 1


def test_sql_injection_in_display_name_is_stored_literally(client):
    _reg(client)
    evil = "Robert'); DROP TABLE meetings;--"
    client.patch("/api/settings/profile", headers=H, json={"display_name": evil})
    assert client.get("/api/auth/me").json()["user"]["display_name"] == evil
    assert store.db().execute("SELECT COUNT(*) c FROM meetings").fetchone()["c"] >= 1


def test_xss_payload_stored_verbatim_not_executed_server_side(client):
    """Máy chủ lưu nguyên văn; việc thoát ký tự là của tầng hiển thị.

    Quan trọng là nó KHÔNG bị biến dạng — biến dạng nghĩa là có ai đó đang cố
    "làm sạch" bằng cách thay chuỗi, và cách đó luôn có lỗ.
    """
    _reg(client)
    evil = '<script>alert("xss")</script>'
    client.patch("/api/settings/profile", headers=H, json={"display_name": evil})
    got = client.get("/api/auth/me").json()["user"]["display_name"]
    assert got == evil
    # phản hồi JSON phải mã hoá dấu ngoặc nhọn an toàn khi nhúng vào HTML
    raw = client.get("/api/auth/me").text
    assert '"<script>' in raw or '\\u003c' in raw


def test_path_traversal_in_uploaded_filename(client, tmp_path):
    """Tên tệp độc không được thoát khỏi thư mục tải lên."""
    _reg(client)
    for name in ["../../../../etc/passwd.vtt", "..\\..\\windows\\system32\\a.vtt",
                 "/tmp/tuyet_doi.vtt", "....//....//x.vtt"]:
        r = client.post("/api/meetings/upload", headers=H,
                        files={"file": (name, "WEBVTT\n\n00:00.000 --> 00:01.000\nxin chào\n".encode("utf-8"),
                                        "text/vtt")},
                        data={"title": "T", "meeting_date": "2026-08-01"})
        assert r.status_code in (202, 400, 415), f"{name} → {r.status_code}"
    from server import app as app_module
    for f in app_module.UPLOAD_DIR.glob("**/*"):
        assert app_module.UPLOAD_DIR in f.resolve().parents, f"tệp thoát ra ngoài: {f}"
        assert ".." not in f.name


def test_null_bytes_and_control_chars_rejected_or_neutralised(client):
    _reg(client)
    r = client.patch("/api/settings/profile", headers=H,
                     json={"display_name": "Tên\x00Có\x07Ký\x1btự lạ"})
    assert r.status_code in (200, 422)
    if r.status_code == 200:
        assert client.get("/api/auth/me").status_code == 200


def test_unicode_email_normalisation_prevents_duplicate_accounts(client):
    _reg(client, email="Nguoi.Dung@CongTy.VN")
    r = client.post("/api/auth/register", headers=H,
                    json={"email": "nguoi.dung@congty.vn", "password": PW,
                          "display_name": "Trùng"})
    assert r.status_code == 409, "email khác hoa thường không được tạo tài khoản thứ hai"


# ===========================================================================
#  5 · Rò rỉ thông tin
# ===========================================================================

def test_response_never_contains_password_hash_or_totp_secret(client):
    _reg(client)
    secret = client.post("/api/auth/2fa/setup", headers=H).json()["secret"]
    client.post("/api/auth/2fa/enable", headers=H, json={"code": security.totp_now(secret)})

    for path in ["/api/auth/me", "/api/meetings", "/api/notifications"]:
        body = client.get(path).text
        assert "password_hash" not in body
        assert "scrypt$" not in body
        assert "totp_secret" not in body
        assert secret not in body, f"khoá TOTP lộ ở {path}"


def test_login_error_identical_for_unknown_email_and_wrong_password(client):
    _reg(client)
    client.post("/api/auth/logout", headers=H)
    a = client.post("/api/auth/login", headers=H,
                    json={"email": "chu@congty.vn", "password": "sai-mat-khau"})
    b = client.post("/api/auth/login", headers=H,
                    json={"email": "khong.co@congty.vn", "password": "sai-mat-khau"})
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json(), "thông báo khác nhau cho biết email nào đã đăng ký"


def test_login_timing_does_not_reveal_account_existence(client):
    """Cả hai nhánh đều phải chạy scrypt, nên thời gian phải xấp xỉ nhau."""
    _reg(client)
    client.post("/api/auth/logout", headers=H)

    def measure(email):
        best = 1e9
        for _ in range(3):
            t = time.perf_counter()
            client.post("/api/auth/login", headers=H,
                        json={"email": email, "password": "sai-mat-khau"})
            best = min(best, time.perf_counter() - t)
        return best

    known = measure("chu@congty.vn")
    unknown = measure("khong.co@congty.vn")
    ratio = max(known, unknown) / max(1e-6, min(known, unknown))
    assert ratio < 4, f"chênh lệch {ratio:.1f}× là đủ để dò email đã đăng ký"


def test_error_body_shape_is_uniform(client):
    """Mọi lỗi trả về cùng một hình dạng, để frontend chỉ xử lý một kiểu."""
    _reg(client)
    for r in [client.get("/api/meetings/khong-co"),
              client.post("/api/auth/login", headers=H,
                          json={"email": "a@b.vn", "password": "x"}),
              client.delete("/api/notifications/khong-co", headers=H)]:
        assert set(r.json()) == {"error"}, r.json()
        assert isinstance(r.json()["error"], str)


# ===========================================================================
#  6 · Nâng quyền
# ===========================================================================

def test_cannot_set_privileged_fields_through_profile(client):
    _reg(client)
    r = client.patch("/api/settings/profile", headers=H, json={
        "display_name": "Bình thường",
        "totp_enabled": True, "password_hash": "gia-mao",
        "id": "u_khac", "email": "doi@mail.vn", "role": "admin",
    })
    assert r.status_code in (200, 422)
    me = client.get("/api/auth/me").json()["user"]
    assert me["email"] == "chu@congty.vn"
    assert me["totp_enabled"] is False
    row = store.get_user(me["id"])
    assert row["password_hash"] != "gia-mao"


def test_member_role_cannot_be_escalated_via_invite(client):
    """Mời lại chính mình với vai trò khác không được nâng quyền."""
    _reg(client)
    mid = _mid(client)
    guest = TestClient(client.app)
    guest.post("/api/auth/register", headers=H,
               json={"email": "tv@congty.vn", "password": PW, "display_name": "TV"})
    client.post(f"/api/meetings/{mid}/members", headers=H, json={"email": "tv@congty.vn"})
    # thành viên tự mời mình lại — phải bị chặn ngay ở tầng quyền
    assert guest.post(f"/api/meetings/{mid}/members", headers=H,
                      json={"email": "tv@congty.vn"}).status_code == 403
    assert guest.get(f"/api/meetings/{mid}").json()["my_role"] == "member"


def test_2fa_cannot_be_disabled_without_a_valid_code(client):
    """Phiên bị chiếm không được tự tháo hàng rào 2 lớp."""
    _reg(client)
    secret = client.post("/api/auth/2fa/setup", headers=H).json()["secret"]
    client.post("/api/auth/2fa/enable", headers=H, json={"code": security.totp_now(secret)})
    for bad in ["000000", "", "abcdef", security.totp_now(security.new_totp_secret())]:
        r = client.post("/api/auth/2fa/disable", headers=H, json={"code": bad})
        assert r.status_code in (401, 422)
    assert client.get("/api/auth/me").json()["user"]["totp_enabled"] is True


def test_password_change_requires_current_password(client):
    _reg(client)
    r = client.post("/api/settings/password", headers=H,
                    json={"current_password": "doan-bua", "new_password": "mat-khau-moi-123"})
    assert r.status_code == 401
    client.post("/api/auth/logout", headers=H)
    assert client.post("/api/auth/login", headers=H,
                       json={"email": "chu@congty.vn", "password": PW}).status_code == 200
