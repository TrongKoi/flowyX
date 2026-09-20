package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.graphics.Typeface
import android.util.TypedValue
import android.view.View
import android.view.ViewGroup
import android.widget.TextView

/**
 * GIAO DIEN - kieu chu, co chu va chu de, dung chung cho moi Activity.
 *
 * ====================================================================
 * BA KIEU CHU, TAT CA DU DAU TIENG VIET
 * ====================================================================
 *
 * Lexend (mac dinh) - Andika (cho nguoi kho doc) - Inter (trung tinh).
 * Ly do loai Atkinson Hyperlegible va OpenDyslexic: ghi trong
 * `AppSettings.kieuChu`. Tom tat: thieu dau tieng Viet.
 *
 * ====================================================================
 * CO CHU KEO GIAN CA LAYOUT, KHONG CHI CHU
 * ====================================================================
 *
 * Doi rieng co chu thi chu to ra con nut, le va vung cham giu nguyen -
 * chu tran ra ngoai nut. `apCoChu` nhan CA kich thuoc chu, chieu cao toi
 * thieu va padding cua tung view voi cung mot he so, nen bo cuc gian deu.
 *
 * Moi view duoc danh dau bang tag de khong bi nhan he so hai lan khi
 * `apGiaoDien` chay lai (vi du sau khi doi ngon ngu).
 *
 * ====================================================================
 * CHE DO SANG / TOI
 * ====================================================================
 *
 * THEO MAY, khong co nut doi trong app. Ban v3 tung doi thu cong bang
 * `createConfigurationContext` + `recreate()` va lam app VANG RA tren
 * Galaxy Tab S7 FE. De he thong lo vong doi Activity thi khong con chuoi
 * goi do. Bang mau dem o `values-night/colors.xml`.
 */
object GiaoDien {

    private val dem = HashMap<String, Typeface>()
    private const val TAG_DA_GIAN = -0x5F10_0001

    /** Typeface theo lua chon hien tai. Tra null = dung font he thong. */
    fun font(ctx: Context, datDam: Boolean): Typeface? {
        val kieu = AppSettings(ctx).kieuChu
        val tep = AppSettings.TEP_CHU[kieu] ?: return null
        val ten = if (datDam) tep.second else tep.first
        dem[ten]?.let { return it }
        return try {
            Typeface.createFromAsset(ctx.assets, "fonts/$ten").also { dem[ten] = it }
        } catch (_: RuntimeException) {
            null                      // tep font hong -> van chay bang font he thong
        }
    }

    /** Ap CA kieu chu lan co chu cho ca cay view. Goi sau khi dung xong man hinh. */
    fun apGiaoDien(v: View, ctx: Context) {
        apFontKhongKiem(v, ctx)
        apCoChu(v, AppSettings(ctx).coChu)
    }

    /** Giu ten cu de code hien co khong phai sua. */
    fun apFont(v: View, ctx: Context) = apGiaoDien(v, ctx)

    private fun apFontKhongKiem(v: View, ctx: Context) {
        when (v) {
            is TextView -> {
                val laDam = v.typeface?.isBold == true ||
                    (android.os.Build.VERSION.SDK_INT >= 28 && (v.typeface?.weight ?: 400) >= 600)
                val f = font(ctx, laDam) ?: return
                // Chi dat khi khac: setTypeface goi requestLayout, dat lai moi lan
                // se thanh vong lap voi OnGlobalLayoutListener ben duoi.
                if (v.typeface !== f) v.typeface = f
            }
            is ViewGroup -> for (i in 0 until v.childCount) apFontKhongKiem(v.getChildAt(i), ctx)
        }
    }

    /**
     * Nhan kich thuoc chu, chieu cao toi thieu va padding voi `k`.
     * He so 1.0 thi khong lam gi ca - khong dung toi nhanh nay.
     */
    fun apCoChu(v: View, k: Float) {
        if (k == 1f) return
        apCoChuMot(v, k)
    }

    private fun apCoChuMot(v: View, k: Float) {
        if (v.getTag(R.id.tag_da_gian) == null) {
            if (v is TextView) {
                v.setTextSize(TypedValue.COMPLEX_UNIT_PX, v.textSize * k)
                if (v.minHeight > 0) v.minHeight = (v.minHeight * k).toInt()
                if (v.minimumHeight > 0) v.minimumHeight = (v.minimumHeight * k).toInt()
                v.setPaddingRelative(
                    (v.paddingStart * k).toInt(), (v.paddingTop * k).toInt(),
                    (v.paddingEnd * k).toInt(), (v.paddingBottom * k).toInt())
                // Chieu cao co dinh phai gian theo, khong thi chu tran ra ngoai.
                val lp = v.layoutParams
                if (lp != null && lp.height > 0) { lp.height = (lp.height * k).toInt(); v.layoutParams = lp }
            }
            v.setTag(R.id.tag_da_gian, TAG_DA_GIAN)
        }
        if (v is ViewGroup) for (i in 0 until v.childCount) apCoChuMot(v.getChildAt(i), k)
    }

    /**
     * Theo doi mot cay view: moi lan layout lai (them dong danh sach, doi
     * trang thai) thi ap kieu chu cho view MOI. Dung cho hop thoai he
     * thong, noi cac dong danh sach duoc tao TRE sau khi show().
     */
    fun theoDoi(goc: View, ctx: Context) {
        apFontKhongKiem(goc, ctx)
        goc.viewTreeObserver.addOnGlobalLayoutListener { apFontKhongKiem(goc, ctx) }
    }

    /** Ap kieu chu cho mot hop thoai vua show(). */
    fun hopThoai(d: android.app.Dialog) {
        d.window?.decorView?.let { theoDoi(it, d.context) }
    }

    /**
     * Chon theme TRUOC super.onCreate. Theme mac dinh (manifest) co Lexend
     * o tang theme tu Android 8; chon font he thong thi doi sang theme
     * khong khai bao fontFamily, de ca hop thoai he thong cung doi theo.
     */
    fun apTheme(a: Activity) {
        if (AppSettings(a).kieuChu == AppSettings.CHU_HE_THONG) a.setTheme(R.style.FlowyHeThong)
        // Goi o day vi moi Activity deu goi `apTheme` ngay dau `onCreate`,
        // truoc `super.onCreate` - som nhat co the trong vong doi.
        CheDoToi.apDung(a)
    }

    /**
     * Boc Context cho `attachBaseContext`: ngon ngu TRUOC, roi che do toi.
     *
     * Goi mot ham thay vi hai o 16 man hinh - them mot lop boc nua ve sau
     * thi sua dung mot cho, khong phai di sua 16 cho va quen mat mot.
     */
    fun boc(goc: android.content.Context): android.content.Context =
        CheDoToi.boc(NgonNgu.boc(goc))

    /**
     * Dau vet cua moi thu anh huong toi cach ve man hinh. Activity so dau
     * vet luc onResume voi luc dung man hinh; khac nhau thi ve lai ngay -
     * day la cach doi font / co chu / ngon ngu co hieu luc TUC THI ma
     * khong can khoi dong lai app.
     */
    fun dauVet(ctx: Context): String {
        val s = AppSettings(ctx)
        return "${s.kieuChu}|${s.coChu}|${s.ngonNgu}|${s.mucRung}|${s.cheDoToi}"
    }
}

/** show() + ap kieu chu. Dung thay cho show() o moi hop thoai. */
fun android.app.AlertDialog.Builder.hien(): android.app.AlertDialog =
    show().also { GiaoDien.hopThoai(it) }

fun android.app.Dialog.hien() {
    show()
    GiaoDien.hopThoai(this)
}
