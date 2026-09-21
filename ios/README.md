# Flowy cho iPhone và iPad

SwiftUI, **iOS 16 trở lên**. Một app chạy cả iPhone (một cột) và iPad (hai cột).

> ✅ **Đã biên dịch sạch — 21/09/2026.** Toàn bộ 47 file Swift qua được
> trình biên dịch lần đầu tiên, trên CI (`macos-latest`, Xcode 26). Xem
> [`.github/workflows/build.yml`](../.github/workflows/build.yml).
>
> Hai lỗi thật đã lộ ra và đã sửa trong lần chạy đầu:
>
> 1. `FlowyModel.guiLenh` **không hề tồn tại** — bảy chỗ gọi nó, không chỗ
>    nào định nghĩa. `tools_kiem_swift.py` chỉ đếm ngoặc và đối chiếu tên
>    *trong từng file*, nên một ký hiệu thiếu hẳn như thế nó không thấy.
> 2. `ManHinhBienBan` dùng `nhieuDong ? 3... : 1...1` — `PartialRangeFrom`
>    và `ClosedRange` là hai kiểu khác nhau.

> ⚠️ **Nhưng vẫn chưa từng chạy trên máy thật.** Biên dịch được không có
> nghĩa là cài được: ký và nạp app lên iPhone bắt buộc phải có Xcode trên
> macOS. Nhóm hiện không có máy Mac. CI chỉ build cho **Simulator** —
> không cần chứng chỉ ký, và bắt đủ mọi lỗi kiểu, nhưng không bắt được
> lỗi lúc ký.

## Mở và chạy

1. Cần **Xcode 16** trở lên (project dùng thư mục đồng bộ — thêm file `.swift`
   vào `Flowy/` là tự vào target, không phải kéo vào Xcode).
2. Mở `ios/Flowy.xcodeproj`.
3. Chọn target **Flowy** → *Signing & Capabilities* → chọn **Team** (Apple ID
   cá nhân miễn phí là đủ để cài lên máy của mình).
4. Cắm iPhone/iPad, chọn máy, bấm Run.
5. Trong app: tab **Cài đặt** → nhập địa chỉ mà `run_flowy.py` in ra.

Nếu Xcode không mở được project: `brew install xcodegen && cd ios && xcodegen generate`
(dùng `project.yml`).

## Cấu trúc

```
Flowy/
  FlowyApp.swift        điểm vào, 4 tab, hiện thông báo khi app đang mở
  ManHinh/              các màn hình
    ManHinhChinh.swift    Hôm nay (thời gian, bước, nút chính, thẻ Tiếp theo)
    ManHinhLich.swift     Lịch: dải tuần + dòng thời gian khối màu
    SuaKeHoach.swift      tạo / sửa kế hoạch
    ManHinhSo.swift       Lời nhắc + Nhật ký
    ManHinhCaiDat.swift   laptop, giao diện, giọng đọc, kiểm tra quyền
    ThanhPhan.swift       vòng thời gian, chip, khối màu
  LoiGiao/              nối với laptop: Payload, BridgeClient, FlowyModel
  So/                   dữ liệu trên máy: Lich, SoNhac, SoNhatKy, SoThoiLuong
  HeThong/              màu/font, giọng đọc, nhận dạng, thông báo, quyền
  Fonts/                Lexend (OFL)
Flowy-Info.plist        mạng LAN, font - phần không đặt được bằng build setting
```

Mỗi file Swift có bản Kotlin cùng tên hoặc cùng vai trò trong `android/`. Sửa
quy tắc hay câu chữ ở một bên thì sửa cả bên kia.

## Khác Android

| | Android | iOS |
|---|---|---|
| Lời nhắc, lịch | AlarmManager + quyền báo thức chính xác | Thông báo lịch của hệ thống, chỉ cần quyền thông báo |
| Giọng tiếng Việt | Có thể thiếu → mở trang cài | Thường có sẵn; thiếu thì Cài đặt → Trợ năng → Nội dung được đọc |
| Điều hướng | Màn hình chính + nút Lịch/Lời nhắc/Nhật ký | 4 tab |
| Xuất nhật ký | Trình chọn tệp | Bảng chia sẻ (Lưu vào Tệp, AirDrop…) |
| Giới hạn | 48 chuông lịch | 64 thông báo chờ: 32 lời nhắc + 30 lịch |
