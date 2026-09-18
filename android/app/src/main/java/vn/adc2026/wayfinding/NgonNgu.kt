package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.content.res.Configuration
import android.os.Build
import java.util.Locale

/**
 * NGON NGU - tieng Viet va tieng Anh (v5).
 *
 * ====================================================================
 * CACH LAM VA VI SAO AN TOAN
 * ====================================================================
 *
 * Moi Activity goi `NgonNgu.boc()` trong `attachBaseContext`. Ham nay
 * tra ve mot Context co Locale da chon. Chuoi hien len lay tu
 * `values/strings.xml` (vi) hoac `values-en/strings.xml` (en) - he thong
 * tu chon, app khong tu dich chuoi nao.
 *
 * Luu y quan trong: ban v3 tung dung `createConfigurationContext` +
 * `recreate()` cho CHE DO SANG/TOI va lam app vang tren Galaxy Tab S7 FE.
 * Cho nen o day:
 *
 *   · `boc()` chi doi Locale, khong dung toi che do giao dien.
 *   · `recreate()` CHI goi khi nguoi dung tu bam doi ngon ngu trong Cai
 *     dat - mot lan, do nguoi dung chu dong, khong nam trong vong lap
 *     nao dang chay.
 *   · Neu nguoi dung de "Theo may", ham tra ve context goc nguyen ven,
 *     khong tao context moi -> duong nguy hiem kia khong he chay.
 *
 * ====================================================================
 * DOI NGAY, KHONG CAN MO LAI APP
 * ====================================================================
 *
 * `GiaoDien.dauVet()` co ca ngon ngu. Man hinh nao dang mo se so dau vet
 * luc onResume, thay khac thi tu ve lai - nen quay ve tu Cai dat la thay
 * ngon ngu moi ngay lap tuc.
 */
object NgonNgu {

    const val VIET = "vi"
    const val ANH = "en"

    /** Danh sach hien trong Cai dat: ma + ten hien len. */
    val DANH_SACH = listOf("" to "Theo máy", VIET to "Tiếng Việt", ANH to "English")

    /** Goi trong attachBaseContext cua moi Activity. */
    fun boc(goc: Context): Context {
        val ma = AppSettings(goc).ngonNgu
        if (ma.isBlank()) return goc                 // theo may: khong dong vao gi ca
        val loc = Locale(ma)
        Locale.setDefault(loc)
        val cf = Configuration(goc.resources.configuration)
        if (Build.VERSION.SDK_INT >= 24) {
            cf.setLocales(android.os.LocaleList(loc))
        } else {
            @Suppress("DEPRECATION") cf.locale = loc
        }
        return goc.createConfigurationContext(cf)
    }

    /**
     * Doi ngon ngu tu man hinh Cai dat. Ve lai chinh man hinh do de nhan
     * chuoi moi; cac man hinh phia sau tu ve lai o onResume nho dau vet.
     */
    fun doi(a: Activity, ma: String) {
        val s = AppSettings(a)
        if (s.ngonNgu == ma) return
        s.ngonNgu = ma
        a.recreate()
    }

    /** Ma ngon ngu dang thuc su duoc dung (de danh dau lua chon). */
    fun dangDung(ctx: Context): String = AppSettings(ctx).ngonNgu
}
