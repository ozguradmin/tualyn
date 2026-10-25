#!/usr/bin/env python3
"""Self-righting for Tarcin = the concept's OpenCat-'rc'-style keyframe recovery (concept_B/sim/out/best_seq_13.json,
copied here as rc_seq13.json), run on the GLB-frame model (tarcin.py) with MG90S limits.
Roles: 'd' = legs on the side that is down, 'u' = legs on the side that is up; values (hip, knee) in deg.
Trigger: IMU up-vector (body Z) z-component < 0.85 after settling. Retries: up to 4, mirrored on every 2nd attempt
(OpenCat-style). Between attempts: back to stand pose 0.8 + 0.5 s (as in the concept's verify.py)."""
import sys, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tarcin as T
import mujoco

SEQ = json.load(open(os.path.join(HERE, "rc_seq13.json")))["seq"]
UP_OK = 0.85


def kf_target(kf, down):
    tg = {}
    for leg in T.LEGS:
        sx = 1 if leg[1] == "l" else -1          # l = +x  (= concept 'R')
        a, k = kf[("d" if sx == down else "u") + leg[0].upper()]
        tg["hip_" + leg] = a
        tg["knee_" + leg] = k
    tg["neck_pan"] = kf["pan"] * down
    tg["tail"] = kf.get("tail", 0.0) * down
    return tg


def stand():
    p = T.rest_pose(); return p


def recover(s, tries=4, on_attempt=None):
    """returns (ok, attempts_used). attempts_used = 0 if it was already upright."""
    for att in range(tries):
        x, y, z = s.up()
        if z[2] > UP_OK:
            return True, att
        down = 1 if x[2] < 0 else -1
        if att % 2 == 1:
            down = -down
        if on_attempt: on_attempt(att, down)
        for kf in SEQ:
            s.hold(kf_target(kf, down), kf["T"])
        s.hold(stand(), 0.8)
        s.hold(stand(), 0.5)
    return bool(s.up()[2][2] > UP_OK), tries


def quat_roll_pitch(roll, pitch):
    qy = np.zeros(4); mujoco.mju_axisAngle2Quat(qy, np.array([0, 1.0, 0]), math.radians(roll))
    qx = np.zeros(4); mujoco.mju_axisAngle2Quat(qx, np.array([1.0, 0, 0]), math.radians(pitch))
    qq = np.zeros(4); mujoco.mju_mulQuat(qq, qx, qy)
    return qq


def drop_case(xml, roll, pitch, tries=4, record=False):
    s = T.Sim(xml, record=record)
    q = quat_roll_pitch(roll, pitch)
    s.set_pose(stand(), base=(0, 0, 0.0, *q))
    s.drop_to_floor()
    s.d.qpos[2] += 0.015
    s.hold(stand(), 1.2)
    settled = round(float(s.up()[2][2]), 2)
    ok, att = recover(s, tries)
    return dict(roll=round(roll, 1), pitch=round(pitch, 1), settled_up=settled, ok=ok, attempts=att if ok else -1,
                t=round(s.d.time, 2), peak_tau=round(s.peak_tau, 3))


ORIENTS = None


def orients():
    rng = np.random.default_rng(7)   # the same 24 orientations as concept_B/sim/verify.py
    return [(90, 0), (-90, 0), (180, 0), (135, 0), (-135, 0), (90, 20), (-90, -20), (180, -15), (180, 15)] + \
           [(float(rng.uniform(-180, 180)), float(rng.uniform(-35, 35))) for _ in range(15)]


if __name__ == "__main__":
    variants = [a for a in sys.argv[1:] if not a.startswith("-")] or ["0.6:rigid"]
    allres = {}
    for v in variants:
        mu, ears = v.split(":")
        mu = float(mu)
        xml = T.build(mu=mu, ears=ears)
        cases = [drop_case(xml, r, p) for r, p in orients()]
        n_ok = sum(c["ok"] for c in cases)
        first = sum(c["ok"] and c["attempts"] <= 1 for c in cases)
        allres[v] = dict(mu=mu, mu_paw=round(1.5 * mu, 2), ears=ears, success=f"{n_ok}/{len(cases)}", first_try_or_upright=f"{first}/{len(cases)}",
                         peak_tau=max(c["peak_tau"] for c in cases), cases=cases)
        print(v, allres[v]["success"], "first-try", allres[v]["first_try_or_upright"], [c["attempts"] for c in cases], flush=True)
        json.dump(allres[v], open(os.path.join(HERE, "out", f"recovery_mu{mu}_{ears}.json"), "w"), indent=1)
