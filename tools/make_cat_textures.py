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

# ---------------------------------------------------------------------------
# SPAWNÄGG-IKONER FÖR DE HEMLIGA KATTERNA.
#
# Xbox-bild: fyra helsvarta ägg i hotbaren mellan katternas ansikten. Det var
# midnight, aurora, nova och spökkatten — alla fyra saknade `spawn_egg` i sin
# klientdefinition, och då ritar Minecraft sitt standardägg. De syns redan i
# kreativlistan, så ett ansikte avslöjar ingenting som inte redan står där;
# ritualerna är kvar där de hör hemma.
#
# Ikonen härleds ur pc_misty: hennes ansiktsmall målas om i KATTENS EGNA
# färger, hämtade ur dess entitetstextur. Ingen ny bild ritas för hand, och en
# ny hemlig katt kostar en rad.
MISTY_PALS = (154, 160, 166)      # grundpälsen i pc_misty, mätt
MISTY_OGA = (122, 201, 67)        # ögonen i mallen
MISTY_OGA_MORK = (61, 100, 33)


def prova_huvud(cat):
    """Pälsfärg och ögonfärg ur huvudets UV-yta (x 30-56, y 0-12).

    Pälsen är den vanligaste färgen där. Ögonen är den mättade färg som
    förekommer FÅ gånger — brun päls är mättad nog att lura ett rent
    mättnadsfilter, men den är aldrig sällsynt."""
    from collections import Counter
    w, h, px = rr.read_png(f"{RP}/textures/entity/{cat}.png")
    alla = Counter()
    for y in range(0, 12):
        for x in range(30, 56):
            p = px[y][x]
            if len(p) > 3 and p[3] == 0:
                continue
            alla[(p[0], p[1], p[2])] += 1
    pals = alla.most_common(1)[0][0]
    kandidater = [(c, n) for c, n in alla.items()
                  if max(c) - min(c) > 60 and n <= 20 and c != pals]
    oga = max(kandidater, key=lambda t: t[1])[0] if kandidater else MISTY_OGA
    return pals, oga


def ikon_ur_mall(cat):
    """pc_misty omfärgad till kattens egen päls och ögon.

    LJUSGOLV: en ikon på 16x16 mot mörk hotbar måste gå att SE. Midnight och
    Domino är nästan svarta, och en trogen omfärgning blir just det svarta ägg
    som anmäldes. Mörka pälsar lyfts därför mot en läsbar ton i ikonen — bara
    i ikonen, aldrig i pälsen på katten själv."""
    pals, oga = prova_huvud(cat)
    lum_pals = (pals[0] * 3 + pals[1] * 5 + pals[2] * 2) // 10
    if lum_pals < 90:
        k = (90 - lum_pals) / 90 * 0.7
        pals = tuple(min(255, int(c + (150 - c) * k)) for c in pals)
    lum_bas = (MISTY_PALS[0] * 3 + MISTY_PALS[1] * 5 + MISTY_PALS[2] * 2) // 10
    w, h, px = rr.read_png(f"{RP}/textures/items/pc_misty.png")
    ut = []
    for rad in px:
        ny = []
        for p in rad:
            q = (p[0], p[1], p[2], p[3] if len(p) > 3 else 255)
            if q[3] == 0:
                ny.append((0, 0, 0, 0))
            elif q[:3] == MISTY_OGA:
                ny.append((oga[0], oga[1], oga[2], q[3]))
            elif q[:3] == MISTY_OGA_MORK:
                ny.append(tuple(int(c * 0.55) for c in oga) + (q[3],))
            elif q[:3] in ANSIKTE:
                ny.append(q)                       # nos och glans orörda
            else:
                # pälsen: behåll mallens ljus/skugga, byt kulör
                lum = (q[0] * 3 + q[1] * 5 + q[2] * 2) // 10
                k = lum / max(1, lum_bas)
                ny.append(tuple(min(255, int(c * k)) for c in pals) + (q[3],))
        ut.append(ny)
    dp = f"{RP}/textures/items/pc_{cat}.png"
    rr.write_png(dp, w, h, ut)
    return pals, oga


HEMLIGA = ["midnight", "aurora", "nova", "spokkatt"]


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

# Domino är kolsvart och blev samma svarta klump i hotbaren som de hemliga
# katterna, fast av motsatt orsak: hon HADE en ikon, den gick bara inte att se.
# Mallvägen med ljusgolv ger henne ett läsbart ansikte.
print("spawnägg ur mallen (med ljusgolv för mörka pälsar):")
for cat in HEMLIGA + ["domino"]:
    pals, oga = ikon_ur_mall(cat)
    print(f"  pc_{cat}.png  päls {pals}  ögon {oga}")
