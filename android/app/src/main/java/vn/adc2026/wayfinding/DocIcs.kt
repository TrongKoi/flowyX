package vn.adc2026.wayfinding

import java.util.Calendar
import java.util.TimeZone

/**
 * ====================================================================
 * DOC TEP .ics (iCalendar, RFC 5545) - tu viet, khong thu vien
 * ====================================================================
 *
 * Google Calendar, Apple Calendar, Outlook deu xuat duoc .ics, va ca ba
 * deu cho "tai lich" bang mot duong link .ics. Doc duoc dinh dang nay la
 * doc duoc ca ba, khong can API, khong can dang nhap, khong gui du lieu
 * cua nguoi dung di dau.
 *
 * ----- Doc den dau -----
 *
 * Lay: VEVENT, SUMMARY, DTSTART, DTEND / DURATION, RRULE (FREQ=DAILY va
 * FREQ=WEEKLY + BYDAY), LOCATION.
 *
 * Bo qua: VTODO, VALARM, VTIMEZONE day du, RRULE phuc tap (BYMONTHDAY,
 * INTERVAL > 1, COUNT/UNTIL), sua le tung lan (RECURRENCE-ID), dinh kem.
 * Cac phan bo qua duoc DEM lai va bao cho nguoi dung - khong am tham lam
 * mat su kien.
 *
 * ----- Vi sao khong dung thu vien -----
 *
 * ical4j keo theo vai MB va mot cay phu thuoc (slf4j, commons). App nay
 * khong dung androidx, muc tieu la APK duoi 1 MB. Phan .ics ma nguoi dung
 * that su can chi la vai truong tren.
 *
 * ----- Mui gio -----
 *
 * DTSTART co ba dang:
 *   20260921T090000Z     - UTC, doi ve gio may
 *   20260921T090000      - gio dia phuong, giu nguyen
 *   20260921             - ca ngay, coi nhu 00:00 va danh dau caNgay
 * TZID=... duoc doc qua `TimeZone.getTimeZone`, khong biet thi coi nhu
 * gio dia phuong (va dem vao so "khong chac").
 */
object DocIcs {

    data class SuKien(
        val ten: String,
        /** So ngay tu 1970 (cung he voi `Lich`). */
        val ngay: Long,
        /** Phut tu 00:00. */
        val batDau: Int,
        val thoiLuong: Int,
        val lapLai: LapLai = LapLai.KHONG,
        val thuLap: Set<Int> = emptySet(),
        val oDau: String? = null,
        val caNgay: Boolean = false,
    )

    data class KetQua(
        val suKien: List<SuKien>,
        /** So VEVENT doc duoc nhung bo qua (thieu ngay, RRULE khong ho tro...). */
        val boQua: Int,
        val loi: String? = null,
    )

    /** Tran an toan: tep .ics cong ty co the co hang chuc nghin su kien. */
    const val TOI_DA = 400

    fun doc(chu: String): KetQua {
        return try {
            val dong = noiDongGap(chu)
            val ra = ArrayList<SuKien>()
            var boQua = 0
            var trong = false
            var ten: String? = null
            var loc: String? = null
            var dt: Moc? = null
            var het: Moc? = null
            var keoDai: Int? = null
            var lap = LapLai.KHONG
            var thu = emptySet<Int>()

            for (d in dong) {
                val tren = d.uppercase()
                when {
                    tren.startsWith("BEGIN:VEVENT") -> {
                        trong = true; ten = null; loc = null; dt = null; het = null
                        keoDai = null; lap = LapLai.KHONG; thu = emptySet()
                    }
                    !trong -> Unit
                    tren.startsWith("END:VEVENT") -> {
                        trong = false
                        val b = dt
                        if (b == null || ten.isNullOrBlank()) { boQua++; continue }
                        val tl = when {
                            keoDai != null -> keoDai!!
                            het != null -> ((het!!.ngay - b.ngay) * 1440 + (het!!.phut - b.phut)).toInt()
                            b.caNgay -> 1440
                            else -> 60
                        }.coerceIn(5, 24 * 60)
                        if (ra.size >= TOI_DA) { boQua++; continue }
                        ra += SuKien(ten!!.trim(), b.ngay, b.phut, tl, lap, thu, loc?.trim()?.ifBlank { null }, b.caNgay)
                    }
                    tren.startsWith("SUMMARY") -> ten = boDau(d)
                    tren.startsWith("LOCATION") -> loc = boDau(d)
                    tren.startsWith("DTSTART") -> dt = docMoc(d)
                    tren.startsWith("DTEND") -> het = docMoc(d)
                    tren.startsWith("DURATION") -> keoDai = docKeoDai(boDau(d))
                    tren.startsWith("RRULE") -> {
                        val r = boDau(d).uppercase()
                        when {
                            "FREQ=DAILY" in r && "INTERVAL=" !in r -> lap = LapLai.HANG_NGAY
                            "FREQ=WEEKLY" in r && "INTERVAL=" !in r -> {
                                val by = Regex("BYDAY=([A-Z,]+)").find(r)?.groupValues?.get(1)
                                if (by != null) {
                                    thu = by.split(",").mapNotNull { THU_ICS[it.takeLast(2)] }.toSet()
                                    lap = if (thu.isEmpty()) LapLai.HANG_TUAN else LapLai.THEO_THU
                                } else lap = LapLai.HANG_TUAN
                            }
                            else -> Unit          // RRULE phuc tap: lay lan dau tien thoi
                        }
                    }
                }
            }
            KetQua(ra, boQua)
        } catch (e: Exception) {
            KetQua(emptyList(), 0, e.javaClass.simpleName)
        }
    }

    // ---------------------------------------------------------------

    private data class Moc(val ngay: Long, val phut: Int, val caNgay: Boolean)

    /**
     * Dong gap (folding): RFC 5545 cho phep ngat dong dai roi noi tiep bang
     * mot dau cach hoac tab o dau dong sau. Khong noi lai thi ten su kien
     * dai se bi cat doi.
     */
    private fun noiDongGap(chu: String): List<String> {
        val ra = ArrayList<String>()
        for (d in chu.replace("\r\n", "\n").replace('\r', '\n').split('\n')) {
            if (d.isEmpty()) continue
            if ((d[0] == ' ' || d[0] == '\t') && ra.isNotEmpty()) {
                ra[ra.size - 1] = ra[ra.size - 1] + d.substring(1)
            } else ra += d
        }
        return ra
    }

    /** Phan sau dau hai cham dau tien. Ky tu thoat cua iCalendar duoc go bo. */
    private fun boDau(d: String): String {
        val i = d.indexOf(':')
        val v = if (i < 0) "" else d.substring(i + 1)
        return v.replace("\\n", "\n").replace("\\,", ",")
            .replace(THOAT_CHAM_PHAY, ";").replace("\\\\", "\\")
    }

    private fun docMoc(d: String): Moc? {
        val gt = boDau(d).trim()
        val thamSo = d.substringBefore(':').uppercase()
        val caNgay = "VALUE=DATE" in thamSo || gt.length == 8
        val tz = Regex("TZID=([^;:]+)").find(thamSo)?.groupValues?.get(1)

        return try {
            val nam = gt.substring(0, 4).toInt()
            val thang = gt.substring(4, 6).toInt()
            val ngayThang = gt.substring(6, 8).toInt()
            if (caNgay) return Moc(Lich.tuNgayThang(nam, thang, ngayThang), 0, true)

            val gio = gt.substring(9, 11).toInt()
            val phut = gt.substring(11, 13).toInt()
            if (gt.endsWith("Z") || tz != null) {
                // Doi ve gio cua may: nguoi dung nhin lich theo gio ho dang song.
                val c = Calendar.getInstance(
                    if (gt.endsWith("Z")) TimeZone.getTimeZone("UTC") else TimeZone.getTimeZone(tz))
                c.clear()
                c.set(nam, thang - 1, ngayThang, gio, phut)
                val may = Calendar.getInstance()
                may.timeInMillis = c.timeInMillis
                Moc(
                    Lich.tuNgayThang(may.get(Calendar.YEAR), may.get(Calendar.MONTH) + 1,
                        may.get(Calendar.DAY_OF_MONTH)),
                    may.get(Calendar.HOUR_OF_DAY) * 60 + may.get(Calendar.MINUTE), false)
            } else {
                Moc(Lich.tuNgayThang(nam, thang, ngayThang), gio * 60 + phut, false)
            }
        } catch (_: Exception) {
            null
        }
    }

    /** DURATION dang PT1H30M / PT45M / P1D. Tra ve so phut. */
    private fun docKeoDai(s: String): Int? {
        val m = Regex("P(?:(\\d+)D)?T?(?:(\\d+)H)?(?:(\\d+)M)?").find(s.uppercase()) ?: return null
        val (d, h, p) = m.destructured
        val tong = (d.toIntOrNull() ?: 0) * 1440 + (h.toIntOrNull() ?: 0) * 60 + (p.toIntOrNull() ?: 0)
        return if (tong <= 0) null else tong
    }

    /** Chuoi hai ky tu: dau cheo nguoc + cham phay. Viet bang ma de tranh
     *  lan voi ky tu thoat cua Kotlin. */
    private val THOAT_CHAM_PHAY = "\u005C;"

    private val THU_ICS = mapOf(
        "MO" to 0, "TU" to 1, "WE" to 2, "TH" to 3, "FR" to 4, "SA" to 5, "SU" to 6)

    // ---------------------------------------------------------------
    // Trung gio
    // ---------------------------------------------------------------

    data class Trung(val moi: SuKien, val cu: KeHoach)

    /**
     * Tim su kien moi trung gio voi ke hoach da co trong MOT ngay cu the.
     *
     * Hai khoang trung nhau khi bat dau cua ben nay nam truoc ket thuc cua
     * ben kia va nguoc lai. Khong xet su kien ca ngay: no phu ca ngay nen
     * se "trung" voi tat ca, bao ra chi lam nhieu.
     */
    fun timTrung(moi: List<SuKien>, daCo: List<KeHoach>): List<Trung> {
        val ra = ArrayList<Trung>()
        for (s in moi) {
            if (s.caNgay) continue
            val ketThuc = s.batDau + s.thoiLuong
            for (k in daCo) {
                if (!Lich.coTrongNgay(k, s.ngay)) continue
                if (s.batDau < k.ketThuc && k.batDau < ketThuc) ra += Trung(s, k)
            }
        }
        return ra
    }

    /** Doi mot su kien .ics thanh ke hoach cua Flowy. */
    fun sangKeHoach(s: SuKien): KeHoach = KeHoach(
        id = SoLich.moiId(),
        ten = s.ten.take(120),
        emoji = if (s.caNgay) "📅" else "📥",
        ngay = s.ngay,
        batDau = s.batDau.coerceIn(0, 1439),
        thoiLuong = s.thoiLuong,
        lapLai = s.lapLai,
        thuLap = s.thuLap,
        oDau = s.oDau,
        nhacTruoc = if (s.caNgay) listOf(0) else listOf(15, 0),
    )
}
