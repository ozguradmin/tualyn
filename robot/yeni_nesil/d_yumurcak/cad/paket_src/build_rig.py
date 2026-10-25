#!/usr/bin/env python3
"""Build the articulated model.glb for package D (Yumurcak, the walking egg).

Geometry = concept_D2/model.py (copied verbatim as model_base.py), re-split per LINK at joint zero:
  body                 lower egg bowl (+ seam lip), ToF window, USB-C, slide switch, belly screws, internals
  head                 upper egg above the 12 deg oblique seam: shell, smoked visor, black eye pocket, eggshell
                       cap, two GC9A01 screens (flat, real depth), SG90 + hub (internal)
  haunch_<leg>         41 mm ball (two hemispheres, equator seam), knee MG90S inside; hip-yaw joint (vertical)
  paw_<leg>            48 mm bean paw + TPU sole + horn screw; knee joint (axis along +-Y)
Legs: fl/fr/bl/br, robot's LEFT = +X (robot faces -Y).

Frames (world): mm, Z up, faces -Y, origin on the ground under the egg centre. body node = identity.
Concept body frame C (bottom-sphere centre) = world - (0,0,CZ). CZ is set so that the TPU soles touch Z=0
with the knees at 30 deg (pose_rest), exactly like the concept's "stand" pose.

Joint conventions (positive directions, all legs mirror-symmetric):
  knee_<leg>  + = paw swings OUTWARD/UP (0 = paw straight down, 30 = stand, 178 = folded "egg" mode)
  yaw_<leg>   + = the knee knuckle swings OUTWARD (towards the robot's side)
  head        + = head turns to the robot's LEFT (about the 12 deg tilted axis)

usage: python3 -I build_rig.py      -> ../model.glb, rig_info.json
"""
import json, math, os, shutil, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.argv = [sys.argv[0]]
exec(open(os.path.join(HERE, "model_base.py")).read(), globals())
import numpy as np
import trimesh

TMP = tempfile.mkdtemp(dir=HERE)
_n = [0]


def tess(part, tol=0.05, ang=0.15):
    _n[0] += 1
    f = os.path.join(TMP, f"p{_n[0]}.stl")
    export_stl(part, f, tolerance=tol, angular_tolerance=ang)
    m = trimesh.load(f, force="mesh")
    m.merge_vertices()
    os.remove(f)
    return m


def T_from(origin, x_dir, z_dir):
    x = np.array(x_dir, float); x /= np.linalg.norm(x)
    z = np.array(z_dir, float); z /= np.linalg.norm(z)
    y = np.cross(z, x)
    M = np.eye(4); M[:3, 0] = x; M[:3, 1] = y; M[:3, 2] = z; M[:3, 3] = origin
    return M


def tr(m, M):
    m = m.copy(); m.apply_transform(M); return m


def mirror_x(m):
    m = m.copy(); m.vertices[:, 0] *= -1; m.faces = m.faces[:, ::-1].copy(); return m


LM = {}          # (link, mat) -> list of meshes in concept frame C


def add(link, mat, m):
    LM.setdefault((link, mat), []).append(m)


def rbox(sx_, sy_, sz_, r):
    b = Box(sx_, sy_, sz_)
    try:
        b = fillet(b.edges().filter_by(Axis.Y), r)
    except Exception:
        pass
    return b


LEGS = {"fr": (-24.0, -24.0), "fl": (24.0, -24.0), "br": (-24.0, 24.0), "bl": (24.0, 24.0)}
KNUCKLE_OFF = FLAT + 6.8                       # knee-axis point distance from the yaw axis along +-Y

# ------------------------------------------------------------------ paw (local, joint 0 = straight down)
paw_m = tess(FOOT, 0.04, 0.15)
sole_m = tess(SOLE, 0.04, 0.15)
# horn screw: M2 pan head in a 3 mm counterbore on the knuckle's outer face (local +Y face, y = +6.5)
cb = Pos(0, 6.5 - 1.5, 0) * Rot(90, 0, 0) * Cylinder(2.3, 3.2)
paw_cb = FOOT - cb
paw_m = tess(paw_cb, 0.04, 0.15)
head_s = Rot(-90, 0, 0) * Cylinder(1.9, 1.2, align=(Align.CENTER, Align.CENTER, Align.MIN))   # along +Y
head_s = Pos(0, 6.5 - 3.0, 0) * head_s
slot = Pos(0, 6.5 - 3.0 + 1.2, 0) * (Box(2.6, 1.0, 0.5) + Box(0.5, 1.0, 2.6))
screw_paw = tess(head_s - slot, 0.02, 0.2)

def sole_low(beta, sx=1):
    v = sole_m.vertices.copy()
    a = math.radians(beta)
    # Rot about local Y by -beta (outward for sx=+1): x' = x cos - z sin? use matrix
    R = trimesh.transformations.rotation_matrix(-a, [0, 1, 0])[:3, :3]
    return (v @ R.T)[:, 2].min()

STAND = 30.0
CZ = -(KNEE_Z + sole_low(STAND))
print("CZ", CZ, "(concept stand CZ 77.279)")

# ------------------------------------------------------------------ body link
lip = (revolve_profile(prof(WALL)) - revolve_profile(prof(WALL + 1.4))) \
    & halfspace(NV, D_SEAM - GAP / 2 - 3.0, True) & halfspace(NV, D_SEAM + 2.4, False)
# 45 deg x ~0.6 mm chamfers on both seam edges (V reveal around the 0.8 mm gap): ring revolved about the head axis
_rs = math.sqrt(R * R - D_SEAM * D_SEAM)
_v = Polygon((_rs + 1.5, D_SEAM - 2.5), (_rs + 1.5, D_SEAM + 2.5), (_rs - 1.0, D_SEAM), align=None)
SEAM_V = Rot(ALPHA, 0, 0) * revolve(Plane.XZ * _v, Axis.Z, 360)
bs = body_shell + lip - SEAM_V
# USB-C port is cut in the concept; slide-switch slot under it
bs = bs - Pos(0, 40, -28.0) * Box(8.2, 10, 3.8)
# 4 x M2 countersunk belly screws (the only screws visible from outside apart from the 4 paw horn screws)
BELLY = [(0, -20), (0, 20), (-20, 0), (20, 0)]
screw_heads = []
for (bx, by) in BELLY:
    bz = -math.sqrt(R * R - bx * bx - by * by)
    n = Vector(bx, by, bz).normalized()
    p = Vector(bx, by, bz)
    xd = Vector(1, 0, 0) if abs(n.X) < 0.9 else Vector(0, 1, 0)
    pl = Plane(origin=p, x_dir=xd, z_dir=n)
    cs = pl.location * Pos(0, 0, -1.2) * Cone(1.0, 2.2, 1.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
    bs = bs - cs - pl.location * Pos(0, 0, -6) * Cylinder(1.1, 6, align=(Align.CENTER, Align.CENTER, Align.MIN))
    hd = pl.location * Pos(0, 0, -1.2) * Cone(1.0, 1.9, 1.12, align=(Align.CENTER, Align.CENTER, Align.MIN))
    hd = hd - pl.location * Pos(0, 0, -0.2) * (Box(2.6, 0.5, 0.8) + Box(0.5, 2.6, 0.8))
    screw_heads.append(hd)
add("body", "shell", tess(bs, 0.025, 0.1))
add("body", "lens", tess(lens, 0.03, 0.2))
for hd in screw_heads:
    add("body", "screw", tess(hd, 0.02, 0.25))
# USB-C receptacle (8.94 x 3.26 stainless shell) in the back port, mouth 0.8 mm under the surface
usb_o = Pos(0, 40.3, -20.5) * rbox(8.94, 4.6, 3.26, 1.5)
usb_i = Pos(0, 40.8, -20.5) * rbox(8.34, 4.6, 2.66, 1.2)
add("body", "usb_metal", tess(usb_o - usb_i, 0.02, 0.2))
add("body", "black", tess(Pos(0, 40.0, -20.5) * Box(6.6, 3.0, 0.7) + Pos(0, 38.4, -20.5) * Box(8.3, 0.4, 2.6), 0.02, 0.2))
# 2S USB-C charger PCB face behind the port (closes the 10 x 4 mm cut-out around the receptacle)
add("body", "black", tess(Pos(0, 38.0, -20.5) * Box(11.5, 0.8, 6.0), 0.05, 0.3))
# IC205 (SS12D00-class) 3-pin slide switch, Robotistan: 10.5 x 5.7 mm body, knob through the 8.2 x 3.8 slot.
# It only switches the gate of an IRF4905 P-MOSFET (high-side main switch), so no battery current flows through it.
add("body", "black", tess(Pos(-1.3, 38.6, -28.0) * Box(2.6, 3.2, 1.6), 0.02, 0.2))
add("body", "black", tess(Pos(0, 33.8, -28.0) * Box(10.5, 3.6, 5.7), 0.05, 0.3))   # switch body closes the slot (inside the 1.6 mm wall)

# internals
MG = tess(mg90s(False), 0.05, 0.3)
SG = tess(sg90(), 0.05, 0.3)
HORN8 = tess(horn(8.0), 0.05, 0.3)
HORN65 = tess(horn(6.5), 0.05, 0.3)
for k, (x, y) in LEGS.items():
    add("body", "internal_servo", tr(MG, T_from((x, y, POCKET + 4.2), (-x, -y, 0), (0, 0, -1))))
add("body", "internal_battery", tess(union(cells), 0.05, 0.3))
add("body", "internal_frame", tess(deck + collars + posts + post_head + sled, 0.05, 0.3))
add("body", "internal_pcb", tess(mcu, 0.05, 0.3))
add("body", "internal_pcb", tess(bucks + charger + bms + imu + tof, 0.05, 0.3))
for (bx, by) in BELLY:       # bosses the belly screws bite into (part of the printed deck/cell cradle)
    bz = -math.sqrt(R * R - bx * bx - by * by)
    add("body", "internal_frame", tess(Pos(bx, by, bz + 1.6) * Cylinder(2.6, 5.0, align=(Align.CENTER, Align.CENTER, Align.MIN)), 0.05, 0.3))

# ------------------------------------------------------------------ head link
hs = head_shell - vis_out - SEAM_V
add("head", "shell", tess(hs, 0.025, 0.1))
add("head", "visor", tess(visor, 0.03, 0.12))
add("head", "cap", tess(cap, 0.05, 0.15))
# black eye pocket behind the visor (printed in matte black PLA), holes show the GC9A01 glass + dark ring
in_a = revolve_profile(prof(WALL + 0.25))
in_b = revolve_profile(prof(WALL + 1.45))
mask = (in_a - in_b) & stadium_prism(VW + 4, VH + 4, 18.6, VZ) & halfspace(Vector(0, -1, 0), 8, True)
EYES = {}
for side, sx in (("eyeR", -1), ("eyeL", 1)):          # eyeL = robot's LEFT eye (+X, viewer's right)
    p, n, _ = eye_frame(sx)
    nn = np.array([n.X, n.Y, n.Z]); pp = np.array([p.X, p.Y, p.Z])
    u = np.cross([0, 0, 1], nn); u /= np.linalg.norm(u); v = np.cross(nn, u)
    EYES[side] = (pp, nn, u, v)
    pl = Plane(origin=p, x_dir=Vector(*u), z_dir=n)
    mask = mask - pl.location * Pos(0, 0, -20) * Cylinder(17.3, 30, align=(Align.CENTER, Align.CENTER, Align.MIN))
    sleeve = pl.location * Pos(0, 0, -6.3) * (Cylinder(18.9, 5.6, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                              - Cylinder(17.3, 5.6, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    mask = mask + (sleeve & in_a)
    # GC9A01 module: PCB 38.6 dia (blue), glass 35.5 dia, glass front 6.4 mm behind the egg surface
    add("head", "internal_pcb_disp", tess(pl.location * Pos(0, 0, -9.8) * Cylinder(19.3, 1.6, align=(Align.CENTER, Align.CENTER, Align.MIN))
                                          + pl.location * Pos(0, -17, -12.0) * Box(12, 4, 3), 0.05, 0.3))
    add("head", "internal_lcd", tess(pl.location * Pos(0, 0, -8.2) * Cylinder(17.75, 1.75, align=(Align.CENTER, Align.CENTER, Align.MIN)), 0.05, 0.3))
add("head", "mask", tess(mask, 0.05, 0.15))
# screen glass: flat disc, 35.5 mm glass, UV so that the 32.4 mm active circle = the unit circle
SCREEN_DISC = {}
for side, (pp, nn, u, v) in EYES.items():
    N = 128
    c = pp - nn * 6.38
    th = np.linspace(0, 2 * np.pi, N, endpoint=False)
    rg = 35.5 / 2
    ring = c + rg * (np.cos(th)[:, None] * u + np.sin(th)[:, None] * v)
    verts = np.vstack([c, ring])
    uv = np.vstack([[0.5, 0.5], np.stack([0.5 + rg * np.cos(th) / 32.4, 0.5 + rg * np.sin(th) / 32.4], 1)])
    faces = [[0, 1 + i, 1 + (i + 1) % N] for i in range(N)]
    m = trimesh.Trimesh(verts, faces, process=False)
    uv_t = uv.copy(); uv_t[:, 1] = 1.0 - uv_t[:, 1]       # trimesh flips V on glTF export
    m.visual = trimesh.visual.TextureVisuals(uv=uv_t)
    SCREEN_DISC[side] = m
add("head", "internal_servo", tess(head_servo, 0.05, 0.3))
add("head", "internal_frame", tess(head_hub, 0.05, 0.3))
for a in (60, 240):          # 2 x 6x2 mm cap magnets under the crown (cap is swappable)
    mx, my = 14 * math.cos(math.radians(a)), 14 * math.sin(math.radians(a))
    add("head", "internal_magnet", tess(Pos(mx, my, egg_r(0) * 0 + 47.0) * Cylinder(3.0, 2.0), 0.05, 0.3))

# ------------------------------------------------------------------ legs
groove = (Sphere(RT + 2) - Sphere(RT - 0.45)) & Box(100, 100, 0.55)
ball = tess(TUR - Pos(0, 0, BZ) * groove, 0.015, 0.08)                 # TUR is already at z = BZ
for k, (x, y) in LEGS.items():
    sx = 1 if x > 0 else -1
    sy = 1 if y > 0 else -1
    hl, pl_ = "haunch_" + k, "paw_" + k
    add(hl, "ball", tr(ball, trimesh.transformations.translation_matrix((x, y, 0))))
    add(hl, "internal_servo", tr(MG, T_from((x, y + sy * 12.1, KNEE_Z), (0, 0, -1), (0, sy, 0))))
    add(hl, "internal_horn", tr(HORN8, T_from((x, y, POCKET + 4.2), (1, 0, 0), (0, 0, -1))))
    Tk = trimesh.transformations.translation_matrix((x, y + sy * KNUCKLE_OFF, KNEE_Z))
    pm, sm, scm = paw_m, sole_m, screw_paw
    if sy < 0:      # screw on the knuckle's OUTER (away from ball) face: local +Y for back legs, -Y for front
        pm, sm, scm = [trimesh.Trimesh(q.vertices * [1, -1, 1], q.faces[:, ::-1]) for q in (pm, sm, scm)]
    if sx < 0:
        pm, sm, scm = mirror_x(pm), mirror_x(sm), mirror_x(scm)
    add(pl_, "paw", tr(pm, Tk))
    add(pl_, "sole", tr(sm, Tk))
    add(pl_, "screw", tr(scm, Tk))
    add(pl_, "internal_horn", tr(HORN65, T_from((x, y + sy * (FLAT - 2.6), KNEE_Z), (1, 0, 0), (0, sy, 0))))

# ------------------------------------------------------------------ frames + scene
ORIG = {"body": np.zeros(3), "head": np.array([P0.X, P0.Y, P0.Z + CZ])}
PARENT = {"head": "body"}
for k, (x, y) in LEGS.items():
    sy = 1 if y > 0 else -1
    ORIG["haunch_" + k] = np.array([x, y, BZ + CZ]); PARENT["haunch_" + k] = "body"
    ORIG["paw_" + k] = np.array([x, y + sy * KNUCKLE_OFF, KNEE_Z + CZ]); PARENT["paw_" + k] = "haunch_" + k

# explicit `body` node under trimesh's implicit 'world' base frame -> `body` is the GLB's only top-level node
scene = trimesh.Scene(base_frame="world")
scene.graph.update(frame_from="world", frame_to="body", matrix=np.eye(4))
for link in ["head"] + [f"{a}_{k}" for k in LEGS for a in ("haunch", "paw")]:
    T = np.eye(4); T[:3, 3] = ORIG[link] - ORIG[PARENT[link]]
    scene.graph.update(frame_from=PARENT[link], frame_to=link, matrix=T)

tri = {}
SMOOTH = {"head__shell", "body__shell", "head__cap"} | {f"haunch_{k}__ball" for k in LEGS}
for (link, mat), ms in LM.items():
    m = trimesh.util.concatenate(ms)
    m.apply_translation([0, 0, CZ])
    m.apply_translation(-ORIG[link])
    nm = f"{link}__{mat}"
    if nm in SMOOTH:
        # weld + smooth-shade the big printed shells: OCCT leaves sliver triangles along the revolve seam and the
        # visor/seam cuts; with rig.js crease normals they showed as a dashed hairline. Explicit normals
        # (35 deg crease, slivers < 10 mm2 ignored when building facets) are exported for these meshes only.
        m.merge_vertices()
        m.update_faces(m.nondegenerate_faces(height=1e-6))
        m.remove_unreferenced_vertices()
        m = trimesh.graph.smooth_shade(m, angle=math.radians(35), facet_minarea=10.0)
        _ = m.vertex_normals
    else:
        m._cache.clear()
    scene.add_geometry(m, node_name=nm, geom_name=nm, parent_node_name=link)
    tri[nm] = len(m.faces)
for side, m in SCREEN_DISC.items():
    m = m.copy(); m.apply_translation([0, 0, CZ]); m.apply_translation(-ORIG["head"])
    nm = f"head__screen_{side}"
    scene.add_geometry(m, node_name=nm, geom_name=nm, parent_node_name="head")
    tri[nm] = len(m.faces)

scene.export(os.path.join(PKG, "model.glb"))
cap_axis = Rot(-7.0, 11.0, 0) * Vertex(0, 0, 1)
info = dict(CZ=CZ, origins={k: v.round(3).tolist() for k, v in ORIG.items()}, parents=PARENT,
            NV=[NV.X, NV.Y, NV.Z], cap_layer_axis=[round(cap_axis.X, 4), round(cap_axis.Y, 4), round(cap_axis.Z, 4)],
            eyes={s: dict(centre_world=(e[0] - e[1] * 6.38 + [0, 0, CZ]).round(2).tolist(), normal=e[1].round(4).tolist())
                  for s, e in EYES.items()},
            triangles=tri, total_triangles=int(sum(tri.values())))
json.dump(info, open(os.path.join(HERE, "rig_info.json"), "w"), indent=1)
print(json.dumps(dict(CZ=CZ, total=info["total_triangles"], cap_axis=info["cap_layer_axis"]), indent=1))
for k in sorted(tri, key=lambda z: -tri[z])[:12]:
    print(k, tri[k])
shutil.rmtree(TMP, ignore_errors=True)
