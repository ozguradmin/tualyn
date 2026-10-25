#!/usr/bin/env python3
"""Write manifest.json and the placeholder anim/idle.json for package C (Findik).
Keeps fields that later phases add (animations, specs/sim_summary updates) if manifest.json exists."""
import json, math, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
ri = json.load(open(os.path.join(HERE, "rig_info.json")))
n = [round(v, 3) for v in ri["split_plane_normal"]]
EAR = [0, round(math.cos(math.radians(10)), 3), round(-math.sin(math.radians(10)), 3)]

CREAM = "#ECE3D0"      # matte ivory/cream PLA as it photographs (warm off-white, not #FFF)
CARAMEL = "#745034"    # RENDER albedo for Bambu Lab PLA Matte "Caramel" (catalogue swatch #AE835B); darker because the viewer lighting lifts it
CARAMEL_SWATCH = "#AE835B"

mat = {
 "cream":     {"type": "print", "color": CREAM, "filament": "PLA Mat Fildişi/Krem (ör. Bambu Lab PLA Matte Ivory White veya Elas PLA Krem)", "layer": 0.12, "layerAxis": n,
               "part": "alt gövde (yüz halkası, karın, omuz yuvaları); ayırma yüzü tablada, kubbe yukarı basılır -> katmanlar ayırma düzlemine paralel (~23° eğik)"},
 "cap":       {"type": "print", "color": CARAMEL, "filament": "Bambu Lab PLA Matte Caramel", "layer": 0.12, "layerAxis": n,
               "part": "karamel kapak; ayırma yüzü tablada, destek yok; 4 çift Ø6x1.5 mm N35 mıknatısla tutulur"},
 "ear":       {"type": "print", "color": CARAMEL, "filament": "Bambu Lab PLA Matte Caramel", "layer": 0.12, "layerAxis": EAR, "part": "kulak kabuğu x2, düz basılır, kapağa pimle yapıştırılır"},
 "ear_inner": {"type": "print", "color": CREAM, "filament": "PLA Mat Fildişi/Krem", "layer": 0.12, "layerAxis": EAR, "part": "kulak içi krem parça x2, yapıştırılır"},
 "visor":     {"type": "petg", "color": "#141518", "filament": "PETG Siyah, dış yüz yukarı basılır; parlaklık için zımpara (400->1500) + 2K şeffaf vernik (kavisli yüzeyde ütüleme işe yaramaz)", "layer": 0.12, "layerAxis": [0, 1, 0]},
 "nose":      {"type": "petg", "color": "#141518", "filament": "PETG Siyah (vizörle aynı işlem)", "layer": 0.12, "layerAxis": [0, 1, 0]},
 "arm":       {"type": "print", "color": CARAMEL, "filament": "Bambu Lab PLA Matte Caramel, %50 gyroid", "layer": 0.16, "layerAxis": [1, 0, 0], "part": "kol + çizme tek parça, göbek yüzü tablada (destek yok)"},
 "hubcap":    {"type": "print", "color": CARAMEL, "filament": "Bambu Lab PLA Matte Caramel", "layer": 0.16, "layerAxis": [1, 0, 0], "part": "tekerlek kapağı, aks vidasını gizler"},
 "hub":       {"type": "print", "color": CREAM, "filament": "PLA Mat Fildişi/Krem", "layer": 0.16, "layerAxis": [1, 0, 0]},
 "beans":     {"type": "print", "color": CREAM, "filament": "PLA Mat Fildişi/Krem (4 minik parça yapıştırılır; tek renk baskıda kabartma olur)", "layer": 0.12, "layerAxis": [1, 0, 0]},
 "tyre":      {"type": "tpu", "color": "#202124", "filament": "TPU 95A Siyah", "layerAxis": [1, 0, 0]},
 "screen_eyeL": {"type": "screen", "screen": "eyeL"},
 "screen_eyeR": {"type": "screen", "screen": "eyeR"},
 "lcd_glass": {"type": "glass", "color": "#0b0c0e", "roughness": 0.04, "note": "GC9A01 modülünün ön camı: Ø35.6 cam, Ø32.4 aktif alanın etrafında ~1.6 mm siyah maske halkası"},
 "screw":     {"type": "metal", "color": "#a6aab0", "roughness": 0.38, "note": "M2 çinko kaplı vida: 4 x MG90S korna vidası (kol dış yüzünde havşada), 2 x karın altı havşa başlı"},
 "usb_metal": {"type": "metal", "color": "#c4c7cc", "roughness": 0.3, "note": "2S USB-C şarj modülünün soketi, arkada altta"},
 "usb_tongue": {"type": "plastic", "color": "#151516", "roughness": 0.6},
 "tcrt_body": {"type": "plastic", "color": "#151517", "roughness": 0.6, "note": "TCRT5000 gövdesi, çene yarıklarından görünür"},
 "tcrt_emitter": {"type": "plastic", "color": "#2a3a6e", "roughness": 0.12, "note": "IR verici lens (mavimsi şeffaf)"},
 "tcrt_detector": {"type": "plastic", "color": "#0c0c0e", "roughness": 0.1, "note": "IR alıcı lens (siyah)"},
 "speaker_cloth": {"type": "plastic", "color": "#19191b", "roughness": 0.95, "note": "ızgara arkasında siyah hoparlör kumaşı"},
 "wire_red":  {"type": "plastic", "color": "#b8322a", "roughness": 0.45, "note": "N20 motor kablosu, 28 AWG silikon"},
 "wire_black": {"type": "plastic", "color": "#1c1c1e", "roughness": 0.45},
 # internals (x-ray only)
 "internal_servo":   {"type": "internal", "color": "#3b82f6", "label": "4 x MG90S"},
 "internal_horn":    {"type": "internal", "color": "#f1f1ee", "label": "servo kornası (kolun içine gömülü)"},
 "internal_motor":   {"type": "internal", "color": "#c3c7cc", "label": "2 x N20 6V 100rpm"},
 "internal_shaft":   {"type": "internal", "color": "#8d939a", "label": "aks (ön: M3x12 cıvata + baskı PETG burç, arka: N20 D-mil)"},
 "internal_battery": {"type": "internal", "color": "#4caf7a", "label": "2 x 14500 900 mAh (2S), baskı yuvada, tutucudan sökülmüş yay/plaka kontaklar"},
 "internal_pcb":     {"type": "internal", "color": "#1f7a3a", "label": "BMS, 2 x MP1584, MAX98357A, INMP441, BMI160, şarj"},
 "internal_pcb_esp": {"type": "internal", "color": "#22262c", "label": "ESP32-S3 N16R8 devkit"},
 "internal_module":  {"type": "internal", "color": "#b8bdc3", "label": "ESP32-S3-WROOM-1 metal kılıf"},
 "internal_metal":   {"type": "internal", "color": "#c4c7cc"},
 "internal_pcb_blue": {"type": "internal", "color": "#1f4fa8", "label": "GC9A01 ve TCRT5000 kartları"},
 "internal_pcb_red": {"type": "internal", "color": "#7a2d8f", "label": "DRV8833"},
 "internal_lcd":     {"type": "internal", "color": "#0e1014"},
 "internal_speaker": {"type": "internal", "color": "#5b5f66", "label": "32 mm hoparlör"},
 "internal_chassis": {"type": "internal", "color": "#d6d1c7", "label": "iç şasi (servo yuvaları, pil tepsisi, güverte)"},
 "internal_led":     {"type": "internal", "color": "#f4f4f4", "label": "2 x WS2812B yanak"},
 "internal_magnet":  {"type": "internal", "color": "#9aa0a6", "label": "kapak mıknatısları Ø6x1.5 (kapakta 4 + gövdede 4)"},
}
screens = {s: {"res": [240, 240], "round": True, "uvAxes": ["x", "z"], "panel": "GC9A01 1.28in IPS 240x240 (SPI, RGB565)",
               "active_diam_mm": 32.4, "glass_diam_mm": 35.6, "brightness": 1.15,
               "note": ("robotun SOL gözü (+X), önden bakınca sağda" if s == "eyeL" else "robotun SAĞ gözü (-X), önden bakınca solda")}
           for s in ("eyeL", "eyeR")}
EXPRS = ["neutral", "blink", "happy", "talk_a", "talk_b", "surprised", "sleepy", "sad", "determined", "curious"]
faces = {e: {"eyeL": f"faces/{e}_L.png", "eyeR": f"faces/{e}_R.png"} for e in EXPRS}
joints = {}
for k in ("fl", "fr", "rl", "rr"):
    front = k[0] == "f"
    joints["hip_" + k] = {"node": "leg_" + k, "axis": [-1, 0, 0] if front else [1, 0, 0],
                          "min": 5 if front else 5, "max": 82 if front else 118, "zero": 0, "servo": "MG90S",
                          "note": ("0 = kol dik aşağı; + = teker ileri gider; ayakta 22°. Alt sınır +5°: kol +4°'nin altında gövdeye sürtünür (0°'de 0.6 mm, −5°'de 1.6 mm girer; sim/check_arm_shell.py)" if front else "0 = kol dik aşağı; + = teker geri gider; ayakta 22°. Alt sınır +5° (N20 çizme kovanı +3°'nin altında karına girer: 0°'de 0.7 mm, −12°'de 4 mm), üst sınır 118° (120°'de kapağa 0.1 mm, 122°'de 0.7 mm sürtünür)"),
                          "coupled_limit": "sınırlar kol+çizme gövdeye girmeyecek şekilde (sim/check_arm_shell.py) seçildi; bu aralıkta ön ve arka teker birbirine değmez (sin(ön)+sin(arka) > 0)"}
for k in ("fl", "fr", "rl", "rr"):
    front = k[0] == "f"
    joints["wheel_" + k] = {"node": "wheel_" + k, "axis": [1, 0, 0], "continuous": True,
                            "motor": "yok - serbest teker (M3x12 cıvata kolu sıkar, teker baskı PETG burç üstünde döner)" if front else "N20 6V 100rpm, DRV8833",
                            "note": "+ = ileri (-Y) yuvarlanma"}
pose_rest = {f"hip_{k}": 22 for k in ("fl", "fr", "rl", "rr")}
pose_rest.update({f"wheel_{k}": 0 for k in ("fl", "fr", "rl", "rr")})

old = {}
mp = os.path.join(PKG, "manifest.json")
if os.path.exists(mp):
    old = json.load(open(mp))
man = {
 "key": "C", "name": "Fındık", "subtitle_tr": "Teker patili hacıyatmaz hamster",
 "tagline_tr": "Avuç içi kadar bir hamster: dört teker-patiyle masada koşturur, el sallar, eğilir; yan yattığında hacıyatmaz gibi kendini toparlar.",
 "accent": CARAMEL, "glb": "model.glb", "creaseDeg": 40,
 "joints": joints, "materials": mat, "screens": screens, "faces": faces,
 "animations": old.get("animations", {"idle": "anim/idle.json"}),
 "pose_rest": pose_rest,
 "specs": old.get("specs", {
   "dims_mm": [96.0, 92.5, 117.0], "dims_note": "G x U x Y, ayakta (22°), kulaklar dahil", "mass_g": 301, "mass_note": "CAD hacim x PLA yoğunluğu + gerçek parça kütleleri (konsept tahmini)",
   "servos": 4, "motors": 2, "actuators_note": "4 x MG90S kalça (bacak başına 1 serbestlik) + 2 x N20 arka tekerde; ön tekerler serbest",
   "brain": "ESP32-S3 N16R8 DevKitC-1 (16 MB flash, 8 MB PSRAM, Wi-Fi -> Claude API, telefon/PC proxy üzerinden)",
   "battery": "2S 14500 900 mAh Li-ion (7.4 V, 6.7 Wh) + 2S BMS + USB-C 2S şarj", "runtime_walk_min": 60, "runtime_idle_h": 4.6,
   "walk_speed_cm_s": 16, "walk_speed_note": "tekerle yuvarlanır; 6 V'ta 100 rpm x Ø30 = 16 cm/s (hesap; sim sonucu Motion fazında)",
   "self_righting": "Yan düşüşte: alt taraftaki bacakları dışarı süpürüp yuvarlak karın üzerinde doğrulur (yarı-statik analizle doğrulandı). Yüzüstü/sırtüstü düşüşte kalkamaz; yardım ister.",
   "sensors": ["BMI160 IMU", "2 x TCRT5000 çene uçurum sensörü", "2 x TTP223 dokunma (kafa, sırt)", "INMP441 mikrofon"],
   "voice": "MAX98357A + 32 mm hoparlör (cıvıltı/TTS); ses tanıma telefon veya PC sunucusu üzerinden",
   "screens": "2 x GC9A01 1.28\" yuvarlak IPS 240x240"}),
 "sim_summary": old.get("sim_summary", {"status": "pending (Motion phase)"}),
 "realism_notes_tr": [
   "Renk: karamel parçalar Bambu Lab PLA Matte Caramel ile basılırsa gerçekte konsept görselindeki parlak altın-turuncudan daha kahverengi, sütlü kahve tonunda olur. Gövde mat fildişi/krem PLA; saf beyaz değil.",
   "Katman çizgileri: gövde ve kapak ayırma yüzü tablaya gelecek şekilde basılır; katmanlar yatayla ~23° eğiktir ve 0.12 mm'de yakından (30 cm altı) seçilir. Kollar ve tekerlek parçaları yan yatık basıldığı için çizgiler yanal yüzlere paraleldir.",
   "Ek yerleri: kapak-gövde arasında 0.9 mm ayrım oluğu, vizörün çevresinde ~0.45 mm boşluk, kulaklarda yapıştırma çizgisi; tekerlekte göbek, TPU lastik ve kapak ayrı parçalardır.",
   "Gözler: her biri 240x240 piksel GC9A01, Ø32.4 mm aktif alan (~7.4 piksel/mm). Kol mesafesinden pikseller seçilmez, 10 cm'den yakında ızgara görünür. Panel 16-bit RGB565 aldığı için iris gradyanında hafif bantlaşma olur. IPS siyahı tam siyah değildir: karanlıkta yuvarlak panel hafifçe gri parlar.",
   "Siyah arka plan ekranı tamamen yok etmez: aydınlık odada aktif alan, cam yansıması ve IPS arka ışık sızması yüzünden parlak siyah vizörden biraz daha açık, koyu gri bir daire olarak seçilir (konseptteki 'panel vizörde kaybolur' iddiası iyimserdir).",
   "Ekran camı vizör yüzeyinin ~4.4 mm altında: gözler hafif çukurda durur, yandan bakınca vizör kenarı gözün bir kısmını kapatır ve camın siyah kenar halkası (Ø32.4 -> Ø35.6) ince bir çizgi olarak görünür.",
   "Parlak siyah vizör: FDM PETG kendiliğinden bu kadar parlak olmaz ve kavisli yüzeyde ütüleme işe yaramaz. Zımpara + 2K vernik gerekir (ya da reçine baskı, ~+150 TL). İşlem yapılmazsa yarı mat ve katman basamaklı görünür.",
   "Görünen vidalar: her kalçada kol dış yüzünde M2 servo korna vidası (havşa içinde), karın altında 2 adet M2 havşa vida. Kapak mıknatıslıdır, vidası yoktur.",
   "Kablolar: arka N20 motor kabloları kolun iç yüzündeki kanaldan kalçaya gider; kalçada yay şeklinde bir geçiş yarığı ve servis halkası gerekir. Konseptte bu güzergah çizilmemişti, burada kanal olarak modellendi.",
   "Çene sensörleri: TCRT5000'in iki lensi (mavimsi verici, siyah alıcı) 11x6 mm yarıklardan görünür. Konseptteki 6.6 mm pencere sensörü sığdırmıyordu; yarık büyütüldü.",
   "USB-C şarj soketi arkada, altta metal olarak görünür. Hoparlör ızgarasının arkasında siyah kumaş görünür.",
   "Yanak LED'leri (WS2812B) 0.8 mm krem PLA'nın arkasındadır: kapalıyken görünmez, yanınca pembe ve bulanık bir leke olarak sızar (bu modelde yalnız x-ray'de görünür).",
   "Patilerdeki toe-bean'ler 4 minik krem parçanın yapıştırılmasıyla olur; tek renk baskıda yalnızca kabartma olarak kalır.",
 ],
}
json.dump(man, open(mp, "w"), indent=1, ensure_ascii=False)

# ---------------- placeholder idle: 2 s breathing loop, kinematically consistent with wheels on the floor
fps, T = 30, 2.0
F = int(fps * T) + 1
HIP_H_W = ri["frames"]["leg_fl"][2]          # hip axis height above the floor in the rest pose
L, R = 34.0, 15.0
th = [22 + 3.0 * math.sin(2 * math.pi * i / (F - 1)) for i in range(F)]
base, wf, wr = [], [], []
for t_ in th:
    a = math.radians(t_)
    bz = R - (HIP_H_W - 0.0) + L * math.cos(a) + 0.0
    bz = (R - HIP_H_W + L * math.cos(a))
    by = L * (math.sin(math.radians(22)) - math.sin(a))      # rear wheels held by the N20 gearboxes
    base.append([0.0, round(by, 4), round(bz, 4), 1.0, 0.0, 0.0, 0.0])
    # rear wheel: world rotation = hip + wheel, axle fixed -> wheel = -(hip - 22)
    wr.append(round(-(t_ - 22), 4))
    # front wheel rolls: axle world y = by - 15.5 - L sin a ; world rot = -hip + wheel ; dy = -R * d(rot)
    ay = by - 15.5 - L * math.sin(a)
    ay0 = -15.5 - L * math.sin(math.radians(22))
    wf.append(round((t_ - 22) - math.degrees((ay - ay0) / R), 4))
anim = {"fps": fps, "loop": True, "frames": F,
        "joints": {"hip_fl": th, "hip_fr": th, "hip_rl": th, "hip_rr": th,
                   "wheel_fl": wf, "wheel_fr": wf, "wheel_rl": wr, "wheel_rr": wr},
        "base": base, "face": [[0, "neutral"], [38, "blink"], [42, "neutral"]],
        "source": "PLACEHOLDER (rig phase): kinematic 2 s breathing loop, hips 22±3°, base z/y solved so all tyres stay on the floor with the rear N20s holding; to be replaced by the Motion phase",
        "metrics": {}}
os.makedirs(os.path.join(PKG, "anim"), exist_ok=True)
json.dump(anim, open(os.path.join(PKG, "anim", "idle.json"), "w"))
print("manifest + idle written; layer axis body/cap", n)
