# Meety — Hệ thống Tóm tắt Cuộc họp

Pipeline 6 pha xử lý từ audio hoặc transcript ra `StructuredMinutes` JSON,
kèm giao diện web và máy chủ. Chạy hoàn toàn trên free tier: **0 VNĐ**.

> **Muốn chạy ngay?** Xem [`HUONG_DAN_CHAY.md`](HUONG_DAN_CHAY.md) — hướng dẫn
> từng bước từ máy trắng, có cả phần xử lý khi hỏng.
>
> Ba cách chạy: nháy đúp `mm-ai-preview.html` (xem giao diện, không cần cài gì)
> · `python main.py` (dòng lệnh) · `python run_server.py` (máy chủ web đầy đủ:
> đăng nhập, 2FA, tải cuộc họp lên).

## Chạy thử ngay (không cần API key)

```bash
pip install pydantic pytest
python main.py --input tests/fixtures/ingest/zoom_sprint23.vtt \
               --date 2026-07-22 --mock
python -m pytest tests/ -q          # 311 test
```

## Xuất Word hai bản (dùng cho FlowyX)

```bash
python xuat_word.py output/<id>_minutes.json
#  -> <id>_bien_ban.docx          bản tiêu chuẩn (NĐ 30/2020)
#  -> <id>_bien_ban_de_doc.docx   bản dễ đọc cho người khó đọc / ADHD
```

Chỉ dùng thư viện chuẩn. Quy chuẩn bản dễ đọc: đầu tệp `exporters/docx_de_doc.py`.
Tệp `_minutes.json` cũng mở được thẳng trong tab Biên bản của app FlowyX.

## ⭐ Đường vào rẻ nhất: transcript từ Zoom / Meet / Teams

Nút thắt tài nguyên của cả dự án là **8 giờ audio/ngày từ Groq**. Nhưng
Zoom, Google Meet và Microsoft Teams đều cho tải transcript về **miễn phí,
không giới hạn, kèm sẵn tên người nói**.

Đường này vừa bỏ qua hoàn toàn nút thắt Groq, vừa cho kết quả tách người nói
**tốt hơn** đường audio: Groq Whisper không làm diarization, nên một file
audio đi vào sẽ ra transcript chỉ có một nhãn speaker — và khi đó mọi công
việc trong biên bản đều rơi về "chưa phân công".

```bash
# Zoom: Recordings -> Audio Transcript -> tải file .vtt
python main.py --input GMT20260722-140000_Recording.vtt --date 2026-07-22

# Dán transcript từ chỗ khác vào một file .txt cũng chạy được
python main.py --input bien_ban_tho.txt --date 2026-07-22
```

Pha INGEST nhận `.vtt`, `.srt`, `.txt`, `.md` và `.json`, nhận dạng theo
**nội dung** chứ không theo đuôi file, rồi chạy một cổng tiền kiểm chất
lượng trước khi tiêu bất kỳ quota nào.

## Kiến trúc

```
.vtt / .srt / .txt ─┐
                    ├─▶ s0 INGEST     0 request  ─┐ chuẩn hoá + tiền kiểm
audio ─[Groq Whisper]┘                            │
                                                  │
   s2 DIARIZE      0 request  ────────────────────┤  gán tên qua xưng hô
   s3 CHUNK        0 request  ────────────────────┤  chia chunk theo quota
   s4 EXTRACT      1-N request Gemini ────────────┤  sự kiện thô + evidence
   s5 RECONCILE    1 request Gemini  ─────────────┤  supersession, ngày, tên
   s6 COMPOSE      1 request Gemini  ─────────────┤  CHỈ văn xuôi
   s7 VALIDATE     0 request (Python) ────────────┘  8 lớp grounding
                                       TỔNG: 3 request/cuộc họp mẫu
```

## Cấu trúc

| Thư mục | Vai trò |
|---|---|
| `schemas/` | Hợp đồng dữ liệu Pydantic (nguồn sự thật duy nhất) |
| `nlp/` | Logic Python thuần, 0 quota, test offline 100% |
| `core/` | SQLite: cache theo băm + sổ cái quota bền vững |
| `providers/` | Adapter — biên giới duy nhất chạm mạng |
| `pipeline/` | Sáu pha: s0 ingest, s2 diarize, s3 chunk, s4–s7 |
| `exporters/` | Kết xuất biên bản (hiện có Markdown) |

## Ba bất biến của thiết kế

1. **COMPOSE không nhìn thấy transcript.** Chỉ nhận JSON đã hoà giải, và
   schema đầu ra chỉ có `tldr`/`paragraphs`/`chapters`. Model không có
   nguyên liệu để bịa và cũng không có chỗ để ghi. Có test khoá lại.
2. **Ngày tháng do Python quy đổi, không hỏi LLM.** LLM tính sai âm thầm;
   `datetime` thì không.
3. **Pha VALIDATE tốn 0 quota.** Miễn phí, tất định, chạy vô hạn lần.

Pha INGEST cũng tuân theo bất biến thứ ba: 100% Python, 0 request, có test
khoá lại.

## Chi phí quota

| Nguồn | Hạn mức/ngày | 1 cuộc họp 60 phút | Số cuộc họp/ngày |
|---|---|---|---|
| Groq audio-seconds | 28.800s | 3.600s | **8** ← nút thắt |
| Gemini RPD | ~250–1.500 | 4–6 request | 40–250 |

Lần chạy lại tốn **0 request** nhờ cache theo băm nội dung.

## Lệnh hữu ích

```bash
python main.py --quota-status                    # xem quota còn lại
python main.py --input zoom.vtt --date 2026-07-22 --dump-transcript  # xuất bản đã chuẩn hoá để sửa tay
python main.py --input zoom.vtt --date 2026-07-22 --merge-gap 0      # giữ nguyên từng cue của Zoom
python main.py --input x.json --skip-stt --dry-run   # ước tính, không gọi API
python main.py --input meeting.m4a --date 2026-07-22 # từ audio (cần 2 API key)
python main.py --input x.json --skip-stt --pace 6    # giãn 6s/request, né RPM
```

## Gán tên người nói

`nlp/vocative.py` khai thác đặc thù tiếng Việt: người Việt gọi tên nhau liên
tục trong cuộc họp. Mỗi câu "Anh Tuấn cập nhật giúp em" là một phiếu bầu danh
tính cho người nói ở lượt kế tiếp. Hoàn toàn Python thuần, 0 quota.

```bash
python main.py --input meeting.json --skip-stt --date 2026-07-22 \
               --attendees "Hùng:PM,Tuấn:Backend,Lan:QA,Minh:Mobile"
```

Biết trước danh sách tham dự cho độ chính xác cao hơn hẳn (4/4 so với 2/4
trên cuộc họp mẫu), vì không gian tên bị giới hạn nên có thể hạ ngưỡng chấp
nhận bằng chứng.

## Cổng tiền kiểm đầu vào

Chạy trước khi tiêu quota, chặn file rác thay vì đốt 3 request Gemini rồi
mới phát hiện biên bản rỗng. Tám loại cảnh báo:

| Mã | Mức | Ý nghĩa |
|---|---|---|
| `SINGLE_SPEAKER` | cao | Chỉ một người nói — không quy được cam kết về ai |
| `TOO_FEW_SEGMENTS` | cao | Nhiều khả năng đọc sai định dạng |
| `LOW_TEXT_VOLUME` | cao | Quá ít nội dung để trích xuất |
| `UNATTRIBUTED_SPEECH` | vừa | Có đoạn không rõ ai nói, đã tách riêng nhãn |
| `NO_SPEAKER_NAMES` | vừa | Nguồn không kèm tên, phải đoán qua xưng hô |
| `MEETING_TOO_SHORT` | vừa | File có thể bị cắt |
| `TIMESTAMPS_OUT_OF_ORDER` | vừa | Quy tắc supersession có thể sai |
| `LONG_SILENCE_GAPS` | thấp | Ghi âm đứt quãng |
| `SYNTHETIC_TIMESTAMPS` | thấp | Mốc thời gian suy ra, không dùng để tua audio |
| `DUPLICATE_SOURCE` | thấp | Nội dung này đã nạp trước đó |

Cảnh báo mức **cao** làm dừng pipeline. Thêm `--force` để chạy tiếp.

## Chưa có trong bản này

- **Diarization âm học** (`pyannote`): hiện chỉ suy ra danh tính từ xưng hô.
  Nếu nguồn ASR không tách được lượt nói (Groq Whisper), toàn bộ transcript
  mang một nhãn duy nhất và xưng hô không đủ để chia lượt. **Cách né hiệu
  quả nhất hiện nay là dùng transcript `.vtt` thay cho audio.**
- **Adapter Ollama** cho `--offline`.
- **Exporter DOCX** (đã có Markdown và JSON).

## Lưu ý quyền riêng tư

Free tier Gemini AI Studio có thể dùng prompt để cải thiện sản phẩm. Dùng
dữ liệu mẫu để demo; với nội dung họp thật cần bật redaction hoặc chờ
adapter offline.
