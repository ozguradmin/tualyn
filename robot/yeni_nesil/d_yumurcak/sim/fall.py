#!/usr/bin/env python3
"""Fall + self-righting in MuJoCo, using the concept's manoeuvre (concept_D2/righting.py) as ESP32 firmware
would run it, with only the IMU (body orientation + gyro) as input:
  1. fall detected (tilt > 40 deg)          -> 'surprised' face, all knees fold to 164 (egg mode), yaws 0
  2. wait until the egg has rolled to rest  (|gyro| < 25 deg/s for 0.3 s)
  3. if tilt < 25 deg: rise on all 4 legs
  4. else: the two down-side legs yaw so their paw-swing plane contains the fall direction (within the real
     yaw range -20..72), then their knees sweep the paws 164 -> 0 at 60 deg/s ('determined' face);
     the paw tips lift the flank, the CoM passes over the haunch ball and the egg rolls upright
  5. rise on 4 legs (knees 164 -> 30 at 90 deg/s), 'happy' face
  6. if a sweep ends with the robot still on its side: fold again and retry with the mirrored choice
     (OpenCat 'rc' style; attempt 2 pushes with the next leg pair, attempt 3 with all down-side legs);
     after 3 failed attempts: 'sad' face = ask for help.
usage: python3 fall.py [mu ...]   -> out/fall_results_mu<mu>.json
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from rec import Rec

AZ = {"fl": 1, "fr": -1, "bl": -1, "br": 1}          # yaw axis z sign
SX = {"fl": 1, "fr": -1, "bl": 1, "br": -1}
SY = {"fl": -1, "fr": -1, "bl": 1, "br": 1}
YAW_LO, YAW_HI = -20.0, 72.0                          # real limits (knee > 70 -> yaw <= 72)
TUCK = 164.0
FOLD = {"knee": float(os.environ.get("FOLD_KNEE", "164")), "yaw": float(os.environ.get("FOLD_YAW", "0"))}


STRATEGY = os.environ.get("STRATEGY", "hybrid")
FOLD_B = {"knee": 150.0, "yaw": 40.0}      # robust: 145-160 / 33-47 all 7/7 on the hard cases (t_foldB.py)      # 'flank tuck': paws folded along the flanks, back/front of the egg clear


def fold_pose(attempt=0):
    """concept: always the egg-mode tuck (knees 164, yaws 0).
    hybrid: first fold = egg-mode tuck; re-folds after a failed push use the flank tuck, which stops the
    folded paw tips from propping the egg on its back/front"""
    f = FOLD_B if (STRATEGY == "hybrid" and attempt >= 1) else FOLD
    return {**{f"knee_{k}": f["knee"] for k in LEGS}, **{f"yaw_{k}": f["yaw"] for k in LEGS}}


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def pusher_yaw(k, want_deg):
    th = AZ[k] * wrap(want_deg - (0.0 if SX[k] > 0 else 180.0))
    if YAW_LO <= th <= YAW_HI:
        return th
    # nearest feasible bound (angular distance)
    return YAW_LO if abs(wrap(th - YAW_LO)) < abs(wrap(th - YAW_HI)) else YAW_HI


class Righter:
    def __init__(self, log):
        self.state = "stand"; self.ts = 0.0; self.attempt = 0; self.log = log
        self.quiet = 0.0; self.pushers = []; self.knee = TUCK; self.fell_at = None; self.done_at = None

    def go(self, sim, st):
        self.state = st; self.ts = sim.t
        self.log.append([round(sim.t, 3), st, round(sim.tilt(), 1)])

    def __call__(self, sim, t):
        if int(round(t / sim.dt)) % 10:             # 100 Hz control loop
            return
        tilt = sim.tilt()
        w = np.linalg.norm(sim.d.qvel[3:6]) * 57.3
        dt = 0.01
        st = self.state
        if st == "stand":
            if tilt > 40:
                self.fell_at = sim.t
                sim.set_face("surprised")
                sim.target({**fold_pose(), "head": 0})
                self.go(sim, "fold")
        elif st == "fold":
            self.quiet = self.quiet + dt if w < 25 else 0.0
            if (self.quiet > 0.3 and sim.t - self.ts > 0.6) or sim.t - self.ts > 3.0:
                self.go(sim, "assess")
        elif st == "assess":
            if tilt < 25:
                sim.set_face("determined"); self.go(sim, "rise")
                sim.slew = 90.0
                sim.target({**{f"knee_{k}": 30 for k in LEGS}, **{f"yaw_{k}": 0 for k in LEGS}})
                return
            self.attempt += 1
            if self.attempt > 3:
                sim.set_face("sad"); self.go(sim, "help"); return
            R = sim.d.xmat[sim.body].reshape(3, 3)
            g = R.T @ np.array([0, 0, -1.0])           # gravity in the body frame (IMU)
            h = np.array([g[0], g[1]]); h /= np.linalg.norm(h) + 1e-9
            score = {k: SX[k] * h[0] + SY[k] * h[1] for k in LEGS}
            order = sorted(LEGS, key=lambda k: -score[k])
            if self.attempt == 1:
                self.pushers = order[:2]
            elif self.attempt == 2:                     # mirrored: the next pair round the fall direction
                self.pushers = [order[0], order[2]]
            else:
                self.pushers = order[:3]
            want = math.degrees(math.atan2(h[1], h[0]))
            sim.set_face("determined")
            sim.target({**{f"yaw_{k}": pusher_yaw(k, want) for k in self.pushers}, **{f"knee_{k}": TUCK for k in self.pushers}})
            self.log.append([round(sim.t, 3), "pushers", self.pushers, [round(pusher_yaw(k, want), 1) for k in self.pushers], round(want, 1)])
            self.go(sim, "aim")
        elif st == "aim":
            if sim.t - self.ts > 0.35:
                self.knee = TUCK; sim.slew = 60.0; self.go(sim, "push")
        elif st == "push":
            self.knee = max(0.0, self.knee - 60.0 * dt)
            sim.target({f"knee_{k}": self.knee for k in self.pushers})
            if tilt < 22:
                sim.slew = 90.0
                sim.target({**{f"knee_{k}": 30 for k in LEGS}, **{f"yaw_{k}": 0 for k in LEGS}})
                self.go(sim, "rise")
            elif self.knee <= 0 and sim.t - self.ts > 3.0:
                sim.slew = 300.0
                sim.target(fold_pose(self.attempt))
                self.go(sim, "fold")
        elif st == "rise":
            if all(abs(sim.q(f"knee_{k}") - 30) < 4 for k in LEGS) and tilt < 10 and sim.t - self.ts > 0.5:
                sim.slew = 300.0; sim.set_face("happy"); self.done_at = sim.t; self.go(sim, "up")
            elif tilt > 40 and sim.t - self.ts > 0.3:   # fell again while rising
                sim.slew = 300.0; sim.set_face("surprised")
                sim.target(fold_pose(self.attempt))
                self.go(sim, "fold")


def push_force(sim, az_deg, F=4.0, dur=0.12, t0=0.6, zh=0.105):
    """horizontal shove of F newtons for dur s at height zh (m) on the head, towards azimuth az (0 = +X = robot's left)"""
    u = np.array([math.cos(math.radians(az_deg)), math.sin(math.radians(az_deg)), 0.0])
    def apply(s, t):
        s.d.xfrc_applied[:] = 0
        if t0 <= t < t0 + dur:
            p = s.d.xpos[s.body] + np.array([0, 0, zh])
            c = s.d.xipos[s.body]
            s.d.xfrc_applied[s.body, :3] = F * u
            s.d.xfrc_applied[s.body, 3:] = np.cross(p - c, F * u)
    return apply


AZS = [0, 45, 90, 135, 180, 225, 270, 315]
AZNAME = {0: "towards its left (+X)", 45: "back-left", 90: "backwards", 135: "back-right", 180: "towards its right (-X)",
          225: "front-right", 270: "forwards (face down)", 315: "front-left"}
CASES = {}
for a in AZS:
    CASES[f"nudge {AZNAME[a]}"] = ("push", a, 1.25)       # 1.25 x the smallest shove that tips it over
    CASES[f"shove {AZNAME[a]}"] = ("push", a, 2.0)        # 2 x
CASES["dropped upside down (2 cm)"] = ("place", [3.0, 178.0, 10.0], None)
CASES["placed on its back, legs out"] = ("place", [-92.0, 0.0, 5.0], None)
CASES["placed face down, legs out"] = ("place", [92.0, 0.0, -5.0], None)
CASES["placed on right side, legs out"] = ("place", [0.0, -95.0, 0.0], None)

_THR = {}


def tip_threshold(az, mu):
    """smallest 0.12 s shove (N, at head height) that tips the standing robot over (bisection)"""
    if (az, mu) in _THR:
        return _THR[(az, mu)]
    lo, hi = 0.5, 6.0
    for _ in range(7):
        F = 0.5 * (lo + hi)
        s = Sim(mu, 300.0); s.set_pose(REST); s.drop_to_floor(0.05)
        pf = push_force(s, az, F=F)
        s.step_time(2.0, lambda sm, t: pf(sm, t), record=False)
        if s.tilt() > 45: hi = F
        else: lo = F
    _THR[(az, mu)] = hi
    return hi


def quat_xyz(rx, ry, rz):
    q = np.zeros(4)
    mujoco.mju_euler2Quat(q, np.radians([rx, ry, rz]), "xyz")
    return q


def run_case(name, mu, T=14.0, keep=False):
    kind, v, mult = CASES[name]
    sim = Rec(mu, 300.0)
    F = None
    log = []
    ctl = Righter(log)
    if kind == "push":
        sim.set_pose(REST); sim.drop_to_floor(0.05)
        F = tip_threshold(v, mu) * mult
        pf = push_force(sim, v, F=F)
    else:
        q = quat_xyz(*v)
        sim.set_pose(REST, base=(0, 0, 200, *q)); sim.drop_to_floor(20.0 if v[1] > 150 else 1.0)
        pf = lambda s, t: None
    sim.begin()
    sim.set_face("neutral")

    def ctrl(s, t):
        pf(s, t); ctl(s, t)
        if ctl.state == "up" and s.t - ctl.ts > 0.8:
            pass
    sim.step_time(T, ctrl)
    res = dict(case=name, mu=mu, strategy=STRATEGY, push_N=F and round(F, 2), success=ctl.state == "up", attempts=ctl.attempt, fell=ctl.fell_at is not None or kind == "place",
               t_fall=ctl.fell_at, t_up=ctl.done_at, final_tilt=round(sim.tilt(), 1),
               max_knee_Nm=round(max(sim.max_tau[f"knee_{k}"] for k in LEGS), 3),
               max_yaw_Nm=round(max(sim.max_tau[f"yaw_{k}"] for k in LEGS), 3), max_pen_mm=round(sim.maxpen, 2), servo_at_clamp_s=round(sim.sat_s, 3), log=log)
    if keep:
        return res, sim
    return res


if __name__ == "__main__":
    from multiprocessing import Pool
    mus = [float(a) for a in sys.argv[1:]] or [0.6, 0.4]
    jobs = [(n, mu) for mu in mus for n in CASES]
    with Pool(int(os.environ.get("NPROC", "2"))) as P:
        R = P.starmap(run_case, jobs)
    for mu in mus:
        rr = [r for r in R if r["mu"] == mu]
        json.dump(rr, open(os.path.join(HERE, "out", f"fall_{STRATEGY}_mu{mu}.json"), "w"), indent=1)
        ok = sum(r["success"] for r in rr)
        print(f"mu={mu}: {ok}/{len(rr)} recovered")
        for r in rr:
            print("  %-32s %s att=%d t_up=%s tilt=%.1f knee=%.3f yaw=%.3f pen=%.2f" % (r["case"], "OK  " if r["success"] else "FAIL", r["attempts"], r["t_up"] and round(r["t_up"], 2), r["final_tilt"], r["max_knee_Nm"], r["max_yaw_Nm"], r["max_pen_mm"]))
