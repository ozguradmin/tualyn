"""Tosbi sim library: model loading, servo command loop (50 Hz like PCA9685 + firmware), IMU, recorder.

Angles everywhere are in the manifest convention (degrees, zero = 0); qpos = deg2rad(angle).
Base pose recorded = world pose of the GLB root/body link (mm, quaternion wxyz), exactly what rig.js setBase takes.
"""
import json, math, os
import numpy as np, mujoco

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
MAN = json.load(open(os.path.join(PKG, "manifest.json")))
JN = list(MAN["joints"].keys())
LEGS = ("fl", "fr", "rl", "rr")
MASS_G = json.load(open(os.path.join(HERE, "links.json")))["total_g"] if os.path.exists(os.path.join(HERE, "links.json")) else 380
REST = dict(MAN["pose_rest"])
CTRL_DT = 0.02            # firmware/PCA9685 update period (50 Hz)
FPS = 30
ACC_NOISE = 0.08          # m/s^2, MPU6050 +-2 g range noise is ~0.004 g/sqrt(Hz) -> ~0.03-0.08 m/s^2 at 50-400 Hz
SEED = 7


def load(mu=0.6):
    m = mujoco.MjModel.from_xml_path(os.path.join(HERE, "tosbi.xml"))
    tpu = 0.9 * mu / 0.6  # TPU toes: 0.9 on the mu 0.6 desk, scaled down on the slippery desk
    for g in range(m.ngeom):
        nm = m.geom(g).name
        if nm == "floor" or not nm.startswith("foot") or "toe" not in nm:
            m.geom_friction[g, 0] = mu
        else:
            m.geom_friction[g, 0] = tpu
    d = mujoco.MjData(m)
    return m, d


class Sim:
    def __init__(self, mu=0.6):
        self.mu = mu
        self.m, self.d = load(mu)
        m = self.m
        self.qadr = {j: m.jnt_qposadr[m.joint(j).id] for j in JN}
        self.dadr = {j: m.jnt_dofadr[m.joint(j).id] for j in JN}
        self.act = {j: m.actuator(j).id for j in JN}
        self.bid = m.body("body").id
        self.acc_adr = m.sensor_adr[m.sensor("imu_acc").id]
        self.rng = np.random.default_rng(SEED)
        self.frames = []; self.faces = []; self.t = 0.0; self.next_rec = 0.0
        self.cmd = dict(REST)
        self.events = []
        self.reset_torque_stats()

    def reset_torque_stats(self):
        self.tau_peak = np.zeros(self.m.nu); self.tau_sum = np.zeros(self.m.nu); self.tau_n = 0; self.tau_sat = np.zeros(self.m.nu)

    def torque_stats(self):
        """peak / mean |torque| (N m) and fraction of time at the 0.20 N m clamp, grouped hip / knee / neck."""
        out = {}
        for grp in ("hip", "knee", "neck"):
            ids = [self.act[j] for j in JN if j.startswith(grp)]
            out[grp] = {"peak": round(float(self.tau_peak[ids].max()), 3),
                        "mean": round(float(self.tau_sum[ids].mean() / max(1, self.tau_n)), 4),
                        "time_at_clamp_pct": round(float(100 * self.tau_sat[ids].max() / max(1, self.tau_n)), 1)}
        return out

    # ------------------------------------------------------------- state
    def set_pose(self, pose, base=(0, 0, 0, 1, 0, 0, 0)):
        d = self.d
        mujoco.mj_resetData(self.m, d)
        d.qpos[0:3] = np.array(base[:3]) / 1000.0
        d.qpos[3:7] = base[3:7]
        for j, v in pose.items():
            d.qpos[self.qadr[j]] = math.radians(v)
        self.cmd = dict(pose)
        self.apply_cmd()
        mujoco.mj_forward(self.m, d)

    def drop_to_floor(self, clearance=0.5):
        """shift the base vertically so the lowest geom point sits `clearance` mm above the floor."""
        m, d = self.m, self.d
        mujoco.mj_forward(m, d)
        zmin = 1e9
        for g in range(m.ngeom):
            if m.geom_bodyid[g] == 0: continue
            mid = m.geom_dataid[g]
            if mid < 0: continue
            va, vn = m.mesh_vertadr[mid], m.mesh_vertnum[mid]
            V = m.mesh_vert[va:va + vn]
            W = V @ d.geom_xmat[g].reshape(3, 3).T + d.geom_xpos[g]
            zmin = min(zmin, W[:, 2].min())
        d.qpos[2] += -zmin + clearance / 1000.0
        mujoco.mj_forward(m, d)

    def R(self):
        return self.d.xmat[self.bid].reshape(3, 3)

    def up(self):          # world-z component of body z axis (+1 face A up, -1 face B up)
        return self.R()[2, 2]

    def grav_body(self):
        """gravity direction in the body frame as the MPU6050 (GY-521) accelerometer gives it: the simulated imu_acc
        sensor (specific force, site on the deck) + 0.08 m/s^2 white noise per axis, sign-flipped and normalised.
        No ideal rotation matrix is used (review fix)."""
        a = self.d.sensordata[self.acc_adr:self.acc_adr + 3] + self.rng.normal(0.0, ACC_NOISE, 3)
        n = float(np.linalg.norm(a)); self.acc_norm = n
        return -a / n if n > 1e-6 else np.array([0.0, 0.0, -1.0])

    def base(self):
        d = self.d
        p = d.xpos[self.bid] * 1000.0; q = d.xquat[self.bid]
        return [float(p[0]), float(p[1]), float(p[2]), float(q[0]), float(q[1]), float(q[2]), float(q[3])]

    def joints_deg(self):
        return {j: math.degrees(self.d.qpos[self.qadr[j]]) for j in JN}

    # ------------------------------------------------------------- control
    def apply_cmd(self):
        for j, v in self.cmd.items():
            lo, hi = self.m.actuator_ctrlrange[self.act[j]]
            self.d.ctrl[self.act[j]] = min(hi, max(lo, math.radians(v)))

    def run(self, duration, policy=None, record=True, face=None, push=None):
        """step physics for `duration` s. policy(sim, t) -> dict of joint targets (deg) or None, called at 50 Hz.
        push(sim, t) may set xfrc_applied. face: expression name to log at the current frame."""
        m, d = self.m, self.d
        if face is not None: self.set_face(face)
        t_end = self.t + duration
        next_ctrl = self.t
        while self.t < t_end - 1e-9:
            if self.t >= next_ctrl - 1e-9:
                if policy is not None:
                    c = policy(self, self.t)
                    if c: self.cmd.update(c)
                self.apply_cmd()
                next_ctrl += CTRL_DT
            if record and self.t >= self.next_rec - 1e-9:
                self.record()
            d.xfrc_applied[:] = 0
            if push is not None: push(self, self.t)
            mujoco.mj_step(m, d)
            f = np.abs(d.actuator_force); self.tau_peak = np.maximum(self.tau_peak, f); self.tau_sum += f; self.tau_n += 1
            self.tau_sat += f > 0.98 * m.actuator_forcerange[:, 1]
            self.t += m.opt.timestep
        return self

    def record(self):
        jd = self.joints_deg()
        self.frames.append({"t": self.t, "joints": jd, "base": self.base(), "up": float(self.up())})
        self.next_rec += 1.0 / FPS

    def set_face(self, expr):
        n = len(self.frames)
        if self.faces and self.faces[-1][1] == expr: return
        if self.faces and self.faces[-1][0] == n: self.faces[-1] = [n, expr]
        else: self.faces.append([n, expr])

    # ------------------------------------------------------------- metrics
    def max_actuator_torque(self):
        return float(np.abs(self.d.actuator_force).max())

    def penetration(self):
        """deepest floor penetration (mm) in current contacts"""
        worst = 0.0
        for i in range(self.d.ncon):
            c = self.d.contact[i]
            worst = min(worst, c.dist)
        return -worst * 1000.0

    def to_clip(self, loop=False, start=0, end=None, extra=None, source_note=""):
        fr = self.frames[start:end]
        # rig.js clamps to the manifest ranges anyway; clamp here too so the data never shows a hip past its hard stop.
        # The largest excess before clamping is reported (impact back-driving a servo against its stop).
        self.clamp_excess = 0.0
        for f in fr:
            for j, v in f["joints"].items():
                lo, hi = MAN["joints"][j]["min"], MAN["joints"][j]["max"]
                if v < lo or v > hi:
                    self.clamp_excess = max(self.clamp_excess, lo - v if v < lo else v - hi)
                    f["joints"][j] = min(hi, max(lo, v))
        faces = [[max(0, f - start), e] for f, e in self.faces if (end is None or f < end)]
        # keep the last face that started before `start`
        fs = []
        for f, e in faces:
            if f == 0 and fs: fs[-1] = [0, e]
            else: fs.append([f, e])
        ded = []
        for f, e in fs:                          # drop consecutive repeats of the same expression
            if not ded or ded[-1][1] != e: ded.append([f, e])
        fs = ded
        clip = {"fps": FPS, "loop": loop, "frames": len(fr),
                "joints": {j: [round(f["joints"][j], 2) for f in fr] for j in JN},
                "base": [[round(v, 3) if k < 3 else round(v, 5) for k, v in enumerate(f["base"])] for f in fr],
                "face": fs,
                "source": f"MuJoCo {mujoco.__version__}, MG90S position servos 0.20 N·m clamp / 600°/s torque-speed line "
                          f"(kp 3 N·m/rad, damping 0.019, armature 2e-4), 50 Hz servo updates, μ={self.mu} (TPU toes {0.9*self.mu/0.6:.2f}), "
                          f"mass {MASS_G:.0f} g, dt 1 ms, stiff ideal 5.5 V servo rail" + (("; " + source_note) if source_note else "")}
        if extra: clip["metrics"] = extra
        return clip


def save_clip(clip, name):
    p = os.path.join(PKG, "anim", name + ".json")
    json.dump(clip, open(p, "w"), separators=(",", ":"))
    return p


def smooth(x):  # 0..1 -> 0..1 smoothstep
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def lerp_pose(a, b, s):
    return {k: a[k] + (b[k] - a[k]) * s for k in a}


def stand_pose(sign=1, neck=15):
    p = {f"hip_{l}": 0.0 for l in LEGS}
    p.update({f"knee_{l}": 80.0 * sign for l in LEGS}); p["neck"] = neck * sign
    return p


def yaw_of(q):
    w, x, y, z = q
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
