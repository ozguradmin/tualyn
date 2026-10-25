#!/usr/bin/env python3
"""Fit / collision checks on the per-part STLs written by model.py.
usage: python3 -I check.py out/<pose> [out/<pose2> ...]"""
import glob, os, sys, itertools
import trimesh, numpy as np
import manifold3d as mf

class P:
    def __init__(self, mesh):
        mm = mf.Mesh(vert_properties=np.asarray(mesh.vertices, dtype=np.float32),
                     tri_verts=np.asarray(mesh.faces, dtype=np.uint32))
        mm.merge()
        self.m = mf.Manifold(mm)
        self.ok = self.m.status() == mf.Error.NoError
        self.bounds = np.array(mesh.bounds)

def load(d):
    m = {}
    for f in glob.glob(os.path.join(d, "parts", "*.stl")):
        m[os.path.basename(f)[:-4]] = P(trimesh.load(f, process=True))
    return m

def inter(a, b):
    (amin, amax), (bmin, bmax) = a.bounds, b.bounds
    if (amax < bmin).any() or (bmax < amin).any():
        return 0.0
    if not (a.ok and b.ok):
        return -1.0
    return float((a.m ^ b.m).volume())

BODY = ["shell_top", "shell_bot", "lip", "tail"]
INTERNAL = ["cell_l", "cell_r", "pca9685", "pca_chip", "mp1584_servoA", "mp1584_servoB", "mp1584_logic",
            "pam8403", "bmi160", "bms_2s", "charger_2s_usbc", "usbc_breakout", "speaker29", "stalk_mount"] + [f"hip_servo{i}" for i in range(4)]

def run(d):
    m = load(d)
    legs = {i: [n for n in (f"egg{i}", f"arm{i}", f"foot{i}", f"toe{i}", f"knee_servo{i}") if n in m] for i in range(4)}
    head = [n for n in m if n.startswith("head_")]
    pairs = []
    for i, ps in legs.items():
        for p in ps:
            pairs += [(p, b) for b in BODY]
        pairs += [(f"foot{i}", f"arm{i}"), (f"foot{i}", f"egg{i}"), (f"toe{i}", f"arm{i}"),
                  (f"knee_servo{i}", f"hip_servo{i}"), (f"arm{i}", f"hip_servo{i}"), (f"foot{i}", f"knee_servo{i}")]
        for j in range(i + 1, 4):
            pairs += [(a, b) for a in ps for b in legs[j]]
        pairs += [(p, h) for p in ps for h in head]
    pairs += [(a, b) for a, b in itertools.combinations(INTERNAL, 2)]
    pairs += [(a, b) for a in INTERNAL for b in BODY]
    pairs += [(h, b) for h in head for b in BODY + ["stalk"]]
    pairs += [(h, b) for h in head if h != "head_skin0" for b in ("neck_servo", "stalk_plate")]
    pairs += [("stalk", b) for b in BODY]
    bad = []
    for a, b in pairs:
        if a in m and b in m:
            v = inter(m[a], m[b])
            if abs(v) > 0.5:   # mm^3
                bad.append((a, b, round(v, 1)))
    # knee servo containment (outside-arm volume, excluding the horn spline that pokes to the foot cheek)
    cont = {}
    for i in range(4):
        ks, arm = m.get(f"knee_servo{i}"), m.get(f"arm{i}")
        if ks is not None and arm is not None:
            cont[i] = round(float((ks.m - arm.m).volume()), 1) if (ks.ok and arm.ok) else None
    zmin = min(mm.bounds[0][2] for mm in m.values()) if m else None
    print(f"== {d}: {len(m)} parts, z_min={zmin:.2f}")
    print("   collisions (>0.5 mm3):", bad if bad else "none")
    print("   knee servo volume outside arm shell (mm3; spline ~60 expected):", cont)
    return bad

if __name__ == "__main__":
    for d in sys.argv[1:]:
        run(d)
