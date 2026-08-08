#!/usr/bin/env python3
"""Promo-video för YouTube — renderad helt med vår egen z-buffrade motor.

Samma renderare som bildregressionen (render_regression.render) gör videorutor:
gångcykeln animeras med samma matematik som spelets animationer, kameran
sveper, plaggen visas ett i taget. Ingen Minecraft-klient, ingen PIL, inget
ljud (Pelle lägger musik från YouTubes ljudbibliotek — licensfritt där).

Rutor renderas i 480×270 och skalas till 1080p med NÄRMSTA GRANNE — pixellooken
är en del av Minecraft-estetiken, inte en kompromiss.

ENDAST publika namn (Misty/Hazel/Mocha/Snow) — videon är marknadsföring.

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
CATS = [("misty", "MISTY"), ("hazel", "HAZEL"), ("mocha", "MOCHA"), ("snow", "SNOW")]
OUTFITS = [("sadel1", "SADDLE"), ("keps1", "CAP"), ("halsduk1", "SCARF"),
           ("ryggsack1", "BACKPACK"), ("glasogon1", "GLASSES"), ("mantel1", "CAPE"),
           ("tossor1", "BOOTIES"), ("halsband1", "COLLAR"), ("rosett1", "BOW"),
           ("vingar1", "WINGS"), ("krona1", "CROWN"), ("vagn1", "CART")]
FULL = ["sadel1", "keps1", "halsduk1", "ryggsack1", "mantel1", "vagn1"]


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
        text(img, "FOUR HAND-MADE CATS FOR MINECRAFT BEDROCK", W // 2, 236, 1)
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


if __name__ == "__main__":
    main()
