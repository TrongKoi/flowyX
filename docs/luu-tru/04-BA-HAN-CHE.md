# Ba hạn chế kỹ thuật — đề xuất, **chờ Dũng duyệt**

Tài liệu bàn giao nêu rõ: với ba điểm này, muốn được **đề xuất giải pháp trước**
rồi mới triển khai. Tài liệu này giữ đúng thứ tự đó.

Với mỗi hạn chế: phân tích → các phương án → khuyến nghị → **trạng thái hiện tại
trong mã nguồn**. Phần cuối là quan trọng: một số thứ đã được cài đặt sẵn ở mức
tối thiểu vì hệ thống không chạy được nếu thiếu, và điều đó được ghi rõ chứ
không làm lén.

---

## Hạn chế 1 — Ngược sáng và thiếu sáng

### Vấn đề

Độ sâu của ARCore dựng từ chuyển động và từ tương phản ảnh. Nó yếu ở đúng những
chỗ văn phòng hay có: **tường trắng trơn, ngược sáng từ cửa sổ, sàn đá bóng,
vách kính**. Ở những chỗ đó cảm biến trả về độ tin cậy thấp, hoặc không trả về
gì.

### Nhận định quan trọng

Đây **không phải bài toán làm cho camera nhìn được**. Đó là bài toán quang học
và nó không giải được bằng phần mềm trên một cái camera phổ thông.

Đây là bài toán **biết mình đang không nhìn được, và cư xử đúng khi đó**. Bài
toán thứ hai giải được, và giải nó tốt còn ghi điểm cao hơn.

### Các phương án

| Phương án | Đánh giá |
|---|---|
| **A. Coi vùng không đọc được là CHƯA BIẾT, không bao giờ là trống** | Rẻ, đúng nguyên tắc, và là điều kiện cần cho mọi phương án khác |
| B. Dùng ước lượng ánh sáng của ARCore để giải thích cho người dùng | Rẻ, tăng độ tin cậy của người dùng vào hệ thống |
| C. Khoá phơi sáng khi phát hiện loá | Trung bình; có thể làm hỏng cả khung thay vì cứu nó |
| D. Mô hình học sâu ước lượng độ sâu đơn ảnh (MiDaS, Depth Anything) | Đắt: mô hình vài chục MB, tốn pin, và **chỉ cho độ sâu tương đối** — không ra mét. Không dùng để cảnh báo khoảng cách được |
| E. Cảm biến hồng ngoại rời | Ngoài phạm vi: đổi phần cứng, mất luôn lập luận "công nghệ hỗ trợ duy nhất không thêm kỳ thị" |

### Khuyến nghị

**A + B.** Bỏ D dù nghe hấp dẫn: mô hình đơn ảnh cho độ sâu *tương đối*, mà hệ
thống này nói *"cách một mét hai"* — một con số tương đối không đổi ra mét được
nếu không có tỷ lệ tuyệt đối, và đoán bừa tỷ lệ thì vi phạm nguyên tắc số một.

C giữ lại làm việc sau hackathon.

### Trạng thái trong mã nguồn

**Đã cài A và B ở mức đầy đủ.** Lý do làm trước khi duyệt: hệ thống *không thể
chạy an toàn* nếu thiếu — không có A thì mọi mảng tường trắng là "đường trống".

- `depth.classify_cell` xét độ tin cậy **trước** khoảng cách
- `trust.assess` dùng tỷ lệ ô không đọc được làm cảm biến ngược sáng — đo *hậu
  quả* thay vì đo *nguyên nhân*, nên bắt được cả sàn bóng và mặt kính
- `speech.mo_ta_do_tin_cay_thap` giải thích bằng lời, nói về **hệ thống** chứ
  không nói về người dùng
- Xem chạy thử: `python tools/sim.py nguoc_sang`

**Cần Dũng duyệt:** có bỏ hẳn phương án D không, hay giữ trong slide như hướng
phát triển tiếp.

---

## Hạn chế 2 — Vật cản tầm cao, KHÔNG đổi góc camera, KHÔNG mở góc nhìn

### Vấn đề

Đây là ràng buộc Dũng đặt ra: tìm hướng thứ ba ngoài hai hướng hiển nhiên.

Camera chúc xuống ~22° để nhìn mặt đất trước chân — đúng vùng mù của gậy khi
vung. Nhưng vì vậy, lúc sắp va vào một cái tủ treo tường thì cái tủ đã trôi ra
khỏi khung hình.

### Hướng thứ ba: nhớ, thay vì nhìn lại

Quan sát then chốt: **vật ngang đầu ở cách 3–7 mét thì NẰM TRONG khung hình.**
Nó chỉ trôi ra khi đã tới gần. Hệ thống **đã nhìn thấy nó rồi** — chỉ là sớm
hơn vài giây.

Nên: ghi vị trí của nó trong **không gian** (không phải trong khung hình) tại
lúc còn thấy, rồi dùng VIO — vốn đã có sẵn cho việc định vị — để biết mình đang
tiến tới gần nó.

Không đổi góc máy. Không đổi ống kính. Không thêm cảm biến. Không thêm chi phí.

### Đánh đổi, nói thẳng

| Đánh đổi | Xử lý |
|---|---|
| Vật **di chuyển** thì vị trí nhớ được sẽ sai | Bộ nhớ chỉ sống 12 giây; thứ đang nhìn thấy luôn thắng thứ đang nhớ |
| VIO trôi thì vị trí nhớ trôi theo | Trong 12 giây, sai số VIO trong nhà thường dưới 10cm — nhỏ so với ngưỡng cảnh báo 2 mét |
| Người dùng không phân biệt được "thấy" và "nhớ" | Câu nói khác nhau rõ: *"vật cản ngang đầu"* so với *"tôi thấy nó lúc nãy"* |
| Vật đã đi khỏi mà vẫn cảnh báo | Camera nhìn xuyên qua đúng chỗ đó ở đúng tầm cao thì xoá khỏi bộ nhớ ngay |

### Một phát hiện phải nêu — nó suýt làm hỏng cả tính năng này

Bộ mô phỏng phát hiện: **với góc mở dọc 50° và góc chúc 22°, mép trên khung hình
chỉ với tới +3°.** Camera không bao giờ nhìn cao hơn tầm ngực, và tính năng này
im lặng mà không báo lỗi gì.

Lời giải: **đeo máy DỌC.** Cảm biến camera nằm ngang, nên đeo dọc thì cạnh dài
của cảm biến nằm theo chiều đứng — góc mở dọc thành ~66°, mép trên với tới +11°,
đủ thấy tầm đầu ở 3–7 mét.

> Nghĩa là **cách đeo máy là một quyết định kỹ thuật**, không phải chuyện tiện
> tay. Nếu người dùng đeo ngang thì tính năng khác biệt nhất của sản phẩm biến
> mất trong im lặng. Điều này phải nằm trong hướng dẫn sử dụng.

App tự đo góc mở từ thông số quang học của máy thay vì dùng hằng số.

### Trạng thái trong mã nguồn

**Đã cài đầy đủ** — `core/navcore/memory.py`, có 8 test riêng.
Xem chạy thử: `python tools/sim.py tu_treo`

**Cần Dũng duyệt:**
1. Bộ nhớ 12 giây có hợp lý không, hay nên ngắn hơn (an toàn hơn với vật di
   chuyển, nhưng dễ quên mất cái tủ nếu đi chậm)?
2. Bán kính cảnh báo 2 mét và hình nón 22° — cần thử thật rồi chốt.
3. Có đưa "phải đeo dọc" thành yêu cầu bắt buộc trong hướng dẫn không?

---

## Hạn chế 3 — Độ trễ và độ tin cậy

### Phần độ trễ: đã giải quyết triệt để bằng kiến trúc

Tài liệu bàn giao nêu đúng: kiến trúc hai máy làm độ trễ mạng thành một biến số.

**Bỏ hẳn máy thứ hai là bỏ hẳn biến số đó.** Không phải giảm — bỏ hẳn. Không có
mạng trong luồng chính thì không có độ trễ mạng, không có mất gói, không có phụ
thuộc WiFi của địa điểm thi.

Ngân sách độ trễ còn lại, một nhịp:

| Chặng | Ước lượng |
|---|---|
| ARCore lấy độ sâu | ~5–15 ms |
| Kotlin gộp 19.200 điểm xuống 48 ô | ~2–5 ms |
| Vượt biên JNI + lõi Python quyết định | ~3–8 ms |
| Rung phát ra | ~10 ms |
| Giọng nói bắt đầu phát | ~150–300 ms |

Điểm đáng chú ý: **giọng nói chiếm phần lớn độ trễ**, và không rút ngắn được vì
đó là thời gian tổng hợp tiếng nói. Nên **rung phát ra TRƯỚC giọng nói** — rung
không phải trang trí, nó là kênh nhanh, và với cảnh báo gấp thì hai trăm mili
giây là khoảng cách giữa dừng kịp và không kịp.

Ba quy tắc trong `MainActivity` giữ ngân sách này:
1. Không bao giờ chặn vòng lặp khung hình — chặn là mất bám vị trí, không chỉ
   giật hình
2. **Bận thì bỏ khung, không xếp hàng** — cảnh báo trễ ba giây về một cái ghế
   đã đi qua còn tệ hơn không cảnh báo, vì nó sai chỗ
3. Nhịp do lõi quyết định theo rủi ro, không do màn hình

### Phần độ tin cậy: KHÔNG giải quyết triệt để được, và đó là câu trả lời

Đây là chỗ cần nói thẳng.

Không có cách nào làm cho một cái camera phổ thông đo đúng trong mọi điều kiện.
Ai hứa điều đó là đang hứa sai. Câu hỏi đúng không phải *"làm sao cho luôn
đúng"* mà là:

> **Khi nó sai, nó sai theo hướng nào?**

Một hệ thống sai theo hướng "báo có vật trong khi không có" thì gây khó chịu.
Một hệ thống sai theo hướng "báo trống trong khi có vật" thì làm người ta ngã —
và ngã **tự tin hơn bình thường**, vì vừa được trấn an.

Toàn bộ thiết kế nghiêng hẳn về hướng sai thứ nhất:

| Cơ chế | Nghiêng về đâu |
|---|---|
| Tin cậy thấp → CHƯA BIẾT, không bao giờ TRỐNG | không dám nói an toàn |
| Tin cậy thấp → **nới** ngưỡng nguy hiểm ra xa | cảnh báo sớm hơn, không muộn hơn |
| Chưa quét bản nền → CO_VAT, không đoán là tạm thời | không dám đoán |
| Camera nhìn không tới tầm vật → giữ trong bộ nhớ | không dám quên |
| Nguồn độ sâu thưa → chặn trần tin cậy ở 0,75 | không dám tự tin |

Đổi lại: hệ thống nói nhiều hơn mức tối ưu ở những nơi khó đo. Đó là cái giá
đã chọn, có ý thức.

### Cần Dũng duyệt

1. **Có đồng ý với cách nghiêng này không?** Nó có nghĩa là ở hành lang ngược
   sáng, người dùng sẽ nghe *"tôi không quan sát được"* khá thường xuyên.
2. **Có nên có nút "im lặng 5 phút" không?** Lập luận thuận: người dùng ở khu
   vực quen thuộc không cần cảnh báo, và ép nghe là cách chắc chắn để họ tắt
   hẳn app. Lập luận nghịch: khu vực quen thuộc là đúng nơi người ta mất cảnh
   giác. **Khuyến nghị: có**, vì tắt tạm thời có kiểm soát vẫn tốt hơn gỡ app.
3. **Ngưỡng "nói quá nhiều" là bao nhiêu?** Hiện `replay.py` đo tỷ lệ nhịp có
   tiếng; bản mẫu ở 6%. Cần một con số trần để lấy làm mục tiêu khi chỉnh.

---

## Tóm tắt cần duyệt

| # | Việc | Khuyến nghị |
|---|---|---|
| 1 | Bỏ hẳn mô hình độ sâu đơn ảnh (MiDaS) | Bỏ khỏi phạm vi, giữ trên slide |
| 2 | Thời hạn bộ nhớ vật cản 12 giây | Giữ, đo lại sau khi thử thật |
| 3 | "Đeo dọc" thành yêu cầu bắt buộc | Có — không đeo dọc là mất tính năng chính |
| 4 | Chấp nhận nghiêng về phía cảnh báo thừa | Có |
| 5 | Thêm nút "im lặng 5 phút" | Có |
| 6 | Chốt trần tỷ lệ nhịp có tiếng | Đề xuất 12% |
