# Báo lỗi & kết quả sửa

Mọi báo cáo test nằm ở **đúng một chỗ**: thư mục này, ngay gốc repo.
Không cần tìm trong `docs/` hay các thư mục con.

## Thêm một báo cáo mới

1. Tạo thư mục `NAM-THANG-NGAY_ten-may/` (ví dụ `2026-09-20_iphone-13/`).
2. Copy [`MAU_BAO_LOI.md`](MAU_BAO_LOI.md) vào đó, hoặc bỏ file Word vào.
3. Thêm một dòng vào bảng dưới đây.

## Các đợt test

| Ngày | Máy | Báo cáo gốc | Kết quả sửa | Còn mở |
|---|---|---|---|---|
| 16/09/2026 | Galaxy Tab S7 FE (Android 14) | [bao-cao-goc.docx](2026-09-16_galaxy-tab-s7fe/bao-cao-goc.docx) | [ket-qua-sua.md](2026-09-16_galaxy-tab-s7fe/ket-qua-sua.md) | 0 — chờ test lại trên máy |

## Tìm nhanh: lỗi ở phần nào thì mở file nào

| Phần | Android | iOS | Laptop (Python) |
|---|---|---|---|
| Màn hình Hôm nay | `android/app/src/main/java/vn/adc2026/wayfinding/MainActivity.kt` | `ios/Flowy/ManHinh/ManHinhChinh.swift` | `adc_wayfinding/run_flowy.py` |
| Lịch, kế hoạch | `LichActivity.kt`, `KeHoachActivity.kt`, `Lich.kt` | `ManHinh/ManHinhLich.swift`, `ManHinh/SuaKeHoach.swift`, `So/Lich.swift` | — (không qua laptop) |
| Thông báo lịch | `LichBao.kt` | `HeThong/BaoLich.swift` | — |
| Lời nhắc hằng ngày | `BaoGio.kt`, `SoNhac.kt` | `HeThong/BaoGio.swift`, `So/SoNhac.swift` | `wayfinding/adhd/nhacviec.py` |
| Nhật ký | `SoNhatKy.kt` (hộp thoại trong `MainActivity.kt`) | `ManHinh/ManHinhSo.swift` | `wayfinding/adhd/nhatky.py` |
| Cài đặt, kiểm tra quyền | `CaiDatActivity.kt`, `KiemQuyen.kt` | `ManHinh/ManHinhCaiDat.swift`, `HeThong/KiemQuyen.swift` | — |
| Giọng đọc, rung | `Speaker.kt` | `HeThong/Speaker.swift` | `wayfinding/loi_chung/speech.py` |
| Nhận dạng giọng nói | `VoiceInput.kt` | `HeThong/VoiceInput.swift` | — |
| Kết nối laptop | `BridgeClient.kt`, `Payload.kt` | `LoiGiao/BridgeClient.swift`, `LoiGiao/Payload.swift` | `wayfinding/loi_chung/bridge.py` |
| Màu, font, giao diện | `res/values*/colors.xml`, `res/layout*/`, `GiaoDien.kt` | `HeThong/GiaoDien.swift` | — |
| Đồng hồ tròn | `frontend/src/main/java/vn/adc2026/frontend/TimerTronView.kt` | `ManHinh/ThanhPhan.swift` (`VongThoiGian`) | `wayfinding/adhd/timeblind.py` |

Đường dẫn Android bắt đầu từ `android/app/src/main/java/vn/adc2026/wayfinding/` nếu không ghi đầy đủ; iOS từ `ios/Flowy/`.
