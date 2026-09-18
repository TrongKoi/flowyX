package vn.adc2026.wayfinding

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.util.Calendar
import java.util.UUID

/**
 * So lich tren may. Logic nam o `Lich.kt`; lop nay chi LUU va DOC.
 *
 * KHONG di qua cau noi - xem phan dau `Lich.kt`.
 */
class SoLich private constructor(
    val danhSach: MutableList<KeHoach>,
    /** "id|ngay" cua cac lan da danh dau xong. Chi de hien dau tich. */
    val daXong: MutableSet<String>,
) {

    fun luu(ctx: Context) {
        val mang = JSONArray()
        for (k in danhSach) {
            mang.put(JSONObject()
                .put("id", k.id).put("ten", k.ten).put("emoji", k.emoji)
                .put("mau", k.mau).put("ngay", k.ngay).put("bat_dau", k.batDau)
                .put("thoi_luong", k.thoiLuong).put("lap_lai", k.lapLai.name)
                .put("nhac_truoc", JSONArray(k.nhacTruoc))
                .put("o_dau", k.oDau ?: JSONObject.NULL)
                .put("thu_lap", JSONArray(k.thuLap.sorted()))
                .put("uu_tien", k.uuTien.name)
                .put("ghim", k.ghim))
        }
        // Chi giu dau tich 60 ngay gan day - khong phai lich su hanh vi.
        val homNay = homNay()
        daXong.removeAll { (it.substringAfter('|').toLongOrNull() ?: 0L) < homNay - 60 }
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putString(KHOA, mang.toString())
            .putString(KHOA_XONG, JSONArray(daXong.toList()).toString())
            .apply()
    }

    fun luuKeHoach(ctx: Context, kh: KeHoach) {
        val i = danhSach.indexOfFirst { it.id == kh.id }
        if (i >= 0) danhSach[i] = kh else danhSach.add(kh)
        luu(ctx)
    }

    fun xoa(ctx: Context, id: String) {
        danhSach.removeAll { it.id == id }
        daXong.removeAll { it.startsWith("$id|") }
        luu(ctx)
    }

    fun doiXong(ctx: Context, id: String, ngay: Long) {
        val k = Lich.khoaXong(id, ngay)
        if (!daXong.remove(k)) daXong.add(k)
        luu(ctx)
    }

    fun tim(id: String?): KeHoach? = danhSach.firstOrNull { it.id == id }

    /** Ghim / bo ghim mot ke hoach. Tra ve trang thai moi. */
    fun doiGhim(ctx: Context, id: String): Boolean {
        val i = danhSach.indexOfFirst { it.id == id }
        if (i < 0) return false
        val moi = !danhSach[i].ghim
        danhSach[i] = danhSach[i].copy(ghim = moi)
        luu(ctx)
        return moi
    }

    companion object {
        private const val PREFS = "flowy_lich"
        private const val KHOA = "ke_hoach"
        private const val KHOA_XONG = "da_xong"

        fun moiId(): String = UUID.randomUUID().toString()

        fun doc(ctx: Context): SoLich {
            val p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            val ds = mutableListOf<KeHoach>()
            val xong = mutableSetOf<String>()
            try {
                val mang = JSONArray(p.getString(KHOA, "[]"))
                for (i in 0 until mang.length()) {
                    val o = mang.optJSONObject(i) ?: continue
                    val ten = o.optString("ten", "")
                    if (ten.isBlank() || !o.has("ngay") || !o.has("bat_dau")) continue
                    val nhac = o.optJSONArray("nhac_truoc")
                    ds += KeHoach(
                        id = o.optString("id").ifBlank { moiId() },
                        ten = ten,
                        emoji = o.optString("emoji", "📝"),
                        mau = o.optInt("mau", 0).coerceIn(0, 4),
                        ngay = o.optLong("ngay"),
                        batDau = o.optInt("bat_dau").coerceIn(0, 1439),
                        thoiLuong = o.optInt("thoi_luong", 30).coerceIn(5, 24 * 60),
                        lapLai = runCatching { LapLai.valueOf(o.optString("lap_lai")) }
                            .getOrDefault(LapLai.KHONG),
                        nhacTruoc = if (nhac == null) listOf(15, 0)
                                    else (0 until nhac.length()).map { nhac.optInt(it) },
                        oDau = if (o.isNull("o_dau")) null else o.optString("o_dau").ifBlank { null },
                        thuLap = o.optJSONArray("thu_lap")?.let { m ->
                            (0 until m.length()).map { m.optInt(it, -1) }
                                .filter { it in 0..6 }.toSet()
                        } ?: emptySet(),
                        uuTien = runCatching { UuTien.valueOf(o.optString("uu_tien")) }
                            .getOrDefault(UuTien.VUA),
                        ghim = o.optBoolean("ghim", false),
                    )
                }
                val mx = JSONArray(p.getString(KHOA_XONG, "[]"))
                for (i in 0 until mx.length()) xong += mx.optString(i)
            } catch (_: Exception) {
                // So hong -> bat dau lai tu trong, khong lam sap app.
            }
            return SoLich(ds, xong)
        }

        /** So ngay tu 1970 theo GIO DIA PHUONG (khong phai UTC). */
        fun homNay(): Long = ngayCua(Calendar.getInstance())

        fun ngayCua(c: Calendar): Long =
            Lich.tuNgayThang(c.get(Calendar.YEAR), c.get(Calendar.MONTH) + 1,
                c.get(Calendar.DAY_OF_MONTH))

        /** "Bay gio" dang so phut tuyet doi dia phuong, cho Lich.kt. */
        fun bayGio(): Long {
            val c = Calendar.getInstance()
            return ngayCua(c) * 1440 + c.get(Calendar.HOUR_OF_DAY) * 60 + c.get(Calendar.MINUTE)
        }

        /** Phut tuyet doi dia phuong -> mili giay he thong (co mui gio, DST). */
        fun sangMili(phutTuyetDoi: Long): Long {
            val ngay = Math.floorDiv(phutTuyetDoi, 1440L)
            val phut = (phutTuyetDoi - ngay * 1440).toInt()
            val (y, m, d) = Lich.ngayThang(ngay)
            return Calendar.getInstance().apply {
                clear()
                set(y, m - 1, d, phut / 60, phut % 60, 0)
            }.timeInMillis
        }
    }
}
