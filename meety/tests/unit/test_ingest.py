"""Test cho pha 0 — INGEST.

Trọng tâm không nằm ở việc "parser chạy được". Nó nằm ở các chỗ mà một
parser cẩu thả sẽ âm thầm làm hỏng dữ liệu:

* gán lời của người này cho người khác,
* nuốt phần đầu tài liệu vào transcript rồi biến nó thành bằng chứng giả,
* nhận nhầm một mệnh đề tiếng Việt có dấu hai chấm thành tên người,
* đảo lộn thứ tự thời gian, phá quy tắc supersession ở ``s5_reconcile``.

Mỗi lỗi trên đều có test riêng ở dưới.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from pipeline.s0_ingest import (
    UNKNOWN_LABEL,
    _split_speaker,
    IngestPolicy,
    SourceFormat,
    detect_format,
    merge_cues,
    parse_plain_text,
    parse_srt,
    parse_webvtt,
    read_source_text,
    run_ingest,
)
from schemas.common import IdentificationMethod, Language, MeetingType
from schemas.transcript import TranscriptMeta

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
INGEST_DIR = FIXTURES / "ingest"
MEETING_DATE = dt.date(2026, 7, 22)


def _meta(title: str = "Cuộc họp thử") -> TranscriptMeta:
    return TranscriptMeta(
        title=title,
        meeting_date=MEETING_DATE,
        meeting_type=MeetingType.PLANNING,
        duration_ms=0,
    )


def _ingest(name: str, **kwargs):
    path = INGEST_DIR / name
    return run_ingest(path, meta=_meta(), meeting_id="mtg_test", **kwargs)


# --------------------------------------------------------------------------- #
# Nhận dạng định dạng
# --------------------------------------------------------------------------- #


class TestDetectFormat:
    def test_webvtt_theo_header(self) -> None:
        assert detect_format("WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nxin chào") is (
            SourceFormat.WEBVTT
        )

    def test_srt_theo_dau_phay_mili_giay(self) -> None:
        text = "1\n00:00:01,000 --> 00:00:02,500\nxin chào\n"
        assert detect_format(text) is SourceFormat.SRT

    def test_json_theo_ky_tu_dau(self) -> None:
        assert detect_format('{"transcript_id": "x"}') is SourceFormat.NATIVE_JSON

    def test_van_ban_thuan_khi_khong_co_moc_thoi_gian(self) -> None:
        assert detect_format("Hùng: xin chào\nTuấn: vâng") is SourceFormat.PLAIN_TEXT

    def test_noi_dung_thang_duoi_dinh_dang(self) -> None:
        """Đuôi file không đáng tin — trình duyệt hay tải VTT về thành .txt."""
        text = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHùng: xin chào\n"
        assert detect_format(text, suffix=".txt") is SourceFormat.WEBVTT

    def test_dung_duoi_file_khi_noi_dung_khong_ket_luan_duoc(self) -> None:
        assert detect_format("chỉ là văn bản", suffix=".srt") is SourceFormat.SRT


# --------------------------------------------------------------------------- #
# Parser WebVTT
# --------------------------------------------------------------------------- #


class TestParseWebVTT:
    def test_kieu_zoom_ten_truoc_dau_hai_cham(self) -> None:
        cues = parse_webvtt(
            "WEBVTT\n\n1\n00:00:04.000 --> 00:00:08.500\nHùng: Bắt đầu nhé.\n"
        )
        assert len(cues) == 1
        assert cues[0].speaker == "Hùng"
        assert cues[0].text == "Bắt đầu nhé."
        assert (cues[0].start_ms, cues[0].end_ms) == (4000, 8500)

    def test_kieu_teams_the_voice_span(self) -> None:
        cues = parse_webvtt(
            "WEBVTT\n\n00:00:02.140 --> 00:00:09.820\n"
            "<v Trần Thị Lan>Chào cả nhà.</v>\n"
        )
        assert cues[0].speaker == "Trần Thị Lan"
        assert cues[0].text == "Chào cả nhà."

    def test_bo_qua_khoi_note_style_region(self) -> None:
        text = (
            "WEBVTT\n\n"
            "NOTE\nGhi chú của Zoom\nDòng thứ hai\n\n"
            "STYLE\n::cue { color: white }\n\n"
            "1\n00:00:01.000 --> 00:00:03.000\nHùng: nội dung thật\n"
        )
        cues = parse_webvtt(text)
        assert len(cues) == 1
        assert cues[0].text == "nội dung thật"

    def test_noi_cac_dong_trong_than_cue(self) -> None:
        text = (
            "WEBVTT\n\n1\n00:00:01.000 --> 00:00:05.000\n"
            "Tuấn: phần API đã xong\nvà đã deploy lên staging\n"
        )
        cues = parse_webvtt(text)
        assert cues[0].text == "phần API đã xong và đã deploy lên staging"

    def test_moc_thoi_gian_thieu_gio(self) -> None:
        cues = parse_webvtt("WEBVTT\n\n01:30.500 --> 02:00.000\nHùng: xin chào\n")
        assert (cues[0].start_ms, cues[0].end_ms) == (90_500, 120_000)

    def test_mili_giay_thieu_chu_so_duoc_dem_phai(self) -> None:
        """``.5`` là 500ms chứ không phải 5ms — đệm phải, không đệm trái."""
        cues = parse_webvtt("WEBVTT\n\n00:00:01.5 --> 00:00:02.25\nHùng: a\n")
        assert cues[0].start_ms == 1_500
        assert cues[0].end_ms == 2_250

    def test_cue_rong_bi_bo_qua(self) -> None:
        text = (
            "WEBVTT\n\n1\n00:00:01.000 --> 00:00:02.000\n\n"
            "2\n00:00:03.000 --> 00:00:04.000\nHùng: có nội dung\n"
        )
        assert len(parse_webvtt(text)) == 1


# --------------------------------------------------------------------------- #
# Parser SRT
# --------------------------------------------------------------------------- #


class TestParseSRT:
    def test_doc_duoc_dau_phay_mili_giay(self) -> None:
        cues = parse_srt(
            "1\n00:00:03,000 --> 00:00:12,500\nHoàng: Bản mockup đã lên Figma.\n"
        )
        assert cues[0].speaker == "Hoàng"
        assert (cues[0].start_ms, cues[0].end_ms) == (3_000, 12_500)

    def test_bo_phan_trong_ngoac_sau_ten(self) -> None:
        cues = parse_srt(
            "1\n00:00:03,000 --> 00:00:12,500\n"
            "Hoàng (Design Lead): Bản mockup đã lên Figma.\n"
        )
        assert cues[0].speaker == "Hoàng"
        assert cues[0].text == "Bản mockup đã lên Figma."


# --------------------------------------------------------------------------- #
# Parser văn bản thuần — nơi dễ sai nhất
# --------------------------------------------------------------------------- #


class TestParsePlainText:
    def test_moc_thoi_gian_trong_ngoac_vuong(self) -> None:
        cues = parse_plain_text("[00:01:15] Hùng: anh Tuấn chuẩn bị bảng nhé.")
        assert cues[0].start_ms == 75_000
        assert cues[0].speaker == "Hùng"

    def test_dong_khong_co_ten_noi_tiep_nguoi_truoc(self) -> None:
        cues = parse_plain_text(
            "Tuấn: bên em đề xuất tăng ngân sách.\nLý do là chi phí cloud vượt dự toán."
        )
        assert [c.speaker for c in cues] == ["Tuấn", "Tuấn"]

    @pytest.mark.parametrize(
        "line",
        [
            "Kết luận: chốt tăng ngân sách hạ tầng.",
            "Thời gian: 14:00 ngày 22/07/2026",
            "Địa điểm: phòng họp tầng 5",
            "Ghi chú: cần gửi lại tài liệu",
            "Lưu ý: bản này cần khớp design system",
        ],
    )
    def test_menh_de_co_dau_hai_cham_khong_bi_nham_la_ten(self, line: str) -> None:
        """Câu tiếng Việt bình thường cũng chứa dấu hai chấm.

        Nhận nhầm một mệnh đề thành tên sẽ đẻ ra speaker ma và phá vỡ toàn bộ
        phần quy trách nhiệm — tệ hơn nhiều so với bỏ sót một tên.
        """
        cues = parse_plain_text(f"Hùng: mở đầu.\n{line}")
        assert all(c.speaker == "Hùng" for c in cues)
        assert cues[-1].text == line

    def test_url_khong_bi_nham_la_ten(self) -> None:
        cues = parse_plain_text("Hùng: xem tại https://example.com/tai-lieu nhé")
        assert cues[0].speaker == "Hùng"
        assert "https://example.com" in cues[0].text

    def test_cum_qua_dai_khong_phai_ten(self) -> None:
        line = "Việc cần làm trong tuần này và cả tuần sau nữa: rà soát lại toàn bộ"
        cues = parse_plain_text(f"Hùng: mở đầu.\n{line}")
        assert cues[-1].speaker == "Hùng"

    def test_bo_phan_dau_tai_lieu(self) -> None:
        """Tiêu đề/thời gian/địa điểm KHÔNG được lọt vào transcript.

        Nếu lọt, chúng sẽ bị gán cho một người nào đó và trở thành bằng chứng
        có thật cho các mệnh đề trong biên bản.
        """
        text = (
            "Biên bản họp kế hoạch quý 3\n"
            "Thời gian: 14:00 ngày 22/07/2026\n"
            "Địa điểm: phòng họp tầng 5\n\n"
            "Hùng: Chào mọi người.\n"
        )
        cues = parse_plain_text(text)
        assert len(cues) == 1
        assert cues[0].text == "Chào mọi người."

    def test_giu_lai_tat_ca_khi_khong_co_ten_nao(self) -> None:
        """Không có tên trong cả file thì đây là transcript một khối, giữ nguyên."""
        cues = parse_plain_text("đoạn một\nđoạn hai\nđoạn ba")
        assert len(cues) == 3

    def test_moc_thoi_gian_suy_ra_van_tang_dan(self) -> None:
        """Không có timestamp thật thì THỨ TỰ vẫn phải đúng.

        Quy tắc "phát biểu sau đè phát biểu trước" ở ``s5_reconcile`` sắp xếp
        theo ``start_ms``. Thứ tự sai thì supersession chọn nhầm quyết định.
        """
        cues = parse_plain_text(
            "Hùng: câu một.\nTuấn: câu hai.\nLan: câu ba.\nHùng: câu bốn."
        )
        starts = [c.start_ms for c in cues]
        assert starts == sorted(starts)
        assert all(c.end_ms >= c.start_ms for c in cues)

    def test_khong_de_lan_sang_moc_thoi_gian_ke_tiep(self) -> None:
        cues = parse_plain_text(
            "[00:00:00] Hùng: một câu rất dài với thật nhiều từ để thời lượng "
            "suy ra bị tràn qua mốc kế tiếp\n[00:00:02] Tuấn: câu sau"
        )
        assert cues[0].end_ms <= cues[1].start_ms


# --------------------------------------------------------------------------- #
# Gộp lượt thoại
# --------------------------------------------------------------------------- #


class TestMergeCues:
    def test_gop_cue_lien_nhau_cung_nguoi(self) -> None:
        cues = parse_webvtt(
            "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHùng: câu một.\n\n"
            "00:00:02.500 --> 00:00:04.000\nHùng: câu hai.\n"
        )
        merged = merge_cues(cues, IngestPolicy())
        assert len(merged) == 1
        assert merged[0].text == "câu một. câu hai."
        assert merged[0].end_ms == 4_000

    def test_khong_bao_gio_gop_qua_ranh_gioi_nguoi_noi(self) -> None:
        """Gộp qua ranh giới người nói = gán lời người này cho người kia."""
        cues = parse_webvtt(
            "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHùng: câu một.\n\n"
            "00:00:02.100 --> 00:00:04.000\nTuấn: câu hai.\n"
        )
        merged = merge_cues(cues, IngestPolicy(merge_gap_ms=10_000))
        assert len(merged) == 2

    def test_khoang_lang_dai_thi_khong_gop(self) -> None:
        cues = parse_webvtt(
            "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHùng: câu một.\n\n"
            "00:00:30.000 --> 00:00:32.000\nHùng: câu hai.\n"
        )
        assert len(merge_cues(cues, IngestPolicy())) == 2

    def test_ton_trong_tran_do_dai(self) -> None:
        cues = parse_webvtt(
            "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHùng: aaaaaaaaaa.\n\n"
            "00:00:02.200 --> 00:00:04.000\nHùng: bbbbbbbbbb.\n"
        )
        assert len(merge_cues(cues, IngestPolicy(max_segment_chars=15))) == 2

    def test_danh_sach_rong(self) -> None:
        assert merge_cues([], IngestPolicy()) == []


# --------------------------------------------------------------------------- #
# Dựng Transcript
# --------------------------------------------------------------------------- #


class TestRunIngest:
    def test_vtt_zoom_dung_lai_dung_transcript_mau(self) -> None:
        """Phép thử mạnh nhất của cả module.

        File VTT được dựng từ ``sample_transcript.json``. Nếu ingest đúng thì
        nó phải tái tạo lại chính xác từng segment — cùng ID, cùng nhãn, cùng
        mốc thời gian, cùng ký tự.
        """
        outcome = _ingest("zoom_sprint23.vtt", policy=IngestPolicy(merge_gap_ms=0))
        reference = json.loads(
            (FIXTURES / "sample_transcript.json").read_text(encoding="utf-8")
        )

        assert len(outcome.transcript.segments) == len(reference["segments"])
        for expected, actual in zip(reference["segments"], outcome.transcript.segments):
            assert actual.id == expected["id"]
            assert actual.text == expected["text"]
            assert actual.speaker_label == expected["speaker_label"]
            assert actual.start_ms == expected["start_ms"]
            assert actual.end_ms == expected["end_ms"]

    def test_nhan_speaker_danh_theo_thu_tu_xuat_hien(self) -> None:
        outcome = _ingest("zoom_sprint23.vtt")
        names = {s.label: s.display_name for s in outcome.transcript.speakers}
        assert names == {
            "SPEAKER_00": "Hùng",
            "SPEAKER_01": "Tuấn",
            "SPEAKER_02": "Lan",
            "SPEAKER_03": "Minh",
        }

    def test_ten_tu_nen_tang_hop_duoc_danh_dau_manual(self) -> None:
        """Tên do nền tảng họp cung cấp là do người thật khai, không phải suy đoán.

        Đánh dấu MANUAL cũng khiến ``s2_diarize`` bỏ qua đúng cách thay vì
        chạy lại phép đoán xưng hô lên dữ liệu vốn đã chắc chắn.
        """
        outcome = _ingest("zoom_sprint23.vtt")
        assert all(
            s.identification_method is IdentificationMethod.MANUAL
            for s in outcome.transcript.speakers
        )
        assert all(not s.needs_manual_assignment for s in outcome.transcript.speakers)

    def test_loi_khong_ro_nguoi_noi_khong_bi_gan_cho_nguoi_dau_tien(self) -> None:
        """Đây là lỗi nguy hiểm nhất mà module này có thể gây ra."""
        text = (
            "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nHùng: câu có tên.\n\n"
            "00:00:10.000 --> 00:00:15.000\nmột câu không rõ ai nói.\n"
        )
        outcome = run_ingest(
            Path("khong_ro.vtt"), text=text, meta=_meta(), meeting_id="mtg_test"
        )
        labels = [s.speaker_label for s in outcome.transcript.segments]
        assert labels == ["SPEAKER_00", UNKNOWN_LABEL]

        unknown = outcome.transcript.speaker_index[UNKNOWN_LABEL]
        assert unknown.display_name is None
        assert unknown.identification_method is IdentificationMethod.UNIDENTIFIED
        assert "UNATTRIBUTED_SPEECH" in {w.code for w in outcome.report.warnings}

    def test_thoi_luong_lay_tu_segment_cuoi(self) -> None:
        outcome = _ingest("zoom_sprint23.vtt")
        assert outcome.transcript.meta.duration_ms == 275_000

    def test_nhan_dien_code_switching(self) -> None:
        outcome = _ingest("zoom_sprint23.vtt")
        profile = outcome.transcript.language_profile
        assert profile.primary is Language.VI
        assert profile.code_switching is True
        assert Language.EN in profile.secondary

    def test_provider_ghi_ro_nguon_nhap(self) -> None:
        """Truy vết nguồn gốc lỗi: phải biết transcript đến từ đâu."""
        outcome = _ingest("meet_review.srt")
        assert outcome.transcript.provider.asr == "import/srt"
        assert outcome.transcript.provider.post_process == "s0_ingest"

    def test_json_goc_di_thang_khong_qua_parser(self) -> None:
        outcome = run_ingest(
            FIXTURES / "sample_transcript.json", meta=_meta(), meeting_id="mtg_test"
        )
        assert outcome.report.source_format is SourceFormat.NATIVE_JSON
        assert len(outcome.transcript.segments) == 22

    def test_file_rong_bao_loi_ro_rang(self) -> None:
        with pytest.raises(ValueError, match="Không đọc được lượt thoại"):
            run_ingest(
                Path("rong.vtt"), text="WEBVTT\n\n", meta=_meta(), meeting_id="mtg_test"
            )

    def test_checksum_on_dinh_theo_noi_dung(self) -> None:
        first = _ingest("zoom_sprint23.vtt")
        second = _ingest("zoom_sprint23.vtt")
        assert first.report.checksum == second.report.checksum


# --------------------------------------------------------------------------- #
# Cổng tiền kiểm chất lượng
# --------------------------------------------------------------------------- #


class TestQualityGate:
    def test_mot_nguoi_noi_duoc_canh_bao_nhung_khong_bi_chan(self) -> None:
        """Mot nguoi noi la chuyen DINH DANG, khong phai file hong (muc 8.3).

        Bai nay truoc day khang dinh dieu nguoc lai - ``assert
        outcome.report.blocking``. Do chinh la hanh vi da chan ca pipeline
        truoc khi kip ghi ``_minutes.json``: ban xuat khong gan nhan nguoi
        noi, hoac gan theo kieu bo tach chua biet, la mat trang ca buoi hop.

        Canh bao van phai con - nguoi dung can biet cam ket se khong quy
        duoc ve ai - nhung no khong duoc dung pipeline.
        """
        text = "\n".join(
            f"doan noi thu {i} voi du noi dung de khong bi coi la qua ngan qua"
            for i in range(40)
        )
        outcome = run_ingest(
            Path("mot_nguoi.txt"), text=text, meta=_meta(), meeting_id="mtg_test"
        )
        codes = {w.code for w in outcome.report.warnings}
        assert "SINGLE_SPEAKER" in codes
        assert "NO_SPEAKER_NAMES" in codes
        assert not outcome.report.blocking

    def test_hop_ngan_khong_bi_chan(self) -> None:
        """Ha cap ba cong khong duoc bien thanh "nuot moi thu".

        Ranh gioi moi: mot buoi dung nhanh - ba luot thoai, duoi 200 ky tu -
        van phai chay het. Day dung la loai buoi hop ma nguoi ADHD quen
        nhieu nhat, va la loai ma nguong 200 ky tu cu vut di.

        File RONG HAN thi van bi tu choi, nhung o mot lop som hon: parser
        khong dung duoc luot thoai nao nen nem ValueError truoc khi toi
        cong B9. Chan o do con dut khoat hon.
        """
        ngan = "Khoi: xong phan mau roi\nHuy: minh lo phan lich\nKhoi: chot"
        outcome = run_ingest(
            Path("dung_nhanh.txt"), text=ngan, meta=_meta(), meeting_id="mtg_ngan"
        )
        codes = {w.code for w in outcome.report.warnings}
        assert "LOW_TEXT_VOLUME" in codes      # van canh bao
        assert not outcome.report.blocking      # nhung khong chan

    def test_file_rong_bi_tu_choi_o_lop_parser(self) -> None:
        with pytest.raises(ValueError):
            run_ingest(
                Path("rong.txt"), text="   ", meta=_meta(), meeting_id="mtg_rong"
            )

    def test_moc_thoi_gian_suy_ra_duoc_ghi_nhan(self) -> None:
        outcome = _ingest("plain_no_timestamp.txt")
        assert "SYNTHETIC_TIMESTAMPS" in {w.code for w in outcome.report.warnings}

    def test_vtt_that_khong_co_canh_bao_nao(self) -> None:
        """Đầu vào tốt phải đi qua sạch — cổng chất lượng không được kêu bừa."""
        outcome = _ingest("zoom_sprint23.vtt")
        assert outcome.report.warnings == []
        assert outcome.transcript.quality.overall_score == 1.0

    def test_khoang_lang_dai_duoc_phat_hien(self) -> None:
        text = (
            "WEBVTT\n\n00:00:00.000 --> 00:02:00.000\nHùng: phần đầu cuộc họp.\n\n"
            "00:05:00.000 --> 00:07:00.000\nTuấn: phần sau cuộc họp.\n\n"
            "00:07:10.000 --> 00:08:00.000\nLan: kết thúc.\n"
        )
        outcome = run_ingest(
            Path("gap.vtt"), text=text, meta=_meta(), meeting_id="mtg_test"
        )
        assert "LONG_SILENCE_GAPS" in {w.code for w in outcome.report.warnings}

    def test_diem_chat_luong_giam_theo_muc_nghiem_trong(self) -> None:
        tot = _ingest("zoom_sprint23.vtt")
        kem = _ingest("plain_no_timestamp.txt")
        assert tot.transcript.quality.overall_score > kem.transcript.quality.overall_score


# --------------------------------------------------------------------------- #
# Nối với các pha phía sau
# --------------------------------------------------------------------------- #


class TestPipelineHandoff:
    def test_s2_diarize_bo_qua_khi_da_co_ten(self) -> None:
        from pipeline.s2_diarize import run_diarize

        outcome = _ingest("zoom_sprint23.vtt")
        result = run_diarize(outcome.transcript)
        assert result.skipped is True

    def test_s3_chunk_nhan_duoc_transcript(self) -> None:
        from pipeline.s3_chunk import ChunkingPolicy, run_chunk

        outcome = _ingest("zoom_sprint23.vtt", policy=IngestPolicy(merge_gap_ms=0))
        chunking = run_chunk(outcome.transcript, ChunkingPolicy.from_quota(None))
        assert chunking.chunks
        covered = {sid for chunk in chunking.chunks for sid in chunk.segment_ids}
        assert covered == {s.id for s in outcome.transcript.segments}

    def test_moi_segment_deu_tro_ve_speaker_co_that(self) -> None:
        """Toàn vẹn tham chiếu — điều kiện để validator ở s7 chạy được."""
        for name in (
            "zoom_sprint23.vtt",
            "teams_standup.vtt",
            "meet_review.srt",
            "plain_planning.txt",
            "plain_no_timestamp.txt",
        ):
            outcome = _ingest(name)
            labels = {s.label for s in outcome.transcript.speakers}
            assert all(s.speaker_label in labels for s in outcome.transcript.segments)


# --------------------------------------------------------------------------- #
# Bảng mã file nguồn — lỗi crash thật đã gặp
# --------------------------------------------------------------------------- #


class TestSourceEncoding:
    """Zoom trên Windows đôi khi xuất VTT dạng UTF-16.

    Lỗi gốc: ``read_text(encoding="utf-8-sig")`` ném ``UnicodeDecodeError:
    invalid start byte`` ngay ở byte đầu tiên. Thông báo đó không gợi ý gì về
    nguyên nhân, nên người dùng đi nghi ngờ file hỏng trong khi file hoàn toàn
    bình thường — chỉ khác bảng mã.
    """

    SAMPLE = (
        "WEBVTT\n\n00:00:01.000 --> 00:00:20.000\n"
        "Hùng: Chào mọi người, mình bắt đầu cuộc họp nhé.\n\n"
        "00:00:21.000 --> 00:00:40.000\n"
        "Tuấn: Vâng anh, phần backend em đã deploy lên staging rồi ạ.\n"
    )

    @pytest.mark.parametrize(
        "encoding",
        ["utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "utf-32"],
    )
    def test_doc_dung_moi_bang_ma_pho_bien(self, encoding: str, tmp_path: Path) -> None:
        path = tmp_path / "zoom.vtt"
        path.write_bytes(self.SAMPLE.encode(encoding))

        outcome = run_ingest(path, meta=_meta(), meeting_id="mtg_test")
        names = {s.display_name for s in outcome.transcript.speakers}
        assert names == {"Hùng", "Tuấn"}
        assert "deploy lên staging" in outcome.transcript.segments[1].text

    def test_utf16_khong_bom_van_nhan_ra(self, tmp_path: Path) -> None:
        """Không bắt được ca này thì UTF-8 vẫn "thành công".

        Byte NUL là ký tự UTF-8 hợp lệ, nên chuỗi trả về đầy ký tự NUL xen kẽ,
        parser không tìm thấy cue nào, và lỗi hiện ra là "không đọc được lượt
        thoại" — sai hoàn toàn so với nguyên nhân thật.
        """
        path = tmp_path / "khong_bom.vtt"
        path.write_bytes(self.SAMPLE.encode("utf-16-le"))
        assert not path.read_bytes().startswith(b"\xff\xfe")

        _, used = read_source_text(path)
        assert "utf-16-le" in used
        assert len(run_ingest(path, meta=_meta(), meeting_id="m").transcript.segments) == 2

    def test_byte_rac_khong_lam_sap_chuong_trinh(self, tmp_path: Path) -> None:
        """latin-1 là lưới an toàn: mọi chuỗi byte đều giải mã được."""
        path = tmp_path / "rac.vtt"
        path.write_bytes(
            b"WEBVTT\n\n00:00:01.000 --> 00:00:20.000\n"
            b"Hung: noi dung co byte la \x81\x8d\x9d va van phai doc duoc\n"
        )
        outcome = run_ingest(path, meta=_meta(), meeting_id="m")
        assert outcome.transcript.segments

    def test_bao_cao_khi_bang_ma_khong_chac_chan(self, tmp_path: Path) -> None:
        path = tmp_path / "mo_ho.vtt"
        path.write_bytes(
            b"WEBVTT\n\n00:00:01.000 --> 00:00:20.000\n"
            b"Hung: byte la \x81\x8d o day\n\n"
            b"00:00:21.000 --> 00:00:30.000\nTuan: dong thu hai\n"
        )
        outcome = run_ingest(path, meta=_meta(), meeting_id="m")
        assert "UNCERTAIN_ENCODING" in {w.code for w in outcome.report.warnings}

    def test_bang_ma_dung_thi_khong_canh_bao_thua(self, tmp_path: Path) -> None:
        path = tmp_path / "sach.vtt"
        path.write_bytes(self.SAMPLE.encode("utf-16"))
        outcome = run_ingest(path, meta=_meta(), meeting_id="m")
        assert "UNCERTAIN_ENCODING" not in {w.code for w in outcome.report.warnings}


class TestReversedTimestamps:
    def test_moc_ket_thuc_truoc_moc_bat_dau_duoc_canh_bao(self, tmp_path: Path) -> None:
        """File nguồn hỏng mốc thời gian làm tỉ lệ nói bị tính thiếu.

        Trước đây ``end_ms`` bị âm thầm ép về ``start_ms``, segment thành
        thời lượng 0, và người nói đó biến mất khỏi thống kê talk time mà
        không có dấu hiệu gì.
        """
        text = "WEBVTT\n\n" + "\n\n".join(
            f"00:00:{i*10:02d}.000 --> 00:00:{i*10-5:02d}.000\n"
            f"Người{i}: nội dung của lượt thứ {i} trong cuộc họp này"
            for i in range(1, 6)
        )
        outcome = run_ingest(
            Path("nguoc.vtt"), text=text, meta=_meta(), meeting_id="m"
        )
        assert "ZERO_LENGTH_SEGMENTS" in {w.code for w in outcome.report.warnings}

# --------------------------------------------------------------------------- #


class TestTachNguoiNoi:
    """Bo tach nguoi noi - muc 8.3, van de 2.

    Ban truoc chi nhan hai kieu: the ``<v Ten>`` cua Teams va
    ``Ten: noi dung``. Moi kieu khac roi ve ``(None, text)``, nen
    ``speaker_count`` bi quy ve 1 va cong B9 chan ca file. Nghia la mot
    transcript binh thuong bi tu choi chi vi phan mem xuat no dung dau
    ``>>`` thay vi dau hai cham tran.

    Moi bai duoi day la mot kieu lay tu ban xuat that.
    """

    def test_teams_voice_span(self) -> None:
        assert _split_speaker("<v Khoi>xin chao moi nguoi</v>") == ("Khoi", "xin chao moi nguoi")

    def test_hai_cham_tran(self) -> None:
        assert _split_speaker("Khoi: xin chao") == ("Khoi", "xin chao")

    def test_kem_moc_thoi_gian_trong_ngoac(self) -> None:
        assert _split_speaker("Khoi (00:12:34): xin chao") == ("Khoi", "xin chao")

    def test_dau_mui_ten_kep_cua_zoom(self) -> None:
        assert _split_speaker(">> Khoi: xin chao") == ("Khoi", "xin chao")
        assert _split_speaker(">>> Khoi: xin chao") == ("Khoi", "xin chao")

    def test_ten_trong_ngoac_vuong(self) -> None:
        assert _split_speaker("[Khoi] xin chao") == ("Khoi", "xin chao")
        assert _split_speaker("[Khoi]: xin chao") == ("Khoi", "xin chao")

    def test_ten_trong_ngoac_don(self) -> None:
        assert _split_speaker("(Khoi) xin chao") == ("Khoi", "xin chao")

    def test_dang_danh_sach_co_gach_dau_dong(self) -> None:
        assert _split_speaker("- Khoi: xin chao") == ("Khoi", "xin chao")

    def test_gach_ngang_thay_hai_cham(self) -> None:
        assert _split_speaker("Khoi - toi nghi nen hoan") == ("Khoi", "toi nghi nen hoan")
        assert _split_speaker("Khoi — toi nghi nen hoan") == ("Khoi", "toi nghi nen hoan")

    def test_cau_thuong_co_gach_ngang_thi_KHONG_nhan_nham(self) -> None:
        """Gach ngang co mat khap noi trong cau, nen ve trai phai that su
        trong nhu ten: toi da bon tu, va co chu hoa."""
        cau = "chung ta nen chot phuong an nay - nhung con cho Huy tra loi"
        assert _split_speaker(cau) == (None, cau)

    def test_khong_co_ten_thi_tra_nguyen_cau(self) -> None:
        assert _split_speaker("chi la mot cau binh thuong") == (
            None, "chi la mot cau binh thuong")
