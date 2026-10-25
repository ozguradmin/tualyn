"""Rig base geometry for package C (Findik). AUTO-DERIVED from concept_C2/model.py lines 1-320
(shell, split, visor, screens, ears) with material keys renamed per link. Do not edit by hand; see build_rig.py."""
#!/usr/bin/env python3
"""
Concept C2 "Findik" - a wheel-pawed roly-poly hamster for the desk.

Actuators: 4 x MG90S hip-pitch servos (one per leg) + 2 x N20 6 V 100 rpm gearmotors in the rear paws.
The front paws are free-rolling wheels.  The body is a hacıyatmaz (roly-poly) egg: round in front and
side view, battery at the very bottom.  After a fall it swings its legs fore/aft out of the round
outline, rolls upright on its belly by itself, then puts its paws down and stands.

Units mm, Z up, robot faces -Y, robot's right = -X.
Body frame: origin at the lowest point of the egg (h = 0).  World = body frame posed and shifted so min Z = 0.

usage:  python3 -I model.py [pose] [outdir] [emotion]
   pose: stand | tuck | wave | xray     emotion only switches the cheek-blush part on (happy)
Writes one STL per material into outdir and outdir/info.json (CoM, masses, bbox, clearances).
"""
import json, math, os, sys
from build123d import *

POSE = "stand"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp")
EMO = "neutral"
FAST = os.environ.get("FAST") == "1"          # skip clash checks
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ parameters
R0, HTOP, PTOP, YS = 48.0, 50.0, 2.0, 0.896      # egg: 96 wide, 86 deep, 98 tall
WALL = 1.8
EGG_C = R0                                       # centre of the round lower half (h)
SPLIT_F, SPLIT_B = 76.0, 40.0                    # two-tone split plane: height at front / back
HIP_X = 31.0                                     # servo spline tip (the horn sits inside the arm)
ARM_X0, ARM_X1 = 29.6, 34.0                      # arm faces (4.4 mm rounded bar)
HIP_H = 32.0
HIP_YF, HIP_YR = 15.5, 21.5                      # front hips at -HIP_YF, rear at +HIP_YR
LEG_L = 34.0                                     # hip axis -> wheel axle
WHEEL_R, WHEEL_W = 15.0, 6.8
WHEEL_X0 = 34.4                                  # wheel inner face
EYE_X, EYE_H = 21.5, 46.0                        # screen centres
SCREEN_R, GLASS_R, APER_R = 16.2, 17.8, 16.7     # GC9A01 active area r, glass r, visor aperture r
VIS_R, VIS_PINCH = 21.4, 15.0                    # visor lobes radius, bridge half-height (peanut)
STAND = 22.0
LEG_RANGE = {"f": (-5.0, 82.0), "r": (-12.0, 122.0)}     # usable hip sweep (deg)
BOOT_R, BOOT_X_IN = 11.6, 21.0                   # paw boot radius, inner face x

POSES = {   # leg angles (deg); +ve = wheel moves away from the body centre (front: forward, rear: back)
    "stand": dict(fl=STAND, fr=STAND, rl=STAND, rr=STAND, pitch=0.0),
    "xray":  dict(fl=STAND, fr=STAND, rl=STAND, rr=STAND, pitch=0.0),
    "tuck":  dict(fl=80, fr=STAND, rl=120, rr=STAND, pitch=0.0),   # self-righting: lower-side (left) legs swing
    "wave":  dict(fl=78, fr=STAND, rl=10, rr=10, pitch=None),  # waves the left paw on 3 wheels; pitch solved
}
P = dict(POSES[POSE])

MAT = {}
TAGS = {}           # (material, index) -> tag ("leg", "shell")
CUR = "body"
LM = {}             # (link, matKey) -> [solids]
def add(mat, s, tag=None):
    LM.setdefault((CUR, mat), []).append(s)
    MAT.setdefault(mat, []).append(s)
    if tag:
        TAGS[(mat, len(MAT[mat]) - 1)] = tag

# ------------------------------------------------------------------ helpers
def cyl(r, h, c=(0, 0, 0), axis="Z"):
    s = Cylinder(r, h)
    if axis == "X":
        s = s.rotate(Axis.Y, 90)
    elif axis == "Y":
        s = s.rotate(Axis.X, 90)
    return s.translate(c)

def box(x0, x1, y0, y1, z0, z1):
    return Box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))

def rbox(x0, x1, y0, y1, z0, z1, r):
    b = box(x0, x1, y0, y1, z0, z1)
    try:
        return fillet(b.edges(), min(r, (x1 - x0) / 2.01, (y1 - y0) / 2.01, (z1 - z0) / 2.01))
    except Exception:
        return b

def egg_pts(R, Ht, p, z0=0.0, n=26):
    pts = []
    for k in range(n + 1):
        t = (math.pi / 2) * k / n
        pts.append((R * math.sin(t), 0.0, z0 + R - R * math.cos(t)))
    for k in range(1, n + 1):
        u = (math.pi / 2) * k / n
        pts.append((R * math.cos(u) ** (2 / p), 0.0, z0 + R + Ht * math.sin(u) ** (2 / p)))
    pts[0] = (0.0, 0.0, z0)
    pts[-1] = (0.0, 0.0, z0 + R + Ht)
    return pts

def egg(R=R0, Ht=HTOP, p=PTOP, ys=YS, z0=0.0, n=18):
    """Egg as a loft of ellipses between two apex vertices (a non-uniformly scaled revolve makes
    OCCT booleans fail silently; the loft does not)."""
    pts = egg_pts(R, Ht, p, z0, n)
    secs = [Ellipse(r, r * ys).wires()[0].moved(Location((0, 0, z))) for (r, _, z) in pts[1:-1] if r > 0.2]
    return Solid.make_loft([Vertex(0, 0, pts[0][2])] + secs + [Vertex(0, 0, pts[-1][2])], ruled=False)

def egg_off(o):
    """egg offset inward by o (approximately uniform)."""
    return egg(R0 - o, HTOP - o, PTOP, (R0 * YS - o) / (R0 - o), o)

def egg_inside(x, y, h, o=0.0):
    R, Ht, ys = R0 - o, HTOP - o, (R0 * YS - o) / (R0 - o)
    h = h - o
    r = math.hypot(x, y / ys)
    if h < 0:
        return False
    if h <= R:
        return r * r + (R - h) ** 2 <= R * R
    if h > R + Ht:
        return False
    return (r / R) ** PTOP + ((h - R) / Ht) ** PTOP <= 1

def egg_surf_y(x, h, sign=-1, o=0.0):
    R, Ht, ys = R0 - o, HTOP - o, (R0 * YS - o) / (R0 - o)
    h = h - o
    if h <= R:
        rr2 = R * R - (R - h) ** 2
    else:
        q = 1 - ((h - R) / Ht) ** PTOP
        rr2 = (R * max(q, 0) ** (1 / PTOP)) ** 2
    return sign * ys * math.sqrt(max(rr2 - x * x, 0.0))

def egg_normal(x, y, h):
    e = 1e-3
    def f(a, b, c):
        R, Ht, ys = R0, HTOP, YS
        r = math.hypot(a, b / ys)
        if c <= R:
            return (r * r + (R - c) ** 2) / (R * R) - 1
        return (r / R) ** PTOP + ((c - R) / Ht) ** PTOP - 1
    g = ((f(x + e, y, h) - f(x - e, y, h)), (f(x, y + e, h) - f(x, y - e, h)), (f(x, y, h + e) - f(x, y, h - e)))
    return unit(g)

def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)

def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

def place_axis(s, origin, d):
    """Solid built along +Z at the origin -> axis d through 'origin'."""
    d = unit(d)
    ax = cross((0, 0, 1), d)
    sn = math.sqrt(sum(c * c for c in ax))
    ang = math.degrees(math.atan2(sn, d[2]))
    if sn > 1e-9:
        s = s.rotate(Axis((0, 0, 0), ax), ang)
    return s.translate(origin)

def hip(k):
    sx, sy = HIPS[k]
    return (sx * HIP_X, sy * (HIP_YF if sy < 0 else HIP_YR), HIP_H)

HIPS = {"fr": (-1, -1), "fl": (1, -1), "rr": (-1, 1), "rl": (1, 1)}   # x<0 = robot's right

# ------------------------------------------------------------------ shell + split
OUTER = egg()
INNER = egg_off(WALL)
nrm = unit((0.0, SPLIT_F - SPLIT_B, 2 * R0 * YS))
SPLIT_PL = Plane(origin=(0, 0, (SPLIT_F + SPLIT_B) / 2), z_dir=nrm)
shell = OUTER - INNER

# joint sockets: the arm's round hub sits in a cup; the cup is the region the arm's root sweeps over
# its usable range (so the arm never rubs the round flank), with a 1.8 mm wall behind it
def sweep_relief(k, grow, x_in):
    sx, sy = HIPS[k]
    _, hy, hh = hip(k)
    a0, a1 = LEG_RANGE["f" if sy < 0 else "r"]
    reach = 24.0
    r = 10.0 + grow
    x0, x1 = sorted((sx * x_in, sx * 70.0))
    xc, w = (x0 + x1) / 2, x1 - x0
    sol = cyl(r, w, (xc, hy, hh), "X")
    n = max(2, int((a1 - a0) / 9) + 1)
    for i in range(n):
        a = math.radians(a0 + (a1 - a0) * i / (n - 1))
        dy, dh = sy * math.sin(a), -math.cos(a)
        sol = sol + cyl(r - 0.6, w, (xc, hy + reach * dy, hh + reach * dh), "X") \
            + Box(w, reach, 2 * (r - 0.6)).rotate(Axis.X, math.degrees(math.atan2(dh, dy))).translate((xc, hy + reach / 2 * dy, hh + reach / 2 * dh))
    return sol
POCKETS = []
for k, (sx, sy) in HIPS.items():
    _, hy, hh = hip(k)
    pocket = sweep_relief(k, 0.8, ARM_X0 - 0.8) & OUTER
    POCKETS.append(pocket)
    cup = (sweep_relief(k, 0.8 + WALL, ARM_X0 - 0.8 - WALL) & OUTER) - pocket
    shell = (shell + cup) - pocket
    shell = shell - cyl(6.3, 12, (sx * (ARM_X0 - 3), hy, hh), "X")       # horn boss hole

# eyes: screen axes follow the local surface normal
EYES = []
for sx in (-1, 1):
    yS = egg_surf_y(sx * EYE_X, EYE_H)
    E = (sx * EYE_X, yS, EYE_H)
    n_ = egg_normal(*E)
    d = unit((n_[0], n_[1] - 0.12, n_[2] + 0.05))       # ~21 deg toe-out, ~2 deg look-up (close to the surface normal)
    EYES.append((E, d, sx))

# visor: peanut-shaped glossy black face plate (two lobes + pinched bridge), flush in the egg
def visor_prism(grow=0.0):
    p = None
    for sx in (-1, 1):
        c = cyl(VIS_R + grow, 70, (sx * EYE_X, -45, EYE_H), "Y")
        p = c if p is None else p + c
    p = p + box(-EYE_X, EYE_X, -80, -10, EYE_H - VIS_PINCH - grow, EYE_H + VIS_PINCH + grow)
    try:
        es = [e for e in p.edges().filter_by(Axis.Y) if abs(abs(e.center().Z - EYE_H) - VIS_PINCH - grow) < 0.3
              and abs(abs(e.center().X) - EYE_X) < 16]
        p = fillet(es, 6.0)
    except Exception as ex:
        print("visor fillet failed", ex)
    return p

shell = shell - visor_prism(0.45)

# speaker grille (back, caramel) + USB-C charge port (back-bottom)
yb = egg_surf_y(0, 60, +1)
holes = None
pts_g = [(0, 0)] + [(4.3 * math.cos(2 * math.pi * i / 6), 4.3 * math.sin(2 * math.pi * i / 6)) for i in range(6)] \
        + [(8.4 * math.cos(2 * math.pi * i / 12 + 0.26), 8.4 * math.sin(2 * math.pi * i / 12 + 0.26)) for i in range(12)]
for (gx, gz) in pts_g:
    hc = cyl(0.85, 20, (gx, yb, 60 + gz), "Y")
    holes = hc if holes is None else holes + hc
shell = shell - holes
USB_H = 17.0
yu = egg_surf_y(0, USB_H, +1)
USB_D = egg_normal(0, yu, USB_H)
shell = shell - place_axis(rbox(-4.7, 4.7, -1.8, 1.8, -6, 6, 1.6), (0, yu, USB_H), USB_D)

# chin windows for the two downward-forward cliff sensors
CHIN = []
for sx in (-1, 1):
    ch_h = 9.0
    yc = egg_surf_y(sx * 12, ch_h)
    CHIN.append((sx * 12, yc, ch_h))
    shell = shell - place_axis(rbox(-5.6, 5.6, -3.1, 3.1, -6, 6, 1.6), (sx * 12, yc, ch_h), egg_normal(sx * 12, yc, ch_h))   # widened to the real TCRT5000 lens pair (10.2 mm)

# two-tone split with a 0.9 mm reveal groove
skin = OUTER - egg_off(0.8)
shell = shell - (Box(400, 400, 0.9).moved(SPLIT_PL.location) & skin)
cap = split(shell, bisect_by=SPLIT_PL, keep=Keep.TOP)
body = split(shell, bisect_by=SPLIT_PL, keep=Keep.BOTTOM)
add("cream", body, "shell")
add("cap", cap, "shell")

# ------------------------------------------------------------------ visor + screens
vis = visor_prism(0.0) & (egg_off(0.15) - egg_off(2.0))
for pk in POCKETS:
    vis = vis - pk                         # the visor lobes stop at the shoulder sockets
SCREEN_DEPTH = {}
EYE_POCKETS = []
def sag_depth(E, d, rr, o):
    """deepest point (along -d, from the plane through E) of the egg skin offset o on a circle of radius rr."""
    u = unit(cross(d, (0, 0, 1)))
    v = cross(d, u)
    worst = 0.0
    for i in range(48):
        a = 2 * math.pi * i / 48
        px = [E[j] + rr * (math.cos(a) * u[j] + math.sin(a) * v[j]) for j in range(3)]
        lo, hi = -15.0, 15.0
        for _ in range(40):
            mid = (lo + hi) / 2
            q = [px[j] + mid * d[j] for j in range(3)]
            if egg_inside(*q, o=o):
                lo = mid
            else:
                hi = mid
        worst = min(worst, lo)
    return -worst
for (E, d, sx) in EYES:
    # the flat LCD sits in a counterbored seat so the edge of the active area is flush with the
    # visor surface at the aperture rim (no deep well); the visor rim overlaps the glass by ~1 mm
    depth = sag_depth(E, d, APER_R, 0.15) + 0.2
    SCREEN_DEPTH[sx] = depth
    vis = vis - place_axis(cyl(APER_R, 30, (0, 0, 0)), E, d)
    vis = vis - place_axis(cyl(GLASS_R + 0.15, 2.4, (0, 0, -depth - 1.2)), E, d)
    vis = vis - place_axis(cyl(19.8, 12, (0, 0, -depth - 2.1 - 6)), E, d)          # GC9A01 PCB pocket
    EYE_POCKETS.append(place_axis(cyl(19.8, 12, (0, 0, -depth - 2.1 - 6)), E, d))
    add("screen_eyeR" if sx < 0 else "screen_eyeL", place_axis(cyl(SCREEN_R, 0.3, (0, 0, -depth - 0.15)), E, d))
    add("lcd_glass", place_axis(cyl(GLASS_R, 0.3, (0, 0, -depth - 0.2)) - cyl(SCREEN_R - 0.05, 2, (0, 0, -depth)), E, d))
try:
    vis = fillet(vis.edges().filter_by(GeomType.CIRCLE).group_by(SortBy.RADIUS)[0], 0.4)
except Exception:
    pass
add("visor", vis, "shell")
for pk in EYE_POCKETS:                     # the shell around the visor is thinned where the round PCB sits
    LM[("body", "cream")][0] = LM[("body", "cream")][0] - pk

# nose (tiny glossy bean under the visor bridge)
NOSE_H = 22.5
yn = egg_surf_y(0, NOSE_H)
add("nose", scale(Sphere(1.0), by=(3.4, 2.0, 2.4)).translate((0, yn + 0.7, NOSE_H)))
# cliff-sensor windows (smoked) + USB-C insert
for (cx, cy, chh) in CHIN:
    pass   # chin windows: see build_rig.py (open slot + visible TCRT5000 lenses)
pass   # USB-C: real metal receptacle added in build_rig.py
# cheek blush (WS2812B behind 0.8 mm cream window) - only lit when happy
if EMO == "happy":
    for sx in (-1, 1):
        bx, bh = sx * 27.0, 21.5
        by = egg_surf_y(bx, bh)
        add("blush", place_axis(scale(Sphere(1.0), by=(7.0, 4.8, 0.6)), (bx, by, bh), egg_normal(bx, by, bh)))

# ------------------------------------------------------------------ ears (caramel shell, cream inner)
for sx in (-1, 1):
    ex, ey = sx * 29.5, -6.0
    r = math.hypot(ex, ey / YS)
    eh = R0 + HTOP * (1 - (r / R0) ** PTOP) ** (1 / PTOP)
    shellE = scale(Sphere(1.0), by=(13.0, 4.8, 13.5))
    shellE = shellE - scale(Sphere(1.0), by=(9.4, 3.0, 9.8)).translate((0, -2.8, 1.2))
    inner = scale(Sphere(1.0), by=(9.0, 2.2, 9.4)).translate((0, -2.2, 1.2)) & box(-20, 20, -20, -0.9, -20, 20)
    def pose_ear(s, sx=sx, ex=ex, ey=ey, eh=eh):
        s = s.translate((0, 0, 9.0)).rotate(Axis.Y, -sx * 26).rotate(Axis.X, -10)
        return s.translate((ex, ey, eh - 5.5))
    add("ear", pose_ear(shellE) - INNER)
    add("ear_inner", pose_ear(inner))

