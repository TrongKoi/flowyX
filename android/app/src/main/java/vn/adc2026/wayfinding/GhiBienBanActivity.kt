package vn.adc2026.wayfinding

import android.app.Activity
import android.graphics.Typeface
import android.os.Bundle
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView

/**
 * GHI BIEN BAN TAY - duong du phong khi khong co tep ghi am (v4).
 *
 * Nam o, chi o ten la bat buoc. "Viec can lam" moi dong mot viec - viet
 * "Minh: gui bao gia truoc thu 6" la du, khong bat chon nguoi va ngay.
 */
class GhiBienBanActivity : Activity() {

    /** Ngon ngu: xem NgonNgu.boc. Theo may thi khong tao context moi. */
    override fun attachBaseContext(moi: android.content.Context) {
        super.attachBaseContext(NgonNgu.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        setContentView(R.layout.man_con)
        ThanhTieuDe.noiCon(this, getString(R.string.bb_ghi_tay))
        val k = findViewById<LinearLayout>(R.id.noi_dung_con)

        val oTen = o(k, R.string.bb_o_ten, R.string.bb_hint_ten, false)
        val tvLoi = TextView(this).apply {
            text = getString(R.string.bb_hint_ten); textSize = 13f; visibility = View.GONE
            setTextColor(mau(R.color.chu)); setPadding(0, dp(4), 0, 0)
        }
        k.addView(tvLoi)
        val oNguoi = o(k, R.string.bb_o_nguoi, R.string.bb_hint_nguoi, false)
        val oChot = o(k, R.string.bb_o_chot, R.string.bb_hint_chot, true)
        val oViec = o(k, R.string.bb_o_viec, R.string.bb_hint_viec, true)
        val oHoi = o(k, R.string.bb_o_hoi, R.string.bb_hint_hoi, true)

        findViewById<TextView>(R.id.nut_duoi_con).apply {
            visibility = View.VISIBLE
            text = getString(R.string.bb_luu)
            setOnClickListener {
                val so = SoBienBan.doc(this@GhiBienBanActivity)
                val ok = so.themBan(SoBienBan.BienBan(
                    luc = System.currentTimeMillis(),
                    ten = oTen.text.toString(),
                    daChot = oChot.text.toString(),
                    viec = oViec.text.toString().split("\n"),
                    nguoiDu = oNguoi.text.toString().split(",", "\n"),
                    cauHoi = oHoi.text.toString().split("\n"),
                ))
                if (!ok) { tvLoi.visibility = View.VISIBLE; oTen.requestFocus(); return@setOnClickListener }
                so.luu(this@GhiBienBanActivity)
                Rung.xong(it)
                finish()
            }
        }
        GiaoDien.apFont(findViewById(android.R.id.content), this)
    }

    private fun o(k: LinearLayout, nhan: Int, goiY: Int, nhieuDong: Boolean): EditText {
        k.addView(TextView(this).apply {
            text = getString(nhan); textSize = 15f; typeface = Typeface.DEFAULT_BOLD
            setTextColor(mau(R.color.chu))
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(18) })
        val e = EditText(this).apply {
            hint = getString(goiY); textSize = 16f
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_SENTENCES or
                (if (nhieuDong) InputType.TYPE_TEXT_FLAG_MULTI_LINE else 0)
            if (nhieuDong) { minLines = 3; gravity = Gravity.TOP or Gravity.START }
            setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
            background = getDrawable(R.drawable.o_nhap)
            minHeight = dp(52); setPadding(dp(14), dp(12), dp(14), dp(12))
            setLineSpacing(0f, 1.3f)
        }
        k.addView(e, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(6) })
        return e
    }

    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)
}
