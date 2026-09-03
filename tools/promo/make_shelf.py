#!/usr/bin/env python3
"""Hyllbilden för CurseForge — 16:9 utan text, bara katterna i päls med plagg.

CurseForge bad om en bild till månadshyllan "Pocket Pets" (2026-09-03). Hyllan
sätter sin egen rubrik, så ordmärket ur hjältebilden ska INTE med — en bild
med text i en hylla med text blir dubbelt. Samma miljö och samma renderare som
hjältebilden, men fler katter större och fler plagg synliga: det är pälsen och
materialen som är nyheten.

    python3 tools/promo/make_shelf.py      # -> publish/purrfect-shelf.png
"""
import os, sys
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE); sys.path.insert(0, f"{BASE}/tools/promo")
import render_regression as rr
import make_hero as mh

W, H = mh.W, mh.H


def bygg():
    img = mh.duk()
    mh.moln(img)
    mh.kullar(img)
    mh.mark(img)
    for bx, hojd in ((1, 6), (5, 5), (72, 6), (77, 5)):
        mh.bjork(img, bx, mh.HORISONT + mh.B, hojd)
    # ÅTTA KATTER i två djupled. Framraden stor så pälsen läser i miniatyr;
    # plaggen spridda så varje katt visar något eget utan att bli katalog.
    stallningar = [
        ("ginger", ["gruvlampa1"],            0.14, 0.86, 250, 26, 0.5),
        ("mocha",  ["horn2", "vingar1"],      0.32, 0.90, 270, 34, 1.4),
        ("misty",  ["sadel1", "halsduk5"],    0.52, 0.92, 285, 20, 2.2),
        ("snow",   ["rosett1"],               0.70, 0.88, 260, 40, 0.9),
        ("domino", ["krona1", "mantel1"],     0.87, 0.85, 245, 18, 1.7),
        ("hazel",  ["ryggsack1", "tossor1"],  0.26, 0.66, 160, 44, 2.6),
        ("misty",  ["regnrock1"],             0.60, 0.64, 150, 12, 0.2),
        ("mocha",  ["flytvast1"],             0.80, 0.66, 150, 30, 2.9),
    ]
    for cat, plagg, fx, fy, hojd, yaw, t in stallningar:
        mh.katt(img, cat, plagg, int(W * fx), int(H * fy), hojd, yaw, t)
    ut = f"{BASE}/publish/purrfect-shelf.png"
    rr.write_png(ut, W, H, [[(p[0], p[1], p[2], 255) for p in rad] for rad in img])
    print(f"  publish/purrfect-shelf.png ({W}x{H})")


if __name__ == "__main__":
    bygg()
