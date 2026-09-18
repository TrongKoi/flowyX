# Sửa lỗi sau buổi test 16/09/2026

Máy test: Galaxy Tab S7 FE, One UI 6.1 (Android 14).

> **Lưu ý:** commit `4c8bae9 fixed permission + input errors` chỉ đổi tên
> `Settings.kt → AppSettings.kt`, thêm `activity_settings.xml` rỗng và một
> dòng `chuoi.json`. Hai bug được đánh dấu "đã sửa" trong file docx
> (ô giờ, quyền báo thức) **không có trong commit đó**. Nếu bản sửa nằm ở
> máy ai đó mà chưa push, hãy so với bản dưới đây trước khi merge.

## Trạng thái từng mục

| # | Mục | Nguyên nhân thật | Sửa ở đâu |
|---|---|---|---|
| 1 | Thêm lời nhắc thiếu dữ liệu → dialog đóng | `AlertDialog` tự đóng khi bấm nút tích cực | `MainActivity.themLoiNhac()` — ghi đè nút trong `setOnShowListener`, báo lỗi tại ô thiếu, chỉ đóng khi hợp lệ |
| 2 | Ô giờ chỉ có bàn phím số | `TYPE_CLASS_DATETIME` + `docGio` bắt buộc dấu `:` | Chạm ô giờ mở `TimePickerDialog` 24h; gõ tay vẫn được, `DocGio` nhận `1400`, `930`, `14h30`, `14.30` |
| 3 | Crash `SCHEDULE_EXACT_ALARM` | Comment cũ sai: từ Android 12 `setAlarmClock` **cũng** cần quyền này, Android 14 tắt mặc định | Khai báo quyền; `BaoGio.datLai` hỏi `canScheduleExactAlarms()`, chưa có thì dùng chuông có thể trễ vài phút (không crash) và hỏi người dùng bật |
| 4 | Nhật ký mở lại trống, xuất tệp vẫn đủ | Gọi cả `setMessage` và `setAdapter` — Android bỏ danh sách khi có message | Câu ghi chú chuyển vào `setCustomTitle`; thêm chạm để xoá mục |
| F1 | Không có giọng TTS tiếng Việt → mở đúng cài đặt | — | `Speaker.moCaiDatGiongDoc()`: thử `ACTION_INSTALL_TTS_DATA` → `TTS_SETTINGS` → Cài đặt chung |
| F2 | Mục kiểm tra quyền trong Cài đặt | — | `KiemQuyen.kt` + nút "Kiểm tra quyền" |

## Lỗi tìm thêm khi đọc code

| Lỗi | Hậu quả | Đã sửa |
|---|---|---|
| Không bao giờ xin quyền `RECORD_AUDIO` | Nút **Nói** luôn báo "chưa nghe được" trên máy mới cài | ✅ xin khi bấm Nói |
| Không đặt lại chuông sau khi khởi động lại máy | Sạc qua đêm → sáng ra mất hết lời nhắc | ✅ `BaoGio.KhoiDongReceiver` |
| `cau_mo_dau()` trong `run_flowy.py` không được gọi | Bấm Bắt đầu xong app im lặng, câu chống mù thời gian §3.1 không bao giờ được nói | ✅ + 4 test |
| Laptop chỉ gửi `ten_viec` sau khi có phiên | Điện thoại không gửi lịch sử kịp → không có câu "những lần trước việc này mất khoảng X phút" | ✅ + 2 test |
| Lớp tên `Settings` trùng `android.provider.Settings` | Không dùng được hằng số cài đặt hệ thống | ✅ đổi thành `AppSettings` |
| Nhật ký có hàm xoá nhưng giao diện không gọi | Trái với thiết kế "người dùng phải xoá được bất cứ mục nào" | ✅ |

## Kiểm chứng

- Python: `pytest tests -q` → **408 passed** (402 cũ + 6 mới).
- Kotlin: toàn bộ `app` + `frontend` biên dịch sạch với `android.jar` API 34.
- `DocGio`: kiểm bằng script với 21 trường hợp; `DocGioTest.kt` đã thêm cho `gradlew testDebugUnitTest`.
- **Chưa chạy trên máy thật.** Checklist cho buổi cắm máy:

1. Cài mới → thêm lời nhắc để trống cả hai ô → dialog còn mở, hai ô báo lỗi.
2. Chạm ô giờ → hiện đồng hồ chọn giờ. Gõ tay `1400` → nhận.
3. Thêm lời nhắc (Android 14, chưa bật quyền) → **không crash**, hiện hộp giải thích → Mở cài đặt → bật → quay về.
4. Đặt lời nhắc 2 phút tới, tắt màn hình → thông báo hiện.
5. Khởi động lại máy → lời nhắc vẫn còn chuông.
6. Nhật ký: ghi 2 mục → đóng → mở lại → thấy cả 2. Chạm một mục → xoá được.
7. Cài đặt → Kiểm tra quyền → từng dòng ✗ chạm vào mở đúng trang.
8. Máy chỉ có Samsung TTS → mở app → hộp "Chưa có giọng tiếng Việt" → Mở cài đặt.
9. Bấm Nói lần đầu → hộp xin quyền micro → cho phép → bắt đầu nghe luôn.

---

## Đợt 2 (cùng ngày): lỗi tìm thêm khi làm giao diện v2

| Lỗi | Hậu quả | Sửa ở |
|---|---|---|
| Cầu nối chỉ giữ **một** gói chờ gửi | Mạng chậm → gói của vòng lặp đè mất gói có lệnh. Bấm "Xong bước" mà không có tác dụng | `BridgeClient.kt`, `BridgeClient.swift`: hàng ưu tiên cho gói có thao tác |
| Bấm Bắt đầu lần hai tạo phiên mới | Mất hết các bước đã thêm | `run_flowy.py` `_bat_dau` |
| `_da_bao_xong` kẹt `True` sau phiên đầu | Làm lại việc lần 2 không bao giờ báo xong, không ghi thời lượng | `run_flowy.py` |
| Bước nói trước khi bấm Bắt đầu bị bỏ | Người dùng liệt kê bước trước rồi mới bắt đầu thì mất hết | `run_flowy.py` `_buoc_cho` |
| Tạm dừng chỉ có tác dụng trong một gói tin | Nút tạm dừng (nếu có) vô dụng sau 0,5 giây | `run_flowy.py` `_tam_dung`/`_tiep_tuc` |
| Không có đường làm việc mới | Xong một việc thì 3 ô ý định vẫn đầy | lệnh `viec_moi` |
| Dòng trạng thái được đọc to bằng TTS | "Lỗi mạng" bị đọc lặp lại — trái nguyên tắc không chủ động lên tiếng | `MainActivity.datTrangThai` |
| Font đề xuất (Atkinson Hyperlegible) thiếu dấu tiếng Việt | Kiểm bằng fontTools trước khi dùng → đổi sang Lexend | `GiaoDien.kt` |

Test Python: **442 passed**.
