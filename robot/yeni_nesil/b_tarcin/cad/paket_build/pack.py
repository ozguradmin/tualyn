#!/usr/bin/env python3
"""Assemble build/meshes/*.npz into ../model.glb (articulated, link frames as in the concept mechanism),
write ../manifest.json and the placeholder ../anim/idle.json.

Link tree (all rest rotations identity, joint axes in the link frame):
  body (root; origin on the hip-axis height, centre of the body)          free base
   |- head      origin (0,-32,0)  axis +Z   neck_pan   (4 g micro servo in the head, neck post fixed to body)
   |- tail      origin (0,+48,-5) axis +Y   tail       (MG90S in the rump, wiper-style wag + self-righting lever)
   |- thigh_fl  origin (0,-32,0)  axis +X   hip_fl     (+x side = robot's LEFT; robot faces -Y)
   |    |- shin_fl origin (0,0,-40) axis +X knee_fl
   |- thigh_fr  (-x side, mirrored geometry, same axis/sign convention) ...
   |- thigh_hl / thigh_hr  origin (0,+32,0)
Angle convention (= concept model.py / sim): hip = thigh angle a from -Z toward +Y; knee = b - a (b = shin abs. angle).
"""
import json, math, os, glob, sys
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.abspath(os.path.join(HERE, ".."))
MD = os.path.join(HERE, "meshes")
L1 = 40.0
HIP_Y = 32.0


def load(name):
    d = np.load(os.path.join(MD, name + ".npz"))
    return d["v"].astype(np.float64), d["f"].astype(np.int64)


def rx(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    R = np.eye(4); R[1, 1] = c; R[1, 2] = -s; R[2, 1] = s; R[2, 2] = c
    return R


def rz(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    R = np.eye(4); R[0, 0] = c; R[0, 1] = -s; R[1, 0] = s; R[1, 1] = c
    return R


def ry(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    R = np.eye(4); R[0, 0] = c; R[0, 2] = s; R[2, 0] = -s; R[2, 2] = c
    return R


def tr(x, y, z):
    T = np.eye(4); T[:3, 3] = (x, y, z)
    return T


LEGS = {  # name: (end, x side, y)
    "fl": ("F", +1, -HIP_Y), "fr": ("F", -1, -HIP_Y), "hl": ("H", +1, +HIP_Y), "hr": ("H", -1, +HIP_Y)}

# ---------------------------------------------------------------------------------- collect link meshes
links = {"body": {}, "head": {}, "tail": {}}
for f in sorted(glob.glob(os.path.join(MD, "*.npz"))):
    n = os.path.basename(f)[:-4]
    link, mat = n.split("__")
    if link in links:
        mat = {("head", "shell"): "shell_head", ("head", "charcoal"): "mouth"}.get((link, mat), mat)
        links[link][mat] = load(n)
for leg, (end, sx, y) in LEGS.items():
    for part in ("thigh", "shin"):
        d = {}
        for f in sorted(glob.glob(os.path.join(MD, f"{part}__*_{end}.npz"))):
            n = os.path.basename(f)[:-4]
            mat = n.split("__")[1][:-2]
            v, fc = load(n)
            if sx < 0:
                v = v * np.array([-1.0, 1.0, 1.0])
                fc = fc[:, ::-1].copy()
            if mat == "paw":
                mat = "paw_f" if end == "F" else "paw_h"
            d[mat] = (v, fc)
        links[f"{part}_{leg}"] = d

parent = {"head": "body", "tail": "body"}
origin = {"head": (0, -HIP_Y, 0), "tail": (0, 48.0, -5.0)}
for leg, (end, sx, y) in LEGS.items():
    parent[f"thigh_{leg}"] = "body"; origin[f"thigh_{leg}"] = (0, y, 0)
    parent[f"shin_{leg}"] = f"thigh_{leg}"; origin[f"shin_{leg}"] = (0, 0, -L1)

JOINTS = {"neck_pan": ("head", [0, 0, 1], -40, 40), "tail": ("tail", [0, 1, 0], -85, 85)}
for leg, (end, sx, y) in LEGS.items():
    if end == "F":
        JOINTS[f"hip_{leg}"] = (f"thigh_{leg}", [1, 0, 0], -20, 160)
        JOINTS[f"knee_{leg}"] = (f"shin_{leg}", [1, 0, 0], -140, 25)
    else:
        JOINTS[f"hip_{leg}"] = (f"thigh_{leg}", [1, 0, 0], -50, 130)
        JOINTS[f"knee_{leg}"] = (f"shin_{leg}", [1, 0, 0], -25, 140)
POSE_REST = {"neck_pan": 0, "tail": 0}
for leg in LEGS:
    f = leg[0] == "f"
    POSE_REST[f"hip_{leg}"] = 20 if f else -20
    POSE_REST[f"knee_{leg}"] = -44 if f else 44


def world_T(link, pose, root=np.eye(4)):
    if link == "body":
        return root
    T = world_T(parent[link], pose, root) @ tr(*origin[link])
    for jn, (node, ax, lo, hi) in JOINTS.items():
        if node == link:
            a = pose.get(jn, 0.0)
            T = T @ (rx(a) if ax[0] else rz(a) if ax[2] else ry(a))
    return T


def is_visible(mat):
    return not mat.startswith("internal")


# ---------------------------------------------------------------------------------- rest-pose ground
zmin = 1e9
for link, mats in links.items():
    T = world_T(link, POSE_REST)
    for mat, (v, f) in mats.items():
        if not is_visible(mat):
            continue
        w = (T[:3, :3] @ v.T).T + T[:3, 3]
        zmin = min(zmin, w[:, 2].min())
ROOT_Z = -zmin
print("root z (hip axis height above desk) =", round(ROOT_Z, 2))
# body node = identity (origin on the desk under the body centre): shift body meshes and child origins by ROOT_Z,
# so that anim 'base' = world pose of the body node exactly as rig.js applies it.
for mat, (v, f) in list(links["body"].items()):
    links["body"][mat] = (v + np.array([0, 0, ROOT_Z]), f)
for k in list(origin):
    if parent[k] == "body":
        origin[k] = (origin[k][0], origin[k][1], origin[k][2] + ROOT_Z)

# ---------------------------------------------------------------------------------- GLB
scene = trimesh.Scene()
scene.graph.update(frame_from=scene.graph.base_frame, frame_to="body", matrix=np.eye(4))
order = ["body", "head", "tail"] + [f"{p}_{l}" for l in LEGS for p in ("thigh", "shin")]
for link in order:
    if link != "body":
        scene.graph.update(frame_from=parent[link], frame_to=link, matrix=tr(*origin[link]))
ntri = 0
tri_by = {}
for link in order:
    for mat, (v, f) in links[link].items():
        m = trimesh.Trimesh(vertices=v, faces=f, process=True)
        ntri += len(m.faces)
        tri_by[f"{link}__{mat}"] = len(m.faces)
        scene.add_geometry(m, node_name=f"{link}__{mat}", geom_name=f"{link}__{mat}", parent_node_name=link)
glb = scene.export(file_type="glb")
open(os.path.join(PKG, "model.glb"), "wb").write(glb)
print("triangles", ntri, "glb MB", round(len(glb) / 1e6, 2))

# overall bbox at rest
allw = []
for link, mats in links.items():
    T = world_T(link, POSE_REST)
    for mat, (v, f) in mats.items():
        if is_visible(mat):
            allw.append((T[:3, :3] @ v.T).T + T[:3, 3])
allw = np.vstack(allw)
dims = (allw.max(0) - allw.min(0)).round(1).tolist()
print("rest bbox mm (x,y,z):", dims, "zmin", allw[:, 2].min().round(3))

json.dump({"root_z": ROOT_Z, "triangles": ntri, "tri_by": tri_by, "dims": dims}, open(os.path.join(HERE, "pack_info.json"), "w"), indent=1)
if "--manifest-skeleton" not in sys.argv:
    # Default since the review update: write ONLY model.glb + pack_info.json. manifest.json is maintained by the motion
    # stage and build/manifest_patch.py; the skeleton below (and the placeholder idle) would overwrite their content.
    print("ok (GLB only; pass --manifest-skeleton to regenerate the stage-1 manifest + placeholder idle)")
    sys.exit(0)
# ---------------------------------------------------------------------------------- manifest
PLA = 0.16
mats = {
    "shell":        {"type": "print", "color": "#e0692b", "filament": "Elas PLA Turuncu (mat)", "layer": PLA, "layerAxis": [0, 0, 1],
                     "part": "gövde üst kabuğu, kubbe yukarı basılır"},
    "shell_head":   {"type": "print", "color": "#e0692b", "filament": "Elas PLA Turuncu (mat)", "layer": 0.12, "layerAxis": [0, 0, 1],
                     "part": "kafa tepe kabuğu, kubbe yukarı, 0.12 mm katman"},
    "shellcap":     {"type": "print", "color": "#e0692b", "filament": "Elas PLA Turuncu (mat)", "layer": PLA, "layerAxis": [0, 0, 1],
                     "part": "kafa çene/alt kapağı (boyun deliği, 2x M2 vida)"},
    "hub":          {"type": "print", "color": "#e0692b", "filament": "Elas PLA Turuncu (mat)", "layer": PLA, "layerAxis": [1, 0, 0],
                     "part": "kalça göbek direkleri, uçları üzerine basılır"},
    "shell_pod":    {"type": "print", "color": "#e0692b", "filament": "Elas PLA Turuncu (mat)", "layer": PLA, "layerStrength": 0.38, "layerAxis": [1, 0, 0],
                     "part": "bacak modülü dış kapağı, ayırma yüzü tablaya"},
    "shell_podin":  {"type": "print", "color": "#e0692b", "filament": "Elas PLA Turuncu (mat)", "layer": PLA, "layerStrength": 0.38, "layerAxis": [1, 0, 0],
                     "part": "bacak modülü iç yarısı (2 servo + göbek yakaları), ayırma yüzü tablaya"},
    "shell_tail":   {"type": "print", "color": "#e0692b", "filament": "Elas PLA Turuncu (mat)", "layer": 0.2, "layerAxis": [0, 0, 1],
                     "part": "kuyruk halkaları (içi boş, dik basılır)"},
    "ear":          {"type": "print", "color": "#e0692b", "filament": "Elas PLA Turuncu (mat)", "layer": PLA, "layerAxis": [0, 0.985, -0.174],
                     "part": "kulak dış kabuğu, yatık basılır, mıknatısla takılır"},
    "cream":        {"type": "print", "color": "#efe4cc", "filament": "Elas PLA Krem / Fildişi", "layer": PLA, "layerAxis": [0, 0, 1],
                     "part": "karın kabuğu"},
    "cream_face":   {"type": "print", "color": "#efe4cc", "filament": "Elas PLA Krem / Fildişi", "layer": PLA, "layerAxis": [0, 1, 0],
                     "part": "ağız/yanak parçası, düz yüzü tablaya"},
    "cream_ear":    {"type": "print", "color": "#efe4cc", "filament": "Elas PLA Krem / Fildişi", "layer": PLA, "layerAxis": [0, 0.985, -0.174],
                     "part": "kulak içi"},
    "cheek":        {"type": "print", "color": "#efe4cc", "filament": "Elas PLA Krem / Fildişi (0.6 mm pencere, arkasında WS2812B)", "layer": PLA,
                     "layerAxis": [0, 1, 0], "part": "yanak ışık pencereleri (LED kapalıyken krem görünür)"},
    "charcoal":     {"type": "print", "color": "#26272b", "filament": "Elas PLA Siyah", "layer": PLA, "layerAxis": [0, 0, 1], "part": "boyun direği"},
    "mouth":        {"type": "print", "color": "#26272b", "filament": "Elas PLA Siyah (kakma parça; AMS ya da ayrı parça + yapıştırma)", "layer": PLA,
                     "layerAxis": [0, 1, 0], "part": "ω ağız"},
    "sock":         {"type": "print", "color": "#26272b", "filament": "Elas PLA Siyah", "layer": PLA, "layerStrength": 0.38, "layerAxis": [0, 0, 1],
                     "part": "bacak 'çorap' kapağı, dik basılır, oluğa geçme + yapıştırma"},
    "ring":         {"type": "print", "color": "#26272b", "filament": "Elas PLA Siyah", "layer": 0.2, "layerAxis": [0, 0, 1], "part": "kuyruk siyah halkaları"},
    "shin":         {"type": "print", "color": "#26272b", "filament": "Elas PLA Siyah", "layer": PLA, "layerAxis": [1, 0, 0],
                     "part": "kaval plakası, düz basılır (katmanlar kalınlık boyunca)"},
    "backer":       {"type": "print", "color": "#1d1e21", "filament": "Elas PLA Siyah", "layer": PLA, "layerAxis": [0, 1, 0],
                     "part": "füme akrilik arkasındaki siyah maske/ekran yuvası"},
    "nose":         {"type": "petg", "color": "#141518", "filament": "PETG Siyah (doğal yarı parlak; kavisli olduğu için ütüleme yok)",
                     "layerAxis": [0, 0, 1]},
    "paw_f":        {"type": "tpu", "color": "#202124", "filament": "TPU 95A Siyah", "layerAxis": [0, -0.407, 0.914], "part": "ön pati, taban tablaya"},
    "paw_h":        {"type": "tpu", "color": "#202124", "filament": "TPU 95A Siyah", "layerAxis": [0, 0.407, 0.914], "part": "arka pati, taban tablaya"},
    "visor":        {"type": "acrylic", "color": "#0b0c0e", "opacity": 0.32, "note": "2 mm açık füme akrilik (~%65-70 geçirgen), lazer kesim maske şekli; arkası siyah PLA"},
    "lcdglass":     {"type": "glass", "color": "#050607", "roughness": 0.06, "note": "GC9A01 cam: Ø35.5, aktif alan dışındaki siyah halka"},
    "screen_eyeL":  {"type": "screen", "screen": "eyeL"},
    "screen_eyeR":  {"type": "screen", "screen": "eyeR"},
    "screw":        {"type": "metal", "color": "#a9adb3", "roughness": 0.38, "note": "M2 yıldız başlı galvaniz vida (havşada) + USB-C soket"},
    "tofwin":       {"type": "glass", "color": "#0d0e10", "roughness": 0.08, "note": "VL53L0X için 1 mm IR-geçirgen siyah akrilik pencere"},
    "speaker":      {"type": "rubber", "color": "#18191b", "note": "20 mm 1 W hoparlör konisi, ızgaranın hemen arkasında"},
    "wire_brown":   {"type": "rubber", "color": "#4a3122", "note": "servo kablosu (kahve/kırmızı/turuncu), kalçadan gövdeye servis halkası"},
    "wire_red":     {"type": "rubber", "color": "#a3281f"},
    "wire_orange":  {"type": "rubber", "color": "#d9822b"},
    "internal_servo":   {"type": "internal", "color": "#3b82f6", "note": "MG90S x9 (8 bacak + kuyruk), 4 g mikro servo (kafa)"},
    "internal_horn":    {"type": "internal", "color": "#e5e7eb", "note": "servo kolları"},
    "internal_battery": {"type": "internal", "color": "#22c55e", "note": "2S 14500 Li-ion"},
    "internal_pcb":     {"type": "internal", "color": "#0f766e", "note": "ESP32-S3 Super Mini x2, BMS, şarj kartı, BMI160, VL53L0X, TTP223, hoparlör"},
    "internal_power":   {"type": "internal", "color": "#f59e0b", "note": "MP1584 x3 + kondansatörler"},
    "internal_screen":  {"type": "internal", "color": "#14b8a6", "note": "GC9A01 modül PCB'leri + pin başlıkları"},
}
# rename mesh-level keys that are shared between links but differ in print orientation
manifest = {
    "key": "B", "name": "Tarçın", "subtitle_tr": "Cep boyu kızıl panda",
    "tagline_tr": "Maskeli yüzü, iki yuvarlak göz ekranı ve hem sevinçle sallanan hem de düşünce kalkmasını sağlayan halkalı kuyruğuyla cep boyu kızıl panda yavrusu.",
    "accent": "#e0692b",
    "glb": "model.glb",
    "creaseDeg": 40,
    "frame_notes": "mm, Z yukarı, robot -Y'ye bakar. +x = robotun SOLU (fl/hl/eyeL), -x = SAĞI (fr/hr/eyeR). "
                   "Konsept model.py/sim 'R'=+x der: sim hip_FR = buradaki hip_fl, hip_FL = hip_fr, hip_HR = hip_hl, hip_HL = hip_hr. "
                   "Kalça = uyluğun -Z'den +Y'ye açısı (a); diz = b - a. "
                   "Kök düğüm 'body' birim dönüşümlüdür: orijini masada, gövde merkezinin altında; kalça ekseni z = " + str(round(ROOT_Z, 2)) + " mm. "
                   "anim base = bu düğümün dünya pozu, dinlenmede [0,0,0,1,0,0,0]. MuJoCo gövde (kalça yüksekliğindeki torso) pozundan: "
                   "base = torso_pose * T(0,0,-" + str(round(ROOT_Z, 2)) + ").",
    "joints": {},
    "materials": mats,
    "screens": {
        "eyeL": {"res": [240, 240], "round": True, "uvAxes": ["x", "z"], "panel": "GC9A01 1.28in IPS 240x240 (RGB565, SPI)",
                 "active_diam_mm": 32.4, "glass_diam_mm": 35.5, "brightness": 1.5,
                 "behind": "2 mm füme akrilik (açık füme, yaklaşık %65-70 ışık geçirir)", "side": "+x (robotun solu)"},
        "eyeR": {"res": [240, 240], "round": True, "uvAxes": ["x", "z"], "panel": "GC9A01 1.28in IPS 240x240 (RGB565, SPI)",
                 "active_diam_mm": 32.4, "glass_diam_mm": 35.5, "brightness": 1.5,
                 "behind": "2 mm füme akrilik (açık füme, yaklaşık %65-70 ışık geçirir)", "side": "-x (robotun sağı)"},
    },
    "faces": {},
    "animations": {"idle": "anim/idle.json"},
    "pose_rest": POSE_REST,
    "specs": {
        "dims_mm": [round(d) for d in dims], "mass_g": 368, "servos": 10, "motors": 0,
        "servo_list": "9x MG90S (8 bacak + kuyruk), 1x 4 g dijital mikro servo (kafa pan)",
        "brain": "2x ESP32-S3 Super Mini (kafa: gözler, Wi-Fi/Claude API, ses; gövde: 9 servo, IMU, ToF) - UART ile bağlı",
        "battery": "2S 14500 Li-ion (7.4 V, ~6 Wh), 2S BMS + USB-C 2S şarj kartı (port karnın önünde)",
        "runtime_walk_min": 30, "runtime_idle_h": 2.2, "walk_speed_cm_s": 0,
        "screens": "2x GC9A01 1.28\" yuvarlak IPS 240x240, 2 mm füme akrilik maskenin arkasında",
        "self_righting": "Kuyruk kaldıraç + bacak tekmesi (OpenCat 'rc' tarzı); konsept MuJoCo testinde μ=0.6'da 24/24, μ=0.4'te 20/24",
        "sensors": ["BMI160 IMU", "VL53L0X masa kenarı (ToF, göğüste)", "TTP223 kafa dokunma", "INMP441 yok (ses telefondan/PC'den)"],
        "voice": "PAM8403 + 32 mm hoparlör (kafa arkası ızgara) - cıvıltı/ses; konuşma tanıma telefon/PC üzerinden",
        "hip_height_mm": round(ROOT_Z, 1),
    },
    "sim_summary": {"walk_speed_cm_s": 0, "recovery": "konsept sim: 24/24 (μ 0.6), 20/24 (μ 0.4) - hareket aşamasında yeniden doğrulanacak",
                    "notes": "Bu paketteki animasyonlar henüz yer tutucu (idle)."},
    "realism_notes_tr": [
        "Gövde, kafa, bacaklar ve kuyruk mat PLA'dır: yakından 0.12-0.16 mm katman çizgileri görünür, parlak 'oyuncak' yüzey yoktur.",
        "Parçaların birleştiği yerlerde 0.5-0.8 mm ek çizgileri (gövde üst/karın, kafa tepe/çene kapağı, ağız parçası, bacak modülü iç/dış yarısı, siyah çorap, kuyruk halkaları) gerçekten görünür.",
        "Gözler iki adet GC9A01 1.28\" yuvarlak IPS ekrandır: 240x240 piksel, 32.4 mm aktif daire. Yakından pikseller seçilir; çizimler ESP32'nin RGB565 renkleriyle, yazılımın çizebileceği basit şekillerdir.",
        "Ekranlar 2 mm füme akriliğin arkasındadır: göz parlaklığı yaklaşık üçte bir azalır ve parlak odada akrilik yansıması gözlerin üstüne gri bir perde ekler, camın siyah kenar halkası ve IPS siyahının hafif mavi parlaması akrilik arkasından belli belirsiz görünür.",
        "Siyah maske parlak görünüyorsa bu baskı değil, lazer kesim füme akriliktir. Burun PETG'dir, doğal yarı parlak; ütüleme kavisli yüzeyde mümkün değildir.",
        "Vidalar gizli değildir: karnın altında 4, kafanın altında 2, her bacak modülünün iç yüzünde 1 ve her kaval plakasında 3 adet M2 vida başı görünür; kuyruk kökünün arkasında da bir servo vidası vardır.",
        "Her kalçada iki servonun 6 telli kablosu (kahve/kırmızı/turuncu) bacak modülünden gövdeye kısa bir halka yaparak geçer; alttan ve önden bakınca görünür.",
        "Ağız ('ω') ekran değildir, basılı siyah kakma parçadır ve hareket etmez. Konuşma; gözlerin ritmik nabzı, kafa ve kuyruk hareketiyle anlatılır.",
        "Yanak pencereleri arkasında WS2812B LED olan ince krem PLA'dır; LED kapalıyken krem görünür, mutlu olduğunda pembe yanar.",
        "Turuncu, krem ve siyah standart PLA renkleridir (Elas/Porima vb.); ayrı parçalar olarak basıldığı için çok renkli yazıcı (AMS) gerekmez, yalnızca ağız kakması için gerekir ya da ayrı parça yapıştırılır.",
        "USB-C şarj girişi karnın önündedir (konseptteki yan konumda kalça göbeği var); şarj için robot yan yatırılır veya L tipi kablo kullanılır.",
        "Göğüsteki küçük siyah pencere, masa kenarını gören VL53L0X sensörüdür.",
    ],
}
for jn, (node, ax, lo, hi) in JOINTS.items():
    j = {"node": node, "axis": ax, "min": lo, "max": hi, "zero": 0}
    if jn == "neck_pan":
        j["servo"] = "4 g dijital mikro servo (E-Sky 002279 / ES9051 sınıfı)"
        j["note"] = "+ açı yüzü +x'e (robotun soluna) çevirir"
    elif jn == "tail":
        j["servo"] = "MG90S (metal dişli önerilir)"
        j["note"] = "silecek gibi yana sallanır; + açı ucu +x'e götürür"
    else:
        j["servo"] = "MG90S"
        j["side"] = "+x (robotun solu)" if jn.endswith("l") else "-x (robotun sağı)"
        j["sim_name"] = {"fl": "FR", "fr": "FL", "hl": "HR", "hr": "HL"}[jn[-2:]].join(["hip_" if jn.startswith("hip") else "knee_", ""])
    manifest["joints"][jn] = j
for e in ["neutral", "blink", "happy", "talk_a", "talk_b", "surprised", "sleepy", "sleep", "sad", "determined", "curious", "love"]:
    manifest["faces"][e] = {"eyeL": f"faces/{e}_L.png", "eyeR": f"faces/{e}_R.png"}

mp = os.path.join(PKG, "manifest.json")
if os.path.exists(mp):            # keep fields other stages may have added (animations, sim_summary, specs...)
    old = json.load(open(mp))
    for k in ("animations",):
        if k in old:
            manifest[k] = {**manifest[k], **old[k]}
json.dump(manifest, open(mp, "w"), indent=1, ensure_ascii=False)

# ---------------------------------------------------------------------------------- placeholder idle (2 s breathing)
fps, n = 30, 61
L2 = 34.0
a0 = 20.0
b0 = -24.0
h0 = L1 * math.cos(math.radians(a0)) + L2 * math.cos(math.radians(b0))
J = {k: [] for k in JOINTS}
base = []
for i in range(n):
    t = i / (n - 1)
    s = math.sin(2 * math.pi * t)
    a = a0 + 3.5 * s
    b = -math.degrees(math.asin(L1 * math.sin(math.radians(a)) / L2))
    h = L1 * math.cos(math.radians(a)) + L2 * math.cos(math.radians(b))
    for leg in LEGS:
        f = leg[0] == "f"
        J[f"hip_{leg}"].append(round(a if f else -a, 3))
        J[f"knee_{leg}"].append(round((b - a) if f else -(b - a), 3))
    J["neck_pan"].append(round(4.0 * math.sin(2 * math.pi * t + 0.8), 3))
    J["tail"].append(round(9.0 * math.sin(2 * math.pi * t), 3))
    base.append([0.0, 0.0, round(h - h0, 3), 1.0, 0.0, 0.0, 0.0])
idle = {"fps": fps, "loop": True, "frames": n, "joints": J, "base": base,
        "face": [[0, "neutral"], [36, "blink"], [40, "neutral"]],
        "source": "kinematic placeholder (2 s breathing loop, paws kept under the hips); to be replaced by the motion stage",
        "metrics": {}}
os.makedirs(os.path.join(PKG, "anim"), exist_ok=True)
json.dump(idle, open(os.path.join(PKG, "anim", "idle.json"), "w"))
json.dump({"root_z": ROOT_Z, "triangles": ntri, "tri_by": tri_by, "dims": dims}, open(os.path.join(HERE, "pack_info.json"), "w"), indent=1)
print("ok")
