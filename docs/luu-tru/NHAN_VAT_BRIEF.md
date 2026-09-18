> **ĐÃ BỎ (16/09/2026).** Nhóm quyết định không làm nhân vật đồng hành.
> `BanDongHanhView.kt` đã xoá. Giữ file này vì **nguyên tắc mục 2.4** vẫn áp
> dụng cho toàn app: app không bao giờ chủ động bắt chuyện — lời mời duy nhất
> để app đọc lên một câu hỏi giờ là nút **Gợi ý** trên màn hình chính (trường
> `cham_nhan_vat` trong giao thức giữ nguyên tên để không phá hợp đồng với laptop).

# Nhân vật đồng hành — bản mô tả cho hoạ sĩ

Tài liệu này dành cho người vẽ nhân vật. Nó không nói về mã nguồn.

Mỗi ràng buộc dưới đây đều có lý do, và lý do đó được viết ra — vì một
ràng buộc không giải thích thì người vẽ sẽ (hợp lý thôi) coi nó là ý
thích cá nhân và phá nó khi thấy đẹp hơn.

---

## 1. Nhân vật này làm gì

Nó **ngồi cùng người dùng trong lúc họ làm việc**. Chỉ vậy.

Nó không nhắc việc, không chấm điểm, không báo cáo tiến độ, không cần
được cho ăn. Toàn bộ giá trị của nó nằm ở **sự có mặt**.

Nghe đơn giản nhưng đây là tính năng trung tâm của app, không phải trang
trí. Nghiên cứu về ADHD gọi cơ chế này là **body doubling** — có người
ngồi cạnh thì người ADHD bắt đầu và duy trì được công việc. Một khảo sát
220 người: 85% báo cải thiện rõ rệt. Một nghiên cứu 2025 cho thấy hiệu
quả **không mất đi khi người ngồi cạnh là nhân vật ảo**.

Đó là lý do nhân vật này tồn tại, và là lý do nó phải được vẽ đúng.

---

## 2. Sáu ràng buộc — không thương lượng

### 2.1. Ngồi BÊN CẠNH, không nhìn thẳng vào người dùng

Đây là quyết định quan trọng nhất trong cả tài liệu.

| Nhìn thẳng ra ngoài màn hình | Ngồi nghiêng, hướng nhìn đi cùng chiều |
|---|---|
| Đọc ra là **đang bị quan sát** | Đọc ra là **đang được đi cùng** |
| Tạo áp lực phải làm việc | Tạo cảm giác có người bên cạnh |

Người ADHD thường đã có sẵn cảm giác bị đánh giá về năng suất. Một khuôn
mặt nhìn chằm chằm ra màn hình sẽ khuếch đại đúng cảm giác đó.

Cụ thể: nhân vật quay khoảng **3/4 hoặc nghiêng hẳn**, ánh mắt hướng về
phía trước hoặc hơi xuống — **không** hướng ra người xem. Nếu có bàn,
sách, hay máy tính trong bố cục thì nhân vật nhìn vào đó.

### 2.2. Không có trạng thái buồn, thất vọng, hay trách móc

Nhân vật có **bốn trạng thái**, ba tích cực một trung tính:

| Trạng thái | Khi nào | Biểu cảm |
|---|---|---|
| **Bình thường** | Mặc định, và cả khi người dùng trễ giờ | Điềm tĩnh, có mặt, không đánh giá |
| **Vui** | Xong việc đúng giờ | Ấm áp, nhẹ nhàng — **không** reo hò |
| **Tự hào** | Nhiều ngày liền đúng giờ | Vui hơn một bậc, vẫn kiềm chế |
| **Dịu xuống** | Vừa quay lại sau khi bị phân tâm | Mềm, ở cạnh — **không** thương hại |

**Trạng thái xấu nhất có thể xảy ra là *bình thường*** — tức là không
khen, chứ không bao giờ là chê.

Lý do không phải về giọng điệu mà về hành vi người dùng: ADHD thường đi
kèm **nhạy cảm với sự từ chối và thất bại**. Một nhân vật tỏ ra thất
vọng sẽ khiến người dùng **tránh mở app** — và lúc đó mọi tính năng khác
đều thành vô dụng, kể cả những cái đang chạy tốt.

Điều này đã được khoá bằng ba bài kiểm thử trong mã nguồn. Bên lập trình
không vẽ nổi nét mặt buồn kể cả khi muốn: độ cong của miệng bị chặn
không cho âm.

Riêng trạng thái **"dịu xuống"**: đây là lúc người dùng vừa bị mất tập
trung và đang được dẫn trở lại. Nét mặt phải là **cùng phe**, không phải
thương hại. Gợi ý: mắt lim nhẹ thành một nét ngang mềm — cử chỉ dịu
xuống, không phải cử chỉ buồn.

### 2.3. Không có thanh máu, không có nhu cầu được chăm sóc

Không nuôi, không cho ăn, không héo đi khi bị bỏ quên, không chuỗi ngày
bị đứt gây tiếc nuối.

Mọi cơ chế kiểu thú ảo đều tạo ra **nghĩa vụ**. Nghĩa vụ không làm tròn
sinh ra **cảm giác tội lỗi**. Với nhóm người dùng này, cảm giác tội lỗi
là thứ trực tiếp dẫn tới việc gỡ app.

Nhân vật **không bao giờ ở tình trạng xấu vì người dùng**.

### 2.4. Chỉ phản hồi khi được CHẠM. Còn lại thì tự làm việc của nó

Đây là bổ sung của nhóm, và nó làm nhân vật đúng với cơ chế hơn.

**Phần "tự làm việc của nó".** Body doubling thật là như vậy: người ngồi
cạnh bạn ở thư viện **không nhìn bạn** — họ làm việc của họ. Sự có mặt
của họ có tác dụng chính vì họ đang bận. Một nhân vật ngồi im như tượng
phản lại chính cơ chế nó mô phỏng.

Nên nhân vật có **3–5 tư thế "đang bận"**: đọc, viết, nhấp một ngụm
nước, nhìn ra xa nghĩ ngợi. Đều là việc **tẻ nhạt và lặp lại** — xem
§2.5 về lý do.

**Phần "chỉ khi được chạm".** Nhân vật **không bao giờ chủ động bắt
chuyện**. Không bong bóng thoại tự hiện, không vẫy tay, không gọi.

Người dùng chạm vào nó khi họ muốn. Và thời điểm đó gần như luôn là lúc
họ đang kẹt — nên chạm là lúc **duy nhất** thích hợp để app đặt câu hỏi
can thiệp (*"Bước nhỏ nhất bạn làm được ngay bây giờ là gì?"*). Người
dùng hỏi thì app trả lời; app không bao giờ chen vào.

Điều này biến một ràng buộc thành một tính năng: **app không cằn nhằn,
về mặt cấu trúc chứ không phải về mặt thiện chí.**

**Phân biệt hai thứ dễ lẫn.** Nhân vật vẫn **đổi nét mặt** theo sự kiện
(xong việc đúng giờ, quay lại sau phân tâm) — đó là *biểu cảm*, thụ
động, không đòi hỏi gì ở người dùng. Khác hẳn *tương tác*, vốn chỉ xảy
ra khi chạm.

| | Đổi nét mặt | Tương tác |
|---|---|---|
| Kích hoạt bởi | Sự kiện của người dùng | **Chỉ cú chạm** |
| Đòi hỏi phản hồi | Không | Có |
| Ví dụ | Chuyển sang nét vui | Hiện câu hỏi chia nhỏ việc |

### 2.5. Nhân vật phải KÉM THÚ VỊ HƠN công việc của người dùng

Đây là chỗ bổ sung ở §2.4 có thể phản tác dụng, nên phải nói thẳng.

Mục tiêu **không phải** giữ mắt người dùng ở lại app. Mục tiêu là giữ
họ ở lại **công việc của họ**. Nếu nhân vật đủ hấp dẫn để người dùng
ngồi nhìn nó, thì nó đã trở thành đúng thứ phân tâm mà app sinh ra để
giảm.

**Ba quy tắc giữ nó nhàm chán đúng mức:**

1. **Không có nội dung mới theo thời gian.** Không mở khoá trang phục,
   không vật phẩm sưu tầm, không tư thế hiếm. Dùng một tháng vẫn đúng
   3–5 tư thế đó.
2. **Không có lý do để quay lại xem.** Nhân vật không thay đổi khi người
   dùng vắng mặt. Mở app ra không có gì mới để khám phá.
3. **Tư thế phải tẻ.** Đọc, viết, uống nước. **Không** nhào lộn, không
   biểu cảm hài, không gì đáng chụp màn hình gửi bạn.

**Tiêu chí thất bại, để tự kiểm:** nếu trong lúc thử, có người bắt gặp
mình **đang ngồi nhìn nhân vật** thay vì làm việc — thiết kế đã hỏng ở
đúng chỗ quan trọng nhất.

### 2.6. Chuyển tư thế: rời rạc, thưa, và chậm lại khi người dùng đang tập trung

Đây là chỗ §2.4 đụng ràng buộc ở §3: *chuyển động lặp lại trong tầm nhìn
ngoại vi là nguồn phân tâm*.

Cách gỡ: **đổi tư thế rời rạc, không phải hoạt hình chạy liên tục.**

| Không làm | Làm |
|---|---|
| Vòng lặp hoạt hình chạy suốt | Đứng yên ở một tư thế, thỉnh thoảng **đổi sang tư thế khác** |
| Nhấp nháy, nảy, lắc lư | Mờ chồng khoảng 300 ms giữa hai tư thế tĩnh |
| Nhịp đều, dễ đoán | Khoảng cách **ngẫu nhiên 3–8 phút** |

Nhịp đều bị loại có lý do: một nhịp đều đặn tự nó thành cái đồng hồ, và
người dùng sẽ bắt đầu chờ nhịp tiếp theo.

**Và nhân vật chậm lại khi người dùng đang tập trung.** Trong một phiên
làm việc, khoảng cách đổi tư thế giãn ra (8–15 phút); giữa các phiên thì
ngắn lại. Đây là **đồng điều hoà nhìn thấy được**: nhân vật đi theo nhịp
của người dùng thay vì áp nhịp của nó lên họ.

Về phía hoạ sĩ, điều này nghĩa là: **mỗi tư thế phải đứng vững một mình
như một bức tĩnh.** Không cần vẽ khung trung gian, không cần nghĩ về
chuyển động — chỉ cần 3–5 bức đẹp khi đứng yên.

---

## 3. Yêu cầu kỹ thuật

| | |
|---|---|
| Kích thước hiển thị | **140×140 dp** ở màn hình làm việc. Xem §3.2 |
| Số bản vẽ cần | **4 nét mặt** (§2.2) × **3–5 tư thế bận** (§2.4). Xem §3.1 về cách giảm số bức phải vẽ |
| Chuyển động | **Từng bức tĩnh.** Đổi tư thế bằng mờ chồng, không hoạt hình (§2.6) |
| Nền | Trong suốt |
| Định dạng | SVG nếu được; nếu không thì PNG ở 1x/2x/3x |

### 3.2. Về kích thước — đã chỉnh lên từ 96 dp

Bản đầu của tài liệu này ghi 96 dp. **Sai, sau khi thêm §2.4**: một nhân
vật đang *đọc sách* hay *viết* cần đủ chỗ để thấy được cuốn sách và cây
bút. Ở 96 dp thì bốn tư thế bận trông giống hệt nhau, và cả §2.4 mất
tác dụng.

**140 dp** ở màn hình làm việc — nơi nhân vật có ý nghĩa và màn hình
vốn trống (chỉ có đồng hồ và việc đang làm).

Ràng buộc đi kèm để nó không lấn: nhân vật **không xuất hiện** ở các màn
hình khác (danh sách việc, cài đặt, nhật ký). Nó chỉ có mặt lúc người
dùng đang làm việc — đúng lúc body doubling có tác dụng, và không lúc
nào khác.

### 3.1. Cách giảm số bức phải vẽ

4 nét mặt × 5 tư thế = 20 bức, quá nhiều cho khung thời gian này.

Đề xuất: **tách phần đầu khỏi phần thân.** Vẽ 4 cái đầu (bốn nét mặt) và
3–5 phần thân (các tư thế bận), rồi ghép khi hiển thị. Nếu bố cục cho
phép thì số bức xuống còn 8–9.

Nếu tách không đẹp thì làm theo thứ tự này, dừng lại khi hết thời gian:

1. **1 tư thế × 4 nét mặt** — đủ để app chạy đầy đủ
2. Thêm 2 tư thế bận, dùng chung nét mặt *bình thường*
3. Thêm nốt

Bước 1 là bắt buộc; hai bước sau là làm cho hay hơn.

**Vì sao tĩnh.** Nhân vật nằm ngay cạnh thông tin người dùng cần đọc.
Chuyển động lặp lại trong tầm nhìn ngoại vi là nguồn phân tâm — mà đây
là app dành cho người khó tập trung. Chuyển động duy nhất được phép là
lúc **đổi trạng thái**, và nó phải là mờ dần khoảng 200 ms, không trượt,
không chớp.

**Vì sao nhỏ.** Nó là bạn đồng hành, không phải nhân vật chính. Vẽ to sẽ
đẩy thông tin quan trọng xuống dưới.

---

## 4. Bảng màu

Nền app là **xám rất tối `#121212`**, chữ `#E8E8E8`. Nhân vật phải đọc
được trên nền đó.

Màu đã dùng trong app, để tham chiếu cho hoà hợp:

| Màu | Mã | Dùng cho |
|---|---|---|
| Xanh lam dịu | `#5B8DEF` | Còn nhiều thời gian |
| Hổ phách | `#E0A030` | Sắp đến giờ |
| Đỏ gạch | `#D4553F` | Cần đi ngay |
| Xanh lá dịu | `#7BC67B` | Vui |
| Xanh lam nhạt | `#8FA8D8` | Dịu xuống |

**Tránh**: màu bão hoà mạnh, tương phản gắt, và **đỏ tươi `#FF0000`**.
Đỏ tươi đọc ra là *báo động*, mà báo động lặp lại sẽ bị bỏ qua hoặc làm
người dùng tránh mở app.

Nhân vật nên ở **tông trung tính hoặc ấm nhẹ**, để khi app đổi màu theo
mức gấp thì nó không đánh nhau với màu đó.

---

## 5. Không ràng buộc — hoạ sĩ tự quyết

Những thứ dưới đây **cố ý để mở**. Người vẽ hiểu nhân vật hơn tôi.

- **Là gì**: người, con vật, sinh vật tưởng tượng, hay một hình khối
  trừu tượng đều được
- **Phong cách**: nét tay, phẳng, hay tối giản hình học
- **Giới tính**: khuyến khích để mơ hồ hoặc không có — người dùng không
  nên phải thấy mình giống hay không giống nhân vật
- **Tên**: chưa có, và có thể không cần

Gợi ý duy nhất: thứ gì đó **hơi lặng lẽ**. Nhân vật này ngồi im phần lớn
thời gian, và sự im lặng đó là tính năng.

---

## 6. Ba câu để tự kiểm trước khi giao

1. Nhìn vào nó, cảm giác là **"có người ngồi cạnh"** hay **"có người
   đang trông chừng"**? Phải là vế đầu.
2. Nếu người dùng trễ giờ ba ngày liền rồi mở app, nhân vật này có làm
   họ thấy **tệ hơn** không? Phải là không.
3. Ở cỡ 140 dp, có phân biệt được bốn nét mặt **và** các tư thế bận không?
4. Xem một tư thế bận trong 5 giây — nó có **tẻ** không? Phải là có
   (§2.5). Nếu nó thú vị thì nó đang cạnh tranh với công việc người dùng.

---

## 7. Bản đang có trong mã nguồn

Hiện `frontend/src/main/java/vn/adc2026/frontend/BanDongHanhView.kt` vẽ
một khuôn mặt tối giản bằng `Canvas`: hai hình tròn làm mắt, một đường
cong làm miệng, đổi màu và độ cong theo trạng thái.

Đó là **bản tạm để chạy được**, không phải bản thiết kế. Nó tồn tại để
phần logic có thứ mà kiểm thử. Khi có bản vẽ thật thì thay vào.

Một điểm bản tạm làm đúng và nên giữ: trạng thái *dịu xuống* vẽ mắt lim
thành gạch ngang thay vì cong xuống — cử chỉ dịu, không phải cử chỉ
buồn.
