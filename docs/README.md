# Tài liệu Flowy

Sáu tài liệu, chia theo **bạn đang cần gì**.

---

## Muốn chạy thử ngay

**`HUONGDAN_SUDUNG.md`** — cài đặt, chạy, hai chế độ sử dụng, xử lý sự cố,
hợp đồng JSON giữa điện thoại và laptop.

Không cần đọc gì khác trước file này.

## Muốn sửa code

1. **`KIEN_TRUC.md`** — hệ thống gồm gì, file nào làm việc gì, dữ liệu chảy
   đi đâu. Đọc trước tiên để biết nên mở file nào.
2. **`SPEC.md`** — đặc tả để viết code: từng node, công thức, ngưỡng, tiêu
   chí nghiệm thu. Dài nhưng là nguồn chân lý.

## Muốn sửa giao diện

**`GIAO_DIEN_V2.md`** — giao diện hiện tại (16/09): bảng màu sáng/tối, chữ,
bố cục điện thoại và máy tính bảng, lịch kiểu khối màu. **Đọc file này trước.**

**`UIUX_QUYET_DINH.md`** — các phương án đã cân nhắc và lý do chọn: cách
hỏi người dùng chọn chế độ, logic chuyển giữa hai chế độ, quy tắc màu và
vị trí thông tin, và vì sao **không dùng Jetpack Compose**.

Đọc file này trước khi đổi bất cứ thứ gì trên màn hình — nhiều quyết định
trông tuỳ tiện nhưng có lý do đằng sau.

## Muốn báo lỗi hoặc xem lỗi đã sửa

Không nằm trong `docs/` — xem **[`../BAO_LOI/`](../BAO_LOI/README.md)** ở gốc repo.

## Muốn biết đã thay đổi những gì

**`THAYDOI_2026-09-12.md`** — nhật ký thay đổi. Dài, đọc từ dưới lên nếu
chỉ cần phần mới nhất.

Phần đáng đọc nhất là các mục **"Lỗi phát hiện khi viết test"** — ghi lại
những lỗi ẩn đã tìm ra, để không ai vô tình khôi phục lại chúng.

---

## Thư mục ngoài `docs/`

**`thu_nghiem/`** (ở gốc repo) — code đã cất, không nằm trong đường chạy
của app. Mỗi thư mục con có `README.md` riêng ghi cách lấy lại.

---

## Thư mục `luu-tru/`

Tài liệu **không còn đúng với mã nguồn hiện tại**. Giữ làm lịch sử,
**không dùng làm chỉ dẫn**.

| File | Vì sao lưu trữ |
|---|---|
| `BANGIAO.md` | Ghi "code ArUco vẫn còn trong repo" — sai, ArUco đã gỡ hoàn toàn |
| `04-BA-HAN-CHE.md` | Là đề xuất chờ duyệt; các quyết định trong đó đã hiện thực xong |
| `NHAN_VAT_BRIEF.md` | Nhân vật đồng hành đã bỏ (16/09). Nguyên tắc §2.4 "app không chủ động bắt chuyện" vẫn áp dụng |

---

## Đã xoá trong đợt dọn

| File | Lý do |
|---|---|
| `ENGINEERING_COMPARISON.md` | So sánh kỹ thuật với sản phẩm khác — không còn cần khi trọng tâm chuyển sang ADHD |
| `MO_HINH_RIENG.md` | Bàn về tự huấn luyện mô hình nhận diện; kết luận là không cần, nên tài liệu cũng không cần |
| `PIPELINE.md`, `BANDO_MA_NGUON.md` | Đã **gộp** thành `KIEN_TRUC.md` — cả hai đều mô tả "hệ thống gồm gì" |

---

## Trạng thái dự án

**442 bài kiểm thử** cho lõi Python:

```bash
cd adc_wayfinding
python3 -m pytest tests/ -q              # tất cả
python3 -m pytest tests/adhd/ -q         # riêng phần ADHD
python3 -m pytest tests/loi_chung/ -q    # riêng lõi chung
```

Phải đứng đúng trong `adc_wayfinding/` — một test dùng đường dẫn tương đối.
