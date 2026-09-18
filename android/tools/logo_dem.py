#!/usr/bin/env python3
"""Sinh ban logo cho CHE DO DEM tu tep logo goc.

Chay lai moi khi nhom xuat logo moi:

    python3 android/tools/logo_dem.py

Quy tac doi mau (xem res/layout/khoi_logo.xml de biet vi sao):
    · diem co R - B > 25  -> vang/cam, GIU NGUYEN
    · moi diem con lai    -> muc navy, doi sang mau nga #E8E6F0
    · alpha giu nguyen, nen vien ram van muot

Khong ve lai logo, khong doi hinh dang hay ty le.
"""
import os, sys
from PIL import Image

NGA = (232, 230, 240)          # = @color/chu trong values-night/colors.xml
GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app', 'src', 'main', 'res')


def doi(src: str, dst: str) -> tuple[int, int]:
    im = Image.open(src).convert('RGBA')
    px = im.load()
    doi_diem = giu = 0
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if r - b > 25:
                giu += 1
                continue
            px[x, y] = (*NGA, a)
            doi_diem += 1
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im.save(dst)
    return doi_diem, giu


def main() -> int:
    tong = 0
    for md in ('mdpi', 'hdpi', 'xhdpi', 'xxhdpi', 'xxxhdpi'):
        src = os.path.join(GOC, f'drawable-{md}', 'logo_ngang.png')
        if not os.path.exists(src):
            continue
        d, g = doi(src, os.path.join(GOC, f'drawable-night-{md}', 'logo_ngang.png'))
        print(f'{md:8} doi {d:6} diem muc, giu {g:6} diem vang/cam')
        tong += 1
    if tong == 0:
        print('Khong thay tep logo nao trong res/drawable-*/', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
