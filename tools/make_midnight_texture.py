#!/usr/bin/env python3
"""Genererar Midnights textur ur Mistys — kolsvart päls, glödande ögon.

Midnight är den hemliga femte katten. Texturen är en deterministisk
transform av misty.png: all päls trycks ner mot blåsvart kol (ljusstyrkan
behålls så teckningen skymtar), och de grönaktiga ögonpixlarna byts mot
glödande bärnsten. Körs om när misty.png ändras:

    python3 tools/make_midnight_texture.py
"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import render_regression as rr

SRC = f"{BASE}/PurrfectCompanions_RP/textures/entity/misty.png"
DST = f"{BASE}/PurrfectCompanions_RP/textures/entity/midnight.png"

w, h, px = rr.read_png(SRC)
out = []
eyes = fur = 0
for row in px:
    orow = []
    for p in row:
        r, g, b, a = p[0], p[1], p[2], p[3] if len(p) > 3 else 255
        if a == 0:
            orow.append((0, 0, 0, 0)); continue
        if g > r + 18 and g > b + 18:                 # ögonen (gröna hos Misty)
            orow.append((255, 196, 64, a)); eyes += 1
        else:                                          # pälsen → blåsvart kol
            lum = (r * 3 + g * 5 + b * 2) // 10
            orow.append((10 + lum // 9, 10 + lum // 10, 16 + lum // 7, a)); fur += 1
    out.append(orow)
rr.write_png(DST, w, h, out)
print(f"midnight.png: {w}x{h}, {eyes} ögonpixlar, {fur} pälspixlar")
