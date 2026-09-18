/* =========================================================================
   KIỂM THỬ NỐI MÁY CHỦ THẬT

   Vì sao bộ này phải tồn tại
   --------------------------
   Trước bộ này, dự án có ba lớp kiểm thử và **không lớp nào phủ được chỗ nối
   giữa frontend và máy chủ**:

     tests/frontend/dom_test.js   frontend ở chế độ RỜI máy chủ (dữ liệu nhúng)
     tools/smoke_server.py        máy chủ thật, nhưng KHÔNG có frontend
     tests/test_*.py              từng tầng backend riêng

   Khe hở đó để lọt một lỗi làm hỏng hoàn toàn việc đăng nhập: `/api/meetings`
   cố ý KHÔNG trả `transcript` (nó nặng gấp nhiều lần phần biên bản và trang
   tổng quan không cần), nhưng thẻ cuộc họp lại gọi `resolveSpeakers(mt.transcript)`
   để vẽ avatar. Ở chế độ rời máy chủ mọi cuộc họp đều có transcript nhúng sẵn
   nên lỗi không bao giờ lộ. Nối máy chủ thật thì `hubView()` ném ngay, người
   dùng kẹt ở nút "Đang xử lý…" với server log toàn 200 OK.

   Bài học: dữ liệu nhúng và dữ liệu máy chủ có **hình dạng khác nhau**. Mỗi
   khác biệt về hình dạng là một chỗ có thể vỡ, và chỉ bộ này nhìn thấy.

   Cách chạy
   ---------
       npm install jsdom
       node tests/frontend/online_test.js

   Bộ này tự bật uvicorn, tự tạo tài khoản, tự dọn DB tạm khi xong.
   ========================================================================= */

const { JSDOM } = require("jsdom");
const { spawn, spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");
const net = require("net");

const ROOT = path.resolve(__dirname, "..", "..");
const H = { "X-Requested-With": "Meety" };
const PREVIEW = path.join(ROOT, "mm-ai-preview.html");
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "meety_online_"));
const PW = "meety-online-2026";
const EMAIL = "online@meety.vn";

let FAILS = 0;
const ok = (name, cond, extra = "") => {
  console.log(`  ${cond ? "✓" : "✕"} ${name}${extra ? `  (${extra})` : ""}`);
  if (!cond) FAILS++;
};

function freePort() {
  return new Promise(res => {
    const s = net.createServer();
    s.listen(0, "127.0.0.1", () => { const p = s.address().port; s.close(() => res(p)); });
  });
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

/* ---------------------------------------------------------------------------
   jsdom không có `fetch`. Gắn một bản dùng fetch của Node và TỰ GIỮ COOKIE —
   phiên đăng nhập nằm trong cookie HttpOnly, không có nó thì mọi lời gọi sau
   khi đăng nhập đều trả 401 và bộ này chẳng kiểm được gì.
   --------------------------------------------------------------------------- */
function makeFetch(base, jar) {
  return async (url, opt = {}) => {
    const full = String(url).startsWith("http") ? String(url) : base + url;
    const headers = { ...(opt.headers || {}) };
    if (jar.cookie) headers["Cookie"] = jar.cookie;
    const res = await fetch(full, { ...opt, headers, redirect: "manual" });
    const setCookie = res.headers.getSetCookie ? res.headers.getSetCookie()
                                               : [res.headers.get("set-cookie")].filter(Boolean);
    for (const c of setCookie) {
      const pair = c.split(";")[0];
      if (pair.startsWith("meety_session=")) jar.cookie = pair;
    }
    const buf = Buffer.from(await res.arrayBuffer());
    return {
      ok: res.ok, status: res.status, statusText: res.statusText,
      headers: res.headers,
      text: async () => buf.toString("utf8"),
      json: async () => JSON.parse(buf.toString("utf8")),
      blob: async () => ({ size: buf.length, type: res.headers.get("content-type") || "" }),
    };
  };
}

async function main() {
  if (!fs.existsSync(PREVIEW)) {
    console.log("Chưa có mm-ai-preview.html — chạy: python tools/build_preview.py --out mm-ai-preview.html");
    return 1;
  }

  const port = await freePort();
  const base = `http://127.0.0.1:${port}`;
  const dbPath = path.join(TMP, "online.db");

  console.log(`\nKhởi động máy chủ ở cổng ${port} (DB tạm: ${dbPath})`);
  const py = process.env.PYTHON || "python3";
  const srv = spawn(py, ["-m", "uvicorn", "server.app:app", "--host", "127.0.0.1",
                         "--port", String(port), "--log-level", "warning"],
                    { cwd: ROOT, env: { ...process.env, MEETY_DB: dbPath }, stdio: "pipe" });
  let srvErr = "";
  srv.stderr.on("data", d => { srvErr += d.toString(); });

  const jar = {};
  const api = makeFetch(base, jar);
  const call = async (p, method = "GET", body) => {
    const r = await api(p, {
      method,
      headers: { "X-Requested-With": "Meety",
                 ...(body ? { "Content-Type": "application/json" } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    let data = null;
    try { data = await r.json(); } catch { data = null; }
    return [r.status, data];
  };

  try {
    // -- chờ cổng mở ------------------------------------------------------ #
    let up = false;
    for (let i = 0; i < 80; i++) {
      try { if ((await call("/api/health"))[0] === 200) { up = true; break; } } catch {}
      await sleep(250);
    }
    if (!up) { console.log("Máy chủ không mở cổng:\n" + srvErr.slice(0, 800)); return 1; }

    // -- dựng dữ liệu qua API thật ---------------------------------------- #
    console.log("\n=== A. Chuẩn bị dữ liệu trên máy chủ ===");
    let [st] = await call("/api/auth/register", "POST",
      { email: EMAIL, password: PW, display_name: "Người Dùng Nối Mạng" });
    ok("Đăng ký được tài khoản", st === 201, `HTTP ${st}`);

    const seed = spawnSync(py, ["tools/seed_data.py", "--email", EMAIL],
                           { cwd: ROOT, env: { ...process.env, MEETY_DB: dbPath },
                             encoding: "utf8" });
    ok("Nạp được cuộc họp mẫu", seed.status === 0,
       (seed.stdout || seed.stderr || "").trim().split("\n").pop());

    const [, list] = await call("/api/meetings");
    ok("Máy chủ có cuộc họp để hiển thị", (list.meetings || []).length >= 2,
       `${(list.meetings || []).length} cuộc`);
    ok("Danh sách CỐ Ý không kèm bản thoại — đây là chỗ frontend hay vỡ",
       list.meetings.every(m => m.transcript === undefined));

    // -- nạp frontend thật, trỏ vào máy chủ thật -------------------------- #
    console.log("\n=== B. Frontend thật nói chuyện với máy chủ thật ===");
    const errs = [];
    const dom = new JSDOM(fs.readFileSync(PREVIEW, "utf8"), {
      runScripts: "dangerously", pretendToBeVisual: true, url: base + "/",
      beforeParse(w) {
        w.scrollTo = () => {}; w.alert = () => {};
        w.HTMLElement.prototype.scrollIntoView = function () {};
        w.navigator.mediaDevices = { getUserMedia: () => Promise.reject(new Error("no mic")) };
        w.URL.createObjectURL = () => "blob:giả-lập";
        w.URL.revokeObjectURL = () => {};
        w.fetch = makeFetch(base, jar);
        w.addEventListener("error", e =>
          errs.push(e.error ? (e.error.stack || e.error.message) : e.message));
      },
    });
    const w = dom.window, d = w.document;
    const $ = s => d.querySelector(s);
    const $$ = s => [...d.querySelectorAll(s)];
    const click = el => el && el.dispatchEvent(new w.Event("click", { bubbles: true }));
    const byText = (sel, t) => $$(sel).find(e => (e.textContent || "").includes(t));
    /* body.textContent gộp cả nội dung <script> — tức là toàn bộ mã nguồn.
       Đo trên đó thì mọi phép kiểm về chữ hiển thị đều báo sai. */
    const seen = () => {
      const c = d.body.cloneNode(true);
      [...c.querySelectorAll("script,style")].forEach(e => e.remove());
      return c.textContent;
    };

    await sleep(1200);
    ok("Frontend dò ra máy chủ", w.eval("API.online") === true);
    ok("Không có lỗi JS lúc khởi động", errs.length === 0,
       errs[0] ? errs[0].split("\n").slice(0, 3).join(" ") : "");

    // Cookie đã có sẵn từ lúc đăng ký → frontend phải vào thẳng, không bắt
    // đăng nhập lại.
    ok("Vào thẳng trang tổng quan nhờ phiên còn hiệu lực",
       w.eval("state.view") === "hub" && w.eval("state.authed") === true,
       `view=${w.eval("state.view")} authed=${w.eval("state.authed")}`);
    ok("KHÔNG kẹt ở nút Đang xử lý", !seen().includes("Đang xử lý"));
    ok("Nạp đúng số cuộc họp từ máy chủ",
       w.eval("MEETINGS.length") === list.meetings.length,
       `${w.eval("MEETINGS.length")} cuộc`);

    console.log("\n=== C. Trang tổng quan dựng từ dữ liệu máy chủ ===");
    ok("Thẻ cuộc họp hiện ra", $$(".mcard").length === list.meetings.length,
       `${$$(".mcard").length} thẻ`);
    ok("Thẻ vẽ được avatar dù CHƯA có bản thoại",
       $$(".mcard .av").length > 0, `${$$(".mcard .av").length} avatar`);
    ok("Gắn thẻ ngữ nghĩa chạy được khi chưa có bản thoại",
       (() => { try { return w.eval("MEETINGS.map(semanticTags).flat().length") > 0; }
                catch { return false; } })());
    ok("Bốn thẻ KPI dựng từ số liệu máy chủ", $$(".kpi").length === 4);
    ok("Tỷ lệ hoàn thành tính được", /Tỷ lệ hoàn thành/.test(seen()));
    ok("Tên người dùng lấy từ máy chủ", w.eval("state.user.email") === "online@meety.vn",
       w.eval("state.user.name"));

    console.log("\n=== D. Mở biên bản: nạp bản thoại theo yêu cầu ===");
    click($$(".mcard")[0]);
    await sleep(900);
    ok("Chuyển sang trang chi tiết", w.eval("state.view") === "meeting");
    // Lấy id của cuộc họp ĐANG MỞ thay vì đoán: frontend gom nhóm theo dự án
    // nên thẻ đầu trên màn hình không nhất thiết là cuộc họp đầu trong danh
    // sách máy chủ trả về.
    const openId = w.eval("currentMeeting().id");
    ok("Bản thoại được nạp thêm khi mở",
       w.eval("!!(currentMeeting() && currentMeeting().transcript)"));
    ok("Đủ 6 khối nội dung", $$("section[id^=sec-]").length === 6,
       `${$$("section[id^=sec-]").length} khối`);
    ok("Bản thoại hiện đủ lượt nói", $$("#sec-transcript .seg").length > 5,
       `${$$("#sec-transcript .seg").length} lượt`);
    ok("Biết mình là chủ cuộc họp", w.eval("myRole()") === "owner");
    ok("Không có lỗi JS khi mở biên bản", errs.length === 0,
       errs[0] ? errs[0].split("\n")[0] : "");

    console.log("\n=== E. Ghi dữ liệu qua máy chủ ===");
    const stPill = $("#sec-actions .pill[class*=st-]");
    const before = stPill ? stPill.textContent.trim() : "";
    click(stPill);
    await sleep(700);
    const [, afterTask] = await call(`/api/meetings/${openId}`);
    const anyStatus = Object.values(afterTask.assignments || {})
                            .some(a => a.status && a.status !== "todo");
    ok("Đổi trạng thái công việc lưu được xuống máy chủ", anyStatus,
       `${before} → ${$("#sec-actions .pill[class*=st-]").textContent.trim()}`);

    const inv = $("#inv-email");
    if (inv) {
      inv.value = "nguoiduocmoi@congty.vn";
      click(byText("#sec-members .btn", "Mời thành viên"));
      await sleep(900);
      const [, mem] = await call(`/api/meetings/${openId}/members`);
      ok("Mời thành viên lưu được xuống máy chủ",
         (mem.members || []).some(m => m.email === "nguoiduocmoi@congty.vn"),
         `${(mem.members || []).length} người`);
      ok("Danh sách trên màn hình cập nhật theo",
         seen().includes("nguoiduocmoi@congty.vn"));
    } else {
      ok("Có ô mời thành viên", false, "không tìm thấy #inv-email");
    }

    click(byText("button", "Phê duyệt biên bản"));
    await sleep(300);
    ok("Phê duyệt mở modal xác nhận", seen().includes("Xác nhận phê duyệt"));
    click(byText(".modal-foot .btn", "Xác nhận phê duyệt"));
    await sleep(900);
    const [, approved] = await call(`/api/meetings/${openId}`);
    ok("Phê duyệt ghi được xuống máy chủ", approved.status === "approved",
       approved.approved_by || "");
    ok("Màn hình hiện trạng thái đã phê duyệt", seen().includes("ĐÃ PHÊ DUYỆT"));

    console.log("\n=== F. Xuất Word qua HTTP thật ===");
    const docx = await api(`/api/meetings/${openId}/export.docx`,
                           { headers: { "X-Requested-With": "Meety" } });
    ok("Tải được tệp .docx", docx.status === 200);
    ok("Đúng kiểu MIME của Word",
       (docx.headers.get("content-type") || "").includes("wordprocessingml"));
    const blob = await docx.blob();
    ok("Tệp có nội dung thật", blob.size > 3000, `${blob.size} byte`);

    console.log("\n=== G. Thông báo và đăng xuất ===");
    click($$(".icon-btn")[0]);
    await sleep(300);
    ok("Bảng thông báo lấy dữ liệu từ máy chủ", $$(".notif").length > 0,
       `${$$(".notif").length} mục`);
    const un = $$(".notif.unread").length;
    if (un) {
      click(byText(".notif-head .notif-act", "Đã đọc hết"));
      await sleep(700);
      const [, nt] = await call("/api/notifications");
      ok("Đánh dấu đã đọc lưu được xuống máy chủ", nt.unread === 0, `còn ${nt.unread}`);
    } else {
      ok("Đánh dấu đã đọc lưu được xuống máy chủ", true, "không có mục chưa đọc");
    }

    click($(".avatar-btn"));
    await sleep(200);
    click(byText(".menu-item", "Đăng xuất"));
    await sleep(700);
    ok("Đăng xuất về màn hình đăng nhập", seen().includes("Đăng nhập"));
    const [meSt] = await call("/api/auth/me");
    ok("Phiên trên máy chủ đã bị huỷ", meSt === 401, `HTTP ${meSt}`);

    console.log("\n=== H. Đăng nhập lại từ đầu bằng biểu mẫu ===");
    const emailBox = $("#in-email"), passBox = $("#in-pass");
    ok("Có biểu mẫu đăng nhập", !!emailBox && !!passBox);
    if (emailBox && passBox) {
      emailBox.value = EMAIL;
      passBox.value = PW;
      click(byText(".panel .btn", "Tiếp tục"));
      await sleep(1800);
      ok("Đăng nhập bằng biểu mẫu vào được trang tổng quan",
         w.eval("state.view") === "hub" && w.eval("state.authed") === true,
         `view=${w.eval("state.view")}`);
      ok("KHÔNG kẹt ở Đang xử lý sau khi đăng nhập",
         !seen().includes("Đang xử lý") && w.eval("state.authBusy") === false);
      ok("Thấy lại đủ cuộc họp", $$(".mcard").length === list.meetings.length);
    }

    console.log("\n=== I. Sai mật khẩu báo lỗi tử tế ===");
    click($(".avatar-btn"));
    await sleep(150);
    click(byText(".menu-item", "Đăng xuất"));
    await sleep(600);
    $("#in-email").value = EMAIL;
    $("#in-pass").value = "sai-mat-khau-hoan-toan";
    click(byText(".panel .btn", "Tiếp tục"));
    await sleep(1500);
    ok("Báo lỗi ngay trên màn hình", /không đúng|Email hoặc mật khẩu/i.test(seen()));
    ok("Nút trở lại bình thường, không kẹt",
       w.eval("state.authBusy") === false && !seen().includes("Đang xử lý"));
    ok("Vẫn ở màn hình đăng nhập", w.eval("state.authed") === false);

    console.log("\n=== K. Hai tài khoản: phân quyền và đồng bộ (Bài 3 & 4) ===");
    // Dựng hai tài khoản kiểm thử rồi mở HAI phiên trình duyệt song song.
    const seed2 = spawnSync(py, ["tools/seed_data.py", "--accounts"],
                            { cwd: ROOT, env: { ...process.env, MEETY_DB: dbPath },
                              encoding: "utf8" });
    ok("Dựng được hai tài khoản kiểm thử", seed2.status === 0);

    const openAs = async (email, pw) => {
      const j = {}; const f = makeFetch(base, j);
      const lg = await f("/api/auth/login", { method: "POST",
        headers: { ...H, "Content-Type": "application/json" },
        body: JSON.stringify({ email, password: pw }) });
      const errs = [];
      const dm = new JSDOM(fs.readFileSync(PREVIEW, "utf8"), {
        runScripts: "dangerously", pretendToBeVisual: true, url: base + "/",
        beforeParse(w) {
          w.scrollTo = () => {}; w.alert = () => {};
          w.HTMLElement.prototype.scrollIntoView = function () {};
          w.navigator.mediaDevices = { getUserMedia: () => Promise.reject(new Error("x")) };
          w.URL.createObjectURL = () => "blob:x"; w.URL.revokeObjectURL = () => {};
          w.fetch = f;
          w.addEventListener("error", e => errs.push(e.error ? e.error.stack : e.message));
        } });
      await sleep(1300);
      return { w: dm.window, d: dm.window.document, api: f, errs, login: lg.status };
    };

    const OWNER = await openAs("owner@meety.ai", "admin123");
    const MEMBER = await openAs("member@meety.ai", "user123");
    ok("Đăng nhập được cả hai tài khoản kiểm thử",
       OWNER.login === 200 && MEMBER.login === 200);

    const mid2 = OWNER.w.eval("MEETINGS[0].id");
    OWNER.w.eval(`openMeeting('${mid2}')`); await sleep(900);
    MEMBER.w.eval(`openMeeting('${mid2}')`); await sleep(900);
    ok("3 · Owner nhận đúng vai trò chủ toạ", OWNER.w.eval("myRole()") === "owner");
    ok("3 · Member nhận đúng vai trò thành viên", MEMBER.w.eval("myRole()") === "member");

    console.log("  -- 3 · quyền lấy từ máy chủ --");
    ok("3 · Owner có quyền chuyển quyền chủ toạ",
       OWNER.w.eval("can('transfer_ownership')") === true);
    ok("3 · Member không có quyền phân quyền nào",
       MEMBER.w.eval("can('promote_co_host')") === false
       && MEMBER.w.eval("can('remove_member')") === false);
    ok("3 · Member không thấy nút thao tác thành viên nào",
       MEMBER.d.querySelectorAll("#sec-members .mem-x").length === 0);
    const ownerMenuBtns = OWNER.d.querySelectorAll("#sec-members .mem-x");
    ok("3 · Owner thấy nút thao tác với thành viên", ownerMenuBtns.length >= 1);
    ownerMenuBtns[0].dispatchEvent(new OWNER.w.Event("click", { bubbles: true }));
    const ownerItems = [...OWNER.d.querySelectorAll(".mem-pop .menu-item")]
      .map(x => x.textContent.replace(/\s+/g, " ").trim());
    ok("3 · Menu chủ toạ có đủ ba mục phân quyền",
       ownerItems.some(t => t.includes("Chỉ định")) &&
       ownerItems.some(t => t.includes("Chuyển quyền")) &&
       ownerItems.some(t => t.includes("Gỡ khỏi")), ownerItems.join(" | "));

    console.log("  -- 4 · Owner gán việc, Member thấy ngay --");
    const memberRowId = OWNER.w.eval(
      `membersOf().find(m => m.email === 'member@meety.ai').id`);
    OWNER.w.eval("state.memMenu = null; render()");
    const selNode = OWNER.d.querySelector("#sec-actions .assign select");
    ok("4 · Owner thấy ô chọn người nhận việc", !!selNode);
    const beforeToast = seen(OWNER.d);
    selNode.value = memberRowId;
    selNode.dispatchEvent(new OWNER.w.Event("change", { bubbles: true }));
    await sleep(1100);
    ok("4 · Gán việc KHÔNG báo lỗi quyền",
       !/Chỉ chủ toạ mới gán|không có quyền|403/i.test(
         seen(OWNER.d).replace(beforeToast, "")),
       (seen(OWNER.d).match(/Đã giao việc cho [^.]*/) || ["(không có toast)"])[0]);

    const [, detail] = await (async () => {
      const r = await OWNER.api(`/api/meetings/${encodeURIComponent(mid2)}`, { headers: H });
      return [r.status, await r.json()];
    })();
    const assignedIds = Object.entries(detail.assignments)
      .filter(([, a]) => a.member_id === memberRowId).map(([t]) => t);
    ok("4 · Máy chủ lưu đúng người nhận", assignedIds.length >= 1, assignedIds.join());

    // Nhịp đồng bộ nền chạy 2,5s/lần — chờ đủ một nhịp, KHÔNG gọi tay.
    await sleep(4000);
    const memberCards = MEMBER.d.querySelectorAll("#sec-actions .card").length;
    ok("4 · Member thấy việc mới mà KHÔNG cần tải lại trang", memberCards >= 1,
       memberCards + " thẻ");
    ok("4 · Id thành viên khớp giữa hai phiên",
       MEMBER.w.eval("myMemberId()") === memberRowId);

    console.log("  -- 4 · Member đổi trạng thái việc của mình --");
    const stPill2 = MEMBER.d.querySelector("#sec-actions .pill[class*=st-]");
    ok("4 · Member bấm được pill trạng thái", stPill2 && !stPill2.hasAttribute("disabled"));
    if (stPill2 && !stPill2.hasAttribute("disabled")) {
      stPill2.dispatchEvent(new MEMBER.w.Event("click", { bubbles: true }));
      await sleep(900);
      const r2 = await OWNER.api(`/api/meetings/${encodeURIComponent(mid2)}`, { headers: H });
      const d2 = await r2.json();
      ok("4 · Trạng thái Member đổi được lưu xuống máy chủ",
         Object.values(d2.assignments).some(a => a.status !== "todo"));
    }
    ok("4 · Member KHÔNG đổi được mức ưu tiên", (() => {
      const pr = MEMBER.d.querySelector("#sec-actions .pill[class*=pr-]");
      return pr && pr.hasAttribute("disabled");
    })());

    console.log("  -- 3 · nâng Member lên đồng chủ toạ --");
    OWNER.w.eval("state.memMenu = null; render()");
    const btns2 = OWNER.d.querySelectorAll("#sec-members .mem-x");
    btns2[btns2.length - 1].dispatchEvent(new OWNER.w.Event("click", { bubbles: true }));
    const promote = [...OWNER.d.querySelectorAll(".mem-pop .menu-item")]
      .find(x => x.textContent.includes("Chỉ định làm đồng chủ toạ"));
    if (promote) {
      promote.dispatchEvent(new OWNER.w.Event("click", { bubbles: true }));
      await sleep(1000);
    }
    const [, mem2] = await (async () => {
      const r = await OWNER.api(`/api/meetings/${encodeURIComponent(mid2)}/members`,
                                { headers: H });
      return [r.status, await r.json()];
    })();
    ok("3 · Nâng quyền lưu xuống máy chủ",
       mem2.members.some(m => m.email === "member@meety.ai" && m.role === "co_owner"));

    await sleep(4000);   // chờ nhịp đồng bộ bên Member
    ok("3 · Member tự nhận quyền mới mà không cần tải lại",
       MEMBER.w.eval("myRole()") === "co_owner", MEMBER.w.eval("myRole()"));
    ok("3 · Đồng chủ toạ KHÔNG chuyển được quyền chủ toạ",
       MEMBER.w.eval("can('transfer_ownership')") === false);
    ok("3 · Đồng chủ toạ KHÔNG gỡ được thành viên",
       MEMBER.w.eval("can('remove_member')") === false);
    ok("3 · Đồng chủ toạ VẪN gán được việc", MEMBER.w.eval("can('assign_task')") === true);

    ok("Không lỗi JS ở cả hai phiên", OWNER.errs.length === 0 && MEMBER.errs.length === 0,
       (OWNER.errs[0] || MEMBER.errs[0] || "").toString().split("\n")[0]);
    OWNER.w.eval("stopSync()"); MEMBER.w.eval("stopSync()");

    console.log("\n=== J. Không lỗi JS trong toàn bộ phiên ===");
    ok("Console sạch", errs.length === 0,
       errs.length ? errs[0].split("\n").slice(0, 3).join(" | ") : "");

    console.log("\n" + (FAILS ? `✕ CÓ ${FAILS} LỖI` : "✓ TẤT CẢ ĐỀU QUA"));
    return FAILS ? 1 : 0;
  } finally {
    srv.kill("SIGTERM");
    await sleep(300);
    try { srv.kill("SIGKILL"); } catch {}
    try { fs.rmSync(TMP, { recursive: true, force: true }); } catch {}
  }
}

main().then(code => process.exit(code)).catch(e => {
  console.error("Bộ kiểm thử gặp lỗi:", e);
  process.exit(1);
});
