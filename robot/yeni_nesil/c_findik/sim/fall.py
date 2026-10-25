"""Fall + self-righting experiments for Findik (concept C2 'tuck & roll').

Firmware logic simulated (only IMU gravity vector + servo commands, like the ESP32 would have):
  STAND    : legs 22 deg.  mode "concept" (the concept's rule): tilt from upright > 60 deg for 0.3 s -> FALLEN
             (in practice this fires while the egg is still rolling).
             mode "settled": additionally wait until the gyro is still (< 40 deg/s for 0.2 s).
             mode "reflex": fire immediately at > 50 deg (tested as a firmware improvement).
             mode "hybrid": immediate tuck at > 50 deg only when the SIDE component dominates; fore/aft
             tilts use the concept rule (recommended firmware).
  Paw-catch reflex (concept): a fore/aft tilt > 15 deg swings that end's paws out to 60 deg.
  FALLEN   : classify by gravity in the body frame.
             side (|g_x| dominant): swing ONLY the lower-side legs out: front 80 deg, rear 118 deg (concept: 120; 118 is the shell-clear joint max),
                 at 300 deg/s; the egg rolls on its round belly.
                 when tilt < 45 deg (or 1.2 s passed) -> all legs back to 22 deg at 200 deg/s -> STAND.
                 if still > 60 deg 2.5 s after the tuck -> one retry, then HELP.
             face/back (|g_y| dominant): concept cannot recover -> HELP (rocks the upper legs, sad eyes).
Disturbances: a 'finger' pushes at the top of the head (95 mm above the body origin) in a horizontal
direction, at a controlled tilt speed, and lets go at 40 deg (just past the 38 deg side tip angle) ; or the
robot is dropped from 30 mm in a given orientation.

usage: python3 -I fall.py            -> results/fall_matrix.json (all cases; CoM sweep 0-3.5 mm at mu 0.6, mu 0.4 rows; 3 processes)
       (fall_recover clip is written by clips.py using run_case())
"""
import json, math, os, sys
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation as Rot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim_lib import Robot, HIPS

HERE = os.path.dirname(os.path.abspath(__file__))


class Righting:
    def __init__(self, r, mode="concept", catch=True):
        self.mode = mode
        self.catch = catch
        self.caught = False
        self.r = r
        self.state = "STAND"
        self.t_state = 0.0
        self.t_over = None
        self.retries = 0
        self.side = 0
        self.events = []          # (frame, name)
        self.cmd = {j: 22.0 for j in HIPS}
        self.rate = {j: 300.0 for j in HIPS}
        self.rock = 0.0
        self.frame = 0
        self.t_still = 0.0

    def set(self, tgt, rate):
        for j, v in tgt.items():
            self.cmd[j] = v
            self.rate[j] = rate

    def ev(self, name):
        self.events.append((self.frame, name))

    def update(self, dt):
        r = self.r
        side, pitch, up = r.tilt()
        g = r.gravity_body()
        t = r.d.time
        self.t_state += dt
        rate = math.degrees(np.linalg.norm(r.d.qvel[3:6]))      # gyro magnitude
        self.t_still = self.t_still + dt if rate < 40 else 0.0
        if self.state == "STAND":
            if up > (50 if self.mode in ("reflex", "hybrid") else 60):
                self.t_over = self.t_over if self.t_over is not None else t
                if (self.mode == "concept" and t - self.t_over > 0.3) or \
                   (self.mode == "settled" and t - self.t_over > 0.3 and self.t_still > 0.2) or \
                   (self.mode == "reflex" and up > 50) or \
                   (self.mode == "hybrid" and abs(g[0]) >= abs(g[1]) and up > 50) or \
                   (self.mode == "hybrid" and t - self.t_over > 0.3):
                    if abs(g[0]) >= abs(g[1]):
                        self.side = 1 if g[0] > 0 else -1          # +1: left (+X) side down
                        self.tuck()
                    else:
                        self.state = "HELP"; self.t_state = 0; self.ev("help")
            else:
                self.t_over = None
            # concept's paw-catch reflex: a fore/aft tip starting -> swing the paws on that end out to 60 deg
            if self.catch and up < 60:
                if abs(pitch) > 15 and abs(pitch) > abs(side) * 1.2:
                    if pitch < 0:
                        self.set({"hip_fl": 60.0, "hip_fr": 60.0}, 600.0)
                    else:
                        self.set({"hip_rl": 60.0, "hip_rr": 60.0}, 600.0)
                    if not self.caught:
                        self.caught = True; self.ev("catch")
                elif self.caught and up < 6:
                    self.set({j: 22.0 for j in HIPS}, 150.0)
                    self.caught = False
        elif self.state == "TUCK":
            if up < 45 or self.t_state > 1.2:
                if up < 60:
                    self.set({j: 22.0 for j in HIPS}, 200.0)
                    self.state = "RISE"; self.t_state = 0; self.ev("rise")
                elif self.t_state > 2.5:
                    if self.retries < 1:
                        self.retries += 1
                        self.set({j: 22.0 for j in HIPS}, 300.0)
                        self.state = "RETRY"; self.t_state = 0; self.ev("retry")
                    else:
                        self.state = "HELP"; self.t_state = 0; self.ev("help")
        elif self.state == "RETRY":
            if self.t_state > 0.6 and self.t_still > 0.2:
                if abs(g[0]) >= abs(g[1]):
                    self.side = 1 if g[0] > 0 else -1
                    self.tuck()
                else:
                    self.state = "HELP"; self.t_state = 0; self.ev("help")
        elif self.state == "RISE":
            if self.t_state > 0.6:
                if up < 12:
                    self.state = "DONE"; self.ev("done")
                elif up > 60:
                    self.state = "STAND"; self.t_over = None
        elif self.state == "HELP":
            if up < 15 and self.t_state > 0.5:
                self.set({j: 22.0 for j in HIPS}, 200.0)
                self.state = "RISE"; self.t_state = 0; self.ev("rise")
            # rock the upper legs slowly (+-) to say "help me", as the concept describes
            ph = math.sin(2 * math.pi * 0.8 * self.t_state)
            self.set({"hip_fl": 22 + 40 * max(0, ph), "hip_fr": 22 + 40 * max(0, ph),
                      "hip_rl": 22 + 40 * max(0, -ph), "hip_rr": 22 + 40 * max(0, -ph)}, 200.0)
        # slew the servo targets (firmware ramps the PWM command)
        for j in HIPS:
            cur = r.target[j]
            step = self.rate[j] * dt
            r.target[j] = cur + max(-step, min(step, self.cmd[j] - cur))

    def tuck(self):
        lo = ("fl", "rl") if self.side > 0 else ("fr", "rr")
        tgt = {f"hip_{lo[0]}": 80.0, f"hip_{lo[1]}": 118.0}     # rear 118 = joint max (120 grazes the cap)
        self.set(tgt, 300.0)
        self.state = "TUCK"; self.t_state = 0; self.ev("tuck")


def run_case(case, mu=0.6, com_dz=0.0, record=True, t_end=None, mode="concept", catch=True, lead_s=0.6, tail_s=1.0, help_s=2.5):
    """case: {"kind":"push","dir_deg":0,"speed":30} (0 = push toward +X = robot's left falls down)
             {"kind":"drop","side":84,"pitch":0}  ("pitch" + = back down)"""
    r = Robot(mu_floor=mu, com_dz_mm=com_dz)
    ctl = Righting(r, mode, catch)
    lead = lead_s
    if case["kind"] == "drop":
        R = Rot.from_euler("xy", [case.get("pitch", 0.0), case["side"]], degrees=True)
        q = R.as_quat()
        r.d.qpos[3:7] = [q[3], q[0], q[1], q[2]]
        r.d.qpos[2] = 0.0
        mujoco.mj_forward(r.m, r.d)
        # lift so the lowest geom is 30 mm above the floor
        low = min(r.d.geom_xpos[i][2] - (r.m.geom_rbound[i] if r.m.geom_type[i] != 0 else 0) for i in range(r.m.ngeom) if r.m.geom(i).name != "floor")
        r.d.qpos[2] = 0.03 - low
        # find true lowest point by stepping down quickly: use mj_forward contacts
        mujoco.mj_forward(r.m, r.d)
        lead = 0.0
    else:
        r.settle(0.4)
        ang = math.radians(case["dir_deg"])
        dvec = np.array([math.cos(ang), math.sin(ang), 0.0])
        st = {"on": False, "prev": 0.0, "tp": 0.0, "t0": None}
        wt = case.get("speed", 30.0)

        def ext(t):
            if st["t0"] is None or not st["on"]:
                return np.zeros(3), np.zeros(3)
            side, pitch, up = r.tilt()
            w = (up - st["prev"]) / max(1e-4, t - st["tp"]); st["prev"] = up; st["tp"] = t
            if up > case.get("release", 40.0) or t - st["t0"] > 4:
                st["on"] = False
            # velocity-servo finger: holds the tilt speed at wt deg/s, lets go at 40 deg
            F = min(4.0, max(0.0, 1.2 + 0.02 * (wt - w)))
            f = dvec * F
            com = r.d.subtree_com[r.bid]
            top = r.d.xpos[r.bid] + r.d.xmat[r.bid].reshape(3, 3) @ np.array([0, 0, 0.095])
            return f, np.cross(top - com, f)
        r.ext = ext
    fps = r.fps
    T = t_end or 12.0
    n = int(T * fps)
    push_frame = int(lead * fps)
    landing = None
    max_up = 0.0
    for i in range(n):
        ctl.frame = i
        if case["kind"] == "push" and i == push_frame:
            st["on"] = True; st["t0"] = r.d.time; ctl.ev("push")
        # controller at 100 Hz inside the frame
        if record:
            r.record()
        for k in range(r.substeps):
            if k % 10 == 0:
                ctl.update(0.01)
            r._control()
            if r.ext is not None:
                f, tq = r.ext(r.d.time)
                r.d.xfrc_applied[r.bid, :3] = f; r.d.xfrc_applied[r.bid, 3:] = tq
            mujoco.mj_step(r.m, r.d)
        r.d.xfrc_applied[r.bid] = 0
        side, pitch, up = r.tilt()
        max_up = max(max_up, up)
        if landing is None and ctl.state != "STAND":
            g = r.gravity_body()
            landing = {"side_deg": round(side, 1), "pitch_deg": round(pitch, 1), "up_deg": round(up, 1),
                       "g_body": [round(float(x), 3) for x in g]}
        if ctl.state == "DONE" and t_end is None:
            # stay a bit to prove it is stable
            for _ in range(int(tail_s * fps)):
                if record:
                    r.record()
                for k in range(r.substeps):
                    r._control(); mujoco.mj_step(r.m, r.d)
            break
        if ctl.state == "HELP" and ctl.t_state > help_s and t_end is None:
            break
    side, pitch, up = r.tilt()
    fell = landing is not None
    ok = ctl.state == "DONE" and up < 12
    res = {"case": case, "mode": mode, "catch_reflex": catch, "mu": mu, "com_dz_mm": com_dz, "fell": fell, "landing": landing,
           "final_state": ctl.state, "final_up_deg": round(up, 1), "recovered": ok,
           "retries": ctl.retries, "events": ctl.events, "peak_hip_torque_Nm": {j: round(v, 3) for j, v in r.peak_tau.items()},
           "t_recover_s": None}
    ev = dict((nm, f) for f, nm in ctl.events)
    if ok and "tuck" in ev:
        res["t_recover_s"] = round((ev["done"] - ev["tuck"]) / fps, 2)
    return r, ctl, res


CASES = []
for d in range(0, 360, 30):             # finger push at the head toward 12 directions, gentle and brisk
    for sp in (30, 90):                 # 0 = toward +X (robot tips onto its LEFT side), 90 = toward +Y (back)
        CASES.append({"kind": "push", "dir_deg": d, "speed": sp})
for s in (84, -84):                     # concept's quasi-static cases: lying on a side, pitched -15/0/+15
    for p in (-15, 0, 15):
        CASES.append({"kind": "drop", "side": s, "pitch": p})
for s, p in ((0, 95), (0, -95), (0, 180)):   # on the back, on the face, upside down
    CASES.append({"kind": "drop", "side": s, "pitch": p})

# CoM sensitivity: com_dz shifts the body CoM up (mm). +1.6 mm = the concept's own CoM estimate (47.9 mm vs the
# MJCF mass model); the sweep 0/1/1.6/2.5/3.5 is run for both firmwares at mu 0.6.
COM_SWEEP = (0.0, 1.0, 1.6, 2.5, 3.5)
CONFIGS = [("concept", 0.6, dz, True) for dz in COM_SWEEP] + [("hybrid", 0.6, dz, True) for dz in COM_SWEEP] + \
          [("concept", 0.4, 0.0, True), ("hybrid", 0.4, 0.0, True), ("hybrid", 0.4, 1.6, True), ("concept", 0.6, 0.0, False)]


def run_config(cfg):
    mode, mu, dz, catch = cfg
    rows = []
    for c in CASES:
        r, ctl, res = run_case(c, mu, dz, record=False, mode=mode, catch=catch)
        rows.append(res)
    pushes = [x for x in rows if x["case"]["kind"] == "push"]
    drops = [x for x in rows if x["case"]["kind"] == "drop"]
    side_drops = [x for x in drops if abs(x["case"]["side"]) > 45]
    bf_drops = [x for x in drops if abs(x["case"]["side"]) <= 45]
    fell = [x for x in pushes if x["fell"]]
    trec = [x["t_recover_s"] for x in rows if x["t_recover_s"]]
    summ = {"mode": mode, "mu": mu, "com_dz_mm": dz, "catch_reflex": catch,
            "pushes": len(pushes), "pushes_no_fall_or_caught": len(pushes) - len(fell),
            "pushes_fell": len(fell), "pushes_fell_recovered": sum(x["recovered"] for x in fell),
            "pushes_failed_dirs": [(x["case"]["dir_deg"], x["case"]["speed"]) for x in fell if not x["recovered"]],
            "side_drops_recovered": f'{sum(x["recovered"] for x in side_drops)}/{len(side_drops)}',
            "back_face_upsidedown_drops_recovered": f'{sum(x["recovered"] for x in bf_drops)}/{len(bf_drops)}',
            "t_recover_s_median": float(np.median(trec)) if trec else None,
            "peak_hip_torque_Nm": max(max(x["peak_hip_torque_Nm"].values()) for x in rows)}
    print(json.dumps(summ), flush=True)
    return summ, rows


if __name__ == "__main__":
    from multiprocessing import Pool
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    nproc = int(os.environ.get("FALL_PROCS", "3"))
    with Pool(nproc) as pool:
        outs = pool.map(run_config, CONFIGS, chunksize=1)
    summary = [o[0] for o in outs]
    out = [r for o in outs for r in o[1]]
    curve = {mode: [[s["com_dz_mm"], s["pushes_fell_recovered"], s["pushes_fell"]] for s in summary
                    if s["mode"] == mode and s["mu"] == 0.6 and s["catch_reflex"]] for mode in ("concept", "hybrid")}
    json.dump({"summary": summary, "com_curve_mu06": curve, "runs": out},
              open(os.path.join(HERE, "results", "fall_matrix.json"), "w"), indent=1)
