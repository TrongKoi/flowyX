package vn.adc2026.wayfinding

import android.Manifest
import android.app.Activity
import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import android.provider.Settings

/**
 * KIEM QUYEN - mot cho duy nhat tra loi "app con thieu gi de chay du?".
 *
 * Feature request tu buoi test: mot muc trong Cai dat chay kiem tra tat
 * ca quyen, va chua co thi DAN nguoi dung tu cap.
 *
 * --------------------------------------------------------------------
 * VI SAO GOM VE MOT CHO
 * --------------------------------------------------------------------
 *
 * Moi quyen thieu lam hong mot tinh nang theo cach IM LANG: khong co
 * thong bao thi loi nhac khong hien, khong co giong Viet thi doc thanh
 * chuoi am vo nghia. Khong cai
 * nao bao loi. Nguoi dung chi thay "app khong chay" va go di.
 *
 * Nen danh sach nay noi ro TUNG QUYEN de lam gi, bang chu cua nguoi dung,
 * va cham vao mot dong la toi thang cho cap quyen do.
 *
 * --------------------------------------------------------------------
 * KHONG CHAN GI CA
 * --------------------------------------------------------------------
 *
 * Thieu quyen nao thi app van chay, chi mat dung tinh nang do. Khong co
 * man hinh "phai cap du moi dung duoc" - do la buc tuong dat ngay o khau
 * cai dat, noi nhom nguoi dung nay de bo cuoc nhat.
 */
object KiemQuyen {

    const val MA_THONG_BAO = 1

    private const val PREFS = "flowy_kiem_quyen"

    enum class Loai { THONG_BAO, BAO_THUC, GIONG_VIET, PIN }

    data class Muc(
        val loai: Loai,
        val ten: String,
        /** Quyen nay de lam gi - noi bang loi ich, khong bang ten ky thuat. */
        val deLamGi: String,
        val daCo: Boolean,
        /** Khuyen dung chu khong can thiet - hien khac di mot chut. */
        val tuyChon: Boolean = false,
        /** null = chua biet (vd TTS chua khoi tao xong). */
        val chuaBiet: Boolean = false,
    ) {
        fun dong(): String {
            val dau = when {
                chuaBiet -> "…"
                daCo -> "✓"
                tuyChon -> "○"
                else -> "✗"
            }
            return "$dau  $ten\n     $deLamGi"
        }
    }

    fun danhSach(a: Activity, speaker: Speaker?): List<Muc> {
        val ds = mutableListOf<Muc>()

        ds += Muc(Loai.THONG_BAO, "Thông báo",
            "Để lời nhắc hiện ra khi bạn đang ở app khác.",
            coThongBao(a))

        ds += Muc(Loai.BAO_THUC, "Báo thức chính xác",
            "Để lời nhắc tới đúng phút, không trễ.",
            BaoGio.coTheDatChinhXac(a))

        val viet = speaker?.coGiongViet
        ds += Muc(Loai.GIONG_VIET, "Giọng đọc tiếng Việt",
            "Để app đọc lên đúng tiếng Việt.",
            viet == true, chuaBiet = viet == null)

        ds += Muc(Loai.PIN, "Không tối ưu pin cho Flowy",
            "Khuyên dùng trên Samsung: tránh máy tự tắt lời nhắc.",
            khongToiUuPin(a), tuyChon = true)

        return ds
    }

    /** Con thieu quyen BAT BUOC nao khong. Muc tuy chon khong tinh. */
    fun conThieu(a: Activity, speaker: Speaker?): Int =
        danhSach(a, speaker).count { !it.daCo && !it.tuyChon && !it.chuaBiet }

    /**
     * Dan nguoi dung toi cho cap mot quyen.
     *
     * Hop thoai xin quyen cua he thong chi hien DUOC vai lan. Nguoi dung
     * da tu choi hai lan thi `requestPermissions` im lang khong lam gi -
     * luc do phai mo trang thong tin app de ho bat tay.
     */
    fun xuLy(a: Activity, muc: Muc, speaker: Speaker?) {
        when (muc.loai) {
            Loai.THONG_BAO ->
                if (Build.VERSION.SDK_INT >= 33 &&
                    conXinDuoc(a, Manifest.permission.POST_NOTIFICATIONS)
                ) {
                    xin(a, Manifest.permission.POST_NOTIFICATIONS, MA_THONG_BAO)
                } else {
                    moTrang(a, Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
                        .putExtra(Settings.EXTRA_APP_PACKAGE, a.packageName))
                }

            Loai.BAO_THUC ->
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    moTrang(a, Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM,
                        Uri.parse("package:${a.packageName}")))
                }

            Loai.GIONG_VIET -> Speaker.moCaiDatGiongDoc(a)

            Loai.PIN -> moTrang(a, Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))
        }
    }

    // ---------------------------------------------------------------

    fun coQuyen(ctx: Context, quyen: String): Boolean =
        Build.VERSION.SDK_INT < 23 ||
            ctx.checkSelfPermission(quyen) == PackageManager.PERMISSION_GRANTED

    private fun coThongBao(ctx: Context): Boolean {
        if (Build.VERSION.SDK_INT >= 33 &&
            !coQuyen(ctx, Manifest.permission.POST_NOTIFICATIONS)) return false
        val nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE)
            as? NotificationManager ?: return false
        return nm.areNotificationsEnabled()
    }

    private fun khongToiUuPin(ctx: Context): Boolean {
        val pm = ctx.getSystemService(Context.POWER_SERVICE) as? PowerManager
            ?: return true
        return pm.isIgnoringBatteryOptimizations(ctx.packageName)
    }

    /**
     * Hop thoai he thong con hien duoc khong.
     *
     * Chua xin lan nao -> duoc. Da xin ma he thong con muon giai thich ->
     * duoc. Da xin, va he thong khong muon giai thich nua -> nguoi dung
     * da tu choi han, phai sang Cai dat.
     */
    private fun conXinDuoc(a: Activity, quyen: String): Boolean {
        val p = a.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val daXin = p.getBoolean(quyen, false)
        return !daXin || a.shouldShowRequestPermissionRationale(quyen)
    }

    fun xin(a: Activity, quyen: String, ma: Int) {
        a.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putBoolean(quyen, true).apply()
        a.requestPermissions(arrayOf(quyen), ma)
    }

    private fun moTrang(a: Activity, i: Intent) {
        try {
            a.startActivity(i)
        } catch (_: Exception) {
            try { moTrangAppKhongDeQuy(a) } catch (_: Exception) { }
        }
    }

    private fun moTrangAppKhongDeQuy(a: Activity) {
        a.startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
            Uri.parse("package:${a.packageName}")))
    }
}
