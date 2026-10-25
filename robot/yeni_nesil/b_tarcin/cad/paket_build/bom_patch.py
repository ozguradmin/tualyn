#!/usr/bin/env python3
"""Review fixes to ../bom.json (idempotent): one choice per part (IMU, speaker, ears, nose, ToF place), GPIO budget
verified from the shop's pinout image, battery/LiPo check, new risks, and totals + lean variant recomputed from
their stated basis.  Run: python3 -I bom_patch.py"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); F = os.path.join(HERE, "..", "bom.json")
b = json.load(open(F))
items = [it for it in b["items"] if not it["part"].startswith("Neodymium magnet")]      # ears are glued now
def find(prefix):
    return next(it for it in items if it["part"].startswith(prefix))
tof = find("VL53L0X")
tof["part"] = "VL53L0X ToF, black (desk-edge sensor behind the IR window in the lower chest)"
mcu = find("ESP32-S3 Super Mini")
mcu["note"] = ("GPIO budget verified from Motorobit's own pinout image (dosya.motorobit.com/resim/esp32-s3-super-mini-pinout.jpg, "
               "fetched 2026-10-25): the edge headers carry GPIO1-13 + TX43/RX44 = 15 usable pins (the '11 GPIO' in the page text "
               "undercounts; more GPIO sit on bottom pads). Body board needs 14 (9 servo PWM, I2C x2, UART x2, battery ADC on GPIO1-10), "
               "head board 12. Pin map in NOTES.md. No PCA9685 needed; if a board revision has fewer pins, a PCA9685 (Robotistan 245.54 TL, "
               "not counted) frees 9 pins but is 62 x 25 mm and does not fit the body without a layout change.")
mcu["gpio_verified"] = True
imu = find("MPU6500")
imu["note"] = "Chosen IMU everywhere in the package (manifest, GLB internals, NOTES). Replaces the concept's BMI160 (only at Direnc) to save a 4th parcel; same I2C role"
spk = find("Speaker 8")
spk["part"] = "Speaker 8 Ω 1 W 32 mm (32 x 5 mm), back of the head behind a 37-hole grille"
spk["note"] = "Modelled at 32 x 5 mm. Fits only because the head-pan micro servo body was turned to point forward; front rim 0.4 mm inside the 1.6 mm wall, 3+ mm behind the head MCU board (build/meshes/speaker_fit.json)"
chg = find("2S 8.4 V 4 A")
chg["part"] = "2S 8.4 V 4 A Type-C charge module (in-robot charger, port at the front of the belly)"
usb = find("USB-A to Type-C")
usb["note"] = "Data-capable; also used to charge via the belly port"
cell = find("14500 Li-ion")
cell["note"] = ("Orion; Robotistan gives no discharge rating, Direnc lists the same cell as 3C (~2.7 A). Recovery peaks ~4.8 A battery side. "
                "Checked 2026-10-25 for a stronger pack: the smallest in-stock 2S LiPo >= 20C at Robotistan is Tinylab 2S 850 mAh 40C "
                "(847.30 TL, qty 30) but it is 59 x 31 x 17 mm, 52 g, vs the 50.5 x 14.2 x 28.6 mm bay; JSumo 2S 450 mAh 25C (1149.09 TL, qty 4) "
                "lists no size. Neither is used: the cell stays the weak link, see risks.")
if not any(it["part"].startswith("Clear gloss varnish") for it in items):
    items.append({"part": "Clear gloss varnish for the black PLA nose (acrylic spray or nail top-coat)", "qty": 1, "unit_tl": 90, "line_tl": 90,
                  "range_tl": [40, 150], "shop": "hardware / cosmetics store", "url": None, "stock": "n/a (common item)",
                  "checked": "2026-10-25", "verified_on_page": False, "group": "forgotten",
                  "note": "Nose = black PLA + 2 coats of clear varnish (no PETG spool needed). Optional: matte nose in the lean variant"})
b["items"] = items
b["checked"] = "2026-10-25 (review update; prices/stock as fetched 2026-10-24 unless noted)"
ver = round(sum(it["line_tl"] for it in items if it.get("verified_on_page")), 2)
est = [sum(it["range_tl"][0] for it in items if not it.get("verified_on_page")), sum(it["range_tl"][1] for it in items if not it.get("verified_on_page"))]
b["parts_tl_verified"] = ver; b["parts_tl_estimated"] = est
pr = b["print"]
pr["materials"] = [
    "PLA Turuncu / Tarçın (Elas, Porima or eSun; ~#DF6E35): crown, chin cap, body top, pods, tail rings A, hubs, ears (~95 g)",
    "PLA Krem / Fildişi (~#F3EEE4): muzzle, belly, cheek windows, inner ears (~13 g)",
    "PLA Antrasit / Siyah (~#2A2C31): socks, shins, tail rings B, neck, mouth, nose (~40 g); nose gloss = 2 coats of clear varnish (no PETG, no ironing on the curved nose)",
    "TPU 95A black: paws only (~7 g)",
    "+ ~18 g PLA internal frame, hub posts, neck yoke, eye bezels (in the CAD mass budget but not in the STLs)"]
pr["basis"] = pr["basis"].replace("(PLA 140 g, TPU 12 g)", "(PLA 145 g, TPU 7 g; ears are PLA)").replace(
    "177 g PLA x 3.5-5 TL = 620-885 + 14 g TPU x 6-8 TL = 85-110", "182 g PLA x 3.5-5 TL = 637-910 + 9 g TPU x 6-8 TL = 54-72")
# shipping detail order sums from the line items
shops = {}
for it in items:
    if it.get("verified_on_page"): shops[it["shop"]] = shops.get(it["shop"], 0) + it["line_tl"]
for ps in b["shipping_detail"]["per_shop"]:
    key = {"Robolink Market": "Robolink"}.get(ps["shop"], ps["shop"])
    if key in shops: ps["order_tl"] = round(shops[key], 2)
pmin, pmax = pr["tl_min"], pr["tl_max"]; smin, smax = b["shipping_tl"]
tot = [ver + est[0] + pmin + smin, ver + est[1] + pmax + smax]
b["total_tl"] = [int(round(tot[0] / 10) * 10), int(round(tot[1] / 10) * 10)]
b["total_breakdown"] = {"parts_verified": ver, "services_and_unverified_est": est, "print": [pmin, pmax], "shipping": [smin, smax],
                        "formula": f"{ver} + {est[0]}-{est[1]} + {pmin}-{pmax} + {smin}-{smax} = {tot[0]:.2f}-{tot[1]:.2f}, rounded to 10 TL"}
lv = b["lean_variant"]
rem = round(sum(r["tl"] for r in lv["removed"]), 2)
lean_parts = round(ver - rem, 2)
est_lean = [est[0] - 40, est[1] - 150]              # no varnish (matte nose)
p_lean = [pmin, round((pmin + pmax) / 2)]
lt = [lean_parts + est_lean[0] + p_lean[0] + smin, lean_parts + est_lean[1] + p_lean[1] + smax]
lv["total_tl"] = [int(round(lt[0] / 10) * 10), int(round(lt[1] / 10) * 10)]
lv["what"] = ("Drop the spare MG90S, the VL53L0X edge sensor, the flux and the copper tape, leave the nose matte (no varnish) and take the "
              "cheaper half of the print range (a hobby studio). Formula: parts " + f"{ver} - {rem} = {lean_parts}" + " + services "
              + f"{est_lean[0]}-{est_lean[1]}" + " (acrylic visor + pack welding) + print " + f"{p_lean[0]}-{p_lean[1]}" + " + shipping "
              + f"{smin}-{smax}" + f" = {lt[0]:.2f}-{lt[1]:.2f}, rounded. Further option, not counted: one ESP32-S3 N16R8 devkit (Direnc 610.23) in the head "
              "instead of two Super Minis saves ~335 TL but adds a Direnc parcel (~100 TL), a 12-wire neck loom and a tight fit.")
cv = b["changes_vs_concept"]
cv = [c for c in cv if not c.startswith(("Magnets 6x2", "Speaker 32 mm 1 W", "Ears: rigid", "Nose: black PLA"))]
cv += ["Ears: rigid orange PLA on a pin, glued (CA). The concept's TPU ears and the magnet 'pop-off' idea are dropped, because the sim treats the ears as rigid colliders and that is what gets built. Magnets removed from the BOM.",
       "Speaker 32 mm 1 W (the concept text and calc.json); the GLB now models it at 32 x 5 mm. To fit, the head-pan micro servo body points forward instead of back.",
       "Nose: black PLA + clear varnish (was PETG in one file and PLA in another)."]
b["changes_vs_concept"] = cv
risks = [r for r in b["risks"] if not r.startswith(("ESP32-S3 Super Mini", "Battery current", "MP1584", "Head-pan servo", "Hip leads"))]
risks = [
    "Battery current: the only 14500s in stock are ~3C cells (2.7 A). Walking (~1.3 A battery side) is fine; self-righting peaks (~4.8 A for < 0.5 s) will sag the pack and may trip the 5 A BMS. A BMS trip or a brown-out mid-flip means a reset (the robot lies there until it reboots), not just a weaker kick. The MuJoCo recovery numbers assume stiff 5.5 V rails; with 0.16 N·m (a sagging pack) only 15/23 of the concept's falls recover within 4 tries and 1/23 on the first try (sim/out/sens_tau0.16.json). Mitigations: firmware staggers the hip kicks (no more than 4 servos at full torque at once), 2 x 1000 µF on the servo banks, and brown-out-safe firmware that resumes the recovery after a reset. No 2S LiPo >= 20C in stock fits the 50.5 mm bay (Tinylab 850 mAh 40C is 59 x 31 x 17 mm).",
    "MP1584 modules are 3 A peak and about 2 A continuous; each servo bank peaks near 2.9 A during recovery.",
    "Head-pan servo: a 76 g head on a 4 g plastic-gear micro servo (0.07 N·m). Falls back-drive it into its end stop (sim: neck_pan overshoots +-40° by a few degrees; peak gear load logged in sim/out/pan_load.json). Gear stripping is likely after repeated falls; keep 1-2 spare micro servos, or add a friction (O-ring) slip coupling at the horn. An MG90S does not fit the head next to the 32 mm speaker and eye PCBs.",
    "Hip leads: each hip's 6 servo wires cross into the body through an arc slot and flex at the slot lip on every hip move; recovery swings the hind hips through ~145° and the front hips through ~80° in a fraction of a second, several times per recovery. Standard PVC servo leads may crack after a few thousand recoveries. Use the softest lead available (or re-lead with 28 AWG silicone wire) and treat the leads as a wear part.",
] + risks
b["risks"] = risks
json.dump(b, open(F, "w"), indent=1, ensure_ascii=False)
print("verified", ver, "est", est, "total", b["total_tl"], "lean", lv["total_tl"], lv["what"][:200])
