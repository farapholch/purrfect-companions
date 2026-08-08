#!/usr/bin/env python3
"""Grafik för Cat Haven-världen — allt renderat med regressionsmotorn.

Ingen Minecraft-klient finns på maskinen, så "screenshots" i spelmotorns
mening går inte att ta här. I stället komponeras riktiga modellrenderingar
(samma motor som trailern) mot en procedurell nattscen med fyren och
katthemmet:

  /tmp/cathaven-world-icon.png       800x450  — världslistans ikon (utan text;
                                                Minecraft visar namnet bredvid)
  publish/cathaven-hero.png          1280x720 — sajt + CurseForge-galleri
  publish/cathaven-teaser.gif        480x270  — loopande teaser (fyrsken + gång)

Ikonen bäddas in som world_icon.jpeg i .mcworld av build_world.py.
Endast publika namn — familjevarianten delar bildspråk utan text.
"""
import math, os, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_regression as rr
import make_video as mv

mv.FONT["V"] = "#...# #...# #...# #...# #...# .#.#. ..#..".split()

CATS = ["misty", "hazel", "mocha", "snow"]


def canvas(w, h):
    """Nattscen: gradienthimmel, stjärnor, måne, kullar, fyr, katthem."""
    mv.W, mv.H = w, h
    top, bot = (14, 16, 38), (30, 40, 70)
    img = [[(top[0] + (bot[0] - top[0]) * y // h,
             top[1] + (bot[1] - top[1]) * y // h,
             top[2] + (bot[2] - top[2]) * y // h, 255) for _ in range(w)]
           for y in range(h)]
    rnd = 40601
    for _ in range(w * h // 3200):                       # stjärnor (deterministiska)
        rnd = (rnd * 75 + 74) % 65537
        sx, sy = rnd % w, (rnd // w) % (h // 2)
        c = 150 + rnd % 90
        img[sy][sx] = (c, c, min(255, c + 25), 255)
    mx, my, mr = int(w * 0.86), int(h * 0.16), h // 14   # månen
    for y in range(my - mr, my + mr + 1):
        for x in range(mx - mr, mx + mr + 1):
            d = ((x - mx) ** 2 + (y - my) ** 2) ** 0.5
            if d <= mr: img[y][x] = (228, 230, 214, 255)
    hy = int(h * 0.72)                                    # kullarna
    for x in range(w):
        ridge = hy - int(h * 0.06 * math.sin(x / w * 3.1) + h * 0.03 * math.sin(x / w * 9.7))
        for y in range(max(0, ridge), h):
            t = (y - ridge) / max(1, h - ridge)
            img[y][x] = (int(18 + 10 * t), int(52 - 14 * t), int(30 + 4 * t), 255)
    return img


def lighthouse(img, w, h, beam_deg=None):
    """Fyren på högra kullen; beam_deg ritar ett svepande ljus."""
    lx, base_y = int(w * 0.74), int(h * 0.78)             # rotad i kullen
    th, tw = int(h * 0.36), max(6, w // 40)               # tornhöjd/-bredd
    for y in range(base_y - th, base_y):
        band = (base_y - y) * 4 // th % 2 == 0
        col = (216, 60, 60, 255) if band else (238, 240, 244, 255)
        for x in range(lx - tw // 2, lx + tw // 2 + 1):
            img[y][x] = col
    ly = base_y - th                                      # ljusrummet
    for y in range(ly - tw, ly):
        for x in range(lx - tw // 2 - 1, lx + tw // 2 + 2):
            img[y][x] = (28, 30, 40, 255)
    for y in range(ly - tw + 2, ly - 2):
        for x in range(lx - tw // 2 + 1, lx + tw // 2):
            img[y][x] = (255, 224, 120, 255)
    if beam_deg is not None:                              # ljuskäglan
        a = math.radians(beam_deg)
        cy = ly - tw // 2
        for r in range(tw, int(w * 0.45)):
            for spread in (-0.05, -0.025, 0.0, 0.025, 0.05):
                x = int(lx + r * math.cos(a + spread))
                y = int(cy + r * math.sin(a + spread) * 0.35)
                if 0 <= x < w and 0 <= y < h:
                    p = img[y][x]
                    f = max(0.0, 1.0 - r / (w * 0.45))
                    img[y][x] = (min(255, int(p[0] + 160 * f)),
                                 min(255, int(p[1] + 140 * f)),
                                 min(255, int(p[2] + 60 * f)), 255)


def shelter(img, w, h):
    """Katthemmet på vänstra kullen: varmt ljus i fönstren."""
    sx, sy = int(w * 0.16), int(h * 0.70)
    bw, bh = int(w * 0.11), int(h * 0.10)
    for y in range(sy - bh, sy):                          # stomme
        for x in range(sx, sx + bw):
            img[y][x] = (66, 46, 30, 255)
    for i in range(bh * 2 // 3):                          # sadeltak
        for x in range(sx - 2 + i, sx + bw + 2 - i):
            y = sy - bh - i
            if 0 <= y < h: img[y][x] = (40, 28, 20, 255)
    ww = max(3, bw // 6)
    for wx in (sx + bw // 5, sx + bw - bw // 5 - ww):     # fönster
        for y in range(sy - bh * 2 // 3, sy - bh // 4):
            for x in range(wx, wx + ww):
                img[y][x] = (255, 200, 96, 255)


def cat_sprite(cat, pose, yaw):
    """Rendera med genomskinlig bakgrund — motorns fond är opak, nyckla bort den."""
    src = rr.render(cat, [], pose, W=240, H=240, yaw=yaw, pitch=10)
    bg = src[0][0]
    def near(p): return abs(p[0]-bg[0]) + abs(p[1]-bg[1]) + abs(p[2]-bg[2]) < 18
    return [[(p[0], p[1], p[2], 0 if near(p) else 255) for p in row] for row in src]


def cats_row(img, w, h, t=0.35, sizes=None):
    """De fyra katterna i gångcykel längs kullarna."""
    sizes = sizes or [0.30, 0.24, 0.20, 0.26]
    spots = [(0.30, 0.86), (0.44, 0.80), (0.56, 0.84), (0.68, 0.78)]
    for i, cat in enumerate(CATS):
        pose = mv.walk_pose(t + i * 0.9)
        src = cat_sprite(cat, pose, yaw=38 + i * 7)
        mv.paste(img, src, 240, 240, int(w * spots[i][0]), int(h * spots[i][1]),
                 int(h * sizes[i]))


def save_png(path, img, w, h):
    # write_png skriver RGBA (färgtyp 6) — säkerställ 4 kanaler per pixel
    rr.write_png(path, w, h, [[(p[0], p[1], p[2], 255) for p in row] for row in img])


def build_icon():
    w, h = 800, 450
    img = canvas(w, h); lighthouse(img, w, h, beam_deg=192)
    shelter(img, w, h); cats_row(img, w, h)
    save_png("/tmp/cathaven-world-icon.png", img, w, h)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i",
                    "/tmp/cathaven-world-icon.png", "-q:v", "3",
                    "/tmp/cathaven-world-icon.jpeg"], check=True)
    print("ikon: /tmp/cathaven-world-icon.jpeg (800x450)")


def build_hero():
    w, h = 1280, 720
    img = canvas(w, h); lighthouse(img, w, h, beam_deg=192)
    shelter(img, w, h); cats_row(img, w, h)
    mv.W, mv.H = w, h
    mv.text(img, "CAT HAVEN", w // 2, int(h * 0.10), scale=9)
    mv.text(img, "A READY-MADE WORLD FOR PURRFECT COMPANIONS", w // 2, int(h * 0.24), scale=3,
            col=(170, 200, 240, 255))
    save_png(f"{BASE}/publish/cathaven-hero.png", img, w, h)
    print("hjältebild: publish/cathaven-hero.png (1280x720)")


def build_gif():
    w, h, frames = 480, 270, 36
    os.makedirs("/tmp/cathaven-gif", exist_ok=True)
    for f in range(frames):
        t = f / frames
        img = canvas(w, h)
        lighthouse(img, w, h, beam_deg=180 + 50 * math.sin(t * 2 * math.pi))
        shelter(img, w, h)
        cats_row(img, w, h, t=t * 2 * math.pi / 3)
        mv.W, mv.H = w, h
        mv.text(img, "CAT HAVEN", w // 2, int(h * 0.10), scale=3)
        save_png(f"/tmp/cathaven-gif/f{f:03d}.png", img, w, h)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12",
                    "-i", "/tmp/cathaven-gif/f%03d.png",
                    "-vf", "split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer",
                    "-loop", "0", f"{BASE}/publish/cathaven-teaser.gif"], check=True)
    print("teaser: publish/cathaven-teaser.gif")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("icon", "all"): build_icon()
    if what in ("hero", "all"): build_hero()
    if what in ("gif", "all"): build_gif()
