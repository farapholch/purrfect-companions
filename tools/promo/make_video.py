#!/usr/bin/env python3
"""Promo-video för YouTube — renderad helt med vår egen z-buffrade motor.

Samma renderare som bildregressionen (render_regression.render) gör videorutor:
gångcykeln animeras med samma matematik som spelets animationer, kameran
sveper, plaggen visas ett i taget. Ingen Minecraft-klient, ingen PIL, inget
ljud (Pelle lägger musik från YouTubes ljudbibliotek — licensfritt där).

Rutor renderas i 480×270 och skalas till 1080p med NÄRMSTA GRANNE — pixellooken
är en del av Minecraft-estetiken, inte en kompromiss.

ENDAST publika namn — videon är marknadsföring.

Titelkortets räkneord följer CATS-listan. Det stod "FOUR" i klartext och blev
fel i samma stund som femte och sjätte katten kom; en trailer som räknar fel
är värre än ingen trailer.

    python3 tools/promo/make_video.py            # full render (~10-15 min)
    python3 tools/promo/make_video.py --smoke    # var 30:e ruta, snabbkoll
"""
import math, multiprocessing, os, shutil, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)
import render_regression as rr

W, H, FPS = 480, 270, 30
OUTDIR = "/tmp/promo-frames"
OUT = "/tmp/purrfect-promo.mp4"
GIF = f"{BASE}/publish/purrfect-trailer.gif"
KATTGIF = f"{BASE}/publish/purrfect-cats.gif"
SMOKE = "--smoke" in sys.argv

# ---------------------------------------------------------------- 5x7-font --
# Ingen PIL på maskinen — egen bitmappsfont för versaler och det lilla som
# behövs i skyltarna.
FONT = {c: rows.split() for c, rows in {
 "A": ".###. #...# #...# ##### #...# #...# #...#",
 "B": "####. #...# #...# ####. #...# #...# ####.",
 "C": ".###. #...# #.... #.... #.... #...# .###.",
 "D": "####. #...# #...# #...# #...# #...# ####.",
 "E": "##### #.... #.... ####. #.... #.... #####",
 "F": "##### #.... #.... ####. #.... #.... #....",
 "G": ".###. #...# #.... #.### #...# #...# .###.",
 "H": "#...# #...# #...# ##### #...# #...# #...#",
 "I": "##### ..#.. ..#.. ..#.. ..#.. ..#.. #####",
 "K": "#...# #..#. #.#.. ##... #.#.. #..#. #...#",
 "L": "#.... #.... #.... #.... #.... #.... #####",
 "M": "#...# ##.## #.#.# #.#.# #...# #...# #...#",
 "N": "#...# ##..# #.#.# #..## #...# #...# #...#",
 "O": ".###. #...# #...# #...# #...# #...# .###.",
 "P": "####. #...# #...# ####. #.... #.... #....",
 "R": "####. #...# #...# ####. #.#.. #..#. #...#",
 "S": ".###. #...# #.... .###. ....# #...# .###.",
 "T": "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
 "U": "#...# #...# #...# #...# #...# #...# .###.",
 "W": "#...# #...# #...# #.#.# #.#.# ##.## #...#",
 # J, Q, V och X saknades helt, och text() byter tyst ut en okänd bokstav mot
 # mellanslag. Titelkortet skrev "SI HAND-MADE CATS" i en hel renderad trailer
 # innan någon tittade. Hellre fyra glyfer för mycket än en tyst lucka.
 "J": "..### ...#. ...#. ...#. #..#. #..#. .##..",
 "Q": ".###. #...# #...# #...# #.#.# #..#. .##.#",
 "V": "#...# #...# #...# #...# #...# .#.#. ..#..",
 "X": "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
 "Y": "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..",
 "Z": "##### ....# ...#. ..#.. .#... #.... #####",
 ".": "..... ..... ..... ..... ..... ..... ..#..",
 "-": "..... ..... ..... .###. ..... ..... .....",
 "+": "..... ..#.. ..#.. ##### ..#.. ..#.. .....",
 " ": "..... ..... ..... ..... ..... ..... .....",
 "0": ".###. #...# #..## #.#.# ##..# #...# .###.",
 "1": "..#.. .##.. ..#.. ..#.. ..#.. ..#.. #####",
 "2": ".###. #...# ....# ..##. .#... #.... #####",
 "3": ".###. #...# ....# ..##. ....# #...# .###.",
 "4": "...#. ..##. .#.#. #..#. ##### ...#. ...#.",
 "5": "##### #.... ####. ....# ....# #...# .###.",
 "6": ".###. #.... #.... ####. #...# #...# .###.",
 "7": "##### ....# ...#. ..#.. .#... .#... .#...",
 "8": ".###. #...# #...# .###. #...# #...# .###.",
 "9": ".###. #...# #...# .#### ....# ....# .###.",
}.items()}


def text(img, s, cx, y, scale=2, col=(235, 240, 250, 255)):
    """Centrerad pixeltext på bildens rader (muterar img)."""
    w = len(s) * 6 * scale - scale
    x0 = cx - w // 2
    for i, ch in enumerate(s.upper()):
        rows = FONT.get(ch, FONT[" "])
        for ry, row in enumerate(rows):
            for rx, c in enumerate(row):
                if c != "#": continue
                for dy in range(scale):
                    for dx in range(scale):
                        px, py = x0 + (i * 6 + rx) * scale + dx, y + ry * scale + dy
                        if 0 <= px < W and 0 <= py < H:
                            img[py][px] = col


def bg_gradient():
    top, bot = (26, 26, 46), (22, 33, 62)          # sajtens gradient
    return [[(top[0] + (bot[0] - top[0]) * y // H,
              top[1] + (bot[1] - top[1]) * y // H,
              top[2] + (bot[2] - top[2]) * y // H, 255)] * W for y in range(H)]


def paste(img, src, sw, sh, cx, cy, out_h):
    """Klistra in src nedskalad (boxmedel) till out_h hög, centrerad på cx,cy."""
    k = sh / out_h; out_w = int(sw / k)
    for oy in range(out_h):
        for ox in range(out_w):
            x0, x1 = int(ox * k), max(int(ox * k) + 1, int((ox + 1) * k))
            y0, y1 = int(oy * k), max(int(oy * k) + 1, int((oy + 1) * k))
            rs = gs = bs = As = n = 0
            for yy in range(y0, min(y1, sh)):
                for xx in range(x0, min(x1, sw)):
                    p = src[yy][xx]; rs += p[0]; gs += p[1]; bs += p[2]; As += p[3]; n += 1
            if n and As / n > 40:
                px, py = cx - out_w // 2 + ox, cy - out_h // 2 + oy
                if 0 <= px < W and 0 <= py < H:
                    img[py][px] = (rs // n, gs // n, bs // n, 255)


def walk_pose(t):
    """Samma matematik som animation.katt.walk, i grader."""
    a = math.cos(t * 9.0) * 38
    return {"leg0": (a, 0, 0), "leg3": (a, 0, 0),
            "leg1": (-a, 0, 0), "leg2": (-a, 0, 0),
            "head": (0, math.sin(t * 1.7) * 10, 0),
            "tail": (8, 0, math.sin(t * 2.3) * 16)}


# ---------------------------------------------------------------- scener ----
# Varje scen ger (renderjobb | färdig bild). Jobb kör i arbetarpool.
CATS = [("misty", "MISTY"), ("hazel", "HAZEL"), ("mocha", "MOCHA"), ("snow", "SNOW"),
        ("ginger", "GINGER"), ("domino", "DOMINO")]
OUTFITS = [("sadel1", "SADDLE"), ("rustning3", "ARMOR"), ("horn2", "UNICORN HORN"),
           ("vingar1", "WINGS"), ("batvingar1", "BAT WINGS"), ("haxhatt1", "WITCH HAT"),
           ("tomteluva1", "SANTA HAT"), ("doktorsrock1", "DOCTOR COAT"), ("keps1", "CAP"),
           ("halsduk1", "SCARF"), ("ryggsack1", "BACKPACK"), ("glasogon1", "GLASSES"),
           ("mantel1", "CAPE"), ("tossor1", "BOOTIES"), ("halsband1", "COLLAR"),
           ("rosett1", "BOW"), ("krona1", "CROWN"), ("vagn1", "CART")]
FULL = ["rustning3", "horn1", "vingar1", "halsduk1", "tossor2", "vagn1"]
RAKNEORD = {4: "FOUR", 5: "FIVE", 6: "SIX", 7: "SEVEN", 8: "EIGHT"}

# KATTDRÄKTEN. Trailern visade bara vad KATTEN kan bära; sedan 3.28.0 kan
# spelaren bära en egen dräkt i fyra nivåer, och det syntes ingenstans i
# filmen. Delarna har var sin textur, så varje ruta komponeras av fyra
# renderingar med bakgrunden bortnycklad — samma teknik som förhandsbilden.
#
# INFLATE SLÄNGS, precis som i förhandsbilden: renderaren räknar texturytan ur
# kubens mått, så en uppblåst kub läser fel del av bilden.
DRAKT_DELAR = ["luva", "vast", "byxor", "tassar"]
DRAKT_NIVAER = [("", "LEATHER"), ("_jarn", "IRON"),
                ("_diamant", "DIAMOND"), ("_netherit", "NETHERITE")]
DRAKT_RAM = ((-11, 11), (0, 39), (-11, 11))
_DRAKT_BEN = {}


def drakt_ben(del_):
    if del_ not in _DRAKT_BEN:
        import json as _json
        g = _json.load(open(f"{BASE}/PurrfectCompanions_RP/models/entity/mjau_{del_}.geo.json")
                       )["minecraft:geometry"][0]
        _DRAKT_BEN[del_] = [(b["name"], b["pivot"],
                             [{k: v for k, v in c.items() if k != "inflate"} for c in b["cubes"]])
                            for b in g["bones"]]
    return _DRAKT_BEN[del_]


def drakt_ruta(niv, yaw):
    """Hela dräkten i en ruta: fyra renderingar lagda på varandra."""
    bild = bg = None
    for del_ in DRAKT_DELAR:
        orig = rr.bones_for
        rr.bones_for = lambda acc, _l=drakt_ben(del_): _l
        try:
            vy = rr.render(f"mjau_{del_}{niv}", [], {}, W=W, H=H,
                           yaw=yaw, pitch=4, ram=DRAKT_RAM)
        finally:
            rr.bones_for = orig
        if bild is None:
            bild = [list(r) for r in vy]
            bg = vy[0][0]
        else:
            for y in range(H):
                for x in range(W):
                    if vy[y][x] != bg:
                        bild[y][x] = vy[y][x]
    return bild


def scenes():
    out = []
    # 1) titelkort, 2.5 s
    out += [("card_title", i, 75) for i in range(75)]
    # 2) katterna i gångcykel, kamerasvep, 3 s var
    for ci, (cat, label) in enumerate(CATS):
        out += [("cat", ci, i, 90) for i in range(90)]
    # 3) plaggmontage, 0.8 s per plagg
    for oi in range(len(OUTFITS)):
        out += [("outfit", oi, i, 24) for i in range(24)]
    # 4) fullt utrustad, svep, 3 s
    out += [("full", i, 90) for i in range(90)]
    # 4b) kattdräkten: 1,5 s per nivå
    for ni in range(len(DRAKT_NIVAER)):
        out += [("drakt", ni, i, 45) for i in range(45)]
    # 5) slutkort, 4 s
    out += [("card_end", i, 120) for i in range(120)]
    return out


def watermark(img):
    """Diskret stämpel i hörnet på alla scenrutor (slutkortet bär redan adressen).
    Ritas i halvton — vår text() saknar alfa, men dämpad grå på mörk botten
    ger samma intryck."""
    text(img, "PURRFECT.PELLEOPS.SE", W - 70, H - 12, 1, (120, 128, 148, 255))
    return img


def fade(img, i, n, edge=8):
    k = min(1.0, (i + 1) / edge, (n - i) / edge)
    if k >= 1.0: return img
    return [[(int(p[0] * k), int(p[1] * k), int(p[2] * k), 255) for p in row] for row in img]


LOGO = None


def make_frame(job):
    global LOGO
    kind = job[0]
    if kind == "card_title":
        _, i, n = job
        img = bg_gradient()
        if LOGO is None:
            LOGO = rr.read_png(f"{BASE}/publish/video-logo.png")
        lw, lh, lp = LOGO
        # bara huvudena (övre delen) — ordbilden sätter kortet själv, större
        paste(img, lp[:404], lw, 404, W // 2, 96, 132)
        text(img, "PURRFECT COMPANIONS", W // 2, 200, 3)
        text(img, f"{RAKNEORD[len(CATS)]} HAND-MADE CATS FOR MINECRAFT BEDROCK", W // 2, 236, 1)
        return fade(img, i, n)
    if kind == "cat":
        _, ci, i, n = job
        cat, label = CATS[ci]
        t = i / FPS
        img = rr.render(cat, [], walk_pose(t), W=W, H=H, yaw=15 + i * 0.55, pitch=14)
        text(img, label, W // 2, H - 30, 2)
        return fade(watermark(img), i, n)
    if kind == "outfit":
        _, oi, i, n = job
        acc, label = OUTFITS[oi]
        img = rr.render("misty", [acc], {"head": (-8, 18, 0), "tail": (10, 0, 12)},
                        W=W, H=H, yaw=30 + i * 0.3, pitch=14)
        text(img, label, W // 2, H - 30, 2)
        return fade(watermark(img), i, n, edge=4)
    if kind == "full":
        _, i, n = job
        t = i / FPS
        img = rr.render("misty", FULL, walk_pose(t), W=W, H=H, yaw=10 + i * 0.8, pitch=16)
        text(img, "ALL WEARABLE AT THE SAME TIME", W // 2, H - 30, 1)
        return fade(watermark(img), i, n)
    if kind == "drakt":
        _, ni, i, n = job
        niv, etikett = DRAKT_NIVAER[ni]
        img = drakt_ruta(niv, 18 + i * 0.7)
        text(img, etikett + " CAT SUIT", W // 2, H - 30, 2)
        if ni == 0:
            text(img, "AND ONE FOR YOU", W // 2, 16, 1)
        return fade(watermark(img), i, n)
    if kind == "card_end":
        _, i, n = job
        img = bg_gradient()
        text(img, "PURRFECT COMPANIONS", W // 2, 60, 3)
        text(img, "CURSEFORGE . MCPEDL", W // 2, 130, 2)
        text(img, "PURRFECT.PELLEOPS.SE", W // 2, 165, 2)
        text(img, "TAME . RIDE . BREED . DRESS UP", W // 2, 215, 1)
        return fade(img, i, n, edge=15)
    raise ValueError(kind)


def worker(arg):
    idx, job = arg
    img = make_frame(job)
    rr.write_png(f"{OUTDIR}/{idx:05d}.png", W, H, img)
    return idx


def main():
    jobs = scenes()
    if SMOKE:
        jobs = jobs[::30]
    shutil.rmtree(OUTDIR, ignore_errors=True); os.makedirs(OUTDIR)
    print(f"{len(jobs)} rutor à {W}x{H}, {multiprocessing.cpu_count()} kärnor")
    with multiprocessing.Pool(min(5, multiprocessing.cpu_count())) as pool:
        for k, _ in enumerate(pool.imap_unordered(worker, list(enumerate(jobs)), chunksize=8)):
            if k % 100 == 0: print(f"  {k}/{len(jobs)}")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
        "-i", f"{OUTDIR}/%05d.png",
        "-vf", "scale=1920:1080:flags=neighbor",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", OUT,
    ], check=True)
    dur = len(jobs) / FPS
    print(f"klar: {OUT} ({dur:.1f} s, {os.path.getsize(OUT)//1024} kB)")
    gif()


def gif():
    """README:s och sajtens loopande trailer.

    Fanns inte som byggsteg: publish/purrfect-trailer.gif var handgjord en gång
    med ffmpeg och visade fyra katter långt efter att det blivit sex. Nu faller
    den ut ur samma rutor som videon.

    Egen palett (palettegen/paletteuse) — standardpaletten gör grus av
    pixelkonsten. 12 rutor/s och halva bredden håller filen kring en megabyte,
    vilket GitHub och sajten orkar visa direkt.
    """
    if SMOKE:
        return
    paletten = "/tmp/purrfect-gif-palett.png"
    kallor = f"{OUTDIR}/%05d.png"
    # 480 px bred (samma som renderingen, inte halva): 240 px var för smått i
    # CurseForges mediagalleri. 12 rutor/s håller hela 42-sekunderstrailern
    # kring 1,3 MB.
    filter_ = f"fps=12,scale={W}:-1:flags=neighbor"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", kallor, "-vf", f"{filter_},palettegen=max_colors=192",
                    paletten], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", kallor, "-i", paletten,
                    "-lavfi", f"{filter_}[x];[x][1:v]paletteuse=dither=none",
                    "-loop", "0", GIF], check=True)
    print(f"klar: {GIF} ({os.path.getsize(GIF)//1024} kB)")

    # KATTPARADEN som egen kort loop till butikssidor: hela trailern är 42 s
    # och för lång för ett galleri. Rutorna 75-615 är titelkortets slut och de
    # sex kattavsnitten (90 rutor styck) — ändras scenlängderna i scenes()
    # måste intervallet räknas om.
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-start_number", "75", "-t", "18", "-i", kallor,
                    "-vf", "fps=12,scale=480:-1:flags=neighbor,palettegen=max_colors=192",
                    paletten], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-start_number", "75", "-t", "18", "-i", kallor, "-i", paletten,
                    "-lavfi", "fps=12,scale=480:-1:flags=neighbor[x];[x][1:v]paletteuse=dither=none",
                    "-loop", "0", KATTGIF], check=True)
    print(f"klar: {KATTGIF} ({os.path.getsize(KATTGIF)//1024} kB)")


if __name__ == "__main__":
    main()
