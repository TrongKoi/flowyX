package vn.adc2026.wayfinding

import android.animation.ValueAnimator
import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import android.view.accessibility.AccessibilityNodeInfo
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import kotlin.math.abs

/**
 * ====================================================================
 * THE VUOT (v5) - MOT BEN HAI VIEC, MOT BEN MOT VIEC
 * ====================================================================
 *
 *   vuot TRAI  -> lo ra HAI nut tach bach, kieu Messenger:
 *                    [✓ Xong]  nen xanh
 *                    [🗑 Xoá]  nen do
 *                 Hai nut RIENG BIET, bam dung nut minh muon. Vuot het
 *                 tay (qua 65% be ngang) thi an luon nut NGOAI CUNG -
 *                 tuc la Xoa - nhung chi khi da keo that sau.
 *
 *   vuot PHAI  -> GHIM viec len dau danh sach. Mot viec, khong co nut
 *                 nao de bam nham; vuot qua nguong la xong.
 *
 * ----- Vi sao doi so voi v4 -----
 *
 * v4 lam "phai = xoa". Hai van de:
 *   1. Xoa la hanh dong mat mat, ma vuot phai lai la chieu vuot vo tinh
 *      hay xay ra nhat khi cuon danh sach bang ngon cai.
 *   2. Voi mot hanh dong moi ben, khong con cho cho "danh dau xong" va
 *      "ghim" cung ton tai.
 * Nay: ben trai co menu hai nut (nguoi dung NHIN THAY roi moi bam), ben
 * phai la ghim - hanh dong khong mat mat gi, lo tay cung khong sao.
 *
 * ----- Mau -----
 *
 * Do CHI dung o day, cho dung mot viec la xoa that. Khong dung do de bao
 * "viec chua xong" o bat cu dau trong app.
 *
 * ----- Khong chan cuon doc -----
 *
 * Chi chiem cu cham khi di ngang ro rang: |dx| > touchSlop va
 * |dx| > 1.5|dy|. Keo xeo len xuong thi danh sach van cuon binh thuong.
 *
 * ----- TalkBack -----
 *
 * Nguoi dung trinh doc man hinh khong vuot duoc. Ca ba thao tac deu la
 * AccessibilityAction co ten, hien trong menu hanh dong cua the.
 */
@SuppressLint("ViewConstructor")
class KhungVuot(
    ctx: Context,
    private val the: View,
    private val khiXong: (() -> Unit)? = null,
    private val khiXoa: (() -> Unit)? = null,
    private val khiGhim: (() -> Unit)? = null,
    private val nhanXong: String = ctx.getString(R.string.vuot_xong),
    private val nhanGhim: String = ctx.getString(R.string.vuot_ghim),
) : FrameLayout(ctx) {

    private val nenTrai = LinearLayout(ctx).apply {          // lo ra khi vuot TRAI
        orientation = LinearLayout.HORIZONTAL
        gravity = Gravity.END
        visibility = INVISIBLE
    }
    private val nenPhai = LinearLayout(ctx).apply {          // lo ra khi vuot PHAI
        orientation = LinearLayout.HORIZONTAL
        gravity = Gravity.START or Gravity.CENTER_VERTICAL
        visibility = INVISIBLE
    }
    private val slop = ViewConfiguration.get(ctx).scaledTouchSlop
    private var x0 = 0f
    private var y0 = 0f
    private var dangKeo = false
    private var moTrai = false                                // dang mo san hai nut

    init {
        addView(nenTrai, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
        addView(nenPhai, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
        addView(the, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT))
        dungNen()
        the.accessibilityDelegate = object : AccessibilityDelegate() {
            override fun onInitializeAccessibilityNodeInfo(host: View, info: AccessibilityNodeInfo) {
                super.onInitializeAccessibilityNodeInfo(host, info)
                if (khiXong != null) info.addAction(AccessibilityNodeInfo.AccessibilityAction(ID_XONG, nhanXong))
                if (khiGhim != null) info.addAction(AccessibilityNodeInfo.AccessibilityAction(ID_GHIM, nhanGhim))
                if (khiXoa != null) info.addAction(
                    AccessibilityNodeInfo.AccessibilityAction(ID_XOA, context.getString(R.string.xoa)))
            }
            override fun performAccessibilityAction(host: View, action: Int, args: Bundle?): Boolean {
                when (action) {
                    ID_XOA -> { khiXoa?.invoke(); return true }
                    ID_XONG -> { khiXong?.invoke(); return true }
                    ID_GHIM -> { khiGhim?.invoke(); return true }
                }
                return super.performAccessibilityAction(host, action, args)
            }
        }
    }

    // ---------------------------------------------------------------
    // Nen lo ra
    // ---------------------------------------------------------------

    private fun dungNen() {
        nenTrai.removeAllViews()
        khiXong?.let { nenTrai.addView(nutNen(R.drawable.ic_tick, nhanXong, R.color.xanh_xong) { dong(); it() }) }
        khiXoa?.let { nenTrai.addView(nutNen(R.drawable.ic_thung_rac, context.getString(R.string.xoa), R.color.do_xoa) { dong(); it() }) }
        nenPhai.removeAllViews()
        khiGhim?.let {
            nenPhai.addView(nutNen(R.drawable.ic_ghim, nhanGhim, R.color.ghim, chiNhin = true))
        }
    }

    private fun nutNen(icon: Int, nhan: String, mauId: Int, chiNhin: Boolean = false,
                       khiBam: (() -> Unit)? = null) = LinearLayout(context).apply {
        orientation = LinearLayout.VERTICAL
        gravity = Gravity.CENTER
        setBackgroundColor(mau(mauId))
        layoutParams = LinearLayout.LayoutParams(dp(RONG_NUT), LinearLayout.LayoutParams.MATCH_PARENT)
        addView(ImageView(context).apply {
            setImageResource(icon)
            setColorFilter(0xFFFFFFFF.toInt())
            importantForAccessibility = IMPORTANT_FOR_ACCESSIBILITY_NO
        }, LinearLayout.LayoutParams(dp(21), dp(21)))
        addView(TextView(context).apply {
            text = nhan
            textSize = 12f
            includeFontPadding = false
            setTextColor(0xFFFFFFFF.toInt())
            typeface = Typeface.DEFAULT_BOLD
            setPadding(0, dp(5), 0, 0)
        }, LinearLayout.LayoutParams(-2, -2))
        contentDescription = nhan
        if (khiBam != null) {
            isClickable = true
            setOnClickListener { Rung.xong(this); khiBam() }
        } else if (chiNhin) {
            isClickable = false
        }
        GiaoDien.apFont(this, context)
    }

    // ---------------------------------------------------------------
    // Cu cham
    // ---------------------------------------------------------------

    /** Da di ngang du ro de chiem cu cham chua. Goi tu CA HAI duong su kien. */
    private fun batDauKeo(e: MotionEvent): Boolean {
        if (dangKeo) return true
        val dx = e.x - x0
        val dy = e.y - y0
        val huongDuoc = (dx < 0 && (khiXong != null || khiXoa != null)) ||
            (dx > 0 && (khiGhim != null || moTrai))
        if (huongDuoc && abs(dx) > slop && abs(dx) > abs(dy) * 1.5f) {
            dangKeo = true
            parent?.requestDisallowInterceptTouchEvent(true)
        }
        return dangKeo
    }

    override fun onInterceptTouchEvent(e: MotionEvent): Boolean {
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                x0 = e.x; y0 = e.y; dangKeo = false
                // Dang mo hai nut ma cham vao THE thi dong lai, khong cho bam xuyen.
                if (moTrai && e.x < width - dp(RONG_NUT * soNutTrai())) { dong(); return true }
            }
            MotionEvent.ACTION_MOVE -> return batDauKeo(e)
        }
        return dangKeo
    }

    @SuppressLint("ClickableViewAccessibility")
    override fun onTouchEvent(e: MotionEvent): Boolean {
        if (e.actionMasked == MotionEvent.ACTION_DOWN) { x0 = e.x; y0 = e.y; dangKeo = false; return true }
        if (e.actionMasked == MotionEvent.ACTION_MOVE && !batDauKeo(e)) return true
        if (!dangKeo) return false
        val goc = if (moTrai) -dp(RONG_NUT * soNutTrai()).toFloat() else 0f
        val dx = goc + (e.x - x0)
        when (e.actionMasked) {
            MotionEvent.ACTION_MOVE -> {
                val gioiHan = when {
                    dx < 0 && khiXong == null && khiXoa == null -> 0f
                    dx > 0 && khiGhim == null -> 0f
                    // Keo sang trai: cho keo qua ca hai nut mot chut de "vuot het tay".
                    dx < 0 -> dx.coerceAtLeast(-width * 0.9f)
                    else -> dx.coerceAtMost(width * 0.9f)
                }
                the.translationX = gioiHan
                veNen(gioiHan)
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                dangKeo = false
                parent?.requestDisallowInterceptTouchEvent(false)
                val tha = e.actionMasked == MotionEvent.ACTION_UP
                when {
                    // Vuot het tay sang trai -> xoa luon (khong bat bam nut nua).
                    tha && dx < -width * NGUONG_HET && khiXoa != null ->
                        truot(-width.toFloat()) { Rung.xong(this); khiXoa.invoke() }
                    // Keo vua du -> giu mo hai nut de nguoi dung CHON.
                    tha && dx < -dp(RONG_NUT).toFloat() * 0.6f && soNutTrai() > 0 -> mo()
                    // Vuot phai qua nguong -> ghim.
                    tha && dx > width * NGUONG_GHIM && khiGhim != null ->
                        truot(0f) { Rung.xong(this); khiGhim.invoke() }
                    else -> dong()
                }
            }
        }
        return true
    }

    private fun soNutTrai() = (if (khiXong != null) 1 else 0) + (if (khiXoa != null) 1 else 0)

    private fun veNen(dx: Float) {
        nenTrai.visibility = if (dx < 0) VISIBLE else INVISIBLE
        nenPhai.visibility = if (dx > 0) VISIBLE else INVISIBLE
        if (dx > 0) {
            // Ghim: nen tim, icon truot theo ngon tay, dam dan khi qua nguong.
            nenPhai.setBackgroundColor(mau(R.color.ghim))
            nenPhai.alpha = if (dx > width * NGUONG_GHIM) 1f else 0.72f
        }
    }

    /** Mo san hai nut va giu nguyen cho nguoi dung bam. */
    private fun mo() {
        moTrai = true
        truot(-dp(RONG_NUT * soNutTrai()).toFloat(), null)
    }

    /** Dong lai ve vi tri thuong. */
    fun dong() {
        moTrai = false
        truot(0f, null)
    }

    private fun truot(toi: Float, sau: (() -> Unit)?) {
        ValueAnimator.ofFloat(the.translationX, toi).apply {
            duration = 170
            addUpdateListener { the.translationX = it.animatedValue as Float; veNen(the.translationX) }
            addListener(object : android.animation.AnimatorListenerAdapter() {
                override fun onAnimationEnd(a: android.animation.Animator) {
                    if (toi == 0f) { the.translationX = 0f; veNen(0f) }
                    sau?.invoke()
                }
            })
            start()
        }
    }

    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    private fun mau(id: Int) = resources.getColor(id, context.theme)

    companion object {
        /** Be ngang mot nut lo ra. 78dp: du cho icon + chu, du rong de bam. */
        const val RONG_NUT = 78

        /** Vuot het tay sang trai qua muc nay = xoa luon. */
        const val NGUONG_HET = 0.65f

        /** Vuot phai qua muc nay = ghim. Thap hon vi ghim khong mat gi. */
        const val NGUONG_GHIM = 0.30f

        private const val ID_XOA = 0x7f0f0001
        private const val ID_XONG = 0x7f0f0002
        private const val ID_GHIM = 0x7f0f0003
    }
}
