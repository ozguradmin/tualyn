#!/usr/bin/env python3
"""Review update of ../manifest.json (idempotent; numbers are read from the sim outputs).
Run after the sims: python3 -I manifest_patch.py"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE); OUT = os.path.join(PKG, "sim", "out")
M = os.path.join(PKG, "manifest.json")
m = json.load(open(M))
def J(name, default=None):
    f = os.path.join(OUT, name)
    return json.load(open(f)) if os.path.exists(f) else default
def A(name):
    return json.load(open(os.path.join(PKG, "anim", name + ".json")))
L = json.load(open(os.path.join(HERE, "limits.json")))
T = L["hip_f_vs_pan"]
# ---------------- materials (one choice per part)
mt = m["materials"]
mt["ear"].update(filament="Elas PLA Turuncu (mat)", part="kulak dış kabuğu, yatık basılır; pimle kafaya oturur ve CA ile yapıştırılır (sabit, mıknatıs yok)")
mt["nose"] = {"type": "print", "color": "#1b1c1f", "filament": "Elas PLA Siyah + 2 kat şeffaf parlak vernik (sprey ya da tırnak cilası üst katı)",
              "layer": 0.12, "layerAxis": [0, 0, 1], "layerStrength": 0.3, "roughness": 0.3, "clearcoat": 0.7,
              "part": "burun: siyah PLA, vernikle parlatılmış (PETG yok; kavisli yüzeyde ütüleme yapılamaz)"}
mt["speaker"] = {"type": "rubber", "color": "#18191b", "note": "32 mm 8 Ω 1 W hoparlör (32 x 5 mm), kafanın arka duvarında, 37 delikli ızgaranın arkasında"}
mt["internal_pcb"]["note"] = "ESP32-S3 Super Mini x2, BMS, şarj kartı, MPU6500 IMU, VL53L0X, TTP223, 32 mm hoparlörün mıknatıs gövdesi"
mt["internal_servo"]["note"] = "MG90S x9 (8 bacak + kuyruk), 4 g mikro servo (kafa pan; gövdesi pan ekseninden öne doğru)"
mt["internal_wire"] = {"type": "internal", "color": "#d9822b", "note": "kalça servo kablolarının gövde içindeki boşluk (slack) halkası: kablo yay yarıktan girer, bu halka uzunluk değişimini alır"}
mt["wire_brown"]["note"] = ("servo kabloları (2 servo x kahve/kırmızı/turuncu = 6 telli yassı demet): bacak modülünün iç yüzündeki yarıktan çıkar, "
                            "kalça ekseninden 13.6 mm uzakta düz geçer ve gövdedeki kalça eksenli yay yarıktan içeri girer (bacakla birlikte döner)")
# ---------------- animations
m["animations"]["fall_recover_back"] = "anim/fall_recover_back.json"
# ---------------- specs
walk, turn, fr, frb = A("walk")["metrics"], A("turn")["metrics"], A("fall_recover")["metrics"], A("fall_recover_back")["metrics"]
r06, r04 = J("rec2_mu0.6_rc_side.json"), J("rec2_mu0.4_rc_side.json")
v06, v04, v11 = J("rec2_validate_mu0.6_m1.0.json"), J("rec2_validate_mu0.4_m1.0.json"), J("rec2_validate_mu0.6_m1.1.json")
s16, s450 = J("sens_tau0.16.json"), J("sens_v450.json")
def ps(r, st):
    p = (r or {}).get("per_state", {}).get(st)
    return f"{p['first_try']}/{p['n']}" if p else "?"
def tot(rs, st):
    n = sum(r["per_state"][st]["n"] for r in rs if r and st in r.get("per_state", {}))
    f = sum(r["per_state"][st]["first_try"] for r in rs if r and st in r.get("per_state", {}))
    ok = sum(r["per_state"][st]["ok"] for r in rs if r and st in r.get("per_state", {}))
    return f, ok, n
def fell_ok(r):
    if r is None: return "?"
    if "success_of_fallen" in r: return r["success_of_fallen"]
    fc = [c for c in r["cases"] if c["settled"] != "up"]; return f"{sum(c['ok'] for c in fc)}/{len(fc)}"
def first(r):
    if r is None: return "?"
    if "first_try_of_fallen" in r: return r["first_try_of_fallen"]
    fc = [c for c in r["cases"] if c["settled"] != "up"]; return f"{sum(c['ok'] and c['attempts'] == 1 for c in fc)}/{len(fc)}"
sf6, so6, sn6 = tot([r06, v06], "side"); bf6, bo6, bn6 = tot([r06, v06], "back")
sf4, so4, sn4 = tot([r04, v04], "side"); bf4, bo4, bn4 = tot([r04, v04], "back")
worst = max([c.get("t", 0) for r in (r06, r04, v06, v04) if r for c in r["cases"]] + [0])
worst_att = max([c["attempts"] for r in (r06, r04, v06, v04) if r for c in r["cases"] if c["ok"]] + [0])
worst6 = max([c.get("t", 0) for r in (r06, v06) if r for c in r["cases"]] + [0])
worst_att6 = max([c["attempts"] for r in (r06, v06) if r for c in r["cases"] if c["ok"]] + [0])
fails = [(f"μ {r['mu']}" + (f", kütle x{r['mass_scale']}" if r.get('mass_scale', 1.0) != 1.0 else ""), c) for r in (r06, r04, v06, v04, v11) if r for c in r["cases"] if not c["ok"]]
fail_txt = ("; ".join(f"{w}: {c.get('kind', 'drop')} roll {c.get('roll', '')}° pitch {c.get('pitch', '')}° ({c['settled']}) 4 denemede kalkamadı → yardım ister" for w, c in fails)
            if fails else "başarısız düşüş yok")
pan_peak = max([r.get("pan_gear_peak_Nm", 0) for r in (r06, r04, v06, v04, v11) if r] + [0])
pan_os = max([r.get("pan_overshoot_max_deg", 0) for r in (r06, r04, v06, v04, v11) if r] + [0])
sp = m["specs"]
sp["walk_speed_cm_s"] = walk["speed_cm_s"]; sp["turn_rate_deg_s"] = round(turn["yaw_rate_deg_s"])
sp["sensors"] = ["MPU6500 IMU (6 eksen)", "VL53L0X masa kenarı (ToF, alt göğüsteki IR pencerenin arkasında)", "TTP223 kafa dokunma", "INMP441 yok (ses telefondan/PC'den)"]
sp["voice"] = "PAM8403 + 32 mm 8 Ω 1 W hoparlör (kafa arkası 37 delikli ızgara) - cıvıltı/ses; konuşma tanıma telefon/PC üzerinden"
sp["brain"] = ("2x ESP32-S3 Super Mini (kafa: gözler, Wi-Fi/Claude API, ses; gövde: 9 servo, IMU, ToF) - UART ile bağlı. "
               "Pin bütçesi mağazanın pinout görselinden doğrulandı: kenarda 15 GPIO (1-13, TX, RX); gövde 14, kafa 12 kullanır.")
sp["battery"] = ("2S 14500 Li-ion (7.4 V, ~6 Wh, hücre ~3C / 2.7 A), 5 A 2S BMS + USB-C 2S şarj kartı (port karnın önünde). "
                 "Kalkma anında ~4.8 A tepe çekilir: paket çöker ya da BMS keserse robot yeniden başlar (risk, NOTES).")
sp["self_righting"] = (f"Kuyruk kaldıraç + bacak tekmesi (OpenCat 'rc' tarzı, IMU ile kapalı döngü), en çok 4 deneme. MuJoCo (μ 0.6, tork-hız düşüşlü servo, "
                       f"ön kalça-kafa sınırı): yan düşüş ilk denemede {sf6}/{sn6}, sırtüstü ilk denemede yalnızca {bf6}/{bn6}; μ 0.6'da hepsi en çok {worst_att6} denemede kalktı "
                       f"(en kötü ≈{worst6:.0f} s). μ 0.4'te 30 yeni düşüşten biri kalkamadı. Benzetim 5.5 V hatlarının çökmediğini varsayar; 0.16 N·m'ye düşen "
                       f"tork ile 23 düşüşten yalnızca {s16['success'].split('/')[0] if s16 else '?'}'i kalkar.")
# ---------------- sim summary
ss = m["sim_summary"]
ss["engine"] = "MuJoCo 3.17, dt 0.5 ms, model.glb kopyası (aynı eklem orijinleri/eksenleri/sıfırları), dışbükey kabuk çarpışma, 368 g"
ss["servo_model"] = ("MG90S konum servosu: kp 3 N·m/rad, sürücü torku ±0.20 N·m, komut hızı 600°/s; zıt-EMK tork-hız düşüşü: hareket yönünde en çok "
                     "0.20·(1-ω/ω0), ω0 = 11 rad/s (sönüm 0.2/11 + 0.001 sürtünme = 0.0192; yüksüz ≈600°/s). Kafa pan 4 g mikro servo ±0.07 N·m, ω0 14 rad/s. "
                     "Ön kalça ≤ tablo(neck_pan) yazılım sınırı uygulanır. (İncelemeden önce sönüm 0.012 idi: yüksüz ≈955°/s, fazla iyimser.)")
ss["walk_speed_cm_s"] = walk["speed_cm_s"]
ss["walk"] = (f"Tırıs, periyot {walk['period_s']} s, adım {walk['stride_mm']} mm, ayak kaldırma {walk['step_height_mm']} mm + IMU dengeleme. "
              f"Klipte ölçülen {walk['speed_cm_s']} cm/s (μ 0.6). Yeni servo modeliyle (tork-hız düşüşü) önceki 5.6 cm/s'den daha hızlı çıktı: "
              "daha güçlü zıt-EMK sönümü bacak titreşimini azaltıyor. Gerçekte servo ve zemin farkıyla ±%30 sapma beklenmeli.")
ss["turn"] = f"Yerinde dönüş (tırıs, ±11 mm ters adım, periyot 0.42 s): {turn['yaw_rate_deg_s']}°/s (μ 0.6), merkez kayması {turn['centre_drift_mm']} mm."
ss["recovery"] = (f"μ 0.6: konseptin 24 düşüşü {fell_ok(r06)} kalktı (ilk denemede {first(r06)}), 24 yeni + 8 itme {fell_ok(v06)} (ilk denemede {first(v06)}); "
                  f"μ 0.4: {fell_ok(r04)} (ilk {first(r04)}) ve {fell_ok(v04)} (ilk {first(v04)}); +%10 kütle μ 0.6: {fell_ok(v11)} (ilk {first(v11)}). "
                  f"İniş durumuna göre ilk deneme (μ 0.6, iki set): YAN {sf6}/{sn6}, SIRT {bf6}/{bn6}; μ 0.4: YAN {sf4}/{sn4}, SIRT {bf4}/{bn4}. "
                  f"Sırtüstü düşüşler çoğunlukla 2-3 deneme ister (her deneme ≈2.5 s + 1.3 s bekleme); en kötü başarılı durum {worst_att} deneme, ≈{worst:.0f} s. "
                  f"Başarısız: {fail_txt}.")
ss["recovery_per_state"] = {"mu0.6": {"side_first_try": f"{sf6}/{sn6}", "side_ok": f"{so6}/{sn6}", "back_first_try": f"{bf6}/{bn6}", "back_ok": f"{bo6}/{bn6}"},
                            "mu0.4": {"side_first_try": f"{sf4}/{sn4}", "side_ok": f"{so4}/{sn4}", "back_first_try": f"{bf4}/{bn4}", "back_ok": f"{bo4}/{bn4}"},
                            "sets": "konseptin 24 yönelimi (23'ü düşer) + 24 yeni rastgele yönelim ve 8 itme (30'u düşer)"}
if s16 and s450:
    ss["recovery_sensitivity"] = (f"Konseptin 23 düşüşü, μ 0.6: tam güç (0.20 N·m, 600°/s) {fell_ok(r06)} (ilk {first(r06)}); paket çökmesi 0.16 N·m {s16['success']} "
                                  f"(ilk {s16['first_try']}; yan {ps(s16, 'side')}, sırt {ps(s16, 'back')}); 450°/s servolar {s450['success']} (ilk {s450['first_try']}; "
                                  f"yan {ps(s450, 'side')}, sırt {ps(s450, 'back')}); en çok 4 deneme. Kalkma tork ve hız payı olmadan çalışıyor: diziler zayıf servolara göre yeniden ayarlanmalı. Komut: sim/sensitivity.py.")
ss["power_assumption"] = ("Kalkma benzetimi her servonun aynı anda tam 0.20 N·m verdiğini, yani 5.5 V hatlarının sabit kaldığını varsayar. Stoktaki 14500 hücreler ~3C "
                          "(2.7 A); kalkma tepesi ~4.8 A. Paket çöker ya da 5 A BMS keserse sonuç daha zayıf bir tekme değil, işlemcinin yeniden başlamasıdır. "
                          "Yazılım servoları sıraya koyar (aynı anda en çok 4 tam tork), 2x1000 µF tampon vardır. Bölmeye sığan ≥20C 2S LiPo stokta bulunamadı.")
ss["head_pan_load"] = (f"Düşüşlerde kafa (76 g) 4 g pan servosunu geri sürer: dişliye binen en büyük tork ≈{pan_peak:.2f} N·m (servonun gücü 0.07 N·m), "
                       f"pan ±40° sınırını {pan_os:.1f}°'ye kadar aşar (görüntüleyici 40°'de keser). Dişli sıyırma riski: yedek servo ya da kaydırmalı kavrama önerilir.")
ss["recovery_strategy"] = ("IMU yerçekimi vektörüne göre: sırtüstü → konseptin best_seq_13 dizisi (2. denemede aynalanır); yan → bu pakette ayarlanan yan dizi. "
                           "Ön kalça komutları kafa-bacak tablosuyla kırpılır (dizilerdeki 135-148° komutlar pan'a göre 114-128°'ye iner); kayıtlı kliplerde ön kalça zemin/gövde temasıyla zaten 60°'yi geçmiyor.")
ss["honest_failures"] = ("Kurtarma dizileri eski servo modeliyle ayarlanmıştı; tork-hız düşüşü ve kafa-bacak sınırı eklenince ilk deneme oranı düştü (çoğunlukla tork-hız düşüşü yüzünden; özellikle sırtüstü), "
                         "μ 0.6'da tüm düşüşler en çok 3-4 denemede kalktı, μ 0.4'te 30 yeni düşüşten biri kalkamadı. Diziler bu benzetimde ayarlandı; gerçek robotta yeniden ayar gerekir. "
                         "Konseptin tek dizisi bu modelde yan düşüşlerde başarısızdı (8/24, eski model); yan dizi bu yüzden yeniden ayarlandı.")
pc = J("playcheck.json", {})
if pc:
    lut = pc.get("_luts", {})
    worst_pc = min(((k, v["min_clearance_in_range_mm"]) for k, v in lut.items()), key=lambda x: x[1]) if lut else None
    hh = [v.get("head_vs_front_leg_min_gap_mm") for k, v in pc.items() if not k.startswith("_") and isinstance(v.get("head_vs_front_leg_min_gap_mm"), (int, float))]
    zmin = min(v["lowest_z_min_mm"] for k, v in pc.items() if not k.startswith("_")); zmax = max(v["lowest_z_max_mm"] for k, v in pc.items() if not k.startswith("_"))
    ss["playback_check"] = (f"rig.js ile aynı FK, {len([k for k in pc if not k.startswith('_')])} klibin hepsi tek koşuda: en alçak görünür nokta {zmin}…{zmax} mm (üst değer fall_recover_back'in 1. karesindeki 15 mm'den bırakma; diğer kliplerde ≤ 1.3 mm). "
                            f"Ebeveyn-çocuk çiftleri (gövde-kafa, gövde-kuyruk, gövde-uyluk, uyluk-kaval) gerçek modellerle açıya göre tarandı (MuJoCo bunları süzer); "
                            + (f"tüm eklem aralığında en dar yer {worst_pc[0]} {worst_pc[1]} mm (açıdan bağımsız sabit çalışma boşluğu; baskıda ~0.3 mm bırakılmalı). " if worst_pc else "")
                            + (f"Kafa-ön bacak (gerçek model) kliplerde en az {min(hh)} mm. " if hh else "") + "Ayrıntı: sim/out/playcheck.json.")
ss["notes"] = "Kaynaklar: sim/ (tarcin.py, gait.py, recover2.py, clips.py, hipsweep.py, sensitivity.py, playcheck.py, out/*.json)."
# ---------------- realism notes
rn = m["realism_notes_tr"]
rn = [x for x in rn if not x.startswith(("Siyah maske parlak", "Her kalçada", "Hareketler MuJoCo", "Yanak pencereleri", "Ekrandaki turuncu",
                                         "Kulaklar sert", "Kalkma benzetimi", "Ön bacak kafaya", "Kafanın arkasındaki"))]
rn += [
    "Siyah maske parlak görünüyorsa bu baskı değil, lazer kesim füme akriliktir. Burun siyah PLA'dır; parlaklığı 2 kat şeffaf vernikten gelir (kavisli yüzeyde ütüleme yapılamaz), katman çizgileri vernik altında hafifçe seçilir.",
    "Her kalçada iki servonun 6 telli yassı kablosu bacak modülünün iç yüzündeki yarıktan çıkar, 8-10 mm düz gider ve gövdedeki kalça ekseni etrafında kıvrılan 2 mm'lik yay yarıktan içeri girer; yarık alttan ve önden görünür. Kablo her kalça hareketinde yarık kenarında esner: sık düşüp kalkan bir robotta servo kabloları aşınan parçadır.",
    "Kulaklar sert turuncu PLA'dır, pimle oturur ve yapıştırılır; düşüşte çıkmaz (benzetim de böyle hesaplar), sert bir darbede kırılabilir.",
    "Kafanın arkasındaki 37 delikli ızgaranın arkasında 32 mm hoparlör vardır; sığması için kafa pan servosunun gövdesi öne bakar.",
    "Ekrandaki turuncu, gerçek Elas PLA Turuncu'dan daha açık ve kayısı tonlu görünür (ışıklı yüzlerde #ee9758-#f5a159): gerçek baskı daha koyu ve doygun turuncudur (makara rengi #e0692b'ye yakın). Gözler ise akrilik arkasında gerçekte olduğu gibi biraz soluk gri-turkuaz görünür.",
    "Yanak pencereleri arkasında WS2812B LED olan ince krem PLA'dır; LED kapalıyken krem görünür, mutlu olduğunda pembe yanar (stills/rig_face_happy_blush.png). Animasyonlarda yanak LED'i gösterilmez.",
    f"Ön bacak kafaya çarpmasın diye ön kalça en çok 128°'ye kalkar; kafa bu bacağa doğru dönükse sınır daha düşüktür (20°'de {T['20']}°, 40°'de {T['40']}°). Görüntüleyicideki 128° üst sınırı yalnızca kafa düzken çarpışmasızdır.",
    f"Hareketler MuJoCo fizik benzetimidir: yürüme yaklaşık {walk['speed_cm_s']} cm/s, dönüş {round(turn['yaw_rate_deg_s'])}°/s. Düşünce kalkma kuyruğun yere vurması ve bacak tekmeleriyle olur: yana düşünce çoğunlukla ilk denemede ({sf6}/{sn6}), sırtüstü düşünce çoğunlukla 2-3 denemede kalkar (ilk denemede yalnızca {bf6}/{bn6}); 'fall_recover_back' klibi bu zor durumu gösterir.",
    "Kalkma benzetimi pilin ve 5.5 V hatlarının çökmediğini varsayar. Stoktaki 14500 hücreler kalkma anındaki ~4.8 A tepeyi zor verir: pil zayıfladığında ya da BMS kestiğinde robot kalkamaz ve yeniden başlar; kafa pan servosu da düşüşlerde zorlanır ve dişlisi sıyırabilir.",
]
m["realism_notes_tr"] = rn
json.dump(m, open(M, "w"), indent=1, ensure_ascii=False)
print("ok", len(rn), "notes;", ss["recovery"][:200])
