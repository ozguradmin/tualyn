#!/usr/bin/env python3
"""(1+1)-ES on the SIDE recovery sequence (first-try success, no retries) over randomised side drops,
common random numbers per block of 8 iterations. usage: es_side.py iters seed"""
import sys, os, json, math, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tarcin as T, recover as R, recover2 as R2, rclib as L
iters, seed = int(sys.argv[1]), int(sys.argv[2])
X = {0.6: T.build(0.6), 0.4: T.build(0.4)}
rng = np.random.default_rng(seed)
def cases(r):
    c = []
    for i in range(14):
        mu = 0.6 if i < 10 else 0.4
        roll = float(r.uniform(55, 140)) * (1 if i % 2 else -1); pitch = float(r.uniform(-30, 30))
        c.append((mu, roll, pitch))
    return c
def one(seq, mu, roll, pitch):
    s = T.Sim(X[mu], record=False); q = R.quat_roll_pitch(roll, pitch)
    s.set_pose(R.stand(), base=(0, 0, 0, *q)); s.drop_to_floor(); s.d.qpos[2] += 0.015; s.hold(R.stand(), 1.2)
    kind, down = R2.classify(s)
    if kind == 'up': return 1.0
    for kf in (seq if kind == 'side' else R2.BACK): s.hold(R.kf_target(kf, down), kf['T'])
    s.hold(R.stand(), 0.8); s.hold(R.stand(), 0.5)
    return float(s.up()[2][2])
def score(seq, cs):
    v = [one(seq, *c) for c in cs]; return sum(x > 0.85 for x in v) / len(v), v
best = json.load(open(os.path.join(HERE, 'rc_side.json')))['seq']
out = os.path.join(HERE, 'out', f'es_side_{seed}.json')
cs = cases(rng); bs, _ = score(best, cs); print('start', round(bs, 3), flush=True)
for i in range(iters):
    if i % 8 == 7:
        cs = cases(rng); bs, _ = score(best, cs); print(i, 're-sample, best on new set', round(bs, 3), flush=True)
    seq = json.loads(json.dumps(best))
    for kf in seq[:-1]:
        for role in ('dF', 'dH', 'uF', 'uH'):
            if rng.random() < 0.3: kf[role][0] += rng.normal() * 12; kf[role][1] += rng.normal() * 12
        if rng.random() < 0.3: kf['tail'] += rng.normal() * 15
        if rng.random() < 0.2: kf['pan'] += rng.normal() * 10
        if rng.random() < 0.2: kf['T'] += rng.normal() * 0.06
        L.clip_kf(kf) if hasattr(L, 'clip_kf') else None
        for role in ('dF', 'dH', 'uF', 'uH'):
            (a0, a1), (k0, k1) = L.RANGES[role[1]]
            kf[role] = [float(np.clip(kf[role][0], a0, a1)), float(np.clip(kf[role][1], k0, k1))]
        kf['pan'] = float(np.clip(kf['pan'], -40, 40)); kf['tail'] = float(np.clip(kf['tail'], -85, 85)); kf['T'] = float(np.clip(kf['T'], 0.2, 0.9))
    sc, v = score(seq, cs)
    if sc >= bs:
        if sc > bs: print(i, 'improved', round(sc, 3), flush=True)
        best, bs = seq, sc
        json.dump(dict(score_last_block=bs, seed=seed, iter=i, seq=best), open(out, 'w'), indent=1)
print('DONE', bs, flush=True)
