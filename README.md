# FlowyX

**Trợ thủ quản lý thời gian cho người ADHD**, app Android. Làm cho Hackathon
ADC RMIT 2026, chủ đề *Neurodivergence*.

FlowyX không dạy người dùng cách quản lý thời gian. ADHD là khó khăn về **thực thi**,
không phải thiếu kiến thức — nên FlowyX làm hộ những phần não đang khó làm: cảm nhận
thời gian trôi, nhớ mình đang làm gì sau khi bị cắt ngang, và bắt đầu một việc mơ hồ.

---

## Năm tab

| Tab | Làm gì |
|---|---|
| **Kế hoạch** | Việc cần làm, kéo thả để sắp xếp, ghim việc quan trọng |
| **Lịch** | Dải tuần + dòng thời gian kiểu khối màu: khối dài là việc lâu, có vạch "Bây giờ". Mở một kế hoạch để **chia nhỏ việc** |
| **Tập trung** | Đồng hồ vòng màu thu nhỏ dần thay cho con số; nút **Gỡ rối** khi bị kẹt, dẫn tới **chia nhỏ việc** |
| **Sức khỏe** | Nhật ký bằng chữ của người dùng, giấc ngủ và vận động (Health Connect, tuỳ chọn) |
| **Meety** | Biên bản họp: ghi tay, hoặc nhập tệp `_minutes.json` do [`meety/`](meety/) sinh ra |

## Nguyên tắc thiết kế

- **Không bao giờ phản hồi tiêu cực.** Việc chưa xong không bị tô đỏ, không có "tỉ lệ hoàn thành".
- **App không chủ động bắt chuyện.**
- **Một lần chạm.** Chọn giờ bằng đồng hồ, chọn thời lượng bằng chip; chỉ tên việc là phải gõ.
- **Dữ liệu ở lại trên máy.** Ngoại lệ duy nhất: chia nhỏ việc gửi tên việc tới Gemini khi bản cài có khoá API.
- **Sáng hoặc tối theo máy**, font Lexend (dễ đọc, đủ dấu tiếng Việt), tiếng Việt và tiếng Anh.

Chi tiết: [`docs/`](docs/README.md).

**Chia nhỏ việc (AI Task Demystifier):** tách một việc mơ hồ thành tối đa 5 bước cụ thể,
mỗi bước có số phút; người dùng sửa và duyệt trước khi bắt đầu. 3 lượt mỗi ngày.

---

## Cấu trúc repo

```
android/     app Android (Kotlin, không androidx, không Compose)
frontend/    module Android: đồng hồ vòng, trống cuộn chọn giờ, pháo hoa
meety/       pipeline Python tóm tắt biên bản họp -> _minutes.json cho tab Meety
docs/        kiến trúc, thiết kế, bảo mật, bản xem trước giao diện
research/    nghiên cứu ADC, đối chiếu sản phẩm đối thủ
thiet_ke/    logo và bộ nhận diện
```

## Chạy thử

**App Android** — cần **JDK 17** (AGP 8.5.2 từ chối JDK 25):

```bash
cd android
JAVA_HOME=/đường/dẫn/tới/jdk-17 ./gradlew :app:testDebugUnitTest :app:assembleDebug
```

APK ra ở `android/app/build/outputs/apk/debug/app-debug.apk`. Mỗi lần đẩy code, CI
cũng xuất APK tải về được từ tab **Actions**.

Muốn phần chia nhỏ việc gọi Gemini thật thì thêm `GEMINI_API_KEY=...` vào
`android/local.properties` (tệp này không lên GitHub). Không có khoá thì app dùng
bản mẫu chạy trên máy. Xem [`android/README.md`](android/README.md).

**Meety** — xem [`meety/HUONG_DAN_CHAY.md`](meety/HUONG_DAN_CHAY.md):

```bash
cd meety
pip install -r requirements.txt
python main.py --input sample_transcript.json --skip-stt --date 2026-07-22 --mock
```

---

## Giới hạn — nói thẳng

- **Chưa thử với người dùng ADHD thật.** Đây là giới hạn lớn nhất.
- Các hằng số (ngưỡng "bị kẹt", mốc nhắc) là giá trị tạm, **chưa hiệu chỉnh bằng số đo thực tế**.
- Bản iOS đã bỏ; repo chỉ còn Android.

> FlowyX là công cụ hỗ trợ tự quản lý, **không phải thiết bị y tế**: không chẩn đoán,
> không theo dõi triệu chứng, không đưa lời khuyên điều trị. Xem `docs/FLOWY_THIET_KE.md` §4.
