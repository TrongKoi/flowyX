package vn.adc2026.frontend

import android.animation.ValueAnimator
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View
import kotlin.random.Random

/**
 * PHAO HOA AN MUNG - chay mot lan khi het gio tap trung.
 *
 * ====================================================================
 * AN MUNG NHUNG KHONG GAY SOC
 * ====================================================================
 *
 * Nao ADHD thieu phan thuong tuc thi; mot dau hieu an mung ngay luc xong
 * giup viec "lam den cuoi" de lap lai hon. Nhung nguoi qua tai giac quan
 * thi mot man chop sang la cuc hinh. Nen o day:
 *
 *   · KHONG chop sang toan man hinh, khong doi mau nen.
 *   · Hat giay BAY LEN tu day man hinh, cham dan roi tan o tren (v5.1).
 *   · Chi 1.8 giay roi tu tat han; khong lap lai.
 *   · Khong am thanh - app chua bao gio phat am thanh dot ngot.
 *   · Ton trong cai dat "Xoa hieu ung" cua he thong: he so animation
 *     bang 0 thi khong ve gi ca, chi goi `khiXong` ngay.
 *
 * View nay trong suot voi cham: dat de len tren cung roi bo di khi xong.
 */
class PhaoHoaView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyle: Int = 0,
) : View(context, attrs, defStyle) {

    /** Goi khi hieu ung ket thuc - Activity go view nay ra. */
    var khiXong: (() -> Unit)? = null

    private class Hat(
        var x: Float, var y: Float, val vx: Float, val vy: Float,
        val xoay: Float, val mau: Int, val rong: Float, val cao: Float,
    )

    private val hat = ArrayList<Hat>(48)
    private val but = Paint(Paint.ANTI_ALIAS_FLAG)
    private val o = RectF()
    private var chay: ValueAnimator? = null
    private var tien = 0f
    private var mauHat = intArrayOf(Color.parseColor("#FFD400"), Color.parseColor("#F58A07"))

    init {
        isClickable = false
        isFocusable = false
        importantForAccessibility = IMPORTANT_FOR_ACCESSIBILITY_NO
    }

    fun datMau(vararg mau: Int) {
        if (mau.isNotEmpty()) mauHat = mau
    }

    /** Bat dau. Goi sau khi view da co kich thuoc (post{} tu Activity). */
    fun batDau() {
        val r = Random(System.currentTimeMillis())
        hat.clear()
        val heSo = try {
            android.provider.Settings.Global.getFloat(
                context.contentResolver, android.provider.Settings.Global.ANIMATOR_DURATION_SCALE, 1f)
        } catch (_: Exception) { 1f }
        if (heSo == 0f || width == 0) { khiXong?.invoke(); return }

        // ----- BAY LEN, KHONG ROI XUONG (muc 6.2) -----
        //
        // Ban truoc tha hat tu tren xuong. Ve mat vat ly thi giong giay vun
        // that, nhung y nghia thi nguoc: mot thu roi tu tren xuong doc ra la
        // "ket thuc", con day la luc nguoi dung vua LAM XONG mot viec.
        //
        // Bay len tu day man hinh doc ra la "di len". Va no con mot cai loi
        // thuc te: mat nguoi dung dang o GIUA man hinh, cho dong ho vua dem
        // ve khong. Hat di tu duoi len se di qua tam nhin do roi tan o tren;
        // hat roi tu tren xuong thi da qua mat truoc khi kip nhin.
        for (i in 0 until 44) {
            hat += Hat(
                x = width * (0.08f + 0.84f * r.nextFloat()),
                y = height * (1.02f + 0.06f * r.nextFloat()),
                vx = (r.nextFloat() - 0.5f) * width * 0.16f,
                vy = -height * (0.62f + 0.5f * r.nextFloat()),   // am = di len
                xoay = (r.nextFloat() - 0.5f) * 1080f,
                mau = mauHat[i % mauHat.size],
                rong = width * 0.018f,
                cao = width * 0.028f,
            )
        }
        chay?.cancel()
        chay = ValueAnimator.ofFloat(0f, 1f).apply {
            duration = 1800
            addUpdateListener { tien = it.animatedValue as Float; invalidate() }
            addListener(object : android.animation.AnimatorListenerAdapter() {
                override fun onAnimationEnd(a: android.animation.Animator) {
                    hat.clear(); invalidate(); khiXong?.invoke()
                }
            })
            start()
        }
    }

    override fun onDetachedFromWindow() {
        super.onDetachedFromWindow()
        chay?.cancel()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        if (hat.isEmpty()) return
        val t = tien
        for (h in hat) {
            // Bay len roi CHAM DAN: `vy` am, gia toc duong keo nguoc lai.
            // Cuoi hoat hinh hat gan nhu dung lai roi mo han - giong phao
            // giay that hon la bay thang len roi bien mat.
            val x = h.x + h.vx * t
            val y = h.y + h.vy * t + (-h.vy) * 0.45f * t * t
            if (y < -h.cao) continue
            but.color = h.mau
            but.alpha = (255 * (1f - t * t)).toInt().coerceIn(0, 255)
            canvas.save()
            canvas.rotate(h.xoay * t, x, y)
            o.set(x - h.rong / 2, y - h.cao / 2, x + h.rong / 2, y + h.cao / 2)
            canvas.drawRoundRect(o, h.rong * 0.25f, h.rong * 0.25f, but)
            canvas.restore()
        }
    }
}
