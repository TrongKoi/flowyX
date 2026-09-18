# Đối chiếu với các sản phẩm đã có

Năm sản phẩm được nêu, cộng Clew. Mục đích: biết mình đứng ở đâu, và chuẩn bị
sẵn câu trả lời cho câu giám khảo chắc chắn hỏi — *"cái này có gì mới?"*

Tra ngày 12/09/2026. Nguồn ghi ở cuối.

---

## 1. Bản đồ thị trường theo hai trục

Hai trục quyết định mọi thứ: **cần lắp gì** và **giải bài toán nào**.

```
                    GIẢI BÀI TOÁN NÀO
                    
        "tôi ở đâu, đi đường nào"        "phía trước có gì"
      ┌────────────────────────────┬──────────────────────────┐
 CẦN  │  GoodMaps    (quét LiDAR)  │                          │
 LẮP  │  NaviLens    (dán mã)      │  Project Guideline       │
 GÌ   │  Lazarillo   (beacon)      │  (sơn vạch dưới đất)     │
 ĐÓ   │                            │                          │
      ├────────────────────────────┼──────────────────────────┤
 KHÔNG│  BlindSquare (GPS, ngoài   │                          │
 LẮP  │              trời)         │        ← TRỐNG →         │
 GÌ   │  Clew        (chỉ đi lại   │                          │
      │              đường đã ghi) │                          │
      └────────────────────────────┴──────────────────────────┘
```

**Ô dưới bên phải đang trống.** Không sản phẩm nào trong danh sách vừa trả lời
"phía trước có gì" vừa không đòi lắp đặt gì.

Đó là chỗ sản phẩm của nhóm nhắm vào — và cũng là chỗ phải giải thích được **vì
sao nó trống**: có thể vì khó, hoặc vì không ai cần. Mục 4 trả lời câu đó.

---

## 2. Từng sản phẩm

### Google Project Guideline

Điện thoại Android đeo thắt lưng, mô hình phân đoạn ảnh chạy **trên máy** phân
loại từng điểm ảnh thành "vạch" hoặc "không phải vạch", rồi báo bằng âm thanh
qua tai nghe để người khiếm thị **chạy bộ** một mình.

| Điểm mạnh | Điểm yếu |
|---|---|
| Chạy hoàn toàn trên máy, không cần mạng, không cần GPS | **Phải sơn một vạch vàng dưới đất** — chỉ dùng được ở nơi đã sơn |
| Độ trễ rất thấp, đủ cho tốc độ chạy bộ | Chỉ bám vạch, **không phát hiện vật cản** |
| Đã mã nguồn mở, ai cũng dùng lại được | Một mục đích duy nhất: tập thể dục, không phải đi lại hằng ngày |

**Đáng chú ý nhất:** Google đang hướng tới **bỏ hẳn vạch sơn**, dùng ARCore
Scene Semantics để nhận ra vỉa hè và công trình. Nghĩa là chính Google cũng đang
đi đúng hướng mà nhóm chọn — dùng hiểu biết ngữ cảnh thay cho hạ tầng dán thêm.

### Clew

App iOS của Olin College. Dùng **ARKit** ghi lại đường đi bằng "vụn bánh mì" ảo,
rồi dẫn người dùng quay lại đúng đường đó bằng giọng nói, âm báo và rung.

| Điểm mạnh | Điểm yếu |
|---|---|
| **Không cần lắp gì** — đúng điểm chung với sản phẩm của nhóm | **Chỉ đi lại được đường đã tự ghi**, không tới được nơi chưa từng đi |
| Miễn phí, mã nguồn mở | Không có bản đồ, không tìm đường |
| Đã có người khiếm thị dùng thật | Kém ở ngoài trời, nắng gắt, chỗ đông người |
| Rung + âm báo + giọng nói, không chỉ giọng nói | Không phát hiện vật cản |

Đây là sản phẩm **gần nhất về mặt kỹ thuật** với nhóm: cùng dùng VIO, cùng không
lắp gì. Khác biệt nằm ở chỗ Clew không có bản đồ.

### GoodMaps

Thương mại. Quét toà nhà bằng **LiDAR**, dựng bản đồ, rồi định vị bằng camera —
**không cần beacon, không cần Bluetooth**. Chính xác tới cỡ bước chân. Dùng ở
sân bay, nhà ga.

| Điểm mạnh | Điểm yếu |
|---|---|
| Chính xác cao nhất trong nhóm này | **Phải quét toà nhà trước** — tốn kém, và toà nhà phải đồng ý trả tiền |
| Không cần beacon | LiDAR có trường nhìn hẹp, toà nhà lớn phải quét nhiều lượt |
| Có chế độ **tự quét** cho chủ toà nhà | Bản đồ cũ đi khi toà nhà đổi bố trí |
| Đã triển khai thật ở quy mô lớn | Không phát hiện vật cản |

Chế độ tự quét của GoodMaps rất giống ý "quét phòng" trong hướng mới của nhóm.
**Nghĩa là ý đó không mới** — nhưng nó đã được chứng minh là chạy được.

### NaviLens

Mã màu **ddTag** dán lên tường, đọc được từ **xa gấp khoảng 12 lần mã QR
thường** — mã 5cm đọc được ở 5 mét, mã lớn hơn thì xa hơn nhiều. Đọc được ở góc
rộng **160–180 độ**, và **không phải ngắm camera**. Triển khai ở tàu điện
Barcelona, MTA New York.

| Điểm mạnh | Điểm yếu |
|---|---|
| **Không phải ngắm** — giải đúng bài toán mà nhóm từng vấp với ArUco | **Phải dán mã** — chính thứ mentor đã bác |
| Đọc được khi đang đi, ở góc rất xiên | Chỉ biết được ở đúng chỗ có dán mã |
| Miễn phí, đã triển khai quy mô lớn | Không phát hiện vật cản |
| In ra là dùng, không cần điện, không pin | Mã phải được in đúng và bảo quản |

**Bài học cho nhóm:** vấn đề "camera đeo ngực có ngắm được mã không" mà nhóm lo
là vấn đề có thật — và NaviLens giải nó bằng **thiết kế mã tốt hơn**, không phải
bằng cách bỏ mã. Nếu sau này cần quay lại hướng dán mã thì đây là cách đúng.

### Lazarillo

Điều hướng cả ngoài trời lẫn trong nhà, đọc tên địa điểm xung quanh, hợp tác với
các toà nhà để có bản đồ trong nhà.

| Điểm mạnh | Điểm yếu |
|---|---|
| Bao phủ cả ngoài trời và trong nhà — hiếm | Trong nhà phải có hợp tác với chủ toà nhà |
| Đọc địa điểm xung quanh, không chỉ dẫn đường | Chất lượng phụ thuộc dữ liệu từng nơi |
| Đã có người dùng thật ở nhiều nước | Không phát hiện vật cản |

### BlindSquare

Lâu đời nhất. GPS cộng dữ liệu OpenStreetMap và Foursquare, đọc tên cửa hàng,
ngã tư, hướng đi. Trả phí.

| Điểm mạnh | Điểm yếu |
|---|---|
| Rất chín, rất nhiều người dùng, tin cậy | **Không dùng được trong nhà** — GPS không xuyên tường |
| Không cần lắp gì (dùng dữ liệu mở sẵn có) | Không phát hiện vật cản |
| Mạnh ở việc "xung quanh tôi có gì" | Trả phí |

---

## 3. Bảng đối chiếu

| | Trong nhà | Ngoài trời | Cần lắp gì | Tìm đường tới đích | Cảnh báo vật cản | Chạy một mình trên máy |
|---|---|---|---|---|---|---|
| Project Guideline | ❌ | ✅ | Sơn vạch | ❌ bám vạch | ❌ | ✅ |
| Clew | ✅ | ⚠️ kém | **Không** | ⚠️ chỉ đường đã ghi | ❌ | ✅ |
| GoodMaps | ✅ | ❌ | Quét LiDAR | ✅ | ❌ | ✅ |
| NaviLens | ✅ | ✅ | Dán mã | ⚠️ theo điểm có mã | ❌ | ✅ |
| Lazarillo | ✅ | ✅ | Beacon/hợp tác | ✅ | ❌ | ✅ |
| BlindSquare | ❌ | ✅ | Không | ✅ | ❌ | ✅ |
| **Sản phẩm của nhóm** | ✅ | ❌ | **Không** | ✅ | ✅ | ❌ **cần laptop** |

---

## 4. Sản phẩm của nhóm CÓ mà các app kia KHÔNG có

### 4.1 Cảnh báo vật cản ngang tầm đầu — không app nào trong danh sách có

Cột "cảnh báo vật cản" trống ở **cả sáu** sản phẩm.

Và nghiên cứu nền của nhóm đã chỉ ra đây không phải ô trống vô nghĩa: gậy dò
đường **không phát hiện vật cản tầm đầu/ngực, vật treo lơ lửng, vật di chuyển**.
Nghĩa là có một khoảng trống thật, mà cả gậy lẫn sáu sản phẩm này đều không lấp.

Đây là luận điểm mạnh nhất khi pitch, vì nó đứng trên hai chân: nghiên cứu nói
gậy mù ở đó, và bảng này nói không app nào lấp chỗ đó.

### 4.2 Trong nhà, tìm đường tới đích, mà không lắp gì

Chỉ có Clew cùng nhóm "không lắp gì" trong nhà — nhưng Clew **chỉ đi lại được
đường đã tự ghi**. Muốn tới một phòng chưa từng đi thì Clew chịu.

Cách làm của nhóm — **đọc chính biển chữ toà nhà đã có** — là điểm khác biệt
đáng bảo vệ nhất. Các sản phẩm khác hoặc lắp thêm (NaviLens, GoodMaps,
Lazarillo), hoặc bỏ luôn bản đồ (Clew).

### 4.3 Mô hình độ tin cậy và quyền từ chối

Không tài liệu nào của sáu sản phẩm nói về việc **hệ thống tự nhận là không
chắc**. Sản phẩm của nhóm từ chối nói khi:

- chưa định vị được
- mốc neo kéo theo bước nhảy vị trí vô lý
- hai tấm biển trùng chữ mà không chọn được chắc chắn
- độ sâu không đáng tin ở vùng mặt đất

và khi từ chối thì **nói thật** thay vì im lặng. Với người khiếm thị, "tự tin
nói sai" nguy hiểm hơn "thừa nhận không biết".

### 4.4 Đặt trong bối cảnh việc làm

Sáu sản phẩm đều là công cụ đi lại chung. Không cái nào nhắm vào **rào cản việc
làm**. Đó là trục chấm điểm của ADC 2026.

---

## 5. Các app kia CÓ mà sản phẩm của nhóm KHÔNG có

Phần này quan trọng hơn phần trên. Nói trước còn hơn bị hỏi.

### 5.1 🔴 Chúng là app độc lập — sản phẩm của nhóm cần một cái laptop

Đây là khoảng cách lớn nhất, và giám khảo sẽ thấy ngay trong 10 giây đầu của
demo.

Cả sáu sản phẩm chạy trọn vẹn trên điện thoại. Sản phẩm của nhóm gửi dữ liệu về
laptop để xử lý.

Kiến trúc này có lý do chính đáng — gỡ lỗi nhanh hơn nhiều, và đổi nền tảng chỉ
là viết lại client mỏng — nhưng **phải nói thẳng đó là kiến trúc bản mẫu**, kèm
lộ trình đưa về chạy hoàn toàn trên máy. Giấu thì mất điểm nặng hơn nhiều so với
nhận.

### 5.2 Chúng đã có người dùng thật, sản phẩm của nhóm chưa có ai

NaviLens ở tàu điện Barcelona và MTA New York. GoodMaps ở sân bay. Clew có người
khiếm thị dùng nhiều năm. BlindSquare hàng chục nghìn người dùng.

Sản phẩm của nhóm: **chưa một người khiếm thị nào thử.**

### 5.3 Không có ngoài trời

BlindSquare, Lazarillo, NaviLens, Project Guideline đều dùng được ngoài trời.
Sản phẩm của nhóm chỉ trong nhà. Chấp nhận được vì bài toán là nơi làm việc,
nhưng phải nói rõ là lựa chọn phạm vi, không phải thiếu sót bỏ quên.

### 5.4 Không có chế độ "xung quanh tôi có gì"

Giá trị lõi của BlindSquare là đọc tên cửa hàng, ngã tư, hướng đi — **khám phá**
chứ không chỉ dẫn đường. Lazarillo cũng vậy. Sản phẩm của nhóm chỉ dẫn từ A tới
B, không giúp người dùng hiểu không gian xung quanh.

### 5.5 Không có giao thông công cộng

NaviLens và Lazarillo tích hợp thông tin tàu xe. Không liên quan tới bài toán
văn phòng, nhưng đó là lý do chúng được triển khai quy mô lớn.

### 5.6 Chưa có bản iOS

**70,6% người dùng screen reader dùng VoiceOver** (WebAIM #10, xem
`research/README.md`). Clew chỉ có iOS. GoodMaps, NaviLens, BlindSquare,
Lazarillo đều có iOS.

Sản phẩm của nhóm hiện chỉ có Android, và Android mới chỉ là bản để kiểm thử.

### 5.7 Mã đọc được từ xa và không cần ngắm

NaviLens đọc mã từ xa gấp 12 lần QR thường, ở góc 160–180 độ, **không phải ngắm
camera**. Đó đúng là vấn đề nhóm đã lo khi dùng ArUco — và NaviLens giải nó bằng
thiết kế mã tốt hơn chứ không phải bỏ mã.

---

## 6. Nói gì khi pitch

Một câu định vị:

> Các sản phẩm hiện có trả lời *"tôi đang ở đâu"*. Cây gậy trả lời *"ngay dưới
> chân có gì"*. Không ai trả lời *"ngang tầm đầu tôi có gì"* — và đó là chỗ
> nghiên cứu chỉ ra người khiếm thị hay bị thương nhất.

Và một câu về triển khai:

> NaviLens phải dán mã. GoodMaps phải quét toà nhà. Lazarillo phải lắp beacon.
> Chúng tôi đọc chính những tấm biển toà nhà đã có sẵn — không lắp gì, không xin
> phép ai, chi phí triển khai bằng không.

### Ba câu hỏi giám khảo sẽ hỏi, và câu trả lời

**"Cái này khác GoodMaps chỗ nào?"**
GoodMaps chính xác hơn, đã triển khai thật, và chúng tôi không định cạnh tranh
ở đó. Khác biệt là GoodMaps cần toà nhà trả tiền quét trước; còn chúng tôi chạy
được ở toà nhà chưa ai quét. Và GoodMaps không cảnh báo vật cản.

**"Sao phải cần laptop?"**
Đó là kiến trúc bản mẫu để gỡ lỗi nhanh trong 13 ngày. Toàn bộ logic đã tách
khỏi phần cảm biến, nên đưa về chạy trên máy là chuyển một lớp mỏng, không phải
viết lại. *(Nói thẳng, đừng vòng vo.)*

**"Đã có người khiếm thị nào thử chưa?"**
Trả lời thật. Nếu chưa thì nói chưa, nêu rõ đã liên hệ những đâu, và trình bày
kiểm thử bịt mắt như bước trung gian — **đừng bao giờ ngụ ý đã kiểm chứng**.

---

## 7. Cái gì thật sự mới, cái gì không

Tự phân loại cho trung thực, vì giám khảo kỹ thuật sẽ tự làm việc này.

| Thành phần | Mới? |
|---|---|
| Định vị trong nhà bằng VIO | **Không mới** — Clew, GoodMaps đã làm |
| Quét phòng dựng bản nền | **Không mới** — GoodMaps có chế độ tự quét |
| Chỉ đường bằng giọng nói, rung | **Không mới** — cả sáu đều có |
| Đọc **biển chữ sẵn có** làm mốc định vị | **Đáng gọi là mới** trong nhóm này |
| Cảnh báo vật cản **ngang tầm đầu** | **Đáng gọi là mới** — không app nào có |
| Mô hình độ tin cậy và quyền **từ chối nói** | **Đáng gọi là mới** trong nhóm này |
| Đặt trong bối cảnh **việc làm** | Mới so với sáu sản phẩm |

Ba dòng "đáng gọi là mới" là phần nên dành thời lượng pitch. Ba dòng đầu thì nên
nói ngắn và thừa nhận là nền đã có — cố nhận là phát minh sẽ bị bắt bài.

---

## Nguồn

- Project Guideline — [Google Research blog](https://research.google/blog/project-guideline-enabling-those-with-low-vision-to-run-independently/) · [mã nguồn mở](https://github.com/google-research/project-guideline) · [thông báo mở nguồn](https://research.google/blog/open-sourcing-project-guideline-a-platform-for-computer-vision-accessibility-technology/)
- Clew — [mã nguồn](https://github.com/occamLab/Clew) · [đánh giá của Perkins School for the Blind](https://www.perkins.org/resource/clew-navigation-app-review/) · [AbilityNet](https://abilitynet.org.uk/news-blogs/new-free-app-uses-apples-arkit-help-blind-find-way)
- GoodMaps — [cách hoạt động](https://goodmaps.com/how-it-works/) · [bản đồ LiDAR](https://goodmaps.com/newsroom/lidar-mapping-for-precise-indoor-navigation/) · [hướng dẫn tự quét](https://connect.goodmaps.com/docs/self-scanning-guide/)
- NaviLens — [Wikipedia](https://en.wikipedia.org/wiki/NaviLens) · [RNIB](https://www.rnib.org.uk/living-with-sight-loss/assistive-aids-and-technology/navigation-and-communication/navilens/) · [MTA New York](https://www.mta.info/accessibility/innovations/navilens) · [AFB AccessWorld](https://afb.org/aw/march2023/navilens)

Lazarillo và BlindSquare mô tả theo hiểu biết chung về sản phẩm, chưa tra nguồn
chính thức — **nên tự kiểm lại trước khi đưa số liệu cụ thể nào của hai app này
vào deck.**
