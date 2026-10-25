#!/usr/bin/env python3
"""Open-loop OpenCat-style gaits for Tarcin, generated from foot trajectories + leg IK, run in MuJoCo with the
MG90S servo model. Forward = -Y. Turning left (CCW seen from above) = +yaw."""
import math, sys, os, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tarcin as T

PHASE = {
    "trot": {"fl": 0.0, "hr": 0.0, "fr": 0.5, "hl": 0.5},
    "walk": {"hr": 0.0, "fr": 0.25, "hl": 0.5, "fl": 0.75},    # lateral-sequence crawl: LH? (r=-x) RF, LH ...
    "walk2": {"hl": 0.0, "fl": 0.25, "hr": 0.5, "fr": 0.75},
}


def leg_targets(p, t, rest_feet, ramp=1.0, lev=None):
    """p: params dict. lev: optional per-leg z offsets (m) from the IMU levelling loop. Returns joint targets (deg)."""
    out = {}
    per, duty, S, H = p["period"], p["duty"], p["stride"], p["height"]
    for leg in T.LEGS:
        y0, z0 = rest_feet[leg]
        y0 += p.get("shift", 0.0)                 # move all feet fore/aft (body CoM relative to support)
        z0 += p.get("dz", 0.0)                    # body height change (negative = crouch -> feet higher)
        if lev: z0 += lev[leg]
        if leg[0] == "f": y0 += p.get("fy", 0.0)
        else: y0 += p.get("hy", 0.0)
        side = 1 if leg[1] == "l" else -1
        s = S * ramp
        if "turn" in p:                            # differential stride: + turn = CCW (to robot's left, +x)
            s = S * ramp * p.get("fwd", 0.0) - side * p["turn"] * ramp
        ph = (t / per + PHASE[p["gait"]][leg]) % 1.0
        if ph < duty:                              # stance: foot moves backward (+Y) relative to the body
            u = ph / duty
            y = y0 - s / 2 + s * u
            z = z0
        else:                                      # swing: lift and bring forward
            u = (ph - duty) / (1 - duty)
            y = y0 + s / 2 - s * (0.5 - 0.5 * math.cos(math.pi * u))
            z = z0 + H * ramp * math.sin(math.pi * u) ** p.get("hpow", 1.0)
        h, k = T.ik(leg, y, z)
        out["hip_" + leg] = h
        out["knee_" + leg] = k
    return out


class Leveler:
    """IMU levelling (OpenCat-style gyro balance): PI on body roll/pitch -> per-leg foot height offsets.
    x_z = world-z of body +x (left) axis; y_z = world-z of body +y (rear) axis. 1 kHz-ish update, 15 ms filter."""
    def __init__(self, kp=0.5, ki=1.5, lim=0.008):
        self.kp, self.ki, self.lim = kp, ki, lim
        self.ix = self.iy = 0.0; self.fx = self.fy = 0.0
    def __call__(self, s, dt):
        R = s.d.xmat[s.bid].reshape(3, 3)
        a = min(1.0, dt / 0.015)
        self.fx += a * (R[2, 0] - self.fx); self.fy += a * (R[2, 1] - self.fy)
        self.ix = max(-0.3, min(0.3, self.ix + self.fx * dt)); self.iy = max(-0.3, min(0.3, self.iy + self.fy * dt))
        ex = self.kp * self.fx + self.ki * self.ix; ey = self.kp * self.fy + self.ki * self.iy
        out = {}
        for leg in T.LEGS:
            sx = 1 if leg[1] == "l" else -1; sy = -1 if leg[0] == "f" else 1
            dz = 0.023 * ex * sx + 0.032 * ey * sy
            out[leg] = max(-self.lim, min(self.lim, dz))
        return out


def rest_feet():
    r = T.rest_pose()
    return {leg: T.fk(leg, r["hip_" + leg], r["knee_" + leg]) for leg in T.LEGS}


def run(p, xml, duration=6.0, warm=0.6, record=False, sim=None, extra=None):
    s = sim or T.Sim(xml, record=record)
    if sim is None:
        s.set_pose(T.rest_pose()); s.drop_to_floor()
        s.hold(T.rest_pose(), 0.3)
    rf = rest_feet()
    t0 = s.d.time
    p0 = s.d.qpos[0:3].copy()
    minup, maxtilt = 1.0, 0.0
    n = int(duration / T.DT)
    start_meas = None
    zs, sat = [], 0.0
    for i in range(n):
        t = s.d.time - t0
        ramp = min(1.0, t / warm) if warm > 0 else 1.0
        tg = leg_targets(p, t, rf, ramp)
        tg["tail"] = 0.0; tg["neck_pan"] = 0.0
        if extra: tg.update(extra(t))
        s.step(tg)
        if start_meas is None and t >= warm + p["period"]:
            start_meas = (s.d.time, s.d.qpos[0:3].copy(), yaw(s))
        up = s.up()[2][2]
        minup = min(minup, up)
        if start_meas is not None:
            zs.append(s.d.qpos[2]); maxtilt = max(maxtilt, math.degrees(math.acos(min(1, up))))
            sat += float(np.mean(np.abs(s.d.actuator_force[2:]) > 0.195))
    t1 = s.d.time
    ts, ps, yw0 = start_meas
    dp = s.d.qpos[0:3] - ps
    dyaw = unwrap(yaw(s) - yw0)
    # forward speed along the robot's average heading
    hd = yw0 + dyaw / 2
    fwd = np.array([math.sin(hd), -math.cos(hd)])      # -Y rotated by yaw
    v_fwd = float(dp[:2] @ fwd) / (t1 - ts)
    v_lat = float(dp[:2] @ np.array([fwd[1] * -1, fwd[0]])) / (t1 - ts)
    return dict(v_cm_s=round(v_fwd * 100, 3), lat_cm_s=round(abs(v_lat) * 100, 3), yaw_deg_s=round(math.degrees(dyaw) / (t1 - ts), 2),
                minup=round(float(minup), 3), peak_tau=round(s.peak_tau, 3), fell=bool(minup < 0.7),
                bounce_mm=round(float(np.ptp(zs)) * 1000, 2), tilt_deg=round(maxtilt, 1),
                sat_frac=round(sat / max(1, len(zs)), 3),
                eff=round(v_fwd / (p['stride'] / (p['duty'] * p['period'])), 2) if p.get('stride') else 0), s


def yaw(s):
    R = s.d.xmat[s.bid].reshape(3, 3)
    y = R[:, 1]                    # body +Y (backward) axis
    return math.atan2(-y[0], y[1])   # 0 when +Y body = +Y world


def unwrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


if __name__ == "__main__":
    xml = T.build()
    p = dict(gait="trot", period=0.5, duty=0.5, stride=0.02, height=0.01)
    t = time.time()
    r, s = run(p, xml, 4.0)
    print(r, "wall", round(time.time() - t, 1))
