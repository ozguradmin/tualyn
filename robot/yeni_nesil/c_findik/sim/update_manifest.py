#!/usr/bin/env python3
"""Write the Motion-phase results into ../manifest.json (animations, specs, sim_summary, motion notes).
Headline self-righting numbers are the RECOMMENDED hybrid firmware; the concept's own rule is reported next to it,
including at the concept's own CoM estimate (+1.6 mm, see fall.py COM_SWEEP)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
mp = os.path.join(PKG, "manifest.json")
m = json.load(open(mp))
R = json.load(open(os.path.join(HERE, "results", "clips_report.json")))
FM = json.load(open(os.path.join(HERE, "results", "fall_matrix.json")))
S = {(s["mode"], s["mu"], s["com_dz_mm"], s["catch_reflex"]): s for s in FM["summary"]}
mass = json.load(open(os.path.join(HERE, "mass_report.json")))
SW = json.load(open(os.path.join(HERE, "results", "arm_shell_sweep.json")))

def rf(s):
    return f"{s['pushes_fell_recovered']}/{s['pushes_fell']}"

m["animations"] = {k: f"anim/{k}.json" for k in
                   ("idle", "walk", "turn", "talk", "happy", "fall_recover", "sleep", "fall_back_help")}
w, t, hp = R["walk"], R["turn"], R["happy"]
c0, c16, c35 = S[("concept", 0.6, 0.0, True)], S[("concept", 0.6, 1.6, True)], S[("concept", 0.6, 3.5, True)]
c04, cnc = S[("concept", 0.4, 0.0, True)], S[("concept", 0.6, 0.0, False)]
h0, h16, h35 = S[("hybrid", 0.6, 0.0, True)], S[("hybrid", 0.6, 1.6, True)], S[("hybrid", 0.6, 3.5, True)]
h04, h0416 = S[("hybrid", 0.4, 0.0, True)], S[("hybrid", 0.4, 1.6, True)]
COM = [0.23, 4.49, 46.32]
cmp_ = t["comparison"]
wm = hp["wave_static_margin"]

sp = m["specs"]
sp["walk_speed_cm_s"] = w["speed_cm_s"]
sp["walk_speed_note"] = (f"MuJoCo: arka N20'ler %80 PWM'de (≈6 V) düz yolda {w['speed_cm_s']} cm/s (μ 0.6 ve 0.4'te aynı; "
                         f"boşta hesap 15.7 cm/s). Yürümez, tekerle yuvarlanır.")
sp["turn_rate_deg_s"] = t["yaw_rate_deg_s"]
sp["turn_note"] = (f"Ayakta 4 teker üstünde yerinde dönemez: ön tekerler serbest ama TPU lastikli olduğu için yana kaymaya direnir; "
                   f"konseptteki 'geriye yaslanıp dön' simde yalnız {cmp_['concept_lean_back_spin_TPU_front']['yaw_deg_s']}°/s dönüp "
                   f"{cmp_['concept_lean_back_spin_TPU_front']['drift_cm_s']} cm/s kayıyor (geniş yay). Çalışan yol: karnına oturup arka "
                   f"tekerlerle ters yönde kürek çekmek, {t['yaw_rate_deg_s']}°/s (μ0.4: {cmp_['belly_pivot_mu04']['yaw_deg_s']}°/s); "
                   f"karın PLA'sı masada sürtünür, pivot noktasına keçe/PTFE ped önerilir. Ön tekerlere sert PLA/PETG jant takılırsa "
                   f"geriye yaslanıp 4 teker üstünde {cmp_['lean_back_spin_if_front_wheels_hard_PLA_mu035']['yaw_deg_s']}°/s döner "
                   f"({cmp_['lean_back_spin_if_front_wheels_hard_PLA_mu035']['drift_cm_s']} cm/s kayma; arka kalça +5° sınırında).")
sp["mass_g"] = 301
sp["mass_note"] = (f"CAD hacim x PLA yoğunluğu + gerçek parça kütleleri; simde 300.9 g, ağırlık merkezi zeminden {COM[2]:.1f} mm. "
                   f"Konseptin kendi hesabı 47.9 mm (kablo kütlesini güverteye toplar); kalkma bu farka duyarlı, sim/fall.py iki değeri de test eder.")
sp["battery"] = ("2S 14500 900 mAh Li-ion (7.4 V, 6.7 Wh), baskı pil yuvasında (iç uzunluk 53.6 mm; 2'li AA tutucudan sökülen yay/plaka "
                 "kontaklar) + 2S BMS + USB-C 2S şarj")
sp["self_righting"] = (
    f"Yana devrilince alttaki iki bacağı dışarı süpürür (ön 80°, arka 118°), yumurta gövde yuvarlanır, ~1 s'de ayakta. "
    f"Önerilen 'hibrit' yazılımla (yan eğim 50°'yi geçer geçmez toparlan): kafadan 12 yöne itmede devrilen {h0['pushes_fell']} "
    f"durumun {h0['pushes_fell_recovered']}'i kalktı; konseptin kendi ağırlık merkezi hesabında (+1.6 mm) {rf(h16)}, +3.5 mm'de {rf(h35)}, "
    f"μ0.4'te {rf(h04)}. Konseptin kendi kuralı (60°'de 0.3 s bekle) bu kütle modelinde {rf(c0)}, ama konseptin ağırlık merkezinde "
    f"yalnız {rf(c16)}, +3.5 mm'de {rf(c35)}: o kural tek başına güvenilmez. Sırtüstü/yüzüstü/ters düşüşte kalkamaz, yardım ister (0/3).")
sp["runtime_note"] = "çalışma süreleri konseptin güç tablosundan (hesap), sim değil"

curve = FM["com_curve_mu06"]
m["sim_summary"] = {
    "status": "done (MuJoCo 3.17, sim/)",
    "engine": "MuJoCo 3.17, 1 ms step, implicitfast, elliptic cones; MJCF link frames = model.glb nodes (same origins, axes, zero; asserted by sim/verify_replay.py)",
    "model": {"mass_g": 300.9, "com_mm": COM, "com_concept_estimate_mm_z": 47.9, "body_g": round(mass["body_g"], 1),
              "collision": "convex hulls of the real meshes (egg shell, 2 ears, 4 arm+boot); tyres = cylinders r15 x 6.8; body<->leg contact excluded (hull would fill the sockets) -> joint limits set from the arm-vs-shell sweep instead",
              "servo": "MG90S: ±0.20 N·m, 600°/s torque-speed line, kp 2.9 N·m/rad, armature 5e-5",
              "n20": "6 V 100 rpm, 0.10 N·m stall (conservative), brake = back-EMF damping + 0.006 N·m gearbox friction",
              "friction": "PLA shell = desk μ (0.6 / 0.4); TPU tyres 0.9 at μ0.6, 0.4 at μ0.4 (worst case); tyre contact softened (TPU)"},
    "joint_limits_deg": {j: [m["joints"][j]["min"], m["joints"][j]["max"]] for j in ("hip_fl", "hip_fr", "hip_rl", "hip_rr")},
    "joint_limits_basis": {j: {"clear_range_deg": v["clear_range_deg"], "inside": v["manifest_inside_clear"]} for j, v in SW.items()},
    "walk_speed_cm_s": w["speed_cm_s"],
    "walk_speed_cm_s_mu04": w["speed_cm_s_mu04"],
    "turn_rate_deg_s": t["yaw_rate_deg_s"],
    "turn_comparison_deg_s": {k: v for k, v in cmp_.items()},
    "recovery": (f"RECOMMENDED hybrid firmware (tuck the lower-side legs 80°/118° as soon as the side tilt passes 50°, fore/aft tilts use the concept rule, + paw-catch reflex): "
                 f"μ0.6 {rf(h0)} falls recovered at the sim CoM, {rf(h16)} at the concept's own CoM (+1.6 mm), {rf(h35)} at +3.5 mm; μ0.4 {rf(h04)} ({rf(h0416)} at +1.6 mm). "
                 f"The concept's own rule (tilt > 60° for 0.3 s): {rf(c0)} at the sim CoM but only {rf(c16)} at the concept CoM and {rf(c35)} at +3.5 mm (μ0.4: {rf(c04)}). "
                 f"Side drops ±15° pitch 6/6 in every configuration; back/face/upside-down 0/3 (asks for help). The fall_recover clip uses the hybrid firmware."),
    "recovery_com_curve_mu06": {"what": "[com_dz_mm, recovered, fell] for 24 head pushes at μ0.6 (com_dz = body CoM raised; +1.6 = concept estimate)", **curve},
    "recovery_matrix": list(S.values()),
    "notes": [
        "Every clip is a MuJoCo result (also idle/talk/happy/sleep): joint targets go to the simulated servos and the base pose is what the sim produced.",
        "Fall tests: a 'finger' pushes at the top of the head at 30 or 90°/s tilt speed toward 12 directions and lets go at 40° (just past the 38° side tip angle). The finger is not shown in the viewer.",
        "In dynamic side falls the egg does NOT stop on its side: it keeps rolling to ~100-105° (partly onto the back). The concept rule only works when its 0.3 s timer fires while the egg is still rolling, which is why it is so sensitive to the CoM height; the hybrid trigger tucks during the fall.",
        f"Without the paw-catch reflex, back pushes end on the back: {rf(cnc)} recovered (concept rule).",
        f"Joint limits come from a winding-number arm-vs-shell sweep (sim/check_arm_shell.py): front {m['joints']['hip_fl']['min']}..{m['joints']['hip_fl']['max']}°, rear {m['joints']['hip_rl']['min']}..{m['joints']['hip_rl']['max']}°. The concept's −5/−12° minima put the arm 1.6 mm / the N20 boot sleeve 4 mm into the shell; 122° grazed the cap. Inside the new limits the front and rear tyres can never touch.",
        "Turning: with TPU on the free front wheels the robot can hardly turn on 4 wheels (skid steer, see turn_comparison). The turn clip uses a belly-pivot spin (sit, paddle); the rear tyres carry only ~10 % of the weight and chatter, so the real rate is uncertain, and the cream PLA belly slides on the desk at μ 0.6 (wear; the two M2 belly screws are 3-5 mm above the lowest point, a felt/PTFE dot at the pivot is recommended). Hard PLA/PETG front rims are the preferred fix (lean-back spin on 4 wheels).",
        f"Wave (happy): FR 40°, RL 8°, RR 65° (RL kept ≥ 5° for shell clearance); on 3 wheels the CoM stays {wm['min_mm']} mm inside the support triangle (min over the wave, sim).",
        "Servos touch the 0.20 N·m stall only for milliseconds (happy bounce, sitting down for the turn, back-fall rocking); never for long.",
        "TPU tyres may sink up to ~1.3 mm into the floor in the sim during the sit-down/wave (soft tyre contact standing in for TPU compression).",
        "Loop clips (idle, talk): the residual drift after one loop (≤1.6 mm, ≤0.02°) is spread linearly so the loop closes.",
    ],
}
rcp = os.path.join(HERE, "results", "replay_check.json")
if os.path.exists(rcp):
    rc = {k: v for k, v in json.load(open(rcp)).items() if not k.startswith("_")}
    rc_all = json.load(open(rcp))
    m["sim_summary"]["replay_check"] = rc_all
    m["sim_summary"]["notes"].append(
        "Replay check (sim/verify_replay.py: GLB forward kinematics with the rig.js convention; MJCF body positions/axes/ranges parsed and asserted equal to the GLB/manifest): every clip, every frame: "
        f"lowest visible point {min(v['min_z_mm'] for v in rc.values()):.2f} mm to +{max(v['max_gap_mm'] for v in rc.values()):.2f} mm (no visible floating), "
        f"tyres/hubs never inside the egg hull ({max(v['tyre_hub_in_egg_hull_mm'] for v in rc.values()):.1f} mm), arm/boot sleeve never inside the shell skin "
        f"({max(v['arm_in_shell_mm'] for v in rc.values()):.2f} mm), front/rear tyre clearance ≥ {min(v['tyre_tyre_clearance_mm'] for v in rc.values()):.1f} mm. "
        "Posecheck strips: stills/anim_*.png (anim_walk_follow = close follow camera, base wrapped every 30 cm so the grid stays under the robot).")
notes = [n for n in m.get("realism_notes_tr", []) if not n.startswith("Hareket:") and not n.startswith("Renk:") and not n.startswith("Kablolar:")]
notes.insert(0, "Renk: karamel parçalar Bambu Lab PLA Matte Caramel (katalog rengi #AE835B) varsayıldı; gerçekte konsept görselindeki parlak altın-turuncudan "
                "daha kahverengi, sütlü kahve tonundadır. Bu sahnenin ışığı renkleri açtığı için modeldeki albedo koyulaştırıldı (#745034): aydınlık yüzler "
                "swatch'tan biraz açık, gölgeler biraz koyu görünür. Türkiye'de bu rengin satıcısı doğrulanmadı; baskı stüdyosu başka marka açık kahve/latte "
                "PLA kullanırsa ton değişir. Gövde mat fildişi/krem PLA; saf beyaz değil.")
notes.insert(8, "Kablolar: arka N20 motor kabloları kolun iç yüzündeki kanaldan kalça eksenine 4.6 mm kadar yaklaşır ve servo korna deliğinden (Ø12.6) "
                "gövdeye girer; kol dönerken kablo yalnızca eksen çevresinde döner/burulur, gövdede ~4 cm servis halkası vardır. Bu güzergah konseptte yoktu, burada eklendi.")
notes += [
    f"Hareket: Fındık yürümez, arka tekerleriyle yuvarlanır (simde {w['speed_cm_s']} cm/s). Bacaklar yalnız duruş, eğilme, el sallama ve kalkma için.",
    f"Hareket: TPU lastikli serbest ön tekerler yüzünden ayakta yerinde dönmesi çok zayıf (~7-9°/s, geniş yay). Dönmek için karnına oturup arka tekerleri ters çevirir (~{round(t['yaw_rate_deg_s'])}°/s); "
    "bu sırada krem karın masada sürtünür (pivot noktasına keçe/PTFE ped önerilir). Ön tekerlere sert plastik jant takmak dönmeyi düzeltir.",
    f"Hareket: yana düşünce kendini kaldırır, ama yalnız önerilen hibrit yazılımla güvenilir: simde {rf(h0)}, konseptin kendi ağırlık merkezinde {rf(h16)}. "
    f"Konseptin kendi kuralı ağırlık merkezi birkaç mm yükselince çöküyor ({rf(c0)} -> {rf(c16)} -> {rf(c35)}). Sırtüstü veya yüzüstü düşerse kalkamaz ve yardım ister.",
]
m["realism_notes_tr"] = notes
m["tagline_tr"] = ("Avuç içi kadar bir hamster: dört teker-patiyle masada koşturur, el sallar, eğilir; yana devrilince bacaklarını savurup "
                   "hacıyatmaz gibi kendini toparlar, sırtüstü düşerse yardım ister.")
json.dump(m, open(mp, "w"), ensure_ascii=False, indent=1)
print("manifest updated:", list(m["animations"]))
