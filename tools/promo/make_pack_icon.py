#!/usr/bin/env python3
"""Paketikonen (pack_icon.png i BP+RP) — samma bild som projektloggan.

Ikonen visas i spelets paketlista, alltså varje gång någon slår på addonet:
det är den mest sedda ytan i hela projektet. Den hade en egen komposition
(katternas ansikten i ett rutnät) som levde sitt eget liv och hann bli fyra
katter när det fanns sex.

Nu härleds den ur publish/logo.png. En bild, ett uttryck, ett ställe att
ändra — och loggan är dessutom formgiven för att läsa i litet format, vilket
är precis vad ikonen behöver.

Nedskalningen 512 -> 256 är exakt 2:1 och görs med NÄRMSTA GRANNE. Ett
medelvärde hade suddat pixelkonsten; hellre skarpa kanter.

    python3 tools/promo/make_pack_icon.py     (kör make_logo.py först)
"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)
import render_regression as rr

KALLA = f"{BASE}/publish/logo.png"
N = 256

w, h, px = rr.read_png(KALLA)
ut = [[px[y * h // N][x * w // N] for x in range(N)] for y in range(N)]
ut = [[(p[0], p[1], p[2], 255) for p in rad] for rad in ut]
for pack in ("PurrfectCompanions_BP", "PurrfectCompanions_RP"):
    rr.write_png(f"{BASE}/{pack}/pack_icon.png", N, N, ut)
print(f"pack_icon.png ({N}x{N}) skriven till BP+RP ur {os.path.basename(KALLA)}")
