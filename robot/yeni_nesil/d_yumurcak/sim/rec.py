"""Recorder on top of common.Sim: exact 30 fps sampling, clip start at t=0, loop closing, face timeline."""
import math, json, os
import numpy as np
import mujoco
from common import Sim, JOINTS, REST, LEGS, FPS, HERE, PKG


_LC = json.load(open(os.path.join(HERE, "limits_coupled.json")))


def kmax(yaw):
    return float(np.interp(yaw, _LC["yaw"], _LC["kmax"]))


_YS = np.linspace(0, 85, 341)
_KG = np.arange(-15, 164.01, 0.5)
_YM = np.array([_YS[np.interp(_YS, _LC["yaw"], _LC["kmax"]) >= kg - 1e-6].max() for kg in _KG])


def ymax_for_knee(knee):
    """largest yaw whose kmax still allows this knee (kmax is non-increasing for yaw >= 0)"""
    return float(np.interp(knee, _KG, _YM))


class Rec(Sim):
    coupled = True
    def begin(self):
        """start a clip here: t = 0, first frame recorded now"""
        self.t = 0.0; self.frames = []; self.face = []; self.k = 0
        self.maxpen = 0.0; self.max_tau = {j: 0.0 for j in JOINTS}; self.sat_s = 0.0
        self.snap(); self.k = 1

    def step_time(self, T, ctrl_fn=None, record=True):
        n = int(round(T / self.dt))
        for _ in range(n):
            if ctrl_fn is not None:
                ctrl_fn(self, self.t)
            for j in JOINTS:
                cur = math.degrees(self.d.ctrl[self.act[j]])
                mx = self.slew * self.dt
                cur += float(np.clip(self.cmd[j] - cur, -mx, mx))
                self.d.ctrl[self.act[j]] = math.radians(cur)
            if self.coupled:                      # firmware coupled yaw/knee limit (no paw-shell collisions)
                for k in LEGS:
                    ay, ak = self.act["yaw_" + k], self.act["knee_" + k]
                    yq, kq = self.q("yaw_" + k), self.q("knee_" + k)
                    kc = min(math.degrees(self.d.ctrl[ak]), kmax(max(yq, math.degrees(self.d.ctrl[ay]))))
                    self.d.ctrl[ak] = math.radians(kc)
                    yc = math.degrees(self.d.ctrl[ay])
                    if yc > 0:
                        yc = min(yc, max(ymax_for_knee(kq), min(yq, yc)))
                    self.d.ctrl[ay] = math.radians(yc)
            mujoco.mj_step(self.m, self.d)
            self.t += self.dt
            sat = False
            for j in JOINTS:
                f = abs(self.d.actuator_force[self.act[j]])
                self.max_tau[j] = max(self.max_tau[j], f)
                sat = sat or (j != "head" and f > 0.195)
            if sat:
                self.sat_s = getattr(self, "sat_s", 0.0) + self.dt
            if self.d.ncon:
                for i in range(self.d.ncon):
                    c = self.d.contact[i]
                    if c.geom1 == 0 or c.geom2 == 0:
                        self.maxpen = max(self.maxpen, -c.dist * 1000)
            if record and hasattr(self, "k") and self.t >= self.k / FPS - self.dt / 2:
                self.snap(); self.k += 1

    def settle(self, pose=None, T=0.4):
        self.set_pose(pose or REST); self.drop_to_floor(0.05)
        self.step_time(T, record=False)


def close_loop(anim):
    """make the last frame equal the first by spreading the mismatch linearly over the clip (joints + base xyz)"""
    n = anim["frames"]
    for j, arr in anim["joints"].items():
        d = arr[-1] - arr[0]
        anim["joints"][j] = [round(v - d * i / (n - 1), 2) for i, v in enumerate(arr)]
    b = np.array(anim["base"], float)
    d = b[-1, :3] - b[0, :3]
    b[:, :3] -= np.outer(np.arange(n) / (n - 1), d)
    q0 = b[0, 3:]
    # quaternion: blend the end towards the start over the last 10 frames
    for i in range(max(0, n - 10), n):
        w = (i - (n - 10)) / 9.0
        q = (1 - w) * b[i, 3:] + w * q0 * np.sign(np.dot(q0, b[i, 3:]))
        b[i, 3:] = q / np.linalg.norm(q)
    anim["base"] = [[round(v, 2) for v in r[:3]] + [round(v, 5) for v in r[3:]] for r in b]
    return anim


def clamp_to_manifest(anim):
    """clamp recorded joint angles to the manifest limits (e.g. the knee servo overshoots 164 -> 165 by ~1 deg
    under impact in the sim; the viewer and a real MG90S calibrated to 0..164 never go past the limit)"""
    lim = json.load(open(os.path.join(PKG, "manifest.json")))["joints"]
    for j, arr in anim["joints"].items():
        if j in lim and not lim[j].get("continuous"):
            lo, hi = lim[j].get("min", -180), lim[j].get("max", 180)
            anim["joints"][j] = [round(min(hi, max(lo, v)), 2) for v in arr]
    return anim


def save(name, anim):
    anim = clamp_to_manifest(anim)
    f = os.path.join(PKG, "anim", name + ".json")
    json.dump(anim, open(f, "w"), separators=(",", ":"))
    return f
