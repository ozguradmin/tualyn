#!/usr/bin/env python3
"""Bütçe kademelerini tek bir karşılaştırma görseline (docs/butce.png) çizer.

Önce kademe renderlarını üretir (OpenSCAD, cad/kipir.scad içindeki `kademe`
değişkeni), sonra yazıları ekler.  Kullanım:  python3 docs/butce_ciz.py
Gerekenler: openscad (ekransız sunucuda xvfb-run), Pillow.
"""
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SCAD = os.path.join(HERE, "..", "cad", "kipir.scad")
OUT = os.path.join(HERE, "butce.png")

KADEMELER = [
    {
        "kademe": 1, "fiyat": "≈ 2.250–3.350 TL", "ad": "Sade",
        "alt": "baskı tanıdıkta/atölyede: ~1.300 TL",
        "maddeler": ["Telefondan sürülür, tablette yüz", "Engelde durur, uyur, uyanır", "Tek powerbank, kulaksız"],
    },
    {
        "kademe": 2, "fiyat": "≈ 2.650–3.750 TL", "ad": "Kıpır v1",
        "alt": "baskı tanıdıkta/atölyede: ~1.700 TL",
        "maddeler": ["Sade'nin hepsi", "Motorlara ayrı pil: daha sağlam", "Kulaklarda renkli ışık"],
    },
    {
        "kademe": 3, "fiyat": "≈ 3.850–4.950 TL", "ad": "Göz",
        "alt": "baskı tanıdıkta/atölyede: ~2.900 TL",
        "maddeler": ["v1 + kameralı ESP32-S3 kartı", "Ev Wi-Fi'ından Claude'a fotoğraf yollar", "Gördüğünü tablette yazar, gezer"],
    },
    {
        "kademe": 4, "fiyat": "≈ 4.200–5.300 TL", "ad": "Göz + Ses",
        "alt": "baskı tanıdıkta/atölyede: ~3.250 TL",
        "maddeler": ["Göz + mikrofon + hoparlör", "Sesli konuşur", "Claude ile konuşması için evde PC gerekir"],
    },
    {
        "kademe": "kol", "fiyat": "≈ 21.000–29.000 TL", "ad": "Öğrenen kol (SO-101)",
        "alt": "ayrı masa istasyonu · temsili görsel",
        "maddeler": ["Gösterimden iş öğrenir (LeRobot)", "Parçalar yurt dışından, gümrüklü", "Spark gerekmez; dizüstü/bulut yeter"],
    },
]

PANEL_W, IMG_H, CAP_H = 600, 560, 230
COLS = 3


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for d in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu", "/Library/Fonts"):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def render(k, path):
    cmd = ["openscad"]
    if not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
        cmd = ["xvfb-run", "-a", "openscad"]
    if k == "kol":
        args = ["-D", 'part="kol_sahnesi"', "--camera=0,0,0,62,0,30,0"]
    else:
        args = ["-D", 'part="assembly"', "-D", f"kademe={k}", "--camera=0,0,0,68,0,50,0"]
    subprocess.run(cmd + ["-q"] + args + ["--viewall", "--autocenter", "--imgsize=1200,1200",
                                          "--colorscheme=Tomorrow", "-o", path, SCAD], check=True)


def main():
    rows = (len(KADEMELER) + COLS - 1) // COLS
    head_h, foot_h = 130, 70
    W = PANEL_W * COLS
    H = head_h + rows * (IMG_H + CAP_H) + foot_h
    sheet = Image.new("RGB", (W, H), "#f7f7f5")
    d = ImageDraw.Draw(sheet)
    d.text((30, 28), "Kıpır: bütçeye göre ne çıkar?", font=font(46, True), fill="#1d2733")
    d.text((32, 88), "Toplamlar 3D baskı stüdyoda yapılırsa (1.150–2.250 TL dahil). Telefon, tablet ve powerbank zaten var sayıldı.",
           font=font(21), fill="#516070")
    with tempfile.TemporaryDirectory() as tmp:
        for i, k in enumerate(KADEMELER):
            png = os.path.join(tmp, f"k{i}.png")
            render(k["kademe"], png)
            im = Image.open(png).convert("RGB").resize((PANEL_W, PANEL_W))
            im = im.crop((0, (PANEL_W - IMG_H) // 2, PANEL_W, (PANEL_W - IMG_H) // 2 + IMG_H))
            x = (i % COLS) * PANEL_W
            y = head_h + (i // COLS) * (IMG_H + CAP_H)
            sheet.paste(im, (x, y))
            cy = y + IMG_H
            d.rectangle([x + 14, cy, x + PANEL_W - 14, cy + CAP_H - 18], fill="white", outline="#d9dee5")
            d.text((x + 32, cy + 14), k["fiyat"], font=font(34, True), fill="#c2410c")
            d.text((x + 32, cy + 60), k["ad"], font=font(27, True), fill="#1d2733")
            d.text((x + 32, cy + 96), k["alt"], font=font(18), fill="#6b7785")
            for j, m in enumerate(k["maddeler"]):
                d.text((x + 32, cy + 128 + j * 27), "• " + m, font=font(20), fill="#1d2733")
    # 6. kutu: yapay zekâ notu
    if len(KADEMELER) % COLS:
        x = (len(KADEMELER) % COLS) * PANEL_W
        y = head_h + (rows - 1) * (IMG_H + CAP_H)
        d.rectangle([x + 14, y + 20, x + PANEL_W - 14, y + IMG_H + CAP_H - 18], fill="white", outline="#d9dee5")
        d.text((x + 36, y + 44), "Yapay zekâ şart mı?", font=font(32, True), fill="#1d2733")
        satirlar = [
            ("Hayır. 1. ve 2. kademe onsuz", False), ("çalışır: sürersin, yüzü ve", False),
            ("ruh hâlleri döner, engelde durur.", False), ("", False),
            ("3. ve 4. kademede robot ev", False), ("Wi-Fi'ından Claude'a kendisi", False),
            ("istek atar (tablet çok eski,", False), ("sadece yazıyı gösterir).", False), ("", False),
            ("İstek başı API maliyeti:", True), ("• Haiku 5.5: ~1–5 kuruş", False),
            ("• Opus 5.5: ~0,5–1,5 TL", False), ("", False),
            ("Gezerken sürekli soran bir", False), ("robot için Haiku mantıklı.", False),
        ]
        for j, (t, b) in enumerate(satirlar):
            d.text((x + 36, y + 100 + j * 34), t, font=font(22, b), fill="#1d2733")
    d.text((30, H - 52), "Fiyatlar KDV dahil, 24 Ekim 2026 mağaza sayfaları. Parça kargoları (~100–400 TL) hariç. "
           "3–4. kademenin kamera/hoparlör tutucuları ve yazılımı henüz hazır değil.",
           font=font(18), fill="#6b7785")
    sheet.save(OUT, optimize=True)
    print("yazıldı:", OUT)


if __name__ == "__main__":
    main()
