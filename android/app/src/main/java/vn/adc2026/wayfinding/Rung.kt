package vn.adc2026.wayfinding

import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.HapticFeedbackConstants
import android.view.View

/**
 * RUNG PHAN HOI XUC GIAC - bon muc cuong do (v5).
 *
 * ====================================================================
 * VI SAO BON MUC, KHONG PHAI MOT CONG TAC BAT/TAT
 * ====================================================================
 *
 * Ban cu chi co bat/tat. Nhung hai nhom nguoi dung can hai thu khac han:
 * nguoi nhay cam giac quan thay rung mac dinh la kho chiu nhung van muon
 * mot cham rat nhe de biet thao tac da an; nguoi de may trong tui thi
 * muc mac dinh khong cam thay gi. Bon muc (Tat / Nhe / Vua / Manh) phuc
 * vu duoc ca hai dau.
 *
 * ====================================================================
 * HAI DUONG RUNG
 * ====================================================================
 *
 * 1. `nhe/tich/xong` - cac cham binh thuong. Muc "Vua" di qua
 *    `View.performHapticFeedback`, ton trong cai dat "Phan hoi cham" cua
 *    he thong va dung dung dong co rung tinh cua may. Muc Nhe va Manh
 *    can bien do khac mac dinh nen phai qua `Vibrator` voi bien do cu the.
 *
 * 2. `luyTien` - rieng cho vong xoay dong ho. Keo cang dai thi moi nhip
 *    rung cang day va manh dan, co TRAN AN TOAN: khong qua 30 ms va
 *    khong qua bien do 200/255. Rung lien tuc manh lam te tay va ton pin.
 *
 * Quyen VIBRATE da khai trong manifest. Khong co quyen thi cac ham nay
 * im lang chu khong lam sap app.
 */
object Rung {

    /** Bien do 1..255 cho tung muc (API 26+). Chi so 0 = Tat. */
    private val BIEN_DO = intArrayOf(0, 60, 130, 210)

    /** So mili giay cho mot cham, theo muc. */
    private val DO_DAI = intArrayOf(0, 8, 14, 22)

    fun nhe(v: View) = rung(v, 1)
    fun tich(v: View) = rung(v, 1)
    fun xong(v: View) = rung(v, 3)

    /** Mot cham. `nang` 1 = nhe, 2 = vua, 3 = ro (xong viec, het gio). */
    fun rung(v: View, nang: Int) {
        val muc = AppSettings(v.context).mucRung
        if (muc == 0) return
        // Muc Vua + cham binh thuong: de he thong lo, ton trong cai dat may.
        if (muc == 2 && nang <= 2) {
            v.performHapticFeedback(
                if (Build.VERSION.SDK_INT >= 27) HapticFeedbackConstants.KEYBOARD_PRESS
                else HapticFeedbackConstants.VIRTUAL_KEY)
            return
        }
        if (muc == 2 && nang >= 3) {
            v.performHapticFeedback(
                if (Build.VERSION.SDK_INT >= 30) HapticFeedbackConstants.CONFIRM
                else HapticFeedbackConstants.LONG_PRESS)
            return
        }
        val dai = (DO_DAI[muc] * if (nang >= 3) 2 else 1).toLong()
        batRung(v.context, dai, BIEN_DO[muc])
    }

    /**
     * Rung luy tien khi keo vong dong ho.
     *
     * @param tyLe 0f..1f - da keo duoc bao nhieu so voi toi da (2 tieng).
     *
     * Bien do di tu 40% den 100% cua muc nguoi dung chon, do dai 6..14 ms.
     * Nguoi dung chon muc Nhe thi tran cung thap theo - "luy tien" khong
     * bao gio vuot qua cai ho da chon.
     */
    fun luyTien(v: View, tyLe: Float) {
        val muc = AppSettings(v.context).mucRung
        if (muc == 0) return
        val t = tyLe.coerceIn(0f, 1f)
        val bienDo = (BIEN_DO[muc] * (0.4f + 0.6f * t)).toInt().coerceIn(1, 255)
        val dai = (6 + 8 * t).toLong().coerceAtMost(TRAN_MS)
        batRung(v.context, dai, bienDo)
    }

    /** Hai nhip ngan - dung khi het gio, di kem phao hoa. */
    fun anMung(v: View) {
        val muc = AppSettings(v.context).mucRung
        if (muc == 0) return
        val mau = longArrayOf(0, 18, 70, 18, 70, 36)
        try {
            may(v.context)?.let { vib ->
                if (Build.VERSION.SDK_INT >= 26) {
                    val bd = IntArray(mau.size) { i -> if (i % 2 == 1) BIEN_DO[muc] else 0 }
                    vib.vibrate(VibrationEffect.createWaveform(mau, bd, -1))
                } else {
                    @Suppress("DEPRECATION") vib.vibrate(mau, -1)
                }
            }
        } catch (_: SecurityException) {
        } catch (_: IllegalArgumentException) {
        }
    }

    private fun batRung(ctx: Context, dai: Long, bienDo: Int) {
        if (dai <= 0) return
        try {
            val vib = may(ctx) ?: return
            if (Build.VERSION.SDK_INT >= 26) {
                vib.vibrate(VibrationEffect.createOneShot(dai, bienDo.coerceIn(1, 255)))
            } else {
                @Suppress("DEPRECATION") vib.vibrate(dai)
            }
        } catch (_: SecurityException) {
        } catch (_: IllegalArgumentException) {
        }
    }

    private fun may(ctx: Context): Vibrator? =
        if (Build.VERSION.SDK_INT >= 31) {
            (ctx.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager)?.defaultVibrator
        } else {
            @Suppress("DEPRECATION") ctx.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
        }

    /** Tran an toan cho mot nhip rung luy tien. */
    private const val TRAN_MS = 30L
}
