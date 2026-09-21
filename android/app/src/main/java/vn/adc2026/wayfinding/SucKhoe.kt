package vn.adc2026.wayfinding

import android.content.ContentValues
import android.content.Context
import android.os.Build
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale

/**
 * ====================================================================
 * DU LIEU SUC KHOE - LOP CHUNG
 * ====================================================================
 *
 * Flowy doc mot vai chi so suc khoe de dat canh so lieu tap trung: "hom
 * qua ngu 5 tieng, hom nay bo do hai phien" la mot cau nguoi dung tu rut
 * ra duoc, va no huu ich hon moi loi khuyen chung chung nao.
 *
 * ----- Vi sao co lop truu tuong nay -----
 *
 * Nguon du lieu khac nhau theo he dieu hanh:
 *
 *   Android 14+ -> android.health.connect (NAM TRONG HE DIEU HANH,
 *                  khong can thu vien ngoai) - xem `SucKhoeHC`
 *   Android cu  -> khong co nguon nao; nguoi dung tu nhap
 *   iOS         -> HealthKit - xem ban iOS, cung lop `NguonSucKhoe`
 *
 * Phan con lai cua app chi goi `SucKhoe`, khong goi thang Health Connect.
 * Nho vay them nguon moi khong phai sua man hinh nao.
 *
 * ----- Nguyen tac xu ly (Dieu 9 GDPR, va muc 6 Chinh sach rieng tu) -----
 *
 *   1. CHI DOC. Khong bao gio ghi nguoc vao ho so suc khoe cua nguoi dung.
 *   2. CHI LOAI DA TICH. Moi loai chi so la mot o tich rieng.
 *   3. CHI TONG HOP THEO NGAY. Khong luu chuoi do chi tiet - Flowy can
 *      "dem qua ngu 320 phut", khong can biet luc 2h07 nguoi dung tro minh.
 *   4. CHI BAY NGAY. Qua bay ngay thi xoa. Du de thay xu huong, khong du
 *      de dung mot ho so suc khoe.
 *   5. KHONG RA KHOI MAY. Khong co duong mang nao cham vao bang nay.
 *   6. TAT LA XOA. Tat ket noi xoa sach du lieu da doc, ngay lap tuc -
 *      khong danh dau "da tat" roi giu lai du lieu.
 *
 * Diem 3, 4 va 6 la cach hien thuc hoa nguyen tac toi thieu hoa du lieu.
 * Chung khien Flowy KHONG THE tro thanh mot kho ho so suc khoe ngay ca
 * khi ai do sau nay muon bien no thanh the.
 */
object SucKhoe {

    private const val PREFS = "flowy_suc_khoe"
    private const val K_BAT = "bat"
    private const val K_NGU = "loai_ngu"
    private const val K_BUOC = "loai_buoc"
    private const val K_NHIP_TIM = "loai_nhip_tim"
    private const val K_DONG_Y_LUC = "dong_y_luc"

    /** Giu bay ngay gan nhat. Xem nguyen tac 4. */
    const val GIU_NGAY = 7

    /** Mot ngay du lieu suc khoe, da tong hop. */
    data class Ngay(
        val ngay: String,
        val nguPhut: Int?,
        val buocChan: Int?,
        /**
         * Nhip tim luc nghi, don vi nhip/phut (muc 7.2).
         *
         * Co the null, va do la trang thai BINH THUONG chu khong phai
         * loi: may khong co cam bien nhip tim, hoac hom do khong deo
         * dong ho, thi ngay do khong co so. Bang `suc_khoe` cung de cot
         * nay NULL - xem di tru 1 -> 2 trong `KhoDuLieu`.
         *
         * Vi sao chi so NGHI chu khong phai nhip tim trung binh ca ngay:
         * nhip trung binh doi theo viec vua lam gi (di bo, leo cau
         * thang), con nhip nghi doi cham va phan anh trang thai nen -
         * ngu du hay thieu, cang thang keo dai hay khong. Do la thu co
         * the dat canh so phut tap trung de thay lien he.
         */
        val nhipTimNghi: Int? = null,
    )

    // ---------------------------------------------------------------
    // Trang thai dong y
    // ---------------------------------------------------------------

    fun dangBat(ctx: Context): Boolean = p(ctx).getBoolean(K_BAT, false)

    fun docNgu(ctx: Context): Boolean = p(ctx).getBoolean(K_NGU, true)
    fun docBuoc(ctx: Context): Boolean = p(ctx).getBoolean(K_BUOC, true)

    /**
     * Doc nhip tim nghi khong. MAC DINH TAT (muc 7.2).
     *
     * Hai o tich kia mac dinh bat vi ngu va buoc chan la nhung so ma
     * gan nhu ai cung da quen nhin. Nhip tim thi khac: no la chi so y
     * te ro net nhat trong ba, va bat san mot o doc du lieu tim mach la
     * dieu khong nen lam thay nguoi dung - du man hinh co giai thich.
     */
    fun docNhipTim(ctx: Context): Boolean = p(ctx).getBoolean(K_NHIP_TIM, false)

    /** Luc nguoi dung bam dong y - GDPR doi hoi chung minh duoc su dong y. */
    fun dongYLuc(ctx: Context): Long = p(ctx).getLong(K_DONG_Y_LUC, 0L)

    fun bat(ctx: Context, ngu: Boolean, buoc: Boolean, nhipTim: Boolean = false) {
        p(ctx).edit()
            .putBoolean(K_BAT, true)
            .putBoolean(K_NGU, ngu)
            .putBoolean(K_BUOC, buoc)
            .putBoolean(K_NHIP_TIM, nhipTim)
            .putLong(K_DONG_Y_LUC, System.currentTimeMillis())
            .apply()
    }

    /** Tat VA xoa. Hai viec nay khong tach roi duoc - xem nguyen tac 6. */
    fun tat(ctx: Context) {
        p(ctx).edit().clear().apply()
        xoaHet(ctx)
    }

    /** May nay co nguon du lieu suc khoe nao khong. */
    fun coNguon(ctx: Context): Boolean =
        Build.VERSION.SDK_INT >= 34 && SucKhoeHC.coTrenMay(ctx)

    /** Quyen can xin, theo dung cac o tich nguoi dung da chon. */
    fun quyenCan(ctx: Context): Array<String> {
        if (Build.VERSION.SDK_INT < 34) return emptyArray()
        val ds = ArrayList<String>(2)
        if (docNgu(ctx)) ds.add("android.permission.health.READ_SLEEP")
        if (docBuoc(ctx)) ds.add("android.permission.health.READ_STEPS")
        if (docNhipTim(ctx)) ds.add("android.permission.health.READ_RESTING_HEART_RATE")
        return ds.toTypedArray()
    }

    // ---------------------------------------------------------------
    // Doc tu nguon va ghi vao bang
    // ---------------------------------------------------------------

    /**
     * Doc bay ngay gan nhat tu nguon cua he dieu hanh va ghi de vao bang.
     *
     * Chay o luong nen (nguon tra ket qua bat dong bo), `xong` duoc goi o
     * luong do - nguoi goi tu chuyen ve luong giao dien.
     */
    fun lamMoi(ctx: Context, xong: (Boolean) -> Unit) {
        if (!dangBat(ctx) || Build.VERSION.SDK_INT < 34) { xong(false); return }
        SucKhoeHC.doc(ctx, GIU_NGAY) { ds ->
            if (ds == null) { xong(false); return@doc }
            for (n in ds) ghi(ctx, n)
            donNgayCu(ctx)
            xong(true)
        }
    }

    fun ghi(ctx: Context, n: Ngay) {
        val v = ContentValues()
        v.put("ngay", n.ngay)
        v.put("ngu_phut", n.nguPhut)
        v.put("buoc_chan", n.buocChan)
        v.put("nhip_tim_nghi", n.nhipTimNghi)
        v.put("cap_nhat", System.currentTimeMillis())
        KhoDuLieu(ctx).writableDatabase.insertWithOnConflict(
            "suc_khoe", null, v, android.database.sqlite.SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun doc(ctx: Context, soNgay: Int = GIU_NGAY): List<Ngay> {
        val ra = ArrayList<Ngay>()
        val c = KhoDuLieu(ctx).readableDatabase.query(
            "suc_khoe", arrayOf("ngay", "ngu_phut", "buoc_chan", "nhip_tim_nghi"),
            null, null, null, null, "ngay DESC", soNgay.toString())
        c.use {
            while (it.moveToNext()) {
                ra.add(Ngay(
                    it.getString(0),
                    if (it.isNull(1)) null else it.getInt(1),
                    if (it.isNull(2)) null else it.getInt(2),
                    if (it.isNull(3)) null else it.getInt(3)))
            }
        }
        return ra
    }

    fun homQua(ctx: Context): Ngay? {
        val c = Calendar.getInstance().apply { add(Calendar.DAY_OF_YEAR, -1) }
        val ngay = dinhDangNgay(c.time)
        return doc(ctx, GIU_NGAY).firstOrNull { it.ngay == ngay }
    }

    private fun donNgayCu(ctx: Context) {
        val c = Calendar.getInstance().apply { add(Calendar.DAY_OF_YEAR, -GIU_NGAY) }
        KhoDuLieu(ctx).writableDatabase.delete(
            "suc_khoe", "ngay < ?", arrayOf(dinhDangNgay(c.time)))
    }

    fun xoaHet(ctx: Context) {
        KhoDuLieu(ctx).writableDatabase.delete("suc_khoe", null, null)
    }

    fun dinhDangNgay(d: Date): String =
        SimpleDateFormat("yyyy-MM-dd", Locale.US).format(d)

    private fun p(ctx: Context) =
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
}
