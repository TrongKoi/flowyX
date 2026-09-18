# Thiết kế — nguồn gốc

Thư mục này giữ **bản gốc** do nhóm xuất ra, và các bản tôi chế biến từ
đó. Mọi thứ trong `android/app/src/main/res/` đều sinh ra từ đây.

## Tệp gốc (nhóm gửi, đừng sửa)

| Tệp | Là gì |
|---|---|
| `FlowyX_LogoBrand/1.png` | Bảng nhận diện — bảng màu, phông, elements |
| `FlowyX_LogoBrand/2.png` | Logo ngang, **nền trắng đặc** |

## Tệp đã chế biến

| Tệp | Làm thế nào |
|---|---|
| `flowyx_ngang.png` | Tách nền trắng khỏi `2.png`, cắt sát nội dung |
| `flowyx_dau.png` | Cụm bốn giọt, cắt ra từ bản trên, đưa về khung vuông |

### Vì sao phải tách nền

`2.png` **không có kênh trong suốt** — nền trắng nằm hẳn trong ảnh. Đặt
thẳng nó lên nền kem của app sẽ thành một ô trắng quanh logo.

Cách tách: mỗi điểm ảnh là một pha trộn giữa màu logo `C` và trắng.

```
O = A·C + (1−A)·255
```

Độ "xa trắng" `d = 255 − min(R,G,B)`. Màu đậm nhất của logo là navy
`#2D2A42`, có `d = 213` — nên chia cho 213 thì navy ra alpha đầy. Sau đó
gỡ phần trắng còn lẫn trong màu (khử tiền nhân), không gỡ thì viền logo
bị bạc màu.

## Bảng màu — đo, không đoán

Bốn mã màu lấy bằng cách **đo điểm ảnh ở giữa từng ô** trong `1.png`:

| | Mã |
|---|---|
| vàng | `#FFD400` |
| navy | `#2D2A42` |
| kem | `#FEF4EF` |
| cam | `#F58A07` |

Bản trước tôi đọc bằng mắt và **lệch ở ba trong bốn màu**. Nếu cần lấy
lại, quét một hàng ngang qua bốn ô và lấy màu ở giữa từng đoạn.

## Sinh lại tài nguyên cho app

Bốn thứ sinh ra từ `flowyx_ngang.png` và `flowyx_dau.png`:

| Tài nguyên | Kích thước |
|---|---|
| `drawable-*/logo_ngang.png` | cao 22dp, năm mật độ |
| `mipmap-*/ic_launcher.png` | 48dp, nền kem sẵn — cho API 24–25 |
| `mipmap-*/ic_launcher_foreground.png` | 108dp, logo trong vùng an toàn 72dp |
| `mipmap-anydpi-v26/ic_launcher.xml` | biểu tượng thích ứng |

Cần bản **API 24–25** vì `minSdk = 24`, mà biểu tượng thích ứng chỉ có
từ API 26.

## Còn thiếu

Chưa có bản **SVG**. Có SVG thì logo đổi được thành VectorDrawable — sắc
ở mọi kích thước và nhẹ hơn năm tệp PNG. Canva xuất SVG là tính năng trả
phí; khi nào có thì bỏ vào đây.
