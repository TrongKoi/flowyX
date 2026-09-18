package vn.adc2026.wayfinding

import android.content.Context
import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

/**
 * ====================================================================
 * MA HOA DU LIEU NHAY CAM TREN MAY (v5)
 * ====================================================================
 *
 * Dung cho nhat ky va cam xuc - thu rieng tu nhat trong app. Quy tac da
 * cong bo voi nguoi dung: nhung dong nay KHONG BAO GIO roi khoi may, va
 * nam tren may thi cung o dang ma hoa.
 *
 * ----- Chon thuat toan -----
 *
 * AES-256-GCM. GCM vi no vua ma hoa vua CHONG SUA: neu ai do doi mot byte
 * trong tep prefs, giai ma se nem loi chu khong tra ve chu rac. CBC khong
 * lam duoc dieu do.
 *
 * ----- Khoa nam o dau -----
 *
 * Trong Android Keystore, ten "flowy_nhat_ky_v1". Keystore giu khoa trong
 * phan cung bao mat (TEE/StrongBox) khi may co; app chi duoc GOI khoa chu
 * khong doc duoc byte cua no. Go app la khoa bien mat cung - dung y muon:
 * du ai co ban sao tep prefs cung khong giai ma duoc.
 *
 * Khoa KHONG doi hoi mo khoa man hinh (`setUserAuthenticationRequired`
 * = false). Ly do: nhat ky phai ghi duoc ngay ca khi man hinh vua khoa
 * (vi du ghi xong roi tat man hinh), va bat xac thuc se lam mat noi dung
 * dang go. Bao ve o day la chong doc tep tu ben ngoai, khong phai chong
 * nguoi cam may.
 *
 * ----- May cu (API 24-25) -----
 *
 * Keystore tren mot so may API 24 khong ho tro AES; luc do dung khoa sinh
 * tu SecureRandom luu trong prefs rieng. Yeu hon (ai doc duoc prefs thi
 * doc duoc khoa) nhung van chan duoc viec doc thang bang cong cu sao luu,
 * va van tot hon luu chu tran. `nguyenVen()` cho biet dang o muc nao de
 * man hinh Bao mat noi that voi nguoi dung.
 *
 * ----- Dinh dang -----
 *
 *     base64( IV 12 byte || ban ma || the xac thuc 16 byte )
 *
 * Chuoi khong bat dau bang tien to `v1:` duoc coi la du lieu CU chua ma
 * hoa - doc thang, roi lan luu sau se tu ma hoa. Nguoi dung nang cap app
 * khong mat nhat ky.
 */
object MaHoa {

    private const val TEN_KHOA = "flowy_nhat_ky_v1"
    private const val TIEN_TO = "v1:"
    private const val PREFS_DU_PHONG = "flowy_khoa_du_phong"
    private const val KHOA_DU_PHONG = "k"
    private const val DAI_IV = 12
    private const val DAI_THE = 128

    /** Keystore that hay khoa du phong? Man hinh Bao mat hien dung su that. */
    fun nguyenVen(ctx: Context): Boolean = layKhoa(ctx) != null && dungKeystore

    private var dungKeystore = true

    fun maHoa(ctx: Context, chu: String): String {
        val khoa = layKhoa(ctx) ?: return chu          // khong co khoa: thà luu tran con hon mat du lieu
        return try {
            val c = Cipher.getInstance("AES/GCM/NoPadding")
            c.init(Cipher.ENCRYPT_MODE, khoa)
            val ma = c.doFinal(chu.toByteArray(Charsets.UTF_8))
            val goi = c.iv + ma
            TIEN_TO + Base64.encodeToString(goi, Base64.NO_WRAP)
        } catch (_: Exception) {
            chu
        }
    }

    fun giaiMa(ctx: Context, chu: String): String {
        if (!chu.startsWith(TIEN_TO)) return chu        // du lieu ban cu, chua ma hoa
        val khoa = layKhoa(ctx) ?: return ""
        return try {
            val goi = Base64.decode(chu.removePrefix(TIEN_TO), Base64.NO_WRAP)
            val c = Cipher.getInstance("AES/GCM/NoPadding")
            c.init(Cipher.DECRYPT_MODE, khoa, GCMParameterSpec(DAI_THE, goi, 0, DAI_IV))
            String(c.doFinal(goi, DAI_IV, goi.size - DAI_IV), Charsets.UTF_8)
        } catch (_: Exception) {
            // Khoa mat (go app roi cai lai, khoi phuc may khac): khong con
            // cach nao doc duoc. Tra ve rong de app van chay.
            ""
        }
    }

    private fun layKhoa(ctx: Context): SecretKey? {
        try {
            val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
            (ks.getEntry(TEN_KHOA, null) as? KeyStore.SecretKeyEntry)?.secretKey?.let {
                dungKeystore = true
                return it
            }
            val gen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
            val spec = KeyGenParameterSpec.Builder(TEN_KHOA,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .apply {
                    // Sao luu len may khac khong mang theo khoa duoc, va dung the:
                    // nhat ky khong nen di theo ban sao luu dam may.
                    if (Build.VERSION.SDK_INT >= 28) setIsStrongBoxBacked(false)
                }
                .build()
            gen.init(spec)
            dungKeystore = true
            return gen.generateKey()
        } catch (_: Exception) {
            return khoaDuPhong(ctx)
        }
    }

    /** May khong dung duoc Keystore: khoa ngau nhien luu rieng. */
    private fun khoaDuPhong(ctx: Context): SecretKey? = try {
        dungKeystore = false
        val p = ctx.getSharedPreferences(PREFS_DU_PHONG, Context.MODE_PRIVATE)
        val cu = p.getString(KHOA_DU_PHONG, null)
        val byteKhoa = if (cu != null) Base64.decode(cu, Base64.NO_WRAP) else {
            ByteArray(32).also {
                SecureRandom().nextBytes(it)
                p.edit().putString(KHOA_DU_PHONG, Base64.encodeToString(it, Base64.NO_WRAP)).apply()
            }
        }
        SecretKeySpec(byteKhoa, "AES")
    } catch (_: Exception) {
        null
    }
}
