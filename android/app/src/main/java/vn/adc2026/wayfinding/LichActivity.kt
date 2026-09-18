package vn.adc2026.wayfinding

import android.app.Activity
import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/**
 * MAN HINH LICH - dai tuan + dong thoi gian cua mot ngay.
 *
 * Xem ghi chu o `res/layout/activity_lich.xml` va phan dau `Lich.kt`.
 *
 * Tra ve MainActivity (qua setResult) khi nguoi dung bam "Bat dau viec
 * nay": MainActivity dien san y dinh thuc thi tu ke hoach.
 */
class LichActivity : Activity() {

    private lateinit var so: SoLich
    private lateinit var daiTuan: LinearLayout
    private lateinit var dongThoiGian: LinearLayout
    private lateinit var tvThang: TextView
    private lateinit var tvNgay: TextView
    private lateinit var tvTomTat: TextView
    private lateinit var cuon: ScrollView

    private var ngayChon: Long = 0
    private var laMayTinhBang = false
    private val tay = Handler(Looper.getMainLooper())

    /** Ve lai moi phut de vach "Bay gio" di dung cho. */
    private val moiPhut = object : Runnable {
        override fun run() {
            veNgay()
            tay.postDelayed(this, 60_000L - System.currentTimeMillis() % 60_000L)
        }
    }

    override fun attachBaseContext(base: Context) {
        super.attachBaseContext(base)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        GiaoDien.apTheme(this)
        super.onCreate(savedInstanceState)
        laMayTinhBang = resources.configuration.smallestScreenWidthDp >= 600
        if (!laMayTinhBang) {
            requestedOrientation = android.content.pm.ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
        }
        setContentView(R.layout.activity_lich)

        daiTuan = findViewById(R.id.dai_tuan)
        dongThoiGian = findViewById(R.id.dong_thoi_gian)
        tvThang = findViewById(R.id.tv_thang)
        tvNgay = findViewById(R.id.tv_ngay)
        tvTomTat = findViewById(R.id.tv_tom_tat)
        cuon = findViewById(R.id.cuon_ngay)

        ngayChon = savedInstanceState?.getLong("ngay") ?: SoLich.homNay()

        ThanhTieuDe.noiCaiDat(this)
        // Duong vao nhap lich .ics - dat canh Cai dat tren thanh tieu de.
        findViewById<View>(R.id.nut_hanh_dong)?.apply {
            visibility = View.VISIBLE
            (this as? TextView)?.text = getString(R.string.nl_tieu_de)
            setOnClickListener {
                Rung.nhe(it)
                startActivity(Intent(this@LichActivity, NhapLichActivity::class.java))
            }
        }
        findViewById<Button>(R.id.nut_hom_nay).setOnClickListener { chonNgay(SoLich.homNay()) }
        findViewById<Button>(R.id.nut_tuan_truoc).setOnClickListener { chonNgay(ngayChon - 7) }
        findViewById<Button>(R.id.nut_tuan_sau).setOnClickListener { chonNgay(ngayChon + 7) }
        findViewById<Button>(R.id.nut_them).setOnClickListener { moSua(null) }

        batKeoTuan()

        ThanhTab.noi(this, ThanhTab.LICH)
        ChuyenLoiNhac.chayMotLan(this)
        GiaoDien.apFont(findViewById(android.R.id.content), this)
    }

    override fun onSaveInstanceState(out: Bundle) {
        super.onSaveInstanceState(out)
        out.putLong("ngay", ngayChon)
    }

    override fun onResume() {
        super.onResume()
        so = SoLich.doc(this)
        LichBao.datLai(this, so)
        veTuan()
        tay.removeCallbacks(moiPhut)
        tay.post(moiPhut)
    }

    override fun onPause() {
        super.onPause()
        HoanTac.dong()
        tay.removeCallbacks(moiPhut)
    }

    private fun chonNgay(ngay: Long) {
        ngayChon = ngay
        veTuan()
        veNgay()
    }

    /**
     * KEO NGANG TREN DAI TUAN de doi tuan.
     *
     * Hai nut mui ten van con - keo la duong THEM, khong phai duong thay.
     * Nguoi run tay, nguoi dung mot ngon, va nguoi dung TalkBack deu can
     * hai cai nut do; bo chung di de lay cu chi la doi mot nhom nguoi lay
     * mot nhom khac.
     *
     * Vi sao dai tuan DI THEO ngon tay thay vi doi ngay khi tha:
     * quet ma khong thay gi nhuc nhich la cu chi "khong biet co an khong"
     * - nguoi dung quet lai lan nua, va doi hai tuan. Keo theo ngon tay
     * cho biet cu chi da duoc nhan NGAY tu milimet dau tien, va keo chua
     * du xa thi dai tuan tu truot ve cho cu, tu no noi "chua du".
     *
     * NGUONG = 1/4 be ngang dai tuan. Duoi do thi tra ve cho cu.
     */
    private fun batKeoTuan() {
        val nguong = { daiTuan.width / 4f }
        var xDau = 0f
        var dangKeo = false

        daiTuan.setOnTouchListener { v, e ->
            when (e.actionMasked) {
                android.view.MotionEvent.ACTION_DOWN -> {
                    xDau = e.rawX; dangKeo = false; false
                }
                android.view.MotionEvent.ACTION_MOVE -> {
                    val lech = e.rawX - xDau
                    if (!dangKeo && Math.abs(lech) > 10f * resources.displayMetrics.density) {
                        dangKeo = true
                        v.parent?.requestDisallowInterceptTouchEvent(true)
                        daiTuan.animate().cancel()
                    }
                    if (dangKeo) {
                        // Chia 2: dai tuan di CHAM HON ngon tay. Cam giac
                        // "co suc can" nay noi rang day la mot dai dai hon
                        // man hinh, khong phai mot the roi keo tu do.
                        daiTuan.translationX = lech / 2f
                        daiTuan.alpha = 1f - (Math.abs(lech) / (daiTuan.width * 1.6f)).coerceAtMost(0.45f)
                    }
                    dangKeo
                }
                android.view.MotionEvent.ACTION_UP,
                android.view.MotionEvent.ACTION_CANCEL -> {
                    if (!dangKeo) return@setOnTouchListener false
                    dangKeo = false
                    val lech = e.rawX - xDau
                    if (e.actionMasked == android.view.MotionEvent.ACTION_UP &&
                        Math.abs(lech) > nguong()) {
                        // Keo sang PHAI la di ve QUA KHU - cung chieu voi
                        // viec keo mot to lich sang phai de lo trang truoc.
                        doiTuan(if (lech > 0) -7L else 7L, lech > 0)
                    } else {
                        traVeCho()
                    }
                    true
                }
                else -> false
            }
        }
    }

    /** Dai tuan truot han ra roi tuan moi truot vao tu phia ben kia. */
    private fun doiTuan(buoc: Long, veBenPhai: Boolean) {
        Rung.tich(daiTuan)
        val rong = daiTuan.width.toFloat()
        daiTuan.animate()
            .translationX(if (veBenPhai) rong else -rong)
            .alpha(0f)
            .setDuration(130)
            .withEndAction {
                ngayChon += buoc
                veTuan(); veNgay()
                daiTuan.translationX = if (veBenPhai) -rong else rong
                daiTuan.animate().translationX(0f).alpha(1f).setDuration(190)
                    .setInterpolator(android.view.animation.DecelerateInterpolator(1.5f))
                    .start()
            }
            .start()
    }

    private fun traVeCho() {
        daiTuan.animate().translationX(0f).alpha(1f).setDuration(170)
            .setInterpolator(android.view.animation.DecelerateInterpolator())
            .start()
    }

    // ---------------------------------------------------------------
    // Dai tuan
    // ---------------------------------------------------------------

    private fun veTuan() {
        val homNay = SoLich.homNay()
        val dau = Lich.dauTuan(ngayChon)
        val (nam, thang, _) = Lich.ngayThang(ngayChon)
        tvThang.text = getString(R.string.thang_nam, thang, nam)

        daiTuan.removeAllViews()
        for (i in 0 until 7) {
            val ngay = dau + i
            val chon = ngay == ngayChon
            val soViec = Lich.trongNgay(so.danhSach, ngay).size
            val (_, _, d) = Lich.ngayThang(ngay)

            val o = LinearLayout(this).apply {
                orientation = if (laMayTinhBang) LinearLayout.HORIZONTAL else LinearLayout.VERTICAL
                gravity = Gravity.CENTER
                setPadding(dp(4), dp(8), dp(4), dp(8))
                minimumHeight = dp(if (laMayTinhBang) 56 else 72)
                background = GradientDrawable().apply {
                    cornerRadius = dp(16).toFloat()
                    setColor(getColor(if (chon) R.color.nhan_nhat else R.color.the))
                    setStroke(dp(if (chon) 2 else 1), getColor(if (chon) R.color.nhan else R.color.vien))
                }
                isClickable = true
                isFocusable = true
                setOnClickListener { chonNgay(ngay) }
                contentDescription = Lich.tenNgay(ngay, homNay) +
                    if (soViec > 0) ", $soViec kế hoạch" else ", trống"
            }
            o.addView(TextView(this).apply {
                text = Lich.TEN_THU_NGAN[i]
                setTextColor(getColor(R.color.chu_phu))
                textSize = 13f
                gravity = Gravity.CENTER
                if (laMayTinhBang) minWidth = dp(40)
            })
            o.addView(TextView(this).apply {
                text = "$d"
                textSize = 19f
                gravity = Gravity.CENTER
                setTextColor(getColor(if (ngay == homNay) R.color.nhan else R.color.chu))
                setTypeface(typeface, Typeface.BOLD)
                if (laMayTinhBang) setPadding(dp(8), 0, dp(8), 0)
            })
            // Cham cho biet ngay co viec - khong phai so dem, khong phai muc do.
            o.addView(TextView(this).apply {
                text = when {
                    soViec == 0 -> " "
                    laMayTinhBang -> "$soViec việc"
                    else -> "•"
                }
                textSize = if (laMayTinhBang) 13f else 16f
                gravity = Gravity.CENTER
                setTextColor(getColor(R.color.nhan))
            })

            val lp = if (laMayTinhBang) {
                LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT).apply { if (i > 0) topMargin = dp(6) }
            } else {
                LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
                    .apply { if (i > 0) marginStart = dp(4) }
            }
            daiTuan.addView(o, lp)
        }
        GiaoDien.apFont(daiTuan, this)
    }

    // ---------------------------------------------------------------
    // Dong thoi gian cua ngay
    // ---------------------------------------------------------------

    private fun veNgay() {
        if (!::so.isInitialized) return
        val homNay = SoLich.homNay()
        val ds = Lich.trongNgay(so.danhSach, ngayChon)
        tvNgay.text = Lich.tenNgay(ngayChon, homNay)
        tvTomTat.text = if (ds.isEmpty()) "" else
            getString(R.string.tom_tat_ngay, ds.size, Lich.moTaPhut(ds.sumOf { it.thoiLuong }))

        dongThoiGian.removeAllViews()
        if (ds.isEmpty()) {
            dongThoiGian.addView(TextView(this).apply {
                setText(R.string.ngay_trong)
                gravity = Gravity.CENTER
                textSize = 16f
                setTextColor(getColor(R.color.chu_phu))
                setPadding(dp(16), dp(48), dp(16), dp(48))
            })
            GiaoDien.apFont(dongThoiGian, this)
            return
        }

        val bayGioPhut = if (ngayChon == homNay) (SoLich.bayGio() - homNay * 1440).toInt() else -1
        var daVeBayGio = bayGioPhut < 0
        var viTriBayGio: View? = null
        var ketThucTruoc: Int? = null

        for (kh in ds) {
            if (!daVeBayGio && bayGioPhut < kh.batDau) {
                viTriBayGio = vachBayGio(bayGioPhut)
                daVeBayGio = true
            }
            // Khoang trong dang ke giua hai viec - thoi gian nhin thay duoc.
            ketThucTruoc?.let { kt ->
                val trong = kh.batDau - kt
                if (trong >= 15) dongThoiGian.addView(dongTrong(trong))
            }
            dongThoiGian.addView(khoiKeHoach(kh))
            ketThucTruoc = maxOf(ketThucTruoc ?: 0, kh.ketThuc)
        }
        if (!daVeBayGio) viTriBayGio = vachBayGio(bayGioPhut)
        GiaoDien.apFont(dongThoiGian, this)

        // Hom nay: cuon toi vach "Bay gio" de khong phai tim.
        viTriBayGio?.let { v -> cuon.post { cuon.smoothScrollTo(0, maxOf(0, v.top - dp(120))) } }
    }

    private fun khoiKeHoach(kh: KeHoach): View {
        val xong = Lich.khoaXong(kh.id, ngayChon) in so.daXong
        val mau = intArrayOf(R.color.buoc_1, R.color.buoc_2, R.color.buoc_3,
            R.color.buoc_4, R.color.buoc_5)

        val hang = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, dp(4), 0, dp(4))
        }
        // Cot gio
        hang.addView(LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            addView(TextView(this@LichActivity).apply {
                text = Lich.gioPhut(kh.batDau)
                setTextColor(getColor(R.color.chu))
                textSize = 15f
                setTypeface(typeface, Typeface.BOLD)
            })
            addView(TextView(this@LichActivity).apply {
                text = Lich.gioPhut(kh.ketThuc)
                setTextColor(getColor(R.color.chu_phu))
                textSize = 13f
            })
        }, LinearLayout.LayoutParams(dp(58), LinearLayout.LayoutParams.WRAP_CONTENT))

        // Khoi mau: cao theo thoi luong, co tran de khong chiem ca man hinh.
        val khoi = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(14), dp(12), dp(14), dp(12))
            minimumHeight = dp((kh.thoiLuong * 1.4f).toInt().coerceIn(64, 220))
            background = GradientDrawable().apply {
                cornerRadius = dp(18).toFloat()
                setColor(getColor(mau[kh.mau.coerceIn(0, 4)]))
            }
            alpha = if (xong) 0.55f else 1f
            isClickable = true
            isFocusable = true
            setOnClickListener { hoiThaoTac(kh) }
        }
        khoi.addView(TextView(this).apply {
            text = if (xong) "✓" else kh.emoji
            textSize = 26f
            gravity = Gravity.CENTER
            setTextColor(getColor(R.color.chu))
        }, LinearLayout.LayoutParams(dp(44), LinearLayout.LayoutParams.WRAP_CONTENT))

        val chu = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(10), 0, 0, 0)
        }
        chu.addView(TextView(this).apply {
            text = kh.ten
            setTextColor(getColor(R.color.chu))
            textSize = 17f
            setTypeface(typeface, Typeface.BOLD)
        })
        val phu = buildList {
            add(Lich.moTaPhut(kh.thoiLuong))
            kh.oDau?.let { add(it) }
            if (kh.lapLai != LapLai.KHONG) add(Lich.moTaLapLai(kh.lapLai))
        }.joinToString(" · ")
        chu.addView(TextView(this).apply {
            text = phu
            setTextColor(getColor(R.color.chu))
            textSize = 14f
        })
        if (kh.nhacTruoc.isNotEmpty()) {
            chu.addView(TextView(this).apply {
                text = "🔔 " + kh.nhacTruoc.sortedDescending().joinToString(", ") { Lich.moTaNhac(it) }
                setTextColor(getColor(R.color.chu_phu))
                textSize = 13f
                setPadding(0, dp(2), 0, 0)
            })
        }
        khoi.addView(chu, LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f))

        // v4: o tron danh dau xong - MOT cham, khong phai mo hop thoai roi chon.
        khoi.addView(android.widget.ImageView(this).apply {
            val p = dp(10)
            setPadding(p, p, p, p)
            if (xong) {
                background = getDrawable(R.drawable.tron_cam)
                setImageResource(R.drawable.ic_tick)
                setColorFilter(getColor(R.color.the))
            } else {
                setImageDrawable(getDrawable(R.drawable.tron_viec))
            }
            contentDescription = getString(if (xong) R.string.kh_bo_danh_dau else R.string.kh_danh_dau_xong)
            setOnClickListener { Rung.xong(it); doiXong(kh) }
        }, LinearLayout.LayoutParams(dp(44), dp(44)).apply { marginStart = dp(6) })
        khoi.contentDescription = buildString {
            append("${Lich.gioPhut(kh.batDau)} đến ${Lich.gioPhut(kh.ketThuc)}, ${kh.ten}, $phu")
            if (xong) append(", đã xong")
        }

        // Vuot tren KHOI MAU, khong tren ca hang: cot gio dung yen lam moc.
        khoi.isClickable = true
        hang.addView(KhungVuot(this, khoi,
            khiXong = { doiXong(kh) }, khiXoa = { xoa(kh) }, khiGhim = { doiGhim(kh) }),
            LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f))
        return hang
    }

    private fun vachBayGio(phut: Int): View {
        val v = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(6), 0, dp(6))
            addView(TextView(this@LichActivity).apply {
                text = getString(R.string.bay_gio_luc, Lich.gioPhut(phut))
                setTextColor(getColor(R.color.nhan))
                textSize = 13f
                setTypeface(typeface, Typeface.BOLD)
            })
            addView(View(this@LichActivity).apply { setBackgroundColor(getColor(R.color.nhan)) },
                LinearLayout.LayoutParams(0, dp(2), 1f).apply { marginStart = dp(8) })
        }
        dongThoiGian.addView(v)
        return v
    }

    private fun dongTrong(phut: Int): View = TextView(this).apply {
        text = getString(R.string.trong_phut, Lich.moTaPhut(phut))
        setTextColor(getColor(R.color.chu_phu))
        textSize = 13f
        setPadding(dp(58), dp(2), 0, dp(2))
    }

    // ---------------------------------------------------------------
    // Thao tac
    // ---------------------------------------------------------------

    /**
     * Cham than khoi: hai lua chon thay vi bon. "Danh dau xong" va "Xoa" da
     * co thao tac truc tiep ngay tren the (o tron, vuot) - khong lap lai o day.
     */
    private fun hoiThaoTac(kh: KeHoach) {
        val xong = Lich.khoaXong(kh.id, ngayChon) in so.daXong
        val muc = mutableListOf<Pair<String, () -> Unit>>()
        if (ngayChon == SoLich.homNay() && !xong) {
            muc += getString(R.string.kh_bat_dau_viec) to {
                ThanhTab.mo(this, FocusActivity::class.java) { it.putExtra(FocusActivity.EXTRA_KE_HOACH, kh.id) }
            }
        }
        muc += getString(R.string.kh_sua) to { moSua(kh.id) }
        AlertDialog.Builder(this)
            .setTitle("${kh.emoji}  ${kh.ten}")
            .setItems(muc.map { it.first }.toTypedArray()) { _, i -> muc[i].second() }
            .setNegativeButton(R.string.huy, null)
            .hien()
    }

    private fun doiGhim(kh: KeHoach) {
        val moi = so.doiGhim(this, kh.id)
        veTuan(); veNgay()
        ThongBao.hien(this, getString(
            if (moi) R.string.da_ghim_ten else R.string.da_bo_ghim_ten, kh.ten))
    }

    private fun doiXong(kh: KeHoach) {
        so.doiXong(this, kh.id, ngayChon)
        if (Lich.khoaXong(kh.id, ngayChon) in so.daXong && ngayChon == SoLich.homNay()) {
            SoTienDo.doc(this).apply { ghi(); luu(this@LichActivity) }
        }
        LichBao.datLai(this, so)
        veTuan(); veNgay()
    }

    /** Xoa ngay, Hoan tac 5 giay - khong hop thoai xac nhan. */
    private fun xoa(kh: KeHoach) {
        val dauXong = so.daXong.filter { it.startsWith(kh.id + "|") }
        so.xoa(this, kh.id)
        LichBao.datLai(this, so)
        veTuan(); veNgay()
        HoanTac.hien(this, getString(if (kh.lapLai != LapLai.KHONG) R.string.da_xoa_lap_lai else R.string.da_xoa_ten, kh.ten)) {
            so = SoLich.doc(this)
            so.luuKeHoach(this, kh)
            so.daXong.addAll(dauXong); so.luu(this)
            LichBao.datLai(this, so)
            veTuan(); veNgay()
        }
    }

    private fun moSua(id: String?) {
        startActivity(Intent(this, KeHoachActivity::class.java)
            .putExtra(KeHoachActivity.THEM_ID, id)
            .putExtra(KeHoachActivity.THEM_NGAY, ngayChon))
    }

    private fun dp(n: Int): Int = (n * resources.displayMetrics.density).toInt()

    companion object {
        const val KET_QUA_ID = "bat_dau_id"
        const val KET_QUA_NGAY = "bat_dau_ngay"
    }
}
