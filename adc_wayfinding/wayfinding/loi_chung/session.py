"""
Ghi lai buoi di thu de PHAT LAI - cong cu quan trong nhat khi kiem thu
thuc dia.

Van de: di thu mot vong hanh lang mat 5 phut. Neu he thong chi sai o giay
thu 40, ban khong the "quay lai giay 40" - phai di lai ca vong, va lan
sau dieu kien anh sang, toc do di, goc camera deu khac. Khong bao gio tai
hien duoc dung loi vua thay.

Cach lam: ghi lai MOI khung hinh nhung gi he thong nhin thay va quyet
dinh - moc neo bat duoc, tu the, do tin cay, cau da noi. Sau do phat lai
tren laptop bao nhieu lan cung duoc, sua code roi phat lai de xem loi da
het chua.

Ghi o dinh dang JSONL (moi dong mot ban ghi JSON):
  - Ghi duoc trong luc dang chay, khong can dong file moi doc duoc
  - Mat dien giua chung thi van con nhung gi da ghi
  - Doc bang bat ky cong cu nao, khong can thu vien rieng

TUY CHON ghi kem anh: nang hon nhieu nhung cho phep chay lai CA phan
nhan dien, khong chi phan quyet dinh. Dung khi nghi ngo loi nam o buoc
doc ma chu khong phai buoc chi duong.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass
class FrameRecord:
    """Nhung gi he thong thay va quyet dinh o mot khung hinh."""

    t: float                              # giay ke tu luc bat dau
    frame_index: int
    sightings: list[dict] = field(default_factory=list)
    session_pose: dict | None = None      # tu the VIO, he toa do phien
    fix: dict | None = None               # vi tri suy ra, he toa do toa nha
    confidence: str | None = None
    distance_since_fix: float | None = None
    state: str | None = None
    said: str | None = None
    haptic: str | None = None
    sharpness: float | None = None
    gyro_dps: float | None = None
    image: str | None = None              # ten file anh, neu co ghi

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


class SessionRecorder:
    """
    Ghi mot buoi di thu.

    Cach dung trong vong lap:
        rec = SessionRecorder("runs/2026-09-19-tuyenA")
        ...
        rec.log(frame_index=i, sightings=[...], fix=fix, said=text)
        ...
        rec.close()
    """

    def __init__(self, path: str | Path, meta: dict | None = None,
                 save_images: bool = False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.save_images = save_images
        self.image_dir = self.path.with_suffix("") / "frames"
        if save_images:
            self.image_dir.mkdir(parents=True, exist_ok=True)

        self._t0 = time.time()
        self._fh = self.path.open("w", encoding="utf-8")
        self.count = 0

        header = {"kind": "meta", "started": self._t0}
        header.update(meta or {})
        self._fh.write(json.dumps(header, ensure_ascii=False) + "\n")
        self._fh.flush()

    def log(self, frame_index: int, sightings=None, session_pose=None,
            fix=None, instruction=None, sharpness=None, gyro_dps=None,
            frame=None) -> None:
        rec = FrameRecord(
            t=round(time.time() - self._t0, 3),
            frame_index=frame_index,
            sharpness=sharpness,
            gyro_dps=gyro_dps,
        )

        for s in (sightings or []):
            rec.sightings.append({
                "key": s.key, "source": s.source,
                "distance": round(s.distance, 3),
                "quality": s.quality,
                "cam_from_anchor": [round(s.cam_from_anchor.x, 4),
                                    round(s.cam_from_anchor.y, 4),
                                    round(s.cam_from_anchor.theta, 2)],
            })

        if session_pose is not None:
            rec.session_pose = {"x": round(session_pose.x, 4),
                                "y": round(session_pose.y, 4),
                                "theta": round(session_pose.theta, 2)}

        if fix is not None:
            rec.fix = {"x": round(fix.pose.x, 3),
                       "y": round(fix.pose.y, 3),
                       "theta": round(fix.pose.theta, 2)}
            rec.confidence = fix.confidence.value
            rec.distance_since_fix = round(fix.distance_since_fix, 2)

        if instruction is not None:
            rec.said = instruction.text
            rec.haptic = instruction.haptic

        if frame is not None and self.save_images:
            import cv2

            name = f"{frame_index:06d}.jpg"
            cv2.imwrite(str(self.image_dir / name), frame,
                        [cv2.IMWRITE_JPEG_QUALITY, 80])
            rec.image = name

        self._fh.write(rec.to_json() + "\n")
        self._fh.flush()          # mat dien giua chung van con du lieu
        self.count += 1

    def set_state(self, state: str) -> None:
        self._pending_state = state

    def close(self, summary: dict | None = None) -> None:
        if summary:
            tail = {"kind": "summary"}
            tail.update(summary)
            self._fh.write(json.dumps(tail, ensure_ascii=False) + "\n")
        self._fh.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


# --------------------------------------------------------------------

def read_session(path: str | Path) -> tuple[dict, list[dict], dict | None]:
    """Doc lai mot buoi da ghi. Tra ve (thong tin dau, cac khung hinh, tong ket)."""
    meta: dict = {}
    frames: list[dict] = []
    summary: dict | None = None

    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue              # dong hong (mat dien giua chung) - bo qua
        kind = rec.get("kind")
        if kind == "meta":
            meta = rec
        elif kind == "summary":
            summary = rec
        else:
            frames.append(rec)

    return meta, frames, summary


def iter_frames(path: str | Path) -> Iterator[dict]:
    """Duyet tung khung hinh, khong nap ca file vao bo nho."""
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("kind") in ("meta", "summary"):
                continue
            yield rec


# --------------------------------------------------------------------

def summarize_session(frames: list[dict]) -> dict:
    """
    Tom tat mot buoi di thu.

    Nhung con so nay tra loi truc tiep cau "he thong co chay tot khong"
    ma khong phai xem lai ca buoi.
    """
    if not frames:
        return {"frames": 0}

    anchors = [f for f in frames if f.get("sightings")]
    fixes = [f for f in frames if f.get("fix")]
    said = [f for f in frames if f.get("said")]

    conf_counts: dict[str, int] = {}
    for f in fixes:
        c = f.get("confidence")
        if c:
            conf_counts[c] = conf_counts.get(c, 0) + 1

    gaps = [f["distance_since_fix"] for f in fixes
            if f.get("distance_since_fix") is not None]

    keys: dict[str, int] = {}
    for f in anchors:
        for s in f["sightings"]:
            keys[s["key"]] = keys.get(s["key"], 0) + 1

    duration = frames[-1].get("t", 0.0) - frames[0].get("t", 0.0)

    return {
        "frames": len(frames),
        "duration_s": round(duration, 1),
        "fps": round(len(frames) / duration, 1) if duration > 0 else 0.0,
        "frames_with_anchor": len(anchors),
        "anchor_rate": round(len(anchors) / len(frames), 3),
        "frames_localized": len(fixes),
        "localized_rate": round(len(fixes) / len(frames), 3),
        "instructions": len(said),
        "confidence_counts": conf_counts,
        "max_gap_m": round(max(gaps), 2) if gaps else None,
        "anchors_seen": keys,
    }
