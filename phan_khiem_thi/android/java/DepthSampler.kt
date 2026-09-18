package vn.adc2026.wayfinding

import android.media.Image
import com.google.ar.core.Config
import com.google.ar.core.Frame
import com.google.ar.core.Session
import com.google.ar.core.exceptions.NotYetAvailableException
import java.nio.ByteOrder
import java.nio.ShortBuffer
import kotlin.math.roundToInt

/**
 * Lay do sau tu ARCore Depth API va GOP XUONG LUOI THO ngay tren may.
 *
 * --------------------------------------------------------------------
 * VI SAO GOP TREN MAY CHU KHONG GUI ANH DAY DU
 * --------------------------------------------------------------------
 *
 * Anh do sau cua ARCore khoang 160x120 diem, moi diem 16 bit - tuc
 * ~38 KB moi khung. O nhip 8 khung/giay la ~300 KB/s lien tuc qua WiFi.
 *
 * Ma phan quyet dinh phia laptop KHONG CAN chi tiet den the: no chi hoi
 * "dai nao co vat, cach bao xa". Luoi 16x12 la 192 so - khoang 21 KB/giay
 * o nhip 8 khung, so voi ~300 KB/s neu gui ca anh.
 *
 * Gui anh day du vua lang phi bang thong vua THEM DO TRE, ma do tre la
 * thu nguy hiem truc tiep: canh bao den sau khi nguoi dung da buoc vao
 * vat can thi khong con la canh bao nua.
 *
 * --------------------------------------------------------------------
 * DEPTH-FROM-MOTION, KHONG PHAI CAM BIEN
 * --------------------------------------------------------------------
 *
 * May khong co cam bien ToF rieng (Galaxy A36 la mot vi du) van dung
 * duoc Depth API, nhung ARCore se uoc luong do sau TU CHUYEN DONG
 * CAMERA qua nhieu khung hinh. He qua thuc te phai biet truoc:
 *
 *   - Dung yen hoan toan thi do sau KEM DAN, vi khong co thi sai de
 *     tam giac hoa. Chinh luc nguoi dung dung lai de nghe ngong lai la
 *     luc so do te nhat.
 *   - Tuong trang tron khong co van thi gan nhu khong do duoc.
 *   - Vat vua xuat hien can vai khung hinh moi hien ra.
 *
 * Ca ba deu doi ve TRANG THAI CHUA BIET phia laptop, va do la ly do lop
 * do ton tai. Tuyet doi khong duoc coi `confidence` thap la "chac gan
 * dung" - phai coi la KHONG BIET.
 *
 * Hop dong JSON: xem `adc_wayfinding/wayfinding/bridge.py`.
 */
class DepthSampler(
    // --------------------------------------------------------------
    // 16x12, KHONG PHAI 4x3
    // --------------------------------------------------------------
    //
    // Luoi 4 cot chia 65 do thanh 4 o, moi o 16,25 do. Mot cot den 8 cm
    // o cu ly 2 m chi choán 2,29 do - tuc 14% mot o:
    //
    //   vat                   goc      % mot o (4 cot)   (16 cot)
    //   cot den 8cm @2m      2,29°          14%            56%
    //   chan ban 4cm @1,5m   1,53°           9%            38%
    //   gay 3cm @1m          1,72°          11%            42%
    //   canh kim tu thap     4,30°          26%           106%
    //
    // O 4 cot thi MOI vat tren deu vo hinh, bat ke thuat toan phia sau
    // tot den dau. Day la ly do that su khien dang que khong duoc phat
    // hien - khong phai loi bo nhan dien.
    //
    // Gia: 192 so thay vi 12, khoang 21 KB/giay o nhip 8 khung. Chap
    // nhan duoc; ban chay rieng tren may thi khong ton gi ca.
    private val cols: Int = 16,
    private val rows: Int = 12,
) {

    /** Ket qua mot lan lay mau. Mang san dang de Payload ghi ra JSON. */
    data class Grid(
        val cols: Int,
        val rows: Int,
        val depth: FloatArray,        // met, 0 nghia la khong do duoc
        val confidence: FloatArray,   // 0..1
    )

    var supported: Boolean = false
        private set

    /**
     * Bat che do do sau neu may ho tro.
     *
     * Goi TRUOC `session.configure(config)`. Tra ve true neu bat duoc.
     *
     * May khong ho tro thi KHONG phai loi: he thong van chay, chi mat
     * lop canh bao vat can. Bao ro roi di tiep con hon tu choi khoi
     * dong.
     */
    fun enable(session: Session, config: Config): Boolean {
        supported = session.isDepthModeSupported(Config.DepthMode.AUTOMATIC)
        config.depthMode =
            if (supported) Config.DepthMode.AUTOMATIC else Config.DepthMode.DISABLED
        return supported
    }

    /**
     * Lay mot luoi do sau tu khung hinh hien tai.
     *
     * Tra null khi chua co du lieu - chuyen binh thuong trong vai khung
     * dau, va moi khi ARCore chua tam giac hoa kip. Ben goi phai coi
     * null la "khung nay khong co do sau", KHONG phai "phia truoc
     * trong".
     */
    fun sample(frame: Frame): Grid? {
        if (!supported) return null

        // --- Uu tien cap ANH THO + DO TIN CAY THO ---
        //
        // Hai anh nay la MOT CAP KHOP NHAU tung diem. Ghep anh do sau da
        // LAM MUON (`acquireDepthImage16Bits`) voi do tin cay THO la
        // ghep nham hai anh khac nhau: toa do khong tuong ung, nen o
        // duoc gan do tin cay cua mot cho khac han.
        //
        // Loi kieu do khong lam sap gi ca - no chi lam do tin cay sai im
        // lang, va do tin cay sai chinh la thu sinh ra trang thai CHUA
        // BIET sai. Voi mot he canh bao vat can thi do la loi nguy hiem
        // dung nghia.
        var depthImage: Image? = null
        var confImage: Image? = null
        try {
            depthImage = frame.acquireRawDepthImage16Bits()
            confImage = frame.acquireRawDepthConfidenceImage()
        } catch (e: NotYetAvailableException) {
            depthImage?.close(); depthImage = null
            confImage?.close(); confImage = null
        } catch (e: UnsupportedOperationException) {
            depthImage?.close(); depthImage = null
            confImage?.close(); confImage = null
        }

        // --- Khong co anh tho thi dung anh da lam muon, KHONG kem do
        //     tin cay. Luc do do tin cay suy ra tu TY LE DIEM DOC DUOC.
        if (depthImage == null) {
            depthImage = try {
                frame.acquireDepthImage16Bits()
            } catch (e: NotYetAvailableException) {
                return null
            }
        }

        // Chot lai mot tham chieu KHONG NULL de dung o duoi.
        //
        // `depthImage` la `var Image?`, nen moi lan dung deu phai qua
        // kiem tra null lai. Khai bao mot `val` roi VAN dung `depthImage`
        // o duoi thi khong giai quyet gi ca - do la trang thai truoc
        // thay doi nay: bien `resolvedDepthImage` duoc khai bao nhung
        // khong duoc dung o dau, con hai cho ben duoi van tham chieu
        // bien nullable.
        val anh: Image = depthImage ?: return null

        try {
            return gop(anh, confImage)
        } finally {
            // PHAI dong, neu khong ARCore het bo dem sau vai chuc khung
            // va ngung tra anh do sau hoan toan.
            anh.close()
            confImage?.close()
        }
    }

    /**
     * Gop anh do sau thanh luoi cols x rows.
     *
     * Moi o lay PHAN VI 20 cua cac diem hop le trong o do.
     *
     * Khong lay trung binh: mot diem nhieu doc ra 0,2m se keo trung binh
     * xuong va sinh canh bao gia ngay truoc mat nguoi dung.
     *
     * Cung khong lay trung vi: trung vi chi "thay" duoc thu choán tren
     * mot nua o, nen vat hep - chan ban, cot den - bi xoa han. Xem ghi
     * chu dai o cho tinh ben duoi.
     */
    private fun gop(depthImage: Image, confImage: Image?): Grid {
        val w = depthImage.width
        val h = depthImage.height
        val plane = depthImage.planes[0]
        val buf: ShortBuffer = plane.buffer
            .order(ByteOrder.nativeOrder())
            .asShortBuffer()
        val rowStrideShorts = plane.rowStride / 2

        val confPlane = confImage?.planes?.get(0)
        val confBuf = confPlane?.buffer
        val confRowStride = confPlane?.rowStride ?: 0
        val confW = confImage?.width ?: 0
        val confH = confImage?.height ?: 0

        val depth = FloatArray(cols * rows)
        val conf = FloatArray(cols * rows)

        for (ry in 0 until rows) {
            for (rx in 0 until cols) {
                val x0 = w * rx / cols
                val x1 = w * (rx + 1) / cols
                val y0 = h * ry / rows
                val y1 = h * (ry + 1) / rows

                val mau = ArrayList<Float>(((x1 - x0) * (y1 - y0)) / STEP_SQ + 1)
                var tongConf = 0f
                var demConf = 0

                var y = y0
                while (y < y1) {
                    var x = x0
                    while (x < x1) {
                        // Gia tri 16 bit khong dau, don vi MILIMET.
                        // 0 nghia la ARCore khong do duoc diem nay.
                        val mm = buf.get(y * rowStrideShorts + x).toInt() and 0xFFFF
                        if (mm in MIN_MM..MAX_MM) mau.add(mm / 1000f)

                        if (confBuf != null && confW > 0 && confH > 0) {
                            val cxp = x * confW / w
                            val cyp = y * confH / h
                            val idx = cyp * confRowStride + cxp
                            if (idx < confBuf.limit()) {
                                tongConf += (confBuf.get(idx).toInt() and 0xFF) / 255f
                                demConf++
                            }
                        }
                        x += STEP
                    }
                    y += STEP
                }

                val i = ry * cols + rx
                if (mau.isEmpty()) {
                    // Khong do duoc diem nao trong o nay. Gui 0 va do tin
                    // cay 0 - phia laptop se cho ra trang thai CHUA BIET.
                    depth[i] = 0f
                    conf[i] = 0f
                } else {
                    mau.sort()
                    // ------------------------------------------------
                    // PHAN VI 20, KHONG PHAI TRUNG VI
                    // ------------------------------------------------
                    //
                    // Trung vi chi "thay" duoc thu choán TREN MOT NUA o.
                    // Ngay o luoi 16 cot, chan ban 4 cm chi choán 38%
                    // mot o - trung vi van xoa no di.
                    //
                    // Nhung lay hang MIN thi mot diem nhieu doc ra 0,2 m
                    // se sinh canh bao ngay truoc mat nguoi dung ma
                    // khong co gi ca.
                    //
                    // Phan vi 20 la diem can: vat choán tren 20% o thi
                    // lo ra, con mot diem nhieu don le (1/N so mau)
                    // khong keo noi.
                    //
                    // Docstring cua DepthGrid ben Python noi "moi o giu
                    // do sau NHO NHAT" - cau do khong dung ke ca truoc
                    // thay doi nay (code cu lay trung vi). Da sua lai
                    // ben do cho khop.
                    depth[i] = mau[(mau.size * 20) / 100]
                    conf[i] = when {
                        demConf > 0 -> tongConf / demConf
                        // Khong co anh do tin cay thi suy ra tu TY LE
                        // DIEM DOC DUOC. O ma phan lon diem doc khong ra
                        // la o khong dang tin, du vai diem con lai nhin
                        // co ve gon gang.
                        else -> (mau.size.toFloat() /
                            maxOf(1, ((x1 - x0) / STEP) * ((y1 - y0) / STEP)))
                            .coerceIn(0f, 1f)
                    }
                }
            }
        }
        return Grid(cols, rows, depth, conf)
    }

    companion object {
        /**
         * Buoc nhay khi duyet diem anh. Duyet tung diem mot la thua -
         * anh do sau von da nhoe - va ton CPU moi khung hinh.
         */
        private const val STEP = 2
        private const val STEP_SQ = STEP * STEP

        /**
         * Nguong tin duoc cua Depth API, milimet.
         *
         * Duoi 0,1m gan nhu luon la nhieu. Tren 8m thi depth-from-motion
         * sai qua lon de dung vao viec gi, va cung xa hon nhieu so voi
         * quang duong canh bao vat can can quan tam.
         */
        private const val MIN_MM = 100
        private const val MAX_MM = 8000

        /** Lam tron met ve 2 chu so thap phan khi ghi JSON. */
        fun round2(v: Float): Double = (v * 100f).roundToInt() / 100.0
    }
}
