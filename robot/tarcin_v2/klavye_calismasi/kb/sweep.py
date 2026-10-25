#!/usr/bin/env python3
"""Structured sweep: lift H x stance spread x period (x gait family) on a fixed sweep set (seeds 200+, not the test
seeds): flat x3, K2 rows x4, K2 diag x4, K1 diag x2. usage: sweep.py tag '<json list of specs>' [extra variant json]"""
import sys, os, json, time
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OUT = os.path.join(os.path.dirname(HERE), "out")
SET = [("flat", "flat", 0.6, 0), ("flat", "flat", 0.4, 1), ("flat", "flat", 0.6, 2),
       ("K2", "rows", 0.4, 200), ("K2", "rows", 0.3, 201), ("K2", "rows", 0.6, 202), ("K2", "rows", 0.4, 203),
       ("K2", "diag", 0.4, 200), ("K2", "diag", 0.3, 201), ("K2", "diag", 0.6, 202), ("K2", "diag", 0.4, 207),
       ("K1", "diag", 0.3, 204), ("K1", "rows", 0.3, 205)]
VAR = {}
if os.environ.get("SWEEPSET") == "val":
    MUS = (0.3, 0.4, 0.6)
    SET = [("flat", "flat", 0.6, 0), ("flat", "flat", 0.4, 1), ("flat", "flat", 0.6, 2)] + \
          [("K2", "rows", MUS[i % 3], 300 + i) for i in range(8)] + [("K2", "diag", MUS[i % 3], 300 + i) for i in range(8)] + \
          [("K1", "diag", 0.3, 310), ("K1", "rows", 0.3, 311)]


def one(a):
    spec, (kind, mode, mu, seed) = a
    import kbsim
    kbsim.VARIANT.update(VAR)
    import batch
    r = batch.one((spec, kind, mode, mu, seed, 15.0))
    return dict(kind=kind, mode=mode, mu=mu, seed=seed, result=r["result"], prog=r.get("progress_mm", 0), v=r.get("speed_cm_s", 0),
                hsat=r.get("hip", {}).get("sat", 1), ksat=r.get("knee", {}).get("sat", 1))


if __name__ == "__main__":
    tag = sys.argv[1]; specs = json.loads(sys.argv[2])
    if len(sys.argv) > 3: VAR.update(json.loads(sys.argv[3]))
    jobs = [(sp, s) for sp in specs for s in SET]
    t = time.time()
    with Pool(4) as P:
        res = P.map(one, jobs, chunksize=1)
    out = []
    for i, sp in enumerate(specs):
        rs = res[i * len(SET):(i + 1) * len(SET)]
        f = [r for r in rs if r["kind"] == "flat"]; k2 = [r for r in rs if r["kind"] == "K2"]; k1 = [r for r in rs if r["kind"] == "K1"]
        ok = lambda L: sum(r["result"] == "success" for r in L)
        vflat = np.mean([r["v"] for r in f if r["result"] == "success"]) if ok(f) else 0
        line = (f"{json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in sp.items() if k in ('gait', 'H', 'fy', 'hy', 'period', 'duty', 'dz', 'shift', 'lev_kp', 'kh', 'sway_y')})} "
                f"flat {ok(f)}/3 v{vflat:.1f} | K2 rows {ok([r for r in k2 if r['mode'] == 'rows'])}/{len([r for r in k2 if r['mode'] == 'rows'])} diag {ok([r for r in k2 if r['mode'] == 'diag'])}/{len([r for r in k2 if r['mode'] == 'diag'])} | K1 {ok(k1)}/2 | sat h{np.mean([r['hsat'] for r in rs]):.2f} k{np.mean([r['ksat'] for r in rs]):.2f} "
                f"| K2 fails {[r['result'][:5] for r in k2 if r['result'] != 'success']}")
        print(line)
        out.append(dict(spec=sp, res=rs))
    json.dump(out, open(os.path.join(OUT, f"sweep_{tag}.json"), "w"), indent=0)
    print("wall", round(time.time() - t))
