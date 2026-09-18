# Giao diện v2 — hướng C (16/09/2026)

Sáng + tối theo máy, khối màu kiểu Tiimo, một nút chính. Android và iOS dùng
**cùng mã màu, cùng bố cục, cùng câu chữ**.

## Màu

| Tên | Sáng | Tối | Dùng cho |
|---|---|---|---|
| `nen` | `#F7F3EC` | `#121212` | nền màn hình |
| `the` | `#FFFDF8` | `#1E1E1E` | nền khối |
| `vien` | `#E6DFD3` | `#2C2C2C` | viền, vạch chia |
| `chu` | `#2B2A28` | `#E8E8E8` | chữ chính |
| `chu_phu` | `#625D55` | `#A8A39A` | chữ phụ |
| `nhan` | `#2F7F72` | `#6FC0B1` | nút chính, lựa chọn, vạch "Bây giờ" |
| `dh_con_nhieu` | `#4A78D0` | `#5B8DEF` | vòng thời gian: còn nhiều |
| `dh_sap_den` | `#B07512` | `#E0A030` | vòng thời gian: sắp đến giờ |
| `dh_di_ngay` | `#B9483A` | `#D4553F` | vòng thời gian: cần bắt tay ngay |
| `buoc_1…5` | 5 màu dịu | 5 màu trầm | khối bước, khối kế hoạch |

Tương phản đã đo: chữ/nền ≥ 12:1, chữ phụ ≥ 6:1, chữ trên nút chính 4,77:1,
vòng thời gian ≥ 3:1. **Không có đỏ tươi.** Màu khối bước không mang nghĩa.

Nguồn: `android/app/src/main/res/values(-night)/colors.xml`, `ios/Flowy/HeThong/GiaoDien.swift`.

## Chữ

Mặc định font hệ thống. Tùy chọn **Lexend** (Cài đặt → Giao diện).

Đề xuất ban đầu là Atkinson Hyperlegible, nhưng kiểm bằng fontTools thì cả bản
gốc lẫn bản Next đều **thiếu toàn bộ nguyên âm có dấu tiếng Việt**. Lexend đủ dấu,
giấy phép OFL. Hai bản tĩnh Regular / SemiBold tách từ bản biến thiên.

## Màn hình Hôm nay

```
Điện thoại                         Máy tính bảng (≥ 600 dp / iPad)
┌──────────────────────┐           ┌───────────────┬──────────────────────┐
│ Flowy       Cài đặt  │           │ THỜI GIAN     │ Việc đang làm        │
│ [Tiếp theo · 14:00]  │           │  (vòng to)    │ Câu hỏi + ô nhập     │
│ Việc đang làm        │           │               │ BƯỚC HIỆN TẠI        │
│ Câu hỏi + ô nhập     │           │ [Tiếp theo]   │  + Gợi ý             │
│ THỜI GIAN            │           │               │ [ Nút chính ]        │
│ BƯỚC HIỆN TẠI + Gợi ý│           │               │ Nhắc giờ: Ít Vừa Nhiều│
│ [    Nút chính    ]  │           └───────────────┴──────────────────────┘
│ Tạm dừng | Kết thúc  │
│ Nhắc giờ: Ít Vừa Nhiều│          Nút chính đổi nhãn theo lúc:
│ Lịch | Lời nhắc | Nhật ký        Bắt đầu → Xong bước → Xong việc; Tiếp tục khi tạm dừng
└──────────────────────┘
```

iOS dùng 4 tab: **Hôm nay · Lịch · Sổ · Cài đặt**.

## Lịch

- **Dải tuần** (iPad/tablet: dọc bên trái), chấm dưới ngày có kế hoạch.
- **Dòng thời gian:** mỗi kế hoạch một khối màu, **cao theo thời lượng**
  (64–220 dp), có emoji, giờ bắt đầu/kết thúc, nơi làm, lặp lại, các lần nhắc.
- **Vạch "Bây giờ"** trên ngày hôm nay, tự cuộn tới.
- **"Trống 45 phút"** giữa hai việc cách nhau ≥ 15 phút.
- Chạm một khối: **Bắt đầu việc này** · Đánh dấu đã xong · Sửa · Xoá.
- **Tạo/sửa:** chỉ tên là phải gõ. Emoji, màu, ngày, giờ, thời lượng (chip),
  lặp lại (không / hằng ngày / hằng tuần), nhắc (nhiều lựa chọn; mặc định
  15 phút trước + đúng giờ), nơi làm.
- **Bắt đầu việc này** điền sẵn: việc gì = tên, khi nào = "lúc 14:00",
  ở đâu = nơi làm, giờ hẹn = giờ kết thúc, ước lượng = thời lượng.
- Việc đã xong mờ đi và có dấu ✓. Việc chưa xong **không** bị đánh dấu gì.

## Đã bỏ

- **Nhân vật đồng hành** (16/09). Nút **Gợi ý** thay vai trò "chạm vào nhân vật".
