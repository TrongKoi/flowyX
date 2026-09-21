# Kiến trúc Flowy

Hệ thống gồm những gì, file nào làm việc gì, và dữ liệu chảy đi đâu.
Đọc file này trước khi mở bất cứ file mã nguồn nào.

> **Viết lại 21/09/2026.** Bản trước mô tả *“BoussoleX — hai chế độ, ADHD
> và khiếm thị, ba nhánh `adhd/` `khiemthi/` `loi_chung/`”*. Điều đó đã
> không còn đúng từ 15/09, ngày hai sản phẩm tách ra: phần khiếm thị
> chuyển sang repo [opticguard](https://github.com/TrongKoi/opticguard).
> Repo này chỉ còn **Flowy**, và chỉ còn **hai** nhánh mã nguồn.

---

## 1. Một sản phẩm, ba lần hiện thực

Flowy là trợ thủ quản lý thời gian cho người ADHD. Cùng một bộ quy tắc
được viết ba lần, và **bản Python là bản gốc**:

| Nơi | Vai trò |
|---|---|
| `adc_wayfinding/` | **Bản gốc.** Quy tắc + test. Sửa quy tắc thì sửa ở đây trước |
| `android/` | Bản dịch thứ nhất — Kotlin |
| `ios/` | Bản dịch thứ hai — SwiftUI |

Viết quy tắc ở ba nơi nghĩa là có ba bản phải giữ khớp nhau bằng tay, và
chúng **sẽ** lệch. Nên có một bài test riêng canh việc đó:
`android/app/src/test/.../DoiChieuBanPythonTest.kt` chạy cùng một gói tin
qua cả hai bản và so kết quả.

---

## 2. Cái gì chạy trên máy, cái gì cần laptop

Đây là chỗ hay hiểu nhầm nhất.

| Tính năng | Cần laptop? |
|---|---|
| Lịch, kế hoạch, lời nhắc, nhật ký, đồng hồ Tập trung, Meety | **Không.** Chạy trọn trên điện thoại |
| Luồng hỏi–đáp dẫn dắt (ý định thực thi, khôi phục mạch, Gỡ rối) | Có, trong giai đoạn thử nghiệm |

Phần quy tắc chạy trên laptop **chỉ để phát triển**: sửa thuật toán rồi
chạy lại test trong vài giây, thay vì build lại APK mỗi lần. Bản phát
hành sẽ port phần này sang Kotlin/Swift.

---

## 3. `wayfinding/adhd/` — quy tắc riêng của Flowy

| File | Nhiệm vụ |
|---|---|
| `timeblind.py` | **Chống mù thời gian.** Neo mọi câu vào giờ thật trên đồng hồ, tính mốc phải bắt đầu, so ước lượng với thời gian thực tế |
| `thoiluong.py` | Sổ thời lượng: người này ước bao lâu, thật ra mất bao lâu |
| `mach.py` | Khôi phục mạch sau khi bị cắt ngang: đang làm gì, còn mấy bước, bước trước mắt |
| `cauhoi.py` | Ý định thực thi — hỏi đủ *việc gì / khi nào / ở đâu* trước khi bắt đầu |
| `phien.py` | Một phiên làm việc: các bước, bước đang làm, tạm dừng |
| `dongvien.py` | Câu phản hồi. **Không bao giờ thể hiện thất vọng** |
| `nhacviec.py` | Lời nhắc hằng ngày do người dùng tự đặt tên |
| `nhatky.py` | Nhật ký bằng chữ của người dùng. App không chấm điểm, không diễn giải |
| `meety.py` | Gọi Meety tóm tắt biên bản, xuất `.md` / `.docx` |

## 4. `wayfinding/loi_chung/` — hạ tầng, không mang quy tắc

| File | Nhiệm vụ |
|---|---|
| `bridge.py` | Giao thức điện thoại ↔ laptop. **Bảng ở đầu file quy định dữ liệu nào không bao giờ được rời máy** |
| `announce.py` | Nhiều nguồn cùng muốn nói thì nói câu nào |
| `speech.py` | Đầu ra giọng nói và mã rung |
| `session.py` | Ghi lại phiên để phát lại khi gỡ lỗi |
| `health.py` | Pin, độ trễ, tình trạng lúc chạy |
| `metrics.py` | Chỉ số nghiệm thu. Chỉ số chưa đo thì báo **“chưa đo”**, không bao giờ báo đạt |

## 5. Ranh giới dữ liệu — đọc trước khi thêm trường vào gói tin

Bảng ở đầu `bridge.py`:

| Được mang | **KHÔNG BAO GIỜ** được mang |
|---|---|
| đang làm việc gì | nhật ký cảm xúc |
| còn bao nhiêu phút | ghi chú về triệu chứng |
| lệnh hiển thị | tên các lời nhắc người dùng tự đặt |
| câu nói, mã rung | sổ thời lượng (lịch sử làm việc) |

Nên `SoNhac` và `SoNhatKy` **không được chạm vào** `Payload` hay
`BridgeClient`. Đây là thứ rất dễ vô tình phá: thêm một dòng `import` cho
tiện là đủ. Mã hỏng kiểu đó không làm test nào đổ, không làm app sập — nó
chỉ lặng lẽ đưa dữ liệu cá nhân lên đường truyền.

---

## 6. `android/` — bản dịch Kotlin

Năm tab: **Kế hoạch · Lịch · Tập trung · Sức khỏe · Meety**. Mỗi tab là
một Activity riêng; thanh tab nối ở một chỗ duy nhất (`ThanhTab.kt`) và
viên thuốc kính trượt qua ranh giới giữa hai Activity.

Không dùng Jetpack Compose — lý do ở `UIUX_QUYET_DINH.md`.

| Nhóm | File tiêu biểu |
|---|---|
| Màn hình | `ViecCanLamActivity`, `LichActivity`, `FocusActivity`, `NhatKyActivity`, `MeetyActivity`, `CaiDatActivity` |
| Sổ trên máy | `SoLich`, `SoNhac`, `SoNhatKy`, `SoThoiLuong`, `SoBienBan`, `SoTienDo` |
| Tài khoản | `TaiKhoan`, `KhoDuLieu`, `MaHoa`, `DangNhapActivity`, `DangKyActivity` |
| Giao diện | `GiaoDien` (font + bọc Context), `CheDoToi` (sáng/tối), `NgonNgu` (vi/en) |
| Vào ra | `Speaker`, `VoiceInput`, `Rung`, `KiemQuyen`, `DocIcs`, `DocxViet` |

## 7. `ios/` — bản dịch SwiftUI

iOS 16+, chạy cả iPhone (một cột) và iPad (hai cột). Mỗi file Swift có
bản Kotlin cùng vai trò trong `android/`. Sửa quy tắc hay câu chữ ở một
bên thì sửa cả bên kia.

## 8. `meety/` — dự án con, chép hẳn vào repo

Hệ tóm tắt biên bản cuộc họp, gọi qua tiến trình con từ
`wayfinding/adhd/meety.py`.

Đã **cắt bỏ** `frontend/`, `server/`, `run_server.py` của Meety: chúng
dùng để hiện biên bản trên web, mà Flowy không hiện UI biên bản — Meety
xuất thẳng ra `.md` / `.docx`.

> Vì đã cắt, `meety/tests/test_api_*.py`, `test_server_api.py`,
> `test_store_unit.py`, `test_jobs_unit.py`, `test_security_unit.py` và
> `tests/unit/test_frontend_contract.py` là **test mồ côi** — chúng kiểm
> phần mã không còn ở đây. Chạy sẽ đỏ. Đó là chuyện đã biết, không phải
> lỗi mới.

Chạy phần còn dùng được:

```bash
cd meety
python -m pytest tests/unit tests/integration -q
```

---

## 9. Kiểm thử

```bash
cd adc_wayfinding && python -m pytest tests -q          # 442 test, lõi quy tắc
cd android && ./gradlew :app:testDebugUnitTest          # 162 test Kotlin, cần JDK 17
cd meety && python -m pytest tests/unit -q              # Meety
```

`adc_wayfinding` phải đứng đúng trong thư mục đó — một test dùng đường
dẫn tương đối. Android cần **JDK 17**: AGP 8.5.2 từ chối JDK 25 với một
câu báo lỗi khó hiểu (`What went wrong: 25.0.2`).

Cả ba chạy tự động trên CI mỗi lần đẩy code — xem
[`.github/workflows/build.yml`](../.github/workflows/build.yml). Job
Android còn **xuất APK tải về được** từ tab Actions.

---

## 10. `phan_khiem_thi/` — bản sao đã ngừng bảo trì

Không nằm trong đường chạy của Flowy. `adc_wayfinding/` không import gì từ
đây. Bản đang được bảo trì nằm ở repo **opticguard**; sửa ở đây sẽ không
đi đâu cả.

## 11. `thu_nghiem/` — code đã cất

Không nằm trong đường chạy của app, `pytest` không quét. Mỗi thư mục con
có `README.md` riêng ghi cách lấy lại.
