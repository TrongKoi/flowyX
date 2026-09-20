package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.graphics.Typeface
import android.os.Bundle
import android.text.InputType
import android.text.method.PasswordTransformationMethod
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView

/**
 * ====================================================================
 * DANG NHAP (v5)
 * ====================================================================
 *
 * Hai o, mot nut. Tai khoan nay KHOA APP tren may nay - khong dong bo,
 * khong gui gi len may chu. Dong chu duoi cung noi thang dieu do, vi
 * nguoi dung co quyen biet truoc khi go bat cu thu gi.
 *
 * ----- Nut hien mat khau: GIU de xem -----
 *
 * Bam mot lan de hien roi bam lai de an la hai thao tac, va de quen o
 * trang thai "dang hien" giua cho dong nguoi. O day: GIU ngon tay thi
 * hien, tha ra la an lai - mot thao tac, khong the quen. Van co
 * `contentDescription` de TalkBack doc duoc.
 *
 * ----- Nhap sai nhieu lan -----
 *
 * Khong khoa han tai khoan. Nguoi ADHD go nham mat khau nhieu lan la
 * chuyen thuong, va day la may CUA HO - khoa han se bien mot lan lo dang
 * thanh mat sach nhat ky. Sau 5 lan sai thi phai cho, thoi gian cho tang
 * gap doi (xem `TaiKhoan.ghiNhanSai`).
 */
class DangNhapActivity : Activity() {

    private lateinit var oEmail: EditText
    private lateinit var oMatKhau: EditText
    private lateinit var tvLoi: TextView

    override fun attachBaseContext(moi: Context) {
        super.attachBaseContext(GiaoDien.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        val cuon = android.widget.ScrollView(this).apply {
            setBackgroundColor(mau(R.color.nen)); isFillViewport = true
        }
        val goc = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(24), dp(30), dp(24), dp(26))
        }

        goc.addView(ImageView(this).apply {
            setImageResource(R.drawable.logo_ngang)
            adjustViewBounds = true
            contentDescription = getString(R.string.app_name)
        }, LinearLayout.LayoutParams(-2, dp(26)).apply { gravity = Gravity.CENTER_HORIZONTAL })

        goc.addView(TextView(this).apply {
            text = getString(R.string.dn_chao)
            textSize = 24f
            gravity = Gravity.CENTER
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(mau(R.color.chu))
            if (android.os.Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(28) })
        goc.addView(TextView(this).apply {
            text = getString(R.string.dn_phu)
            textSize = 13.5f
            gravity = Gravity.CENTER
            setTextColor(mau(R.color.chu_phu))
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(6) })

        goc.addView(nhan(getString(R.string.dk_email)), lp(24))
        oEmail = oNhap(getString(R.string.dk_hint_email),
            InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS)
        goc.addView(oEmail, lp(6))

        goc.addView(nhan(getString(R.string.dk_mat_khau)), lp(16))
        goc.addView(oMatKhauCoMat(), lp(6))

        tvLoi = TextView(this).apply {
            textSize = 13f
            setTextColor(mau(R.color.do_xoa))
            visibility = View.GONE
            accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_ASSERTIVE
        }
        goc.addView(tvLoi, lp(8))

        goc.addView(TextView(this).apply {
            text = getString(R.string.dn_quen)
            textSize = 13.5f
            gravity = Gravity.END
            typeface = Typeface.DEFAULT_BOLD
            minHeight = dp(44)
            setTextColor(mau(R.color.chu_lien_ket))
            setOnClickListener {
                Rung.nhe(it)
                startActivity(Intent(this@DangNhapActivity, QuenMatKhauActivity::class.java))
            }
        }, lp(4))

        goc.addView(nutChinh(getString(R.string.dn_nut)) { thu() }, lp(10))

        goc.addView(TextView(this).apply {
            text = getString(R.string.dn_chua_co)
            textSize = 13.5f
            gravity = Gravity.CENTER
            minHeight = dp(44)
            setTextColor(mau(R.color.chu_lien_ket))
            setOnClickListener {
                Rung.nhe(it)
                startActivity(Intent(this@DangNhapActivity, DangKyActivity::class.java))
            }
        }, lp(14))

        goc.addView(View(this), LinearLayout.LayoutParams(-1, 0, 1f))
        goc.addView(TextView(this).apply {
            text = getString(R.string.dn_rieng_tu)
            textSize = 12f
            gravity = Gravity.CENTER
            setLineSpacing(0f, 1.45f)
            setTextColor(mau(R.color.chu_phu))
        }, lp(20))

        cuon.addView(goc)
        setContentView(cuon)
        GiaoDien.apFont(goc, this)
    }

    /** O mat khau + nut con mat: GIU de hien, tha ra la an. */
    private fun oMatKhauCoMat(): View {
        val hang = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            background = getDrawable(R.drawable.o_nhap)
        }
        oMatKhau = EditText(this).apply {
            hint = getString(R.string.dk_hint_mat_khau)
            textSize = 16f
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
            transformationMethod = PasswordTransformationMethod.getInstance()
            setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
            background = null
            minHeight = dp(54)
            setPadding(dp(14), 0, dp(6), 0)
        }
        hang.addView(oMatKhau, LinearLayout.LayoutParams(0, -2, 1f))
        hang.addView(ImageView(this).apply {
            setImageResource(R.drawable.ic_mat)
            setColorFilter(mau(R.color.chu_phu))
            val p = dp(13); setPadding(p, p, p, p)
            contentDescription = getString(R.string.dk_giu_de_hien)
            setOnTouchListener { v, e ->
                when (e.actionMasked) {
                    MotionEvent.ACTION_DOWN -> {
                        oMatKhau.transformationMethod = null
                        (v as ImageView).setImageResource(R.drawable.ic_mat_tat)
                        oMatKhau.setSelection(oMatKhau.text.length)
                        true
                    }
                    MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                        oMatKhau.transformationMethod = PasswordTransformationMethod.getInstance()
                        (v as ImageView).setImageResource(R.drawable.ic_mat)
                        oMatKhau.setSelection(oMatKhau.text.length)
                        v.performClick()
                        true
                    }
                    else -> false
                }
            }
        }, LinearLayout.LayoutParams(dp(50), dp(50)))
        return hang
    }

    private fun thu() {
        val cho = TaiKhoan.conPhaiCho(this)
        if (cho > 0) {
            loi(getString(R.string.dn_cho_giay, (cho / 1000 + 1).toInt()))
            return
        }
        val e = oEmail.text.toString().trim()
        val mk = oMatKhau.text.toString()
        if (e.isEmpty() || mk.isEmpty()) { loi(getString(R.string.dn_thieu)); return }

        // Bam mat khau ton 200-400 ms: chay o luong nen de giao dien khong dung.
        val nut = findViewById<View>(android.R.id.content)
        Thread {
            val nd = KhoDuLieu(this).dangNhap(e, mk)
            runOnUiThread {
                if (nd == null) {
                    TaiKhoan.ghiNhanSai(this)
                    loi(getString(R.string.dn_sai))
                } else {
                    TaiKhoan.ghiNhanDung(this)
                    TaiKhoan.ghiPhien(this, nd)
                    Rung.xong(nut)
                    startActivity(Intent(this, ViecCanLamActivity::class.java))
                    finish()
                }
            }
        }.start()
    }

    private fun loi(s: String) {
        tvLoi.text = s
        tvLoi.visibility = View.VISIBLE
    }

    // --- khuon nho ---

    private fun oNhap(goiY: String, kieu: Int) = EditText(this).apply {
        hint = goiY
        textSize = 16f
        inputType = kieu
        setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
        background = getDrawable(R.drawable.o_nhap)
        minHeight = dp(54)
        setPadding(dp(14), 0, dp(14), 0)
    }

    private fun nhan(s: String) = TextView(this).apply {
        text = s; textSize = 11.5f; typeface = Typeface.DEFAULT_BOLD
        letterSpacing = 0.05f
        setTextColor(mau(R.color.chu_phu))
    }

    private fun nutChinh(s: String, khi: () -> Unit) = TextView(this).apply {
        text = s; textSize = 17f; gravity = Gravity.CENTER
        typeface = Typeface.DEFAULT_BOLD
        minHeight = dp(54); includeFontPadding = false
        setTextColor(mau(R.color.chu_tren_nhan))
        background = getDrawable(R.drawable.nut_chinh)
        setOnClickListener { Rung.nhe(it); khi() }
    }

    private fun lp(tren: Int) = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(tren) }
    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)
}
