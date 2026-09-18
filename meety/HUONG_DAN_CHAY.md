# HƯỚNG DẪN CHẠY DỰ ÁN MEETY

Từ máy trắng đến chạy được: khoảng 10 phút.

Có **ba cách chạy**, chọn theo việc bạn muốn làm:

| Cách | Cần gì | Dùng khi nào |
|---|---|---|
| A · Mở file HTML | Không cần gì | Xem thử giao diện, gửi cho người khác xem |
| B · Chạy CLI | Python | Xử lý một cuộc họp, lấy file kết quả |
| C · Chạy máy chủ web | Python + 4 gói | Dùng thật: đăng nhập, tải lên, nhiều cuộc họp |

---

## CÁCH A — Chỉ xem giao diện (0 phút)

Nháy đúp vào `mm-ai-preview.html`.

Xong. Không cần cài gì, không cần mạng. File này tự chứa toàn bộ dữ liệu mẫu,
gửi qua Zalo cho đồng nghiệp cũng mở được.

Ở chế độ này bạn xem được mọi màn hình, nhưng **không** đăng nhập thật và
**không** tải cuộc họp lên được — trang sẽ ghi rõ điều đó ở đầu trang tổng quan.

---

## CÁCH B — Chạy pipeline bằng dòng lệnh

### B1. Cài Python

Cần **Python 3.10 trở lên**. Kiểm tra:

```powershell
python --version
```

Nếu báo lỗi hoặc thấp hơn 3.10, tải ở https://www.python.org/downloads/ —
lúc cài **nhớ tích ô “Add Python to PATH”**, thiếu ô này là nguồn gốc của
phần lớn rắc rối về sau.

### B2. Tạo môi trường ảo

Môi trường ảo giữ thư viện của dự án nằm riêng, không lẫn với Python của máy.

```powershell
cd "đường\dẫn\tới\Meeting Minutes AI"
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

### B3. Cài thư viện

```powershell
pip install -r requirements.txt
```

### B4. Đặt API key

Chép `.env.example` thành `.env`, rồi mở ra điền:

```powershell
copy .env.example .env      # Windows
cp .env.example .env        # macOS/Linux
```

Nội dung `.env`:

```
GEMINI_API_KEY=AIza...
GROQ_API_KEY=gsk_...
```

Lấy khoá **miễn phí, không cần thẻ tín dụng**:

- Gemini — https://aistudio.google.com/apikey
- Groq — https://console.groq.com/keys (chỉ cần nếu bạn nạp file **âm thanh**;
  nạp `.vtt` từ Zoom/Meet/Teams thì không cần)

Kiểm tra máy đã sẵn sàng chưa:

```powershell
python doctor.py
```

### B5. Chạy thử

Chạy **không tốn quota, không cần key** trên transcript mẫu:

```powershell
python main.py --input frontend/src/mocks/sample_transcript.json --skip-stt --date 2026-07-22 --mock
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

Kết quả nằm ở `data/artifacts/<mã cuộc họp>/`. Xem bằng trình duyệt:

```powershell
python tools/build_preview.py --latest --out bien_ban.html
```

---

## CÁCH C — Chạy máy chủ web (dùng thật)

Làm xong bước **B1 → B4** ở trên, rồi:

### C1. Sinh file giao diện

Máy chủ phục vụ file `mm-ai-preview.html`. File này sinh ra từ template:

```powershell
python tools/build_preview.py --out mm-ai-preview.html
```

Chạy lại lệnh này **mỗi khi sửa** `frontend/preview/template.html`.

### C2. Khởi động máy chủ

```powershell
python run_server.py
```

Thấy dòng này là được:

```
  MM AI đang chạy tại  http://127.0.0.1:8000
  Tài liệu API         http://127.0.0.1:8000/api/docs
```

Mở trình duyệt vào **http://127.0.0.1:8000**.

> Đừng nháy đúp vào file HTML lúc này. Mở bằng đường dẫn `file://` thì trình
> duyệt coi đó là nguồn khác với máy chủ và **chặn cookie phiên** — bạn sẽ
> đăng nhập được nhưng vào lại là mất phiên. Luôn vào bằng `http://127.0.0.1:8000`.

Các tuỳ chọn khác:

```powershell
python run_server.py --port 9000        # đổi cổng
python run_server.py --reload           # tự nạp lại khi sửa mã Python
python run_server.py --host 0.0.0.0     # cho máy khác trong mạng LAN vào
```

### C3. Dùng thử

1. Bấm **Đăng ký**, nhập email và mật khẩu (ít nhất 8 ký tự).
2. Tài khoản mới có sẵn một biên bản mẫu để bấm vào xem ngay.
3. Bấm **＋ Tạo cuộc họp mới** → kéo thả file `.vtt`, `.mp3`, `.m4a`…
4. Thanh tiến trình hiện **đúng 8 pha thật** của pipeline kèm chi phí quota
   từng pha. Xong thì biên bản tự vào danh sách.

### C3-0. Hai tài khoản kiểm thử phân quyền (nhanh nhất)

```powershell
python tools/seed_data.py --accounts
```

Lệnh này dựng sẵn nguyên luồng kiểm thử: tạo hai tài khoản, nạp hai cuộc họp
cho Owner, và mời Member vào cả hai.

| Tài khoản | Mật khẩu | Vai trò |
|---|---|---|
| `owner@meety.ai` | `admin123` | Chủ toạ — toàn quyền |
| `member@meety.ai` | `user123` | Thành viên — chỉ đọc |

> Hai mật khẩu này **cố ý ngắn dưới 8 ký tự**, nên chúng không đăng ký được
> qua giao diện. Đó là chủ ý: chúng chỉ dùng để thử trên máy, và việc chúng bị
> giao diện từ chối chính là bằng chứng ràng buộc mật khẩu đang có hiệu lực.
> Chạy lại lệnh trên bất cứ lúc nào để đặt lại mật khẩu về mặc định.

### Kịch bản kiểm thử từng bước

Mở **hai cửa sổ**: một cửa sổ thường và một cửa sổ ẩn danh, để hai tài khoản
đăng nhập song song mà không đá phiên của nhau.

**Bước 1 — Owner đăng nhập** (`owner@meety.ai` / `admin123`)

Vào một cuộc họp. Phải thấy:
- Thanh vai trò ghi **Chủ toạ**
- Nút `＋ Thêm công việc mới` trong khối Công việc
- Nút thùng rác ở góc mỗi thẻ việc (khi rê chuột)
- Nút `⋯` cạnh mỗi thành viên (trừ chính mình)

**Bước 2 — Member đăng nhập** (`member@meety.ai` / `user123`, cửa sổ ẩn danh)

Vào **cùng cuộc họp đó**. Phải thấy:
- Thanh vai trò ghi **Thành viên**, có dòng "chế độ chỉ đọc"
- **Không** có nút `⋯` nào ở khối Thành viên
- **Không** có nút thêm việc, xoá việc, mời người, phê duyệt
- Khối Công việc chỉ hiện **việc giao cho chính mình**, kèm nút
  *Xem tất cả (N)* nếu muốn xem bối cảnh

**Bước 3 — Owner gán việc cho Member** ← *đây là lỗi cũ*

Ở cửa sổ Owner, chọn Member trong ô người nhận của một công việc.

| Phải xảy ra | Không được xảy ra |
|---|---|
| Hiện *"Đã giao việc cho …"* | Báo lỗi thiếu quyền |
| Cửa sổ **Member tự hiện việc đó trong ~3 giây**, không cần bấm F5 | Member phải tải lại trang mới thấy |

Nhịp đồng bộ nền chạy 2,5 giây một lần khi đang mở trang chi tiết. Nếu chuyển
sang tab khác thì nó tạm dừng, quay lại thì chạy tiếp.

**Bước 4 — Member cập nhật trạng thái việc của mình**

Bấm vào pill trạng thái: `Cần làm → Đang làm → Hoàn thành`. Phải đổi được.
Bấm vào pill **ưu tiên**: phải bị khoá (con trỏ không đổi, có tooltip giải
thích). Ưu tiên là phán đoán quản lý, không phải cảm nhận của người thực thi.

**Bước 5 — Owner nâng Member lên đồng chủ toạ**

Bấm `⋯` cạnh Member → **Chỉ định làm đồng chủ toạ**. Trong ~3 giây, cửa sổ
Member đổi thanh vai trò thành **Đồng chủ toạ** và hiện thêm các nút quản trị.

**Bước 6 — Kiểm giới hạn của đồng chủ toạ**

Ở cửa sổ Member (giờ là đồng chủ toạ), bấm `⋯` cạnh một thành viên khác:

| Thấy | Không thấy |
|---|---|
| Chỉ định làm đồng chủ toạ | Chuyển quyền chủ toạ |
| | Bãi nhiệm đồng chủ toạ |
| | Gỡ khỏi cuộc họp |

Đồng chủ toạ vẫn gán việc, thêm việc, xoá việc, phê duyệt và mời người bình
thường.

**Bước 7 — Chuyển quyền chủ toạ**

Ở cửa sổ Owner, bấm `⋯` → **Chuyển quyền chủ toạ** → xác nhận. Owner cũ tụt
xuống **đồng chủ toạ** (vẫn quản trị được, chỉ mất quyền chuyển quyền và bãi
nhiệm), Member trở thành chủ toạ.

**Bước 8 — Thu nhỏ cửa sổ** (Bài toán 1)

Kéo hẹp cửa sổ trình duyệt xuống dưới 1080px. Thanh trên cùng phải:
- Giữ nguyên chiều cao, không xuống dòng, không tràn viền
- Sáu nút điều hướng gom vào một nút `☰` — bấm vào ra dropdown đủ 6 mục
- Logo · Nút hành động · Chuông · Avatar luôn còn nguyên

Dưới 780px, nhãn nút hành động rút gọn còn dấu `＋`.

### Chạy tự động thay vì bấm tay

```powershell
node tests/frontend/online_test.js
```

Bộ này tự bật máy chủ, tạo hai tài khoản, mở **hai phiên trình duyệt song
song** và đi hết đúng tám bước trên — 65 phép kiểm, khoảng 40 giây.

### C3a. Nạp cuộc họp mẫu để thử ngay

Không muốn tự thu âm mà vẫn cần dữ liệu để bấm:

```powershell
python tools/seed_data.py --create-user
```

Nạp hai kịch bản đầy đủ — một cuộc họp kỹ thuật (Sprint Planning, có quyết định
bị đảo ngược giữa cuộc họp và hai việc không ai nhận) và một cuộc họp kinh
doanh (Chiến lược Quý 4, có bất đồng, số liệu tài chính, và một đoạn thoại
nghe không rõ). Đăng nhập bằng `demo@meety.vn` / `meety-demo-2026`.

Muốn chạy pipeline **thật** trên hai kịch bản đó thay vì nạp thẳng vào DB:

```powershell
python tools/seed_data.py --export data/kich_ban
```

rồi tải hai tệp `.json` sinh ra lên qua nút **＋ Tạo cuộc họp mới**.

### C3b. Thử phân quyền chủ / thành viên

Mở một biên bản, kéo tới khối **Thành viên**:

1. Gõ email vào ô rồi bấm **＋ Mời thành viên**. Mời được cả người **chưa có
   tài khoản** — lời mời chờ sẵn theo email, họ đăng ký xong là thấy ngay.
2. Ở mỗi công việc, ô chọn người nhận cho phép gán tay. Việc nào mô hình đã
   rút được tên và tên đó trùng khít với đúng một thành viên thì hệ thống **tự
   gán sẵn**, có nhãn “tự gán”.
3. Nút gạt **XEM VỚI TƯ CÁCH: CHỦ CUỘC HỌP / THÀNH VIÊN** ở đầu trang cho bạn
   thử ngay giao diện của người được mời — không cần đăng nhập bằng tài khoản
   khác.

> Nút gạt đó **không phải hàng rào bảo mật**, nó chỉ đổi cách hiển thị.
> Chặn thật nằm ở máy chủ: mọi endpoint ghi đều qua `require_owner`. Bạn có
> thể tự kiểm bằng cách đăng nhập tài khoản thành viên rồi gọi thẳng API — sẽ
> nhận `403`.

Muốn kiểm bằng hai tài khoản thật: mở thêm một **cửa sổ ẩn danh**, đăng ký
email khác, rồi mời email đó vào cuộc họp.

**Bật xác thực 2 lớp:** vào ảnh đại diện → *Bảo mật* → *Bật ngay*. Chép chuỗi
khoá vào Google Authenticator (chọn “nhập bằng khoá thủ công”), nhập mã 6 số
để xác nhận. Từ lần sau đăng nhập sẽ cần mã.

### C3c. Thu cuộc họp đang diễn ra

Bấm **＋ Tạo cuộc họp mới** → **Thu cuộc họp đang diễn ra** → **Thu tiếng tab**.

Đọc kỹ modal hướng dẫn, vì đây là chỗ dễ sai nhất:

1. Trong hộp thoại của trình duyệt, chọn thẻ **Thẻ** (Chrome Tab) — **không**
   chọn "Toàn màn hình". Chọn toàn màn hình thì macOS không cho tiếng hệ thống.
2. Chọn đúng tab đang họp (Meet / Zoom Web / Teams).
3. **Tích ô "Chia sẻ âm thanh của thẻ"** ở góc dưới bên trái. Không tích thì
   không có tiếng — và Meety sẽ báo lỗi ngay chứ không ghi im lặng.

Meety trộn tiếng tab với micro của bạn, huỷ phần hình ngay khi có luồng, ghi ra
tệp rồi gửi lên máy chủ chạy pipeline như tệp tải lên bình thường.

> Chỉ chạy trên **Chrome, Edge, Brave** bản máy tính. Firefox và Safari nhận
> lệnh nhưng bỏ qua phần tiếng **mà không báo lỗi** — đây là hạn chế của trình
> duyệt, không phải của Meety. Cần `https://` hoặc `localhost`.

### C3c-2. Nghe lại ghi âm và tua

Nút Play chỉ kêu khi cuộc họp **có tệp ghi âm kèm theo** — tức là được nạp từ
`.mp3/.wav/.m4a/.mp4/.webm`, hoặc thu trực tiếp trên trình duyệt. Cuộc họp nạp
từ `.vtt` hay `.json` thì không có gì để phát, và giao diện nói thẳng điều đó
thay vì để đồng hồ đứng ở 00:00.

Máy chủ phục vụ âm thanh qua **HTTP Range Request**: kéo thanh trượt về giữa
bài, trình duyệt hỏi đúng đoạn byte cần và máy chủ trả `206 Partial Content`.
Không có phần đó thì tua sẽ nhảy về đầu, và với tệp `.webm` từ máy ghi âm,
trình duyệt còn báo thời lượng vô hạn nên thanh tiến trình không vẽ được.

Kiểm nhanh bằng dòng lệnh:

```powershell
curl -i -H "Range: bytes=0-99" http://127.0.0.1:8000/api/meetings/<id>/audio
# phải thấy: HTTP/1.1 206 Partial Content  +  Content-Range: bytes 0-99/...
```

### C3d. Phê duyệt và xuất Word

Mở một biên bản → cuối phần **Kiểm chứng** có ba nút:

| Nút | Việc |
|---|---|
| ✓ Phê duyệt biên bản | Mở modal xác nhận, ghi lại người duyệt và thời điểm |
| 📄 Xuất Word (.docx) | Biên bản hành chính: Times New Roman 13pt, lề theo Nghị định 30, có bảng thành phần tham dự và bảng phân công |
| Xuất file Markdown (.md) | Bản gọn, chạy được cả khi không có máy chủ |

Tệp `.docx` do **máy chủ** dựng vì đó là nơi có đủ dữ liệu thành viên và phân
công. Thành viên cũng tải được — họ đã đọc toàn bộ nội dung trên màn hình rồi,
chặn tải xuống không bảo vệ được gì.

### C3e. Quản lý công việc

Mỗi thẻ việc có đúng **hai** nhãn bấm được, không hơn:

* **Trạng thái** — Cần làm → Đang làm → Hoàn thành. Chủ toạ **và người được
  giao việc** đều đổi được: người làm mới biết việc đã xong hay chưa.
* **Ưu tiên** — Cao / Trung bình / Thấp. Chỉ chủ toạ đổi được. Mô hình **không
  đoán** trường này: mức ưu tiên phụ thuộc bối cảnh ngoài cuộc họp mà bản thoại
  không hề chứa, nên mặc định luôn là Trung bình.

**Sửa hạn chót:** bấm thẳng vào ô ngày. Mô hình quy đổi "cuối tuần này" thành
ngày cụ thể và thường lệch — bản người sửa được lưu ở lớp riêng, **không ghi
đè** ngày mô hình rút ra từ lời nói (đó là bằng chứng).

**Xoá việc:** rê chuột lên thẻ, nút thùng rác hiện ở góc. Chỉ chủ toạ. Xoá
**mềm** — việc biến khỏi màn hình và khỏi tài liệu xuất ra, nhưng hệ thống giữ
dấu vết để biết mô hình hay bắt nhầm ở đâu.

**Thêm việc thủ công:** nút `＋ Thêm công việc mới`. Việc thêm tay **không có
dẫn chứng** trong bản thoại, và điều đó là đúng — nó không đến từ lời nói nào.
Giao diện gắn nhãn "Thêm tay" để người đọc không đi tìm mốc thời gian không
tồn tại.

### C3f. Thu gọn từng khối

Mỗi khối lớn (Tóm tắt, Quyết định, Công việc, Bản thoại) có nút `▾` ở góc phải.
Thu gọn rồi thì **tiêu đề và badge tóm tắt vẫn hiện** — ví dụ "3 chốt · 1 bị
thay thế" — nên vẫn biết trong đó có gì mà không phải mở ra.

### C4. Dừng máy chủ

`Ctrl + C` ở cửa sổ dòng lệnh.

---

## TẦNG AI: MÔ HÌNH CỤC BỘ VÀ CHƯNG CẤT TRI THỨC

Phần này **không bắt buộc** để chạy Meety. Bỏ qua được nếu chỉ dùng Gemini.

### Chạy mô hình tại chỗ (không cần API, không rời máy)

```powershell
# 1. Cài Ollama: https://ollama.com/download
ollama pull llama3.1:8b        # hoặc qwen2.5:7b — tiếng Việt tốt hơn
ollama serve

# 2. Thêm vào .env
#    LOCAL_LLM_URL=http://localhost:11434
#    LOCAL_LLM_MODEL=qwen2.5:7b
#    LOCAL_LLM_DIALECT=ollama

# 3. Kiểm tra máy chủ thấy model chưa
curl http://127.0.0.1:8000/api/ai/status
```

### Đối soát mô hình cục bộ với Gemini

Mở một biên bản, gọi:

```
POST /api/meetings/{id}/ai/analyze   {"mode": "shadow", "secondary": "local"}
```

Chế độ `shadow` chạy **cả hai song song** nhưng chỉ trả kết quả của Gemini —
mô hình cục bộ chỉ để đo. Báo cáo cho biết nó bỏ sót quyết định nào, gán lệch
người nhận việc nào, và bịa ra mục nào.

Đó là cách duy nhất trả lời được câu "mô hình cục bộ đã đủ tốt chưa" trên chính
dữ liệu của tổ chức bạn, thay vì tin vào điểm benchmark chung chung.

### Thu dữ liệu để fine-tune mô hình riêng

```env
MEETY_COLLECT_TRAINING=1
```

**Mặc định TẮT.** Bật rồi thì mỗi lần bạn phê duyệt một biên bản, cặp
`[bản thoại] → [biên bản đã duyệt]` được ẩn danh và ghi vào
`data/training/finetune_dataset.jsonl`.

Ẩn danh che email, số điện thoại, số tài khoản, CCCD, URL kèm token, và tên
người dự họp. **Không** che được tên người lạ nhắc thoáng qua hay tên khách
hàng — nên hãy coi tệp đó là **dữ liệu nội bộ**, không phải dữ liệu công khai.

### Chấm điểm mô hình bằng Meeting-Bench

Sau khi phê duyệt một biên bản, bản đó trở thành **đáp án chuẩn**. Chạy lại mô
hình trên cùng bản thoại rồi so:

```
POST /api/meetings/{id}/ai/benchmark
```

Bốn thước đo, mỗi cái đo một loại hỏng khác nhau: bỏ sót **quyết định** (biên
bản vô dụng), bỏ sót **công việc** (không ai làm), sai **người nhận việc** (lỗi
nguy hiểm nhất), sai **hạn chót** (trễ mà không ai biết).

Chấm bằng hàm Python thuần, **không dùng LLM để chấm LLM** — cách đó thiên vị
mô hình cùng họ với giám khảo và cho điểm khác nhau giữa hai lần chạy.

Chạy trên tệp dữ liệu:

```powershell
python -m ai.meeting_evaluator data/bench/cases.jsonl
```

### Xem mô hình đang yếu ở khâu nào

```
GET /api/ai/learning
```

Mỗi lần bạn sửa hạn chót, đổi người nhận, xoá việc thừa hay thêm việc bị bỏ
sót, hệ thống ghi lại **loại** thao tác đó. Báo cáo cho biết người dùng đang
phải sửa nhiều nhất ở khâu nào — dùng được **ngay**, trước cả khi đủ mẫu để
fine-tune, vì nó chỉ đúng kỹ năng cần chỉnh prompt.

Ví dụ: nếu 40 lần đều phải sửa hạn chót, vấn đề nằm ở đúng một kỹ năng — quy
đổi cụm chỉ thời gian tương đối. Sửa bằng prompt trong một buổi chiều, không
cần fine-tune gì cả.

Chi tiết kiến trúc, lộ trình fine-tune và giới hạn: **`ai/README.md`**.

> **Về DeepSeek-Harness — nói cho đúng.** Repo `deepseek-ai/deepseek-harness`
> là một **agent harness**: bộ khung chạy tác tử theo kiến trúc plugin, dựng
> trên kernel Cordis, viết bằng TypeScript/Node, có Web UI riêng. Nó **không**
> phải bộ khung chấm điểm benchmark. Meeting-Bench ở đây lấy khuôn mẫu từ
> `EleutherAI/lm-evaluation-harness` — nơi thật sự đặt ra cách làm này. Muốn
> dùng DSH thật thì hướng đúng là thêm DeepSeek làm một provider trong
> `providers/llm/` (dễ, vì `LocalLLMProvider` đã nói được giao thức
> OpenAI-compatible), hoặc viết một `dsh-plugin` — nhưng đó là hệ TypeScript,
> khác hệ với backend Python của Meety.

---

## KIỂM THỬ

```powershell
# Toàn bộ Python — 864 phép kiểm, chạy trong tiến trình, không mở cổng
python -m pytest tests/ -q

# Backend — bật máy chủ thật rồi đi hết hành trình người dùng qua HTTP (93)
python tools/smoke_server.py

# Giao diện, chế độ rời máy chủ — nạp HTML vào DOM thật rồi bấm nút (204)
npm install jsdom
node tests/frontend/dom_test.js

# Giao diện NỐI máy chủ thật — hai tài khoản song song, phân quyền, đồng bộ (65)
node tests/frontend/online_test.js
```

Chi tiết từng bộ và danh sách lỗi mà chúng đã bắt được: `tests/README.md`.

---

## HỎNG THÌ XEM ĐÂY

**`ModuleNotFoundError: No module named 'fastapi'`**
Chưa kích hoạt `.venv`, hoặc chưa `pip install -r requirements.txt`.
Đầu dòng lệnh phải có `(.venv)`.

**`python` không được nhận là lệnh**
Lúc cài Python chưa tích “Add Python to PATH”. Cài lại và tích ô đó, hoặc
dùng `py` thay cho `python` trên Windows.

**Máy chủ báo “Chưa có mm-ai-preview.html”**
Chạy `python tools/build_preview.py --out mm-ai-preview.html`.

**Đăng nhập xong kẹt ở nút "Đang xử lý…" dù log máy chủ toàn 200 OK**
Lỗi JavaScript lúc dựng màn hình — backend không sai. Mở Console của trình
duyệt (F12) để thấy thông báo thật. Đã sửa ở bản này; nếu vẫn gặp, chạy
`node tests/frontend/online_test.js` để tái hiện và gửi lại kết quả.

**`pip install -r requirements.txt` báo lỗi `charmap codec can't decode`**
`requirements.txt` phải là ASCII thuần: trên Windows pip đọc file này bằng mã
trang hệ điều hành (cp1252) chứ không phải UTF-8. Đã sửa ở bản này. Kiểm bằng
`python doctor.py`.

**`doctor.py` báo `ZoneInfoNotFoundError: America/Los_Angeles`**
**Không phải lỗi.** Windows không kèm cơ sở dữ liệu múi giờ IANA, nhưng
`core/quota.py` có sẵn bộ tính giờ Thái Bình Dương tự lập nên hạn mức vẫn đếm
đúng. Muốn hết dòng cảnh báo thì `pip install tzdata`.

**Đăng nhập xong vào lại thì mất phiên**
Bạn đang mở bằng `file://`. Vào bằng `http://127.0.0.1:8000`.

**Trang tổng quan hiện dải vàng “Đang chạy chế độ giả lập”**
Chưa có `GEMINI_API_KEY` trong `.env`. Máy chủ vẫn chạy, nhưng biên bản do bản
giả lập sinh ra, **không phải mô hình thật**. Thêm khoá rồi khởi động lại.

**Tải file âm thanh lên thì lỗi ở pha nhận dạng giọng nói**
Thiếu `GROQ_API_KEY`. Không có key này thì chỉ nạp được `.vtt`, `.srt`, `.json`.

**`Address already in use` / cổng bận**
Cổng 8000 đang có thứ khác dùng. `python run_server.py --port 9000`.

**Ghi âm trực tiếp không thấy dạng sóng**
Chỉ chạy trên Chrome, Edge, Brave bản máy tính. Firefox và Safari nhận lệnh
nhưng bỏ qua phần tiếng mà không báo lỗi. Trình duyệt cũng chỉ cho truy cập
micro qua `https://` hoặc `localhost` — trùng khớp với cách chạy ở trên.

**Muốn xoá sạch làm lại**
Xoá `data/app.db*` (tài khoản, cuộc họp, thông báo) và `data/artifacts/`
(kết quả pipeline). Quota và cache cũng nằm trong `app.db` nên xoá là mất
lịch sử đếm quota.

---

## CẤU TRÚC THƯ MỤC

```
main.py                 CLI xử lý một cuộc họp
run_server.py           Khởi chạy máy chủ web
doctor.py               Kiểm tra môi trường

server/                 ← thêm ở bản v2
  app.py                FastAPI: định tuyến, phục vụ giao diện
  store.py              SQLite: người dùng, phiên, cuộc họp, thông báo
  security.py           scrypt, token phiên, TOTP (chỉ dùng thư viện chuẩn)
  jobs.py               Chạy pipeline ở luồng nền, báo tiến độ

pipeline/               Phần lõi — 6 pha, không đổi
  orchestrator.py       Điều phối, ghi artifact từng pha để chạy lại được
  s0_ingest.py … s7_validate.py

providers/              Gemini, Groq Whisper, bản giả lập
schemas/                Kiểu dữ liệu pydantic dùng chung
core/                   env, db, cache, quota, logging
nlp/                    Ngày tháng tiếng Việt, xưng hô

ai/                     Tầng AI — xem ai/README.md
  agent.py              Chuỗi prompt + ba chốt chặn chống bịa
  collector.py          Thu dữ liệu chưng cất, ẩn danh trước khi ghi
  learning_collector.py Ghi Diff người sửa — vòng lặp 4 bước tự học
  meeting_evaluator.py  Meeting-Bench: chấm điểm biên bản AI
  consensus.py          Chạy song song và đối soát hai mô hình
server/audio_stream.py  Phát ghi âm qua HTTP Range (206 Partial Content)
providers/llm/local.py  Ollama / vLLM / mọi endpoint tương thích OpenAI
exporters/docx.py       Xuất Word, viết thẳng OOXML, không thêm phụ thuộc
tools/seed_data.py      Hai kịch bản cuộc họp thật để thử backend
frontend/assets/logo/   Bộ nhận diện Meety (xem README.md trong đó)
frontend/preview/
  template.html         ← SOURCE của giao diện. Sửa ở đây.
mm-ai-preview.html      ← file SINH RA. Đừng sửa trực tiếp.

tests/
  README.md             Bản đồ 7 bộ kiểm thử và lỗi từng bộ đã bắt được
  test_security_unit.py     scrypt, TOTP, token (36)
  test_store_unit.py        lược đồ, khớp tên tự động (42)
  test_api_security.py      CSRF, IDOR, chèn mã, rò rỉ (61)
  test_api_validation.py    biên, sai kiểu, hợp đồng HTTP (86)
  test_api_concurrency.py   đua nhau, lặp, khởi động lại (19)
  test_jobs_unit.py         luồng nền và pipeline (27)
  test_server_api.py        luồng người dùng, phân quyền, task CRUD, audio (89)
  test_ai_layer.py          agent, ẩn danh, đối soát mô hình (40)
  test_evaluator.py         Meeting-Bench: chấm điểm biên bản (20)
  frontend/dom_test.js      giao diện rời máy chủ (245)
  frontend/online_test.js   hai tài khoản + máy chủ thật + HTTP thật (65)
tools/
  build_preview.py      Sinh mm-ai-preview.html từ template
  smoke_server.py       Bật máy chủ thật, đi hết hành trình người dùng
```

---

## ĐIỀU CẦN BIẾT TRƯỚC KHI ĐƯA LÊN MÔI TRƯỜNG THẬT

Bản này chạy tốt cho một nhóm nhỏ trên máy nội bộ. Bốn chỗ phải sửa trước khi
mở ra Internet, nói thẳng để không ai bị bất ngờ:

1. **`secure=False` ở cookie phiên** (`server/app.py`). Đang tắt để chạy được
   trên `http://localhost`. Sau HTTPS thì bật `secure=True`, nếu không cookie
   đi qua đường không mã hoá.
2. **Nội dung cuộc họp lưu dưới dạng thô** trong SQLite. Chưa mã hoá. Đây là
   việc còn nợ, không phải việc đã xong.
3. **Chưa giới hạn số lần thử đăng nhập.** Cần thêm đếm và khoá tạm theo IP.
4. **Hàng đợi việc nằm trong bộ nhớ tiến trình.** Khởi động lại máy chủ giữa
   chừng thì job đang chạy mất dấu — nhưng artifact từng pha vẫn còn trên đĩa,
   nên chạy lại không tốn lại quota.

---

## LƯỢC ĐỒ & API PHÂN QUYỀN

Hai bảng mới, cả hai đều là **lớp phủ** — không sửa vào biên bản mà mô hình đã
sinh ra. Biên bản là bằng chứng; bằng chứng thì không được ghi đè.

```sql
meeting_members (
    id, meeting_id, user_id, email, display_name,
    role,            -- 'owner' | 'member'
    invited_by, invited_at, accepted,
    UNIQUE (meeting_id, email)
)

task_assignments (
    meeting_id, task_id,
    member_id,       -- NULL = cố ý bỏ trống
    source,          -- 'auto' (khớp tên) | 'manual' (chủ tự chọn)
    assigned_by, assigned_at,
    PRIMARY KEY (meeting_id, task_id)
)
```

Ba quyết định trong lược đồ này:

**Mời bằng email, không bằng `user_id`.** Người được mời thường chưa có tài
khoản — đó là trường hợp *thường gặp*, không phải ngoại lệ. `user_id` để `NULL`
cho tới khi họ đăng ký, lúc đó `link_pending_invites` nối lại.

**Chỉ hai vai trò.** Thêm vai trò về sau dễ hơn nhiều so với gỡ vai trò đã lỡ
phát cho người dùng.

**`source` phân biệt auto và manual.** Người đọc cần biết dòng nào do máy khớp
tên (có thể sai) và dòng nào do người quyết định.

### API

| Method | Đường dẫn | Ai gọi được |
|---|---|---|
| `GET` | `/api/meetings` | ai cũng — trả cả cuộc họp được mời, kèm `my_role` |
| `GET` | `/api/meetings/{id}` | chủ **hoặc** thành viên |
| `GET` | `/api/meetings/{id}/members` | chủ **hoặc** thành viên |
| `POST` | `/api/meetings/{id}/members` | **chỉ chủ** — mời theo email |
| `DELETE` | `/api/meetings/{id}/members/{mid}` | **chỉ chủ** — không gỡ được chủ |
| `PUT` | `/api/meetings/{id}/tasks/{tid}/assignee` | **chỉ chủ** |
| `POST` | `/api/meetings/{id}/tasks/auto-assign` | **chỉ chủ** |
| `PATCH` | `/api/meetings/{id}/status` | **chỉ chủ** |
| `PUT` | `/api/meetings/{id}/speakers` | **chỉ chủ** |

Người ngoài nhận **404**, không phải 403. Trả 403 là xác nhận cuộc họp đó có
tồn tại, cho phép người lạ dò xem ai đang họp với ai.

### Luật khớp tên tự động

Chỉ gán khi tên mô hình rút ra trùng khít với **đúng một** thành viên (theo tên
đầy đủ, hoặc theo tên riêng cuối cùng). Có hai người cùng tên “Tuấn” thì **bỏ
qua, để trống**.

Đây là cùng một nguyên tắc chạy suốt dự án: gán sai người cho một cam kết là
loại lỗi nguy hiểm nhất của sản phẩm này. Thà để trống và bật cảnh báo còn hơn
đoán.
