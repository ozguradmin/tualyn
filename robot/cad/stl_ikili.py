#!/usr/bin/env python3
"""OpenSCAD'in ASCII STL çıktılarını ikili (binary) STL'ye çevirir (~5 kat küçük).
Kullanım: python3 stl_ikili.py stl/*.stl"""
import struct
import sys


def convert(path):
    with open(path, "rb") as f:
        head = f.read(5)
    if head != b"solid":
        return False  # zaten ikili
    tris = []
    normal = None
    verts = []
    with open(path, encoding="ascii", errors="replace") as f:
        for line in f:
            t = line.split()
            if not t:
                continue
            if t[0] == "facet":
                normal = tuple(float(v) for v in t[2:5])
                verts = []
            elif t[0] == "vertex":
                verts.append(tuple(float(v) for v in t[1:4]))
            elif t[0] == "endfacet":
                tris.append((normal, verts))
    with open(path, "wb") as f:
        f.write(b"Kipir v1 - OpenSCAD".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for n, v in tris:
            f.write(struct.pack("<12fH", *n, *v[0], *v[1], *v[2], 0))
    return True


if __name__ == "__main__":
    for p in sys.argv[1:]:
        if convert(p):
            print("ikili:", p)
