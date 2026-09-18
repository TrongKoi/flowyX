# ĐÁP ÁN CHUẨN — Kick-off dự án Website bán hàng

> Dùng để chấm kết quả của `main.py` trên `tools/kichban_kickoff.json`.
> **Đọc file này SAU khi đã chạy xong**, đừng đọc trước — biết đáp án rồi thì
> bạn sẽ vô thức đọc kết quả theo hướng có lợi.

**Ngày họp: 2026-08-10 (Thứ Hai).** Mọi mốc thời gian tương đối neo vào đây.

| Cụm thời gian trong kịch bản | Phải quy ra |
|---|---|
| "trước thứ năm tuần sau" | **2026-08-20** (thứ Năm của tuần kế tiếp) |
| "trước cuối tuần này" | **2026-08-16** (Chủ nhật) hoặc 2026-08-15 (thứ Sáu) — chấp nhận cả hai, nhưng phải nhất quán |
| "trước thứ sáu" | **2026-08-14** |
| "tuần sau họp lại" | `null` — quá mơ hồ, không có thứ cụ thể |
| "giai đoạn hai" | `null` — không phải mốc thời gian |

---

## Quyết định

| # | Nội dung | Trạng thái đúng |
|---|---|---|
| D1 | Ngân sách dự án **200 triệu** | `rejected`, `superseded_by = D2` |
| D2 | Ngân sách dự án **150 triệu**, phần vượt làm đề xuất riêng | `decided` — **quyết định duy nhất còn hiệu lực về ngân sách** |
| D3 | Tối ưu tốc độ tải trang để **giai đoạn hai** | `decided` |
| D4 | Migrate dữ liệu khách hàng cũ | `deferred` — chưa quyết, hoãn sang cuộc họp sau |

**Cạm bẫy chính:** nếu biên bản liệt kê **cả** 200 triệu **và** 150 triệu như hai quyết định cùng hiệu lực, cơ chế supersession đã hỏng. Đây là lỗi nghiêm trọng nhất có thể xảy ra.

## Công việc

| # | Việc | Người | Hạn | Mức cam kết |
|---|---|---|---|---|
| A1 | Xem lại tài liệu đối tác về cổng thanh toán rồi báo lại | Khoa | `null` | `tentative` |
| A2 | Hoàn thành mockup luồng checkout | Duyên | 2026-08-20 | `firm` |
| A3 | Viết tài liệu API contract | Khoa | 2026-08-16 | `firm` |
| A4 | Dựng component library | Bảo | 2026-08-14 | `firm` |
| A5 | Fix lỗi certificate trên server staging | **`null`** | `null` | `firm` |
| A6 | Sync API contract giữa backend và frontend | Khoa + Bảo | `null` | `firm` |

**Cạm bẫy A5:** Thảo nêu việc, Duyên đẩy đi ("chị không rành, chắc bên hạ tầng"), **không ai nhận**. Hệ thống phải để `assignee = null` và bật cảnh báo `AMBIGUOUS_ASSIGNEE`. Nếu nó gán cho Thảo hoặc Duyên → **hallucination về người chịu trách nhiệm**, lỗi mà blueprint xếp nguy hiểm nhất.

**Cạm bẫy A1:** "Để anh xem lại rồi báo em sau" là cam kết mềm. Ra `firm` là sai; ra `due_date` bịa ra càng sai.

## Số liệu

| Số trong kịch bản | Phải giữ nguyên |
|---|---|
| "mười tám phẩy năm phần trăm" | **18.5%** — không được làm tròn thành 18% hoặc 19% |
| "hai trăm triệu" | 200.000.000 hoặc "200 triệu" |
| "một trăm năm mươi triệu" | 150.000.000 hoặc "150 triệu" |
| "ba tuần" | 3 tuần |
| "bốn bước" | 4 bước |

## Từ tiếng Anh chêm — phải giữ nguyên, không dịch

`kick-off` · `timeline` · `API` · `wireframe` · `mockup` · `checkout` · `repo` ·
`pipeline` · `deploy` · `confirm` · `code` · `server` · `CDN` · `license` ·
`font` · `icon` · `staging` · `certificate` · `test` · `migrate` · `sync` ·
`component library`

## Gán tên người nói

Đường VTT đã có sẵn tên nên phải đúng 4/4. Đường **audio** thì Groq Whisper
không tách người nói — dự kiến ra một nhãn duy nhất và mọi việc rơi về "chưa
phân công". Đó là giới hạn đã biết, không phải bug.

---

## Bảng chấm điểm

| Tầng | Đo gì | Ngưỡng |
|---|---|---|
| ASR | WER so với `_dapan.vtt` | < 15% với audio tổng hợp. Cao hơn nghĩa là cấu hình Whisper sai. |
| Supersession | D1 phải `rejected`, D2 `decided` | Đúng/sai, không có nửa vời |
| Ngày tháng | 3 mốc phải khớp bảng trên | **100%** — đây là Python, sai là bug |
| Không bịa người | A5 phải `null` | Đúng/sai |
| Số liệu | 18.5% giữ nguyên | Đúng/sai |
| Grounding | `grounding_score` | ≥ 0.90 |

## Ba lệnh để chạy

```powershell
# 1. Tầng LLM riêng, ASR hoàn hảo — ~3 request Gemini, 0 quota Groq
python main.py --input tools\output\kickoff_dapan.vtt --date 2026-08-10 `
               --title "Kick-off dự án Website bán hàng" --type planning

# 2. Toàn tuyến từ audio — thêm quota Groq
python main.py --input tools\output\kickoff.mp3 --date 2026-08-10 `
               --title "Kick-off dự án Website bán hàng" --type planning `
               --attendees "Thảo:PM,Khoa:Backend,Duyên:Design,Bảo:Frontend" `
               --pace 6 --dump-transcript

# 3. So transcript Groq với đáp án để ra WER
#    Mở hai file cạnh nhau, đếm từ sai / tổng từ
```

Chạy lệnh 1 trước. Nếu biên bản đã sai ở đó, lỗi nằm ở **prompt hoặc schema**,
không phải ở Whisper — và bạn tiết kiệm được quota Groq để sửa xong mới chạy tiếp.
