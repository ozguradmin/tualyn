#!/usr/bin/env python3
"""Concept B "Tarcin" - pocket red-panda quadruped (OpenCat-style sagittal legs).

Units mm, Z up, robot faces -Y, origin on the ground under the body centre.
Usage: python3 -I model.py [pose.json] [outdir]
  pose.json keys (all optional, degrees):
    legs: {"FR":[a,b], "FL":[a,b], "HR":[a,b], "HL":[a,b]}  a = thigh angle from -Z toward +Y,
          b = shin angle from -Z toward +Y (absolute).  Knee = b - a.
    pan, roll: head pan (about Z) and head roll (about Y)
    body: [dx,dy,dz,roll,pitch] extra body offset (for non-standing poses; default auto-ground)
    internals: true -> also export servo/battery/board envelopes
"""
import json, math, os, sys
from build123d import *

# ----------------------------------------------------------------- parameters
P = dict(
    hip_y=32.0,          # hips at y = -32 (front) / +32 (hind)
    L1=40.0,             # hip axis -> knee axis (set by two stacked MG90S in the pod)
    L2=34.0,             # knee axis -> paw sole (shin straight down)
    body_hw=19.5, body_hh=24.0, body_hl=49.0, body_p=2.6,
    pod_x0=28.6, pod_x1=58.0, pod_w=21.0,
    shin_x0=21.0, shin_x1=25.0,
    head_c=(0.0, -53.0, 0.0),          # z filled in relative to hip height below
    head_hw=44.0, head_hd=34.0, head_hh=28.5, head_p=2.7,
    eye_dx=20.0, eye_toe=13.0,
    wall=1.6,
)
HIP_Z_NOM = 62.0      # hip height in the nominal stand (recomputed to put paws on z=0)

STAND = {"FR": [30, -36], "FL": [30, -36], "HR": [-30, 36], "HL": [-30, 36]}


# ----------------------------------------------------------------- primitives
def se_profile_pts(r, h, p, n=56):
    pts = []
    for i in range(n + 1):
        t = math.pi * i / n
        s, c = math.sin(t), math.cos(t)
        pts.append((r * abs(s) ** (2 / p), h * math.copysign(abs(c) ** (2 / p), c)))
    return pts


def se_rev(r, h, p):
    """Superellipse profile (exponent p) revolved about Z: radius r, half-height h."""
    pts = se_profile_pts(r, h, p)
    with BuildPart() as bp:
        with BuildSketch(Plane.XZ):
            with BuildLine():
                Spline(*pts, tangents=[(1, 0), (-1, 0)])
                Line(pts[-1], pts[0])
            make_face()
        revolve(axis=Axis.Z)
    return bp.part


def blob(hw, hd, hh, p):
    """Rounded 'marshmallow' solid: half sizes x, y, z; vertical profile exponent p."""
    r = max(hw, hd)
    s = se_rev(r, hh, p)
    return scale(s, by=(hw / r, hd / r, 1.0))


def ellipsoid(a, b, c):
    return scale(Sphere(1.0), by=(a, b, c))


def place(obj, origin, x_dir, z_dir):
    return Plane(origin=origin, x_dir=x_dir, z_dir=z_dir).location * obj


# ----------------------------------------------------------------- off-the-shelf envelopes
def mg90s(tabs=False):
    """MG90S envelope. Local: case bottom z=0, shaft on +z at (0,0); case spans x -5.9..16.9."""
    case = Pos(5.5, 0, 22.7 / 2) * Box(22.8, 12.2, 22.7)
    s = case
    if tabs:
        s += Pos(5.5, 0, 17.05) * Box(32.5, 12.2, 2.5)
    s += Pos(0, 0, 22.7) * Cylinder(5.9, 4.3, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s += Pos(7.0, 0, 22.7) * Cylinder(3.0, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s += Pos(0, 0, 27.0) * Cylinder(2.4, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s


def sg90():
    case = Pos(5.2, 0, 22.5 / 2) * Box(22.2, 11.8, 22.5)
    s = case + Pos(5.2, 0, 16.5) * Box(32.2, 11.8, 2.5)
    s += Pos(0, 0, 22.5) * Cylinder(5.8, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s += Pos(0, 0, 26.5) * Cylinder(2.4, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s


def horn(r=9.5, t=1.6):
    return Cylinder(3.6, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN)) + \
        Pos(0, 0, 0) * Cylinder(r, t, align=(Align.CENTER, Align.CENTER, Align.MIN))


# ----------------------------------------------------------------- leg
def leg(side, end, a, b, hip):
    """Returns dict material->solid for one leg. side=+1 (x>0) / -1. hip=(x,y,z) of hip axis on centreline."""
    L1, L2 = P["L1"], P["L2"]
    x0, x1, w = P["pod_x0"], P["pod_x1"], P["pod_w"]
    # ---- pod (thigh) in leg frame: hip at origin, leg along -Z, built for +x side
    with BuildPart() as pod:
        with BuildSketch(Plane.YZ.offset(x0)):
            with Locations((0, -L1 / 2)):
                SlotCenterToCenter(L1 - 1.2, w, rotation=90)
        extrude(amount=x1 - x0)
        outer = pod.faces().sort_by(Axis.X)[-1]
        fillet(outer.edges(), radius=6.0)
        inner = pod.faces().sort_by(Axis.X)[0]
        fillet(inner.edges(), radius=2.5)
    pod_s = pod.part
    # hub collars hiding the horns (hip and knee) on the inner side of the pod
    collar = Pos(25.3, 0, 0) * Rot(0, 90, 0) * Cylinder(11.5, x0 - 25.3 + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    collar = fillet(collar.edges().sort_by(Axis.X)[0:1], 1.2)
    pod_s = pod_s + collar + Pos(0, 0, -L1) * collar
    # shallow decorative "paw-print" disk on the outer face (accent inlay)
    inlay = Pos(x1 - 0.2, 0, -L1 * 0.55) * Rot(0, 90, 0) * Cylinder(5.2, 0.6, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # ---- servos in the pod (for x-ray / fit checks)
    hip_servo = place(mg90s(), (55.3, 0, 0), (0, 0, -1), (-1, 0, 0))
    knee_servo = place(mg90s(), (55.3, 0, -L1), (0, 0, 1), (-1, 0, 0))
    hip_horn = Pos(25.0, 0, 0) * Rot(0, 90, 0) * horn()
    knee_horn = Pos(25.0, 0, -L1) * Rot(0, 90, 0) * horn()

    # ---- shin in its own frame (knee at origin, along -Z)
    sx0, sx1 = P["shin_x0"], P["shin_x1"]
    with BuildPart() as sh:
        with BuildSketch(Plane.YZ.offset(sx0)):
            with BuildLine():
                l1 = CenterArc((0, 0), 9.0, 0, 180)
                l2 = Line(l1 @ 1, (-6.0, -(L2 - 9)))
                l3 = Line((6.0, -(L2 - 9)), l1 @ 0)
                Line(l2 @ 1, l3 @ 0)
            make_face()
        extrude(amount=sx1 - sx0)
        fillet(sh.edges().filter_by(Axis.X, reverse=True).group_by(Axis.X)[0], 1.2)
        fillet(sh.edges().filter_by(Axis.X, reverse=True).group_by(Axis.X)[-1], 1.2)
    shin_s = sh.part
    paw = Pos((sx0 + sx1) / 2 + 0.5, 0, -(L2 - 7.5)) * ellipsoid(9.5, 11.0, 7.5)

    # ---- transform to world
    knee_local = Vector(0, 0, -L1)
    T_thigh = Pos(*hip) * Rot(a, 0, 0)
    kn = T_thigh * Pos(0, 0, -L1)
    knee_w = Vector(hip[0], hip[1] + L1 * math.sin(math.radians(a)), hip[2] - L1 * math.cos(math.radians(a)))
    T_shin = Pos(*knee_w) * Rot(b, 0, 0)
    out = {
        "pod": T_thigh * pod_s,
        "pod_inlay": T_thigh * inlay,
        "shin": T_shin * shin_s,
        "paw": T_shin * paw,
        "int_servo": T_thigh * (hip_servo + knee_servo),
        "int_horn": T_thigh * hip_horn + T_shin * Pos(0, 0, 0) * (Pos(0, 0, L1) * Pos(0, 0, -L1) * Pos(25.0, 0, 0) * Rot(0, 90, 0) * horn()),
    }
    if side < 0:
        out = {k: mirror(v, Plane.YZ) for k, v in out.items()}
    return out, knee_w


# ----------------------------------------------------------------- head
def head_parts(zc):
    hw, hd, hh, p = P["head_hw"], P["head_hd"], P["head_hh"], P["head_p"]
    cx, cy, _ = P["head_c"]
    C = Vector(cx, cy, zc)
    outer = Pos(C) * blob(hw, hd, hh, p)
    inner = Pos(C) * blob(hw - 1.8, hd - 1.8, hh - 1.8, p)
    shell = outer - inner
    z_eye = zc - 3.0          # eye line slightly below head centre (baby schema)
    # ---- mask outline (front projection), raccoon / red-panda mask
    with BuildSketch(Plane.XZ) as mk:
        for sx in (-1, 1):
            with Locations((sx * P["eye_dx"], z_eye)):
                Ellipse(20.5, 18.5)
        with Locations((0, z_eye + 1.0)):
            Rectangle(2 * P["eye_dx"], 22)
        with Locations((0, z_eye - 19.5)):
            Circle(8.5, mode=Mode.SUBTRACT)
        with Locations((0, z_eye + 21.0)):
            Ellipse(9, 6, mode=Mode.SUBTRACT)
    mask_prism = extrude(mk.sketch, amount=120, both=True)
    front = Pos(0, cy - 60, zc) * Box(200, 120, 200)          # y < cy  (front half only)
    mask_prism = mask_prism & front
    mask = (outer & mask_prism) - Pos(C) * blob(hw - 2.4, hd - 2.4, hh - 2.4, p)
    groove = offset(mk.sketch, 0.6)
    groove_prism = extrude(groove, amount=120, both=True) & front
    # ---- cream face plate: cheeks + muzzle (front lower region)
    with BuildSketch(Plane.XZ) as fp:
        with Locations((0, z_eye - 4)):
            Ellipse(41, 23)
        with Locations((0, z_eye + 26)):        # brow patches (red-panda eyebrows)
            pass
    face_prism = extrude(fp.sketch, amount=120, both=True) & (Pos(0, cy - 60 + 8, zc) * Box(200, 120, 200))
    face = (shell & face_prism) - groove_prism
    with BuildSketch(Plane.XZ) as fg:
        with Locations((0, z_eye - 4)):
            Ellipse(41.6, 23.6)
    face_groove = extrude(fg.sketch, amount=120, both=True) & (Pos(0, cy - 60 + 8, zc) * Box(200, 120, 200))
    main = shell - face_groove - groove_prism
    face = face - groove_prism
    # brow dots (cream) above each eye
    brows = None
    # ---- eye windows: holes through mask, toe-out
    eyes, windows, screens = [], [], []
    for sx in (-1, 1):
        ex = sx * P["eye_dx"]
        # find surface y at (ex, z_eye)
        ray_y = cy - hd - 5
        # approximate surface point by bisection on 'outer' containment
        lo, hi = cy - hd - 2, cy
        for _ in range(30):
            mid = (lo + hi) / 2
            if outer.is_inside(Vector(ex, mid, z_eye)):
                hi = mid
            else:
                lo = mid
        ys = hi
        toe = sx * P["eye_toe"]
        n = Vector(math.sin(math.radians(toe)), -math.cos(math.radians(toe)), 0)      # outward normal
        # cylinder cut along -n
        hole = Pos(ex, ys, z_eye) * Rot(0, 0, toe) * Rot(90, 0, 0) * Cylinder(16.6, 30)
        windows.append(hole)
        # emissive eye disc (stands for 2 mm smoked acrylic + GC9A01 glass behind it)
        disc_c = Vector(ex, ys, z_eye) - n * 2.2
        disc = Pos(disc_c) * Rot(0, 0, toe) * Rot(90, 0, 0) * Cylinder(16.6, 0.6)
        eyes.append(disc)
        # GC9A01 module envelope (PCB dia 38 + glass + header) behind the disc
        mod = Pos(disc_c - n * 1.0) * Rot(0, 0, toe) * Rot(90, 0, 0) * (
            Pos(0, 0, -3.5) * Cylinder(19.0, 5.0) + Pos(0, -16, -9) * Box(12, 9, 8))
        screens.append(mod)
    for h in windows:
        mask = mask - h
        main = main - h
        face = face - h
    # recessed dark bezel ring inside each window (black PLA cup) so the module edge is never seen
    cups = []
    for sx, e in zip((-1, 1), eyes):
        pass
    # ---- nose (glossy black)
    lo, hi = cy - hd - 2, cy
    zn = z_eye - 17.5
    for _ in range(30):
        mid = (lo + hi) / 2
        if outer.is_inside(Vector(0, mid, zn)):
            hi = mid
        else:
            lo = mid
    nose = Pos(0, hi + 1.2, zn) * ellipsoid(4.6, 3.2, 3.3)
    # ---- ears
    ears_o, ears_i = [], []
    for sx in (-1, 1):
        ear_pts = [(-12, -4), (-11.5, 4), (-7.5, 11.5), (-2.2, 17.4), (0, 18.4), (2.2, 17.4), (7.5, 11.5), (11.5, 4), (12, -4), (0, -7)]
        def ear_sec(k, y):
            pts = [(px * k, pz * k + (1 - k) * 4.0) for px, pz in ear_pts]
            w = Spline(*[(px, y, pz) for px, pz in pts], periodic=True)
            return Face(Wire([w]))
        ear_part = loft([ear_sec(0.70, -3.2), ear_sec(0.93, -2.2), ear_sec(1.0, 0.0), ear_sec(0.93, 2.2), ear_sec(0.70, 3.2)])
        class _E: pass
        ear = _E(); ear.part = ear_part
        ei_pts = [(-6.8, 1.0), (-5.4, 7.5), (-1.4, 13.4), (0, 14.2), (1.4, 13.4), (5.4, 7.5), (6.8, 1.0), (0, -1.5)]
        with BuildPart() as eari:
            with BuildSketch(Plane.XZ):
                with BuildLine():
                    Spline(*ei_pts, periodic=True)
                make_face()
            extrude(amount=1.6)
            fillet(eari.edges().group_by(Axis.Y)[0], 0.7)
        T = Pos(sx * 26.5, cy + 4.0, zc + hh - 6.5) * Rot(0, sx * 24, 0) * Rot(-12, 0, 0)
        ears_o.append(T * (ear.part - Pos(0, -3.3, 0) * eari.part.translate((0, 0, 0))))
        ears_i.append(T * Pos(0, -2.0, 0) * eari.part)
    return dict(head_main=main, head_face=face, mask=mask, eye_L=eyes[1], eye_R=eyes[0],
                nose=nose, ear_outer=ears_o[0] + ears_o[1], ear_inner=ears_i[0] + ears_i[1],
                int_eyes=screens[0] + screens[1]), C, z_eye


# ----------------------------------------------------------------- body
def body_parts(zc):
    hw, hh, hl, p = P["body_hw"], P["body_hh"], P["body_hl"], P["body_p"]
    s = se_rev(hh, hl, p)                       # axis along Z, radius hh
    s = Rot(90, 0, 0) * s                       # axis along Y
    s = scale(s, by=(hw / hh, 1, 1))
    outer = Pos(0, 0, zc) * s
    s_in = Rot(90, 0, 0) * se_rev(hh - P["wall"], hl - P["wall"], p)
    inner = Pos(0, 0, zc) * scale(s_in, by=((hw - P["wall"]) / (hh - P["wall"]), 1, 1))
    shell = outer - inner
    split_z = zc - 5.0
    top = shell & Pos(0, 0, split_z + 0.4 + 100) * Box(300, 300, 200)
    belly = shell & Pos(0, 0, split_z - 0.4 - 100) * Box(300, 300, 200)
    # hip hub posts (charcoal, they stay with the body)
    posts = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            pz = Pos(sx * (hw - 1.5), sy * P["hip_y"], zc) * Rot(0, 90, 0) * Cylinder(10.0, 2 * (24.9 - (hw - 1.5)) if False else 0.1)
    post_list = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x_a, x_b = hw - 3.0, 24.9
            c = Pos(sx * (x_a + x_b) / 2, sy * P["hip_y"], zc) * Rot(0, 90, 0) * Cylinder(9.5, x_b - x_a)
            post_list.append(c)
    posts = post_list[0] + post_list[1] + post_list[2] + post_list[3]
    return dict(body_top=top, body_belly=belly, hub=posts), outer, inner


# ----------------------------------------------------------------- tail
def tail_parts(zc):
    # centre-line: quadratic Bezier from base (inside body rear) up and back, curling forward
    p0 = Vector(0, 40, zc + 8)
    p1 = Vector(0, 64, zc + 22)
    p2 = Vector(0, 54, zc + 50)
    def bez(t):
        return p0 * (1 - t) ** 2 + p1 * (2 * t * (1 - t)) + p2 * t ** 2
    def dbez(t):
        return (p1 - p0) * (2 * (1 - t)) + (p2 - p1) * (2 * t)
    ts = [i / 9 for i in range(10)]
    radii = [6.5, 7.8, 9.0, 9.8, 10.0, 9.6, 8.7, 7.3, 5.4, 2.6]
    secs = []
    for t, r in zip(ts, radii):
        c, d = bez(t), dbez(t).normalized()
        pl = Plane(origin=c, z_dir=d)
        secs.append(pl * Circle(r))
    tail = loft(secs)
    tail = tail + Pos(bez(1.0) - dbez(1.0).normalized() * 0.0) * Sphere(2.6)
    # ring split into alternating bands (cinnamon / cream)
    bands = [(0.0, 0.30), (0.30, 0.47), (0.47, 0.64), (0.64, 0.80), (0.80, 1.01)]
    out_a, out_b = [], []
    for i, (t0, t1) in enumerate(bands):
        def slab(t, keep_after):
            c, d = bez(min(t, 1.0)), dbez(min(t, 1.0)).normalized()
            pl = Plane(origin=c, z_dir=d)
            return pl * Pos(0, 0, 50 if keep_after else -50) * Box(80, 80, 100)
        piece = tail & slab(t0 + (0.004 if i else -1), True) if i else tail
        if t1 < 1.0:
            piece = piece & slab(t1 - 0.004, False)
        (out_a if i % 2 == 0 else out_b).append(piece)
    A = out_a[0]
    for q in out_a[1:]:
        A = A + q
    B = out_b[0]
    for q in out_b[1:]:
        B = B + q
    return dict(tail_a=A, tail_b=B)


# ----------------------------------------------------------------- internals of the body
def body_internals(zc, inner):
    parts = {}
    # 2S 14500 Li-ion, side by side, low in the belly, slightly rearward (CoM)
    cells = None
    for sx in (-1, 1):
        c = Pos(sx * 7.3, 6.0, zc - 24 + 1.6 + 7.4) * Rot(90, 0, 0) * Cylinder(7.1, 50.5)
        cells = c if cells is None else cells + c
    parts["int_battery"] = cells
    # PCA9685 16-ch servo driver (62.5 x 25.4, headers removed, wires soldered) standing on edge
    parts["int_pca"] = Pos(0, 4.0, zc + 6.5) * Box(62.5, 3.5, 25.4).rotate(Axis.Z, 90) if False else Pos(0, 6.0, zc + 6.0) * Box(3.2, 62.5, 22.0)
    # bucks (3 x MP1584 22x17x4), BMS, USB-C 2S charger, BMI160, VL53L0X
    parts["int_buck"] = Pos(-10.5, -14.0, zc + 4.0) * Box(4.0, 22.0, 17.0) + Pos(10.5, -14.0, zc + 4.0) * Box(4.0, 22.0, 17.0) \
        + Pos(-10.5, 24.0, zc + 4.0) * Box(4.0, 22.0, 17.0)
    parts["int_charger"] = Pos(10.5, 25.0, zc + 4.0) * Box(4.0, 22.0, 15.0)
    parts["int_imu"] = Pos(0, -10.0, zc - 7.5) * Box(13.0, 18.0, 2.5)
    parts["int_tof"] = Pos(0, -43.0, zc - 14.0) * Rot(-45, 0, 0) * Box(13.0, 2.5, 18.0)
    return parts


# ----------------------------------------------------------------- assembly
def build(pose):
    legs = dict(STAND)
    legs.update(pose.get("legs", {}))
    pan, roll = pose.get("pan", 0.0), pose.get("roll", 0.0)
    # find hip height that puts the lowest paw at z=0 (nominal stand), unless body override
    hip_z = HIP_Z_NOM
    groups = {}
    def add(k, s):
        if s is None:
            return
        groups.setdefault(k, []).append(s)

    leg_out = []
    for name, (a, b) in legs.items():
        side = 1 if name[1] == "R" else -1      # R = +x
        sy = -1 if name[0] == "F" else 1
        o, kn = leg(1, name[0], a, b, (0, sy * P["hip_y"], hip_z))
        if side < 0:
            o = {k: mirror(v, Plane.YZ) for k, v in o.items()}
        leg_out.append(o)
    b, outer, inner = body_parts(hip_z)
    hz = hip_z + 46.5
    h, C, z_eye = head_parts(hz)
    t = tail_parts(hip_z)
    # neck: pan servo (SG90) vertical in the chest, roll servo (MG90S) in the head, axis along Y
    neck_pivot = Vector(0, P["head_c"][1] + 8.0, hip_z + 30.0)
    neck = Pos(0, P["head_c"][1] + 10.0, hip_z + 26.0) * Cylinder(7.5, 10.0)
    Th = Pos(neck_pivot) * Rot(0, 0, pan) * Rot(0, roll, 0) * Pos(-neck_pivot)
    h = {k: Th * v for k, v in h.items()}
    ints = body_internals(hip_z, inner)
    ints["int_neck_servos"] = place(sg90(), (0, P["head_c"][1] + 14.0, hip_z + 0.5), (0, 1, 0), (0, 0, 1)) + \
        Th * place(mg90s(), (0, P["head_c"][1] + 22.0, hip_z + 34.0), (1, 0, 0), (0, -1, 0))
    for o in leg_out:
        for k, v in o.items():
            add(k, v)
    for k, v in b.items():
        add(k, v)
    for k, v in h.items():
        add(k, v)
    for k, v in t.items():
        add(k, v)
    add("neck", neck)
    for k, v in ints.items():
        add(k, v)
    merged = {}
    for k, lst in groups.items():
        c = Compound(children=[s for s in lst])
        merged[k] = c
    # ground: shift so min z of visible parts = 0
    vis = [v for k, v in merged.items() if not k.startswith("int_")]
    zmin = min(v.bounding_box().min.Z for v in vis)
    merged = {k: Pos(0, 0, -zmin) * v for k, v in merged.items()}
    return merged, dict(hip_z=hip_z - zmin, zmin=zmin)


if __name__ == "__main__":
    pose = {}
    if len(sys.argv) > 1 and sys.argv[1].endswith(".json"):
        pose = json.load(open(sys.argv[1]))
    outdir = sys.argv[2] if len(sys.argv) > 2 else "stl"
    os.makedirs(outdir, exist_ok=True)
    parts, info = build(pose)
    allbb = None
    for k, v in parts.items():
        export_stl(v, os.path.join(outdir, k + ".stl"), tolerance=0.03, angular_tolerance=0.08)
    vis = Compound(children=[v for k, v in parts.items() if not k.startswith("int_")])
    bb = vis.bounding_box()
    info["bbox"] = [round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1)]
    print(json.dumps(info))
