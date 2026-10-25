#!/usr/bin/env python3
"""Yumurcak: torque, power and cost numbers (reads check.json for mass/CoM). Writes calc.json."""
import json, math

chk = json.load(open("check.json"))
m = chk["mass"]["total_g"] / 1000.0
W = m * 9.81
STALL = {"MG90S@5.5V": 0.20, "SG90@5.5V": 0.19}

FOOT_L, OFF = 48.0, -4.0         # knee axis -> sole, paw toe offset (mm, toe turned inward)
def lever(beta):                  # horizontal lever of the sole about the knee axis (beta from vertical)
    b = math.radians(beta)
    return FOOT_L * math.sin(b) + OFF * math.cos(b)

rows = []
def add(case, F, lev_mm, servo="MG90S@5.5V"):
    t = F * lev_mm / 1000
    rows.append(dict(case=case, force_N=round(F, 2), lever_mm=round(lev_mm, 1), static_Nm=round(t, 3),
                     dyn_x2_Nm=round(2 * t, 3), pct_static=round(100 * t / STALL[servo], 0),
                     pct_dyn=round(200 * t / STALL[servo], 0), servo=servo))

add("knee, 4-leg stand (beta 30)", W / 4, lever(30))
add("knee, trot 2 legs (beta 30)", W / 2, lever(30))
add("knee, crouched trot (beta 45)", W / 2, lever(45))
add("knee, rise from sitting/nest (beta 90, 4 legs)", W / 4, lever(90))
add("knee, rise from sitting on 2 legs (worst)", W / 2, lever(90))
# yaw: sole scrub about the yaw axis, foot 23 mm in front of the axis and 'lever(30)'+? outward
r_yaw = math.hypot(lever(30) + 0.0, 23.0)
add("hip yaw, foot scrub mu=0.5, trot", 0.5 * W / 2, r_yaw)
add("hip yaw, foot scrub mu=0.8 (TPU), trot", 0.8 * W / 2, r_yaw)
# head: ~57 g head assembly, CoM 10 mm off the 12-deg axis + 60 deg in 0.15 s + PTFE ring friction
mh, rc = 0.057, 0.010
grav = mh * 9.81 * rc * math.sin(math.radians(12))
I = mh * 0.03 ** 2
acc = 2 * math.radians(60) / 0.15 ** 2
head_t = grav + I * acc + 0.010
rows.append(dict(case="head (SG90): gravity + 60deg/0.15s accel + ring friction", static_Nm=round(head_t, 4),
                 pct_static=round(100 * head_t / STALL["SG90@5.5V"]), servo="SG90@5.5V"))

# righting push (from righting.json if present)
try:
    rj = json.load(open("righting.json"))
    tmax = max(v["max_knee_Nm"] for v in rj["manoeuvres"].values())
    rows.append(dict(case="knee, self-righting push (quasi-static model, worst fall)", static_Nm=tmax,
                     dyn_x2_Nm=round(2 * tmax, 3), pct_static=round(100 * tmax / 0.2), pct_dyn=round(200 * tmax / 0.2),
                     servo="MG90S@5.5V"))
except Exception:
    pass

# power
cells_Wh = 2 * 3.6 * 0.80          # 2S 14500 IMR ~800 mAh
walk_W = 5.5 * 1.9 + 1.4           # 8 MG90S walking avg ~1.9 A + ESP32/2 LCDs/Wi-Fi
idle_W = 1.4                       # servos detached, 2 LCD @ 50 % backlight, Wi-Fi bursts
power = dict(pack="2S 14500 IMR (2 x 3.6 V x ~0.8 Ah)", energy_Wh=round(cells_Wh, 1),
             walk_W=round(walk_W, 1), walk_min=round(60 * cells_Wh * 0.85 / walk_W),
             idle_talk_W=idle_W, idle_h=round(cells_Wh * 0.85 / idle_W, 1),
             peak_A_5V5="~4.7 A (9 servos, get-up), split on two MP1584 banks (<=3 A each)")

# cost (TL, KDV incl.)
bom = [
    ("MG90S servo (legs) x8", 8, 125.80, "Robotistan, 518 in stock"),
    ("MG90S spare x1", 1, 125.80, "Robotistan"),
    ("SG90 servo (head) x1", 1, 82.25, "Robotistan"),
    ("ESP32-S3 Mini/Zero board (4 MB/2 MB PSRAM, 23.5x18)", 1, 632.44, "Robot Sepeti code 25517"),
    ("GC9A01 1.28in round IPS 240x240 x2 (eyes)", 2, 351.50, "Robotistan, 19 in stock"),
    ("BMI160 6-DOF IMU", 1, 127.86, "Direnc"),
    ("VL53L0X ToF (cliff, looks forward-down)", 1, 423.35, "Robotistan"),
    ("14500 Li-ion cell (IMR / high-drain) x2", 2, 105.48, "guide price - verify >=4 A rating"),
    ("2S BMS (>=5 A)", 1, 45.24, "guide price"),
    ("2S 8.4 V 4 A USB-C charger", 1, 78.00, "Robolink"),
    ("MP1584 3 A buck x3 (2 servo banks + logic)", 3, 53.22, "Robotistan"),
    ("2x1000 uF low-ESR, SS14, 220 uF, switch (est.)", 1, 55.00, "est."),
    ("Copper tape for 2 touch pads (est.)", 1, 30.00, "est."),
    ("Wire, JST, M2 screws/inserts, PTFE tape, 4 magnets (est.)", 1, 150.00, "est."),
    ("1 mm smoked PETG sheet for the visor (est.)", 1, 100.00, "est."),
]
parts = sum(q * p for _, q, p, _ in bom)
print_tl, ship_tl = 650.0, 250.0
audio = [("INMP441 mic", 1, 145.29), ("MAX98357A amp (guide price)", 1, 309.0), ("8 ohm 1 W 32 mm speaker", 1, 51.51)]
audio_tl = sum(q * p for _, q, p in audio)
res = dict(mass_g=chk["mass"]["total_g"], weight_N=round(W, 2), torque=rows, power=power,
           bom=[dict(item=a, qty=q, unit_tl=p, total_tl=round(q * p, 2), source=s) for a, q, p, s in bom],
           parts_tl=round(parts, 2), print_tl=print_tl, shipping_tl=ship_tl,
           total_tl=round(parts + print_tl + ship_tl, 2),
           audio_option=dict(items=audio, tl=round(audio_tl, 2),
                             total_with_audio_tl=round(parts + print_tl + ship_tl + audio_tl, 2),
                             total_with_audio_and_ir_cliff_tl=round(parts + print_tl + ship_tl + audio_tl - 423.35 + 2 * 25, 2)))
json.dump(res, open("calc.json", "w"), indent=1)
for r in rows:
    print(r)
print(power)
print("parts", res["parts_tl"], "total", res["total_tl"], "with audio", res["audio_option"])
