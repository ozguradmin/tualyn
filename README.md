# Tuana — Sayı 01

Tuana için hazırlanmış, risograf zin estetiğinde tek sayfalık bir site.
Build adımı yok: `index.html`, `style.css`, `script.js`.

## Sayfalar

1. **Kapak**: Harflere dokununca zıplıyorlar. İmleçle mavi baskı katmanı hafifçe kayıyor.
2. **Proje brief'i**: "onaylıyorum" butonuna basınca ONAYLANDI damgası vuruluyor.
3. **Renk kartelası**: Pantone tarzı kartlar. Dokununca arkaları dönüyor.
4. **Cicikuşlar**: İki muhabbet kuşu (biri fiyonklu). Okşanınca seviniyorlar, dürtülünce eziliyorlar, çok dürtülünce küsüyorlar, biri sevilince öbürü kıskanıyor, 16 saniye kimse ilgilenmezse uyuyorlar. Atıştırmalıklar sürüklenebiliyor. Mutluluk dolunca dans edip T.C. kimliği çıkarıyorlar.
5. **Parolla (parol değil)**: 16 harf + 1 bonus ("?") soruluk, Tuana'ya özel soru çemberi. Doğru, yanlış ve pas; paslananlar turun sonunda geri geliyor.
6. **Kupon defteri**: Kazı kazan kuponlar (canvas).
7. **Çıkartma sayfası**: Sürüklenebilir çıkartmalar. İki kez dokununca dönüyorlar; klavyede ok tuşları ve R de çalışıyor.
8. **Kalp kavanozu**: Küçük bir fizik motoru. Dokun: kalp düşer, basılı tut: döker, sürükle: sallanır. Dolunca kapağı kapanıyor.
9. **Son sayfa + künye**.

## Kişiselleştirme

- Renk kartelasındaki metinler: `script.js` içindeki `swatches` dizisi.
- Kuponlar: `script.js` içindeki `COUPONS` dizisi.
- Parolla soruları: `script.js` içindeki `PZ` dizisi (`[harf, ipucu, [kabul edilen cevaplar], isteğe bağlı ipucu satırı]`). Cevaplar büyük/küçük harf ve Türkçe karakter farkına bakılmadan kontrol ediliyor.
- Cicikuşların cümleleri: `script.js` içinde `say(...)` çağrıları; gizli mesaj `index.html` içinde `#secret`.
- Brief satırları ve künye: `index.html`.
- Çıkartmalar: `script.js` içindeki `STICKERS` dizisi (her biri satır içi SVG).

## Yayınlama

Cloudflare Pages'te bu repoyu bağlaman yeterli. Build komutu boş, çıktı klasörü `/`.
Yerelde denemek için: `python3 -m http.server` ve ardından http://localhost:8000.
