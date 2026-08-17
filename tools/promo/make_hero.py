#!/usr/bin/env python3
"""Hjältebild: ordmärket och alla sex katterna i en spelmiljö.

Butiksbilderna visade katterna som modeller mot mörk fond — korrekt, men det
ser ut som ett modellark, inte som ett spel. Den här bilden gör samma sak som
Cat Havens hjältebild redan gör: komponerar RIKTIGA modellrenderingar (samma
motor som bildregressionen och trailern) mot en procedurell björkäng.

  publish/purrfect-hero.png   1280x720 — sajt, CurseForge, MCPEDL

Ingen Minecraft-klient finns på maskinen, så en riktig skärmdump går inte att
ta här. Allt ritas i block om 16 px så miljön läser som Minecraft i stället
för som en målning: gräset varierar per block, björkarna har stammar med
streck, molnen är rutor.

    python3 tools/promo/make_hero.py
"""
import math, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_regression as rr
import make_video as mv

W, H = 1280, 720
# make_video.text() och paste() klipper mot SIN modulnivås W/H — trailerns
# 480x270. Utan den här raden försvann alla sex katterna (de klistras under
# y=270) och ordmärket kapades mitt i ordet. Verktygen är skrivna för
# trailern; vi lånar dem och måste tala om vilken duk de ritar på.
mv.W, mv.H = W, H
B = 16                                    # blockstorlek i pixlar
HORISONT = int(H * 0.52)

HIMMEL_TOPP = (108, 166, 232)
HIMMEL_BOTTEN = (186, 216, 240)
GRAS = [(106, 152, 62), (98, 143, 58), (114, 160, 66), (90, 134, 54)]
JORD = [(122, 88, 60), (110, 79, 54)]
BJORK_BARK = (222, 222, 214)
BJORK_STRECK = (58, 58, 54)
LOV = [(74, 128, 52), (64, 114, 46), (84, 140, 58)]
KULLE = (78, 118, 52)

CATS = ["misty", "hazel", "mocha", "snow", "ginger", "domino"]


def slump(n):
    """Deterministiskt brus — bilden ska bli IDENTISK varje körning, annars
    blir varje ombyggnad en ny bild att granska."""
    n = (n * 1103515245 + 12345) & 0x7FFFFFFF
    return (n >> 16) & 0x7FFF


def duk():
    img = []
    for y in range(H):
        k = min(1.0, y / HORISONT)
        img.append([tuple(int(HIMMEL_TOPP[i] + (HIMMEL_BOTTEN[i] - HIMMEL_TOPP[i]) * k)
                          for i in range(3)) + (255,)] * W)
    return [list(r) for r in img]


def rita(img, x0, y0, w, h, c):
    for y in range(int(y0), int(y0 + h)):
        for x in range(int(x0), int(x0 + w)):
            if 0 <= y < H and 0 <= x < W:
                img[y][x] = c


def moln(img):
    for i, (cx, cy, bredd) in enumerate([(3, 3, 7), (26, 2, 5), (48, 4, 6), (64, 2, 4)]):
        for b in range(bredd):
            hoj = 1 + (slump(i * 13 + b) % 2)
            rita(img, (cx + b) * B, (cy + (b % 2)) * B, B, hoj * B, (246, 250, 255, 255))


def kullar(img):
    """Två lager kullar i blockform bakom ängen — ger djup utan att ta fokus."""
    for lager, (bas, farg) in enumerate([(HORISONT - 2 * B, (92, 132, 64)),
                                         (HORISONT - B, KULLE)]):
        for bx in range(0, W // B + 1):
            hoj = (slump(bx * 7 + lager * 91) % 3) * (B // 2)
            rita(img, bx * B, bas - hoj, B, hoj + 3 * B, farg + (255,))


def mark(img):
    """Ängen sedd framifrån: GRÄSTOPPAR hela vägen ner, inte en jordvägg.

    Första försöket la två rader gräs och fyllde resten med jord — det blev en
    tvärsnittsbild av marken, som om man tittade in i en grop. Man ser inte
    jordlagret när man står på en äng."""
    for by, y in enumerate(range(HORISONT, H, B)):
        for bx, x in enumerate(range(0, W, B)):
            n = slump(bx * 31 + by * 17)
            c = GRAS[n % len(GRAS)]
            # ljusare längre bort, mörkare i förgrunden — ger djup utan dimma
            f = 0.88 + min(0.26, by * 0.022)
            rita(img, x, y, B, B, tuple(min(255, int(v * f)) for v in c) + (255,))
            if n % 6 == 0:                                   # grässtrån
                rita(img, x + (n % 12), y + 2, 2, B // 3, (128, 176, 74, 255))
            if n % 47 == 0:                                  # enstaka blomma
                rita(img, x + 6, y + 4, 4, 4, [(255, 214, 66, 255), (255, 255, 255, 255),
                                               (240, 120, 170, 255)][n % 3])


def bjork(img, bx, marknivå, hojd):
    """Björkstam med streck och en lövkrona — samma träd som i skogen där
    Ginger bor, och de syns i barnens egen skärmdump."""
    x = bx * B
    rita(img, x, marknivå - hojd * B, B, hojd * B, BJORK_BARK + (255,))
    for i in range(hojd):
        if slump(bx * 5 + i) % 3 == 0:
            rita(img, x, marknivå - (i + 1) * B + B // 3, B, B // 3, BJORK_STRECK + (255,))
    top = marknivå - hojd * B
    for ly in range(-3, 2):
        bredd = 5 - abs(ly)
        for lx in range(-(bredd // 2), bredd // 2 + 1):
            n = slump(bx * 3 + lx * 11 + ly * 7)
            if n % 7 == 0:
                continue                                    # luckor i kronan
            rita(img, x + lx * B, top + ly * B, B, B, LOV[n % len(LOV)] + (255,))


def katt(img, cat, plagg, cx, cy, hojd, yaw, t):
    src = rr.render(cat, plagg, mv.walk_pose(t), W=260, H=260, yaw=yaw, pitch=9)
    bg = src[0][0]

    def nara(p):
        return abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) < 18
    nyckl = [[(p[0], p[1], p[2], 0 if nara(p) else 255) for p in row] for row in src]
    # SKUGGAN måste ligga där tassarna landar, inte där mitten av bilden är:
    # renderingen har luft under katten, så en skugga vid cy hamnade en bit
    # under djuret och det såg ut att strax lyfta. Mätt: fötterna ligger runt
    # 88 % ner i rutan.
    fot_y = cy - hojd // 2 + int(hojd * 0.38)
    for i, (bredd, m) in enumerate(((0.62, 0.82), (0.44, 0.66))):
        w2 = int(hojd * bredd)
        rita(img, cx - w2 // 2, fot_y - i, w2, 3 - i,
             tuple(int(v * m) for v in (96, 138, 62)) + (255,))
    mv.paste(img, nyckl, 260, 260, cx, cy - hojd // 2, hojd)


def ordmarke(img):
    """Vit text mot ljus himmel gick inte att läsa — en skugga rakt nedåt
    räcker inte när bakgrunden är ljus åt alla håll. Två saker fixar det: ett
    mörkt band bakom texten, och en HELDRAGEN kontur (åtta riktningar) i
    stället för en enkel slagskugga."""
    for y in range(18, 176):
        k = 1.0 - abs(y - 97) / 95.0
        for x in range(W):
            p = img[y][x]
            m = 0.42 + 0.34 * (1 - k)
            img[y][x] = (int(p[0] * m), int(p[1] * m), int(p[2] * m), 255)
    kontur = [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, -2), (-2, 2), (2, 2)]
    for dx, dy in kontur:
        mv.text(img, "PURRFECT COMPANIONS", W // 2 + dx, 58 + dy, 8, (16, 20, 30, 255))
    mv.text(img, "PURRFECT COMPANIONS", W // 2, 58, 8, (255, 255, 255, 255))
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        mv.text(img, "SIX HAND-MADE CATS FOR MINECRAFT BEDROCK", W // 2 + dx, 136 + dy, 3,
                (16, 20, 30, 255))
    mv.text(img, "SIX HAND-MADE CATS FOR MINECRAFT BEDROCK", W // 2, 136, 3, (188, 232, 255, 255))


def bygg():
    img = duk()
    moln(img)
    kullar(img)
    mark(img)
    # träden ramar in bilden; inga mitt i, där ska katterna synas
    for bx, hojd in ((1, 6), (5, 5), (72, 6), (77, 5)):
        bjork(img, bx, HORISONT + B, hojd)

    # SEX KATTER i två djupled: fyra fram, två längre bak och mindre. Några
    # bär plagg — bilden ska visa både vilka katterna är och vad de kan ha på
    # sig, utan att bli en plaggkatalog.
    stallningar = [
        ("mocha",  ["horn2", "vingar1"],   0.26, 0.80, 235, 32, 0.4),
        ("snow",   [],                     0.45, 0.74, 205, 24, 1.3),
        ("misty",  ["vagn1", "halsduk1"],   0.62, 0.83, 250, 44, 2.1),
        ("domino", ["krona1"],             0.83, 0.75, 215, 20, 0.9),
        ("hazel",  ["ryggsack1"],          0.36, 0.65, 150, 46, 1.7),
        ("ginger", [],                     0.72, 0.64, 145, 14, 2.6),
    ]
    for cat, plagg, fx, fy, hojd, yaw, t in stallningar:
        katt(img, cat, plagg, int(W * fx), int(H * fy), hojd, yaw, t)

    ordmarke(img)
    rr.write_png(f"{BASE}/publish/purrfect-hero.png", W, H,
                 [[(p[0], p[1], p[2], 255) for p in rad] for rad in img])
    print(f"  publish/purrfect-hero.png ({W}x{H})")


if __name__ == "__main__":
    bygg()
