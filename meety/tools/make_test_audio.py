#!/usr/bin/env python3
"""Sinh file audio họp tiếng Việt kèm ĐÁP ÁN CHUẨN, để kiểm thử đầu-cuối.

Vì sao cần công cụ này
----------------------
Không tồn tại bộ dữ liệu công khai nào gồm *audio họp tiếng Việt + biên bản
đối chiếu*. Các corpus có sẵn (VIVOS, BUD500, VLSP) đều là giọng đọc một
người, không có quyết định, không có cam kết, không có ai đổi ý giữa chừng —
tức là chúng đo được ASR nhưng **không đo được sản phẩm**.

Công cụ này lấp chỗ đó bằng cách tổng hợp giọng nói từ một kịch bản mà ta
biết trước đáp án. Nhờ vậy bạn đo được toàn bộ chuỗi Groq → Gemini với sai
số đã biết, ngay hôm nay, không cần rủ ai họp cùng.

Giới hạn phải ghi nhớ
---------------------
Audio tổng hợp là audio **sạch**: không tiếng ồn, không micro hội nghị,
không ai nói chồng lời. Nên WER đo ở đây là **cận dưới lạc quan** — audio
họp thật sẽ tệ hơn, thường gấp hai tới ba lần. Đây là phép thử "hệ thống có
chạy đúng không", không phải "hệ thống chịu được thực tế không". Bước sau
vẫn phải là một bản ghi âm thật.

Cách dùng
---------
Cài công cụ tổng hợp giọng (miễn phí, không cần API key)::

    python -m pip install edge-tts

Sinh audio và đáp án::

    python tools/make_test_audio.py --script tools/kichban_kickoff.json

Kết quả trong ``tools/output/``:

* ``<tên>.mp3``          — đưa vào ``main.py --input`` để chạy đường audio
* ``<tên>_dapan.vtt``    — transcript chuẩn, dùng làm mốc đo WER
* ``<tên>_dapan.json``   — kịch bản đã kèm mốc thời gian

So sánh transcript Groq trả về với ``_dapan.vtt`` cho ra WER của tầng ASR.
Chạy thẳng ``_dapan.vtt`` qua pipeline cho ra chất lượng tầng LLM khi ASR
hoàn hảo. Hai phép đo tách bạch — đó là điểm mấu chốt: khi biên bản sai, bạn
biết ngay lỗi nằm ở tầng nào.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

GAP_MS = 400
"""Khoảng lặng chèn giữa hai lượt thoại, mô phỏng nhịp hội thoại thật."""

PACE_SECONDS = 1.2
"""Giãn cách mặc định giữa hai lời gọi tổng hợp giọng.

Bắn liên tiếp không nghỉ là cách nhanh nhất để bị Microsoft chặn tạm.
"""

MAX_ATTEMPTS = 4
"""Số lần thử lại mỗi lượt trước khi bỏ cuộc."""


def _timecode(ms: int) -> str:
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    seconds, ms = divmod(ms, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"


async def _synthesize_turn(
    text: str, voice: str, pitch: str, rate: str, target: Path
) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(str(target))


async def _synthesize_with_retry(
    text: str, voice: str, pitch: str, rate: str, target: Path
) -> None:
    """Tổng hợp một lượt, thử lại với giãn cách tăng dần khi bị chặn.

    ``edge-tts`` nói chuyện với endpoint nội bộ của Microsoft Edge — không
    phải API công khai, không có hạn mức công bố, và có chống lạm dụng. Bắn
    hai chục lời gọi liên tiếp rất hay bị chặn giữa chừng.

    Điều khiến lỗi này khó chẩn đoán: khi bị chặn, endpoint trả về **luồng
    rỗng** chứ không trả mã lỗi, nên thư viện ném ``NoAudioReceived`` kèm
    thông báo *"verify that your parameters are correct"* — chỉ sai địa chỉ
    hoàn toàn so với nguyên nhân thật. Người đọc sẽ đi soi lại tên giọng và
    pitch, trong khi vấn đề nằm ở nhịp gọi.
    """
    last_error: Exception | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            await _synthesize_turn(text, voice, pitch, rate, target)
            if target.is_file() and target.stat().st_size > 0:
                return
            raise RuntimeError("edge-tts ghi ra file rỗng")
        except Exception as exc:  # noqa: BLE001 — thư viện ném nhiều kiểu lỗi
            last_error = exc
            target.unlink(missing_ok=True)
            if attempt == MAX_ATTEMPTS:
                break
            backoff = 2.0 * attempt
            print(
                f"       bị chặn (lần {attempt}/{MAX_ATTEMPTS}), "
                f"chờ {backoff:.0f}s rồi thử lại..."
            )
            await asyncio.sleep(backoff)

    raise RuntimeError(
        f"Không tổng hợp được lượt thoại sau {MAX_ATTEMPTS} lần thử.\n"
        f"  Lỗi gốc: {type(last_error).__name__}: {last_error}\n\n"
        "Nguyên nhân thường gặp, xếp theo khả năng:\n"
        "  1. Microsoft chặn tạm vì gọi quá dày. Chờ vài phút rồi chạy lại,\n"
        "     hoặc giãn nhịp ra: --pace 3\n"
        "  2. edge-tts đã cũ. Microsoft thỉnh thoảng đổi cơ chế xác thực và\n"
        "     bản cũ ngừng chạy: python -m pip install -U edge-tts\n"
        "  3. Mạng chặn endpoint của Microsoft (VPN, tường lửa công ty).\n\n"
        "Dù sao thì file VTT đáp án đã được ghi ra rồi và dùng được ngay —\n"
        "xem đường dẫn ở thông báo phía trên. Đường VTT không cần audio."
    )


def _duration_ms(path: Path) -> int:
    """Đo thời lượng thật của một file audio.

    Cần ``ffprobe``. Không có thì ước tính theo số từ — kém chính xác hơn
    nhưng vẫn cho ra file dùng được, chỉ là mốc thời gian trong đáp án sẽ
    lệch. Mốc lệch không ảnh hưởng tới việc đo WER.
    """
    if shutil.which("ffprobe"):
        try:
            output = subprocess.run(
                [
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", str(path),
                ],
                capture_output=True, text=True, timeout=30, check=True,
            ).stdout.strip()
            return int(float(output) * 1000)
        except (subprocess.SubprocessError, ValueError):
            pass
    return 0


def _concat(parts: list[Path], target: Path) -> None:
    """Ghép các đoạn mp3 thành một file duy nhất.

    Ưu tiên ``ffmpeg`` vì nó chèn được khoảng lặng và cho file sạch. Không có
    ffmpeg thì nối byte trực tiếp: các đoạn đều do cùng một engine sinh ra
    với cùng codec và bitrate, nên bộ giải mã của Groq đọc được. Đánh đổi là
    không có khoảng lặng giữa các lượt và thời lượng báo cáo có thể lệch.
    """
    if shutil.which("ffmpeg"):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8"
        ) as handle:
            listing = Path(handle.name)
            for part in parts:
                handle.write(f"file '{part.resolve().as_posix()}'\n")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-nostdin", "-y", "-loglevel", "error",
                    "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", str(target),
                ],
                check=True, timeout=300,
            )
            return
        finally:
            listing.unlink(missing_ok=True)

    print("  ffmpeg không có — nối byte trực tiếp (chấp nhận được với mp3 cùng nguồn)")
    with target.open("wb") as out:
        for part in parts:
            out.write(part.read_bytes())


def _estimate_ms(text: str) -> int:
    """Ước tính thời lượng nói từ số từ, dùng khi chưa có audio thật."""
    return max(1_500, int(len(text.split()) / 140 * 60_000))


def _build_cues(turns: list[dict[str, str]], durations: list[int]) -> list[dict[str, Any]]:
    cues: list[dict[str, Any]] = []
    cursor_ms = 0
    for index, (turn, spoken) in enumerate(zip(turns, durations), start=1):
        cues.append(
            {
                "index": index,
                "speaker": turn["speaker"],
                "text": turn["text"],
                "start_ms": cursor_ms,
                "end_ms": cursor_ms + spoken,
            }
        )
        cursor_ms += spoken + GAP_MS
    return cues


def _write_answers(
    script: dict[str, Any], cues: list[dict[str, Any]], output_dir: Path, stem: str
) -> tuple[Path, Path]:
    """Ghi transcript đáp án ra đĩa.

    Hàm này KHÔNG phụ thuộc vào việc tổng hợp giọng. Đó là điểm mấu chốt:
    đáp án suy ra được hoàn toàn từ kịch bản, nên nó phải tồn tại kể cả khi
    edge-tts hỏng. Bản đầu tiên của công cụ này ghi đáp án SAU khi tổng hợp
    xong, nên một lỗi mạng ở lượt thứ tư làm mất luôn cả file mà đáng lẽ
    không cần mạng để tạo ra — và người dùng mất luôn đường chạy rẻ nhất.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    vtt_lines = ["WEBVTT", ""]
    for cue in cues:
        vtt_lines += [
            str(cue["index"]),
            f"{_timecode(cue['start_ms'])} --> {_timecode(cue['end_ms'])}",
            f"{cue['speaker']}: {cue['text']}",
            "",
        ]
    vtt = output_dir / f"{stem}_dapan.vtt"
    vtt.write_text("\n".join(vtt_lines), encoding="utf-8")

    answer = output_dir / f"{stem}_dapan.json"
    answer.write_text(
        json.dumps(
            {"meeting": script["meeting"], "cues": cues}, ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    return vtt, answer


async def _build(
    script: dict[str, Any],
    output_dir: Path,
    stem: str,
    *,
    pace_seconds: float = PACE_SECONDS,
    vtt_only: bool = False,
) -> int:
    speakers: dict[str, dict[str, str]] = script["speakers"]
    turns: list[dict[str, str]] = script["turns"]

    # BƯỚC 1 — đáp án trước, không cần mạng.
    estimates = [_estimate_ms(turn["text"]) for turn in turns]
    vtt, answer = _write_answers(script, _build_cues(turns, estimates), output_dir, stem)
    print(f"  Đáp án VTT : {vtt}")
    print(f"  Đáp án JSON: {answer}")
    print("  (dùng được ngay cho đường LLM — không cần audio, không tốn quota Groq)\n")

    if vtt_only:
        return 0

    # BƯỚC 2 — tổng hợp giọng. Hỏng ở đây cũng không mất đáp án.
    workdir = Path(tempfile.mkdtemp(prefix="tts_turns_"))
    parts: list[Path] = []
    durations: list[int] = []

    try:
        for index, turn in enumerate(turns, start=1):
            config = speakers[turn["speaker"]]
            part = workdir / f"turn_{index:03d}.mp3"

            print(f"  [{index:2d}/{len(turns)}] {turn['speaker']}: {turn['text'][:50]}...")
            await _synthesize_with_retry(
                turn["text"],
                config["voice"],
                config.get("pitch", "+0Hz"),
                config.get("rate", "+0%"),
                part,
            )
            parts.append(part)

            measured = _duration_ms(part)
            durations.append(measured or estimates[index - 1])

            if index < len(turns) and pace_seconds > 0:
                await asyncio.sleep(pace_seconds)

        audio = output_dir / f"{stem}.mp3"
        _concat(parts, audio)

        # BƯỚC 3 — ghi lại đáp án với thời lượng ĐO ĐƯỢC, khớp audio thật.
        cues = _build_cues(turns, durations)
        vtt, answer = _write_answers(script, cues, output_dir, stem)
        total_ms = cues[-1]["end_ms"] if cues else 0

        size_mb = audio.stat().st_size / 1e6
        print()
        print(f"  Audio      : {audio}  ({size_mb:.1f} MB, ~{total_ms / 60000:.1f} phút)")
        print(f"  Đáp án     : đã cập nhật theo thời lượng đo được")
        if size_mb > 24:
            print(
                "  ⚠ Vượt 24MB — Groq free tier chặn upload trên 25MB. "
                "Cần ffmpeg để chia nhỏ."
            )
        return 0
    except RuntimeError as exc:
        print(f"\n  Dừng phần tổng hợp giọng.\n\n{exc}\n", file=sys.stderr)
        return 2
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sinh audio họp tiếng Việt kèm đáp án chuẩn, dùng edge-tts (0 đồng)",
    )
    parser.add_argument(
        "--script", type=Path, default=Path("tools/kichban_kickoff.json"),
        help="File kịch bản JSON",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("tools/output"), help="Thư mục kết quả"
    )
    parser.add_argument(
        "--pace", type=float, default=PACE_SECONDS, dest="pace_seconds",
        help="Giãn cách (giây) giữa hai lời gọi tổng hợp. Tăng lên 3 nếu bị chặn",
    )
    parser.add_argument(
        "--vtt-only", action="store_true",
        help="Chỉ sinh transcript đáp án, bỏ qua tổng hợp giọng. Không cần "
        "edge-tts, không cần mạng — đủ để chạy đường LLM",
    )
    args = parser.parse_args(argv)

    try:
        if not args.vtt_only:
            import edge_tts  # noqa: F401
    except ImportError:
        print(
            "Thiếu edge-tts. Cài bằng:\n"
            "  python -m pip install edge-tts\n\n"
            "Gói này miễn phí, không cần API key, và KHÔNG nằm trong "
            "requirements.txt vì nó chỉ phục vụ việc tạo dữ liệu kiểm thử — "
            "pipeline chạy được mà không có nó.",
            file=sys.stderr,
        )
        return 1

    if not args.script.is_file():
        print(f"Không tìm thấy kịch bản: {args.script}", file=sys.stderr)
        return 1

    script = json.loads(args.script.read_text(encoding="utf-8"))
    print(f"Kịch bản: {script['meeting']['title']}")
    print(f"  {len(script['turns'])} lượt thoại, {len(script['speakers'])} người nói\n")

    return asyncio.run(
        _build(
            script,
            args.output,
            args.script.stem.replace("kichban_", ""),
            pace_seconds=args.pace_seconds,
            vtt_only=args.vtt_only,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
