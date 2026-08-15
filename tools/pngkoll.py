#!/usr/bin/env python3
"""Läser VARJE PNG i resurspaketen och kräver att den går att avkoda.

Bakgrunden: alla föremålsikoner ritades som rutmönster på Xbox i v3.19-3.23.
Filerna fanns, item_texture.json pekade rätt, och granskningen sa grönt — men
själva PNG-erna var trasiga. write_png deklarerar RGBA och skriver bytes(px),
så en RGB-trippel gav tre byte i en rad som ska ha fyra. Bilden blev förskjuten
och klienten vägrade rita den.

Läxan: att en fil finns säger ingenting om att den går att läsa.

    python3 tools/pngkoll.py <mapp eller .mcaddon/.mcworld> [...]
"""
import struct, sys, zlib


def kolla(namn, data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return f"{namn}: inte en PNG"
    i, w, h, ct, idat = 8, 0, 0, None, b""
    while i < len(data):
        ln = struct.unpack(">I", data[i:i+4])[0]
        typ, kropp = data[i+4:i+8], data[i+8:i+8+ln]
        vantad = zlib.crc32(typ + kropp) & 0xffffffff
        if struct.unpack(">I", data[i+8+ln:i+12+ln])[0] != vantad:
            return f"{namn}: trasig kontrollsumma i {typ.decode('ascii','replace')}"
        if typ == b"IHDR":
            w, h, _, ct = struct.unpack(">IIBB", kropp[:10])
        elif typ == b"IDAT":
            idat += kropp
        i += 12 + ln
    if not w or not h:
        return f"{namn}: saknar IHDR"
    kanaler = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ct)
    if kanaler is None:
        return f"{namn}: okänd färgtyp {ct}"
    try:
        raw = zlib.decompress(idat)
    except Exception as e:
        return f"{namn}: IDAT går inte att packa upp ({e})"
    vantat = h * (w * kanaler + 1)          # en filterbyte per rad
    if len(raw) != vantat:
        return (f"{namn}: {len(raw)} byte bilddata, väntade {vantat} "
                f"({w}x{h}, {kanaler} kanaler) — raderna går inte ihop")
    return None


def main(mal):
    fel, antal = [], 0
    for m in mal:
        if m.endswith((".mcaddon", ".mcworld", ".mctemplate", ".zip")):
            import zipfile
            z = zipfile.ZipFile(m)
            for n in z.namelist():
                if n.endswith(".png"):
                    antal += 1
                    f = kolla(f"{m}:{n}", z.read(n))
                    if f: fel.append(f)
        else:
            import os
            for rot, _, filer in os.walk(m):
                for n in filer:
                    if n.endswith(".png"):
                        antal += 1
                        p = os.path.join(rot, n)
                        f = kolla(p, open(p, "rb").read())
                        if f: fel.append(f)
    print(f"PNG-koll: {antal} filer")
    for f in fel:
        print("  ❌", f)
    if fel:
        print(f"  {len(fel)} trasiga")
        return 1
    print("  ✅ alla går att avkoda")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["PurrfectCompanions_RP", "PurrfectHarbour_RP"]))
