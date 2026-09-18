# Xem trước lộ trình — CẤT ĐI, không dùng trong app

Thư mục `thu_nghiem/` **không nằm trong đường chạy của ứng dụng**. Không
có gì trong `adc_wayfinding/` import từ đây, và `pytest` không chạy các
test ở đây.

---

## Đây là gì

Cơ chế đọc lộ trình **chia theo khối**: đọc một câu tóm tắt trước, rồi
từng chặng một khi người dùng hỏi tiếp, luôn kèm "còn bao nhiêu chặng".

```
"Lộ trình: 2 lần rẽ, 1 lần đổi tầng, khoảng 4 phút.
 Bạn muốn nghe chi tiết không?"
    → "chi tiết"
"Đi thẳng khoảng 8 mét tới Chân cầu thang bộ. Còn 3 chặng."
    → "tiếp"
"Đi lên 3 tầng bằng thang máy. Còn 2 chặng."
```

## Vì sao cất đi

Không phải vì nó sai. Cơ sở thiết kế vẫn đúng: trí nhớ làm việc giữ được
khoảng bốn đơn vị thông tin, nên đọc một lộ trình sáu chặng liền mạch sẽ
vượt giới hạn và người nghe mất phần giữa.

Cất vì **nó chưa đủ mạnh để làm một tính năng trong bản thi**. Nó là một
cách trình bày tốt hơn, không phải một năng lực mới — và trong một cuộc
thi mà giám khảo chỉ nhìn được vài phút, cải thiện cách trình bày khó
tạo ấn tượng bằng việc giải một vấn đề chưa ai giải.

Trụ cột của chế độ ADHD giờ là `wayfinding/adhd/timeblind.py` — neo lộ
trình vào **giờ hẹn thật** thay vì một khoảng thời gian trôi nổi.

---

## Thứ đã KHÔNG cất đi cùng

`uoc_phut()` (ước thời gian đi) và ba hằng số tốc độ trước đây nằm trong
file này, nhưng **đã chuyển sang `wayfinding/adhd/timeblind.py`**.

Lý do: nó không thuộc ý tưởng "đọc theo khối". Nó là bộ ước lượng thời
gian, và là **đầu vào bắt buộc** của lớp chống mù thời gian. Cất nhầm nó
đi sẽ làm sập trụ cột chính của chế độ ADHD.

Nếu sau này khôi phục `preview.py`, **đừng chép lại `uoc_phut()` vào
đây** — import từ `timeblind` để tránh có hai bản trôi lệch nhau.

---

## Cách lấy lại sau này

```bash
# 1. Chuyển file về chỗ cũ
mv thu_nghiem/xem_truoc_lo_trinh/preview.py      adc_wayfinding/wayfinding/adhd/
mv thu_nghiem/xem_truoc_lo_trinh/test_preview.py adc_wayfinding/tests/adhd/
```

2. Trong `preview.py`, xoá phần `uoc_phut()`/`_la_lan_re()`/hằng số tốc độ
   nếu còn sót, thay bằng:

```python
from .timeblind import uoc_phut
```

3. Trong `run_bridge.py`, nối lại ba chỗ:

```python
from wayfinding.adhd.preview import PhienXemTruoc          # đầu file

xem_truoc = [PhienXemTruoc(route)]                          # trong main()

if upd.voice and xem_truoc[0] is not None:                  # trong on_update()
    tho = upd.voice.lower()
    if "tiếp" in tho or "chi tiết" in tho:
        chon_say = xem_truoc[0].tiep() or "Hết lộ trình."
    elif "lại" in tho:
        chon_say = xem_truoc[0].lap_lai()
```

> Dùng **container một phần tử** `[...]` chứ không phải biến thường.
> `on_update` gán lại giá trị này, và trong Python gán lại một tên trong
> hàm làm nó thành biến cục bộ — mọi lần đọc trước dòng gán sẽ ném
> `UnboundLocalError`, mà `BridgeServer` nuốt thành lỗi 500 im lặng,
> không có traceback trong log. Lỗi này đã xảy ra một lần rồi.

4. Chạy `pytest tests/adhd/test_preview.py -q` để xác nhận.

---

## Test kèm theo

`test_preview.py` có 20 test, vẫn xanh lúc cất đi. Chúng không chạy trong
bộ test chính vì `pytest` chỉ quét `adc_wayfinding/tests/`.

Muốn chạy thử:

```bash
cd adc_wayfinding
python3 -m pytest ../thu_nghiem/xem_truoc_lo_trinh/test_preview.py -q
```

Sẽ đỏ cho tới khi bạn làm bước 1 và 2 ở trên, vì test import
`wayfinding.adhd.preview`.
