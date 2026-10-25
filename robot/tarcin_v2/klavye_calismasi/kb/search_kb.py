#!/usr/bin/env python3
"""Random search + (1+lambda)-ES for the rough-terrain gait (rgait.Rough), scored on a fixed TRAINING set of terrains
(seeds 100+; the reported test uses seeds 0-15): flat desk, 5 deg plain slopes, K2 rows/diag, K1 rows/diag.
usage: search_kb.py family n_random n_es seed tag [init.json]"""
import sys, os, json, math, time
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OUT = os.path.join(os.path.dirname(HERE), "out")

TRAIN = [("flat", None, 0.6, 0), ("flat", None, 0.4, 0), ("slope", "x", 0.4, 0), ("slope", "up", 0.4, 0),
         ("K2", "rows", 0.4, 100), ("K2", "rows", 0.3, 101), ("K2", "rows", 0.6, 102), ("K2", "rows", 0.4, 103),
         ("K2", "diag", 0.4, 100), ("K2", "diag", 0.3, 101), ("K2", "diag", 0.4, 102), ("K2", "diag", 0.6, 106),
         ("K1", "rows", 0.3, 100), ("K1", "diag", 0.3, 101)]
T_MAX = 15.0

SPACE = {  # name: (lo, hi)
    "trot": dict(period=(0.35, 0.9), duty=(0.5, 0.65), stride=(0.010, 0.035), H=(0.005, 0.022), apex_f=(0.3, 0.7),
                 apex_h=(0.3, 0.7), hh=(0.6, 1.2), fy=(-0.022, 0.004), hy=(-0.004, 0.022), dz=(-0.004, 0.010),
                 shift=(-0.008, 0.008), kh=(0.0, 1.5), hlim=(0.003, 0.010), kc=(0.0, 8.0), lev_kp=(0.0, 1.0),
                 lev_ki=(0.0, 3.0), lev_lim=(0.004, 0.012), dip=(0.0, 0.004)),
    "walk": dict(period=(0.8, 2.5), duty=(0.72, 0.9), stride=(0.010, 0.035), H=(0.006, 0.022), apex_f=(0.3, 0.7),
                 apex_h=(0.3, 0.7), hh=(0.6, 1.2), fy=(-0.022, 0.004), hy=(-0.004, 0.022), dz=(-0.004, 0.010),
                 shift=(-0.008, 0.012), sway_y=(0.0, 0.015), kh=(0.0, 1.5), hlim=(0.003, 0.010), kc=(0.0, 8.0),
                 lev_kp=(0.0, 1.0), lev_ki=(0.0, 3.0), lev_lim=(0.004, 0.012), dip=(0.0, 0.004)),
}


def run_one(args):
    spec, ter, mode, mu, seed = args
    import kbd, kbsim, rgait, batch
    try:
        if ter == "flat":
            kb, hd, x0, y0, yj = None, 0.0, 0.0, 0.0, 0.0
            r = kbsim.Run(None, 0.0, 0.0, 0.0, mu_desk=mu)
        elif ter == "slope":
            kb = kbd.Slope(5.0, mu=mu)
            hd, x0, y0 = (0.0, 60.0, 200.0) if mode == "x" else (90.0, 300.0, 60.0)
            r = kbsim.Run(kb, hd, x0, y0)
        else:
            kb = kbd.Keyboard(ter, "real" if mode == "rows" else "field", seed=seed, mu=mu)
            hd, x0, y0, yj, tgt = batch.start(ter, mode, seed, kb)
            r = kbsim.Run(kb, hd, x0, y0, yaw_jitter_deg=yj, target_mm=tgt)
        o = r.go(rgait.Rough(spec), t_max=T_MAX)
        return dict(ok=o["result"] == "success", res=o["result"], prog=o["progress_mm"], v=o["speed_cm_s"],
                    sat=(o["hip"]["sat"] + o["knee"]["sat"]) / 2, t=o["t"])
    except Exception as e:
        return dict(ok=False, res="error:" + str(e)[:80], prog=0, v=0, sat=1, t=0)


def score(rs):
    s = 0.0
    for r in rs:
        s += 10.0 if r["ok"] else 5.0 * max(0.0, min(1.0, r["prog"] / 250.0)) - (2.0 if r["res"] == "fell" else 0.0)
        s += 0.4 * min(8.0, max(0.0, r["v"])) if r["ok"] else 0.0
        s -= 8.0 * max(0.0, r["sat"] - 0.08)
    return s / len(rs)


def evaluate(P, specs):
    jobs = [(sp,) + t for sp in specs for t in TRAIN]
    res = P.map(run_one, jobs, chunksize=1)
    out = []
    for i, sp in enumerate(specs):
        rs = res[i * len(TRAIN):(i + 1) * len(TRAIN)]
        out.append((score(rs), rs))
    return out


def sample(rng, fam):
    sp = {"gait": fam, "a": 0.0}
    for k, (lo, hi) in SPACE[fam].items():
        sp[k] = float(rng.uniform(lo, hi))
    return sp


def mutate(rng, sp, fam, sigma):
    q = dict(sp)
    for k, (lo, hi) in SPACE[fam].items():
        if rng.random() < 0.4:
            q[k] = float(np.clip(q[k] + rng.normal() * sigma * (hi - lo), lo, hi))
    return q


if __name__ == "__main__":
    fam, nr, ne, seed, tag = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    init = json.load(open(sys.argv[6])) if len(sys.argv) > 6 else []
    rng = np.random.default_rng(seed)
    log = open(os.path.join(OUT, f"search_{tag}.log"), "a")
    hist = []
    t0 = time.time()
    with Pool(4) as P:
        cands = list(init) + [sample(rng, fam) for _ in range(nr)]
        for i in range(0, len(cands), 4):
            for sp, (sc, rs) in zip(cands[i:i + 4], evaluate(P, cands[i:i + 4])):
                hist.append(dict(score=sc, spec=sp, res=rs))
                log.write(f"R {len(hist)} {sc:.3f} ok {sum(r['ok'] for r in rs)}/{len(rs)} {json.dumps(sp)}\n"); log.flush()
        hist.sort(key=lambda x: -x["score"])
        best = hist[0]
        print("random best", round(best["score"], 3), sum(r["ok"] for r in best["res"]), best["spec"], flush=True)
        sigma = 0.12
        for it in range(ne):
            kids = [mutate(rng, best["spec"], fam, sigma) for _ in range(4)]
            ev = evaluate(P, kids)
            imp = False
            for sp, (sc, rs) in zip(kids, ev):
                hist.append(dict(score=sc, spec=sp, res=rs))
                if sc > best["score"]:
                    best = dict(score=sc, spec=sp, res=rs); imp = True
            sigma = min(0.25, sigma * 1.15) if imp else max(0.03, sigma * 0.93)
            log.write(f"E {it} best {best['score']:.3f} ok {sum(r['ok'] for r in best['res'])}/{len(TRAIN)} sigma {sigma:.3f} {json.dumps(best['spec'])}\n"); log.flush()
            if imp: print("es", it, round(best["score"], 3), sum(r["ok"] for r in best["res"]), [r["res"][:5] for r in best["res"]], flush=True)
    hist.sort(key=lambda x: -x["score"])
    json.dump(dict(best=best, top=hist[:20]), open(os.path.join(OUT, f"search_{tag}.json"), "w"), indent=1)
    print("done", round(time.time() - t0), "s; best", best["score"], best["spec"])
