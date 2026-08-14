#!/usr/bin/env python3
"""Genererar STJÄRNHAMNS-PACKEN — spjutjaktaren, som en EGEN add-on.

Skeppet låg först i kattpaketet. Det hörde inte hemma där: Purrfect Companions
säljs som ett kattpaket, och ett rymdskepp bland tillbehören förvirrar den som
laddar ner det för katternas skull ("jag tror inte jag vill ha den i katt-
paketet", "fokusera på addonet och att det bara håller katt-tema").

Nu bor skeppet i PurrfectHarbour_BP/RP med egna UUID:n och eget skript.
Stjärnhamnen bäddar in BÅDA paketen; kattpaketet vet ingenting om skepp.

Plaggen (energisvärd, rymdmantel) stannar däremot kvar i kattpaketet — de
sitter monterade på kattmodellen, och att flytta dem hade krävt att den här
packen bar egna kopior av alla åtta kattentiteter.

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
BP = f"{BASE}/PurrfectHarbour_BP"
RP = f"{BASE}/PurrfectHarbour_RP"
GAMMAL_BP = f"{BASE}/PurrfectCompanions_BP"
GAMMAL_RP = f"{BASE}/PurrfectCompanions_RP"

# egna UUID:n — får ALDRIG krocka med kattpaketets
# Header och moduler måste ha OLIKA UUID:n — samma på båda ger
# "Provided UUID '/header/uuid' element already exists in pack manifest"
# och hela paketet ignoreras tyst av servern.
UUID_BP = "b1e7c9a4-5f28-4d63-9a17-2c8e05f4d311"
UUID_BP_DATA = "e4b0fcd7-825b-4096-ad4a-5fb138c7a644"
UUID_BP_SKRIPT = "c2f8dab5-6039-4e74-8b28-3d9f16a5e422"
UUID_RP = "d3a9ebc6-714a-4f85-9c39-4ea027b6f533"
UUID_RP_MODUL = "f5c10de8-936c-41a7-be5b-60c249d8b755"
VERSION = [1, 1, 0]
SERVER_API = "1.9.0"     # samma nivå som kattpaketet kör mot

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
                # is_spawnable=False: INGET spawnägg. Skeppet ska inte dyka upp
                # bland addonets föremål — "jag tror inte jag vill ha den i
                # kattpaketet". Det summoneras av Stjärnhamnen vid bygget och
                # finns bara där, medan Purrfect Companions förblir ett
                # kattpaket i allt spelaren ser.
                "identifier": ID,
                "is_spawnable": False, "is_summonable": True,
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
                "render_controllers": ["controller.render.default"],
            },
        },
    }


MEDDELANDEN = {
    "en_US": {"mjau.skepp.varning": "Turn back - the harbour is falling behind",
              "mjau.skepp.hem": "Autopilot returned you to the landing pad",
              "mjau.skepp.behovkatt": "A cat must fly with you - call one over",
              "mjau.skepp.utankatt": "No cat aboard. The harbour will not let you launch."},
    "sv_SE": {"mjau.skepp.varning": "Vand om - hamnen borjar forsvinna bakom dig",
              "mjau.skepp.hem": "Autopiloten satte dig pa landningsplattan",
              "mjau.skepp.behovkatt": "En katt maste folja med - ropa hit en",
              "mjau.skepp.utankatt": "Ingen katt ombord. Hamnen slapper inte ivag dig."},
}


def sprak():
    os.makedirs(f"{RP}/texts", exist_ok=True)
    for lang, namn in NAMN.items():
        p = f"{RP}/texts/{lang}.lang"
        rader = open(p, encoding="utf-8").read().splitlines() if os.path.exists(p) else []
        # båda formerna: UI-skärmar slår upp namnet utan namnrymd (2.6.3-läxan)
        # ingen spawnägg-sträng: ägget finns inte längre
        vill = {f"entity.{ID}.name": namn,
                f"entity.spjutjaktare.name": namn}
        vill.update(MEDDELANDEN[lang])
        kvar = [r for r in rader if r.split("=")[0] not in vill]
        for k, v in vill.items():
            kvar.append(f"{k}={v}")
        open(p, "w", encoding="utf-8").write("\n".join(kvar) + "\n")


def manifest_bp():
    return {
        "format_version": 2,
        "header": {
            "name": "Star Harbour - Spear Fighter",
            "description": "Det flygbara jaktplanet i Stjarnhamnen. Kraver Purrfect Companions.",
            "uuid": UUID_BP, "version": VERSION, "min_engine_version": [1, 20, 0],
        },
        "modules": [
            {"type": "data", "uuid": UUID_BP_DATA, "version": VERSION},
            {"type": "script", "language": "javascript", "uuid": UUID_BP_SKRIPT,
             "version": VERSION, "entry": "scripts/skepp.js"},
        ],
        "dependencies": [{"module_name": "@minecraft/server", "version": SERVER_API}],
    }


def manifest_rp():
    return {
        "format_version": 2,
        "header": {
            "name": "Star Harbour - Spear Fighter",
            "description": "Modell och textur till jaktplanet.",
            "uuid": UUID_RP, "version": VERSION, "min_engine_version": [1, 20, 0],
        },
        "modules": [{"type": "resources", "uuid": UUID_RP_MODUL, "version": VERSION}],
    }


def skript():
    """Skeppets egen logik, utbruten ur kattpaketets main.js."""
    kod = open(f"{BASE}/tools/skeppskod.js", encoding="utf-8").read()
    return 'import { world, system } from "@minecraft/server";\n\n' + kod


def stada_gamla_spar():
    """Skeppet låg förut i kattpaketet — filerna får inte bli kvar där."""
    for p in (f"{GAMMAL_BP}/entities/spjutjaktare.json",
              f"{GAMMAL_RP}/entity/spjutjaktare.json",
              f"{GAMMAL_RP}/models/entity/spjutjaktare.geo.json",
              f"{GAMMAL_RP}/textures/entity/spjutjaktare.png"):
        if os.path.exists(p):
            os.remove(p); print(f"  tog bort ur kattpaketet: {os.path.relpath(p, BASE)}")
    for lang in NAMN:
        f = f"{GAMMAL_RP}/texts/{lang}.lang"
        if not os.path.exists(f): continue
        rader = open(f, encoding="utf-8").read().splitlines()
        kvar = [r for r in rader if "spjutjaktare" not in r and "mjau.skepp." not in r]
        if len(kvar) != len(rader):
            open(f, "w", encoding="utf-8").write("\n".join(kvar) + "\n")
            print(f"  rensade {len(rader)-len(kvar)} rader ur {lang}.lang")


def main():
    stada_gamla_spar()
    os.makedirs(f"{BP}/entities", exist_ok=True)
    os.makedirs(f"{BP}/scripts", exist_ok=True)
    json.dump(manifest_bp(), open(f"{BP}/manifest.json", "w"), indent=2)
    os.makedirs(f"{RP}/entity", exist_ok=True)
    json.dump(manifest_rp(), open(f"{RP}/manifest.json", "w"), indent=2)
    open(f"{BP}/scripts/skepp.js", "w", encoding="utf-8").write(skript())
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
