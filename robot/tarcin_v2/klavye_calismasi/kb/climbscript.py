#!/usr/bin/env python3
"""Scripted step-up for the K2 front edge (stretch goal). Uses the ToF idea: the robot trots up to the edge, stops
with the front paw tips ~4 mm from the case wall, then:
  1. shifts the body back (feet forward) and lifts BOTH front paws high and forward onto the rim/caps
     (the body tips forward onto them; with one front paw at a time the 3-leg stance is not stable)
  2. 'hind step-up' loop: trot with a large lift on the hind legs only (front legs keep a normal trot), body
     raised as far as the legs allow, so the hind paws can catch the rim.
Parameters are swept in __main__; reports how many paws got above the rim."""
import sys, os, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kbd, kbsim, climb, rgait, ctrl as C, tarcin as T, gait as G


def sm(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


class StepUp:
    def __init__(self, kb, run, front_up=0.034, front_fwd=0.024, back=0.012, hind_H=0.024, hind_spread=0.014, t_reach=0.8):
        self.kb, self.run = kb, run
        self.base = C.Baseline()
        self.rf = G.rest_feet()
        self.edge = kb.base[2] / 1000.0
        self.phase = 0; self.t1 = None
        self.fu, self.ff, self.bk, self.hH, self.hs, self.tr = front_up, front_fwd, back, hind_H, hind_spread, t_reach
        self.walk = rgait.Rough(dict(gait="trot", period=0.6, duty=0.55, stride=0.018, H=0.010, hh=hind_H / 0.010,
                                     fy=-0.004, hy=hind_spread, dz=-0.004, kh=0.6, lev_kp=0.0, lev_ki=0.0, apex_h=0.4))

    def __call__(self, t, s, run):
        if self.phase == 0:
            if run.paws()[:, 1].max() + 0.0125 > self.edge - 0.004:   # paw tip (sole centre + 12.5 mm) near the wall
                self.phase = 1; self.t1 = t
            else:
                return self.base(t, s, run)
        if self.phase == 1:
            u = t - self.t1
            a = sm(u / 0.4)                       # shift back
            b = sm((u - 0.4) / self.tr)           # lift front + reach
            c = sm((u - 0.4 - self.tr) / 0.5)     # put front paws down (lower until contact: target below the step)
            out = {"tail": 0.0, "neck_pan": 0.0}
            for leg in T.LEGS:
                y, z = self.rf[leg]
                y -= self.bk * a
                if leg[0] == "f":
                    y -= self.ff * b
                    z += self.fu * b - (self.fu - 0.020) * c
                h, k = T.ik(leg, y, z)
                out["hip_" + leg] = h; out["knee_" + leg] = k
            if u > 0.4 + self.tr + 0.8:
                self.phase = 2; self.t2 = t
            return out
        return self.walk(t - self.t2, s, run)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    grid = [dict(), dict(front_up=0.040, front_fwd=0.030), dict(hind_H=0.030, hind_spread=0.018), dict(back=0.018, front_up=0.038)]
    for gp in grid:
        for sd in range(n):
            kb, run, zmin, ygoal = climb.setup("K2", sd, 0.4)
            c = StepUp(kb, run, **gp)
            o = climb.climb_go(run, c, zmin, ygoal, t_max=25)
            print(gp, sd, round(kb.h0, 1), o, flush=True)
