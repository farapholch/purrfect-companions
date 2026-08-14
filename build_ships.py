#!/usr/bin/env python3
"""Genererar SPJUTJAKTAREN — Stjärnhamnens flygbara jaktplan.

Jaktplanen i hangaren var byggda av block: snygga att titta på, men bara
kulisser ("kan man köra rymdskeppen?" — nej). Det här skriptet gör dem till
en riktig entitet man kan sätta sig i och flyga.

Genererar allt som behövs, på samma sätt som build_accessories.py:
  BP/entities/spjutjaktare.json          komponenter, sits, flygning
  RP/entity/spjutjaktare.json            klientdefinition + spawnägg
  RP/models/entity/spjutjaktare.geo.json geometri (kabin, bommar, vingpaneler)
  RP/textures/entity/spjutjaktare.png    textur
  RP/texts/*.lang                        namnet på båda språken

Formen är EGEN, inte lånad: klotkabin mellan två höga sexkantiga paneler.
Samma siluett som blockbygget i hangaren, så det man ser är det man flyger.

    python3 build_ships.py
"""
import json, os, struct, sys, zlib

BASE = os.path.dirname(os.path.abspath(__file__))
BP = f"{BASE}/PurrfectCompanions_BP"
RP = f"{BASE}/PurrfectCompanions_RP"

ID = "mjau:spjutjaktare"
NAMN = {"en_US": "Spear Fighter", "sv_SE": "Spjutjaktare"}

# ------------------------------------------------------------------ geometri
# 16 enheter = 1 block. Kabinen sitter mellan panelerna, bommarna håller ihop.
# Ytterkant -32..32 (4 block bred), 0..52 hög (3¼ block) — stor nog att kännas
# som ett fordon, liten nog att komma ut genom hangarporten.
KUBER = [
    # (namn, origin, size, uv)
    ("kabin", [-10, 16, -10], [20, 20, 20], [0, 0]),
    ("bom_v", [-26, 24, -3], [16, 4, 6], [0, 48]),
    ("bom_h", [10, 24, -3], [16, 4, 6], [0, 48]),
    ("panel_v", [-32, 0, -14], [6, 52, 28], [0, 64]),
    ("panel_h", [26, 0, -14], [6, 52, 28], [0, 64]),
]
TEX_W = TEX_H = 256


def geometri():
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": "geometry.spjutjaktare",
                "texture_width": TEX_W, "texture_height": TEX_H,
                "visible_bounds_width": 5, "visible_bounds_height": 5,
                "visible_bounds_offset": [0, 1.5, 0],
            },
            "bones": [{
                "name": "body", "pivot": [0, 0, 0],
                "cubes": [{"origin": o, "size": s, "uv": uv}
                          for _, o, s, uv in KUBER],
            }],
        }],
    }


# -------------------------------------------------------------------- textur
def png(path, pixlar, w, h):
    """Minimal PNG-skrivare — samma teknik som resten av projektet."""
    rader = b"".join(b"\x00" + b"".join(bytes(p) for p in rad) for rad in pixlar)
    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))
    ut = (b"\x89PNG\r\n\x1a\n"
          + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
          + chunk(b"IDAT", zlib.compress(rader))
          + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(ut)


def textur():
    SKROV = (38, 38, 48, 255)      # mörk skrovplåt
    KANT = (24, 24, 32, 255)       # panelkant
    KABIN = (58, 58, 72, 255)
    FONSTER = (130, 200, 240, 255)
    px = [[KANT for _ in range(TEX_W)] for _ in range(TEX_H)]

    def rect(x0, y0, w, h, f):
        for y in range(y0, min(TEX_H, y0 + h)):
            for x in range(x0, min(TEX_W, x0 + w)):
                px[y][x] = f

    # box-uv: en kub (w,h,d) upptar 2*(w+d) x (h+d) från sin uv-punkt
    rect(0, 0, 2 * (20 + 20), 20 + 20, KABIN)       # kabinen
    rect(0, 48, 2 * (16 + 6), 4 + 6, SKROV)         # bommen
    rect(0, 64, 2 * (6 + 28), 52 + 28, SKROV)       # vingpanelen
    # panelens nitrader — ger plåten struktur i stället för en platt yta
    for y in range(70, 140, 8):
        rect(6, y, 56, 1, KANT)
    # KABINENS FRAMSIDA i box-uv ligger på (d, d) med storlek (w, h)
    # = (20,20) 20x20. Fönsterbandet målas där, annars ser kabinen blind ut.
    rect(22, 24, 16, 6, FONSTER)
    png(f"{RP}/textures/entity/spjutjaktare.png", px, TEX_W, TEX_H)


# -------------------------------------------------------------------- entitet
def bp_entitet():
    return {
        "format_version": "1.20.50",
        "minecraft:entity": {
            "description": {
                "identifier": ID,
                "is_spawnable": True, "is_summonable": True,
            },
            "component_groups": {},
            "components": {
                "minecraft:type_family": {"family": ["spjutjaktare", "mjaufordon"]},
                "minecraft:health": {"value": 60, "max": 60},
                "minecraft:collision_box": {"width": 2.8, "height": 3.2},
                "minecraft:knockback_resistance": {"value": 1.0},
                "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
                # ett fordon ska inte ta fallskada och inte drunkna i tomrummet
                "minecraft:damage_sensor": {"triggers": [
                    {"cause": "fall", "deals_damage": False},
                    {"cause": "void", "deals_damage": False}]},
                # FLYGNINGEN. input_ground_controlled ger ryttaren styrningen,
                # can_fly + navigation.fly gör att motorn accepterar höjd, och
                # can_power_jump + jump_strength är stigningen. Utan gravitation
                # skulle planet stå stilla i luften när man släpper allt — med
                # den sjunker det mjukt, vilket är det som känns som flygning.
                "minecraft:movement": {"value": 0.42},
                "minecraft:movement.fly": {},
                "minecraft:navigation.fly": {"can_path_over_water": True},
                "minecraft:can_fly": {},
                "minecraft:jump.static": {},
                "minecraft:horse.jump_strength": {"value": 1.6},
                "minecraft:can_power_jump": {},
                "minecraft:input_ground_controlled": {},
                # TVA sitsar: piloten framme, katten i navigatorsstolen.
                # Kravet "man ska behova ha katt med sig for att flyga" losas
                # inte med ett osynligt villkor utan med en stol — katten aker
                # med, och det syns.
                "minecraft:rideable": {
                    "seat_count": 2, "family_types": ["player", "mjaukatt"],
                    "interact_text": "action.interact.ride",
                    "seats": [{"position": [0.0, 1.35, 0.2]},
                              {"position": [0.0, 1.30, -0.85]}]},
                "minecraft:persistent": {},
                "minecraft:nameable": {},
                "minecraft:behavior.look_at_player": {"priority": 9,
                                                      "look_distance": 8},
            },
            "events": {},
        },
    }


def rp_entitet():
    return {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": ID,
                "materials": {"default": "entity_alphatest"},
                "textures": {"default": "textures/entity/spjutjaktare"},
                "geometry": {"default": "geometry.spjutjaktare"},
                "spawn_egg": {"base_colour": "#26262f", "overlay_colour": "#82c8f0"},
                "render_controllers": ["controller.render.default"],
            },
        },
    }


def sprak():
    for lang, namn in NAMN.items():
        p = f"{RP}/texts/{lang}.lang"
        rader = open(p, encoding="utf-8").read().splitlines() if os.path.exists(p) else []
        # båda formerna: UI-skärmar slår upp namnet utan namnrymd (2.6.3-läxan)
        vill = {f"entity.{ID}.name": namn,
                f"entity.spjutjaktare.name": namn,
                f"item.spawn_egg.entity.{ID}.name": f"Spawn {namn}"}
        kvar = [r for r in rader if r.split("=")[0] not in vill]
        for k, v in vill.items():
            kvar.append(f"{k}={v}")
        open(p, "w", encoding="utf-8").write("\n".join(kvar) + "\n")


def main():
    os.makedirs(f"{BP}/entities", exist_ok=True)
    os.makedirs(f"{RP}/entity", exist_ok=True)
    os.makedirs(f"{RP}/models/entity", exist_ok=True)
    json.dump(bp_entitet(), open(f"{BP}/entities/spjutjaktare.json", "w"),
              indent=2, ensure_ascii=False)
    json.dump(rp_entitet(), open(f"{RP}/entity/spjutjaktare.json", "w"),
              indent=2, ensure_ascii=False)
    json.dump(geometri(), open(f"{RP}/models/entity/spjutjaktare.geo.json", "w"),
              indent=2, ensure_ascii=False)
    textur()
    sprak()
    print(f"spjutjaktare: entitet + geometri ({len(KUBER)} kuber) + textur + språk")


if __name__ == "__main__":
    main()
