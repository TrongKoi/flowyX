package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * ====================================================================
 * KIEM THU PHAN XAC THUC (v5)
 * ====================================================================
 *
 * Chi kiem cac ham THUAN trong `KhoDuLieu.Companion` va `TaiKhoan`:
 * bam mat khau, so sanh hang dinh, kiem dinh dang email, do manh, dinh
 * dang ma khoi phuc.
 *
 * Phan dung co so du lieu (dangKy/dangNhap/doiMatKhau) khong kiem duoc o
 * day: chung can SQLite that cua Android, ma `android.jar` trong duong
 * build nay chi co lop rong. Chung duoc kiem bang tay tren may that -
 * xem docs/BAO_MAT.md muc 6.
 */
class XacThucTest {

    // ---------------------------------------------------------------
    // Bam mat khau
    // ---------------------------------------------------------------

    @Test
    fun cungMatKhauCungMuoiThiCungBam() {
        val muoi = ByteArray(16) { it.toByte() }
        assertEquals(KhoDuLieu.bam("con meo ngu gat", muoi),
                     KhoDuLieu.bam("con meo ngu gat", muoi))
    }

    @Test
    fun khacMuoiThiKhacBam() {
        val a = ByteArray(16) { it.toByte() }
        val b = ByteArray(16) { (it + 1).toByte() }
        assertNotEquals(KhoDuLieu.bam("con meo ngu gat", a),
                        KhoDuLieu.bam("con meo ngu gat", b))
    }

    @Test
    fun muoiMoiKhongTrungNhau() {
        // 16 byte ngau nhien: trung nhau trong mot nghin lan la khong the,
        // tru khi nguon ngau nhien hong han.
        val ds = (1..200).map { KhoDuLieu.muoiMoi().joinToString("") { b -> b.toString() } }
        assertEquals(200, ds.toSet().size)
    }

    @Test
    fun banBamKhongChuaMatKhauThuong() {
        val muoi = KhoDuLieu.muoiMoi()
        val bam = KhoDuLieu.bam("mat khau rat de nhin thay", muoi)
        assertFalse(bam.contains("mat khau"))
    }

    // ---------------------------------------------------------------
    // So sanh hang dinh
    // ---------------------------------------------------------------

    @Test
    fun bangNhauDungVoiChuoiGiongNhau() {
        assertTrue(KhoDuLieu.bangNhau("abcdef", "abcdef"))
    }

    @Test
    fun bangNhauSaiKhiLechMotKyTu() {
        assertFalse(KhoDuLieu.bangNhau("abcdef", "abcdeg"))
    }

    @Test
    fun bangNhauSaiKhiLechDoDai() {
        assertFalse(KhoDuLieu.bangNhau("abcdef", "abcde"))
        assertFalse(KhoDuLieu.bangNhau("", "a"))
    }

    // ---------------------------------------------------------------
    // Email
    // ---------------------------------------------------------------

    @Test
    fun emailThuongLeThiHopLe() {
        for (e in listOf("ai.do@gmail.com", "ten_co.dau@truong.edu.vn", "a@b.co")) {
            assertTrue(e, KhoDuLieu.emailHopLe(e))
        }
    }

    @Test
    fun emailThieuBoPhanThiKhongHopLe() {
        for (e in listOf("", "khong-co-a-cong", "@gmail.com", "ai@", "ai@gmail",
                         "co khoang trang@gmail.com", "hai@@gmail.com")) {
            assertFalse(e, KhoDuLieu.emailHopLe(e))
        }
    }

    // ---------------------------------------------------------------
    // Do manh mat khau
    // ---------------------------------------------------------------

    @Test
    fun doManhTangTheoDoDai() {
        val ngan = KhoDuLieu.doManh("12345678")
        val dai = KhoDuLieu.doManh("mot cau bon tu that dai va de nho")
        assertTrue("dai phai manh hon ngan", dai > ngan)
    }

    @Test
    fun doManhNamTrongKhoangHopLe() {
        for (mk in listOf("", "a", "12345678", "Abc12345!", "cau rat dai de nho lam")) {
            val d = KhoDuLieu.doManh(mk)
            assertTrue("$mk -> $d", d in 0..2)
        }
    }

    @Test
    fun toiThieuTamKyTuTheoOwasp() {
        assertEquals(8, KhoDuLieu.TOI_THIEU)
    }

    @Test
    fun soVongPbkdf2DungKhuyenNghi2023() {
        // OWASP 2023 cho PBKDF2-HMAC-SHA256. Ha con so nay xuong la ha
        // gia thanh cua mot cuoc do vet - neu doi, phai doi co y thuc.
        assertEquals(210_000, KhoDuLieu.VONG)
    }

    // ---------------------------------------------------------------
    // Ma khoi phuc
    // ---------------------------------------------------------------

    @Test
    fun dinhDangMaChiaBaCumBonKyTu() {
        assertEquals("ABCD-EFGH-JKLM", TaiKhoan.dinhDangMa("ABCDEFGHJKLM"))
    }

    @Test
    fun dinhDangMaKhongLamHongChuoiNgan() {
        assertEquals("AB", TaiKhoan.dinhDangMa("AB"))
    }
}
