#!/usr/bin/env python3
"""Mass, centre of mass, support margins and servo torque check for concept A (Tosbi).
Reads out/stand/parts/*.stl (+ parts.json) written by model.py. Prints a report and writes calc.json."""
import json, math, os, glob
import numpy as np, trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "out", "stand")
info = json.load(open(os.path.join(D, "parts.json")))
P = info["parts"]
HM = info["HM"]
g = 9.81

def cen(name):
    m = trimesh.load(os.path.join(D, "parts", name + ".stl"))
    return np.array(m.bounds.mean(axis=0) if not m.is_volume else m.center_mass)

PLA, TPU, PETG = 1.24, 1.21, 1.27
def shell_mass(name, wall=0.16, infill=0.12, minus=0.0, rho=PLA):
    """solid-modelled printed part -> walls (A*t) + sparse infill of the rest (cm units)."""
    V, A = P[name]["volume_cm3"], P[name]["area_cm2"]
    w = A * wall
    return rho * (w + infill * max(0.0, V - w - minus))

parts = []          # (name, mass_g, centroid_mm)
def add(name, m, c):
    parts.append((name, float(m), np.asarray(c, float)))

# printed parts ---------------------------------------------------------------
for n in ("shell_top", "shell_bot", "badge_top", "badge_bot", "tail", "lip"):
    add(n, PLA * P[n]["volume_cm3"], cen(n))
# legs: 1.2 mm walls (3 x 0.4 perimeters, no LEDs inside) + ribs/bosses; head 1.4 mm; body domes as modelled (1.8)
for i in range(4):
    add(f"egg{i}", shell_mass(f"egg{i}", 0.12, 0.08), cen(f"egg{i}"))
    add(f"arm{i}", shell_mass(f"arm{i}", 0.12, 0.08, minus=7.0), cen(f"arm{i}"))
    add(f"foot{i}", shell_mass(f"foot{i}", 0.12, 0.12), cen(f"foot{i}"))
    add(f"toe{i}", TPU * P[f"toe{i}"]["volume_cm3"] * 0.7, cen(f"toe{i}"))       # TPU 70 % infill
add("head_shell", shell_mass("head_skin0", 0.14, 0.03), cen("head_skin0"))
add("bezel", PLA * P["head_accent0"]["volume_cm3"], cen("head_accent0"))
add("visor", PETG * P["head_visor0"]["volume_cm3"], cen("head_visor0"))
add("stalk+plate", PLA * (0.6 * P["stalk"]["volume_cm3"] + P["stalk_plate"]["volume_cm3"]), cen("stalk"))
add("chassis (servo cradles, deck, cell holder; est.)", 14.0, (0, 0, HM - 4))
# purchased parts -------------------------------------------------------------
for i in range(4):
    add(f"hip MG90S {i}", 13.4, cen(f"hip_servo{i}"))
    add(f"knee MG90S {i}", 13.4, cen(f"knee_servo{i}"))
add("neck MG90S (fixed on stalk, inside head)", 13.4, cen("neck_servo"))
add("2x 14500 Li-ion", 2 * 20.0, (0, 0, HM - 13.4))
add("PCA9685", 9.0, cen("pca9685"))
add("3x MP1584", 10.5, (0, 0, HM - 3))
add("2S BMS + 2S USB-C charger + USB-C breakout", 9.0, (0, 12, HM + 2))
add("PAM8403 + 29 mm speaker", 7.0, (0, 25, HM))
add("BMI160", 1.0, cen("bmi160"))
add("GC9A01 round LCD module", 7.0, cen("head_pcb0"))
add("ESP32-S3 SuperMini", 2.5, cen("head_pcb1"))
add("VL53L0X ToF", 1.5, cen("head_pcb2"))
add("wiring, caps, M2 screws, bearing pins, copper touch foil", 17.0, (0, -5, HM))

M = sum(m for _, m, _ in parts)
CG = sum(m * c for _, m, c in parts) / M
head_names = ("head_shell", "bezel", "visor", "GC9A01 round LCD module",
              "ESP32-S3 SuperMini", "VL53L0X ToF")
Mh = sum(m for n, m, _ in parts if n in head_names)
CGh = sum(m * c for n, m, c in parts if n in head_names) / Mh

# geometry from model.py parameters -------------------------------------------
LC, LF, BETA = 33.0, 36.0, math.radians(80.0)
HUBS = [(30.7, -25.8), (-30.7, -25.8), (30.7, 25.8), (-30.7, 25.8)]
DIRS = [-35.0, 215.0, 35.0, 145.0]
HEAD_C_Y = -(84 / 2 + 5 + 22)          # neck pivot (servo shaft) = head centre
feet = []
for (hx, hy), d in zip(HUBS, DIRS):
    r = LC + LF * math.cos(BETA)
    feet.append((hx + r * math.cos(math.radians(d)), hy + r * math.sin(math.radians(d))))
feet = np.array(feet)

def margin(tri, p):
    """signed distance of p inside triangle tri (min distance to an edge, >0 inside)."""
    ds = []
    for k in range(3):
        a, b = tri[k], tri[(k + 1) % 3]
        e = b - a
        n = np.array([-e[1], e[0]]) / np.linalg.norm(e)
        c = tri[(k + 2) % 3]
        if np.dot(c - a, n) < 0:
            n = -n
        ds.append(float(np.dot(p - a, n)))
    return min(ds)

cg2 = CG[:2]
crawl = {}
names = ["FL(+x,front)", "FR(-x,front)", "RL(+x,rear)", "RR(-x,rear)"]
for lift in range(4):
    tri = np.array([feet[k] for k in range(4) if k != lift])
    crawl[names[lift]] = round(margin(tri, cg2), 1)

# torque check ----------------------------------------------------------------
STALL = {"MG90S@6V": 0.216, "MG90S@5.5V(est)": 0.20, "MG90S@4.8V": 0.177}
T_ref = 0.20
yf, yr = feet[:, 1].min(), feet[:, 1].max()
front_share = (yr - CG[1]) / (yr - yf)          # share of weight on the front pair (4-leg stance)
W = M / 1000 * g
lever_knee = LF * math.cos(BETA) / 1000
cases = []
def case(name, F, lever, note=""):
    t = F * lever
    cases.append({"case": name, "force_N": round(F, 2), "lever_mm": round(lever * 1000, 1),
                  "static_Nm": round(t, 4), "x2_dyn_Nm": round(2 * t, 4),
                  "pct_stall_5V5": round(100 * 2 * t / T_ref, 1), "note": note})
case("knee, 4-leg stand, front leg", W * front_share / 2, lever_knee)
case("knee, trot (diagonal pair), front leg", W * front_share, lever_knee, "front foot of the pair carries the front share")
case("knee, crouched trot (foot 55 deg)", W * front_share, LF * math.cos(math.radians(55)) / 1000)
case("knee, belly-down push-up / flip transit (foot horizontal), 4 legs", W / 4 * 1.15, LF / 1000, "+15 % uneven")
case("knee, belly-down push-up, only 2 legs touching", W / 2, LF / 1000, "worst realistic")
r_hip = (LC + LF * math.cos(BETA)) / 1000
case("hip yaw, stance scrub mu=0.5 (trot)", 0.5 * W / 2, r_hip, "PLA/TPU on desk; TPU can reach mu~0.8")
case("hip yaw, stance scrub mu=0.8 (TPU, worst)", 0.8 * W / 2, r_hip)
neck_lever = abs(CGh[1] - HEAD_C_Y) / 1000
case("neck pitch, rotating head mass, CoM offset from pivot", Mh / 1000 * g, max(neck_lever, 0.004), "pivot at head centre; servo itself does not rotate")
case("neck pitch, head pushing on desk (self-right assist)", W * 0.5, 0.030, "using the head as a lever, half body weight")

rep = {
    "mass_total_g": round(M, 1), "mass_head_g": round(Mh, 1),
    "CoM_mm": [round(v, 1) for v in CG], "CoM_height_above_ground_mm": round(CG[2], 1),
    "head_CoM_vs_pivot_mm": round(CGh[1] - HEAD_C_Y, 1),
    "feet_xy_mm": feet.round(1).tolist(), "front_weight_share": round(front_share, 3),
    "crawl_margin_mm(lifted leg: CoM distance inside 3-foot triangle, <0 = must shift body)": crawl,
    "torque_cases": cases, "stall_Nm": STALL,
    "parts": [(n, round(m, 1)) for n, m, _ in parts],
}
json.dump(rep, open(os.path.join(HERE, "calc.json"), "w"), indent=1)
print(f"mass total {M:.0f} g (head {Mh:.0f} g); CoM {CG.round(1)} (height {CG[2]:.1f} mm)")
print("feet", feet.round(1).tolist(), "front share", round(front_share, 3))
print("crawl margins", crawl)
for c in cases:
    print(f"  {c['case']:<62} F={c['force_N']:5.2f} N  r={c['lever_mm']:5.1f} mm  2T={c['x2_dyn_Nm']:.3f} Nm  {c['pct_stall_5V5']:5.1f} %")
printed = sum(m for n, m, _ in parts if any(n.startswith(k) for k in ("shell", "badge", "tail", "lip", "egg", "arm", "foot", "toe", "head_shell", "bezel", "visor", "stalk", "chassis")))
print(f"printed parts {printed:.0f} g, bought parts {M - printed:.0f} g")
