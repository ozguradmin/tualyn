#!/usr/bin/env python3
"""Servo/power sensitivity of the closed-loop self-righting (recover2) on the concept's 24 drop orientations
(23 actually fall), desk mu 0.6.  Variants (review request):
  base    : MG90S 0.20 N*m, 600 deg/s, back-EMF droop (tarcin.py defaults)
  tau0.16 : sagging pack -> 0.16 N*m stall; back-EMF damping kept (tau and w0 both scale with voltage)
  v450    : slower servos, 450 deg/s slew and no-load speed scaled to 450/600 (same stall torque)
usage: sensitivity.py [variant ...]   -> out/sens_<variant>.json"""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tarcin as T, recover as R, recover2 as R2
VARIANTS = {
    "base": {},
    "tau0.16": dict(TAU=0.16, DAMP_OVERRIDE=0.20 / 11.0),
    "v450": dict(VMAX=math.radians(450), W0=11.0 * 450 / 600),
}
for v in sys.argv[1:] or list(VARIANTS):
    for k, val in VARIANTS[v].items(): setattr(T, k, val)
    xml = T.build(mu=0.6)
    cases = [R2.drop_case(xml, r, p) for r, p in R.orients()]
    fell = [c for c in cases if c["settled"] != "up"]
    res = dict(variant=v, servo_model=R2.SERVO_MODEL(), fell=len(fell), success=f"{sum(c['ok'] for c in fell)}/{len(fell)}",
               first_try=f"{sum(c['ok'] and c['attempts'] == 1 for c in fell)}/{len(fell)}", per_state=R2.per_state(fell), cases=cases)
    print("RESULT", v, res["success"], "first", res["first_try"], res["per_state"], flush=True)
    json.dump(res, open(os.path.join(HERE, "out", f"sens_{v}.json"), "w"), indent=1)
    import importlib; importlib.reload(T); importlib.reload(R); importlib.reload(R2)
