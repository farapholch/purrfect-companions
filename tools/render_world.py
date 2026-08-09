#!/usr/bin/env python3
"""Visuell verifiering av Cat Haven — renderar världen UTAN Minecraft-klient.

Dagens läxa: bygget verifierades logiskt (testforblock) men aldrig visuellt,
så fel som "ingången vetter åt fel håll" och "stegen når inte luckan" nådde
Xbox. Den här renderaren spelar upp EXAKT samma byggrecept som build_world
(strukturfiler + fill/setblock-kommandon) i en voxelmodell och ritar vyer:

    python3 tools/render_world.py            # -> /tmp/worldviews/*.png

  overview.png    isometrisk översikt från sydost
  front.png       katthemmet rakt söderifrån (dörr, trappa, skyltar)
  lighthouse.png  fyren rakt norrifrån — INGÅNGEN ska synas
  interior.png    katthemmet uppifrån utan tak — möblerna och kistan
  den.png         tvärsnitt x=0 genom jordkulan och fyrkullen
  cellar.png      tvärsnitt z=10 genom källaren under huset

Kommandotolken förstår bara det build_world faktiskt använder: fill,
setblock, structure load. Övriga kommandon ignoreras. Custom-blockens
färger samplas ur deras faktiska texturer.
"""
import json, os, re, shutil, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, f"{BASE}/tools/gametest")
import nbt
import render_regression as rr
import build_world as bw

OUT = "/tmp/worldviews"

# ------------------------------------------------------------ blockfärger ----
VANILLA = {
    "grass_block": (98, 155, 62), "dirt": (134, 96, 67), "bedrock": (60, 60, 60),
    "gravel": (150, 141, 137), "cobblestone": (122, 122, 122),
    "spruce_planks": (114, 84, 48), "oak_planks": (162, 130, 78),
    "oak_log": (109, 85, 50), "oak_leaves": (60, 120, 40),
    "glass_pane": (200, 225, 235), "lantern": (255, 200, 90),
    "glowstone": (255, 220, 120), "white_concrete": (207, 213, 214),
    "red_concrete": (142, 32, 32), "stone_bricks": (120, 120, 120),
    "water": (60, 90, 200), "ladder": (170, 135, 80),
    "oak_fence": (162, 130, 78), "wooden_door": (150, 110, 60),
    "oak_stairs": (162, 130, 78), "standing_sign": (180, 148, 92),
    "wall_sign": (180, 148, 92), "chest": (170, 120, 50),
    "hay_block": (220, 190, 60), "white_carpet": (235, 235, 235),
    "poppy": (220, 40, 40), "dandelion": (250, 220, 60),
    "dark_oak_log": (60, 46, 26), "dark_oak_leaves": (35, 60, 25),
    "web": (240, 240, 240), "soul_lantern": (80, 220, 255), "air": None,
}

def _custom_colors():
    """Dominant färg ur varje mjau-blocks textur."""
    tt = json.load(open(f"{BASE}/PurrfectCompanions_RP/textures/terrain_texture.json"))["texture_data"]
    out = {}
    for key, v in tt.items():
        try:
            w, h, px = rr.read_png(f"{BASE}/PurrfectCompanions_RP/{v['textures']}.png")
        except Exception:
            continue
        rs = gs = bs = n = 0
        for row in px:
            for p in row:
                if len(p) > 3 and p[3] < 128: continue
                rs += p[0]; gs += p[1]; bs += p[2]; n += 1
        if n: out[key.replace("pc_", "mjau:")] = (rs // n, gs // n, bs // n)
    return out

# Signalfärger för mjau-blocken — verifieringsvyer ska ha KONTRAST, inte
# realism (texturmedelvärdena smälte ihop med trägolvet).
MJAU = {
    "mjau:kattbadd": (255, 60, 180), "mjau:matskal": (0, 220, 220),
    "mjau:kartong": (255, 140, 0), "mjau:stallning": (255, 255, 0),
    "mjau:kattoa": (255, 255, 255), "mjau:garnnystan": (255, 0, 0),
    "mjau:kattlucka": (200, 0, 255), "mjau:fiskdamm": (0, 100, 255),
}

def color_of(name, custom):
    if name in MJAU: return MJAU[name]
    n = name.replace("minecraft:", "")
    if n in VANILLA: return VANILLA[n]
    if name in custom: return custom[name]
    return (250, 70, 220)   # skrikrosa = "okänt block" — ska synas direkt

# ------------------------------------------------------------- voxelbygge ----
def build_voxels():
    """Spela upp byggreceptet: FLAT-terräng + strukturer + kommandon."""
    t = bw.TEXTS["public"]
    for src in ("misty", "hazel", "mocha", "snow"):
        t = {**t, "book_pages": [p.replace(f"%{src.upper()}%", src.capitalize())
                                 for p in t["book_pages"]]}
    cats = {c: c for c in ("misty", "hazel", "mocha", "snow")}
    disp = {c: c.capitalize() for c in cats}
    stdir = "/tmp/worldview-structs"
    if os.path.exists(stdir): shutil.rmtree(stdir)
    bw.build_structures(stdir, t, disp, cats)

    vox = {}
    g = bw.GROUND
    for x in range(-45, 45):            # FLAT-terräng i spelområdet
        for z in range(-10, 95):
            vox[(x, g, z)] = "minecraft:grass_block"
            vox[(x, g - 1, z)] = "minecraft:dirt"

    def load_struct(name, ox, oy, oz):
        data = open(f"{stdir}/structures/haven/{name}.mcstructure", "rb").read()
        root, _ = nbt._read(data, 3, nbt.TAG_COMPOUND)
        st = root.v
        sx, sy, sz = [v.v for v in st["size"].v[1]]
        pal = [ (p.v["name"].v,) for p in st["structure"].v["palette"].v["default"].v["block_palette"].v[1] ]
        idx = [v.v for v in st["structure"].v["block_indices"].v[1][0].v[1]]
        i = 0
        for x in range(sx):
            for y in range(sy):
                for z in range(sz):
                    pi = idx[i]; i += 1
                    if pi < 0: continue
                    name = pal[pi][0]
                    if name == "minecraft:air":
                        vox.pop((ox + x, oy + y, oz + z), None)
                    else:
                        vox[(ox + x, oy + y, oz + z)] = name
    for cmd in bw.build_commands(cats, disp):
        if isinstance(cmd, tuple): continue
        m = re.match(r"structure load haven:(\S+) (-?\d+) (-?\d+) (-?\d+)", cmd)
        if m:
            load_struct(m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))); continue
        m = re.match(r"fill (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) (\S+)", cmd)
        if m:
            x1, y1, z1, x2, y2, z2 = map(int, m.groups()[:6]); name = m.group(7)
            repl = re.search(r"replace (\S+)", cmd)
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    for z in range(min(z1, z2), max(z1, z2) + 1):
                        if repl and vox.get((x, y, z), "minecraft:air").replace("minecraft:", "") != repl.group(1):
                            continue
                        if name == "air": vox.pop((x, y, z), None)
                        else: vox[(x, y, z)] = name
            continue
        m = re.match(r"setblock (-?\d+) (-?\d+) (-?\d+) (\S+)", cmd)
        if m:
            x, y, z, name = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
            if name == "air": vox.pop((x, y, z), None)
            else: vox[(x, y, z)] = name
    return vox

# ---------------------------------------------------------------- vyerna ----
def shade(c, f):
    return (min(255, int(c[0] * f)), min(255, int(c[1] * f)), min(255, int(c[2] * f)), 255)

def save(path, img, w, h):
    rr.write_png(path, w, h, img)

def render_topdown(vox, custom, path, ymax=None, area=((-45, 45), (-10, 95)), scale=6):
    (x0, x1), (z0, z1) = area
    w, h = (x1 - x0) * scale, (z1 - z0) * scale
    img = [[(20, 22, 30, 255)] * w for _ in range(h)]
    for x in range(x0, x1):
        for z in range(z0, z1):
            for y in range(-40 if ymax is None else ymax, -66, -1):
                name = vox.get((x, y, z))
                if not name: continue
                c = color_of(name, custom)
                if c is None: continue
                f = 1.0 + (y + 60) * 0.02
                px, pz = (x - x0) * scale, (z - z0) * scale
                for dx in range(scale):
                    for dz in range(scale):
                        img[pz + dz][px + dx] = shade(c, f)
                break
    save(path, img, w, h)

def render_elevation(vox, custom, path, axis, at_range, area, scale=6, flip=False):
    """Ortografisk fasad: närmsta block längs siktlinjen (axis='z' => tittar längs z)."""
    (u0, u1), (y0, y1) = area
    w, h = (u1 - u0) * scale, (y1 - y0) * scale
    img = [[(135, 176, 235, 255)] * w for _ in range(h)]
    rng = list(at_range)
    for u in range(u0, u1):
        for y in range(y0, y1):
            for d in rng:
                pos = (u, y, d) if axis == "z" else (d, y, u)
                name = vox.get(pos)
                if not name: continue
                c = color_of(name, custom)
                if c is None: continue
                depth = rng.index(d) / max(1, len(rng))
                f = max(0.15, 1.1 - depth * 1.6)   # öppningar ska vara UPPENBART mörka
                uu = (u - u0) if not flip else (u1 - 1 - u)
                py = (y1 - 1 - y) * scale
                for dx in range(scale):
                    for dy in range(scale):
                        img[py + dy][uu * scale + dx] = shade(c, f)
                break
    save(path, img, w, h)

def render_slice(vox, custom, path, axis, at, area, scale=8):
    (u0, u1), (y0, y1) = area
    w, h = (u1 - u0) * scale, (y1 - y0) * scale
    img = [[(25, 25, 34, 255)] * w for _ in range(h)]
    for u in range(u0, u1):
        for y in range(y0, y1):
            pos = (u, y, at) if axis == "x" else (at, y, u)   # axis = vilken led u löper i
            name = vox.get(pos)
            if not name: continue
            c = color_of(name, custom)
            if c is None: continue
            py = (y1 - 1 - y) * scale
            for dx in range(scale):
                for dy in range(scale):
                    img[py + dy][(u - u0) * scale + dx] = shade(c, 1.0)
    save(path, img, w, h)

def main():
    os.makedirs(OUT, exist_ok=True)
    custom = _custom_colors()
    vox = build_voxels()
    print(f"{len(vox)} voxlar")
    render_topdown(vox, custom, f"{OUT}/overview.png")
    # klipp vid MÖBELPLANET (-59): skyltarna på -58 skymmer annars bäddarna
    render_topdown(vox, custom, f"{OUT}/interior.png", ymax=-59,
                   area=((-10, 10), (5, 20)), scale=14)
    render_elevation(vox, custom, f"{OUT}/front.png", "z", range(0, 20),
                     area=((-12, 12), (-62, -50)), scale=10)
    render_elevation(vox, custom, f"{OUT}/lighthouse.png", "z", range(40, 66),
                     area=((-12, 12), (-62, -38)), scale=10)
    render_slice(vox, custom, f"{OUT}/den.png", "z", 0,
                 area=((44, 70), (-64, -50)), scale=10)
    render_slice(vox, custom, f"{OUT}/cellar.png", "x", 10,
                 area=((-8, 8), (-66, -54)), scale=10)
    print(f"vyer -> {OUT}/")

if __name__ == "__main__":
    main()
