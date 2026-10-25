#!/usr/bin/env python3
"""Findik: worst-case actuator torques, power budget and BOM/cost, from the model's info.json.
usage: python3 calc.py stl/info.json  -> prints a report, writes calc.json"""
import json, math, sys

info = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "stl/info.json"))
m = info["mass_g"] / 1000.0
g = 9.81
W = m * g
L = 0.034          # hip -> axle
R_W = 0.015        # wheel radius
HIP_H = 0.032      # hip height above belly (body frame)
STAND_DEG = info["legs_deg"]["fl"]
STAND = math.radians(STAND_DEG)
com_y = info["com_world"][1] / 1000.0
yf, yr = info["wheel_contacts_world"]["fl"][1] / 1000.0, info["wheel_contacts_world"]["rl"][1] / 1000.0
track = 2 * abs(info["wheel_contacts_world"]["fl"][0]) / 1000.0

# servo: MG90S stall torque ~0.177 N*m @4.8 V, ~0.216 @6 V -> servo rail 5.6 V (MP1584) ~0.20 N*m
T_SERVO = 0.20
T_N20 = 0.10       # N20 6 V 100 rpm (~150:1) stall, conservative (vendor tables 1.0-1.6 kg*cm)
cases = []
def hip(name, load_frac, lever, dyn):
    t = W * load_frac * lever
    cases.append(dict(case=name, static_Nm=round(t, 4), dynamic_Nm=round(t * dyn, 4),
                      pct_stall_static=round(100 * t / T_SERVO, 1), pct_stall_dynamic=round(100 * t * dyn / T_SERVO, 1)))

hip(f"stand, 4 wheels, legs {STAND_DEG:.0f} deg", 0.25, L * math.sin(STAND), 2.0)
hip("paw wave on 3 wheels (diagonal leg takes 1/2 W)", 0.5, L * math.sin(STAND), 2.0)
a_td = math.acos((HIP_H - R_W) / L)       # leg angle when a wheel first touches while the belly sits on the desk
hip("stand-up from belly, wheel touchdown, 4 legs share", 0.25, L * math.sin(a_td), 1.5)
hip("stand-up from belly, only 2 legs share (worst)", 0.5, L * math.sin(a_td), 1.5)
hip("leg sweep while lying on side (friction mu=0.5, half weight)", 0.5 * 0.5, L, 1.5)
hip("step-up: front paw on a 15 mm book, rear pair pushes", 0.5, L * math.sin(math.radians(35)), 2.0)

# wheels (2 driven rear wheels)
wheel = []
def wh(name, F_per_wheel):
    t = F_per_wheel * R_W
    wheel.append(dict(case=name, per_wheel_Nm=round(t, 4), pct_stall=round(100 * t / T_N20, 1)))
wh("accelerate 1 m/s^2", m * 1.0 / 2)
wh("climb 15 deg ramp", W * math.sin(math.radians(15)) / 2)
front_frac = (yr - com_y) / (yr - yf)
N_front = W * front_frac
M_scrub = 0.8 * N_front * (yr - yf)                 # front wheels slide sideways when pivoting about the rear axle
wh("spin in place (front wheels skid, mu 0.8)", M_scrub / track)
wh("spin in place leaning back (front load -50 %)", 0.5 * M_scrub / track)
speed = 100 / 60 * math.pi * 2 * R_W

# tipping angles in the stand pose
h_com = info["com_world"][2] / 1000.0
tip_side = math.degrees(math.atan((track / 2) / h_com))
tip_front = math.degrees(math.atan((com_y - yf) / h_com))
tip_back = math.degrees(math.atan((yr - com_y) / h_com))

# power
pack_Wh = 2 * 3.7 * 0.9
loads = {
    "idle_sitting(servos off, wifi+2 screens 50%)": 0.55 + 0.17 + 0.05,
    "idle_standing(servos holding)": 0.55 + 0.17 + 0.05 + 4 * 0.015 * 5.6,
    "rolling + expressive motion": 0.7 + 0.17 + 2 * 0.15 * 7.4 + 4 * 0.08 * 5.6,
}
eff = 0.85
runtime = {k: round(pack_Wh * 0.9 / (v / eff), 2) for k, v in loads.items()}
peak_A = (4 * 0.45 * 5.6 / eff + 2.2 / eff) / 7.2            # stand-up: 4 servos at ~40 % stall + logic/Wi-Fi burst
peak_drive_A = (2 * 0.35 * 7.4 + 4 * 0.2 * 5.6 / eff + 2.2 / eff) / 7.2   # spinning in place + posture + logic
worst_A = (4 * 0.75 * 5.6 / eff + 2 * 0.6 * 7.4 + 2.2 / eff) / 7.2     # everything stalled at once (fault case)

BOM = [  # part, qty, unit TL, shop, verified-in-stock?
    ("MG90S 180 deg metal-gear servo (4 hips + 1 spare)", 5, 125.80, "Robotistan", "V"),
    ("N20 6 V 100 rpm gearmotor (rear paws)", 2, 178.56, "Robo90", "S, q=28"),
    ("DRV8833 2-ch motor driver", 1, 75.75, "Motorobit", "S, q=14"),
    ("ESP32-S3 N16R8 devkit (Wi-Fi, 8 MB PSRAM)", 1, 610.23, "Direnc", "S, q=1073"),
    ("GC9A01 1.28in 240x240 round IPS (eyes)", 2, 351.50, "Robotistan", "V, q=19"),
    ("BMI160 6-DOF IMU", 1, 127.86, "Direnc", "V, q=379"),
    ("TCRT5000 IR reflectance module (cliff)", 2, 52.31, "Direnc", "S, q=111"),
    ("TTP223B touch module (head pat, back)", 2, 17.86, "Robo90", "S, q=1310"),
    ("WS2812B LED (cheek blush)", 2, 6.00, "Robolink", "S, q=2351"),
    ("INMP441 I2S microphone", 1, 145.29, "Direnc", "S, q=602"),
    ("MAX98357A I2S amp (Amazon.com.tr, not re-verified; Adafruit fallback 740.38)", 1, 309.00, "Amazon.com.tr", "brief"),
    ("Speaker 8 ohm 1 W 32 mm", 1, 51.51, "Motorobit", "S, q=4900"),
    ("Orion 14500 3.7 V 900 mAh 3C Li-ion", 2, 105.48, "Direnc", "S"),
    ("2S 7.4 V 4.5 A BMS", 1, 66.66, "Motorobit", "S, q=172"),
    ("2S 8.4 V 4 A Type-C charger", 1, 78.00, "Robolink", "S, q=18"),
    ("MP1584 3 A buck (servo 5.6 V, logic 5.0 V)", 2, 53.22, "Robotistan", "S, q=187"),
]
EST = [
    ("misc: slide switch, 1000 uF + 470 uF caps, SS14, JST/wire, M2/M3 screws + heat-set inserts, 4 x 6x2 magnets, 2 x M3 axle screws, PTFE grease", 250.0),
]
PRINT = ("3D print at a studio: cream + caramel matte PLA (~150 g), black PETG visor (ironed/glossy), TPU tyres", 750.0)
SHIP = ("shipping, 5 shops (some free over threshold)", 300.0)
parts_total = sum(q * u for _, q, u, _, _ in BOM) + sum(v for _, v in EST)
total = parts_total + PRINT[1] + SHIP[1]
no_audio = total - (145.29 + 309.00 + 51.51)
no_spare = total - 125.80

rep = dict(mass_g=info["mass_g"], hip_cases=cases, wheel_cases=wheel, speed_m_s=round(speed, 3),
           tip_angles_deg=dict(side=round(tip_side, 1), forward=round(tip_front, 1), backward=round(tip_back, 1)),
           wheelbase_mm=round((yr - yf) * 1000, 1), track_mm=round(track * 1000, 1), front_load_frac=round(front_frac, 2),
           pack_Wh=pack_Wh, loads_W=loads, runtime_h=runtime, peak_battery_A_standup=round(peak_A, 2),
           peak_battery_A_driving=round(peak_drive_A, 2), worst_case_all_stalled_A=round(worst_A, 2),
           bom=[dict(part=p, qty=q, unit_tl=u, line_tl=round(q * u, 2), shop=s, stock=v) for p, q, u, s, v in BOM],
           estimates=[dict(item=a, tl=b) for a, b in EST + [PRINT, SHIP]],
           parts_total_tl=round(parts_total, 2), total_tl=round(total, 2), total_without_audio_tl=round(no_audio, 2),
           total_without_spare_servo_tl=round(no_spare, 2))
json.dump(rep, open("calc.json", "w"), indent=1)
for c in cases:
    print(f"HIP  {c['case']:58s} {c['static_Nm']*1000:6.1f} mN*m  x dyn {c['dynamic_Nm']*1000:6.1f}  -> {c['pct_stall_dynamic']:5.1f} % of MG90S")
for c in wheel:
    print(f"N20  {c['case']:58s} {c['per_wheel_Nm']*1000:6.1f} mN*m -> {c['pct_stall']:5.1f} % of stall")
print("speed", rep["speed_m_s"], "m/s   tip", rep["tip_angles_deg"], " wheelbase", rep["wheelbase_mm"], "track", rep["track_mm"])
print("runtime h", runtime, " peak A stand-up", rep["peak_battery_A_standup"], "driving", rep["peak_battery_A_driving"], "all-stalled", rep["worst_case_all_stalled_A"])
print("parts", rep["parts_total_tl"], " total", rep["total_tl"], " no audio", rep["total_without_audio_tl"])
