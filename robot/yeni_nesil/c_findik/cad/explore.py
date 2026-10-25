#!/usr/bin/env python3
"""Fast analytic point-cloud model of Findik for exploring leg ranges and self-righting sequences.
Imports the geometry parameters from model.py (without building any CAD).

- legal(k, ang): does the arm/boot/wheel of leg k at angle ang stay out of the egg (outside the hip
  socket) and out of the visor zone?
- rests(pose, plane): stable rest angles (local minima of the CoM height over the convex hull).
- quasi-static sequence: the robot sits in the minimum it is in; legs move in small steps; we track it.
usage: python3 explore.py [model.py]"""
import json, math, re, sys
import numpy as np

src = open(sys.argv[1] if len(sys.argv) > 1 else "model.py").read()
head = src[:src.index("# ------------------------------------------------------------------ shell + split")]
head = head.replace("os.makedirs(OUT, exist_ok=True)", "")
g = {}
exec(head.replace("from build123d import *", ""), g)
R0, HTOP, PTOP, YS = g["R0"], g["HTOP"], g["PTOP"], g["YS"]
HIP_X, ARM_X0, ARM_X1, HIP_H = g["HIP_X"], g["ARM_X0"], g["ARM_X1"], g["HIP_H"]
HIP_YF, HIP_YR, LEG_L = g["HIP_YF"], g["HIP_YR"], g["LEG_L"]
WHEEL_R, WHEEL_W, WHEEL_X0 = g["WHEEL_R"], g["WHEEL_W"], g["WHEEL_X0"]
BOOT_R, BOOT_X_IN = g["BOOT_R"], g["BOOT_X_IN"]
EYE_X, EYE_H, VIS_R, VIS_PINCH = g["EYE_X"], g["EYE_H"], g["VIS_R"], g["VIS_PINCH"]
egg_inside = g["egg_inside"]
HIPS = {"fr": (-1, -1), "fl": (1, -1), "rr": (-1, 1), "rl": (1, 1)}
info = json.load(open("stl/info.json"))
MB = info["mass_breakdown_g"]
M = info["mass_g"]


def hip(k):
    sx, sy = HIPS[k]
    return np.array([sx * HIP_X, sy * (HIP_YF if sy < 0 else HIP_YR), HIP_H])


def leg_points(k, ang, n=10):
    """surface-ish samples of arm, boot, wheel (+ N20 sleeve for rear legs) in the body frame."""
    sx, sy = HIPS[k]
    hp = hip(k)
    a = math.radians(ang)
    d = np.array([0, sy * math.sin(a), -math.cos(a)])
    perp = np.array([0, -d[2], d[1]])
    pts = []
    xs_arm = [sx * ARM_X0, sx * ARM_X1]
    for s in np.linspace(0, LEG_L, 12):
        r = 10.0 + (8.2 - 10.0) * s / LEG_L
        for t in np.linspace(-r, r, 7):
            for x in xs_arm:
                p = hp + s * d + t * perp
                pts.append([x, p[1], p[2]])
    c = hp + LEG_L * d
    for th in np.linspace(0, 2 * math.pi, 36, endpoint=False):
        for rr, xa, xb in ((WHEEL_R, WHEEL_X0, WHEEL_X0 + WHEEL_W), (BOOT_R, BOOT_X_IN, ARM_X1)):
            for x in (xa, xb, (xa + xb) / 2):
                pts.append([sx * x, c[1] + rr * math.cos(th), c[2] + rr * math.sin(th)])
        if k in ("rl", "rr"):
            for x in (3.2, 12, BOOT_X_IN):
                pts.append([sx * x, c[1] + 8.4 * math.cos(th), c[2] + 8.4 * math.sin(th)])
    return np.array(pts), c


def visor_zone(p):
    """point near the face skin inside the peanut visor outline (projected along y)"""
    x, y, h = p
    if y > -5:
        return False
    inl = any((x - sx * EYE_X) ** 2 + (h - EYE_H) ** 2 <= (VIS_R + 1.0) ** 2 for sx in (-1, 1)) or \
        (abs(x) <= EYE_X and abs(h - EYE_H) <= VIS_PINCH + 1.0)
    return inl


def legal(k, ang):
    """arm+boot+wheel must stay outside the egg (except inside the hip socket r 11.7) and away from the visor."""
    pts, c = leg_points(k, ang)
    hp = hip(k)
    bad = 0
    for p in pts:
        dist = math.hypot(p[1] - hp[1], p[2] - hp[2])
        if dist <= 11.7 and abs(p[0]) >= ARM_X0 - 0.7:
            continue
        if egg_inside(p[0], p[1], p[2]):
            bad += 1
    return bad


def over_visor(k, ang):
    """arm points that sit within 6 mm in front of the visor (they would cover the face)"""
    pts, c = leg_points(k, ang)
    n = 0
    for p in pts:
        if visor_zone(p) and not egg_inside(*p) and egg_inside(p[0] * 0.9, p[1] * 0.9, 48 + (p[2] - 48) * 0.9):
            n += 1
    return n


# ---------------- body point cloud (egg surface + ears) and masses
def egg_cloud():
    pts = []
    for i in range(72):
        t = 2 * math.pi * i / 72
        for j in range(1, 60):
            u = math.pi * j / 60
            # parametrise along the profile: bottom circle then superellipse top
            if u <= math.pi / 2:
                r = R0 * math.sin(u)
                h = R0 - R0 * math.cos(u)
            else:
                v = u - math.pi / 2
                r = R0 * math.cos(v) ** (2 / PTOP)
                h = R0 + HTOP * math.sin(v) ** (2 / PTOP)
            pts.append([r * math.cos(t), YS * r * math.sin(t), h])
    pts.append([0, 0, 0])
    pts.append([0, 0, R0 + HTOP])
    # ears: ellipsoids 13 x 4.8 x 13.5 (approx placed as in model.py)
    for sx in (-1, 1):
        ex, ey = sx * 29.5, -6.0
        r = math.hypot(ex, ey / YS)
        eh = R0 + HTOP * (1 - (r / R0) ** PTOP) ** (1 / PTOP)
        tilt = math.radians(-sx * 26)
        for i in range(24):
            a = 2 * math.pi * i / 24
            lx, lz = 13.0 * math.cos(a), 13.5 * math.sin(a) + 9.0
            x = lx * math.cos(tilt) + lz * math.sin(tilt)
            z = -lx * math.sin(tilt) + lz * math.cos(tilt)
            pts.append([ex + x, ey, eh - 5.5 + z])
    return np.array(pts)


EGG = egg_cloud()
# mass model: fixed body part + moving legs
leg_mass = {}
for k in HIPS:
    m = sum(v for kk, v in MB.items() if kk.startswith("leg_")) / 4
    if k in ("rl", "rr"):
        m += 9.5
    leg_mass[k] = m
stand_angles = info["legs_deg"]
com0 = np.array(info["com_world"]) - np.array([0, 0, info["ground_offset_GZ"]])
body_mass = M - sum(leg_mass.values())


def leg_com(k, ang):
    sx, sy = HIPS[k]
    hp = hip(k)
    a = math.radians(ang)
    d = np.array([0, sy * math.sin(a), -math.cos(a)])
    return hp + 0.80 * LEG_L * d + np.array([sx * 6.0, 0, 0])   # lumped at 80 % of the leg, out at the wheel


body_com = (com0 * M - sum(leg_mass[k] * leg_com(k, stand_angles[k]) for k in HIPS)) / body_mass


def pose_cloud(angles):
    pts = [EGG]
    for k in HIPS:
        p, _ = leg_points(k, angles[k])
        pts.append(p)
    com = (body_com * body_mass + sum(leg_mass[k] * leg_com(k, angles[k]) for k in HIPS)) / M
    return np.vstack(pts), com


def H_curve(angles, plane):
    P, c = pose_cloud(angles)
    i, j = (0, 2) if plane == "roll" else (1, 2)
    Q = P[:, [i, j]] - c[[i, j]]
    angs = np.arange(-180, 180, 0.5)
    rad = np.radians(angs)
    N = np.stack([np.sin(rad), -np.cos(rad)], 1)
    H = (Q @ N.T).max(0)
    return angs, H, c


def minima(angs, H):
    out = []
    n = len(H)
    for k in range(n):
        if H[k] < H[k - 1] and H[k] <= H[(k + 1) % n]:
            out.append((float(angs[k]), round(float(H[k]), 2)))
    return out


def settle(angs, H, phi):
    """from phi, roll downhill to the local minimum"""
    k = int(np.argmin(np.abs(angs - phi)))
    n = len(H)
    while True:
        l, r = H[k - 1], H[(k + 1) % n]
        if l < H[k] and l <= r:
            k = k - 1
        elif r < H[k]:
            k = (k + 1) % n
        else:
            return float(angs[k]), float(H[k])


if __name__ == "__main__":
    print("leg mass (g)", {k: round(v, 1) for k, v in leg_mass.items()}, "body", round(body_mass, 1))
    print("legal ranges (bad points per angle):")
    for k in ("fl", "rl"):
        row = []
        for ang in range(-40, 181, 5):
            row.append((ang, "%d/%d" % (legal(k, ang), over_visor(k, ang))))
        print(k, " ".join(f"{a}:{b}" for a, b in row))
