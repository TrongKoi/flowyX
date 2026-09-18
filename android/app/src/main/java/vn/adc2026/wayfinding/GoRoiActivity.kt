package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.animation.AlphaAnimation
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import vn.adc2026.frontend.VongTapTrungView

/**
 * ====================================================================
 * GO ROI DE BAT DAU (v5) - MOT CAU MOI MAN
 * ====================================================================
 *
 * ----- Vi sao doi so voi v4 -----
 *
 * v4 do ca nam cau ra cung mot man hinh, voi ly do "thay het thi biet chi
 * co chung nay". Thu nghiem cho ket qua nguoc: nguoi dang TE LIET nhin
 * mot trang day cau hoi thi thay them mot viec nua phai lam. Dung luc can
 * nhe nhat thi man hinh lai nang nhat.
 *
 * v5: moi man MOT cau, ba lua chon cham la xong. Khong ban phim (tru cau
 * 2, va cau do van bo qua duoc). Bon cham tien trinh o tren cho biet con
 * bao nhieu - "sap het" la thong tin quan trong nhat voi nguoi dang ngai.
 *
 * ----- Nam nguyen tac giu nguyen -----
 *
 *   1. Cau nao cung bo qua duoc. Nut "Chưa rõ, đi tiếp" luon o duoi.
 *   2. Khong co cau tra loi sai - man hinh noi thang dieu do.
 *   3. Chi MOT duong thoat: dau X o goc. v4 co ca "Bỏ qua" lan X, hai
 *      nut cung mot y nghia la mot lan phai chon.
 *   4. Khong tinh diem, khong luu lai cau tra loi de "phan tich".
 *   5. Ket thuc bang mot cau cam ket doc len duoc, roi vao thang dong ho.
 *
 * ----- Bon buoc -----
 *
 *   1. Viec gi dang cho?        (go, co the bo trong)
 *   2. Viec nay dang thay the nao?  (ba nut cam xuc)
 *   3. Buoc nho nhat la gi?     (ba goi y sinh theo buoc 2, hoac tu go)
 *   4. Thu bao lau?             (vong nho keo duoc 1..30 phut)
 */
class GoRoiActivity : Activity() {

    private var buoc = 0
    private var viec = ""
    private var canTro = -1
    private var buocNho = ""
    private var phut = 10

    private lateinit var khung: FrameLayout
    private lateinit var chamTienTrinh: LinearLayout

    override fun attachBaseContext(moi: Context) {
        super.attachBaseContext(NgonNgu.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        val tt = TrangThaiFocus.doc(this)
        viec = tt.ten ?: ""
        buocNho = tt.buocDau ?: ""

        val goc = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(mau(R.color.nen))
        }
        // Thanh tren: CHI mot dau X, khong co nut nao khac.
        goc.addView(LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            minimumHeight = dp(56)
            addView(View(this@GoRoiActivity), LinearLayout.LayoutParams(0, dp(1), 1f))
            addView(ImageView(this@GoRoiActivity).apply {
                setImageResource(R.drawable.ic_dong)
                setColorFilter(mau(R.color.chu_phu))
                val p = dp(14); setPadding(p, p, p, p)
                contentDescription = getString(R.string.go_roi_dong)
                setOnClickListener { Rung.nhe(it); finish() }
            }, LinearLayout.LayoutParams(dp(52), dp(52)))
        }, LinearLayout.LayoutParams(-1, -2))

        chamTienTrinh = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }
        goc.addView(chamTienTrinh, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(4) })

        khung = FrameLayout(this)
        goc.addView(khung, LinearLayout.LayoutParams(-1, 0, 1f))
        setContentView(goc)
        ve()
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (buoc > 0) { buoc--; ve() } else @Suppress("DEPRECATION") super.onBackPressed()
    }

    // ---------------------------------------------------------------

    private fun ve() {
        veCham()
        val noi = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(22), dp(10), dp(22), dp(22))
        }
        when (buoc) {
            0 -> buocViec(noi)
            1 -> buocCamXuc(noi)
            2 -> buocNhoNhat(noi)
            else -> buocThoiGian(noi)
        }
        khung.removeAllViews()
        khung.addView(noi, FrameLayout.LayoutParams(-1, -1))
        noi.startAnimation(AlphaAnimation(0f, 1f).apply { duration = 160 })
        GiaoDien.apFont(noi, this)
    }

    private fun veCham() {
        chamTienTrinh.removeAllViews()
        for (i in 0 until 4) {
            chamTienTrinh.addView(View(this).apply {
                background = GradientDrawable().apply {
                    cornerRadius = dp(2).toFloat()
                    setColor(mau(if (i <= buoc) R.color.cam else R.color.vien))
                }
            }, LinearLayout.LayoutParams(dp(26), dp(4)).apply { marginStart = dp(3); marginEnd = dp(3) })
        }
    }

    /** Cau hoi to, can giua, co khoang tho phia tren. */
    private fun cauHoi(noi: LinearLayout, cau: Int, phu: Int? = null) {
        noi.addView(TextView(this).apply {
            text = getString(cau)
            textSize = 23f
            typeface = Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
            setTextColor(mau(R.color.chu))
            setLineSpacing(0f, 1.3f)
            if (android.os.Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(26) })
        phu?.let {
            noi.addView(TextView(this).apply {
                text = getString(it)
                textSize = 13.5f
                gravity = Gravity.CENTER
                setTextColor(mau(R.color.chu_phu))
            }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(8) })
        }
    }

    /** Nut lua chon to, cham mot cai la sang buoc sau. */
    private fun nutChon(noi: LinearLayout, chu: String, emoji: String, khi: () -> Unit) {
        noi.addView(LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            minimumHeight = dp(60)
            background = getDrawable(R.drawable.nut_phu)
            setPadding(dp(18), dp(10), dp(18), dp(10))
            isClickable = true
            setOnClickListener { Rung.nhe(it); khi() }
            addView(TextView(this@GoRoiActivity).apply {
                text = emoji; textSize = 20f
                includeFontPadding = false
                importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
            }, LinearLayout.LayoutParams(-2, -2).apply { marginEnd = dp(14) })
            addView(TextView(this@GoRoiActivity).apply {
                text = chu; textSize = 16f
                setTextColor(mau(R.color.chu))
                setLineSpacing(0f, 1.25f)
            }, LinearLayout.LayoutParams(0, -2, 1f))
            contentDescription = chu
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10) })
    }

    private fun boQua(noi: LinearLayout, chu: Int = R.string.go_roi_di_tiep) {
        noi.addView(TextView(this).apply {
            text = getString(chu)
            textSize = 14.5f
            gravity = Gravity.CENTER
            minHeight = dp(48)
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(mau(R.color.chu_lien_ket))
            setOnClickListener { Rung.nhe(it); buoc++; ve() }
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(18) })
    }

    // --- Buoc 1: viec gi ---

    private fun buocViec(noi: LinearLayout) {
        cauHoi(noi, R.string.gr_cau_viec, R.string.gr_viec_phu)
        val o = EditText(this).apply {
            hint = getString(R.string.gr_hint_viec)
            setText(viec)
            textSize = 17f
            gravity = Gravity.CENTER
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
            setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
            background = getDrawable(R.drawable.o_nhap)
            minHeight = dp(56)
            setPadding(dp(14), dp(10), dp(14), dp(10))
        }
        noi.addView(o, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(24) })
        noi.addView(View(this), LinearLayout.LayoutParams(-1, 0, 1f))
        noi.addView(nutChinh(getString(R.string.tiep_tuc)) {
            viec = o.text.toString().trim(); buoc++; ve()
        })
        boQua(noi, R.string.gr_chua_ro)
    }

    // --- Buoc 2: cam xuc ---

    private fun buocCamXuc(noi: LinearLayout) {
        cauHoi(noi, R.string.gr_cau_cam_xuc, R.string.gr_khong_sai)
        val ten = resources.getStringArray(R.array.gr_can_tro)
        val emoji = listOf("🫥", "🏔️", "😬", "😐", "😮‍💨", "🌀")
        for (i in ten.indices) {
            nutChon(noi, ten[i], emoji.getOrElse(i) { "•" }) { canTro = i; buoc++; ve() }
        }
        noi.addView(View(this), LinearLayout.LayoutParams(-1, 0, 1f))
        boQua(noi)
    }

    // --- Buoc 3: buoc nho nhat ---

    private fun buocNhoNhat(noi: LinearLayout) {
        cauHoi(noi, R.string.gr_cau_buoc, R.string.gr_buoc_phu)
        // Goi y sinh theo cam xuc da chon o buoc 2 - dung cai dang can.
        canTro.takeIf { it >= 0 }?.let { i ->
            resources.getStringArray(R.array.gr_goi_y).getOrNull(i)?.let { g ->
                noi.addView(TextView(this).apply {
                    text = g
                    textSize = 14f
                    setTextColor(mau(R.color.chu))
                    setLineSpacing(0f, 1.4f)
                    background = getDrawable(R.drawable.nen_the_vang)
                    setPadding(dp(14), dp(12), dp(14), dp(12))
                }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(18) })
            }
        }
        val o = EditText(this).apply {
            hint = getString(R.string.gr_hint_buoc)
            setText(buocNho)
            textSize = 16f
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
            setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
            background = getDrawable(R.drawable.o_nhap)
            minHeight = dp(56)
            setPadding(dp(14), dp(10), dp(14), dp(10))
        }
        noi.addView(o, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(16) })
        noi.addView(View(this), LinearLayout.LayoutParams(-1, 0, 1f))
        noi.addView(nutChinh(getString(R.string.tiep_tuc)) {
            buocNho = o.text.toString().trim(); buoc++; ve()
        })
        boQua(noi)
    }

    // --- Buoc 4: bao lau ---

    private fun buocThoiGian(noi: LinearLayout) {
        cauHoi(noi, R.string.gr_cau_bao_lau, R.string.gr_bao_lau_phu)
        val v = VongTapTrungView(this).apply {
            datMau(mau(R.color.the), mau(R.color.nen), mau(R.color.dh_ranh),
                mau(R.color.chu), mau(R.color.chu_phu),
                mau(R.color.dh_con_nhieu), mau(R.color.dh_sap_den), mau(R.color.dh_di_ngay))
            datFont(GiaoDien.font(this@GoRoiActivity, false), GiaoDien.font(this@GoRoiActivity, true))
            datPhutKeo(phut)
            khiQuaMoc = { tyLe -> Rung.luyTien(this, tyLe) }
        }
        val camKet = TextView(this).apply {
            textSize = 15.5f
            gravity = Gravity.CENTER
            setTextColor(mau(R.color.chu))
            setLineSpacing(0f, 1.4f)
            background = getDrawable(R.drawable.nen_the_vang)
            setPadding(dp(16), dp(14), dp(16), dp(14))
        }
        fun capNhat() {
            v.dat(phut.toFloat(), false, "$phut", getString(R.string.focus_phut))
            camKet.text = getString(R.string.gr_cam_ket,
                buocNho.ifBlank { viec.ifBlank { getString(R.string.gr_viec_nay) } }, phut)
        }
        // Gioi han 1..30 phut o day: day la "thu mot chut", khong phai phien lam viec.
        v.khiDoiPhut = { p -> phut = p.coerceIn(1, 30); capNhat() }
        capNhat()
        noi.addView(v, LinearLayout.LayoutParams(-1, -2).apply {
            topMargin = dp(10); marginStart = dp(40); marginEnd = dp(40)
        })
        noi.addView(camKet, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(14) })
        noi.addView(View(this), LinearLayout.LayoutParams(-1, 0, 1f))
        noi.addView(nutChinh(getString(R.string.go_roi_bat_dau)) { xong() })
    }

    private fun xong() {
        val cu = TrangThaiFocus.doc(this)
        TrangThaiFocus(
            dem = if (cu.dem.chuaBatDau) DemNguoc().datThoiLuong(phut) else cu.dem,
            ten = viec.ifBlank { null },
            buocDau = buocNho.ifBlank { null },
            lyDo = cu.lyDo,
            keHoachId = cu.keHoachId,
        ).luu(this)
        findViewById<View>(android.R.id.content)?.let { Rung.xong(it) }
        setResult(RESULT_OK)
        finish()
    }

    private fun nutChinh(chu: String, khi: () -> Unit) = TextView(this).apply {
        text = chu; textSize = 17f; gravity = Gravity.CENTER
        typeface = Typeface.DEFAULT_BOLD
        minHeight = dp(54); includeFontPadding = false
        setTextColor(mau(R.color.chu_tren_nhan))
        background = getDrawable(R.drawable.nut_chinh)
        setOnClickListener { Rung.nhe(it); khi() }
        layoutParams = LinearLayout.LayoutParams(-1, -2)
    }

    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)
}
