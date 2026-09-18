# Đặc tả pipeline — hệ chỉ đường trong nhà cho người khiếm thị

Tài liệu này là **đặc tả để viết code**, không phải bản mô tả ý tưởng.
Mỗi node có: chạy ở đâu, vào gì ra gì, công thức, ngưỡng, và tiêu chí
nghiệm thu. Ai code theo tài liệu này — người hay LLM — phải ra được
cùng một hành vi.

Quy ước viết: mã nguồn và chú thích trong code viết **không dấu**; mọi
chuỗi **sẽ được đọc lên** (strings.xml, Localizable.strings, câu TTS)
bắt buộc **có dấu đầy đủ**. Lý do: bộ đọc tiếng Việt đọc "Dang chay"
thành chuỗi âm vô nghĩa.

---

## §1. Năm nguyên tắc bất biến

Mọi quyết định thiết kế bên dưới đều suy ra từ năm điều này. Khi có mâu
thuẫn, nguyên tắc thắng.

**1.1 — Thà im lặng còn hơn nói sai.**
Người dùng không kiểm chứng được điều hệ thống nói. Một câu "rẽ trái"
sai đưa họ vào tường. Mọi phát ngôn phải kèm mức tin cậy; dưới ngưỡng
thì **không nói gì**, hoặc nói "tôi không chắc" — không bao giờ đoán.

**1.2 — Không bao giờ chặn vòng lặp thời gian thực.**
Vòng VIO + cảnh báo vật cản chạy ở 30 Hz. OCR mất 80–300 ms, TTS mất
hàng giây, mạng có thể treo. Tất cả những thứ đó chạy trên luồng riêng
với hàng đợi **ngắn, bỏ phần tử cũ nhất** (drop-oldest, maxsize 1–2).
Dữ liệu cũ 2 giây là vô dụng, không đáng xếp hàng.

**1.3 — Mọi nguồn vị trí đi qua đúng một cổng.**
Không nguồn nào được ghi thẳng vào pose. Tất cả nộp `AnchorSighting` cho
`Localizer`, nơi kiểm tra tính hợp lý rồi mới quyết định sửa. Thêm nguồn
mới = thêm một lớp nộp đơn, không phải sửa lõi.

**1.4 — Lõi không phụ thuộc nền tảng.**
`Localizer`, `Router`, `Depth`, `Backdrop`, `Announce` chỉ nhận số và
trả số. Không import ARCore, ARKit hay OpenCV trong lõi. Nhờ vậy cùng
một logic chạy được trên Python (demo), Kotlin (Android), Swift (iOS),
và kiểm thử được mà không cần thiết bị.

**1.5 — Ngân sách độ phân giải là ràng buộc thiết kế, không phải chi tiết.**
Xem §3. Đây là điều dễ bỏ sót nhất, và là thứ làm hỏng lớp OCR nếu bỏ sót.

---

## §2. Hai chế độ vận hành (mục 12)

Cùng một lõi, khác đường truyền. Phải thiết kế **từ đầu**: nếu viết demo
trước rồi mới nghĩ cách bỏ laptop thì phải viết lại.

### 2.1 Chế độ DEMO — điện thoại là cảm biến, laptop là bộ não

```
  ĐIỆN THOẠI                         LAPTOP
  ARCore/ARKit                       adc_wayfinding (Python)
    pose 6-DoF  ──┐
    ảnh camera    │   HTTP POST      Localizer
    depth map     ├──  /update   ──> Router
    nội tại       │    ~8 Hz         Depth / Backdrop
                ──┘                  Announce
    TTS  <────── câu nói ──────────────┤
    rung <────── lệnh rung ────────────┘
```

Dùng để: sửa thuật toán nhanh (sửa Python, chạy lại, không build lại
app), ghi log đầy đủ, vẽ bản đồ trên màn hình lớn cho giám khảo xem.

### 2.2 Chế độ SẢN PHẨM — tất cả trên điện thoại

```
  ĐIỆN THOẠI
  ARCore/ARKit ──> Localizer ──> Router ──> Announce ──> TTS + rung
       │              ▲
       ├──> OCR ──────┤
       └──> Depth ────┘
```

Không WiFi, không laptop, không độ trễ mạng. Đây là thứ nộp.

### 2.3 Ranh giới phải giữ

Để hai chế độ dùng chung một lõi, **cả hai đi qua cùng một hàm**:

```
step(sensors: SensorFrame, t: float) -> Decision
```

- DEMO: điện thoại đóng gói `SensorFrame` thành JSON → laptop gọi
  `step()` → trả `Decision` về.
- SẢN PHẨM: điện thoại gọi `step()` trực tiếp trong tiến trình.

Bất cứ thứ gì nằm **trong** `step()` phải được viết lại bằng Kotlin/Swift
cho bản sản phẩm. Bất cứ thứ gì nằm **ngoài** chỉ là đường truyền.

### 2.4 Bảng chuyển ngữ — module nào phải port

| Module Python | Phải port? | Ghi chú |
|---|---|---|
| `localizer.py` | **Có** | Lõi an toàn. Port trước tiên. |
| `router.py` | **Có** | Thuần hình học. |
| `depth.py` | **Có** | Thuần số học trên lưới. |
| `backdrop.py` | **Có** | Cần thêm I/O tệp JSON. |
| `announce.py` | **Có** | Ưu tiên + chống lặp. |
| `signtext.py` | **Có** | Bỏ dấu + so khớp mờ. |
| `geometry.py` | **Có** | SE(2). |
| `profile.py` | Một phần | Chỉ cần hằng số + `floor_coverage`. |
| `anchors.py` | **Không** | Thay bằng ML Kit (Android) / Vision (iOS). |
| `arcore.py` | **Không** | Đã có `ArMath.kt`; làm bản Swift tương ứng. |
| `bridge*.py` | **Không** | Chỉ dùng cho DEMO. |
| `metrics.py` | Không | Công cụ đánh giá ngoại tuyến. |

**Thứ tự port**: `geometry` → `localizer` → `router` → `announce` →
`depth` → `signtext` → `backdrop`. Mỗi bước port kèm port luôn bộ test.

---

## §3. Ngân sách độ phân giải — ràng buộc nền tảng

Phần dễ sai nhất. Đọc kỹ trước khi viết bất kỳ lớp thị giác nào.

### 3.1 Ảnh trong phiên AR không phải ảnh chụp

`Frame.acquireCameraImage()` trả ảnh CPU ở kích thước do `CameraConfig`
quy định — **không phải** độ phân giải cảm biến. Nếu không gọi
`setCameraConfig()`, ARCore chọn cấu hình mặc định, thường là **ảnh CPU
nhỏ nhất** để giữ tốc độ bám vị trí. Trên nhiều máy đó là 640×480.

**Trạng thái hiện tại của repo: không có chỗ nào gọi `setCameraConfig`.**
Nghĩa là lớp OCR đang chạy trên ảnh 640px mà không ai biết.

### 3.2 Cự ly đọc được, theo độ phân giải

OCR cần khoảng **20 px chiều cao chữ** để ổn định. FOV ngang 65°:

| Ảnh CPU | Biển 30mm (số phòng) | Biển 50mm | Biển 100mm (tầng, thoát hiểm) | Biển 150mm |
|---|---|---|---|---|
| 640px | **0,8 m** | 1,3 m | 2,5 m | 3,8 m |
| 1280px | 1,5 m | 2,5 m | 5,0 m | 7,5 m |
| 1920px | 2,3 m | 3,8 m | 7,5 m | 11,3 m |

Đây là giới hạn **quang học tuyệt đối**, chưa tính nhòe do chuyển động,
lệch góc, hay thiếu sáng. Thực tế lấy khoảng **70%** các con số này.

### 3.3 Ba hệ quả thiết kế

**(a) Phải chọn `CameraConfig` chủ động.** Khi tạo phiên:

```
filter = CameraConfigFilter(session)
    .setTargetFps(EnumSet.of(TargetFps.TARGET_FPS_30))
configs = session.getSupportedCameraConfigs(filter)
chọn config có imageSize.width lớn nhất
session.setCameraConfig(config)
```

Chấp nhận 30 fps để đổi lấy ảnh lớn hơn. VIO ở 30 fps là đủ; OCR ở 640px
thì không thuật toán nào cứu được.

*Bắt buộc ghi log `imageSize` thực nhận ở lần chạy đầu trên máy thật.*
Danh sách cấu hình khác nhau theo máy — không được giả định.

**(b) Đổi thứ tự tin cậy của các lớp thị giác.** Số phòng 30mm chỉ đọc
được trong 1,5 m ngay cả ở 1280px, nên nó **không thể** là lớp mốc chính:

| Lớp | Cỡ chữ | Cự ly dùng được | Vai trò |
|---|---|---|---|
| Biển tầng / thoát hiểm | 100–150mm | 3–7 m | **Mốc chính** — tìm từ xa |
| Số phòng | 25–40mm | 0,8–1,5 m | **Mốc xác nhận** — khi đi ngang cửa |

Biển lớn dùng để *định vị lại khi lạc*; số phòng dùng để *xác nhận đã
tới đúng cửa*. Hai vai trò khác nhau, ngưỡng khác nhau.

**(c) Lối dự phòng: đọc texture GPU.** ARCore cấp thêm texture camera ở
`textureSize`, thường 1920×1080 — lớn hơn ảnh CPU. Có thể vẽ texture đó
vào framebuffer ngoài màn hình rồi `glReadPixels` một vùng cắt để OCR:
được ảnh lớn mà không hạ fps bám vị trí. Phức tạp hơn — xếp giai đoạn 2,
chỉ làm nếu (a) không đủ.

### 3.4 Lấy nét — ràng buộc thứ hai, độc lập

Mặc định ARCore đặt `FocusMode.FIXED`, lấy nét gần vô cực, để giữ chất
lượng bám vị trí. Vật ở 0,3 m sẽ **mất nét**. Chuyển `AUTO` thì ảnh nét
hơn ở gần nhưng VIO xấu đi mỗi lần ống kính đảo nét.

Quy tắc: **giữ FIXED trong lúc điều hướng.** Chỉ bật AUTO trong chế độ
"đọc biển" tạm thời, khi người dùng đã dừng lại.

---

## §4. Mục 4 — đọc biển chữ nổi braille

Mục duy nhất trong danh sách tôi **không khuyến nghị làm theo cách đã
nêu**. Lý do bên dưới, kèm phương án thay thế.

### 4.1 Braille có đọc được bằng camera không?

Chấm braille tiêu chuẩn đường kính 1,5 mm, khoảng cách tâm 2,5 mm. Cần
tối thiểu ~5 px/chấm để tách được chấm có/không.

| Ảnh CPU | Cự ly xa nhất còn đọc được |
|---|---|
| 640px | **0,15 m** |
| 1280px | **0,30 m** |
| 1920px | **0,45 m** |

Thêm ba yếu tố nữa:

1. **Mất nét.** Ở FIXED focus, 0,15–0,45 m nằm ngoài vùng nét (§3.4).
2. **Braille không có tương phản màu.** Chấm nổi và nền cùng màu, cùng
   chất liệu. Camera chỉ thấy chấm nhờ **đổ bóng**, nên phụ thuộc hoàn
   toàn vào hướng đèn. Đèn trần chiếu thẳng từ trên xuống → gần như
   không có bóng → không thấy gì.
3. **Người dùng phải giơ camera cách biển 20 cm và giữ vuông góc** —
   trong khi không nhìn thấy biển ở đâu.

Điểm 3 là chỗ lập luận tự sụp đổ: **ở cự ly 20 cm thì tay người dùng đã
chạm được biển rồi.** Mà chạm chính là công dụng của braille.

### 4.2 Ba phương án

**A. Giải mã braille bằng camera** → **không làm.** Ba rào cản trên, mỗi
cái đủ để hỏng. Kể cả làm được cũng chỉ chạy ở cự ly mà bàn tay làm tốt hơn.

**B. Chỉ phát hiện *có* biển braille, không giải mã.** Khả thi hơn — chỉ
cần nhận ra một mảng chấm đều. Nhưng giá trị thấp: biết "có biển ở đây"
mà không biết biển ghi gì thì không định vị được.

**C. ★ Người trong vòng lặp — hệ thống hướng dẫn, người dùng đọc.**

```
Hệ thống:   "Bên phải bạn, ngang tầm tay, có biển chữ nổi.
             Sờ và đọc số phòng."
Người dùng: [sờ biển] "sáu lẻ tư"
Hệ thống:   "Phòng 604. Đã xác nhận vị trí."   ← mốc tuyệt đối, tin cậy 100%
```

Vì sao đây mới là phương án đúng:

- **Chính xác tuyệt đối.** Người đọc braille bằng tay không nhầm. Không
  lớp thị giác nào của ta đạt độ tin cậy đó.
- **Đặt lại trôi VIO về 0** tại một điểm biết chắc.
- **Tôn trọng kỹ năng người dùng thay vì thay thế nó.** Luận điểm đáng
  trình bày trước giám khảo: ta không giả định người khiếm thị bất lực;
  ta bù đúng phần họ thiếu (biết mình ở đâu trong toà nhà) và dùng đúng
  phần họ giỏi hơn máy (đọc braille).
- **Chưa app nào trong nhóm đối thủ làm.** Đây là điểm khác biệt thật.

### 4.3 Đặc tả node `BrailleConfirm`

| | |
|---|---|
| **ID** | `braille_confirm` |
| **Chạy ở** | Điện thoại (cả hai chế độ) |
| **Kích hoạt** | `Localizer` tin cậy < NGƯỠNG_THẤP **và** vị trí ước tính nằm trong 2 m của một cửa đã biết trong bản đồ |
| **Vào** | `estimated_pose`, `floor_map`, kết quả nhận dạng giọng nói |
| **Ra** | `AnchorSighting(kind="braille", confidence=HIGH)` hoặc `None` |

Luồng:

1. Nói câu hướng dẫn, nêu rõ **bên nào** và **tầm cao nào**. Biển braille
   theo chuẩn đặt ở cạnh mép mở của cửa, tâm cao 1,40–1,50 m.
2. Mở nhận dạng giọng nói, cửa sổ 10 giây.
3. Chuẩn hoá số tiếng Việt thành chữ số: `"sáu không bốn"`,
   `"sáu trăm lẻ bốn"`, `"sáu lẻ tư"` → `"604"`.
4. Đối chiếu `floor_map`. Không có phòng đó → nói "Không tìm thấy phòng
   đó trong bản đồ" và **không** tạo mốc.
5. Khớp → nộp `AnchorSighting` tại toạ độ cửa đó, `confidence = HIGH`,
   và cho phép sửa pose **vượt** ngưỡng nhảy thông thường
   (`ANCHOR_JUMP_BASE_M`) — vì đây là nguồn đáng tin nhất trong hệ.

**Người dùng luôn được phép từ chối.** Im lặng hết 10 giây → bỏ qua,
không hỏi lại trong 60 giây. Không được biến thành thứ phiền.

**Nghiệm thu**: `floor_map` có phòng 604 tại (12,0; 4,0); giả lập đầu
vào giọng nói `"sáu lẻ tư"`; kỳ vọng `AnchorSighting(kind="braille",
x=12.0, y=4.0, confidence=HIGH)`. Với `"chín chín chín"` (không có trong
bản đồ) kỳ vọng `None` kèm một câu báo lỗi.

---

## §5. Năm nguồn vị trí và thứ bậc tin cậy

VIO là **xương sống**: nó cho vị trí tương đối liên tục, mượt, tần số
cao, nhưng **trôi** — sai số tích luỹ theo quãng đường đi, điển hình
1–3% quãng đường trong nhà. Năm nguồn còn lại là **mốc tuyệt đối**: thưa,
gián đoạn, nhưng đặt lại sai số tích luỹ về gần 0.

Không nguồn nào tự sửa pose. Tất cả nộp `AnchorSighting` cho `Localizer`.

| Lớp | Nguồn | Cho gì | Tin cậy | Tần suất thực tế |
|---|---|---|---|---|
| **L0** | VIO (ARCore / ARKit) | x, y, θ tương đối | — (nền) | 30 Hz |
| **L1** | Người xác nhận braille (§4) | x, y tuyệt đối | **HIGH** | vài lần/hành trình |
| **L2** | OCR biển lớn (tầng, thoát hiểm) | x, y tuyệt đối | HIGH / MED | mỗi 10–30 m |
| **L3** | OCR số phòng | x, y tuyệt đối | MED | khi đi ngang cửa |
| **L4** | So khớp bản nền depth (§10) | x, y tuyệt đối | MED / LOW | liên tục, khi có bản nền |
| **L5** | Điểm tụ hành lang (§9) | **chỉ θ** | MED | liên tục trong hành lang |

Quy tắc quyết định trong `Localizer`:

1. Mốc mâu thuẫn với pose hiện tại quá `ANCHOR_JUMP_BASE_M +
   ANCHOR_JUMP_FACTOR × σ` thì **từ chối** (trừ L1 — xem §4.3).
2. Từ chối liên tiếp quá `MAX_CONSECUTIVE_REJECTS` lần → kết luận là
   pose sai chứ không phải mốc sai → chấp nhận mốc, đặt lại σ.
3. Hai mốc cùng hạng cùng khớp mà không cách nhau đủ `SIGN_MARGIN_M` →
   **nhập nhằng** → từ chối cả hai, không sửa gì.

Điểm 3 là phòng thủ cho **nhập nhằng tri giác**: mọi biển "THOÁT HIỂM"
trong toà nhà đọc ra y hệt nhau. Thấy chữ đó không nói lên bạn ở đâu, trừ
khi chỉ có đúng một biển như vậy trong bán kính hợp lý.

---

## §6. Đặc tả từng node

Ký hiệu cột "Chạy ở": **P** = điện thoại luôn, **L** = laptop ở chế độ
DEMO / điện thoại ở chế độ SẢN PHẨM (tức là nằm trong `step()`).

### 6.1 `vio_pose` — đọc pose từ nền tảng (mục 1, 6)

| | |
|---|---|
| Chạy ở | P |
| Vào | `Frame` của ARCore, hoặc `ARFrame` của ARKit |
| Ra | `Pose2D(x, y, theta_deg)` + `tracking_state` |

Chiếu 6-DoF xuống SE(2) vì hệ chỉ chạy trên **một mặt sàn**:

```
map_x     = ar_x
map_y     = ar_z
theta_deg = atan2(dz, dx)  của vector hướng camera đã xoay
```

Đây là phép chiếu **thuận tay trái**. Phải áp dụng **y hệt** cho cả
camera lẫn mốc, nếu không toàn hệ lệch gương. Đã hiện thực ở
`wayfinding/arcore.py` và `ArMath.kt`; bản Swift phải khớp từng bit.

`CAMERA_FORWARD_AXIS = (0, 0, -1)` theo quy ước OpenGL của ARCore.
`IMAGE_NORMAL_AXIS = (0, 1, 0)` — **phải kiểm chứng trên máy thật**;
nếu hướng ngược 180° thì đảo dấu.

**Nghiệm thu**: xoay thiết bị đúng 90° sang phải tại chỗ → `theta_deg`
phải giảm 90 (± 3), `x`, `y` đổi dưới 0,10 m.

### 6.2 `camera_config` — chọn độ phân giải (§3)

| | |
|---|---|
| Chạy ở | P, một lần lúc tạo phiên |
| Ra | `imageSize`, `focal_px`, `principal_point` |

Chọn `imageSize.width` lớn nhất trong các cấu hình hỗ trợ ở 30 fps.
Lấy nội tại qua `frame.camera.imageIntrinsics` — **không cần bàn cờ
hiệu chuẩn**, nền tảng đã cung cấp sẵn.

**Nghiệm thu**: log ra `imageSize` và `focal_px` thực nhận trên Galaxy
A36. Nếu `width < 1280` phải ghi rõ trong báo cáo, vì lớp L3 sẽ gần như
vô dụng.

### 6.3 `sign_ocr` — đọc biển (L2, L3)

| | |
|---|---|
| Chạy ở | P (ML Kit / Vision), luồng riêng, hàng đợi maxsize=1 |
| Vào | ảnh CPU + `focal_px` |
| Ra | danh sách `(text, box, distance_m)` |

Khoảng cách theo mô hình lỗ kim:

```
d = focal_px × H_thực / h_px
```

`H_thực` tra từ `sign_heights()` theo loại biển. Kẹp kết quả vào
[0,2 m; 8,0 m]; ngoài khoảng đó coi như không đo được.

So khớp chữ: bỏ dấu tiếng Việt rồi so khớp mờ (`signtext.py`). "Đ" xử lý
riêng vì không phải tổ hợp dấu. Chỉ cho phép so khớp mờ khi chuỗi dài
≥ `MIN_LEN_FOR_FUZZY` (5), ngưỡng `FUZZY_RATIO` 0,2.

**Nghiệm thu**: in biển "THOÁT HIỂM" cao 100 mm, đặt cách 3,0 m, đo bằng
thước. Kỳ vọng `distance_m` trong [2,6; 3,4].

### 6.4 `depth_obstacle` — cảnh báo vật cản (mục 5)

| | |
|---|---|
| Chạy ở | P (lấy depth) → L (phân loại) |
| Vào | depth map thô + confidence map |
| Ra | tối đa một `Hazard` cho mỗi `Zone` |

Gộp depth thành lưới thô **trên điện thoại** trước khi gửi, để không
đẩy cả ảnh depth qua mạng.

Ba vùng theo tầm cao: `CAO` (ngang đầu), `XA` (thân), `SAN` (mặt sàn).
Ngưỡng: `DANGER_M = 1,5`, `WARN_M = 3,0`, `CLEAR_M = 4,0`,
`MIN_CONFIDENCE = 0,3`.

Năm trạng thái ô — **không phải ba**:

```
TRONG      đo được, xa hơn CLEAR_M          → an toàn
CO_VAT     đo được, gần hơn CLEAR_M         → có vật
CO_DINH    khớp bản nền, vật cố định        → không cảnh báo lặp
TAM_THOI   lệch bản nền, vật mới xuất hiện  → cảnh báo
CHUA_BIET  confidence thấp hoặc không đo được
```

`CHUA_BIET` **phải kiểm tra trước tiên** trong `classify_cell()`. Sai lầm
kinh điển là gộp "không đo được" vào "trống". Kính, mặt nước, bề mặt đen
tuyền, và vật quá gần đều trả depth rác — đúng những thứ nguy hiểm nhất.

`CHUA_BIET` chỉ báo ra ở `Zone.SAN` (hố, bậc, vật thấp). Ở `CAO` và `XA`
thì im lặng, nếu không sẽ báo động suốt.

Cảnh báo ngang tầm đầu là lý do tồn tại quan trọng nhất của lớp này:
**gậy trắng không phát hiện được vật ngang tầm đầu** — cành cây, biển
treo, góc tủ mở, gầm cầu thang.

**Nghiệm thu**: `classify_cell(depth=nan, confidence=0.9)` → `CHUA_BIET`.
`classify_cell(depth=1.0, confidence=0.1)` → `CHUA_BIET`, **không** phải
`CO_VAT`. `classify_cell(depth=5.0, confidence=0.9)` → `TRONG`.

### 6.5 `router` — sinh chỉ dẫn (mục 3)

| | |
|---|---|
| Chạy ở | L |
| Vào | `Pose2D`, `floor_map`, đích |
| Ra | `RouteCue(kind, text, bearing_deg, distance_m)` |

Chỉ dẫn dùng **hệ quy chiếu gắn thân người**, không dùng phương hướng
địa lý: "rẽ phải", không phải "đi về hướng bắc". Khoảng cách nói theo
bước chân khi dưới 10 m ("khoảng mười bước"), theo mét khi xa hơn.

Rẽ chỉ được phát khi tin cậy ≥ MEDIUM. Dưới ngưỡng → giữ hướng hiện tại
và im lặng (nguyên tắc 1.1).

### 6.6 `announce` — chọn nói cái gì

| | |
|---|---|
| Chạy ở | L |
| Vào | `Hazard` + `RouteCue` |
| Ra | tối đa một câu mỗi chu kỳ |

Ba mức ưu tiên, xét theo thứ tự: **(1)** nguy hiểm gấp → **(2)** chỉ
đường → **(3)** nguy hiểm không gấp.

Mỗi kênh có **bộ đệm chống lặp riêng**. Đây là chỗ đã từng sinh lỗi:
dùng chung một bộ đệm khiến hai kênh luân phiên nhau vô hạn, mỗi câu
đều "mới" so với câu ngay trước. `URGENT_REPEAT_S = 4,0`,
`CALM_REPEAT_S = 20,0`.

Rung đi kèm chứ không thay lời nói: một xung = cảnh báo, hai xung = rẽ
phải, ba xung = rẽ trái. Rung đến trước lời nói vài trăm ms vì nó tức thì.

**Nghiệm thu**: nạp xen kẽ một `Hazard` và một `RouteCue` giống hệt nhau
suốt 60 giây. Kỳ vọng số câu nói ≤ 60/4 + 60/20 = 18, không phải hàng trăm.

---

## §7. Cấu trúc dữ liệu chuẩn

Đây là hợp đồng giữa các node. Đổi thì phải đổi đồng loạt cả ba ngôn ngữ.

```
Pose2D:          x: float (m)      y: float (m)      theta_deg: float
AnchorSighting:  kind: str         x: float          y: float
                 confidence: enum{HIGH, MEDIUM, LOW}
                 distance_m: float|None    t: float
Hazard:          zone: enum{CAO, XA, SAN}  distance_m: float
                 cell: enum{...}           urgent: bool
RouteCue:        kind: str         text: str
                 bearing_deg: float        distance_m: float
SensorFrame:     pose: Pose2D      tracking: str
                 depth_grid: float[][]|None
                 sightings: AnchorSighting[]
                 t: float
Decision:        speak: str|None   vibrate: int      pose: Pose2D
                 confidence: enum
```

### 7.1 Lược đồ JSON của cầu nối (chỉ chế độ DEMO)

`POST /update`, khoảng 8 Hz:

```json
{
  "t": 1726000000.123,
  "pose": {"x": 3.21, "y": -1.05, "theta_deg": 87.4},
  "tracking": "TRACKING",
  "intrinsics": {"fx": 1430.2, "fy": 1430.2, "cx": 640.0, "cy": 360.0,
                 "width": 1280, "height": 720},
  "depth_grid": [[3.2, 3.1, 2.8], [4.0, 3.9, 1.4], [5.0, 5.0, 5.0]],
  "depth_conf": [[0.9, 0.9, 0.8], [0.9, 0.9, 0.7], [0.4, 0.4, 0.3]],
  "sightings": [
    {"kind": "sign", "text": "THOAT HIEM", "distance_m": 3.4,
     "bearing_deg": -12.0}
  ]
}
```

Trả về:

```json
{"speak": "Đi thẳng khoảng mười bước.", "vibrate": 0, "confidence": "MEDIUM"}
```

Ghi chú: dấu thập phân trong JSON luôn là **dấu chấm** (`Locale.US` khi
sinh chuỗi trên Android). Chỉ câu **nói** mới dùng dấu phẩy thập phân.

Trường `depth` hiện **chưa được phía Android gửi** — đây là việc còn tồn.

---

## §8. Mục 2 — quét phòng dựng bản nền

Bản nền (`backdrop`) là bản ghi "khi không có ai, chỗ này sâu bao nhiêu".
Có nó thì phân biệt được **cột nhà** (cố định, không cần báo mỗi lần đi
qua) với **người đang đứng chắn** (mới, phải báo).

### 8.1 Quy trình quét

Cần một `run_scan.py` (chưa có trong repo) và một chế độ quét trong app:

1. Người hỗ trợ sáng mắt cầm máy, đi **chậm** một vòng khu vực, quét
   camera trái–phải.
2. Mỗi khung hình: với mỗi ô depth, tính khoá
   `"{cx},{cy},{heading_bin}"` với `DEFAULT_CELL_M = 1,0` và
   `DEFAULT_HEADING_BINS = 12` (mỗi bin 30°).
3. Ghi vào bản nền bằng phép **lấy MAX**, không phải trung bình.

**Vì sao MAX**: vật thể tạm thời chỉ có thể làm depth **ngắn đi**, không
bao giờ dài ra. Lấy max nên người đi ngang trong lúc quét tự động bị
loại, không cần lọc gì thêm.

4. Lưu JSON. Một bản nền gắn với một tầng của một toà nhà.

### 8.2 So sánh khi chạy

```
novel = (d_nền − d_đo) > max(NOVELTY_ABS_M, NOVELTY_REL × d_nền)
```

với `NOVELTY_ABS_M = 0,5`, `NOVELTY_REL = 0,25`. `novel` → `TAM_THOI`,
ngược lại → `CO_DINH`.

Không có bản nền cho ô đó → trả `CO_VAT`, **không** trả `TAM_THOI`.
Chưa biết thì không được vờ như đã biết.

**Nghiệm thu**: quét hành lang trống, rồi cho một người đứng giữa hành
lang. Ô chứa người phải ra `TAM_THOI`; ô chứa tường phải ra `CO_DINH`.

---

## §9. Mục 7 + 10 — chuyển động và lệch hướng ngầm trong ảnh

Hai mục này đến từ Project Guideline, vốn bám một vạch sơn trên mặt đất.
Trong nhà không có vạch sơn — nhưng hành lang cho ta thứ tương đương:
**đường giao tường–sàn** ở hai bên hội tụ về một điểm tụ.

### 9.1 Điểm tụ → sai số hướng (mục 10)

1. Chỉ xét **nửa dưới** khung hình (sàn và chân tường).
2. Dò cạnh, rồi Hough biến đổi lấy các đoạn thẳng.
3. Bỏ đoạn gần ngang (|góc| < 10°) và gần dọc (|góc| > 80°).
4. Gom các giao điểm từng cặp; lấy trung vị → `(u_vp, v_vp)`.
5. Sai số hướng so với trục hành lang:

```
heading_error_deg = degrees( atan( (u_vp − cx) / fx ) )
```

Điều kiện chấp nhận: ít nhất **4 đoạn** đóng góp, và độ phân tán của
các giao điểm dưới `VP_SPREAD_PX = 60`. Không đạt → không có kết quả,
**không đoán**.

Nộp thành `AnchorSighting` hạng **L5**, chỉ sửa θ, không sửa x, y.

### 9.2 Luồng quang → kiểm chứng chuyển động (mục 7)

Không dùng để định vị. Dùng để **bắt lỗi VIO**.

Lấy luồng quang thưa (Lucas–Kanade trên các góc Shi–Tomasi) giữa hai
khung liên tiếp. Độ lớn trung vị của vector luồng cho biết cảnh có đang
dịch chuyển hay không.

Ba trường hợp cần bắt:

| Luồng quang | VIO | Kết luận |
|---|---|---|
| ≈ 0 | báo đang di chuyển | **VIO trôi khi đứng yên** → đóng băng pose |
| lớn | báo đứng yên | VIO mất bám → hạ tin cậy, cảnh báo người dùng |
| lớn, đồng hướng toàn khung | báo đang đi | bình thường |

Trường hợp 1 là lỗi nguy hiểm nhất trong thực tế: người dùng dừng lại
hỏi đường, VIO tích luỹ trôi, hệ thống tưởng họ đã đi thêm 5 m.

**Nghiệm thu**: đặt máy nằm yên trên bàn 60 giây. Luồng quang ≈ 0 suốt.
Pose báo ra phải dịch chuyển dưới 0,20 m trong toàn bộ 60 giây đó.

---

## §10. Mục 11 — bản nền depth làm nguồn định vị

Đây là bước nâng bản nền từ "lọc vật cản" lên "nguồn vị trí" (lớp L4).

Ý tưởng: hình dạng depth quanh một điểm trong hành lang là khá riêng
biệt. Nếu ta đã quét cả tầng, thì có thể **tìm xem hình dạng đang thấy
khớp nhất với chỗ nào trong bản nền**.

### 10.1 Thuật toán

```
Vào:  quan sát depth hiện tại, pose ước tính từ VIO (x0, y0, θ0),
      độ bất định σ
Ra:   AnchorSighting hoặc None

1. Tập ứng viên = các ô trong bản nền cách (x0, y0) dưới
   R = min(3σ, SEARCH_MAX_M = 8,0), và có bin hướng nằm trong
   ±H = 2 bin quanh θ0.

   -- Chỉ tìm quanh ước tính VIO. Tìm toàn tầng sẽ ra nhiều chỗ
      trông giống nhau (mọi hành lang đều giống hành lang).

2. Với mỗi ứng viên c, tính sai lệch:
      err(c) = trung vị theo các ô j của | d_quan_sát[j] − d_nền[c][j] |
   Bỏ qua ô CHUA_BIET ở cả hai phía.
   Cần ít nhất MIN_OVERLAP_CELLS = 8 ô hợp lệ, nếu không bỏ ứng viên.

3. Sắp xếp. Gọi best, second là hai ứng viên tốt nhất.

4. Chấp nhận khi và chỉ khi CẢ BA điều kiện:
      a) err(best) < MATCH_MAX_ERR_M = 0,6
      b) err(second) − err(best) > MATCH_MARGIN_M = 0,3
      c) best cách (x0, y0) dưới R

5. Chấp nhận → AnchorSighting(kind="backdrop", x, y của best,
   confidence = MEDIUM nếu (b) vượt gấp đôi, LOW nếu vừa đủ).
   Không chấp nhận → None. KHÔNG sửa gì cả.
```

Điều kiện (b) là quan trọng nhất. Nó là phòng thủ trực tiếp chống nhập
nhằng tri giác: nếu hai chỗ trong bản nền khớp gần bằng nhau thì ta
không biết mình ở chỗ nào trong hai chỗ đó, và **đoán là tệ hơn không
sửa** (nguyên tắc 1.1).

### 10.2 Vì sao chỉ MEDIUM/LOW

Bản nền được quét một lần. Bàn ghế bị dịch, cửa mở/đóng, người đứng —
tất cả làm bản nền lệch thực tế theo thời gian. Vì vậy L4 **không bao
giờ** được vượt quyền L1/L2. Nó có ích khi đi trong đoạn dài không có
biển nào để đọc.

**Nghiệm thu**: dựng bản nền tổng hợp cho một hành lang thẳng 20 m có
một hốc tường ở mét thứ 7. Cho quan sát lấy tại mét thứ 7. Kỳ vọng khớp
đúng ô đó. Cho quan sát lấy tại mét thứ 3 (đoạn thẳng đều, không có nét
đặc trưng) — kỳ vọng **None**, vì không đủ biên độ (b).

---

## §11. Mục 8 — khoảng cách hình học trong hệ VIO

Hai loại khoảng cách, đừng lẫn:

**(a) Khoảng cách tới một mốc đã lưu** (cách làm của Clew). Cả pose hiện
tại và pose mốc đều nằm trong **cùng một hệ toạ độ VIO**, nên khoảng
cách chỉ là phép trừ:

```
d = hypot(x_mốc − x_hiện_tại, y_mốc − y_hiện_tại)
```

Chính xác tới mức VIO còn chính xác — không cần thị giác, không cần
depth. Đây là lý do cách "đi tới đâu thì ghi lại đường, rồi lần ngược"
của Clew hoạt động tốt: nó không bao giờ cần biết mình ở đâu trong toà
nhà, chỉ cần biết mình ở đâu **so với lúc bắt đầu**.

**(b) Khoảng cách tới vật đang nhìn thấy lần đầu.** Không có pose lưu
sẵn, nên phải đo bằng mô hình lỗ kim (§6.3) hoặc depth (§6.4).

Chuyển đổi giữa hệ camera và hệ bản đồ dùng `cam_from_anchor()` trong
`arcore.py`:

```
T_cam_anchor = inv(T_map_cam) @ T_map_anchor
```

**Nghiệm thu**: ghi một mốc, đi 10 m theo thước dây, quay lại. Khoảng
cách hệ thống báo lúc quay về phải dưới 0,5 m.

---

## §12. Mục 6 — ARKit và iOS

Android để phát triển và kiểm thử; iOS là bản chính thức (VoiceOver là
nền tảng người khiếm thị dùng thật).

| Khái niệm | ARCore | ARKit |
|---|---|---|
| Phiên | `Session` | `ARSession` |
| Cấu hình | `Config` | `ARWorldTrackingConfiguration` |
| Pose | `Frame.camera.pose` | `ARFrame.camera.transform` |
| Ảnh CPU | `acquireCameraImage()` | `ARFrame.capturedImage` (CVPixelBuffer) |
| Nội tại | `camera.imageIntrinsics` | `ARFrame.camera.intrinsics` |
| Độ sâu | Depth API (`acquireDepthImage16Bits`) | `sceneDepth` (chỉ máy có LiDAR) |
| OCR | ML Kit Text Recognition | Vision `VNRecognizeTextRequest` |
| TTS | `TextToSpeech` | `AVSpeechSynthesizer` |
| Đọc màn hình | TalkBack | VoiceOver |

Bốn khác biệt phải xử lý:

1. **Hệ toạ độ.** ARKit dùng thuận tay phải, y hướng lên, giống ARCore
   trên thực tế. Nhưng `capturedImage` xoay 90° so với hướng màn hình —
   phải xoay trước khi OCR, nếu không mọi chữ đều nằm ngang.
2. **LiDAR.** iPhone Pro có `sceneDepth` chất lượng cao hơn hẳn Depth
   API của ARCore. iPhone thường **không có**, chỉ có
   `smoothedSceneDepth` ước lượng bằng ML với chất lượng thấp hơn.
   → Lớp depth phải hoạt động được cả khi **không có** depth. Khi thiếu,
   hạ xuống chỉ dùng L1/L2/L3/L5.
3. **VoiceOver và TTS tranh nhau nói.** Cùng vấn đề với TalkBack: nội
   dung màn hình đi qua vùng sống (accessibility notification), còn chỉ
   dẫn điều hướng đi qua TTS của app. Trong lúc điều hướng phải **tắt**
   thông báo vùng sống, nếu không hai giọng chồng lên nhau.
4. **Chạy nền.** iOS dừng `ARSession` khi app vào nền, gắt hơn Android.
   Phải xử lý phiên bị gián đoạn: `sessionWasInterrupted` → báo người
   dùng, và **không** dùng pose cũ như thể còn đúng.

---

## §13. Thứ tự xây dựng và nghiệm thu từng bước

Mỗi bước chỉ được coi là xong khi qua tiêu chí của nó. Không bước nào
phụ thuộc bước sau.

| # | Việc | Xong khi |
|---|---|---|
| 0 | Gọi `setCameraConfig`, log `imageSize` thật | Biết chắc ảnh CPU rộng bao nhiêu px trên Galaxy A36 |
| 1 | Android gửi `depth_grid` + `depth_conf` | `/update` nhận được depth, `depth.py` phân loại ra 5 trạng thái |
| 2 | Cảnh báo vật cản ngang tầm đầu chạy đầu-cuối | Giơ vật ngang tầm đầu ở 1,2 m → nghe cảnh báo dưới 400 ms |
| 3 | `run_scan.py` + chế độ quét trong app | Quét được một hành lang, ra tệp JSON bản nền |
| 4 | Bản nền phân biệt cố định / tạm thời | Người đứng chắn → `TAM_THOI`; tường → `CO_DINH` |
| 5 | Điểm tụ sửa hướng (§9.1) | Đứng lệch 15° trong hành lang → hệ sửa về dưới 5° |
| 6 | Kiểm chứng luồng quang (§9.2) | Máy nằm yên 60 s → pose trôi dưới 0,20 m |
| 7 | `BrailleConfirm` (§4.3) | Nói "sáu lẻ tư" → pose nhảy về đúng toạ độ phòng 604 |
| 8 | So khớp bản nền định vị (§10) | Qua cả hai ca nghiệm thu §10.2, kể cả ca trả `None` |
| 9 | Port lõi sang Kotlin | Bộ test Kotlin ra kết quả trùng bộ test Python |
| 10 | Chạy độc lập trên điện thoại | **Tắt WiFi**, đi trọn một hành trình |
| 11 | Bản iOS | Đi trọn một hành trình bằng VoiceOver |

Bước 10 là mốc quan trọng nhất về mặt chấm điểm: nó là ranh giới giữa
"bản trình diễn" và "sản phẩm". Nên đạt nó **trước** ngày thi, không
phải trong ngày thi.

### 13.1 Chỉ tiêu đo lường

`metrics.py` đã giữ sẵn 9 chỉ tiêu. Ba chỉ tiêu quan trọng nhất:

```
missed_obstacles   == 0      -- bỏ sót vật cản là hỏng, không thương lượng
interventions      == 0      -- không được cần người sáng mắt can thiệp
alert_latency_ms   <= 400    -- chậm hơn thì người dùng đã va vào rồi
```

`missed_obstacles == 0` là chỉ tiêu tuyệt đối, khác với
`false_alarms_per_min <= 1,0` vốn chỉ là chỉ tiêu dễ chịu. Đánh đổi luôn
nghiêng về phía báo thừa còn hơn bỏ sót — nhưng chỉ trong giới hạn: báo
thừa quá nhiều thì người dùng tắt app, và lúc đó tỉ lệ bỏ sót thành 100%.

---

## §14. Những việc còn tồn, không thuộc phần code

Các mục này cần đi thực địa, không LLM nào làm thay được:

- Đo chiều cao chữ **thật** của biển phòng và biển tầng tại RMIT Nam Sài
  Gòn. Toàn bộ §3.2 phụ thuộc con số này.
- Đo độ trôi VIO thật trên quãng 50 m, để đặt `ANCHOR_JUMP_FACTOR` cho đúng.
- Xác nhận có biển braille ở RMIT không, và đặt ở đâu. Nếu không có thì
  §4 phải chuyển sang phương án khác (người dùng đọc số phòng in nổi,
  hoặc bỏ hẳn lớp L1).
- Thử nghiệm OCR tại chỗ dưới ánh đèn thật.
- Liên hệ tổ chức người khiếm thị để có người dùng thật thử.

---

## §15. Đã hiện thực — bổ sung ngoài đặc tả gốc

Phần này ghi những gì **đã code xong** và những tính năng **thêm mới** so
với đặc tả gốc, kèm lý do. Lịch sử chi tiết ở `THAYDOI_2026-09-12.md`.

Mốc kiểm thử: **739 test**, chạy `cd adc_wayfinding && python3 -m pytest tests/ -q`.

### §15.1. Sửa đặc tả: bốn trạng thái → hai trục

§6.4 nêu "năm trạng thái ô", nhưng năm giá trị đó trộn **hai trục khác
nhau**. Một cột nhà trong hành lang đã quét thì **vừa** `CO_VAT` (đo được)
**vừa** `CO_DINH` (khớp bản nền) — enum phẳng buộc phải vứt một trong hai.

```
Cell     = TRONG | CO_VAT | CHUA_BIET       ← thuần đo độ sâu
Novelty  = CO_DINH | TAM_THOI | KHONG_RO    ← thuần so bản nền
```

`Backdrop.classify()` đổi tên thành `Backdrop.refine()`, trả `list[Novelty]`.
`Hazard` mang cả hai trường. **Đây là đổi hợp đồng dữ liệu §7** — port sang
Kotlin/Swift phải đổi đồng loạt.

### §15.2. Lớp ArUco đã gỡ hoàn toàn

Gỡ **cả code lẫn test**, không phải chỉ test — code còn chạy được mà mất
lưới an toàn thì tệ hơn cả hai. Đã xoá `ArucoAnchorDetector`, nguồn
`"aruco"`, cờ `--aruco`, `tools/generate_markers.py`, và chế độ camera của
`run_panel.py`.

`AnchorSource` hiện là: `ocr` | `sign` | `braille` | `backdrop`.

### §15.3. Tính năng thêm mới

| Module | Việc | Vì sao thêm |
|---|---|---|
| `objects.py` | Nhận diện đồ vật, ghép nhãn với độ sâu | Độ sâu nói "có gì đó cách 1,2 m"; lớp này nói "đó là cái gì". Biết là ghế hay người thì người dùng xử lý khác hẳn |
| `places.py` | Đánh dấu địa điểm (hướng B + C) | Thiết kế gốc bắt người khiếm thị tự đi quét — tự mâu thuẫn: nếu họ đã đi thạo được thì đã không cần hệ thống |
| `floors.py` | Biết đang ở tầng mấy bằng khí áp kế | Đặc tả gốc ngầm giả định người dùng **đã ở đúng tầng**. Thực tế phải đi thang máy trước |
| `power.py` | Điều tiết nhịp xử lý | Độ trễ và hao pin có **chung một lời giải** |
| `corridor.py` | Điểm tụ (L5) + luồng quang bắt lỗi VIO | §9.1 và §9.2 của đặc tả |
| `braille.py` | Xác nhận bằng biển chữ nổi (L1) | §4 của đặc tả, **thêm hai lớp phòng thủ** |

### §15.4. `places.py` — chống hiểu nhầm chỗ cũ thành chỗ mới

Vị trí ước tính luôn lệch ít nhiều, nên so bằng khoảng cách một mình sẽ
hoặc tạo 5 marker cho cùng một cái bàn, hoặc gộp hai cái bàn khác nhau làm
một. Cái thứ hai nguy hiểm hơn: chỉ đường tới một chỗ hoàn toàn khác mà vẫn
tự tin.

Đối chiếu **bốn dấu hiệu độc lập**:

| Dấu hiệu | Vai trò |
|---|---|
| Tầng | Rẻ nhất, dứt khoát nhất |
| Khoảng cách, bán kính **nở theo độ trôi** | Định vị chắc thì khắt khe, đang trôi thì rộng lượng |
| Hình dạng độ sâu | **Độc lập với vị trí** — bắt được ca khoảng cách bỏ sót |
| Hơn hẳn chỗ nhì | Cùng nguyên tắc với biển trùng chữ và §10 |

Không đủ chắc thì **hỏi**, không tự quyết.

### §15.5. `floors.py` — nhiều tầng

Đoạn trong cabin là chỗ VIO gần như chắc chắn hỏng: kim loại kín, chuyển
động thẳng đứng, rung động. Khí áp kế không dính gì tới ba vấn đề đó.

**Chỉ dùng chênh lệch tương đối**, không bao giờ tính độ cao tuyệt đối — độ
cao tuyệt đối cần áp suất quy chiếu, mà giá trị đó đổi theo thời tiết suốt
ngày.

**Bù trôi thời tiết là bắt buộc**, không phải tối ưu: không bù thì người
dùng **ngồi yên tại bàn một tiếng** sẽ được báo đã đổi 3-6 tầng. Tốc độ bù
nằm giữa hai thang thời gian — thời tiết ~0,04 Pa/giây phải bị triệt tiêu,
thang máy ~4 Pa/giây phải giữ nguyên.

**Máy không có khí áp kế:** ước bằng thời gian trong cabin, **luôn** trả tin
cậy "thấp" và hệ thống phải hỏi lại — thời gian trong cabin còn gồm chờ cửa
và dừng ở tầng trung gian.

**Quyền:** Android không cần gì. iOS **cần** Motion & Fitness — thiếu
`NSMotionUsageDescription` trong Info.plist thì iOS **giết app** ngay khi gọi
`CMAltimeter`, lỗi im lặng. Phải xin quyền **sớm ở màn hình thiết lập**, vì
iOS chỉ hiện hộp thoại khi app ở tiền cảnh.

### §15.6. `power.py` — độ trễ và pin

Ba tầng, giá tăng dần:

| Tầng | Giá | Khi nào chạy |
|---|---|---|
| Độ sâu | ~2 ms | **Luôn** |
| Nhận diện đồ vật | ~40 ms | Khi tầng 1 thấy có gì |
| Đọc biển OCR | ~500 ms | Khi cần mốc neo |

Tầng 1 trả lời "có gì phía trước không"; chỉ khi nó nói **có** thì tầng 2
mới đáng chạy — câu hỏi "đó là cái gì" vô nghĩa khi không có gì.

**Độ trễ giảm** vì lúc có vật thật, bộ xử lý đang rảnh. **Pin giảm** vì
80-90% khung hình hành lang trống không kích hoạt tầng 2 và 3. Không đánh
đổi chất lượng: vật cản vẫn phát hiện ở tầng 1 với đầy đủ tốc độ.

Hai ràng buộc an toàn **không được đánh đổi lấy pin**:

- Không đo được độ sâu → **CẢNH GIÁC**, không phải NGHỈ.
- Máy nóng vượt 40°C → **hạ tải**, và không bao giờ lên mức KHẨN — không
  phải để bảo vệ phần cứng mà để tránh bị hệ điều hành bóp hiệu năng đột
  ngột giữa lúc đang đi.

### §15.7. Hợp đồng JSON đã mở rộng

Điện thoại gửi thêm: `depth`, `intrinsics`, `voice`, `objects`, `pressure`,
`thermal`.

Laptop trả thêm: `listen` (bảo điện thoại bật micro), `nhip_ms` (bảo điện
thoại giãn hay đẩy nhịp gửi).

Trong `depth`, giá trị **0 nghĩa là không đo được**, không phải "cách 0 mét".

### §15.8. Lỗi ẩn đã tìm ra và sửa

Ghi lại để không ai vô tình khôi phục lại chúng.

| Lỗi | Hậu quả nếu không sửa |
|---|---|
| Chuỗi TTS **không dấu** | Bộ đọc tiếng Việt phát ra âm vô nghĩa — hỏng kênh đầu ra duy nhất |
| Ghép ảnh độ sâu **đã làm mượt** với độ tin cậy ảnh **thô** | Mỗi ô nhận độ tin cậy của một chỗ khác — sai im lặng |
| Trung vị/trung bình **pha loãng** đặc trưng nhỏ | Vật nhỏ vô hình trước thuật toán khớp |
| Chỉ xét **tâm ô** trong hộp bao | Cột đèn hẹp không lấy được khoảng cách → bỏ qua hoàn toàn |
| Chốt tầng **giữa chừng** chuyến đi | Nghe hai câu báo đổi tầng cho một chuyến |
| Kiểm ổn định trên giá trị **đã làm mượt** | Báo đổi tầng chậm ~11 giây, người dùng đã ra khỏi cabin |
| **Không bù trôi thời tiết** | Ngồi yên một tiếng bị báo đã đổi 3-6 tầng |
| Tên địa điểm **rỗng** được chấp nhận | Không bao giờ gọi lại được bằng giọng nói |
| Ngoài bán kính thì **bỏ qua hình dạng** | Âm thầm tạo marker trùng khi trôi xa |
| `"không"` vừa là số 0 vừa là từ phủ định | Mọi câu **từ chối** thành một lần khai báo số phòng |

### §15.9. Bỏ ràng buộc hiệu chỉnh camera

`run_live.py` từng **thoát hẳn** nếu thiếu `camera.npz`, trong khi dòng
ngay dưới đặt `K = dist = None` và không dùng đến — đòi một tệp rồi bỏ
qua chính tệp đó. Hậu quả: phải in bảng cờ vua mới chạy thử được.

Đã bỏ. Tiêu cự lấy theo thứ tự ưu tiên: `camera.npz` nếu có → thông số
nội tại từ ARCore/ARKit (đường điện thoại) → `uoc_focal_px()` ước từ góc
nhìn ngang 65° (đường webcam). Biển cao 100 mm ở 1-3 m đo lại bằng ước
lượng cho sai số dưới 2%.

`calibrate.py` giữ lại làm **công cụ tuỳ chọn**.

### §15.10. Còn tồn

- Bản **iOS**: chưa có dự án Xcode, và không có máy Mac để biên dịch. Lõi
  quyết định đã thuần số, bản Swift chỉ cần lớp vỏ gọi `sceneDepth`,
  `CMAltimeter`, và Vision rồi nộp vào cùng lõi.
- **Bản đồ nhiều tầng**: `floors.py` biết đang ở tầng mấy, nhưng vẫn chỉ có
  **một** file bản đồ. Cần lớp "bản đồ toà nhà" biết tầng nào dùng file nào
  và tráo bản đồ khi đổi tầng.
- Các hằng số ở §14 vẫn **chưa đo thực địa**.

---

## §16. Mở rộng sang người neurodivergent

Hai tính năng đưa sản phẩm phục vụ thêm người tự kỷ và ADHD, **không phải
xây lại lõi**. Cơ sở khoa học: hệ thống ASSIST (Nair và cộng sự, ECCV
Workshop 2018) đã chứng minh một hệ định vị trong nhà phục vụ được cả
người khiếm thị lẫn người thuộc phổ tự kỷ, bằng cách dùng **chung lõi,
khác giao diện**.

### §16.1. Vì sao kiến trúc sẵn có đã hợp

Nhiều thứ xây cho người khiếm thị vốn đã giải đúng nhu cầu neurodivergent:

| Đã có | Vốn để | Cũng đúng nhu cầu |
|---|---|---|
| Bộ đệm chống lặp từng kênh (`announce.py`) | Tránh nói liên miên | Quản lý tải giác quan |
| "Thà im còn hơn nói sai" | An toàn | Khả năng dự đoán |
| Câu ngắn, hệ quy chiếu gắn thân người | Không thấy đường | Giảm tải nhận thức |
| Điều tiết nhịp (`power.py`) | Tiết kiệm pin | Giảm mật độ thông tin |
| `objects.py` nhận diện `"person"` | Cảnh báo va chạm | Nền tảng đếm mật độ đám đông |
| `shortest_path_multi(allow_edge=)` | Loại thang máy khi cháy | Hook sẵn cho tuyến tránh đông |

Đây là hiệu ứng **lề dốc**: cái làm cho một nhóm thường làm cho tất cả dễ
hơn.

### §16.2. Tuyến yên tĩnh — đã cân nhắc và loại bỏ

`crowd.py` từng hiện thực ý tưởng tránh hành lang đông người. **Đã gỡ
bỏ hoàn toàn** ngày 15/09/2026.

Lý do: cơ chế cần hai điều kiện, và không điều kiện nào thoả được trong
khung thời gian hackathon.

1. **Bản đồ phải có đường vòng.** `map_floor3.json` là một chuỗi thẳng —
   trên đó không bao giờ có gì để chọn.
2. **Sổ mật độ phải tích luỹ qua nhiều tuần** mới đủ số liệu dùng được.
   Lần chạy đầu sổ trống, và hệ thống không tránh gì cả.

Nên tính năng sẽ không trình diễn được gì tại hội trường. Giữ một tính
năng không demo được là rủi ro, không phải điểm cộng.

**Phần giữ lại**: tham số `edge_cost` trong `shortest_path_multi()` và
`build_route()`. Đó là hạ tầng tổng quát (đường ngắn nhất theo trọng số
tuỳ chỉnh), không gắn riêng với mật độ người. Khác biệt với `allow_edge`
vẫn là điểm thiết kế cốt lõi:

```
allow_edge  → "tuyệt đối không được đi lối này"
edge_cost   → "lối này đi được, nhưng đắt hơn"
```

Cấm hẳn một hành lang có thể làm **đích không tới được**, và lúc đó hệ
thống im lặng thay vì đưa ra đường dài hơn.

Gỡ `crowd.py` làm mất toàn bộ lớp phủ kiểm thử của `edge_cost` — nó
trước đó chỉ được kiểm **gián tiếp** qua các test của lớp mật độ. Giữ
một tham số mà không còn lưới an toàn nào là trạng thái tệ hơn cả hai
lựa chọn, nên `tests/test_edge_cost.py` kiểm nó trực tiếp.


### §16.3. `preview.py` — xem trước hành trình

**Cái bẫy quan trọng nhất, ngược trực giác:** đọc cả lộ trình một lượt là
phản tác dụng. Giới hạn trí nhớ làm việc bằng lời là **ba đến năm đơn
vị**, Cowan đề xuất **bốn**. Tuyến 6 chặng đọc liền mạch sẽ vượt giới hạn,
và người có ADHD mất phần giữa — tính năng định giúp họ lại làm khó họ.

Nên chia khối, đọc **theo yêu cầu**:

```
tóm tắt   "2 lần rẽ, 1 lần đổi tầng, khoảng 4 phút."   ≤ 4 đơn vị
từng chặng  mỗi lần một chặng, người dùng tự hỏi tiếp
luôn luôn   nói CÒN BAO NHIÊU chặng
```

`lap_lai()` là bắt buộc: người có khó khăn trí nhớ làm việc sẽ bỏ lỡ một
câu và **không thể** đọc lại màn hình như người sáng mắt.

### §16.4. `timeblind.py` — chống mù thời gian

Trụ cột của phần ADHD. Đặc tả đủ để hiện thực lại từ đầu.

**Vấn đề đúng phải giải.** Câu *"khoảng 4 phút"* không giải quyết gì cả.
Nó là một khoảng **trôi nổi**, và vẫn đòi người dùng tự làm ba phép tính
trong đầu: bây giờ mấy giờ, cộng 4 phút là mấy giờ, so với giờ vào lớp
thì sao. Ba phép đó chính là thứ người mù thời gian khó làm.

**Đơn vị.** Mọi phép tính dùng *phút tính từ nửa đêm* (0–1440, float).
Không dùng epoch, không dùng `datetime`. Nhờ vậy toàn bộ logic kiểm thử
được bằng số thuần, không phụ thuộc múi giờ của máy chạy test. Chuyển
đổi từ đồng hồ thật nằm ở đúng một chỗ: `phut_trong_ngay()`.

**Công thức đệm an toàn.**

```
dem = phut_di × DEM_TY_LE + DEM_KHOI_DONG_PHUT
      (0,20)                (1,5 phút)

phut_can          = phut_di + dem
phut_truoc_khi_di = (gio_hen − bay_gio) − phut_can
gio_phai_di       = gio_hen − phut_can
```

Đệm có **hai thành phần** vì có hai nguồn trễ khác nhau:

| Thành phần | Nguồn trễ | Vì sao dạng đó |
|---|---|---|
| Tỷ lệ 20% | Trễ tích luỹ theo quãng đường: đi chậm hơn ước lượng, dừng tránh người, đọc biển sai phải quay lại | Càng đi xa càng nhiều cơ hội lệch → phải tỷ lệ thuận |
| Hằng số 1,5 phút | Chi phí khởi động cố định: ra khỏi phòng, định hướng lần đầu, lần rẽ đầu tiên | Không đổi theo độ dài tuyến |

Chỉ dùng tỷ lệ thì tuyến ngắn gần như không có đệm. Chỉ dùng hằng số thì
tuyến dài bị đệm thiếu.

**Ngưỡng phân mức**, theo `phut_truoc_khi_di`:

| Mức | Điều kiện | Giọng |
|---|---|---|
| `DA_TRE` | < 0 | Nói rõ muộn bao nhiêu phút, kèm việc phải làm |
| `DI_NGAY` | < 2,0 | *"Bạn cần đi ngay bây giờ để không trễ."* |
| `SAP_DEN_GIO` | ≤ 10,0 | *"…bạn cần bắt đầu đi trong N phút nữa."* |
| `SOM` | > 10,0 | Nói mốc khởi hành trên đồng hồ |

`NGUONG_GAP_PHUT = 2.0` không được đặt thấp hơn: người dùng còn phải
**nghe hết câu**, hiểu, rồi đứng dậy. Báo "còn 30 giây" thì câu báo
chính nó đã ăn hết thời gian.

Trên `NGUONG_DOC_SO_PHUT = 120`, **không đọc số phút đếm ngược nữa**,
chỉ nói mốc đồng hồ. *"Còn 821 phút nữa"* đúng về số học nhưng vô dụng
về thực tế.

**Ràng buộc cứng về câu nói.** Mọi câu phải kết thúc bằng **một việc cụ
thể phải làm**. Câu kiểu *"sắp trễ rồi"* không kèm hành động là vô dụng:
nó chỉ thêm lo âu mà không giảm được gì. Có test khoá điều này cho cả
bốn mức.

**Nhắc trong lúc đi** (`BoNhacGio`). Mốc `(10, 5, 3, 1)` phút còn lại
tới giờ hẹn — thưa dần về cuối, vì càng gần giờ thì một phút càng đáng
giá.

Mỗi lần nhắc **bắt buộc có con số phút**. Chặng đường là thông tin kèm
theo, không phải thông tin chính: *"còn 2 chặng"* trả lời câu hỏi **còn
bao xa**; nó không trả lời **còn kịp không**. Người ADHD có thể đi đúng
tiến độ về khoảng cách mà không có khái niệm nó tương ứng bao nhiêu phút.

Khi một mốc phát, **mọi mốc đã qua đều bị đánh dấu**, không chỉ mốc vừa
khớp. Thiếu điều này thì mất sóng một lúc rồi có lại sẽ đọc liên tiếp
bốn câu gần giống hệt nhau.

Quá giờ hẹn: báo **đúng một lần**, và **không trách móc**. ADHD thường
đi kèm nhạy cảm với thất bại; một câu trách sẽ làm người dùng tránh mở
app — ngược hoàn toàn với mục đích.

### §16.5. `mach.py` — giữ mạch chuyến đi

Dừng lại giữa đường rồi quên mất đang đi đâu là chuyện xảy ra **hằng
ngày** với người ADHD, không phải sự cố.

Hành vi mặc định của mọi hệ chỉ đường — người dùng đi lại thì nói *"rẽ
phải"* — giả định họ **vẫn còn** giữ ngữ cảnh trong đầu. Với đúng nhóm
người sản phẩm này phục vụ, giả định đó sai.

**Ngưỡng phát hiện.** `NGUONG_PHAN_TAM_S = 90`. Dưới ngưỡng là chuyện
bình thường trong lúc đi: chờ thang máy, nhường đường, chỉnh dây đeo.
Con số này là **ước lượng, chưa đo bằng người dùng thật**.

Trạng thái "đang đi hay đứng yên" **không tự đo lại** mà lấy từ
`power.py` (`MucHoatDong.NGHI`). Hai chỗ cùng đo một thứ sẽ lệch nhau
rồi sinh lỗi rất khó tìm.

**Câu khôi phục phải có đủ ba phần, theo đúng thứ tự:**

```
(a) đang đi đâu   → "Bạn đang trên đường tới phòng 6.04"
(b) để làm gì     → "để nộp đơn xin nghỉ"
(c) việc trước mắt → "Còn 2 chặng. Rẽ phải ở đây."
```

Bỏ (a) hoặc (b) là quay về đúng hành vi mà tính năng này sinh ra để sửa.
Đảo thứ tự sẽ làm phần chỉ dẫn trôi nổi giữa một câu dài — mà chỉ dẫn là
thứ duy nhất cần hành động ngay.

**Mục đích chuyến đi** là chuỗi tự do, hỏi **một lần**, không bắt trả
lời. Từ chối (*"không"*, *"thôi"*, *"bỏ qua"*) hoặc im lặng đều đánh dấu
đã hỏi rồi thôi — hỏi lại là làm phiền. Câu trả lời dưới 3 ký tự bị loại:
người dùng lẩm bẩm một tiếng, hoặc micro bắt được tiếng ồn, sẽ thành một
câu vô nghĩa đọc lại lúc tới nơi.

### §16.6. `meety.py` — tóm tắt biên bản cuộc họp

Meety là **chương trình độc lập**, không phải thư viện. Ranh giới là
tiến trình con: dòng lệnh vào, tệp JSON ra. Không copy code của nó.

**Sơ đồ dữ liệu thật** (đã kiểm trên kết quả thật, không đoán từ tài
liệu): kết quả **không có** `tldr` hay `paragraphs` ở cấp một. `tldr`
nằm trong `executive_summary.tldr` và là **một danh sách câu**. Phần nội
dung chia theo `chapters`.

Đường chạy cho demo: `--skip-stt --mock` → không cần API key, không gọi
mạng, xong trong vài giây.

Lớp này **không bao giờ ném ngoại lệ**: bên gọi nằm trong vòng lặp thời
gian thực, và một ngoại lệ lọt ra sẽ làm dừng cả phiên chỉ đường đang
chạy. Mọi đường thất bại trả về một câu tiếng Việt có dấu để đọc lên.

### §16.7. `dongvien.py` — phản hồi tích cực và bạn đồng hành

Hai việc, một nguyên tắc chung. Cả hai là lớp đặt **lên trên** cơ chế đã
có — không tạo khái niệm mới nào.

**Xong một chặng.** Tê liệt trước nhiệm vụ (task paralysis) là khi một
việc trông quá lớn nên không bắt đầu được. Cách gỡ thông thường là chia
nhỏ ra và đánh dấu từng phần xong. Một lộ trình **vốn đã** được chia sẵn
thành các chặng, nên ở đây không thiết kế lại gì — chỉ làm cho mỗi chặng
xong **có cảm giác** là xong.

Phản hồi là **rung nhẹ + âm ngắn**, không phải câu nói. Một cái rung đúng
lúc tốt hơn một câu nói dài: nó không chiếm kênh tai và không cắt ngang
dòng suy nghĩ.

Mã rung `xong_chang = [40, 60, 40]`. Tổng thời lượng **phải nhỏ hơn** mã
cảnh báo nguy hiểm — đây là lời khen, không phải cảnh báo, và rung mạnh
bằng cảnh báo sẽ làm người dùng học sai ý nghĩa của mã rung. Có test khoá
điều này.

Chỉ báo khi `leg_index` **tăng**. Đi lạc rớt về chặng trước không phải
thành tựu gì, và càng không phải lúc để khen.

**Bạn đồng hành.** Bốn trạng thái, **ba trong số đó tích cực**:

| Trạng thái | Khi nào | Âm thanh |
|---|---|---|
| `TU_HAO` | Chuỗi ≥ 3 ngày đi đúng giờ | có |
| `VUI` | Tới đích đúng giờ | có |
| `THONG_CAM` | Vừa khôi phục mạch sau phân tâm | **không** |
| `BINH_THUONG` | Mặc định, và cả khi tới muộn | không |

`THONG_CAM` cố ý **không có âm thanh**: người dùng vừa bị phân tâm và
đang được dựng lại ngữ cảnh — thêm một tiếng động là thêm một thứ phải
xử lý, đúng lúc họ cần ít thứ phải xử lý nhất.

**Ràng buộc cứng: không có trạng thái tiêu cực nào.** Không buồn, không
thất vọng, không trách móc — kể cả khi người dùng trễ giờ, đi lạc, hay bỏ
dở chuyến đi. Trạng thái xấu nhất có thể xảy ra là `BINH_THUONG`, tức là
**không khen**, chứ không bao giờ là **chê**.

Đây không phải lựa chọn về giọng điệu. ADHD thường đi kèm nhạy cảm với sự
từ chối và thất bại: một nhân vật tỏ ra thất vọng sẽ làm người dùng
**tránh mở app**, và lúc đó mọi tính năng khác đều thành vô dụng, kể cả
những tính năng đang chạy tốt.

Có ba test khoá ràng buộc này: không enum nào chứa từ tiêu cực, không câu
nào trách móc, và tới đích muộn phải ra `BINH_THUONG`.

**Chuỗi ngày** đếm theo **ngày**, không theo chuyến đi. Đếm theo chuyến đi
sẽ thưởng người đi nhiều và phạt người đi ít, mà số chuyến đi một ngày
không nói lên điều gì về việc giữ giờ. Ngưỡng 3 ngày chọn thấp có chủ ý:
chuỗi dài quá thì phần lớn người dùng không bao giờ chạm tới, và một phần
thưởng không bao giờ nhận được thì không phải phần thưởng.

### §16.8. Giới hạn và yêu cầu mới

**Chưa thử với người dùng thật** ở cả hai nhóm.

**Ngưỡng 90 giây và đệm 20% đều là ước lượng.** Cả hai cần đo lại bằng
người dùng thật rồi sửa ở đúng một chỗ.

**Lớp nhắc trước bằng thông báo hệ thống chỉ chạy trên Android** — nó
dùng `AlarmManager`, nên không xuất hiện trong bản demo chạy trên laptop.

**Kênh hình ảnh mới chỉ có một màn hình.** `TimerTronView` vẽ được đĩa
đếm ngược, nhưng phần còn lại của chế độ ADHD (bạn đồng hành, chọn mức
độ chi tiết) chưa làm. Quyết định thiết kế cho cả hai nằm ở
`docs/UIUX_QUYET_DINH.md`.

**Bản đồ mẫu vẫn là một chuỗi thẳng.** Không ảnh hưởng tới các tính năng
ở trên, nhưng cần nhớ khi đọc kết quả chạy thử: mọi lộ trình trên bản đồ
này đều chỉ có một lối đi.
