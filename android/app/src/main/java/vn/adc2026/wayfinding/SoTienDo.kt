package vn.adc2026.wayfinding

import android.content.Context
import org.json.JSONObject
import java.util.Calendar

/**
 * SO TIEN DO - dem so viec lam xong theo NGAY.
 *
 * --------------------------------------------------------------------
 * VI SAO PHAI CO MOT SO RIENG
 * --------------------------------------------------------------------
 *
 * `SoThoiLuong` ghi thoi luong tung lan lam, nhung KHONG ghi ngay - no
 * chi can biet "viec nay thuong mat bao lau", khong can biet lam hom
 * nao. Them ngay vao do la lam mot so hai viec.
 *
 * So nay nam tren may, giong ba so kia.
 *
 * --------------------------------------------------------------------
 * CHUOI NGAY LA CON DAO HAI LUOI
 * --------------------------------------------------------------------
 *
 * Voi nguoi nhay cam voi that bai, mot chuoi dut co the te hon la khong
 * co chuoi nao: no bien mot ngay nghi thanh mot lan THUA nhin thay
 * duoc.
 *
 * Ba thu giam bot dieu do, va deu la lua chon co chu dinh:
 *
 *   1. Chuoi KHONG dut ngay khi bo mot ngay. `chuoi()` dem nguoc tu hom
 *      nay HOAC hom qua - lam hom qua ma hom nay chua lam thi chuoi van
 *      con nguyen. Nguoi dung co ca ngay de tiep, khong phai chay dua
 *      voi nua dem.
 *
 *   2. Man hinh khong bao gio noi "ban da mat chuoi". Chuoi ve 0 thi
 *      the do doi sang mot cau khac, khong phai mot cau trach.
 *
 *   3. `tuan()` hien bay ngay gan nhat NHU NHAU - ngay khong lam la mot
 *      cham xam, khong phai mot dau X do.
 *
 * KHONG dem ty le phan tram, KHONG so sanh tuan nay voi tuan truoc,
 * KHONG ve duong xu huong. Xem `adhd/nhatky.py`: cho nao app quy ghi
 * chep ve mot con so tong hop de danh gia, cho do no vuot ranh.
 *
 * Day chi dem so viec da xong, va do la mot con so nguoi dung tu doi
 * chieu duoc.
 */
class SoTienDo private constructor(
    /** Ngay dang "2026-09-16" -> so viec xong trong ngay do. */
    private val theoNgay: MutableMap<String, Int>,
    /**
     * Ngay nguoi dung MO APP (v4). Chuoi ngay tinh ca ngay chi mo app ma
     * khong xong viec nao: quay lai da la mot hanh dong dang ghi nhan, va
     * nguoi dung khong phai bam "diem danh" - them mot thao tac nho la them
     * mot cho de quen roi thay chuoi dut.
     */
    private val ngayMo: MutableSet<String> = mutableSetOf(),
) {

    constructor() : this(mutableMapOf())

    /** Ghi hom nay la ngay co mo app. Goi moi lan mot tab hien len; goi nhieu lan khong sao. */
    fun diemDanh(ngay: String = homNay()): Boolean {
        val moi = ngayMo.add(ngay)
        if (ngayMo.size > GIU_NGAY) ngayMo.sorted().take(ngayMo.size - GIU_NGAY).forEach(ngayMo::remove)
        return moi
    }

    fun coHoatDong(ngay: String): Boolean = soViec(ngay) > 0 || ngay in ngayMo

    /** Ghi mot viec vua xong. */
    fun ghi(ngay: String = homNay()) {
        theoNgay[ngay] = (theoNgay[ngay] ?: 0) + 1
        don()
    }

    fun soViec(ngay: String): Int = theoNgay[ngay] ?: 0

    /** Tong so viec da xong tu truoc toi nay. Chi dung cho thong ke noi bo. */
    fun tongSoViec(): Int = theoNgay.values.sum()

    /**
     * Ban doc-only cua bang ngay -> so viec, cho chuc nang xuat du lieu.
     *
     * `theoNgay` giu private vi moi cho ghi vao no deu phai di qua `ghi()`
     * (co cat bot ngay cu). Xuat du lieu chi doc, nen tra ve ban khong sua
     * duoc thay vi mo han truong ra.
     */
    fun bangTheoNgay(): Map<String, Int> = theoNgay.toMap()

    /**
     * So viec xong TRONG HOM NAY - con so hien tren tab Nhat ky.
     *
     * v5 doi tu "tong tu truoc toi nay" sang "hom nay". Mot con so cong
     * don mai mai bien thanh diem so: no chi co the tang, va ngay nao
     * tang cham la ngay do "kem". Con so theo ngay tu ve 0 sau 00:00,
     * nen moi ngay bat dau lai binh dang, khong ai phai phá ky luc cua
     * chinh minh.
     */
    fun soViecHomNay(): Int = soViec(homNay())

    /**
     * So ngay lien tiep co it nhat mot viec xong.
     *
     * Dem nguoc tu hom nay; hom nay chua co gi thi dem nguoc tu hom qua.
     * Xem ly do o phan dau file - nguoi dung co ca ngay de tiep.
     */
    fun chuoi(tuNgay: Calendar = Calendar.getInstance()): Int {
        val c = tuNgay.clone() as Calendar
        if (!coHoatDong(ngayCua(c))) {
            c.add(Calendar.DAY_OF_YEAR, -1)
            if (!coHoatDong(ngayCua(c))) return 0
        }
        var n = 0
        while (coHoatDong(ngayCua(c))) {
            n++
            c.add(Calendar.DAY_OF_YEAR, -1)
        }
        return n
    }

    /**
     * Bay ngay gan nhat, cu nhat truoc.
     *
     * Tra ve cap (nhan thu, co lam hay khong). Nhan thu lay tu lich he
     * thong nen khong phu thuoc mui gio hay ngon ngu may.
     */
    fun tuan(tuNgay: Calendar = Calendar.getInstance()): List<Pair<String, Boolean>> {
        val ten = listOf("CN", "T2", "T3", "T4", "T5", "T6", "T7")
        val ra = mutableListOf<Pair<String, Boolean>>()
        val c = tuNgay.clone() as Calendar
        c.add(Calendar.DAY_OF_YEAR, -6)
        repeat(7) {
            ra.add(ten[c.get(Calendar.DAY_OF_WEEK) - 1] to coHoatDong(ngayCua(c)))
            c.add(Calendar.DAY_OF_YEAR, 1)
        }
        return ra
    }

    /**
     * Bo cac ngay cu hon [GIU_NGAY].
     *
     * Gioi han RIENG TU, khong phai gioi han ky thuat - cung ly do voi
     * `SoNhatKy.TOI_DA_MUC`. Mot ban ghi khong gioi han ve viec ai do
     * lam gi vao ngay nao la mot ho so.
     */
    private fun don() {
        if (theoNgay.size <= GIU_NGAY) return
        theoNgay.keys.sorted().take(theoNgay.size - GIU_NGAY).forEach(theoNgay::remove)
    }

    fun luu(ctx: Context) {
        val o = JSONObject()
        for ((k, v) in theoNgay) o.put(k, v)
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString(KHOA, o.toString())
            .putString(KHOA_MO, org.json.JSONArray(ngayMo.sorted()).toString())
            .apply()
    }

    companion object {
        /** Giu toi da bao nhieu ngay. Hon mot nam thi bo dan. */
        const val GIU_NGAY = 400

        private const val PREFS = "flowy_tien_do"
        private const val KHOA = "theo_ngay"
        private const val KHOA_MO = "ngay_mo"

        fun ngayCua(c: Calendar): String = String.format(
            java.util.Locale.US, "%04d-%02d-%02d",
            c.get(Calendar.YEAR), c.get(Calendar.MONTH) + 1,
            c.get(Calendar.DAY_OF_MONTH))

        fun homNay(): String = ngayCua(Calendar.getInstance())

        fun doc(ctx: Context): SoTienDo {
            val p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            return tuJson(p.getString(KHOA, null) ?: "{}", p.getString(KHOA_MO, null))
        }

        /** So hong thi bat dau lai tu trong, khong lam sap app. */
        fun tuJson(s: String, ngayMoJson: String? = null): SoTienDo {
            val mo = mutableSetOf<String>()
            try {
                if (ngayMoJson != null) {
                    val m = org.json.JSONArray(ngayMoJson)
                    for (i in 0 until m.length()) m.optString(i).takeIf { it.length == 10 }?.let(mo::add)
                }
            } catch (_: Exception) { }
            val ra = mutableMapOf<String, Int>()
            try {
                val o = JSONObject(s)
                for (k in o.keys()) {
                    val n = o.optInt(k, 0)
                    if (n > 0) ra[k] = n
                }
            } catch (_: Exception) {
                return SoTienDo(mutableMapOf(), mo)
            }
            return SoTienDo(ra, mo)
        }
    }
}
