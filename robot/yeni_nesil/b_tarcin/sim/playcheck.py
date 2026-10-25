#!/usr/bin/env python3
"""Numeric playback check of anim/*.json with the GLB's visual meshes (same FK as rig.js). All clips in one run.
Per clip:
 - lowest visible vertex z (mm) per frame: <0 = ground penetration, >0 = nothing touches the desk.
 - sibling links (MuJoCo hull contacts, mj_forward of the recorded pose): deepest hull-hull penetration. Hulls are
   coarser than the real meshes, so this over-reports.
 - PARENT-CHILD pairs (body-head, body-tail, body-thigh, thigh-shin) with the REAL meshes: MuJoCo filters these
   contacts by default (review finding), so they are checked here with a per-joint-angle lookup table built from the
   visible meshes: clearance = nearest child surface point to the parent surface (KD tree, 0.5 mm sampling, unsigned:
   < ~0.5 mm means touching or crossing). The hub post inside the hip collar (a designed bearing fit,
   rotation-symmetric) is excluded.
 - head vs front legs (siblings) with the real meshes for frames with hip_f > 90 deg (sim/hipsweep.py's gap).
Writes out/playcheck.json."""
import sys, os, json, math, numpy as np, trimesh, mujoco
from scipy.spatial import cKDTree, ConvexHull
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fixcam as F, tarcin as T
S, G = F._S, F._G
HV = []
for n in G.nodes_geometry:
    link, mat = n.split('__', 1)
    if mat.startswith('internal'): continue
    Tn, g = G.get(n); m = S.geometry[g]
    v = m.convex_hull.vertices if len(m.vertices) > 60 else m.vertices
    HV.append((link, (np.linalg.inv(G.get(link)[0]) @ Tn @ np.c_[v, np.ones(len(v))].T).T[:, :3]))
def minz(j, b):
    W = F.world(j, b); return min(float((W[l] @ np.c_[v, np.ones(len(v))].T)[2].min()) for l, v in HV)

# ---------------- real-mesh parent-child lookup tables
def local(n):
    Tn, gn = G.get(n); link = n.split('__')[0]
    m = S.geometry[gn].copy(); m.apply_transform(np.linalg.inv(G.get(link)[0]) @ Tn); return m
def link_pts(link, skip=(), n_per=4000, vox=0.5):
    P = []
    for n in G.nodes_geometry:
        l, mat = n.split('__', 1)
        if l != link or mat.startswith('internal') or mat in skip: continue
        m = local(n); P.append(m.vertices); P.append(trimesh.sample.sample_surface(m, n_per, seed=2)[0])
    P = np.vstack(P); _, idx = np.unique(np.floor(P / vox).astype(np.int64), axis=0, return_index=True)
    return P[np.sort(idx)]
def rot(ax, deg):
    return F.axang(np.array(ax, float), deg)[:3, :3]
PAIRS = []
for jn, jd in F.MAN['joints'].items():
    child = jd['node']; parent = F.parent_link(child)
    o = (np.linalg.inv(F.REST[parent]) @ F.REST[child])[:3, 3]
    PAIRS.append((jn, parent, child, o, jd['axis'], jd['min'], jd['max']))
LUT = {}
for jn, parent, child, o, ax, lo, hi in PAIRS:
    pp = link_pts(parent, skip=('hub',) if child.startswith('thigh') else ())
    tree = cKDTree(pp); cp = link_pts(child)
    if child.startswith('thigh'):     # the collar face sits on the hub post: exclude the bearing zone (r < 11.5 around the hip axis)
        r = np.hypot(cp[:, 1], cp[:, 2]); cp = cp[r > 11.5]
    angs = np.arange(math.floor(lo) - 5, math.ceil(hi) + 6, 1.0)
    vals = []
    for a in angs:
        q = cp @ rot(ax, a).T + o
        d, _ = tree.query(q, distance_upper_bound=30); d = np.where(np.isfinite(d), d, 30.0)
        v = float(d.min())     # unsigned: a surface crossing shows up as ~0 (sampling 0.5 mm); the body is concave (neck nook), so no hull inside-test
        vals.append(round(v, 2))
    LUT[jn] = (angs, np.array(vals))
    print('LUT', jn, parent, '->', child, 'range', lo, hi, 'min clearance in range %.2f mm' % np.array(vals)[(angs >= lo) & (angs <= hi)].min(), flush=True)
import hipsweep as HS

m = mujoco.MjModel.from_xml_string(T.build(0.6)); d = mujoco.MjData(m)
jadr = {n: m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in T.JOINTS}
floor = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, 'floor')
res = {'_luts': {jn: dict(min_clearance_in_range_mm=float(v[(a >= p[5]) & (a <= p[6])].min()),
                         at_deg=float(a[(a >= p[5]) & (a <= p[6])][int(np.argmin(v[(a >= p[5]) & (a <= p[6])]))]))
                 for (jn, (a, v)), p in zip(LUT.items(), PAIRS)}}
clips = sys.argv[1:] or list(F.MAN['animations'])
for clip in clips:
    a = json.load(open(os.path.join(F.PKG, 'anim', clip + '.json')))
    zs, pen, pc, hh = [], 0.0, {}, 99.0
    for i in range(a['frames']):
        j = {k: v[i] for k, v in a['joints'].items()}; b = a['base'][i] if a.get('base') else [0, 0, 0, 1, 0, 0, 0]
        jc = {k: min(F.MAN['joints'][k]['max'], max(F.MAN['joints'][k]['min'], v)) for k, v in j.items()}   # rig.js clamps
        zs.append(minz(jc, np.array(b, float)))
        d.qpos[:3] = np.array(b[:3]) / 1000; d.qpos[3:7] = b[3:]
        for k in T.JOINTS: d.qpos[jadr[k]] = math.radians(j[k])
        mujoco.mj_forward(m, d)
        for c in d.contact[:d.ncon]:
            if floor in (c.geom1, c.geom2): continue
            pen = max(pen, -c.dist * 1000)
        for jn, (angs, vals) in LUT.items():
            v = float(np.interp(jc[jn], angs, vals)); pc[jn] = min(pc.get(jn, 99.0), v)
        for side in ('l', 'r'):
            hip = jc['hip_f' + side]
            if hip > 90:
                pan = jc['neck_pan'] if side == 'l' else -jc['neck_pan']
                hh = min(hh, HS.leg_gap(pan, hip, jc['knee_f' + side]))
    zs = np.array(zs)
    worst = min(pc, key=pc.get)
    res[clip] = dict(frames=a['frames'], lowest_z_min_mm=round(zs.min(), 2), lowest_z_max_mm=round(zs.max(), 2),
                     frames_penetrating_gt1mm=int((zs < -1).sum()), frames_floating_gt1mm=int((zs > 1).sum()),
                     sibling_hull_penetration_mm=round(pen, 2),
                     parent_child_min_clearance_mm={k: round(v, 2) for k, v in pc.items()},
                     parent_child_worst=f"{worst} {pc[worst]:.2f} mm",
                     head_vs_front_leg_min_gap_mm=(round(hh, 2) if hh < 99 else "hip_f never > 90°"))
    print(clip, res[clip], flush=True)
json.dump(res, open(os.path.join(HERE, 'out', 'playcheck.json'), 'w'), indent=1)
