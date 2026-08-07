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


def texture(bid, cfg):
    """16x16 blocktextur: bas med vävt/nystat mönster."""
    S = 16
    base = cfg["base"] + (255,)
    acc = cfg["accent"] + (255,)
    dark = tuple(int(c * 0.72) for c in cfg["base"]) + (255,)
    px = [[base] * S for _ in range(S)]
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
        json.dump({"format_version": "1.16.0", "minecraft:geometry": [{
            "description": {"identifier": f"geometry.{bid}", "texture_width": 16, "texture_height": 16},
            "bones": [{"name": bid, "pivot": [0, 0, 0],
                       "cubes": [{"origin": o, "size": s, "uv": [0, 0]} for o, s in cfg["cubes"]]}]}]},
            open(f"{RP}/models/blocks/{bid}.geo.json", "w"), indent=2)

        h = cfg["height"]
        json.dump({"format_version": "1.20.50", "minecraft:block": {
            "description": {"identifier": f"mjau:{bid}", "menu_category": {"category": "nature"}},
            "components": {
                "minecraft:geometry": f"geometry.{bid}",
                "minecraft:material_instances": {"*": {"texture": f"pc_{bid}", "render_method": "opaque"}},
                "minecraft:collision_box": {"origin": [-8, 0, -8], "size": [16, h, 16]},
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

    # katterna söker sig till bädd och nystan
    targets = [f"mjau:{b}" for b in BLOCKS]
    for f in sorted(glob.glob(f"{BP}/entities/*.json")):
        d = json.load(open(f)); c = d["minecraft:entity"]["components"]
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
                 "minecraft:behavior.random_stroll", "minecraft:behavior.random_sitting",
                 "minecraft:behavior.look_at_player", "minecraft:behavior.random_look_around"]
        P = {k: i for i, k in enumerate(order)}
        for bucket in [c] + list(d["minecraft:entity"].get("component_groups", {}).values()):
            for k, v in bucket.items():
                if k in P and isinstance(v, dict): v["priority"] = P[k]
        json.dump(d, open(f, "w"), indent=2)

    return len(BLOCKS), targets


if __name__ == "__main__":
    n, t = build()
    print(f"{n} block byggda: {', '.join(t)}")
    print("katterna söker sig till dem via behavior.move_to_block (prio 12)")
