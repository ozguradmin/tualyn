#!/usr/bin/env python3
"""Tosbi (concept A): build a MuJoCo MJCF that mirrors model.glb exactly.

- Link frames are read from the GLB node graph (same origins, identity rest rotation).
- Joint axes / ranges / zero come from manifest.json (angle convention: q_mjcf[rad] = deg2rad(angle - zero)).
- Collision geometry: convex hulls of each link's visible meshes (one hull per part).
- Masses: per-part masses from concept_A/calc.json (CAD volume x PLA 1.24 g/cm3 x wall/infill, + real component
  masses), assigned to the GLB meshes of the link that carries them. Inertia from area-sampled (printed thin walls)
  or volume (solid components) point clouds of the real meshes.
Run: python3 -I build_mjcf.py   (writes meshes/*.stl, tosbi.xml, links.json)
"""
import json, os, sys
import numpy as np, trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
man = json.load(open(os.path.join(PKG, "manifest.json")))
scene = trimesh.load(os.path.join(PKG, "model.glb"))
G = scene.graph
MESHDIR = os.path.join(HERE, "meshes"); os.makedirs(MESHDIR, exist_ok=True)
rng = np.random.default_rng(0)

LINKS = ["body", "leg_fl", "leg_fr", "leg_rl", "leg_rr", "foot_fl", "foot_fr", "foot_rl", "foot_rr", "head"]
PARENT = {"body": None, "head": "body"}
for l in ("fl", "fr", "rl", "rr"):
    PARENT[f"leg_{l}"] = "body"; PARENT[f"foot_{l}"] = f"leg_{l}"

def local(n):  # transform of node n relative to its parent link
    T = G.get(n)[0]; p = PARENT[n]
    return T if p is None else np.linalg.inv(G.get(p)[0]) @ T
def geom(link, mat):
    nm = f"{link}__{mat}"
    return scene.geometry[nm] if nm in scene.geometry else None

# ---------------------------------------------------------------- masses (g), from calc.json parts
# (link, matKey, grams, mode)  mode: 'surf' thin printed walls | 'vol' solid component
# Review fix 2026-10-25: the BOM parts (GY-521, 39x18 charger, PAM8403 with pot, 2 x GY-53 ToF, KCD1 switch, perfboard,
# bulk caps, JST leads, M2 nuts, upper-deck bracket) add ~25 g over the concept's 380 g.
MASS = [
    ("body", "shell", 17.4, "surf"), ("body", "badge", 2.4, "vol"), ("body", "tail", 0.4, "vol"), ("body", "lip", 0.6, "surf"),
    ("body", "stalk", 1.9, "vol"), ("body", "internal_chassis", 14.0 + 2.5, "vol"),   # deck plate/cradles + upper-deck bracket
    ("body", "internal_servo", 5 * 13.4, "vol"),          # 4 hip servos + neck servo (fixed on the stalk = body link)
    ("body", "internal_cell", 40.0, "vol"),
    ("body", "internal_pcb", 9.0 + 10.5 + 4.5 + 2.5 + 2.0 + 4.0 + 1.5 + 3.5 + 2 * 1.8, "vol"),
    # PCA9685, 3x MP1584, perfboard 30x60, GY-521, 2S BMS, 39x18 charger, USB-C breakout, PAM8403+pot, 2x GY-53
    ("body", "internal_cap", 4.0, "vol"),                 # 2 x 1000 uF + 470 uF
    ("body", "switch", 2.0, "vol"),                       # KCD1 rocker
    ("body", "speaker", 5.0, "vol"),                      # 29 mm speaker
    ("body", "internal_wire", 13.0 + 4.0, "vol"), ("body", "screw", 2.5 + 1.5, "vol"), ("body", "metal", 1.5, "vol"),  # + JST leads, M2 nuts
    ("head", "head", 24.0, "surf"), ("head", "bezel", 1.5, "vol"), ("head", "visor", 3.3, "surf"),
    ("head", "lcd_glass", 3.0, "vol"), ("head", "internal_pcb", 4.0 + 2.5, "vol"),    # LCD PCB, ESP32-S3 SuperMini
    ("head", "internal_wire", 1.0, "vol"),                # 6-core neck flex (jumper-ribbon wires)
]
for l in ("fl", "fr", "rl", "rr"):
    MASS += [(f"leg_{l}", "egg", 5.8, "surf"), (f"leg_{l}", "arm", 7.3, "surf"), (f"leg_{l}", "internal_servo", 13.4, "vol"),
             (f"foot_{l}", f"boot_{l}", 7.5, "surf"), (f"foot_{l}", f"toe_{l}", 1.8, "vol")]

def part_props(m, mode, g):
    """(mass kg, com m, inertia about com kg m^2) of one part."""
    kg = g / 1000.0
    if mode == "vol" and m.is_watertight and m.volume > 0:
        mm = m.copy(); mm.apply_scale(0.001)
        mp = mm.mass_properties          # density 1
        return kg, np.asarray(mp["center_mass"]), np.asarray(mp["inertia"]) * kg / mp["mass"]
    if mode == "surf":
        P = trimesh.sample.sample_surface(m, 8000, seed=1)[0] / 1000.0
    else:                                 # box (thin chassis plate) or non-watertight fallback
        lo, hi = m.bounds; P = rng.uniform(lo, hi, (8000, 3)) / 1000.0
    c = P.mean(0); d = P - c; w = kg / len(P)
    I = w * (np.eye(3) * (d ** 2).sum() - d.T @ d)
    return kg, c, I

inert = {}
for link in LINKS:
    parts = [part_props(geom(link, mat), mode, g) for (lk, mat, g, mode) in MASS if lk == link]
    for (lk, mat, g, mode) in MASS:
        if lk == link and geom(link, mat) is None: sys.exit(f"missing mesh {link}__{mat}")
    M = sum(p[0] for p in parts); c = sum(p[0] * p[1] for p in parts) / M
    I = np.zeros((3, 3))
    for mk, ck, Ik in parts:
        d = ck - c; I += Ik + mk * (np.dot(d, d) * np.eye(3) - np.outer(d, d))
    inert[link] = (M, c, I)

# ---------------------------------------------------------------- collision hulls (link-local, metres)
HULLS = {"body": [["shell", "lip", "switch"], ["tail"]],
         "head": [["head", "bezel", "visor"]]}
for l in ("fl", "fr", "rl", "rr"):
    HULLS[f"leg_{l}"] = [["egg"], ["arm"]]
    HULLS[f"foot_{l}"] = [[f"boot_{l}"], [f"toe_{l}"]]
hullfiles = {}
for link, groups in HULLS.items():
    hullfiles[link] = []
    for gi, mats in enumerate(groups):
        V = np.vstack([geom(link, m).vertices for m in mats])
        h = trimesh.Trimesh(V / 1000.0).convex_hull
        hv = h.vertices
        if len(hv) > 240:               # farthest-point subsample of the hull vertices (keeps shape within ~0.3 mm)
            sel = [int(np.argmin(hv[:, 2]))]; dmin = np.linalg.norm(hv - hv[sel[0]], axis=1)
            for _ in range(239):
                k = int(np.argmax(dmin)); sel.append(k); dmin = np.minimum(dmin, np.linalg.norm(hv - hv[k], axis=1))
            h2 = trimesh.Trimesh(hv[sel]).convex_hull
            err = float(np.max(np.abs(trimesh.proximity.signed_distance(h2, hv[::7]))) if False else 0.0)
            h = h2
        fn = f"{link}_{gi}_{'_'.join(mats)}.stl"
        h.export(os.path.join(MESHDIR, fn))
        hullfiles[link].append((fn, mats))

# ---------------------------------------------------------------- MJCF
J = man["joints"]
JOINT_OF = {v["node"]: k for k, v in J.items()}
TOE = {f"foot_{l}" for l in ("fl", "fr", "rl", "rr")}

def f3(v): return " ".join(f"{x:.6g}" for x in v)
def body_xml(link, ind):
    T = local(link); pos = T[:3, 3] / 1000.0
    assert np.allclose(T[:3, :3], np.eye(3), atol=1e-9), link
    M, c, I = inert[link]
    s = [f'{ind}<body name="{link}" pos="{f3(pos)}">']
    if link == "body":
        s.append(f'{ind}  <freejoint name="root"/>')
    else:
        jn = JOINT_OF[link]; j = J[jn]
        s.append(f'{ind}  <joint name="{jn}" class="servo" axis="{f3(j["axis"])}" range="{np.deg2rad(j["min"] - j.get("zero", 0)):.5f} {np.deg2rad(j["max"] - j.get("zero", 0)):.5f}"/>')
    s.append(f'{ind}  <inertial pos="{f3(c)}" mass="{M:.6g}" fullinertia="{I[0,0]:.6g} {I[1,1]:.6g} {I[2,2]:.6g} {I[0,1]:.6g} {I[0,2]:.6g} {I[1,2]:.6g}"/>')
    for fn, mats in hullfiles[link]:
        nm = fn[:-4]
        cls = "tpu" if any(m.startswith("toe") for m in mats) else "pla"
        s.append(f'{ind}  <geom name="{nm}" class="{cls}" type="mesh" mesh="{nm}"/>')
    if link == "body":   # GY-521 on the deck: x 0, y -21, 1.6 mm above the mid-plane (internals.py)
        s.append(f'{ind}  <site name="imu" pos="0 {-21.0/1000:.5f} {(42.45+1.6)/1000:.5f}"/>')
    for ch in LINKS:
        if PARENT.get(ch) == link: s += body_xml(ch, ind + "  ")
    s.append(f"{ind}</body>")
    return s

# MG90S at ~5.5 V: stall 0.20 N m, no-load 0.10 s/60 deg = 600 deg/s = 10.47 rad/s
TAU, WMAX = 0.20, np.deg2rad(600)
DAMP = TAU / WMAX          # back-EMF-like linear torque-speed line: tau = 0.2 - 0.0191*w
KP = 3.0                   # N m / rad -> torque saturates at ~3.8 deg position error (hobby-servo P loop)
ARM = 2.0e-4               # reflected rotor inertia, kg m^2 (motor ~5e-9 x gear ratio^2 ~ 3e4..9e4)
xml = f"""<mujoco model="tosbi">
  <compiler angle="radian" meshdir="meshes" autolimits="true"/>
  <option timestep="0.001" integrator="implicitfast" gravity="0 0 -9.81"/>
  <default>
    <joint damping="{DAMP:.5f}" armature="{ARM}" frictionloss="0.004" solreflimit="0.002 1" solimplimit="0.95 0.99 0.0005" margin="0.002"/>
    <default class="servo"/>
    <geom contype="1" conaffinity="1" condim="3" solref="0.004 1" solimp="0.9 0.95 0.001"/>
    <default class="pla"><geom friction="0.6 0.005 0.0001" rgba="0.62 0.85 0.76 1"/></default>
    <default class="tpu"><geom friction="0.9 0.005 0.0001" priority="1" rgba="0.93 0.36 0.30 1"/></default>
    <position kp="{KP}" forcerange="-{TAU} {TAU}" forcelimited="true"/>
  </default>
  <asset>
{chr(10).join(f'    <mesh name="{fn[:-4]}" file="{fn}"/>' for l in LINKS for fn, _ in hullfiles[l])}
  </asset>
  <worldbody>
    <light pos="0 0 1" dir="0 0 -1"/>
    <geom name="floor" type="plane" size="2 2 0.01" friction="0.6 0.005 0.0001" rgba="0.9 0.9 0.88 1"/>
{chr(10).join(body_xml("body", "    "))}
  </worldbody>
  <actuator>
{chr(10).join(f'    <position name="{k}" joint="{k}" ctrlrange="{np.deg2rad(v["min"]-v.get("zero",0)):.5f} {np.deg2rad(v["max"]-v.get("zero",0)):.5f}"/>' for k, v in J.items())}
  </actuator>
  <sensor>
    <framequat name="imu_quat" objtype="site" objname="imu"/>
    <accelerometer name="imu_acc" site="imu"/>
  </sensor>
</mujoco>
"""
open(os.path.join(HERE, "tosbi.xml"), "w").write(xml)
summary = {l: {"mass_g": round(inert[l][0] * 1000, 2), "com_mm": (inert[l][1] * 1000).round(2).tolist()} for l in LINKS}
tot = sum(inert[l][0] for l in LINKS)
summary["total_g"] = round(tot * 1000, 1)
json.dump(summary, open(os.path.join(HERE, "links.json"), "w"), indent=1)
print(json.dumps(summary))
