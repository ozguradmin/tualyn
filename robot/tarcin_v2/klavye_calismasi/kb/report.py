#!/usr/bin/env python3
"""Tables from out/batch_<tag>.json: success per terrain x mode x friction, speed, failure causes, torque stats.
usage: report.py tag [tag ...]"""
import sys, os, json, math
import numpy as np
from collections import defaultdict
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")


def cause(x):
    r = x["result"]
    if r == "success": return "ok"
    if x["kind"] == "K2" and x["mode"] == "rows":
        ex = x.get("end_xy_mm", [0, 0])[0]
        if abs(x.get("lat_mm", 0)) >= 40: return r + ":drift-off-edge"
        if 255 <= ex <= 370: return r + ":nav-cluster"
    if x["kind"] == "K2" and x["mode"] == "diag":
        hd = x["start"][0]
        return r + (":uphill" if math.sin(math.radians(hd)) > 0 else ":downhill")
    return r


def table(tag):
    d = json.load(open(os.path.join(OUT, f"batch_{tag}.json")))
    res = d["results"]
    g = defaultdict(list)
    for x in res:
        g[(x["kind"], x["mode"], x["mu"])].append(x)
    rows = []
    for k in sorted(g, key=lambda k: (k[0] != "flat", k)):
        xs = g[k]
        ok = [x for x in xs if x["result"] == "success"]
        why = defaultdict(int)
        for x in xs:
            if x["result"] != "success": why[cause(x)] += 1
        sp = np.mean([x["speed_cm_s"] for x in ok]) if ok else float("nan")
        H = np.array([[x["hip"]["peak"], x["hip"]["p95"], x["hip"]["sat"]] for x in xs if "hip" in x])
        K = np.array([[x["knee"]["peak"], x["knee"]["p95"], x["knee"]["sat"]] for x in xs if "knee" in x])
        rows.append(dict(kind=k[0], mode=k[1], mu=k[2], ok=len(ok), n=len(xs), v=None if math.isnan(sp) else round(float(sp), 2),
                         hip_peak=round(float(H[:, 0].max()), 3), hip_p95=round(float(H[:, 1].mean()), 3), hip_sat=round(float(H[:, 2].mean()), 3),
                         knee_peak=round(float(K[:, 0].max()), 3), knee_p95=round(float(K[:, 1].mean()), 3), knee_sat=round(float(K[:, 2].mean()), 3),
                         fails=dict(why)))
    return d["spec"], rows


def md(tag):
    spec, rows = table(tag)
    s = f"### {tag}\nspec: `{json.dumps(spec) if not isinstance(spec, str) else spec}`\n\n"
    s += "| terrain | heading | mu | success | speed cm/s (successes) | hip p95 / sat | knee p95 / sat | failures |\n|---|---|---|---|---|---|---|---|\n"
    for r in rows:
        s += (f"| {r['kind']} | {r['mode']} | {r['mu']} | {r['ok']}/{r['n']} | {r['v'] if r['v'] is not None else '-'} | "
              f"{r['hip_p95']:.3f} / {100 * r['hip_sat']:.1f}% | {r['knee_p95']:.3f} / {100 * r['knee_sat']:.1f}% | "
              f"{', '.join(f'{k} {v}' for k, v in sorted(r['fails'].items())) or '-'} |\n")
    tot = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["kind"] != "flat":
            tot[r["kind"]][0] += r["ok"]; tot[r["kind"]][1] += r["n"]
    s += "\ntotals: " + ", ".join(f"{k} {a}/{b}" for k, (a, b) in sorted(tot.items())) + "\n"
    return s


if __name__ == "__main__":
    for t in sys.argv[1:]:
        print(md(t))
