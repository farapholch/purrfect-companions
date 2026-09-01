#!/usr/bin/env python3
"""Ritar en UTLAGD MALL över kattens texturyta — för konstnärer utifrån.

Bakgrund: en spelare som är konstnär skrev att hen gärna skulle hjälpa till med
texturerna, men trodde att det krävde att man kan Minecraft-texturer. Det gör
det inte i det här projektet. Konsten är vanliga 256x256-PNG:er i
art/kattpalsar/, och generatorn bygger paketet ur dem. Det enda som saknades var
en bild som visar VAD som är vad — utan den är texturytan en obegriplig samling
rutor, och det är rimligt att tacka nej till att måla på den.

    python3 tools/make_art_template.py

Skriver publish/art-template.png: varje kubs utfällning inramad och namngiven,
med den befintliga pälsen svagt under så man ser vilken ruta som är vilken.

MÅLGRUPPEN KAN INTE PAKETET. Därför står måtten i klartext och rutorna är
namngivna på engelska — det här är den enda filen i projektet som talar till
någon utanför det.
"""
import json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, f"{BASE}/tools/promo")
import render_regression as rr
import make_video as mv

RP = f"{BASE}/PurrfectCompanions_RP"
SKALA = 4                      # 256 -> 1024, så texten får plats
BAKGRUND = (26, 28, 36, 255)
RAM = (120, 200, 255, 255)
TEXT = (226, 238, 250, 255)

# Bennamnen är engelska i geometrin men säger inget till en utomstående: "body"
# är hela bålen, "leg0" är vänster framben. Namnen här är för människan som
# ska måla, inte för motorn.
NAMN = {"body": "BODY", "head": "HEAD", "leg0": "FRONT LEFT LEG",
        "leg1": "FRONT RIGHT LEG", "leg2": "BACK LEFT LEG",
        "leg3": "BACK RIGHT LEG", "tail": "TAIL"}


def rutor():
    """Varje kub i grundkatten som (namn, uv-fotavtryck). Läses ur geometrin, så
    mallen kan aldrig visa en annan modell än den som faktiskt byggs."""
    geo = [g for g in json.load(open(f"{RP}/models/entity/katt.geo.json"))["minecraft:geometry"]
           if g["description"]["identifier"] == "geometry.katt"][0]
    ut = []
    for b in geo["bones"]:
        for c in b.get("cubes", []):
            F = rr.faces(c["uv"][0], c["uv"][1], *c["size"])
            x0 = min(v[0] for v in F.values())
            y0 = min(v[1] for v in F.values())
            x1 = max(v[0] + v[2] for v in F.values())
            y1 = max(v[1] + v[3] for v in F.values())
            ut.append((NAMN.get(b["name"], b["name"].upper()), c["size"], x0, y0, x1, y1))
    return ut


def main():
    tw, th, tex = rr.read_png(f"{RP}/textures/entity/misty.png")
    W, H = tw * SKALA, th * SKALA
    mv.W, mv.H = W, H
    duk = [[BAKGRUND] * W for _ in range(H)]

    # PÄLSEN SVAGT UNDER. En tom mall säger var rutorna är men inte vad de
    # föreställer; med den befintliga katten nertonad ser man direkt att den
    # här rutan är ett öra och den där en tass.
    for y in range(th):
        for x in range(tw):
            p = tex[y][x]
            if p[3] == 0:
                continue
            f = 0.42
            c = tuple(int(p[i] * f + BAKGRUND[i] * (1 - f)) for i in range(3)) + (255,)
            for dy in range(SKALA):
                for dx in range(SKALA):
                    duk[y * SKALA + dy][x * SKALA + dx] = c

    # ETT RUTNÄT PER TEXEL, svagt. En konstnär behöver se pixelgränserna: det
    # här är en textur där en pixel är en pixel, inte en duk att måla mjukt på.
    for i in range(0, tw + 1):
        for y in range(H):
            if i * SKALA < W:
                duk[y][i * SKALA] = (44, 48, 58, 255)
    for j in range(0, th + 1):
        for x in range(W):
            if j * SKALA < H:
                duk[j * SKALA][x] = (44, 48, 58, 255)

    for namn, matt, x0, y0, x1, y1 in rutor():
        a, b = int(x0 * SKALA), int(y0 * SKALA)
        c, d = int(x1 * SKALA), int(y1 * SKALA)
        for x in range(a, min(c, W)):
            for yy in (b, min(d - 1, H - 1)):
                if 0 <= yy < H: duk[yy][x] = RAM
        for y in range(b, min(d, H)):
            for xx in (a, min(c - 1, W - 1)):
                if 0 <= xx < W: duk[y][xx] = RAM
        # Etiketten hamnar under rutan om den inte får plats ovanför.
        ty = b - 9 if b > 12 else min(d + 2, H - 8)
        mv.text(duk, namn, (a + c) // 2, ty, 1, TEXT)

    os.makedirs(f"{BASE}/publish", exist_ok=True)
    ut = f"{BASE}/publish/art-template.png"
    rr.write_png(ut, W, H, duk)
    print(f"  {os.path.relpath(ut, BASE)} ({W}x{H}) — {len(rutor())} rutor, "
          f"texturen är {tw}x{th}")


if __name__ == "__main__":
    main()
