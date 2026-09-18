"""Kiểm thử nhận diện danh tính người nói qua xưng hô tiếng Việt.

Toàn bộ chạy offline, không gọi API, không tốn quota.
"""

from __future__ import annotations

from typing import Any

import pytest

from nlp.vocative import (
    SpeakerVotes,
    assign_speakers,
    collect_votes,
    detect_mentions,
)


def seg(index: int, label: str, text: str) -> dict[str, Any]:
    return {
        "id": f"s_{index:04d}",
        "index": index,
        "speaker_label": label,
        "text": text,
    }


@pytest.fixture(scope="module")
def meeting() -> list[dict[str, Any]]:
    """Trích đoạn cuộc họp mẫu, giữ nguyên cấu trúc lượt nói thật."""
    return [
        seg(1, "SPEAKER_00", "Ok mọi người mình bắt đầu nhé."),
        seg(2, "SPEAKER_00", "Anh Tuấn cập nhật giúp em phần backend trước đi."),
        seg(3, "SPEAKER_01", "Ừ, phần API thanh toán thì anh merge xong rồi."),
        seg(4, "SPEAKER_00", "Ok. Chị Lan bên QA thì sao ạ?"),
        seg(5, "SPEAKER_02", "Bên chị test được khoảng 70% test case rồi."),
        seg(6, "SPEAKER_03", "Em confirm là bên mobile build xong bản RC rồi."),
        seg(7, "SPEAKER_02", "Khoan anh Hùng ơi, cuối tuần này thì chị không kịp."),
        seg(8, "SPEAKER_01", "Anh cũng nghĩ vậy."),
        seg(9, "SPEAKER_00", "Ừ thôi được rồi, mình lùi lại vậy."),
    ]


# --------------------------------------------------------------------------- #
# Dò tên
# --------------------------------------------------------------------------- #


class TestDetectMentions:
    def test_finds_vocative_names(self, meeting: list[dict[str, Any]]) -> None:
        names = [m.name for m in detect_mentions(meeting)]
        assert "Tuấn" in names
        assert "Lan" in names
        assert "Hùng" in names

    def test_records_who_said_it_and_where(self, meeting: list[dict[str, Any]]) -> None:
        mention = next(m for m in detect_mentions(meeting) if m.name == "Tuấn")
        assert mention.speaker_label == "SPEAKER_00"
        assert mention.segment_id == "s_0002"
        assert mention.kind == "vocative"

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Anh Tuấn cho ý kiến", "Tuấn"),
            ("Chị Lan bên QA thì sao ạ?", "Lan"),
            ("Sếp Hùng duyệt giúp em", "Hùng"),
            ("Em Minh làm phần này nhé", "Minh"),
            ("Bạn Hương gửi báo cáo chưa?", "Hương"),
            ("Cô Nguyễn Thị Mai phụ trách", "Nguyễn Thị Mai"),
        ],
    )
    def test_honorific_patterns(self, text: str, expected: str) -> None:
        mentions = detect_mentions([seg(1, "SPEAKER_00", text)])
        assert [m.name for m in mentions] == [expected]

    @pytest.mark.parametrize(
        "text",
        [
            "anh em mình cùng làm nhé",
            "các bạn cho ý kiến đi",
            "chị ấy nói vậy rồi",
            "anh không đồng ý đâu",
            "em cũng nghĩ thế",
            "bạn nào xung phong không",
        ],
    )
    def test_ignores_pronouns_without_names(self, text: str) -> None:
        """Không phải cứ sau "anh/chị/em" là tên riêng.

        Thiếu bước lọc này thì "anh em", "các bạn", "chị ấy" đều bị nhận nhầm
        thành người tham dự.
        """
        assert detect_mentions([seg(1, "SPEAKER_00", text)]) == []

    def test_ignores_uppercase_acronyms(self) -> None:
        """"anh QA" không phải tên người."""
        assert detect_mentions([seg(1, "SPEAKER_00", "anh QA kiểm tra giúp")]) == []

    def test_detects_self_introduction(self) -> None:
        mentions = detect_mentions([seg(1, "SPEAKER_02", "Em là Minh bên mobile")])
        assert len(mentions) == 1
        assert mentions[0].name == "Minh"
        assert mentions[0].kind == "self_intro"

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Em là Minh", "Minh"),
            ("Mình tên là Hương", "Hương"),
            ("Tôi tên Dũng", "Dũng"),
        ],
    )
    def test_self_introduction_variants(self, text: str, expected: str) -> None:
        mentions = detect_mentions([seg(1, "SPEAKER_00", text)])
        assert any(m.name == expected and m.kind == "self_intro" for m in mentions)

    def test_known_names_filter_removes_strangers(
        self, meeting: list[dict[str, Any]]
    ) -> None:
        """Biết trước danh sách tham dự thì mọi tên lạ bị loại ngay."""
        mentions = detect_mentions(meeting, known_names=["Tuấn", "Lan"])
        assert {m.name for m in mentions} == {"Tuấn", "Lan"}

    def test_preserves_vietnamese_diacritics(self) -> None:
        mentions = detect_mentions([seg(1, "SPEAKER_00", "Anh Tuấn ơi")])
        assert mentions[0].name == "Tuấn"


# --------------------------------------------------------------------------- #
# Bỏ phiếu
# --------------------------------------------------------------------------- #


class TestVoting:
    def test_addressee_gets_positive_vote(
        self, meeting: list[dict[str, Any]]
    ) -> None:
        votes = collect_votes(meeting, detect_mentions(meeting))
        assert votes["SPEAKER_01"].scores.get("Tuấn", 0) > 0

    def test_speaker_gets_negative_vote_for_name_they_said(
        self, meeting: list[dict[str, Any]]
    ) -> None:
        """Người gọi tên X thì không phải X — phiếu chống này hiếm khi sai."""
        votes = collect_votes(meeting, detect_mentions(meeting))
        assert votes["SPEAKER_00"].scores.get("Tuấn", 0) < 0
        assert votes["SPEAKER_00"].is_ruled_out("Tuấn")

    def test_self_introduction_outweighs_being_addressed(self) -> None:
        segments = [
            seg(1, "SPEAKER_00", "Ai làm phần này?"),
            seg(2, "SPEAKER_01", "Em là Minh, em nhận ạ"),
        ]
        votes = collect_votes(segments, detect_mentions(segments))
        assert votes["SPEAKER_01"].scores["Minh"] >= 5.0

    def test_vote_reaches_speaker_who_replies_late(self) -> None:
        """Người được gọi tên không phải lúc nào cũng đáp ngay lượt sau.

        Trong cuộc họp thật thường có người chen vào trước, nên phiếu phải
        được rải qua vài lượt chứ không dồn hết cho lượt liền kề.
        """
        segments = [
            seg(1, "SPEAKER_02", "Khoan anh Hùng ơi, em chưa kịp."),
            seg(2, "SPEAKER_01", "Anh cũng nghĩ vậy."),
            seg(3, "SPEAKER_00", "Ừ thôi được rồi."),
        ]
        votes = collect_votes(segments, detect_mentions(segments))
        assert votes["SPEAKER_00"].scores.get("Hùng", 0) > 0

    def test_margin_reflects_competition(self) -> None:
        vote = SpeakerVotes(label="SPEAKER_00")
        vote.add("Tuấn", 5.0)
        vote.add("Lan", 4.5)
        assert vote.margin() == pytest.approx(0.5)


# --------------------------------------------------------------------------- #
# Ghép cặp
# --------------------------------------------------------------------------- #


class TestAssignment:
    def test_assigns_all_speakers_with_attendee_list(
        self, meeting: list[dict[str, Any]]
    ) -> None:
        result = assign_speakers(
            meeting, known_names=["Hùng", "Tuấn", "Lan", "Minh"]
        )
        assert result.assignments == {
            "SPEAKER_00": "Hùng",
            "SPEAKER_01": "Tuấn",
            "SPEAKER_02": "Lan",
            "SPEAKER_03": "Minh",
        }
        assert result.unresolved == []

    def test_stays_conservative_without_attendee_list(
        self, meeting: list[dict[str, Any]]
    ) -> None:
        """Không biết trước danh sách thì chỉ gán những gì thật chắc chắn.

        Thà để nguyên nhãn thô còn hơn gán nhầm người cho một cam kết.
        """
        result = assign_speakers(meeting)
        for label, name in result.assignments.items():
            assert name in {"Hùng", "Tuấn", "Lan", "Minh"}
        assert result.unresolved

    def test_never_assigns_one_name_to_two_speakers(
        self, meeting: list[dict[str, Any]]
    ) -> None:
        result = assign_speakers(meeting, known_names=["Hùng", "Tuấn", "Lan", "Minh"])
        names = list(result.assignments.values())
        assert len(names) == len(set(names))

    def test_records_evidence_for_each_assignment(
        self, meeting: list[dict[str, Any]]
    ) -> None:
        """Mọi phép gán phải truy được về segment cụ thể, trừ suy luận loại trừ."""
        result = assign_speakers(meeting, known_names=["Hùng", "Tuấn", "Lan", "Minh"])
        for label, method in result.methods.items():
            if method != "attendee_list_elimination":
                assert result.evidence[label], f"{label} không có dẫn chứng"

    def test_elimination_has_lower_confidence(
        self, meeting: list[dict[str, Any]]
    ) -> None:
        """Suy luận gián tiếp phải được đánh dấu kém tin cậy hơn bằng chứng thật."""
        result = assign_speakers(meeting, known_names=["Hùng", "Tuấn", "Lan", "Minh"])
        by_elimination = [
            label
            for label, method in result.methods.items()
            if method == "attendee_list_elimination"
        ]
        for label in by_elimination:
            assert result.confidences[label] < 0.80

    def test_confidence_never_claims_certainty(
        self, meeting: list[dict[str, Any]]
    ) -> None:
        """Đây là suy luận gián tiếp, không phải nhận dạng giọng nói."""
        result = assign_speakers(meeting, known_names=["Hùng", "Tuấn", "Lan", "Minh"])
        assert all(value <= 0.95 for value in result.confidences.values())

    def test_empty_transcript_returns_empty_result(self) -> None:
        result = assign_speakers([])
        assert result.assignments == {}
        assert result.unresolved == []

    def test_transcript_without_names_resolves_nothing(self) -> None:
        segments = [
            seg(1, "SPEAKER_00", "Mình bắt đầu nhé."),
            seg(2, "SPEAKER_01", "Vâng ạ."),
        ]
        result = assign_speakers(segments)
        assert result.assignments == {}
        assert set(result.unresolved) == {"SPEAKER_00", "SPEAKER_01"}

    def test_self_introduction_is_assigned_directly(self) -> None:
        segments = [
            seg(1, "SPEAKER_00", "Xin chào mọi người."),
            seg(2, "SPEAKER_01", "Em là Minh bên mobile ạ."),
        ]
        result = assign_speakers(segments)
        assert result.assignments["SPEAKER_01"] == "Minh"
        assert result.methods["SPEAKER_01"] == "self_intro"

    def test_is_deterministic(self, meeting: list[dict[str, Any]]) -> None:
        """Cùng đầu vào phải cho cùng kết quả — pipeline phải tái lập được."""
        first = assign_speakers(meeting, known_names=["Hùng", "Tuấn", "Lan", "Minh"])
        for _ in range(4):
            again = assign_speakers(
                meeting, known_names=["Hùng", "Tuấn", "Lan", "Minh"]
            )
            assert again.assignments == first.assignments
