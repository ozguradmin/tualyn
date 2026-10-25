#!/usr/bin/env python3
"""Build the Kıpır viewer.

Outputs:
  dist/index.html            page with the JS bundle inlined; assets fetched from dist/pkg/ (http server)
  dist/pkg/...               catalog.json + one folder per robot (manifest, model.glb, faces, anim, bom)
  dist/kipir_tek_dosya.html  fully self-contained offline version (assets embedded as base64)
  dist_art/artifact.html     fragment for the Artifact host, with dist_art/pkg/ as its supporting files.
                             Artifacts serve no .glb and their CSP blocks fetches of data:/blob: URLs, so each
                             model ships as model.glb.b64.txt (base64 text) and rig.js decodes it.

Usage: python3 build.py --pkg KEY=/path/to/package [--pkg ...] [--jury jury.json] [--tr tr_overlay.json] [--no-offline]

--tr (default src/tr_overlay.json): Turkish text for package fields that are still in English
(BOM part and shop names, print summary, lean variant, simulation notes). It is merged into
catalog.json under "tr"; the packages themselves are never edited.
"""
import argparse, base64, json, os, re, shutil, struct, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")
DIST_ART = os.path.join(HERE, "dist_art")


def strip_glb_images(path):
    """Drop embedded images and texture references from a GLB in place.

    rig.js replaces every mesh material, so these images are never shown, but GLTFLoader would still load
    each one through a blob: URL, which the Artifact CSP blocks."""
    b = open(path, "rb").read()
    magic, ver, _ = struct.unpack_from("<4sII", b, 0)
    assert magic == b"glTF" and ver == 2, path
    jlen, jtype = struct.unpack_from("<II", b, 12)
    assert jtype == 0x4E4F534A, path
    js = json.loads(b[20:20 + jlen])
    if not js.get("images") and not js.get("textures"):
        return
    for k in ("images", "textures", "samplers"):
        js.pop(k, None)
    for m in js.get("materials", []):
        for d in (m, m.get("pbrMetallicRoughness", {})):
            for k in [k for k in d if k.endswith("Texture")]:
                del d[k]
    jb = json.dumps(js, separators=(",", ":")).encode()
    jb += b" " * (-len(jb) % 4)
    rest = b[20 + jlen:]
    out = struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(jb) + len(rest)) + struct.pack("<II", len(jb), 0x4E4F534A) + jb + rest
    open(path, "wb").write(out)


def write_artifact(page):
    """dist_art/: the Artifact fragment plus a copy of dist/pkg with each GLB as base64 text."""
    if os.path.exists(DIST_ART):
        shutil.rmtree(DIST_ART)
    shutil.copytree(os.path.join(DIST, "pkg"), os.path.join(DIST_ART, "pkg"))
    open(os.path.join(DIST_ART, "artifact.html"), "w").write(page)       # fragment: the Artifact host adds the skeleton
    for key in os.listdir(os.path.join(DIST_ART, "pkg")):
        d = os.path.join(DIST_ART, "pkg", key)
        if not os.path.isdir(d):
            continue
        mp = os.path.join(d, "manifest.json")
        man = json.load(open(mp))
        glb = os.path.join(d, man["glb"])
        open(glb + ".b64.txt", "w").write(base64.b64encode(open(glb, "rb").read()).decode())
        os.remove(glb)
        man["glb"] += ".b64.txt"
        man["glb_bytes"] = os.path.getsize(glb + ".b64.txt")      # for the loading percentage
        json.dump(man, open(mp, "w"), ensure_ascii=False, indent=1)


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
        if rel == man["glb"]:
            strip_glb_images(d)
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
    # same skeleton the Artifact host wraps the fragment in, so every build lays out alike (safe areas padded on :root)
    head = ("<!doctype html><html lang=\"tr\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
            "<style>:root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
            "body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style></head><body>")
    open(os.path.join(DIST, "index.html"), "w").write(head + page + "</body></html>")
    write_artifact(page)
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
    tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(DIST_ART) for f in fs)
    print(f"dist_art/: {tot/1e6:.2f} MB")


if __name__ == "__main__":
    main()
