#!/usr/bin/env python3
"""Build the MuJoCo model of Yumurcak (package D) straight from ../model.glb, so that the MJCF link frames are
EXACTLY the GLB link frames used by rig.js:
  * every link body sits at the GLB node origin (rig_info.json), identity rest rotation, same parent;
  * every hinge uses the manifest axis (in the link frame) and the manifest range; qpos 0 = manifest zero (0);
  * the free joint of `body` = the GLB root node pose (origin on the ground under the egg centre).
So joint qpos (deg) and the body pose (xpos mm, xquat) replay 1:1 in rig.js.

Collision: convex hulls of each link's real exterior meshes (paw split into 3 hulls along its length, TPU sole
separate with its own friction). Masses: the concept's itemised mass budget (concept_D2/check.json, 345.6 g),
each item spread over its real CAD mesh (surface samples for thin shells, volume samples for solids) -> link mass,
CoM and full inertia.

usage: python3 -I build_mjcf.py [mu]   -> yumurcak_mu<mu>.xml (default writes 0.6 and 0.4)
"""
import json, math, os, sys
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
CONCEPT = os.path.join(os.path.dirname(PKG), "..", "concept_D2")
info = json.load(open(os.path.join(PKG, "src", "rig_info.json")))
man = json.load(open(os.path.join(PKG, "manifest.json")))
CZ = info["CZ"]
ORIG = {k: np.array(v) for k, v in info["origins"].items()}
PARENT = info["parents"]
sc = trimesh.load(os.path.join(PKG, "model.glb"))
G = dict(sc.geometry)
LEGS = ["fl", "fr", "bl", "br"]
rng = np.random.default_rng(1)
MESHDIR = os.path.join(HERE, "meshes")
os.makedirs(MESHDIR, exist_ok=True)


def geo(name):
    return G[name]


def surf(m, n=3000):
    return trimesh.sample.sample_surface(m, n, seed=1)[0]


def vol(m, n=3000):
    """uniform volume samples of a solid: each connected component approximated by its convex hull
    (no rtree in this container), components weighted by hull volume"""
    comps = m.split(only_watertight=False) if len(m.faces) > 12 else [m]
    hulls = [c.convex_hull for c in comps]
    vols = np.array([max(hh.volume, 1e-6) for hh in hulls])
    pts = []
    for hh, v in zip(hulls, vols):
        k = max(20, int(n * v / vols.sum()))
        lo, hi = hh.bounds
        P = rng.uniform(lo, hi, size=(k * 6, 3))
        nrm = hh.face_normals; d = (hh.triangles[:, 0, :] * nrm).sum(1)
        inside = np.all(P @ nrm.T - d <= 1e-9, axis=1)
        P = P[inside][:k]
        if len(P) == 0:
            P = hh.vertices
        pts.append(P)
    return np.vstack(pts)


def C2world(p):            # concept body frame -> world (GLB) frame
    return np.array(p, float) + [0, 0, CZ]


# ---------------------------------------------------------------- mass items (grams, points in LINK frame)
ITEMS = {"body": [], "head": []}
for k in LEGS:
    ITEMS["haunch_" + k] = []
    ITEMS["paw_" + k] = []
b = ITEMS["body"]
b.append(("body shell PLA", 19.2, surf(geo("body__shell"))))
b.append(("4 x yaw MG90S", 4 * 13.4, vol(geo("body__internal_servo"))))
b.append(("2 x 14500", 41.0, vol(geo("body__internal_battery"))))
b.append(("deck/collars/posts/sled", 9.1, vol(geo("body__internal_frame"))))
b.append(("ESP32 + bucks + charger/BMS + IMU/ToF", 18.0, vol(geo("body__internal_pcb"))))
b.append(("wiring, caps", 16.0, C2world([0, 5, -5])[None, :]))
b.append(("M2 screws, inserts, PTFE, magnets", 8.0, C2world([0, 0, -10])[None, :]))
h = ITEMS["head"]
oh = ORIG["head"]
h.append(("head shell PLA", 21.4, surf(geo("head__shell"))))
h.append(("visor PETG", 6.2, surf(geo("head__visor"))))
h.append(("eggshell cap", 4.9, surf(geo("head__cap"))))
h.append(("SG90", 9.0, vol(geo("head__internal_servo"))))
h.append(("2 x GC9A01", 12.0, np.vstack([vol(geo("head__internal_lcd")), vol(geo("head__internal_pcb_disp"))])))
for k in LEGS:
    ITEMS["haunch_" + k] += [("ball PLA", 9.0, surf(geo(f"haunch_{k}__ball"))),
                             ("knee MG90S", 13.4, vol(geo(f"haunch_{k}__internal_servo"))),
                             ("yaw horn+screws", 1.2, vol(geo(f"haunch_{k}__internal_horn")))]
    pawm = trimesh.util.concatenate([geo(f"paw_{k}__paw"), geo(f"paw_{k}__sole")])
    ITEMS["paw_" + k] += [("paw PLA + TPU sole", 7.0, vol(geo(f"paw_{k}__paw"))),
                          ("knee horn + screw", 1.2, vol(geo(f"paw_{k}__internal_horn")))]
# body items given in world coords == body frame (body origin = world origin at rest) -> OK as is


def inertial(items):
    M = sum(i[1] for i in items) / 1000.0
    com = sum(i[1] / 1000.0 * i[2].mean(0) for i in items) / M
    I = np.zeros((3, 3))
    for _, g, P in items:
        m = g / 1000.0
        d = (P - com) / 1000.0                       # m
        w = m / len(P)
        I += w * (np.sum(d * d) * np.eye(3) - d.T @ d)
    I += np.eye(3) * 1e-9
    return M, com / 1000.0, I


def hull_file(name, meshes, zcut=None):
    m = trimesh.util.concatenate(meshes)
    V = m.vertices
    if zcut is not None:
        lo, hi = zcut
        V = V[(V[:, 2] >= lo) & (V[:, 2] <= hi)]
    hm = trimesh.convex.convex_hull(V)
    if len(hm.vertices) > 300:                         # keep hulls light
        k = np.arange(600) + 0.5                       # support points in 600 Fibonacci directions
        ph = np.arccos(1 - 2 * k / 600); th = math.pi * (1 + 5 ** 0.5) * k
        D = np.c_[np.cos(th) * np.sin(ph), np.sin(th) * np.sin(ph), np.cos(ph)]
        hm = trimesh.convex.convex_hull(hm.vertices[np.unique(np.argmax(hm.vertices @ D.T, axis=0))])
    hm.apply_scale(0.001)
    f = os.path.join(MESHDIR, name + ".stl")
    hm.export(f)
    return name, hm


ASSETS = []
GEOMS = {k: [] for k in ITEMS}
_, hb = hull_file("body_hull", [geo("body__shell")]); ASSETS.append("body_hull")
GEOMS["body"].append(('<geom name="g_body" type="mesh" mesh="body_hull" class="pla"/>'))
_, hh = hull_file("head_hull", [geo("head__shell"), geo("head__visor"), geo("head__cap")]); ASSETS.append("head_hull")
GEOMS["head"].append(('<geom name="g_head" type="mesh" mesh="head_hull" class="pla"/>'))
for k in LEGS:
    hull_file(f"ball_{k}", [geo(f"haunch_{k}__ball")]); ASSETS.append(f"ball_{k}")
    GEOMS["haunch_" + k].append(f'<geom name="g_ball_{k}" type="mesh" mesh="ball_{k}" class="pla"/>')
    pm = geo(f"paw_{k}__paw")
    for i, (lo, hi) in enumerate([(-14, 9), (-32, -12), (-47.0, -30)]):
        hull_file(f"paw_{k}_{i}", [pm], (lo, hi)); ASSETS.append(f"paw_{k}_{i}")
        GEOMS["paw_" + k].append(f'<geom name="g_paw_{k}_{i}" type="mesh" mesh="paw_{k}_{i}" class="pla"/>')
    hull_file(f"sole_{k}", [geo(f"paw_{k}__sole")]); ASSETS.append(f"sole_{k}")
    GEOMS["paw_" + k].append(f'<geom name="g_sole_{k}" type="mesh" mesh="sole_{k}" class="tpu"/>')
    # site at the sole centre (for foot tracking)
    sv = geo(f"paw_{k}__sole").vertices
    c = sv.mean(0); c[2] = sv[:, 2].min()
    GEOMS["paw_" + k].append(f'<site name="foot_{k}" pos="{c[0]/1000:.5f} {c[1]/1000:.5f} {c[2]/1000:.5f}" size="0.002"/>')

# ---------------------------------------------------------------- servo model
MG = dict(tau=0.20, kp=2.0)      # N m, N m/rad  (torque saturates beyond ~5.7 deg error)
SG = dict(tau=0.15, kp=1.5)
VMAX = math.radians(600)         # no-load speed 0.10 s/60 deg
def damping(tau):                # joint damping so that free-running speed at stall torque ~= 600 deg/s
    return tau / VMAX
ARM = 3e-5                       # reflected rotor inertia (kg m^2), micro-servo class


def fmt(v):
    return " ".join(f"{x:.6g}" for x in v)


def body_xml(link, indent):
    sp = " " * indent
    par = PARENT.get(link)
    pos = (ORIG[link] - (ORIG[par] if par else 0)) / 1000.0 if par else np.zeros(3)
    M, com, I = inertial(ITEMS[link])
    out = [f'{sp}<body name="{link}" pos="{fmt(pos)}">']
    if link == "body":
        out.append(f'{sp}  <freejoint name="root"/>')
        out.append(f'{sp}  <site name="imu" pos="0 -0.008 {(9.5+CZ)/1000:.5f}" size="0.002"/>')
    else:
        jn = {"head": "head"}.get(link) or (("yaw_" if link.startswith("haunch") else "knee_") + link.split("_")[1])
        j = man["joints"][jn]
        servo = SG if jn == "head" else MG
        out.append(f'{sp}  <joint name="{jn}" axis="{fmt(j["axis"])}" range="{j["min"]} {j["max"]}" '
                   f'damping="{damping(servo["tau"]):.5f}" armature="{ARM}" frictionloss="0.002"/>')
    out.append(f'{sp}  <inertial pos="{fmt(com)}" mass="{M:.5f}" fullinertia="{I[0,0]:.4e} {I[1,1]:.4e} {I[2,2]:.4e} {I[0,1]:.4e} {I[0,2]:.4e} {I[1,2]:.4e}"/>')
    for g in GEOMS[link]:
        out.append(sp + "  " + g)
    for ch in [c for c, p in PARENT.items() if p == link]:
        out += body_xml(ch, indent + 2)
    out.append(f"{sp}</body>")
    return out


def build(mu):
    acts = []
    for jn, j in man["joints"].items():
        servo = SG if jn == "head" else MG
        acts.append(f'    <position name="a_{jn}" joint="{jn}" kp="{servo["kp"]}" forcelimited="true" '
                    f'forcerange="-{servo["tau"]} {servo["tau"]}" ctrlrange="{math.radians(j["min"]):.4f} {math.radians(j["max"]):.4f}"/>')
    tpu = mu * 1.5        # TPU sole: 0.9 on the nominal 0.6 desk, scaled with the desk
    xml = f"""<mujoco model="yumurcak">
  <!-- generated by build_mjcf.py from ../model.glb (frames identical to rig.js). Units: m, kg, s, rad. -->
  <compiler angle="degree" meshdir="meshes" autolimits="true"/>
  <option timestep="0.001" integrator="implicitfast" gravity="0 0 -9.81" cone="elliptic" impratio="2"/>
  <size memory="64M"/>
  <default>
    <geom solref="0.004 1" solimp="0.95 0.99 0.0005" condim="3"/>
    <default class="pla"><geom friction="{mu} 0.003 0.0001" rgba="0.94 0.9 0.83 1"/></default>
    <default class="tpu"><geom friction="{tpu:.3f} 0.005 0.0001" priority="1" condim="4" rgba="0.15 0.15 0.15 1"/></default>
  </default>
  <asset>
{chr(10).join(f'    <mesh name="{a}" file="{a}.stl"/>' for a in ASSETS)}
  </asset>
  <worldbody>
    <light pos="0 -0.3 0.6" dir="0 0.4 -1"/>
    <geom name="floor" type="plane" size="1 1 0.01" friction="{mu} 0.003 0.0001" rgba="0.8 0.8 0.78 1"/>
{chr(10).join(body_xml("body", 4))}
  </worldbody>
  <contact>
    <exclude body1="body" body2="head"/>
  </contact>
  <actuator>
{chr(10).join(acts)}
  </actuator>
  <sensor>
    <framequat name="imu_q" objtype="site" objname="imu"/>
    <gyro name="imu_gyro" site="imu"/>
  </sensor>
</mujoco>
"""
    f = os.path.join(HERE, f"yumurcak_mu{mu}.xml")
    open(f, "w").write(xml)
    return f


if __name__ == "__main__":
    mus = [float(a) for a in sys.argv[1:]] or [0.6, 0.4]
    tot = 0
    rep = {}
    for k, its in ITEMS.items():
        M, com, I = inertial(its)
        tot += M
        rep[k] = dict(mass_g=round(M * 1000, 2), com_link_mm=(com * 1000).round(2).tolist())
    # whole-robot CoM at rest
    comw = sum(rep[k]["mass_g"] * (np.array(rep[k]["com_link_mm"]) + ORIG[k]) for k in rep) / (tot * 1000)
    rep["_total_g"] = round(tot * 1000, 1)
    rep["_com_world_rest_mm"] = comw.round(2).tolist()
    rep["_com_concept_frame_mm"] = (comw - [0, 0, CZ]).round(2).tolist()
    json.dump(rep, open(os.path.join(HERE, "mass_model.json"), "w"), indent=1)
    print(json.dumps({k: rep[k] for k in rep if k.startswith("_")}))
    for mu in mus:
        print("wrote", build(mu))
