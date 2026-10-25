# Turkish in-stock parts for a cuter, more compact robot (checked 2026-10-24)

## Method
- Search pages of six T-Soft shops were scraped. The shops are Robotistan (rob), Direnc (dir), Motorobit (mot), Robot Sepeti (rs), Robo90 (r90) and Robolink Market (rl).
- Each page embeds `PRODUCT_DATA` with the KDV-inclusive `total_sale_price` and the shop's own stock `quantity`.
- Prices are TL with KDV included. The "+KDV / KDV dahil" pair was confirmed on the product pages of rob, mot, r90 and rl.
- **Stk** is the stock count the shop reports. Direnc shows 99999 when the shop says "in stock" without a count.
- **V** means the spec was read on the product page. **S** means it comes from the search listing only. **M** means it is the manufacturer's spec and the shop page does not state it.
- Scraper and cache: `research/tools/s.py`, `research/tools/p.py`, `research/raw/*.tsv`.

## (a) Displays for the eyes

| Part | Shop | TL | Stk | Size / notes | V | URL |
|---|---|---|---|---|---|---|
| GC9A01 1.28" 240x240 round TFT (SPI) | rob | 351.50 | 19 | Round IPS, 3.3 V. Cheapest round eye. | V | https://www.robotistan.com/gc9a01-128-inc-yuvarlak-tft-lcd-ekran |
| GC9A01 1.28" round, round PCB | mot | 545.40 | 112 | Active area Ø33.4 mm, 400 cd/m². Round PCB, so it is easy to bezel. | V | https://www.motorobit.com/gc9a01-128-240x240-oled-grafik-lcd-ekran-yuvarlak-pcb |
| 1.28" round LCD module (Waveshare style) | rob | 873.92 | 40 | IPS 240x240 | S | https://www.robotistan.com/128inc-yuvarlak-lcd-ekran-modulu |
| 0.96" 160x80 IPS (ST7735S) | rob | 362.87 | 5 | Small wide eye or mouth strip | V | https://www.robotistan.com/096-inc-lcd-ekran-modulu |
| 1.14" 240x135 IPS | rob | 456.01 | 18 | Wide "visor" face | S | https://www.robotistan.com/114-inc-lcd-ekran-modulu |
| 1.3" 240x240 IPS ST7789 | mot | 315.12 | 91 | Square face | S | https://www.motorobit.com/13-240x240-spi-tft-lcd-ekran-st7789 |
| 1.3" 240x240 IPS ST7789 | rl | 381.00 | 61 | | S | https://www.robolinkmarket.com/13inch-240x240-ips-hd-tft-st7789-lcd-oled |
| 1.44" 128x128 TFT (ILI9163) | mot | 303.00 | 123 | Square, low resolution, not IPS | V | https://www.motorobit.com/144-128x128-spi-tft-lcd-ekran |
| 1.69" 240x280 IPS ST7789 (rounded corners) | mot | 363.60 | 32 | Active area 27.97x32.63 mm. Good single "face" screen. | V | https://www.motorobit.com/169-240x280-spi-tft-lcd-ekran-st7789 |
| Waveshare 1.69" 240x280 IPS | rs | 876.99 | 5 | | S | https://www.robotsepeti.com/waveshare-169-inc-lcd-ekran-240280-spi-ips-262k-renk-24382 |
| **ESP32-S3 + 1.28" round IPS board (Waveshare ESP32-S3-LCD-1.28)** | rob | 2,052.76 | 8 | GC9A01, Type-C, LiPo charger on board. M: QMI8658 IMU, 2 MB PSRAM, Ø~38 mm. | V/M | https://www.robotistan.com/esp32s3-128-inc-yuvarlak-ips-gelistirme-karti |
| Same board with touch | rob | 2,692.87 | 15 | Touch version | S | https://www.robotistan.com/esp32s3-128-inc-yuvarlak-dokunmatik-gelistirme-karti |
| Seeed XIAO 1.28" round **touch** display carrier | rs | 1,807.65 | 50 | 39 mm disc; plugs onto a XIAO ESP32S3. M: RTC, microSD and battery management. | V | https://www.robotsepeti.com/seeed-studio-xiao-128-inc-esp32-uyumlu-yuvarlak-ekran-gelistirme-karti |
| LilyGO T-QT ESP32-S3 0.85" GC9107 128x128 | r90 | 1,607.04 | 5 | Tiny all-in-one with 8 MB flash and charger | V | https://www.robo90.com/t-qt-v11-esp32-s3-gelistirme-karti-085-inc-ips-lcd-gc9107 |
| Waveshare ESP32-S3 1.47" 172x320 | mot | 1,636.20 | 26 | Flash + PSRAM | V | https://www.motorobit.com/esp32-s3-147-inch-172320-lcd-ekran-gelistirme-karti |

Not found in stock in any of the six shops:
- 0.71" GC9D01 (the Direnc ESP32-C3 0.71" board shows qty 0)
- 1.54" colour IPS 240x240 (only OLED or e-ink)
- dual-eye modules
- 0.85" ST7735 bare module

Two GC9A01 panels can share one SPI bus with separate CS pins.

## (b) Compact ESP32-S3 boards with PSRAM

| Board | Shop | TL | Stk | Size | Memory | V | URL |
|---|---|---|---|---|---|---|---|
| **ESP32-S3 Super Mini** | mot | 472.68 | 186 | **22.52 x 18 mm** | ESP32S3FH4R2: 4 MB flash, **2 MB PSRAM**; RGB LED on GPIO48; 11 GPIO | V | https://www.motorobit.com/esp32-s3-super-mini-wifible-gelistirme-karti |
| ESP32-S3 Mini dev board (code 25517, Waveshare-style ESP32-S3-Zero/Mini) | rs | 632.44 | 12 | M: ~23.5 x 18 mm | 4 MB flash, 2 MB PSRAM, ceramic antenna | V | https://www.robotsepeti.com/esp32-s3-mini-gelistirme-karti |
| **Seeed XIAO ESP32S3** | rs | 937.37 | **2** | 21 x 17.8 mm | 8 MB flash; M: 8 MB PSRAM; LiPo charger built in | V | https://www.robotsepeti.com/xiao-esp32-s3-gelisitirme-karti |
| Seeed XIAO ESP32S3 **Sense** (camera + mic) | rs | 1,615.55 | 16 | 21 x 17.8 mm (plus camera board) | 8 MB PSRAM, 8 MB flash, OV2640, PDM mic, microSD, charger | V | https://www.robotsepeti.com/seeed-studio-xiao-esp32-s3-sense-kamera-ve-mikrofonlu-ai-gelistirme-karti-ble-wifi |
| ESP32-S3 N16R8 devkit (reference) | dir | 610.23 | 1073 | ~63-69 x 25.5 mm | 16 MB / 8 MB | S | https://www.direnc.net/esp32-s3-n16r8-wifi-bluetooth-board |
| ESP32-S3 N16R8 + OV2640 camera | rl | 1,111.50 | 6 | | 16 MB / 8 MB | S | https://www.robolinkmarket.com/esp32-s3-n16r8-ov2640-kamerali-gelistirme-karti |
| M5StickS3 | r90 | 2,678.40 | 57 | Stick with case | | S | https://www.robo90.com/m5stick-s3-esp32s3-mini-iot-gelistirme-kiti |

Out of stock:
- XIAO ESP32S3 at Robotistan (583.62, qty 0)
- AtomS3 at Direnc (1,917.88, qty 0)
- S3 Super Mini at Direnc, Robo90 and Robolink (qty 0)
- Lolin S3 mini: not listed

## (c) Servos and motors

| Part | Shop | TL | Stk | Specs | V | URL |
|---|---|---|---|---|---|---|
| SG90 180° | rob | 82.25 | 2740 | 9 g, plastic gears | S | https://www.robotistan.com/tower-pro-sg90-rc-mini-servo-motor |
| MG90S 180° | rob | 125.80 | 518 | 13.4 g, metal output gears | S | https://www.robotistan.com/mg90s-servo-motor |
| Tower Pro SG92R | r90 | 130.94 | 205 | 9 g, carbon gears, ~2.5 kg·cm (M) | S | https://www.robo90.com/tower-pro-sg92r-mini-servo-motor |
| **Feetech FS90-FB (position feedback, 4th wire)** | rob | 358.64 | 23 | 1.5 kg·cm @6 V, 0.10 s/60°, 13 g, 23.2x12.5x22 mm. Analog feedback pot means a fall can be detected and the robot can be posed by hand. | V | https://www.robotistan.com/feetech-fs90-fb-mikro-servo-motor-pozisyon-geri-bildirimli |
| **Emax ES08MD II metal digital** | mot | 606.00 | 164 | 1.5/1.8 kg·cm, 0.10 s/60° @6 V, metal gears, digital, 12 g | V | https://www.motorobit.com/emax-es08md-ii-metal-disli-dijital-servo-motor-180 |
| Emax ES08MA II metal analog | mot | 424.20 | 121 | ~1.8 kg·cm, 12 g | S | https://www.motorobit.com/emax-es08ma-ii-metal-disli-analog-servo-motor-180 |
| Emax ES08MA II plastic | mot | 363.60 | 27 | | S | https://www.motorobit.com/emax-es08ma-ii-plastik-disli-analog-servo-motor |
| ES08A II | rob | 355.01 | 43 | 8 g plastic | S | https://www.robotistan.com/es08a-ii-mini-servo-motor |
| **Emax ES9051 4.1 g digital** | rob | 364.08 | 14 | ~0.8 kg·cm (M). For a head tilt or ear, not for legs. | V | https://www.robotistan.com/emax-freestyle-fs2306-2306-1700kv-3-6s-buzz-hawk-rc-drone-fpv-yarisi-icin-2400kv-3-4s-fircasiz-motor-11050 |
| Emax ES9051 | mot | 575.70 | 58 | | S | https://www.motorobit.com/emax-es9051-digital-mini-servo-motor |
| Emax ES9251 II 4 g digital | rob | 409.44 | 31 | 0.25-0.3 kg·cm, 0.07 s/60°. For ears or eyelids. | V | https://www.robotistan.com/emax-es9251Ⅱ-plastik-servo-motor |
| E-Sky 002279 4 g digital | mot | 303.00 | 794 | Micro-heli servo, ears/antenna | V | https://www.motorobit.com/e-sky-002279-4g-dijital-mikro-servo-motor |
| SG90 360° continuous | rob | 94.35 | 1426 | Wheels | S | https://www.robotistan.com/servo-sg90-360-derece |
| MG90S 360° continuous | rob | 187.48 | 904 | | S | https://www.robotistan.com/servo-mg90s-mikro-servo |
| Feetech FS90R continuous | rob | 183.25 | 120 | Better zero-point than SG90-360 | S | https://www.robotistan.com/feetech-fs90r-surekli-donebilen-micro-servo-motor |
| Analog-feedback 9 g 270° metal servo (1.5 kg) | dir | 741.87 | 4 | | S | https://www.direnc.net/analog-geri-beslemeli-9g-270-metal-servo-motor-1 |
| N20 6 V geared, 12 mm (50-1000 rpm options; 100 rpm suits wheels) | r90 | 178.56 | 25-37 | e.g. 6 V 100 rpm qty 28 | S | https://www.robo90.com/6v-12mm-100-rpm-reduktorlu-n20-mikro-dc-motor |
| N20 wheel | r90 | 38.69 | 41 | | S | https://www.robo90.com/n20-tekerlek |
| DRV8833 2-ch driver | mot | 75.75 | 14 | For N20s, runs from 1S | S | https://www.motorobit.com/drv8833-2-kanal-dc-motor-surucusu |
| TB6612FNG | dir | 81.36 | 427 | | S | https://www.direnc.net/tb6612fng-dc-ve-step-motor-surucu-modulu |

Not available:
- Feetech SCS0009, STS3032 and other small bus servos: none listed or in stock. Waveshare ST3215 at Direnc is qty 0, and is 30 kg and far too big anyway.
- MG92B: not listed.
- Geekservo at Robot Sepeti: qty 0.

## (d) Sensors for character

| Part | Shop | TL | Stk | Notes | V | URL |
|---|---|---|---|---|---|---|
| **VL53L0X ToF (black)** | rob | 423.35 | 41 | I2C. For a cliff/edge sensor pointing down. | S | https://www.robotistan.com/vl53l0x-lazer-tof-sensor-modul-i2c-pwm-serial-siyah |
| VL53L0X ToF | rob | 590.88 | 29 | | S | https://www.robotistan.com/vl53l0x-lazer-tof-sensor-modul-i2c-pwm-serial |
| VL53L1X CJMCU-531 (4 m) | rob | 568.50 | 90 | Forward obstacle / "sees you" | S | https://www.robotistan.com/cjmcu531-vl53l1x-lazer-mesafe-sensoru |
| VL53L1X TOF400C | mot | 575.70 | 94 | | S | https://www.motorobit.com/tof0400c-vl53l1x-4m-mesafe-sensor-modulu |
| Pololu VL6180X (≤60 cm, regulated) | rs | 695.25 | 10 | Best for short-range cliff detection | S | https://www.robotsepeti.com/vl6180x-time-of-flight-distance-sensor-carrier-with-voltage-regulato |
| TTP223B touch module | r90 | 17.86 | 1310 | Head pat. A copper-tape pad works behind ~2 mm PLA. | S | https://www.robo90.com/tpp223b-dokunmatik-touch-sensor-modulu |
| TTP223 touch (bare IC) | mot | 9.09 | 1123 | | S | https://www.motorobit.com/ttp223-sot23-6-dokunmatik-sensor-entegresi |
| **BMI160 6-DOF** | dir | 127.86 | 379 | Small, low noise, I2C. For self-righting and fall detection. | V | https://www.direnc.net/bmi160-gyro-sensor-modulu-6-dof-egim-ivmeolcer-jiroskop |
| MPU6500 GY-6500 | mot | 136.35 | 75 | | S | https://www.motorobit.com/mpu6500-6-eksen-ivme-ve-gyro-sensoru-gy-6500 |
| MPU6050 GY-521 | rs | 164.66 | 48 | | S | https://www.robotsepeti.com/mpu6050-6-eksen-ivme-ve-gyro-sensoru-gy-521 |
| INMP441 I2S MEMS mic | dir | 145.29 | 602 | | S | https://www.direnc.net/inmp441-mems-i2s-cok-yonlu-mikrofon-modulu |
| MAX98357 I2S 3 W amp (Adafruit) | rs | 740.38 | 50 | The only in-stock MAX98357 found. The cheap clone at Robo90 is qty 0. | S | https://www.robotsepeti.com/adafruit-3w-class-d-amplifikator-breakout-karti-i2s |
| PAM8403 2x3 W analog amp (cheap fallback, PWM or sigma-delta) | r90 | 26.78 | 85 | | S | https://www.robo90.com/pam8403-2x3w-mini-ses-yukseltici-karti-stereo-amfi |
| Speaker 8 Ω 1 W 32 mm | mot | 51.51 | 4900 | | S | https://www.motorobit.com/hoparlor-8-ohm-8Ω-1w-32mm |
| Speaker 8 Ω 2 W 36 mm | mot | 106.05 | 899 | | S | https://www.motorobit.com/hoparlor-8-ohm-8Ω-2w-36mm |
| Speaker 0.25 W 29 mm | rob | 70.76 | 46 | | S | https://www.robotistan.com/8-ohm-0-25w-hoparlor-29mm |
| WS2812B 5050 single LED | rl | 6.00 | 2351 | Cheek / heart glow | S | https://www.robolinkmarket.com/ws2812b-adreslenebilir-led |
| WS2812 RGB LED module | rob | 130.08 | 160 | | S | https://www.robotistan.com/ws2812-rgb-led-modulu |
| NeoPixel 7-LED disc | mot | 84.84 | 54 | ~23 mm disc | S | https://www.motorobit.com/neopixel-7 |
| NeoPixel 12 ring | rob | 71.97 | 1161 | | S | https://www.robotistan.com/neopixel-12li-halka |

No QMI8658 or ICM-42688 breakout was found in stock. A QMI8658 comes on the Waveshare round S3 board.

## (e) Compact power

### 1S LiPo

| Pack | Shop | TL | Stk | Size / mass | Notes | V | URL |
|---|---|---|---|---|---|---|---|
| Profuse 1S 350 mAh 40C | mot | 363.60 | 106 | 46x20x9 mm, 11 g | High discharge, no PCM | V | https://www.motorobit.com/37v-1s-350mah-40c-lipo-batarya |
| Power-Xtra PX803035 800 mAh (PCM) | rl | 186.00 | 27 | 8x30x35 mm | PCM limits current (~1-2 A typ.) | V | https://www.robolinkmarket.com/power-xtra-px803035-37v-800-mah-li-polymer-pil-devreli |
| Power-Xtra PX603048 900 mAh (PCM, connector) | rl | 231.00 | 20 | 6x30x48 mm | | V | https://www.robolinkmarket.com/power-xtra-px603048-37v-900-mah-li-polymer-pil-devreli-soketli |
| Power-Xtra PX502251 500 mAh | rl | 184.50 | 36 | 5x22x51 mm (from model code) | | S | https://www.robolinkmarket.com/power-xtra-px502251-37v-500-mah-li-polymer-pil-devreli |
| Power-Xtra 1000 mAh (PCM) | rob | 215.30 | 111 | 34x51x5.8 mm, 22 g | | V | https://www.robotistan.com/37v-1000mah-lipo-pil-devreli |
| **Profuse 1S 950 mAh 40C** | mot | 442.38 | 931 | 52.5x30x9 mm, 23 g | Supplies servo peaks easily; needs external protection | V | https://www.motorobit.com/37v-1s-950mah-40c-lipo-batarya |
| Profuse 1S 1050 mAh 40C | mot | 415.72 | 181 | 71x34x6.5 mm, 28 g | | V | https://www.motorobit.com/37v-1s-1050mah-40c-lipo-batarya |
| Profuse 1S 1500 mAh 45C | mot | 569.64 | 153 | 70x34x9 mm, 38 g | | V | https://www.motorobit.com/37v-1s-1500mah-45c-lipo-batarya |
| PX505060 2000 mAh | rob | 347.15 | **1** | 5x50x60 mm (model code) | | S | https://www.robotistan.com/px505060-37v-2000-mahli-polymer-pil |

### 2S LiPo

| Pack | Shop | TL | Stk | Size / mass | V | URL |
|---|---|---|---|---|---|---|
| Tinylab 2S 850 mAh 40C | rob | 847.30 | 30 | | S | https://www.robotistan.com/tinylab-74v-2s-lipo-batarya-850mah-40c |
| Profuse 2S 850 mAh 40C | mot | 1,094.44 | 164 | 56x30x16 mm, 46 g | V | https://www.motorobit.com/74v-2s-850mah-40c-lipo-batarya |
| JSumo 2S 450 mAh 25C | rs | 994.09 | 30 | | S | https://www.robotsepeti.com/jsumo-2s-74v-lipo-li-po-lityum-polimer-batarya-450mah-25c |
| Tinylab 2S 1300 mAh 40C | rob | 759.61 | 60 | | S | https://www.robotistan.com/tinylab-74v-2s-lipo-batarya-1300mah-40c |

### Chargers, protection and converters

| Part | Shop | TL | Stk | Specs | V | URL |
|---|---|---|---|---|---|---|
| TP4056 Type-C 1S charger (with protection) | rob | 21.77 | 7256 | 1 A | S | https://www.robotistan.com/tp4056-type-c-1s-37v-lipo-li-ion-pil-sarj-devresi |
| 1S 2.8 A Type-C charger | mot | 121.20 | 93 | Faster charge; short-circuit and over-temperature protection | V | https://www.motorobit.com/1s-28a-type-c-li-ion-lipo-pil-sarj-devresi |
| 1S 3 A charge + protection board | rl | 37.50 | 144 | | S | https://www.robolinkmarket.com/1s-3a-li-po-sarj-ve-koruma-devresi |
| 1S 4.5 A BMS | mot | 42.42 | 425 | Protection for the 40C packs | S | https://www.motorobit.com/1s-37v-45a-lipo-lion-18650-bms-batarya-koruyucu-balans-devresi |
| **5 V 2 A boost + charger, Type-C (powerbank SoC)** | rl | 55.50 | 69 | 2 A continuous, 3 A peak; charges at 2 A; 4-LED gauge; OCP 3 A. Caveat: these chips may auto-sleep at low load. | V | https://www.robolinkmarket.com/5v-2a-boost-ve-sarj-modulu-type-c-9625 |
| **TPS61088 boost** | r90 | 178.56 | 19 | In 2.8-5 V; out 5 V 3 A (QC can raise it to 9/12 V; keep QC untriggered). 10 A switch, so 4 servos peak OK. | V | https://www.robo90.com/tps61088-hizli-sarj-modulu |
| XL6009 boost | mot | 69.69 | 903 | Realistically ~1.5-2 A at 5 V from 1S | S | https://www.motorobit.com/xl6009-4a-voltaj-yukseltici-regulator-karti |
| SX1308 2 A boost | mot | 39.39 | 2235 | Tiny; 1-1.5 A real | S | https://www.motorobit.com/sx1308-dc-2a-voltaj-yukseltici-boost-modul |
| **SY8205 7-30 V → 5 V 5 A "servo power" buck** | mot | 145.44 | 85 | For a 2S pack | S | https://www.motorobit.com/sy8205-7-30vtan-5va-5a-voltaj-dusurucu-servo-surucu-guc-karti |
| MP1584 3 A adjustable buck (6 V servo rail from 2S) | rob | 53.22 | 187 | | S | https://www.robotistan.com/3a-mini-ayarlanabilir-voltaj-dusurucu-regulator-karti-step-down |
| 2S 8.4 V 2 A charger | mot | 181.80 | 64 | | S | https://www.motorobit.com/2s-84v-2a-li-ion-lipo-pil-sarj-devresi |
| 2S 8.4 V 4 A Type-C charger | rl | 78.00 | 18 | | S | https://www.robolinkmarket.com/2s-li-ion-lipo-pil-sarj-modulu-84v-4a-type-c-girisli |
| 2S 3 A BMS | mot | 53.93 | 106 | | S | https://www.motorobit.com/2s-74v-3a-lipo-lion-18650-bms-batarya-koruyucu-balans-devresi |
