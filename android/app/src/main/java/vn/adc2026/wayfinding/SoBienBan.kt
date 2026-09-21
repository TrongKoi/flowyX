package vn.adc2026.wayfinding

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/**
 * SO BIEN BAN CUOC HOP - song tren may nay, khong len duong truyen.
 *
 * Hai duong vao (v4):
 *
 *   1. GHI TAY - khi khong co ban ghi am. Ten, nguoi du, da chot, viec,
 *      cau hoi con mo. (`GhiBienBanActivity`)
 *
 *   2. NHAP TU MEETY - chay loi Meety tren laptop tu tep ghi am / transcript
 *      Zoom-Meet-Teams, ra `<id>_minutes.json` (schema `StructuredMinutes`),
 *      mo tep do trong app. KHONG mang giao dien Meety vao app - chi lay du
 *      lieu da co cau truc. (`tuMeety`)
 *
 * Mot duong ra: Word (.docx), hai ban - Tieu chuan va De doc (`khoiDocx`).
 */
class SoBienBan private constructor(val danhSach: MutableList<BienBan>) {

    constructor() : this(mutableListOf())

    data class BienBan(
        val luc: Long,
        val ten: String,
        val daChot: String,
        val viec: List<String>,
        val tomTat: List<String> = emptyList(),
        val nguoiDu: List<String> = emptyList(),
        val cauHoi: List<String> = emptyList(),
        val thoiLuongPhut: Int? = null,
        /** "tay" hoac "meety". */
        val nguon: String = NGUON_TAY,
    ) {
        fun ngayDoc(): String = java.text.SimpleDateFormat(
            "dd/MM · HH:mm", java.util.Locale.US).format(java.util.Date(luc))
    }

    fun them(ten: String, daChot: String, viec: List<String>,
             luc: Long = System.currentTimeMillis()): Boolean =
        themBan(BienBan(luc, ten, daChot, viec))

    fun themBan(b: BienBan): Boolean {
        val t = b.ten.trim()
        if (t.length < MIN_KY_TU) return false
        danhSach.add(b.copy(
            ten = t, daChot = b.daChot.trim(),
            viec = sach(b.viec), tomTat = sach(b.tomTat),
            nguoiDu = sach(b.nguoiDu), cauHoi = sach(b.cauHoi)))
        while (danhSach.size > TOI_DA) danhSach.removeAt(0)
        return true
    }

    fun xoa(chiSo: Int): Boolean {
        if (chiSo !in danhSach.indices) return false
        danhSach.removeAt(chiSo)
        return true
    }

    fun chen(chiSo: Int, b: BienBan) { danhSach.add(chiSo.coerceIn(0, danhSach.size), b) }

    fun luu(ctx: Context) {
        val m = JSONArray()
        for (b in danhSach) {
            m.put(JSONObject()
                .put("luc", b.luc).put("ten", b.ten).put("chot", b.daChot)
                .put("viec", JSONArray(b.viec)).put("tom_tat", JSONArray(b.tomTat))
                .put("nguoi_du", JSONArray(b.nguoiDu)).put("cau_hoi", JSONArray(b.cauHoi))
                .put("thoi_luong", b.thoiLuongPhut ?: JSONObject.NULL)
                .put("nguon", b.nguon))
        }
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString(KHOA, m.toString()).apply()
    }

    companion object {
        const val MIN_KY_TU = 3
        const val TOI_DA = 200
        const val NGUON_TAY = "tay"
        const val NGUON_MEETY = "meety"

        /**
         * Ten dat cho bien ban khuyet tieu de. Man hinh goi `tuMeety` nen
         * truyen ban da dich (`R.string.bb_khong_ten`); mac dinh nay chi
         * de test va cac duong goi khong co Context van chay duoc.
         */
        const val TEN_THAY_THE = "Cuộc họp không tên"
        private const val PREFS = "flowy_bien_ban"
        private const val KHOA = "danh_sach"

        private fun sach(ds: List<String>) = ds.map { it.trim() }.filter { it.isNotEmpty() }

        private fun mang(o: JSONObject?, khoa: String): List<String> {
            val v = o?.optJSONArray(khoa) ?: return emptyList()
            return (0 until v.length()).map { v.optString(it, "") }
        }

        /**
         * ============================================================
         * DANH DAU THE TREN TAB KE HOACH
         * ============================================================
         *
         * Hai thu nho luu rieng khoi ban ghi bien ban, vi chung la trang
         * thai CUA GIAO DIEN chu khong phai noi dung cuoc hop:
         *
         *   · `danhDauDong`  - nguoi dung da bam X tren the tom tat.
         *   · `danhDauVaoLich` - mot viec trong bien ban da duoc dua vao
         *     lich, de the khong con giuc nua.
         *
         * Khoa dung moc thoi gian cua bien ban, nen xoa bien ban di thi
         * cac dau nay cung tro thanh vo hai.
         */
        private const val PREFS_THE = "flowy_bien_ban_the"

        fun danhDauDong(ctx: Context, luc: Long) {
            ctx.getSharedPreferences(PREFS_THE, Context.MODE_PRIVATE)
                .edit().putBoolean("dong_$luc", true).apply()
        }

        fun daDong(ctx: Context, luc: Long): Boolean =
            ctx.getSharedPreferences(PREFS_THE, Context.MODE_PRIVATE)
                .getBoolean("dong_$luc", false)

        fun danhDauVaoLich(ctx: Context, luc: Long, viec: String) {
            val p = ctx.getSharedPreferences(PREFS_THE, Context.MODE_PRIVATE)
            val cu = p.getStringSet("lich_$luc", emptySet())?.toMutableSet() ?: mutableSetOf()
            cu.add(viec)
            p.edit().putStringSet("lich_$luc", cu).apply()
        }

        fun daVaoLich(ctx: Context, luc: Long, viec: String): Boolean =
            ctx.getSharedPreferences(PREFS_THE, Context.MODE_PRIVATE)
                .getStringSet("lich_$luc", emptySet())?.contains(viec) == true

        fun doc(ctx: Context): SoBienBan {
            val s = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getString(KHOA, null) ?: return SoBienBan()
            return tuJson(s)
        }

        fun tuJson(s: String): SoBienBan {
            val so = SoBienBan()
            try {
                val m = JSONArray(s)
                for (i in 0 until m.length()) {
                    val o = m.optJSONObject(i) ?: continue
                    so.themBan(BienBan(
                        luc = o.optLong("luc", System.currentTimeMillis()),
                        ten = o.optString("ten", ""),
                        daChot = o.optString("chot", ""),
                        viec = mang(o, "viec"), tomTat = mang(o, "tom_tat"),
                        nguoiDu = mang(o, "nguoi_du"), cauHoi = mang(o, "cau_hoi"),
                        thoiLuongPhut = if (o.isNull("thoi_luong") || !o.has("thoi_luong")) null else o.optInt("thoi_luong"),
                        nguon = o.optString("nguon", NGUON_TAY),
                    ))
                }
            } catch (_: Exception) {
                return SoBienBan()
            }
            return so
        }

        /**
         * Doc `StructuredMinutes` cua Meety (tep `<id>_minutes.json`).
         * Chi lay phan nguoi hop can: tieu de, ngay, thoi luong, nguoi du,
         * tl;dr, quyet dinh CON HIEU LUC, viec (kem nguoi nhan + han), cau
         * hoi mo. Bo qua evidence, quality report, chapter - thuoc ve giao
         * dien Meety, khong thuoc ve biên ban.
         *
         * Tra ve null neu tep khong phai bien ban Meety.
         */
        /**
         * ============================================================
         * NHAN DANG MOT TEP CO PHAI BIEN BAN MEETY KHONG (muc 8.2)
         * ============================================================
         *
         * Ban truoc chi kiem dung mot dieu: `meta.meeting_title` co rong
         * khong. Mot cong nhu vay sai ca hai chieu:
         *
         *   · NHAN NHAM. Bat cu tep JSON nao tinh co co `meta.meeting_title`
         *     deu duoc nuot, ke ca khi khong co mot quyet dinh, mot dau
         *     viec hay mot dong tom tat nao. Nguoi dung thay mot ban bien
         *     ban trong ron va khong hieu vi sao.
         *
         *   · TU CHOI NHAM. Mot bien ban day du nhung khuyet tieu de - dieu
         *     hoan toan binh thuong voi cuoc hop khong ten - bi vut di sach
         *     se, keo theo ca quyet dinh lan dau viec.
         *
         * Gio kiem CAU TRUC: phai co `meta`, VA phai co it nhat mot trong
         * ba khoi mang y nghia (`decisions`, `action_items`,
         * `executive_summary`). Ba khoi do la thu phan biet mot bien ban
         * DA PHAN TICH voi mot ban ghi tho - ban ghi tho co `segments` va
         * `speakers`, khong co khoi nao trong ba.
         *
         * Neu tep co `validation.schema_valid` va co la `false` thi tin
         * theo co do: chinh pipeline Meety noi ra rang no biet tep nay hong.
         *
         * Tieu de rong khong con la ly do tu choi - no duoc dat ten thay.
         */
        fun hopLeMeety(o: JSONObject): Boolean {
            val meta = o.optJSONObject("meta") ?: return false

            // Pipeline tu bao tep hong -> tin theo, khong doan lai.
            o.optJSONObject("validation")?.let {
                if (it.has("schema_valid") && !it.optBoolean("schema_valid", true)) return false
            }

            val coQuyetDinh = (o.optJSONArray("decisions")?.length() ?: 0) > 0
            val coViec = (o.optJSONArray("action_items")?.length() ?: 0) > 0
            val coTomTat = o.optJSONObject("executive_summary") != null
            if (!coQuyetDinh && !coViec && !coTomTat) return false

            // `meta.attendees` la cua bien ban; `speakers` o goc la cua ban
            // ghi tho. Kiem dung cai dau, dung lay cai sau ra thay the.
            if (meta.has("attendees") && meta.optJSONArray("attendees") == null) return false
            return true
        }

        fun tuMeety(json: String, tenThayThe: String = TEN_THAY_THE): BienBan? = try {
            val o = JSONObject(json)
            if (!hopLeMeety(o)) throw IllegalArgumentException("khong phai bien ban Meety")
            val meta = o.getJSONObject("meta")
            val ten = meta.optString("meeting_title", "").trim()
            val luc = meta.optString("date", "").let { d ->
                runCatching {
                    java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US).parse(d)!!.time
                }.getOrDefault(System.currentTimeMillis())
            }
            val nguoi = (0 until (meta.optJSONArray("attendees")?.length() ?: 0)).mapNotNull {
                meta.getJSONArray("attendees").optJSONObject(it)?.optString("display_name")
            }
            val quyetDinh = mutableListOf<String>()
            o.optJSONArray("decisions")?.let { a ->
                for (i in 0 until a.length()) {
                    val d = a.optJSONObject(i) ?: continue
                    // Quyet dinh da bi thay the thi khong con la "da chot".
                    if (!d.isNull("superseded_by") && d.optString("superseded_by").isNotBlank()) continue
                    if (d.optString("status") in setOf("rejected", "superseded", "reverted")) continue
                    d.optString("statement").takeIf { it.isNotBlank() }?.let(quyetDinh::add)
                }
            }
            val viec = mutableListOf<String>()
            o.optJSONArray("action_items")?.let { a ->
                for (i in 0 until a.length()) {
                    val v = a.optJSONObject(i) ?: continue
                    val task = v.optString("task").takeIf { it.isNotBlank() } ?: continue
                    val ai = v.optString("assignee").takeIf { !v.isNull("assignee") && it.isNotBlank() }
                    val han = v.optString("due_date").takeIf { !v.isNull("due_date") && it.isNotBlank() }
                        ?: v.optString("due_raw").takeIf { !v.isNull("due_raw") && it.isNotBlank() }
                    viec += buildString {
                        if (ai != null) append("$ai: ")
                        append(task)
                        if (han != null) append(" (hạn $han)")
                    }
                }
            }
            val cauHoi = (0 until (o.optJSONArray("open_questions")?.length() ?: 0)).mapNotNull {
                o.getJSONArray("open_questions").optJSONObject(it)?.optString("question")
            }
            BienBan(
                // Tieu de rong -> dat ten theo ngay, thay vi vut ca tep.
                luc = luc, ten = ten.ifEmpty {
                    "$tenThayThe · " + java.text.SimpleDateFormat(
                        "dd/MM/yyyy", java.util.Locale.US).format(java.util.Date(luc))
                },
                daChot = quyetDinh.joinToString("\n"),
                viec = viec,
                tomTat = mang(o.optJSONObject("executive_summary"), "tldr"),
                nguoiDu = nguoi, cauHoi = cauHoi,
                thoiLuongPhut = meta.optInt("duration_minutes", 0).takeIf { it > 0 },
                nguon = NGUON_MEETY,
            )
        } catch (_: Exception) {
            null
        }

        /**
         * Noi dung tai lieu Word. CUNG cau truc cho hai ho so - khac nhau o
         * cach TRINH BAY (xem `DocxViet`): ban De doc to nen khoi "Viec cua
         * ban" va "Tom tat", tach cau dai, gian dong 1.5.
         *
         * Thu tu cho nguoi kho doc: dieu can LAM truoc (tom tat, viec), roi
         * moi den dieu da noi (quyet dinh), cuoi cung la cau hoi con mo.
         */
        fun khoiDocx(b: BienBan): List<DocxViet.Khoi> {
            val k = mutableListOf<DocxViet.Khoi>()
            k += DocxViet.Khoi.TieuDe(b.ten)
            val ngay = java.text.SimpleDateFormat("dd/MM/yyyy", java.util.Locale.US).format(java.util.Date(b.luc))
            k += DocxViet.Khoi.ChuNho(listOfNotNull(
                "Ngày $ngay",
                b.thoiLuongPhut?.let { "$it phút" },
                if (b.nguoiDu.isNotEmpty()) "Người dự: ${b.nguoiDu.joinToString(", ")}" else null,
            ).joinToString("  ·  "))
            if (b.tomTat.isNotEmpty()) k += DocxViet.Khoi.NoiBat("Tóm tắt", b.tomTat)
            if (b.viec.isNotEmpty()) k += DocxViet.Khoi.NoiBat("Việc cần làm", b.viec)
            val chot = b.daChot.split("\n").map { it.trim() }.filter { it.isNotEmpty() }
            if (chot.isNotEmpty()) {
                k += DocxViet.Khoi.Muc("Đã chốt")
                chot.forEach { k += DocxViet.Khoi.GachDau(it) }
            }
            if (b.cauHoi.isNotEmpty()) {
                k += DocxViet.Khoi.Muc("Câu hỏi còn mở")
                b.cauHoi.forEach { k += DocxViet.Khoi.GachDau(it) }
            }
            k += DocxViet.Khoi.ChuNho(if (b.nguon == NGUON_MEETY) "Tạo từ Meety qua FlowyX" else "Ghi tay trên FlowyX")
            return k
        }
    }
}
