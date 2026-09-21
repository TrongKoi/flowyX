package vn.adc2026.wayfinding

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.ByteArrayInputStream
import java.util.Calendar
import java.util.zip.ZipInputStream

/**
 * Test cho logic v4 (17/09): lap theo thu, uu tien, nhac tuy y, dong ho
 * dem nguoc, loi nhan theo ngay, diem danh, xuat Word.
 */
class LichV4Test {
    private val thuHai = Lich.tuNgayThang(2026, 9, 14)

    @Test fun ngay14_09_2026_la_thu_hai() = assertEquals(0, Lich.thu(thuHai))

    @Test fun lapTheoThu_chiRoiDungThuDaChon() {
        val kh = KeHoach("a", "Tập", ngay = thuHai, batDau = 600, lapLai = LapLai.THEO_THU, thuLap = setOf(0, 3))
        assertTrue(Lich.coTrongNgay(kh, thuHai))
        assertFalse(Lich.coTrongNgay(kh, thuHai + 1))
        assertTrue(Lich.coTrongNgay(kh, thuHai + 3))
        assertTrue(Lich.coTrongNgay(kh, thuHai + 10))
        assertFalse("khong roi vao TRUOC ngay bat dau", Lich.coTrongNgay(kh, thuHai - 7))
    }

    @Test fun lapTheoThu_rongThiLayThuCuaNgayBatDau() {
        val kh = KeHoach("a", "Tập", ngay = thuHai, batDau = 600, lapLai = LapLai.THEO_THU)
        assertTrue(Lich.coTrongNgay(kh, thuHai + 7))
        assertFalse(Lich.coTrongNgay(kh, thuHai + 1))
    }

    /**
     * Ban truoc kiem thang chuoi "T2, T5 hằng tuần". Tu khi `moTaLapLai`
     * lay chuoi tu `strings.xml` thi no can Context, va Context khong co
     * trong test JVM. Phan DANG KIEM - gom thu, va gom du bay thu thanh
     * "hằng ngày" - da duoc tach ra thanh `lapLaiThuan`, thuan tuy va
     * khong dinh Android. Phan con lai chi la thay so vao mau.
     */
    @Test fun lapLaiThuan_gomThuVaGomDuBayThanhHangNgay() {
        val kh = KeHoach("a", "Tập", ngay = thuHai, batDau = 600, lapLai = LapLai.THEO_THU, thuLap = setOf(3, 0))
        assertEquals(Lich.MoTaLap.TheoThu(listOf(0, 3)), Lich.lapLaiThuan(kh))
        assertEquals(Lich.MoTaLap.HangNgay, Lich.lapLaiThuan(kh.copy(thuLap = (0..6).toSet())))
    }

    /** Thu rong -> lay thu cua chinh ngay bat dau, khong phai bo trong. */
    @Test fun lapLaiThuan_thuRongThiLayThuCuaNgayBatDau() {
        val kh = KeHoach("a", "Tập", ngay = thuHai, batDau = 600, lapLai = LapLai.THEO_THU)
        assertEquals(Lich.MoTaLap.TheoThu(listOf(0)), Lich.lapLaiThuan(kh))
    }

    @Test fun nhacTruocBaNgay_vanDuocDatChuong() {
        val xa = KeHoach("b", "Nộp hồ sơ", ngay = thuHai + 5, batDau = 540, nhacTruoc = listOf(3 * 1440))
        val ln = Lich.lanNhacToi(listOf(xa), thuHai * 1440 + 480, soNgay = 8)
        assertEquals(1, ln.size)
        assertEquals((thuHai + 2) * 1440 + 540, ln[0].phutTuyetDoi)
    }

    /**
     * MUC 4.3 - thoi luong hien MOT don vi, khong phai hai.
     *
     * Day la bai canh gac cho quy tac do: duoi ba tieng phai tra ve
     * `0 to phut`, nghia la "hien nguyen bang phut". Ai ha nguong xuong
     * 60 lai - va app quay ve "1 giờ 15 phút" - se lam bai nay do.
     */
    @Test fun chiaHienThi_duoiBaTiengThiGiuNguyenBangPhut() {
        assertEquals(0 to 45, Lich.chiaHienThi(45))
        assertEquals(0 to 75, Lich.chiaHienThi(75))     // KHONG phai 1 gio 15
        assertEquals(0 to 120, Lich.chiaHienThi(120))
        assertEquals(0 to 179, Lich.chiaHienThi(179))
    }

    /** Tu ba tieng tro len thi con so phut het truc quan -> quay ve gio. */
    @Test fun chiaHienThi_tuBaTiengThiTachGioVaPhut() {
        assertEquals(3 to 0, Lich.chiaHienThi(180))
        assertEquals(3 to 5, Lich.chiaHienThi(185))
        assertEquals(4 to 0, Lich.chiaHienThi(240))
    }

    @Test fun thoiLuongGiua_quaNuaDem() {
        assertEquals(75, Lich.thoiLuongGiua(540, 615))
        assertEquals(120, Lich.thoiLuongGiua(23 * 60, 60))
        assertEquals("bang nhau = ca ngay, khong phai 0", 1440, Lich.thoiLuongGiua(600, 600))
    }

    @Test fun theoUuTien_caoTruocRoiTheoGio() {
        val g = KeHoach("x", "x", ngay = thuHai, batDau = 600)
        val ds = listOf(g.copy(id = "1", uuTien = UuTien.THAP, batDau = 480),
            g.copy(id = "2", uuTien = UuTien.CAO, batDau = 1200),
            g.copy(id = "3", uuTien = UuTien.VUA), g.copy(id = "4", uuTien = UuTien.CAO, batDau = 300))
        assertEquals(listOf("4", "2", "3", "1"), Lich.theoUuTien(ds).map { it.id })
    }
}

class DemNguocTest {
    @Test fun tranHaiGio() = assertEquals(120 * 60_000L, DemNguoc().datThoiLuong(500).tongMs)
    @Test fun itNhatMotPhut() = assertEquals(60_000L, DemNguoc().datThoiLuong(0).tongMs)

    @Test fun chayTamDungTiepTuc_giuDungPhanConLai() {
        var d = DemNguoc().datThoiLuong(25).batDau(1_000)
        assertEquals(24 * 60_000L, d.conLaiMs(61_000))
        d = d.tamDung(61_000)
        assertEquals("dung thi dong ho khong chay", 24 * 60_000L, d.conLaiMs(9_999_999))
        d = d.batDau(100_000)
        assertEquals(24 * 60_000L, d.conLaiMs(100_000))
    }

    @Test fun themPhut_khongVuotHaiGio() {
        val d = DemNguoc().datThoiLuong(100).batDau(0).themPhut(60, 0)
        assertEquals(120 * 60_000L, d.conLaiMs(0))
    }

    @Test fun khongDoiThoiLuongKhiDangChay() {
        val d = DemNguoc().datThoiLuong(25).batDau(0)
        assertEquals(d, d.datThoiLuong(5))
    }

    @Test fun hetGio() {
        val d = DemNguoc().datThoiLuong(1).batDau(0)
        assertFalse(d.daHet(59_999)); assertTrue(d.daHet(60_000))
    }

    @Test fun dinhDang_lamTronLen() {
        assertEquals("25:00", DemNguoc.dinhDang(25 * 60_000L))
        assertEquals("00:01", DemNguoc.dinhDang(1))
        assertEquals("1:30:00", DemNguoc.dinhDang(90 * 60_000L))
    }
}

class LoiNhanNgayTest {
    @Test fun khongBaoGioTrungHomQua() {
        for (n in 19_000L..21_000L) assertNotEquals(LoiNhanNgay.cua(n), LoiNhanNgay.cua(n + 1))
    }
    @Test fun bamMotNgayMoiCauDeuXuatHien() =
        assertEquals(LoiNhanNgay.CAU.size, (0L until LoiNhanNgay.CAU.size).map { LoiNhanNgay.cua(it) }.toSet().size)
    /**
     * ================================================================
     * BAI CANH GAC CAU CHU - doc thang tu strings.xml
     * ================================================================
     *
     * Ban truoc duyet `LoiNhanNgay.CAU` va goi `.lowercase()` tren tung
     * phan tu, vi luc do `CAU` la `List<String>`. Dot localization
     * 20-21/09 doi no thanh `List<Int>` (ma so tai nguyen) - dung huong,
     * nhung bai canh gac mat cho bam: khong con doc duoc cau nao ca.
     *
     * Neu chi sua cho no bien dich duoc - vi du bo han bai nay - thi tu
     * gio ai cung co the them "bạn phải cố lên!" vao strings.xml ma
     * khong gi chan lai. Dung thu quy tac nay sinh ra de chan.
     *
     * Nen bai kiem doc THANG tep strings.xml. Doi lai, no manh hon ban
     * cu: no soat CA HAI ngon ngu, trong khi ban cu chi soat tieng Viet.
     */
    @Test fun khongCoCauRaLenh() {
        val cam = listOf(
            // tieng Viet
            "bạn phải", "bạn nên", "cố lên", "đừng lười", "hãy cố",
            // tieng Anh
            "you must", "you should", "you need to", "just do it", "cheer up",
        )
        var daSoat = 0
        for (thuMuc in listOf("values", "values-en")) {
            val tep = java.io.File("src/main/res/$thuMuc/strings.xml")
            assertTrue("khong thay ${tep.path} - kiem lai thu muc chay test", tep.exists())
            val xml = tep.readText()
            for (m in Regex("""<string name="(motd_[^"]+)">(.*?)</string>""",
                            RegexOption.DOT_MATCHES_ALL).findAll(xml)) {
                val ten = m.groupValues[1]
                val cau = m.groupValues[2].lowercase()
                daSoat++
                for (xau in cam) {
                    assertFalse("$thuMuc/$ten chua cau ra lenh: \"$xau\"", xau in cau)
                }
            }
        }
        // Khong tim thay cau nao nghia la mau doc sai, chu khong phai "sach".
        assertEquals(LoiNhanNgay.CAU.size * 2, daSoat)
    }
}

class DiemDanhTest {
    private fun ngay(d: Int) = Calendar.getInstance().apply { clear(); set(2026, 8, d) }

    @Test fun chiMoAppCungTinhVaoChuoi() {
        val so = SoTienDo()
        so.diemDanh("2026-09-15"); so.diemDanh("2026-09-16")
        assertEquals(2, so.chuoi(ngay(16)))
        assertEquals("diem danh khong phai la xong viec", 0, so.tongSoViec())
    }
    @Test fun diemDanhHaiLanMotNgay_chiTinhMot() {
        val so = SoTienDo()
        assertTrue(so.diemDanh("2026-09-16")); assertFalse(so.diemDanh("2026-09-16"))
    }
    @Test fun tuanDanhDauNgayChiMoApp() {
        val so = SoTienDo(); so.diemDanh("2026-09-16")
        assertTrue(so.tuan(ngay(16)).last().second)
    }
}

class DocxVietTest {
    private fun tep(b: ByteArray): Map<String, String> {
        val ra = mutableMapOf<String, String>()
        ZipInputStream(ByteArrayInputStream(b)).use { z ->
            while (true) { val e = z.nextEntry ?: break; ra[e.name] = z.readBytes().toString(Charsets.UTF_8) }
        }
        return ra
    }
    private val khoi = listOf(DocxViet.Khoi.TieuDe("Họp <nhóm> & chốt"),
        DocxViet.Khoi.Doan("Câu một khá dài để vượt ngưỡng tách ý của bản dễ đọc, có đủ chữ. Câu hai cũng dài vừa phải để thành một gạch riêng biệt nữa."))

    @Test fun duCacTepBatBuoc() {
        val t = tep(DocxViet.tao("x", khoi, DocxViet.HoSo.TIEU_CHUAN))
        for (n in listOf("[Content_Types].xml", "_rels/.rels", "word/document.xml", "word/styles.xml", "word/_rels/document.xml.rels"))
            assertTrue(n, n in t)
    }
    @Test fun thoatKyTuXml() {
        val doc = tep(DocxViet.tao("x", khoi, DocxViet.HoSo.TIEU_CHUAN))["word/document.xml"]!!
        assertTrue(doc.contains("Họp &lt;nhóm&gt; &amp; chốt"))
    }
    @Test fun banDeDoc_verdanaGianDongNenKemCanTrai() {
        val t = tep(DocxViet.tao("x", khoi, DocxViet.HoSo.DE_DOC))
        val st = t["word/styles.xml"]!!
        assertTrue(st.contains("Verdana")); assertTrue(st.contains("w:line=\"360\""))
        assertTrue(st.contains("<w:jc w:val=\"left\"/>")); assertFalse(st.contains("<w:i/>"))
        assertTrue(t["word/document.xml"]!!.contains("FFF8E7"))
        assertTrue(t["word/settings.xml"]!!.contains("displayBackgroundShape"))
    }
    @Test fun banDeDoc_tachCauDaiThanhGachDau() {
        assertEquals(2, DocxViet.tachY((khoi[1] as DocxViet.Khoi.Doan).chu).size)
        assertEquals(1, DocxViet.tachY("Ngắn.").size)
    }
    @Test fun boKyTuDieuKhienLamHongTep() = assertEquals("ab", DocxViet.esc("a\u0001b"))
}
