#!/usr/bin/env python3
"""Build the articulated model.glb for package C (Findik, wheel-pawed roly-poly hamster).

Geometry comes from the concept CAD (concept_C2/model.py, via model_base.py), rebuilt per LINK:
  body                      shell (cream lower body + caramel cap + ears), visor, screens, internals
  leg_fl/fr/rl/rr           one MG90S hip-pitch joint each; origin on the servo spline axis
  wheel_fl/fr/rl/rr         wheel axle (front: free M3 shoulder-screw axle, rear: N20 D-shaft)
Legs are modelled at joint angle 0 (arm pointing straight down) in their own frames; the stand pose
(22 deg) is manifest.pose_rest.  World: mm, Z up, robot faces -Y, origin on the ground under the body
centre, wheels touch Z = 0 in the rest pose.

Additions over the concept CAD (realism): MG90S horn screws (M2 pan head, in a counterbore on the arm's
outer face), two M2 countersunk belly screws, a real USB-C receptacle (metal shell + tongue), TCRT5000
lens pairs visible in the chin slots, black speaker cloth behind the grille, rear N20 wire pair in a
groove on the inner face of the rear arms, MG90S horns embedded in the arms (internal).

usage:  python3 -I build_rig.py   (writes ../model.glb and ../src/rig_info.json)
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(PKG)), "..", "pylib_c"))
os.environ["FAST"] = "1"
exec(open(os.path.join(HERE, "model_base.py")).read(), globals())
import numpy as np
import trimesh

# ------------------------------------------------------------------ legs (per link, joint angle 0)
def leg_vec(k, ang):
    sy = HIPS[k][1]
    a = math.radians(ang)
    return (sy * math.sin(a), -math.cos(a))

def wheel_centre(k, ang):
    sx, sy = HIPS[k]
    _, hy, hh = hip(k)
    dy, dh = leg_vec(k, ang)
    return (sx * (WHEEL_X0 + WHEEL_W / 2), hy + LEG_L * dy, hh + LEG_L * dh)

def build_leg(k, driven):
    """Same solids as concept leg_solids(), at angle 0, assigned to leg_<k> / wheel_<k> links."""
    global CUR
    sx, sy = HIPS[k]
    _, hy, hh = hip(k)
    ang = 0.0
    cx, cy, ch = wheel_centre(k, ang)
    th = ARM_X1 - ARM_X0
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
    # MG90S horn screw: M2 pan head in a 4.6 mm counterbore on the arm's outer face (it is really there:
    # the horn is embedded in the arm and the screw goes in from outside into the spline)
    xo = sx * ARM_X1
    arm = arm - cyl(2.35, 2.4, (xo, hy, hh), "X")
    # wire groove on the inner face of the driven (rear) arms
    if driven:
        arm = arm - box(min(sx * (ARM_X0 - 0.5), sx * (ARM_X0 + 0.9)), max(sx * (ARM_X0 - 0.5), sx * (ARM_X0 + 0.9)),
                        hy - 1.2, hy + 1.2, hh - 23.0, hh - 4.0)
    CUR = "leg_" + k
    add("arm", arm, "leg")
    head = cyl(1.9, 1.3, (xo - sx * (0.15 + 0.65), hy, hh), "X")
    try:
        head = fillet(head.edges().group_by(Axis.X)[-1 if sx > 0 else 0], 0.5)
    except Exception:
        pass
    xc0, xc1 = sorted((sx * (ARM_X1 - 0.75), sx * (ARM_X1 + 1.0)))      # Phillips cross, 0.6 mm deep
    head = head - box(xc0, xc1, hy - 0.3, hy + 0.3, hh - 1.2, hh + 1.2) - box(xc0, xc1, hy - 1.2, hy + 1.2, hh - 0.3, hh + 0.3)
    add("screw", head)
    if driven:
        # 2 x 28 AWG silicone wires (red/black) in the groove; they run up to 4.6 mm from the hip axis and turn
        # inward through the Ø12.6 horn-boss hole of the socket cup, i.e. they cross into the body ON the hip axis
        # region: when the arm swings the wires only orbit 4.6 mm around the axis inside the hole and twist
        # (no arc slot needed; a 40 mm service loop sits inside the body, x-ray only)
        xw = sx * (ARM_X0 + 0.3)
        for dyw, mat in ((-0.55, "wire_red"), (0.55, "wire_black")):
            w = cyl(0.5, 18.0, (xw, hy + dyw, hh - 13.6), "Z")
            w = w + Sphere(0.5).translate((xw, hy + dyw, hh - 4.6))
            x_in = sx * (ARM_X0 - 5.0)
            w = w + cyl(0.5, abs(xw - x_in), ((xw + x_in) / 2, hy + dyw, hh - 4.6), "X")
            add(mat, w)
    # MG90S single-arm horn, embedded in the arm (internal, x-ray only)
    hx = sx * (ARM_X0 + 1.2)
    horn = cyl(3.6, 1.6, (hx, hy, hh), "X") + box(min(hx - 0.8, hx + 0.8), max(hx - 0.8, hx + 0.8), hy - 1.8, hy + 1.8, hh - 15, hh)
    add("internal_horn", horn)

    # wheel (spins on its own link)
    CUR = "wheel_" + k
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
    # hub spokes are hidden by the cap; show 6 lightening dimples in the hub face (real printed hub)
    def place(s):
        s = s.rotate(Axis.Y, 90 * sx)
        return s.translate((cx, cy, ch))
    for part, mat in ((tyre, "tyre"), (hub, "hub"), (capw, "hubcap"), (beans, "beans")):
        add(mat, place(part), "leg")
    CUR = "body"
    return (cx, cy, ch)

LEGS = {}
WHEEL_C = {}
for k in HIPS:
    WHEEL_C[k] = build_leg(k, k in ("rl", "rr"))

# ------------------------------------------------------------------ body extras
CUR = "body"
# USB-C receptacle (8.94 x 3.26 mm stainless shell, mouth 0.4 mm under the shell surface) + black tongue
usb_outer = rbox(-4.47, 4.47, -1.63, 1.63, -7.4, -0.4, 1.55)
usb_inner = rbox(-4.17, 4.17, -1.33, 1.33, -7.0, 0.5, 1.25)
add("usb_metal", place_axis(usb_outer - usb_inner, (0, yu, USB_H), USB_D))
add("usb_tongue", place_axis(box(-3.3, 3.3, -0.35, 0.35, -7.0, -1.2), (0, yu, USB_H), USB_D))
add("usb_tongue", place_axis(box(-4.2, 4.2, -1.35, 1.35, -7.4, -7.0), (0, yu, USB_H), USB_D))
# TCRT5000 in the chin slots: black body with blue-tinted emitter and black detector lenses
for (cx_, cy_, chh_) in CHIN:
    nrm_c = egg_normal(cx_, cy_, chh_)
    add("tcrt_body", place_axis(box(-5.1, 5.1, -2.9, 2.9, -9.5, -3.0), (cx_, cy_, chh_), nrm_c))
    add("tcrt_emitter", place_axis(cyl(1.55, 1.2, (-2.55, 0, -2.6)) + Sphere(1.55).translate((-2.55, 0, -2.0)) & box(-5, 0, -3, 3, -4, -1.6), (cx_, cy_, chh_), nrm_c))
    add("tcrt_detector", place_axis(cyl(1.55, 1.2, (2.55, 0, -2.6)) + Sphere(1.55).translate((2.55, 0, -2.0)) & box(0, 5, -3, 3, -4, -1.6), (cx_, cy_, chh_), nrm_c))
# speaker cloth (black) just behind the grille, in front of the speaker cone
_ysp = egg_surf_y(0, 66.0, +1)
_dsp = egg_normal(0, _ysp, 66.0)
_spd = sag_depth((0, _ysp, 66.0), _dsp, 16.3, WALL) + 0.4
add("speaker_cloth", place_axis(cyl(11.5, 0.3, (0, 0, -_spd + 0.15)), (0, _ysp, 66.0), _dsp))
# M2 countersunk belly screws into the battery-tray bosses (only visible from below)
for sxs in (-1, 1):
    bx_, by_ = sxs * 18.0, 4.0
    r_ = math.hypot(bx_, by_ / YS)
    bh_ = R0 - math.sqrt(R0 * R0 - r_ * r_)
    nb = egg_normal(bx_, by_, bh_)
    hd = cyl(1.9, 0.25, (0, 0, -0.18)) - box(-0.25, 0.25, -1.5, 1.5, -0.2, 0.2) - box(-1.5, 1.5, -0.25, 0.25, -0.2, 0.2)
    add("screw", place_axis(hd, (bx_, by_, bh_), nb))
    LM[("body", "cream")][0] = LM[("body", "cream")][0] - place_axis(cyl(2.0, 1.0, (0, 0, -0.2)), (bx_, by_, bh_), nb)

# ------------------------------------------------------------------ internals (concept, + per-link)
def mg90s(k):
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
    add("internal_servo", mg90s(k))
for k in ("rl", "rr"):
    sx, sy = HIPS[k]
    cx, cy, ch = WHEEL_C[k]
    gb = box(min(sx * 20.6, sx * 29.6), max(sx * 20.6, sx * 29.6), cy - 6, cy + 6, ch - 5, ch + 5)
    mo = cyl(6.0, 15.0, (sx * 13.1, cy, ch), "X") & box(-40, 40, cy - 6, cy + 6, ch - 5, ch + 5)
    endc = cyl(4.5, 1.8, (sx * 4.7, cy, ch), "X")
    shaft = cyl(1.5, 9.0, (sx * 34.1, cy, ch), "X")
    CUR = "leg_" + k
    add("internal_motor", gb + mo + endc)
    add("internal_shaft", shaft)
    CUR = "body"
for k in ("fl", "fr"):
    sx, sy = HIPS[k]
    cx, cy, ch = WHEEL_C[k]
    CUR = "leg_" + k
    add("internal_shaft", cyl(1.5, 16.0, (sx * 30.0, cy, ch), "X"))      # M3 shoulder screw axle
    CUR = "body"

# Battery bay (review fix): 2 x Orion 14500 (Ø14.5 x 50.5 button top) in a PRINTED bay with the spring/plate contacts
# taken out of the BOM's 2xAA holder (the holder itself, 57 mm long, does not fit).  Bay inner length 53.6 mm =
# 50.5 cell + 2.3 compressed spring + 0.8 plate.  Cells raised 1.4 mm and centred between the hip servos (BAT_Y 3.0)
# so the longer bay clears the inner shell; see the clearance print-out below.
BAT_Y, BAT_H, CELL_R, BAY_X = 3.0, 20.0, 7.25, 26.8
for yy in (BAT_Y - CELL_R, BAT_Y + CELL_R):
    add("internal_battery", cyl(CELL_R, 50.5, (0.75, yy, BAT_H), "X"))
    # cell at x = -24.5..+26.0: spring side (-X) 2.3 mm, plate side (+X) 0.8 mm
for yy, sgn in ((BAT_Y - CELL_R, 1), (BAT_Y + CELL_R, -1)):
    add("internal_metal", box(BAY_X - 0.8, BAY_X, yy - 4.5, yy + 4.5, BAT_H - 4.5, BAT_H + 4.5))                  # + plate / bridge (9 x 9)
    add("internal_metal", box(-BAY_X, -BAY_X + 0.6, yy - 4.5, yy + 4.5, BAT_H - 4.5, BAT_H + 4.5)
        + cyl(2.6, 1.7, (-BAY_X + 1.45, yy, BAT_H), "X"))                                                         # - spring (compressed)
add("internal_pcb", box(-15, 15, BAT_Y - 5, BAT_Y + 5, BAT_H + CELL_R + 0.3, BAT_H + CELL_R + 1.9))  # 2S BMS
DECK_H, DEV_H = 55.0, 62.0
add("internal_pcb_esp", box(-34.5, 34.5, -4.0, 21.5, DEV_H, DEV_H + 1.6))                  # ESP32-S3 devkit PCB
add("internal_module", box(-12, 6, -3.0, 20.5, DEV_H + 1.6, DEV_H + 4.8))                   # WROOM-1 can
add("internal_metal", box(29.0, 34.5, -2.0, 7.0, DEV_H + 1.6, DEV_H + 4.8) + box(29.0, 34.5, 11.0, 20.0, DEV_H + 1.6, DEV_H + 4.8))  # 2 x USB-C on the devkit
for (E, d, sx) in EYES:
    dep = SCREEN_DEPTH[sx]
    add("internal_pcb_blue", place_axis(cyl(19.3, 1.6, (0, 0, -dep - 2.1 - 0.8)), E, d))
    add("internal_lcd", place_axis(cyl(GLASS_R, 1.8, (0, 0, -dep - 1.2 - 0.9)), E, d))
SPK_H = 66.0
spk = cyl(16.0, 4.5, (0, 0, -_spd - 2.25)) + cyl(9, 3.0, (0, 0, -_spd - 6.0))
add("internal_speaker", place_axis(spk, (0, _ysp, SPK_H), _dsp))
add("internal_pcb", box(11, 28, 10, 26, DECK_H + 1, DECK_H + 3.5))        # MAX98357A
add("internal_pcb", box(-7, 7, -7, 7, 86.5, 87.9))                       # INMP441
add("internal_pcb", box(-6.5, 6.5, -6, 7, DECK_H + 1, DECK_H + 2.6))     # BMI160
add("internal_pcb_red", box(-9.25, 9.25, 9, 25.5, DECK_H + 1, DECK_H + 4))   # DRV8833
add("internal_pcb", box(-29, -12, -13, 9, DECK_H + 1, DECK_H + 4.5))     # MP1584 servo rail
add("internal_pcb", box(12, 29, -13, 9, DECK_H + 1, DECK_H + 4.5))       # MP1584 logic rail
add("internal_pcb", box(-9, 9, 28.0, 31.5, 21.0, 45.0))                  # 2S USB-C charger
for (cx_, cy_, chh_) in CHIN:
    add("internal_pcb_blue", box(cx_ - 5, cx_ + 5, cy_ + 5.0, cy_ + 10.0, chh_ + 6.0, chh_ + 15.8))   # TCRT5000 module PCB
for sxs in (-1, 1):                                                         # WS2812B cheek LEDs (5x5)
    bx_, bh_ = sxs * 27.0, 21.5
    by_ = egg_surf_y(bx_, bh_)
    add("internal_led", place_axis(box(-2.5, 2.5, -2.5, 2.5, -3.4, -1.8), (bx_, by_, bh_), egg_normal(bx_, by_, bh_)))
for i in range(4):                                                          # Ø6x1.5 mm cap magnets (pairs)
    a = math.radians(45 + 90 * i)
    mx_, my_ = 33 * math.cos(a), 30 * math.sin(a)
    mz_ = (SPLIT_F + SPLIT_B) / 2 - (my_ * (SPLIT_F - SPLIT_B) / (2 * R0 * YS))
    add("internal_magnet", cyl(3.0, 3.0, (mx_, my_, mz_)))                 # Ø6 x 1.5 pair (cap + body)
ch_ = None
for k, (sx, sy) in HIPS.items():
    _, hy, hh = hip(k)
    xa, xb = sorted((sx * 15.6, sx * 18.6))
    plate = box(xa, xb, hy - 9, hy + 9, hh - 9, hh + 23) - box(xa - 1, xb + 1, hy - 6.3, hy + 6.3, hh - 6.4, hh + 16.9)
    ch_ = plate if ch_ is None else ch_ + plate
tray = box(-BAY_X, BAY_X, BAT_Y - 15, BAT_Y + 15, BAT_H - CELL_R - 1.6, BAT_H - CELL_R - 0.1) \
    + box(-BAY_X - 1.2, -BAY_X, BAT_Y - 15, BAT_Y + 15, BAT_H - CELL_R - 0.5, BAT_H + 6) + box(BAY_X, BAY_X + 1.2, BAT_Y - 15, BAT_Y + 15, BAT_H - CELL_R - 0.5, BAT_H + 6)
# clearance of the cells and contacts to the inner shell (WALL) and to the hip servo cases
def _clr(x, y, h):
    if not egg_inside(x, y, h, o=WALL):
        return -1.0
    lo_, hi_ = 0.0, 10.0
    for _ in range(30):
        mid = (lo_ + hi_) / 2
        if egg_inside(x, y, h, o=WALL + mid): lo_ = mid
        else: hi_ = mid
    return lo_
_cells = min(_clr(x, yc + CELL_R * math.cos(a), BAT_H + CELL_R * math.sin(a)) for x in np.linspace(-24.5, 26.0, 30)
             for yc in (BAT_Y - CELL_R, BAT_Y + CELL_R) for a in np.linspace(0, 2 * math.pi, 60))
_plates = min(_clr(sx_ * BAY_X, yc + dy, BAT_H + dz) for sx_ in (-1, 1) for yc in (BAT_Y - CELL_R, BAT_Y + CELL_R)
              for dy in np.linspace(-4.5, 4.5, 9) for dz in np.linspace(-4.5, 4.5, 9))
print("battery bay: min clearance to the inner shell: cells %.2f mm, contacts %.2f mm" % (_cells, _plates))
_srv = min(25.9 - (BAT_H + math.sqrt(max(0, CELL_R ** 2 - (abs(y_e - y_c)) ** 2))) for y_c in (BAT_Y - CELL_R, BAT_Y + CELL_R) for y_e in (-9.4, 15.4) if abs(y_e - y_c) < CELL_R)
print("battery bay: min vertical clearance cells -> MG90S case bottoms %.2f mm" % _srv)
deck = box(-30, 30, -14, 26, DECK_H - 0.8, DECK_H + 0.8)
spine = box(-1.2, 1.2, -12, 14, 28.6, DECK_H)
ch_ = (ch_ + tray + deck + spine) & egg_off(WALL + 0.4)
add("internal_chassis", ch_)

# ------------------------------------------------------------------ frames
STAND_DEG = STAND
def wheel_low_z(ang):
    _, hy, hh = hip("fl")
    return hh - LEG_L * math.cos(math.radians(ang)) - WHEEL_R
GZ = -wheel_low_z(STAND_DEG)                 # lift so the tyres touch Z = 0 in the rest pose
FR = {"body": ("world", np.eye(4))}
LINK_ORIGIN = {"body": np.array([0.0, 0.0, -GZ])}          # vertex(model) -> vertex(link) = v - origin
for k in HIPS:
    sx, sy = HIPS[k]
    hp = np.array(hip(k), float)
    LINK_ORIGIN["leg_" + k] = hp
    LINK_ORIGIN["wheel_" + k] = np.array(WHEEL_C[k], float)
    T = np.eye(4); T[:3, 3] = hp + [0, 0, GZ]
    FR["leg_" + k] = ("body", T)
    T2 = np.eye(4); T2[:3, 3] = np.array(WHEEL_C[k]) - hp
    FR["wheel_" + k] = ("leg_" + k, T2)

# ------------------------------------------------------------------ tessellate + export
FINE = {"screen_eyeL", "screen_eyeR", "lcd_glass"}
def tess(solids, key):
    tol, ang = (0.05, 0.15)
    if key in ("cream", "cap", "visor", "nose", "ear", "ear_inner"):
        tol, ang = 0.015, 0.07          # big smooth glossy/matte shells: avoid visible facets
    if key in ("visor", "nose"):
        tol, ang = 0.004, 0.035         # glossy: reflections show every facet
    if key.startswith("internal_"):
        tol, ang = 0.12, 0.35
    if key in ("screw", "usb_metal", "usb_tongue", "tcrt_emitter", "tcrt_detector", "tcrt_body", "beans", "wire_red", "wire_black"):
        tol, ang = 0.03, 0.3
    if key in FINE:
        tol, ang = 0.02, 0.06
    V, F, off = [], [], 0
    for s in solids:
        if s is None:
            continue
        v, t = s.tessellate(tol, ang)
        if not t:
            continue
        V.append(np.array([[p.X, p.Y, p.Z] for p in v])); F.append(np.array(t) + off); off += len(v)
    if not V:
        return None
    return trimesh.Trimesh(np.vstack(V), np.vstack(F), process=True)

def decimate(m, target):
    if len(m.faces) <= target:
        return m
    import fast_simplification
    v, f = fast_simplification.simplify(m.vertices.astype(np.float32), m.faces.astype(np.int64), 1 - target / len(m.faces))
    return trimesh.Trimesh(v, f, process=True)

BUDGET = {"cream": 70000, "cap": 50000, "arm": 12000, "tyre": 7800, "hubcap": 4000,
          "ear": 8000, "ear_inner": 4000, "internal_chassis": 6000, "nose": 4000}
ANALYTIC = {"cream", "cap", "visor"}      # outer skin of the egg: use exact surface normals (no facet shimmer)
def smooth(m, key):
    """split vertices at > 40 deg creases (same rule rig.js uses), then for the egg's outer skin replace
    the averaged normals by the analytic egg normals.  Returns a mesh in the link frame with normals."""
    m = trimesh.graph.smooth_shade(m, angle=math.radians(40), facet_minarea=1e12)
    vn = np.array(m.vertex_normals)
    if key in ANALYTIC:
        n_rep = 0
        for i, (x, y, h) in enumerate(m.vertices):
            if egg_inside(x, y, h, o=0.7) or not egg_inside(x, y, h, o=-0.15):
                continue
            g = np.array(egg_normal(x, y, h))
            if np.dot(g, vn[i]) > math.cos(math.radians(25)):
                vn[i] = g; n_rep += 1
        print("   analytic normals", key, n_rep, "/", len(vn))
    return m, vn

scene = trimesh.Scene(base_frame="world")          # "world" is not exported; "body" is the only top-level node
for link, (parent, T) in FR.items():
    scene.graph.update(frame_from=parent, frame_to=link, matrix=T)
stats = {}
for (link, key), solids in sorted(LM.items(), key=lambda kv: (list(FR).index(kv[0][0]), kv[0][1])):
    m = tess(solids, key)
    if m is None:
        print("empty", link, key); continue
    n0 = len(m.faces)
    if key in BUDGET:
        m = decimate(m, BUDGET[key])
    if key in ANALYTIC:
        m, vn = smooth(m, key)
        m = trimesh.Trimesh(m.vertices - LINK_ORIGIN[link], m.faces, vertex_normals=vn, process=False)
    else:          # no normals in the file: rig.js computes the same 40 deg crease normals (smaller GLB)
        m = trimesh.Trimesh(m.vertices - LINK_ORIGIN[link], m.faces, process=False)
    nm = f"{link}__{key}"
    scene.add_geometry(m, node_name=nm, geom_name=nm, parent_node_name=link)
    stats[nm] = [n0, len(m.faces)]
    print(f"{nm:34s} {n0:7d} -> {len(m.faces):7d}")
glb = trimesh.exchange.gltf.export_glb(scene, include_normals=None)   # only meshes with cached normals (the analytic egg skins)
open(os.path.join(PKG, "model.glb"), "wb").write(glb)
tot = sum(v[1] for v in stats.values())
vis_tot = sum(v[1] for k, v in stats.items() if "__internal_" not in k)
info = {"GZ": GZ, "triangles": tot, "triangles_visible": vis_tot, "meshes": stats,
        "frames": {k: [round(float(x), 3) for x in v[1][:3, 3]] for k, v in FR.items()},
        "screen_depth_mm": SCREEN_DEPTH, "eyes": [[list(E), list(d), sx] for (E, d, sx) in EYES],
        "split_plane_normal": list(nrm), "split_heights": [SPLIT_F, SPLIT_B]}
json.dump(info, open(os.path.join(HERE, "rig_info.json"), "w"), indent=1, default=float)
print("triangles", tot, "visible", vis_tot, "GZ", GZ, "glb bytes", len(glb))
