# FlowyX — kiến trúc bảo mật và dữ liệu

*Cập nhật 18/09/2026 · áp dụng cho bản v5*

Tài liệu này giải thích **dữ liệu nằm ở đâu, được bảo vệ bằng gì, và vì sao chọn cách đó**.
Nó viết cho người sẽ đọc lại mã sau sáu tháng, và cho giám khảo muốn kiểm chứng những gì
ứng dụng hứa trong Chính sách quyền riêng tư.

---

## 1. Một câu trả lời cho câu hỏi khó nhất

> *Ứng dụng có tài khoản, có mật khẩu, có "quên mật khẩu" — vậy máy chủ ở đâu?*

**Không có máy chủ nào cả.**

Tài khoản Flowy là một bản ghi SQLite trong vùng nhớ riêng của ứng dụng trên chính thiết bị
đó. Nó không đồng bộ, không khôi phục từ xa được, và không ai ngoài người cầm máy chạm tới
được.

Đây là một lựa chọn, không phải một thiếu sót. Thứ Flowy giữ — nhật ký, cảm xúc, việc chưa
làm được — là loại dữ liệu mà một vụ rò rỉ không sửa được bằng lời xin lỗi. Cách chắc chắn
nhất để không làm rò rỉ dữ liệu là **không bao giờ nhận nó**.

Cái giá phải trả được nói thẳng ở ba nơi trong ứng dụng (màn đăng ký, màn mã khôi phục,
và Cài đặt): mất mật khẩu và mất mã khôi phục là **mất dữ liệu**.

---

## 2. Bản đồ dữ liệu

| Dữ liệu | Nơi lưu | Bảo vệ |
|---|---|---|
| Họ tên, email, điện thoại | SQLite `nguoi_dung` | Vùng nhớ riêng của app |
| Mật khẩu | *không lưu* | Chỉ lưu băm PBKDF2-HMAC-SHA256, 210 000 vòng, muối riêng |
| Mã khôi phục | SharedPreferences `flowy_phien` | Chỉ lưu băm, cùng tham số |
| Kế hoạch, lịch | SQLite `ke_hoach` + prefs | Vùng nhớ riêng |
| **Nhật ký, cảm xúc** | SQLite `nhat_ky` | **AES-256-GCM**, khoá ở Android Keystore |
| Biên bản họp | SQLite `bien_ban` | Vùng nhớ riêng |
| Thời lượng, tiến độ | prefs | Vùng nhớ riêng |
| **Dữ liệu sức khoẻ** | SQLite `suc_khoe` | Như nhật ký, và tự xoá sau 7 ngày |
| Tuỳ chọn giao diện | prefs | — |

`android:allowBackup="false"` trong manifest: dữ liệu Flowy **không** lọt vào bản sao lưu
đám mây của Google hay của hãng máy. Nếu để mặc định `true`, toàn bộ nhật ký đã mã hoá sẽ
được đẩy lên Google Drive của người dùng — và khoá Keystore thì không đi theo, nên bản sao
lưu đó vừa vô dụng vừa là một bản sao dữ liệu nằm ngoài tầm kiểm soát.

---

## 3. Mật khẩu

### Tham số

```
Thuật toán   PBKDF2-HMAC-SHA256
Số vòng      210 000            (khuyến nghị OWASP 2023 cho SHA-256)
Muối         16 byte SecureRandom, riêng cho từng tài khoản
Khoá ra      256 bit
```

`KhoDuLieu.VONG` có một bài kiểm thử khoá con số này lại (`XacThucTest`). Hạ nó xuống là
hạ giá thành của một cuộc dò vét — nếu đổi, phải đổi có ý thức chứ không phải vì tối ưu tốc
độ đăng nhập.

### Vì sao không phải Argon2id

Argon2id tốt hơn PBKDF2 (kháng phần cứng chuyên dụng nhờ tốn bộ nhớ). Nhưng Android không
có sẵn Argon2, nên dùng nó nghĩa là nhúng một thư viện native (`.so` cho bốn kiến trúc, ~2 MB)
và tự nhận trách nhiệm vá nó. Với **đường build không Gradle** của dự án này thì còn thêm
một bước không tự động hoá được.

PBKDF2 210 000 vòng là khuyến nghị hiện hành của OWASP và có sẵn trong `javax.crypto`. Trong
bối cảnh cụ thể ở đây — bản băm chỉ nằm trên máy của chính người dùng, kẻ tấn công muốn dò
vét phải có máy đó trong tay và phải qua được khoá màn hình trước — chênh lệch giữa hai
thuật toán không đổi kết quả.

### So sánh hằng định

`KhoDuLieu.bangNhau` duyệt hết cả chuỗi dù đã lệch từ ký tự đầu. So sánh `==` thông thường
thoát ra ngay khi gặp khác biệt, và thời gian thoát đó rò rỉ thông tin về bao nhiêu ký tự
đầu đã đúng.

### Chậm dần thay vì khoá tài khoản

Sau 5 lần sai, mỗi lần sai tiếp phải chờ, thời gian chờ **gấp đôi** mỗi lần: 15 giây, 30,
60… tối đa 5 phút (`TaiKhoan.ghiNhanSai`).

Không khoá hẳn. Người ADHD gõ nhầm mật khẩu nhiều lần là chuyện thường, và đây là **máy của
họ** — khoá hẳn sẽ biến một lần lơ đãng thành mất sạch nhật ký. Chậm dần đủ để chặn dò tự
động, mà không biến một buổi tối tệ thành một mất mát vĩnh viễn.

---

## 4. Quên mật khẩu — và đường máy chủ nếu sau này có

### Cách đang dùng: mã khôi phục 12 ký tự

Sinh lúc đăng ký, hiện **đúng một lần**, máy chỉ giữ bản băm (cùng tham số PBKDF2). Bảng
chữ 32 ký tự **bỏ I, O, số 0 và số 1** — bốn ký tự người ta chép tay hay nhầm nhất.
12 ký tự trên bảng 32 ≈ **60 bit**: dò vét không thực tế, nhất là khi dùng chung bộ đếm
chậm dần với màn đăng nhập.

Màn hình hiện mã chặn nút Back, và bắt bấm "Tôi đã lưu mã" mới đi tiếp. Đổi mật khẩu thành
công thì **mã cũ hết hiệu lực ngay** và một mã mới được sinh ra — nếu không, người từng
nhìn trộm mã cũ vẫn mở được lần sau.

### Vì sao không gửi email

Gửi email cần khoá SMTP. Khoá nhét trong APK là **khoá công khai**: `apktool d flowy.apk`
rồi `grep` là ra. Dựng một nút "gửi mã về Gmail" với khoá nằm trong ứng dụng là mời người
khác dùng hạ tầng gửi thư của nhóm để gửi thư rác.

### Nếu sau này có máy chủ

Bản mẫu này không có, nhưng đặc tả sẵn để sau khỏi ứng biến:

1. Máy chủ **chỉ** giữ `email → băm(mã OTP), hết hạn, số lần thử`. Không giữ nhật ký, không
   giữ kế hoạch, không giữ gì khác.
2. OTP 6 số, hạn **10 phút**, tối đa 5 lần thử, một lần dùng.
3. Gửi qua nhà cung cấp giao vận thư (Postmark/SES), khoá nằm **ở máy chủ**, không ở APK.
4. Giới hạn tần suất theo email *và* theo IP; email không tồn tại vẫn trả lời giống hệt
   email tồn tại, để không lộ danh sách người dùng.
5. Dùng OTP để đặt lại **mật khẩu**, không phải để giải mã nhật ký — khoá nhật ký vẫn nằm
   trong Keystore của máy và vẫn không rời máy. Đặt lại mật khẩu từ máy khác **không** lấy
   lại được nhật ký cũ, và giao diện phải nói rõ điều đó trước khi người dùng bấm.

---

## 5. Mã hoá nhật ký

```
Thuật toán   AES-256-GCM          (có xác thực toàn vẹn, không chỉ bảo mật)
Khoá         sinh trong Android Keystore, alias `flowy_nhat_ky_v1`
IV           12 byte ngẫu nhiên, mới cho từng bản ghi, ghi kèm bản mã
Định dạng    "v1:" + base64(IV ‖ bản mã ‖ thẻ xác thực)
```

Khoá **sinh trong** Keystore và không bao giờ đi ra ngoài dưới dạng byte — ứng dụng gửi dữ
liệu *vào* Keystore để mã hoá chứ không lấy khoá *ra*. Trên phần lớn máy hiện nay, khoá nằm
trong vùng phần cứng tách biệt (TEE hoặc StrongBox) và không trích xuất được kể cả khi máy
đã root.

GCM chứ không phải CBC: GCM phát hiện được bản mã bị sửa. Với CBC, một byte bị lật sẽ ra
một đoạn văn bản rác mà ứng dụng vẫn hiển thị như thật.

Tiền tố `"v1:"` để sau này đổi thuật toán vẫn đọc được bản ghi cũ mà không phải đoán.

**Máy không có Keystore phần cứng**: rơi về khoá `SecureRandom` lưu trong vùng nhớ riêng của
app. Vẫn mã hoá, nhưng yếu hơn — và Cài đặt **nói thẳng** tình trạng đó ra (`MaHoa.nguyenVen`),
chứ không im lặng hiển thị một cái khoá màu xanh.

### Giới hạn thành thật

Bảo mật của Flowy dựa trên bảo mật của thiết bị. Máy không đặt khoá màn hình, hoặc bị root
và có phần mềm độc hại chạy quyền cao nhất, thì các lớp trên đều bị vượt qua. Chính sách
quyền riêng tư nói điều này ở mục 9 thay vì hứa hẹn quá lời.

---

## 6. Phần chưa kiểm thử tự động được

`XacThucTest` phủ các hàm thuần: băm, so sánh hằng định, kiểm email, độ mạnh, định dạng mã.
**157 bài kiểm thử pass, 0 lỗi.**

Không phủ được ở môi trường này, vì cần SQLite và Keystore thật của Android:

| Việc | Cách kiểm trên máy thật |
|---|---|
| `dangKy` / `dangNhap` / `doiMatKhau` | Tạo tài khoản, đăng xuất, đăng nhập lại, đổi mật khẩu, đăng nhập lại |
| Mã khôi phục | Đăng ký → chép mã → quên mật khẩu → nhập mã → đặt mật khẩu mới |
| Mã hoá nhật ký | Viết một mục, dùng `adb` đọc thẳng tệp `.db`, xác nhận thấy bản mã chứ không thấy chữ |
| Xoá tài khoản | Xoá, rồi kiểm tra bảng rỗng và alias Keystore đã mất |
| Health Connect | Máy Android 14, bật/tắt kết nối, xác nhận bảng `suc_khoe` rỗng sau khi tắt |

---

## 7. Dữ liệu sức khoẻ

Sáu nguyên tắc, cài đặt trong `SucKhoe.kt` chứ không chỉ viết trong chính sách:

1. **Chỉ đọc.** Không có quyền `WRITE_*` nào trong manifest.
2. **Chỉ loại đã tích.** `SucKhoe.quyenCan` sinh danh sách quyền từ chính các ô người dùng chọn.
3. **Chỉ tổng theo ngày.** Bản ghi thô được cộng lại ngay tại chỗ, không bao giờ lưu.
4. **Chỉ 7 ngày.** `donNgayCu` chạy sau mỗi lần làm mới.
5. **Không ra khỏi máy.** Không có đường mạng nào chạm vào bảng này.
6. **Tắt là xoá.** `SucKhoe.tat` gọi `xoaHet` trong cùng một hàm — hai việc không tách rời được.

Ba nguyên tắc 3, 4 và 6 khiến Flowy **không thể** trở thành một kho hồ sơ sức khoẻ, ngay cả
khi ai đó sau này muốn biến nó thành thế.

**HIPAA**: luật Hoa Kỳ này áp dụng cho các đơn vị được điều chỉnh (cơ sở y tế, hãng bảo
hiểm, đối tác của họ). Flowy không phải một trong số đó, và dữ liệu người dùng tự ghi vào
một ứng dụng cá nhân không phải "thông tin sức khoẻ được bảo vệ" theo nghĩa pháp lý. Dù
vậy, các biện pháp kỹ thuật tương đương mức HIPAA yêu cầu — mã hoá khi lưu trữ, kiểm soát
truy cập, tối thiểu hoá dữ liệu — vẫn được áp dụng, vì đó là cách đúng để đối xử với loại
thông tin này.

**GDPR Điều 9**: dữ liệu sức khoẻ thuộc nhóm đặc biệt. Cơ sở pháp lý duy nhất được dựa vào
là **sự đồng ý rõ ràng**, nên nó có màn hình riêng chứ không phải một công tắc trong danh
sách, và thời điểm đồng ý được ghi lại (`SucKhoe.dongYLuc`) để chứng minh được.

---

## 8. Quyền của người dùng

GDPR (EU), Nghị định 13/2023/NĐ-CP (Việt Nam) và các luật tương đương cho người dùng quyền
truy cập, sửa, xoá, hạn chế xử lý và mang dữ liệu đi. Trong Flowy, những quyền này không cần
đơn từ vì dữ liệu nằm trong tay họ:

| Quyền | Trong ứng dụng |
|---|---|
| Truy cập, sửa | Mở app |
| Xoá | Cài đặt → Tài khoản → Xoá tài khoản (gõ chữ xác nhận) |
| Mang đi | Cài đặt → Xuất dữ liệu ra tệp (JSON, qua Storage Access Framework) |
| Phản đối xử lý | Gỡ ứng dụng |

Tệp xuất ra là **bản rõ** — khoá không rời khỏi máy được, và một tệp không ai giải được thì
xuất ra vô nghĩa. Hộp thoại nói điều đó **trước** khi người dùng chọn nơi lưu, không phải sau.

---

## 9. Danh sách quyền, và vì sao từng cái có mặt

| Quyền | Vì sao |
|---|---|
| `INTERNET` | Chỉ cho phần chia nhỏ việc gọi Gemini, khi bản cài có khoá API. Gửi đúng tên việc và mô tả người dùng gõ — không nhật ký, không sức khoẻ, không tài khoản |
| `VIBRATE` | Phản hồi không cần âm thanh, dùng được ở chỗ đông người |
| `POST_NOTIFICATIONS` | Từ API 33, thiếu nó thì `notify()` im lặng không báo lỗi |
| `SCHEDULE_EXACT_ALARM` | Từ Android 14 tắt mặc định; thiếu nó app sập khi đặt lời nhắc |
| `RECEIVE_BOOT_COMPLETED` | Đặt lại chuông sau khi khởi động máy |
| `health.READ_SLEEP`, `health.READ_STEPS` | Chỉ xin khi người dùng bật kết nối sức khoẻ |

**Không có** camera, micro, vị trí, danh bạ, bộ nhớ ngoài. Danh sách quyền là bằng chứng kiểm chứng
được cho những gì chính sách quyền riêng tư nói — nó khó chối hơn một đoạn văn.
