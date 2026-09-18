package vn.adc2026.wayfinding

import android.util.Log
import java.io.BufferedReader
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Gui goi tin len laptop qua WiFi, tren luong nen.
 *
 * Cung nguyen tac voi AsyncSpeech va AsyncRoomSignReader ben Python
 * (issue #9, #10): viec CHAM khong bao gio duoc chay dong bo trong vong
 * lap thoi gian thuc. O day vong lap do la vong lap giao dien:
 * chan no thi man hinh dung hinh, va nguoi dung dang can mot cau tra
 * loi lai nhin thay mot app treo.
 *
 * Hang doi giu DUNG MOT goi tin. Goi tin cu khong con dang gui nua: neu
 * mang cham va co su kien moi, bo cai cu di. Xep hang chi lam do tre
 * cang luc cang lon, ma chi dan den muon thi vo dung.
 *
 * Dung HttpURLConnection cua thu vien chuan thay vi them OkHttp:
 * bot mot phu thuoc, bot mot cho co the hong luc build gap.
 */
class BridgeClient(
    @Volatile var baseUrl: String,
    private val onReply: (Reply) -> Unit,
    private val onError: (String) -> Unit,
) {
    /**
     * HAI LOAI GOI TIN, HAI CACH GIU.
     *
     * Ban cu giu DUNG MOT goi cho gui, goi moi de goi cu. Dung cho goi
     * THUONG (chi co trang thai - cai cu vo gia tri khi da co cai moi).
     * Nhung SAI cho goi co LENH: mang cham, POST truoc chua xong, nhip
     * sau 0,5 giay sinh goi thuong moi va de mat goi "Xong buoc" nguoi
     * dung vua bam. Nut bam ma khong co tac dung la loi te nhat voi nhom
     * nguoi dung nay.
     *
     *     quan trong (lenh, loi noi, cu cham, gio hen...) -> xep hang, KHONG mat
     *     thuong                                            -> chi giu cai moi nhat
     *
     * Goi quan trong luon di truoc.
     */
    private val hangQuanTrong = java.util.concurrent.LinkedBlockingQueue<String>(32)
    private val goiThuong = java.util.concurrent.atomic.AtomicReference<String?>(null)
    private val coViec = java.util.concurrent.Semaphore(0)
    private val running = AtomicBoolean(true)
    private var consecutiveErrors = 0

    @Volatile var lastRoundTripMs: Long = 0L
        private set

    private val worker = Thread({
        while (running.get()) {
            if (!coViec.tryAcquire(200, TimeUnit.MILLISECONDS)) continue
            val body = hangQuanTrong.poll() ?: goiThuong.getAndSet(null) ?: continue
            val t0 = System.currentTimeMillis()
            try {
                val reply = post("/update", body)
                lastRoundTripMs = System.currentTimeMillis() - t0
                consecutiveErrors = 0
                onReply(Payload.parseReply(reply))
            } catch (e: Exception) {
                consecutiveErrors++
                if (consecutiveErrors == 3 || consecutiveErrors % 25 == 0) {
                    onError(e.message ?: "mat ket noi")
                }
                Log.w(TAG, "POST /update hong", e)
            }
        }
    }, "bridge").apply { isDaemon = true; start() }

    /** @param quanTrong goi co lenh/loi noi/thao tac nguoi dung - khong duoc mat. */
    fun send(body: String, quanTrong: Boolean = false) {
        if (!running.get()) return
        if (quanTrong) {
            if (!hangQuanTrong.offer(body)) return      // 32 goi dang cho: mang da chet
        } else {
            goiThuong.set(body)
        }
        coViec.release()
    }

    private fun post(path: String, body: String): String {
        val conn = (URL(baseUrl.trimEnd('/') + path).openConnection() as HttpURLConnection)
        conn.requestMethod = "POST"
        conn.connectTimeout = 2000
        conn.readTimeout = 2000
        conn.doOutput = true
        conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")
        // Noi ro y dinh dung lai ket noi. Mac dinh da la keep-alive,
        // nhung ghi ra de nguoi doc sau khong tuong day la thieu sot.
        conn.setRequestProperty("Connection", "keep-alive")

        conn.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }

        val ma = conn.responseCode
        if (ma !in 200..299) {
            // PHAI doc het errorStream. Bo do dang thi socket khong tra
            // ve be duoc va lai roi vao dung canh dong dot ngot o tren.
            conn.errorStream?.use { it.readBytes() }
            throw IllegalStateException("HTTP $ma")
        }
        return conn.inputStream.bufferedReader(Charsets.UTF_8)
            .use(BufferedReader::readText)
    }

    fun close() {
        running.set(false)
        worker.interrupt()
    }

    private companion object {
        const val TAG = "BridgeClient"
    }
}
