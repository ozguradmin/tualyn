#!/usr/bin/env python3
"""Kıpır Mini seçeneklerini telefonla yan yana gösteren görseli çizer (docs/mini.png).

cad/mini_konsept.scad'ı OpenSCAD ile çizer, altına fiyat ve özellikleri yazar.
Kullanım:  python3 docs/mini_ciz.py    Gerekenler: openscad (ekransızda xvfb-run), Pillow.
Rakamlar docs/MINI.md ile aynı tutulmalı.
"""
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SCAD = os.path.join(HERE, "..", "cad", "mini_konsept.scad")
OUT = os.path.join(HERE, "mini.png")

# (görseldeki yatay konum oranı, renk, ad, boy, fiyat, maddeler)
SECENEKLER = [
    (0.42, "#2a78d6", "Kıpır Mini 4", "~8 cm boy, 8 servo", "FIYAT", ["dört bacakla yürür", "ekran yüz", "Claude'a istek atar"]),
    (0.63, "#eb6834", "Kıpır Mini 2", "~12 cm boy, 4 servo", "FIYAT", ["iki ayakla paytak yürür", "240×240 ekran yüz", "Türkçe sesli sohbet"]),
    (0.83, "#1baf7a", "Kıpır Küp", "~9 cm boy, 2 servo", "FIYAT", ["yürümez, başını çevirir", "kamerayla yüzünü izler", "Türkçe sesli sohbet"]),
]
W, IMG_H, CAP_H, HEAD_H = 1800, 900, 250, 120


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for d in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu", "/Library/Fonts"):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def render(path):
    cmd = ["openscad"]
    if not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
        cmd = ["xvfb-run", "-a", "openscad"]
    subprocess.run(cmd + ["-q", "-o", path, f"--imgsize={W},{IMG_H}", "--camera=-15,0,60,72,0,22,780",
                          "--colorscheme=Tomorrow", SCAD], check=True)


def main():
    sheet = Image.new("RGB", (W, HEAD_H + IMG_H + CAP_H), "#f7f7f5")
    d = ImageDraw.Draw(sheet)
    d.text((30, 26), "Kıpır Mini: masaüstü boyunda üç seçenek", font=font(44, True), fill="#1d2733")
    d.text((32, 82), "Temsili boyut karşılaştırması; soldaki telefon ölçek için (16 cm). "
           "Fiyatlar Türkiye'de stokta olan parçalarla, KDV dahil.", font=font(20), fill="#516070")
    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "k.png")
        render(png)
        sheet.paste(Image.open(png).convert("RGB"), (0, HEAD_H))
    d.text((395, HEAD_H + 640), "telefon (16 cm)", font=font(22), fill="#6b7785")
    cw = 330
    for fx, renk, ad, boy, fiyat, maddeler in SECENEKLER:
        x = int(W * fx) - cw // 2
        y = HEAD_H + IMG_H - 10
        d.rectangle([x, y, x + cw, y + CAP_H - 20], fill="white", outline="#d9dee5")
        d.rectangle([x, y, x + 8, y + CAP_H - 20], fill=renk)
        d.text((x + 24, y + 12), ad, font=font(28, True), fill="#1d2733")
        d.text((x + 24, y + 50), boy, font=font(18), fill="#6b7785")
        d.text((x + 24, y + 78), fiyat, font=font(30, True), fill="#c2410c")
        for j, m in enumerate(maddeler):
            d.text((x + 24, y + 124 + j * 30), "• " + m, font=font(20), fill="#1d2733")
    sheet.save(OUT, optimize=True)
    print("yazıldı:", OUT)


if __name__ == "__main__":
    main()
