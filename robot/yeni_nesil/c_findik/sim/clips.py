#!/usr/bin/env python3
"""Generate every animation clip of package C (Findik) in MuJoCo and write ../anim/*.json.

ALL clips are physics results: joint targets go to the simulated MG90S servos (torque-limited), the rear
N20s get PWM commands, and the recorded joint angles + base pose are whatever the simulation produced.
Even the 'expressive' clips (idle, talk, happy, sleep) are simulated, so the body really shifts when the
legs move (the front paws roll freely) and nothing can float or sink.

usage: python3 -I clips.py   -> ../anim/{idle,walk,turn,talk,happy,sleep,fall_recover,fall_back_help}.json
                                results/clips_report.json
"""
import json, math, os, sys
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation as Rot
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sim_lib import Robot, HIPS, WHEELS, smooth, src_line
import fall
from explore_wave_pose import margin as static_margin

ANIM = os.path.join(os.path.dirname(HERE), "anim")
FPS = 30


def yaw_of(b):
    return Rot.from_quat([b[4], b[5], b[6], b[3]]).as_euler("zyx", degrees=True)[0]


class Checker:
    """per-frame physical sanity: worst contact penetration, frames with no floor contact, coupled limit"""
    def __init__(self):
        self.pen = 0.0; self.air = 0; self.coupled = 1.0; self.n = 0; self.pen_geoms = None

    def __call__(self, r):
        self.n += 1
        for c in r.d.contact[: r.d.ncon]:
            if -c.dist * 1000 > self.pen:
                self.pen = -c.dist * 1000
                self.pen_geoms = (r.m.geom(c.geom1).name, r.m.geom(c.geom2).name)
        if not r.lowest_floor_contact_geoms():
            self.air += 1
        for s in ("l", "r"):
            v = math.sin(math.radians(r.q("hip_f" + s))) + math.sin(math.radians(r.q("hip_r" + s)))
            self.coupled = min(self.coupled, v)

    def report(self):
        return {"max_penetration_mm": round(self.pen, 3), "worst_contact": self.pen_geoms, "frames_without_floor_contact": self.air,
                "min_sin_front_plus_sin_rear": round(self.coupled, 3)}


def run_script(script, T, mu=0.6, loop=False, warm=0.0, settle=0.6, probe=None):
    """script(t) -> (targets dict, (u_rl, u_rr)).  Records T s (T*fps+1 frames if loop)."""
    r = Robot(mu_floor=mu)
    r.settle(settle)
    chk = Checker()
    n = int(round(T * FPS)) + (1 if loop else 0)
    t = 0.0
    if warm:
        for i in range(int(round(warm * FPS))):
            tg, u = script((i / FPS) % T)
            r.target.update(tg); r.u["wheel_rl"], r.u["wheel_rr"] = u
            r.step_frame(record=False)
    for i in range(n):
        tg, u = script(i / FPS if not loop else (i / FPS) % T if i < n - 1 else T)
        r.target.update(tg); r.u["wheel_rl"], r.u["wheel_rr"] = u
        chk(r)
        if probe:
            probe(r, i / FPS)
        r.step_frame(record=True)
    # shift so the clip starts at the origin, facing -Y (pure rigid ground-plane shift/rotation)
    b0 = r.frames[0]["base"]
    yaw0 = yaw_of(b0)
    Rz = Rot.from_euler("z", -yaw0, degrees=True)
    for f in r.frames:
        b = f["base"]
        p = Rz.apply([b[0] - b0[0], b[1] - b0[1], b[2]])
        q = (Rz * Rot.from_quat([b[4], b[5], b[6], b[3]])).as_quat()
        f["base"] = [p[0], p[1], b[2], q[3], q[0], q[1], q[2]]
    drift = None
    if loop:
        bN = r.frames[-1]["base"]
        dx, dy = bN[0], bN[1]
        dyaw = yaw_of(bN)
        drift = {"x_mm": round(dx, 3), "y_mm": round(dy, 3), "yaw_deg": round(dyaw, 3)}
        for i, f in enumerate(r.frames):
            a = i / (len(r.frames) - 1)
            b = f["base"]
            Rc = Rot.from_euler("z", -dyaw * a, degrees=True)
            q = (Rc * Rot.from_quat([b[4], b[5], b[6], b[3]])).as_quat()
            f["base"] = [b[0] - dx * a, b[1] - dy * a, b[2], q[3], q[0], q[1], q[2]]
        for j in WHEELS:      # wheels: remove the tiny net roll so frame N == frame 0
            d = r.frames[-1][j] - r.frames[0][j]
            for i, f in enumerate(r.frames):
                f[j] -= d * i / (len(r.frames) - 1)
    return r, chk, drift


def peak_tau(r):
    out = {j: round(v, 3) for j, v in r.peak_tau.items()}
    out["s_at_stall_(>=95%)"] = {j: round(v, 3) for j, v in r.sat_s.items()}
    return out


def write(name, r, face, loop, metrics, extra_src=""):
    path = os.path.join(ANIM, name + ".json")
    r.export(path, face, loop=loop, source=src_line(0.6, extra_src), metrics=metrics)
    print("wrote", path, len(r.frames), "frames", json.dumps(metrics)[:300])


REPORT = {}

# ---------------------------------------------------------------- idle (5 s loop)
def idle_s(t):
    br = 3.0 * math.sin(2 * math.pi * t / 2.5)            # breathing: 2 breaths
    sw = 2.0 * math.sin(2 * math.pi * t / 5.0)            # slow weight shift / head tilt
    return ({"hip_fl": 22 + br + sw, "hip_rl": 22 + br + sw, "hip_fr": 22 + br - sw, "hip_rr": 22 + br - sw}, (0.0, 0.0))
r, chk, drift = run_script(idle_s, 5.0, loop=True, warm=5.0)
face = [[0, "neutral"], [40, "blink"], [44, "neutral"], [96, "curious"], [118, "blink"], [122, "neutral"]]
m = {"physics": chk.report(), "loop_drift_removed": drift, "peak_hip_torque_Nm": peak_tau(r), "rear_wheels": "braked (DRV8833 slow decay)"}
write("idle", r, face, True, m, "; breathing ±3° + sway ±2°, simulated")
REPORT["idle"] = m

# ---------------------------------------------------------------- talk (5 s loop)
def talk_s(t):
    env = 1.0 if (t % 5.0) < 4.8 else 0.0
    nod = 4.0 * math.sin(2 * math.pi * 1.2 * t)           # small nods with the speech rhythm
    tilt = 3.0 * math.sin(2 * math.pi * 0.4 * t)           # head tilt left/right
    return ({"hip_fl": 22 + nod + tilt, "hip_fr": 22 + nod - tilt,
             "hip_rl": 22 - 0.6 * nod + tilt, "hip_rr": 22 - 0.6 * nod - tilt}, (0.0, 0.0))
r, chk, drift = run_script(talk_s, 5.0, loop=True, warm=5.0)
face = []
def syll(a, b, step=6):
    k = 0
    for f in range(a, b, step):
        face.append([f, "talk_a" if k % 2 == 0 else "talk_b"]); k += 1
face.append([0, "neutral"])
syll(4, 50, 6); face.append([50, "neutral"])
syll(62, 110, 5); face.append([110, "neutral"]); face.append([114, "blink"]); face.append([118, "neutral"])
syll(122, 146, 6); face.append([146, "happy"])
face.sort(key=lambda x: x[0])
m = {"physics": chk.report(), "loop_drift_removed": drift, "peak_hip_torque_Nm": peak_tau(r),
     "face_rate_s": "talk_a/talk_b every 0.17-0.20 s, in 3 phrases"}
write("talk", r, face, True, m, "; nods + tilt, simulated")
REPORT["talk"] = m

# ---------------------------------------------------------------- happy (4 s): lean, wave the front-left paw, bounce-wiggle
# lean for the 3-wheel wave: RL >= 5 deg (below that the N20 boot sleeve enters the belly, check_arm_shell.py);
# picked by explore_wave_pose.py (static margin 14.5 mm settled)
LEAN = {"hip_fl": 22.0, "hip_fr": 40.0, "hip_rl": 8.0, "hip_rr": 65.0}
def happy_s(t):
    tg = {}
    if t < 0.6:
        x = t / 0.6
        tg = {j: smooth(22, LEAN[j], x) for j in HIPS}
    elif t < 2.3:
        tg = dict(LEAN)
        if t < 0.95:
            tg["hip_fl"] = smooth(22, 70, (t - 0.6) / 0.35)
        elif t < 2.0:
            tg["hip_fl"] = 70 + 11 * math.sin(2 * math.pi * 2.5 * (t - 0.95))
        else:
            tg["hip_fl"] = smooth(70, 22, (t - 2.0) / 0.3)
    elif t < 2.8:
        tg = {j: smooth(LEAN[j], 22, (t - 2.3) / 0.5) for j in HIPS}
    elif t < 3.75:
        b = 6.0 * math.sin(2 * math.pi * 2.6 * (t - 2.8))
        w = 4.0 * math.sin(2 * math.pi * 1.3 * (t - 2.8))
        tg = {"hip_fl": 22 + b + w, "hip_rl": 22 + b + w, "hip_fr": 22 + b - w, "hip_rr": 22 + b - w}
    else:
        tg = {j: 22.0 for j in HIPS}
    u = (0.0, 0.0)
    if 2.8 <= t < 3.75:
        s = 0.45 if math.sin(2 * math.pi * 2.6 * (t - 2.8)) > 0 else -0.45     # wheel jiggle (wiggle in place)
        u = (s, -s)
    return tg, u
WM = []
def wave_probe(r, t):
    if 1.0 <= t < 2.0:                    # paw up and waving: CoM must stay inside the 3-tyre support triangle
        WM.append((static_margin(r)[0], sorted(r.lowest_floor_contact_geoms())))
r, chk, drift = run_script(happy_s, 4.0, probe=wave_probe)
wave_margin = {"min_mm": round(min(w[0] for w in WM), 1), "median_mm": round(float(np.median([w[0] for w in WM])), 1),
               "frames_tyre_fl_on_floor": sum("tyre_fl" in w[1] for w in WM), "frames": len(WM)}
face = [[0, "neutral"], [6, "happy"], [62, "happy"], [112, "happy"]]
m = {"physics": chk.report(), "peak_hip_torque_Nm": peak_tau(r),
     "wave_static_margin": wave_margin,
     "content": "leans right/back (FR 40°, RL 8°, RR 65°), lifts and waves the front-left paw 59-81° at 2.5 Hz on 3 wheels, then bounce + wheel wiggle"}
write("happy", r, face, False, m, "; wave on 3 wheels + bounce-wiggle, simulated")
REPORT["happy"] = m

# ---------------------------------------------------------------- walk (7 s): it is a wheeled robot: roll forward
def walk_s(t):
    if t < 0.5:
        u = 0.0
    elif t < 1.0:
        u = (t - 0.5) / 0.5
    elif t < 6.0:
        u = 1.0
    else:
        u = 0.0                                             # brake (slow decay)
    return {j: 22.0 for j in HIPS}, (u, u)
r, chk, drift = run_script(walk_s, 7.0)
ys = [f["base"][1] for f in r.frames]
v = -(ys[int(5.5 * FPS)] - ys[int(2.0 * FPS)]) / 3.5 / 10.0
stop = -(ys[-1] - ys[int(6.0 * FPS)])
r04, _, _ = run_script(walk_s, 7.0, mu=0.4)
ys4 = [f["base"][1] for f in r04.frames]
v4 = -(ys4[int(5.5 * FPS)] - ys4[int(2.0 * FPS)]) / 3.5 / 10.0
face = [[0, "neutral"], [12, "determined"], [186, "happy"], [200, "neutral"]]
m = {"speed_cm_s": round(v, 1), "speed_cm_s_mu04": round(v4, 1), "distance_mm": round(-ys[-1], 1),
     "stopping_distance_mm": round(stop, 1), "physics": chk.report(), "peak_hip_torque_Nm": peak_tau(r),
     "note": "N20 at the 80 % PWM cap (≈6 V): no-load 100 rpm = 15.7 cm/s; sim includes gearbox friction and the N20 torque-speed line"}
write("walk", r, face, False, m, "; rear N20 drive, 80 % PWM")
REPORT["walk"] = m

# ---------------------------------------------------------------- turn (5 s): sit on the belly and paddle round
SIT = {"hip_fl": 82.0, "hip_fr": 82.0, "hip_rl": 50.0, "hip_rr": 50.0}
def turn_s(t):
    if t < 0.8:
        return {j: smooth(22, SIT[j], t / 0.8) for j in HIPS}, (0.0, 0.0)
    if t < 4.0:
        return dict(SIT), (-1.0, 1.0)                       # left wheel back, right forward -> turns left (CCW)
    return {j: smooth(SIT[j], 22, (t - 4.1) / 0.7) for j in HIPS}, (0.0, 0.0)
r, chk, drift = run_script(turn_s, 5.0)
yaws = [yaw_of(f["base"]) for f in r.frames]
tot = 0.0
for a, b in zip(yaws[:-1], yaws[1:]):
    tot += (b - a + 180) % 360 - 180
seg = 0.0
for a, b in zip(yaws[int(1.2 * FPS):int(3.8 * FPS)], yaws[int(1.2 * FPS) + 1:int(3.8 * FPS) + 1]):
    seg += (b - a + 180) % 360 - 180
rate = seg / 2.6
end = r.frames[-1]["base"]
face = [[0, "curious"], [30, "determined"], [124, "happy"], [140, "neutral"]]
# comparison runs (not recorded): the concept's own 'lean back + differential spin' on 4 wheels
def cmp_run(pose, cmd, mu=0.6, front_mu=None):
    rr = Robot(mu_floor=mu)
    if front_mu:
        for g in ("tyre_fl", "tyre_fr"):
            rr.m.geom_friction[rr.m.geom(g).id][0] = front_mu
    for i in range(45):
        rr.target.update({k: smooth(22, v_, i / 40) for k, v_ in pose.items()}); rr.step_frame(False)
    for i in range(20):
        rr.u["wheel_rl"], rr.u["wheel_rr"] = cmd; rr.step_frame(False)
    b1 = rr.base_pose(); prev = yaw_of(b1); tt = 0.0
    for i in range(60):
        rr.step_frame(False); y = yaw_of(rr.base_pose()); tt += (y - prev + 180) % 360 - 180; prev = y
    b2 = rr.base_pose()
    return {"yaw_deg_s": round(abs(tt) / 2, 1), "drift_cm_s": round(math.hypot(b2[0] - b1[0], b2[1] - b1[1]) / 20, 1)}
LB = {"hip_fl": 60.0, "hip_fr": 60.0, "hip_rl": 5.0, "hip_rr": 5.0}     # rear at its +5 deg limit
cmp = {"belly_pivot_mu04": cmp_run(SIT, (-1, 1), 0.4),
       "concept_lean_back_spin_TPU_front": cmp_run(LB, (-1, 1)),
       "concept_lean_back_spin_TPU_front_mu04": cmp_run(LB, (-1, 1), 0.4),
       "stand_4wheel_spin_TPU_front": cmp_run({j: 22.0 for j in HIPS}, (-1, 1)),
       "lean_back_spin_if_front_wheels_hard_PLA_mu035": cmp_run(LB, (-1, 1), 0.6, 0.35),
       "arc_one_wheel_TPU_front": cmp_run({j: 22.0 for j in HIPS}, (0, 1))}
m = {"yaw_rate_deg_s": round(rate, 1), "total_turn_deg": round(tot, 1),
     "end_offset_mm": [round(end[0], 1), round(end[1], 1)], "physics": chk.report(), "peak_hip_torque_Nm": peak_tau(r),
     "strategy": "sit on the round belly (front paws 82°, rear 50°) and paddle with the rear wheels in opposite directions; the egg is the pivot",
     "comparison": cmp,
     "caveat": "in the belly pivot the rear tyres carry only ~10 % of the weight and chatter (in contact 15-30 % of the time); the real rate may differ"}
write("turn", r, face, False, m, "; belly-pivot spin, rear N20s ±80 % PWM")
REPORT["turn"] = m

# ---------------------------------------------------------------- sleep (4 s)
SLEEP = {"hip_fl": 75.0, "hip_fr": 75.0, "hip_rl": 72.0, "hip_rr": 72.0}
def sleep_s(t):
    if t < 0.5:
        return {j: 22.0 for j in HIPS}, (0.0, 0.0)
    if t < 2.6:
        return {j: smooth(22, SLEEP[j], (t - 0.5) / 2.1) for j in HIPS}, (0.0, 0.0)
    br = 2.0 * math.sin(2 * math.pi * (t - 2.6) / 1.4)
    return {j: SLEEP[j] + br for j in HIPS}, (0.0, 0.0)
r, chk, drift = run_script(sleep_s, 4.0)
belly = "egg" in r.lowest_floor_contact_geoms()
face = [[0, "neutral"], [10, "sleepy"], [66, "blink"], [72, "sleepy"], [84, "blink"]]
m = {"physics": chk.report(), "belly_on_desk_at_end": belly, "peak_hip_torque_Nm": peak_tau(r),
     "note": "the egg settles on its belly; servos could then be detached (sitting idle ≈ 0.77 W in the concept power table)"}
write("sleep", r, face, False, m, "; sinks onto the belly, simulated")
REPORT["sleep"] = m

# ---------------------------------------------------------------- fall_recover: the concept's own tuck & roll
def fall_clip(name, case, mode, catch, title, max_s=10.0, lead=1.5, tail=2.2, help_s=4.0):
    rr, ctl, res = fall.run_case(case, 0.6, 0.0, record=True, mode=mode, catch=catch, t_end=None,
                                 lead_s=lead, tail_s=tail, help_s=help_s)
    frames = rr.frames
    ev = {}
    for f, nm in ctl.events:
        ev.setdefault(nm, f)
    # landing frame = first frame with tilt > 60
    land = None
    for i, f in enumerate(frames):
        b = f["base"]
        Rm = Rot.from_quat([b[4], b[5], b[6], b[3]]).as_matrix()
        if Rm[2, 2] < math.cos(math.radians(60)):
            land = i; break
    face = [[0, "neutral"]]
    if "push" in ev: face.append([ev["push"] + 3, "surprised"])
    if land is not None and ("tuck" not in ev or land + 4 < ev["tuck"]):   # hybrid tucks before it lands: no sad face then
        face.append([land + 4, "sad"])
    if "tuck" in ev: face.append([ev["tuck"], "determined"])
    if "done" in ev:
        face.append([ev["done"] - 6, "happy"]); face.append([min(len(frames) - 1, ev["done"] + 24), "neutral"])
    if "help" in ev: face.append([ev["help"], "sad"])
    face.sort(key=lambda x: x[0])
    rr.frames = frames[: int(max_s * FPS)]
    b0 = rr.frames[0]["base"]
    for f in rr.frames:
        f["base"][0] -= b0[0]; f["base"][1] -= b0[1]
    # physics check replay is not possible after the fact; take contacts from the result
    m = {"result": "recovered" if res["recovered"] else ("asks for help (cannot recover)" if res["final_state"] == "HELP" else res["final_state"]),
         "landing_gravity_in_body": res["landing"] and res["landing"]["g_body"],
         "t_from_tuck_to_standing_s": res["t_recover_s"], "events_frame": ev, "firmware": mode, "catch_reflex": catch,
         "case": case, "peak_hip_torque_Nm": res["peak_hip_torque_Nm"], "title": title}
    write(name, rr, face, False, m, f"; {title}")
    return m, res

m1, res1 = fall_clip("fall_recover", {"kind": "push", "dir_deg": 0, "speed": 30}, "hybrid", True,
                     "finger push at the head toward its left side, tuck & roll with the recommended HYBRID trigger (tuck at 50° side tilt)")
summ = json.load(open(os.path.join(HERE, "results", "fall_matrix.json")))["summary"]
m1["success_matrix"] = summ
REPORT["fall_recover"] = m1
m2, res2 = fall_clip("fall_back_help", {"kind": "push", "dir_deg": 90, "speed": 90, "release": 75}, "hybrid", True,
                     "hard shove backward (held to 75°), the paw-catch reflex is not enough, lands on its back and asks for help", max_s=8.0)
REPORT["fall_back_help"] = m2
json.dump(REPORT, open(os.path.join(HERE, "results", "clips_report.json"), "w"), indent=1, default=float)
