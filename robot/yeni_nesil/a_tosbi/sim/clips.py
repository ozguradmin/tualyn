#!/usr/bin/env python3
"""Generate every Tosbi animation clip from MuJoCo (anim/*.json) + sim/results.json.

All clips run through the physics: the joint values written are the SIMULATED joint angles (servo tracking,
torque/speed limited) and `base` is the simulated world pose of the body link. idle/talk/happy/sleep use
scripted servo targets (what the firmware would send); walk/turn use the tuned trot; fall_recover is a shove
followed by the self-righting firmware (recover.py) reacting to the simulated IMU only.
Usage: python3 -I clips.py [mu]
"""
import json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tosbi import Sim, REST, LEGS, stand_pose, smooth, lerp_pose, save_clip, yaw_of, FPS, PKG
from gait import gait_targets, DEFAULT
from recover import Recover

HERE = os.path.dirname(os.path.abspath(__file__))
MU = float(sys.argv[1]) if len(sys.argv) > 1 else 0.6
WALK = dict(DEFAULT, T=0.7, sw=0.5, lift=20, Af=14, Ab=20, bias=3.0)      # knees never reach the 0.20 N m clamp
WALK_FAST = dict(DEFAULT, T=0.5, sw=0.5, lift=25, Af=14, Ab=20, bias=3.0) # reported only: +45 % speed, knees at clamp 7 % of the time
TURN = dict(DEFAULT, T=0.8, sw=0.5, lift=25, Af=14, Ab=14, bias=0.0)
results = {}


def _save(clip, name):
    if MU == 0.6: save_clip(clip, name)          # anim/ holds the mu 0.6 runs; other mu only report metrics


def new_sim(sign=1):
    s = Sim(MU); s.set_pose(stand_pose(sign)); s.drop_to_floor(0.0)
    s.run(0.5, record=False)                     # settle on the toes
    return s


def start_rec(s):
    s.frames = []; s.faces = []; s.next_rec = s.t; s.reset_torque_stats()
    return s.t


def close_loop(clip):
    """make frame n-1 == frame 0 (rig.js loops x % (n-1)); spread the small physical drift linearly."""
    B = np.array(clip["base"], float); n = len(B)
    d = B[-1] - B[0]
    for i in range(n):
        B[i] -= d * (i / (n - 1))
    B[:, 3:] /= np.linalg.norm(B[:, 3:], axis=1, keepdims=True)
    clip["base"] = [[round(v, 3) if k < 3 else round(v, 5) for k, v in enumerate(b)] for b in B]
    for j, arr in clip["joints"].items():
        e = arr[-1] - arr[0]
        clip["joints"][j] = [round(v - e * (i / (n - 1)), 2) for i, v in enumerate(arr)]
    return float(np.linalg.norm(d[:3])), float(np.degrees(2 * np.arccos(min(1.0, abs(float(np.dot(B[0, 3:], B[0, 3:] + d[3:])) / max(1e-9, np.linalg.norm(B[0, 3:] + d[3:])))))))


def frame_checks(s):
    zs = [f["base"][2] for f in s.frames]
    return {"base_z_min_mm": round(min(zs), 2), "base_z_max_mm": round(max(zs), 2)}


def blink_faces(s, base_face, t0, blinks, tt):
    """face scheduler helper: blink for 4 frames (0.13 s) at each time in `blinks`."""
    for b in blinks:
        if b <= tt < b + 0.13: return "blink"
    return base_face


# ------------------------------------------------------------------ idle (5 s loop)
def idle():
    s = new_sim(); P = 5.0
    def tg(tt):
        br = math.sin(2 * math.pi * tt / 2.5)
        sw = math.sin(2 * math.pi * tt / P)
        p = {f"knee_{l}": 80 + 2.5 * br for l in LEGS}
        for l in LEGS: p[f"hip_{l}"] = (3.0 if l in ("fl", "rl") else -3.0) * sw
        p["neck"] = 15 + 5 * math.sin(2 * math.pi * tt / P + 0.8) + 1.5 * br
        return p
    s.run(0.6, lambda sim, t: lerp_pose(stand_pose(1), tg(0.0), smooth(t / 0.6)), record=False)
    t0 = s.t; s.run(P, lambda sim, t: tg(t - t0), record=False)        # warm-up cycle
    t0 = start_rec(s)
    def pol(sim, t):
        tt = t - t0; sim.set_face(blink_faces(sim, "neutral", t0, [1.2, 3.5, 3.8], tt)); return tg(tt % P)
    s.run(P + 1.0 / FPS + 1e-6, pol)
    s.frames = s.frames[:int(round(P * FPS)) + 1]
    clip = s.to_clip(loop=True, source_note="scripted servo targets (breathing knees ±2.5°, yaw sway ±3°, neck look), body motion from physics")
    dpos, dang = close_loop(clip)
    clip["metrics"] = {"loop_drift_corrected_mm": round(dpos, 2), **frame_checks(s), "servo_torque_Nm": s.torque_stats()}
    _save(clip, "idle"); results["idle"] = clip["metrics"]


# ------------------------------------------------------------------ talk (5 s loop)
def talk():
    s = new_sim(); P = 5.0
    def tg(tt):
        w = 2 * math.pi
        p = {}
        rock = math.sin(w * 0.6 * tt)
        for l in LEGS:
            p[f"knee_{l}"] = 80 + (3.0 if l in ("fl", "fr") else -3.0) * rock
            p[f"hip_{l}"] = (4.0 if l in ("fl", "rl") else -4.0) * math.sin(w * 0.4 * tt)
        p["neck"] = 17 + 5 * math.sin(w * 1.2 * tt) + 3 * math.sin(w * 0.4 * tt + 1.0)
        return p
    # mouth flaps: talk_a/talk_b alternate every 5-7 frames, one pause with a blink
    seq, f = [], 0
    pattern = [6, 5, 7, 6, 5, 6, 7, 5, 6, 6, 5, 7]
    k = 0
    while f < 150:
        if 72 <= f < 90:
            seq.append([f, "neutral"]); seq.append([f + 8, "blink"]); seq.append([f + 12, "neutral"]); f = 90; continue
        seq.append([f, "talk_a" if k % 2 == 0 else "talk_b"]); f += pattern[k % len(pattern)]; k += 1
    seq = [x for x in seq if x[0] < 150]
    s.run(0.6, lambda sim, t: lerp_pose(stand_pose(1), tg(0.0), smooth(t / 0.6)), record=False)
    t0 = s.t; s.run(P, lambda sim, t: tg(t - t0), record=False)
    t0 = start_rec(s)
    s.run(P + 1.0 / FPS + 1e-6, lambda sim, t: tg((t - t0) % P))
    s.frames = s.frames[:int(round(P * FPS)) + 1]
    clip = s.to_clip(loop=True, source_note="scripted head nods/body rock (kinematic targets), body motion from physics")
    clip["face"] = seq
    dpos, _ = close_loop(clip)
    clip["metrics"] = {"loop_drift_corrected_mm": round(dpos, 2), **frame_checks(s), "mouth_flap_s": "0.17-0.23", "servo_torque_Nm": s.torque_stats()}
    _save(clip, "talk"); results["talk"] = clip["metrics"]


# ------------------------------------------------------------------ happy (4 s): shift weight, raise front-left paw, wave, bounce
def happy():
    s = new_sim(); t0 = start_rec(s)
    st = stand_pose(1)
    shift = dict(st, hip_rl=20, hip_rr=20, hip_fr=14, neck=26)          # move the support triangle under the CoM
    up = dict(shift, knee_fl=-15, hip_fl=14)
    tilts = []
    def pol(sim, t):
        tt = t - t0
        sim.set_face("happy")
        if tt < 0.5: return lerp_pose(st, shift, smooth(tt / 0.5))
        if tt < 0.95: return lerp_pose(shift, up, smooth((tt - 0.5) / 0.45))
        if tt < 2.45:
            ph = (tt - 0.95) * 2.0                                         # 3 waves at 2 Hz
            return dict(up, hip_fl=14 - 18 * (0.5 - 0.5 * math.cos(2 * math.pi * ph)), knee_fl=-15 + 10 * math.sin(2 * math.pi * ph))
        if tt < 2.95: return lerp_pose(up, shift, smooth((tt - 2.45) / 0.5))
        if tt < 3.35: return lerp_pose(shift, st, smooth((tt - 2.95) / 0.4))
        b = math.sin(math.pi * min(1.0, (tt - 3.35) / 0.32)) ** 2           # one happy bounce
        return {**st, **{f"knee_{l}": 80 - 12 * b for l in LEGS}, "neck": 15 + 8 * b}
    s.run(4.0 + 1e-6, pol)
    for f in s.frames:
        q = f["base"][3:]; R = 1 - 2 * (q[1] ** 2 + q[2] ** 2); tilts.append(math.degrees(math.acos(max(-1, min(1, R)))))
    clip = s.to_clip(loop=False, source_note="scripted wave targets; 3-leg balance comes from the physics (rear hips +20°, front-right +14° shift)")
    clip["metrics"] = {"max_body_tilt_deg": round(max(tilts), 2), **frame_checks(s), "servo_torque_Nm": s.torque_stats(),
                       "note": "without the weight shift the sim nose-dives onto the head (calc.py: CoM 7.4 mm outside the 3-foot triangle)"}
    _save(clip, "happy"); results["happy"] = clip["metrics"]


# ------------------------------------------------------------------ sleep (4 s)
def sleep():
    s = new_sim(); t0 = start_rec(s)
    st = stand_pose(1)
    low = {**{f"hip_{l}": 0.0 for l in LEGS}, **{f"knee_{l}": 12.0 for l in LEGS}, "neck": -24.0}
    def pol(sim, t):
        tt = t - t0
        if tt < 0.4: f = "neutral"
        elif tt < 1.3: f = "sleepy"
        elif tt < 1.45: f = "blink"
        elif tt < 2.4: f = "sleepy"
        else: f = "blink"
        sim.set_face(f)
        p = lerp_pose(st, low, smooth((tt - 0.6) / 2.0))
        p["neck"] = st["neck"] + (low["neck"] - st["neck"]) * smooth((tt - 0.4) / 1.6)
        if tt > 2.8: p["neck"] = low["neck"] - 2.0 * math.sin(math.pi * min(1, (tt - 2.8) / 1.2))   # slow sleepy breath
        return p
    s.run(4.0 + 1e-6, pol)
    clip = s.to_clip(loop=False, source_note="scripted settle; the belly dome lands on the desk in the physics")
    clip["metrics"] = {**frame_checks(s), "servo_torque_Nm": s.torque_stats(), "rests_on": "belly dome + chin (head) on the desk, toes lifted (MuJoCo contacts at the last frame)"}
    _save(clip, "sleep"); results["sleep"] = clip["metrics"]


# ------------------------------------------------------------------ walk (7 s)
def walk():
    s = new_sim(); t0 = start_rec(s)
    t_go, t_stop, t_end = 0.3, 6.3, 7.0
    last = {}
    def pol(sim, t):
        tt = t - t0
        sim.set_face(blink_faces(sim, "neutral", t0, [2.1, 4.7], tt))
        if tt < t_go: return stand_pose(1)
        if tt < t_stop:
            g = gait_targets(tt - t_go, WALK, amp=min(1.0, (tt - t_go) / WALK["T"]))
            last.update(g); return g
        return lerp_pose(last, stand_pose(1), smooth((tt - t_stop) / 0.4))
    s.run(t_end + 1e-6, pol)
    F = s.frames
    i0 = int((t_go + WALK["T"] * 1.0) * FPS); i1 = int(t_stop * FPS)
    p0, p1 = np.array(F[i0]["base"][:3]), np.array(F[i1]["base"][:3])
    dist = np.linalg.norm((p1 - p0)[:2]); dt = (i1 - i0) / FPS
    fwd = -(p1 - p0)[1]
    yaw = math.degrees(yaw_of(F[i1]["base"][3:]) - yaw_of(F[i0]["base"][3:]))
    clip = s.to_clip(loop=False, source_note=f"trot T={WALK['T']} s, hip -{WALK['Ab']-WALK['bias']:.0f}..+14/+{WALK['Af']+WALK['bias']:.0f}°, knee lift {WALK['lift']}°")
    clip["metrics"] = {"speed_cm_s": round(fwd / 10 / dt, 2), "path_cm": round(dist / 10, 1), "steady_window_s": round(dt, 2),
                       "lateral_drift_cm": round((p1 - p0)[0] / 10, 2), "yaw_drift_deg": round(yaw, 1),
                       "servo_torque_Nm": s.torque_stats(), **frame_checks(s)}
    _save(clip, "walk"); results["walk"] = clip["metrics"]


def walk_fast():
    """metrics only: the 0.5 s period trot (not saved as a clip)"""
    s = new_sim(); t0 = start_rec(s)
    def pol(sim, t):
        tt = t - t0
        return gait_targets(tt, WALK_FAST, amp=min(1.0, tt / WALK_FAST["T"]))
    s.run(5.0, pol)
    F = s.frames; i0, i1 = int(1.0 * FPS), len(F) - 1
    fwd = -(F[i1]["base"][1] - F[i0]["base"][1]); dt = (i1 - i0) / FPS
    results["walk_fast"] = {"speed_cm_s": round(fwd / 10 / dt, 2), "servo_torque_Nm": s.torque_stats()}


# ------------------------------------------------------------------ turn (5 s)
def turn():
    s = new_sim(); t0 = start_rec(s)
    t_go, t_stop, t_end = 0.3, 4.5, 5.0
    last = {}
    def pol(sim, t):
        tt = t - t0
        sim.set_face(blink_faces(sim, "neutral", t0, [1.6, 3.6], tt))
        if tt < t_go: return stand_pose(1)
        if tt < t_stop:
            g = gait_targets(tt - t_go, TURN, fwd=0.0, turn=1.0, amp=min(1.0, (tt - t_go) / TURN["T"]))
            last.update(g); return g
        return lerp_pose(last, stand_pose(1), smooth((tt - t_stop) / 0.4))
    s.run(t_end + 1e-6, pol)
    F = s.frames
    i0 = int((t_go + TURN["T"]) * FPS); i1 = int(t_stop * FPS)
    yaws = np.unwrap([yaw_of(f["base"][3:]) for f in F])
    rate = math.degrees(yaws[i1] - yaws[i0]) / ((i1 - i0) / FPS)
    drift = np.linalg.norm(np.array(F[-1]["base"][:2]) - np.array(F[0]["base"][:2]))
    clip = s.to_clip(loop=False, source_note=f"turn in place (left side strokes reversed), T={TURN['T']} s, hip ±14°, lift {TURN['lift']}°")
    clip["metrics"] = {"yaw_rate_deg_s": round(rate, 1), "total_yaw_deg": round(math.degrees(yaws[-1] - yaws[0]), 1),
                       "centre_drift_cm": round(drift / 10, 2), "servo_torque_Nm": s.torque_stats(), **frame_checks(s)}
    _save(clip, "turn"); results["turn"] = clip["metrics"]


# ------------------------------------------------------------------ fall_recover
def fall_recover(push_ang_deg=90.0, F=10.0, name="fall_recover", save=True, hand=(-41.0, 70.0, 2.6), T_END=6.6, WALK_S=1.2):
    """hand=(edge_x_mm, release_tilt_deg, force_N): a hand lifts the shell edge at x=edge_x (mid-plane) straight up
    until the body is tilted release_tilt_deg, then lets go. Otherwise a 0.15 s shove of F newtons at push_ang_deg.
    After standing up on the other face it walks WALK_S seconds (the top-dome ToF now looks at the desk) and stops."""
    s = new_sim(); t0 = start_rec(s)
    ctrl = Recover(); t_push = 0.8
    state = {"stood": None, "walk0": None, "released": None, "landed": None, "flip": None, "stop": None}
    ang = math.radians(push_ang_deg)
    def push(sim, t):
        b = sim.bid; com = sim.d.xipos[b]
        if hand is not None:
            ex, rel, Fh = hand
            tilt = math.degrees(math.acos(max(-1.0, min(1.0, sim.up()))))
            if t >= t0 + t_push and state["released"] is None:
                if tilt >= rel: state["released"] = t - t0; return
                ramp = min(1.0, (t - t0 - t_push) / 0.6)
                p = sim.d.xpos[b] + sim.R() @ np.array([ex, 0.0, 42.45]) / 1000
                f = np.array([0.0, 0.0, Fh * ramp])
                sim.d.xfrc_applied[b, :3] = f; sim.d.xfrc_applied[b, 3:] = np.cross(p - com, f)
            return
        if t0 + t_push <= t < t0 + t_push + 0.15:
            f = np.array([math.cos(ang), math.sin(ang), 0.0]) * F
            p = sim.d.xpos[b] + sim.R() @ np.array([0, 0, 0.06])
            sim.d.xfrc_applied[b, :3] = f; sim.d.xfrc_applied[b, 3:] = np.cross(p - com, f)
    def pol(sim, t):
        tt = t - t0
        if state["walk0"] is not None:                                     # keeps walking on the other face, then stops
            sg = ctrl.sign; w = tt - state["walk0"]
            sim.set_face(blink_faces(sim, "neutral_inv" if sg < 0 else "neutral", t0, [], w))
            if w < WALK_S:
                g = gait_targets(w, WALK, sign=sg, amp=min(1.0, w / WALK["T"])); state["last"] = g; return g
            state["stop"] = state["stop"] or tt
            return lerp_pose(state["last"], stand_pose(sg), smooth((w - WALK_S) / 0.4))
        c = ctrl(sim, t)
        if state["landed"] is None and state["released"] is not None and sim.up() < -0.5: state["landed"] = tt
        if state["flip"] is None and ctrl.mode == "flip_through": state["flip"] = tt
        if t_push <= tt and state["stood"] is None and ctrl.mode in ("stand", "edge_kick"):
            sim.set_face("surprised_inv" if ctrl.sign < 0 else "surprised")
        if ctrl.done_t is not None and len(ctrl.log) > 0:
            state["stood"] = state["stood"] or tt
            sim.set_face("happy_inv" if ctrl.sign < 0 else "happy")
            if tt - state["stood"] > 1.0: state["walk0"] = tt
        return c
    s.run(T_END + 1e-6, pol, push=push)
    dist = (f"a hand lifts the shell edge (x={hand[0]:.0f} mm) with up to {hand[2]:.1f} N and lets go at {hand[1]:.0f}° tilt" if hand else
            f"{F:.0f} N shove for 0.15 s at {push_ang_deg:.0f}° 60 mm above the floor")
    clip = s.to_clip(loop=False, source_note=dist + ", then recover.py (MPU6050-accelerometer-only firmware state machine, "
                     "simulated imu_acc + noise) – NOT hand animated")
    fr = lambda x: None if x is None else int(round(x * FPS))
    ev = [[fr(t_push), "el kabuğun sağ kenarını kaldırıyor (2.6 N)"]]
    if state["released"] is not None: ev.append([fr(state["released"]), "el bırakıyor (70° eğik)"])
    if state["landed"] is not None: ev.append([fr(state["landed"]), "sırtüstü yere çarptı; firmware ivmeölçerle tepki veriyor"])
    if state["flip"] is not None: ev.append([fr(state["flip"]), "dizler kabuk düzleminden geçiyor (~160°)"])
    if state["stood"] is not None: ev.append([fr(state["stood"]), "öbür yüzünde (B) ayakta, ekran döndü"])
    if state["walk0"] is not None: ev.append([fr(state["walk0"]), "B yüzünde yürüyor; üst kubbedeki ToF masayı görüyor"])
    if state["stop"] is not None: ev.append([fr(state["stop"]), "duruyor"])
    clip["events"] = [e for e in ev if e[0] is not None and e[0] < clip["frames"]]
    clip["caption_tr"] = ("Fizik simülasyonu: bir el kabuğun kenarını kaldırıp bırakıyor (el görünmüyor), Tosbi sırtüstü düşüyor, "
                          "dizlerini kabuk düzleminden geçirip öbür yüzünde kalkıyor ve kısa bir yürüyüş yapıyor.")
    B = np.array(clip["base"], float)
    yaw0, yaw1 = yaw_of(B[0, 3:]), yaw_of(B[-1, 3:])
    clip["metrics"] = {"disturbance": dist, "released_at_s": state["released"], "modes": ctrl.log, "recovered": state["stood"] is not None,
                       "t_recovered_s": None if state["stood"] is None else round(state["stood"], 2),
                       "t_react_to_stand_s": None if (state["stood"] is None or state["landed"] is None) else round(state["stood"] - state["landed"], 2),
                       "final_face": "B (ters yüz)" if ctrl.sign < 0 else "A", **frame_checks(s),
                       "walk_after_s": WALK_S if state["walk0"] is not None else None,
                       "base_drift_mm": round(float(np.linalg.norm(B[-1, :2] - B[0, :2])), 1),
                       "heading_change_deg": round(math.degrees(math.atan2(math.sin(yaw1 - yaw0), math.cos(yaw1 - yaw0))), 1),
                       "joint_clamp_excess_deg": round(s.clamp_excess, 2), "servo_torque_Nm": s.torque_stats()}
    if save:
        _save(clip, name); results[name] = clip["metrics"]
    return clip, ctrl


if __name__ == "__main__":
    which = sys.argv[2:] or ["idle", "talk", "happy", "sleep", "walk", "walk_fast", "turn", "fall_recover"]
    for w in which:
        globals()[w](); print(w, json.dumps(results.get(w)), flush=True)
    p = os.path.join(HERE, "out", f"clips_mu{MU}.json"); os.makedirs(os.path.dirname(p), exist_ok=True)
    old = json.load(open(p)) if os.path.exists(p) else {}
    old.update(results); json.dump(old, open(p, "w"), indent=1)
