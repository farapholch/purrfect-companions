#!/usr/bin/env python3
"""Genererar Purrfect Companions block: kattbädd och garnnystan.

Som build_accessories.py: en definition nedan → geometri, textur, block-JSON,
blocks.json, terrain_texture.json, recept och språksträng.

Katterna söker sig till blocken via minecraft:behavior.move_to_block (sätts på
entiteterna av det här skriptet, med entydig prioritet).
"""
import json, os, zlib, struct, glob

BASE = "/opt/purrfect-companions"; BP = f"{BASE}/PurrfectCompanions_BP"; RP = f"{BASE}/PurrfectCompanions_RP"

BLOCKS = {
 "kattbadd": dict(
   name="Cat Bed",
   # låg kudde: 16x4x16 med en liten kant runt om
   cubes=[([-8,0,-8],[16,3,16]), ([-8,3,-8],[16,2,2]), ([-8,3,6],[16,2,2]),
          ([-8,3,-6],[2,2,12]), ([6,3,-6],[2,2,12])],
   base=(150,86,110), accent=(196,132,152), sound="cloth",
   recipe=dict(pattern=["WWW","LLL"],
     key={"W":{"item":"minecraft:white_wool"},"L":{"item":"minecraft:leather"}},
     unlock=[{"item":"minecraft:white_wool"}]),
   height=5),
 "matskal": dict(
   name="Food Bowl",
   # låg skål med kant och "mat" i mitten
   cubes=[([-5,0,-5],[10,1,10]), ([-5,1,-5],[10,2,1]), ([-5,1,4],[10,2,1]),
          ([-5,1,-4],[1,2,8]), ([4,1,-4],[1,2,8]), ([-3,1,-3],[6,1,6])],
   base=(188,148,96), accent=(120,78,52), sound="wood",
   recipe=dict(pattern=[" F ","PBP"],
     key={"B":{"item":"minecraft:bowl"},"P":{"item":"minecraft:planks"},
          "F":{"item":"minecraft:cod"}},
     unlock=[{"item":"minecraft:bowl"}]),
   height=3),
 "kattoa": dict(
   name="Litter Box",
   # låg back med kant och strö i mitten
   cubes=[([-7,0,-7],[14,1,14]), ([-7,1,-7],[14,3,1]), ([-7,1,6],[14,3,1]),
          ([-7,1,-6],[1,3,12]), ([6,1,-6],[1,3,12]), ([-6,1,-6],[12,1,12])],
   base=(158,160,168), accent=(214,198,150), sound="gravel",
   recipe=dict(pattern=["P P","PSP"],
     key={"P":{"item":"minecraft:planks"},"S":{"item":"minecraft:sand"}},
     unlock=[{"item":"minecraft:sand"}]),
   height=4),
 "stallning": dict(
   name="Cat Tower",
   # OMRITAT 2026-08-29. Den gamla var en 3x10-pinne mellan två breda plattor och
   # läste som en I-BALK, inte som ett klösträd: stolpen för smal, kant bara på
   # två av fyra sidor, och alla kuber delade samma texturhörn så repet och
   # mattan såg likadana ut.
   #
   # Nu: tjockare sisalstolpe, en MELLANHYLLA som sticker ut (det är den som gör
   # det till ett träd och inte en pall), kant runt hela toppen, och en boll i
   # ett snöre — det mest igenkännbara ett klösträd har.
   cubes=[([-7,0,-7],[14,1,14],"tra"),           # bottenplatta
          ([-2.5,1,-2.5],[5,10,5],"rep"),        # sisalstolpe
          ([-8,6,-3],[6,1,6],"matta"),           # mellanhylla
          ([-6,11,-6],[12,1,12],"matta"),        # topplattform
          ([-6,12,-6],[12,1,1],"kant"),          # kant: fram
          ([-6,12,5],[12,1,1],"kant"),           # kant: bak
          ([-6,12,-5],[1,1,10],"kant"),          # kant: vänster
          ([5,12,-5],[1,1,10],"kant"),           # kant: höger
          ([-5.5,4,-0.5],[1,2,1],"rep"),         # snöre
          ([-6,2,-1],[2,2,2],"boll")],           # leksaksboll
   material={
     # SISAL: täta vågräta varv. Ett rep känns igen på varvet, inte på färgen.
     "rep":   lambda x,y: (188,156,104,255) if y % 2 else (150,118,74,255),
     # MATTA: tät luddig väv i varm sand, inte grå. Första omgången låg på
     # (214,206,192) och läste som betong bredvid det mörka träet.
     "matta": lambda x,y: (226,206,170,255) if (x + y) % 3 else (204,182,146,255),
     # KANT: samma väv en tydlig aning mörkare. Kanten hade samma material som
     # plattformen och FÖRSVANN — en upphöjd list man inte ser är ingen list.
     "kant":  lambda x,y: (186,162,124,255) if (x + y) % 3 else (164,140,104,255),
     # TRÄ: plankor med mörka fogar
     "tra":   lambda x,y: (108,78,50,255) if y % 5 == 0 else (146,110,72,255),
     "boll":  lambda x,y: (214,96,88,255) if (x + y) % 4 else (240,150,140,255),
   },
   base=(196,176,140), accent=(150,118,84), sound="wood",
   recipe=dict(pattern=["WWW"," S ","PPP"],
     key={"W":{"item":"minecraft:white_wool"},"S":{"item":"minecraft:string"},
          "P":{"item":"minecraft:planks"}},
     unlock=[{"item":"minecraft:white_wool"}]),
   height=13),
 "kartong": dict(
   name="Cardboard Box",
   # öppen låda — katter älskar lådor
   cubes=[([-7,0,-7],[14,1,14]), ([-7,1,-7],[14,7,1]), ([-7,1,6],[14,7,1]),
          ([-7,1,-6],[1,7,12]), ([6,1,-6],[1,7,12]),
          ([-8,7,-8],[3,1,16]), ([5,7,-8],[3,1,16])],   # uppvikta flikar
   base=(184,146,98), accent=(150,112,70), sound="wood",
   recipe=dict(pattern=["P P","PPP"],
     key={"P":{"item":"minecraft:paper"}},
     unlock=[{"item":"minecraft:paper"}]),
   height=8),
 "fiskdamm": dict(
   name="Fish Pond",
   cubes=[([-8,0,-8],[16,2,16]), ([-8,2,-8],[16,2,2]), ([-8,2,6],[16,2,2]),
          ([-8,2,-6],[2,2,12]), ([6,2,-6],[2,2,12]), ([-6,2,-6],[12,1,12])],
   base=(96,104,116), accent=(66,132,196), sound="stone",
   recipe=dict(pattern=["SFS","SWS"],
     key={"S":{"item":"minecraft:stone"},"W":{"item":"minecraft:water_bucket"},
          "F":{"item":"minecraft:cod"}},
     unlock=[{"item":"minecraft:stone"}]),
   height=4),
 "kattlucka": dict(
   name="Cat Door",
   genomgang=True,          # en lucka man kan gå igenom, inte en vägg
   # ram med lucka — dekorativ, ställs i en dörröppning
   cubes=[([-6,0,-1],[2,14,2]), ([4,0,-1],[2,14,2]), ([-6,14,-1],[12,2,2]),
          ([-4,2,-0.5],[8,10,1])],
   base=(142,104,66), accent=(190,160,120), sound="wood",
   recipe=dict(pattern=["PPP","P P","PWP"],
     key={"P":{"item":"minecraft:planks"},"W":{"item":"minecraft:white_wool"}},
     unlock=[{"item":"minecraft:planks"}]),
   height=16),
 "garnnystan": dict(
   name="Yarn Ball",
   cubes=[([-5,0,-5],[10,10,10]), ([-6,2,-3],[12,6,6]), ([-3,2,-6],[6,6,12])],
   base=(206,86,74), accent=(236,140,124), sound="cloth",
   recipe=dict(pattern=["SSS","SWS","SSS"],   # 4 snören i kvadrat = vanilla ull-receptet
     key={"S":{"item":"minecraft:string"},"W":{"item":"minecraft:white_wool"}},
     unlock=[{"item":"minecraft:string"}]),
   height=10),
}


def write_png(p, w, h, px):
    def ch(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw += bytes(px[y][x])
    open(p, "wb").write(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                        + ch(b"IDAT", zlib.compress(bytes(raw), 9)) + ch(b"IEND", b""))



# --- flera ytor på samma block ----------------------------------------------
# ALLA KUBER DELADE SAMMA TEXTURHÖRN. uv låg hårdkodat på [0,0] och texturen var
# 16x16, så stolpen, mattan och träet på ett klösträd samplade exakt samma
# pixlar — ett rep kunde inte se ut som ett rep. Klösträdet läste som en I-balk.
#
# En kub får därför ange ett MATERIAL som tredje fält. Gör den det packas UV:n
# ut på en större duk och varje material målas för sig. Kuber utan tredje fält
# beter sig precis som förut, så de sju andra möblerna är orörda.
#
# Bedrocks utfällning av en kub (b,h,d) är 2*(d+b) bred och d+h hög — samma
# räkning som kattens och grisens kroppar använder.
DUK = (128, 64)

def packa_kuber(kuber):
    rutor = [(i, 2 * (k[1][2] + k[1][0]), k[1][2] + k[1][1]) for i, k in enumerate(kuber)]
    x = y = radhojd = 0
    uv = {}
    for i, w, h in sorted(rutor, key=lambda r: -r[2]):
        w, h = int(w + 0.999), int(h + 0.999)
        if x + w > DUK[0]:
            x, y, radhojd = 0, y + radhojd, 0
        if y + h > DUK[1]:
            raise SystemExit(f"blockets UV-yta räcker inte till ({DUK[0]}x{DUK[1]})")
        uv[i] = [x, y]
        x += w
        radhojd = max(radhojd, h)
    return uv


def mala_ytor(bid, cfg, uv):
    """Målar en duk där varje kub får sitt materials mönster i sin egen ruta."""
    W, H = DUK
    px = [[(0, 0, 0, 0)] * W for _ in range(H)]
    for i, kub in enumerate(cfg["cubes"]):
        mat = kub[2]
        f = cfg["material"][mat]
        u, v = uv[i]
        b, h, d = kub[1]
        bw, bh = int(2 * (d + b) + 0.999), int(d + h + 0.999)
        for yy in range(v, min(H, v + bh)):
            for xx in range(u, min(W, u + bw)):
                px[yy][xx] = f(xx - u, yy - v)
    return W, H, px

def texture(bid, cfg):
    """16x16 blocktextur: bas med vävt/nystat mönster.

    Block som anger MATERIAL per kub målas i stället på den packade duken, där
    varje kub får sin egen ruta — det är enda sättet att låta ett rep och en
    matta se olika ut på samma block."""
    if "material" in cfg:
        w, h, px = mala_ytor(bid, cfg, packa_kuber(cfg["cubes"]))
        write_png(f"{RP}/textures/blocks/pc_{bid}.png", w, h, px)
        return
    S = 16
    base = cfg["base"] + (255,)
    acc = cfg["accent"] + (255,)
    dark = tuple(int(c * 0.72) for c in cfg["base"]) + (255,)
    px = [[base] * S for _ in range(S)]
    if bid == "kartong":
        for y in range(S):
            for x in range(S):
                if (x + y * 3) % 7 == 0: px[y][x] = dark          # wellpapp-räfflor
    if bid == "fiskdamm":
        for y in range(S):
            for x in range(S):
                d2 = max(abs(x - 7.5), abs(y - 7.5))
                if d2 > 6: px[y][x] = dark                        # stenkant
                else:
                    px[y][x] = acc                                # vatten
                    if (x * 3 + y * 5) % 7 == 0: px[y][x] = (110, 176, 224, 255)
    if bid == "kattlucka":
        for y in range(S):
            for x in range(S):
                if x < 2 or x > 13 or y < 2: px[y][x] = dark      # karm
                elif (y % 5) == 0: px[y][x] = acc                 # panel
    if bid == "kattoa":
        for y in range(S):
            for x in range(S):
                d2 = max(abs(x - 7.5), abs(y - 7.5))
                if d2 > 6: px[y][x] = dark                        # kant
                elif (x * 7 + y * 3) % 5 == 0: px[y][x] = acc     # strö
    if bid == "stallning":
        for y in range(S):
            for x in range(S):
                if y % 4 == 0 and 5 <= x <= 10: px[y][x] = dark   # sisalvarv
                elif (x + y * 2) % 5 == 0: px[y][x] = acc         # matta
    if bid == "matskal":
        for y in range(S):
            for x in range(S):
                d2 = max(abs(x - 7.5), abs(y - 7.5))
                if d2 > 6: px[y][x] = dark          # kant
                elif d2 < 4: px[y][x] = (222, 130, 92, 255)  # mat (lax!)
                if d2 < 4 and (x + y) % 3 == 0: px[y][x] = (196, 100, 70, 255)
    if bid == "kattbadd":
        for y in range(S):                       # tygvävnad
            for x in range(S):
                if (x + y) % 4 == 0: px[y][x] = acc
                elif (x - y) % 6 == 0: px[y][x] = dark
        for i in range(S):                       # söm längs kanten
            for e in (0, 1, S - 2, S - 1):
                px[e][i] = dark; px[i][e] = dark
    else:
        for y in range(S):                       # garntrådar på tvären
            for x in range(S):
                if (x * 2 + y) % 5 == 0: px[y][x] = acc
                if (y * 2 - x) % 7 == 0: px[y][x] = dark
    write_png(f"{RP}/textures/blocks/pc_{bid}.png", S, S, px)


def build():
    for d in ("blocks", "recipes"): os.makedirs(f"{BP}/{d}", exist_ok=True)
    for d in ("textures/blocks", "models/blocks"): os.makedirs(f"{RP}/{d}", exist_ok=True)

    terrain = {"resource_pack_name": "PurrfectCompanions", "texture_name": "atlas.terrain", "texture_data": {}}
    blocksjson = {"format_version": [1, 1, 0]}
    lang = []

    for bid, cfg in BLOCKS.items():
        texture(bid, cfg)
        terrain[f"pc_{bid}"] = None  # platshållare, sätts nedan
        terrain["texture_data"][f"pc_{bid}"] = {"textures": f"textures/blocks/pc_{bid}"}
        terrain.pop(f"pc_{bid}")

        # geometri
        _flera = "material" in cfg
        _uv = packa_kuber(cfg["cubes"]) if _flera else None
        json.dump({"format_version": "1.16.0", "minecraft:geometry": [{
            "description": {"identifier": f"geometry.{bid}",
                            "texture_width": DUK[0] if _flera else 16,
                            "texture_height": DUK[1] if _flera else 16},
            "bones": [{"name": bid, "pivot": [0, 0, 0],
                       "cubes": [{"origin": k[0], "size": k[1],
                                  "uv": _uv[i] if _flera else [0, 0]}
                                 for i, k in enumerate(cfg["cubes"])]}]}]},
            open(f"{RP}/models/blocks/{bid}.geo.json", "w"), indent=2)

        h = cfg["height"]
        json.dump({"format_version": "1.20.50", "minecraft:block": {
            "description": {"identifier": f"mjau:{bid}", "menu_category": {"category": "nature"}},
            "components": {
                "minecraft:geometry": f"geometry.{bid}",
                # opaque på gles modell cullar grannblockens ytor -> "grop i golvet"
                # (2.6.1-läxan för kattluckan, gällde förstås ALLA glesa modeller)
                "minecraft:material_instances": {"*": {"texture": f"pc_{bid}", "render_method": "alpha_test"}},
                # KATTLUCKAN SKA GÅ ATT GÅ IGENOM — den är en lucka. Filen stod
                # handrättad till false och generatorn hade skrivit över den vid
                # nästa körning; nu säger blocket det själv.
                "minecraft:collision_box": (False if cfg.get("genomgang")
                                            else {"origin": [-8, 0, -8], "size": [16, h, 16]}),
                "minecraft:selection_box": {"origin": [-8, 0, -8], "size": [16, h, 16]},
                "minecraft:destructible_by_mining": {"seconds_to_destroy": 0.4},
                "minecraft:destructible_by_explosion": {"explosion_resistance": 0.5},
                "minecraft:light_dampening": 0,
                "minecraft:loot": f"loot_tables/blocks/{bid}.json"}}},
            open(f"{BP}/blocks/{bid}.json", "w"), indent=2)

        os.makedirs(f"{BP}/loot_tables/blocks", exist_ok=True)
        json.dump({"pools": [{"rolls": 1, "entries": [{"type": "item", "name": f"mjau:{bid}"}]}]},
                  open(f"{BP}/loot_tables/blocks/{bid}.json", "w"), indent=2)

        blocksjson[f"mjau:{bid}"] = {"textures": f"pc_{bid}", "sound": cfg["sound"]}

        r = cfg["recipe"]
        json.dump({"format_version": "1.20.10", "minecraft:recipe_shaped": {
            "description": {"identifier": f"mjau:{bid}"}, "tags": ["crafting_table"],
            "pattern": r["pattern"], "key": r["key"], "unlock": r["unlock"],
            "result": {"item": f"mjau:{bid}"}}},
            open(f"{BP}/recipes/{bid}.json", "w"), indent=2)

        lang.append(f"tile.mjau:{bid}.name={cfg['name']}")

    json.dump(terrain, open(f"{RP}/textures/terrain_texture.json", "w"), indent=2)
    json.dump(blocksjson, open(f"{RP}/blocks.json", "w"), indent=2)

    for pack in ("PurrfectCompanions_BP", "PurrfectCompanions_RP"):
        lp = f"{BASE}/{pack}/texts/en_US.lang"
        keep = [l for l in open(lp, encoding="utf-8").read().rstrip("\n").split("\n")
                if not l.startswith("tile.mjau:")]
        open(lp, "w", encoding="utf-8").write("\n".join(keep + lang) + "\n")

    # katterna söker sig till bädd, nystan och matskål — men bara av FRI VILJA:
    # beteendet bor i mjau:fri, som tas bort medan en spelare rider (annars
    # "styr katten sig själv", sett på Xbox).
    targets = [f"mjau:{b}" for b in BLOCKS]
    for f in sorted(glob.glob(f"{BP}/entities/*.json")):
        d = json.load(open(f)); ent = d["minecraft:entity"]
        # SKEPPET OCH FORDONEN HAR INGA KOMPONENTGRUPPER. Loopen tog alla
        # entitetsfiler och kraschade på den första utan grupper — samma klass
        # av fel som build_accessories fick fixad 2026-08-13, och den hade
        # legat kvar här hela tiden: skriptet dog EFTER att blocken skrivits,
        # så bygget såg ut att lyckas ända tills man läste sista raden.
        if "component_groups" not in ent:
            continue
        c = ent["component_groups"].setdefault("mjau:fri", {})
        c["minecraft:behavior.move_to_block"] = {
            "priority": 12, "tick_interval": 40, "start_chance": 0.4,
            "search_range": 12, "search_height": 4, "goal_radius": 1.5,
            "stay_duration": 20, "target_selection_method": "nearest",
            "target_offset": [0, 1, 0], "target_blocks": targets}
        # entydiga prioriteter (move_to_block ovanför random_stroll, annars kör den aldrig)
        order = ["minecraft:behavior.controlled_by_player", "minecraft:behavior.float",
                 "minecraft:behavior.panic", "minecraft:behavior.drop_item_for",
                 "minecraft:behavior.breed", "minecraft:behavior.stay_while_sitting",
                 "minecraft:behavior.nearest_attackable_target",
                 "minecraft:behavior.stalk_and_pounce_on_target", "minecraft:behavior.melee_attack",
                 "minecraft:behavior.tempt", "minecraft:behavior.follow_owner",
                 "minecraft:behavior.follow_parent", "minecraft:behavior.move_to_block",
                 "minecraft:behavior.nap", "minecraft:behavior.random_stroll", "minecraft:behavior.random_sitting",
                 "minecraft:behavior.look_at_player", "minecraft:behavior.random_look_around"]
        P = {k: i for i, k in enumerate(order)}
        # OBS: c pekar på mjau:fri sedan frivilje-flytten — basen måste med separat
        # GRUPPER MED MEDVETET VALDA PRIORITETER LÄMNAS IFRED. Omnumreringen
        # sätter move_to_block till 12 och random_sitting till 15 ÖVERALLT, och
        # skrev därmed sönder mjau:sovdags, som fått 19 och 20 just för att inte
        # krocka med mjau:fri:s. Två beteenden med samma prioritet är odefinierat
        # i Bedrock, så kolonins nattgrupp slutade fungera i tysthet varje gång
        # det här skriptet kördes EFTER build_accessories.
        #
        # En grupp vars prioriteter är valda med avsikt måste stå här. Glöms den
        # fäller strukturgrindens prioritetskontroll bygget, så felet kan inte
        # nå ett släpp — men det är billigare att slippa felsöka det.
        SKYDDADE = {"mjau:sovdags"}
        for namn, bucket in [("", ent["components"])] + \
                            list(ent.get("component_groups", {}).items()):
            if namn in SKYDDADE:
                continue
            for k, v in bucket.items():
                if k in P and isinstance(v, dict): v["priority"] = P[k]
        json.dump(d, open(f, "w"), indent=2)

    return len(BLOCKS), targets


if __name__ == "__main__":
    n, t = build()
    print(f"{n} block byggda: {', '.join(t)}")
    print("katterna söker sig till dem via behavior.move_to_block (prio 12)")
