# Câu hỏi giám khảo có thể hỏi — và câu trả lời

Hackathon ADC RMIT 2026 · nhánh **Neurodivergence** · Stage 5: *On the job*

Cập nhật 21/09/2026.

---

## Cách dùng file này

Đừng học thuộc. Đọc một lượt để **biết mình đã có câu trả lời**, rồi trả lời bằng lời của mình.

Ba nguyên tắc khi đứng trước hội đồng:

1. **Câu nào không biết thì nói không biết**, rồi nói mình sẽ làm gì để biết. Giám khảo mảng accessibility rất nhanh nhận ra một câu bịa, và một câu bịa làm hỏng cả phần trình bày.
2. **Dẫn số liệu và dẫn chỗ trong code.** *"Chúng em có 209 bài test Kotlin"* mạnh hơn *"chúng em test rất kỹ"*.
3. **Giới hạn thì nói thẳng.** Xem mục cuối — nói trước khi bị hỏi thì đó là sự trung thực; nói sau khi bị hỏi thì đó là bào chữa.

---

## A. Về đề bài và vấn đề

### A1. Vì sao chọn Stage 5, và vấn đề cụ thể các em giải là gì?

Đề bài nói rào cản là hệ thống hỗ trợ **reactive và disclosure-dependent** — chỉ khởi động sau khi người lao động tự khai báo, mà nhiều người không dám khai báo.

Flowy tấn công một mảnh cụ thể của nó: **khoảnh khắc tê liệt trước một đầu việc mơ hồ (task paralysis)**. Đây là lúc người lao động đa dạng thần kinh cần giúp nhất, và cũng là lúc **khó xin giúp nhất** — vì xin giúp có nghĩa là thừa nhận mình chưa bắt đầu được một việc mà người khác thấy đơn giản.

Flowy đưa một đường hỗ trợ **không cần xin phép ai**, nằm ngay trong công cụ họ dùng hằng ngày.

### A2. Vì sao không làm một công cụ để nhân viên báo cáo khó khăn cho quản lý?

Chúng em đã cân nhắc và **bỏ**. Hai lý do thực tế:

- App không có cách nào biết ai là quản lý của người dùng.
- Không có kênh gửi nào mà vừa ẩn danh vừa đến đúng người.

Một tính năng nghe hay nhưng không chạy được trong thực tế thì tệ hơn là không có — nhất là với một nhóm người dùng đã quen bị hứa hẹn rồi thất vọng.

### A3. Tại sao ADHD chứ không phải cả bốn nhóm khuyết tật?

Vì làm tử tế cho một nhóm thì hơn làm hời hợt cho bốn. Tuy nhiên nhiều quyết định trong app có lợi cho các nhóm khác: cỡ chữ điều chỉnh được, font Andika cho người khó đọc, tương phản WCAG AAA, TalkBack ở mọi màn hình.

---

## B. Về thiết kế cho người đa dạng thần kinh

### B1. Điều gì trong app này chỉ có vì người dùng là ADHD?

Ba thứ cụ thể:

**Không bao giờ phản hồi tiêu cực.** Không có "tỉ lệ hoàn thành", việc chưa xong không bị tô đỏ. Đỏ **chỉ** dùng cho nút Xóa. Có bài test canh gác chữ để không ai vô tình thêm câu ra lệnh vào app.

**Thời lượng hiện một đơn vị.** Dưới ba tiếng thì ghi "75 phút", không ghi "1 giờ 15 phút". Vì so "1 giờ 15 phút" với "50 phút" phải quy đổi trong đầu mới biết cái nào dài hơn — đúng chỗ yếu của người mù thời gian.

**App không chủ động bắt chuyện.** Chỉ nói khi được chạm vào.

### B2. Làm sao đảm bảo AI không làm người dùng tê liệt nặng hơn?

Đây là rủi ro lớn nhất của tính năng AI, và bọn em chặn bằng **ba lớp**, không chỉ bằng prompt:

| Lớp | Chặn cái gì |
| --- | --- |
| Prompt giới hạn 3–5 bước | Đề nghị, nhưng mô hình có thể không nghe |
| Parser **cắt cứng** ở bước thứ 5 | Đây mới là thứ chặn thật |
| Màn xem trước chỉ tô đậm bước 1 | Bốn bước sau chỉ để biết đường còn bao xa |

Trả về 12 bước là đổi **một** việc không bắt đầu được thành **mười hai** việc không bắt đầu được — nhân lên, không phải cải thiện. Có một bài test riêng cho đúng ca này.

### B3. Vì sao người dùng sửa và xóa được từng bước AI đưa ra?

Vì đề bài nói về công việc **bị giao rập khuôn, không đồng điệu với phong cách nhận thức**. Một AI áp đặt cách chia việc của nó là **lặp lại chính cái rào cản đó**, chỉ khác người ra lệnh.

Xóa hết các bước vẫn duyệt được. Đây không phải tính năng phụ — nó là khác biệt giữa một công cụ hỗ trợ và một cấp trên nữa.

### B4. Nút chính ở màn xem trước là "Bắt đầu bước 1" chứ không phải "Lưu" — vì sao?

Vì *"để tôi nhờ AI chia nhỏ đã"* là một việc **có cảm giác năng suất, tốn hai mươi giây, và không phải làm cái việc thật**. Làm ba lần là hết buổi sáng.

Bắt luồng phân rã kết thúc bằng **hành động** thì nó không thành một cách trì hoãn mới được. "Chỉ lưu" vẫn có, nhưng là một dòng chữ nhỏ bên dưới.

### B5. Trạng thái chờ khi gọi AI thiết kế thế nào?

Ba dòng xương đúng hình dạng kết quả sắp hiện ra, **không phải vòng quay**. Vòng quay vô định không cho biết còn bao lâu — đúng chỗ yếu của người mù thời gian. Dòng xương thì vừa nói "đang tải", vừa cho biết kết quả sẽ trông thế nào, nên lúc hiện ra thật không có cú nhảy bố cục.

Trần 8 giây. Quá thì chuyển sang đường tự chia thủ công.

---

## C. Về kỹ thuật

### C1. Khóa Gemini API các em để ở đâu?

**Không ở trong mã nguồn và không lên GitHub.** Nó đọc từ `local.properties` — tệp đã nằm trong `.gitignore` — qua `BuildConfig`.

Gắn khóa vào APK thì **bất kỳ ai cũng lấy ra được**: giải nén tệp apk và đọc chuỗi, không cần kỹ năng gì. Mã hóa cũng vô nghĩa vì cả khóa lẫn mã giải đều nằm trong cùng gói cài đặt.

Không có khóa thì app dùng bản mẫu. Đường đúng về lâu dài là **proxy qua máy chủ**: khóa nằm trên máy chủ, app gọi qua đó. Kiến trúc đã sẵn sàng cho việc đó — chỉ cần thêm một lớp hiện thực của `PhanRaProvider`.

### C2. Demo hôm nay chạy AI thật hay bản mẫu?

*(Trả lời trung thực theo thực tế lúc demo.)*

Nếu chạy bản mẫu: bản mẫu đi qua **đúng đường mã thật**, kể cả bộ đọc JSON và bộ cắt 5 bước. Toàn bộ trải nghiệm các thầy cô thấy là thật — chỉ nguồn sinh ra các bước là khác. Chọn vậy để buổi demo không phụ thuộc WiFi hội trường và không lộ khóa cho ai nhìn màn hình.

### C3. Dữ liệu người dùng đi đâu?

| Dữ liệu | Rời máy? |
| --- | --- |
| Lịch, lời nhắc, nhật ký, sổ thời lượng | **Không bao giờ** |
| Tài khoản đăng nhập | Có — mật khẩu băm PBKDF2-HMAC-SHA256, không bao giờ lưu dạng thường |
| Tên công việc khi gọi phân rã | Có, chỉ tên việc đó |

`bridge.py` có một **bảng cấm** liệt kê rõ dữ liệu nào không bao giờ được lên đường truyền — nhật ký cảm xúc, ghi chú triệu chứng, tên lời nhắc tự đặt, sổ thời lượng. `SoNhac` và `SoNhatKy` không được phép chạm vào lớp truyền tin.

### C4. Các em test thế nào?

| Bộ | Số bài |
| --- | --- |
| Python — lõi quyết định | 442 |
| Kotlin — Android | 209 |
| Meety — xử lý biên bản | 426 |

Cả ba chạy tự động trên GitHub Actions mỗi lần đẩy code, và job Android **xuất APK tải về được**.

Điều đáng nói hơn con số: một phần các bài test là **canh gác câu chữ**, không phải canh gác logic. Ví dụ có một bài đọc thẳng `strings.xml` và chặn mọi câu ra lệnh ("bạn phải", "hãy cố") ở **cả hai ngôn ngữ**. Vì nguyên tắc "không bao giờ phản hồi tiêu cực" là thứ dễ vô tình phá nhất, và phá nó thì không có test logic nào đổ.

### C5. Vì sao không dùng Jetpack Compose?

Quyết định có ghi lại trong `docs/UIUX_QUYET_DINH.md`. Lý do chính là kiểm soát chính xác thứ tự và kích thước cho trình đọc màn hình, cộng với việc nhóm thạo View hơn — và trước ngày thi thì đó là yếu tố quyết định.

### C6. App chạy được trên iOS chưa?

Mã iOS **đã biên dịch sạch** — 47 file Swift, trên CI với Xcode 26. Nhưng **chưa từng chạy trên máy thật**, vì ký và nạp app lên iPhone bắt buộc phải có Xcode trên macOS và nhóm hiện không có máy Mac.

Nói thẳng: biên dịch được **không** có nghĩa là cài được.

---

## D. Về tác động và tính khả thi

### D1. Làm sao đo được app này có tác dụng?

Chưa đo được, và bọn em nói thẳng điều đó. **Chưa thử với người dùng ADHD thật** — đây là giới hạn lớn nhất.

Điều bọn em đã chuẩn bị là **hạ tầng để đo**: sổ thời lượng ghi lại ước lượng và thời gian thật của từng việc, nên chỉ số đầu tiên có thể đo được là **khoảng lệch giữa ước lượng và thực tế có thu hẹp lại sau vài tuần dùng hay không**. Đó là một chỉ số khách quan, không phải khảo sát cảm nhận.

### D2. Doanh nghiệp bỏ tiền ra thì được gì? ROI thế nào?

Đề bài nói đúng vấn đề: hỗ trợ sức khỏe tinh thần bị cắt vì **thiếu ROI đo được**.

Câu trả lời trung thực: bọn em **chưa có** con số ROI. Điều bọn em có là một cơ chế để tạo ra nó — nếu một tổ chức tài trợ bản Doanh nghiệp, chỉ số đo được là **số lần nhân viên dùng đường phân rã thay vì để việc trôi tới hạn**. Đó là can thiệp sớm, đúng cái "middle-ground" mà đề bài nói employers đang thiếu.

### D3. Hạn mức 3 lượt/ngày có phải là rào cản thu phí với người khuyết tật không?

Đây là câu bọn em chuẩn bị kỹ nhất, vì nó là rủi ro thật.

**Hết lượt không chặn đường.** Màn Gỡ rối bốn câu hỏi **vẫn mở bình thường** — nó không dùng AI và giải đúng vấn đề đó. AI chỉ là đường nhanh hơn, không phải đường duy nhất.

Hộp thoại hết lượt **không có nút "Nâng cấp"**. Thông tin bản Doanh nghiệp nằm trong Cài đặt, nơi người dùng tự tìm tới — không phải nơi họ vừa bị chặn.

### D4. Cái gì trong này mà một cuốn sổ giấy không làm được?

Ba thứ:

- **Neo vào giờ thật.** *"Cần xong lúc 14 giờ. Bạn cần bắt tay vào lúc 13 giờ 34."* Sổ giấy không tính hộ khoảng đệm đó.
- **Học từ chính người dùng.** *"Lần trước bạn ước 20 phút, thực tế 35 phút."*
- **Có mặt đúng lúc tê liệt.** Sổ giấy không biết bạn đã ngồi lì ở một bước 20 phút.

---

## E. Giới hạn — nói trước khi bị hỏi

Nói những điều này ra **trước** thì nó là sự trung thực. Nói sau khi bị hỏi thì nó là bào chữa.

1. **Chưa thử với người dùng ADHD thật.** Giới hạn lớn nhất, không có cách nào vòng qua bằng kỹ thuật.
2. **Bản iOS chưa chạy trên máy thật.** Biên dịch sạch trên CI, nhưng cần máy Mac để ký và nạp.
3. **Các hằng số chưa hiệu chỉnh.** Ngưỡng "bị kẹt", mốc nhắc trước — đều là giá trị tạm.
4. **Chưa có số liệu ROI.**
5. **Luồng hỏi–đáp dẫn dắt còn cần laptop** trong giai đoạn thử nghiệm. Lịch, lời nhắc, nhật ký, đồng hồ Tập trung thì không.

---

## F. Câu hỏi khó — chuẩn bị riêng

### F1. "Các em có phải là người đa dạng thần kinh không? Nếu không thì sao dám thiết kế cho họ?"

Trả lời thật. Nếu không, thì nói rõ là nhóm **dựa vào nghiên cứu nền** (xem `research/`) chứ không dựa vào phỏng đoán, và nói thẳng rằng **chưa kiểm chứng với người dùng thật là giới hạn số một** — đã ghi trong README.

Đừng tự nhận trải nghiệm mình không có.

### F2. "Tính năng AI này có gì khác ChatGPT?"

ChatGPT cũng chia nhỏ được một công việc. Ba khác biệt:

- **Nó không bao giờ trả về 12 bước.** Cắt cứng ở 5.
- **Nó kết thúc bằng một đồng hồ đang chạy**, không phải một đoạn văn để đọc.
- **Nó biết ngữ cảnh**: việc đó nằm ở đâu trong lịch, lần trước bạn ước sai bao nhiêu.

Và nó nằm **trong chính công cụ người ta đang dùng**, không phải một tab trình duyệt nữa — mà chuyển sang một tab khác chính là chỗ người ADHD mất mạch.

### F3. "Nếu AI đưa ra lời khuyên sai và người dùng làm theo thì sao?"

Flowy **không đưa lời khuyên**. Nó đề xuất các bước, và người dùng sửa, xóa, hoặc bỏ hết trước khi duyệt. Không có gì được lưu nếu chưa bấm duyệt.

Và Flowy **không phải thiết bị y tế**: không chẩn đoán, không theo dõi triệu chứng, không đưa lời khuyên điều trị. Ranh giới đó có ghi trong `docs/FLOWY_THIET_KE.md` §4, và có bài test canh gác để không ai vô tình vượt qua.

### F4. "Bảng sức khỏe nói 'những hôm ngủ nhiều hơn, bạn xong nhiều việc hơn' — đó có phải kết luận nhân quả không?"

Không, và app cố ý **không** nói như vậy. Câu chữ là một **quan sát**, không phải lời khuyên.

Bảy ngày không đủ để tính tương quan có ý nghĩa thống kê, nên app **không gọi nó là tương quan**. Nó chỉ chia hai nhóm theo trung vị số phút ngủ và so số việc xong trung bình, và **chỉ nói ra khi** có ít nhất bốn ngày đủ cả hai số **và** hai nhóm lệch từ 25% trở lên.

Và có một ngoại lệ riêng: **tuần không xong việc nào thì app tuyệt đối không nói gì** — đó là tuần người dùng đang chật vật nhất, và một nhận xét lúc đó đọc ra như một lời trách. Có mười một bài test cho phần này, phần lớn kiểm rằng nó **im**.
