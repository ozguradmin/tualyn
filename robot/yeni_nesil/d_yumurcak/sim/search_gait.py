#!/usr/bin/env python3
"""Grid search of the open-loop trot / turn on the MuJoCo model -> out/search_<mode>_mu<mu>.json
usage: python3 search_gait.py walk 0.6"""
import itertools, json, math, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from gait import trot_pose

MODE = sys.argv[1] if len(sys.argv) > 1 else "walk"
MU = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
T = 7.0


def run(p, mu=MU, mode=MODE, T=T, keep=False):
    s = Sim(mu)
    s.set_pose(REST)
    s.drop_to_floor(0.05)
    s.step_time(0.3, record=keep)
    t0 = s.t
    b0 = s.base()

    def ctrl(sim, t):
        tt = t - t0
        ramp = min(1.0, tt / 0.5)
        sim.target(trot_pose(tt, p, mode, ramp))
    s.step_time(T, ctrl, record=keep)
    b1 = s.base()
    fr = s.frames
    tilts = [f["tilt"] for f in fr] if fr else [s.tilt()]
    # heading change (yaw of body about Z)
    def yaw(b):
        w, x, y, z = b[3:]
        return math.degrees(math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))
    dpsi = (yaw(b1) - yaw(b0) + 540) % 360 - 180
    res = dict(p=p, dx=b1[0] - b0[0], dy=b1[1] - b0[1], dpsi=dpsi, tilt_end=s.tilt(),
               speed_cm_s=-(b1[1] - b0[1]) / T / 10.0, turn_deg_s=dpsi / T,
               max_tau=max(s.max_tau.values()), upright=s.tilt() < 20, pen=s.maxpen)
    if keep:
        return res, s
    return res


def grid():
    if MODE == "walk":
        G = dict(f=[1.0, 1.5, 2.0, 2.5], A=[16, 20, 24], c=[0, 4, 8], K0=[26, 32], dK=[16, 24], duty=[0.5, 0.6])
    else:
        G = dict(f=[1.0, 1.5, 2.0], A=[14, 18, 20], c=[2, 6], K0=[30], dK=[16, 24], duty=[0.5, 0.6])
    keys = list(G)
    out = []
    for vals in itertools.product(*[G[k] for k in keys]):
        p = dict(zip(keys, vals))
        if p["c"] - p["A"] < -20 or p["c"] + p["A"] > 85:
            continue
        out.append(p)
    return out


if __name__ == "__main__":
    ps = grid()
    print(len(ps), "candidates")
    with Pool(int(os.environ.get("NPROC", "2"))) as pool:
        R = pool.map(run, ps)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    key = (lambda r: r["speed_cm_s"] - 0.02 * abs(r["dpsi"]) - 0.05 * abs(r["dx"]) / 10) if MODE == "walk" else (lambda r: abs(r["turn_deg_s"]) - 0.5 * math.hypot(r["dx"], r["dy"]) / 10)
    R = [r for r in R if r["upright"]]
    R.sort(key=key, reverse=True)
    json.dump(R, open(os.path.join(HERE, "out", f"search_{MODE}_mu{MU}.json"), "w"), indent=1)
    for r in R[:12]:
        print(json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}))
