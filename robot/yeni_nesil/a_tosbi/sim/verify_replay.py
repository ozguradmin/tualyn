#!/usr/bin/env python3
"""Replay every anim/*.json the way rig.js does (node = offset * axisAngle(axis, angle), root = base pose) on the REAL
GLB meshes and check per frame: lowest visible point vs the floor (penetration / floating), and with MuJoCo:
link-vs-link interpenetration (limbs through body). Writes out/replay_check.json."""
import json, math, os, sys
import numpy as np, trimesh, mujoco
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tosbi import Sim, JN, MAN, PKG

scene = trimesh.load(os.path.join(PKG, "model.glb")); G = scene.graph
PARENT = {"body": None, "head": "body"}
for l in ("fl", "fr", "rl", "rr"): PARENT[f"leg_{l}"] = "body"; PARENT[f"foot_{l}"] = f"leg_{l}"
OFF = {n: (G.get(n)[0] if PARENT[n] is None else np.linalg.inv(G.get(PARENT[n])[0]) @ G.get(n)[0]) for n in PARENT}
JOINT_OF = {v["node"]: (k, np.array(v["axis"], float) / np.linalg.norm(v["axis"])) for k, v in MAN["joints"].items()}
VIS = {}
for nm in G.nodes_geometry:
    link, mat = nm.split("__")
    if mat.startswith("internal"): continue
    V = scene.geometry[nm].vertices
    VIS.setdefault(link, []).append(V[:: max(1, len(V) // 1500)])
VIS = {k: np.vstack(v) for k, v in VIS.items()}

def rot(axis, deg):
    return trimesh.transformations.rotation_matrix(math.radians(deg), axis)

def quat_mat(q):
    M = np.eye(4); r = np.zeros(9); mujoco.mju_quat2Mat(r, np.asarray(q, float)); M[:3, :3] = r.reshape(3, 3); return M

def world_T(base, joints):
    Tb = quat_mat(base[3:]); Tb[:3, 3] = base[:3]
    T = {}
    for n in ("body", "head", "leg_fl", "leg_fr", "leg_rl", "leg_rr", "foot_fl", "foot_fr", "foot_rl", "foot_rr"):
        P = Tb if PARENT[n] is None else T[PARENT[n]]
        L = OFF[n].copy()
        if n in JOINT_OF:
            jn, ax = JOINT_OF[n]; j = MAN["joints"][jn]
            ang = min(j["max"], max(j["min"], joints[jn]))          # rig.js clamps to the manifest range
            L = L @ rot(ax, ang - j.get("zero", 0))
        T[n] = P @ L
    return T

def check(name, clip):
    n = clip["frames"]; base = clip["base"] if "base" in clip else [[0, 0, 0, 1, 0, 0, 0]] * n
    s = Sim(0.6); m, d = s.m, s.d
    zmins, selfpen, worst_pair = [], [], None
    for i in range(n):
        J = {j: clip["joints"][j][i] for j in JN if j in clip["joints"]}
        T = world_T(base[i], J)
        zmin = min(((VIS[l] @ T[l][:3, :3].T) + T[l][:3, 3])[:, 2].min() for l in VIS)
        zmins.append(zmin)
        d.qpos[0:3] = np.array(base[i][:3]) / 1000; d.qpos[3:7] = base[i][3:]
        for j in JN: d.qpos[s.qadr[j]] = math.radians(J.get(j, 0))
        mujoco.mj_forward(m, d)
        w = 0.0
        for k in range(d.ncon):
            c = d.contact[k]
            if m.geom_bodyid[c.geom1] == 0 or m.geom_bodyid[c.geom2] == 0: continue
            if c.dist < w: w = c.dist; worst_pair = (m.geom(c.geom1).name, m.geom(c.geom2).name, i)
        selfpen.append(-w * 1000)
    z = np.array(zmins)
    return {"frames": n, "floor_min_mm": round(float(z.min()), 2), "floor_max_lowest_point_mm": round(float(z.max()), 2),
            "frames_floating_gt_2mm": int((z > 2.0).sum()), "frames_penetrating_gt_1mm": int((z < -1.0).sum()),
            "max_link_interpenetration_mm(hulls)": round(max(selfpen), 2), "worst_pair": worst_pair,
            "z_lowest_per_frame": [round(float(v), 1) for v in z]}

if __name__ == "__main__":
    out = {}
    for f in sorted(os.listdir(os.path.join(PKG, "anim"))):
        nm = f[:-5]; clip = json.load(open(os.path.join(PKG, "anim", f)))
        r = check(nm, clip); out[nm] = r
        print(nm, {k: v for k, v in r.items() if k != "z_lowest_per_frame"}, flush=True)
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "replay_check.json"), "w"))
