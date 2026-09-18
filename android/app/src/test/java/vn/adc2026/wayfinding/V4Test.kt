package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.ByteArrayInputStream
import java.util.Calendar
import java.util.zip.ZipInputStream

/**
 * Test cho logic v4 (17/09): lap theo thu, uu tien, nhac tuy y, dong ho
 * dem nguoc, loi nhan theo ngay, diem danh, xuat Word.
 */
class LichV4Test {
    private val thuHai = Lich.tuNgayThang(2026, 9, 14)

    @Test fun ngay14_09_2026_la_thu_hai() = assertEquals(0, Lich.thu(thuHai))

    @Test fun lapTheoThu_chiRoiDungThuDaChon() {
        val kh = KeHoach("a", "Tập", ngay = thuHai, batDau = 600, lapLai = LapLai.THEO_THU, thuLap = setOf(0, 3))
        assertTrue(Lich.coTrongNgay(kh, thuHai))
        assertFalse(Lich.coTrongNgay(kh, thuHai + 1))
        assertTrue(Lich.coTrongNgay(kh, thuHai + 3))
        assertTrue(Lich.coTrongNgay(kh, thuHai + 10))
        assertFalse("khong roi vao TRUOC ngay bat dau", Lich.coTrongNgay(kh, thuHai - 7))
    }

    @Test fun lapTheoThu_rongThiLayThuCuaNgayBatDau() {
        val kh = KeHoach("a", "Tập", ngay = thuHai, batDau = 600, lapLai = LapLai.THEO_THU)
        assertTrue(Lich.coTrongNgay(kh, thuHai + 7))
        assertFalse(Lich.coTrongNgay(kh, thuHai + 1))
    }

    @Test fun moTaLapLai_docDuocNgay() {
        val kh = KeHoach("a", "Tập", ngay = thuHai, batDau = 600, lapLai = LapLai.THEO_THU, thuLap = setOf(3, 0))
        assertEquals("T2, T5 hằng tuần", Lich.moTaLapLai(kh))
        assertEquals("Hằng ngày", Lich.moTaLapLai(kh.copy(thuLap = (0..6).toSet())))
    }

    @Test fun nhacTruocBaNgay_vanDuocDatChuong() {
        val xa = KeHoach("b", "Nộp hồ sơ", ngay = thuHai + 5, batDau = 540, nhacTruoc = listOf(3 * 1440))
        val ln = Lich.lanNhacToi(listOf(xa), thuHai * 1440 + 480, soNgay = 8)
        assertEquals(1, ln.size)
        assertEquals((thuHai + 2) * 1440 + 540, ln[0].phutTuyetDoi)
    }

    @Test fun moTaNhac_tuy_y() {
        assertEquals("Đúng giờ", Lich.moTaNhac(0))
        assertEquals("1 giờ trước", Lich.moTaNhac(60))
        assertEquals("1 giờ 30 phút trước", Lich.moTaNhac(90))
        assertEquals("2 ngày trước", Lich.moTaNhac(2880))
    }

    @Test fun thoiLuongGiua_quaNuaDem() {
        assertEquals(75, Lich.thoiLuongGiua(540, 615))
        assertEquals(120, Lich.thoiLuongGiua(23 * 60, 60))
        assertEquals("bang nhau = ca ngay, khong phai 0", 1440, Lich.thoiLuongGiua(600, 600))
    }

    @Test fun theoUuTien_caoTruocRoiTheoGio() {
        val g = KeHoach("x", "x", ngay = thuHai, batDau = 600)
        val ds = listOf(g.copy(id = "1", uuTien = UuTien.THAP, batDau = 480),
            g.copy(id = "2", uuTien = UuTien.CAO, batDau = 1200),
            g.copy(id = "3", uuTien = UuTien.VUA), g.copy(id = "4", uuTien = UuTien.CAO, batDau = 300))
        assertEquals(listOf("4", "2", "3", "1"), Lich.theoUuTien(ds).map { it.id })
    }
}

class DemNguocTest {
    @Test fun tranHaiGio() = assertEquals(120 * 60_000L, DemNguoc().datThoiLuong(500).tongMs)
    @Test fun itNhatMotPhut() = assertEquals(60_000L, DemNguoc().datThoiLuong(0).tongMs)

    @Test fun chayTamDungTiepTuc_giuDungPhanConLai() {
        var d = DemNguoc().datThoiLuong(25).batDau(1_000)
        assertEquals(24 * 60_000L, d.conLaiMs(61_000))
        d = d.tamDung(61_000)
        assertEquals("dung thi dong ho khong chay", 24 * 60_000L, d.conLaiMs(9_999_999))
        d = d.batDau(100_000)
        assertEquals(24 * 60_000L, d.conLaiMs(100_000))
    }

    @Test fun themPhut_khongVuotHaiGio() {
        val d = DemNguoc().datThoiLuong(100).batDau(0).themPhut(60, 0)
        assertEquals(120 * 60_000L, d.conLaiMs(0))
    }

    @Test fun khongDoiThoiLuongKhiDangChay() {
        val d = DemNguoc().datThoiLuong(25).batDau(0)
        assertEquals(d, d.datThoiLuong(5))
    }

    @Test fun hetGio() {
        val d = DemNguoc().datThoiLuong(1).batDau(0)
        assertFalse(d.daHet(59_999)); assertTrue(d.daHet(60_000))
    }

    @Test fun dinhDang_lamTronLen() {
        assertEquals("25:00", DemNguoc.dinhDang(25 * 60_000L))
        assertEquals("00:01", DemNguoc.dinhDang(1))
        assertEquals("1:30:00", DemNguoc.dinhDang(90 * 60_000L))
    }
}

class LoiNhanNgayTest {
    @Test fun khongBaoGioTrungHomQua() {
        for (n in 19_000L..21_000L) assertNotEquals(LoiNhanNgay.cua(n), LoiNhanNgay.cua(n + 1))
    }
    @Test fun bamMotNgayMoiCauDeuXuatHien() =
        assertEquals(LoiNhanNgay.CAU.size, (0L until LoiNhanNgay.CAU.size).map { LoiNhanNgay.cua(it) }.toSet().size)
    @Test fun khongCoCauRaLenh() {
        for (c in LoiNhanNgay.CAU) {
            val t = c.lowercase()
            assertFalse(c, "bạn phải" in t || "bạn nên" in t || "cố lên" in t)
        }
    }
}

class DiemDanhTest {
    private fun ngay(d: Int) = Calendar.getInstance().apply { clear(); set(2026, 8, d) }

    @Test fun chiMoAppCungTinhVaoChuoi() {
        val so = SoTienDo()
        so.diemDanh("2026-09-15"); so.diemDanh("2026-09-16")
        assertEquals(2, so.chuoi(ngay(16)))
        assertEquals("diem danh khong phai la xong viec", 0, so.tongSoViec())
    }
    @Test fun diemDanhHaiLanMotNgay_chiTinhMot() {
        val so = SoTienDo()
        assertTrue(so.diemDanh("2026-09-16")); assertFalse(so.diemDanh("2026-09-16"))
    }
    @Test fun tuanDanhDauNgayChiMoApp() {
        val so = SoTienDo(); so.diemDanh("2026-09-16")
        assertTrue(so.tuan(ngay(16)).last().second)
    }
}

class DocxVietTest {
    private fun tep(b: ByteArray): Map<String, String> {
        val ra = mutableMapOf<String, String>()
        ZipInputStream(ByteArrayInputStream(b)).use { z ->
            while (true) { val e = z.nextEntry ?: break; ra[e.name] = z.readBytes().toString(Charsets.UTF_8) }
        }
        return ra
    }
    private val khoi = listOf(DocxViet.Khoi.TieuDe("Họp <nhóm> & chốt"),
        DocxViet.Khoi.Doan("Câu một khá dài để vượt ngưỡng tách ý của bản dễ đọc, có đủ chữ. Câu hai cũng dài vừa phải để thành một gạch riêng biệt nữa."))

    @Test fun duCacTepBatBuoc() {
        val t = tep(DocxViet.tao("x", khoi, DocxViet.HoSo.TIEU_CHUAN))
        for (n in listOf("[Content_Types].xml", "_rels/.rels", "word/document.xml", "word/styles.xml", "word/_rels/document.xml.rels"))
            assertTrue(n, n in t)
    }
    @Test fun thoatKyTuXml() {
        val doc = tep(DocxViet.tao("x", khoi, DocxViet.HoSo.TIEU_CHUAN))["word/document.xml"]!!
        assertTrue(doc.contains("Họp &lt;nhóm&gt; &amp; chốt"))
    }
    @Test fun banDeDoc_verdanaGianDongNenKemCanTrai() {
        val t = tep(DocxViet.tao("x", khoi, DocxViet.HoSo.DE_DOC))
        val st = t["word/styles.xml"]!!
        assertTrue(st.contains("Verdana")); assertTrue(st.contains("w:line=\"360\""))
        assertTrue(st.contains("<w:jc w:val=\"left\"/>")); assertFalse(st.contains("<w:i/>"))
        assertTrue(t["word/document.xml"]!!.contains("FFF8E7"))
        assertTrue(t["word/settings.xml"]!!.contains("displayBackgroundShape"))
    }
    @Test fun banDeDoc_tachCauDaiThanhGachDau() {
        assertEquals(2, DocxViet.tachY((khoi[1] as DocxViet.Khoi.Doan).chu).size)
        assertEquals(1, DocxViet.tachY("Ngắn.").size)
    }
    @Test fun boKyTuDieuKhienLamHongTep() = assertEquals("ab", DocxViet.esc("a\u0001b"))
}
