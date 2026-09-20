package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/**
 * ====================================================================
 * DIEU KHOAN SU DUNG / CHINH SACH RIENG TU
 * ====================================================================
 *
 * Van ban nam trong res/raw (raw-en cho ban tieng Anh), khong nam trong
 * strings.xml. Ly do: hai tai lieu nay dai vai nghin tu, va nhet chung
 * vao strings.xml se bat moi nguoi dich phai cuon qua chung de tim mot
 * nhan nut. Tach ra thi nguoi soan luat sua tep cua ho, nguoi dich sua
 * tep cua minh.
 *
 * ----- Vi sao KHONG dung WebView -----
 *
 * WebView keo theo mot engine trinh duyet chi de hien chu den tren nen
 * trang: nang, cham mo, va tu doi mau chu theo che do toi rat te (chu
 * den tren nen den). O day tep la van ban thuan voi vai dau hieu dinh
 * dang don gian, dung ra bang TextView - nen dung mau cua app, dung
 * font cua nguoi dung chon, va dung co chu ho keo trong Cai dat.
 *
 * Cu phap trong tep:
 *   "# "  tieu de muc
 *   "## " tieu de nho
 *   "- "  gach dau dong
 *   ""    dong trong = het doan
 */
class PhapLyActivity : Activity() {

    companion object {
        const val PHAN = "phan"
        const val DIEU_KHOAN = "dieu_khoan"
        const val RIENG_TU = "rieng_tu"
    }

    override fun attachBaseContext(moi: Context) {
        super.attachBaseContext(GiaoDien.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)

        val rieng = intent.getStringExtra(PHAN) == RIENG_TU
        val tep = if (rieng) R.raw.chinh_sach_rieng_tu else R.raw.dieu_khoan_su_dung
        val tenMan = getString(if (rieng) R.string.pl_rieng_tu else R.string.pl_dieu_khoan)

        val goc = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(22), dp(18), dp(22), dp(40))
        }

        // Hang dau: nut quay lai + ten man hinh.
        goc.addView(LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            addView(ImageView(this@PhapLyActivity).apply {
                setImageResource(R.drawable.ic_quay_lai)
                setColorFilter(mau(R.color.chu_phu))
                val p = dp(8); setPadding(p, p, p, p)
                contentDescription = getString(R.string.quay_lai)
                background = GradientDrawable().apply {
                    shape = GradientDrawable.OVAL; setColor(mau(R.color.the))
                }
                setOnClickListener { Rung.nhe(it); finish() }
            }, LinearLayout.LayoutParams(dp(40), dp(40)).apply { marginEnd = dp(14) })
            addView(TextView(this@PhapLyActivity).apply {
                text = tenMan
                textSize = 19f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(mau(R.color.chu))
                if (android.os.Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
            }, LinearLayout.LayoutParams(-1, -2))
        }, LinearLayout.LayoutParams(-1, -2))

        for (v in dung(docTep(tep))) goc.addView(v)

        val cuon = ScrollView(this).apply {
            setBackgroundColor(mau(R.color.nen)); isFillViewport = true
        }
        cuon.addView(goc)
        setContentView(cuon)
        GiaoDien.apFont(goc, this)
    }

    private fun docTep(id: Int): List<String> =
        resources.openRawResource(id).bufferedReader().use { it.readLines() }

    /** Doi cac dong van ban thanh TextView, gop cac dong lien nhau thanh doan. */
    private fun dung(dong: List<String>): List<View> {
        val ra = ArrayList<View>()
        val dem = StringBuilder()

        fun xaDoan() {
            if (dem.isEmpty()) return
            ra.add(doan(dem.toString().trim()))
            dem.setLength(0)
        }

        for (d in dong) {
            val t = d.trim()
            when {
                t.isEmpty() -> xaDoan()
                t.startsWith("## ") -> { xaDoan(); ra.add(tieuDeNho(t.substring(3))) }
                t.startsWith("# ") -> { xaDoan(); ra.add(tieuDeMuc(t.substring(2))) }
                t.startsWith("- ") -> { xaDoan(); ra.add(gach(t.substring(2))) }
                else -> { if (dem.isNotEmpty()) dem.append(' '); dem.append(t) }
            }
        }
        xaDoan()
        return ra
    }

    private fun tieuDeMuc(s: String) = TextView(this).apply {
        text = s
        textSize = 17f
        typeface = Typeface.DEFAULT_BOLD
        setTextColor(mau(R.color.chu))
        if (android.os.Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
        layoutParams = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(26) }
    }

    private fun tieuDeNho(s: String) = TextView(this).apply {
        text = s
        textSize = 14.5f
        typeface = Typeface.DEFAULT_BOLD
        setTextColor(mau(R.color.chu))
        if (android.os.Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
        layoutParams = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(18) }
    }

    private fun doan(s: String) = TextView(this).apply {
        text = s
        textSize = 14f
        setLineSpacing(0f, 1.55f)
        setTextColor(mau(R.color.chu_phu))
        layoutParams = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10) }
    }

    private fun gach(s: String) = LinearLayout(this).apply {
        orientation = LinearLayout.HORIZONTAL
        addView(TextView(this@PhapLyActivity).apply {
            text = "•"
            textSize = 14f
            setTextColor(mau(R.color.cam))
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }, LinearLayout.LayoutParams(dp(18), -2))
        addView(TextView(this@PhapLyActivity).apply {
            text = s
            textSize = 14f
            setLineSpacing(0f, 1.5f)
            setTextColor(mau(R.color.chu_phu))
        }, LinearLayout.LayoutParams(-1, -2))
        layoutParams = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(7) }
    }

    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)
}
