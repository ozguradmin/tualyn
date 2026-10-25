#!/usr/bin/env python3
"""Concept B "Tarcin" -> per-link meshes for the articulated viewer GLB.

Reuses the concept CAD (concept_B/model.py, imported read-only) and adds what a real print would show:
seams/split lines, counterbored M2 screw heads, the smoked-acrylic visor over the real GC9A01 modules
(32.4 mm active circle, 35.5 mm glass with its black ring, black PLA backer), speaker grille, ToF window,
USB-C charge port, and the servo leads crossing each hip.

Every mesh is written in its LINK frame (joint at origin, rest rotation identity), mm, Z up, robot faces -Y.
Output: build/meshes/<link>__<matKey>.npz (vertices, faces) for the +x legs and the single links;
-x legs are mirrored in pack.py.
Run:  python3 -I -B geom.py
"""
import math, os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "..", "..", "concept_B"))
sys.path.insert(0, SRC)
import numpy as np
from build123d import *
import model as CB                    # concept CAD (read-only)

OUT = os.path.join(HERE, "meshes")
os.makedirs(OUT, exist_ok=True)
P = CB.P
HZ = CB.HIP_Z                           # hip axis height in the concept's model coordinates (before the z shift)
TRI = {}
SPK = {}
LIM = json.load(open(os.path.join(HERE, "limits.json")))
HIP_RANGE = {"F": tuple(LIM["hip_f"]), "H": tuple(LIM["hip_h"])}   # joint windows the wire route must cover
WR = 13.6          # radius of the lead crossing from the hip axis (outside the r 11 hip collar)
PHI0 = {"F": 25.0, "H": -25.0}   # exit angle in the thigh frame (from -Z toward +Y), toward the body centre
RIB_W = 6.6        # 2 servo leads side by side = 6 x 1.1 mm flat ribbon, width laid tangentially
SLOT_W = 2.0       # radial width of the arc slot


def save(name, shape, tol=0.05, ang=0.15):
    """tessellate a build123d shape into <OUT>/<name>.npz, vertices relative to `origin` already applied"""
    if shape is None:
        return
    if "__screw" in name or "__wire" in name or "__internal" in name:
        tol, ang = max(tol, 0.08), max(ang, 0.4)
    if "__wire" in name:
        tol, ang = 0.2, 0.6
    if "shin__shin" in name:
        tol, ang = 0.06, 0.3
    if "__ear" in name:
        tol, ang = max(tol, 0.06), max(ang, 0.2)
    vs, ts = shape.tessellate(tol, ang)
    v = np.array([[p.X, p.Y, p.Z] for p in vs], dtype=np.float32)
    f = np.array(ts, dtype=np.int32)
    np.savez_compressed(os.path.join(OUT, name + ".npz"), v=v, f=f)
    TRI[name] = len(f)
    print(f"{name:34s} {len(f):7d} tris", flush=True)


def T(shape, dx, dy, dz):
    return Pos(dx, dy, dz) * shape


def ray_surface(solid, p0, d, t_max=60.0):
    """first point along p0 + t*d (t>0) that is inside `solid` (p0 outside), by bisection on a coarse march"""
    p0, d = Vector(*p0), Vector(*d).normalized()
    prev = 0.0
    t = 0.0
    while t < t_max:
        t += 0.5
        if solid.is_inside(p0 + d * t):
            lo, hi = prev, t
            for _ in range(30):
                mid = (lo + hi) / 2
                if solid.is_inside(p0 + d * mid):
                    hi = mid
                else:
                    lo = mid
            return p0 + d * hi
        prev = t
    raise RuntimeError(f"no surface along {p0} {d}")


def screw_head(d_head=3.8, h=1.3):
    """M2 pan-head (cross recess), axis +Z, underside of the head at z=0"""
    s = Cylinder(d_head / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    try:
        s = fillet(s.edges().sort_by(Axis.Z)[-1:], 0.55)
    except Exception:
        pass
    for rot in (0, 90):
        s = s - Pos(0, 0, h) * Rot(0, 0, rot) * Box(0.55, 2.3, 1.4)
    return s


def screw_at(host, p_surf, n_out, sink=0.25, d_cb=4.5, depth=1.6):
    """counterbore `host` at p_surf (outward normal n_out) and return (host_cut, screw solid).
    The screw head top ends `sink` mm below the surface."""
    n = Vector(*n_out).normalized()
    pl = Plane(origin=p_surf, z_dir=n)
    cb = pl * Pos(0, 0, -depth) * Cylinder(d_cb / 2, depth + 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
    host = host - cb
    scr = pl * Pos(0, 0, -depth) * screw_head()
    # head is 1.3 tall: top at -depth+1.3; push so that top = -sink
    scr = pl * Pos(0, 0, -sink - 1.3) * screw_head()
    return host, scr


def wire_bundle(pts, n_strands=6, r=0.45, colors=("brown", "red", "orange")):
    """flat-ish bundle of 2 servo leads (brown/red/orange x2) following the spline through pts.
    Returns {color: solid}."""
    path = Spline(*[Vector(*p) for p in pts])
    out = {c: [] for c in colors}
    # strands side by side in the path's normal plane: offsets along a fixed side vector
    for i in range(n_strands):
        off = (i - (n_strands - 1) / 2) * (2 * r + 0.05)
        # offset path: shift every point along a side vector perpendicular to the local tangent and to X
        q = []
        for k in range(len(pts)):
            u = k / (len(pts) - 1)
            tan = path.tangent_at(u)
            # flat lead: strands side by side along X (ribbon lies flat against the pod / body flank)
            side = Vector(1, 0, 0) - tan * tan.dot(Vector(1, 0, 0))
            side = side.normalized()
            q.append(Vector(*pts[k]) + side * off)
        sp = Spline(*q)
        prof = Plane(origin=sp @ 0, z_dir=sp % 0) * Circle(r)
        try:
            st = sweep(prof, path=sp)
        except Exception as e:
            print("sweep failed", e)
            continue
        out[colors[i % 3]].append(st)
    return {c: Compound(children=v) for c, v in out.items() if v}


# =====================================================================================================
# BODY LINK  (frame: (0,0,HZ) in model coordinates; mesh = model - (0,0,HZ))
# =====================================================================================================
def build_body():
    C = Vector(0, P["head_y"], HZ + P["head_dz"])
    bp, b_outer, b_inner = CB.body_parts(HZ, CB.head_clearance(C))
    top, belly, hub = bp["body_top"], bp["body_belly"], bp["hub"]
    screws = []
    # --- belly: 4 x M2 from below into the top shell's bosses (concept: "screws go in from the underside only")
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 8.5, sy * 19.0
            p = ray_surface(b_outer, (x, y, HZ - 40), (0, 0, 1))
            n = Vector(sx * 0.25, 0, -1).normalized()
            belly, s = screw_at(belly, p, n)
            screws.append(s)
    # --- USB-C charge port: front of the belly (the right-flank spot in concept.md is occupied by the hip hub post)
    pu = ray_surface(b_outer, (0, -36.0, HZ - 40), (0, 0, 1))
    nrm = Vector(0, -0.35, -1).normalized()
    plu = Plane(origin=pu, x_dir=(0, 1, 0), z_dir=nrm)
    slot = plu * Pos(0, 0, -3.5) * extrude(RectangleRounded(9.6, 3.9, 1.6), amount=8)
    belly = belly - slot
    usb_shell = plu * Pos(0, 0, -1.6) * (extrude(RectangleRounded(8.94, 3.26, 1.3), amount=-6.5) -
                                       extrude(RectangleRounded(8.2, 2.5, 1.0), amount=-5.8))
    usb_tongue = plu * Pos(0, 0, -2.6) * Box(6.6, 0.7, 4.6, align=(Align.CENTER, Align.CENTER, Align.MAX))
    # --- VL53L0X window in the chest (sensor looks down-forward)
    ptof_o = Vector(0, -39.5, HZ - 3.0)
    dtof = Vector(0, -0.62, -0.78).normalized()
    pt = ray_surface(b_outer, ptof_o + dtof * 40, -dtof)          # come from outside, back toward the sensor
    plt = Plane(origin=pt, x_dir=(1, 0, 0), z_dir=dtof)
    win_cut = plt * Pos(0, 0, -3) * extrude(RectangleRounded(7.4, 4.4, 1.4), amount=6)
    win = plt * Pos(0, 0, -1.2) * extrude(RectangleRounded(7.0, 4.0, 1.2), amount=1.0)   # 1 mm IR-black acrylic, 0.2 below
    belly_or_top = "top" if pt.Z > HZ - 5.0 else "belly"
    if belly_or_top == "top":
        top = top - win_cut
    else:
        belly = belly - win_cut
    # --- neck post (fixed to the body; the head pans around it)
    neck = Pos(0, P["neck_y"], HZ + 15.5) * Cylinder(10.5, 9.0)
    neck = neck - Pos(0, P["neck_y"], HZ + 15.5) * Cylinder(4.0, 12)            # cable bore (UART loom)
    # --- internals (concept layout; charger moved to the belly front with the USB-C port)
    d = CB.body_internals(HZ)
    pw = [Pos(11.6, 14.0, HZ - 1.0) * Box(4.2, 22.0, 17.0),
          Pos(-11.6, 14.0, HZ - 1.0) * Box(4.2, 22.0, 17.0),
          Pos(-11.6, -9.0, HZ - 1.0) * Box(4.2, 22.0, 17.0)]
    bms = Pos(0, -13.0, HZ + 13.4) * Box(13.0, 24.0, 2.2)
    charger = plu * Pos(0, -0.0, -6.0) * Box(13.0, 17.0, 1.6, align=(Align.CENTER, Align.CENTER, Align.MAX))
    tof = plt * Pos(0, 0, -4.0) * Box(12.0, 14.0, 2.5, align=(Align.CENTER, Align.CENTER, Align.MAX))
    imu = Pos(0, 6.5, HZ + 13.4) * Box(13.0, 13.0, 2.5)
    caps = [Pos(-5.0, 30.0, HZ - 12.0) * Cylinder(4.0, 10.0), Pos(5.0, 30.0, HZ - 12.0) * Cylinder(4.0, 10.0)]
    # --- hip service-loop arc slots (review fix): the 6-wire flat lead leaves the pod at a fixed point (r = WR from the
    # hip axis, angle PHI0 in the thigh frame) and crosses straight (along x) into the body through a 2 mm arc slot
    # concentric with the hip axis that spans the whole joint window (+ the ribbon's own width). Inside, a slack bay
    # takes up the length change (body-fixed loop, internal).
    loops = []
    for end, (amin, amax) in HIP_RANGE.items():
        phi0 = PHI0[end]
        dd = math.degrees((RIB_W / 2 + 0.6) / WR)
        f0, f1 = phi0 + amin - dd, phi0 + amax + dd
        yh = -P["hip_y"] if end == "F" else P["hip_y"]
        arc = CenterArc((yh, HZ), WR, f0 - 90.0, f1 - f0)                   # in Plane.YZ coordinates (u = Y, v = Z)
        sk = Plane.YZ * SlotArc(arc=arc, height=SLOT_W)
        pr = extrude(sk, amount=26.0)                  # x 0..26: cuts whatever shell wall the arc meets
        for sx in (1, -1):
            cut = pr if sx > 0 else mirror(pr, about=Plane.YZ)
            top = top - cut
            belly = belly - cut
            fm = math.radians(phi0 + (amin + amax) / 2.0)
            ent = (sx * 13.5, yh + WR * math.sin(fm), HZ - WR * math.cos(fm))
            sy = 1.0 if end == "F" else -1.0
            pts = [ent, (sx * 15.0, yh + sy * 3.0, HZ + 9.0), (sx * 15.2, yh - sy * 6.0, HZ + 2.0),
                   (sx * 14.6, yh + sy * 2.0, HZ - 6.0), (sx * 12.6, yh + sy * 14.0, HZ - 3.0)]
            sp = Spline(*[Vector(*q) for q in pts])
            prof = Plane(origin=sp @ 0, z_dir=sp % 0) * Rectangle(RIB_W, 1.1)
            try:
                loops.append(sweep(prof, path=sp))
            except Exception as e:
                print("slack loop sweep failed", e)
    o = {}
    o["body__shell"] = top
    o["body__cream"] = belly
    if loops:
        o["body__internal_wire"] = Compound(children=loops)
    o["body__hub"] = hub
    o["body__charcoal"] = neck
    o["body__screw"] = Compound(children=screws + [usb_shell, usb_tongue])
    o["body__tofwin"] = win
    o["body__internal_battery"] = d["int_battery"]
    o["body__internal_pcb"] = Compound(children=[d["int_mcu"], charger, tof, imu, bms])
    o["body__internal_power"] = Compound(children=pw + caps)
    o["body__internal_servo"] = d["int_tail_servo"]
    for k, v in o.items():
        fine = k in ("body__shell", "body__cream")
        save(k, T(v, 0, 0, -HZ), tol=0.04 if fine else 0.05, ang=0.12 if fine else 0.2)
    return b_outer


# =====================================================================================================
# HEAD LINK  (pan axis: frame at (0, neck_y, HZ); mesh = model - (0, neck_y, HZ))
# =====================================================================================================
def build_head():
    C = Vector(0, P["head_y"], HZ + P["head_dz"])
    hw, hd, hh = P["head"]
    cx, cy, zc = C
    yf = cy - hd + P["face_cut"]
    hp, z_eye = CB.head_parts(C)
    main, face = hp["head_main"], hp["head_face"]
    outer = CB.head_outer_solid(C)
    # --- visor: the concept's mask outline as ONE 2 mm smoked-acrylic plate (no holes) - the screens sit behind it
    holes = []
    for sx in (-1, 1):
        holes.append(Pos(sx * P["eye_dx"], yf + 1.0, z_eye) * Rot(90, 0, 0) * Cylinder(P["eye_r"] + 0.2, 2.0))
    vb = hp["mask"].bounding_box()
    visor = hp["mask"] + ((holes[0] + holes[1]) & Pos(0, (vb.min.Y + vb.max.Y) / 2, z_eye) * Box(200, vb.size.Y, 200))
    visor = visor & Pos(0, (vb.min.Y + vb.max.Y) / 2, z_eye) * Box(200, vb.size.Y, 200)
    # black PLA backer behind the acrylic (hides the module PCBs), with the glass openings
    backer = Pos(0, 2.0, 0) * visor
    backer = backer + Pos(0, 3.4, 0) * visor
    for sx in (-1, 1):
        backer = backer - Pos(sx * P["eye_dx"], yf + 3.0, z_eye) * Rot(90, 0, 0) * Cylinder(18.0, 8.0)
    # --- GC9A01 modules: active circle 32.4, glass 35.5 with a black ring, round PCB 38, header up
    g0 = vb.max.Y + 0.3                             # glass front, 0.3 behind the acrylic
    act, ring, pcb = [], [], []
    for sx, tag in ((1, "L"), (-1, "R")):
        ex = sx * P["eye_dx"]
        a = Pos(ex, g0 + 0.05, z_eye) * Rot(90, 0, 0) * Cylinder(16.2, 0.1)
        act.append((tag, a))
        rg = Pos(ex, g0 + 0.6, z_eye) * Rot(90, 0, 0) * (Cylinder(17.75, 1.2) - Cylinder(16.2, 2.0))
        ring.append(rg)
        pcb.append(Pos(ex, g0 + 1.2 + 0.8, z_eye) * Rot(90, 0, 0) * Cylinder(19.0, 1.6))
        pcb.append(Pos(ex, g0 + 2.8 + 1.8, z_eye + 15.5) * Box(12.7, 3.6, 2.5))   # 7-pin header
    # --- chin cap split (the crown prints dome-up; the cap closes the bottom and carries the neck opening)
    zs = zc - 17.0
    crown = main & Pos(0, 0, zs + 0.3 + 100) * Box(300, 300, 200)
    cap = main & Pos(0, 0, zs - 0.3 - 100) * Box(300, 300, 200)
    cap = cap - Pos(0, P["neck_y"], zc - hh) * Cylinder(11.6, 20)               # neck opening (post is r 10.5)
    screws = []
    for sx in (-1, 1):
        p = ray_surface(outer, (sx * 13.0, cy + 9.0, zc - 60), (0, 0, 1))
        cap, s = screw_at(cap, p, (0, 0, -1))
        screws.append(s)
    # --- speaker grille on the back of the crown (32 mm speaker faces +Y)
    # --- 32 mm 8 ohm 1 W speaker (Motorobit, 32 x 5 mm) on the back wall, facing +Y through the grille.
    # Fit: the front rim (r 16) must stay 0.4 mm inside the 1.6 mm wall; the pan servo body now points FORWARD
    # (it pointed back and filled the lower back of the head), the head MCU board sits in front of the speaker.
    def y_wall(x, z, g=-1.6):      # back inner wall of the head superellipsoid (analytic, same exponents as CB)
        a, b_, c = hw + g, hd + g, hh + g
        e = P["head_ev_top"] if z > 0 else 2.55
        sv = max(1e-6, 1 - abs(z / c) ** e) ** (1 / e)
        return cy + b_ * sv * max(0.0, 1 - (abs(x) / (a * sv)) ** 2.8) ** (1 / 2.8)
    best = None
    for dz in np.arange(-8.0, 4.01, 0.25):
        ys = []
        for th in np.linspace(0, 2 * math.pi, 48, endpoint=False):
            ys.append(y_wall(16.0 * math.cos(th), dz + 16.0 * math.sin(th)))
        yf_s = min(ys) - 0.4
        if best is None or yf_s > best[1]:
            best = (dz, yf_s)
    sdz, ysf = best
    zsp = zc + sdz
    SPK.update(dz=round(float(sdz), 2), y_front=round(float(ysf), 2), y_back=round(float(ysf - 5.0), 2),
               mcu_back_y=round(cy + 16.0, 2), head_centre_y=cy)
    print("speaker 32 mm: centre dz", sdz, "front y", round(ysf, 2), "back y", round(ysf - 5, 2), "MCU board back y", cy + 16)
    grille = []
    for i in range(-3, 4):
        for j in range(-3, 4):
            x, z = i * 3.4 + (1.7 if j % 2 else 0), j * 2.95
            if x * x + z * z <= 10.4 ** 2:
                grille.append(Pos(x, cy + 30, zsp + z) * Rot(90, 0, 0) * Cylinder(0.8, 20))
    SPK["grille_holes"] = len(grille)
    crown = crown - Compound(children=grille)
    spk_cone = Pos(0, ysf - 1.2, zsp) * Rot(90, 0, 0) * (Cylinder(16.0, 0.8) - Cylinder(13.8, 2.0) + Pos(0, 0, 0.6) * Cylinder(13.8, 0.6))
    spk_body = Pos(0, ysf - 1.6 - 1.7, zsp) * Rot(90, 0, 0) * (Cylinder(16.0, 3.4) - Pos(0, 0, -1.0) * Cylinder(10.5, 2.0)) \
        + Pos(0, ysf - 5.0 + 1.0, zsp) * Rot(90, 0, 0) * Cylinder(8.0, 2.0)
    # --- micro servo (pan) in the head (body of the servo forward of the pan axis), head MCU, touch pad
    neck_srv = CB.place(CB.micro4g(), (0, P["neck_y"], HZ + 36.5), (0, -1, 0), (0, 0, -1))
    o = {}
    o["head__shell"] = crown
    o["head__shellcap"] = cap
    o["head__cream_face"] = face
    o["head__cheek"] = hp["cheeks"]
    o["head__charcoal"] = hp["mouth"]
    o["head__nose"] = hp["nose"]
    o["head__ear"] = hp["ear_outer"]
    o["head__cream_ear"] = hp["ear_inner"]
    o["head__visor"] = visor
    o["head__backer"] = backer
    o["head__lcdglass"] = ring[0] + ring[1]
    for tag, a in act:
        o["head__screen_eye" + tag] = a
    o["head__screw"] = Compound(children=screws)
    o["head__internal_screen"] = Compound(children=pcb)
    o["head__speaker"] = spk_cone
    touch_mcu = Pos(0, cy + 2, zc + hh - 3.5) * Box(15, 11, 1.6) + Pos(0, cy + 14, zc + 9) * Box(22.5, 4.0, 18.0)
    o["head__internal_pcb"] = touch_mcu + spk_body
    o["head__internal_servo"] = neck_srv
    for k, v in o.items():
        fine = k in ("head__shell", "head__shellcap", "head__cream_face", "head__ear")
        save(k, T(v, 0, -P["neck_y"], -HZ), tol=0.035 if fine else 0.04, ang=0.12 if fine else 0.18)
    return dict(yf=yf, z_eye=z_eye, g0=g0, C=(cx, cy, zc))


# =====================================================================================================
# TAIL LINK  (axis +Y through (0, 48, HZ-5))
# =====================================================================================================
def build_tail():
    tp = CB.tail_parts(HZ)
    ty, tz = CB.TAIL_AXIS
    tail_all = tp["tail_a"] + tp["tail_b"]
    # horn screw: from the back of the tail root, along the servo axis
    p = ray_surface(tail_all, (0, ty + 40, HZ + tz), (0, -1, 0))
    ta, s = screw_at(tp["tail_a"], p, (0, 1, 0), sink=0.3, d_cb=4.6, depth=1.8)
    o = {"tail__shell_tail": ta, "tail__ring": tp["tail_b"], "tail__screw": s,
         "tail__internal_horn": Pos(0, ty, HZ + tz) * Rot(-90, 0, 0) * CB.horn()}
    for k, v in o.items():
        save(k, T(v, 0, -ty, -HZ - tz), tol=0.04, ang=0.15)


# =====================================================================================================
# LEGS (+x side, built in the concept's leg-local frames: thigh = hip axis at origin with a = 0,
#        shin = knee axis at origin with b = 0). -x legs are mirrored copies.
# =====================================================================================================
def build_leg(end):
    L1 = P["L1"]
    full, outer, inner, up, low = CB.pod_solid()
    # pod print split: inner half (carries the hub collars + both servos) and outer cap, vertical seam at x = 41
    xs = 41.0
    up_in = up & Pos(xs - 0.3 - 100, 0, 0) * Box(200, 300, 300)
    up_out = up & Pos(xs + 0.3 + 100, 0, 0) * Box(200, 300, 300)
    screws = []
    # 2 x M2 through the inner half into the outer cap, heads on the body-facing side
    for zz in (-14.0, 4.0):
        if zz > 0:
            continue
        p = ray_surface(full, (0.0, 0.0, zz), (1, 0, 0))
        up_in, s = screw_at(up_in, p, (-1, 0, 0))
        screws.append(s)
    low2 = low                                       # sock cap: press-fit + glue at the groove (no screw)
    hip_servo = CB.place(CB.mg90s(), (55.3, 0, 0), (0, 0, -1), (-1, 0, 0))
    knee_servo = CB.place(CB.mg90s(), (55.3, 0, -L1), (0, 0, 1), (-1, 0, 0))
    hrn = Pos(25.0, 0, 0) * Rot(0, 90, 0) * CB.horn()
    # servo leads (hip + knee servo = 2 flat 3-wire leads) leave the pod's inner face behind the hub collar
    # and enter the body flank through a grommet. sy_in: toward the body centre.
    # lead exit: straight flat stub along -x at r = WR, angle PHI0 (thigh frame), from 1 mm inside the pod face to
    # 1.5 mm inside the body shell at the deepest point of the arc (computed on the real body surface)
    phi0 = math.radians(PHI0[end])
    yh = -P["hip_y"] if end == "F" else P["hip_y"]
    amin, amax = HIP_RANGE[end]
    bo = CB.body_outer_solid(HZ)
    xs_shell = []
    for a in np.linspace(amin, amax, 19):
        f = phi0 + math.radians(a)
        pz = ray_surface(bo, (45.0, yh + WR * math.sin(f), HZ - WR * math.cos(f)), (-1, 0, 0), t_max=45)
        xs_shell.append(pz.X)
    x_end = min(xs_shell) - 1.5
    print(f"leg {end}: body surface x along the slot {min(xs_shell):.1f}..{max(xs_shell):.1f}, stub ends at x={x_end:.1f}")
    c0 = Vector(0, WR * math.sin(phi0), -WR * math.cos(phi0))
    tng = Vector(0, math.cos(phi0), math.sin(phi0))
    x_face = P["pod_x0"]
    wires = {"brown": [], "red": [], "orange": []}
    for i in range(6):
        off = (i - 2.5) * 1.1
        q = c0 + tng * off
        st = Pos(x_end, q.Y, q.Z) * Rot(0, 90, 0) * Cylinder(0.5, x_face + 1.0 - x_end, align=(Align.CENTER, Align.CENTER, Align.MIN))
        wires[("brown", "red", "orange")[i % 3]].append(st)
    wires = {c: Compound(children=v) for c, v in wires.items()}
    # exit slot in the pod's inner face (rounded 7.6 x 2.0) with the lead in it
    pl_exit = Plane(origin=(x_face, c0.Y, c0.Z), x_dir=(0, tng.Y, tng.Z), z_dir=(-1, 0, 0))
    up_in = up_in - pl_exit * Pos(0, 0, -4.0) * extrude(SlotOverall(RIB_W + 1.0, 2.0), amount=6.0)
    open(os.path.join(OUT, f"wire_{end}.json"), "w").write(json.dumps(dict(x_end=x_end, shell_x=[min(xs_shell), max(xs_shell)], WR=WR, PHI0=PHI0[end])))
    o = {"thigh__shell_pod": up_out, "thigh__shell_podin": up_in, "thigh__sock": low2,
         "thigh__screw": Compound(children=screws),
         "thigh__internal_servo": hip_servo + knee_servo, "thigh__internal_horn": hrn}
    for c, v in wires.items():
        o["thigh__wire_" + c] = v
    for k, v in o.items():
        fine = k.startswith("thigh__shell") or k == "thigh__sock"
        save(f"{k}_{end}", v, tol=0.04 if fine else 0.05, ang=0.13 if fine else 0.25)
    # ---- shin
    shin, paw = CB.shin_solid(end)
    x0 = P["shin_x0"]
    shs = []
    shin2 = shin
    for (yy, zz, big) in ((0.0, 0.0, True), (0.0, -6.0, False), (0.0, 6.0, False)):
        if big:
            shin2, s = screw_at(shin2, Vector(x0, yy, zz), (-1, 0, 0), sink=0.2, d_cb=4.4, depth=1.4)
        else:
            sc = Plane(origin=(x0, yy, zz), z_dir=(-1, 0, 0)) * Pos(0, 0, -0.9) * screw_head(2.6, 1.0)
            shin2 = shin2 - Plane(origin=(x0, yy, zz), z_dir=(-1, 0, 0)) * Pos(0, 0, -1.0) * Cylinder(1.6, 3, align=(Align.CENTER, Align.CENTER, Align.MIN))
            s = sc
        shs.append(s)
    knee_hrn = Pos(25.0, 0, 0) * Rot(0, 90, 0) * CB.horn()
    o = {"shin__shin": shin2, "shin__paw": paw, "shin__screw": Compound(children=shs), "shin__internal_horn": knee_hrn}
    for k, v in o.items():
        save(f"{k}_{end}", v, tol=0.04, ang=0.15)


if __name__ == "__main__":
    which = sys.argv[1:] or ["body", "head", "tail", "legF", "legH"]
    info = {}
    if "body" in which:
        build_body()
    if "head" in which:
        info["head"] = build_head()
    if "tail" in which:
        build_tail()
    if "legF" in which:
        build_leg("F")
    if "legH" in which:
        build_leg("H")
    prev = {}
    fp = os.path.join(OUT, "tris.json")
    if os.path.exists(fp):
        prev = json.load(open(fp))
    prev.update(TRI)
    json.dump(prev, open(fp, "w"), indent=1)
    if SPK:
        json.dump(SPK, open(os.path.join(OUT, "speaker_fit.json"), "w"), indent=1)
    if info:
        json.dump({k: {kk: (list(vv) if isinstance(vv, (tuple, Vector)) else vv) for kk, vv in v.items()} for k, v in info.items()},
                  open(os.path.join(OUT, "info.json"), "w"), indent=1, default=float)
    print("total tris", sum(prev.values()))
