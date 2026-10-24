// =====================================================================
//  Kıpır v1 firmware (ESP32 DevKit V1)
//
//  - Wi-Fi: kendi ağını açar (Kipir / kipir1234), istersen ev ağına da bağlanır
//      http://192.168.4.1/      kumanda sayfası (telefon ya da eski tablet)
//      http://192.168.4.1/yuz   robot yüzü (Galaxy Tab 3 Lite gibi eski cihazlar)
//  - BLE (Nordic UART): telefonun "beyin" sayfası (web/beyin.html) Web Bluetooth
//    ile bağlanır; kamera + yapay zekâ telefonda çalışır, robot sadece uygular.
//  - 2 TT motor: TB6612FNG ya da DRV8833, yumuşak hızlanma, komut gelmezse durur
//  - HC-SR04: önünde engel varsa ileri gitmez
//  - IR alıcı: gece lambasının kumandasıyla sürülür, tuşlar öğretilebilir
//  - Kulaklarda adreslenebilir LED, pasif buzzer ile küçük sesler
//
//  Kod bu dosyada; kipir_esp32.ino sadece Arduino IDE'nin klasörü tanıması için.
//  Arduino IDE: Kart = "ESP32 Dev Module". KIPIR_BLE 1 ise
//  Partition Scheme = "Huge APP (3MB No OTA/1MB SPIFFS)".
//  ESP32 Arduino çekirdeği 2.0.x ve 3.x ile derlenir.
// =====================================================================
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include "soc/soc.h"
#include "soc/gpio_reg.h"
#include "config.h"
#include "web_pages.h"
#include "nec_decoder.h"
#if KIPIR_BLE
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#endif

#ifndef ESP_ARDUINO_VERSION_MAJOR
#define ESP_ARDUINO_VERSION_MAJOR 1
#endif

// ---------------------------------------------------------------------
//  çekirdek 2.x / 3.x uyumu
// ---------------------------------------------------------------------
static void pwmAttach(uint8_t pin, uint8_t ch, uint32_t freq, uint8_t bits) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttachChannel(pin, freq, bits, ch);
#else
  ledcSetup(ch, freq, bits);
  ledcAttachPin(pin, ch);
#endif
}

static void pwmWrite(uint8_t pin, uint8_t ch, uint32_t duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  (void)ch;
  ledcWrite(pin, duty);
#else
  (void)pin;
  ledcWrite(ch, duty);
#endif
}

static const uint8_t BUZZ_CH = 6;  // motorlardan ayrı zamanlayıcı (kanal 6/7)

static void buzzTone(uint32_t f) {
#if USE_BUZZER
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWriteTone(PIN_BUZZER, f);
#else
  ledcWriteTone(BUZZ_CH, f);
#endif
#else
  (void)f;
#endif
}

// Tek bir WS2812 LED'ine 24 bit gönderir (~30 µs, bu çekirdekte kesmeler kapalı).
// Çekirdeğin neopixelWrite'ı 2.0.x'te tek pinde çalıştığı için kendi sürücümüz.
static portMUX_TYPE ledMux = portMUX_INITIALIZER_UNLOCKED;

static void IRAM_ATTR ws2812Send(uint8_t pin, uint32_t bits, uint32_t t0h, uint32_t t1h, uint32_t per) {
  const uint32_t setReg = pin < 32 ? GPIO_OUT_W1TS_REG : GPIO_OUT1_W1TS_REG;
  const uint32_t clrReg = pin < 32 ? GPIO_OUT_W1TC_REG : GPIO_OUT1_W1TC_REG;
  const uint32_t mask = 1UL << (pin & 31);
  portENTER_CRITICAL(&ledMux);
  uint32_t t = ESP.getCycleCount();
  for (int i = 23; i >= 0; i--) {
    const uint32_t hi = ((bits >> i) & 1) ? t1h : t0h;
    while (ESP.getCycleCount() - t < per) {}
    t = ESP.getCycleCount();
    REG_WRITE(setReg, mask);
    while (ESP.getCycleCount() - t < hi) {}
    REG_WRITE(clrReg, mask);
  }
  while (ESP.getCycleCount() - t < per) {}
  portEXIT_CRITICAL(&ledMux);
}

static void earWrite(uint8_t pin, uint8_t r, uint8_t g, uint8_t b) {
#if EAR_ORDER_RGB
  const uint32_t bits = ((uint32_t)r << 16) | ((uint32_t)g << 8) | b;   // PL9823
#else
  const uint32_t bits = ((uint32_t)g << 16) | ((uint32_t)r << 8) | b;   // WS2812
#endif
  const uint32_t mhz = getCpuFrequencyMhz();
  ws2812Send(pin, bits, mhz * 35 / 100, mhz * 70 / 100, mhz * 125 / 100);
}

static bool timeReached(uint32_t deadline) {
  return (int32_t)(millis() - deadline) >= 0;
}

// ---------------------------------------------------------------------
//  durum
// ---------------------------------------------------------------------
enum Action { A_ILERI, A_GERI, A_SOL, A_SAG, A_DUR, A_SELAM, A_DANS, A_UYKU, A_COUNT };
static const char* ACTION_NAMES[A_COUNT] = {"ileri", "geri", "sol", "sag", "dur", "selam", "dans", "uyku"};
static const uint32_t IR_DEFAULTS[A_COUNT] = {
  IR_DEFAULT_ILERI, IR_DEFAULT_GERI, IR_DEFAULT_SOL, IR_DEFAULT_SAG,
  IR_DEFAULT_DUR, IR_DEFAULT_SELAM, IR_DEFAULT_DANS, IR_DEFAULT_UYKU
};

static const char* MOODS[] = {"mutlu", "saskin", "uykulu", "kizgin", "sevgi", "merak", "uzgun"};
static const int MOOD_COUNT = sizeof(MOODS) / sizeof(MOODS[0]);

float speedLimit = 1.0f;           // pil zayıflayınca düşer
float tgtL = 0, tgtR = 0;          // istenen hız (-1..1)
float curL = 0, curR = 0;          // uygulanan hız (rampalı)
uint32_t driveDeadline = 0;        // bu ana kadar komut geçerli
bool blocked = false;

int baseMood = 0;                  // kullanıcının seçtiği mod
int tempMood = -1;                 // kısa süreli mod (ör. engelde şaşkın)
uint32_t tempMoodUntil = 0;
bool sleeping = false;
uint32_t lastInteraction = 0;
float lookX = 0, lookY = 0;
uint32_t lookUntil = 0;
bool talking = false;
uint32_t talkUntil = 0;

bool earAuto = true;
uint8_t earR = 0, earG = 0, earB = 0;

uint32_t irCodes[A_COUNT];
uint32_t lastIrCode = 0;
int learnAction = -1;
uint32_t learnUntil = 0;
int lastIrAction = -1;

Preferences prefs;
WebServer server(80);

int currentMood() {
  if (sleeping) return 2;
  if (tempMood >= 0 && !timeReached(tempMoodUntil)) return tempMood;
  return baseMood;
}

int moodIndex(const String& m) {
  for (int i = 0; i < MOOD_COUNT; i++)
    if (m == MOODS[i]) return i;
  return -1;
}

void touchInteraction() {
  lastInteraction = millis();
}

// ---------------------------------------------------------------------
//  ses
// ---------------------------------------------------------------------
struct Note { uint16_t f; uint16_t ms; };
static const Note SND_SELAM[] = {{880, 90}, {0, 40}, {1175, 140}, {0, 0}};
static const Note SND_SASKIN[] = {{600, 60}, {900, 60}, {1300, 120}, {0, 0}};
static const Note SND_UYKU[] = {{700, 200}, {500, 250}, {350, 400}, {0, 0}};
static const Note SND_DANS[] = {{523, 120}, {659, 120}, {784, 120}, {1047, 220}, {0, 0}};
static const Note SND_BIP[] = {{1000, 70}, {0, 0}};
static const Note SND_ENGEL[] = {{300, 140}, {0, 0}};
static const Note SND_SEVGI[] = {{784, 110}, {988, 110}, {1319, 200}, {0, 0}};

const Note* sndPlaying = nullptr;
int sndIndex = 0;
uint32_t sndNext = 0;

void playSound(const Note* s) {
  sndPlaying = s;
  sndIndex = 0;
  sndNext = millis();
}

bool playSoundByName(const String& n) {
  if (n == "selam") playSound(SND_SELAM);
  else if (n == "saskin") playSound(SND_SASKIN);
  else if (n == "uyku") playSound(SND_UYKU);
  else if (n == "dans") playSound(SND_DANS);
  else if (n == "bip") playSound(SND_BIP);
  else if (n == "sevgi") playSound(SND_SEVGI);
  else return false;
  return true;
}

void updateSound() {
  if (!sndPlaying || !timeReached(sndNext)) return;
  const Note& n = sndPlaying[sndIndex];
  if (n.ms == 0) {
    buzzTone(0);
    sndPlaying = nullptr;
    return;
  }
  buzzTone(n.f);
  sndNext = millis() + n.ms;
  sndIndex++;
}

// ---------------------------------------------------------------------
//  motorlar
// ---------------------------------------------------------------------
void motorOut(int side, float v) {
  bool inv = side == 0 ? INVERT_LEFT : INVERT_RIGHT;
  if (inv) v = -v;
  float a = fabsf(v);
  const uint32_t maxd = (1UL << PWM_BITS) - 1;
  // pil gerilimine göre ölçekle: motor hiçbir zaman ~6V'tan fazlasını görmesin
  const float dmax = fminf(1.0f, MOTOR_MAX_V / MOTOR_VOLT) * speedLimit;
  const float dmin = fminf(dmax, MOTOR_START_V / MOTOR_VOLT);
  uint32_t duty = a < 0.02f ? 0 : (uint32_t)((dmin + (dmax - dmin) * fminf(a, 1.0f)) * maxd);
#if MOTOR_DRIVER == 1
  uint8_t in1 = side == 0 ? PIN_AIN1 : PIN_BIN1;
  uint8_t in2 = side == 0 ? PIN_AIN2 : PIN_BIN2;
  uint8_t pwm = side == 0 ? PIN_PWMA : PIN_PWMB;
  uint8_t ch = side == 0 ? 0 : 1;
  if (duty == 0) {            // kısa devre fren: tekerler serbestçe kaymaz
    digitalWrite(in1, HIGH);
    digitalWrite(in2, HIGH);
    pwmWrite(pwm, ch, 0);
  } else {
    digitalWrite(in1, v > 0 ? HIGH : LOW);
    digitalWrite(in2, v > 0 ? LOW : HIGH);
    pwmWrite(pwm, ch, duty);
  }
#else
  uint8_t p1 = side == 0 ? PIN_L_IN1 : PIN_R_IN1;
  uint8_t p2 = side == 0 ? PIN_L_IN2 : PIN_R_IN2;
  uint8_t c1 = side == 0 ? 0 : 2;
  uint8_t c2 = side == 0 ? 1 : 3;
  if (duty == 0) {
    pwmWrite(p1, c1, maxd);
    pwmWrite(p2, c2, maxd);
  } else if (v > 0) {
    pwmWrite(p1, c1, duty);
    pwmWrite(p2, c2, 0);
  } else {
    pwmWrite(p1, c1, 0);
    pwmWrite(p2, c2, duty);
  }
#endif
}

void setupMotors() {
#if MOTOR_DRIVER == 1
  pinMode(PIN_AIN1, OUTPUT);
  pinMode(PIN_AIN2, OUTPUT);
  pinMode(PIN_BIN1, OUTPUT);
  pinMode(PIN_BIN2, OUTPUT);
  pinMode(PIN_STBY, OUTPUT);
  digitalWrite(PIN_STBY, HIGH);
  pwmAttach(PIN_PWMA, 0, PWM_FREQ, PWM_BITS);
  pwmAttach(PIN_PWMB, 1, PWM_FREQ, PWM_BITS);
#else
  pwmAttach(PIN_L_IN1, 0, PWM_FREQ, PWM_BITS);
  pwmAttach(PIN_L_IN2, 1, PWM_FREQ, PWM_BITS);
  pwmAttach(PIN_R_IN1, 2, PWM_FREQ, PWM_BITS);
  pwmAttach(PIN_R_IN2, 3, PWM_FREQ, PWM_BITS);
#endif
  motorOut(0, 0);
  motorOut(1, 0);
}

void wake();

// Sürüş komutu: l, r -1..1, süre ms
void drive(float l, float r, uint32_t ms) {
  if (!isfinite(l) || !isfinite(r)) l = r = 0;
  tgtL = constrain(l, -1.0f, 1.0f);
  tgtR = constrain(r, -1.0f, 1.0f);
  driveDeadline = millis() + ms;
  touchInteraction();
  if (fabsf(l) + fabsf(r) > 0.05f) {
    if (sleeping) wake();
    // sağa dönerken (l > r) robotun sağına bakar; ekran karşıya dönük olduğu için bu ekranın solu
    lookX = constrain((r - l) * 0.8f, -1.0f, 1.0f);
    lookY = 0;
    lookUntil = millis() + 400;
  }
}

// Joystick: x sağ +, y ileri +, -1..1
void driveXY(float x, float y, uint32_t ms) {
  float l = y + x * TURN_GAIN;
  float r = y - x * TURN_GAIN;
  float m = fmaxf(fabsf(l), fabsf(r));
  if (m > 1.0f) { l /= m; r /= m; }
  drive(l, r, ms);
}

void stopAll();
void startDance();

// ---------------------------------------------------------------------
//  HC-SR04 (kesmeli, beklemesiz)
// ---------------------------------------------------------------------
volatile uint32_t echoStart = 0, echoUs = 0;
volatile bool echoNew = false;
int distCm = -1;
int distBuf[3] = {-1, -1, -1};
uint32_t lastPing = 0, lastEcho = 0;
bool sonarNear = false;   // son geçerli ölçüm engele yakındı

void IRAM_ATTR echoIsr() {
  if (digitalRead(PIN_ECHO)) {
    echoStart = micros();
  } else {
    echoUs = micros() - echoStart;
    echoNew = true;
  }
}

static int median3(int a, int b, int c) {
  if (a > b) { int t = a; a = b; b = t; }
  if (b > c) { int t = b; b = c; c = t; }
  if (a > b) { int t = a; a = b; b = t; }
  return b;
}

void setupSonar() {
#if USE_SONAR
  pinMode(PIN_TRIG, OUTPUT);
  digitalWrite(PIN_TRIG, LOW);
  pinMode(PIN_ECHO, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_ECHO), echoIsr, CHANGE);
#endif
}

void updateSonar() {
#if USE_SONAR
  uint32_t now = millis();
  if (echoNew) {
    echoNew = false;
    int d = (int)(echoUs / 58);
    if (d < 2) d = 1;          // sensörün kör bölgesi: çok yakın
    if (d <= 400) {            // 400'den uzunu "yankı yok" demek; aşağıda zaman aşımı karar verir
      distBuf[0] = distBuf[1];
      distBuf[1] = distBuf[2];
      distBuf[2] = d;
      distCm = distBuf[0] < 0 ? d : median3(distBuf[0], distBuf[1], distBuf[2]);
      lastEcho = now;
      sonarNear = distCm < STOP_CM + 10;
    }
  }
  if (now - lastPing >= 70) {
    lastPing = now;
    digitalWrite(PIN_TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(PIN_TRIG, LOW);
  }
  // Ölçüm kesildi: az önce engele yakındıysak (burnu duvara dayalı, ses emiliyor) bir süre
  // "çok yakın" say; değilse açık alan say.
  if (now - lastEcho > 500) distCm = (sonarNear && now - lastEcho < 2500) ? 1 : -1;
#endif
}

// ---------------------------------------------------------------------
//  IR alıcı: NEC çözücü (kütüphanesiz)
// ---------------------------------------------------------------------
static uint32_t irLastEdge = 0;   // sadece kesme içinde kullanılır
static NecDecoder nec;
volatile uint32_t irCodeIsr = 0;
volatile bool irReady = false, irRepeatIsr = false;
portMUX_TYPE irMux = portMUX_INITIALIZER_UNLOCKED;

void IRAM_ATTR irIsr() {
  uint32_t now = micros();
  uint32_t d = now - irLastEdge;
  irLastEdge = now;
  bool wasMark = digitalRead(PIN_IR);  // kenardan sonra HIGH ise önceki parça LOW (taşıyıcı) idi
  uint32_t code;
  int r = nec.edge(d, wasMark, &code);
  if (r == NecDecoder::CODE) {
    irCodeIsr = code;
    irRepeatIsr = false;
    irReady = true;
  } else if (r == NecDecoder::REPEAT && !(irReady && !irRepeatIsr)) {  // okunmamış yeni kodu ezme
    irRepeatIsr = true;
    irReady = true;
  }
}

void loadIrCodes() {
  prefs.begin("kipir", true);
  for (int i = 0; i < A_COUNT; i++) {
    char key[6];
    snprintf(key, sizeof key, "ir%d", i);
    irCodes[i] = prefs.getULong(key, IR_DEFAULTS[i]);
  }
  prefs.end();
}

void saveIrCode(int a, uint32_t code) {
  prefs.begin("kipir", false);
  for (int i = 0; i < A_COUNT; i++) {   // aynı tuş başka bir eylemde kalmasın
    if (i != a && irCodes[i] != code) continue;
    irCodes[i] = i == a ? code : 0;
    char key[6];
    snprintf(key, sizeof key, "ir%d", i);
    prefs.putULong(key, irCodes[i]);
  }
  prefs.end();
}

void resetIrCodes() {
  prefs.begin("kipir", false);
  prefs.clear();
  prefs.end();
  for (int i = 0; i < A_COUNT; i++) irCodes[i] = IR_DEFAULTS[i];
}

void setupIR() {
#if USE_IR
  pinMode(PIN_IR, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_IR), irIsr, CHANGE);
#endif
  loadIrCodes();
}

void doAction(int a, bool repeat) {
  switch (a) {
    case A_ILERI: drive(IR_SPEED, IR_SPEED, IR_DRIVE_MS); break;
    case A_GERI: drive(-IR_SPEED, -IR_SPEED, IR_DRIVE_MS); break;
    case A_SOL: drive(-IR_SPEED * 0.8f, IR_SPEED * 0.8f, IR_DRIVE_MS); break;
    case A_SAG: drive(IR_SPEED * 0.8f, -IR_SPEED * 0.8f, IR_DRIVE_MS); break;
    case A_DUR: stopAll(); break;
    case A_SELAM:
      if (!repeat) { wake(); baseMood = 0; playSound(SND_SELAM); }
      break;
    case A_DANS:
      if (!repeat) startDance();
      break;
    case A_UYKU:
      if (!repeat) { stopAll(); sleeping = true; playSound(SND_UYKU); }
      break;
  }
}

void updateIR() {
#if USE_IR
  if (learnAction >= 0 && timeReached(learnUntil)) learnAction = -1;   // 15 sn içinde tuşa basılmadı
  if (!irReady) return;
  portENTER_CRITICAL(&irMux);
  uint32_t code = irCodeIsr;
  bool rep = irRepeatIsr;
  irReady = false;
  portEXIT_CRITICAL(&irMux);

  static uint32_t lastIrMs = 0;
  uint32_t gap = millis() - lastIrMs;
  lastIrMs = millis();
  if (rep) {  // tuş basılı tutuluyor: sadece az önce basılan sürüş tuşunu sürdür
    if (gap < 200 && lastIrAction >= A_ILERI && lastIrAction <= A_SAG) doAction(lastIrAction, true);
    else lastIrAction = -1;
    return;
  }
  lastIrCode = code;
  Serial.printf("IR: 0x%08lX\n", (unsigned long)code);
  if (learnAction >= 0) {
    saveIrCode(learnAction, code);
    Serial.printf("IR ogrenildi: %s = 0x%08lX\n", ACTION_NAMES[learnAction], (unsigned long)code);
    learnAction = -1;
    playSound(SND_BIP);
    return;
  }
  int found = irCodes[A_DUR] == code ? A_DUR : -1;   // DUR her zaman önce
  for (int i = 0; found < 0 && i < A_COUNT; i++)
    if (code != 0 && irCodes[i] == code) found = i;
  lastIrAction = found;
  if (found >= 0) {
    if (sleeping && found != A_UYKU) wake();
    doAction(found, false);
  }
#endif
}

// ---------------------------------------------------------------------
//  pil gerilimi
// ---------------------------------------------------------------------
float batV = -1;

void updateBattery() {
#if USE_BAT
  static uint32_t last = 0, lastWarn = 0;
  if (millis() - last < 500) return;
  last = millis();
  float v = analogReadMilliVolts(PIN_BAT) / 1000.0f * BAT_RATIO;
  batV = batV < 0 ? v : batV * 0.8f + v * 0.2f;   // yumuşat
  bool low = batV > 1.0f && batV < BAT_LOW_V;
  speedLimit = low ? 0.6f : 1.0f;
  if (low && millis() - lastWarn > 60000UL) {
    lastWarn = millis();
    playSound(SND_UYKU);
    tempMood = 6;  // üzgün
    tempMoodUntil = millis() + 3000;
  }
#endif
}

// ---------------------------------------------------------------------
//  Gamebox (NES tipi) kablolu kol
//  bit: 0 A, 1 B, 2 Select, 3 Start, 4 Yukarı, 5 Aşağı, 6 Sol, 7 Sağ
// ---------------------------------------------------------------------
#if USE_NES_PAD
uint8_t readNes() {
  digitalWrite(PIN_NES_LATCH, HIGH);
  delayMicroseconds(12);
  digitalWrite(PIN_NES_LATCH, LOW);
  delayMicroseconds(6);
  uint8_t b = 0;
  for (int i = 0; i < 8; i++) {
    if (digitalRead(PIN_NES_DATA) == LOW) b |= (1 << i);  // basılı = LOW
    digitalWrite(PIN_NES_CLOCK, HIGH);
    delayMicroseconds(6);
    digitalWrite(PIN_NES_CLOCK, LOW);
    delayMicroseconds(6);
  }
  return b;
}
#endif

void setupNes() {
#if USE_NES_PAD
  pinMode(PIN_NES_LATCH, OUTPUT);
  pinMode(PIN_NES_CLOCK, OUTPUT);
  pinMode(PIN_NES_DATA, INPUT_PULLUP);   // kol takılı değilse "hiçbiri basılı değil" okunur
  digitalWrite(PIN_NES_LATCH, LOW);
  digitalWrite(PIN_NES_CLOCK, LOW);
#endif
}

void updateNes() {
#if USE_NES_PAD
  static uint32_t last = 0;
  static uint8_t prev = 0;
  if (millis() - last < 30) return;
  last = millis();
  uint8_t b = readNes();
  if (b == 0xFF) b = 0;   // hepsi birden basılı görünüyorsa kol takılı değildir
  uint8_t down = b & ~prev;
  prev = b;
  float x = (b & 0x80 ? 1.0f : 0) - (b & 0x40 ? 1.0f : 0);
  float y = (b & 0x10 ? 1.0f : 0) - (b & 0x20 ? 1.0f : 0);
  if (x != 0 || y != 0) {
    if (sleeping) wake();
    driveXY(x * 0.8f, y * 0.8f, 150);
  }
  if (down & 0x01) { wake(); playSound(SND_SELAM); }
  if (down & 0x02) stopAll();
  if (down & 0x08) startDance();
  if (down & 0x04) { wake(); baseMood = (baseMood + 1) % MOOD_COUNT; if (baseMood == 2) baseMood = 3; }
#endif
}

// ---------------------------------------------------------------------
//  dans rutini
// ---------------------------------------------------------------------
struct Step { float l, r; uint16_t ms; };
static const Step DANCE[] = {
  {0.8f, -0.8f, 260}, {-0.8f, 0.8f, 260}, {0.8f, -0.8f, 260}, {-0.8f, 0.8f, 260},
  {0.6f, 0.6f, 220}, {-0.6f, -0.6f, 220}, {0.9f, -0.9f, 700}, {0, 0, 0}
};
int danceStep = -1;
uint32_t danceNext = 0;

void startDance() {
  wake();
  danceStep = 0;
  danceNext = millis();
  playSound(SND_DANS);
}

void updateDance() {
  if (danceStep < 0 || !timeReached(danceNext)) return;
  const Step& s = DANCE[danceStep];
  if (s.ms == 0) {
    danceStep = -1;
    drive(0, 0, 0);
    return;
  }
  drive(s.l, s.r, s.ms + 50);
  danceNext = millis() + s.ms;
  danceStep++;
}

void stopAll() {
  danceStep = -1;
  tgtL = tgtR = 0;
  driveDeadline = millis();
  touchInteraction();
}

void wake() {
  touchInteraction();
  if (sleeping) {
    sleeping = false;
    baseMood = 0;
    playSound(SND_SELAM);
  }
}

// ---------------------------------------------------------------------
//  sürüş döngüsü (rampa + engel + zaman aşımı)
// ---------------------------------------------------------------------
void updateMotors() {
  static uint32_t last = 0;
  uint32_t now = millis();
  if (now - last < 5) return;
  float dt = (now - last) / 1000.0f;
  last = now;
  if (dt > 0.1f) dt = 0.1f;

  if (timeReached(driveDeadline)) tgtL = tgtR = 0;
  if (!isfinite(tgtL) || !isfinite(tgtR)) tgtL = tgtR = 0;
  if (!isfinite(curL)) curL = 0;
  if (!isfinite(curR)) curR = 0;

  float fwd = (tgtL + tgtR) * 0.5f;
  float turn = (tgtL - tgtR) * 0.5f;
  static bool vetoed = false;
  bool nowBlocked = USE_SONAR && distCm > 0 && distCm < STOP_CM;
  bool veto = nowBlocked && fwd > 0;
  if (veto) {
    if (!vetoed) {                // ileri gitmek istendi ama engel var
      playSound(SND_ENGEL);
      tempMood = 1;  // şaşkın
      tempMoodUntil = now + 1500;
    }
    fwd = 0;
  } else if (USE_SONAR && fwd > 0 && distCm > 0 && distCm < STOP_CM + SLOW_CM) {
    // engele yaklaşırken yavaşla: duruş mesafesi STOP_CM'yi aşmasın
    fwd = fminf(fwd, 0.3f + 0.7f * (distCm - STOP_CM) / (float)SLOW_CM);
  }
  vetoed = veto;
  blocked = nowBlocked;
  float l = fwd + turn, r = fwd - turn;

  float up = ACCEL_PER_S * dt, down = 2.0f * ACCEL_PER_S * dt;  // yavaşlama daha hızlı
  float dl = l - curL, dr = r - curR;
  curL += constrain(dl, -(fabsf(l) < fabsf(curL) ? down : up), (fabsf(l) < fabsf(curL) ? down : up));
  curR += constrain(dr, -(fabsf(r) < fabsf(curR) ? down : up), (fabsf(r) < fabsf(curR) ? down : up));
  motorOut(0, curL);
  motorOut(1, curR);
}

// ---------------------------------------------------------------------
//  mod / uyku / kulaklar
// ---------------------------------------------------------------------
void updateMood() {
  if (!sleeping && millis() - lastInteraction > (uint32_t)SLEEP_AFTER_S * 1000UL) {
    sleeping = true;
    playSound(SND_UYKU);
  }
  if (talking && timeReached(talkUntil)) talking = false;
}

void updateEars() {
#if USE_EARS
  static uint32_t last = 0;
  if (millis() - last < 33) return;
  last = millis();
  float t = millis() / 1000.0f;
  uint8_t r, g, b;
  float k = 1.0f;
  if (!earAuto) {
    r = earR; g = earG; b = earB;
  } else {
    switch (currentMood()) {
      case 0: r = 255; g = 170; b = 0; break;    // mutlu
      case 1: r = 255; g = 255; b = 255; k = (millis() / 120) % 2 ? 1.0f : 0.2f; break;  // şaşkın
      case 2: r = 0; g = 40; b = 255; k = 0.25f + 0.25f * sinf(t * 1.2f); break;          // uykulu
      case 3: r = 255; g = 0; b = 0; break;      // kızgın
      case 4: r = 255; g = 30; b = 120; k = 0.6f + 0.4f * sinf(t * 6.0f); break;          // sevgi
      case 5: r = 0; g = 220; b = 255; break;    // merak
      default: r = 60; g = 60; b = 255; k = 0.5f; break;  // üzgün
    }
    if (danceStep >= 0) {  // dansta gökkuşağı
      float h = fmodf(t * 2.0f, 3.0f);
      r = (uint8_t)(255 * fmaxf(0, 1 - fabsf(h - 0.0f)) + 255 * fmaxf(0, h - 2.0f));
      g = (uint8_t)(255 * fmaxf(0, 1 - fabsf(h - 1.0f)));
      b = (uint8_t)(255 * fmaxf(0, 1 - fabsf(h - 2.0f)));
      k = 1.0f;
    }
  }
  if (talking) k *= 0.55f + 0.45f * sinf(t * 18.0f);
  float s = k * EAR_MAX / 255.0f;
  uint8_t rr = (uint8_t)(r * s), gg = (uint8_t)(g * s), bb = (uint8_t)(b * s);
  earWrite(PIN_EAR_L, rr, gg, bb);
  earWrite(PIN_EAR_R, rr, gg, bb);
#endif
}

void updateStatusLed() {
  uint32_t period = (fabsf(curL) + fabsf(curR) > 0.05f) ? 150 : 1000;
  digitalWrite(PIN_STATUS_LED, (millis() / period) % 2 ? HIGH : LOW);
}

// ---------------------------------------------------------------------
//  durum JSON
// ---------------------------------------------------------------------
bool bleConnected = false;

String statusJson() {
  float lx = timeReached(lookUntil) ? 0 : lookX;
  float ly = timeReached(lookUntil) ? 0 : lookY;
  char buf[320];
  snprintf(buf, sizeof buf,
           "{\"m\":\"%s\",\"lx\":%.2f,\"ly\":%.2f,\"t\":%d,\"d\":%d,\"b\":%d,"
           "\"l\":%.2f,\"r\":%.2f,\"ir\":\"%08lX\",\"ogren\":\"%s\",\"dans\":%d,"
           "\"ble\":%d,\"v\":%.2f,\"up\":%lu,\"ip\":\"%s\"}",
           MOODS[currentMood()], lx, ly, talking ? 1 : 0, distCm, blocked ? 1 : 0,
           curL, curR, (unsigned long)lastIrCode,
           learnAction >= 0 ? ACTION_NAMES[learnAction] : "",
           danceStep >= 0 ? 1 : 0, bleConnected ? 1 : 0, batV,
           (unsigned long)(millis() / 1000), WiFi.localIP().toString().c_str());
  return String(buf);
}

// ---------------------------------------------------------------------
//  ortak komut yorumlayıcı (HTTP ve BLE aynı komutları kullanır)
//  BLE'de her yazma tek komut ve en fazla 20 bayt (varsayılan MTU); satır sonu isteğe bağlı.
//  surus X Y | teker L R | dur | mod AD | kulak R G B | kulak oto |
//  bak X Y | konus 0/1 | ses AD | dans | uyu | uyan
// ---------------------------------------------------------------------
bool runCommand(const String& line) {
  String cmd = line;
  cmd.trim();
  int sp = cmd.indexOf(' ');
  String name = sp < 0 ? cmd : cmd.substring(0, sp);
  String rest = sp < 0 ? String("") : cmd.substring(sp + 1);
  float a[3] = {0, 0, 0};
  int n = 0;
  int from = 0;
  while (n < 3 && from < (int)rest.length()) {
    int next = rest.indexOf(' ', from);
    if (next < 0) next = rest.length();
    String tok = rest.substring(from, next);
    from = next + 1;
    if (tok.length() == 0) continue;
    float f = tok.toFloat();
    if (!isfinite(f)) return false;   // "nan", "inf", "1e39" gibi değerleri reddet
    a[n++] = f;
  }
  // isteğe bağlı süre en fazla MAX_MOVE_MS: güvenlik zaman aşımı aşılamasın
  const uint32_t ms = n >= 3 ? (uint32_t)constrain(a[2], 0.0f, (float)MAX_MOVE_MS) : CMD_TIMEOUT_MS;

  if (name == "surus") {            // x, y: -100..100, isteğe bağlı süre ms
    if (danceStep >= 0) danceStep = -1;
    driveXY(constrain(a[0], -100.0f, 100.0f) / 100.0f, constrain(a[1], -100.0f, 100.0f) / 100.0f, ms);
  } else if (name == "teker") {     // l, r: -100..100, isteğe bağlı süre ms
    if (danceStep >= 0) danceStep = -1;
    drive(a[0] / 100.0f, a[1] / 100.0f, ms);
  } else if (name == "dur") {
    stopAll();
  } else if (name == "mod") {
    int m = moodIndex(rest);
    if (m < 0) return false;
    wake();
    sleeping = (m == 2);
    baseMood = m;
    tempMood = -1;
  } else if (name == "kulak") {
    if (rest == "oto") {
      earAuto = true;
    } else {
      earAuto = false;
      earR = constrain((int)a[0], 0, 255);
      earG = constrain((int)a[1], 0, 255);
      earB = constrain((int)a[2], 0, 255);
    }
  } else if (name == "bak") {
    lookX = constrain(a[0], -1.0f, 1.0f);
    lookY = constrain(a[1], -1.0f, 1.0f);
    lookUntil = millis() + 2500;
  } else if (name == "konus") {
    talking = a[0] > 0.5f;
    talkUntil = millis() + 20000;   // sayfa kapanırsa ağız sonsuza dek açık kalmasın
    touchInteraction();
  } else if (name == "ses") {
    return playSoundByName(rest);
  } else if (name == "dans") {
    startDance();
  } else if (name == "uyu") {
    stopAll();
    sleeping = true;
    playSound(SND_UYKU);
  } else if (name == "uyan") {
    wake();
  } else if (name == "durum") {
    // sadece durum
  } else {
    return false;
  }
  return true;
}

// ---------------------------------------------------------------------
//  HTTP
// ---------------------------------------------------------------------
void sendStatus() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Cache-Control", "no-store");
  server.send(200, "application/json", statusJson());
}

void sendPage(const char* page) {
  server.sendHeader("Cache-Control", "no-store");
  server.send_P(200, "text/html; charset=utf-8", page);
}

String argOr(const char* k, const char* def) {
  return server.hasArg(k) ? server.arg(k) : String(def);
}

void setupHttp() {
  server.on("/", []() { sendPage(PAGE_KUMANDA); });
  server.on("/yuz", []() { sendPage(PAGE_YUZ); });
  server.on("/durum", sendStatus);
  server.on("/k", []() {  // genel komut: /k?c=surus%2050%200
    bool ok = runCommand(server.arg("c"));
    if (!ok) {
      server.sendHeader("Access-Control-Allow-Origin", "*");
      server.send(400, "text/plain", "bilinmeyen komut");
      return;
    }
    sendStatus();
  });
  server.on("/surus", []() {
    runCommand("surus " + argOr("x", "0") + " " + argOr("y", "0"));
    sendStatus();
  });
  server.on("/dur", []() {
    runCommand("dur");
    sendStatus();
  });
  server.on("/ir_ogren", []() {
    String a = server.arg("a");
    learnAction = -1;
    for (int i = 0; i < A_COUNT; i++)
      if (a == ACTION_NAMES[i]) learnAction = i;
    learnUntil = millis() + 15000;
    sendStatus();
  });
  server.on("/ir_sifirla", []() {
    resetIrCodes();
    sendStatus();
  });
  server.on("/ir_liste", []() {
    String s = "{";
    for (int i = 0; i < A_COUNT; i++) {
      char b[40];
      snprintf(b, sizeof b, "%s\"%s\":\"%08lX\"", i ? "," : "", ACTION_NAMES[i], (unsigned long)irCodes[i]);
      s += b;
    }
    s += "}";
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "application/json", s);
  });
  server.onNotFound([]() { server.send(404, "text/plain", "yok"); });
  server.begin();
}

// ---------------------------------------------------------------------
//  BLE (Nordic UART Service)
// ---------------------------------------------------------------------
#if KIPIR_BLE
#define NUS_SERVICE "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define NUS_RX "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
#define NUS_TX "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

BLECharacteristic* bleTx = nullptr;
portMUX_TYPE bleMux = portMUX_INITIALIZER_UNLOCKED;
const int BLEQ = 8;
char bleQueue[BLEQ][64];
volatile int bleHead = 0, bleTail = 0;
volatile bool bleJustDisconnected = false;

class KipirServerCb : public BLEServerCallbacks {
  void onConnect(BLEServer*) override { bleConnected = true; }
  void onDisconnect(BLEServer*) override {
    bleConnected = false;
    bleJustDisconnected = true;
  }
};

class KipirRxCb : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* c) override {
    String v = String(c->getValue().c_str());
    // bir yazımda birden çok satır gelebilir
    int from = 0;
    while (from < (int)v.length()) {
      int nl = v.indexOf('\n', from);
      if (nl < 0) nl = v.length();
      String line = v.substring(from, nl);
      from = nl + 1;
      if (line.length() == 0) continue;
      portENTER_CRITICAL(&bleMux);
      int next = (bleHead + 1) % BLEQ;
      if (next != bleTail) {
        strncpy(bleQueue[bleHead], line.c_str(), 63);
        bleQueue[bleHead][63] = 0;
        bleHead = next;
      }
      portEXIT_CRITICAL(&bleMux);
    }
  }
};

void setupBle() {
  BLEDevice::init(BLE_NAME);
  BLEDevice::setMTU(185);   // telefon isterse daha uzun yazmalar; komutlarımız zaten <= 20 bayt
  BLEServer* srv = BLEDevice::createServer();
  srv->setCallbacks(new KipirServerCb());
  BLEService* svc = srv->createService(NUS_SERVICE);
  bleTx = svc->createCharacteristic(NUS_TX, BLECharacteristic::PROPERTY_NOTIFY);
  bleTx->addDescriptor(new BLE2902());
  BLECharacteristic* rx = svc->createCharacteristic(
      NUS_RX, BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
  rx->setCallbacks(new KipirRxCb());
  svc->start();
  BLEAdvertising* adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(NUS_SERVICE);
  adv->setScanResponse(true);
  BLEDevice::startAdvertising();
}

void bleNotify(const char* s) {
  if (!bleConnected || !bleTx) return;
  bleTx->setValue((uint8_t*)s, strlen(s));
  bleTx->notify();
}

void updateBle() {
  while (true) {
    char line[64];
    portENTER_CRITICAL(&bleMux);
    bool empty = bleHead == bleTail;
    if (!empty) {
      memcpy(line, bleQueue[bleTail], sizeof line);
      bleTail = (bleTail + 1) % BLEQ;
    }
    portEXIT_CRITICAL(&bleMux);
    if (empty) break;
    runCommand(String(line));
  }
  static bool advPending = false;
  static uint32_t advAt = 0;
  if (bleJustDisconnected) {   // bağlantı koptu: hemen dur, biraz sonra tekrar görünür ol
    bleJustDisconnected = false;
    stopAll();
    talking = false;
    advPending = true;
    advAt = millis() + 200;
  }
  if (advPending && timeReached(advAt)) {
    advPending = false;
    BLEDevice::startAdvertising();
  }
  // telefona kısa durum: "d=23 b=0 m=mutlu" (20 bayt sınırına sığar)
  static uint32_t last = 0;
  if (bleConnected && millis() - last > 300) {
    last = millis();
    char s[24];
    snprintf(s, sizeof s, "d=%d b=%d m=%d", distCm, blocked ? 1 : 0, currentMood());
    bleNotify(s);
  }
}
#endif

// ---------------------------------------------------------------------
//  kurulum ve döngü
// ---------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\nKipir v1 basliyor");
  pinMode(PIN_STATUS_LED, OUTPUT);
#if USE_BUZZER
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttachChannel(PIN_BUZZER, 2000, 8, BUZZ_CH);
#else
  ledcSetup(BUZZ_CH, 2000, 8);
  ledcAttachPin(PIN_BUZZER, BUZZ_CH);
#endif
  buzzTone(0);
#endif
#if USE_EARS
  pinMode(PIN_EAR_L, OUTPUT);
  pinMode(PIN_EAR_R, OUTPUT);
  digitalWrite(PIN_EAR_L, LOW);
  digitalWrite(PIN_EAR_R, LOW);
#endif
  setupMotors();
  setupSonar();
  setupIR();
  setupNes();

  WiFi.persistent(false);
  bool sta = strlen(WIFI_STA_SSID) > 0;
  WiFi.mode(sta ? WIFI_AP_STA : WIFI_AP);
  WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASS);
  if (sta) WiFi.begin(WIFI_STA_SSID, WIFI_STA_PASS);
  Serial.printf("Robot agi: %s  sifre: %s  adres: http://%s/\n", WIFI_AP_SSID, WIFI_AP_PASS,
                WiFi.softAPIP().toString().c_str());
  if (MDNS.begin(MDNS_NAME)) MDNS.addService("http", "tcp", 80);
  setupHttp();
#if KIPIR_BLE
  setupBle();
  Serial.printf("BLE adi: %s\n", BLE_NAME);
#endif
  lastInteraction = millis();
  playSound(SND_SELAM);
}

void loop() {
  server.handleClient();
#if KIPIR_BLE
  updateBle();
#endif
  updateIR();
  updateNes();
  updateSonar();
  updateBattery();
  updateDance();
  updateMotors();
  updateSound();
  updateMood();
  updateEars();
  updateStatusLed();

  static bool staShown = false;
  if (!staShown && WiFi.status() == WL_CONNECTED) {
    staShown = true;
    Serial.printf("Ev agina baglandi: http://%s/  (ya da http://%s.local/)\n",
                  WiFi.localIP().toString().c_str(), MDNS_NAME);
  }
  delay(1);
}
