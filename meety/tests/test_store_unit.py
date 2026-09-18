"""Kiểm thử đơn vị cho `server/store.py` — chạm thẳng vào DB, không qua HTTP.

Vì sao cần tầng này khi đã có test API: test API đi qua đường vui vẻ. Ở đây ta
soi vào ràng buộc của lược đồ và vào những nhánh mà API không bao giờ gọi tới
nhưng vẫn phải đúng — xoá dây chuyền, khoá duy nhất, dữ liệu hỏng, và luật
khớp tên tự động (chỗ dễ sai nhất, vì "gần đúng" ở đây nghĩa là gán việc cho
nhầm người).

    pytest tests/test_store_unit.py -v
"""

from __future__ import annotations

import json
import time

import pytest

from server import security, store


@pytest.fixture()
def db(tmp_path, monkeypatch):
    store.close_all()
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "unit.db")
    store.db()
    yield store
    store.close_all()


def _user(db, email="a@congty.vn", name="Nguyễn Văn A"):
    return db.create_user(email=email, display_name=name,
                          password_hash=security.hash_password("mat-khau-1234"))


def _meeting(db, user, mid="mtg_test", tasks=None, title="Cuộc họp thử"):
    minutes = {
        "meeting_id": mid,
        "meta": {"meeting_title": title, "date": "2026-08-01"},
        "action_items": tasks if tasks is not None else [
            {"id": "a_001", "task": "Việc một", "assignee": "Trần Thị Bích"},
            {"id": "a_002", "task": "Việc hai", "assignee": None},
        ],
        "quality_report": {"warnings": []},
    }
    db.create_meeting(user["id"], meeting_id=mid, title=title, meeting_date="2026-08-01",
                      minutes=minutes, transcript={"segments": []}, job_state="done")
    db.add_owner(mid, user)
    return mid


# ===========================================================================
#  Người dùng
# ===========================================================================

def test_email_is_normalised_to_lowercase(db):
    _user(db, email="NGUOI.Dung@CongTy.VN")
    assert db.get_user_by_email("nguoi.dung@congty.vn") is not None
    assert db.get_user_by_email("NGUOI.DUNG@CONGTY.VN") is not None
    assert db.get_user_by_email("  nguoi.dung@congty.vn  ") is not None


def test_duplicate_email_blocked_by_schema(db):
    """Ràng buộc UNIQUE ném ra một lỗi CÓ TÊN, không phải IntegrityError trần.

    Endpoint đăng ký cần phân biệt "trùng email" (409) với mọi lỗi DB khác
    (500). Bắt IntegrityError chung chung sẽ nuốt luôn cả những lỗi thật sự
    đáng báo động.
    """
    _user(db)
    with pytest.raises(db.EmailTakenError):
        _user(db)


def test_duplicate_email_leaves_no_orphan_workspaces(db):
    """Đăng ký hỏng giữa chừng không được để lại 4 workspace mồ côi."""
    _user(db)
    before = db.db().execute("SELECT COUNT(*) c FROM workspaces").fetchone()["c"]
    with pytest.raises(db.EmailTakenError):
        _user(db)
    after = db.db().execute("SELECT COUNT(*) c FROM workspaces").fetchone()["c"]
    assert after == before == 4


def test_other_integrity_errors_still_propagate(db):
    """Chỉ trùng email mới thành EmailTakenError; lỗi khác phải nổi lên nguyên vẹn."""
    import sqlite3
    u = _user(db)
    with pytest.raises(sqlite3.IntegrityError):
        db.db().execute(
            "INSERT INTO meeting_members (id, meeting_id, email, invited_by, invited_at)"
            " VALUES (?,?,?,?,?)", (None, "m", "a@b.vn", u["id"], 0))


def test_new_user_gets_four_workspaces(db):
    u = _user(db)
    ws = db.list_workspaces(u["id"])
    assert len(ws) == 4
    assert {w["id"] for w in ws} == {"w_prod", "w_eng", "w_hr", "w_fin"}


def test_workspaces_are_per_user_not_shared(db):
    a = _user(db, "a@x.vn")
    b = _user(db, "b@x.vn", "Người B")
    ids_a = {w["id"] for w in db.list_workspaces(a["id"])}
    ids_b = {w["id"] for w in db.list_workspaces(b["id"])}
    assert ids_a == ids_b                       # cùng id ngắn cho frontend
    rows = db.db().execute("SELECT id FROM workspaces").fetchall()
    assert len(rows) == 8                       # nhưng là 8 bản ghi tách biệt


def test_update_user_ignores_unknown_fields(db):
    """Chỉ danh sách trường cho phép mới được ghi.

    Không có chốt này thì một endpoint sơ ý sẽ cho người dùng tự đặt
    `password_hash` hoặc `totp_enabled` qua body JSON.
    """
    u = _user(db)
    db.update_user(u["id"], display_name="Tên Mới", id="hacker", email="doi@mail.vn")
    again = db.get_user(u["id"])
    assert again["display_name"] == "Tên Mới"
    assert again["id"] == u["id"]
    assert again["email"] == "a@congty.vn"


# ===========================================================================
#  Phiên
# ===========================================================================

def test_expired_session_is_deleted_on_read(db):
    u = _user(db)
    th = security.hash_token("token-gia")
    db.create_session(u["id"], th, mfa_pending=False)
    db.db().execute("UPDATE sessions SET expires_at = ? WHERE token_hash = ?",
                    (time.time() - 1, th))
    db.db().commit()
    assert db.get_session(th) is None
    # phải dọn luôn, không để rác tích lại
    assert db.db().execute("SELECT COUNT(*) c FROM sessions").fetchone()["c"] == 0


def test_delete_all_sessions_can_keep_current(db):
    u = _user(db)
    hashes = [security.hash_token(f"t{i}") for i in range(4)]
    for h in hashes:
        db.create_session(u["id"], h, mfa_pending=False)
    killed = db.delete_all_sessions(u["id"], keep=hashes[0])
    assert killed == 3
    assert db.get_session(hashes[0]) is not None
    assert all(db.get_session(h) is None for h in hashes[1:])


def test_sessions_of_other_users_untouched(db):
    a, b = _user(db, "a@x.vn"), _user(db, "b@x.vn", "B")
    ha, hb = security.hash_token("ta"), security.hash_token("tb")
    db.create_session(a["id"], ha, mfa_pending=False)
    db.create_session(b["id"], hb, mfa_pending=False)
    db.delete_all_sessions(a["id"])
    assert db.get_session(hb) is not None


def test_count_sessions_excludes_mfa_pending(db):
    """Phiên chưa qua 2FA chưa phải là một thiết bị đang đăng nhập."""
    u = _user(db)
    db.create_session(u["id"], security.hash_token("done"), mfa_pending=False)
    db.create_session(u["id"], security.hash_token("pending"), mfa_pending=True)
    assert db.count_sessions(u["id"]) == 1


def test_deleting_user_cascades_to_sessions(db):
    u = _user(db)
    db.create_session(u["id"], security.hash_token("t"), mfa_pending=False)
    db.db().execute("PRAGMA foreign_keys = ON")
    db.db().execute("DELETE FROM users WHERE id = ?", (u["id"],))
    db.db().commit()
    assert db.db().execute("SELECT COUNT(*) c FROM sessions").fetchone()["c"] == 0


# ===========================================================================
#  Thành viên
# ===========================================================================

def test_owner_added_once_even_if_called_twice(db):
    u = _user(db)
    mid = _meeting(db, u)
    db.add_owner(mid, u)
    assert len(db.list_members(mid)) == 1


def test_owner_sorts_first(db):
    u = _user(db)
    mid = _meeting(db, u)
    db.invite_member(mid, "z@x.vn", u["id"])
    db.invite_member(mid, "a@x.vn", u["id"])
    assert db.list_members(mid)[0]["role"] == "owner"


def test_invite_same_email_twice_returns_same_row(db):
    u = _user(db)
    mid = _meeting(db, u)
    m1 = db.invite_member(mid, "b@x.vn", u["id"])
    m2 = db.invite_member(mid, "B@X.VN", u["id"])       # khác hoa thường
    assert m1["id"] == m2["id"]
    assert len(db.list_members(mid)) == 2


def test_invite_links_existing_account(db):
    owner = _user(db, "chu@x.vn")
    guest = _user(db, "khach@x.vn", "Khách Mời")
    mid = _meeting(db, owner)
    m = db.invite_member(mid, "khach@x.vn", owner["id"])
    assert m["user_id"] == guest["id"] and m["accepted"] == 1
    assert m["display_name"] == "Khách Mời"


def test_invite_without_account_stays_pending(db):
    u = _user(db)
    mid = _meeting(db, u)
    m = db.invite_member(mid, "chuacó@x.vn", u["id"])
    assert m["user_id"] is None and m["accepted"] == 0
    assert db.role_of(mid, "khong-ton-tai") is None


def test_link_pending_invites_on_registration(db):
    owner = _user(db, "chu@x.vn")
    mid = _meeting(db, owner)
    db.invite_member(mid, "sau.nay@x.vn", owner["id"])
    later = _user(db, "sau.nay@x.vn", "Sau Này")
    n = db.link_pending_invites(later)
    assert n == 1
    assert db.role_of(mid, later["id"]) == "member"


def test_link_pending_invites_across_several_meetings(db):
    owner = _user(db, "chu@x.vn")
    ids = [_meeting(db, owner, mid=f"mtg_{i}") for i in range(3)]
    for mid in ids:
        db.invite_member(mid, "nhieu@x.vn", owner["id"])
    u = _user(db, "nhieu@x.vn", "Nhiều Lời Mời")
    assert db.link_pending_invites(u) == 3
    assert all(db.role_of(mid, u["id"]) == "member" for mid in ids)


def test_remove_member_rejects_owner_and_foreign_id(db):
    owner = _user(db, "chu@x.vn")
    other_owner = _user(db, "chu2@x.vn", "Chủ Khác")
    mid = _meeting(db, owner)
    mid2 = _meeting(db, other_owner, mid="mtg_khac")
    owner_row = db.list_members(mid)[0]
    foreign = db.invite_member(mid2, "x@x.vn", other_owner["id"])

    assert db.remove_member(mid, owner_row["id"]) is False
    assert db.remove_member(mid, foreign["id"]) is False, "không được gỡ chéo cuộc họp"
    assert db.remove_member(mid, "khong-ton-tai") is False
    assert len(db.list_members(mid2)) == 2


def test_role_of_falls_back_to_meeting_creator(db):
    """Cuộc họp tạo trước khi có bảng thành viên vẫn phải nhận đúng chủ."""
    u = _user(db)
    db.create_meeting(u["id"], meeting_id="mtg_cu", title="Cũ",
                      meeting_date="2026-01-01", minutes={}, transcript={})
    assert db.role_of("mtg_cu", u["id"]) == "owner"


def test_list_meetings_for_user_includes_invited(db):
    owner = _user(db, "chu@x.vn")
    guest = _user(db, "khach@x.vn", "Khách")
    mine = _meeting(db, owner, mid="mtg_cua_toi")
    theirs = _meeting(db, guest, mid="mtg_cua_ho")
    db.invite_member(mine, "khach@x.vn", owner["id"])

    rows = db.list_meetings_for_user(guest["id"])
    by_id = {m["id"]: role for m, role in rows}
    assert by_id[theirs] == "owner"
    assert by_id[mine] == "member"


def test_list_meetings_has_no_duplicates(db):
    """Chủ cuộc họp cũng nằm trong bảng thành viên — JOIN dễ nhân đôi hàng."""
    u = _user(db)
    mid = _meeting(db, u)
    rows = db.list_meetings_for_user(u["id"])
    assert len(rows) == 1 and rows[0][1] == "owner"


# ===========================================================================
#  Gán công việc
# ===========================================================================

def test_assignment_replaces_not_duplicates(db):
    u = _user(db)
    mid = _meeting(db, u)
    m1 = db.invite_member(mid, "b@x.vn", u["id"])
    m2 = db.invite_member(mid, "c@x.vn", u["id"])
    db.set_assignment(mid, "a_001", m1["id"], u["id"])
    db.set_assignment(mid, "a_001", m2["id"], u["id"])
    a = db.list_assignments(mid)
    assert len(a) == 1 and a["a_001"]["member_id"] == m2["id"]


def test_assignment_null_means_deliberately_empty(db):
    u = _user(db)
    mid = _meeting(db, u)
    m = db.invite_member(mid, "b@x.vn", u["id"])
    db.set_assignment(mid, "a_001", m["id"], u["id"])
    db.set_assignment(mid, "a_001", None, u["id"])
    a = db.list_assignments(mid)
    assert "a_001" in a and a["a_001"]["member_id"] is None


def test_removing_member_nulls_their_assignments_only(db):
    u = _user(db)
    mid = _meeting(db, u)
    keep = db.invite_member(mid, "giu@x.vn", u["id"])
    drop = db.invite_member(mid, "go@x.vn", u["id"])
    db.set_assignment(mid, "a_001", drop["id"], u["id"])
    db.set_assignment(mid, "a_002", keep["id"], u["id"])
    db.remove_member(mid, drop["id"])
    a = db.list_assignments(mid)
    assert a["a_001"]["member_id"] is None
    assert a["a_002"]["member_id"] == keep["id"]


def test_assignments_scoped_per_meeting(db):
    u = _user(db)
    m1 = _meeting(db, u, mid="mtg_1")
    m2 = _meeting(db, u, mid="mtg_2")
    mem = db.invite_member(m1, "b@x.vn", u["id"])
    db.set_assignment(m1, "a_001", mem["id"], u["id"])
    assert db.list_assignments(m2) == {}


def test_deleting_meeting_cascades_members_and_assignments(db):
    u = _user(db)
    mid = _meeting(db, u)
    mem = db.invite_member(mid, "b@x.vn", u["id"])
    db.set_assignment(mid, "a_001", mem["id"], u["id"])
    db.db().execute("PRAGMA foreign_keys = ON")
    db.delete_meeting(mid, u["id"])
    assert db.list_members(mid) == []
    assert db.list_assignments(mid) == {}


# ---- Luật khớp tên tự động: chỗ dễ sai nhất ---- #

def test_auto_assign_exact_full_name(db):
    u = _user(db)
    mid = _meeting(db, u)
    m = db.invite_member(mid, "bich@x.vn", u["id"], display_name="Trần Thị Bích")
    assert db.auto_assign(mid, u["id"]) == 1
    assert db.list_assignments(mid)["a_001"]["member_id"] == m["id"]
    assert db.list_assignments(mid)["a_001"]["source"] == "auto"


def test_auto_assign_matches_by_last_name(db):
    """Biên bản hay chỉ ghi tên riêng ("Bích"), thành viên ghi tên đầy đủ."""
    u = _user(db)
    mid = _meeting(db, u, tasks=[{"id": "a_001", "task": "V", "assignee": "Bích"}])
    m = db.invite_member(mid, "bich@x.vn", u["id"], display_name="Trần Thị Bích")
    assert db.auto_assign(mid, u["id"]) == 1
    assert db.list_assignments(mid)["a_001"]["member_id"] == m["id"]


def test_auto_assign_is_case_and_space_insensitive(db):
    u = _user(db)
    mid = _meeting(db, u, tasks=[{"id": "a_001", "task": "V", "assignee": "  trần thị BÍCH "}])
    db.invite_member(mid, "b@x.vn", u["id"], display_name="Trần Thị Bích")
    assert db.auto_assign(mid, u["id"]) == 1


def test_auto_assign_skips_when_two_people_share_a_name(db):
    """Thà để trống còn hơn gán sai người cho một cam kết."""
    u = _user(db)
    mid = _meeting(db, u, tasks=[{"id": "a_001", "task": "V", "assignee": "Tuấn"}])
    db.invite_member(mid, "t1@x.vn", u["id"], display_name="Nguyễn Anh Tuấn")
    db.invite_member(mid, "t2@x.vn", u["id"], display_name="Lê Minh Tuấn")
    assert db.auto_assign(mid, u["id"]) == 0
    assert db.list_assignments(mid) == {}


def test_auto_assign_never_overwrites_existing(db):
    u = _user(db)
    mid = _meeting(db, u)
    right = db.invite_member(mid, "bich@x.vn", u["id"], display_name="Trần Thị Bích")
    other = db.invite_member(mid, "khac@x.vn", u["id"], display_name="Người Khác")
    db.set_assignment(mid, "a_001", other["id"], u["id"], source="manual")
    assert db.auto_assign(mid, u["id"]) == 0
    assert db.list_assignments(mid)["a_001"]["member_id"] == other["id"]


def test_auto_assign_ignores_tasks_without_assignee(db):
    u = _user(db)
    mid = _meeting(db, u)
    db.invite_member(mid, "x@x.vn", u["id"], display_name="Không Liên Quan")
    assert db.auto_assign(mid, u["id"]) == 0


def test_auto_assign_is_idempotent(db):
    u = _user(db)
    mid = _meeting(db, u)
    db.invite_member(mid, "bich@x.vn", u["id"], display_name="Trần Thị Bích")
    assert db.auto_assign(mid, u["id"]) == 1
    assert db.auto_assign(mid, u["id"]) == 0, "chạy lại không được gán chồng"


def test_auto_assign_survives_missing_minutes(db):
    u = _user(db)
    db.create_meeting(u["id"], meeting_id="mtg_rong", title="Rỗng",
                      meeting_date="2026-01-01", minutes=None, transcript=None)
    assert db.auto_assign("mtg_rong", u["id"]) == 0
    assert db.auto_assign("khong-ton-tai", u["id"]) == 0


def test_auto_assign_ignores_tasks_without_id(db):
    """Biên bản hỏng không được làm sập việc khớp tên."""
    u = _user(db)
    mid = _meeting(db, u, tasks=[{"task": "Thiếu id", "assignee": "Trần Thị Bích"}])
    db.invite_member(mid, "b@x.vn", u["id"], display_name="Trần Thị Bích")
    assert db.auto_assign(mid, u["id"]) == 0


def test_auto_assign_can_match_the_owner(db):
    u = _user(db, "chu@x.vn", "Trần Thị Bích")
    mid = _meeting(db, u)
    owner_row = db.list_members(mid)[0]
    assert db.auto_assign(mid, u["id"]) == 1
    assert db.list_assignments(mid)["a_001"]["member_id"] == owner_row["id"]


# ===========================================================================
#  Thông báo & dữ liệu hỏng
# ===========================================================================

def test_notifications_newest_first(db):
    u = _user(db)
    for i in range(3):
        db.add_notification(u["id"], f"Thông báo {i}")
        time.sleep(0.005)
    items = db.list_notifications(u["id"])
    assert [n["title"] for n in items] == ["Thông báo 2", "Thông báo 1", "Thông báo 0"]


def test_notifications_are_per_user(db):
    a, b = _user(db, "a@x.vn"), _user(db, "b@x.vn", "B")
    db.add_notification(a["id"], "Của A")
    assert db.list_notifications(b["id"]) == []
    assert db.delete_notification(db.list_notifications(a["id"])[0]["id"], b["id"]) is False
    assert db.clear_notifications(b["id"]) == 0
    assert len(db.list_notifications(a["id"])) == 1


def test_meeting_with_corrupt_json_does_not_crash(db):
    """Một hàng hỏng phải trả None, không được làm sập cả danh sách."""
    u = _user(db)
    mid = _meeting(db, u)
    db.db().execute("UPDATE meetings SET minutes = ? WHERE id = ?", ("{hỏng", mid))
    db.db().commit()
    row = db.get_meeting_row(mid)
    assert row["minutes"] is None
    assert len(db.list_meetings_for_user(u["id"])) == 1


def test_meeting_status_scoped_to_owner(db):
    a = _user(db, "a@x.vn")
    b = _user(db, "b@x.vn", "B")
    mid = _meeting(db, a)
    assert db.set_meeting_status(mid, b["id"], "approved") is False
    assert db.get_meeting_row(mid)["status"] == "pending"
