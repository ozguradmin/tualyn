#!/usr/bin/env python3
"""Front hip vs head clearance sweep with the REAL visible meshes of model.glb (not hulls).
For hip_fl (+x leg; hip_fr is the mirror image with pan -> -pan) over neck_pan x hip x knee:
  gap = smallest distance from any leg surface point (thigh + shin) to the head surface (mm),
  negative = leg point inside the head (crown+chin cap hull or an ear hull) -> -(depth).
Writes out/hipsweep.json: per pan the largest hip angle with gap >= CLEAR for every knee in the knee range
(and for the stand/recovery knees only).  usage: hipsweep.py"""
import os, json, math, numpy as np, trimesh
from scipy.spatial import cKDTree, ConvexHull
class Hull:
    def __init__(self, V): self.E = ConvexHull(V).equations; self.volume = ConvexHull(V).volume
    def contains(self, q): return np.all(q @ self.E[:, :3].T + self.E[:, 3] <= 0, axis=1)
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
CLEAR = 1.0
s = trimesh.load(os.path.join(PKG, 'model.glb')); g = s.graph
def local(n):
    T, gn = g.get(n); link = n.split('__')[0]
    m = s.geometry[gn].copy(); m.apply_transform(np.linalg.inv(g.get(link)[0]) @ T); return m
def pts(names, n_per=6000, vox=0.7):
    P = []
    for nm in names:
        m = local(nm); P.append(m.vertices); P.append(trimesh.sample.sample_surface(m, n_per, seed=1)[0])
    P = np.vstack(P)
    _, idx = np.unique(np.floor(P / vox).astype(np.int64), axis=0, return_index=True)   # ~0.7 mm voxel thinning
    return P[np.sort(idx)]
nodes = list(g.nodes_geometry)
head_vis = [n for n in nodes if n.startswith('head__') and '__internal' not in n]
head_pts = pts(head_vis, 30000)
tree = cKDTree(head_pts)
core = trimesh.util.concatenate([local('head__shell_head'), local('head__shellcap'), local('head__cream_face')]).vertices
core = Hull(core)
ear = trimesh.util.concatenate([local('head__ear'), local('head__cream_ear')])
ear_hulls = [Hull(p.vertices) for p in ear.split(only_watertight=False) if len(p.faces) > 50]
ear_hulls = [h for h in ear_hulls if h.volume > 50]
thigh_names = [n for n in nodes if n.startswith('thigh_fl__') and '__internal' not in n]
shin_names = [n for n in nodes if n.startswith('shin_fl__') and '__internal' not in n]
TP, SP = pts(thigh_names), pts(shin_names)
O = np.array([0, -32.0, 69.04594303749643])          # hip axis = pan axis position (same y in this design)
def rx(d):
    c, s_ = math.cos(math.radians(d)), math.sin(math.radians(d)); return np.array([[1, 0, 0], [0, c, -s_], [0, s_, c]])
def rz(d):
    c, s_ = math.cos(math.radians(d)), math.sin(math.radians(d)); return np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
def gap_of(Pw_head):
    # Pw_head: points already in the head frame
    bb_lo, bb_hi = head_pts.min(0) - 3, head_pts.max(0) + 3
    sel = np.all((Pw_head > bb_lo) & (Pw_head < bb_hi), axis=1)
    if not sel.any(): return 99.0
    q = Pw_head[sel]
    d, _ = tree.query(q, distance_upper_bound=20)
    gmin = float(np.min(d)) if np.isfinite(d).any() else 20.0
    near = (d < 4.0) | ~np.isfinite(d)
    inside = np.zeros(len(q), bool)
    qn = q[near]
    ins = core.contains(qn)
    for h in ear_hulls: ins |= h.contains(qn)
    inside[near] = ins
    if inside.any():
        di = d[inside]; return -float(np.max(np.where(np.isfinite(di), di, 20.0)))
    return gmin
def leg_gap(pan, hip, knee):
    Rh = rz(pan); Rt = rx(hip); Rs = Rt @ rx(knee)
    th = (TP @ Rt.T)                                         # thigh points relative to O
    sh = (SP @ Rs.T) + Rt @ np.array([0, 0, -40.0])
    P = np.vstack([th, sh]) @ Rh                             # into head frame (head origin = O, rotated by pan)
    return gap_of(P)
if __name__ == '__main__':
    import sys
    pans = [int(a) for a in sys.argv[1:]] or list(range(-40, 41, 5)); hips = list(range(90, 161, 2)); knees = list(range(-140, 26, 15)) + [25, -44]
    res = {}
    for pan in pans:
        row = {}
        for hip in hips:
            row[hip] = {k: round(leg_gap(pan, hip, k), 2) for k in knees}
        res[pan] = row
        # largest hip such that every hip <= it is clear for all knees
        def lim(kset):
            ok = None
            for hip in hips:
                if min(row[hip][k] for k in kset) >= CLEAR: ok = hip
                else: break
            return ok
        print(pan, len(TP), len(SP), 'max hip (all knees):', lim(knees), ' (knee -44 stand):', lim([-44]), flush=True)
        res[pan]['_lim_all'] = lim(knees); res[pan]['_lim_k44'] = lim([-44])
    json.dump({str(k): v for k, v in res.items()}, open(os.path.join(HERE, 'out', 'hipsweep%s.json' % ('' if len(sys.argv) < 2 else '_' + '_'.join(sys.argv[1:]))), 'w'))
