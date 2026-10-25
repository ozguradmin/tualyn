#!/usr/bin/env python3
"""Concept B 'Tarcin' - torque, power, battery and BOM numbers (writes calc.json and prints a summary).
Geometry and mass come from model.py (stl/checks.json); the MuJoCo results from sim/out/verify_*.json."""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
chk = json.load(open(os.path.join(HERE, "stl", "checks.json")))
M = chk["checks"]["mass_total_g"] / 1000.0          # kg, CAD mass budget
G = 9.81
L1, L2 = 0.040, 0.034
TAU_STALL = {"MG90S @6.0V": 0.216, "MG90S @5.5V (design)": 0.200, "SG90 @4.8V": 0.176}
T_DESIGN = TAU_STALL["MG90S @5.5V (design)"]

out = {"mass_kg": round(M, 3)}


def leg_geom(a_deg, b_deg):
    """horizontal levers (m) from knee and from hip to the paw contact, for thigh angle a and shin angle b"""
    a, b = math.radians(a_deg), math.radians(b_deg)
    knee_y = L1 * math.sin(a)
    foot_y = knee_y + L2 * math.sin(b)
    return abs(foot_y - knee_y), abs(foot_y)


cases = []
# (name, a, b, number of legs sharing the weight, dynamic factor)
for name, a, b, n, k in [
    ("stand (4 legs)", 20, -24, 4, 2.0),
    ("trot (2 diagonal legs)", 20, -24, 2, 2.0),
    ("crawl / paw-wave (3 legs, worst leg carries 1/2)", 20, -24, 2, 2.0),
    ("deep crouch trot (a=40)", 40, -math.degrees(math.asin(L1 * math.sin(math.radians(40)) / L2)), 2, 2.0),
    ("stride end, foot 20 mm ahead of hip (trot)", 5, -40, 2, 2.0),
]:
    lk, lh = leg_geom(a, b)
    F = M * G / n
    tk, th = F * lk, F * lh
    cases.append(dict(case=name, a=round(a, 1), b=round(b, 1), knee_lever_mm=round(lk * 1000, 1), hip_lever_mm=round(lh * 1000, 1),
                      knee_static_Nm=round(tk, 4), hip_static_Nm=round(th, 4),
                      knee_peak_pct=round(100 * tk * k / T_DESIGN, 1), hip_peak_pct=round(100 * th * k / T_DESIGN, 1)))
out["leg_torque_cases"] = cases
worst = max(cases, key=lambda c: max(c["knee_peak_pct"], c["hip_peak_pct"]))
out["worst_joint"] = worst

# getting up from the belly: 4 legs push, foot ~22 mm out from the knee, knee carries m*g/4
lk = 0.022
t_up = M * G / 4 * lk
out["stand_up_from_belly"] = dict(knee_static_Nm=round(t_up, 4), pct_x2=round(100 * 2 * t_up / T_DESIGN, 1))

# tail lever (self-righting): tail tip ~75 mm from its axis; pushing the floor to roll the body.
r_tail = 0.075
out["tail_lever"] = dict(tip_force_at_stall_N=round(T_DESIGN / r_tail, 2), robot_weight_N=round(M * G, 2),
                         note="MuJoCo run uses the 0.2 N*m limit; the recovery saturates it for <0.5 s per attempt")

# head pan (4 g micro servo, 0.08 N*m): inertia of the head about the pan axis
m_head, r_g = 0.072, 0.030
alpha = math.radians(300) / 0.1
out["head_pan"] = dict(inertia_kgm2=round(m_head * r_g ** 2, 7), torque_for_300dps_in_0p1s_Nm=round(m_head * r_g ** 2 * alpha, 4),
                       pct_of_0p08=round(100 * m_head * r_g ** 2 * alpha / 0.08, 1))

# power
servo_walk_avg_A = 0.18 * 8 + 0.05 * 2
servo_peak_A = 0.9 * 5 + 0.25 * 5             # recovery: ~5 servos near stall at 5.5 V, others moving
logic_A_5V = (2 * 0.12 + 2 * 0.06 + 0.05) * 3.3 / 5.0 / 0.9 + 0.08    # 2 S3 (Wi-Fi bursts avg), 2 LCD backlights, sensors, audio avg
P_walk = 5.5 * servo_walk_avg_A / 0.9 + 5.0 * logic_A_5V / 0.9
P_idle = 5.5 * 0.10 / 0.9 + 5.0 * logic_A_5V / 0.9
E_Wh = 2 * 3.6 * 1.0 * 0.85                    # 2S 14500 ~1000 mAh real cells, 85 % usable
out["power"] = dict(servo_walk_avg_A=round(servo_walk_avg_A, 2), servo_peak_A=round(servo_peak_A, 2),
                    logic_avg_A_at_5V=round(logic_A_5V, 2), P_walk_W=round(P_walk, 2), P_idle_W=round(P_idle, 2),
                    battery_Wh=round(E_Wh, 2), walk_minutes=round(60 * E_Wh / P_walk), idle_talk_minutes=round(60 * E_Wh / P_idle))

# BOM (TL, KDV incl.) - verified shop prices from research/parts.md and the guide; (est.) marked
bom = [
    ("MG90S servo (8 legs + 1 tail + 1 spare)", 10, 125.80, "Robotistan, 518 stk"),
    ("4 g digital micro servo, head pan (E-Sky 002279)", 1, 303.00, "Motorobit, 794 stk"),
    ("GC9A01 1.28in round IPS 240x240 (eyes)", 2, 351.50, "Robotistan, 19 stk"),
    ("ESP32-S3 Super Mini 4MB/2MB PSRAM (head + body MCU)", 2, 472.68, "Motorobit, 186 stk"),
    ("BMI160 6-DoF IMU", 1, 127.86, "Direnc, 379 stk"),
    ("VL53L0X ToF (cliff sensor)", 1, 423.35, "Robotistan, 41 stk"),
    ("TTP223B touch module (head pat)", 1, 17.86, "Robo90"),
    ("PAM8403 amp + 8 ohm 1 W 32 mm speaker", 1, 26.78 + 51.51, "Robo90 + Motorobit"),
    ("WS2812B LED (cheek blush)", 2, 6.00, "Robolink"),
    ("14500 Li-ion cell (2S)", 2, 105.48, "guide price - check IMR / >=4 A rating"),
    ("2S BMS (>=5 A)", 1, 53.93, "Motorobit 2S 3A listed; pick a 5 A part if stocked"),
    ("2S 8.4 V 4 A USB-C charger", 1, 78.00, "Robolink, 18 stk"),
    ("MP1584 buck (2x servo 5.5 V, 1x logic 5.0 V)", 3, 53.22, "Robotistan, 187 stk"),
    ("Caps 2x1000 uF + 470 uF, SS14, wires, JST, M2 screws, 6x2 magnets (est.)", 1, 220.00, "est."),
    ("2 mm smoked acrylic, 2x d32 laser cut (est.)", 1, 60.00, "est."),
]
rows = [dict(item=i, qty=q, unit_TL=u, total_TL=round(q * u, 2), source=s) for i, q, u, s in bom]
parts_total = round(sum(r["total_TL"] for r in rows), 2)
out["bom"] = rows
out["bom_parts_TL"] = parts_total
out["all_in_TL_range"] = [round(parts_total + 450 + 150), round(parts_total + 900 + 150)]
out["savings_options"] = [
    ("drop spare MG90S", 125.80), ("one ESP32-S3 N16R8 devkit in the head instead of 2 Super Minis (+12-wire neck loom)", 2 * 472.68 - 610.23),
    ("skip VL53L0X (edge detection off)", 423.35)]

json.dump(out, open(os.path.join(HERE, "calc.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: out[k] for k in ("mass_kg", "worst_joint", "stand_up_from_belly", "tail_lever", "head_pan", "power", "bom_parts_TL", "all_in_TL_range")}, indent=1))
for c in cases:
    print(c)
