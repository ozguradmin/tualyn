#!/usr/bin/env python3
"""MuJoCo self-righting check for concept B 'Tarcin', built from the real CAD STLs (convex hulls).

Usage: python3 -I sim/righting.py <stl_dir> [--ears soft|rigid]
Starts the robot lying on its +x side, -x side, on its back, and at several random orientations,
runs an OpenCat-'rc'-style recovery state machine with MG90S-limited actuators, and reports success.
"""
import json, math, os, sys
import numpy as np
import mujoco
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
STL = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "stl")
EARS = "rigid" if "--rigid-ears" in sys.argv else "soft"
TAILC = "0" if "--soft-tail" in sys.argv else "1"
TAIL_SCALE = float([a.split("=")[1] for a in sys.argv if a.startswith("--tail-scale=")][0]) if any(a.startswith("--tail-scale=") for a in sys.argv) else 1.0
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

HIP_Y, L1, L2 = 0.032, 0.040, 0.034
info = json.load(open(os.path.join(STL, "checks.json")))
HIP_Z = info["hip_z"] / 1000.0
STAND = {"F": (20.0, -24.0), "H": (-20.0, 24.0)}        # (a, b) absolute thigh/shin angles, deg
HIP_RANGE = {"F": "-20 160", "H": "-50 130"}     # 180-deg servo windows: both hips swing 'backward' over the back
KNEE_RANGE = {"F": "-150 25", "H": "-25 150"}
if "--knee140" in sys.argv:          # tighter fold limit (shin/paw vs hip hub clearance in the CAD)
    KNEE_RANGE = {"F": "-140 25", "H": "-25 140"}
TAU_MAX = 0.20                                            # MG90S @ ~5.5-6 V stall, N*m
VMAX = math.radians(400)                                  # rad/s, MG90S no-load ~600 deg/s


def load(name):
    return trimesh.load(os.path.join(STL, name + ".stl"))


def rotx(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def write_hull(mesh, fname):
    h = mesh.convex_hull
    h.export(os.path.join(OUT, fname))
    return fname


def split_by(mesh, fn):
    parts = mesh.split(only_watertight=False)
    return [p for p in parts if fn(p.centroid)]


def build_xml():
    # ---- world-frame STLs (standing pose), converted to metres and to local frames
    def m(name):
        x = load(name)
        x.apply_scale(0.001)
        return x
    body = trimesh.util.concatenate([m("body_top"), m("body_belly")])
    body.apply_translation([0, 0, -HIP_Z])
    head = trimesh.util.concatenate([m("head_main"), m("head_face"), m("mask")])
    head.apply_translation([0, 0, -HIP_Z])
    ears = m("ear_outer"); ears.apply_translation([0, 0, -HIP_Z])
    tail = trimesh.util.concatenate([m("tail_a"), m("tail_b")]); tail.apply_translation([0, 0, -HIP_Z])
    pods = trimesh.util.concatenate([m("pod"), m("pod_low")])
    shins = trimesh.util.concatenate([m("shin"), m("paw")])
    files = {}
    files["body"] = write_hull(body, "body.stl")
    files["head"] = write_hull(head, "head.stl")
    for sx, tag in ((1, "p"), (-1, "n")):
        e = trimesh.util.concatenate(split_by(ears, lambda c, sx=sx: c[0] * sx > 0))
        files["ear_" + tag] = write_hull(e, f"ear_{tag}.stl")
    if TAIL_SCALE != 1.0:       # what-if: longer tail lever (scaled about the tail axis)
        ax = np.array([0, 0.048, -0.005])
        tail.vertices = ax + (tail.vertices - ax) * np.array([1.0, 1.0, TAIL_SCALE])
    files["tail"] = write_hull(tail, "tail.stl")
    legs = {}
    for end, sy in (("F", -1), ("H", 1)):
        a, b = STAND[end]
        for sx, side in ((1, "R"), (-1, "L")):
            hip = np.array([0, sy * HIP_Y, HIP_Z])
            knee = hip + np.array([0, L1 * math.sin(math.radians(a)), -L1 * math.cos(math.radians(a))])
            sel = lambda c: c[0] * sx > 0 and c[1] * sy > 0
            pd = trimesh.util.concatenate(split_by(pods, sel))
            pd.apply_translation(-hip); pd.vertices = pd.vertices @ rotx(-a).T
            sh = trimesh.util.concatenate(split_by(shins, sel))
            sh.apply_translation(-knee); sh.vertices = sh.vertices @ rotx(-b).T
            files[f"pod_{end}{side}"] = write_hull(pd, f"pod_{end}{side}.stl")
            files[f"shin_{end}{side}"] = write_hull(sh, f"shin_{end}{side}.stl")
            legs[end + side] = (sx, sy)
    # ---- masses (kg) from the CAD mass budget
    M = dict(body=0.1152 - 0.0045 + 0.0134, head=0.0716 + 0.0045 - 0.006, ears=0.006, tail=0.0081, thigh=0.0378, shin=0.0030)
    ear_c = "1" if EARS == "rigid" else "0"
    xml = f"""
<mujoco model="tarcin">
  <compiler angle="degree" meshdir="{OUT}"/>
  <option timestep="0.0005" integrator="implicitfast" gravity="0 0 -9.81"/>
  <default>
    <geom friction="0.6 0.005 0.0001" condim="3" solref="0.004 1" solimp="0.9 0.95 0.001"/>
    <joint damping="0.012" armature="0.0004"/>
    <position kp="3.0" forcerange="-{TAU_MAX} {TAU_MAX}" forcelimited="true"/>
  </default>
  <asset>
""" + "".join(f'    <mesh name="{k}" file="{v}"/>\n' for k, v in files.items()) + f"""
  </asset>
  <worldbody>
    <geom name="floor" type="plane" size="1 1 0.1" friction="0.6 0.005 0.0001"/>
    <body name="torso" pos="0 0 {HIP_Z + 0.002}">
      <freejoint/>
      <geom type="mesh" mesh="body" mass="0.024"/>
      <geom type="capsule" fromto="0 -0.015 -0.0034 0 0.035 -0.0034" size="0.012" mass="0.039" contype="0" conaffinity="0" rgba="0 1 0 0.3"/>
      <geom type="box" pos="0 0.005 0" size="0.013 0.03 0.012" mass="{M['body'] - 0.024 - 0.039:.4f}" contype="0" conaffinity="0"/>
      <body name="tail" pos="0 0.048 -0.005">
        <joint name="tail" type="hinge" axis="0 1 0" range="-85 85"/>
        <geom type="mesh" mesh="tail" pos="0 -0.048 0.005" mass="{M['tail']}" contype="{TAILC}" conaffinity="{TAILC}"/>
      </body>
      <body name="head" pos="0 -0.032 0">
        <joint name="pan" type="hinge" axis="0 0 1" range="-40 40"/>
        <geom type="mesh" mesh="head" pos="0 0.032 0" mass="{M['head']:.4f}"/>
        <geom type="mesh" mesh="ear_p" pos="0 0.032 0" mass="0.003" contype="{ear_c}" conaffinity="{ear_c}"/>
        <geom type="mesh" mesh="ear_n" pos="0 0.032 0" mass="0.003" contype="{ear_c}" conaffinity="{ear_c}"/>
      </body>
"""
    for name, (sx, sy) in legs.items():
        end, side = name[0], name[1]
        hr = HIP_RANGE[end]
        kr = KNEE_RANGE[end]
        xml += f"""
      <body name="thigh_{name}" pos="0 {sy * HIP_Y} 0">
        <joint name="hip_{name}" type="hinge" axis="1 0 0" range="{hr}"/>
        <geom type="mesh" mesh="pod_{name}" mass="{M['thigh']}" friction="0.5 0.005 0.0001"/>
        <body name="shin_{name}" pos="0 0 {-L1}">
          <joint name="knee_{name}" type="hinge" axis="1 0 0" range="{kr}"/>
          <geom type="mesh" mesh="shin_{name}" mass="{M['shin']}" friction="1.0 0.005 0.0001"/>
        </body>
      </body>
"""
    xml += """
    </body>
  </worldbody>
  <actuator>
    <position name="pan" joint="pan" ctrlrange="-40 40" kp="1.0"/>
    <position name="tail" joint="tail" ctrlrange="-85 85"/>
"""
    for name in legs:
        end = name[0]
        hr = HIP_RANGE[end]
        kr = KNEE_RANGE[end]
        xml += f'    <position name="hip_{name}" joint="hip_{name}" ctrlrange="{hr}"/>\n'
        xml += f'    <position name="knee_{name}" joint="knee_{name}" ctrlrange="{kr}"/>\n'
    xml += "  </actuator>\n</mujoco>\n"
    open(os.path.join(OUT, "tarcin.xml"), "w").write(xml)
    return xml


LEGS = ["FR", "FL", "HR", "HL"]


def pose_targets(spec):
    """spec: dict leg -> (a, b) absolute angles in degrees; returns joint-space targets in radians (hip, knee)."""
    t = {}
    for leg, (a, b) in spec.items():
        t["hip_" + leg] = math.radians(a)
        t["knee_" + leg] = math.radians(b - a)
    return t


def stand_spec():
    return {leg: STAND[leg[0]] for leg in LEGS}


class Runner:
    def __init__(self, model):
        self.m = model
        self.d = mujoco.MjData(model)
        self.act = {model.actuator(i).name: i for i in range(model.nu)}
        self.jq = {}
        for i in range(model.nu):
            j = model.actuator_trnid[i, 0]
            self.jq[model.actuator(i).name] = model.jnt_qposadr[j]
        self.target = {}
        self.log = []

    def set_orientation(self, roll_deg, pitch_deg=0.0, yaw_deg=0.0, z=None):
        d = self.d
        mujoco.mj_resetData(self.m, d)
        q = np.zeros(4)
        mujoco.mju_euler2Quat(q, np.radians([roll_deg, pitch_deg, yaw_deg]), "XYZ")
        # body long axis is Y: 'roll' about Y lays it on its side
        qy = np.zeros(4); mujoco.mju_axisAngle2Quat(qy, np.array([0, 1.0, 0]), math.radians(roll_deg))
        qx = np.zeros(4); mujoco.mju_axisAngle2Quat(qx, np.array([1.0, 0, 0]), math.radians(pitch_deg))
        qq = np.zeros(4); mujoco.mju_mulQuat(qq, qx, qy)
        d.qpos[3:7] = qq
        d.qpos[2] = 0.12 if z is None else z
        for name, adr in self.jq.items():
            if name.startswith("hip_") or name.startswith("knee_"):
                leg = name.split("_")[1]
                a, b = STAND[leg[0]]
                d.qpos[adr] = math.radians(a) if name.startswith("hip") else math.radians(b - a)
        self.target = {n: d.qpos[self.jq[n]] for n in self.act}
        for n, i in self.act.items():
            d.ctrl[i] = self.target[n]
        mujoco.mj_forward(self.m, d)

    def axes(self):
        R = self.d.xmat[1].reshape(3, 3)     # torso
        return R[:, 0], R[:, 1], R[:, 2]

    def step_to(self, tgt, duration, vmax=VMAX):
        """move actuator targets toward tgt with a speed limit (servo-like), for 'duration' seconds"""
        n = int(duration / self.m.opt.timestep)
        cur = {k: self.d.ctrl[self.act[k]] for k in self.act}
        for s in range(n):
            for k, v in tgt.items():
                c = cur[k]
                dv = max(-vmax * self.m.opt.timestep, min(vmax * self.m.opt.timestep, v - c))
                cur[k] = c + dv
                self.d.ctrl[self.act[k]] = cur[k]
            mujoco.mj_step(self.m, self.d)
            if s % 40 == 0:
                x, y, z = self.axes()
                self.log.append(dict(t=round(self.d.time, 3), up=round(float(z[2]), 3), side=round(float(x[2]), 3),
                                     h=round(float(self.d.qpos[2]), 4),
                                     q={k: round(math.degrees(float(self.d.qpos[self.jq[k]])), 1) for k in self.act}))

    def upright(self):
        return self.axes()[2][2] > 0.85


def recover(r, max_tries=6, verbose=False):
    """OpenCat-'rc'-style recovery, adapted to this body: the long TAIL (MG90S, rotates about the body's long axis)
    is the roll lever; legs tuck so the pods don't prop the body; closed loop on the IMU 'up' value.
    Mirrored by the side that is down; alternates direction on retries (like OpenCat's coin-flip mirroring)."""
    st = pose_targets(stand_spec()); st["tail"] = 0.0; st["pan"] = 0.0
    tuck = {leg: ((20, -24) if leg[0] == "F" else (-20, 24)) for leg in LEGS}
    for attempt in range(max_tries):
        x, y, z = r.axes()
        if z[2] > 0.85:
            break
        if abs(x[2]) > 0.35:
            down = 1 if x[2] < 0 else -1          # +1: the +x flank is on the floor
        else:
            down = 1 if attempt % 2 == 0 else -1   # on its back: pick a side, alternate on retries
        # sweep the tail toward the floor side until the body has rolled past ~70 deg from the floor
        tg = pose_targets(tuck); tg["pan"] = 0.0
        for ang in range(0, 86, 5):
            tg["tail"] = math.radians(ang * down)
            r.step_to(tg, 0.05)
            x, y, z = r.axes()
            if z[2] > 0.35:
                break
        r.step_to(tg, 0.25)
        # tail back to centre while the legs catch and stand
        r.step_to(st, 0.6)
        r.step_to(st, 0.5)
        if verbose:
            x, y, z = r.axes(); print("   attempt", attempt, "up", round(float(z[2]), 2))
    return r.upright(), attempt + 1


def main():
    build_xml()
    model = mujoco.MjModel.from_xml_path(os.path.join(OUT, "tarcin.xml"))
    total_mass = float(sum(model.body_mass))
    res = {"ears": EARS, "tail_scale": TAIL_SCALE, "total_mass_kg": round(total_mass, 4), "cases": []}
    r = Runner(model)
    # sanity: standing still for 1.5 s
    r.set_orientation(0, z=HIP_Z + 0.004)
    r.step_to(pose_targets(stand_spec()), 1.5)
    res["stand_ok"] = bool(r.upright())
    res["stand_height_mm"] = round(float(r.d.qpos[2]) * 1000, 1)
    # torque in quiet stance
    tq = {model.actuator(i).name: round(float(r.d.actuator_force[i]), 4) for i in range(model.nu)}
    res["stand_torque_Nm"] = tq
    rng = np.random.default_rng(1)
    cases = [("side +x down", 90, 0), ("side -x down", -90, 0), ("on back", 180, 0), ("back, nose-down 20", 180, 20),
             ("side +x, nose-up 25", 90, -25), ("side -x, nose-down 25", -90, 25)]
    for i in range(6):
        cases.append((f"random {i}", float(rng.uniform(-180, 180)), float(rng.uniform(-40, 40))))
    for name, roll, pitch in cases:
        r = Runner(model)
        r.set_orientation(roll, pitch)
        r.step_to(r.target, 1.2)          # let it fall and settle
        x, y, z = r.axes()
        settled = dict(up=round(float(z[2]), 2), side=round(float(x[2]), 2))
        ok, tries = recover(r)
        peak = max(abs(float(f)) for f in r.d.actuator_force)
        res["cases"].append(dict(case=name, settled=settled, ok=bool(ok), tries=tries, t_end=round(r.d.time, 2)))
        json.dump(r.log, open(os.path.join(OUT, f"log_{name.replace(' ', '_').replace(',', '')}.json"), "w"))
    res["success_rate"] = f"{sum(c['ok'] for c in res['cases'])}/{len(res['cases'])}"
    json.dump(res, open(os.path.join(OUT, f"result_{EARS}_tail{TAIL_SCALE}.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
