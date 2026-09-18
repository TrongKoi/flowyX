package vn.adc2026.wayfinding

import android.app.Activity
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.View
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView

/**
 * THANH HOAN TAC - hien 5 giay o day man hinh, ngay tren thanh tab.
 *
 * Thay cho hop thoai "Ban co chac muon xoa?". Hop thoai chen mot buoc vao
 * GIUA moi lan xoa dung; hoan tac chi ton them mot buoc cho lan xoa NHAM.
 *
 * Khong dung Snackbar (thuoc Material Components, can androidx). Tu dung
 * mot khoi va gan vao `android.R.id.content` - la FrameLayout o moi Activity.
 */
object HoanTac {

    private val tay = Handler(Looper.getMainLooper())
    private var dangHien: View? = null
    private var an: Runnable? = null

    fun hien(a: Activity, loiBao: String, cachDay: Int = 72, khiHoanTac: () -> Unit) {
        val goc = a.findViewById<FrameLayout>(android.R.id.content) ?: return
        dong()
        val d = a.resources.displayMetrics.density
        fun dp(n: Int) = (n * d).toInt()

        val thanh = LinearLayout(a).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(18), dp(6), dp(6), dp(6))
            background = GradientDrawable().apply {
                cornerRadius = dp(14).toFloat()
                setColor(a.resources.getColor(R.color.chu, a.theme))
            }
            elevation = dp(6).toFloat()
            accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_POLITE
        }
        thanh.addView(TextView(a).apply {
            text = loiBao
            textSize = 14f
            setTextColor(a.resources.getColor(R.color.nen, a.theme))
            maxLines = 2
        }, LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f))
        thanh.addView(TextView(a).apply {
            text = a.getString(R.string.hoan_tac)
            textSize = 14f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(a.resources.getColor(R.color.nhan, a.theme))
            gravity = Gravity.CENTER
            minHeight = dp(44); minWidth = dp(88)
            background = a.getDrawable(android.R.drawable.list_selector_background)
            setOnClickListener { dong(); khiHoanTac() }
        })
        GiaoDien.apFont(thanh, a)
        goc.addView(thanh, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT,
            Gravity.BOTTOM).apply { setMargins(dp(12), 0, dp(12), dp(cachDay)) })
        dangHien = thanh
        an = Runnable { dong() }.also { tay.postDelayed(it, 5000) }
    }

    fun dong() {
        an?.let(tay::removeCallbacks)
        dangHien?.let { (it.parent as? FrameLayout)?.removeView(it) }
        dangHien = null
    }
}

/**
 * THONG BAO NGAN trong app - thay cho Toast.
 *
 * Tu Android 11, Toast chu do SystemUI ve bang font he thong: app KHONG doi
 * duoc sang Lexend. Mot dong bao ngan trong chinh cua so app thi doi duoc,
 * va doc duoc bang TalkBack (live region).
 */
object ThongBao {
    private val tay = Handler(Looper.getMainLooper())
    private var dangHien: View? = null

    fun hien(a: Activity, loiBao: String, cachDay: Int = 72) {
        val goc = a.findViewById<FrameLayout>(android.R.id.content) ?: return
        dangHien?.let { (it.parent as? FrameLayout)?.removeView(it) }
        val d = a.resources.displayMetrics.density
        val tv = TextView(a).apply {
            text = loiBao
            textSize = 14f
            setTextColor(a.resources.getColor(R.color.nen, a.theme))
            setPadding((18 * d).toInt(), (13 * d).toInt(), (18 * d).toInt(), (13 * d).toInt())
            background = GradientDrawable().apply {
                cornerRadius = 14 * d
                setColor(a.resources.getColor(R.color.chu, a.theme))
            }
            elevation = 6 * d
            accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_POLITE
        }
        GiaoDien.apFont(tv, a)
        goc.addView(tv, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT,
            Gravity.BOTTOM).apply {
            setMargins((12 * d).toInt(), 0, (12 * d).toInt(), (cachDay * d).toInt())
        })
        dangHien = tv
        tay.postDelayed({ (tv.parent as? FrameLayout)?.removeView(tv); if (dangHien === tv) dangHien = null }, 2500)
    }
}
