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

POSE = sys.argv[1] if len(sys.argv) > 1 else "stand"
OUT = sys.argv[2] if len(sys.argv) > 2 else "stl"
EMO = sys.argv[3] if len(sys.argv) > 3 else "neutral"
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
def add(mat, s, tag=None):
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
    shell = shell - place_axis(rbox(-3.3, 3.3, -2.0, 2.0, -6, 6, 1.4), (sx * 12, yc, ch_h), egg_normal(sx * 12, yc, ch_h))

# two-tone split with a 0.9 mm reveal groove
skin = OUTER - egg_off(0.8)
shell = shell - (Box(400, 400, 0.9).moved(SPLIT_PL.location) & skin)
cap = split(shell, bisect_by=SPLIT_PL, keep=Keep.TOP)
body = split(shell, bisect_by=SPLIT_PL, keep=Keep.BOTTOM)
add("cream", body, "shell")
add("caramel", cap, "shell")

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
    add("eye_r" if sx < 0 else "eye_l", place_axis(cyl(SCREEN_R, 0.3, (0, 0, -depth - 0.15)), E, d))
    add("glass", place_axis(cyl(GLASS_R, 0.3, (0, 0, -depth - 0.2)) - cyl(SCREEN_R - 0.05, 2, (0, 0, -depth)), E, d))
try:
    vis = fillet(vis.edges().filter_by(GeomType.CIRCLE).group_by(SortBy.RADIUS)[0], 0.4)
except Exception:
    pass
add("dark", vis, "shell")
for pk in EYE_POCKETS:                     # the shell around the visor is thinned where the round PCB sits
    MAT["cream"][0] = MAT["cream"][0] - pk

# nose (tiny glossy bean under the visor bridge)
NOSE_H = 22.5
yn = egg_surf_y(0, NOSE_H)
add("dark", scale(Sphere(1.0), by=(3.4, 2.0, 2.4)).translate((0, yn + 0.7, NOSE_H)))
# cliff-sensor windows (smoked) + USB-C insert
for (cx, cy, chh) in CHIN:
    add("dark", place_axis(rbox(-3.0, 3.0, -1.7, 1.7, -2.6, 0.4, 1.2), (cx, cy, chh), egg_normal(cx, cy, chh)))
add("dark", place_axis(rbox(-4.4, 4.4, -1.5, 1.5, -2.4, -0.6, 1.4) - rbox(-3.4, 3.4, -0.7, 0.7, -5, 1, 0.6),
                       (0, yu, USB_H), USB_D))
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
    add("caramel", pose_ear(shellE) - INNER)
    add("cream", pose_ear(inner))

# ------------------------------------------------------------------ legs
def leg_vec(k, ang):
    sy = HIPS[k][1]
    a = math.radians(ang)
    return (sy * math.sin(a), -math.cos(a))           # (dy, dh)

def wheel_centre(k, ang):
    sx, sy = HIPS[k]
    _, hy, hh = hip(k)
    dy, dh = leg_vec(k, ang)
    return (sx * (WHEEL_X0 + WHEEL_W / 2), hy + LEG_L * dy, hh + LEG_L * dh)

def leg_solids(k, ang, driven):
    """Arm = tapered rounded bar (hip disc r10 -> axle boss r8.2, 6.8 mm thick, 2.6 mm edge rounds);
    wheel outboard on the axle; driven legs carry the N20 inboard in a slim dark pod under the belly."""
    sx, sy = HIPS[k]
    _, hy, hh = hip(k)
    cx, cy, ch = wheel_centre(k, ang)
    th = ARM_X1 - ARM_X0
    xc = sx * (ARM_X0 + th / 2)
    r1, r2 = 10.0, 8.2
    ln = math.hypot(cy - hy, ch - hh)
    a1 = math.asin((r1 - r2) / ln)
    pts = [(-r1 * math.sin(a1), r1 * math.cos(a1)), (ln - r2 * math.sin(a1), r2 * math.cos(a1)),
           (ln - r2 * math.sin(a1), -r2 * math.cos(a1)), (-r1 * math.sin(a1), -r1 * math.cos(a1))][::-1]
    arm = extrude(Polygon(*pts, align=None), amount=th) + cyl(r1, th, (0, 0, th / 2)) + cyl(r2, th, (ln, 0, th / 2))
    arm = arm.clean()
    try:
        arm = fillet(arm.edges().filter_by(Axis.Z, reverse=True), 2.0)
    except Exception as ex:
        print("arm fillet failed", ex)
    dy, dh = (cy - hy) / ln, (ch - hh) / ln
    x0 = ARM_X0 if sx > 0 else -ARM_X1
    arm = arm.moved(Location(Plane(origin=(x0, hy, hh), x_dir=(0, dy, dh), z_dir=(1, 0, 0))))
    # chunky boot around the axle (reads as a paw; rear boots also sleeve the N20 gearmotor)
    xb0 = BOOT_X_IN if not driven else 3.2
    if driven:
        boot = cyl(BOOT_R, ARM_X1 - BOOT_X_IN, (sx * (ARM_X1 + BOOT_X_IN) / 2, cy, ch), "X") \
            + cyl(8.4, BOOT_X_IN - 3.2, (sx * (BOOT_X_IN + 3.2) / 2, cy, ch), "X")
    else:
        boot = cyl(BOOT_R, ARM_X1 - BOOT_X_IN, (sx * (ARM_X1 + BOOT_X_IN) / 2, cy, ch), "X")
    try:
        es = boot.edges().filter_by(GeomType.CIRCLE)
        boot = fillet(es.group_by(Axis.X)[0 if sx > 0 else -1], 3.2 if not driven else 2.6)
    except Exception as ex:
        print("boot fillet failed", ex)
    arm = arm + boot
    add("legcaramel", arm, "leg")
    # wheel
    w = WHEEL_W
    tyre = cyl(WHEEL_R, w) - cyl(WHEEL_R - 2.8, w + 2)
    try:
        tyre = fillet(tyre.edges().filter_by(GeomType.CIRCLE).group_by(SortBy.RADIUS)[-1], 2.3)
    except Exception:
        pass
    hub = cyl(WHEEL_R - 2.8, w - 0.6) - cyl(1.6, 20)
    capw = cyl(8.2, 1.4, (0, 0, w / 2 + 0.1))
    try:
        capw = fillet(capw.edges().group_by(Axis.Z)[-1], 1.0)
    except Exception:
        pass
    beans = scale(Sphere(1.0), by=(2.9, 2.4, 0.8)).translate((0, -1.5, w / 2 + 0.8))
    for bx, by in ((-3.2, 2.6), (0, 3.9), (3.2, 2.6)):
        beans = beans + scale(Sphere(1.0), by=(1.2, 1.2, 0.7)).translate((bx, by, w / 2 + 0.8))
    def place(s):
        s = s.rotate(Axis.Y, 90 * sx)
        return s.translate((cx, cy, ch))
    for part, mat in ((tyre, "tyre"), (hub, "legcream"), (capw, "legcaramel"), (beans, "cream2")):
        add(mat, place(part), "leg")

LEGS = {}
for k in HIPS:
    LEGS[k] = P[k]
    leg_solids(k, P[k], k in ("rl", "rr"))

# ------------------------------------------------------------------ internals (x-ray / fit check)
INT = {}
def addi(name, s, mat, mass):
    INT[name] = [s, mat, mass]

def mg90s(k):
    """MG90S: shaft along sx*X at the hip; case long axis +Z (up), shaft 6.1 mm from the bottom end.
    The lower mounting ear is trimmed off (it would pierce the round belly); the upper ear is screwed."""
    sx, sy = HIPS[k]
    _, hy, hh = hip(k)
    xs = lambda a, b: (min(sx * a, sx * b), max(sx * a, sx * b))
    x0, x1 = xs(HIP_X - 28.5, HIP_X - 6.0)
    case = box(x0, x1, hy - 6.1, hy + 6.1, hh - 6.1, hh + 16.7)
    tx0, tx1 = xs(HIP_X - 28.5 + 15.9, HIP_X - 28.5 + 18.4)
    tab = box(tx0, tx1, hy - 6.1, hy + 6.1, hh + 16.7, hh + 16.7 + 4.85)
    boss = cyl(5.9, 4.0, (sx * (HIP_X - 4.0), hy, hh), "X")
    spl = cyl(2.4, 2.0, (sx * (HIP_X - 1.0), hy, hh), "X")
    return case + tab + boss + spl

for k in HIPS:
    addi("servo_" + k, mg90s(k), "servo", 13.4)
for k in ("rl", "rr"):
    sx, sy = HIPS[k]
    cx, cy, ch = wheel_centre(k, LEGS[k])
    gb = box(min(sx * 20.6, sx * 29.6), max(sx * 20.6, sx * 29.6), cy - 6, cy + 6, ch - 5, ch + 5)
    mo = cyl(6.0, 15.0, (sx * 13.1, cy, ch), "X") & box(-40, 40, cy - 6, cy + 6, ch - 5, ch + 5)
    endc = cyl(4.5, 1.8, (sx * 4.7, cy, ch), "X")
    shaft = cyl(1.5, 9.0, (sx * 34.1, cy, ch), "X")
    addi("n20_" + k, gb + mo + endc + shaft, "motor", 9.5)

BAT_Y, BAT_H = 3.5, 18.6           # 2 x 14500 side by side, under the servo cases (different heights)
addi("battery_2x14500", cyl(7.1, 50, (0, BAT_Y - 7.1, BAT_H), "X") + cyl(7.1, 50, (0, BAT_Y + 7.1, BAT_H), "X"), "battery", 42.0)
addi("bms_2s", box(-15, 15, BAT_Y - 5, BAT_Y + 5, BAT_H + 7.2, BAT_H + 8.8), "pcb", 2.0)
DECK_H = 55.0
DEV_H = 62.0
addi("esp32s3_devkit", box(-34.5, 34.5, -4.0, 21.5, DEV_H, DEV_H + 1.6) + box(-12, 6, -3.0, 20.5, DEV_H + 1.6, DEV_H + 4.8)
     + box(29.0, 34.5, -2.0, 7.0, DEV_H + 1.6, DEV_H + 4.8) + box(29.0, 34.5, 11.0, 20.0, DEV_H + 1.6, DEV_H + 4.8), "pcb", 8.0)
for (E, d, sx) in EYES:
    dep = SCREEN_DEPTH[sx]
    lcd = place_axis(cyl(GLASS_R, 2.1, (0, 0, -dep - 1.05)), E, d)
    pcb = place_axis(cyl(19.3, 1.6, (0, 0, -dep - 2.1 - 0.8)), E, d)      # header removed, wires soldered to pads
    nm = "r" if sx < 0 else "l"
    addi("gc9a01_" + nm, pcb, "pcb_blue", 4.5)
    addi("lcd_" + nm, lcd, "lcdglass", 2.5)
SPK_H = 66.0
_ysp = egg_surf_y(0, SPK_H, +1)
SPK_D = sag_depth((0, _ysp, SPK_H), egg_normal(0, _ysp, SPK_H), 16.3, WALL) + 0.4
spk = cyl(16.0, 4.5, (0, 0, -SPK_D - 2.25)) + cyl(9, 3.0, (0, 0, -SPK_D - 6.0))
addi("speaker_32mm", place_axis(spk, (0, _ysp, SPK_H), egg_normal(0, _ysp, SPK_H)), "speaker", 7.0)
addi("max98357a", box(11, 28, 10, 26, DECK_H + 1, DECK_H + 3.5), "pcb", 2.0)
addi("inmp441", box(-7, 7, -7, 7, 86.5, 87.9), "pcb", 1.5)
addi("bmi160", box(-6.5, 6.5, -6, 7, DECK_H + 1, DECK_H + 2.6), "pcb", 1.5)
addi("drv8833", box(-9.25, 9.25, 9, 25.5, DECK_H + 1, DECK_H + 4), "pcb", 2.0)
addi("mp1584_servo", box(-29, -12, -13, 9, DECK_H + 1, DECK_H + 4.5), "pcb", 2.0)
addi("mp1584_logic", box(12, 29, -13, 9, DECK_H + 1, DECK_H + 4.5), "pcb", 2.0)
addi("charger_2s_typec", box(-9, 9, 28.0, 31.5, 21.0, 45.0), "pcb", 3.0)
for (cx, cy, chh) in CHIN:
    addi("tcrt5000_%s" % ("l" if cx > 0 else "r"), box(cx - 5, cx + 5, cy + 3.0, cy + 10.0, chh + 2.0, chh + 15.8), "pcb", 3.0)
# inner chassis: servo cradles (upper ears screwed, lower body in a saddle) + battery tray + deck
ch_ = None
for k, (sx, sy) in HIPS.items():
    _, hy, hh = hip(k)
    xa, xb = sorted((sx * 15.6, sx * 18.6))
    plate = box(xa, xb, hy - 9, hy + 9, hh - 9, hh + 23) - box(xa - 1, xb + 1, hy - 6.3, hy + 6.3, hh - 6.4, hh + 16.9)
    ch_ = plate if ch_ is None else ch_ + plate
tray = box(-25.5, 25.5, BAT_Y - 15, BAT_Y + 15, BAT_H - 8.6, BAT_H - 7.1) + box(-26.3, -25.1, BAT_Y - 15, BAT_Y + 15, BAT_H - 7.5, BAT_H + 6) + box(25.1, 26.0, BAT_Y - 15, BAT_Y + 15, BAT_H - 7.5, BAT_H + 6)
deck = box(-30, 30, -14, 26, DECK_H - 0.8, DECK_H + 0.8)
spine = box(-1.2, 1.2, -12, 14, 28.6, DECK_H)
ch_ = (ch_ + tray + deck + spine) & egg_off(WALL + 0.4)
addi("chassis_frame", ch_, "chassis", 0.0)

# ------------------------------------------------------------------ pose
def rot_pitch(s, deg):
    return s.rotate(Axis((0, 0, EGG_C), (1, 0, 0)), deg) if abs(deg) > 1e-6 else s

def egg_low(pitch_deg):
    a = math.radians(pitch_deg)
    best = (1e9, 0)
    for i in range(0, 72):
        t = math.radians(i * 5)
        for j in range(0, 46):
            u = math.radians(j * 2)
            r = R0 * math.sin(u)
            h = R0 - R0 * math.cos(u)
            x, y = r * math.cos(t), YS * r * math.sin(t)
            yy = y * math.cos(a) - (h - EGG_C) * math.sin(a)
            zz = y * math.sin(a) + (h - EGG_C) * math.cos(a) + EGG_C
            if zz < best[0]:
                best = (zz, yy)
    return best

def wheel_low(k, ang, pitch_deg):
    cx, cy, ch = wheel_centre(k, ang)
    a = math.radians(pitch_deg)
    return cy * math.sin(a) + (ch - EGG_C) * math.cos(a) + EGG_C - WHEEL_R, cy * math.cos(a) - (ch - EGG_C) * math.sin(a)

pitch = P.get("pitch")
if pitch is None:
    # the supporting front wheel (fr) and the rear wheels touch the desk together
    best = None
    for pd10 in range(-400, 101):
        pd = pd10 / 10.0           # negative rotation about +X tips the nose up (face -Y goes up)
        dz = wheel_low("fr", P["fr"], pd)[0] - wheel_low("rl", P["rl"], pd)[0]
        if best is None or abs(dz) < abs(best[1]):
            best = (pd, dz)
    pitch = best[0]
    P["pitch"] = pitch
    P["belly_clearance"] = egg_low(pitch)[0] - wheel_low("rl", P["rl"], pitch)[0]

for m in MAT:
    MAT[m] = [rot_pitch(s, pitch) for s in MAT[m]]
for n in INT:
    INT[n][0] = rot_pitch(INT[n][0], pitch)
zmin = min(min(s.bounding_box().min.Z for s in MAT[m]) for m in MAT)
GZ = -zmin
for m in MAT:
    MAT[m] = [s.translate((0, 0, GZ)) for s in MAT[m]]
for n in INT:
    INT[n][0] = INT[n][0].translate((0, 0, GZ))

# ------------------------------------------------------------------ mass properties
DENS = {"cream": 1.24 * 0.92, "caramel": 1.24 * 0.92, "legcaramel": 1.24 * 0.92, "legcream": 1.24 * 0.92, "lens": 1.27, "dark": 1.27, "cream2": 1.24, "tyre": 1.21 * 0.9,
        "glass": 2.0, "eye_l": 2.5, "eye_r": 2.5, "blush": 1.2}
masses = []      # (name, grams, centroid)
for m, lst in MAT.items():
    for i_, s in enumerate(lst):
        isleg = TAGS.get((m, i_)) == "leg"
        g = s.volume / 1000.0 * DENS.get(m, 1.2)
        if m in ("eye_l", "eye_r", "glass"):
            continue                      # counted inside the GC9A01 module masses
        if isleg and m == "legcaramel":
            g *= 0.6                      # arms printed at ~50 % gyroid infill
        masses.append(("leg_" + m if isleg else m, g, tuple(s.center(CenterOf.MASS))))
for n, (s, mat, g) in INT.items():
    if n == "chassis_frame":
        g = s.volume / 1000.0 * 1.24 * 0.6
    masses.append((n, g, tuple(s.center(CenterOf.MASS))))
# lumped extras: wiring 9 g, screws/inserts/magnets 7 g, M3 front axles 2 g, bulk caps 3 g, WS2812B x2 1 g,
# horns 2 g -> placed at the deck / hips
cx_deck = (0.0, 6.0, DECK_H + GZ)
masses.append(("wires+screws+caps+leds", 22.0, cx_deck))
masses.append(("horns", 2.0, (0.0, 0.0, HIP_H + GZ)))
M = sum(g for _, g, _ in masses)
com = tuple(sum(g * c[i] for _, g, c in masses) / M for i in range(3))

# ------------------------------------------------------------------ export
def compound(lst):
    lst = [s for s in lst if s is not None and getattr(s, "_wrapped", None) is not None]
    return Compound(children=lst) if len(lst) > 1 else lst[0]

info = {"pose": POSE, "emotion": EMO, "legs_deg": {k: P[k] for k in HIPS}, "pitch_deg": pitch,
        "belly_clearance_mm": P.get("belly_clearance"),
        "ground_offset_GZ": round(GZ, 2), "mass_g": round(M, 1),
        "com_world": [round(c, 2) for c in com], "com_body_h": round(com[2] - GZ, 2),
        "screen_depth_mm": {str(k): round(v, 2) for k, v in SCREEN_DEPTH.items()}, "parts": {}}
by_group = {}
for name, g, c in masses:
    by_group[name] = round(by_group.get(name, 0) + g, 1)
info["mass_breakdown_g"] = by_group
for m, lst in MAT.items():
    c = compound(lst)
    export_stl(c, os.path.join(OUT, m + ".stl"), tolerance=0.03, angular_tolerance=0.08)
    bb = c.bounding_box()
    info["parts"][m] = {"volume_mm3": round(sum(s.volume for s in lst), 1),
                        "bbox": [round(v, 1) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)]}
groups = {}
for n, (s, mat, g) in INT.items():
    groups.setdefault(mat, []).append(s)
for mat, lst in groups.items():
    export_stl(compound(lst), os.path.join(OUT, "int_" + mat + ".stl"), tolerance=0.05, angular_tolerance=0.1)
allb = compound([s for l in MAT.values() for s in l]).bounding_box()
info["overall_bbox_mm"] = [round(allb.max.X - allb.min.X, 1), round(allb.max.Y - allb.min.Y, 1), round(allb.max.Z - allb.min.Z, 1)]
for k in HIPS:
    info.setdefault("wheel_contacts_world", {})[k] = [round(v, 1) for v in wheel_centre(k, LEGS[k])]

# ---- fit checks (interference volumes, mm^3); legs are checked against the shell in every pose
if not FAST:
    shell_parts = [MAT[m][i] for (m, i), t in TAGS.items() if t == "shell"]
    leg_parts = [(m, i, MAT[m][i]) for (m, i), t in TAGS.items() if t == "leg"]
    shell_all = compound(shell_parts)
    clash = {}
    names = list(INT.keys())
    def vol(a, b):
        ba, bb_ = a.bounding_box(), b.bounding_box()
        if (ba.max.X < bb_.min.X or bb_.max.X < ba.min.X or ba.max.Y < bb_.min.Y or bb_.max.Y < ba.min.Y
                or ba.max.Z < bb_.min.Z or bb_.max.Z < ba.min.Z):
            return 0.0
        try:
            return (a & b).volume
        except Exception:
            return -1.0
    # legs (arms, wheels, motor pods) against the shell, in every pose
    for (m, i, sl) in leg_parts:
        for sp in shell_parts:
            v = vol(sl, sp)
            if abs(v) > 0.3:
                clash["leg_%s%d|shell" % (m, i)] = round(clash.get("leg_%s%d|shell" % (m, i), 0) + v, 2)
    if POSE in ("stand", "xray"):
        for i, a in enumerate(names):
            sa = INT[a][0]
            v = vol(sa, shell_all) if a != "chassis_frame" else 0
            if abs(v) > 0.3:
                clash[a + "|shell"] = round(v, 2)
            for b in names[i + 1:]:
                if "chassis_frame" in (a, b):
                    continue
                v = vol(sa, INT[b][0])
                if abs(v) > 0.3:
                    clash[a + "|" + b] = round(v, 2)
            # internals vs legs (except the N20 that lives in its own pod / the servo spline in its arm)
            for (m, i2, sl) in leg_parts:
                if a.startswith("n20") or a.startswith("servo"):
                    continue
                v = vol(sa, sl)
                if abs(v) > 0.3:
                    clash[a + "|leg_%s%d" % (m, i2)] = round(v, 2)
    info["clashes_mm3"] = clash
with open(os.path.join(OUT, "info.json"), "w") as f:
    json.dump(info, f, indent=1)
print(json.dumps({k: info[k] for k in info if k not in ("parts",)}, indent=1))
