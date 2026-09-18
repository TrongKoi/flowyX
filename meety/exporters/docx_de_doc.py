"""Xuất biên bản ra Word bản DỄ ĐỌC — cho người khó đọc (dyslexia) và người ADHD.

Đi cùng ``exporters/docx.py`` (bản tiêu chuẩn theo Nghị định 30). Hai bản dùng
CÙNG dữ liệu ``StructuredMinutes``, khác nhau ở cách trình bày và thứ tự.

Quy chuẩn trình bày (British Dyslexia Association, Dyslexia Style Guide 2023)
-----------------------------------------------------------------------------
- Phông không chân **Verdana 13pt**: chữ rộng, b/d/p/q và I/l/1 tách bạch; có
  sẵn trên Windows/macOS và đủ dấu tiếng Việt. Không dùng Lexend: Word của
  người nhận thường không có, rơi về Times New Roman là hỏng cả mục đích.
- Giãn dòng **1,5**, cách đoạn 12pt, giãn chữ 0,5pt.
- **Căn trái**, không căn đều hai bên (tạo "sông trắng" giữa các chữ).
- **Không in nghiêng, không gạch chân, không viết HOA cả câu.** Nhấn mạnh
  bằng chữ đậm.
- **Nền kem** ``#FFF8E7`` với chữ navy ``#1F1E2E`` — giảm chói so với đen trên
  trắng tinh.
- **Không bảng nhiều cột**: mắt phải nhảy ngang giữa các ô. Mỗi việc là một
  khối dọc: tên việc (đậm), rồi "Ai · Hạn" ở dòng dưới.
- **Câu ngắn**: câu dài hơn 110 ký tự tự tách thành gạch đầu dòng.
- **Khối nổi bật** tô nền vàng nhạt + viền trái cam cho "Tóm tắt" và "Việc
  cần làm" — thứ người đọc cần tìm thấy đầu tiên.

Thứ tự nội dung — việc cần LÀM trước, điều đã NÓI sau
-----------------------------------------------------
Bản tiêu chuẩn đi theo trình tự hành chính (thành phần → tóm tắt → quyết
định → phân công). Người khó đọc thường chỉ đọc đoạn đầu, nên bản này đưa
lên trước: Tóm tắt → Việc cần làm → Đã chốt → Câu hỏi còn mở → Rủi ro →
Người dự. Quyết định đã bị thay thế KHÔNG xuất hiện (bản tiêu chuẩn vẫn giữ
để truy vết).
"""

from __future__ import annotations

import re
import zipfile
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

__all__ = ["build_docx_de_doc", "tach_y", "CAU_DAI"]

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CAU_DAI = 110
NEN = "FFF8E7"
NHAN_NEN = "FFF1C2"
NHAN_VIEN = "F58A07"

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _esc(t: Any) -> str:
    return escape(_CONTROL.sub("", str(t if t is not None else "")))


def tach_y(text: str) -> list[str]:
    """Tách câu dài thành các ý ngắn ở dấu . ; ! ? — không tách được thì giữ."""
    t = (text or "").strip()
    if len(t) <= CAU_DAI:
        return [t] if t else []
    parts = [p.strip() for p in re.split(r"(?<=[.;!?])\s+", t) if p.strip()]
    return parts if len(parts) > 1 else [t]


def _run(text: str, *, bold: bool = False, color: str | None = None, size: int | None = None) -> str:
    rpr = ("<w:b/>" if bold else "") + (f'<w:color w:val="{color}"/>' if color else "") + \
          (f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>' if size else "")
    rpr = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{_esc(text)}</w:t></w:r>'


def _p(runs: str, *, style: str | None = None, extra: str = "") -> str:
    ppr = (f'<w:pStyle w:val="{style}"/>' if style else "") + extra
    return f"<w:p>{'<w:pPr>' + ppr + '</w:pPr>' if ppr else ''}{runs}</w:p>"


_HL = (f'<w:shd w:val="clear" w:color="auto" w:fill="{NHAN_NEN}"/>'
       f'<w:pBdr><w:left w:val="single" w:sz="24" w:space="8" w:color="{NHAN_VIEN}"/></w:pBdr>')
_IND = '<w:ind w:left="426" w:hanging="284"/>'


def _bullets(text: str, *, highlight: bool = False) -> list[str]:
    return [_p(_run("•  " + y), extra=(_HL if highlight else "") + _IND) for y in tach_y(text)]


def _vi_date(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        y, m, d = str(iso).split("-")[:3]
        return f"{int(d)}/{int(m)}/{y}"
    except ValueError:
        return str(iso)


def build_docx_de_doc(minutes: dict[str, Any]) -> bytes:
    """Dựng bản dễ đọc từ dict ``StructuredMinutes``. Trả về bytes của tệp .docx."""
    if not isinstance(minutes, dict) or not minutes.get("meta"):
        raise ValueError("Biên bản không có phần meta")
    meta = minutes["meta"]
    title = meta.get("meeting_title") or "Biên bản cuộc họp"
    body: list[str] = [_p(_run(title), style="Title")]

    info = [x for x in (
        f"Ngày {_vi_date(meta.get('date'))}" if meta.get("date") else "",
        f"{meta['duration_minutes']} phút" if meta.get("duration_minutes") else "",
    ) if x]
    if info:
        body.append(_p(_run("  ·  ".join(info), color="5A566E")))

    # 1. Tóm tắt
    tldr = (minutes.get("executive_summary") or {}).get("tldr") or []
    if tldr:
        body.append(_p(_run("Tóm tắt", bold=True), extra=_HL))
        for line in tldr:
            body += _bullets(str(line), highlight=True)

    # 2. Việc cần làm — khối dọc, không bảng
    items = [a for a in (minutes.get("action_items") or []) if a.get("status") not in ("done", "cancelled")]
    body.append(_p(_run("Việc cần làm"), style="Heading1"))
    if not items:
        body.append(_p(_run("Không có việc nào được giao.")))
    for a in items:
        # Ten viec DINH vao dong "Ai · Han" ben duoi (cach 2pt, keepNext), con
        # giua hai viec van cach 12pt: mat thay ngay dong nao thuoc viec nao.
        body.append(_p(_run(str(a.get("task", "")), bold=True),
                       extra=_HL + '<w:keepNext/><w:spacing w:after="40"/>'))
        who = a.get("assignee") or "Chưa có người nhận"
        due = _vi_date(a.get("due_date")) or (a.get("due_raw") or "Chưa có hạn")
        body.append(_p(_run(f"{who}  ·  Hạn: {due}"), extra=_HL))

    # 3. Đã chốt — chỉ quyết định còn hiệu lực
    live = [d for d in (minutes.get("decisions") or [])
            if not d.get("superseded_by") and d.get("status") not in ("rejected", "superseded", "reverted")]
    if live:
        body.append(_p(_run("Đã chốt"), style="Heading1"))
        for d in live:
            body += _bullets(str(d.get("statement", "")))

    # 4. Câu hỏi còn mở
    qs = minutes.get("open_questions") or []
    if qs:
        body.append(_p(_run("Câu hỏi còn mở"), style="Heading1"))
        for q in qs:
            body += _bullets(str(q.get("question", "")))

    # 5. Rủi ro còn mở
    risks = [r for r in (minutes.get("risks") or []) if r.get("status") not in ("closed", "mitigated")]
    if risks:
        body.append(_p(_run("Rủi ro cần để ý"), style="Heading1"))
        for r in risks:
            body += _bullets(str(r.get("risk", "")))

    # 6. Người dự — cuối cùng, ít quan trọng nhất để HÀNH ĐỘNG
    names = [a.get("display_name") for a in (meta.get("attendees") or []) if a.get("display_name")]
    if names:
        body.append(_p(_run("Người dự"), style="Heading1"))
        body.append(_p(_run(", ".join(names))))

    return _package(title, "".join(body))


_STYLES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W}">
<w:docDefaults><w:rPrDefault><w:rPr>
<w:rFonts w:ascii="Verdana" w:hAnsi="Verdana" w:cs="Verdana" w:eastAsia="Verdana"/>
<w:color w:val="1F1E2E"/><w:spacing w:val="10"/><w:sz w:val="26"/><w:szCs w:val="26"/><w:lang w:val="vi-VN"/>
</w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="240" w:line="360" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/>
<w:pPr><w:spacing w:after="120"/></w:pPr><w:rPr><w:b/><w:sz w:val="36"/><w:szCs w:val="36"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>
<w:pPr><w:keepNext/><w:spacing w:before="360" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:style>
</w:styles>"""

_CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>"""
_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>"""
_DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/></Relationships>"""
# Thiếu displayBackgroundShape thì Word ẩn màu nền trang.
_SETTINGS = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="{W}"><w:displayBackgroundShape/><w:defaultTabStop w:val="720"/></w:settings>"""


def _package(title: str, body: str) -> bytes:
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document xmlns:w="{W}"><w:background w:color="{NEN}"/><w:body>{body}'
                '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
                '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1418" '
                'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr></w:body></w:document>')
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            f'<dc:title>{_esc(title)} (bản dễ đọc)</dc:title><dc:creator>Meety</dc:creator></cp:coreProperties>')
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CT)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/document.xml", document)
        z.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        z.writestr("word/styles.xml", _STYLES)
        z.writestr("word/settings.xml", _SETTINGS)
        z.writestr("docProps/core.xml", core)
    return buf.getvalue()
