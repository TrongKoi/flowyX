# Hệ thống chỉ đường trong nhà — ADC 2026

Bản mã nguồn Giai đoạn 1 theo tài liệu `ADC2026_HuongDan_XayDung.docx`.
Toàn bộ lõi chạy trên laptop, có sẵn chỗ cắm ARCore để đưa lên điện thoại sau.

**Trạng thái:** 543/543 test qua. Đủ 6 kịch bản, nhiều tầng, và bộ công cụ chạy thật ngoài đời. Giai đoạn 1–4 đã code xong. Bản mô phỏng chạy
trọn tuyến, sai số định vị tối đa 0.05m. Bản webcam và bản điện thoại đã viết
xong nhưng **chưa chạy thử với phần cứng thật**.

---

## Chạy thử ngay (không cần camera)

```bash
pip install numpy opencv-python
python3 run_sim.py
```

Ba ca kiểm thử quan trọng:

```bash
python3 run_sim.py --detour       # đi lạc → cơ chế phục hồi
python3 run_sim.py --no-anchors   # không có mốc → từ chối chỉ đường
python3 run_sim.py --to R16 --drift 0.06   # VIO trôi nặng
```

Chạy test:

```bash
pip install pytest
python3 -m pytest tests/ -v
```

---

## Quy trình đầy đủ với camera thật

**Bước 1 — Hiệu chỉnh camera** (bắt buộc làm trước, ~30 phút)

In mẫu bảng cờ vua 9x6 giao điểm trong, dán phẳng lên bìa cứng, đo cạnh
một ô bằng thước.

```bash
python3 tools/calibrate.py --capture --square 0.025
```

SPACE để lưu ảnh (cần ít nhất 15 ảnh, nhiều góc khác nhau), Q để xong.
Kết quả lưu vào `camera.npz`. Nếu sai số tái chiếu > 1px thì chụp lại.

**Bước 2 — Sinh và in mã**

```bash
```

`--tile` chia mỗi mã thành 4 tờ A4 để in ở máy in trường rồi ghép — rẻ hơn
in A3 ở tiệm. In **giấy mờ**, không dùng giấy bóng.

**Đo lại cạnh mã sau khi in bằng thước.** Máy in co giãn vài phần trăm, và
con số đo được mới là con số đưa vào `--marker-size`.

**Bước 3 — Dựng bản đồ**

Sửa `config/map_floor3.json`. Chốt gốc toạ độ trước và không đổi. Mã và biển
số phòng nằm **trên tường**, lệch khỏi tim hành lang khoảng 0.9m — không đặt
trùng toạ độ với nút.

Trường `hazard` là trường quan trọng nhất: mọi cạnh đi ngang cầu thang, bậc
hụt, cửa kính đều phải ghi.

**Bước 4 — Chạy**

```bash
python3 run_live.py --to R12 --marker-size 0.198 --show
python3 run_live.py --to R12 --speak      # đọc thành tiếng
python3 run_live.py --to R12 --ocr        # bật thêm lớp OCR (chậm)
```

Lớp OCR cần `pip install easyocr` (khá nặng). Không bật thì chỉ dùng ArUco.

---

## Giai đoạn 3 — đưa lên điện thoại

Điện thoại làm **cảm biến**, laptop làm **bộ não**. Dùng lại toàn bộ code
Giai đoạn 1, chỉ thay nguồn cảm biến.

```bash
python3 run_bridge.py --to R12 --record runs.json --tester Nam
```

Kiểm thử **không cần điện thoại thật**, mở cửa sổ thứ hai:

```bash
python3 tools/android_sim.py --url http://127.0.0.1:8765
```

`android_sim.py` sinh tư thế ARCore 6 bậc tự do rồi cho chạy qua đúng phần
toán mà app Android dùng (`wayfinding/arcore.py`) — nên nó kiểm chứng được cả
phần đổi hệ toạ độ, thứ mà `phone_sim.py` không kiểm chứng được vì gửi thẳng
toạ độ 2D đã biết sẵn.

Mã nguồn app Android nằm ở `android/`, xem `android/README.md`.

Màn hình sẽ hiện địa chỉ để trỏ điện thoại tới. Kiểm thử **không cần điện
thoại thật**, mở cửa sổ thứ hai:

```bash
python3 tools/phone_sim.py --url http://127.0.0.1:8765
```

### Giao thức

`POST /update` — điện thoại gửi lên:

```json
{
  "pose": {"x": 1.5, "y": 1.2, "z": -3.0, "yaw": 90},
  "markers": [{"id": "11", "x": 2.3, "y": 0.1, "theta": 180,
               "distance": 2.3, "quality": 0.8}],
  "jpeg": "<base64, tuỳ chọn>",
  "battery": 87.5
}
```

Trả về:

```json
{
  "say": "Còn khoảng 5 mét nữa rẽ phải. Cột vuông ở góc, sờ được bên phải",
  "haptic": "two_pulse",
  "confidence": "cao",
  "state": "dang_di",
  "position": {"x": 18.5, "y": 7.2, "theta": 90.0}
}
```

Hai chế độ, chọn cái nào chạy được trước:

- **Điện thoại tự nhận mã** (ARCore Augmented Images) → gửi mảng `markers`.
  Nhẹ, nhanh, không cần `camera.npz`.
- **Điện thoại gửi ảnh** → gửi `jpeg`, laptop nhận diện. Cần `camera.npz`
  nhưng không phải tích hợp OpenCV vào Android.

ARCore dùng trục y hướng lên, mặt phẳng đi lại là x-z. Chuyển đổi nằm trong
`bridge.parse_update()`, phần còn lại của hệ thống không phải biết.

**Khi pitch phải nói thật:** đây là kiến trúc bản mẫu để chứng minh nguyên lý;
bản sản phẩm sẽ chạy hoàn toàn trên thiết bị.

---

## Kịch bản C — đọc biển, tài liệu, bảng trắng

Kịch bản pivot thứ hai (Mục 2 của tài liệu). Rẻ và nhanh nhất trong sáu kịch
bản vì dùng lại gần như toàn bộ lõi: khối OCR chính là lớp định vị chính của
kịch bản A, khối giọng nói đã có sẵn chống lặp và cắt lời.

```bash
python3 run_reader.py --demo     # không cần camera lẫn easyocr
python3 run_reader.py --image to_roi.jpg
python3 run_reader.py --speak    # webcam, đọc thành tiếng
```

Phím: `n` đoạn tiếp, `p` đoạn trước, `r` đọc lại, `a` làm mới, `q` thoát.

Ba thứ mới so với kịch bản A, đều là thứ không thể thiếu khi đọc cả trang:

**Thứ tự đọc.** OCR trả về các ô văn bản không theo thứ tự nào. Module gom
dòng theo tâm chữ (chữ hoa và chữ thường có mép trên khác nhau nhưng cùng
dòng), rồi nhận biết bố cục nhiều cột — đọc ngang qua hai cột thì câu chữ
trộn vào nhau và vô nghĩa hoàn toàn.

**Chia đoạn.** Đọc liền một trang A4 mất vài phút và người nghe không quay
lại được. Chia thành đoạn, ưu tiên cắt ở chỗ kết thúc câu.

**Cơ chế ổn định.** Không đọc ngay khi vừa thấy chữ — nếu đọc ngay, hệ thống
sẽ đọc lại liên tục mỗi khi người dùng nhúc nhích camera. Phải ổn định vài
khung hình rồi mới đọc, và không đọc lại nội dung đã đọc.

Vẫn giữ đúng triết lý an toàn: nếu chữ đọc được quá mờ, hệ thống nói thẳng
"chữ đọc được không rõ, hãy lại gần hơn" thay vì đọc bừa. Đọc sai chính tả
cho người khiếm thị bằng giọng chắc nịch cũng là một dạng tự tin nói sai —
họ không có cách nào kiểm chứng.

---

## Kịch bản D — dùng thiết bị màn hình cảm ứng

Máy in, máy pha cà phê, lò vi sóng ở văn phòng giờ đều là màn cảm ứng phẳng:
không nút bấm, không phản hồi xúc giác, không đọc được bằng màn hình đọc.

```bash
python3 run_panel.py --demo --marker 40   # không cần camera
python3 run_panel.py --speak              # webcam
```

**Ý tưởng cốt lõi: chính tấm mã là mốc sờ được.** Vị trí các nút cố định so
với mã, nên hướng dẫn thành *"đặt ngón tay lên mã, rồi trượt sang phải 4 phẩy
5 xentimét"*. Cách này không phụ thuộc ước lượng tư thế vốn nhiều nhiễu —
camera chỉ cần đọc ra đây là thiết bị nào, phần còn lại là số đo cố định. Và
người dùng tự kiểm chứng được bằng tay.

**Vật tư bắt buộc:** dán một miếng xốp tròn đường kính 1cm vào đúng tâm mã.
Mã in trên giấy không sờ thấy được — thiếu bước này thì cả kịch bản vô nghĩa.

Bảng điều khiển khai báo trong `config/panels.json`, đo bằng thước rồi nhập
tay. Hệ toạ độ: gốc là tâm mã, x sang phải, y lên, đơn vị mét.

---

## Kịch bản E — sơ tán khẩn cấp

Kế hoạch thoát hiểm của toà nhà hầu như không tính đến nhân viên khiếm thị:
họ không đọc được sơ đồ dán tường, và khi báo cháy thì đám đông đi ngược chiều
làm mọi mốc quen thuộc biến mất.

Dùng lại toàn bộ stack chỉ đường, chỉ khác hai điểm:

- Đích là **bất kỳ lối thoát nào gần nhất**, không phải một phòng cụ thể
- **Thang máy bị loại**: khi báo cháy thang máy bị khoá tự động, đi tới đó rồi
  kẹt lại là tình huống nguy hiểm thật sự

```python
from wayfinding.routing import build_evacuation_route
route = build_evacuation_route(fm, "R12")        # tự chọn lối gần nhất
```

Bản đồ khai báo thêm `exits` và cờ `is_lift` trên cạnh.

---

## Kiểm tra bản đồ trước khi demo

Chạy vào sáng ngày dán mã. Bản đồ sai làm hệ thống *tự tin chỉ sai đường* —
loại nguy hiểm nhất. `load_map()` đã bắt các lỗi làm sập chương trình, nhưng
còn một loạt vấn đề chỉ làm chỉ dẫn sai chứ không sập.

```bash
python3 tools/validate_map.py config/map_floor3.json
python3 tools/validate_map.py config/map_floor3.json --strict
```

Bắt được, trong đó có mấy thứ khó tự phát hiện:

- Nút quá xa mọi mốc neo → độ tin cậy tụt xuống mức thấp **trước khi** tới nơi,
  hệ thống sẽ từ chối chỉ đường đúng lúc cần nhất
- Nút tên có "thang"/"bậc" nhưng không cạnh nào quanh nó ghi `hazard`
- Mốc sờ được mô tả **bằng màu sắc** — người khiếm thị không dùng được
- Chỉ có đường thoát hiểm qua thang máy → báo cháy thì kẹt lại
- Số phòng trộn nhiều kiểu phân cách (3.01 và 3-02) → biểu thức chính quy chỉ
  khớp được một kiểu, một nửa số phòng không bao giờ đọc được

Trả về mã thoát khác 0 khi có lỗi, nên gắn được vào script kiểm tra trước demo.

---

## Chiều cao người dùng

Người cao 1m50 và 1m80 đeo máy ở độ cao chênh nhau gần 25cm; người ngồi xe lăn
thấp hơn nữa. Cùng một mã sẽ được nhìn ở góc hoàn toàn khác — và quá 60 độ thì
bộ phát hiện từ chối, tức là người thấp và người ngồi xe lăn bị loại khỏi hệ thống.

```bash
python3 tools/check_profile.py --heights 1.52 1.68 1.79 --wheelchair
```

**Kết quả ngược trực giác: độ cao dán mã tối ưu là ~1.21m, không phải 1.4–1.6m.**
Biển báo thông thường đặt ở tầm mắt người đứng nhìn, nhưng camera ở đây đeo
trước ngực (1.05–1.40m). Dán ở 1.45m làm góc xiên tệ nhất tăng từ 4.8° lên 11.3°.

Đây là bài toán **minimax**: chọn độ cao làm góc xiên của người bất lợi nhất là
nhỏ nhất, không tối ưu cho người trung bình. Thêm một người ngồi xe lăn thì độ
cao tối ưu của cả nhóm hạ xuống.

Hai ràng buộc tính đồng thời: mã phải nằm trong khung hình theo chiều dọc, và
góc xiên ≤ 60°. Ràng buộc thứ hai quyết định **khoảng cách gần nhất** còn đọc
được — `d_min = |Δh| / tan(60°)`.

**Rút ngắn dây giải quyết hai vấn đề cùng lúc:** vừa thoát vùng cộng hưởng, vừa
đưa camera lên gần độ cao mã. Hai yêu cầu cùng chiều nên luôn ưu tiên dây ngắn
cộng neo hai điểm.

> **Cần chỉnh trong code sau khi đo thật:** `UserProfile.strap_drop_m` (độ dài
> dây), `UserProfile.camera_height_m` (độ cao camera đo thật, ưu tiên hơn tỷ lệ),
> và `marker_height` trong bản đồ hoặc trường `h` của từng mã.

---

## Ba kiểu hỏng âm thầm

Người sáng mắt liếc màn hình là biết; người khiếm thị thì không.

**Đọc nhầm mã** → `Localizer` từ chối mốc neo kéo theo bước nhảy vị trí vô lý so
với quãng đường đã đi. Ngưỡng nới rộng theo sai số tích luỹ, và có lối thoát sau
4 lần từ chối liên tiếp để không tự khoá chính mình ở vị trí sai.

**Hết pin** → cảnh báo ở 30/15/5%, mỗi ngưỡng nói đúng một lần. Tụt nhanh từ 80%
xuống 4% chỉ đọc câu của mức 5%.

**Camera lệch trên dây** → nếu trước đó bắt mã đều rồi mất hẳn, hệ thống nói
"kiểm tra xem điện thoại có bị xoay lệch không". Nếu ngay từ đầu đã không bắt
được gì thì không báo câu này — đó là vấn đề lắp đặt, cần câu khác.

---

## Chạy thật ngoài đời

Ba thứ trước đây chặn đường chạy thật, giờ đã có công cụ.

**Dựng bản đồ từ số đo** — trước phải gõ tay JSON, sai một dấu phẩy là hệ thống
tự tin chỉ sai đường.

```bash
python3 tools/build_map.py --template > phieudo.txt
python3 tools/build_map.py --sheet phieudo.txt --out config/tang3.json
```

Phiếu đo viết bằng dòng đơn giản, dấu `|` ngăn tên và mốc sờ được, `!` là cảnh
báo nguy hiểm, `#` là chất liệu sàn. Công cụ báo số dòng khi sai, và tự kiểm
tra lại bản đồ sau khi ghi.

**Ghi lại buổi đi thử** — đi một lần, gỡ lỗi nhiều lần.

```bash
python3 run_live.py --to R12 --record runs/tuyenA.jsonl --tester Nam
python3 tools/replay.py runs/tuyenA.jsonl --gaps
```

Ghi từng dòng ngay lập tức nên mất điện giữa chừng vẫn còn dữ liệu. Chế độ
`--gaps` chỉ ra những đoạn đi lâu không gặp mốc — chính là chỗ nên dán thêm mã.

**Chế độ chỉ dùng mã** — cho lần chạy thật đầu tiên.

```bash
python3 run_live.py --to R12 --no-vio
```

Bỏ hẳn VIO, chỉ định vị khi nhìn thấy mã. Kém chính xác hơn nhưng ổn định nhất,
và quan trọng là nó **tách bạch hai nguồn lỗi**: nếu chế độ này chạy tốt mà bật
VIO lại hỏng, thì lỗi nằm ở VIO chứ không phải ở mã hay bản đồ.

**Lọc khung hình nhoè** — `--burst 3` gom ba khung rồi chỉ xử lý cái nét nhất,
`--sharp-ratio 0.45` bỏ hẳn khung nhoè.

---

## Kịch bản F — khảo sát độ tiếp cận toà nhà

Đổi góc nhìn: các kịch bản kia trang bị cho **cá nhân**, kịch bản này làm cho
**toà nhà** tiếp cận được. Nó trả lời trực tiếp câu hỏi giám khảo chắc chắn
hỏi — ai bỏ tiền, và bao nhiêu.

```bash
python3 run_audit.py
python3 run_audit.py --target 0.98 --markdown > khaosat.md
```

Cách đo độ phủ: sai số tích luỹ theo **quãng đường đi** kể từ mốc neo gần
nhất, không phải khoảng cách đường chim bay. Một phòng cách mốc 3m đường chim
bay nhưng phải đi vòng 40m thì vẫn là điểm mù. Nên công cụ chạy Dijkstra đa
nguồn từ mọi mốc neo, rải điểm dọc các lối đi, rồi đổi ra độ tin cậy bằng
đúng mô hình trong `localizer.py`.

Đề xuất dán thêm mã theo kiểu tham lam: dán vào đúng điểm tệ nhất, tính lại,
lặp lại. Không tối ưu tuyệt đối nhưng **giải thích được** với bộ phận quản lý:
dán ở đây vì đây là chỗ tệ nhất.

---

## Chống rung

Phát hiện: điện thoại treo trên dây đeo là một **con lắc đơn**. Dây 25–45cm
dao động ở 0.74–1.00 Hz, mà thân người lắc ngang khi đi bộ cũng ở 0.82–1.05 Hz.
Hai con số trùng nhau — dây đeo tự do **khuếch đại** rung chứ không giảm.

```bash
python3 tools/check_mount.py --length 0.30
```

Cách sửa, xếp theo hiệu quả trên chi phí:

1. **Neo hai điểm** (tốt nhất, ~0 đồng) — thêm dây thun vòng quanh thân kéo
   máy ép vào ngực. Con lắc cần một điểm treo duy nhất để dao động; có điểm
   neo thứ hai thì kiểu dao động đó biến mất hoàn toàn.
2. **Đệm xốp giữa máy và ngực** — ma sát tiêu tán năng lượng dao động.
3. **Rút dây xuống ≤15cm** — đưa tần số lên 1.29 Hz, tách khỏi vùng nhịp đi.

Đừng treo thêm vật nặng: chu kỳ con lắc không phụ thuộc khối lượng.

Về phần mềm, `stabilize.py` có `MotionGate` (bỏ khung hình chụp lúc đang xoay
nhanh, dựa trên con quay hồi chuyển — rẻ vì không xử lý ảnh) và `SharpnessGate`
(phương sai Laplace, ngưỡng tự điều chỉnh theo bối cảnh).

---

## Nhiều tầng

Nút có trường `floor`, cạnh có `is_stairs` / `is_lift`, bản đồ có `ground_floor`.
Sơ tán ưu tiên lối thoát ở tầng trệt, và loại thang máy vì báo cháy thì thang
máy khoá tự động.

Chỉ dẫn đổi tầng được ưu tiên **trên cả cảnh báo nguy hiểm**: chặng cầu thang
thường có cả hai, và nếu cảnh báo chạy trước thì người dùng nghe "có cầu thang"
nhưng không bao giờ nghe "xuống ba tầng" — biết có nguy hiểm mà không biết
phải làm gì.

---

## Giai đoạn 4 — đo nghiệm thu

**Hiệu chỉnh tỷ lệ trôi** (làm trước, vì nó điều khiển mô hình độ tin cậy):

```bash
python3 tools/measure_drift.py --errors 1.2 0.9 1.6 --distance 50
```

Bài đo đi-và-về: đứng trên vạch, đi 25m, quay đầu, về đúng vạch cũ, xem hệ
thống lệch bao nhiêu. Làm ít nhất 3 lần, ở cả hành lang có đồ lẫn hành lang
trắng trơn. Công cụ khuyến nghị dùng **con số xấu nhất**, vì đây là cơ chế an
toàn — phải giả định trường hợp xấu.

**Sinh bảng nghiệm thu** cho slide:

```bash
python3 tools/eval_report.py runs.json
python3 tools/eval_report.py runs.json --markdown > ketqua.md
```

Sáu chỉ số ở Mục 17, ngưỡng chốt sẵn trong `metrics.TARGETS`. Chỉ số **chưa
đo** báo "chưa đo", không bao giờ báo đạt — để khi pitch không vô tình nói dối.

---

## Kiến trúc

```
wayfinding/
  geometry.py   phép biến đổi SE(2), rút về 2D vì chỉ làm một tầng
  floormap.py   đọc và KIỂM TRA file bản đồ
  anchors.py    ba lớp mốc neo, gộp về một kiểu dữ liệu
  signtext.py   chuẩn hoá và so khớp chữ trên biển (bỏ dấu, chịu lỗi OCR)
  vio.py        đo chuyển động, tách backend
  localizer.py  ghép VIO với mốc neo + mô hình độ tin cậy
  routing.py    đồ thị và Dijkstra
  guidance.py   sinh câu chỉ dẫn + xử lý đi lạc
  speech.py     giọng nói và rung
  arcore.py     đổi tư thế ARCore sang gói tin (bản tham chiếu cho Kotlin)
  bridge.py     cầu nối WiFi với điện thoại (GĐ 3)
  reader.py     đọc biển/tài liệu (kịch bản C)
  panel.py      thiết bị màn hình cảm ứng (kịch bản D)
  desk.py       tìm chỗ ngồi hot-desk (kịch bản B)
  audit.py      khảo sát độ tiếp cận toà nhà (kịch bản F)
  stabilize.py  chống rung: vật lý cách đeo + lọc khung hình
  session.py    ghi lại buổi đi thử để phát lại
  profile.py    hồ sơ chiều cao người dùng + hình học cách đeo
  health.py     theo dõi pin và phát hiện camera lệch
  metrics.py    sáu chỉ số nghiệm thu (GĐ 4)

tools/
  calibrate.py        hiệu chỉnh camera
  phone_sim.py        giả lập điện thoại (toạ độ 2D)
  android_sim.py      giả lập điện thoại (tư thế ARCore 6 bậc)
  measure_drift.py    đo tỷ lệ trôi thật
  eval_report.py      sinh bảng nghiệm thu
  validate_map.py     kiểm tra bản đồ trước khi demo
  check_device.py     tính năng lực thiết bị (độ phân giải, rung, chiều cao)
  check_mount.py      kiểm tra cách đeo, cảnh báo cộng hưởng
  build_map.py        dựng bản đồ từ phiếu đo thực địa
  replay.py           xem lại buổi đi thử đã ghi
  check_profile.py    kê đơn dây đeo và độ cao dán mã theo chiều cao đội
```

**Nguyên lý một câu:** mốc neo cho biết mình ở đâu và quay mặt hướng nào một
cách tuyệt đối; VIO cho biết đã đi được bao xa kể từ mốc gần nhất.

**Ba lớp mốc neo** trả về cùng kiểu `AnchorSighting`, nên `Localizer` xử lý
cả ba y hệt nhau:

| Lớp | `source` | Nguồn | Đặt ở đâu | Chi phí |
|---|---|---|---|---|
| Số phòng | `ocr` | Biển số phòng **sẵn có** | Cửa phòng | 0đ |
| Biển chữ | `sign` | Biển thoát hiểm, số tầng **sẵn có** | Ngã rẽ, cầu thang | 0đ |
| ArUco | `aruco` | Mã in dán thêm | *đang loại bỏ dần* | ~50k/tầng |

Lớp **biển chữ** sinh ra vì mentor không cho dán mã giấy lên tường RMIT, mà
ngã rẽ và cầu thang thì không có số phòng để đọc — đúng những chỗ chỉ sai là
nguy hiểm nhất. Theo quy định phòng cháy, những chỗ đó **luôn có biển thoát
hiểm**, và đó là biển toà nhà đã có sẵn.

### Biển chữ và bài toán trùng chữ

Số phòng là duy nhất trong một tầng, đọc được là biết đang ở đâu. Biển chữ thì
không: **mọi biển thoát hiểm đều ghi giống hệt nhau**. Đọc được "LỐI THOÁT"
chỉ thu hẹp xuống một *nhóm* ứng viên.

Việc gỡ nhập nhằng nằm ở `Localizer._resolve_sign()`:

| Tình huống | Xử lý |
|---|---|
| Chỉ một tấm khớp chữ | Dùng ngay |
| Nhiều tấm, **chưa định vị được** | **Từ chối** — không có căn cứ để chọn |
| Nhiều tấm, tấm gần nhất gần hơn hẳn (> 3m) | Chọn tấm gần nhất |
| Nhiều tấm, hai tấm gần bằng nhau | **Từ chối** — đoán bừa là 50% sai |
| Tấm gần nhất vẫn cách quá xa (> 8m) | **Từ chối** |

Nguyên tắc giữ nguyên như toàn hệ thống: với người khiếm thị, neo nhầm sang
đầu kia toà nhà nguy hiểm hơn nhiều so với bỏ qua một lần neo đúng.

Khai báo trong bản đồ — `text` phải là chữ **in thật** trên biển, dấu má thế
nào cũng được vì `signtext.normalize()` tự bỏ dấu:

```json
"signs": {
  "exit-nga-re-dong": { "x": 18.5, "y": -0.9, "theta": 90,
                        "text": "LOI THOAT",
                        "at": "Tuong nga re hanh lang dong" }
}
```

`signtext.matches()` chịu được OCR rụng dấu, nhầm `O` với `0`, thừa thiếu vài
ký tự, và dính thêm chữ bên cạnh. Nhưng chuỗi ngắn dưới 5 ký tự thì phải khớp
tuyệt đối — `"A3"` và `"A4"` chỉ cách nhau một ký tự.

**VIO tách backend** — đổi backend không phải sửa `Localizer`:

- `SimulatedVIO` — test logic ngay, không cần camera
- `MonocularVIO` — webcam, trôi nhanh, chỉ để chứng minh nguyên lý
- `ArCoreVIO` — chỗ cắm sẵn cho điện thoại

---

## Quy tắc an toàn

Nằm trong `localizer.can_announce()`, có test riêng trong `tests/test_core.py`:

1. Cảnh báo nguy hiểm **chỉ** phát khi độ tin cậy cao
2. Lệnh rẽ cần độ tin cậy từ trung bình trở lên
3. Chưa định vị được thì **không** đưa bất kỳ chỉ dẫn đường nào
4. Đi quá 30m chưa gặp mốc thì chủ động báo độ tin cậy đang giảm

Khi độ tin cậy không đủ, hệ thống **nói thật** thay vì im lặng:
"Sắp tới ngã rẽ, nhưng độ chính xác đang giảm. Hãy dùng gậy để xác nhận."

Thang độ tin cậy dựa trên `drift = 2.5% × quãng đường từ mốc cuối`.
**Con số 2.5% là giả định — phải đo thực tế để hiệu chỉnh.** Cách đo: đi 50m
rồi quay lại điểm đầu, xem lệch bao nhiêu.

---

## Hạn chế phải nói thật khi pitch

**MonocularVIO không thay được ARCore.** Camera đơn không biết tỷ lệ thực và
trôi nhanh hơn ARCore nhiều vì không có cảm biến quán tính. Nó kém hẳn ở hành
lang tường trắng trơn — đúng vấn đề đã nêu trong phân tích. Đủ để chứng minh
nguyên lý trên laptop, **không đủ để dùng thật**.

**Ước lượng khoảng cách của lớp OCR rất thô**, vì không biết kích thước biển
thật. Chấp nhận được vì OCR chỉ đọc được ở 1–2m và sai số bị xoá ngay ở lần
neo kế tiếp.

**Chưa chạy thử với camera thật.** Bộ test dùng ảnh tổng hợp. Thí nghiệm ở
Mục 3.2 và 3.3 của tài liệu vẫn phải làm.

**Nhập nhằng tư thế mặt phẳng đã xử lý nhưng nên kiểm chứng lại ngoài đời.**
Xem mục dưới.

---

## Ghi chú kỹ thuật: nhập nhằng hai nghiệm

Bài toán tư thế của một mục tiêu **phẳng** luôn có hai nghiệm đối xứng qua mặt
phẳng ảnh. Khi nhìn gần trực diện, hai nghiệm gần trùng nhau và **dấu của pháp
tuyến trở nên bất định** — solver có thể trả về pháp tuyến hướng ra xa camera.

Nếu không xử lý, hệ thống sẽ tưởng mã quay mặt ngược lại, tính sai hướng, rồi
tự tin chỉ ngược đường. Đúng loại lỗi mà toàn bộ thiết kế đang phòng.

Cách xử lý trong `_solve_marker_pose`: dựa trên ràng buộc vật lý rằng **mã in
dán tường thì không bao giờ nhìn thấy được mặt sau**, nên nếu pháp tuyên hướng
ra xa thì **lật lại** chứ không loại bỏ lần phát hiện. Loại bỏ sẽ làm mất mốc
neo ở đúng trường hợp phổ biến nhất — người dùng đi thẳng vào mặt mã.

Khoảng cách luôn ổn định bất kể nhập nhằng hướng, nên phần ước lượng khoảng
cách không bị ảnh hưởng.

---

## Việc tiếp theo

1. Chạy thí nghiệm Mục 3.2 và 3.3 — **làm trước mọi thứ khác**
2. Đo tỷ lệ trôi thật của VIO, sửa `DEFAULT_DRIFT_RATE` trong `localizer.py`
3. Đo bản đồ thật của tầng demo
4. Chạy `run_live.py` với webcam, sửa những gì hỏng
5. Chạy `run_bridge.py` + `phone_sim.py` để thấy Giai đoạn 3 hoạt động
6. Viết phía Android theo giao thức ở trên — mốc quyết định cứng 14/9
7. Đo đủ sáu chỉ số, sinh bảng bằng `eval_report.py` cho slide
