#!/usr/bin/env python3
"""(1+1)-ES refinement of the best random-search gaits, scored on BOTH mu=0.6 and mu=0.4 (worst case).
usage: refine_gait.py gaitname iters seed"""
import sys, os, json, glob, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tarcin as T, gait as G
gname, iters, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
TAG = sys.argv[4] if len(sys.argv) > 4 else gname
PMIN = float(sys.argv[5]) if len(sys.argv) > 5 else 0.3
SATMAX = float(sys.argv[6]) if len(sys.argv) > 6 else 0.08
XML = {mu: T.build(mu=mu) for mu in (0.6, 0.4)}
def sc(r, p):
    if r['fell']: return -10
    pen = (max(0, r['bounce_mm'] - 3) * 0.5 + max(0, r['tilt_deg'] - 6) * 0.3 + r['lat_cm_s'] + abs(r['yaw_deg_s']) * 0.1
           + max(0, r['sat_frac'] - SATMAX) * 60 + max(0, 0.75 - r['eff']) * 5 + max(0, r['eff'] - 1.1) * 5)
    return r['v_cm_s'] - pen
def ev(p):
    rs = {mu: G.run(p, XML[mu], 5.0)[0] for mu in XML}
    return min(sc(r, p) for r in rs.values()), rs
cands = []
for f in glob.glob(os.path.join(HERE, 'out', 'gait_search_*_mu0.6.json')):
    cands += [x for x in json.load(open(f)) if x['p']['gait'].startswith(gname)]
cands.sort(key=lambda x: -x['score'])
rng = np.random.default_rng(seed)
best = None
for c in [c for c in cands if c['p']['period'] >= PMIN][:4]:
    c['p']['period'] = max(c['p']['period'], PMIN)
    s, rs = ev(c['p'])
    if best is None or s > best[0]: best = (s, c['p'], rs)
print('start', best[0], best[1]); sys.stdout.flush()
step = dict(period=0.05, duty=0.03, stride=0.003, height=0.0015, shift=0.0015, dz=0.001)
lo = dict(period=PMIN, duty=0.5 if gname == 'trot' else 0.68, stride=0.005, height=0.003, shift=-0.01, dz=-0.012)
hi = dict(period=1.2, duty=0.65 if gname == 'trot' else 0.9, stride=0.04, height=0.02, shift=0.01, dz=0.003)
for i in range(iters):
    p = dict(best[1])
    for k in step:
        if rng.random() < 0.5:
            p[k] = float(np.clip(p[k] + rng.normal() * step[k], lo[k], hi[k]))
    s, rs = ev(p)
    if s > best[0]:
        best = (s, p, rs); print(i, round(s, 3), p, rs[0.6], rs[0.4]); sys.stdout.flush()
json.dump(dict(score=best[0], p=best[1], r={str(k): v for k, v in best[2].items()}), open(os.path.join(HERE, 'out', f'gait_best_{TAG}.json'), 'w'), indent=1)
