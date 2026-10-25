"""Fixed-camera helper for posecheck: pose.html scales the camera distance by the posed robot's bounding-box radius
(Box3.setFromObject, non-precise = transformed local AABBs). We replicate that radius here so that a requested
absolute camera distance D (mm) stays fixed across frames: distance_param = D*sin(fov/2)/(1.05*rad)."""
import json, math, os, numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
MAN = json.load(open(os.path.join(PKG, 'manifest.json')))
_S = trimesh.load(os.path.join(PKG, 'model.glb'))
_G = _S.graph
PARENT = {}
for n in _G.nodes:
    if n == _G.base_frame: continue
    try: PARENT[n] = _G.transforms.parents[n]
    except Exception: pass
JN = {v['node']: (k, np.array(v['axis'], float), v.get('zero', 0)) for k, v in MAN['joints'].items()}
# per mesh node: corners in its link frame
CORN = []
LINKS = set(v['node'] for v in MAN['joints'].values()) | {'body'}
for n in _G.nodes_geometry:
    T, g = _G.get(n); link = n.split('__')[0]
    TL = _G.get(link)[0]
    b = _S.geometry[g].bounds
    c = np.array([[x, y, z, 1] for x in b[:, 0] for y in b[:, 1] for z in b[:, 2]])
    CORN.append((link, (np.linalg.inv(TL) @ T @ c.T).T[:, :3]))
REST = {l: _G.get(l)[0] for l in LINKS}
def parent_link(l):
    p = PARENT.get(l)
    while p is not None and p not in LINKS: p = PARENT.get(p)
    return p
def axang(ax, deg):
    a = math.radians(deg); ax = ax / np.linalg.norm(ax); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    R = np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K; M = np.eye(4); M[:3, :3] = R; return M
def quat2m(q):
    w, x, y, z = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)], [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)], [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]])
def world(joints, base):
    B = np.eye(4)
    if base is not None: B[:3, :3] = quat2m(base[3:]); B[:3, 3] = base[:3]
    W = {}
    def get(l):
        if l in W: return W[l]
        p = parent_link(l)
        if p is None: W[l] = B @ REST[l]; return W[l]
        loc = np.linalg.inv(REST[p]) @ REST[l]
        if l in JN:
            k, ax, z0 = JN[l]; loc = loc @ axang(ax, joints.get(k, MAN['pose_rest'].get(k, 0)) - z0)
        W[l] = get(p) @ loc; return W[l]
    for l in LINKS: get(l)
    return W
def bbox(joints, base):
    W = world(joints, base); P = []
    for l, c in CORN: P.append((W[l] @ np.c_[c, np.ones(len(c))].T).T[:, :3])
    P = np.vstack(P); return P.min(0), P.max(0)
def frame(anim, t):
    fps = anim.get('fps', 30); n = anim['frames']; x = t * fps
    x = x % (n - 1) if anim.get('loop') else min(x, n - 1)
    i = int(math.floor(x)); f = x - i; i2 = min(i + 1, n - 1)
    j = {k: v[i] + (v[i2] - v[i]) * f for k, v in anim['joints'].items()}
    b = None
    if anim.get('base'):
        b0, b1 = np.array(anim['base'][i]), np.array(anim['base'][i2]); b = b0 + (b1 - b0) * f
        b[3:] /= np.linalg.norm(b[3:])
    return j, b
def dist_param(D_mm, joints, base, fov=28.0):
    lo, hi = bbox(joints, base); rad = max(0.06, np.linalg.norm(hi - lo) / 2 / 1000)
    return D_mm / 1000 * math.sin(math.radians(fov / 2)) / (1.05 * rad), lo, hi
if __name__ == '__main__':
    print(bbox(MAN['pose_rest'], None))
