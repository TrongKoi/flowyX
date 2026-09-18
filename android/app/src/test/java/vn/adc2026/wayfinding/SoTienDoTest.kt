package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.Calendar

/**
 * Kiem so tien do.
 *
 * Phan de sai nhat la quy tac "chuoi khong dut ngay khi bo mot ngay".
 * No la lua chon co chu dinh, khong phai loi - xem phan dau
 * `SoTienDo.kt` - nen no can duoc khoa lai.
 */
class SoTienDoTest {

    /** Mot ngay co dinh de test khong phu thuoc hom nay la ngay nao. */
    private fun ngay(y: Int, m: Int, d: Int): Calendar =
        Calendar.getInstance().apply {
            clear(); set(y, m - 1, d, 12, 0)
        }

    private fun ten(y: Int, m: Int, d: Int) = SoTienDo.ngayCua(ngay(y, m, d))

    // ============================================================
    // Dem viec
    // ============================================================

    @Test
    fun soTrongThiKhongCoViecNao() {
        assertEquals(0, SoTienDo().tongSoViec())
        assertEquals(0, SoTienDo().chuoi(ngay(2026, 9, 16)))
    }

    @Test
    fun ghiNhieuViecTrongMotNgay() {
        val so = SoTienDo()
        repeat(3) { so.ghi(ten(2026, 9, 16)) }
        assertEquals(3, so.soViec(ten(2026, 9, 16)))
        assertEquals(3, so.tongSoViec())
    }

    @Test
    fun moiNgayDemRieng() {
        val so = SoTienDo()
        so.ghi(ten(2026, 9, 15))
        so.ghi(ten(2026, 9, 16))
        so.ghi(ten(2026, 9, 16))
        assertEquals(1, so.soViec(ten(2026, 9, 15)))
        assertEquals(2, so.soViec(ten(2026, 9, 16)))
    }

    // ============================================================
    // Chuoi ngay
    // ============================================================

    @Test
    fun lamHomNayThiChuoiLaMot() {
        val so = SoTienDo()
        so.ghi(ten(2026, 9, 16))
        assertEquals(1, so.chuoi(ngay(2026, 9, 16)))
    }

    @Test
    fun bonNgayLienTiep() {
        val so = SoTienDo()
        for (d in 13..16) so.ghi(ten(2026, 9, d))
        assertEquals(4, so.chuoi(ngay(2026, 9, 16)))
    }

    @Test
    fun chuoi_KHONG_DUT_khi_hom_nay_chua_lam() {
        // Quy tac co chu dinh: lam hom qua ma hom nay chua lam thi chuoi
        // van con nguyen. Nguoi dung co CA NGAY de tiep, khong phai chay
        // dua voi nua dem.
        val so = SoTienDo()
        for (d in 13..15) so.ghi(ten(2026, 9, d))
        assertEquals(3, so.chuoi(ngay(2026, 9, 16)))
    }

    @Test
    fun bo_HAI_ngay_thi_chuoi_moi_ve_khong() {
        val so = SoTienDo()
        for (d in 12..14) so.ghi(ten(2026, 9, d))
        assertEquals(0, so.chuoi(ngay(2026, 9, 16)))
    }

    @Test
    fun ngay_dut_quang_khong_duoc_dem_gop() {
        // 10, 11 roi nhay sang 15, 16: chuoi la 2, khong phai 4.
        val so = SoTienDo()
        for (d in listOf(10, 11, 15, 16)) so.ghi(ten(2026, 9, d))
        assertEquals(2, so.chuoi(ngay(2026, 9, 16)))
    }

    @Test
    fun chuoi_vat_qua_dau_thang() {
        // Cho de sai neu ai do cong chuoi bang cach tru so ngay thay vi
        // dung Calendar.
        val so = SoTienDo()
        for (d in 29..31) so.ghi(ten(2026, 8, d))
        for (d in 1..2) so.ghi(ten(2026, 9, d))
        assertEquals(5, so.chuoi(ngay(2026, 9, 2)))
    }

    // ============================================================
    // Dai tuan
    // ============================================================

    @Test
    fun daiTuanLuonCoDungBayNgay() {
        assertEquals(7, SoTienDo().tuan(ngay(2026, 9, 16)).size)
    }

    @Test
    fun daiTuanKetThucO_HOM_NAY() {
        val so = SoTienDo()
        so.ghi(ten(2026, 9, 16))
        val t = so.tuan(ngay(2026, 9, 16))
        assertTrue("o cuoi phai la hom nay", t.last().second)
        assertFalse("sau ngay truoc chua lam", t.dropLast(1).any { it.second })
    }

    @Test
    fun nhanThuDungVoiLich() {
        // 16/09/2026 la thu tu. Bay ngay gan nhat ket thuc o T4.
        val t = SoTienDo().tuan(ngay(2026, 9, 16))
        assertEquals("T4", t.last().first)
        assertEquals("T5", t.first().first)
    }

    // ============================================================
    // Luu va doc
    // ============================================================

    @Test
    fun luuRoiDocLaiGiuNguyen() {
        val so = SoTienDo()
        for (d in 14..16) so.ghi(ten(2026, 9, d))
        so.ghi(ten(2026, 9, 16))
        val json = org.json.JSONObject().apply {
            put(ten(2026, 9, 14), 1); put(ten(2026, 9, 15), 1)
            put(ten(2026, 9, 16), 2)
        }.toString()
        val lai = SoTienDo.tuJson(json)
        assertEquals(so.tongSoViec(), lai.tongSoViec())
        assertEquals(so.chuoi(ngay(2026, 9, 16)), lai.chuoi(ngay(2026, 9, 16)))
    }

    @Test
    fun soHongThiBatDauLaiChuKhongLamSap() {
        assertEquals(0, SoTienDo.tuJson("khong phai json").tongSoViec())
        assertEquals(0, SoTienDo.tuJson("[]").tongSoViec())
        assertEquals(0, SoTienDo.tuJson("""{"2026-09-16":"hong"}""").tongSoViec())
    }

    @Test
    fun ngay_cu_hon_gioi_han_thi_roi_ra() {
        // Gioi han RIENG TU: mot ban ghi khong gioi han ve viec ai do lam
        // gi vao ngay nao la mot ho so.
        val so = SoTienDo()
        val c = ngay(2024, 1, 1)
        repeat(SoTienDo.GIU_NGAY + 30) {
            so.ghi(SoTienDo.ngayCua(c))
            c.add(Calendar.DAY_OF_YEAR, 1)
        }
        assertEquals(SoTienDo.GIU_NGAY, so.tongSoViec())
        assertEquals(0, so.soViec(ten(2024, 1, 1)))
    }

    // ============================================================
    // Nhung thu KHONG duoc co
    // ============================================================

    @Test
    fun KHONG_co_ty_le_phan_tram_hay_xu_huong() {
        // Cho nao app quy ghi chep ve mot con so tong hop de DANH GIA,
        // cho do no vuot ranh. Dem so viec thi duoc; cham diem thi khong.
        val so = SoTienDo()
        so.ghi(ten(2026, 9, 16))
        for (ten in listOf("tyLe", "phanTram", "xuHuong", "diem", "mucDo",
                           "soSanh", "tuanTruoc", "danhGia")) {
            assertFalse(ten, SoTienDo::class.java.methods.any {
                it.name.equals(ten, ignoreCase = true)
            })
        }
    }
}
