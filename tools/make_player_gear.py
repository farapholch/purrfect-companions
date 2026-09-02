#!/usr/bin/env python3
"""Kattdräkten — fyra plagg som SPELAREN bär, inte katten.

Önskemål från barnen: "man själv som gubbe ska också ha kattutrustning". Hela
paketet har hittills bara klätt katten; ingenting har ritats på spelarkroppen,
och paketet hade inga attachables alls. Det här skriptet skapar allt som krävs:

  luva   slot.armor.head    kattöron, rosa insida
  vast   slot.armor.chest   päls med ljus mage
  byxor  slot.armor.legs
  tassar slot.armor.feet    ljusa tassar med rosa trampdynor

Skyddet motsvarar järnrustning (2/6/5/2), så dräkten är ett riktigt alternativ
och inte bara utklädnad.

TRE SAKER SOM MÅSTE STÄMMA, och som inget serverprov kan se:

1. BENNAMNEN i geometrin måste vara spelarskelettets (head, body, leftArm,
   rightArm, leftLeg, rightLeg). Fel namn = plagget hamnar i marken. Samma
   fälla som fällde vakthunden, fast på spelaren.
2. INFLATE lyfter plagget utanför kroppen. Utan den ligger tyget exakt i
   samma yta som huden och flimrar (z-fighting).
3. Attachablens `parent_setup` släcker vaniljalagret, annars syns både vår
   luva och en osynlig hjälmkontur.

Egna UV:n i egna texturer — vi behöver alltså inte gissa vaniljas
rustningsutfällning, som ändå inte går att läsa här (BDS resurspack är
avskalad).

    python3 tools/make_player_gear.py
"""
import json, math, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE); sys.path.insert(0, f"{BASE}/tools")
import render_regression as rr
from make_cat_pals import Duk, korn, blanda, skala, avst_segment, _h, ROSA, GLANS

BP = f"{BASE}/PurrfectCompanions_BP"
RP = f"{BASE}/PurrfectCompanions_RP"
TW = TH = 64          # geometrins UV-ENHETER — arket är SKALA gånger det
# FYRA TEXLAR PER ENHET sedan 3.41.0, samma mekanism som katternas pälsark:
# geometrin deklarerar 64x64, PNG:en är 256x256 och Bedrock läser den tätare.
# Innan dess bestod byxorna av tre färger och varje sida var ett färgfält —
# bredvid katterna med ny päls såg spelaren ut som en kartong.
SKALA = 4

PALS      = (150, 140, 128, 255)   # varm kattgrå — syns mot både gräs och sten
PALS_MORK = (112, 104, 95, 255)
MAGE      = (224, 218, 208, 255)   # ljus mage, bringa och tassar
ORA_IN    = (226, 140, 160, 255)   # samma rosa som katternas nos och trampdynor
DYNA      = (226, 140, 160, 255)
OGON      = (232, 176, 64, 255)    # bärnsten, samma som vakthundens
OGON_GLANS = (255, 232, 176, 255)


def fot(size):
    w, h, d = size
    return math.ceil(2 * (d + w)), math.ceil(d + h)


# NIVÅERNA. Läderdräkten är BASEN och behåller sina gamla identifierare
# (mjau:luva, mjau:vast ...) — byter man id försvinner plaggen ur inventariet
# hos alla som redan har dem, och familjen har dem sedan 3.28.0. De tre nya
# nivåerna får suffix.
#
# Skyddet stiger, men KRAFTERNA är det som gör uppgraderingen värd besväret;
# de bor i main.js och står listade här bara som dokumentation:
#
#   läder     mörkerseende · motstånd I · snabbhet I · mjuk landning
#             hel dräkt: snabbhet II + hopp, katterna omkring dig läks
#   järn      + hoppkraft i tassarna
#             hel dräkt: styrka I när en tämjd katt är i närheten
#   diamant   motstånd II · snabbhet II
#             hel dräkt: läkning I
#   netherit  + eldskydd i luvan (netherit brinner inte)
#             hel dräkt: styrka I alltid, och katterna omkring dig får motstånd
#
# Geometrin DELAS mellan nivåerna — det är samma dräkt, i annat material. Bara
# textur, ikon, skydd och slitage skiljer.
NIVAER = {
    "": {"namn": "", "skydd": 0, "slitage": 1.0, "pals": (150, 140, 128, 255),
         "mork": (112, 104, 95, 255), "ljus": (224, 218, 208, 255), "upp": None, "antal": 0},
    "jarn": {"namn": "Iron ", "skydd": 1, "slitage": 1.8, "pals": (176, 178, 186, 255),
             "mork": (128, 131, 140, 255), "ljus": (226, 228, 234, 255),
             "upp": "minecraft:iron_ingot", "antal": 5},
    "diamant": {"namn": "Diamond ", "skydd": 2, "slitage": 3.4, "pals": (94, 200, 202, 255),
                "mork": (58, 148, 156, 255), "ljus": (198, 244, 246, 255),
                "upp": "minecraft:diamond", "antal": 5},
    "netherit": {"namn": "Netherite ", "skydd": 2, "slitage": 5.0, "pals": (74, 66, 70, 255),
                 "mork": (48, 42, 46, 255), "ljus": (150, 132, 120, 255),
                 "upp": "minecraft:netherite_ingot", "antal": 1},
}
NIVAORDNING = ["", "jarn", "diamant", "netherit"]


def farga(c, niv):
    """Kubens färg översatt till nivåns palett. Kuberna är skrivna i lädrets
    färger; nivån byter ut dem så samma tabell duger till alla fyra."""
    n = NIVAER[niv]
    return {PALS: n["pals"], PALS_MORK: n["mork"], MAGE: n["ljus"],
            ORA_IN: ORA_IN, DYNA: DYNA}.get(c, c)


# (ben, origin, size, uv, färg) — spelarskelettets bennamn, inget annat duger
PLAGG = {
    "luva": {
        "slot": "slot.armor.head", "skydd": 2, "slitage": 165,
        "namn": "Cat Hood", "enchant": "armor_head",
        "kuber": [
            ("head", [-4, 24, -4], [8, 8, 8], [0, 0], PALS, 1.0),
            # ÖRONEN: hjälmkuben är inflate 1.0 och når därmed y=33, inte 32.
            # Första försöket satte öronen på 31-34 — tre av fyra enheter låg
            # INUTI hjälmen och kvar syntes en stump. Xbox-rapport: "inga
            # öron". De börjar nu ovanför hjälmens topp och är 5 höga.
            ("head", [-4.5, 32, -2.5], [3, 5, 1], [40, 0], PALS_MORK, 0.0),  # vänster öra
            ("head", [1.5, 32, -2.5], [3, 5, 1], [46, 0], PALS_MORK, 0.0),   # höger öra
            ("head", [-3.8, 33.4, -2.9], [1.6, 3, 0.6], [40, 12], ORA_IN, 0.0),
            ("head", [2.2, 33.4, -2.9], [1.6, 3, 0.6], [46, 12], ORA_IN, 0.0),
        ],
    },
    "vast": {
        "slot": "slot.armor.chest", "skydd": 6, "slitage": 240,
        "namn": "Cat Vest", "enchant": "armor_torso",
        "kuber": [
            # BÅLEN SMALARE ÄN ÄRMARNA. Med bål 1.01 och ärm 1.0 låg ytorna i
            # samma plan och de växte ihop till en bred platta ("man har typ
            # inga armar"). Nu buktar ärmen längre ut än bålen åt alla håll,
            # så det finns en synlig avsats där armen börjar.
            ("body", [-4, 12, -2], [8, 12, 4], [0, 0], PALS, 0.5),
            ("body", [-2.5, 12.5, -2.6], [5, 8, 1], [26, 0], MAGE, 0.0),      # ljus bringa
            # HELA ÄRMAR, men tydliga. Två försök gick fel före det här: först
            # ärmar kant i kant med bålen (allt blev en platta), sedan ärmlös
            # väst med bara axelstycken — men önskemålet är en RIKTIG kropp
            # med tydliga armar, inte bar hud.
            #
            # Tre saker skiljer dem åt nu: ärmen buktar mer än bålen (1.15 mot
            # 0.7) så det finns en avsats, den är i den mörkare tonen, och den
            # får en ljus manschett vid handleden så armen har ett slut.
            # SMALARE. 1.15 mot bålens 0.7 gav en tydlig avsats men en bred,
            # klumpig siluett — axlarna blev bredare än en vanlig spelares.
            # Nu bär FÄRGEN och MANSCHETTEN skillnaden (bevisat på Xbox), så
            # utbuktningen behöver bara vara precis så stor att armen ligger
            # utanför bålen: 0.75 mot 0.5. Under ~0.4 börjar plagget flimra
            # mot spelarens egen hud, så längre ner än så går det inte.
            ("leftArm", [4, 12, -2], [4, 12, 4], [40, 0], PALS_MORK, 0.75),
            ("rightArm", [-8, 12, -2], [4, 12, 4], [40, 20], PALS_MORK, 0.75),
        ],
    },
    "byxor": {
        "slot": "slot.armor.legs", "skydd": 5, "slitage": 225,
        "namn": "Cat Trousers", "enchant": "armor_legs",
        "kuber": [
            ("body", [-4, 12, -2], [8, 12, 4], [0, 0], PALS_MORK, 0.55),
            ("leftLeg", [0, 0, -2], [4, 12, 4], [28, 0], PALS_MORK, 0.55),
            ("rightLeg", [-4, 0, -2], [4, 12, 4], [28, 20], PALS_MORK, 0.55),
        ],
    },
    "tassar": {
        "slot": "slot.armor.feet", "skydd": 2, "slitage": 195,
        "namn": "Cat Paws", "enchant": "armor_feet",
        "kuber": [
            # FÖTTERNA satt ihop. Benen ligger kant i kant (x 0..4 och -4..0),
            # så VARJE enhet utbuktning får tassarna att överlappa i mitten —
            # med 1.0 möttes de två enheter in i varandra och blev ett enda
            # vitt block. Xbox-bild: "fötterna smälter ihop". 0.55 räcker för
            # att ligga utanför benet utan att korsa mittlinjen nämnvärt, och
            # insidorna mörkas i texturen så skarven syns.
            ("leftLeg", [0, 0, -2], [4, 5, 4], [0, 0], MAGE, 0.55),
            ("rightLeg", [-4, 0, -2], [4, 5, 4], [0, 14], MAGE, 0.55),
            ("leftLeg", [0.6, -0.1, -2.6], [2.8, 1, 1], [28, 0], DYNA, 0.0),   # trampdynor
            ("rightLeg", [-3.4, -0.1, -2.6], [2.8, 1, 1], [28, 4], DYNA, 0.0),
        ],
    },
}


def ident(namn, niv):
    """Basen behåller sitt gamla id — se kommentaren vid NIVAER."""
    return namn if not niv else f"{namn}_{niv}"


def sh(c, k):
    return tuple(min(255, int(v * k)) for v in c[:3]) + (255,)


def geometri(namn, cfg):
    ben = {}
    for b, origin, size, uv, _f, inflate in cfg["kuber"]:
        kub = {"origin": origin, "size": size, "uv": uv}
        if inflate:
            kub["inflate"] = inflate
        ben.setdefault(b, []).append(kub)
    PIVOT = {"head": [0, 24, 0], "body": [0, 24, 0],
             "leftArm": [5, 22, 0], "rightArm": [-5, 22, 0],
             "leftLeg": [1.9, 12, 0], "rightLeg": [-1.9, 12, 0]}
    g = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": f"geometry.mjau_{namn}",
                        "texture_width": TW, "texture_height": TH,
                        "visible_bounds_width": 2, "visible_bounds_height": 3,
                        "visible_bounds_offset": [0, 1.5, 0]},
        "bones": [{"name": b, "pivot": PIVOT[b], "cubes": k} for b, k in ben.items()]}]}
    json.dump(g, open(f"{RP}/models/entity/mjau_{namn}.geo.json", "w"), indent=2)
    return len(ben), len(cfg["kuber"])


def textur(namn, cfg, niv):
    """Dräktens ark. Läderdräkten är en tabbykatt (ringar runt kropp, armar och
    ben, M i pannan, ränder över hjässan); metallnivåerna behåller pälsen i
    nivåns ton och får PLÅTAR på: pannband, bröstplåt, axelkappor, bälte,
    knäskydd och tåhättor. Så syns det på avstånd vilken nivå någon bär."""
    n = NIVAER[niv]
    duk = Duk(TW * SKALA, TH * SKALA)
    pals, mork, ljus = n["pals"][:3], n["mork"][:3], n["ljus"][:3]
    metall = bool(niv)
    rand = None if metall else blanda(mork, (0, 0, 0), 0.30)
    plat = blanda(ljus, pals, 0.35)
    plat_ljus, plat_mork = blanda(plat, (255, 255, 255), 0.35), blanda(plat, (0, 0, 0), 0.40)
    OG_MORK = (150, 100, 20)

    def ytor(uv, size):
        return {k: tuple(v * SKALA for v in r)
                for k, r in rr.faces(uv[0], uv[1], *size).items()}

    def pals_fn(bas, ringar=False, ring_rader=(0.30, 0.62)):
        def fn(a, b, x, y):
            c = skala(bas, 1.06 - 0.16 * b)
            if rand and ringar:
                for rb in ring_rader:
                    if abs(b - rb + 0.02 * math.sin(a * 9)) < 0.045 and not (_h(x, y, 5) < 0.2):
                        c = blanda(rand, c, 0.2)
            return korn(c, x, y)
        return fn

    def plat_fn(rekt, nitar=True):
        X0, Y0, FW, FH = rekt

        def fn(a, b, x, y):
            X, Y = a * FW, b * FH
            c = plat
            if X < 1.5 or Y < 1.5:
                c = plat_ljus
            elif X > FW - 1.5 or Y > FH - 1.5:
                c = plat_mork
            if nitar:
                for nx in (3.0, FW - 3.0):
                    for ny in (3.0, FH - 3.0):
                        if abs(X - nx) < 1.0 and abs(Y - ny) < 1.0:
                            c = plat_mork
            return korn(c, x, y, 0.3)
        return fn

    def band(fn_pals, fn_plat, villkor):
        """Plåt där villkor(a, b) gäller, päls annars."""
        return lambda a, b, x, y: (fn_plat(a, b, x, y) if villkor(a, b) else fn_pals(a, b, x, y))

    for b_, origin, size, uv, farg0, _i in cfg["kuber"]:
        farg = farga(farg0, niv)[:3]
        F = ytor(uv, size)
        w, h, d = size
        SIDOR = ("north", "south", "east", "west")

        if namn == "luva" and size == [8, 8, 8]:
            # HJÄSSAN: ränder längs huvudet på läderdräkten, pannband på metall.
            def hjassa(a, b, x, y):
                c = skala(farg, 1.06)
                if rand:
                    for ca in (0.2, 0.5, 0.8):
                        if abs(a - ca) < 0.045 + 0.02 * math.sin(b * 9 + ca * 5) and b > 0.1:
                            c = blanda(rand, c, 0.15)
                return korn(c, x, y)
            duk.yta(F["top"], hjassa, 255)
            duk.yta(F["bottom"], lambda a, b, x, y: korn(skala(farg, 0.7), x, y), 255)
            for sida in ("east", "west", "south"):
                fn = pals_fn(farg)
                if metall:
                    fn = band(fn, plat_fn(F[sida], nitar=False), lambda a, b: b < 0.2)
                duk.yta(F[sida], fn, 255)
            # ANSIKTET, samma anatomi som katternas: mandelögon med kant, iris
            # i bärnsten, lodrät pupill och glans, rosa nos och ett ω-leende.
            X0, Y0, FW, FH = F["north"]
            OGON_C = [(FW * 0.25, FH * 0.42, +1), (FW * 0.75, FH * 0.42, -1)]
            RX, RY = FW * 0.11, FH * 0.15
            mork_ans = blanda(farg, (0, 0, 0), 0.75)
            nosparti = blanda(farg, (255, 255, 255), 0.30)
            mun = blanda(mork_ans, (150, 108, 104), 0.55)

            def ansikte(a, b, x, y):
                X, Y = a * FW, b * FH
                c = farg
                if metall and b < 0.2:
                    return plat_fn(F["north"], nitar=False)(a, b, x, y)
                if abs(a - 0.5) < 0.2 and b > 0.5:
                    c = blanda(c, nosparti, min(1.0, (b - 0.5) / 0.25))
                if rand and b < 0.36:
                    m = [((8, 11), (12, 3)), ((12, 3), (16, 9)), ((16, 9), (20, 3)), ((20, 3), (24, 11))]
                    m = [((p[0] * FW / 32, p[1] * FH / 32), (q[0] * FW / 32, q[1] * FH / 32)) for p, q in m]
                    if min(avst_segment(X, Y, *p, *q) for p, q in m) < 0.8:
                        c = blanda(rand, c, 0.15)
                for cx, cy, _ in OGON_C:
                    if abs(X - cx) < RX + 0.6 and Y < cy - RY:
                        c = blanda(c, mork_ans, 0.28 * max(0.0, 1 - (cy - RY - Y) / (FH * 0.15)))
                # morrhårsprickar
                if abs(b - 0.62) < 0.05 and (a < 0.12 or a > 0.88) and _h(x, y, 7) < 0.5:
                    c = blanda(c, (255, 255, 255), 0.35)
                c = korn(c, x, y, 0.7)
                # nosen och munnen
                if abs(X - FW / 2) < 2.6 - (Y - FH * 0.55) * 0.9 and FH * 0.55 <= Y < FH * 0.68:
                    return ROSA
                if abs(X - FW / 2) < 0.9 and FH * 0.66 <= Y < FH * 0.76:
                    return mun
                if FH * 0.74 <= Y < FH * 0.80 and abs(X - FW / 2) < FW * 0.10:
                    return mun
                if FH * 0.69 <= Y < FH * 0.76 and FW * 0.09 < abs(X - FW / 2) < FW * 0.15:
                    return mun
                for cx, cy, inat in OGON_C:
                    dx, dy = (X - cx) / RX, (Y - cy) / RY
                    r = math.hypot(dx, dy)
                    if r > 1.0:
                        continue
                    if r > 0.86:
                        return mork_ans
                    iris = blanda(OGON[:3], OG_MORK, max(0.0, min(1.0, 0.15 + 0.55 * (dy + 1) / 2)))
                    if abs(X - cx) < 0.75 and abs(Y - cy) < RY * 0.70:
                        iris = blanda(OG_MORK, (0, 0, 0), 0.75)
                    if math.hypot(X - (cx + inat * RX * 0.42), Y - (cy - RY * 0.42)) < 1.15:
                        iris = GLANS
                    return iris
                return c
            duk.yta(F["north"], ansikte, 255)
            continue

        if farg0 == ORA_IN or farg0 == DYNA:
            # inneröron och trampdynor: rosa, en aning mörkare nedåt
            for sida in F:
                duk.yta(F[sida], lambda a, b, x, y: blanda(farg, (0, 0, 0), 0.12 * b), 255)
            continue

        if namn == "luva":                                      # öronen
            for sida in F:
                fn = pals_fn(farg)
                if metall:
                    fn = band(fn, plat_fn(F[sida], nitar=False), lambda a, b: b < 0.25)
                duk.yta(F[sida], fn, 255)
            continue

        if namn == "vast" and farg0 == MAGE:                    # bringan
            for sida in F:
                fn = plat_fn(F[sida]) if metall else pals_fn(farg)
                duk.yta(F[sida], fn, 255)
            continue

        # KROPP, ARMAR, BEN, FÖTTER — päls med ringar på lädret, plåtar på metall.
        for sida in ("top", "bottom"):
            fn = pals_fn(farg)
            if metall and namn == "tassar" and sida == "top":
                fn = band(fn, plat_fn(F[sida], nitar=False), lambda a, b: b < 0.5)
            duk.yta(F[sida], fn, 255)
        for sida in SIDOR:
            rekt = F[sida]
            fn = pals_fn(farg, ringar=(namn != "tassar"))       # tassar är ljusa, inte randiga
            if metall:
                if b_ == "body" and namn == "byxor":
                    fn = band(fn, plat_fn(rekt, nitar=False), lambda a, b: b < 0.14)     # bälte
                elif b_ in ("leftArm", "rightArm"):
                    fn = band(fn, plat_fn(rekt), lambda a, b: b < 0.27)                 # axelkappa
                elif b_ in ("leftLeg", "rightLeg") and namn == "byxor" and sida == "north":
                    fn = band(fn, plat_fn(rekt), lambda a, b: 0.40 < b < 0.62)          # knäskydd
                elif namn == "tassar" and sida == "north":
                    fn = band(fn, plat_fn(rekt, nitar=False), lambda a, b: b < 0.38)    # tåhätta

            def kant(fn0, sida=sida, rekt=rekt):
                X0, Y0, FW, FH = rekt

                def fn2(a, b, x, y):
                    X, Y = a * FW, b * FH
                    c = fn0(a, b, x, y)
                    if b_ in ("leftLeg", "rightLeg") and sida in ("north", "south") and (X < 1.5 or X > FW - 1.5):
                        return blanda(c, (0, 0, 0), 0.30)        # skarven mellan benen
                    if b_ in ("leftArm", "rightArm") and b > 0.84:
                        return korn(blanda(ljus, c, 0.25), x, y)  # manschett
                    if namn == "tassar" and sida == "north" and b > 0.78 and (abs(a - 0.33) < 0.05 or abs(a - 0.67) < 0.05):
                        return blanda(c, (0, 0, 0), 0.2)         # tåspringor
                    return c
                return fn2
            duk.yta(rekt, kant(fn), 255)

    rr.write_png(f"{RP}/textures/entity/mjau_{ident(namn, niv)}.png", TW * SKALA, TH * SKALA, duk.px)


def attachable(namn, cfg, niv):
    """Utan attachable BÄRS plagget men syns inte — bara ikonen i rutan."""
    d = {"format_version": "1.10.0", "minecraft:attachable": {"description": {
        "identifier": f"mjau:{ident(namn, niv)}",
        "materials": {"default": "armor", "enchanted": "armor_enchanted"},
        "textures": {"default": f"textures/entity/mjau_{ident(namn, niv)}",
                     "enchanted": "textures/misc/enchanted_item_glint"},
        "geometry": {"default": f"geometry.mjau_{namn}"},
        # släck vaniljalagret för samma plats, annars ritas två plagg
        "scripts": {"parent_setup": f"variable.{ {'luva':'helmet','vast':'chest','byxor':'leg','tassar':'boot'}[namn] }_layer_visible = 0.0;"},
        "render_controllers": ["controller.render.armor"]}}}
    json.dump(d, open(f"{RP}/attachables/{ident(namn, niv)}.json", "w"), indent=2)


def ikon(namn, cfg, niv):
    PALS, PALS_MORK, MAGE = (NIVAER[niv]["pals"], NIVAER[niv]["mork"], NIVAER[niv]["ljus"])
    N = 16
    px = [[(0, 0, 0, 0)] * N for _ in range(N)]

    def rect(x0, y0, w, h, c):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if 0 <= x < N and 0 <= y < N:
                    px[y][x] = c
    if namn == "luva":
        rect(3, 4, 10, 9, PALS); rect(2, 1, 3, 4, PALS_MORK); rect(11, 1, 3, 4, PALS_MORK)
        rect(3, 2, 1, 2, ORA_IN); rect(12, 2, 1, 2, ORA_IN)
        rect(5, 8, 2, 2, (40, 40, 46, 255)); rect(9, 8, 2, 2, (40, 40, 46, 255))
        rect(3, 4, 10, 1, sh(PALS, 1.14))
    elif namn == "vast":
        rect(4, 3, 8, 10, PALS); rect(2, 4, 2, 6, PALS); rect(12, 4, 2, 6, PALS)
        rect(6, 5, 4, 6, MAGE); rect(4, 3, 8, 1, sh(PALS, 1.14))
    elif namn == "byxor":
        rect(4, 2, 8, 5, PALS_MORK); rect(4, 7, 3, 7, PALS_MORK); rect(9, 7, 3, 7, PALS_MORK)
        rect(4, 2, 8, 1, sh(PALS_MORK, 1.14))
    else:
        rect(3, 6, 4, 7, MAGE); rect(9, 6, 4, 7, MAGE)
        rect(3, 11, 4, 2, DYNA); rect(9, 11, 4, 2, DYNA)
        rect(3, 6, 4, 1, sh(MAGE, 1.14)); rect(9, 6, 4, 1, sh(MAGE, 1.14))
    rr.write_png(f"{RP}/textures/items/pc_{ident(namn, niv)}.png", N, N, px)


# --- föremål och recept -----------------------------------------------------
# Läder och ull, samma material som kattens egna plagg — dräkten hör ihop med
# resten av paketet och kräver inget nytt som barnen inte redan har.
MONSTER = {
    "luva":   ["WLW", "L L"],
    "vast":   ["L L", "LWL", "LLL"],
    # ULLEN I TOPPEN är inte pynt: rent läder ger EXAKT vaniljas recept för
    # läderbyxor, och då hade spelaren fått vaniljabyxorna i stället för våra.
    # Granskningen (audit.py mot en vaniljakopia) fångade det.
    "byxor":  ["LWL", "L L", "L L"],
    "tassar": ["L L", "W W"],
}


def foremal(namn, cfg, niv):
    n = NIVAER[niv]
    json.dump({"format_version": "1.20.50", "minecraft:item": {
        "description": {"identifier": f"mjau:{ident(namn, niv)}",
                        "menu_category": {"category": "equipment"}},
        "components": {
            "minecraft:icon": {"texture": f"pc_{ident(namn, niv)}"},
            "minecraft:display_name": {"value": n["namn"] + cfg["namn"]},
            "minecraft:max_stack_size": 1,
            "minecraft:wearable": {"slot": cfg["slot"],
                                   "protection": cfg["skydd"] + n["skydd"]},
            "minecraft:durability": {"max_durability": int(cfg["slitage"] * n["slitage"])},
            "minecraft:repairable": {"repair_items": [
                {"items": ["minecraft:leather"], "repair_amount": 25}]},
            "minecraft:enchantable": {"slot": cfg["enchant"], "value": 9},
        }}}, open(f"{BP}/items/{ident(namn, niv)}.json", "w"), indent=2)
    if niv:
        # UPPGRADERING, inte nytillverkning: nivån under plus material. Kan
        # aldrig krocka med ett vaniljarecept eftersom vårt eget plagg ingår.
        forra = NIVAORDNING[NIVAORDNING.index(niv) - 1]
        ing = [{"item": f"mjau:{ident(namn, forra)}"}] + \
              [{"item": n["upp"]} for _ in range(n["antal"])]
        json.dump({"format_version": "1.20.10", "minecraft:recipe_shapeless": {
            "description": {"identifier": f"mjau:{ident(namn, niv)}"},
            "tags": ["crafting_table"],
            "ingredients": ing,
            "unlock": [{"item": n["upp"]}],
            "result": {"item": f"mjau:{ident(namn, niv)}"}}},
            open(f"{BP}/recipes/{ident(namn, niv)}.json", "w"), indent=2)
        return
    json.dump({"format_version": "1.20.10", "minecraft:recipe_shaped": {
        "description": {"identifier": f"mjau:{namn}"},
        "tags": ["crafting_table"],
        "pattern": MONSTER[namn],
        "key": {"L": {"item": "minecraft:leather"}, "W": {"item": "minecraft:white_wool"}},
        # UNLOCK KRÄVS sedan format 1.20: utan den vägrar servern receptet med
        # "1.20+ Recipes require unlock data" — och receptet finns då helt
        # enkelt inte i spelet, fast filen ligger på plats och JSON:en är giltig.
        # Fångades av innehållsloggen, inte av någon av de statiska kollarna.
        "unlock": [{"item": "minecraft:leather"}],
        "result": {"item": f"mjau:{namn}"}}},
        open(f"{BP}/recipes/{namn}.json", "w"), indent=2)


def forhandsbild():
    """publish/06-kattdrakt.png — hela dräkten monterad, en kolumn per nivå,
    med ikonerna under.

    Delarna renderas var för sig (varje plagg har egen textur) men med SAMMA
    kamera och samma ram, så de landar på rätt plats i förhållande till
    varandra och kan läggas ovanpå varandra. Bakgrunden nycklas bort.

    KUBERNA FÅR INTE SKALAS: renderaren räknar texturytorna ur kubens mått, så
    en nedskalad kub läser fel del av bilden — det gav ett ansiktslöst huvud i
    en tidigare förhandsbild fast texturen var rätt. Ramen vidgas i stället.
    """
    import render_preview as rp
    RAM = ((-10, 10), (0, 38), (-10, 10))       # spelarens hela höjd
    RUTA = 320
    K, N = 3, 16
    kolumner = []
    for niv in NIVAORDNING:
        lager = None
        for namn in PLAGG:
            g = json.load(open(f"{RP}/models/entity/mjau_{namn}.geo.json"))["minecraft:geometry"][0]
            ben = []
            for b in g["bones"]:
                kub = []
                for c in b["cubes"]:
                    # INFLATE SLÄNGS, den kompenseras INTE genom att kuben görs
                    # större. Minecraft blåser upp lådan utan att röra UV:n,
                    # men vår renderare räknar texturytan ur kubens MÅTT — en
                    # kub som gjorts 10 bred läser ett 10 px brett fönster ur
                    # en textur som ritats för 8. Ansiktet hamnade då ur led
                    # och rapporterades som "ögonen sitter snett", fast bilden
                    # på disk var spegelsymmetrisk. En enhets skillnad i
                    # tjocklek syns ändå inte i en förhandsbild.
                    k = dict(c)
                    k.pop("inflate", None)
                    kub.append(k)
                ben.append((b["name"], b["pivot"], kub))
            rr.bones_for = lambda acc, _l=ben: _l
            vy = rr.render(f"mjau_{ident(namn, niv)}", [], {}, W=RUTA, H=RUTA,
                           yaw=10, pitch=3, ram=RAM, enheter=(TW, TH))
            if lager is None:
                lager = [list(r) for r in vy]
                bg = vy[0][0]
            else:
                for y in range(RUTA):
                    for x in range(RUTA):
                        p2 = vy[y][x]
                        if p2 != bg:
                            lager[y][x] = p2
        kolumner.append(lager)

    bred, hojd = len(kolumner) * RUTA, RUTA + N * K + 20
    ark = [[(24, 27, 36, 255)] * bred for _ in range(hojd)]
    for ci, kol in enumerate(kolumner):
        for y in range(RUTA):
            for x in range(RUTA):
                ark[y][ci * RUTA + x] = kol[y][x]
        for pi, namn in enumerate(PLAGG):
            w, h, px = rr.read_png(f"{RP}/textures/items/pc_{ident(namn, NIVAORDNING[ci])}.png")
            ox = ci * RUTA + 12 + pi * (N * K + 8)
            for y in range(h):
                for x in range(w):
                    q = px[y][x]
                    if len(q) > 3 and q[3] == 0:
                        continue
                    for dy in range(K):
                        for dx in range(K):
                            ark[RUTA + 10 + y * K + dy][ox + x * K + dx] = (q[0], q[1], q[2], 255)
    rr.write_png(f"{BASE}/publish/06-kattdrakt.png", bred, hojd, ark)
    print(f"  publish/06-kattdrakt.png ({bred}x{hojd}) — läder, järn, diamant, netherit")


if __name__ == "__main__":
    os.makedirs(f"{RP}/attachables", exist_ok=True)
    it = json.load(open(f"{RP}/textures/item_texture.json"))
    for namn, cfg in PLAGG.items():
        ben, kuber = geometri(namn, cfg)          # geometrin delas av alla nivåer
        for niv in NIVAORDNING:
            textur(namn, cfg, niv)
            attachable(namn, cfg, niv)
            ikon(namn, cfg, niv)
            foremal(namn, cfg, niv)
            i = ident(namn, niv)
            it["texture_data"][f"pc_{i}"] = {"textures": f"textures/items/pc_{i}"}
        print(f"  {cfg['namn']:14} {cfg['slot']:18} "
              f"skydd {cfg['skydd']}-{cfg['skydd'] + NIVAER['netherit']['skydd']}  "
              f"{ben} ben, {kuber} kuber, {len(NIVAORDNING)} nivåer")
    json.dump(it, open(f"{RP}/textures/item_texture.json", "w"), indent=2)
    print("  item_texture.json uppdaterad")
    forhandsbild()
