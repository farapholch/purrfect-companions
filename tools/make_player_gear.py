#!/usr/bin/env python3
"""Kattdräkten — fyra plagg som SPELAREN bär, inte katten.

Önskemål från barnen: "man själv som gubbe ska också ha kattutrustning". Hela
paketet har hittills bara klätt katten; ingenting har ritats på spelarkroppen,
och paketet hade inga attachables alls. Det här skriptet skapar allt som krävs:

  luva   slot.armor.head    kattöron, rosa insida
  vast   slot.armor.chest   päls med ljus mage
  byxor  slot.armor.legs
  tassar slot.armor.feet    ljusa tassar med rosa trampdynor

Skyddet motsvarar järnrustning (2/6/5/2), så dräkten är ett riktigt alternativ
och inte bara utklädnad.

TRE SAKER SOM MÅSTE STÄMMA, och som inget serverprov kan se:

1. BENNAMNEN i geometrin måste vara spelarskelettets (head, body, leftArm,
   rightArm, leftLeg, rightLeg). Fel namn = plagget hamnar i marken. Samma
   fälla som fällde vakthunden, fast på spelaren.
2. INFLATE lyfter plagget utanför kroppen. Utan den ligger tyget exakt i
   samma yta som huden och flimrar (z-fighting).
3. Attachablens `parent_setup` släcker vaniljalagret, annars syns både vår
   luva och en osynlig hjälmkontur.

Egna UV:n i egna texturer — vi behöver alltså inte gissa vaniljas
rustningsutfällning, som ändå inte går att läsa här (BDS resurspack är
avskalad).

    python3 tools/make_player_gear.py
"""
import json, math, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import render_regression as rr

BP = f"{BASE}/PurrfectCompanions_BP"
RP = f"{BASE}/PurrfectCompanions_RP"
TW = TH = 64

PALS      = (150, 140, 128, 255)   # varm kattgrå — syns mot både gräs och sten
PALS_MORK = (112, 104, 95, 255)
MAGE      = (224, 218, 208, 255)   # ljus mage, bringa och tassar
ORA_IN    = (226, 140, 160, 255)   # samma rosa som katternas nos och trampdynor
DYNA      = (226, 140, 160, 255)
OGON      = (232, 176, 64, 255)    # bärnsten, samma som vakthundens
OGON_GLANS = (255, 232, 176, 255)


def fot(size):
    w, h, d = size
    return math.ceil(2 * (d + w)), math.ceil(d + h)


# NIVÅERNA. Läderdräkten är BASEN och behåller sina gamla identifierare
# (mjau:luva, mjau:vast ...) — byter man id försvinner plaggen ur inventariet
# hos alla som redan har dem, och familjen har dem sedan 3.28.0. De tre nya
# nivåerna får suffix.
#
# Skyddet stiger, men KRAFTERNA är det som gör uppgraderingen värd besväret;
# de bor i main.js och står listade här bara som dokumentation:
#
#   läder     mörkerseende · motstånd I · snabbhet I · mjuk landning
#             hel dräkt: snabbhet II + hopp, katterna omkring dig läks
#   järn      + hoppkraft i tassarna
#             hel dräkt: styrka I när en tämjd katt är i närheten
#   diamant   motstånd II · snabbhet II
#             hel dräkt: läkning I
#   netherit  + eldskydd i luvan (netherit brinner inte)
#             hel dräkt: styrka I alltid, och katterna omkring dig får motstånd
#
# Geometrin DELAS mellan nivåerna — det är samma dräkt, i annat material. Bara
# textur, ikon, skydd och slitage skiljer.
NIVAER = {
    "": {"namn": "", "skydd": 0, "slitage": 1.0, "pals": (150, 140, 128, 255),
         "mork": (112, 104, 95, 255), "ljus": (224, 218, 208, 255), "upp": None, "antal": 0},
    "jarn": {"namn": "Iron ", "skydd": 1, "slitage": 1.8, "pals": (176, 178, 186, 255),
             "mork": (128, 131, 140, 255), "ljus": (226, 228, 234, 255),
             "upp": "minecraft:iron_ingot", "antal": 5},
    "diamant": {"namn": "Diamond ", "skydd": 2, "slitage": 3.4, "pals": (94, 200, 202, 255),
                "mork": (58, 148, 156, 255), "ljus": (198, 244, 246, 255),
                "upp": "minecraft:diamond", "antal": 5},
    "netherit": {"namn": "Netherite ", "skydd": 2, "slitage": 5.0, "pals": (74, 66, 70, 255),
                 "mork": (48, 42, 46, 255), "ljus": (150, 132, 120, 255),
                 "upp": "minecraft:netherite_ingot", "antal": 1},
}
NIVAORDNING = ["", "jarn", "diamant", "netherit"]


def farga(c, niv):
    """Kubens färg översatt till nivåns palett. Kuberna är skrivna i lädrets
    färger; nivån byter ut dem så samma tabell duger till alla fyra."""
    n = NIVAER[niv]
    return {PALS: n["pals"], PALS_MORK: n["mork"], MAGE: n["ljus"],
            ORA_IN: ORA_IN, DYNA: DYNA}.get(c, c)


# (ben, origin, size, uv, färg) — spelarskelettets bennamn, inget annat duger
PLAGG = {
    "luva": {
        "slot": "slot.armor.head", "skydd": 2, "slitage": 165,
        "namn": "Cat Hood", "enchant": "armor_head",
        "kuber": [
            ("head", [-4, 24, -4], [8, 8, 8], [0, 0], PALS, 1.0),
            # ÖRONEN: hjälmkuben är inflate 1.0 och når därmed y=33, inte 32.
            # Första försöket satte öronen på 31-34 — tre av fyra enheter låg
            # INUTI hjälmen och kvar syntes en stump. Xbox-rapport: "inga
            # öron". De börjar nu ovanför hjälmens topp och är 5 höga.
            ("head", [-4.5, 32, -2.5], [3, 5, 1], [40, 0], PALS_MORK, 0.0),  # vänster öra
            ("head", [1.5, 32, -2.5], [3, 5, 1], [46, 0], PALS_MORK, 0.0),   # höger öra
            ("head", [-3.8, 33.4, -2.9], [1.6, 3, 0.6], [40, 12], ORA_IN, 0.0),
            ("head", [2.2, 33.4, -2.9], [1.6, 3, 0.6], [46, 12], ORA_IN, 0.0),
        ],
    },
    "vast": {
        "slot": "slot.armor.chest", "skydd": 6, "slitage": 240,
        "namn": "Cat Vest", "enchant": "armor_torso",
        "kuber": [
            ("body", [-4, 12, -2], [8, 12, 4], [0, 0], PALS, 1.01),
            ("body", [-2.5, 12.5, -2.6], [5, 8, 1], [26, 0], MAGE, 0.0),      # ljus bringa
            # KORTA ÄRMAR. Först täckte de hela armen (y 12-24) och satt kant i
            # kant med bålen — med inflate växte de ihop till ETT brett block
            # och spelaren såg armlös ut. Xbox-bild: "man har typ inga armar".
            #
            # En väst ÄR ärmlös, så plagget får axelstycken (y 18-24) och
            # lämnar underarmen bar: armarna syns, rör sig, och silhuetten
            # läser som en människa igen. Mindre inflate så axeln inte
            # blir bredare än kroppen.
            ("leftArm", [4, 18, -2], [4, 6, 4], [40, 0], PALS_MORK, 0.6),
            ("rightArm", [-8, 18, -2], [4, 6, 4], [40, 14], PALS_MORK, 0.6),
        ],
    },
    "byxor": {
        "slot": "slot.armor.legs", "skydd": 5, "slitage": 225,
        "namn": "Cat Trousers", "enchant": "armor_legs",
        "kuber": [
            ("body", [-4, 12, -2], [8, 12, 4], [0, 0], PALS_MORK, 0.55),
            ("leftLeg", [0, 0, -2], [4, 12, 4], [28, 0], PALS_MORK, 0.55),
            ("rightLeg", [-4, 0, -2], [4, 12, 4], [28, 20], PALS_MORK, 0.55),
        ],
    },
    "tassar": {
        "slot": "slot.armor.feet", "skydd": 2, "slitage": 195,
        "namn": "Cat Paws", "enchant": "armor_feet",
        "kuber": [
            ("leftLeg", [0, 0, -2], [4, 5, 4], [0, 0], MAGE, 1.0),
            ("rightLeg", [-4, 0, -2], [4, 5, 4], [0, 14], MAGE, 1.0),
            ("leftLeg", [0.6, -0.1, -2.6], [2.8, 1, 1], [28, 0], DYNA, 0.0),   # trampdynor
            ("rightLeg", [-3.4, -0.1, -2.6], [2.8, 1, 1], [28, 4], DYNA, 0.0),
        ],
    },
}


def ident(namn, niv):
    """Basen behåller sitt gamla id — se kommentaren vid NIVAER."""
    return namn if not niv else f"{namn}_{niv}"


def sh(c, k):
    return tuple(min(255, int(v * k)) for v in c[:3]) + (255,)


def geometri(namn, cfg):
    ben = {}
    for b, origin, size, uv, _f, inflate in cfg["kuber"]:
        kub = {"origin": origin, "size": size, "uv": uv}
        if inflate:
            kub["inflate"] = inflate
        ben.setdefault(b, []).append(kub)
    PIVOT = {"head": [0, 24, 0], "body": [0, 24, 0],
             "leftArm": [5, 22, 0], "rightArm": [-5, 22, 0],
             "leftLeg": [1.9, 12, 0], "rightLeg": [-1.9, 12, 0]}
    g = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": f"geometry.mjau_{namn}",
                        "texture_width": TW, "texture_height": TH,
                        "visible_bounds_width": 2, "visible_bounds_height": 3,
                        "visible_bounds_offset": [0, 1.5, 0]},
        "bones": [{"name": b, "pivot": PIVOT[b], "cubes": k} for b, k in ben.items()]}]}
    json.dump(g, open(f"{RP}/models/entity/mjau_{namn}.geo.json", "w"), indent=2)
    return len(ben), len(cfg["kuber"])


def textur(namn, cfg, niv):
    px = [[(0, 0, 0, 0)] * TW for _ in range(TH)]

    def rect(x0, y0, w, h, c):
        for y in range(int(y0), int(y0 + h)):
            for x in range(int(x0), int(x0 + w)):
                if 0 <= x < TW and 0 <= y < TH:
                    px[y][x] = c
    for b, origin, size, uv, farg0, _i in cfg["kuber"]:
        farg = farga(farg0, niv)
        w, h, d = size
        fw, fh = fot(size)
        rect(uv[0], uv[1], fw, fh, farg)
        rect(uv[0], uv[1], fw, math.ceil(d), sh(farg, 1.14))
        rect(uv[0], uv[1] + fh - 1, fw, 1, sh(farg, 0.72))
        # KATTANSIKTET målas på huvudkubens framsida — utan det är luvan en
        # slät låda på skallen, vilket är exakt vad som rapporterades från
        # Xbox ("inga ögon"). Ögonen är bärnsten i alla nivåer: de ska läsa
        # som katt även när materialet är diamant.
        if namn == "luva" and size == [8, 8, 8]:
            fx, fy = uv[0] + d, uv[1] + d
            rect(fx + 1, fy + 2, 2, 2, OGON)          # vänster öga
            # HÖGDAGERN SPEGLAS: båda låg på ögats vänstra pixel, vilket gav
            # vänster öga glansen på utsidan och höger på insidan — ansiktet
            # läste som att det sneglade ("ögonen sitter snett"). Allt annat i
            # ansiktet var redan spegelsymmetriskt, uppmätt pixel för pixel.
            rect(fx + 5, fy + 2, 2, 2, OGON)          # höger öga
            rect(fx + 1, fy + 2, 1, 1, OGON_GLANS)
            rect(fx + 6, fy + 2, 1, 1, OGON_GLANS)
            rect(fx + 3, fy + 4, 2, 1, ORA_IN)        # nos
            rect(fx + 2, fy + 5, 1, 1, sh(farg, 0.55))   # mungipor
            rect(fx + 5, fy + 5, 1, 1, sh(farg, 0.55))
            for mx in (fx, fx + 7):                   # morrhår
                rect(mx, fy + 4, 1, 1, sh(farg, 1.3))
    rr.write_png(f"{RP}/textures/entity/mjau_{ident(namn, niv)}.png", TW, TH, px)


def attachable(namn, cfg, niv):
    """Utan attachable BÄRS plagget men syns inte — bara ikonen i rutan."""
    d = {"format_version": "1.10.0", "minecraft:attachable": {"description": {
        "identifier": f"mjau:{ident(namn, niv)}",
        "materials": {"default": "armor", "enchanted": "armor_enchanted"},
        "textures": {"default": f"textures/entity/mjau_{ident(namn, niv)}",
                     "enchanted": "textures/misc/enchanted_item_glint"},
        "geometry": {"default": f"geometry.mjau_{namn}"},
        # släck vaniljalagret för samma plats, annars ritas två plagg
        "scripts": {"parent_setup": f"variable.{ {'luva':'helmet','vast':'chest','byxor':'leg','tassar':'boot'}[namn] }_layer_visible = 0.0;"},
        "render_controllers": ["controller.render.armor"]}}}
    json.dump(d, open(f"{RP}/attachables/{ident(namn, niv)}.json", "w"), indent=2)


def ikon(namn, cfg, niv):
    PALS, PALS_MORK, MAGE = (NIVAER[niv]["pals"], NIVAER[niv]["mork"], NIVAER[niv]["ljus"])
    N = 16
    px = [[(0, 0, 0, 0)] * N for _ in range(N)]

    def rect(x0, y0, w, h, c):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if 0 <= x < N and 0 <= y < N:
                    px[y][x] = c
    if namn == "luva":
        rect(3, 4, 10, 9, PALS); rect(2, 1, 3, 4, PALS_MORK); rect(11, 1, 3, 4, PALS_MORK)
        rect(3, 2, 1, 2, ORA_IN); rect(12, 2, 1, 2, ORA_IN)
        rect(5, 8, 2, 2, (40, 40, 46, 255)); rect(9, 8, 2, 2, (40, 40, 46, 255))
        rect(3, 4, 10, 1, sh(PALS, 1.14))
    elif namn == "vast":
        rect(4, 3, 8, 10, PALS); rect(2, 4, 2, 6, PALS); rect(12, 4, 2, 6, PALS)
        rect(6, 5, 4, 6, MAGE); rect(4, 3, 8, 1, sh(PALS, 1.14))
    elif namn == "byxor":
        rect(4, 2, 8, 5, PALS_MORK); rect(4, 7, 3, 7, PALS_MORK); rect(9, 7, 3, 7, PALS_MORK)
        rect(4, 2, 8, 1, sh(PALS_MORK, 1.14))
    else:
        rect(3, 6, 4, 7, MAGE); rect(9, 6, 4, 7, MAGE)
        rect(3, 11, 4, 2, DYNA); rect(9, 11, 4, 2, DYNA)
        rect(3, 6, 4, 1, sh(MAGE, 1.14)); rect(9, 6, 4, 1, sh(MAGE, 1.14))
    rr.write_png(f"{RP}/textures/items/pc_{ident(namn, niv)}.png", N, N, px)


# --- föremål och recept -----------------------------------------------------
# Läder och ull, samma material som kattens egna plagg — dräkten hör ihop med
# resten av paketet och kräver inget nytt som barnen inte redan har.
MONSTER = {
    "luva":   ["WLW", "L L"],
    "vast":   ["L L", "LWL", "LLL"],
    # ULLEN I TOPPEN är inte pynt: rent läder ger EXAKT vaniljas recept för
    # läderbyxor, och då hade spelaren fått vaniljabyxorna i stället för våra.
    # Granskningen (audit.py mot en vaniljakopia) fångade det.
    "byxor":  ["LWL", "L L", "L L"],
    "tassar": ["L L", "W W"],
}


def foremal(namn, cfg, niv):
    n = NIVAER[niv]
    json.dump({"format_version": "1.20.50", "minecraft:item": {
        "description": {"identifier": f"mjau:{ident(namn, niv)}",
                        "menu_category": {"category": "equipment"}},
        "components": {
            "minecraft:icon": {"texture": f"pc_{ident(namn, niv)}"},
            "minecraft:display_name": {"value": n["namn"] + cfg["namn"]},
            "minecraft:max_stack_size": 1,
            "minecraft:wearable": {"slot": cfg["slot"],
                                   "protection": cfg["skydd"] + n["skydd"]},
            "minecraft:durability": {"max_durability": int(cfg["slitage"] * n["slitage"])},
            "minecraft:repairable": {"repair_items": [
                {"items": ["minecraft:leather"], "repair_amount": 25}]},
            "minecraft:enchantable": {"slot": cfg["enchant"], "value": 9},
        }}}, open(f"{BP}/items/{ident(namn, niv)}.json", "w"), indent=2)
    if niv:
        # UPPGRADERING, inte nytillverkning: nivån under plus material. Kan
        # aldrig krocka med ett vaniljarecept eftersom vårt eget plagg ingår.
        forra = NIVAORDNING[NIVAORDNING.index(niv) - 1]
        ing = [{"item": f"mjau:{ident(namn, forra)}"}] + \
              [{"item": n["upp"]} for _ in range(n["antal"])]
        json.dump({"format_version": "1.20.10", "minecraft:recipe_shapeless": {
            "description": {"identifier": f"mjau:{ident(namn, niv)}"},
            "tags": ["crafting_table"],
            "ingredients": ing,
            "unlock": [{"item": n["upp"]}],
            "result": {"item": f"mjau:{ident(namn, niv)}"}}},
            open(f"{BP}/recipes/{ident(namn, niv)}.json", "w"), indent=2)
        return
    json.dump({"format_version": "1.20.10", "minecraft:recipe_shaped": {
        "description": {"identifier": f"mjau:{namn}"},
        "tags": ["crafting_table"],
        "pattern": MONSTER[namn],
        "key": {"L": {"item": "minecraft:leather"}, "W": {"item": "minecraft:white_wool"}},
        # UNLOCK KRÄVS sedan format 1.20: utan den vägrar servern receptet med
        # "1.20+ Recipes require unlock data" — och receptet finns då helt
        # enkelt inte i spelet, fast filen ligger på plats och JSON:en är giltig.
        # Fångades av innehållsloggen, inte av någon av de statiska kollarna.
        "unlock": [{"item": "minecraft:leather"}],
        "result": {"item": f"mjau:{namn}"}}},
        open(f"{BP}/recipes/{namn}.json", "w"), indent=2)


def forhandsbild():
    """publish/06-kattdrakt.png — hela dräkten monterad, en kolumn per nivå,
    med ikonerna under.

    Delarna renderas var för sig (varje plagg har egen textur) men med SAMMA
    kamera och samma ram, så de landar på rätt plats i förhållande till
    varandra och kan läggas ovanpå varandra. Bakgrunden nycklas bort.

    KUBERNA FÅR INTE SKALAS: renderaren räknar texturytorna ur kubens mått, så
    en nedskalad kub läser fel del av bilden — det gav ett ansiktslöst huvud i
    en tidigare förhandsbild fast texturen var rätt. Ramen vidgas i stället.
    """
    import render_preview as rp
    RAM = ((-10, 10), (0, 38), (-10, 10))       # spelarens hela höjd
    RUTA = 260
    K, N = 3, 16
    kolumner = []
    for niv in NIVAORDNING:
        lager = None
        for namn in PLAGG:
            g = json.load(open(f"{RP}/models/entity/mjau_{namn}.geo.json"))["minecraft:geometry"][0]
            ben = []
            for b in g["bones"]:
                kub = []
                for c in b["cubes"]:
                    # INFLATE SLÄNGS, den kompenseras INTE genom att kuben görs
                    # större. Minecraft blåser upp lådan utan att röra UV:n,
                    # men vår renderare räknar texturytan ur kubens MÅTT — en
                    # kub som gjorts 10 bred läser ett 10 px brett fönster ur
                    # en textur som ritats för 8. Ansiktet hamnade då ur led
                    # och rapporterades som "ögonen sitter snett", fast bilden
                    # på disk var spegelsymmetrisk. En enhets skillnad i
                    # tjocklek syns ändå inte i en förhandsbild.
                    k = dict(c)
                    k.pop("inflate", None)
                    kub.append(k)
                ben.append((b["name"], b["pivot"], kub))
            rr.bones_for = lambda acc, _l=ben: _l
            vy = rr.render(f"mjau_{ident(namn, niv)}", [], {}, W=RUTA, H=RUTA,
                           yaw=22, pitch=6, ram=RAM)
            if lager is None:
                lager = [list(r) for r in vy]
                bg = vy[0][0]
            else:
                for y in range(RUTA):
                    for x in range(RUTA):
                        p2 = vy[y][x]
                        if p2 != bg:
                            lager[y][x] = p2
        kolumner.append(lager)

    bred, hojd = len(kolumner) * RUTA, RUTA + N * K + 20
    ark = [[(24, 27, 36, 255)] * bred for _ in range(hojd)]
    for ci, kol in enumerate(kolumner):
        for y in range(RUTA):
            for x in range(RUTA):
                ark[y][ci * RUTA + x] = kol[y][x]
        for pi, namn in enumerate(PLAGG):
            w, h, px = rr.read_png(f"{RP}/textures/items/pc_{ident(namn, NIVAORDNING[ci])}.png")
            ox = ci * RUTA + 12 + pi * (N * K + 8)
            for y in range(h):
                for x in range(w):
                    q = px[y][x]
                    if len(q) > 3 and q[3] == 0:
                        continue
                    for dy in range(K):
                        for dx in range(K):
                            ark[RUTA + 10 + y * K + dy][ox + x * K + dx] = (q[0], q[1], q[2], 255)
    rr.write_png(f"{BASE}/publish/06-kattdrakt.png", bred, hojd, ark)
    print(f"  publish/06-kattdrakt.png ({bred}x{hojd}) — läder, järn, diamant, netherit")


if __name__ == "__main__":
    os.makedirs(f"{RP}/attachables", exist_ok=True)
    it = json.load(open(f"{RP}/textures/item_texture.json"))
    for namn, cfg in PLAGG.items():
        ben, kuber = geometri(namn, cfg)          # geometrin delas av alla nivåer
        for niv in NIVAORDNING:
            textur(namn, cfg, niv)
            attachable(namn, cfg, niv)
            ikon(namn, cfg, niv)
            foremal(namn, cfg, niv)
            i = ident(namn, niv)
            it["texture_data"][f"pc_{i}"] = {"textures": f"textures/items/pc_{i}"}
        print(f"  {cfg['namn']:14} {cfg['slot']:18} "
              f"skydd {cfg['skydd']}-{cfg['skydd'] + NIVAER['netherit']['skydd']}  "
              f"{ben} ben, {kuber} kuber, {len(NIVAORDNING)} nivåer")
    json.dump(it, open(f"{RP}/textures/item_texture.json", "w"), indent=2)
    print("  item_texture.json uppdaterad")
    forhandsbild()
