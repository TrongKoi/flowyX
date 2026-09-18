package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.text.Editable
import android.text.InputType
import android.text.TextWatcher
import android.text.method.PasswordTransformationMethod
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/**
 * ====================================================================
 * DANG KY (v5)
 * ====================================================================
 *
 * Mot Activity, HAI BUOC:
 *
 *   buoc 0 - bieu mau (ho ten, Gmail, mat khau, xac nhan, dien thoai)
 *   buoc 1 - MA KHOI PHUC hien mot lan duy nhat
 *
 * Buoc 1 khong tach ra Activity rieng, va nut Back bi chan o do. Ly do:
 * ma khoi phuc la duong DUY NHAT lay lai tai khoan khi quen mat khau
 * (khong co may chu de gui email dat lai - xem docs/BAO_MAT.md §4). Neu
 * nguoi dung lo tay thoat, tai khoan van ton tai nhung khong con duong
 * cuu - nen man hinh nay bat ho bam "Toi da luu ma" moi di tiep.
 *
 * ----- Vi sao khong gui email xac thuc? -----
 *
 * Gui email can khoa SMTP, ma khoa nam trong APK thi ai giai nen APK
 * cung doc duoc. Flowy chay hoan toan tren may, nen "Gmail" o day chi la
 * DINH DANH (khoa tai khoan tren may nay), khong phai kenh lien lac.
 * Dong chu duoi cung noi thang dieu do de khong ai hieu nham.
 *
 * ----- Do manh mat khau -----
 *
 * Thanh do manh KHONG CHAN nguoi dung. Toi thieu 8 ky tu (OWASP), con
 * lai chi la goi y mau sac. Chan them dieu kien (phai co so, phai co ky
 * tu dac biet) chi day nguoi ta toi "Matkhau123!" - de doan hon mot cau
 * bon chu ngau nhien, va kho nho hon nhieu.
 */
class DangKyActivity : Activity() {

    private var buoc = 0
    private var maKhoiPhuc = ""

    private lateinit var oTen: EditText
    private lateinit var oEmail: EditText
    private lateinit var oMatKhau: EditText
    private lateinit var oXacNhan: EditText
    private lateinit var oDienThoai: EditText
    private lateinit var tvLoi: TextView
    private lateinit var thanhManh: View
    private lateinit var tvManh: TextView
    private var dongY = false

    override fun attachBaseContext(moi: Context) {
        super.attachBaseContext(NgonNgu.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        veBieuMau()
    }

    override fun onBackPressed() {
        // Buoc ma khoi phuc: khong cho thoat bang Back (xem ghi chu dau file).
        if (buoc == 1) { Rung.nhe(window.decorView); return }
        super.onBackPressed()
    }

    // ================================================================
    // BUOC 0 - BIEU MAU
    // ================================================================

    private fun veBieuMau() {
        buoc = 0
        val goc = cot()

        goc.addView(ImageView(this).apply {
            setImageResource(R.drawable.logo_ngang)
            adjustViewBounds = true
            contentDescription = getString(R.string.app_name)
        }, LinearLayout.LayoutParams(-2, dp(26)).apply { gravity = Gravity.CENTER_HORIZONTAL })

        goc.addView(tieuDe(getString(R.string.dk_tieu_de)), lp(26))
        goc.addView(phu(getString(R.string.dk_phu)), lp(6))

        goc.addView(nhan(getString(R.string.dk_ho_ten)), lp(22))
        oTen = oNhap(getString(R.string.dk_hint_ho_ten),
            InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_WORDS)
        goc.addView(oTen, lp(6))

        goc.addView(nhan(getString(R.string.dk_email)), lp(14))
        oEmail = oNhap(getString(R.string.dk_hint_email),
            InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS)
        goc.addView(oEmail, lp(6))

        goc.addView(nhan(getString(R.string.dk_mat_khau)), lp(14))
        oMatKhau = EditText(this)
        goc.addView(oCoMat(oMatKhau, getString(R.string.dk_hint_mat_khau)), lp(6))
        goc.addView(veThanhManh(), lp(8))

        goc.addView(nhan(getString(R.string.dk_xac_nhan)), lp(14))
        oXacNhan = EditText(this)
        goc.addView(oCoMat(oXacNhan, getString(R.string.dk_hint_xac_nhan)), lp(6))

        goc.addView(nhan(getString(R.string.dk_dien_thoai)), lp(14))
        oDienThoai = oNhap(getString(R.string.dk_hint_dien_thoai), InputType.TYPE_CLASS_PHONE)
        goc.addView(oDienThoai, lp(6))

        goc.addView(veODongY(), lp(18))

        tvLoi = TextView(this).apply {
            textSize = 13f
            setLineSpacing(0f, 1.35f)
            setTextColor(mau(R.color.do_xoa))
            visibility = View.GONE
            accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_ASSERTIVE
        }
        goc.addView(tvLoi, lp(10))

        goc.addView(nutChinh(getString(R.string.dk_nut)) { thuTao() }, lp(14))

        goc.addView(TextView(this).apply {
            text = getString(R.string.dk_da_co)
            textSize = 13.5f
            gravity = Gravity.CENTER
            minHeight = dp(44)
            setTextColor(mau(R.color.chu_lien_ket))
            setOnClickListener {
                Rung.nhe(it)
                startActivity(Intent(this@DangKyActivity, DangNhapActivity::class.java))
                finish()
            }
        }, lp(12))

        goc.addView(TextView(this).apply {
            text = getString(R.string.dk_o_lai_may)
            textSize = 12f
            gravity = Gravity.CENTER
            setLineSpacing(0f, 1.45f)
            setTextColor(mau(R.color.chu_phu))
        }, lp(18))

        datNoiDung(goc)
    }

    /** Thanh do manh: mot vach mau + mot dong chu. Khong chan, chi goi y. */
    private fun veThanhManh(): View {
        val hang = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }
        thanhManh = View(this).apply {
            background = GradientDrawable().apply { cornerRadius = dp(3).toFloat() }
            visibility = View.INVISIBLE
        }
        hang.addView(thanhManh, LinearLayout.LayoutParams(dp(54), dp(5)).apply { marginEnd = dp(10) })
        tvManh = TextView(this).apply {
            textSize = 12f
            setTextColor(mau(R.color.chu_phu))
        }
        hang.addView(tvManh, LinearLayout.LayoutParams(-1, -2))

        oMatKhau.addTextChangedListener(object : TextWatcher {
            override fun afterTextChanged(s: Editable?) = capNhatManh(s?.toString() ?: "")
            override fun beforeTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}
            override fun onTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}
        })
        return hang
    }

    private fun capNhatManh(mk: String) {
        if (mk.isEmpty()) { thanhManh.visibility = View.INVISIBLE; tvManh.text = ""; return }
        val d = KhoDuLieu.doManh(mk)
        val m = when (d) { 0 -> R.color.do_xoa; 1 -> R.color.cam; else -> R.color.xanh_xong }
        val chu = when (d) {
            0 -> R.string.dk_manh_yeu
            1 -> R.string.dk_manh_vua
            else -> R.string.dk_manh_tot
        }
        thanhManh.visibility = View.VISIBLE
        (thanhManh.background as GradientDrawable).setColor(mau(m))
        thanhManh.layoutParams = (thanhManh.layoutParams as LinearLayout.LayoutParams).apply {
            width = dp(when (d) { 0 -> 30; 1 -> 54; else -> 78 })
        }
        thanhManh.requestLayout()
        tvManh.text = getString(chu)
    }

    /** O tich "dong y" + hai lien ket mo van ban phap ly. */
    private fun veODongY(): View {
        val hang = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            minimumHeight = dp(48)
        }
        val o = ImageView(this).apply {
            val p = dp(4); setPadding(p, p, p, p)
            setImageResource(R.drawable.ic_tick)
            setColorFilter(mau(R.color.chu_tren_nhan))
        }
        fun veO() {
            o.background = GradientDrawable().apply {
                cornerRadius = dp(7).toFloat()
                setColor(mau(if (dongY) R.color.nhan else android.R.color.transparent))
                setStroke(dp(2), mau(if (dongY) R.color.nhan else R.color.vien))
            }
            o.setImageResource(if (dongY) R.drawable.ic_tick else 0)
        }
        veO()
        hang.addView(o, LinearLayout.LayoutParams(dp(24), dp(24)).apply {
            topMargin = dp(2); marginEnd = dp(12)
        })

        val chu = TextView(this).apply {
            text = getString(R.string.dk_dong_y)
            textSize = 13.5f
            setLineSpacing(0f, 1.4f)
            setTextColor(mau(R.color.chu_phu))
        }
        hang.addView(chu, LinearLayout.LayoutParams(0, -2, 1f))

        hang.isClickable = true
        hang.setOnClickListener { Rung.nhe(it); dongY = !dongY; veO()
            hang.contentDescription = getString(R.string.dk_dong_y) +
                ", " + getString(if (dongY) R.string.da_chon else R.string.chua_chon)
        }
        hang.contentDescription = getString(R.string.dk_dong_y) +
            ", " + getString(R.string.chua_chon)

        val cot = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        cot.addView(hang, LinearLayout.LayoutParams(-1, -2))
        val hai = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        hai.addView(lienKet(getString(R.string.pl_dieu_khoan), PhapLyActivity.DIEU_KHOAN))
        hai.addView(TextView(this).apply {
            text = "  ·  "; textSize = 13f; setTextColor(mau(R.color.chu_phu))
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            minHeight = dp(40); gravity = Gravity.CENTER_VERTICAL
        })
        hai.addView(lienKet(getString(R.string.pl_rieng_tu), PhapLyActivity.RIENG_TU))
        cot.addView(hai, LinearLayout.LayoutParams(-1, -2).apply { marginStart = dp(36) })
        return cot
    }

    private fun lienKet(s: String, phan: String) = TextView(this).apply {
        text = s
        textSize = 13f
        typeface = Typeface.DEFAULT_BOLD
        minHeight = dp(40)
        gravity = Gravity.CENTER_VERTICAL
        setTextColor(mau(R.color.chu_lien_ket))
        paintFlags = paintFlags or android.graphics.Paint.UNDERLINE_TEXT_FLAG
        setOnClickListener {
            Rung.nhe(it)
            startActivity(Intent(this@DangKyActivity, PhapLyActivity::class.java)
                .putExtra(PhapLyActivity.PHAN, phan))
        }
    }

    // ================================================================
    // KIEM TRA VA TAO
    // ================================================================

    private fun thuTao() {
        val ten = oTen.text.toString().trim()
        val email = oEmail.text.toString().trim()
        val mk = oMatKhau.text.toString()
        val xn = oXacNhan.text.toString()
        val dt = oDienThoai.text.toString().trim()

        // Kiem tra theo THU TU TREN MAN HINH, va bao MOT loi mot luc.
        // Do het mot danh sach loi cung luc la cach nhanh nhat de nguoi
        // ta dong app - nhat la nguoi de nan long truoc bieu mau dai.
        val loi = when {
            ten.length < 2 -> getString(R.string.dk_loi_ten)
            !KhoDuLieu.emailHopLe(email) -> getString(R.string.dk_loi_email)
            mk.length < KhoDuLieu.TOI_THIEU ->
                getString(R.string.dk_loi_ngan, KhoDuLieu.TOI_THIEU)
            mk != xn -> getString(R.string.dk_loi_khac_nhau)
            !dongY -> getString(R.string.dk_loi_dong_y)
            else -> null
        }
        if (loi != null) { loi(loi); return }

        tvLoi.visibility = View.GONE
        val kho = KhoDuLieu(this)
        if (kho.coEmail(email)) { loi(getString(R.string.dk_loi_trung)); return }

        // Bam PBKDF2 210k vong ton 200-400 ms tren may tam trung: chay o
        // luong nen, neu khong ANR watchdog co the ban ra hop thoai.
        Thread {
            val nd = kho.dangKy(ten, email, mk, dt.ifBlank { null })
            runOnUiThread {
                if (nd == null) { loi(getString(R.string.dk_loi_chung)); return@runOnUiThread }
                TaiKhoan.ghiPhien(this, nd)
                maKhoiPhuc = TaiKhoan.taoMaKhoiPhuc(this)
                Rung.xong(window.decorView)
                veMaKhoiPhuc()
            }
        }.start()
    }

    // ================================================================
    // BUOC 1 - MA KHOI PHUC
    // ================================================================

    private fun veMaKhoiPhuc() {
        buoc = 1
        val goc = cot()

        goc.addView(ImageView(this).apply {
            setImageResource(R.drawable.ic_khoa)
            setColorFilter(mau(R.color.nhan))
        }, LinearLayout.LayoutParams(dp(40), dp(40)).apply {
            gravity = Gravity.CENTER_HORIZONTAL; topMargin = dp(10)
        })

        goc.addView(tieuDe(getString(R.string.ma_tieu_de)), lp(18))
        goc.addView(phu(getString(R.string.ma_phu)), lp(8))

        // Ma hien thanh 3 cum 4 ky tu, chu to va gian: doc to tay len
        // giay khong nham 8 voi B, 5 voi S (bang chu da bo I O 0 1).
        goc.addView(TextView(this).apply {
            text = maKhoiPhuc   // taoMaKhoiPhuc da tra ve dang ABCD-EFGH-JKLM
            textSize = 25f
            gravity = Gravity.CENTER
            letterSpacing = 0.12f
            typeface = Typeface.MONOSPACE
            minHeight = dp(76)
            setPadding(dp(12), dp(20), dp(12), dp(20))
            setTextColor(mau(R.color.chu))
            background = GradientDrawable().apply {
                cornerRadius = dp(18).toFloat()
                setColor(mau(R.color.the_2))
                setStroke(dp(2), mau(R.color.nhan))
            }
            // TalkBack doc tung ky tu mot, khong doc "ABCD" thanh mot tu.
            contentDescription = getString(R.string.ma_doc,
                maKhoiPhuc.filter { it != '-' }.toCharArray().joinToString(" "))
        }, lp(24))

        goc.addView(nutPhu(getString(R.string.ma_sao_chep)) {
            val cb = getSystemService(Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
            cb.setPrimaryClip(android.content.ClipData.newPlainText(
                getString(R.string.ma_nhan_clip), maKhoiPhuc))
            android.widget.Toast.makeText(this, getString(R.string.ma_da_chep),
                android.widget.Toast.LENGTH_SHORT).show()
        }, lp(12))

        goc.addView(TextView(this).apply {
            text = getString(R.string.ma_canh_bao)
            textSize = 13f
            setLineSpacing(0f, 1.5f)
            setTextColor(mau(R.color.chu_phu))
            setPadding(dp(16), dp(14), dp(16), dp(14))
            background = GradientDrawable().apply {
                cornerRadius = dp(16).toFloat()
                setColor(mau(R.color.nhan_nhat))
            }
        }, lp(22))

        goc.addView(View(this), LinearLayout.LayoutParams(-1, 0, 1f))
        goc.addView(nutChinh(getString(R.string.ma_da_luu)) {
            startActivity(Intent(this, ViecCanLamActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_NEW_TASK))
            finish()
        }, lp(24))

        datNoiDung(goc)
    }

    // ================================================================
    // KHUON NHO
    // ================================================================

    private fun datNoiDung(goc: LinearLayout) {
        val cuon = ScrollView(this).apply {
            setBackgroundColor(mau(R.color.nen))
            isFillViewport = true
        }
        cuon.addView(goc)
        setContentView(cuon)
        GiaoDien.apFont(goc, this)
    }

    private fun cot() = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(24), dp(30), dp(24), dp(26))
    }

    private fun loi(s: String) {
        tvLoi.text = s
        tvLoi.visibility = View.VISIBLE
        Rung.nhe(tvLoi)
    }

    /** O mat khau + nut con mat: GIU de hien, tha ra la an (nhu DangNhap). */
    private fun oCoMat(o: EditText, goiY: String): View {
        val hang = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            background = getDrawable(R.drawable.o_nhap)
        }
        o.apply {
            hint = goiY
            textSize = 16f
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
            transformationMethod = PasswordTransformationMethod.getInstance()
            setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
            background = null
            minHeight = dp(54)
            setPadding(dp(14), 0, dp(6), 0)
        }
        hang.addView(o, LinearLayout.LayoutParams(0, -2, 1f))
        hang.addView(ImageView(this).apply {
            setImageResource(R.drawable.ic_mat)
            setColorFilter(mau(R.color.chu_phu))
            val p = dp(13); setPadding(p, p, p, p)
            contentDescription = getString(R.string.dk_giu_de_hien)
            setOnTouchListener { v, e ->
                when (e.actionMasked) {
                    MotionEvent.ACTION_DOWN -> {
                        o.transformationMethod = null
                        (v as ImageView).setImageResource(R.drawable.ic_mat_tat)
                        o.setSelection(o.text.length); true
                    }
                    MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                        o.transformationMethod = PasswordTransformationMethod.getInstance()
                        (v as ImageView).setImageResource(R.drawable.ic_mat)
                        o.setSelection(o.text.length); v.performClick(); true
                    }
                    else -> false
                }
            }
        }, LinearLayout.LayoutParams(dp(50), dp(50)))
        return hang
    }

    private fun oNhap(goiY: String, kieu: Int) = EditText(this).apply {
        hint = goiY
        textSize = 16f
        inputType = kieu
        setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
        background = getDrawable(R.drawable.o_nhap)
        minHeight = dp(54)
        setPadding(dp(14), 0, dp(14), 0)
    }

    private fun tieuDe(s: String) = TextView(this).apply {
        text = s; textSize = 24f; gravity = Gravity.CENTER
        typeface = Typeface.DEFAULT_BOLD
        setTextColor(mau(R.color.chu))
        if (android.os.Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
    }

    private fun phu(s: String) = TextView(this).apply {
        text = s; textSize = 13.5f; gravity = Gravity.CENTER
        setLineSpacing(0f, 1.4f)
        setTextColor(mau(R.color.chu_phu))
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

    private fun nutPhu(s: String, khi: () -> Unit) = TextView(this).apply {
        text = s; textSize = 15f; gravity = Gravity.CENTER
        typeface = Typeface.DEFAULT_BOLD
        minHeight = dp(48); includeFontPadding = false
        setTextColor(mau(R.color.chu_lien_ket))
        background = getDrawable(R.drawable.nut_phu)
        setOnClickListener { Rung.nhe(it); khi() }
    }

    private fun lp(tren: Int) = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(tren) }
    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)
}
