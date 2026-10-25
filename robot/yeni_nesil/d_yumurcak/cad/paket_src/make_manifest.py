#!/usr/bin/env python3
"""Write manifest.json + placeholder anim/idle.json for package D (Yumurcak).
Reads rig_info.json (from build_rig.py) and model.glb (for the sole geometry -> ground contact)."""
import json, math, os
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
info = json.load(open(os.path.join(HERE, "rig_info.json")))
NV = [round(v, 4) for v in info["NV"]]
LEGS = {"fr": (-1, -1), "fl": (1, -1), "br": (-1, 1), "bl": (1, 1)}     # (sx, sy)

# ---------------------------------------------------------------- joints
LIM = json.load(open(os.path.join(HERE, "limits.json"))) if os.path.exists(os.path.join(HERE, "limits.json")) else {}
joints = {"head": {"node": "head", "axis": NV, "min": -60, "max": 60, "zero": 0, "servo": "SG90 (9 g, plastik dişli)",
                   "note": "12° eğik eksen: +60° = sola bakış ~58° yaw + ~10° yan eğim + ~6° yukarı"}}
for k, (sx, sy) in LEGS.items():
    joints[f"yaw_{k}"] = {"node": f"haunch_{k}", "axis": [0, 0, -sx * sy], "min": LIM.get("yaw_min", -30), "max": LIM.get("yaw_max", 85),
                          "zero": 0, "servo": "MG90S", "note": "kalça topu kendi dikey ekseninde döner; + = diz yumrusu dışa (yana) döner. -22° altında yumru gövdeye girer; diz > 70° iken yaw ≤ 72° (komşu topa çarpar)"}
    joints[f"knee_{k}"] = {"node": f"paw_{k}", "axis": [0, -sx, 0], "min": LIM.get("knee_min", -5), "max": LIM.get("knee_max", 178),
                           "zero": 0, "servo": "MG90S", "note": "0 = pati dik aşağı, 30 = ayakta, 164 = tam katlanmış (yumurta modu); + = pati dışa/yukarı. Konseptteki 178° kabuğa 4 mm giriyor; 164° üstü yalnızca yaw ≥ +30° iken"}
pose_rest = {"head": 0}
for k in LEGS:
    pose_rest[f"yaw_{k}"] = 0
    pose_rest[f"knee_{k}"] = 30

# ---------------------------------------------------------------- materials
CREAM, ORANGE = "#efe6d4", "#f2881c"
mats = {
    "shell": {"type": "print", "color": CREAM, "filament": "Elas PLA Krem / Fildişi (mat)", "layer": 0.12, "layerAxis": NV,
              "note": "gövde kasesi ve kafa, eğik (12°) dikiş yüzeyi tablaya gelecek şekilde basılır; katmanlar eğik eksene dik"},
    "cap": {"type": "print", "color": ORANGE, "filament": "eSUN PLA+ Turuncu (Orange)", "layer": 0.12, "layerAxis": info["cap_layer_axis"],
            "note": "yumurta kabuğu şapka, kubbe yukarı basılır; 2 mıknatısla takılır"},
    "ball": {"type": "print", "color": ORANGE, "filament": "eSUN PLA+ Turuncu (Orange)", "layer": 0.16, "layerAxis": [0, 0, 1],
             "note": "kalça topu: ekvatordan iki yarım küre, ikisi de kubbe yukarı basılır"},
    "paw": {"type": "print", "color": ORANGE, "filament": "eSUN PLA+ Turuncu (Orange)", "layer": 0.16, "layerAxis": [0, 1, 0],
            "note": "pati yan yatırılarak basılır (katmanlar diz ekseni boyunca)"},
    "sole": {"type": "tpu", "color": "#202124", "filament": "TPU 95A Siyah", "layerAxis": [0, 0, 1], "note": "yapıştırılan taban"},
    "visor": {"type": "acrylic", "color": "#0d0e11", "opacity": 0.3,
              "note": "1 mm açık füme PETG levha (~%70 geçirgen; koyu görünüm arkadaki siyah göz cebinden gelir), basılı kalıp üzerinde vakumla şekillendirilir (parlaklık levhadan gelir). Yedek: 0.8 mm yarı saydam siyah PETG baskı (mat, katmanlı)"},
    "mask": {"type": "print", "color": "#131416", "filament": "PLA Mat Siyah", "layer": 0.16, "layerAxis": [0, 0, 1], "layerStrength": 0.2,
             "note": "vizör arkasındaki siyah göz cebi; ekran PCB kenarlarını gizler"},
    "lens": {"type": "acrylic", "color": "#050506", "opacity": 0.85, "note": "VL53L0X için IR geçiren siyah akrilik pencere (Ø6.8 mm)"},
    "screen_eyeL": {"type": "screen", "screen": "eyeL"},
    "screen_eyeR": {"type": "screen", "screen": "eyeR"},
    "screw": {"type": "metal", "color": "#a7abb1", "roughness": 0.4, "note": "M2 paslanmaz: 4 göbek altı havşa + 4 pati boynuz vidası"},
    "usb_metal": {"type": "metal", "color": "#c9ccd1", "roughness": 0.3, "note": "USB-C dişi soket (2S şarj kartı)"},
    "black": {"type": "plastic", "color": "#151517", "roughness": 0.55, "note": "USB-C dili, SS12D00 sürgü anahtar"},
    "internal_servo": {"type": "internal", "color": "#3b82f6"},
    "internal_horn": {"type": "internal", "color": "#f2f2f2"},
    "internal_battery": {"type": "internal", "color": "#2fa35a"},
    "internal_frame": {"type": "internal", "color": "#bdbdbd"},
    "internal_pcb": {"type": "internal", "color": "#1f7a4a"},
    "internal_pcb_disp": {"type": "internal", "color": "#2a5bd7"},
    "internal_lcd": {"type": "internal", "color": "#18191b"},
    "internal_magnet": {"type": "internal", "color": "#9aa0a6"},
}

screens = {s: {"res": [240, 240], "round": True, "panel": "GC9A01 1.28in IPS (Robotistan)", "active_diam_mm": 32.4,
               "glass_diam_mm": 35.5, "brightness": 1.6,
               "uv": "GLB'de gömülü: u = ekranın sağı (önden bakınca +X), v = yukarı",
               "behind": "1 mm füme PETG vizörün ~3-5 mm arkasında, siyah göz cebinin içinde"} for s in ("eyeL", "eyeR")}
screens["eyeL"]["side"] = "robotun SOL gözü (+X, önden bakınca sağda)"
screens["eyeR"]["side"] = "robotun SAĞ gözü (-X, önden bakınca solda)"

EXPR = ["neutral", "blink", "happy", "talk_a", "talk_b", "surprised", "sleepy", "asleep", "sad", "determined", "curious"]
faces = {e: {"eyeL": f"faces/{e}_L.png", "eyeR": f"faces/{e}_R.png"} for e in EXPR}

# ---------------------------------------------------------------- ground contact vs knee (for base z)
sc = trimesh.load(os.path.join(PKG, "model.glb"))
sole = None
for nm, g in sc.geometry.items():
    if nm.startswith("paw_fl__sole"):
        sole = g
paw_z0 = info["origins"]["paw_fl"][2]


def ground_dz(knee):
    R = trimesh.transformations.rotation_matrix(math.radians(knee), [0, -1, 0])[:3, :3]
    return paw_z0 + (sole.vertices @ R.T)[:, 2].min()


dz_rest = ground_dz(30)
dims = info.get("dims")

# ---------------------------------------------------------------- idle (2 s breathing placeholder)
F = 60
idle = {"fps": 30, "loop": True, "frames": F, "joints": {}, "base": [], "face": [[0, "neutral"], [38, "blink"], [42, "neutral"]],
        "source": "kinematic placeholder (2 s breathing loop) for posecheck; base z keeps the soles on the desk",
        "metrics": {}}
kn = [30 + 3.0 * (0.5 - 0.5 * math.cos(2 * math.pi * i / (F - 1))) for i in range(F)]
for k in LEGS:
    idle["joints"][f"knee_{k}"] = [round(v, 3) for v in kn]
    idle["joints"][f"yaw_{k}"] = [0.0] * F
idle["joints"]["head"] = [round(4.0 * math.sin(2 * math.pi * i / (F - 1)), 3) for i in range(F)]
for i in range(F):
    idle["base"].append([0.0, 0.0, round(-ground_dz(kn[i]), 4), 1.0, 0.0, 0.0, 0.0])
os.makedirs(os.path.join(PKG, "anim"), exist_ok=True)
json.dump(idle, open(os.path.join(PKG, "anim", "idle.json"), "w"))

man = {
    "key": "D", "name": "Yumurcak", "subtitle_tr": "Yürüyen yumurta", "accent": ORANGE,
    "tagline_tr": "Sallanır, düşer, kendi kalkar; sonra da kendinle gurur duyar.",
    "glb": "model.glb", "creaseDeg": 35,
    "joints": joints, "materials": mats, "screens": screens, "faces": faces,
    "animations": {"idle": "anim/idle.json"},
    "pose_rest": pose_rest,
    "frames_note": "mm, Z yukarı, robot -Y'ye bakar; body düğümü = yerde, yumurta merkezinin altında. Bacaklar: fl/fr/bl/br, robotun SOLU = +X.",
    "specs": {"dims_mm": dims or [107, 122, 146], "mass_g": 346, "servos": 9, "servo_detail": "8 × MG90S (kalça yaw + diz) + 1 × SG90 (eğik eksenli kafa)",
              "motors": 0, "brain": "ESP32-S3-Zero/Mini (4 MB flash, 2 MB PSRAM, Wi-Fi)", "screens": "2 × GC9A01 1.28\" yuvarlak 240×240 IPS",
              "battery": "2S 14500 IMR (2 hücre, ~5.8 Wh) + 2S BMS + 3 × MP1584", "runtime_walk_min": 25, "runtime_idle_h": 3.5,
              "walk_speed_cm_s": 4, "walk_speed_note": "tahmin (1.5 Hz tırıs, 27 mm adım); MuJoCo sonucu sim/ klasörüne gelecek",
              "self_righting": "Yumurta şekli + 4 pati itişi; yarı statik dışbükey-zarf modelinde 7/7 düşme yönü (MuJoCo doğrulaması ayrı)",
              "sensors": ["BMI160 IMU", "VL53L0X ToF uçurum sensörü (göbek penceresi)", "kapasitif dokunma (şapka içi + göbek, bakır bant)"],
              "voice": "Telefon/PC üzerinden (isteğe bağlı INMP441 + MAX98357A, +506 TL)", "charge": "Arkada USB-C (2S 4 A şarj kartı), yuva pozunda şarj"},
    "realism_notes_tr": [
        "Krem gövde ve kafa 0.12 mm katmanla, eğik dikiş yüzeyi tablada basılır: yakından bakınca katman çizgileri eğik eksene dik halkalar halinde görünür; kubbenin tepesinde 'basamaklanma' olur.",
        "Kafa ile gövde arasında 0.8 mm'lik eğik bir dikiş çizgisi her zaman görünür; kafa dönerken açılmaz çünkü dikiş yumurtanın küresel bölgesinde bir çemberdir. Arkasında gövdeden çıkan bir dudak var, içerisi görünmez.",
        "Vizör 1 mm füme PETG levhanın vakumla şekillendirilmesiyle yapılır, parlaklığı levhadan gelir (baskı değil). Kenarında kafa kabuğuyla arasında ~0.4 mm yapıştırma boşluğu görünür. Vakum düzeneği yoksa yedek: 0.8 mm yarı saydam siyah PETG baskı; o zaman vizör mat ve katmanlı olur, gözler daha bulanık parlar.",
        "Gözler gerçek GC9A01 panelleri: 240×240 piksel, 32.4 mm aktif daire, 35.5 mm cam. Yakından piksel ızgarası seçilir; aktif alanın çevresinde ~1.5 mm koyu cam halkası ve siyah göz cebi vardır. Siyah pikseller IPS olduğu için hafif mavimsi parlar.",
        "Turuncu parçalar (şapka, kalça topları, patiler) ayrı basılır; tek renkli yazıcı yeterli, AMS gerekmez. Kalça toplarının ekvatorunda iki yarım kürenin birleşim çizgisi görünür.",
        "Görünen vidalar: göbeğin altında 4 adet M2 havşa vida ve her patinin dış yüzünde boynuz vidası (M2, havşa cebinde). Şapka mıknatısla tutulur; diğer bağlantılar kalça topları ve kabuk içinde kalır.",
        "Arkada USB-C soket ve küçük bir sürgü anahtar deliği görünür; ön altta ToF sensörü için Ø6.8 mm siyah pencere vardır.",
        "Kablolar dışarıda görünmez: diz servolarının kabloları topun üst cebinden gövdeye, kafa şeridi içi boş merkez direkten geçer.",
        "Taban TPU 95A siyah, patilere yapıştırılır. Renkler mat PLA'dır; görsellerdeki parlak yansımalar sadece vizörde olmalıdır.",
    ],
}
json.dump(man, open(os.path.join(PKG, "manifest.json"), "w"), ensure_ascii=False, indent=1)
print("dz_rest", dz_rest, "idle base z range", min(b[2] for b in idle["base"]), max(b[2] for b in idle["base"]))
