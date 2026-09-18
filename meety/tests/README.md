# Kiểm thử Meety

Bảy bộ, mỗi bộ soi một tầng khác nhau. Chạy tất cả:

```powershell
python -m pytest tests/ -q          # 864 phép kiểm Python
python tools/smoke_server.py        # 74 phép kiểm qua HTTP thật
node tests/frontend/dom_test.js     # 204 phép kiểm giao diện, chế độ RỜI máy chủ
node tests/frontend/online_test.js  # 42 phép kiểm giao diện NỐI máy chủ thật
```

## Bộ nào làm gì

| Bộ | Số | Soi vào |
|---|---|---|
| `test_security_unit.py` | 36 | scrypt, token phiên, TOTP — có vector chuẩn RFC 4226/6238 |
| `test_store_unit.py` | 42 | ràng buộc lược đồ, xoá dây chuyền, luật khớp tên tự động |
| `test_api_security.py` | 61 | CSRF, IDOR, chèn mã, rò rỉ, nâng quyền |
| `test_api_validation.py` | 86 | biên, sai kiểu, hợp đồng HTTP |
| `test_api_concurrency.py` | 19 | đua nhau, lặp yêu cầu, khởi động lại |
| `test_jobs_unit.py` | 27 | ánh xạ pha, đường thất bại, chạy đầu-cuối |
| `test_server_api.py` | 89 | luồng người dùng, phân quyền, đồng chủ toạ, task CRUD, audio Range, DOCX |
| `test_ai_layer.py` | 40 | agent chống bịa, ẩn danh PII, đối soát hai mô hình |
| `test_evaluator.py` | 20 | Meeting-Bench: bốn thước đo, xếp hạng mô hình |
| `tools/smoke_server.py` | 93 | bật uvicorn thật, đi hết hành trình qua HTTP |
| `tests/frontend/dom_test.js` | 245 | frontend ở chế độ RỜI máy chủ, dữ liệu nhúng |
| `tests/frontend/online_test.js` | 65 | **hai tài khoản song song + máy chủ thật** |

Bốn bộ đầu chạy **trong tiến trình**, không mở cổng — nhanh, hợp cho vòng lặp
sửa-chạy. `smoke_server.py` mở cổng thật, bắt được lớp lỗi mà `TestClient`
không thấy: cookie không qua được, multipart hỏng khi đi qua mạng, cổng không
mở, tệp tĩnh không phục vụ được.

## Vì sao tách nhiều bộ thay vì một file lớn

Mỗi bộ hỏi một câu khác nhau, nên khi có bộ đỏ là biết ngay tầng nào hỏng.
Một file 700 phép kiểm thì đỏ ở đâu cũng như nhau.

## Những lỗi các bộ này đã bắt được

Ghi lại để biết bộ nào đáng giữ:

| Lỗi | Bắt bởi | Mức |
|---|---|---|
| Segfault sập tiến trình khi đóng kết nối SQLite lúc luồng nền đang ghi | `test_api_security` (chạy cả file) | nghiêm trọng |
| Phiên chưa qua 2FA vẫn đá được mọi phiên khác của nạn nhân | `test_api_security` | lỗ hổng |
| Đăng ký cùng email đồng thời → 500 thay vì 409 | `test_api_concurrency` | trung bình |
| TOTP nhận chữ số Ả Rập → 500 thay vì 401 | `test_security_unit` | trung bình |
| Lỗi trong đoạn xử-lý-lỗi giết luồng nền và che mất lỗi gốc | `pytest tests/` (cảnh báo luồng) | trung bình |
| `date.fromisoformat` cho kết quả khác nhau trên Python 3.10 và 3.12 | `test_api_validation` | nhẹ |
| `/api/meetings/upload` bị bỏ sót khỏi danh sách kiểm CSRF | `test_route_list_covers_every_write_endpoint` | nhẹ |
| Tên tệp tải lên còn giữ `..` sau khi lọc | `test_api_security` | nhẹ |
| Tiêu đề người dùng gõ bị `meta.title` trong tệp ghi đè | `test_server_api` | nhẹ |
| **Đăng nhập kẹt ở "Đang xử lý"** — thẻ cuộc họp gọi `resolveSpeakers(mt.transcript)` nhưng `/api/meetings` cố ý không trả bản thoại | `online_test` (bộ mới) | nghiêm trọng |
| **`MEETY_DB` không được đọc** — smoke test ghi thẳng vào DB thật của người dùng thay vì DB tạm | `online_test` (bộ mới) | nghiêm trọng |
| `requirements.txt` chứa tiếng Việt có dấu — pip trên Windows đọc bằng cp1252 và chết trước khi cài gì | `doctor.py` | trung bình |
| **Member không bao giờ thấy việc được gán** — `ensureTranscript` thoát sớm khi đã có bản thoại, nên không nạp lại `assignments` | `online_test` (hai tài khoản) | nghiêm trọng |
| **CSS sửa thước đo không được ghi vào file** — `grep -c` trả 0 kết quả nên exit code 1, chặn luôn lệnh `python` phía sau `&&` | kiểm bằng mắt sau khi user báo lại | nghiêm trọng |
| Đồng chủ toạ gỡ được thành viên và bãi nhiệm co-host khác | `test_server_api` | trung bình |
| **Biên bản RỖNG được 0.45 điểm** — thước đo phụ trả recall 1.0 khi không có gì để chấm, nên "không làm gì" hơn "làm sai" | `test_evaluator` | nghiêm trọng |
| Hạn chót `2026-13-01` lưu được vào DB — regex chỉ kiểm hình dạng, không kiểm tháng 13 có thật không | `test_server_api` | trung bình |
| `set_assignment` xoá mất trạng thái việc khi đổi người nhận | `test_server_api` | trung bình |
| Sáu route ghi mới quên đưa vào danh sách kiểm CSRF | `test_route_list_covers_every_write_endpoint` | nhẹ |
| **Tên người nói lộ nguyên trong tệp huấn luyện** — chỉ ẩn danh nội dung câu, quên nhãn đầu dòng | `test_ai_layer` | nghiêm trọng |
| `close_all()` đóng kết nối của luồng nền đang chạy — tái tạo lại chính con segfault nó sinh ra để chữa | `pytest tests/` (chạy chung) | nghiêm trọng |
| `set_assignment` ghi đè cả hàng, xoá mất trạng thái công việc khi đổi người nhận | `test_server_api` | trung bình |
| `list_assignments` không trả hai cột mới → giao diện không thấy trạng thái | `test_server_api` | trung bình |

## Vì sao cần bộ `online_test.js`

Ba bộ cũ có một khe hở lớn mà không bộ nào nhìn thấy:

```
dom_test.js       frontend ở chế độ RỜI máy chủ  (dữ liệu nhúng)
smoke_server.py   máy chủ thật, KHÔNG có frontend
test_*.py         từng tầng backend riêng
```

Không bộ nào phủ **chỗ nối** giữa hai bên. Khe hở đó để lọt một lỗi làm hỏng
hoàn toàn việc đăng nhập: `/api/meetings` cố ý không trả `transcript` (nặng
gấp nhiều lần biên bản, trang tổng quan không cần), nhưng thẻ cuộc họp lại gọi
`resolveSpeakers(mt.transcript)`. Chạy rời máy chủ thì mọi cuộc họp đều có
transcript nhúng sẵn nên lỗi **không bao giờ lộ**.

Triệu chứng người dùng gặp: nút kẹt ở "Đang xử lý…", trong khi log máy chủ
toàn `200 OK`. Nhìn log thì tưởng backend hỏng; thực ra backend đúng hoàn toàn
và frontend ném lỗi lúc dựng màn hình.

**Bài học chung: dữ liệu nhúng và dữ liệu máy chủ có hình dạng khác nhau.**
Mỗi khác biệt về hình dạng là một chỗ có thể vỡ, và chỉ bộ nối thật nhìn thấy.

## Hai phép kiểm tự bảo vệ chính bộ kiểm thử

`test_route_list_covers_every_write_endpoint` đối chiếu danh sách route ghi
viết tay với `app.routes` thật. Thêm endpoint mới mà quên kiểm CSRF thì nó tố
cáo ngay — nó đã bắt được đúng một lần như vậy.

`test_stage_names_cover_every_orchestrator_stage` đối chiếu `STAGE_VI` với
`STAGE_ORDER` của orchestrator. Thêm pha vào pipeline mà quên đặt tên hiển thị
thì thanh tiến trình sẽ nhảy cóc, và người dùng tưởng hệ thống treo.

## Lưu ý khi viết thêm

**jsdom:** `document.body.textContent` gộp cả nội dung thẻ `<script>`, tức là
toàn bộ JSON nhúng và mã nguồn. Đo trên đó thì mọi phép kiểm kiểu "không lộ mã
kỹ thuật ra màn hình" đều báo sai. Dùng hàm `seen()` trong `dom_test.js`.

**Luồng nền:** fixture phải gọi `store.close_all()`, không phải `store.close()`.
`close()` chỉ đóng kết nối của luồng hiện tại; kết nối của luồng nền còn sót
lại sẽ giữ file DB tạm và làm hỏng lần dọn dẹp.
