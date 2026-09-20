package vn.adc2026.wayfinding

import android.app.Activity
import android.app.UiModeManager
import android.content.Context
import android.content.res.Configuration
import android.os.Build

/**
 * ====================================================================
 * SANG / TOI / THEO MAY (v5.1)
 * ====================================================================
 *
 * ----- DOC PHAN NAY TRUOC KHI SUA -----
 *
 * Ban v3 da tung lam dung viec nay va lam app VANG tren Galaxy Tab S7 FE:
 * `createConfigurationContext` doi `uiMode` roi goi `recreate()`. Ghi chu
 * dau `NgonNgu.kt` con giu lai canh bao do, va vi the duong ngon ngu o
 * ben ay co y chi dong vao Locale, khong dong vao che do giao dien.
 *
 * Nen o day chia lam hai duong, va duong chinh KHONG phai duong da hong:
 *
 *   API >= 31 (Android 12+)   `UiModeManager.setApplicationNightMode()`
 *                             API chinh chu cua he thong. He thong tu lo
 *                             viec ve lai, khong ai phai goi `recreate()`,
 *                             va lua chon song qua ca lan tat app.
 *                             Galaxy Tab S7 FE chay Android 14 -> may thu
 *                             nghiem chinh di duong nay.
 *
 *   API < 31                  Boc `uiMode` trong `attachBaseContext`, dung
 *                             MOT LAN moi lan Activity duoc dung len.
 *                             Day la cung khuon voi `NgonNgu.boc()` - thu
 *                             da chay on dinh tren may that - chu khong
 *                             phai khuon "doi context roi recreate trong
 *                             luc dang chay" cua v3.
 *
 * ----- Vi sao khong dung AppCompatDelegate -----
 *
 * `AppCompatDelegate.setDefaultNightMode()` la cach quen thuoc nhat, nhung
 * no doi moi man hinh phai la `AppCompatActivity`. Ca app nay dung `Activity`
 * thuan - mot quyet dinh co chu dich, xem `UIUX_QUYET_DINH.md`. Doi ca 20
 * man hinh sang AppCompat chi de doi mau nen la mot thay doi lon hon nhieu
 * so voi thu dang can.
 */
object CheDoToi {

    const val THEO_MAY = ""
    const val SANG = "sang"
    const val TOI = "toi"

    /** Danh sach hien trong Cai dat: ma + id chuoi. */
    val DANH_SACH = listOf(
        THEO_MAY to R.string.cd_theme_theo_may,
        SANG to R.string.cd_theme_sang,
        TOI to R.string.cd_theme_toi,
    )

    /**
     * Goi trong `attachBaseContext` cua moi Activity, SAU `NgonNgu.boc`.
     *
     * Tren API >= 31 ham nay tra ve context goc nguyen ven: he thong da
     * biet che do roi qua `setApplicationNightMode`, boc them chi la lam
     * hai lan cung mot viec.
     */
    fun boc(goc: Context): Context {
        val ma = AppSettings(goc).cheDoToi
        if (ma == THEO_MAY) return goc              // theo may: khong dong vao gi ca
        if (Build.VERSION.SDK_INT >= 31) return goc // da xu ly o apDung()

        val cf = Configuration(goc.resources.configuration)
        cf.uiMode = (cf.uiMode and Configuration.UI_MODE_NIGHT_MASK.inv()) or
            if (ma == TOI) Configuration.UI_MODE_NIGHT_YES else Configuration.UI_MODE_NIGHT_NO
        return goc.createConfigurationContext(cf)
    }

    /**
     * Bao cho he thong biet che do vua chon. Goi mot lan luc app khoi dong
     * va moi lan nguoi dung doi trong Cai dat.
     *
     * Tren API < 31 ham nay khong lam gi - viec ep nam o `boc()`.
     */
    fun apDung(ctx: Context) {
        if (Build.VERSION.SDK_INT < 31) return
        val um = ctx.getSystemService(Context.UI_MODE_SERVICE) as? UiModeManager ?: return
        um.setApplicationNightMode(
            when (AppSettings(ctx).cheDoToi) {
                SANG -> UiModeManager.MODE_NIGHT_NO
                TOI -> UiModeManager.MODE_NIGHT_YES
                else -> UiModeManager.MODE_NIGHT_AUTO
            })
    }

    /**
     * Doi che do tu man hinh Cai dat.
     *
     * Tren API >= 31, `setApplicationNightMode` tu lo viec ve lai - goi
     * them `recreate()` la ve hai lan, va man hinh chop mot cai.
     * Tren API < 31 thi phai tu ve lai, vi `boc()` chi chay luc dung
     * Activity len.
     */
    fun doi(a: Activity, ma: String) {
        val s = AppSettings(a)
        if (s.cheDoToi == ma) return
        s.cheDoToi = ma
        apDung(a)
        if (Build.VERSION.SDK_INT < 31) a.recreate()
    }

    /** Vi tri dang chon, de danh dau trong hang chip. */
    fun viTri(ctx: Context): Int =
        DANH_SACH.indexOfFirst { it.first == AppSettings(ctx).cheDoToi }.coerceAtLeast(0)
}
