package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.PorterDuff
import android.graphics.PorterDuffXfermode
import android.graphics.RectF
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView

/**
 * ====================================================================
 * HUONG DAN LAN DAU - TOI NEN, SANG MOT CHO
 * ====================================================================
 *
 * Chay mot lan sau khi nguoi dung dang ky xong. Moi buoc: ca man hinh
 * toi di, DUNG MOT thanh phan duoc khoet sang, kem mot hai cau ngan.
 *
 * ----- Ba quyet dinh, va ly do -----
 *
 * 1. MOI BUOC CHI MOT THU.
 *    Cach thong thuong la mot man gioi thieu liet ke het tinh nang. Voi
 *    tri nho lam viec von da chat vat - dac diem chung cua ADHD - mot
 *    danh sach nam muc doc xong la quen muc dau. Khoet sang dung mot chi
 *    tiet thi khong con gi de chon de nhin.
 *
 * 2. CHU PHAI NGAN TOI MUC DOC DUOC TRONG MOT HOI THO.
 *    Toi da hai cau, va cau dau luon la MOT VIEC LAM DUOC, khong phai
 *    mot mo ta. "Chạm để bắt đầu 25 phút" chu khong phai "Đây là đồng hồ
 *    tập trung giúp bạn quản lý thời gian hiệu quả".
 *    Co mot bai test canh gac do dai nay - xem `HuongDanTest`.
 *
 * 3. BO QUA DUOC O MOI BUOC, VA KHONG BAO GIO HIEN LAI.
 *    Mot huong dan khong tat duoc la mot cai bay. Nut "Bỏ qua" o goc
 *    tren, luon cung mot cho, va bam mot lan la xong han.
 *
 * ----- Vi sao khoet bang PorterDuff chu khong phai bon mang toi -----
 *
 * Cach de hon la ve bon hinh chu nhat toi quanh vung can sang. Nhung
 * bon manh ghep lai luon lo duong noi khi bo goc, va khong bo tron duoc
 * vung sang. O day ve MOT lop toi phu kin roi XOA mot hinh bo goc ra
 * khoi no bang `PorterDuff.Mode.CLEAR` - vung sang sach, bo goc dung
 * bang the that ben duoi.
 *
 * Can `setLayerType(LAYER_TYPE_SOFTWARE)`: `CLEAR` khong hoat dong tren
 * lop ve phan cung cua mot View trong suot.
 */
object HuongDan {

    private const val PREFS = "flowy_huong_dan"
    private const val K_XONG = "da_xong"

    /** Da chay (hoac da bo qua) chua. */
    fun daXong(ctx: Context): Boolean =
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean(K_XONG, false)

    fun danhDauXong(ctx: Context) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putBoolean(K_XONG, true).apply()
    }

    /** Cho phep chay lai tu Cai dat. */
    fun datLai(ctx: Context) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putBoolean(K_XONG, false).apply()
    }

    /**
     * Mot buoc huong dan.
     *
     * @param idView  view can khoet sang. `null` = khong khoet, chi hien
     *                the chu o giua man (dung cho buoc mo dau va ket).
     * @param tron    khoet hinh tron thay vi bo goc - cho nut tron.
     */
    data class Buoc(
        val idView: Int?,
        val tieuDe: Int,
        val noiDung: Int,
        val tron: Boolean = false,
    )

    /**
     * Chuoi buoc chuan, chay o tab Ke hoach.
     *
     * Tat ca deu khoet sang mot muc tren THANH TAB, tru buoc mo dau va
     * buoc Cai dat. Ly do: thanh tab luon o day man hinh va khong bao
     * gio cuon di, nen khoet sang no la on dinh o moi co man hinh va moi
     * co chu. Khoet mot the trong danh sach thi the do co the nam ngoai
     * vung nhin, va luc ay lop toi phu kin ma khong co gi sang.
     *
     * Bay buoc. Khong phai muoi: moi buoc them vao la mot lan nguoi dung
     * phai quyet dinh co doc tiep khong, va den buoc thu tam thi cau tra
     * loi thuong la bo qua.
     */
    fun chuoiChuan(): List<Buoc> = listOf(
        Buoc(null, R.string.hd_chao_td, R.string.hd_chao_nd),
        Buoc(R.id.tab_viec, R.string.hd_viec_td, R.string.hd_viec_nd),
        Buoc(R.id.tab_lich, R.string.hd_lich_td, R.string.hd_lich_nd),
        Buoc(R.id.tab_focus, R.string.hd_focus_td, R.string.hd_focus_nd),
        Buoc(R.id.tab_nhat_ky, R.string.hd_suckhoe_td, R.string.hd_suckhoe_nd),
        Buoc(R.id.tab_meety, R.string.hd_meety_td, R.string.hd_meety_nd),
        Buoc(R.id.nut_cai_dat_icon, R.string.hd_caidat_td, R.string.hd_caidat_nd, tron = true),
    )

    /**
     * Hien chuoi buoc tren mot Activity.
     *
     * @param khiXong goi khi di het hoac bo qua.
     */
    fun hien(a: Activity, cacBuoc: List<Buoc>, khiXong: () -> Unit = {}) {
        if (cacBuoc.isEmpty()) { khiXong(); return }
        val goc = a.findViewById<ViewGroup>(android.R.id.content)
        val lop = LopHuongDan(a, cacBuoc) {
            danhDauXong(a)
            goc.post { goc.removeView(it) }
            khiXong()
        }
        goc.addView(lop, FrameLayout.LayoutParams(-1, -1))
    }

    // -----------------------------------------------------------------

    private class LopHuongDan(
        private val a: Activity,
        private val cacBuoc: List<Buoc>,
        private val khiDong: (View) -> Unit,
    ) : FrameLayout(a) {

        private var chiSo = 0
        private val butToi = Paint(Paint.ANTI_ALIAS_FLAG)
        private val butXoa = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            xfermode = PorterDuffXfermode(PorterDuff.Mode.CLEAR)
        }
        private val butVien = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
        }
        private val o = RectF()
        private val the = LinearLayout(a)

        init {
            // `CLEAR` khong chay tren lop ve phan cung.
            setLayerType(LAYER_TYPE_SOFTWARE, null)
            butToi.color = 0xD9000000.toInt()      // ~85% - du toi de tach han
            butVien.color = a.resources.getColor(R.color.nhan, a.theme)
            butVien.strokeWidth = dp(2).toFloat()
            isClickable = true
            isFocusable = true
            dungThe()
            veBuoc()
        }

        // ----- Vung can khoet sang -----

        private fun vungSang(): RectF? {
            val b = cacBuoc[chiSo]
            val id = b.idView ?: return null
            val v = a.findViewById<View>(id) ?: return null
            if (v.width == 0 || v.visibility != VISIBLE) return null
            val xy = IntArray(2); v.getLocationInWindow(xy)
            val cua = IntArray(2); getLocationInWindow(cua)
            val dem = dp(6)
            return RectF(
                (xy[0] - cua[0] - dem).toFloat(),
                (xy[1] - cua[1] - dem).toFloat(),
                (xy[0] - cua[0] + v.width + dem).toFloat(),
                (xy[1] - cua[1] + v.height + dem).toFloat())
        }

        override fun dispatchDraw(canvas: Canvas) {
            canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), butToi)
            vungSang()?.let { r ->
                o.set(r)
                if (cacBuoc[chiSo].tron) {
                    val bk = maxOf(o.width(), o.height()) / 2f
                    canvas.drawCircle(o.centerX(), o.centerY(), bk, butXoa)
                    canvas.drawCircle(o.centerX(), o.centerY(), bk, butVien)
                } else {
                    val bk = dp(16).toFloat()
                    canvas.drawRoundRect(o, bk, bk, butXoa)
                    canvas.drawRoundRect(o, bk, bk, butVien)
                }
            }
            super.dispatchDraw(canvas)
        }

        // Nuot moi cu cham: trong luc huong dan thi khong duoc bam trung
        // vao app ben duoi. Cham vao dau cung la sang buoc tiep - mot cu
        // chi duy nhat, khong phai tim nut.
        override fun onTouchEvent(e: MotionEvent): Boolean {
            if (e.actionMasked == MotionEvent.ACTION_UP) { Rung.nhe(this); tiep() }
            return true
        }

        // ----- The chu -----

        private fun dungThe() {
            the.orientation = LinearLayout.VERTICAL
            the.background = GradientDrawable().apply {
                cornerRadius = dp(20).toFloat()
                setColor(a.resources.getColor(R.color.the_3, a.theme))
            }
            the.setPadding(dp(18), dp(16), dp(18), dp(14))
            addView(the, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT).apply {
                marginStart = dp(20); marginEnd = dp(20)
            })

            // Nut "Bo qua" - goc tren phai, LUON o mot cho.
            addView(TextView(a).apply {
                text = a.getString(R.string.hd_bo_qua)
                textSize = 14f
                typeface = Typeface.DEFAULT_BOLD
                gravity = Gravity.CENTER
                minWidth = dp(64); minHeight = dp(44)
                setTextColor(0xFFFFFFFF.toInt())
                setOnClickListener { khiDong(this@LopHuongDan) }
            }, LayoutParams(LayoutParams.WRAP_CONTENT, LayoutParams.WRAP_CONTENT, Gravity.END or Gravity.TOP)
                .apply { topMargin = dp(10); marginEnd = dp(10) })
        }

        private fun veBuoc() {
            val b = cacBuoc[chiSo]
            the.removeAllViews()

            the.addView(TextView(a).apply {
                text = a.getString(R.string.hd_buoc_may, chiSo + 1, cacBuoc.size)
                textSize = 11f
                letterSpacing = 0.06f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(a.resources.getColor(R.color.cam, a.theme))
            })
            the.addView(TextView(a).apply {
                text = a.getString(b.tieuDe)
                textSize = 18f
                typeface = Typeface.DEFAULT_BOLD
                setTextColor(a.resources.getColor(R.color.chu, a.theme))
                setPadding(0, dp(6), 0, 0)
                if (android.os.Build.VERSION.SDK_INT >= 28) isAccessibilityHeading = true
            })
            the.addView(TextView(a).apply {
                text = a.getString(b.noiDung)
                textSize = 15f
                setLineSpacing(0f, 1.4f)
                setTextColor(a.resources.getColor(R.color.chu_phu, a.theme))
                setPadding(0, dp(8), 0, dp(4))
            })
            the.addView(TextView(a).apply {
                text = a.getString(
                    if (chiSo == cacBuoc.size - 1) R.string.hd_xong else R.string.hd_tiep)
                textSize = 15f
                typeface = Typeface.DEFAULT_BOLD
                gravity = Gravity.CENTER
                minHeight = dp(48)
                setTextColor(a.resources.getColor(R.color.chu_tren_nhan, a.theme))
                background = GradientDrawable().apply {
                    cornerRadius = dp(14).toFloat()
                    setColor(a.resources.getColor(R.color.nhan, a.theme))
                }
                setOnClickListener { Rung.nhe(it); tiep() }
            }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(12) })

            GiaoDien.apFont(the, a)
            datChoThe()
            // Trinh doc man hinh: doc ngay buoc moi, khong doi nguoi dung
            // di tim.
            the.announceForAccessibility(
                a.getString(b.tieuDe) + ". " + a.getString(b.noiDung))
            invalidate()
        }

        /**
         * The chu tranh vung sang: vung sang o nua tren thi the xuong
         * duoi, va nguoc lai. Khong co buoc nay thi the co the che dung
         * cai dang duoc chi.
         */
        private fun datChoThe() {
            val lp = the.layoutParams as LayoutParams
            val r = vungSang()
            lp.gravity = when {
                r == null -> Gravity.CENTER
                r.centerY() < height / 2f -> Gravity.BOTTOM
                else -> Gravity.TOP
            }
            lp.topMargin = if (lp.gravity == Gravity.TOP) dp(72) else 0
            lp.bottomMargin = if (lp.gravity == Gravity.BOTTOM) dp(96) else 0
            the.layoutParams = lp
        }

        override fun onLayout(changed: Boolean, l: Int, t: Int, r: Int, b: Int) {
            super.onLayout(changed, l, t, r, b)
            if (changed) { datChoThe(); invalidate() }
        }

        private fun tiep() {
            if (chiSo < cacBuoc.size - 1) { chiSo++; veBuoc() } else khiDong(this)
        }

        private fun dp(n: Int) = (n * a.resources.displayMetrics.density).toInt()
    }
}
