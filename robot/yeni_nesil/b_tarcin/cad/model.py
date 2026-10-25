#!/usr/bin/env python3
"""Concept B "Tarcin" - pocket red-panda quadruped (OpenCat-style sagittal legs, 2-servo leg pods).

Units mm, Z up, robot faces -Y, origin on the ground under the body centre.
Usage: python3 -I model.py [pose.json] [outdir]
  pose.json keys (all optional, degrees):
    legs: {"FR":[a,b], "FL":[a,b], "HR":[a,b], "HL":[a,b]}
          a = thigh angle from -Z toward +Y, b = shin angle from -Z toward +Y (absolute). knee = b - a.
          Names use model sides: R = +x, L = -x.
    pan, roll: head pan (about Z) and head roll (about Y)
    world: [rot_about_Y_deg, dz]  rigid roll of the whole robot (for lying / recovery poses)
    check: true -> run clearance / containment / mass checks and write checks.json
"""
import json, math, os, sys
from build123d import *

# ----------------------------------------------------------------- parameters
P = dict(
    hip_y=32.0,          # hip axes at y = -32 (front) / +32 (hind)
    L1=40.0,             # hip axis -> knee axis (two stacked MG90S in the pod)
    L2=34.0,             # knee axis -> paw sole (shin straight)
    body=(19.5, 49.0, 24.0),           # half width x, half length y, half height z
    pod_c=44.2, pod_a=15.8, pod_b=11.5, pod_c_len=35.5, pod_x0=28.6,
    shin_x0=20.8, shin_x1=25.2,
    head_y=-44.0, head_dz=40.5,        # head centre relative to hip height
    face_cut=12.5,
    tail_scale=1.5,                    # long bushy tail = self-righting lever (MuJoCo-verified length)
    head_ev_top=1.8,                   # crown exponent (<2 = domed crown: robot cannot rest on its head when upside down)
    head=(44.0, 33.0, 27.5),           # half w, d, h
    eye_dx=19.6, eye_toe=0.0, eye_r=15.8,
    neck_y=-32.0, neck_dz=28.0,        # pan axis y, roll axis height above hip
    wall=1.6,
)
HIP_Z = 68.9
STAND = {"FR": [20, -24], "FL": [20, -24], "HR": [-20, 24], "HL": [-20, 24]}
PAW_NOM = {"F": -24, "H": 24}          # shin angle at which the sole is flat


# ----------------------------------------------------------------- primitives
def sq_wire(a, b, e, z, n=56):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        pts.append((a * math.copysign(abs(c) ** (2 / e), c), b * math.copysign(abs(s) ** (2 / e), s), z))
    return Wire([Spline(*pts, periodic=True)])


def superellipsoid(a, b, c, eh=2.0, ev=2.0, n=26, ev_top=None):
    """Half sizes a (x), b (y), c (z); eh = horizontal squircle exponent, ev = vertical exponent
    (ev_top: separate vertical exponent for the upper half, e.g. a domed crown)."""
    secs = []
    for i in range(n + 1):
        t = -math.pi / 2 + math.pi * i / n
        e = ev_top if (ev_top and math.sin(t) > 0) else ev
        z = c * math.copysign(abs(math.sin(t)) ** (2 / e), math.sin(t))
        s = abs(math.cos(t)) ** (2 / e)
        if i in (0, n):
            secs.append(Vertex(0, 0, z))
        else:
            secs.append(Face(sq_wire(a * s, b * s, eh, z)))
    return loft(secs)


def ellipsoid(a, b, c):
    return scale(Sphere(1.0), by=(a, b, c))


def place(obj, origin, x_dir, z_dir):
    return Plane(origin=origin, x_dir=x_dir, z_dir=z_dir).location * obj


def union(lst):
    out = lst[0]
    for s in lst[1:]:
        out = out + s
    return out


def surface_y(solid, x, z, y_lo, y_hi):
    """first y (coming from -Y) where the line (x, *, z) enters the solid"""
    lo, hi = y_lo, y_hi
    for _ in range(32):
        mid = (lo + hi) / 2
        if solid.is_inside(Vector(x, mid, z)):
            hi = mid
        else:
            lo = mid
    return hi


# ----------------------------------------------------------------- off-the-shelf envelopes
def mg90s():
    """MG90S envelope, tabs trimmed (pod clamps the case). Local: case bottom z=0, shaft at origin on +z."""
    s = Pos(5.5, 0, 22.7 / 2) * Box(22.8, 12.2, 22.7)
    s += Pos(0, 0, 22.7) * Cylinder(5.9, 4.3, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s += Pos(7.0, 0, 22.7) * Cylinder(3.0, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s += Pos(0, 0, 27.0) * Cylinder(2.4, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s


def sg90():
    s = Pos(5.2, 0, 22.5 / 2) * Box(22.2, 11.8, 22.5) + Pos(5.2, 0, 16.5) * Box(32.2, 11.8, 2.5)
    s += Pos(0, 0, 22.5) * Cylinder(5.8, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s += Pos(0, 0, 26.5) * Cylinder(2.4, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s


def micro4g():
    """4 g digital micro servo (Emax ES9051 / E-Sky 002279 class), tabs trimmed. Shaft at origin on +z."""
    s = Pos(5.5, 0, 8.0) * Box(20.0, 8.6, 16.0)
    s += Pos(0, 0, 16.0) * Cylinder(4.2, 2.8, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s += Pos(0, 0, 18.8) * Cylinder(2.0, 2.4, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s


def horn():
    return Cylinder(3.6, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN)) + \
        Cylinder(9.5, 1.6, align=(Align.CENTER, Align.CENTER, Align.MIN))


# ----------------------------------------------------------------- leg (built for +x side)
_CACHE = {}


def pod_solid():
    if "pod" in _CACHE:
        return _CACHE["pod"]
    L1 = P["L1"]
    a, b, c = P["pod_a"], P["pod_b"], P["pod_c_len"]
    outer = Pos(P["pod_c"], 0, -L1 / 2) * superellipsoid(a, b, c, eh=3.0, ev=3.4)
    outer = outer & Pos(P["pod_x0"] + 50, 0, -L1 / 2) * Box(100, 100, 200)
    try:
        outer = fillet(outer.edges().group_by(Axis.X)[0], 2.0)
    except Exception as e:
        print("pod fillet skipped:", e)
    inner = Pos(P["pod_c"], 0, -L1 / 2) * superellipsoid(a - P["wall"], b - P["wall"], c - P["wall"], eh=3.0, ev=3.4)
    collar = Pos(25.4, 0, 0) * Rot(0, 90, 0) * Cylinder(11.0, P["pod_x0"] - 25.4 + 1.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    collar = fillet(collar.edges().sort_by(Axis.X)[0:1], 1.0)
    hip_collar = Pos(21.2, 0, 0) * Rot(0, 90, 0) * Cylinder(11.0, P["pod_x0"] - 21.2 + 1.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    hip_collar = fillet(hip_collar.edges().sort_by(Axis.X)[0:1], 1.5)
    full = outer + hip_collar + Pos(0, 0, -L1) * collar
    zs = -L1 * 0.66                                   # colour split: cinnamon thigh / charcoal "sock"
    up = full & Pos(0, 0, zs + 0.35 + 100) * Box(300, 300, 200)
    low = full & Pos(0, 0, zs - 0.35 - 100) * Box(300, 300, 200)
    _CACHE["pod"] = (full, outer, inner, up, low)
    return _CACHE["pod"]


def shin_solid(end):
    key = "shin" + end
    if key in _CACHE:
        return _CACHE[key]
    L2 = P["L2"]
    x0, x1 = P["shin_x0"], P["shin_x1"]
    zA = -(L2 - 10.5)
    with BuildPart() as sh:
        with BuildSketch(Plane.YZ.offset(x0)):
            Circle(9.0)
            with Locations((0, zA)):
                Circle(6.4)
        extrude(amount=x1 - x0)
        with BuildSketch(Plane.YZ.offset(x0)):
            with BuildLine():
                Polyline((-8.95, 0), (-6.35, zA), (6.35, zA), (8.95, 0), close=True)
            make_face()
        extrude(amount=x1 - x0)
    shin = sh.part
    try:
        shin = fillet(shin.edges().group_by(Axis.X)[0] + shin.edges().group_by(Axis.X)[-1], 1.5)
    except Exception as e:
        print("shin fillet skipped:", e)
    pw = superellipsoid(10.0, 12.5, 7.2, eh=2.3, ev=2.4)
    pw = pw & Pos(0, 0, -4.6 + 50) * Box(60, 60, 100)            # flat sole at z=-4.6
    pw = Pos(0, -1.5, 0) * pw
    pawc = Vector((x0 + x1) / 2 + 0.3, 0, -(L2 - 4.6))
    paw = Pos(pawc) * Rot(-PAW_NOM[end], 0, 0) * pw
    _CACHE[key] = (shin, paw)
    return _CACHE[key]


def leg(end, a, b, hip):
    L1 = P["L1"]
    full, outer, inner, up, low = pod_solid()
    shin, paw = shin_solid(end)
    hip_servo = place(mg90s(), (55.3, 0, 0), (0, 0, -1), (-1, 0, 0))
    knee_servo = place(mg90s(), (55.3, 0, -L1), (0, 0, 1), (-1, 0, 0))
    case = Pos(5.5, 0, 22.7 / 2) * Box(22.8, 12.2, 22.7)
    hrn = Pos(25.0, 0, 0) * Rot(0, 90, 0) * horn()
    T_thigh = Pos(*hip) * Rot(a, 0, 0)
    knee_w = Vector(hip[0], hip[1] + L1 * math.sin(math.radians(a)), hip[2] - L1 * math.cos(math.radians(a)))
    T_shin = Pos(knee_w) * Rot(b, 0, 0)
    return {
        "pod": T_thigh * up,
        "pod_low": T_thigh * low,
        "shin": T_shin * shin,
        "paw": T_shin * paw,
        "int_servo": T_thigh * (hip_servo + knee_servo),
        "int_horn": T_thigh * hrn + T_shin * hrn,
        "_pod_inner": T_thigh * inner,
        "_servo_cases": T_thigh * (place(case, (55.3, 0, 0), (0, 0, -1), (-1, 0, 0)) +
                                   place(case, (55.3, 0, -L1), (0, 0, 1), (-1, 0, 0))),
    }


# ----------------------------------------------------------------- head
def head_outer_solid(C, grow=0.0, flat=True):
    """Rounded head with a flat face plane (the flat 2 mm smoked-acrylic visor sits in it)."""
    hw, hd, hh = P["head"]
    s = Pos(C) * superellipsoid(hw + grow, hd + grow, hh + grow, eh=2.8, ev=2.55, ev_top=P["head_ev_top"])
    if flat:
        yf = C.Y - hd + P["face_cut"] - grow
        s = s & Pos(0, yf + 100, C.Z) * Box(300, 200, 300)
    return s


def head_parts(C):
    hw, hd, hh = P["head"]
    cx, cy, zc = C
    yf = cy - hd + P["face_cut"]                 # flat face plane
    outer = head_outer_solid(C)
    try:
        outer_f = fillet(outer.edges().filter_by(lambda e: abs(e.center().Y - yf) < 0.2), 3.0)
        if outer_f.is_valid and abs(outer_f.volume - outer.volume) < 500:
            outer = outer_f
    except Exception as e:
        print("face fillet skipped:", e)
    inner = head_outer_solid(C, -1.6)
    shell = outer - inner
    z_eye = zc - 2.5                    # eye line below head centre (45 % of head height)
    front = Pos(0, cy - 60, zc) * Box(200, 120, 200)

    def prism(sk, grow=0.0):
        s_ = offset(sk, grow) if grow else sk
        return extrude(s_, amount=150, both=True) & front

    ex0 = P["eye_dx"]
    r_e = P["eye_r"]
    with BuildSketch(Plane.XZ) as mk:                 # visor (flat 2 mm smoked acrylic), red-panda "mask" outline
        with BuildLine():
            band = [(-ex0 - r_e - 1.0, z_eye + 1), (-ex0 - 9, z_eye + 15.6), (-ex0, z_eye + 17.6), (-7, z_eye + 16.6), (0, z_eye + 16.0),
                    (7, z_eye + 16.6), (ex0, z_eye + 17.6), (ex0 + 9, z_eye + 15.6), (ex0 + r_e + 1.0, z_eye + 1),
                    (ex0 + 11, z_eye - 15.4), (ex0, z_eye - 18.0), (9.5, z_eye - 16.4), (0, z_eye - 12.2),
                    (-9.5, z_eye - 16.4), (-ex0, z_eye - 18.0), (-ex0 - 11, z_eye - 15.4)]
            Spline(*band, periodic=True)
        make_face()
    mask_sk = mk.sketch
    with BuildSketch(Plane.XZ) as fp:                 # cream muzzle + cheeks (wraps under the chin)
        with Locations((0, z_eye - 19.0)):
            Ellipse(31.0, 12.0)
    face_sk = fp.sketch
    # visor plate, flush in a 2 mm pocket of the face
    visor_plate = extrude(mask_sk, amount=2.0).translate((0, 0, 0))
    visor_plate = Pos(0, yf, 0) * Rot(0, 0, 0) * visor_plate
    # Plane.XZ normal is -Y; extrude(amount) goes along -Y, so move it back inside the face
    vb = visor_plate.bounding_box()
    visor_plate = visor_plate.translate((0, yf - vb.min.Y, 0))
    pocket = visor_plate
    groove = extrude(offset(mask_sk, 0.5), amount=2.6)
    gb = groove.bounding_box()
    groove = groove.translate((0, yf - 0.01 - gb.min.Y, 0))
    face = (shell & prism(face_sk)) - groove
    main = shell - groove - prism(face_sk, 0.5)
    face = face - groove

    eyes, screens = [], []
    for sx in (-1, 1):
        ex = sx * ex0
        hole = Pos(ex, yf, z_eye) * Rot(90, 0, 0) * Cylinder(r_e, 10)
        visor_plate = visor_plate - hole
        eyes.append(Pos(ex, yf + 0.3, z_eye) * Rot(90, 0, 0) * Cylinder(r_e - 0.03, 0.6))
        # GC9A01 module: glass (dia 35.6) right behind the acrylic, round PCB dia 38, 7-pin header on top
        g0 = yf + 2.0 + 0.3
        mod = Pos(ex, g0 + 0.8, z_eye) * Rot(90, 0, 0) * Cylinder(17.8, 1.6) +             Pos(ex, g0 + 1.6 + 2.6, z_eye) * Rot(90, 0, 0) * Cylinder(19.0, 3.6) +             Pos(ex, g0 + 9.0, z_eye + 14.5) * Box(12, 8, 6)
        screens.append(mod)
    zn = z_eye - 14.6
    nose = Pos(0, yf - 1.2, zn) * ellipsoid(4.6, 3.0, 3.2)
    zm = z_eye - 21.0
    ym = surface_y(outer, 0, zm, cy - hd - 2, cy)
    with BuildSketch(Plane.XZ) as mo:
        for dx in (-2.5, 2.5):
            with Locations((dx, zm + 0.6)):
                Circle(2.95)
                Circle(2.05, mode=Mode.SUBTRACT)
        with Locations((0, zm + 0.6 + 5.0)):
            Rectangle(20, 10, mode=Mode.SUBTRACT)
    mouth = (extrude(mo.sketch, amount=150, both=True) & front) & (outer - head_outer_solid(C, -0.6))
    face = face - mouth
    cheeks = []
    for sx in (-1, 1):
        ck = (Pos(sx * 27.5, yf - 1, z_eye - 21.0) * Rot(90, 0, 0) * scale(Cylinder(1.0, 40), by=(6.2, 4.0, 1.0)))
        cheeks.append(ck & (outer - head_outer_solid(C, -0.8)))
    for ck in cheeks:
        face = face - ck
        main = main - ck
    ear_pts = [(-14, -5), (-13.6, 4.5), (-9.0, 13.5), (-2.8, 20.6), (0, 21.6), (2.8, 20.6), (9.0, 13.5), (13.6, 4.5), (14, -5), (0, -9)]
    ei_pts = [(-8.2, 0.5), (-6.6, 8.6), (-1.8, 15.6), (0, 16.5), (1.8, 15.6), (6.6, 8.6), (8.2, 0.5), (0, -2.5)]

    def sec(pts, k, y, zoff=4.0):
        q = [(px * k, y, pz * k + (1 - k) * zoff) for px, pz in pts]
        return Face(Wire([Spline(*q, periodic=True)]))
    ear = loft([sec(ear_pts, 0.66, -3.4), sec(ear_pts, 0.92, -2.4), sec(ear_pts, 1.0, 0.0), sec(ear_pts, 0.92, 2.4), sec(ear_pts, 0.66, 3.4)])
    eari = loft([sec(ei_pts, 1.0, -1.0), sec(ei_pts, 0.9, -2.3)])
    ears_o, ears_i = [], []
    for sx in (-1, 1):
        T = Pos(sx * 27.5, cy + 3.0, zc + hh - 7.0) * Rot(0, sx * 27, 0) * Rot(-10, 0, 0)
        ears_o.append(T * (ear - Pos(0, -1.2, 0) * eari))
        ears_i.append(T * Pos(0, -0.4, 0) * eari)
    spk = Pos(0, cy + 14, zc - 4) * Rot(-90, 0, 0) * Cylinder(10.0, 4.0)
    touch = Pos(0, cy + 2, zc + hh - 3.5) * Box(15, 11, 1.6)
    touch = touch + Pos(0, cy + 14, zc + 9) * Box(22.5, 4.0, 18.0)          # head ESP32-S3 Super Mini
    return dict(head_main=main, head_face=face, mask=visor_plate, cheeks=cheeks[0] + cheeks[1], mouth=mouth,
                eye_L=eyes[1], eye_R=eyes[0], nose=nose, ear_outer=union(ears_o), ear_inner=union(ears_i),
                int_eyes=screens[0] + screens[1], int_head=spk + touch), z_eye


# ----------------------------------------------------------------- body
def body_outer_solid(zc, grow=0.0):
    a, b, c = P["body"]
    s = superellipsoid(a + grow, c + grow, b + grow, eh=2.0, ev=2.6)    # long axis on Z
    return Pos(0, 0, zc) * Rot(90, 0, 0) * s


def body_parts(zc, head_clear):
    outer = body_outer_solid(zc)
    inner = body_outer_solid(zc, -P["wall"])
    shell = outer - inner
    if head_clear is not None:
        for env in head_clear:
            cut = shell - env
            ok = cut.is_valid and cut.volume > 0.5 * shell.volume and cut.volume <= shell.volume + 1
            if ok:
                shell = cut
            else:
                print("head clearance cut skipped", cut.is_valid, round(cut.volume), round(shell.volume))
    split_z = zc - 5.0
    top = shell & Pos(0, 0, split_z + 0.4 + 100) * Box(300, 300, 200)
    belly = shell & Pos(0, 0, split_z - 0.4 - 100) * Box(300, 300, 200)
    posts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x_a, x_b = P["body"][0] - 3.0, 24.9
            posts.append(Pos(sx * (x_a + x_b) / 2, sy * P["hip_y"], zc) * Rot(0, 90, 0) * Cylinder(9.0, x_b - x_a))
    return dict(body_top=top, body_belly=belly, hub=union(posts)), outer, inner


# ----------------------------------------------------------------- tail
def tail_parts(zc):
    k = P["tail_scale"]
    z0 = zc + TAIL_AXIS[1]
    p0, p1, p2 = [Vector(v.X, v.Y, z0 + (v.Z - z0) * k) for v in (Vector(0, 46, zc - 3), Vector(0, 70, zc + 6), Vector(0, 58, zc + 46))]
    bez = lambda t: p0 * (1 - t) ** 2 + p1 * (2 * t * (1 - t)) + p2 * t ** 2
    dbez = lambda t: ((p1 - p0) * (2 * (1 - t)) + (p2 - p1) * (2 * t)).normalized()
    ts = [i / 12 for i in range(13)]
    rad = lambda t: 6.5 + 7.6 * math.sin(math.pi * 0.86 * max(t, 0.0) ** 0.6)
    secs = [Plane(origin=bez(t), z_dir=dbez(t)) * Circle(rad(t)) for t in ts]
    tip_r = rad(1.0)
    tail = loft(secs) + Pos(bez(1.0)) * Sphere(tip_r)
    bands = [(0.0, 0.36), (0.36, 0.45), (0.45, 0.60), (0.60, 0.69), (0.69, 0.82), (0.82, 0.90), (0.90, 1.5)]
    A, B = [], []
    for i, (t0, t1) in enumerate(bands):
        piece = tail
        if i:
            piece = piece & (Plane(origin=bez(t0), z_dir=dbez(t0)) * Pos(0, 0, 50 + 0.35) * Box(90, 90, 100))
        if t1 < 1.0:
            piece = piece & (Plane(origin=bez(t1), z_dir=dbez(t1)) * Pos(0, 0, -50 - 0.35) * Box(90, 90, 100))
        (A if i % 2 == 0 else B).append(piece)
    return dict(tail_a=union(A), tail_b=union(B))


# ----------------------------------------------------------------- body internals
TAIL_AXIS = (48.0, -5.0)     # tail-servo spline: y, z (rel. to hip height); axis along +Y (tail 'wiper' wag)


def body_internals(zc):
    """Body bay layout. The body holds no leg servos (all 8 live in the leg pods). It holds the battery,
    the body MCU, power, IMU, cliff ToF and the TAIL servo (MG90S, shaft along +Y out of the rump): the tail wags
    sideways AND is the roll lever for self-righting. The head-pan micro servo sits in the head."""
    d = {}
    d["int_battery"] = union([Pos(0, -8.0, zc + dz) * Rot(90, 0, 0) * Cylinder(7.1, 50.5) for dz in (-10.4, 4.0)])
    d["int_mcu"] = Pos(11.4, -9.0, zc - 1.0) * Box(4.0, 22.5, 18.0)                 # body ESP32-S3 Super Mini
    d["int_power"] = union([
        Pos(11.6, 14.0, zc - 1.0) * Box(4.2, 22.0, 17.0),          # MP1584 servo bank A (5.5 V)
        Pos(-11.6, 14.0, zc - 1.0) * Box(4.2, 22.0, 17.0),         # MP1584 servo bank B (5.5 V)
        Pos(-11.6, -9.0, zc - 1.0) * Box(4.2, 22.0, 17.0),         # MP1584 logic 5.0 V
        Pos(0, -13.0, zc + 13.4) * Box(13.0, 24.0, 2.2),           # 2S BMS on top of the cells
        Pos(11.0, -28.0, zc - 1.0) * Box(4.2, 14.0, 11.0),         # 2S USB-C charger, port through the right flank
    ])
    d["int_sensors"] = union([
        Pos(0, 6.5, zc + 13.4) * Box(13.0, 13.0, 2.5),                                   # BMI160 IMU on the spine
        Pos(0, -39.5, zc - 3.0) * Rot(-55, 0, 0) * Box(12.0, 2.5, 14.0),                 # VL53L0X cliff sensor (nose, looks down-forward)
    ])
    ty, tz = TAIL_AXIS
    d["int_tail_servo"] = place(mg90s(), (0, ty - 30.0 + 0.0, zc + tz), (0, 0, 1), (0, 1, 0))
    return d


# ----------------------------------------------------------------- assembly
def head_transform(pan, roll=0.0):
    piv_pan = Vector(0, P["neck_y"], 0)
    return Pos(piv_pan) * Rot(0, 0, pan) * Pos(-piv_pan)


def head_clearance(C):
    """Neck nook: a round seat (solid of revolution about the pan axis) cut into the body's front-top so the
    head can pan +-45 deg with >= 1.5 mm clearance. Floor sits below the head's lowest point."""
    hz = C.Z - P["head_dz"]
    R, rz, z0 = 40.0, 16.0, hz + 10.0
    nook = Pos(0, P["neck_y"], z0 + rz) * ellipsoid(R, R, rz)       # smooth saucer, no visible step
    return [nook]


def build(pose, do_check=False):
    legs = dict(STAND)
    legs.update(pose.get("legs", {}))
    pan, roll = pose.get("pan", 0.0), pose.get("roll", 0.0)
    hz = HIP_Z
    groups = {}

    def add(k, s):
        groups.setdefault(k, []).append(s)

    for name, (a, b) in legs.items():
        sy = -1 if name[0] == "F" else 1
        o = leg(name[0], a, b, (0, sy * P["hip_y"], hz))
        if name[1] == "L":
            o = {k: mirror(v, Plane.YZ) for k, v in o.items()}
        for k, v in o.items():
            add(k, v)
    C = Vector(0, P["head_y"], hz + P["head_dz"])
    bp, b_outer, b_inner = body_parts(hz, head_clearance(C))
    for k, v in bp.items():
        add(k, v)
    hp, z_eye = head_parts(C)
    Th = head_transform(pan, roll)
    for k, v in hp.items():
        add(k, Th * v)
    tail = pose.get("tail", 0.0)
    Tt = Pos(0, TAIL_AXIS[0], hz + TAIL_AXIS[1]) * Rot(0, tail, 0) * Pos(0, -TAIL_AXIS[0], -hz - TAIL_AXIS[1])
    for k, v in tail_parts(hz).items():
        add(k, Tt * v)
    add("neck", Pos(0, P["neck_y"], hz + 15.5) * Rot(0, 0, pan) * Cylinder(10.5, 9.0))
    # head-pan micro servo lives in the head: case up in the head, shaft pointing down into a horn on the neck post
    add("int_neck", Th * place(micro4g(), (0, P["neck_y"], hz + 36.5), (0, 1, 0), (0, 0, -1)))
    for k, v in body_internals(hz).items():
        add(k, v)
    merged = {k: Compound(children=lst) for k, lst in groups.items()}
    W = pose.get("world")
    if W:
        T = Pos(0, 0, W[1]) * Rot(0, W[0], 0)
        merged = {k: T * v for k, v in merged.items()}
    Q = pose.get("world_quat")          # (w, x, y, z) of the torso, e.g. from the MuJoCo recovery run
    if Q:
        w, x, y, z = Q
        R0 = (1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w))          # body x axis in world
        R2 = (2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y))          # body z axis in world
        T = Pos(0, 0, hz) * Plane(origin=(0, 0, 0), x_dir=R0, z_dir=R2).location * Pos(0, 0, -hz)
        merged = {k: T * v for k, v in merged.items()}
    vis = [v for k, v in merged.items() if not k.startswith("int_") and not k.startswith("_")]
    zmin = min(v.bounding_box().min.Z for v in vis)
    merged = {k: Pos(0, 0, -zmin) * v for k, v in merged.items()}
    info = dict(hip_z=round(hz - zmin, 2), z_eye=round(z_eye - zmin, 2))
    if do_check:
        info["checks"] = run_checks(merged, Pos(0, 0, -zmin) * b_inner, C, zmin)
    return merged, info


# ----------------------------------------------------------------- checks
PLA, TPU = 1.24, 1.21


def run_checks(m, body_inner, C, zmin):
    r = {}
    vol = lambda s: s.volume if s is not None else 0.0
    r["servo_case_outside_pod_mm3"] = round(vol(m["_servo_cases"] - m["_pod_inner"]), 1)
    keys = ["int_battery", "int_mcu", "int_power", "int_sensors", "int_tail_servo"]
    r["body_internal_outside_mm3"] = {k: round(vol(m[k] - body_inner), 1) for k in keys}
    inter = {}
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            v = vol(m[keys[i]] & m[keys[j]])
            if v > 0.01:
                inter[keys[i] + "&" + keys[j]] = round(v, 1)
    r["body_internal_interference_mm3"] = inter
    Cz = Vector(C.X, C.Y, C.Z - zmin)
    r["eye_modules_outside_head_mm3"] = round(vol(m["int_eyes"] - head_outer_solid(Cz, -1.6)), 1)
    r["visor_outside_face_mm3"] = round(vol(m["mask"] - head_outer_solid(Cz)), 1)
    head_now = head_outer_solid(Cz)
    pods = Compound(children=[m["pod"], m["pod_low"]])
    clear = {}
    for pan in (-40, -20, 0, 20, 40):
        Th = Pos(0, 0, -zmin) * head_transform(pan) * Pos(0, 0, zmin)
        clear[f"pan{pan}"] = round((Th * head_now).distance_to(pods), 2)
    r["head_to_pods_min_mm"] = clear
    body_vis = Compound(children=[m["body_top"], m["body_belly"]])
    hb = {}
    for pan in (-40, 0, 40):
        Th = Pos(0, 0, -zmin) * head_transform(pan) * Pos(0, 0, zmin)
        hb[f"pan{pan}"] = round((Th * head_now).distance_to(body_vis), 2)
    r["head_to_body_min_mm"] = hb
    shell_v = sum(vol(m[k]) for k in ("head_main", "head_face", "mask", "body_top", "body_belly"))
    pod_shell_v = vol(m["pod"]) + vol(m["pod_low"]) - vol(m["_pod_inner"])
    g = {}
    g["shells head+body (4 perimeters)"] = shell_v / 1000 * PLA
    g["leg pods shell + clamp ribs (x1.25)"] = pod_shell_v / 1000 * PLA * 1.25
    g["shins (60% eq.)"] = vol(m["shin"]) / 1000 * PLA * 0.6
    g["paws TPU (45% eq.)"] = vol(m["paw"]) / 1000 * TPU * 0.45
    g["tail (hollow, 30% eq.)"] = (vol(m["tail_a"]) + vol(m["tail_b"])) / 1000 * PLA * 0.3
    g["ears (60% eq.)"] = (vol(m["ear_outer"]) + vol(m["ear_inner"])) / 1000 * PLA * 0.6
    g["internal frame, hub posts, neck yoke, eye bezels"] = 18.0
    g["8x MG90S legs"] = 8 * 13.4
    g["4 g micro servo head pan (ES9051 class)"] = 4.5
    g["MG90S tail (wag + self-righting lever)"] = 13.4
    g["2x 14500 Li-ion"] = 2 * 19.5
    g["2x GC9A01 modules"] = 2 * 7.5
    g["2x smoked acrylic windows d32x2"] = 2 * 1.9
    g["2x ESP32-S3 Super Mini + BMI160 + VL53L0X"] = 2 * 2.5 + 1.2 + 1.5
    g["3x MP1584 + 2S BMS + 2S charger"] = 3 * 3.0 + 3.0 + 3.5
    g["speaker 20 mm + PAM8403 + TTP223"] = 3.0 + 1.5 + 0.8
    g["wiring, caps, screws, magnets, horns"] = 20.0
    r["mass_g"] = {k: round(v, 1) for k, v in g.items()}
    r["mass_total_g"] = round(sum(g.values()), 1)
    return r


if __name__ == "__main__":
    pose = {}
    if len(sys.argv) > 1 and sys.argv[1].endswith(".json"):
        pose = json.load(open(sys.argv[1]))
    outdir = sys.argv[2] if len(sys.argv) > 2 else "stl"
    os.makedirs(outdir, exist_ok=True)
    parts, info = build(pose, do_check=pose.get("check", False))
    for k, v in parts.items():
        if k.startswith("_"):
            continue
        export_stl(v, os.path.join(outdir, k + ".stl"), tolerance=0.025, angular_tolerance=0.06)
    vis = Compound(children=[v for k, v in parts.items() if not k.startswith("int_") and not k.startswith("_")])
    bb = vis.bounding_box()
    info["bbox_xyz_mm"] = [round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1)]
    if "checks" in info:
        json.dump(info, open(os.path.join(outdir, "checks.json"), "w"), indent=1)
    print(json.dumps(info, indent=1))
