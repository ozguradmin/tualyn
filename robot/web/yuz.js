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
