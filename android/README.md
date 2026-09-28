# App Android của FlowyX

Kotlin thuần trên `Activity` của nền tảng: không AndroidX, không Jetpack
Compose (lý do ở [`docs/UIUX_QUYET_DINH.md`](../docs/UIUX_QUYET_DINH.md)).
Mọi thứ chạy trên máy; không có máy chủ nào phải bật.

Android 7.0 trở lên (`minSdk 24`), `targetSdk 34`.

---

## Build

Cần **JDK 17**. JDK 25 bị AGP 8.5.2 từ chối với một câu báo lỗi khó hiểu
(`What went wrong: 25.0.2`).

```bash
cd android
JAVA_HOME=/đường/dẫn/tới/jdk-17 ./gradlew :app:testDebugUnitTest   # test JVM, không cần máy thật
JAVA_HOME=/đường/dẫn/tới/jdk-17 ./gradlew :app:assembleDebug       # APK
```

APK ra ở `app/build/outputs/apk/debug/app-debug.apk`. Trên Windows dùng
`gradlew.bat`. Cách dễ nhất để có JDK 17 là để Android Studio tự tải:
*Settings → Build Tools → Gradle → Gradle JDK → Download JDK → 17*.

Không muốn build? CI xuất APK mỗi lần đẩy code — tải artifact
`flowyx-debug-apk` ở tab **Actions** trên GitHub.

### Khoá Gemini (tuỳ chọn)

Phần chia nhỏ việc gọi Gemini khi có khoá. Thêm vào `android/local.properties`:

```
GEMINI_API_KEY=...
```

Tệp này nằm trong `.gitignore`, không lên GitHub. Khoá gắn vào APK thì ai
có APK cũng lấy ra được — nên chỉ dùng khoá riêng cho bản build của mình.
Không có khoá thì app dùng `MauProvider`, sinh bước mẫu ngay trên máy.
Chi tiết ở đầu `PhanRaProvider.kt`.

---

## Các lớp

Mã nguồn ở `app/src/main/java/vn/adc2026/wayfinding/` (tên gói còn giữ từ
dự án cũ).

### Màn hình

| Nhóm | Tệp |
|---|---|
| Năm tab | `ViecCanLamActivity` (Kế hoạch), `LichActivity`, `FocusActivity` (Tập trung), `NhatKyActivity` (Sức khỏe), `MeetyActivity` |
| Khung chung | `TrangCoTab` (lớp cha của mọi tab), `ThanhTab` (thanh tab dưới) |
| Màn con | `KeHoachActivity`, `GoRoiActivity`, `PhanRaActivity`, `VietNhatKyActivity`, `SucKhoeActivity`, `GhiBienBanActivity`, `BienBanVaoLichActivity`, `NhapLichActivity`, `CaiDatActivity`, `PhapLyActivity` |
| Vào app | `KhoiDongActivity`, `ChonNgonNguActivity`, `DangNhapActivity`, `DangKyActivity`, `QuenMatKhauActivity`, `HuongDan` (hướng dẫn lần đầu) |

### Dữ liệu — tất cả nằm trên máy

| Tệp | Làm gì |
|---|---|
| `KhoDuLieu`, `MaHoa`, `TaiKhoan` | SQLite; nhật ký và sức khoẻ mã hoá AES-256-GCM, khoá trong Android Keystore; mật khẩu băm PBKDF2 |
| `Lich`, `SoLich`, `LichBao`, `DocIcs` | Logic lịch thuần (test được trên JVM), lưu lịch, đặt chuông, nhập `.ics` |
| `SoNhac`, `BaoGio`, `NhacCaiDat` | Lời nhắc; chuông báo và receiver khởi động lại máy |
| `SoThoiLuong`, `SoTienDo` | Ước lượng so với thời gian thật; chuỗi ngày |
| `SoNhatKy`, `SucKhoe`, `SucKhoeHC`, `SucKhoeBang` | Nhật ký; Health Connect (chỉ đọc, mặc định tắt) |
| `SoBienBan`, `DocxViet` | Biên bản họp; xuất Word hai bản (tiêu chuẩn và dễ đọc) |
| `PhanRa`, `PhanRaProvider` | Chia nhỏ việc: đọc JSON của mô hình, chặn cứng 5 bước; nguồn Gemini hoặc bản mẫu |
| `XuatDuLieu`, `AppSettings` | Xuất dữ liệu; tuỳ chọn |

### Giao diện và vào ra

| Tệp | Làm gì |
|---|---|
| `GiaoDien`, `CheDoToi`, `NgonNgu`, `MauDongHo` | Font Lexend, sáng/tối, vi/en, màu đồng hồ |
| `Speaker`, `Rung` | Đọc tiếng Việt, rung, âm ngắn |
| `KiemQuyen` | Liệt kê quyền còn thiếu, dẫn tới đúng trang cấp |

Module `../frontend/` giữ ba View vẽ tay: `VongTapTrungView` (đồng hồ
vòng), `TrongCuonView` (trống cuộn chọn giờ), `PhaoHoaView`.

---

## Quyền

Chỉ `INTERNET` (cho Gemini), rung, thông báo, báo thức chính xác, khởi
động lại, và hai quyền đọc Health Connect. Không camera, không micro,
không vị trí, không danh bạ. Lý do từng quyền ghi ngay trong
`AndroidManifest.xml`.

## App không bao giờ chủ động bắt chuyện

App chỉ đọc lên thành tiếng khi người dùng bấm. Hiện chữ trên màn hình là
thụ động và không đòi hỏi gì; đọc lên thành tiếng là bắt chuyện.
