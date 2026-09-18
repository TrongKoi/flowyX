# Hướng dẫn sử dụng

Hệ chỉ đường trong nhà cho người khiếm thị — ADC RMIT 2026.

---

## Trạng thái hiện tại

Lõi Python **và** phía Android đều đã nối xong. App gửi đủ bảy trường:
`pose`, `markers`, `battery`, `jpeg`, `depth`, `intrinsics`, `voice`.

Nghĩa là cắm máy Android vào là chạy được toàn bộ, gồm cảnh báo vật cản,
phân biệt cố định/tạm thời, khớp bản nền định vị (L4), điểm tụ sửa hướng
(L5), và xác nhận bằng biển chữ nổi (L1).

Ba điều còn phụ thuộc thiết bị và hiện trường, không phải phụ thuộc code:

| Việc | Vì sao chưa chắc |
|---|---|
| Depth API trên máy không có cảm biến ToF | Chạy ở chế độ **depth‑from‑motion**: đứng yên thì số đo kém dần, tường trắng trơn gần như không đo được. Cả hai đều đổ về trạng thái `CHUA_BIET` — đúng thiết kế, nhưng nghĩa là mất cảnh báo |
| Nhận dạng giọng nói tiếng Việt | Máy chưa cài gói tiếng Việt sẽ nghe sai số phòng. Bước đọc lại xác nhận sẽ chặn lại, nhưng người dùng phải nói lại |
| Bản đồ tầng | `config/map_floor3.json` vẫn là **bản mẫu**, chưa đo thật tại RMIT |

## Cài đặt

```bash
cd adc_wayfinding
pip install -r requirements.txt
```

Cần Python 3.10 trở lên.

**Không cần hiệu chỉnh camera.** Không phải in bảng cờ vua, không phải
chạy `calibrate.py` trước. Đường điện thoại lấy thông số nội tại từ
ARCore/ARKit lúc chạy; đường webcam ước tiêu cự từ góc nhìn. Ai cần đo
chính xác hơn vẫn chạy `tools/calibrate.py` được, và giá trị trong
`camera.npz` sẽ được ưu tiên.

## Chạy test

```bash
cd adc_wayfinding          # PHẢI đứng ở đây
python3 -m pytest tests/ -q
```

Kỳ vọng: **693 passed**.

> Phải đứng đúng trong `adc_wayfinding/`. Có một test dùng đường dẫn
> tương đối `config/map_floor3.json` nên chạy từ thư mục cha sẽ đỏ —
> đây là lỗi có sẵn từ trước, không phải do cấu hình sai.

---

## Chạy thử không cần điện thoại

Cách nhanh nhất để thấy hệ thống hoạt động:

```bash
python3 run_sim.py                              # mô phỏng toàn bộ hành trình
python3 run_bridge.py --to S                    # mở server
python3 tools/phone_sim.py --url http://<ip>:8765   # giả lập điện thoại
```

---

## Chạy với điện thoại Android

### 1. Cùng mạng WiFi

Laptop và điện thoại phải cùng một mạng. Mạng khách của trường thường
**chặn máy nói chuyện với nhau** — nếu không kết nối được thì phát WiFi
từ chính điện thoại và cho laptop nối vào.

### 2. Mở server trên laptop

```bash
python3 run_bridge.py --to S
```

Màn hình in ra địa chỉ dạng `http://192.168.1.23:8765`. Nhập địa chỉ đó
vào app.

Tham số hay dùng:

| Tham số | Việc |
|---|---|
| `--to <id>` | đích đến, **bắt buộc** |
| `--start <id>` | điểm xuất phát, mặc định `A` |
| `--map <file>` | bản đồ tầng, mặc định `config/map_floor3.json` |
| `--backdrop <file>` | bản nền độ sâu, bật lớp cố định/tạm thời và L4 |
| `--record <file>` | ghi số liệu nghiệm thu ra JSON |
| `--no-l4` `--no-l5` `--no-braille` | tắt từng lớp để khoanh vùng lỗi |

### 3. Quét dựng bản nền (làm một lần cho mỗi tầng)

Bắt buộc nếu muốn dùng cảnh báo "vật lạ" và lớp định vị L4.

```bash
python3 run_scan.py --out config/backdrop_tang3.json
```

Rồi **người sáng mắt** cầm máy đi chậm một vòng, quét camera trái–phải.
Ctrl-C để lưu.

Không phải dọn phòng trống, không phải đuổi người ra khỏi hành lang:
bản nền lấy giá trị độ sâu **lớn nhất** từng thấy, mà vật tạm thời chỉ
làm độ sâu ngắn lại chứ không bao giờ dài ra — nên người đi ngang qua tự
động bị loại.

Sau đó chạy kèm bản nền:

```bash
python3 run_bridge.py --to S --backdrop config/backdrop_tang3.json
```

### 4. Đeo máy cho đúng

Phần này quyết định hệ thống chạy được hay không, không phải chi tiết
phụ.

| Thông số | Giá trị | Vì sao |
|---|---|---|
| Dây đeo | **≤ 15 cm** | Điện thoại treo dây là một con lắc đơn. Dây 25 cm dao động ở 1,00 Hz, mà thân người lắc ngang khi đi bộ ở 0,85–1,00 Hz — **cộng hưởng**, càng đi càng lắc mạnh |
| Neo hai điểm | khuyến nghị mạnh | Thêm dây thun quanh thân kéo máy áp vào ngực. Con lắc cần **một** điểm treo để dao động; có điểm neo thứ hai thì mode con lắc biến mất hoàn toàn |
| Góc chúc xuống | 20–25° | Vùng mù dưới chân 1,1–1,3 m, xấp xỉ tầm quét của gậy trắng |
| Độ cao đeo | ~0,77 × chiều cao | ngang xương ức |

**Dây đeo thường quanh cổ là thiết kế sai** cho bài toán này, dù là thứ
dễ nghĩ đến nhất. Nó không giảm rung mà khuếch đại rung.

Công cụ tính cụ thể theo chiều cao:

```bash
python3 tools/check_mount.py --height 1.70
```

---

## Luồng xác nhận bằng biển chữ nổi

Khi hệ thống lạc và đang ở gần một cửa đã biết, nó sẽ mời người dùng sờ
biển:

```
Hệ thống:   "Bên phải bạn, ngang tầm tay, có biển chữ nổi.
             Hãy sờ và đọc số phòng."
Người dùng: "ba chấm mười hai"
Hệ thống:   "Phòng 3.12, đúng không ạ?"
Người dùng: "đúng"
Hệ thống:   "Đã xác nhận vị trí."
```

Bước đọc lại **không phải thủ tục thừa**. Chuỗi thật là: người sờ → người
nói → nhận dạng giọng nói → chuẩn hoá số. Khâu nhận dạng giọng nói trong
hành lang ồn có thể nghe "sáu lẻ tư" thành "sáu lẻ tám", mà mốc này được
phép sửa vị trí vượt ngưỡng thông thường — nên một lỗi nghe nhầm đơn lẻ
đủ đẩy vị trí đi rất xa nếu không có bước xác nhận.

Người dùng **luôn được phép từ chối**. Im lặng 10 giây là một câu trả
lời hợp lệ, và hệ thống sẽ không hỏi lại trong 60 giây.

---

## Khi có sự cố

| Hiện tượng | Nguyên nhân thường gặp |
|---|---|
| Điện thoại không nối được | Khác mạng WiFi, hoặc mạng chặn máy nói chuyện với nhau |
| Không nghe thấy gì | Máy chưa cài gói giọng tiếng Việt cho TextToSpeech |
| Nói liên tục không dứt | Kiểm tra `announce.py` — mỗi kênh phải có bộ đệm chống lặp **riêng** |
| Không cảnh báo vật cản | Android chưa gửi `depth` |
| Lớp L4 không khớp được | Chưa có bản nền, hoặc đặc trưng quá nhỏ (xem mục dưới) |
| Đọc biển sai khoảng cách | Android chưa gửi `intrinsics`, đang dùng ước lượng thô |

### L4 không khớp được ở hành lang trông rất đặc trưng

Cách chấm điểm dùng **trung vị**, nên nó chỉ "thấy" được đặc trưng phủ
**trên một nửa** số ô trong lưới. Một hốc tường chỉ làm đổi 3 trong 12 ô
thì trung vị vẫn bằng 0, và ô có hốc cho điểm y hệt ô hành lang thường.

Đây là đánh đổi có chủ đích — trung vị chống được người đi ngang qua.
Hướng sửa là **tăng độ phân giải lưới** (`--cell-m` nhỏ hơn khi quét),
không phải đổi sang trung bình. Đổi sang trung bình sẽ khiến một người
đi ngang qua đủ sức phá điểm của ô đúng.

---

## Hợp đồng JSON giữa điện thoại và laptop

`POST /update`, khoảng 8 lần/giây. Dấu thập phân **luôn là dấu chấm**
(dùng `Locale.US` khi sinh chuỗi trên Android).

Điện thoại gửi:

```json
{
  "pose": {"x": 3.21, "y": 1.4, "z": -1.05, "yaw": 87.4},
  "markers": [],
  "battery": 78,
  "intrinsics": {"fx": 1430.2, "fy": 1430.5, "cx": 640, "cy": 360,
                 "width": 1280, "height": 720},
  "depth": {"cols": 4, "rows": 3,
            "depth": [3.2, 3.1, 0, 4.0, ...],
            "confidence": [0.9, 0.9, 0, 0.9, ...]},
  "voice": "ba chấm mười hai"
}
```

Trong `depth`, giá trị **0 nghĩa là không đo được**, không phải "cách 0
mét". Phía laptop cho ra trạng thái `CHUA_BIET`.

`voice` chỉ xuất hiện ở khung hình ngay sau khi người dùng nói, rồi bị
xoá — gửi lại cùng một câu sẽ làm laptop tưởng người dùng nói hai lần.

Laptop trả về:

```json
{"say": "Đi thẳng khoảng mười bước.", "haptic": null,
 "confidence": "trung_binh", "state": "dang_di",
 "position": {"x": 3.2, "y": -1.1, "theta": 87.4},
 "distance_since_fix": 4.2}
```

---

## Mở app bằng NFC

Chạm điện thoại vào thẻ NFC là **một thao tác, không cần nhìn**, và
Android mở được ngay cả khi màn hình đang khoá — bỏ luôn bước mở khoá.

So với các đường vào khác:

| Cách | Số thao tác |
|---|---|
| Tìm biểu tượng qua TalkBack | Đánh thức → mở khoá → vuốt tìm → chạm đúp |
| Ô trong bảng Cài đặt nhanh | Vuốt xuống → tìm ô → chạm |
| **Chạm thẻ NFC** | **Chạm** |

### Ghi thẻ

Dùng bất kỳ app ghi NFC nào (ví dụ "NFC Tools"), chọn kiểu **URI**:

```
wayfinding://go                  → chỉ mở app
wayfinding://go?start=A          → mở app, đặt điểm xuất phát
wayfinding://go?start=A&to=S     → mở app và bắt đầu đi luôn
```

`start` và `to` là id nút trong bản đồ tầng.

Nên ghi kèm một bản ghi **AAR** trỏ tới `vn.adc2026.wayfinding`. Máy
chưa cài app sẽ được đưa thẳng tới trang cài đặt thay vì không phản ứng
gì.

App luôn **nói ra điểm đến vừa đọc được** trước khi bắt đầu đi. Người
dùng không nhìn thấy màn hình, nên nếu thẻ ghi sai đích thì đó là cơ hội
duy nhất để họ biết mà dừng lại.

### Vì sao không dùng NFC để định vị

Một thẻ NFC đặt ở vị trí đã biết là mốc neo gần như hoàn hảo: không nhầm
lẫn, không cần nhìn thấy, không phụ thuộc ánh sáng.

Nhưng nó vướng đúng điều đã khiến dự án bỏ ArUco: **phải dán lên tường**.
Phải xin phép toà nhà, phải dán trước khi dùng được, và hệ thống chỉ chạy
ở những toà nhà đã dán. Đó là rào cản triển khai thật.

Một thẻ ở cửa vào là đề nghị hợp lý; dán thẻ khắp hành lang thì không.
Nếu về sau vẫn muốn dùng làm mốc neo, đường đi là nộp
`AnchorSighting(source = "nfc")` qua đúng một cổng như mọi nguồn khác —
không ghi thẳng vào pose.

## Build app Android

**Cần JDK 17 hoặc 21.** Không dùng được JDK 25: AGP 8.5.2 từ chối nó, và
lỗi báo ra chỉ là một dòng `25.0.2` không giải thích gì.

Cách dễ nhất là để Android Studio tự tải:

> Settings → Build, Execution, Deployment → Build Tools → Gradle →
> **Gradle JDK** → Download JDK → chọn **17** → Apply

Rồi build từ terminal:

```bash
cd android
./gradlew assembleDebug          # ra app/build/outputs/apk/debug/app-debug.apk
./gradlew testDebugUnitTest      # 38 test Kotlin, không cần máy thật
```

Trên Windows dùng `gradlew.bat`. Nếu `JAVA_HOME` đang trỏ JDK khác, đặt
lại cho riêng lần chạy:

```bash
JAVA_HOME="C:/Users/<ten>/.jdks/ms-17.0.20.1" ./gradlew assembleDebug
```

Đã kiểm chứng: JDK 17 + Gradle 8.7 + AGP 8.5.2 → build thành công, APK
khoảng 51 MB, 38 test Kotlin xanh.

**Không cần cài Kotlin riêng.** Android Studio đã kèm sẵn `kotlinc`, và
Gradle tự dùng đúng phiên bản plugin Kotlin ghi trong `build.gradle.kts`.

---

## Hai chế độ sử dụng

App phục vụ hai nhóm người dùng bằng **cùng một lõi**, khác phần hiển thị.

| | Chế độ giọng nói (mặc định) | Chế độ nhắc giờ |
|---|---|---|
| Dành cho | Người khiếm thị | Người ADHD, hoặc bất kỳ ai hay trễ giờ |
| Kênh chính | Giọng nói và rung | Hình ảnh trên màn hình |
| Màn hình | Gần như trống | Đĩa đếm ngược, chặng, chỉ dẫn |

**App luôn mở vào chế độ giọng nói trước** — dẫn bằng âm thanh ngay, không
đòi ai nhìn màn hình. Nút chuyển sang chế độ nhắc giờ nằm **ngay dưới**
nút Bắt đầu.

Câu hỏi chuyển chế độ hỏi theo **nhu cầu**, không theo chẩn đoán: *"Bạn
muốn xem nhắc giờ trên màn hình?"* Bất kỳ ai cũng trả lời được, kể cả
người chưa từng được chẩn đoán ADHD. Chi tiết ở `UIUX_QUYET_DINH.md`.

Hai chế độ **không loại trừ nhau**: bật nhắc giờ không tắt giọng nói.

---

## Đi kèm giờ hẹn — chống mù thời gian

Đây là tính năng chính của chế độ nhắc giờ.

```bash
python3 run_bridge.py --to R12 --gio-hen 14:00 --viec "Lớp học"                       --muc-dich "nộp đơn xin nghỉ"
```

| Tham số | Việc |
|---|---|
| `--gio-hen GIO:PHUT` | Giờ **cần có mặt**. Có nó thì hệ thống neo lộ trình vào đồng hồ thật |
| `--viec TEN` | Tên sự kiện để đọc lên |
| `--muc-dich TEXT` | Tới đó để làm gì — nhắc lại lúc tới nơi và lúc khôi phục mạch |

Không truyền `--gio-hen` thì mọi thứ chạy y như trước: các lớp này **cộng
thêm**, không đổi hành vi nền.

### Câu neo

Thay vì *"khoảng 6 phút"* — một khoảng trôi nổi — hệ thống nói:

> *"Lớp học bắt đầu lúc 14 giờ. Đi tới Phòng 3.12 mất khoảng 6 phút.
> Bây giờ là 13 giờ 48 — bạn cần bắt đầu đi trong 4 phút nữa."*

Con số *4 phút* đã trừ **đệm an toàn** (20% quãng đường cộng 1,5 phút chi
phí khởi động). Ước lượng đi đường là thời gian **trung bình**, nên neo
đúng khớp giờ đến là cầm chắc trễ một nửa số lần.

Sắp hết giờ thì câu đổi giọng, nhưng **luôn kèm việc phải làm**:

> *"Bạn cần đi ngay bây giờ để không trễ."*

Không bao giờ có câu kiểu *"sắp trễ rồi"* không kèm hành động.

### Nhắc trong lúc đi

Ở các mốc **10, 5, 3, 1 phút** còn lại. Mỗi lần nhắc đều có **con số
phút**, vì *"còn 2 chặng"* trả lời câu hỏi *còn bao xa* chứ không trả lời
*còn kịp không*.

Quá giờ thì báo **đúng một lần**, và không trách móc.

### Khôi phục mạch sau khi bị phân tâm

Dừng lại quá **90 giây** rồi đi lại, câu tiếp theo không phải *"rẽ phải"*
mà dựng lại ngữ cảnh trước:

> *"Bạn đang trên đường tới Phòng 3.12 để nộp đơn xin nghỉ. Còn 2 chặng.
> Rẽ phải ở đây."*

Ba phần — đang đi đâu, để làm gì, việc trước mắt — đều cần, không rút gọn.

### Phản hồi khi xong chặng

Mỗi lần đi hết một chặng, máy **rung nhẹ kèm một tiếng ngắn**. Không có
câu nói — một cái rung đúng lúc không chiếm kênh tai và không cắt ngang
dòng suy nghĩ.

Mã rung `xong_chang` nhẹ hơn hẳn mã cảnh báo nguy hiểm, có chủ ý: đây là
lời khen, không phải cảnh báo.

Tắt cùng với rung trong Cài đặt của app.

### Bạn đồng hành

Một khuôn mặt đơn giản trên màn hình chế độ nhắc giờ, đổi nét theo sự kiện:

| Khi nào | Nét mặt |
|---|---|
| Tới đích đúng giờ | Vui |
| Đi đúng giờ từ 3 ngày liên tiếp | Tự hào |
| Vừa khôi phục mạch sau khi bị phân tâm | Dịu xuống, ở cạnh bạn |
| Còn lại | Bình thường |

**Không có nét mặt buồn hay thất vọng**, kể cả khi bạn trễ giờ hay đi lạc.
Trạng thái xấu nhất có thể xảy ra là *bình thường* — tức là không khen,
chứ không bao giờ là chê.

Chuỗi ngày lưu ở `config/chuoi.json`, đổi chỗ bằng `--chuoi <file>`.

---

## Tóm tắt biên bản cuộc họp (Meety)

Gọi Meety như một tiến trình con. Cần tải Meety về trước:

```bash
git clone https://github.com/TrongKoi/meeting-minutes-ai-demo meety
```

Đường chạy cho demo **không cần API key và không gọi mạng**:

```python
from wayfinding.meety import goi, cau_tom_tat
kq = goi("đường/dẫn/tới/meety", "hop.vtt", "2026-09-15", mock=True)
if kq.ok:
    print(cau_tom_tat(kq.bien_ban))
else:
    print(kq.loi_doc)      # câu tiếng Việt để đọc lên
```

Transcript lấy từ Zoom, Google Meet hay Teams — cả ba đều cho tải `.vtt`
miễn phí, nên bỏ qua được khâu nhận diện giọng nói.

Mọi đường thất bại trả về `loi_doc` — một câu tiếng Việt có dấu, **không
bao giờ ném ngoại lệ**, vì bên gọi nằm trong vòng lặp thời gian thực.

---

## Quy ước dấu tiếng Việt — dễ sai, hậu quả nặng

- **Mã nguồn và chú thích**: viết **không dấu**.
- **Mọi chuỗi sẽ được đọc lên**: **bắt buộc có dấu đầy đủ**.

Bộ đọc tiếng Việt đọc "Dang chay" thành chuỗi âm vô nghĩa. Với app cho
người khiếm thị, giọng nói là kênh đầu ra **duy nhất**.

Ngoại lệ quan trọng đi ngược lại: **`signs[].text` trong bản đồ phải
KHÔNG dấu**. Đó là chữ in thật trên tấm biển, dùng để so khớp OCR;
`signtext.py` bỏ dấu trước khi so. Thêm dấu vào đó sẽ làm hỏng lớp nhận
diện biển.

`tests/test_tts_tieng_viet.py` khoá cả hai chiều này.

---

## Build APK và chạy demo

### Dự án đã build được APK chưa?

**Android: rồi.** Có đủ `gradlew`, `build.gradle.kts`, `AndroidManifest.xml`,
và hai dependency ngoài đều đã khai báo (`com.google.ar:core:1.44.0` và
`com.google.mlkit:object-detection:17.0.2`).

**iOS: chưa.** Repo **không có dự án Xcode nào** — không `.xcodeproj`,
không file Swift, không `Info.plist`. Xem mục cuối để biết phải làm gì.

### Build APK

Cần **Android Studio** (hoặc JDK 17 + Android SDK) và máy có mạng để tải
dependency lần đầu.

```bash
cd android
./gradlew assembleDebug
```

APK nằm ở `android/app/build/outputs/apk/debug/app-debug.apk`.

Cài lên máy đã bật gỡ lỗi USB:

```bash
./gradlew installDebug
# hoặc
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

> **Lần đầu build phải mở Android Studio sync một lần.** Module `frontend/`
> nằm **ngoài** thư mục `android/`, khai báo qua
> `project(":frontend").projectDir = file("../frontend")`. Cấu hình này
> đúng về mặt Gradle nhưng chưa được biên dịch kiểm chứng — nếu sync báo
> lỗi, kiểm tra đường dẫn tương đối trước tiên.

### Yêu cầu thiết bị Android

| Thứ | Yêu cầu | Thiếu thì sao |
|---|---|---|
| Android | 7.0 trở lên (API 24) | Không cài được |
| ARCore | Máy phải nằm trong danh sách hỗ trợ của Google | Không định vị được |
| Khí áp kế | Có thì tốt | Không tự biết đổi tầng, hệ thống sẽ **hỏi** người dùng |
| Depth API | Có thì tốt | Mất cảnh báo vật cản; chế độ ADHD không cần |
| Gói giọng tiếng Việt | Cài trong Cài đặt → Text-to-speech | Không nghe thấy gì |

Kiểm tra nhanh máy có đủ không:

```bash
cd adc_wayfinding
python3 tools/check_device.py
```

### Chạy demo — hai cách

**Cách A: không cần điện thoại** (dùng khi WiFi hội trường có vấn đề)

```bash
cd adc_wayfinding
python3 run_sim.py
```

Chạy trọn hành trình bằng mô phỏng. Đây là **phương án dự phòng cho ngày
thi** — nên thử trước ít nhất một lần.

**Cách B: điện thoại thật + laptop**

```bash
# Trên laptop
cd adc_wayfinding
python3 run_bridge.py --to R12 --gio-hen 14:00
```

Laptop in ra một địa chỉ dạng `http://192.168.1.23:8765`. Nhập địa chỉ đó
vào app trên điện thoại rồi bấm bắt đầu.

> Laptop và điện thoại phải **cùng mạng WiFi**. Mạng khách của trường
> thường chặn hai máy nói chuyện với nhau — nếu không kết nối được, phát
> WiFi từ chính điện thoại rồi cho laptop nối vào.

Muốn thử cầu nối mà chưa có máy thật:

```bash
python3 tools/phone_sim.py --url http://192.168.1.23:8765
```

### Vì sao vẫn cần laptop?

Laptop là **bộ não tạm thời** trong giai đoạn phát triển, không phải thiết
kế cuối. Toàn bộ lõi quyết định viết thuần bằng số (không gọi ARCore,
không gọi OpenCV) nên kiểm thử được 915 ca mà không cần cầm thiết bị.

Bước tiếp theo là port lõi đó sang Kotlin để chạy hẳn trên điện thoại —
kiến trúc đã chuẩn bị sẵn cho việc này.

### Chạy trên iOS

**Chưa làm được.** Cần ba thứ mà repo hiện chưa có:

1. **Một máy Mac** — Xcode chỉ chạy trên macOS, không có đường vòng.
2. **Một dự án Xcode mới** cho thư mục `ios/`, chưa tồn tại.
3. **Port lớp cảm biến sang Swift**: `ARKit` thay `ARCore`, `sceneDepth`
   thay Depth API (chỉ máy có LiDAR), `CMAltimeter` thay khí áp kế,
   `Vision` thay ML Kit.

Phần **không** phải viết lại: toàn bộ lõi quyết định trong
`wayfinding/loi_chung/` và `wayfinding/adhd/` — chúng thuần số và chuỗi,
port thẳng sang Swift được.

Một cái bẫy đã ghi sẵn trong `BarometerReader.kt`: iOS **bắt buộc** có
khoá `NSMotionUsageDescription` trong `Info.plist`. Thiếu nó thì iOS
**giết app** ngay khi gọi `CMAltimeter` — lỗi im lặng, rất khó tìm. Và
phải xin quyền **sớm ở màn hình thiết lập**, vì iOS chỉ hiện hộp thoại
khi app đang ở tiền cảnh.
