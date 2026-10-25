#!/usr/bin/env python3
"""Sweep each leg joint and report penetration of the paw/knuckle into the egg body, the other haunch balls
and the other paws. Uses the GLB meshes (link frames) + the manifest joint axes, i.e. exactly the rig.
Egg body volume is analytic (concept profile), minus the 4 haunch cut-outs.  -> limits.json (suggested)"""
import json, math, os, sys
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.argv = [sys.argv[0]]
R, ZS, TOP = 48.0, 18.0, 58.0
_r0 = math.sqrt(R * R - ZS * ZS); _H = TOP - ZS; _u = _H * _H / ((_r0 * _r0 / ZS) - 2 * _H)
B2 = _u + _H; ZC2 = TOP - B2; A2 = math.sqrt(B2 * B2 * ZS / _u)
RT, BZ, FLAT = 20.5, -36.0, 17.5
info = json.load(open(os.path.join(HERE, "rig_info.json")))
man = json.load(open(os.path.join(PKG, "manifest.json")))
CZ = info["CZ"]
sc = trimesh.load(os.path.join(PKG, "model.glb"))
G = {n: g for n, g in sc.geometry.items()}
LEGS = {"fr": (-24.0, -24.0), "fl": (24.0, -24.0), "br": (-24.0, 24.0), "bl": (24.0, 24.0)}


def egg_r(z):
    if z <= ZS:
        return np.sqrt(np.maximum(R * R - z * z, 0))
    return A2 * np.sqrt(np.maximum(1 - ((z - ZC2) / B2) ** 2, 0))


def inside_egg(P):          # P in concept frame C; depth (mm) inside the egg minus haunch cut spheres
    z = P[:, 2]
    rr = np.hypot(P[:, 0], P[:, 1])
    er = np.where(z <= ZS, np.sqrt(np.maximum(R * R - z * z, 0)), A2 * np.sqrt(np.maximum(1 - ((z - ZC2) / B2) ** 2, 0)))
    d = er - rr
    d[(z < -R) | (z > TOP)] = -1
    for (x, y) in LEGS.values():
        inball = np.linalg.norm(P - [x, y, BZ], axis=1) < RT + 0.7
        d[inball] = -1
    return d


def rot(axis, deg):
    return trimesh.transformations.rotation_matrix(math.radians(deg), axis)


def leg_world(k, yaw, knee):
    """returns paw vertices in concept frame C and the yaw rotation (about the haunch axis)"""
    j_y, j_k = man["joints"][f"yaw_{k}"], man["joints"][f"knee_{k}"]
    oh = np.array(info["origins"][f"haunch_{k}"]); op = np.array(info["origins"][f"paw_{k}"])
    Th = trimesh.transformations.translation_matrix(oh) @ rot(j_y["axis"], yaw)
    Tp = Th @ trimesh.transformations.translation_matrix(op - oh) @ rot(j_k["axis"], knee)
    V = []
    for mat in ("paw", "sole"):
        g = G[f"paw_{k}__{mat}"]
        V.append(trimesh.transform_points(g.vertices, Tp))
    V = np.vstack(V)
    V[:, 2] -= CZ
    return V, Th


def ball_pen(Pw, k, Th):
    """penetration into ball k (sphere RT with flats |y_local|<=FLAT), Pw in world coords"""
    Pl = trimesh.transform_points(Pw, np.linalg.inv(Th))
    d = RT - np.linalg.norm(Pl, axis=1)
    d = np.minimum(d, FLAT - np.abs(Pl[:, 1]))
    return d


def report(k, yaw, knee, others=None):
    V, Th = leg_world(k, yaw, knee)
    e = inside_egg(V).max()
    Vw = V.copy(); Vw[:, 2] += CZ
    b = ball_pen(Vw, k, Th).max()
    ob = -9
    for k2, (x, y) in LEGS.items():
        if k2 == k:
            continue
        T2 = trimesh.transformations.translation_matrix(info["origins"][f"haunch_{k2}"])
        ob = max(ob, ball_pen(Vw, k2, T2).max())
    return round(float(e), 2), round(float(b), 2), round(float(ob), 2), round(float(Vw[:, 2].min()), 1)


out = {}
k = "fl"
print("knee sweep (yaw 0): knee, egg_pen, own_ball_pen, other_ball_pen, min z")
for kn in range(-40, 181, 10):
    print(kn, report(k, 0, kn))
for kn in (0, 30, 90, 178):
    print(f"yaw sweep at knee {kn}")
    for yw in range(-90, 91, 10):
        print("  ", yw, report(k, yw, kn))

if "--fine" in os.environ.get("CL", ""):
    pass
print("fine knee at yaw 0:", [(kn, report("fl", 0, kn)[0]) for kn in range(155, 181, 2)])
print("fine yaw at knee 30:", [(yw, report("fl", yw, 30)[0]) for yw in range(-30, -14, 2)])
print("fine yaw at knee 90:", [(yw, report("fl", yw, 90)[2]) for yw in range(60, 91, 4)])
V, Th = leg_world("fl", 0, 178)
d = inside_egg(V); i = d.argmax(); print("worst point @178 (C frame):", V[i].round(1), d[i].round(2))
for kk in LEGS:
    print(kk, "knee165", report(kk, 0, 165), "yaw-20", report(kk, -20, 30), "yaw85", report(kk, 85, 30))
