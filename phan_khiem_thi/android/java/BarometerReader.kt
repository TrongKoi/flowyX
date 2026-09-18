package vn.adc2026.wayfinding

import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.util.Log
import java.util.concurrent.atomic.AtomicReference

/**
 * Doc khi ap ke de biet dang o tang may.
 *
 * --------------------------------------------------------------------
 * VI SAO CAN CAM BIEN NAY
 * --------------------------------------------------------------------
 *
 * Doan trong cabin thang may la cho VIO gan nhu chac chan hong: cabin
 * kim loai kin khong co dac trung thi giac de bam, chuyen dong la THANG
 * DUNG chu khong phai ngang, va rung dong tao nhieu cho gia toc ke.
 *
 * Khi ap ke khong dinh gi toi ba van de do. No do ap suat khi quyen, ma
 * ap suat giam theo do cao - khong can nhin thay gi, khong can chuyen
 * dong ngang, khong so kim loai.
 *
 * --------------------------------------------------------------------
 * QUYEN: ANDROID VA iOS KHAC HAN NHAU
 * --------------------------------------------------------------------
 *
 * Android: KHONG can quyen gi ca. `TYPE_PRESSURE` la cam bien moi
 * truong, khong thuoc nhom nhay cam, nen chi can kiem tra may co cam
 * bien hay khong.
 *
 * iOS: CAN quyen "Chuyen dong va The chat" (Motion & Fitness), vi
 * `CMAltimeter` nam trong Core Motion. Cu the ben do phai lam:
 *
 *   1. Them `NSMotionUsageDescription` vao Info.plist. Chuoi mo ta phai
 *      noi ro CONG DUNG THAT bang tieng Viet co dau, vi day la cau
 *      nguoi dung nghe qua VoiceOver khi he thong hoi quyen:
 *
 *        "Ứng dụng dùng cảm biến áp suất để biết bạn đang ở tầng mấy,
 *         giúp chỉ đường chính xác khi đi thang máy."
 *
 *      Thieu khoa nay thi iOS KHONG hoi quyen ma GIET APP ngay khi goi
 *      CMAltimeter - loi im lang, kho tim.
 *
 *   2. Kiem `CMAltimeter.isRelativeAltitudeAvailable()` truoc khi dung.
 *
 *   3. Kiem `CMAltimeter.authorizationStatus()`. Bi tu choi thi roi ve
 *      phuong an du phong (`BoDemTangKhongCamBien` ben Python), KHONG
 *      duoc hong ca app.
 *
 *   4. QUAN TRONG: iOS chi hien hop thoai xin quyen khi app DANG CHAY
 *      O TIEN CANH va lan dau goi `startRelativeAltitudeUpdates`. Nen
 *      phai goi no som, o man hinh thiet lap, KHONG phai giua luc nguoi
 *      dung dang di trong hanh lang - luc do ho khong nhin thay hop
 *      thoai de bam dong y.
 *
 * Chinh vi diem 4 ma lop nay co ham `xinQuyenSom()`: Android khong can
 * nhung van co ham do de hai ban goi cung mot cho trong vong doi app.
 *
 * --------------------------------------------------------------------
 * CHI DUNG CHENH LECH TUONG DOI
 * --------------------------------------------------------------------
 *
 * Lop nay gui nguyen so doc Pascal sang lop quyet dinh
 * (`wayfinding/floors.py`). No KHONG tinh do cao tuyet doi, va do la co
 * y: do cao tuyet doi can ap suat quy chieu cua khu vuc, ma gia tri do
 * thay doi theo thoi tiet suot ca ngay.
 *
 * Ta chi can "da len may tang so voi luc bat dau" - mot phep tru giua
 * hai so doc cach nhau vai chuc giay, va trong khoang do thi thoi tiet
 * khong kip doi.
 */
class BarometerReader(private val context: Context) : SensorEventListener {

    private val sensorManager: SensorManager? =
        context.getSystemService(Context.SENSOR_SERVICE) as? SensorManager

    private val sensor: Sensor? =
        sensorManager?.getDefaultSensor(Sensor.TYPE_PRESSURE)

    /** So doc moi nhat, Pascal. Null nghia la chua co so doc nao. */
    private val moiNhat = AtomicReference<Float?>(null)

    private var dangChay = false

    /**
     * May co khi ap ke khong.
     *
     * Khong co KHONG phai loi: he thong van chay, chi mat kha nang tu
     * biet doi tang va phai hoi nguoi dung. Xem `BoDemTangKhongCamBien`.
     */
    fun available(): Boolean =
        sensor != null &&
            context.packageManager.hasSystemFeature(
                PackageManager.FEATURE_SENSOR_BAROMETER)

    /**
     * Ben Android khong can xin quyen gi - tra ve true ngay.
     *
     * Ham nay ton tai de hai ban Android va iOS goi CUNG MOT CHO trong
     * vong doi app. Ban iOS se hien hop thoai Motion & Fitness o day,
     * va phai goi tu man hinh thiet lap chu khong phai giua luc dang di.
     */
    fun xinQuyenSom(xong: (Boolean) -> Unit) {
        xong(available())
    }

    fun start() {
        val sm = sensorManager ?: return
        val s = sensor ?: return
        if (dangChay) return

        // SENSOR_DELAY_NORMAL la ~5 Hz. Lop quyet dinh chi can 1 Hz, con
        // lai de lam trung binh truot loc nhieu tu viec mo cua, quat gio,
        // va nguoi dung doi tu the cam dien thoai.
        //
        // Nhanh hon khong cho them thong tin gi, chi ton pin.
        dangChay = sm.registerListener(this, s, SensorManager.SENSOR_DELAY_NORMAL)
        if (!dangChay) Log.w(TAG, "khong dang ky duoc khi ap ke")
    }

    fun stop() {
        if (!dangChay) return
        sensorManager?.unregisterListener(this)
        dangChay = false
    }

    /**
     * So doc moi nhat tinh bang PASCAL, hoac null.
     *
     * Android tra hectopascal (hPa) nen phai nhan 100. Nham don vi o day
     * lam moi phep tinh tang lech 100 lan, va loi do khong lo ra ngay -
     * he thong chi don gian khong bao gio phat hien doi tang.
     */
    fun pascal(): Double? = moiNhat.get()?.let { it * 100.0 }

    override fun onSensorChanged(event: SensorEvent) {
        if (event.sensor?.type != Sensor.TYPE_PRESSURE) return
        val v = event.values.firstOrNull() ?: return
        if (!v.isFinite() || v <= 0f) return
        moiNhat.set(v)
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) = Unit

    companion object {
        private const val TAG = "Barometer"
    }
}
