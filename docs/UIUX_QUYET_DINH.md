# Quyết định UI/UX cho hai chế độ

> **Ghi chú 28/09/2026.** Tài liệu này viết khi app còn hai chế độ
> (khiếm thị và ADHD) chung một phiên ARCore. Phần khiếm thị đã tách
> sang repo opticguard, nên **Câu 1 và Câu 2** chỉ còn là lịch sử quyết
> định. **Câu 3, Câu 4 và mục “Những gì KHÔNG làm”** (màu, nhịp độ, mật
> độ thông tin, vì sao không dùng Jetpack Compose) vẫn áp dụng cho FlowyX.

Tài liệu này trả lời bốn câu hỏi thiết kế **trước khi** viết layout hay
Activity nào. Mỗi câu có 2–3 phương án, so sánh, rồi chọn một kèm lý do.

Ràng buộc nền, không được vi phạm:

- Chế độ khiếm thị gần như **không có giao diện đồ hoạ** — đó là quyết
  định có chủ đích, không phải thiếu sót. Người không nhìn màn hình thì
  hình ảnh không có giá trị, và vẽ thêm chỉ làm chậm vòng lặp camera.
- Chế độ ADHD thì **ngược lại**: hình ảnh là kênh chính, giọng nói là
  kênh phụ trợ.
- App mặc định vào chế độ khiếm thị trước, dẫn bằng âm thanh ngay khi
  mở. **Đã chốt, không đổi.**

---

## Câu 1 — Màn hình chọn chế độ xuất hiện khi nào, trông ra sao?

### Phương án A — hỏi ngay màn hình đầu, dạng hộp thoại

Mở app → hộp thoại hai nút.

| | |
|---|---|
| Được | Rõ ràng, người dùng biết ngay có hai chế độ |
| Mất | **Chặn đường** người khiếm thị mỗi lần mở app. Họ phải nghe hết câu hỏi rồi mới tới được nút Bắt đầu — tức là mỗi lần dùng đều trả giá cho một tính năng họ không cần |

### Phương án B — chôn trong Cài đặt

| | |
|---|---|
| Được | Không cản trở ai |
| Mất | Người ADHD sẽ **không bao giờ tìm thấy**. Một tính năng phải đi tìm mới thấy thì với đúng nhóm người có khó khăn về chức năng điều hành là tính năng không tồn tại |

### ★ Phương án C — dẫn bằng âm thanh, nhưng để sẵn lối rẽ (đã chọn)

Mở app → nói ngay như hiện tại, **không chặn gì cả**:

```
"Sẵn sàng. Chạm nút Bắt đầu ở giữa màn hình để chạy.
 Nếu bạn muốn xem nhắc giờ và hình ảnh trên màn hình,
 chạm nút bên dưới."
```

Nút thứ hai nằm **ngay dưới** nút Bắt đầu, to bằng, có nhãn TalkBack đọc
được. Không hộp thoại, không chặn.

**Vì sao chọn**: giữ nguyên đường đi của người khiếm thị (họ chạm nút
giữa màn hình như cũ), mà vẫn để lối rẽ ở chỗ **không thể bỏ sót** —
ngay dưới ngón tay, và được đọc lên trong câu chào.

### Cách hỏi: theo NHU CẦU, không theo chẩn đoán

**Không hỏi "Bạn có phải người ADHD không?"** Nhiều người chưa được chẩn
đoán chính thức, hoặc không muốn khai báo. Hỏi thẳng như vậy khiến người
dùng thấy bị dán nhãn, và câu trả lời thu được cũng không chính xác hơn.

Nhãn nút, cả hai đều mô tả **thứ họ sẽ nhận được**:

```
[  Bắt đầu đi  ]              <- chế độ giọng nói (mặc định)
[  Xem nhắc giờ trên màn hình  ]   <- chế độ ADHD
```

Câu này **bất kỳ ai cũng trả lời được**: người không tự nhận có ADHD
nhưng hay trễ giờ vẫn chọn được; người khiếm thị muốn thử nhắc giờ cũng
chọn được. Không ai phải tự nhận mình thuộc nhóm nào.

Hệ quả kỹ thuật: **hai chế độ không loại trừ nhau.** Chế độ ADHD bật
thêm phần hình ảnh và nhắc giờ, chứ không tắt giọng nói. Xem câu 2.

---

## Câu 2 — Logic chuyển cảnh giữa hai chế độ

### 2a. Một Activity hay hai?

**Phương án A — hai Activity riêng.** Tách sạch, mỗi bên tối ưu riêng.
Nhưng: phiên ARCore **không sống qua được** ranh giới Activity. Chuyển
chế độ giữa đường sẽ mất tracking, mất vị trí, mất cả lộ trình đang đi.
Với người dùng thì đó là "app khởi động lại giữa lúc tôi đang đi".

**Phương án B — một Activity, nhiều trạng thái hiển thị.** Cùng phiên
ARCore, cùng `BridgeClient`, chỉ đổi phần hiển thị.

**★ Chọn B.** Lý do quyết định là ARCore: phiên tracking là thứ đắt nhất
và mong manh nhất trong app. Mọi thiết kế phải xoay quanh việc **không
làm gián đoạn nó**.

Cách hiện thực: `MainActivity` giữ hai `View` con trong cùng layout.

```
ScrollView
 ├── GLSurfaceView 1dp        (ARCore, luôn sống, cả hai chế độ)
 ├── khối khiếm thị           (trạng thái, nút, live region)
 └── khối ADHD                (timer đĩa tròn, chặng, giờ hẹn)  ← View.GONE mặc định
```

Đổi chế độ = đổi `visibility` của hai khối. Vòng lặp camera không biết
gì cả.

**Chi phí đã cân nhắc**: chế độ ADHD vẽ nặng hơn. Nhưng `power.py` đã
điều tiết nhịp xử lý theo hoạt động, và timer chỉ vẽ lại **mỗi giây một
lần** (xem câu 3), không phải mỗi khung hình. Phần vẽ thêm không đụng
vào vòng 30 Hz.

### 2b. Đổi chế độ giữa đường được không?

**Được.** Nếu phải dừng lại mới đổi được thì người dùng sẽ không đổi —
lúc họ nhận ra mình cần nhắc giờ chính là lúc họ đang đi và đang lo trễ.

| Giữ nguyên | Khởi động lại |
|---|---|
| Phiên ARCore, vị trí, lộ trình, `leg_index` | Chỉ phần hiển thị |
| Giờ hẹn và các mốc đã nhắc (`BoNhacGio`) | |
| Mục đích chuyến đi, trạng thái `BoTheoMach` | |

Nói cách khác: **toàn bộ trạng thái nằm ở lõi, không nằm ở giao diện.**
Đó là lý do việc đổi chế độ giữa đường rẻ như vậy — kiến trúc sẵn có đã
tách đúng chỗ.

### 2c. Hiệu ứng chuyển cảnh

| Chiều | Hiệu ứng |
|---|---|
| Khiếm thị → khiếm thị | Không có. Không ai nhìn. |
| Vào/ra chế độ ADHD | Mờ dần 200 ms, **không** trượt, **không** chớp sáng |

Người ADHD và nhiều người neurodivergent khác nhạy cảm với thay đổi hình
ảnh đột ngột. Một cú chớp hoặc trượt mạnh ngay khi vừa mở app là đủ gây
khó chịu và mất tập trung — đúng thứ app này sinh ra để giảm.

200 ms là ngưỡng đủ để mắt theo kịp mà không thành chậm chạp. Dùng
`alpha` chứ không dùng dịch chuyển: chuyển động ngang trong tầm nhìn
ngoại vi dễ gây mất tập trung hơn thay đổi độ mờ.

---

## Câu 3 — Màu sắc, nhịp độ, mật độ thông tin cho chế độ ADHD

Sáu tiêu chí nền: khả năng dự đoán, rõ ràng, quản lý tải giác quan, quản
lý tải nhận thức, quyền kiểm soát, không tạo áp lực xã hội.

### Màu

Nền hiện tại của app là **đen tuyền** (`#000000`) — đúng cho chế độ
khiếm thị (tiết kiệm pin OLED, không ai nhìn). Cho chế độ ADHD thì nền
đen với chữ trắng cho độ tương phản rất cao, **mỏi mắt khi nhìn lâu** —
mà màn hình timer thì đúng là loại nhìn lâu.

Chọn: nền **xám rất tối** `#121212` thay vì đen tuyền, chữ `#E8E8E8` thay
vì trắng tinh. Giảm tương phản từ 21:1 xuống khoảng 14:1 — vẫn vượt xa
chuẩn WCAG AA (4,5:1) nhưng dịu hơn hẳn khi nhìn liên tục.

Đĩa timer:

| Trạng thái | Màu | Vì sao |
|---|---|---|
| Còn nhiều thời gian | xanh lam dịu `#5B8DEF` | Trung tính, không giục |
| Sắp đến giờ | hổ phách `#E0A030` | Đổi màu là tín hiệu, không cần đọc chữ |
| Cần đi ngay | đỏ gạch `#D4553F` | **Không** dùng đỏ tươi bão hoà |

Đỏ tươi bão hoà (`#FF0000`) bị loại có chủ đích: nó đọc là *báo động*,
và báo động lặp lại nhiều lần sẽ bị bỏ qua hoặc làm người dùng tránh mở
app. Đỏ gạch vẫn rõ là "gấp" mà không gào lên.

### Chuyển động

- Đĩa timer cập nhật **mỗi giây một lần**, không mượt liên tục. Chuyển
  động liên tục trong tầm nhìn ngoại vi là nguồn phân tâm.
- **Không nhấp nháy gì cả**, kể cả khi sắp trễ. Đổi màu là đủ. Nhấp nháy
  là thứ gây khó chịu nhiều nhất trong nhóm này.

### Vị trí thông tin — quy tắc cứng

**Mọi thông tin quan trọng luôn ở đúng một chỗ, không bao giờ nhảy vị
trí giữa các lần cập nhật.**

```
┌─────────────────────────┐
│   [ đĩa tròn thu nhỏ ]  │  ← luôn ở giữa trên
│        6 phút           │  ← số nhỏ, PHỤ
├─────────────────────────┤
│  Còn 2 chặng            │  ← luôn ở đây
│  Rẽ phải ở lối tới      │  ← luôn ở đây
└─────────────────────────┘
```

Nhất quán vị trí giảm tải nhận thức: mỗi lần nhìn lại màn hình, người
dùng không phải **tìm** lại thông tin. Với người có khó khăn về chức
năng điều hành, chi phí tìm lại đó là thật và lặp lại hàng chục lần mỗi
chuyến đi.

Hệ quả: khi không có dữ liệu, ô đó hiển thị dấu gạch, **không bị co
lại**. Layout không bao giờ đổi hình dạng.

### Mật độ

Tối đa **ba khối** thông tin một lúc: đĩa, chặng, chỉ dẫn. Cùng giới hạn
~4 đơn vị mà `preview.py` đã dùng cho phần đọc lên — cùng một giới hạn
trí nhớ làm việc, nên cùng một con số.

---

## Câu 4 — Mức độ chi tiết (ít nói / vừa / nhắc thường xuyên)

**Có làm**, vì rẻ: `BoNhacGio` đã nhận danh sách mốc làm tham số, nên
thay đổi mức chỉ là truyền một danh sách khác.

| Mức | Mốc nhắc (phút còn lại) |
|---|---|
| Ít nói | 5, 1 |
| Vừa (mặc định) | 10, 5, 3, 1 |
| Nhắc thường xuyên | 15, 10, 5, 3, 2, 1 |

**Đặt ở đâu**: một hàng ba nút ngay trên màn hình chính của chế độ ADHD,
**không** chôn trong Cài đặt.

Lý do: người dùng chỉ biết mức nào hợp khi đang đi và thấy nó quá nhiều
hoặc quá ít. Bắt họ dừng lại, mở menu, tìm mục — là bắt họ làm đúng
chuỗi thao tác nhiều bước mà nhóm này khó nhất. Đổi mức phải là **một
lần chạm**.

Quyền kiểm soát là một trong sáu tiêu chí nền, và đây là chỗ rẻ nhất để
trao nó.

---

## Những gì KHÔNG làm, và vì sao

**Bạn đồng hành** — đã làm, `BanDongHanhView.kt`.

Vẽ bằng `Canvas` chứ không dùng tài nguyên ảnh: một khuôn mặt gồm hai
hình tròn và một đường cong. Đổi nét mặt chỉ là đổi vài con số, không
phải đóng gói bốn tệp ảnh cho bốn trạng thái ở nhiều độ phân giải.

Giữ **tĩnh**, không hoạt hình. Chuyển động lặp lại trong tầm nhìn ngoại
vi là nguồn phân tâm, và nó nằm ngay cạnh thông tin dẫn đường.

Ràng buộc đã chốt và đã hiện thực: **không có trạng thái buồn hay thất
vọng**. Độ cong miệng không bao giờ âm — cung quay xuống là nét mặt
buồn, và module cấm điều đó. Trạng thái `THONG_CAM` vẽ mắt lim thành
gạch ngang: cử chỉ **dịu xuống**, không phải cử chỉ buồn.

ADHD thường đi kèm nhạy cảm với thất bại, và một nhân vật tỏ ra thất
vọng sẽ làm người dùng tránh mở app — ngược hoàn toàn với mục đích.

**Jetpack Compose** — không dùng. Dự án cố ý không có androidx nào
(`build.gradle.kts` ghi rõ lý do: bớt một phụ thuộc là bớt một chỗ có
thể hỏng lúc build gấp). Compose kéo theo khoảng 8 dependency androidx
cộng compiler plugin phải khớp phiên bản Kotlin. Đĩa timer vẽ bằng
`Canvas.drawArc` mất chừng 40 dòng và **chắc chắn build được**.
