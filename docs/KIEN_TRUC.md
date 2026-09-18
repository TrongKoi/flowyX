# Kiến trúc Flowy

Gộp từ hai tài liệu cũ (`PIPELINE.md` — luồng dữ liệu, và `BANDO_MA_NGUON.md`
— nhiệm vụ từng file), vì cả hai đều trả lời cùng một câu hỏi: *hệ thống
gồm những gì và chúng nối với nhau ra sao*.

---

## 1. Hai chế độ, một lõi

BoussoleX phục vụ **hai nhóm người dùng có nhu cầu gần như ngược nhau**:

| | Người ADHD / neurodivergent | Người khiếm thị |
|---|---|---|
| Nhìn thấy đường? | Có | Không |
| Kênh chính | Hình ảnh (timer, lộ trình) | Giọng nói |
| Cầm máy thế nào | Cầm tay, dùng lúc cần | Đeo cố định trên ngực |
| Vấn đề cần giải | Mù thời gian, mất mạch, quên mục đích | Không biết mình ở đâu, có gì chắn đường |

Vì nhu cầu khác nhau như vậy, mã nguồn chia **ba nhánh**, và chiều phụ
thuộc chỉ đi một chiều:

```
        adhd/  ─────┐
                    ├──▶  loi_chung/
    khiemthi/  ─────┘

    KHÔNG có chiều ngược lại.
```

`loi_chung/` không bao giờ được `import` từ `adhd/` hay `khiemthi/`. Vi
phạm điều này sẽ làm hai chế độ dính vào nhau, và sửa một bên sẽ vô tình
làm hỏng bên kia.

---

## 2. `wayfinding/loi_chung/` — dùng cho cả hai chế độ

Đây là phần **phải port** sang Kotlin/Swift khi chạy độc lập trên điện
thoại. Các module này chỉ nhận số và trả số — không import ARCore, ARKit
hay OpenCV — nhờ vậy cùng một logic chạy được trên cả ba ngôn ngữ và kiểm
thử được không cần thiết bị.

| File | Nhiệm vụ |
|---|---|
| `geometry.py` | Hình học SE(2): phép biến đổi 2D. Nền móng của mọi tính toán vị trí |
| `localizer.py` | **Lõi an toàn.** Ghép VIO với mốc neo, kiểm tính hợp lý, quyết định độ tin cậy. Mọi nguồn vị trí đều đi qua đây |
| `routing.py` | Tìm đường trên đồ thị tầng (Dijkstra), có hỗ trợ trọng số cạnh tuỳ chỉnh |
| `guidance.py` | Sinh câu chỉ dẫn theo hệ quy chiếu gắn thân người ("rẽ phải"), xử lý đi lạc |
| `floormap.py` | Đọc và kiểm tra file bản đồ tầng |
| `bridge.py` | Cầu nối điện thoại ↔ laptop qua WiFi. Định nghĩa `PhoneUpdate`, `BridgeReply` |
| `announce.py` | Chọn câu nào được nói khi nhiều kênh cùng muốn nói. Mỗi kênh có bộ đệm chống lặp **riêng** |
| `depth.py` | Phân loại ô lưới độ sâu: `TRONG` / `CO_VAT` / `CHUA_BIET` |
| `objects.py` | Ghép nhãn vật thể với độ sâu, quyết định nói gì |
| `anchors.py` | Đọc biển báo và số phòng bằng OCR, tính khoảng cách theo mô hình lỗ kim |
| `signtext.py` | Chuẩn hoá và so khớp chữ trên biển báo (bỏ dấu rồi so khớp mờ) |
| `floors.py` | Biết đang ở tầng mấy bằng khí áp kế |
| `power.py` | Điều tiết nhịp xử lý — giảm độ trễ **và** giảm hao pin |
| `profile.py` | Hồ sơ người dùng và hình học cách đeo máy |
| `speech.py` | Đầu ra giọng nói và mã rung |
| `session.py` | Ghi lại buổi đi thử để **phát lại** — công cụ quan trọng nhất khi gỡ lỗi tại chỗ |
| `health.py` | Theo dõi sức khoẻ hệ thống lúc chạy: pin, tỷ lệ nhận diện sụt |
| `metrics.py` | Ghi và tính chỉ số nghiệm thu. Chỉ số chưa đo báo "chưa đo", không bao giờ báo đạt |

**Vì sao `depth`, `objects`, `anchors` nằm ở lõi chung dù thiên về khiếm
thị:** `bridge.py` là giao thức chung cho cả hai chế độ và cần cấu trúc dữ
liệu `DepthGrid`, `VatNhinThay`; `localizer.py` cần `AnchorSighting`. Để
chúng ở nhánh khiếm thị sẽ sinh phụ thuộc ngược.

---

## 3. `wayfinding/adhd/` — riêng cho người ADHD

| File | Nhiệm vụ |
|---|---|
| `timeblind.py` | **Chống mù thời gian.** Neo lộ trình vào giờ hẹn thật, tính buffer an toàn, báo trước mốc khởi hành. Chứa cả `uoc_phut()` — bộ ước lượng thời gian đi |
| `mach.py` | Khôi phục mạch sau khi bị phân tâm: dựng lại "đang đi đâu, để làm gì, bước tiếp theo" |
| `dongvien.py` | Bạn đồng hành — phản hồi tích cực, **không bao giờ thể hiện thất vọng** |
| `meety.py` | Gọi Meety tóm tắt biên bản cuộc họp, xuất ra tệp `.md`/`.docx` |
| `places.py` | Đánh dấu địa điểm cá nhân ("bàn của tôi"), có chống nhầm chỗ cũ thành chỗ mới |

---

## 4. `wayfinding/khiemthi/` — riêng cho người khiếm thị

| File | Nhiệm vụ |
|---|---|
| `braille.py` | Xác nhận vị trí bằng biển chữ nổi — người dùng sờ và đọc, hệ thống nghe |
| `backdrop.py` | Bản nền độ sâu: phân biệt vật cố định với vật tạm thời, và dùng làm nguồn vị trí |
| `corridor.py` | Điểm tụ hành lang (sửa hướng) và luồng quang (bắt lỗi VIO) |
| `shapes.py` | Phát hiện vật cản bằng hình học |
| `stabilize.py` | Chống rung: lọc khung mờ, chọn khung nét nhất |
| `vio.py` | Lớp đo chuyển động, tách giao diện để thay backend |
| `arcore.py` | Chuyển tư thế ARCore 6 bậc tự do sang gói tin cầu nối |
| `reader.py` | Kịch bản C — đọc biển, tài liệu, bảng trắng |
| `desk.py` | Kịch bản B — tìm chỗ ngồi hot-desk |
| `panel.py` | Kịch bản D — dùng thiết bị màn hình cảm ứng |
| `audit.py` | Kịch bản F — khảo sát độ tiếp cận cho quản lý toà nhà |

---

## 5. Luồng dữ liệu khi đang chạy

```
  ĐIỆN THOẠI                          LAPTOP (bộ não)
  ──────────                          ───────────────
  ARCore → pose         ─┐
  Depth API → lưới      ─┤
  ML Kit → vật thể      ─┼─ POST /update ─▶  bridge.parse_update()
  Khí áp kế → áp suất   ─┤    ~8 lần/giây          │
  Micro → câu nói       ─┘                         ▼
                                        localizer  (tôi ở đâu)
                                              │
                          ┌───────────────────┼───────────────────┐
                          ▼                   ▼                   ▼
                    khiemthi/            loi_chung/            adhd/
                    depth, backdrop      routing, guidance     timeblind
                    braille, corridor    floors                mach, preview
                          │                   │                   │
                          └───────────────────┼───────────────────┘
                                              ▼
                                       announce  (nói câu nào)
                                              │
                        ◀── BridgeReply ───────┘
  Speaker → giọng nói
  Rung
```

---

## 6. Chương trình chạy — `adc_wayfinding/`

| File | Nhiệm vụ |
|---|---|
| `run_bridge.py` | **Đường chạy demo thật.** Điện thoại làm cảm biến, laptop làm bộ não |
| `run_scan.py` | Quét dựng bản nền độ sâu cho một tầng (làm một lần mỗi tầng) |
| `run_sim.py` | Chạy thử toàn bộ bằng mô phỏng, không cần camera lẫn điện thoại |
| `run_live.py` | Chạy với webcam laptop |
| `run_audit.py`, `run_reader.py`, `run_panel.py` | Kịch bản phụ F, C, D |

## 7. Công cụ — `adc_wayfinding/tools/`

| File | Nhiệm vụ |
|---|---|
| `phone_sim.py` | Giả lập điện thoại khi chưa có máy thật |
| `android_sim.py` | Giả lập sâu hơn: sinh tư thế ARCore 6 bậc tự do |
| `build_map.py` | Dựng bản đồ tầng từ số đo thực địa |
| `validate_map.py` | **Kiểm tra bản đồ trước khi demo.** Chạy vào sáng ngày thi |
| `check_device.py` | Đo năng lực thiết bị: có ARCore không, có Depth API không |
| `check_mount.py`, `check_profile.py` | Kiểm tra cách đeo máy theo chiều cao |
| `measure_drift.py` | Đo tỷ lệ trôi thật của VIO |
| `calibrate.py` | Hiệu chỉnh camera — **tuỳ chọn**, hệ thống chạy ngay không cần |
| `replay.py` | Phát lại một buổi đi thử đã ghi |
| `eval_report.py` | Sinh bảng nghiệm thu từ các lần chạy đã ghi |

---

## 8. Kiểm thử — chia đúng theo ba nhánh

```
tests/
  loi_chung/    định vị, tìm đường, cầu nối, pin, tầng, thông báo
  adhd/         chống mù thời gian, mạch, đồng hành, Meety
  khiemthi/     độ sâu, bản nền, chữ nổi, điểm tụ, hình dạng, OCR
```

Chạy: `cd adc_wayfinding && python3 -m pytest tests/ -q`

Phải đứng đúng trong `adc_wayfinding/` — một test dùng đường dẫn tương đối.

---

## 9. `meety/` — dự án con, chép hẳn vào repo

Hệ tóm tắt biên bản cuộc họp, gọi qua tiến trình con từ
`wayfinding/adhd/meety.py`.

Đã **cắt bỏ** `frontend/`, `server/`, `run_server.py` của Meety: chúng
dùng để hiện biên bản trên web, mà BoussoleX **không hiện UI biên bản** —
Meety xuất thẳng ra tệp `.md`/`.docx` cho người dùng đọc.

Chạy thử độc lập:

```bash
cd meety
python3 main.py --input sample_transcript.json --skip-stt \
                --date 2026-07-22 --mock --format json,md --output /tmp/ra
```

---

## 10. `frontend/` — giao diện Android, module Gradle riêng

Tách khỏi `android/app` để phần hiển thị không lẫn với phần cảm biến. Xem
`docs/UIUX_QUYET_DINH.md` để biết vì sao chọn View thuần thay vì Compose,
và cách chuyển giữa hai chế độ.

---

## 11. `thu_nghiem/` — code đã cất

**Không nằm trong đường chạy của app.** Không có gì trong
`adc_wayfinding/` import từ đây, và `pytest` không quét thư mục này.

| Thư mục | Nội dung | Vì sao cất |
|---|---|---|
| `xem_truoc_lo_trinh/` | Đọc lộ trình chia theo khối | Là cách trình bày tốt hơn, không phải năng lực mới — chưa đủ mạnh cho bản thi |

Mỗi thư mục có `README.md` riêng ghi cách lấy lại.

---

## 12. Hằng số còn để tạm — cần đo thực địa

| Hằng số | File | Cần gì để đặt đúng |
|---|---|---|
| `BAN_KINH_HOP_LY_M` | `khiemthi/braille.py` | Đo độ trôi VIO thật trên quãng 50 m |
| `text_h` từng biển | `config/map_floor3.json` | Đo chiều cao chữ thật tại RMIT |
| Bản đồ tầng | `config/map_floor3.json` | Đang là bản mẫu, **chưa đo thật** |
