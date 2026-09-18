# Flowy

**Trợ thủ quản lý thời gian cho người ADHD** — bản dự thi Hackathon ADC RMIT 2026,
chủ đề *Neurodivergence*. Thi ngày 21–23/09/2026.

Flowy không dạy người dùng cách quản lý thời gian. ADHD là khó khăn về **thực thi**,
không phải thiếu kiến thức — nên Flowy làm hộ những phần não đang khó làm: cảm nhận
thời gian trôi, nhớ mình đang làm gì sau khi bị cắt ngang, và bắt đầu một việc mơ hồ.

Chạy trên **Android** (điện thoại, máy tính bảng) và **iOS** (iPhone, iPad).

---

## Ba khó khăn, và Flowy làm gì

**Mù thời gian.** Khó cảm nhận thời gian trôi, khó ước lượng một việc mất bao lâu.
- Vòng màu thu nhỏ dần thay cho con số trừu tượng; đổi màu khi sắp đến giờ, không nhấp nháy.
- Mọi câu nhắc neo vào giờ thật: *"Cần xong lúc 14 giờ. Bạn cần bắt tay vào lúc 13 giờ 34."*
- **Học từ chính người dùng:** ghi lại ước lượng và thời gian thật. Lần sau: *"Lần trước bạn ước 20 phút, thực tế 35 phút."*
- **Lịch kiểu khối màu:** khối dài hơn là việc lâu hơn, có vạch "Bây giờ" và khoảng trống giữa các việc — nhìn một cái thấy cả ngày.

**Mất mạch sau khi bị sao nhãng.** Rời app năm phút rồi quên đang làm gì.
- Quay lại app thì câu đầu tiên dựng lại ngữ cảnh: đang làm gì, còn mấy bước, bước trước mắt là gì.

**Tê liệt trước việc mơ hồ.**
- Ý định thực thi: hỏi đủ **việc gì / khi nào / ở đâu** trước khi bắt đầu.
- Chia việc thành bước nhỏ; mỗi bước xong có rung nhẹ và âm ngắn.
- Nút **Gợi ý** khi bị kẹt: hỏi *"Bước nhỏ nhất bạn làm được ngay bây giờ là gì?"*

**Kèm theo:**
- Lời nhắc hằng ngày do người dùng tự đặt tên.
- Nhật ký bằng chữ của người dùng — app không chấm điểm, không diễn giải.
- Kiểm tra quyền trong Cài đặt.

## Nguyên tắc thiết kế

- **Không bao giờ phản hồi tiêu cực.** Việc chưa xong không bị tô đỏ, không có "tỉ lệ hoàn thành".
- **App không chủ động bắt chuyện.** Chỉ đọc lên câu hỏi khi người dùng bấm Gợi ý.
- **Một lần chạm.** Chọn giờ bằng đồng hồ, chọn thời lượng bằng chip; chỉ tên việc là phải gõ.
- **Vị trí cố định.** Mỗi khối thông tin luôn ở đúng chỗ; không có dữ liệu thì hiện dấu gạch chứ không biến mất.
- **Dữ liệu ở lại trên máy.** Lịch, lời nhắc, nhật ký không bao giờ rời điện thoại.
- **Sáng hoặc tối theo máy**, tùy chọn font Lexend (dễ đọc, đủ dấu tiếng Việt), co giãn theo cỡ chữ hệ thống.

Chi tiết: [`docs/GIAO_DIEN_V4.md`](docs/GIAO_DIEN_V4.md) (giao diện hiện tại, 17/09) · [`docs/FLOWY_THIET_KE.md`](docs/FLOWY_THIET_KE.md)

---

## Tìm nhanh

| Muốn… | Mở |
|---|---|
| **Báo lỗi / xem lỗi đã sửa** | [`BAO_LOI/`](BAO_LOI/README.md) — có bảng "lỗi ở phần nào thì mở file nào" |
| Sửa app Android | [`android/`](android/README.md) |
| Sửa app iPhone / iPad | [`ios/`](ios/README.md) |
| Sửa quy tắc (khi nào hỏi gì, nhắc lúc nào) | [`adc_wayfinding/run_flowy.py`](adc_wayfinding/run_flowy.py), `adc_wayfinding/wayfinding/adhd/` |
| Đọc thiết kế và nghiên cứu | [`docs/`](docs/README.md), [`research/`](research/) |

```
BAO_LOI/          báo cáo test và kết quả sửa - MỞ ĐÂY TRƯỚC khi báo lỗi
android/          app Android (Kotlin, không androidx)
frontend/         module Android vẽ đồng hồ tròn
ios/              app iPhone / iPad (SwiftUI, iOS 16+)
adc_wayfinding/   lõi quyết định (Python) + 442 test
docs/             thiết kế, quyết định giao diện
research/         nghiên cứu, đối chiếu sản phẩm
meety/            biên bản cuộc họp - sẽ tích hợp sau
```

---

## Chạy thử

**Lõi và test** (không cần điện thoại):

```bash
cd adc_wayfinding
pip install pytest
python3 -m pytest tests -q          # 442 test
python3 run_flowy.py               # in ra địa chỉ cho điện thoại
```

**App:** cài bản Android ([`android/README.md`](android/README.md)) hoặc iOS
([`ios/README.md`](ios/README.md)), mở **Cài đặt**, nhập địa chỉ laptop vừa in ra.

> **Về laptop:** trong giai đoạn test và demo, phần quy tắc chạy trên laptop để sửa
> thuật toán và chạy lại test trong vài giây. Điện thoại và laptop cần chung WiFi.
> Lịch, lời nhắc và nhật ký chạy hoàn toàn trên máy, không cần laptop.

---

## Giới hạn hiện tại — nói thẳng

- **Chưa thử với người dùng ADHD thật.**
- **Bản iOS chưa được biên dịch** — viết trên máy không có Xcode, đã kiểm cú pháp. Cần một lần build trên Mac trước ngày thi.
- **Bản Android chưa build lại APK** sau giao diện v2 — đã type-check toàn bộ với Android API 34.
- Các hằng số (ngưỡng "bị kẹt", mốc nhắc) là giá trị tạm, chưa hiệu chỉnh bằng số đo thực tế.
- Phần quy tắc cần laptop khi test/demo (xem trên).

> Flowy là công cụ hỗ trợ tự quản lý, **không phải thiết bị y tế**: không chẩn đoán,
> không theo dõi triệu chứng, không đưa lời khuyên điều trị. Xem `docs/FLOWY_THIET_KE.md` §4.
