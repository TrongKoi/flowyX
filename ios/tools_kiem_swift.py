#!/usr/bin/env python3
"""Kiem tra tinh cho ma Swift khi khong co Xcode.

KHONG thay duoc trinh bien dich: chi bat duoc loi cau truc va ten goi sai.
Chay:  python3 ios/tools_kiem_swift.py
"""
import re, sys, glob, os

GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Flowy")
loi = []


def bo_chuoi_va_ghi_chu(s):
    """Bo ghi chu va chuoi de dem ngoac cho dung."""
    ra, i, n = [], 0, len(s)
    while i < n:
        if s.startswith('"""', i):
            j = s.find('"""', i + 3)
            i = n if j < 0 else j + 3
        elif s[i] == '"':
            i += 1
            while i < n and s[i] != '"':
                i += 2 if s[i] == '\\' else 1
            i += 1
        elif s.startswith('//', i):
            i = s.find('\n', i)
            if i < 0:
                i = n
        elif s.startswith('/*', i):
            j = s.find('*/', i)
            i = n if j < 0 else j + 2
        else:
            ra.append(s[i]); i += 1
    return ''.join(ra)


tep = sorted(glob.glob(os.path.join(GOC, "**", "*.swift"), recursive=True))
ma = {f: open(f, encoding="utf-8").read() for f in tep}

# 1. Can bang ngoac
for f, s in ma.items():
    t = bo_chuoi_va_ghi_chu(s)
    for mo, dong in "{}", "()", "[]":
        if t.count(mo) != t.count(dong):
            loi.append(f"{os.path.basename(f)}: lech ngoac {mo}{dong}: {t.count(mo)} mo, {t.count(dong)} dong")

# Quet TEN GOI tren ban da bo ghi chu: ten tep trong ghi chu (vd "Lich.kt")
# khong phai loi.
sach = {f: bo_chuoi_va_ghi_chu(s) for f, s in ma.items()}
tat_ca = "\n".join(sach.values())
tat_ca_co_ghi_chu = "\n".join(ma.values())

# 2. Kieu duoc dinh nghia
kieu = set(re.findall(r"(?:public |final |private )*(?:struct|class|enum|protocol) (\w+)", tat_ca))
kieu |= {"View", "App", "Scene", "Color", "Date", "Data", "String", "Int", "Double", "Bool", "UUID"}

# 3. Moi View dung trong FlowyApp phai co that
for t in re.findall(r"case \.\w+: (\w+)\(", sach[os.path.join(GOC, "FlowyApp.swift")]):
    if t not in kieu:
        loi.append(f"FlowyApp dung View khong co: {t}")

# 4. Mau.X phai co trong enum Mau
than_mau = re.search(r"enum Mau \{(.*?)\n\}", tat_ca, re.S).group(1)
co_mau = set(re.findall(r"static (?:let|func) (\w+)", than_mau))
for m in sorted(set(re.findall(r"\bMau\.(\w+)", tat_ca))):
    if m not in co_mau:
        loi.append(f"Mau.{m} khong co trong enum Mau")

# 5. Lich.X, DemNguoc.X, LoiNhanNgay.X, DocxViet.X
def thanh_vien(ten):
    m = re.search(r"(?:enum|struct|final class|class) %s\b[^\{]*\{(.*?)\n\}\n" % ten, tat_ca, re.S)
    if not m:
        return None
    b = m.group(1)
    # Ke ca kieu long ben trong (DocxViet.HoSo, DocxViet.Khoi).
    return (set(re.findall(r"(?:static )?(?:let|var|func) (\w+)", b))
            | set(re.findall(r"case (\w+)", b))
            | set(re.findall(r"(?:enum|struct|class) (\w+)", b)))

for lop in ["Lich", "DemNguoc", "LoiNhanNgay", "DocxViet", "SoLich"]:
    tv = thanh_vien(lop)
    if tv is None:
        loi.append(f"khong tim thay dinh nghia {lop}")
        continue
    for m in sorted(set(re.findall(r"\b%s\.(\w+)" % lop, tat_ca))):
        if m not in tv and m not in kieu:
            loi.append(f"{lop}.{m} khong co")

# 6. Khong con tham chieu toi thu da xoa
for xoa in ["ManHinhSo", "VongThoiGianCu"]:
    if re.search(r"\b%s\b" % xoa, tat_ca):
        loi.append(f"con tham chieu toi {xoa} da xoa")

# 7. @EnvironmentObject phai duoc cap o FlowyApp
cap = set(re.findall(r"\.environmentObject\((?:model\.)?(\w+)\)", sach[os.path.join(GOC, "FlowyApp.swift")]))
ten_lop = {"soLich": "SoLich", "soNhatKy": "SoNhatKy", "settings": "AppSettings", "model": "FlowyModel",
           "focus": "FocusModel", "tienDo": "SoTienDo", "bienBan": "SoBienBan", "hoanTac": "HoanTacModel"}
da_cap = {ten_lop[c] for c in cap if c in ten_lop}
for f, s in ma.items():
    for k in set(re.findall(r"@EnvironmentObject var \w+: (\w+)", sach[f])):
        if k not in da_cap:
            loi.append(f"{os.path.basename(f)}: @EnvironmentObject {k} chua duoc cap o FlowyApp")

print("\n".join(loi) if loi else f"OK - {len(tep)} tep Swift, khong thay loi cau truc")
sys.exit(1 if loi else 0)
