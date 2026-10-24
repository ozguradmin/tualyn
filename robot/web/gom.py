#!/usr/bin/env python3
"""web/ klasöründeki kumanda.html ve yuz.html'i (yuz.js gömülü olarak)
firmware/kipir_esp32/web_pages.h dosyasına yazar.
Sayfalarda bir şey değiştirdikten sonra çalıştır:  python3 gom.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "firmware", "kipir_esp32", "web_pages.h")
DELIM = "KIPIR"


def page(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        html = f.read()
    with open(os.path.join(HERE, "yuz.js"), encoding="utf-8") as f:
        js = f.read()
    html = html.replace('<script src="yuz.js"></script>', "<script>\n" + js + "</script>")
    if ")" + DELIM + '"' in html:
        raise SystemExit(f"{name}: ham dize sınırlayıcısı sayfada geçiyor")
    return html


def main():
    parts = [
        "// OTOMATİK ÜRETİLDİ: robot/web/gom.py. Elle düzenleme; web/ altındaki dosyaları değiştir.",
        "#pragma once",
        "#include <pgmspace.h>",
        "",
    ]
    for var, name in (("PAGE_KUMANDA", "kumanda.html"), ("PAGE_YUZ", "yuz.html")):
        parts.append(f'const char {var}[] PROGMEM = R"{DELIM}(' + page(name) + f'){DELIM}";')
        parts.append("")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("yazıldı:", os.path.relpath(OUT, HERE), os.path.getsize(OUT), "bayt")


if __name__ == "__main__":
    main()
