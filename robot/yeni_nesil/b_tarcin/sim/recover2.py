#!/usr/bin/env python3
"""Tarcin self-righting, closed loop on the IMU (OpenCat 'rc' style, the concept's tail-lever + leg-kick strategy):
  1. wait until the body is still; if up_z > 0.85 it is standing -> done
  2. classify from the IMU gravity vector: on a SIDE (|x_z| > 0.5) or on the BACK
  3. play the matching keyframe sequence, mirrored by the side that is down (legs 'd' = down side, 'u' = up side,
     tail and pan signs follow the down side):
       BACK: the concept's sequence (concept_B/sim/out/best_seq_13.json, unchanged)
       SIDE: re-tuned on this package model (rc_side.json) - the concept sequence fails from the side here
  4. stand pose 1.3 s, re-check; retry up to 4 times, mirroring the move on every second attempt (OpenCat-style)
usage: recover2.py mu [side_seq.json]"""
import sys, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tarcin as T, recover as R
BACK = json.load(open(os.path.join(HERE, "rc_seq13.json")))["seq"]
SIDE_F = os.path.join(HERE, "rc_side.json")
SIDE = json.load(open(SIDE_F))["seq"] if os.path.exists(SIDE_F) else None
UP_OK = 0.85


def SERVO_MODEL():
    return dict(tau=T.TAU, vmax_deg_s=round(math.degrees(T.VMAX)), w0=T.W0, damping=round(T.damping()[0], 5), droop=T.DROOP,
                coupled_hip_limit=T.COUPLED, tau_pan=T.TAU_PAN)


def classify(s):
    x, y, z = s.up()
    if z[2] > UP_OK: return "up", 0
    if abs(x[2]) > 0.5: return "side", (1 if x[2] < 0 else -1)
    return "back", (1 if x[2] < 0 else -1)


PLAN = [(False, False), (True, False)]   # (mirror, use the other sequence) per attempt: OpenCat-style mirror on every 2nd try
# (tried: switching to the other sequence on tries 3-4 - no better, see out/dbg_rc_*.log)


MIRROR_SIDE = False   # on a side the IMU says unambiguously which side is down: mirroring there only rolls it the wrong way


def recover(s, tries=4, side_seq=None, log=None, on_kf=None, plan=None):
    side_seq = side_seq or SIDE
    plan = plan or PLAN
    for att in range(tries):
        kind, down = classify(s)
        if kind == "up": return True, att
        mirror, other = plan[att % len(plan)]
        if mirror and (kind == "back" or MIRROR_SIDE): down = -down
        seq = side_seq if (kind == "side") != other else BACK
        if log is not None: log.append(dict(t=round(s.d.time, 2), attempt=att + 1, state=kind, down=down))
        for i, kf in enumerate(seq):
            if on_kf: on_kf(att, i, len(seq))
            s.hold(R.kf_target(kf, down), kf["T"])
        if on_kf: on_kf(att, -1, len(seq))
        s.hold(R.stand(), 0.8); s.hold(R.stand(), 0.5)
    return classify(s)[0] == "up", tries


def drop_case(xml, roll, pitch, tries=4, side_seq=None):
    s = T.Sim(xml, record=False)
    q = R.quat_roll_pitch(roll, pitch)
    s.set_pose(R.stand(), base=(0, 0, 0.0, *q)); s.drop_to_floor(); s.d.qpos[2] += 0.015
    s.hold(R.stand(), 1.2)
    st = classify(s)[0]
    ok, att = recover(s, tries, side_seq)
    return dict(roll=round(roll, 1), pitch=round(pitch, 1), settled=st, up_end=round(float(s.up()[2][2]), 2),
                ok=ok, attempts=att if ok else -1, t=round(s.d.time, 2), peak_tau=round(s.peak_tau, 3), **pan_log(s))


def pan_log(s):
    return dict(pan_gear_peak_Nm=round(s.peak_pan_gear, 3), pan_ext_peak_Nm=round(s.peak_pan_ext, 3),
                pan_overshoot_deg=round(max(0.0, s.max_pan_overshoot), 2), hip_f_clamp_steps=s.n_hip_clamped)


def per_state(cases):
    """first-try / total success per landing state (only cases that actually fell)"""
    out = {}
    for st in ("side", "back"):
        cs = [c for c in cases if c.get("settled") == st]
        if cs:
            out[st] = dict(n=len(cs), ok=sum(c["ok"] for c in cs), first_try=sum(c["ok"] and c["attempts"] == 1 for c in cs),
                           worst_attempts=max((c["attempts"] for c in cs if c["ok"]), default=-1),
                           worst_t_s=max((c.get("t", 0) for c in cs), default=0))
    return out


if __name__ == "__main__":
    mu = float(sys.argv[1])
    side = json.load(open(sys.argv[2]))["seq"] if len(sys.argv) > 2 else None
    tag = os.path.basename(sys.argv[2]).replace(".json", "") if len(sys.argv) > 2 else "rc_side"
    T.TAU_PAN = 0.07
    xml = T.build(mu=mu)
    cases = []
    for r, p in R.orients():
        c = drop_case(xml, r, p, side_seq=side); cases.append(c); print(c, flush=True)
    n = sum(c["ok"] for c in cases); first = sum(c["ok"] and c["attempts"] <= 1 for c in cases)
    res = dict(mu=mu, mu_paw=round(1.5 * mu, 2), side_seq=tag, servo_model=SERVO_MODEL(), success=f"{n}/{len(cases)}", first_try=f"{first}/{len(cases)}",
               per_state=per_state(cases), pan_gear_peak_Nm=max(c["pan_gear_peak_Nm"] for c in cases),
               pan_overshoot_max_deg=max(c["pan_overshoot_deg"] for c in cases), cases=cases)
    print("RESULT", mu, tag, res["success"], "first", res["first_try"], flush=True)
    json.dump(res, open(os.path.join(HERE, "out", f"rec2_mu{mu}_{tag}.json"), "w"), indent=1)
