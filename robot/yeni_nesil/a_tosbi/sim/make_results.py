#!/usr/bin/env python3
"""Collect the sim outputs (out/*.json) into sim/results.json; src/write_manifest.py merges it into manifest.json."""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out")
c6 = json.load(open(os.path.join(OUT, "clips_mu0.6.json"))); c4 = json.load(open(os.path.join(OUT, "clips_mu0.4.json")))
rec = json.load(open(os.path.join(OUT, "recovery.json"))); rep = json.load(open(os.path.join(OUT, "replay_check.json")))
links = json.load(open(os.path.join(HERE, "links.json")))
S = rec["summary"]

def cat(c, mu): return S[f"{c}@{mu}"]
# ONE time basis for every group: from the moment the firmware can react (drops/tumbles: control on 0.9 s after the
# release, placed poses: 1.5 s, pushes: the push at 0.5 s) to the start of >= 1 s of stable standing on >= 3 toes.
# Only cases that actually needed righting (flip-through or edge kick) are timed.
T0 = {"systematic_drop_15mm": 0.9, "random_tumble_40mm": 0.9, "placed_still": 1.5, "pushes": 0.5, "weak_servo_4V8_random": 0.9}
def times(c, mu=None):
    return [v["t_recovered"] - T0[c] for k, v in rec[c].items()
            if v["ok"] and any(m in ("flip_through", "edge_kick") for _, m in v["modes"]) and (mu is None or k.endswith(f"@{mu}"))]
def t_from(c, mu=None):
    ts = times(c, mu)
    return (round(float(np.median(ts)), 2), round(float(max(ts)), 2)) if ts else (None, None)
ALL = [t for c in ("systematic_drop_15mm", "random_tumble_40mm", "placed_still", "pushes") for t in times(c)]
med_all, max_all = round(float(np.median(ALL)), 2), round(float(max(ALL)), 2)

tot = {mu: [0, 0] for mu in (0.6, 0.4)}
for c in ("systematic_drop_15mm", "random_tumble_40mm", "placed_still", "pushes"):
    for mu in (0.6, 0.4):
        a, b = cat(c, mu)["success"].split("/"); tot[mu][0] += int(a); tot[mu][1] += int(b)
med_drop, max_drop = t_from("systematic_drop_15mm")
med_rand, max_rand = t_from("random_tumble_40mm")
med_pl, max_pl = t_from("placed_still")
med_push, max_push = t_from("pushes")
weak = S["weak_servo_4V8_random@0.6"]["success"]
walk6, walk4, turn6, turn4 = c6["walk"], c4["walk"], c6["turn"], c4["turn"]

recovery_tr = (f"μ 0.6: {tot[0.6][0]}/{tot[0.6][1]}, μ 0.4: {tot[0.4][0]}/{tot[0.4][1]} düşüş senaryosunda kendi kendine kalktı "
               f"(26 sistematik yön, 30 rastgele 40 mm takla, 6 yere bırakılmış yan/burun/kuyruk/sırt pozu, 16 itme/kaldırma). "
               f"Çoğu düşüşte sırtüstü gelip dizleri düzlemden geçirerek öbür yüzünde ayağa kalkar (firmware tepkisinden sağlam duruşa: medyan {med_all} s, en uzun {max_all} s, tüm gruplarda aynı ölçü). "
               f"Zayıf servo (4.8 V, 0.177 N·m): {weak}. Başarısız durum bulunamadı; 'yardım iste' dalı simülasyonda hiç tetiklenmedi.")
res = {
 "animations": {k: f"anim/{k}.json" for k in ("idle", "walk", "turn", "talk", "happy", "fall_recover", "sleep")},
 "specs": {
   "walk_speed_cm_s": walk6["speed_cm_s"],
   "turn_rate_deg_s": turn6["yaw_rate_deg_s"],
   "self_righting": "Gerekmez/var: iki kabuk özdeş. Sırtüstü düşünce dizler ~160° kabuk düzleminden geçip öbür yüzde ayağa kalkar, ekran 180° döner. "
                    "Yan/burun/kuyruk üstü düşüşte alttaki bacaklar tekmeleyip gövdeyi bir yüze devirir. MuJoCo: " + recovery_tr,
 },
 "sim_summary": {
   "engine": f"MuJoCo 3.x (sim/tosbi.xml, GLB bağlantı çerçeveleriyle birebir), 1 ms adım, MG90S konum servosu ±0.20 N·m / 600°/s, 50 Hz komut, kütle {links['total_g']:.0f} g (BOM parçalarıyla), IMU = simüle ivmeölçer + gürültü, servo hattı ideal sabit 5.5 V",
   "walk_speed_cm_s": walk6["speed_cm_s"],
   "walk_speed_mu04_cm_s": walk4["speed_cm_s"],
   "walk_fast_mode_cm_s": c6["walk_fast"]["speed_cm_s"],
   "turn_rate_deg_s": turn6["yaw_rate_deg_s"],
   "turn_rate_mu04_deg_s": turn4["yaw_rate_deg_s"],
   "recovery": recovery_tr,
   "recovery_detail": {k: {"success": v["success"], "needed_righting": v["needed_righting"],
                           "t_median_s": t_from(k.split("@")[0], float(k.split("@")[1]))[0],
                           "t_max_s": t_from(k.split("@")[0], float(k.split("@")[1]))[1],
                           "max_torque_Nm": v["max_torque_Nm"], "ended_face_B": v["ended_face_B"], "fails": v["fails"]} for k, v in S.items()},
   "recovery_time_s": {"basis": "firmware tepki anından (bırakmadan 0.9 s sonra kontrol açılır / yere konan pozda 1.5 s / itme anı 0.5 s) "
                                "en az 1 s kesintisiz ayakta durmanın başladığı ana; sadece doğrulma gereken durumlar",
                       "all_median": med_all, "all_max": max_all,
                       "drop_median": med_drop, "drop_max": max_drop, "random_tumble_median": med_rand, "random_tumble_max": max_rand,
                       "placed_median": med_pl, "placed_max": max_pl, "push_median": med_push, "push_max": max_push},
   "min_servo_torque_for_recovery_Nm": "0.05 ile 14/14 (stall'ın %25'i) – geniş pay (380 g'lık önceki modelde ölçüldü, yeniden koşulmadı)",
   "tip_over_threshold": "Düz masada kolay devrilmez: 0.15 s itmede yandan ≥0.6–1.05 N·s gerekir, çapraz (45°/135°) 8 N'da bile devrilmedi (380 g'lık önceki modelde); klipte bir el kabuk kenarını 2.6 N ile kaldırıp 70°'de bırakıyor.",
   "servo_torque_Nm": {"walk": walk6["servo_torque_Nm"], "turn": turn6["servo_torque_Nm"], "fall_recover": c6["fall_recover"]["servo_torque_Nm"],
                       "happy": c6["happy"]["servo_torque_Nm"]},
   "replay_check": {k: {kk: vv for kk, vv in v.items() if kk != "z_lowest_per_frame"} for k, v in rep.items()},
   "link_masses_g": {k: v["mass_g"] for k, v in links.items() if k != "total_g"},
   "notes": [
     f"Yürüme: diyagonal tırıs, periyot 0.7 s, kalça −17…+14/+17°, diz kaldırma 20°. μ 0.6'da {walk6['speed_cm_s']} cm/s, μ 0.4'te {walk4['speed_cm_s']} cm/s; "
     f"{walk6['path_cm']} cm'de {abs(walk6['lateral_drift_cm'])} cm yana kayma. 0.5 s periyotla {c6['walk_fast']['speed_cm_s']} cm/s mümkün ama dizler "
     f"zamanın %{c6['walk_fast']['servo_torque_Nm']['knee']['time_at_clamp_pct']}'inde 0.20 N·m sınırına dayanıyor; o yüzden gösterilen yürüyüş yavaş olan.",
     f"Dönüş: yerinde, sol bacaklar ters adım; 0.8 s periyotla ~{turn6['yaw_rate_deg_s']:.0f}°/s. Ters yüzdeyken firmware dönüş yönünü çevirir.",
     "Mutlu el sallama: ön bacak kalkınca ağırlık merkezi 3 ayak üçgeninin dışında kalıyor; arka kalçalar +20°, sağ ön +14° öne alınmadan simülasyonda burnunun (kafanın) üstüne düşüyor. Klipte bu ağırlık kaydırma var; stills/action_wave bu klipten.",
     "Uyku: dizler 12°'ye iner, gövde karın kubbesine, çene (kafa) masaya oturur; ayak uçları havada kalır.",
     f"Düşüp kalkma klibi el ile animasyon değil: görünmeyen bir el kabuğun sağ kenarını 2.6 N ile kaldırıp 70°'de bırakıyor (klipte 'events' ve 'caption_tr' var), robot sırtüstü düşüyor, ivmeölçerden ters olduğunu anlayıp dizleri ~160° çeviriyor, öbür yüzünde kalkıp *_inv yüzlerle {c6['fall_recover']['walk_after_s']} s yürüyüp duruyor (toplam kayma {c6['fall_recover']['base_drift_mm']/10:.1f} cm).",
     "Basitleştirmeler: parçalar rijit dışbükey kabuklar (gerçek şekilden biraz dolgun), servo boşluğu/ölü bölgesi, plastik esnemesi ve kablo direnci yok, servo hattı ideal sabit 5.5 V (pil çökmesi yok). Gerçek hız ve dönüş büyük olasılıkla daha düşük olur; simülasyon değerleri üst sınır gibi okunmalı.",
     "Test edilmeyenler: masadan düşme (iki ToF bunu önlemek için; ToF modellenmedi), halı/yumuşak zemin, bir engelin dibinde sıkışma, düşerken çarpma hasarı, pil gerilim çökmesi.",
     "idle, talk, happy, sleep komutları el ile yazıldı (firmware'in göndereceği servo hedefleri) ama fizik içinde oynatıldı; gövde hareketi simülasyondan.",
     f"Darbede eklem sınırı: MJCF eklem sınırları sertleştirildi (solreflimit 2 ms); kalan en büyük taşma {c6['fall_recover']['joint_clamp_excess_deg']}°, klipte sınıra kırpıldı (servo mekanik durdurucuya dayanır).",
   ],
 },
}
json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(res["sim_summary"]["recovery"], ensure_ascii=False)); print(res["specs"]["walk_speed_cm_s"], res["specs"]["turn_rate_deg_s"])
