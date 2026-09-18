package vn.adc2026.frontend

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.graphics.Typeface
import android.os.Bundle
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.roundToInt
import kotlin.math.sin

/**
 * ====================================================================
 * DONG HO TAP TRUNG - CO CHE TIIMO (v5)
 * ====================================================================
 *
 * Mot VANH khac vach bao quanh mot MAT tron. Phan thoi gian da chon duoc
 * to mau tren vanh; dau vanh co mot TAY CAM de keo. Mot vong = 60 phut,
 * gio thu hai la vanh mong ben ngoai, toi da 2 tieng.
 *
 * ----- Bon quyet dinh, va ly do -----
 *
 * 1. MAT TUYET DOI 60 PHUT, khong phai "luon day luc bat dau".
 *    15 phut LUC NAO cung la mot phan tu vanh. Nguoi mu thoi gian khong
 *    thieu con so - ho thieu cam nhan "15 phut dai co nao". Voi vanh
 *    luon day thi 15 phut va 90 phut trong y het nhau, khong hoc duoc gi.
 *
 * 2. KHONG HIEN GIAY. Giay nhay lien tuc keo mat nhin va tao lo au. O
 *    giua chi co SO PHUT; mat vanh chi ghi bon moc 15 / 30 / 45 / 60.
 *    Duoi mot phut thi ghi "sap xong" chu khong dem lui tung giay.
 *
 * 3. MAU DOI THEO CHANG. Con nhieu -> mau lanh (khong giuc). Con it ->
 *    vang. Sap het -> cam. Mau la mot kenh thong tin nua ve thoi gian,
 *    cho nguoi khong doc duoc con so trong mot cai liec.
 *
 * 4. RUNG LUY TIEN KHI KEO. Moi moc 5 phut co mot nhip rung; keo cang
 *    dai thi nhip cang manh, co tran an toan (xem `Rung.luyTien`). Tay
 *    "nghe" duoc do dai ma khong can nhin so.
 *
 * View nay khong biet gi ve dem nguoc: no chi ve va bao ra so phut. Logic
 * dem o `DemNguoc`, da co test tren JVM.
 */
class VongTapTrungView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyle: Int = 0,
) : View(context, attrs, defStyle) {

    /** Goi khi nguoi dung keo doi so phut (chi khi `choKeo`). */
    var khiDoiPhut: ((Int) -> Unit)? = null

    /** Goi moi khi qua mot moc 5 phut luc keo, kem ty le 0..1 de rung luy tien. */
    var khiQuaMoc: ((Float) -> Unit)? = null

    /** Cho phep keo dat gio. Dang chay thi tat, de cham nham khong doi gio. */
    var choKeo: Boolean = true

    private var conLaiPhut: Float = 25f
    private var dangChay: Boolean = false

    // Mau - Activity bom vao tu res/values(-night)/colors.xml.
    private var mauMat = Color.WHITE
    private var mauVachKhac = Color.WHITE
    private var mauRanh = Color.LTGRAY
    private var mauChu = Color.DKGRAY
    private var mauChuPhu = Color.GRAY
    private var mauConNhieu = Color.parseColor("#4A4470")
    private var mauSapDen = Color.parseColor("#E8A200")
    private var mauDiNgay = Color.parseColor("#F0663A")

    private val butMat = Paint(Paint.ANTI_ALIAS_FLAG)
    private val butVanh = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE }
    private val butVach = Paint(Paint.ANTI_ALIAS_FLAG).apply { strokeCap = Paint.Cap.ROUND }
    private val butTay = Paint(Paint.ANTI_ALIAS_FLAG)
    private val butSo = Paint(Paint.ANTI_ALIAS_FLAG).apply { textAlign = Paint.Align.CENTER }
    private val butGiua = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        textAlign = Paint.Align.CENTER; typeface = Typeface.DEFAULT_BOLD
    }
    private val butNhan = Paint(Paint.ANTI_ALIAS_FLAG).apply { textAlign = Paint.Align.CENTER }
    private val oVanh = RectF()
    private val duong = Path()

    private var nhanGiua = "25"
    private var nhanDuoi = "PHÚT"

    // Trang thai keo: goc cong don de keo qua 60 phut thi sang gio thu hai.
    private var gocTruoc = 0.0
    private var phutKeo = 25.0
    private var mocTruoc = 5

    init {
        isFocusable = true
        importantForAccessibility = IMPORTANT_FOR_ACCESSIBILITY_YES
    }

    fun datMau(mat: Int, vachKhac: Int, ranh: Int, chu: Int, chuPhu: Int,
               conNhieu: Int, sapDen: Int, diNgay: Int) {
        mauMat = mat; mauVachKhac = vachKhac; mauRanh = ranh
        mauChu = chu; mauChuPhu = chuPhu
        mauConNhieu = conNhieu; mauSapDen = sapDen; mauDiNgay = diNgay
        invalidate()
    }

    fun datFont(thuong: Typeface?, dam: Typeface?) {
        butSo.typeface = thuong; butNhan.typeface = thuong
        butGiua.typeface = dam ?: Typeface.DEFAULT_BOLD
        invalidate()
    }

    /**
     * @param conLai so phut con lai (co the le)
     * @param chay   dang dem nguoc hay dang dat gio
     * @param giua   chu o giua mat (so phut, hoac "Sắp xong")
     * @param duoi   nhan nho duoi so ("PHÚT" / "PHÚT CÒN LẠI")
     */
    fun dat(conLai: Float, chay: Boolean, giua: String, duoi: String) {
        conLaiPhut = conLai.coerceIn(0f, TOI_DA)
        dangChay = chay
        nhanGiua = giua; nhanDuoi = duoi
        contentDescription = "$giua $duoi"
        invalidate()
    }

    /** Dong bo khi so phut doi tu ngoai (chip chon nhanh). */
    fun datPhutKeo(p: Int) {
        phutKeo = p.toDouble().coerceIn(1.0, TOI_DA.toDouble())
        mocTruoc = (phutKeo / 5).toInt()
    }

    private fun mauChang(): Int = when {
        !dangChay || conLaiPhut > 45f -> mauConNhieu
        conLaiPhut > 10f -> mauSapDen
        else -> mauDiNgay
    }

    override fun onMeasure(w: Int, h: Int) {
        val rong = MeasureSpec.getSize(w)
        val cao = if (MeasureSpec.getMode(h) == MeasureSpec.UNSPECIFIED) rong
                  else min(rong, MeasureSpec.getSize(h))
        setMeasuredDimension(rong, cao)
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val d = min(width, height).toFloat()
        if (d <= 0f) return
        val cx = width / 2f
        val cy = height / 2f
        val rNgoai = d / 2f - d * 0.02f
        val dayVanh = d * 0.096f                 // be day cua vanh khac vach
        val rVanh = rNgoai - dayVanh / 2f - d * 0.022f
        val rMat = rVanh - dayVanh / 2f - d * 0.012f
        val mau = mauChang()

        // 1. Vanh nen (phan chua chon)
        butVanh.color = mauRanh
        butVanh.strokeWidth = dayVanh
        canvas.drawCircle(cx, cy, rVanh, butVanh)

        // 2. Phan da chon - gio dau
        val gioDau = min(conLaiPhut, 60f)
        oVanh.set(cx - rVanh, cy - rVanh, cx + rVanh, cy + rVanh)
        if (gioDau > 0f) {
            butVanh.color = mau
            canvas.drawArc(oVanh, -90f, 360f * gioDau / 60f, false, butVanh)
        }

        // 3. Vach khac - ve DE LEN vanh bang mau nen, trong nhu khac vao
        for (i in 0 until SO_VACH) {
            val goc = Math.toRadians(i * (360.0 / SO_VACH) - 90.0)
            val moc5 = i % (SO_VACH / 12) == 0
            val dai = if (moc5) dayVanh * 0.62f else dayVanh * 0.40f
            butVach.color = mauVachKhac
            butVach.strokeWidth = if (moc5) d * 0.0095f else d * 0.006f
            val r1 = rVanh + dayVanh / 2f - d * 0.004f
            val r2 = r1 - dai
            canvas.drawLine(
                cx + r1 * cos(goc).toFloat(), cy + r1 * sin(goc).toFloat(),
                cx + r2 * cos(goc).toFloat(), cy + r2 * sin(goc).toFloat(), butVach)
        }

        // 4. Gio thu hai: vanh mong ben ngoai
        val gioHai = (conLaiPhut - 60f).coerceAtLeast(0f)
        if (gioHai > 0f) {
            val rHai = rNgoai - d * 0.012f
            butVanh.strokeWidth = d * 0.022f
            butVanh.color = mauRanh
            canvas.drawCircle(cx, cy, rHai, butVanh)
            butVanh.color = mau
            butVanh.strokeCap = Paint.Cap.ROUND
            oVanh.set(cx - rHai, cy - rHai, cx + rHai, cy + rHai)
            canvas.drawArc(oVanh, -90f, 360f * gioHai / 60f, false, butVanh)
            butVanh.strokeCap = Paint.Cap.BUTT
        }

        // 5. Mat tron o giua
        butMat.color = mauMat
        canvas.drawCircle(cx, cy, rMat, butMat)

        // 6. Bon moc gio tren mat - CHI 15 / 30 / 45 / 60
        butSo.color = mauChuPhu
        butSo.textSize = d * 0.052f
        for ((phut, nhan) in MOC) {
            val goc = Math.toRadians(phut / 60.0 * 360.0 - 90.0)
            val rr = rMat - d * 0.055f
            canvas.drawText(nhan,
                cx + rr * cos(goc).toFloat(),
                cy + rr * sin(goc).toFloat() - (butSo.descent() + butSo.ascent()) / 2, butSo)
        }

        // 7. So phut o giua
        butGiua.color = mauChu
        butGiua.textSize = if (nhanGiua.length > 3) d * 0.115f else d * 0.215f
        canvas.drawText(nhanGiua, cx, cy + butGiua.textSize * 0.33f, butGiua)
        butNhan.color = mauChuPhu
        butNhan.textSize = d * 0.048f
        butNhan.letterSpacing = 0.14f
        canvas.drawText(nhanDuoi, cx, cy + butGiua.textSize * 0.33f + d * 0.085f, butNhan)

        // 8. Tay cam o dau vanh - chi hien khi dang dat gio
        if (choKeo && !dangChay) {
            val goc = Math.toRadians(gioDau / 60.0 * 360.0 - 90.0)
            val tx = cx + rVanh * cos(goc).toFloat()
            val ty = cy + rVanh * sin(goc).toFloat()
            val rTay = dayVanh * 0.62f
            butTay.color = mauMat
            canvas.drawCircle(tx, ty, rTay, butTay)
            butTay.color = mau
            butTay.style = Paint.Style.STROKE
            butTay.strokeWidth = d * 0.011f
            canvas.drawCircle(tx, ty, rTay, butTay)
            // mui ten nho chi chieu keo
            duong.reset()
            val a = Math.toRadians(gioDau / 60.0 * 360.0)
            val mui = rTay * 0.45f
            duong.moveTo(tx - mui * cos(a).toFloat() - mui * sin(a).toFloat(),
                         ty - mui * sin(a).toFloat() + mui * cos(a).toFloat())
            duong.lineTo(tx + mui * cos(a).toFloat() - mui * sin(a).toFloat() * 0f,
                         ty + mui * sin(a).toFloat())
            butTay.strokeWidth = d * 0.009f
            canvas.drawPath(duong, butTay)
            butTay.style = Paint.Style.FILL
        }
    }

    // ---------------------------------------------------------------
    // Keo de dat gio
    // ---------------------------------------------------------------

    /** 0 do o dinh, tang theo chieu kim dong ho. */
    private fun gocCua(x: Float, y: Float): Double {
        val a = Math.toDegrees(atan2((y - height / 2f).toDouble(), (x - width / 2f).toDouble())) + 90.0
        return (a + 360.0) % 360.0
    }

    override fun onTouchEvent(e: MotionEvent): Boolean {
        if (!choKeo || dangChay || !isEnabled) return super.onTouchEvent(e)
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                parent?.requestDisallowInterceptTouchEvent(true)
                val g = gocCua(e.x, e.y)
                // Cham xuong la NHAY toi goc do trong vong hien tai: cham vao
                // "vi tri 20 phut" thi duoc 20 phut, khong phai keo tu 25 ve.
                val vong = if (phutKeo > 60.0) 60.0 else 0.0
                phutKeo = (vong + g / 6.0).coerceIn(1.0, TOI_DA.toDouble())
                gocTruoc = g
                bao()
                return true
            }
            MotionEvent.ACTION_MOVE -> {
                val g = gocCua(e.x, e.y)
                var delta = g - gocTruoc
                if (delta > 180) delta -= 360
                if (delta < -180) delta += 360
                gocTruoc = g
                phutKeo = (phutKeo + delta / 6.0).coerceIn(1.0, TOI_DA.toDouble())
                bao()
                return true
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                parent?.requestDisallowInterceptTouchEvent(false)
                if (e.actionMasked == MotionEvent.ACTION_UP) {
                    phutKeo = phutKeo.roundToInt().toDouble()
                    bao()
                    performClick()
                }
                return true
            }
        }
        return super.onTouchEvent(e)
    }

    override fun performClick(): Boolean = super.performClick()

    private fun bao() {
        val p = phutKeo.roundToInt().coerceIn(1, TOI_DA.toInt())
        val moc = p / 5
        if (moc != mocTruoc) {
            mocTruoc = moc
            khiQuaMoc?.invoke(p / TOI_DA)          // ty le 0..1 cho rung luy tien
        }
        khiDoiPhut?.invoke(p)
    }

    // ---------------------------------------------------------------
    // TalkBack: khong vuot vong duoc, nen co tang/giam 5 phut
    // ---------------------------------------------------------------

    override fun onInitializeAccessibilityNodeInfo(info: AccessibilityNodeInfo) {
        super.onInitializeAccessibilityNodeInfo(info)
        info.className = "android.widget.SeekBar"
        if (choKeo && !dangChay) {
            info.addAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_FORWARD)
            info.addAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_BACKWARD)
        }
    }

    override fun performAccessibilityAction(action: Int, args: Bundle?): Boolean {
        if (choKeo && !dangChay) {
            val buoc = when (action) {
                AccessibilityNodeInfo.ACTION_SCROLL_FORWARD -> 5
                AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD -> -5
                else -> 0
            }
            if (buoc != 0) {
                phutKeo = (phutKeo.roundToInt() + buoc).toDouble().coerceIn(1.0, TOI_DA.toDouble())
                khiDoiPhut?.invoke(phutKeo.toInt())
                sendAccessibilityEvent(AccessibilityEvent.TYPE_VIEW_SELECTED)
                return true
            }
        }
        return super.performAccessibilityAction(action, args)
    }

    private companion object {
        const val TOI_DA = 120f
        /** 120 vach = moi vach 30 giay; cu 10 vach (5 phut) co mot vach dai. */
        const val SO_VACH = 120
        val MOC = listOf(60 to "60", 15 to "15", 30 to "30", 45 to "45")
    }
}
