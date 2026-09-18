package vn.adc2026.wayfinding

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/**
 * NHAT KY - cua nguoi dung, va app KHONG DIEN GIAI no.
 *
 * Ban Kotlin cua `adc_wayfinding/wayfinding/adhd/nhatky.py`. Ranh gioi
 * quyet dinh ca phan phap ly lan phan thiet ke nam o mot cho:
 *
 *     ghi chep   nguoi dung viet, doc lai, va TU rut ra ket luan
 *     theo doi   app do luong, cham diem, va rut ra ket luan HO ho
 *
 * Cai thu nhat la mot quyen so. Cai thu hai la mot thiet bi y te.
 *
 * Nen lop nay KHONG CO PHEP TINH NAO. Khong trung binh, khong xu huong,
 * khong "tuan nay ban kem hon tuan truoc". Thu duy nhat no lam voi noi
 * dung nguoi dung viet la SAP XEP THEO THOI GIAN va IN RA.
 *
 * --------------------------------------------------------------------
 * CAM XUC GHI BANG CHU, KHONG PHAI THANG DIEM
 * --------------------------------------------------------------------
 *
 * Thang 1-5 tien cho app hon nhieu: de luu, de ve bieu do. Do chinh xac
 * la ly do khong dung no - mot con so chi co ich khi co gi do cong no
 * lai, ma cong lai chinh la thu khong duoc lam.
 *
 * "mệt", "ổn", "như bị kéo từng mảnh" hop le nhu nhau.
 *
 * --------------------------------------------------------------------
 * LOP NAY KHONG DUOC DI QUA CAU NOI
 * --------------------------------------------------------------------
 *
 * Bang trong `bridge.py`: nhat ky cam xuc khong bao gio duoc len duong
 * truyen. Giong `SoNhac` - khong cham vao `Payload` hay `BridgeClient`.
 *
 * Va app khong gui no cho ai. `xuatVanBan()` tra ve mot CHUOI; buoc ghi
 * tep di qua trinh chon tep cua he dieu hanh, tuc la nguoi dung tu chon
 * cho. Xem `MainActivity.xuatNhatKy()`.
 */
class SoNhatKy private constructor(
    val muc: MutableList<Muc>,
) {

    constructor() : this(mutableListOf())

    /** Mot muc nhat ky. Ca hai truong deu la CHU cua nguoi dung. */
    data class Muc(
        /** Mili giay, gio he thong. */
        val luc: Long,
        /**
         * Tieu de mot dong (v5). Tach khoi noi dung vi trong danh sach,
         * mot dong dam de nhan ra giup tim lai ban ghi cu nhanh hon nhieu
         * so voi doc trich doan. Rong cung duoc: luc do danh sach hien
         * dong dau cua noi dung.
         */
        val tieuDe: String = "",
        val noiDung: String,
        /** Ho cam thay the nao, bang chu cua ho. */
        val theNao: String? = null,
    ) {
        /** Mot dong trong ban xuat. Khong them nhan xet nao. */
        fun dong(): String {
            val gio = java.text.SimpleDateFormat(
                "yyyy-MM-dd HH:mm", java.util.Locale.US)
                .format(java.util.Date(luc))
            return if (theNao != null) "$gio  [$theNao] $noiDung"
            else "$gio  $noiDung"
        }
    }

    fun ghi(noiDung: String, theNao: String? = null, tieuDe: String = "",
            luc: Long = System.currentTimeMillis()): Boolean {
        val nd = noiDung.trim()
        if (nd.length < MIN_KY_TU) return false
        val tn = theNao?.trim()?.ifEmpty { null }
        muc.add(Muc(luc, tieuDe.trim(), nd, tn))
        if (muc.size > TOI_DA_MUC) {
            // Muc cu nhat roi ra. Day la gioi han RIENG TU, khong phai
            // gioi han ky thuat: mot quyen so khong gioi han la mot ho
            // so dai vo han ve mot nguoi.
            while (muc.size > TOI_DA_MUC) muc.removeAt(0)
        }
        return true
    }

    /**
     * Nguoi dung phai xoa duoc bat cu muc nao, bat cu luc nao.
     *
     * Quyen xoa la mot phan cua quyen so huu. Mot quyen so khong xe
     * duoc trang la mot ho so.
     */
    fun xoa(chiSo: Int): Boolean {
        if (chiSo !in muc.indices) return false
        muc.removeAt(chiSo)
        return true
    }

    fun xoaHet() = muc.clear()

    /** Dat lai mot muc vua xoa vao dung cho cu - cho nut Hoan tac. */
    fun chen(chiSo: Int, m: Muc) {
        muc.add(chiSo.coerceIn(0, muc.size), m)
    }

    /** Sua noi dung mot muc (tim theo `luc`). Rong qua thi khong sua. */
    fun sua(luc: Long, noiDung: String, theNao: String?, tieuDe: String = ""): Boolean {
        val i = muc.indexOfFirst { it.luc == luc }
        val nd = noiDung.trim()
        if (i < 0 || nd.length < MIN_KY_TU) return false
        muc[i] = Muc(luc, tieuDe.trim(), nd, theNao?.trim()?.ifEmpty { null })
        return true
    }

    /** Vai muc gan nhat, de nguoi dung DOC LAI - khong de app doc. */
    fun ganDay(soMuc: Int = 10): List<Muc> =
        if (soMuc <= 0) emptyList() else muc.takeLast(soMuc)

    /**
     * Toan bo so, dang van ban thuan.
     *
     * Tra ve CHUOI. Khong mo tep, khong goi mang. Nguoi dung quyet dinh
     * chuoi nay di dau - ke ca khi cau tra loi la khong di dau ca.
     *
     * Van ban thuan chu khong phai dinh dang rieng: nguoi dung phai doc
     * duoc so cua chinh ho ma khong can app nay.
     */
    fun xuatVanBan(): String =
        if (muc.isEmpty()) "" else muc.joinToString("\n") { it.dong() } + "\n"

    /**
     * Luu. Toan bo danh sach duoc MA HOA truoc khi ghi (AES-256-GCM, khoa
     * trong Android Keystore - xem `MaHoa`). Khong co dong nao roi khoi
     * may, va nam tren may cung khong doc duoc bang cong cu sao luu.
     */
    fun luu(ctx: Context) {
        val mang = JSONArray()
        for (m in muc) {
            val o = JSONObject().put("luc", m.luc).put("noi_dung", m.noiDung)
            if (m.tieuDe.isNotBlank()) o.put("tieu_de", m.tieuDe)
            if (m.theNao != null) o.put("the_nao", m.theNao)
            mang.put(o)
        }
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString(KHOA, MaHoa.maHoa(ctx, mang.toString())).apply()
    }

    companion object {
        /** Ghi chep ngan hon nay coi nhu bam nham. */
        const val MIN_KY_TU = 2

        const val TOI_DA_MUC = 500

        private const val PREFS = "flowy_nhat_ky"
        private const val KHOA = "muc"

        fun doc(ctx: Context): SoNhatKy {
            val s = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getString(KHOA, null) ?: return SoNhatKy()
            // Ban truoc luu chu tran: `giaiMa` tra ve nguyen van, va lan
            // luu sau se tu ma hoa lai. Nang cap app khong mat nhat ky.
            return tuJson(MaHoa.giaiMa(ctx, s))
        }

        /** So hong thi bat dau lai tu trong, khong lam sap app. */
        fun tuJson(s: String): SoNhatKy {
            val so = SoNhatKy()
            try {
                val mang = JSONArray(s)
                for (i in 0 until mang.length()) {
                    val o = mang.optJSONObject(i) ?: continue
                    if (!o.has("luc") || !o.has("noi_dung")) continue
                    so.ghi(o.optString("noi_dung", ""),
                        if (o.isNull("the_nao")) null
                        else o.optString("the_nao", "").ifEmpty { null },
                        o.optString("tieu_de", ""),
                        o.optLong("luc", 0L))
                }
            } catch (_: Exception) {
                return SoNhatKy()
            }
            return so
        }
    }
}
