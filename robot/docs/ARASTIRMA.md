# Araştırma notları (24 Ekim 2026)

Bu notlar, Kıpır'ın tasarım kararlarının dayandığı araştırmanın özetidir. Fiyatlar 23-24 Ekim
2026'da mağaza sayfalarından okundu; kur: **1 USD ≈ 49,65 TL, 1 EUR ≈ 55,60 TL**
(TCMB 23.10.2026 bülteni). Fiyatlar hızla değişiyor; sipariş öncesi tekrar bak.

## 1. "PhoneBot" nedir?

Ekim 2026'da gündemdeki **PhoneBot**, UCLA RoMeLa laboratuvarının (Dennis Hong ekibi)
telefonla çalışan insansı robotu:

- 48,3 cm, 1,8 kg, 13 serbestlik derecesi (her bacakta 6 + bel). Telefon kamera, IMU,
  yürüme politikası (TFLite), insan takibi ve ARCore haritalama işini yapar; eklem hedeflerini
  Wi-Fi/UDP ile küçük bir karta (Radxa ZERO 3W) gönderir, o da 13 Dynamixel XL430 servoyu sürer.
- Makaleye göre telefon hariç ~400 USD; yayımlanan malzeme listesinin toplamı ~443 USD.
  Test telefonları 50-90 USD'lik moto g 2024/2025, Galaxy A16 5G.
- **"Tamamen açık kaynak" haberleri şimdilik abartılı**: phonebot.dev'de CAD, baskı
  parçaları ve montaj rehberi düğmeleri görünüyor ama sitenin kendi yapılandırmasında bu
  bağlantılar boş (24 Ekim). İndirilebilen yalnızca malzeme listesi (.xlsx) ve STEP montaj
  dosyası; lisans CC BY-NC 4.0 (ticari değil). Telefon uygulaması ve firmware kodu için
  bir depo bulunamadı.
- Türkiye'de kopyalamak pahalı: XL430 servo Robot Sepeti'nde ~2.950 TL (stokta yok),
  13 adedi ~38.000 TL.

Kaynaklar: [arXiv 2610.08737](https://arxiv.org/abs/2610.08737) ·
[phonebot.dev](https://phonebot.dev) ·
[PhoneBot web sitesi deposu](https://github.com/hruochenUCLA2021/PhoneBot-website) ·
[Robot Sepeti XL430](https://www.robotsepeti.com/dynamixel-xl430-w250-t)

**Bizim için çıkan ders:** fikir harika (telefon = beyin + göz + kulak, ucuz kart = kas), ama
ilk robot için yürüyen insansı değil, **tekerlekli** bir gövde mantıklı. Kıpır bu fikri
TT motorlu bir gövdeye uyguluyor.

### Akrabaları

- **OpenBot** (Intel'den çıktı, şimdi [github.com/ob-f/OpenBot](https://github.com/ob-f/OpenBot), MIT):
  telefonla sürülen 4 TT motorlu araba, gövdesi ~50 USD. Android uygulaması artık
  Android 7.0+ istiyor (build.gradle minSdk 24); ESP32 firmware'i Arduino ESP32 çekirdeği
  2.0.17 ile derleniyor ve telefona sadece BLE ile bağlanıyor (klasik Bluetooth yok).
  Kişi takibi, otopilot ve ARCore ile hedefe gitme özellikleri var.
- **LOOI**: telefonunu yüz ve beyin olarak takan ticari masaüstü robot, ~179-220 USD;
  iPhone 12+ ya da Android 12+ istiyor. Kıpır'ın "telefon kafa" fikrine en yakın ürün.
- **BotParty** (Pixel 1 + ESP32 + Web Bluetooth + WebRTC, ~120 USD parça): telefon beyinli
  ucuz robot için iyi bir örnek. ([proje](https://dheera.net/projects/botparty/))

## 2. Hugging Face robotiği (LeRobot)

- **LeRobot** son sürüm v0.6.1 (Ağustos 2026), Python ≥3.12. İş akışı: uzaktan kumanda et →
  kaydet → eğit → çalıştır. ([belgeler](https://huggingface.co/docs/lerobot/index))
- **SO-101 kol** (Apache-2.0): resmi malzeme listesi lider+takipçi çift için **229,88 USD**
  (12 × Feetech STS3215 servo ~13,89 USD). Baskı ~665 g PLA, 16-24 saat.
  ([SO-ARM100 deposu](https://github.com/TheRobotStudio/SO-ARM100))
  - Hazır kitler: WowRobo 199 USD'den (stok belirsiz), Hiwonder DIY 256,99 USD,
    Seeed motor kiti 277,99 USD (baskısız). Seeed'in 315,99 USD'lik "assembled" ürünü
    **tek kol**, çift değil.
  - Türkiye'de STS3215 eşdeğeri SAMM'de ~1.594 TL (stokta yok); yurt dışının ~2,3 katı.
    İzmir'de Hashtag Robotics montajlı 12V SO-101 çifti için ön sipariş topluyor (fiyat yok).
- **LeKiwi**: 3 omni tekerli taban + SO-101 + Raspberry Pi 5. Kollar dahil malzeme
  ~482-499 USD; 5V sürümü 65-85 W'lık USB-C powerbank ile çalışıyor.
- **Reachy Mini**: Lite 399 USD / Wireless 499 USD (Seeed). Pollen'ın mağazası
  **Türkiye'ye göndermiyor**; Seeed ya da aracı ile alınır, gümrük ayrıca.
- **Microduck** (Ağustos 2026, 399 USD): donanımı kapalı, yeni siparişlerde 4-6 ay bekleme,
  Türkiye satış bölgesinde değil.
- **Modeller ve gereken GPU** (LeRobot donanım rehberi):
  - **ACT** (~80M parametre): 2-6 GB VRAM yeter (dizüstü RTX 3060). İlk denenecek model.
    50 bölüm veri ile RTX 4090'da 30-60 dk, bulutta L4 ile ~1-2 saat (~0,80 USD/saat).
  - **SmolVLA** (450M): ince ayar için 10-16 GB, en az 50 bölüm (25 yetmiyor). Çıkarım
    dizüstü GPU'da, hatta CPU'da çalışabilecek kadar küçük.
  - **pi0 / pi0.5, GR00T N1.7, X-VLA**: ince ayar için 24-40 GB+ (A100 kiralamak gerekir,
    HF Jobs'ta ~2,50 USD/saat).
- **Önemli değişiklik:** Türkiye, Şubat 2026'da 30 € altı posta/kargo muafiyetini kaldırdı.
  Artık her yurt dışı paketine vergi ödeniyor; kargo ücreti de gümrük değerine ekleniyor.
  0-1.500 € arası kişisel gönderilerde kurye ayrıntılı beyan yapıyor ve müşavirlik/ardiye
  ücreti de isteyebiliyor; oyuncak sayılan kitler basitleştirilmiş beyana giremiyor.
  ([Ticaret Bakanlığı SSS](https://ticaret.gov.tr/gumruk-islemleri/sikca-sorulan-sorular/bireysel/posta-ve-hizli-kargo-muafiyeti))

## 3. "RTX Spark" ve "DGX Spark": ikisi farklı şeyler

- **NVIDIA RTX Spark** gerçek bir 2026 ürünü: 31 Mayıs 2026'da Computex'te duyurulan,
  **Windows-on-Arm dizüstü/kompakt masaüstü** platformu (N1X çipi: 20 çekirdek Grace CPU +
  6.144 CUDA çekirdekli Blackwell GPU, 128 GB'a kadar birleşik bellek). Dizüstüler
  16 Ekim 2026'da 2.599 USD'den satışa çıktı (Surface Laptop Ultra, ASUS ProArt, Dell XPS 16…).
  Türkiye'de ~210.000-424.000 TL. Windows-on-Arm için PyTorch/CUDA henüz yeni (önizleme).
  ([NVIDIA duyurusu](https://nvidianews.nvidia.com/news/nvidia-rtx-spark-pcs-available-today-a-new-beginning-for-windows-pcs))
- **DGX Spark**: aynı silikon ailesinin (GB10) Linux'lu kutu hâli, 128 GB. Ekim 2025'te
  3.999 USD'ydi, bellek fiyatları yüzünden şimdi ~6.950 USD; Türkiye'de ~322.000-500.000 TL.
- **Hobi robotu için ikisi de gerekmiyor.** DGX Spark, ham eğitim hızında bir RTX 4090'dan
  3-4 kat yavaş (topluluk ölçümü), tek avantajı 128 GB bellek. Bulutta bir SmolVLA ince ayarı
  ~5-10 USD; DGX Spark kendini yüzlerce ince ayardan sonra öder.
- Temmuz 2026 bellek fiyat şoku: Jetson Orin Nano Super 249 → **399 USD**
  (Türkiye'de 24 Ekim itibarıyla ~30.400-43.700 TL, çoğu yerde stokta yok),
  Raspberry Pi 5 4GB ~110 USD (Türkiye'de ~7.000 TL liste fiyatı, bakılan mağazaların
  hiçbirinde stokta yok).

**Önerilen işlem gücü:** robotun üstünde ESP32 + telefon; yapay zekâ için bulut API'si;
LeRobot eğitimi için varsa NVIDIA'lı dizüstü (6 GB+), yoksa saatlik kiralık GPU.

## 4. Elindeki cihazlar: ne işe yarar?

### Samsung Galaxy Tab 3 Lite SM-T110
193,4 × 116,4 × 9,7 mm, 310 g; 7" 1024×600 ekran; Android 4.2.2; 1 GB RAM.
- **Ön kamerası yok**, sadece 2 MP arka kamera var. Ekran öne bakınca kamera arkaya bakar.
- Android 4.2'de uygulamalar BLE kullanamıyor (4.3'te geldi); USB OTG kullanıcı
  raporlarına göre çalışmıyor; güncel Chrome yok (son sürüm Chrome 71); hazır tarayıcıda
  **WebSocket yok**; Let's Encrypt kök sertifikası güvenilir değil, yani modern HTTPS
  siteleri ve bulut API'leri doğrudan çalışmaz.
- **En iyi kullanım: robotun yüzü ya da dokunmatik kumandası.** Kıpır'ın yüz sayfası bu yüzden
  ESP32'den düz HTTP ile geliyor, WebSocket yerine 150 ms'de bir sorgu (XHR) yapıyor ve ES5
  ile yazıldı. İstersen Firefox 68.11 APK'sı (Android 4.1+ destekli son Fennec) daha
  rahat çalışır.
- Pili 10+ yaşında: robota takmadan önce **şişme var mı kontrol et**. Eski Samsung
  tabletler bazı powerbank'lerden yavaş şarj olur; bağlıyken bile pil azalıyorsa farklı bir
  çıkış ya da kablo dene.

### Powerbank
- ESP32 ve tablet için ideal. Ama iki TT motor sıkışınca 1,1-1,5 A'er çekiyor (toplam
  2,2-3 A) → powerbank kesebilir, ESP32 resetlenir. Ayrıca çoğu powerbank ~100-150 mA'nın
  altında kendini kapatır (Wi-Fi açık ESP32 genelde yeterli akım çeker).
- **Karar:** powerbank → ESP32 + tablet; motorlar → ayrı 2×18650 pil. İlk denemede tek
  powerbank da olur (firmware'de yumuşak kalkış var), resetlenirse pili ayır.

### Corby drone
- Corby, TT Teknoloji'nin (İstanbul) Çin'den getirdiği oyuncak dronların markası. CX017'de
  1800 mAh 3,7 V LiPo (USB şarj kablolu), fırçalı coreless motorlar ve ayrı bir Wi-Fi kamera
  modülü var. CX018'in pili 2S (7,4 V), CX019/CX037 fırçasız.
- Coreless motorlar 40-50 bin devir ve neredeyse torksuz: **teker için işe yaramaz**,
  fan ya da titreşim için olur.
- **Modelin CX018 (Anka) ise:** pili kendi micro-USB şarj girişi olan hazır bir
  **2S 7,4 V 1300 mAh** paket. Kıpır'ın motor pili olarak doğrudan kullanılabilir
  (`MOTOR_VOLT 7.4`), 2×18650 almana gerek kalmaz.
- Kamera modülü: bazı uygulama aileleri `rtsp://192.168.1.1:7070/webcam` adresinden
  yayın veriyor. Bilgisayarı dronun Wi-Fi'ına bağlayıp VLC ile bu adresi dene; çalışırsa
  robotun ikinci gözü olabilir. Benzer dronlarda kamera 3,3 V ile çalışıyor; sökersen
  3,7-4,2 V'luk pili doğrudan bağlama, önce multimetreyle ölç.
- LiPo: koruma devresi yoksa bir TP4056 Type-C (korumalı) modülüyle kullan. Şişmiş pili
  asla kullanma.

### Gamebox ve kolu
- Türkiye'de "Gamebox" çoğunlukla **400 oyunlu SUP el konsolu**. Kablolu 2. oyuncu kolu
  NES tipi bir kaydırma yazmacı (4021): LATCH, CLOCK, DATA, VCC, GND. ESP32 bunu 3 pinle
  okuyabilir. **Kıpır firmware'i bunu destekliyor** (`USE_NES_PAD 1`); kablodaki 5 teli
  multimetreyle bulman gerekiyor.
- HDMI'lı "4K Game Stick" ise: GD10/X2 Plus (Amlogic S905X/W) modelleri microSD'den
  Armbian açabiliyor (bedava Linux bilgisayar). M8 modeli kapalı bir sistem. 2,4 GHz
  kolların USB alıcısı bilgisayarda standart gamepad olarak görünüyorsa, telefon beyni
  sayfası (Gamepad API) ve LeRobot onu kullanabilir.

### Kumandalı RGB gece lambası
- **Önce kumandanın IR mi RF mi olduğunu anla:** telefonun kamerasını açıp kumandanın
  ucuna bak ve bir tuşa bas. Ekranda mor/beyaz bir ışık yanıp sönüyorsa IR'dır. Işık yoksa ve
  lambaya bakmadan da çalışıyorsa RF (433 MHz) olabilir; o zaman VS1838B onu okuyamaz,
  bir 433 MHz alıcı (RXB6 / SRX882) gerekir.
- IR kumandalar neredeyse her zaman 38 kHz NEC protokolü kullanır. ~7-10 TL'lik bir
  VS1838B alıcıyla ESP32 kodları okur. **Kıpır firmware'inde kütüphanesiz bir NEC çözücü ve
  "tuş öğretme" ekranı var**: ileri/geri/sol/sağ/dur/selam/dans/uyku tuşlarını kendi
  kumandana öğretirsin.
- Lambanın LED'leri: 4 bacaklı düz RGB ise 3 PWM + transistör; WS2812 ise doğrudan
  kullanılabilir. Gövde ışığı olur.

## 5. Yapay zekâ seçenekleri

- **Claude (telefon beyin sayfası):** Kıpır'ın `beyin.html` sayfası telefonun ön kamerasından
  kare alıp Claude'a araçlarla (hareket et, yüz ifadesi, bak, ses, dans) gönderiyor.
  Varsayılan model Claude Opus 5.5 (4 / 20 USD / milyon token); ayarlardan Sonnet 5.5
  (2 / 10) ya da Haiku 5.5 (0,10 / 0,50) seçilebilir. Kabaca bir keşif adımı Opus ile birkaç
  sent, Haiku ile 0,1 sentin altında. Anahtar sadece telefonda durur.
- **Gemini Live**: gerçek zamanlı sesli + görüntülü konuşma (WSS), Türkçe destekli; telefon
  sayfasıyla birleştirilebilir.
- **xiaozhi-esp32** (MIT): ESP32-S3 + mikrofon + hoparlörle telefonsuz sesli asistan.
  tr-TR arayüzü var, cihaz tarafında MCP araçlarıyla motorları sürebilir. Kıpır v2 için
  "telefonsuz kafa" seçeneği.
- **Cihaz üstünde AI**: Gemini Nano yalnızca yeni amiral gemisi telefonlarda. Tab 3 Lite'ta
  hiçbir modern model çalışmaz.

## 6. Ticari robotlarla kıyas (fikir vermesi için)

| Robot | Fiyat | Not |
|---|---|---|
| LOOI | ~179-220 USD | Telefonunu yüz yapar |
| Anki/DDL Vector 2.0 | 249,99 USD + 11,99 USD/ay | Abonelik ister |
| EMO | 279 USD | |
| Loona | 429 USD+ | |
| Reachy Mini Lite / Wireless | 399 / 499 USD | Türkiye'ye Seeed üzerinden, gümrük ayrı |
| Petoi Bittle X | 319-469 USD | ESP32'li robot köpek |
| **Kıpır v1** | **~2.600-3.900 TL** (≈52-79 USD) | baskı dahil; bkz. [MALZEME.md](MALZEME.md) |

## 7. Kararlar

1. **Gövde:** 2 TT motor + misket teker, yuvarlak 2 katlı şase (OpenBot/LOOI yaklaşımı).
2. **Beyin:** ESP32-WROOM-32 (klasik; hem Wi-Fi hem BLE, eski tabletle de konuşabilsin).
   Güvenlik (engelde durma, komut zaman aşımı) her zaman ESP32'de; telefon sadece öneri verir.
3. **Yüz:** telefon (kamera + AI ile) ya da Tab 3 Lite (sadece yüz). Kafa rayı ikisine de
   uyar (cihaz boyu 140-200 mm).
4. **Kumanda:** gece lambası kumandası (IR), Gamebox kolu (NES), telefon/tablet web sayfası,
   USB/Bluetooth gamepad (telefon sayfası üzerinden).
5. **Sonraki adım:** SO-101 kol + LeRobot ile taklit öğrenmesi (ACT → SmolVLA). Pahalı
   Spark kutularına gerek yok.
