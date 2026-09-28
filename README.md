# FlowyX

**Trợ thủ thực thi cho người ADHD đang đi làm.** App Android, làm cho Hackathon
Accessibility Design Competition (ADC) RMIT 2026, chủ đề *Neurodivergence*.

---

## Vì sao có FlowyX

Người lớn ADHD thường **biết** phải làm gì — cái khó là **làm được**. Tài liệu
CBT cho ADHD gọi đó là vấn đề *thực thi*, không phải vấn đề *kiến thức*.

Phần lớn app ADHD lại đi đúng hướng ngược: dạy thêm, nhắc thêm. Bằng chứng nhóm
đã đối chiếu cho thấy hướng đó không đủ:

- Một tổng quan năm 2025 sàng lọc **829 app ADHD, chỉ 17 app đạt tiêu chí** —
  và phần lớn chủ yếu làm giáo dục tâm lý.
- Một thử nghiệm ngẫu nhiên **73 người lớn ADHD trong 3 tháng**: app nhắc nhở
  không cải thiện có ý nghĩa kết quả. *Nhắc đơn thuần chưa đủ.*
- Nghiên cứu 2026 phỏng vấn người lớn ADHD: công cụ năng suất hiện có mặc định
  người dùng **tự điều hoà ổn định** và **cảm nhận thời gian tuyến tính** — hai
  thứ người ADHD không có sẵn.

Ở nơi làm việc, những khó khăn này thành rào cản cụ thể: một đầu việc mơ hồ sếp
giao không biết bắt đầu từ đâu, một cuộc họp dài không nhớ mình đã nhận việc gì,
một hạn chót đến lúc nào không hay.

Nên FlowyX **không dạy và không chỉ nhắc**. Mỗi tính năng can thiệp vào đúng
khoảnh khắc người dùng đang kẹt.

Nguồn và lập luận đầy đủ: [`docs/FLOWY_THIET_KE.md`](docs/FLOWY_THIET_KE.md) §2.

---

## FlowyX làm gì

| Khó khăn | Trong app |
|---|---|
| **Tê liệt trước việc mơ hồ** — biết phải làm nhưng không bắt đầu được | **Gỡ rối**: vài câu hỏi ngắn — việc gì, đang thấy thế nào, *bước nhỏ nhất làm được trong 2 phút*, thử bao lâu — rồi hẹn giờ luôn. **Chia nhỏ việc bằng AI**: tách một việc thành tối đa 5 bước cụ thể có số phút; bước nào mở đầu bằng động từ mơ hồ (“nghiên cứu”, “chuẩn bị”) được đánh dấu để sửa. Người dùng sửa và duyệt trước khi bắt đầu |
| **Mù thời gian** — khó cảm nhận thời gian trôi | Đồng hồ **vòng màu thu nhỏ dần** thay cho con số, đổi màu theo từng chặng, không nhấp nháy. **Lịch khối màu**: khối dài là việc lâu, có vạch “Bây giờ”. Lời nhắc trước giờ, có giờ yên lặng |
| **Quá tải thông tin ở nơi làm việc** — họp xong không nhớ đã nhận gì | **Meety**: từ transcript Zoom / Meet / Teams ra biên bản có cấu trúc; việc được giao **đưa vào lịch** chỉ bằng chọn ngày giờ, tên việc đã điền sẵn; xuất Word hai bản, trong đó một bản **dễ đọc** (chữ rộng, giãn dòng, câu ngắn) |
| **Tự đánh giá tiêu cực** | Nhật ký bằng chữ của chính người dùng — app không chấm điểm, không diễn giải. Chuỗi ngày tính cả ngày chỉ mở app. Liên kết giấc ngủ và vận động qua Health Connect (tuỳ chọn) |

Năm tab: **Kế hoạch · Lịch · Tập trung · Sức khỏe · Meety.** Không thêm tab nào
nữa — với người ADHD, mỗi tab thêm là một chỗ nữa để lạc.

## Nguyên tắc không đổi

- **Không bao giờ phản hồi tiêu cực.** Việc chưa xong không bị tô đỏ, không có “tỉ lệ hoàn thành”.
- **AI đề xuất, người dùng quyết.** AI không tự thêm việc, không áp cách chia việc; hết lượt hay mất mạng thì vẫn có đường tự chia.
- **Một lần chạm.** Chọn giờ bằng trống cuộn, thời lượng bằng chip; chỉ tên việc là phải gõ.
- **Dữ liệu ở lại trên máy.** Nhật ký và sức khoẻ mã hoá AES-256-GCM, khoá trong Android Keystore. Đường duy nhất ra mạng: chia nhỏ việc gửi *tên việc và mô tả* tới Gemini, và chỉ khi bản cài có khoá API.
- **Dễ đọc.** Font Lexend, sáng/tối, cỡ chữ chỉnh được, tiếng Việt và tiếng Anh.
- **Không phải thiết bị y tế.** Không chẩn đoán, không theo dõi triệu chứng, không lời khuyên điều trị — [`docs/FLOWY_THIET_KE.md`](docs/FLOWY_THIET_KE.md) §4.

---

## Hiện trạng — 28/09/2026

Cuộc thi đã kết thúc; repo đã dọn, chỉ còn FlowyX.

**Chạy được:** cả năm tab, chia nhỏ việc bằng AI (có bản mẫu chạy không cần
mạng), lời nhắc, nhập lịch `.ics`, tài khoản lưu trên máy, hướng dẫn lần đầu, xuất
dữ liệu. 175 test Kotlin và gần 500 test Meety chạy tự động trên CI; mỗi lần đẩy
code CI xuất một APK tải về được.

**Chưa có — nói thẳng:**

- **Chưa thử với người dùng ADHD thật.** Giới hạn lớn nhất.
- **App chưa học từ người dùng.** App đã ghi thời gian thật của từng phiên tập
  trung, nhưng chưa màn nào hiện câu so sánh *“Lần trước bạn ước 20 phút, thực tế
  35 phút”* — mà theo thiết kế, chính câu đó mới là can thiệp.
- **Chưa có khôi phục mạch** (dựng lại ngữ cảnh khi quay lại sau gián đoạn). Bản
  cũ có trong màn “Phiên có laptop”, đã gỡ cùng màn đó.
- Các ngưỡng (bao lâu thì coi là kẹt, mốc nhắc) là giá trị tạm, **chưa hiệu chỉnh
  bằng số đo thực tế**.
- Chỉ có Android; bản iOS đã bỏ.

---

## Repo

```
android/     app Android — Kotlin trên Activity của nền tảng, không AndroidX, không Compose
frontend/    module Android: đồng hồ vòng, trống cuộn chọn giờ, pháo hoa
meety/       công cụ Python: bản ghi họp -> _minutes.json cho tab Meety
docs/        kiến trúc, thiết kế, bảo mật, bản xem trước giao diện
thiet_ke/    logo và bộ nhận diện
```

**Build app** — cần JDK 17:

```bash
cd android
./gradlew :app:testDebugUnitTest :app:assembleDebug
```

Không muốn build: tải APK `flowyx-debug-apk` ở tab **Actions**. Chi tiết, kể cả
cách gắn khoá Gemini: [`android/README.md`](android/README.md).

**Chạy Meety:** [`meety/HUONG_DAN_CHAY.md`](meety/HUONG_DAN_CHAY.md).

**Đọc tiếp:** [`docs/KIEN_TRUC.md`](docs/KIEN_TRUC.md) — hệ thống gồm gì, dữ liệu
đi đâu. Mục lục tài liệu: [`docs/README.md`](docs/README.md).
