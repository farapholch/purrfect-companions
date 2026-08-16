#!/usr/bin/env python3
"""Bygger vakthunden — egen geometri, egen textur, eget spawnägg.

Hunden var inte vår. Den lånade vaniljas `geometry.wolf` och vargtexturen med
`controller.render.default` och utan animationer, och på Xbox föll modellen
isär: kroppen på ett ställe, huvudet på ett annat. Vaniljas varg sätts ihop av
sina EGNA animationer, och dem kan ett paket varken läsa eller lita på.

Nu äger vi hela hunden. Kuberna står i tabellen längst ner, texturen målas ur
samma tabell (så UV och bild aldrig kan glida isär), och resultatet går att
rendera och titta på innan det lämnar huset:

    python3 tools/make_dog.py

  PurrfectCompanions_RP/models/entity/hund.geo.json   geometry.hund
  PurrfectCompanions_RP/textures/entity/hund.png      64x64
  PurrfectCompanions_RP/textures/items/pc_vakthund.png  16x16 spawnägg

Måtten är i modellenheter (16 = ett block). Hunden är avsiktligt grövre än
katten: högre ben, tyngre bringa, rak svans. Med minecraft:scale 1.35 i
beteendepaketet blir den drygt ett block hög.
"""
import json, math, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import render_regression as rr

RP = f"{BASE}/PurrfectCompanions_RP"
TW = TH = 64

# --- färger -----------------------------------------------------------------
PALS      = (86, 88, 96, 255)      # mörkgrå vaktpäls
PALS_MORK = (58, 60, 68, 255)      # skuggsida
BRINGA    = (176, 178, 188, 255)   # ljus bringa och tassar
NOS       = (26, 26, 30, 255)
OGA       = (232, 176, 64, 255)    # bärnsten — vakthund, inte sällskapskatt


def fot(size):
    """Bedrocks kubutfällning: bredd 2*(djup+bredd), höjd djup+höjd."""
    w, h, d = size
    return math.ceil(2 * (d + w)), math.ceil(d + h)


# --- kuberna: (ben, origin, size, uv, färg) ---------------------------------
# Alla ben har föräldern None precis som i kattmodellen — renderaren och
# animationerna där utgår från det, och en hund som avviker i struktur skulle
# behöva egna specialfall i varje verktyg.
KUBER = [
    ("body", [-3.5, 7, -6], [7, 7, 12], [0, 0], PALS),
    ("head", [-3, 11, -9], [6, 6, 5], [0, 26], PALS),
    ("head", [-2, 11.5, -12], [4, 3.5, 3], [24, 26], PALS_MORK),   # nosparti
    ("head", [-3, 17, -8], [2, 2.5, 1], [40, 26], PALS_MORK),      # vänster öra
    ("head", [1, 17, -8], [2, 2.5, 1], [46, 26], PALS_MORK),       # höger öra
    ("leg0", [-3.5, 0, 3], [3, 7, 3], [0, 40], BRINGA),
    ("leg1", [0.5, 0, 3], [3, 7, 3], [0, 40], BRINGA),
    ("leg2", [-3.5, 0, -6], [3, 7, 3], [0, 40], BRINGA),
    ("leg3", [0.5, 0, -6], [3, 7, 3], [0, 40], BRINGA),
    ("tail", [-1, 12, 6], [2, 6, 2], [16, 40], PALS),
]
PIVOTER = {
    "body": [0, 10.5, 0],
    "head": [0, 13, -6],      # nacken, där huvudet möter kroppen
    "leg0": [-2, 7, 4.5], "leg1": [2, 7, 4.5],
    "leg2": [-2, 7, -4.5], "leg3": [2, 7, -4.5],
    "tail": [0, 12, 6],
}


def geometri():
    ben = {}
    for namn, origin, size, uv, _f in KUBER:
        ben.setdefault(namn, []).append({"origin": origin, "size": size, "uv": uv})
    g = {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": "geometry.hund",
                # MÅSTE stämma med den faktiska PNG-filen, annars läses UV i
                # fel skala och modellen blir obegriplig i spelet — servern
                # märker ingenting. Samma fälla som kattens statiska kontroll
                # redan vaktar.
                "texture_width": TW, "texture_height": TH,
                "visible_bounds_width": 2.5, "visible_bounds_height": 2,
                "visible_bounds_offset": [0, 0.75, 0],
            },
            "bones": [{"name": n, "pivot": PIVOTER[n], "cubes": c}
                      for n, c in ben.items()],
        }],
    }
    p = f"{RP}/models/entity/hund.geo.json"
    json.dump(g, open(p, "w"), indent=2)
    return p, sum(len(c) for c in ben.values()), len(ben)


def sh(c, k):
    return (min(255, int(c[0] * k)), min(255, int(c[1] * k)), min(255, int(c[2] * k)), 255)


def textur():
    px = [[(0, 0, 0, 0)] * TW for _ in range(TH)]

    def rect(x0, y0, w, h, c):
        for y in range(int(y0), int(y0 + h)):
            for x in range(int(x0), int(x0 + w)):
                if 0 <= x < TW and 0 <= y < TH:
                    px[y][x] = c

    for namn, origin, size, uv, farg in KUBER:
        w, h, d = size
        u, v = uv
        fw, fh = fot(size)
        rect(u, v, fw, fh, farg)
        rect(u, v, fw, math.ceil(d), sh(farg, 1.18))          # ovansidan ljusare
        rect(u, v + fh - 1, fw, 1, sh(farg, 0.7))             # underkanten mörkare
        if namn == "head" and size == [6, 6, 5]:
            # ANSIKTET sitter på framsidan, som i Bedrocks utfällning ligger på
            # (u+d, v+d) med storlek (bredd, höjd). Räknas den fel hamnar ögonen
            # på hjässan — och det syns först på en konsol.
            # ÖGONHÖJDEN ÄR UTRÄKNAD, inte prövad. Nospartiet (y 11.5-15) sitter
            # framför skallen (y 11-17) och skymmer allt som målas bakom det.
            # Rad fy+j täcker y 16-j..17-j, så bara fy+0 och fy+1 ligger ovanför
            # nosryggen: målade på fy+3 försvann ögonen helt bakom nosen.
            fx, fy = u + d, v + d
            rect(fx + 1, fy + 1, 1, 1, OGA)
            rect(fx + w - 2, fy + 1, 1, 1, OGA)
        if namn == "head" and size == [4, 3.5, 3]:
            # Svart nostipp. Tänderna som stod här blev ett vitt galler tvärs
            # över nosen i renderingen — en hund ska se vaksam ut, inte skrattande.
            fx, fy = u + d, v + d
            rect(fx + 1, fy, w - 2, 2, NOS)
            rect(u + d, v, w, math.ceil(d), sh(PALS_MORK, 1.05))   # nosryggen ovanifrån
    p = f"{RP}/textures/entity/hund.png"
    rr.write_png(p, TW, TH, px)
    return p


def spawnagg():
    """16x16 hundnos rakt framifrån — samma sorts ikon som katternas, i stället
    för Minecrafts standardägg (som är vad man får när spawn_egg saknas helt)."""
    N = 16
    px = [[(0, 0, 0, 0)] * N for _ in range(N)]

    def rect(x0, y0, w, h, c):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if 0 <= x < N and 0 <= y < N:
                    px[y][x] = c

    rect(3, 3, 10, 11, PALS)          # skalle
    rect(2, 1, 3, 4, PALS_MORK)       # öron
    rect(11, 1, 3, 4, PALS_MORK)
    rect(3, 3, 10, 1, sh(PALS, 1.18))
    rect(5, 7, 6, 5, PALS_MORK)       # nosparti
    rect(6, 10, 4, 2, NOS)
    rect(5, 6, 2, 2, OGA)             # bärnstensögon
    rect(9, 6, 2, 2, OGA)
    rect(3, 13, 10, 1, sh(PALS, 0.7))
    p = f"{RP}/textures/items/pc_vakthund.png"
    rr.write_png(p, N, N, px)
    return p


if __name__ == "__main__":
    p, kuber, ben = geometri()
    print(f"  {os.path.relpath(p, BASE)}: {ben} ben, {kuber} kuber, textur {TW}x{TH}")
    print(f"  {os.path.relpath(textur(), BASE)}")
    print(f"  {os.path.relpath(spawnagg(), BASE)}")
