# App Android của Flowy

Điện thoại làm **màn hình và đầu vào**, laptop làm **bộ não**.

Không có quy tắc nào của Flowy nằm ở đây, và đó là chủ ý. App không biết
khi nào nên hỏi gì, khi nào nên đổi nét mặt, hay một bước coi là kẹt bao
lâu — tất cả nằm ở `adc_wayfinding/run_flowy.py`, đã có test, và bản iOS
sẽ chạy cùng logic đó.

Viết quy tắc ở cả hai nơi là có hai bản quy tắc phải giữ khớp nhau bằng
tay, và chúng sẽ lệch.

App làm đúng ba việc:

1. gửi **sự kiện người dùng** lên cầu nối
2. hiện và đọc lên những gì cầu nối trả về
3. **giữ** ba sổ của riêng máy này

---

## Trạng thái

Cập nhật 21/09/2026.

| | |
|---|---|
| Giao diện v5 (năm tab, bảng màu đêm viết lại) | ✅ xem [`docs/GIAO_DIEN_V5.md`](../docs/GIAO_DIEN_V5.md) |
| Biên dịch Kotlin, Android API 34 | ✅ sạch |
| Test đơn vị Kotlin | ✅ **162 bài qua** |
| Build APK | ✅ CI xuất APK mỗi lần đẩy code — tải từ tab **Actions** |
| Sáng / Tối / Theo máy | ✅ `CheDoToi.kt` |
| Tiếng Việt / English | ✅ cả hai |
| Chạy trên máy thật | Galaxy Tab S7 FE (bản trước v5). Lỗi: [`BAO_LOI/`](../BAO_LOI/README.md) |

> **Cách nhanh nhất để lấy bản mới lên máy thật:** vào tab **Actions** trên
> GitHub, mở lần chạy mới nhất, tải artifact `flowyx-debug-apk`. Không cần
> cài Android Studio, không cần JDK, không cần ai build hộ.

## Chạy thử

Cần **JDK 17**. JDK 25 bị AGP 8.5.2 từ chối với một câu báo lỗi khó hiểu
(`What went wrong: 25.0.2`).

```bash
cd android
JAVA_HOME=/đường/dẫn/tới/jdk-17 ./gradlew :app:testDebugUnitTest
```

Build APK:

```bash
JAVA_HOME=/đường/dẫn/tới/jdk-17 ./gradlew :app:assembleDebug
```

Rồi cài, mở app, bấm **Cài đặt**, nhập địa chỉ mà `run_flowy.py` in ra
lúc khởi động.

---

## Các lớp

### Màn hình

| Tệp | Layout |
|---|---|
| `MainActivity.kt` | `activity_main.xml` (điện thoại), `layout-sw600dp/activity_main.xml` (tablet) — ghép từ `khoi_*.xml` |
| `LichActivity.kt` | `activity_lich.xml` (+ bản sw600dp) |
| `KeHoachActivity.kt` | `activity_ke_hoach.xml` — tạo/sửa kế hoạch |
| `CaiDatActivity.kt` | `activity_settings.xml` — laptop, giao diện, giọng đọc, kiểm tra quyền |
| `GiaoDien.kt` | sáng/tối và font Lexend cho mọi màn hình |

### Cầu nối (chỉ khi test / demo)

| Tệp | Làm gì |
|---|---|
| `Payload.kt` | Dựng và đọc gói tin JSON. Hợp đồng ở `loi_chung/bridge.py` |
| `BridgeClient.kt` | Gửi trên luồng nền. Gói có thao tác người dùng xếp hàng, không bao giờ bị đè |

### Dữ liệu của riêng máy này — không qua cầu nối

| Tệp | Làm gì |
|---|---|
| `Lich.kt` | Logic lịch thuần (lặp lại, các lần nhắc, kế hoạch tiếp theo) — test được trên JVM |
| `SoLich.kt`, `LichBao.kt` | Lưu lịch; đặt chuông cho 48 lần nhắc gần nhất |
| `SoThoiLuong.kt` | Ước lượng và thời gian thật của từng việc |
| `SoNhac.kt`, `BaoGio.kt` | Lời nhắc hằng ngày; receiver khởi động lại máy |
| `SoNhatKy.kt` | Nhật ký |

### Đầu vào / đầu ra

| Tệp | Làm gì |
|---|---|
| `Speaker.kt` | Đọc tiếng Việt, rung, âm ngắn; mở cài đặt giọng đọc |
| `VoiceInput.kt` | Nhận dạng giọng nói trên máy |
| `KiemQuyen.kt` | Liệt kê quyền còn thiếu, dẫn tới đúng trang cấp |
| `DocGio.kt` | Đọc giờ gõ tay: `14:00`, `1400`, `930`, `14h30` |
| `Accessibility.kt` | TalkBack |

Module `frontend/` chỉ còn `TimerTronView` (vòng thời gian). Nhân vật đồng hành đã bỏ.

---

## Ranh giới dữ liệu — đọc trước khi thêm trường vào gói tin

Bảng ở đầu `bridge.py`:

| được mang | **KHÔNG BAO GIỜ** được mang |
|---|---|
| đang làm việc gì | nhật ký cảm xúc |
| còn bao nhiêu phút | ghi chú về triệu chứng |
| lệnh hiển thị | tên các lời nhắc người dùng tự đặt |
| câu nói, mã rung | sổ thời lượng (lịch sử làm việc) |

Nên **`SoNhac` và `SoNhatKy` không được chạm vào `Payload` hay
`BridgeClient`.** Chúng sống trọn vẹn trên máy người dùng; bản Python là
bản gốc để đối chiếu.

Đây là thứ rất dễ vô tình phá — thêm một dòng `import` cho tiện là đủ. Mã
hỏng kiểu đó không làm test nào đổ, không làm app sập; nó chỉ lặng lẽ đưa
dữ liệu cá nhân lên đường truyền.

`lich_su` là ngoại lệ **có kiểm soát**: chỉ lịch sử của đúng một công
việc đang làm, gửi đi rồi thôi. Laptop không ghi gì xuống đĩa.

---

## App không bao giờ chủ động bắt chuyện

`docs/luu-tru/NHAN_VAT_BRIEF.md` mục 2.4 — nhân vật đã bỏ, nguyên tắc giữ.
Nút **Gợi ý** là lời mời **duy nhất** để app đọc lên một câu hỏi. Trường gói tin
vẫn tên `cham_nhan_vat` để không phá hợp đồng với laptop.

| | |
|---|---|
| **hiện chữ trên màn hình** | thụ động. Không đòi hỏi gì |
| **đọc lên thành tiếng** | app bắt chuyện |

