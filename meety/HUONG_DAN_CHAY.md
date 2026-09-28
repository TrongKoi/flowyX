# HƯỚNG DẪN CHẠY MEETY

Meety biến bản ghi một cuộc họp (transcript hoặc ghi âm) thành biên bản có
cấu trúc. Kết quả là tệp `_minutes.json` để mở trong **tab Meety của app
FlowyX**, kèm bản Markdown và hai bản Word.

Từ máy trắng đến chạy được: khoảng 10 phút. Chạy bằng dòng lệnh trên máy
tính; không có máy chủ nào phải bật.

---

## 1. Cài Python

Cần **Python 3.10 trở lên**. Kiểm tra:

```powershell
python --version
```

Nếu báo lỗi hoặc thấp hơn 3.10, tải ở https://www.python.org/downloads/ —
lúc cài **nhớ tích ô “Add Python to PATH”**, thiếu ô này là nguồn gốc của
phần lớn rắc rối về sau.

## 2. Tạo môi trường ảo

Môi trường ảo giữ thư viện của dự án nằm riêng, không lẫn với Python của máy.

```powershell
cd meety
python -m venv .venv
```

Kích hoạt:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

Thành công thì đầu dòng lệnh có `(.venv)`. Nếu PowerShell báo
*“không thể tải vì việc chạy tập lệnh bị vô hiệu hoá”*, chạy một lần:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 3. Cài thư viện

```powershell
pip install -r requirements.txt
```

## 4. Đặt API key (bỏ qua nếu chỉ chạy thử với `--mock`)

Tạo tệp `.env` trong thư mục `meety/`:

```
GEMINI_API_KEY=...
GROQ_API_KEY=...
```

`.env` đã nằm trong `.gitignore` — **không bao giờ** đưa nó lên GitHub.

Lấy khoá **miễn phí, không cần thẻ tín dụng**:

- Gemini — https://aistudio.google.com/apikey
- Groq — https://console.groq.com/keys (chỉ cần nếu nạp file **âm thanh**;
  nạp `.vtt` từ Zoom/Meet/Teams thì không cần)

Kiểm tra máy đã sẵn sàng chưa:

```powershell
python doctor.py
```

## 5. Chạy

Chạy **không tốn quota, không cần key**, trên transcript mẫu:

```powershell
python main.py --input sample_transcript.json --skip-stt --date 2026-07-22 --mock
```

Chạy thật với transcript Zoom tải về:

```powershell
python main.py --input "GMT20260722-Recording.vtt" --date 2026-07-22 --title "Sprint 23 Review"
```

Chạy từ file ghi âm (cần cả hai key):

```powershell
python main.py --input hop.m4a --date 2026-07-22 --title "Sprint 23 Review" --type planning
```

Xem quota còn lại trước khi chạy:

```powershell
python main.py --quota-status
```

Các lệnh khác: [`README.md`](README.md) mục “Lệnh hữu ích”.

## 6. Lấy kết quả

Biên bản nằm ở `data/exports/`:

```
data/exports/<mã cuộc họp>_minutes.json   ← mở trong tab Meety của FlowyX
data/exports/<mã cuộc họp>_minutes.md
```

Xuất thêm hai bản Word:

```powershell
python xuat_word.py data/exports/<mã cuộc họp>_minutes.json
#  -> <mã>_bien_ban.docx          bản tiêu chuẩn (NĐ 30/2020)
#  -> <mã>_bien_ban_de_doc.docx   bản dễ đọc cho người khó đọc / ADHD
```

Kết quả từng pha (để chạy lại không tốn quota) nằm ở `data/artifacts/`.
Cả thư mục `data/` đã nằm trong `.gitignore`.

---

## KIỂM THỬ

```powershell
python -m pytest tests/ -q
```

Chi tiết từng bộ và các lỗi chúng đã bắt được: [`tests/README.md`](tests/README.md).

---

## HỎNG THÌ XEM ĐÂY

**`python` không được nhận là lệnh**
Lúc cài Python chưa tích “Add Python to PATH”. Cài lại và tích ô đó, hoặc
dùng `py` thay cho `python` trên Windows.

**`ModuleNotFoundError`**
Chưa kích hoạt `.venv`, hoặc chưa `pip install -r requirements.txt`. Đầu dòng
lệnh phải có `(.venv)`. Vẫn lỗi thì chạy `python doctor.py` — nó chỉ ra tệp
nào nằm sai chỗ.

**`pip install -r requirements.txt` báo lỗi `charmap codec can't decode`**
`requirements.txt` phải là ASCII thuần: trên Windows pip đọc file này bằng mã
trang hệ điều hành (cp1252) chứ không phải UTF-8. Kiểm bằng `python doctor.py`.

**`doctor.py` báo `ZoneInfoNotFoundError: America/Los_Angeles`**
**Không phải lỗi.** Windows không kèm cơ sở dữ liệu múi giờ IANA, nhưng
`core/quota.py` có sẵn bộ tính giờ Thái Bình Dương tự lập nên hạn mức vẫn đếm
đúng. Muốn hết dòng cảnh báo thì `pip install tzdata`.

**Lỗi ở pha nhận dạng giọng nói**
Thiếu `GROQ_API_KEY`. Không có key này thì chỉ nạp được `.vtt`, `.srt`,
`.txt`, `.json`.

**Pipeline dừng với cảnh báo mức cao** (`SINGLE_SPEAKER`, `TOO_FEW_SEGMENTS`…)
Cổng tiền kiểm chặn file trông như rác trước khi tốn quota. Xem bảng mã ở
[`README.md`](README.md); chắc chắn file đúng thì thêm `--force`.

**Muốn xoá sạch làm lại**
Xoá thư mục `data/`. Quota và cache cũng nằm trong đó nên xoá là mất lịch sử
đếm quota.

---

## CẤU TRÚC THƯ MỤC

```
main.py                 CLI xử lý một cuộc họp
xuat_word.py            Xuất hai bản Word từ _minutes.json
doctor.py               Kiểm tra môi trường
sample_transcript.json  Transcript mẫu để chạy thử

pipeline/               Sáu pha: s0 ingest … s7 validate, orchestrator
providers/              Gemini, Groq Whisper, bản giả lập
schemas/                Kiểu dữ liệu pydantic dùng chung
core/                   env, db, cache, quota, logging
nlp/                    Ngày tháng tiếng Việt, xưng hô
exporters/              Markdown, Word (viết thẳng OOXML, không thêm phụ thuộc)
ai/                     Tầng AI thử nghiệm — xem ai/README.md
tools/                  Sinh ghi âm thử từ kịch bản (make_test_audio.py) + đáp án
tests/                  Xem tests/README.md
```
