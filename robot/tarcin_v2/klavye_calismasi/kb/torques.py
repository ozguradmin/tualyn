"""servo torque split by stance / swing for the final gaits (flat desk mu 0.6 and K1/K2 keyboards), limit 0.20 N*m"""
import sys, os, json, math; sys.path.insert(0, '.')
import numpy as np
from multiprocessing import Pool
OUT = '../out'
def one(a):
    name, spec, var, ter, seed, mu = a
    import kbsim; kbsim.VARIANT.update(var)
    import kbd, batch, ctrl as C, rgait, gait as G, tarcin as T
    if ter == 'flat':
        kb = None; r = kbsim.Run(None, 0, 0, 0, mu_desk=mu)
    else:
        kb = kbd.Keyboard(ter, 'real' if ter == 'K2' else 'real', seed=seed, mu=mu)
        st = batch.start(ter, 'rows', seed, kb); r = kbsim.Run(kb, st[0], st[1], st[2], yaw_jitter_deg=st[3])
    c = C.Baseline() if spec == 'baseline' else rgait.Rough(spec)
    p = c.p
    ph = (G.PHASE if spec == 'baseline' else rgait.PH)[p['gait']]
    duty = p['duty']; per = p['period']
    s = r.s; t0 = s.d.time
    rec = {('hip', 'st'): [], ('hip', 'sw'): [], ('knee', 'st'): [], ('knee', 'sw'): []}
    n = int(6.0 / T.DT)
    for i in range(n):
        t = s.d.time - t0
        s.step(c(t, s, r))
        if t < 1.0: continue
        if s.d.xmat[s.bid][8] < 0.7: break
        for leg in T.LEGS:
            st_ = ((t / per + ph[leg]) % 1.0) < duty
            for j in ('hip', 'knee'):
                rec[(j, 'st' if st_ else 'sw')].append(abs(float(s.d.actuator_force[s.aid[f'{j}_{leg}']])))
    out = {}
    for (j, k), v in rec.items():
        v = np.array(v) if v else np.zeros(1)
        out[f'{j}_{k}'] = dict(med=round(float(np.median(v)), 3), p95=round(float(np.percentile(v, 95)), 3), sat=round(float((v > 0.195).mean()), 3))
    return name, ter, out
if __name__ == '__main__':
    mech = {"ski": 0.005, "track_add": 0.025}
    cfg = [('BASE (package trot)', 'baseline', {}), ('RT (spread trot, stock)', json.load(open(f'{OUT}/spec_RT.json')), {}),
           ('WALK (stock)', json.load(open(f'{OUT}/spec_WALK.json')), {}), ('MECH (wide track + ski paws, spread trot 8 mm)', json.load(open(f'{OUT}/spec_MECH.json')), mech)]
    jobs = [(n, sp, v, ter, 0, mu) for n, sp, v in cfg for ter, mu in (('flat', 0.6), ('K1', 0.4), ('K2', 0.4))]
    with Pool(4) as P: res = P.map(one, jobs)
    json.dump([dict(cfg=n, terrain=t, torque=o) for n, t, o in res], open(f'{OUT}/torques.json', 'w'), indent=1)
    for n, t, o in res:
        print(f'{n:48s} {t:4s} ' + ' | '.join(f"{k}: med {v['med']:.3f} p95 {v['p95']:.3f} sat {100*v['sat']:.0f}%" for k, v in o.items()))
