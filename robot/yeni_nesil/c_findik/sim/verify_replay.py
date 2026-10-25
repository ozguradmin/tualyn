#!/usr/bin/env python3
"""Independent replay check of anim/*.json against model.glb using the rig.js convention
(node.quaternion = rest * axisAngle(axis, angle - zero); base = world pose of the root node).
It does NOT run MuJoCo: it re-does the forward kinematics from the GLB itself.  Separately it PARSES findik_base.xml and
asserts that every MJCF body position, hinge axis and range equals the GLB node transform / manifest joint (mjcf_vs_glb),
so the 1:1 replay claim is checked, not assumed.  Per clip it reports:
  min_z_mm         lowest visible vertex over all frames (negative = sinks into the desk)
  max_gap_mm       worst 'floating' gap = max over frames of the lowest visible vertex (should be ~0 unless airborne)
  tyre_in_egg      max depth (mm) any tyre/hub vertex reaches inside the egg's convex hull (limbs through body)
  tyre_tyre_mm     min distance between front and rear tyre centres on one side minus 2 r (negative = tyres overlap)
  arm_in_shell_mm  max depth by which the egg skin (cream/cap/visor) enters a posed arm (arm + boot + N20 sleeve), looked
                   up per frame from the winding-number sweep in results/arm_shell_sweep.json (check_arm_shell.py);
                   MuJoCo cannot see this (body<->leg contact is excluded there), so this is the only guard
usage: python3 -I verify_replay.py  -> results/replay_check.json
"""
import json, math, os
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation as Rot
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
man = json.load(open(os.path.join(PKG, "manifest.json")))
sc = trimesh.load(os.path.join(PKG, "model.glb"))
W = lambda n: sc.graph.get(n)[0]
links = ["body", "leg_fl", "leg_fr", "leg_rl", "leg_rr", "wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"]
parent = {"leg_fl": "body", "leg_fr": "body", "leg_rl": "body", "leg_rr": "body",
          "wheel_fl": "leg_fl", "wheel_fr": "leg_fr", "wheel_rl": "leg_rl", "wheel_rr": "leg_rr"}
Tloc = {l: np.linalg.inv(W(p)) @ W(l) for l, p in parent.items()}
jn_of = {v["node"]: (k, np.array(v["axis"], float), v.get("zero", 0), v) for k, v in man["joints"].items()}
mats = man["materials"]
pts = {l: [] for l in links}
for n in sc.graph.nodes_geometry:
    link, mk = n.split("__", 1)
    if mats.get(mk, {}).get("type") == "internal" or mk.startswith("internal"):
        continue
    T, g = sc.graph.get(n)
    v = trimesh.transform_points(sc.geometry[g].vertices[::3], np.linalg.inv(W(link)) @ T)
    pts[link].append(v)
pts = {l: np.vstack(v) for l, v in pts.items() if v}
egg = trimesh.util.concatenate([sc.geometry[sc.graph.get(k)[1]] for k in ("body__cream", "body__cap", "body__visor", "body__nose")])
egg_v = trimesh.transform_points(egg.vertices, np.linalg.inv(W("body")) @ sc.graph.get("body__cream")[0])
H = trimesh.PointCloud(egg_v[::30]).convex_hull          # subsampled hull (a hair smaller than the true hull)
Aeq = H.face_normals; beq = np.einsum("ij,ij->i", H.face_normals, H.triangles[:, 0])
limb = {l: np.vstack([trimesh.transform_points(sc.geometry[sc.graph.get(f"{l}__{m}")[1]].vertices[::6],
                      np.linalg.inv(W(l)) @ sc.graph.get(f"{l}__{m}")[0]) for m in ("tyre", "hub")])
        for l in ("wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr")}

def rot(axis, deg):
    R = np.eye(4); R[:3, :3] = Rot.from_rotvec(axis / np.linalg.norm(axis) * math.radians(deg)).as_matrix(); return R

def fk(a, i):
    b = a["base"][i] if a.get("base") else [0, 0, 0, 1, 0, 0, 0]
    Tb = np.eye(4); Tb[:3, :3] = Rot.from_quat([b[4], b[5], b[6], b[3]]).as_matrix(); Tb[:3, 3] = b[:3]
    out = {"body": Tb}
    for l in links[1:]:
        k, ax, z, jd = jn_of[l]
        deg = a["joints"].get(k, [man["pose_rest"].get(k, 0)] * (i + 1))[i]
        if not jd.get("continuous"):
            deg = max(jd["min"], min(jd["max"], deg))
        out[l] = out[parent[l]] @ Tloc[l] @ rot(ax, deg - z)
    return out

# ---------------------------------------------------------------- MJCF <-> GLB frame check
import xml.etree.ElementTree as ET
X = ET.parse(os.path.join(HERE, "findik_base.xml")).getroot()
xb = {b.get("name"): b for b in X.iter("body")}
mj = {"checked": [], "max_pos_err_mm": 0.0, "max_axis_err": 0.0, "range_ok": True}
for l in links[1:]:
    b = xb[l]
    p_mj = np.array([float(v) for v in b.get("pos").split()]) * 1000.0
    p_glb = Tloc[l][:3, 3]
    jn = b.find("joint")
    ax_mj = np.array([float(v) for v in jn.get("axis").split()])
    k, ax, z, jd = jn_of[l]
    e_p = float(np.abs(p_mj - p_glb).max()); e_a = float(np.abs(ax_mj / np.linalg.norm(ax_mj) - ax / np.linalg.norm(ax)).max())
    mj["max_pos_err_mm"] = max(mj["max_pos_err_mm"], round(e_p, 4)); mj["max_axis_err"] = max(mj["max_axis_err"], round(e_a, 6))
    assert np.allclose(Tloc[l][:3, :3], np.eye(3), atol=1e-6), l + " GLB rest rotation is not identity"
    if jn.get("range"):
        lo, hi = (float(v) for v in jn.get("range").split())
        mj["range_ok"] &= (lo == jd["min"] and hi == jd["max"])
    mj["checked"].append(l)
mass = sum(float(i.get("mass")) for i in X.iter("inertial")) * 1000
mj["mass_sum_g"] = round(mass, 2)
assert mj["max_pos_err_mm"] < 0.01 and mj["max_axis_err"] < 1e-6 and mj["range_ok"], mj
print("mjcf_vs_glb", mj, flush=True)

SW = json.load(open(os.path.join(HERE, "results", "arm_shell_sweep.json")))
def arm_depth(j, deg):
    t = np.array(SW[j]["table_deg_depth_mm"]); return float(np.interp(deg, t[:, 0], t[:, 1]))

res = {"_mjcf_vs_glb": mj, "_arm_shell_clear_range_deg": {j: v["clear_range_deg"] for j, v in SW.items()}}
for clip, f in man["animations"].items():
    a = json.load(open(os.path.join(PKG, f)))
    n = a["frames"]; minz = 1e9; gaps = []; inside = 0.0; tt = 1e9; worst_gap_frame = None
    arm_in = {}; hip_range = {}
    for j in ("hip_fl", "hip_fr", "hip_rl", "hip_rr"):
        v = np.array(a["joints"].get(j, [man["pose_rest"][j]]))
        hip_range[j] = [round(float(v.min()), 2), round(float(v.max()), 2)]
        arm_in[j] = round(max(arm_depth(j, x) for x in v), 2)
    for i in range(n):
        T = fk(a, i)
        lo = min(trimesh.transform_points(p, T[l])[:, 2].min() for l, p in pts.items())
        minz = min(minz, lo); gaps.append(lo)
        Binv = np.linalg.inv(T["body"])
        for l, p in (limb.items() if i % 2 == 0 else ()):
            q = trimesh.transform_points(p, Binv @ T[l])
            d = (q @ Aeq.T - beq).max(axis=1)        # <0 inside hull
            inside = max(inside, -d.min())
        for s in ("l", "r"):
            c1 = T["wheel_f" + s][:3, 3]; c2 = T["wheel_r" + s][:3, 3]
            tt = min(tt, np.linalg.norm(c1 - c2) - 30.0)
    g = np.array(gaps)
    res[clip] = {"frames": n, "min_z_mm": round(float(minz), 2), "max_gap_mm": round(float(g.max()), 2),
                 "frames_gap_over_1mm": int((g > 1.0).sum()), "frames_below_minus_1p2mm": int((g < -1.2).sum()),
                 "tyre_hub_in_egg_hull_mm": round(float(inside), 2), "tyre_tyre_clearance_mm": round(float(tt), 2),
                 "arm_in_shell_mm": max(arm_in.values()), "hip_range_deg": hip_range}
    print(clip, res[clip], flush=True)
json.dump(res, open(os.path.join(HERE, "results", "replay_check.json"), "w"), indent=1)
