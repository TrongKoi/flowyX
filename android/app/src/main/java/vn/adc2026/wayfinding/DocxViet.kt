package vn.adc2026.wayfinding

import java.io.ByteArrayOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * XUAT WORD (.docx) - tu viet OOXML, KHONG thu vien.
 *
 * `.docx` la tep ZIP chua vai tep XML. Sinh moi tu du lieu co cau truc la
 * phan de nhat cua dinh dang: khoang 200 dong, doi lai du an van khong keo
 * them phu thuoc nao (Apache POI nang ~10 MB va can androidx). Cung cach voi
 * `meety/exporters/docx.py`.
 *
 * Hai HO SO trinh bay, chon luc xuat:
 *
 * TIEU_CHUAN - van ban hanh chinh: Times New Roman 13pt, gian dong 1.15,
 *   theo Nghi dinh 30/2020/ND-CP. Dung khi gui cho nguoi khac luu ho so.
 *
 * DE_DOC - cho nguoi kho doc (dyslexia), theo British Dyslexia Association
 *   Style Guide 2023:
 *     - Verdana 13pt: khong chan, chu rong, phan biet ro b/d, I/l/1; co san
 *       tren Windows va macOS va co du dau tieng Viet. (Lexend dep hon nhung
 *       Word cua nguoi nhan thuong KHONG co - roi ve Times New Roman la hong
 *       ca muc dich.)
 *     - Gian dong 1.5, cach doan 12pt, gian chu 0.5pt.
 *     - Can TRAI, khong can deu hai ben: can deu tao "song trang" giua cac tu.
 *     - KHONG in nghieng, KHONG gach chan - nhan manh bang chu dam.
 *     - Nen kem #FFF8E7, chu navy #1F1E2E thay vi den tren trang tinh.
 *     - Cau dai tu tach thanh gach dau dong (moi dong mot y).
 *     - Khoi "noi bat" to nen vang nhat + vien trai: mat tim thay ngay.
 */
object DocxViet {

    enum class HoSo { TIEU_CHUAN, DE_DOC }

    sealed class Khoi {
        data class TieuDe(val chu: String) : Khoi()
        data class Muc(val chu: String) : Khoi()
        data class Doan(val chu: String) : Khoi()
        data class GachDau(val chu: String) : Khoi()
        /** Khoi noi bat: nhan dam + noi dung. Ban DE_DOC to nen. */
        data class NoiBat(val nhan: String, val dong: List<String>) : Khoi()
        data class ChuNho(val chu: String) : Khoi()
    }

    /** Cau dai hon nguong nay trong ban DE_DOC se bi tach thanh nhieu gach dau dong. */
    const val CAU_DAI = 110

    fun tao(tieuDe: String, khoi: List<Khoi>, hoSo: HoSo): ByteArray {
        val than = StringBuilder()
        for (k in khoi) than.append(xml(k, hoSo))
        val nen = if (hoSo == HoSo.DE_DOC) "<w:background w:color=\"FFF8E7\"/>" else ""
        val document = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="$W">$nen<w:body>$than<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1418" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr></w:body></w:document>"""

        val ra = ByteArrayOutputStream()
        ZipOutputStream(ra).use { z ->
            fun tep(ten: String, noiDung: String) {
                z.putNextEntry(ZipEntry(ten))
                z.write(noiDung.toByteArray(Charsets.UTF_8))
                z.closeEntry()
            }
            tep("[Content_Types].xml", CONTENT_TYPES)
            tep("_rels/.rels", ROOT_RELS)
            tep("word/_rels/document.xml.rels", DOC_RELS)
            tep("word/document.xml", document)
            tep("word/styles.xml", styles(hoSo))
            tep("word/settings.xml", SETTINGS)
            tep("docProps/core.xml", core(tieuDe))
            tep("docProps/app.xml", APP)
        }
        return ra.toByteArray()
    }

    /**
     * Tach cau dai thanh cac y ngan. Tach o dau cham / cham phay / cham than
     * / hoi; khong tach duoc thi giu nguyen. Chi dung cho ban DE_DOC.
     */
    fun tachY(chu: String): List<String> {
        val t = chu.trim()
        if (t.length <= CAU_DAI) return listOf(t)
        val y = t.split(Regex("(?<=[.;!?])\\s+")).map { it.trim() }.filter { it.isNotEmpty() }
        return if (y.size > 1) y else listOf(t)
    }

    // ---------------------------------------------------------------

    private fun xml(k: Khoi, hs: HoSo): String = when (k) {
        is Khoi.TieuDe -> doan(chay(k.chu), kieu = "Title")
        is Khoi.Muc -> doan(chay(k.chu), kieu = "Heading1")
        is Khoi.Doan ->
            if (hs == HoSo.DE_DOC) tachY(k.chu).let { y ->
                if (y.size == 1) doan(chay(y[0])) else y.joinToString("") { gachDau(it) }
            } else doan(chay(k.chu))
        is Khoi.GachDau ->
            if (hs == HoSo.DE_DOC) tachY(k.chu).joinToString("") { gachDau(it) }
            else gachDau(k.chu)
        is Khoi.ChuNho -> doan(chay(k.chu, mau = "5A566E", co = if (hs == HoSo.DE_DOC) 22 else 22))
        is Khoi.NoiBat -> {
            val tren = if (hs == HoSo.DE_DOC)
                "<w:shd w:val=\"clear\" w:color=\"auto\" w:fill=\"FFF1C2\"/>" +
                    "<w:pBdr><w:left w:val=\"single\" w:sz=\"24\" w:space=\"8\" w:color=\"F58A07\"/></w:pBdr>"
            else ""
            val sb = StringBuilder()
            sb.append(doan(chay(k.nhan, dam = true), them = tren))
            for (d in k.dong) sb.append(doan(chay("•  $d"), them = tren))
            sb.toString()
        }
    }

    private fun gachDau(chu: String) =
        doan(chay("•  $chu"), them = "<w:ind w:left=\"426\" w:hanging=\"284\"/>")

    private fun doan(runs: String, kieu: String? = null, them: String = ""): String {
        val pPr = (if (kieu != null) "<w:pStyle w:val=\"$kieu\"/>" else "") + them
        return "<w:p>" + (if (pPr.isNotEmpty()) "<w:pPr>$pPr</w:pPr>" else "") + runs + "</w:p>"
    }

    private fun chay(chu: String, dam: Boolean = false, mau: String? = null, co: Int? = null): String {
        val rPr = (if (dam) "<w:b/>" else "") +
            (if (mau != null) "<w:color w:val=\"$mau\"/>" else "") +
            (if (co != null) "<w:sz w:val=\"$co\"/><w:szCs w:val=\"$co\"/>" else "")
        // Xuong dong trong mot doan: tach thanh <w:br/>.
        val phan = chu.split("\n").joinToString("<w:br/>") {
            "<w:t xml:space=\"preserve\">${esc(it)}</w:t>"
        }
        return "<w:r>" + (if (rPr.isNotEmpty()) "<w:rPr>$rPr</w:rPr>" else "") + phan + "</w:r>"
    }

    /** Thoat XML, va bo ky tu dieu khien XML 1.0 khong cho phep (lam Word bao tep hong). */
    fun esc(s: String): String {
        val sb = StringBuilder(s.length)
        for (c in s) {
            when {
                c == '&' -> sb.append("&amp;")
                c == '<' -> sb.append("&lt;")
                c == '>' -> sb.append("&gt;")
                c == '"' -> sb.append("&quot;")
                c < ' ' && c != '\t' && c != '\n' && c != '\r' -> Unit
                else -> sb.append(c)
            }
        }
        return sb.toString()
    }

    private fun styles(hs: HoSo): String {
        val de = hs == HoSo.DE_DOC
        val font = if (de) "Verdana" else "Times New Roman"
        val co = 26                                  // 13pt, tinh bang nua point
        val mauChu = if (de) "1F1E2E" else "000000"
        // line: 240 = don. 276 = 1.15, 360 = 1.5
        val dong = if (de) 360 else 276
        val sau = if (de) 240 else 120
        val gianChu = if (de) "<w:spacing w:val=\"10\"/>" else ""
        val canDeu = if (de) "left" else "both"
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="$W">
<w:docDefaults><w:rPrDefault><w:rPr>
<w:rFonts w:ascii="$font" w:hAnsi="$font" w:cs="$font" w:eastAsia="$font"/>
<w:color w:val="$mauChu"/>$gianChu<w:sz w:val="$co"/><w:szCs w:val="$co"/><w:lang w:val="vi-VN"/>
</w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="$sau" w:line="$dong" w:lineRule="auto"/><w:jc w:val="$canDeu"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/>
<w:pPr><w:jc w:val="${if (de) "left" else "center"}"/><w:spacing w:before="120" w:after="${if (de) 360 else 200}"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="${if (de) 36 else 32}"/><w:szCs w:val="${if (de) 36 else 32}"/>${if (de) "" else "<w:caps/>"}</w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>
<w:pPr><w:keepNext/><w:spacing w:before="${if (de) 360 else 240}" w:after="120"/><w:jc w:val="left"/><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="${if (de) 32 else 28}"/><w:szCs w:val="${if (de) 32 else 28}"/></w:rPr></w:style>
</w:styles>"""
    }

    private fun core(tieuDe: String) = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>${esc(tieuDe)}</dc:title><dc:creator>FlowyX</dc:creator></cp:coreProperties>"""

    private const val W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

    private const val CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>"""

    private const val ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>"""

    private const val DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/></Relationships>"""

    /** displayBackgroundShape: KHONG co dong nay thi Word an mau nen trang. */
    private const val SETTINGS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:displayBackgroundShape/><w:defaultTabStop w:val="720"/><w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat></w:settings>"""

    private const val APP = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>FlowyX</Application></Properties>"""

    const val MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}
