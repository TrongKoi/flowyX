package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Bo doc .ics: doc dung, va khong lam mat su kien mot cach am tham. */
class DocIcsTest {

    private fun ics(than: String) = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n$than\r\nEND:VCALENDAR\r\n"

    @Test fun doc_su_kien_co_ban() {
        val k = DocIcs.doc(ics("""
            BEGIN:VEVENT
            SUMMARY:Họp nhóm ADC
            DTSTART:20260921T090000
            DTEND:20260921T103000
            LOCATION:Phòng B2
            END:VEVENT
        """.trimIndent()))
        assertEquals(1, k.suKien.size)
        val s = k.suKien[0]
        assertEquals("Họp nhóm ADC", s.ten)
        assertEquals(Lich.tuNgayThang(2026, 9, 21), s.ngay)
        assertEquals(9 * 60, s.batDau)
        assertEquals(90, s.thoiLuong)
        assertEquals("Phòng B2", s.oDau)
    }

    @Test fun dong_gap_duoc_noi_lai() {
        // RFC 5545: dong dai bi ngat, dong sau bat dau bang mot dau cach.
        val k = DocIcs.doc(ics(
            "BEGIN:VEVENT\r\nSUMMARY:Buổi ôn tập rất dài cho kỳ thi\r\n  cuối kỳ\r\n" +
            "DTSTART:20260921T140000\r\nDTEND:20260921T150000\r\nEND:VEVENT"))
        assertEquals("Buổi ôn tập rất dài cho kỳ thi cuối kỳ", k.suKien[0].ten)
    }

    @Test fun duration_thay_cho_dtend() {
        val k = DocIcs.doc(ics("""
            BEGIN:VEVENT
            SUMMARY:Chạy bộ
            DTSTART:20260921T060000
            DURATION:PT45M
            END:VEVENT
        """.trimIndent()))
        assertEquals(45, k.suKien[0].thoiLuong)
    }

    @Test fun su_kien_ca_ngay() {
        val k = DocIcs.doc(ics("""
            BEGIN:VEVENT
            SUMMARY:Nghỉ lễ
            DTSTART;VALUE=DATE:20260902
            END:VEVENT
        """.trimIndent()))
        assertTrue(k.suKien[0].caNgay)
        assertEquals(0, k.suKien[0].batDau)
        assertEquals(1440, k.suKien[0].thoiLuong)
    }

    @Test fun rrule_hang_ngay_va_theo_thu() {
        val k = DocIcs.doc(ics("""
            BEGIN:VEVENT
            SUMMARY:Uống thuốc
            DTSTART:20260921T080000
            DURATION:PT5M
            RRULE:FREQ=DAILY
            END:VEVENT
            BEGIN:VEVENT
            SUMMARY:Lớp tiếng Anh
            DTSTART:20260921T190000
            DTEND:20260921T203000
            RRULE:FREQ=WEEKLY;BYDAY=MO,TH
            END:VEVENT
        """.trimIndent()))
        assertEquals(LapLai.HANG_NGAY, k.suKien[0].lapLai)
        assertEquals(LapLai.THEO_THU, k.suKien[1].lapLai)
        assertEquals(setOf(0, 3), k.suKien[1].thuLap)
    }

    @Test fun thieu_ten_hoac_thieu_ngay_thi_DEM_chu_khong_bien_mat() {
        val k = DocIcs.doc(ics("""
            BEGIN:VEVENT
            DTSTART:20260921T090000
            END:VEVENT
            BEGIN:VEVENT
            SUMMARY:Không có giờ
            END:VEVENT
        """.trimIndent()))
        assertEquals(0, k.suKien.size)
        assertEquals("phai bao cho nguoi dung biet co 2 muc bi bo", 2, k.boQua)
    }

    @Test fun ky_tu_thoat_duoc_go_bo() {
        val k = DocIcs.doc(ics(
            "BEGIN:VEVENT\r\nSUMMARY:Họp\\, rồi ăn trưa\r\nDTSTART:20260921T090000\r\nEND:VEVENT"))
        assertEquals("Họp, rồi ăn trưa", k.suKien[0].ten)
    }

    @Test fun tep_rac_khong_lam_sap() {
        val k = DocIcs.doc("day khong phai ics")
        assertEquals(0, k.suKien.size)
        assertNotNull(k)
    }

    @Test fun tran_400_su_kien() {
        val than = (1..450).joinToString("\r\n") {
            "BEGIN:VEVENT\r\nSUMMARY:Việc $it\r\nDTSTART:20260921T090000\r\nDURATION:PT30M\r\nEND:VEVENT"
        }
        val k = DocIcs.doc(ics(than))
        assertEquals(DocIcs.TOI_DA, k.suKien.size)
        assertEquals(50, k.boQua)
    }

    @Test fun tim_trung_gio() {
        val ngay = Lich.tuNgayThang(2026, 9, 21)
        val daCo = listOf(KeHoach("x", "Ôn bài", ngay = ngay, batDau = 19 * 60, thoiLuong = 60))
        val moi = listOf(
            DocIcs.SuKien("Lớp tiếng Anh", ngay, 19 * 60 + 30, 60),   // trung
            DocIcs.SuKien("Chạy bộ", ngay, 6 * 60, 45),               // khong trung
            DocIcs.SuKien("Sát giờ", ngay, 20 * 60, 30),              // ke sat, khong trung
        )
        val t = DocIcs.timTrung(moi, daCo)
        assertEquals(1, t.size)
        assertEquals("Lớp tiếng Anh", t[0].moi.ten)
    }

    @Test fun su_kien_ca_ngay_khong_bao_trung() {
        val ngay = Lich.tuNgayThang(2026, 9, 21)
        val daCo = listOf(KeHoach("x", "Ôn bài", ngay = ngay, batDau = 19 * 60, thoiLuong = 60))
        val moi = listOf(DocIcs.SuKien("Nghỉ lễ", ngay, 0, 1440, caNgay = true))
        assertTrue(DocIcs.timTrung(moi, daCo).isEmpty())
    }

    @Test fun doi_sang_ke_hoach_giu_du_thong_tin() {
        val ngay = Lich.tuNgayThang(2026, 9, 21)
        val kh = DocIcs.sangKeHoach(
            DocIcs.SuKien("Lớp tiếng Anh", ngay, 19 * 60, 90, LapLai.THEO_THU, setOf(0, 3), "Phòng 305"))
        assertEquals("Lớp tiếng Anh", kh.ten)
        assertEquals(19 * 60, kh.batDau)
        assertEquals(90, kh.thoiLuong)
        assertEquals(LapLai.THEO_THU, kh.lapLai)
        assertEquals(setOf(0, 3), kh.thuLap)
        assertEquals("Phòng 305", kh.oDau)
    }
}
