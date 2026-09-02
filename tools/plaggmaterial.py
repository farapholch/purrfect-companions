#!/usr/bin/env python3
"""Plaggens MATERIAL — det som gör en sadel till läder och en krona till guld.

Bakgrund: plaggen målades av build_accessories som en färgad rektangel med en
ljus rad överst, en mörk underst och en mörkare kolumn var fjärde texel. På en
texel per enhet fanns inte plats för mer. Sedan katterna (3.40.0) och dräkten
(3.41.0) fick päls i fyra texlar per enhet var plaggen det sista som såg ut som
färgade lådor.

Plaggen bor nu i ETT delat ark, `textures/entity/plagg.png`, i SKALA gånger
plagg-geometriernas 256x256 uv-enheter. Ett ark för alla katter: plaggen såg
likadana ut i alla tio atlasen ändå (och de hemliga katternas atlas hade
plaggen omfärgade av sin päls-transform — en svart sadel på Midnight).

VARJE PLAGG HAR ETT MATERIAL, uppslaget på namnet i MATERIAL nedan. Ett nytt
plagg utan rad där får tyg. Färgen kommer ur ACC som förut; det som skiljer
är hur den läggs på: läder får sömmar, ull får stickade ribbor, plåt får fasade
kanter och nitar, trä får plankor, fjädrar får rader, bladet glöder.

Kuber som delar uv-ruta (fyra tossor, två vingar, två hjul) målas en gång.
"""
import math, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE); sys.path.insert(0, f"{BASE}/tools")
import render_regression as rr
from make_cat_pals import korn, blanda, skala, klamp, lum, _h, avst_segment

SKALA = 4
GULD = (238, 198, 72)
VIT = (240, 240, 238)
LINS = (198, 222, 232)
STAL = (150, 150, 160)


def ytor(uv, size):
    return {n: tuple(v * SKALA for v in r) for n, r in rr.faces(uv[0], uv[1], *size).items()}


def _kuber(cfg, i):
    """Plaggets kuber med absolut uv — och bara EN per uv-ruta."""
    u, v = cfg["uv"][i]
    ut, sedda = [], set()
    for o, s, (du, dv) in cfg["cubes"]:
        nyckel = (tuple(s), du, dv)
        if nyckel in sedda:
            continue
        sedda.add(nyckel)
        ut.append((o, s, (u + du, v + dv)))
    return ut


def grund(col, b, spann=0.22):
    """Ljus uppifrån: ljusare överst, mörkare nederst — på varje yta."""
    return skala(col, 1.0 + spann / 2 - spann * b)


def kantad(fn, rekt, ton=0.82, bredd=1.0):
    """Mörkare kant runt ytan så plagget får en kontur mot pälsen."""
    X0, Y0, FW, FH = rekt

    def fn2(a, b, x, y):
        c = fn(a, b, x, y)
        X, Y = a * FW, b * FH
        if X < bredd or Y < bredd or X > FW - bredd or Y > FH - bredd:
            return skala(c, ton)
        return c
    return fn2


def alla(duk, kuber, gor, **kw):
    """Kör gor(sida, rekt, kub) -> fn över varje yta i varje kub."""
    for kub in kuber:
        o, s, uv = kub
        for sida, rekt in ytor(uv, s).items():
            fn = gor(sida, rekt, kub, **kw)
            if fn:
                duk.yta(rekt, fn, 255)


# ---------------------------------------------------------------- grundmaterial
def tyg(col, rekt, vav=0.03):
    def fn(a, b, x, y):
        c = grund(col, b)
        if (x + y) % 2 == 0:
            c = skala(c, 1 + vav)
        return korn(c, x, y, 0.4)
    return kantad(fn, rekt)


def lader(col, rekt, som=True):
    X0, Y0, FW, FH = rekt
    stygn = blanda(col, (255, 255, 255), 0.40)

    def fn(a, b, x, y):
        c = korn(grund(col, b, 0.18), x, y, 0.5)
        X, Y = a * FW, b * FH
        if som and FW >= 6 and FH >= 6:
            # sömmen: en rad korta stygn en texel innanför kanten
            innanfor = (1.5 <= X < 2.5 or FW - 2.5 <= X < FW - 1.5) and 1 <= Y < FH - 1
            innanfor |= (1.5 <= Y < 2.5 or FH - 2.5 <= Y < FH - 1.5) and 1 <= X < FW - 1
            if innanfor and (x + y) % 3 != 0:
                return stygn
        return c
    return kantad(fn, rekt, 0.75)


def ull(col, rekt):
    def fn(a, b, x, y):
        c = grund(col, b, 0.16)
        rib = 1.07 if (y % 4) < 2 else 0.93
        if (x + (y // 2)) % 2 == 0:
            rib *= 0.97
        return korn(skala(c, rib), x, y, 0.3)
    return kantad(fn, rekt, 0.85)


def metall(col, rekt, nitar=True, band=True):
    X0, Y0, FW, FH = rekt
    ljus, mork = blanda(col, (255, 255, 255), 0.40), blanda(col, (0, 0, 0), 0.40)

    def fn(a, b, x, y):
        X, Y = a * FW, b * FH
        c = grund(col, b, 0.12)
        if band and abs(b - 0.3) < 0.08:
            c = blanda(c, (255, 255, 255), 0.18)             # högdager
        if X < 1.5 or Y < 1.5:
            c = ljus
        elif X > FW - 1.5 or Y > FH - 1.5:
            c = mork
        if nitar and FW >= 8 and FH >= 8:
            for nx in (3.0, FW - 3.0):
                for ny in (3.0, FH - 3.0):
                    if abs(X - nx) < 1.0 and abs(Y - ny) < 1.0:
                        c = mork
        return korn(c, x, y, 0.25)
    return fn


def tra(col, rekt, langs="x"):
    """Plankor längs ytans längsta led, med en spik i varje plankände."""
    X0, Y0, FW, FH = rekt
    tvars = FH if langs == "x" else FW
    linje, spik = skala(col, 0.62), skala(col, 0.45)

    def fn(a, b, x, y):
        X, Y = a * FW, b * FH
        t = Y if langs == "x" else X
        l = X if langs == "x" else Y
        L = FW if langs == "x" else FH
        c = grund(col, b, 0.14)
        # ådring: långa svaga strimmor längs plankan
        c = skala(c, 1 + 0.05 * (_h(int(l // 5), int(t), 11) - 0.5))
        if tvars >= 6 and int(t) % 6 == 5:
            return linje
        if tvars >= 6 and (l < 2.5 or l > L - 2.5) and int(t) % 6 == 2:
            return spik
        return korn(c, x, y, 0.35)
    return kantad(fn, rekt, 0.8)


def fluff(col, rekt):
    def fn(a, b, x, y):
        return korn(grund(col, b, 0.10), x, y, 2.2)
    return fn


# ---------------------------------------------------------------- plaggen
def m_sadel(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        o, s, uv = kub
        if s[0] < 4:                                     # sadelhornet
            return lader(skala(col, 0.8), rekt, som=False)
        fn = lader(col, rekt)
        if sida == "top":
            X0, Y0, FW, FH = rekt
            def fn2(a, b, x, y, fn=fn):
                if abs(a * FW - FW / 2) < 0.6:
                    return skala(col, 0.6)               # mittsöm längs sitsen
                return fn(a, b, x, y)
            return fn2
        return fn
    alla(duk, kuber, gor)


def m_keps(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        o, s, uv = kub
        if s[1] < 1:                                     # skärmen
            return tyg(skala(col, 0.78), rekt)
        fn = tyg(col, rekt)
        X0, Y0, FW, FH = rekt
        som = skala(col, 0.72)

        def fn2(a, b, x, y):
            X, Y = a * FW, b * FH
            if sida == "top":
                if abs(X - FW / 2) < 0.6 or abs(Y - FH / 2) < 0.6:
                    return som                           # panelsömmarna
                if math.hypot(X - FW / 2, Y - FH / 2) < 1.6:
                    return skala(col, 0.55)              # knappen
            elif sida in ("north", "south", "east", "west") and abs(X - FW / 2) < 0.6:
                return som
            return fn(a, b, x, y)
        return fn2
    alla(duk, kuber, gor)


def m_halsduk(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        o, s, uv = kub
        fn = ull(col, rekt)
        if s[0] <= 2 and sida in ("north", "south", "east", "west"):
            X0, Y0, FW, FH = rekt

            def fn2(a, b, x, y):
                if b > 0.72:                             # fransen
                    return skala(col, 0.55) if (x % 2) else skala(col, 1.05)
                return fn(a, b, x, y)
            return fn2
        return fn
    alla(duk, kuber, gor)


def m_ryggsack(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        o, s, uv = kub
        if s[1] < 1:                                     # locket
            return lader(col, rekt)
        fn = tyg(col, rekt)
        X0, Y0, FW, FH = rekt
        rem = skala(col, 0.7)

        def fn2(a, b, x, y):
            X, Y = a * FW, b * FH
            if sida in ("south", "top") and (abs(a - 0.25) < 0.05 or abs(a - 0.75) < 0.05):
                return rem                               # remmarna
            if sida == "south" and 0.36 < a < 0.64 and 0.3 < b < 0.72:
                # spännet: metall med mörk kant
                if 0.38 < a < 0.62 and 0.34 < b < 0.68:
                    return blanda(GULD, (255, 255, 255), 0.3 if b < 0.45 else 0.0)
                return skala(GULD, 0.5)
            return fn(a, b, x, y)
        return fn2
    alla(duk, kuber, gor)


def m_glasogon(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        X0, Y0, FW, FH = rekt
        ram = col

        def fn(a, b, x, y):
            X, Y = a * FW, b * FH
            if sida in ("north", "south"):
                for la, lb in ((0.06, 0.45), (0.55, 0.94)):
                    if la < a < lb and 0.15 < b < 0.9:
                        # linsen med en sned högdager
                        if 3 < (X - Y * 0.8) % 9 < 5:
                            return (240, 248, 252)
                        return blanda(LINS, (255, 255, 255), 0.25 * (1 - b))
            return korn(grund(ram, b, 0.12), x, y, 0.2)
        return kantad(fn, rekt, 0.7, 0.6)
    alla(duk, kuber, gor)


def m_tossor(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        if sida == "bottom":
            return lambda a, b, x, y: korn(skala(col, 0.5), x, y, 0.3)
        fn = ull(col, rekt)

        def fn2(a, b, x, y):
            if sida != "top" and b > 0.78:
                return korn(skala(col, 0.62), x, y, 0.3)   # sulkanten
            return fn(a, b, x, y)
        return fn2
    alla(duk, kuber, gor)


def m_vagn(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        o, s, uv = kub
        X0, Y0, FW, FH = rekt
        if s[1] == 4 and s[0] == 1:                      # hjulen
            if sida in ("east", "west"):
                nav, ek = skala(col, 0.5), skala(col, 0.72)

                def hjul(a, b, x, y):
                    dx, dy = (a - 0.5) * FW, (b - 0.5) * FH
                    r = math.hypot(dx, dy) / (FW / 2)
                    if r > 1.0:
                        return skala(col, 0.45)
                    if r > 0.78 or r < 0.22:
                        return korn(nav, x, y, 0.3)
                    if abs(dx) < 0.8 or abs(dy) < 0.8:
                        return ek
                    return korn(grund(col, b, 0.1), x, y, 0.3)
                return hjul
            return lambda a, b, x, y: korn(skala(col, 0.5), x, y, 0.3)
        if s[1] == 1:                                    # dragstången
            return tra(skala(col, 0.8), rekt, "y" if FH > FW else "x")
        return tra(col, rekt, "x" if FW >= FH else "y")
    alla(duk, kuber, gor)


def m_halsband(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        o, s, uv = kub
        if s == [1, 1, 1]:                               # bjällran
            fn = metall(GULD, rekt, nitar=False)
            X0, Y0, FW, FH = rekt

            def fn2(a, b, x, y):
                if sida in ("north", "south") and b > 0.7 and abs(a - 0.5) < 0.18:
                    return skala(GULD, 0.35)             # springan
                return fn(a, b, x, y)
            return fn2
        return lader(col, rekt)
    alla(duk, kuber, gor)


def m_rosett(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        X0, Y0, FW, FH = rekt

        def fn(a, b, x, y):
            X, Y = a * FW, b * FH
            c = grund(col, b, 0.2)
            if (X + Y) % 7 < 1.6:
                c = blanda(c, (255, 255, 255), 0.30)     # satinglans
            if sida in ("north", "south", "top", "bottom") and 0.4 < a < 0.6:
                c = skala(col, 0.72)                     # knuten
                if abs(a - 0.4) < 0.04 or abs(a - 0.6) < 0.04:
                    c = skala(col, 0.5)
            return korn(c, x, y, 0.3)
        return kantad(fn, rekt, 0.8)
    alla(duk, kuber, gor)


def m_vingar(duk, kuber, col, i, cfg):
    linje = blanda(col, (255, 255, 255) if lum(col) < 90 else (0, 0, 0), 0.28)

    def gor(sida, rekt, kub):
        X0, Y0, FW, FH = rekt
        if sida not in ("east", "west"):
            return lambda a, b, x, y: korn(skala(col, 0.85), x, y, 0.4)

        def fn(a, b, x, y):
            X, Y = a * FW, b * FH
            c = skala(grund(col, b, 0.12), 1.0 - 0.08 * a)
            # fjäderrader: en vågig kant var femte texel
            if (Y + 1.2 * math.sin(X * 1.1)) % 5 < 1.0:
                return linje
            # fjäderspolen: en ljus strimma mitt i varje fjäder
            if int(X + 1.2 * math.sin(Y * 0.5)) % 5 == 2 and _h(x, y, 12) < 0.6:
                c = blanda(c, (255, 255, 255) if lum(col) < 90 else (0, 0, 0), 0.10)
            return korn(c, x, y, 0.3)
        return kantad(fn, rekt, 0.85)
    alla(duk, kuber, gor)


def m_horn(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        o, s, uv = kub
        topp = 1.0 + 0.08 * (s[1] < 1.5)                 # spetsen ljusare

        def fn(a, b, x, y):
            ring = 1.12 if ((y + x // 2) % 4) < 2 else 0.90
            return korn(skala(grund(col, b, 0.1), ring * topp), x, y, 0.2)
        return fn
    alla(duk, kuber, gor)


def m_rustning(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        o, s, uv = kub
        fn = metall(col, rekt, nitar=(s[0] > 3))
        if sida == "top" and s[2] > 10:
            X0, Y0, FW, FH = rekt

            def fn2(a, b, x, y):
                if abs(a - 0.5) * FW < 0.8:
                    return blanda(col, (255, 255, 255), 0.35)   # ryggåsen
                return fn(a, b, x, y)
            return fn2
        return fn
    alla(duk, kuber, gor)


def m_haxhatt(duk, kuber, col, i, cfg):
    band = blanda(col, (120, 90, 40), 0.55)

    def gor(sida, rekt, kub):
        o, s, uv = kub
        fn = tyg(col, rekt)
        if s[1] > 2 and sida in ("north", "south", "east", "west"):   # kupan
            X0, Y0, FW, FH = rekt

            def fn2(a, b, x, y):
                if b > 0.72:
                    if sida == "north" and 0.4 < a < 0.6 and 0.76 < b < 0.96:
                        return skala(GULD, 0.5) if (a < 0.44 or a > 0.56 or b < 0.8 or b > 0.92) else GULD
                    return korn(grund(band, b, 0.1), x, y, 0.3)
                return fn(a, b, x, y)
            return fn2
        if sida == "bottom":
            return tyg(skala(col, 0.7), rekt)
        return fn
    alla(duk, kuber, gor)


def m_tomteluva(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        o, s, uv = kub
        if s[1] <= 1.6 and s[0] < 6 and s != [3.6, 2.4, 3.6]:   # kant och tofs
            return fluff(VIT, rekt)
        return tyg(col, rekt, 0.02)
    alla(duk, kuber, gor)


def m_doktorsrock(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        o, s, uv = kub
        fn = tyg(col, rekt, 0.02)
        X0, Y0, FW, FH = rekt
        som = skala(col, 0.8)

        def fn2(a, b, x, y):
            X, Y = a * FW, b * FH
            if s[0] < 1 and sida in ("east", "west") and 0.55 < a < 0.9 and 0.45 < b < 0.85:
                if a < 0.58 or a > 0.87 or b < 0.5 or b > 0.82:
                    return som                            # fickans kant
            if s[0] > 6 and sida == "top" and abs(X - FW / 2) < 0.6:
                return som                                # ryggsömmen
            return fn(a, b, x, y)
        return fn2
    alla(duk, kuber, gor)


def m_batvingar(duk, kuber, col, i, cfg):
    ben = blanda(col, (0, 0, 0), 0.5)
    hinna = blanda(col, (255, 255, 255), 0.10)

    def gor(sida, rekt, kub):
        o, s, uv = kub
        X0, Y0, FW, FH = rekt
        if s[1] > 1:                                      # armarna
            return lambda a, b, x, y: korn(skala(col, 0.8), x, y, 0.4)
        if sida not in ("top", "bottom"):
            return lambda a, b, x, y: ben

        def fn(a, b, x, y):
            X, Y = a * FW, b * FH
            if b > 0.90 + 0.05 * math.sin(X * 0.9):
                return skala(col, 0.4)                    # den flikiga bakkanten
            for mal in (0.02, 0.35, 0.65, 0.98):
                if avst_segment(X, Y, FW / 2, 1.0, mal * FW, FH - 1) < 0.7:
                    return ben
            return korn(skala(hinna, 1.0 - 0.15 * b), x, y, 0.4)
        return fn
    alla(duk, kuber, gor)


def m_krona(duk, kuber, col, i, cfg):
    JUVELER = [(0.25, (200, 40, 60)), (0.5, (60, 90, 220)), (0.75, (60, 190, 90))]

    def gor(sida, rekt, kub):
        X0, Y0, FW, FH = rekt
        fn = metall(col, rekt, nitar=False)

        def fn2(a, b, x, y):
            X, Y = a * FW, b * FH
            if sida in ("north", "south", "east", "west"):
                if b < 0.3 and int(X // 3) % 2 == 1:
                    return None                           # tinnarna: hål mellan spetsarna
                if sida == "north":
                    for ja, jc in JUVELER:
                        if abs(X - ja * FW) + abs(Y - 0.62 * FH) < 1.6:
                            return blanda(jc, (255, 255, 255), 0.5 if (X < ja * FW and Y < 0.62 * FH) else 0.0)
            return fn(a, b, x, y)
        return fn2
    alla(duk, kuber, gor)


def m_mantel(duk, kuber, col, i, cfg):
    trim = blanda(col, GULD, 0.55)

    def gor(sida, rekt, kub):
        o, s, uv = kub
        X0, Y0, FW, FH = rekt
        if s[1] == 1:                                     # kragen
            return tyg(skala(col, 0.8), rekt)

        def fn(a, b, x, y):
            X, Y = a * FW, b * FH
            c = grund(col, b, 0.18)
            c = skala(c, 1 + 0.07 * math.sin(X * 0.8))    # vecken
            if s[1] > 2 and sida in ("north", "south") and (b > 0.85 or X < 1.5 or X > FW - 1.5):
                return trim                               # bården
            return korn(c, x, y, 0.4)
        return fn
    alla(duk, kuber, gor)


def m_energisvard(duk, kuber, col, i, cfg):
    def gor(sida, rekt, kub):
        o, s, uv = kub
        X0, Y0, FW, FH = rekt
        if s[1] == 2 and s[0] == 1:                       # greppet: lindat läder
            return lambda a, b, x, y: skala((60, 52, 58), 1.0 if (y % 4) < 2 else 0.7)
        if s[0] == 3:                                     # parerstången
            return metall(STAL, rekt, nitar=False)

        def fn(a, b, x, y):                               # bladet glöder
            X = a * FW
            d = abs(a - 0.5) * 2
            c = blanda((255, 255, 255), col, min(1.0, d * 1.3))
            if (y % 6) < 1:
                c = blanda(c, (255, 255, 255), 0.25)      # pulsen
            return c
        return fn
    alla(duk, kuber, gor)


def m_rymdmantel(duk, kuber, col, i, cfg):
    mork = lum(col) < 90

    def gor(sida, rekt, kub):
        o, s, uv = kub
        X0, Y0, FW, FH = rekt

        def fn(a, b, x, y):
            c = grund(col, b, 0.16)
            if mork:
                n = _h(x // 4, y // 4, 13) * 0.6 + _h(x // 8, y // 8, 14) * 0.4
                c = blanda(c, (96, 60, 130), max(0.0, n - 0.55) * 0.9)   # nebulosa
            h = _h(x, y, 15)
            if h > 0.982:
                return (255, 255, 255)                                   # stjärna
            if h > 0.965:
                return blanda(c, (255, 255, 255), 0.5)
            return korn(c, x, y, 0.3)
        return kantad(fn, rekt, 0.85)
    alla(duk, kuber, gor)


def m_gruvlampa(duk, kuber, col, i, cfg):
    """Läderrem över hjässan och en lampa av metall med en glödande lins."""
    LENS = (255, 244, 170)

    def gor(sida, rekt, kub):
        o, s, uv = kub
        if s[1] < 1:                                      # remmen
            return lader((70, 52, 36), rekt, som=True)
        fn = metall(col, rekt, nitar=False)
        X0, Y0, FW, FH = rekt
        if sida == "north":
            def fn2(a, b, x, y):
                r = math.hypot((a - 0.5) * FW / (FW * 0.36), (b - 0.5) * FH / (FH * 0.38))
                if r < 0.75:
                    return blanda(LENS, (255, 255, 255), max(0.0, 0.6 - r))
                if r < 1.0:
                    return blanda(col, (0, 0, 0), 0.45)       # linsens ram
                return fn(a, b, x, y)
            return fn2
        return fn
    alla(duk, kuber, gor)


def m_flytvast(duk, kuber, col, i, cfg):
    """Nylon med reflexband, spännen fram och en mörk rem över ryggen."""
    reflex = (222, 224, 226)
    spanne = (34, 34, 38)

    def gor(sida, rekt, kub):
        o, s, uv = kub
        X0, Y0, FW, FH = rekt
        if s[1] <= 0.5:                                   # ryggremmen: mörk väv
            return lambda a, b, x, y: korn(blanda(col, (0, 0, 0), 0.55 if (y % 3) else 0.65), x, y, 0.3)
        fn = tyg(col, rekt, 0.04)

        def fn2(a, b, x, y):
            if sida in ("north", "south", "east", "west"):
                if abs(b - 0.32) < 0.06 or abs(b - 0.68) < 0.06:
                    return korn(reflex, x, y, 0.3)          # reflexbanden
                if s[0] > 6 and sida == "north" and 0.4 < a < 0.6 and (0.12 < b < 0.24 or 0.76 < b < 0.88):
                    return spanne if not (0.45 < a < 0.55 and (0.15 < b < 0.21 or 0.79 < b < 0.85)) else (150, 150, 156)
            return fn(a, b, x, y)
        return fn2
    alla(duk, kuber, gor)


def m_regnrock(duk, kuber, col, i, cfg):
    """Blankt regntyg: lodräta ljusstrimmor, regndroppar och en nedfälld huva."""
    def gor(sida, rekt, kub):
        o, s, uv = kub
        X0, Y0, FW, FH = rekt
        bas = blanda(col, (0, 0, 0), 0.15) if s[1] > 1 and s[0] > 6 else col   # huvan mörkare

        def fn(a, b, x, y):
            X, Y = a * FW, b * FH
            c = grund(bas, b, 0.14)
            if (X + 0.3 * Y) % 9 < 1.5:
                c = blanda(c, (255, 255, 255), 0.22)         # glansstrimman
            if _h(x // 2, y // 2, 61) > 0.965:
                return blanda(c, (255, 255, 255), 0.55)      # en droppe
            if s[0] < 1 and sida in ("east", "west") and abs(b - 0.5) < 0.04:
                c = blanda(c, (0, 0, 0), 0.25)               # sömmen runt midjan
            return korn(c, x, y, 0.25)
        return kantad(fn, rekt, 0.8)
    alla(duk, kuber, gor)


def m_tyg(duk, kuber, col, i, cfg):
    alla(duk, kuber, lambda sida, rekt, kub: tyg(col, rekt))


MATERIAL = {
    "sadel": m_sadel, "keps": m_keps, "halsduk": m_halsduk, "ryggsack": m_ryggsack,
    "glasogon": m_glasogon, "tossor": m_tossor, "vagn": m_vagn, "halsband": m_halsband,
    "rosett": m_rosett, "vingar": m_vingar, "horn": m_horn, "rustning": m_rustning,
    "haxhatt": m_haxhatt, "tomteluva": m_tomteluva, "doktorsrock": m_doktorsrock,
    "batvingar": m_batvingar, "krona": m_krona, "mantel": m_mantel,
    "energisvard": m_energisvard, "rymdmantel": m_rymdmantel,
    "gruvlampa": m_gruvlampa, "flytvast": m_flytvast, "regnrock": m_regnrock,
}


def mala_plagg(duk, namn, cfg, i, col):
    """Målar plagg `namn` i färgvariant i på arket."""
    MATERIAL.get(namn, m_tyg)(duk, _kuber(cfg, i), tuple(col[:3]), i, cfg)
