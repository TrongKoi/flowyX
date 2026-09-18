"""
KICH BAN C - doc bien, tai lieu, bang trang.

Rao can noi lam viec: tai lieu in, bien so phong, bang trang cuoc hop
hoan toan khong tiep can duoc voi nhan vien khiem thi.

Day la kich ban RE VA NHANH NHAT trong sau kich ban o Muc 2, vi no dung
lai gan nhu toan bo loi da co:
    - khoi OCR      : chinh la lop dinh vi chinh (anchors.RoomSignReader)
    - khoi giong noi: AsyncSpeech, chong lap va cat loi da lam roi
    - trietly an toan: khong doc nhung gi khong chac, y het Muc 11

Cai MOI o day chi co ba thu, va deu la thu ma doc nguyen mot trang van
ban khong the thieu:

  1. THU TU DOC. OCR tra ve cac o van ban khong theo thu tu nao. Doc
     lung tung thi nguoi nghe khong hieu gi. Phai gom dong, xep tren
     xuong duoi trai sang phai, va nhan biet bo cuc nhieu cot.

  2. CHIA DOAN. Doc lien mot trang A4 mat vai phut va khong the quay
     lai. Phai chia thanh doan va cho di chuyen qua lai.

  3. CO CHE ON DINH. Neu doc ngay khi vua nhan duoc chu, he thong se
     doc lai lien tuc moi khi nguoi dung nhuc nhich camera. Phai cho
     hinh on dinh vai khung hinh roi moi doc.
"""

from __future__ import annotations

import re
import statistics
from collections import Counter, deque
from dataclasses import dataclass, field
from enum import Enum

# Nguong do tin cay OCR. Duoi muc nay thi KHONG doc nhu la chac chan.
# Doc sai chinh ta cho nguoi khiem thi cung la mot dang "tu tin noi sai".
CONF_TRUSTED = 0.75
CONF_DOUBTFUL = 0.45

# Hai o van ban duoc coi la CUNG MOT DONG neu tam cua chung lech nhau
# duoi ty le nay so voi chieu cao o. 0.6 chiu duoc bien hoi nghieng.
LINE_TOLERANCE = 0.6

# Khoang trong ngang lon hon ty le nay so voi be rong anh thi coi la
# ranh gioi COT, khong phai khoang cach giua hai tu.
COLUMN_GAP_RATIO = 0.18


class ReadState(str, Enum):
    IDLE = "cho"                    # chua thay chu nao
    SETTLING = "dang_on_dinh"       # thay chu roi nhung hinh chua on
    READY = "san_sang"              # da on dinh, doc duoc
    READING = "dang_doc"


@dataclass
class TextBlock:
    """Mot o van ban do OCR tra ve."""

    text: str
    conf: float
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2.0

    @property
    def height(self) -> float:
        return max(1.0, self.y1 - self.y0)

    @staticmethod
    def from_ocr(item) -> "TextBlock":
        """Doc mot phan tu easyocr: (box, text, conf)."""
        box, text, conf = item[0], item[1], float(item[2])
        xs = [float(p[0]) for p in box]
        ys = [float(p[1]) for p in box]
        return TextBlock(text=str(text), conf=conf,
                         x0=min(xs), y0=min(ys), x1=max(xs), y1=max(ys))


def group_into_lines(blocks: list[TextBlock]) -> list[list[TextBlock]]:
    """
    Gom cac o van ban thanh dong, roi xep trai sang phai trong moi dong.

    Gom theo tam doc chu khong theo mep tren, vi chu hoa va chu thuong
    co mep tren khac nhau nhung cung nam tren mot dong.
    """
    if not blocks:
        return []

    ordered = sorted(blocks, key=lambda b: b.cy)
    lines: list[list[TextBlock]] = [[ordered[0]]]

    for blk in ordered[1:]:
        cur = lines[-1]
        ref_cy = statistics.mean(b.cy for b in cur)
        ref_h = statistics.mean(b.height for b in cur)
        if abs(blk.cy - ref_cy) <= LINE_TOLERANCE * ref_h:
            cur.append(blk)
        else:
            lines.append([blk])

    for ln in lines:
        ln.sort(key=lambda b: b.x0)
    return lines


def split_columns(lines: list[list[TextBlock]],
                  frame_width: float) -> list[list[list[TextBlock]]]:
    """
    Tach bo cuc nhieu cot.

    Bang trang cuoc hop va to roi thuong chia hai cot. Doc ngang qua ca
    hai cot thi cau chu tron vao nhau va vo nghia hoan toan.

    Cach nhan biet: neu PHAN LON cac dong deu co mot khoang trong ngang
    lon o gan cung mot vi tri, do la ranh gioi cot.
    """
    if len(lines) < 3:
        return [lines]                     # qua it dong de ket luan

    gap_threshold = COLUMN_GAP_RATIO * frame_width
    split_points: list[float] = []

    for ln in lines:
        if len(ln) < 2:
            continue
        for a, b in zip(ln, ln[1:]):
            gap = b.x0 - a.x1
            if gap > gap_threshold:
                split_points.append((a.x1 + b.x0) / 2.0)

    # Can it nhat mot nua so dong cung co khoang trong thi moi tin la cot
    if len(split_points) < max(2, len(lines) // 2):
        return [lines]

    boundary = statistics.median(split_points)
    left: list[list[TextBlock]] = []
    right: list[list[TextBlock]] = []

    for ln in lines:
        l = [b for b in ln if b.cx < boundary]
        r = [b for b in ln if b.cx >= boundary]
        if l:
            left.append(l)
        if r:
            right.append(r)

    return [c for c in (left, right) if c]


def line_text(line: list[TextBlock]) -> str:
    return " ".join(b.text.strip() for b in line if b.text.strip())


def reading_order(blocks: list[TextBlock], frame_width: float) -> list[str]:
    """Cac dong van ban theo dung thu tu nguoi doc se doc."""
    lines = group_into_lines(blocks)
    out: list[str] = []
    for column in split_columns(lines, frame_width):
        for ln in column:
            txt = line_text(ln)
            if txt:
                out.append(txt)
    return out


# --------------------------------------------------------------------

def chunk_lines(lines: list[str], max_chars: int = 180) -> list[str]:
    """
    Gom dong thanh doan vua nghe.

    Doc lien mot trang A4 mat vai phut va nguoi nghe khong the quay lai
    doan vua roi. Chia thanh doan de dieu huong duoc.

    Uu tien cat o cho ket thuc cau; neu khong co thi cat theo so ky tu.
    """
    chunks: list[str] = []
    buf: list[str] = []
    size = 0

    for ln in lines:
        buf.append(ln)
        size += len(ln) + 1
        ends_sentence = ln.rstrip().endswith((".", "!", "?", ":"))
        if size >= max_chars or (ends_sentence and size >= max_chars // 2):
            chunks.append(" ".join(buf))
            buf, size = [], 0

    if buf:
        chunks.append(" ".join(buf))
    return chunks


def describe_confidence(blocks: list[TextBlock]) -> tuple[str | None, float]:
    """
    Canh bao khi chu luot doc duoc khong dang tin.

    Doc van ban sai chinh ta cho nguoi khiem thi bang giong chac nich
    cung la mot dang "tu tin noi sai" - ho khong co cach nao kiem chung.
    Tha noi that la chu mo con hon.
    """
    if not blocks:
        return None, 0.0

    mean_conf = statistics.mean(b.conf for b in blocks)
    weak = sum(1 for b in blocks if b.conf < CONF_DOUBTFUL)
    ratio = weak / len(blocks)

    if mean_conf < CONF_DOUBTFUL or ratio > 0.5:
        return ("Chu doc duoc khong ro. Hay lai gan hon hoac chinh anh sang.",
                mean_conf)
    if mean_conf < CONF_TRUSTED or ratio > 0.2:
        return ("Mot so chu doc khong chac.", mean_conf)
    return None, mean_conf


_WS = re.compile(r"\s+")


def _fingerprint(lines: list[str]) -> str:
    """Dau van de so sanh hai lan doc co giong nhau khong."""
    return _WS.sub(" ", " ".join(lines)).strip().lower()


@dataclass
class ReadResult:
    say: str | None = None
    state: ReadState = ReadState.IDLE
    chunk_index: int = 0
    total_chunks: int = 0
    warning: str | None = None
    mean_conf: float = 0.0


@dataclass
class DocumentReader:
    """
    Doc van ban truoc camera, co dieu huong theo doan.

    Cach dung trong vong lap:
        r = reader.observe(ocr_results, frame_width)
        if r.say: speaker.speak(r.say)

    Va khi nguoi dung bam nut / ra lenh:
        reader.next_chunk() / prev_chunk() / repeat()
    """

    stable_frames: int = 3
    max_chars: int = 180
    auto_read_first: bool = True
    # Cua so xet on dinh. Chi can `stable_frames` khung hinh GIONG NHAU
    # trong `window` khung hinh gan nhat, KHONG can lien tiep.
    window: int = 8

    state: ReadState = ReadState.IDLE
    chunks: list[str] = field(default_factory=list)
    index: int = 0

    _recent: deque = field(default_factory=lambda: deque(maxlen=8))
    _spoken_fp: str = ""

    def __post_init__(self) -> None:
        self._recent = deque(maxlen=max(self.window, self.stable_frames))

    # ---------- quan sat ----------

    def observe(self, ocr_results, frame_width: float) -> ReadResult:
        blocks = [TextBlock.from_ocr(it) for it in ocr_results]
        blocks = [b for b in blocks if b.text.strip()]

        if not blocks:
            self._recent.clear()
            self.state = ReadState.IDLE
            return ReadResult(state=self.state)

        lines = reading_order(blocks, frame_width)
        fp = _fingerprint(lines)
        self._recent.append(fp)

        # --- co che on dinh: hai duong ---
        #
        # Ban dau cho nay doi cac khung hinh LIEN TIEP giong het nhau.
        # Voi nguoi run tay - Parkinson, run vo can, hoac don gian la
        # nguoi lon tuoi - chi can MOT khung hinh nhoe lam OCR doc lech
        # mot ky tu la bo dem ve 0, va he thong KHONG BAO GIO doc duoc.
        #
        # Nhung neu chi dem da so thi lai cham chuyen sang van ban moi:
        # cac ban ghi cu con trong cua so se lan at ban moi. Nen dung
        # hai duong:
        #
        #   Duong nhanh - cac khung hinh MOI NHAT nhat quan voi nhau:
        #       camera that su da chuyen sang cho khac, nhan ngay.
        #   Duong cham - khung hinh nhieu, lay ban DA SO trong cua so:
        #       bo qua cac khung hinh nhoe xen ke, van doc duoc nho
        #       nhung khung hinh net.
        #
        # Day cung la cach SightingFilter cua lop moc neo van lam.
        recent = list(self._recent)
        tail = recent[-self.stable_frames:]

        if len(tail) == self.stable_frames and len(set(tail)) == 1:
            fp = tail[0]                    # duong nhanh
        else:
            best_fp, best_n = Counter(recent).most_common(1)[0]
            if best_n < self.stable_frames:
                self.state = ReadState.SETTLING
                return ReadResult(state=self.state)
            fp = best_fp                    # duong cham, chiu nhieu

        # Da doc noi dung nay roi thi thoi, dung doc lai
        if fp == self._spoken_fp:
            self.state = ReadState.READY
            return ReadResult(state=self.state,
                              chunk_index=self.index,
                              total_chunks=len(self.chunks))

        warning, mean_conf = describe_confidence(blocks)
        self.chunks = chunk_lines(lines, self.max_chars)
        self.index = 0
        self._spoken_fp = fp
        self.state = ReadState.READY

        if not self.auto_read_first or not self.chunks:
            return ReadResult(state=self.state, warning=warning,
                              mean_conf=mean_conf,
                              total_chunks=len(self.chunks))

        self.state = ReadState.READING
        say = self.chunks[0]
        if warning:
            say = f"{warning} {say}"
        if len(self.chunks) > 1:
            say = f"{say} (doan 1 tren {len(self.chunks)})"

        return ReadResult(say=say, state=self.state, chunk_index=0,
                          total_chunks=len(self.chunks),
                          warning=warning, mean_conf=mean_conf)

    # ---------- dieu huong ----------

    def _current(self) -> ReadResult:
        if not self.chunks:
            return ReadResult(say="Chua doc duoc chu nao.", state=self.state)
        say = self.chunks[self.index]
        if len(self.chunks) > 1:
            say = f"{say} (doan {self.index + 1} tren {len(self.chunks)})"
        return ReadResult(say=say, state=ReadState.READING,
                          chunk_index=self.index, total_chunks=len(self.chunks))

    def next_chunk(self) -> ReadResult:
        if not self.chunks:
            return self._current()
        if self.index >= len(self.chunks) - 1:
            return ReadResult(say="Da het van ban.", state=self.state,
                              chunk_index=self.index,
                              total_chunks=len(self.chunks))
        self.index += 1
        return self._current()

    def prev_chunk(self) -> ReadResult:
        if not self.chunks:
            return self._current()
        if self.index <= 0:
            return ReadResult(say="Dang o doan dau.", state=self.state,
                              chunk_index=0, total_chunks=len(self.chunks))
        self.index -= 1
        return self._current()

    def repeat(self) -> ReadResult:
        return self._current()

    def total(self) -> int:
        return len(self.chunks)

    def read_all(self) -> str:
        return " ".join(self.chunks)

    def reset(self) -> None:
        """Quen van ban hien tai de doc lai tu dau."""
        self.chunks = []
        self.index = 0
        self._recent.clear()
        self._spoken_fp = ""
        self.state = ReadState.IDLE
