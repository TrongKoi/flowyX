package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/**
 * ====================================================================
 * XEM TRUOC & DUYET - ket qua phan ra truoc khi vao luong lam viec
 * ====================================================================
 *
 * ----- Nam quyet dinh, va ly do -----
 *
 * 1. CHECKLIST TINH, KHONG PHAI ACCORDION.
 *    Accordion giau noi dung sau mot cu cham, nen nguoi dung phai mo
 *    tung cai de biet ben trong co gi - dung kieu tuong tac lam mat
 *    mach. Toi da nam buoc thi hien het la vua mot man.
 *
 * 2. BUOC 1 KHAC HAN BON BUOC CON LAI.
 *    Nen noi, chu to hon, vien cam. Cac buoc sau phang va mo hon. Mat
 *    roi vao buoc 1 truoc, va do la buoc DUY NHAT can quyet dinh bay
 *    gio. Bon buoc kia chi de biet duong con dai bao nhieu.
 *
 * 3. SUA NGAY TAI CHO.
 *    Cham vao chu la thanh o nhap, khong mo man khac. Xoa bang dau X
 *    cuoi dong - KHONG dung vuot, vi vuot o app nay da mang nghia khac
 *    o tab Ke hoach, va mot cu chi hai nghia la mot cho de nham.
 *
 *    Day khong phai tinh nang phu. De bai ADC noi ve cong viec BI GIAO
 *    RAP KHUON, khong dong dieu voi phong cach nhan thuc. Mot AI ap dat
 *    cach chia viec cua no la lap lai chinh cai rao can do, chi khac
 *    nguoi ra lenh.
 *
 * 4. MOT NUT CHINH DUY NHAT: "Bat dau buoc 1".
 *    Khong phai "Luu". Ly do: "de toi nho AI chia nho da" la mot viec
 *    CO CAM GIAC nang suat, ton hai muoi giay, va khong phai lam cai
 *    viec that. Lam ba lan la het buoi sang. Bat luong phan ra ket thuc
 *    bang HANH DONG thi no khong thanh mot cach tri hoan moi duoc.
 *    "Chi luu" van co, nhung la mot dong chu nho ben duoi.
 *
 * 5. KHONG DANH SO 1..5 TO O DAU DONG.
 *    Mot day so doc ra la "con bon cai nua". Dung cham tron nho.
 */
class PhanRaActivity : Activity() {

    private lateinit var khoi: LinearLayout
    private val tay = Handler(Looper.getMainLooper())

    private var viec = ""
    private var keHoachId: String? = null
    private var cacBuoc = mutableListOf<PhanRa.Buoc>()
    private var dangCho = false
    private var loi: String? = null
    private var cauHoi: String? = null

    override fun attachBaseContext(moi: Context) {
        super.attachBaseContext(GiaoDien.boc(moi))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        setContentView(R.layout.man_con)
        khoi = findViewById(R.id.noi_dung_con)
        ThanhTieuDe.noiCon(this, getString(R.string.pr_tieu_de))

        viec = intent.getStringExtra(EXTRA_VIEC)?.trim().orEmpty()
        keHoachId = intent.getStringExtra(EXTRA_KE_HOACH)
        if (viec.isBlank()) { finish(); return }

        goi()
    }

    override fun onDestroy() {
        super.onDestroy()
        tay.removeCallbacksAndMessages(null)
    }

    // ---------------------------------------------------------------

    private fun goi() {
        dangCho = true; loi = null; cauHoi = null
        ve()
        Thread {
            val kq = try {
                NguonPhanRa.chon(this).phanRa(viec, null)
            } catch (e: Exception) {
                tay.post { dangCho = false; loi = e.message ?: "?"; ve() }
                return@Thread
            }
            tay.post {
                dangCho = false
                // Tru luot SAU khi da co ket qua hop le - mat mang hay mo
                // hinh tra rac khong phai loi cua nguoi dung.
                PhanRa.truMotLuot(this)
                cauHoi = kq.can
                cacBuoc = kq.cacBuoc.toMutableList()
                ve()
            }
        }.start()
    }

    private fun ve() {
        khoi.removeAllViews()
        when {
            dangCho -> veCho()
            loi != null -> veLoi()
            cauHoi != null -> veCauHoi()
            else -> veDanhSach()
        }
        GiaoDien.apFont(findViewById(android.R.id.content), this)
    }

    /**
     * Trang thai cho: BA DONG XUONG, khong phai vong quay.
     *
     * Mot vong quay vo dinh khong cho biet con bao lau - dung cho yeu
     * cua nguoi mu thoi gian. Ba dong xuong dung hinh dang ket qua sap
     * hien ra thi vua noi "dang tai", vua cho biet no se trong the nao,
     * nen luc hien ra that khong co cu nhay bo cuc.
     */
    private fun veCho() {
        khoi.addView(chuPhu(getString(R.string.pr_dang_chia, viec)), lp(6))
        val vung = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            accessibilityLiveRegion = View.ACCESSIBILITY_LIVE_REGION_POLITE
            contentDescription = getString(R.string.pr_dang_chia, viec)
        }
        for (i in 0 until 3) {
            vung.addView(View(this).apply {
                background = GradientDrawable().apply {
                    cornerRadius = dp(14).toFloat()
                    setColor(mau(R.color.the))
                }
                alpha = 1f - i * 0.22f
            }, LinearLayout.LayoutParams(-1, dp(60)).apply { topMargin = dp(10) })
        }
        khoi.addView(vung, lp(8))
    }

    private fun veLoi() {
        khoi.addView(chuTo(getString(R.string.pr_khong_noi_duoc)), lp(20))
        khoi.addView(chuPhu(getString(R.string.pr_khong_noi_duoc_phu)), lp(8))
        khoi.addView(nutChinh(getString(R.string.pr_thu_lai)) { goi() }, lp(20))
        khoi.addView(nutChu(getString(R.string.pr_tu_chia)) { moGoRoi() }, lp(4))
    }

    /** AI noi khong du thong tin - hien dung cau hoi cua no, khong bia buoc. */
    private fun veCauHoi() {
        khoi.addView(chuTo(getString(R.string.pr_can_them)), lp(20))
        khoi.addView(chuPhu(cauHoi ?: ""), lp(8))
        khoi.addView(nutChu(getString(R.string.pr_tu_chia)) { moGoRoi() }, lp(20))
    }

    private fun veDanhSach() {
        khoi.addView(chuPhu(getString(R.string.pr_con_luot, PhanRa.conLai(this))), lp(4))
        khoi.addView(chuTo(viec, 19f), lp(6))

        for ((i, b) in cacBuoc.withIndex()) khoi.addView(theBuoc(i, b), lp(10))

        if (cacBuoc.isEmpty()) {
            khoi.addView(chuPhu(getString(R.string.pr_da_xoa_het)), lp(16))
            khoi.addView(nutChu(getString(R.string.pr_tu_chia)) { moGoRoi() }, lp(12))
            return
        }

        khoi.addView(View(this), LinearLayout.LayoutParams(-1, dp(18)))
        val dau = cacBuoc.first()
        khoi.addView(nutChinh(getString(R.string.pr_bat_dau_buoc_1, dau.phut)) {
            duyet(batDauLuon = true)
        }, lp(8))
        khoi.addView(nutChu(getString(R.string.pr_chi_luu)) { duyet(batDauLuon = false) }, lp(2))
    }

    /**
     * Mot buoc. Buoc dau tien to va noi han - xem quyet dinh 2.
     */
    private fun theBuoc(i: Int, b: PhanRa.Buoc): View {
        val dau = i == 0
        val t = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(14), dp(12), dp(10), dp(12))
            background = getDrawable(if (dau) R.drawable.nen_the_cam else R.drawable.nen_the)
        }
        t.addView(View(this).apply {
            background = GradientDrawable().apply {
                shape = GradientDrawable.OVAL
                setColor(mau(if (dau) R.color.cam else R.color.chu_phu))
            }
        }, LinearLayout.LayoutParams(dp(8), dp(8)).apply { marginEnd = dp(12) })

        val cot = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        val o = EditText(this).apply {
            setText(b.ten)
            textSize = if (dau) 17f else 15f
            setTextColor(mau(if (dau) R.color.chu else R.color.chu_phu))
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
            background = null
            setPadding(0, 0, 0, 0)
            includeFontPadding = false
            setOnFocusChangeListener { _, coTieuDiem ->
                if (!coTieuDiem) cacBuoc[i] = cacBuoc[i].copy(ten = text.toString().trim())
            }
            contentDescription = getString(R.string.pr_buoc_tren, i + 1, cacBuoc.size, b.ten, b.phut)
        }
        cot.addView(o, LinearLayout.LayoutParams(-1, -2))
        cot.addView(chuPhu(Lich.moTaPhut(b.phut, this), 12f).apply {
            setPadding(0, dp(3), 0, 0)
        })
        // Dong tu mo ho -> goi y sua, khong chan. Xem `PhanRa.moHo`.
        if (b.moHo) {
            cot.addView(chuPhu(getString(R.string.pr_mo_ho), 12f).apply {
                setTextColor(mau(R.color.cam)); setPadding(0, dp(4), 0, 0)
            })
        }
        t.addView(cot, LinearLayout.LayoutParams(0, -2, 1f))

        t.addView(ImageView(this).apply {
            setImageResource(R.drawable.ic_dong)
            setColorFilter(mau(R.color.chu_phu))
            val p = dp(10); setPadding(p, p, p, p)
            contentDescription = getString(R.string.pr_xoa_buoc, i + 1)
            setOnClickListener {
                Rung.nhe(it)
                luuChuDangGo()
                cacBuoc.removeAt(i)
                ve()
            }
        }, LinearLayout.LayoutParams(dp(40), dp(40)))
        return t
    }

    /**
     * Gom chu dang go trong cac o truoc khi ve lai.
     *
     * `setOnFocusChangeListener` chi chay khi o MAT tieu diem. Nguoi
     * dung sua buoc 2 roi bam xoa buoc 3 ngay thi o buoc 2 chua mat
     * tieu diem, va ban sua se bien mat khi ve lai.
     */
    private fun luuChuDangGo() {
        currentFocus?.clearFocus()
    }

    private fun duyet(batDauLuon: Boolean) {
        luuChuDangGo()
        val sach = cacBuoc.map { it.ten.trim() }.filter { it.isNotBlank() }
        if (sach.isEmpty()) { ve(); return }

        val cu = TrangThaiFocus.doc(this)
        TrangThaiFocus(
            dem = if (batDauLuon) DemNguoc().datThoiLuong(cacBuoc.first().phut) else cu.dem,
            ten = viec,
            buocDau = sach.joinToString("\n"),
            lyDo = cu.lyDo,
            keHoachId = keHoachId ?: cu.keHoachId,
        ).luu(this)

        findViewById<View>(android.R.id.content)?.let { Rung.xong(it) }
        setResult(RESULT_OK)
        if (batDauLuon) {
            // Da bam "Bat dau" thi chuyen NGAY, khong hoi lai. Mot hop
            // thoai xac nhan o day la mot lan nua bat quyet dinh, dung
            // luc nguoi dung vua vuot qua duoc cho kho nhat.
            ThanhTab.mo(this, FocusActivity::class.java)
        }
        finish()
    }

    private fun moGoRoi() {
        startActivity(Intent(this, GoRoiActivity::class.java))
        finish()
    }

    // ---------------------------------------------------------------

    private fun chuTo(chu: String, co: Float = 17f) = TextView(this).apply {
        text = chu; textSize = co
        typeface = Typeface.DEFAULT_BOLD
        setTextColor(mau(R.color.chu))
    }

    private fun chuPhu(chu: String, co: Float = 13.5f) = TextView(this).apply {
        text = chu; textSize = co
        setLineSpacing(0f, 1.4f)
        setTextColor(mau(R.color.chu_phu))
    }

    private fun nutChinh(chu: String, khi: () -> Unit) = TextView(this).apply {
        text = chu; textSize = 16f; gravity = Gravity.CENTER
        typeface = Typeface.DEFAULT_BOLD
        minHeight = dp(54); includeFontPadding = false
        setTextColor(mau(R.color.chu_tren_nhan))
        background = getDrawable(R.drawable.nut_chinh)
        setOnClickListener { Rung.nhe(it); khi() }
    }

    private fun nutChu(chu: String, khi: () -> Unit) = TextView(this).apply {
        text = chu; textSize = 14f; gravity = Gravity.CENTER
        minHeight = dp(46); includeFontPadding = false
        setTextColor(mau(R.color.chu_lien_ket))
        setOnClickListener { Rung.nhe(it); khi() }
    }

    private fun lp(tren: Int) = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(tren) }
    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, theme)

    companion object {
        const val EXTRA_VIEC = "viec"
        const val EXTRA_KE_HOACH = "ke_hoach"

        /**
         * Mo man phan ra. Tra ve `false` khi het luot - goi phai tu bao.
         */
        fun moDuoc(ctx: Context): Boolean = PhanRa.conLai(ctx) > 0

        fun mo(a: Activity, viec: String, keHoachId: String? = null) {
            a.startActivity(Intent(a, PhanRaActivity::class.java)
                .putExtra(EXTRA_VIEC, viec)
                .putExtra(EXTRA_KE_HOACH, keHoachId))
        }

        /**
         * Mo phan ra, hoac bao het luot.
         *
         * ----- HET LUOT KHONG DUOC CHAN DUONG -----
         *
         * Man Go roi bon cau hoi VAN MO BINH THUONG - no khong dung AI
         * va giai dung van de do. AI chi la duong nhanh hon, khong phai
         * duong duy nhat. Neu het luot ma nguoi dung mat luon kha nang
         * chia nho viec, thi do DUNG LA mot rao can thu phi voi nguoi
         * khuyet tat, va de bai ADC noi thang ve dieu do.
         *
         * Hop thoai het luot KHONG co nut "Nang cap". Thong tin ban
         * Doanh nghiep nam trong Cai dat, noi nguoi dung tu tim toi -
         * khong phai noi ho vua bi chan.
         */
        fun moHoacBao(a: Activity, viec: String, keHoachId: String? = null) {
            if (moDuoc(a)) { mo(a, viec, keHoachId); return }
            android.app.AlertDialog.Builder(a)
                .setTitle(R.string.pr_het_luot_td)
                .setMessage(R.string.pr_het_luot)
                .setPositiveButton(R.string.pr_mo_go_roi) { _, _ ->
                    a.startActivity(Intent(a, GoRoiActivity::class.java))
                }
                .setNegativeButton(R.string.huy, null)
                .hien()
        }
    }
}
