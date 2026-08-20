#!/usr/bin/env python3
"""Logga + YouTube-miniatyr för promo-filmen.

Allas katthuvuden renderas rakt framifrån med regressionsmotorn
(bones_for filtreras till bara huvudet), beskärs automatiskt och komponeras:

  publish/video-logo.png        512x512-märke till filmens titelkort
  publish/youtube-thumbnail.png 1280x720 till uppladdningen

Endast publika namn/utseenden — allt är marknadsföring.
"""
import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_regression as rr
from make_video import FONT

CATS = ["misty", "hazel", "mocha", "snow", "ginger", "domino"]


def head_render(cat, size=240, yaw=24, pitch=8):
    """Bara huvudben(et), autobeskuret till innehållet.

    Vinkeln går att välja sedan projektloggan behövde en RAKARE vy: i
    trekvart blir kattens öron breda klumpar och huvudet läser som en björn i
    listrutan. Rakt framifrån syns ansiktet — ögon, nos, två öron — precis
    som på spawnägg-ikonerna, som är ritade för att läsa i 16 px."""
    orig = rr.bones_for
    rr.bones_for = lambda acc: [b for b in orig(acc) if b[0] == "head"]
    try:
        img = rr.render(cat, [], {}, W=size, H=size, yaw=yaw, pitch=pitch)
    finally:
        rr.bones_for = orig
    bgpix = img[0][0]
    xs = [x for y in range(size) for x in range(size) if img[y][x] != bgpix]
    ys = [y for y in range(size) for x in range(size) if img[y][x] != bgpix]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    return [row[x0:x1 + 1] for row in img[y0:y1 + 1]], bgpix


def canvas(w, h):
    top, bot = (26, 26, 46), (22, 33, 62)
    return [[(top[0] + (bot[0] - top[0]) * y // h,
              top[1] + (bot[1] - top[1]) * y // h,
              top[2] + (bot[2] - top[2]) * y // h, 255)] * w for y in range(h)]


def blit_scaled(dst, src, bgpix, cx, cy, out_h):
    sh, sw = len(src), len(src[0])
    k = sh / out_h; out_w = int(sw / k)
    W, H = len(dst[0]), len(dst)
    for oy in range(out_h):
        for ox in range(out_w):
            p = src[min(sh - 1, int(oy * k))][min(sw - 1, int(ox * k))]
            if p == bgpix: continue
            px, py = cx - out_w // 2 + ox, cy - out_h // 2 + oy
            if 0 <= px < W and 0 <= py < H:
                dst[py][px] = p


def text(dst, s, cx, y, scale, col=(235, 240, 250, 255)):
    W, H = len(dst[0]), len(dst)
    w = len(s) * 6 * scale - scale
    x0 = cx - w // 2
    for i, ch in enumerate(s.upper()):
        for ry, row in enumerate(FONT.get(ch, FONT[" "])):
            for rx, c in enumerate(row):
                if c != "#": continue
                for dy in range(scale):
                    for dx in range(scale):
                        px, py = x0 + (i * 6 + rx) * scale + dx, y + ry * scale + dy
                        if 0 <= px < W and 0 <= py < H:
                            dst[py][px] = col


heads = {c: head_render(c) for c in CATS}

# --- märket: 2x2 huvuden + ordmärke -----------------------------------------
S = 512
logo = canvas(S, S)
# 3x2 sedan katterna blev sex. Huvudena krymper från 165 till 128 px så
# raderna får plats ovanför ordmärket i stället för att växa in i det.
POS = [(108, 128), (256, 128), (404, 128),
       (108, 286), (256, 286), (404, 286)]
for (c, (img, bg)), (cx, cy) in zip(heads.items(), POS):
    blit_scaled(logo, img, bg, cx, cy, 128)
text(logo, "PURRFECT", S // 2, 428, 6, (0, 212, 255, 255))
text(logo, "COMPANIONS", S // 2, 476, 4)
rr.write_png(f"{BASE}/publish/video-logo.png", S, S, logo)

# --- projektloggan: ETT ansikte, stort ------------------------------------
# CurseForge visar den i avatarstorlek. Den gamla var en hel katt i 3/4 med
# sadel, keps, halsband och tossor — vid 64 px blev allt det gröt och kvar
# blev "grått djur med nåt blått på huvudet". Ett ansikte som fyller rutan
# läser i alla storlekar, och Ginger är den som syns bäst mot mörk botten.
# ---------------------------------------------------------------------------
# PROJEKTAVATAREN: SÅ MÅNGA KATTER SOM MÖJLIGT, i miljö och med plagg.
#
# Vägen hit gick via tre försök som alla föll. En hel katt i 3/4 med plagg blev
# gröt vid 130 px. Ett stort renderat ansikte läste som kanin — modellens öron
# är två höga rektanglar framifrån. Ett ritat 32x32-ansikte blev snyggare men
# sa bara "en katt", och det är inte vad paketet handlar om.
#
# Grannarna i CurseForge-listan som fungerar bäst är skinpaketen: ett collage
# av MÅNGA figurer säger på en halv sekund vad man får. Sex katter i två rader,
# var och en med något på sig, mot en riktig äng — och en ram runt alltihop så
# rutan håller ihop mot listans mörka bakgrund.
P = 512
FRAM = int(P * 0.46)          # horisonten
proj = [[(0, 0, 0, 255)] * P for _ in range(P)]
for y in range(P):
    k = min(1.0, y / FRAM)
    # MÖRK STIL: djupblå natt som ljusnar en aning mot horisonten. Ljusa
    # pälsar lyfter mot mörkt, och rutan skiljer sig från grannarnas
    # dagsljusbilder i listan utan att för den skull rinna ut i den — ramen
    # och de ljusa katterna håller emot.
    for x in range(P):
        proj[y][x] = (int(16 + 26 * k), int(20 + 34 * k), int(44 + 46 * k), 255)

B = 16                         # blockstorlek, samma pixelspråk som hjältebilden
def _rita(x0, y0, w, h, c):
    for y in range(int(y0), int(y0 + h)):
        for x in range(int(x0), int(x0 + w)):
            if 0 <= y < P and 0 <= x < P:
                proj[y][x] = c

def _brus(n):
    n = (n * 1103515245 + 12345) & 0x7FFFFFFF
    return (n >> 16) & 0x7FFF

# STJÄRNOR, glesa och små — deterministiska så bilden blir identisk varje
# körning (annars är varje ombyggnad en ny bild att granska).
for i2 in range(46):
    n = _brus(i2 * 977)
    sx, sy = n % P, (n // 7) % int(P * 0.42)
    ljus = 170 + (n % 70)
    _rita(sx, sy, 3, 3, (ljus, ljus, min(255, ljus + 20), 255))
# MÅNEN uppe till höger, med en svag gloria
for y in range(int(P * 0.04), int(P * 0.30)):
    for x in range(int(P * 0.62), int(P * 0.94)):
        d = (((x - P * 0.78) ** 2 + (y - P * 0.16) ** 2) ** 0.5) / (P * 0.115)
        if d < 1.0:
            p4 = proj[y][x]
            f = (1.0 - d) ** 2 * 0.75
            proj[y][x] = (min(255, int(p4[0] + 210 * f)), min(255, int(p4[1] + 215 * f)),
                          min(255, int(p4[2] + 190 * f)), 255)
_rita(int(P * 0.735), int(P * 0.115), int(P * 0.09), int(P * 0.09), (244, 244, 226, 255))
for bx in range(0, P // B + 1):                                            # kullar
    _rita(bx * B, FRAM - B - (_brus(bx * 7) % 2) * (B // 2), B, 3 * B, (22, 40, 30, 255))
GRAS = [(30, 54, 40), (25, 46, 34), (36, 62, 44), (22, 42, 31)]
for by, y in enumerate(range(FRAM, P, B)):                                 # ängen
    for bx, x in enumerate(range(0, P, B)):
        n = _brus(bx * 31 + by * 17)
        f = 0.9 + min(0.22, by * 0.03)
        c = GRAS[n % len(GRAS)]
        _rita(x, y, B, B, tuple(min(255, int(v * f)) for v in c) + (255,))
        if n % 5 == 0:
            _rita(x + (n % 11), y + 2, 2, B // 3, (44, 74, 50, 255))
        if n % 41 == 0:                       # nattblommor, dova
            _rita(x + 5, y + 5, 4, 4, [(196, 168, 96, 255), (206, 206, 214, 255),
                                       (190, 112, 148, 255)][n % 3])

# KATTERNA: bakre raden mindre och högre upp, främre större. Var och en bär
# något — poängen är att visa både antalet och att de går att klä.
import render_preview as rp
UPPSTALLNING = [
    # HÖJDERNA ÄR RÄKNADE MOT RAMEN: främre radens tassar hamnade utanför
    # rutan vid 0.855/224 — en logga med avklippta fötter ser trasig ut.
    # Fotlinjen ligger nu på 0.80 av höjden, med marginal till ramens 0.99.
    ("hazel",  ["keps1", "halsduk2"],   0.19, 0.585, 150),
    ("mocha",  ["horn2", "vingar1"],    0.50, 0.555, 146),
    ("domino", ["krona1"],              0.81, 0.585, 150),
    ("misty",  ["sadel1", "halsband1"], 0.27, 0.800, 196),
    ("snow",   ["doktorsrock1"],        0.55, 0.825, 202),
    ("ginger", ["mantel2", "tossor1"],  0.83, 0.795, 192),
]
for cat, plagg, fx, fy, hojd in UPPSTALLNING:
    src = rp.render3d(cat, plagg, 260, 260)
    bgp = src[0][0]
    # BAKGRUNDEN MÅSTE BLI EXAKT sentinelfärgen: blit_scaled jämför pixlar mot
    # ett värde, inte mot alfa. Första försöket behöll r,g,b och satte bara
    # alfa=0 — då matchade ingenting och varje katt fick en svart ruta runt sig.
    TOM = (0, 0, 0, 0)
    nyckl = [[TOM if p2 == bgp else (p2[0], p2[1], p2[2], 255) for p2 in rad] for rad in src]
    _rita(int(P * fx) - hojd // 3, int(P * fy) - 4, (hojd * 2) // 3, 5, (22, 38, 28, 255))
    blit_scaled(proj, nyckl, TOM, int(P * fx), int(P * fy) - hojd // 2, hojd)

# HJÄRTAN i himlen — det är det gulliga inslaget, och de får INTE ligga över
# katterna: en logga ska läsa på en halv sekund, och prydnad framför motivet
# gör tvärtom.
def _hjarta(hx, hy, sk, c):
    mall = ["..##.##..", ".#######.", ".#######.", "..#####..", "...###...", "....#...."]
    for ry, rad in enumerate(mall):
        for rx, tecken in enumerate(rad):
            if tecken == "#":
                _rita(hx + rx * sk, hy + ry * sk, sk, sk, c)
for hx, hy, sk in ((int(P * 0.09), int(P * 0.30), 3), (int(P * 0.86), int(P * 0.22), 4),
                   (int(P * 0.70), int(P * 0.36), 2)):
    _hjarta(hx, hy, sk, (255, 150, 180, 255))

# INGEN TEXT. Ordmärket ströks helt på begäran — och det stämmer med hur
# rutan används: CurseForge skriver ut projektnamnet bredvid avataren ändå,
# och utan remsa nertill får katterna hela ytan.

# RAMEN: mörk kant med en ljus innerlinje, så rutan håller ihop mot listans
# mörka bakgrund i stället för att rinna ut i den.
for t in range(6):
    for x in range(P):
        proj[t][x] = proj[P - 1 - t][x] = (14, 22, 30, 255)
    for y in range(P):
        proj[y][t] = proj[y][P - 1 - t] = (14, 22, 30, 255)
for x in range(6, P - 6):
    proj[6][x] = proj[P - 7][x] = (0, 212, 255, 255)
for y in range(6, P - 6):
    proj[y][6] = proj[y][P - 7] = (0, 212, 255, 255)
rr.write_png(f"{BASE}/publish/logo.png", P, P, proj)

# --- miniatyren: huvuden till vänster, budskap till höger -------------------
TW, TH = 1280, 720
th = canvas(TW, TH)
TPOS = [(160, 200), (390, 200), (620, 200),
        (160, 460), (390, 460), (620, 460)]
for (c, (img, bg)), (cx, cy) in zip(heads.items(), TPOS):
    blit_scaled(th, img, bg, cx, cy, 200)
text(th, "PURRFECT", 985, 190, 9, (0, 212, 255, 255))
text(th, "COMPANIONS", 985, 290, 6)
# Stod "4 CATS . 12 OUTFITS" — fel i BÅDA leden sedan länge; det är sex
# katter och tjugo plagg.
text(th, "6 CATS . 20 OUTFITS", 985, 400, 4)
text(th, "TAME . RIDE . BREED", 985, 450, 4)
text(th, "MINECRAFT BEDROCK", 985, 540, 3, (150, 200, 255, 255))
rr.write_png(f"{BASE}/publish/youtube-thumbnail.png", TW, TH, th)
print("video-logo.png + youtube-thumbnail.png klara")
