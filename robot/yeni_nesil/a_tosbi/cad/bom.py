#!/usr/bin/env python3
"""BOM for concept A (TL, KDV incl.; prices from research/parts.md and GUIDE, 2026-10-24). est. = not shop-verified."""
import json
BOM = [
 ("MG90S servo (8 legs + 1 neck + 1 spare)", 10, 125.80, "Robotistan", ""),
 ("ESP32-S3 SuperMini (4 MB flash, 2 MB PSRAM) - in head", 1, 472.68, "Motorobit", ""),
 ("GC9A01 1.28in round IPS 240x240", 1, 351.50, "Robotistan (19 in stock; Motorobit 545.40, 112 stock)", ""),
 ("PCA9685 16-ch servo driver (I2C)", 1, 245.54, "guide price", ""),
 ("BMI160 IMU (flip / fall detection)", 1, 127.86, "Direnc", ""),
 ("VL53L0X ToF (cliff/edge, in chin)", 1, 423.35, "Robotistan", "optional: drop for -423 TL"),
 ("14500 Li-ion cell (2S pack)", 2, 105.48, "guide price", "verify high-drain >=4 A"),
 ("2S BMS", 1, 45.24, "guide price", "verify >=5 A"),
 ("2S 8.4 V 4 A USB-C charger", 1, 78.00, "Robolink", ""),
 ("MP1584 buck (2x servo rail 5.5 V, 1x logic 5.0 V)", 3, 53.22, "Robotistan", ""),
 ("PAM8403 amp", 1, 26.78, "Robo90", ""),
 ("Speaker 8 ohm 0.25 W 29 mm", 1, 70.76, "Robotistan", ""),
 ("USB-C panel breakout (tail)", 1, 30.00, "est.", ""),
 ("Caps 2x1000 uF + 470 uF, SS14 Schottky", 1, 40.00, "est.", ""),
 ("Copper tape (touch pads), wire, JST/Dupont, 6-core neck flex", 1, 90.00, "est.", ""),
 ("M2 screws, M2 shoulder screws (bearing pins), 2 mm acrylic offcut", 1, 70.00, "est.", ""),
]
rows = [(n, q, p, q * p, s, note) for n, q, p, s, note in BOM]
parts = sum(r[3] for r in rows)
print_lo, print_hi, ship = 650, 950, 150
out = {"rows": rows, "parts_TL": round(parts, 2), "print_TL": [print_lo, print_hi], "shipping_TL_est": ship,
       "total_TL": [round(parts + print_lo + ship), round(parts + print_hi + ship)],
       "total_without_ToF_and_spare_TL": [round(parts - 423.35 - 125.80 + print_lo + ship), round(parts - 423.35 - 125.80 + print_hi + ship)]}
json.dump(out, open("bom.json", "w"), indent=1)
for r in rows: print(f"{r[1]:>2} x {r[2]:8.2f} = {r[3]:8.2f}  {r[0]}  [{r[4]}] {r[5]}")
print("parts", round(parts, 2), "total", out["total_TL"], "lean", out["total_without_ToF_and_spare_TL"])
