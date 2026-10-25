#!/usr/bin/env python3
"""Quasi-static self-righting check for Findik.

For a rigid body resting on a flat desk, the CoM height as a function of the roll (or pitch) angle is the
support function of the body's convex hull (projected on the plane of rotation) measured from the CoM.
Local minima = angles where the robot can come to rest.  A design is "self-righting" in that plane when
the only minimum is upright.  We evaluate two leg poses exported by model.py:
  stand : legs down (what it is in when it falls)
  tuck  : legs swung fore/aft out of the round outline (what it does after the IMU sees a fall)
usage: python3 selfright.py <stand_dir> <tuck_dir>  -> prints a table and writes selfright.json
"""
import json, math, os, struct, sys
import numpy as np

EXTERIOR = ["cream", "caramel", "dark", "tyre", "cream2", "glass", "eye_l", "eye_r"]


def read_stl(path):
    with open(path, "rb") as f:
        data = f.read()
    n = struct.unpack("<I", data[80:84])[0]
    arr = np.frombuffer(data[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return arr["v"].reshape(-1, 3).astype(float)


def hull2d(pts):
    pts = np.unique(np.round(pts, 3), axis=0)
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(tuple(p))
    for p in pts[::-1]:
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(tuple(p))
    return np.array(lower[:-1] + upper[:-1])


def analyse(d, axes):
    info = json.load(open(os.path.join(d, "info.json")))
    com = np.array(info["com_world"])
    pts = np.vstack([read_stl(os.path.join(d, m + ".stl")) for m in EXTERIOR if os.path.exists(os.path.join(d, m + ".stl"))])
    i, j = axes
    P = hull2d(pts[:, [i, j]])
    c = com[[i, j]]
    angs = np.arange(-180, 180, 0.5)
    H = []
    for a in angs:
        r = math.radians(a)
        n = np.array([math.sin(r), -math.cos(r)])       # ground-facing direction in the body frame
        H.append(float(np.max((P - c) @ n)))
    H = np.array(H)
    mins = []
    N = len(H)
    for k in range(N):
        if H[k] < H[k - 1] and H[k] <= H[(k + 1) % N]:
            mins.append((float(angs[k]), round(float(H[k]), 2)))
    # energy barrier from the upright rest: lowest max of H on the way to +-90
    up = H[np.argmin(np.abs(angs))]
    return dict(minima_deg_and_com_height_mm=mins, upright_com_height_mm=round(float(up), 2),
                H_at_90=round(float(H[np.argmin(np.abs(angs - 90))]), 2), mass_g=info["mass_g"], com=info["com_world"],
                curve=[(float(a), round(float(h), 2)) for a, h in zip(angs[::10], H[::10])])


if __name__ == "__main__":
    out = {}
    for name, d in (("stand", sys.argv[1]), ("tuck", sys.argv[2])):
        out[name] = {"roll(front view, x-z)": analyse(d, (0, 2)), "pitch(side view, y-z)": analyse(d, (1, 2))}
    for name in out:
        for plane, r in out[name].items():
            print(f"{name:6s} {plane:22s} rests at {r['minima_deg_and_com_height_mm']}  (upright CoM h {r['upright_com_height_mm']} mm)")
    json.dump(out, open("selfright.json", "w"), indent=1)
