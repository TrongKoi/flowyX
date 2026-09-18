package vn.adc2026.wayfinding

import android.app.Activity
import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.text.InputType
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
 * QUEN MAT KHAU (v5)
 * ====================================================================
 *
 * Khong co may chu, nen khong co "gui link dat lai qua email". Duong
 * lay lai tai khoan la MA KHOI PHUC 12 ky tu da hien mot lan luc dang
 * ky (ban BAM nam trong may - xem TaiKhoan.taoMaKhoiPhuc).
 *
 * Hai buoc:
 *   buoc 0 - nhap ma khoi phuc
 *   buoc 1 - dat mat khau moi
 *
 * ----- Loi thoat cuoi cung: xoa het va bat dau lai -----
 *
 * Mat ma khoi phuc la mat nhat ky (nhat ky ma hoa bang khoa trong
 * Keystore, va Keystore khong mo lai duoc khi khong con tai khoan).
 * Thay vi de nguoi dung ket cung o man hinh dang nhap voi mot app
 * khong vao duoc - tinh huong chi con cach go app - o day co duong
 * xoa sach va bat dau lai, VOI HAI LAN XAC NHAN va mot cau noi thang
 * la du lieu se mat han. Hai lan xac nhan la vi day la thao tac khong
 * hoan tac duoc, va nguoi dung o day dang buc boi - trang thai de bam
 * bua nhat.
 *
 * ----- Vi sao cham dan cung ap o day -----
 *
 * Ma khoi phuc chi 12 ky tu tren bang 32 chu (~60 bit) - do vet can
 * khong thuc te, nhung `TaiKhoan.ghiNhanSai` van dung chung bo dem voi
 * man dang nhap de mot cong cu tu dong khong the thu hang nghin lan.
 */
class QuenMatKhauActivity : Activity() {

    private var buoc = 0
    private lateinit var oMa: EditText
    private lateinit var oMoi: EditText
    private lateinit var oXacNhan: EditText
    private lateinit var tvLoi: TextView

    override fun attachBaseContext(moi: Context) {
        super.attachBaseContext(NgonNgu.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        veNhapMa()
    }

    override fun onBackPressed() {
        if (buoc == 1) { buoc = 0; veNhapMa(); return }
        super.onBackPressed()
    }

    // ================================================================
    // BUOC 0 - NHAP MA KHOI PHUC
    // ================================================================

    private fun veNhapMa() {
        buoc = 0
        val goc = cot()
        goc.addView(nutQuayLai(), LinearLayout.LayoutParams(dp(40), dp(40)))

        goc.addView(ImageView(this).apply {
            setImageResource(R.drawable.ic_khoa)
            setColorFilter(mau(R.color.nhan))
        }, LinearLayout.LayoutParams(dp(38), dp(38)).apply {
            gravity = Gravity.CENTER_HORIZONTAL; topMargin = dp(12)
        })

        goc.addView(tieuDe(getString(R.string.qmk_tieu_de)), lp(18))
        goc.addView(phu(getString(R.string.qmk_phu)), lp(8))

        goc.addView(nhan(getString(R.string.qmk_nhan_ma)), lp(26))
        oMa = EditText(this).apply {
            hint = getString(R.string.qmk_hint_ma)
            textSize = 18f
            gravity = Gravity.CENTER
            letterSpacing = 0.1f
            typeface = Typeface.MONOSPACE
            // CAP_CHARACTERS: bang chu cua ma chi co chu hoa va so, viet
            // hoa san de nguoi dung khong phai voi phim Shift.
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS
            setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
            background = getDrawable(R.drawable.o_nhap)
            minHeight = dp(58)
            setPadding(dp(14), 0, dp(14), 0)
        }
        goc.addView(oMa, lp(8))

        tvLoi = oLoi()
        goc.addView(tvLoi, lp(10))

        goc.addView(nutChinh(getString(R.string.qmk_nut_kiem)) { kiemMa() }, lp(16))

        goc.addView(View(this), LinearLayout.LayoutParams(-1, 0, 1f))

        goc.addView(TextView(this).apply {
            text = getString(R.string.qmk_mat_ma)
            textSize = 13.5f
            gravity = Gravity.CENTER
            minHeight = dp(48)
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(mau(R.color.do_xoa))
            setOnClickListener { Rung.nhe(it); hoiXoaHet() }
        }, lp(20))

        datNoiDung(goc)
    }

    private fun kiemMa() {
        val cho = TaiKhoan.conPhaiCho(this)
        if (cho > 0) { loi(getString(R.string.dn_cho_giay, (cho / 1000 + 1).toInt())); return }

        if (!TaiKhoan.coMaKhoiPhuc(this)) { loi(getString(R.string.qmk_khong_co_ma)); return }

        val nhap = oMa.text.toString()
        Thread {
            val dung = TaiKhoan.kiemMaKhoiPhuc(this, nhap)
            runOnUiThread {
                if (!dung) {
                    TaiKhoan.ghiNhanSai(this)
                    loi(getString(R.string.qmk_ma_sai))
                } else {
                    TaiKhoan.ghiNhanDung(this)
                    Rung.xong(window.decorView)
                    veDatMoi()
                }
            }
        }.start()
    }

    // ================================================================
    // BUOC 1 - DAT MAT KHAU MOI
    // ================================================================

    private fun veDatMoi() {
        buoc = 1
        val goc = cot()
        goc.addView(nutQuayLai(), LinearLayout.LayoutParams(dp(40), dp(40)))

        goc.addView(tieuDe(getString(R.string.qmk_moi_tieu_de)), lp(24))
        goc.addView(phu(getString(R.string.qmk_moi_phu)), lp(8))

        goc.addView(nhan(getString(R.string.qmk_mat_khau_moi)), lp(26))
        oMoi = EditText(this)
        goc.addView(oCoMat(oMoi, getString(R.string.dk_hint_mat_khau)), lp(6))

        goc.addView(nhan(getString(R.string.dk_xac_nhan)), lp(14))
        oXacNhan = EditText(this)
        goc.addView(oCoMat(oXacNhan, getString(R.string.dk_hint_xac_nhan)), lp(6))

        tvLoi = oLoi()
        goc.addView(tvLoi, lp(10))

        goc.addView(nutChinh(getString(R.string.qmk_nut_doi)) { doiMatKhau() }, lp(16))

        goc.addView(View(this), LinearLayout.LayoutParams(-1, 0, 1f))
        goc.addView(TextView(this).apply {
            text = getString(R.string.qmk_ma_moi)
            textSize = 12f
            gravity = Gravity.CENTER
            setLineSpacing(0f, 1.45f)
            setTextColor(mau(R.color.chu_phu))
        }, lp(20))

        datNoiDung(goc)
    }

    private fun doiMatKhau() {
        val mk = oMoi.text.toString()
        val xn = oXacNhan.text.toString()
        if (mk.length < KhoDuLieu.TOI_THIEU) {
            loi(getString(R.string.dk_loi_ngan, KhoDuLieu.TOI_THIEU)); return
        }
        if (mk != xn) { loi(getString(R.string.dk_loi_khac_nhau)); return }

        val kho = KhoDuLieu(this)
        val nd = kho.nguoiDau()
        if (nd == null) { loi(getString(R.string.qmk_khong_co_tk)); return }

        Thread {
            val xong = kho.doiMatKhau(nd.email, mk)
            // Ma cu da dung mot lan thi bo di, sinh ma moi ngay - neu
            // khong, nguoi nao doc trom ma cu van mo duoc lan sau.
            val maMoi = if (xong) TaiKhoan.taoMaKhoiPhuc(this) else ""
            runOnUiThread {
                if (!xong) { loi(getString(R.string.dk_loi_chung)); return@runOnUiThread }
                TaiKhoan.ghiPhien(this, nd)
                Rung.xong(window.decorView)
                hienMaMoi(maMoi)
            }
        }.start()
    }

    private fun hienMaMoi(ma: String) {
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.qmk_ma_moi_tieu_de))
            .setMessage(getString(R.string.qmk_ma_moi_noi_dung, ma))
            .setCancelable(false)
            .setPositiveButton(getString(R.string.ma_da_luu)) { _, _ ->
                startActivity(Intent(this, ViecCanLamActivity::class.java)
                    .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_NEW_TASK))
                finish()
            }
            .hien()
    }

    // ================================================================
    // LOI THOAT: XOA HET
    // ================================================================

    private fun hoiXoaHet() {
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.qmk_xoa_tieu_de))
            .setMessage(getString(R.string.qmk_xoa_1))
            .setNegativeButton(getString(R.string.huy), null)
            .setPositiveButton(getString(R.string.qmk_xoa_tiep)) { _, _ -> hoiLanHai() }
            .hien()
    }

    private fun hoiLanHai() {
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.qmk_xoa_chac))
            .setMessage(getString(R.string.qmk_xoa_2))
            .setNegativeButton(getString(R.string.qmk_xoa_giu), null)
            .setPositiveButton(getString(R.string.qmk_xoa_lam)) { _, _ ->
                TaiKhoan.xoaHet(this)
                startActivity(Intent(this, DangKyActivity::class.java)
                    .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TASK or Intent.FLAG_ACTIVITY_NEW_TASK))
                finish()
            }
            .hien()
    }

    // ================================================================
    // KHUON NHO
    // ================================================================

    private fun datNoiDung(goc: LinearLayout) {
        val cuon = ScrollView(this).apply {
            setBackgroundColor(mau(R.color.nen)); isFillViewport = true
        }
        cuon.addView(goc)
        setContentView(cuon)
        GiaoDien.apFont(goc, this)
    }

    private fun cot() = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(24), dp(20), dp(24), dp(26))
    }

    private fun nutQuayLai() = ImageView(this).apply {
        setImageResource(R.drawable.ic_quay_lai)
        setColorFilter(mau(R.color.chu_phu))
        val p = dp(8); setPadding(p, p, p, p)
        contentDescription = getString(R.string.quay_lai)
        background = GradientDrawable().apply {
            shape = GradientDrawable.OVAL; setColor(mau(R.color.the))
        }
        setOnClickListener { Rung.nhe(it); onBackPressed() }
    }

    private fun oLoi() = TextView(this).apply {
        textSize = 13f
        setLineSpacing(0f, 1.35f)
        setTextColor(mau(R.color.do_xoa))
        visibility = View.GONE
        accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_ASSERTIVE
    }

    private fun loi(s: String) {
        tvLoi.text = s; tvLoi.visibility = View.VISIBLE; Rung.nhe(tvLoi)
    }

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

    private fun tieuDe(s: String) = TextView(this).apply {
        text = s; textSize = 24f; gravity = Gravity.CENTER
        typeface = Typeface.DEFAULT_BOLD
        setTextColor(mau(R.color.chu))
        if (android.os.Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
    }

    private fun phu(s: String) = TextView(this).apply {
        text = s; textSize = 13.5f; gravity = Gravity.CENTER
        setLineSpacing(0f, 1.45f)
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

    private fun lp(tren: Int) = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(tren) }
    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)
}
