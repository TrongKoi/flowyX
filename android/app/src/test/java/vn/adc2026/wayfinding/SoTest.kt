package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Kiem ba so cua rieng dien thoai.
 *
 * Moi lop o day co mot ban goc bang Python duoi `wayfinding/adhd/`, va
 * hai ban PHAI cho cung mot con so. Cac bai test duoi lay dung nhung
 * truong hop moc ma ban Python khoa, de mot ben lech la lo ra ngay.
 *
 *     SoThoiLuong  <- thoiluong.py   (test_thoiluong.py)
 *     SoNhac       <- nhacviec.py    (test_nhacviec.py)
 *     SoNhatKy     <- nhatky.py      (test_nhatky.py)
 *
 * Phan `doc()` / `luu()` can `Context` nen khong kiem o day; phan logic
 * va phan doc JSON thi khong can gi ca.
 */
class SoThoiLuongTest {

    private val viec = "viết báo cáo"

    @Test
    fun chuaCoSoLieuThiKhongUocDuoc() {
        // Chua biet thi noi khong biet, khong doan.
        assertNull(SoThoiLuong().uocLuong(viec))
    }

    @Test
    fun motLanThiDungLuonLanDo() {
        val so = SoThoiLuong()
        so.ghi(viec, thatPhut = 35.0, uocPhut = 20.0)
        assertEquals(35.0, so.uocLuong(viec)!!, 1e-9)
    }

    @Test
    fun dungTRUNG_VI_chuKhongPhaiTrungBinh() {
        // Mot lan bi gian doan bat thuong keo trung binh lech han.
        // Trung binh o day se la 98,25.
        val so = SoThoiLuong()
        for (p in listOf(30.0, 32.0, 31.0, 300.0)) so.ghi(viec, p)
        assertEquals(31.5, so.uocLuong(viec)!!, 1e-9)
    }

    @Test
    fun chiXetMayLanGanNhat() {
        val so = SoThoiLuong()
        repeat(10) { so.ghi(viec, 120.0) }        // nhung lan dau, rat cham
        repeat(SoThoiLuong.SO_LAN_XET) { so.ghi(viec, 20.0) }   // gio da nhanh
        assertEquals(20.0, so.uocLuong(viec)!!, 1e-9)
    }

    @Test
    fun ghiDuLieuVoNghiaThiBoQua() {
        val so = SoThoiLuong()
        so.ghi("", 30.0)
        so.ghi(viec, 0.0)
        so.ghi(viec, -5.0)
        assertEquals(0, so.soLan(viec))
    }

    @Test
    fun cauDoiChieuNeuCaHaiConSo() {
        val so = SoThoiLuong()
        so.ghi(viec, thatPhut = 35.0, uocPhut = 20.0)
        val s = so.cauDoiChieu(viec)!!
        assertTrue(s, s.contains("20") && s.contains("35"))
    }

    @Test
    fun uocGanDungThi_IM_LANG() {
        // Noi ra mot chenh lech khong dang ke se lam cau canh bao mat
        // gia tri o nhung lan that su lech nhieu.
        val so = SoThoiLuong()
        so.ghi(viec, thatPhut = 22.0, uocPhut = 20.0)
        assertNull(so.cauDoiChieu(viec))
    }

    @Test
    fun khongUocThiKhongCoGiDeDoiChieu() {
        val so = SoThoiLuong()
        so.ghi(viec, 35.0)
        assertNull(so.cauDoiChieu(viec))
    }

    @Test
    fun cauDoiChieu_KHONG_ketLuanVeNguoiDung() {
        // "Ban hay uoc thieu" la nhan xet ve tinh cach; "lan truoc 20,
        // thuc te 35" la con so ho tu doi chieu duoc.
        val so = SoThoiLuong()
        so.ghi(viec, thatPhut = 35.0, uocPhut = 20.0)
        val s = so.cauDoiChieu(viec)!!.lowercase()
        for (xau in listOf("bạn hay", "bạn thường", "bạn luôn", "bạn kém",
                           "đáng lẽ", "lẽ ra", "sai")) {
            assertFalse(s, s.contains(xau))
        }
    }

    @Test
    fun cauKHOP_TUNG_CHU_voiBanPython() {
        // Hai ban doc len cho nguoi dung nghe. Lech mot chu la hai thiet
        // bi noi hai kieu cho cung mot tinh huong.
        val so = SoThoiLuong()
        so.ghi(viec, thatPhut = 35.0, uocPhut = 20.0)
        assertEquals("Lần trước bạn ước 20 phút, thực tế 35 phút.",
            so.cauDoiChieu(viec))
        assertEquals("Những lần trước việc này mất khoảng 35 phút.",
            so.cauGoiY(viec))
    }

    @Test
    fun jsonMotViecChiMangDungViecDo() {
        // Gui ca so la dua lich su lam viec len duong truyen, va bang
        // trong bridge.py cam dieu do.
        val so = SoThoiLuong()
        so.ghi(viec, 35.0, 20.0)
        so.ghi("dọn phòng", 15.0)
        val s = so.jsonMotViec(viec)!!
        assertTrue(s, s.contains(viec))
        assertFalse(s, s.contains("dọn phòng"))
    }

    @Test
    fun luuRoiDocLaiGiuNguyen() {
        val so = SoThoiLuong()
        so.ghi(viec, 35.0, 20.0)
        so.ghi(viec, 30.0)
        val lai = SoThoiLuong.tuJson(so.jsonMotViec(viec)!!)
        assertEquals(so.uocLuong(viec)!!, lai.uocLuong(viec)!!, 1e-9)
        assertEquals(so.cauDoiChieu(viec), lai.cauDoiChieu(viec))
    }

    @Test
    fun soHongThiBatDauLaiChuKhongLamSap() {
        // Mat lich su la mot phien toai; app khong chay duoc la mot loi.
        assertEquals(0, SoThoiLuong.tuJson("khong phai json").soLan(viec))
        assertEquals(0, SoThoiLuong.tuJson("[]").soLan(viec))
        assertEquals(0, SoThoiLuong.tuJson("""{"$viec":[{"thieu":1}]}""")
            .soLan(viec))
    }

    @Test
    fun banGhiHongLeKhongLamMatCaMuc() {
        val so = SoThoiLuong.tuJson(
            """{"$viec":[{"that":30},{"hong":true},{"that":40}]}""")
        assertEquals(2, so.soLan(viec))
    }
}

class SoNhacTest {

    private val homNay = "2026-09-15"
    private val mai = "2026-09-16"

    @Test
    fun themRoiCoTrongDanhSach() {
        val so = SoNhac()
        assertTrue(so.them("uống nước", 8 * 60.0))
        assertEquals("uống nước", so.danhSach[0].ten)
    }

    @Test
    fun tenQuaNganThiKhongNhan() {
        val so = SoNhac()
        assertFalse(so.them("ab", 8 * 60.0))
        assertFalse(so.them("   ", 8 * 60.0))
        assertEquals(0, so.danhSach.size)
    }

    @Test
    fun gioNgoaiMotNgayThiKhongNhan() {
        val so = SoNhac()
        assertFalse(so.them("việc gì đó", -1.0))
        assertFalse(so.them("việc gì đó", 1440.0))
        assertEquals(0, so.danhSach.size)
    }

    @Test
    fun dungGioThiBao() {
        val so = SoNhac()
        so.them("uống nước", 8 * 60.0)
        assertEquals("uống nước", so.denHan(8 * 60.0, homNay)?.ten)
    }

    @Test
    fun chuaToiGioThiIm() {
        val so = SoNhac()
        so.them("uống nước", 8 * 60.0)
        assertNull(so.denHan(8 * 60.0 - 1.0, homNay))
    }

    @Test
    fun treTrongCuaSoThiVanBao() {
        val so = SoNhac()
        so.them("uống nước", 8 * 60.0)
        assertNotNull(so.denHan(8 * 60.0 + SoNhac.CUA_SO_PHUT - 1.0, homNay))
    }

    @Test
    fun treQuaCuaSoThi_THOI() {
        // Khong bao mai: mot loi nhac hien lien tuc se bi tat di, va
        // luc do moi loi nhac khac cung mat theo.
        val so = SoNhac()
        so.them("uống nước", 8 * 60.0)
        assertNull(so.denHan(8 * 60.0 + SoNhac.CUA_SO_PHUT + 1.0, homNay))
    }

    @Test
    fun baoRoiThiKhongBaoLaiTrongNgay() {
        val so = SoNhac()
        so.them("uống nước", 8 * 60.0)
        assertNotNull(so.denHan(8 * 60.0, homNay))
        assertNull(so.denHan(8 * 60.0 + 1.0, homNay))
    }

    @Test
    fun sangNgayMoiThiBaoLai() {
        val so = SoNhac()
        so.them("uống nước", 8 * 60.0)
        so.denHan(8 * 60.0, homNay)
        assertNotNull(so.denHan(8 * 60.0, mai))
    }

    @Test
    fun xoaRoiThiMucConLaiVanBaoDuoc() {
        // Chi so `daBao` phai truot theo khi mot muc bi xoa. Neu khong,
        // xoa muc dau se lam muc thu hai bi coi nhu da bao roi.
        val so = SoNhac()
        so.them("việc sáng", 8 * 60.0)
        so.them("việc trưa", 12 * 60.0)
        so.denHan(8 * 60.0, homNay)
        so.xoa(0)
        assertEquals("việc trưa", so.denHan(12 * 60.0, homNay)?.ten)
    }

    @Test
    fun cauKHOP_TUNG_CHU_voiBanPython() {
        assertEquals("Đã tới giờ: uống nước.",
            SoNhac.LoiNhac("uống nước", 8 * 60.0).cau())
    }

    @Test
    fun cau_KHONG_themLoiKhuyenNao() {
        // App nhac dung cai nguoi dung bao no nhac, va khong noi gi
        // them. "Nho uong du nuoc nhe" la loi khuyen suc khoe.
        val s = SoNhac.LoiNhac("uống nước", 8 * 60.0).cau().lowercase()
        for (xau in listOf("nên", "nhớ", "đừng quên", "hãy", "tốt cho")) {
            assertFalse(s, s.contains(xau))
        }
    }

    @Test
    fun tenLaChuoiTUDO_khongDoiChieuDanhMucNao() {
        // Module khong duoc biet ten nguoi dung go la gi. Biet ten thuoc
        // la biet chan doan.
        val so = SoNhac()
        for (ten in listOf("uống nước", "gọi mẹ", "xyzzy", "!!!???")) {
            assertTrue(ten, so.them(ten, 9 * 60.0))
        }
        assertEquals(4, so.danhSach.size)
    }

    @Test
    fun luuRoiDocLaiGiuNguyen() {
        val so = SoNhac()
        so.them("uống nước", 8 * 60.0)
        so.them("gọi mẹ", 19 * 60.0, lapLaiHangNgay = false)
        val json = org.json.JSONArray().apply {
            for (ln in so.danhSach) {
                put(org.json.JSONObject()
                    .put("ten", ln.ten).put("gio", ln.gio)
                    .put("lap_lai", ln.lapLaiHangNgay))
            }
        }.toString()
        val lai = SoNhac.tuJson(json)
        assertEquals(listOf("uống nước", "gọi mẹ"), lai.danhSach.map { it.ten })
        assertFalse(lai.danhSach[1].lapLaiHangNgay)
    }

    @Test
    fun soHongThiBatDauLaiChuKhongLamSap() {
        assertEquals(0, SoNhac.tuJson("khong phai json").danhSach.size)
        assertEquals(0, SoNhac.tuJson("""[{"thieu_khoa":1}]""").danhSach.size)
    }

    @Test
    fun gioPhutHienDungDinhDang() {
        assertEquals("08:30", SoNhac.LoiNhac("việc gì đó", 510.0).gioPhut)
        assertEquals("00:05", SoNhac.LoiNhac("việc gì đó", 5.0).gioPhut)
    }
}

class SoNhatKyTest {

    private val luc = 1_757_000_000_000L

    @Test
    fun ghiRoiCoTrongSo() {
        val so = SoNhatKy()
        assertTrue(so.ghi("hôm nay khó vào việc", luc = luc))
        assertEquals("hôm nay khó vào việc", so.muc[0].noiDung)
    }

    @Test
    fun noiDungRongThiKhongNhan() {
        val so = SoNhatKy()
        assertFalse(so.ghi(""))
        assertFalse(so.ghi("   "))
        assertFalse(so.ghi("a"))
        assertEquals(0, so.muc.size)
    }

    @Test
    fun theNaoLa_CHU_khongPhaiSo() {
        // Thang 1-5 tien cho app hon, va do chinh la ly do khong dung
        // no: mot con so chi co ich khi co gi do cong no lai, ma cong
        // lai la thu khong duoc lam.
        val so = SoNhatKy()
        for (chu in listOf("mệt", "ổn", "như bị kéo từng mảnh")) {
            so.ghi("ghi chú", theNao = chu, luc = luc)
        }
        assertEquals(listOf("mệt", "ổn", "như bị kéo từng mảnh"),
            so.muc.map { it.theNao })
    }

    @Test
    fun theNaoToanKhoangTrangCoiNhuKhongCo() {
        val so = SoNhatKy()
        so.ghi("ghi chú", theNao = "   ", luc = luc)
        assertNull(so.muc[0].theNao)
    }

    @Test
    fun quaGioiHanThiMucCuNhatRoiRa() {
        // Gioi han nay la gioi han RIENG TU, khong phai gioi han ky
        // thuat: mot quyen so khong gioi han la mot ho so dai vo han ve
        // mot nguoi.
        val so = SoNhatKy()
        for (i in 0 until SoNhatKy.TOI_DA_MUC + 10) {
            so.ghi("muc $i", luc = luc + i)
        }
        assertEquals(SoNhatKy.TOI_DA_MUC, so.muc.size)
        assertEquals("muc 10", so.muc[0].noiDung)
    }

    @Test
    fun nguoiDungXoaDuocBatCuMucNao() {
        // Quyen xoa la mot phan cua quyen so huu. Mot quyen so khong xe
        // duoc trang la mot ho so.
        val so = SoNhatKy()
        for (i in 0 until 3) so.ghi("muc $i", luc = luc + i)
        assertTrue(so.xoa(1))
        assertEquals(listOf("muc 0", "muc 2"), so.muc.map { it.noiDung })
    }

    @Test
    fun ganDayTraVeCacMucMoiNhat() {
        val so = SoNhatKy()
        for (i in 0 until 10) so.ghi("muc $i", luc = luc + i)
        assertEquals(listOf("muc 7", "muc 8", "muc 9"),
            so.ganDay(3).map { it.noiDung })
    }

    @Test
    fun soTrongThiXuatRaChuoiRong() {
        assertEquals("", SoNhatKy().xuatVanBan())
    }

    @Test
    fun xuatGomMoiMucTheoThuTu() {
        val so = SoNhatKy()
        for (i in 0 until 3) so.ghi("muc $i", luc = luc + i * 60_000)
        val dong = so.xuatVanBan().trim().split("\n")
        assertEquals(3, dong.size)
        assertTrue(dong[0], dong[0].contains("muc 0"))
        assertTrue(dong[2], dong[2].contains("muc 2"))
    }

    @Test
    fun banXuat_KHONG_coNhanXetNaoCuaApp() {
        // Ban xuat la so cua nguoi dung, khong phai bao cao cua app.
        val so = SoNhatKy()
        so.ghi("hôm nay khó vào việc", theNao = "mệt", luc = luc)
        val s = so.xuatVanBan().lowercase()
        for (xau in listOf("tổng", "trung bình", "xu hướng", "nhận xét",
                           "kết luận", "điểm", "so với", "bạn nên")) {
            assertFalse(s, s.contains(xau))
        }
    }

    @Test
    fun soHongThiBatDauLaiChuKhongLamSap() {
        assertEquals(0, SoNhatKy.tuJson("khong phai json").muc.size)
        assertEquals(0, SoNhatKy.tuJson("""[{"thieu_khoa":1}]""").muc.size)
    }

    @Test
    fun mucHongLeKhongLamMatMucConLai() {
        val so = SoNhatKy.tuJson(
            """[{"luc":$luc,"noi_dung":"muc mot"},
                {"hong":true},
                {"luc":${luc + 60}, "noi_dung":"muc hai"}]""")
        assertEquals(listOf("muc mot", "muc hai"), so.muc.map { it.noiDung })
    }
}
