package vn.adc2026.wayfinding

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/**
 * LOI NHAC THEO GIO - do nguoi dung tu dat ten.
 *
 * Ban Kotlin cua `adc_wayfinding/wayfinding/adhd/nhacviec.py`. Doc phan
 * dau file do truoc khi sua gi o day: no giai thich vi sao bon thu duoi
 * KHONG duoc lam, va moi thu deu co mot bai test khoa lai ben Python.
 *
 *     khong lam                     | vi sao
 *     ------------------------------|--------------------------------
 *     danh muc thuoc, ten hoat chat | biet ten thuoc la biet chan doan
 *     tinh lieu, nhac theo phac do  | do la huong dan dieu tri
 *     dem "ty le tuan thu"          | do la theo doi de quan ly benh
 *     canh bao bo lieu              | do la canh bao lam sang
 *
 * --------------------------------------------------------------------
 * LOP NAY KHONG DUOC DI QUA CAU NOI
 * --------------------------------------------------------------------
 *
 * Bang trong `bridge.py` ghi ro: ten cac loi nhac nguoi dung tu dat la
 * thu KHONG BAO GIO duoc len duong truyen.
 *
 * Nen `SoNhac` khong duoc cham vao `Payload` hay `BridgeClient`. No song
 * tron ven tren may nay. Ben Python co hai bai test canh gac dieu do;
 * ben nay no nam o day duoi dang mot dong chu, va o mat nguoi review.
 *
 * Them mot dong `import` cho tien la du de pha. Ma hong kieu do khong
 * lam app sap - no chi lang le dua du lieu ca nhan len duong truyen.
 */
class SoNhac private constructor(
    val danhSach: MutableList<LoiNhac>,
) {

    constructor() : this(mutableListOf())

    /**
     * Mot loi nhac. `ten` la chuoi TU DO - nguoi dung go gi cung duoc.
     *
     * Lop nay khong phan tich chuoi do, khong doi chieu voi danh muc
     * nao, va khong luu y nghia nao khac ngoai chinh chuoi do.
     */
    data class LoiNhac(
        val ten: String,
        /** Phut tinh tu nua dem. */
        val gio: Double,
        val lapLaiHangNgay: Boolean = true,
    ) {
        /** Cau doc len. Chi nhac lai dung ten nguoi dung da dat. */
        fun cau(): String = "Đã tới giờ: $ten."

        val gioPhut: String
            get() = String.format(
                java.util.Locale.US, "%02d:%02d",
                (gio / 60).toInt(), (gio % 60).toInt())
    }

    /**
     * Chi so cac loi nhac DA BAO trong ngay hom nay.
     *
     * Day la thu duy nhat lop nay ghi nho ve qua khu, va no chi de
     * tranh bao hai lan. No KHONG phai ban ghi ve hanh vi nguoi dung, va
     * no khong duoc luu xuong dia.
     */
    private val daBao = mutableSetOf<Int>()
    private var ngay: String? = null

    fun them(ten: String, gio: Double, lapLaiHangNgay: Boolean = true): Boolean {
        val t = ten.trim()
        if (t.length < MIN_KY_TU) return false
        if (gio < 0.0 || gio >= 1440.0) return false
        danhSach.add(LoiNhac(t, gio, lapLaiHangNgay))
        return true
    }

    fun xoa(chiSo: Int): Boolean {
        if (chiSo !in danhSach.indices) return false
        danhSach.removeAt(chiSo)
        // Chi so phai truot theo, neu khong thi xoa muc dau se lam muc
        // thu hai bi coi nhu da bao roi.
        val moi = daBao.filter { it != chiSo }
            .map { if (it < chiSo) it else it - 1 }
        daBao.clear()
        daBao.addAll(moi)
        return true
    }

    /**
     * Loi nhac can bao ngay bay gio, hoac null.
     *
     * @param ngayHomNay dang "2026-09-15". Sang ngay moi thi cac loi
     *   nhac lap lai duoc bao lai - nen phai biet hom nay la ngay nao.
     */
    fun denHan(bayGio: Double, ngayHomNay: String): LoiNhac? {
        if (ngayHomNay != ngay) {
            ngay = ngayHomNay
            daBao.clear()
        }
        for (i in danhSach.indices) {
            if (i in daBao) continue
            val tre = bayGio - danhSach[i].gio
            if (tre >= 0.0 && tre <= CUA_SO_PHUT) {
                daBao.add(i)
                return danhSach[i]
            }
        }
        return null
    }

    fun luu(ctx: Context) {
        val mang = JSONArray()
        for (ln in danhSach) {
            mang.put(JSONObject()
                .put("ten", ln.ten)
                .put("gio", ln.gio)
                .put("lap_lai", ln.lapLaiHangNgay))
        }
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString(KHOA, mang.toString()).apply()
    }

    companion object {
        /** Ten ngan hon nay coi nhu chua nhap. */
        const val MIN_KY_TU = 3

        /**
         * Loi nhac den han roi bao nhieu phut thi thoi, coi nhu da lo.
         *
         * Khong bao mai: mot loi nhac hien lien tuc se bi tat di, va luc
         * do moi loi nhac khac cung mat theo.
         */
        const val CUA_SO_PHUT = 30.0

        private const val PREFS = "flowy_nhac"
        private const val KHOA = "danh_sach"

        fun doc(ctx: Context): SoNhac {
            val s = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getString(KHOA, null) ?: return SoNhac()
            return tuJson(s)
        }

        /** So hong thi bat dau lai tu trong, khong lam sap app. */
        fun tuJson(s: String): SoNhac {
            val so = SoNhac()
            try {
                val mang = JSONArray(s)
                for (i in 0 until mang.length()) {
                    val o = mang.optJSONObject(i) ?: continue
                    val ten = o.optString("ten", "")
                    if (!o.has("gio")) continue
                    val gio = o.optDouble("gio", Double.NaN)
                    if (gio.isNaN()) continue
                    so.them(ten, gio, o.optBoolean("lap_lai", true))
                }
            } catch (_: Exception) {
                return SoNhac()
            }
            return so
        }
    }
}
