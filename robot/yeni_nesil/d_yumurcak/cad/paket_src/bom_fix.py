#!/usr/bin/env python3
"""Review round 2: power switch = slide switch on the back (as modelled) + P-MOSFET high-side switch;
recompute every total and the lean variant from their components. Idempotent."""
import json, os
PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
f = os.path.join(PKG, "bom.json")
b = json.load(open(f))
items = [it for it in b["items"] if not any(k in it["part"] for k in ("KCD1", "IC205", "IRF4905", "100 k 1/4 W"))]
new = [
    {"part": "IC205 3-pin slide switch (SS12D00 class, 10.5 x 5.7 mm), main power at the back under the USB-C port; switches only the MOSFET gate",
     "qty": 1, "unit_tl": 6.23, "line_tl": 6.23, "shop": "Robotistan", "url": "https://www.robotistan.com/ic205-180-derece-surgulu-switch",
     "stock": "in stock (qty 768)", "checked": "2026-10-25", "verified_on_page": True, "role": "power",
     "note": "Replaces the KCD1 rocker: a 19 x 13 mm rocker does not fit under the belly (haunch balls, cells and BMS fill it), and the model shows this slide-switch slot at the back. A slide switch of this class is rated ~0.5 A, so it must not carry the ~4 A get-up peak."},
    {"part": "IRF4905 P-channel MOSFET TO-220 (55 V, 20 mOhm): high-side main switch after the BMS, gate pulled up, slide switch pulls it to GND",
     "qty": 1, "unit_tl": 55.64, "line_tl": 55.64, "shop": "Robotistan", "url": "https://www.robotistan.com/irf4905-74a-55v-p-mosfet-to220",
     "stock": "in stock (qty 4, low)", "checked": "2026-10-25", "verified_on_page": True, "role": "power",
     "note": "Vgs is -6 to -8.4 V on a 2S pack, so it is fully on; ~0.3-0.5 W at a 4 A peak, laid flat on the perfboard."},
    {"part": "100 k 1/4 W resistor (MOSFET gate pull-up)", "qty": 1, "unit_tl": 0.24, "line_tl": 0.24, "shop": "Robotistan",
     "url": "https://www.robotistan.com/14w-100k-direnc-paketi-10-adet", "stock": "in stock (qty 11875)", "checked": "2026-10-25",
     "verified_on_page": True, "role": "power"},
]
# insert where the KCD1 line was (index 11)
items[11:11] = new
b["items"] = items
bought = [it for it in items if it.get("verified_on_page")]
parts = round(sum(it["line_tl"] for it in bought), 2)   # local services (welding, sheet) are in services_tl
b["parts_tl"] = parts
b["parts_tl_verified_online"] = round(sum(it["line_tl"] for it in bought), 2)
sub = {}
for it in bought:
    sub[it["shop"]] = round(sub.get(it["shop"], 0) + it["line_tl"], 2)
b["subtotal_by_shop"] = sub
b["shipping_breakdown"][0]["order_tl"] = sub["Robotistan"]
svc = b["services_tl"]; pr = (b["print"]["tl_min"], b["print"]["tl_max"]); sh = b["shipping_tl"]
lo = parts + svc[0] + pr[0] + sh[0]; hi = parts + svc[1] + pr[1] + sh[1]; ty = parts + 285 + 950 + 300
r10 = lambda x: int(round(x / 10.0) * 10)
b["total_tl"] = [r10(lo), r10(hi)]
b["total_typical_tl"] = r10(ty)
b["total_basis"] = (f"Minimum: verified parts {parts} + services {svc[0]} + print {pr[0]} + shipping {sh[0]} = {lo:.2f}. "
                    f"Maximum: parts + services {svc[1]} + print {pr[1]} + shipping {sh[1]} = {hi:.2f}. "
                    f"Typical: parts + 285 services + 950 print + 300 shipping = {ty:.2f}. Rounded to 10 TL. "
                    "Excludes tools (0-762) and the optional on-board voice (+505.80).")
lv = b["lean_variant"]
removed = 125.8 + 423.35 + 101.6
lv["parts_tl"] = round(parts - removed, 2)
# lean services: only the battery welding (75-150); the smoked sheet is dropped. Print/shipping as the full build.
llo = lv["parts_tl"] + 75 + pr[0] + sh[0]; lhi = lv["parts_tl"] + 150 + pr[1] + sh[1]
lv["total_tl"] = [r10(llo), r10(lhi)]
lv["total_basis"] = (f"Minimum: lean parts {lv['parts_tl']} + battery welding 75 + print {pr[0]} + shipping {sh[0]} = {llo:.2f}. "
                     f"Maximum: lean parts + welding 150 + print {pr[1]} + shipping {sh[1]} = {lhi:.2f}. "
                     "Same print range as the full build (the PETG visor was already inside the print estimate).")
b["changes_vs_concept"] = [c for c in b["changes_vs_concept"] if not c.startswith("Power switch")] + [
    "Power switch: the BOM's KCD1 rocker 'under the belly' did not fit there and was not modelled; replaced by the slide switch the model shows at the back (IC205, 6.23) driving an IRF4905 P-MOSFET high-side switch (55.64) + 100 k pull-up, so no battery current flows through the small switch (+57.27 TL)."]
b["risks"] = [r for r in b["risks"] if not r.startswith("IRF4905")] + [
    "IRF4905 stock at Robotistan is 4; any TO-220 P-MOSFET with Rds(on) <= 50 mOhm at Vgs -4.5 V works."]
import re
b["method"] = re.sub(r"All \d+ bought lines", f"All {len(bought)} bought lines", b["method"]) + ("" if "2026-10-25" in b["method"] else " The switch, MOSFET and 100 k lines were fetched live on 2026-10-25.")
json.dump(b, open(f, "w"), indent=1, ensure_ascii=False)
print(parts, b["total_tl"], b["total_typical_tl"], lv["parts_tl"], lv["total_tl"], sub)
