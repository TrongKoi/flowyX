# Kiểm thử Meety

```powershell
python -m pytest tests/ -q          # 498 phép kiểm, không gọi mạng, không cần API key
```

## Bộ nào làm gì

| Bộ | Số | Soi vào |
|---|---|---|
| `unit/test_vn_dates.py` | 131 | Quy đổi cụm ngày tiếng Việt (“thứ Sáu tuần sau”) ra ngày thật |
| `unit/test_ingest.py` | 79 | Đọc `.vtt` / `.srt` / `.txt` / `.json` / `.docx`, tách người nói, cổng tiền kiểm |
| `unit/test_env.py` | 39 | Đọc tệp `.env`: dấu ngoặc, dấu `=`, giá trị đặc biệt |
| `unit/test_vocative.py` | 36 | Gán tên người nói qua cách xưng hô |
| `unit/test_markdown_export.py` | 28 | Xuất biên bản Markdown |
| `unit/test_logging.py` | 23 | Che API key trong log |
| `unit/test_chunk.py` | 22 | Chia transcript theo hạn mức |
| `unit/test_orchestrator.py` | 19 | Điều phối sáu pha, ghi artifact để chạy lại được |
| `unit/test_pacific_time.py` | 19 | Tính mốc reset quota theo giờ Thái Bình Dương khi thiếu tz database |
| `integration/test_pipeline_e2e.py` | 25 | Chạy trọn pipeline bằng mô hình giả lập |
| `integration/test_ingest_e2e.py` | 5 | Chạy pha ingest trên các tệp mẫu |
| `test_ai_layer.py` | 40 | Tầng `ai/`: agent chống bịa, ẩn danh PII, đối soát hai mô hình |
| `test_evaluator.py` | 20 | Meeting-Bench: bốn thước đo, xếp hạng mô hình |
| `test_docx_de_doc.py` | 12 | Xuất Word bản dễ đọc |

## Một bài phụ thuộc máy

`test_pacific_time.py::…::test_quota_ledger_runs_without_system_tz_database`
giả lập Windows không có cơ sở dữ liệu múi giờ bằng cách xoá `TZPATH`. Trên
máy đã `pip install tzdata`, `zoneinfo` vẫn tìm được múi giờ trong gói đó
nên bài này đỏ — lỗi của cách giả lập, không phải của `core/quota.py`.

## Những lỗi các bộ này đã bắt được

| Lỗi | Bắt bởi | Mức |
|---|---|---|
| **Biên bản RỖNG được 0.45 điểm** — thước đo phụ trả recall 1.0 khi không có gì để chấm, nên “không làm gì” hơn “làm sai” | `test_evaluator` | nghiêm trọng |
| **Tên người nói lộ nguyên trong tệp huấn luyện** — chỉ ẩn danh nội dung câu, quên nhãn đầu dòng | `test_ai_layer` | nghiêm trọng |
| `requirements.txt` chứa tiếng Việt có dấu — pip trên Windows đọc bằng cp1252 và chết trước khi cài gì | `doctor.py` | trung bình |

Máy chủ web và giao diện web của Meety đã cắt (FlowyX hiện biên bản ngay
trong app), cùng với các bộ kiểm thử của chúng. Xem lịch sử git nếu cần.
