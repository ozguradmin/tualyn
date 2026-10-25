#!/usr/bin/env python3
"""Fit + mass checks for Yumurcak: runs model.py (stand pose) in-process, then
 - pairwise interference volumes between internal parts and shells
 - head-sweep clearance (head rotated -60..+60 deg about the oblique axis)
 - mass table and centre of mass (body frame and world frame)
Writes check.json and exports local paw STL for the righting analysis."""
import sys, json, math, os
sys.argv = ["model.py", "stand", "stl_stand"]
ns = {}
exec(open("model.py").read(), ns)
from build123d import *
g = ns
res = {"interference_mm3": {}, "sweep": {}}

def iv(a, b):
    try:
        v = (a & b).volume
    except Exception:
        v = -1
    return round(v, 2)

legs = g["legs"]
tur_wall = [Pos(x, y, 0) * (g["TUR"] - g["TUR_IN"]) for (x, y) in g["YAW"]]
body = g["body_shell"]; head = g["head_shell"]
cells = g["union"](g["cells"])
yserv = [l["yservo"] for l in legs]; kserv = [l["kservo"] for l in legs]
pairs = {}
for i, n in enumerate(g["NAMES"]):
    pairs[f"knee_servo_{n} vs haunch wall"] = (kserv[i], tur_wall[i])
    pairs[f"yaw_servo_{n} vs body shell"] = (yserv[i], body)
    pairs[f"yaw_servo_{n} vs cells"] = (yserv[i], cells)
    pairs[f"haunch_{n} vs cells"] = (Pos(g["YAW"][i][0], g["YAW"][i][1], 0) * g["TUR"], cells)
    pairs[f"yaw_servo_{n} vs deck"] = (yserv[i], g["deck"])
    pairs[f"foot_{n} vs body shell"] = (legs[i]["foot"], body)
for i in range(4):
    for j in range(i + 1, 4):
        pairs[f"yaw_servo_{g['NAMES'][i]} vs yaw_servo_{g['NAMES'][j]}"] = (yserv[i], yserv[j])
pairs["cells vs body shell"] = (cells, body)
pairs["elec vs body shell"] = (g["mcu"] + g["bucks"] + g["charger"], body)
pairs["elec vs yaw servos"] = (g["mcu"] + g["bucks"] + g["charger"] + g["bms"] + g["imu"], g["union"](yserv))
pairs["bms/imu vs cells"] = (g["bms"] + g["imu"], cells)
pairs["head servo vs head shell"] = (g["head_servo"], head)
pairs["head servo vs yaw servos"] = (g["head_servo"], g["union"](yserv))
pairs["head servo vs cells"] = (g["head_servo"], cells)
pairs["displays vs head shell+visor"] = (g["union"](g["disp"]), head + g["visor"])
for k, (a, b) in pairs.items():
    res["interference_mm3"][k] = iv(a, b)

# head sweep: displays + head servo + head shell vs fixed internals
fixed = g["union"](yserv) + cells + g["mcu"] + g["bucks"] + g["sled"] + g["post_head"]
AX = g["HEAD_AX"]
for ang in (-60, -30, 0, 30, 60):
    d_ = g["union"](g["disp"]).rotate(AX, ang)
    hsv = g["head_servo"].rotate(AX, ang)
    hs = g["head_shell"].rotate(AX, ang)
    res["sweep"][str(ang)] = dict(displays=iv(d_, fixed), head_servo=iv(hsv, fixed),
                                  head_servo_vs_post=iv(hsv, g["post_head"]), head_shell=iv(hs, fixed))

# ---------------- mass table
PLA, PETG = 1.24e-3, 1.27e-3
def vol(s): return s.volume
items = []
def add(name, mass, solid=None, pos=None):
    if pos is None:
        c = solid.center(); pos = (c.X, c.Y, c.Z)
    items.append(dict(name=name, g=round(mass, 1), x=round(pos[0], 1), y=round(pos[1], 1), z=round(pos[2], 1)))
add("body shell (PLA, 1.6 wall)", vol(body) * PLA, body)
add("head shell (PLA)", vol(head) * PLA, head)
add("visor (PETG, smoked)", vol(g["visor"]) * PETG, g["visor"])
add("eggshell cap (PLA)", vol(g["cap"]) * PLA, g["cap"])
for i, n in enumerate(g["NAMES"]):
    tw = tur_wall[i]
    add(f"haunch {n} (PLA shell)", vol(tw) * PLA, tw)
    f = legs[i]["foot"]
    add(f"paw {n} (PLA, 3 walls + 15% gyroid, TPU sole)", vol(f) * PLA * 0.38 + vol(legs[i]["sole"]) * 1.2e-3, f)
    add(f"yaw MG90S {n}", 13.4, legs[i]["yservo"])
    add(f"knee MG90S {n}", 13.4, legs[i]["kservo"])
    add(f"horns+screws {n}", 2.4, legs[i]["yhorn"])
add("head SG90", 9.0, g["head_servo"])
add("2 x 14500 Li-ion (IMR)", 41.0, cells)
add("deck/collars/posts/sled (PLA)", vol(g["deck"] + g["collars"] + g["posts"] + g["post_head"] + g["sled"]) * PLA * 0.5, g["deck"])
add("2 x GC9A01 round LCD modules", 12.0, g["union"](g["disp"]))
add("ESP32-S3-Zero", 3.0, g["mcu"])
add("3 x MP1584 buck", 6.0, g["bucks"])
add("2S Type-C charger + 2S BMS", 6.0, g["charger"])
add("BMI160 IMU + VL53L0X ToF", 3.0, g["imu"])
add("wiring, caps (2x1000uF), connectors", 16.0, pos=(0, 5, -5))
add("M2 screws, inserts, PTFE tape, magnets", 8.0, pos=(0, 0, -10))
tot = sum(i["g"] for i in items)
com = [sum(i["g"] * i[k] for i in items) / tot for k in "xyz"]
res["mass"] = dict(items=items, total_g=round(tot, 1), com_body=[round(c, 2) for c in com],
                   com_world_z=round(com[2] + g["CZ"], 2), CZ=round(g["CZ"], 2))
json.dump(res, open("check.json", "w"), indent=1)
# local paw + sole STLs for the righting analysis
export_stl(g["FOOT"] + g["SOLE"], "stl_stand/_paw_local.stl", tolerance=0.05, angular_tolerance=0.1)
print(json.dumps({k: v for k, v in res.items() if k != "mass"}, indent=1))
print("mass", res["mass"]["total_g"], "com", res["mass"]["com_body"], "world z", res["mass"]["com_world_z"])
