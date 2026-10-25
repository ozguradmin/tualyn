import sys, os, json, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tarcin as T, gait as G
best = json.load(open(os.path.join(HERE, 'out', 'gait_best_trot_calm.json')))['p']
XML = {mu: T.build(mu=mu) for mu in (0.6, 0.4)}
res = []
for per, turn, fwd, h in itertools.product([0.42, 0.524, 0.65], [0.010, 0.016, 0.022], [0.0, 0.5], [0.0053, 0.008]):
    p = dict(best); p.update(period=per, height=h, turn=turn, fwd=fwd)
    rs = {mu: G.run(p, XML[mu], 5.0)[0] for mu in XML}
    res.append(dict(p=p, r={str(k): v for k, v in rs.items()}))
    a, b = rs[0.6], rs[0.4]
    print(per, turn, fwd, h, '| yaw', a['yaw_deg_s'], b['yaw_deg_s'], 'v', a['v_cm_s'], b['v_cm_s'], 'lat', a['lat_cm_s'], 'sat', a['sat_frac'], 'tilt', a['tilt_deg'], 'fell', a['fell'] or b['fell'], flush=True)
json.dump(res, open(os.path.join(HERE, 'out', 'turn_grid.json'), 'w'), indent=0)
