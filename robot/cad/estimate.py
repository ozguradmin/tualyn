#!/usr/bin/env python3
"""Kıpır v1 baskı tahmini: her STL'i PrusaSlicer CLI ile dilimler,
gram ve süre çıkarır, baski_tahmini.md tablosunu yazar.

Kullanım:  python3 estimate.py   (prusa-slicer PATH'te olmalı)
"""
import os
import re
import shutil
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE = os.path.join(HERE, "slicer", "pla_020_20pct.ini")

# parça, adet, açıklama
PARTS = [
    ("taban", 1, "Taban: motor duvarları + misket direkleri tek parça (ters basılır)"),
    ("ust_kat", 1, "Üst kat + 4 direk tek parça (ters basılır)"),
    ("boyun", 1, "Boyun"),
    ("kafa_ray", 1, "Kafa rayı"),
    ("cene_sol", 1, "Sol çene"),
    ("cene_sag", 1, "Sağ çene"),
    ("teker_kapak", 2, "Misket kapağı"),
    ("sensor_tutucu", 1, "HC-SR04 tutucu"),
    ("kulak_sol", 1, "Sol kulak/anten (isteğe bağlı, beyaz/şeffaf)"),
    ("kulak_sag", 1, "Sağ kulak/anten (isteğe bağlı, beyaz/şeffaf)"),
]


def slicer_cmd():
    exe = shutil.which("prusa-slicer") or shutil.which("PrusaSlicer")
    if not exe:
        raise SystemExit("prusa-slicer bulunamadı")
    cmd = [exe]
    if not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
        cmd = ["xvfb-run", "-a", exe]
    return cmd


def parse_time(t):
    h = re.search(r"(\d+)h", t)
    m = re.search(r"(\d+)m", t)
    d = re.search(r"(\d+)d", t)
    return (int(d.group(1)) * 1440 if d else 0) + (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)


def slice_one(stl, tmp):
    out = os.path.join(tmp, os.path.basename(stl) + ".gcode")
    res = subprocess.run(slicer_cmd() + ["--export-gcode", "--load", PROFILE, "--center", "128,128",
                                         "-o", out, stl], capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(res.stdout + res.stderr)
    g = t = None
    with open(out) as f:
        for line in f:
            if line.startswith("; total filament used [g]"):
                g = float(line.split("=")[1])
            elif line.startswith("; estimated printing time (normal mode)"):
                t = parse_time(line.split("=")[1])
    log = res.stdout + res.stderr
    notes = []
    if "Low bed adhesion" in log:
        notes.append("5 mm brim önerilir")
    if "Floating" in log or "Long bridging" in log or "Collapsing" in log:
        notes.append("destek gerekebilir")
    return g, t, ", ".join(notes)


def main():
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, qty, desc in PARTS:
            stl = os.path.join(HERE, "stl", f"kipir_{name}.stl")
            g, t, warn = slice_one(stl, tmp)
            rows.append((name, qty, desc, g, t, warn))
    tg = sum(r[1] * r[3] for r in rows)
    tt = sum(r[1] * r[4] for r in rows)
    tg_core = sum(r[1] * r[3] for r in rows if not r[0].startswith("kulak"))
    tt_core = sum(r[1] * r[4] for r in rows if not r[0].startswith("kulak"))
    lines = [
        "# Baskı tahmini (PrusaSlicer, otomatik)",
        "",
        "Profil: `slicer/pla_020_20pct.ini`: 0.4 mm nozül, 0.2 mm katman, 3 duvar, "
        "%20 gyroid dolgu, destek yok, PLA (1.24 g/cm³). PETG ~%2 daha ağır çıkar.",
        "",
        "| Parça | Adet | Gram (1 adet) | Süre (1 adet) | Not |",
        "|---|---:|---:|---:|---|",
    ]
    for name, qty, desc, g, t, warn in rows:
        lines.append(f"| `kipir_{name}.stl`: {desc} | {qty} | {g:.0f} g | {t // 60} sa {t % 60} dk | {warn} |")
    lines += [
        f"| **Toplam (kulaklar hariç)** | | **{tg_core:.0f} g** | **{tt_core // 60} sa {tt_core % 60} dk** | |",
        f"| **Toplam (kulaklar dahil)** | | **{tg:.0f} g** | **{tt // 60} sa {tt % 60} dk** | |",
        "",
        "Süreler hızlı olmayan, klasik bir yazıcı içindir; Bambu/Klipper makineler 2-3 kat hızlıdır.",
    ]
    with open(os.path.join(HERE, "baski_tahmini.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
