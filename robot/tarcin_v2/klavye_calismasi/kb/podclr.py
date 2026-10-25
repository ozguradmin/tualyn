"""kinematic clearance between the same-side leg pods (thigh hulls) over one gait cycle"""
import sys, math; sys.path.insert(0,'.')
import kbsim, gait as G, numpy as np, mujoco, tarcin as T
_S = None
def _sim():
    global _S
    if _S is None:
        r = kbsim.Run(None, 0, 0, 0); _S = r.s
    return _S
def clearance(foot_fn, n=60):
    """foot_fn(leg, phase01) -> (y, z) body frame rel. hip. returns min distance fl-hl and fr-hr pods (mm) and where"""
    s = _sim(); m, d = s.m, s.d
    g = {k: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f'thigh_{k}_hull') for k in T.LEGS}
    q0 = d.qpos.copy(); best = (1e9, None); ft = np.zeros(6)
    for i in range(n):
        u = i / n
        for leg in T.LEGS:
            y, z = foot_fn(leg, u)
            h, k = T.ik(leg, y, z)
            d.qpos[s.qadr['hip_' + leg]] = math.radians(h); d.qpos[s.qadr['knee_' + leg]] = math.radians(k)
        mujoco.mj_kinematics(m, d)
        for a, b in (('fl', 'hl'), ('fr', 'hr')):
            dd = mujoco.mj_geomDistance(m, d, g[a], g[b], 0.05, ft) * 1000
            if dd < best[0]: best = (dd, u)
    d.qpos[:] = q0; mujoco.mj_kinematics(m, d)
    return best
if __name__ == '__main__':
    import rgait, json
    sp = json.loads(sys.argv[1])
    R = rgait.Rough(sp)
    p = R.p
    def fn(leg, u):
        y0, z0 = R.rf[leg]
        y0 += p['shift'] + (p['fy'] if leg[0]=='f' else p['hy']); z0 += p['dz']
        ph = (u + rgait.PH[p['gait']][leg]) % 1.0
        return R.foot(leg, ph, p['stride'], p['H'], z0, y0)
    print(clearance(fn))
