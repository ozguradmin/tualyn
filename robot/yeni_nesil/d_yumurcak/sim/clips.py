#!/usr/bin/env python3
"""Generate every anim/*.json for Yumurcak from the MuJoCo model (sim/yumurcak_mu0.6.xml).
All clips are servo targets played through the physics (MG90S ±0.20 N·m position servos, firmware slew limit,
contacts), so joints AND base pose are what the sim produced. walk / turn / fall_recover are open-loop gaits /
the IMU recovery controller; idle / talk / happy / sleep are scripted target curves (kinematic intent) whose
static stability is checked by the same sim.
usage: python3 clips.py [clip ...]     (default: all)  -> ../anim/<clip>.json, out/clips_report.json"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rec import *
from common import source_str
from gait import trot_pose

MU = 0.6
WALK = dict(f=2.0, A=24, c=8, K0=32, dK=24, duty=0.5)      # chosen from out/search_walk_mu0.6.json + eval_walk.py
TURN = dict(f=2.0, A=20, c=0, K0=32, dK=16, duty=0.5)      # chosen from eval_turn2.py
REPORT = {}


def yawdeg(b):
    w, x, y, z = b[3:]
    return math.degrees(math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


def stats(s):
    return dict(max_tilt_deg=round(max(f["tilt"] for f in s.frames), 2),
                max_servo_Nm=round(max(v for k, v in s.max_tau.items() if k != "head"), 3),
                max_head_Nm=round(s.max_tau["head"], 3), max_floor_pen_mm=round(s.maxpen, 2), servo_at_clamp_s=round(s.sat_s, 3))


def blink_faces(fr, base="neutral", times=()):
    out = [[0, base]]
    for t in times:
        k = int(round(t * FPS)); out += [[k, "blink"], [k + 4, base]]
    return sorted(out)


# ---------------------------------------------------------------------------------------------------- walk
def walk(mu=MU, T=7.0, record=True):
    s = Rec(mu, 300.0); s.settle(); s.begin()
    s.step_time(0.3)
    t0 = s.t; Tw = T - 0.3 - 0.6
    def ctrl(sim, t):
        tt = t - t0
        if tt < Tw:
            ramp = min(1.0, tt / 0.5)
            sim.target(trot_pose(tt, WALK, "walk", ramp))
        else:
            sim.target(dict(REST))
    s.step_time(T - 0.3, ctrl)
    # steady-state speed: from 1.0 s to the end of the gait, whole strides only
    fr = s.frames
    i0 = int(1.0 * FPS); n_str = int((Tw - 0.7) * WALK["f"]); i1 = i0 + int(round(n_str / WALK["f"] * FPS))
    v = -(fr[i1]["base"][1] - fr[i0]["base"][1]) / ((i1 - i0) / FPS) / 10.0
    dx = fr[-1]["base"][0] - fr[0]["base"][0]
    dpsi = yawdeg(fr[-1]["base"]) - yawdeg(fr[0]["base"])
    m = dict(speed_cm_s=round(v, 2), distance_mm=round(-(fr[-1]["base"][1] - fr[0]["base"][1]), 1),
             lateral_drift_mm=round(dx, 1), heading_drift_deg=round(dpsi, 1), gait=WALK, **stats(s))
    face = [[0, "neutral"], [6, "determined"], [int(2.4 * FPS), "blink"], [int(2.4 * FPS) + 4, "determined"],
            [int(5.2 * FPS), "blink"], [int(5.2 * FPS) + 4, "determined"], [int((T - 0.5) * FPS), "happy"]]
    a = s.anim(loop=False, source=source_str(mu, f"; open-loop diagonal trot f={WALK['f']} Hz, yaw ±{WALK['A']}° about {WALK['c']}°, knee {WALK['K0']}°+{WALK['dK']}° lift"),
               metrics=m, face=face)
    return a, m


# ---------------------------------------------------------------------------------------------------- turn
def turn(mu=MU, T=5.0):
    s = Rec(mu, 300.0); s.settle(); s.begin()
    s.target({"head": 25}); s.step_time(0.3)
    t0 = s.t; Tw = T - 0.3 - 0.6
    def ctrl(sim, t):
        tt = t - t0
        if tt < Tw:
            sim.target({**trot_pose(tt, TURN, "turn", min(1.0, tt / 0.5)), "head": 25})
        else:
            sim.target(dict(REST))
    s.step_time(T - 0.3, ctrl)
    ys = np.degrees(np.unwrap(np.radians([yawdeg(f["base"]) for f in s.frames])))
    i0, i1 = int(1.0 * FPS), int((0.3 + Tw) * FPS)
    rate = (ys[i1] - ys[i0]) / ((i1 - i0) / FPS)
    xy = [f["base"][:2] for f in s.frames]
    drift = max(math.hypot(p[0] - xy[0][0], p[1] - xy[0][1]) for p in xy)
    m = dict(turn_rate_deg_s=round(rate, 1), total_turn_deg=round(ys[-1] - ys[0], 1), max_drift_mm=round(drift, 1),
             direction="to the robot's left (CCW from above)", gait=TURN, **stats(s))
    face = [[0, "curious"], [int(1.8 * FPS), "blink"], [int(1.8 * FPS) + 4, "curious"], [int(3.6 * FPS), "neutral"],
            [int((T - 0.4) * FPS), "blink"], [int((T - 0.4) * FPS) + 4, "neutral"]]
    return s.anim(loop=False, source=source_str(mu, f"; turn in place: trot with all paws sweeping the same way round the egg, f={TURN['f']} Hz, yaw ±{TURN['A']}°"),
                  metrics=m, face=face), m


# ---------------------------------------------------------------------------------------------------- scripted clips
def scripted(name, T, fn, face, loop, mu=MU, lead=1.0, slew=300.0, extra=""):
    """fn(t) -> joint targets; the clip records [lead, lead+T]; loops get lead-in so the start state is periodic"""
    s = Rec(mu, slew); s.settle()
    if lead > 0:
        t_start = s.t
        def pre(sim, t):
            sim.target(fn((t - t_start - lead) % T if loop else 0.0))
        s.step_time(lead, pre, record=False)
    s.begin()
    s.step_time(T, lambda sim, t: sim.target(fn(t)))
    m = stats(s)
    xy = [f["base"][:2] for f in s.frames]
    m["base_drift_mm"] = round(math.hypot(xy[-1][0] - xy[0][0], xy[-1][1] - xy[0][1]), 2)
    a = s.anim(loop=loop, source=source_str(mu, "; scripted servo targets played through the sim (static stability checked)" + extra),
               metrics=m, face=face)
    if loop:
        a = close_loop(a)
    return a, m


def idle_fn(t):            # 5 s loop: breathing (2 breaths), slow head look, tiny weight shift
    T = 5.0
    br = 0.5 - 0.5 * math.cos(2 * math.pi * 2 * t / T)
    look = 10 * math.sin(2 * math.pi * t / T) + 4 * math.sin(2 * math.pi * 2 * t / T + 0.6)
    sway = 2.0 * math.sin(2 * math.pi * t / T)
    p = {"head": look}
    for k in LEGS:
        side = 1 if k[1] == "l" else -1
        p[f"knee_{k}"] = 30 + 3.5 * br + side * sway
        p[f"yaw_{k}"] = 0
    return p


def talk_fn(t):            # 5 s loop: head gestures, nods (front/back knee differential), little bounce
    T = 5.0
    w = 2 * math.pi / T
    head = 18 * math.sin(w * t) + 7 * math.sin(3 * w * t + 0.8) + 4 * math.sin(7 * w * t)
    nod = 3.0 * math.sin(2 * w * t)     # faster nods made the paws stick-slip and the egg crept 9-15 mm per loop
    bounce = 2.5 * (0.5 - 0.5 * math.cos(8 * w * t))
    p = {"head": head}
    for k in LEGS:
        fb = 1 if k[0] == "f" else -1
        p[f"knee_{k}"] = 31 + bounce + fb * nod
        p[f"yaw_{k}"] = 0
    return p


def talk_faces(T=5.0):
    rng = np.random.default_rng(7)
    out, k, cur = [], 0, "talk_a"
    pauses = {int(1.9 * FPS): ("neutral", 8), int(3.7 * FPS): ("blink", 4)}
    while k < int(T * FPS) - 3:
        if any(abs(k - p) < 3 for p in pauses):
            pk = [p for p in pauses if abs(k - p) < 3][0]
            e, n = pauses.pop(pk); out.append([k, e]); k += n; continue
        out.append([k, cur]); cur = "talk_b" if cur == "talk_a" else "talk_a"
        k += int(rng.integers(5, 8))            # 0.17 - 0.23 s
    out.append([int(T * FPS) - 3, "talk_a"])
    return out


HAPPY_T = 4.0
def happy_fn(t):           # signature: weight onto the right-back, front-left paw up and waves, head turns to it
    def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
    shift = ease(t / 0.5) * (1 - ease((t - 3.2) / 0.6))
    lift = ease((t - 0.45) / 0.35) * (1 - ease((t - 2.9) / 0.4))
    wave = math.sin(2 * math.pi * 2.5 * max(0.0, t - 0.8)) if 0.8 < t < 2.9 else 0.0
    p = {"head": 30 * ease((t - 0.3) / 0.4) * (1 - ease((t - 3.0) / 0.6)) + 6 * wave * lift,
         "knee_br": 30 + 30 * shift, "knee_fr": 30 + 10 * shift, "knee_bl": 30 + 10 * shift,
         "yaw_fr": 0, "yaw_bl": 0, "yaw_br": 0,
         "knee_fl": 30 + lift * (88 + 22 * wave), "yaw_fl": 35 * lift}
    return p


SLEEP_T = 4.0
def sleep_fn(t):           # settle into the nest pose (sits on the 4 hip balls), head droops to one side
    def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
    d = ease((t - 0.4) / 2.2)
    p = {"head": -22 * ease((t - 1.2) / 1.6)}
    for k in LEGS:
        p[f"knee_{k}"] = 30 + (162 - 30) * d     # 162: paws tucked flat along the egg (kmax 164 at yaw 0)
        p[f"yaw_{k}"] = 0
    return p


def idle():
    face = [[0, "neutral"], [38, "blink"], [42, "neutral"], [96, "curious"], [118, "neutral"], [124, "blink"], [128, "neutral"]]
    return scripted("idle", 5.0, idle_fn, face, True, extra="; 5 s loop")


def talk():
    return scripted("talk", 5.0, talk_fn, talk_faces(), True, extra="; 5 s loop, talk_a/talk_b every 0.17-0.23 s")


def happy():
    face = [[0, "neutral"], [8, "happy"], [int(3.3 * FPS), "blink"], [int(3.3 * FPS) + 4, "happy"]]
    a, m = scripted("happy", HAPPY_T, happy_fn, face, False, lead=0.0, slew=400.0, extra="; wave on 3 legs after a weight shift onto the right-back leg")
    return a, m


def sleep():
    face = [[0, "neutral"], [6, "blink"], [10, "sleepy"], [int(2.7 * FPS), "asleep"]]
    return scripted("sleep", SLEEP_T, sleep_fn, face, False, lead=0.0, slew=150.0, extra="; slow 150°/s settle onto the hip balls")


# ---------------------------------------------------------------------------------------------------- fall_recover
def _fall_clip(case, T, mu=MU):
    import fall
    res, s = fall.run_case(case, mu, T=T, keep=True)
    m = {k: res[k] for k in ("case", "push_N", "success", "attempts", "t_fall", "t_up", "max_knee_Nm", "max_yaw_Nm", "max_pen_mm", "servo_at_clamp_s")}
    m["t_up"] = m["t_up"] and round(m["t_up"], 2); m["t_fall"] = m["t_fall"] and round(m["t_fall"], 2)
    m["max_tilt_deg"] = round(max(f["tilt"] for f in s.frames), 1)
    m["log"] = res["log"]
    src = source_str(mu, f"; {case}: {res['push_N']} N shove for 0.12 s at head height, then the IMU self-righting controller "
                         f"(sim/fall.py, strategy '{fall.STRATEGY}': egg-mode tuck, down-side paws sweep 164->0 at 60°/s, re-fold in flank tuck on retry)")
    a = s.anim(loop=False, source=src, metrics=m)
    a["face"][0][0] = 0                       # the first face is set right after the first recorded frame
    return a, m


def fall_recover():
    return _fall_clip("nudge towards its right (-X)", 6.8)


def fall_recover_back():
    return _fall_clip("nudge backwards", 13.5)


CLIPS = dict(walk=walk, turn=turn, idle=idle, talk=talk, happy=happy, sleep=sleep, fall_recover=fall_recover,
             fall_recover_back=fall_recover_back)

if __name__ == "__main__":
    which = sys.argv[1:] or list(CLIPS)
    rep_f = os.path.join(HERE, "out", "clips_report.json")
    REPORT = json.load(open(rep_f)) if os.path.exists(rep_f) else {}
    for c in which:
        a, m = CLIPS[c]()
        save(c, a)
        REPORT[c] = m
        if c in ("walk", "turn"):              # same gait on the slippery desk (not saved as a clip)
            REPORT[c + "_mu0.4"] = CLIPS[c](mu=0.4)[1]
        print(c, a["frames"], "frames", json.dumps(m))
    json.dump(REPORT, open(rep_f, "w"), indent=1)
