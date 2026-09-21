package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * ====================================================================
 * PHAN RA TAC VU
 * ====================================================================
 *
 * Doc mot goi JSON do MOT MO HINH sinh ra, va khong mo hinh nao tra ve
 * dung dinh dang moi lan. Nen phan lon cac bai duoi day khong kiem
 * "doc dung khi moi thu binh thuong" - chung kiem app **khong vo** khi
 * mo hinh tra ve thu khac voi da bao.
 *
 * Bai quan trong nhat la `nhieuHonNamBuoc_thiCatCung`: prompt co gioi
 * han 5 buoc, nhung prompt la mot LOI DE NGHI, khong phai mot rang
 * buoc. Neu mo hinh tra 12 buoc ma app hien het ra, ta vua doi mot viec
 * khong bat dau duoc thanh muoi hai viec khong bat dau duoc.
 */
class PhanRaTest {

    // ----- Duong binh thuong -----

    @Test fun docDuocGoiChuan() {
        val kq = PhanRa.doc("""
            {"steps":[
              {"buoc_so":1,"ten_hanh_dong":"Mở tệp báo cáo","thoi_gian_du_tinh":5},
              {"buoc_so":2,"ten_hanh_dong":"Viết đoạn mở đầu","thoi_gian_du_tinh":20}
            ],"need":null}
        """.trimIndent())
        assertEquals(2, kq.cacBuoc.size)
        assertEquals("Mở tệp báo cáo", kq.cacBuoc[0].ten)
        assertEquals(20, kq.cacBuoc[1].phut)
        assertNull(kq.can)
    }

    // ----- Chan tan goc: khong bao gio qua nam buoc -----

    /**
     * Prompt gioi han 5 buoc, nhung prompt khong phai rang buoc.
     * Cho nay moi la thu chan that.
     */
    @Test fun nhieuHonNamBuoc_thiCatCung() {
        val mang = (1..12).joinToString(",") {
            """{"buoc_so":$it,"ten_hanh_dong":"Việc $it","thoi_gian_du_tinh":10}"""
        }
        val kq = PhanRa.doc("""{"steps":[$mang],"need":null}""")
        assertEquals(PhanRa.TOI_DA_BUOC, kq.cacBuoc.size)
        assertEquals("Việc 1", kq.cacBuoc[0].ten)
        assertEquals("Việc 5", kq.cacBuoc[4].ten)
    }

    // ----- Ba kieu mo hinh hay lam sai -----

    @Test fun bocTrongKhoiMa_vanDocDuoc() {
        val kq = PhanRa.doc(
            "```json\n{\"steps\":[{\"ten_hanh_dong\":\"Gọi cho Huy\",\"thoi_gian_du_tinh\":5}]}\n```")
        assertEquals(1, kq.cacBuoc.size)
        assertEquals("Gọi cho Huy", kq.cacBuoc[0].ten)
    }

    @Test fun coRaoDonQuanhJson_vanDocDuoc() {
        val kq = PhanRa.doc(
            "Đây là kết quả:\n{\"steps\":[{\"ten_hanh_dong\":\"In hồ sơ\"}]}\nChúc bạn làm tốt.")
        assertEquals(1, kq.cacBuoc.size)
        assertEquals("In hồ sơ", kq.cacBuoc[0].ten)
    }

    @Test fun buocKhongCoThoiGian_thiLayMacDinh() {
        val kq = PhanRa.doc("""{"steps":[{"ten_hanh_dong":"Xếp lại bàn"}]}""")
        assertEquals(10, kq.cacBuoc[0].phut)
    }

    // ----- Thoi gian: boi so cua 5, trong khoang 5..45 -----

    /**
     * Con so le lam danh sach trong nhu mot bang tinh. Boi so cua 5 doc
     * luot qua la uoc duoc tong - thu nguoi mu thoi gian can.
     */
    @Test fun thoiGianLuonLaBoiSoCuaNam() {
        assertEquals(5, PhanRa.lamTronPhut(3))
        assertEquals(5, PhanRa.lamTronPhut(5))
        assertEquals(10, PhanRa.lamTronPhut(8))
        assertEquals(35, PhanRa.lamTronPhut(37))
    }

    @Test fun thoiGianVoLy_biKeoVeTrongKhoang() {
        assertEquals(10, PhanRa.lamTronPhut(0))      // mo hinh bo trong
        assertEquals(10, PhanRa.lamTronPhut(-5))
        assertEquals(45, PhanRa.lamTronPhut(500))
        assertEquals(45, PhanRa.lamTronPhut(90))
    }

    // ----- Dong tu mo ho -----

    /**
     * Day chinh la nhom tu ma nguoi dang te liet KHONG hanh dong duoc:
     * "nghien cuu bao cao" khong noi cho biet mo cai gi ra truoc.
     *
     * Danh dau, KHONG chan: nguoi dung sua lai truoc khi duyet. Chan
     * han thi lai la app ap dat cach chia viec - dung cai rao can ma de
     * bai noi toi.
     */
    @Test fun dongTuMoHo_biDanhDau() {
        assertTrue(PhanRa.moHo("Nghiên cứu thị trường"))
        assertTrue(PhanRa.moHo("chuẩn bị tài liệu"))
        assertTrue(PhanRa.moHo("Research the topic"))
        assertTrue(PhanRa.moHo("Lên kế hoạch cho quý sau"))
    }

    @Test fun dongTuCuThe_khongBiDanhDau() {
        assertFalse(PhanRa.moHo("Mở tệp báo cáo và đọc lại tiêu đề"))
        assertFalse(PhanRa.moHo("Gọi cho Huy hỏi số liệu"))
        assertFalse(PhanRa.moHo("Open the file"))
        // "xem xet" o GIUA cau thi khong tinh - chi dong tu DAU cau moi
        // quyet dinh buoc do co lam duoc ngay khong.
        assertFalse(PhanRa.moHo("Gửi bản nháp để sếp xem xét"))
    }

    // ----- AI noi khong du thong tin -----

    /**
     * Khong co duong nay thi mo hinh luon bia ra nam buoc chung chung,
     * va nam buoc chung chung te hon khong co gi.
     */
    @Test fun khongDuThongTin_thiTraCauHoi_khongBiaBuoc() {
        val kq = PhanRa.doc("""{"steps":[],"need":"Báo cáo này nộp cho ai?"}""")
        assertTrue(kq.cacBuoc.isEmpty())
        assertEquals("Báo cáo này nộp cho ai?", kq.can)
    }

    // ----- Hong thi phai NEM, khong duoc im lang tra ve rong -----

    /**
     * Tra ve mot danh sach rong roi coi nhu thanh cong la kieu hong te
     * nhat: man hinh hien ra trong tron va nguoi dung khong biet vi sao.
     * Nem ngoai le thi man hinh hien duoc duong tu chia thu cong.
     */
    @Test fun jsonHong_thiNemNgoaiLe() {
        for (rac in listOf("", "không phải json", "{ thiếu ngoặc", "[]")) {
            try {
                PhanRa.doc(rac)
                throw AssertionError("phai nem voi dau vao: \"$rac\"")
            } catch (_: IllegalArgumentException) {
                // dung
            }
        }
    }

    @Test fun mangStepsRong_thiNemNgoaiLe() {
        try {
            PhanRa.doc("""{"steps":[],"need":null}""")
            throw AssertionError("phai nem")
        } catch (_: IllegalArgumentException) {
        }
    }

    @Test fun buocKhongCoTen_thiBiBoQua() {
        val kq = PhanRa.doc("""
            {"steps":[
              {"ten_hanh_dong":"","thoi_gian_du_tinh":5},
              {"ten_hanh_dong":"Gửi email","thoi_gian_du_tinh":5}
            ]}
        """.trimIndent())
        assertEquals(1, kq.cacBuoc.size)
        assertEquals("Gửi email", kq.cacBuoc[0].ten)
    }

    // ----- Han muc -----

    @Test fun banMauSinhRaKetQuaDocDuoc() {
        // `MauProvider` phai di qua dung `PhanRa.doc` nhu ban that, chu
        // khong duoc tra ve mot doi tuong dung san - khong thi no khong
        // con kiem chung duoc duong ma that.
        val kq = MauProvider().phanRa("viết báo cáo", null)
        assertTrue(kq.cacBuoc.isNotEmpty())
        assertTrue(kq.cacBuoc.size <= PhanRa.TOI_DA_BUOC)
        assertTrue("phai mang ten viec that", kq.cacBuoc[0].ten.contains("viết báo cáo"))
        assertNull(kq.can)
    }

    @Test fun soLuotMoiNgayLaBa() {
        assertEquals(3, PhanRa.LUOT_MOI_NGAY)
    }
}
