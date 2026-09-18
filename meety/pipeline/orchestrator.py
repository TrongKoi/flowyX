"""Bộ điều phối pipeline — chạy các pha, phát sự kiện, tiếp tục từ dở dang.

Vì sao tách khỏi ``main.py``
----------------------------
Trước module này, toàn bộ việc điều phối nằm trong ``run_pipeline()`` của
``main.py``, trộn lẫn ba trách nhiệm khác nhau:

* quyết định chạy pha nào theo thứ tự nào,
* ghi artifact ra đĩa,
* **in kết quả ra màn hình và gọi** ``SystemExit``.

Trách nhiệm thứ ba làm cho hàm đó không dùng lại được. Một giao diện web
không thể gọi một hàm in ra ``stdout`` rồi kết thúc tiến trình; nó cần một
lời gọi trả về dữ liệu, báo tiến độ trong lúc chạy, và trả lỗi như một giá
trị chứ không phải như một ngoại lệ làm sập tiến trình.

Module này giữ lại đúng hai trách nhiệm đầu. Nó **không in gì cả**. Nơi gọi
tự quyết định trình bày ra sao — CLI in ra terminal, web đẩy qua websocket,
test thì chỉ đọc danh sách sự kiện.

Vì sao có cơ chế tiếp tục từ dở dang
------------------------------------
Ba pha tốn quota (EXTRACT, RECONCILE, COMPOSE) chạy nối tiếp. Khi COMPOSE
hỏng vì mạng chập hoặc chạm trần RPM, hai pha trước đã tốn quota rồi. Bộ nhớ
đệm che được phần lớn trường hợp đó, nhưng chỉ khi prompt trùng khít từng
byte — mà chỉ cần sửa một chữ trong prompt là hỏng.

Artifact theo pha vốn đã được ghi ra đĩa từ trước. Cơ chế ở đây chỉ đơn giản
là *đọc lại chúng* thay vì tính lại: rẻ, không thêm trạng thái mới, và
không có gì để đồng bộ hoá sai.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pipeline.s2_diarize import AttendeeHint, run_diarize
from pipeline.s3_chunk import ChunkingPolicy, run_chunk
from pipeline.s4_extract import run_extract
from pipeline.s5_reconcile import run_reconcile
from pipeline.s6_compose import run_compose
from pipeline.s7_validate import run_validate
from providers.base import LLMRunner
from schemas.extraction import ChunkExtraction
from schemas.minutes import PipelineInfo, StructuredMinutes
from schemas.reconciled import MeetingAnchor, ReconciledFacts
from schemas.transcript import Transcript

logger = logging.getLogger(__name__)

__all__ = [
    "Stage",
    "StageStatus",
    "StageEvent",
    "OrchestratorConfig",
    "RunOutcome",
    "STAGE_ORDER",
    "STAGE_ARTIFACTS",
    "resumable_stages",
    "run_pipeline",
]


class Stage(str, Enum):
    """Các pha của pipeline, theo đúng thứ tự thực thi."""

    DIARIZE = "diarize"
    CHUNK = "chunk"
    EXTRACT = "extract"
    RECONCILE = "reconcile"
    COMPOSE = "compose"
    VALIDATE = "validate"


STAGE_ORDER: tuple[Stage, ...] = (
    Stage.DIARIZE,
    Stage.CHUNK,
    Stage.EXTRACT,
    Stage.RECONCILE,
    Stage.COMPOSE,
    Stage.VALIDATE,
)

STAGE_ARTIFACTS: dict[Stage, str] = {
    Stage.DIARIZE: "transcript_diarized.json",
    Stage.CHUNK: "transcript_chunked.json",
    Stage.EXTRACT: "extract.json",
    Stage.RECONCILE: "reconciled.json",
    Stage.COMPOSE: "minutes_draft.json",
    Stage.VALIDATE: "minutes_final.json",
}
"""Artifact mà mỗi pha ghi ra. Đây cũng là thứ dùng để tiếp tục từ dở dang."""

COSTLY_STAGES: frozenset[Stage] = frozenset(
    {Stage.EXTRACT, Stage.RECONCILE, Stage.COMPOSE}
)
"""Các pha có gọi LLM. Chỉ những pha này mới đáng để khôi phục."""


class StageStatus(str, Enum):
    STARTED = "started"
    DONE = "done"
    SKIPPED = "skipped"
    RESTORED = "restored"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class StageEvent:
    """Một mốc trong quá trình chạy, để nơi gọi hiển thị tiến độ."""

    stage: Stage
    status: StageStatus
    message: str = ""
    elapsed_ms: int = 0
    detail: dict[str, Any] = field(default_factory=dict)

    @property
    def position(self) -> int:
        return STAGE_ORDER.index(self.stage) + 1

    def __str__(self) -> str:
        return (
            f"[{self.position}/{len(STAGE_ORDER)}] {self.stage.value.upper()} "
            f"{self.status.value}: {self.message}"
        )


@dataclass(frozen=True, slots=True)
class OrchestratorConfig:
    """Tham số điều khiển một lần chạy.

    Cố ý KHÔNG tái dùng ``RunConfig`` của ``main.py``: cấu hình đó chứa cả
    thứ chỉ CLI mới quan tâm (định dạng xuất, thư mục kết quả, cờ in ấn).
    Giữ hai kiểu riêng khiến bộ điều phối không bị kéo ngược về phụ thuộc
    vào giao diện dòng lệnh.
    """

    anchor: MeetingAnchor
    artifacts_dir: Path
    attendees: Sequence[AttendeeHint] = ()
    skip_diarize: bool = False
    max_chunk_tokens: int = 120_000
    pace_seconds: float = 0.0
    rpd_remaining: int | None = None
    from_stage: Stage | None = None
    prompt_versions: dict[str, str] = field(
        default_factory=lambda: {
            "extract": "extract.vi.v1.2",
            "reconcile": "reconcile.vi.v1.1",
            "compose": "compose.vi.v1.0",
        }
    )


@dataclass(slots=True)
class RunOutcome:
    """Kết quả một lần chạy — thành công hay thất bại đều trả về kiểu này.

    Lỗi là **giá trị trả về**, không phải ngoại lệ. Nơi gọi quyết định xử lý
    ra sao: CLI in ra rồi thoát với mã lỗi, web ghi vào bản ghi job và trả
    HTTP 500. Nếu bộ điều phối tự ném ngoại lệ ra ngoài thì nó đã thay nơi
    gọi quyết định mất rồi.
    """

    transcript: Transcript
    minutes: StructuredMinutes | None = None
    events: list[StageEvent] = field(default_factory=list)
    failed_stage: Stage | None = None
    error: str | None = None
    llm_requests: int = 0
    token_estimate: int = 0
    restored_stages: list[Stage] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.minutes is not None and self.failed_stage is None

    @property
    def grounding_score(self) -> float | None:
        if self.minutes is None or self.minutes.validation is None:
            return None
        return self.minutes.validation.grounding_score


EventSink = Callable[[StageEvent], None]


def resumable_stages(artifacts_dir: Path) -> list[Stage]:
    """Liệt kê các pha tốn quota đã có artifact trên đĩa.

    Chỉ xét các pha trong ``COSTLY_STAGES``: khôi phục DIARIZE hay CHUNK
    không tiết kiệm được gì (chúng là Python thuần, chạy hết vài mili giây)
    mà lại thêm một đường mã có thể sai.
    """
    if not artifacts_dir.is_dir():
        return []
    return [
        stage
        for stage in STAGE_ORDER
        if stage in COSTLY_STAGES and (artifacts_dir / STAGE_ARTIFACTS[stage]).is_file()
    ]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, model: Any) -> None:
    _save_raw(path, model.model_dump(mode="json"))


def _save_raw(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class _Recorder:
    """Gom sự kiện và chuyển tiếp cho nơi gọi."""

    def __init__(self, sink: EventSink | None) -> None:
        self.events: list[StageEvent] = []
        self._sink = sink
        self._started_at = 0.0

    def start(self, stage: Stage) -> None:
        self._started_at = time.monotonic()
        self._emit(StageEvent(stage, StageStatus.STARTED))

    def finish(
        self,
        stage: Stage,
        status: StageStatus,
        message: str = "",
        **detail: Any,
    ) -> None:
        elapsed = int((time.monotonic() - self._started_at) * 1000)
        self._emit(StageEvent(stage, status, message, elapsed, detail))

    def _emit(self, event: StageEvent) -> None:
        self.events.append(event)
        logger.info("%s", event)
        if self._sink is not None:
            self._sink(event)


def run_pipeline(
    transcript: Transcript,
    config: OrchestratorConfig,
    runner: LLMRunner,
    *,
    on_event: EventSink | None = None,
) -> RunOutcome:
    """Chạy các pha 2–7 trên một transcript đã nạp sẵn.

    Pha nạp dữ liệu (s0/s1) cố ý nằm ngoài: nó phụ thuộc định dạng đầu vào
    và, với đường audio, tiêu quota của một nhà cung cấp khác. Nơi gọi nạp
    transcript rồi đưa vào đây.

    Args:
        transcript: Transcript đã chuẩn hoá.
        config: Tham số điều khiển.
        runner: Bộ chạy LLM đã gắn cache và sổ cái quota.
        on_event: Hàm nhận sự kiện tiến độ, gọi đồng bộ trong lúc chạy.

    Returns:
        ``RunOutcome``. Kiểm tra ``succeeded`` trước khi đọc ``minutes``.
    """
    recorder = _Recorder(on_event)
    artifacts = config.artifacts_dir
    artifacts.mkdir(parents=True, exist_ok=True)

    outcome = RunOutcome(transcript=transcript, events=recorder.events)
    resume_from = config.from_stage
    skip_until = STAGE_ORDER.index(resume_from) if resume_from else 0

    extractions: list[ChunkExtraction] | None = None
    facts: ReconciledFacts | None = None
    draft: StructuredMinutes | None = None

    try:
        # -- Pha 2: gán tên người nói (Python thuần, 0 quota) -------------- #
        if skip_until <= STAGE_ORDER.index(Stage.DIARIZE):
            recorder.start(Stage.DIARIZE)
            if config.skip_diarize:
                recorder.finish(Stage.DIARIZE, StageStatus.SKIPPED, "bỏ qua theo yêu cầu")
            else:
                result = run_diarize(transcript, attendees=config.attendees)
                transcript = result.transcript
                if not result.skipped:
                    _save(artifacts / STAGE_ARTIFACTS[Stage.DIARIZE], transcript)
                recorder.finish(
                    Stage.DIARIZE,
                    StageStatus.SKIPPED if result.skipped else StageStatus.DONE,
                    result.summary(),
                    named=sum(1 for s in transcript.speakers if s.display_name),
                )

        # -- Pha 3: chia chunk theo quota còn lại (Python thuần) ----------- #
        if skip_until <= STAGE_ORDER.index(Stage.CHUNK):
            recorder.start(Stage.CHUNK)
            chunking = run_chunk(
                transcript,
                ChunkingPolicy.from_quota(
                    config.rpd_remaining, max_tokens_per_chunk=config.max_chunk_tokens
                ),
            )
            transcript = transcript.model_copy(update={"chunks": chunking.chunks})
            _save(artifacts / STAGE_ARTIFACTS[Stage.CHUNK], transcript)
            recorder.finish(
                Stage.CHUNK,
                StageStatus.DONE,
                f"{len(chunking.chunks)} chunk",
                chunks=len(chunking.chunks),
            )
        else:
            path = artifacts / STAGE_ARTIFACTS[Stage.CHUNK]
            if path.is_file():
                recorder.start(Stage.CHUNK)
                transcript = Transcript.model_validate(_load_json(path))
                recorder.finish(Stage.CHUNK, StageStatus.RESTORED, path.name)
                outcome.restored_stages.append(Stage.CHUNK)

        outcome.transcript = transcript

        # -- Pha 4: trích xuất theo chunk (TỐN QUOTA) --------------------- #
        recorder.start(Stage.EXTRACT)
        restored = _restore_extract(artifacts) if skip_until > STAGE_ORDER.index(Stage.EXTRACT) else None
        if restored is not None:
            extractions = restored
            outcome.restored_stages.append(Stage.EXTRACT)
            recorder.finish(
                Stage.EXTRACT, StageStatus.RESTORED,
                f"{len(extractions)} chunk, tiết kiệm {len(extractions)} request",
            )
        else:
            extraction = run_extract(
                transcript, config.anchor, runner, pace_seconds=config.pace_seconds
            )
            extractions = extraction.extractions
            _save_raw(
                artifacts / STAGE_ARTIFACTS[Stage.EXTRACT],
                [e.model_dump(mode="json") for e in extractions],
            )
            recorder.finish(
                Stage.EXTRACT, StageStatus.DONE,
                f"{extraction.total_items} mục, loại {len(extraction.dropped_items)} "
                "mục thiếu bằng chứng hợp lệ",
                items=extraction.total_items,
                dropped=len(extraction.dropped_items),
            )

        # -- Pha 5: đối chiếu, khử trùng lặp, supersession (TỐN QUOTA) ----- #
        recorder.start(Stage.RECONCILE)
        path = artifacts / STAGE_ARTIFACTS[Stage.RECONCILE]
        if skip_until > STAGE_ORDER.index(Stage.RECONCILE) and path.is_file():
            facts = ReconciledFacts.model_validate(_load_json(path))
            outcome.restored_stages.append(Stage.RECONCILE)
            recorder.finish(Stage.RECONCILE, StageStatus.RESTORED, path.name)
        else:
            facts = run_reconcile(extractions, transcript, config.anchor, runner)
            _save(path, facts)
            recorder.finish(
                Stage.RECONCILE, StageStatus.DONE,
                f"{len(facts.decisions)} quyết định, {len(facts.action_items)} công việc",
                decisions=len(facts.decisions), actions=len(facts.action_items),
            )

        # -- Pha 6: viết văn xuôi (TỐN QUOTA) ----------------------------- #
        recorder.start(Stage.COMPOSE)
        path = artifacts / STAGE_ARTIFACTS[Stage.COMPOSE]
        if skip_until > STAGE_ORDER.index(Stage.COMPOSE) and path.is_file():
            draft = StructuredMinutes.model_validate(_load_json(path))
            outcome.restored_stages.append(Stage.COMPOSE)
            recorder.finish(Stage.COMPOSE, StageStatus.RESTORED, path.name)
        else:
            draft = run_compose(
                facts, transcript, runner,
                pipeline_info=PipelineInfo(
                    asr_provider=transcript.provider.asr,
                    llm_provider=runner.providers[0].key,
                    prompt_versions=dict(config.prompt_versions),
                    total_llm_requests=runner.request_count,
                    total_tokens_estimate=runner.token_count,
                    cost_usd=0.0,
                ),
            )
            _save(path, draft)
            recorder.finish(Stage.COMPOSE, StageStatus.DONE, "đã viết văn xuôi")

        # -- Pha 7: kiểm chứng (Python thuần, 0 quota) -------------------- #
        # KHÔNG BAO GIỜ khôi phục pha này. Nó miễn phí, tất định, và là lớp
        # bảo vệ cuối cùng chống bịa đặt — chạy lại luôn rẻ hơn là tin vào
        # một kết quả kiểm chứng cũ có thể ứng với bản nháp khác.
        recorder.start(Stage.VALIDATE)
        validated = run_validate(draft, transcript)
        _save(artifacts / STAGE_ARTIFACTS[Stage.VALIDATE], validated.minutes)
        recorder.finish(
            Stage.VALIDATE, StageStatus.DONE,
            f"grounding={validated.minutes.validation.grounding_score:.2f}"
            if validated.minutes.validation
            else "đã kiểm chứng",
        )

        outcome.minutes = validated.minutes

    except Exception as exc:  # noqa: BLE001 — lỗi là giá trị trả về, không phải ngoại lệ
        stage = _current_stage(recorder.events)
        outcome.failed_stage = stage
        outcome.error = f"{type(exc).__name__}: {exc}"
        recorder.finish(stage, StageStatus.FAILED, outcome.error)
        logger.exception("Pipeline hỏng ở pha %s", stage.value)

    outcome.llm_requests = runner.request_count
    outcome.token_estimate = runner.token_count
    return outcome


def _current_stage(events: Sequence[StageEvent]) -> Stage:
    for event in reversed(events):
        if event.status is StageStatus.STARTED:
            return event.stage
    return STAGE_ORDER[0]


def _restore_extract(artifacts: Path) -> list[ChunkExtraction] | None:
    path = artifacts / STAGE_ARTIFACTS[Stage.EXTRACT]
    if not path.is_file():
        return None
    try:
        payload = _load_json(path)
        return [ChunkExtraction.model_validate(item) for item in payload]
    except Exception as exc:  # noqa: BLE001
        # Artifact hỏng thì tính lại, đừng làm sập cả lần chạy. Tốn quota còn
        # hơn là dừng hẳn khi người dùng đang cần kết quả.
        logger.warning("Không đọc được %s (%s), sẽ tính lại pha EXTRACT.", path.name, exc)
        return None
