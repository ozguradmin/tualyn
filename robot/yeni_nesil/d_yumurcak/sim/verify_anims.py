#!/usr/bin/env python3
"""Replay every anim/*.json through the GLB exactly like rig.js (node.quaternion = rest * axisAngle(axis, angle-zero),
root = base pose) and check, per frame:
  * lowest visible vertex z (floating > +0.5 mm while 'standing', or ground penetration < -0.5 mm)
  * paw / knuckle vertices inside the egg shell or inside another hip ball (rig checker, src/check_limits.py)
  * the three.js Box3.setFromObject radius (for fixed-camera strips)
-> out/verify_anims.json"""
import json, math, os, sys, io, contextlib, runpy
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
man = json.load(open(os.path.join(PKG, "manifest.json")))
info = json.load(open(os.path.join(PKG, "src", "rig_info.json")))
with contextlib.redirect_stdout(io.StringIO()):
    CL = runpy.run_path(os.path.join(PKG, "src", "check_limits.py"))
inside_egg, ball_pen = CL["inside_egg"], CL["ball_pen"]
CZ = info["CZ"]
sc = trimesh.load(os.path.join(PKG, "model.glb"))
g = sc.graph
LINKS = ["body"] + list(info["parents"].keys())
ORIG = {k: np.array(v) for k, v in info["origins"].items()}
JN = {v["node"]: (k, np.array(v["axis"], float), v.get("zero", 0)) for k, v in man["joints"].items()}
MESH = {}                    # link -> list of (verts_local, is_internal, aabb corners local)
for n in g.nodes_geometry:
    T, gname = g[n]
    link, mat = n.split("__", 1)
    Lw = np.eye(4) if link == "body" else g.get(link)[0]
    M = np.linalg.inv(Lw) @ T
    V = trimesh.transform_points(sc.geometry[gname].vertices, M)
    lo, hi = sc.geometry[gname].bounds
    C = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    C = trimesh.transform_points(C, M)       # three: local AABB of the geometry, corners -> world
    internal = mat.startswith("internal") or man["materials"].get(mat, {}).get("type") == "internal"
    MESH.setdefault(link, []).append((V[::2] if len(V) > 4000 else V, internal, C, mat))


def qmat(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def fk(anim, i):
    T = {}
    b = anim.get("base")
    B = np.eye(4)
    if b:
        B[:3, :3] = qmat(b[i][3:]); B[:3, 3] = b[i][:3]
    T["body"] = B
    for link in LINKS[1:]:
        par = info["parents"][link]
        jn, ax, zero = JN[link]
        ang = anim["joints"][jn][i] if jn in anim["joints"] else man["pose_rest"].get(jn, 0)
        R = trimesh.transformations.rotation_matrix(math.radians(ang - zero), ax)
        L = np.eye(4); L[:3, 3] = ORIG[link] - ORIG[par]
        T[link] = None, (par, L @ R)
    out = {"body": B}
    for link in LINKS[1:]:
        par, M = T[link][1]
        out[link] = out[par] @ M
    return out


def check(name, anim, every=1):
    n = anim["frames"]
    zmin, pen_egg, pen_ball, rads = [], [], [], []
    for i in range(0, n, every):
        W = fk(anim, i)
        zl, corners = 1e9, []
        for link, lst in MESH.items():
            for V, internal, C, mat in lst:
                corners.append(trimesh.transform_points(C, W[link]))
                if not internal:
                    zl = min(zl, trimesh.transform_points(V, W[link])[:, 2].min())
        Cc = np.vstack(corners); size = Cc.max(0) - Cc.min(0)
        rads.append(max(0.06, np.linalg.norm(size) / 2000.0))
        zmin.append(zl)
        # paws in the body frame vs egg and other balls
        Binv = np.linalg.inv(W["body"])
        pe, pb = -9.0, -9.0
        for k in ("fl", "fr", "bl", "br"):
            Pb = np.vstack([trimesh.transform_points(V, Binv @ W[f"paw_{k}"]) for V, internal, C, mat in MESH[f"paw_{k}"] if mat in ("paw", "sole")])
            Pc = Pb.copy(); Pc[:, 2] -= CZ
            pe = max(pe, float(inside_egg(Pc).max()))
            for k2 in ("fl", "fr", "bl", "br"):
                if k2 == k:
                    continue
                Th = Binv @ W[f"haunch_{k2}"]
                pb = max(pb, float(ball_pen(Pb, k2, Th).max()))
        pen_egg.append(pe); pen_ball.append(pb)
    zmin = np.array(zmin)
    return dict(frames=n, zmin_min=round(float(zmin.min()), 2), zmin_max=round(float(zmin.max()), 2),
                frames_below_minus0_5mm=int((zmin < -0.5).sum()), paw_in_egg_max_mm=round(max(pen_egg), 2),
                paw_in_other_ball_max_mm=round(max(pen_ball), 2), zmin=[round(float(z), 2) for z in zmin], rad_m=[round(r, 5) for r in rads])


if __name__ == "__main__":
    res = {}
    for k, f in man["animations"].items():
        a = json.load(open(os.path.join(PKG, f)))
        r = check(k, a)
        res[k] = r
        print(k, {kk: v for kk, v in r.items() if kk not in ("zmin", "rad_m")})
    json.dump(res, open(os.path.join(HERE, "out", "verify_anims.json"), "w"))
