# Kıpır v1: malzeme listesi ve maliyet

Fiyatlar **KDV dahil**, 24 Ekim 2026'da mağaza sayfalarından okundu. (Direnc.net ve
Motorobit sayfalarında önce KDV hariç fiyat yazar, dikkat.) "~" ile başlayanlar tahmindir;
bu kalemlerin fiyatına bakamadık. Stok durumları hızla değişir; en ucuz seçeneği ve bir
alternatifi yazdım.

## A. Elektronik ve mekanik (zorunlu)

| # | Parça | Adet | Fiyat (TL) | Nereden |
|---|---|---:|---:|---|
| 1 | ESP32 DevKit V1 (**WROOM-32**, 30 pin). S3/C3 alma: eski tabletle klasik Bluetooth isteyebilirsin | 1 | 377,76 | [Direnc.net](https://www.direnc.net/esp32-wroom-32d-wifi-bluetooth-gelistirme-board) · [Robotistan 422,75](https://www.robotistan.com/esp32-esp-32s-wifi-bluetooth-dual-mode-gelistirme-karti) |
| 2 | TB6612FNG motor sürücü | 1 | 81,36 | [Direnc.net](https://www.direnc.net/tb6612fng-dc-ve-step-motor-surucu-modulu) · [Robolink 117,00](https://www.robolinkmarket.com/motor-surucu-1a-cift-dc-tb6612fng) · [Robotistan 122,17](https://www.robotistan.com/tb6612fng-step-motor-surucu-dc-motor-sucuru) |
| 3 | TT sarı motor 6V 250 rpm + 65 mm teker seti | 2 | 145,30 | [Direnc.net 72,65/adet](https://www.direnc.net/6v-250-rpm-motor-ve-tekerlek-seti-1) · [Robotistan 96,77/adet](https://www.robotistan.com/6v-250-rpm-motor-ve-tekerlek-seti) |
| 4 | HC-SR04 ultrasonik mesafe sensörü | 1 | 63,50 | [Robotistan](https://www.robotistan.com/hc-sr04-ultrasonik-mesafe-sensoru) (stoğu sepette kontrol et) |
| 5 | VS1838B 38 kHz IR alıcı | 1 | 7,14 | [Robo90](https://www.robo90.com/38khz-ir-kizilotesi-alici-sensoru-vs1838b) |
| 6 | 2'li 18650 pil yuvası (kapaklı, anahtarlı) | 1 | 38,46 | [Robotistan](https://www.robotistan.com/2li-18650-kapakli-anahtarli-jakli-pil-yuvasi) |
| 7 | 18650 Li-ion pil 2600 mAh | 2 | 297,28 | [Direnc.net 148,64/adet](https://www.direnc.net/orion-18650-37v-2600mah-5c-li-ion-pil) |
| 8 | TP4056 Type-C korumalı şarj modülü + 1'li 18650 pil yuvası (pilleri tek tek şarj etmek için; evde 18650 şarj aleti varsa ikisi de gerekmez) | 1+1 | ~30 | [Robotronik 14,40](https://www.robotronik.com.tr/tp4056-type-c-37v-18650-korumali-lityum-pil-sarj-modulu-a0005) + yuva ~15 |
| 9 | Jumper kablo: dişi-dişi + erkek-dişi + erkek-erkek (40'lı, 20 cm) | 3 | ~150 | [Direnc.net dişi-dişi 49,40](https://www.direnc.net/40-adet-disi-disi-jumper-kablo-20cm); diğerleri benzer fiyatta |
| 10 | Breadboard (830) ya da küçük delikli pertinaks | 1 | 55,21 | [Direnc.net](https://www.direnc.net/tekli-breadboard) |
| 11 | Pasif buzzer | 1 | ~20 | herhangi bir elektronik mağazası |
| 12 | Kondansatör 1000 µF 16V + 100 µF + direnç (1k, 2k, 100Ω) + 1N4148 diyot | takım | ~40 | herhangi bir elektronik mağazası |
| 13 | M3 vida/somun: M3×30 ×4, M3×16 ×4, M3×12 ×2, M3×10 ×14, M3×8 ×2, somun ×12, pul ×4 | takım | ~80 | [M3×10 0,82 TL/adet](https://www.robotistan.com/m3-10mm-ysb-yildiz-silindirik-bas-metrik-vida-10-adet), [somun](https://www.robotistan.com/m3-somun-50-adet) |
| 14 | 16 mm cam misket (bilye) | 2 | ~10 | oyuncakçı / kırtasiye |
| 15 | Cırt bant (20 mm) + EVA sünger bant + birkaç zip-tie | takım | ~80 | hırdavat / kırtasiye |
| | **Elektronik + mekanik toplam** | | **≈ 1.480 TL** | Robotistan ağırlıklı alırsan ≈ 1.600 TL |

Robotistan 1.500 TL üzeri siparişte kargo ücretsiz.

## B. İsteğe bağlı

| Parça | Fiyat (TL) | Ne için |
|---|---:|---|
| Adreslenebilir 5 mm RGB LED (WS2812D-F5) ×2 + biraz ince kablo | ~30 | kulak ışıkları; bacaklara uzatma teli lehimlenir. Yerine [NeoPixel 12'li halka 71,97](https://www.robotistan.com/neopixel-12li-halka) ya da gece lambasının LED'leri |
| Direnç 100k + 33k | ~5 | pil gerilimini ölçmek (`USE_BAT 1`) |
| Kameralı ESP32-S3 N16R8 kartı (OV2640) | 1.111,50 | tablet yüz modunda ileri bakan kamera; USB'li, programlayıcı gerekmez ([Robolink](https://www.robolinkmarket.com/esp32-s3-n16r8-ov2640-kamerali-gelistirme-karti), stokta). ESP32-CAM ([Motorobit 909,00](https://www.motorobit.com/esp32-kamerali-gelistirme-karti-ov2640-wifi-blu)) daha ucuz ama programlayıcısı şu an hiçbir yerde stokta değil. Bkz. [BUTCE.md](BUTCE.md) |
| DRV8833 (TB6612 yerine) | 68,34 | [Robotistan](https://www.robotistan.com/drv8833-step-motor-surucu-karti); `MOTOR_DRIVER 2` |

## C. 3D baskı

Dilimleyici tahmini: **281 g PLA, ~22 saat** (kulaklarla 288 g). Ayrıntı:
[`cad/baski_tahmini.md`](../cad/baski_tahmini.md).

| Seçenek | Tahmini tutar |
|---|---|
| Yerel stüdyo / Armut (3-6 TL/g, en az ~500 TL) | **~1.000-2.000 TL** + 150-250 TL kargo, 1-5 gün |
| JLC3DP (Çin) + DHL + gümrük | ~3.000-7.000 TL, 7-14 gün. Gövde için değmez. |
| Kendi yazıcın (filament 0,42-0,71 TL/g) | ~150-200 TL malzeme |

Yazıcı almak istersen: Bambu Lab A1 ~17.550 TL (şu an stokta yok), A1 Combo ~24.900 TL.
A1 mini'nin tablası (180 mm) taban ve üst kata yetmez. Yazıcı, 4-6 kg baskıdan sonra
kendini ödüyor. Stüdyo mesajı ve ayarlar için: [BASKI.md](BASKI.md).

## D. Toplam

| | TL |
|---|---:|
| Elektronik + mekanik | ~1.480-1.600 |
| 3D baskı (stüdyo) | ~1.150-2.250 |
| **Kıpır v1 toplam** | **≈ 2.600-3.900 TL** (≈ 52-79 USD) |
| Zaten var | telefon, Tab 3 Lite, powerbank, gece lambası + kumandası, Gamebox kolu |

Kıyas: LOOI ~9.000-11.000 TL, Reachy Mini Lite 399 USD + kargo + gümrük, SO-101 kol çifti
yalnızca parçada ~230 USD.

## E. Sonraki aşama: kol (Kıpır v2)

| Parça | Fiyat |
|---|---|
| SO-101 lider + takipçi resmi malzeme listesi | 229,88 USD (+ kargo ve gümrük) |
| SO-101 baskısı (~665 g) | yerel stüdyoda ~2.000-4.000 TL |
| 2 USB kamera | ~2 × 13 USD |
| Eğitim (ACT, bulut L4) | ~1-2 USD/oturum, ya da NVIDIA'lı dizüstünde bedava |

Ayrıntı: [ARASTIRMA.md](ARASTIRMA.md#2-hugging-face-robotiği-lerobot).
