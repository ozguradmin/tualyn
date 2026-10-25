"""Tosbi internals at the size of the parts the BOM actually buys (review fix, 2026-10-25).

Body parts are in the body MID-PLANE frame (build_glb.up() shifts them by HM), head parts in the head frame
(pitch pivot at the origin, face toward -Y). Every part is a list of (name, solid) so fit_check.py can test them
one by one; build_glb.py concatenates them per matKey.

Sizes (BOM / datasheets, mm):
  MPU6050 GY-521            21 x 16 x 1.6 PCB + QFN 4 x 4 x 0.9
  2S USB-C charger (Motorobit) 39 x 18 x 6.3 (product page)
  PAM8403 + volume pot      24 x 21 x 1.6 PCB + RV09-type pot 10 x 11 x 5 + D6 x 7 shaft (typical, page gives no size)
  GY-53 VL53L0X + STM32     25 x 15.6 x 1.6 PCB + sensor 4.4 x 2.4 x 1.0 + STM32 5 x 5 x 1
  KCD1 rocker               bezel 21 x 15 x 1.5, panel cut-out 19 x 13, body 19 x 12.5 x 10.5 + 2 tabs 7 mm
  perfboard                 3 x 7 cm cut down to 30 x 60 x 1.6
  MP1584EN                  22 x 17 x 4 (1.0 PCB + 3.0 parts)
  caps                      1000 uF 10 V D8 x 12 (x2), 470 uF 16 V D6.3 x 11
"""
import math
from build123d import *

# ----------------------------------------------------------------- helpers
def box(x0, x1, y0, y1, z0, z1):
    return Box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))

def cyl(r, h, center=(0, 0, 0), axis="Z"):
    c = Cylinder(r, h)
    if axis == "X": c = c.rotate(Axis.Y, 90)
    elif axis == "Y": c = c.rotate(Axis.X, 90)
    return c.translate(center)

def rbox(w, l, h, r):
    """box centred at the origin (w along x), corners rounded in the y-z plane (edges parallel to X)"""
    b = Box(w, l, h)
    return b.fillet(r, b.edges().filter_by(Axis.X))

# ----------------------------------------------------------------- body (mid-plane frame)
CELL_Z = -14.0             # 2 x 14500 (D14.2 x 50.5), lowered 0.6 mm vs the concept so the bucks clear them
SW_Y, SW_Z = 0.0, 0.0      # KCD1 on the robot's RIGHT flank (x < 0), centred on the dome seam -> same on both faces
SW_X_WALL = -41.0          # outer wall at the flank centre (W / 2)

def body_parts():
    P = {"pcb": [], "chip": [], "cell": [], "chassis": [], "cap": []}
    # cells
    P["cell"] += [("cell_l", cyl(7.1, 50.5, (-7.3, 0.0, CELL_Z), "Y")), ("cell_r", cyl(7.1, 50.5, (7.3, 0.0, CELL_Z), "Y"))]
    P["chassis"].append(("chassis_plate", box(-14.2, 14.2, -34, 30, -1.4, -0.2)))   # printed deck plate, between the hip servos
    # PCA9685 on the deck (62.5 x 25.4); chip on top
    P["pcb"].append(("pca9685", box(-12.7, 12.7, -33.0, 29.0, 7.4, 9.0)))
    P["chip"].append(("pca9685_chip", box(-6, 6, -8, 8, 9.0, 10.8)))
    # perfboard 30 x 60 screwed under the chassis plate; 3 x MP1584 hang under it on header pins
    P["pcb"].append(("perfboard", box(-15.0, 15.0, -30.0, 30.0, -3.05, -1.45)))
    for k, (y0, y1) in enumerate(((-27.0, -10.0), (-8.5, 8.5), (10.0, 27.0))):
        P["pcb"].append((f"mp1584_{k}", box(-11.0, 11.0, y0, y1, -4.25, -3.25)))
        yc = (y0 + y1) / 2
        P["chip"].append((f"mp1584_{k}_parts", box(-7.0, 7.0, yc - 6.0, yc + 6.0, -6.55, -4.25)))   # inductor + caps, 3.0 incl. PCB gap
    # deck (on the chassis plate, z -0.2 .. 7.4 under the PCA9685)
    P["pcb"].append(("gy521", box(-8.0, 8.0, -31.5, -10.5, 0.3, 1.9)))
    P["chip"].append(("gy521_mpu", box(-2.0, 2.0, -23.0, -19.0, 1.9, 2.8)))
    P["pcb"].append(("bms_2s", box(-15.0, 15.0, -8.8, -1.8, 0.3, 1.3)))
    P["chip"].append(("bms_fets", box(-8.0, 8.0, -7.5, -3.0, 1.3, 2.4)))
    # upper deck: printed bracket on 4 standoffs over the PCA9685 (internal_chassis)
    P["chassis"].append(("upper_deck", box(-10.0, 10.0, -21.0, 21.0, 11.2, 12.4) + box(10.0, 36.0, -12.0, 12.0, 11.2, 12.4)))
    # 2S USB-C charger 39 x 18 x 6.3 on top of the upper deck
    P["pcb"].append(("charger_2s", box(-9.0, 9.0, -19.5, 19.5, 12.4, 13.4)))
    P["chip"].append(("charger_parts", box(-7.0, 7.0, -14.0, 13.0, 13.4, 18.7)))
    P["chip"].append(("charger_usbc", box(-4.5, 4.5, 15.0, 19.5, 13.4, 16.7)))
    # PAM8403 + pot hung upside-down under the upper deck, pot reaching down past the PCA9685 edge
    P["pcb"].append(("pam8403", box(12.0, 36.0, -10.5, 10.5, 9.6, 11.2)))
    P["chip"].append(("pam8403_chip", box(30.5, 35.0, -4.0, 4.0, 8.6, 9.6)))
    P["chip"].append(("pam8403_pot", box(18.5, 29.5, -5.0, 5.0, 4.6, 9.6) + cyl(3.0, 7.0, (24.0, 0.0, 1.1))))
    # USB-C breakout at the tail, stalk mount
    P["pcb"].append(("usbc_breakout", box(-5.5, 5.5, 35.0, 39.8, -2.5, -1.7)))
    P["pcb"].append(("stalk_mount", box(-10.0, 10.0, -39.5, -34.5, -6.0, 6.0)))
    # bulk caps (one per servo bank) standing in the left flank pocket under the PAM8403, 470 uF lying below them
    P["cap"] += [("cap1000_a", cyl(4.0, 12.0, (33.5, -4.3, -0.5))), ("cap1000_b", cyl(4.0, 12.0, (33.5, 4.3, -0.5))),
                 ("cap470", cyl(3.15, 11.0, (32.4, 0.0, -10.0), "Y"))]
    # KCD1 rocker: body and tabs inside the right flank (bezel/rocker are visible parts, see switch_visible)
    xb = SW_X_WALL + 1.8                          # inner face of the wall
    P["chip"].append(("kcd1_body", box(xb, xb + 10.5, SW_Y - 6.25, SW_Y + 6.25, SW_Z - 9.5, SW_Z + 9.5)))
    P["chip"].append(("kcd1_tabs", box(xb + 10.5, xb + 17.5, SW_Y - 0.4, SW_Y + 0.4, SW_Z - 6.5, SW_Z + 6.5)))
    for sg in (-1, 1):                              # cliff ToF boards, one per dome
        for nm, sld in tof_board(sg):
            P["pcb" if nm == "gy53_pcb" else "chip"].append((f"{nm}_{'bot' if sg < 0 else 'top'}", sld))
    return P

def switch_cutter():
    """panel cut-out 13 (y) x 19 (z) through the flank wall, half in each dome and through the black band"""
    c = rbox(14.0, 13.0, 19.0, 0.6)       # w along x (through the wall), l along y, h along z
    return c.translate((SW_X_WALL + 1.0, SW_Y, SW_Z))

def switch_visible():
    """bezel 21 x 15 x 1.5 on the outside of the wall + rocker paddle, rocked to ON"""
    bz = rbox(1.5, 15.0, 21.0, 1.2).translate((SW_X_WALL - 0.75, SW_Y, SW_Z))
    bz = bz - box(SW_X_WALL - 2.0, SW_X_WALL + 1.0, SW_Y - 5.6, SW_Y + 5.6, SW_Z - 8.4, SW_Z + 8.4)
    rocker = box(-1.1, 1.1, -5.3, 5.3, -8.1, 8.1)
    rocker = rocker.rotate(Axis.Y, 0).rotate(Axis.Y, 7.0)                    # tilted paddle
    rocker = rocker.translate((SW_X_WALL - 0.4, SW_Y, SW_Z))
    rocker = rocker & box(SW_X_WALL - 3.0, SW_X_WALL + 1.5, -6, 6, -9, 9)
    return [bz, rocker]

# ----------------------------------------------------------------- cliff ToF (moved from the chin to the body, review fix)
# A 25 x 15.6 GY-53 board does not fit behind the chin slot: the best of ~400 placements still cut 58 mm3 into the
# head shell (src/fit_report.json). It fits in the front of each dome, under / over the neck stalk. Both domes stay
# the same STL: the dome that is DOWN carries the active sensor, so face A and face B each have edge sensing.
TOF_ZW, TOF_AIM, TOF_D, TOF_S = 15.0, 50.0, 3.5, 3.3      # window height, aim below horizontal, sensor depth, board offset

def _surf_y(z):
    q = max(0.0, (abs(z) - 4) / 20)
    return -(42 - 26 * (1 - math.sqrt(max(0.0, 1 - q * q))))

def _place(solid, sign):
    """local frame: x = 25 mm side, -y = outward aim, z = 15.6 mm side. sign -1 = bottom dome (face A), +1 = top dome."""
    return solid.rotate(Axis.X, -sign * TOF_AIM).translate((0, _surf_y(TOF_ZW), sign * TOF_ZW))

def tof_board(sign):
    s = TOF_S * sign
    pcb = box(-12.5, 12.5, 0.0, 1.6, -7.8 + s, 7.8 + s).translate((0, TOF_D, 0))
    sensor = box(-2.2, 2.2, -1.0, 0.0, -1.2, 1.2).translate((0, TOF_D, 0))
    stm = box(-2.5, 2.5, 1.6, 2.6, -2.5 + s, 2.5 + s).translate((0, TOF_D, 0))
    return [("gy53_pcb", _place(pcb, sign)), ("gy53_sensor", _place(sensor, sign)), ("gy53_stm32", _place(stm, sign))]

def tof_cutter(sign):
    return _place(box(-4.7, 4.7, -6.0, TOF_D - 0.9, -3.2, 3.2), sign)

def tof_liner(sign):
    """black PLA light tunnel: 0.7 mm walls around an 8 x 5 mm aperture, from the shell surface to the sensor"""
    outer = box(-4.7, 4.7, -0.6, TOF_D - 1.0, -3.2, 3.2)
    inner = box(-4.0, 4.0, -7.0, TOF_D + 1.0, -2.5, 2.5)
    return _place(outer - inner, sign)

def tof_ray(sign):
    """(origin, direction) of the sensor axis in the body mid-plane frame"""
    a = math.radians(TOF_AIM)
    y0, z0 = _surf_y(TOF_ZW), sign * TOF_ZW
    # local origin (0, TOF_D-1, 0) rotated by -sign*aim about X
    ang = math.radians(-sign * TOF_AIM); yl = TOF_D - 1.0
    o = (0.0, y0 + yl * math.cos(ang), z0 + yl * math.sin(ang))
    d = (0.0, -math.cos(a), sign * math.sin(a))
    return o, d

# ----------------------------------------------------------------- head (head frame)
def head_wires():
    """6-core neck flex (jumper-ribbon wires), rerouted around the neck servo: it leaves the stalk end beside the servo
    tab (x -3..-8, clear of the tab at x -0.6..1.9), follows the rear wall at R 18.6 (the servo body sweeps R <= 17.9
    over +-40 deg of pitch, the stalk plate starts at R 21.7) and climbs to the SuperMini pins under the crown."""
    import numpy as np, trimesh
    out = []
    for k in range(6):
        x = -3.1 - 0.9 * k
        pts = [(x, 21.0, 0.0)]
        for i in range(0, 13):
            a = math.radians(78.0 * i / 12)
            pts.append((x, 18.6 * math.cos(a), 18.6 * math.sin(a)))
        pts += [(x, 2.0, 19.9)]
        P = np.array(pts, float); segs = []
        for a_, b_ in zip(P[:-1], P[1:]):
            segs.append(trimesh.creation.cylinder(radius=0.45, segment=[a_, b_], sections=6))
            segs.append(trimesh.creation.icosphere(subdivisions=1, radius=0.45).apply_translation(b_))
        out.append((f"neck_flex_{k}", trimesh.util.concatenate(segs)))
    return out

LCD_Y0 = -12.4

def head_parts():
    """head internals: GC9A01 PCB + FPC tab, ESP32-S3 SuperMini (module can, USB-C), neck flex. The chin slot no longer
    holds a sensor (see cliff ToF above); it stays as the black 'mouth' insert."""
    out = [("gc9a01_pcb", cyl(19.25, 1.6, (0, LCD_Y0 + 1.8 + 0.8, 0), "Y") + box(19.0, 25.8, LCD_Y0 + 1.8, LCD_Y0 + 3.4, -6, 6)),
           ("esp32s3_supermini", box(-11.25, 11.25, -9.0, 9.0, 20.6, 21.8)),
           ("esp32_can", box(-9, 9, -6, 6, 21.8, 23.2)),
           ("esp32_usbc", box(-4.5, 4.5, -9.5, -6.5, 21.8, 24.0))]
    return out + head_wires()
