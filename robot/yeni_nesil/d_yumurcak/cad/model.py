#!/usr/bin/env python3
"""Concept D2 "Yumurcak" - the walking weeble egg.

An upright egg (96 x 96 x 106 mm) that walks on four short legs. Each leg is a round
"haunch" turret that yaws about its own vertical axis (hip yaw, MG90S above it) and
carries a knee MG90S inside; the knee swings a bean-shaped paw outward/up (lift).
The head is the upper egg above an OBLIQUE seam (12 deg): one MG90S turns it about the
tilted axis, so one servo gives look-left/right + curious head-tilt + look-up, and the
seam never opens because it is a circle on the spherical part of the egg.

Units mm, Z up, robot faces -Y.  Body frame: origin = centre C of the bottom sphere.
World = body + (0, 0, CZ) so that the lowest point sits on Z=0.

usage: python3 -I model.py <pose> <outdir>
  pose: stand | curious | egg | xray (stand + internals exported)
"""
import json, math, os, sys
from build123d import *

POSE = sys.argv[1] if len(sys.argv) > 1 else "stand"
OUT = sys.argv[2] if len(sys.argv) > 2 else "stl"
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------- shell profile
R, ZS, TOP, WALL = 48.0, 18.0, 58.0, 1.6
_r0 = math.sqrt(R * R - ZS * ZS)
_H = TOP - ZS
_u = _H * _H / ((_r0 * _r0 / ZS) - 2 * _H)
B2 = _u + _H
ZC2 = TOP - B2
A2 = math.sqrt(B2 * B2 * ZS / _u)

ALPHA = 12.0                       # head-joint tilt (deg), axis leans forward (-Y)
NV = Vector(0, -math.sin(math.radians(ALPHA)), math.cos(math.radians(ALPHA)))
D_SEAM = 4.0                       # plane n.p = D_SEAM ; seam circle stays on the sphere (z<=18)
P0 = NV * D_SEAM                   # head-axis point on the seam plane
GAP = 0.8

YAW = [(-24.0, -24.0), (24.0, -24.0), (-24.0, 24.0), (24.0, 24.0)]   # FR FL BR BL  (robot faces -Y, so x<0 = robot right)
NAMES = ["FR", "FL", "BR", "BL"]
RT = 20.5                          # ball haunch radius
BZ = -36.0                         # ball centre height
FLAT = 17.5                        # knee joint plate (flat on the ball) at +-17.5 along Y
T_TOP, T_CYL_BOT, T_BOT = -17.0, -38.0, -56.5
POCKET = -23.4                     # horn pocket floor in the ball top
T_FIL = 7.0
KNEE_Z = -30.5                     # knee shaft at the TOP of the knee servo (higher push point)
KNEE_OFF = 18.5                    # horn plane distance from yaw axis along +-Y
FOOT_L = 48.0                      # knee axis -> sole
EYE_Z, EYE_X = 19.0, 19.6


def prof(off=0.0, n=48):
    pts = []
    l1 = math.asin(ZS / R)
    for i in range(n + 1):
        la = -math.pi / 2 + (l1 + math.pi / 2) * i / n
        pts.append(((R - off) * math.cos(la), (R - off) * math.sin(la)))
    t0 = math.asin((ZS - ZC2) / B2)
    for i in range(1, n + 1):
        tt = t0 + (math.pi / 2 - t0) * i / n
        nx, nz = math.cos(tt) / A2, math.sin(tt) / B2
        m = math.hypot(nx, nz)
        pts.append((A2 * math.cos(tt) - off * nx / m, ZC2 + B2 * math.sin(tt) - off * nz / m))
    pts[0] = (0.0, pts[0][1])
    pts[-1] = (0.0, pts[-1][1])
    return pts


def revolve_profile(pts):
    sp = Spline(*[Vector(p[0], 0, p[1]) for p in pts])
    ln = Line(Vector(0, 0, pts[-1][1]), Vector(0, 0, pts[0][1]))
    return revolve(Face(Wire([sp, ln])), Axis.Z, 360)


def egg_r(z):
    if z <= ZS:
        return math.sqrt(max(R * R - z * z, 0))
    return A2 * math.sqrt(max(1 - ((z - ZC2) / B2) ** 2, 0))


def halfspace(n, d, keep_above=True, size=400):
    """solid = {p : n.p >= d} (keep_above) or {n.p <= d}"""
    pl = Plane(origin=n * d, z_dir=n if keep_above else -n)
    return pl.location * Pos(0, 0, size / 2) * Box(size, size, size)


def place(obj, origin, x_dir, z_dir):
    return Plane(origin=origin, x_dir=x_dir, z_dir=z_dir).location * obj


def union(lst):
    out = lst[0]
    for s in lst[1:]:
        out = out + s
    return out


def stadium_prism(w, h, rad, zc, y0=-80, y1=0):
    """rounded rectangle in XZ centred (0, zc), extruded along Y from y0 to y1"""
    with BuildPart() as bp:
        with BuildSketch(Plane.XZ.offset(-y0)):
            with Locations((0, zc)):
                RectangleRounded(w, h, rad)
        extrude(amount=y1 - y0, dir=(0, 1, 0))
    return bp.part


# ----------------------------------------------------------------- off-the-shelf envelopes
def mg90s(tabs=True):
    """MG90S: case 22.8 x 12.2 x 22.7 (+ gear top -> 28.5 overall), tabs 32.5. Shaft at origin, +z."""
    s = Pos(5.5, 0, -22.7 / 2 - 1.5) * Box(22.8, 12.2, 22.7)
    if tabs:
        s += Pos(5.5, 0, -1.5 - 6.2) * Box(32.5, 12.2, 2.5)        # tabs
    s += Pos(0, 0, -1.5) * Cylinder(5.9, 1.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s += Pos(7.0, 0, -1.5) * Cylinder(3.0, 1.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s += Pos(0, 0, 0) * Cylinder(2.4, 3.6, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s


def sg90():
    """SG90: case 22.2 x 11.8 x 22.7, tabs 32.2. Shaft at origin, +z."""
    s = Pos(5.2, 0, -22.7 / 2 - 1.2) * Box(22.2, 11.8, 22.7)
    s += Pos(5.2, 0, -1.2 - 6.0) * Box(32.2, 11.8, 2.5)
    s += Pos(0, 0, -1.2) * Cylinder(5.8, 1.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s += Pos(0, 0, 0) * Cylinder(2.4, 3.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s


def horn(r=8.5):
    return Cylinder(3.6, 2.6, align=(Align.CENTER, Align.CENTER, Align.MIN)) + \
        Pos(0, 0, 2.6) * Cylinder(r, 1.6, align=(Align.CENTER, Align.CENTER, Align.MIN))


def capsule(r, z0, z1, f):
    with BuildPart() as tp:
        Cylinder(r, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        fillet(tp.edges().group_by(Axis.Z)[0], f)
        fillet(tp.edges().group_by(Axis.Z)[-1], f)
    return Pos(0, 0, z0) * tp.part


# ----------------------------------------------------------------- shells
egg_out = revolve_profile(prof())
egg_in = revolve_profile(prof(WALL))
shell = egg_out - egg_in

head_shell = shell & halfspace(NV, D_SEAM + GAP / 2, True)
body_shell = shell & halfspace(NV, D_SEAM - GAP / 2, False)

# --- haunch cut-outs in the body shell
_cut = Sphere(RT + 0.7)
for (x, y) in YAW:
    body_shell = body_shell - Pos(x, y, BZ) * _cut

# --- charging port + ToF window
body_shell = body_shell - Pos(0, 44, -20.5) * Box(10.0, 12, 4.0)
_tofc = place(Cylinder(3.4, 14), (0, -41, -23), (1, 0, 0), (0, -0.8, -0.6))
body_shell = body_shell - _tofc
lens = _tofc & (egg_out - revolve_profile(prof(1.2)))

# --- face: visor band + accent bezel + eye sockets
VZ, VW, VH = 20.0, 74.0, 35.0
vis_in = stadium_prism(VW, VH, 16.8, VZ)
vis_out = stadium_prism(VW + 0.8, VH + 0.8, 17.2, VZ)
bez_out = stadium_prism(VW + 5.6, VH + 5.6, 19.6, VZ)
visor = head_shell & vis_in
head_shell = head_shell - vis_in           # visor sits flush (0.2 mm glue gap in reality)


def eye_frame(sx):
    x, z = sx * EYE_X, EYE_Z
    r = egg_r(z)
    y = -math.sqrt(r * r - x * x)
    n = Vector(x, y, z).normalized()
    p = Vector(x, y, z)
    xd = Vector(0, 0, 1).cross(n).normalized() * (-1)   # +x of screen ~ robot's left->right as seen
    return p, n, xd


skin = revolve_profile(prof(-0.12)) - egg_out
screens = []
for sx in (-1, 1):
    p, n, xd = eye_frame(sx)
    scr = skin & place(Cylinder(16.2, 30), p, xd, n) & halfspace(Vector(0, -1, 0), 10, True)
    screens.append(scr)

# ----------------------------------------------------------------- quiff (signature curl on top)
def quiff():
    """forward-curling cowlick: loft of shrinking circles along a curve"""
    path = Spline(Vector(0, -3.0, 54.5), Vector(0, -4.0, 60.5), Vector(0, -7.5, 65.0), Vector(0, -12.5, 65.6),
                  Vector(0, -14.5, 62.0))
    rs = [5.2, 4.6, 3.8, 3.0, 2.3, 1.7]
    secs = []
    for k, r in enumerate(rs):
        t = k / (len(rs) - 1)
        secs.append(Plane(origin=path @ t, z_dir=path % t) * Circle(r))
    q = loft(secs)
    q = q + Pos(path @ 1) * Sphere(1.7) + Pos(0, -3.0, 54.0) * scale(Sphere(1.0), by=(6.0, 6.0, 3.0))
    return q


qf = quiff()


def shell_cap(z0=48.0, teeth=7, depth=4.6, tilt=(-7.0, 11.0)):
    """the hatchling's eggshell 'hat': a 2.2 mm layer over the crown with a zig-zag rim"""
    layer = revolve_profile(prof(-1.7)) - revolve_profile(prof(-0.2))
    keep = Pos(0, 0, z0 + 50) * Box(200, 200, 100)
    for k in range(teeth):
        phi = 360.0 * (k + 0.5) / teeth
        with BuildPart() as tb:
            with BuildSketch(Plane.YZ):
                Polygon((-6.2, z0 + 0.01), (6.2, z0 + 0.01), (0, z0 - depth), align=None)
            extrude(amount=70)
        keep = keep + Rot(0, 0, phi) * tb.part
    keep = Rot(tilt[0], tilt[1], 0) * keep
    return layer & keep


cap = shell_cap()

# ----------------------------------------------------------------- legs
def turret():
    """ball haunch: sphere about the yaw axis, flat top (horn hub, hidden) and two joint plates"""
    b = Sphere(RT)
    b = b & Pos(0, 0, (T_TOP - BZ) - 50) * Box(100, 100, 100)
    b = b & Box(100, 2 * FLAT, 100)
    b = b - Pos(0, 0, POCKET - BZ) * Cylinder(9.6, 30, align=(Align.CENTER, Align.CENTER, Align.MIN))
    b = Pos(0, 0, BZ) * b
    inner = Pos(0, 0, BZ) * (Sphere(RT - 1.6) & Box(100, 2 * FLAT - 3.2, 100))
    return b, inner


TUR, TUR_IN = turret()


def foot_local():
    """bean paw, local frame: knee axis = local Y through origin, paw points to -Z (rotated later).
    local +X = outward."""
    top = Rot(90, 0, 0) * Cylinder(8.4, 13.0)
    top = fillet(top.edges(), 3.4)
    shank = Pos(0.4, 0, -(FOOT_L - 12.0) / 2) * Box(14.6, 13.0, FOOT_L - 12.0)
    shank = fillet(shank.edges().filter_by(Axis.Z), 5.6)
    paw = Pos(-4.0, 0, -FOOT_L + 9.6) * scale(Sphere(1.0), by=(14.8, 12.8, 10.2))   # bean foot, toe turned IN
    body = top + shank + paw
    cut = Pos(0, 0, -FOOT_L + 1.6 - 50) * Box(100, 100, 100)
    sole = body & cut
    body = body - cut
    return body, sole


FOOT, SOLE = foot_local()

# pose tables -------------------------------------------------------
# beta: paw angle from straight down, +ve = swung outward (deg); yaw: hip yaw (deg)
POSES = {
    "stand":   dict(beta=[30, 30, 30, 30], yaw=[0, 0, 0, 0], head=0.0),
    "curious": dict(beta=[30, 140, 30, 30], yaw=[0, 45, 0, 0], head=30.0),
    "xray":    dict(beta=[30, 30, 30, 30], yaw=[0, 0, 0, 0], head=0.0),
    "egg":     dict(beta=[100, 100, 100, 100], yaw=[0, 0, 0, 0], head=0.0),
    "push":    dict(beta=[143, 70, 143, 70], yaw=[0, 0, 0, 0], head=-12.0),
    "fallen":  dict(beta=[178, 178, 178, 178], yaw=[0, 0, 0, 0], head=0.0),
    "step":    dict(beta=[27, 60, 60, 27], yaw=[18, -18, 18, -18], head=18.0),
}
PZ = POSES.get(POSE, POSES["stand"])


def leg_parts(i):
    x, y = YAW[i]
    sx = -1 if x < 0 else 1           # outward X sign
    sy = -1 if y < 0 else 1           # horn faces front for front legs
    yawd = PZ["yaw"][i]
    beta = PZ["beta"][i]
    # foot: rotate about local Y so it points outward (sx) by beta, then place on knee axis
    mir = (lambda o: o) if sx > 0 else (lambda o: mirror(o, Plane.YZ))
    f = Rot(0, -sx * beta, 0) * mir(FOOT)
    s = Rot(0, -sx * beta, 0) * mir(SOLE)
    T = Pos(x, y + sy * (FLAT + 6.8), KNEE_Z)
    foot = T * f
    sole = T * s
    tur = Pos(x, y, 0) * TUR
    # knee servo inside turret: shaft along sy*Y at knee axis
    ks = place(mg90s(False), (x, y + sy * 12.1, KNEE_Z), (0, 0, -1), (0, sy, 0))
    kh = place(horn(6.5), (x, y + sy * (FLAT - 2.6), KNEE_Z), (1, 0, 0), (0, sy, 0))
    ys = place(mg90s(False), (x, y, POCKET + 4.2), (-x, -y, 0), (0, 0, -1))
    yh = place(horn(8.0), (x, y, POCKET + 4.2), (1, 0, 0), (0, 0, -1))
    ax = Axis((x, y, 0), (0, 0, 1))
    grp = dict(turret=tur, foot=foot, sole=sole, kservo=ks, khorn=kh)
    for k in list(grp):
        grp[k] = grp[k].rotate(ax, yawd)
    grp["yservo"] = ys
    grp["yhorn"] = yh
    return grp


legs = [leg_parts(i) for i in range(4)]

# ----------------------------------------------------------------- internals
cells = [Pos(sy * 7.2, 0, -43.5) * Cylinder(7.1, 50.0, align=(Align.CENTER, Align.CENTER, Align.MIN)) for sy in (-1, 1)]
# deck (tab plate) at z=2..4.5, clipped to the inner egg
deck = Pos(0, 0, -7.0) * Box(90, 90, 2.0) & egg_in
for (x, y) in YAW:
    deck = deck - Pos(x, y, -7.0) * Rot(0, 0, math.degrees(math.atan2(-y, -x))) * Pos(5.5, 0, 0) * Box(23.4, 12.8, 10)
for c in cells:
    deck = deck - Pos(0, 0, 0) * c
collars = union([Pos(x, y, T_TOP + 0.6) * (Cylinder(12.0, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                     - Cylinder(9.0, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN))) for (x, y) in YAW])
collars = collars & egg_in
posts = union([Pos(x * 0.86, y * 0.86, -12) * Box(4, 4, 8) for (x, y) in [(-31, 0), (31, 0), (0, 31), (0, -31)]])
post_head = place(Cylinder(5.0, 12.0, align=(Align.CENTER, Align.CENTER, Align.MIN)), P0 + NV * 2.3, (1, 0, 0), NV)
mcu = Pos(0, 32.0, 3.5) * Box(18, 3.6, 23.5)          # ESP32-S3-Zero 23.5x18 on the electronics sled
bucks = Pos(0, 37.0, 4.0) * Box(18, 5.0, 23)              # 3 x MP1584 sandwich + bulk caps
sled = Pos(0, 29.4, 3.0) * Box(24, 1.6, 26)
charger = Pos(0, 37.0, -10.5) * Box(13, 4, 23)
bms = Pos(0, -11.5, -22) * Box(6, 4, 28)
imu = Pos(0, -8, 9.5) * Box(13, 18, 2)
tof = place(Box(13, 2, 25 * 0 + 13), (0, -40.0, -21.5), (1, 0, 0), (0, -0.8, -0.6))
# displays (GC9A01 module: glass 35.5 + PCB 38.6 + header)
disp = []
for sx in (-1, 1):
    p, n, xd = eye_frame(sx)
    m = place(Pos(0, 0, -9.0) * (Cylinder(19.3, 1.6) + Pos(0, 0, 1.7) * Cylinder(17.8, 1.8)) +
              place(Box(12, 4, 8), (0, -17, -9), (1, 0, 0), (0, 0, 1)), p, xd, n)
    disp.append(m)
head_servo = place(sg90(), P0 + NV * 18.5, (1, 0, 0), -NV)
head_hub = place(Box(30, 16, 2.0), P0 + NV * 44.0, (1, 0, 0), NV) & egg_in

# ----------------------------------------------------------------- head rotation
HEAD_AX = Axis(tuple(P0), tuple(NV))
head_parts = dict(head_shell=head_shell, visor=visor, quiff=qf, cap=cap,
                  screen_L=screens[0], screen_R=screens[1],
                  int_disp=union(disp), int_hservo=head_servo + head_hub)
for k in head_parts:
    head_parts[k] = head_parts[k].rotate(HEAD_AX, PZ["head"])

# ----------------------------------------------------------------- groups
groups = dict(
    body_shell=body_shell,
    head_shell=head_parts["head_shell"],
    visor=head_parts["visor"],
    cap=head_parts["cap"],
    lens=lens,
    screen_L=head_parts["screen_L"],
    screen_R=head_parts["screen_R"],
    haunch=union([l["turret"] for l in legs]),
    foot=union([l["foot"] for l in legs]),
    sole=union([l["sole"] for l in legs]),
    int_servo=union([l["kservo"] for l in legs] + [l["yservo"] for l in legs]),
    int_horn=union([l["khorn"] for l in legs] + [l["yhorn"] for l in legs]),
    int_hservo=head_parts["int_hservo"],
    int_cells=union(cells),
    int_frame=deck + collars + posts + post_head + sled,
    int_elec=mcu + bucks + charger + bms + imu + tof,
    int_disp=head_parts["int_disp"],
)

# ground: lowest point
zmin = min(g.bounding_box().min.Z for k, g in groups.items() if not k.startswith("int_"))
CZ = -zmin
info = {"pose": POSE, "CZ": CZ, "parts": {}}
for k, g in groups.items():
    g = Pos(0, 0, CZ) * g
    bb = g.bounding_box()
    info["parts"][k] = dict(vol=g.volume, cx=g.center().X, cy=g.center().Y, cz=g.center().Z,
                            bb=[bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z])
    fine = k in ("visor", "head_shell", "screen_L", "screen_R", "body_shell", "cap")
    export_stl(g, os.path.join(OUT, k + ".stl"), tolerance=0.012 if fine else 0.03,
               angular_tolerance=0.04 if fine else 0.08)
allb = [info["parts"][k]["bb"] for k in info["parts"] if not k.startswith("int_")]
info["overall"] = [min(b[0] for b in allb), min(b[1] for b in allb), min(b[2] for b in allb),
                   max(b[3] for b in allb), max(b[4] for b in allb), max(b[5] for b in allb)]
info["seam"] = dict(alpha=ALPHA, d=D_SEAM, front_z=D_SEAM * math.cos(math.radians(ALPHA)) - math.sqrt(R * R - D_SEAM ** 2) * math.sin(math.radians(ALPHA)),
                    back_z=D_SEAM * math.cos(math.radians(ALPHA)) + math.sqrt(R * R - D_SEAM ** 2) * math.sin(math.radians(ALPHA)))
json.dump(info, open(os.path.join(OUT, "parts.json"), "w"), indent=1)
print(json.dumps(dict(CZ=CZ, overall=info["overall"], seam=info["seam"]), indent=1))
