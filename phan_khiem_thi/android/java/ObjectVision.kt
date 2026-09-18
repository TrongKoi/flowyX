package vn.adc2026.wayfinding

import android.graphics.Rect
import android.media.Image
import android.util.Log
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.objects.DetectedObject
import com.google.mlkit.vision.objects.ObjectDetection
import com.google.mlkit.vision.objects.defaults.ObjectDetectorOptions
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference

/**
 * Nhan dien do vat bang ML Kit, chay TREN MAY.
 *
 * --------------------------------------------------------------------
 * LOP NAY CHI NHIN. LOI QUYET DINH O CHO KHAC
 * --------------------------------------------------------------------
 *
 * No tra ve danh sach hop bao kem nhan, roi gui nguyen sang laptop.
 * Viec CHON NOI GI nam o `wayfinding/objects.py`.
 *
 * Chia nhu vay vi hai nen tang co hai bo nhan dien khac nhau (ML Kit
 * ben Android, Vision ben iOS) nhung quy tac "noi gi" phai giong het
 * nhau. De o mot cho thi mot bo test kiem duoc ca hai ban, va phan de
 * sai nhat - chon noi cai gi trong so muoi vat cung trong khung hinh -
 * duoc kiem thu ma khong can may.
 *
 * --------------------------------------------------------------------
 * TOA DO CHUAN HOA
 * --------------------------------------------------------------------
 *
 * Hop bao gui di dang 0..1 so voi khung hinh, khong phai diem anh. Hai
 * nen tang tra anh khac kich thuoc, va chuan hoa ngay tren may thi
 * phia laptop khong can biet may nao dang gui.
 *
 * --------------------------------------------------------------------
 * CHAY BAT DONG BO, BO KHUNG KHI BAN
 * --------------------------------------------------------------------
 *
 * ML Kit mat 20-60ms moi khung. Goi dong bo trong vong lap ve se tut
 * fps va lam VIO kem theo. Nen lop nay nhan mot khung, tra ngay ket qua
 * GAN NHAT, va bo qua khung moi neu lan truoc chua xong.
 *
 * Bo khung la dung: xu ly khung MOI NHAT quan trong hon xu ly du moi
 * khung - cung ly do voi gioi han hang doi o `bridge.py`.
 */
class ObjectVision {

    /** Mot vat nhin thay, toa do da chuan hoa 0..1. */
    data class Box(
        val nhan: String,
        val diem: Float,
        val x0: Float,
        val y0: Float,
        val x1: Float,
        val y1: Float,
    )

    private val dangChay = AtomicBoolean(false)
    private val ketQua = AtomicReference<List<Box>>(emptyList())

    private val detector by lazy {
        ObjectDetection.getClient(
            ObjectDetectorOptions.Builder()
                // STREAM_MODE bam vat qua cac khung hinh, nen nhan on
                // dinh hon va it nhay lung tung giua cac khung.
                .setDetectorMode(ObjectDetectorOptions.STREAM_MODE)
                .enableMultipleObjects()
                .enableClassification()
                .build()
        )
    }

    /** Ket qua gan nhat. Khong bao gio chan luong goi. */
    fun latest(): List<Box> = ketQua.get()

    /**
     * Nap mot khung hinh de nhan dien.
     *
     * Tra ve ngay lap tuc. Lan truoc chua xong thi khung nay bi BO QUA -
     * xem docstring dau lop.
     *
     * ----------------------------------------------------------------
     * PHAI SAO CHEP ANH RA, KHONG DUOC GIU THAM CHIEU
     * ----------------------------------------------------------------
     *
     * Ban truoc goi `InputImage.fromMediaImage(image, ...)`, ham nay
     * KHONG sao chep - no chi boc lay tham chieu. Ma phia goi lam:
     *
     *     frame.acquireCameraImage().use { img -> submit(img, rot) }
     *
     * `.use` DONG anh ngay khi khoi lenh ket thuc, tuc ngay sau khi
     * submit() tra ve - ma submit() tra ve TRUOC khi ML Kit chay xong.
     * Den luc luong nen cua ML Kit doc anh thi ArImage da dong:
     *
     *     FatalException: Unknown error in ArImage.getPlanes()
     *
     * Day la dung vet ngan xep da thay trong log. Loi dung-sau-khi-dong
     * kinh dien.
     *
     * Khong sua bang cach giu anh mo lau hon: ARCore chi cho giu mot so
     * it anh cung luc, va giu qua khung hinh sau se lam doi phien. Nen
     * cach dung la SAO CHEP ra NV21 roi tra anh lai ngay.
     */
    fun submit(image: Image, rotationDegrees: Int) {
        if (!dangChay.compareAndSet(false, true)) return

        val w = image.width.toFloat()
        val h = image.height.toFloat()

        val input = try {
            val nv21 = sangNv21(image)
            InputImage.fromByteArray(
                nv21, image.width, image.height, rotationDegrees,
                InputImage.IMAGE_FORMAT_NV21,
            )
        } catch (e: Exception) {
            // Bat Exception chung co chu dich: ArImage nem
            // FatalException cua ARCore, khong phai lop con cua
            // IllegalArgumentException. Bat hep thi van sap.
            Log.d(TAG, "khong doc duoc khung hinh", e)
            dangChay.set(false)
            return
        }

        detector.process(input)
            .addOnSuccessListener { objs ->
                ketQua.set(objs.mapNotNull { doiSang(it, w, h) })
            }
            .addOnFailureListener { e ->
                Log.d(TAG, "nhan dien that bai", e)
                // Giu ket qua cu thay vi xoa trang: mot khung hong khong
                // co nghia la phia truoc da trong.
            }
            .addOnCompleteListener {
                dangChay.set(false)
            }
    }

    private fun doiSang(o: DetectedObject, w: Float, h: Float): Box? {
        // ----------------------------------------------------------
        // VAT KHONG CO NHAN VAN LA VAT CAN
        // ----------------------------------------------------------
        //
        // Ban truoc: `?: return null` - khong phan loai duoc thi vut di.
        //
        // Bo phan loai mac dinh cua ML Kit chi biet NAM nhom tho
        // (Home good, Fashion good, Food, Place, Plant). Moi thu ngoai
        // nam nhom do deu ra khong nhan. Cot den, thung rac, va khoi
        // hinh hoc deu roi vao truong hop nay.
        //
        // Voi mot he TRANH VAT CAN thi "khong biet la cai gi" khong he
        // giong "khong co gi". Van noi duoc "co vat can cach 1,2 met" -
        // cau do van dung va van huu ich.
        val nhan = o.labels.maxByOrNull { it.confidence }
        val r: Rect = o.boundingBox

        return Box(
            nhan = nhan?.text ?: KHONG_RO,
            // Khong co nhan thi khong co diem phan loai. Cho 1.0 vi day
            // la do chac co VAT - thu duy nhat dang khang dinh - chu
            // khong phai do chac ve TEN cua no.
            diem = nhan?.confidence ?: 1.0f,
            x0 = (r.left / w).coerceIn(0f, 1f),
            y0 = (r.top / h).coerceIn(0f, 1f),
            x1 = (r.right / w).coerceIn(0f, 1f),
            y1 = (r.bottom / h).coerceIn(0f, 1f),
        )
    }

    fun close() {
        try {
            detector.close()
        } catch (e: Exception) {
            Log.d(TAG, "dong detector that bai", e)
        }
    }

    /**
     * Sao chep YUV_420_888 sang mot mang NV21 lien khoi.
     *
     * NV21 la: toan bo mat Y, roi den cac cap V,U xen ke nhau.
     *
     * Phai di TUNG HANG chu khong copy ca khoi: `rowStride` cua camera
     * thuong LON HON chieu rong anh (phan cung can canh le bo nho), nen
     * copy thang se keo theo rac o cuoi moi hang va lam anh xien.
     */
    private fun sangNv21(image: Image): ByteArray {
        val w = image.width
        val h = image.height
        val can = w * h * 3 / 2
        var buf = dem
        if (buf == null || buf.size != can) {
            // Giu lai giua cac khung de khong sinh rac 460 KB moi lan -
            // bo thu gom rac chay giua vong lap thoi gian thuc la dung
            // thu gay giat hinh.
            buf = ByteArray(can)
            dem = buf
        }

        val yPlane = image.planes[0]
        val uPlane = image.planes[1]
        val vPlane = image.planes[2]

        // --- mat Y ---
        var o = 0
        val yBuf = yPlane.buffer
        val yStride = yPlane.rowStride
        val hang = ByteArray(yStride)
        for (r in 0 until h) {
            yBuf.position(r * yStride)
            val n = minOf(yStride, yBuf.remaining())
            yBuf.get(hang, 0, n)
            System.arraycopy(hang, 0, buf, o, w)
            o += w
        }

        // --- mat V,U xen ke ---
        val uBuf = uPlane.buffer
        val vBuf = vPlane.buffer
        val uvRow = uPlane.rowStride
        val uvPix = uPlane.pixelStride
        for (r in 0 until h / 2) {
            for (c in 0 until w / 2) {
                val i = r * uvRow + c * uvPix
                buf[o++] = if (i < vBuf.limit()) vBuf.get(i) else 0
                buf[o++] = if (i < uBuf.limit()) uBuf.get(i) else 0
            }
        }
        return buf
    }

    private var dem: ByteArray? = null

    companion object {
        private const val TAG = "ObjectVision"

        /** Nhan cho vat thay duoc nhung khong phan loai duoc. */
        const val KHONG_RO = "unknown"
    }
}
