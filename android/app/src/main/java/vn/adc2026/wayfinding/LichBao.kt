package vn.adc2026.wayfinding

import android.app.AlarmManager
import android.app.Notification
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build

/**
 * Chuong cho ke hoach trong lich.
 *
 * Cung cach voi `BaoGio` (loi nhac hang ngay), va dung chung quyen bao
 * thuc chinh xac, kenh thong bao, va receiver khoi dong lai may.
 *
 * AlarmManager khong co "lap hang tuan dung phut", nen lop nay dat CAC
 * LAN TOI GAN NHAT (toi da 48, trong 8 ngay). Moi lan mot chuong reo, no
 * tinh va dat lai - ke hoach lap lai van reo mai mai. Mo app, sua lich,
 * khoi dong may, doi gio cung dat lai.
 */
object LichBao {

    private const val MA_GOC = 20000
    private const val TOI_DA = 48
    private const val PREFS = "flowy_lich_bao"
    private const val KHOA_SO_DA_DAT = "so_da_dat"
    private const val TEN_CAU = "cau"
    private const val TEN_ID = "id"

    fun datLai(ctx: Context, so: SoLich = SoLich.doc(ctx)): BaoGio.KetQua {
        val am = ctx.getSystemService(Context.ALARM_SERVICE) as? AlarmManager
            ?: return BaoGio.KetQua.KHONG_DAT_DUOC
        val p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

        // Huy dung so chuong da dat lan truoc.
        val cu = p.getInt(KHOA_SO_DA_DAT, TOI_DA)
        for (i in 0 until maxOf(cu, 0)) {
            try { am.cancel(pi(ctx, i, "", "")) } catch (_: SecurityException) { }
        }

        val ds = Lich.lanNhacToi(so.danhSach, SoLich.bayGio(), toiDa = TOI_DA)
            // Lan da danh dau xong truoc gio thi khong nhac nua.
            .filter { Lich.khoaXong(it.keHoach.id, it.ngayDienRa) !in so.daXong }
        p.edit().putInt(KHOA_SO_DA_DAT, ds.size).apply()
        if (ds.isEmpty()) return BaoGio.KetQua.KHONG_CO_GI

        BaoGio.taoKenh(ctx)
        val chinhXac = BaoGio.coTheDatChinhXac(ctx)
        var kq = if (chinhXac) BaoGio.KetQua.CHINH_XAC else BaoGio.KetQua.CO_THE_TRE
        ds.forEachIndexed { i, ln ->
            val luc = SoLich.sangMili(ln.phutTuyetDoi)
            val y = pi(ctx, i, "${ln.keHoach.emoji} ${Lich.cauNhac(ln)}", ln.keHoach.id)
            try {
                if (chinhXac) am.setAlarmClock(AlarmManager.AlarmClockInfo(luc, y), y)
                else am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, luc, y)
            } catch (_: SecurityException) {
                try {
                    am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, luc, y)
                    kq = BaoGio.KetQua.CO_THE_TRE
                } catch (_: SecurityException) {
                    kq = BaoGio.KetQua.KHONG_DAT_DUOC
                }
            }
        }
        return kq
    }

    private fun pi(ctx: Context, i: Int, cau: String, id: String): PendingIntent {
        val intent = Intent(ctx, Receiver::class.java)
            .putExtra(TEN_CAU, cau).putExtra(TEN_ID, id)
        return PendingIntent.getBroadcast(ctx, MA_GOC + i, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    }

    class Receiver : BroadcastReceiver() {
        override fun onReceive(ctx: Context, intent: Intent) {
            val cau = intent.getStringExtra(TEN_CAU)
            if (!cau.isNullOrBlank()) {
                val nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager
                // v4: Ke hoach ben duoi, Lich ben tren - Back khong roi ra ngoai app.
                val mo = NgaXep.mo(ctx, LichActivity::class.java, 1)
                val b = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
                    Notification.Builder(ctx, BaoGio.KENH)
                else @Suppress("DEPRECATION") Notification.Builder(ctx)
                val tb = b.setContentTitle(ctx.getString(R.string.lich))
                    .setContentText(cau)
                    .setStyle(Notification.BigTextStyle().bigText(cau))
                    .setSmallIcon(android.R.drawable.ic_popup_reminder)
                    .setContentIntent(mo)
                    .setAutoCancel(true)
                    .build()
                try {
                    nm?.notify(MA_GOC + (intent.getStringExtra(TEN_ID)?.hashCode() ?: 0) % 1000, tb)
                } catch (_: SecurityException) {
                    // Chua co quyen thong bao - khong duoc lam sap.
                }
            }
            // Tinh va dat cac lan toi.
            datLai(ctx)
        }
    }
}
