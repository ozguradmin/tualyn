# Tarçın v2: durum ve kararlar

25 Ekim 2026. Bu dosya, mola verilen yerden devam edebilmek için yazıldı.

## Verilen kararlar

- **Robot: Tarçın** (kırmızı panda).
  - Yumurcak'ın görünüşü beğenilmedi.
  - Fındık tekerlekli olduğu için klavye üstünde gidemiyor.
  - Sesame ve StackChan karşılaştırması: [../docs/SESAME_STACKCHAN.md](../docs/SESAME_STACKCHAN.md).
- **Lehimi aile kendisi yapacak.** Tamamen lehimsiz yapmak çok pahalı: yalnızca parçalar ~8.650 TL tutuyordu, normal Tarçın'da ~5.160 TL.
  - En büyük fark lehimsiz göz ekranlarından geliyor: tanesi 874-1.515 TL, normali 351 TL.
  - Türkiye'deki ucuz modüllerin çoğu pinleri lehimsiz geliyor; mağazaların hiçbiri lehim hizmeti vermiyor.
- **Pil: hazır RC tipi 2S LiPo.** Pil kaynağı yaptırmak mümkün değil, LiPo bunu ortadan kaldırıyor.

  | Parça | Mağaza | Fiyat |
  |---|---|---|
  | Tinylab 7,4 V 2S 850 mAh 40C LiPo (59×31×17 mm, 52 g) | [Robotistan](https://www.robotistan.com/tinylab-74v-2s-lipo-batarya-850mah-40c) | 847,30 TL |
  | iMAX B3 PRO denge şarj aleti (pil robottan çıkarılıp şarj edilir) | [Robot Sepeti](https://www.robotsepeti.com/imax-b3-pro-2-3s-lipo-pil-balansli-sarj-cihazi) | 731,84 TL |
  | LiPo seviye alarmı | [Motorobit](https://www.motorobit.com/lipo-seviye-olcer-ve-alarm-modulu) | 115,14 TL |
  | Pil fişinin karşılığı (kablolu) | [Robotistan](https://www.robotistan.com/jst-lipo-batarya-disi-konektoru-15cm-22awg) | 16,93 TL |

  Eski pil bölümüne göre yaklaşık +1.150 TL. Kazancı: kaynak gerekmiyor ve pil, düşüp kalkarken çekilen ~4,8 A'lik tepeyi rahat karşılıyor.
  Pilin fiş tipi ve 3 A'lik JST'nin yetip yetmediği, elektronik tasarımında kesinleşecek.
- **Elektronik: tek ESP32-S3 kartı.** İki kart yerine tek kart var; 10 servo, takılarak bağlanan bir PCA9685 sürücü kartına gidiyor ([Robotistan, 245,54 TL](https://www.robotistan.com/pca9685-16-kanal-i2c-pwmservo-surucu-karti-klon), pinleri lehimli).
- **Bacaklar: klavye için daha geniş duruş ve kızak gibi pençe.** Genişlik henüz seçilmedi (aşağıya bakın).

## Klavye testi (MuJoCo simülasyonu)

| | Dizüstü klavyesi | Mekanik klavye, çapraz | Mekanik klavye, tuş sırası boyunca | Düz masa |
|---|---|---|---|---|
| Tarçın, şimdiki hâli | 72/72, 7-9 cm/s | 14/36 | 0/36 | 20/20, 7,2-7,7 cm/s |
| Tarçın, taraf başına +25 mm geniş duruş, kızak pençe ve 8 mm adım | 72/72 | 30/36 | 2/36 | 20/20, 5,5 cm/s |
| Sesame, ayarlanmış yürüyüş | 58/60 | 28/30 aşağı, 11/30 yukarı | 0/30 | 30/30 |

- **Dizüstü klavyesi:** Tarçın üstünde rahat yürüyor; 8 denemenin 5'inde masadan üstüne de çıkıyor.
- **Büyük mekanik klavye:** eğik ve kaygan olduğu için tuş sırası boyunca yürüyemiyor; masadan üstüne de çıkamıyor.
- **+25 mm geniş duruş:** görünüşü çok değiştirebilir. Daha küçük genişliklerin (8-20 mm) denenmesi bir sonraki adım.
- **Ayrıntılar:**
  - sonuçlar: [girdi/sim_tarcin-keyboard.json](girdi/sim_tarcin-keyboard.json), [girdi/sim_sesame-keyboard.json](girdi/sim_sesame-keyboard.json)
  - betikler ve ham çıktılar: [klavye_calismasi/](klavye_calismasi/)

## Lehim alet seti (~1.000 TL, fiyatlar 24 Ekim'de mağaza sayfalarından alındı)

| Alet | Mağaza | Fiyat |
|---|---|---|
| Isı ayarlı 60 W kalem havya | Motorobit | 242,40 TL |
| DT-830D multimetre | Motorobit | 212,10 TL |
| Havya standı (ZD-10A) | Robotistan | 155,85 TL |
| Yan keski (Plato 170) | Motorobit | 151,50 TL |
| Lehim teli 60/40, 1 mm | Robotistan | 142,73 TL |
| Krem flux (RMA-223) | Motorobit | 48,48 TL |
| Lehim sökme teli | Motorobit | 54,54 TL |
| Alıştırma için pertinaks + pin dizisi | Robotistan | ~52 TL |

Lehimsiz parça araştırmasının tamamı (Türk mağazaları, bağlantılar, pinleri lehimli mi değil mi):
[girdi/research_solder-free-parts.json](girdi/research_solder-free-parts.json).

## Sıradaki adımlar

1. **Elektronik ve güç tasarımı:**
   - kart seçimi ve yeri, PCA9685 kanal haritası;
   - servo güç hatları (düşüp kalkarken 4,8-5,8 A tepe);
   - pil azalınca kapanma için voltaj bölücü, pin haritası;
   - lehim noktalarının listesi ve Türkçe bağlantı şeması.
2. **Bacak genişliği ve pençe seçimi:** 0/8/12/16/20/25 mm denenir. Klavye, düz masa ve düşüp kalkma testleri ile görünüş birlikte değerlendirilir.
3. **Baskıya hazır parçalar:**
   - gövde renk başına ayrı parçalara bölünür; vida yuvaları ve servo yuvaları eklenir;
   - aletsiz açılan bir pil kapağı, USB erişimi ve kablo kanalları olur;
   - STL ve 3MF dosyaları çıkarılır, parçalar PrusaSlicer'da dilimlenip gram ve saat hesaplanır.
4. **Yeni ağırlıklarla simülasyon doğrulaması:** yürüme, klavye, düşüp kalkma ve akım tepeleri. Ardından 3B sayfa için Tarçın v2 modeli.
5. **Mağaza mağaza sepet listesi:** fiyatlar o gün yeniden kontrol edilir; ücretsiz kargo sınırları gözetilir.
6. **Türkçe kurulum kılavuzu:** güvenlik, sıfırdan lehim dersi, adım adım montaj, ilk çalıştırma, sorun giderme ve baskı stüdyosuna gidecek hazır mesaj.
7. **Bağımsız incelemeler ve düzeltmeler:** biri donanım uzmanı gözüyle, biri hiç lehim yapmamış biri gözüyle.

## Devam etmek için

- Bu adımların hepsini sırayla yapan iş akışı betiği: [is_akisi.js](is_akisi.js) (Claude Code Workflow).
  - İçindeki yollar eski oturumun geçici klasörünü gösteriyor; yeni oturumda depodaki karşılıklarıyla değiştirilmeli.
  - Tarçın paketi `robot/yeni_nesil/b_tarcin/` (bom.json, manifest.json, NOTES.md, `cad/model.py`, `sim/`).
  - Girdiler `robot/tarcin_v2/girdi/`, klavye çalışması `robot/tarcin_v2/klavye_calismasi/`.
- Tarçın'ın baskı modeli (`model.glb`) depoda ayrı dosya olarak yok. 3B sunumun içinde gömülü (`robot/sunum/index.html`); ayrıca `cad/model.py` ile yeniden üretilebilir.
