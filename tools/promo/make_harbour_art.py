#!/usr/bin/env python3
"""Världslistans ikon för STJÄRNHAMNEN.

Stjärnhamnen ärvde Cat Havens ikon, så båda världarna såg likadana ut i
listan. Den här ritar en egen rymdscen — stjärnfält, planet, stationens
kupol och ett jaktplan i siluett — med samma handritade stil och samma
kattsprite-renderare som make_cathaven_art.py.

Rent stdlib plus ffmpeg för JPEG-konverteringen, precis som systerskriptet.
Ikonen bäddas in som world_icon.jpeg av build_spaceworld.py.

    python3 tools/promo/make_harbour_art.py
"""
import math, os, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)
sys.path.insert(0, f"{BASE}/tools/promo")
import render_regression as rr
import make_cathaven_art as art          # cat_sprite + mv-hjälparna
mv = art.mv

OUT_PNG = "/tmp/starharbour-world-icon.png"
OUT_JPEG = "/tmp/starharbour-world-icon.jpeg"


def rymden(w, h):
    """Djup rymd: nästan svart gradient, tätt stjärnfält, en planet i kanten."""
    mv.W, mv.H = w, h
    top, bot = (6, 6, 18), (18, 14, 40)
    img = [[(top[0] + (bot[0] - top[0]) * y // h,
             top[1] + (bot[1] - top[1]) * y // h,
             top[2] + (bot[2] - top[2]) * y // h, 255) for _ in range(w)]
           for y in range(h)]

    # stjärnfält — deterministiskt (samma frö som systerskriptet använder),
    # tätare och över hela ytan eftersom det INTE finns någon horisont här
    rnd = 40601
    for _ in range(w * h // 900):
        # TVÅ dragningar per stjärna: (rnd // w) % h ger bara 0..81 för w=800
        # (rnd är max 65537), så stjärnorna hamnade i övre sjättedelen. Cat
        # Haven-ikonen slapp undan för att den ändå bara ville ha himmel.
        rnd = (rnd * 75 + 74) % 65537
        sx = rnd % w
        rnd = (rnd * 75 + 74) % 65537
        sy = rnd % h
        c = 140 + rnd % 110
        img[sy][sx] = (c, c, min(255, c + 30), 255)
        if rnd % 11 == 0 and 0 < sx < w - 1 and 0 < sy < h - 1:   # några ljusare
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                img[sy + dy][sx + dx] = (c - 60, c - 60, c - 30, 255)

    # PLANETEN nere till vänster: halvt utanför bild, med ljusterminator
    pr = int(h * 0.55)
    pcx, pcy = int(w * 0.13), int(h * 1.05)
    for y in range(max(0, pcy - pr), h):
        for x in range(max(0, pcx - pr), min(w, pcx + pr + 1)):
            d = ((x - pcx) ** 2 + (y - pcy) ** 2) ** 0.5
            if d > pr:
                continue
            # ljuset kommer uppifrån höger
            lit = ((x - pcx) * 0.6 - (y - pcy) * 0.8) / max(1, pr)
            t = max(0.0, min(1.0, 0.5 + lit * 0.7))
            img[y][x] = (int(28 + 90 * t), int(40 + 70 * t), int(70 + 90 * t), 255)
    return img


def stationen(img, w, h):
    """Kupolen med lysande fönsterband, på en pelare — sedd på håll."""
    cx, cy = int(w * 0.60), int(h * 0.46)
    r = int(h * 0.20)
    # kupolens glaskalott
    for y in range(cy - r, cy + 1):
        for x in range(cx - r, cx + r + 1):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= r and 0 <= y < h and 0 <= x < w:
                t = 1 - d / r
                img[y][x] = (int(70 + 90 * t), int(120 + 100 * t), int(150 + 90 * t), 255)
    # golvplattan under kupolen
    for y in range(cy, cy + int(h * 0.035)):
        for x in range(cx - r, cx + r + 1):
            if 0 <= y < h and 0 <= x < w:
                img[y][x] = (198, 200, 208, 255)
    # pelaren ner
    for y in range(cy + int(h * 0.035), int(h * 0.86)):
        for x in range(cx - int(r * 0.22), cx + int(r * 0.22)):
            if 0 <= y < h and 0 <= x < w:
                img[y][x] = (150, 154, 165, 255)
    # lysande fönsterband i pelaren
    for i in range(3):
        yy = cy + int(h * 0.09) + i * int(h * 0.10)
        for x in range(cx - int(r * 0.18), cx + int(r * 0.18)):
            if 0 <= yy < h and 0 <= x < w:
                img[yy][x] = (255, 226, 140, 255)


def jaktplan(img, w, h, cx_f, cy_f, storlek):
    """Spjutjaktaren i siluett: klotkabin mellan två höga vingpaneler."""
    cx, cy = int(w * cx_f), int(h * cy_f)
    s = int(h * storlek)
    panel_w, panel_h = max(1, s // 6), s
    for sida in (-1, 1):
        px = cx + sida * int(s * 0.42)
        for y in range(cy - panel_h // 2, cy + panel_h // 2):
            for x in range(px - panel_w // 2, px + panel_w // 2 + 1):
                if not (0 <= y < h and 0 <= x < w):
                    continue
                # fasa av hörnen så rektangeln läser som en sexkant
                dy = abs(y - cy) / max(1, panel_h / 2)
                if dy > 0.82 and abs(x - px) > panel_w * 0.25:
                    continue
                img[y][x] = (26, 26, 36, 255)
    kr = max(2, s // 7)                                   # kabinen
    for y in range(cy - kr, cy + kr + 1):
        for x in range(cx - kr, cx + kr + 1):
            if ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 <= kr and 0 <= y < h and 0 <= x < w:
                img[y][x] = (40, 40, 52, 255)
    for x in range(cx - kr // 2, cx + kr // 2 + 1):       # fönsterband
        if 0 <= cy < h and 0 <= x < w:
            img[cy][x] = (120, 190, 230, 255)
    for sida in (-1, 1):                                  # bommarna
        for x in range(cx, cx + sida * int(s * 0.42), sida):
            if 0 <= cy < h and 0 <= x < w:
                img[cy][x] = (30, 30, 40, 255)


def build_icon():
    w, h = 800, 450
    img = rymden(w, h)
    stationen(img, w, h)
    jaktplan(img, w, h, 0.30, 0.30, 0.20)
    jaktplan(img, w, h, 0.84, 0.62, 0.14)
    # en katt på kupolens golvplatta — det är trots allt en kattstation
    src = art.cat_sprite("misty", mv.walk_pose(0.35), yaw=42)
    mv.paste(img, src, 240, 240, int(w * 0.615), int(h * 0.495), int(h * 0.17))
    art.save_png(OUT_PNG, img, w, h)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT_PNG,
                    "-q:v", "3", OUT_JPEG], check=True)
    print(f"ikon: {OUT_JPEG} (800x450)")


if __name__ == "__main__":
    build_icon()
