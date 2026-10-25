#!/usr/bin/env python3
"""Stretch test: climb from the desk onto the keyboard.
K1: the laptop's front edge (palm rest, deck 8-12 mm); success = all four paws on the laptop and the front paws on
    the key area (y > 0), i.e. a step-up then ~100 mm of palm rest.
K2: the keyboard's front edge (case rim ~18-21 mm at the front, then caps 7-10 mm above the plate); success = all
    four paws above the rim height - 2 mm and the front paws past the bottom key row (y > 19 mm).
The robot starts on the desk 40 mm (paw tip to edge) in front of the edge, heading +y (straight at the edge),
heading jitter +-5 deg, x offset random in the middle of the keyboard."""
import sys, os, json, math, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kbd, kbsim, tarcin as T


def setup(kind, seed, mu):
    kb = kbd.Keyboard(kind, "real", seed=seed, mu=mu)
    r = np.random.default_rng(500 + seed)
    W = kb.key_x[1]
    x0 = W / 2 + r.uniform(-60, 60)
    edge = kb.base[2]                       # front edge y of the laptop base / keyboard case
    y0 = edge - 44.0 - 40.0                 # front paw tip 40 mm before the edge
    yj = r.uniform(-5, 5)
    run = kbsim.Run(kb, 90.0, x0, y0, yaw_jitter_deg=yj, target_mm=1e9)
    if kind == "K1":
        zmin, ygoal = kb.h_deck - 2.0, 0.0
    else:
        zmin, ygoal = kb.h0 + kb.base[2] * math.tan(kb.tilt) - 2.0, 19.05
    return kb, run, zmin / 1000.0, ygoal / 1000.0


def climb_go(run, ctrl, zmin, ygoal, t_max=30.0, warm=0.6):
    s = run.s
    t0 = s.d.time
    best_up = 0
    res = "timeout"
    k = 0
    while s.d.time - t0 < t_max:
        t = s.d.time - t0
        s.step(ctrl(t, s, run))
        k += 1
        if k % 100 == 0:
            up = s.d.xmat[s.bid][8]
            PW = run.paws()
            n_up = int((PW[:, 2] > zmin).sum())
            best_up = max(best_up, n_up)
            if up < 0.5:
                res = "fell"; break
            if n_up == 4 and PW[:, 1].max() > ygoal:
                res = "success"; break
    PW = run.paws()
    return dict(result=res, t=round(s.d.time - t0, 2), best_paws_up=best_up, paws_z_mm=[round(v * 1000, 1) for v in PW[:, 2]],
                body_y_mm=round(float(s.d.qpos[1]) * 1000, 1), tilt_deg=round(math.degrees(math.acos(min(1, s.d.xmat[s.bid][8]))), 1))


if __name__ == "__main__":
    import ctrl as C, rgait
    spec = sys.argv[1]
    kinds = sys.argv[2].split(",") if len(sys.argv) > 2 else ["K1", "K2"]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    for kind in kinds:
        for mu in (0.4,):
            for sd in range(n):
                kb, run, zmin, ygoal = setup(kind, sd, mu)
                c = C.Baseline() if spec == "baseline" else rgait.Rough(json.loads(spec) if spec.startswith("{") else json.load(open(spec)))
                o = climb_go(run, c, zmin, ygoal)
                print(kind, sd, mu, kb.info().get("deck_mm", kb.info().get("plate_front_mm")), o, flush=True)
