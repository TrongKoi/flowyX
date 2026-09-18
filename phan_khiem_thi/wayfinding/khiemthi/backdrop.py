"""
BAN NEN cua can phong - va dia diem danh dau trong luc quet.

--------------------------------------------------------------------
NGUYEN LY ROBOT HUT BUI
--------------------------------------------------------------------

Robot hut bui KHONG nhan ra cai cap la cai cap. No biet day la vat la
vi SO VOI BAN NEN da dung tu nhung lan truoc.

Do la loi giai cho bai toan "co dinh hay tam thoi", va no tranh duoc
cai bay: phan biet bang HINH DANG la bai toan rat kho, vi mot cai cap
va mot cai ban thap trong giong nhau trong mot khung hinh - va "tam
thoi" khong phai thuoc tinh hinh dang nen khong co tap du lieu nao day
duoc.

    Co dinh   = co trong ban quet nen
    Tam thoi  = khong co trong nen nhung dang co bay gio
    Trong     = khong co gi trong nguong

--------------------------------------------------------------------
BAN NEN LAY DO SAU LON NHAT, KHONG PHAI TRUNG BINH
--------------------------------------------------------------------

Diem thiet ke quan trong nhat cua module nay.

Vat tam thoi chi lam do sau NGAN LAI, khong bao gio lam dai ra. Nen lay
gia tri LON NHAT tung quan sat duoc theo moi huong thi tu dong loai bo
nhung thu di ngang qua trong luc quet.

Nghia la nguoi quet khong phai don phong trong, khong phai duoi nguoi
ra khoi hanh lang. Cu di vai vong, ai di ngang qua cung khong sao.

Trung binh thi khong lam duoc dieu do - mot nguoi dung yen mot luc se
bi ghi vao nen thanh buc tuong.

--------------------------------------------------------------------
MOT LAN QUET, HAI CONG DUNG
--------------------------------------------------------------------

Viec di mot vong de dung ban nen CUNG CHINH LA viec danh dau dia diem.
Dia diem danh dau trong luc quet thay the hoan toan cho ma dan tuong:
khong dan gi, va nguoi dung tu dat ten theo cach ho goi.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from ..loi_chung.depth import Cell, DepthGrid, Novelty, classify_cell
from ..loi_chung.geometry import Pose2D, norm_angle

# Kich thuoc o luoi vi tri, met. Nho hon thi chinh xac hon nhung can
# quet ky hon moi phu het.
DEFAULT_CELL_M = 1.0

# So huong chia deu 360 do. 12 bin = moi bin 30 do, du tho de mot lan
# quet phu duoc ma du min de phan biet quay mat huong nao.
DEFAULT_HEADING_BINS = 12

# Do sau ngan hon nen bao nhieu thi coi la vat la
NOVELTY_ABS_M = 0.5
NOVELTY_REL = 0.25

# ---------- khop ban nen de DINH VI (dac ta muc 10) ----------
#
# Ban nen dung cho viec loc vat can CUNG CHINH LA mot ban do 3D tho cua
# toa nha. No dang chi duoc dung mot chieu - so hien tai voi nen de tim
# vat la. Nhung no chay duoc CA CHIEU NGUOC LAI: so hien tai voi nen de
# tim MINH DANG O O NAO.
#
# Do la dieu GoodMaps lam, chi khac la tho hon nhieu va khong ton them
# gi - vi ban do da co san roi.

# Ban kinh tim toi da, met. KHONG bao gio tim toan tang: moi hanh lang
# deu trong giong hanh lang, va hai dau toa nha se khop nham nhau.
SEARCH_MAX_M = 8.0

# So bin huong lech toi da con duoc xet
SEARCH_HEADING_BINS = 2

# Can it nhat bao nhieu o hop le de mot ung vien duoc tinh diem
MIN_OVERLAP_CELLS = 8

# Sai lech toi da cua ung vien tot nhat, met
MATCH_MAX_ERR_M = 0.6

# Ung vien tot nhat phai HON HAN ung vien nhi bao nhieu met.
#
# Day la dieu kien QUAN TRONG NHAT. No la phong thu truc tiep chong
# nhap nhang tri giac: neu hai cho trong ban nen khop gan bang nhau thi
# ta khong biet minh o cho nao trong hai cho do, va DOAN LA TE HON
# KHONG SUA (nguyen tac 1.1).
#
# Cung mot nguyen tac da dung cho bien trung chu.
MATCH_MARGIN_M = 0.3


@dataclass(frozen=True)
class Place:
    """Mot dia diem nguoi dung danh dau trong luc quet."""

    name: str
    pose: Pose2D
    note: str = ""


@dataclass(frozen=True)
class BackdropFix:
    """
    Ket qua khop ban nen de dinh vi - lop L4.

    KHONG bao gio duoc vuot quyen L1 (xac nhan braille) hay L2 (bien
    lon), va day la co y: ban nen chi duoc quet MOT LAN. Ban ghe bi
    dich, cua mo dong, nguoi dung - tat ca lam nen lech dan khoi thuc
    te theo thoi gian.

    No co ich o doan dai khong co bien nao de doc, chu khong phai de
    thay the viec doc bien.
    """

    x: float
    y: float
    err_m: float
    confidence: str              # "MEDIUM" | "LOW" - khong bao gio HIGH
    key: str


@dataclass
class Backdrop:
    """
    Ban nen do sau theo o vi tri, cong danh sach dia diem.

    Khoa la (o_x, o_y, bin_huong): cung mot cho nhung quay mat huong
    khac thi nhin thay canh khac han, nen phai tach rieng.
    """

    cell_m: float = DEFAULT_CELL_M
    heading_bins: int = DEFAULT_HEADING_BINS
    grids: dict[str, list[float]] = field(default_factory=dict)
    shape: tuple[int, int] | None = None       # (cols, rows)
    places: list[Place] = field(default_factory=list)

    # ---------- khoa ----------

    def key(self, pose: Pose2D) -> str:
        cx = math.floor(pose.x / self.cell_m)
        cy = math.floor(pose.y / self.cell_m)
        step = 360.0 / self.heading_bins
        b = int((norm_angle(pose.theta) + 180.0) // step) % self.heading_bins
        return f"{cx},{cy},{b}"

    # ---------- quet ----------

    def observe(self, pose: Pose2D, grid: DepthGrid) -> None:
        """
        Ghi mot lan quan sat vao ban nen.

        Lay do sau LON NHAT tung thay - xem phan dau file ve ly do.
        O khong dang tin thi bo qua, khong ghi de len so tot da co.
        """
        if self.shape is None:
            self.shape = (grid.cols, grid.rows)
        elif self.shape != (grid.cols, grid.rows):
            raise ValueError(
                f"Ban nen dung luoi {self.shape}, nhan duoc "
                f"{(grid.cols, grid.rows)} - khong so sanh duoc"
            )

        k = self.key(pose)
        cur = self.grids.get(k)
        if cur is None:
            cur = [0.0] * (grid.cols * grid.rows)
            self.grids[k] = cur

        for i, (d, c) in enumerate(zip(grid.depth, grid.confidence)):
            if classify_cell(d, c) is Cell.CHUA_BIET:
                continue                        # khong tin thi khong ghi
            if d > cur[i]:
                cur[i] = d

    def mark(self, name: str, pose: Pose2D, note: str = "") -> Place:
        """
        Danh dau mot dia diem. Day la 'marker' moi, thay ma dan tuong.

        Ten do NGUOI DUNG dat, theo cach ho goi cho do - khong phai ma
        so do he thong sinh ra.
        """
        name = name.strip()
        if not name:
            raise ValueError("Dia diem phai co ten")
        p = Place(name=name, pose=pose, note=note.strip())
        self.places.append(p)
        return p

    def nearest_place(self, pose: Pose2D,
                      within: float = 3.0) -> Place | None:
        """Dia diem da danh dau gan vi tri nay nhat."""
        best, best_d = None, within
        for p in self.places:
            d = math.hypot(p.pose.x - pose.x, p.pose.y - pose.y)
            if d < best_d:
                best, best_d = p, d
        return best

    # ---------- so sanh ----------

    def expected(self, pose: Pose2D) -> list[float] | None:
        """Do sau ky vong tai o vi tri nay, hoac None neu chua tung quet."""
        return self.grids.get(self.key(pose))

    def refine(self, pose: Pose2D, grid: DepthGrid) -> list[Novelty]:
        """
        Thu trong tung o la co san hay moi xuat hien.

        Tang THU HAI cua viec phan loai. Tang thu nhat - `classify_cell`
        trong depth.py - chi tra loi "do duoc gi". Tang nay doi chieu
        voi ban nen de tra loi "thu do co san khong".

        Chi o CO_VAT moi co cau tra loi. O TRONG thi khong co gi de doi
        chieu; o CHUA_BIET thi chinh so do da khong dang tin nen doi
        chieu no la vo nghia.

        Chua tung quet cho nay thi tra KHONG_RO chu KHONG doan la tam
        thoi: khong co nen de so thi khong the ket luan, va doan bua o
        day nghia la bao dong gia lien tuc o moi cho chua quet. Ben goi
        phai coi KHONG_RO nhu CO_VAT binh thuong - van canh bao, chi la
        khong noi them duoc "vat la".
        """
        base = self.expected(pose)
        out: list[Novelty] = []

        for i, (d, c) in enumerate(zip(grid.depth, grid.confidence)):
            if classify_cell(d, c) is not Cell.CO_VAT:
                out.append(Novelty.KHONG_RO)
                continue
            if base is None or base[i] <= 0.0:
                out.append(Novelty.KHONG_RO)    # chua co nen de so
                continue

            margin = max(NOVELTY_ABS_M, NOVELTY_REL * base[i])
            out.append(Novelty.TAM_THOI if d < base[i] - margin
                       else Novelty.CO_DINH)
        return out

    @property
    def scanned_cells(self) -> int:
        return len(self.grids)

    # ---------- khop de DINH VI (dac ta muc 10) ----------

    def _tam_o(self, khoa: str) -> tuple[float, float, int] | None:
        """Tam o va bin huong, suy nguoc tu khoa."""
        try:
            cx, cy, b = khoa.split(",")
            return ((int(cx) + 0.5) * self.cell_m,
                    (int(cy) + 0.5) * self.cell_m,
                    int(b))
        except (ValueError, TypeError):
            return None

    def _bin_cua(self, theta: float) -> int:
        step = 360.0 / self.heading_bins
        return int((norm_angle(theta) + 180.0) // step) % self.heading_bins

    def _lech_bin(self, a: int, b: int) -> int:
        """Khoang cach vong tron giua hai bin huong."""
        d = abs(a - b) % self.heading_bins
        return min(d, self.heading_bins - d)

    def match(self, pose: Pose2D, grid: DepthGrid, sigma_m: float = 2.0,
              search_max_m: float = SEARCH_MAX_M,
              max_err_m: float = MATCH_MAX_ERR_M,
              margin_m: float = MATCH_MARGIN_M,
              min_overlap: int = MIN_OVERLAP_CELLS) -> BackdropFix | None:
        """
        Tim xem hinh dang depth dang thay khop nhat voi cho nao trong nen.

        Day la buoc nang ban nen tu "loc vat can" len "nguon vi tri"
        (lop L4 trong bang thu bac tin cay).

        Ba dieu khien no an toan:

          - CHI TIM QUANH UOC TINH VIO, khong tim toan tang. Hai hanh
            lang giong het nhau o hai dau toa nha khong bao gio cung nam
            trong ban kinh tim.
          - QUY TAC HON HAN O NHI, giong het quy tac da dung cho bien
            trung chu. Cung mot nguyen tac, cung mot cach tu choi.
          - KHONG KHOP DUOC THI KHONG NAN. Suy giam em, khong sinh trang
            thai hong moi.

        Tra None khi khong du chac - va do la ket qua HOP LE, khong phai
        loi.
        """
        if self.shape != (grid.cols, grid.rows) or not self.grids:
            return None

        R = min(3.0 * sigma_m, search_max_m)
        bin0 = self._bin_cua(pose.theta)

        # --- buoc 1: lap tap ung vien quanh uoc tinh hien tai ---
        ung_vien: list[tuple[float, str, float, float]] = []
        for khoa, nen in self.grids.items():
            t = self._tam_o(khoa)
            if t is None:
                continue
            cx, cy, b = t
            if self._lech_bin(b, bin0) > SEARCH_HEADING_BINS:
                continue
            if math.hypot(cx - pose.x, cy - pose.y) > R:
                continue

            # --- buoc 2: sai lech, lay TRUNG VI ---
            #
            # Trung vi chu khong phai trung binh: mot nguoi dung chan
            # vai o se keo trung binh di rat xa, trong khi trung vi gan
            # nhu khong nhuc nhich.
            #
            # CAI GIA CUA LUA CHON NAY, phai biet truoc khi dung:
            # trung vi chi "thay" duoc dac trung nao phu TREN MOT NUA
            # so o hop le. Mot hoc tuong chi lam doi 3 trong 12 o thi
            # trung vi van bang 0, va o co hoc se cho diem Y HET o hanh
            # lang thuong - tuc la vo hinh.
            #
            # Do la danh doi co chu dich: chong nhieu tot, doi lai kem
            # nhay voi dac trung nho. Neu thuc dia cho thay bo lo qua
            # nhieu cho, huong sua la TANG DO PHAN GIAI LUOI chu khong
            # phai doi sang trung binh - doi sang trung binh se lam mot
            # nguoi di ngang qua du suc pha diem cua o dung.
            lech: list[float] = []
            for i, (d, c) in enumerate(zip(grid.depth, grid.confidence)):
                if classify_cell(d, c) is Cell.CHUA_BIET:
                    continue                      # phia quan sat khong tin
                if nen[i] <= 0.0:
                    continue                      # phia nen chua tung quet
                lech.append(abs(d - nen[i]))

            if len(lech) < min_overlap:
                continue
            lech.sort()
            n = len(lech)
            err = (lech[n // 2] if n % 2
                   else 0.5 * (lech[n // 2 - 1] + lech[n // 2]))
            ung_vien.append((err, khoa, cx, cy))

        if not ung_vien:
            return None

        # --- buoc 3: sap xep ---
        ung_vien.sort(key=lambda u: u[0])
        err, khoa, cx, cy = ung_vien[0]

        # --- buoc 4: ba dieu kien, phai dat CA BA ---
        if err >= max_err_m:
            return None

        if len(ung_vien) > 1:
            bien = ung_vien[1][0] - err
            if bien <= margin_m:
                return None            # nhap nhang -> khong sua gi ca
            manh = bien > 2.0 * margin_m
        else:
            # Chi mot ung vien trong ban kinh thi khong co gia thuyet
            # nao canh tranh, nen dieu kien "hon han o nhi" khong ap
            # dung duoc. Dac ta khong noi ro ca nay; o day chap nhan
            # nhung chi cho tin cay THAP.
            manh = False

        # --- buoc 5 ---
        return BackdropFix(x=cx, y=cy, err_m=err,
                           confidence="MEDIUM" if manh else "LOW",
                           key=khoa)

    # ---------- luu va nap ----------

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.write_text(json.dumps({
            "cell_m": self.cell_m,
            "heading_bins": self.heading_bins,
            "shape": list(self.shape) if self.shape else None,
            "grids": self.grids,
            "places": [
                {"name": pl.name, "x": pl.pose.x, "y": pl.pose.y,
                 "theta": pl.pose.theta, "note": pl.note}
                for pl in self.places
            ],
        }, ensure_ascii=False), encoding="utf-8")
        return p

    @staticmethod
    def load(path: str | Path) -> "Backdrop":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        shape = d.get("shape")
        return Backdrop(
            cell_m=float(d.get("cell_m", DEFAULT_CELL_M)),
            heading_bins=int(d.get("heading_bins", DEFAULT_HEADING_BINS)),
            grids={k: [float(x) for x in v] for k, v in d.get("grids", {}).items()},
            shape=(int(shape[0]), int(shape[1])) if shape else None,
            places=[
                Place(name=p["name"],
                      pose=Pose2D(float(p["x"]), float(p["y"]),
                                  float(p.get("theta", 0.0))),
                      note=p.get("note", ""))
                for p in d.get("places", [])
            ],
        )
