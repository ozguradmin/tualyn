#!/usr/bin/env python3
"""
Tosbi (concept A) -> articulated model.glb for the viewer package.

Geometry comes from concept_A/model.py (same parameters and helper functions, copied here so the
concept stays read-only), re-cut into links:

  body (root, identity, origin on the ground under the body centre; mid-plane at z = HM)
   +- leg_fl / leg_fr / leg_rl / leg_rr   hub egg + arm (+ knee servo inside); hip yaw about body Z
   |   +- foot_xx                         knee barrel end caps + boot + TPU toe; knee about leg Y
   +- head                                head shell, bezel, PETG visor, acrylic window, GC9A01; pitch about X

Realism additions over the concept model: 0.5 mm seam grooves (hub-egg equator, arm halves, head halves),
counterbored M2 screw heads (egg poles, knee caps, domes, head back), speaker grille holes,
a real USB-C receptacle, the GC9A01 glass with its 32.4 mm active circle behind a hole in the visor and a
2 mm smoked acrylic window, black mask tube, internals and wires (x-ray only).

usage: python3 -I build_glb.py <package_dir>
"""
import json, math, os, sys
import numpy as np
import trimesh
from build123d import *
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import internals as I      # BOM-sized internals, KCD1 switch, cliff ToF (review fix 2026-10-25)

PKG = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOL, ATOL = 0.05, 0.15

# ----------------------------------------------------------------- parameters (from concept_A/model.py)
W, L, T = 82.0, 84.0, 48.0
RC = 30.0
SEC_A, SEC_B = 26.0, 20.0
WALL = 1.8
CC = (W / 2 - RC, L / 2 - RC)
HUB_ANG, HUB_IN = 35.0, 6.0
def _hub(sx, sy):
    a = math.radians(HUB_ANG); r = RC - HUB_IN
    return (sx * (CC[0] + r * math.cos(a)), sy * (CC[1] + r * math.sin(a)))
HUB = [_hub(1, -1), _hub(-1, -1), _hub(1, 1), _hub(-1, 1)]        # +x = robot's LEFT (robot faces -Y)
LEGS = ["fl", "fr", "rl", "rr"]
LEG_DIR0 = [-HUB_ANG, 180 + HUB_ANG, HUB_ANG, 180 - HUB_ANG]
SERVO_DIR = [120.0, 60.0, -120.0, -60.0]
HUB_R, HUB_H, HUB_P = 13.2, 19.5, 2.6
SOCK_GAP = 0.8
LC = 33.0
POD_HW, POD_HZ = 17.0, 9.5
NECK_HW = 9.0
LF = 36.0
TOE_R = 7.0
BETA0 = 80.0
HM = LF * math.sin(math.radians(BETA0)) + TOE_R
HIP_SERVO_Z = 13.0
HEAD_R, HEAD_HF, HEAD_HB, HEAD_PF, HEAD_PB = 33.0, 18.0, 22.0, 3.0, 2.3
HEAD_ZS = 0.88
HEAD_GAP = 5.0
HEAD_C = (0.0, -(L / 2 + HEAD_GAP + HEAD_HB), 0.0)
VISOR_A, VISOR_B = 26.3, 18.3
BEZEL_W = 2.6
STALK_R = 7.5
KNEE_R, KNEE_HW, CAP_V, REVEAL = 11.4, 20.3, 17.5, 0.4

# real screen stack (head frame, face toward -Y)
ACT_R = 32.4 / 2          # GC9A01 active circle
GLASS_R = 35.5 / 2        # GC9A01 cover glass
LCD_Y0 = -12.4            # glass front face
HOLE_R = 17.2             # hole in the PETG visor
WIN_R, WIN_Y0, WIN_T = 17.0, -16.6, 2.0   # 2 mm smoked acrylic window, press-fit in the hole

# ----------------------------------------------------------------- helpers (from model.py)
def rrect_wire(w, l, r, z):
    r = max(0.3, min(r, w / 2 - 0.05, l / 2 - 0.05))
    return RectangleRounded(w, l, r).wires()[0].moved(Location((0, 0, z)))

def pebble(Wd, Ld, Td, rc, a, b, off=0.0, n=10):
    z0 = Td / 2 - b
    zs = {0.0, z0 * 0.5, -z0 * 0.5}
    for i in range(n + 1):
        zz = z0 + b * math.sin(i / n * math.pi / 2); zs.add(zz); zs.add(-zz)
    secs = []
    for z in sorted(zs):
        az = abs(z)
        q = 0.0 if az <= z0 else min(1.0, (az - z0) / b)
        d = a * (1 - math.sqrt(max(0.0, 1 - q * q))) + off
        zz = z if az < Td / 2 - 1e-6 else math.copysign(Td / 2 - off, z)
        secs.append(rrect_wire(Wd - 2 * d, Ld - 2 * d, rc - d, zz))
    return Solid.make_loft(secs, ruled=False)

def cyl(r, h, center=(0, 0, 0), axis="Z"):
    c = Cylinder(r, h)
    if axis == "X": c = c.rotate(Axis.Y, 90)
    elif axis == "Y": c = c.rotate(Axis.X, 90)
    return c.translate(center)

def box(x0, x1, y0, y1, z0, z1):
    return Box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))

def egg2(R, Ht, Hb, pt, pb, n=26):
    pts = []
    for k in range(n + 1):
        t = -math.pi / 2 + (math.pi / 2) * k / n
        pts.append((R * max(math.cos(t), 0) ** (2 / pb), 0.0, -Hb * abs(math.sin(t)) ** (2 / pb)))
    for k in range(1, n + 1):
        t = (math.pi / 2) * k / n
        pts.append((R * max(math.cos(t), 0) ** (2 / pt), 0.0, Ht * math.sin(t) ** (2 / pt)))
    sp = Spline(*pts, tangents=[(1, 0, 0), (-1, 0, 0)])
    return revolve(Face(Wire([sp, Line(pts[-1], pts[0])])), Axis.Z)

def mg90s(tabs=(True, True), horn_r=0.0):
    s = box(-6.0, 16.8, -6.1, 6.1, -28.5, -6.0)
    s += cyl(6.1, 6.0, (0, 0, -3.0))
    s += cyl(3.6, 4.5, (6.5, 0, -3.75))
    if tabs[0]: s += box(-10.85, -6.0, -6.1, 6.1, -12.6, -10.1)
    if tabs[1]: s += box(16.8, 21.65, -6.1, 6.1, -12.6, -10.1)
    s += cyl(2.4, 3.5, (0, 0, 1.75))
    if horn_r: s += cyl(horn_r, 2.0, (0, 0, 2.0))
    return s

def zone(z0, z1):
    return box(-80, 80, -80, 80, z0, z1)

def up(s):            # body mid-plane frame -> body link frame (origin on the ground)
    return s.translate((0, 0, HM))

# ----------------------------------------------------------------- screws
def screw_solid(kind):
    """Head at origin, axis +Z, bearing face at z=0. 'button' = ISO 7380 M2 (d3.5 x 1.1, hex 1.3);
    'cap' = M2 socket head cap (shoulder-screw bearing pin, d3.8 x 2.0, hex 1.5)."""
    if kind == "button":
        h = Cylinder(1.75, 1.1, align=(Align.CENTER, Align.CENTER, Align.MIN))
        h = h.fillet(0.75, h.edges().group_by(Axis.Z)[-1])
        hx = extrude(RegularPolygon(0.75, 6), amount=0.9).translate((0, 0, 0.45))
    else:
        h = Cylinder(1.9, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        h = h.fillet(0.25, h.edges().group_by(Axis.Z)[-1])
        hx = extrude(RegularPolygon(0.87, 6), amount=1.5).translate((0, 0, 0.8))
    return h - hx

def tri(shape, tol=TOL, atol=ATOL):
    v, f = shape.tessellate(tol, atol)
    return trimesh.Trimesh(np.array([[p.X, p.Y, p.Z] for p in v]), np.array(f), process=True)

def surface_hit(solid, origin, direction):
    m = tri(solid, 0.1, 0.3)
    O = np.array(origin, float); D = np.array(direction, float); D /= np.linalg.norm(D)
    tr = m.triangles; v0, e1, e2 = tr[:, 0], tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0]
    pv = np.cross(D, e2); det = np.einsum('ij,ij->i', e1, pv)
    ok = np.abs(det) > 1e-12; inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    tv = O - v0; u = np.einsum('ij,ij->i', tv, pv) * inv
    qv = np.cross(tv, e1); v = (qv @ D) * inv; t = np.einsum('ij,ij->i', e2, qv) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    if not hit.any():
        raise RuntimeError(f"no hit {origin} {direction}")
    return O + D * t[hit].min()

def add_screws(solid, sites, kind="button"):
    """sites: list of (ray_origin, axis_outward). Cuts a counterbore along the axis at the surface point,
    returns (cut solid, [screw solids])."""
    rcb, depth = (2.15, 1.25) if kind == "button" else (2.3, 2.15)
    screws = []
    for (o, ax) in sites:
        ax = np.array(ax, float); ax /= np.linalg.norm(ax)
        p = surface_hit(solid, o, -ax)
        floor = p - ax * depth
        pl = Plane(origin=tuple(floor), z_dir=tuple(ax))
        cb = Cylinder(rcb, depth + 6, align=(Align.CENTER, Align.CENTER, Align.MIN))
        solid = solid - cb.moved(pl.location)
        screws.append(screw_solid(kind).moved(pl.location))
    return solid, screws

def build_geometry():
    global POD_SK
    # ----------------------------------------------------------------- BODY (mid-plane frame, shifted by HM at the end)
    body_out = pebble(W, L, T, RC, SEC_A, SEC_B)
    body_in = pebble(W, L, T, RC, SEC_A, SEC_B, off=WALL)
    sock = egg2(HUB_R + SOCK_GAP, HUB_H + SOCK_GAP, HUB_H + SOCK_GAP, HUB_P, HUB_P)
    sockets = None
    for (hx, hy) in HUB:
        c = sock.translate((hx, hy, 0)); sockets = c if sockets is None else sockets + c
    stalk_hole = cyl(STALK_R + 0.8, 12.0, (0, -L / 2, 0), "Y")
    tail_hole = box(-4.6, 4.6, L / 2 - 8, L / 2 + 6, -1.7, 1.7)
    tail_slot = cyl(7.3, 14.0, (0, L / 2 - 0.5, 0), "Y") & box(-9, 9, L / 2 - 9, L / 2 + 6, -4.8, 4.8)
    shell = body_out - body_in - sockets - stalk_hole - tail_slot
    # speaker grille (29 mm speaker sits behind the rear wall at y = 32.5): 2 x 5 holes d1.6 per dome
    grille = None
    for zg, xs in ((6.2, (-8.0, -4.0, 0.0, 4.0, 8.0)), (9.4, (-6.0, -2.0, 2.0, 6.0))):
        for xg in xs:
            for sg in (1, -1):
                c = cyl(0.8, 16.0, (xg, L / 2 - 2, sg * zg), "Y")
                grille = c if grille is None else grille + c
    shell = shell - grille
    # KCD1 power rocker on the right flank (cut-out half in each dome) + one cliff-ToF window per dome
    shell = shell - I.switch_cutter() - I.tof_cutter(-1) - I.tof_cutter(1)
    shell_top = (shell & zone(0.4, 40)) - tail_hole
    shell_bot = (shell & zone(-40, -0.4)) - tail_hole
    lip = (pebble(W, L, T, RC, SEC_A, SEC_B, off=1.0) - body_in) & zone(-1.6, 1.6)
    lip = lip - sockets - stalk_hole - tail_hole - I.switch_cutter()
    tof_liners = [I.tof_liner(sg) & body_out for sg in (-1, 1)]

    def scute_cutter(sign):
        R = 15.0
        pts = [(R * math.cos(math.radians(60 * i)), R * math.sin(math.radians(60 * i))) for i in range(6)]
        segs = [(pts[i], pts[(i + 1) % 6]) for i in range(6)]
        for p in pts:
            a = math.atan2(p[1], p[0]); segs.append((p, (p[0] + 70 * math.cos(a), p[1] + 70 * math.sin(a))))
        g = None
        for (a, b) in segs:
            ln = math.hypot(b[0] - a[0], b[1] - a[1]); ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            s = Box(ln + 1.3, 1.5, 40).rotate(Axis.Z, ang).translate(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, sign * 25))
            g = s if g is None else g + s
        skin = body_out - pebble(W, L, T, RC, SEC_A, SEC_B, off=1.0)
        z = zone(8.0, 40) if sign > 0 else zone(-40, -8.0)
        return g & skin & z

    shell_top = shell_top - scute_cutter(+1)
    shell_bot = shell_bot - scute_cutter(-1)
    hexr = 15.0 - 0.75 - 0.05
    hexp = extrude(RegularPolygon(hexr, 6, major_radius=True), amount=60, both=True)
    badge_t = shell_top & hexp
    badge_b = shell_bot & hexp
    shell_top = shell_top - hexp
    shell_bot = shell_bot - hexp
    # dome screws: 2 x M2 button head per dome, in the scute spokes along +-x (into chassis bosses)
    shell_top, scr_top = add_screws(shell_top, [((24.0, 0, 60), (0, 0, 1)), ((-24.0, 0, 60), (0, 0, 1))])
    shell_bot, scr_bot = add_screws(shell_bot, [((24.0, 0, -60), (0, 0, -1)), ((-24.0, 0, -60), (0, 0, -1))])

    tail = cyl(6.5, 12.0, (0, L / 2 - 0.5, 0), "Y") & box(-8, 8, L / 2 - 6.5, L / 2 + 3.6, -4.0, 4.0)
    try:
        tail = tail.fillet(1.6, [e for e in tail.edges() if e.center().Y > L / 2 + 3.0])
    except Exception:
        pass
    tail = tail - tail_hole - body_in
    # USB-C receptacle (8.94 x 3.26 stadium shell), mouth 1.0 mm inside the tail nub
    def stadium(w, h, y0, y1):
        s = box(-w / 2, w / 2, y0, y1, -h / 2, h / 2)
        return s.fillet(h / 2 - 0.01, s.edges().filter_by(Axis.Y))
    usb_shell = stadium(8.94, 3.26, L / 2 - 7.5, L / 2 + 2.6) - stadium(8.34, 2.66, L / 2 - 6.0, L / 2 + 3.0)
    usb_tongue = box(-3.3, 3.3, L / 2 - 6.0, L / 2 + 1.9, -0.35, 0.35)
    usb_back = box(-4.2, 4.2, L / 2 - 6.4, L / 2 - 5.9, -1.3, 1.3)

    stalk_y1 = HEAD_C[1] + 21.7
    stalk = cyl(STALK_R, (-L / 2 + 5.0) - stalk_y1, (0, (stalk_y1 + (-L / 2 + 5.0)) / 2, 0), "Y")
    NECK_SERVO_X = 12.0
    neck_servo = mg90s(tabs=(False, True)).rotate(Axis.Z, 90).rotate(Axis.Y, 90).translate((NECK_SERVO_X, HEAD_C[1], 0))
    plate = box(-6.0, 6.0, stalk_y1 - 0.01, stalk_y1 + 3.0, -6.1, 6.1) - neck_servo

    body = {
        "shell": [shell_top, shell_bot],
        "badge": [badge_t, badge_b],
        "lip": [lip, usb_tongue, usb_back],
        "tail": [tail],
        "metal": [usb_shell],
        "stalk": [stalk],
        "screw": scr_top + scr_bot,
        "internal_servo": [neck_servo] + [mg90s(tabs=(False, True)).rotate(Axis.Z, sd).translate((hx, hy, HIP_SERVO_Z))
                                          for (hx, hy), sd in zip(HUB, SERVO_DIR)],
        "speaker": [cyl(14.5, 4.0, (0, 32.5, 0), "Y") - cyl(11.0, 2.0, (0, 35.0, 0), "Y")],   # visible through the grille
        "switch": I.switch_visible(),
    }
    body["lip"] += tof_liners
    BP = I.body_parts()
    body["internal_cell"] = [x for _, x in BP["cell"]]
    body["internal_pcb"] = [x for _, x in BP["pcb"]] + [plate]
    body["internal_chip"] = [x for _, x in BP["chip"]]
    body["internal_chassis"] = [x for _, x in BP["chassis"]]
    body["internal_cap"] = [x for _, x in BP["cap"]]

    # ----------------------------------------------------------------- LEGS (leg frame: u=+X radial, knee axis = +Y)
    def knee_barrel():
        b = cyl(KNEE_R, 2 * KNEE_HW, (0, 0, 0), "Y")
        return b.fillet(4.5, b.edges().filter_by(GeomType.CIRCLE))

    POD_SK = None
    def pod_parts(window_center_deg):
        global POD_SK
        hub = egg2(HUB_R, HUB_H, HUB_H, HUB_P, HUB_P)
        pts = [(0, -NECK_HW), (11.0, -NECK_HW), (16.2, -POD_HW), (LC + 2, -POD_HW),
               (LC + 2, POD_HW), (16.2, POD_HW), (11.0, NECK_HW), (0, NECK_HW)]
        sk = Polygon(*pts, align=None)
        try:
            sk = fillet(sk.vertices().filter_by(lambda v: 10 < v.X < 17), 5.0)
        except Exception as e:
            print("2d fillet failed", e)
        POD_SK = sk
        arm = extrude(sk, amount=POD_HZ, both=True)
        for rf in (7.0, 6.5, 6.0, 5.0):
            try:
                arm = arm.fillet(rf, arm.edges().filter_by(lambda e: abs(abs(e.center().Z) - POD_HZ) < 0.01 and e.center().X > 4)); break
            except Exception:
                continue
        arm = arm & box(-30, LC, -40, 40, -20, 20)
        mid = knee_barrel().translate((LC, 0, 0)) & box(0, 80, -(CAP_V - REVEAL), CAP_V - REVEAL, -20, 20)
        arm = arm + mid
        arm = arm - cyl(9.6, 3.0, (LC, CAP_V - 1.4, 0), "Y")
        arm = arm - cyl(2.6, 4.0, (LC, -(CAP_V - 1.5), 0), "Y")
        arm = arm - hub
        # seam: the arm is two halves split at z = 0 (they clamp the knee servo) -> 0.5 x 0.5 mm groove
        try:
            inner = extrude(offset(sk, amount=-0.5), amount=1.0, both=True) & box(-30, LC, -40, 40, -2, 2)
            inner = inner + cyl(KNEE_R - 0.5, 2 * CAP_V, (LC, 0, 0), "Y")
            arm = arm - (box(-5, LC + 15, -25, 25, -0.25, 0.25) - inner)
        except Exception as e:
            print("arm seam failed", e)
        w = None
        for a in range(-54, 55, 6):
            s = box(9.5, 15.0, -3.6, 3.6, -16.5, 7.6).rotate(Axis.Z, window_center_deg + a)
            w = s if w is None else w + s
        egg = hub - w
        # seam: egg printed as two halves split at the equator
        egg = egg - (box(-20, 20, -20, 20, -0.25, 0.25) - egg2(HUB_R - 0.5, HUB_H - 0.5, HUB_H - 0.5, HUB_P, HUB_P))
        # screws: horn screw on the top pole, M2 shoulder screw (bearing pin) on the bottom pole
        egg, s1 = add_screws(egg, [((0, 0, 60), (0, 0, 1))], "button")
        egg, s2 = add_screws(egg, [((0, 0, -60), (0, 0, -1))], "cap")
        return egg, arm, s1 + s2

    def foot_parts():
        caps = knee_barrel() - box(-30, 30, -CAP_V, CAP_V, -30, 30)
        pin = cyl(2.4, 3.6, (0, -(CAP_V - 1.6), 0), "Y")
        rc_, P = 10.0, (13.0, 8.5)
        dP = math.hypot(*P); th = math.atan2(P[1], P[0]) + math.acos(rc_ / dP)
        pts = [P] + [(rc_ * math.cos(a), rc_ * math.sin(a)) for a in
                     [th + (2 * math.pi - 2 * th) * k / 40 for k in range(41)]] + [(P[0], -P[1])]
        hull = Polygon(*[(x, z) for (x, z) in pts], align=None)
        tabs = None
        for sg in (1, -1):
            t = extrude(hull, amount=1.0).rotate(Axis.X, 90)
            t = t.translate((0, 18.6 if sg > 0 else -17.6, 0))
            tabs = t if tabs is None else tabs + t
        s0 = RectangleRounded(18.0, 2 * KNEE_HW - 0.6, 8.0).wires()[0].rotate(Axis.Y, 90).translate((11.9, 0, 0))
        s1 = RectangleRounded(14.6, 25.0, 7.0).wires()[0].rotate(Axis.Y, 90).translate((LF - 7.0, 0, 0))
        s2 = RectangleRounded(14.0, 24.0, 6.9).wires()[0].rotate(Axis.Y, 90).translate((LF - 2.0, 0, 0))
        boot = Solid.make_loft([s0, s1, s2], ruled=False)
        try:
            boot = boot.fillet(3.0, boot.faces().sort_by(Axis.X)[0].edges())
        except Exception as e:
            print("boot fillet", e)
        clear = cyl(KNEE_R + REVEAL, 2 * (CAP_V - 0.01), (0, 0, 0), "Y")
        f = (caps + pin + tabs + boot) - clear + pin
        toe = cyl(TOE_R, 24.0, (LF, 0, 0), "Y")
        toe = toe.fillet(TOE_R - 0.6, toe.edges().filter_by(GeomType.CIRCLE))
        cut = box(LF - 30, LF - 2.0, -20, 20, -20, 20)
        f = f + (toe & cut)
        # knee cap screws: horn screw (+Y cap) and shoulder-screw bearing pin (-Y cap)
        f, s1 = add_screws(f, [((0, 60, 0), (0, 1, 0))], "button")
        f, s2 = add_screws(f, [((0, -60, 0), (0, -1, 0))], "cap")
        return f, toe - cut, s1 + s2

    foot_f, foot_toe, foot_scr = foot_parts()
    FOOT = {"boot": [foot_f], "toe": [foot_toe], "screw": foot_scr}
    KS = mg90s(tabs=(False, True)).rotate(Axis.X, -90).rotate(Axis.Y, 180).translate((LC, 14.25, 0))

    pod_cache = {}
    LEGLINK = []
    for i, ((hx, hy), d0, sdir) in enumerate(zip(HUB, LEG_DIR0, SERVO_DIR)):
        key = round(sdir - d0, 3)
        if key not in pod_cache:
            pod_cache[key] = pod_parts(sdir - d0)
        egg, arm, scr = pod_cache[key]
        LEGLINK.append({"egg": [egg], "arm": [arm], "screw": scr, "internal_servo": [KS]})

    # ----------------------------------------------------------------- HEAD (head frame = pitch pivot, face toward -Y)
    def head_solid(dr):
        h = egg2(HEAD_R + dr, HEAD_HF + dr, HEAD_HB + dr, HEAD_PF, HEAD_PB).rotate(Axis.X, 90)
        return scale(h, by=(1.0, 1.0, HEAD_ZS))
    def ecyl(a, b, y0, y1):
        return scale(cyl(b, y1 - y0, (0, (y0 + y1) / 2, 0), "Y"), by=(a / b, 1.0, 1.0))

    fy = -HEAD_HF
    hd = head_solid(0.0)
    inner = head_solid(-1.6)
    front = box(-40, 40, fy - 3, fy + 9, -40, 40)
    rim_o = ecyl(VISOR_A + BEZEL_W, VISOR_B + BEZEL_W, fy - 3, fy + 9)
    vis_o = ecyl(VISOR_A, VISOR_B, fy - 3, fy + 9)
    hd = hd - (ecyl(VISOR_A + BEZEL_W + 0.3, VISOR_B + BEZEL_W + 0.3, fy - 3, fy + 9) & front)
    visor = head_solid(0.0) & vis_o
    visor = visor - inner
    visor = visor - cyl(HOLE_R, 12, (0, fy + 2, 0), "Y")                       # window for the round LCD
    bez = ((head_solid(0.5) & rim_o) - ecyl(VISOR_A - 0.6, VISOR_B - 0.6, fy - 3, fy + 9)) - inner
    slot = None
    for a in range(-44, 45, 4):
        s = box(-STALK_R - 1.0, STALK_R + 1.0, 0.0, 30.0, -STALK_R - 1.0, STALK_R + 1.0).rotate(Axis.X, a)
        slot = s if slot is None else slot + s
    slot_big = None
    for a_ in range(-44, 45, 4):
        sb = box(-STALK_R - 1.6, STALK_R + 1.6, -0.6, 30.0, -STALK_R - 1.6, STALK_R + 1.6).rotate(Axis.X, a_)
        slot_big = sb if slot_big is None else slot_big + sb
    slot_liner = ((slot_big - slot) & head_solid(-0.3)) - head_solid(-2.6)
    hd = hd - slot_big
    hd = hd - inner                     # printed shell, 1.6 mm walls (the concept GLB had a solid head)
    phi = math.radians(55)
    rho = 1 / ((math.sin(phi) / HEAD_R) ** 3 + (math.cos(phi) / HEAD_HF) ** 3) ** (1 / 3)
    my, mz = -rho * math.cos(phi), -rho * math.sin(phi) * HEAD_ZS
    hd = hd - Box(7.0, 6.0, 3.0).rotate(Axis.X, 55).translate((0, my, mz))
    tof_win = Box(6.2, 1.0, 2.4).rotate(Axis.X, 55).translate((0, my + 1.4 * math.cos(phi), mz + 1.4 * math.sin(phi)))
    # seam: head printed as front + back halves, split 1 mm behind the pivot plane
    hd = hd - (box(-40, 40, 0.75, 1.25, -40, 40) - head_solid(-0.5))
    # 2 x M2 button heads from the back half into the front half bosses (screw axis along +Y)
    hd, head_scr = add_screws(hd, [((17.5, 60, -13.0), (0, 1, 0)), ((-17.5, 60, -13.0), (0, 1, 0))])
    # black-painted mask tube between the acrylic window and the LCD glass, acrylic window, LCD glass + active area
    mask = cyl(19.2, LCD_Y0 - (WIN_Y0 + WIN_T) + 0.6, (0, (LCD_Y0 + WIN_Y0 + WIN_T) / 2 - 0.3, 0), "Y") - \
           cyl(HOLE_R + 0.1, 10, (0, LCD_Y0, 0), "Y")
    mask = mask - visor
    window = cyl(WIN_R, WIN_T, (0, WIN_Y0 + WIN_T / 2, 0), "Y")
    lcd_ring = cyl(GLASS_R, 1.8, (0, LCD_Y0 + 0.9, 0), "Y") - cyl(ACT_R, 1.0, (0, LCD_Y0 + 0.4, 0), "Y")
    lcd_act = cyl(ACT_R, 0.6, (0, LCD_Y0 + 0.3 + 0.02, 0), "Y")

    HEAD = {
        "head": [hd],
        "bezel": [bez],
        "visor": [visor],
        "lip": [slot_liner, tof_win],
        "mask": [mask],
        "window": [window],
        "lcd_glass": [lcd_ring],
        "screen_face": [lcd_act],
        "screw": head_scr,
    }
    HP = dict(I.head_parts())
    HEAD["internal_pcb"] = [HP["gc9a01_pcb"], HP["esp32s3_supermini"]]
    HEAD["internal_chip"] = [HP["esp32_can"], HP["esp32_usbc"]]
    HEAD_WIRES = [v for k, v in HP.items() if k.startswith("neck_flex")]

    # ----------------------------------------------------------------- wires (x-ray), built directly as tubes
    def tube(points, r=0.7, sections=8):
        pts = np.array(points, float)
        out = []
        for a, b in zip(pts[:-1], pts[1:]):
            c = trimesh.creation.cylinder(radius=r, segment=[a, b], sections=sections)
            out.append(c)
            out.append(trimesh.creation.icosphere(subdivisions=1, radius=r).apply_translation(b))
        return trimesh.util.concatenate(out)

    def arcpts(c, r, a0, a1, n=10, plane="yz"):
        out = []
        for k in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * k / n)
            if plane == "yz": out.append((c[0], c[1] + r * math.cos(a), c[2] + r * math.sin(a)))
        return out

    WIRES_HEAD = HEAD_WIRES          # rerouted around the neck servo (internals.head_wires)
    WIRES_BODY = []
    for (hx, hy) in HUB:     # hip + knee servo leads to the PCA9685 headers (x = +-11, y = -30..26)
        for dz, r in ((0.0, 1.0), (2.2, 1.0)):
            WIRES_BODY.append(tube([(hx * 0.7, hy * 0.85, 2.0 + dz), (hx * 0.45, hy * 0.75, 6.5 + dz),
                                    (math.copysign(10.0, hx), math.copysign(min(abs(hy), 28.0), hy), 10.4 + dz)], r, 6))
    WIRES_BODY.append(tube([(0, -34.0, 0.0), (0, -40.0, 0.0), (0, -47.0, 0.0)], 1.6, 8))     # neck flex into the stalk
    # power: KCD1 leads to the perfboard, battery leads from the cell ends to the perfboard (JST 22 AWG)
    for zz in (4.5, -4.5):
        WIRES_BODY.append(tube([(-22.0, 0.0, zz), (-17.0, 0.0, 0.7 * zz), (-15.9, 0.0, -2.3), (-14.6, 0.0, -2.3)], 0.8, 8))
    for xx in (-3.5, 3.5):
        WIRES_BODY.append(tube([(xx, 26.2, -10.0), (xx, 28.6, -6.6), (xx, 28.6, -3.9)], 0.8, 8))

    G = {"body": dict(body, internal_wire=WIRES_BODY), "foot": FOOT, "head": dict(HEAD, internal_wire=WIRES_HEAD)}
    for i, leg in enumerate(LEGS):
        G[f"leg_{leg}"] = LEGLINK[i]
    return G

CACHE = os.path.join(PKG, "src", "cache")
def save_cache(G):
    import pickle
    os.makedirs(CACHE, exist_ok=True); idx = {}
    for g, mats in G.items():
        idx[g] = {}
        for mat, items in mats.items():
            fl = []
            for k, s in enumerate(items):
                if isinstance(s, trimesh.Trimesh):
                    fn = f"{g}__{mat}__{k}.pkl"; pickle.dump(s, open(os.path.join(CACHE, fn), "wb"))
                else:
                    fn = f"{g}__{mat}__{k}.brep"; export_brep(s, os.path.join(CACHE, fn))
                fl.append(fn)
            idx[g][mat] = fl
    json.dump(idx, open(os.path.join(CACHE, "index.json"), "w"), indent=1)
def load_cache():
    import pickle
    idx = json.load(open(os.path.join(CACHE, "index.json"))); G = {}
    for g, mats in idx.items():
        G[g] = {mat: [pickle.load(open(os.path.join(CACHE, f), "rb")) if f.endswith(".pkl") else import_brep(os.path.join(CACHE, f))
                      for f in fl] for mat, fl in mats.items()}
    return G
if "--cached" in sys.argv and os.path.exists(os.path.join(CACHE, "index.json")):
    G = load_cache()
else:
    G = build_geometry(); save_cache(G)
TESS = {"screw": (0.05, 0.4), "metal": (0.03, 0.3), "screen_face": (0.02, 0.08), "lcd_glass": (0.02, 0.08), "window": (0.02, 0.08),
        "mask": (0.03, 0.15), "head": (0.03, 0.07), "shell": (0.04, 0.1), "egg": (0.04, 0.1), "bezel": (0.03, 0.08), "visor": (0.03, 0.08),
        "badge": (0.05, 0.12), "stalk": (0.04, 0.1), "lip": (0.05, 0.15)}

# ----------------------------------------------------------------- scene assembly
scene = trimesh.Scene()
counts = {}
def addgeo(parent, link, mat, items, T=None, tol=TOL, atol=ATOL):
    meshes = []
    for s in items:
        m = s if isinstance(s, trimesh.Trimesh) else tri(s, tol, atol)
        if T is not None: m.apply_transform(T)
        meshes.append(m)
    m = trimesh.util.concatenate(meshes)
    nm = f"{link}__{mat}"
    scene.add_geometry(m, node_name=nm, geom_name=nm, parent_node_name=link)
    counts[nm] = len(m.faces)

def Tz(psi_deg):
    return trimesh.transformations.rotation_matrix(math.radians(psi_deg), [0, 0, 1])
def Tt(v):
    return trimesh.transformations.translation_matrix(v)

scene.graph.update(frame_from=scene.graph.base_frame, frame_to="body", matrix=np.eye(4))
Hup = Tt((0, 0, HM))
for mat, items in G["body"].items():
    addgeo("body", "body", mat, items, Hup, *TESS.get(mat, (TOL, ATOL)))

for i, leg in enumerate(LEGS):
    hx, hy = HUB[i]; psi = LEG_DIR0[i]
    ln, fn = f"leg_{leg}", f"foot_{leg}"
    scene.graph.update(frame_from="body", frame_to=ln, matrix=Tt((hx, hy, HM)))
    for mat, items in G[ln].items():
        addgeo(ln, ln, mat, items, Tz(psi), *TESS.get(mat, (TOL, ATOL)))
    kx, ky = LC * math.cos(math.radians(psi)), LC * math.sin(math.radians(psi))
    scene.graph.update(frame_from=ln, frame_to=fn, matrix=Tt((kx, ky, 0.0)))
    for mat, items in G["foot"].items():
        mk = {"boot": f"boot_{leg}", "toe": f"toe_{leg}"}.get(mat, mat)
        addgeo(fn, fn, mk, items, Tz(psi), *TESS.get(mat, (TOL, ATOL)))

scene.graph.update(frame_from="body", frame_to="head", matrix=Tt((0, HEAD_C[1], HM)))
for mat, items in G["head"].items():
    addgeo("head", "head", mat, items, None, *TESS.get(mat, (TOL, ATOL)))

out = os.path.join(PKG, "model.glb")
scene.export(out)
tot = sum(counts.values())
info = {"HM": HM, "hubs": HUB, "leg_dir0": LEG_DIR0, "head_c": HEAD_C, "triangles": tot, "per_node": counts}
json.dump(info, open(os.path.join(PKG, "src", "build_info.json"), "w"), indent=1)
print("triangles", tot, "file MB", round(os.path.getsize(out) / 1e6, 2))
for k, v in sorted(counts.items(), key=lambda kv: -kv[1])[:12]:
    print(" ", k, v)
