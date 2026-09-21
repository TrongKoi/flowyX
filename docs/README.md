# Tài liệu Flowy

Bảy tài liệu, chia theo **bạn đang cần gì**.

---

## Muốn hiểu hệ thống

**[`KIEN_TRUC.md`](KIEN_TRUC.md)** — hệ thống gồm gì, file nào làm việc
gì, cái gì chạy trên máy và cái gì cần laptop. **Đọc trước tiên.**

## Muốn chạy thử

**[`HUONGDAN_SUDUNG.md`](HUONGDAN_SUDUNG.md)** — cài đặt, chạy, xử lý sự
cố, hợp đồng JSON giữa điện thoại và laptop.

## Muốn sửa giao diện

**[`GIAO_DIEN_V5.md`](GIAO_DIEN_V5.md)** — bản mới nhất (18/09): bảng màu
đêm viết lại, bốn tầng bề mặt, logo nghịch đảo sinh tự động, số đo tương
phản WCAG. **Đọc file này trước.**

**[`GIAO_DIEN_V4.md`](GIAO_DIEN_V4.md)** — năm tab, đồng hồ mặt 60 phút,
cử chỉ vuốt. V5 không nhắc lại những gì đã nói ở đây.

**[`UIUX_QUYET_DINH.md`](UIUX_QUYET_DINH.md)** — các phương án đã cân
nhắc và **lý do chọn**, kể cả vì sao không dùng Jetpack Compose. Đọc
trước khi đổi bất cứ thứ gì trên màn hình: nhiều quyết định trông tuỳ
tiện nhưng có lý do đằng sau.

**[`preview/flowyx-ui.html`](preview/flowyx-ui.html)** — bấm đúp để mở.
Không cần máy chủ, không cần mạng. Đồng hồ chạy thật, thanh tab trượt
thật, đổi được sáng/tối và ba phông chữ.

## Muốn hiểu vì sao Flowy làm thế này chứ không thế kia

**[`FLOWY_THIET_KE.md`](FLOWY_THIET_KE.md)** — ba khó khăn của người
ADHD, và §4 giải thích Flowy tránh trở thành thiết bị y tế bằng cách nào.

## Muốn biết dữ liệu đi đâu

**[`BAO_MAT.md`](BAO_MAT.md)** — dữ liệu nào ở lại máy, dữ liệu nào rời
máy, và mã hoá ra sao.

## Chuẩn bị cho phần thi

**[`ques/CAU_HOI_GIAM_KHAO.md`](ques/CAU_HOI_GIAM_KHAO.md)** — những câu
hội đồng có thể hỏi, kèm câu trả lời. Có cả mục **giới hạn nói trước khi
bị hỏi** và bốn câu khó chuẩn bị riêng.

Đọc một lượt để *biết mình đã có câu trả lời*, rồi trả lời bằng lời của
mình. Đừng học thuộc.

## Muốn báo lỗi

Không nằm trong `docs/` — xem **[`../BAO_LOI/`](../BAO_LOI/README.md)** ở
gốc repo, có bảng “lỗi ở phần nào thì mở file nào”.

---

## Thư mục `luu-tru/`

Tài liệu **không còn đúng với mã nguồn hiện tại**. Giữ làm lịch sử,
**không dùng làm chỉ dẫn**.

| File | Vì sao lưu trữ |
|---|---|
| `NHAN_VAT_BRIEF.md`, `NHAN_VAT_BRIEF_v2.md` | Nhân vật đồng hành đã bỏ (16/09). Nguyên tắc §2.4 “app không chủ động bắt chuyện” vẫn áp dụng |
| `THAYDOI_2026-09-12.md` | Nhật ký thay đổi tới 12/09 |
| `FLOWY_NHAT_KY_CODE.md` | Nhật ký viết code, dừng ở 16/09 |
| `BANGIAO.md` | Ghi “code ArUco vẫn còn trong repo” — sai, đã gỡ hoàn toàn |
| `04-BA-HAN-CHE.md` | Là đề xuất chờ duyệt; các quyết định trong đó đã hiện thực xong |

## Đã xoá trong đợt dọn 21/09

| File | Lý do |
|---|---|
| `SPEC.md` | 61 KB đặc tả pipeline dẫn đường cho người khiếm thị. Sản phẩm đó đã tách sang repo **opticguard** từ 15/09. Để lại đây khiến người đọc tưởng Flowy có dẫn đường trong nhà |
| `GIAO_DIEN_V2.md` | Đã bị V4 và V5 thay thế. Tệ hơn là chính `docs/README.md` còn bảo “đọc file này trước” |
| `ENGINEERING_COMPARISON.md`, `MO_HINH_RIENG.md` | Bàn về nhận diện hình ảnh — không còn liên quan |
| `PIPELINE.md`, `BANDO_MA_NGUON.md` | Đã gộp thành `KIEN_TRUC.md` |
