import sys, os; os.environ["STRATEGY"] = "hybrid"; sys.path.insert(0, '.')
import fall
from multiprocessing import Pool
def job(a):
    kn, yw, case, mu = a
    fall.FOLD_B["knee"] = kn; fall.FOLD_B["yaw"] = yw
    r = fall.run_case(case, mu)
    return kn, yw, case, mu, r["success"], r["final_tilt"], r["t_up"]
if __name__ == "__main__":
    V = [(150, 40), (164, 50)]
    with Pool(2) as P: R = P.map(job, [(kn, yw, c, mu) for kn, yw in V for c in fall.CASES for mu in (0.6, 0.5, 0.4)])
    for kn, yw in V:
        for mu in (0.6, 0.5, 0.4):
            rr = [r for r in R if r[0] == kn and r[1] == yw and r[3] == mu]
            print(kn, yw, mu, "%d/%d" % (sum(r[4] for r in rr), len(rr)), "max t_up %.1f" % max(r[6] or 0 for r in rr), [(r[2][:16], r[5]) for r in rr if not r[4]])
