#!/usr/bin/env python3
"""Fit / collision check for Tosbi (successor of concept_A/check.py, same manifold3d boolean method).

Printed parts come from model.glb (exactly what the viewer shows), named internals from internals.py (the same
solids build_glb.py writes into the GLB). Checks, all as boolean intersection volume (mm3, > 0.5 = collision):
  A  body internals vs each other and vs every body part (static)
  B  head internals vs each other and vs every head part (static)
  C  neck sweep -40..+40 deg: every head part vs every body part (incl. neck servo, stalk plate, body wires)
  D  legs: hip yaw at min/0/max x knee -90..90: leg + foot parts vs body, head and the neighbouring legs
  E  cliff ToF view: sensor axis + 12.5 deg cone vs head (all neck angles), stalk and legs
usage: python3 -I fit_check.py <package_dir> [--quick]  -> writes src/fit_report.json
"""
import itertools, json, math, os, sys
import numpy as np, trimesh, manifold3d as mf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import internals as I

PKG = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else os.path.dirname(HERE)
QUICK = "--quick" in sys.argv
man = json.load(open(os.path.join(PKG, "manifest.json")))
scene = trimesh.load(os.path.join(PKG, "model.glb")); G = scene.graph
HM = 36 * math.sin(math.radians(80)) + 7
LEGS = ("fl", "fr", "rl", "rr")
PARENT = {"body": None, "head": "body", **{f"leg_{l}": "body" for l in LEGS}, **{f"foot_{l}": f"leg_{l}" for l in LEGS}}
OFF = {n: (G.get(n)[0] if PARENT[n] is None else np.linalg.inv(G.get(PARENT[n])[0]) @ G.get(n)[0]) for n in PARENT}
JOINT_OF = {v["node"]: k for k, v in man["joints"].items()}
TOL = 0.5

def to_mf(V, F):
    m = mf.Mesh(vert_properties=np.asarray(V, np.float32), tri_verts=np.asarray(F, np.uint32)); m.merge()
    return mf.Manifold(m)

def solid_mesh(s):
    if isinstance(s, trimesh.Trimesh): return s.copy()
    v, f = s.tessellate(0.08, 0.25)
    return trimesh.Trimesh(np.array([[p.X, p.Y, p.Z] for p in v]), np.array(f), process=True)

class Part:
    def __init__(self, name, link, mesh):
        self.name, self.link, self.mesh = name, link, mesh            # mesh in the link frame
        self.M = to_mf(mesh.vertices, mesh.faces)
        self.ok = self.M.status() == mf.Error.NoError
        if not self.ok:                                                # split concatenated node meshes into bodies
            self.M = None
            subs = [to_mf(b.vertices, b.faces) for b in mesh.split(only_watertight=False)]
            subs = [s for s in subs if s.status() == mf.Error.NoError]
            if subs:
                self.M = subs[0]
                for s in subs[1:]: self.M = self.M + s
                self.ok = True
    def at(self, T):
        return self.M.transform(np.asarray(T, float)[:3, :])

def rot(axis, deg):
    return trimesh.transformations.rotation_matrix(math.radians(deg), axis)

def world(pose):
    T = {}
    for n in ("body", "head", *[f"leg_{l}" for l in LEGS], *[f"foot_{l}" for l in LEGS]):
        L = OFF[n].copy()
        if n in JOINT_OF:
            j = man["joints"][JOINT_OF[n]]
            L = L @ rot(j["axis"], pose.get(JOINT_OF[n], man["pose_rest"].get(JOINT_OF[n], 0)) - j.get("zero", 0))
        T[n] = L if PARENT[n] is None else T[PARENT[n]] @ L
    return T

# ----------------------------------------------------------------- parts
parts = []
named_internal = {"body": set(), "head": set()}
for nm in G.nodes_geometry:
    link, mat = nm.split("__")
    if mat.startswith("internal") and link in ("body", "head") and mat != "internal_servo": continue   # named below
    if mat in ("screen_face",): continue
    p = Part(nm, link, scene.geometry[nm])
    parts.append(p)
UP = trimesh.transformations.translation_matrix((0, 0, HM))
for mk, items in I.body_parts().items():
    for nm, s in items:
        m = solid_mesh(s); m.apply_transform(UP); parts.append(Part(f"body:{nm}", "body", m)); named_internal["body"].add(f"body:{nm}")
def head_internals():
    import build_glb_head_internals as H
    return H.items()
try:
    from internals import head_parts          # optional
    hp = head_parts()
except Exception:
    hp = []
for nm, s in hp:
    parts.append(Part(f"head:{nm}", "head", solid_mesh(s))); named_internal["head"].add(f"head:{nm}")
bad_parts = [p.name for p in parts if not p.ok]
parts = [p for p in parts if p.ok]
P = {p.name: p for p in parts}
print("parts", len(parts), "non-manifold skipped:", bad_parts, flush=True)

# by design: wires run through the hollow stalk / its mount; the neck flex body segment ends in the stalk plate
ALLOW = {("body__internal_wire", "body__stalk"), ("body__internal_wire", "body:stalk_mount"), ("body__internal_wire", "body__shell"),
         ("body__internal_wire", "body:chassis_plate")}
def allowed(a, b):
    if (a, b) in ALLOW or (b, a) in ALLOW: return True
    for x, y in ((a, b), (b, a)):
        # the hip egg is modelled solid and sits on the hip servo's horn/top (concept check.py did not pair them either)
        if x.endswith("__egg") and y == "body__internal_servo": return True
        # knee servo output spline engages the foot cheek (concept check: ~60 mm3 expected)
        if x.startswith("foot_") and y.startswith("leg_") and y.endswith("__internal_servo") and x[5:7] == y[4:6]: return True
        # the stalk is pressed into its printed mount
        if x == "body:stalk_mount" and y == "body__stalk": return True
    return False

def vol(a, Ta, b, Tb):
    x = a.at(Ta) ^ b.at(Tb)
    return float(x.volume())

def check_pairs(pairs, T, tag, out):
    for a, b in pairs:
        if allowed(a.name, b.name): continue
        ba = trimesh.transform_points(a.mesh.bounds, T[a.link]) if False else None
        v = vol(a, T[a.link], b, T[b.link])
        if v > TOL: out.append({"check": tag, "a": a.name, "b": b.name, "mm3": round(v, 1)})

def bbox_overlap(a, Ta, b, Tb, pad=0.5):
    A = trimesh.transform_points(a.mesh.bounding_box.vertices, Ta); B = trimesh.transform_points(b.mesh.bounding_box.vertices, Tb)
    return not ((A.max(0) + pad < B.min(0)).any() or (B.max(0) + pad < A.min(0)).any())

def run_pairs(pairs, pose, tag, out):
    T = world(pose)
    for a, b in pairs:
        if allowed(a.name, b.name): continue
        if not bbox_overlap(a, T[a.link], b, T[b.link]): continue
        v = vol(a, T[a.link], b, T[b.link])
        if v > TOL: out.append({"check": tag, "pose": pose, "a": a.name, "b": b.name, "mm3": round(v, 1)})

report = {"method": "manifold3d boolean intersection volume between closed meshes, > 0.5 mm3 counts", "non_manifold_skipped": bad_parts}
body = [p for p in parts if p.link == "body"]; head = [p for p in parts if p.link == "head"]
body_int = [p for p in body if p.name.startswith("body:") or p.name == "body__internal_servo"]
head_int = [p for p in head if p.name.startswith("head:") or "internal" in p.name]

# A
out = []
pairs = [(a, b) for a, b in itertools.combinations(body_int, 2)] + [(a, b) for a in body_int for b in body if b not in body_int]
run_pairs(pairs, {}, "A body static", out); report["A_body_static"] = out; print("A", out, flush=True)
# B
out = []
pairs = [(a, b) for a, b in itertools.combinations(head_int, 2)] + [(a, b) for a in head_int for b in head if b not in head_int]
run_pairs(pairs, {}, "B head static", out); report["B_head_static"] = out; print("B", out, flush=True)
# C
out = []
necks = [-40, -20, 0, 15, 20, 40] if QUICK else list(range(-40, 41, 5))
for nk in necks:
    run_pairs([(h, b) for h in head for b in body], {"neck": nk}, "C neck sweep", out)
report["C_neck_sweep"] = {"angles": necks, "hits": out}; print("C", out, flush=True)
# D
out = []
legp = {l: [p for p in parts if p.link in (f"leg_{l}", f"foot_{l}")] for l in LEGS}
knees = [-90, -45, 0, 45, 80, 90]
for l in LEGS:
    j = man["joints"][f"hip_{l}"]
    for hip in (j["min"], 0, j["max"]):
        for kn in knees:
            pose = {f"hip_{l}": hip, f"knee_{l}": kn, "neck": 15}
            pairs = [(a, b) for a in legp[l] for b in body + head] + \
                    [(a, b) for a in legp[l] if a.link.startswith("foot") for b in legp[l] if b.link.startswith("leg")]
            run_pairs(pairs, pose, "D leg sweep", out)
report["D_leg_sweep"] = {"hip": "min/0/max per leg", "knee": knees, "hits": out}; print("D", out, flush=True)

# E: cliff ToF view
def raycast_hits(origin, d, meshes):
    hits = []
    O = np.asarray(origin, float); D = np.asarray(d, float)
    for nm, m in meshes:
        tr = m.triangles; v0, e1, e2 = tr[:, 0], tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0]
        pv = np.cross(D, e2); det = np.einsum('ij,ij->i', e1, pv)
        ok = np.abs(det) > 1e-12; inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        tv = O - v0; u = np.einsum('ij,ij->i', tv, pv) * inv
        qv = np.cross(tv, e1); v = (qv @ D) * inv; t = np.einsum('ij,ij->i', e2, qv) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        if hit.any(): hits.append((nm, round(float(t[hit].min()), 1)))
    return hits
E = []
for sg in (-1, 1):
    o, dvec = I.tof_ray(sg)
    o = np.array(o) + np.array([0, 0, HM]); dvec = np.array(dvec)
    # cone rays (half angle 12.5 deg, 8 around the axis)
    a = np.cross(dvec, [1, 0, 0]); a /= np.linalg.norm(a); b = np.cross(dvec, a)
    rays = [dvec] + [math.cos(math.radians(12.5)) * dvec + math.sin(math.radians(12.5)) * (math.cos(t) * a + math.sin(t) * b)
                     for t in np.linspace(0, 2 * math.pi, 9)[:-1]]
    for nk in (-40, -20, 0, 15, 20, 40):
        T = world({"neck": nk})
        meshes = []
        for p in parts:
            if p.link == "body" and (p.name.startswith("body:") or "internal" in p.name or p.name in ("body__shell", "body__lip")): continue
            if p.link.startswith("leg") or p.link.startswith("foot"): pass
            m = p.mesh.copy(); m.apply_transform(T[p.link]); meshes.append((p.name, m))
        # flip the frame for the top sensor: on face B the robot is upside down; geometry is the same relative to the body
        for k, r in enumerate(rays):
            r = r / np.linalg.norm(r)
            h = raycast_hits(o + r * 0.3, r, meshes)
            # floor distance on the face this sensor serves (sensor below the mid-plane looks at the floor at z=0)
            zfloor = 0.0 if sg < 0 else 2 * HM
            t_floor = (zfloor - o[2]) / r[2] if abs(r[2]) > 1e-6 else 1e9
            first = [x for x in h if x[1] < t_floor]
            if first: E.append({"sensor": "bottom (face A)" if sg < 0 else "top (face B)", "neck": nk if sg < 0 else -nk, "ray": k, "blocked_by": first, "floor_at_mm": round(t_floor, 1)})
    E.append({"sensor": "bottom (face A)" if sg < 0 else "top (face B)", "axis_floor_hit_y_mm": round(float(o[1] + dvec[1] * ((0 if sg < 0 else 2 * HM) - o[2]) / dvec[2]), 1),
              "axis_range_to_floor_mm": round(float(((0 if sg < 0 else 2 * HM) - o[2]) / dvec[2]), 1)})
report["E_tof_view"] = E; print("E", E, flush=True)
tot = sum(len(report[k]) if isinstance(report[k], list) else len(report[k]["hits"]) for k in ("A_body_static", "B_head_static", "C_neck_sweep", "D_leg_sweep"))
report["collisions_total"] = tot
json.dump(report, open(os.path.join(HERE, "fit_report.json"), "w"), indent=1)
print("collisions", tot)
