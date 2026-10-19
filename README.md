# Tuana — Sayı 01

Tuana için hazırlanmış, risograf zin estetiğinde tek sayfalık bir site.
Build adımı yok: `index.html`, `style.css`, `script.js`.

## Sayfalar

1. **Kapak**: Harflere dokununca zıplıyorlar. İmleçle mavi baskı katmanı hafifçe kayıyor.
2. **Proje brief'i**: "Onaylıyorum" butonuna basınca ONAYLANDI damgası vuruluyor.
3. **Renk kartelası**: Pantone tarzı kartlar. Dokununca arkaları dönüyor.
4. **Cicikuş**: Okşanınca seviniyor, dürtülünce eziliyor, çok dürtülürse küsüyor, 16 saniye kimse ilgilenmezse uyuyor. Atıştırmalıklar sürüklenebiliyor. Mutluluk dolunca dans edip gizli mesajı söylüyor.
5. **Kupon defteri**: Kazı kazan kuponlar (canvas).
6. **Çıkartma sayfası**: Sürüklenebilir çıkartmalar. İki kez dokununca dönüyorlar; klavyede ok tuşları ve R de çalışıyor.
7. **Kalp kavanozu**: Küçük bir fizik motoru. Dokun: kalp düşer, basılı tut: döker, sürükle: sallanır. Dolunca kapağı kapanıyor.
8. **Son sayfa + künye**.

## Kişiselleştirme

- Renk kartelasındaki metinler: `script.js` içindeki `swatches` dizisi.
- Kuponlar: `script.js` içindeki `COUPONS` dizisi.
- Cicikuşun cümleleri: `script.js` içinde `say(...)` çağrıları; gizli mesaj `index.html` içinde `#secret`.
- Brief satırları ve künye: `index.html`.
- Çıkartmalar: `script.js` içindeki `STICKERS` dizisi (her biri satır içi SVG).

## Yayınlama

Cloudflare Pages'te bu repoyu bağlaman yeterli. Build komutu boş, çıktı klasörü `/`.
Yerelde denemek için: `python3 -m http.server` ve ardından http://localhost:8000.
