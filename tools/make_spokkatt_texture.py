#!/usr/bin/env python3
"""Spökkattens textur: Mistys teckning, vitnad och halvgenomskinlig.

Spökkatterna strövar i mörka skogen i Cat Haven — de gamla katternas
spöken. Materialet i RP-entityn är entity_alphablend, så texturens
alfakanal ger äkta genomskinlighet. Ögonen får kallt blågrönt sken.

    python3 tools/make_spokkatt_texture.py
"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import render_regression as rr

SRC = f"{BASE}/PurrfectCompanions_RP/textures/entity/misty.png"
DST = f"{BASE}/PurrfectCompanions_RP/textures/entity/spokkatt.png"

w, h, px = rr.read_png(SRC)
out = []
for row in px:
    orow = []
    for p in row:
        r, g, b, a = p[0], p[1], p[2], p[3] if len(p) > 3 else 255
        if a == 0:
            orow.append((0, 0, 0, 0)); continue
        if g > r + 18 and g > b + 18:                  # ögonen -> kallt sken
            orow.append((140, 255, 230, 235))
        else:                                           # pälsen -> blekvit, halvklar
            lum = (r * 3 + g * 5 + b * 2) // 10
            v = 190 + lum // 5
            orow.append((min(255, v), min(255, v + 4), 255, 150))
    out.append(orow)
rr.write_png(DST, w, h, out)
print(f"spokkatt.png: {w}x{h}")
