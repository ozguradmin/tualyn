#!/usr/bin/env python3
"""Arm-vs-shell interference sweep (the check MuJoCo cannot do: body<->leg contact is excluded there).

For every hip joint the posed arm mesh (arm + boot + inboard N20 boot sleeve, exactly as in model.glb) is tested
against points sampled on the egg's visible skin (cream lower body, caramel cap, visor) with a winding-number
point-in-mesh test.  The result is the max depth (mm) by which the shell enters the arm at each angle.
usage: python3 -I check_arm_shell.py [step_deg] [hip_fl,hip_rl,...]  -> results/arm_shell_sweep.json
The clear range per joint is what manifest.joints min/max must stay inside (verify_replay.py checks every clip frame
against this table).
"""
import json, math, os, sys
import numpy as np
import trimesh
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
STEP = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
sc = trimesh.load(os.path.join(PKG, "model.glb")); g = sc.graph
man = json.load(open(os.path.join(PKG, "manifest.json")))

def mesh(n):
    T, gn = g[n]; m = sc.geometry[gn].copy(); m.apply_transform(T); return m   # world (rest) frame

def winding(tri, pts, chunk=150):
    w = np.zeros(len(pts))
    for k in range(0, len(pts), chunk):
        P = pts[k:k + chunk][:, None, :]
        a = tri[None, :, 0, :] - P; b = tri[None, :, 1, :] - P; c = tri[None, :, 2, :] - P
        la = np.linalg.norm(a, axis=2); lb = np.linalg.norm(b, axis=2); lc = np.linalg.norm(c, axis=2)
        det = np.einsum('ijk,ijk->ij', a, np.cross(b, c))
        den = la * lb * lc + np.einsum('ijk,ijk->ij', a, b) * lc + np.einsum('ijk,ijk->ij', b, c) * la + np.einsum('ijk,ijk->ij', c, a) * lb
        w[k:k + chunk] = np.arctan2(det, den).sum(1) / (2 * np.pi)
    return w

body = trimesh.util.concatenate([mesh("body__cream"), mesh("body__visor"), mesh("body__cap")])
np.random.seed(1)
BP, _ = trimesh.sample.sample_surface_even(body, 150000, seed=1)

def depth_at(leg, axis, ang, arm0, AP0):
    T = g[leg][0]
    R = trimesh.transformations.rotation_matrix(math.radians(ang), axis, point=T[:3, 3])
    arm = arm0.copy(); arm.apply_transform(R)
    lo, hi = arm.bounds
    pts = BP[np.all((BP > lo - 0.1) & (BP < hi + 0.1), axis=1)]
    if len(pts) == 0:
        return 0.0
    ins = pts[winding(arm.triangles, pts) > 0.5]
    if len(ins) == 0:
        return 0.0
    AP = trimesh.transform_points(AP0, R)
    d, _ = cKDTree(AP).query(ins)
    return float(d.max())

res = {}
JOINTS = sys.argv[2].split(",") if len(sys.argv) > 2 else ["hip_fl", "hip_fr", "hip_rl", "hip_rr"]
for j in JOINTS:
    jd = man["joints"][j]; leg = jd["node"]; axis = np.array(jd["axis"], float)
    arm0 = mesh(leg + "__arm")
    AP0, _ = trimesh.sample.sample_surface_even(arm0, 150000, seed=2)
    front = j[4] == "f"
    # 1-degree steps where the arm comes near the shell (both ends of the sweep), 10-degree steps in between
    if front:
        angs = list(np.arange(-6, 10 + 1e-6, STEP)) + list(np.arange(20, 70, 10)) + list(np.arange(74, 90 + 1e-6, STEP))
    else:
        angs = list(np.arange(-12, 12 + 1e-6, STEP)) + list(np.arange(20, 110, 10)) + list(np.arange(110, 124 + 1e-6, STEP))
    angs = np.array(sorted(set([round(float(a), 2) for a in angs] + [22.0, float(jd["min"]), float(jd["max"])])))
    tab = []
    for a in angs:
        tab.append([round(float(a), 2), round(depth_at(leg, axis, a, arm0, AP0), 2)])
    clear = [a for a, d in tab if d <= 0.0]
    # largest contiguous clear interval containing the stand angle 22
    lo = hi = 22.0
    angs_l = [a for a, _ in tab]; dd = dict((a, d) for a, d in tab)
    for a in sorted([x for x in angs_l if x <= 22], reverse=True):
        if dd[a] > 0: break
        lo = a
    for a in sorted([x for x in angs_l if x >= 22]):
        if dd[a] > 0: break
        hi = a
    res[j] = {"table_deg_depth_mm": tab, "clear_range_deg": [lo, hi], "manifest_range_deg": [jd["min"], jd["max"]],
              "manifest_inside_clear": bool(jd["min"] >= lo and jd["max"] <= hi)}
    print(j, "clear", lo, "..", hi, "manifest", jd["min"], jd["max"], "worst", max(d for _, d in tab), flush=True)
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
outp = os.path.join(HERE, "results", "arm_shell_sweep.json")
old = json.load(open(outp)) if os.path.exists(outp) else {}
old.update(res)
# the CAD is mirror-symmetric in X (build_rig.py builds every leg from the same solids with sx = +-1), so a side that
# was not swept takes its mirror's table
for jr, jl in (("hip_fr", "hip_fl"), ("hip_rr", "hip_rl")):
    if jr not in res and jl in old:
        old[jr] = dict(old[jl]); old[jr]["mirrored_from"] = jl
        old[jr]["manifest_range_deg"] = [man["joints"][jr]["min"], man["joints"][jr]["max"]]
for j, v in old.items():      # re-evaluate against the current manifest
    v["manifest_range_deg"] = [man["joints"][j]["min"], man["joints"][j]["max"]]
    v["manifest_inside_clear"] = bool(v["manifest_range_deg"][0] >= v["clear_range_deg"][0] and v["manifest_range_deg"][1] <= v["clear_range_deg"][1])
json.dump(old, open(outp, "w"), indent=0)
