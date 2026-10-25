"""flat desk check: 10 starts (yaw jitter -9..+9 deg) x mu 0.6 / 0.4, 25 cm, same failure rules"""
import sys, os, json; sys.path.insert(0, '.')
from multiprocessing import Pool
import numpy as np
OUT = '../out'
def one(a):
    name, spec, var, mu, sd = a
    import kbsim; kbsim.VARIANT.update(var)
    import batch
    r = batch.one((spec, 'flat', 'flat', mu, sd, 20.0))
    return name, mu, r['result'], r.get('speed_cm_s', 0), r.get('lat_mm', 0), r.get('yaw_err_deg', 0)
if __name__ == '__main__':
    mech = {"ski": 0.005, "track_add": 0.025}
    L = lambda n: json.load(open(f'{OUT}/spec_{n}.json'))
    cfg = [('BASE', 'baseline', {}), ('RT', L('RT'), {}), ('RT8', L('RT8'), {}), ('WALK', L('WALK'), {}), ('MECH', L('MECH'), mech)]
    jobs = [(n, sp, v, mu, sd - 5) for n, sp, v in cfg for mu in (0.6, 0.4) for sd in range(10)]
    with Pool(4) as P: res = P.map(one, jobs)
    out = {}
    for n, _, _ in cfg:
        for mu in (0.6, 0.4):
            rs = [x for x in res if x[0] == n and x[1] == mu]
            ok = [x for x in rs if x[2] == 'success']
            out[f'{n}_mu{mu}'] = dict(ok=len(ok), n=len(rs), v=round(float(np.mean([x[3] for x in ok])), 2) if ok else None,
                                      v_min=round(float(min(x[3] for x in ok)), 2) if ok else None, fails=[x[2] for x in rs if x[2] != 'success'],
                                      lat_abs_mean_mm=round(float(np.mean([abs(x[4]) for x in ok])), 1) if ok else None)
            print(n, mu, out[f'{n}_mu{mu}'])
    json.dump(out, open(f'{OUT}/flatcheck.json', 'w'), indent=1)
