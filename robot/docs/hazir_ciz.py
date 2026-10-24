#!/usr/bin/env python3
"""Hazır robotların Türkiye'ye gelmiş tahmini fiyatlarını Kıpır kademeleriyle
yan yana çizer (docs/hazir.png).  Kullanım:  python3 docs/hazir_ciz.py
Gereken: Pillow.  Rakamlar docs/HAZIR_ROBOTLAR.md ile aynı tutulmalı.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hazir.png")

# Gruplar: renk kimliği (doğrulanmış kategorik sıra: mavi, turuncu, su yeşili, sarı)
GRUPLAR = {
    "kendin": ("Kendin yap (Kıpır)", "#2a78d6"),
    "kalkar": ("Yürür, düşünce kendi kalkar", "#eb6834"),
    "yurur": ("Yürür, kalkması belgeli değil", "#1baf7a"),
    "yurumez": ("Yürümez (masa/teker), konuşur", "#eda100"),
}

# (grup, ad, alt satır, en az TL, en çok TL, ölçek dışı metni)
SATIRLAR = [
    ("kendin", "Kıpır v1 (2. kademe)", "tekerli, tablet yüz, telefondan sürülür", 2650, 3750, None),
    ("kendin", "Kıpır Göz + Ses (4. kademe)", "kamera + Claude + sesli konuşma", 4200, 5300, None),
    ("kalkar", "Petoi Bittle X V2 (kendin getir)", "köpek, 0,3 kg; petoi.com'dan, gümrük dahil", 29900, 41000, None),
    ("kalkar", "Hugging Face Microduck", "Türkiye'ye göndermiyor; aracıyla, 4-6 ay", 34000, 46000, None),
    ("kalkar", "Hiwonder Tonybot (kendin getir)", "insansı, 38 cm; hiwonder.com'dan", 37200, 51500, None),
    ("kalkar", "Petoi Bittle X V2 (Türk satıcı)", "ithalatçı ilanı, hepsi tükendi", 44400, 51700, None),
    ("kalkar", "Unitree Go2 Air (Türk satıcı)", "15 kg gerçek robot köpek", 70000, 70000, "234–291 bin TL"),
    ("yurur", "Open Duck Mini v2 (kendin yap)", "14 servo, yarım kılavuz, ciddi proje", 30000, 40000, None),
    ("yurur", "Hiwonder MechDog (Türk satıcı)", "ön sipariş, 4-8 hafta", 53400, 61700, None),
    ("yurumez", "Loona (Türk satıcı, 2 yıl garanti)", "tekerli robot köpek, GPT sesli sohbet", 32900, 41500, None),
    ("yurumez", "Reachy Mini Wireless", "konuşur, kafasını oynatır; bacak yok", 39700, 48700, None),
]

W, LEFT, RIGHT, TOP, ROW, BOT = 1900, 600, 360, 210, 74, 120
XMAX = 70000


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for d in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu", "/Library/Fonts"):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def bin_tl(v):
    return f"{v / 1000:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def main():
    H = TOP + ROW * len(SATIRLAR) + BOT
    im = Image.new("RGB", (W, H), "#fcfcfb")
    d = ImageDraw.Draw(im)
    plot_w = W - LEFT - RIGHT

    def x(v):
        return LEFT + plot_w * min(v, XMAX) / XMAX

    d.text((30, 26), "Hazır robot mu, Kıpır mı? Türkiye'ye gelmiş tahmini fiyat", font=font(40, True), fill="#0b0b0b")
    d.text((32, 82), "Çubuk = en az–en çok tahmin (KDV, kargo, gümrük dahil). 1 USD = 49,65 TL, 1 EUR = 55,60 TL (TCMB, 23.10.2026).",
           font=font(20), fill="#52514e")
    lx = 32
    for key in GRUPLAR:
        ad, renk = GRUPLAR[key]
        d.rounded_rectangle([lx, 128, lx + 26, 146], radius=4, fill=renk)
        d.text((lx + 36, 125), ad, font=font(20), fill="#0b0b0b")
        lx += 36 + d.textlength(ad, font=font(20)) + 40

    # kullanıcının bütçesi: 5-10 bin TL
    d.rectangle([x(5000), TOP - 14, x(10000), TOP + ROW * len(SATIRLAR)], fill="#eef3fb")
    d.text((x(5000) + 6, TOP - 40), "bütçen", font=font(18, True), fill="#2a78d6")

    # ızgara ve eksen
    for v in range(0, XMAX + 1, 10000):
        gx = x(v)
        d.line([gx, TOP - 14, gx, TOP + ROW * len(SATIRLAR)], fill="#e1e0d9" if v else "#c3c2b7", width=1 if v else 2)
        etiket = "0" if v == 0 else f"{v // 1000} bin"
        tw = d.textlength(etiket, font=font(18))
        d.text((gx - tw / 2, TOP + ROW * len(SATIRLAR) + 10), etiket, font=font(18), fill="#898781")

    for i, (g, ad, alt, lo, hi, disari) in enumerate(SATIRLAR):
        y = TOP + i * ROW
        renk = GRUPLAR[g][1]
        d.text((32, y + 6), ad, font=font(23, True), fill="#0b0b0b")
        d.text((32, y + 38), alt, font=font(18), fill="#52514e")
        cy = y + 30
        x0, x1 = x(lo), x(hi)
        if disari:
            x0 = x(XMAX) - 70
            x1 = x(XMAX)
        x1 = max(x1, x0 + 10)
        d.rounded_rectangle([x0, cy - 13, x1, cy + 13], radius=4, fill=renk)
        if disari:
            d.polygon([(x1 + 4, cy - 16), (x1 + 26, cy), (x1 + 4, cy + 16)], fill=renk)
            metin, mx = disari + " (ölçek dışı)", x1 + 36
        else:
            metin, mx = f"≈ {bin_tl(lo)}–{bin_tl(hi)} bin TL", x1 + 14
        d.text((mx, cy - 13), metin, font=font(21, True), fill="#0b0b0b")

    d.text((32, H - 62), "Kaynaklar ve varsayımlar: docs/HAZIR_ROBOTLAR.md. Yurt dışı fiyatlar 24.10.2026 mağaza sayfaları; "
           "gümrük sınıfı (oyuncak/elektronik) toplamı değiştirebilir.", font=font(18), fill="#898781")
    im.save(OUT, optimize=True)
    print("yazıldı:", OUT)


if __name__ == "__main__":
    main()
