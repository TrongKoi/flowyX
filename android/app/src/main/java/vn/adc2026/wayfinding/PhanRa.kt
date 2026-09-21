package vn.adc2026.wayfinding

import android.content.Context
import org.json.JSONObject

/**
 * ====================================================================
 * PHAN RA TAC VU - chia mot viec lon thanh vai buoc nho
 * ====================================================================
 *
 * Phan LOGIC. Khong dung toi View nao, nen test duoc tren JVM.
 *
 * ----- Ba rang buoc, va ca ba deu la ve AN TOAN NHAN THUC -----
 *
 * 1. TOI DA NAM BUOC, CAT CUNG O DAY.
 *    Nguoi dung den voi mot viec ho khong bat dau duoc. Tra ve 12 buoc
 *    la doi MOT viec khong bat dau duoc thanh MUOI HAI viec khong bat
 *    dau duoc - nhan len, khong phai cai thien.
 *
 *    Gioi han nam trong prompt, NHUNG khong tin vao prompt: mo hinh co
 *    the tra nhieu hon, va luc do cat o day moi la thu chan that.
 *
 * 2. BUOC 1 PHAI LA VIEC LAM DUOC NGAY.
 *    Prompt yeu cau dong tu hanh dong cu the. O day co them mot luoi
 *    loc: buoc nao chi gom dong tu mo ho ("nghien cuu", "chuan bi",
 *    "tim hieu") thi bi danh dau, va man hinh xem truoc se de nguoi
 *    dung sua truoc khi duyet.
 *
 * 3. KHONG CO GI DUOC LUU NEU NGUOI DUNG CHUA DUYET.
 *    `PhanRa` chi TRA VE ket qua. Viec ghi vao `TrangThaiFocus` nam o
 *    man hinh xem truoc, sau khi nguoi dung bam. Khong co duong nao de
 *    mot ket qua AI di thang vao du lieu.
 */
object PhanRa {

    /** Toi da so buoc giu lai. Xem rang buoc 1. */
    const val TOI_DA_BUOC = 5

    /** So luot mien phi moi ngay. */
    const val LUOT_MOI_NGAY = 3

    private const val PREFS = "flowy_phan_ra"
    private const val K_NGAY = "ngay_cuoi"
    private const val K_SO_LUOT = "so_luot"

    /**
     * Dong tu qua mo ho de lam buoc dau tien.
     *
     * Day chinh la nhom tu ma nguoi dang te liet KHONG hanh dong duoc:
     * "nghien cuu bao cao" khong noi cho biet mo cai gi ra truoc.
     */
    private val DONG_TU_MO_HO = listOf(
        "nghiên cứu", "tìm hiểu", "chuẩn bị", "xây dựng", "tối ưu",
        "rà soát", "suy nghĩ", "lên kế hoạch", "xem xét", "phân tích",
        "research", "explore", "prepare", "build", "optimi", "review",
        "think about", "plan ", "consider", "analyse", "analyze",
    )

    /** Mot buoc nho. */
    data class Buoc(
        val ten: String,
        val phut: Int,
        /** Dong tu mo ho -> man xem truoc goi y nguoi dung sua. */
        val moHo: Boolean = false,
    )

    /**
     * Ket qua phan ra.
     *
     * @param can cau hoi khi AI khong du thong tin de chia. Co gia tri
     *            thi `cacBuoc` rong, va man hinh hien cau hoi do thay vi
     *            mot danh sach bia ra.
     */
    data class KetQua(val cacBuoc: List<Buoc>, val can: String? = null)

    // -----------------------------------------------------------------
    // Doc JSON tra ve
    // -----------------------------------------------------------------

    /**
     * Doc goi JSON cua mo hinh.
     *
     * Chiu duoc ba thu mo hinh hay lam sai, vi ca ba deu da gap:
     *
     *   · Boc JSON trong ```json ... ``` du da bao "chi tra JSON".
     *   · Tra nhieu hon nam buoc.
     *   · Bo qua `thoi_gian_du_tinh`, hoac dien mot so vo ly (0, 500).
     *
     * Khong doc duoc -> nem `IllegalArgumentException`, va man hinh hien
     * duong tu chia thu cong. KHONG bia ra mot danh sach rong roi coi
     * nhu thanh cong.
     */
    fun doc(chu: String): KetQua {
        val sach = goBocMa(chu)
        val o = try { JSONObject(sach) } catch (e: Exception) {
            throw IllegalArgumentException("khong phai JSON", e)
        }

        o.optString("need").takeIf { it.isNotBlank() && it != "null" }?.let {
            return KetQua(emptyList(), it.trim())
        }

        val mang = o.optJSONArray("steps")
            ?: throw IllegalArgumentException("thieu truong steps")

        val ra = ArrayList<Buoc>(TOI_DA_BUOC)
        for (i in 0 until mang.length()) {
            if (ra.size >= TOI_DA_BUOC) break          // CAT CUNG - xem rang buoc 1
            val b = mang.optJSONObject(i) ?: continue
            val ten = b.optString("ten_hanh_dong").trim()
            if (ten.isEmpty()) continue
            ra += Buoc(ten, lamTronPhut(b.optInt("thoi_gian_du_tinh", 0)), moHo(ten))
        }
        if (ra.isEmpty()) throw IllegalArgumentException("khong co buoc nao doc duoc")
        return KetQua(ra)
    }

    /**
     * Go `​```json ... ​``` ` neu mo hinh boc ket qua trong khoi ma.
     *
     * Bao "chi tra JSON" trong prompt khong du - moi mo hinh deu boc
     * them khoi ma mot cach ngau nhien, va khi do `JSONObject` do ngay
     * o ky tu dau.
     */
    private fun goBocMa(chu: String): String {
        var t = chu.trim()
        if (t.startsWith("```")) {
            t = t.removePrefix("```json").removePrefix("```").trim()
            t = t.removeSuffix("```").trim()
        }
        // Con rao don ngoai khoi ma: lay tu dau ngoac nhon dau tien.
        val dau = t.indexOf('{')
        val cuoi = t.lastIndexOf('}')
        return if (dau >= 0 && cuoi > dau) t.substring(dau, cuoi + 1) else t
    }

    /**
     * Lam tron ve boi so cua 5, trong khoang 5..45.
     *
     * Mot buoc "3 phut" hay "37 phut" khong sai, nhung cac con so le
     * lam danh sach trong nhu mot bang tinh. Boi so cua 5 doc luot qua
     * la uoc duoc tong, va do la thu nguoi mu thoi gian can.
     */
    fun lamTronPhut(p: Int): Int {
        if (p <= 0) return 10                      // mo hinh bo trong
        val t = ((p + 2) / 5) * 5
        return t.coerceIn(5, 45)
    }

    fun moHo(ten: String): Boolean {
        val t = ten.lowercase().trim()
        return DONG_TU_MO_HO.any { t.startsWith(it) }
    }

    // -----------------------------------------------------------------
    // Han muc
    // -----------------------------------------------------------------

    /**
     * So luot con lai hom nay.
     *
     * So theo CHUOI NGAY `yyyy-MM-dd`, khong phai bo dem 24 gio. Chuoi
     * ngay dung ke ca khi doi mui gio hay doi gio he thong, va dung voi
     * dung cau ma man hinh hua: "den nua dem co lai".
     */
    fun conLai(ctx: Context): Int {
        val p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val homNay = ngayHomNay()
        if (p.getString(K_NGAY, "") != homNay) return LUOT_MOI_NGAY
        return (LUOT_MOI_NGAY - p.getInt(K_SO_LUOT, 0)).coerceAtLeast(0)
    }

    /**
     * Tru mot luot. Goi SAU khi da nhan duoc ket qua hop le.
     *
     * Khong tru luc GUI DI: mat mang, het gio cho, hay mo hinh tra rac
     * deu khong phai loi cua nguoi dung, va tru luot trong nhung ca do
     * la phat ho vi mot thu ho khong gay ra.
     */
    fun truMotLuot(ctx: Context) {
        val p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val homNay = ngayHomNay()
        val daDung = if (p.getString(K_NGAY, "") == homNay) p.getInt(K_SO_LUOT, 0) else 0
        p.edit().putString(K_NGAY, homNay).putInt(K_SO_LUOT, daDung + 1).apply()
    }

    private fun ngayHomNay(): String = java.text.SimpleDateFormat(
        "yyyy-MM-dd", java.util.Locale.US).format(java.util.Date())
}
