#!/usr/bin/env python3
"""Logga + YouTube-miniatyr för promo-filmen.

Alla fyra katternas huvuden renderas rakt framifrån med regressionsmotorn
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

CATS = ["misty", "hazel", "mocha", "snow"]


def head_render(cat, size=240):
    """Bara huvudben(et), rakt framifrån, autobeskuret till innehållet."""
    orig = rr.bones_for
    rr.bones_for = lambda acc: [b for b in orig(acc) if b[0] == "head"]
    try:
        img = rr.render(cat, [], {}, W=size, H=size, yaw=24, pitch=8)
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
POS = [(150, 130), (362, 130), (150, 320), (362, 320)]
for (c, (img, bg)), (cx, cy) in zip(heads.items(), POS):
    blit_scaled(logo, img, bg, cx, cy, 165)
text(logo, "PURRFECT", S // 2, 428, 6, (0, 212, 255, 255))
text(logo, "COMPANIONS", S // 2, 476, 4)
rr.write_png(f"{BASE}/publish/video-logo.png", S, S, logo)

# --- miniatyren: huvuden till vänster, budskap till höger -------------------
TW, TH = 1280, 720
th = canvas(TW, TH)
TPOS = [(210, 200), (470, 200), (210, 470), (470, 470)]
for (c, (img, bg)), (cx, cy) in zip(heads.items(), TPOS):
    blit_scaled(th, img, bg, cx, cy, 220)
text(th, "PURRFECT", 950, 190, 10, (0, 212, 255, 255))
text(th, "COMPANIONS", 950, 290, 7)
text(th, "4 CATS . 12 OUTFITS", 950, 400, 4)
text(th, "TAME . RIDE . BREED", 950, 450, 4)
text(th, "MINECRAFT BEDROCK", 950, 540, 3, (150, 200, 255, 255))
rr.write_png(f"{BASE}/publish/youtube-thumbnail.png", TW, TH, th)
print("video-logo.png + youtube-thumbnail.png klara")
