package vn.adc2026.wayfinding

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * ====================================================================
 * GIO YEN TINH (muc 3.3)
 * ====================================================================
 *
 * Bai kiem o day co mot muc tieu duy nhat: khung gio VAT QUA NUA DEM.
 *
 * Do la truong hop THUONG GAP NHAT - gio yen tinh dien hinh la 22:00
 * den 07:00 - va cung la truong hop ma mot phep so sanh viet nhanh se
 * lam sai:
 *
 *     phut in tu until den        // 1320 until 420 -> day rong
 *
 * Voi khung vat qua nua dem thi bieu thuc do LUON tra ve false, nghia la
 * gio yen tinh khong bao gio co hieu luc. Va no hong dung o khung gio ma
 * nguoi dung can no nhat - ban dem.
 *
 * Loi kieu nay khong lam app sap, khong lam test nao khac do, va chi lo
 * ra khi co nguoi bi danh thuc luc hai gio sang.
 */
class NhacCaiDatTest {

    private val muoiHaiDem = 22 * 60      // 22:00
    private val bayGioSang = 7 * 60       // 07:00

    // ----- Khung vat qua nua dem: 22:00 -> 07:00 -----

    @Test fun vatQuaNuaDem_truocNuaDem_thiYen() {
        assertTrue(NhacCaiDat.trongGioYen(22 * 60, muoiHaiDem, bayGioSang))
        assertTrue(NhacCaiDat.trongGioYen(23 * 60 + 30, muoiHaiDem, bayGioSang))
    }

    @Test fun vatQuaNuaDem_sauNuaDem_thiVanYen() {
        assertTrue(NhacCaiDat.trongGioYen(0, muoiHaiDem, bayGioSang))
        assertTrue(NhacCaiDat.trongGioYen(2 * 60, muoiHaiDem, bayGioSang))
        assertTrue(NhacCaiDat.trongGioYen(6 * 60 + 59, muoiHaiDem, bayGioSang))
    }

    @Test fun vatQuaNuaDem_ngoaiKhung_thiKhongYen() {
        assertFalse(NhacCaiDat.trongGioYen(bayGioSang, muoiHaiDem, bayGioSang))   // dung 07:00
        assertFalse(NhacCaiDat.trongGioYen(12 * 60, muoiHaiDem, bayGioSang))
        assertFalse(NhacCaiDat.trongGioYen(21 * 60 + 59, muoiHaiDem, bayGioSang))
    }

    // ----- Khung thuong: 13:00 -> 14:00 -----

    @Test fun khungThuong_trongKhungThiYen() {
        assertTrue(NhacCaiDat.trongGioYen(13 * 60, 13 * 60, 14 * 60))
        assertTrue(NhacCaiDat.trongGioYen(13 * 60 + 30, 13 * 60, 14 * 60))
    }

    @Test fun khungThuong_ngoaiKhungThiKhong() {
        assertFalse(NhacCaiDat.trongGioYen(12 * 60 + 59, 13 * 60, 14 * 60))
        assertFalse(NhacCaiDat.trongGioYen(14 * 60, 13 * 60, 14 * 60))   // dau cuoi la mo
    }

    // ----- Truong hop bien -----

    /**
     * Dat hai dau bang nhau khong duoc hieu la "yen ca ngay".
     *
     * Nguoi dung keo hai bo chon ve cung mot gio la chuyen xay ra khi ho
     * dang thu nghich cac lua chon. Neu luc do app im suot 24 gio thi ho
     * se khong noi duoc nguyen nhan, va cach chua duy nhat ho nghi ra la
     * tat han gio yen tinh.
     */
    @Test fun haiDauBangNhau_thiKhongYen() {
        assertFalse(NhacCaiDat.trongGioYen(0, 9 * 60, 9 * 60))
        assertFalse(NhacCaiDat.trongGioYen(9 * 60, 9 * 60, 9 * 60))
        assertFalse(NhacCaiDat.trongGioYen(20 * 60, 9 * 60, 9 * 60))
    }

    @Test fun cacMucChon_deuHopLe() {
        assertTrue(NhacCaiDat.TRUOC_PHIEN.all { it in 0..60 })
        assertTrue(NhacCaiDat.NHAC_LAI.all { it in 0..60 })
        // 0 phai co trong ca hai: "dung gio" va "khong nhac lai" deu la
        // lua chon hop le, khong phai thieu sot.
        assertTrue(0 in NhacCaiDat.TRUOC_PHIEN)
        assertTrue(0 in NhacCaiDat.NHAC_LAI)
    }
}
