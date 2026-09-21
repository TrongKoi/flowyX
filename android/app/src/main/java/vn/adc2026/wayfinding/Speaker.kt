package vn.adc2026.wayfinding

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.os.Build
import android.media.AudioManager
import android.media.ToneGenerator
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.speech.tts.TextToSpeech
import android.util.Log
import java.util.Locale

/**
 * Dau ra cho nguoi dung: giong noi tieng Viet va rung.
 *
 * Ba luu y lay tu Muc 14 cua tai lieu huong dan:
 *   - Toc do doc: nguoi dung screen reader quen toc do NHANH hon nhieu
 *     so voi nguoi sang mat tuong. Mac dinh dat cao hon muc thay thoai
 *     mai, va phai cho chinh duoc.
 *   - Cat loi: chi dan khan cap phai cat cau dang doc do, khong xep hang.
 *   - Khong lap: viec chong lap da lam o phia laptop (run_bridge.py chi
 *     gui `say` khi cau THAY DOI), nen o day chi can cat loi dung cach.
 *
 * Tu vung rung phai KHOP voi HAPTIC_PATTERNS trong
 * adc_wayfinding/wayfinding/speech.py.
 */
class Speaker(context: Context, private val onReady: (Boolean) -> Unit) {

    private val appContext = context.applicationContext
    private var tts: TextToSpeech? = null
    private var ready = false

    /**
     * Trang thai giong tieng Viet. null = TTS chua khoi tao xong.
     *
     * Doc tu man hinh kiem tra quyen, nen phai la thuoc tinh chu khong chi
     * la mot lan goi `onReady`.
     */
    @Volatile var coGiongViet: Boolean? = null
        private set

    /** TTS co khoi tao duoc khong. false = may khong co bo doc nao. */
    @Volatile var ttsHoatDong: Boolean? = null
        private set
    private var utteranceId = 0

    /**
     * Tu vung rung - dien thoai chi co MOT motor nen dung SO NHIP thay
     * cho vi tri trai/phai. Don vi mili giay, xen ke bat/tat.
     */
    private val patterns: Map<String, LongArray> = mapOf(
        "one_pulse" to longArrayOf(0, 120),                          // re trai
        "two_pulse" to longArrayOf(0, 120, 80, 120),                 // re phai
        "three_pulse" to longArrayOf(0, 100, 60, 100, 60, 100),      // da toi dich
        "long_buzz" to longArrayOf(0, 600),                          // di lac
        "double_repeat" to longArrayOf(0, 200, 100, 200),            // nguy hiem
        // Xong mot chang - loi khen, khong phai canh bao. Phai khop
        // HAPTIC_PATTERNS ben speech.py.
        "xong_chang" to longArrayOf(0, 40, 60, 40),
    )

    private val vibrator: Vibrator? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        (appContext.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager)
            ?.defaultVibrator
    } else {
        @Suppress("DEPRECATION")
        appContext.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
    }

    init {
        tts = TextToSpeech(appContext) { status ->
            if (status != TextToSpeech.SUCCESS) {
                Log.e(TAG, "Khong khoi tao duoc TextToSpeech")
                ttsHoatDong = false
                coGiongViet = false
                onReady(false)
                return@TextToSpeech
            }
            val engine = tts ?: return@TextToSpeech
            val vi = Locale.forLanguageTag("vi-VN")
            val result = engine.setLanguage(vi)
            val ok = result != TextToSpeech.LANG_MISSING_DATA &&
                result != TextToSpeech.LANG_NOT_SUPPORTED
            if (!ok) {
                // Khong co giong tieng Viet thi VAN chay, chi la doc sai
                // giong. Van con hon khong noi gi. Nguoi dung se duoc bao
                // de cai them goi ngon ngu.
                Log.w(TAG, "May chua co giong tieng Viet")
            }
            engine.setSpeechRate(DEFAULT_RATE)
            ttsHoatDong = true
            coGiongViet = ok
            ready = true
            onReady(ok)
        }
    }

    /**
     * Doc mot cau. `urgent` thi cat ngang cau dang doc do.
     *
     * ----- GIO YEN TINH (muc 3.3) -----
     *
     * Trong khung gio yen tinh thi KHONG doc len. Chan ngay o day, cho
     * duy nhat phat ra tieng noi, thay vi di sua tung cho goi toi - thieu
     * mot cho la app van noi giua dem, va do la loi khong ai phat hien ra
     * cho toi khi no xay ra voi nguoi dung that.
     *
     * Rung KHONG bi chan: xem ghi chu dau `NhacCaiDat.kt`. Rung khong
     * danh thuc nguoi khac trong phong, va no van doc duoc khi may de
     * trong tui - thu can chan la tieng.
     */
    fun say(text: String, urgent: Boolean) {
        val engine = tts ?: return
        if (!ready || text.isBlank()) return
        if (NhacCaiDat.dangYen(appContext)) return
        val mode = if (urgent) TextToSpeech.QUEUE_FLUSH else TextToSpeech.QUEUE_ADD
        engine.speak(text, mode, null, "wf-${utteranceId++}")
    }

    /** Phat mot ma rung. Ma la, hoac may khong co motor, thi bo qua. */
    fun vibrate(pattern: String?) {
        val timings = patterns[pattern] ?: return
        val v = vibrator ?: return
        if (!v.hasVibrator()) return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            v.vibrate(VibrationEffect.createWaveform(timings, -1))
        } else {
            @Suppress("DEPRECATION")
            v.vibrate(timings, -1)
        }
    }

    /**
     * Phat mot am NGAN. Khong phai giong noi.
     *
     * Vi sao khong dung tep am thanh: them tep la them tai nguyen phai
     * dong goi, phai lo ban quyen, va phai chon do dai cho dung. Mot
     * tieng bip 90 mili giay tu ToneGenerator la du cho viec can lam -
     * bao "xong roi" ma khong chiem kenh tai.
     *
     * ToneGenerator nam trong android.media, khong phai androidx.
     *
     * Dung luong AM BAO (STREAM_NOTIFICATION) chu khong phai am nhac:
     * nguoi dung co the dang nghe nhac hoac podcast trong luc di, va am
     * bao se duoc he dieu hanh tron xuong dung cach thay vi de len.
     */
    fun playAm(ten: String?) {
        if (ten == null) return
        val (loai, ms) = when (ten) {
            // Xong mot chang: ngan va kho, nhu mot dau tich.
            "tach" -> ToneGenerator.TONE_PROP_BEEP to 90
            // Toi dich: hai nhip, ro rang hon vi day la ket thuc.
            "hoan_thanh" -> ToneGenerator.TONE_PROP_BEEP2 to 180
            else -> return
        }
        try {
            // Tao roi giai phong ngay: giu mot ToneGenerator song mai se
            // giu luon mot kenh audio, va vai may se khong cho ung dung
            // khac dung kenh do.
            val tg = ToneGenerator(AudioManager.STREAM_NOTIFICATION, 70)
            tg.startTone(loai, ms)
            Thread {
                try {
                    Thread.sleep((ms + 60).toLong())
                } catch (e: InterruptedException) {
                    Thread.currentThread().interrupt()
                }
                tg.release()
            }.apply { isDaemon = true }.start()
        } catch (e: RuntimeException) {
            // Mot so may nem khi kenh audio ban. Mot tieng bip khong
            // phat duoc KHONG duoc phep lam sap app.
        }
    }

    /**
     * Cau chi dan tu bridge co phai loai khan cap khong.
     *
     * Cach nhan biet: bridge gui kem ma rung `double_repeat` cho canh
     * bao nguy hiem, va `long_buzz` khi da di lac. Hai loai nay phai
     * cat ngang cau dang doc.
     */
    fun isUrgent(haptic: String?): Boolean =
        haptic == "double_repeat" || haptic == "long_buzz"

    fun setRate(rate: Float) {
        tts?.setSpeechRate(rate)
    }

    fun stop() {
        tts?.stop()
    }

    fun close() {
        tts?.stop()
        tts?.shutdown()
        tts = null
        ready = false
    }

    companion object {
        private const val TAG = "Speaker"

        /**
         * Mo DUNG man hinh de cai giong tieng Viet.
         *
         * Feature request tu buoi test: chi bao "vao Cai dat, muc Chuyen
         * van ban thanh giong noi" la bat nguoi dung tu tim trong mot menu
         * nhieu tang - dung chuoi thao tac nhom nay kho nhat. Nen app mo
         * thang toi do.
         *
         * Thu tu thu, dung o cai dau tien mo duoc:
         *
         *   1. ACTION_INSTALL_TTS_DATA - man hinh tai goi ngon ngu CUA BO
         *      DOC dang dung (Google TTS, Samsung TTS...). Gan dich nhat.
         *   2. com.android.settings.TTS_SETTINGS - trang TTS cua he thong,
         *      noi doi bo doc (vd tu Samsung sang Google, vi Samsung TTS
         *      thuong khong co tieng Viet).
         *   3. Trang Cai dat chung - van con hon khong mo gi.
         *
         * Tra ve false neu khong mo duoc gi.
         */
        fun moCaiDatGiongDoc(activity: Activity): Boolean {
            val thu = listOf(
                Intent(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA),
                Intent("com.android.settings.TTS_SETTINGS"),
                Intent(android.provider.Settings.ACTION_SETTINGS),
            )
            for (i in thu) {
                try {
                    activity.startActivity(i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                    return true
                } catch (_: Exception) {
                    // Thu cach tiep theo.
                }
            }
            return false
        }

        /**
         * Nhanh hon mac dinh cua he thong (1.0) mot cach co chu y.
         * Xem Muc 14: nguoi dung screen reader quen toc do cao hon nhieu.
         */
        const val DEFAULT_RATE = 1.35f
    }
}
