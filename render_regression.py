#!/usr/bin/env python3
"""Bildregression för modellen.

Servern renderar ingenting, och den befintliga förhandsvisningen plattar ut alla
kuber till en enda hög — den kastar bort ben och pivotar och ritar bara
viloposen. Därför kunde kronans felaktiga pivot passera: en pivot spelar roll
FÖRST när något roterar.

Den här filen renderar katten i en POSE — huvudet vridet, benen i gång, svansen
utsvängd — genom att rotera varje kub kring sitt eget bens pivot, precis som
spelet gör. Sedan jämförs resultatet pixel för pixel mot godkända bilder.

Poängen är att den fångar visuella fel vi inte förutsett. Den vet inget om
pivotar eller svansar; den vet bara hur katten SKA se ut.

    python3 render_regression.py            # jämför mot tests/baseline
    python3 render_regression.py --update   # skriv om facit (granska diffen!)
"""
import json, math, os, sys, zlib, struct, glob

BASE = os.path.dirname(os.path.abspath(__file__))
RP = f"{BASE}/PurrfectCompanions_RP"
GOLD = f"{BASE}/tests/baseline"
SIZE = 80

GEO = {g["description"]["identifier"]: g
       for g in json.load(open(f"{RP}/models/entity/katt.geo.json"))["minecraft:geometry"]}

# En enda pose som sätter varje rörligt ben i arbete. Står något stilla här kan
# dess pivot vara hur fel som helst utan att synas.
POSE = {"head": (-22, 28, 0), "body": (0, 0, 6),
        "leg0": (32, 0, 0), "leg1": (-32, 0, 0), "leg2": (-28, 0, 0), "leg3": (28, 0, 0),
        "tail": (12, 0, 20)}


def read_png(path):
    d = open(path, "rb").read()
    w, h = struct.unpack(">II", d[16:24])
    i, raw = 8, b""
    while i < len(d):
        ln = struct.unpack(">I", d[i:i + 4])[0]
        if d[i + 4:i + 8] == b"IDAT":
            raw += d[i + 8:i + 8 + ln]
        i += 12 + ln
    data = zlib.decompress(raw)
    px, prev, pos, stride = [], bytearray(w * 4), 0, w * 4
    for _ in range(h):
        ft = data[pos]; pos += 1
        line = bytearray(data[pos:pos + stride]); pos += stride
        for x in range(stride):
            a = line[x - 4] if x >= 4 else 0
            b = prev[x]
            c = prev[x - 4] if x >= 4 else 0
            if ft == 1: line[x] = (line[x] + a) & 255
            elif ft == 2: line[x] = (line[x] + b) & 255
            elif ft == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif ft == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        px.append([tuple(line[x:x + 4]) for x in range(0, stride, 4)])
        prev = line
    return w, h, px


def write_png(p, w, h, px):
    raw = b"".join(b"\x00" + bytes(v for pix in row for v in pix) for row in px)

    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    open(p, "wb").write(b"\x89PNG\r\n\x1a\n"
                        + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                        + ch(b"IDAT", zlib.compress(raw, 9)) + ch(b"IEND", b""))


def rot(p, pivot, deg):
    """Rotera kring benets egen pivot — det är HELA poängen med testet."""
    x, y, z = p[0] - pivot[0], p[1] - pivot[1], p[2] - pivot[2]
    for axis, a in zip("xyz", (math.radians(d) for d in deg)):
        c, s = math.cos(a), math.sin(a)
        if axis == "x": y, z = y * c - z * s, y * s + z * c
        elif axis == "y": x, z = x * c + z * s, -x * s + z * c
        else: x, y = x * c - y * s, x * s + y * c
    return (x + pivot[0], y + pivot[1], z + pivot[2])


def bones_for(accessories):
    out = [(b.get("name"), b.get("pivot", [0, 0, 0]), b.get("cubes", []))
           for b in GEO["geometry.katt"]["bones"]]
    for a in accessories:
        g = GEO.get(f"geometry.katt.{a}")
        if g:
            out += [(b.get("name"), b.get("pivot", [0, 0, 0]), b.get("cubes", []))
                    for b in g["bones"]]
    return out


def faces(U, V, w, h, d):
    return dict(top=(U + d, V, w, d), bottom=(U + d + w, V, w, d), west=(U, V + d, d, h),
                north=(U + d, V + d, w, h), east=(U + d + w, V + d, d, h),
                south=(U + 2 * d + w, V + d, w, h))


SH = {"top": 1.00, "bottom": 0.45, "north": 0.92, "south": 0.55, "east": 0.72, "west": 0.66}


def render(cat, acc, pose, W=SIZE, H=SIZE, yaw=34, pitch=16, ram=None):
    tw, th, tex = read_png(f"{RP}/textures/entity/{cat}.png")
    bones = bones_for(acc)
    ya, pa = math.radians(yaw), math.radians(pitch)

    def cam(p):
        x, y, z = p
        xr = x * math.cos(ya) + z * math.sin(ya)
        zr = -x * math.sin(ya) + z * math.cos(ya)
        return (xr, y * math.cos(pa) - zr * math.sin(pa), zr * math.cos(pa) + y * math.sin(pa))

    def place(p, pivot, deg):
        return cam(rot(p, pivot, deg) if any(deg) else p)

    # FAST ram. Anpassas den till modellens omslutande låda förskjuts hela bilden
    # så fort någon del rör sig, och då blir varje diff 25 % av alla pixlar utan
    # att peka ut vad som ändrats. Med fast kamera rör bara det trasiga sig.
    # Ramen går att vidga för det som INTE är en katt: spelardräkten är 37
    # enheter hög och ryms inte i kattens ram. Bildregressionen skickar aldrig
    # in något och behåller därmed exakt samma fasta ram som förut — det är
    # hela poängen med den, att en flyttad detalj inte förskjuter hela bilden.
    rx, ry, rz = ram or ((-9, 9), (0, 17), (-9, 11))
    corners = [cam((x, y, z)) for x in rx for y in ry for z in rz]
    minx, maxx = min(c[0] for c in corners), max(c[0] for c in corners)
    miny, maxy = min(c[1] for c in corners), max(c[1] for c in corners)
    pad = int(min(W, H) * 0.04)
    sc = min((W - 2 * pad) / (maxx - minx), (H - 2 * pad) / (maxy - miny))
    offx = pad - minx * sc + (W - 2 * pad - (maxx - minx) * sc) / 2
    offy = pad - miny * sc + (H - 2 * pad - (maxy - miny) * sc) / 2
    cv = [[(20, 22, 28, 255)] * W for _ in range(H)]
    zb = [[9e9] * W for _ in range(H)]
    for name, pivot, cubes in bones:
        deg = pose.get(name, (0, 0, 0))
        for c in cubes:
            ox, oy, oz = c["origin"]; w, h, d = c["size"]; U, V = c["uv"]
            F = faces(U, V, w, h, d)
            fns = {"top": lambda a, b: (ox + a * w, oy + h, oz + b * d),
                   "bottom": lambda a, b: (ox + a * w, oy, oz + b * d),
                   "north": lambda a, b: (ox + a * w, oy + (1 - b) * h, oz),
                   "south": lambda a, b: (ox + a * w, oy + (1 - b) * h, oz + d),
                   "east": lambda a, b: (ox + w, oy + (1 - b) * h, oz + a * d),
                   "west": lambda a, b: (ox, oy + (1 - b) * h, oz + a * d)}
            for fname, fn in fns.items():
                u0, v0, fw, fh = F[fname]; shd = SH[fname]
                steps = max(int(max(fw, fh) * sc * 1.6), 10)
                for i in range(steps + 1):
                    for j in range(steps + 1):
                        a, b = i / steps, j / steps
                        X, Y, Z = place(fn(a, b), pivot, deg)
                        px = int(X * sc + offx); py = int(H - (Y * sc + offy))
                        if not (0 <= px < W and 0 <= py < H): continue
                        if Z >= zb[py][px]: continue
                        col = tex[min(th - 1, max(0, int(v0 + b * fh)))][min(tw - 1, max(0, int(u0 + a * fw)))]
                        if col[3] < 8: continue
                        cv[py][px] = (int(col[0] * shd), int(col[1] * shd), int(col[2] * shd), 255)
                        zb[py][px] = Z
    return cv


def scenes():
    """Varje katt i vila, och varje plagg i pose — plus allt på en gång."""
    out = [(f"cat-{c}", c, [], {}) for c in ("misty", "hazel", "mocha", "snow", "midnight", "spokkatt")]
    accs = sorted({g.split("geometry.katt.")[1] for g in GEO
                   if g.startswith("geometry.katt.") and g != "geometry.katt.empty"})
    seen = set()
    for a in accs:
        stem = a.rstrip("0123456789")
        if stem in seen: continue
        seen.add(stem)
        out.append((f"posed-{stem}", "misty", [a], POSE))
    out.append(("posed-all", "misty", [a for a in accs if a.endswith("1")], POSE))
    return out


def main():
    update = "--update" in sys.argv
    os.makedirs(GOLD, exist_ok=True)
    diffs = []
    for name, cat, acc, pose in scenes():
        img = render(cat, acc, pose)
        path = f"{GOLD}/{name}.png"
        if update or not os.path.exists(path):
            write_png(path, SIZE, SIZE, img)
            continue
        _, _, gold = read_png(path)
        n = sum(1 for y in range(SIZE) for x in range(SIZE) if gold[y][x] != img[y][x])
        if n:
            write_png(f"/tmp/render-diff-{name}.png", SIZE, SIZE, img)
            diffs.append(f"{name}: {n} pixlar skiljer mot facit "
                         f"(ny bild: /tmp/render-diff-{name}.png)")
    if update:
        print(f"facit uppdaterat: {len(scenes())} bilder i tests/baseline")
    else:
        print("\n".join(diffs))


if __name__ == "__main__":
    main()
