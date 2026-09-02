#!/usr/bin/env python3
"""Målar katternas PÄLS — hela pälsarket, FYRA TEXLAR PER MODELLENHET.

Bakgrund: fyra versioner (3.36–3.39) la teckningar, points, skuggning och
pälskorn på katterna, och allt mättes grönt. Men modellen ritades i EN texel per
enhet: bålens sida var 10x5 texlar, benen 2x4. På den ytan kan ingen måla päls,
hur skickligt det än görs — ränderna fick bli varannan-tredje kolumn för att det
inte fanns plats för mer. Det var det taket spelarna såg, inte målningen.

Pälsen har därför ett EGET ark nu, `textures/entity/<katt>_pals.png`, i SKALA
gånger geometrins upplösning. Plaggen bor kvar i det gamla 256-atlaset; de är
egna geometrier med egen render controller och rörs inte.

    python3 tools/make_cat_pals.py

HUR SKALAN FUNGERAR I BEDROCK: geometrins texture_width/height är UV-enheter,
inte pixlar. Är PNG:en större än det deklarerade läses den tätare — det är så
alla HD-paket fungerar. geometry.katt säger 128x32 enheter (build_accessories
äger det), arket är 512x128, och varje uv-tal i geometrin är oförändrat.

EN TABELL ÄGER VARJE KATT. Förut var Ginger en transform av Misty, Domino en av
Hazel, Midnight och Spökkatten av Misty igen, och fyra skript målade ovanpå
varandra i en körordning som bara stod i docstrings. Nu står varje katts färger
och drag i KATTER nedan och allt målas från en tom duk. Det gör skriptet
idempotent av konstruktion: det läser aldrig en texel det själv skrivit.

ARK UTIFRÅN. Finns `art/pals/<katt>.png` (samma mått som arket) kopieras det i
stället för att generera — det är vägen in för en konstnär som målat på mallen
från tools/make_art_template.py.

UV-YTORNA LÄSES UR GEOMETRIN. Ändras modellen följer pälsen med. Kanter som
ligger mellan två texlar (öronen börjar på 33,3) hanteras som förut: grundfärg
täcker utåt, detaljer läggs inåt.
"""
import json, math, os, shutil, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import render_regression as rr

RP = f"{BASE}/PurrfectCompanions_RP"
ART = f"{BASE}/art/pals"
SKALA = 4

ROSA = (226, 140, 160)          # nos och inneröra
GLANS = (255, 255, 255)
VIT = (247, 247, 244)           # bringor, tassar, handskar
TASSROSA = (214, 128, 142)      # trampdynor

# ------------------------------------------------------------------ katterna
# pals      grundpäls på bålen            huvud    huvudets färg (None = pals)
# buk       ljusare buk                   rand     teckningsfärg (None = ej tabby)
# points    öron/ben/svans (None = inga)  bringa   vit bringa på bröstet
# tassar    vita tassar (halva benet)     handskar vita handskar (bara foten)
# magrander ljusa ränder på buken         stjarna  märke på hjässan
# iris/iris_mork ögonfärger · alfa pälsens alfa · ogon_alfa ögonens alfa
KATTER = {
    "misty":    dict(pals=(154, 160, 166), buk=(171, 177, 183), rand=(112, 117, 122),
                     iris=(122, 201, 67), iris_mork=(67, 110, 36)),
    "hazel":    dict(pals=(138, 106, 69), buk=(151, 116, 75), rand=(106, 80, 51),
                     bringa=True, tassar=True,
                     iris=(122, 201, 67), iris_mork=(67, 110, 36)),
    "mocha":    dict(pals=VIT, buk=(250, 250, 248), huvud=(107, 74, 53),
                     points=(107, 74, 53), handskar=True, magrander=(196, 170, 142),
                     iris=(79, 168, 224), iris_mork=(43, 92, 123)),
    "snow":     dict(pals=VIT, buk=(252, 252, 250), points=(176, 182, 190),
                     handskar=True,
                     iris=(79, 168, 224), iris_mork=(43, 92, 123)),
    "ginger":   dict(pals=(176, 93, 44), buk=(192, 108, 56), rand=(140, 72, 34),
                     iris=(122, 201, 67), iris_mork=(67, 110, 36)),
    "domino":   dict(pals=(42, 42, 52), buk=(50, 50, 61), bringa=True, tassar=True,
                     iris=(122, 201, 67), iris_mork=(67, 110, 36)),
    "midnight": dict(pals=(27, 25, 38), buk=(34, 32, 46),
                     iris=(255, 196, 64), iris_mork=(160, 112, 28)),
    "aurora":   dict(pals=(237, 242, 244), buk=(242, 246, 248),
                     iris=(170, 235, 240), iris_mork=(110, 200, 210)),
    "nova":     dict(pals=(19, 17, 33), buk=(26, 24, 42), stjarna=(150, 170, 230),
                     iris=(200, 235, 255), iris_mork=(140, 200, 255)),
    "spokkatt": dict(pals=(221, 225, 255), buk=(229, 232, 255), alfa=150, ogon_alfa=235,
                     iris=(140, 255, 230), iris_mork=(90, 200, 180)),
}

# ------------------------------------------------------------------ geometri
_geo = [g for g in json.load(open(f"{RP}/models/entity/katt.geo.json"))["minecraft:geometry"]
        if g["description"]["identifier"] == "geometry.katt"][0]
ENHETER = (_geo["description"]["texture_width"], _geo["description"]["texture_height"])
BEN = {b["name"]: b.get("cubes", []) for b in _geo["bones"]}
_head = BEN["head"]
SKALLE = max(_head, key=lambda c: c["size"][0] * c["size"][1])
NOS = min(_head, key=lambda c: c["origin"][2])
_topp = SKALLE["origin"][1] + SKALLE["size"][1]
ORON = [c for c in _head if c is not NOS and c["origin"][1] >= _topp - 0.5]
KINDER = [c for c in _head if c is not NOS and c not in ORON and c is not SKALLE]
SVANS = max(BEN["tail"], key=lambda c: c["size"][1])     # tre kuber delar en uv-ruta


def ytor(kub):
    """Kubens sex ytor i TEXLAR (uv-enheter gånger SKALA)."""
    F = rr.faces(kub["uv"][0], kub["uv"][1], *kub["size"])
    return {n: tuple(v * SKALA for v in r) for n, r in F.items()}


def tacker(f0, fl):
    return int(math.floor(f0 + 1e-6)), int(math.ceil(f0 + fl - 1e-6))


# ------------------------------------------------------------------ färg
def klamp(c):
    return tuple(max(0, min(255, int(round(v)))) for v in c[:3])


def blanda(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def skala(c, k):
    return klamp(tuple(v * k for v in c))


def lum(c):
    return (c[0] * 3 + c[1] * 5 + c[2] * 2) / 10


def _h(x, y, s=0):
    """Deterministiskt brus i 0..1 — samma varje bygge, så det går att resonera om."""
    v = (x * 374761393 + y * 668265263 + s * 982451653) & 0xFFFFFFFF
    v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((v ^ (v >> 16)) & 0xFFFF) / 65535.0


def korn(c, x, y, k=1.0):
    """Pälskorn: fint brus per texel plus grövre tussar. Amplituden följer
    ljusheten så en svart katt får synligt korn utan att en vit blir smutsig."""
    amp = (4 + 0.025 * lum(c)) * k
    n = (_h(x, y) - 0.5) * 2 * amp + (_h(x // 3, y // 3, 1) - 0.5) * 2 * amp * 0.6
    return klamp((c[0] + n, c[1] + n, c[2] + n))


def avst_segment(px_, py_, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px_ - ax) * dx + (py_ - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px_ - (ax + t * dx), py_ - (ay + t * dy))


def i_stjarna(dx, dy, r_ut, r_in, uddar=5):
    r = math.hypot(dx, dy)
    if r == 0:
        return True
    f = ((math.atan2(dy, dx) + math.pi / 2) * uddar / (2 * math.pi)) % 1.0
    tri = abs(f * 2 - 1)                       # 0 vid udd, 1 i dalen
    return r <= r_in + (r_ut - r_in) * (1 - tri)


# ------------------------------------------------------------------ målning
class Duk:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [[(0, 0, 0, 0)] * w for _ in range(h)]

    def yta(self, rekt, fn, alfa):
        """Kör fn(a, b, x, y) över ytan; a/b är 0..1 tvärs/nedåt, x/y texlar.
        fn returnerar RGB eller None (rör inte texeln)."""
        X0, Y0, FW, FH = rekt
        xa, xb = tacker(X0, FW)
        ya, yb = tacker(Y0, FH)
        for y in range(max(0, ya), min(self.h, yb)):
            for x in range(max(0, xa), min(self.w, xb)):
                c = fn((x + 0.5 - X0) / FW, (y + 0.5 - Y0) / FH, x, y)
                if c is not None:
                    self.px[y][x] = tuple(c) + (alfa,)


def mala(namn, K):
    W, H = ENHETER[0] * SKALA, ENHETER[1] * SKALA
    duk = Duk(W, H)
    pals = K["pals"]
    huvud = K.get("huvud") or pals
    buk = K.get("buk") or skala(pals, 1.08)
    rand = K.get("rand")
    points = K.get("points")
    oron = points or huvud
    alfa = K.get("alfa", 255)
    ogon_alfa = K.get("ogon_alfa", alfa)
    mork = blanda(huvud, (0, 0, 0), 0.80)
    # Nospartiet är ljusare än pälsen på varje katt — det är kontrasten som gör
    # att nosen läser som en nos och inte som en bula. Bringkatterna har vitt.
    nosparti = VIT if K.get("bringa") else blanda(huvud, (255, 255, 255), 0.30)
    mun = blanda(mork, (150, 108, 104), 0.55)
    tass_vit = K.get("tassar") or K.get("handskar")

    # ---------------------------------------------------------------- bålen
    B = ytor(BEN["body"][0])
    RANDER = 6                                  # ränder längs bålen

    def rand_pa(a, b, x, y, hw_bas, bmax, fas):
        """Är texeln på en tabbyrand? Ränderna vaggar lite och tunnar ut mot
        buken, och kanten är bruten så de inte ser ritade med linjal ut."""
        if not rand or b > bmax:
            return False
        FW = B["east"][2]
        for k in range(RANDER):
            # Mjuk böj, inte slingor: första försöket vaggade 1,2 texlar var
            # elfte rad och ränderna blev S-formade sömmar i stället för päls.
            cx = (k + 0.5) / RANDER * FW + 0.7 * math.sin(y * 0.28 + k * 1.7 + fas)
            hw = hw_bas - 0.45 * b
            d = abs((a * FW) - cx)
            if d < hw and not (d > hw - 0.5 and _h(x, y, 3) < 0.30):
                return True
        return False

    def sida(a, b, x, y):
        c = skala(pals, 1.08 - 0.24 * b)        # ljus uppifrån, mörkare nedåt
        if b > 0.85:
            c = blanda(c, buk, (b - 0.85) / 0.15)
        if rand_pa(a, b, x, y, 1.35, 0.78, 0.0):
            c = blanda(rand, c, 0.15 + 0.5 * max(0, b - 0.5))
        return korn(c, x, y)

    duk.yta(B["east"], sida, alfa)
    duk.yta(B["west"], sida, alfa)

    def rygg(a, b, x, y):
        c = skala(pals, 1.04)
        if rand:
            FW = B["top"][2]
            if abs(a - 0.5) * FW < 1.5:                       # ålstrimman längs ryggraden
                c = rand
            for k in range(RANDER):
                cz = (k + 0.5) / RANDER
                if abs(b - cz) * B["top"][3] < 1.0 and 0.12 < a < 0.88 \
                        and not (_h(x, y, 4) < 0.22):
                    c = blanda(rand, c, 0.2)
        return korn(c, x, y)

    duk.yta(B["top"], rygg, alfa)

    def mage(a, b, x, y):
        c = buk
        mr = K.get("magrander")
        if mr and 0.2 < a < 0.8:
            for k in range(RANDER):
                if abs(b - (k + 0.5) / RANDER) * B["bottom"][3] < 0.9:
                    c = mr
        return korn(c, x, y, 0.8)

    duk.yta(B["bottom"], mage, alfa)

    def brost(a, b, x, y):
        c = skala(pals, 1.02 + 0.06 * (1 - abs(a - 0.5) * 2))
        if K.get("bringa"):
            kant = 0.14 + 0.05 * math.sin(a * 9.0)
            if kant < b < 0.86 - 0.04 * math.cos(a * 11.0):
                c = VIT
        return korn(c, x, y)

    duk.yta(B["north"], brost, alfa)

    def bak(a, b, x, y):
        c = skala(pals, 1.02 - 0.18 * b)
        FW, FH = B["south"][2], B["south"][3]
        if math.hypot((a - 0.5) * FW / 2.2, (b - 0.12) * FH / 1.6) < 1.0:
            c = blanda(c, (0, 0, 0), 0.22)       # skugga vid svansfästet
        return korn(c, x, y)

    duk.yta(B["south"], bak, alfa)

    # ---------------------------------------------------------------- benen
    # Alla fyra ben delar en uv-ruta; det som målas här sitter på alla.
    L = ytor(BEN["leg0"][0])

    def bengrund(a, b, x, y, fram=False):
        if points:
            # Points är mörkast längst ut: benet går från kroppens färg upptill
            # till pointfärgen nedtill.
            c = blanda(pals, points, max(0.0, min(1.0, (b - 0.10) / 0.35)))
        else:
            c = skala(pals, 1.0 - 0.1 * b)
        if b < 0.12:
            c = blanda(c, (0, 0, 0), 0.22 * (1 - b / 0.12))   # kontaktskugga mot bålen
        FH = L["east"][3]
        if rand:
            for cb in (0.30, 0.58):
                if abs(b - cb) * FH < 1.0 and not (_h(x, y, 5) < 0.2):
                    c = blanda(rand, c, 0.2)
        if tass_vit:
            grans = (0.55 if K.get("tassar") else 0.72) + 0.03 * math.sin(a * 7.0 + 1.0)
            if b > grans:
                c = VIT
        if fram and b > 0.8 and (abs(a - 0.33) < 0.06 or abs(a - 0.67) < 0.06):
            c = blanda(c, (0, 0, 0), 0.18)       # tåspringorna
        return korn(c, x, y)

    duk.yta(L["east"], bengrund, alfa)
    duk.yta(L["west"], bengrund, alfa)
    duk.yta(L["south"], bengrund, alfa)
    duk.yta(L["north"], lambda a, b, x, y: bengrund(a, b, x, y, True), alfa)
    duk.yta(L["top"], lambda a, b, x, y: korn(skala(pals, 0.9), x, y), alfa)

    def trampdyna(a, b, x, y):
        c = VIT if tass_vit else (points or pals)
        FW, FH = L["bottom"][2], L["bottom"][3]
        X, Y = a * FW, b * FH
        dynor = [((FW * 0.5, FH * 0.66), 2.0, 1.5)]
        for tx in (0.2, 0.5, 0.8):
            dynor.append(((FW * tx, FH * (0.18 if tx == 0.5 else 0.28)), 0.95, 0.95))
        for (cx, cy), rx, ry in dynor:
            if ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1.0:
                return TASSROSA if lum(c) > 120 else blanda(TASSROSA, c, 0.35)
        return korn(c, x, y)

    duk.yta(L["bottom"], trampdyna, alfa)

    # ---------------------------------------------------------------- svansen
    T = ytor(SVANS)

    def svans(a, b, x, y):
        c = points or pals
        c = skala(c, 1.0 - 0.12 * b)             # mörkare mot spetsen
        FH = T["east"][3]
        if rand:
            for cb in (0.28, 0.62):
                if abs(b - cb) * FH < 0.9:
                    c = blanda(rand, c, 0.2)
            if b > 0.86:
                c = blanda(rand, c, 0.3)         # mörk spets
        return korn(c, x, y)

    for n in ("east", "west", "north", "south"):
        duk.yta(T[n], svans, alfa)
    duk.yta(T["top"], lambda a, b, x, y: korn(points or pals, x, y), alfa)
    duk.yta(T["bottom"], lambda a, b, x, y: korn(blanda(points or pals, (0, 0, 0), 0.25), x, y), alfa)

    # ---------------------------------------------------------------- skallen
    S = ytor(SKALLE)
    FW, FH = S["north"][2], S["north"][3]
    OGON = [(FW * (1 / 6), FH * 0.5, +1), (FW * (5 / 6), FH * 0.5, -1)]   # (cx, cy, inåt)
    RX, RY = FW * 0.135, FH * 0.26

    def ansikte(a, b, x, y):
        X, Y = a * FW, b * FH
        c = huvud
        # NOSRYGG OCH HAKA: nospartiet ljusnar in mot mitten och nedåt.
        bredd = 0.42 if K.get("bringa") else 0.34
        if abs(a - 0.5) < bredd and b > 0.42:
            t = min(1.0, (b - 0.42) / 0.3) * (1 - (abs(a - 0.5) / bredd) ** 2 * 0.5)
            c = blanda(c, nosparti, t)
        # TABBYNS M I PANNAN.
        if rand and b < 0.45:
            m = [((6, 8), (9, 1.5)), ((9, 1.5), (12, 7)), ((12, 7), (15, 1.5)), ((15, 1.5), (18, 8))]
            m = [((p[0] * FW / 24, p[1] * FH / 20), (q[0] * FW / 24, q[1] * FH / 20)) for p, q in m]
            if min(avst_segment(X, Y, *p, *q) for p, q in m) < 0.75:
                c = blanda(rand, c, 0.15)
        # ÖGONBRYN: en mjuk skugga ovanför varje öga, inte ett svart band.
        for cx, cy, _ in OGON:
            if abs(X - cx) < RX + 0.6 and Y < cy - RY:
                t = 0.30 * max(0.0, 1 - (cy - RY - Y) / (FH * 0.22))
                c = blanda(c, mork, t)
        # KINDRODNAD: en antydan, ytterst nedtill.
        for cx, cy, inat in OGON:
            if math.hypot((X - (cx - inat * FW * 0.06)) / 2.8, (Y - FH * 0.9) / 2.2) < 1.0:
                c = blanda(c, (206, 132, 138), 0.20)
        c = korn(c, x, y, 0.7)
        # ÖGONEN: mandelform med mörk kant, iris med ljus ovan och djup nedan,
        # lodrät pupill och en glans. Glansen är det enda som skiljer ett öga
        # från en knapp.
        for cx, cy, inat in OGON:
            dx, dy = (X - cx) / RX, (Y - cy) / RY
            r = math.hypot(dx, dy)
            if r > 1.0:
                continue
            if r > 0.86:
                return mork
            iris = blanda(K["iris"], K["iris_mork"], max(0.0, min(1.0, 0.15 + 0.55 * (dy + 1) / 2)))
            if abs(X - cx) < 0.75 and abs(Y - cy) < RY * 0.70:
                iris = blanda(K["iris_mork"], (0, 0, 0), 0.75)       # pupillen
            if math.hypot(X - (cx + inat * RX * 0.42), Y - (cy - RY * 0.42)) < 1.15:
                iris = GLANS
            return ("oga", iris)
        return c

    def ansikte_alfa(a, b, x, y):
        c = ansikte(a, b, x, y)
        if isinstance(c, tuple) and c and c[0] == "oga":
            duk.px[y][x] = tuple(c[1]) + (ogon_alfa,)
            return None
        return c

    duk.yta(S["north"], ansikte_alfa, alfa)

    def hjassa(a, b, x, y):
        c = huvud
        if rand:
            FWt = S["top"][2]
            for ca in (0.2, 0.5, 0.8):
                if abs(a - ca) * FWt < (1.5 if ca == 0.5 else 1.0) + 0.5 * math.sin(b * 9 + ca * 5) \
                        and b > 0.1:
                    c = blanda(rand, c, 0.15)
        st = K.get("stjarna")
        if st and i_stjarna((a - 0.5) * S["top"][2], (b - 0.45) * S["top"][3], 3.4, 1.4):
            return st
        return korn(c, x, y)

    duk.yta(S["top"], hjassa, alfa)

    def skallsida(a, b, x, y):
        c = huvud
        if rand:
            FWs, FHs = S["east"][2], S["east"][3]
            for cb, langd in ((0.45, 0.85), (0.68, 0.6)):
                if abs(b - cb + 0.03 * math.sin(a * 8)) * FHs < 1.0 and 0.12 < a < langd:
                    c = blanda(rand, c, 0.2)
        return korn(c, x, y)

    duk.yta(S["east"], skallsida, alfa)
    duk.yta(S["west"], skallsida, alfa)
    duk.yta(S["south"], lambda a, b, x, y: korn(skala(huvud, 1.0 - 0.15 * b), x, y), alfa)
    duk.yta(S["bottom"], lambda a, b, x, y: korn(blanda(huvud, nosparti, 0.6), x, y, 0.7), alfa)

    # ---------------------------------------------------------------- nosen
    N = ytor(NOS)
    NW, NH = N["north"][2], N["north"][3]

    def nos(a, b, x, y):
        X, Y = a * NW, b * NH
        c = nosparti
        # Morrhårskuddar: två små mörkare fält vid munvinklarna.
        if 0.45 < b < 0.75 and (a < 0.22 or a > 0.78):
            c = blanda(c, mork, 0.12)
        # Nosen: en rosa triangel med spetsen nedåt.
        hw = NW * 0.40 - (Y / (NH * 0.45)) * NW * 0.34
        if Y < NH * 0.45 and abs(X - NW / 2) < hw:
            c = ROSA
            if abs(Y - NH * 0.18) < 0.6 and abs(abs(X - NW / 2) - NW * 0.2) < 0.6:
                c = blanda(ROSA, (0, 0, 0), 0.22)                     # näsborrar
            return c
        # Munnen: ett kort lodrätt streck under nosen och två bågar som går UPPÅT
        # i vinklarna — ett "ω". Första försöket drog dem nedåt, som på en
        # riktig katt, och det läste som en bister min på en kub.
        if abs(X - NW / 2) < 0.9 and NH * 0.42 <= Y < NH * 0.64:
            return mun
        if NH * 0.60 <= Y < NH * 0.74 and abs(X - NW / 2) < NW * 0.30:
            return mun
        if NH * 0.48 <= Y < NH * 0.64 and NW * 0.26 < abs(X - NW / 2) < NW * 0.42:
            return mun
        return korn(c, x, y, 0.5)

    duk.yta(N["north"], nos, alfa)
    for n in ("top", "east", "west", "south"):
        duk.yta(N[n], lambda a, b, x, y: korn(nosparti, x, y, 0.5), alfa)
    duk.yta(N["bottom"], lambda a, b, x, y: blanda(nosparti, mork, 0.35), alfa)

    # ---------------------------------------------------------------- kinderna
    # I exakt pälsfärg: det är att konturen byter bredd som läser som en kind,
    # inte att ytan har en annan ton. Nedtill ljusnar tofsen mot nospartiet.
    for kub in KINDER:
        for n, rekt in ytor(kub).items():
            duk.yta(rekt, lambda a, b, x, y: korn(blanda(huvud, nosparti, 0.25 * b), x, y), alfa)

    # ---------------------------------------------------------------- öronen
    # Örats egen färg är pointfärgen på en pointad katt — att måla örat i
    # ansiktets färg hade tagit bort hela rasmarkeringen.
    avst = sum(abs(ROSA[i] - oron[i]) for i in range(3)) / 3
    t_inre = 0.60 if avst <= 0 else min(0.88, max(0.60, 28.0 / avst))
    inre = blanda(oron, ROSA, t_inre)
    for kub in ORON:
        Y_ = ytor(kub)

        def orafram(a, b, x, y):
            if 0.18 < b < 0.92 and abs(a - 0.5) < 0.08 + (b - 0.18) * 0.42:
                return blanda(inre, oron, 0.25 * (1 - b))
            return korn(oron, x, y)

        duk.yta(Y_["north"], orafram, alfa)
        for n in ("top", "bottom", "east", "west", "south"):
            duk.yta(Y_[n], lambda a, b, x, y: korn(oron, x, y), alfa)

    return duk


def katterna():
    """Alla entiteter som använder kattmodellen — läses ur paketet."""
    import glob
    ut = []
    for f in sorted(glob.glob(f"{RP}/entity/*.json")):
        d = json.load(open(f))["minecraft:client_entity"]["description"]
        if d.get("geometry", {}).get("default") == "geometry.katt":
            ut.append(d["identifier"].split(":")[1])
    return ut


def fil(namn):
    return f"{RP}/textures/entity/{namn}_pals.png"


def main():
    # Arket måste rymma varje kub. Läses ur geometrin så en flyttad uv-ruta
    # faller här och inte som en osynlig kroppsdel på Xbox.
    W, H = ENHETER[0] * SKALA, ENHETER[1] * SKALA
    for bn, kuber in BEN.items():
        for k in kuber:
            for n, (x0, y0, fw, fh) in ytor(k).items():
                if x0 + fw > W + 1e-6 or y0 + fh > H + 1e-6:
                    raise SystemExit(f"{bn}: ytan {n} når utanför arket ({W}x{H})")
    finns = set(katterna())
    saknas = finns - set(KATTER)
    if saknas:
        raise SystemExit(f"katter utan rad i KATTER: {sorted(saknas)}")
    print(f"pälsark {W}x{H} = {ENHETER[0]}x{ENHETER[1]} enheter x {SKALA}")
    for namn, K in KATTER.items():
        if namn not in finns:
            print(f"  {namn:10s} (ingen entitet — hoppar över)")
            continue
        egen = f"{ART}/{namn}.png"
        if os.path.exists(egen):
            w, h, _ = rr.read_png(egen)
            if (w, h) != (W, H):
                raise SystemExit(f"{egen}: {w}x{h}, arket ska vara {W}x{H}")
            shutil.copy(egen, fil(namn))
            print(f"  {namn:10s} ark från art/pals/")
            continue
        duk = mala(namn, K)
        rr.write_png(fil(namn), W, H, duk.px)
        drag = [d for d in ("rand", "points", "bringa", "tassar", "handskar", "magrander", "stjarna") if K.get(d)]
        print(f"  {namn:10s} {', '.join(drag) or 'enfärgad'}")


if __name__ == "__main__":
    main()
