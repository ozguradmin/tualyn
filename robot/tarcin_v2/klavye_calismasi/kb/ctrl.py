#!/usr/bin/env python3
"""Gait controllers for kbsim.Run.go(ctrl): ctrl(t, sim, run) -> joint targets (deg)."""
import sys, os, math, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(os.path.dirname(HERE), "pkg", "sim")
sys.path.insert(0, SIM)
import tarcin as T, gait as G

PKG_TROT = json.load(open(os.path.join(SIM, "out", "gait_best_trot_calm.json")))["p"]


class Baseline:
    """The package's walk clip exactly: trot (0.52 s, 20 mm stride, 5.3 mm lift) + IMU levelling (PI kp 0.5 ki 1.5),
    tail sway 10 deg and head pan 3 deg at half the step frequency, 0.6 s ramp. Open loop in heading."""
    def __init__(self, p=None, heading_hold=0.0):
        self.p = dict(p or PKG_TROT)
        self.L = G.Leveler(0.5, 1.5)
        self.rf = G.rest_feet()
        self.kh = heading_hold
        self.warm = 0.6

    def __call__(self, t, s, run):
        p = self.p
        ramp = min(1.0, t / self.warm)
        if self.kh:
            e = math.atan2(math.sin(run.yaw() - run.psi0), math.cos(run.yaw() - run.psi0))
            p = dict(p, fwd=1.0, turn=max(-0.008, min(0.008, -self.kh * e)))
        tg = G.leg_targets(p, t, self.rf, ramp, self.L(s, T.DT))
        tg["tail"] = 10 * math.sin(2 * math.pi * t / p["period"] / 2)
        tg["neck_pan"] = 3 * math.sin(2 * math.pi * t / p["period"] / 2)
        return tg
