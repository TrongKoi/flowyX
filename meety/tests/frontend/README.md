# Kiểm thử giao diện

`dom_test.js` nạp chính `mm-ai-preview.html` vào một DOM thật (jsdom) rồi bấm
nút như người dùng: đăng nhập, lọc, sắp xếp, gom nhóm, mở cửa sổ nạp, đổi tên
người nói, đi lại giữa các cuộc họp trong chuỗi, dùng phím tắt.

Kiểm tra chuỗi HTML không đủ. Bộ này bắt được những thứ chỉ lộ ra khi DOM chạy
thật — ví dụ ô tìm kiếm mất con trỏ sau mỗi ký tự nếu gõ mà gọi `render()`.

## Chạy

    npm install jsdom
    python tools/build_preview.py --out mm-ai-preview.html
    node tests/frontend/dom_test.js

Ra `✓ TẤT CẢ ĐỀU QUA` là đạt. Mã thoát khác 0 khi có lỗi, dùng được trong CI.

## Lưu ý khi viết thêm phép kiểm

`document.body.textContent` trong jsdom **gộp cả nội dung thẻ `<script>`**, tức
là toàn bộ JSON dữ liệu nhúng và mã nguồn. Đo trên đó thì mọi phép kiểm kiểu
"không lộ mã kỹ thuật ra màn hình" đều báo sai. Dùng hàm `seen()` trong file —
nó nhân bản body, bỏ `script`/`style`, rồi mới lấy chữ.
