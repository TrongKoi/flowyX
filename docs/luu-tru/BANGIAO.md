# BÀN GIAO DỰ ÁN — Hệ thống hỗ trợ di chuyển cho người khiếm thị
**Ngày lập:** phiên chat trước khi chuyển sang đoạn mới
**Mục đích file này:** để một phiên chat mới (hoặc chính người đọc sau vài tuần) nắm được toàn bộ bối cảnh, quyết định đã chốt, và không lặp lại các câu hỏi/quyết định đã giải quyết.

---

## 1. Bối cảnh cuộc thi

- Dự án làm cho một hackathon (ADC 2026), thời gian thi đấu giới hạn 3 ngày.
- Bài toán: hỗ trợ người khiếm thị di chuyển an toàn trong nhà (ưu tiên bối cảnh văn phòng/toà nhà), có khả năng mở rộng ra ngoài phạm vi đó.
- Nguyên tắc xuyên suốt: **hệ thống bổ trợ cho gậy dò đường, không thay thế**. Gậy vẫn phải được mang theo. Giá trị của hệ thống nằm ở việc làm được thứ gậy không làm được (định vị vị trí, dẫn đường tới một điểm cụ thể, cảnh báo vật cản treo cao ngang đầu — vùng gậy không quét tới).

---

## 2. Lịch sử kiến trúc — ba giai đoạn đã đi qua

### Giai đoạn A — ArUco (đã bỏ)
Dùng mã ArUco dán lên tường làm mốc định vị tuyệt đối, kết hợp VIO (Visual-Inertial Odometry) của điện thoại để nội suy vị trí giữa các mốc.

**Lý do bỏ:** rào cản triển khai thật — không được phép dán giấy/mã lên tường (ví dụ RMIT không cho phép), khiến quy mô áp dụng bị giới hạn nghiêm trọng. Người dùng chính (nêu ý tưởng chuyển hướng) đánh giá đây là "quá bất tiện".

**Trạng thái hiện tại:** code ArUco vẫn còn trong repo, được coi là lớp "di sản", tắt mặc định, bật lại bằng cờ `--aruco`. Không xoá, có thể dùng làm phương án dự phòng hoặc đối chứng khi demo.

### Giai đoạn B — OCR biển sẵn có + kênh độ sâu (bản pipeline vừa phân tích, PIPELINE.md)
Thay ArUco bằng ba lớp mốc neo dựa trên biển/chữ đã có sẵn trong toà nhà (số phòng, biển thoát hiểm) — không cần dán gì. Đồng thời phác thảo một kênh phát hiện chướng ngại vật bằng bản đồ độ sâu (Depth API), phân loại 4 trạng thái: cố định / tạm thời / chưa biết / trống.

**Vấn đề phát hiện được khi phân tích:** pipeline này dùng kiến trúc **hai thiết bị** — điện thoại chỉ là cảm biến (thu camera + tư thế), gửi dữ liệu qua WiFi tới **một laptop chạy Python làm toàn bộ xử lý và ra quyết định (N6–N20)**, rồi gửi kết quả (câu nói, mã rung) ngược lại điện thoại.

Đây là **quán tính kiến trúc** kế thừa từ giai đoạn ArUco (khi lý do dùng laptop là vì viết OpenCV nhận diện ArUco trên di động phức tạp), không phải thiết kế có chủ đích cho hướng đi mới.

### Giai đoạn C — Hướng đi hiện tại, đã chốt (xem mục 3)
Người dùng làm rõ ý tưởng chuyển hướng thật sự: mô phỏng theo nguyên tắc **robot hút bụi** — một thiết bị (điện thoại) tự quét, tự xử lý, tự ra quyết định, tự phản hồi, **không gọi về máy trung tâm nào**. Đây khác với pipeline hai-thiết-bị ở Giai đoạn B.

---

## 3. QUYẾT ĐỊNH KIẾN TRÚC ĐÃ CHỐT — Mô hình 2 (quan trọng nhất, đọc kỹ)

Khi được hỏi chọn giữa (1) bỏ hẳn laptop ngay bây giờ, (2) giữ laptop chỉ cho giai đoạn phát triển/debug với lộ trình rõ ràng chuyển sang độc lập trên điện thoại, hoặc (3) mô hình lai khác — **người dùng chọn Mô hình 2**.

### Ý nghĩa cụ thể của Mô hình 2:

- **Laptop-là-bộ-não KHÔNG phải kiến trúc cuối cùng.** Nó là công cụ trung gian để phát triển và gỡ lỗi nhanh trong giai đoạn hiện tại, vì:
  - Viết và test logic bằng Python trên laptop nhanh hơn viết trực tiếp bằng Kotlin/Swift.
  - Dễ debug, dễ log, dễ chỉnh sửa thuật toán mà không cần build lại app mỗi lần.
- **Đích cuối cùng là chạy độc lập hoàn toàn trên điện thoại** — đúng mô hình robot hút bụi: một thiết bị, tự trị, không phụ thuộc laptop, không phụ thuộc WiFi nội bộ giữa hai máy.
- Mọi thiết kế thuật toán từ bây giờ trở đi **phải được viết với giả định rằng nó sẽ được port sang chạy on-device**, tức là:
  - Tránh các phép toán chỉ khả thi vì "laptop có sức mạnh tính toán vô hạn". Phải tính tới giới hạn CPU/GPU/NPU của điện thoại tầm trung.
  - Giữ pipeline xử lý (nhận diện độ sâu → phân loại vật thể → ra quyết định → phát âm thanh) là các hàm/module tách biệt rõ ràng, để sau này chuyển từng khối sang chạy native mà không phải viết lại toàn bộ logic từ đầu.
  - Không thiết kế tính năng nào **bắt buộc** phải có kết nối tới máy thứ hai mới hoạt động được (trừ các tính năng phụ trợ không thuộc luồng chính, nếu có).

### Việc cần làm khi bắt đầu phiên chat mới:
1. Xác nhận lại với người dùng: giai đoạn hiện tại đang ở đâu trong lộ trình laptop → điện thoại độc lập (có thể đã có tiến triển thêm giữa các phiên).
2. Khi thiết kế bất kỳ module mới nào, luôn hỏi: "cái này có port được sang chạy trên điện thoại không, hay nó ngầm giả định có laptop?"
3. Không tự ý quay lại kiến trúc hai-thiết-bị-vĩnh-viễn như PIPELINE.md mô tả, trừ khi người dùng chủ động đổi ý.

---

## 4. Ba loại vật thể — định nghĩa lại theo trục THỜI GIAN, không phải HÌNH DẠNG

Yêu cầu gốc của người dùng: phân loại vật thể thành 3 nhóm — cố định (tường, bàn), tạm thời (cặp, bóng để giữa đường — cảnh báo "cẩn thận" nhưng vẫn cho đi), và không có vật thể (an toàn).

**Nguyên tắc kỹ thuật đã thống nhất khi thảo luận:** không thể phân biệt "cố định" và "tạm thời" bằng cách nhận dạng hình dạng vật thể (một cái cặp và một cái ghế thấp có thể trông giống nhau về mặt hình học). Thay vào đó, dùng nguyên tắc robot hút bụi thật sự áp dụng: **so sánh với bản đồ nền (backdrop/baseline) đã quét trước đó**.
- Vật có trong bản đồ nền → cố định.
- Vật không có trong bản đồ nền nhưng đang xuất hiện → tạm thời.
- Không có gì bất thường → trống/an toàn.

**Bổ sung quan trọng đã thêm vào khi phân tích PIPELINE.md — trạng thái thứ 4: CHƯA BIẾT.**
Đây không phải một trong ba loại người dùng yêu cầu, nhưng là bổ sung an toàn bắt buộc: khi chất lượng dữ liệu độ sâu thấp (tường trắng trơn, ngược sáng, sàn bóng — các điều kiện phổ biến trong văn phòng), hệ thống **không được phép coi vùng đó là "trống"/an toàn**. Phải báo "chưa biết" và xử lý thận trọng (ví dụ: không tự tin nói "an toàn để đi"). Đây là nguyên tắc an toàn cốt lõi xuyên suốt toàn dự án: **thà nói "tôi không biết" còn hơn nói sai**.

---

## 5. Tính năng: Cảnh báo tốc độ đi và chất lượng khung hình

Người dùng hỏi: có nên cảnh báo khi người dùng đi quá nhanh, vì đi chậm giúp bắt khung hình tốt hơn?

**Vấn đề cần cân nhắc khi thiết kế (chưa chốt giải pháp cụ thể, cần bàn tiếp ở phiên mới):**
- Đi nhanh → khung hình dễ bị mờ/nhoè (motion blur) → giảm độ chính xác nhận diện độ sâu và phân loại vật thể → tăng nguy cơ bỏ sót vật cản hoặc báo sai.
- Nhưng cảnh báo "đi chậm lại" có thể gây khó chịu, giảm tin cậy của người dùng vào hệ thống nếu họ vốn đã quen tốc độ đi tự nhiên của mình.
- Hướng cân nhắc: có thể không cảnh báo trực tiếp "đi chậm lại", mà thay vào đó điều chỉnh **độ tin cậy của cảnh báo** theo tốc độ đo được (nếu tốc độ cao và khung hình kém chất lượng, tăng ngưỡng thận trọng, có thể hạ giọng nói "tôi không chắc, hãy cẩn thận" thay vì im lặng hoàn toàn hoặc báo sai).
- Cần làm rõ ở phiên chat mới: cơ chế đo tốc độ di chuyển (từ VIO/gia tốc kế), ngưỡng tốc độ nào là "quá nhanh" xét theo giới hạn xử lý thực tế của thiết bị, và hình thức phản hồi phù hợp (không nên ra lệnh, nên là thông báo trạng thái).

---

## 6. Vấn đề thiết bị: không giả định trước hệ điều hành/mẫu máy cụ thể

Người dùng làm rõ: **chưa biết** sẽ dùng điện thoại của đội hay điện thoại do ban tổ chức cấp khi thi đấu. Do đó:
- **Không thể đảm bảo trước máy có ARCore Depth API (Android) hay không.**
- **Chuyển hướng ưu tiên: iOS mới là nền tảng quan trọng/chính thức**, nhưng đội đang làm Android trước vì dễ test hơn trong giai đoạn phát triển.

**Hệ quả kỹ thuật cần lưu ý ở phiên mới:**
- Thiết kế phải có **phương án suy giảm êm (graceful degradation)** khi thiết bị không hỗ trợ Depth API — không được để tính năng cốt lõi (phát hiện chướng ngại) sập hoàn toàn nếu thiếu phần cứng/API nâng cao.
- Cần làm rõ chiến lược cho iOS: thiết bị iOS phổ thông (không có LiDAR) không có `sceneDepth` đầy đủ như iPhone Pro — cần phương án dự phòng cho các máy iOS không có LiDAR nếu muốn iOS thật sự là nền tảng chính thức, không chỉ nền tảng lý tưởng hoá.
- Việc phát triển trước trên Android chỉ là chiến lược thử nghiệm nhanh — logic cốt lõi (đặc biệt nếu vẫn đang chạy trên laptop theo Mô hình 2) cần được thiết kế trung lập nền tảng để dễ chuyển sang iOS sau.

---

## 7. Đầu vào cho người dùng khiếm thị — cách tiếp cận app

- Nền tảng test trước: **Android**, dùng **TalkBack** (screen reader có sẵn của Android) làm kênh chính để người khiếm thị điều khiển/nghe phản hồi từ app.
- Kênh thay thế đang cân nhắc: **NFC** — chạm điện thoại vào thẻ/điểm NFC để mở thẳng vào app, dành cho người không dùng TalkBack. **Được xếp ưu tiên thấp hơn, có thể làm sau.**
- Hướng iOS (VoiceOver) sẽ làm sau khi ổn định trên Android, nhưng lưu ý mục 6 — về lâu dài iOS được xác định là nền tảng quan trọng hơn, nên đừng để việc "làm Android trước" biến thành thiết kế chỉ tối ưu cho Android.

---

## 8. Cơ chế vận hành: chu kỳ quét, nhiệt độ, pin

Người dùng lo ngại việc quét camera liên tục gây nóng máy và hao pin nhanh, đề xuất tìm một **chu kỳ quét nhất định** thay vì quét liên tục 100% thời gian.

**Việc cần làm ở phiên mới:** thiết kế cụ thể chu kỳ bật/tắt hoặc điều chỉnh tần suất xử lý khung hình (ví dụ: không nhất thiết phải chạy nhận diện độ sâu đầy đủ ở mọi khung hình; có thể xử lý đầy đủ theo nhịp thấp hơn và dùng phép nội suy/theo dõi chuyển động nhẹ ở giữa). Cần cân bằng giữa:
- Tốc độ phản hồi khi có vật cản xuất hiện đột ngột (không được để lỡ khung hình quan trọng vì đang ở "chu kỳ nghỉ").
- Nhiệt độ và pin khi dùng liên tục trong thời gian dài.

Đây là điểm cần bàn kỹ ở phiên mới, hiện chưa có con số/thuật toán cụ thể được chốt.

---

## 9. Góc camera và vùng mù

- Người dùng chủ động chọn **chúc camera xuống dưới nhiều hơn**, ưu tiên phát hiện chướng ngại vật ở tầm thấp (dưới chân/tầm gối) — vì đây là nơi gậy dò đường **không** phát hiện tốt (mù phía trước gần chân khi vung gậy).
- Người dùng **thừa nhận chưa có giải pháp** cho chướng ngại vật ở tầm cao (ngang đầu, ngang ngực) — nêu rõ đây cũng là hạn chế mà gậy trắng truyền thống chưa giải quyết được.
- **Việc cần làm ở phiên mới:** đây là khoảng trống thiết kế thật sự, cần bàn giải pháp cụ thể — có thể là góc camera kép/quét theo chu kỳ đổi góc, cảm biến phụ, hoặc chấp nhận giới hạn này và ghi rõ trong tài liệu sản phẩm để không gây hiểu lầm "hệ thống bảo vệ toàn thân".

---

## 10. Ba hạn chế kỹ thuật người dùng đã nêu, cần giải pháp brainstorm ở phiên mới

Người dùng liệt kê rõ ba "drawback" ưu tiên xử lý, trong bối cảnh scale nhỏ (văn phòng trước tiên):

1. **Ngược sáng / thiếu ánh sáng:** camera gặp điều kiện ngược sáng hoặc ánh sáng yếu thì xử lý thế nào để vẫn hiệu quả? (Chưa có giải pháp chốt — cần brainstorm: có thể liên quan tới cảm biến IR, xử lý ảnh HDR, hoặc kết hợp cảm biến khác ngoài camera thường.)

2. **Va chạm vật thể tầm cao** (liên kết với mục 9): làm sao xử lý mà **không đổi góc camera hay mở rộng góc camera** — tức người dùng đặt ràng buộc cụ thể là muốn tìm cách khác ngoài hai hướng đó. Cần brainstorm hướng đi thứ ba.

3. **Độ trễ (latency) và độ tin cậy (reliability):** làm sao giải quyết triệt để nhất — đây là câu hỏi mở, cần phân tích kỹ ở phiên mới, đặc biệt quan trọng vì Mô hình 2 (mục 3) có giai đoạn trung gian vẫn phụ thuộc kết nối laptop-điện thoại, nên độ trễ mạng cũng là một biến số cần tính tới trong giai đoạn hiện tại, không chỉ độ trễ xử lý thuật toán.

**Lưu ý cho AI ở phiên mới:** người dùng muốn được **brainstorm và đề xuất giải pháp**, sau đó **người dùng sẽ là người duyệt** — không tự ý chốt và triển khai luôn mà chưa qua bước đề xuất/duyệt cho ba điểm này.

---

## 11. Nhận định phân tích quan trọng đã trình bày (business + kỹ thuật) — nên nhắc lại nếu liên quan

Khi được hỏi đóng vai business analyst + senior engineer để đánh giá xem dự án có tối ưu cho cuộc thi không, các điểm chính đã nêu (người dùng chưa phản hồi chốt, cần theo dõi tiếp ở phiên mới nếu quay lại chủ đề này):

- **Rủi ro:** khối lượng yêu cầu kỹ thuật (Swift, TestFlight, phân biệt hệ điều hành, mô hình con lắc cho dây đeo, hồ sơ chiều cao người dùng...) đang ở quy mô "sản phẩm MVP thật" chứ không phải quy mô "bài dự thi hackathon 3 ngày". Cần cân nhắc thu hẹp phạm vi demo.
- **Định vị giá trị:** không nên pitch là "thay thế gậy" — nên pitch là "làm được ba việc gậy không làm được" (định vị vị trí, dẫn đường tới điểm cụ thể, cảnh báo vật cản tầm cao) và **minh bạch rằng gậy vẫn cần mang theo song song**.
- **Rủi ro vận hành ngày thi:** kiến trúc hai-thiết-bị (nếu vẫn dùng khi lên sân khấu demo) phụ thuộc WiFi ổn định giữa điện thoại và laptop — rủi ro sập demo nếu mạng sự kiện chập chờn. Cần có phương án dự phòng hoặc offline demo nếu tới lúc đó vẫn chưa chuyển hết sang chạy độc lập trên điện thoại.
- Đề xuất đã đưa ra nhưng **chưa được người dùng duyệt**: cân nhắc dùng lại ArUco làm lớp định vị chính cho riêng bản demo hackathon (ổn định, dễ debug, ít phụ thuộc phần cứng đặc thù), giữ hướng OCR/biển sẵn có + depth làm câu chuyện "hướng phát triển tiếp theo" trên slide. **Người dùng đã phản hồi muốn quay lại dùng ArUco** (xem tin nhắn gần nhất) — cần làm rõ ở phiên mới: có phải người dùng đã chốt quay lại ArUco làm chính, hay vẫn đang cân nhắc song song với hướng độ sâu/3-lớp-vật-thể.

---

## 12. Việc CHƯA làm / cần làm tiếp ở phiên chat mới (tổng hợp thứ tự ưu tiên gợi ý)

1. Làm rõ trạng thái ArUco: quay lại làm chính, hay vẫn giữ vai trò di sản/dự phòng trong khi phát triển hướng độ sâu + 3 lớp vật thể song song.
2. Xác nhận phạm vi demo cho hackathon 3 ngày — có thể cần thu hẹp so với toàn bộ tầm nhìn dài hạn.
3. Thiết kế cụ thể cơ chế phân loại 4 trạng thái (cố định/tạm thời/chưa biết/trống) dựa trên so sánh bản đồ nền — bao gồm cách quét và lưu bản đồ nền ban đầu.
4. Thiết kế chu kỳ xử lý khung hình để cân bằng tốc độ phản hồi với nhiệt độ/pin (mục 8).
5. Brainstorm và chốt giải pháp cho ba hạn chế ở mục 10 (ngược sáng, vật cản tầm cao không đổi góc camera, độ trễ/độ tin cậy) — trình bày để người dùng duyệt trước khi code.
6. Thiết kế cơ chế phản hồi tốc độ đi (mục 5) — dạng điều chỉnh độ tin cậy, không phải ra lệnh trực tiếp.
7. Làm rõ chiến lược suy giảm êm cho thiết bị không có Depth API, và chiến lược thật sự cho iOS không LiDAR (mục 6).
8. Tiếp tục lộ trình Mô hình 2: theo dõi tiến độ chuyển từ "laptop xử lý" sang "điện thoại xử lý độc lập", đảm bảo mọi module mới thiết kế đều tính trước khả năng port sang on-device.

---

## 13. Ghi chú cho AI ở phiên chat mới

- Người dùng sẽ tự gửi lại các file code hiện có ở phiên mới — **không cần AI tạo lại hay xuất code ở đây**.
- Khi bắt đầu phiên mới, nên **đọc file bàn giao này trước, sau đó hỏi xác nhận nhanh các điểm ở mục 12** (đặc biệt điểm 1 — trạng thái ArUco) trước khi đề xuất kiến trúc hoặc viết bất kỳ thuật toán nào, để tránh giả định sai và đi lệch hướng như đã từng xảy ra ở PIPELINE.md.
- Giữ đúng phong cách làm việc đã thiết lập trong dự án: đề xuất → giải thích đánh đổi → chờ người dùng duyệt → mới triển khai, đặc biệt với các quyết định kiến trúc hoặc an toàn (ví dụ nguyên tắc "chưa biết thì báo chưa biết, không đoán là an toàn").
