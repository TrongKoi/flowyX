# FlowyX — Giao diện v4: quyết định thiết kế và thông số bố cục

Cập nhật 17/09/2026, theo phản hồi thử nghiệm của nhóm. Áp cho **app Android**.
iOS chưa theo (xem §11).

| # | Phản hồi | Giải pháp | Tệp chính |
|---|---|---|---|
| 1 | Nút "Quay lại"/"Hôm nay" chói | Đổi vàng → `#57536E` (1,32:1 → 6,77:1) | `values/colors.xml`, `themes.xml` |
| 2 | Dark mode cho ADHD | Bảng "than trầm", chỉ theo máy | `values-night/` |
| 3 | Lexend toàn app | Mặc định bật | `AppSettings.kt` |
| 4 | Icon Cài đặt mới, mọi tab | Bánh răng bo tròn, cố định góc phải | `ic_cai_dat.xml`, `khoi_thanh_logo.xml` |
| 5 | Haptics | 3 mức, tắt được | `Rung.kt` |
| 6 | Chỉ báo tab | Pill + icon navy + nhãn chữ | `khoi_tab_duoi.xml`, `ThanhTab.kt` |
| 7 | Không kẹt điều hướng | Thanh con có mũi tên; ngăn xếp 2 tầng từ thông báo | `khoi_thanh_con.xml`, `NgaXep` |
| 8 | Bỏ Lời nhắc, gộp vào Kế hoạch | Tự chuyển dữ liệu một lần | `ChuyenLoiNhac.kt` |
| 9 | Tóm tắt + ưu tiên lên đầu | Tab Kế hoạch viết lại | `ViecCanLamActivity.kt` |
| 10 | Lệch căn icon/nhãn | Khuôn hàng chung, tắt font padding | `KeHoachActivity.kt` |
| 11 | Giờ bắt đầu + kết thúc tự do, lặp theo thứ, nhắc tuỳ ý | Viết lại trình tạo | `KeHoachActivity.kt`, `Lich.kt` |
| 12 | Vuốt xoá, chạm/vuốt xong | Thẻ vuốt + ô tròn; bỏ nhấn giữ | `KhungVuot.kt`, `HoanTac.kt` |
| 13 | Focus: bỏ ô bắt buộc, chỉ đếm ngược ≤2h | Timer chạy trên máy | `FocusActivity.kt`, `DemNguoc.kt` |
| 14 | Visual timer | Mặt tuyệt đối 60 phút, xoay để đặt | `frontend/…/VongTapTrungView.kt` |
| 15 | Nút `+` gỡ rối, mọi câu cùng lúc | Màn Gỡ rối | `GoRoiActivity.kt` |
| 16 | Nhật ký: căn giữa, 7 chấm | Ô cao cố định, chấm cùng một khuôn | `NhatKyActivity.kt` |
| 17 | Tự điểm danh | Mở app = ngày có hoạt động | `SoTienDo.diemDanh` |
| 18 | Trang viết toàn màn hình | Lưu nháp, không mất chữ | `VietNhatKyActivity.kt` |
| 19 | Chọn bản ghi → .docx | Chế độ chọn + 2 hồ sơ | `DocxViet.kt` |
| 20 | Lời nhắn đổi mỗi ngày | 31 câu, không trùng hôm qua | `LoiNhanNgay.kt` |
| 21 | Meety → .docx, 2 bản, giữ ghi tay | Nhập `_minutes.json` + exporter Python | `MeetyActivity.kt`, `meety/exporters/docx_de_doc.py` |

---

## 1. Màu

Quy tắc giữ nguyên từ FlowyX: **vàng và cam là mặt nền, navy là mực**. Không màu đỏ.

### 1.1. Sáng — chỉ đổi và thêm

| Token | Hex | Dùng cho | Tương phản |
|---|---|---|---|
| `chu_lien_ket` | `#57536E` | Nút chữ: Hôm nay, ‹ ›, Xong, giá trị trong hàng | 6,77:1 trên nền kem |
| `tab_pill` / `tab_chon` | `#FFF1C2` / `#2D2A42` | Tab đang chọn | 12,99:1 |
| `uu_cao` / `uu_vua` / `uu_thap` | `#F58A07` / `#FFD400` / `#C9C2D6` | Chấm/vạch ưu tiên — **luôn kèm chữ** | trang trí |
| `vuot_xoa` / `vuot_xong` | `#2D2A42` / `#FFD400` | Nền lộ ra khi vuốt | chữ 12,75 / 9,64:1 |

Vì sao `#57536E` mà không phải navy thường: navy `#2D2A42` đạt 12,75:1 — quá gắt cho
một nút phụ, giành chú ý với tiêu đề. `#57536E` vẫn gấp rưỡi chuẩn AA.

### 1.2. Tối "than trầm"

| Vai trò | Token | Hex | Đo |
|---|---|---|---|
| Nền | `nen` | `#17161F` | — |
| Thẻ tầng 1 | `the` | `#201F2A` | — |
| Thẻ tầng 2 (nổi) | `the_2` | `#2A2936` | — |
| Viền | `vien` | `#353344` | — |
| Chữ | `chu` | `#EAE4DC` | 14,2:1 nền · 12,9:1 thẻ |
| Chữ phụ | `chu_phu` | `#A29DB0` | 6,8:1 nền · 6,2:1 thẻ |
| Nút chữ | `chu_lien_ket` | `#C9C3E0` | 10,6:1 |
| Nhấn chính | `nhan` | `#E9C46A` | chữ trên nó `#1B1A22`: 10,3:1 |
| Nhấn "đang làm" | `cam` | `#F0A15A` | 7,7:1 trên thẻ |
| Timer còn nhiều | `dh_con_nhieu` | `#B9B3D6` | 8,1:1 |

Năm quyết định:
1. **Không đen tuyền.** `#000` + chữ trắng = 21:1 → nét chữ "loé" (halation), mỏi khi nhìn lâu.
   `#17161F` là navy của logo hạ sáng — vẫn thuộc bộ nhận diện.
2. **Chữ ngà, không trắng tinh.**
3. **Phân tầng bằng độ sáng, không bằng bóng đổ** — bóng gần như vô hình trên nền tối.
4. **Giảm bão hoà màu nhấn.** Vàng/cam bão hoà "rung" trên nền tối và hút mắt.
5. **Một màu nhấn mỗi lúc:** vàng = hành động chính, cam = đang làm.

**Chỉ theo máy, không có nút đổi trong app.** Bản v3 bỏ dark mode vì đổi thủ công
(`createConfigurationContext` + `recreate()`) làm app văng trên Galaxy Tab S7 FE. Theo
máy thì hệ thống tự lo vòng đời Activity — không còn chuỗi gọi đó.

---

## 2. Chữ và icon

- **Lexend mặc định bật.** Vẫn tắt được trong Cài đặt. Hạn chế đã biết: hộp thoại hệ
  thống (DatePicker, TimePicker, AlertDialog) và Toast vẫn dùng font máy.
- **Icon Cài đặt:** bánh răng 8 răng bo tròn + lỗ giữa, nét 1,8 trên khung 24 (cùng nét
  với icon tab). Thay bản cũ răng cưa nhọn — ở 24 dp trông như bông hoa.
- Icon mới cùng bộ: `ic_quay_lai`, `ic_cong`, `ic_dong_ho`, `ic_lap_lai`, `ic_chuong`,
  `ic_lich_nho`, `ic_co`, `ic_ghim`.

---

## 3. Điều hướng

### 3.1. Thanh tiêu đề

| Loại màn hình | Khối | Nội dung |
|---|---|---|
| Tab (5 tab) | `khoi_thanh_logo.xml`, cao 60 dp | logo · [nút hành động có chữ, tuỳ tab] · **icon Cài đặt 48×48** |
| Màn con | `khoi_thanh_con.xml`, cao 56 dp | **mũi tên 48×48** · tiêu đề 18sp · [nút chữ bên phải] |

Màn con: Tạo/sửa kế hoạch, Gỡ rối, Viết nhật ký, Ghi biên bản, Cài đặt. **Không màn con
nào có thanh tab** — xong một việc thì quay lại. Tab Lịch bỏ nút "Quay lại" (tab không
có gì để quay lại; nút cũ đóng Activity và đẩy người dùng ra khỏi app).

### 3.2. Thanh tab — ba tín hiệu cho tab đang chọn

```
cao 64 dp, paddingTop 6
┌──────────────────────────────────────────────┐
│  ╭────────╮                                  │
│  │  icon  │   icon    icon    icon    icon   │  pill 64×32 dp, bo 16, nền tab_pill
│  ╰────────╯                                  │  icon 24 dp: navy (chọn) / chu_phu
│  Kế hoạch                                    │  nhãn 11sp đậm, CHỈ tab đang chọn
└──────────────────────────────────────────────┘
```

Bản v3 chỉ đổi icon sang cam: 2,2:1 trên nền trắng, người mù màu đỏ-lục không phân biệt
với xám. Giờ mất màu vẫn còn hình (pill) và chữ.

Chuyển động duy nhất: pill giãn `scaleX` 0,6 → 1 trong **180 ms**, DecelerateInterpolator,
ở trang vừa hiện. Tắt "Hiệu ứng" hệ thống thì hiện ngay.

### 3.3. Haptics

| Mức | Hằng số | Khi |
|---|---|---|
| `Rung.nhe` | `KEYBOARD_PRESS` (API 27+) / `VIRTUAL_KEY` | chuyển tab, chạm chip, chạm hàng |
| `Rung.tich` | `CLOCK_TICK` | mỗi mốc 5 phút khi xoay timer |
| `Rung.xong` | `CONFIRM` (API 30+) / `LONG_PRESS` | đánh dấu xong, lưu, hết giờ, vuốt qua ngưỡng |

Dùng `View.performHapticFeedback` — theo cài đặt "Phản hồi chạm" của máy, không cần
quyền VIBRATE. Tắt hẳn khi Cài đặt → Phản hồi = "Chỉ đọc lên".

### 3.4. Mở từ thông báo

`NgaXep.mo()` dựng ngăn xếp **[Kế hoạch, màn đích]** bằng `PendingIntent.getActivities`.
Bấm Back từ màn đích → về Kế hoạch, không rơi ra màn hình chính của máy. Áp cho chuông
lịch và chuông hết giờ Focus.

---

## 4. Tab Kế hoạch

Thứ tự từ trên xuống — **tóm tắt trước, nút sau**:

```
Kế hoạch hôm nay                         24sp đậm
Thứ năm, 17 tháng 9                      13sp chu_phu
┌─ Tóm tắt ───────────────────────────┐  thẻ, padding 14/13
│    5          3g15′        2        │  3 cột weight 1, số 22sp CENTER
│   việc    tổng thời gian  còn lại   │  nhãn 12sp
│ (● Cao·1) (● Vừa·3) (● Thấp·1)      │  3 chip cao 40, LUÔN đủ 3 kể cả = 0
└─────────────────────────────────────┘
┌─ TIẾP THEO · 14:00 ─────────────────┐  viền cam
│ 📚 Ôn thi                           │
│ 14:00 – 15:00 · 1 giờ               │
│ [    Bắt đầu việc này    ]          │  → Focus, điền tên + thời lượng, chạy luôn
└─────────────────────────────────────┘
ƯU TIÊN CAO                              nhóm theo ưu tiên, trong nhóm theo giờ
(○) 📝 Nộp báo cáo   09:00–09:30 ▌       ô tròn 44 · vạch ưu tiên 6×30 bên phải
ƯU TIÊN VỪA …
[ + Thêm kế hoạch ]   [ Xem lịch tuần ]
Mẹo: vuốt trái để đánh dấu xong, vuốt phải để xoá.
```

---

## 5. Trình tạo/sửa kế hoạch

### 5.1. Lỗi căn gióng — nguyên nhân và khuôn sửa

**Nguyên nhân:** Lexend có ascender cao hơn descender; `TextView` mặc định
`includeFontPadding = true` nên chữ bị đẩy thấp hơn tâm icon vài dp. Mỗi hàng cũ lại tự
cân padding riêng.

**Khuôn hàng dùng chung** cho mọi dòng:

```kotlin
fun hang(icon, nhan, giaTri, khiCham) = LinearLayout(HORIZONTAL).apply {
    gravity = CENTER_VERTICAL
    minimumHeight = 56.dp
    addView(ImageView(icon), LayoutParams(20.dp, 20.dp).apply { marginEnd = 12.dp })
    addView(TextView(nhan).apply { includeFontPadding = false; textSize = 15f },
            LayoutParams(0, WRAP, weight = 1f))
    addView(TextView(giaTri).apply {                  // can phai, mau chu_lien_ket
        includeFontPadding = false; gravity = END or CENTER_VERTICAL })
}
```

Vạch ngăn giữa hàng: cao 1 dp, `marginStart = 32 dp` (thẳng mép chữ, không chạy dưới icon).

### 5.2. Bố cục

```
[😀] [ Tên kế hoạch                       ]    56 dp
┌ ⚑ Ưu tiên ──────────────────────────────┐
│ (● Cao) (● Vừa) (● Thấp)                 │    chip cao 44, weight 1
├ 📅 Ngày ···················· Thứ Năm ───┤
│ 🕒 Bắt đầu ···················· 14:00   │    → TimePicker 24h
│ 🕒 Kết thúc ··················· 15:20   │    → TimePicker; ≤ bắt đầu = "(hôm sau)"
│    Kéo dài 1 giờ 20 phút                 │    TỰ TÍNH
│ (+15 phút) (+30 phút) (+1 giờ) …         │    lối tắt đặt Kết thúc, không phải giới hạn
├ ⟲ Lặp lại ──────────────────────────────┤
│ (Không lặp) (Hằng ngày) (Theo thứ)       │
│  (T2)(T3)(T4)(T5)(T6)(T7)(CN)            │    tròn 42 dp, chọn nhiều, luôn còn ≥1
│  T2, T5 hằng tuần                        │
├ 🔔 Nhắc tôi ────────────────────────────┤
│ (15 phút trước ✕) (Đúng giờ ✕)           │    mốc đã chọn
│ (+ 5 phút trước) (+ 1 giờ trước) (Tuỳ chỉnh…) │  số 1–90 × phút/giờ/ngày, trần 7 ngày
└──────────────────────────────────────────┘
[          Lưu kế hoạch          ]              cố định dưới đáy
```

Đổi giờ Bắt đầu thì **giữ thời lượng**, Kết thúc đi theo. Thiếu tên: báo ngay dưới ô,
cuộn lên, không đóng màn hình.

---

## 6. Cử chỉ vuốt

Áp cho: thẻ Kế hoạch, khối Lịch, thẻ Nhật ký (chỉ xoá), thẻ Biên bản (chỉ xoá).

```
onInterceptTouchEvent / onTouchEvent (cả hai đường):
  DOWN  : x0, y0 = vị trí; dangKeo = false
  MOVE  : dx = x - x0; dy = y - y0
          nếu chưa kéo VÀ hướng có hành động
             VÀ |dx| > touchSlop VÀ |dx| > 1.5·|dy|:
                dangKeo = true; parent.requestDisallowInterceptTouchEvent(true)
          nếu đang kéo: the.translationX = dx; vẽ nền lộ ra
                        alpha nền = 1.0 nếu |dx| > 35% bề ngang, ngược lại 0.75
  UP    : nếu |dx| > 35% bề ngang:
             dx > 0 → trượt ra hết (160 ms) → rung xong → XOÁ → hiện Hoàn tác 5 s
             dx < 0 → trượt về 0 → rung xong → ĐỔI XONG
          ngược lại → trượt về 0
```

- Vuốt **phải = xoá** (nền navy, chữ "Xoá" bên trái). Vuốt **trái = xong** (nền vàng, chữ bên phải).
- **Ngưỡng 35%**: xoá nhầm là lỗi nặng nhất, cần một cú vuốt có chủ đích.
- **Không hộp thoại xác nhận** — thanh Hoàn tác 5 giây. Hộp thoại chèn một bước vào *mọi*
  lần xoá đúng; hoàn tác chỉ tốn thêm cho lần xoá *nhầm*.
- Tỉ lệ 1,5 giữa ngang và dọc: vuốt xéo vẫn cuộn trang bình thường.
- **TalkBack:** mỗi thẻ có `AccessibilityAction` "Xoá" và "Xong" trong menu hành động.
- **Không còn nhấn giữ ở đâu cả.** Đánh dấu xong còn có ô tròn 44 dp — một chạm.

---

## 7. Focus

### 7.1. Không còn rào cản

Vào tab là bấm **Bắt đầu** được ngay. Không ô nào bắt buộc. Tên việc, bước đầu, lý do
đều nằm ở màn Gỡ rối và đều tuỳ chọn. Chỉ **đếm ngược**, 1–120 phút.

Tab này **chạy hẳn trên máy**, không cần laptop. Phiên có laptop cũ vẫn còn: Cài đặt →
"Phiên có laptop (thử nghiệm)".

### 7.2. Đồng hồ — mặt tuyệt đối 60 phút (kiểu Time Timer)

| | Cách A: vòng luôn đầy lúc bắt đầu (Tiimo) | **Cách B: mặt 60 phút cố định — CHỌN** |
|---|---|---|
| 15 phút trông thế nào | giống hệt 90 phút lúc bắt đầu | luôn là 1/4 mặt |
| Học được cảm giác thời gian | không | có — sau vài lần, "1/4 mặt" thành kích thước quen |

Người mù thời gian không thiếu con số, họ thiếu **cảm nhận** 15 phút dài cỡ nào.

```
       0                   quạt còn lại: gờ 1 trên mặt (bán kính 0,86 r)
   45     15               60–120 phút: mặt đầy + VÒNG NGOÀI mỏng cho giờ thứ 2
       30                  màu theo phần còn lại: >50% dh_con_nhieu,
   ( 24:10 )               >15% dh_sap_den, còn lại dh_di_ngay
   còn lại                 nút giữa bán kính 0,42 r: thời gian + trạng thái
```

- **Đặt giờ = xoay núm** (như Apple Clock): mỗi vòng 60 phút, tối đa 2 vòng, bước 1 phút.
  Chạm xuống là nhảy tới góc đó. Rung "tích" mỗi mốc 5 phút.
- Chỉ xoay được khi **chưa chạy** — chạm nhầm lúc đang chạy không đổi giờ.
- Chip nhanh: 5′ 10′ 15′ 25′ 45′ 1h 1h30 2h.
- TalkBack: vuốt lên/xuống = ±5 phút.
- Lưu **mốc kết thúc** chứ không đếm ngầm: đóng app, khoá máy vẫn đúng. Chuông báo qua
  `AlarmManager` khi hết giờ.

Nút dưới đồng hồ: **Bắt đầu / Tạm dừng / Tiếp tục** (chính) · `+5 phút` · `Dừng lại`
(có Hoàn tác). Hết giờ: thẻ vàng "Hết giờ rồi. Bạn đã tập trung 25 phút." + nhắc lại lý
do (nếu có) + `Nghỉ 5 phút` · `Làm thêm 10 phút` · `Xong, đóng lại`. Ghi vào tiến độ, sổ
thời lượng, và đánh dấu kế hoạch xong nếu mở từ tab Kế hoạch.

### 7.3. Nút `+ Gỡ rối` — vị trí

**Trên thanh tiêu đề, cạnh icon Cài đặt, có chữ.** Vùng ngón cái đã có MỘT nút chính
(Bắt đầu). Hai nút lớn cạnh tranh ở cùng chỗ là hai lựa chọn phải cân nhắc — đúng thứ
nhóm người dùng này khó nhất. `+` là đường phụ nên ở trên; có chữ vì `+` trơn không nói
nó làm gì.

### 7.4. Màn Gỡ rối

```
← Gỡ rối để bắt đầu                        Bỏ qua
Không cần trả lời hết. Câu nào khó thì bỏ trống —
bấm Bắt đầu lúc nào cũng được.

Việc gì đang chờ bạn?            Tuỳ chọn    [ô nhập]
Bước nhỏ nhất, làm được trong 2 phút?        [ô nhập]
Điều gì đang làm bạn khựng lại?              chip 2 cột, chọn nhiều:
  (Không biết bắt đầu từ đâu) (Việc có vẻ quá lớn)
  (Sợ làm chưa tốt)           (Thấy chán)
  (Đang mệt)                  (Nhiều thứ quá)
  ┃ Bản nháp được phép xấu. Sửa sau dễ hơn…   một câu gợi ý theo chip vừa chọn
Làm xong thì bạn được gì?                    [ô nhập]
Thử trong bao lâu?   (5′) (10′●) (15′) (25′)   mặc định 10 — "chỉ 10 phút" dễ nói "có"
[        Bắt đầu hẹn giờ        ]            luôn bấm được → về Focus, chạy ngay
```

Tất cả câu hỏi hiện **cùng lúc**: thấy hết ngay từ đầu nghĩa là "chỉ có chừng này", không
có bước ẩn phía sau. Thứ tự: gọi tên việc → bước nhỏ nhất → gọi tên cản trở → nhớ lý do →
cam kết thời gian ngắn.

---

## 8. Nhật ký

### 8.1. Sửa lệch tâm

| Chỗ | Nguyên nhân | Sửa |
|---|---|---|
| Số Streak / Việc đã xong | cột `WRAP_CONTENT` + font padding | mỗi ô `FrameLayout` cao **88 dp** cố định; số và nhãn `MATCH_PARENT` + `CENTER` + `includeFontPadding=false`; vạch ngăn 1×56 dp giữa |
| 7 chấm | trộn 2 loại view kích thước đo khác nhau | mỗi chấm cùng một `FrameLayout` **32×32 dp**, tick 16 dp ở `CENTER`; cột weight 1; nhãn thứ `MATCH_PARENT` + `CENTER` |

### 8.2. Còn lại

- **Tự điểm danh:** mỗi tab hiện lên gọi `SoTienDo.diemDanh()`. Ngày chỉ mở app cũng tính
  vào chuỗi và vào 7 chấm; không tính vào "Việc đã xong".
- **Lời nhắn hôm nay** ở đầu tab. 31 câu, chỉ số `(ngày × 7 + 3) mod 31`: hai ngày liền
  nhau không bao giờ trùng, sau 31 ngày mọi câu xuất hiện đúng một lần. Đổi theo **ngày**,
  không theo lần mở — tránh vòng lặp "mở lại xem câu mới". Test canh gác: không "bạn
  phải/bạn nên/cố lên".
- **Trang viết** toàn màn hình: chữ 18sp, giãn dòng 1,5, không viền ô, chiếm ≥55% chiều cao.
  Lưu nháp mỗi lần rời màn; Back/mũi tên/Xong đều **lưu**. "Bạn thấy thế nào?" nằm dưới,
  tuỳ chọn — viết trước, gọi tên cảm xúc sau.
- **Xuất:** "Chọn để xuất" → chạm thẻ để chọn (ô tích) → chọn **Bản dễ đọc** (mặc định)
  hoặc **Bản tiêu chuẩn** → "Xuất Word" → trình chọn nơi lưu của hệ thống.

---

## 9. Biên bản và Meety

### 9.1. Luồng

```
Có ghi âm / transcript Zoom-Meet-Teams              Không có
        │                                               │
laptop: python main.py --input hop.vtt --mock           │
        │  → output/<id>_minutes.json                   │
        ├── python xuat_word.py <id>_minutes.json       │
        │     → <id>_bien_ban.docx + _de_doc.docx       │
        └── chép JSON sang điện thoại                   │
              │                                         │
app: tab Biên bản → [Nhập từ Meety]            [Ghi tay] → trang 5 ô
              └──────────────► biên bản ◄───────────────┘
                     [Xuất Word] → Tiêu chuẩn | Dễ đọc
```

App **không** mang giao diện Meety vào — chỉ lấy dữ liệu đã có cấu trúc: tiêu đề, ngày,
thời lượng, người dự, tl;dr, quyết định **còn hiệu lực** (bỏ `rejected`/`superseded_by`),
việc (kèm người nhận + hạn), câu hỏi mở.

### 9.2. Hai hồ sơ Word

| | Tiêu chuẩn | Dễ đọc |
|---|---|---|
| Phông | Times New Roman 13pt (NĐ 30/2020) | **Verdana 13pt** |
| Giãn dòng / cách đoạn | 1,15 / 6pt | **1,5 / 12pt**, giãn chữ 0,5pt |
| Căn lề | đều hai bên (app) · trái (Meety) | **trái** |
| Nền trang / chữ | trắng / đen | **kem `#FFF8E7` / navy `#1F1E2E`** |
| Nghiêng, gạch chân, HOA cả câu | có (trích dẫn, tiêu đề) | **không** — nhấn bằng đậm |
| Bảng nhiều cột | có | **không** — mỗi việc một khối dọc |
| Câu > 110 ký tự | giữ nguyên | **tách thành gạch đầu dòng** |
| Khối nổi bật | không | Tóm tắt, Việc cần làm: nền `#FFF1C2` + viền trái cam 3pt |
| Thứ tự | hành chính: thành phần → tóm tắt → quyết định → phân công | **hành động trước:** tóm tắt → việc → đã chốt → câu hỏi → rủi ro → người dự |
| Quyết định bị thay thế | giữ (truy vết) | bỏ |

Vì sao Verdana mà không Lexend hay OpenDyslexic: Word của **người nhận** thường không có
hai phông đó và sẽ thay bằng Times New Roman — hỏng cả mục đích. Verdana có sẵn trên
Windows/macOS, chữ rộng, phân biệt rõ b/d, I/l/1, đủ dấu tiếng Việt, và nằm trong danh sách
khuyến nghị của BDA.

Trong khối "Việc cần làm", tên việc cách dòng "Ai · Hạn" 2pt, còn giữa hai việc cách
12pt — mắt thấy ngay dòng nào thuộc việc nào.

---

## 10. Lexend trong hộp thoại hệ thống

Phủ bằng **hai lớp**, vì một lớp không đủ:

| Lớp | Phạm vi | Cách |
|---|---|---|
| Theme (Android 8+) | mọi TextView do hệ thống tạo, kể cả trong hộp thoại | `android:fontFamily="@font/lexend"` trong `values-v26/themes.xml`, và trong theme của AlertDialog / DatePicker / TimePicker (`android:alertDialogTheme`, `datePickerDialogTheme`, `timePickerDialogTheme`) |
| Runtime (Android 7 trở lên) | những view đặt phông riêng qua style, và dòng danh sách tạo trễ | `GiaoDien.hopThoai(dialog)` sau `show()`: gắn `OnGlobalLayoutListener` áp Lexend cho cây view, chỉ đặt khi khác phông nên không lặp vô hạn |

`AlertDialog.Builder.hien()` thay cho `.show()` ở toàn bộ 21 chỗ mở hộp thoại.

Theme hộp thoại cũng sửa một lỗi tương phản có sẵn: nút "Huỷ"/"Xoá" trong hộp thoại
lấy màu nhấn vàng trên nền trắng (≈1,4:1), nay dùng `chu_lien_ket`.

**Toast không sửa được.** Từ Android 11, Toast chữ do SystemUI vẽ, app không đổi
được phông. 12 Toast đã thay bằng `ThongBao` — một thanh trong cửa sổ app, đúng
phông, đúng màu, và TalkBack đọc được (live region).

Còn lại ngoài tầm với: số trên mặt đồng hồ tròn của TimePicker và lưới ngày của
DatePicker do hệ thống vẽ bằng Paint với phông cứng.

## 11. Build APK

Đường chính vẫn là `cd android && ./gradlew assembleDebug`.

Thêm đường dự phòng `android/tools/build_khong_gradle.sh` — dùng khi Gradle hỏng
sát giờ thi, hoặc trên máy không vào được `dl.google.com`:

```
aapt → R.java → javac → kotlinc (JVM 1.8) → ProGuard (chỉ thu gọn)
     → dx → zip → zipalign → apksigner
```

Hai chỗ khác bản Gradle, nói thẳng:
- **`dx` thay `d8`,** nên không "desugar" được `invokedynamic`. `kotlin-stdlib`
  dùng nó ở vài hàm; ProGuard loại các hàm app không gọi tới là hết. Vì vậy
  `Lich.theoUuTien` viết `Comparator` tường minh thay cho `compareBy(vararg)`.
- **Không có R8/minify,** APK lớn hơn bản release đôi chút.

Kết quả đã chạy trên máy này: **APK 616 KB**, ký và `apksigner verify` qua, đủ 11
màn hình và 4 receiver, có `res/font-v26`, `values-night`, `sw600dp`.

## 12. Kiểm chứng

| Kiểm | Kết quả |
|---|---|
| Type-check toàn bộ Kotlin (app + frontend) với Android API 34 | sạch, 114 lớp |
| Test Kotlin | 104 pass (26 mới ở `V4Test.kt`); 15 bài chỉ chạy được qua Gradle — cần `org.json` thật và đường dẫn fixture |
| Test Python `adc_wayfinding` | 442 pass |
| Test Meety mới `test_docx_de_doc.py` | 12 pass |
| `.docx` do Kotlin và Python tạo | mở bằng python-docx, render bằng LibreOffice |
| Tài nguyên XML | parse sạch; không trùng tên; bản tối đủ mọi màu của bản sáng |
| Tương phản | đo WCAG từng cặp ở §1 |
| **Build APK** | 616 KB, chữ ký hợp lệ, thành phần Manifest khớp lớp trong DEX |
| **Preview HTML v4** | 14 màn hình, có công tắc Sáng/Tối và Lexend, không lỗi JS, chạy cả `file://` lẫn Live Server |
| **iOS** | 35 tệp Swift qua `ios/tools_kiem_swift.py` (ngoặc cân, ký hiệu tồn tại, EnvironmentObject đủ) — **chưa biên dịch** |

## 13. Chưa làm — nói thẳng

- **APK chưa chạy trên máy thật.** Máy này không có emulator (không tải được ảnh
  hệ thống). Vuốt, xoay đồng hồ và rung chỉ kiểm chắc được bằng tay trên máy.
- **iOS viết xong nhưng CHƯA TỪNG BIÊN DỊCH.** Linux không có SwiftUI; chỉ kiểm
  được cấu trúc bằng script. Lỗi kiểu chỉ Xcode bắt được.
- Chưa thử với người dùng ADHD/dyslexia thật; các con số (ngưỡng vuốt 35%, mặc định 10
  phút, 110 ký tự) là điểm khởi đầu có lý do, chưa hiệu chỉnh.
- Số trên TimePicker/DatePicker của hệ thống vẫn dùng phông máy (§10).
