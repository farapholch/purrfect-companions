#!/usr/bin/env python3
"""Målar TECKNINGAR på kattpälsarna — ränder, ljus buk, svansringar.

Bakgrund: en spelare skrev "it's cute, but... are u able to improve the
textures?" och hade rätt. Ansiktena har detaljer, men KROPPARNA var enfärgade
plattor: ingen päls, ingen skuggning, ingen teckning. README lovade dessutom
"grey tabby" och "warm ginger tabby" utan att det fanns en enda rand.

Hund- och grispaketen har haft mönstermaskineri hela tiden (fläckar, sadel,
bringa, strumpor, ullkrus). Katterna är det ÄLDSTA paketet och byggdes innan
den tekniken fanns — det här är den, portad hit.

    python3 tools/make_cat_markings.py

KÖRORDNING (viktig):
    1. make_cat_markings.py   DEN HÄR — teckningar på grundpälsarna
    2. make_cat_textures.py   Ginger, Domino och de hemliga härleds ur de MÅLADE
    3. make_cat_shading.py    points, tassar och form på kroppen
    4. make_cat_faces.py      ansiktet, på alla katter
    5. build_accessories.py   plaggens UV-ytor målas in igen

KÄLLAN ÄR art/kattpalsar/, inte paketet. Målas det i paketet blir en andra
körning en dubbelmålning — ränderna blir mörkare för varje gång någon råkar
köra skriptet. Originalen ligger utanför resurspaketet så de inte skeppas.
"""
import json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import render_regression as rr

RP = f"{BASE}/PurrfectCompanions_RP"
KALLA = f"{BASE}/art/kattpalsar"

# UV-YTORNA LÄSES UR GEOMETRIN, inte ur en tabell här. Ändras modellen följer
# teckningen med; en handskriven kopia hade målat ränder på fel kroppsdel.
_geo = json.load(open(f"{RP}/models/entity/katt.geo.json"))["minecraft:geometry"][0]
YTOR = {}
for _b in _geo["bones"]:
    for _c in _b.get("cubes", []):
        u, v = _c["uv"]; w, h, d = _c["size"]
        YTOR.setdefault(_b["name"], []).append(rr.faces(u, v, w, h, d))

# HUVUDET RÖRS ALDRIG. Ögon, nos och glans är uppmätta och ömtåliga — samma
# försiktighet som make_cat_textures.py tar, och av samma skäl: ett filter som
# "bara päls" råkar alltid ta med en ögonvrå förr eller senare.
MALAS = ("body", "leg0", "leg1", "leg2", "leg3", "tail")

# (ränder, bukljus, svansringar) per ras.
# EN RAGDOLL SKA INTE VARA RANDIG. Snow är helvit och Mocha är birma — vit med
# bruna points. Ränder på dem vore inte "bättre textur", det vore fel katt.
RASER = {
    "misty": dict(rand=0.80, buk=1.10, ring=True),
    "hazel": dict(rand=0.82, buk=1.10, ring=True),
    "mocha": dict(rand=None, buk=1.07, ring=False),
    "snow":  dict(rand=None, buk=1.05, ring=False),
}


def dominant(px):
    """Pälsens grundfärg = vanligaste ogenomskinliga pixeln i kroppens ytor."""
    from collections import Counter
    c = Counter()
    for f in YTOR["body"]:
        for namn, (x0, y0, w, h) in f.items():
            for y in range(int(y0), int(y0 + h)):
                for x in range(int(x0), int(x0 + w)):
                    p = px[y][x]
                    if p[3]:
                        c[p[:3]] += 1
    return c.most_common(1)[0][0]


def nara(a, b, tol=46):
    """Är pixeln pälsfärgad? Vita bringor och tassar ligger långt ifrån och
    lämnas därmed i fred utan att någon behöver lista dem."""
    return sum(abs(a[i] - b[i]) for i in range(3)) < tol * 3


def skala(p, k):
    return tuple(min(255, max(0, int(p[i] * k))) for i in range(3)) + (p[3],)


def mala(rasid, cfg):
    w, h, px = rr.read_png(f"{KALLA}/{rasid}.png")
    grund = dominant(px)
    rord = 0

    def satt(x, y, k):
        nonlocal rord
        p = px[y][x]
        if p[3] and nara(p[:3], grund):
            px[y][x] = skala(p, k); rord += 1

    for ben in MALAS:
        for f in YTOR.get(ben, []):
            for namn, (x0, y0, fw, fh) in f.items():
                x0, y0, fw, fh = int(x0), int(y0), int(fw), int(fh)
                if namn == "bottom" and ben == "body":
                    # BUKEN ÄR LJUSARE på nästan varje katt — det är det billigaste
                    # sättet att ge en enfärgad kropp volym.
                    for y in range(y0, y0 + fh):
                        for x in range(x0, x0 + fw):
                            satt(x, y, cfg["buk"])
                    continue
                if cfg["rand"] is None:
                    continue
                if ben == "body" and namn in ("east", "west"):
                    # SIDORNAS RÄNDER löper lodrätt, alltså tvärs över kroppen.
                    # Var tredje kolumn, och de yttersta raderna hoppas över så
                    # ränderna inte möter buken i en hård kant.
                    for x in range(x0, x0 + fw):
                        if (x - x0) % 3: continue
                        for y in range(y0 + 1, y0 + fh):
                            satt(x, y, cfg["rand"])
                elif ben == "body" and namn == "top":
                    # RYGGENS RÄNDER löper tvärs, alltså vinkelrätt mot ryggraden.
                    for y in range(y0, y0 + fh):
                        if (y - y0) % 3 != 1: continue
                        for x in range(x0 + 1, x0 + fw - 1):
                            satt(x, y, cfg["rand"])
                elif ben.startswith("leg") and namn in ("east", "west", "north", "south"):
                    # Benen får EN ring högt upp; fler gör dem randiga som en
                    # zebra på fyra pixlar.
                    for x in range(x0, x0 + fw):
                        satt(x, y0 + 1, cfg["rand"])
                elif ben == "tail" and cfg["ring"] and namn in ("east", "west", "north", "south"):
                    for x in range(x0, x0 + fw):
                        satt(x, y0, cfg["rand"])

    rr.write_png(f"{RP}/textures/entity/{rasid}.png", w, h, px)
    return grund, rord


if __name__ == "__main__":
    for rasid, cfg in RASER.items():
        grund, n = mala(rasid, cfg)
        vad = "ränder + buk" if cfg["rand"] else "bara buk"
        print(f"  {rasid:7s} grundfärg {grund}  {vad}  {n} pixlar")
