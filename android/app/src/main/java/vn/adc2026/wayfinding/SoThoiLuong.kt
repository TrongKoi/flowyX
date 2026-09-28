package vn.adc2026.wayfinding

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/**
 * SO THOI LUONG - hoc tu chinh nguoi dung, thay vi tin loi ho uoc.
 *
 * `SoThoiLuongTest` khoa vai truong hop moc.
 *
 * --------------------------------------------------------------------
 * VI SAO BAN NAY NAM O DIEN THOAI
 * --------------------------------------------------------------------
 *
 * Ten cong viec la noi dung ca nhan, va mot so ghi "toi hay mat 3 tieng
 * cho viec dang le 30 phut" la thu rat rieng tu. Nen so nay chi nam tren
 * dien thoai, khong gui di dau.
 *
 * --------------------------------------------------------------------
 * TRUNG VI, KHONG PHAI TRUNG BINH
 * --------------------------------------------------------------------
 *
 * Mot lan bi gian doan bat thuong - mat dien, co nguoi goi - keo trung
 * binh lech han. Trung vi bo qua cac lan ca biet do.
 */
class SoThoiLuong private constructor(
    private val banGhi: MutableMap<String, MutableList<LanDo>>,
) {

    constructor() : this(mutableMapOf())

    /** Mot lan lam viec da xong. `uocPhut` null = nguoi dung khong uoc. */
    data class LanDo(val uocPhut: Double?, val thatPhut: Double)

    fun ghi(tenViec: String, thatPhut: Double, uocPhut: Double? = null) {
        if (tenViec.isBlank() || thatPhut <= 0.0) return
        banGhi.getOrPut(tenViec) { mutableListOf() }
            .add(LanDo(uocPhut, thatPhut))
    }

    fun soLan(tenViec: String): Int = banGhi[tenViec]?.size ?: 0

    /** Thoi luong nen dung cho lan toi. null neu chua co so lieu. */
    fun uocLuong(tenViec: String): Double? {
        val lan = banGhi[tenViec] ?: return null
        if (lan.isEmpty()) return null
        val ganDay = lan.takeLast(SO_LAN_XET).map { it.thatPhut }.sorted()
        val giua = ganDay.size / 2
        return if (ganDay.size % 2 == 1) ganDay[giua]
        else (ganDay[giua - 1] + ganDay[giua]) / 2.0
    }

    /**
     * Cau noi ra khoang cach giua uoc luong va thuc te cua LAN TRUOC.
     *
     * Chi NEU SO LIEU, khong ket luan gi ve nguoi dung. "Ban hay uoc
     * thieu" la mot nhan xet ve tinh cach; "lan truoc 20, thuc te 35" la
     * mot con so ho tu doi chieu duoc.
     */
    fun cauDoiChieu(tenViec: String): String? {
        val cuoi = banGhi[tenViec]?.lastOrNull() ?: return null
        val uoc = cuoi.uocPhut ?: return null
        if (kotlin.math.abs(cuoi.thatPhut - uoc) < CHENH_DANG_KE_PHUT) return null
        return "Lần trước bạn ước ${phut(uoc)} phút, " +
            "thực tế ${phut(cuoi.thatPhut)} phút."
    }

    fun cauGoiY(tenViec: String): String? {
        val u = uocLuong(tenViec) ?: return null
        return "Những lần trước việc này mất khoảng ${phut(u)} phút."
    }

    // ---------------------------------------------------------------
    // Luu va doc
    // ---------------------------------------------------------------

    /** Chi lich su cua MOT cong viec, dang JSON de gui qua cau noi. */
    fun jsonMotViec(tenViec: String): String? {
        val lan = banGhi[tenViec] ?: return null
        val mang = JSONArray()
        for (d in lan) {
            val o = JSONObject()
            if (d.uocPhut != null) o.put("uoc", d.uocPhut) else o.put("uoc", JSONObject.NULL)
            o.put("that", d.thatPhut)
            mang.put(o)
        }
        return JSONObject().put(tenViec, mang).toString()
    }

    fun luu(ctx: Context) {
        val goc = JSONObject()
        for ((ten, ds) in banGhi) {
            val mang = JSONArray()
            for (d in ds) {
                val o = JSONObject()
                if (d.uocPhut != null) o.put("uoc", d.uocPhut) else o.put("uoc", JSONObject.NULL)
                o.put("that", d.thatPhut)
                mang.put(o)
            }
            goc.put(ten, mang)
        }
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString(KHOA, goc.toString()).apply()
    }

    companion object {
        /**
         * Lay trung vi cua toi da bay nhieu lan gan nhat.
         *
         * Du de loc ca biet, va du ngan de theo kip khi nguoi dung that
         * su nhanh len o mot loai viec.
         */
        const val SO_LAN_XET = 5

        /**
         * Chenh lech duoi muc nay thi khong noi gi.
         *
         * Uoc 20 thuc te 22 la uoc DUNG. Noi ra mot chenh lech khong
         * dang ke se lam cau canh bao mat gia tri o nhung lan that su
         * lech nhieu.
         */
        const val CHENH_DANG_KE_PHUT = 5.0

        private const val PREFS = "flowy_thoi_luong"
        private const val KHOA = "so"

        fun doc(ctx: Context): SoThoiLuong {
            val s = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getString(KHOA, null) ?: return SoThoiLuong()
            return tuJson(s)
        }

        /** So hong thi bat dau lai tu trong, khong lam sap app. */
        fun tuJson(s: String): SoThoiLuong {
            val ra = mutableMapOf<String, MutableList<LanDo>>()
            try {
                val goc = JSONObject(s)
                for (ten in goc.keys()) {
                    val mang = goc.optJSONArray(ten) ?: continue
                    val ds = mutableListOf<LanDo>()
                    for (i in 0 until mang.length()) {
                        val o = mang.optJSONObject(i) ?: continue
                        if (!o.has("that")) continue
                        val that = o.optDouble("that", Double.NaN)
                        if (that.isNaN()) continue
                        val uoc = if (o.isNull("uoc")) null
                        else o.optDouble("uoc", Double.NaN).takeIf { !it.isNaN() }
                        ds.add(LanDo(uoc, that))
                    }
                    if (ds.isNotEmpty()) ra[ten] = ds
                }
            } catch (_: Exception) {
                // Mat lich su la mot phien toai; app khong chay duoc la
                // mot loi.
                return SoThoiLuong()
            }
            return SoThoiLuong(ra)
        }

        /** Lam tron ve phut. Nua phut khong giup nguoi dung hinh dung hon. */
        internal fun phut(x: Double): String =
            maxOf(1, Math.round(x).toInt()).toString()
    }
}
