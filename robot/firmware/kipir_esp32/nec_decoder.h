// NEC kızılötesi protokol çözücü (kütüphanesiz). Kesme içinden her kenarda çağrılır.
// Bilgisayarda test edilebilsin diye Arduino'ya bağımlı değil: robot/firmware/test/
#pragma once
#include <stdint.h>

// Her zaman çağıran fonksiyonun (IRAM'deki kesme) içine gömülsün; ayrı bir
// IRAM_ATTR fonksiyon olursa Xtensa bağlayıcısı "literal placed after use" hatası verir.
#define NEC_INLINE inline __attribute__((always_inline))

struct NecDecoder {
  uint8_t state = 0, bits = 0;
  uint32_t data = 0;

  enum { NONE = 0, CODE = 1, REPEAT = 2 };

  // d: önceki kenardan bu yana geçen süre (µs).
  // wasMark: biten parça taşıyıcı (alıcı çıkışı LOW) idiyse true.
  // Tam kod çözülünce CODE döner ve *code'a yazar (ilk gelen bit en solda,
  // eski IRremote tablolarındaki 0x00F7C03F biçimi). Tekrar karesinde REPEAT döner.
  NEC_INLINE int edge(uint32_t d, bool wasMark, uint32_t* code) {
    // hangi durumda olursak olalım 9 ms'lik başlangıç taşıyıcısı yeni bir kare demek:
    // yarım kalmış bir kareden sonra da hemen toparlanır
    if (wasMark && d > 8000 && d < 10000) {
      state = 1;
      return NONE;
    }
    switch (state) {
      case 0:  // 9 ms başlangıç taşıyıcısı
        if (wasMark && d > 8000 && d < 10000) state = 1;
        break;
      case 1:  // 4,5 ms boşluk = yeni kod, 2,25 ms = tekrar
        if (!wasMark && d > 4000 && d < 5000) { state = 2; data = 0; bits = 0; }
        else if (!wasMark && d > 1900 && d < 2700) state = 4;
        else state = 0;
        break;
      case 2:  // bit taşıyıcısı (~562 µs)
        state = (wasMark && d > 350 && d < 800) ? 3 : 0;
        break;
      case 3:  // bit boşluğu: ~562 µs = 0, ~1687 µs = 1
        if (!wasMark && d > 350 && d < 800) { data <<= 1; bits++; }
        else if (!wasMark && d > 1350 && d < 1950) { data = (data << 1) | 1; bits++; }
        else { state = 0; break; }
        state = bits == 32 ? 5 : 2;
        break;
      case 4:  // tekrar karesinin bitiş taşıyıcısı
        state = 0;
        if (wasMark && d > 350 && d < 800) return REPEAT;
        break;
      case 5:  // kodun bitiş taşıyıcısı
        state = 0;
        if (wasMark && d > 350 && d < 800) { *code = data; return CODE; }
        break;
    }
    return NONE;
  }
};
