"""Kiểm thử đồng thời, tính bất biến khi lặp, và độ bền của dữ liệu.

Ba loại lỗi mà test tuần tự không bao giờ thấy:

  1. **Đua nhau (race).** Hai yêu cầu tới cùng lúc trên cùng một bản ghi. Với
     SQLite chỉ có một người ghi tại một thời điểm, nên câu hỏi không phải
     "có mất dữ liệu không" mà là "người thua có nhận lỗi tử tế không, hay
     nhận 500".
  2. **Lặp lại (idempotency).** Người dùng bấm hai lần vì mạng chậm. Lần thứ
     hai phải cho cùng kết quả, không tạo bản ghi trùng.
  3. **Bền (durability).** Máy chủ khởi động lại giữa chừng. Dữ liệu đã ghi
     phải còn; job đang chạy phải báo trạng thái tử tế chứ không biến mất.

    pytest tests/test_api_concurrency.py -v
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

pytest.importorskip("fastapi", reason="cần: pip install -r requirements.txt")
from fastapi.testclient import TestClient  # noqa: E402

from server import security, store  # noqa: E402

H = {"X-Requested-With": "Meety"}
PW = "mat-khau-manh-2026"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store.close_all()
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "conc.db")
    from server import app as app_module
    monkeypatch.setattr(app_module, "UPLOAD_DIR", tmp_path / "uploads")
    from server import jobs
    monkeypatch.setattr(jobs, "DB_PATH", tmp_path / "conc.db")
    monkeypatch.setattr(jobs, "ARTIFACT_ROOT", tmp_path / "artifacts")
    monkeypatch.setattr(jobs, "mock_needed", lambda: True)
    with TestClient(app_module.app) as c:
        yield c
    store.close_all()


def _reg(c, email="chu@congty.vn"):
    return c.post("/api/auth/register", headers=H,
                  json={"email": email, "password": PW, "display_name": "Chủ"})


def _mid(c):
    return c.get("/api/meetings").json()["meetings"][0]["id"]


def _parallel(fn, n=8):
    """Chạy `fn(i)` trên n luồng, trả về danh sách kết quả theo đúng thứ tự."""
    with ThreadPoolExecutor(max_workers=n) as ex:
        return list(ex.map(fn, range(n)))


# ===========================================================================
#  1 · Đăng ký và đăng nhập đồng thời
# ===========================================================================

def test_same_email_registered_concurrently_yields_one_account(client):
    """Khoá UNIQUE phải giữ, và người thua nhận 409 chứ không phải 500."""
    def go(_i):
        c = TestClient(client.app)
        return c.post("/api/auth/register", headers=H, json={
            "email": "dua@congty.vn", "password": PW, "display_name": "Đua"}).status_code

    codes = _parallel(go, 8)
    assert codes.count(201) == 1, f"tạo {codes.count(201)} tài khoản: {codes}"
    assert all(c in (201, 409, 500) for c in codes), codes
    assert codes.count(500) == 0, "va chạm khoá UNIQUE lộ ra thành lỗi 500"
    n = store.db().execute("SELECT COUNT(*) c FROM users WHERE email = ?",
                           ("dua@congty.vn",)).fetchone()["c"]
    assert n == 1


def test_many_parallel_logins_all_succeed(client):
    _reg(client)

    def go(_i):
        c = TestClient(client.app)
        r = c.post("/api/auth/login", headers=H,
                   json={"email": "chu@congty.vn", "password": PW})
        return r.status_code

    assert _parallel(go, 10) == [200] * 10


def test_parallel_sessions_are_all_independent(client):
    _reg(client)
    clients = []
    for _ in range(5):
        c = TestClient(client.app)
        c.post("/api/auth/login", headers=H, json={"email": "chu@congty.vn", "password": PW})
        clients.append(c)
    assert all(c.get("/api/auth/me").status_code == 200 for c in clients)
    # đăng xuất một phiên không được ảnh hưởng phiên khác
    clients[0].post("/api/auth/logout", headers=H)
    assert clients[0].get("/api/auth/me").status_code == 401
    assert all(c.get("/api/auth/me").status_code == 200 for c in clients[1:])


def test_concurrent_password_change_and_read(client):
    """Đổi mật khẩu trong lúc phiên khác đang đọc — không được sập."""
    _reg(client)
    others = []
    for _ in range(4):
        c = TestClient(client.app)
        c.post("/api/auth/login", headers=H, json={"email": "chu@congty.vn", "password": PW})
        others.append(c)

    stop = threading.Event()
    errors = []

    def reader(c):
        while not stop.is_set():
            code = c.get("/api/auth/me").status_code
            if code not in (200, 401):
                errors.append(code)

    threads = [threading.Thread(target=reader, args=(c,), daemon=True) for c in others]
    for t in threads:
        t.start()
    time.sleep(0.05)
    r = client.post("/api/settings/password", headers=H,
                    json={"current_password": PW, "new_password": "mat-khau-moi-2026"})
    stop.set()
    for t in threads:
        t.join(timeout=5)
    assert r.status_code == 200
    assert not errors, f"phản hồi lạ khi đang đổi mật khẩu: {set(errors)}"


# ===========================================================================
#  2 · Mời và gán việc đồng thời
# ===========================================================================

def test_inviting_same_email_concurrently_creates_one_member(client):
    _reg(client)
    mid = _mid(client)
    cookie = client.cookies.get("meety_session")

    def go(_i):
        c = TestClient(client.app)
        c.cookies.set("meety_session", cookie)
        return c.post(f"/api/meetings/{mid}/members", headers=H,
                      json={"email": "trung@congty.vn"}).status_code

    codes = _parallel(go, 8)
    assert all(c in (201, 400, 409) for c in codes), codes
    members = client.get(f"/api/meetings/{mid}/members").json()["members"]
    dup = [m for m in members if m["email"] == "trung@congty.vn"]
    assert len(dup) == 1, f"tạo {len(dup)} bản ghi cho cùng một email"


def test_concurrent_assignment_last_write_wins_without_duplicates(client):
    _reg(client)
    mid = _mid(client)
    cookie = client.cookies.get("meety_session")
    task = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"][0]["id"]
    ids = []
    for i in range(4):
        inv = client.post(f"/api/meetings/{mid}/members", headers=H,
                          json={"email": f"tv{i}@congty.vn"}).json()
        ids.append([m for m in inv["members"] if m["email"] == f"tv{i}@congty.vn"][0]["id"])

    def go(i):
        c = TestClient(client.app)
        c.cookies.set("meety_session", cookie)
        return c.put(f"/api/meetings/{mid}/tasks/{task}/assignee", headers=H,
                     json={"member_id": ids[i % len(ids)]}).status_code

    codes = _parallel(go, 8)
    assert all(c == 200 for c in codes), codes
    a = store.list_assignments(mid)
    assert len(a) == 1, "khoá chính (meeting, task) không giữ được duy nhất"
    assert a[task]["member_id"] in ids


def test_concurrent_status_updates_settle_on_one_value(client):
    _reg(client)
    mid = _mid(client)
    cookie = client.cookies.get("meety_session")

    def go(i):
        c = TestClient(client.app)
        c.cookies.set("meety_session", cookie)
        return c.patch(f"/api/meetings/{mid}/status", headers=H,
                       json={"status": "approved" if i % 2 else "pending"}).status_code

    assert set(_parallel(go, 10)) == {200}
    assert client.get(f"/api/meetings/{mid}").json()["status"] in ("approved", "pending")


def test_parallel_reads_during_writes_never_500(client):
    """Đọc trong lúc ghi: WAL cho phép, nên không được có 500 nào."""
    _reg(client)
    mid = _mid(client)
    cookie = client.cookies.get("meety_session")
    codes = []

    def reader(_i):
        c = TestClient(client.app)
        c.cookies.set("meety_session", cookie)
        for _ in range(10):
            codes.append(c.get(f"/api/meetings/{mid}").status_code)

    def writer(_i):
        c = TestClient(client.app)
        c.cookies.set("meety_session", cookie)
        for i in range(10):
            codes.append(c.patch(f"/api/meetings/{mid}/status", headers=H,
                                 json={"status": "approved" if i % 2 else "pending"}).status_code)

    with ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(lambda f: f(0), [reader, writer, reader, writer, reader, writer]))
    assert set(codes) == {200}, f"mã lạ khi đọc-ghi song song: {sorted(set(codes))}"


def test_concurrent_notification_deletes(client):
    _reg(client)
    for i in range(6):
        store.add_notification(client.get("/api/auth/me").json()["user"]["id"], f"TB {i}")
    ids = [n["id"] for n in client.get("/api/notifications").json()["items"]]
    cookie = client.cookies.get("meety_session")

    def go(i):
        c = TestClient(client.app)
        c.cookies.set("meety_session", cookie)
        return c.delete(f"/api/notifications/{ids[i % len(ids)]}", headers=H).status_code

    codes = _parallel(go, len(ids) * 2)
    assert all(c in (200, 404) for c in codes), codes
    assert codes.count(200) == len(ids), "mỗi thông báo phải chỉ xoá thành công đúng một lần"
    assert client.get("/api/notifications").json()["items"] == []


# ===========================================================================
#  3 · Lặp lại yêu cầu
# ===========================================================================

def test_repeating_every_write_is_safe(client):
    """Người dùng bấm hai lần vì mạng chậm — lần hai không được gây hại."""
    _reg(client)
    mid = _mid(client)
    inv = client.post(f"/api/meetings/{mid}/members", headers=H,
                      json={"email": "tv@congty.vn"}).json()
    member = [m for m in inv["members"] if m["role"] == "member"][0]["id"]
    task = client.get(f"/api/meetings/{mid}").json()["minutes"]["action_items"][0]["id"]

    repeats = [
        ("patch", f"/api/meetings/{mid}/status", {"status": "approved"}, 200),
        ("put", f"/api/meetings/{mid}/speakers", {"mapping": {"S0": {"name": "A"}}}, 200),
        ("put", f"/api/meetings/{mid}/tasks/{task}/assignee", {"member_id": member}, 200),
        ("post", f"/api/meetings/{mid}/tasks/auto-assign", None, 200),
        ("post", f"/api/meetings/{mid}/members", {"email": "tv@congty.vn"}, 201),
        ("post", "/api/notifications/read", None, 200),
        ("patch", "/api/settings/profile", {"display_name": "Tên"}, 200),
    ]
    for method, path, body, want in repeats:
        first = getattr(client, method)(path, headers=H, json=body) if body is not None \
            else getattr(client, method)(path, headers=H)
        second = getattr(client, method)(path, headers=H, json=body) if body is not None \
            else getattr(client, method)(path, headers=H)
        assert first.status_code == second.status_code == want, f"{path}: {second.text[:120]}"

    assert len(client.get(f"/api/meetings/{mid}/members").json()["members"]) == 2
    assert len(store.list_assignments(mid)) == 1


def test_double_2fa_enable_is_harmless(client):
    _reg(client)
    secret = client.post("/api/auth/2fa/setup", headers=H).json()["secret"]
    code = security.totp_now(secret)
    a = client.post("/api/auth/2fa/enable", headers=H, json={"code": code})
    b = client.post("/api/auth/2fa/enable", headers=H, json={"code": code})
    assert a.status_code == b.status_code == 200
    assert client.get("/api/auth/me").json()["user"]["totp_enabled"] is True


def test_2fa_setup_twice_keeps_same_secret(client):
    """Sinh khoá mới ở lần gọi thứ hai sẽ làm hỏng mã QR người dùng vừa quét."""
    _reg(client)
    a = client.post("/api/auth/2fa/setup", headers=H).json()["secret"]
    b = client.post("/api/auth/2fa/setup", headers=H).json()["secret"]
    assert a == b


def test_disable_2fa_when_already_off(client):
    _reg(client)
    r = client.post("/api/auth/2fa/disable", headers=H, json={"code": "000000"})
    assert r.status_code == 200 and r.json()["totp_enabled"] is False


# ===========================================================================
#  4 · Độ bền qua khởi động lại
# ===========================================================================

def test_data_survives_app_restart(client, tmp_path, monkeypatch):
    """Đóng máy chủ, mở lại trên cùng file DB — dữ liệu và phiên phải còn."""
    _reg(client)
    mid = _mid(client)
    client.patch(f"/api/meetings/{mid}/status", headers=H, json={"status": "approved"})
    client.post(f"/api/meetings/{mid}/members", headers=H, json={"email": "tv@congty.vn"})
    cookie = client.cookies.get("meety_session")

    from server import app as app_module
    with TestClient(app_module.app) as fresh:
        fresh.cookies.set("meety_session", cookie)
        assert fresh.get("/api/auth/me").status_code == 200, "phiên không sống qua khởi động lại"
        d = fresh.get(f"/api/meetings/{mid}").json()
        assert d["status"] == "approved"
        assert len(d["members"]) == 2


def test_job_status_readable_after_restart(client):
    """Job không còn trong bộ nhớ vẫn phải báo trạng thái từ DB, không 500."""
    _reg(client)
    r = client.post("/api/meetings/upload", headers=H,
                    files={"file": ("a.vtt", b"WEBVTT\n\n00:00.000 --> 00:01.000\nxin chao\n",
                                    "text/vtt")},
                    data={"meeting_date": "2026-08-01"})
    mid = r.json()["meeting_id"]
    for _ in range(60):
        if client.get(f"/api/meetings/{mid}/job").json()["state"] in ("done", "error"):
            break
        time.sleep(0.5)

    from server import jobs
    jobs._jobs.clear()                       # giả lập máy chủ vừa khởi động lại
    j = client.get(f"/api/meetings/{mid}/job")
    assert j.status_code == 200
    assert j.json()["state"] in ("done", "error", "queued", "running")
    assert "percent" in j.json()


def test_wal_checkpoint_leaves_data_intact(client):
    """Ép SQLite dồn WAL về file chính rồi đọc lại."""
    _reg(client)
    mid = _mid(client)
    client.patch(f"/api/meetings/{mid}/status", headers=H, json={"status": "approved"})
    store.db().execute("PRAGMA wal_checkpoint(TRUNCATE)")
    assert client.get(f"/api/meetings/{mid}").json()["status"] == "approved"


def test_connection_is_per_thread(client):
    """Mỗi luồng phải có kết nối riêng — dùng chung là nguồn của segfault."""
    seen = {}

    def grab(name):
        seen[name] = id(store.db())

    t = threading.Thread(target=grab, args=("nen",))
    t.start()
    t.join()
    grab("chinh")
    assert seen["nen"] != seen["chinh"], "hai luồng đang dùng chung một kết nối"


def test_closing_one_thread_connection_does_not_break_others(client):
    """Đây chính là cảnh gây segfault ở bản trước."""
    _reg(client)
    done = threading.Event()
    errors = []

    def worker():
        try:
            store.db().execute("SELECT COUNT(*) FROM users").fetchone()
            store.close()                    # luồng này tự đóng kết nối của nó
        except Exception as e:               # noqa: BLE001
            errors.append(repr(e))
        finally:
            done.set()

    t = threading.Thread(target=worker)
    t.start()
    done.wait(timeout=5)
    t.join(timeout=5)
    assert not errors, errors
    # luồng chính vẫn dùng được như thường
    assert client.get("/api/auth/me").status_code == 200


def test_background_job_writes_while_main_thread_reads(client):
    """Luồng nền ghi kết quả trong lúc luồng chính liên tục đọc."""
    _reg(client)
    r = client.post("/api/meetings/upload", headers=H,
                    files={"file": ("b.vtt", b"WEBVTT\n\n00:00.000 --> 00:01.000\nxin chao\n",
                                    "text/vtt")},
                    data={"meeting_date": "2026-08-01"})
    mid = r.json()["meeting_id"]
    codes = set()
    deadline = time.time() + 30
    while time.time() < deadline:
        codes.add(client.get("/api/meetings").status_code)
        state = client.get(f"/api/meetings/{mid}/job").json()["state"]
        if state in ("done", "error"):
            break
        time.sleep(0.2)
    assert codes == {200}, f"đọc bị lỗi trong lúc luồng nền ghi: {codes}"
