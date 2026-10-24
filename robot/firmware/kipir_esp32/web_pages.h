// OTOMATİK ÜRETİLDİ: robot/web/gom.py. Elle düzenleme; web/ altındaki dosyaları değiştir.
#pragma once
#include <pgmspace.h>

const char PAGE_KUMANDA[] PROGMEM = R"KIPIR(<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>Kıpır kumanda</title>
<style>
  * { box-sizing: border-box; -webkit-tap-highlight-color: rgba(0,0,0,0); }
  html, body { margin: 0; background: #0b0e13; color: #e6ebf2; font: 15px sans-serif; }
  .ust { display: -webkit-box; display: flex; -webkit-box-align: center; align-items: center;
         padding: 10px 14px; background: #121823; border-bottom: 1px solid #1f2836; }
  .ust b { font-size: 18px; margin-right: 10px; }
  .nokta { width: 10px; height: 10px; border-radius: 5px; background: #e5484d; display: inline-block; margin-right: 8px; }
  .nokta.ok { background: #2fbf71; }
  #bilgi { color: #9aa7b8; font-size: 13px; }
  .alan { padding: 12px 14px; max-width: 560px; margin: 0 auto; }
  #pad { position: relative; width: 260px; height: 260px; margin: 6px auto 4px; border-radius: 130px;
         background: #141b26; border: 2px solid #233042; touch-action: none; }
  #pad:before, #pad:after { content: ""; position: absolute; background: #1f2836; }
  #pad:before { left: 50%; top: 18px; bottom: 18px; width: 2px; margin-left: -1px; }
  #pad:after { top: 50%; left: 18px; right: 18px; height: 2px; margin-top: -1px; }
  #topuz { position: absolute; left: 50%; top: 50%; width: 92px; height: 92px; margin: -46px 0 0 -46px;
           border-radius: 46px; background: #3fe0ff; z-index: 2; box-shadow: 0 4px 14px rgba(0,0,0,.5); }
  .satir { display: -webkit-box; display: flex; -webkit-box-pack: center; justify-content: center;
           flex-wrap: wrap; margin: 8px 0; }
  button { border: 0; border-radius: 8px; padding: 11px 12px; margin: 4px; font: 15px sans-serif;
           color: #0b0e13; background: #cfd6e0; min-width: 72px; }
  button.dur { background: #e5484d; color: #fff; font-weight: bold; min-width: 150px; font-size: 18px; }
  button.renk { min-width: 44px; height: 40px; }
  h3 { font-size: 13px; letter-spacing: .08em; text-transform: uppercase; color: #7f8da0; margin: 18px 0 6px; }
  .hiz { text-align: center; color: #9aa7b8; }
  .hiz input { width: 220px; vertical-align: middle; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  td { padding: 6px 4px; border-bottom: 1px solid #1a2230; }
  td.kod { font-family: monospace; color: #9aa7b8; }
  #ogrenMesaj { color: #ffd166; min-height: 20px; text-align: center; }
  a { color: #3fe0ff; }
  .alt { text-align: center; padding: 8px 0 24px; color: #7f8da0; font-size: 13px; }
</style>
</head>
<body>
<div class="ust"><span class="nokta" id="nokta"></span><b>Kıpır</b><span id="bilgi">bağlanıyor…</span></div>
<div class="alan">
  <div id="pad"><div id="topuz"></div></div>
  <div class="hiz">Hız <input type="range" id="hiz" min="30" max="100" value="70"> <span id="hizYaz">70</span>%</div>
  <div class="satir"><button class="dur" id="durBtn">DUR</button></div>

  <h3>Ruh hâli</h3>
  <div class="satir" id="modlar"></div>

  <h3>Hareket ve ses</h3>
  <div class="satir">
    <button data-k="ses selam">Selam</button>
    <button data-k="dans">Dans</button>
    <button data-k="ses bip">Bip</button>
    <button data-k="uyu">Uyu</button>
    <button data-k="uyan">Uyan</button>
  </div>

  <h3>Kulak rengi</h3>
  <div class="satir" id="renkler"></div>

  <h3>Gece lambası kumandasını öğret</h3>
  <div id="ogrenMesaj"></div>
  <div class="hiz" style="font-size:13px">Son okunan kod: <span id="irSon" style="font-family:monospace">–</span></div>
  <table id="irTablo"></table>
  <div class="satir"><button id="irSifir">Varsayılana dön</button></div>

  <div class="alt">Bu cihazı robotun yüzü yapmak için: <a href="/yuz">/yuz</a></div>
</div>
<script>
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var son = null, bekleyen = 0;

  function iste(yol, cb, oncelikli) {
    if (bekleyen > 2 && !oncelikli) return;   // ağ yavaşsa kuyruk biriktirme (dur hariç)
    bekleyen++;
    var x = new XMLHttpRequest(), bitti = false;
    var zaman = setTimeout(function () { if (!bitti) { bitti = true; bekleyen--; x.abort(); cevrimdisi(); } }, 1500);
    x.onreadystatechange = function () {
      if (x.readyState !== 4 || bitti) return;
      bitti = true; clearTimeout(zaman); bekleyen--;
      if (x.status === 200) {
        var d = null;
        try { d = JSON.parse(x.responseText); } catch (e) {}
        if (d && d.m !== undefined) goster(d);
        if (cb) cb(d);
      } else if (x.status === 0) { cevrimdisi(); }
    };
    x.open('GET', yol + (yol.indexOf('?') < 0 ? '?' : '&') + '_=' + new Date().getTime(), true);
    x.send();
  }
  function komut(k, cb) { iste('/k?c=' + encodeURIComponent(k), cb, k === 'dur'); }
  function dur() {   // birkaç kez gönder: yolda kalmış bir sürüş komutundan sonra da ulaşsın
    iste('/dur', null, true);
    setTimeout(function () { iste('/dur', null, true); }, 150);
    setTimeout(function () { iste('/dur', null, true); }, 700);
  }

  function cevrimdisi() { $('nokta').className = 'nokta'; $('bilgi').innerHTML = 'robota ulaşılamıyor (Kipir ağına bağlı mısın?)'; }

  var MOD_ADLARI = { mutlu: 'Mutlu', saskin: 'Şaşkın', uykulu: 'Uykulu', kizgin: 'Kızgın', sevgi: 'Sevgi', merak: 'Merak', uzgun: 'Üzgün' };
  var ogrenilen = '', ogrenGoruldu = false;
  function goster(d) {
    son = d;
    $('nokta').className = 'nokta ok';
    var mesafe = d.d > 0 ? d.d + ' cm' : '–';
    $('bilgi').innerHTML = (MOD_ADLARI[d.m] || d.m) + ' · önü: ' + mesafe + (d.b ? ' · <b style="color:#ffd166">engel!</b>' : '') +
      (d.v > 0 ? ' · pil ' + d.v.toFixed(1) + ' V' : '') + (d.ble ? ' · telefon beyni bağlı' : '');
    if (d.ir && d.ir !== '00000000') $('irSon').innerHTML = d.ir;
    if (d.ogren) {
      ogrenGoruldu = true;
      $('ogrenMesaj').innerHTML = 'Şimdi kumandada "' + (ogrenilen || d.ogren) + '" için kullanmak istediğin tuşa bas…';
    } else if (ogrenGoruldu) {
      ogrenGoruldu = false;
      $('ogrenMesaj').innerHTML = (ogrenilen ? '"' + ogrenilen + '" ' : '') + 'öğrenildi ✓ (son kod: ' + d.ir + ')';
      ogrenilen = '';
      irListe();
    }
  }

  // ---- joystick ----
  var pad = $('pad'), topuz = $('topuz'), aktif = false, jx = 0, jy = 0, dokunId = null;
  function konum(ex, ey) {
    var r = pad.getBoundingClientRect();
    var cx = r.left + r.width / 2, cy = r.top + r.height / 2, R = r.width / 2 - 30;
    var dx = ex - cx, dy = ey - cy, l = Math.sqrt(dx * dx + dy * dy);
    if (l > R) { dx = dx / l * R; dy = dy / l * R; }
    topuz.style.webkitTransform = topuz.style.transform = 'translate(' + dx + 'px,' + dy + 'px)';
    jx = dx / R; jy = -dy / R;
  }
  function birak() {
    aktif = false; dokunId = null; jx = jy = 0;
    topuz.style.webkitTransform = topuz.style.transform = 'translate(0,0)';
    dur();
  }
  pad.addEventListener('touchstart', function (e) {
    e.preventDefault();
    var t = e.changedTouches[0]; dokunId = t.identifier; aktif = true; konum(t.clientX, t.clientY);
  }, false);
  pad.addEventListener('touchmove', function (e) {
    e.preventDefault();
    for (var i = 0; i < e.changedTouches.length; i++)
      if (e.changedTouches[i].identifier === dokunId) konum(e.changedTouches[i].clientX, e.changedTouches[i].clientY);
  }, false);
  pad.addEventListener('touchend', function (e) { e.preventDefault(); birak(); }, false);
  pad.addEventListener('touchcancel', function (e) { e.preventDefault(); birak(); }, false);
  pad.addEventListener('mousedown', function (e) { aktif = true; konum(e.clientX, e.clientY); }, false);
  document.addEventListener('mousemove', function (e) { if (aktif && dokunId === null) konum(e.clientX, e.clientY); }, false);
  document.addEventListener('mouseup', function () { if (aktif && dokunId === null) birak(); }, false);

  setInterval(function () {
    if (!aktif) return;
    var h = +$('hiz').value;
    iste('/surus?x=' + Math.round(jx * h) + '&y=' + Math.round(jy * h));
  }, 100);
  setInterval(function () { if (!aktif) iste('/durum'); }, 700);

  $('hiz').onchange = $('hiz').oninput = function () { $('hizYaz').innerHTML = this.value; };
  $('durBtn').onclick = dur;

  // ---- modlar, sesler ----
  var modlar = $('modlar');
  for (var m in MOD_ADLARI) {
    var b = document.createElement('button');
    b.innerHTML = MOD_ADLARI[m];
    b.setAttribute('data-k', 'mod ' + m);
    modlar.appendChild(b);
  }
  var dugmeler = document.querySelectorAll('button[data-k]');
  for (var i = 0; i < dugmeler.length; i++)
    dugmeler[i].onclick = function () { komut(this.getAttribute('data-k')); };

  var RENKLER = [['oto', '#3a4556', 'oto'], ['255 170 0', '#ffaa00'], ['255 0 0', '#ff2a2a'], ['0 255 80', '#00ff50'],
                 ['0 120 255', '#0078ff'], ['255 30 120', '#ff1e78'], ['255 255 255', '#ffffff'], ['0 0 0', '#000000', 'kapalı']];
  for (i = 0; i < RENKLER.length; i++) {
    var r = document.createElement('button');
    r.className = 'renk';
    r.style.background = RENKLER[i][1];
    r.style.color = '#e6ebf2';
    r.innerHTML = RENKLER[i][2] || '';
    r.setAttribute('data-r', RENKLER[i][0]);
    r.onclick = function () { komut('kulak ' + this.getAttribute('data-r')); };
    $('renkler').appendChild(r);
  }

  // ---- IR öğretme ----
  var EYLEM_ADLARI = { ileri: 'İleri', geri: 'Geri', sol: 'Sola dön', sag: 'Sağa dön', dur: 'Dur', selam: 'Selam', dans: 'Dans', uyku: 'Uyu' };
  function irListe() {
    iste('/ir_liste', function (d) {
      if (!d) return;
      var h = '';
      for (var a in EYLEM_ADLARI)
        h += '<tr><td>' + EYLEM_ADLARI[a] + '</td><td class="kod">' + (d[a] || '') + '</td><td style="text-align:right"><button data-a="' + a + '">Öğret</button></td></tr>';
      $('irTablo').innerHTML = h;
      var bs = $('irTablo').getElementsByTagName('button');
      for (var j = 0; j < bs.length; j++)
        bs[j].onclick = function () {
          ogrenilen = EYLEM_ADLARI[this.getAttribute('data-a')];
          iste('/ir_ogren?a=' + this.getAttribute('data-a'));
        };
    });
  }
  $('irSifir').onclick = function () { iste('/ir_sifirla', irListe); };
  irListe();
})();
</script>
</body>
</html>
)KIPIR";

const char PAGE_YUZ[] PROGMEM = R"KIPIR(<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Kıpır yüzü</title>
<style>
  html, body { margin: 0; padding: 0; height: 100%; background: #05070a; overflow: hidden; }
  #c { display: block; width: 100%; height: 100%; }
  #menu { position: absolute; left: 0; right: 0; bottom: 0; padding: 12px; text-align: center;
          font: 16px sans-serif; color: #cfd6e0; background: rgba(0,0,0,0.75); display: none; }
  #menu a, #menu button { color: #05070a; background: #3fe0ff; border: 0; border-radius: 6px;
          padding: 10px 14px; margin: 4px; font: 16px sans-serif; text-decoration: none; display: inline-block; }
</style>
</head>
<body>
<canvas id="c"></canvas>
<div id="menu">
  <button id="tam">Tam ekran</button>
  <a href="/">Kumanda</a>
  <div style="margin-top:8px;font-size:13px">İpucu: tablet şarjdayken açık kalsın diye Ayarlar &gt; Geliştirici seçenekleri &gt; "Uyanık kal".</div>
</div>
<script>
/* Kıpır yüzü: tuvale (canvas) iki büyük göz çizer.
 * Bilerek ES5 yazıldı: Galaxy Tab 3 Lite gibi Android 4.2 tarayıcılarında da çalışır.
 * Kullanım:
 *   var yuz = new KipirYuz(document.getElementById('c'));
 *   yuz.durum({ m: 'mutlu', lx: 0, ly: 0, t: 0 });   // m: mod, lx/ly: bakış, t: konuşuyor mu
 *   yuz.baslat();
 */
(function (g) {
  var raf = g.requestAnimationFrame || g.webkitRequestAnimationFrame ||
    function (cb) { return g.setTimeout(function () { cb(new Date().getTime()); }, 40); };

  // her mod için hedef değerler; çizim bu değerlere yumuşakça kayar
  var MODLAR = {
    mutlu:  { renk: [63, 224, 255], acik: 1.0, gulus: 0.5, kapak: 0, egim: 0, boy: 1.0 },
    saskin: { renk: [255, 255, 255], acik: 1.22, gulus: 0, kapak: 0, egim: 0, boy: 1.15, yuvarlak: 1 },
    uykulu: { renk: [74, 125, 255], acik: 0.12, gulus: 0, kapak: 0, egim: 0, boy: 1.0 },
    kizgin: { renk: [255, 74, 61], acik: 0.85, gulus: 0, kapak: 0.3, egim: 1, boy: 1.0 },
    sevgi:  { renk: [255, 79, 154], acik: 1.0, gulus: 0, kapak: 0, egim: 0, boy: 1.0, kalp: 1 },
    merak:  { renk: [63, 224, 255], acik: 1.0, gulus: 0, kapak: 0.22, egim: -0.4, boy: 1.0, asim: 1 },
    uzgun:  { renk: [111, 140, 255], acik: 0.8, gulus: 0, kapak: 0.38, egim: -1, boy: 0.95 }
  };
  var SAYILAR = ['acik', 'gulus', 'kapak', 'egim', 'boy', 'yuvarlak', 'kalp', 'asim'];

  function simdi() { return new Date().getTime(); }
  function yaklas(a, b, k) { return a + (b - a) * k; }

  function KipirYuz(tuval, ayar) {
    ayar = ayar || {};
    this.c = tuval;
    this.x = tuval.getContext('2d');
    this.arka = ayar.arka || '#05070a';
    this.fpsAralik = ayar.fps ? 1000 / ayar.fps : 50;  // eski cihazlar için 20 fps
    this.hedef = { m: 'mutlu', lx: 0, ly: 0, t: 0 };
    this.p = {};
    var m = MODLAR.mutlu, i;
    for (i = 0; i < SAYILAR.length; i++) this.p[SAYILAR[i]] = m[SAYILAR[i]] || 0;
    this.renk = m.renk.slice(0);
    this.bakX = 0; this.bakY = 0;
    this.gezX = 0; this.gezY = 0; this.sonrakiGez = simdi() + 1500;
    this.kirp = 0; this.sonrakiKirp = simdi() + 2500;
    this.agiz = 0;
    this.son = 0;
    this.cevrimici = true;
    this.durumNoktasi = !!ayar.durumNoktasi;
    var self = this;
    this.boyutla();
    g.addEventListener('resize', function () { self.boyutla(); });
  }

  KipirYuz.prototype.boyutla = function () {
    var dpr = Math.min(g.devicePixelRatio || 1, 2);
    var w = this.c.clientWidth || g.innerWidth, h = this.c.clientHeight || g.innerHeight;
    this.c.width = Math.round(w * dpr);
    this.c.height = Math.round(h * dpr);
  };

  KipirYuz.prototype.durum = function (d) {
    if (!d) return;
    if (d.m && MODLAR[d.m]) this.hedef.m = d.m;
    this.hedef.lx = +d.lx || 0;
    this.hedef.ly = +d.ly || 0;
    this.hedef.t = +d.t || 0;
  };

  KipirYuz.prototype.baglanti = function (var_mi) { this.cevrimici = var_mi; };

  KipirYuz.prototype.baslat = function () {
    var self = this;
    function dongu() {
      var t = simdi();
      if (t - self.son >= self.fpsAralik) { self.son = t; self.ciz(t); }
      raf(dongu);
    }
    raf(dongu);
  };

  KipirYuz.prototype.guncelle = function (t) {
    var hedef = MODLAR[this.hedef.m] || MODLAR.mutlu, i, k = 0.2;
    for (i = 0; i < SAYILAR.length; i++) {
      var ad = SAYILAR[i];
      this.p[ad] = yaklas(this.p[ad], hedef[ad] || 0, k);
    }
    for (i = 0; i < 3; i++) this.renk[i] = yaklas(this.renk[i], hedef.renk[i], k);

    // kendi kendine etrafa bakınma (dışarıdan bakış gelmiyorsa)
    if (t > this.sonrakiGez) {
      this.gezX = (Math.random() * 2 - 1) * 0.6;
      this.gezY = (Math.random() * 2 - 1) * 0.35;
      if (Math.random() < 0.35) { this.gezX = 0; this.gezY = 0; }
      this.sonrakiGez = t + 1200 + Math.random() * 2800;
    }
    var disari = Math.abs(this.hedef.lx) + Math.abs(this.hedef.ly) > 0.01;
    this.bakX = yaklas(this.bakX, disari ? this.hedef.lx : this.gezX, 0.25);
    this.bakY = yaklas(this.bakY, disari ? this.hedef.ly : this.gezY, 0.25);

    // göz kırpma
    if (t > this.sonrakiKirp) {
      this.kirpBas = t;
      this.sonrakiKirp = t + 2200 + Math.random() * 4000;
      if (Math.random() < 0.2) this.sonrakiKirp = t + 260;  // bazen çift kırpar
    }
    var kp = this.kirpBas ? (t - this.kirpBas) / 160 : 2;
    this.kirp = kp < 1 ? Math.sin(kp * Math.PI) : 0;

    // konuşurken ağız
    var agizHedef = this.hedef.t ? 0.35 + 0.65 * Math.abs(Math.sin(t / 95) * Math.sin(t / 37)) : 0;
    this.agiz = yaklas(this.agiz, agizHedef, 0.45);
  };

  function yuvarlakDikdortgen(x, cx, cy, w, h, r) {
    var x0 = cx - w / 2, y0 = cy - h / 2;
    r = Math.max(0, Math.min(r, w / 2, h / 2));
    x.beginPath();
    x.moveTo(x0 + r, y0);
    x.lineTo(x0 + w - r, y0);
    x.arcTo(x0 + w, y0, x0 + w, y0 + r, r);
    x.lineTo(x0 + w, y0 + h - r);
    x.arcTo(x0 + w, y0 + h, x0 + w - r, y0 + h, r);
    x.lineTo(x0 + r, y0 + h);
    x.arcTo(x0, y0 + h, x0, y0 + h - r, r);
    x.lineTo(x0, y0 + r);
    x.arcTo(x0, y0, x0 + r, y0, r);
    x.closePath();
  }

  function kalp(x, cx, cy, s) {
    x.beginPath();
    x.moveTo(cx, cy + s * 0.35);
    x.bezierCurveTo(cx - s * 0.9, cy - s * 0.25, cx - s * 0.45, cy - s * 0.95, cx, cy - s * 0.45);
    x.bezierCurveTo(cx + s * 0.45, cy - s * 0.95, cx + s * 0.9, cy - s * 0.25, cx, cy + s * 0.35);
    x.closePath();
  }

  KipirYuz.prototype.goz = function (cx, cy, w, h, yon, t) {
    var x = this.x, p = this.p, arka = this.arka;
    var renk = 'rgb(' + Math.round(this.renk[0]) + ',' + Math.round(this.renk[1]) + ',' + Math.round(this.renk[2]) + ')';
    var kalpOrani = p.kalp;

    if (kalpOrani > 0.5) {
      var nabiz = 1 + 0.08 * Math.sin(t / 140);
      x.fillStyle = renk;
      kalp(x, cx, cy + h * 0.05, w * 0.95 * nabiz);
      x.fill();
      return;
    }

    var r = Math.min(w, h) * (0.28 + 0.22 * p.yuvarlak);
    x.fillStyle = renk;
    yuvarlakDikdortgen(x, cx, cy, w, Math.max(h, 2), r);
    x.fill();

    var ust = cy - h / 2;
    // gülen göz: alttan arka plan rengiyle hilal oy
    if (p.gulus > 0.02) {
      x.fillStyle = arka;
      x.beginPath();
      if (x.ellipse) {
        x.ellipse(cx, cy + h * 0.78, w * 0.8, h * 0.62 * Math.min(1, p.gulus * 1.6), 0, 0, Math.PI * 2);
      } else {
        x.save();
        x.translate(cx, cy + h * 0.78);
        x.scale(1, (h * 0.62 * Math.min(1, p.gulus * 1.6)) / (w * 0.8));
        x.arc(0, 0, w * 0.8, 0, Math.PI * 2);
        x.restore();
      }
      x.fill();
    }
    // göz kapağı: eğimli (kızgın / üzgün / meraklı)
    if (p.kapak > 0.02) {
      var ic = cx - yon * w / 2, dis = cx + yon * w / 2;   // yon: sol göz -1 (iç kenarı sağda)
      var icH = h * p.kapak * (1 + 0.9 * p.egim), disH = h * p.kapak * (1 - 0.9 * p.egim);
      x.fillStyle = arka;
      x.beginPath();
      x.moveTo(dis + yon * 4, ust - 4);
      x.lineTo(ic - yon * 4, ust - 4);
      x.lineTo(ic - yon * 4, ust + Math.max(0, icH));
      x.lineTo(dis + yon * 4, ust + Math.max(0, disH));
      x.closePath();
      x.fill();
    }
  };

  KipirYuz.prototype.ciz = function (t) {
    this.guncelle(t);
    var x = this.x, W = this.c.width, H = this.c.height, p = this.p;
    x.fillStyle = this.arka;
    x.fillRect(0, 0, W, H);

    var birim = Math.min(W, H * 1.6);
    var gw = birim * 0.2 * p.boy, gh = birim * 0.25 * p.boy * p.acik * (1 - 0.92 * this.kirp);
    var ara = birim * 0.21;
    var cx = W / 2 + this.bakX * birim * 0.07, cy = H * 0.46 + this.bakY * H * 0.08;
    var sag = p.asim > 0.5 ? 1.15 : 1;

    this.goz(cx - ara, cy, gw, gh, -1, t);
    this.goz(cx + ara, cy, gw * sag, gh * sag, 1, t);

    if (this.agiz > 0.02) {
      x.fillStyle = 'rgb(' + Math.round(this.renk[0]) + ',' + Math.round(this.renk[1]) + ',' + Math.round(this.renk[2]) + ')';
      yuvarlakDikdortgen(x, cx, cy + gh * 0.5 + birim * 0.14, birim * 0.12, birim * 0.012 + birim * 0.07 * this.agiz, birim * 0.03);
      x.fill();
    }

    if (this.hedef.m === 'uykulu') {  // zZ
      x.fillStyle = 'rgba(120,150,255,0.8)';
      var z = (t / 1200) % 1;
      x.font = Math.round(birim * (0.05 + 0.04 * z)) + 'px sans-serif';
      x.fillText('z', cx + ara + gw * 0.7 + z * birim * 0.08, cy - gh - z * birim * 0.18);
      x.font = Math.round(birim * 0.07) + 'px sans-serif';
      x.fillText('Z', cx + ara + gw * 0.9 + z * birim * 0.04, cy - gh - birim * 0.14 - z * birim * 0.1);
    }

    if (this.durumNoktasi) {
      x.fillStyle = this.cevrimici ? '#2fbf71' : '#e5484d';
      x.beginPath();
      x.arc(W - 14, 14, 5, 0, Math.PI * 2);
      x.fill();
    }
  };

  KipirYuz.MODLAR = MODLAR;
  g.KipirYuz = KipirYuz;
})(this);
</script>
<script>
(function () {
  var yuz = new KipirYuz(document.getElementById('c'), { durumNoktasi: true, fps: 20 });
  yuz.baslat();

  var bekliyor = false, hata = 0;
  function sor() {
    if (bekliyor) return;
    bekliyor = true;
    var x = new XMLHttpRequest(), bitti = false;
    var zaman = setTimeout(function () { if (!bitti) { bitti = true; x.abort(); bekliyor = false; hata++; yuz.baglanti(hata < 3); } }, 1200);
    x.onreadystatechange = function () {
      if (x.readyState !== 4 || bitti) return;
      bitti = true; clearTimeout(zaman); bekliyor = false;
      if (x.status === 200) {
        try { yuz.durum(JSON.parse(x.responseText)); hata = 0; yuz.baglanti(true); } catch (e) { hata++; }
      } else { hata++; yuz.baglanti(hata < 3); }
    };
    x.open('GET', '/durum?_=' + new Date().getTime(), true);
    x.send();
  }
  setInterval(sor, 150);

  var menu = document.getElementById('menu'), gizle;
  document.getElementById('c').onclick = function () {
    menu.style.display = 'block';
    clearTimeout(gizle);
    gizle = setTimeout(function () { menu.style.display = 'none'; }, 5000);
  };
  document.getElementById('tam').onclick = function () {
    var e = document.documentElement;
    var f = e.requestFullscreen || e.webkitRequestFullscreen || e.webkitRequestFullScreen;
    if (f) f.call(e);
    menu.style.display = 'none';
  };
})();
</script>
</body>
</html>
)KIPIR";
