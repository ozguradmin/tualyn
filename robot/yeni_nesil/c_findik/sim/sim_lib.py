"""Findik MuJoCo helpers: model loading, MG90S / N20 actuator models, IMU, 30 fps recorder.

Actuator models (applied every 1 ms physics step, like a real servo's internal loop):
  MG90S (5.6 V rail): tau = clip(kp*(q_t - q) - kd*qd, +-0.20 N m), and along the direction of motion
         |tau| <= 0.20*(1 - |qd|/w0) with w0 = 600 deg/s (no-load 0.10 s/60 deg)  -> real torque-speed line.
         kp = 2.9 N m/rad (full torque at ~4 deg error; analog MG90S, sensitivity 1.5-20 checked), kd = 0.006 N m s/rad. Armature 5e-5 kg m^2.
  N20 6 V 100 rpm (DRV8833, PWM <= 80 % of the 7.4 V pack ~ 6 V): tau = Ts*(u - qd/w0), Ts = 0.10 N m
         (conservative stall), w0 = 100 rpm; u = 0 is brake (slow decay) = back-EMF damping; gearbox
         friction 0.006 N m. Front wheels: free on an M3 shoulder screw (3e-5 N m friction).
"""
import json, math, os
import numpy as np
import mujoco

HERE = os.path.dirname(os.path.abspath(__file__))
HIPS = ["hip_fl", "hip_fr", "hip_rl", "hip_rr"]
WHEELS = ["wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"]
MAN = json.load(open(os.path.join(os.path.dirname(HERE), "manifest.json")))
LIM = {j: (MAN["joints"][j]["min"], MAN["joints"][j]["max"]) for j in HIPS}

SERVO_TS, SERVO_W0, SERVO_KP, SERVO_KD = 0.20, math.radians(600), 2.9, 0.006
N20_TS, N20_W0 = 0.10, 100 * 2 * math.pi / 60


def model_xml(mu_floor=0.6, mu_tyre=None, com_dz_mm=0.0):
    """mu_floor: PLA shell <-> desk; tyres use mu_tyre (TPU 95A, default 0.9 at mu 0.6, = mu_floor otherwise)."""
    if mu_tyre is None:
        mu_tyre = 0.9 if mu_floor >= 0.6 else mu_floor
    x = open(os.path.join(HERE, "findik_base.xml")).read()
    x = x.replace("@MU_SHELL@", f"{mu_floor}").replace("@MU_FLOOR@", f"{mu_floor}").replace("@MU_TYRE@", f"{mu_tyre}")
    x = x.replace('file="meshes/', f'file="{HERE}/meshes/')
    if com_dz_mm:
        import re
        def sh(mt):
            v = [float(t) for t in mt.group(1).split()]
            v[2] += com_dz_mm * 1e-3
            return 'pos="' + " ".join(f"{t:.7g}" for t in v) + '"'
        i = x.index("<freejoint")
        j = x.index("<inertial", i)
        k = x.index("/>", j)
        x = x[:j] + re.sub(r'pos="([^"]+)"', sh, x[j:k], count=1) + x[k:]
    return x


class Robot:
    def __init__(self, mu_floor=0.6, mu_tyre=None, com_dz_mm=0.0, fps=30):
        self.m = mujoco.MjModel.from_xml_string(model_xml(mu_floor, mu_tyre, com_dz_mm))
        self.d = mujoco.MjData(self.m)
        m = self.m
        self.qa = {j: m.joint(j).qposadr[0] for j in HIPS + WHEELS}
        self.va = {j: m.joint(j).dofadr[0] for j in HIPS + WHEELS}
        self.act = {n: m.actuator("m_" + n).id for n in HIPS + ["wheel_rl", "wheel_rr"]}
        self.bid = m.body("body").id
        self.target = {j: 22.0 for j in HIPS}
        self.u = {"wheel_rl": 0.0, "wheel_rr": 0.0}
        self.fps = fps
        self.substeps = int(round(1.0 / fps / m.opt.timestep))
        self.frames = []
        self.t = 0.0
        self.face = []
        self.peak_tau = {j: 0.0 for j in HIPS}
        self.sat_s = {j: 0.0 for j in HIPS}      # time spent at >= 95 % of stall torque
        self.sat_log = []
        self.ext = None          # optional (fn(t) -> (force3, torque3)) applied to the body CoM
        for j in HIPS:
            self.d.qpos[self.qa[j]] = math.radians(22)
        self.d.qpos[2] = 0.0002
        mujoco.mj_forward(m, self.d)

    # ---------------------------------------------------------------- state
    def q(self, j):
        return math.degrees(self.d.qpos[self.qa[j]])

    def gravity_body(self):
        R = self.d.xmat[self.bid].reshape(3, 3)
        return R.T @ np.array([0, 0, -1.0])

    def tilt(self):
        """(side, pitch) deg from the IMU gravity vector. side > 0: robot's LEFT (+X) side down.
        pitch < 0: nose (-Y) down."""
        g = self.gravity_body()
        side = math.degrees(math.atan2(g[0], -g[2]))
        pitch = math.degrees(math.atan2(g[1], -g[2]))
        up = math.degrees(math.acos(max(-1, min(1, -g[2]))))
        return side, pitch, up

    def base_pose(self):
        p = self.d.xpos[self.bid] * 1000
        q = self.d.xquat[self.bid]
        return [float(p[0]), float(p[1]), float(p[2]), float(q[0]), float(q[1]), float(q[2]), float(q[3])]

    # ---------------------------------------------------------------- actuators
    def _control(self):
        d = self.d
        for j in HIPS:
            lo, hi = LIM[j]
            qt = math.radians(min(hi, max(lo, self.target[j])))
            q, qd = d.qpos[self.qa[j]], d.qvel[self.va[j]]
            tau = SERVO_KP * (qt - q) - SERVO_KD * qd
            tau = max(-SERVO_TS, min(SERVO_TS, tau))
            if tau * qd > 0:
                lim = SERVO_TS * max(0.0, 1 - abs(qd) / SERVO_W0)
                tau = max(-lim, min(lim, tau))
            d.ctrl[self.act[j]] = tau
            self.peak_tau[j] = max(self.peak_tau[j], abs(tau))
            if abs(tau) > 0.95 * SERVO_TS:
                self.sat_s[j] += self.m.opt.timestep
                self.sat_log.append(round(self.d.time, 2))
        for w in ("wheel_rl", "wheel_rr"):
            qd = d.qvel[self.va[w]]
            tau = N20_TS * (self.u[w] - qd / N20_W0)
            d.ctrl[self.act[w]] = max(-N20_TS, min(N20_TS, tau))

    def step_frame(self, record=True):
        """advance 1/fps s; record the frame (state at the START of the frame is frame 0)."""
        if record:
            self.record()
        for _ in range(self.substeps):
            self._control()
            if self.ext is not None:
                f, tq = self.ext(self.d.time)
                self.d.xfrc_applied[self.bid, :3] = f
                self.d.xfrc_applied[self.bid, 3:] = tq
            mujoco.mj_step(self.m, self.d)
        self.d.xfrc_applied[self.bid] = 0
        self.t += 1.0 / self.fps

    def record(self):
        fr = {j: self.q(j) for j in HIPS + WHEELS}
        fr["base"] = self.base_pose()
        self.frames.append(fr)

    def settle(self, seconds=1.0):
        for _ in range(int(seconds * self.fps)):
            self.step_frame(record=False)

    # ---------------------------------------------------------------- checks
    def penetration_mm(self):
        worst = 0.0
        for c in self.d.contact[: self.d.ncon]:
            worst = min(worst, c.dist)
        return -worst * 1000

    def lowest_floor_contact_geoms(self):
        out = set()
        for c in self.d.contact[: self.d.ncon]:
            n1, n2 = self.m.geom(c.geom1).name, self.m.geom(c.geom2).name
            if "floor" in (n1, n2):
                out.add(n2 if n1 == "floor" else n1)
        return out

    def floating_mm(self):
        """distance from lowest collision geometry to the floor (approx, via contacts present)."""
        return 0.0 if self.d.ncon else 99.0

    # ---------------------------------------------------------------- export
    def export(self, path, face, loop=False, source="", metrics=None, joints=None):
        n = len(self.frames)
        J = joints or (HIPS + WHEELS)
        out = {"fps": self.fps, "loop": loop, "frames": n,
               "joints": {j: [round(f[j], 3) for f in self.frames] for j in J},
               "base": [[round(v, 3) if i < 3 else round(v, 6) for i, v in enumerate(f["base"])] for f in self.frames],
               "face": face, "source": source, "metrics": metrics or {}}
        json.dump(out, open(path, "w"), separators=(",", ":"))
        return out


def smooth(a, b, x):
    """cosine ease from a to b for x in [0,1]"""
    x = min(1.0, max(0.0, x))
    return a + (b - a) * (0.5 - 0.5 * math.cos(math.pi * x))


def src_line(mu=0.6, extra=""):
    return (f"MuJoCo {mujoco.__version__}, 1 ms step; MG90S 0.20 N·m / 600°/s torque-speed servo model; "
            f"N20 6 V 100 rpm 0.10 N·m stall; μ shell {mu}, TPU tyre {0.9 if mu >= 0.6 else mu}; mass 300.9 g" + extra)
