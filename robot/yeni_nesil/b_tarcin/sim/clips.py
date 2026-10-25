#!/usr/bin/env python3
"""Produce anim/*.json for Tarcin from the MuJoCo model (tarcin.py, GLB frames).
  walk, turn, fall_recover, happy, sleep : physically simulated (recorded joint angles + base from MuJoCo)
  idle, talk                              : kinematic loops (feet fixed by IK, sagittal body motion only), then
                                            replayed in MuJoCo as a stability check (report in out/clip_checks.json)
usage: clips.py [names...]"""
import sys, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tarcin as T, gait as G, recover as R

PKG = T.PKG
ANIM = os.path.join(PKG, "anim")
OUT = os.path.join(HERE, "out")
MU = 0.6
SRC = ("MuJoCo 3.17, model.glb hulls, MG90S 0.20 N·m / 600°/s position servos (kp 3) with back-EMF torque-speed droop "
       "(tau·(1-ω/ω0), ω0 11 rad/s), firmware hip_f(neck_pan) limit, μ=0.6 desk / 0.9 TPU paws, mass 368 g, dt 0.5 ms")
HZ = T.HIP_Z / 1000.0
CHECKS_F = os.path.join(OUT, "clip_checks.json")


def save(name, clip):
    os.makedirs(ANIM, exist_ok=True)
    json.dump(clip, open(os.path.join(ANIM, name + ".json"), "w"), separators=(",", ":"))
    print("wrote", name, clip["frames"], "frames", clip.get("metrics", {}))


def checks_update(name, d):
    c = json.load(open(CHECKS_F)) if os.path.exists(CHECKS_F) else {}
    c[name] = d
    json.dump(c, open(CHECKS_F, "w"), indent=1)


def smooth(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


# ---------------- kinematic body motion with feet fixed ----------------
REST_FEET = None


def body_pose_joints(dy=0.0, dz=0.0, pitch=0.0, feet=None):
    """Body moved by (dy, dz) [m] and pitched by 'pitch' deg (about X through the hip-height centre), feet kept at
    their rest world positions. Returns (joint dict, base [mm + quat])."""
    global REST_FEET
    if REST_FEET is None: REST_FEET = G.rest_feet()
    feet = feet or {}
    th = math.radians(pitch); c, s = math.cos(th), math.sin(th)
    out = {}
    for leg in T.LEGS:
        hy = -0.032 if leg[0] == "f" else 0.032
        fy0, fz0 = REST_FEET[leg]
        fw = np.array([hy + fy0, HZ + fz0])                   # foot world (y, z)
        if leg in feet: fw = fw + np.array(feet[leg])          # lifted / moved paw
        hl = np.array([hy, HZ]); cc = np.array([0, HZ])
        Rm = np.array([[c, -s], [s, c]])
        hw = cc + Rm @ (hl - cc) + np.array([dy, dz])
        rel = Rm.T @ (fw - hw)
        h, k = T.ik(leg, rel[0], rel[1])
        out["hip_" + leg] = h; out["knee_" + leg] = k
    org = np.array([0, 0.0]); bw = np.array([0, HZ]) + Rm @ (org - np.array([0, HZ])) + np.array([dy, dz])
    base = [0.0, bw[0] * 1000, bw[1] * 1000, math.cos(th / 2), math.sin(th / 2), 0.0, 0.0]
    return out, base


def kin_clip(fn, n, loop):
    fr = []
    for i in range(n):
        t = i / 30.0
        j, b = fn(t)
        fr.append((j, b))
    joints = {n_: [round(f[0].get(n_, 0.0), 3) for f in fr] for n_ in T.JOINTS}
    base = [[round(x, 4) if k < 3 else round(x, 6) for k, x in enumerate(f[1])] for f in fr]
    return {"fps": 30, "loop": loop, "frames": n, "joints": joints, "base": base}


def sim_replay_check(clip, mu=MU, seconds_extra=0.0):
    """Replay a kinematic clip's joint angles as servo setpoints on the free-standing model."""
    xml = T.build(mu=mu)
    s = T.Sim(xml, record=False)
    j0 = {n: clip["joints"][n][0] for n in T.JOINTS}
    b0 = clip["base"][0]
    s.set_pose(j0, base=(b0[0] / 1000, b0[1] / 1000, b0[2] / 1000, *b0[3:]))
    s.drop_to_floor(); s.hold(j0, 0.5)
    n = clip["frames"]
    dev_p, dev_a, minup = 0.0, 0.0, 1.0
    p_start = s.d.qpos[0:3].copy()
    loops = 2 if clip["loop"] else 1
    for L in range(loops):
        for i in range(n):
            tg = {k: clip["joints"][k][i] for k in T.JOINTS}
            for _ in range(s.sub):
                s.step(tg)
            b = clip["base"][i]
            p = s.d.qpos[0:3] * 1000
            dev_p = max(dev_p, float(np.linalg.norm(p - np.array(b[:3]))))
            q = s.d.qpos[3:7]; qb = np.array(b[3:])
            ang = math.degrees(2 * math.acos(min(1.0, abs(float(q @ qb)))))
            dev_a = max(dev_a, ang)
            minup = min(minup, float(s.up()[2][2]))
    drift = float(np.linalg.norm(s.d.qpos[0:2] - p_start[0:2]) * 1000)
    return dict(max_base_dev_mm=round(dev_p, 2), max_tilt_dev_deg=round(dev_a, 2), min_up=round(minup, 3),
                drift_after_mm=round(drift, 2), loops=loops, peak_tau=round(s.peak_tau, 3), mu=mu)


# ---------------- idle (kinematic loop, 5 s) ----------------
def idle():
    n = 151
    def f(t):
        u = t / 5.0
        dz = 0.0010 * math.sin(2 * math.pi * 2 * u)                       # 2 breaths per loop, +-1 mm
        dy = 0.0012 * math.sin(2 * math.pi * u)                           # slow weight shift fore/aft
        pitch = 0.8 * math.sin(2 * math.pi * u + 0.6)
        j, b = body_pose_joints(dy, dz, pitch)
        # look around: eyes lead, head follows (face timing below)
        pan = 0.0
        for (t0, t1, a0, a1) in [(0.6, 1.0, 0, 16), (1.0, 2.0, 16, 16), (2.0, 2.45, 16, -12), (2.45, 3.6, -12, -12), (3.6, 4.1, -12, 0)]:
            if t0 <= t <= t1: pan = a0 + (a1 - a0) * smooth((t - t0) / (t1 - t0))
        j["neck_pan"] = pan
        j["tail"] = 9 * math.sin(2 * math.pi * u * 2)
        return j, b
    c = kin_clip(f, n, True)
    c["face"] = [[0, "neutral"], [16, "curious"], [40, "neutral"], [52, "blink"], [55, "neutral"], [98, "blink"], [101, "neutral"], [130, "blink"], [133, "neutral"]]
    c["source"] = "kinematic loop (IK, feet fixed, sagittal body motion only); replayed in MuJoCo as a stability check"
    chk = sim_replay_check(c)
    c["metrics"] = {"sim_check": chk}
    checks_update("idle", chk)
    save("idle", c)


# ---------------- talk (kinematic loop, 5 s) ----------------
def talk():
    n = 151
    rng = np.random.default_rng(3)
    # syllable timeline: talk_a/talk_b alternate every 5-7 frames (0.17-0.23 s), with two short pauses
    face, i, st = [[0, "talk_a"]], 0, 0
    pauses = [(62, 72), (118, 126)]
    while i < n - 6:
        i += int(rng.integers(5, 8))
        if any(a <= i < b for a, b in pauses):
            face.append([i, "neutral"]); i = [b for a, b in pauses if a <= i < b][0]; face.append([i, "talk_a"]); st = 0; continue
        st ^= 1
        face.append([i, "talk_b" if st else "talk_a"])
    face = [f for f in face if f[0] < n]
    face.insert(len([f for f in face if f[0] <= 64]), [65, "blink"])
    face.sort(key=lambda x: x[0])
    def f(t):
        u = t / 5.0
        nod = 1.6 * math.sin(2 * math.pi * 6 * u) * (0.6 + 0.4 * math.sin(2 * math.pi * u))   # small nods via front legs
        dz = 0.0006 * math.sin(2 * math.pi * 6 * u + 1.0)
        j, b = body_pose_joints(0.0, dz, nod)
        pan = 0.0
        for (t0, t1, a0, a1) in [(0.0, 0.5, 0, 10), (0.5, 1.9, 10, 10), (1.9, 2.3, 10, -8), (2.3, 3.9, -8, -8), (3.9, 4.5, -8, 0)]:
            if t0 <= t <= t1: pan = a0 + (a1 - a0) * smooth((t - t0) / (t1 - t0))
        j["neck_pan"] = pan + 2.0 * math.sin(2 * math.pi * 10 * u)
        j["tail"] = 14 * math.sin(2 * math.pi * 2 * u)
        return j, b
    c = kin_clip(f, n, True)
    # loop-safe: last face equals first
    c["face"] = face
    c["source"] = "kinematic loop (IK, feet fixed): eyes pulse talk_a/talk_b every 0.17-0.23 s (mouth is printed, static); replayed in MuJoCo as a stability check"
    chk = sim_replay_check(c)
    c["metrics"] = {"sim_check": chk, "face_switch_s": "0.17-0.23"}
    checks_update("talk", chk)
    save("talk", c)


# ---------------- physically simulated clips ----------------
def new_sim(mu=MU, ears="rigid"):
    s = T.Sim(T.build(mu=mu, ears=ears))
    s.set_pose(T.rest_pose()); s.drop_to_floor()
    s.record = False; s.hold(T.rest_pose(), 0.4); s.record = True
    s.frames = []; s.k = 0; s.t_rec = None
    return s


def walk():
    p = json.load(open(os.path.join(OUT, "gait_best_trot_calm.json")))["p"]
    s = new_sim()
    s.face("neutral")
    s.hold(T.rest_pose(), 0.4)
    s.face("determined")
    rf = G.rest_feet()
    t0 = s.d.time; dur = 6.3; warm = 0.6
    blink_at = {int(2.3 * 30): "blink", int(2.3 * 30) + 3: "determined", int(4.9 * 30): "blink", int(4.9 * 30) + 3: "determined"}
    y_meas = []
    L = G.Leveler(0.5, 1.5)
    while s.d.time - t0 < dur:
        t = s.d.time - t0
        ramp = min(1.0, t / warm)
        if t > dur - 0.6: ramp = max(0.0, (dur - t) / 0.6)
        tg = G.leg_targets(p, t, rf, ramp, L(s, T.DT))
        tg["tail"] = 10 * math.sin(2 * math.pi * t / p["period"] / 2)  # tail sways at half step frequency
        tg["neck_pan"] = 3 * math.sin(2 * math.pi * t / p["period"] / 2)
        fi = len(s.frames)
        if fi in blink_at and (not s.face_events or s.face_events[-1][0] != fi): s.face(blink_at[fi])
        s.step(tg)
        if warm + p["period"] <= t <= dur - 0.6: y_meas.append((s.d.time, s.d.qpos[1]))
    s.face("neutral")
    s.hold(T.rest_pose(), 0.6)
    (ta, ya), (tb, yb) = y_meas[0], y_meas[-1]
    v = -(yb - ya) / (tb - ta) * 100
    total = -(s.d.qpos[1]) * 100
    m = {"speed_cm_s": round(float(v), 2), "distance_cm": round(float(total), 1), "gait": "trot + IMU levelling", "period_s": round(p["period"], 3),
         "stride_mm": round(p["stride"] * 1000, 1), "step_height_mm": round(p["height"] * 1000, 1), "peak_servo_torque_Nm": round(s.peak_tau, 3)}
    c = s.clip(loop=False, source=SRC + "; trot from IK foot paths + IMU levelling loop (PI on roll/pitch -> foot heights)", metrics=m)
    save("walk", c)
    return m


def turn():
    p = json.load(open(os.path.join(OUT, "gait_best_trot_calm.json")))["p"]
    p.update(period=0.42, height=0.0053, turn=0.022, fwd=0.0)
    s = new_sim()
    s.face("neutral")
    s.hold(T.rest_pose(), 0.3)
    s.face("curious")
    rf = G.rest_feet()
    y0 = G.yaw(s); t0 = s.d.time; dur = 4.4; warm = 0.5
    s.hold(dict(T.rest_pose(), neck_pan=22), 0.25)      # eyes + head lead the turn (+pan = face to the robot's left)
    t0 = s.d.time
    while s.d.time - t0 < dur:          # no levelling loop here: it costs ~40 % of the yaw rate in place
        t = s.d.time - t0
        ramp = min(1.0, t / warm)
        if t > dur - 0.5: ramp = max(0.0, (dur - t) / 0.5)
        tg = G.leg_targets(p, t, rf, ramp)
        tg["neck_pan"] = 22; tg["tail"] = -15 * ramp
        if abs(len(s.frames) - 75) < 1 and s.face_events[-1][1] != "blink": s.face("blink")
        if abs(len(s.frames) - 78) < 1 and s.face_events[-1][1] == "blink": s.face("curious")
        s.step(tg)
    s.face("neutral")
    s.hold(T.rest_pose(), 0.5)
    yw = [2 * math.atan2(b[6], b[3]) for b in s.frames and [f["base"] for f in s.frames]]
    dyaw = math.degrees(float(np.unwrap(np.array(yw))[-1] - np.unwrap(np.array(yw))[0]))
    drift = float(np.linalg.norm(s.d.qpos[0:2])) * 1000
    m = {"yaw_deg": round(dyaw, 1), "yaw_rate_deg_s": round(dyaw / dur, 1), "centre_drift_mm": round(drift, 1), "direction": "left (CCW from above)",
         "gait": "trot in place, differential stride ±11 mm, period 0.42 s, open loop", "peak_servo_torque_Nm": round(s.peak_tau, 3)}
    c = s.clip(loop=False, source=SRC + "; turn in place (left legs step back, right legs forward)", metrics=m)
    save("turn", c)
    return m


def happy():
    """Signature: fast tail wag + play-bow wiggle + bounce, happy/love eyes. Physically simulated."""
    s = new_sim()
    s.face("happy")
    rest = T.rest_pose()
    t0 = s.d.time; dur = 4.0
    while s.d.time - t0 < dur:
        t = s.d.time - t0
        # play bow (front down, rear up) 0.3-1.4 s, then upright bounces 1.6-3.4 s
        bow = smooth((t - 0.2) / 0.35) * (1 - smooth((t - 1.3) / 0.35))
        bounce = 0.0
        if 1.6 < t < 3.4: bounce = 0.0035 * (0.5 - 0.5 * math.cos(2 * math.pi * (t - 1.6) / 0.45))
        j, _ = body_pose_joints(-0.004 * bow, -0.010 * bow - bounce, 9.0 * bow)
        wag_amp = 45 * smooth((t - 0.1) / 0.3) * (1 - smooth((t - 3.5) / 0.4))
        j["tail"] = wag_amp * math.sin(2 * math.pi * 2.0 * t)
        j["neck_pan"] = (14 * math.sin(2 * math.pi * 0.9 * t)) * (1 - smooth((t - 3.3) / 0.5))
        fi = len(s.frames)
        if fi == 45: s.face("love")
        if fi == 78: s.face("happy")
        if fi == 102: s.face("blink")
        if fi == 105: s.face("happy")
        s.step(j)
    s.hold(rest, 0.3)
    m = {"tail_wag_hz": 2.0, "tail_wag_cmd_deg": 45, "peak_servo_torque_Nm": round(s.peak_tau, 3), "min_up": None}
    c = s.clip(loop=False, source=SRC + "; tail wag + play bow + bounce", metrics=m)
    ups = [quat_up(f) for f in c["base"]]; c["metrics"]["min_up"] = round(min(ups), 3)
    save("happy", c)
    return c["metrics"]


def quat_up(b):
    w, x, y, z = b[3:]
    return 1 - 2 * (x * x + y * y)


def sleep():
    """Settle down onto the belly, tail curls to the side, head turns, eyes close. Physically simulated."""
    s = new_sim()
    s.face("neutral")
    rest = T.rest_pose()
    lie = {"hip_fl": 70, "knee_fl": -135, "hip_fr": 70, "knee_fr": -135,
           "hip_hl": -48, "knee_hl": 130, "hip_hr": -48, "knee_hr": 130}
    t0 = s.d.time
    s.hold(rest, 0.3)
    s.face("sleepy")
    # crouch first with the feet still planted (IK), then fold
    for i in range(int(0.9 / T.DT)):
        u = smooth(i * T.DT / 0.9)
        j, _ = body_pose_joints(0.0, -0.022 * u, 0.0)
        j["neck_pan"] = 0; j["tail"] = 0
        s.step(j, slew=math.radians(200))
    s.face("blink"); s.hold(j, 0.1); s.face("sleepy")
    j2 = dict(lie); j2["neck_pan"] = 18; j2["tail"] = 70
    s.hold(j2, 1.2, slew=math.radians(150))
    s.face("blink"); s.hold(j2, 0.12); s.face("sleepy"); s.hold(j2, 0.5)
    s.face("sleep")
    s.hold(j2, 0.9)
    up = float(s.up()[2][2])
    m = {"final_body_height_mm": round(float(s.d.qpos[2]) * 1000, 1), "min_up_end": round(up, 3), "peak_servo_torque_Nm": round(s.peak_tau, 3)}
    c = s.clip(loop=False, source=SRC + "; lie down on the belly, tail curled to the side", metrics=m)
    save("sleep", c)
    return m


def fall_recover(push=(0.0, 9.0), mu=MU, name="fall_recover"):
    """Standing -> finger flick (angular-velocity kick, body frame [wx, wy] rad/s) -> topples -> lies still ->
    IMU-triggered closed-loop recovery (recover2: concept back sequence / re-tuned side sequence, mirrored retries)
    -> stands -> happy. Everything after the kick is the MuJoCo result."""
    import recover2 as R2
    s = new_sim(mu=mu)
    s.face("neutral")
    s.hold(T.rest_pose(), 0.5)
    s.face("blink"); s.hold(T.rest_pose(), 0.1); s.face("neutral"); s.hold(T.rest_pose(), 0.3)
    t_push = s.d.time
    s.d.qvel[3:6] = s.d.xmat[s.bid].reshape(3, 3) @ np.array([push[0], push[1], 0.0])
    s.face("surprised")
    s.hold(T.rest_pose(), 0.9)
    s.face("sad")
    s.hold(T.rest_pose(), 0.5)
    state0 = R2.classify(s)[0]
    log = []
    def on_kf(att, i, n):
        if i == 0: s.face("determined")
        if i == -1: s.face("neutral")
    ok, att = R2.recover(s, 4, log=log, on_kf=on_kf)
    if ok:
        s.face("happy"); s.hold(T.rest_pose(), 0.5)
        s.face("blink"); s.hold(T.rest_pose(), 0.1); s.face("happy"); s.hold(T.rest_pose(), 0.4)
    else:
        s.face("sad"); s.hold(T.rest_pose(), 1.0)   # firmware: give up after 4 tries and ask for help (chirp + sad eyes)
    tr0 = s.frames[0]["t"]
    for e in log: e["t"] = round(e["t"] - tr0, 2)
    t_push -= tr0
    m = {"push_body_rad_s": list(push), "landed_on": state0, "recovered": bool(ok), "attempts": att if ok else -1,
         "attempt_log": log, "t_push_s": round(t_push, 2), "mu": mu, "peak_servo_torque_Nm": round(s.peak_tau, 3),
         "pan_gear_peak_Nm": round(s.peak_pan_gear, 3), "pan_overshoot_deg": round(max(0.0, s.max_pan_overshoot), 2),
         "note": "neck_pan may exceed its ±40° range by the overshoot above when an impact back-drives the head; rig.js clamps the display to ±40°."}
    c = s.clip(loop=False, source=SRC.replace("μ=0.6", f"μ={mu}") + "; kick at t_push, then closed-loop IMU recovery (sim/recover2.py)", metrics=m)
    save(name, c)
    return m


def fall_recover_back(roll=180.0, pitch=0.0, mu=MU, name="fall_recover_back"):
    """The hard case: lying on its BACK. Released upside down 15 mm above the desk (as if a hand turned it over and
    let go; the same start as the roll-180 drop test), lies still, then the IMU-triggered closed-loop recovery
    (recover2: concept back sequence, mirrored on every 2nd try, up to 4 tries). Everything is the MuJoCo result."""
    import recover2 as R2
    s = T.Sim(T.build(mu=mu))
    q = R.quat_roll_pitch(roll, pitch)
    s.set_pose(R.stand(), base=(0, 0, 0.0, *q)); s.drop_to_floor(); s.d.qpos[2] += 0.015
    s.face("surprised")
    s.hold(R.stand(), 0.6)
    s.face("sad")
    s.hold(R.stand(), 0.6)
    state0 = R2.classify(s)[0]
    log = []
    def on_kf(att, i, n):
        if i == 0: s.face("determined")
        if i == -1: s.face("neutral")
    ok, att = R2.recover(s, 4, log=log, on_kf=on_kf)
    if ok:
        s.face("happy"); s.hold(T.rest_pose(), 0.5)
        s.face("blink"); s.hold(T.rest_pose(), 0.1); s.face("happy"); s.hold(T.rest_pose(), 0.4)
    else:
        s.face("sad"); s.hold(T.rest_pose(), 1.5)
    tr0 = s.frames[0]["t"]
    for e in log: e["t"] = round(e["t"] - tr0, 2)
    m = {"start": f"released upside down (roll {roll}°, pitch {pitch}°) 15 mm above the desk", "landed_on": state0,
         "recovered": bool(ok), "attempts": att if ok else -1, "attempt_log": log, "mu": mu,
         "t_standing_s": round(s.frames[-1]["t"] - tr0 - (1.0 if ok else 1.5), 2),
         "peak_servo_torque_Nm": round(s.peak_tau, 3), "pan_gear_peak_Nm": round(s.peak_pan_gear, 3),
         "pan_overshoot_deg": round(max(0.0, s.max_pan_overshoot), 2), "hip_f_clamp_steps": s.n_hip_clamped}
    c = s.clip(loop=False, source=SRC.replace("μ=0.6", f"μ={mu}") + "; released on its back, then closed-loop IMU recovery (sim/recover2.py)", metrics=m)
    save(name, c)
    return m


if __name__ == "__main__":
    names = sys.argv[1:] or ["idle", "talk", "walk", "turn", "happy", "sleep"]
    for nm in names:
        r = globals()[nm]()
        if r: print(nm, r)
