#!/usr/bin/env python3
"""Tarcin (concept B) MuJoCo model built directly from the package's model.glb, so that the link frames, joint
origins, axes and zeros are IDENTICAL to what rig.js animates.

- Body link 'body' = GLB root: origin on the desk under the body centre (freejoint). anim base = this body's pose.
- Joints: names, axes, ranges = manifest.joints (anatomical sides: l = +x = robot's LEFT).
- Collision: convex hulls of each link's real (non-internal) meshes; ears are separate hulls (rigid PLA by default).
- Masses: CAD mass budget (concept_B/stl/checks.json, 367.9 g) distributed per link, with the heavy internals
  (servos, cells, screens, boards) as non-colliding boxes at their real GLB positions.
- Servos: MG90S position actuators, torque clamped to +-0.20 N*m, kp 3 N*m/rad, damping + armature, command slew
  600 deg/s; head pan 4 g micro servo +-0.06 N*m.
- Contact: floor friction MU (0.6 nominal / 0.4 glossy). TPU paws are explicit floor pairs with MU_PAW
  (0.9 nominal / 0.6 glossy). Everything else uses the floor value (floor has contact priority).
"""
import json, math, os
import numpy as np
import trimesh
import mujoco

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
MESHDIR = os.path.join(HERE, "meshes")
MAN = json.load(open(os.path.join(PKG, "manifest.json")))
HIP_Z = 69.04594303749643
LEGS = ["fl", "fr", "hl", "hr"]
TAU = 0.20          # MG90S stall at ~5.5 V
TAU_PAN = 0.07      # E-Sky 002279 4 g digital micro servo, ~0.7 kg*cm
VMAX = math.radians(600)
DT = 0.0005
# Torque-speed droop (review fix). DC-motor servo model: torque = tau_max*u - (tau_max/w0)*w with the drive
# u = clip(kp*err/tau_max, -1, 1). The drive is the position actuator clamped to +-tau_max; the back-EMF term
# tau_max/w0 is joint damping (plus ~0.001 gear friction). Moving at w the servo can therefore only push
# tau_max*(1 - w/w0), and the no-load speed is ~600 deg/s (0.2/(0.2/11 + 0.001) = 10.4 rad/s).
# Before the review the damping was 0.012 only (no-load ~955 deg/s, i.e. too strong at speed).
# Voltage sag scales tau_max and w0 together, so the back-EMF damping stays the same (see sensitivity.py).
DROOP = True
W0 = 11.0           # MG90S no-load speed at 5.5 V, rad/s (~630 deg/s; 0.1 s/60 deg at 4.8 V)
W0_PAN = 14.0       # 4 g micro servo, ~0.075 s/60 deg
FRICTION = 0.001
DAMP_OVERRIDE = None   # sensitivity runs: fixed back-EMF damping (N*m*s/rad) independent of TAU


def damping():
    if not DROOP: return 0.012, 0.012
    d = DAMP_OVERRIDE if DAMP_OVERRIDE is not None else TAU / W0
    return d + FRICTION, TAU_PAN / W0_PAN + 0.0005


_LIMF = os.path.join(os.path.dirname(HERE), "build", "limits.json")
LIMITS = json.load(open(_LIMF)) if os.path.exists(_LIMF) else {}
COUPLED = True      # firmware coupled limit hip_f(max) = f(neck_pan) from sim/hipsweep.py (front leg vs head)


def hip_f_max(pan_deg, side):
    """largest allowed front hip angle for a given neck_pan (deg). side 'l' (+x leg) or 'r' (mirror: pan -> -pan).
    Table = build/limits.json 'hip_f_vs_pan' (pan step 5 deg, linear interpolation, conservative min of neighbours)."""
    tab = LIMITS.get("hip_f_vs_pan")
    if not tab: return 999.0
    p = pan_deg if side == "l" else -pan_deg
    ks = sorted(int(k) for k in tab)
    p = min(ks[-1], max(ks[0], p))
    lo = max(k for k in ks if k <= p); hi = min(k for k in ks if k >= p)
    return float(min(tab[str(lo)], tab[str(hi)]))

# ---- mass budget per link (g), from concept_B/stl/checks.json (367.9 g total) ----
MASS = {
    "head": {"hull": 47.8, "internal_screen": 15.0, "internal_servo": 4.5, "internal_pcb": 9.15},       # 76.45
    "body": {"hull": 40.8, "internal_battery": 39.0, "internal_servo": 13.4, "internal_power": 15.5,
             "internal_pcb": 3.85},                                                                         # 112.55
    "tail": {"hull": 14.1},
    "thigh": {"hull": 12.475, "internal_servo": 26.8},                                                     # 39.275 x4
    "shin": {"shin": 0.875, "paw": 1.075},                                                                  # 1.95 x4
}

COLLIDE = {
    "body": ["shell", "cream", "charcoal", "hub"],
    "head": ["shell_head", "shellcap", "cream_face", "visor", "nose", "backer", "lcdglass", "cheek"],
    "tail": ["shell_tail", "ring"],
    "thigh": ["shell_pod", "shell_podin", "sock"],
}


def _load_links():
    s = trimesh.load(os.path.join(PKG, "model.glb"))
    g = s.graph
    link_T = {}
    meshes = {}
    for n in g.nodes_geometry:
        T, gn = g.get(n)
        link, mat = n.split("__", 1)
        if link not in link_T:
            link_T[link] = g.get(link)[0]
        m = s.geometry[gn].copy()
        m.apply_transform(np.linalg.inv(link_T[link]) @ T)   # into the link frame (joint at origin), mm
        meshes.setdefault(link, {})[mat] = m
    return link_T, meshes


def _hull(parts, fname):
    m = trimesh.util.concatenate(parts)
    h = m.convex_hull
    h.apply_scale(0.001)
    dst = os.path.join(MESHDIR, fname)
    data = h.export(file_type="stl")
    if not (os.path.exists(dst) and open(dst, "rb").read() == data):   # atomic: parallel runs share this folder
        tmp = f"{dst}.{os.getpid()}.tmp"
        open(tmp, "wb").write(data); os.replace(tmp, dst)
    return fname


def build(mu=0.6, mu_paw=None, ears="rigid", self_collide=True, out=None):
    """Writes meshes + MJCF, returns xml string."""
    mu_paw = mu_paw if mu_paw is not None else 1.5 * mu
    os.makedirs(MESHDIR, exist_ok=True)
    link_T, M = _load_links()
    files = {}
    boxes = {}      # link -> list of (pos_m, half_m, mass_kg)
    for link, mats in M.items():
        kind = link.split("_")[0]
        if kind in ("thigh", "shin"):
            pass
        if kind in COLLIDE:
            parts = [mats[k] for k in COLLIDE[kind] if k in mats]
            files[link] = _hull(parts, f"{link}.stl")
        if kind == "head":
            ear = trimesh.util.concatenate([mats["ear"], mats["cream_ear"]])
            for sx, tag in ((1, "l"), (-1, "r")):
                sel = [p for p in ear.split(only_watertight=False) if p.centroid[0] * sx > 0]
                files[f"ear_{tag}"] = _hull(sel, f"ear_{tag}.stl")
        if kind == "shin":
            files[link] = _hull([mats["shin"]], f"{link}.stl")
            pk = [k for k in mats if k.startswith("paw")][0]
            files[link + "_paw"] = _hull([mats[pk]], f"{link}_paw.stl")
        for mk, gm in MASS.get(kind, {}).items():
            if mk.startswith("internal") and mk in mats:
                b = mats[mk].bounds / 1000.0
                boxes.setdefault(link, []).append(((b[0] + b[1]) / 2, np.maximum((b[1] - b[0]) / 2, 0.002), gm / 1000.0))

    def pos(link):
        T = link_T[link]
        parent = {"head": "body", "tail": "body"}.get(link)
        if link.startswith("thigh"): parent = "body"
        if link.startswith("shin"): parent = "thigh" + link[4:]
        P = link_T[parent] if parent else np.eye(4)
        return (np.linalg.inv(P) @ T)[:3, 3] / 1000.0

    def fmt(v):
        return " ".join(f"{x:.6g}" for x in v)

    def boxgeoms(link, ind):
        s = ""
        for p, h, m in boxes.get(link, []):
            s += f'{ind}<geom type="box" pos="{fmt(p)}" size="{fmt(h)}" mass="{m:.5f}" contype="0" conaffinity="0" group="3" rgba="0.2 0.5 1 0.4"/>\n'
        return s

    J = MAN["joints"]
    ec = "3" if ears == "rigid" else "0"
    ea = "1" if ears == "rigid" else "0"
    xml = f"""<mujoco model="tarcin_B">
  <compiler angle="degree" meshdir="{MESHDIR}"/>
  <option timestep="{DT}" integrator="implicitfast" gravity="0 0 -9.81"/>
  <size memory="20M"/>
  <visual><global offwidth="1400" offheight="1050"/></visual>
  <default>
    <geom contype="3" conaffinity="1" condim="3" friction="0.3 0.005 0.0001" solref="0.004 1" solimp="0.9 0.95 0.001"/>
    <joint damping="{damping()[0]:.5f}" armature="0.0004" limited="true"/>
    <position kp="3.0" forcerange="-{TAU} {TAU}" forcelimited="true"/>
  </default>
  <asset>
""" + "".join(f'    <mesh name="{k}" file="{v}"/>\n' for k, v in files.items()) + f"""  </asset>
  <worldbody>
    <light pos="0 -0.3 0.6" dir="0 0.4 -1"/>
    <geom name="floor" type="plane" size="2 2 0.1" friction="{mu} 0.005 0.0001" priority="1" contype="1" conaffinity="3" rgba="0.8 0.78 0.74 1"/>
    <body name="body" pos="0 0 0.002">
      <freejoint name="root"/>
      <geom name="body_hull" type="mesh" mesh="body" mass="{MASS['body']['hull'] / 1000:.5f}"/>
{boxgeoms('body', '      ')}      <site name="imu" pos="0 0 {HIP_Z / 1000:.5f}"/>
      <body name="head" pos="{fmt(pos('head'))}">
        <joint name="neck_pan" axis="0 0 1" range="{J['neck_pan']['min']} {J['neck_pan']['max']}" damping="{damping()[1]:.5f}"/>
        <geom name="head_hull" type="mesh" mesh="head" mass="{MASS['head']['hull'] / 1000 - 0.006:.5f}"/>
        <geom name="ear_l" type="mesh" mesh="ear_l" mass="0.003" contype="{ec}" conaffinity="{ea}"/>
        <geom name="ear_r" type="mesh" mesh="ear_r" mass="0.003" contype="{ec}" conaffinity="{ea}"/>
{boxgeoms('head', '        ')}      </body>
      <body name="tail" pos="{fmt(pos('tail'))}">
        <joint name="tail" axis="0 1 0" range="{J['tail']['min']} {J['tail']['max']}"/>
        <geom name="tail_hull" type="mesh" mesh="tail" mass="{MASS['tail']['hull'] / 1000:.5f}"/>
      </body>
"""
    for leg in LEGS:
        th, sh = "thigh_" + leg, "shin_" + leg
        jh, jk = J["hip_" + leg], J["knee_" + leg]
        xml += f"""      <body name="{th}" pos="{fmt(pos(th))}">
        <joint name="hip_{leg}" axis="1 0 0" range="{jh['min']} {jh['max']}"/>
        <geom name="{th}_hull" type="mesh" mesh="{th}" mass="{MASS['thigh']['hull'] / 1000:.5f}"/>
{boxgeoms(th, '        ')}        <body name="{sh}" pos="{fmt(pos(sh))}">
          <joint name="knee_{leg}" axis="1 0 0" range="{jk['min']} {jk['max']}"/>
          <geom name="{sh}_hull" type="mesh" mesh="{sh}" mass="{MASS['shin']['shin'] / 1000:.5f}"/>
          <geom name="{sh}_paw" type="mesh" mesh="{sh}_paw" mass="{MASS['shin']['paw'] / 1000:.5f}" contype="2" conaffinity="2" rgba="0.1 0.1 0.1 1"/>
        </body>
      </body>
"""
    xml += "    </body>\n  </worldbody>\n  <contact>\n"
    for leg in LEGS:
        xml += f'    <pair geom1="floor" geom2="shin_{leg}_paw" condim="3" friction="{mu_paw} {mu_paw} 0.005 0.0001 0.0001" solref="0.004 1" solimp="0.9 0.95 0.001"/>\n'
    xml += "  </contact>\n  <actuator>\n"
    xml += f'    <position name="neck_pan" joint="neck_pan" kp="1.0" forcerange="-{TAU_PAN} {TAU_PAN}" ctrlrange="-40 40"/>\n'
    xml += f'    <position name="tail" joint="tail" ctrlrange="-85 85"/>\n'
    for leg in LEGS:
        jh, jk = J["hip_" + leg], J["knee_" + leg]
        xml += f'    <position name="hip_{leg}" joint="hip_{leg}" ctrlrange="{jh["min"]} {jh["max"]}"/>\n'
        xml += f'    <position name="knee_{leg}" joint="knee_{leg}" ctrlrange="{jk["min"]} {jk["max"]}"/>\n'
    xml += "  </actuator>\n  <sensor>\n    <framequat name=\"imu_q\" objtype=\"site\" objname=\"imu\"/>\n  </sensor>\n</mujoco>\n"
    if out:
        open(out, "w").write(xml)
    return xml


def foot_points():
    """Paw sole centre (m) in each shin frame, from the GLB in the rest pose (hip/knee from pose_rest)."""
    link_T, M = _load_links()
    res = {}
    for leg in LEGS:
        mats = M["shin_" + leg]
        pk = [k for k in mats if k.startswith("paw")][0]
        v = mats[pk].vertices.copy()     # shin frame, mm
        b = math.radians(MAN["pose_rest"]["hip_" + leg] + MAN["pose_rest"]["knee_" + leg])
        c, s = math.cos(b), math.sin(b)
        zr = v[:, 1] * s + v[:, 2] * c          # z after rotating by b about +X
        sole = v[zr < zr.min() + 0.6]
        res[leg] = sole.mean(axis=0) / 1000.0
    return res


JOINTS = ["neck_pan", "tail"] + [f"{p}_{l}" for l in LEGS for p in ("hip", "knee")]


class Sim:
    def __init__(self, xml, record=True):
        self.m = mujoco.MjModel.from_xml_string(xml)
        self.d = mujoco.MjData(self.m)
        self.aid = {self.m.actuator(i).name: i for i in range(self.m.nu)}
        self.qadr = {n: self.m.jnt_qposadr[mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in JOINTS}
        self.vadr = {n: self.m.jnt_dofadr[mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in JOINTS}
        self.bid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, "body")
        self.cmd = {n: 0.0 for n in JOINTS}      # degrees, slewed command sent to the servo
        self.frames = []
        self.record = record
        self.peak_tau = 0.0
        self.sub = round(1 / 30 / DT)
        self.k = 0
        self.face_events = []
        self.t_rec = None
        self.tau = TAU; self.vmax = VMAX; self.coupled = COUPLED
        self.peak_pan_gear = 0.0; self.peak_pan_ext = 0.0; self.max_pan_overshoot = 0.0
        self.n_hip_clamped = 0
        self.pan_jid = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_JOINT, "neck_pan")
        self.rng = {}
        for n in JOINTS:
            j = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_JOINT, n)
            self.rng[n] = tuple(math.degrees(v) for v in self.m.jnt_range[j])

    def total_mass(self):
        return float(self.m.body_subtreemass[self.bid])

    def set_pose(self, pose, base=(0, 0, 0.0, 1, 0, 0, 0)):
        mujoco.mj_resetData(self.m, self.d)
        self.d.qpos[0:3] = base[0:3]
        self.d.qpos[3:7] = base[3:7]
        for n in JOINTS:
            v = pose.get(n, 0.0)
            self.d.qpos[self.qadr[n]] = math.radians(v)
            self.cmd[n] = v
            self.d.ctrl[self.aid[n]] = math.radians(v)
        mujoco.mj_forward(self.m, self.d)

    def drop_to_floor(self):
        """shift the base so that the lowest contact geom just touches z=0"""
        mujoco.mj_forward(self.m, self.d)
        zmin = 1e9
        for gi in range(self.m.ngeom):
            if self.m.geom_type[gi] != mujoco.mjtGeom.mjGEOM_MESH: continue
            mid = self.m.geom_dataid[gi]
            va, nv = self.m.mesh_vertadr[mid], self.m.mesh_vertnum[mid]
            V = self.m.mesh_vert[va:va + nv]
            W = V @ self.d.geom_xmat[gi].reshape(3, 3).T + self.d.geom_xpos[gi]
            zmin = min(zmin, W[:, 2].min())
        self.d.qpos[2] -= zmin - 0.0002
        mujoco.mj_forward(self.m, self.d)

    def up(self):
        R = self.d.xmat[self.bid].reshape(3, 3)
        return R[:, 0], R[:, 1], R[:, 2]

    def q(self, n):
        return math.degrees(self.d.qpos[self.qadr[n]])

    def snap(self):
        p = self.d.xpos[self.bid] * 1000.0
        qt = self.d.xquat[self.bid]
        self.frames.append(dict(t=self.d.time, base=[round(float(x), 3) for x in p] + [round(float(x), 6) for x in qt],
                                joints={n: round(self.q(n), 3) for n in JOINTS}))

    def step(self, target=None, slew=None):
        """one physics step; target: dict joint->deg (the servo setpoint), slewed at 'slew' rad/s (default self.vmax)"""
        slew = self.vmax if slew is None else min(slew, self.vmax)
        if target:
            lim = math.degrees(slew) * DT
            for n, v in target.items():
                lo, hi = self.rng[n]
                v = min(hi, max(lo, v))
                c = self.cmd[n]
                self.cmd[n] = c + max(-lim, min(lim, v - c))
        if self.coupled:            # firmware: front hip may not swing into the head (limit depends on pan)
            pq = self.q("neck_pan"); pc = self.cmd["neck_pan"]
            for side in ("l", "r"):
                n = "hip_f" + side
                hm = min(hip_f_max(pq, side), hip_f_max(pc, side))
                if self.cmd[n] > hm:
                    self.cmd[n] = max(hm, self.cmd[n] - math.degrees(self.vmax) * DT); self.n_hip_clamped += 1
        for n in JOINTS:
            self.d.ctrl[self.aid[n]] = math.radians(self.cmd[n])
        if self.record:
            if self.t_rec is None: self.t_rec = self.d.time
            if self.d.time >= self.t_rec - 1e-9:
                self.snap(); self.t_rec += 1.0 / 30.0
        mujoco.mj_step(self.m, self.d)
        self.k += 1
        f = float(np.abs(self.d.actuator_force[1:]).max())
        self.peak_tau = max(self.peak_tau, f)
        # head-pan gear load: actuator torque + joint-limit reaction (the limit stop is the servo's own gear train),
        # and the external (contact) torque about the pan axis
        dp = self.vadr["neck_pan"]
        ne = self.d.nefc
        lim_t = 0.0
        if ne:
            msk = (self.d.efc_type[:ne] == mujoco.mjtConstraint.mjCNSTR_LIMIT_JOINT) & (self.d.efc_id[:ne] == self.pan_jid)
            if msk.any():   # unilateral limit force pushes back into the range
                lim_t = float(self.d.efc_force[:ne][msk].sum()) * (1.0 if self.q("neck_pan") < 0 else -1.0)
        gear = abs(float(self.d.actuator_force[self.aid["neck_pan"]]) + lim_t)
        self.peak_pan_gear = max(self.peak_pan_gear, gear)
        self.peak_pan_ext = max(self.peak_pan_ext, abs(float(self.d.qfrc_constraint[dp]) - lim_t))
        self.max_pan_overshoot = max(self.max_pan_overshoot, abs(self.q("neck_pan")) - 40.0)

    def hold(self, target, seconds, slew=VMAX):
        for _ in range(int(round(seconds / DT))):
            self.step(target, slew)

    def face(self, expr):
        self.face_events.append((len(self.frames), expr))

    def clip(self, loop=False, source="", metrics=None, start=0, end=None):
        fr = self.frames[start:end]
        out = {"fps": 30, "loop": loop, "frames": len(fr),
               "joints": {n: [f["joints"][n] for f in fr] for n in JOINTS},
               "base": [f["base"] for f in fr],
               "face": [[max(0, i - start), e] for i, e in self.face_events if i - start < len(fr)],
               "source": source}
        # keep only the last face event at or before frame 0, plus later ones
        fe, last0 = [], None
        for i, e in out["face"]:
            if i == 0: last0 = [0, e]
            else: fe.append([i, e])
        out["face"] = ([last0] if last0 else []) + fe
        if metrics: out["metrics"] = metrics
        return out


# ---------------- leg kinematics (in the sagittal plane of each hip) ----------------
L1 = 0.040
FOOT = None


def _foot():
    global FOOT
    if FOOT is None:
        FOOT = foot_points()
    return FOOT


def fk(leg, hip, knee):
    """foot (y, z) in m relative to the hip axis, body frame; hip/knee in deg"""
    a, b = math.radians(hip), math.radians(hip + knee)
    p = _foot()[leg]
    ky, kz = L1 * math.sin(a), -L1 * math.cos(a)
    fy = ky + p[1] * math.cos(b) - p[2] * math.sin(b)
    fz = kz + p[1] * math.sin(b) + p[2] * math.cos(b)
    return fy, fz


def ik(leg, y, z):
    """foot target (y, z) relative to hip -> (hip, knee) deg, choosing the concept's knee direction
    (front knees point back/inward: knee<0; hind knees point forward: knee>0)."""
    p = _foot()[leg]
    L2 = math.hypot(p[1], p[2])
    off = math.atan2(p[1], -p[2])          # angle of the foot point inside the shin frame (from -Z toward +Y)
    D = math.hypot(y, z)
    D = min(D, L1 + L2 - 1e-5)
    cos_k = (L1 * L1 + L2 * L2 - D * D) / (2 * L1 * L2)
    inner = math.acos(max(-1, min(1, cos_k)))
    bend = math.pi - inner                  # |knee + off| deviation
    sgn = -1 if leg[0] == "f" else 1
    phi = math.atan2(y, -z)                 # direction hip->foot, from -Z toward +Y
    alpha = math.asin(max(-1, min(1, L2 * math.sin(bend) / D)))
    hip = phi - sgn * alpha
    knee_eff = sgn * bend
    knee = knee_eff - off
    return math.degrees(hip), math.degrees(knee)


def rest_pose():
    return dict(MAN["pose_rest"])
