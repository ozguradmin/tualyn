#!/usr/bin/env python3
"""Build the MuJoCo model of Findik (package C) from the package's own model.glb.

The MJCF mirrors the GLB link frames exactly (same origins, axes, zero), so joint angles and base
poses recorded in the sim replay 1:1 in rig.js:
  body (free joint, frame = GLB root: origin on the floor under the egg centre at rest, Z up, faces -Y)
  leg_<k>  hinge on the MG90S spline axis, axis = manifest axis, 0 = arm straight down
  wheel_<k> hinge on the axle, axis +X, + = rolls forward (-Y)
Collision: convex hulls of the real link meshes (egg shell hull, 2 ear hulls, arm+boot hull per leg),
tyres as cylinders (r 15, w 6.8).  Contact body<->legs/wheels is excluded: the shell has sculpted
socket reliefs that a convex hull would fill (CAD check: 0 mm^3 interference standing, 0.4 mm^3 tucked).
Masses: concept mass breakdown (concept_C2/stl/info.json, 300.9 g) distributed onto the real meshes:
thin-shell inertia for the printed shell, solid inertia for internals, legs from CAD volume x density.

usage: python3 -I build_mjcf.py  -> writes meshes/*.stl, findik_base.xml (template) and mass_report.json
"""
import json, os
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
OUT_M = os.path.join(HERE, "meshes")
os.makedirs(OUT_M, exist_ok=True)

scene = trimesh.load(os.path.join(PKG, "model.glb"))
G = {}
for n in scene.graph.nodes_geometry:
    T, gn = scene.graph.get(n)
    G[n] = scene.geometry[gn]            # vertices already in the link's local frame (mm)
LINKPOS = {n: scene.graph.get(n)[0][:3, 3].copy() for n in
           ["leg_fl", "leg_fr", "leg_rl", "leg_rr", "wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"]}
man = json.load(open(os.path.join(PKG, "manifest.json")))
J = man["joints"]

MM = 1e-3
PLA = 1.24e-3            # g/mm^3

def shell_props(meshes, mass):
    """thin-shell (area weighted) com and inertia about com, kg m^2, in mm frame -> SI"""
    P, A = [], []
    for m in meshes:
        tri = m.triangles
        P.append(tri.mean(axis=1)); A.append(m.area_faces)
    P = np.vstack(P) * MM; A = np.concatenate(A)
    w = A / A.sum() * mass
    c = (P * w[:, None]).sum(0) / mass
    d = P - c
    I = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            I[i, j] = -(w * d[:, i] * d[:, j]).sum()
    I += np.eye(3) * (w * (d ** 2).sum(1)).sum()
    return c, I

def solid_props(mesh, mass):
    m = mesh if mesh.is_watertight else mesh.convex_hull
    c = m.center_mass * MM
    I = m.moment_inertia / m.volume * mass * MM ** 2   # trimesh moment_inertia uses density 1 (mm^5)
    return c, I

def combine(parts):
    M = sum(p[0] for p in parts)
    c = sum(p[0] * p[1] for p in parts) / M
    I = np.zeros((3, 3))
    for m, ci, Ii in parts:
        d = ci - c
        I += Ii + m * (np.dot(d, d) * np.eye(3) - np.outer(d, d))
    return M, c, I

report = {}
# ------------------------------------------------------------------ body mass model (kg)
g = lambda x: x * 1e-3
bodyparts = []
bodyparts.append((g(55.5),) + shell_props([G[k] for k in ("body__cream", "body__cap", "body__ear",
                                            "body__ear_inner", "body__visor", "body__nose")], g(55.5)))
for key, grams in (("body__internal_servo", 53.6), ("body__internal_battery", 42.0), ("body__internal_pcb_esp", 8.0),
                   ("body__internal_lcd", 14.0), ("body__internal_speaker", 7.0), ("body__internal_pcb", 16.0),
                   ("body__tcrt_body", 6.0), ("body__internal_chassis", 8.7), ("body__internal_magnet", 2.0)):
    bodyparts.append((g(grams),) + solid_props(G[key], g(grams)))
leg_mass = {}
for k in ("fl", "fr", "rl", "rr"):
    rear = k[0] == "r"
    arm = G[f"leg_{k}__arm"].volume * PLA * 0.55          # 50 % gyroid + 3 walls
    extra = 0.8 + (10.5 if rear else 1.0)                    # horn+screw, N20+wires or M3 shoulder axle
    wheel = G[f"wheel_{k}__hub"].volume * PLA * 0.8 + G[f"wheel_{k}__hubcap"].volume * PLA + 0.3 \
        + G[f"wheel_{k}__tyre"].volume * 1.21e-3
    leg_mass[k] = (arm, extra, wheel)
legs_total = sum(a + e + w for a, e, w in leg_mass.values())
known = sum(p[0] for p in bodyparts) * 1e3
rest_g = 300.9 - legs_total - known                         # wires, screws, inserts, caps: lumped at the deck
deck = trimesh.creation.box(extents=(50, 36, 14)); deck.apply_translation((0, 6.0, 55.0 + 14.52))   # as concept model.py
bodyparts.append((g(rest_g),) + solid_props(deck, g(rest_g)))
MB, CB, IB = combine(bodyparts)
report["body_g"] = MB * 1e3
report["misc_spread_g"] = rest_g
report["legs_g"] = {k: [round(x, 2) for x in v] for k, v in leg_mass.items()}

# ------------------------------------------------------------------ collision hulls
def save_hull(mesh, name, maxv=None):
    h = mesh.convex_hull
    if maxv and len(h.vertices) > maxv:
        try:
            import fast_simplification  # noqa
            h = h.simplify_quadric_decimation(face_count=maxv * 2).convex_hull
        except Exception:
            pass
    hs = h.copy(); hs.apply_scale(MM)
    hs.export(os.path.join(OUT_M, name + ".stl"))
    return h

egg_h = save_hull(trimesh.util.concatenate([G[k] for k in ("body__cream", "body__cap", "body__visor", "body__nose")]), "egg")
ear = G["body__ear"]
for side, nm in ((1, "earL"), (-1, "earR")):
    v = ear.vertices[ear.vertices[:, 0] * side > 0]
    save_hull(trimesh.PointCloud(v), nm)
for k in ("fl", "fr", "rl", "rr"):
    save_hull(G[f"leg_{k}__arm"], f"arm_{k}")
report["egg_hull_vertices"] = int(len(egg_h.vertices))

# ------------------------------------------------------------------ leg/wheel inertials (local frames)
def leg_inertial(k):
    arm = G[f"leg_{k}__arm"]
    a, e, w = leg_mass[k]
    parts = [(g(a),) + solid_props(arm, g(a))]
    if k[0] == "r":
        parts.append((g(e),) + solid_props(G[f"leg_{k}__internal_motor"], g(e)))
    else:
        parts.append((g(e),) + solid_props(G[f"leg_{k}__internal_shaft"], g(e)))
    return combine(parts)

def wheel_inertial(k):
    a, e, w = leg_mass[k]
    m = g(w)
    r = 0.0128
    Ixx = 0.6 * m * r * r                     # hub disc + heavier TPU rim
    Iyy = Ixx / 2 + m * 0.0068 ** 2 / 12
    return m, np.zeros(3), np.diag([Ixx, Iyy, Iyy])

def fmt(v):
    return " ".join(f"{x:.7g}" for x in v)

def inertial_xml(M, c, I):
    return (f'<inertial pos="{fmt(c)}" mass="{M:.6g}" '
            f'fullinertia="{I[0,0]:.6g} {I[1,1]:.6g} {I[2,2]:.6g} {I[0,1]:.6g} {I[0,2]:.6g} {I[1,2]:.6g}"/>')

legs_xml = []
for k in ("fl", "fr", "rl", "rr"):
    jn = J["hip_" + k]
    lp = LINKPOS["leg_" + k] * MM
    wp = (LINKPOS["wheel_" + k] - LINKPOS["leg_" + k]) * MM
    Ml, cl, Il = leg_inertial(k)
    Mw, cw, Iw = wheel_inertial(k)
    driven = k[0] == "r"
    report[f"leg_{k}_g"] = Ml * 1e3; report[f"wheel_{k}_g"] = Mw * 1e3
    legs_xml.append(f"""
    <body name="leg_{k}" pos="{fmt(lp)}">
      {inertial_xml(Ml, cl, Il)}
      <joint name="hip_{k}" type="hinge" axis="{fmt(jn['axis'])}" range="{jn['min']} {jn['max']}" limited="true"
             armature="5e-5" damping="0.002" frictionloss="0.004"/>
      <geom name="arm_{k}" type="mesh" mesh="arm_{k}" class="shell"/>
      <body name="wheel_{k}" pos="{fmt(wp)}">
        {inertial_xml(Mw, cw, Iw)}
        <joint name="wheel_{k}" type="hinge" axis="1 0 0" {'armature="5e-5" damping="0.0005" frictionloss="0.006"' if driven else 'armature="1e-7" damping="2e-6" frictionloss="3e-5"'}/>
        <geom name="tyre_{k}" type="cylinder" size="0.015 0.0034" zaxis="1 0 0" class="tyre"/>
      </body>
    </body>""")

xml = f"""<mujoco model="findik">
  <compiler angle="degree" autolimits="true"/>
  <option timestep="0.001" integrator="implicitfast" cone="elliptic" noslip_iterations="0"/>
  <size memory="20M"/>
  <visual><global offwidth="800" offheight="600"/></visual>
  <asset>
    <mesh name="egg" file="meshes/egg.stl"/>
    <mesh name="earL" file="meshes/earL.stl"/>
    <mesh name="earR" file="meshes/earR.stl"/>
    <mesh name="arm_fl" file="meshes/arm_fl.stl"/>
    <mesh name="arm_fr" file="meshes/arm_fr.stl"/>
    <mesh name="arm_rl" file="meshes/arm_rl.stl"/>
    <mesh name="arm_rr" file="meshes/arm_rr.stl"/>
  </asset>
  <default>
    <geom solref="0.004 1" solimp="0.95 0.99 0.0005"/>
    <default class="shell"><geom friction="@MU_SHELL@ 0.005 0.0001" priority="0" condim="3" rgba="0.9 0.85 0.75 1"/></default>
    <default class="tyre"><geom friction="@MU_TYRE@ 0.005 0.0001" priority="2" condim="4" solref="0.015 1" solimp="0.9 0.95 0.001" rgba="0.1 0.1 0.1 1"/></default>
  </default>
  <worldbody>
    <light pos="0 -0.3 0.5" dir="0 0.5 -1"/>
    <geom name="floor" type="plane" size="2 2 0.01" friction="@MU_FLOOR@ 0.005 0.0001" priority="1" rgba="0.8 0.8 0.8 1"/>
    <body name="body" pos="0 0 0">
      <freejoint name="base"/>
      {inertial_xml(MB, CB, IB)}
      <geom name="egg" type="mesh" mesh="egg" class="shell"/>
      <geom name="earL" type="mesh" mesh="earL" class="shell"/>
      <geom name="earR" type="mesh" mesh="earR" class="shell"/>
      <site name="imu" pos="0 0.004 0.05"/>{''.join(legs_xml)}
    </body>
  </worldbody>
  <contact>
    <exclude body1="body" body2="wheel_fl"/><exclude body1="body" body2="wheel_fr"/>
    <exclude body1="body" body2="wheel_rl"/><exclude body1="body" body2="wheel_rr"/>
  </contact>
  <actuator>
    <motor name="m_hip_fl" joint="hip_fl" ctrlrange="-0.2 0.2"/>
    <motor name="m_hip_fr" joint="hip_fr" ctrlrange="-0.2 0.2"/>
    <motor name="m_hip_rl" joint="hip_rl" ctrlrange="-0.2 0.2"/>
    <motor name="m_hip_rr" joint="hip_rr" ctrlrange="-0.2 0.2"/>
    <motor name="m_wheel_rl" joint="wheel_rl" ctrlrange="-0.1 0.1"/>
    <motor name="m_wheel_rr" joint="wheel_rr" ctrlrange="-0.1 0.1"/>
  </actuator>
</mujoco>
"""
open(os.path.join(HERE, "findik_base.xml"), "w").write(xml)
# total CoM at the stand pose is checked in sim_lib (needs FK); store body numbers here
report["body_com_mm"] = (CB * 1e3).round(2).tolist()
report["total_g_nominal"] = 300.9
json.dump(report, open(os.path.join(HERE, "mass_report.json"), "w"), indent=1)
print(json.dumps(report, indent=1))
