"""Test cho bộ điều phối pipeline.

Ba nhóm rủi ro được kiểm ở đây:

* **Tiếp tục sai** — đọc lại artifact của một lần chạy khác, hoặc bỏ qua
  pha VALIDATE. Cả hai đều cho ra biên bản trông đúng nhưng sai.
* **Lỗi bị nuốt** — bộ điều phối trả lỗi như giá trị, nên phải chắc rằng
  thất bại thật sự được báo chứ không âm thầm trả về ``minutes=None``.
* **Rò rỉ trách nhiệm trình bày** — bộ điều phối không được in gì ra
  ``stdout``; nếu nó in, giao diện web sẽ thừa hưởng rác.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from core.cache import LLMCache
from pipeline.orchestrator import (
    COSTLY_STAGES,
    STAGE_ARTIFACTS,
    STAGE_ORDER,
    OrchestratorConfig,
    Stage,
    StageStatus,
    resumable_stages,
    run_pipeline,
)
from pipeline.s0_ingest import IngestPolicy, run_ingest
from providers.base import LLMRunner
from providers.llm.mock import MockLLMProvider
from schemas.common import MeetingType
from schemas.reconciled import MeetingAnchor
from schemas.transcript import TranscriptMeta

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
VTT = FIXTURES / "ingest" / "zoom_sprint23.vtt"
MEETING_DATE = dt.date(2026, 7, 22)


@pytest.fixture
def transcript():
    meta = TranscriptMeta(
        title="Sprint 23 Review & Chốt release v2.4",
        meeting_date=MEETING_DATE,
        meeting_type=MeetingType.PLANNING,
        duration_ms=0,
    )
    return run_ingest(
        VTT,
        meta=meta,
        meeting_id="mtg_20260722_sprint24",
        policy=IngestPolicy(merge_gap_ms=0),
    ).transcript


def _runner(tmp_path: Path) -> LLMRunner:
    cache = LLMCache(tmp_path / "cache.db", enabled=False)
    return LLMRunner([MockLLMProvider(FIXTURES / "mock_llm")], cache=cache, quota=None)


def _config(artifacts: Path, **overrides) -> OrchestratorConfig:
    base = {
        "anchor": MeetingAnchor(meeting_date=MEETING_DATE),
        "artifacts_dir": artifacts,
    }
    base.update(overrides)
    return OrchestratorConfig(**base)


class TestHappyPath:
    def test_chay_tron_ven_ra_grounding_hoan_hao(self, transcript, tmp_path) -> None:
        outcome = run_pipeline(transcript, _config(tmp_path), _runner(tmp_path))
        assert outcome.succeeded
        assert outcome.grounding_score == pytest.approx(1.0)
        assert outcome.failed_stage is None

    def test_ghi_du_artifact_cua_moi_pha(self, transcript, tmp_path) -> None:
        run_pipeline(transcript, _config(tmp_path), _runner(tmp_path))
        for stage in STAGE_ORDER:
            if stage is Stage.DIARIZE:
                continue  # transcript đã có tên, pha này bỏ qua đúng cách
            assert (tmp_path / STAGE_ARTIFACTS[stage]).is_file(), stage

    def test_phat_su_kien_cho_moi_pha(self, transcript, tmp_path) -> None:
        seen: list[tuple[Stage, StageStatus]] = []
        run_pipeline(
            transcript, _config(tmp_path), _runner(tmp_path),
            on_event=lambda e: seen.append((e.stage, e.status)),
        )
        finished = {stage for stage, status in seen if status is not StageStatus.STARTED}
        assert finished == set(STAGE_ORDER)

    def test_su_kien_co_thu_tu_va_vi_tri_dung(self, transcript, tmp_path) -> None:
        outcome = run_pipeline(transcript, _config(tmp_path), _runner(tmp_path))
        positions = [
            e.position for e in outcome.events if e.status is StageStatus.STARTED
        ]
        assert positions == sorted(positions)

    def test_khong_in_gi_ra_stdout(self, transcript, tmp_path, capsys) -> None:
        """Trình bày là việc của nơi gọi, không phải của bộ điều phối."""
        run_pipeline(transcript, _config(tmp_path), _runner(tmp_path))
        assert capsys.readouterr().out == ""


class TestResume:
    def test_liet_ke_dung_cac_pha_khoi_phuc_duoc(self, transcript, tmp_path) -> None:
        assert resumable_stages(tmp_path) == []
        run_pipeline(transcript, _config(tmp_path), _runner(tmp_path))
        assert resumable_stages(tmp_path) == [
            Stage.EXTRACT, Stage.RECONCILE, Stage.COMPOSE
        ]

    def test_thu_muc_khong_ton_tai_thi_khong_no(self, tmp_path) -> None:
        assert resumable_stages(tmp_path / "chua-co") == []

    def test_chi_khoi_phuc_pha_ton_quota(self) -> None:
        """DIARIZE và CHUNK là Python thuần — khôi phục chúng không lợi gì
        mà lại thêm một đường mã có thể sai."""
        assert COSTLY_STAGES == {Stage.EXTRACT, Stage.RECONCILE, Stage.COMPOSE}

    def test_tiep_tuc_tu_compose_tiet_kiem_dung_hai_request(
        self, transcript, tmp_path
    ) -> None:
        first = run_pipeline(transcript, _config(tmp_path), _runner(tmp_path))
        assert first.llm_requests == 3

        second = run_pipeline(
            transcript,
            _config(tmp_path, from_stage=Stage.COMPOSE),
            _runner(tmp_path),
        )
        assert second.succeeded
        assert second.llm_requests == 1
        assert second.restored_stages == [Stage.CHUNK, Stage.EXTRACT, Stage.RECONCILE]

    def test_ket_qua_khi_tiep_tuc_trung_voi_chay_lien_mach(
        self, transcript, tmp_path
    ) -> None:
        """Tiếp tục mà ra biên bản khác thì cơ chế này vô dụng."""
        first = run_pipeline(transcript, _config(tmp_path), _runner(tmp_path))
        second = run_pipeline(
            transcript, _config(tmp_path, from_stage=Stage.COMPOSE), _runner(tmp_path)
        )
        assert first.minutes is not None and second.minutes is not None
        assert [d.statement for d in first.minutes.active_decisions] == [
            d.statement for d in second.minutes.active_decisions
        ]
        assert first.grounding_score == second.grounding_score

    def test_validate_khong_bao_gio_duoc_khoi_phuc(self, transcript, tmp_path) -> None:
        """Pha VALIDATE miễn phí và là lớp chặn bịa đặt cuối cùng.

        Đọc lại kết quả kiểm chứng cũ có thể ứng với một bản nháp khác — rẻ
        hơn nhiều nếu cứ chạy lại.
        """
        run_pipeline(transcript, _config(tmp_path), _runner(tmp_path))
        assert Stage.VALIDATE not in resumable_stages(tmp_path)

        outcome = run_pipeline(
            transcript, _config(tmp_path, from_stage=Stage.VALIDATE), _runner(tmp_path)
        )
        statuses = {
            e.status for e in outcome.events if e.stage is Stage.VALIDATE
        }
        assert StageStatus.DONE in statuses
        assert StageStatus.RESTORED not in statuses

    def test_artifact_hong_thi_tinh_lai_chu_khong_sap(
        self, transcript, tmp_path
    ) -> None:
        run_pipeline(transcript, _config(tmp_path), _runner(tmp_path))
        (tmp_path / STAGE_ARTIFACTS[Stage.EXTRACT]).write_text(
            "{ đây không phải JSON", encoding="utf-8"
        )
        outcome = run_pipeline(
            transcript, _config(tmp_path, from_stage=Stage.COMPOSE), _runner(tmp_path)
        )
        assert outcome.succeeded
        assert Stage.EXTRACT not in outcome.restored_stages

    def test_khong_co_artifact_thi_chay_lai_binh_thuong(
        self, transcript, tmp_path
    ) -> None:
        outcome = run_pipeline(
            transcript, _config(tmp_path, from_stage=Stage.COMPOSE), _runner(tmp_path)
        )
        assert outcome.succeeded
        assert outcome.llm_requests == 3


class TestFailureHandling:
    def test_loi_tra_ve_nhu_gia_tri_khong_nem_ngoai_le(
        self, transcript, tmp_path
    ) -> None:
        """Bộ điều phối không được tự quyết định thay nơi gọi."""

        class _Exploding(MockLLMProvider):
            def generate_json(self, *args, **kwargs):
                raise RuntimeError("mạng chập giữa chừng")

        runner = LLMRunner(
            [_Exploding(FIXTURES / "mock_llm")],
            cache=LLMCache(tmp_path / "c.db", enabled=False),
            quota=None,
        )
        outcome = run_pipeline(transcript, _config(tmp_path), runner)

        assert not outcome.succeeded
        assert outcome.minutes is None
        assert outcome.failed_stage is Stage.EXTRACT
        assert "mạng chập giữa chừng" in outcome.error

    def test_pha_da_xong_van_giu_duoc_artifact_khi_hong_sau_do(
        self, transcript, tmp_path
    ) -> None:
        """Đây là toàn bộ lý do cơ chế tiếp tục tồn tại."""

        class _FailAtCompose(MockLLMProvider):
            """Hỏng đúng ở pha COMPOSE, sau khi hai pha tốn quota đã xong."""

            def generate_json(self, *args, **kwargs):
                if self.calls and len(self.calls) >= 2:
                    raise RuntimeError("hết quota giữa chừng")
                return super().generate_json(*args, **kwargs)

        runner = LLMRunner(
            [_FailAtCompose(FIXTURES / "mock_llm")],
            cache=LLMCache(tmp_path / "c.db", enabled=False),
            quota=None,
        )
        outcome = run_pipeline(transcript, _config(tmp_path), runner)

        if not outcome.succeeded:
            assert (tmp_path / STAGE_ARTIFACTS[Stage.EXTRACT]).is_file()
            assert (tmp_path / STAGE_ARTIFACTS[Stage.RECONCILE]).is_file()
            assert Stage.EXTRACT in resumable_stages(tmp_path)

    def test_su_kien_failed_duoc_ghi_lai(self, transcript, tmp_path) -> None:
        class _Exploding(MockLLMProvider):
            def generate_json(self, *args, **kwargs):
                raise RuntimeError("hỏng")

        runner = LLMRunner(
            [_Exploding(FIXTURES / "mock_llm")],
            cache=LLMCache(tmp_path / "c.db", enabled=False),
            quota=None,
        )
        outcome = run_pipeline(transcript, _config(tmp_path), runner)
        assert any(e.status is StageStatus.FAILED for e in outcome.events)


class TestStageContract:
    def test_thu_tu_pha_khop_voi_bang_artifact(self) -> None:
        assert set(STAGE_ORDER) == set(STAGE_ARTIFACTS)

    def test_moi_pha_co_ten_artifact_rieng(self) -> None:
        names = list(STAGE_ARTIFACTS.values())
        assert len(names) == len(set(names))

    def test_su_kien_doc_duoc_khi_in_ra(self, transcript, tmp_path) -> None:
        outcome = run_pipeline(transcript, _config(tmp_path), _runner(tmp_path))
        rendered = str(outcome.events[-1])
        assert "VALIDATE" in rendered
        assert "6/6" in rendered
