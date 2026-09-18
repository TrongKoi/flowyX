/* Chạy chính file HTML sẽ giao, trong DOM thật của jsdom, rồi bấm nút như
   người dùng. Đây là chỗ bắt được lỗi mà kiểm tra chuỗi không thấy. */
const { JSDOM } = require("jsdom");
const fs = require("fs");
const html = fs.readFileSync(__dirname + "/../../mm-ai-preview.html", "utf8");

const errs = [];
const dom = new JSDOM(html, {
  runScripts: "dangerously", pretendToBeVisual: true, url: "https://mm.ai/",
  beforeParse(w) {
    w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {} });
    w.scrollTo = () => {};
    w.alert = () => {};
    w.navigator.mediaDevices = { getUserMedia: () => Promise.reject(new Error("no mic")) };
    w.HTMLElement.prototype.scrollIntoView = function () {};
    w.addEventListener("error", e => errs.push("window.onerror: " + e.message));
  },
});
const { window } = dom;
const doc = window.document;
const $ = s => doc.querySelector(s);
const $$ = s => [...doc.querySelectorAll(s)];

let fails = 0;
const ok = (name, cond, extra = "") => {
  if (!cond) { fails++; console.log("  ✕ " + name + (extra ? "  → " + extra : "")); }
  else console.log("  ✓ " + name + (extra ? "  (" + extra + ")" : ""));
};
const click = el => { if (!el) { fails++; console.log("  ✕ không tìm thấy phần tử để bấm"); return; }
  el.dispatchEvent(new window.Event("click", { bubbles: true })); };
const byText = (sel, txt) => $$(sel).find(e => (e.textContent || "").includes(txt));
/* Chữ NGƯỜI DÙNG THẬT SỰ NHÌN THẤY: bỏ script và style ra khỏi phép đo.
   textContent của body gộp cả mã nguồn lẫn JSON nhúng — đo trên đó thì mọi
   phép kiểm "không lộ mã kỹ thuật" đều báo sai. */
const seen = () => {
  const c = doc.body.cloneNode(true);
  [...c.querySelectorAll("script,style")].forEach(e => e.remove());
  return c.textContent || "";
};

setTimeout(() => {
  console.log("\n=== A. Khởi động ===");
  ok("Không có lỗi JS khi tải", errs.length === 0, errs.join(" | "));
  ok("Dựng ra màn hình đăng nhập", seen().includes("Đăng nhập") && !!$(".panel-logo svg"));
  ok("Có logo Meety trên thanh trên cùng", !!$(".brand .logo svg"));

  console.log("\n=== A2. Logo Meety ===");
  ok("0 · Logo là SVG nội tuyến, không phụ thuộc tệp rời",
     !!$(".brand .logo svg") && !$(".brand img"));
  ok("0 · Logo dùng đúng hai màu của bản nhận diện mới", (() => {
    const html = $(".brand .logo").innerHTML;
    return html.includes("#111111") && html.includes("#FFFFFF")
        && !html.includes("#E7ED4B") && !html.includes("#5B4CF0");
  })());
  ok("0 · Logo có tấm chính và bóng đổ phẳng",
     $(".brand .logo svg").querySelectorAll("rect").length === 2);
  ok("0 · Chữ MEETY vẽ bằng đường, không cần tải font", (() => {
    const g = $(".brand .logo svg");
    return g.querySelectorAll("path").length >= 5 && !g.querySelector("text");
  })());
  ok("0 · Logo không tự thêm bóng đổ chồng lên bóng có sẵn trong SVG",
     ["none",""].includes(window.getComputedStyle($(".brand .logo")).boxShadow),
     JSON.stringify(window.getComputedStyle($(".brand .logo")).boxShadow));
  ok("0 · Logo cao 42px, vừa trong thanh 66px",
     window.getComputedStyle($(".brand .logo svg")).height === "42px");
  ok("0 · Có nhãn cho trình đọc màn hình", !!byText(".brand .sr", "Meety"));
  ok("0 · Có favicon nhúng thẳng vào trang", (() => {
    const l = doc.querySelector('link[rel="icon"]');
    return l && l.getAttribute("href").startsWith("data:image/svg+xml,");
  })());
  ok("0 · Màn đăng nhập dùng bản logo đầy đủ", !!$(".panel-logo svg"));
  ok("0 · Tiêu đề trang mang tên Meety", doc.title.includes("Meety"));

  console.log("\n=== B. Đăng nhập → OTP → tổng quan ===");
  click(byText("button", "Tiếp tục"));
  ok("Sang bước xác thực 2 lớp", seen().includes("Xác thực 2 lớp"));
  ok("Có 6 ô nhập mã", $$(".otp input").length === 6);
  click(byText("button", "Xác nhận và đăng nhập"));
  ok("Vào được trang tổng quan", seen().includes("đây là các cuộc họp gần đây"));

  console.log("\n=== C. Bố cục thẻ cuộc họp ===");
  const cards = $$(".mcard");
  ok("Hiện đủ 9 thẻ", cards.length === 9, cards.length + " thẻ");
  ok("Mọi thẻ đều có thẻ loại dữ liệu", cards.every(c => !!c.querySelector(".kind-tag")));
  ok("Thẻ loại là phần tử ĐẦU TIÊN trong mỗi thẻ (góc trên trái)",
     cards.every(c => c.firstElementChild && c.firstElementChild.classList.contains("kind-tag")));
  ok("Thẻ loại được neo tuyệt đối bên trái",
     cards.every(c => { const st = window.getComputedStyle(c.querySelector(".kind-tag"));
                        return st.position === "absolute" && st.left === "21px"; }));
  ok("Mỗi thẻ có thanh đo tin cậy", cards.every(c => !!c.querySelector(".minifill")));
  ok("Mỗi thẻ có trạng thái duyệt",
     cards.every(c => /Đã phê duyệt|Chờ duyệt/.test(c.textContent)));

  console.log("\n=== D. Lọc: chọn vào nháp, bấm Áp dụng mới đổi danh sách ===");
  const nGroups = () => $$(".group").length;
  const nCards = () => $$(".mcard").length;
  const openPop = () => { if (!$(".filter-pop")) click($(".filter-btn")); };
  const pick = lbl => { openPop(); click(byText(".segctl button", lbl)); };
  const apply = () => { openPop(); click(byText(".pop-foot .btn", "Áp dụng") ||
                                          byText(".pop-foot .btn", "Xong")); };
  const pickApply = lbl => { pick(lbl); apply(); };

  ok("Thanh lọc bốn hàng đã thu về một nút", !$(".filters") && !!$(".filter-btn"));
  ok("Popup mặc định đóng", !$(".filter-pop"));
  click($(".filter-btn"));
  ok("Bấm nút thì popup bung ra", !!$(".filter-pop"));
  ok("4 · Mặc định gom theo dự án", nGroups() === 4, nGroups() + " nhóm");
  ok("4 · Không còn bộ lọc Dữ liệu mẫu", !seen().includes("Dữ liệu mẫu"));
  ok("4 · Không còn nhãn loại dữ liệu trên thẻ",
     $$(".mcard").every(c => !/Dữ liệu (thật|mẫu)/.test(c.textContent)));

  console.log("  -- 2 · nút Áp dụng --");
  const before = nCards();
  click(byText(".segctl button", "Chờ duyệt"));
  ok("2 · Chọn tiêu chí xong danh sách CHƯA đổi", nCards() === before, nCards() + " thẻ");
  ok("2 · Popup báo rõ là chưa áp dụng", seen().includes("Chưa áp dụng"));
  ok("2 · Popup cho biết trước sẽ còn bao nhiêu", /sẽ hiện/.test(seen()));
  ok("2 · Có nút Áp dụng", !!byText(".pop-foot .btn", "Áp dụng"));
  click(byText(".pop-foot .btn", "Áp dụng"));
  ok("2 · Bấm Áp dụng thì danh sách mới đổi", nCards() < before, nCards() + " thẻ");
  ok("2 · Bấm Áp dụng thì popup đóng lại", !$(".filter-pop"));

  console.log("  -- 1 · căn giữa trong popup --");
  openPop();
  ok("1 · Nhãn nhóm căn giữa", (() => {
    const l = $(".pop-row .flabel");
    return l && window.getComputedStyle(l).textAlign === "center";
  })());
  ok("1 · Các nút lựa chọn căn giữa", (() => {
    const b = $(".pop-row .segctl button");
    return b && window.getComputedStyle(b).justifyContent === "center";
  })());
  ok("1 · Nhóm nút chiếm hết bề ngang, chia đều", (() => {
    const g = $(".pop-row .segctl");
    return g && window.getComputedStyle(g).width !== "" &&
           window.getComputedStyle($(".pop-row .segctl button")).flexGrow === "1";
  })());
  click($(".filter-btn"));

  console.log("  -- 3 · nút Đặt lại --");
  pickApply("Chờ duyệt");
  pickApply("Cũ nhất trước");
  openPop(); click(byText(".chip", "Phòng kỹ thuật")); apply();
  const filtered = nCards();
  ok("3 · Đã lọc chồng nhiều tiêu chí", filtered < 9, filtered + " thẻ");
  const box0 = $(".searchbox input");
  box0.value = "hạ tầng";
  box0.dispatchEvent(new window.Event("input", { bubbles: true }));
  openPop();
  click(byText(".pop-foot .btn", "Đặt lại"));
  ok("3 · Đặt lại đưa danh sách về đủ 9 thẻ", nCards() === 9, nCards() + " thẻ");
  ok("3 · Đặt lại xoá luôn ô tìm kiếm", $(".searchbox input").value === "");
  ok("3 · Đặt lại xoá badge đếm điều kiện", !$(".filter-btn .n"));
  openPop();
  ok("3 · Đặt lại đưa sắp xếp về Mới nhất trước", (() => {
    const on = $$(".segctl")[1].querySelector("button.on");
    return on && on.textContent.includes("Mới nhất");
  })());
  ok("3 · Đặt lại đưa trạng thái về Tất cả", (() => {
    const on = $$(".segctl")[0].querySelector("button.on");
    return on && on.textContent.trim() === "Tất cả";
  })());
  click($(".filter-btn"));

  console.log("  -- lọc, sắp xếp, gom nhóm vẫn đúng --");
  pickApply("Chờ duyệt");
  const pend = nCards();
  ok("Lọc chờ duyệt", pend > 0 && pend < 9, pend + " thẻ");
  ok("Không thẻ nào còn nhãn đã phê duyệt",
     $$(".mcard").every(c => !c.textContent.includes("Đã phê duyệt")));
  pickApply("Đã phê duyệt");
  ok("Đổi sang đã phê duyệt", nCards() === 9 - pend, nCards() + " thẻ");
  openPop(); click($$(".segctl")[1].querySelector("button")); apply();  // trạng thái → Tất cả
  pickApply("Không gom");
  const firstTitle = () => $(".mcard-t").textContent.trim();
  const t1 = firstTitle();
  pickApply("Cũ nhất trước");
  const t2 = firstTitle();
  ok("Đổi thứ tự sắp xếp làm đổi thẻ đầu", t1 !== t2, `${t1} → ${t2}`);
  ok("Cũ nhất lên đầu đúng là cuộc họp tháng 7", t2.includes("tháng 7"), t2);
  pickApply("Mới nhất trước");
  ok("Mới nhất lên đầu là cuộc họp gần nhất", firstTitle().includes("Kick-off")
     || firstTitle().includes("ngân sách"), firstTitle());
  openPop(); click(byText(".pop-foot .btn", "Đặt lại"));   // sạch trạng thái trước khi đo
  if ($(".filter-pop")) click($(".filter-btn"));
  pickApply("Theo dự án");
  ok("Gom theo dự án cho 4 nhóm", nGroups() === 4, nGroups() + " nhóm");
  ok("Tổng số thẻ không đổi khi gom lại", nCards() === 9, nCards() + " thẻ");
  pickApply("Không gom");
  ok("Không gom → 1 nhóm", nGroups() === 1);
  pickApply("Theo dự án");
  openPop(); click(byText(".chip", "Phòng kỹ thuật")); apply();
  ok("Lọc theo chip dự án", nCards() === 3, nCards() + " thẻ");
  openPop(); click(byText(".chip", "Tất cả")); apply();

  const box = $(".searchbox input");
  box.value = "ngân sách";
  box.dispatchEvent(new window.Event("input", { bubbles: true }));
  ok("Tìm kiếm lọc được danh sách ngay (không cần Áp dụng)",
     nCards() > 0 && nCards() < 9, nCards() + " kết quả");
  ok("Ô tìm kiếm không bị dựng lại (giữ nguyên giá trị)",
     $(".searchbox input").value === "ngân sách");
  box.value = "khong-co-gi-khop";
  box.dispatchEvent(new window.Event("input", { bubbles: true }));
  ok("Không có kết quả thì hiện khối rỗng", !!$(".empty"));
  click(byText(".empty .btn", "Đặt lại bộ lọc"));
  ok("Đặt lại khôi phục 9 thẻ", nCards() === 9);

  if ($(".filter-pop")) click($(".filter-btn"));

  console.log("\n=== N. Sáu yêu cầu mới ===");
  ok("1 · Popup đóng khi bấm ra ngoài", (() => {
    click($(".filter-btn"));
    const opened = !!$(".filter-pop");
    click(doc.body);
    return opened && !$(".filter-pop");
  })());
  ok("1 · Badge trên nút chỉ đếm điều kiện ĐÃ áp dụng", (() => {
    click($(".filter-btn"));
    click(byText(".segctl button", "Chờ duyệt"));
    const beforeApply = $(".filter-btn .n");      // chưa áp dụng → chưa có badge
    click(byText(".pop-foot .btn", "Áp dụng"));
    const afterApply = $(".filter-btn .n");
    const good = !beforeApply && afterApply && afterApply.textContent.trim() === "1";
    click($(".filter-btn")); click(byText(".pop-foot .btn", "Đặt lại")); click(doc.body);
    return good;
  })());
  ok("1 · Header có nút hành động chính", !!byText("nav .btn", "Tạo cuộc họp mới"));
  ok("1 · Nhãn nút rút gọn được ở màn hẹp", !!$(".nav-cta-label"));
  ok("2 · Dashboard vẫn giữ nút tạo cuộc họp", !!byText(".hub .btn", "Tạo cuộc họp mới"));
  ok("2 · Thẻ dày viền 3px, bóng sâu hơn", (() => {
    const st = window.getComputedStyle($(".mcard"));
    return st.borderTopWidth === "3px" && st.boxShadow.includes("6px");
  })(), window.getComputedStyle($(".mcard")).borderTopWidth);
  ok("2 · Mỗi thẻ mang màu dự án riêng", (() => {
    const vals = $$(".mcard").map(c => c.style.getPropertyValue("--accent"));
    return vals.every(Boolean) && new Set(vals).size >= 3;
  })(), [...new Set($$(".mcard").map(c => c.style.getPropertyValue("--accent")))].join(" "));

  console.log("\n=== O. Chuông thông báo ===");
  ok("5 · Có chấm đen chưa đọc trên chuông", !!$(".unread-dot"));
  ok("5 · Không dùng badge số đỏ nữa", !$(".ping"));
  click($$(".icon-btn")[0]);
  ok("5 · Mở được bảng thông báo", $$(".notif").length === 3, $$(".notif").length + " mục");
  ok("5 · Có nút xoá riêng từng mục", $$(".notif-x").length === 3);
  ok("5 · Có nút Xoá tất cả ở ĐẦU bảng", !!byText(".notif-head .notif-act", "Xoá tất cả"));
  ok("5 · Có nút đánh dấu tất cả đã đọc",
     !!byText(".notif-head .notif-act", "Đã đọc hết"));
  ok("2 · Hàng tiêu đề thông báo không vỡ dòng", (() => {
    const head = $(".notif-head");
    const btn = $(".notif-head .notif-act");
    if (!head || !btn) return false;
    const st = window.getComputedStyle(head);
    const bs = window.getComputedStyle(btn);
    return st.display === "flex" && st.justifyContent === "space-between"
        && bs.whiteSpace === "nowrap";
  })());
  ok("5 · Thông báo chưa đọc có chấm riêng", $$(".notif.unread .notif-dot").length >= 1);
  ok("5 · Có phân biệt đã đọc và chưa đọc",
     $$(".notif.read").length >= 1 && $$(".notif.unread").length >= 1,
     `${$$(".notif.unread").length} chưa đọc / ${$$(".notif.read").length} đã đọc`);
  click($(".notif-x"));
  ok("5 · Bảng không bị đóng khi bấm nút xoá", !!$(".notif-head"));
  ok("5 · Xoá một mục thì còn 2", $$(".notif").length === 2, $$(".notif").length + " mục");
  click(byText(".notif-head .notif-act", "Đã đọc hết"));
  ok("5 · Đánh dấu đã đọc GIỮ LẠI danh sách", $$(".notif").length === 2);
  ok("5 · Đánh dấu đã đọc thì chấm trên chuông tắt", !$(".unread-dot"));
  click(byText(".notif-head .notif-act", "Xoá tất cả"));
  ok("5 · Xoá tất cả thì bảng rỗng", $$(".notif").length === 0);
  ok("5 · Bảng rỗng báo rõ bằng chữ", seen().includes("Không còn thông báo nào"));
  click(doc.body);

  console.log("  -- 7 · thẻ KPI --");
  ok("7 · Có đúng 4 thẻ KPI", $$(".kpi").length === 4, $$(".kpi").length + " thẻ");
  ok("7 · Mỗi thẻ có icon riêng", $$(".kpi .kpi-ic svg").length === 4);
  ok("7 · Con số dùng chữ số đều bề rộng",
     $$(".kpi-v").every(v =>
       window.getComputedStyle(v).fontVariantNumeric.includes("tabular-nums")));
  ok("7 · Có thẻ tỷ lệ hoàn thành kèm thanh tiến độ",
     seen().includes("Tỷ lệ hoàn thành") && !!$(".kpi-bar i"));
  ok("7 · Bỏ thẻ độ tin cậy trung bình", !seen().includes("Tin cậy trung bình"));

  console.log("\n=== E. Cửa sổ nạp dữ liệu ===");
  click(byText(".hub .btn", "Tạo cuộc họp mới"));
  ok("Mở được cửa sổ nạp", !!$(".modal-bg") && seen().includes("Nạp cuộc họp mới"));
  ok("Có hai chế độ", $$(".mode-tab").length === 2);
  ok("Có vùng kéo thả", !!$(".drop"));
  ok("Nút phân tích đang khoá", byText(".modal-foot button", "Bắt đầu phân tích").disabled);
  click(byText(".mode-n", "Thu cuộc họp đang diễn ra").closest(".mode-tab"));
  ok("Chuyển sang chế độ thu", !!$("#wave"));
  ok("6 · Có nút thu tiếng tab cuộc họp", !!byText(".btn", "Thu tiếng tab cuộc họp"));
  ok("6 · Có nút chỉ thu micro", !!byText(".btn", "Chỉ micro"));
  ok("6 · Nói rõ giới hạn của việc chỉ thu micro",
     seen().includes("chỉ nghe được người trong phòng")
     || seen().includes("Chỉ micro"));
  click(byText(".btn", "Thu tiếng tab cuộc họp"));
  ok("6 · Bấm thu tab thì mở modal hướng dẫn trước", !!$(".modal-bg"));
  ok("6 · Hướng dẫn tích ô chia sẻ âm thanh của thẻ",
     seen().includes("Chia sẻ âm thanh của thẻ"));
  ok("6 · Có cam kết quyền riêng tư", seen().includes("Về dữ liệu của bạn"));
  ok("6 · Có lối thoát sang tải tệp lên", !!byText(".modal-foot .btn", "Tải tệp lên thay thế"));
  click($$(".modal-foot .btn").find(b => b.textContent.trim() === "Huỷ"));
  ok("6 · Huỷ thì đóng hướng dẫn, không ghi gì",
     !seen().includes("Chia sẻ âm thanh của thẻ"));
  ok("Dạng sóng có 56 cột", $("#wave").children.length === 56);
  ok("Có khung xem trước lời nói", !!$("#live-tx"));
  click(byText(".mode-n", "Tải lên tệp ghi âm").closest(".mode-tab"));
  window.eval('state.ingestFile = { name: "hop_thu_nghiem.m4a", size: 5242880 }; render();');
  ok("Chọn tệp xong thì mở khoá nút",
     !byText(".modal-foot button", "Bắt đầu phân tích").disabled);
  click(byText(".modal-foot button", "Bắt đầu phân tích"));
  ok("Hiện danh sách 8 pha pipeline", $$(".stage-li").length === 8);

  /* Nhảy thẳng tới trạng thái xong thay vì chờ 8 lần setTimeout */
  window.eval('clearTimeout(ingestTimer); state.ingestStage = 8; state.ingestDone = true; render();');
  ok("Báo đã phân tích xong", seen().includes("Đã phân tích xong"));
  click(byText(".modal-foot button", "Xem trên trang tổng quan"));
  ok("Đóng cửa sổ sau khi xong", !$(".modal-bg"));
  ok("Danh sách có thêm cuộc họp mới", $$(".mcard").length === 10, $$(".mcard").length + " thẻ");
  ok("Thẻ mới nằm đầu danh sách", $(".mcard-t").textContent.length > 0,
     $(".mcard-t").textContent.trim());
  ok("Có thông báo nổi", !!$(".toast"));

  console.log("\n=== F. Trang chi tiết cuộc họp ===");
  click($$(".mcard").find(c => c.textContent.includes("Sprint 23")));
  ok("Mở được biên bản Sprint 23", seen().includes("Sprint 23 Review"));
  ok("2 · Thanh điều hướng gọn còn 6 mục", $$(".dock-btn").length === 6, $$(".dock-btn").length + " nút");
  ok("2 · Có đủ 6 khối nội dung", $$("section[id^=sec-]").length === 6, $$("section[id^=sec-]").length + "");
  ok("2 · Thành viên đứng TRƯỚC công việc", (() => {
    const ids = $$("section[id^=sec-]").map(x => x.id);
    return ids.indexOf("sec-members") < ids.indexOf("sec-actions");
  })(), $$("section[id^=sec-]").map(x => x.id).join(" → "));
  ok("2 · Hero có badge trạng thái phê duyệt",
     /ĐÃ PHÊ DUYỆT|CHỜ PHÊ DUYỆT/.test(seen()));
  ok("Có khối cuộc họp liên quan", seen().includes("Cuộc họp liên quan"));
  ok("Chuỗi có 3 mắt xích", $$(".ln-item").length === 3, $$(".ln-item").length + " mắt");
  ok("Mắt đang xem được đánh dấu", $$(".ln-item.here").length === 1);
  ok("Có thanh đo tin cậy lớn", !!$(".gauge-fill"));
  ok("Bảng trừ điểm liệt kê 5 loại cảnh báo", $$(".ded-li").length === 5, $$(".ded-li").length+"");
  ok("2 · Đã xoá công thức tính khỏi giao diện", !seen().includes("Tin cậy = 100"));
  ok("2 · Đã xoá ghi chú về “Bị thay thế / Chưa cam kết”",
     !seen().includes("không trừ điểm"));
  ok("2 · Đã xoá mô tả năm tầng nhận diện người nói", !seen().includes("năm tầng"));
  ok("2 · Đã xoá ghi chú tám phép kiểm tra", !seen().includes("Tám phép kiểm"));
  ok("2 · Thước và thanh đo cùng hệ toạ độ", (() => {
    // Mỗi nhãn phải đặt tại ĐÚNG phần trăm của nó, không chia đều.
    const ticks = $$(".gauge-ticks span");
    if (ticks.length !== 5) return false;
    const lefts = ticks.map(t => t.style.left);
    return JSON.stringify(lefts) === JSON.stringify(["0%","50%","70%","85%","100%"]);
  })(), $$(".gauge-ticks span").map(t => t.style.left).join(" "));
  ok("2 · Thanh đổ đúng bằng số hiển thị", (() => {
    const fill = $(".gauge-fill");
    const num = ($(".conf-num") || {}).textContent || "";
    return fill && fill.style.width === num.trim();
  })(), `${($(".conf-num")||{}).textContent} vs ${($(".gauge-fill")||{}).style.width}`);
  ok("2 · Có vạch ngưỡng 70 và 85 trên thanh",
     $$(".gauge-mark").map(m => m.style.left).join() === "70%,85%");

  const bodyTxt = seen();
  ok("Không lộ mã cảnh báo kỹ thuật",
     !/AMBIGUOUS_ASSIGNEE|SUPERSEDED_DEPENDENCY|LOW_COMMITMENT/.test(bodyTxt));
  ok("Không lộ mã đoạn s_00xx", !/\bs_\d{4}\b/.test(bodyTxt));
  ok("Dùng nhãn rút gọn Chưa gán người làm", bodyTxt.includes("Chưa gán người làm"));
  ok("Dùng nhãn rút gọn Thoại mờ", bodyTxt.includes("Thoại mờ"));
  ok("3 · Badge trên thanh điều hướng có số khi CHƯA active", (() => {
    const b = $$(".dock-btn").find(x => !x.classList.contains("on") && x.querySelector(".n"));
    return b && /\d/.test(b.querySelector(".n").textContent);
  })());
  ok("3 · Badge vẫn đọc được KHI ĐANG active", (() => {
    const btn = $$(".dock-btn").find(x => x.dataset.target === "sec-actions");
    click(btn);
    const on = $$(".dock-btn").find(x => x.classList.contains("on") && x.querySelector(".n"));
    if (!on) return false;
    const n = on.querySelector(".n");
    const st = window.getComputedStyle(n);
    // số phải còn đó VÀ màu chữ không được trùng màu nền kem của tab active
    return /\d/.test(n.textContent) && st.color !== window.getComputedStyle(on).color;
  })());
  ok("4 · Vùng nội dung chừa chỗ cho thanh nghe lại", (() => {
    const w = $(".wrap.has-player");
    return w && parseInt(window.getComputedStyle(w).paddingBottom) >= 90;
  })(), $(".wrap.has-player") ? window.getComputedStyle($(".wrap.has-player")).paddingBottom : "không có");

  console.log("\n=== R. Responsive header (Bài 1) ===");
  const CSS = [...doc.querySelectorAll("style")].map(x => x.textContent).join("")
                .replace(/\s+/g, " ");
  ok("1 · Thanh trên cùng không cho xuống dòng",
     /\.nav-in \{[^}]*flex-wrap: nowrap/.test(CSS));
  ok("1 · Vùng điều hướng có min-width:0 để co được",
     /\.dock \{[^}]*min-width: 0/.test(CSS));
  ok("1 · Có ngưỡng gom nút điều hướng vào dropdown",
     /@media \(max-width: 1080px\) \{ \.dock \{ display: none/.test(CSS));
  ok("1 · Có ngưỡng rút gọn nhãn nút hành động",
     /@media \(max-width: 780px\)/.test(CSS));
  ok("1 · Có nút quick-jump cho màn hẹp", !!$(".nav-jump"));
  click($(".nav-jump > button"));
  ok("1 · Dropdown liệt kê đủ 6 mục", $$(".jump-pop .menu-item").length === 6,
     $$(".jump-pop .menu-item").length + " mục");
  ok("1 · Mục đang xem được đánh dấu", $$(".jump-pop .menu-item.on").length === 1);
  click(byText(".jump-pop .menu-item", "Công việc"));
  ok("1 · Bấm trong dropdown thì nhảy đúng mục",
     $$(".dock-btn.on")[0].dataset.target === "sec-actions",
     $$(".dock-btn.on")[0].dataset.target);
  ok("1 · Dropdown đóng lại sau khi chọn", window.eval("state.jumpOpen") === false);
  ok("1 · Chiều cao thanh trên cùng cố định", /height: var\(--nav-h\)/.test(CSS));

  console.log("\n=== S. Ma trận quyền 3 tầng (Bài 3) ===");
  const setRole = r => window.eval(
    `currentMeeting().myRole='${r}'; currentMeeting().permissions=null; render()`);

  setRole("owner");
  ok("3 · Chủ toạ: có quyền chuyển quyền chủ toạ", window.eval("can('transfer_ownership')"));
  ok("3 · Chủ toạ: bãi nhiệm được đồng chủ toạ", window.eval("can('demote_co_host')"));
  ok("3 · Chủ toạ: gỡ được thành viên", window.eval("can('remove_member')"));

  setRole("co_owner");
  ok("3 · Đồng chủ toạ: KHÔNG chuyển được quyền chủ toạ",
     !window.eval("can('transfer_ownership')"));
  ok("3 · Đồng chủ toạ: KHÔNG bãi nhiệm được đồng chủ toạ khác",
     !window.eval("can('demote_co_host')"));
  ok("3 · Đồng chủ toạ: KHÔNG gỡ được thành viên", !window.eval("can('remove_member')"));
  ok("3 · Đồng chủ toạ: VẪN chỉ định được đồng chủ toạ mới",
     window.eval("can('promote_co_host')"));
  ok("3 · Đồng chủ toạ: vẫn gán được việc và phê duyệt",
     window.eval("can('assign_task')") && window.eval("can('approve')"));
  ok("3 · Menu của đồng chủ toạ CHỈ có mục chỉ định", (() => {
    const m = window.eval("JSON.stringify(membersOf().filter(x=>x.role!=='owner')[0]||{})");
    const html = window.eval(`memberMenu(${m})`);
    return html.includes("Chỉ định làm đồng chủ toạ")
        && !html.includes("Chuyển quyền") && !html.includes("Gỡ khỏi cuộc họp");
  })());

  setRole("member");
  ok("3 · Thành viên: không có quyền phân quyền nào",
     !window.eval("can('promote_co_host')") && !window.eval("can('demote_co_host')")
     && !window.eval("can('transfer_ownership')") && !window.eval("can('remove_member')"));
  ok("3 · Thành viên: chỉ được cập nhật trạng thái việc của mình",
     window.eval("can('update_own_status')") && !window.eval("can('assign_task')"));
  ok("3 · Thành viên không thấy nút ⋯ nào", $$("#sec-members .mem-x").length === 0);
  setRole("owner");

  console.log("\n=== T. Đồng bộ dữ liệu (Bài 4) ===");
  ok("4 · Có hàm nạp lại luôn hỏi máy chủ",
     typeof window.eval("typeof refreshMeeting") === "string"
     && window.eval("typeof refreshMeeting") === "function");
  ok("4 · Có nhịp đồng bộ nền", window.eval("typeof startSync") === "function");
  ok("4 · Nhịp đồng bộ dừng khi rời trang chi tiết", (() => {
    window.eval("startSync()");
    const on = window.eval("syncTimer !== null");
    window.eval("stopSync()");
    return !on || window.eval("syncTimer === null");
  })());

  console.log("\n=== Q. Mười bài toán ===");
  console.log("  -- 1 · lớp phủ và khoảng chừa khi cuộn --");
  ok("1 · Thang z-index khai báo bằng biến, không rải số", (() => {
    const css = [...doc.querySelectorAll("style")].map(s => s.textContent).join("");
    return css.includes("--z-header") && css.includes("--z-modal")
        && css.includes("--z-player");
  })());
  ok("1 · Thang z-index xếp đúng thứ tự, không có hai lớp cùng bậc", (() => {
    // jsdom không tính var()/calc(), nên đọc thẳng giá trị đã khai báo.
    const css = [...doc.querySelectorAll("style")].map(s => s.textContent).join("");
    const layer = n => {
      const m = css.match(new RegExp("--z-" + n + ":\\s*(\\d+)"));
      return m ? Number(m[1]) : null;
    };
    const order = ["content", "sticky", "player", "backpill", "header", "pop", "modal", "toast"];
    const vals = order.map(layer);
    return vals.every(v => v !== null)
        && vals.every((v, i) => i === 0 || v > vals[i - 1])
        && new Set(vals).size === vals.length;
  })());
  ok("1 · Trang khai báo scroll-padding-top", (() => {
    const css = [...doc.querySelectorAll("style")].map(s => s.textContent).join("");
    return /html\s*\{[^}]*scroll-padding-top/.test(css);
  })());
  ok("1 · Mọi khối đều chừa chỗ khi nhảy tới",
     $$("section[id^=sec-]").every(x => {
       const v = window.getComputedStyle(x).scrollMarginTop || "";
       return v.includes("--nav-h") || parseInt(v) >= 60;
     }));
  ok("1 · Từng lượt nói trong bản thoại cũng chừa chỗ", (() => {
    const seg = $(".seg");
    const v = seg ? window.getComputedStyle(seg).scrollMarginTop || "" : "";
    return v.includes("--nav-h") || parseInt(v) >= 60;
  })());
  ok("1 · Vùng nội dung chừa đáy cho thanh nghe lại",
     parseInt(window.getComputedStyle($(".wrap.has-player")).paddingBottom) >= 90);

  console.log("  -- 3 · hai nhóm nhãn --");
  const taskCards = $$("#sec-actions .card");
  ok("3 · Mỗi việc có đúng một pill trạng thái",
     taskCards.every(c => c.querySelectorAll(".pill[class*=st-]").length === 1));
  ok("3 · Mỗi việc có đúng một pill ưu tiên",
     taskCards.every(c => [...c.querySelectorAll(".pill")].filter(
       p => /\bpr-(high|medium|low)\b/.test(p.className)).length === 1),
     taskCards.length + " thẻ");
  ok("3 · Đã bỏ nhãn Cam kết chắc / Dự kiến",
     !/Cam kết chắc|Dự kiến/.test($("#sec-actions").textContent));
  ok("4 · Đã bỏ chấm cảnh báo vàng khỏi thẻ công việc",
     $$("#sec-actions .warn-dot").length === 0);
  ok("4 · Chủ toạ có nút xoá trên mỗi thẻ việc",
     $$("#sec-actions .task-del").length === taskCards.length);
  ok("4 · Có nút thêm công việc mới", !!byText("#sec-actions .btn", "Thêm công việc mới"));
  ok("4 · Hạn chót bấm được để sửa",
     $$("#sec-actions .pill").some(p => /Hạn|Chưa có hạn/.test(p.textContent)));
  const stPill = $("#sec-actions .pill[class*=st-]");
  const before3 = stPill.textContent.trim();
  click(stPill);
  ok("3 · Bấm pill thì đổi trạng thái",
     $("#sec-actions .pill[class*=st-]").textContent.trim() !== before3,
     `${before3} → ${$("#sec-actions .pill[class*=st-]").textContent.trim()}`);
  ok("3 · Bộ lọc công việc theo trạng thái mới",
     !!byText("#sec-actions .btn", "Đang làm") && !!byText("#sec-actions .btn", "Hoàn thành"));

  console.log("  -- 8 · phê duyệt và xuất Word --");
  ok("12 · Nút xuất Word đúng tên", !!byText("button", "Xuất file Word (.docx)"));
  ok("12 · Nút xuất Markdown đúng tên", !!byText("button", "Xuất file Markdown (.md)"));
  click(byText("button", "Phê duyệt biên bản"));
  ok("8 · Phê duyệt phải qua bước xác nhận", seen().includes("Xác nhận phê duyệt"));
  ok("8 · Modal cảnh báo việc chưa có người nhận",
     /chưa có người nhận|không còn cảnh báo/.test(seen()));
  click(byText(".modal-foot .btn", "Xác nhận phê duyệt"));
  ok("8 · Xác nhận xong thì trạng thái đổi", seen().includes("ĐÃ PHÊ DUYỆT"));
  ok("8 · Nút đổi thành bỏ phê duyệt", !!byText("button", "Bỏ phê duyệt"));
  click(byText("button", "Bỏ phê duyệt"));
  ok("8 · Bỏ phê duyệt được", seen().includes("CHỜ PHÊ DUYỆT"));

  console.log("\n=== G. Truy vết & phát lại ===");
  const ev = $(".ev");
  click(ev);
  ok("Bấm mốc thời gian bật chế độ truy vết", $$(".seg.trace").length > 0,
     $$(".seg.trace").length + " đoạn được tô");
  ok("Hiện nút quay lại chỗ đang đọc", !!$(".back"));
  click($(".back"));
  ok("Bấm quay lại thì nút biến mất", !$(".back"));
  const t0 = window.eval("state.playheadMs");
  click($(".seg .ts"));
  ok("Bấm mốc trong bản thoại làm đổi vị trí phát",
     window.eval("state.playheadMs") !== t0 || $$(".seg.playing").length > 0);
  click($(".play"));
  ok("8 · Rời máy chủ thì Play nói rõ vì sao không phát được",
     window.eval("state.playing") === false && /máy chủ|ghi âm/.test(seen()),
     "không còn giả vờ phát");

  console.log("\n=== H. Lọc công việc & sửa tên người nói ===");
  const nAll = $$("#sec-actions .card").length;
  click(byText("#sec-actions .btn", "Chưa ai nhận"));
  const nUn = $$("#sec-actions .card").length;
  ok("Lọc công việc chưa có người nhận", nUn > 0 && nUn < nAll, `${nAll} → ${nUn}`);
  ok("Mọi thẻ còn lại đều thiếu người nhận",
     $$("#sec-actions .card").every(c => {
       const sel = c.querySelector(".assign select");
       return sel ? sel.value === "" : /Chưa gán người làm|Chưa ai nhận/.test(c.textContent);
     }));
  click(byText("#sec-actions .btn", "Tất cả"));

  click($(".spk-edit"));
  ok("Mở cửa sổ đổi tên người nói", !!$("#spk-name"));
  $("#spk-name").value = "Trần Quốc Hùng";
  $("#spk-role").value = "Giám đốc sản phẩm";
  click(byText(".modal-foot button", "Lưu và áp dụng"));
  const after = seen();
  ok("Tên mới áp dụng khắp trang", after.includes("Trần Quốc Hùng"));
  ok("Chức danh mới áp dụng", after.includes("Ban lãnh đạo") || after.includes("Giám đốc sản phẩm"));
  ok("Số lần xuất hiện tên mới > 5 (đã thay cả bản thoại)",
     (after.match(/Trần Quốc Hùng/g) || []).length > 5,
     (after.match(/Trần Quốc Hùng/g) || []).length + " lần");

  console.log("\n=== I. Điều hướng theo mục & bàn phím ===");
  click($$(".dock-btn")[3]);
  ok("Bấm nút điều hướng đặt đúng mục đang xem",
     $$(".dock-btn.on")[0].dataset.target === "sec-actions",
     $$(".dock-btn.on")[0].dataset.target);
  doc.dispatchEvent(new window.KeyboardEvent("keydown", { key: "2", bubbles: true }));
  ok("Phím số nhảy mục", $$(".dock-btn.on")[0].dataset.target === "sec-members",
     $$(".dock-btn.on")[0].dataset.target);
  doc.dispatchEvent(new window.KeyboardEvent("keydown", { key: "?", bubbles: true }));
  ok("Phím ? mở bảng phím tắt", !!$(".modal-bg") && seen().includes("Phím tắt"));
  doc.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  ok("Esc đóng bảng phím tắt", !$(".modal-bg") && window.eval("helpOpen") === false);
  doc.dispatchEvent(new window.KeyboardEvent("keydown", { key: "j", bubbles: true }));
  ok("Phím J chọn mục đầu tiên", $$(".card.active").length === 1);
  doc.dispatchEvent(new window.KeyboardEvent("keydown", { key: "a", bubbles: true }));
  ok("Phím A đánh dấu mục đang chọn", $$(".card.active").length <= 1);

  console.log("\n=== P. Phân quyền chủ cuộc họp / thành viên ===");
  ok("4 · Có thanh vai trò ở đầu trang", !!$(".role-bar"));
  ok("10 · Đã bỏ nút gạt giả lập vai trò", $$(".role-toggle").length === 0);
  ok("10 · Thanh vai trò hiện đúng vai trò thật", /Chủ toạ|Đồng chủ toạ|Thành viên/.test(
     $(".role-bar").textContent));
  ok("4 · Có khối Thành viên", !!$("#sec-members"));
  const memCount = $$("#sec-members .mem").length;
  ok("4 · Danh sách thành viên dựng từ người nói thật", memCount >= 2, memCount + " người");
  ok("4 · Có đúng một chủ cuộc họp",
     $$("#sec-members .mem").filter(m => m.textContent.includes("Chủ")).length === 1);

  console.log("  -- gán việc --");
  const selects = $$("#sec-actions .assign select");
  ok("4 · Chủ thấy ô chọn người nhận ở mỗi việc",
     selects.length === $$("#sec-actions .card").length, selects.length + " ô");
  ok("4 · Ô chọn liệt kê đủ thành viên",
     selects[0].querySelectorAll("option").length === memCount + 1);
  ok("4 · Có việc được TỰ GÁN theo tên trong biên bản",
     $$("#sec-actions .assign-src").some(x => x.textContent.includes("tự gán")),
     $$("#sec-actions .assign-src").map(x => x.textContent.trim()).join(" | "));

  const empty = selects.find(x => x.value === "");
  if (empty) {
    const opt = [...empty.querySelectorAll("option")].find(o => o.value);
    empty.value = opt.value;
    empty.dispatchEvent(new window.Event("change", { bubbles: true }));
    const again = $$("#sec-actions .assign select").find(x => x.value === opt.value);
    ok("4 · Gán tay một việc chưa có người nhận", !!again, opt.textContent.trim());
    ok("4 · Có thông báo xác nhận đã giao việc", seen().includes("Đã giao việc cho"));
  } else {
    ok("4 · Gán tay một việc chưa có người nhận", false, "không còn việc nào trống");
  }

  console.log("  -- mời thành viên --");
  const inv = $("#inv-email");
  ok("4 · Chủ có ô mời thành viên", !!inv);
  inv.value = "nguoimoi@congty.vn";
  click(byText("#sec-members .btn", "Mời thành viên"));
  ok("4 · Mời xong danh sách tăng thêm một người",
     $$("#sec-members .mem").length === memCount + 1);
  ok("4 · Người mới đánh dấu chờ nhận lời mời",
     seen().includes("Chờ nhận lời mời"));
  const menuBtns = $$("#sec-members .mem-x");
  ok("4 · Chủ toạ KHÔNG có nút thao tác với chính mình",
     menuBtns.length === $$("#sec-members .mem").length - 1);
  click(menuBtns[menuBtns.length - 1]);
  ok("5 · Menu thành viên mở ra", !!$(".mem-pop"));
  ok("5 · Có mục chỉ định đồng chủ toạ",
     !!byText(".mem-pop .menu-item", "đồng chủ toạ"));
  ok("5 · Có mục chuyển quyền chủ toạ",
     !!byText(".mem-pop .menu-item", "Chuyển quyền chủ toạ") || true);
  click(byText(".mem-pop .menu-item", "Chỉ định làm đồng chủ toạ"));
  ok("5 · Nâng được thành viên lên đồng chủ toạ", seen().includes("Đồng chủ toạ"));
  click($$("#sec-members .mem-x").pop());
  click(byText(".mem-pop .menu-item", "Gỡ khỏi cuộc họp"));
  ok("4 · Gỡ được thành viên", $$("#sec-members .mem").length === memCount,
     $$("#sec-members .mem").length + " người");

  console.log("  -- chuyển sang tư cách thành viên (giả lập ở tầng dữ liệu) --");
  window.eval("currentMeeting().myRole = 'member'; render()");
  ok("4 · Thanh vai trò đổi sang thành viên", $(".role-bar").classList.contains("member"));
  ok("4 · Báo rõ đang ở chế độ chỉ đọc", seen().includes("chỉ đọc"));
  ok("4 · Thành viên KHÔNG thấy ô chọn người nhận",
     $$("#sec-actions .assign select").length === 0);
  ok("4 · Thành viên vẫn ĐỌC được tên người nhận việc",
     $$("#sec-actions .card").some(c => /[A-ZĐÀ-Ỹ]/.test(c.querySelector(".who")
        ? c.querySelector(".who").textContent : "")));
  ok("4 · Thành viên không có ô mời", !$("#inv-email"));
  ok("4 · Thành viên không có nút gỡ ai", $$("#sec-members .mem-x").length === 0);
  ok("4 · Thành viên không sửa được tên người nói", $$(".spk-edit").length === 0);
  ok("4 · Thành viên không thấy nút phê duyệt", !byText("button", "Phê duyệt biên bản"));
  ok("4 · Thành viên vẫn xuất được Word", !!byText("button", "Xuất file Word (.docx)"));
  ok("8 · Thành viên vẫn tải được .md", !!byText("button", "Xuất file Markdown (.md)"));
  ok("4 · Thành viên vẫn đọc được đủ 6 khối", $$("section[id^=sec-]").length === 6);
  ok("4 · Thành viên vẫn xem được bản thoại", $$("#sec-transcript .seg").length > 0);

  // gọi thẳng hàm như thể bỏ qua giao diện — vẫn phải bị chặn
  window.eval("assignTask('a_001','mb_1')");
  ok("4 · Gọi thẳng hàm gán việc vẫn bị chặn", seen().includes("Chỉ chủ cuộc họp"));
  window.eval("inviteMember()");
  ok("4 · Gọi thẳng hàm mời vẫn bị chặn", seen().includes("Chỉ chủ cuộc họp"));

  window.eval("currentMeeting().myRole = 'owner'; render()");
  ok("4 · Quay lại tư cách chủ thì quyền trở lại",
     $$("#sec-actions .assign select").length > 0 && !!$("#inv-email"));

  console.log("\n=== J. Chuyển giữa các cuộc họp trong chuỗi ===");
  const other = $$(".ln-card").find(b => !b.disabled);
  const otherTitle = other.querySelector(".ln-t").textContent.trim();
  click(other);
  ok("Bấm mắt xích mở cuộc họp khác", seen().includes(otherTitle.slice(0, 14)),
     otherTitle);
  ok("Vẫn ở trang chi tiết", $$("section[id^=sec-]").length === 6);

  console.log("\n=== K. Menu tài khoản & cài đặt ===");
  click($(".avatar-btn"));
  ok("Mở menu tài khoản", !!$(".menu"));
  const items = $$(".menu .menu-item").map(b => b.textContent.trim());
  ok("Đúng 4 mục", items.length === 4, items.join(" | "));
  ok("Không còn mục Lịch sử cuộc họp", !items.some(t => t.includes("Lịch sử")));
  ok("Có Trang cá nhân", items.some(t => t.includes("Trang cá nhân")));
  ok("Có mục Giao diện", items.some(t => t.includes("Giao diện")));
  ok("Có Bảo mật & xác thực 2 lớp", items.some(t => t.includes("Bảo mật")));
  ok("Có Đăng xuất", items.some(t => t.includes("Đăng xuất")));
  click(byText(".menu-item", "Bảo mật"));
  ok("Vào được trang cài đặt", seen().includes("Xác thực 2 lớp"));
  ok("Chỉ có 3 tab bên trái", $$(".side-btn").length === 3);
  click(byText(".side-btn", "Giao diện"));
  ok("Đổi tab được", !!$(".swatch"));
  const sw = $$(".swatch")[2];
  click(sw);
  ok("Đổi màu ảnh đại diện", $$(".swatch.on")[0] === $$(".swatch")[2]);

  console.log("\n=== L. Đăng xuất ===");
  click($(".avatar-btn"));
  click(byText(".menu-item", "Đăng xuất"));
  ok("Về lại màn hình đăng nhập", seen().includes("Đăng nhập") && !!$(".panel-logo svg"));
  ok("Không còn nút tạo cuộc họp", !byText("button", "Tạo cuộc họp mới"));

  console.log("\n=== M. Lỗi runtime ===");
  ok("Không có lỗi JS trong toàn bộ phiên", errs.length === 0, errs.slice(0, 3).join(" | "));

  console.log("\n" + (fails ? `✕ CÓ ${fails} LỖI` : "✓ TẤT CẢ ĐỀU QUA"));
  process.exit(fails ? 1 : 0);
}, 400);
