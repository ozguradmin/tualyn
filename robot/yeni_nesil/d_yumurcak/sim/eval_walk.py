import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from search_gait import run
from multiprocessing import Pool
C = [dict(f=2.0,A=24,c=4,K0=32,dK=16,duty=0.5), dict(f=2.0,A=24,c=8,K0=32,dK=24,duty=0.5),
     dict(f=2.0,A=24,c=4,K0=32,dK=24,duty=0.5), dict(f=2.5,A=24,c=4,K0=32,dK=16,duty=0.5),
     dict(f=2.0,A=24,c=4,K0=32,dK=20,duty=0.55), dict(f=1.5,A=24,c=4,K0=32,dK=20,duty=0.5)]
def job(a):
    p, mu, slew = a
    common.Sim.__init__.__defaults__ = (0.6, slew)
    r = run(p, mu=mu, mode="walk", T=6.0)
    r["mu"]=mu; r["slew"]=slew
    return r
if __name__ == "__main__":
    args = [(p, mu, sl) for p in C for mu in (0.6, 0.4) for sl in (300.0,)]
    with Pool(2) as P: R = P.map(job, args)
    for r in R:
        print(r["p"], r["mu"], r["slew"], "v=%.2f dx=%.1f dpsi=%.1f tau=%.3f up=%s pen=%.2f" % (r["speed_cm_s"], r["dx"], r["dpsi"], r["max_tau"], r["upright"], r["pen"]))
