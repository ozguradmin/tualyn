"""record paw tracks on the real K2 (rows) for BASE and MECH, same keyboard and starts"""
import sys, os, json; sys.path.insert(0, '.')
from multiprocessing import Pool
OUT = '../out'
def one(a):
    name, spec, var, seed, mu = a
    import kbsim; kbsim.VARIANT.update(var)
    import kbd, batch, ctrl as C, rgait, tarcin as T
    kb = kbd.Keyboard('K2', 'real', seed=seed, mu=mu); st = batch.start('K2', 'rows', seed, kb)
    r = kbsim.Run(kb, st[0], st[1], st[2], yaw_jitter_deg=st[3])
    c = C.Baseline() if spec == 'baseline' else rgait.Rough(spec)
    s = r.s; t0 = s.d.time; tr = []
    res = 'timeout'
    for i in range(int(20 / T.DT)):
        t = s.d.time - t0; s.step(c(t, s, r))
        if i % 40 == 0:
            tr.append([round(float(v) * 1000, 1) for v in r.paws()[:, :2].ravel()] + [round(float(s.d.qpos[0]) * 1000, 1), round(float(s.d.qpos[1]) * 1000, 1)])
        if s.d.xmat[s.bid][8] < 0.7: res = 'fell'; break
        if i % 40 == 0 and t > 0.6 and r.paws()[:, 2].min() < 0.004: res = 'off'; break
        if r.progress() >= 0.25: res = 'success'; break
    return dict(name=name, seed=seed, mu=mu, result=res, start=st, track=tr)
if __name__ == '__main__':
    mech = {"ski": 0.005, "track_add": 0.025}
    jobs = [('BASE', 'baseline', {}, sd, 0.4) for sd in (0, 1, 2, 4)] + [('MECH', json.load(open(f'{OUT}/spec_MECH.json')), mech, sd, 0.4) for sd in (0, 1, 2, 4)]
    with Pool(4) as P: res = P.map(one, jobs)
    for x in res: print(x['name'], x['seed'], x['result'], len(x['track']))
    json.dump(res, open(f'{OUT}/tracks_K2.json', 'w'))
