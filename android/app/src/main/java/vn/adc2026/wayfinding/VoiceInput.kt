package vn.adc2026.wayfinding

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import java.util.Locale

/**
 * Nghe cau nguoi dung noi, phuc vu lop xac nhan bang bien chu noi (L1).
 *
 * --------------------------------------------------------------------
 * VI SAO NHAN DANG PHAI CHAY TREN MAY
 * --------------------------------------------------------------------
 *
 * Micro nam tren dien thoai. Laptop khong nghe duoc gi, nen day la mot
 * trong nhung lop KHONG THE day sang ben kia cau noi - khac voi doc
 * bien chu, von chi can anh.
 *
 * Ket qua gui sang laptop la MOT CHUOI, con viec hieu chuoi do thanh so
 * phong thi nam o `wayfinding/braille.py`. Tach nhu vay de logic chuan
 * hoa so tieng Viet - phan de sai nhat - duoc kiem thu tren JVM/Python
 * thuong, khong can may that.
 *
 * --------------------------------------------------------------------
 * NGUOI DUNG LUON DUOC PHEP KHONG TRA LOI
 * --------------------------------------------------------------------
 *
 * Lop nay KHONG tu bat lai khi khong nghe duoc gi. Im lang la mot cau
 * tra loi hop le, va he thong ep nguoi dung noi lai la he thong lam
 * phien. Phia laptop se cho het cua so 10 giay roi nghi 60 giay.
 */
class VoiceInput(private val context: Context) {

    private var recognizer: SpeechRecognizer? = null
    private var dangNghe = false

    /** May co ho tro nhan dang giong noi khong. */
    fun available(): Boolean = SpeechRecognizer.isRecognitionAvailable(context)

    /**
     * Nghe MOT cau roi dung.
     *
     * `onResult` duoc goi voi cau nghe duoc, hoac null khi khong nghe ra
     * gi. Goi tren luong chinh.
     *
     * Khong nghe ra gi thi tra null chu KHONG doan - mot so phong doan
     * bua se di thang vao lop sua vi tri.
     */
    fun listenOnce(onResult: (String?) -> Unit) {
        if (dangNghe) return
        if (!available()) {
            Log.w(TAG, "May khong ho tro nhan dang giong noi")
            onResult(null)
            return
        }

        val r = SpeechRecognizer.createSpeechRecognizer(context)
        recognizer = r
        dangNghe = true

        var daTraLoi = false
        fun traLoi(s: String?) {
            if (daTraLoi) return
            daTraLoi = true
            dangNghe = false
            r.destroy()
            recognizer = null
            onResult(s)
        }

        r.setRecognitionListener(object : RecognitionListener {
            override fun onResults(results: Bundle?) {
                val ds = results?.getStringArrayList(
                    SpeechRecognizer.RESULTS_RECOGNITION)
                traLoi(ds?.firstOrNull()?.trim()?.takeIf { it.isNotEmpty() })
            }

            override fun onError(error: Int) {
                // Moi loi deu ve null. Khong phan biet "khong nghe thay"
                // voi "loi mang" o day: ca hai deu nghia la KHONG CO so
                // phong, va do la tat ca nhung gi ben goi can biet.
                Log.d(TAG, "khong nghe duoc, ma loi $error")
                traLoi(null)
            }

            override fun onReadyForSpeech(params: Bundle?) = Unit
            override fun onBeginningOfSpeech() = Unit
            override fun onRmsChanged(rmsdB: Float) = Unit
            override fun onBufferReceived(buffer: ByteArray?) = Unit
            override fun onEndOfSpeech() = Unit
            override fun onPartialResults(partialResults: Bundle?) = Unit
            override fun onEvent(eventType: Int, params: Bundle?) = Unit
        })

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            // Tieng Viet. May chua cai goi tieng Viet se roi ve mac dinh
            // cua he thong, va luc do so phong gan nhu chac chan nghe sai
            // - nhung van ra mot chuoi, va lop doc lai xac nhan phia
            // laptop se chan no lai.
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, VI_VN)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
        }

        try {
            r.startListening(intent)
        } catch (e: SecurityException) {
            // Thieu quyen RECORD_AUDIO
            Log.e(TAG, "khong co quyen ghi am", e)
            traLoi(null)
        }
    }

    fun cancel() {
        recognizer?.cancel()
        recognizer?.destroy()
        recognizer = null
        dangNghe = false
    }

    companion object {
        private const val TAG = "VoiceInput"
        private val VI_VN = Locale("vi", "VN").toLanguageTag()
    }
}
