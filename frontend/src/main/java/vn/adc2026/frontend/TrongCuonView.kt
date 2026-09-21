package vn.adc2026.frontend

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.VelocityTracker
import android.view.View
import android.view.ViewConfiguration
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.widget.Scroller
import kotlin.math.abs
import kotlin.math.roundToInt

/**
 * ====================================================================
 * TRONG CUON - mot cot so cuon duoc, kieu dong ho bao thuc iOS
 * ====================================================================
 *
 * Vi sao tu viet thay vi dung TimePickerDialog cua he thong:
 *
 *   · Hop thoai he thong mang bang mau va bo goc rieng, khong theo duoc
 *     FlowyX; giua mot man hinh kem-navy no nhin nhu mot manh vo.
 *   · NumberPicker cua he thong khong doi duoc co chu theo cai dat "co
 *     chu" cua app, nen nguoi chon cho To van thay so nho.
 *   · Cuon co quan tinh cho cam giac "quay trong" that; gõ mot dong bat
 *     ky cung nhay thang toi dong do.
 *
 * View nay CHI la mot cot. Bo chon gio = ba cot ghep lai (gio / phut /
 * nhan), ghep o `BoChonGioView`.
 *
 * Tro nang: TalkBack doc gia tri hien tai va co hanh dong tang/giam, nen
 * khong cuon duoc van dat duoc gio.
 */
class TrongCuonView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyle: Int = 0,
) : View(context, attrs, defStyle) {

    /** Cac gia tri hien trong trong. */
    var gia: List<String> = (0..23).map { "%02d".format(it) }
        set(v) { field = v; chiSo = chiSo.coerceIn(0, (v.size - 1).coerceAtLeast(0)); invalidate() }

    /** Cho phep chay vong (23 -> 00). Tat cho cac danh sach ngan. */
    var chayVong: Boolean = true

    var khiDoi: ((Int) -> Unit)? = null

    /** Chi so dang chon. */
    var chiSo: Int = 0
        set(v) {
            val moi = v.coerceIn(0, (gia.size - 1).coerceAtLeast(0))
            if (field != moi) { field = moi; khiDoi?.invoke(moi); sendAccessibilityEvent(AccessibilityEvent.TYPE_VIEW_SELECTED) }
            invalidate()
        }

    private var mauChu = Color.DKGRAY
    private var mauChuMo = Color.GRAY
    private var coChu = 0f

    private val but = Paint(Paint.ANTI_ALIAS_FLAG).apply { textAlign = Paint.Align.CENTER }
    private val truot = Scroller(context)
    /** Tam nem toi da tinh bang pixel - du xa de khong bao gio cham tran. */
    private val TAM_NEM = 100_000
    private var doDoi = 0f                       // lech so voi vi tri chuan, don vi px
    private var yTruoc = 0f
    private var dangKeo = false
    private var vt: VelocityTracker? = null
    private val slop = ViewConfiguration.get(context).scaledTouchSlop
    private val vToiDa = ViewConfiguration.get(context).scaledMaximumFlingVelocity.toFloat()

    /** Chieu cao mot dong. Ba dong hien cung luc: tren - giua - duoi. */
    private val caoDong: Float get() = height / 3f

    init {
        isFocusable = true
        importantForAccessibility = IMPORTANT_FOR_ACCESSIBILITY_YES
    }

    fun datMau(chu: Int, chuMo: Int) { mauChu = chu; mauChuMo = chuMo; invalidate() }
    fun datFont(f: Typeface?, co: Float) { but.typeface = f; coChu = co; invalidate() }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        if (gia.isEmpty()) return
        val h = caoDong
        but.textSize = if (coChu > 0f) coChu else h * 0.46f
        val cx = width / 2f
        val giua = height / 2f

        for (k in -2..2) {
            val i = chiSo + k
            val ten = when {
                i in gia.indices -> gia[i]
                chayVong && gia.isNotEmpty() -> gia[((i % gia.size) + gia.size) % gia.size]
                else -> null
            } ?: continue
            val y = giua + k * h + doDoi
            // Cang xa dong giua cang mo va cang nho - trong quay co chieu sau.
            val xa = (abs(y - giua) / h).coerceAtMost(2f)
            but.color = if (xa < 0.5f) mauChu else mauChuMo
            but.alpha = (255 * (1f - xa * 0.42f)).toInt().coerceIn(40, 255)
            val co = but.textSize * (1f - xa * 0.16f)
            val luu = but.textSize
            but.textSize = co
            canvas.drawText(ten, cx, y - (but.descent() + but.ascent()) / 2, but)
            but.textSize = luu
        }
    }

    override fun onTouchEvent(e: MotionEvent): Boolean {
        if (gia.isEmpty()) return false
        if (vt == null) vt = VelocityTracker.obtain()
        vt?.addMovement(e)
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                parent?.requestDisallowInterceptTouchEvent(true)
                truot.forceFinished(true)
                yTruoc = e.y; dangKeo = false
                return true
            }
            MotionEvent.ACTION_MOVE -> {
                val dy = e.y - yTruoc
                if (!dangKeo && abs(dy) > slop) dangKeo = true
                if (dangKeo) {
                    yTruoc = e.y
                    doDoi += dy
                    chuanHoa()
                    invalidate()
                }
                return true
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                parent?.requestDisallowInterceptTouchEvent(false)
                if (!dangKeo && e.actionMasked == MotionEvent.ACTION_UP) {
                    // Go thang vao mot dong -> nhay toi dong do.
                    val k = ((e.y - height / 2f) / caoDong).roundToInt()
                    if (k != 0) { doi(k); performClick() }
                    else performClick()
                } else {
                    vt?.computeCurrentVelocity(1000, vToiDa)
                    val v = vt?.yVelocity ?: 0f
                    nem(v)
                }
                vt?.recycle(); vt = null
                dangKeo = false
                return true
            }
        }
        return super.onTouchEvent(e)
    }

    override fun performClick(): Boolean = super.performClick()

    /** Khi keo qua nua dong thi doi chi so, giu `doDoi` trong mot dong. */
    private fun chuanHoa() {
        val h = caoDong
        while (doDoi > h / 2) { doi(-1); doDoi -= h }
        while (doDoi < -h / 2) { doi(1); doDoi += h }
    }

    private fun doi(buoc: Int) {
        var i = chiSo + buoc
        if (chayVong && gia.isNotEmpty()) i = ((i % gia.size) + gia.size) % gia.size
        chiSo = i
    }

    /**
     * ================================================================
     * QUAN TINH THAT, KHONG PHAI MOT CU NHAY (muc 5.3)
     * ================================================================
     *
     * Ban truoc tinh van toc roi NHAY thang `them` dong mot cai, sau do
     * bam nam cham ngay:
     *
     *     val them = (-v / caoDong / 4f).roundToInt()
     *     if (them != 0) doi(them)
     *     bamNamCham()
     *
     * Ket qua la trong khong bao gio QUAY. Ngon tay roi ra, con so nhay
     * sang mot gia tri khac roi dung phat - khong co giam toc, khong co
     * gi noi cho biet no da di qua bao nhieu dong. Cam giac "khung co
     * hoc" nam o day: mat nguoi doi mot vat dang chuyen dong thi cham
     * dan, va khi no khong cham dan thi nao doc ra la "hong" chu khong
     * phai "nhanh".
     *
     * Gio dung `Scroller` - dung bo giam toc cua he thong, cung duong
     * cong ma moi danh sach Android dung. `computeScroll()` duoc goi moi
     * khung hinh cho toi khi dung han, va MOI DONG DI QUA deu co mot
     * nhip rung: tai nghe duoc trong dang cham lai.
     *
     * `Scroller` da nam san trong tep nay tu dau, chi la chua ai goi toi.
     */
    private fun nem(vanToc: Float) {
        // Duoi nguong nay thi coi nhu tha tay, khong phai nem.
        if (abs(vanToc) < caoDong * 1.2f) { bamNamCham(); return }
        yTruot = 0
        truot.fling(
            0, 0, 0, vanToc.roundToInt(),
            0, 0, -TAM_NEM, TAM_NEM)
        postInvalidateOnAnimation()
    }

    /** Vi tri cuon o khung hinh truoc, de tinh phan da di duoc. */
    private var yTruot = 0

    override fun computeScroll() {
        if (!truot.computeScrollOffset()) {
            if (doDoi != 0f) bamNamCham()
            return
        }
        val y = truot.currY
        doDoi += (y - yTruot).toFloat()
        yTruot = y
        chuanHoa()
        invalidate()
        postInvalidateOnAnimation()
    }

    /**
     * Ve dong dang chon.
     *
     * Goi khi nem da dung han. Truoc day ham nay dat thang `doDoi = 0`,
     * nghia la dong dang do do bi giat ve dung cho. Gio chay not doan
     * ngan con lai trong 140 ms - trong "do" vao dung nac thay vi bi
     * giat vao.
     */
    private fun bamNamCham() {
        if (doDoi == 0f) { invalidate(); return }
        val tu = doDoi
        android.animation.ValueAnimator.ofFloat(tu, 0f).apply {
            duration = 140
            interpolator = android.view.animation.DecelerateInterpolator(1.6f)
            addUpdateListener { doDoi = it.animatedValue as Float; invalidate() }
            start()
        }
    }

    // --- Tro nang ---

    override fun onInitializeAccessibilityNodeInfo(info: AccessibilityNodeInfo) {
        super.onInitializeAccessibilityNodeInfo(info)
        info.className = "android.widget.NumberPicker"
        info.text = gia.getOrNull(chiSo)
        info.addAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_FORWARD)
        info.addAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_BACKWARD)
    }

    override fun performAccessibilityAction(action: Int, args: android.os.Bundle?): Boolean {
        when (action) {
            AccessibilityNodeInfo.ACTION_SCROLL_FORWARD -> { doi(1); return true }
            AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD -> { doi(-1); return true }
        }
        return super.performAccessibilityAction(action, args)
    }
}
