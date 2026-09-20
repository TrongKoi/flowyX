package vn.adc2026.wayfinding

import android.app.AlarmManager
import android.app.Notification
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.View
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.TextView
import vn.adc2026.frontend.VongTapTrungView

/**
 * TAB FOCUS - dong ho dem nguoc truc quan, chay HAN tren may (v4).
 *
 * ================================================================
 * BON QUYET DINH
 * ================================================================
 *
 * 1. KHONG CO O NHAP BAT BUOC. Ban truoc mo tab la gap "Ban dinh lam gi?"
 *    va phai tra loi ba cau truoc khi bam gio. Voi nguoi dang te liet
 *    truoc nhiem vu, moi o bat buoc la mot buc tuong nua. Gio: vao tab la
 *    bam Bat dau duoc ngay. Ten viec, buoc dau, ly do - tat ca la TUY
 *    CHON, nam o man hinh "Go roi" (nut + tren thanh tieu de).
 *
 * 2. CHI DEM NGUOC, TOI DA 2 GIO. Xem `DemNguoc`.
 *
 * 3. MAT DONG HO TUYET DOI 60 PHUT, XOAY DE DAT. Xem `VongTapTrungView`.
 *
 * 4. NUT + NAM TREN THANH TIEU DE, CANH ICON CAI DAT, CO CHU "Go roi".
 *    Vung ngon cai (day man hinh) da co MOT nut chinh: Bat dau. Hai nut
 *    lon canh tranh o cung mot cho la hai lua chon phai can nhac - dung
 *    thu nhom nguoi dung nay kho nhat. Nut + la duong PHU, nen o tren; va
 *    co chu vi "+" tron dan khong noi no lam gi.
 *
 * Khong can laptop. Phien co laptop (buoc nho, cau hoi dung luc) van con,
 * vao tu Cai dat -> "Phien co laptop (thu nghiem)".
 */
class FocusActivity : TrangCoTab() {

    override fun tab() = ThanhTab.FOCUS

    private lateinit var tt: TrangThaiFocus
    private var vong: VongTapTrungView? = null
    private var nutBatDau: TextView? = null
    private var tvGoiY: TextView? = null
    private val tay = Handler(Looper.getMainLooper())

    private val nhip = object : Runnable {
        override fun run() {
            capNhatDongHo()
            tay.postDelayed(this, 500)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        tt = TrangThaiFocus.doc(this)
        nutHanhDong.apply {
            visibility = View.VISIBLE
            text = getString(R.string.go_roi_nut)
            contentDescription = getString(R.string.go_roi_mo_ta)
            setCompoundDrawablesRelativeWithIntrinsicBounds(
                getDrawable(R.drawable.ic_cong)?.mutate()?.apply {
                    setTint(mau(R.color.chu)); setBounds(0, 0, dp(18), dp(18))
                }, null, null, null)
            setOnClickListener {
                Rung.nhe(it)
                @Suppress("DEPRECATION")
                startActivityForResult(Intent(this@FocusActivity, GoRoiActivity::class.java), MA_GO_ROI)
            }
        }
        docYDinh(intent)
    }

    override fun onNewIntent(i: Intent) {
        super.onNewIntent(i)
        setIntent(i)
        docYDinh(i)
    }

    /** Mo tu "Bat dau viec nay" o tab Ke hoach: dien ten + thoi luong, bat dau luon. */
    private fun docYDinh(i: Intent?) {
        val id = i?.getStringExtra(EXTRA_KE_HOACH) ?: return
        i.removeExtra(EXTRA_KE_HOACH)
        val kh = SoLich.doc(this).tim(id) ?: return
        tt = TrangThaiFocus(
            dem = DemNguoc().datThoiLuong(kh.thoiLuong.coerceAtMost(DemNguoc.TOI_DA_PHUT)),
            ten = kh.ten, keHoachId = id,
        )
        batDau()
    }

    override fun onResume() {
        super.onResume()
        tay.post(nhip)
    }

    override fun onPause() {
        super.onPause()
        tay.removeCallbacks(nhip)
    }

    @Deprecated("Deprecated in Java")
    override fun onActivityResult(ma: Int, kq: Int, data: Intent?) {
        @Suppress("DEPRECATION")
        super.onActivityResult(ma, kq, data)
        if (ma == MA_GO_ROI && kq == RESULT_OK) {
            tt = TrangThaiFocus.doc(this)          // GoRoi da ghi san
            batDau()
        }
    }

    // ---------------------------------------------------------------
    // Ve
    // ---------------------------------------------------------------

    override fun ve() {
        tt = TrangThaiFocus.doc(this)
        val bay = System.currentTimeMillis()

        tieuDe(getString(if (tt.laNghi) R.string.focus_dang_nghi else R.string.tab_focus))

        // Viec dang lam - TUY CHON. Khong co thi mot dong moi, khong phai o trong.
        val tenViec = tt.ten
        them(TextView(this).apply {
            text = if (tenViec != null) getString(R.string.focus_dang_lam, tenViec)
                   else getString(R.string.focus_chua_ten)
            textSize = 14f
            setTextColor(mau(if (tenViec != null) R.color.chu else R.color.chu_phu))
            includeFontPadding = false
        }, 4)

        if (tt.ketQuaPhut != null) veKetQua()

        tt.buocDau?.let { b ->
            val t = the(vienCam = true)
            t.addView(nhan(getString(R.string.focus_buoc_dau)))
            t.addView(chuTo(b, 16f).apply { setPadding(0, dp(4), 0, 0) })
        }

        // Dong ho
        val v = VongTapTrungView(this).apply {
            // Vach khac mau NEN de trong nhu khac vao vanh (xem VongTapTrungView).
            datMau(mau(R.color.the), mau(R.color.nen), mau(R.color.dh_ranh),
                mau(R.color.chu), mau(R.color.chu_phu),
                mau(R.color.dh_con_nhieu), mau(R.color.dh_sap_den), mau(R.color.dh_di_ngay))
            datFont(GiaoDien.font(this@FocusActivity, false), GiaoDien.font(this@FocusActivity, true))
            datPhutKeo((tt.dem.tongMs / 60_000L).toInt())
            // Keo cang dai, rung cang day va manh - co tran an toan trong Rung.
            khiQuaMoc = { tyLe -> Rung.luyTien(this, tyLe) }
            khiDoiPhut = { p ->
                tt = tt.copy(dem = tt.dem.datThoiLuong(p))
                tt.luu(this@FocusActivity)
                capNhatDongHo()
            }
        }
        vong = v
        noiDung.addView(v, LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT
        ).apply { topMargin = dp(12); marginStart = dp(20); marginEnd = dp(20) })

        tvGoiY = chuPhu("", 13f).apply { gravity = Gravity.CENTER }
        them(tvGoiY!!, 4)

        // Chip nhanh - chi khi chua bat dau
        if (tt.dem.chuaBatDau) {
            val cuon = HorizontalScrollView(this).apply { isHorizontalScrollBarEnabled = false }
            val hang = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            val dangChon = (tt.dem.tongMs / 60_000L).toInt()
            for (p in DemNguoc.PHIM_TAT) {
                hang.addView(TextView(this).apply {
                    text = Lich.moTaPhut(p, this@FocusActivity)
                    contentDescription = Lich.moTaPhut(p, this@FocusActivity)
                    textSize = 14f
                    gravity = Gravity.CENTER
                    includeFontPadding = false
                    minWidth = dp(60); minHeight = dp(44)
                    setPadding(dp(12), 0, dp(12), 0)
                    background = getDrawable(R.drawable.chip)
                    isSelected = p == dangChon
                    setTextColor(mau(R.color.chu))
                    setOnClickListener {
                        Rung.nhe(it)
                        tt = tt.copy(dem = tt.dem.datThoiLuong(p)); tt.luu(this@FocusActivity)
                        vong?.datPhutKeo(p); lamMoi()
                    }
                }, LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT).apply { marginEnd = dp(8) })
            }
            cuon.addView(hang)
            them(cuon, 12)
        }

        // Nut chinh
        nutBatDau = nutChinh("") { bamNutChinh() }
        them(nutBatDau!!, 16)

        if (!tt.dem.chuaBatDau) {
            // v5: "+1 phút" chu khong phai "+5 phút". Dang chay ma con 30 giay thi
            // mot phut la du de viet not cau dang dang; nam phut la bat dau mot
            // doan moi - hai viec khac nhau.
            hang(nutPhu(getString(R.string.focus_them_1)) {
                tt = tt.copy(dem = tt.dem.themPhut(1, System.currentTimeMillis()))
                tt.luu(this); FocusBao.dat(this, tt.dem); capNhatDongHo()
            }, nutPhu(getString(R.string.focus_dung_lai)) { dungLai() }, 8)
        }

        capNhatDongHo()
        if (tt.dem.daHet(bay)) hetGio()
    }

    private fun veKetQua() {
        val phut = tt.ketQuaPhut ?: return
        val t = the(nenVang = true, tren = 12)
        t.addView(chuTo(getString(if (tt.laNghi) R.string.focus_het_nghi else R.string.focus_het_gio), 17f))
        t.addView(chuPhu(if (tt.laNghi) getString(R.string.focus_het_nghi_phu)
            else getString(R.string.focus_da_lam, Math.round(phut).toInt())).apply { setPadding(0, dp(4), 0, 0) })
        tt.lyDo?.takeIf { !tt.laNghi }?.let {
            t.addView(chuPhu(getString(R.string.focus_nhac_ly_do, it), 13f).apply { setPadding(0, dp(6), 0, 0) })
        }
        val h = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; setPadding(0, dp(12), 0, 0) }
        val lp = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        if (tt.laNghi) {
            h.addView(nutPhu(getString(R.string.focus_phien_moi)) {
                tt = TrangThaiFocus(dem = DemNguoc().datThoiLuong(25), ten = tt.ten); tt.luu(this); lamMoi()
            }, lp)
        } else {
            h.addView(nutPhu(getString(R.string.focus_nghi_5)) {
                tt = tt.copy(dem = DemNguoc().datThoiLuong(5), laNghi = true, ketQuaPhut = null)
                batDau()
            }, lp)
            h.addView(nutPhu(getString(R.string.focus_them_10)) {
                tt = tt.copy(dem = DemNguoc().datThoiLuong(10), ketQuaPhut = null)
                batDau()
            }, LinearLayout.LayoutParams(lp).apply { marginStart = dp(8) })
        }
        t.addView(h)
        t.addView(nutChu(getString(R.string.focus_xong_roi)) {
            tt = TrangThaiFocus(dem = DemNguoc().datThoiLuong((tt.dem.tongMs / 60_000L).toInt()))
            tt.luu(this); lamMoi()
        })
    }

    private fun nutChu(chu: String, khi: () -> Unit) = TextView(this).apply {
        text = chu; textSize = 14f; gravity = Gravity.CENTER
        setTextColor(mau(R.color.chu_lien_ket))
        minHeight = dp(44); includeFontPadding = false
        setPadding(0, dp(8), 0, 0)
        setOnClickListener { khi() }
    }

    private fun capNhatDongHo() {
        val v = vong ?: return
        val bay = System.currentTimeMillis()
        val d = tt.dem
        val con = d.conLaiMs(bay)
        v.choKeo = d.chuaBatDau
        // KHONG hien giay: chi so phut. Duoi mot phut thi mot chu "Sắp xong"
        // thay cho dem lui 59, 58, 57... (xem ghi chu dau VongTapTrungView).
        val phutHien = DemNguoc.soPhutHien(con)
        v.dat(
            conLai = con / 60_000f,
            chay = !d.chuaBatDau,
            giua = if (phutHien == 0) getString(R.string.focus_sap_xong) else "$phutHien",
            duoi = getString(when {
                d.chuaBatDau -> R.string.focus_phut
                d.dangDung -> R.string.dang_tam_dung
                phutHien == 0 -> R.string.focus_con_lai
                else -> R.string.focus_phut_con_lai
            }))
        nutBatDau?.text = getString(when {
            d.dangChay -> R.string.tam_dung
            d.dangDung -> R.string.tiep_tuc
            else -> R.string.bat_dau
        })
        tvGoiY?.text = if (d.dangChay) getString(R.string.focus_xong_luc,
            java.text.SimpleDateFormat("HH:mm", java.util.Locale.US).format(java.util.Date(d.ketThucLuc!!)))
            else ""
        if (d.daHet(bay)) hetGio()
    }

    // ---------------------------------------------------------------
    // Hanh dong
    // ---------------------------------------------------------------

    private fun bamNutChinh() {
        nutBatDau?.let { Rung.nhe(it) }
        val bay = System.currentTimeMillis()
        tt = when {
            tt.dem.dangChay -> tt.copy(dem = tt.dem.tamDung(bay)).also { FocusBao.huy(this) }
            else -> tt.copy(dem = tt.dem.batDau(bay), ketQuaPhut = null).also { FocusBao.dat(this, it.dem) }
        }
        tt.luu(this)
        lamMoi()
    }

    private fun batDau() {
        tt = tt.copy(dem = tt.dem.batDau(System.currentTimeMillis()), ketQuaPhut = null)
        tt.luu(this)
        FocusBao.dat(this, tt.dem)
        if (daDung) lamMoi()
    }

    private fun dungLai() {
        val truoc = tt
        tt = tt.copy(dem = tt.dem.datLai())
        tt.luu(this); FocusBao.huy(this); lamMoi()
        HoanTac.hien(this, getString(R.string.focus_da_dung)) {
            tt = truoc; tt.luu(this)
            if (tt.dem.dangChay) FocusBao.dat(this, tt.dem)
            lamMoi()
        }
    }

    private fun hetGio() {
        val bay = System.currentTimeMillis()
        if (!tt.dem.daHet(bay)) return
        val phut = tt.dem.daLamPhut(bay)
        if (!tt.laNghi) {
            SoTienDo.doc(this).apply { ghi(); luu(this@FocusActivity) }
            tt.ten?.let { ten ->
                SoThoiLuong.doc(this).apply {
                    ghi(ten, phut, tt.dem.tongMs / 60_000.0); luu(this@FocusActivity)
                }
            }
            tt.keHoachId?.let { id ->
                val lich = SoLich.doc(this); val homNay = SoLich.homNay()
                if (Lich.khoaXong(id, homNay) !in lich.daXong) lich.doiXong(this, id, homNay)
            }
        }
        tt = tt.copy(dem = tt.dem.datLai(), ketQuaPhut = phut)
        tt.luu(this)
        FocusBao.huy(this)
        vong?.let { Rung.anMung(it) }
        lamMoi()
        if (!tt.laNghi) phaoHoa()
    }

    /**
     * Hat giay roi 1.8 giay roi tu go minh ra khoi cay view.
     * Khong chop sang, khong am thanh - xem ghi chu trong `PhaoHoaView`.
     */
    private fun phaoHoa() {
        val goc = findViewById<android.widget.FrameLayout>(android.R.id.content) ?: return
        val v = vn.adc2026.frontend.PhaoHoaView(this).apply {
            datMau(mau(R.color.nhan), mau(R.color.cam), mau(R.color.ghim))
            khiXong = { (parent as? android.view.ViewGroup)?.removeView(this) }
        }
        goc.addView(v, android.widget.FrameLayout.LayoutParams(-1, -1))
        v.post { v.batDau() }
    }

    companion object {
        const val EXTRA_KE_HOACH = "ke_hoach"
        private const val MA_GO_ROI = 8101
    }
}

/** Trang thai tab Focus, luu trong SharedPreferences - song qua dong app. */
data class TrangThaiFocus(
    val dem: DemNguoc = DemNguoc(),
    val ten: String? = null,
    val buocDau: String? = null,
    val lyDo: String? = null,
    val keHoachId: String? = null,
    val laNghi: Boolean = false,
    /** Phien vua het: so phut da lam. Con gia tri thi hien the ket qua. */
    val ketQuaPhut: Double? = null,
) {
    fun luu(ctx: Context) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putString("dem", dem.toJson())
            .putString("ten", ten).putString("buoc", buocDau).putString("ly_do", lyDo)
            .putString("ke_hoach", keHoachId).putBoolean("nghi", laNghi)
            .putString("ket_qua", ketQuaPhut?.toString())
            .apply()
    }

    companion object {
        private const val PREFS = "flowy_focus"
        fun doc(ctx: Context): TrangThaiFocus {
            val p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            return TrangThaiFocus(
                dem = DemNguoc.tuJson(p.getString("dem", null)),
                ten = p.getString("ten", null)?.ifBlank { null },
                buocDau = p.getString("buoc", null)?.ifBlank { null },
                lyDo = p.getString("ly_do", null)?.ifBlank { null },
                keHoachId = p.getString("ke_hoach", null),
                laNghi = p.getBoolean("nghi", false),
                ketQuaPhut = p.getString("ket_qua", null)?.toDoubleOrNull(),
            )
        }
    }
}

/**
 * Chuong het gio Focus. App dong hay may khoa man hinh van bao.
 * Bam thong bao: mo Focus, va Back ve tab Ke hoach - khong bao gio roi
 * thang ra man hinh chinh cua may (xem `NgaXep`).
 */
object FocusBao {
    private const val MA = 30001

    fun dat(ctx: Context, dem: DemNguoc) {
        val luc = dem.ketThucLuc ?: return huy(ctx)
        val am = ctx.getSystemService(Context.ALARM_SERVICE) as? AlarmManager ?: return
        val pi = pi(ctx)
        try {
            if (BaoGio.coTheDatChinhXac(ctx)) am.setAlarmClock(AlarmManager.AlarmClockInfo(luc, pi), pi)
            else am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, luc, pi)
        } catch (_: SecurityException) {
            try { am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, luc, pi) } catch (_: SecurityException) { }
        }
    }

    fun huy(ctx: Context) {
        (ctx.getSystemService(Context.ALARM_SERVICE) as? AlarmManager)?.cancel(pi(ctx))
    }

    private fun pi(ctx: Context) = PendingIntent.getBroadcast(ctx, MA,
        Intent(ctx, Receiver::class.java),
        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

    class Receiver : BroadcastReceiver() {
        override fun onReceive(ctx: Context, intent: Intent) {
            BaoGio.taoKenh(ctx)
            val nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager ?: return
            val b = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) Notification.Builder(ctx, BaoGio.KENH)
                    else @Suppress("DEPRECATION") Notification.Builder(ctx)
            val nghi = TrangThaiFocus.doc(ctx).laNghi
            val tb = b.setContentTitle(ctx.getString(if (nghi) R.string.focus_het_nghi else R.string.focus_het_gio))
                .setContentText(ctx.getString(R.string.focus_thong_bao_phu))
                .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
                .setContentIntent(NgaXep.mo(ctx, FocusActivity::class.java, 2))
                .setAutoCancel(true)
                .build()
            try { nm.notify(MA, tb) } catch (_: SecurityException) { }
        }
    }
}

/**
 * NGAN XEP KHI MO TU THONG BAO.
 *
 * Mo thang mot man hinh tu thong bao thi ngan xep chi co man do - bam Back
 * la roi khoi app, nguoi dung "ket" o ngoai, khong biet vua o dau. Dung
 * ngan xep hai tang: tab Ke hoach ben duoi, man hinh dich ben tren.
 */
object NgaXep {
    fun mo(ctx: Context, lop: Class<*>, ma: Int): PendingIntent {
        val goc = Intent(ctx, ViecCanLamActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
        val dich = Intent(ctx, lop)
        return PendingIntent.getActivities(ctx, ma, arrayOf(goc, dich),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    }
}
