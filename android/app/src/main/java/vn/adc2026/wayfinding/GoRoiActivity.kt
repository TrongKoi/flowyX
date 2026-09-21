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
    private var nutQuayLai: ImageView? = null

    /**
     * Cac buoc nho. Nhieu hon mot, va do la co y (muc 6.3).
     *
     * Ban truoc chi co DUNG mot o. Nhung khi nguoi dung da ngoi xuong va
     * nghi ra duoc buoc dau tien, thuong buoc thu hai va thu ba ra theo
     * ngay lap tuc - va bat ho nho trong dau cho toi luc bat dau la lam
     * hong dung cai vua go duoc.
     *
     * Toi da ba. Khong phai gioi han ky thuat: o thu tu bien man hinh nay
     * thanh mot danh sach viec phai lap, va lap danh sach la CHINH CAI
     * viec ma nguoi dung dang ne.
     */
    private val buocNhoThem = mutableListOf<String>()

    override fun attachBaseContext(moi: Context) {
        super.attachBaseContext(GiaoDien.boc(moi))
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
        // ----- MUC 6.3: MOI BUOC PHAI CO DUONG QUAY LAI THAY DUOC -----
        //
        // Ghi chu "nguyen tac 3" o dau tep noi chi nen co MOT duong thoat,
        // va dieu do van dung - `✕` van la loi ra duy nhat. Nhung "quay
        // lai mot buoc" khong phai la thoat: no la sua mot cau vua tra
        // loi hoi.
        //
        // Truoc day chi nut Back CUNG cua may lam duoc viec do. Tren may
        // dung cu chi vuot thi nguoi dung phai biet vuot tu mep; tren man
        // hinh nay - noi ho vua cham ba nut lien tiep - khong co gi goi y
        // rang lui lai duoc. Va cam giac "lo cham nham roi, khong sua
        // duoc" la dung thu day nguoi ta ra khoi luong.
        //
        // Hai icon o hai dau, y nghia khac han nhau, khong nham vao nhau:
        // `←` ben trai lui mot buoc, `✕` ben phai thoat han.
        goc.addView(LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            minimumHeight = dp(56)
            nutQuayLai = ImageView(this@GoRoiActivity).apply {
                setImageResource(R.drawable.ic_quay_lai)
                setColorFilter(mau(R.color.chu_phu))
                val p = dp(14); setPadding(p, p, p, p)
                contentDescription = getString(R.string.quay_lai)
                setOnClickListener { Rung.nhe(it); lui() }
            }
            addView(nutQuayLai, LinearLayout.LayoutParams(dp(52), dp(52)))
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
        if (buoc > 0) lui() else @Suppress("DEPRECATION") super.onBackPressed()
    }

    private fun lui() {
        if (buoc > 0) { buoc--; ve() } else finish()
    }

    // ---------------------------------------------------------------

    private fun ve() {
        veCham()
        // Buoc dau chua co gi de lui ve - an di chu khong de mot nut bam
        // vao thi khong co gi xay ra.
        nutQuayLai?.visibility = if (buoc > 0) View.VISIBLE else View.INVISIBLE
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
        // ----- MOT O, ROI THEM O NEU MUON (muc 6.3) -----
        //
        // Man hinh mo ra van chi co DUNG MOT o - giu nguyen cam giac nhe
        // cua ban cu. O thu hai va thu ba chi xuat hien khi nguoi dung tu
        // bam "+ Thêm bước". Ai chi can mot buoc thi khong bao gio thay
        // cai nao khac.
        val cacO = mutableListOf<EditText>()
        val cotO = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }

        fun themO(giaTri: String, dau: Boolean) {
            val o = EditText(this).apply {
                hint = getString(if (dau) R.string.gr_hint_buoc else R.string.gr_hint_buoc_them)
                setText(giaTri)
                textSize = 16f
                inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
                setTextColor(mau(R.color.chu)); setHintTextColor(mau(R.color.chu_phu))
                background = getDrawable(R.drawable.o_nhap)
                minHeight = dp(56)
                setPadding(dp(14), dp(10), dp(14), dp(10))
            }
            cacO += o
            cotO.addView(o, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10) })
        }

        themO(buocNho, true)
        for (b in buocNhoThem) themO(b, false)
        noi.addView(cotO, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(6) })

        val nutThemBuoc = TextView(this).apply {
            text = getString(R.string.gr_them_buoc)
            textSize = 14.5f
            gravity = Gravity.CENTER
            minHeight = dp(46)
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(mau(R.color.chu_lien_ket))
            visibility = if (cacO.size < TOI_DA_BUOC) View.VISIBLE else View.GONE
            setOnClickListener {
                Rung.nhe(it)
                // Giu lai nhung gi da go truoc khi ve lai man hinh.
                buocNho = cacO[0].text.toString().trim()
                buocNhoThem.clear()
                buocNhoThem += cacO.drop(1).map { e -> e.text.toString().trim() }
                buocNhoThem += ""
                ve()
            }
        }
        noi.addView(nutThemBuoc, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(4) })

        noi.addView(View(this), LinearLayout.LayoutParams(-1, 0, 1f))
        noi.addView(nutChinh(getString(R.string.tiep_tuc)) {
            buocNho = cacO[0].text.toString().trim()
            buocNhoThem.clear()
            // O de trong thi bo di - khong bat nguoi dung phai dien cho du.
            buocNhoThem += cacO.drop(1).map { e -> e.text.toString().trim() }.filter { t -> t.isNotBlank() }
            buoc++; ve()
        })
        boQua(noi)
    }

    // --- Buoc 4: bao lau ---

    private fun buocThoiGian(noi: LinearLayout) {
        cauHoi(noi, R.string.gr_cau_bao_lau, R.string.gr_bao_lau_phu)
        val v = VongTapTrungView(this).apply {
            datMau(mau(R.color.the), mau(R.color.dh_mat_dang_keo),
                mau(R.color.nen), mau(R.color.dh_ranh),
                mau(R.color.chu), mau(R.color.chu_phu),
                mau(R.color.dh_con_nhieu), mau(R.color.dh_sap_den), mau(R.color.dh_di_ngay),
                mau(R.color.dh_dang_keo))
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
        // ----- NOI RONG TRAN 30 PHUT (muc 6.3) -----
        //
        // Y dinh ban dau la "day chi la thu mot chut". Nhung tran cung o
        // 30 phut bien mot cau dong vien thanh mot cau TU CHOI: nguoi dung
        // keo toi 30 roi vong khong nhuc nhich nua, ma khong co gi noi vi
        // sao. Va voi nhieu nguoi ADHD, luc cuoi cung cung vao duoc luong
        // thi 30 phut la qua ngan de phai dung lai xin them.
        //
        // 90 phut la tran moi: du dai cho mot phien that, va van du ngan
        // de khong ai vo tinh hen minh ba tieng lien.
        v.khiDoiPhut = { p -> phut = p.coerceIn(1, TOI_DA_PHUT_GO_ROI); capNhat() }
        capNhat()
        noi.addView(v, LinearLayout.LayoutParams(-1, -2).apply {
            topMargin = dp(10); marginStart = dp(40); marginEnd = dp(40)
        })
        noi.addView(camKet, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(14) })
        noi.addView(View(this), LinearLayout.LayoutParams(-1, 0, 1f))
        noi.addView(nutChinh(getString(R.string.go_roi_bat_dau)) { xong() })
    }

    /**
     * ----- XUNG DOT PHIEN (muc 6.3) -----
     *
     * Dong ho dang chay cho viec A, nguoi dung mo Go roi va dat xong viec
     * B. `xong()` cu giu nguyen `cu.dem` neu no da bat dau - nghia la ten
     * va buoc nho doi sang B, con dong ho van dang dem cho A. Man hinh
     * Focus khi do hien ten B ben tren mot dong ho thuoc ve A, va khong
     * co gi noi ra dieu do.
     *
     * Gio hoi mot cau, DUNG MOT LAN, va chi khi that su co xung dot:
     * khong co dong ho nao dang chay thi khong hoi gi ca - them mot hop
     * thoai vao luong cua nguoi dang te liet la them mot buc tuong.
     */
    private fun xong() {
        val cu = TrangThaiFocus.doc(this)
        if (cu.dem.dangChay) {
            val con = DemNguoc.soPhutHien(cu.dem.conLaiMs(System.currentTimeMillis()))
            android.app.AlertDialog.Builder(this)
                .setTitle(R.string.gr_dang_chay_tieu_de)
                .setMessage(getString(R.string.gr_dang_chay_hoi,
                    cu.ten ?: getString(R.string.gr_viec_nay), con))
                // Bat dau viec moi: dong ho dat lai theo so phut vua chon.
                .setPositiveButton(R.string.gr_dang_chay_bat_dau) { _, _ -> luuVaDong(cu, datLai = true) }
                // Giu phien cu: chi ghi lai ten + cac buoc, dong ho khong dong toi.
                .setNegativeButton(R.string.gr_dang_chay_giu) { _, _ -> luuVaDong(cu, datLai = false) }
                .hien()
            return
        }
        luuVaDong(cu, datLai = true)
    }

    private fun luuVaDong(cu: TrangThaiFocus, datLai: Boolean) {
        TrangThaiFocus(
            dem = if (cu.dem.chuaBatDau || datLai) DemNguoc().datThoiLuong(phut) else cu.dem,
            ten = viec.ifBlank { null },
            buocDau = (listOf(buocNho) + buocNhoThem)
                .map { it.trim() }.filter { it.isNotBlank() }
                .joinToString("\n").ifBlank { null },
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

    private companion object {
        /** Toi da ba o. Xem ghi chu o `buocNhoThem`. */
        const val TOI_DA_BUOC = 3
        /** Xem ghi chu tai `khiDoiPhut` cua buoc 4. */
        const val TOI_DA_PHUT_GO_ROI = 90
    }
}
