"""Tosbi self-righting firmware, as it would run on the ESP32 at 50 Hz with only the MPU6050 (GY-521) accelerometer
(sim: the MJCF imu_acc sensor + 0.08 m/s^2 noise, tosbi.Sim.grav_body; no ideal orientation is read).

Concept A strategy (concept.md, "Kendi kendine dogrulma"):
  * both shell faces are 'up'. If gravity says face B is up, mirror knees (b -> -b), neck (t -> -t),
    rotate the display (faces *_inv). The knees swing ~160 deg through the flipper plane and the robot
    pushes up with all four legs on the other face (FLIP-THROUGH).
  * side / nose / tail landings: the LOWER legs (closest to the floor) kick the body onto either face (EDGE KICK).
  * if not upright after the time budget: 'ask for help' (sad face, legs tucked).
"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tosbi import LEGS, stand_pose, smooth

HUB = {"fl": (30.66, -25.77), "fr": (-30.66, -25.77), "rl": (30.66, 25.77), "rr": (-30.66, 25.77)}
DIR0 = {"fl": -35.0, "fr": 215.0, "rl": 35.0, "rr": 145.0}
HIPSIGN = {"fl": -1, "fr": 1, "rl": -1, "rr": 1}   # hip axis z-sign: world yaw of leg = DIR0 + HIPSIGN*hip


class Recover:
    def __init__(self, give_up=9.0, kick_period=0.9, slew=360.0):
        self.mode = "stand"; self.sign = 1; self.t_mode = 0.0; self.t0 = None
        self.give_up = give_up; self.kick_period = kick_period; self.slew = slew
        self.g = None; self.cmd = None; self.log = []; self.face = "neutral"; self.done_t = None
        self.kick_dir = 1; self.kicks = 0; self.off_since = None

    def _set(self, sim, t, mode):
        if mode != self.mode:
            self.log.append((round(t, 2), mode)); self.mode = mode; self.t_mode = t
            if mode != "stand": self.done_t = None

    def __call__(self, sim, t):
        if self.t0 is None: self.t0 = t
        if self.cmd is None: self.cmd = dict(sim.cmd)
        gb = sim.grav_body()                                  # accelerometer (gravity direction in body frame)
        # only trust the accelerometer as a tilt sensor while |a| is near 1 g (shoves / impacts / free fall are ignored),
        # then IIR low-pass like firmware
        near_1g = abs(getattr(sim, "acc_norm", 9.81) - 9.81) < 2.5
        if self.g is None: self.g = gb
        elif near_1g: self.g = 0.75 * self.g + 0.25 * gb
        g = self.g / np.linalg.norm(self.g)
        u = -g[2]                                             # +1: face A up, -1: face B up
        tgt = None
        # hysteresis: a face counts once |u| > 0.82 (tilt < 35 deg); we only leave it again below 0.6 (53 deg)
        on_face = abs(u) > (0.6 if self.mode in ("stand", "settle", "flip_through") else 0.82)
        held = False
        # debounce: leaving a face must persist 0.2 s before the firmware starts kicking (one noisy sample is not a fall)
        if on_face: self.off_since = None
        elif self.mode in ("stand", "settle", "flip_through"):
            self.off_since = t if self.off_since is None else self.off_since
            if t - self.off_since < 0.2: on_face = True; held = True
        if on_face:
            s = self.sign if held else (1 if u > 0 else -1)
            if s != self.sign:
                self.sign = s; self._set(sim, t, "flip_through")
            elif self.mode not in ("flip_through", "stand"):
                self._set(sim, t, "settle")
            tgt = stand_pose(s)
            if self.mode == "flip_through":
                self.face = "determined_inv" if s < 0 else "determined"
                cur_k = np.mean([self.cmd[f"knee_{l}"] for l in LEGS]) * s
                if cur_k > 75 and t - self.t_mode > 0.4: self._set(sim, t, "stand")
            elif self.mode == "settle":
                self.face = "determined_inv" if s < 0 else "determined"
                if t - self.t_mode > 0.6: self._set(sim, t, "stand")
            else:
                self.face = "neutral_inv" if s < 0 else "neutral"
            if self.mode == "stand" and self.done_t is None and abs(u) > 0.94 and t - self.t0 > 0.3:
                self.done_t = t
        else:                                                 # on a side, nose or tail
            if t - self.t0 > self.give_up:
                self._set(sim, t, "ask_help"); self.face = "sad"
                tgt = {**{f"hip_{l}": 0 for l in LEGS}, **{f"knee_{l}": 0 for l in LEGS}, "neck": 0}
            else:
                if self.mode != "edge_kick": self._set(sim, t, "edge_kick"); self.kicks = 0
                pref = 1 if u >= 0 else -1                    # roll toward the nearer face
                self.face = "determined" if pref > 0 else "determined_inv"
                ph = ((t - self.t_mode) / self.kick_period) % 1.0
                ncyc = int((t - self.t_mode) / self.kick_period)
                if ncyc >= 3 and abs(u) < 0.3: pref = -pref if (ncyc // 3) % 2 else pref   # stuck: try the other face
                tgt = {"neck": 0.0}
                for l in LEGS:
                    hx, hy = HUB[l]
                    hd = np.array([hx, hy, 0.0]); hd /= np.linalg.norm(hd)
                    low = float(hd @ g)                       # >0: this hip is on the floor side
                    # yaw the leg toward the floor (within limits)
                    gxy = np.array([g[0], g[1]])
                    if low > 0.2 and np.linalg.norm(gxy) > 0.2:
                        want = math.degrees(math.atan2(gxy[1], gxy[0]))
                        dyaw = (want - DIR0[l] + 180) % 360 - 180
                        hip = max(-20, min(14 if l in ("fl", "fr") else 20, dyaw / HIPSIGN[l]))
                    else:
                        hip = 0.0
                    tgt[f"hip_{l}"] = hip
                    if low > 0.2:                             # lower legs: kick 0 -> pref*85 and back
                        k = smooth(ph / 0.45) if ph < 0.45 else 1 - smooth((ph - 0.45) / 0.55)
                        tgt[f"knee_{l}"] = pref * (85 * k)
                    else:                                     # upper legs: ready to land on face `pref`
                        tgt[f"knee_{l}"] = pref * 80
        sim.set_face(self.face)
        # firmware slew limit (deg per control tick) so the commanded path is smooth
        step = self.slew * 0.02
        for k, v in tgt.items():
            c = self.cmd.get(k, v)
            self.cmd[k] = c + max(-step, min(step, v - c))
        if self.mode == "flip_through":                      # knees sweep through 0 together (all four)
            pass
        return dict(self.cmd)
