#!/usr/bin/env python3
"""Writes manifest.json and the placeholder anim/idle.json for Tosbi (concept A)."""
import json, math, os, sys
PKG = sys.argv[1]
HM = 36 * math.sin(math.radians(80)) + 7
LEGS = ["fl", "fr", "rl", "rr"]
PSI0 = {"fl": -35.0, "fr": 215.0, "rl": 35.0, "rr": 145.0}
# hip yaw: + = leg swings forward (toward -Y). Left legs (+x) need -Z for that, right legs +Z.
HIP_AX = {"fl": [0, 0, -1], "fr": [0, 0, 1], "rl": [0, 0, -1], "rr": [0, 0, 1]}
HIP_LIM = {"fl": (-20, 14), "fr": (-20, 14), "rl": (-20, 20), "rr": (-20, 20)}

def knee_axis(leg):
    p = math.radians(PSI0[leg]); return [round(-math.sin(p), 6), round(math.cos(p), 6), 0]
def foot_axis(leg):
    p = math.radians(PSI0[leg]); return [round(math.cos(p), 6), round(math.sin(p), 6), 0]

joints = {}
for l in LEGS:
    lo, hi = HIP_LIM[l]
    joints[f"hip_{l}"] = {"node": f"leg_{l}", "axis": HIP_AX[l], "min": lo, "max": hi, "zero": 0, "servo": "MG90S",
                          "note": "kalça yaw; + = bacak öne. Ön bacaklarda +14° sınırı kafa çarpışmasından (concept check.py)"}
for l in LEGS:
    joints[f"knee_{l}"] = {"node": f"foot_{l}", "axis": knee_axis(l), "min": -90, "max": 90, "zero": 0, "servo": "MG90S",
                           "note": "ayak açısı, yüzgeç düzleminin altında; +80 = ayakta, 0 = yatay, -80 = ters dönmüş halde ayakta"}
joints["neck"] = {"node": "head", "axis": [-1, 0, 0], "min": -40, "max": 40, "zero": 0, "servo": "MG90S",
                  "note": "kafa pitch, kafanın kendi merkezi etrafında; + = yukarı bakar. Servo sapın üstünde sabit, kafa onun etrafında döner"}

M = {}
def pr(key, color, fil, axis, layer=0.16, **kw):
    M[key] = {"type": "print", "color": color, "filament": fil, "layer": layer, "layerAxis": axis, **kw}
pr("shell", "#9fd8c3", "PLA Mint (Elas / Porima pastel mint)", [0, 0, 1], 0.12,
   note="iki kubbe aynı STL, kubbe yukarı basılır (Z katman), 0.12 mm; dikiş izi arkada")
pr("egg", "#9fd8c3", "PLA Mint (Elas / Porima pastel mint)", [0, 0, 1], 0.12, note="kalça yumurtası, ekvatordan iki yarım, kutup aşağı basılır")
pr("arm", "#9fd8c3", "PLA Mint (Elas / Porima pastel mint)", [0, 0, 1], 0.16, note="kol üst/alt iki yarım, düz basılır, diz servosunu sıkıştırır")
for l in LEGS:
    pr(f"boot_{l}", "#9fd8c3", "PLA Mint (Elas / Porima pastel mint)", foot_axis(l), 0.16, note="ayak çizmesi + diz kapakları, ayakta (boyuna) basılır")
    M[f"toe_{l}"] = {"type": "tpu", "color": "#d64a3a", "filament": "TPU 95A Kırmızı", "layerAxis": knee_axis(l),
                     "note": "kapsül parmak dik basılır; mercan rengi TPU Türkiye'de nadir, kırmızı TPU gerçekçi seçim"}
pr("head", "#efe4cc", "PLA Krem / Fildişi", [0, 1, 0], 0.12, note="kafa ön/arka iki yarım, ayırma yüzeyi tablaya gelecek şekilde basılır (Y katman)")
pr("stalk", "#efe4cc", "PLA Krem / Fildişi", [0, 1, 0], 0.16, note="boyun sapı dik basılır")
pr("tail", "#efe4cc", "PLA Krem / Fildişi", [0, 0, 1], 0.16, note="kuyruk (USB-C yuvası) yan yatık basılır")
pr("bezel", "#f2846b", "PLA Mercan / Somon", [0, 1, 0], 0.16, note="vizör çevresindeki mercan halka, düz basılır")
pr("badge", "#f2846b", "PLA Mercan / Somon", [0, 0, 1], 0.16, note="'beni sev' altıgen dokunma plakası, arkasında bakır bant")
pr("lip", "#26272b", "PLA Siyah", [0, 0, 1], 0.16, note="iki kubbe arasındaki şasi bandı, kubbelerdeki ToF ışık tünelleri, çene yarığı (kozmetik 'ağız'), boyun yuvası astarı")
pr("mask", "#141414", "Mat siyah boya (iç maske)", [0, 1, 0], 0.16, roughness=0.9)
M["visor"] = {"type": "petg", "color": "#141518", "filament": "PETG Siyah",
              "layerAxis": [0, 1, 0], "note": "Kubbeli vizör yüzü yukarı basılır. Eğri yüzey ütülenemez: yarı parlak olur ve kontur halkaları görünür; tam parlaklık için zımpara + şeffaf vernik gerekir"}
M["window"] = {"type": "acrylic", "color": "#0b0c0e", "opacity": 0.4, "note": "2 mm açık füme akrilik disk Ø34 (~%60 geçirgen), lazer kesim, vizör deliğine pres geçme"}
M["lcd_glass"] = {"type": "glass", "color": "#07080a", "roughness": 0.08, "note": "GC9A01 modülün Ø35.5 ön camı; aktif alan dışındaki siyah halka"}
M["screen_face"] = {"type": "screen", "screen": "face"}
M["screw"] = {"type": "metal", "color": "#4a4c52", "roughness": 0.42, "note": "M2 siyah oksit çelik: ISO 7380 yuvarlak başlı (kalça/diz/kubbe/kafa); yatak pimi yerine M2x15 vida (Türkiye stoğunda M2 omuz cıvatası bulunamadı; dişli gövde PLA yatakta zamanla aşınır/boşluk yapar)"}
M["metal"] = {"type": "metal", "color": "#b4b8be", "roughness": 0.3, "note": "USB-C dişi soket (kuyrukta)"}
M["internal_servo"] = {"type": "internal", "color": "#2f56b0"}
M["internal_pcb"] = {"type": "internal", "color": "#1f7a4a"}
M["internal_chip"] = {"type": "internal", "color": "#222326"}
M["internal_cell"] = {"type": "internal", "color": "#d6402b"}
M["speaker"] = {"type": "rubber", "color": "#1d1e21", "note": "29 mm hoparlör, ızgara deliklerinden görünür"}
M["internal_wire"] = {"type": "internal", "color": "#e0a030"}
M["internal_chassis"] = {"type": "internal", "color": "#c9c5bd"}
M["internal_cap"] = {"type": "internal", "color": "#3a4fa8"}
M["switch"] = {"type": "plastic", "color": "#141416", "roughness": 0.35,
               "note": "KCD1 mini rocker anahtar (siyah, 21x15 çerçeve), sağ yanda kubbe ek yerinde: iki yüzde de aynı yerde durur"}

faces = ["neutral", "blink", "happy", "talk_a", "talk_b", "surprised", "sleepy", "sad", "determined"]
pose_rest = {**{f"hip_{l}": 0 for l in LEGS}, **{f"knee_{l}": 80 for l in LEGS}, "neck": 15}

LINKS = os.path.join(PKG, "sim", "links.json")
MASS_G = round(json.load(open(LINKS))["total_g"]) if os.path.exists(LINKS) else 380
man = {
 "key": "A", "name": "Tosbi", "subtitle_tr": "İki yüzlü kaplumbağa",
 "tagline_tr": "Ters dönse de yürür: iki kabuğu aynı, sırtüstü düşünce diğer yüzüyle yürümeye devam eder.",
 "accent": "#f2846b",
 "glb": "model.glb",
 "frame_note": "body link origin = zemin, gövde merkezinin altı (dinlenme pozunda). Orta düzlem z = %.2f mm. base = bu çerçevenin dünya pozu; ayakta [0,0,0,1,0,0,0]." % HM,
 "joints": joints,
 "materials": M,
 "screens": {"face": {"res": [240, 240], "round": True, "uvAxes": ["x", "z"], "panel": "GC9A01 1.28in IPS 240x240 (SPI, RGB565)",
                      "active_diam_mm": 32.4, "glass_diam_mm": 35.5, "brightness": 1.25,
                      "behind": "Ø34 delikli PETG vizör + 2 mm açık füme akrilik (~%60 geçirgen), ekran camı akriliğin 2.2 mm arkasında"}},
 "faces": {**{f: {"face": f"faces/{f}.png"} for f in faces}, **{f + "_inv": {"face": f"faces/{f}_inv.png"} for f in faces}},
 "faces_note": "*_inv = aynı ifade 180° döndürülmüş; robot ters (diğer kabuğunun üstünde) dururken firmware ekranı döndürür. Ters pozdaki animasyonlar *_inv kullanmalı.",
 "animations": {"idle": "anim/idle.json"},
 "pose_rest": pose_rest,
 "specs": {"dims_mm": [154, 156, 72], "mass_g": MASS_G, "mass_note": "BOM parçalarıyla (GY-521, 39x18 şarj, PAM8403+pot, 2 x GY-53, KCD1, delikli pertinaks, kondansatörler, JST kablolar, somunlar); hedef 350 g aşılıyor", "servos": 9, "motors": 0,
           "brain": "ESP32-S3 SuperMini (Wi-Fi, kafada) + PCA9685 (I2C servo sürücü, gövdede)",
           "battery": "2S 14500 Li-ion (2 hücre, ~6 Wh), 2S BMS, USB-C 2S şarj (kuyrukta), KCD1 güç anahtarı (sağ yan)",
           "battery_note": "Satın alınabilen Orion 14500 hücreler 3C (~2.7 A); konseptin istediği ≥4 A değil. Takla sırasında 4 diz servosu aynı anda stall'a yakın akım çeker: gerilim çökmesi / ESP32 resetlenme riski (simülasyonda modellenmedi).",
           "runtime_walk_min": 35, "runtime_idle_h": 2.5, "walk_speed_cm_s": None,
           "self_righting": "Gerekmez: iki kabuk özdeş. Sırtüstü düşünce dizler ~160° düzlemden geçip diğer yüzde ayağa kalkar (4 bacak itişi stall'ın %39'u). Yan ve burun üstü düşüş henüz simüle edilmedi.",
           "sensors": ["MPU6050 GY-521 IMU (ters dönme / düşme)",
                       "2 x VL53L0X ToF (GY-53 modül), her kubbenin önünde boynun altında/üstünde birer pencere: hangi yüz alttaysa onun sensörü masa kenarına bakar (A ve B yüzünde de kenar algısı var)",
                       "ESP32-S3 dokunma pinleri + bakır bant (2 kabuk plakası, kafa üstü)"],
           "sensors_note": "Konseptteki çene ToF'u B yüzünde yukarı bakıyordu ve GY-53 kartı (25x15.6) çeneye sığmıyor (src/fit_report.json). Çene yarığı artık kozmetik.",
           "screen": "GC9A01 1.28\" yuvarlak IPS 240x240, aktif Ø32.4 mm",
           "voice": "PAM8403 + 29 mm hoparlör (cıvıltı / telefon veya PC üzerinden ses)"},
 "realism_notes_tr": [
   "Kabuk, yumurtalar, kollar ve ayaklar FDM PLA: yakından 0.12–0.16 mm katman çizgileri görünür; kubbelerin tepesinde kontur basamakları oluşur.",
   "Parçalar arasında gerçek ayrım çizgileri var: iki kubbe arasında siyah şasi bandı, yumurtaların ekvatoru, kolların üst/alt yarısı, kafanın ön/arka yarısı, diz kapaklarındaki 0.4 mm boşluk.",
   "Görünen vidalar gerçek yerlerinde: her kalça yumurtasının üstünde horn vidası ve altında M2x15 vida (omuz cıvatası bulunamadı), her dizde iki vida, her kubbede 2, kafanın arkasında 2 adet M2.",
   "Yüz tek bir yuvarlak GC9A01 ekran: 240x240 piksel, aktif alan Ø32.4 mm. Oval vizörün tamamı ekran değil; ekran vizördeki yuvarlak deliğin arkasında, füme akrilikten görünür. Yakından pikseller seçilir.",
   "Açık füme akrilik ekranı yaklaşık %40 karartır ve üzerinde yansıma oluşur; ekranın Ø35.5 camının siyah kenar halkası akriliğin arkasında hafifçe seçilir.",
   "Vizör parlak siyah PETG'den basılır ama kubbeli olduğu için ütülenemez: yarı parlak görünür, kontur halkaları seçilir. Ayna gibi parlaklık için zımpara ve vernik gerekir.",
   "Renkler hazır filamentlerden: PLA Mint, PLA Krem, PLA Mercan, PLA Siyah, PETG Siyah, TPU 95A Kırmızı. Mercan renkli TPU bulmak zor, bu yüzden parmaklar kırmızı. Her renk ayrı parça; çok renkli (AMS) yazıcı gerekmez.",
   "Konsept görsellerindeki daha doygun yeşil yerine gerçek pastel mint filament rengi kullanıldı.",
   "Gözlerdeki yumuşak parıltı, ESP32'nin LVGL ile çizebileceği kadar: ekran RGB565 renk derinliğinde, renk geçişlerinde hafif bantlanma olur.",
   "Servolar, kablolar ve kartlar dışarıdan görünmez. Boyundaki 6 telli kablo sapın içinden geçer, kafada boyun servosunun yanından arka duvar boyunca SuperMini'ye çıkar (±40° boyunca servoya değmez).",
   "Sağ yanda, iki kubbenin birleştiği yerde siyah KCD1 güç anahtarı görünür; kesiği yarı yarıya iki kubbede.",
   "Her kubbenin önünde, boynun hemen altında/üstünde küçük siyah bir ToF penceresi var (kubbeler hâlâ aynı STL)."
 ]
}
# MuJoCo results (sim/make_results.py) override animations / speed / self-righting and add sim_summary
SIMRES = os.path.join(PKG, "sim", "results.json")
if os.path.exists(SIMRES):
    sr = json.load(open(SIMRES))
    man["animations"] = sr["animations"]
    man["specs"].update(sr["specs"])
    man["sim_summary"] = sr["sim_summary"]
FR = os.path.join(PKG, "anim", "fall_recover.json")
if os.path.exists(FR):
    fr = json.load(open(FR))
    man["animation_captions_tr"] = {"fall_recover": {"caption": fr.get("caption_tr"), "events": fr.get("events", [])}}
man["stills_notes_tr"] = {
    "action_wave": "happy klibinden (MuJoCo) alınmış kare: arka kalçalar öne alınmış, ağırlık 3 ayağın üstünde; robot bu pozda gerçekten durabiliyor.",
    "lim_knee": "eklem yönü testi, dengede değil (dizler farklı uç açılarda; robot bu pozda duramaz)",
    "lim_hip_fwd": "kalça ileri sınırları (ön +14°, arka +20°), eklem testi",
    "lim_hip_back": "kalça geri sınırları (−20°), eklem testi",
    "lim_neck_up": "boyun +40° (yukarı sınır)", "lim_neck_down": "boyun −40° (aşağı sınır)",
    "xray / xray_side": "BOM'daki gerçek kart ölçüleriyle iç yerleşim (src/fit_report.json: 0 çakışma)",
    "macro_switch": "sağ yandaki KCD1 güç anahtarı, kubbe ek yerinde",
    "macro_tof": "kubbelerin önündeki ToF pencereleri (alttaki A yüzü için, üstteki B yüzü için)"}
json.dump(man, open(os.path.join(PKG, "manifest.json"), "w"), indent=1, ensure_ascii=False)

# placeholder idle: 2 s breathing loop (knees +-2.5 deg, neck +-3 deg), base compensates so the toes stay on the floor
fps, n = 30, 61
J = {k: [] for k in pose_rest}; base = []
for i in range(n):
    ph = 2 * math.pi * i / (n - 1)
    kb = 80 + 2.5 * math.sin(ph)
    for l in LEGS:
        J[f"hip_{l}"].append(0.0); J[f"knee_{l}"].append(round(kb, 3))
    J["neck"].append(round(15 + 3 * math.sin(ph - 0.8), 3))
    dz = 36 * (math.sin(math.radians(kb)) - math.sin(math.radians(80)))
    base.append([0.0, 0.0, round(dz, 4), 1.0, 0.0, 0.0, 0.0])
anim = {"fps": fps, "loop": True, "frames": n, "joints": J, "base": base,
        "face": [[0, "neutral"], [40, "blink"], [44, "neutral"]],
        "source": "placeholder: kinematic 2 s breathing loop for posecheck (not simulated)", "metrics": {}}
os.makedirs(os.path.join(PKG, "anim"), exist_ok=True)
IDLE = os.path.join(PKG, "anim", "idle.json")
if not os.path.exists(IDLE) or json.load(open(IDLE)).get("source", "").startswith("placeholder"):
    json.dump(anim, open(IDLE, "w"))      # never overwrite the MuJoCo idle clip from sim/clips.py
print("ok HM", HM)
