# Meety Intelligence — kiến trúc tầng AI

Bốn lớp, mỗi lớp giải một bài toán khác nhau. Đọc theo thứ tự này.

> **Ghi chú 28/09/2026.** Tầng này từng được gọi qua máy chủ web của Meety
> (các đường `GET/POST /api/...` nhắc bên dưới). Máy chủ đó đã cắt khỏi
> repo, nên hiện `ai/` là thư viện thử nghiệm: có đủ mã và
> `tests/test_ai_layer.py`, nhưng `main.py` không gọi tới. Chạy trực tiếp
> được một thứ: `python -m ai.meeting_evaluator <tệp .jsonl>` (Meeting-Bench).

```
  providers/            ①  Nói chuyện với mô hình nào cũng được
    base.py                 Giao diện chung: generate_json(prompt, schema)
    llm/gemini.py           API — nhanh, tốt, có hạn mức
    llm/local.py            Ollama / vLLM — chậm hơn, không hạn mức, không rời máy
    llm/mock.py             Fixture đóng hộp cho kiểm thử

  ai/agent.py           ②  Biết hỏi gì và kiểm lại câu trả lời
  ai/collector.py       ③  Biến việc dùng sản phẩm thành dữ liệu huấn luyện
  ai/consensus.py       ④  Đo xem mô hình cục bộ đã theo kịp API chưa
```

---

## ① Provider Abstraction Layer

`LLMProvider` chỉ đòi đúng một phương thức:

```python
generate_json(prompt, schema: type[BaseModel], *, system, temperature) -> LLMResponse
```

**Vì sao là `generate_json` chứ không phải `generate_text`.** Một giao diện trả
chuỗi sẽ đẩy việc phân tích JSON lên từng chỗ gọi, và mỗi chỗ sẽ tự chế một
cách xử lý lỗi khác nhau. Ép cấu trúc ngay ở biên giới nghĩa là mọi tầng trên
chỉ phải xử lý một loại thất bại: "không dựng được đối tượng".

Cả ba bản cài đặt đều ép định dạng **ở tầng giải mã**, không phải bằng cách xin
xỏ trong prompt:

| Provider | Cách ép |
|---|---|
| Gemini | `response_schema` trong `generationConfig` |
| Ollama | trường `format` nhận thẳng JSON Schema (từ 0.5.0) |
| vLLM / OpenAI | `response_format: {type: "json_schema", strict: true}` |

Endpoint nào không hỗ trợ `json_schema` thì `local.py` lùi về `json_object` và
**ghi log cảnh báo** — chứ không im lặng bỏ ràng buộc.

### Cấu hình mô hình cục bộ

```env
LOCAL_LLM_URL=http://localhost:11434     # Ollama
LOCAL_LLM_MODEL=llama3.1:8b
LOCAL_LLM_DIALECT=ollama                 # hoặc: openai

# vLLM / LM Studio / llama.cpp server:
# LOCAL_LLM_URL=http://localhost:8000
# LOCAL_LLM_DIALECT=openai
# LOCAL_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
```

Kiểm nhanh: `GET /api/ai/status` trả về danh sách model đang có và cho biết
model đã cấu hình có nằm trong đó không.

**Nói thẳng về chất lượng:** Llama-3-8B chạy trên máy để bàn *không* ngang
Gemini Flash ở việc trích xuất cam kết từ hội thoại tiếng Việt pha tiếng Anh.
Nó kém rõ rệt, nhất là ở việc phân biệt "đã chốt" với "đang bàn". Lớp này tồn
tại để chạy đối soát, làm chỗ hạ cánh cho mô hình fine-tune, và làm đường lùi
khi API chết — không phải để thay thế ngay hôm nay.

---

## ② Meeting Intelligence Agent

Chuỗi bốn bước, **không phải một prompt to**:

```
  distill    nén bản thoại thành mệnh đề có mốc      ← thấy transcript
  decisions  chỉ tìm quyết định                      ← CHỈ thấy mệnh đề đã nén
  actions    chỉ tìm cam kết và người nhận           ← CHỈ thấy mệnh đề đã nén
  score      chấm độ tin cậy                          ← chạy bằng Python
```

Hai bước giữa **không nhìn thấy transcript gốc** — chúng chỉ nhận các mệnh đề
đã qua kiểm dẫn chứng. Đây là cùng nguyên tắc "tách Extract khỏi Compose" của
pipeline sáu pha: bước sau không có nguyên liệu để bịa thêm.

Bước bốn cố ý **không dùng LLM**. Hỏi mô hình "anh có chắc không" là hỏi sai
đối tượng — nó trả lời theo giọng điệu của câu hỏi. Độ tin cậy tính từ những
thứ đếm được:

```
Tin cậy = 100 − (Thoại mờ × 5) − (Chưa gán người làm × 8) − (Rủi ro ảo giác × 15)
```

"Rủi ro ảo giác" ở đây đo cụ thể: số mục có câu trích **không tìm thấy** trong
bản thoại, cộng số mục bị gỡ tên người nhận vì người đó **không dự họp**.

### Ba chốt chặn chạy sau khi mô hình trả lời

Prompt có thể bị lờ đi; kiểm tra bằng Python thì không.

| Hàm | Việc |
|---|---|
| `_prune_ungrounded` | Xoá mục trỏ tới đoạn thoại không tồn tại |
| `_verify_quotes` | Gắn cờ câu trích không khớp bản thoại (không xoá — lệch vài chữ vẫn có thể đúng) |
| `_clean_assignees` | Gỡ tên người nhận không có trong danh sách tham dự |

Bộ kiểm thử `tests/test_ai_layer.py` có một provider giả **cố ý trả về rác** để
chứng minh ba chốt này chạy kể cả khi mô hình lờ hết mọi hướng dẫn.

---

## ③ Continuous Learning & Distillation Collector

Mỗi lần chủ cuộc họp phê duyệt một biên bản, họ vừa tạo ra một mẫu huấn luyện
chất lượng cao mà không hề biết: đầu vào là bản thoại thật, đầu ra là biên bản
**đã được người có trách nhiệm xác nhận là đúng**.

```
POST /api/meetings/{id}/approve
   └─ store.approve_meeting()
   └─ DataCollector.collect()        ← chỉ khi MEETY_COLLECT_TRAINING=1
         ├─ ẩn danh toàn bộ
         └─ ghi 1 dòng vào data/training/finetune_dataset.jsonl
```

Định dạng Instruction–Input–Output, đọc trực tiếp được bằng Axolotl,
LLaMA-Factory, Unsloth và HuggingFace TRL.

### Ba điều bắt buộc, không phải tuỳ chọn

1. **Chỉ lấy biên bản ĐÃ PHÊ DUYỆT.** Biên bản chờ duyệt là ý kiến của mô hình,
   chưa ai xác nhận. Huấn luyện trên đó là dạy mô hình lặp lại lỗi của chính
   nó — sai lệch tự khuếch đại qua từng vòng.
2. **Ẩn danh TRƯỚC khi ghi xuống đĩa**, không phải lúc dùng. Tệp `.jsonl` sẽ
   được copy lên máy huấn luyện, có khi lên cả dịch vụ đám mây. Mọi bản sao
   phải đã sạch.
3. **Mặc định TẮT.** Bật bằng `MEETY_COLLECT_TRAINING=1`. Thu thập dữ liệu cuộc
   họp mà không hỏi là chuyện không được làm, kể cả khi đã ẩn danh.

### Ẩn danh tới đâu là đủ — nói thẳng

Che được: email, số điện thoại (cả `0xx` và `+84`), URL kèm token, số tài
khoản, CCCD, và tên riêng lấy từ danh sách tham dự (che cả **nhãn người nói**
lẫn tên xuất hiện giữa câu).

Trong cùng một cuộc họp, "Nguyễn Văn An" luôn thành `[NGƯỜI_1]` để mô hình vẫn
học được rằng *cùng một người* nói ở nhiều chỗ. Bảng thay thế **không** dùng
chung giữa các cuộc họp — `[NGƯỜI_1]` ở cuộc A và cuộc B là hai người khác
nhau, nên không ai ghép lại được danh tính xuyên các mẫu.

**Không che được:** tên người lạ nhắc thoáng qua mà không có trong danh sách
tham dự, tên riêng của sản phẩm/khách hàng, địa chỉ. Vì vậy tệp sinh ra phải
được coi là **dữ liệu nội bộ**, không phải dữ liệu công khai. Nói khác đi là
nói sai.

### Lộ trình fine-tune

```bash
# 1. Xem đã đủ mẫu chưa
curl -b cookie http://127.0.0.1:8000/api/ai/dataset

# 2. Tách train/val (theo thứ tự thời gian, không xáo ngẫu nhiên)
python -c "from ai.collector import DataCollector; \
           print(DataCollector().export_train_val('data/training/split'))"

# 3. LoRA trên Qwen2.5-7B — chạy ở máy có GPU, không phải ở đây
#    axolotl train config.yml

# 4. Nạp vào Ollama rồi trỏ LOCAL_LLM_MODEL sang model mới
# 5. Chạy chế độ shadow vài chục cuộc họp để đối soát trước khi tin
```

Ngưỡng `ready_for_finetune` đặt ở **200 mẫu đã phê duyệt**. Dưới mức đó,
fine-tune thường cho kết quả *tệ hơn* một prompt tốt — mô hình học thuộc vài
chục ví dụ thay vì học quy luật.

---

## ④ Hybrid Routing & Consensus Engine

```
POST /api/meetings/{id}/ai/analyze  {"mode": "shadow", "secondary": "local"}
```

| Chế độ | Chạy gì | Người dùng nhận gì |
|---|---|---|
| `primary` | chỉ provider chính | kết quả provider chính |
| `shadow` | cả hai, song song | **kết quả provider chính**, kèm báo cáo đối soát |
| `consensus` | cả hai, hợp nhất | kết quả có gắn cờ chỗ bất đồng, tin cậy bị hạ |

`shadow` là chế độ để thu số liệu **mà không đánh cược** vào mô hình chưa được
kiểm chứng: provider phụ hỏng hay chậm cũng không ảnh hưởng gì tới thứ người
dùng thấy.

Ở `consensus`, provider chính là **nguồn chân lý về nội dung**; provider phụ
chỉ được làm đúng một việc — bật cờ nghi ngờ. Cho phép nó ghi đè nội dung nghĩa
là để mô hình yếu hơn sửa mô hình mạnh hơn.

### Đo cái gì

Không đo "giống nhau bao nhiêu phần trăm" — vô nghĩa, vì hai mô hình diễn đạt
khác nhau cho cùng một ý. Đo ba thứ có hậu quả thật:

1. **Quyết định bị bỏ sót** — biên bản thiếu quyết định thì vô dụng.
2. **Người nhận việc khác nhau** — lỗi nguy hiểm nhất của sản phẩm này.
3. **Mục bịa** — không có dẫn chứng, hoặc trích câu không có trong bản thoại.

Khớp quyết định dùng Jaccard trên tập từ, ngưỡng 0.55: đủ chặt để không gộp
nhầm hai quyết định khác nhau, đủ lỏng để chấp nhận cách diễn đạt khác.

`verdict` chỉ nói "Đạt" khi **không bỏ sót quyết định nào, không lệch người
nhận việc nào, mọi mục đều có dẫn chứng** — và ngay cả khi đó nó vẫn nhắc rằng
một mẫu chưa kết luận được gì, cần ít nhất 20 cuộc họp.

---

## Quan hệ với pipeline sáu pha

Agent **không thay thế** `pipeline/`. Pipeline vẫn là đường chạy chính thức cho
việc dựng biên bản: nó có cache, sổ quota, artifact từng pha để chạy lại không
tốn tiền, và 419 phép kiểm bao quanh.

Agent trả lời một câu hỏi khác: *"nếu chỉ có một transcript và một mô hình bất
kỳ, ta rút ra được gì?"* — dùng để đối soát, để đánh giá mô hình mới, và làm
đường chạy gọn cho bản on-prem.

```
Tải tệp lên  →  pipeline sáu pha  →  biên bản chính thức  →  người duyệt
                                                                  │
                                                                  ▼
                                                          DataCollector
                                                                  │
Nút "Phân tích lại"  →  MeetingAgent  →  đối soát   ←──── mô hình fine-tune
```

## Kiểm thử

```bash
pytest tests/test_ai_layer.py -v      # 40 phép kiểm, không cần mạng, không tốn quota
```

Provider giả trong bộ này cố ý trả về nội dung bịa để chứng minh các chốt chặn
hoạt động. Đó là cách duy nhất kiểm được rằng hệ thống chịu được một mô hình
tồi — chứ không phải chỉ chạy tốt với mô hình tốt.
