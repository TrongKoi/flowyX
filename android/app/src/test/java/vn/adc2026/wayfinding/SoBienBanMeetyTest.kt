package vn.adc2026.wayfinding

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * ====================================================================
 * CONG NHAN DANG BIEN BAN MEETY (muc 8.2)
 * ====================================================================
 *
 * Bai kiem o day di theo dung hai kieu sai ma cong cu - chi nhin
 * `meta.meeting_title` - mac phai: nhan nham tep rac, va tu choi nham
 * bien ban that khuyet tieu de.
 *
 * `org.json` that nam tren test classpath (xem `app/build.gradle.kts`),
 * nen day la JSON thuc su chu khong phai vo rong cua android.jar.
 */
class SoBienBanMeetyTest {

    private fun bienBanDu() = """
        {
          "meta": {
            "meeting_title": "Chốt giao diện v5",
            "date": "2026-09-18",
            "duration_minutes": 45,
            "attendees": [{"display_name": "Khôi"}, {"display_name": "Huy"}]
          },
          "executive_summary": {"tldr": ["Chốt bảng màu đêm"]},
          "decisions": [{"statement": "Dùng tím oải hương cho nút bấm", "status": "agreed"}],
          "action_items": [{"task": "Đo lại tương phản", "assignee": "Khôi", "due_date": "2026-09-19"}],
          "open_questions": [{"question": "Logo trên nền đêm xử lý sao?"}]
        }
    """.trimIndent()

    @Test
    fun bienBanDayDu_thiNhan() {
        val b = SoBienBan.tuMeety(bienBanDu())
        assertNotNull(b)
        assertEquals("Chốt giao diện v5", b!!.ten)
        assertEquals(listOf("Khôi", "Huy"), b.nguoiDu)
        assertEquals(45, b.thoiLuongPhut)
        assertEquals(1, b.viec.size)
    }

    // ----- Chieu sai thu nhat: NHAN NHAM -----

    /**
     * Day chinh la tep lam lo cong cu: co `meta.meeting_title` day du,
     * nhung khong mot khoi noi dung nao. Ban truoc nhan no va dung len
     * mot bien ban rong ron.
     */
    @Test
    fun coTieuDeNhungRongNoiDung_thiTuChoi() {
        val rac = """{"meta": {"meeting_title": "Họp gì đó", "date": "2026-09-18"}}"""
        assertFalse(SoBienBan.hopLeMeety(JSONObject(rac)))
        assertNull(SoBienBan.tuMeety(rac))
    }

    /** Ban ghi THO: co `speakers` va `segments`, khong co khoi nao cua bien ban. */
    @Test
    fun banGhiTho_thiTuChoi() {
        val tho = """
            {
              "speakers": ["A", "B"],
              "segments": [{"speaker": "A", "text": "chào mọi người"}],
              "meta": {"meeting_title": "Bản ghi thô"}
            }
        """.trimIndent()
        assertFalse(SoBienBan.hopLeMeety(JSONObject(tho)))
    }

    /** Pipeline tu cam co bao tep hong -> tin theo co do. */
    @Test
    fun pipelineBaoSchemaKhongHopLe_thiTuChoi() {
        val o = JSONObject(bienBanDu()).put("validation", JSONObject().put("schema_valid", false))
        assertFalse(SoBienBan.hopLeMeety(o))
    }

    @Test
    fun schemaValidLaTrue_thiVanNhan() {
        val o = JSONObject(bienBanDu()).put("validation", JSONObject().put("schema_valid", true))
        assertTrue(SoBienBan.hopLeMeety(o))
    }

    // ----- Chieu sai thu hai: TU CHOI NHAM -----

    /**
     * Cuoc hop khong dat ten la chuyen binh thuong. Ban truoc vut ca tep,
     * mat luon quyet dinh lan dau viec. Gio dat ten thay theo ngay.
     */
    @Test
    fun khuyetTieuDe_thiVanNhanVaDatTenTheoNgay() {
        val o = JSONObject(bienBanDu())
        o.getJSONObject("meta").put("meeting_title", "")
        val b = SoBienBan.tuMeety(o.toString(), "Cuộc họp không tên")
        assertNotNull(b)
        assertEquals("Cuộc họp không tên · 18/09/2026", b!!.ten)
        assertEquals(1, b.viec.size)   // noi dung khong mat
    }

    /** Chi co mot trong ba khoi cung du - khong bat phai co ca ba. */
    @Test
    fun chiCoMotKhoiNoiDung_thiVanNhan() {
        val chiViec = """
            {
              "meta": {"meeting_title": "Đứng nhanh", "date": "2026-09-18"},
              "action_items": [{"task": "Gửi bản nháp"}]
            }
        """.trimIndent()
        assertTrue(SoBienBan.hopLeMeety(JSONObject(chiViec)))

        val chiTomTat = """
            {
              "meta": {"meeting_title": "Đứng nhanh"},
              "executive_summary": {"tldr": ["Không có gì chặn"]}
            }
        """.trimIndent()
        assertTrue(SoBienBan.hopLeMeety(JSONObject(chiTomTat)))
    }

    @Test
    fun khongCoMeta_thiTuChoi() {
        val khongMeta = """{"decisions": [{"statement": "x"}]}"""
        assertFalse(SoBienBan.hopLeMeety(JSONObject(khongMeta)))
    }

    @Test
    fun jsonHong_thiTraVeNull_khongNemLoi() {
        assertNull(SoBienBan.tuMeety("{ khong phai json"))
        assertNull(SoBienBan.tuMeety(""))
    }
}
