import sys, json, os, itertools, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from gait import trot_pose
from multiprocessing import Pool
def yawdeg(b):
    w, x, y, z = b[3:]
    return math.degrees(math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z)))
def run(p, mu, T=5.0):
    s = Sim(mu, 300.0); s.set_pose(REST); s.drop_to_floor(0.05); s.step_time(0.3)
    t0 = s.t; b0 = s.base()
    def ctrl(sim, t):
        tt = t - t0; sim.target(trot_pose(tt, p, "turn", min(1, tt/0.5)))
    s.step_time(T, ctrl)
    ys = np.unwrap(np.radians([yawdeg(f["base"]) for f in s.frames if f["t"] >= t0]))
    b1 = s.base()
    return dict(p=p, mu=mu, rate=math.degrees(ys[-1]-ys[0])/T, drift=math.hypot(b1[0]-b0[0], b1[1]-b0[1]),
                tau=max(s.max_tau.values()), tilt=max(f["tilt"] for f in s.frames))
G = dict(f=[1.5, 2.0], A=[12, 16, 20], c=[0, 4], K0=[32], dK=[16, 24], duty=[0.5])
C = [dict(zip(G, v)) for v in itertools.product(*G.values())]
C = [p for p in C if p["c"]-p["A"] >= -20]
def job(a): return run(*a)
if __name__ == "__main__":
    with Pool(2) as P: R = P.map(job, [(p, mu) for p in C for mu in (0.6, 0.4)])
    R.sort(key=lambda r: -r["rate"])
    for r in R: print(r["p"], r["mu"], "rate=%.1f drift=%.1f tau=%.3f maxtilt=%.1f" % (r["rate"], r["drift"], r["tau"], r["tilt"]))
