package vn.adc2026.wayfinding

import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import android.service.quicksettings.TileService

/**
 * O trong bang Cai dat nhanh, de mo app ma khong phai tim bieu tuong.
 *
 * ------------------------------------------------------------------
 * Vi sao can them mot cach mo nua
 * ------------------------------------------------------------------
 *
 * Tim mot bieu tuong tren man hinh chinh bang TalkBack nghia la vuot
 * tay qua tung ung dung mot, nghe doc ten tung cai, cho toi khi trung.
 * Man hinh nhieu app thi viec do rat lau - va nguoi dung can mo app
 * NAY dung luc ho dang dung giua hanh lang, khong biet duong.
 *
 * Ba cach mo, tu nhanh den cham:
 *
 *   1. Giong noi   "Ok Google, mo Chi duong ADC"
 *                  Khong can code gi ca - Android tu mo app theo ten.
 *                  Dieu kien duy nhat la TEN APP phai de doc, de nghe.
 *
 *   2. O Cai dat nhanh (file nay)
 *                  Vuot hai ngon tu canh tren xuong, TalkBack doc ten
 *                  tung o. Nguoi dung keo o nay len dau bang mot lan,
 *                  sau do luon o vi tri co dinh - va vi tri co dinh la
 *                  thu quan trong nhat voi nguoi khiem thi.
 *
 *   3. Bieu tuong tren man hinh chinh
 *                  Cham dat, nhung van giu vi no la cach quen thuoc.
 */
class LaunchTileService : TileService() {

    override fun onClick() {
        super.onClick()

        val intent = Intent(this, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or
                     Intent.FLAG_ACTIVITY_CLEAR_TOP)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            // Tu API 34, ban cu bi khoa lai vi ly do bao mat
            startActivityAndCollapse(
                PendingIntent.getActivity(
                    this, 0, intent,
                    PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
                )
            )
        } else {
            @Suppress("DEPRECATION")
            startActivityAndCollapse(intent)
        }
    }
}
