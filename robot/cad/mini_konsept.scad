// Kıpır Mini seçenekleri: TEMSİLİ boyut karşılaştırması (baskı dosyası değildir).
// Ölçüler: Sesame STL'lerinden (gövde 79×68 mm), Otto (~12 cm boy) ve
// StackChan (CoreS3 54×54 mm kafa) ölçülerinden kabaca alındı. Yanda telefon ölçek için.
// Kullanım: openscad -o mini.png --imgsize=1800,900 mini_konsept.scad
$fn = 32;

KREM = [0.95, 0.93, 0.88];
GRI = [0.55, 0.56, 0.58];
EKRAN = [0.08, 0.09, 0.11];
GOZ = [0.85, 0.95, 1.0];

module yuvarlak_kutu(s, r = 4) {
    hull() for (x = [r, s[0] - r], y = [r, s[1] - r], z = [r, s[2] - r])
        translate([x, y, z]) sphere(r);
}

// ekran + iki göz; ön yüzü -y yönüne bakar, merkezi (0,0,0)
module yuz(w, h, goz = 0.18) {
    color(EKRAN) translate([-w / 2, -1, -h / 2]) cube([w, 1.2, h]);
    color(GOZ) for (sx = [-1, 1])
        translate([sx * w * 0.22, -1.3, h * 0.05]) rotate([90, 0, 0]) cylinder(d = h * goz * 2, h = 0.4);
}

module telefon() {
    color([0.2, 0.21, 0.24]) translate([-37.5, -4, 0]) yuvarlak_kutu([75, 8, 160], 6);
    color([0.12, 0.3, 0.5]) translate([-34, -4.3, 8]) cube([68, 0.5, 144]);
}

// 1) Sesame tabanlı dört bacak: gövde 79×68, 8 servo
module sesame(renk) {
    z0 = 34;
    color(KREM) translate([-39.5, -34, z0]) yuvarlak_kutu([79, 68, 26], 6);
    color(renk) translate([-39.5, -30, z0 + 22]) yuvarlak_kutu([79, 60, 16], 6);
    translate([0, -34.2, z0 + 15]) yuz(26, 14);
    for (sx = [-1, 1], sy = [-1, 1]) {
        hip = [sx * 39, sy * 28, z0 + 10];
        knee = [sx * 64, sy * 40, z0 + 14];
        foot = [sx * 70, sy * 46, 2];
        color(GRI) translate(hip) cube([14, 14, 14], center = true);
        color(renk) hull() { translate(hip) sphere(5.5); translate(knee) sphere(5.5); }
        color(KREM) hull() { translate(knee) sphere(5.5); translate(foot) sphere(4); }
    }
}

// 2) Otto tabanlı iki ayak: ~12 cm boy, 240×240 ekran yüz
module otto(renk) {
    color(KREM) translate([-36, -28, 52]) yuvarlak_kutu([72, 56, 62], 6);
    translate([0, -28.2, 86]) yuz(32, 32, 0.14);
    color(renk) translate([-36, -28, 48]) yuvarlak_kutu([72, 56, 10], 3);
    for (sx = [-1, 1]) {
        color(GRI) translate([sx * 16 - 9, -9, 12]) cube([18, 18, 38]);
        color(renk) translate([sx * 18 - 15, -24, 0]) yuvarlak_kutu([30, 48, 10], 3);
    }
}

// 3) StackChan benzeri küp: 56 mm kafa, pan/tilt taban
module kup(renk) {
    color(GRI) translate([-30, -30, 0]) yuvarlak_kutu([60, 60, 24], 5);
    color(GRI) translate([0, 0, 24]) cylinder(d = 22, h = 8);
    color(KREM) translate([-28, -28, 32]) yuvarlak_kutu([56, 56, 54], 6);
    translate([0, -28.2, 58]) yuz(40, 30, 0.16);
    color(renk) translate([-28, -26, 80]) cube([56, 4, 6]);
    color([0.1, 0.1, 0.1]) translate([0, -28.6, 78]) rotate([90, 0, 0]) cylinder(d = 5, h = 0.6);
}

translate([-210, 40, 0]) telefon();
translate([-70, 0, 0]) sesame([0.16, 0.47, 0.84]);
translate([75, 0, 0]) otto([0.92, 0.41, 0.2]);
translate([190, 0, 0]) kup([0.11, 0.69, 0.48]);
color([0.86, 0.86, 0.84]) translate([-300, -90, -2]) cube([560, 200, 2]);
