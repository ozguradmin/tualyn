# Tosbi (A): neler basitleştirildi, neler belirsiz

Son güncelleme: 2026-10-25 (inceleme düzeltmeleri). Rakamlar `manifest.json`, `bom.json`, `sim/results.json` ve `src/fit_report.json` ile aynıdır.

## 1. Renkler ve baskı

- **Çok renkli baskı yok, AMS gerekmez.** Her renk ayrı bir parça:
  - mint kubbeler, yumurtalar, kollar ve ayaklar
  - krem kafa, sap ve kuyruk
  - mercan vizör halkası ve altıgen plakalar
  - siyah PLA: şasi bandı, ToF tünelleri ve çene yarığı
  - siyah PETG vizör
  - kırmızı TPU parmaklar

  İnce mercan bir şerit gibi ikinci renk istenirse ya ayrı parça ya da AMS'li yazıcı gerekir.
- **Vizör parlak değil, yarı parlak.** Kubbeli PETG vizör yüzü yukarı basılır. Eğri yüzey ütülenemez (ironing). Sonuç yarı parlak olur ve kontur halkaları görünür; görseller de böyle gösteriyor. Ayna gibi parlaklık için:
  - 400'den 2000'e kadar zımparayla ıslak zımpara
  - şeffaf vernik

  Bu işlem `bom.json` içinde `optional_visor_gloss` olarak duruyor: tahmini 200-400 TL, toplama dahil değil.
- **Kafa artık içi boş.** Kafa 1.6 mm et kalınlığıyla modellendi. Önceki GLB'de kafa dolu bir yumurtaydı.

## 2. İç yerleşim ve sığma (inceleme düzeltmesi)

- **Kartlar BOM'daki gerçek ölçüleriyle modellendi.** Yerleşimler (gövde orta düzlemine göre, mm):

  | Parça | Ölçü | Nerede |
  |---|---|---|
  | GY-521 | 21x16 | güverte |
  | 2S USB-C şarj | 39x18x6.3 | PCA9685'in üstündeki baskılı "üst kat" |
  | PAM8403 + pot | 24x21 + RV09 pot | üst katın altında baş aşağı; pot PCA9685'in yanından aşağı iner |
  | 2 x GY-53 | 25x15.6 | her kubbenin önünde |
  | KCD1 anahtar | - | sağ yan, kesik 19x13 |
  | Delikli pertinaks | 30x60 | güverte plakasının altında; 3 MP1584 altına asılı |
  | 2 x 1000 µF ve 470 µF | - | sol yan cep |

- **Çakışma kontrolü sıfır çıktı.** `src/fit_check.py` concept `check.py` ile aynı manifold3d boolean yöntemini kullanır. Taranan pozlar:
  - boyun −40…+40°, 5° adımla
  - her kalça min/0/max
  - diz −90…+90

  Sonuç 0 çakışma (`src/fit_report.json`). Tasarım gereği izin verilen temaslar:
  - kalça yumurtası kalça servosunun üstüne oturur
  - diz servosunun spline'ı ayağa geçer
  - sap baskılı yuvasına geçer
- **PAM8403 ölçüsü varsayım.** Pot'lu kartın ölçüsü satıcı sayfasında yok; 24x21 kart ve RV09 tipi pot varsayıldı. Gelen kart daha büyükse pot sökülüp sabit ses düzeyine geçilebilir.
- **Servo fişleri kubbeye sığmaz.** PCA9685'in düz pin header'larına takılan servo fişleri üst kubbeye çarpar (yaklaşık 16 mm yükseklik). Servo kabloları karta doğrudan lehimlenmeli ya da 90° header kullanılmalı. Modeldeki kablolar böyle çizildi.
- **Boyun kablosu servoya değmiyor.** 6 telli kablo artık boyun servosunun yanından (x −3…−8) ve arka duvar boyunca (R 18.6) SuperMini'ye gider. Servo ±40° boyunca R ≤ 17.9 tarar, yani kablo ona değmez. Kablonun sapın içindeki kısmı gövdeye bağlı. Esneyen geçiş bölümü basitleştirildi: model, sabit bir kafa kablosu ve sabit bir gövde kablosu olarak çizildi.

## 3. Masa kenarı sensörü (inceleme düzeltmesi)

- **Eski çene sensörü iki sorunluydu:**
  - Konseptteki çene ToF'u kafa eksenine göre 55° aşağı bakıyordu. B yüzünde (ters) bu, ufkun 35-55° üstüne bakmak demekti, yani masa kenarı görülemiyordu. Düşüşlerin çoğu B yüzünde bitiyor.
  - GY-53 kartı (25x15.6) çeneye hiç sığmıyordu. Yaklaşık 400 yerleşim denendi; en iyisi bile kafa kabuğuna 58 mm³ giriyordu.
- **Yeni çözüm: kubbe başına bir ToF.** İki GY-53 kullanılıyor, her kubbenin önünde bir pencere var: biri boynun altında, biri üstünde. İki kubbe hâlâ aynı STL. Hangi yüz alttaysa onun sensörü masaya 50° aşağı bakar, firmware de onu okur. A ve B yüzünde de kenar algısı var.
- **Kafa görüşü kapatmıyor.** Sensör ekseni ve 12.5°'lik görüş konisi, boynun −40…+40° aralığının tamamında kafaya çarpmıyor.
- **Kalan sınırlar:**
  - Sensör yalnızca orta şeridi görür. Eksen zemine gövde merkezinin 61 mm önünde değer; bu, ön ayak hattının yaklaşık 13 mm önü. 5 cm/s hızda bu yaklaşık 0.25 s uyarı demek.
  - Çapraz gelen bir kenar önce bir ayağı boşluğa düşürebilir.
  - ToF kenar algısı simülasyonda modellenmedi.
- **İki GY-53 aynı I2C adresini kullanır.** I2C modunda iki STM32 aynı adreste cevap verir. Ya biri UART/PWM çıkışından okunmalı ya da her yüz için besleme ayrı açılıp kapanmalı. SuperMini'de yalnızca 11 serbest GPIO var; bu bütçenin yetip yetmediği doğrulanmadı.
- **Çene yarığı artık kozmetik.** Siyah bir "ağız" olarak duruyor.
- **Ucuz varyantta kenar algısı yok.** Ucuz varyant iki ToF'u da çıkarıyor, yani iki yüzde de masa kenarını göremez.

## 4. Güç

- **Hücreler istenen akımı vermiyor.** Türkiye stoğunda bulunabilen Orion 14500 hücreler 3C, yani yaklaşık 2.7 A. Konsept ≥4 A istiyordu ve bu karşılanmıyor.
- **Takla anında gerilim çökebilir.** Her MP1584 4-5 servoyu besliyor. Takla sırasında dört diz servosu aynı anda sınıra dayanır: diz servoları zamanın %5.8'inde 0.20 N·m'de kalıyor. Bu, gerilim çökmesine ve ESP32'nin resetlenmesine yol açabilir.
- **Simülasyon ideal hat varsayıyor.** Sabit, ideal bir 5.5 V servo hattı kabul ediliyor; pil çökmesi yok. Firmware servo hareketlerini kademelendirmeli; 1000 µF kondansatörler bu yüzden var.

## 5. Mekanik riskler

- **Omuz cıvatası yerine M2x15 vida.** Türkiye stoğunda M2 omuz cıvatası bulunamadı. Kalça ve diz yatak pimi olarak M2x15 vida kullanılıyor. Dişli gövde PLA yatakta zamanla aşınır ve boşluk yapar. 3 mm dış çaplı pirinç boru kovan ya da 2 mm çelik pim bunu düzeltir; bunlar fiyatlanmadı.
- **Anahtar kesiği iki kubbeye bölünüyor.** KCD1'in kesiği yarı yarıya iki kubbede; anahtar iki kubbenin arasında sıkışarak tutulur. Kubbelerin yan duvarı ±10 mm'de 1.4 mm içeri kıvrıldığı için çerçeve kenarında küçük bir aralık görünür.

## 6. Ağırlık ve fiyat

- **Ağırlık hedefi aşılıyor.** Kütle 403 g (gövde 221, kafa 39, bacaklar 4 x 35.8). Konsept 380 g diyordu; BOM'daki gerçek parçalar yaklaşık 25 g ekledi. Rehberdeki ≤350 g hedefi aşılıyor. Simülasyon 403 g ile yeniden koşuldu.
- **Fiyat hedefi aşılıyor.** Tam yapı 6,048-7,048 TL (alet hariç). Ucuz varyant 4,853-5,683 TL. İkisi de 5,000 TL hedefinin üstünde ya da sınırında. Hesap tabanı `bom.json` içinde (`total_basis`) yazılı. Yerel kalemlerin aralığı 280-550 TL olarak düzeltildi; önceki dosyada üst sınır 500 yazıyordu.

## 7. Simülasyondaki idealleştirmeler (MuJoCo)

- **Basitleştirilmiş fizik:**
  - Çarpışma geometrisi, her parçanın dışbükey kabuğu; gerçekten biraz dolgun.
  - Servo boşluğu ve ölü bölge yok.
  - Plastik esnemesi yok.
  - Kablo direnci yok.
  - Servo hattı ideal.

  Bu yüzden hız ve dönüş değerleri **üst sınır** olarak okunmalı:

  | Hareket | μ 0.6 | μ 0.4 |
  |---|---|---|
  | Yürüme | 5.08 cm/s | 5.13 cm/s |
  | Dönüş | 33.9°/s | - |
- **IMU gerçek ivmeölçer gibi modellendi.** Simüle edilen ivmeölçer okunuyor (GY-521'in güvertedeki konumunda) ve 0.08 m/s² gürültü ekleniyor; ideal yönelim kullanılmıyor. Firmware modeli (`sim/recover.py`) iki kural uyguluyor:
  - |a| 1 g'den ±2.5 m/s²'den fazla saptığında (itme, çarpma, serbest düşüş) eğimi güncellemez.
  - Bir yüzden çıkış 0.2 s sürmeden tekme başlatmaz.
- **Kendi kendine kalkma sonuçları:**
  - μ 0.6'da 78/78, μ 0.4'te 78/78. Zayıf servoyla (4.8 V) 30/30.
  - Kalkma süresi tek bir tabanla ölçüldü: firmware tepkisinden en az 1 s sürekli ayakta durmanın başlangıcına kadar. Tüm gruplarda medyan 0.5 s, en uzun 1.6 s; en uzunu itme durumlarında.
- **Darbede eklem sınırı aşılabiliyor.** Darbe, yumuşak MJCF eklem sınırlarını geri itebiliyordu. Sınırlar sertleştirildi (solreflimit 2 ms). Kalan en büyük taşma 0.18°; klip bu değeri sınıra kırpıyor. Gerçekte servo mekanik durdurucusuna dayanır.
- **`fall_recover` klibini okuma notları:**
  - Kabuğu kaldıran el görünmüyor. Klipte olay listesi (`events`) ve bir açıklama (`caption_tr`) var; manifest'te de `animation_captions_tr` olarak duruyor.
  - Robot düşerken yaklaşık 21 cm kayıyor ve yaklaşık 177° dönüyor. B yüzünde kalktıktan sonra yalnızca 1.2 s yürüyüp duruyor.
- **Henüz ölçülmeyen ya da yeniden koşulmayan değerler:**
  - `min_servo_torque_for_recovery_Nm` ve `tip_over_threshold` 380 g'lık önceki modelden; yeniden koşulmadı.
  - `idle`, `talk`, `happy` ve `sleep` için servo hedefleri elle yazıldı, ama fizik içinde oynatıldı.

## 8. Test edilmeyenler

- masadan gerçekten düşme
- ToF ile kenar algısı (sensör simüle edilmedi)
- halı ya da yumuşak zemin
- bir engelin dibinde sıkışma
- düşerken çarpma hasarı
- pil gerilim çökmesi
- servo ısınması

## 9. Görseller

- **`stills/action_wave.png`** `happy` klibinden, t=1.4 s anı. Robot bu pozu gerçekten tutabiliyor; ağırlık üç ayağa kaydırılmış durumda.
- **Eklem sınırı testleri.** `stills/lim_*.png` görselleri yalnızca eklem testi; robot bu pozlarda dengede duramaz (manifest `stills_notes_tr`).
- **Yeni yakın çekimler:**
  - `stills/macro_switch.png`: sağ yandaki KCD1 anahtarı
  - `stills/macro_tof.png`: kubbelerdeki ToF pencereleri; kafanın arkasında kaldıkları için görmesi zor
