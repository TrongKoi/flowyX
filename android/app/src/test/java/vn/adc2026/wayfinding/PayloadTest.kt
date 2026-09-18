package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Kiem hop dong JSON, phia dien thoai.
 *
 * Phia kia cua hop dong nam o `adc_wayfinding/tests/loi_chung/
 * test_hop_dong.py`. Hai file cung khoa MOT bang ten truong; doi mot
 * ben ma quen ben kia thi cau noi im lang hong.
 *
 * Chay duoc bang unit test JVM thuong, khong can may that - `Payload`
 * co y khong dung `org.json` chinh vi vay.
 */
class PayloadTest {

    // ============================================================
    // Chieu len: dien thoai -> laptop
    // ============================================================

    @Test
    fun goiTinToiThieuCoDuBaTruongBatBuoc() {
        val s = Payload.buildUpdate(tSeconds = 1234.5, trenManHinh = true)
        assertTrue(s, s.contains("\"t\":1234.5"))
        assertTrue(s, s.contains("\"tren_man_hinh\":true"))
        assertTrue(s, s.contains("\"cham_nhan_vat\":false"))
    }

    @Test
    fun truongDeTrongThiKhongCoMatTrongGoiTin() {
        // Gui `"voice":null` cung chay, nhung goi tin dai them ma khong
        // them thong tin gi - va no gui 2 lan moi giay.
        val s = Payload.buildUpdate(tSeconds = 0.0, trenManHinh = true)
        assertFalse(s, s.contains("voice"))
        assertFalse(s, s.contains("lenh"))
        assertFalse(s, s.contains("battery"))
        assertFalse(s, s.contains("lich_su"))
    }

    @Test
    fun goiTinDayDuCoMoiTruong() {
        val s = Payload.buildUpdate(
            tSeconds = 10.0,
            trenManHinh = false,
            chamNhanVat = true,
            voice = "sau bữa tối",
            lenh = Payload.LENH_BAT_DAU,
            noiDung = "viết báo cáo",
            battery = 55.0,
            thermal = 31.5,
            lichSu = "{\"viết báo cáo\":[{\"that\":35}]}",
        )
        assertTrue(s, s.contains("\"cham_nhan_vat\":true"))
        assertTrue(s, s.contains("\"voice\":\"sau bữa tối\""))
        assertTrue(s, s.contains("\"lenh\":\"bat_dau\""))
        assertTrue(s, s.contains("\"noi_dung\":\"viết báo cáo\""))
        assertTrue(s, s.contains("\"lich_su\":{"))
    }

    @Test
    fun dauTiengVietDiQua_NGUYEN_VEN() {
        // Ten cong viec la chu cua nguoi dung. Mat dau o day la laptop
        // ghi so vao mot muc KHAC, va lich su thoi luong tach lam doi ma
        // khong ai thay.
        val s = Payload.buildUpdate(tSeconds = 0.0, trenManHinh = true,
            noiDung = "viết báo cáo cuối kỳ")
        assertTrue(s, s.contains("viết báo cáo cuối kỳ"))
    }

    @Test
    fun dauNhayTrongTenViecDuocThoat() {
        // Nguoi dung go dau nhay la chuyen binh thuong. Khong thoat thi
        // goi tin thanh JSON hong va ca phien dung lai.
        val s = Payload.buildUpdate(tSeconds = 0.0, trenManHinh = true,
            noiDung = "viết bài \"Mở đầu\"")
        assertTrue(s, s.contains("\\\"Mở đầu\\\""))
    }

    @Test
    fun soThucLuonDungDauCHAM() {
        // String.format theo Locale mac dinh sinh dau PHAY o may cai
        // tieng Viet, va goi tin thanh JSON hong. Loi nay chi lo ra tren
        // may that nen rat de bo sot.
        val cu = java.util.Locale.getDefault()
        try {
            java.util.Locale.setDefault(java.util.Locale("vi", "VN"))
            val s = Payload.buildUpdate(tSeconds = 1234.5, trenManHinh = true)
            assertTrue(s, s.contains("1234.5"))
            assertFalse(s, s.contains("1234,5"))
        } finally {
            java.util.Locale.setDefault(cu)
        }
    }

    @Test
    fun soVoNghiaThanhKhongChuKhongLamHongGoiTin() {
        val s = Payload.buildUpdate(tSeconds = Double.NaN, trenManHinh = true)
        assertTrue(s, s.contains("\"t\":0"))
    }

    // ============================================================
    // Chieu ve: laptop -> dien thoai
    // ============================================================

    @Test
    fun docDuocMoiTruongCuaCauTraLoi() {
        val tra = Payload.parseReply(
            """{"say":"Xong việc rồi.","haptic":"xong_buoc","am":"tach",
               "ban":"tu_hao","tu_the":2,"hoi":"Bạn định làm gì?",
               "listen":true,"con_lai_giay":90.5,"tong_giay":1800.0,
               "nhip_ms":2000,"xong_phien":true,"ten_viec":"viết báo cáo"}"""
        )
        assertEquals("Xong việc rồi.", tra.say)
        assertEquals("xong_buoc", tra.haptic)
        assertEquals("tach", tra.am)
        assertEquals("tu_hao", tra.ban)
        assertEquals(2, tra.tuThe)
        assertEquals("Bạn định làm gì?", tra.hoi)
        assertTrue(tra.listen)
        assertEquals(90.5, tra.conLaiGiay!!, 1e-6)
        assertEquals(1800.0, tra.tongGiay!!, 1e-6)
        assertEquals(2000, tra.nhipMs)
        assertTrue(tra.xongPhien)
        assertEquals("viết báo cáo", tra.tenViec)
    }

    @Test
    fun goiTinRongChoMacDinhAnToan() {
        // Mot goi tin hong khong duoc phep dung ca phien lam viec cua
        // nguoi dung.
        val tra = Payload.parseReply("{}")
        assertNull(tra.say)
        assertNull(tra.hoi)
        assertFalse(tra.listen)
        assertFalse(tra.xongPhien)
        assertEquals(0, tra.tuThe)
        assertEquals(Payload.NHIP_MAC_DINH_MS, tra.nhipMs)
    }

    @Test
    fun truongNullDocRaNull() {
        val tra = Payload.parseReply(
            """{"say":null,"con_lai_giay":null,"ten_viec":null}""")
        assertNull(tra.say)
        assertNull(tra.conLaiGiay)
        assertNull(tra.tenViec)
    }

    @Test
    fun dauTiengVietTrongCauTraLoiDocRaDung() {
        val tra = Payload.parseReply(
            """{"say":"Bạn đang làm dở viết báo cáo. Còn 1 bước."}""")
        assertEquals("Bạn đang làm dở viết báo cáo. Còn 1 bước.", tra.say)
    }

    @Test
    fun docDuocChuoiCoKyTuThoat() {
        val tra = Payload.parseReply("""{"say":"viết bài \"Mở đầu\""}""")
        assertEquals("viết bài \"Mở đầu\"", tra.say)
    }

    @Test
    fun docDuocChuoiMaHoaUnicode() {
        // Laptop dung `ensure_ascii=False`, nhung mot thu vien JSON khac
        // co the khong. Doc duoc ca hai dang thi khong phu thuoc vao do.
        val tra = Payload.parseReply("""{"say":"Bạn"}""")
        assertEquals("Bạn", tra.say)
    }

    @Test
    fun soAmVaSoMuDocDuoc() {
        val tra = Payload.parseReply(
            """{"con_lai_giay":-12.5,"tong_giay":1.8e3}""")
        assertEquals(-12.5, tra.conLaiGiay!!, 1e-6)
        assertEquals(1800.0, tra.tongGiay!!, 1e-6)
    }

    @Test
    fun goiTinRacKhongLamNo() {
        // Khong dung mot cau assert nao ve noi dung - chi doi la no
        // KHONG nem loi. Mot byte rac tren WiFi khong duoc lam sap app.
        for (rac in listOf("", "{", "}", "khong phai json",
                           """{"say":""", """{"tu_the":}""")) {
            Payload.parseReply(rac)
        }
    }

    // ============================================================
    // Ranh gioi du lieu
    // ============================================================

    @Test
    fun goiTinKHONG_mang_nhat_ky_hay_ten_loi_nhac() {
        // Bang o dau `bridge.py`. Bai test nay bat luc co ai them mot
        // tham so moi vao `buildUpdate` ma khong doc bang do.
        val s = Payload.buildUpdate(
            tSeconds = 0.0, trenManHinh = true,
            voice = "câu người dùng vừa nói",
            noiDung = "viết báo cáo",
            lichSu = "{\"viết báo cáo\":[{\"that\":35}]}")
        for (cam in listOf("nhat_ky", "ghi_chu", "the_nao", "cam_xuc",
                           "loi_nhac", "thuoc", "lieu", "trieu_chung")) {
            assertFalse("$cam co trong goi tin: $s", s.contains(cam))
        }
    }
}
