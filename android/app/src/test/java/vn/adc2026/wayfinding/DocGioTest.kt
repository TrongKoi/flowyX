package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * Khoa bug o gio tu buoi test tren Galaxy Tab S7 FE: ban phim chi co so,
 * go "1400" bi bao sai.
 */
class DocGioTest {

    @Test
    fun coDauPhanCach() {
        assertEquals(840.0, DocGio.doc("14:00")!!, 0.0)
        assertEquals(510.0, DocGio.doc("08:30")!!, 0.0)
        assertEquals(870.0, DocGio.doc("14.30")!!, 0.0)
        assertEquals(870.0, DocGio.doc("14h30")!!, 0.0)
        assertEquals(840.0, DocGio.doc("14h")!!, 0.0)
        assertEquals(425.0, DocGio.doc(" 7 : 05 ")!!, 0.0)
    }

    @Test
    fun chiCoSo_banPhimSamsung() {
        assertEquals(840.0, DocGio.doc("1400")!!, 0.0)
        assertEquals(570.0, DocGio.doc("930")!!, 0.0)
        assertEquals(540.0, DocGio.doc("9")!!, 0.0)
        assertEquals(0.0, DocGio.doc("0000")!!, 0.0)
        assertEquals(1439.0, DocGio.doc("2359")!!, 0.0)
    }

    @Test
    fun saiThiNull_khongDoan() {
        for (s in listOf("", "abc", "2400", "1260", "25:00", "14:60", "12345")) {
            assertNull("'$s' phai la null", DocGio.doc(s))
        }
        // "14:5" co the la 14:05 hoac 14:50 - khong doan.
        assertNull(DocGio.doc("14:5"))
        assertNull(DocGio.doc(null))
    }

    @Test
    fun hienLaiDungDinhDang() {
        assertEquals("08:30", DocGio.hien(510.0))
        assertEquals("00:00", DocGio.hien(0.0))
    }
}
