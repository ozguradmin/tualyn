"""Interference check of the recovery 'flank tuck' pose (knee 150, yaw 40) with the rig's own checker
(src/check_limits.py functions: paw vs analytic egg, own ball, other balls)."""
import os, sys, io, contextlib, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(os.path.join(HERE, "..", "src", "check_limits.py"))
report = g["report"]
print("leg, (yaw, knee): egg_pen, own_ball_pen, other_ball_pen, min z   (pen > 0 = collision, mm)")
for k in ("fl", "fr", "bl", "br"):
    for yw, kn in ((40, 150), (40, 145), (40, 155), (35, 150), (45, 150), (0, 164), (72, 164)):
        print(k, (yw, kn), report(k, yw, kn))
print("max interference-free knee per yaw (fl; legs are mirror images):")
res = {}
for yw in list(range(-20, 73, 4)) + [72]:
    best = None
    for kn in range(164, 60, -2):
        e, b, ob, _ = report("fl", yw, kn)
        if e <= 0 and b <= 0 and ob <= 0:
            best = kn; break
    res[yw] = best
print(res)
