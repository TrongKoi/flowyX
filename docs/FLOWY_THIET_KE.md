# Flowy — thiết kế hệ thống

**Hackathon ADC RMIT 2026 — Disability focus area: Neurodivergence (ADHD)**
Thi ngày 21–23/09/2026.

Tài liệu này ghi lại **cái gì được làm, vì sao, và dựa trên bằng chứng
nào**. Nó là nguồn chân lý cho đợt làm lại này.

> **Trạng thái**: v2, cập nhật 15/09/2026 sau khi nhận bảng research của
> nhóm. Bảng đó lật một phần thiết kế ở v1 — xem §2.4.
>
> **Ghi chú 28/09/2026.** §2–§4 (bằng chứng, ba tính năng, ranh giới
> thiết bị y tế) vẫn đúng. Những phần sau đã **không còn khớp mã nguồn**
> và giữ lại chỉ như lịch sử quyết định: §5 và §7.2 (lõi Python
> `adc_wayfinding/` và cầu nối laptop — đã gỡ, app giờ chạy trọn trên
> máy), §7.4 (nhân vật đồng hành — đã bỏ 16/09), mọi chỗ nhắc bản iOS
> (đã bỏ). Hiện trạng: [`KIEN_TRUC.md`](KIEN_TRUC.md).

---

## §1. Flowy là gì, sau khi bỏ điều hướng

Quyết định đã chốt: **bỏ hẳn phần dẫn đường trong nhà.** Flowy không còn
là app chỉ đường; nó là app **hỗ trợ thực thi** cho người ADHD.

Ba tính năng chính:

| | Triệu chứng nhắm tới |
|---|---|
| **Mù thời gian** | Khó cảm nhận thời gian trôi, khó ước lượng một việc mất bao lâu |
| **Sao nhãng, mất tập trung** | Bị ngắt mạch rồi không quay lại được việc đang làm |
| **Tê liệt trước nhiệm vụ** | Biết phải làm gì nhưng không bắt đầu được |

Nền tảng: **iOS là bản chính**, Android dùng để kiểm thử và demo.

---

## §2. Nền tảng bằng chứng

### 2.1. ADHD là vấn đề THỰC THI, không phải vấn đề KIẾN THỨC

Đây là câu quan trọng nhất trong cả tài liệu.

Tài liệu về CBT cho người lớn ADHD ghi rằng phần lớn thân chủ nói họ
*"biết phải làm gì, nhưng khó làm được"* — ADHD là **một vấn đề thực
thi, không phải một vấn đề kiến thức**.

Hệ quả trực tiếp, và nó loại bỏ cả một hướng thiết kế:

> **Mọi tính năng chỉ cung cấp thông tin, lời khuyên, hay bài học đều
> không giải quyết vấn đề.** Người dùng đã biết rồi.

Nên Flowy không làm thư viện bài viết, không làm khoá học, không làm bộ
mẹo. Mỗi tính năng phải **can thiệp vào đúng khoảnh khắc thực thi** —
lúc người dùng đang kẹt, chứ không phải lúc họ đang rảnh đọc.

Đây cũng là câu trả lời sẵn cho giám khảo nếu bị hỏi *"khác gì mấy app
ADHD đã có"*.

### 2.2. Các app hiện có đứng yên sau lần cài đặt đầu

Khảo sát các công cụ hỗ trợ ADHD chỉ ra một khoảng trống chung: **rất ít
công cụ có cơ chế học hay phản hồi thời gian thực sau bước tuỳ chỉnh ban
đầu.** Phần lớn can thiệp là tĩnh sau khi triển khai, không thích ứng
theo mẫu chú ý hay chiến lược đang thay đổi của người dùng.

Riêng nhóm công cụ **body doubling** — nhóm có bằng chứng mạnh nhất —
bị chê ở ba điểm: **lịch cứng nhắc, thiếu tương tác, ít tuỳ biến**.

Hệ quả cho Flowy: **thứ phân biệt chúng ta không phải danh sách tính
năng mà là việc app HỌC từ chính người dùng.** Xem §3.1.

### 2.3. Body doubling: can thiệp có bằng chứng mạnh nhất

Một khảo sát 220 người neurodivergent: **85% báo cải thiện rõ rệt về khả
năng hoàn thành nhiệm vụ** nhờ body doubling. Một nghiên cứu VR năm 2025
cho thấy **cả người thật lẫn body double bằng AI** đều cải thiện đáng kể
tốc độ, độ chính xác và khả năng duy trì chú ý ở người lớn ADHD.

Điều này quan trọng: **body double không nhất thiết phải là người thật.**
Đó là cánh cửa để làm tính năng này trên một app chạy một mình, không cần
ghép cặp, không cần đặt lịch — tức là gỡ đúng ba điểm yếu ở §2.2.

### 2.4. Bảng research của nhóm lật một phần thiết kế v1

Bảng `Elicit — Nhu cầu ADHD đối với ứng dụng di động` có một dòng đáng
giá hơn tất cả phần còn lại.

**Nhóm nhu cầu "Nhắc việc và tuân thủ thuốc"**: một thử nghiệm ngẫu
nhiên có đối chứng trên **73 người lớn ADHD trong 3 tháng** cho thấy app
FOCUS **không cải thiện có ý nghĩa** chỉ số sở hữu thuốc. Thứ làm thay
đổi con số là **ưu đãi tài chính** — nó làm tăng lượt đăng ký liều và
đạt tỷ lệ áp dụng app 100% trong nhóm có ưu đãi.

Kết luận của bảng: *"nhắc đơn thuần chưa đủ; hành vi và động lực/khuyến
khích quan trọng."*

**Vì sao điều này lật thiết kế.** Ở §2.1 tôi viết ADHD không phải vấn đề
kiến thức. Bằng chứng này đi xa hơn một bước:

> **Nó cũng không phải vấn đề NHẮC NHỞ.**
>
> Một lời nhắc cũng là một lần chuyển giao thông tin. Thử nghiệm trên
> chứng minh chuyển giao thông tin không tạo ra hành động.

Điều này đụng thẳng vào bản v1 của tài liệu này: `timeblind.py` và phần
lớn §3.1 xoay quanh **nhắc đúng lúc**. Theo bằng chứng, nhắc là điều
kiện cần nhưng rõ ràng không đủ.

**Hai dòng khác trong bảng cùng chỉ một hướng.**

Tổng quan 2025 về app ADHD: **sàng lọc 829 app, chỉ 17 app đạt tiêu
chí** — tỷ lệ 2%. Chất lượng tổng thể ở mức trung bình, và *"nhiều app
chủ yếu giáo dục tâm lý"*. Tức là thị trường đã bão hoà đúng cái hướng
mà §2.1 nói là không hiệu quả.

Cũng tổng quan đó: **tính năng tạo tương tác liên quan tích cực với chất
lượng app; thiếu engagement làm giảm điểm chất lượng.**

### 2.5. Luận điểm trung tâm: ĐỒNG ĐIỀU HOÀ, không phải tự điều hoà

Một nghiên cứu 2026 khép kín lập luận. Nhóm tác giả phỏng vấn sâu **22
người lớn ADHD**, rồi cho **20 người khác** đánh giá 13 ý tưởng thiết kế
AI. Kết quả:

- Quản lý nhiệm vụ ở người lớn ADHD **được kiến tạo chung về mặt quan hệ
  và cảm xúc**, chứ không phải một hành vi cá nhân đơn độc. Họ xử lý việc
  **thông qua sự ăn khớp cảm xúc và quan hệ với người khác**, không phải
  bằng tự chủ đơn độc.
- Công cụ năng suất hiện có được thiết kế cho người neurotypical, nên
  **mặc định người dùng có khả năng tự điều hoà ổn định và thời gian
  tuyến tính** — cả hai đều không đúng với ADHD.
- Điều người dùng chọn: hệ thống hỗ trợ **đồng điều hoà (co-regulation)**
  và **nhịp chú ý phi tuyến**.

Ghép ba nguồn độc lập lại — bảng research của nhóm, tài liệu CBT, và
nghiên cứu 2026 — ra một luận điểm duy nhất:

> Phần lớn app ADHD cố sửa khả năng **tự điều hoà** của người dùng bằng
> cách đưa thêm thông tin: bài học, lời nhắc, đồng hồ.
>
> Nhưng tự điều hoà chính là thứ đang không có sẵn, và thông tin không
> tạo ra nó.
>
> **Thứ hiệu quả là đồng điều hoà — sự điều hoà mượn từ bên ngoài.**

**Hệ quả cho thứ tự ưu tiên.** Ở v1 tôi xếp body double là tính năng thứ
hai. Sai. Nó là **cơ chế trung tâm**; đồng hồ và lời nhắc là tuyến sau.

| | v1 | v2 |
|---|---|---|
| Trung tâm | Neo thời gian + nhắc | **Đồng điều hoà (body double)** |
| Tuyến sau | Body double | Neo thời gian, nhắc, phản hồi bước |

Và nó cho nhóm một câu trả lời sắc trước giám khảo, có số liệu đỡ:

> *"829 app đã được sàng lọc, chỉ 17 đạt chuẩn. Phần lớn làm giáo dục và
> nhắc nhở. Một thử nghiệm ngẫu nhiên 73 người trong 3 tháng cho thấy
> nhắc nhở không cải thiện kết quả. Chúng tôi không làm cái thứ 830 —
> chúng tôi làm cái mà bằng chứng nói là có tác dụng: đồng điều hoà."*

---

## §3. Ba tính năng chính

### 3.1. Mù thời gian — neo vào đồng hồ, và HỌC từ người dùng

**Cái đã có và giữ được.** `wayfinding/adhd/timeblind.py` (350 dòng) đã
có phần khó nhất:

- Neo vào giờ thật thay vì nói khoảng thời gian trôi nổi
- Công thức đệm an toàn hai thành phần (tỷ lệ + hằng số khởi động)
- Bốn mức gấp, mỗi mức một giọng, **mọi câu đều kết thúc bằng việc phải làm**
- Mốc nhắc thưa dần về cuối, mỗi mốc chỉ báo một lần

**Cái phải thay.** Hiện `phut_di` lấy từ `uoc_phut(route)` — một lộ trình
điều hướng. Bỏ điều hướng thì mất nguồn số liệu này.

**Thay bằng gì — đây là chỗ Flowy khác các app khác.**

Không hỏi người dùng "việc này mất bao lâu" rồi tin lời họ. **Ước lượng
sai thời lượng chính là triệu chứng cần chữa** — hỏi rồi tin là xây trên
đúng chỗ đang gãy.

Thay vào đó, ba giai đoạn:

```
lần 1   Người dùng ước. App GHI LẠI, và đo thời gian thật.
lần 2   App nói: "Lần trước bạn ước 20 phút, thực tế 35 phút."
        -> chính câu này là can thiệp, không phải cái đồng hồ
lần 3+  App tự dùng số đo thật, người dùng chỉ xác nhận.
```

Câu ở lần 2 làm đúng thứ mà một cái đồng hồ đếm ngược không làm được:
nó **huấn luyện cảm nhận thời gian** bằng chính dữ liệu của người dùng.
Và nó là "cơ chế học" mà §2.2 nói các app hiện có đang thiếu.

Kiến trúc: một `SoThoiLuong` (sổ thời lượng) ghi `{tên việc → danh sách
lần đo}`, trả về ước lượng theo trung vị các lần gần nhất. Trung vị chứ
không phải trung bình: một lần bị gián đoạn bất thường không được kéo
lệch mọi lần sau.

**Đồng hồ trực quan** đã có `TimerTronView.kt` — đĩa màu thu nhỏ dần, số
chỉ là phụ. Giữ nguyên, chỉ cần nối nguồn dữ liệu mới.

### 3.2. Sao nhãng — khôi phục mạch, và body double không cần hẹn

**Cái đã có và giữ được.** `wayfinding/adhd/mach.py` (177 dòng) giải đúng
nửa sau của vấn đề: người dùng dừng quá 90 giây rồi quay lại, câu đầu
tiên phải **dựng lại ngữ cảnh** — đang làm gì, để làm gì, và việc ngay
trước mắt — chứ không phải nói tiếp như chưa có gì xảy ra.

Cơ chế này chuyển thẳng từ bối cảnh đi lại sang bối cảnh làm việc: đổi
"đang đi tới phòng 6.04" thành "đang làm bài tập chương 3", đổi "còn 2
chặng" thành "còn 2 bước". Logic phát hiện đứt mạch giữ nguyên.

**Cái phải làm mới: body double.**

Theo §2.3, body double bằng AI có hiệu quả đo được, và theo §2.2, các
công cụ hiện có hỏng vì phải đặt lịch và ghép cặp. Nên bản của Flowy:

- **Không đặt lịch, không ghép cặp.** Bấm một nút là có mặt ngay.
- **Hiện diện chứ không giám sát.** Một nhân vật tĩnh trên màn hình, và
  vài lần lên tiếng thưa thớt — không đếm giờ tập trung, không chấm
  điểm, không báo cáo.
- **Không bao giờ có trạng thái tiêu cực.** Đây là ràng buộc đã hiện
  thực trong `dongvien.py` và phải giữ: ADHD thường đi kèm nhạy cảm với
  thất bại, nên một nhân vật tỏ ra thất vọng sẽ làm người dùng tránh mở
  app — lúc đó mọi tính năng khác thành vô dụng.

`BanDongHanhView.kt` đã có sẵn khuôn mặt bốn trạng thái, ba tích cực một
trung tính, vẽ bằng `Canvas`. Dùng lại được ngay.

### 3.3. Tê liệt trước nhiệm vụ — ý định thực thi và bước nhỏ

**Cái đã có và giữ được.** `wayfinding/adhd/dongvien.py` (220 dòng) có
đúng cơ chế cần: mỗi bước nhỏ hoàn thành thì **rung nhẹ + âm ngắn**,
không phải câu nói dài. Chỉ cần đổi khái niệm "chặng đường" thành "bước
việc" — cấu trúc dữ liệu và logic chống lặp giữ nguyên.

**Cái phải làm mới: ý định thực thi (implementation intentions).**

Tài liệu CBT cho ADHD nêu công thức: ý định thực thi phải nói rõ **chính
xác khi nào và ở đâu** việc sẽ diễn ra. Ví dụ trong tài liệu:

> *"Sau bữa tối thứ Ba, tôi sẽ dành 15 phút hoàn thành bản ghi suy nghĩ
> tại bàn bếp."*

Ba thành phần bắt buộc: **khi nào + ở đâu + việc gì**. Thiếu một là quay
về một ý định mơ hồ, và ý định mơ hồ chính là thứ không khởi động được.

Nên khi người dùng thêm một việc, app không hỏi "việc gì?" mà hỏi ba ô,
và **không cho lưu nếu thiếu ô nào**. Ràng buộc đó nghe phiền nhưng nó
chính là can thiệp — nó buộc việc mơ hồ thành việc cụ thể trước khi nó
kịp thành nguồn tê liệt.

Cộng thêm: **chia nhỏ bước đầu tiên tới mức buồn cười.** Bước đầu không
phải "viết mở bài" mà "mở tệp lên". Cơ chế phản hồi ở `dongvien.py` khen
ngay bước đó — và đó là lúc cần khen nhất, vì vượt qua được bước đầu là
phần khó nhất của tê liệt.

---

## §4. Ba nhóm chức năng liên quan y tế — và cách không thành thiết bị y tế

Nhóm yêu cầu lấy **cả ba**. Đây là phần cần cẩn thận nhất, nên tôi tra
văn bản thật thay vì đoán.

### 4.1. Ranh giới do FDA vạch ra

FDA ban hành bản sửa đổi **"General Wellness: Policy for Low Risk
Devices"** ngày **06/01/2026**, thay bản 2019. FDA **không có ý định
quản lý** sản phẩm wellness rủi ro thấp như thiết bị y tế, nếu sản phẩm
chỉ nhắm mục đích wellness chung và rủi ro thấp.

Nhưng hướng dẫn cũng nêu rõ những thứ **làm sản phẩm rơi vào diện thiết
bị y tế**:

| Rơi vào diện quản lý | Ghi chú |
|---|---|
| Nhắc tới **tên bệnh cụ thể** | **"ADHD" được nêu làm ví dụ** |
| Câu chẩn đoán ("bất thường", "bệnh lý") | |
| Hướng dẫn điều trị, "ngưỡng lâm sàng" | |
| Theo dõi hoặc cảnh báo liên tục **để quản lý bệnh** | |
| **Nhắc thuốc hoặc theo dõi triệu chứng gắn với chẩn đoán** | Đúng hai trong ba nhóm nhóm hỏi |
| Thay thế thiết bị đã được FDA duyệt | |

Ngược lại, được chấp nhận: nhắc người dùng đi gặp bác sĩ khi số đo ra
ngoài ngưỡng thường **mà không nêu tên bệnh nào**, và dùng ngôn ngữ
không bệnh tật kiểu "tình trạng sức khoẻ chung".

**Điều này có ý nghĩa gì cho Flowy.** Chữ "ADHD" trong *tuyên bố về mục
đích sử dụng* là thứ đắt nhất. Nói về ADHD trong bài thuyết trình, trong
phần nghiên cứu, trong lý do làm sản phẩm — không sao. Viết trên cửa hàng
ứng dụng rằng app này *dành cho người ADHD* để *quản lý triệu chứng ADHD*
— đó là lúc nó thành thiết bị y tế.

### 4.2. Phía Việt Nam: luật mới, không phải nghị định cũ

**Nghị định 13/2023/NĐ-CP đã hết hiệu lực từ 01/01/2026.** Hiện áp dụng
**Luật Bảo vệ dữ liệu cá nhân 2025** (Quốc hội thông qua 26/06/2025, hiệu
lực 01/01/2026) cùng **Nghị định 356/2025/NĐ-CP**.

Điểm phải nhớ: **dữ liệu sức khoẻ là dữ liệu cá nhân nhạy cảm**, đòi hỏi
mức bảo vệ và sự đồng ý cao hơn dữ liệu thường.

> Nếu bài thuyết trình trích Nghị định 13/2023, giám khảo biết luật sẽ
> thấy ngay là trích văn bản đã hết hiệu lực. Trích đúng Luật 2025 thì
> ngược lại — nó cho thấy nhóm có tra cứu thật.

### 4.3. Thiết kế ba nhóm để nằm ngoài diện thiết bị y tế

Nguyên tắc chung, áp cho cả ba: **app cung cấp NĂNG LỰC, người dùng
quyết định DÙNG VÀO VIỆC GÌ.** App không biết, không hỏi, không suy diễn
về chẩn đoán.

#### (a) Nhắc thuốc → "lời nhắc theo giờ do người dùng tự đặt tên"

Rủi ro cao nhất trong ba nhóm, nhưng gỡ được bằng cách đổi chỗ quyết
định:

| Không làm | Làm |
|---|---|
| Danh mục thuốc, tên hoạt chất | Ô nhập tự do, người dùng gõ gì cũng được |
| Tính liều, nhắc theo phác đồ | Chỉ có giờ và lặp lại |
| Đếm "tỷ lệ tuân thủ" | Không chấm điểm, không thống kê tuân thủ |
| Cảnh báo bỏ liều | Không cảnh báo gì |

Kết quả: một cơ chế **nhắc việc theo giờ** hoàn toàn chung. Người dùng
đặt tên "uống thuốc sáng" là việc của họ; app không biết đó là thuốc.

Lưu ý thêm: thuốc điều trị ADHD ở Việt Nam thuộc nhóm **kiểm soát đặc
biệt**, nên mọi tính năng chạm vào tên thuốc hay liều đều kéo thêm một
tầng quy định nữa. Càng nên tránh.

#### (b) Tự theo dõi triệu chứng / cảm xúc → "nhật ký của người dùng, app không diễn giải"

Ranh giới nằm ở chữ **diễn giải**:

| Không làm | Làm |
|---|---|
| Thang đo lâm sàng (ASRS, DIVA...) | Ghi chú tự do, và tối đa một thang cảm xúc đơn giản không tên bệnh |
| Chấm điểm, xếp mức độ | Chỉ hiển thị lại đúng cái người dùng đã ghi |
| "Hôm nay triệu chứng của bạn nặng hơn" | Không kết luận gì |
| Tự gửi cho bác sĩ | **Người dùng tự xuất tệp** và tự mang đi |

Chi tiết cuối quan trọng hơn vẻ ngoài: **xuất tệp do người dùng chủ
động** giữ dữ liệu trong tay họ, tránh luôn phần truyền dữ liệu sức khoẻ
cho bên thứ ba — vốn là chỗ nặng nhất của Luật 2025.

Đây cũng là cách nhóm chức năng thứ ba trong research ("giao tiếp với
điều trị") được đáp ứng mà không phải xây kênh y tế nào.

#### (c) Giáo dục tâm lý + kỹ năng CBT → "kỹ năng tự quản lý, nhúng vào lúc dùng"

Rủi ro thấp nhất, và cũng là nhóm **hữu ích nhất** — vì các thành phần
CBT cho ADHD trùng gần hết với ba tính năng chính.

Các thành phần CBT cho ADHD người lớn gồm: giáo dục tâm lý; huấn luyện
tổ chức, lập kế hoạch và quản lý thời gian; kỹ năng giải quyết vấn đề;
kỹ thuật giảm sao nhãng và tăng khả năng tập trung; và tái cấu trúc nhận
thức quanh những tình huống gây căng thẳng.

Đối chiếu với §3:

| Thành phần CBT | Đã nằm ở tính năng nào |
|---|---|
| Quản lý thời gian | §3.1 mù thời gian |
| Giảm sao nhãng, tăng tập trung | §3.2 body double + khôi phục mạch |
| Tổ chức, lập kế hoạch | §3.3 ý định thực thi + chia bước |
| Tái cấu trúc nhận thức | Câu nói lúc tê liệt — xem dưới |
| Giáo dục tâm lý | **Không làm thành bài học** — xem §2.1 |

**Cách nhúng, không làm khoá học.** Theo §2.1, bài giảng không giải
quyết vấn đề thực thi. Nên kỹ năng CBT xuất hiện **dưới dạng câu hỏi
đúng lúc**, không phải chương mục:

- Lúc thêm việc → ba ô *khi nào / ở đâu / việc gì* (ý định thực thi)
- Lúc kẹt quá lâu ở một bước → *"Bước nhỏ nhất bạn làm được ngay bây giờ
  là gì?"* (chia nhỏ + tái cấu trúc)
- Lúc quay lại sau gián đoạn → câu dựng lại ngữ cảnh (đã có ở `mach.py`)

Mỗi câu là một kỹ thuật CBT, nhưng người dùng gặp nó **lúc đang cần**
chứ không phải lúc học.

### 4.4. Bốn quy tắc viết chữ, áp cho toàn bộ app

Ranh giới ở §4.1 nằm ở **câu chữ** nhiều hơn ở mã nguồn. Nên bốn quy tắc
này phải thành test canh gác, giống test dấu tiếng Việt đã có:

1. **Không chuỗi nào trong app chứa tên bệnh** — "ADHD", "rối loạn",
   "tăng động", "giảm chú ý". Nói về nhu cầu, không nói về chẩn đoán.
2. **Không câu nào khẳng định về tình trạng người dùng** — không "hôm
   nay bạn mất tập trung hơn".
3. **Không con số nào được gọi là điểm số hay mức độ.**
4. **Không câu nào hứa hẹn hiệu quả điều trị.**

---

## §5. Kiểm kê: giữ gì, bỏ gì

Sau khi bỏ điều hướng.

### 5.1. Giữ và dùng lại gần như nguyên vẹn

| Module | Dòng | Dùng vào đâu |
|---|---|---|
| `adhd/timeblind.py` | 350 | §3.1 — chỉ thay nguồn `phut_di` |
| `adhd/mach.py` | 177 | §3.2 — đổi "chặng" thành "bước" |
| `adhd/dongvien.py` | 220 | §3.3 — đổi "chặng" thành "bước" |
| `adhd/meety.py` | 324 | Tóm tắt biên bản họp, giữ nguyên |
| `loi_chung/announce.py` | 123 | Chọn câu nói + chống lặp từng kênh |
| `loi_chung/speech.py` | 246 | Giọng nói và rung |
| `loi_chung/power.py` | 258 | Điều tiết nhịp — tiết kiệm pin |
| `loi_chung/health.py` | 172 | Theo dõi sức khoẻ hệ thống |
| `loi_chung/metrics.py` | 230 | Chỉ tiêu nghiệm thu — **phải đổi bộ chỉ tiêu** |
| `loi_chung/session.py` | 239 | Ghi lại phiên để phát lại khi kiểm thử |
| `frontend/TimerTronView.kt` | | §3.1 đồng hồ trực quan |
| `frontend/BanDongHanhView.kt` | | §3.2 body double |

### 5.2. Bỏ — chỉ phục vụ điều hướng

`loi_chung/`: `anchors`, `arcore`, `depth`, `floormap`, `floors`,
`geometry`, `guidance`, `localizer`, `objects`, `routing`, `signtext`,
`vio`, `profile`

`adhd/`: `places` (đánh dấu địa điểm — cần định vị), `preview` (xem
trước lộ trình)

Android: `MainActivity` phần ARCore, `DepthSampler`, `ObjectVision`,
`ArMath`, `BarometerReader`, `NfcLauncher`

Kèm theo: `config/map_floor3.json`, toàn bộ `tools/` liên quan bản đồ,
và `run_bridge.py` phải viết lại vì nó là runner của hệ điều hướng.

### 5.3. Cần quyết định riêng

| Thứ | Vấn đề |
|---|---|
| `loi_chung/bridge.py` | Cầu nối laptop. Bản chính chạy iOS thì không cần — nhưng demo Android có thể vẫn dùng. Xem §7. |
| `phan_khiem_thi/` | Bản sao phần khiếm thị. Bản bảo trì nằm ở repo OpticGuard nên ở đây là dư — nhưng nhóm đã bảo giữ. |
| `metrics.py` | Chín chỉ tiêu hiện tại là của hệ dẫn đường (tỷ lệ tới đích, số lần đi lạc...). Phải thay bằng bộ chỉ tiêu của app quản lý thời gian. |

---

## §6. Thứ tự làm

| # | Việc | Vì sao thứ tự này |
|---|---|---|
| 1 | Dọn: bỏ 15 module điều hướng, viết lại runner | Làm trước để không sửa hai lần |
| 2 | `SoThoiLuong` — sổ thời lượng học từ người dùng | Là đầu vào của `timeblind`, chặn mọi thứ sau |
| 3 | Nối lại `timeblind` vào nguồn mới | Tính năng có bằng chứng rõ nhất |
| 4 | Đổi "chặng" → "bước" ở `mach` và `dongvien` | Rẻ, dùng lại code đã có test |
| 5 | Ý định thực thi: ba ô bắt buộc | Can thiệp cho tê liệt |
| 6 | Body double: nút bật, nhân vật, câu thưa thớt | Bằng chứng mạnh nhất, nhưng cần UI — **xong**, xem nhật ký code §2.7 |
| 7 | Ba nhóm y tế theo khuôn §4.3 | Sau khi lõi đã chạy — **xong**, xem nhật ký code §2.6 |
| 8 | Bốn test canh gác câu chữ ở §4.4 | Trước khi nộp |

---

## §7. Các quyết định đã chốt

### 7.1. Bảng research — đã nhận, đã đối chiếu

Bảng `Elicit — Nhu cầu ADHD đối với ứng dụng di động và dữ liệu Việt Nam`.
Kết quả đối chiếu với phần tôi tự tra:

| Chỗ | Trạng thái |
|---|---|
| ADHD là vấn đề thực thi (§2.1) | **Trùng** — bảng cũng chỉ ra thị trường bão hoà app giáo dục tâm lý |
| App hiện có đứng yên (§2.2) | **Trùng** |
| Body doubling có bằng chứng (§2.3) | Bảng **không có** mục này — đây là phần tôi bổ sung |
| Nhắc nhở không đủ (§2.4) | Bảng **có, tôi không có** — và nó lật thiết kế v1 |
| Đồng điều hoà (§2.5) | Cả hai đều không có — tôi tìm thêm sau khi đọc bảng |

Bảng bổ sung được thứ quan trọng nhất: **bằng chứng phủ định**. Nó cho
biết cái gì đã thử và **không** hiệu quả, mà đó là loại bằng chứng hiếm
và đắt hơn bằng chứng khẳng định.

Ba app trong bảng đáng đối chiếu khi thuyết trình: **Tiimo** (lịch trực
quan, bộ đếm ngược, checklist AI), **Structured** (lịch trực quan,
routine), **Tempus** (chuyển lời nói thành timeline trực quan). Cả ba
đều mạnh ở *hiển thị thời gian*. **Không cái nào làm đồng điều hoà** —
đó là chỗ trống của Flowy.

### 7.2. Cầu nối laptop — GIỮ

Đã chốt. Hệ quả cần chuẩn bị trước:

Giám khảo gần như chắc chắn hỏi *"sao phải có laptop"*. Câu trả lời
không nên là lời bào chữa mà nên là một lựa chọn kỹ thuật có lý do:

> *"Laptop là môi trường phát triển, không phải một phần sản phẩm. Lõi
> quyết định viết bằng Python để chúng tôi sửa thuật toán và chạy lại
> bộ test trong vài giây thay vì build lại app. Bản iOS chạy cùng lõi
> đó, không cần laptop."*

Và phải kèm một ràng buộc kỹ thuật — xem 7.3.

### 7.3. Dữ liệu lưu ở đâu — ĐỀ XUẤT

**Lưu hoàn toàn trên máy người dùng, và người dùng tự xuất tệp khi muốn
mang đi.** Không máy chủ, không tài khoản, không đồng bộ.

Bốn lý do, theo thứ tự quan trọng:

**(a) Pháp lý.** Luật Bảo vệ dữ liệu cá nhân 2025 coi dữ liệu sức khoẻ
là dữ liệu nhạy cảm. Phần nặng nhất của luật rơi vào **chuyển dữ liệu
cho bên thứ ba** và **chuyển ra nước ngoài**. Không có máy chủ thì
không có hai thứ đó — cả một chương nghĩa vụ biến mất.

**(b) Quy định thiết bị y tế.** §4.1 liệt kê *"theo dõi hoặc cảnh báo
liên tục để quản lý bệnh"* là thứ làm sản phẩm rơi vào diện quản lý. Một
máy chủ giữ nhật ký triệu chứng trông rất giống hệ thống theo dõi. Không
có máy chủ thì lập luận gọn hơn nhiều.

**(c) Đúng nhóm người dùng.** Phần lớn nội dung là ghi chú riêng tư về
lúc mình kẹt, mình quên, mình trễ. Nói được *"dữ liệu của bạn không rời
khỏi máy"* là một lời hứa mạnh, và nó miễn phí nếu thiết kế từ đầu.

**(d) Rẻ nhất để làm và để demo.** Không backend, không auth, không
downtime giữa buổi thi.

**Ràng buộc kèm theo cho cầu nối laptop (7.2).**

Vì cầu nối vẫn còn, phải vạch rõ nó được mang gì:

| Qua cầu nối | Không bao giờ qua cầu nối |
|---|---|
| Trạng thái tạm: đang chạy việc gì, còn bao nhiêu phút | Nhật ký cảm xúc, ghi chú triệu chứng |
| Lệnh hiển thị, câu nói, mã rung | Tên các lời nhắc người dùng tự đặt |
| | Sổ thời lượng (lịch sử làm việc) |

Nghĩa là laptop **không ghi gì xuống đĩa**. Nó là bộ não tạm thời, không
phải kho lưu trữ. Điều này nên thành một test canh gác: kiểm rằng
`bridge.py` không có lời gọi ghi tệp nào cho dữ liệu cá nhân.

**Mất gì.** Không đồng bộ giữa iOS và Android, không sao lưu tự động.
Với một app cá nhân dùng hằng ngày thì mất mát này thật nhưng chấp nhận
được — và tính năng **xuất tệp** ở §4.3(b) bù lại một phần: người dùng
tự sao lưu được.

**Mã hoá khi nằm trên máy.** iOS dùng Data Protection của hệ điều hành;
Android dùng Android Keystore (không dùng `EncryptedSharedPreferences`
vì nó thuộc androidx, mà dự án cố ý không có androidx).

### 7.4. Nhân vật đồng hành — GIỮ, và đây là bản mô tả cho hoạ sĩ

Đã chốt giữ. Vì §2.5 nâng nó thành **cơ chế trung tâm** chứ không còn là
tính năng phụ, nhân vật này giờ là thứ quan trọng nhất trên màn hình.

Bản mô tả đầy đủ cho người vẽ nằm ở tài liệu riêng:
**[`docs/luu-tru/NHAN_VAT_BRIEF.md`](./luu-tru/NHAN_VAT_BRIEF.md)** (nhân vật đã bỏ 16/09, nguyên tắc §2.4 giữ)

**Bổ sung của nhóm (đã đưa vào bản mô tả):** nhân vật **chỉ phản hồi khi
được chạm**; còn lại nó tự làm việc của nó.

Bổ sung này làm nhân vật đúng với cơ chế hơn — body doubling thật là vậy,
người ngồi cạnh bạn ở thư viện không nhìn bạn, họ bận việc của họ. Và
"chỉ khi được chạm" biến một ràng buộc thành tính năng: **app không cằn
nhằn, về mặt cấu trúc chứ không phải thiện chí.**

Nó cũng đặt câu hỏi can thiệp vào đúng chỗ. Người dùng chạm vào nhân vật
khi họ đang kẹt — nên đó là thời điểm duy nhất thích hợp để hỏi *"bước
nhỏ nhất bạn làm được ngay bây giờ là gì?"*.

Hai điều chỉnh tôi phải làm kèm, vì bổ sung này đụng ràng buộc cũ:

1. **Đổi tư thế phải rời rạc và thưa**, không phải hoạt hình chạy liên
   tục — vì chuyển động lặp trong tầm nhìn ngoại vi là nguồn phân tâm.
   Ngẫu nhiên 3–8 phút, và **giãn ra 8–15 phút khi người dùng đang tập
   trung**: đồng điều hoà nhìn thấy được.
2. **Nhân vật phải kém thú vị hơn công việc của người dùng.** Mục tiêu
   không phải giữ mắt người dùng ở lại app mà giữ họ ở lại công việc.
   Kèm tiêu chí thất bại rõ ràng ở §2.5 của bản mô tả.

Tóm tắt ba quyết định lớn khác trong đó:

1. **Ngồi BÊN CẠNH, không nhìn thẳng vào người dùng.** Nhìn thẳng đọc ra
   là bị giám sát; ngồi bên cạnh đọc ra là được đi cùng. Đồng điều hoà
   cần vế thứ hai.
2. **Không có thanh máu, không có nhu cầu được chăm.** Mọi cơ chế kiểu
   thú ảo tạo ra nghĩa vụ, và nghĩa vụ không làm tròn sinh cảm giác tội
   lỗi — đúng cái bẫy nhạy cảm với thất bại cần tránh.
3. **Không có trạng thái buồn hay thất vọng.** Ràng buộc này đã hiện
   thực trong `dongvien.py` và có ba bài test khoá.

---

## Nguồn

- FDA, *General Wellness: Policy for Low Risk Devices* (bản sửa đổi
  06/01/2026) — [tóm tắt của Troutman Pepper Locke](https://www.troutman.com/insights/fdas-2026-guidance-on-general-wellness-devices-policy-for-low-risk-devices/)
- [Luật Bảo vệ dữ liệu cá nhân, hiệu lực 01/01/2026 — Báo Chính phủ](https://baochinhphu.vn/luat-bao-ve-du-lieu-ca-nhan-chinh-thuc-co-hieu-luc-tu-ngay-mai-1-1-2026-102251231155609721.htm)
- [Nghị định 13/2023/NĐ-CP (đã hết hiệu lực) — Thư viện pháp luật](https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin/Nghi-dinh-13-2023-ND-CP-bao-ve-du-lieu-ca-nhan-465185.aspx)
- Ramsay, *"Turning Intentions Into Actions": CBT for Adult ADHD Focused on Implementation* — [ResearchGate](https://www.researchgate.net/publication/283239518_Turning_Intentions_Into_Actions_CBT_for_Adult_ADHD_Focused_on_Implementation)
- [Cognitive Behavioral Therapy for adult ADHD — Society of Clinical Psychology](https://societyofclinicalpsychology.org/psychological-treatments-archive/cognitive-behavioral-therapy-for-adult-adhd/)
- [Toward Neurodivergent-Aware Productivity: A Systems and AI-Based Human-in-the-Loop Framework for ADHD-Affected Professionals (arXiv)](https://arxiv.org/pdf/2507.06864)
- [You Are Not Alone: Designing Body Doubling for ADHD in Virtual Reality (arXiv)](https://arxiv.org/pdf/2509.12153)
- [Body Doubling: The ADHD Productivity Strategy That Actually Works — Simply Psychology](https://www.simplypsychology.com/articles/body-doubling-adhd)
- ["Not Just Me and My To-Do List": Understanding Challenges of Task Management for Adults with ADHD and the Need for AI-Augmented Social Scaffolds (arXiv 2026)](https://arxiv.org/html/2603.17258v2)
- Bảng research của nhóm: `Elicit — Nhu cầu ADHD đối với ứng dụng di động và dữ liệu Việt Nam`, trong đó hai nguồn nặng ký nhất là Carvalho et al. 2023 (thử nghiệm FOCUS ADHD) và Jin et al. 2025 (tổng quan 829 app)
