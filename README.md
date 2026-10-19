# Tuana — Sayı 01

Tuana için hazırlanmış, risograf zin estetiğinde tek sayfalık bir site.
Build adımı yok: `index.html`, `style.css`, `script.js`.

## Sayfalar

1. **Kapak**: pembe mürekkep, mavi tram gölge, sarı tram kalp. İmleçle mavi katman hafifçe kayıyor.
2. **Proje brief'i**: "Onaylıyorum" butonuna basınca ONAYLANDI damgası vuruluyor.
3. **Tuana renk sistemi**: Pantone tarzı kartela. Kartlara dokununca arkası dönüyor.
4. **Yazı karakteri örneği**: Fraunces değişken fontu, "Sevgi" (ağırlık) ve "Yumuşaklık" (SOFT) eksenleri. Yazının üstüne tıklanıp değiştirilebiliyor.
5. **Çıkartma sayfası**: Sürüklenebilir çıkartmalar. İki kez dokununca dönüyorlar, klavyede ok tuşları ve R tuşu da çalışıyor.
6. **Son sayfa + künye**.

## Kişiselleştirme

- Renk kartelasındaki metinler: `script.js` içindeki `swatches` dizisi.
- Brief satırları ve künye: `index.html`.
- Çıkartmalar: `script.js` içindeki `STICKERS` dizisi (her biri satır içi SVG).

## Yayınlama

Cloudflare Pages'te bu repoyu bağlaman yeterli. Build komutu boş, çıktı klasörü `/`.
Yerelde denemek için: `python3 -m http.server` ve ardından http://localhost:8000.
