"""Search the 3-wheel wave lean (front-left paw lifted to 82 deg) for the largest static margin, with the rear hip
limited to >= 5 deg (arm/boot-sleeve vs belly clearance, see check_arm_shell.py).  usage: python3 -I explore_wave_pose.py"""
import math, os, sys, itertools
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim_lib import Robot, smooth
from scipy.spatial import ConvexHull


def margin(r):
    """static margin (mm): distance of the CoM ground projection inside the hull of the floor contact points"""
    pts = [c.pos[:2] for c in r.d.contact[: r.d.ncon]
           if "floor" in (r.m.geom(c.geom1).name, r.m.geom(c.geom2).name)]
    if len(pts) < 3:
        return -99.0, []
    P = np.array(pts)
    try:
        h = ConvexHull(P)
    except Exception:
        return -99.0, []
    com = r.d.subtree_com[r.bid][:2]
    m = min(-(np.dot(eq[:2], com) + eq[2]) for eq in h.equations)
    return m * 1000, sorted(r.lowest_floor_contact_geoms())


if __name__ == "__main__":
    res = []
    for fr, rl, rr in itertools.product([30, 40, 55], [5, 8, 12], [50, 65, 80]):
        r = Robot()
        for i in range(45):
            x = i / 40
            r.target.update({'hip_fl': smooth(22, 82, (x - 0.3) / 0.7), 'hip_fr': smooth(22, fr, x),
                             'hip_rl': smooth(22, rl, x), 'hip_rr': smooth(22, rr, x)})
            r.step_frame(False)
        r.settle(0.5)
        m, g = margin(r)
        res.append((round(m, 1), fr, rl, rr, g, np.round(r.tilt(), 1).tolist()))
        print(res[-1], flush=True)
    res.sort(key=lambda x: -x[0])
    print("best:")
    for x in res[:6]:
        print(x)
