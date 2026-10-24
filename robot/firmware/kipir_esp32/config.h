// =====================================================================
//  Kıpır v1: ayarlar
//  Kartın: ESP32 DevKit V1 (ESP32-WROOM-32, 30 ya da 38 pin)
//  Değiştirmen gereken çoğu şey bu dosyada.
// =====================================================================
#pragma once

// ---------------- Wi-Fi ----------------
// Robot her zaman kendi ağını açar (eski tablet ve telefon buna bağlanır):
#define WIFI_AP_SSID "Kipir"
#define WIFI_AP_PASS "kipir1234"     // en az 8 karakter
// İstersen ev ağına da bağlanır (boş bırakırsan sadece kendi ağı açılır).
// Ev ağına bağlanınca adres: http://kipir.local ya da Seri Monitör'de yazan IP.
#define WIFI_STA_SSID ""
#define WIFI_STA_PASS ""
#define MDNS_NAME "kipir"

// ---------------- Bluetooth (telefon beyni için) ----------------
// Telefonun "beyin" sayfası (beyin.html) robota Web Bluetooth ile bağlanır.
// 1 iken Arduino IDE'de: Araçlar > Partition Scheme > "Huge APP (3MB No OTA)"
// seçmen gerekir (PlatformIO bunu kendisi yapar).
#define KIPIR_BLE 1
#define BLE_NAME "Kipir"

// ---------------- Motor sürücü ----------------
// 1 = TB6612FNG (önerilen), 2 = DRV8833
#define MOTOR_DRIVER 1

// TB6612FNG bağlantısı (A = sol motor, B = sağ motor)
#define PIN_PWMA 25
#define PIN_AIN1 26
#define PIN_AIN2 27
#define PIN_PWMB 13
#define PIN_BIN1 33
#define PIN_BIN2 32
#define PIN_STBY 14

// DRV8833 bağlantısı (MOTOR_DRIVER 2 ise kullanılır)
#define PIN_L_IN1 25
#define PIN_L_IN2 26
#define PIN_R_IN1 27
#define PIN_R_IN2 13

// Motor ters dönüyorsa kabloları değiştirmek yerine bunu 1 yap
#define INVERT_LEFT 0
#define INVERT_RIGHT 0

#define PWM_FREQ 20000          // Hz (duyulmaz)
#define PWM_BITS 8
// Motor sürücünün VM ucundaki gerilim. Önerilen: 2x18650 pil (7.4V).
// Powerbank'ten besliyorsan 5.0, 4 adet şarjlı kalem pil (NiMH) ise 4.8 yaz.
// TT motorlar 6V'luk olduğu için yazılım en fazla ~6V verecek şekilde sınırlar.
#define MOTOR_VOLT 7.4f
#define MOTOR_MAX_V 6.0f        // motora uygulanacak en yüksek ortalama gerilim
#define MOTOR_START_V 1.8f      // TT motorun kalkış için gereken yaklaşık gerilim
#define ACCEL_PER_S 3.0f        // hız değişim sınırı (0->tam hız ~0.33 sn); powerbank'i korur
#define CMD_TIMEOUT_MS 600      // bu kadar komut gelmezse robot durur (güvenlik)
#define MAX_MOVE_MS 3000        // tek komutla en uzun hareket ("teker 50 50 1000" gibi)
#define TURN_GAIN 0.7f          // joystick sağ/sol hassasiyeti

// ---------------- Mesafe sensörü HC-SR04 ----------------
// ECHO 5V çıkış verir: 1k + 2k gerilim bölücü ile bağla (ya da HC-SR04P kullan).
#define USE_SONAR 1
#define PIN_TRIG 4
#define PIN_ECHO 35
#define STOP_CM 15              // önünde bundan yakın engel varsa ileri gitmez
#define SLOW_CM 30              // STOP_CM + bu mesafe içinde yavaşlayarak yaklaşır

// ---------------- IR alıcı (gece lambası kumandası) ----------------
// VS1838B / TSOP38238 alıcı: OUT -> GPIO34, VCC -> 3V3, GND -> GND.
#define USE_IR 1
#define PIN_IR 34
#define IR_DRIVE_MS 350         // bir tuş basışında ne kadar sürsün
#define IR_SPEED 0.7f

// Yaygın 24 tuşlu RGB lamba kumandası (NEC, 0x00F7....). Senin kumandan
// farklıysa sorun değil: kumanda sayfasındaki "IR öğret" ile her tuşu
// robota öğretebilirsin, bu tablo sadece başlangıç değeri.
#define IR_DEFAULT_ILERI 0x00F700FFUL  // parlaklık +
#define IR_DEFAULT_GERI 0x00F7807FUL   // parlaklık -
#define IR_DEFAULT_SOL 0x00F720DFUL    // R
#define IR_DEFAULT_SAG 0x00F7609FUL    // B
#define IR_DEFAULT_DUR 0x00F740BFUL    // OFF
#define IR_DEFAULT_SELAM 0x00F7C03FUL  // ON
#define IR_DEFAULT_DANS 0x00F7D02FUL   // FLASH
#define IR_DEFAULT_UYKU 0x00F7C837UL   // FADE

// ---------------- Kulak LED'leri ----------------
// Her kulakta tek bir adreslenebilir 5 mm LED (WS2812D-F5) ya da tek bir WS2812
// modülü. Takmazsan sorun olmaz. Renkler karışık çıkarsa (kırmızı yerine yeşil)
// EAR_ORDER_RGB'yi 1 yap. PL9823 önerilmez (zamanlaması farklı).
#define USE_EARS 1
#define PIN_EAR_L 19
#define PIN_EAR_R 18
#define EAR_MAX 60              // parlaklık sınırı (0-255); göz almasın
#define EAR_ORDER_RGB 0

// ---------------- Pil gerilimi (isteğe bağlı) ----------------
// Motor pilinin + ucu -> 100k -> GPIO36 -> 33k -> GND. (8.4V -> ~2.1V)
#define USE_BAT 0
#define PIN_BAT 36
#define BAT_RATIO ((100.0f + 33.0f) / 33.0f)
#define BAT_LOW_V 6.6f          // 2x18650 için; altına inerse robot uyarır ve yavaşlar

// ---------------- Gamebox kumandası (isteğe bağlı) ----------------
// 400 oyunlu "Game Box" el konsollarının kablolu 2. oyuncu kolu NES tipi bir
// kaydırma yazmacıdır (4021): LATCH, CLOCK, DATA, VCC, GND. Kablodaki 5 teli
// multimetreyle bulup bağlarsan robotu kablolu kolla sürebilirsin. VCC -> 3V3.
#define USE_NES_PAD 0
#define PIN_NES_LATCH 23
#define PIN_NES_CLOCK 22
#define PIN_NES_DATA 21

// ---------------- Buzzer (pasif) ----------------
#define USE_BUZZER 1
#define PIN_BUZZER 16

// ---------------- Durum LED'i ----------------
#define PIN_STATUS_LED 2

// ---------------- Davranış ----------------
#define SLEEP_AFTER_S 90        // bu kadar saniye kimse ilgilenmezse uyur
