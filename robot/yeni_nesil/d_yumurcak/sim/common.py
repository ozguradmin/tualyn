"""Shared MuJoCo harness for Yumurcak: load model, servo targets in manifest degrees, 30 fps recorder."""
import json, math, os
import numpy as np
import mujoco

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
MAN = json.load(open(os.path.join(PKG, "manifest.json")))
JOINTS = list(MAN["joints"].keys())
REST = {k: float(v) for k, v in MAN["pose_rest"].items()}
LEGS = ["fl", "fr", "bl", "br"]
FPS = 30


class Sim:
    def __init__(self, mu=0.6, slew=600.0):
        self.mu = mu
        self.m = mujoco.MjModel.from_xml_path(os.path.join(HERE, f"yumurcak_mu{mu}.xml"))
        self.d = mujoco.MjData(self.m)
        self.jq = {j: self.m.jnt_qposadr[mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_JOINT, j)] for j in JOINTS}
        self.jv = {j: self.m.jnt_dofadr[mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_JOINT, j)] for j in JOINTS}
        self.act = {j: mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_ACTUATOR, "a_" + j) for j in JOINTS}
        self.lim = {j: (MAN["joints"][j]["min"], MAN["joints"][j]["max"]) for j in JOINTS}
        self.body = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, "body")
        self.dt = self.m.opt.timestep
        self.slew = slew                      # firmware slew limit deg/s on the commanded target
        self.cmd = dict(REST)
        self.frames = []
        self.face = []
        self.t = 0.0
        self.next_rec = 0.0
        self.maxpen = 0.0
        self.max_tau = {j: 0.0 for j in JOINTS}

    # ------------------------------------------------------------------ state
    def set_pose(self, pose, base=(0, 0, 0, 1, 0, 0, 0)):
        for j in JOINTS:
            self.d.qpos[self.jq[j]] = math.radians(pose.get(j, REST[j]))
        self.d.qpos[0:3] = np.array(base[:3]) / 1000.0
        self.d.qpos[3:7] = base[3:7]
        self.d.qvel[:] = 0
        self.cmd = {j: pose.get(j, REST[j]) for j in JOINTS}
        for j in JOINTS:
            self.d.ctrl[self.act[j]] = math.radians(self.cmd[j])
        mujoco.mj_forward(self.m, self.d)

    def drop_to_floor(self, clearance=0.05):
        """translate the robot so its lowest geom point is `clearance` mm above the floor"""
        mujoco.mj_forward(self.m, self.d)
        zmin = 1e9
        for g in range(1, self.m.ngeom):
            if self.m.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH:
                continue
            mid = self.m.geom_dataid[g]
            a, n = self.m.mesh_vertadr[mid], self.m.mesh_vertnum[mid]
            V = self.m.mesh_vert[a:a + n]
            W = V @ self.d.geom_xmat[g].reshape(3, 3).T + self.d.geom_xpos[g]
            zmin = min(zmin, W[:, 2].min())
        self.d.qpos[2] += -zmin + clearance / 1000.0
        mujoco.mj_forward(self.m, self.d)

    def q(self, j):
        return math.degrees(self.d.qpos[self.jq[j]])

    def base(self):
        p = self.d.xpos[self.body] * 1000.0
        q = self.d.xquat[self.body]
        return [float(p[0]), float(p[1]), float(p[2]), float(q[0]), float(q[1]), float(q[2]), float(q[3])]

    def up(self):
        """body z axis in world (IMU gravity estimate)"""
        return self.d.xmat[self.body].reshape(3, 3)[:, 2].copy()

    def tilt(self):
        return math.degrees(math.acos(np.clip(self.up()[2], -1, 1)))

    def com(self):
        return self.d.subtree_com[self.body] * 1000.0

    # ------------------------------------------------------------------ control
    def target(self, pose):
        for j, v in pose.items():
            lo, hi = self.lim[j]
            self.cmd[j] = float(np.clip(v, lo, hi))

    def step_time(self, T, ctrl_fn=None, record=True):
        n = int(round(T / self.dt))
        for _ in range(n):
            if ctrl_fn is not None:
                ctrl_fn(self, self.t)
            for j in JOINTS:
                cur = math.degrees(self.d.ctrl[self.act[j]])
                tgt = self.cmd[j]
                mx = self.slew * self.dt
                cur += float(np.clip(tgt - cur, -mx, mx))
                self.d.ctrl[self.act[j]] = math.radians(cur)
            mujoco.mj_step(self.m, self.d)
            self.t += self.dt
            for j in JOINTS:
                tau = abs(self.d.actuator_force[self.act[j]])
                if tau > self.max_tau[j]:
                    self.max_tau[j] = tau
            if self.d.ncon:
                pen = -min(self.d.contact[i].dist for i in range(self.d.ncon))
                self.maxpen = max(self.maxpen, pen * 1000)
            if record:
                k = int(round(self.t * FPS * 1000))
                if len(self.frames) < int(self.t * FPS + 1e-6) + 1 and abs(self.t * FPS - round(self.t * FPS)) < self.dt * FPS * 0.5 + 1e-9:
                    self.snap()

    def snap(self):
        self.frames.append(dict(t=self.t, j={j: self.q(j) for j in JOINTS}, base=self.base(), tilt=self.tilt()))

    def set_face(self, expr):
        fi = len(self.frames)
        if self.face and self.face[-1][1] == expr:
            return
        if self.face and self.face[-1][0] == fi:
            self.face[-1] = [fi, expr]
        else:
            self.face.append([fi, expr])

    # ------------------------------------------------------------------ export
    def anim(self, loop=False, source="", metrics=None, start=0, end=None, face=None):
        fr = self.frames[start:end]
        out = {"fps": FPS, "loop": loop, "frames": len(fr),
               "joints": {j: [round(f["j"][j], 2) for f in fr] for j in JOINTS},
               "base": [[round(v, 2) for v in f["base"][:3]] + [round(v, 5) for v in f["base"][3:]] for f in fr]}
        fc = face if face is not None else [[max(0, a - start), e] for a, e in self.face if end is None or a < end]
        # collapse to the last face at or before frame 0
        fc2 = []
        for a, e in fc:
            if a <= 0:
                fc2 = [[0, e]]
            else:
                fc2.append([a, e])
        out["face"] = fc2 or [[0, "neutral"]]
        out["source"] = source
        out["metrics"] = metrics or {}
        return out


def source_str(mu, extra=""):
    return (f"MuJoCo 3.17 (sim/yumurcak_mu{mu}.xml, dt 1 ms): 8 x MG90S position servos clamped to ±0.20 N·m, SG90 head ±0.15 N·m, "
            f"~600°/s (damping), firmware slew limit; convex-hull contacts; desk μ={mu}, TPU soles μ={mu*1.5:.2f}; mass 345.6 g" + extra)
