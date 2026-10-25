import sys, os, json
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OUT = os.path.join(os.path.dirname(HERE), "out")
def one(a):
    spec, var, kind, sd, mu = a
    import kbsim; kbsim.VARIANT.update(var)
    import climb, ctrl as C, rgait
    kb, run, zmin, ygoal = climb.setup(kind, sd, mu)
    c = C.Baseline() if spec == "baseline" else rgait.Rough(spec)
    o = climb.climb_go(run, c, zmin, ygoal, t_max=30.0)
    o.update(kind=kind, seed=sd, mu=mu, step_mm=round(kb.h_deck if kind == "K1" else kb.h0 - 12 * __import__('math').tan(kb.tilt), 1))
    o["paws_z_mm"] = [float(v) for v in o["paws_z_mm"]]
    return o
if __name__ == "__main__":
    tag = sys.argv[1]; spec = sys.argv[2]
    spec = spec if spec == "baseline" else json.load(open(spec))
    var = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    jobs = [(spec, var, k, sd, mu) for k in ("K1", "K2") for sd in range(8) for mu in (0.4,)]
    with Pool(4) as P: res = P.map(one, jobs, chunksize=1)
    json.dump(dict(spec=spec, variant=var, results=res), open(os.path.join(OUT, f"climb_{tag}.json"), "w"), indent=0)
    for k in ("K1", "K2"):
        r = [x for x in res if x["kind"] == k]
        print(tag, k, "success", sum(x["result"] == "success" for x in r), "/", len(r), "| results", [x["result"][:4] for x in r],
              "| max paws up", [x["best_paws_up"] for x in r], "| step mm", [x["step_mm"] for x in r], "| t", [x["t"] for x in r if x["result"] == "success"])
