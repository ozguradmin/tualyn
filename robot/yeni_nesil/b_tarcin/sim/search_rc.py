#!/usr/bin/env python3
"""Re-tune the concept's OpenCat-'rc'-style recovery keyframes (same structure as concept_B/sim/search.py:
mirrored by the side that is down, tail = lever, last keyframe = tuck/stand) on THIS package model.
usage: search_rc.py es|rand iters seed"""
import sys, os, json, math, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tarcin as T, recover as R

mode, iters, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
XML = {0.6: T.build(mu=0.6), 0.4: T.build(mu=0.4)}
CASES = [(0.6, 90, 0), (0.6, -90, 0), (0.6, 180, 0), (0.6, 135, 0), (0.6, -135, 0), (0.6, 90, 20), (0.6, 180, -15),
         (0.4, 90, 0), (0.4, 180, 0), (0.4, -135, 0)]
RANGES = {"F": ((-20, 160), (-140, 25)), "H": ((-50, 130), (-25, 140))}


def one(seq, mu, roll, pitch):
    s = T.Sim(XML[mu], record=False)
    q = R.quat_roll_pitch(roll, pitch)
    s.set_pose(R.stand(), base=(0, 0, 0, *q)); s.drop_to_floor(); s.d.qpos[2] += 0.015
    s.hold(R.stand(), 1.0)
    x, y, z = s.up(); down = 1 if x[2] < 0 else -1
    for kf in seq:
        s.hold(R.kf_target(kf, down), kf["T"])
    s.hold(R.stand(), 0.8); s.hold(R.stand(), 0.4)
    return float(s.up()[2][2])


def score(seq):
    v = [one(seq, *c) for c in CASES]
    return sum(x > 0.85 for x in v) + 0.01 * sum(v), v


def clip(kf):
    for role in ("dF", "dH", "uF", "uH"):
        (a0, a1), (k0, k1) = RANGES[role[1]]
        kf[role] = [float(np.clip(kf[role][0], a0, a1)), float(np.clip(kf[role][1], k0, k1))]
    kf["pan"] = float(np.clip(kf["pan"], -40, 40)); kf["tail"] = float(np.clip(kf["tail"], -85, 85))
    kf["T"] = float(np.clip(kf["T"], 0.2, 1.0))
    return kf


def rand_kf(rng):
    kf = {}
    for role in ("dF", "dH", "uF", "uH"):
        (a0, a1), (k0, k1) = RANGES[role[1]]
        kf[role] = [float(rng.uniform(a0, a1)), float(rng.uniform(k0, k1))]
    kf["pan"] = float(rng.uniform(-40, 40)); kf["tail"] = float(rng.uniform(-85, 85)); kf["T"] = float(rng.uniform(0.25, 0.9))
    return kf


FINAL = dict(dF=[20, -44], dH=[-20, 44], uF=[20, -44], uH=[-20, 44], pan=0.0, tail=0.0, T=0.4)
rng = np.random.default_rng(seed)
out = os.path.join(HERE, "out", f"rc_{mode}_{seed}.json")
if mode == "es":
    best_seq = json.load(open(os.path.join(HERE, "rc_seq13.json")))["seq"]
    if len(sys.argv) > 4: best_seq = json.load(open(sys.argv[4]))["seq"]
else:
    best_seq = None
best = (-1, None)
if best_seq:
    best = (score(best_seq)[0], best_seq)
    print("start", round(best[0], 3), flush=True)
sig = 1.0
for i in range(iters):
    if mode == "es":
        seq = json.loads(json.dumps(best[1]))
        for kf in seq[:-1]:
            for role in ("dF", "dH", "uF", "uH"):
                if rng.random() < 0.35:
                    kf[role][0] += rng.normal() * 20 * sig; kf[role][1] += rng.normal() * 20 * sig
            if rng.random() < 0.35: kf["tail"] += rng.normal() * 25 * sig
            if rng.random() < 0.25: kf["pan"] += rng.normal() * 15 * sig
            if rng.random() < 0.25: kf["T"] += rng.normal() * 0.1 * sig
            clip(kf)
    else:
        seq = [rand_kf(rng) for _ in range(int(rng.integers(2, 5)))] + [dict(FINAL)]
    sc, v = score(seq)
    if sc > best[0]:
        best = (sc, seq)
        print(i, round(sc, 3), [round(x, 2) for x in v], flush=True)
        json.dump(dict(score=sc, vals=v, seq=seq), open(out, "w"), indent=1)
