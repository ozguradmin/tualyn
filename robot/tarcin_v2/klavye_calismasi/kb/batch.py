#!/usr/bin/env python3
"""Batch evaluation on keyboards.
cases: terrain in {K1,K2} x mode in {rows (real keyboard, heading along the rows), diag (3x-deep key field, heading
30-45 deg to the rows)} x friction in {0.3, 0.4, 0.6} x seeds.
usage: batch.py <gait-spec.json | baseline> <tag> [nseeds] [terrains] [mus] [modes]"""
import sys, os, json, math, time
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OUT = os.path.join(os.path.dirname(HERE), "out")
os.makedirs(OUT, exist_ok=True)

DIAG = [30, 45, 135, 150, 210, 225, 315, 330]
FOOT_R = 60.0      # mm: body centre to the outermost paw corner + margin


def paws_on_keys(kb, hd, x0, y0, yj, cov_min=0.35):
    """every paw sole (17 x 21 mm, rest pose: fl/fr centre y=-31.6, hl/hr y=+29.0, x=+-23.3 in the body frame)
    has >= cov_min of its area on key tops (so no paw starts over a blank / pothole)"""
    psi = math.radians(hd + yj) + math.pi / 2
    c, s = math.cos(psi), math.sin(psi)
    gx = np.linspace(-8.5, 8.5, 7); gy = np.linspace(-10.5, 10.5, 8)
    import kbsim
    tx = 23.3 + 1000.0 * kbsim.VARIANT.get("track_add", 0.0)
    for bx, by in ((tx, -31.6), (-tx, -31.6), (tx, 29.0), (-tx, 29.0)):
        n = k = 0
        for ox in gx:
            for oy in gy:
                px, py = bx + ox, by + oy
                wx, wy = x0 + c * px - s * py, y0 + s * px + c * py
                n += 1; k += kb.on_key(wx, wy, margin=0.0)
        if k / n < cov_min: return False
    return True


def start(kind, mode, seed, kb):
    r = np.random.default_rng(seed * 7919 + (1 if kind == "K2" else 2) + (10 if mode == "diag" else 0))
    for _ in range(200):
        st = _start(kind, mode, seed, kb, r)
        if paws_on_keys(kb, st[0], st[1], st[2], st[3]): return st
    return st


def _start(kind, mode, seed, kb, r):
    W, D = kb.key_x[1], kb.key_y[1]
    if mode == "rows":
        hd = 0.0 if seed % 2 == 0 else 180.0
        a = 41.0 + 8.0 + r.uniform(0, 19.05 if kind == "K1" else 45.0)
        x0 = a if hd == 0 else W - a
        yc = (62.0 if kind == "K2" else D / 2 - 8.0) + r.uniform(-14, 14) * (1.0 if kind == "K2" else 10 / 14)
        tgt = 250.0
        return hd, x0, yc, float(r.uniform(-3, 3)), tgt
    hd = float(DIAG[seed % len(DIAG)])
    L = 250.0
    dx, dy = L * math.cos(math.radians(hd)), L * math.sin(math.radians(hd))
    xs = (FOOT_R, W - FOOT_R - abs(dx)); ys = (FOOT_R, D - FOOT_R - abs(dy))
    x0 = r.uniform(*xs); y0 = r.uniform(*ys)
    if dx < 0: x0 = W - x0
    if dy < 0: y0 = D - y0
    return hd, float(x0), float(y0), float(r.uniform(-3, 3)), L


def make_ctrl(spec):
    import ctrl
    if spec == "baseline": return ctrl.Baseline()
    if spec.get("kind") == "baseline":
        return ctrl.Baseline(spec.get("p"), heading_hold=spec.get("heading_hold", 0.0))
    import rgait
    return rgait.Rough(spec)


def one(args):
    spec, kind, mode, mu, seed, t_max = args
    import kbd, kbsim
    try:
        if kind == "flat":
            kb = None
            r = kbsim.Run(None, 0.0, 0.0, 0.0, yaw_jitter_deg=2.0 * seed, mu_desk=mu, target_mm=250.0)
            st = (0.0, 0.0, 0.0, 2.0 * seed, 250.0)
        else:
            tilt = float(os.environ["KB_TILT"]) if os.environ.get("KB_TILT") else None
            kb = kbd.Keyboard(kind, "real" if mode == "rows" else "field", seed=seed, mu=mu, tilt=tilt)
            st = start(kind, mode, seed, kb)
            hd, x0, y0, yj, tgt = st
            r = kbsim.Run(kb, hd, x0, y0, yaw_jitter_deg=yj, target_mm=tgt)
        t = time.time()
        res = r.go(make_ctrl(spec), t_max=t_max, log_every=0.5)
        res.update(kind=kind, mode=mode, mu=mu, seed=seed, start=[round(v, 1) for v in st], kb=kb.info() if kb else None,
                   wall=round(time.time() - t, 1))
        return res
    except Exception as e:
        import traceback
        return dict(kind=kind, mode=mode, mu=mu, seed=seed, result="error", err=traceback.format_exc()[-800:])


def run_batch(spec, tag, nseeds=8, terrains=("K1", "K2"), mus=(0.3, 0.4, 0.6), modes=("rows", "diag"), t_max=30.0,
              procs=4, flat=True):
    jobs = []
    for kind in terrains:
        for mode in modes:
            for mu in mus:
                for sd in range(nseeds):
                    jobs.append((spec, kind, mode, mu, sd, t_max))
    if flat:
        for mu in (0.6, 0.4):
            for sd in range(3):
                jobs.append((spec, "flat", "flat", mu, sd, t_max))
    with Pool(procs) as P:
        res = P.map(one, jobs, chunksize=1)
    import kbsim
    import tarcin as T
    json.dump(dict(spec=spec, variant=dict(kbsim.VARIANT), tau=T.TAU, results=res), open(os.path.join(OUT, f"batch_{tag}.json"), "w"), indent=0)
    return res


def summary(res):
    from collections import defaultdict
    g = defaultdict(list)
    for x in res:
        g[(x["kind"], x["mode"], x["mu"])].append(x)
    lines = []
    for k in sorted(g):
        xs = g[k]
        ok = [x for x in xs if x["result"] == "success"]
        why = defaultdict(int)
        for x in xs:
            if x["result"] != "success": why[x["result"]] += 1
        sp = np.mean([x["speed_cm_s"] for x in ok]) if ok else float("nan")
        hp = max((x.get("hip", {}).get("peak", 0) for x in xs), default=0)
        kp = max((x.get("knee", {}).get("peak", 0) for x in xs), default=0)
        h95 = np.mean([x["hip"]["p95"] for x in xs if "hip" in x]) if xs else 0
        k95 = np.mean([x["knee"]["p95"] for x in xs if "knee" in x]) if xs else 0
        ksat = np.mean([x["knee"]["sat"] for x in xs if "knee" in x]) if xs else 0
        hsat = np.mean([x["hip"]["sat"] for x in xs if "hip" in x]) if xs else 0
        lines.append(f"{k[0]:4s} {k[1]:5s} mu{k[2]:.1f}: {len(ok):2d}/{len(xs):2d}  v={sp:5.2f} cm/s  "
                     f"hip p95 {h95:.3f} sat {hsat:.3f} | knee p95 {k95:.3f} sat {ksat:.3f}  fails {dict(why)}")
    return "\n".join(lines)


if __name__ == "__main__":
    spec = sys.argv[1]
    spec = "baseline" if spec == "baseline" else json.load(open(spec)) if spec.endswith(".json") else json.loads(spec)
    tag = sys.argv[2]
    ns = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    ter = sys.argv[4].split(",") if len(sys.argv) > 4 else ["K1", "K2"]
    mus = [float(v) for v in sys.argv[5].split(",")] if len(sys.argv) > 5 else [0.3, 0.4, 0.6]
    modes = sys.argv[6].split(",") if len(sys.argv) > 6 else ["rows", "diag"]
    if os.environ.get("TAU"):
        import kbsim, tarcin as T
        T.TAU = float(os.environ["TAU"]); T.DAMP_OVERRIDE = 0.20 / T.W0     # sagging pack: weaker stall torque, same back-EMF
    if len(sys.argv) > 7:
        import kbsim
        kbsim.VARIANT.update(json.loads(sys.argv[7]))
    t = time.time()
    res = run_batch(spec, tag, ns, ter, mus, modes)
    print(summary(res))
    print("wall", round(time.time() - t, 1))
