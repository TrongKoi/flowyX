package vn.adc2026.wayfinding

import android.app.Activity
import android.app.PendingIntent
import android.content.Intent
import android.net.Uri
import android.nfc.NdefMessage
import android.nfc.NdefRecord
import android.nfc.NfcAdapter
import android.os.Build
import android.util.Log
import java.nio.charset.StandardCharsets

/**
 * Mo app bang cach CHAM dien thoai vao the NFC GAN TREN DAY DEO.
 *
 * --------------------------------------------------------------------
 * THE NAM TREN DAY DEO, KHONG PHAI TREN TUONG
 * --------------------------------------------------------------------
 *
 * Day la diem khac biet quan trong nhat, va no go duoc dung phan doi da
 * khien du an bo ArUco.
 *
 * The dan tren TUONG thi phai xin phep toa nha, phai dan truoc khi dung
 * duoc, va he thong chi chay o nhung noi da dan. The gan tren DAY DEO
 * thi di theo nguoi dung: mot the duy nhat, thuoc ve ho, dung duoc o
 * moi toa nha. Khong phai xin phep ai ca.
 *
 * Thao tac tu nhien roi vao dung thu tu:
 *
 *     1. Cam dien thoai, cham vao the tren day deo  -> app mo
 *     2. Cai dien thoai vao day deo                 -> bat dau di
 *
 * Buoc 1 va buoc 2 nam ngay canh nhau ve mat vat ly. Nguoi dung dang
 * cam dien thoai va sap gan no vao day deo - cham mot cai giua duong la
 * gan nhu khong ton them thao tac nao.
 *
 * --------------------------------------------------------------------
 * VI SAO KHONG DUNG TRINH DOC MAN HINH LA DU
 * --------------------------------------------------------------------
 *
 * TalkBack mo duoc app, nhung duong di khong ngan: danh thuc may, mo
 * khoa, vuot tim bieu tuong giua hang chuc app, nghe doc tung ten - ma
 * tat ca trong luc mot tay dang giu gay trang.
 *
 * Cham the la MOT thao tac, KHONG CAN NHIN, va Android mo duoc ngay ca
 * khi man hinh dang khoa nen bo duoc ca buoc mo khoa.
 *
 * --------------------------------------------------------------------
 * DINH DANG THE
 * --------------------------------------------------------------------
 *
 * Ghi bang bat ky app ghi NFC nao (vi du "NFC Tools"), chon kieu URI:
 *
 *     wayfinding://go                    chi mo app
 *     wayfinding://go?mount=nguc         mo app, dat kieu deo
 *     wayfinding://go?to=S               mo app va di luon toi S
 *     wayfinding://go?mount=nguc&to=S    ca hai
 *
 * Tham so `mount` cho biet the nay gan tren kieu day deo nao, de ho so
 * hinh hoc (goc chuc, do cao) duoc dat dung ma khong phai hoi. Gia tri:
 * `nguc`, `co`, `vai`.
 *
 * Nen ghi kem mot ban ghi AAR tro toi `vn.adc2026.wayfinding`. May chua
 * cai app se duoc dua thang toi trang cai dat thay vi khong phan ung gi.
 */
object NfcLauncher {

    const val SCHEME = "wayfinding"
    const val HOST = "go"

    /** Kieu deo hop le, khop voi ho so trong `profile.py`. */
    val KIEU_DEO = setOf("nguc", "co", "vai")

    /** Thong tin doc duoc tu the. Truong nao khong co thi de null. */
    data class Destination(
        val start: String?,
        val to: String?,
        /** Kieu day deo the nay gan tren: "nguc", "co", "vai". */
        val mount: String?,
    )

    /**
     * Doc diem den tu intent mo app.
     *
     * Tra null khi intent nay khong phai do cham the NFC - truong hop
     * pho bien nhat, vi app con duoc mo bang bieu tuong va bang o Cai
     * dat nhanh.
     */
    fun parse(intent: Intent?): Destination? {
        if (intent == null) return null

        val uri: Uri? = when (intent.action) {
            NfcAdapter.ACTION_NDEF_DISCOVERED -> intent.data ?: ndefUri(intent)
            Intent.ACTION_VIEW -> intent.data
            else -> null
        }
        if (uri == null) return null
        if (uri.scheme != SCHEME) return null

        return try {
            Destination(
                start = uri.getQueryParameter("start")?.trim()?.ifEmpty { null },
                to = uri.getQueryParameter("to")?.trim()?.ifEmpty { null },
                // Kieu deo la va khong duoc chap nhan: dat sai goc chuc
                // se lam vung mu duoi chan lech han so voi tam quet gay
                // trang, ma nguoi dung khong co cach nao biet.
                mount = uri.getQueryParameter("mount")?.trim()?.lowercase()
                    ?.takeIf { it in KIEU_DEO },
            )
        } catch (e: UnsupportedOperationException) {
            // URI khong phai dang phan cap thi khong co tham so truy van.
            // Van coi la mot lan cham the hop le - chi la khong kem
            // diem den.
            Destination(null, null, null)
        }
    }

    /** Lay URI tu ban ghi NDEF khi `intent.data` khong duoc dien san. */
    private fun ndefUri(intent: Intent): Uri? {
        val raw = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            intent.getParcelableArrayExtra(
                NfcAdapter.EXTRA_NDEF_MESSAGES, NdefMessage::class.java)
        } else {
            @Suppress("DEPRECATION")
            intent.getParcelableArrayExtra(NfcAdapter.EXTRA_NDEF_MESSAGES)
        } ?: return null

        for (m in raw) {
            val msg = m as? NdefMessage ?: continue
            for (r in msg.records) {
                val u = uriCuaBanGhi(r) ?: continue
                if (u.scheme == SCHEME) return u
            }
        }
        return null
    }

    private fun uriCuaBanGhi(r: NdefRecord): Uri? = try {
        when {
            r.tnf == NdefRecord.TNF_WELL_KNOWN &&
                r.type.contentEquals(NdefRecord.RTD_URI) -> r.toUri()
            r.tnf == NdefRecord.TNF_ABSOLUTE_URI ->
                Uri.parse(String(r.type, StandardCharsets.UTF_8))
            else -> null
        }
    } catch (e: Exception) {
        // The hong hoac ghi sai dinh dang. Bo qua ban ghi nay thay vi
        // lam sap app - nguoi dung cham nham mot the la tau xe buyt thi
        // khong co ly do gi app phai chet.
        Log.d(TAG, "ban ghi NDEF khong doc duoc", e)
        null
    }

    /**
     * Bat nhan the khi app DANG MO (foreground dispatch).
     *
     * Khong co buoc nay thi cham the luc app dang chay se khong lam gi,
     * hoac te hon la mo lai app tu dau. Goi trong `onResume()`.
     */
    fun enableForeground(activity: Activity) {
        val adapter = NfcAdapter.getDefaultAdapter(activity) ?: return
        if (!adapter.isEnabled) return

        val intent = Intent(activity, activity.javaClass).addFlags(
            Intent.FLAG_ACTIVITY_SINGLE_TOP)
        val co = PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE
        val pi = PendingIntent.getActivity(activity, 0, intent, co)

        try {
            adapter.enableForegroundDispatch(activity, pi, null, null)
        } catch (e: IllegalStateException) {
            // Goi khi activity khong o trang thai resumed. Khong nghiem
            // trong: mat kha nang nhan the luc dang mo, van nhan duoc
            // the luc app dong.
            Log.d(TAG, "khong bat duoc foreground dispatch", e)
        }
    }

    /** Goi trong `onPause()`, doi xung voi `enableForeground`. */
    fun disableForeground(activity: Activity) {
        val adapter = NfcAdapter.getDefaultAdapter(activity) ?: return
        try {
            adapter.disableForegroundDispatch(activity)
        } catch (e: IllegalStateException) {
            Log.d(TAG, "khong tat duoc foreground dispatch", e)
        }
    }

    /** May co NFC va dang bat khong. */
    fun available(activity: Activity): Boolean =
        NfcAdapter.getDefaultAdapter(activity)?.isEnabled == true

    private const val TAG = "NfcLauncher"
}
