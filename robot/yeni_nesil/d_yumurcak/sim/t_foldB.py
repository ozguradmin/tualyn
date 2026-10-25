import sys, os; os.environ["STRATEGY"] = "hybrid"; sys.path.insert(0, '.')
import fall
from multiprocessing import Pool
HARD = ["shove back-left", "nudge backwards", "nudge forwards (face down)", "shove forwards (face down)", "dropped upside down (2 cm)", "placed on its back, legs out", "placed face down, legs out"]
def job(a):
    kn, yw, case, mu = a
    fall.FOLD_B["knee"] = kn; fall.FOLD_B["yaw"] = yw
    r = fall.run_case(case, mu)
    return kn, yw, case, mu, r["success"], r["final_tilt"]
if __name__ == "__main__":
    V = [tuple(map(int, v.split(","))) for v in sys.argv[1:]]
    with Pool(2) as P: R = P.map(job, [(kn, yw, c, 0.6) for kn, yw in V for c in HARD])
    for kn, yw in V:
        rr = [r for r in R if r[0] == kn and r[1] == yw]
        print(kn, yw, "%d/%d" % (sum(r[4] for r in rr), len(rr)), [(r[2][:14], r[5]) for r in rr if not r[4]])
