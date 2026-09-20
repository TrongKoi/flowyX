package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.animation.AccelerateDecelerateInterpolator
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView

/**
 * ====================================================================
 * MAN HINH MO APP (v5)
 * ====================================================================
 *
 * Dau logo dung giua, roi luot sang trai trong khi chu "flowyX" lo dan ra
 * ben phai. Tong 620 ms, roi chuyen man ngay.
 *
 * ----- Nguyen tac cho nguoi qua tai giac quan -----
 *
 *   · KHONG chop sang, khong doi mau nen, khong phong to giat cuc.
 *   · Mot chuyen dong duy nhat, mot huong, toc do giam dan (ease-out).
 *   · Khong am thanh, khong rung.
 *   · TON TRONG "Xoa hieu ung" cua he thong: he so animation = 0 thi bo
 *     qua hoat hinh, vao thang man hinh sau.
 *   · Khong bao gio la man hinh cho: cac buoc nap du lieu deu chay o day
 *     song song, nen 620 ms nay khong lam app cham hon.
 *
 * ----- Di dau tiep -----
 *
 *   chua chon ngon ngu  -> ChonNgonNguActivity
 *   chua co tai khoan   -> DangKyActivity
 *   co tai khoan, chua dang nhap -> DangNhapActivity
 *   da dang nhap        -> ViecCanLamActivity (tab Ke hoach)
 */
class KhoiDongActivity : Activity() {

    override fun attachBaseContext(moi: Context) {
        super.attachBaseContext(GiaoDien.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)

        val goc = FrameLayout(this).apply { setBackgroundColor(mau(R.color.nen)) }
        val cum = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val dau = ImageView(this).apply {
            setImageResource(R.drawable.logo_dau)
            adjustViewBounds = true
            contentDescription = getString(R.string.app_name)
        }
        val chu = TextView(this).apply {
            text = getString(R.string.logo_flowy)
            textSize = 34f
            includeFontPadding = false
            typeface = GiaoDien.font(this@KhoiDongActivity, true) ?: android.graphics.Typeface.DEFAULT_BOLD
            setTextColor(mau(R.color.chu))
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }
        val chuX = TextView(this).apply {
            text = getString(R.string.logo_x)
            textSize = 34f
            includeFontPadding = false
            typeface = chu.typeface
            setTextColor(mau(R.color.cam))
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }
        cum.addView(dau, LinearLayout.LayoutParams(dp(46), dp(46)).apply { marginEnd = dp(10) })
        cum.addView(chu)
        cum.addView(chuX)
        goc.addView(cum, FrameLayout.LayoutParams(-2, -2, Gravity.CENTER))
        setContentView(goc)

        val nhanh = heSoHieuUng() == 0f
        if (nhanh) {
            di()
        } else {
            // Bat dau: dau logo nam giua man hinh, chu chua hien.
            chu.alpha = 0f; chuX.alpha = 0f
            val lech = dp(58).toFloat()
            dau.translationX = lech
            chu.translationX = lech
            chuX.translationX = lech
            dau.animate().translationX(0f).setDuration(420)
                .setInterpolator(AccelerateDecelerateInterpolator()).start()
            for (v in listOf(chu, chuX)) {
                v.animate().translationX(0f).alpha(1f).setStartDelay(140).setDuration(420)
                    .setInterpolator(AccelerateDecelerateInterpolator()).start()
            }
            goc.postDelayed({ di() }, 620)
        }
    }

    private fun heSoHieuUng(): Float = try {
        android.provider.Settings.Global.getFloat(
            contentResolver, android.provider.Settings.Global.ANIMATOR_DURATION_SCALE, 1f)
    } catch (_: Exception) { 1f }

    private fun di() {
        val lop = when {
            AppSettings(this).ngonNgu.isBlank() && !daChonNgonNgu() -> ChonNgonNguActivity::class.java
            KhoDuLieu(this).nguoiDau() == null -> DangKyActivity::class.java
            TaiKhoan.dangDangNhap(this) == null -> DangNhapActivity::class.java
            else -> ViecCanLamActivity::class.java
        }
        startActivity(Intent(this, lop))
        overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out)
        finish()
    }

    private fun daChonNgonNgu(): Boolean =
        getSharedPreferences("wayfinding", Context.MODE_PRIVATE).contains("da_chon_ngon_ngu")

    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)
}
