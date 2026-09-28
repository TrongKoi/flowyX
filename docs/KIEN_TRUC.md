# Kiến trúc FlowyX

Hệ thống gồm những gì, file nào làm việc gì, và dữ liệu chảy đi đâu.
Đọc file này trước khi mở bất cứ file mã nguồn nào.

> **Viết lại 28/09/2026**, sau đợt dọn repo khi cuộc thi kết thúc. Đã bỏ:
> lõi quy tắc Python `adc_wayfinding/` cùng màn “Phiên có laptop”, bản
> iOS, và bản sao phần khiếm thị (đã chuyển sang repo
> [opticguard](https://github.com/TrongKoi/opticguard) từ 15/09). Lịch sử
> đầy đủ trước khi dọn vẫn nằm ở nhánh `master`.

---

## 1. Hai phần

| Nơi | Vai trò |
|---|---|
| `android/` + `frontend/` | **App FlowyX.** Chạy trọn trên điện thoại, không cần máy chủ |
| `meety/` | Công cụ Python chạy trên máy tính: biến bản ghi họp thành `_minutes.json` để nhập vào tab Meety |

Hai phần nối với nhau **chỉ qua một tệp JSON** mà người dùng tự mở trong
app. Không có mạng, không có cầu nối, không có giao thức nào khác.

---

## 2. `android/` — app

Năm tab: **Kế hoạch · Lịch · Tập trung · Sức khỏe · Meety**. Mỗi tab là
một Activity riêng, cùng kế thừa `TrangCoTab`; thanh tab nối ở một chỗ
duy nhất (`ThanhTab.kt`).

Không dùng AndroidX hay Jetpack Compose — lý do ở `UIUX_QUYET_DINH.md`.

| Nhóm | File tiêu biểu |
|---|---|
| Màn hình | `ViecCanLamActivity`, `LichActivity`, `FocusActivity`, `NhatKyActivity`, `MeetyActivity`, `CaiDatActivity` |
| Sổ trên máy | `SoLich`, `SoNhac`, `SoNhatKy`, `SoThoiLuong`, `SoBienBan`, `SoTienDo` |
| Tài khoản | `TaiKhoan`, `KhoDuLieu`, `MaHoa`, `DangNhapActivity`, `DangKyActivity` |
| Chia nhỏ việc | `PhanRa`, `PhanRaProvider`, `PhanRaActivity` |
| Giao diện | `GiaoDien` (font + bọc Context), `CheDoToi` (sáng/tối), `NgonNgu` (vi/en), `HuongDan` |
| Vào ra | `Speaker`, `Rung`, `KiemQuyen`, `DocIcs`, `DocxViet` |

Bảng đầy đủ từng tệp: [`android/README.md`](../android/README.md).

`frontend/` là module Android riêng, chỉ chứa ba View vẽ tay:
`VongTapTrungView`, `TrongCuonView`, `PhaoHoaView`.

---

## 3. Dữ liệu đi đâu

| Dữ liệu | Ở đâu |
|---|---|
| Kế hoạch, lịch, lời nhắc, biên bản | SQLite của app, trên máy |
| Nhật ký, cảm xúc, sức khoẻ | SQLite, **mã hoá AES-256-GCM**, khoá trong Android Keystore |
| Mật khẩu | Chỉ lưu giá trị băm PBKDF2-HMAC-SHA256 |
| Tên việc + mô tả khi **chia nhỏ việc** | Gửi tới Google Gemini — **chỉ** khi bản cài có khoá API |

Dòng cuối là đường **duy nhất** dữ liệu rời máy. Không có khoá thì
`MauProvider` sinh bước ngay trên máy và app không mở kết nối nào. Chi
tiết: [`BAO_MAT.md`](BAO_MAT.md) và chính sách quyền riêng tư trong app
(`res/raw/chinh_sach_rieng_tu.txt`).

Tên các lời nhắc, nhật ký và sổ thời lượng **không bao giờ** được gửi đi.
Đây là thứ rất dễ vô tình phá: thêm một lời gọi mạng “cho tiện” là đủ. Mã
hỏng kiểu đó không làm test nào đổ, không làm app sập — nó chỉ lặng lẽ
đưa dữ liệu cá nhân ra ngoài.

---

## 4. `meety/` — tóm tắt biên bản họp

Pipeline sáu pha từ transcript (`.vtt`, `.srt`, `.txt`, `.json`) hoặc
ghi âm, ra `StructuredMinutes` JSON. Chạy bằng dòng lệnh:
[`meety/HUONG_DAN_CHAY.md`](../meety/HUONG_DAN_CHAY.md).

Máy chủ web và giao diện web của Meety đã cắt: FlowyX hiện biên bản ngay
trong app, nên chỉ cần tệp JSON.

---

## 5. Kiểm thử

```bash
cd android && ./gradlew :app:testDebugUnitTest     # test Kotlin, cần JDK 17
cd meety && python -m pytest tests -q              # Meety
```

Android cần **JDK 17**: AGP 8.5.2 từ chối JDK 25 với một câu báo lỗi khó
hiểu (`What went wrong: 25.0.2`).

Cả hai chạy tự động trên CI mỗi lần đẩy code — xem
[`.github/workflows/build.yml`](../.github/workflows/build.yml). Job
Android còn **xuất APK tải về được** từ tab Actions.
