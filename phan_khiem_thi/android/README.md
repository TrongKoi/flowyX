# Phần Android của bản điều hướng — đã cắt khỏi Flowy

Thư mục này **không nằm trong bản build**. `android/settings.gradle.kts`
không trỏ tới đây, và `./gradlew` không chạm vào nó.

Cùng lý do với [`phan_khiem_thi/`](../README.md) ở thư mục cha: BoussoleX
có hai sản phẩm, mỗi cái một repo, và ngày 15/09/2026 hai bên tách ra.

> **Bản đang được bảo trì nằm ở [OpticGuard](https://github.com/TrongKoi/opticguard).**
> Sửa ở đây sẽ không đi đâu cả.

## Có gì trong này

| Tệp | Làm gì |
|---|---|
| `ArMath.kt` | Toàn bộ toán trục toạ độ ARCore. Bản tham chiếu là `arcore.py` bên Python |
| `DepthSampler.kt` | Lưới độ sâu 16×12, gộp bằng phân vị 20 |
| `ObjectVision.kt` | Nhận diện vật thể bằng ML Kit |
| `BarometerReader.kt` | Áp suất khí quyển, để biết đang ở tầng nào |
| `NfcLauncher.kt` | Chạm thẻ NFC để mở app và đặt điểm xuất phát |
| `LaunchTileService.kt` | Ô trong bảng Cài đặt nhanh |
| `test/ArMathTest.kt` | Test của `ArMath` |
| `res/shortcuts.xml` | Lối tắt khi chạm giữ biểu tượng app |
| `markers/` | Năm ảnh mã ArUco dùng cho Augmented Images |

## Vì sao giữ lại thay vì xoá

Không mất gì cả, và vẫn tra cứu được khi cần. Riêng `ArMath.kt` còn có
giá trị ngoài phần điều hướng: nó là bản Kotlin của một phần toán học đã
được kiểm chứng kỹ, và cách nó tách phần thuần toán ra khỏi phần phụ
thuộc Android là mẫu đáng theo.

## Thứ đi theo chúng

Cắt phần này ra kéo theo hai phụ thuộc nặng rời khỏi `build.gradle.kts`:

```
com.google.ar:core:1.44.0
com.google.mlkit:object-detection:17.0.2
```

APK của Flowy sau khi bỏ: **50 MB → 856 KB**.

Con số 50 MB đầu tiên là do bản build tăng dần còn giữ `.dex` cũ — phải
`./gradlew clean` mới thấy đúng. Ai đo lại mà thấy 50 MB thì kiểm tra
điều đó trước.
