package vn.adc2026.wayfinding

import java.util.Locale

/**
 * DOC GIO - bien chu nguoi dung go thanh "phut tinh tu nua dem".
 *
 * --------------------------------------------------------------------
 * VI SAO KHONG CHI NHAN "HH:MM"
 * --------------------------------------------------------------------
 *
 * Bug tu buoi test tren Galaxy Tab S7 FE: o gio dung
 * `InputType.TYPE_CLASS_DATETIME`, va ban phim Samsung hien ra CHI CO
 * SO - khong co dau hai cham. Nguoi dung go "1400" thi bi bao sai.
 *
 * O gio gio mo `TimePickerDialog` (xem MainActivity), nhung van giu o go
 * tay cho nguoi quen go. Moi cach ghi pho bien deu phai nhan:
 *
 *     "14:00"  "14.00"  "14h"  "14h30"  "14 30"   -> co dau phan cach
 *     "1400"   "930"    "9"    "14"               -> chi co so
 *
 * Bat nguoi dang vo y dinh nho cu phap la them mot viec nua phai lam -
 * cung ly do `run_flowy.py` gan cau noi theo thu tu o thieu.
 *
 * Lop nay KHONG phu thuoc Android, de test tren JVM thuong.
 */
object DocGio {

    /** Chu -> phut trong ngay. Sai hoac ngoai 00:00..23:59 thi null. */
    fun doc(s: String?): Double? {
        if (s == null) return null
        val t = s.trim().lowercase(Locale.ROOT)
        if (t.isEmpty()) return null

        // Co dau phan cach: ":" "." "h" "g" (gio) hoac khoang trang.
        val coPhanCach = Regex("""^(\d{1,2})\s*[:.hg ]\s*(\d{0,2})\s*(p|ph|phut|phút)?$""")
        coPhanCach.matchEntire(t)?.let { m ->
            val g = m.groupValues[1].toInt()
            val p = m.groupValues[2].ifEmpty { "0" }.toInt()
            // "14:5" de hieu nham thanh 14:05 hay 14:50 - khong doan.
            if (m.groupValues[2].length == 1) return null
            return hopLe(g, p)
        }

        // Chi co so.
        if (!t.all { it.isDigit() }) return null
        return when (t.length) {
            1, 2 -> hopLe(t.toInt(), 0)                       // "9" "14"
            3 -> hopLe(t.substring(0, 1).toInt(), t.substring(1).toInt())  // "930"
            4 -> hopLe(t.substring(0, 2).toInt(), t.substring(2).toInt())  // "1400"
            else -> null
        }
    }

    /** Phut trong ngay -> "HH:MM", de hien lai trong o sau khi chon. */
    fun hien(phut: Double): String = String.format(
        Locale.US, "%02d:%02d", (phut / 60).toInt(), (phut % 60).toInt())

    private fun hopLe(g: Int, p: Int): Double? =
        if (g in 0..23 && p in 0..59) g * 60.0 + p else null
}
