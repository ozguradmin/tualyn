#!/usr/bin/env python3
"""random search of open-loop gait parameters (stability-constrained forward speed). usage: search_gait.py N seed mu"""
import sys, os, json, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tarcin as T, gait as G
N, seed, mu = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3])
xml = T.build(mu=mu)
rng = np.random.default_rng(seed)
res = []
def score(r):
    if r['fell']: return -10
    pen = max(0, r['bounce_mm'] - 3) * 0.5 + max(0, r['tilt_deg'] - 6) * 0.3 + r['lat_cm_s'] * 1.0 + abs(r['yaw_deg_s']) * 0.1 + max(0, r['sat_frac'] - 0.05) * 20
    return r['v_cm_s'] - pen
for i in range(N):
    g = rng.choice(['trot', 'walk', 'walk2'])
    p = dict(gait=str(g), period=float(rng.uniform(0.35, 1.0)), duty=float(rng.uniform(0.5, 0.6) if g == 'trot' else rng.uniform(0.7, 0.85)),
             stride=float(rng.uniform(0.008, 0.035)), height=float(rng.uniform(0.004, 0.016)), shift=float(rng.uniform(-0.008, 0.008)),
             dz=float(rng.uniform(-0.008, 0.002)), hpow=float(rng.choice([0.5, 1.0])))
    r, _ = G.run(p, xml, 5.0)
    res.append(dict(p=p, r=r, score=round(score(r), 3)))
res.sort(key=lambda x: -x['score'])
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', f'gait_search_{seed}_mu{mu}.json'), 'w'), indent=0)
for x in res[:8]: print(x['score'], x['p'], x['r'])
