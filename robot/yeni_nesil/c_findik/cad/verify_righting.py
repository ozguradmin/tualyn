#!/usr/bin/env python3
"""3D quasi-static self-righting verification for Findik (uses model.py parameters + stl/info.json masses).

The robot is a rigid body on a flat desk.  For a "down" direction n (body frame) its CoM height is the
support function H(n) = max_p (p - com).n over all exterior points.  It rests in a local minimum of H.
When the legs move slowly, it follows that minimum (gradient descent on the (pitch, roll) grid).
We start it lying on its side (roll 84 deg, the rest the stand pose falls into) and replay the firmware
sequence: lower-side legs swing (front 80, rear 120) -> body rolls on its round belly -> all legs to stand.
Also: the minimum tuck that still works, the side-fall from different landing pitches, fore/aft tipping
angles with and without the paw-catch reflex, and the 3-wheel wave stability margin.
usage: python3 verify_righting.py  -> prints + writes righting.json"""
import json, math, sys
sys.argv = ["explore.py"]
exec(open("explore.py").read().split('if __name__ == "__main__":')[0])

PH = np.arange(-180, 180, 2.0)
PS = np.arange(-90, 91, 2.0)
D = np.zeros((len(PH), len(PS), 3))
for i, ph in enumerate(np.radians(PH)):
    for j, ps in enumerate(np.radians(PS)):
        D[i, j] = [math.sin(ps), math.cos(ps) * math.sin(ph), -math.cos(ps) * math.cos(ph)]
FLAT = D.reshape(-1, 3)


def Hmap(angles):
    P, c = pose_cloud(angles)
    Q = P - c
    H = np.empty(len(FLAT))
    for k in range(0, len(FLAT), 2000):
        H[k:k + 2000] = (Q @ FLAT[k:k + 2000].T).max(0)
    return H.reshape(len(PH), len(PS)), c


def settle3(H, i, j):
    while True:
        best = (H[i, j], i, j)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                ii, jj = (i + di) % len(PH), j + dj
                if 0 <= jj < len(PS) and H[ii, jj] < best[0] - 1e-9:
                    best = (H[ii, jj], ii, jj)
        if best[1:] == (i, j):
            return i, j
        i, j = best[1], best[2]


def run(seq, ph0, ps0, steps=10):
    i, j = int(np.argmin(abs(PH - ph0))), int(np.argmin(abs(PS - ps0)))
    H, _ = Hmap(seq[0]); i, j = settle3(H, i, j)
    trace = [(float(PH[i]), float(PS[j]))]
    prev = seq[0]
    for tgt in seq[1:]:
        for s in range(1, steps + 1):
            a = {k: prev[k] + (tgt[k] - prev[k]) * s / steps for k in prev}
            H, _ = Hmap(a); i, j = settle3(H, i, j)
        prev = tgt
        trace.append((float(PH[i]), float(PS[j])))
    return trace


S = g["STAND"]
stand = dict(fl=S, fr=S, rl=S, rr=S)
out = {}
H0, c0 = Hmap(stand)
out["stand_com_body_mm"] = [round(v, 1) for v in c0]
# 1) where does a side fall come to rest? (start from 70 deg roll, let it settle)
i, j = settle3(H0, int(np.argmin(abs(PH - 0))), int(np.argmin(abs(PS - 70))))
side_rest = (float(PH[i]), float(PS[j]))
out["side_fall_rest_(pitch,roll)"] = side_rest
# 2) firmware sequence for a left-side fall: lower-side legs swing, then stand
seq = [stand, dict(fl=80, fr=S, rl=120, rr=S), stand]
out["righting_left_side f80/r120"] = run(seq, *side_rest)
mirror = [stand, dict(fl=S, fr=80, rl=S, rr=120), stand]
out["righting_right_side f80/r120"] = run(mirror, side_rest[0], -side_rest[1])
for f, r in ((75, 120), (80, 115), (70, 120), (75, 110)):
    out[f"margin f{f}/r{r}"] = run([stand, dict(fl=f, fr=S, rl=r, rr=S), stand], *side_rest)
for ph in (-15, 15):
    out[f"landing pitch {ph}"] = run(seq, ph, side_rest[1])
# 3) fore/aft tipping angles about the wheel contacts (stand) and with the paw-catch reflex
com = c0
def tip(front_ang, rear_ang):
    fy = -g["HIP_YF"] - LEG_L * math.sin(math.radians(front_ang))
    ry = g["HIP_YR"] + LEG_L * math.sin(math.radians(rear_ang))
    fz = HIP_H - LEG_L * math.cos(math.radians(front_ang)) - WHEEL_R
    rz = HIP_H - LEG_L * math.cos(math.radians(rear_ang)) - WHEEL_R
    return (round(math.degrees(math.atan2(com[1] - fy, com[2] - fz)), 1),
            round(math.degrees(math.atan2(ry - com[1], com[2] - rz)), 1))
out["tip_forward_backward_deg_stand"] = tip(S, S)
out["tip_forward_backward_deg_catch_reflex(f60,r60)"] = tip(60, 60)
xw = WHEEL_X0 + WHEEL_W / 2
out["tip_side_deg"] = round(math.degrees(math.atan2(xw, com[2] - (HIP_H - LEG_L * math.cos(math.radians(S)) - WHEEL_R))), 1)
# 4) 3-wheel wave (fl up) stability margin: distance of CoM ground projection inside the triangle fr-rl-rr
wave = dict(fl=78, fr=S, rl=10, rr=10)
_, cw = pose_cloud(wave)
pts = {}
for k in ("fr", "rl", "rr"):
    sx, sy = HIPS[k]
    a = math.radians(wave[k])
    pts[k] = np.array([sx * xw, (g["HIP_YF"] if sy < 0 else g["HIP_YR"]) * sy + sy * LEG_L * math.sin(a)])
def edge_dist(p, a, b):
    t = b - a
    n = np.array([-t[1], t[0]]) / np.linalg.norm(t)
    return float((p - a) @ n)
cp = cw[:2]
d1 = edge_dist(cp, pts["fr"], pts["rl"]); d2 = edge_dist(cp, pts["rl"], pts["rr"]); d3 = edge_dist(cp, pts["rr"], pts["fr"])
sgn = np.sign(edge_dist((pts["fr"] + pts["rl"] + pts["rr"]) / 3, pts["fr"], pts["rl"]))
out["wave_support_margin_mm"] = round(min(sgn * d1, sgn * d2, sgn * d3), 1)
json.dump(out, open("righting.json", "w"), indent=1)
for k, v in out.items():
    print(f"{k:45s} {v}")
