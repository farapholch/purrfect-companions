#!/usr/bin/env python3
"""Målar om KATTERNAS ANSIKTEN — större ögon, mjukare drag.

Bakgrund: ungarna bad om sötare katter. Ansiktet var 6x5 texlar med ögon på
2x2, en hård svart mun och nästan svarta kinder — korrekt, men strängt. Det som
gör ett ansikte sött är inte fler detaljer utan RÄTT proportioner: stora ögon
lågt i ansiktet, mjuka kanter, en glansprick. Det är samma barnschema vanilla
använder på axolotl och panda.

    python3 tools/make_cat_faces.py

KÖRORDNING (viktig):
    1. make_cat_markings.py   teckningar på kropparna (rör aldrig huvudet)
    2. make_cat_faces.py      DEN HÄR — ansiktet, och bara ansiktet
    3. make_cat_textures.py   Ginger och Domino härleds ur de målade
    4. build_accessories.py   plaggens UV-ytor målas in igen

VARFÖR EN EGEN FIL och inte en gren i make_cat_markings.py: den filen har en
uttrycklig regel om att huvudet ALDRIG rörs, eftersom ett filter som "bara päls"
förr eller senare råkar ta med en ögonvrå. Regeln är bra och får stå kvar. Det
här skriptet rör bara huvudet, och gör det med uppmätta koordinater i stället
för med ett filter.

IDEMPOTENT: varje pixel SÄTTS till en uträknad färg, ingen skalas. Två körningar
ger exakt samma fil. Det var den egenskapen build_accessories.py saknade när den
hann samla på sig 32 kopior av samma rockad.
"""
import json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import render_regression as rr

RP = f"{BASE}/PurrfectCompanions_RP"

# ANSIKTET LÄSES UR GEOMETRIN. Skallen är den största kuben i huvudbenet;
# öronen är de två små. Ändras modellen följer ansiktet med i stället för att
# hamna en texel fel utan att någon märker det.
_geo = json.load(open(f"{RP}/models/entity/katt.geo.json"))["minecraft:geometry"][0]
_head = next(b for b in _geo["bones"] if b["name"] == "head")
_skalle = max(_head["cubes"], key=lambda c: c["size"][0] * c["size"][1])
_u, _v = _skalle["uv"]
_b, _h, _d = _skalle["size"]
FX, FY, FW, FH = rr.faces(_u, _v, _b, _h, _d)["north"]
FX, FY, FW, FH = int(FX), int(FY), int(FW), int(FH)

# Ansiktet är 6x5. Kolumnerna 0-1 och 4-5 är ögon, 2-3 är nosryggen.
OGON_KOL = ((0, 1), (4, 5))
MITT_KOL = (2, 3)
GLANS = (255, 255, 255, 255)


def blanda(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def mala(ras):
    w, h, px = rr.read_png(f"{RP}/textures/entity/{ras}.png")

    def p(kol, rad):
        return px[FY + rad][FX + kol]

    def satt(kol, rad, farg):
        px[FY + rad][FX + kol] = farg

    # FÄRGERNA LÄSES UR ANSIKTET SOM REDAN FINNS. Misty har gröna ögon, Snow
    # blå — en tabell här hade varit ett andra ställe att hålla i synk, och det
    # är exakt den fällan hundpaketet gick i tre gånger.
    iris_ljus = tuple(p(0, 2))[:3]        # den klara irisfärgen, rad 2
    iris_mork = tuple(p(0, 1))[:3]        # den mörka ögonvrån, rad 1
    kind = tuple(p(0, 4))[:3]             # kindens mörka kontur, rad 4

    for kols in OGON_KOL:
        yttre, inre = (kols[0], kols[1]) if kols[0] < 2 else (kols[1], kols[0])
        # RAD 1: mörk ögonvrå ute, glansprick inne. Glansen är det enda som
        # skiljer ett öga från en knapp.
        satt(yttre, 1, iris_mork + (255,))
        satt(inre, 1, GLANS)
        # RAD 2: klar iris, båda texlarna.
        for k in kols:
            satt(k, 2, iris_ljus + (255,))
        # RAD 3 ÄR NYTT — ÖGAT VÄXER NEDÅT. Ett öga på 2x2 i ett ansikte som är
        # 5 texlar högt är ett vuxet öga; 2x3 är ett kattungeöga, och det är
        # hela skillnaden mellan "katt" och "gullig katt". Nedre kanten är en
        # mörkare ton av irisen, inte den klara — annars buktar ögat ut.
        for k in kols:
            satt(k, 3, blanda(iris_ljus, iris_mork, 0.45))

    # PANNAN VAR ETT SVART BAND. Rad 0 ytterst är nästan svart hela vägen och
    # bildade ett tjockt ögonbryn tvärs över ansiktet — det ensamt gör en katt
    # bister. Den mjukas mot pälsen så pannan blir en skugga i stället för en
    # ram. Pälsfärgen tas ur nosryggen (kolumn 2), som alltid är päls.
    pals = tuple(p(2, 0))[:3]
    for kols in OGON_KOL:
        for k in kols:
            satt(k, 0, blanda(tuple(p(k, 0))[:3], pals, 0.34))

    # MUNNEN VAR ETT SVART STRECK. (26,18,14) tvärs över två texlar rakt under
    # nosen läser som ett streck, inte som en mun — och ett streck gör vilket
    # ansikte som helst bistert. En varm, ljusare ton mjukar upp den utan att
    # ta bort den.
    for k in MITT_KOL:
        satt(k, 4, blanda(kind, (150, 108, 104), 0.55))

    # KINDERNA. Ytterhörnen nedtill var nästan svarta och ramade in ansiktet
    # hårt. De ljusas upp mot nosens rosa — det blir en antydan till kindrodnad
    # utan att bli en clownkind.
    for kols in OGON_KOL:
        yttre = kols[0] if kols[0] < 2 else kols[1]
        satt(yttre, 4, blanda(kind, (206, 132, 138), 0.40))

    rr.write_png(f"{RP}/textures/entity/{ras}.png", w, h, px)
    return iris_ljus


RASER = ("misty", "hazel", "mocha", "snow")

if __name__ == "__main__":
    print(f"ansiktsytan: {FW}x{FH} texlar @ ({FX},{FY})")
    for ras in RASER:
        iris = mala(ras)
        print(f"  {ras:7s} iris {iris}  ögon 2x3, mjukad mun och kind")
