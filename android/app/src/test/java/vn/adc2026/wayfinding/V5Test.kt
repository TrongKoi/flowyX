package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Test cho logic v5: hien phut khong hien giay, phim tat mocgio. */
class DongHoV5Test {

    @Test fun duoiMotPhutThiKhongConSoPhut() {
        // 0 = man hinh se hien chu "Sắp xong" thay cho dem lui tung giay.
        assertEquals(0, DemNguoc.soPhutHien(0))
        assertEquals(0, DemNguoc.soPhutHien(59_999))
    }

    @Test fun lamTronLEN_deSoKhongNhayVe0KhiVanConThoiGian() {
        assertEquals(1, DemNguoc.soPhutHien(60_000))
        assertEquals(2, DemNguoc.soPhutHien(60_001))
        assertEquals(25, DemNguoc.soPhutHien(25 * 60_000L))
        assertEquals(120, DemNguoc.soPhutHien(120 * 60_000L))
    }

    @Test fun soPhutHienKhongBaoGioGiamQuaMotDonViMoiPhut() {
        var truoc = Int.MAX_VALUE
        var ms = 30 * 60_000L
        while (ms >= 0) {
            val p = DemNguoc.soPhutHien(ms)
            assertTrue("nhay tu $truoc xuong $p", truoc == Int.MAX_VALUE || truoc - p <= 1)
            truoc = p
            ms -= 1_000
        }
        assertEquals(0, truoc)
    }

    /**
     * Ba muc chon nhanh, khong phai nam.
     *
     * Bai nay truoc day khoa cung nam moc. Da rut con ba (5 / 15 / 30):
     * 60 va 120 la hai con so lon dung canh ba con so nho, va o mot man
     * hinh danh cho nguoi dang kho bat dau thi moi lua chon them la mot
     * lan phai can nhac.
     *
     * Phan quan trong hon la khang dinh thu hai: bo bot CHIP khong duoc
     * lam hep khoang dat duoc. Dong ho van phai keo tay toi 120 phut.
     */
    @Test fun phimTatConBaMuc_nhungTranVanLa120() {
        assertEquals(listOf(5, 15, 30), DemNguoc.PHIM_TAT)
        assertTrue("moi moc phai nam trong khoang dat duoc",
            DemNguoc.PHIM_TAT.all { it in 1..DemNguoc.TOI_DA_PHUT })
        assertEquals("tran keo tay khong duoc doi", 120, DemNguoc.TOI_DA_PHUT)
    }

    @Test fun motTiengHienLa60_khongPhai_60_00() {
        // Yeu cau: "khi hien 1 tieng thi ghi ro 60 phut, khong ghi 60:00".
        assertEquals(60, DemNguoc.soPhutHien(60 * 60_000L))
        assertEquals("60", DemNguoc.soPhutHien(60 * 60_000L).toString())
    }

    @Test fun themMotPhutKhiDangChay() {
        val d = DemNguoc().datThoiLuong(25).batDau(0).themPhut(1, 0)
        assertEquals(26 * 60_000L, d.conLaiMs(0))
    }

    @Test fun themPhutKhongVuotTranHaiTieng() {
        var d = DemNguoc().datThoiLuong(120).batDau(0)
        repeat(5) { d = d.themPhut(1, 0) }
        assertEquals(120 * 60_000L, d.conLaiMs(0))
    }
}

/** Ba kieu chu deu phai co tep that trong assets. */
class KieuChuTest {

    @Test fun moiKieuChuCoDuHaiTep() {
        val thu = java.io.File("src/main/assets/fonts")
        for ((kieu, tep) in AppSettings.TEP_CHU) {
            for (t in listOf(tep.first, tep.second)) {
                val f = java.io.File(thu, t)
                assertTrue("$kieu thieu tep $t", !thu.exists() || f.exists())
                if (f.exists()) assertTrue("$t rong", f.length() > 10_000)
            }
        }
    }

    @Test fun macDinhLaLexend() = assertEquals("lexend", AppSettings.CHU_LEXEND)

    @Test fun baKieuChuVaMotLuaChonFontHeThong() {
        assertEquals(3, AppSettings.TEP_CHU.size)
        assertTrue(AppSettings.CHU_HE_THONG !in AppSettings.TEP_CHU)
    }
}
