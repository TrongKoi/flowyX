# FlowyX v5 — nền tảng hệ thống thiết kế

Cập nhật 18/09/2026. Tài liệu này ghi các quyết định **đã đưa vào code**, không phải đề xuất.
Phần giao diện v4 vẫn đúng; xem `GIAO_DIEN_V4.md` cho những gì không nhắc lại ở đây.

---

## 1. Bảng màu đêm — viết lại hoàn toàn

Bản v4 chỉ hạ sáng bảng màu ngày rồi giảm bão hoà: nhìn ra vẫn là *"bản sáng bị tối đi"*.
Bản v5 đổi **cách phân vai** của màu, không chỉ đổi độ sáng:

| | Bản sáng | Bản đêm |
|---|---|---|
| Nền | giấy kem `#FEF4EF` | **mực navy** `#121320` |
| Chữ | mực navy | ngà lạnh `#E8E6F0` |
| Vàng/cam | mảng nền lớn (khối kế hoạch, nút chính) | **chỉ còn vệt nhấn nhỏ** |
| "Bấm được" | navy dịu `#57536E` | **tím oải hương** `#A99BF0` |

### Bốn tầng bề mặt

| Token | Hex | Dùng cho | Độ sáng L |
|---|---|---|---|
| `nen` | `#121320` | nền màn hình | 0.007 |
| `the` | `#1B1C2B` | thẻ | 0.012 |
| `the_2` | `#24263A` | thẻ nổi trong thẻ | 0.021 |
| `the_3` | `#2D3050` | hộp thoại, bottom sheet | 0.033 |

Trên nền tối bóng đổ gần như vô hình, nên "cao hơn" phải thể hiện bằng **sáng hơn** —
cách Material Dark vẫn làm.

### Vì sao tím oải hương cho thành phần bấm được

- Vàng và cam trên nền tối **rung** và hút mắt liên tục. Đúng thứ người ADHD dễ bị kéo đi.
- Tím lạnh trả về đúng một việc: *"cái này bấm được"*.
- Vẫn thuộc họ màu của logo (navy → tím), không lạc bộ nhận diện.
- Người mù màu đỏ-lục vẫn phân biệt được tím với vàng/cam.

### Tương phản đã đo (WCAG 2.1)

| Cặp màu | Tỉ lệ | Chuẩn |
|---|---|---|
| chữ / nền | 14,92:1 | AAA |
| chữ / thẻ | 13,63:1 | AAA |
| chữ / thẻ tầng 3 | 10,31:1 | AAA |
| chữ phụ / nền | 7,32:1 | AAA |
| tím "bấm được" / nền | 7,58:1 | AAA |
| vàng nhấn / nền | 10,20:1 | AAA |
| chữ trên nút vàng | 9,93:1 | AAA |
| cam / thẻ | 6,50:1 | AA |

Nền **không** phải đen tuyệt đối: chữ trắng trên đen cho 21:1, làm nét chữ "loé"
(halation) và mỏi mắt khi nhìn lâu.

---

## 2. Logo trên nền đêm — bản nghịch đảo sinh tự động

Logo thật là **mực navy `#29293E`**. Trên nền đêm nó chỉ còn **1,3:1** — coi như tàng hình.

### Bản trước đã sai ở đâu

Bản v5 đầu tiên đặt logo lên một **phiến nền màu kem**. Tệp logo giữ nguyên, tương phản
lên 13,1:1, về mặt số đo thì đạt. Nhưng nhìn thì không: giữa một màn hình mực đêm, một
miếng kem sáng trắng đứng riêng ra như miếng dán, không như một phần của giao diện. Nhóm
phản hồi đúng chữ *"thiếu chuyên nghiệp"* — và đó là nhận xét về **cảm giác**, thứ mà
bảng đo tương phản không nói được.

### Cách đang dùng: nghịch đảo theo quy tắc, không vẽ lại

| Cách | Vấn đề |
|---|---|
| Tô trắng logo bằng `tint` | Mất hai giọt vàng/cam, còn lại một vệt trắng. Đây là **sửa logo**. |
| Đặt logo lên phiến kem | Miếng dán sáng giữa nền đêm. Đã thử, đã bỏ. |
| **Bản nghịch đảo sinh tự động** ✔ | Tệp gốc không ai chạm vào. Mực navy → ngà, vàng/cam giữ nguyên tuyệt đối. |

Quy tắc chuyển màu nằm trong `android/tools/logo_dem.py`, chạy trên chính tệp gốc:

```python
if r - b > 25:        # điểm ảnh ngả vàng/cam  -> GIỮ NGUYÊN
    giu(diem)
else:                 # mực navy và khử răng cưa -> đổi sang ngà
    doi(diem, (232, 230, 240), giu_alpha=True)
```

Ngưỡng `r - b > 25` tách được hai giọt thương hiệu khỏi phần chữ mà không cần chọn tay
từng vùng: vàng `#FFD400` có `r - b = 255`, cam `#F58A07` có `r - b = 238`, còn navy
`#29293E` có `r - b = -21`. Alpha giữ nguyên nên viền khử răng cưa vẫn mượt, không bị
rỗ ở cỡ nhỏ.

Kết quả ra năm mật độ, chọn bởi hệ điều hành, **không một dòng Kotlin nào**:

```
res/drawable-night-mdpi/logo_ngang.png     ...  -xxxhdpi
res/drawable-night-*/logo_dau.png          (đầu logo cho màn mở app)
res/layout/khoi_logo.xml                   ImageView trần, không phiến, không lề
```

| Nền | Mực | Tương phản |
|---|---|---|
| Sáng `#FEF4EF` | navy `#29293E` bản gốc | **12,8:1** |
| Đêm `#121320` | ngà `#E8E6F0` bản nghịch đảo | **14,9:1** |

Hai giọt vàng/cam giống hệt nhau ở cả hai bản — đó là phần người ta nhận ra thương hiệu,
và nó không đổi một điểm ảnh. Tệp gốc `thiet_ke/logo/` không bị sửa; bản đêm **sinh ra
từ nó** và sinh lại được bất cứ lúc nào bằng một lệnh.

Biểu tượng app ngoài màn hình chính giữ nền kem cố định ở cả hai chế độ, nên cũng không chìm.

---

## 3. Ba phông chữ — đã kiểm dấu tiếng Việt

Đo bằng fontTools trên bộ **74 ký tự tiếng Việt khó nhất** (ă â ê ô ơ ư đ + nguyên âm có
dấu + chữ hoa có dấu):

| Phông | Thiếu | Kết luận |
|---|---|---|
| Lexend | 0/74 | ✔ mặc định |
| **Andika** (SIL) | 0/74 | ✔ cho người khó đọc |
| Inter | 0/74 | ✔ nét trung tính |
| Atkinson Hyperlegible Next | **50/74** | ✘ loại |
| OpenDyslexic | thiếu | ✘ loại |

Hai phông "dyslexia" nổi tiếng nhất **không dùng được cho tiếng Việt**: chữ sẽ hiện ô
vuông, hoặc hệ thống trộn hai phông trong một từ — tệ hơn là không đổi phông.

Andika do SIL làm cho người mới học đọc: chữ rộng, a/g một tầng, b/d/p/q khác hẳn nhau,
và có đủ dấu. Đây là lựa chọn thay thế đúng nghĩa cho Atkinson.

Tệp đã **cắt bớt ký tự** (subset Latin + tiếng Việt) để APK không phình: Andika 669 KB →
197 KB, Inter 341 KB → 92 KB. Giấy phép OFL cho phép việc này; bản quyền ghi trong
`assets/fonts/OFL-*.txt`.

---

## 4. Cỡ chữ giãn cả layout

Đổi riêng cỡ chữ thì chữ to ra còn nút, lề và vùng chạm giữ nguyên — chữ tràn ra ngoài nút.
`GiaoDien.apCoChu` nhân **cùng một hệ số** (0,9 / 1,0 / 1,15) cho:

- kích thước chữ,
- `minHeight` và chiều cao cố định của view,
- padding bốn phía.

Mỗi view được đánh dấu bằng tag `R.id.tag_da_gian` để không bị nhân hệ số hai lần khi
màn hình vẽ lại.

---

## 5. Rung bốn mức

| Mức | Biên độ | Độ dài một chạm |
|---|---|---|
| Tắt | — | — |
| Nhẹ | 60/255 | 8 ms |
| Vừa | 130/255 | 14 ms |
| Mạnh | 210/255 | 22 ms |

Mức **Vừa** đi qua `View.performHapticFeedback` để tôn trọng cài đặt "Phản hồi chạm" của
máy. Hai mức kia cần biên độ khác mặc định nên phải qua `Vibrator`.

**Rung luỹ tiến** khi kéo vòng đồng hồ: biên độ đi từ 40% đến 100% của mức người dùng
chọn, độ dài 6–14 ms, **trần cứng 30 ms**. Người chọn mức Nhẹ thì trần cũng thấp theo —
"luỹ tiến" không bao giờ vượt quá cái họ đã chọn.

---

## 6. Đồng hồ tập trung — cơ chế Tiimo

- Vành khắc **120 vạch** (mỗi vạch 30 giây), cứ 10 vạch có một vạch dài (mốc 5 phút).
- Vạch vẽ **đè lên** vành bằng màu nền nên trông như khắc vào — giống ảnh tham chiếu.
- Một vòng = 60 phút; giờ thứ hai là vành mỏng bên ngoài. Tối đa 2 tiếng.
- **Không hiện giây.** Giữa chỉ có số phút; dưới một phút ghi "Sắp xong".
- Mặt chỉ ghi **bốn mốc 15 / 30 / 45 / 60**. Một tiếng hiện là "60", không phải "60:00".
- Màu đổi theo chặng: còn nhiều → tím lạnh, còn ≤45 phút → vàng, còn ≤10 phút → cam.
- Phím tắt: **5 phút · 15 · 30 · 1 tiếng · 2 tiếng**.
- Đang chạy: nút đổi thành **"+1 phút"** và **"Dừng lại"**.
- Hết giờ: 44 hạt giấy rơi 1,8 giây + hai nhịp rung. Không chớp sáng, không âm thanh,
  và tôn trọng cài đặt "Xoá hiệu ứng" của hệ thống (hệ số animation = 0 thì bỏ qua hẳn).

Vì sao **mặt tuyệt đối 60 phút** chứ không phải vòng luôn đầy lúc bắt đầu: 15 phút lúc nào
cũng là một phần tư vành, nên sau vài lần dùng, "một phần tư" trở thành một kích thước
quen. Với vòng luôn đầy thì 15 phút và 90 phút trông y hệt nhau lúc bắt đầu — không học
được gì.

---

## 7. Song ngữ Việt / Anh

- `values/strings.xml` (vi) và `values-en/strings.xml` — **298 chuỗi + 2 mảng**, đã kiểm
  khớp khoá và khớp tham số `%1$s`.
- `NgonNgu.boc()` gọi trong `attachBaseContext` của mọi Activity. Chọn "Theo máy" thì
  hàm trả về context gốc, **không** tạo context mới.
- Đổi ngôn ngữ trong Cài đặt gọi `recreate()` đúng một lần, do người dùng chủ động —
  không nằm trong vòng lặp nào. Đây là chỗ bản v3 từng làm app văng trên Galaxy Tab, nên
  nó được giới hạn chặt.
- Màn hình phía sau tự vẽ lại ở `onResume` nhờ so `GiaoDien.dauVet()`, nên **không cần
  mở lại app**.

---

## 8. Thanh tab kính lỏng

Một **viên thuốc dùng chung** cho cả năm tab thay vì năm viên bật/tắt. Nó **trượt** từ tab
cũ sang tab mới — kể cả khi hai tab là hai Activity khác nhau: Activity đi truyền lại chỉ
số tab cũ qua Intent (`ThanhTab.TU_TAB`), Activity đến đặt viên thuốc ở chỗ cũ rồi mới
trượt về chỗ mình. Hai khung hình nối nhau không có hiệu ứng chuyển cảnh, nên mắt đọc đó
là một thanh tab liên tục.

**Kéo ngang** trên thanh tab là đường thứ hai, không thay đường chạm: viên thuốc bám theo
ngón tay, **nhảy từng nấc** (không trượt mượt — nấc là thứ cho biết mình đang ở đâu mà
không phải nhìn), giãn ra `1,18×` rồi co về mỗi lần qua một tab, và rung một nấc. Thả ra
mới chuyển, nên **đổi ý được** — thứ mà chạm không cho.

Nền kính: `drawable/nen_kinh.xml`, ba lớp — tấm màu thẻ ở độ trong 94% (92% ở nền đêm),
một đường kẻ trên, một vạch trắng mờ ngay dưới nó.

**Không làm mờ thật**, và đây là lý do: Android chỉ làm mờ được phía sau một *cửa sổ*
(`Window.setBackgroundBlurRadius`, API 31+), không làm mờ được phía sau một View trong
cùng cửa sổ. `RenderEffect.createBlurEffect` làm mờ *chính* view đó — dùng vào đây sẽ làm
mờ cả icon tab. Ép cho có mờ thật thì phải biến thanh tab thành một cửa sổ riêng: thêm một
lớp nhận chạm, một chỗ để lệch vị trí khi bàn phím hiện lên, và một đường để sập trên máy
cũ. Cái giá đó không đáng cho một hiệu ứng.

---

## 9. Xác thực và cơ sở dữ liệu

Chi tiết đầy đủ ở **`docs/BAO_MAT.md`**. Tóm tắt phần nhìn thấy được:

| Màn hình | Điều đáng chú ý |
|---|---|
| Mở app | Đầu logo lướt 620 ms, tôn trọng "Xoá hiệu ứng" của hệ thống |
| Chọn ngôn ngữ | Chỉ hiện một lần, hai lựa chọn, không có nút Bỏ qua |
| Đăng nhập | Giữ để xem mật khẩu (một thao tác, không thể quên ở trạng thái hiện) |
| Đăng ký | Thanh độ mạnh **gợi ý chứ không chặn**; điện thoại ghi rõ "không bắt buộc" |
| Mã khôi phục | Hiện **đúng một lần**, nút Back bị chặn, bảng chữ bỏ I O 0 1 |
| Quên mật khẩu | Mã khôi phục → mật khẩu mới; lối thoát cuối là xoá sạch, hỏi **hai lần** |

Không có xác thực hai bước và không có "gửi link đặt lại qua email" — **không có máy chủ
nào để gửi**. Khoá SMTP nhét trong APK là khoá công khai: ai giải nén APK cũng đọc được.
Nói thẳng điều đó trong giao diện tốt hơn là dựng một nút không hoạt động.

---

## 10. Cài đặt ba nhóm

**Tài khoản** · **Bảo mật & Dữ liệu** · **Hệ thống & Trợ năng**.

Ba, không phải năm: quá bốn nhóm thì bản thân việc chọn nhóm lại thành một bước phải nghĩ.
Ba nhóm là ba câu hỏi khác nhau — *"tôi là ai"*, *"dữ liệu của tôi thế nào"*, *"app hiện
ra sao"* — và gần như mọi thứ cần tìm đều rơi rõ ràng vào một trong ba.

Màn hình dựng bằng mã chứ không bằng XML, vì nó đổi hình theo trạng thái và phải **vẽ lại
tức thì** khi người dùng kéo thanh cỡ chữ: kéo tới đâu chữ to tới đó, ngay trong lúc ngón
tay còn đang cầm thanh trượt, không phải đoán rồi bấm Lưu.

Chế độ tối **không có công tắc riêng** — nó theo máy. Công tắc tự đổi ở bản v3 làm sập
Galaxy Tab S7 FE, và một cài đặt gây sập thì không đáng có.

---

## 11. Sức khoẻ, pháp lý, xuất dữ liệu

**Sức khoẻ** có màn hình đồng ý riêng, không phải một công tắc trong danh sách. Dữ liệu
sức khoẻ là nhóm đặc biệt theo Điều 9 GDPR: cơ sở pháp lý duy nhất là *sự đồng ý rõ ràng*,
mà một công tắc nằm lẫn giữa mười công tắc khác thì không phải thế. Sáu nguyên tắc (chỉ
đọc, chỉ loại đã tích, chỉ tổng theo ngày, chỉ 7 ngày, không ra khỏi máy, tắt là xoá) nằm
ngay trên màn hình đó, không giấu trong chính sách.

Android 14 đọc qua `android.health.connect` — API **nằm trong hệ điều hành**, không kéo
theo thư viện AndroidX nào, nên đường dựng không-Gradle vẫn chạy. Toàn bộ mã chạm vào nó
nằm riêng trong `SucKhoeHC.kt`, vì máy Android 7 không bao giờ được nạp lớp đó.

**Điều khoản sử dụng** và **Chính sách quyền riêng tư** là văn bản đầy đủ trong `res/raw`
(và `res/raw-en`), dựng ra bằng `TextView` chứ không phải `WebView` — nên chúng dùng đúng
màu, đúng phông và đúng cỡ chữ người dùng đã chọn.

**Xuất dữ liệu** ra JSON qua Storage Access Framework: người dùng chọn nơi lưu, app không
xin quyền đĩa nào. Hộp thoại nói thẳng tệp xuất ra là **bản rõ** — khoá mã hoá không rời
khỏi máy được, và một tệp không ai giải được thì xuất ra làm gì.

---

## 12. Kiểm chứng

| Việc | Kết quả |
|---|---|
| Biên dịch Kotlin (API 34) | sạch, 55 tệp nguồn, 0 lỗi |
| Test Kotlin | **157 pass, 0 lỗi** (145 cũ + 12 mới cho phần xác thực) |
| Khớp chuỗi vi ↔ en | 475/475, không lệch tham số format (đã dọn 51 chuỗi chết) |
| Dấu tiếng Việt của 3 phông | 0/74 thiếu, đo bằng fontTools |
| Tương phản bảng đêm | đo từng cặp, bảng ở §1 |
| APK | **1,2 MB**, chữ ký hợp lệ, `aapt` **0 cảnh báo**, có `values-night`, `values-en`, `raw-en`, 3 phông |
| Bản xem trước HTML | 26 khung, 0 lỗi JS, dựng thử bằng Chromium |
| Swift | 35 tệp, qua `tools_kiem_swift.py` |

## 13. Còn lại

Bản Android đã đủ cả 11 mục trên. Bản **iOS** mới theo kịp phần nền: bảng màu đêm v5,
bốn nấc rung, ba phông và hệ số cỡ chữ. Phần còn lại của iOS — xác thực, kho mã hoá,
cử chỉ vuốt, tab Kế hoạch, bộ chọn trống cuộn, màn sức khoẻ — cần một máy Mac có Xcode
để dựng và thử, nên để nguyên thay vì viết mù.

Hai việc cần máy thật, không giả lập được ở đây:

- Chạy thử trên Galaxy Tab S7 FE (máy từng sập ở v3) và một máy Android 14 có Health Connect.
- Đo lại rung bốn nấc trên ít nhất hai máy khác hãng — ngưỡng cảm nhận chênh nhau rất nhiều.
