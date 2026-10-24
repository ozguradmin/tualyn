// Bilgisayarda NEC çözücü testi:  g++ -std=c++17 -I../kipir_esp32 nec_test.cpp -o nec_test && ./nec_test
#include <cstdio>
#include <vector>
#include "nec_decoder.h"

struct Seg { bool mark; uint32_t us; };

// Bir NEC karesinin parçaları (ilk gönderilen bit = en soldaki bit)
static std::vector<Seg> frame(uint32_t code, int jitter = 0) {
  std::vector<Seg> v{{true, 9000u + jitter}, {false, 4500u - jitter}};
  for (int i = 31; i >= 0; i--) {
    v.push_back({true, 560u + jitter});
    v.push_back({false, (code >> i) & 1 ? 1690u - jitter : 560u + jitter});
  }
  v.push_back({true, 560});
  return v;
}
static std::vector<Seg> repeatFrame() { return {{true, 9000}, {false, 2250}, {true, 560}}; }

// Alıcı çıkışında her parça bitince bir kenar olur: decoder'a (süre, parça taşıyıcı mıydı) gider.
static std::vector<std::pair<int, uint32_t>> feed(NecDecoder& n, const std::vector<Seg>& segs) {
  std::vector<std::pair<int, uint32_t>> out;
  for (auto& s : segs) {
    uint32_t c = 0;
    int r = n.edge(s.us, s.mark, &c);
    if (r) out.push_back({r, c});
  }
  return out;
}

static int fails = 0;
static void check(bool ok, const char* what) {
  printf("%s  %s\n", ok ? "GEÇTİ" : "KALDI", what);
  if (!ok) fails++;
}

int main() {
  {
    NecDecoder n;
    auto r = feed(n, {{false, 50000}});   // uzun bekleme
    auto a = feed(n, frame(0x00F7C03F));
    check(a.size() == 1 && a[0].first == NecDecoder::CODE && a[0].second == 0x00F7C03Fu, "0x00F7C03F (ON) çözülür");
  }
  {
    NecDecoder n;
    auto a = feed(n, frame(0x00F700FF, 120));   // ±120 µs sapma
    check(a.size() == 1 && a[0].second == 0x00F700FFu, "zamanlama sapmasıyla 0x00F700FF çözülür");
  }
  {
    NecDecoder n;
    feed(n, frame(0x00F720DF));
    auto a = feed(n, repeatFrame());
    check(a.size() == 1 && a[0].first == NecDecoder::REPEAT, "tekrar karesi REPEAT verir");
  }
  {
    NecDecoder n;
    auto f = frame(0x00F740BF);
    f.resize(f.size() - 10);                 // yarıda kesilen kare
    auto a = feed(n, f);
    auto b = feed(n, frame(0x00F740BF));     // ardından düzgün kare
    check(a.empty() && b.size() == 1 && b[0].second == 0x00F740BFu, "yarım kare yok sayılır, sonraki kare çözülür");
  }
  {
    NecDecoder n;
    std::vector<Seg> noise;
    for (int i = 0; i < 200; i++) noise.push_back({i % 2 == 0, 100u + (i * 37) % 3000});
    auto a = feed(n, noise);
    check(a.empty(), "rastgele gürültü kod üretmez");
  }
  printf(fails ? "\n%d test KALDI\n" : "\nTüm testler geçti\n", fails);
  return fails ? 1 : 0;
}
