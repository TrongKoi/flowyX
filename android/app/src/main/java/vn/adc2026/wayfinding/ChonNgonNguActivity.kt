package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView

/**
 * CHON NGON NGU - man hinh dau tien, chi hien MOT LAN.
 *
 * Mot quyet dinh, hai lua chon, khong co nut "Bỏ qua". Bo qua o day chi
 * de danh mot cau hoi sang man hinh khac; hai co tiếng Việt va English de
 * ai cung nhan ra ma khong can doc.
 *
 * Doi lai bat cu luc nao trong Cai dat → Hệ thống & Trợ năng.
 */
class ChonNgonNguActivity : Activity() {

    private var chon = ""

    override fun attachBaseContext(moi: Context) {
        super.attachBaseContext(GiaoDien.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        chon = AppSettings(this).ngonNgu.ifBlank {
            if (java.util.Locale.getDefault().language == "vi") NgonNgu.VIET else NgonNgu.ANH
        }
        ve()
    }

    private fun ve() {
        val goc = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(mau(R.color.nen))
            setPadding(dp(24), dp(40), dp(24), dp(28))
        }
        goc.addView(ImageView(this).apply {
            setImageResource(R.drawable.logo_ngang)
            adjustViewBounds = true
            contentDescription = getString(R.string.app_name)
        }, LinearLayout.LayoutParams(-2, dp(26)))

        goc.addView(TextView(this).apply {
            text = "Chọn ngôn ngữ"
            textSize = 25f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(mau(R.color.chu))
            if (android.os.Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(34) })
        goc.addView(TextView(this).apply {
            text = "Choose your language"
            textSize = 15f
            setTextColor(mau(R.color.chu_phu))
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(4) })

        for ((ma, ten, co) in listOf(
            Triple(NgonNgu.VIET, "Tiếng Việt", "🇻🇳"),
            Triple(NgonNgu.ANH, "English", "🇬🇧"))) {
            val dangChon = chon == ma
            goc.addView(LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                minimumHeight = dp(64)
                setPadding(dp(16), dp(10), dp(16), dp(10))
                background = GradientDrawable().apply {
                    cornerRadius = dp(18).toFloat()
                    setColor(mau(if (dangChon) R.color.nhan_nhat else R.color.the))
                    setStroke(dp(if (dangChon) 2 else 1),
                        mau(if (dangChon) R.color.nhan_vien else R.color.vien))
                }
                isClickable = true
                setOnClickListener { Rung.nhe(it); chon = ma; ve() }
                addView(TextView(this@ChonNgonNguActivity).apply {
                    text = co; textSize = 22f; includeFontPadding = false
                    importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
                }, LinearLayout.LayoutParams(-2, -2).apply { marginEnd = dp(14) })
                addView(TextView(this@ChonNgonNguActivity).apply {
                    text = ten; textSize = 17f
                    setTextColor(mau(R.color.chu))
                    typeface = if (dangChon) Typeface.DEFAULT_BOLD else Typeface.DEFAULT
                }, LinearLayout.LayoutParams(0, -2, 1f))
                if (dangChon) addView(ImageView(this@ChonNgonNguActivity).apply {
                    setImageResource(R.drawable.ic_tick)
                    setColorFilter(mau(R.color.cam))
                }, LinearLayout.LayoutParams(dp(22), dp(22)))
                contentDescription = ten + if (dangChon) ", đang chọn" else ""
            }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(14) })
        }

        goc.addView(View(this), LinearLayout.LayoutParams(-1, 0, 1f))
        goc.addView(TextView(this).apply {
            text = if (chon == NgonNgu.VIET) "Tiếp tục" else "Continue"
            textSize = 17f
            gravity = Gravity.CENTER
            typeface = Typeface.DEFAULT_BOLD
            minHeight = dp(54)
            includeFontPadding = false
            setTextColor(mau(R.color.chu_tren_nhan))
            background = getDrawable(R.drawable.nut_chinh)
            setOnClickListener {
                Rung.xong(it)
                AppSettings(this@ChonNgonNguActivity).ngonNgu = chon
                getSharedPreferences("wayfinding", Context.MODE_PRIVATE)
                    .edit().putBoolean("da_chon_ngon_ngu", true).apply()
                startActivity(Intent(this@ChonNgonNguActivity, DangKyActivity::class.java))
                finish()
            }
        }, LinearLayout.LayoutParams(-1, -2))
        goc.addView(TextView(this).apply {
            text = if (chon == NgonNgu.VIET) "Đổi lại bất cứ lúc nào trong Cài đặt."
                   else "You can change this any time in Settings."
            textSize = 12.5f
            gravity = Gravity.CENTER
            setTextColor(mau(R.color.chu_phu))
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(12) })

        setContentView(goc)
        GiaoDien.apFont(goc, this)
    }

    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)
}
