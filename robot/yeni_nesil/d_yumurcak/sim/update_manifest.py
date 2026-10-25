#!/usr/bin/env python3
"""Patch ../manifest.json with the simulated clips, measured specs and sim_summary (run after clips.py + fall.py).
(src/make_manifest.py writes the static part; run this script after it.)"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE)
mf = os.path.join(PKG, "manifest.json")
man = json.load(open(mf))
R = json.load(open(os.path.join(HERE, "out", "clips_report.json")))
F = {(s, mu): json.load(open(os.path.join(HERE, "out", f"fall_{s}_mu{mu}.json"))) for s in ("hybrid", "concept") for mu in (0.6, 0.4)}
ok = {k: sum(r["success"] for r in v) for k, v in F.items()}
n = len(F[("hybrid", 0.6)])
first = {k: sum(r["success"] and r["attempts"] <= 1 for r in v) for k, v in F.items()}
tmax = {k: max(r["t_up"] or 0 for r in v) for k, v in F.items()}

man["animations"] = {c: f"anim/{c}.json" for c in ("idle", "walk", "turn", "talk", "happy", "fall_recover", "sleep", "fall_recover_back")}
w, w4, tu = R["walk"], R["walk_mu0.4"], R["turn"]
sp = man["specs"]
sp["walk_speed_cm_s"] = round(w["speed_cm_s"], 1)
sp["walk_speed_note"] = (f"MuJoCo ölçümü: 2 Hz çapraz tırıs, yaw ±24°, {w['speed_cm_s']} cm/s (μ 0.6), {w4['speed_cm_s']} cm/s (μ 0.4); "
                         f"7 s'de {w['lateral_drift_mm']:+.0f} mm yana kayma, servo tepe torku {w['max_servo_Nm']} N·m (MG90S 0.20). Konsept tahmini 4 cm/s idi.")
sp["turn_rate_deg_s"] = round(tu["turn_rate_deg_s"])
sp["self_righting"] = (f"MuJoCo, {n} düşme senaryosu (8 yönde hafif ve sert itme + ters/ sırt/ yüzüstü/ yan bırakma): "
                       f"{ok[('hybrid', 0.6)]}/{n} (μ 0.6), {ok[('hybrid', 0.4)]}/{n} (μ 0.4) kalkıyor. Yan düşmeler tek denemede ~4-5 s; "
                       f"sırt/yüzüstü düşmeler ancak 'yan katlama' ile 3. denemede ~11-12.5 s. Konseptin saf manevrası (sadece yumurta katlaması): {ok[('concept', 0.6)]}/{n}.")
man["sim_summary"] = {
    "engine": "MuJoCo 3.17, sim/yumurcak_mu0.6.xml & _mu0.4.xml (GLB ile birebir aynı link çerçeveleri), dt 1 ms, 345.6 g",
    "servo_model": "8 × MG90S konum servosu ±0.20 N·m, SG90 kafa ±0.15 N·m, ~600°/s (sönüm), yazılım hız sınırı 300°/s (kalkışta 60-90°/s), diz/yaw bağlı sınırı (sim/limits_coupled.json)",
    "walk_speed_cm_s": w["speed_cm_s"], "walk_speed_mu0.4_cm_s": w4["speed_cm_s"],
    "turn_deg_s": tu["turn_rate_deg_s"], "turn_mu0.4_deg_s": R["turn_mu0.4"]["turn_rate_deg_s"],
    "recovery": f"{ok[('hybrid', 0.6)]}/{n} (μ 0.6), {ok[('hybrid', 0.4)]}/{n} (μ 0.4); ilk denemede {first[('hybrid', 0.6)]}/{n}; en uzun kalkış {tmax[('hybrid', 0.6)]:.1f} s",
    "recovery_concept_only": f"{ok[('concept', 0.6)]}/{n} (μ 0.6), {ok[('concept', 0.4)]}/{n} (μ 0.4): sırt/yüzüstü düşmelerde katlanmış pati uçları yumurtayı ~131° 'baş aşağı sırt üstü' konumda tutuyor",
    "notes": ("Yan düşmelerde konseptin manevrası (patiler katlanır, alttaki iki pati 164°→0° süpürür) aynen çalışıyor: ~5 s, diz torku ≤0.16 N·m. "
              "Sırt/yüzüstü düşmelerde gerçek yaw sınırı (-20° içe) patinin ileri/geri itmesini engelliyor; konseptteki ±85° iki yönlü yaw mümkün değil. "
              "Çözüm (firmware): başarısız denemeden sonra patileri 'yan katlama'ya (diz 150°, yaw 40°) alıp yeniden dene; 145-160°/33-47° aralığında da 7/7. "
              "Sert düşmelerde servolar çarpma anında toplam ≤0.05 s 0.20 N·m sınırına dayanıyor; çarpmada zemine ≤3.2 mm yumuşak temas batması (MuJoCo temas modeli). "
              "Klipler: walk/turn/fall_recover/fall_recover_back fizik sonucu; idle/talk/happy/sleep senaryolu servo hedefleri ama aynı simde oynatıldı (devrilme yok, eğim ≤6.4°)."),
}
json.dump(man, open(mf, "w"), ensure_ascii=False, indent=1)
print(json.dumps(man["sim_summary"], ensure_ascii=False, indent=1)); print(sp["self_righting"])
