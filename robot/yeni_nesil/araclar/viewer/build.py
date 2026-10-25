#!/usr/bin/env python3
"""Build the Kıpır viewer.

Outputs:
  dist/index.html            page with the JS bundle inlined; assets fetched from dist/pkg/ (artifact, http server)
  dist/pkg/...               catalog.json + one folder per robot (manifest, model.glb, faces, anim, bom)
  dist/kipir_tek_dosya.html  fully self-contained offline version (assets embedded as base64)

Usage: python3 build.py --pkg KEY=/path/to/package [--pkg ...] [--jury jury.json] [--tr tr_overlay.json] [--no-offline]

--tr (default src/tr_overlay.json): Turkish text for package fields that are still in English
(BOM part and shop names, print summary, lean variant, simulation notes). It is merged into
catalog.json under "tr"; the packages themselves are never edited.
"""
import argparse, base64, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")


def copy_pkg(key, src):
    dst = os.path.join(DIST, "pkg", key)
    os.makedirs(dst, exist_ok=True)
    man = json.load(open(os.path.join(src, "manifest.json")))
    files = {"manifest.json", man["glb"], "bom.json"}
    for f in (man.get("faces") or {}).values():
        files.update(f.values())
    files.update((man.get("animations") or {}).values())
    out = []
    for rel in sorted(files):
        s = os.path.join(src, rel)
        if not os.path.exists(s):
            if rel != "bom.json":
                print(f"  ! {key}: missing {rel}", file=sys.stderr)
            continue
        d = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copyfile(s, d)
        out.append(f"pkg/{key}/{rel}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg", action="append", default=[])
    ap.add_argument("--jury")
    ap.add_argument("--prices-checked", default="24-25 Ekim 2026")
    ap.add_argument("--tr", default=os.path.join(HERE, "src", "tr_overlay.json"))
    ap.add_argument("--no-offline", action="store_true")
    a = ap.parse_args()
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, "pkg"))
    assets = []
    robots = []
    for spec in a.pkg:
        key, src = spec.split("=", 1)
        assets += copy_pkg(key, src)
        robots.append({"key": key})
    cat = {"robots": robots, "prices_checked": a.prices_checked}
    if a.jury and os.path.exists(a.jury):
        cat["jury"] = json.load(open(a.jury))
    if a.tr and os.path.exists(a.tr):
        tr = json.load(open(a.tr))
        for r in robots:
            bom_p = os.path.join(DIST, "pkg", r["key"], "bom.json")
            if r["key"] in tr and os.path.exists(bom_p):
                have = tr[r["key"]].get("items", {})
                miss = [it["part"] for it in json.load(open(bom_p)).get("items", []) if it.get("part") not in have]
                if miss:
                    print(f"  ! {r['key']}: {len(miss)} BOM parts have no Turkish name (shown in English)", file=sys.stderr)
        cat["tr"] = tr
    json.dump(cat, open(os.path.join(DIST, "pkg", "catalog.json"), "w"), ensure_ascii=False, indent=1)
    assets.append("pkg/catalog.json")

    subprocess.run(["npx", "esbuild", "src/main.js", "--bundle", "--format=iife", "--minify", "--target=es2020",
                    "--outfile=dist/bundle.js", "--log-level=warning"], cwd=HERE, check=True)
    bundle = open(os.path.join(DIST, "bundle.js")).read().replace("</script", "<\\/script")
    tpl = open(os.path.join(HERE, "src", "template.html")).read()
    page = tpl.replace("<!--BUNDLE-->", "<script>" + bundle + "</script>")
    head = "<!doctype html><html lang=\"tr\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\"></head><body>"
    open(os.path.join(DIST, "artifact.html"), "w").write(page)          # fragment: the Artifact host adds the skeleton
    open(os.path.join(DIST, "index.html"), "w").write(head + page + "</body></html>")
    os.remove(os.path.join(DIST, "bundle.js"))

    if not a.no_offline:
        emb = {p: base64.b64encode(open(os.path.join(DIST, p), "rb").read()).decode() for p in assets}
        # the offline file must not wait on Google Fonts; the --f-* stacks fall back to system fonts
        off_page = re.sub(r'<link[^>]+fonts\.(?:googleapis|gstatic)\.com[^>]*>\s*', '', page)
        off = head + "<script>window.__KIPIR_ASSETS__=" + json.dumps(emb) + "</script>" + off_page + "</body></html>"
        open(os.path.join(DIST, "kipir_tek_dosya.html"), "w").write(off)
    for f in sorted(os.listdir(DIST)):
        p = os.path.join(DIST, f)
        if os.path.isfile(p):
            print(f"{f}: {os.path.getsize(p)/1e6:.2f} MB")
    tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(os.path.join(DIST, "pkg")) for f in fs)
    print(f"pkg/: {tot/1e6:.2f} MB, {len(assets)} files")


if __name__ == "__main__":
    main()
