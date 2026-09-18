package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * DOI CHIEU VOI BAN GHI THAT CUA `run_flowy.py`.
 *
 * ====================================================================
 * HAI TEP NAY TU DAU MA RA
 * ====================================================================
 *
 * Khong phai go tay. Ca hai la ban ghi cua mot lan chay that:
 *
 *     goi-tin-kotlin.txt    `Payload.buildUpdate` sinh ra, tung dong
 *     tra-loi-python.txt    `run_flowy.py` tra ve khi nhan dung nhung
 *                           dong do, qua HTTP tren cong 8794
 *
 * Cach lam lai khi hop dong doi:
 *
 *     1. chay `python run_flowy.py --port 8794 --muc-dich "..."`
 *     2. POST tung dong cua goi-tin-kotlin.txt len /update
 *     3. ghi cau tra loi vao tra-loi-python.txt, mot dong mot cau
 *
 * ====================================================================
 * VI SAO BAI TEST NAY DANG GIA
 * ====================================================================
 *
 * `PayloadTest` kiem chuoi do CHINH NO viet ra. Neu toi hieu sai dinh
 * dang cua ban Python thi ca hai phia cua bai test do deu sai theo, va
 * no van xanh.
 *
 * File nay thi khac: no doc chu do ban Python that su sinh ra. Sai lech
 * ve `ensure_ascii`, ve khoang trang sau dau hai cham, ve cach ghi so
 * thuc - nhung thu `PayloadTest` khong the thay - deu lo ra o day.
 *
 * Doi lai, no la ban ghi TINH. No khong biet ban Python hom nay tra ve
 * gi; `test_hop_dong.py` ben kia moi giu phan do.
 */
class DoiChieuBanPythonTest {

    private fun doc(ten: String): List<String> =
        javaClass.classLoader!!.getResourceAsStream(ten)!!
            .bufferedReader(Charsets.UTF_8).readLines()
            .filter { it.isNotBlank() }

    private val traLoi by lazy { doc("tra-loi-python.txt").map { Payload.parseReply(it) } }

    @Test
    fun docDuocMoiCauTraLoiThat() {
        assertEquals(10, traLoi.size)
    }

    @Test
    fun daySoKhopVoiKichBan() {
        // Kich ban: hoi ba o y dinh -> bat dau -> cham -> ra khoi app
        // -> quay lai -> cham -> ket thuc.
        val hoi = traLoi.map { it.hoi }
        assertEquals("Bạn định làm gì?", hoi[0])
        assertEquals("Khi nào bạn sẽ làm?", hoi[1])
        assertEquals("Bạn sẽ làm ở đâu?", hoi[2])
        assertEquals(null, hoi[3])
    }

    @Test
    fun dauTiengVietQuaHaiNgonNguVanNguyenVen() {
        // Cho de hong nhat trong ca duong chay. Ban Python dung
        // `ensure_ascii=False`, nen chu Viet di qua day duoi dang UTF-8
        // that chu khong phai \uXXXX.
        assertEquals("Bạn định làm gì?", traLoi[0].hoi)
        assertTrue(traLoi[7].say!!.contains("Bạn đang làm dở"))
    }

    @Test
    fun dauNHAY_trong_ten_viec_qua_duoc_ca_hai_chieu() {
        // Nguoi dung go `viết báo cáo "phần 1"`. Chuoi nay di tu Kotlin
        // sang Python roi quay ve - hai lan thoat, hai lan go thoat.
        // Sai mot buoc la ten cong viec vo trong cau noi.
        assertEquals("viết báo cáo \"phần 1\"", traLoi[4].tenViec)
        assertTrue(traLoi[9].say!!.contains("viết báo cáo \"phần 1\""))
    }

    @Test
    fun cu_cham_thi_co_cau_hoi_VA_bat_micro() {
        // Cu cham la loi moi DUY NHAT de app len tieng.
        assertNotNull(traLoi[5].hoi)
        assertTrue(traLoi[5].listen)
        assertNotNull(traLoi[8].hoi)
        assertTrue(traLoi[8].listen)
    }

    @Test
    fun o_y_dinh_con_thieu_thi_HIEN_ma_KHONG_bat_micro() {
        // Duong ranh cua NHAN_VAT_BRIEF muc 2.4: chu tren man hinh la
        // thu dong, cau doc len la app bat chuyen.
        for (i in 0..2) {
            assertNotNull("goi tin $i", traLoi[i].hoi)
            assertFalse("goi tin $i", traLoi[i].listen)
        }
    }

    @Test
    fun hai_cu_cham_lien_tiep_cho_hai_cau_KHAC_nhau() {
        // Cung mot cau lap lai lan thu nam se thanh tieng on.
        assertTrue(traLoi[5].hoi != traLoi[8].hoi)
    }

    @Test
    fun quay_lai_sau_phan_tam_thi_co_cau_dung_lai_ngu_canh() {
        assertNotNull(traLoi[7].say)
        assertEquals("thong_cam", traLoi[7].ban)
    }

    @Test
    fun ket_thuc_bao_xong_phien_VA_ten_viec() {
        // Dien thoai can ca hai de ghi so thoi luong: mot de biet LUC
        // NAO ghi, mot de biet ghi vao MUC NAO.
        assertTrue(traLoi[9].xongPhien)
        assertEquals("viết báo cáo \"phần 1\"", traLoi[9].tenViec)
    }

    @Test
    fun xong_viec_KHONG_HEN_GIO_van_doi_net_mat_tich_cuc() {
        // Kich ban nay chay khong co `--gio-hen`. Neu chi doi net mat
        // khi co gio hen thi da so lan lam xong deu khong duoc ghi nhan
        // gi tren man hinh.
        assertEquals("vui", traLoi[9].ban)
    }

    @Test
    fun net_mat_KHONG_BAO_GIO_la_mot_trang_thai_tieu_cuc() {
        // ADHD thuong di kem nhay cam voi that bai: mot nhan vat to ra
        // that vong se lam nguoi dung TRANH MO APP, va luc do moi tinh
        // nang khac deu thanh vo dung.
        val hopLe = setOf("binh_thuong", "vui", "thong_cam", "tu_hao")
        for (t in traLoi) assertTrue(t.ban, t.ban in hopLe)
    }

    @Test
    fun nhip_gian_ra_khi_khong_lam_viec() {
        assertEquals(2000, traLoi[0].nhipMs)    // chua bat dau
        assertEquals(500, traLoi[5].nhipMs)     // dang lam
        assertEquals(2000, traLoi[6].nhipMs)    // vua ra khoi app
    }

    @Test
    fun goi_tin_Kotlin_gui_len_cung_duoc_giu_lai() {
        // Nua kia cua ban ghi. Doi `buildUpdate` ma quen sua ben Python
        // thi bai nay van xanh - nhung nguoi sua nhin thay hai tep nay
        // canh nhau va biet la co mot ben kia.
        val goi = doc("goi-tin-kotlin.txt")
        assertEquals(traLoi.size, goi.size)
        assertTrue(goi[1], goi[1].contains("\"voice\":\"viết báo cáo"))
        assertTrue(goi[5], goi[5].contains("\"cham_nhan_vat\":true"))
        assertTrue(goi[6], goi[6].contains("\"tren_man_hinh\":false"))
        assertTrue(goi[9], goi[9].contains("\"lenh\":\"ket_thuc\""))
    }
}
