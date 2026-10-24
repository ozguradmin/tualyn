#!/usr/bin/env python3
"""Kıpır v1 bağlantı şemasını (docs/baglanti.svg) üretir.  python3 baglanti_ciz.py"""
import os

W, H = 1180, 820
out = []
add = out.append
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Helvetica, Arial, sans-serif">')
add('''<style>
 .blok{fill:#f6f8fb;stroke:#1d2733;stroke-width:2;rx:10}
 .baslik{font-size:17px;font-weight:700;fill:#1d2733}
 .pin{font-size:13px;fill:#1d2733}
 .not{font-size:12.5px;fill:#516070}
 .w{fill:none;stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round}
 .g{stroke:#1d2733}.p5{stroke:#d7263d}.p3{stroke:#f08a24}.pm{stroke:#8b1e3f}
 .s1{stroke:#1b7f79}.s2{stroke:#3a6ea5}.s3{stroke:#7a4fb3}.s4{stroke:#2e8b3a}
 .dot{fill:#1d2733}
</style>''')
add(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
add('<text x="24" y="38" font-size="24" font-weight="700" fill="#1d2733">Kıpır v1: bağlantı şeması</text>')
add('<text x="24" y="62" class="not">Tüm GND\'ler ortak. Kırmızı: 5V (powerbank), turuncu: 3V3, bordo: motor pili (2x18650, 7.4V). Pin numaraları config.h ile aynı.</text>')

def blok(x, y, w, h, ad):
    add(f'<rect class="blok" x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>')
    add(f'<text class="baslik" x="{x+12}" y="{y+24}">{ad}</text>')

def pinler(x, y, adlar, sag=False, adim=22):
    pos = {}
    for i, a in enumerate(adlar):
        yy = y + i * adim
        if sag:
            add(f'<text class="pin" x="{x-10}" y="{yy+4}" text-anchor="end">{a}</text>')
        else:
            add(f'<text class="pin" x="{x+10}" y="{yy+4}">{a}</text>')
        add(f'<circle class="dot" cx="{x}" cy="{yy}" r="3.5"/>')
        pos[a] = (x, yy)
    return pos

def tel(pts, cls):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    add(f'<path class="w {cls}" d="{d}"/>')

# ESP32
blok(420, 110, 230, 520, "ESP32 DevKit V1")
esp_r = pinler(650, 160, ["GPIO25","GPIO26","GPIO27","GPIO13","GPIO33","GPIO32","GPIO14","GND"], sag=True)
esp_l = pinler(420, 160, ["VIN (5V)","3V3","GND","GPIO4","GPIO35","GPIO34","GPIO19","GPIO18","GPIO16"])
add('<text class="not" x="440" y="395">USB: powerbank\'ten 5V</text>')
add('<text class="not" x="440" y="413">(ESP32 ve tablet powerbank\'ten,</text>')
add('<text class="not" x="440" y="431">motorlar ayrı pilden beslenir)</text>')
add('<text class="not" x="440" y="470">İsteğe bağlı:</text>')
add('<text class="not" x="440" y="488">GPIO36 ← pil bölücü 100k/33k</text>')
add('<text class="not" x="440" y="506">GPIO23/22/21 ← Gamebox kolu</text>')
add('<text class="not" x="440" y="524">(LATCH / CLOCK / DATA)</text>')

# TB6612
blok(760, 110, 200, 300, "TB6612FNG")
tb_l = pinler(760, 160, ["PWMA","AIN1","AIN2","PWMB","BIN1","BIN2","STBY","GND","VCC"])
tb_r = pinler(960, 160, ["VM","GND ","AO1","AO2","BO1","BO2"], sag=True)
for a, b, c in [("GPIO25","PWMA","s1"),("GPIO26","AIN1","s1"),("GPIO27","AIN2","s1"),
                ("GPIO13","PWMB","s2"),("GPIO33","BIN1","s2"),("GPIO32","BIN2","s2"),("GPIO14","STBY","s3"),("GND","GND","g")]:
    (x1, y1), (x2, y2) = esp_r[a], tb_l[b]
    tel([(x1, y1), (705, y1), (705, y2), (x2, y2)], c)
# VCC <- 3V3
x2, y2 = tb_l["VCC"]
tel([esp_l["3V3"], (395, esp_l["3V3"][1]), (395, 92), (740, 92), (740, y2), (x2, y2)], "p3")

# Motors
blok(1010, 230, 150, 70, "Sol motor")
blok(1010, 320, 150, 70, "Sağ motor")
tel([tb_r["AO1"], (985, tb_r["AO1"][1]), (985, 255), (1010, 255)], "s1")
tel([tb_r["AO2"], (995, tb_r["AO2"][1]), (995, 275), (1010, 275)], "s1")
tel([tb_r["BO1"], (985, tb_r["BO1"][1]), (985, 345), (1010, 345)], "s2")
tel([tb_r["BO2"], (995, tb_r["BO2"][1]), (995, 365), (1010, 365)], "s2")
add('<text class="not" x="1012" y="410">Ters dönerse config.h:</text>')
add('<text class="not" x="1012" y="426">INVERT_LEFT / RIGHT = 1</text>')

# Battery
blok(780, 470, 230, 120, "Motor pili 2x18650")
add('<text class="not" x="792" y="518">anahtarlı yuva, 7.4V</text>')
add('<text class="not" x="792" y="538">+ ile − arasına 1000µF 16V</text>')
add('<text class="not" x="792" y="556">kondansatör (VM yanında)</text>')
add('<circle class="dot" cx="1010" cy="500" r="3.5"/><text class="pin" x="998" y="504" text-anchor="end">+</text>')
add('<circle class="dot" cx="1010" cy="570" r="3.5"/><text class="pin" x="998" y="574" text-anchor="end">−</text>')
tel([(1010, 500), (1040, 500), (1040, 430), (975, 430), (975, tb_r["VM"][1]), tb_r["VM"]], "pm")
tel([(1010, 570), (1060, 570), (1060, 440), (968, 440), (968, tb_r["GND "][1]), tb_r["GND "]], "g")

# Powerbank
blok(60, 650, 300, 100, "Powerbank (5V USB)")
add('<text class="not" x="72" y="700">USB kablo → ESP32 USB girişi</text>')
add('<text class="not" x="72" y="720">2. çıkış → tablet (yüz modunda)</text>')
tel([(360, 690), (535, 690), (535, 630)], "p5")
add('<text class="not" x="545" y="660">USB</text>')

# HC-SR04
blok(60, 90, 300, 150, "HC-SR04 mesafe")
hc = pinler(360, 135, ["VCC","TRIG","ECHO","GND"], sag=True, adim=24)
tel([hc["VCC"], (380, hc["VCC"][1]), (380, esp_l["VIN (5V)"][1]), esp_l["VIN (5V)"]], "p5")
tel([hc["TRIG"], (388, hc["TRIG"][1]), (388, esp_l["GPIO4"][1]), esp_l["GPIO4"]], "s4")
tel([hc["GND"], (372, hc["GND"][1]), (372, esp_l["GND"][1]), esp_l["GND"]], "g")
# echo divider
ex, ey = hc["ECHO"]
tel([(ex, ey), (300, ey), (300, 275)], "s4")
add('<rect x="288" y="275" width="24" height="34" fill="#fff" stroke="#2e8b3a" stroke-width="2"/><text class="not" x="318" y="297">1k</text>')
tel([(300, 309), (300, 330), (403, 330), (403, esp_l["GPIO35"][1]), esp_l["GPIO35"]], "s4")
add('<rect x="288" y="345" width="24" height="34" fill="#fff" stroke="#1d2733" stroke-width="2"/><text class="not" x="318" y="367">2k → GND</text>')
tel([(300, 330), (300, 345)], "g")
add('<text class="not" x="72" y="228">ECHO 5V verir: 1k/2k bölücü şart</text>')

# IR receiver
blok(60, 400, 230, 110, "IR alıcı VS1838B")
ir = pinler(290, 440, ["OUT","GND","VCC"], sag=True, adim=24)
tel([ir["OUT"], (330, ir["OUT"][1]), (330, esp_l["GPIO34"][1]), esp_l["GPIO34"]], "s3")
add('<text class="not" x="72" y="500">VCC → 3V3, GND → GND</text>')

# Ears and buzzer
blok(60, 530, 300, 100, "Kulak LED'leri + buzzer")
add('<text class="not" x="72" y="575">Sol kulak DIN ← GPIO19, sağ ← GPIO18</text>')
add('<text class="not" x="72" y="593">LED VDD: 5V bir 1N4148 diyot üzerinden</text>')
add('<text class="not" x="72" y="611">Pasif buzzer + ← 100Ω ← GPIO16</text>')
tel([(360, 570), (395, 570), (395, esp_l["GPIO19"][1]), esp_l["GPIO19"]], "s1")
tel([(360, 585), (405, 585), (405, esp_l["GPIO18"][1]), esp_l["GPIO18"]], "s2")
tel([(360, 605), (412, 605), (412, esp_l["GPIO16"][1]), esp_l["GPIO16"]], "s3")

add('<text class="not" x="24" y="800">Kodda değiştirebilirsin: robot/firmware/kipir_esp32/config.h  ·  Çizim: robot/docs/baglanti_ciz.py</text>')
add('</svg>')
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baglanti.svg")
open(p, "w", encoding="utf-8").write("\n".join(out))
print("yazıldı:", p)
