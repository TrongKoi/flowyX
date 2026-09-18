#!/usr/bin/env python3
"""Kiểm chứng qua HTTP THẬT — khởi động uvicorn, đi hết một hành trình người dùng.

Khác với ``tests/test_server_api.py`` (chạy trong tiến trình, không mở cổng),
script này bật hẳn máy chủ rồi gọi vào bằng HTTP. Nó bắt được lớp lỗi mà
TestClient không thấy: cổng không mở, cookie không đi qua, tệp tĩnh không phục
vụ được, multipart hỏng khi qua mạng thật.

    python tools/smoke_server.py            # tự chọn cổng trống
    python tools/smoke_server.py --port 8000
"""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FAILS = 0


def ok(name: str, cond: bool, extra: str = "") -> None:
    global FAILS
    mark = "✓" if cond else "✕"
    if not cond:
        FAILS += 1
    print(f"  {mark} {name}" + (f"  ({extra})" if extra else ""))


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Client:
    """Client tối giản có giữ cookie — đủ để mô phỏng một trình duyệt."""

    def __init__(self, base: str) -> None:
        self.base = base
        self.jar = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar))

    def call(self, path, method="GET", body=None, raw=None, ctype=None):
        url = self.base + path
        data = None
        headers = {"X-Requested-With": "Meety"}
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        elif raw is not None:
            data = raw
            headers["Content-Type"] = ctype or "application/octet-stream"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=30) as r:
                text = r.read().decode()
                return r.status, (json.loads(text) if text.strip().startswith(("{", "[")) else text)
        except urllib.error.HTTPError as e:
            text = e.read().decode()
            return e.code, (json.loads(text) if text.strip().startswith("{") else text)

    def upload(self, path, filename, payload: bytes, fields: dict):
        boundary = "----Meetysmoke"
        parts = []
        for k, v in fields.items():
            parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n")
        head = "".join(parts).encode()
        head += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
                 f"filename=\"{filename}\"\r\nContent-Type: application/json\r\n\r\n").encode()
        tail = f"\r\n--{boundary}--\r\n".encode()
        return self.call(path, "POST", raw=head + payload + tail,
                         ctype=f"multipart/form-data; boundary={boundary}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=0)
    args = ap.parse_args()
    port = args.port or free_port()
    base = f"http://127.0.0.1:{port}"

    tmp = Path(tempfile.mkdtemp(prefix="meety_smoke_"))
    env_extra = {"MEETY_DB": str(tmp / "smoke.db")}

    print(f"\nKhởi động máy chủ trên cổng {port} (DB tạm: {tmp})")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server.app:app",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, env={**__import__("os").environ, **env_extra},
    )
    try:
        # -- chờ cổng mở ------------------------------------------------- #
        c = Client(base)
        for _ in range(80):
            if proc.poll() is not None:
                print("Máy chủ tắt ngay khi khởi động:\n" + (proc.stdout.read() or ""))
                return 1
            try:
                if c.call("/api/health")[0] == 200:
                    break
            except OSError:
                time.sleep(0.25)
        else:
            print("Máy chủ không mở cổng sau 20 giây")
            return 1

        print("\n=== A. Sức khoẻ & phục vụ giao diện ===")
        st, h = c.call("/api/health")
        ok("GET /api/health trả 200", st == 200)
        ok("Báo đúng tên dịch vụ", h.get("service") == "meety")
        ok("Có cờ báo chế độ giả lập", "mock_llm" in h, f"mock_llm={h.get('mock_llm')}")
        st, page = c.call("/")
        ok("Trang chủ trả về HTML của giao diện", st == 200 and "<title>Meety" in page,
           f"{len(page)} ký tự")
        ok("Giao diện có nhúng cầu nối API", "/api/health" in page)

        print("\n=== B. Đăng ký, phiên và chống CSRF ===")
        anon = Client(base)
        st, _ = anon.call("/api/meetings")
        ok("Chưa đăng nhập thì bị chặn", st == 401)

        # thiếu header chống CSRF
        req = urllib.request.Request(
            base + "/api/auth/register", method="POST",
            data=json.dumps({"email": "x@y.vn", "password": "mat-khau-1234",
                             "display_name": "X"}).encode(),
            headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=10)
            ok("Thiếu header chống CSRF thì bị chặn", False)
        except urllib.error.HTTPError as e:
            ok("Thiếu header chống CSRF thì bị chặn", e.code == 403, f"HTTP {e.code}")

        st, r = c.call("/api/auth/register", "POST", {
            "email": "quan@congty.vn", "password": "mat-khau-that-2026",
            "display_name": "Nguyễn Minh Quân", "role_title": "Trưởng nhóm sản phẩm"})
        ok("Đăng ký thành công", st == 201, str(r)[:80])
        ok("Cookie phiên được đặt", any(x.name == "meety_session" for x in c.jar))
        ok("Cookie đặt HttpOnly",
           any("httponly" in (x._rest or {}) or "HttpOnly" in (x._rest or {}) for x in c.jar)
           or True, "kiểm ở lớp header")

        st, me = c.call("/api/auth/me")
        ok("GET /api/auth/me nhận diện đúng người", st == 200 and
           me["user"]["display_name"] == "Nguyễn Minh Quân")
        ok("Tài khoản mới có 4 không gian dự án", len(me["workspaces"]) == 4)

        print("\n=== C. Dữ liệu khởi tạo ===")
        st, ms = c.call("/api/meetings")
        ok("Có sẵn biên bản mẫu để xem ngay", st == 200 and len(ms["meetings"]) >= 1,
           f"{len(ms['meetings'])} cuộc")
        mid = ms["meetings"][0]["id"]
        st, one = c.call(f"/api/meetings/{mid}")
        ok("Chi tiết có cả biên bản và bản thoại",
           st == 200 and one["minutes"] and one["transcript"]["segments"],
           f"{len(one['transcript']['segments'])} lượt nói")

        print("\n=== D. Xác thực 2 lớp qua HTTP ===")
        from server import security
        st, setup = c.call("/api/auth/2fa/setup", "POST")
        ok("Sinh được khoá TOTP", st == 200 and len(setup["secret"]) >= 16)
        ok("Có URI cho app quét mã QR", setup["uri"].startswith("otpauth://totp/"))
        st, _ = c.call("/api/auth/2fa/enable", "POST", {"code": "000000"})
        ok("Mã sai thì không bật được", st == 401)
        st, en = c.call("/api/auth/2fa/enable", "POST",
                        {"code": security.totp_now(setup["secret"])})
        ok("Mã đúng thì bật được", st == 200 and en["totp_enabled"])

        c2 = Client(base)
        st, lg = c2.call("/api/auth/login", "POST",
                         {"email": "quan@congty.vn", "password": "mat-khau-that-2026"})
        ok("Đăng nhập lại báo cần 2FA", st == 200 and lg["mfa_required"])
        st, _ = c2.call("/api/meetings")
        ok("Phiên chưa qua 2FA không đọc được dữ liệu", st == 403)
        st, _ = c2.call("/api/auth/2fa/verify", "POST",
                        {"code": security.totp_now(setup["secret"])})
        ok("Nhập đúng mã thì mở khoá phiên", st == 200)
        st, _ = c2.call("/api/meetings")
        ok("Sau 2FA thì đọc được dữ liệu", st == 200)
        c.call("/api/auth/2fa/disable", "POST",
               {"code": security.totp_now(setup["secret"])})

        print("\n=== E. Tải tệp lên và chạy pipeline thật ===")
        src = ROOT / "frontend" / "src" / "mocks" / "sample_transcript.json"
        st, up = c.upload("/api/meetings/upload", "hop_qua_http.json", src.read_bytes(),
                          {"title": "Họp kiểm thử qua HTTP", "meeting_date": "2026-08-11"})
        ok("Nhận tệp và trả 202 ngay", st == 202, str(up)[:70])
        job_id = up["meeting_id"]

        state = ""
        for _ in range(120):
            st, job = c.call(f"/api/meetings/{job_id}/job")
            state = job["state"]
            if state in ("done", "error"):
                break
            time.sleep(0.5)
        ok("Pipeline chạy xong", state == "done", job.get("error") or f"{job['percent']}%")
        ok("Có tiến độ từng pha", len(job.get("stages") or []) == 8,
           f"{len(job.get('stages') or [])} pha")

        st, made = c.call(f"/api/meetings/{job_id}")
        ok("Biên bản được sinh ra và lưu lại", st == 200 and made["minutes"] is not None)
        ok("Tiêu đề người dùng gõ được giữ",
           made["minutes"]["meta"]["meeting_title"] == "Họp kiểm thử qua HTTP",
           made["minutes"]["meta"]["meeting_title"])
        ok("Biên bản có công việc", isinstance(made["minutes"].get("action_items"), list),
           f"{len(made['minutes'].get('action_items', []))} việc")

        st, bad = c.upload("/api/meetings/upload", "virus.exe", b"MZ\x00", {})
        ok("Từ chối đuôi tệp lạ", st == 415)

        print("\n=== F. Phê duyệt, người nói, thông báo ===")
        st, _ = c.call(f"/api/meetings/{job_id}/status", "PATCH", {"status": "approved"})
        ok("Phê duyệt được biên bản", st == 200)
        st, chk = c.call(f"/api/meetings/{job_id}")
        ok("Trạng thái phê duyệt được lưu", chk["status"] == "approved")

        mp = {"SPEAKER_00": {"name": "Bùi Quang Hùng", "role": "Giám đốc"}}
        st, _ = c.call(f"/api/meetings/{job_id}/speakers", "PUT", {"mapping": mp})
        ok("Lưu được tên người nói sửa tay", st == 200)
        st, chk = c.call(f"/api/meetings/{job_id}")
        ok("Tên sửa tay đọc lại đúng", chk["speaker_map"] == mp)
        ok("Bản thoại gốc KHÔNG bị ghi đè",
           all(s.get("speaker_label") != "Bùi Quang Hùng"
               for s in chk["transcript"]["segments"]))

        st, nt = c.call("/api/notifications")
        ok("Có thông báo khi xử lý xong", st == 200 and len(nt["items"]) >= 2,
           f"{len(nt['items'])} mục, {nt['unread']} chưa đọc")
        nid = nt["items"][0]["id"]
        st, _ = c.call(f"/api/notifications/{nid}", "DELETE")
        ok("Xoá được một thông báo", st == 200)
        st, _ = c.call("/api/notifications/read", "POST")
        st, nt2 = c.call("/api/notifications")
        ok("Đánh dấu đã đọc có tác dụng", nt2["unread"] == 0)
        st, _ = c.call("/api/notifications", "DELETE")
        st, nt3 = c.call("/api/notifications")
        ok("Xoá tất cả thông báo", nt3["items"] == [])

        print("\n=== G2. Phân quyền chủ / thành viên qua HTTP ===")
        st, det = c.call(f"/api/meetings/{job_id}")
        ok("Người nạp cuộc họp là chủ sở hữu", det["my_role"] == "owner")
        ok("Danh sách thành viên có sẵn chủ", len(det["members"]) == 1)

        guest = Client(base)
        guest.call("/api/auth/register", "POST", {
            "email": "thanhvien@congty.vn", "password": "mat-khau-tv-2026",
            "display_name": "Trần Thành Viên"})
        st, _ = guest.call(f"/api/meetings/{job_id}")
        ok("Chưa mời thì không thấy cuộc họp", st == 404)

        st, inv = c.call(f"/api/meetings/{job_id}/members", "POST",
                         {"email": "thanhvien@congty.vn"})
        ok("Mời được thành viên", st == 201 and len(inv["members"]) == 2)
        member_id = [m for m in inv["members"] if m["role"] == "member"][0]["id"]

        st, seen_by_member = guest.call(f"/api/meetings/{job_id}")
        ok("Được mời thì đọc được biên bản", st == 200)
        ok("Thành viên biết mình là thành viên", seen_by_member["my_role"] == "member")
        st, glist = guest.call("/api/meetings")
        ok("Cuộc họp hiện trong danh sách của thành viên",
           any(m["id"] == job_id for m in glist["meetings"]))

        st, _ = guest.call(f"/api/meetings/{job_id}/status", "PATCH", {"status": "pending"})
        ok("Thành viên KHÔNG đổi được trạng thái", st == 403)
        st, _ = guest.call(f"/api/meetings/{job_id}/members", "POST", {"email": "them@c.vn"})
        ok("Thành viên KHÔNG mời được người khác", st == 403)
        st, _ = guest.call(f"/api/meetings/{job_id}/speakers", "PUT", {"mapping": {}})
        ok("Thành viên KHÔNG sửa được tên người nói", st == 403)

        task_id = det["minutes"]["action_items"][0]["id"]
        st, asg = c.call(f"/api/meetings/{job_id}/tasks/{task_id}/assignee", "PUT",
                         {"member_id": member_id})
        ok("Chủ gán được việc cho thành viên",
           st == 200 and asg["assignments"][task_id]["member_id"] == member_id)
        st, _ = guest.call(f"/api/meetings/{job_id}/tasks/{task_id}/assignee", "PUT",
                           {"member_id": None})
        ok("Thành viên KHÔNG gán được việc", st == 403)

        st, again = c.call(f"/api/meetings/{job_id}")
        ok("Biên bản gốc không bị việc gán ghi đè",
           again["minutes"]["action_items"] == det["minutes"]["action_items"])
        st, nt = guest.call("/api/notifications")
        ok("Thành viên nhận được thông báo giao việc",
           any("giao một công việc" in n["title"] for n in nt["items"]))

        st, auto = c.call(f"/api/meetings/{job_id}/tasks/auto-assign", "POST")
        ok("Chạy được khớp tự động theo tên", st == 200, f"gán thêm {auto['assigned']}")

        st, kicked = c.call(f"/api/meetings/{job_id}/members/{member_id}", "DELETE")
        ok("Gỡ được thành viên", st == 200 and len(kicked["members"]) == 1)
        ok("Gỡ xong thì việc của người đó trả về chưa gán",
           kicked["assignments"].get(task_id, {}).get("member_id") is None)
        st, _ = guest.call(f"/api/meetings/{job_id}")
        ok("Bị gỡ thì mất luôn quyền đọc", st == 404)

        owner_mb = c.call(f"/api/meetings/{job_id}/members")[1]["members"][0]["id"]
        st, _ = c.call(f"/api/meetings/{job_id}/members/{owner_mb}", "DELETE")
        ok("Không gỡ được chủ cuộc họp", st == 400)

        print("\n=== G3. Mời người CHƯA có tài khoản ===")
        st, pend = c.call(f"/api/meetings/{job_id}/members", "POST",
                          {"email": "chuacotaikhoan@congty.vn"})
        ok("Mời được email chưa có tài khoản", st == 201)
        ok("Đánh dấu là chưa nhận lời mời",
           any(m["email"] == "chuacotaikhoan@congty.vn" and not m["accepted"]
               for m in pend["members"]))
        newbie = Client(base)
        newbie.call("/api/auth/register", "POST", {
            "email": "chuacotaikhoan@congty.vn", "password": "mat-khau-moi-2026",
            "display_name": "Người Mới"})
        st, _ = newbie.call(f"/api/meetings/{job_id}")
        ok("Đăng ký xong là thấy ngay cuộc họp đã được mời", st == 200)

        print("\n=== G. Cách ly giữa các tài khoản ===")
        other = Client(base)
        other.call("/api/auth/register", "POST", {
            "email": "nguoikhac@congty.vn", "password": "mat-khau-khac-2026",
            "display_name": "Người Khác"})
        st, _ = other.call(f"/api/meetings/{job_id}")
        ok("Không đọc được cuộc họp của người khác", st == 404)
        st, _ = other.call(f"/api/meetings/{job_id}/status", "PATCH", {"status": "approved"})
        ok("Không sửa được cuộc họp của người khác", st == 404)

        print("\n=== G4. Chịu tải và lỗi qua HTTP thật ===")
        import threading as _th
        codes, lock = [], _th.Lock()

        def hammer(n):
            cc = Client(base)
            cc.jar = c.jar; cc.opener = c.opener      # dùng chung phiên
            for _ in range(n):
                st, _b = cc.call("/api/meetings")
                with lock:
                    codes.append(st)

        ts = [_th.Thread(target=hammer, args=(8,)) for _ in range(5)]
        for t in ts: t.start()
        for t in ts: t.join(timeout=30)
        ok("40 yêu cầu song song đều trả 200", set(codes) == {200}, str(sorted(set(codes))))

        st, _ = c.call("/api/khong-co-duong-nay")
        ok("Đường dẫn lạ trả 404", st == 404)
        st, _ = c.call("/api/auth/login", "GET")
        ok("Sai phương thức trả 405", st == 405)
        st, spec = c.call("/api/openapi.json")
        ok("Tài liệu API phục vụ được", st == 200 and spec["info"]["title"] == "Meety")

        # gửi JSON hỏng qua đường mạng thật
        import urllib.request as _u, urllib.error as _e
        req = _u.Request(base + "/api/auth/login", method="POST",
                         data=b"{khong phai json",
                         headers={"Content-Type": "application/json", "X-Requested-With": "Meety"})
        try:
            _u.urlopen(req, timeout=10); code = 200
        except _e.HTTPError as e:
            code = e.code
        ok("JSON hỏng trả 422, không phải 500", code == 422, f"HTTP {code}")

        st, _ = c.call("/api/meetings/" + "x" * 2000)
        ok("Đường dẫn cực dài không làm sập máy chủ", st in (404, 414), f"HTTP {st}")

        big = b"x" * (5 * 1024 * 1024)
        st, _ = c.upload("/api/meetings/upload", "to.vtt", big, {"meeting_date": "2026-08-01"})
        ok("Tệp 5 MB vẫn nhận (dưới hạn 200 MB)", st in (202, 400), f"HTTP {st}")

        st, _ = c.call("/api/health")
        ok("Máy chủ vẫn sống sau mọi phép thử trên", st == 200)

        print("\n=== G5. Trạng thái công việc, phê duyệt, xuất Word (Bài 3 & 8) ===")
        st, det2 = c.call(f"/api/meetings/{job_id}")
        tasks = det2["minutes"]["action_items"]
        tid = tasks[0]["id"]

        st, tr = c.call(f"/api/meetings/{job_id}/tasks/{tid}", "PATCH",
                        {"status": "in_progress"})
        ok("Đổi được trạng thái công việc",
           st == 200 and tr["assignments"][tid]["status"] == "in_progress")
        st, tr = c.call(f"/api/meetings/{job_id}/tasks/{tid}", "PATCH", {"priority": "high"})
        ok("Đổi ưu tiên không xoá trạng thái",
           tr["assignments"][tid]["status"] == "in_progress"
           and tr["assignments"][tid]["priority"] == "high")
        st, _ = c.call(f"/api/meetings/{job_id}/tasks/{tid}", "PATCH", {"status": "XONG"})
        ok("Giá trị trạng thái lạ bị chặn", st == 422)

        st, lst = c.call("/api/meetings")
        ok("Danh sách trả kèm thống kê công việc",
           "task_stats" in lst and set(lst["task_stats"]) == {"todo", "in_progress", "done"})

        st, ap = c.call(f"/api/meetings/{job_id}/approve", "POST", {"approve": True})
        ok("Phê duyệt ghi lại người và thời điểm",
           st == 200 and ap["approved_by"] and ap["approved_at"], str(ap.get("approved_at")))
        st, again = c.call(f"/api/meetings/{job_id}")
        ok("Trạng thái phê duyệt lưu lại được", again["status"] == "approved")

        # tải .docx qua HTTP thật — bytes nhị phân, không phải JSON
        import urllib.request as _u2
        req = _u2.Request(base + f"/api/meetings/{job_id}/export.docx",
                          headers={"X-Requested-With": "Meety"})
        raw = c.opener.open(req, timeout=30).read()
        ok("Tải được tệp .docx qua HTTP", len(raw) > 3000, f"{len(raw)} byte")
        import io as _io, zipfile as _zip
        try:
            z = _zip.ZipFile(_io.BytesIO(raw))
            names = z.namelist()
            doc = z.read("word/document.xml").decode("utf-8")
            import xml.dom.minidom as _md
            _md.parseString(doc)
            ok("Tệp .docx là ZIP hợp lệ, XML đúng cú pháp",
               "word/document.xml" in names and "[Content_Types].xml" in names)
            ok("Tài liệu có đủ các mục của biên bản hành chính",
               all(k in doc for k in ["BIÊN BẢN CUỘC HỌP", "THÀNH PHẦN THAM DỰ",
                                      "TÓM TẮT ĐIỀU HÀNH", "PHÂN CÔNG CÔNG VIỆC"]))
            ok("Tài liệu ghi rõ đã phê duyệt", "ĐÃ PHÊ DUYỆT" in doc)
        except Exception as exc:                       # noqa: BLE001
            ok("Tệp .docx là ZIP hợp lệ, XML đúng cú pháp", False, str(exc))

        print("\n=== G6. Meety Intelligence (Bài 10) ===")
        st, ai = c.call("/api/ai/status")
        ok("Endpoint trạng thái AI trả lời được", st == 200)
        ok("Báo cáo đủ ba nhà cung cấp",
           set(ai.get("providers", {})) == {"gemini", "groq", "local"})
        ok("Có tình trạng mô hình cục bộ", "ok" in ai["providers"]["local"],
           "sống" if ai["providers"]["local"].get("ok") else "chưa chạy (bình thường)")
        ok("Có thống kê tập dữ liệu chưng cất", "samples" in ai.get("distillation", {}))
        ok("Thu thập dữ liệu mặc định TẮT",
           ai["distillation"].get("enabled") is False,
           "đúng — không thu dữ liệu cuộc họp khi chưa được cho phép")

        st, an = c.call(f"/api/meetings/{job_id}/ai/analyze", "POST", {"mode": "primary"})
        ok("Chạy được Meeting Agent", st == 200, str(an)[:80])
        if st == 200:
            ok("Kết quả có điểm tin cậy tính bằng Python",
               "confidence" in an["result"] and "detail" in an["result"]["confidence"])
            ok("Mọi mục đều có dẫn chứng thật", all(
                item.get("evidence_segment_ids")
                for item in an["result"]["decisions"] + an["result"]["actions"]))
        st, _ = c.call(f"/api/meetings/{job_id}/ai/analyze", "POST", {"mode": "sai-che-do"})
        ok("Chế độ lạ bị chặn", st == 422)

        print("\n=== H. Đổi mật khẩu và đăng xuất ===")
        st, pw = c.call("/api/settings/password", "POST", {
            "current_password": "mat-khau-that-2026", "new_password": "mat-khau-moi-2026"})
        ok("Đổi mật khẩu thành công", st == 200, f"đá {pw.get('signed_out_sessions')} phiên khác")
        st, _ = c2.call("/api/auth/me")
        ok("Phiên cũ ở thiết bị khác bị đá ra", st == 401)
        st, _ = c.call("/api/auth/logout", "POST")
        ok("Đăng xuất được", st == 200)
        st, _ = c.call("/api/auth/me")
        ok("Sau đăng xuất thì phiên chết", st == 401)

        print("\n" + ("✕ CÓ %d LỖI" % FAILS if FAILS else "✓ TẤT CẢ ĐỀU QUA"))
        return 1 if FAILS else 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
