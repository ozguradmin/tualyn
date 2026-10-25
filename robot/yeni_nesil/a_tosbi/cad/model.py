#!/usr/bin/env python3
"""
Concept A "Tosbi" - a two-faced turtle desk walker (Sesame lineage: 8 leg servos + 1 neck servo).

Units mm, Z up, robot faces -Y, ground at Z=0 (standing pose).
Body frame B: origin at the body centre on the mid-plane.  World = B + (0, 0, HM).

Usage:  python3 -I model.py [pose] [outdir]
   pose: stand (default) | wave | flip | yawfwd | yawback | pitchup | pitchdown | flat
Exports one STL per material group into outdir, parts.json (volumes, areas, bbox)
and one STL per named part in outdir/parts/ for the fit checks (check.py).
"""
import json, math, os, sys
from build123d import *

# ----------------------------------------------------------------- parameters
W, L, T = 82.0, 84.0, 48.0          # body pebble (x, y, z)
RC = 30.0                           # plan corner radius
SEC_A, SEC_B = 26.0, 20.0           # section roll (horizontal, vertical) -> domed carapace
RIM = 4.5                           # |z| < RIM : cream rim band ("bridge")
WALL = 1.8

CC = (W / 2 - RC, L / 2 - RC)       # corner-arc centre (13, 14)
HUB_ANG = 35.0                      # hubs sit on the corner arcs at +-35 deg, 9.3 mm inside the edge
HUB_IN = 6.0
def _hub(sx, sy):
    a = math.radians(HUB_ANG)
    r = RC - HUB_IN
    return (sx * (CC[0] + r * math.cos(a)), sy * (CC[1] + r * math.sin(a)))
HUB = [_hub(1, -1), _hub(-1, -1), _hub(1, 1), _hub(-1, 1)]          # FR, FL, RR, RL  (x>0 = robot's left)
LEG_DIR0 = [-HUB_ANG, 180 + HUB_ANG, HUB_ANG, 180 - HUB_ANG]           # legs leave along the corner normal
SERVO_DIR = [120.0, 60.0, -120.0, -60.0]                               # hip servo bodies point inward
YAW_RANGE = 20.0                    # +- gait swing about nominal
HUB_R, HUB_H, HUB_P = 13.2, 19.5, 2.6   # hub "egg" (superellipsoid of revolution)
SOCK_GAP = 0.8                      # socket reveal around the egg
LC = 33.0                           # hip axis -> knee axis
POD_HW, POD_HZ = 17.0, 9.5          # knee pod half width (v), half thickness (z)
NECK_HW = 9.0                       # narrow arm root through the socket mouth
LF = 36.0                           # knee axis -> toe ball centre
TOE_R = 7.0                         # toe = TPU capsule (radius) lying along the knee axis
BETA0 = 80.0                        # stance: foot angle below the flipper plane
HM = LF * math.sin(math.radians(BETA0)) + TOE_R      # mid-plane height when standing
HIP_SERVO_Z = 13.0                  # hip servo hump top (horn top +16, egg top +19.5)

HEAD_R, HEAD_HF, HEAD_HB, HEAD_PF, HEAD_PB = 33.0, 18.0, 22.0, 3.0, 2.3
HEAD_ZS = 0.88                      # head is 66 wide x 58 tall
HEAD_GAP = 5.0                      # body front -> head rear
HEAD_C = (0.0, -(L / 2 + HEAD_GAP + HEAD_HB), 0.0)   # head centre = neck pitch pivot (servo inside head)
VISOR_A, VISOR_B = 26.3, 18.3          # oval face visor semi-axes (x, z)
BEZEL_W = 2.6                       # coral pin-stripe ring around the visor
STALK_R = 7.5

MAT = {}      # material -> list of world solids
PARTS = {}    # named world solids for fit checks
def add(mat, s, name=None):
    MAT.setdefault(mat, []).append(s)
    if name:
        PARTS[name] = s

# ----------------------------------------------------------------- helpers
def rrect_wire(w, l, r, z):
    r = max(0.3, min(r, w / 2 - 0.05, l / 2 - 0.05))
    return RectangleRounded(w, l, r).wires()[0].moved(Location((0, 0, z)))

def pebble(Wd, Ld, Td, rc, a, b, off=0.0, n=10):
    """Soap-bar solid: rounded-rect plan, elliptic roll of (a horizontal, b vertical) at top and bottom."""
    z0 = Td / 2 - b
    zs = {0.0, z0 * 0.5, -z0 * 0.5}
    for i in range(n + 1):
        zz = z0 + b * math.sin(i / n * math.pi / 2)
        zs.add(zz); zs.add(-zz)
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
    if axis == "X":
        c = c.rotate(Axis.Y, 90)
    elif axis == "Y":
        c = c.rotate(Axis.X, 90)
    return c.translate(center)

def box(x0, x1, y0, y1, z0, z1):
    return Box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))

def egg2(R, Ht, Hb, pt, pb, n=26):
    """Revolved superellipse about Z: (r/R)^p + (z/H)^p = 1, separate top/bottom half-height + exponent."""
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
    """MG90S envelope (22.8 x 12.2 x 28.5, tabs 32.5). Shaft along +Z, origin = shaft base on the gear hump.
    Body extends along +X (shaft is 6 mm from the -X end). tabs = (shaft-end tab, far-end tab)."""
    s = box(-6.0, 16.8, -6.1, 6.1, -28.5, -6.0)
    s += cyl(6.1, 6.0, (0, 0, -3.0))
    s += cyl(3.6, 4.5, (6.5, 0, -3.75))
    if tabs[0]:
        s += box(-10.85, -6.0, -6.1, 6.1, -12.6, -10.1)
    if tabs[1]:
        s += box(16.8, 21.65, -6.1, 6.1, -12.6, -10.1)
    s += cyl(2.4, 3.5, (0, 0, 1.75))
    if horn_r:
        s += cyl(horn_r, 2.0, (0, 0, 2.0))
    return s

def world(s):
    return s.translate((0, 0, HM))

# ----------------------------------------------------------------- pose
POSE = sys.argv[1] if len(sys.argv) > 1 else "stand"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", POSE)
os.makedirs(os.path.join(OUT, "parts"), exist_ok=True)

yaw = list(LEG_DIR0)
knee = [BETA0] * 4           # foot angle below the flipper plane (deg); negative = foot up
neck = 15.0                  # +: face pitched up (about the head centre)
if POSE == "wave":
    neck = 26.0
    knee = [-15.0, BETA0, BETA0 - 4, BETA0]
    yaw[0] = LEG_DIR0[0] - 15.0
FRONT_FWD = 14.0             # front legs may swing only 14 deg forward (head clearance), 20 deg back
if POSE == "yawfwd":         # all legs at the forward end of the gait swing
    yaw = [LEG_DIR0[0] - FRONT_FWD, LEG_DIR0[1] + FRONT_FWD, LEG_DIR0[2] - YAW_RANGE, LEG_DIR0[3] + YAW_RANGE]
if POSE == "yawback":
    yaw = [LEG_DIR0[0] + YAW_RANGE, LEG_DIR0[1] - YAW_RANGE, LEG_DIR0[2] + YAW_RANGE, LEG_DIR0[3] - YAW_RANGE]
if POSE == "pitchup":
    neck = 40.0
if POSE == "pitchdown":
    neck = -40.0
if POSE == "flat":           # feet folded out horizontal (belly-down / flip transition)
    knee = [0.0] * 4
if POSE == "flip":           # upside down: knees swing through the flipper plane, neck mirrored
    knee = [-BETA0] * 4
    neck = -15.0
if POSE == "fallen":         # just landed on its back: feet still in the air
    neck = 0.0
if POSE == "transit":        # on its back, knees swinging through the flipper plane
    knee = [-10.0] * 4
    neck = -8.0

# ----------------------------------------------------------------- body shell
body_out = pebble(W, L, T, RC, SEC_A, SEC_B)
body_in = pebble(W, L, T, RC, SEC_A, SEC_B, off=WALL)
sock = egg2(HUB_R + SOCK_GAP, HUB_H + SOCK_GAP, HUB_H + SOCK_GAP, HUB_P, HUB_P)
sockets = None
for (hx, hy) in HUB:
    c = sock.translate((hx, hy, 0))
    sockets = c if sockets is None else sockets + c
stalk_hole = cyl(STALK_R + 0.8, 12.0, (0, -L / 2, 0), "Y")
tail_hole = box(-4.6, 4.6, L / 2 - 8, L / 2 + 6, -1.7, 1.7)
tail_slot = cyl(7.3, 14.0, (0, L / 2 - 0.5, 0), "Y") & box(-9, 9, L / 2 - 9, L / 2 + 6, -4.8, 4.8)

shell = body_out - body_in - sockets - stalk_hole - tail_slot

def zone(z0, z1):
    return box(-80, 80, -80, 80, z0, z1)

shell_top = (shell & zone(0.4, 40)) - tail_hole
shell_bot = (shell & zone(-40, -0.4)) - tail_hole
lip = (pebble(W, L, T, RC, SEC_A, SEC_B, off=1.0) - body_in) & zone(-1.6, 1.6)
lip = lip - sockets - stalk_hole - tail_hole

def scute_cutter(sign):
    """1.0 mm deep, 1.5 mm wide grooves: central hexagon + six spokes (turtle scutes) on each dome."""
    R = 15.0
    pts = [(R * math.cos(math.radians(60 * i)), R * math.sin(math.radians(60 * i))) for i in range(6)]
    segs = [(pts[i], pts[(i + 1) % 6]) for i in range(6)]
    for p in pts:
        a = math.atan2(p[1], p[0])
        segs.append((p, (p[0] + 70 * math.cos(a), p[1] + 70 * math.sin(a))))
    g = None
    for (a, b) in segs:
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        s = Box(ln + 1.3, 1.5, 40).rotate(Axis.Z, ang).translate(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, sign * 25))
        g = s if g is None else g + s
    skin = body_out - pebble(W, L, T, RC, SEC_A, SEC_B, off=1.0)
    z = zone(8.0, 40) if sign > 0 else zone(-40, -8.0)
    return g & skin & z

shell_top = shell_top - scute_cutter(+1)
shell_bot = shell_bot - scute_cutter(-1)
hexr = 15.0 - 0.75 - 0.05
hexp = extrude(RegularPolygon(hexr, 6, major_radius=True, align=(Align.CENTER, Align.CENTER)), amount=60, both=True)
hexp = hexp.rotate(Axis.Z, 0)
badge_t = shell_top & hexp
badge_b = shell_bot & hexp
shell_top = shell_top - hexp
shell_bot = shell_bot - hexp

tail = cyl(6.5, 12.0, (0, L / 2 - 0.5, 0), "Y") & box(-8, 8, L / 2 - 6.5, L / 2 + 3.6, -4.0, 4.0)
try:
    tail = tail.fillet(1.6, [e for e in tail.edges() if e.center().Y > L / 2 + 3.0])
except Exception:
    pass
tail = tail - tail_hole - body_in
usb = box(-4.45, 4.45, L / 2 - 7.5, L / 2 + 2.6, -1.6, 1.6)

add("shell", world(shell_top), "shell_top"); add("shell", world(shell_bot), "shell_bot")
add("skin", world(tail), "tail")
add("accent", world(badge_t), "badge_top"); add("accent", world(badge_b), "badge_bot")   # "pat me" touch scute
add("dark", world(lip), "lip"); add("metal", world(usb), "usb")

# ----------------------------------------------------------------- legs
KNEE_R = 11.4                       # knee barrel radius (body of revolution about the knee axis)
KNEE_HW = 20.3                      # knee barrel half length; |v| > CAP_V belongs to the foot (end caps)
CAP_V = 17.5
REVEAL = 0.4

def knee_barrel():
    b = cyl(KNEE_R, 2 * KNEE_HW, (0, 0, 0), "Y")
    return b.fillet(4.5, b.edges().filter_by(GeomType.CIRCLE))

def pod_parts(window_center_deg):
    """Leg frame (u=+X radial, v=+Y, z). Returns (egg hub, arm). The egg carries the hip horn (top)
    and the bearing pin (bottom); the C-window lets the fixed hip servo pass through its inner side.
    The arm ends in the middle of a knee barrel whose two end caps belong to the foot."""
    hub = egg2(HUB_R, HUB_H, HUB_H, HUB_P, HUB_P)
    pts = [(0, -NECK_HW), (11.0, -NECK_HW), (16.2, -POD_HW), (LC + 2, -POD_HW),
           (LC + 2, POD_HW), (16.2, POD_HW), (11.0, NECK_HW), (0, NECK_HW)]
    sk = Polygon(*pts, align=None)
    try:
        sk = fillet(sk.vertices().filter_by(lambda v: 10 < v.X < 17), 5.0)
    except Exception as e:
        print("2d fillet failed", e)
    arm = extrude(sk, amount=POD_HZ, both=True)
    for rf in (7.0, 6.5, 6.0, 5.0):
        try:
            arm = arm.fillet(rf, arm.edges().filter_by(lambda e: abs(abs(e.center().Z) - POD_HZ) < 0.01 and e.center().X > 4))
            break
        except Exception:
            continue
    arm = arm & box(-30, LC, -40, 40, -20, 20)
    mid = knee_barrel().translate((LC, 0, 0)) & box(0, 80, -(CAP_V - REVEAL), CAP_V - REVEAL, -20, 20)
    arm = arm + mid
    arm = arm - cyl(9.6, 3.0, (LC, CAP_V - 1.4, 0), "Y")          # horn window (foot cap screws onto horn)
    arm = arm - cyl(2.6, 4.0, (LC, -(CAP_V - 1.5), 0), "Y")       # bearing-pin hole
    arm = arm - hub
    w = None
    for a in range(-54, 55, 6):
        s = box(9.5, 15.0, -3.6, 3.6, -16.5, 7.6).rotate(Axis.Z, window_center_deg + a)
        w = s if w is None else w + s
    return hub - w, arm

def foot_parts():
    """Foot frame: knee axis = Y through origin, foot points along +X (s), toe capsule axis at X=LF.
    The two knee-barrel end caps (horn side / bearing-pin side) are part of the foot, so the joint
    stays a seamless barrel at every knee angle; the boot starts outside the arm's sweep."""
    caps = knee_barrel() - box(-30, 30, -CAP_V, CAP_V, -30, 30)
    pin = cyl(2.4, 3.6, (0, -(CAP_V - 1.6), 0), "Y")
    # hidden "cuffs": convex hull of a r=10.5 disc and the boot-top corners, inset under the cap ends
    rc_, P = 10.0, (13.0, 8.5)
    dP = math.hypot(*P); th = math.atan2(P[1], P[0]) + math.acos(rc_ / dP)
    pts = [P] + [(rc_ * math.cos(a), rc_ * math.sin(a)) for a in
                 [th + (2 * math.pi - 2 * th) * k / 40 for k in range(41)]] + [(P[0], -P[1])]
    hull = Polygon(*[(x, z) for (x, z) in pts], align=None)          # sketch in XY = (s, w)
    tabs = None
    for sg in (1, -1):
        t = extrude(hull, amount=1.0).rotate(Axis.X, 90)                 # XY -> XZ plane, thickness along -Y
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
    return f + (toe & cut), toe - cut

pod_cache = {}
for i, ((hx, hy), d0, sdir) in enumerate(zip(HUB, LEG_DIR0, SERVO_DIR)):
    psi = yaw[i]
    key = round(sdir - d0, 3)
    if key not in pod_cache:
        pod_cache[key] = pod_parts(sdir - d0)
    eggp, arm = pod_cache[key]
    ks = mg90s(tabs=(False, True)).rotate(Axis.X, -90).rotate(Axis.Y, 180).translate((LC, 14.25, 0))
    f, cap = foot_parts()
    beta = knee[i]
    f = f.rotate(Axis.Y, beta).translate((LC, 0, 0))
    cap = cap.rotate(Axis.Y, beta).translate((LC, 0, 0))
    to_body = lambda s: s.rotate(Axis.Z, psi).translate((hx, hy, 0))
    add("shell", world(to_body(eggp)), f"egg{i}")
    add("leg", world(to_body(arm)), f"arm{i}")
    add("leg", world(to_body(f)), f"foot{i}")
    add("tpu", world(to_body(cap)), f"toe{i}")
    add("servo", world(to_body(ks)), f"knee_servo{i}")
    hs = mg90s(tabs=(False, True)).rotate(Axis.Z, sdir).translate((hx, hy, HIP_SERVO_Z))
    add("servo", world(hs), f"hip_servo{i}")

# ----------------------------------------------------------------- neck stalk (fixed) + head (pitches about its centre)
# Neck: the MG90S is FIXED on the stalk inside the head (body pointing back, far-end tab bolted to the
# stalk plate); its horn drives a bracket on the head's inner wall, the other side runs on a pin.
# The head and everything in it pitch around the fixed servo, so only a slim stalk crosses the gap.
NECK_SERVO_X = 12.0
stalk_y1 = HEAD_C[1] + 21.7                                     # stalk plate meets the servo tab
stalk = cyl(STALK_R, (-L / 2 + 5.0) - stalk_y1, (0, (stalk_y1 + (-L / 2 + 5.0)) / 2, 0), "Y")
neck_servo = mg90s(tabs=(False, True)).rotate(Axis.Z, 90).rotate(Axis.Y, 90).translate((NECK_SERVO_X, HEAD_C[1], 0))
plate = box(-6.0, 6.0, stalk_y1 - 0.01, stalk_y1 + 3.0, -6.1, 6.1) - neck_servo
add("skin", world(stalk), "stalk")
add("servo", world(neck_servo), "neck_servo")
add("pcb", world(plate), "stalk_plate")

def head_parts():
    """Head frame = head centre (pivot). Face toward -Y."""
    hp = {}
    def head_solid(dr):
        h = egg2(HEAD_R + dr, HEAD_HF + dr, HEAD_HB + dr, HEAD_PF, HEAD_PB).rotate(Axis.X, 90)
        return scale(h, by=(1.0, 1.0, HEAD_ZS))                                  # mochi: wider than tall
    def ecyl(a, b, y0, y1):
        return scale(cyl(b, y1 - y0, (0, (y0 + y1) / 2, 0), "Y"), by=(a / b, 1.0, 1.0))
    hd = head_solid(0.0)
    fy = -HEAD_HF
    inner = head_solid(-1.6)
    front = box(-40, 40, fy - 3, fy + 9, -40, 40)
    rim_o = ecyl(VISOR_A + BEZEL_W, VISOR_B + BEZEL_W, fy - 3, fy + 9)
    vis_o = ecyl(VISOR_A, VISOR_B, fy - 3, fy + 9)
    hd = hd - (ecyl(VISOR_A + BEZEL_W + 0.3, VISOR_B + BEZEL_W + 0.3, fy - 3, fy + 9) & front)
    visor = (hd_full := head_solid(0.0)) & vis_o
    visor = visor - inner
    bez = ((head_solid(0.5) & rim_o) - ecyl(VISOR_A - 0.6, VISOR_B - 0.6, fy - 3, fy + 9)) - inner
    # rear slot for the fixed stalk over the +-40 deg pitch range
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
    # ToF window on the chin (reads as a tiny mouth), aimed ~35 deg below the face axis
    phi = math.radians(55)
    rho = 1 / ((math.sin(phi) / HEAD_R) ** 3 + (math.cos(phi) / HEAD_HF) ** 3) ** (1 / 3)
    my, mz = -rho * math.cos(phi), -rho * math.sin(phi) * HEAD_ZS
    hd = hd - Box(7.0, 6.0, 3.0).rotate(Axis.X, 55).translate((0, my, mz))
    hp["skin"] = [hd]
    hp["accent"] = [bez]
    hp["visor"] = [visor]
    hp["dark"] = [slot_liner, Box(6.2, 1.0, 2.4).rotate(Axis.X, 55).translate((0, my + 1.4 * math.cos(phi), mz + 1.4 * math.sin(phi)))]
    # internals: GC9A01 module (round PCB + header tab), glass, ESP32-S3 SuperMini, VL53L0X, neck servo
    hp["pcb"] = [cyl(19.25, 1.6, (0, fy + 8.2, 0), "Y") + box(19.0, 25.8, fy + 7.4, fy + 9.0, -6, 6),
                 box(-11.25, 11.25, -9.0, 9.0, 20.6, 24.6),
                 Box(13.0, 1.6, 11.0).rotate(Axis.X, 55).translate((0, my + 6.0 * math.cos(phi), mz + 6.0 * math.sin(phi)))]
    hp["chip"] = [cyl(17.8, 1.8, (0, fy + 6.5, 0), "Y")]
    return hp

hp = head_parts()
for mat, lst in hp.items():
    for j, s in enumerate(lst):
        add(mat, world(s.rotate(Axis.X, -neck).translate(HEAD_C)), f"head_{mat}{j}")

# ----------------------------------------------------------------- body internals (envelopes)
add("cell", world(cyl(7.1, 50.5, (-7.3, 0.0, -13.4), "Y")), "cell_l")             # 2 x 14500 (2S)
add("cell", world(cyl(7.1, 50.5, (+7.3, 0.0, -13.4), "Y")), "cell_r")
add("pcb", world(box(-12.7, 12.7, -33.0, 29.0, 7.4, 9.0)), "pca9685")              # PCA9685 62 x 25.4
add("chip", world(box(-6, 6, -8, 8, 9.0, 10.8)), "pca_chip")
add("pcb", world(box(-11.0, 11.0, -26.0, -9.0, -5.6, -1.4)), "mp1584_servoA")      # 22 x 17 each
add("pcb", world(box(-11.0, 11.0, -8.5, 8.5, -5.6, -1.4)), "mp1584_servoB")
add("pcb", world(box(-11.0, 11.0, 9.5, 26.5, -5.6, -1.4)), "mp1584_logic")
add("pcb", world(box(-12.0, -1.0, -26.0, -8.0, 1.0, 5.4)), "pam8403")
add("pcb", world(box(1.0, 12.0, -20.0, -8.0, 1.0, 3.0)), "bmi160")
add("pcb", world(box(-15.0, 15.0, -6.5, 0.5, 1.0, 4.0)), "bms_2s")
add("pcb", world(box(-12.5, 12.5, 10.0, 27.0, 1.0, 5.4)), "charger_2s_usbc")
add("pcb", world(box(-5.5, 5.5, 35.0, 39.8, -2.5, 2.5)), "usbc_breakout")
add("speaker", world(cyl(14.5, 4.0, (0, 32.5, 0), "Y")), "speaker29")
add("pcb", world(box(-10.0, 10.0, -39.5, -34.5, -6.0, 6.0)), "stalk_mount")

# ----------------------------------------------------------------- flip pose: whole robot rotated about Y
if POSE in ("flip", "fallen", "transit"):
    for mat in MAT:
        MAT[mat] = [s.translate((0, 0, -HM)).rotate(Axis.Y, 180).translate((0, 0, HM)) for s in MAT[mat]]
    PARTS = {}

# ----------------------------------------------------------------- export
info = {"pose": POSE, "HM": round(HM, 2), "materials": {}, "parts": {}}
for mat, lst in MAT.items():
    comp = Compound(children=lst) if len(lst) > 1 else lst[0]
    export_stl(comp, os.path.join(OUT, f"{mat}.stl"), tolerance=0.03, angular_tolerance=0.08)
    info["materials"][mat] = {"n": len(lst), "volume_cm3": round(sum(s.volume for s in lst) / 1000, 2),
                              "area_cm2": round(sum(s.area for s in lst) / 100, 1)}
for name, s in PARTS.items():
    export_stl(s, os.path.join(OUT, "parts", f"{name}.stl"), tolerance=0.05, angular_tolerance=0.15)
    info["parts"][name] = {"volume_cm3": round(s.volume / 1000, 3), "area_cm2": round(s.area / 100, 2)}
bb = Compound(children=[s for l in MAT.values() for s in l]).bounding_box()
info["bbox"] = [round(v, 1) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)]
json.dump(info, open(os.path.join(OUT, "parts.json"), "w"), indent=1)
print("HM", round(HM, 2), "bbox", info["bbox"], "hubs", [tuple(round(c, 1) for c in h) for h in HUB])
