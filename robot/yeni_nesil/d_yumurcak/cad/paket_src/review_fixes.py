#!/usr/bin/env python3
"""Review round 2 for package D: brings manifest.json specs / sim_summary / realism notes in line with bom.json,
the rest-pose GLB and the sim/out results. Idempotent. usage: python3 -I review_fixes.py"""
import json, os
PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mf = os.path.join(PKG, "manifest.json")
m = json.load(open(mf))
sp = m["specs"]
sp["dims_mm"] = [107, 122, 137]
sp["dims_note"] = ("Dinlenme pozunda (diz 30°, tabanlar Z=0) GLB'den ölçüldü: 107.1 × 122.2 × 137.0 mm. "
                   "concept.md'deki 146 mm yanlıştı; konseptin kendi ayakta STL'leri de 137 mm'de bitiyor.")
sp["battery"] = "2 × Orion 14500 900 mAh Li-ion (~3C ≈ 2.7 A, IMR değil) + 2S 5 A BMS + 3 × MP1584"
sp["battery_note"] = ("Kalkışta pil tarafında ~4 A tepe akım hücre değerini aşar: firmware servoları sırayla "
                      "sürmeli; gerilim düşmesi ve ESP32 resetlenmesi (brown-out) olasıdır.")
sp["runtime_walk_min"] = 25
sp["runtime_note"] = "25 dk yürüme ve 3.5 saat bekleme konseptin hesabıdır (yürürken ort. 11.8 W), ölçüm değildir."
sp["sensors"][0] = "MPU6050 (GY-521) IMU"
sp["charge"] = "Arkada USB-C, 2S 0.55 A şarj kartı (Motorobit), ~2 saat dolum, yuva pozunda"
sp["power_switch"] = ("Arkada, USB-C'nin altında küçük sürgü anahtar (IC205, SS12D00 sınıfı); sadece bir IRF4905 "
                      "P-MOSFET'in kapısını sürer, pil akımı anahtardan geçmez.")
sp["self_righting"] = (
    "MuJoCo, 20 düşme senaryosu (8 yönde hafif ve sert itme + ters/ sırt/ yüzüstü/ yan bırakma): "
    "20/20 (μ 0.6), 20/20 (μ 0.5), 20/20 (μ 0.4). İlk denemede kalkan: 13/20 (μ 0.6), 15/20 (μ 0.5), 13/20 (μ 0.4); "
    "bunlar ~4-5 s. Sırt/yüzüstü düşmeler ve bazı itmeler ancak 'yan katlama' ile 3. denemede ~11-12.6 s "
    "(μ 0.6'da sol-arka sert itme de; μ 0.4'te iki ön-çapraz sert itme de 3. denemeye kalıyor). "
    "'Yan katlama' konseptte yok, firmware'e eklenmesi gerekiyor; konseptin saf manevrası: 13/20.")
ss = m["sim_summary"]
ss["engine"] = ss["engine"].replace("sim/yumurcak_mu0.6.xml & _mu0.4.xml", "sim/yumurcak_mu0.6.xml, _mu0.5.xml & _mu0.4.xml")
ss["recovery"] = ("20/20 (μ 0.6), 20/20 (μ 0.5), 20/20 (μ 0.4); ilk denemede 13/20, 15/20, 13/20; en uzun kalkış 12.6 s. "
                  "Sonuçlar: sim/out/fall_hybrid_mu0.6.json, _mu0.5.json, _mu0.4.json")
ss["recovery_first_try_exceptions"] = {
    "mu0.6": ["shove back-left", "nudge backwards", "nudge/shove forwards (face down)", "dropped upside down",
              "placed on its back", "placed face down"],
    "mu0.5": ["shove towards its left (+X)", "nudge backwards", "dropped upside down", "placed on its back",
              "placed face down"],
    "mu0.4": ["nudge/shove backwards", "shove front-right", "shove front-left", "dropped upside down",
              "placed on its back", "placed face down"]}
ss["servo_load"] = ("Yürüyüşte bacak servosu tepe torku 0.157 N·m = 0.20 N·m sınırının %78'i (konseptin kendi "
                    "≤%60 dinamik kuralının üstünde; konsept 0.07 tahmin etmişti). Zor kalkışlar 0.20 N·m sınırında.")
notes = m["realism_notes_tr"]
notes[6] = ("Arkada USB-C soket ve onun altında küçük bir sürgü anahtar (IC205, SS12D00 sınıfı) görünür; anahtar "
            "bir IRF4905 P-MOSFET'i açıp kapar, akım taşımaz. Ön altta ToF sensörü için Ø6.8 mm siyah pencere vardır.")
extra = [
    "Pil: 2 × Orion 14500 900 mAh (IMR değil, ~3C ≈ 2.7 A). Kalkışta ~4 A tepe akım hücre değerini aşar; servolar sırayla sürülmeli, gerilim düşmesi/ESP32 resetlenmesi olabilir. 25 dk yürüme konseptin tahminidir (11.8 W), ölçülmedi.",
    "MG90S'ler yürürken durma torkunun ~%80'ine yükleniyor (sim tepe 0.157 / 0.20 N·m): ısınma ve yüksek akım beklenmeli. Dizler 0-164°'nin tamamını kullanıyor; birçok MG90S ancak ~160-170° döner, montajdan önce her diz servosunun uç noktaları kalibre edilmeli.",
    "Gerçek turuncu filament ekrandakinden daha koyu/doygun görünür; gözler gerçekte daha parlaktır (görüntüleyicinin ortak ışığı ve ton eşlemesi turuncuyu soluklaştırıyor).",
]
for e in extra:
    key = e[:20]
    notes[:] = [n for n in notes if not n.startswith(key)]
    notes.append(e)
for k, v in m["materials"].items():
    for f in ("note", "filament"):
        if isinstance(v.get(f), str) and "SS12D00" in v[f] and "IC205" not in v[f]:
            v[f] = v[f].replace("SS12D00 sürgü anahtar", "IC205 (SS12D00 sınıfı) sürgü anahtar")
json.dump(m, open(mf, "w"), indent=1, ensure_ascii=False)
print("manifest updated")
