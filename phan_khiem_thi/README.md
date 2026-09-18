# Phần khiếm thị — đã cắt khỏi đường chạy của Flowy

Thư mục này **không nằm trong hệ thống chính**. `adc_wayfinding/` không
import gì từ đây, và `pytest` chạy từ `adc_wayfinding/` không chạm tới
các test ở đây.

## Vì sao còn nằm đây

BoussoleX có hai sản phẩm, mỗi cái một repo:

| Sản phẩm | Cho ai | Repo |
|---|---|---|
| **Flowy** | Người neurodivergent (ADHD) | repo này |
| **OpticGuard** | Người khiếm thị | [opticguard](https://github.com/TrongKoi/opticguard) |

Ngày 15/09/2026 hai bên tách ra. Flowy giữ lại bản sao này thay vì xoá —
**không mất gì cả**, và vẫn tra cứu được khi cần.

> **Bản đang được bảo trì nằm ở OpticGuard.** Sửa ở đây sẽ không đi đâu
> cả. Nếu cần sửa phần khiếm thị, sửa bên đó.

## Có gì trong này

```
wayfinding/khiemthi/    audit, backdrop, braille, corridor, desk,
                        panel, reader, shapes, stabilize
tests/khiemthi/         test của các module trên
config/                 bản sao bản đồ mẫu, để test ở đây tự chạy được
check_mount.py          công cụ tính hình học cách đeo máy
run_live.py             đường webcam trên laptop
run_scan.py             quét dựng bản nền độ sâu
run_panel.py            đọc bảng điều khiển cảm ứng
run_reader.py           đọc tài liệu và biển báo bằng OCR
run_audit.py            rà soát độ phủ tiếp cận của toà nhà
run_sim.py              mô phỏng hành trình, không cần phần cứng
```

## Chạy thử

```bash
cd phan_khiem_thi
python3 -m pytest tests/ -q      # 379 xanh, 7 bỏ qua
```

`conftest.py` nối hai gốc gói `wayfinding` lại: `loi_chung` lấy từ
`adc_wayfinding/`, còn `khiemthi` lấy từ đây. Xem ghi chú trong file đó.

**7 bài bỏ qua** là các bài kiểm "`run_bridge.py` có nối lớp này không".
Flowy đã cắt lớp đó ra khỏi runner nên chúng không thể xanh ở đây —
chúng xanh ở OpticGuard. Không xoá và cũng không sửa file test, để hai
repo vẫn là cùng một mã nguồn.

## Hai module KHÔNG nằm ở đây, dù từng thuộc `khiemthi/`

`arcore.py` và `vio.py` đã chuyển sang `adc_wayfinding/wayfinding/loi_chung/`
chứ không cắt ra, vì hệ thống chính thật sự cần chúng:

| Module | Ai cần |
|---|---|
| `vio.py` | `SimulatedVIO` là công cụ chạy test cho **lõi chung** — `test_core`, `test_bridge`, và `tools/phone_sim.py` đều dùng. Cắt đi là mất cách chạy thử không cần điện thoại. |
| `arcore.py` | Bản tham chiếu của toán toạ độ mà `ArMath.kt` bên Android dịch từ đó, có test đối chiếu hai bên. Flowy vẫn còn `ArMath.kt`. |

Cả hai vốn không phải tính năng của người khiếm thị — chúng bị xếp nhầm
vào `khiemthi/` lúc chia nhánh.

## Flowy đã mất gì ở `run_bridge.py`

Bốn lớp bị gỡ khỏi runner chính, đều là thứ chỉ người khiếm thị cần:

| Lớp | Việc |
|---|---|
| L1 — biển chữ nổi | Người dùng sờ biển braille rồi đọc số phòng, hệ thống lấy làm mốc tuyệt đối |
| L4 — khớp bản nền | Dùng hình dạng độ sâu đã quét làm nguồn vị trí |
| L5 — điểm tụ hành lang | Sửa hướng, và đối chiếu luồng quang để bắt lỗi trôi VIO |
| Cảnh báo vật cản | Tách vật khỏi mặt sàn bằng hình học từ lưới độ sâu |
