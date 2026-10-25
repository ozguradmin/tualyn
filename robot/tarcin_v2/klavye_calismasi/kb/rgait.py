#!/usr/bin/env python3
"""'Rough-terrain' gait for Tarcin on the same hardware (8 sagittal leg servos, MPU6500).

Foot paths (body frame, IK from tarcin.ik) with a box-shaped swing: lift straight up (fraction a of the swing),
carry forward at full height H, put down straight (fraction a), optionally pressing 'dip' below the nominal stance
height at the end of the swing so a paw that lands on a lower cap still takes load. Gaits:
  trot   diagonal pairs (fl+hr, fr+hl)
  walk   4-beat lateral sequence hl, fl, hr, fr (one leg at a time, duty >= 0.75)
  walkd  4-beat diagonal sequence hl, fr, hr, fl
Walk only: centre-of-mass sway synchronised with the swing leg: fore-aft body shift 'sway_y' and a body roll made by
leg-length difference 'sway_r' (m), away from the swing leg; head pan 'head_sway' (deg) toward the support side.
Closed loops (IMU only; the MPU6500 has no magnetometer, so yaw = integrated gyro z):
  - levelling: package Leveler (PI on roll/pitch -> per-leg foot heights), gains lev_kp, lev_ki, limit lev_lim
  - heading hold: differential stride (as the package's turn gait) -kh * yaw error, limited to +-hlim
  - slope crab: the heading set-point is biased uphill by kc * (terrain roll estimated from the levelling offsets)
"""
import sys, os, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "pkg", "sim"))
import tarcin as T, gait as G

PH = {
    "trot": {"fl": 0.0, "hr": 0.0, "fr": 0.5, "hl": 0.5},
    "walk": {"hl": 0.0, "fl": 0.25, "hr": 0.5, "fr": 0.75},
    "walkd": {"hl": 0.0, "fr": 0.25, "hr": 0.5, "fl": 0.75},
}

DEFAULT = dict(gait="trot", period=0.6, duty=0.55, stride=0.020, H=0.015, a=0.25, dz=0.0, shift=0.0, fy=0.0, hy=0.0,
               dip=0.0, sway_y=0.0, sway_r=0.0, head_sway=0.0, kh=0.5, hlim=0.008, kc=0.0, lev_kp=0.5, lev_ki=1.5,
               lev_lim=0.008, warm=0.8, tail=0.0, apex_f=0.5, apex_h=0.5, hh=1.0, hpow=1.0)


def sm(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


class Rough:
    def __init__(self, spec):
        p = dict(DEFAULT); p.update(spec or {})
        self.p = p
        self.rf = G.rest_feet()
        self.L = G.Leveler(p["lev_kp"], p["lev_ki"], p["lev_lim"])
        self.lev = {l: 0.0 for l in T.LEGS}
        self.roll_t = 0.0      # filtered terrain roll estimate (rad), + = left side (+x) higher
        self.warm = p["warm"]

    def foot(self, leg, ph, s, H, z0, y0):
        p = self.p
        duty, a, dip = p["duty"], p["a"], p["dip"]
        if ph < duty:                         # stance: foot moves back (+Y) relative to the body
            u = ph / duty
            return y0 - s / 2 + s * u, z0 - dip * (1 - sm(u / 0.15)) if dip else z0
        u = (ph - duty) / (1 - duty)
        if a <= 0.0:
            ap = p["apex_f"] if leg[0] == "f" else p["apex_h"]
            w = 0.5 * u / ap if u < ap else 0.5 + 0.5 * (u - ap) / (1 - ap)
            Hl = H * (1.0 if leg[0] == "f" else p["hh"])
            return (y0 + s / 2 - s * (0.5 - 0.5 * math.cos(math.pi * u)),
                    z0 + Hl * math.sin(math.pi * w) ** p["hpow"] - dip * sm((u - 0.7) / 0.3))
        if u < a:
            return y0 + s / 2, z0 + H * sm(u / a)
        if u < 1 - a:
            return y0 + s / 2 - s * sm((u - a) / (1 - 2 * a)), z0 + H
        w = (u - (1 - a)) / a
        return y0 - s / 2, z0 + H - (H + dip) * sm(w)

    def __call__(self, t, sim, run):
        p = self.p
        ramp = min(1.0, t / self.warm) if self.warm > 0 else 1.0
        lev = self.L(sim, T.DT)
        # terrain roll estimate: body roll + left/right levelling difference over the 46.6 mm track
        R = sim.d.xmat[sim.bid].reshape(3, 3)
        dl = (lev["fl"] + lev["hl"]) / 2 - (lev["fr"] + lev["hr"]) / 2
        roll = math.asin(max(-1, min(1, R[2, 0]))) + math.atan2(dl, 0.0466)   # >0: left side higher
        self.roll_t += min(1.0, T.DT / 0.5) * (roll - self.roll_t)
        crab = max(-0.6, min(0.6, p["kc"] * self.roll_t))
        if p.get("crab_deg"):           # fixed uphill crab once a cross-slope > 1.5 deg is sensed
            crab = math.copysign(math.radians(p["crab_deg"]), self.roll_t) * min(1.0, abs(self.roll_t) / math.radians(3.0)) if abs(self.roll_t) > math.radians(1.5) else 0.0
        # heading hold
        yaw = run.yaw() if run is not None else 0.0
        psi0 = run.psi0 if run is not None else 0.0
        e = math.atan2(math.sin(yaw - psi0 - crab), math.cos(yaw - psi0 - crab))
        turn = max(-p["hlim"], min(p["hlim"], -p["kh"] * e)) if p["kh"] else 0.0
        per = p["period"]
        cyc = t / per
        out = {}
        swing_leg, swing_u = None, 0.0
        for leg in T.LEGS:
            ph = (cyc + PH[p["gait"]][leg]) % 1.0
            if ph >= p["duty"]:
                swing_leg = leg if swing_leg is None else swing_leg
        # walk: COM sway away from the leg that is about to swing / swinging (smooth, periodic)
        dyb, droll = 0.0, 0.0
        if p["gait"] != "trot" and (p["sway_y"] or p["sway_r"]):
            # continuous sway: sum over legs of a bump centred on that leg's swing
            for leg in T.LEGS:
                ph = (cyc + PH[p["gait"]][leg]) % 1.0
                c = (1 + p["duty"]) / 2                 # middle of this leg's swing
                dph = (ph - c + 0.5) % 1.0 - 0.5
                w = max(0.0, math.cos(math.pi * dph / 0.5)) ** 2 if abs(dph) < 0.5 else 0.0
                fy = 1 if leg[0] == "f" else -1        # front leg swinging -> move body back (+Y)
                sx = 1 if leg[1] == "l" else -1        # left leg swinging -> roll right: raise left side
                dyb += p["sway_y"] * fy * w
                droll += p["sway_r"] * sx * w
        for leg in T.LEGS:
            y0, z0 = self.rf[leg]
            y0 += p["shift"] + (p["fy"] if leg[0] == "f" else p["hy"]) - dyb * ramp   # feet forward = body back
            z0 += p["dz"] + lev[leg]
            sx = 1 if leg[1] == "l" else -1
            z0 -= droll * sx * ramp / 2                 # raise the swing side (foot lower in body frame -> body up)
            side = sx
            s = p["stride"] * ramp - side * turn * ramp
            ph = (cyc + PH[p["gait"]][leg]) % 1.0
            y, z = self.foot(leg, ph, s, p["H"] * ramp, z0, y0)
            h, k = T.ik(leg, y, z)
            out["hip_" + leg] = h; out["knee_" + leg] = k
        out["tail"] = p["tail"] * math.sin(2 * math.pi * cyc / 2)
        out["neck_pan"] = 0.0
        if p["head_sway"] and p["gait"] != "trot":
            out["neck_pan"] = max(-40, min(40, -p["head_sway"] * droll / max(1e-9, p["sway_r"]))) if p["sway_r"] else 0.0
        return out
