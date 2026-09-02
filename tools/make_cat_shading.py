#!/usr/bin/env python3
"""Points, tassar och form på kroppen — det som gör kroppen till mer än ett fält.

Bakgrund: spelaren som är konstnär skrev att det är jobbigt att titta på
katterna. Mätt per kroppsdel hade hen rätt, och det gick att sätta siffror på:
huvudet har tolv toner, men Snows SVANS var 100 % en enda ton, hennes ben 95 %
och kroppen 79 %. Aurora, Nova, Midnight och Spökkatten hade noll variation alls
utanför huvudet. En kropp som är ett färgfält läser som en låda oavsett hur bra
ansiktet är.

Två av felen var inte "platt" utan FEL RAS:

  * Snow är ragdoll. Hennes ÖRON är grå mot en vit kropp — hon HAR points i
    konsten — men svansen och benen var helvita. Points hör till öron, ansikte,
    svans och ben; hon hade dem på en av fyra.
  * Mocha är birma och hade sina points överallt, men en birma har VITA HANDSKAR
    på tassarna. Hennes ben var bruna ända ner.

Resten är rasneutralt: ljus uppifrån på bålen och kontaktskugga där benen och
svansen fäster.

    python3 tools/make_cat_shading.py

KÖRORDNING:
    1. make_cat_markings.py   teckningar på kropparna
    2. make_cat_textures.py   de härledda katterna
    3. make_cat_shading.py    DEN HÄR — points, tassar, form
    4. make_cat_faces.py      ansiktet
    5. build_accessories.py   plaggens UV-ytor

RÖR ALDRIG HUVUDET. Det ägs av make_cat_faces.py, och två skript som skriver på
samma texlar är precis hur öronens rosa försvann en gång redan.

POINTS HÄRLEDS, DE STÅR INTE I EN TABELL. Skiljer örats färg tydligt från
kroppens är katten pointad, och örats färg ÄR då pointfärgen. Det träffar Snow
och Mocha och ingen annan, utan att någon lista behöver hållas i synk.

TRE FÄLLOR SOM KOSTADE TID HÄR, alla värda att minnas:

  * ATT MÄTA ÄR INTE ATT MÅLA. Först mättes färgerna med samma avrundning som
    målningen använder, och den rundar UTÅT för att täcka hela ytan. Örats
    mätning sträckte sig då förbi örats egen ruta och plockade upp den vita ytan
    bredvid: Snows öra räknades till 28 vita texlar mot 16 grå, hon bedömdes som
    opointad, och ragdollen fick inte sina points. Mätning rundar INÅT.
  * SVANSENS TRE KUBER DELAR EN UV-RUTA, och benens fyra likaså. "Mörkare
    svansspets" är därför omöjligt att uttrycka — det målar hela svansen. Det
    syns inte i koden, bara i geometrin.
  * MÄT ALDRIG EN TEXEL DU SJÄLV SKRIVER. Skuggan täcker en stor del av den lilla
    svansrutan, så nästa körning läste sin egen skugga som grundfärg och mörknade
    ett snäpp till — två körningar gav olika filer. Varje mätning här utesluter
    uttryckligen de rader som ska målas.
"""
import json, glob, math, os, sys
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import render_regression as rr

RP = f"{BASE}/PurrfectCompanions_RP"
SIDOR = ("north", "south", "east", "west")

_geo = [g for g in json.load(open(f"{RP}/models/entity/katt.geo.json"))["minecraft:geometry"]
        if g["description"]["identifier"] == "geometry.katt"][0]
BEN = {b["name"]: b.get("cubes", []) for b in _geo["bones"]}


# Pälskornets två toner. De står här för att MÄTNINGEN måste kunna räkna
# tillbaka dem till sin grundfärg — annars ändrar kornet delens dominerande ton
# och nästa körning mäter fel. Se kommentaren vid ton().
KORN_MORK, KORN_LJUS = 0.09, 0.07


def blanda(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def korntoner(f):
    return blanda(f, (0, 0, 0), KORN_MORK), blanda(f, (255, 255, 255), KORN_LJUS)


def fotavtryck(kub):
    """Kubens hela utfällning som texelrektangel, rundat INÅT (för mätning)."""
    u, v = kub["uv"]
    b, h, d = kub["size"]
    return (int(math.ceil(u - 1e-6)), int(math.floor(u + 2 * (d + b) + 1e-6)),
            int(math.ceil(v - 1e-6)), int(math.floor(v + d + h + 1e-6)))


def sidrader(kub):
    """Sidoytornas rader som (första, sista+1). Alla fyra sidor delar rader."""
    _u, v = kub["uv"]
    _b, h, d = kub["size"]
    return int(math.floor(v + d + 1e-6)), int(math.ceil(v + d + h - 1e-6))


def mala(texvag):
    w, h, px = rr.read_png(f"{RP}/{texvag}.png")

    def ton(kub, undanta=()):
        """Kubens dominerande färg, utan de rader som kommer att målas — och med
        pälskornet RÄKNAT TILLBAKA till sin grundfärg.

        Utan den återräkningen ändrar kornet vilken ton som dominerar. Domino och
        Hazel har vita tassar på mörka ben, och där låg vitt bara någon procent
        före svart: kornet tog bort en fjärdedel av de vita texlarna, svart tog
        över som dominerande ton, och nästa körning målade kontaktskuggan i fel
        färg. Två körningar gav olika filer. Det är tredje gången samma regel
        gäller i den här filen — mät aldrig en texel du själv skriver, och om du
        måste, räkna bort din egen påverkan först."""
        xa, xb, ya, yb = fotavtryck(kub)
        c = Counter()
        for y in range(ya, yb):
            if y in undanta:
                continue
            for x in range(xa, xb):
                if px[y][x][3]:
                    c[tuple(px[y][x][:3])] += 1
        if not c:
            return None
        korn = set()
        for f in c:
            korn.update(korntoner(f))
        kandidater = [f for f in c if f not in korn] or list(c)
        return max(kandidater, key=lambda f: c[f] + sum(c.get(k, 0) for k in korntoner(f)))

    def sat(kub, sidor, rader, rgb):
        F = rr.faces(kub["uv"][0], kub["uv"][1], *kub["size"])
        for namn, (x0, y0, fw, fh) in F.items():
            if namn not in sidor:
                continue
            xa = int(math.floor(x0 + 1e-6)); xb = int(math.ceil(x0 + fw - 1e-6))
            ya = int(math.floor(y0 + 1e-6)); yb = int(math.ceil(y0 + fh - 1e-6))
            for y in range(ya, yb):
                if y not in rader:
                    continue
                for x in range(xa, xb):
                    if px[y][x][3]:
                        px[y][x] = tuple(rgb) + (px[y][x][3],)

    bal, tass, svans = BEN["body"][0], BEN["leg0"][0], BEN["tail"][0]
    ba, bb = sidrader(bal)
    ta, tb = sidrader(tass)
    sa, sb = sidrader(svans)

    kropp = ton(bal, undanta={ba, bb - 1})
    orkuber = [k for k in BEN["head"] if k["uv"] in ([32, 10], [40, 10])]
    c = Counter()
    for k in orkuber:
        xa, xb, ya, yb = fotavtryck(k)
        for y in range(ya, yb):
            for x in range(xa, xb):
                if px[y][x][3]:
                    c[tuple(px[y][x][:3])] += 1
    ora = c.most_common(1)[0][0]

    tassgrund = ton(tass, undanta={ta, tb - 1})
    svansgrund = ton(svans, undanta={sb - 1})

    pointad = sum(abs(kropp[i] - ora[i]) for i in range(3)) / 3 >= 25
    gjort = []

    if pointad:
        # POINTS PÅ SVANS OCH BEN, i örats färg.
        sat(svans, SIDOR + ("top", "bottom"), set(range(sa - 4, sb + 4)), ora)
        sat(tass, SIDOR, set(range(ta, tb)), ora)
        # VITA HANDSKAR — birmans signatur och ragdollens vita tassar, och det
        # som gör att benet slutar vara ett fält.
        sat(tass, SIDOR, {tb - 1}, kropp)
        sat(tass, ("bottom",), set(range(0, 999)), kropp)
        tassgrund = svansgrund = ora
        gjort.append(f"points {ora} + handskar {kropp}")

    # LJUS UPPIFRÅN PÅ BÅLEN — rasneutralt, och det som gör mest för katterna
    # som inte har någon teckning alls. Minecraft skuggar hela YTOR efter
    # väderstreck men aldrig inuti en yta, så en sida av bålen är ett platt fält
    # hur bra motorn än lyser.
    sat(bal, SIDOR, {ba}, blanda(kropp, (255, 255, 255), 0.10))
    sat(bal, SIDOR, {bb - 1}, blanda(kropp, (0, 0, 0), 0.16))

    # KONTAKTSKUGGA där benet möter bålen och där svansen fäster. Tonen räknas ur
    # delens EGEN grundfärg, så en vit tass och ett svart ben får var sin rimliga
    # skugga i stället för samma grå streck.
    sat(tass, SIDOR, {ta}, blanda(tassgrund, (0, 0, 0), 0.22))
    sat(svans, SIDOR, {sb - 1}, blanda(svansgrund, (0, 0, 0), 0.22))
    gjort.append("ljus uppifrån på bålen, kontaktskugga vid ben och svansfäste")

    # PÄLSKORN. Efter points och skuggning låg de enfärgade katterna — Aurora,
    # Nova, Midnight och Spökkatten — fortfarande på 79–86 % en enda ton, för de
    # har ingen teckning att bygga på. En svart katt SKA vara mestadels svart,
    # men även en svart katt i bra pixelkonst har tre eller fyra svarta toner,
    # inte en.
    #
    # KORNET ÄR STRUKTURERAT, INTE SLUMPAT. Ett slumpmönster ovanpå en design är
    # precis det som förstörde blockens texturer — kattluckans katthål försvann
    # i garnets prickar. Skillnaden här är att designen ÄR ett fält: kornet
    # tillför i stället för att dölja. Mönstret är en hash av koordinaterna, så
    # det är samma varje bygge och går att resonera om.
    #
    # BARA PÅ GRUNDTONEN. Ränder, points, handskar och skuggrader har alla en
    # annan färg än delens dominerande ton och rörs därför inte — kornet kan inte
    # äta upp en teckning. Det gör det också idempotent: efter första körningen
    # är korntexlarna inte längre grundtonen, så nästa körning hittar dem inte.
    for bennamn, grund in (("body", kropp), ("leg0", tassgrund), ("tail", svansgrund)):
        mork, ljus = korntoner(grund)
        for kub in BEN[bennamn]:
            xa, xb, ya, yb = fotavtryck(kub)
            for y in range(ya, yb):
                for x in range(xa, xb):
                    if not px[y][x][3] or tuple(px[y][x][:3]) != grund:
                        continue
                    v = (x * 7 + y * 13 + x * y * 3) % 11
                    if v < 2:
                        px[y][x] = mork + (px[y][x][3],)
                    elif v == 5:
                        px[y][x] = ljus + (px[y][x][3],)
    gjort.append("pälskorn")

    rr.write_png(f"{RP}/{texvag}.png", w, h, px)
    return pointad, gjort


def katterna():
    ut = []
    for f in sorted(glob.glob(f"{RP}/entity/*.json")):
        d = json.load(open(f))["minecraft:client_entity"]["description"]
        if d.get("geometry", {}).get("default") == "geometry.katt":
            ut.append((d["identifier"].split(":")[1], d["textures"]["default"]))
    return ut


if __name__ == "__main__":
    for namn, tex in katterna():
        pointad, gjort = mala(tex)
        print(f"  {namn:10s} {'POINTAD  ' if pointad else '         '}{'; '.join(gjort)}")
