package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class LichTest {

    private val d = Lich.tuNgayThang(2026, 9, 16)      // Thu Tu

    @Test
    fun ngayThangDiVeKhop() {
        assertEquals(Triple(2026, 9, 16), Lich.ngayThang(d))
        assertEquals(Triple(2028, 2, 29), Lich.ngayThang(Lich.tuNgayThang(2028, 2, 29)))
        assertEquals(2, Lich.thu(d))
        assertEquals(Lich.tuNgayThang(2026, 9, 14), Lich.dauTuan(d))
    }

    @Test
    fun lapHangTuanChiDungThu() {
        val kh = KeHoach("a", "Đi bơi", ngay = d, batDau = 1080, lapLai = LapLai.HANG_TUAN)
        assertTrue(Lich.coTrongNgay(kh, d + 7))
        assertFalse(Lich.coTrongNgay(kh, d + 1))
        assertFalse(Lich.coTrongNgay(kh, d - 7))
    }

    @Test
    fun nhacSapTheoThoiGianVaBoLanDaQua() {
        val kh = KeHoach("c", "Viết báo cáo", ngay = d, batDau = 840, nhacTruoc = listOf(15, 0, 1440))
        val ln = Lich.lanNhacToi(listOf(kh), d * 1440 + 780)
        assertEquals(listOf(15, 0), ln.map { it.truoc })
    }

    @Test
    fun nhacMotNgayTruocChoKeHoachNgayMai() {
        val kh = KeHoach("e", "Khám răng", ngay = d + 1, batDau = 540, nhacTruoc = listOf(1440))
        assertEquals(d * 1440 + 540, Lich.lanNhacToi(listOf(kh), d * 1440 + 480).single().phutTuyetDoi)
    }

    @Test
    fun tiepTheoBoQuaViecDaXong() {
        val kh = KeHoach("c", "Viết báo cáo", ngay = d, batDau = 840)
        assertEquals("c", Lich.tiepTheo(listOf(kh), d * 1440 + 850, emptySet())?.id)
        assertNull(Lich.tiepTheo(listOf(kh), d * 1440 + 780, setOf(Lich.khoaXong("c", d))))
    }

    @Test
    fun cauNhacNeoVaoGioThat() {
        val kh = KeHoach("c", "Viết báo cáo", ngay = d, batDau = 840)
        assertEquals("Còn 15 phút nữa, lúc 14:00: Viết báo cáo.",
            Lich.cauNhac(LanNhac(kh, d, 15, d * 1440 + 825)))
    }
}
