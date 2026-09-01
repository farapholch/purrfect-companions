#!/usr/bin/env python3
"""Målar KATTERNAS ANSIKTEN — nosen som sticker ut, större ögon, mjukare drag.

Bakgrund, i två steg:

  1. Ungarna bad om sötare katter. Ansiktet var 6x5 texlar med ögon på 2x2, en
     hård svart mun och nästan svarta kinder — korrekt, men strängt.
  2. Med större ögon på plats kom nästa omdöme: ansiktena är "väldigt platta".
     Det var bokstavligt sant. Huvudet var EN enda kub, så hela ansiktet låg i
     ett plan och varje drag var målat. En katt har en nos som sticker ut; utan
     den är profilen en tegelsten oavsett hur bra texturen är.

Nosen är därför en egen kub i geometrin (2x2x1 rakt fram, uv 53,0) och det här
skriptet målar den. Samma åtgärd som grisarnas trynskiva, av exakt samma skäl.

    python3 tools/make_cat_faces.py

KÖRORDNING (viktig):
    1. make_cat_markings.py   teckningar på kropparna (rör aldrig huvudet)
    2. make_cat_textures.py   Ginger, Domino, Aurora, Nova, Spökkatt, Midnight
    3. make_cat_faces.py      DEN HÄR — ansiktet, på ALLA katter
    4. build_accessories.py   plaggens UV-ytor målas in igen

ANSIKTET MÅLAS SIST OCH PÅ ALLA. Först låg det här steget före härledningen, och
då fick bara de fyra grundraserna och de två som härleds ur dem ett ansikte.
Aurora, Nova, Spökkatten och Midnight byggs av egna recept med det GAMLA
ansiktet inbakat — de fick en nos-kub i enfärgad päls, alltså en blank låda mitt
i ansiktet. Härledningen först, ansiktet sedan, så finns det bara ett ställe
som äger hur en katt ser ut i ansiktet.

IDEMPOTENT UTAN KNEP: varje färg som skrivs räknas fram ur pixlar som skriptet
självt aldrig skriver (pälsen och nospartiet), eller skrivs tillbaka oförändrad
(irisen). Läser man en pixel man också skriver drar färgen iväg en bit för varje
körning — det är ackumulering, samma fälla som en gång gjorde "ibland född med
rosett" till hundra procent.

GENOMSKINLIGHETEN BEVARAS. Spökkatten har alfa 150 i hela pälsen; skriver man
255 blir hon plötsligt solid i ansiktet och slutar vara ett spöke.
"""
import json, glob, math, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import render_regression as rr

RP = f"{BASE}/PurrfectCompanions_RP"

# ANSIKTET LÄSES UR GEOMETRIN. Skallen är den största kuben i huvudbenet, nosen
# den som sticker längst fram (minst z). Ändras modellen följer ansiktet med i
# stället för att hamna en texel fel utan att någon märker det.
_geo = json.load(open(f"{RP}/models/entity/katt.geo.json"))["minecraft:geometry"][0]
_head = next(b for b in _geo["bones"] if b["name"] == "head")
_skalle = max(_head["cubes"], key=lambda c: c["size"][0] * c["size"][1])
_nos = min(_head["cubes"], key=lambda c: c["origin"][2])
if _nos is _skalle:
    raise SystemExit("geometrin saknar nos-kub — kör inte skriptet mot en platt modell")

# HUVUDETS ÖVRIGA KUBER, klassade på var de SITTER — inte på uv-nummer. Ett
# uv-nummer är ett andra ställe att hålla i synk; läget i modellen är samma sak
# som formen, och det är formen reglerna handlar om.
_topp = _skalle["origin"][1] + _skalle["size"][1]
_x0 = _skalle["origin"][0]
_x1 = _x0 + _skalle["size"][0]
# ÖRONENS FORM RÖRS INTE. Jag byggde om dem i tre omgångar — bas plus spets,
# mindre, bredare-lägre — och varje variant blev SÄMRE än originalet: två torn
# med en knopp på. Öronen var aldrig problemet; huvudet var.
#
# MEN INNERÖRAT ÄGS HÄR. Mätt över alla tio katterna var det ett lapptäcke:
# Aurora, Midnight, Nova och Spökkatten hade inget alls, Domino och Ginger hade
# ett som skilde tjugo steg från pälsen och alltså inte syntes, Misty och Hazel
# hade rosa och Mocha och Snow vitt i tre kolumner. På ALLA satt det dessutom en
# halv texel snett och läckte ut på örats SIDA — framsidan börjar på x 33,30, så
# texel 33 ligger till en tredjedel på västsidan.
_ORON = [c for c in _head["cubes"] if c is not _nos and c["origin"][1] >= _topp - 0.5]
# KINDERNA: kuber som sticker ut i sidled OCH sitter nedanför skallens topp.
# Utan höjdvillkoret fastnade ÖRONEN i regeln — de börjar på x -3,2 mot skallens
# -3,0 och sticker alltså också ut i sidled — och målades platta i pälsfärg.
# Det rosa innerörat försvann utan ett ord, och det syntes bara för att jag
# renderade. En regel som beskriver läge måste beskriva HELA läget.
_KINDER = [c for c in _head["cubes"]
           if c["origin"][1] < _topp - 0.5
           and (c["origin"][0] < _x0 - 0.05 or c["origin"][0] + c["size"][0] > _x1 + 0.05)]

# YTORNA HÅLLS I FLYTTAL. Först trunkerades de till heltal, och då hamnade
# innerörat på en rad som till 30 % ligger på örats OVANSIDA: örats framsida
# börjar på y 11,30, men int() gjorde 11 av det. Det är exakt samma halvtexel-
# fälla som tog grisarnas näsborrar, i ett annat paket — en yta vars kant ligger
# mellan två texlar delar den texeln med grannytan, och en detalj som placeras
# där hamnar till en del på grannen.
_ytor = lambda c: rr.faces(c["uv"][0], c["uv"][1], *c["size"])


def _tacker(f0, fl):
    """Texelintervall som TÄCKER en yta helt — för att måla grundfärg."""
    return int(math.floor(f0 + 1e-6)), int(math.ceil(f0 + fl - 1e-6))


def _inre(f0, fl):
    """Texelintervall som ligger HELT inne i en yta — för att placera detaljer."""
    a = int(math.ceil(f0 - 1e-6))
    return a, max(a + 1, int(math.floor(f0 + fl + 1e-6)))
SK, NOS = _ytor(_skalle), _ytor(_nos)
# ANSIKTETS FRAMSIDA har heltalskanter (uv 32,0 med måtten 6x5x4), så här är
# int() ofarligt — men det skrivs ut i klartext så nästa modelländring inte
# tyst ärver ett antagande som slutat gälla.
FX, FY = int(SK["north"][0]), int(SK["north"][1])
assert (FX, FY) == (SK["north"][0], SK["north"][1]), \
    "skallens framsida ligger inte på hela texlar — ansiktsrutnätet stämmer inte"

# Ansiktet är 6x5. Kolumnerna 0-1 och 4-5 är ögon, 2-3 är nospartiet.
OGON_KOL = ((0, 1), (4, 5))
MITT_KOL = (2, 3)
ROSA = (226, 140, 160)          # nosens rosa
GLANS = (255, 255, 255)


def blanda(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def katterna():
    """Alla entiteter som faktiskt använder kattmodellen. Läses ur paketet, så
    en ny ras får ett ansikte utan att någon minns att lägga till den här."""
    ut = []
    for f in sorted(glob.glob(f"{RP}/entity/*.json")):
        d = json.load(open(f))["minecraft:client_entity"]["description"]
        if d.get("geometry", {}).get("default") == "geometry.katt":
            ut.append((d["identifier"].split(":")[1], d["textures"]["default"]))
    return ut


def mala(namn, texvag):
    w, h, px = rr.read_png(f"{RP}/{texvag}.png")

    def las(kol, rad):
        return tuple(px[FY + rad][FX + kol])

    def satt(kol, rad, rgb, alfa):
        px[FY + rad][FX + kol] = tuple(rgb) + (alfa,)

    def yta(sida, rgb, alfa, rad=None, ytor=None):
        x0, y0, fw, fh = (ytor or NOS)[sida]
        ya, yb = _tacker(y0, fh)
        xa, xb = _tacker(x0, fw)
        for y in range(ya, yb):
            if rad is not None and y - ya != rad:
                continue
            for x in range(xa, xb):
                px[y][x] = tuple(rgb) + (alfa,)

    # KÄLLFÄRGER. Pälsen och nospartiet skrivs aldrig av skriptet, så de kan
    # läsas om och om igen; irisen skrivs tillbaka oförändrad.
    pals = las(2, 0)[:3]
    alfa = las(2, 0)[3]                       # spökkattens 150 måste överleva
    iris_ljus = las(0, 2)[:3]
    iris_mork = las(0, 1)[:3]
    # MÖRKRET RÄKNAS UR PÄLSEN, inte ur konturpixeln. Konturpixeln är en av dem
    # skriptet skriver över, och att läsa den vore att läsa sin egen förra
    # körning.
    mork = blanda(pals, (0, 0, 0), 0.80)
    # NOSPARTIET LJUSAS ALLTID UPP. På Hazel och Snow är rutan bredvid munnen en
    # vit haklapp, men på Misty och Mocha är den bara päls — och en nos i exakt
    # pälsfärg syns inte att den sticker ut, hur mycket geometri man än lägger
    # på. En riktig katt har ljusare nosparti; det är den kontrasten som gör att
    # nosen läser som en nos i stället för som en bula.
    nosparti = blanda(las(1, 4)[:3], (255, 255, 255), 0.30)

    for kols in OGON_KOL:
        yttre, inre = (kols[0], kols[1]) if kols[0] < 2 else (kols[1], kols[0])
        # RAD 1: mörk ögonvrå ute, glansprick inne. Glansen är det enda som
        # skiljer ett öga från en knapp.
        satt(yttre, 1, iris_mork, alfa)
        satt(inre, 1, GLANS, alfa)
        # RAD 2: klar iris, båda texlarna.
        for kol in kols:
            satt(kol, 2, iris_ljus, alfa)
        # RAD 3: ÖGAT VÄXER NEDÅT. Ett öga på 2x2 i ett ansikte som är 5 texlar
        # högt är ett vuxet öga; 2x3 är ett kattungeöga, och det är hela
        # skillnaden mellan "katt" och "gullig katt". Nedre kanten är en mörkare
        # ton av irisen, inte den klara — annars buktar ögat ut.
        for kol in kols:
            satt(kol, 3, blanda(iris_ljus, iris_mork, 0.45), alfa)
        # PANNAN VAR ETT SVART BAND tvärs över ansiktet, och ett band som det
        # ensamt gör en katt bister. Den mjukas mot pälsen så pannan blir en
        # skugga i stället för en ram.
        for kol in kols:
            satt(kol, 0, blanda(mork, pals, 0.34), alfa)
        # KINDEN. Ytterhörnet nedtill var nästan svart och ramade in ansiktet
        # hårt; det ljusas mot nosens rosa — en antydan till kindrodnad.
        satt(yttre, 4, blanda(mork, (206, 132, 138), 0.40), alfa)

    # BAKOM NOSEN — OCH HAKAN. Raderna 3-4 i mitten bar förr nosen och munnen.
    # Nu skyms de av nos-kuben, utom den nedersta biten: nosen sitter 0,6 enheter
    # ÖVER hakan, så remsan under den syns och är kattens haka. Först satt nosen
    # i liv med huvudets underkant och katten hade ingen haka alls — hela nedre
    # framkanten stack ut i ett stycke. Båda raderna målas i nospartiets ljusa
    # färg: det som skyms behöver bara vara ofarligt, det som syns blir haka.
    for kol in MITT_KOL:
        for rad in (3, 4):
            satt(kol, rad, nosparti, alfa)

    # NOS-KUBEN. Ljust nosparti runt om, rosa nos överst på framsidan och en varm
    # mun under den. Munnen var förr ett svart streck rakt över två texlar; på en
    # platt yta blev det ett bistert drag, på en kub som sticker ut blir samma
    # två texlar en mun.
    for sida in ("top", "bottom", "north", "south", "east", "west"):
        yta(sida, nosparti, alfa)
    yta("bottom", blanda(nosparti, mork, 0.35), alfa)          # skugga under hakan
    yta("north", ROSA, alfa, rad=0)                            # nosen
    yta("north", blanda(mork, (150, 108, 104), 0.55), alfa, rad=1)   # munnen

    # KINDTOTTARNA OCH ÖRONSPETSARNA. Nya kuber som bryter rektangeln; de måste
    # målas här eftersom konsten i art/kattpalsar/ inte känner till dem, och en
    # omålad kub är genomskinlig — alltså osynlig, vilket ser exakt ut som att
    # den inte finns.
    #
    # KINDEN ÄR NÅGOT MÖRKARE än pälsen. Lika ljus som huvudet smälter den ihop
    # med det och tar bort hela vinsten; för mörk blir den en fläck. En tiondel
    # mot mörkret räcker för att konturen ska läsa som en tott och inte som en
    # utbuktning.
    # KINDERNA MÅLAS I EXAKT PÄLSFÄRG. Första försöket gjorde dem en aning
    # mörkare för att "synas", och då lossnade de från huvudet och såg ut som två
    # påklistrade flikar. Silhuetten gör redan jobbet — det är att konturen byter
    # bredd som läser som en kind, inte att ytan har en annan ton.
    for kub in _KINDER:
        for sida in ("top", "bottom", "north", "south", "east", "west"):
            yta(sida, pals, alfa, ytor=_ytor(kub))

    # ÖRONEN ÄGS HÄR NU. De var två kuber på 2,4x2,5 — halva huvudets bredd och
    # halva dess höjd var — och det var de som gjorde huvudet fyrkantigt: två
    # torn ovanpå en låda. Nu är de en bred låg bas och en smal hög spets, alltså
    # en kontur som smalnar av på vägen upp. Konsten i art/kattpalsar/ målar
    # fortfarande den gamla örats uv-ruta, men den rutan har bytt storlek, så
    # skriptet målar om båda kuberna från grunden.
    # INNERÖRAT. En texelkolumn mitt på framsidan, plus de rader som ligger HELT
    # inne i den. Framsidan är 2,4 texlar bred och börjar på ,30 — en jämnbred
    # fläck går därför inte att centrera, men EN kolumn gör det exakt: texel 34
    # spänner 34–35 och framsidans mitt ligger på 34,50.
    #
    # ÖRATS EGEN FÄRG LÄSES UR ÖRAT, inte ur ansiktet. Snow är ragdoll och Mocha
    # birma — de har mörkare "points" på just öronen än i ansiktet, och att måla
    # om örat i ansiktets färg hade tagit bort hela rasmarkeringen.
    for kub in _ORON:
        ytor = _ytor(kub)
        fx, fy, fw, fh = ytor["north"]
        rakn = {}
        for y in range(*_tacker(fy, fh)):
            for x in range(*_tacker(fx, fw)):
                rakn[tuple(px[y][x][:3])] = rakn.get(tuple(px[y][x][:3]), 0) + 1
        oronpals = max(rakn, key=rakn.get)
        # HELA KUBEN MÅLAS OM först, så det gamla snedställda innerörat och dess
        # läckage ut på sidoytan försvinner. Örat bär ingen annan teckning.
        for sida in ("top", "bottom", "north", "south", "east", "west"):
            yta(sida, oronpals, alfa, ytor=ytor)
        # BLANDNINGEN ÄR ADAPTIV. En fast andel gav Misty kontrast 19 och Snow 24:
        # grått och rosa ligger nära varandra i ljushet, så samma steg mot rosa
        # syns mycket sämre på en grå katt än på en svart. Andelen ökas tills
        # skillnaden räcker, och taket 0,88 finns för att ett inneröra som är
        # RENT rosa ser målat ut i stället för hudfärgat.
        avst = sum(abs(ROSA[i] - oronpals[i]) for i in range(3)) / 3
        t = 0.60 if avst <= 0 else min(0.88, max(0.60, 28.0 / avst))
        kol = int(fx + fw / 2)
        ya, yb = _inre(fy, fh)
        for y in range(ya, yb):
            px[y][kol] = blanda(oronpals, ROSA, t) + (alfa,)

    rr.write_png(f"{RP}/{texvag}.png", w, h, px)
    return iris_ljus, alfa


if __name__ == "__main__":
    print(f"ansikte {SK['north'][2]}x{SK['north'][3]} @ {SK['north'][:2]}  "
          f"nos {NOS['north'][2]}x{NOS['north'][3]} @ {NOS['north'][:2]}")
    for namn, tex in katterna():
        iris, alfa = mala(namn, tex)
        print(f"  {namn:10s} iris {str(iris):18s} alfa {alfa}")
