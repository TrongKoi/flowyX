package vn.adc2026.wayfinding

import android.app.AlarmManager
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import java.util.Calendar

/**
 * BAO GIO - dat chuong cho cac loi nhac nguoi dung tu dat.
 *
 * --------------------------------------------------------------------
 * VI SAO PHAI LA CHUONG HE THONG, KHONG PHAI VONG LAP TRONG APP
 * --------------------------------------------------------------------
 *
 * Mot loi nhac chi bao khi app dang mo la mot loi nhac vo dung: luc can
 * no nhat la luc nguoi dung dang o trong mot app khac.
 *
 * `AlarmManager` chay ke ca khi app da bi he dieu hanh don di.
 *
 * --------------------------------------------------------------------
 * QUYEN BAO THUC CHINH XAC - VA VI SAO BAN CU BI SAP
 * --------------------------------------------------------------------
 *
 * Ban cu ghi rang `setAlarmClock` khong can SCHEDULE_EXACT_ALARM. SAI.
 * Tu API 31 (Android 12) no CUNG can quyen do, va tu Android 14 quyen
 * nay bi TAT MAC DINH voi app moi cai. Ket qua: tren Galaxy Tab S7 FE
 * (Android 14), dat loi nhac xong la app sap voi SecurityException.
 *
 * Cach sua gio:
 *
 *     1. Manifest khai bao SCHEDULE_EXACT_ALARM
 *     2. Truoc khi dat, hoi `canScheduleExactAlarms()`
 *          co quyen   -> setAlarmClock, dung phut, xuyen Doze
 *          chua co    -> setAndAllowWhileIdle, co the TRE vai phut,
 *                        nhung KHONG SAP va loi nhac van toi
 *     3. Kiem tra quyen (Cai dat) dan nguoi dung sang man hinh cap quyen, va dat lai
 *        chuong o onResume khi ho quay ve
 *     4. Moi lan goi AlarmManager deu boc try/catch SecurityException -
 *        mot loi nhac khong dat duoc KHONG duoc phep lam sap app
 *
 * Khong dung USE_EXACT_ALARM: quyen do Google Play chi cho app bao thuc
 * hoac lich, va Flowy khong phai loai do.
 *
 * Danh doi cua setAlarmClock: hien bieu tuong bao thuc tren thanh trang
 * thai. Chap nhan duoc - do la dau hieu nhin thay duoc rang he thong dang
 * theo gio ho.
 *
 * --------------------------------------------------------------------
 * NOI DUNG THONG BAO LA CHU CUA NGUOI DUNG, VA KHONG DI DAU CA
 * --------------------------------------------------------------------
 *
 * Chuoi trong thong bao la ten nguoi dung tu dat, khong them mot chu
 * nao. App khong biet no la gi, khong doi chieu danh muc nao, va khong
 * gui no qua cau noi - xem `SoNhac`.
 *
 * Va khong dem: lop nay KHONG ghi nhan nguoi dung co lam theo loi nhac
 * hay khong. Khong co truong `da_lam`, khong co thong ke. Xem
 * `adhd/nhacviec.py` ve ly do - ca ly do phap ly lan ly do thuc te.
 *
 * --------------------------------------------------------------------
 * KHONG CAN androidx
 * --------------------------------------------------------------------
 *
 * WorkManager la androidx, va du an co y khong dung androidx nao. No
 * cung khong hop viec nay: no bao dam cong viec SE CHAY, chu khong bao
 * dam chay DUNG LUC. Mot loi nhac di tre 10 phut la mot loi nhac vo
 * dung.
 */
object BaoGio {

    const val KENH = "loi_nhac"

    private const val TEN_CAU = "cau"
    private const val TEN_CHI_SO = "chi_so"
    private const val TEN_LAP_LAI = "lap_lai"

    /** Ma yeu cau bat dau tu day, de khong dung voi ma nao khac. */
    private const val MA_GOC = 9000

    /**
     * Dat lai TOAN BO chuong theo so hien tai.
     *
     * Huy het roi dat lai thay vi tinh phan chenh lech: danh sach ngan,
     * va mot chuong sot lai sau khi nguoi dung xoa loi nhac la loi te
     * hon nhieu so voi vai phep goi thua.
     */
    /** Ket qua dat chuong, de noi goi biet co can xin quyen khong. */
    enum class KetQua {
        /** Dat chinh xac tung phut. */
        CHINH_XAC,
        /** Chua co quyen - da dat ban co the tre vai phut. */
        CO_THE_TRE,
        /** He dieu hanh tu choi hoan toan. Khong sap, nhung khong co chuong. */
        KHONG_DAT_DUOC,
        /** Khong co loi nhac nao de dat. */
        KHONG_CO_GI,
    }

    /**
     * App co duoc dat bao thuc CHINH XAC khong.
     *
     * Duoi API 31 luon co. Tu API 31 phai hoi he dieu hanh - nguoi dung
     * co the bat/tat trong Cai dat bat cu luc nao.
     */
    @JvmStatic
    fun coTheDatChinhXac(ctx: Context): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return true
        val am = ctx.getSystemService(Context.ALARM_SERVICE) as? AlarmManager
            ?: return false
        return am.canScheduleExactAlarms()
    }

    /**
     * Dat lai TOAN BO chuong theo so hien tai.
     *
     * Huy het roi dat lai thay vi tinh phan chenh lech: danh sach ngan,
     * va mot chuong sot lai sau khi nguoi dung xoa loi nhac la loi te
     * hon nhieu so voi vai phep goi thua.
     */
    @JvmStatic
    fun datLai(ctx: Context, so: SoNhac, toiDa: Int = TOI_DA_CHUONG): KetQua {
        huyHet(ctx, toiDa)
        taoKenh(ctx)
        val am = ctx.getSystemService(Context.ALARM_SERVICE) as? AlarmManager
            ?: return KetQua.KHONG_DAT_DUOC
        if (so.danhSach.isEmpty()) return KetQua.KHONG_CO_GI

        val chinhXac = coTheDatChinhXac(ctx)
        var ketQua = if (chinhXac) KetQua.CHINH_XAC else KetQua.CO_THE_TRE

        so.danhSach.take(toiDa).forEachIndexed { i, ln ->
            val luc = lanToi(ln.gio)
            val pi = pendingIntent(ctx, i, ln.cau(), ln.lapLaiHangNgay)
            try {
                if (chinhXac) {
                    // setAlarmClock can hai PendingIntent: mot de chay, mot
                    // de nguoi dung cham vao bieu tuong bao thuc.
                    am.setAlarmClock(AlarmManager.AlarmClockInfo(luc, pi), pi)
                } else {
                    // Khong can quyen. He dieu hanh duoc phep don lai vai
                    // phut, nhung van xuyen Doze.
                    am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, luc, pi)
                }
            } catch (e: SecurityException) {
                // Quyen bi thu hoi giua chung. Thu ban khong can quyen.
                try {
                    am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, luc, pi)
                    ketQua = KetQua.CO_THE_TRE
                } catch (_: SecurityException) {
                    ketQua = KetQua.KHONG_DAT_DUOC
                }
            }
        }
        return ketQua
    }

    @JvmStatic
    fun huyHet(ctx: Context, toiDa: Int = TOI_DA_CHUONG) {
        val am = ctx.getSystemService(Context.ALARM_SERVICE) as? AlarmManager
            ?: return
        for (i in 0 until toiDa) {
            try {
                am.cancel(pendingIntent(ctx, i, "", false))
            } catch (_: SecurityException) {
                // Khong the xay ra voi cancel, nhung khong duoc phep sap.
            }
        }
    }

    /**
     * Moc tuyet doi cho lan bao toi, tinh tu `phut` trong ngay.
     *
     * Gio hom nay da qua thi lay ngay mai. Khong bao ve qua khu.
     */
    internal fun lanToi(phutTrongNgay: Double,
                        bayGio: Long = System.currentTimeMillis()): Long {
        val c = Calendar.getInstance().apply {
            timeInMillis = bayGio
            set(Calendar.HOUR_OF_DAY, (phutTrongNgay / 60).toInt())
            set(Calendar.MINUTE, (phutTrongNgay % 60).toInt())
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }
        if (c.timeInMillis <= bayGio) c.add(Calendar.DAY_OF_YEAR, 1)
        return c.timeInMillis
    }

    private fun pendingIntent(ctx: Context, chiSo: Int, noiDung: String,
                              lapLai: Boolean): PendingIntent {
        val i = Intent(ctx, NhacReceiver::class.java).apply {
            putExtra(TEN_CAU, noiDung)
            putExtra(TEN_CHI_SO, chiSo)
            putExtra(TEN_LAP_LAI, lapLai)
        }
        // FLAG_IMMUTABLE la BAT BUOC tu API 31. Co tu API 23 nen dat
        // thang, khong can re nhanh theo phien ban.
        val co = PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        return PendingIntent.getBroadcast(ctx, MA_GOC + chiSo, i, co)
    }

    fun taoKenh(ctx: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE)
            as? NotificationManager ?: return
        if (nm.getNotificationChannel(KENH) != null) return

        val kenh = NotificationChannel(
            KENH,
            ctx.getString(R.string.kenh_nhac_gio),
            // HIGH chu khong phai DEFAULT: bao nay phai xuyen qua duoc
            // luc nguoi dung dang tap trung vao viec khac - do chinh la
            // tinh huong no sinh ra de xu ly.
            NotificationManager.IMPORTANCE_HIGH,
        ).apply {
            description = ctx.getString(R.string.kenh_nhac_gio_mo_ta)
            enableVibration(true)
        }
        nm.createNotificationChannel(kenh)
    }

    const val TOI_DA_CHUONG = 32

    /** Hien thong bao khi toi gio, roi dat lai cho ngay mai. */
    class NhacReceiver : BroadcastReceiver() {
        override fun onReceive(ctx: Context, intent: Intent) {
            val noiDung = intent.getStringExtra(TEN_CAU) ?: return
            if (noiDung.isEmpty()) return
            val chiSo = intent.getIntExtra(TEN_CHI_SO, 0)

            val nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE)
                as? NotificationManager ?: return

            // v4: loi nhac da gop vao Ke hoach - mo tab Ke hoach.
            val mo = Intent(ctx, ViecCanLamActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or
                    Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
            val pi = PendingIntent.getActivity(
                ctx, 0, mo,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
            )

            val b = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                Notification.Builder(ctx, KENH)
            } else {
                @Suppress("DEPRECATION")
                Notification.Builder(ctx)
            }

            val tb = b.setContentTitle(ctx.getString(R.string.nhac_tieu_de))
                .setContentText(noiDung)
                // Bat buoc co, neu khong thong bao khong hien. Dung icon
                // san co cua he thong de khong phai them tai nguyen anh.
                .setSmallIcon(android.R.drawable.ic_popup_reminder)
                .setContentIntent(pi)
                .setAutoCancel(true)
                // Doc HET cau, khong cat ngang. Cau bi cat o giua thi
                // nguoi dung phai mo ra doc - them mot buoc khong can.
                .setStyle(Notification.BigTextStyle().bigText(noiDung))
                .build()

            // POST_NOTIFICATIONS tu API 33: khong co quyen thi post()
            // im lang khong lam gi. Bat SecurityException cho chac - mot
            // loi nhac khong hien ra KHONG duoc phep lam sap app.
            try {
                nm.notify(MA_GOC + chiSo, tb)
            } catch (_: SecurityException) {
                // Chua cap quyen thong bao. App van chay binh thuong,
                // chi mat lop nhac.
            }

            // Dat lai cho ngay mai. Doc lai so tu dia thay vi tin vao
            // extras: nguoi dung co the da sua loi nhac tu luc chuong
            // duoc dat.
            if (intent.getBooleanExtra(TEN_LAP_LAI, false)) {
                datLai(ctx, SoNhac.doc(ctx))
            }
        }
    }

    /**
     * Dat lai chuong sau khi KHOI DONG LAI MAY, cap nhat app, doi gio, hoac
     * khi nguoi dung vua cap quyen bao thuc chinh xac.
     *
     * AlarmManager XOA SACH chuong khi may tat. Thieu lop nay thi nguoi
     * dung sac pin qua dem, sang ra loi nhac im lang - va ho khong co cach
     * nao biet la no da mat.
     */
    class KhoiDongReceiver : BroadcastReceiver() {
        override fun onReceive(ctx: Context, intent: Intent) {
            when (intent.action) {
                Intent.ACTION_BOOT_COMPLETED,
                Intent.ACTION_MY_PACKAGE_REPLACED,
                Intent.ACTION_TIME_CHANGED,
                Intent.ACTION_TIMEZONE_CHANGED,
                AlarmManager.ACTION_SCHEDULE_EXACT_ALARM_PERMISSION_STATE_CHANGED,
                -> {
                    datLai(ctx, SoNhac.doc(ctx))
                    LichBao.datLai(ctx)
                }
            }
        }
    }
}
