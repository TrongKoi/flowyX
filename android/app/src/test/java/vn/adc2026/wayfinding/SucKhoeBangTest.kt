package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

/**
 * ====================================================================
 * BANG SUC KHOE (muc 7.2)
 * ====================================================================
 *
 * Phan dang canh gac o day khong phai phep tinh - no la SU IM LANG.
 *
 * `lienHeNguVaViec` duoc phep noi ra mot cau nhan xet ve chinh nguoi
 * dung, va nguoi dung doc man hinh nay vao luc de ton thuong. Mot cau
 * sai o do te hon nhieu so voi khong co cau nao. Nen phan lon cac bai
 * duoi day kiem rang no TRA VE `KHONG_RO` - tuc la khong noi gi.
 */
class SucKhoeBangTest {

    private fun ngay(ten: String, ngu: Int?, viec: Int) =
        SucKhoeBang.Ngay(ten, ngu, null, null, viec)

    // ----- Khi nao duoc noi -----

    @Test fun nguNhieuHonThiXongNhieuHon() {
        val ds = listOf(
            ngay("2026-09-15", 300, 1),   // ngu it
            ngay("2026-09-16", 320, 1),
            ngay("2026-09-17", 480, 5),   // ngu nhieu
            ngay("2026-09-18", 500, 6),
        )
        assertEquals(SucKhoeBang.LienHe.NGU_NHIEU_XONG_NHIEU,
            SucKhoeBang.lienHeNguVaViec(ds))
    }

    @Test fun chieuNguocLaiCungNhanRa() {
        val ds = listOf(
            ngay("2026-09-15", 300, 6),
            ngay("2026-09-16", 320, 5),
            ngay("2026-09-17", 480, 1),
            ngay("2026-09-18", 500, 1),
        )
        assertEquals(SucKhoeBang.LienHe.NGU_NHIEU_XONG_IT_HON,
            SucKhoeBang.lienHeNguVaViec(ds))
    }

    // ----- Khi nao PHAI im -----

    @Test fun duoiBonNgay_thiKhongNoiGi() {
        val ds = listOf(
            ngay("2026-09-15", 300, 1),
            ngay("2026-09-16", 480, 6),
            ngay("2026-09-17", 500, 7),
        )
        assertEquals(SucKhoeBang.LienHe.KHONG_RO, SucKhoeBang.lienHeNguVaViec(ds))
    }

    @Test fun thieuSoNgu_thiKhongTinhVao() {
        // Bon ngay, nhung chi hai ngay co so ngu -> chua du.
        val ds = listOf(
            ngay("2026-09-15", null, 1),
            ngay("2026-09-16", null, 1),
            ngay("2026-09-17", 480, 6),
            ngay("2026-09-18", 300, 1),
        )
        assertEquals(SucKhoeBang.LienHe.KHONG_RO, SucKhoeBang.lienHeNguVaViec(ds))
    }

    @Test fun haiNhomLechIt_thiKhongNoiGi() {
        val ds = listOf(
            ngay("2026-09-15", 300, 3),
            ngay("2026-09-16", 320, 3),
            ngay("2026-09-17", 480, 3),
            ngay("2026-09-18", 500, 4),   // lech 1/4 = 25%? -> duoi nguong sau khi trung binh
        )
        // TB nhom nhieu = 3.5, nhom it = 3.0 -> lech 0,143 < 0,25
        assertEquals(SucKhoeBang.LienHe.KHONG_RO, SucKhoeBang.lienHeNguVaViec(ds))
    }

    /**
     * Tuan khong xong viec nao la tuan nguoi dung dang chat vat nhat.
     * Dung luc do ma app dua ra mot nhan xet ve giac ngu cua ho thi no
     * doc ra nhu mot loi trach.
     */
    @Test fun khongXongViecNao_thiTuyetDoiKhongNoiGi() {
        val ds = listOf(
            ngay("2026-09-15", 300, 0),
            ngay("2026-09-16", 320, 0),
            ngay("2026-09-17", 480, 0),
            ngay("2026-09-18", 500, 0),
        )
        assertEquals(SucKhoeBang.LienHe.KHONG_RO, SucKhoeBang.lienHeNguVaViec(ds))
    }

    @Test fun danhSachRong_thiKhongNoiGi() {
        assertEquals(SucKhoeBang.LienHe.KHONG_RO, SucKhoeBang.lienHeNguVaViec(emptyList()))
    }

    // ----- Trung vi, khong phai trung binh -----

    /**
     * Mot dem thuc trang den ba gio sang du de keo TRUNG BINH lech han,
     * va khi do gan nhu moi ngay con lai deu roi vao nhom "ngu nhieu" -
     * phep so mat nghia. Trung vi khong bi mot ngay ca biet keo di.
     */
    @Test fun trungVi_khongBiMotNgayCaBietKeoDi() {
        // Trung binh cua day nay la 327; trung vi la 410. Ngay 60 phut
        // keo trung binh xuong gan mot tram phut, trung vi thi khong.
        assertEquals(410, SucKhoeBang.trungVi(listOf(60, 400, 420, 430)))
        assertEquals(420, SucKhoeBang.trungVi(listOf(400, 420, 440)))
        assertEquals(0, SucKhoeBang.trungVi(emptyList()))
    }

    // ----- Trung binh bo qua o trong -----

    @Test fun trungBinh_boQuaOTrong() {
        assertEquals(20, SucKhoeBang.trungBinh(listOf(10, null, 30)))
        assertNull(SucKhoeBang.trungBinh(listOf(null, null)))
        assertNull(SucKhoeBang.trungBinh(emptyList()))
    }

    @Test fun ghep_layDungSoViecTheoNgay() {
        val sk = listOf(
            SucKhoe.Ngay("2026-09-17", 480, 8000, 58),
            SucKhoe.Ngay("2026-09-18", 300, null, null),
        )
        val bang = SucKhoeBang.ghep(sk) { n -> if (n == "2026-09-17") 5 else 1 }
        assertEquals(2, bang.size)
        assertEquals(5, bang[0].soViecXong)
        assertEquals(58, bang[0].nhipTimNghi)
        assertEquals(1, bang[1].soViecXong)
        assertNull(bang[1].nhipTimNghi)
    }
}
