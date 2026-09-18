#!/usr/bin/env python3
"""CLI cho Hệ thống Tóm tắt Cuộc họp — bản POC 0 đồng.

Ví dụ dùng
----------
Chạy offline trên transcript mẫu, không tốn quota, không cần API key::

    python main.py --input tests/fixtures/sample_transcript.json \\
                   --skip-stt --date 2026-07-22 --mock

Chạy thật với Gemini trên transcript có sẵn::

    python main.py --input transcript.json --skip-stt --date 2026-07-22

Chạy từ transcript Zoom/Meet/Teams tải về (không tốn quota Groq, có sẵn tên
người nói)::

    python main.py --input GMT20260722-140000_Recording.vtt --date 2026-07-22

Chạy từ file audio (cần cả GROQ_API_KEY và GEMINI_API_KEY)::

    python main.py --input meeting.m4a --date 2026-07-22 \\
                   --title "Sprint 23 Review" --type planning

Xem quota còn lại trước khi chạy::

    python main.py --quota-status

Ước tính chi phí quota mà không gọi API::

    python main.py --input transcript.json --skip-stt --dry-run

Mỗi pha ghi checkpoint ra ``data/artifacts/<meeting_id>/``. Nhờ cache theo
băm nội dung, chạy lại khi đang tinh chỉnh prompt gần như không tốn quota
cho các pha phía trước.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from dataclasses import field as dataclasses_field
from pathlib import Path
from typing import Sequence

from core.cache import LLMCache
from core.env import check_permissions, load_dotenv, mask_secret
from core.logging import configure_logging
from core.quota import PROVIDER_LIMITS, QuotaLedger
from exporters.markdown import write_markdown
from pipeline.orchestrator import (
    OrchestratorConfig,
    Stage,
    StageEvent,
    StageStatus,
    STAGE_ORDER,
    resumable_stages,
)
from pipeline.orchestrator import run_pipeline as orchestrate
from pipeline.s0_ingest import (
    IngestPolicy,
    IngestReport,
    run_ingest,
    write_ingest_report,
)
from pipeline.s2_diarize import AttendeeHint, parse_attendee_hints, run_diarize
from pipeline.s3_chunk import ChunkingPolicy, run_chunk
from pipeline.s4_extract import run_extract
from pipeline.s5_reconcile import run_reconcile
from pipeline.s6_compose import run_compose
from pipeline.s7_validate import run_validate
from providers.base import LLMProvider, LLMRunner, ProviderError
from schemas.common import MeetingType
from schemas.minutes import PipelineInfo, StructuredMinutes
from schemas.reconciled import MeetingAnchor
from schemas.transcript import Transcript, TranscriptMeta

logger = logging.getLogger("meeting_minutes")

DATA_DIR = Path("data")
ARTIFACT_DIR = DATA_DIR / "artifacts"
OUTPUT_DIR = DATA_DIR / "exports"
DB_PATH = DATA_DIR / "app.db"

AUDIO_SUFFIXES = frozenset(
    {".wav", ".mp3", ".m4a", ".mp4", ".mov", ".ogg", ".flac", ".webm", ".aac"}
)

TEXT_TRANSCRIPT_SUFFIXES = frozenset({".vtt", ".srt", ".txt", ".md"})
"""Transcript dạng văn bản — đường vào rẻ nhất và cũng chính xác nhất.

Zoom, Google Meet và Microsoft Teams đều cho tải transcript về miễn phí,
**kèm sẵn tên người nói**. Đường này không tốn một giây quota Groq nào, và
cho kết quả tách người nói tốt hơn đường audio: Groq Whisper không làm
diarization nên một file audio đi vào sẽ ra transcript chỉ có một nhãn.
"""


@dataclass(slots=True)
class RunConfig:
    input_path: Path
    meeting_date: dt.date
    skip_stt: bool
    use_mock: bool
    offline: bool
    dry_run: bool
    no_cache: bool
    title: str
    meeting_type: MeetingType
    timezone: str
    output_dir: Path
    llm_model: str
    pace_seconds: float
    attendees: list[AttendeeHint] = dataclasses_field(default_factory=list)
    skip_diarize: bool = False
    max_chunk_tokens: int = 120_000
    formats: tuple[str, ...] = ("json", "md")
    merge_gap_ms: int = 2_000
    force: bool = False
    dump_transcript: bool = False
    resume: bool = False
    from_stage: Stage | None = None


# --------------------------------------------------------------------------- #
# Nạp đầu vào
# --------------------------------------------------------------------------- #


def load_transcript(config: RunConfig) -> tuple[Transcript, IngestReport | None]:
    """Nạp transcript từ mọi nguồn được hỗ trợ.

    Thứ tự ưu tiên cố ý đặt đường văn bản TRƯỚC đường audio: nó rẻ hơn,
    nhanh hơn, và cho tên người nói chính xác hơn.
    """
    path = config.input_path
    if not path.exists():
        raise SystemExit(f"Không tìm thấy file đầu vào: {path}")

    suffix = path.suffix.lower()

    if suffix == ".json":
        return _load_transcript_json(path, config), None

    if suffix in TEXT_TRANSCRIPT_SUFFIXES:
        return _ingest_text(path, config)

    if suffix in AUDIO_SUFFIXES and not config.skip_stt:
        return _transcribe_audio(path, config), None

    if config.skip_stt:
        # Đuôi lạ nhưng người dùng khẳng định đây là transcript. Cứ thử đọc:
        # pha INGEST nhận dạng theo NỘI DUNG nên đuôi sai vẫn xử lý được.
        logger.info("Đuôi %s không quen, thử đọc như transcript văn bản.", suffix)
        return _ingest_text(path, config)

    raise SystemExit(
        f"Đuôi file {path.suffix} không nhận ra.\n"
        f"  Audio      : {', '.join(sorted(AUDIO_SUFFIXES))}\n"
        f"  Transcript : .json, {', '.join(sorted(TEXT_TRANSCRIPT_SUFFIXES))}\n"
        "Dùng --skip-stt nếu đây là transcript có đuôi khác thường."
    )


def _slugify(text: str) -> str:
    """Rút gọn tên file thành mã an toàn cho tên thư mục artifact."""
    folded = unicodedata.normalize("NFD", text)
    ascii_only = "".join(c for c in folded if unicodedata.category(c) != "Mn")
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", ascii_only).strip("_").lower()
    return cleaned[:40] or "meeting"


def _ingest_text(path: Path, config: RunConfig) -> tuple[Transcript, IngestReport]:
    """Chuẩn hoá transcript văn bản và chạy cổng tiền kiểm chất lượng."""
    meta = TranscriptMeta(
        title=config.title or path.stem,
        meeting_date=config.meeting_date,
        timezone=config.timezone,
        meeting_type=config.meeting_type,
        duration_ms=0,
        glossary=[],
    )
    meeting_id = f"mtg_{config.meeting_date:%Y%m%d}_{_slugify(path.stem)}"

    try:
        outcome = run_ingest(
            path,
            meta=meta,
            meeting_id=meeting_id,
            policy=IngestPolicy(merge_gap_ms=config.merge_gap_ms),
            artifact_root=ARTIFACT_DIR,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    _print_ingest_report(outcome.report)

    if outcome.report.blocking and not config.force:
        raise SystemExit(
            "Dừng lại vì chất lượng đầu vào quá thấp. Sửa file nguồn, hoặc "
            "thêm --force để chạy tiếp và chấp nhận kết quả kém."
        )

    return outcome.transcript, outcome.report


def _print_ingest_report(report: IngestReport) -> None:
    print("\n--- TIỀN KIỂM ĐẦU VÀO ---")
    print(f"  Nguồn        : {report.source_name} ({report.source_format.value})")
    print(f"  Lượt thoại   : {report.cue_count} -> {report.segment_count} segment")
    print(
        f"  Người nói    : {report.speaker_count} "
        f"({report.named_speaker_count} có tên)"
    )
    print(f"  Thời lượng   : {report.duration_ms / 60000:.1f} phút")
    print(f"  Tỉ lệ có lời : {report.speech_ratio * 100:.0f}%")
    if report.warnings:
        print(f"  Cảnh báo     : {len(report.warnings)}")
        for warning in report.warnings:
            print(f"    {warning}")
    else:
        print("  Cảnh báo     : không có")


def _load_transcript_json(path: Path, config: RunConfig) -> Transcript:
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.setdefault("meta", {}).setdefault("meeting_date", config.meeting_date.isoformat())

    transcript = Transcript.model_validate(raw)
    if transcript.meta.meeting_date != config.meeting_date:
        logger.warning(
            "Ngày họp trong file (%s) khác --date (%s). Dùng giá trị trong file "
            "vì mọi mốc thời gian tương đối đều neo vào nó.",
            transcript.meta.meeting_date, config.meeting_date,
        )
    return transcript


def _transcribe_audio(path: Path, config: RunConfig) -> Transcript:
    from providers.asr.groq_whisper import (
        GroqWhisperProvider,
        TranscribeOptions,
        build_transcript,
    )

    logger.info("Phiên âm %s bằng Groq Whisper...", path.name)
    provider = GroqWhisperProvider()
    options = TranscribeOptions(language="vi")

    # Đặt chỗ TRƯỚC khi gọi. Giây audio của Groq là nút thắt thật của cả hệ
    # thống (28.800 giây/ngày ~ 8 giờ họp), nên nếu không ghi vào sổ cái thì
    # `--quota-status` báo còn nguyên trong khi thực tế đã cạn, và người dùng
    # chỉ biết khi Groq trả 429 giữa chừng một file dài.
    estimated_seconds = _estimate_audio_seconds(path)
    with QuotaLedger(DB_PATH, enabled=not config.use_mock) as quota:
        decision, reservation = quota.acquire(
            provider.name, provider.model, audio_seconds=estimated_seconds
        )
        if not decision.allowed:
            raise SystemExit(
                f"Không đủ quota audio của Groq: {decision.reason}\n"
                f"File ước tính {estimated_seconds}s. "
                f"Chờ {decision.retry_after_seconds / 60:.0f} phút, hoặc dùng "
                "transcript .vtt từ Zoom/Meet/Teams để không tốn quota nào."
            )
        try:
            result = provider.transcribe(str(path), options=options)
        except Exception:
            if reservation is not None:
                quota.release(reservation, succeeded=False)
            raise
        if reservation is not None:
            quota.release(reservation, succeeded=True)

    logger.info(
        "Đã phiên âm %.0f giây audio (ước tính trước khi gọi: %d giây)",
        result.duration_seconds, estimated_seconds,
    )

    meta = TranscriptMeta(
        title=config.title or path.stem,
        meeting_date=config.meeting_date,
        timezone=config.timezone,
        meeting_type=config.meeting_type,
        duration_ms=int(result.duration_seconds * 1000),
        glossary=list(options.glossary),
    )
    meeting_id = f"mtg_{config.meeting_date:%Y%m%d}_{path.stem}"

    logger.warning(
        "Groq Whisper không làm diarization: toàn bộ segment mang cùng một nhãn "
        "speaker. Biên bản vẫn đầy đủ nội dung nhưng chưa quy được phát biểu về "
        "từng người. Bước tách người nói là một pha riêng chưa có trong bản này."
    )
    return build_transcript(
        result,
        meeting_id=meeting_id,
        transcript_id=f"tr_{meeting_id}_v1",
        meta=meta,
    )


# --------------------------------------------------------------------------- #
# Dựng provider
# --------------------------------------------------------------------------- #


def _estimate_audio_seconds(path: Path) -> int:
    """Ước tính thời lượng audio để đặt chỗ quota trước khi gọi Groq.

    Ưu tiên ``ffprobe`` vì nó cho con số thật. Không có ffprobe thì suy từ
    dung lượng file với bitrate giả định 128 kbps — cố ý ước tính THỪA, vì
    đặt chỗ thiếu sẽ khiến sổ cái báo còn quota trong khi đã cạn.
    """
    import shutil
    import subprocess

    if shutil.which("ffprobe"):
        try:
            output = subprocess.run(
                [
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", str(path),
                ],
                capture_output=True, text=True, timeout=30, check=True,
            ).stdout.strip()
            return max(10, int(float(output)))
        except (subprocess.SubprocessError, ValueError):
            logger.debug("ffprobe không đọc được %s, quay về ước tính theo dung lượng", path.name)

    assumed_bitrate_bytes_per_second = 128_000 / 8
    seconds = path.stat().st_size / assumed_bitrate_bytes_per_second
    # Groq tính tối thiểu 10 giây mỗi request, dù file ngắn hơn.
    return max(10, int(seconds))


def build_llm_providers(config: RunConfig) -> list[LLMProvider]:
    """Dựng chuỗi provider theo thứ tự ưu tiên.

    Chuỗi dự phòng chính là thứ giữ cho hệ 0 đồng chạy được: hết quota
    Gemini Flash thì tụt xuống Flash-Lite (quota riêng), rồi mới thất bại.
    """
    if config.use_mock:
        from providers.llm.mock import MockLLMProvider

        return [MockLLMProvider()]

    if config.offline:
        raise SystemExit(
            "Chế độ --offline cần một backend LLM chạy cục bộ (ví dụ Ollama). "
            "Adapter đó chưa có trong bản này; hiện dùng --mock để chạy thử "
            "toàn bộ pipeline mà không gọi mạng."
        )

    from providers.llm.gemini import GeminiProvider

    providers: list[LLMProvider] = []
    for model in (config.llm_model, "gemini-flash-lite-latest"):
        try:
            providers.append(GeminiProvider(model=model))
        except ProviderError as exc:
            logger.warning("Bỏ qua %s: %s", model, exc)

    if not providers:
        raise SystemExit(
            "Không dựng được provider LLM nào. Đặt GEMINI_API_KEY trong môi "
            "trường, hoặc chạy với --mock để thử pipeline offline."
        )
    return providers


# --------------------------------------------------------------------------- #
# Chạy pipeline
# --------------------------------------------------------------------------- #


def run_pipeline(config: RunConfig) -> StructuredMinutes:
    """Nạp dữ liệu, chạy pipeline, in báo cáo.

    Việc điều phối thật nằm ở ``pipeline/orchestrator.py``. Hàm này chỉ còn
    làm những thứ đặc thù của dòng lệnh: nạp file, in ra terminal, chọn mã
    thoát. Nhờ vậy cùng một bộ điều phối dùng lại được cho giao diện web mà
    không kéo theo phần in ấn.
    """
    transcript, ingest_report = load_transcript(config)

    artifacts = ARTIFACT_DIR / transcript.meeting_id
    artifacts.mkdir(parents=True, exist_ok=True)
    _save(artifacts / "transcript.json", transcript)

    if ingest_report is not None:
        # Ghi báo cáo tiền kiểm cạnh transcript. Lần nạp sau dò checksum ở
        # đây để phát hiện file trùng và tránh chạy lại tốn quota.
        write_ingest_report(artifacts / "ingest.json", ingest_report)

    if config.dump_transcript:
        destination = config.output_dir / f"{transcript.meeting_id}_transcript.json"
        _save(destination, transcript)
        print(f"\nĐã lưu transcript đã chuẩn hoá: {destination}")
        print(
            "Sửa tay file này rồi chạy lại với --input <file> --skip-stt để "
            "dùng bản đã sửa — không tốn thêm quota cho bước nạp."
        )

    logger.info(
        "Transcript: %d segment, %d speaker, %d chunk, thời lượng %d phút",
        len(transcript.segments), len(transcript.speakers),
        len(transcript.chunks), transcript.meta.duration_ms // 60000,
    )

    if config.dry_run:
        _report_dry_run(transcript, config)
        raise SystemExit(0)

    from_stage = _resolve_from_stage(config, artifacts)

    cache = LLMCache(DB_PATH, enabled=not config.no_cache)
    quota = QuotaLedger(DB_PATH, enabled=not config.use_mock)

    remaining = None
    if not config.use_mock:
        status = quota.status("gemini", config.llm_model)
        daily = status.get("RPD")
        remaining = daily["remaining"] if daily else None

    runner = LLMRunner(build_llm_providers(config), cache=cache, quota=quota)

    try:
        outcome = orchestrate(
            transcript,
            OrchestratorConfig(
                anchor=MeetingAnchor(
                    meeting_date=transcript.meta.meeting_date,
                    timezone=config.timezone,
                ),
                artifacts_dir=artifacts,
                attendees=config.attendees,
                skip_diarize=config.skip_diarize,
                max_chunk_tokens=config.max_chunk_tokens,
                pace_seconds=config.pace_seconds,
                rpd_remaining=remaining,
                from_stage=from_stage,
            ),
            runner,
            on_event=_print_stage_event,
        )
    finally:
        cache.close()
        quota.close()

    if not outcome.succeeded:
        print(f"\nDỪNG ở pha {outcome.failed_stage.value.upper()}: {outcome.error}", file=sys.stderr)
        print(
            "\nArtifact của các pha đã xong vẫn còn trong "
            f"{artifacts}.\nChạy lại với --resume để tiếp tục mà không tốn lại quota.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if outcome.restored_stages:
        names = ", ".join(s.value for s in outcome.restored_stages)
        print(f"\nĐã đọc lại artifact của pha: {names} (không tốn quota)")

    _print_report(outcome.minutes, runner, cache, None)
    return outcome.minutes


def _resolve_from_stage(config: RunConfig, artifacts: Path) -> Stage | None:
    """Quyết định bắt đầu lại từ pha nào.

    ``--from-stage`` là chỉ định tường minh, luôn thắng. ``--resume`` thì tự
    dò: tìm pha tốn quota cuối cùng đã có artifact rồi tiếp tục từ pha ngay
    sau đó.
    """
    if config.from_stage is not None:
        return config.from_stage

    if not config.resume:
        return None

    done = resumable_stages(artifacts)
    if not done:
        print("Không có artifact nào để tiếp tục — chạy lại từ đầu.")
        return None

    last = done[-1]
    following = STAGE_ORDER[STAGE_ORDER.index(last) + 1]
    print(
        f"Tiếp tục từ pha {following.value.upper()} "
        f"(đã có artifact tới pha {last.value.upper()})."
    )
    return following


def _print_stage_event(event: StageEvent) -> None:
    """In tiến độ ra terminal.

    Đây chính là phần mà bộ điều phối cố ý không làm. Giao diện web sẽ thay
    hàm này bằng một lời gọi đẩy sự kiện qua websocket, dùng lại y nguyên
    phần điều phối.
    """
    if event.status is StageStatus.STARTED:
        return
    marks = {
        StageStatus.DONE: "  ok  ",
        StageStatus.SKIPPED: " bỏ qua",
        StageStatus.RESTORED: " đọc lại",
        StageStatus.FAILED: " LỖI ",
    }
    mark = marks.get(event.status, "      ")
    print(
        f"  [{event.position}/{len(STAGE_ORDER)}] {event.stage.value:<10s}"
        f"{mark} {event.message} ({event.elapsed_ms}ms)"
    )


def _report_dry_run(transcript: Transcript, config: RunConfig) -> None:
    """Ước tính quota cần dùng mà không gọi API."""
    chunks = max(1, len(transcript.chunks))
    requests = chunks + 2  # extract theo chunk + gom nhóm + compose
    characters = sum(len(s.text) for s in transcript.segments)
    tokens = int(characters / 2.6 * 2.5)  # nhân hệ số cho nhiều lượt gọi

    print("\n--- CHẠY KHÔ (không gọi API) ---")
    print(f"  Segment            : {len(transcript.segments)}")
    print(f"  Chunk              : {chunks}")
    print(f"  Request LLM ước tính: {requests}")
    print(f"  Token ước tính     : ~{tokens:,}")

    if not config.use_mock:
        with QuotaLedger(DB_PATH) as quota:
            affordable, reason = quota.can_afford(
                "gemini", config.llm_model, requests=requests, tokens=tokens
            )
            print(f"  Quota              : {reason}")
            if not affordable:
                print("  -> Chờ tới nửa đêm giờ Thái Bình Dương hoặc dùng --mock.")


def _print_report(
    minutes: StructuredMinutes,
    runner: LLMRunner,
    cache: LLMCache,
    extraction: object,
) -> None:
    validation = minutes.validation
    print("\n" + "=" * 68)
    print(f"BIÊN BẢN: {minutes.meta.meeting_title}")
    print("=" * 68)

    print("\nTÓM TẮT")
    for line in minutes.executive_summary.tldr:
        print(f"  • {line}")

    active = minutes.active_decisions
    print(f"\nQUYẾT ĐỊNH CÒN HIỆU LỰC ({len(active)})")
    for decision in active:
        target = f" [{decision.target_date}]" if decision.target_date else ""
        print(f"  ✓ {decision.statement}{target}")
    for decision in minutes.superseded_decisions:
        print(f"  ✗ (đã thay thế bởi {decision.superseded_by}) {decision.statement}")

    print(f"\nCÔNG VIỆC ({len(minutes.action_items)})")
    for action in minutes.action_items:
        who = action.assignee or "CHƯA PHÂN CÔNG"
        when = action.due_date.isoformat() if action.due_date else "chưa xác định"
        flag = "  ⚠ cần review" if action.needs_review else ""
        print(f"  • [{action.id}] {action.task}")
        print(f"      {who} · hạn {when} · {action.commitment_strength.value}{flag}")

    warnings = minutes.quality_report.warnings
    if warnings:
        print(f"\nCẢNH BÁO ({len(warnings)})")
        for warning in warnings:
            print(f"  [{warning.severity.value}] {warning.code.value}: {warning.message}")

    print("\nKIỂM CHỨNG")
    if validation:
        print(f"  Điểm grounding: {validation.grounding_score:.2f}")
        for name, check in validation.checks.items():
            mark = "PASS" if check.passed else "FAIL"
            print(f"  [{mark}] {name}: {check.checked} kiểm, {check.failed} lỗi")

    stats = runner.stats()
    print("\nTÀI NGUYÊN ĐÃ DÙNG")
    print(f"  Request LLM: {stats['llm_requests']}")
    print(f"  Token      : {stats['llm_tokens']:,}")
    print(f"  {cache.stats.summary()}")
    print(f"  Chi phí    : 0 VNĐ")
    print("=" * 68)


def _save(path: Path, model: object) -> None:
    payload = model.model_dump(mode="json")  # type: ignore[attr-defined]
    _save_raw(path, payload)


def _save_raw(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.debug("Đã ghi %s", path)


# --------------------------------------------------------------------------- #
# Giao diện dòng lệnh
# --------------------------------------------------------------------------- #


def show_quota_status() -> None:
    with QuotaLedger(DB_PATH) as quota:
        print("\n--- QUOTA CÒN LẠI ---")
        print("(reset lúc nửa đêm giờ Thái Bình Dương, khoảng 14-15h giờ Việt Nam)\n")
        for key in PROVIDER_LIMITS:
            provider, model = key.split("/", 1)
            if provider == "mock":
                continue
            report = quota.status(provider, model)
            if not report:
                continue
            print(f"{key}")
            for window, values in report.items():
                bar_width = 20
                ratio = values["used"] / values["limit"] if values["limit"] else 0.0
                filled = min(bar_width, int(ratio * bar_width))
                bar = "█" * filled + "░" * (bar_width - filled)
                print(
                    f"  {window:15s} {bar} "
                    f"{values['used']:>7,}/{values['limit']:<7,} "
                    f"(còn {values['remaining']:,})"
                )
            print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Tóm tắt cuộc họp và xuất biên bản có cấu trúc (POC 0 đồng)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ví dụ:\n"
            "  python main.py --input tests/fixtures/sample_transcript.json "
            "--skip-stt --date 2026-07-22 --mock\n"
            "  python main.py --input zoom_recording.vtt --date 2026-07-22\n"
            "  python main.py --input meeting.m4a --date 2026-07-22\n"
            "  python main.py --quota-status\n"
        ),
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="File audio (.m4a, .mp3...), transcript văn bản (.vtt, .srt, .txt, "
        ".md) hoặc transcript JSON đã chuẩn hoá",
    )
    parser.add_argument(
        "--date",
        type=dt.date.fromisoformat,
        default=dt.date.today(),
        help="Ngày họp (YYYY-MM-DD) — mốc neo cho mọi mốc thời gian tương đối",
    )
    parser.add_argument(
        "--skip-stt", action="store_true", help="Đầu vào đã là transcript, bỏ qua ASR"
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="Dùng phản hồi LLM đóng hộp — không cần API key, không tốn quota",
    )
    parser.add_argument(
        "--offline", action="store_true", help="Không gửi dữ liệu ra ngoài (cần LLM cục bộ)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Ước tính quota mà không gọi API"
    )
    parser.add_argument("--no-cache", action="store_true", help="Bỏ qua cache")
    parser.add_argument("--title", default="", help="Tiêu đề cuộc họp")
    parser.add_argument(
        "--type",
        dest="meeting_type",
        default=MeetingType.OTHER.value,
        choices=[t.value for t in MeetingType],
        help="Loại cuộc họp",
    )
    parser.add_argument("--timezone", default="Asia/Ho_Chi_Minh")
    parser.add_argument(
        "--attendees",
        default="",
        help='Danh sách người tham dự, dạng "Hùng:PM,Tuấn:Backend,Lan:QA". '
        "Biết trước danh sách giúp gán tên người nói chính xác hơn nhiều.",
    )
    parser.add_argument(
        "--skip-diarize",
        action="store_true",
        help="Bỏ qua bước gán tên người nói (dùng khi transcript đã có tên)",
    )
    parser.add_argument(
        "--max-chunk-tokens",
        type=int,
        default=120_000,
        help="Trần token mỗi chunk. Để cao nhằm giảm số request (mặc định 120k)",
    )
    parser.add_argument(
        "--format",
        default="json,md",
        help="Định dạng kết xuất, phân tách bằng dấu phẩy: json, md",
    )
    parser.add_argument(
        "--merge-gap",
        type=int,
        default=2_000,
        dest="merge_gap_ms",
        help="Khoảng lặng tối đa (ms) còn gộp hai lượt thoại liền nhau của "
        "cùng một người. Đặt 0 để giữ nguyên từng cue của Zoom (mặc định 2000)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Tiếp tục từ artifact của lần chạy trước thay vì gọi lại LLM",
    )
    parser.add_argument(
        "--from-stage",
        choices=[s.value for s in STAGE_ORDER],
        help="Bắt đầu lại từ đúng một pha cụ thể (ghi đè --resume)",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Ghi log ra file, xoay vòng khi vượt 2MB. Bí mật luôn bị che.",
    )
    parser.add_argument(
        "--log-full-content",
        action="store_true",
        help="Không cắt ngắn bản ghi DEBUG dài. Log có thể chứa nội dung họp.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Chạy tiếp kể cả khi tiền kiểm phát hiện lỗi nghiêm trọng",
    )
    parser.add_argument(
        "--dump-transcript",
        action="store_true",
        help="Ghi transcript đã chuẩn hoá ra file để sửa tay trước khi chạy tiếp",
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR, help="Thư mục kết quả")
    parser.add_argument("--model", default="gemini-flash-latest", help="Model Gemini")
    parser.add_argument(
        "--pace",
        type=float,
        default=0.0,
        help="Giãn cách giữa các request EXTRACT (giây) để không chạm trần RPM",
    )
    parser.add_argument("--quota-status", action="store_true", help="Xem quota còn lại")
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # Nạp bí mật TRƯỚC khi dựng log: bộ lọc cần biết key để che được chúng
    # nếu chúng lọt ra từ traceback của thư viện bên thứ ba.
    # Biến môi trường có sẵn luôn thắng, nên cách này không phá vỡ CI hay
    # container vốn tiêm key theo cách của chúng.
    load_dotenv()

    configure_logging(
        verbose=args.verbose,
        log_file=args.log_file,
        allow_full_content=args.log_full_content,
    )
    for warning in check_permissions():
        logger.warning("%s", warning)

    if args.quota_status:
        show_quota_status()
        return 0

    if args.input is None:
        build_parser().print_help()
        return 1

    if not args.mock and not args.offline:
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            logger.warning(
                "Chưa có GEMINI_API_KEY. Tạo file .env từ .env.example và điền "
                "key vào, hoặc dùng --mock để chạy thử pipeline offline."
            )
        else:
            logger.info("GEMINI_API_KEY: %s", mask_secret(gemini_key))

    config = RunConfig(
        input_path=args.input,
        meeting_date=args.date,
        skip_stt=args.skip_stt,
        use_mock=args.mock,
        offline=args.offline,
        dry_run=args.dry_run,
        no_cache=args.no_cache,
        title=args.title,
        meeting_type=MeetingType(args.meeting_type),
        timezone=args.timezone,
        output_dir=args.output,
        llm_model=args.model,
        pace_seconds=args.pace,
        attendees=parse_attendee_hints(args.attendees),
        skip_diarize=args.skip_diarize,
        max_chunk_tokens=args.max_chunk_tokens,
        formats=tuple(
            fmt.strip().lower() for fmt in args.format.split(",") if fmt.strip()
        ),
        merge_gap_ms=args.merge_gap_ms,
        force=args.force,
        dump_transcript=args.dump_transcript,
        resume=args.resume,
        from_stage=Stage(args.from_stage) if args.from_stage else None,
    )

    try:
        minutes = run_pipeline(config)
    except SystemExit:
        raise
    except Exception as exc:
        logger.error("Pipeline thất bại: %s", exc, exc_info=args.verbose)
        return 1

    config.output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    if "json" in config.formats:
        destination = config.output_dir / f"{minutes.meeting_id}_minutes.json"
        _save(destination, minutes)
        written.append(destination)

    if "md" in config.formats or "markdown" in config.formats:
        written.append(
            write_markdown(
                minutes,
                config.output_dir / f"{minutes.meeting_id}_minutes.md",
            )
        )

    for path in written:
        print(f"Đã lưu: {path}")

    return 0 if (minutes.validation and minutes.validation.grounding_score >= 0.9) else 2


if __name__ == "__main__":
    raise SystemExit(main())
