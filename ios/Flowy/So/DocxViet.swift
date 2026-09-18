import Foundation

/// XUAT WORD (.docx) - khop Android `DocxViet.kt`, cung hai ho so:
///   .tieuChuan - Times New Roman 13pt, gian dong 1.15 (ND 30/2020)
///   .deDoc     - Verdana 13pt, gian dong 1.5, can trai, nen kem, khong
///                nghieng, cau dai tach gach dau dong (BDA Style Guide 2023)
///
/// iOS khong co API tao ZIP cong khai, nen tu viet ZIP "stored" (khong nen)
/// + CRC32. Tai lieu chi vai KB chu - khong nen khong dang ke.
enum DocxViet {
    enum HoSo { case tieuChuan, deDoc }

    enum Khoi {
        case tieuDe(String)
        case muc(String)
        case doan(String)
        case gachDau(String)
        case noiBat(String, [String])
        case chuNho(String)
    }

    static let cauDai = 110
    static let mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    static func tao(tieuDe: String, khoi: [Khoi], hoSo: HoSo) -> Data {
        let than = khoi.map { xml($0, hoSo) }.joined()
        let nen = hoSo == .deDoc ? "<w:background w:color=\"FFF8E7\"/>" : ""
        let doc = """
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="\(w)">\(nen)<w:body>\(than)<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1418" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr></w:body></w:document>
        """
        var z = ZipGhi()
        z.them("[Content_Types].xml", contentTypes)
        z.them("_rels/.rels", rootRels)
        z.them("word/_rels/document.xml.rels", docRels)
        z.them("word/document.xml", doc)
        z.them("word/styles.xml", styles(hoSo))
        z.them("word/settings.xml", settings)
        z.them("docProps/core.xml", """
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>\(esc(tieuDe))</dc:title><dc:creator>FlowyX</dc:creator></cp:coreProperties>
        """)
        return z.xong()
    }

    static func tachY(_ chu: String) -> [String] {
        let t = chu.trimmingCharacters(in: .whitespacesAndNewlines)
        guard t.count > cauDai else { return t.isEmpty ? [] : [t] }
        var ra: [String] = []
        var hienTai = ""
        let cs = Array(t)
        for (i, c) in cs.enumerated() {
            hienTai.append(c)
            if ".;!?".contains(c), i + 1 < cs.count, cs[i + 1] == " " {
                ra.append(hienTai.trimmingCharacters(in: .whitespaces)); hienTai = ""
            }
        }
        let cuoi = hienTai.trimmingCharacters(in: .whitespaces)
        if !cuoi.isEmpty { ra.append(cuoi) }
        return ra.count > 1 ? ra : [t]
    }

    static func esc(_ s: String) -> String {
        var r = ""
        for u in s.unicodeScalars {
            switch u {
            case "&": r += "&amp;"
            case "<": r += "&lt;"
            case ">": r += "&gt;"
            case "\"": r += "&quot;"
            default:
                if u.value < 0x20 && u != "\t" && u != "\n" && u != "\r" { continue }
                r.unicodeScalars.append(u)
            }
        }
        return r
    }

    // MARK: - XML

    private static let w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

    private static func xml(_ k: Khoi, _ hs: HoSo) -> String {
        switch k {
        case .tieuDe(let c): return doan(chay(c), kieu: "Title")
        case .muc(let c): return doan(chay(c), kieu: "Heading1")
        case .doan(let c):
            if hs == .deDoc {
                let y = tachY(c)
                return y.count == 1 ? doan(chay(y[0])) : y.map(gachDau).joined()
            }
            return doan(chay(c))
        case .gachDau(let c):
            return hs == .deDoc ? tachY(c).map(gachDau).joined() : gachDau(c)
        case .chuNho(let c): return doan(chay(c, mau: "5A566E", co: 22))
        case .noiBat(let nhan, let dong):
            let tren = hs == .deDoc
                ? "<w:shd w:val=\"clear\" w:color=\"auto\" w:fill=\"FFF1C2\"/><w:pBdr><w:left w:val=\"single\" w:sz=\"24\" w:space=\"8\" w:color=\"F58A07\"/></w:pBdr>"
                : ""
            return doan(chay(nhan, dam: true), them: tren) + dong.map { doan(chay("•  \($0)"), them: tren) }.joined()
        }
    }

    private static func gachDau(_ c: String) -> String {
        doan(chay("•  \(c)"), them: "<w:ind w:left=\"426\" w:hanging=\"284\"/>")
    }

    private static func doan(_ runs: String, kieu: String? = nil, them: String = "") -> String {
        let ppr = (kieu.map { "<w:pStyle w:val=\"\($0)\"/>" } ?? "") + them
        return "<w:p>" + (ppr.isEmpty ? "" : "<w:pPr>\(ppr)</w:pPr>") + runs + "</w:p>"
    }

    private static func chay(_ c: String, dam: Bool = false, mau: String? = nil, co: Int? = nil) -> String {
        let rpr = (dam ? "<w:b/>" : "") + (mau.map { "<w:color w:val=\"\($0)\"/>" } ?? "")
            + (co.map { "<w:sz w:val=\"\($0)\"/><w:szCs w:val=\"\($0)\"/>" } ?? "")
        let phan = c.components(separatedBy: "\n")
            .map { "<w:t xml:space=\"preserve\">\(esc($0))</w:t>" }.joined(separator: "<w:br/>")
        return "<w:r>" + (rpr.isEmpty ? "" : "<w:rPr>\(rpr)</w:rPr>") + phan + "</w:r>"
    }

    private static func styles(_ hs: HoSo) -> String {
        let de = hs == .deDoc
        let font = de ? "Verdana" : "Times New Roman"
        return """
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:styles xmlns:w="\(w)"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="\(font)" w:hAnsi="\(font)" w:cs="\(font)" w:eastAsia="\(font)"/><w:color w:val="\(de ? "1F1E2E" : "000000")"/>\(de ? "<w:spacing w:val=\"10\"/>" : "")<w:sz w:val="26"/><w:szCs w:val="26"/><w:lang w:val="vi-VN"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="\(de ? 240 : 120)" w:line="\(de ? 360 : 276)" w:lineRule="auto"/><w:jc w:val="\(de ? "left" : "both")"/></w:pPr></w:pPrDefault></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style><w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:jc w:val="\(de ? "left" : "center")"/><w:spacing w:before="120" w:after="\(de ? 360 : 200)"/></w:pPr><w:rPr><w:b/><w:sz w:val="\(de ? 36 : 32)"/><w:szCs w:val="\(de ? 36 : 32)"/>\(de ? "" : "<w:caps/>")</w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="\(de ? 360 : 240)" w:after="120"/><w:jc w:val="left"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="\(de ? 32 : 28)"/><w:szCs w:val="\(de ? 32 : 28)"/></w:rPr></w:style></w:styles>
        """
    }

    private static let contentTypes = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>
    """
    private static let rootRels = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>
    """
    private static let docRels = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/></Relationships>
    """
    private static let settings = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:displayBackgroundShape/><w:defaultTabStop w:val="720"/></w:settings>
    """
}

/// ZIP toi gian: phuong thuc "stored" (0), CRC32, central directory.
/// Du cho Word/Pages/LibreOffice/Google Docs mo.
struct ZipGhi {
    private var du = Data()
    private var trungTam = Data()
    private var soMuc: UInt16 = 0

    private static let bangCrc: [UInt32] = (0..<256).map { i -> UInt32 in
        var c = UInt32(i)
        for _ in 0..<8 { c = (c & 1) != 0 ? 0xEDB88320 ^ (c >> 1) : c >> 1 }
        return c
    }

    static func crc32(_ d: Data) -> UInt32 {
        var c: UInt32 = 0xFFFFFFFF
        for b in d { c = bangCrc[Int((c ^ UInt32(b)) & 0xFF)] ^ (c >> 8) }
        return c ^ 0xFFFFFFFF
    }

    mutating func them(_ ten: String, _ chu: String) {
        let noiDung = Data(chu.utf8)
        let tenB = Data(ten.utf8)
        let crc = Self.crc32(noiDung)
        let viTri = UInt32(du.count)
        var h = Data()
        h.u32(0x04034B50); h.u16(20); h.u16(0x0800); h.u16(0); h.u16(0); h.u16(0x21)
        h.u32(crc); h.u32(UInt32(noiDung.count)); h.u32(UInt32(noiDung.count))
        h.u16(UInt16(tenB.count)); h.u16(0)
        du.append(h); du.append(tenB); du.append(noiDung)

        var t = Data()
        t.u32(0x02014B50); t.u16(20); t.u16(20); t.u16(0x0800); t.u16(0); t.u16(0); t.u16(0x21)
        t.u32(crc); t.u32(UInt32(noiDung.count)); t.u32(UInt32(noiDung.count))
        t.u16(UInt16(tenB.count)); t.u16(0); t.u16(0); t.u16(0); t.u16(0); t.u32(0); t.u32(viTri)
        trungTam.append(t); trungTam.append(tenB)
        soMuc += 1
    }

    mutating func xong() -> Data {
        var r = du
        let dauTT = UInt32(r.count)
        r.append(trungTam)
        var e = Data()
        e.u32(0x06054B50); e.u16(0); e.u16(0); e.u16(soMuc); e.u16(soMuc)
        e.u32(UInt32(trungTam.count)); e.u32(dauTT); e.u16(0)
        r.append(e)
        return r
    }
}

private extension Data {
    mutating func u16(_ v: UInt16) { var x = v.littleEndian; Swift.withUnsafeBytes(of: &x) { append(contentsOf: $0) } }
    mutating func u32(_ v: UInt32) { var x = v.littleEndian; Swift.withUnsafeBytes(of: &x) { append(contentsOf: $0) } }
}
