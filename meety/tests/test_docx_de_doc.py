"""Bản Word dễ đọc (dyslexia) — kiểm đúng các quy chuẩn trình bày đã hứa."""

import json
import zipfile
from io import BytesIO
from pathlib import Path
from xml.dom import minidom

import pytest

from exporters.docx_de_doc import CAU_DAI, build_docx_de_doc, tach_y

GOLDEN = Path(__file__).parent / "fixtures" / "golden_minutes.json"


@pytest.fixture(scope="module")
def minutes():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def parts(minutes):
    z = zipfile.ZipFile(BytesIO(build_docx_de_doc(minutes)))
    return {n: z.read(n).decode("utf-8") for n in z.namelist()}


def test_moi_phan_xml_deu_hop_le(parts):
    for name, xml in parts.items():
        minidom.parseString(xml.encode("utf-8"))
    assert "word/settings.xml" in parts


def test_font_khong_chan_gian_dong_can_trai(parts):
    st = parts["word/styles.xml"]
    assert "Verdana" in st and "Times New Roman" not in st
    assert 'w:line="360"' in st
    assert '<w:jc w:val="left"/>' in st and 'w:val="both"' not in st


def test_khong_in_nghieng_khong_viet_hoa_ca_cau(parts):
    for xml in (parts["word/styles.xml"], parts["word/document.xml"]):
        assert "<w:i/>" not in xml and "<w:caps/>" not in xml and "<w:u " not in xml


def test_nen_kem_va_hien_duoc_trong_word(parts):
    assert 'w:background w:color="FFF8E7"' in parts["word/document.xml"]
    assert "displayBackgroundShape" in parts["word/settings.xml"]


def test_khong_dung_bang(parts):
    assert "<w:tbl>" not in parts["word/document.xml"]


def test_viec_can_lam_dung_TRUOC_da_chot(parts):
    doc = parts["word/document.xml"]
    assert doc.index("Việc cần làm") < doc.index("Đã chốt")


def test_bo_quyet_dinh_da_bi_thay_the(parts, minutes):
    doc = parts["word/document.xml"]
    bi_bac = next(d for d in minutes["decisions"] if d.get("superseded_by"))
    con = next(d for d in minutes["decisions"] if not d.get("superseded_by"))
    assert bi_bac["statement"][:30] not in doc
    assert con["statement"][:30] in doc


def test_viec_chua_co_nguoi_nhan_van_hien_ro(parts):
    assert "Chưa có người nhận" in parts["word/document.xml"]


def test_tach_cau_dai():
    dai = "Câu thứ nhất khá dài để vượt ngưỡng. " * 3 + "Câu cuối."
    assert len(dai) > CAU_DAI and len(tach_y(dai)) > 1
    assert tach_y("Ngắn.") == ["Ngắn."]
    assert tach_y("") == []


def test_ky_tu_dieu_khien_khong_lam_hong_tep(minutes):
    m = json.loads(json.dumps(minutes))
    m["meta"]["meeting_title"] = "Họp\x01 <nhóm> & chốt"
    z = zipfile.ZipFile(BytesIO(build_docx_de_doc(m)))
    minidom.parseString(z.read("word/document.xml"))


def test_thieu_meta_thi_bao_loi():
    with pytest.raises(ValueError):
        build_docx_de_doc({})


def test_xuat_word_ra_hai_tep(tmp_path, minutes):
    from xuat_word import xuat
    src = tmp_path / "abc_minutes.json"
    src.write_text(json.dumps(minutes, ensure_ascii=False), encoding="utf-8")
    chuan, de_doc = xuat(src)
    assert chuan.name == "abc_bien_ban.docx" and de_doc.name == "abc_bien_ban_de_doc.docx"
    for f in (chuan, de_doc):
        zipfile.ZipFile(f).testzip()
