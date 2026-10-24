# 3D baskı: stüdyoya ne gönderilecek?

## Dosyalar

`robot/cad/` klasöründe:

- `stl/`: 10 parça, **baskı yönünde** (tablaya oturmuş, desteksiz basılacak şekilde)
- `3mf/`: aynı parçalar, baskı profili gömülü (Bambu/Prusa kullanan stüdyolar sever)
- `kipir.scad`: parametrik kaynak (OpenSCAD). Ölçü değiştirmek için `dev_t`, `wheel_d`,
  `ball_d`, `neck_h`, `tilt` gibi değişkenler en üstte.
- `img/`: parça ve montaj görselleri

| Dosya | Adet | Boyut (mm) | ~Gram | Not |
|---|---:|---|---:|---|
| `kipir_taban.stl` | 1 | 190 × 172 × 42 | 103 | Motor duvarları ve misket direkleri dahil; ters (üst yüzü tablada) basılır |
| `kipir_ust_kat.stl` | 1 | 180 × 180 × 62 | 89 | 4 direk dahil; ters basılır |
| `kipir_boyun.stl` | 1 | 34 × 44 × 61 | 24 | |
| `kipir_kafa_ray.stl` | 1 | 200 × 32 × 5 | 21 | |
| `kipir_cene_sol.stl` / `_sag` | 1 + 1 | 20 × 29 × 84 | 16 + 16 | Ayna simetrik, ikisi de lazım |
| `kipir_teker_kapak.stl` | **2** | 25 × 42 × 5 | 3 | |
| `kipir_sensor_tutucu.stl` | 1 | 32 × 50 × 12 | 6 | |
| `kipir_kulak_sol.stl` / `_sag` | 1 + 1 | 23 × 19 × 54 | 4 + 4 | İsteğe bağlı; beyaz ya da şeffaf PETG; 5 mm brim |

**Toplam ~281 g** (kulaklarla 288 g), klasik bir yazıcıda ~22 saat; Bambu sınıfı
yazıcılarda bunun yarısından az.

## Önerilen ayarlar

- **Malzeme:** PETG (sağlam, ısıya daha dayanıklı). PLA+ da olur.
- 0,4 mm nozül, **0,2 mm katman, 3 duvar, %20 gyroid dolgu**
- Destek **gerekmez**. Parçalar 45° kuralına göre tasarlandı; dilimleyici uyarı vermiyor.
- En büyük parça 190 mm; **220 × 220 tablalı her yazıcıya sığar.** Bambu A1 mini'ye
  (180 mm) taban ve üst kat sığmaz.
- Vida delikleri M3 için (Ø3,4 geçiş, Ø2,7 kılavuz). Vidalar plastiğe kendi yolunu açar; ayrıca
  insert gerekmez.

## Önce prova bas (kendi yazıcın ya da ucuz bir prova)

Tablet ya da telefonunun gerçekten oturduğunu görmek için önce `kafa_ray` ile iki `cene`
parçasını hızlı ayarla (0,28 mm katman, 2 duvar, %10 dolgu) bastırıp dene. Sonra hepsini
asıl ayarla bastır.

## Stüdyoya gönderilecek mesaj (kopyala-yapıştır)

> Merhaba, ekteki robot gövdesi parçaları için fiyat almak istiyorum.
>
> - **Dosyalar:** 10 adet STL (aynısı 3MF olarak da ekte). Parçalar baskı yönünde
>   kaydedildi, destek gerekmiyor.
> - **Adetler:** `kipir_teker_kapak` 2 adet, diğerleri 1'er adet.
>   (`kipir_kulak_sol/sag` isteğe bağlı; beyaz ya da şeffaf olabilir.)
> - **Malzeme:** PETG (yoksa PLA+). Renk: ……
> - **Ayarlar:** 0,2 mm katman, 3 duvar, %20 gyroid dolgu.
> - **Boyut:** en büyük parça 190 × 172 × 42 mm, 220 × 220 tablaya sığıyor.
> - Dilimleyici tahmini toplam ~281 g (kulaklarla ~288 g).
>
> Gram ya da saat başı fiyatınızı, toplam tutarı, teslim süresini ve kargo ücretini
> iletebilir misiniz? Teşekkürler.

## Nereye sorulur?

Türk stüdyoları fiyatı dosyayı görünce veriyor; **en az 3 yerden teklif al**. Araştırmada
bulunanlar (iletişim bilgileri sitelerinde):

- [Armut 3D baskı](https://armut.com/3d-baski): tek talep, 4 teklife kadar. 2026 ortalaması
  iş başına 500-2.000 TL (İstanbul), 600-1.500 TL (Ankara).
- [3D Baskı Servisi / Mekatrolab](https://www.3dbaskiservisi.com/) (İstanbul, FDM/SLA/MJF)
- [3D Baskı Ankara](https://www.3dbaskiankara.com/) (Kızılay; 220 × 220 × 250 tabla)
- [3dbaski.com.tr](https://www.3dbaski.com.tr/) (Kayseri)
- [3D Lab](https://3dlab.com.tr/) (dosya yükle, fiyat al)
- Porima ve Zaxe'nin baskı hizmeti sayfaları

**Beklenen fiyat:** yerelde ~3-6 TL/g → bu set için **~1.000-2.000 TL** + kargo.
JLC3DP gibi Çin servisleri kargo ve Şubat 2026'dan beri her pakete uygulanan gümrük vergisiyle
~3.000-7.000 TL'ye çıkıyor. Bu yüzden gövde için yerel stüdyo daha iyi.

## Ölçüleri kendi parçalarına göre değiştirmek

OpenSCAD'i kur, `kipir.scad`'ı aç, en üstteki değerleri değiştir, sonra:

```bash
cd robot/cad
./build.sh          # STL + 3MF + görseller
python3 estimate.py # gram/süre tahmini (PrusaSlicer gerekir)
```

Sık değişenler:

| Değişken | Varsayılan | Ne zaman değiştirilir |
|---|---|---|
| `dev_t` | 12 | Telefonun kılıfla 11,5 mm'den kalınsa |
| `wheel_d`, `wheel_w` | 66, 27 | Farklı teker alırsan |
| `ball_d` | 16 | Misket yerine 19 mm (3/4") çelik bilye kullanırsan |
| `pillar_h` | 58 | İki kat arasına sığması gereken şeyler (powerbank + kablolar) 50 mm'yi geçerse |
| `neck_h`, `tilt` | 45, 8 | Kafa daha yüksek ya da daha dik olsun istersen |
