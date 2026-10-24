// =====================================================================
//  KIPIR v1  —  telefon/tablet yüzlü, ESP32'li, 2 tekerlekli ev robotu
// ---------------------------------------------------------------------
//  OpenSCAD 2021.01 ve sonrası. Birimler: mm.
//  Eksenler: +X ileri, +Y sol, +Z yukarı. Zemin z = 0.
//
//  Tek bir parça almak için:
//    openscad -D 'part="taban"' -o taban.stl kipir.scad
//  part = assembly olduğunda tüm robot (renkli, hayali motor/teker/telefon
//  ile birlikte) görünür. Diğer değerlerde parça baskı yönünde, tablaya
//  oturmuş olarak gelir.
// =====================================================================

part = "assembly"; // [assembly, taban, ust_kat, boyun, kafa_ray, cene_sol, cene_sag, teker_kapak, sensor_tutucu, kulak_sol, kulak_sag]

/* [Cihaz (kafa)] */
// Telefon/tablet kalınlığı için kanal genişliği. 11.5 mm'ye kadar (kılıflı
// telefonlar, Tab 3 Lite 9.7 mm) sığar; boşluğu sünger bantla doldur.
dev_t = 12;
// Sadece montaj görünümü için: cihazın uzun kenarı (SM-T110 = 193.4)
dev_L = 193.4;
// Sadece montaj görünümü için: cihazın kısa kenarı (SM-T110 = 116.4)
dev_H = 116.4;

/* [Teker ve motor (sarı TT motor 1:48 + 65 mm teker)] */
wheel_d = 66;   // 65-68 mm arası tekerler sığar
wheel_w = 27;   // 25.6-27 mm
// Motor dişli kutusu ölçüleri (SunFounder TT motor çizimi)
tt_face_w = 22.3;         // dişli kutusu yüz genişliği
tt_thick = 18.7;          // dişli kutusu kalınlığı
tt_shaft_to_holes = 20.1; // mil ekseni -> 2 adet Ø2.8 montaj deliği
tt_hole_sp = 17.5;        // iki montaj deliği arası
tt_shaft_to_tab = 13.4;   // mil -> alt kulakçık deliği
tt_peg_off = 11.0;        // mil -> küçük merkezleme çıkıntısı
tt_motor_side = 53.4;     // milden motor ucuna (64.4 - 11)
wheel_gap = 2.5;          // dişli kutusu dış yüzü ile teker arası

/* [Gövde] */
base_d = 190;       // taban çapı (220x220 tablaya sığar)
plate_t = 4;        // taban kalınlığı
deck_d = 180;       // üst kat çapı
deck_t = 3.5;       // üst kat kalınlığı
pillar_h = 58;      // iki kat arası boşluk (powerbank + kablolar)
pillar_d = 12;

/* [Sarhoş teker (misket/bilye)] */
ball_d = 16;        // 16 mm cam misket ya da çelik bilye
ball_clr = 0.4;     // bilye yuvası boşluğu
front_gap = 1.0;    // ön misket yerden bu kadar yukarıda: robot 3 noktaya basar
caster_x = 76;

/* [Kafa] */
neck_x = -18;       // boyun konumu (merkezin biraz arkası)
neck_h = 45;        // üst kattan kafa rayı merkezine
tilt = 8;           // ekranın arkaya yatma açısı (derece)
rail_len = 200;
rail_h = 32;
rail_t = 5;

$fn = 64;
eps = 0.01;

// ---------------- türetilmiş ölçüler ----------------
axle_z = wheel_d / 2;
wheel_y = 78.5;                                   // teker orta düzlemi
gear_out_y = wheel_y - wheel_w / 2 - wheel_gap;   // 62.5
gear_in_y = gear_out_y - tt_thick;                // 43.8
wall_t = 4;
wall_x0 = -30;
wall_x1 = 18;
base_z = ceil(axle_z + tt_face_w / 2 + 1.5);      // taban alt yüzü (46)
base_top = base_z + plate_t;                      // 50
notch_x = wheel_d / 2 + 5;
notch_y0 = gear_out_y + 0.5;
wall_zb = axle_z - tt_face_w / 2 - 5;

deck_z = base_top + pillar_h;                     // üst kat alt yüzü
deck_top = deck_z + deck_t;
pillar_pts = [[66, 46], [66, -46], [-66, 46], [-66, -46]];

post_d = ball_d + 9;                              // misket direği çapı
lug_r = post_d / 2 + 4;                           // kapak vidası yarıçapı
cap_R = ball_d / 2 + ball_clr;
cap_open = 0.85 * ball_d;                         // alt ağız çapı
cap_h = sqrt(cap_R * cap_R - (cap_open / 2) * (cap_open / 2));

strap_x = [32, 58];                               // cırt bant yuvaları (x aralığı)
strap_y = [37.5, 41.5];
wire_holes = [[-58, 60], [-58, -60]];
sensor_x = 78;                                    // HC-SR04 tutucu plaka konumu
sensor_holes = [[sensor_x + 7.5, 18], [sensor_x + 7.5, -18]];

// kafa çenesi
jp_t = 5;          // çene plakası
web_t = 3;         // çene yan duvarı
lip_t = 2.5;       // ön dudak
lip_w = 3.5;       // dudağın ekrana bindiği genişlik (boşluk dahil)
clr = 0.5;
floor_t = 3;
floor_w = 14;
jaw_h = 84;
port_z = [22, 70]; // şarj kablosu penceresi (telefon ve tablet için)
ear_w = 8;
jaw_bolt_y = -9;   // cihaz kenarından içeri
rail_z0 = 20;      // çene altından ray merkezine
slot_y = [58, 94]; // ray yuvaları (cihaz boyu 140-200 mm)
slot_z = 8;

// =====================================================================
//  yardımcılar
// =====================================================================
module rounded_slot2d(p0, p1, w) {
    hull() {
        translate(p0) circle(d = w);
        translate(p1) circle(d = w);
    }
}

module hex_pocket(af = 5.7, h = 2.6) {
    cylinder(d = af / cos(30), h = h, $fn = 6);
}

// =====================================================================
//  TABAN  (motor duvarları ve misket direkleri tek parça)
// =====================================================================
module base_plate2d() {
    difference() {
        offset(r = -3) offset(r = 3)            // iç köşeleri yuvarla
        offset(r = 2) offset(r = -2)            // dış köşeleri yuvarla
        difference() {
            circle(d = base_d, $fn = 180);
            for (m = [0, 1]) mirror([0, m])
                translate([-notch_x, notch_y0]) square([2 * notch_x, base_d]);
        }
        // üst kat direk vidaları
        for (p = pillar_pts) translate(p) circle(d = 3.4);
        // powerbank cırt bant yuvaları
        for (sx = [1, -1], m = [0, 1]) mirror([0, m])
            rounded_slot2d([sx * strap_x[0] + (sx > 0 ? 2 : -2), (strap_y[0] + strap_y[1]) / 2],
                           [sx * strap_x[1] - (sx > 0 ? 2 : -2), (strap_y[0] + strap_y[1]) / 2],
                           strap_y[1] - strap_y[0]);
        // motor kablosu delikleri
        for (p = wire_holes) translate(p) circle(d = 10);
        // ön sensör tutucu vidaları
        for (p = sensor_holes) translate(p) circle(d = 3.4);
        // misket kapağı vidalarına üstten tornavida erişimi
        for (cx = [-caster_x, caster_x], sy = [-1, 1]) translate([cx, sy * lug_r]) circle(d = 7);
        // misket direklerinin arasından zip-tie / kablo geçişi
        for (x = [-30, -15, 0, 15, 30]) translate([x, 0]) circle(d = 4);
    }
}

// sol (+Y) motor duvarı; sağ taraf ayna
module motor_wall() {
    y0 = gear_in_y - wall_t;
    translate([wall_x0, y0, wall_zb]) cube([wall_x1 - wall_x0, wall_t, base_z - wall_zb + eps]);
    for (gx = [wall_x0, 6, wall_x1 - 3])
        translate([gx, 0, 0]) rotate([90, 0, 90]) linear_extrude(3)
            polygon([[y0 + eps, base_z + eps], [y0 - 12, base_z + eps], [y0 + eps, base_z - 20]]);
}

module motor_wall_holes() {
    y0 = gear_in_y - wall_t - 1;
    for (dz = [-tt_hole_sp / 2, tt_hole_sp / 2])
        translate([-tt_shaft_to_holes, y0, axle_z + dz]) rotate([-90, 0, 0]) cylinder(d = 3.4, h = wall_t + 2);
    translate([0, y0, axle_z]) rotate([-90, 0, 0]) cylinder(d = 10, h = wall_t + 2);
    translate([-tt_peg_off, y0, axle_z]) rotate([-90, 0, 0]) cylinder(d = 7, h = wall_t + 2);
}

module caster_post(cx, gap) {
    cz = ball_d / 2 + gap;
    lug_out = lug_r + 4.5;
    translate([cx, 0, cz]) cylinder(d = post_d, h = base_z - cz + eps);
    // kapak vida kulakları; üstü 45° pahlı (ters baskıda desteksiz çıkar)
    for (m = [0, 1]) mirror([0, m, 0]) translate([cx, 0, 0]) hull() {
        translate([-4.5, post_d / 2 - 2, cz]) cube([9, lug_out - post_d / 2 + 2, 6]);
        translate([-4.5, post_d / 2 - 2, cz]) cube([9, 2, 6 + lug_out - post_d / 2]);
    }
}

module caster_post_cut(cx, gap) {
    cz = ball_d / 2 + gap;
    translate([cx, 0, cz]) sphere(d = 2 * cap_R, $fn = 48);
    for (s = [-1, 1]) translate([cx, s * lug_r, cz - eps]) {
        cylinder(d = 3.4, h = 30);
        translate([0, 0, 6]) cylinder(d = 6.5, h = 30);   // vida başı oturağı
    }
}

module taban() {
    difference() {
        union() {
            translate([0, 0, base_z]) linear_extrude(plate_t) base_plate2d();
            for (m = [0, 1]) mirror([0, m, 0]) motor_wall();
            caster_post(-caster_x, 0);
            caster_post(caster_x, front_gap);
        }
        for (m = [0, 1]) mirror([0, m, 0]) motor_wall_holes();
        caster_post_cut(-caster_x, 0);
        caster_post_cut(caster_x, front_gap);
    }
}

// misket kapağı (2 adet). z=0 kapak altı, üst yüzü bilye merkezinde.
module teker_kapak() {
    difference() {
        hull() {
            cylinder(d = post_d, h = cap_h);
            for (s = [-1, 1]) translate([-4.5, s > 0 ? 0 : -lug_r - 4.5, 0]) cube([9, lug_r + 4.5, cap_h]);
        }
        translate([0, 0, cap_h]) sphere(d = 2 * cap_R, $fn = 48);
        for (s = [-1, 1]) translate([0, s * lug_r, -eps]) cylinder(d = 2.7, h = cap_h + 1);
    }
}

// =====================================================================
//  ÜST KAT (direkler tek parça; ters basılır)
// =====================================================================
module deck2d() {
    difference() {
        circle(d = deck_d, $fn = 180);
        // elektronik için 10 mm ızgara (M3 / zip-tie): ön bölge ve arka bölge
        for (x = [-80 : 10 : 80], y = [-80 : 10 : 80])
            if (norm([x, y]) < deck_d / 2 - 7
                && ((x >= 0 && x <= 50 && abs(y) <= 40) || (x <= -45 && abs(y) <= 30))
                && min([for (p = pillar_pts) norm([x, y] - p)]) > 10
                && min([for (p = wire_holes) norm([x, y] - p)]) > 10)
                translate([x, y]) circle(d = 3.3, $fn = 16);
        // hafifletme / kablo pencereleri (yanlarda)
        for (m = [0, 1]) mirror([0, m])
            hull() for (x = [-25, 30]) translate([x, 62]) circle(d = 14);
        // kablo geçişleri
        for (p = wire_holes) translate(p) circle(d = 10);
        rounded_slot2d([56, 0], [68, 0], 9);
        // boyun vidaları ve boyun içinden kablo deliği
        for (dx = [-12, 12], dy = [-17, 17]) translate([neck_x + dx, dy]) circle(d = 3.4);
        translate([neck_x, 0]) square([8, 14], center = true);
    }
}

module ust_kat() {
    difference() {
        union() {
            translate([0, 0, deck_z]) linear_extrude(deck_t) deck2d();
            for (p = pillar_pts) translate([p[0], p[1], base_top]) cylinder(d = pillar_d, h = pillar_h + eps);
        }
        // M3 vidalar tabanın altından girip direğe kendi yolunu açar
        for (p = pillar_pts) translate([p[0], p[1], base_top - eps]) cylinder(d = 2.7, h = 14);
    }
}

// =====================================================================
//  BOYUN
// =====================================================================
module pad3d() {
    // YZ'de profil, X boyunca 5 mm; alt kenarlar 45° (desteksiz baskı)
    rotate([90, 0, 90]) linear_extrude(5)
        polygon([[-22, 15], [22, 15], [22, -15], [12, -25], [-12, -25], [-22, -15]]);
    // alt kenarı boyuna 45° ile bağlayan takoz (askıda yüzey kalmasın)
    hull() {
        translate([0, -12, -25]) cube([5, 24, 0.01]);
        translate([-0.01, -12, -30.5]) cube([0.01, 24, 0.01]);
    }
}

module boyun() {
    difference() {
        union() {
            translate([-17, -22, 0]) cube([34, 44, 6]);
            translate([-8, -12, 0]) cube([16, 24, neck_h + 15]);
            translate([8, 0, neck_h]) rotate([0, -tilt, 0]) pad3d();
            // plakanın arkaya yatan alt yarısını boyuna bağlayan kama (baskıda havada kalmasın)
            hull() {
                translate([8 - eps, -12, 10]) cube([eps, 24, 35]);
                translate([8, 0, neck_h]) rotate([0, -tilt, 0]) translate([0, -12, -30.5]) cube([0.01, 24, 30.5]);
            }
        }
        for (dx = [-12, 12], dy = [-17, 17]) translate([dx, dy, -eps]) cylinder(d = 2.7, h = 7);
        // kulak LED kabloları için boyun içi kanal
        translate([-5, -7, -eps]) cube([9, 14, neck_h + 16]);
        translate([8, 0, neck_h]) rotate([0, -tilt, 0])
            for (dy = [-17, 17]) translate([-1, dy, 0]) rotate([0, 90, 0]) cylinder(d = 3.4, h = 8);
    }
}

// =====================================================================
//  KAFA RAYI + ÇENELER (cihaz boyu 140-200 mm ayarlanır)
//  kafa koordinatı: x=0 rayın arka yüzü, ray merkezi y=0,z=0
// =====================================================================
module kafa_ray() {
    difference() {
        hull() for (y = [-1, 1], z = [-1, 1])
            translate([0, y * (rail_len / 2 - 4), z * (rail_h / 2 - 4)]) rotate([0, 90, 0]) cylinder(r = 4, h = rail_t);
        // boyun vidaları + somun yuvaları (ön yüzde)
        for (dy = [-17, 17]) {
            translate([-1, dy, 0]) rotate([0, 90, 0]) cylinder(d = 3.4, h = rail_t + 2);
            translate([rail_t - 2.6, dy, 0]) rotate([0, 90, 0]) rotate([0, 0, 30]) hex_pocket(h = 3);
        }
        // çene kızakları
        for (m = [0, 1], z = [-slot_z, slot_z]) mirror([0, m, 0])
            translate([-1, 0, 0]) rotate([0, 90, 0]) linear_extrude(rail_t + 2)
                rounded_slot2d([-z, slot_y[0]], [-z, slot_y[1]], 3.4);
        // hafifletme pencereleri
        for (y = [-38, 38]) translate([-1, 0, 0]) rotate([0, 90, 0])
            linear_extrude(rail_t + 2) rounded_slot2d([0, y - 6], [0, y + 6], 12);
    }
}

// sol çene: cihaz kenarı y=0'da, cihaz y<0 tarafında. z=0 çene tabanı.
module cene() {
    x0 = rail_t;
    x1 = x0 + jp_t;
    x2 = x1 + dev_t;
    x3 = x2 + lip_t;
    difference() {
        union() {
            translate([x0, -20, 0]) cube([jp_t, 20 + clr + web_t, jaw_h]);
            translate([x0, clr, 0]) cube([x3 - x0, web_t, jaw_h]);
            translate([x2, -lip_w, 0]) cube([lip_t, lip_w + clr + web_t, jaw_h]);
            translate([x0, -floor_w, 0]) cube([x3 - x0, floor_w + clr + web_t, floor_t]);
            hull() {   // kulak bloğu, altı 45° pahlı
                translate([x0, clr, jaw_h - 8]) cube([x3 - x0, ear_w, 8]);
                translate([x0, clr, jaw_h - 8 - (ear_w - web_t) - 1]) cube([x3 - x0, web_t, 1]);
            }
        }
        translate([x1, clr - eps, port_z[0]]) cube([dev_t, web_t + 2 * eps, port_z[1] - port_z[0]]);
        for (z = [rail_z0 - slot_z, rail_z0 + slot_z]) {
            translate([x0 - 1, jaw_bolt_y, z]) rotate([0, 90, 0]) cylinder(d = 3.4, h = jp_t + 2);
            translate([x1 - 2.6, jaw_bolt_y, z]) rotate([0, 90, 0]) rotate([0, 0, 30]) hex_pocket(h = 3);
        }
        translate([x3 - 4.5, clr + ear_w / 2, jaw_h - 10]) cylinder(d = 2.7, h = 11);
    }
}

// kulak / anten: tepesinde 5 mm LED taşır (WS2812D-F5 gibi adreslenebilir
// 5 mm RGB LED önerilir; şeffaf/beyaz PETG ile basılırsa ışığı dağıtır).
// LED üstten yuvaya itilir; bacaklarına uzatma teli lehimlenip çubuktan indirilir.
// z=0 tabla. Çenenin üst bloğuna M3x8 ile vidalanır.
module kulak() {
    tab_l = jp_t + dev_t + lip_t;   // çene derinliği
    difference() {
        union() {
            translate([-tab_l / 2, -ear_w / 2, 0]) cube([tab_l, ear_w, 3]);
            hull() {
                translate([-tab_l / 2 + 4, 0, 0]) cylinder(d = 7, h = 3);
                translate([-tab_l / 2 + 4, 0, 3]) rotate([-10, 0, 0]) cylinder(d = 6.5, h = 0.1);
            }
            translate([-tab_l / 2 + 4, 0, 3]) rotate([-10, 0, 0]) {
                cylinder(d = 6.5, h = 38);
                translate([0, 0, 38 + 6]) hull() {
                    sphere(d = 15);
                    translate([0, 0, -12]) cylinder(d = 3, h = 1);
                }
            }
        }
        translate([tab_l / 2 - 4.5, 0, -eps]) cylinder(d = 3.4, h = 4);
        translate([-tab_l / 2 + 4, 0, 3]) rotate([-10, 0, 0]) {
            translate([0, 0, -1]) cylinder(d = 3.2, h = 45);
            translate([0, 0, 38 + 6 - 4]) cylinder(d = 6.2, h = 12);   // 5 mm LED yuvası (yakası 5,8 mm), üstten takılır
        }
        // kablo çıkışı (arkaya)
        translate([-tab_l / 2 + 4, 0, 4]) rotate([0, -90, 0]) cylinder(d = 3.2, h = 10);
    }
}

// =====================================================================
//  HC-SR04 TUTUCU
//  plaka ön yüzü +X'e bakar; ayak ileri uzanır ve tabana 2xM3 ile bağlanır
// =====================================================================
module sensor_tutucu() {
    sz = 18;  // sensör merkez yüksekliği (taban üstünden)
    difference() {
        union() {
            translate([0, -25, 0]) cube([3, 50, 32]);
            translate([0, -25, 0]) cube([12, 50, 3]);
            for (y = [-25, 22]) translate([0, y, 0]) hull() {
                cube([3, 3, 20]);
                cube([12, 3, 3]);
            }
        }
        for (y = [-13, 13]) translate([-1, y, sz]) rotate([0, 90, 0]) cylinder(d = 16.4, h = 5);
        for (y = [-18, 18]) translate([7.5, y, -1]) cylinder(d = 3.4, h = 5);
    }
}

// =====================================================================
//  montaj görünümü (hayali parçalar dahil)
// =====================================================================
module tt_motor_dummy() {
    // yerel: mil x=0, dişli kutusu iç yüzü y=0, motor -X yönünde
    color("gold") translate([-tt_motor_side, 0, -tt_face_w / 2]) cube([tt_motor_side + 11, tt_thick, tt_face_w]);
    color("silver") translate([-tt_motor_side - 6, 2, -9]) cube([8, 15, 18]);
    color("white") translate([0, -2, 0]) rotate([-90, 0, 0]) cylinder(d = 5.4, h = tt_thick + 11);
}

module wheel_dummy() {
    rotate([-90, 0, 0]) {
        color([0.15, 0.15, 0.15]) difference() {
            cylinder(d = wheel_d, h = wheel_w, center = true);
            cylinder(d = wheel_d - 14, h = wheel_w + 1, center = true);
        }
        color("gold") cylinder(d = wheel_d - 14, h = wheel_w - 6, center = true);
    }
}

module head_frame() {
    translate([neck_x + 8, 0, deck_top + neck_h]) rotate([0, -tilt, 0]) translate([5, 0, 0]) children();
}

module assembly() {
    color("lightskyblue") taban();
    color("tomato") translate([caster_x, 0, ball_d / 2 + front_gap - cap_h]) teker_kapak();
    color("tomato") translate([-caster_x, 0, ball_d / 2 - cap_h]) teker_kapak();
    color("white", 0.7) for (cx = [caster_x, -caster_x]) translate([cx, 0, ball_d / 2 + (cx > 0 ? front_gap : 0)]) sphere(d = ball_d);
    for (m = [0, 1]) mirror([0, m, 0]) {
        translate([0, gear_in_y, axle_z]) tt_motor_dummy();
        translate([0, wheel_y, axle_z]) wheel_dummy();
    }
    color("lightskyblue") ust_kat();
    color("tomato") translate([neck_x, 0, deck_top]) boyun();
    color("tomato") translate([sensor_x, 0, base_top]) sensor_tutucu();
    // powerbank, ESP32, HC-SR04
    color([0.3, 0.3, 0.35]) translate([-86, -36, base_top]) cube([140, 72, 16]);
    color("royalblue") translate([20, -14, deck_top]) cube([52, 28, 12]);
    color("teal") translate([sensor_x - 2, -22.5, base_top + 8]) cube([2, 45, 20]);
    color("silver") for (y = [-13, 13]) translate([sensor_x, y, base_top + 18]) rotate([0, 90, 0]) cylinder(d = 16, h = 15);
    head_frame() {
        color("lightskyblue") kafa_ray();
        for (m = [0, 1]) mirror([0, m, 0])
            translate([0, dev_L / 2, -rail_z0]) {
                color("tomato") cene();
                color("white") translate([rail_t + (jp_t + dev_t + lip_t) / 2, clr + ear_w / 2, jaw_h]) kulak();
            }
        // cihaz
        translate([rail_t + jp_t, -dev_L / 2, -rail_z0 + floor_t]) {
            color([0.1, 0.1, 0.12]) cube([dev_t - 1.3, dev_L, dev_H]);
            color([0.95, 0.85, 0.3]) translate([dev_t - 1.2, 0, 0]) face_dummy();
        }
    }
}

module face_dummy() {
    // basit robot yüzü (sadece görsel)
    for (y = [dev_L * 0.32, dev_L * 0.68]) translate([0, y, dev_H * 0.58]) rotate([0, 90, 0]) cylinder(d = dev_H * 0.26, h = 0.3);
    translate([0, dev_L * 0.4, dev_H * 0.22]) cube([0.3, dev_L * 0.2, dev_H * 0.06]);
}

// =====================================================================
//  baskı yönleri
// =====================================================================
if (part == "assembly") assembly();
else if (part == "taban") translate([0, 0, base_top]) rotate([180, 0, 0]) taban();
else if (part == "ust_kat") translate([0, 0, deck_top]) rotate([180, 0, 0]) ust_kat();
else if (part == "boyun") boyun();
else if (part == "kafa_ray") rotate([0, -90, 0]) kafa_ray();
else if (part == "cene_sol") cene();
else if (part == "cene_sag") mirror([0, 1, 0]) cene();
else if (part == "teker_kapak") teker_kapak();
else if (part == "sensor_tutucu") rotate([0, -90, 0]) sensor_tutucu();
else if (part == "kulak_sol") kulak();
else if (part == "kulak_sag") mirror([0, 1, 0]) kulak();
