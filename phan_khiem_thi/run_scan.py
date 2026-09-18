#!/usr/bin/env python3
"""
Quet mot khu vuc de dung BAN NEN do sau - dac ta muc 8.1.

--------------------------------------------------------------------
CACH DUNG
--------------------------------------------------------------------

    python3 run_scan.py --out config/backdrop_tang3.json

Roi mo app tren dien thoai, tro ve dia chi in ra, va di CHAM mot vong
khu vuc, quet camera trai-phai. Nhan Ctrl-C de luu.

Nguoi quet phai la NGUOI SANG MAT. Day la viec chuan bi mot lan cho moi
tang, khong phai viec nguoi dung cuoi lam.

--------------------------------------------------------------------
VI SAO LAY MAX CHU KHONG PHAI TRUNG BINH
--------------------------------------------------------------------

Diem thiet ke quan trong nhat cua ca quy trinh quet.

Vat tam thoi chi lam do sau NGAN LAI, khong bao gio lam dai ra. Lay gia
tri LON NHAT tung quan sat duoc theo moi huong thi nhung thu di ngang
qua trong luc quet tu dong bi loai.

Nghia la nguoi quet KHONG phai don phong trong, KHONG phai duoi nguoi
ra khoi hanh lang. Cu di vai vong, ai di ngang qua cung khong sao.

Trung binh thi khong lam duoc dieu do: mot nguoi dung yen mot luc se bi
ghi vao nen thanh mot buc tuong, va ve sau buc tuong that o do se bi
bao la "vat tam thoi" mai mai.

Logic nay nam trong `Backdrop.observe()`; tep nay chi la lop vo chay.
"""

from __future__ import annotations

import argparse
import signal
import sys
import time

from wayfinding.khiemthi.backdrop import Backdrop
from wayfinding.loi_chung.bridge import BridgeReply, BridgeServer, PhoneUpdate, local_ip


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Quet dung ban nen do sau cho mot tang")
    ap.add_argument("--out", required=True,
                    help="tep JSON ban nen se ghi ra")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--cell-m", type=float, default=1.0,
                    help="kich thuoc o luoi vi tri, met")
    ap.add_argument("--heading-bins", type=int, default=12,
                    help="so bin huong chia deu 360 do")
    ap.add_argument("--tiep-tuc", action="store_true",
                    help="nap ban nen da co roi quet bo sung vao do")
    args = ap.parse_args()

    if args.tiep_tuc:
        try:
            nen = Backdrop.load(args.out)
            print(f"[NAP] tiep tuc tu {args.out} - "
                  f"{nen.scanned_cells} o da quet")
        except (OSError, ValueError) as e:
            print(f"[LOI] khong nap duoc {args.out}: {e}")
            sys.exit(1)
    else:
        nen = Backdrop(cell_m=args.cell_m, heading_bins=args.heading_bins)

    dem = {"goi": 0, "co_depth": 0, "bo_qua": 0}
    moc_thoi_gian = [time.time()]

    def on_update(upd: PhoneUpdate) -> BridgeReply:
        dem["goi"] += 1

        # Khong co pose thi khong biet ghi vao o nao. Khong co depth thi
        # khong co gi de ghi. Ca hai truong hop deu bo qua im lang -
        # dien thoai co the gui goi khong day du trong luc khoi dong.
        if upd.pose is None or upd.depth is None:
            dem["bo_qua"] += 1
            return BridgeReply(state="dang_quet")

        try:
            nen.observe(upd.pose, upd.depth)
        except ValueError as e:
            # Doi kich thuoc luoi giua chung -> khong so sanh duoc voi
            # phan da quet. Bao ro thay vi ghi hon lon.
            print(f"\n[LOI] {e}")
            dem["bo_qua"] += 1
            return BridgeReply(state="loi_luoi")

        dem["co_depth"] += 1

        gio = time.time()
        if gio - moc_thoi_gian[0] > 2.0:
            moc_thoi_gian[0] = gio
            print(f"\r[QUET] {nen.scanned_cells} o  |  "
                  f"{dem['co_depth']} khung co depth  |  "
                  f"vi tri ({upd.pose.x:.1f}, {upd.pose.y:.1f})   ",
                  end="", flush=True)

        return BridgeReply(state="dang_quet",
                           x=upd.pose.x, y=upd.pose.y, theta=upd.pose.theta)

    server = BridgeServer(port=args.port, on_update=on_update)

    da_luu = {"xong": False}

    def luu_va_thoat(*_):
        # Nhan duoc ca SIGINT lan SIGTERM, hoac Ctrl-C hai lan, thi ham
        # nay bi goi lai. Khong chan thi ghi tep hai lan va in log hai
        # lan - lam nguoi quet tuong co hai ban nen.
        if da_luu["xong"]:
            return
        da_luu["xong"] = True

        print()
        if nen.scanned_cells == 0:
            print("[BO] Chua quet duoc o nao - khong ghi tep.")
            print("     Kiem tra dien thoai da gui truong depth chua.")
            server.stop()
            sys.exit(1)
        duong = nen.save(args.out)
        print(f"[LUU] {duong}")
        print(f"      {nen.scanned_cells} o, luoi {nen.shape}, "
              f"{len(nen.places)} dia diem danh dau")
        print(f"      goi nhan: {dem['goi']}, dung duoc: {dem['co_depth']}, "
              f"bo qua: {dem['bo_qua']}")
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, luu_va_thoat)
    signal.signal(signal.SIGTERM, luu_va_thoat)

    server.start()
    print(f"[SAN SANG] tro dien thoai ve  http://{local_ip()}:{args.port}")
    print("[HUONG DAN] di CHAM mot vong, quet camera trai-phai.")
    print("            nguoi di ngang qua khong sao - xem docstring dau tep.")
    print("            Ctrl-C de luu.")

    while True:
        time.sleep(0.5)


if __name__ == "__main__":
    main()
