"""Xuất biên bản ra Word (.docx) theo mẫu hành chính doanh nghiệp.

Vì sao tự viết OOXML thay vì dùng python-docx
----------------------------------------------
``.docx`` là một tệp ZIP chứa vài tệp XML. Sinh ra nó cần khoảng 200 dòng, và
đổi lại ta không thêm một phụ thuộc nữa vào dự án vốn cố ý giữ ít (xem
``core/env.py``). ``python-docx`` mạnh khi cần *đọc* và *sửa* tài liệu có sẵn;
ở đây ta chỉ *sinh mới* từ dữ liệu đã có cấu trúc — phần dễ nhất của định dạng.

Cái giá: nếu sau này cần chèn ảnh, biểu đồ, hay trộn vào mẫu công ty có sẵn
thì nên chuyển sang ``python-docx``. Chỗ phải sửa là đúng module này.

Tài liệu sinh ra mở được bằng Word, LibreOffice, Google Docs và WPS — đã kiểm
bằng cách giải nén và soi lại XML, không phải bằng niềm tin.
"""

from __future__ import annotations

import zipfile
from datetime import datetime
from io import BytesIO
from typing import Any, Iterable, Sequence
from xml.sax.saxutils import escape

__all__ = ["build_docx", "DocxBuildError"]

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class DocxBuildError(Exception):
    pass


# ===========================================================================
#  Khối XML dựng sẵn
# ===========================================================================

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

# Times New Roman 13pt (size 26 half-points) — chuẩn văn bản hành chính Việt Nam
# theo Nghị định 30/2020/NĐ-CP. Không dùng font của giao diện web ở đây: tài
# liệu này đi vào hồ sơ, phải theo quy chuẩn của hồ sơ.
STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
<w:sz w:val="26"/><w:szCs w:val="26"/><w:lang w:val="vi-VN"/>
</w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/>
<w:pPr><w:jc w:val="center"/><w:spacing w:before="240" w:after="120"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="32"/><w:caps/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/>
<w:pPr><w:spacing w:before="280" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/>
<w:pPr><w:ind w:left="567"/><w:spacing w:after="80"/></w:pPr>
<w:rPr><w:i/><w:color w:val="4A453C"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="caption"/>
<w:rPr><w:sz w:val="20"/><w:color w:val="8A8378"/></w:rPr></w:style>
<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/>
<w:tblPr><w:tblBorders>
<w:top w:val="single" w:sz="8" w:color="000000"/><w:left w:val="single" w:sz="8" w:color="000000"/>
<w:bottom w:val="single" w:sz="8" w:color="000000"/><w:right w:val="single" w:sz="8" w:color="000000"/>
<w:insideH w:val="single" w:sz="8" w:color="000000"/><w:insideV w:val="single" w:sz="8" w:color="000000"/>
</w:tblBorders></w:tblPr></w:style>
</w:styles>"""


# ===========================================================================
#  Bộ dựng đoạn văn
# ===========================================================================

def _esc(text: Any) -> str:
    return escape(str(text if text is not None else ""))


def _run(text: str, *, bold=False, italic=False, color: str | None = None,
         size: int | None = None) -> str:
    props = []
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    if size:
        props.append(f'<w:sz w:val="{size}"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    # xml:space="preserve" bắt buộc, nếu không Word cắt mất khoảng trắng đầu/cuối.
    return f'<w:r>{rpr}<w:t xml:space="preserve">{_esc(text)}</w:t></w:r>'


def _para(runs: str, *, style: str | None = None, align: str | None = None,
          ind: int | None = None) -> str:
    props = []
    if style:
        props.append(f'<w:pStyle w:val="{style}"/>')
    if align:
        props.append(f'<w:jc w:val="{align}"/>')
    if ind:
        props.append(f'<w:ind w:left="{ind}"/>')
    ppr = f"<w:pPr>{''.join(props)}</w:pPr>" if props else ""
    return f"<w:p>{ppr}{runs}</w:p>"


def _text(text: str, **kw) -> str:
    style = kw.pop("style", None)
    align = kw.pop("align", None)
    ind = kw.pop("ind", None)
    return _para(_run(text, **kw), style=style, align=align, ind=ind)


def _bullet(text: str, *, level: int = 0) -> str:
    # Dùng ký tự gạch đầu dòng thay vì numbering.xml: bullet thật cần thêm một
    # part nữa và một bảng abstractNum — nhiều XML hơn để đổi lấy khác biệt
    # thị giác rất nhỏ trong một biên bản.
    return _para(_run(("    " * level) + "– " + text), ind=283 + level * 283)


def _cell(content: str, *, width: int, bold=False, shade: str | None = None) -> str:
    shading = f'<w:shd w:val="clear" w:fill="{shade}"/>' if shade else ""
    body = content if content.startswith("<w:p") else _para(_run(content, bold=bold))
    return (f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shading}'
            f'<w:vAlign w:val="center"/></w:tcPr>{body}</w:tc>')


def _table(rows: Sequence[Sequence[str]], widths: Sequence[int],
           *, header: bool = True) -> str:
    if not rows:
        return ""
    out = [
        '<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
        '<w:tblW w:w="0" w:type="auto"/><w:tblLayout w:type="fixed"/>'
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="8" w:color="000000"/>'
        '<w:left w:val="single" w:sz="8" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="8" w:color="000000"/>'
        '<w:right w:val="single" w:sz="8" w:color="000000"/>'
        '<w:insideH w:val="single" w:sz="8" w:color="000000"/>'
        '<w:insideV w:val="single" w:sz="8" w:color="000000"/>'
        '</w:tblBorders></w:tblPr>',
        '<w:tblGrid>' + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + '</w:tblGrid>',
    ]
    for i, row in enumerate(rows):
        is_head = header and i == 0
        # tblHeader để hàng tiêu đề tự lặp lại khi bảng tràn sang trang sau.
        trpr = '<w:trPr><w:tblHeader/></w:trPr>' if is_head else ""
        cells = "".join(
            _cell(c, width=w, bold=is_head, shade="EBE2CC" if is_head else None)
            for c, w in zip(row, widths))
        out.append(f"<w:tr>{trpr}{cells}</w:tr>")
    out.append("</w:tbl>")
    # Word cần một đoạn văn rỗng sau bảng, nếu không hai bảng liền nhau bị dính.
    out.append(_para(""))
    return "".join(out)


# ===========================================================================
#  Dựng tài liệu
# ===========================================================================

VI_DATE = "{d}/{m}/{y}"
STRENGTH_VI = {"firm": "Cam kết chắc", "tentative": "Dự kiến", "implied": "Ngụ ý"}
STATUS_VI = {"todo": "Cần làm", "in_progress": "Đang làm", "done": "Hoàn thành",
             "open": "Cần làm"}
PRIORITY_VI = {"high": "Cao", "medium": "Trung bình", "low": "Thấp"}


def _vi_date(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        y, m, d = str(iso).split("-")[:3]
        return VI_DATE.format(d=d, m=m, y=y)
    except ValueError:
        return str(iso)


def build_docx(
    minutes: dict[str, Any],
    *,
    transcript: dict[str, Any] | None = None,
    members: Sequence[dict] | None = None,
    assignments: dict[str, dict] | None = None,
    approved_by: str | None = None,
    approved_at: str | None = None,
    org_name: str = "",
    include_transcript: bool = False,
) -> bytes:
    """Dựng tệp .docx, trả về bytes để gửi thẳng qua HTTP."""
    if not isinstance(minutes, dict) or not minutes.get("meta"):
        raise DocxBuildError("Biên bản không có phần meta, không dựng được tài liệu")

    meta = minutes.get("meta", {})
    title = meta.get("meeting_title") or "Biên bản cuộc họp"
    members = list(members or [])
    assignments = assignments or {}
    body: list[str] = []

    # -- Phần đầu: quốc hiệu rút gọn kiểu văn bản nội bộ ------------------- #
    if org_name:
        body.append(_text(org_name, bold=True, align="center", size=24))
    body.append(_text("BIÊN BẢN CUỘC HỌP", style="Title"))
    body.append(_text(title, bold=True, align="center", size=28))
    body.append(_para(""))

    # -- Bảng thông tin chung --------------------------------------------- #
    owner = next((m.get("display_name") or m.get("email")
                  for m in members if m.get("role") == "owner"), "—")
    status_line = ("ĐÃ PHÊ DUYỆT" if approved_by else "CHỜ PHÊ DUYỆT")
    info_rows = [
        ["Thời gian", _vi_date(meta.get("date"))],
        ["Thời lượng", f"{meta.get('duration_minutes', '—')} phút"],
        ["Chủ trì", str(owner)],
        ["Số người tham dự", str(len(members) or len(meta.get("attendees") or []))],
        ["Trạng thái", status_line],
    ]
    if approved_by:
        info_rows.append(["Người phê duyệt", str(approved_by)])
        info_rows.append(["Thời điểm phê duyệt", str(approved_at or "—")])
    body.append(_table([[k, v] for k, v in info_rows], [2600, 6400], header=False))

    # -- Thành phần tham dự ------------------------------------------------ #
    body.append(_text("I. THÀNH PHẦN THAM DỰ", style="Heading1"))
    people = members or [
        {"display_name": a.get("display_name"), "email": "", "role": "member"}
        for a in (meta.get("attendees") or [])
    ]
    if people:
        rows = [["STT", "Họ và tên", "Email", "Vai trò"]]
        for i, m in enumerate(people, 1):
            rows.append([
                str(i),
                str(m.get("display_name") or m.get("email") or "—"),
                str(m.get("email") or "—"),
                "Chủ trì" if m.get("role") == "owner" else "Thành viên",
            ])
        body.append(_table(rows, [700, 3200, 3600, 1500]))
    else:
        body.append(_text("Không có dữ liệu người tham dự.", italic=True))

    # -- Tóm tắt điều hành -------------------------------------------------- #
    body.append(_text("II. TÓM TẮT ĐIỀU HÀNH", style="Heading1"))
    tldr = (minutes.get("executive_summary") or {}).get("tldr") or []
    if tldr:
        for line in tldr:
            body.append(_bullet(str(line)))
    else:
        body.append(_text("Không có nội dung tóm tắt.", italic=True))
    for para in (minutes.get("executive_summary") or {}).get("paragraphs") or []:
        body.append(_text(str(para)))

    # -- Quyết định --------------------------------------------------------- #
    body.append(_text("III. CÁC QUYẾT ĐỊNH", style="Heading1"))
    decisions = [d for d in (minutes.get("decisions") or []) if not d.get("superseded_by")]
    dead = [d for d in (minutes.get("decisions") or []) if d.get("superseded_by")]
    if decisions:
        for i, d in enumerate(decisions, 1):
            body.append(_text(f"{i}. {d.get('statement', '')}", bold=True))
            if d.get("decided_by"):
                body.append(_text(f"Người chốt: {d['decided_by']}", ind=283))
            if d.get("quote"):
                body.append(_text(f"“{d['quote']}”", style="Quote"))
            stamp = _timestamp(d, transcript)
            if stamp:
                body.append(_text(f"Dẫn chứng: đoạn ghi âm lúc {stamp}",
                                  style="Caption", ind=283))
    else:
        body.append(_text("Cuộc họp không chốt quyết định nào.", italic=True))

    if dead:
        body.append(_text("Quyết định đã bị thay thế (giữ lại để truy vết):", bold=True))
        for d in dead:
            body.append(_bullet(str(d.get("statement", ""))))

    # -- Phân công công việc ------------------------------------------------ #
    body.append(_text("IV. PHÂN CÔNG CÔNG VIỆC", style="Heading1"))
    actions = minutes.get("action_items") or []
    if actions:
        rows = [["STT", "Nội dung công việc", "Người phụ trách", "Hạn hoàn thành",
                 "Ưu tiên", "Trạng thái"]]
        by_member = {m.get("id"): m for m in members}
        for i, a in enumerate(actions, 1):
            asg = assignments.get(a.get("id"), {})
            who = None
            if asg.get("member_id") and asg["member_id"] in by_member:
                who = by_member[asg["member_id"]].get("display_name")
            who = who or a.get("assignee")
            rows.append([
                str(i),
                str(a.get("task", "")),
                str(who) if who else "CHƯA PHÂN CÔNG",
                _vi_date(a.get("due_date")) if a.get("due_date") else "Chưa có hạn",
                PRIORITY_VI.get(a.get("priority", "medium"), "Trung bình"),
                STATUS_VI.get(a.get("status", "todo"), "Cần làm"),
            ])
        body.append(_table(rows, [600, 3100, 1900, 1400, 900, 1100]))

        unassigned = sum(
            1 for a in actions
            if not (assignments.get(a.get("id"), {}).get("member_id") or a.get("assignee")))
        if unassigned:
            body.append(_text(
                f"Lưu ý: còn {unassigned} công việc chưa có người nhận. "
                "Hệ thống để trống thay vì suy đoán người phụ trách.",
                italic=True, color="B33A1E"))
    else:
        body.append(_text("Không có công việc nào được giao.", italic=True))

    # -- Chỉ số nhắc tới ----------------------------------------------------- #
    metrics = minutes.get("metrics") or []
    if metrics:
        body.append(_text("V. CÁC CHỈ SỐ ĐƯỢC NHẮC TỚI", style="Heading1"))
        body.append(_table(
            [["Chỉ số", "Giá trị"]] + [[str(m.get("label", "")), str(m.get("value_raw", ""))]
                                       for m in metrics],
            [5200, 3800]))

    # -- Cảnh báo chất lượng -------------------------------------------------- #
    warns = (minutes.get("quality_report") or {}).get("warnings") or []
    if warns:
        body.append(_text("VI. ĐIỂM CẦN RÀ SOÁT", style="Heading1"))
        names = {
            "AMBIGUOUS_ASSIGNEE": "Chưa gán người làm",
            "SUPERSEDED_DEPENDENCY": "Bị thay thế",
            "TRANSCRIPT_GAPS": "Thoại mờ",
            "LOW_COMMITMENT_STRENGTH": "Chưa cam kết",
            "HALLUCINATION_RISK": "Rủi ro ảo giác",
        }
        for w in warns:
            label = names.get(w.get("code"), str(w.get("code", "")))
            body.append(_bullet(f"{label}: {w.get('message', '')}"))

    # -- Bản thoại (tuỳ chọn) -------------------------------------------------- #
    if include_transcript and transcript and transcript.get("segments"):
        body.append(_text("PHỤ LỤC: BẢN THOẠI GỐC", style="Heading1"))
        names = {s.get("label"): s.get("display_name") or s.get("label")
                 for s in (transcript.get("speakers") or [])}
        for s in transcript["segments"]:
            who = names.get(s.get("speaker_label"), s.get("speaker_label", "?"))
            stamp = _ms_to_clock(s.get("start_ms", 0))
            body.append(_para(
                _run(f"[{stamp}] {who}: ", bold=True) + _run(str(s.get("text", "")))))

    # -- Ký tên ---------------------------------------------------------------- #
    body.append(_para(""))
    body.append(_table([[
        _text("NGƯỜI GHI BIÊN BẢN", bold=True, align="center")
        + _text("(Hệ thống Meety tổng hợp tự động)", style="Caption", align="center")
        + _para("") + _para("") + _para(""),
        _text("CHỦ TRÌ CUỘC HỌP", bold=True, align="center")
        + _text("(Ký, ghi rõ họ tên)", style="Caption", align="center")
        + _para("") + _para("") + _para("")
        + _text(str(owner), bold=True, align="center"),
    ]], [4500, 4500], header=False))

    body.append(_text(
        f"Tài liệu sinh tự động bởi Meety lúc "
        f"{datetime.now().strftime('%H:%M %d/%m/%Y')}. "
        "Mọi mệnh đề trong biên bản đều có dẫn chứng tới đoạn ghi âm gốc.",
        style="Caption", align="center"))

    return _package(title, "".join(body))


def _timestamp(item: dict, transcript: dict | None) -> str | None:
    if not transcript:
        return None
    ids = item.get("evidence_segment_ids") or []
    if not ids:
        return None
    for s in transcript.get("segments") or []:
        if s.get("id") == ids[0]:
            return _ms_to_clock(s.get("start_ms", 0))
    return None


def _ms_to_clock(ms: int) -> str:
    total = max(0, int(ms) // 1000)
    return f"{total // 60:02d}:{total % 60:02d}"


def _package(title: str, body_xml: str) -> bytes:
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>{body_xml}'
        # Khổ A4 dọc, lề theo Nghị định 30: trên 20mm, dưới 20mm, trái 30mm,
        # phải 15mm. Đơn vị twip: 1mm = 56.7 twip.
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1134" w:right="851" w:bottom="1134" w:left="1701" '
        'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
        '</w:body></w:document>'
    )
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    core = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties '
        'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f'<dc:title>{_esc(title)}</dc:title>'
        '<dc:creator>Meety</dc:creator><cp:lastModifiedBy>Meety</cp:lastModifiedBy>'
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        '</cp:coreProperties>'
    )
    app = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
        '<Application>Meety</Application><Company></Company></Properties>'
    )

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        # [Content_Types].xml phải là mục ĐẦU TIÊN trong ZIP. Word vẫn mở được
        # nếu sai thứ tự, nhưng một số công cụ nghiêm ngặt hơn thì không.
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("word/document.xml", document)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/styles.xml", STYLES)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
    return buf.getvalue()
