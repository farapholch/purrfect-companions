#!/usr/bin/env python3
"""Genererar de nya rasernas texturer och spawnägg-ikoner ur de befintliga.

Samma princip som make_midnight_texture.py: ingen ny bild ritas för hand, utan
varje ny päls är en DETERMINISTISK transform av en katt som redan finns. Då
följer nya raser automatiskt med när grundtexturen ändras (plaggens UV-ytor
målas t.ex. in i efterhand av build_accessories.py), och två katter kan aldrig
glida isär i teckning.

  Ginger  <- misty.png   grå tabby  -> varm ingefära, teckningen kvar
  Domino  <- hazel.png   brun-vit   -> kolsvart där brunt var, vitt orört

Ansiktet (ögon, nos, glans) lämnas i fred i båda fallen. Plaggens UV-ytor
målas om av build_accessories.py efteråt, så de behöver inget skydd här.

Körs om när grundtexturerna ändras:

    python3 tools/make_cat_textures.py
"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import render_regression as rr

RP = f"{BASE}/PurrfectCompanions_RP"


# ANSIKTET är inte päls. De här färgerna är UPPMÄTTA i huvudets UV-yta
# (x 30-56, y 0-12) i både misty.png och hazel.png och är identiska i båda:
# två gröna ögontoner, en vit glansprick och en rosa nos. Regelbaserade filter
# ("lämna mättade pixlar") gick inte att lita på — hazels bruna päls är mer
# mättad än en del av ansiktet, så Domino blev brun med svarta ögon. Ändras
# grundtexturernas ansikte måste den här listan mätas om.
ANSIKTE = {(122, 201, 67), (67, 110, 36), (255, 255, 255), (226, 140, 160)}


def vit(r, g, b):
    """Hazels vita haklapp och tassar. Höga kanaler OCH nästan neutral kulör —
    annars fastnar även den ljusaste brunbeigen i filtret och Domino blir
    fläckvis vit på fel ställen."""
    return min(r, g, b) > 168 and max(r, g, b) - min(r, g, b) < 30


def lum(r, g, b):
    return (r * 3 + g * 5 + b * 2) // 10


def ginger(p):
    r, g, b, a = p
    if a == 0:
        return (0, 0, 0, 0)
    if (r, g, b) in ANSIKTE:
        return p
    L = lum(r, g, b)
    # Ingefära: rött nästan linjärt mot ljusstyrkan, grönt halva vägen, blått
    # nästan inte alls. Golvet håller de mörkaste strimmorna varma i stället
    # för att låta dem gå i svart.
    return (min(255, 46 + L * 82 // 100),
            min(255, 20 + L * 46 // 100),
            min(255, 10 + L * 22 // 100), a)


def domino(p):
    r, g, b, a = p
    if a == 0:
        return (0, 0, 0, 0)
    if (r, g, b) in ANSIKTE:
        return p
    if vit(r, g, b):
        return p                                 # haklapp och tassar orörda
    L = lum(r, g, b)
    # Kol med en aning blått i, samma knep som Midnight: behåll ljusstyrkan
    # skalad så teckningen skymtar i stället för att bli en svart klump.
    return (14 + L * 26 // 100, 14 + L * 26 // 100, 20 + L * 30 // 100, a)


JOBB = [
    ("ginger", "misty", ginger),
    ("domino", "hazel", domino),
]


def kor(dst, src, fn, mapp, vad):
    sp = f"{RP}/{mapp}/{src}.png"
    dp = f"{RP}/{mapp}/{dst}.png"
    w, h, px = rr.read_png(sp)
    ut = []
    rort = orort = 0
    for rad in px:
        ny = []
        for p in rad:
            q = (p[0], p[1], p[2], p[3] if len(p) > 3 else 255)
            r = fn(q)
            if q[3] == 0:
                pass
            elif r[:3] == q[:3]:
                orort += 1
            else:
                rort += 1
            ny.append(r)
        ut.append(ny)
    rr.write_png(dp, w, h, ut)
    print(f"  {vad:12} {dst}.png {w}x{h}  omfärgade {rort} px, lämnade {orort} px")


for dst, src, fn in JOBB:
    print(f"{dst} <- {src}")
    kor(dst, src, fn, "textures/entity", "päls")
    kor(f"pc_{dst}", f"pc_{src}", fn, "textures/items", "spawnägg")
