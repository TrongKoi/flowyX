package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.os.Bundle
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView

/**
 * VIET NHAT KY - trang giay trong, toan man hinh (v4).
 *
 * Ban cu la hop thoai ba dong. Hop thoai noi "viet it thoi" va de bi dong
 * mat khi cham nham ra ngoai - mat het chu vua viet.
 *
 * Trang nay chi co: mui ten quay lai, chu "Xong", va mot o viet chiem het
 * man hinh. Khong thanh tab, khong logo, khong dem chu. Chu 18sp, gian dong
 * 1.5 - de doc lai cai minh vua viet.
 *
 * KHONG MAT CHU: moi lan go deu luu nhap. Quay lai bang mui ten, nut Back,
 * hay bi goi dien giua chung - chu van con, va Xong/Quay lai deu LUU (khong
 * co cau "Bo thay doi?"). Muon bo thi xoa chu, hoac vuot xoa o danh sach.
 *
 * "Ban thay the nao?" nam DUOI o viet va tuy chon - viet truoc, dat ten cam
 * xuc sau (neu muon), khong bat nguoi dung phan loai minh truoc khi viet.
 */
class VietNhatKyActivity : Activity() {

    private lateinit var oTieuDe: EditText
    private lateinit var oViet: EditText
    private lateinit var oTheNao: EditText
    private var luc: Long = -1L

    /** Ngon ngu: xem NgonNgu.boc. Theo may thi khong tao context moi. */
    override fun attachBaseContext(moi: android.content.Context) {
        super.attachBaseContext(GiaoDien.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE or
            WindowManager.LayoutParams.SOFT_INPUT_STATE_VISIBLE)
        setContentView(R.layout.man_con)
        luc = intent.getLongExtra(THEM_LUC, -1L)
        val cu = if (luc > 0) SoNhatKy.doc(this).muc.firstOrNull { it.luc == luc } else null

        ThanhTieuDe.noiCon(this, getString(if (cu == null) R.string.nk_viet_moi else R.string.nk_sua)) { xong() }
        ThanhTieuDe.nutPhai(this, getString(R.string.xong)) { xong() }

        val khoi = findViewById<LinearLayout>(R.id.noi_dung_con)
        val p = prefs()
        khoi.addView(TextView(this).apply {
            text = java.text.SimpleDateFormat("EEEE, dd/MM/yyyy", java.util.Locale("vi", "VN"))
                .format(java.util.Date(if (cu != null) cu.luc else System.currentTimeMillis()))
                .replaceFirstChar { it.uppercase() }
            textSize = 13f; setTextColor(mau(R.color.chu_phu))
        })
        // Tieu de mot dong, o tren. Tach hai truong de danh sach co mot
        // dong dam nhan ra ngay; tim lai ban ghi cu nhanh hon nhieu so voi
        // doc trich doan. Van bo trong duoc.
        oTieuDe = EditText(this).apply {
            hint = getString(R.string.nk_hint_tieu_de)
            setText(cu?.tieuDe ?: if (luc <= 0) prefs().getString(K_TIEU_DE, "") else "")
            textSize = 21f
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            maxLines = 1
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
            setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
            background = null
            setPadding(0, dp(10), 0, dp(6))
        }
        khoi.addView(oTieuDe, LinearLayout.LayoutParams(-1, -2))
        khoi.addView(View(this).apply { setBackgroundColor(mau(R.color.vien)) },
            LinearLayout.LayoutParams(-1, dp(1)))

        oViet = EditText(this).apply {
            hint = getString(R.string.hint_ghi_chu)
            setText(cu?.noiDung ?: if (luc <= 0) p.getString(K_NHAP, "") else "")
            textSize = 18f
            setLineSpacing(0f, 1.5f)
            gravity = Gravity.TOP or Gravity.START
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE or
                InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
            setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
            background = null
            setPadding(0, dp(12), 0, dp(12))
            minHeight = (resources.displayMetrics.heightPixels * 0.55f).toInt()
        }
        khoi.addView(oViet, LinearLayout.LayoutParams(-1, -2))

        khoi.addView(View(this).apply { setBackgroundColor(mau(R.color.vien)) },
            LinearLayout.LayoutParams(-1, dp(1)))
        oTheNao = EditText(this).apply {
            hint = getString(R.string.hint_the_nao)
            setText(cu?.theNao ?: if (luc <= 0) p.getString(K_THE_NAO, "") else "")
            textSize = 15f
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
            setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
            background = null
            minHeight = dp(52)
        }
        khoi.addView(oTheNao, LinearLayout.LayoutParams(-1, -2))

        // Dong chan: noi ro du lieu nay nam o dau. Nguoi dung viet cam xuc
        // vao day can biet dieu do TRUOC khi viet, khong phai trong muc
        // Chinh sach nao do.
        khoi.addView(LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(18), 0, dp(4))
            addView(ImageView(this@VietNhatKyActivity).apply {
                setImageResource(R.drawable.ic_khoa)
                setColorFilter(mau(R.color.chu_phu))
                importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            }, LinearLayout.LayoutParams(dp(14), dp(14)).apply { marginEnd = dp(7) })
            addView(TextView(this@VietNhatKyActivity).apply {
                text = getString(R.string.nk_o_lai_may)
                textSize = 12f
                setTextColor(mau(R.color.chu_phu))
                setLineSpacing(0f, 1.35f)
            }, LinearLayout.LayoutParams(0, -2, 1f))
        }, LinearLayout.LayoutParams(-1, -2))

        GiaoDien.apFont(findViewById(android.R.id.content), this)
        oViet.requestFocus()
        oViet.setSelection(oViet.text.length)
    }

    override fun onPause() {
        super.onPause()
        // Nhap chi cho muc MOI. Muc dang sua thi luu thang khi Xong.
        if (luc <= 0 && !isFinishing) {
            prefs().edit().putString(K_TIEU_DE, oTieuDe.text.toString())
                .putString(K_NHAP, oViet.text.toString())
                .putString(K_THE_NAO, oTheNao.text.toString()).apply()
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() = xong()

    private fun xong() {
        val nd = oViet.text.toString()
        val tn = oTheNao.text.toString().ifBlank { null }
        val so = SoNhatKy.doc(this)
        val td = oTieuDe.text.toString()
        val daLuu = if (luc > 0) so.sua(luc, nd, tn, td) else so.ghi(nd, tn, td)
        if (daLuu) {
            so.luu(this)
            findViewById<View>(android.R.id.content)?.let { Rung.xong(it) }
        }
        if (luc <= 0) prefs().edit().remove(K_NHAP).remove(K_THE_NAO).remove(K_TIEU_DE).apply()
        finish()
    }

    private fun prefs() = getSharedPreferences("flowy_nhat_ky_nhap", Context.MODE_PRIVATE)
    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)

    companion object {
        const val THEM_LUC = "luc"
        private const val K_NHAP = "nhap"
        private const val K_TIEU_DE = "tieu_de"
        private const val K_THE_NAO = "the_nao"
    }
}
