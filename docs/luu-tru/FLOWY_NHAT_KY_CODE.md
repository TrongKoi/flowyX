# Nhật ký code Flowy

Ghi lại **đã viết gì, xoá gì, và vì sao** trong đợt làm lại sau khi bỏ
điều hướng. Thiết kế nằm ở [`FLOWY_THIET_KE.md`](../FLOWY_THIET_KE.md);
file này là phần thực thi.

> **Đợt 1 — 15/09/2026.** Test: 540 → **230**. Giảm là đúng: phần lớn
> test cũ thuộc về hệ dẫn đường vừa cắt. Số test **cho phần ADHD** tăng
> từ 6 file lên 8 file.

---

## 1. Đã xoá

### 1.1. Mười ba module điều hướng

`loi_chung/`: `anchors`, `arcore`, `depth`, `floormap`, `floors`,
`geometry`, `guidance`, `localizer`, `objects`, `routing`, `signtext`,
`vio`, `profile`

`adhd/`: `places` (đánh dấu địa điểm), `preview` (xem trước lộ trình)

Kèm theo: `run_bridge.py`, mười công cụ trong `tools/`, toàn bộ
`config/` (bản đồ tầng, bàn làm việc, bảng điều khiển), và mười một file
test của chúng.

### 1.2. `power.py` — không chuyển được, khác với dự đoán trong thiết kế

Tài liệu thiết kế §5.1 xếp `power.py` vào nhóm **giữ lại**. Khi dùng
thật thì không được: chữ ký của nó là

```python
cap_nhat(gan_nhat_m, da_di_m, dinh_vi_tot, nhiet_c)
```

Ba trong bốn tham số là số liệu của hệ dẫn đường, và cả cơ chế phân tầng
của nó (độ sâu → nhận diện → OCR) cũng vậy. Không có gì để chuyển sang.

Thay bằng **hai hằng số** trong `run_flowy.py`: đang làm việc thì gửi
gói tin dày hơn, không thì gửi thưa. Mục đích còn lại chỉ là tiết kiệm
pin, không phải giảm độ trễ — Flowy không có việc nặng nào chạy mỗi gói
tin.

---

## 2. Đã viết mới

### 2.1. `adhd/phien.py` — ý định thực thi và các bước

Ba ô **bắt buộc**: khi nào / ở đâu / việc gì. `tao_y_dinh()` trả `None`
nếu thiếu một ô.

Ràng buộc đó chính là can thiệp, không phải phiền phức: một ý định mơ hồ
là thứ không khởi động được, nên buộc người dùng làm nó cụ thể **trước**
là gỡ tê liệt trước khi nó kịp hình thành.

Hệ quả có chủ ý: **không có hàm "thêm việc nhanh"**. Thêm nhanh thì ra
một dòng chữ mơ hồ.

Một test khoá một quyết định thiết kế khác: `Phien` **không có** hàm
`nhay_toi(n)`. Nhảy qua bước là mất luôn phản hồi của những bước bị bỏ,
mà phản hồi từng bước chính là cơ chế chống tê liệt.

### 2.2. `adhd/thoiluong.py` — sổ thời lượng, học từ người dùng

Đây là thứ phân biệt Flowy, theo §3.1 của thiết kế.

**Không hỏi "việc này mất bao lâu" rồi tin lời người dùng.** Ước lượng
sai thời lượng chính là triệu chứng cần chữa.

```
lần 1    Người dùng ước. Ghi lại cả con số đó, VÀ đo thời gian thật.
lần 2    "Lần trước bạn ước 20 phút, thực tế 35 phút."
lần 3+   Dùng số đo thật.
```

Ba quyết định trong đó:

**Trung vị, không phải trung bình.** Một lần bị gián đoạn bất thường —
mất điện, có người gọi — kéo trung bình lệch hẳn. Cùng lý do đã dùng cho
`backdrop.py` bên hệ dẫn đường.

**Chỉ xét 5 lần gần nhất.** Lấy hết lịch sử thì một tháng sau vẫn bị kéo
bởi những lần vụng về đầu tiên.

**Lệch dưới 5 phút thì im lặng.** Ước 20 thực tế 22 là ước *đúng*. Nói ra
một chênh lệch không đáng kể sẽ làm câu cảnh báo mất giá trị ở những lần
thật sự lệch nhiều.

Và một test khoá ranh giới y tế: câu đối chiếu **chỉ nêu số liệu**,
không có "bạn hay ước thiếu" — đó là nhận xét về tính cách, tức là một
bước sang đánh giá.

**Module này không tự ghi ra đĩa**, và có test quét mã nguồn để chắc.
Tên công việc là nội dung cá nhân; điện thoại sở hữu tệp lưu, laptop chỉ
nhận phần cần cho lần tính này (§7.3 của thiết kế).

### 2.3. `run_flowy.py` — runner mới

Thay `run_bridge.py` (775 dòng) bằng khoảng 300 dòng.

Bốn việc, theo thứ tự ưu tiên khi nhiều thứ cùng muốn lên tiếng:

| # | Việc | Vì sao thứ tự này |
|---|---|---|
| 1 | Trả lời cú chạm vào nhân vật | Người dùng vừa hỏi, phải trả lời |
| 2 | Dựng lại ngữ cảnh sau phân tâm | Câu này bị nuốt thì mất hẳn |
| 3 | Phản hồi xong bước | Rung nhẹ, không chiếm kênh tai |
| 4 | Nhắc mốc thời gian | Qua bộ đệm chống lặp |

**Tín hiệu phân tâm đổi từ chuyển động sang tiền cảnh.** Bản dẫn đường
dùng `MucHoatDong.NGHI` (đứng yên). Flowy dùng `tren_man_hinh` — app ra
khỏi tiền cảnh. Mở app khác **chính là** định nghĩa thực tế của "bị sao
nhãng" ở bối cảnh này, và nó chính xác hơn đo chuyển động nhiều.

### 2.4. `dongvien.BoDoiTuThe` — nhân vật tự làm việc của nó

Theo §2.6 của bản mô tả nhân vật.

Đổi tư thế **rời rạc**, ngẫu nhiên 3–8 phút; **giãn ra 8–15 phút khi
người dùng đang tập trung** — đồng điều hoà nhìn thấy được.

Hai chi tiết nhỏ nhưng cần:

- **Không bao giờ đổi vào chính tư thế hiện tại** — người dùng không
  thấy gì, và lần đổi đó bị phí.
- **Bộ sinh ngẫu nhiên riêng**, không dùng `random` toàn cục: một module
  khác gieo lại hạt giống sẽ làm nhịp của nhân vật đổi theo, và đó là
  loại phụ thuộc ngầm rất khó tìm.

Chạy thử 4000 giây: đổi 11 lần (~364 giây/lần, đúng khoảng), không lần
nào đổi vào chính nó.

### 2.5. `tests/loi_chung/test_cau_chu.py` — canh gác câu chữ

Thay `test_tts_tieng_viet.py` (cả 5 bài đều kiểm chuỗi điều hướng).

Giữ phần quý nhất của file cũ: cách kiểm dấu **theo câu** chứ không theo
danh sách âm tiết. Danh sách âm tiết đã từng báo động giả ngay — "thang"
trong "Cầu thang" là từ viết đúng.

Thêm **bốn quy tắc tránh diện thiết bị y tế** (§4.4 của thiết kế) thành
test tự động: không tên bệnh, không khẳng định về tình trạng người dùng,
không điểm số, không hứa hẹn điều trị.

Kiểm **cả hai chiều**: quét chuỗi trong mã nguồn (bắt chuỗi chết trong
nhánh không chạy tới) *và* chạy thật các hàm sinh câu (bắt chuỗi ghép từ
nhiều mảnh).

**Một lỗi trong chính bài test, tìm ra khi chạy.** Bản đầu phân biệt
docstring với câu nói bằng độ dài — *"docstring thì dài và nhiều dòng"*.
Sai ngay: docstring một dòng ngắn hơn ngưỡng nên lọt qua, rồi bài test
báo nó là câu nói mất dấu. Đã sửa sang nhận diện theo **cấu trúc cú
pháp** — lệnh đầu tiên của module/lớp/hàm. Cấu trúc thì không đoán gì cả.

Và một bài canh gác cho chính bộ canh gác: nếu ai đó làm rỗng một danh
sách từ cấm thì mọi bài trên vẫn xanh mà không còn kiểm gì — loại hỏng
im lặng tệ nhất.

---

### 2.6. Ba nhóm y tế — `nhacviec.py`, `nhatky.py`, `cauhoi.py`

Bước 7 của §6. Khuôn ở §4.3 của thiết kế, và điều quyết định cách cả ba
module được viết là **chỗ đặt quyết định**:

> App cung cấp **năng lực**. Người dùng quyết định dùng vào việc gì.

Hướng dẫn *General Wellness* của FDA (bản 06/01/2026) nêu đích danh
"nhắc thuốc hoặc theo dõi triệu chứng gắn với chẩn đoán". Chữ khoá là
**gắn với chẩn đoán**. Chỗ nào app biết cái nó đang nhắc là thuốc gì,
hoặc quy một ghi chép về một thang đo lâm sàng, chỗ đó nó vượt ranh.

#### (a) `adhd/nhacviec.py` — lời nhắc theo giờ, người dùng tự đặt tên

`SoNhac` giữ danh sách `LoiNhac(ten, gio, lap_lai_hang_ngay)`. `ten` là
chuỗi **tự do**: module không phân tích, không đối chiếu danh mục nào, và
không lưu ý nghĩa nào khác ngoài chính chuỗi đó.

Bốn thứ **không làm**, mỗi thứ có một bài test khoá lại:

| không làm | vì sao |
|---|---|
| danh mục thuốc, tên hoạt chất | biết tên thuốc là biết chẩn đoán |
| tính liều, nhắc theo phác đồ | đó là hướng dẫn điều trị |
| đếm "tỷ lệ tuân thủ" | đó là theo dõi để quản lý bệnh |
| cảnh báo bỏ liều | đó là cảnh báo lâm sàng |

Điều thứ ba đáng chú ý nhất: module **không ghi nhận** người dùng có làm
theo lời nhắc hay không. Không có trường `da_lam`, không có thống kê.
`test_KHONG_dem_ty_le_tuan_thu` kiểm bằng `hasattr` để nó không lặng lẽ
quay lại.

Và có lý do thực tế, không chỉ lý do pháp lý: bảng research của nhóm ghi
một thử nghiệm ngẫu nhiên trên 73 người lớn trong 3 tháng cho thấy app
nhắc thuốc **không cải thiện có ý nghĩa** chỉ số sở hữu thuốc. Bỏ phần
đếm tuân thủ là bỏ một thứ vừa rủi ro vừa chưa có bằng chứng.

Cửa sổ báo là 30 phút (`CUA_SO_PHUT`): trễ trong cửa sổ thì vẫn báo, quá
thì thôi. Không báo mãi — một lời nhắc hiện liên tục sẽ bị tắt đi, và
lúc đó mọi lời nhắc khác cũng mất theo.

#### (b) `adhd/nhatky.py` — nhật ký của người dùng, app không diễn giải

Ranh giới quyết định cả phần pháp lý lẫn phần thiết kế nằm ở một chỗ:

| ghi chép | theo dõi |
|---|---|
| người dùng viết, đọc lại, và **tự** rút ra kết luận | app đo lường, chấm điểm, và rút ra kết luận **hộ** người dùng |

Cái thứ nhất là một quyển sổ. Cái thứ hai là một thiết bị y tế.

Nên module này **không có phép tính nào**. Không trung bình, không xu
hướng, không "tuần này bạn kém hơn tuần trước". Thứ duy nhất nó làm với
nội dung người dùng viết là **sắp xếp theo thời gian** và **in ra**.

Cảm xúc ghi bằng **chữ**, không phải thang điểm. Thang 1–5 tiện cho app
hơn nhiều — dễ lưu, dễ vẽ biểu đồ — và đó chính xác là lý do không dùng
nó: một con số chỉ có ích khi có gì đó cộng nó lại, mà cộng lại chính là
thứ không được làm. `"mệt"`, `"ổn"`, `"như bị kéo từng mảnh"` hợp lệ như
nhau. Chữ cũng trung thực hơn: *"3 trên 5"* giả vờ là một phép đo;
*"sáng thì ổn, chiều thì không"* là thứ người dùng thật sự biết.

`xuat_van_ban()` trả về **một chuỗi**. Nó không mở tệp, không gọi mạng,
và không biết tệp sẽ đi đâu. Người dùng có thể muốn đưa sổ cho bác sĩ —
đó là việc của họ và nó hữu ích — nhưng bước "gửi" phải nằm trong tay
họ, không nằm trong code.

Giới hạn 500 mục là giới hạn **riêng tư**, không phải giới hạn kỹ thuật:
một quyển sổ không giới hạn là một hồ sơ dài vô hạn về một người.

#### (c) `adhd/cauhoi.py` — kỹ năng nhúng vào đúng phút cần đến

Hướng hiển nhiên cho nhóm này là một mục bài viết hoặc một khoá học chia
chương. §2.1 của thiết kế bác bỏ thẳng: tài liệu CBT cho người lớn ghi
người đến học thường đã *"biết phải làm gì, nhưng khó làm được"*. Đây là
**vấn đề thực thi**, không phải vấn đề kiến thức. Một thư viện bài viết
giải một vấn đề không tồn tại — và còn tỏ ra là đã giải rồi.

Tệ hơn: đọc bài viết là một việc dễ làm **và** có cảm giác như đang cố
gắng. Nó là chỗ trốn hoàn hảo khỏi chính việc cần làm.

Nên cùng nội dung đó, nhưng ở đúng phút người dùng đang kẹt:

| chương sách | thành câu hỏi lúc nào |
|---|---|
| chia nhỏ công việc | *"Bước nhỏ nhất bạn làm được ngay bây giờ là gì?"* — khi đang kẹt |
| ý định thực thi | ba ô khi nào / ở đâu / việc gì trong `phien.py` |
| đối chiếu ước lượng | câu trong `thoiluong.py` |

Bốn lúc, mỗi lúc 3–4 câu xoay vòng để không thành tiếng ồn:
`CHUA_BAT_DAU`, `DANG_KET`, `BI_KEO_DI`, `VUA_XONG`.

**Mọi chuỗi kết thúc bằng dấu hỏi**, và có test khoá lại. Đó không phải
sở thích văn phong: câu hỏi để lại quyền quyết định cho người dùng; lời
khuyên lấy nó đi. Một app lấy quyền quyết định của người dùng về việc họ
nên làm gì với sức khoẻ của họ là một app khác hẳn về mặt pháp lý.

#### Mâu thuẫn phải gỡ: nhân vật không bao giờ chủ động bắt chuyện

Đây là chỗ dễ nhầm nhất trong cả bước này.

§4.3(c) muốn hỏi khi người dùng **kẹt lâu**. `luu-tru/NHAN_VAT_BRIEF.md` §2.4 nói
nhân vật **chỉ tương tác khi được chạm**. Mà đúng lúc cần hỏi nhất, người
dùng lại ít khả năng chủ động chạm vào nhất.

Cách gỡ là tách hai thứ ra:

| | |
|---|---|
| **nét mặt dịu xuống** | thụ động. Nhìn thấy được, không đòi hỏi gì |
| **câu hỏi** | **chỉ** khi được chạm. Nó đòi một câu trả lời |

Nét mặt dịu xuống là một lời mời nhìn thấy được mà không phải là bắt
chuyện. `BoDoKet` chỉ đổi nét mặt; nó **không bao giờ** làm app lên
tiếng. Ngưỡng 15 phút để rộng — gọi một người đang làm được việc là
"đang kẹt" thì tệ hơn là im lặng, và vì kết quả chỉ đổi nét mặt nên đoán
nhầm ở đây trả giá rất nhẹ.

`_cap_nhat_net_mat()` chỉ đụng tới nét `BINH_THUONG`. Người vừa xong việc
đang ở nét `TU_HAO` thì bộ đo kẹt không được phép giẫm lên.

#### Ranh giới dữ liệu: hai trong ba module **không** nối vào cầu nối

Bảng trong `loi_chung/bridge.py` liệt kê thứ không bao giờ được đi qua
cầu nối — trong đó có **tên các lời nhắc người dùng tự đặt** và **nhật ký
cảm xúc**.

Nên `nhacviec.py` và `nhatky.py` sống trọn vẹn trên máy người dùng. Bản
Python ở đây là **bản gốc để đối chiếu** — chạy được, có test đầy đủ — và
bản iOS hiện thực lại đúng logic đó. Chỉ `cauhoi.py` nối vào
`run_flowy.py`, vì câu hỏi là chuỗi chung, không mang dữ liệu của ai.

Đây là thứ rất dễ vô tình phá: thêm một dòng `import` cho tiện là đủ. Mã
hỏng kiểu đó không làm test nào khác đổ, không làm app sập — nó chỉ lặng
lẽ đưa dữ liệu cá nhân lên đường truyền. Nên có hai bài test canh gác
trong `test_cau_truc_nhanh.py`, kiểm bằng cây cú pháp chứ không bằng tìm
chuỗi (một câu chú thích nhắc tên module là hợp lệ, một lệnh `import` thì
không). Đã thử phá để chắc chúng cắn thật.

**Test thêm: 97.** Tổng 327, tất cả xanh.

---

### 2.7. Phía Android — nối lại với hợp đồng mới

Việc lớn nhất còn lại ở đợt trước. `MainActivity.kt` vẫn là app dẫn
đường, và hợp đồng JSON đã đổi nên hai phía **không khớp**.

#### Cắt phần điều hướng ra, đúng cách phần Python đã làm

Sáu lớp sang `phan_khiem_thi/android/`: `ArMath`, `DepthSampler`,
`ObjectVision`, `BarometerReader`, `NfcLauncher`, `LaunchTileService` —
cùng `ArMathTest`, `shortcuts.xml` và năm ảnh mã ArUco. Dùng `git mv`
nên lịch sử còn nguyên.

Kéo theo hai phụ thuộc nặng rời khỏi `build.gradle.kts`:

```
com.google.ar:core:1.44.0
com.google.mlkit:object-detection:17.0.2
```

APK: **50 MB → 856 KB**.

Con số 50 MB đầu tiên gây hiểu nhầm — bản build tăng dần còn giữ `.dex`
cũ. Phải `./gradlew clean` mới thấy đúng. Ghi lại vì ai đo lại mà thấy 50
MB sẽ tưởng việc bỏ phụ thuộc không có tác dụng.

Bốn quyền còn lại, và không hơn: INTERNET, ACCESS_NETWORK_STATE, VIBRATE,
RECORD_AUDIO, POST_NOTIFICATIONS. Không camera, không vị trí, không NFC.
Mỗi quyền thêm vào là một câu phải trả lời ở phần trình bày.

#### `Payload.kt` — hợp đồng mới

Viết lại hoàn toàn. Vẫn cố ý **không dùng `org.json`**: lớp này phải chạy
được trong unit test JVM thường, mà `org.json` trong android.jar chỉ là
bản rỗng.

#### Ba sổ, bản Kotlin

`SoThoiLuong.kt`, `SoNhac.kt`, `SoNhatKy.kt` — bản Kotlin của ba module
Python ở bước 7. Điện thoại sở hữu tệp lưu; bản Python là bản gốc để đối
chiếu.

Ba sổ này **có** dùng `org.json`, khác `Payload`: nội dung là chữ tự do
của người dùng, và tự viết bộ thoát chuỗi cho chữ đó là đúng chỗ lỗi hay
nằm. Kèm theo là `testImplementation("org.json:json:20231013")` — bản
thật, chỉ trên đường chạy của test.

Chi tiết đó quan trọng hơn vẻ ngoài: `unitTests.isReturnDefaultValues =
true` làm bản rỗng **thôi ném lỗi** và lặng lẽ trả về `null`. Đó là
trường hợp tệ nhất — `SoNhatKyTest` sẽ xanh trong khi `SoNhatKy` không
đọc được gì cả.

#### Nhân vật: tư thế và cử chạm

`BanDongHanhView` thêm `datTuThe(n)` và `onCham`. Bốn tư thế là **bản
tạm** — bốn hình một nét để hệ thống chạy được đầu-cuối trước khi có
tranh vẽ tay. Bản của người vẽ chỉ cần thay `veTuThe`.

Mỗi tư thế là **một nét, tĩnh, không màu riêng**. Ý đồ không phải làm
nhân vật thú vị — mà ngược lại: mục 2.5 của bản mô tả đòi nó phải **kém
thú vị hơn** công việc của người dùng.

---

### 2.8. Ba lỗi chỉ lộ ra khi chạy thật đầu-cuối

Cách tìm ra: cho `Payload.buildUpdate` sinh mười gói tin, POST thật lên
`run_flowy.py` qua HTTP, rồi đọc từng câu trả lời.

Cả ba đều **lọt qua 380 bài test** trước đó, vì cả ba nằm ở chỗ ghép giữa
các module chứ không nằm trong module nào.

#### (1) Bấm "Kết thúc" ở một phiên không có bước nào thì không gì xảy ra

`Phien.xong` đòi `bool(self.buoc)`. Điều kiện đó đúng cho một phiên vừa
tạo — nó chưa xong. Nhưng nó cũng làm một phiên **không bao giờ có bước
nào** không bao giờ xong được.

Mà đó lại là đường đi thường gặp nhất: nói việc gì / khi nào / ở đâu, bắt
đầu, làm, rồi bấm Kết thúc.

Thêm `Phien.ket_thuc()`: người dùng **tự tuyên bố** là xong. Dừng ngay,
kể cả khi còn bước chưa đánh dấu — họ biết rõ hơn app về việc họ đã làm
xong hay chưa.

#### (2) Nét mặt `thong_cam` dính lại vĩnh viễn

Sau một lần phân tâm, nét mặt dịu xuống rồi **không bao giờ trở lại**.

Một nét mặt thông cảm dính mãi thì không còn nghĩa gì nữa — nó thành nét
mặt mặc định, và lúc thật sự cần nó thì không ai thấy khác biệt.

Thêm `GIU_NET_MAT_S = 25.0`: đủ lâu để người dùng ngẩng lên là còn thấy,
đủ ngắn để không thành mặc định. Vẫn đang kẹt thì gia hạn, không tự gỡ.

#### (3) Xong việc mà không hẹn giờ thì nét mặt không đổi

`_cau_xong()` chỉ đổi nét mặt bên trong nhánh `if self.gio_hen is not
None`. Phần lớn phiên không hẹn giờ — nên đa số lần làm xong đều không
được ghi nhận gì, và "xong việc" với "bỏ dở" trông giống hệt nhau trên
màn hình.

---

### 2.9. Một chỗ mỏng tìm ra nhờ đọc kỹ, không phải nhờ test

`BoTheoMach` chỉ tính là đứt mạch nếu nhận được **ít nhất hai gói tin
trong lúc vắng**: gói đầu đặt mốc, gói sau mới so.

Với bản điều hướng thì đúng — điện thoại đeo trên ngực, luôn gửi.

Với Flowy thì không. "Vắng" ở đây nghĩa là **người dùng đã mở app khác**,
và hệ điều hành hoàn toàn có thể treo tiến trình này suốt khoảng đó.

Kết quả là trường hợp **cần nhất** lại là trường hợp im lặng: đi càng
lâu, càng ít khả năng có gói tin giữa chừng, càng chắc chắn không có câu
dựng lại ngữ cảnh nào.

Sửa: đo cả ở gói tin **quay lại**, không chỉ ở lúc đang vắng.

---

### 2.10. Bốn bài canh gác mới

Hợp đồng JSON không có trình biên dịch nào nối hai bên. Đổi `nhip_ms`
thành `nhipMs` bên Python là thao tác an toàn tuyệt đối theo mọi bộ test
cũ — và nó làm điện thoại rơi về nhịp mặc định, im lặng, mãi mãi.

| Tệp | Khoá gì |
|---|---|
| `tests/loi_chung/test_hop_dong.py` | tên từng trường, cả hai chiều, và cả chiều "không có trường thừa" |
| `tests/test_run_flowy.py` | chính vòng lặp, qua đúng cửa vào điện thoại dùng |
| `app/src/test/.../PayloadTest.kt` | phía Kotlin của cùng hợp đồng |
| `app/src/test/.../DoiChieuBanPythonTest.kt` | **bản ghi của một lần chạy thật** |

Bài cuối đáng nói riêng. `PayloadTest` kiểm chuỗi do **chính nó** viết
ra; nếu tôi hiểu sai định dạng của bản Python thì cả hai phía của bài test
đó đều sai theo, và nó vẫn xanh.

`DoiChieuBanPythonTest` thì đọc chữ mà `run_flowy.py` **thật sự** sinh ra
— mười gói tin Kotlin POST qua HTTP, mười câu trả lời ghi nguyên văn vào
`src/test/resources/`. Sai lệch về `ensure_ascii`, về khoảng trắng sau
dấu hai chấm, về cách ghi số thực đều lộ ra ở đó.

Hai trường mới trong hợp đồng, và lý do:

| trường | vì sao cần |
|---|---|
| `xong_phien` | điện thoại sở hữu sổ thời lượng, nên nó phải biết **lúc nào** một phiên xong để ghi lại |
| `ten_viec` | và biết ghi vào **mục nào** |

Không có hai trường này thì điện thoại phải đoán từ câu nói — mà đoán từ
câu nói là hỏng ngay lần đầu ai đó sửa câu chữ.

**Test thêm: 93** (Python +22, Kotlin +71). Tổng 402 Python + 71 Kotlin.

---

## 3. Đã sửa

### 3.1. Đổi từ vựng điều hướng sang từ vựng công việc

| Cũ | Mới |
|---|---|
| `ChuyenDi` | `ViecDangLam` |
| `ten_dich` | `ten_viec` |
| `chang_con_lai` | `buoc_con_lai` |
| `cau_toi_noi` | `cau_xong_viec` |
| `xong_chang` | `xong_buoc` |
| *"Bạn đang trên đường tới X"* | *"Bạn đang làm dở X"* |
| *"Đã tới X"* | *"Xong X rồi"* |
| *"còn 2 chặng"* | *"còn 2 bước"* |
| *"bạn cần bắt đầu đi"* | *"bạn cần bắt tay vào"* |

Việc này lộ ra khi chạy thử: câu khôi phục ngữ cảnh đọc thành *"Bạn đang
trên đường **tới** viết báo cáo. Còn 1 **chặng**."*

Một va chạm khi đổi: `timeblind.cau()` vốn đã có tham số `ten_viec` (tên
sự kiện), nên sau khi đổi `ten_dich` → `ten_viec` thì trùng tên. Đã tách
rõ thành hai khái niệm khác nhau:

- `ten_cong_viec` — việc người dùng sắp làm (*"viết báo cáo"*)
- `ten_su_kien` — mốc phải xong trước (*"Hạn nộp"*, *"Lớp học"*)

### 3.2. `announce.py` — đổi tên hai kênh

`route_*` / `hazard_*` → `chi_dan_*` / `gap_*`. Cấu trúc hai kênh với bộ
đệm chống lặp riêng vẫn đúng cho Flowy; chỉ từ vựng là của hệ dẫn đường.

### 3.3. `bridge.py` — hợp đồng JSON mới

Bỏ `pose`, `depth`, `markers`, `objects`, `jpeg`, `pressure`,
`focal_px`. Thêm:

| Trường | Việc |
|---|---|
| `tren_man_hinh` | Tín hiệu phân tâm |
| `cham_nhan_vat` | Lời mời **duy nhất** để app lên tiếng |
| `lenh` + `noi_dung` | Nút bấm và chuỗi đi kèm |
| `lich_su` | Sổ thời lượng do điện thoại gửi lên |

Phía trả về thêm `tu_the` (tư thế nhân vật), `hoi` (câu hỏi đang chờ trả
lời — khác `say` ở chỗ nó **đòi** phản hồi), `con_lai_giay` và
`tong_giay` cho đồng hồ trực quan.

Máy chủ HTTP giữ nguyên, kể cả bản sửa `handle_error()` đã làm trước đây.

### 3.4. Ba chỗ câu chữ vụng, tìm ra khi chạy thử

| Đọc ra | Sửa thành |
|---|---|
| *"Hạn nộp **bắt đầu** lúc 15 giờ 41"* | *"Hạn nộp lúc 15 giờ 41"* |
| *"... phút. **viết** báo cáo mất khoảng"* | Viết hoa đầu câu |
| *"**Tới** đúng giờ rồi"* | *"**Xong** đúng giờ rồi"* |

---

### 3.5. `test_cau_chu.py` — bộ đo báo động giả ở chuỗi định dạng

Bài canh gác dấu tiếng Việt đổ ở `'%Y-%m-%d %H:%M'` trong `nhatky.py`.

Đó là **báo động giả**. Heuristic tách chuỗi thành từ rồi hỏi "bốn từ
trở lên mà không có lấy một dấu nào thì là tiếng Việt mất dấu". Chuỗi
định dạng tách ra thành `Y m d H M` — năm từ, không dấu.

Sửa ở **bộ đo**, không ở module: chỉ đếm các từ **từ hai chữ cái trở
lên**. Một từ một chữ cái không thể là âm tiết tiếng Việt bị mất dấu,
vì mọi từ một chữ cái của tiếng Việt (*"ý"*, *"ở"*, *"à"*) đều mang dấu
ngay trong chính chữ cái đó — `co_dau` đã bắt được rồi.

Nới một bài test canh gác để code của mình đi qua là việc đáng ngờ, nên
kèm theo hai bài **tự kiểm chính bộ đo**: một bài chứng minh nó vẫn bắt
được câu mất dấu thật, một bài ghi lại giới hạn đã biết — `mat_dau` là
**tất-cả-hoặc-không**, nên một câu mất dấu *một phần* vẫn lọt. Ngưỡng đó
là có ý: bộ đo chặt hơn từng báo động giả liên tục, và một bài test hay
báo động giả sẽ bị tắt đi — lúc đó nó thành vô dụng.

---

## 4. Chạy thử đầu-cuối

```
Lần trước bạn ước 20 phút, thực tế 35 phút.
Hạn nộp lúc 15 giờ 41. Viết báo cáo mất khoảng 35 phút.
Bây giờ là 14 giờ 56. Bạn cần bắt tay vào ngay bây giờ để kịp.
Sau bữa tối, bạn sẽ viết báo cáo tại bàn học. Bước đầu: mở tệp lên.

  [chạm vào nhân vật]
Bước nhỏ nhất bạn làm được ngay bây giờ là gì?

  [ra khỏi app 200 giây rồi quay lại]
Bạn đang làm dở viết báo cáo. Còn 1 bước. viết một câu

  [xong]
Xong viết báo cáo rồi. Bạn làm việc này để nộp cho thầy. Xong đúng giờ rồi.
```

Câu đầu tiên — *"lần trước bạn ước 20 phút, thực tế 35"* — là can thiệp
chính. Cái đồng hồ chỉ là phần hiển thị.

---

### Chạy thử lượt hai — câu hỏi đổi theo lúc, nét mặt dịu rồi trở lại

```
bat dau  : sau bữa tối, bạn sẽ viết báo cáo tại bàn học. Bước đầu: mở tệp lên.
cham 1   : Bước nhỏ nhất bạn làm được ngay bây giờ là gì?

  [ra khỏi app ba lần]
cham 2   : Có gì quanh bạn đang kéo sự chú ý đi không?   | nét mặt: binh_thuong

  [ngồi lì ở một bước 20 phút]
ket lau  : nét mặt -> thong_cam          <- app KHÔNG nói gì
cham 3   : Bước này có chia nhỏ thêm được nữa không?
cham 4   : Chỗ nào trong bước này đang khó đi tiếp?

  [xong bước]
xong buoc: nét mặt -> binh_thuong | Xong viết báo cáo rồi. Bạn làm việc này để nộp cho thầy.
cham 5   : Việc này hoá ra dễ hơn hay khó hơn bạn nghĩ?
```

Dòng đáng nhìn nhất là `ket lau`: người dùng kẹt 20 phút, và app **chỉ
đổi nét mặt**. Không một câu nào được nói ra cho tới khi họ chạm vào.

Và mỗi lần chạm cho một câu khác — không phải vì ngẫu nhiên, mà vì bộ
đếm xoay vòng riêng cho từng lúc.

---

## 5. Còn lại theo §6 của thiết kế

| # | Việc | Trạng thái |
|---|---|---|
| 1 | Dọn điều hướng, viết lại runner | **Xong** |
| 2 | `SoThoiLuong` | **Xong** |
| 3 | Nối `timeblind` vào nguồn mới | **Xong** |
| 4 | Đổi "chặng" → "bước" | **Xong** |
| 5 | Ý định thực thi: ba ô bắt buộc | **Xong** |
| 6 | Body double: nút bật, nhân vật, câu thưa | **Xong** (Android; iOS chưa) |
| 7 | Ba nhóm y tế theo khuôn §4.3 | **Xong** |
| 8 | Bốn test canh gác câu chữ | **Xong** (làm sớm, trước khi có code vi phạm) |

### Việc lớn nhất còn lại

**Chưa cắm máy thật lần nào.** Toàn bộ phần Android đã biên dịch sạch, 71
bài test Kotlin qua, APK build được — nhưng chưa ai mở nó trên một chiếc
điện thoại.

Những thứ chỉ lộ ra ở đó: giọng tiếng Việt có sẵn không, nhận dạng giọng
nói nghe được trong phòng ồn tới đâu, nhân vật vẽ ra trông thế nào ở kích
thước thật, và nhịp 500 ms ăn pin bao nhiêu.

Đây là việc tiếp theo, và nó cần một buổi cắm máy chứ không cần thêm code.

### Sau đó là iOS

`run_flowy.py` là bản gốc, và bản Android vừa xong là bản dịch thứ nhất
của nó. Bản iOS là bản dịch thứ hai, và nó chạy **không cần laptop**.

Ba sổ đã có bản Python lẫn bản Kotlin, nên hình dạng dữ liệu đã được chốt
qua hai lần hiện thực — bản thứ ba sẽ rẻ hơn hai bản đầu.

### Ba chỗ tạm

- `ten_su_kien` chưa có đường nhập riêng, tạm để trống
- Mục đích chuyến làm việc chỉ nhập được qua `--muc-dich`, chưa hỏi
  trong luồng
- Bốn tư thế nhân vật là hình một nét, chờ tranh vẽ tay thay vào
  (`BanDongHanhView.veTuThe`)
