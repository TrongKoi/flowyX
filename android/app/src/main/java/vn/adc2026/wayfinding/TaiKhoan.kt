package vn.adc2026.wayfinding

import android.content.Context
import android.util.Base64
import java.security.SecureRandom

/**
 * ====================================================================
 * TAI KHOAN VA PHIEN DANG NHAP (v5)
 * ====================================================================
 *
 * Tai khoan o day KHOA APP LAI, khong dong bo gi ca. Noi that voi nguoi
 * dung ngay tren man hinh dang nhap: du lieu o lai trong may.
 *
 * ----- "Quen mat khau": vi sao khong gui ma qua Gmail -----
 *
 * Gui email can mot may chu SMTP va mot bo thong tin dang nhap. Nhet bo
 * do vao APK la cho khong: ai giai nen APK cung lay duoc va gui thu mao
 * danh FlowyX. Con dung mot may chu that thi phai co may chu that -
 * khong the co truoc ngay thi, va se keo theo ca mot ho so du lieu ca
 * nhan phai bao ve.
 *
 * Nen ban nay dung MA KHOI PHUC: luc dang ky, app sinh mot ma 12 ky tu,
 * hien mot lan va nhac nguoi dung chep lai. Ma nay bam giong mat khau
 * (PBKDF2, muoi rieng) chu khong luu tho.
 *
 * Neu mat CA hai (mat khau va ma), khong ai mo duoc - ke ca nhom lam app.
 * Duong cuoi cung la "xoa het va bat dau lai", co canh bao ro rang. Day
 * la cai gia phai tra cho viec khong gui du lieu di dau.
 *
 * Khi nhom co may chu that, dac ta luong OTP nam o
 * `docs/BAO_MAT.md` muc 4 - khong phai lam lai tu dau.
 */
object TaiKhoan {

    private const val PREFS = "flowy_phien"
    private const val K_EMAIL = "email"
    private const val K_TEN = "ho_ten"
    private const val K_MA_KP_BAM = "ma_kp_bam"
    private const val K_MA_KP_MUOI = "ma_kp_muoi"
    private const val K_LAN_SAI = "lan_sai"
    private const val K_CHO_DEN = "cho_den"

    /** Bo ky tu ma khoi phuc: bo I, O, 0, 1 de khong doc nham khi chep tay. */
    private const val BANG_CHU = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    data class Phien(val email: String, val hoTen: String)

    fun dangDangNhap(ctx: Context): Phien? {
        val p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val e = p.getString(K_EMAIL, null) ?: return null
        return Phien(e, p.getString(K_TEN, "") ?: "")
    }

    fun ghiPhien(ctx: Context, nd: KhoDuLieu.NguoiDung) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putString(K_EMAIL, nd.email).putString(K_TEN, nd.hoTen)
            .putInt(K_LAN_SAI, 0).remove(K_CHO_DEN).apply()
    }

    fun dangXuat(ctx: Context) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .remove(K_EMAIL).remove(K_TEN).apply()
    }

    // ---------------------------------------------------------------
    // Ma khoi phuc
    // ---------------------------------------------------------------

    /** Sinh ma moi, luu ban BAM, tra ve ma tho de hien MOT lan. */
    fun taoMaKhoiPhuc(ctx: Context): String {
        val r = SecureRandom()
        val ma = (1..12).map { BANG_CHU[r.nextInt(BANG_CHU.length)] }.joinToString("")
        val muoi = KhoDuLieu.muoiMoi()
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putString(K_MA_KP_BAM, KhoDuLieu.bam(ma, muoi))
            .putString(K_MA_KP_MUOI, Base64.encodeToString(muoi, Base64.NO_WRAP))
            .apply()
        return dinhDangMa(ma)
    }

    /** "ABCD-EFGH-JKLM" - chep tay de hon mot chuoi lien. */
    fun dinhDangMa(ma: String): String = ma.chunked(4).joinToString("-")

    fun kiemMaKhoiPhuc(ctx: Context, nhap: String): Boolean {
        val p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val bamLuu = p.getString(K_MA_KP_BAM, null) ?: return false
        val muoi = Base64.decode(p.getString(K_MA_KP_MUOI, "") ?: "", Base64.NO_WRAP)
        val sach = nhap.uppercase().filter { it in BANG_CHU }
        if (sach.length != 12) return false
        return KhoDuLieu.bangNhau(KhoDuLieu.bam(sach, muoi), bamLuu)
    }

    fun coMaKhoiPhuc(ctx: Context): Boolean =
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).contains(K_MA_KP_BAM)

    // ---------------------------------------------------------------
    // Cham dan khi nhap sai
    // ---------------------------------------------------------------

    /**
     * Sau 5 lan sai, moi lan sai tiep phai cho them. Thoi gian cho tang
     * gap doi: 15 giay, 30, 60... toi da 5 phut.
     *
     * Vi sao khong khoa han: nguoi ADHD go nham mat khau nhieu lan la
     * chuyen binh thuong, va day la may CUA HO. Khoa han se bien mot lan
     * lo dang thanh mat sach nhat ky. Cham dan du de chan do tu dong.
     */
    fun conPhaiCho(ctx: Context): Long {
        val p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val den = p.getLong(K_CHO_DEN, 0L)
        return (den - System.currentTimeMillis()).coerceAtLeast(0L)
    }

    fun ghiNhanSai(ctx: Context) {
        val p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val lan = p.getInt(K_LAN_SAI, 0) + 1
        val e = p.edit().putInt(K_LAN_SAI, lan)
        if (lan > 5) {
            val giay = (15L shl (lan - 6).coerceAtMost(5)).coerceAtMost(300L)
            e.putLong(K_CHO_DEN, System.currentTimeMillis() + giay * 1000)
        }
        e.apply()
    }

    fun ghiNhanDung(ctx: Context) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putInt(K_LAN_SAI, 0).remove(K_CHO_DEN).apply()
    }

    /** Xoa sach: tai khoan, ma khoi phuc, va TOAN BO du lieu trong may. */
    fun xoaHet(ctx: Context) {
        KhoDuLieu(ctx).xoaTatCa()
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().clear().apply()
        for (p in listOf("flowy_lich", "flowy_nhat_ky", "flowy_bien_ban", "flowy_tien_do",
                         "flowy_focus", "flowy_thoi_luong", "flowy_nhac")) {
            ctx.getSharedPreferences(p, Context.MODE_PRIVATE).edit().clear().apply()
        }
    }
}
