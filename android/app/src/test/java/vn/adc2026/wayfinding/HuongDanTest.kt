package vn.adc2026.wayfinding

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * ====================================================================
 * CANH GAC CHU HUONG DAN
 * ====================================================================
 *
 * Man hinh huong dan doc ra dung MOT lan trong doi mot nguoi dung, va
 * doc vao luc ho vua dang ky xong - tuc la luc kien nhan mong nhat va
 * chua co ly do nao de tin app.
 *
 * Neu chu o do dai ra, no se bi bo qua het. Va mot huong dan bi bo qua
 * thi khong khac gi khong co huong dan, nhung van ton mot man hinh chan
 * duong nguoi dung.
 *
 * Nen bon quy tac duoi day duoc khoa lai bang test. Ai them mot buoc
 * moi ma viet dai se bi chan ngay, chu khong phai doi toi luc co nguoi
 * doc thu.
 *
 * Doc THANG `strings.xml` nen soat duoc CA HAI ngon ngu - ban dich dai
 * ra cung la mot cach lam hong.
 */
class HuongDanTest {

    /** Tieu de: doc het trong mot cai liec. */
    private val TOI_DA_TIEU_DE = 34

    /** Noi dung: mot hai cau, doc het trong mot hoi tho. */
    private val TOI_DA_NOI_DUNG = 110

    private fun doc(thuMuc: String): Map<String, String> {
        val tep = File("src/main/res/$thuMuc/strings.xml")
        assertTrue("khong thay ${tep.path} - kiem lai thu muc chay test", tep.exists())
        val xml = tep.readText()
        return Regex("""<string name="(hd_[^"]+)">(.*?)</string>""", RegexOption.DOT_MATCHES_ALL)
            .findAll(xml).associate { it.groupValues[1] to it.groupValues[2] }
    }

    @Test
    fun tieuDeNgan() {
        var daSoat = 0
        for (tm in listOf("values", "values-en")) {
            for ((ten, chu) in doc(tm)) {
                if (!ten.endsWith("_td")) continue
                daSoat++
                assertTrue("$tm/$ten dai ${chu.length} ky tu, toi da $TOI_DA_TIEU_DE: \"$chu\"",
                    chu.length <= TOI_DA_TIEU_DE)
            }
        }
        assertTrue("khong soat duoc tieu de nao - mau doc sai?", daSoat >= 12)
    }

    @Test
    fun noiDungNgan() {
        var daSoat = 0
        for (tm in listOf("values", "values-en")) {
            for ((ten, chu) in doc(tm)) {
                if (!ten.endsWith("_nd")) continue
                daSoat++
                assertTrue("$tm/$ten dai ${chu.length} ky tu, toi da $TOI_DA_NOI_DUNG: \"$chu\"",
                    chu.length <= TOI_DA_NOI_DUNG)
            }
        }
        assertTrue("khong soat duoc noi dung nao - mau doc sai?", daSoat >= 12)
    }

    /**
     * Toi da hai cau.
     *
     * Ba cau tro len thi no khong con la mot chu thich - no thanh mot
     * doan van, va doan van tren mot lop phu toi la thu nguoi ta bam
     * "Bỏ qua" de thoat khoi.
     */
    @Test
    fun toiDaHaiCau() {
        for (tm in listOf("values", "values-en")) {
            for ((ten, chu) in doc(tm)) {
                if (!ten.endsWith("_nd")) continue
                val soCau = chu.count { it == '.' || it == '?' || it == '!' }
                assertTrue("$tm/$ten co $soCau cau, toi da 2: \"$chu\"", soCau <= 2)
            }
        }
    }

    /**
     * Khong ra lenh, khong trach.
     *
     * Cung bo quy tac voi loi nhan hang ngay (`LoiNhanNgayTest`). Huong
     * dan la cho DE nhat de vo tinh viet ra mot cau menh lenh, vi ban
     * chat no dang chi nguoi ta lam gi.
     */
    @Test
    fun khongCoCauRaLenh() {
        val cam = listOf(
            "bạn phải", "bạn nên", "cố lên", "hãy cố", "đừng quên", "nhớ phải",
            "you must", "you should", "don't forget", "make sure you", "be sure to",
        )
        for (tm in listOf("values", "values-en")) {
            for ((ten, chu) in doc(tm)) {
                val t = chu.lowercase()
                for (xau in cam) {
                    assertFalse("$tm/$ten chua cau ra lenh: \"$xau\"", xau in t)
                }
            }
        }
    }

    /**
     * Moi buoc trong chuoi chuan deu phai co ca tieu de lan noi dung.
     *
     * Bai nay bat truong hop them mot buoc vao `chuoiChuan()` ma quen
     * viet chuoi cho no - luc chay se hien ra mot the trong.
     */
    @Test
    fun moiBuocDeuCoDuHaiChuoi() {
        val vi = doc("values")
        val en = doc("values-en")
        val nhom = vi.keys.filter { it.endsWith("_td") }.map { it.removeSuffix("_td") }
        assertTrue("phai co it nhat sau nhom chu huong dan", nhom.size >= 6)
        for (n in nhom) {
            assertTrue("thieu ${n}_nd o ban tieng Viet", vi.containsKey("${n}_nd"))
            assertTrue("thieu ${n}_td o ban tieng Anh", en.containsKey("${n}_td"))
            assertTrue("thieu ${n}_nd o ban tieng Anh", en.containsKey("${n}_nd"))
        }
    }
}
