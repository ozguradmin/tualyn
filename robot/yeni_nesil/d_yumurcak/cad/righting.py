#!/usr/bin/env python3
"""Quasi-static self-righting analysis for Yumurcak (convex-hull rolling model).

A rigid convex body on a flat desk rests where its support function
    h(d) = max_v (v - c) . d        (d = body-frame unit vector pointing at the desk, c = CoM)
has a local minimum; potential energy is m g h(d).  We
  1. list every stable rest of the robot with legs TUCKED (egg mode) and STANDING,
  2. find the energy barrier from each non-upright rest back to upright,
  3. simulate the righting manoeuvre: from the rest, the two down-side legs yaw so their
     paw plane contains the fall direction and the knees sweep the paws into the desk;
     after every 5 deg step the body rolls (steepest descent of h) to the new rest.
     Success = the descent ends in the upright basin. Knee torque is estimated at every
     step from the paw contact lever.
Inputs: stl_stand/*.stl (exterior, world frame), stl_stand/_paw_local.stl, check.json.
Output: righting.json
"""
import json, math, os
import numpy as np
import trimesh
from scipy.spatial import cKDTree

P = json.load(open("stl_stand/parts.json"))
CZ = P["CZ"]
MASS = json.load(open("check.json"))["mass"]
M = MASS["total_g"]
COM0 = np.array(MASS["com_body"]) + [0, 0, float(os.environ.get("COMDZ", "0"))]
YAW = [(-24.0, -24.0), (24.0, -24.0), (-24.0, 24.0), (24.0, 24.0)]
NAMES = ["FR", "FL", "BR", "BL"]
KNEE_Z, FLAT = -30.5, 17.5
PAW_G = 5.8

static = []
for k in ("body_shell", "head_shell", "visor", "haunch") + (() if os.environ.get("NOCAP") else ("cap",)):
    m = trimesh.load(f"stl_stand/{k}.stl")
    static.append(m.vertices)
S = np.vstack(static) - [0, 0, CZ]
S = trimesh.convex.convex_hull(S).vertices
paw = trimesh.load("stl_stand/_paw_local.stl")
import os
PAW_L = float(os.environ.get("PAW_L", "48"))
PAWV = paw.convex_hull.vertices.copy()
PAWC = paw.center_mass.copy()
PAWV[:, 2] = np.where(PAWV[:, 2] < -6, -6 + (PAWV[:, 2] + 6) * ((PAW_L - 6) / 42.0), PAWV[:, 2])
PAWC[2] = -6 + (PAWC[2] + 6) * ((PAW_L - 6) / 42.0)
TUCK = float(os.environ.get("TUCK", "178"))


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def leg_pts(i, beta, yaw):
    x, y = YAW[i]
    sx = -1 if x < 0 else 1
    sy = -1 if y < 0 else 1
    R1 = ry(math.radians(-sx * beta)) @ np.diag([sx, 1.0, 1.0])
    t = np.array([x, y + sy * (FLAT + 6.8), KNEE_Z])
    v = PAWV @ R1.T + t
    c = R1 @ PAWC + t
    piv = np.array([x, y, 0.0])
    R2 = rz(math.radians(yaw))
    knee = R2 @ (np.array([x, y + sy * (FLAT + 6.8), KNEE_Z]) - piv) + piv
    kax = R2 @ np.array([0, 1.0, 0])
    return (v - piv) @ R2.T + piv, R2 @ (c - piv) + piv, knee, kax


def config(betas, yaws):
    pts = []
    com = COM0 * M
    paws = []
    for i in range(4):
        v, c, knee, kax = leg_pts(i, betas[i], yaws[i])
        c0 = leg_pts(i, 30, 0)[1]
        com = com + PAW_G * (c - c0)
        pts.append(v)
        paws.append((v, knee, kax))
    return np.vstack(pts), com / M, paws


# sphere grid
N = 14000
k = np.arange(N) + 0.5
phi = np.arccos(1 - 2 * k / N)
th = math.pi * (1 + 5 ** 0.5) * k
D = np.c_[np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)]
TREE = cKDTree(D)
NB = TREE.query(D, k=9)[1][:, 1:]
DOWN = np.array([0, 0, -1.0])
HS = (S @ D.T).max(axis=0)          # static support, computed once


def hfun(pts, com):
    return np.maximum(HS, (pts @ D.T).max(axis=0)) - D @ com


def minima(h):
    return np.where(h <= h[NB].min(axis=1))[0]


def descend(h, i):
    while True:
        j = NB[i][np.argmin(h[NB[i]])]
        if h[j] >= h[i]:
            return i
        i = j


def ang(d):
    return math.degrees(math.acos(np.clip(np.dot(d, DOWN), -1, 1)))


def barriers(h, upi):
    """merge-tree: for every node, the lowest h level at which it connects to the upright node"""
    order = np.argsort(h)
    parent = np.arange(N)
    done = np.zeros(N, bool)
    join = np.full(N, np.inf)
    members = {}
    hasup = {}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in order:
        done[i] = True
        members[i] = [i]
        hasup[i] = (i == upi)
        if i == upi:
            join[i] = h[i]
        for j in NB[i]:
            if not done[j]:
                continue
            ri, rj = find(i), find(j)
            if ri == rj:
                continue
            if hasup[ri] != hasup[rj]:
                other = rj if hasup[ri] else ri
                for m in members[other]:
                    join[m] = h[i]
            if len(members[ri]) < len(members[rj]):
                ri, rj = rj, ri
            parent[rj] = ri
            members[ri] += members.pop(rj)
            hasup[ri] = hasup[ri] or hasup.pop(rj)
    return join


def rest_report(name, betas, yaws):
    pts, com, _ = config(betas, yaws)
    h = hfun(pts, com)
    up = int(np.argmax(D @ DOWN))
    upi = descend(h, up)
    out = []
    J = barriers(h, upi)
    for i in minima(h):
        b = J[i]
        out.append(dict(tilt_deg=round(ang(D[i]), 1), dir=[round(x, 2) for x in D[i]], h_mm=round(float(h[i]), 2),
                        barrier_mm=round(float(b - h[i]), 2), barrier_mJ=round(float((b - h[i]) * M * 9.81e-3), 1)))
    out.sort(key=lambda r: r["tilt_deg"])
    # merge near-duplicates
    merged = []
    for r in out:
        if not any(abs(r["tilt_deg"] - q["tilt_deg"]) < 2 and np.dot(r["dir"], q["dir"]) > 0.995 for q in merged):
            merged.append(r)
    return dict(pose=name, com=[round(x, 2) for x in com], rests=merged)


def manoeuvre(start_dir, tuck=None):
    tuck = TUCK if tuck is None else tuck
    """from the rest reached after a fall towards start_dir (body frame), push with down-side legs"""
    betas = [tuck] * 4
    yaws = [0.0] * 4
    pts, com, _ = config(betas, yaws)
    h = hfun(pts, com)
    i = descend(h, int(np.argmax(D @ start_dir)))
    log = [dict(step="fallen, legs tucked", tilt=round(ang(D[i]), 1))]
    d = D[i]
    horiz = np.array([d[0], d[1], 0.0])
    horiz /= np.linalg.norm(horiz) + 1e-9
    # legs on the down side: those whose (x,y) has positive dot with horiz
    scores = [np.dot(np.array(YAW[j]) / 33.9, horiz[:2]) for j in range(4)]
    order = np.argsort(scores)[::-1]
    pushers = [j for j in order[:2]]
    # yaw each pusher so its paw-swing plane (local XZ, outward = sx*X) contains horiz
    for j in pushers:
        sx = -1 if YAW[j][0] < 0 else 1
        out_dir = math.degrees(math.atan2(0, sx))           # outward direction of paw swing at yaw 0
        want = math.degrees(math.atan2(horiz[1], horiz[0]))
        y = (want - out_dir + 540) % 360 - 180
        yaws[j] = float(np.clip(y, -85, 85))
    pts, com, _ = config(betas, yaws)
    h = hfun(pts, com)
    i = descend(h, i)
    log.append(dict(step=f"yaw pushers {[NAMES[j] for j in pushers]} to {[round(yaws[j]) for j in pushers]}", tilt=round(ang(D[i]), 1)))
    max_tau = 0.0
    for b in np.arange(tuck, -1, -5.0):
        for j in pushers:
            betas[j] = float(b)
        pts, com, paws = config(betas, yaws)
        h = hfun(pts, com)
        i = descend(h, i)
        d = D[i]
        # contact points: hull points within 0.6 mm of the support plane
        allp = np.vstack([S, pts])
        hp = (allp - com) @ d
        # torque: share of weight on paw contacts x horizontal lever about knee axis
        tau = 0.0
        for j in pushers:
            v, knee, kax = paws[j]
            pv = v[((v - com) @ d) > hp.max() - 0.6]
            if len(pv):
                p = pv.mean(axis=0)
                F = M * 9.81e-3 * 0.5                       # worst case: half the weight on this paw
                r = p - knee
                # world vertical = d ; torque about knee axis = |kax . (r x F d)|
                tau = max(tau, abs(np.dot(kax, np.cross(r, F * d))) / 1000)
        max_tau = max(max_tau, tau)
        log.append(dict(step=f"knee beta={b:.0f}", tilt=round(ang(d), 1), knee_Nm=round(tau, 3)))
        if ang(d) < 8:
            break
    # finally all legs to stand
    betas = [30.0] * 4
    yaws = [0.0] * 4
    pts, com, _ = config(betas, yaws)
    h = hfun(pts, com)
    i = descend(h, i)
    log.append(dict(step="all legs to stand pose", tilt=round(ang(D[i]), 1)))
    return dict(start=[round(x, 2) for x in start_dir], success=ang(D[i]) < 8, max_knee_Nm=round(max_tau, 3), log=log)


if __name__ == "__main__":
    res = dict(mass_g=M, com_body=COM0.tolist())
    res["paw_length_mm"] = PAW_L
    if os.environ.get("SKIPRESTS"):
        res["manoeuvres"] = {}
    res["egg_mode"] = rest_report(f"egg mode (paws folded up, beta={TUCK:.0f})", [TUCK] * 4, [0] * 4)
    res["stand"] = rest_report("standing (beta=30)", [30] * 4, [0] * 4)
    falls = {"right side (-X down)": [-1, 0, 0], "left side (+X down)": [1, 0, 0], "face down": [0, -1, 0], "on back": [0, 1, 0],
             "front-right diagonal": [-0.7, -0.7, 0], "back-left diagonal": [0.7, 0.7, 0], "upside down": [0.05, 0.02, 1]}
    if os.environ.get("ONLY"):
        falls = {k: v for k, v in falls.items() if os.environ["ONLY"] in k}
    res["manoeuvres"] = {k: manoeuvre(np.array(v, float) / np.linalg.norm(v)) for k, v in falls.items()}
    json.dump(res, open(os.environ.get("OUTJ", "righting.json"), "w"), indent=1, default=float)
    for k in ("egg_mode", "stand"):
        print(res[k]["pose"], "CoM", res[k]["com"])
        for r in res[k]["rests"][:3] + res[k]["rests"][-2:]:
            print("   rest tilt", r["tilt_deg"], "dir", r["dir"], "barrier", r["barrier_mm"], "mm", r["barrier_mJ"], "mJ")
    for k, v in res["manoeuvres"].items():
        print(k, "success", v["success"], "max knee", v["max_knee_Nm"], "tilts:", [l["tilt"] for l in v["log"]][::3], v["log"][-1])
