# Flowy cho iPhone và iPad

SwiftUI, **iOS 16 trở lên**. Một app chạy cả iPhone (một cột) và iPad (hai cột).

> ⚠️ **Chưa được biên dịch.** Mã được viết trên máy không có Xcode. Đã kiểm
> cú pháp toàn bộ 22 file và đối chiếu tên giữa các file, nhưng lỗi kiểu chỉ
> Xcode mới bắt được. **Cần một lần build trên Mac trước ngày thi** — gửi lỗi
> build vào [`BAO_LOI/`](../BAO_LOI/README.md) nếu có.

> **Trạng thái 17/09/2026:** đã theo giao diện **v4** — năm tab (Kế hoạch, Lịch,
> Tập trung, Nhật ký, Biên bản), bảng màu FlowyX sáng/tối khớp từng mã với
> Android, đồng hồ tập trung mặt 60 phút, vuốt để xoá/xong, xuất Word hai bản,
> nhập biên bản Meety. Chi tiết quyết định: `docs/GIAO_DIEN_V4.md`.
>
> ⚠️ **Vẫn chưa từng biên dịch.** Mã được viết trên máy không có Xcode. Đã kiểm
> cấu trúc bằng `python3 ios/tools_kiem_swift.py` (ngoặc cân, ký hiệu tồn tại,
> `@EnvironmentObject` đều được cấp), nhưng lỗi kiểu chỉ Xcode bắt được. Lần đầu
> mở trên Mac hãy ghi mọi lỗi build vào `BAO_LOI/`.

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
