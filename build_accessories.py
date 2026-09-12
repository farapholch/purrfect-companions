#!/usr/bin/env python3
"""Genererar ALLA tillbehör till Mjau Mods från en enda definition nedan.

Lägg till ett nytt plagg genom att lägga till en post i ACC — skriptet skapar
geometri, textur, render controller, entity-property, event, interaktion,
föremål, ikon, recept och språksträng. Kör sedan `purrfect-test`.

Varje plagg är en EGEN liten geometri (inte inbakad i kattmodellen) — annars
exploderar antalet kombinationer. Läget styrs av entity properties, så alla
plagg är oberoende av varandra.
"""
import copy, json, shutil, zlib, struct, glob, os

BASE = "/opt/purrfect-companions"; BP = f"{BASE}/PurrfectCompanions_BP"; RP = f"{BASE}/PurrfectCompanions_RP"

# DE VANLIGA KATTERNA — de som spawnar naturligt, har spawnägg och ska ha
# plaggens UV-ytor inmålade i sin päls. De hemliga (midnight, aurora, nova) och
# spökkatten står MEDVETET inte här: de har inga spawnägg och ska inte dyka upp
# i föremålslistan. Listan låg tidigare hårdkodad på tre ställen, och när
# Ginger och Domino tillkom raderade ikonstädningen deras spawnägg vid varje
# bygge — en gång per ställe man glömde.
KATTER = ("misty", "hazel", "mocha", "snow", "ginger", "domino")

# Personligheter påverkar bara redan existerande beteenden. Det håller
# skillnaderna märkbara i spelet utan en separat tick-loop per katt.
PERSONLIGHETER = {
    "misty":  {"namn": "Curious", "stroll": 1.12, "hunt": 14, "sit": 0.20, "gift": 0.82},
    "hazel":  {"namn": "Social", "stroll": 1.00, "hunt": 10, "sit": 0.28, "gift": 0.76},
    "mocha":  {"namn": "Sleepy", "stroll": 0.86, "hunt": 8,  "sit": 0.46, "gift": 0.68},
    "snow":   {"namn": "Brave", "stroll": 1.06, "hunt": 16, "sit": 0.18, "gift": 0.78},
    "ginger": {"namn": "Hunter", "stroll": 1.08, "hunt": 20, "sit": 0.14, "gift": 0.72},
    "domino": {"namn": "Playful", "stroll": 1.16, "hunt": 11, "sit": 0.24, "gift": 0.74},
}

# Alla som har ett spawnägg att skydda mot ikonstädningen. Vakthunden är ingen
# katt (ingen päls att måla plagg i), men hennes ikon rensas bort av samma glob
# om hon inte står med här. De hemliga katterna står här av samma skäl — de
# saknade spawn_egg helt och syntes som fyra svarta standardägg i hotbaren
# (Xbox-bild). Ett ansikte avslöjar ingen ritual; de låg redan i kreativlistan.
SPAWNAGG = KATTER + ("vakthund", "midnight", "aurora", "nova", "spokkatt")
TEX = 256
# PÄLSEN HAR ETT EGET ARK sedan 3.40.0: geometry.katt deklarerar PALS uv-enheter
# och tools/make_cat_pals.py skriver <katt>_pals.png i SKALA gånger det, så
# katten ritas i fyra texlar per modellenhet. Plaggen bor kvar i 256-atlaset
# (TEX) — de är egna geometrier med egen render controller. Bedrock läser en PNG
# som är större än det deklarerade tätare; det är så alla HD-paket fungerar.
PALS = (128, 32)

# ---------------------------------------------------------------- definition
# uv: startpunkt i texturen. cubes: (origin, size, uv-offset från plaggets uv)
# EN KRAFT PER PLAGG, och tabellen står på EN plats. Entiteterna får sin
# komponentgrupp härifrån och Kattboken sin text — skrivs den av på två ställen
# lovar boken förr eller senare en kraft plagget inte ger.
#
# SPRÅKNYCKLARNA ÄR VANILJAS EGNA, verifierade mot motorns en_US.lang: prefixet
# är "potion.", inte "effect.", och hoppkraften heter potion.jump och inte
# potion.jumpBoost. Med vaniljas nycklar står effektnamnen översatta på varje
# språk spelet stödjer utan att paketet översätter en enda rad.
# PLAGG DÄR NAMNET INTE RÄCKER. En keps är en keps: namn + färger + effekt är
# hela sanningen, och en rad som säger "A cap." är fjorton tecken utfyllnad på en
# sida som redan är lång. Bara de plagg som GÖR något namnet inte avslöjar får en
# mening — att sadeln betyder ridning, att ryggsäcken har femton fack.
#
# Grinden i purrfect-test kräver en språknyckel för dem som står här, så ett nytt
# plagg tvingar fram ett beslut i stället för att tyst hamna i fel hög.
_BOKPROSA = {"sadel", "ryggsack", "vagn", "halsband", "vingar", "rustning", "energisvard",
             "gruvlampa", "regnrock", "rymdmantel", "krona", "doktorsrock", "totem"}

# FORMAT: (komponentgrupp, effekter, språknyckel). Effekter är antingen ett
# effekt-id (styrka 0) eller en lista av (id, styrka) — vingarna och
# fladdermusvingarna ger två saker på en gång. Boken visar namnet på den första.
_EXTRA_POWERS = {
    "keps":        ("mjau:kepskraft",       "jump_boost",      "potion.jump"),
    "halsduk":     ("mjau:halsdukvarme",    "fire_resistance", "potion.fireResistance"),
    "glasogon":    ("mjau:glasogonskarpa",  "resistance",      "potion.resistance"),
    "tossor":      ("mjau:tossorfart",      "speed",           "potion.moveSpeed"),
    "halsband":    ("mjau:halsbandssken",   "absorption",      "potion.absorption"),
    "rosett":      ("mjau:rosettmod",       "strength",        "potion.damageBoost"),
    "horn":        ("mjau:hornsvavning",    "slow_falling",    "potion.slowFalling"),
    "haxhatt":     ("mjau:haxbrygd",        "water_breathing", "potion.waterBreathing"),
    "energisvard": ("mjau:bladsken",        "night_vision",    "potion.nightVision"),
    "tomteluva":   ("mjau:tomtegava",       "health_boost",    "potion.healthBoost"),
    "flytvast":    ("mjau:flytvastkraft",   "conduit_power",   "potion.conduitPower"),
    # DE SEX SOM SAKNADE KRAFT (2026-09-03). Tre får effekter här; stjärnmanteln,
    # kronan och doktorsrocken får sina i main.js ("auror": glöd om natten,
    # motstånd resp. läkning till katterna runt omkring) och beskrivs i prosan.
    "vingar":      ("mjau:vingsprang",      [("jump_boost", 1)],                        "potion.jump"),
    "batvingar":   ("mjau:nattflygare",     [("night_vision", 0), ("slow_falling", 0)], "potion.nightVision"),
    "mantel":      ("mjau:mantelskold",     [("absorption", 1)],                        "potion.absorption"),
}

# UV entries below are legacy hints; layout_accessory_uvs replaces every slot
# and cube offset deterministically after reading these definitions.
ACC = {
 "sadel": dict(label="Cat Saddle", bone="body", sound="saddle", rideable=True,
   uv={1:(24,26),2:(56,26),3:(88,26)},
   colors={1:("brun",(122,79,45)),2:("svart",(58,52,48)),3:("ljus",(206,190,160))},
   names={1:"Brown",2:"Black",3:"Light"},
   cubes=[([-3.25, 9, -3], [6.5, 1, 6], (0, 0)), ([-2, 10, -3], [4, 1.2, 1], (0, 0)), ([-2.5, 10, 2], [5, 0.8, 1], (0, 0)), ([-3.6, 6.7, -0.5], [0.5, 2.4, 1.5], (0, 0)), ([3.1, 6.7, -0.5], [0.5, 2.4, 1.5], (0, 0))],
   recipe=lambda mat: dict(pattern=["LLL","S S"] if not mat else ["LLL","SDS"],
       key={"L":{"item":"minecraft:leather"},"S":{"item":"minecraft:string"}} if not mat
           else {"L":{"item":"minecraft:leather"},"S":{"item":"minecraft:string"},"D":{"item":mat}},
       unlock=[{"item":"minecraft:leather"}]+([{"item":mat}] if mat else [])),
   mats={1:None,2:"minecraft:black_dye",3:"minecraft:white_dye"}),

 "keps": dict(label="Cat Cap", bone="head", sound="armor.equip_leather",
   uv={1:(24,40),2:(56,40),3:(24,56),4:(56,56)},
   colors={1:("cyan",(0,168,214)),2:("rod",(198,62,55)),3:("gron",(76,168,84)),4:("gul",(238,196,62))},
   names={1:"Cyan",2:"Red",3:"Green",4:"Yellow"},
   cubes=[([-3, 9.8, -9.1], [6, 1.1, 4.2], (0, 0)), ([-2.5, 10.9, -8.8], [5, 0.8, 3.6], (0, 0)), ([-2.5, 9.9, -11.3], [5, 0.5, 2.5], (0, 0)), ([-0.4, 11.7, -7.3], [0.8, 0.3, 0.8], (0, 0))],
   recipe=lambda mat: dict(pattern=["WWW"," L "],
       key={"W":{"item":mat},"L":{"item":"minecraft:leather"}},
       unlock=[{"item":mat},{"item":"minecraft:leather"}]),
   mats={1:"minecraft:cyan_wool",2:"minecraft:red_wool",3:"minecraft:green_wool",4:"minecraft:yellow_wool"}),

 "halsduk": dict(label="Cat Scarf", bone="body", sound="armor.equip_leather",
   uv={1:(0,72),2:(24,72),3:(48,72),4:(72,72),5:(96,72),6:(120,72)},
   colors={1:("rod",(198,62,55)),2:("bla",(64,116,200)),3:("gron",(76,168,84)),4:("gul",(238,196,62)),
           5:("rosa",(238,138,186)),6:("lila",(134,66,186))},
   names={1:"Red",2:"Blue",3:"Green",4:"Yellow",5:"Pink",6:"Purple"},
   cubes=[([-3.5, 4.8, -5.7], [7, 1.5, 1], (0, 0)), ([-3.7, 3.3, -5.9], [1.5, 2.5, 0.7], (0, 0)), ([2, 2.8, -5.9], [1.5, 3, 0.7], (0, 0))],
   recipe=lambda mat: dict(pattern=["WW","WW"], key={"W":{"item":mat}}, unlock=[{"item":mat}]),
   mats={1:"minecraft:red_wool",2:"minecraft:blue_wool",3:"minecraft:green_wool",4:"minecraft:yellow_wool",
         5:"minecraft:pink_wool",6:"minecraft:purple_wool"}),

 "ryggsack": dict(label="Cat Backpack", bone="body", sound="armor.equip_leather",
   uv={1:(0,88),2:(24,88),3:(48,88)},
   colors={1:("brun",(122,79,45)),2:("gron",(76,140,84)),3:("bla",(64,104,168))},
   names={1:"Brown",2:"Green",3:"Blue"},
   cubes=[([-2.5, 9, 1], [5, 3.2, 3], (0, 0)), ([-2.7, 11.5, 0.8], [5.4, 0.7, 3.4], (0, 0)), ([-1.6, 9.4, 4], [3.2, 1.6, 0.6], (0, 0)), ([-3.3, 9.3, 1.4], [0.8, 1.8, 2], (0, 0)), ([2.5, 9.3, 1.4], [0.8, 1.8, 2], (0, 0)), ([-1.2, 12.2, 1.8], [0.5, 0.7, 0.5], (0, 0)), ([0.7, 12.2, 1.8], [0.5, 0.7, 0.5], (0, 0)), ([-1.2, 12.9, 1.8], [2.4, 0.4, 0.5], (0, 0))],
   recipe=lambda mat: dict(pattern=["S S","LDL","LLL"],
       key={"L":{"item":"minecraft:leather"},"S":{"item":"minecraft:string"},"D":{"item":mat}},
       unlock=[{"item":"minecraft:leather"},{"item":mat}]),
   mats={1:"minecraft:brown_dye",2:"minecraft:green_dye",3:"minecraft:blue_dye"}),

 "glasogon": dict(label="Cat Glasses", bone="head", sound="armor.equip_generic",
   uv={1:(0,100),2:(16,100),3:(32,100)},
   colors={1:("svart",(38,38,42)),2:("guld",(212,175,60)),3:("rosa",(232,130,180))},
   names={1:"Black",2:"Gold",3:"Pink"},
   cubes=[([-3.2,7.8,-9.5],[6.4,1.4,0.5],(0,0))],
   recipe=lambda mat: dict(pattern=["GDG"],
       key={"G":{"item":"minecraft:glass_pane"},"D":{"item":mat}},
       unlock=[{"item":"minecraft:glass_pane"},{"item":mat}]),
   mats={1:"minecraft:black_dye",2:"minecraft:gold_nugget",3:"minecraft:pink_dye"}),

 # fyra tossor delar samma UV-region (som benen gör i grundmodellen)
 "tossor": dict(label="Cat Booties", bone="body", sound="armor.equip_leather",
   uv={1:(0,118),2:(12,118),3:(24,118),4:(36,118)},
   colors={1:("vit",(240,240,238)),2:("svart",(52,50,56)),3:("rod",(198,62,55)),4:("gul",(238,196,62))},
   names={1:"White",2:"Black",3:"Red",4:"Yellow"},
   cubes=[([-3.2,-0.05,2.8],[2.4,1.6,2.4],(0,0)),   # bak vänster
          ([0.8,-0.05,2.8],[2.4,1.6,2.4],(0,0)),    # bak höger
          ([-3.2,-0.05,-5.2],[2.4,1.6,2.4],(0,0)),  # fram vänster
          ([0.8,-0.05,-5.2],[2.4,1.6,2.4],(0,0))],  # fram höger
   recipe=lambda mat: dict(pattern=["W W","W W"], key={"W":{"item":mat}}, unlock=[{"item":mat}]),
   mats={1:"minecraft:white_wool",2:"minecraft:black_wool",3:"minecraft:red_wool",4:"minecraft:yellow_wool"}),

 "vagn": dict(label="Cat Cart", bone="cart", sound="armor.equip_leather",
   uv={1:(0,128),2:(32,128),3:(64,128)},
   colors={1:("tra",(150,108,64)),2:("rod",(178,58,52)),3:("bla",(58,102,172))},
   names={1:"Wood",2:"Red",3:"Blue"},
   # uppskalad ~35 % efter Xbox-test ("för liten") — flaket rymmer en spelare
   cubes=[
       ([-4, 2, 8], [8, 0.75, 7], (0, 0)),
       ([-4.8, 6.3, -2.6], [0.6, 0.6, 11.3], (0, 0)),
       ([4.2, 6.3, -2.6], [0.6, 0.6, 11.3], (0, 0)),
       ([-4, 3.35, 8], [0.7, 0.65, 7], (0, 0)),
       ([-4, 5.95, 8], [0.7, 0.65, 7], (0, 0)),
       ([-4, 2.75, 8], [0.7, 3.85, 0.7], (0, 0)),
       ([-4, 2.75, 11.2], [0.7, 3.85, 0.7], (0, 0)),
       ([-4, 2.75, 14.3], [0.7, 3.85, 0.7], (0, 0)),
       ([3.3, 3.35, 8], [0.7, 0.65, 7], (0, 0)),
       ([3.3, 5.95, 8], [0.7, 0.65, 7], (0, 0)),
       ([3.3, 2.75, 8], [0.7, 3.85, 0.7], (0, 0)),
       ([3.3, 2.75, 11.2], [0.7, 3.85, 0.7], (0, 0)),
       ([3.3, 2.75, 14.3], [0.7, 3.85, 0.7], (0, 0)),
       ([-3.3, 3.35, 8], [6.6, 0.65, 0.7], (0, 0)),
       ([-3.3, 5.95, 8], [6.6, 0.65, 0.7], (0, 0)),
       ([-3.3, 3.35, 14.3], [6.6, 0.65, 0.7], (0, 0)),
       ([-3.3, 5.95, 14.3], [6.6, 0.65, 0.7], (0, 0)),
       ([-3.3, 6.35, 11.15], [6.6, 0.65, 1.6], (0, 0)),
       ([-4.9, 1, 10], [1, 2, 4], (0, 0)),
       ([-4.9, 0, 11], [1, 1, 2], (0, 0)),
       ([-4.9, 3, 11], [1, 1, 2], (0, 0)),
       ([3.9, 1, 10], [1, 2, 4], (0, 0)),
       ([3.9, 0, 11], [1, 1, 2], (0, 0)),
       ([3.9, 3, 11], [1, 1, 2], (0, 0)),
       ([-4.8, 6.0, 8.0], [1.5, 0.6, 0.7], (0, 0)),
       ([3.3, 6.0, 8.0], [1.5, 0.6, 0.7], (0, 0)),
       # A body-following girth and breast strap; shafts meet the side pads.
       ([-3.3, 9.02, -2.9], [6.6, 0.38, 1.1], (0, 0)),
       ([-3.3, 3.65, -2.9], [6.6, 0.38, 1.1], (0, 0)),
       ([-3.4, 3.65, -2.9], [0.4, 5.75, 1.1], (0, 0)),
       ([3.0, 3.65, -2.9], [0.4, 5.75, 1.1], (0, 0)),
       ([-3.4, 6.0, -5.35], [6.8, 1.0, 0.4], (0, 0)),
       ([-3.4, 6.0, -5.0], [0.4, 1.0, 2.1], (0, 0)),
       ([3.0, 6.0, -5.0], [0.4, 1.0, 2.1], (0, 0)),
       ([-3.65, 6.0, -2.9], [0.65, 1.2, 1.1], (0, 0)),
       ([3.0, 6.0, -2.9], [0.65, 1.2, 1.1], (0, 0)),
       ([-4.8, 6.3, -2.6], [1.8, 0.6, 0.6], (0, 0)),
       ([3.0, 6.3, -2.6], [1.8, 0.6, 0.6], (0, 0)),
   ], harness_cubes=11,
   # seat 0 = I VAGNEN (styr som en släde), seat 1 = på ryggen. Xbox-testet:
   # med ryggen som seat 0 gick vagnen aldrig att sitta i — ensam spelare får
   # alltid första lediga sätet.
   seats=[[0.0,0.55,0.72],[0.0,0.562,-0.22]],
   recipe=lambda mat: dict(pattern=["S S","PPP","W W"],
       key={"P":{"item":mat},"S":{"item":"minecraft:stick"},"W":{"item":"minecraft:wooden_slab"}},
       unlock=[{"item":mat},{"item":"minecraft:stick"}]),
   mats={1:"minecraft:oak_planks",2:"minecraft:red_terracotta",3:"minecraft:blue_terracotta"}),

 "halsband": dict(label="Cat Collar", bone="body", sound="armor.equip_leather",
   uv={1:(0,176),2:(24,176),3:(48,176)},
   colors={1:("red",(196,58,52)),2:("blue",(58,102,178)),3:("green",(72,158,80))},
   names={1:"Red",2:"Blue",3:"Green"},
   cubes=[([-3.4, 4.9, -5.6], [6.8, 1, 1], (0, 0)), ([-0.5, 4, -5.9], [1, 1, 1], (0, 0))],
   recipe=lambda mat: dict(pattern=["LLL"," I "],
       key={"L":{"item":mat},"I":{"item":"minecraft:iron_nugget"}},
       unlock=[{"item":mat},{"item":"minecraft:iron_nugget"}]),
   mats={1:"minecraft:red_wool",2:"minecraft:blue_wool",3:"minecraft:green_wool"}),

 "rosett": dict(label="Cat Bow", bone="head", sound="armor.equip_leather",
   uv={1:(0,186),2:(16,186),3:(32,186),4:(48,186)},
   colors={1:("pink",(238,138,186)),2:("red",(198,62,55)),3:("blue",(64,116,200)),4:("yellow",(238,196,62))},
   names={1:"Pink",2:"Red",3:"Blue",4:"Yellow"},
   cubes=[([-1.9, 11.7, -7.6], [1.5, 1.7, 0.7], (0, 0)), ([0.4, 11.7, -7.6], [1.5, 1.7, 0.7], (0, 0)), ([-0.5, 12, -7.8], [1, 1.1, 1], (0, 0)), ([-1.3, 11.1, -7.5], [0.7, 1, 0.5], (0, 0)), ([0.6, 11.1, -7.5], [0.7, 1, 0.5], (0, 0))],
   recipe=lambda mat: dict(pattern=["WWW"], key={"W":{"item":mat}}, unlock=[{"item":mat}]),
   mats={1:"minecraft:pink_wool",2:"minecraft:red_wool",3:"minecraft:blue_wool",4:"minecraft:yellow_wool"}),

 "vingar": dict(label="Cat Wings", bone="body", sound="armor.equip_leather",
   uv={1:(0,192),2:(20,192),3:(40,192)},
   colors={1:("white",(242,242,240)),2:("black",(48,46,54)),3:("gold",(226,190,84))},
   names={1:"White",2:"Black",3:"Gold"},
   cubes=[([-4.5, 8, 0], [0.7, 4, 2], (0, 0)), ([3.8, 8, 0], [0.7, 4, 2], (0, 0)), ([-4.7, 8.4, 2], [0.6, 4.3, 1.2], (0, 0)), ([4.1, 8.4, 2], [0.6, 4.3, 1.2], (0, 0)), ([-4.9, 8.7, 3.2], [0.5, 3.7, 1], (0, 0)), ([4.4, 8.7, 3.2], [0.5, 3.7, 1], (0, 0)), ([-5.1, 9, 4.2], [0.4, 2.7, 0.8], (0, 0)), ([4.7, 9, 4.2], [0.4, 2.7, 0.8], (0, 0))],
   recipe=lambda mat: dict(pattern=["F F","FWF"],
       key={"F":{"item":"minecraft:feather"},"W":{"item":mat}},
       unlock=[{"item":"minecraft:feather"},{"item":mat}]),
   mats={1:"minecraft:white_wool",2:"minecraft:black_wool",3:"minecraft:gold_ingot"}),

 "horn": dict(label="Unicorn Horn", bone="head", sound="armor.equip_generic",
   uv={1:(96,128),2:(112,128),3:(128,128)},
   colors={1:("vit",(244,240,232)),2:("guld",(238,198,72)),3:("rosa",(238,150,196))},
   names={1:"White",2:"Gold",3:"Pink"},
   # avsmalnande spira mitt i pannan — enhörningskatt (kombinera med vingarna!)
   cubes=[([-0.6,11.5,-7.1],[1.2,1.6,1.2],(0,0)),
          ([-0.45,13.1,-6.95],[0.9,1.4,0.9],(0,4)),
          ([-0.3,14.5,-6.8],[0.6,1.3,0.6],(0,8))],
   recipe=lambda mat: dict(pattern=["N","I","M"],
       key={"N":{"item":"minecraft:gold_nugget"},"I":{"item":mat},
            "M":{"item":"minecraft:bone"}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:quartz",2:"minecraft:gold_ingot",3:"minecraft:amethyst_shard"}),

 "rustning": dict(label="Cat Armor", bone="body", sound="armor.equip_iron",
   uv={1:(0,224),2:(64,224),3:(128,224),4:(192,224)},
   colors={1:("jarn",(202,206,212)),2:("guld",(238,198,72)),
           3:("diamant",(108,220,214)),4:("netherit",(72,64,70))},
   names={1:"Iron",2:"Gold",3:"Diamond",4:"Netherite"},
   # ryggplåt + sidoplåtar + nackskydd, som hästrustning
   cubes=[
       ([-3.25, 8.95, -4.7], [6.5, 0.35, 1.2], (0, 0)),
       ([-3.25, 8.95, 3.7], [6.5, 0.35, 1.1], (0, 0)),
       ([-3.65, 6.3, -4.3], [0.55, 2.7, 2.2], (0, 0)),
       ([-3.65, 5.7, -1.85], [0.55, 3.15, 3.7], (0, 0)),
       ([-3.65, 6.3, 2.1], [0.55, 2.7, 2.3], (0, 0)),
       ([3.1, 6.3, -4.3], [0.55, 2.7, 2.2], (0, 0)),
       ([3.1, 5.7, -1.85], [0.55, 3.15, 3.7], (0, 0)),
       ([3.1, 6.3, 2.1], [0.55, 2.7, 2.3], (0, 0)),
       ([-2.3, 5.6, -5.35], [4.6, 1.5, 0.35], (0, 0)),
   ],
   recipe=lambda mat: dict(pattern=["I I","III","I I"],
       key={"I":{"item":mat}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:iron_ingot",2:"minecraft:gold_ingot",
         3:"minecraft:diamond",4:"minecraft:netherite_ingot"}),

 "haxhatt": dict(label="Witch Hat", bone="head", sound="armor.equip_leather",
   uv={1:(176,30),2:(216,30)},
   colors={1:("svart",(38,34,44)),2:("lila",(96,56,140))},
   names={1:"Black",2:"Purple"},
   cubes=[([-3, 10.9, -8.5], [6, 0.8, 6], (0, 0)), ([-1.8, 11.7, -7.3], [3.6, 2.2, 3.6], (0, 0)), ([-0.8, 13.9, -6.4], [2, 1.5, 2], (0, 0)), ([0.2, 15.4, -6.1], [1.4, 0.8, 1.4], (0, 0))],
   recipe=lambda mat: dict(pattern=[" W ","WWW"],
       key={"W":{"item":mat}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:black_wool",2:"minecraft:purple_wool"}),

 "tomteluva": dict(label="Santa Hat", bone="head", sound="armor.equip_leather",
   uv={1:(176,60),2:(216,60)},
   colors={1:("rod",(196,44,44)),2:("gron",(46,128,62))},
   names={1:"Red",2:"Green"},
   cubes=[([-2.6, 10.8, -8.1], [5.2, 1, 5.2], (0, 0)), ([-1.8, 11.8, -7.3], [3.6, 2.4, 3.6], (0, 0)), ([0.5, 13.9, -6.6], [1.8, 1.2, 1.8], (0, 0)), ([1.8, 13.2, -6.6], [1.4, 1.4, 1.4], (0, 0))],
   recipe=lambda mat: dict(pattern=[" S ","WWW"],
       key={"W":{"item":mat},"S":{"item":"minecraft:snowball"}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:red_wool",2:"minecraft:green_wool"}),

 "doktorsrock": dict(label="Doctor Coat", bone="body", sound="armor.equip_leather",
   uv={1:(176,90)},
   colors={1:("vit",(238,240,242))},
   names={1:"White"},
   cubes=[
       ([-3.15, 9.02, -4.55], [6.3, 0.25, 1.1], (0, 0)),
       ([-3.15, 9.02, 4.65], [6.3, 0.25, 0.35], (0, 0)),
       ([-3.3, 6.2, -4.55], [0.3, 2.9, 2.15], (0, 0)),
       ([-3.3, 5.65, -2.25], [0.3, 3.45, 4.45], (0, 0)),
       ([-3.3, 5.5, 2.4], [0.3, 3.6, 2.2], (0, 0)),
       ([3.0, 6.2, -4.55], [0.3, 2.9, 2.15], (0, 0)),
       ([3.0, 5.65, -2.25], [0.3, 3.45, 4.45], (0, 0)),
       ([3.0, 5.5, 2.4], [0.3, 3.6, 2.2], (0, 0)),
       ([-3.55, 5.6, -0.7], [0.25, 1.15, 1.8], (0, 0)),
       ([3.3, 5.6, -0.7], [0.25, 1.15, 1.8], (0, 0)),
       ([-2.9, 6.3, -5.15], [1.1, 2.3, 0.3], (0, 0)),
       ([1.8, 6.3, -5.15], [1.1, 2.3, 0.3], (0, 0)),
   ],
   recipe=lambda mat: dict(pattern=["W W","WWW","W W"],
       key={"W":{"item":mat}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:white_wool"}),

 "batvingar": dict(label="Bat Wings", bone="body", sound="armor.equip_leather",
   uv={1:(176,110),2:(216,110)},
   colors={1:("svart",(30,28,34)),2:("lila",(74,44,104))},
   names={1:"Black",2:"Purple"},
   cubes=[([-6, 8.6, -1], [2.5, 0.5, 5], (0, 0)), ([3.5, 8.6, -1], [2.5, 0.5, 5], (0, 0)), ([-8, 8.9, -0.5], [2, 0.5, 3.8], (0, 0)), ([6, 8.9, -0.5], [2, 0.5, 3.8], (0, 0)), ([-9.5, 9.2, 0], [1.5, 0.4, 2], (0, 0)), ([8, 9.2, 0], [1.5, 0.4, 2], (0, 0)), ([-9.6, 9.3, 0], [0.6, 1.2, 0.6], (0, 0)), ([9, 9.3, 0], [0.6, 1.2, 0.6], (0, 0))],
   recipe=lambda mat: dict(pattern=["L L","LLL"],
       key={"L":{"item":mat}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:leather",2:"minecraft:phantom_membrane"}),

 "krona": dict(label="Cat Crown", bone="head", sound="armor.equip_generic",
   uv={1:(0,206),2:(24,206)},
   colors={1:("gold",(232,196,72)),2:("silver",(206,210,216))},
   names={1:"Gold",2:"Silver"},
   cubes=[([-2.5,11.6,-8.4],[5,1.6,3.4],(0,0))],
   recipe=lambda mat: dict(pattern=["GEG","GGG"],
       key={"G":{"item":mat},"E":{"item":"minecraft:emerald"}},
       unlock=[{"item":mat},{"item":"minecraft:emerald"}]),
   mats={1:"minecraft:gold_ingot",2:"minecraft:iron_ingot"}),

 "mantel": dict(label="Cat Cape", bone="body", sound="armor.equip_leather",
   uv={1:(0,150),2:(40,150),3:(80,150),4:(120,150)},
   colors={1:("rod",(178,48,44)),2:("bla",(56,96,178)),3:("lila",(122,64,178)),4:("svart",(44,42,48))},
   names={1:"Red",2:"Blue",3:"Purple",4:"Black"},
   cubes=[
       ([-3.95, 9.45, -4.85], [7.9, 0.35, 1.2], (0, 0)),
       ([-4.05, 8.05, -3.65], [0.35, 1.75, 8.7], (0, 0)),
       ([3.7, 8.05, -3.65], [0.35, 1.75, 8.7], (0, 0)),
       ([-3.7, 4.6, 5.2], [1.6, 4.9, 0.3], (0, 0)),
       ([-2.25, 3.95, 5.45], [1.6, 5.55, 0.3], (0, 0)),
       ([0.65, 3.95, 5.45], [1.6, 5.55, 0.3], (0, 0)),
       ([2.1, 4.6, 5.2], [1.6, 4.9, 0.3], (0, 0)),
   ],        # hängande bakstycke
   recipe=lambda mat: dict(pattern=["S S","WWW","WWW"],
       key={"W":{"item":mat},"S":{"item":"minecraft:string"}},
       unlock=[{"item":mat},{"item":"minecraft:string"}]),
   mats={1:"minecraft:red_wool",2:"minecraft:blue_wool",3:"minecraft:purple_wool",4:"minecraft:black_wool"}),

 # RYMDTEMAT (speltest-önskemål). Medvetet EGNA namn och former, inte lånade
 # från någon film: projektet ligger publikt på CurseForge och ska inte luta
 # sig mot någon annans varumärke. UV-slottarna ligger i det enda helt fria
 # texturbandet (v211-223) — kolliderande UV ger sönderrenderade plagg.
 "energisvard": dict(label="Energy Blade", bone="body", sound="armor.equip_netherite",
   # riktigt vapen i handen, inte bara ett plagg — 8 skada ligger mellan
   # diamant (7) och netherit (8), och 800 hållbarhet är i netheritklass
   weapon=dict(damage=8, durability=800),
   uv={1:(0,211),2:(20,211),3:(40,211),4:(60,211)},
   colors={1:("bla",(96,180,255)),2:("gron",(120,240,140)),
           3:("rod",(255,90,80)),4:("lila",(190,120,255))},
   names={1:"Blue",2:"Green",3:"Red",4:"Purple"},
   # SILUETTEN ska läsa som ett svärd även i en enda färg (målaren ger hela
   # plagget samma kulör): smalt blad, tydlig parerstång, avsmalnande spets.
   # Första versionen var en enkel stolpe och såg ut som ett rör.
   # UV-avtrycken läggs sida vid sida och ryms i det fria bandet v211-223.
   cubes=[([2.6,5.6,-4.6],[1,2,1],(0,0)),          # grepp vid framtassen
          ([1.6,7.6,-4.6],[3,0.8,1],(5,0)),        # parerstång
          ([2.7,8.4,-4.45],[0.8,7,0.7],(14,0)),    # blad framför kroppen
          ([2.85,15.4,-4.38],[0.5,1.2,0.45],(18,0))], # spets
   recipe=lambda mat: dict(pattern=["G","G","I"],
       key={"G":{"item":mat},"I":{"item":"minecraft:iron_ingot"}},
       unlock=[{"item":mat},{"item":"minecraft:iron_ingot"}]),
   mats={1:"minecraft:lapis_lazuli",2:"minecraft:emerald",
         3:"minecraft:redstone",4:"minecraft:amethyst_shard"}),

 "rymdmantel": dict(label="Star Cloak", bone="body", sound="armor.equip_leather",
   uv={1:(88,211),2:(120,211)},
   colors={1:("stjarna",(110,150,235)),2:("tomrum",(38,34,58))},
   names={1:"Starlight",2:"Void"},
   cubes=[
       ([-3.95, 9.45, -4.85], [7.9, 0.35, 1.2], (0, 0)),
       ([-4.05, 8.05, -3.65], [0.35, 1.75, 8.7], (0, 0)),
       ([3.7, 8.05, -3.65], [0.35, 1.75, 8.7], (0, 0)),
       ([-3.7, 4.6, 5.2], [1.6, 4.9, 0.3], (0, 0)),
       ([-2.25, 3.95, 5.45], [1.6, 5.55, 0.3], (0, 0)),
       ([0.65, 3.95, 5.45], [1.6, 5.55, 0.3], (0, 0)),
       ([2.1, 4.6, 5.2], [1.6, 4.9, 0.3], (0, 0)),
   ],
   recipe=lambda mat: dict(pattern=["S S","WWW","WGW"],
       key={"W":{"item":mat},"S":{"item":"minecraft:string"},
            "G":{"item":"minecraft:glowstone_dust"}},
       unlock=[{"item":mat},{"item":"minecraft:glowstone_dust"}]),
   mats={1:"minecraft:light_blue_wool",2:"minecraft:black_wool"}),

 # TRE PLAGG TILL (2026-09-02, "bygg alla"). Band v0-25 i arket blev ledigt
 # när katten flyttade till sitt eget pälsark; regnrocken bor i det lediga
 # högra fältet v176-210.
 "gruvlampa": dict(label="Mining Lamp", bone="head", sound="armor.equip_generic",
   # LJUSET sköts av skriptet (main.js, "gruvlampa"): Bedrock har inget ljus
   # per entitet, så lampan sätter ett osynligt ljusblock i luften vid huvudet.
   uv={1:(0,0),2:(24,0)},
   colors={1:("massing",(214,170,70)),2:("jarn",(150,152,160))},
   names={1:"Brass",2:"Iron"},
   cubes=[([-3.3,10.0,-9.1],[6.6,0.7,4.6],(0,0)),     # remmen över hjässan
          ([-1.0,9.35,-10.3],[2.0,1.4,1.3],(0,6))],     # lampan i pannan, ovanför ögonen
   recipe=lambda mat: dict(pattern=[" G ","NLN"],
       key={"G":{"item":"minecraft:glowstone_dust"},"N":{"item":mat},"L":{"item":"minecraft:leather"}},
       unlock=[{"item":"minecraft:glowstone_dust"},{"item":mat}]),
   mats={1:"minecraft:gold_nugget",2:"minecraft:iron_nugget"}),

 "flytvast": dict(label="Life Vest", bone="body", sound="armor.equip_leather",
   uv={1:(48,0),2:(84,0),3:(120,0)},
   colors={1:("orange",(255,140,40)),2:("gul",(238,196,62)),3:("bla",(64,116,200))},
   names={1:"Orange",2:"Yellow",3:"Blue"},
   cubes=[([-3.7,4.6,-4.6],[0.7,3.8,8.4],(0,0)),       # sidopanel vänster
          ([3.0,4.6,-4.6],[0.7,3.8,8.4],(0,0)),        # sidopanel höger (delar uv)
          ([-3.4,5.0,-5.55],[6.8,3.2,0.6],(19,0)),     # bröststycket med spännen
          ([-3.4,8.9,-4.5],[6.8,0.5,8.2],(0,13))],     # ryggremmen
   recipe=lambda mat: dict(pattern=["L L","WWW","LWL"],
       key={"W":{"item":mat},"L":{"item":"minecraft:leather"}},
       unlock=[{"item":mat},{"item":"minecraft:leather"}]),
   mats={1:"minecraft:orange_wool",2:"minecraft:yellow_wool",3:"minecraft:blue_wool"}),

 "regnrock": dict(label="Raincoat", bone="body", sound="armor.equip_leather",
   uv={1:(72,176),2:(124,176)},
   colors={1:("gul",(238,196,62)),2:("gron",(76,168,84))},
   names={1:"Yellow",2:"Green"},
   cubes=[
       ([-3.15, 9.02, -4.55], [6.3, 0.25, 1.1], (0, 0)),
       ([-3.15, 9.02, 4.65], [6.3, 0.25, 0.35], (0, 0)),
       ([-3.3, 6.2, -4.55], [0.3, 2.9, 2.15], (0, 0)),
       ([-3.3, 5.65, -2.25], [0.3, 3.45, 4.45], (0, 0)),
       ([-3.3, 5.5, 2.4], [0.3, 3.6, 2.2], (0, 0)),
       ([3.0, 6.2, -4.55], [0.3, 2.9, 2.15], (0, 0)),
       ([3.0, 5.65, -2.25], [0.3, 3.45, 4.45], (0, 0)),
       ([3.0, 5.5, 2.4], [0.3, 3.6, 2.2], (0, 0)),
       ([-3.55, 5.6, -0.7], [0.25, 1.15, 1.8], (0, 0)),
       ([3.3, 5.6, -0.7], [0.25, 1.15, 1.8], (0, 0)),
       ([-2.9, 6.3, -5.15], [1.1, 2.3, 0.3], (0, 0)),
       ([1.8, 6.3, -5.15], [1.1, 2.3, 0.3], (0, 0)),
       ([-3.4, 8.4, -6.0], [6.8, 1.4, 1.4], (0, 0)),
   ],    # huvan, nedfälld i nacken
   recipe=lambda mat: dict(pattern=["W W","WWW","WSW"],
       key={"W":{"item":mat},"S":{"item":"minecraft:slime_ball"}},
       unlock=[{"item":mat},{"item":"minecraft:slime_ball"}]),
   mats={1:"minecraft:yellow_wool",2:"minecraft:green_wool"}),

 # KATT-TOTEM (Pelle 2026-09-03: "om man kraschar ner från himlen får man en
 # totem tydligen"). En berlock av guld och smaragd vid halsen som räddar
 # katten från döden EN gång och sedan är borta. Kraften bor i main.js
 # ("totem"): Bedrock låter inte ett paket stoppa ett dödligt slag i förväg,
 # så det är två lager — läkning när ett slag lämnar henne nära döden, och
 # återkomst på platsen om slaget ändå tog henne.
 "totem": dict(label="Cat Totem", bone="body", sound="armor.equip_generic",
   uv={1:(160,0)},
   colors={1:("guld",(238,198,72))},
   names={1:"Gold"},
   # UNDER HAKAN, inte på bröstet: huvudet (y 5-10, z -9..-5) täcker bålens
   # övre framsida, så en berlock på y 6,6-8,8 låg inuti huvudets låda och
   # syntes aldrig (renderingen 2026-09-03). Bålens synliga framsida under
   # hakan är y 4-5; berlocken hänger där och sticker ut en halv enhet.
   cubes=[([-1.0,3.8,-5.55],[2.0,1.7,0.7],(0,0)),      # berlocken under hakan
          ([-0.4,5.5,-5.45],[0.8,0.5,0.5],(6,0))],     # öglan (skyms av huvudet)
   recipe=lambda mat: dict(pattern=["GEG","EKE","GEG"],
       key={"G":{"item":"minecraft:gold_ingot"},"E":{"item":mat},"K":{"item":"mjau:godis"}},
       unlock=[{"item":mat},{"item":"mjau:godis"}]),
   mats={1:"minecraft:emerald"}),
}

# ---------------------------------------------------------------- hjälpare
def sh(c, f):
    return tuple(max(0, min(255, int(v*f))) for v in c[:3]) + (255,)

def read_png(path):
    d=open(path,'rb').read(); pos=8; idat=b''; w=h=None
    while pos<len(d):
        ln=struct.unpack(">I",d[pos:pos+4])[0]; typ=d[pos+4:pos+8]; data=d[pos+8:pos+8+ln]
        if typ==b'IHDR': w,h=struct.unpack(">II",data[:8])
        elif typ==b'IDAT': idat+=data
        pos+=12+ln
    raw=zlib.decompress(idat); px=[]; stride=w*4; prev=bytearray(stride); i=0
    for y in range(h):
        f=raw[i]; i+=1; line=bytearray(raw[i:i+stride]); i+=stride
        for x in range(stride):
            a=line[x-4] if x>=4 else 0; b=prev[x]; cc=prev[x-4] if x>=4 else 0
            if f==1: line[x]=(line[x]+a)&255
            elif f==2: line[x]=(line[x]+b)&255
            elif f==3: line[x]=(line[x]+(a+b)//2)&255
            elif f==4:
                p=a+b-cc; pa,pb,pc=abs(p-a),abs(p-b),abs(p-cc)
                line[x]=(line[x]+(a if(pa<=pb and pa<=pc) else (b if pb<=pc else cc)))&255
        prev=line; px.append([tuple(line[x*4:x*4+4]) for x in range(w)])
    return w,h,px

def write_png(p,w,h,px):
    def ch(t,d):
        c=t+d; return struct.pack(">I",len(d))+c+struct.pack(">I",zlib.crc32(c)&0xffffffff)
    raw=bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w): raw+=bytes(px[y][x])
    open(p,"wb").write(b"\x89PNG\r\n\x1a\n"+ch(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))
        +ch(b"IDAT",zlib.compress(bytes(raw),9))+ch(b"IEND",b""))

def uv_footprint(size):
    w,h,d = size
    import math
    return math.ceil(2*(d+w)), math.ceil(d+h)

def layout_accessory_uvs():
    """Pack each type locally, then its color tiles onto the shared atlas."""
    import math
    tiles = []
    for name, cfg in ACC.items():
        sizes = sorted({tuple(size) for _, size, _ in cfg["cubes"]},
                       key=lambda size: (-math.ceil(size[1]+size[2]), -math.ceil(2*(size[0]+size[2])), size))
        width = max(32, max(math.ceil(2*(size[0]+size[2]))+1 for size in sizes))
        x = y = row = used = 0
        offsets = {}
        for size in sizes:
            w, h = uv_footprint(size)
            if x+w+1 > width:
                x, y, row = 0, y+row, 0
            offsets[size] = (x,y)
            x += w+1; row = max(row,h+1); used = max(used,x)
        cfg["cubes"] = [(o,size,offsets[tuple(size)]) for o,size,_ in cfg["cubes"]]
        for variant in cfg["colors"]:
            tiles.append((used,y+row,name,variant))
    # Preserve established materials: procedural grain uses atlas coordinates.
    # New/expanded tiles are packed around these stable, reviewed anchors.
    anchors=json.load(open(f"{BASE}/tools/accessory_uv_anchors.json"))
    heights = [0]*TEX
    movable=[]
    for w,h,name,variant in tiles:
        fixed=anchors.get(name,{}).get(str(variant))
        if fixed is None:
            movable.append((w,h,name,variant)); continue
        x,y=fixed
        ACC[name]["uv"][variant]=(x,y)
        heights[x:x+w]=[max(old,y+h) for old in heights[x:x+w]]
    tiles=movable
    for w,h,name,variant in sorted(tiles,key=lambda t:(-t[1],-t[0],t[2],t[3])):
        y,x = min((max(heights[x:x+w]),x) for x in range(TEX-w+1))
        if y+h > TEX:
            raise ValueError(f"Accessory atlas overflow: {name}")
        ACC[name]["uv"][variant] = (x,y)
        heights[x:x+w] = [y+h]*w


layout_accessory_uvs()

# ---------------------------------------------------------------- geometri
def build_geometry():
    p=f"{RP}/models/entity/katt.geo.json"
    g=json.load(open(p))
    base=[x for x in g["minecraft:geometry"] if x["description"]["identifier"]=="geometry.katt"][0]
    for b in base["bones"]:
        b["cubes"]=[c for c in b.get("cubes",[]) if c["uv"][1] < 26]   # bara katten själv
    # KRITISKT: bas-geometrin måste deklarera pälsarkets UV-ENHETER (PALS), inte
    # atlasets. Missas det läses alla UV i fel skala och katten blir obegriplig i
    # spelet (tillbehören såg rätt ut eftersom de byggs om med rätt TEX varje gång).
    base["description"]["texture_width"]=PALS[0]
    base["description"]["texture_height"]=PALS[1]
    desc=lambda i:{"identifier":i,"texture_width":TEX,"texture_height":TEX,
                   "visible_bounds_width":2,"visible_bounds_height":1.5,"visible_bounds_offset":[0,0.5,0]}
    geos=[base,{"description":desc("geometry.katt.empty"),"bones":[{"name":"tom","pivot":[0,0,0]}]}]
    # Ett tillbehörsben roterar kring SIN egen pivot. Har den inte exakt samma
    # pivot som benet med samma namn i grundmodellen svänger plagget kring en
    # annan punkt än kroppsdelen och far ut vid sidan om katten när den rör sig.
    PIVOTS={b["name"]:b["pivot"] for b in base["bones"]}
    # Wheels stay on the ground when the cat lowers its body to sit/sleep.
    PIVOTS["cart"] = [0, 0, 0]
    for a,cfg in ACC.items():
        for i in cfg["colors"]:
            u,v=cfg["uv"][i]
            cubes=[{"origin":list(o),"size":list(s),"uv":[u+du,v+dv]} for o,s,(du,dv) in cfg["cubes"]]
            if a == "vagn":
                split = len(cubes)-cfg["harness_cubes"]
                bones = [{"name":"cart", "pivot":PIVOTS["cart"], "cubes":cubes[:split]},
                         {"name":"body", "pivot":PIVOTS["body"], "cubes":cubes[split:]}]
            elif a == "tossor":
                bones = [{"name": f"leg{leg}", "pivot": PIVOTS[f"leg{leg}"],
                          "cubes": [cube]} for leg, cube in enumerate(cubes)]
            else:
                bones = [{"name":cfg["bone"], "pivot":PIVOTS[cfg["bone"]], "cubes":cubes}]
            geos.append({"description":desc(f"geometry.katt.{a}{i}"), "bones":bones})
    g["minecraft:geometry"]=geos
    json.dump(g,open(p,"w"),indent=2)
    return len(geos)

# ---------------------------------------------------------------- textur
def paint_accessories():
    """Plaggens ark: ETT delat `textures/entity/plagg.png` för alla katter, i
    PLAGG_SKALA texlar per uv-enhet (TEX x TEX enheter). Materialen bor i
    tools/plaggmaterial.py — läder, ull, plåt, trä, fjädrar, glas, glöd.

    Förut målades plaggen in i varje katts egen 256-atlas som färgade
    rektanglar. De hemliga katternas atlas var dessutom härledda ur Mistys
    med pälsens färgtransform, så Midnight bar en svart sadel. Ett ark, en
    sanning."""
    import sys; sys.path.insert(0, f"{BASE}/tools")
    from plaggmaterial import mala_plagg, SKALA as PLAGG_SKALA
    from make_cat_pals import Duk
    duk = Duk(TEX * PLAGG_SKALA, TEX * PLAGG_SKALA)
    for a, cfg in ACC.items():
        for i, (slug, col) in cfg["colors"].items():
            mala_plagg(duk, a, cfg, i, col)
    write_png(f"{RP}/textures/entity/plagg.png", duk.w, duk.h, duk.px)

# ---------------------------------------------------------------- ikoner
# EN EGEN SILUETT PER PLAGGTYP. Förut hade bara glasögon, mantel, vagn och
# tossor egna former — allt annat föll ner i ett gemensamt "else" och blev en
# färgad rektangel. I inventariet såg sadel, keps, halsduk, halsband, vingar,
# krona och energisvärd därför likadana ut, och enda skillnaden mellan två
# plagg var nyansen ("det var lite svårt att se skillnader i ikonerna").
#
# Formen ska bära igenkänningen, färgen bara varianten: man ska se att det är
# en sadel innan man ser att den är brun.
def icon(a,col,path):
    S=16; T=(0,0,0,0); px=[[T]*S for _ in range(S)]
    def sp(x,y,c):
        # ALLTID fyra byte. write_png deklarerar RGBA men skriver bytes(px),
        # så en RGB-trippel ger tre byte i en rad som ska ha fyra — hela
        # bilden blir förskjuten och Minecraft ritar rutmönstret i stället.
        # sh() returnerar RGBA, men råfärgen ur ACC är RGB, och den skrevs
        # rakt in på de flesta ställen.
        if len(c) == 3: c = c + (255,)
        if 0<=x<S and 0<=y<S: px[y][x]=c
    def rect(x0,y0,x1,y1,c):
        for y in range(y0,y1+1):
            for x in range(x0,x1+1): sp(x,y,c)
    ljus, mork, djup = sh(col,1.25), sh(col,0.72), sh(col,0.55)

    if a=="glasogon":
        # Mörka glas med blå reflektion, tydlig båge och näsbrygga.
        rect(1,5,2,7,mork); rect(13,5,14,7,mork)
        rect(2,6,6,10,djup); rect(9,6,13,10,djup)
        rect(2,6,6,6,col); rect(9,6,13,6,col)
        rect(3,7,5,9,(44,79,105,255)); rect(10,7,12,9,(44,79,105,255))
        rect(7,7,8,7,col)
        for x in (3,10):
            sp(x,7,(200,239,247,255)); sp(x+1,8,(112,177,206,255))
        sp(3,10,mork); sp(10,10,mork)
    elif a=="sadel":
        # Läder sits, upphöjda ändar och två öppna stigbyglar.
        rect(2,5,13,9,djup); rect(3,6,12,8,col)
        rect(2,3,4,6,mork); rect(3,3,4,4,ljus)
        rect(11,3,13,6,mork); rect(11,3,12,4,ljus)
        rect(5,6,10,6,ljus); rect(4,9,11,10,mork)
        for x in (3,10):
            rect(x,10,x,12,djup)
            rect(x-1,12,x+2,14,(190,163,108,255))
            rect(x,12,x+1,13,T)
        for x in (4,6,8,10): sp(x,8,sh(col,1.1))
    elif a=="keps":
        # Kupad krona med söm, knapp och böjd skärm.
        rect(5,3,9,3,djup); sp(7,2,ljus)
        rect(3,5,11,9,djup); rect(4,4,10,8,col)
        rect(5,4,9,4,ljus); rect(4,5,4,8,ljus)
        rect(8,5,8,8,mork); sp(6,6,ljus)
        rect(3,9,12,10,mork); rect(7,10,14,11,djup)
        rect(8,10,13,10,col); rect(10,11,13,11,mork)
    elif a=="gruvlampa":
        rect(2,4,13,7,(63,46,34,255)); rect(3,4,12,4,(130,100,67,255))
        rect(4,5,11,11,djup); rect(5,4,10,12,mork)
        rect(5,5,10,10,col); rect(6,5,9,5,ljus)
        rect(6,6,9,10,(255,220,103,255)); rect(7,6,8,9,(255,251,214,255))
        sp(6,6,(255,255,250,255)); rect(6,11,9,11,djup)
        for x in (2,12): sp(x,6,(195,170,112,255))
    elif a=="flytvast":
        for x in (3,9):
            rect(x,3,x+3,13,djup); rect(x,4,x+2,12,col)
            rect(x,4,x,11,ljus)
            rect(x,6,x+2,6,(239,241,220,255)); rect(x,10,x+2,10,(239,241,220,255))
        rect(4,2,5,3,ljus); rect(10,2,11,3,ljus)
        for y in (7,11):
            rect(5,y,10,y,(44,43,40,255)); sp(7,y,(180,185,180,255))
        sp(3,13,T); sp(12,13,T)
    elif a=="regnrock":
        rect(5,1,10,1,mork); rect(4,2,11,4,col)
        rect(5,2,10,3,djup); rect(6,2,9,2,mork)
        rect(3,5,12,13,mork); rect(4,4,11,13,col)
        rect(2,5,3,9,col); rect(12,5,13,9,col)
        rect(4,5,4,12,ljus); rect(10,5,10,12,ljus)
        rect(7,5,7,13,djup); rect(4,13,11,14,mork)
        for y in (6,9,12): sp(8,y,(241,218,147,255))
        rect(5,10,6,10,mork); rect(9,10,10,10,mork)
        sp(11,6,(255,243,185,255))
    elif a=="totem":
        rect(6,1,9,3,djup); rect(7,2,8,3,T)
        rect(4,4,11,12,djup); rect(5,3,10,13,mork)
        rect(5,4,10,12,col); rect(5,4,5,11,ljus); rect(6,4,9,4,ljus)
        rect(6,6,9,10,(31,99,61,255)); rect(7,5,8,11,(31,99,61,255))
        rect(7,6,8,10,(57,190,108,255)); rect(6,7,9,9,(57,190,108,255))
        rect(7,6,7,8,(175,255,208,255)); sp(8,9,(32,134,79,255))
        rect(6,12,9,12,ljus)
    elif a=="halsduk":
        # Vikt tyg, rand och separata fransar.
        rect(2,4,12,7,djup); rect(3,4,11,4,ljus)
        rect(2,5,12,6,col); rect(4,6,11,6,mork)
        rect(3,7,5,12,col); rect(10,7,12,13,col)
        rect(3,7,3,11,ljus); rect(10,8,10,12,ljus)
        rect(3,10,5,10,ljus); rect(10,11,12,11,ljus)
        for x,y in ((3,13),(5,13),(10,14),(12,14)): sp(x,y,mork)
        rect(9,5,11,7,mork); sp(9,5,ljus)
    elif a=="ryggsack":
        # Bärhandtag, sidofickor, lock och separat framficka.
        rect(6,1,9,3,djup); rect(7,2,8,3,T)
        rect(4,3,11,14,djup); rect(3,5,12,12,djup)
        rect(4,4,11,12,col); rect(5,13,10,13,mork)
        rect(2,7,3,12,mork); rect(12,7,13,12,mork)
        rect(2,7,3,7,ljus); rect(12,7,13,7,ljus)
        rect(4,4,11,6,ljus); rect(5,7,10,7,mork)
        rect(5,10,10,12,mork); rect(5,9,10,9,ljus)
        rect(7,6,8,9,(91,62,43,255))
        rect(7,7,8,8,(238,197,99,255))
        sp(5,11,ljus); sp(10,11,ljus)
    elif a=="halsband":
        rect(4,3,11,4,mork); rect(4,3,10,3,ljus)
        rect(2,5,3,9,djup); rect(12,5,13,9,djup)
        rect(3,5,3,9,col); rect(12,5,12,9,col)
        rect(4,10,11,11,mork); rect(4,10,10,10,col)
        rect(10,3,12,5,(230,200,126,255)); sp(11,4,djup)
        rect(6,11,9,13,(197,143,50,255)); rect(7,11,8,11,(255,227,138,255))
        sp(7,12,(255,214,102,255)); sp(8,13,(91,66,37,255))
    elif a=="rosett":
        for y,right in ((4,3),(5,4),(6,5),(7,6),(8,6),(9,5),(10,4),(11,3)):
            rect(2,y,right,y,mork); rect(15-right,y,13,y,mork)
            if right > 3:
                rect(3,y,right,y,col); rect(15-right,y,12,y,col)
        rect(3,5,4,6,ljus); rect(11,5,12,6,ljus)
        rect(5,10,6,12,col); rect(9,10,10,12,col)
        rect(6,6,9,9,djup); rect(7,6,8,8,col); sp(7,6,ljus)
    elif a=="vingar":
        # Fjäderspetsar ger kontur; speglade vingben lämnar luft i mitten.
        for flip in (False,True):
            def feather(x,y,c): sp(15-x if flip else x,y,c)
            for y,left,right in ((2,2,2),(3,2,3),(4,1,4),(5,1,5),
                                 (6,1,6),(7,1,6),(8,2,6),(9,2,6),
                                 (10,3,6),(11,4,6),(12,5,6)):
                for x in range(left,right+1): feather(x,y,mork if x==right else col)
            for x,y in ((2,3),(2,4),(2,5),(3,6),(4,7),(5,8),(6,9)):
                feather(x,y,ljus)
            for x,y in ((1,7),(2,9),(3,11),(4,12)):
                feather(x,y,T)
            for x,y in ((2,7),(3,9),(4,10),(5,11)): feather(x,y,ljus)
    elif a=="batvingar":
        col = tuple(max(c, floor) for c, floor in zip(col, (52, 47, 63)))
        ljus, mork, djup = sh(col,1.35), sh(col,0.72), sh(col,0.55)
        # Spetsiga vingfingrar och urtag i membranets nederkant.
        for flip in (False,True):
            def wing(x,y,c): sp(15-x if flip else x,y,c)
            for y,left,right in ((2,2,2),(3,2,3),(4,1,4),(5,1,5),(6,1,6),
                                 (7,1,6),(8,1,6),(9,1,6),(10,1,6),(11,4,6),(12,6,6)):
                for x in range(left,right+1): wing(x,y,col)
            for x,y in ((2,2),(2,3),(3,4),(4,5),(5,6),(6,7),(1,5),(1,6),(1,7),(1,8),(1,9),(1,10)):
                wing(x,y,ljus)
            for x,y in ((4,6),(4,7),(4,8),(4,9),(4,10),(4,11),(6,8),(6,9),(6,10),(6,11),(6,12)):
                wing(x,y,djup)
    elif a=="horn":
        for y in range(2,13):
            half=(y-1)//3
            rect(8-half,y,8+half,y,mork)
            rect(8-half,y,7+half,y,col)
            sp(8-half,y,ljus)
            if y%3==1: rect(8-half,y,8+half,y,sh(col,0.82))
        sp(8,1,ljus); rect(4,13,11,14,djup); rect(5,13,10,13,ljus)
    elif a=="krona":
        # Guld med mörk infattning, tre spetsar och ädelstenar.
        rect(2,8,13,12,djup); rect(3,8,12,11,col)
        for x,top in ((2,4),(7,2),(12,4)):
            rect(x,top,x+1,8,mork); rect(x,top,x,7,ljus)
            sp(x,top,(255,238,169,255))
        rect(3,9,12,9,ljus); rect(3,12,12,12,ljus)
        for x,c in ((4,(69,202,183,255)),(7,(221,67,106,255)),(10,(69,202,183,255))):
            rect(x,10,x+1,11,c); sp(x,10,sh(c,1.3))
    elif a=="haxhatt":
        col = tuple(max(c, floor) for c, floor in zip(col, (52, 47, 63)))
        ljus, mork, djup = sh(col,1.35), sh(col,0.72), sh(col,0.55)
        for y,left,right in ((2,10,11),(3,8,10),(4,7,9),(5,6,9),(6,6,10),
                             (7,5,10),(8,5,11),(9,4,11),(10,4,12)):
            rect(left,y,right,y,mork); rect(left,y,right-1,y,col); sp(left,y,ljus)
        rect(4,10,11,11,(113,72,48,255))
        rect(7,10,9,12,(236,192,85,255)); sp(8,11,djup)
        rect(2,12,13,13,djup); rect(1,12,14,12,mork)
        rect(2,12,5,12,ljus); rect(4,14,11,14,djup)
    elif a=="tomteluva":
        for y,left,right in ((3,6,10),(4,5,11),(5,4,11),(6,4,10),
                             (7,3,10),(8,3,10),(9,3,11),(10,3,11)):
            rect(left,y,right,y,mork); rect(left,y,right-1,y,col); sp(left,y,ljus)
        rect(11,5,12,7,col); rect(11,7,13,9,(207,214,219,255))
        rect(11,7,12,8,(250,250,244,255))
        rect(2,11,12,13,(204,214,222,255)); rect(3,10,11,12,(246,247,238,255))
        for x in (4,7,10): sp(x,10,(255,255,255,255))
    elif a=="doktorsrock":
        rect(3,4,12,13,mork); rect(4,4,11,13,col)
        rect(2,5,3,9,col); rect(12,5,13,9,col)
        rect(6,3,9,5,(74,122,149,255)); rect(7,6,8,13,mork)
        for x,y in ((4,3),(5,4),(6,5),(11,3),(10,4),(9,5)): sp(x,y,ljus)
        rect(4,9,5,11,(181,197,204,255)); rect(4,9,5,9,ljus)
        for y in (7,10,12): sp(8,y,(100,120,130,255))
        rect(9,7,11,7,(195,61,67,255)); rect(10,6,10,8,(195,61,67,255))
        sp(3,13,T); sp(12,13,T)
    elif a=="rustning":
        rect(3,4,12,12,djup); rect(2,4,4,7,mork); rect(11,4,13,7,mork)
        rect(4,5,11,11,col); rect(6,3,9,5,T)
        rect(2,4,4,4,ljus); rect(11,4,13,4,ljus)
        rect(4,6,4,10,ljus); rect(7,6,7,11,ljus); rect(8,6,8,11,mork)
        rect(4,9,11,9,mork); rect(4,12,11,13,mork)
        for x in (4,11): sp(x,7,(240,240,230,255))
        rect(5,13,10,13,djup)
    elif a=="energisvard":
        # Diagonalt blad med vit kärna, färgad kant och separat grepp.
        for i in range(8):
            x,y=6+i,9-i
            sp(x-1,y,mork); sp(x,y,col); sp(x,y-1,ljus); sp(x+1,y-1,(244,253,255,255)); sp(x+1,y,col)
        for x,y in ((4,8),(5,9),(6,10),(7,11)): sp(x,y,(177,192,204,255)); sp(x,y+1,(72,79,91,255))
        for x,y in ((4,11),(3,12),(2,13)): sp(x,y,(65,55,62,255)); sp(x+1,y,(137,146,155,255))
        sp(2,14,(193,200,210,255))
    elif a=="rymdmantel":
        for y in range(3,14):
            left=5-(y//5); right=10+(y//5)
            rect(left,y,right,y,mork); rect(left+1,y,right-1,y,col)
            sp(left+2,y,sh(col,1.1)); sp(right-2,y,sh(col,0.78))
        rect(6,2,9,3,djup); sp(7,3,(212,222,248,255))
        for x,y in ((6,6),(10,8),(5,11),(9,12)):
            sp(x,y,(235,240,255,255))
        sp(9,5,(235,240,255,255)); sp(8,5,(156,189,255,255)); sp(9,4,(156,189,255,255))
        rect(3,14,12,14,(125,153,202,255))
    elif a=="mantel":
        for y in range(3,14):
            left=5-y//5; right=10+y//5
            rect(left,y,right,y,djup); rect(left+1,y,right-1,y,col)
            sp(left+1,y,ljus); sp(8,y,mork); sp(right-1,y,mork)
        rect(5,2,10,3,mork); rect(6,2,9,2,ljus)
        sp(7,3,(235,195,98,255)); sp(8,3,(178,129,50,255))
        rect(3,13,12,13,(193,150,72,255)); rect(4,14,11,14,djup)
    elif a=="vagn":
        rect(2,5,12,10,djup); rect(3,4,11,4,ljus)
        rect(3,5,11,6,sh(col,0.55)); rect(2,7,12,10,col)
        rect(2,7,12,7,ljus); rect(2,10,12,10,mork)
        for x in (4,7,10): rect(x,8,x,9,mork)
        rect(12,8,14,8,(92,75,51,255)); sp(14,7,(166,138,91,255))
        for wx in (4,10):
            rect(wx-1,11,wx+1,13,(51,44,41,255)); rect(wx-2,12,wx+2,12,(51,44,41,255))
            sp(wx,12,(200,166,105,255)); sp(wx-1,11,(127,104,75,255))
    elif a=="tossor":
        for bx,by in ((2,3),(9,3),(2,9),(9,9)):
            rect(bx,by+1,bx+4,by+4,djup); rect(bx+1,by,bx+3,by+3,col)
            rect(bx+1,by,bx+3,by,ljus); rect(bx,by+2,bx+3,by+3,col)
            sp(bx,by+2,ljus); rect(bx+1,by+4,bx+4,by+4,mork)
            rect(bx+2,by+1,bx+3,by+1,sh(col,0.68))
    else:
        rect(3,5,12,11,col); rect(3,5,12,5,ljus); rect(3,11,12,11,mork)
    write_png(path,S,S,px)

def icon_treat():
    """Kattgodis: liten fiskformad godbit."""
    S=16; T=(0,0,0,0); px=[[T]*S for _ in range(S)]
    BODY=(223,153,76,255); DARK=(116,72,38,255); LIGHT=(255,210,137,255)
    def sp(x,y,c):
        if 0<=x<S and 0<=y<S: px[y][x]=c
    # Rounded biscuit body, a narrow tail joint, and a broad forked fin.
    for y, (left, right) in enumerate(((4,8),(3,10),(2,11),(2,11),(2,11),(3,10),(4,8)), 4):
        for x in range(left, right + 1):
            sp(x,y,DARK if x in (left,right) or y in (4,10) else BODY)
    for x,y in ((12,6),(13,5),(14,4),(14,5),(14,6),(12,7),(13,7),
                (14,7),(12,8),(13,9),(14,8),(14,9),(14,10)):
        sp(x,y,DARK if x==14 else BODY)
    for x in range(4,8): sp(x,5,LIGHT)
    sp(4,7,DARK)
    for x,y in ((7,7),(8,8),(7,9)): sp(x,y,LIGHT)
    write_png(f"{RP}/textures/items/pc_godis.png",S,S,px)

def icon_pokal():
    """En guldpokal med två öron — det är en KATTutställning."""
    S=16; T=(0,0,0,0); px=[[T]*S for _ in range(S)]
    GULD=(226,190,96,255); LJUS=(248,226,150,255); MORK=(160,124,50,255)
    ORA_IN=(226,150,168,255)
    def rect(x0,y0,w,h,c):
        for y in range(y0,y0+h):
            for x in range(x0,x0+w):
                if 0<=x<S and 0<=y<S: px[y][x]=c
    rect(4,2,8,6,GULD); rect(4,2,8,1,LJUS)        # skålen
    rect(4,8,8,1,MORK)
    rect(5,9,6,1,GULD); rect(6,10,4,2,MORK)       # foten
    rect(4,12,8,2,GULD); rect(4,13,8,1,MORK)      # basplattan
    rect(1,3,3,1,LJUS); rect(1,4,1,3,GULD)
    rect(2,7,2,1,MORK)
    rect(12,3,3,1,LJUS); rect(14,4,1,3,GULD)
    rect(12,7,2,1,MORK)                         # open handles
    rect(3,0,2,3,GULD); rect(3,1,1,1,ORA_IN)      # kattöronen
    rect(11,0,2,3,GULD); rect(12,1,1,1,ORA_IN)
    rect(5,3,1,4,LJUS)
    rect(7,6,3,2,MORK)                         # paw medal
    rect(6,5,1,1,MORK); rect(8,4,1,1,MORK); rect(10,5,1,1,MORK)
    write_png(f"{RP}/textures/items/pc_pokal.png",S,S,px)

def icon_garnboll():
    """Ett rött garnnystan med trådmönster och en lös trådände."""
    S=16; T=(0,0,0,0); px=[[T]*S for _ in range(S)]
    GARN=(198,62,55,255); LJUS=(232,110,100,255); MORK=(140,38,34,255)
    def sp(x,y,c):
        if 0<=x<S and 0<=y<S: px[y][x]=c
    import math as _m
    for y in range(S):
        for x in range(S):
            dx,dy=x-7.5,y-8.5
            r=_m.hypot(dx,dy)
            if r>5.6: continue
            c=GARN
            if r>4.9: c=MORK
            elif ((x*2+y*3)//3)%4==0: c=LJUS          # trådvarven
            elif ((x*3-y*2)//3)%5==0: c=MORK
            elif r<2.2 and (x+y)%2==0: c=LJUS
            sp(x,y,c)
    for (x,y) in ((12,4),(13,3),(14,3),(14,2)):        # loose end stays inside the icon
        sp(x,y,GARN)
    write_png(f"{RP}/textures/items/pc_garnboll.png",S,S,px)

def icon_vissla():
    """Kattvisslan: en visselpipa med ett kattöra på — samma trick som bokens
    öra, så den syns i en full hotbar."""
    S=16; T=(0,0,0,0); px=[[T]*S for _ in range(S)]
    METALL,LJUS,MORK=(198,164,96,255),(238,214,150,255),(132,104,54,255)
    ORA,ORA_IN=(198,164,96,255),(226,150,168,255)
    def rect(x0,y0,w,h,c):
        for y in range(y0,y0+h):
            for x in range(x0,x0+w):
                if 0<=x<S and 0<=y<S: px[y][x]=c
    rect(6,5,6,9,MORK); rect(5,6,8,7,MORK)
    rect(6,6,6,6,METALL); rect(7,5,4,1,LJUS)
    rect(6,6,5,1,LJUS)
    rect(1,7,6,4,MORK); rect(1,7,6,1,LJUS)      # mouthpiece
    rect(2,8,5,2,METALL)
    rect(3,8,2,1,(61,59,52,255))                # air slot
    rect(9,8,2,2,MORK)
    rect(7,3,1,3,ORA); rect(10,3,1,3,ORA)
    rect(8,5,2,1,ORA_IN)
    rect(12,2,3,1,MORK); rect(12,3,1,3,MORK)
    rect(14,3,1,3,MORK); rect(12,6,3,1,MORK)     # closed attachment ring
    write_png(f"{RP}/textures/items/pc_vissla.png",S,S,px)

def icon_bok():
    """Bound teal handbook: gold cat emblem, page edges and a pink bookmark."""
    S=32; T=(0,0,0,0); px=[[T]*S for _ in range(S)]
    PARM=(36,140,149,255); PARM_M=(22,66,77,255); LJUS=(88,190,191,255)
    SIDA=(247,239,210,255); SIDA_M=(183,179,157,255)
    GULD=(248,211,109,255); SKUGGA=(191,139,57,255); ROSA=(229,116,154,255)
    def sp(x,y,c):
        if 0<=x<S and 0<=y<S: px[y][x]=c
    def rect(x0,y0,w,h,c):
        for y in range(y0,y0+h):
            for x in range(x0,x0+w): sp(x,y,c)
    rect(4,3,23,26,PARM_M)
    rect(6,4,22,24,PARM_M)
    rect(7,6,19,21,SIDA_M); rect(8,7,19,19,SIDA)
    for y in (21,24): rect(9,y,17,1,SIDA_M)
    rect(5,3,20,22,PARM)
    rect(5,3,20,1,LJUS); rect(24,4,1,20,LJUS)
    rect(5,4,3,20,PARM_M)                     # leather spine
    for y in (6,20): rect(5,y,3,2,GULD)
    rect(10,6,12,1,SKUGGA); rect(10,22,12,1,SKUGGA)
    rect(10,9,3,5,GULD); rect(19,9,3,5,GULD)  # pointed cat ears
    sp(10,8,GULD); sp(21,8,GULD)
    rect(10,12,12,6,GULD); rect(12,18,8,2,GULD)
    rect(12,14,2,2,PARM_M); rect(18,14,2,2,PARM_M)
    rect(15,16,2,1,SKUGGA)
    rect(9,16,3,1,SKUGGA); rect(20,16,3,1,SKUGGA)
    rect(19,25,3,6,ROSA); sp(20,30,T)         # forked ribbon below the pages
    write_png(f"{RP}/textures/items/pc_kattbok.png",S,S,px)


# ---------------------------------------------------------------- allt övrigt
def build_rest():
    # render controllers
    # Katten ritas ur pälsarket (Texture.pals), plaggen ur atlaset (Texture.default).
    rcs={"controller.render.katt":{"geometry":"Geometry.default",
         "materials":[{"*":"Material.default"}],"textures":["(q.property('mjau:mobel') == 5 || q.property('mjau:mobel') == 12) && q.modified_move_speed <= 0.02 ? Texture.sleep : Texture.pals"]}}
    for a,cfg in ACC.items():
        arr=["Geometry.empty"]+[f"Geometry.{a}{i}" for i in sorted(cfg["colors"])]
        rcs[f"controller.render.katt_{a}"]={
          "arrays":{"geometries":{f"Array.{a}":arr}},
          "geometry":f"Array.{a}[query.property('mjau:{a}')]",
          "materials":[{"*":"Material.default"}],"textures":["Texture.default"]}
    json.dump({"format_version":"1.10.0","render_controllers":rcs},
              open(f"{RP}/render_controllers/katt.render_controllers.json","w"),indent=2)

    gmap={"default":"geometry.katt","empty":"geometry.katt.empty"}
    for a,cfg in ACC.items():
        for i in cfg["colors"]: gmap[f"{a}{i}"]=f"geometry.katt.{a}{i}"
    # SÄKERHETSFIX 2026-08-13: loopen tog ALLA RP-entiteter och tvingade på dem
    # kattgeometrin — vakthunden (varg-geometri, varg-textur) renderades som en
    # katt. Bara klädbara katter ska röras; de känns igen på att deras
    # BP-motsvarighet har mjau:saddled (dvs. kan bära plagg).
    _katter=set()
    for bf in glob.glob(f"{BP}/entities/*.json"):
        be=json.load(open(bf))["minecraft:entity"]
        if "mjau:saddled" in be.get("component_groups",{}):
            _katter.add(be["description"]["identifier"])
    for f in glob.glob(f"{RP}/entity/*.json"):
        d=json.load(open(f)); desc=d["minecraft:client_entity"]["description"]
        if desc.get("identifier") not in _katter: continue   # t.ex. vakthunden
        desc["geometry"]=gmap
        # katten ur sitt pälsark, plaggen ur det delade plaggarket
        _kort=desc["identifier"].split(":")[1]
        desc["textures"]={"default":"textures/entity/plagg","pals":f"textures/entity/{_kort}_pals","sleep":f"textures/entity/{_kort}_sleep"}
        desc["render_controllers"]=["controller.render.katt"]+[f"controller.render.katt_{a}" for a in ACC]
        # animationer: gångcykel, svanssvaj, huvudet följer spelaren, hopkurad sittpose
        desc["animations"]={
            "walk":"animation.katt.walk", "look":"animation.katt.look",
            "tail":"animation.katt.tail", "sit":"animation.katt.sit",
            "ctrl":"controller.animation.katt.move"}
        desc["animations"]["sova"]="animation.katt.sova"
        desc["animations"]["korgvila"]="animation.katt.korgvila"
        for action in ("korglagg","spa","tv","scratch","window","windowlagg","fountain","tvattar_tassar"):
            desc["animations"][action]="animation.katt."+action
        desc["sound_effects"]={"purr":"mob.cat.purr"}
        desc["particle_effects"]={"hjarta":"minecraft:heart_particle"}
        desc["scripts"]={"animate":["ctrl"]}
        json.dump(d,open(f,"w"),indent=2)

    # föremål, ikoner, recept, språk
    # SÄKERHETSFIX 2026-08-13: raderade tidigare ALLA items/*.json och
    # recipes/*.json — även möblernas (kattbadd, matskal, fiskdamm ...) som
    # ägs av build_blocks.py. Ett fristående körning slog alltså ut åtta
    # orelaterade recept. Nu raderas bara det HÄR skriptet självt återskapar.
    _mina = {f"{a}_{slug}" for a, cfg in ACC.items() for slug, _ in cfg["colors"].values()} | {"godis", "kattbok"}
    for d_ in (f"{BP}/items", f"{BP}/recipes"):
        for f in glob.glob(f"{d_}/*.json"):
            if os.path.splitext(os.path.basename(f))[0] in _mina: os.remove(f)
    # STÄDA BARA DET HÄR SKRIPTET ÄGER. Regeln var tvärtom förut — "behåll en
    # lista, radera resten" — och den listan glömdes tre gånger: Gingers
    # spawnägg, vakthundens ansikte och de hemliga katternas ikoner raderades
    # alla vid nästa bygge. Nu raderas bara ikoner som HETER som ett plagg
    # skriptet självt genererar (pc_<plagg>_<färg>) och inte längre finns.
    # Kattdräktens och spawnäggens ikoner ägs av andra verktyg och lämnas ifred.
    _mina_ikoner={f"pc_{a}_{slug}" for a,cfg in ACC.items() for slug,_ in cfg["colors"].values()}
    def _mitt(k):
        return k.startswith("pc_") and k.rsplit("_",1)[0].replace("pc_","",1) in ACC
    for f in glob.glob(f"{RP}/textures/items/pc_*.png"):
        k=os.path.splitext(os.path.basename(f))[0]
        if _mitt(k) and k not in _mina_ikoner: os.remove(f)
    it=json.load(open(f"{RP}/textures/item_texture.json"))
    it["texture_data"]={k:v for k,v in it["texture_data"].items()
                        if not _mitt(k) or k in _mina_ikoner}
    lang=[]
    for a,cfg in ACC.items():
        for i,(slug,col) in cfg["colors"].items():
            ident=f"mjau:{a}_{slug}"; tex=f"pc_{a}_{slug}"
            icon(a,col,f"{RP}/textures/items/{tex}.png")
            it["texture_data"][tex]={"textures":f"textures/items/{tex}"}
            nm=f"{cfg['label']} ({cfg['names'][i]})"
            comps={"minecraft:icon":{"texture":tex},
                   "minecraft:display_name":{"value":nm},
                   "minecraft:max_stack_size":1}
            # VAPEN (speltest-önskemål: "gör så man kan slåss med svärden"):
            # plaggen är annars bara något man sätter PÅ katten. Energisvärdet
            # är dessutom ett riktigt vapen i handen — hand_equipped får det
            # att renderas som ett verktyg i stället för en platt ikon.
            # Högerklick på katten sätter det ändå på den (interact-filtret
            # läser handen), så båda användningarna funkar sida vid sida.
            if cfg.get("weapon"):
                comps["minecraft:hand_equipped"]=True
                comps["minecraft:damage"]={"value":cfg["weapon"]["damage"]}
                comps["minecraft:durability"]={"max_durability":cfg["weapon"]["durability"]}
                comps["minecraft:enchantable"]={"value":10,"slot":"sword"}
            json.dump({"format_version":"1.20.50","minecraft:item":{"description":{"identifier":ident,
              "menu_category":{"category":"equipment"}},"components":comps}},
              open(f"{BP}/items/{a}_{slug}.json","w"),indent=2)
            r=cfg["recipe"](cfg["mats"][i])
            json.dump({"format_version":"1.20.10","minecraft:recipe_shaped":{
              "description":{"identifier":ident},"tags":["crafting_table"],
              "pattern":r["pattern"],"key":r["key"],"unlock":r["unlock"],"result":{"item":ident}}},
              open(f"{BP}/recipes/{a}_{slug}.json","w"),indent=2)
            lang.append(f"item.{ident}={nm}")
    json.dump(it,open(f"{RP}/textures/item_texture.json","w"),indent=2)

    # föremål UTAN geometri (inget plagg) — t.ex. kattgodis
    icon_treat()
    it["texture_data"]["pc_godis"]={"textures":"textures/items/pc_godis"}
    json.dump({"format_version":"1.20.50","minecraft:item":{"description":{"identifier":"mjau:godis",
      "menu_category":{"category":"nature"}},"components":{"minecraft:icon":{"texture":"pc_godis"},
      "minecraft:display_name":{"value":"Cat Treat"},"minecraft:max_stack_size":16}}},
      open(f"{BP}/items/godis.json","w"),indent=2)
    json.dump({"format_version":"1.20.10","minecraft:recipe_shaped":{
      "description":{"identifier":"mjau:godis"},"tags":["crafting_table"],
      "pattern":["FW"],"key":{"F":{"item":"minecraft:cod"},"W":{"item":"minecraft:wheat"}},
      "unlock":[{"item":"minecraft:cod"}],"result":{"item":"mjau:godis","count":3}}},
      open(f"{BP}/recipes/godis.json","w"),indent=2)
    lang.append("item.mjau:godis=Cat Treat")
    # KATTBOKEN. Paketet har 96 föremål och ett tjugotal mekaniker, och en
    # spelare som installerar det kallt får ingen aning om att en sadlad katt
    # fiskar, att ryggsäckskatten gräver upp diamanter eller att dräktens
    # svagaste del avgör bonusen. Achievements berättar det EFTER att man hittat
    # saken. Boken berättar det innan.
    icon_bok()
    it["texture_data"]["pc_kattbok"]={"textures":"textures/items/pc_kattbok"}
    json.dump({"format_version":"1.20.50","minecraft:item":{"description":{"identifier":"mjau:kattbok",
      "menu_category":{"category":"items"}},"components":{"minecraft:icon":{"texture":"pc_kattbok"},
      "minecraft:display_name":{"value":"Cat Care Book"},"minecraft:max_stack_size":1}}},
      open(f"{BP}/items/kattbok.json","w"),indent=2)
    # POKALEN (3.50.0): priset ur kattutställningen. Inget recept — den enda
    # vägen dit är att ställa en välskött, välklädd katt på podiet och få 90
    # poäng. Ett föremål man inte kan tillverka är det enda som betyder något
    # i en värld där allt annat går att tillverka.
    icon_pokal()
    it["texture_data"]["pc_pokal"]={"textures":"textures/items/pc_pokal"}
    json.dump({"format_version":"1.20.50","minecraft:item":{"description":{"identifier":"mjau:pokal",
      "menu_category":{"category":"items"}},"components":{"minecraft:icon":{"texture":"pc_pokal"},
      "minecraft:display_name":{"value":"Best in Show"},"minecraft:max_stack_size":16}}},
      open(f"{BP}/items/pokal.json","w"),indent=2)
    lang.append("item.mjau:pokal=Best in Show")
    # GARNNYSTANET som FÖREMÅL (3.49.0). Blocket mjau:garnnystan finns redan
    # som möbel; det här är det kastbara. Kasta det, katten jagar, leker och
    # bär hem det — och blir glad på kuppen (humöret som hungern redan äter av).
    icon_garnboll()
    it["texture_data"]["pc_garnboll"]={"textures":"textures/items/pc_garnboll"}
    # KASTBART (3.52.0). Pelle: "ja kasta på riktigt". Att släppa nystanet
    # fungerade men kändes inte som att leka med en katt. minecraft:throwable
    # + projectile_entity ger samma kast som ett ägg; entiteten nedan lägger
    # tillbaka nystanet som föremål där den landar, och katten tar det därifrån
    # med samma mekanik som förut. do_swing_animation gör att armen svingar.
    json.dump({"format_version":"1.20.50","minecraft:item":{"description":{"identifier":"mjau:garnboll",
      "menu_category":{"category":"equipment"}},"components":{"minecraft:icon":{"texture":"pc_garnboll"},
      "minecraft:display_name":{"value":"Yarn Ball"},"minecraft:max_stack_size":16,
      "minecraft:throwable":{"do_swing_animation":True,"launch_power_scale":1.2,
                             "max_draw_duration":0.0,"max_launch_power":1.0,"min_draw_duration":0.0,
                             "scale_power_by_draw_duration":False},
      "minecraft:projectile":{"projectile_entity":"mjau:garnkast","minimum_critical_power":1.25},
      "minecraft:cooldown":{"category":"mjau_garn","duration":0.5}}}},
      open(f"{BP}/items/garnboll.json","w"),indent=2)
    # PROJEKTILEN. Ingen skada, ingen studs kvar: on_hit tar bort den och
    # skriptet lägger nystanet på marken där den slog ner (entityRemove-
    # händelsen finns inte i stabila API:n, så nedslaget speglas i loopen).
    json.dump({"format_version":"1.21.0","minecraft:entity":{
      "description":{"identifier":"mjau:garnkast","is_spawnable":False,"is_summonable":True,
                     "is_experimental":False,"runtime_identifier":"minecraft:snowball"},
      "components":{
        "minecraft:collision_box":{"width":0.25,"height":0.25},
        "minecraft:physics":{},
        "minecraft:pushable":{"is_pushable":False,"is_pushable_by_piston":False},
        "minecraft:projectile":{"angle_offset":0.0,"gravity":0.03,"power":1.2,"uncertainty_base":0.0,
                                "uncertainty_multiplier":0.0,"reflect_on_hurt":False,
                                "hit_sound":"mob.cat.purr",
                                "on_hit":{"impact_damage":{"damage":0,"knockback":False,"destroy_on_hit":True},
                                          "remove_on_hit":{}}}}}},
      open(f"{BP}/entities/garnkast.json","w"),indent=2)
    json.dump({"format_version":"1.20.10","minecraft:recipe_shapeless":{
      "description":{"identifier":"mjau:garnboll"},"tags":["crafting_table"],
      "ingredients":[{"item":"minecraft:string"},{"item":"minecraft:string"},{"item":"minecraft:string"}],
      "unlock":[{"item":"minecraft:string"}],"result":{"item":"mjau:garnboll"}}},
      open(f"{BP}/recipes/garnboll.json","w"),indent=2)
    lang.append("item.mjau:garnboll=Yarn Ball")
    # KATTVISSLAN (2026-09-06). Hundpaketet har en och den räddade den
    # vanligaste situationen: ett djur som blivit kvar tre dalar bort. Katter
    # strövar mer än hundar, och "var är katterna?" har frågats i den här
    # familjen. Avsvalningen ligger i FÖREMÅLET, inte i skriptet — spelaren ser
    # den snurra i handen och förstår varför inget händer.
    icon_vissla()
    it["texture_data"]["pc_vissla"]={"textures":"textures/items/pc_vissla"}
    json.dump({"format_version":"1.20.50","minecraft:item":{"description":{"identifier":"mjau:vissla",
      "menu_category":{"category":"equipment"}},"components":{"minecraft:icon":{"texture":"pc_vissla"},
      "minecraft:display_name":{"value":"Cat Whistle"},"minecraft:max_stack_size":1,
      "minecraft:cooldown":{"category":"mjau_vissla","duration":6.0}}}},
      open(f"{BP}/items/vissla.json","w"),indent=2)
    json.dump({"format_version":"1.20.10","minecraft:recipe_shapeless":{
      "description":{"identifier":"mjau:vissla"},"tags":["crafting_table"],
      "ingredients":[{"item":"minecraft:iron_ingot"},{"item":"minecraft:string"},{"item":"mjau:godis"}],
      "unlock":[{"item":"mjau:godis"}],"result":{"item":"mjau:vissla"}}},
      open(f"{BP}/recipes/vissla.json","w"),indent=2)
    lang.append("item.mjau:vissla=Cat Whistle")
    # Bok + kattgodis: tematiskt, och garanterat utan krock mot vaniljas rutnät
    # (godiset är vårt eget föremål). Receptgrinden i purrfect-test jämför mot
    # hela vaniljas receptlista och hade fällt en krock.
    json.dump({"format_version":"1.20.10","minecraft:recipe_shaped":{
      "description":{"identifier":"mjau:kattbok"},"tags":["crafting_table"],
      "pattern":["BG"],"key":{"B":{"item":"minecraft:book"},"G":{"item":"mjau:godis"}},
      "unlock":[{"item":"minecraft:book"}],"result":{"item":"mjau:kattbok"}}},
      open(f"{BP}/recipes/kattbok.json","w"),indent=2)
    lang.append("item.mjau:kattbok=Cat Care Book")
    # Prompten som visas när man riktar mot katten med ett plagg i handen.
    # Utan den här raden visar spelet nyckeln i klartext ("action.interact.equip").
    lang.append("action.interact.mjau_equip=Put on")
    lang.append("action.interact.mjau_play=Play")
    lang.append("action.interact.ride=Ride")          # visas när man sitter upp
    lang.append("action.interact.mount=Mount")
    # Bedrock bygger avstigningsprompten som action.hint.exit.<entity-id>; utan
    # egna nycklar visas den råa nyckeln på skärmen.
    # SÄKERHETSFIX 2026-08-13: listan var hårdkodad till de fyra grundkatterna,
    # så de hemliga (midnight, aurora) och spökkatten tappade sina hint-rader
    # varje gång generatorn kördes. Härleds nu ur BP-filerna i stället.
    for _bf in sorted(glob.glob(f"{BP}/entities/*.json")):
        _be=json.load(open(_bf))["minecraft:entity"]
        if "mjau:saddled" not in _be.get("component_groups",{}): continue
        c=_be["description"]["identifier"].split(":")[-1]
        lang.append(f"action.hint.exit.mjau:{c}=Dismount")
        lang.append(f"action.hint.exit.{c}=Dismount")
    json.dump(it,open(f"{RP}/textures/item_texture.json","w"),indent=2)  # skrivs om: godis-ikonen tillkom efter första dumpen

    # Keep authored action keyframes separate from the equipment generator.
    from furniture_animations import build as build_furniture_animations
    build_furniture_animations(RP)

    # entiteter: properties, events, interaktioner
    for f in sorted(glob.glob(f"{BP}/entities/*.json")):
        d=json.load(open(f)); e=d["minecraft:entity"]
        if "component_groups" not in e: continue   # inte en klädbar katt (t.ex. vakthund.json)
        # ...och inte heller ett FORDON. Spjutjaktaren har component_groups men
        # ingen mjau:saddled, och koden längre ner skriver rakt in i den
        # gruppen — resultatet blev KeyError så fort skeppet lades till bland
        # entiteterna. Samma klass av fel som när plaggen en gång tvingade
        # kattgeometri på vakthunden: filtret måste fråga vad entiteten ÄR.
        if "mjau:saddled" not in e["component_groups"]: continue
        g=e["component_groups"]; ev=e["events"]
        _cat = e["description"]["identifier"].split(":")[-1]
        _personlighet = PERSONLIGHETER.get(_cat)
        # STORLEKEN SKA MÄRKAS. Katterna hade alla 20 liv och träffytan 0,7 trots
        # att skalan går från 0,85 (Mocha) till 1,15 (Snow) — farten var det enda
        # som skilde dem åt. Och minecraft:scale skalar MODELLEN, inte
        # kollisionslådan: en birma var lika bred att gå in i som en ragdoll.
        # Samma fel fanns i hundpaketet och rättades där 2026-08-28.
        #
        # Båda HÄRLEDS ur skalan som redan står i mjau:adult, så det inte blir
        # en tabell till att hålla i synk. Livet avrundas till jämna tal —
        # spelet ritar hjärtan i par, och 17 liv är åtta och ett halvt hjärta.
        _skala = g.get("mjau:adult",{}).get("minecraft:scale",{}).get("value", 1.0)
        _liv = max(2, round(20 * _skala / 2) * 2)
        e["components"]["minecraft:health"]={"value":_liv,"max":_liv}
        e["components"]["minecraft:collision_box"]={
            "width": round(0.7 * _skala, 2), "height": round(0.7 * _skala, 2)}
        # client_sync ÄR NÖDVÄNDIG: utan den finns propertyn bara på servern och
        # render controllers (som körs på klienten) kan inte läsa query.property
        # → plaggen sätts på men syns aldrig. Ridning fungerade ändå, eftersom den
        # kommer från en komponentgrupp och inte från en property.
        e["description"]["properties"]={
            f"mjau:{a}": {"type":"int","range":[0,len(cfg["colors"])],"default":0,"client_sync":True}
            for a,cfg in ACC.items()}
        # mjau:tam gor tamjningen OBSERVERBAR server-side (is_tamed syns inte i
        # selektorer). Ingen render controller laser den -> ingen client_sync.
        e["description"]["properties"]["mjau:tam"]={"type":"int","range":[0,1],"default":0}
        # humor: 0=hungrig (hängande svans), 1=neutral, 2=glad (hög svans).
        # Godis höjer, timern sänker. client_sync: svans-animationen läser den.
        e["description"]["properties"]["mjau:humor"]={"type":"int","range":[0,2],"default":1,"client_sync":True}
        # sover: 1 när katten ligger i sovhögen. Sovposen (animation.katt.sova)
        # hängde tidigare på q.is_sleeping, en vaniljfråga som ALDRIG blir sann
        # för en katt — staten fanns i styrfilen men gick inte att nå. Med en
        # egen egenskap går den att nå, och högen ser ut som en hög i stället för
        # att bara vara en osynlig mekanik. client_sync: animationsstyrningen
        # körs på klienten och kan inte läsa en egenskap servern inte skickar.
        # hungrig: gör hungerns VERKAN observerbar. Komponentgrupper syns inte i
        # selektorer, så utan den här kan inget test se att gåvorna och
        # skattgrävandet faktiskt pausades — bara att humöret ändrades. Samma
        # skäl som mjau:tam finns av. Ingen renderare läser den, alltså ingen
        # client_sync.
        e["description"]["properties"]["mjau:hungrig"]={"type":"int","range":[0,1],"default":0}
        e["description"]["properties"]["mjau:sover"]={"type":"int","range":[0,1],"default":0,"client_sync":True}
        # Matningen lämnar en kort signal till skriptet, som visar kattens
        # reaktion med hjärtan och ett spinnande utan att gissa på itemUse.
        e["description"]["properties"]["mjau:matad"]={"type":"int","range":[0,1],"default":0}
        # Personligheten är fast per ras, så en katt behåller sin karaktär när
        # världen laddas om. Beteendena nedan justeras från samma profil.
        if _personlighet:
            e["description"]["properties"]["mjau:personlighet"]={
                "type":"int", "range":[0, len(PERSONLIGHETER) - 1],
                "default":list(PERSONLIGHETER).index(_cat)}
            g["mjau:fri"]["minecraft:behavior.random_stroll"]["speed_multiplier"] = _personlighet["stroll"]
            g["mjau:fri"]["minecraft:behavior.random_sitting"]["start_chance"] = _personlighet["sit"]
            g["mjau:jagar"]["minecraft:behavior.nearest_attackable_target"]["within_radius"] = _personlighet["hunt"]
            for _target in g["mjau:jagar"]["minecraft:behavior.nearest_attackable_target"]["entity_types"]:
                _target["max_dist"] = _personlighet["hunt"]
        # GARNNYSTANET (3.49.0): katten jagar ett kastat nystan, leker med det
        # och bär hem det. Hundpaketets läxa gäller här: behavior.pickup_items
        # gör INGENTING utan minecraft:shareables — önskelistan är det som får
        # djuret att gå fram till föremålet. leker: 0 = inget, 1 = jagar,
        # 2 = bär hem. Ingen renderare läser den (ingen kub i munnen ännu).
        e["description"]["properties"]["mjau:leker"]={"type":"int","range":[0,2],"default":0}
        e["components"]["minecraft:shareables"]={"all_items":False,"items":[
            {"item":"mjau:garnboll","want_amount":1,"surplus_amount":1,"priority":0}]}
        # PRIORITET 6, inte 21. Första försöket la jakten längst ner för att den
        # skulle ge vika för allt annat — och då körde den ALDRIG: look_at_player
        # (16) och random_look_around (17) är nästan alltid aktiva, så ett mål
        # under dem får aldrig turen. Katten stod still och tittade på nystanet.
        # Sexan delas med mjau:jagar (kaninjakten), men grupperna UTESLUTER
        # VARANDRA: mjau:lek_pa tar bort jagar och mjau:lek_av lägger tillbaka
        # den. En katt som leker med garn jagar inte kaniner samtidigt.
        g["mjau:lek_jagar"]={"minecraft:behavior.pickup_items":{
            "priority":6,"max_dist":16,"goal_radius":1.4,"speed_multiplier":1.25,
            "pickup_based_on_chance":False,"track_target":True}}
        ev["mjau:lek_pa"]={"add":{"component_groups":["mjau:lek_jagar"]},
                           "remove":{"component_groups":["mjau:jagar"]},
                           "set_property":{"mjau:leker":1}}
        ev["mjau:lek_av"]={"remove":{"component_groups":["mjau:lek_jagar"]},
                           "add":{"component_groups":["mjau:jagar"]}}
        for k in [k for k in ev if k.startswith("mjau:on_") and k not in ("mjau:on_tame",)]: del ev[k]
        g.pop("mjau:vagnsplats",None)   # gammal grupp: rideable bor numera bara i mjau:saddled
        inter=[]
        def entry(item,event,sound):
            return {"on_interact":{"filters":{"all_of":[
                      {"test":"is_family","subject":"other","value":"player"},
                      {"test":"is_owner","subject":"other"},
                      {"test":"has_equipment","domain":"hand","subject":"other","value":item}]},
                    "event":event,"target":"self"},
                    "use_item":True,"play_sounds":sound,"interact_text":"action.interact.mjau_equip"}
        for a,cfg in ACC.items():
            for i,(slug,col) in cfg["colors"].items():
                evn=f"mjau:on_{a}_{i}"
                ev[evn]={"set_property":{f"mjau:{a}":i}}
                if a=="rustning":
                    # inte bara kosmetik: pansar ger liv efter nivå — järn 20,
                    # guld 22, diamant 25, netherit 30 hjärtan (bas 10). Byte av
                    # rustning tar bort de andra nivågrupperna, annars avgör
                    # gruppernas tilläggning vilken hälsa som vinner.
                    # RUSTNINGEN ADDERAR. Den satte ett FAST värde, så en birma i
                    # netherit hade exakt lika mycket liv som en ragdoll — och
                    # storleksskillnaden ovan hade försvunnit i samma sekund
                    # man satte pansar på katten. Tillägget är detsamma för
                    # alla; grunden är kattens egen.
                    _hp=_liv+{1:20,2:24,3:30,4:40}[i]
                    g[f"mjau:armored_{i}"]={"minecraft:health":{"value":_hp,"max":_hp}}
                    # health-gruppen höjer bara MAX — nuvarande hälsa följer inte
                    # med (uppmätt i live-testet). Låt påsättningen läka katten
                    # fullt via spell_effects, annars är extra-hjärtana tomma.
                    g["mjau:pansarkur"]={"minecraft:spell_effects":{"add_effects":[
                        {"effect":"instant_health","duration":1,"amplifier":5,
                         "display_on_screen_animation":False}]}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:pansarkur")
                    ev[evn].setdefault("remove",{}).setdefault("component_groups",[]).append("mjau:pansarkur")
                    # legacy: <=2.6.1 sparade "mjau:armored" i världsdata — behåll
                    # definitionen (annars okänd aktör vid uppgradering) men låt
                    # varje rustningsbyte städa bort den
                    g["mjau:armored"]={"minecraft:health":{"value":30,"max":30}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append(f"mjau:armored_{i}")
                    ev[evn].setdefault("remove",{}).setdefault("component_groups",[]).extend(
                        [f"mjau:armored_{j}" for j in (1,2,3,4) if j!=i]+["mjau:armored"])
                if a in ("mantel","rymdmantel"):
                    # SUPERKRAFTER (speltest-önskemål): manteln är inte bara stil —
                    # en ridd katt blir snabbare och hoppar högre (samma charged-
                    # jump-mekanik som redan bär katten upp fyrkullen/kattbanan,
                    # bara starkare). Alla fyra färger ger samma kraft — manteln
                    # är kraften, färgen är bara stilen. Ingen mutual exclusion
                    # behövs mellan färgerna (samma grupp läggs bara till igen).
                    g["mjau:supermantel"]={
                        "minecraft:movement":{"value":0.68},
                        "minecraft:horse.jump_strength":{"value":1.8}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:supermantel")
                if a=="energisvard":
                    # BEVÄPNAD KATT (speltest-önskemål): bladet är inte bara
                    # dekor på ryggen — en katt som bär det slår hårdare när
                    # den jagar. 3 -> 7 skada, i nivå med ett järnsvärd, så
                    # den blir en riktig stridskompis utan att bli absurd.
                    # Räckvidden lämnas orörd: katten ska fortfarande behöva
                    # gå fram, inte plocka mål på håll.
                    #
                    # Skadan RÄCKTE INTE. Katternas enda måltavlor är kaniner
                    # och höns (mjau:jagar, vanlig kattbeteende), så de sju
                    # skadepoängen kom aldrig till användning mot något
                    # farligt — "kan man slåss med svärden? eller katterna?"
                    # var alltså ett nej för kattens del. En beväpnad katt får
                    # därför riktiga stridsbeteenden: den går emellan när du
                    # blir angripen, hjälper till mot det du slår på, och
                    # tar zombier/skelett/spindlar/creepers som kommer nära.
                    # Bara 8 blocks räckvidd — den ska försvara dig, inte
                    # rusa iväg och dö i mörkret.
                    # Gruppen får BARA komponenter som ingen annan grupp har.
                    # Ett försök att utöka mjau:jagars måltavlor genom att
                    # kopiera hela gruppen föll: två grupper kan inte båda
                    # definiera nearest_attackable_target/stalk/melee_attack —
                    # den ena skriver tyst över den andra, och vilken som vinner
                    # beror på i vilken ordning grupperna råkar ligga. Den
                    # statiska kontrollen fångade det.
                    #
                    # Kvar blir vargmodellen, som är den rätta ändå: katten
                    # slår tillbaka mot det som angriper DIG, och hjälper till
                    # mot det du själv slår på. Anfallet utförs av jagars
                    # melee_attack (prio 8), som redan finns. 13 och 18 är de
                    # lägsta lediga prioriteterna (1-12 är upptagna).
                    #
                    # Katten jagar fortfarande kaniner på prio 6, så mitt i en
                    # kaninjakt går försvaret före först när jakten släpper.
                    g["mjau:bladbararen"]={
                        "minecraft:attack":{"damage":7},
                        "minecraft:behavior.owner_hurt_by_target":{"priority":13},
                        "minecraft:behavior.owner_hurt_target":{"priority":18}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:bladbararen")
                if a in ("vingar","batvingar"):
                    # VINGKRAFT (speltest-önskemål "bygg alla"): aldrig fallskada,
                    # oavsett höjd — utökar samma damage_sensor-knep som redan gör
                    # sadlade/förspända katter fallskadefria, fast permanent.
                    g["mjau:vingkraft"]={"minecraft:damage_sensor":{"triggers":[
                        {"cause":"fall","deals_damage":False}]}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:vingkraft")
                if a=="doktorsrock":
                    # LÄKARROCKEN: konstant sakta läkning (regeneration, mycket
                    # lång varaktighet i praktiken permanent).
                    g["mjau:lakarrock"]={"minecraft:spell_effects":{"add_effects":[
                        {"effect":"regeneration","duration":999999,"amplifier":0,
                         "display_on_screen_animation":False}]}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:lakarrock")
                if a=="regnrock":
                    # REGNROCKEN: torr och nöjd — hungertimern går tre gånger
                    # långsammare. En komponentgrupp med minecraft:timer
                    # skuggar bastimern (600-1200 s) medan plagget sitter på.
                    g["mjau:regnrock_torr"]={"minecraft:timer":{"time":[1800,3600],"looping":True,
                        "time_down_event":{"event":"mjau:hungrigare","target":"self"}}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:regnrock_torr")
                if a=="krona":
                    # KRONAN: alltid synlig (glowing genom väggar) — kungligt och
                    # lätt att hitta katten i mörkret.
                    g["mjau:kunglig_glod"]={"minecraft:spell_effects":{"add_effects":[
                        {"effect":"glowing","duration":999999,"amplifier":0,
                         "display_on_screen_animation":False}]}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:kunglig_glod")
                # ÖVRIGA SUPERKRAFTER (speltest-önskemål: "jag vill fortsätta" —
                # samma effektmönster (spell_effects, mycket lång varaktighet i
                # praktiken permanent), en distinkt vanilla-effekt per plagg.
                if a in _EXTRA_POWERS:
                    _grp,_eff,_ = _EXTRA_POWERS[a]
                    _effekter=_eff if isinstance(_eff,list) else [(_eff,0)]
                    g[_grp]={"minecraft:spell_effects":{"add_effects":[
                        {"effect":_e,"duration":999999,"amplifier":_amp,
                         "display_on_screen_animation":False} for _e,_amp in _effekter]}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append(_grp)
                if cfg.get("rideable"):
                    # SADEL: ryttare på ryggen. Utesluter vagnläget — två aktiva
                    # rideable-definitioner ger odefinierat beteende.
                    g["mjau:saddled"]["minecraft:rideable"]={
                        "seat_count":1,"family_types":["player"],
                        "interact_text":"action.interact.ride",
                        "seats":[{"position":[0.0,0.562,-0.22]}]}
                    ev[evn]["add"]={"component_groups":["mjau:saddled"]}
                    # jagar + fri måste av när riddjuret sätts — annars styr
                    # katten sig själv under ryttaren (sköts av statisk check)
                    ev[evn]["remove"]={"component_groups":["mjau:sittable","mjau:carted","mjau:jagar","mjau:fri","mjau:sovdags","mjau:hunger_sok","mjau:bladbararen"]}
                if cfg.get("seats"):
                    # VAGN: seat 0 I vagnen (styrbar som en släde), seat 1 på ryggen
                    # för en vän. Egen grupp med egna styr-/lastkomponenter; sadel-
                    # och vagnläget tar bort varandra så bara EN rideable är aktiv.
                    sad=g["mjau:saddled"]
                    g["mjau:carted"]={
                        "minecraft:is_saddled":{},
                        "minecraft:input_ground_controlled":{},
                        "minecraft:movement":dict(sad.get("minecraft:movement",{"value":0.5})),
                        "minecraft:horse.jump_strength":dict(sad.get("minecraft:horse.jump_strength",{"value":1.2})),
                        "minecraft:can_power_jump":{},
                        "minecraft:is_chested":{},
                        "minecraft:inventory":{"container_type":"horse",
                                               "inventory_size":15,"private":False},
                        "minecraft:rideable":{
                            "seat_count":2,"family_types":["player"],
                            "interact_text":"action.interact.ride",
                            "seats":[{"position":cfg["seats"][0]},{"position":cfg["seats"][1]}]}}
                    ev[evn].setdefault("add",{}).setdefault("component_groups",[]).append("mjau:carted")
                    ev[evn].setdefault("remove",{}).setdefault("component_groups",[]).extend(["mjau:sittable","mjau:saddled","mjau:jagar","mjau:fri","mjau:sovdags","mjau:hunger_sok","mjau:bladbararen"])
                inter.append(entry(f"mjau:{a}_{slug}",evn,cfg["sound"]))   # namnrymd krävs för EGNA föremål
        inter.append(entry("saddle","mjau:on_sadel_1","saddle"))
        # SPINNA/MATA: godis på tam katt höjer humöret
        inter.append(entry("mjau:godis","mjau:on_matad","eat"))
        ev["mjau:on_matad"]={"set_property":{"mjau:humor":2,"mjau:matad":1}}
        # PINNLEK: ägaren kan starta en kort jaktlek med en vanlig pinne.
        # Pinnen förbrukas inte; garnbollen behåller sin egen kast-/hämtlek.
        inter.append({"on_interact":{"filters":{"all_of":[
            {"test":"is_family","subject":"other","value":"player"},
            {"test":"is_owner","subject":"other"},
            {"test":"has_equipment","domain":"hand","subject":"other","value":"stick"}]},
            "event":"mjau:lek_pa","target":"self"},
            "use_item":False,"interact_text":"action.interact.mjau_play"})
        # humöret sjunker med tiden (ordningen 1->0 före 2->1 hindrar kaskad)
        e["components"]["minecraft:timer"]={"time":[180,360],"looping":True,
            "time_down_event":{"event":"mjau:hungrigare","target":"self"}}
        ev["mjau:hungrigare"]={"sequence":[
            {"filters":{"test":"int_property","domain":"mjau:humor","value":1},
             "set_property":{"mjau:humor":0}},
            {"filters":{"test":"int_property","domain":"mjau:humor","value":2},
             "set_property":{"mjau:humor":1}}]}
        # (behavior.nap togs bort i 2.6.1 — katterna "bara låg och sov";
        #  statisk check förbjuder den, så återinför den inte här)
        # KATTFISKE: sadlad/förspänd katt i vatten fångar fisk
        for _rg in ("mjau:saddled","mjau:carted"):
            # RIDDJURET tar fallskadan i Bedrock — nolla 'fall' så katten
            # inte dör när ryttaren hoppar ner (2.6.1-fix)
            g[_rg]["minecraft:damage_sensor"]={"triggers":[
                {"cause":"fall","deals_damage":False}]}
            g[_rg]["minecraft:spawn_entity"]={"entities":[
                {"min_wait_time":12,"max_wait_time":40,"spawn_item":"minecraft:cod",
                 "spawn_sound":"splash","filters":{"test":"in_water","value":True}}]}
        # SKATTLETANDE: ryggsäckskatter gräver fram småsaker (sällsynt en diamant)
        g["mjau:skattletare"]={"minecraft:spawn_entity":{"entities":[
            {"min_wait_time":300,"max_wait_time":900,"spawn_item":"minecraft:string","spawn_sound":"drop.slot"},
            {"min_wait_time":420,"max_wait_time":1200,"spawn_item":"minecraft:feather","spawn_sound":"drop.slot"},
            {"min_wait_time":2400,"max_wait_time":4800,"spawn_item":"minecraft:diamond","spawn_sound":"random.levelup"}]}}
        if _personlighet:
            g["mjau:gavor"]["minecraft:behavior.drop_item_for"]["drop_item_chance"] = _personlighet["gift"]
        # ...och bär på RIKTIGT. Ryggsäcken var ren dekor: den syntes på ryggen
        # och räckte som filter för Skattgrävaren, men gick inte att lägga något
        # i. Lastrummet är samma som vagnens (is_chested + horse-container), och
        # med FLIT identiska värden: en katt kan ha både vagn och ryggsäck, och
        # två grupper som sätter minecraft:inventory olika stort ger odefinierad
        # storlek. Lika värden = ingen konflikt oavsett vilken som vinner.
        g["mjau:packad"]={
            "minecraft:is_chested":{},
            "minecraft:inventory":{"container_type":"horse",
                                   "inventory_size":15,"private":False}}
        for _i in (1,2,3):
            _evn=f"mjau:on_ryggsack_{_i}"
            if _evn in ev:
                ev[_evn].setdefault("add",{}).setdefault("component_groups",[]).extend(
                    ["mjau:skattletare","mjau:packad"])
        # KATTUNGAR föds ibland med rosett.
        #
        # SLUMPNINGARNA RENSAS FÖRST. Raderna nedan la tidigare BARA till, och
        # entiteterna är inte färskgenererade utan patchade — så varje körning
        # av det här skriptet la på ett par till. Vid upptäckten 2026-08-27 låg
        # det 32 rosettslumpningar och 31 halsband i varje katt, och effekten
        # var tyst men total: "ibland född med rosett" är 40 % en gång, men
        # 1 - 0,6^32 = 100 % trettiotvå gånger. VARJE kattunge föddes med rosett
        # och 98 % med halsband. Det har legat ute i alla släpp sedan funktionen
        # kom.
        _born=ev["minecraft:entity_born"]
        _seq=_born.setdefault("sequence",[])
        _seq[:] = [x for x in _seq if not ("randomize" in x and any(
            ("mjau:rosett" in json.dumps(o) or "mjau:halsband" in json.dumps(o))
            for o in x["randomize"]))]
        _seq.append({"randomize":[
            {"weight":60},
            {"weight":10,"set_property":{"mjau:rosett":1}},
            {"weight":10,"set_property":{"mjau:rosett":2}},
            {"weight":10,"set_property":{"mjau:rosett":3}},
            {"weight":10,"set_property":{"mjau:rosett":4}}]})
        # ...och mer sällan med ett halsband (speltest-önskemål: "bygg alla" —
        # kitten-trait-idén, varje kull lite unik utöver bara namn+antal)
        _seq.append({"randomize":[
            {"weight":88},
            {"weight":4,"set_property":{"mjau:halsband":1}},
            {"weight":4,"set_property":{"mjau:halsband":2}},
            {"weight":4,"set_property":{"mjau:halsband":3}}]})
        # KOLONIN — NATTENS SOVGRUPP. mjau:fri låter katten stryka omkring och
        # söka sig till ÅTTA möbeltyper med 40 % chans. På natten ska flocken i
        # stället samlas, och med åtta mål sprider den sig över matskål,
        # kattlucka och fiskdamm — då blir det aldrig någon hög. Nattgruppen
        # söker bara sovplatser (bädd och kartong), med hög chans och lång
        # liggtid.
        #
        # GRUPPEN ERSÄTTER mjau:fri, den läggs INTE ovanpå — men den lånar INTE
        # dess prioriteter. Första försöket återanvände 12 och 15 med
        # motiveringen "de är ändå aldrig aktiva samtidigt", och strukturgrinden
        # underkände det på alla tio katterna. Grinden hade rätt: ingenting i
        # DATAN garanterar att de är uteslutande — det garanteras bara av att
        # skriptet råkar byta dem parvis, och nästa händelse som lägger på
        # mjau:fri skulle ge två move_to_block med samma prioritet, vilket är
        # odefinierat i Bedrock. 19 och 20 är lediga och ligger under allt
        # annat, precis som en sysselsättning ska göra.
        #
        # tempt och random_stroll finns med flit inte här: en katt som ska sova
        # ska varken vandra iväg eller lockas av fisk.
        g["mjau:sovdags"]={
            "minecraft:behavior.move_to_block":{
                "priority":19,"tick_interval":40,"start_chance":0.9,
                "search_range":16,"search_height":4,"goal_radius":1.2,
                "stay_duration":200,"target_selection_method":"nearest",
                "target_offset":[0,1,0],
                "target_blocks":["mjau:kattbadd","mjau:kartong"]},
            "minecraft:behavior.random_sitting":{
                "priority":20,"min_sit_time":20,"start_chance":0.3,"stop_chance":0.02}}
        # Furniture visits reserve distinct native navigation goals, then stop
        # movement briefly. Release restores the speed of the current outfit.
        e["description"]["properties"]["mjau:mobel"]={"type":"int","range":[-1,15],"default":0,"client_sync":True}
        g["mjau:sittable"]["minecraft:sittable"]={
            "sit_event":{"event":"mjau:mobel_sitt","target":"self"},
            "stand_event":{"event":"mjau:mobel_stand","target":"self"}}
        ev["mjau:mobel_sitt"]={"set_property":{"mjau:mobel":-1}}
        ev["mjau:mobel_stand"]={"set_property":{"mjau:mobel":0}}
        # Navigation must outrank ambient looking. move_to_block can still wait
        # on a look goal even when its explicit control_flags omit "look".
        e["components"]["minecraft:behavior.look_at_player"]["priority"]=60
        e["components"]["minecraft:behavior.random_look_around"]["priority"]=61
        ambient=g["mjau:fri"]["minecraft:behavior.move_to_block"]
        managed={"mjau:"+b for b in ("sovkorg","kattspa","katt_tv","klosbrada","fonsterbadd","kattfontan")}
        ambient["target_blocks"]=[b for b in ambient["target_blocks"] if b not in managed]
        furniture_goals=[]
        for direction,(cos,sin) in {"north":(1,0),"east":(0,1),"south":(-1,0),"west":(0,-1)}.items():
            for mode,(name,block,(x,y,z)) in enumerate([
                ("basket0","sovkorg",[-.46,3/16,0]),("basket1","sovkorg",[.46,3/16,0]),
                ("spa","kattspa",[0,1/16,0]),("tv","katt_tv",[0,0,-1.3]),("scratch","klosbrada",[0,0,-.95]),("window","fonsterbadd",[0,1,-.25]),("fountain","kattfontan",[0,0,-1.1]),("spa_exit","kattspa",[0,0,-1.4])],1):
                furniture_goals.append((name+"_"+direction,block,[x*cos-z*sin,y,x*sin+z*cos],{"scratch":9,"window":10,"fountain":13,"spa_exit":15}.get(name,mode)))
        # Remove old generated approach definitions after expanding directions.
        for name in ("basket0","basket1","spa","tv"):
            g.pop("mjau:mobel_"+name,None);ev.pop("mjau:mobel_"+name,None)
        furniture_groups=["mjau:mobel_"+name for name,_,_,_ in furniture_goals]+["mjau:mobel_hold"]
        speed_groups=["mjau:mobel_normal","mjau:mobel_ride","mjau:mobel_fast"]
        for i,(name,block,offset,mode) in enumerate(furniture_goals):
            g["mjau:mobel_"+name]={"minecraft:movement":{"value":.32},"minecraft:behavior.move_to_block":{
                "control_flags":["move","jump"],"priority":22+i,"tick_interval":1,"start_chance":1,
                "search_range":6,"search_height":2,"goal_radius":.2,
                "stay_duration":300,"target_selection_method":"nearest",
                "target_offset":offset,"target_blocks":["mjau:"+block]}}
            ev["mjau:mobel_"+name]={"sequence":[
                {"set_property":{"mjau:mobel":mode,"mjau:sover":0},
                 "remove":{"component_groups":[group for group in furniture_groups if group != "mjau:mobel_"+name]+["mjau:fri","mjau:sovdags"]}},
                {"add":{"component_groups":["mjau:mobel_"+name]}}]}
        g["mjau:mobel_hold"]={"minecraft:movement":{"value":0},"minecraft:pushable":{"is_pushable":False,"is_pushable_by_piston":True}}
        for name,speed in (("normal",.32),("ride",.5),("fast",.68)):
            g["mjau:mobel_"+name]={"minecraft:movement":{"value":speed},"minecraft:pushable":{"is_pushable":True,"is_pushable_by_piston":True}}
        ev["mjau:mobel_vantar"]={
            "remove":{"component_groups":furniture_groups[:-1]+speed_groups},
            "add":{"component_groups":["mjau:mobel_hold"]}}
        for kind,mode in (("basket",5),("spa",6),("tv",7),("scratch",8),("window",11),("window_sleep",12),("fountain",14)):
            ev["mjau:mobel_vila_"+kind]={"set_property":{"mjau:mobel":mode},
                "remove":{"component_groups":furniture_groups[:-1]+speed_groups},
                "add":{"component_groups":["mjau:mobel_hold"]}}
        for event_name,event in ev.items():
            if event_name.startswith(("mjau:on_sadel_","mjau:on_vagn_")):
                removed=event.setdefault("remove",{}).setdefault("component_groups",[])
                removed[:]=[group for group in removed if group not in ["mjau:mobel_"+n for n in ("basket0","basket1","spa","tv")]]
                for group in furniture_groups+speed_groups:
                    if group not in removed: removed.append(group)
                event.setdefault("set_property",{})["mjau:mobel"]=0
        def gear_filter(name):
            return {"test":"int_property","domain":"mjau:"+name,"operator":">","value":0}
        ev["mjau:mobel_av"]={"sequence":[
            {"set_property":{"mjau:mobel":0,"mjau:sover":0},
             "remove":{"component_groups":furniture_groups+speed_groups}},
            {"add":{"component_groups":["mjau:mobel_normal"]}},
            {"filters":{"any_of":[gear_filter("sadel"),gear_filter("vagn")]},
             "remove":{"component_groups":["mjau:mobel_normal"]},
             "add":{"component_groups":["mjau:mobel_ride"]}},
            {"filters":{"any_of":[gear_filter("mantel"),gear_filter("rymdmantel")]},
             "remove":{"component_groups":["mjau:mobel_normal","mjau:mobel_ride"]},
             "add":{"component_groups":["mjau:mobel_fast"]}}]}
        ev["mjau:sover_pa"]={"set_property":{"mjau:sover":1}}
        ev["mjau:sover_av"]={"set_property":{"mjau:sover":0}}
        ev["mjau:sovdags_pa"]={"add":{"component_groups":["mjau:sovdags"]},
                               "remove":{"component_groups":["mjau:fri"]}}
        ev["mjau:sovdags_av"]={"add":{"component_groups":["mjau:fri"]},
                               "remove":{"component_groups":["mjau:sovdags"]}}
        # HUNGERN SKA BETYDA NÅGOT. Systemet fanns redan — en timer sänker
        # mjau:humor, mat höjer det — men det ENDA i hela paketet som läste det
        # var svansens vinkel i animationen. En katt som inte fått mat på en
        # kvart betedde sig exakt som en mätt katt.
        #
        # REGELN: hungern rör bara BONUSARNA. En hungrig katt följer, bär, bärs,
        # vaktar och varnar precis som vanligt — hon slutar bara gräva fram
        # skatter och komma med morgongåvor tills hon fått mat. Det man är
        # BEROENDE av får aldrig gå sönder för att man glömt en fisk.
        #
        # GÅVORNA FLYTTAS TILL EN EGEN GRUPP. De låg i mjau:tamed, som måste
        # sitta kvar (den bär is_tamed och interaktionerna) — en grupp går bara
        # att stänga av genom att ta bort den, så beteendet behöver bo för sig.
        _gavor = g["mjau:tamed"].pop("minecraft:behavior.drop_item_for", None)
        if _gavor is not None:
            g["mjau:gavor"] = {"minecraft:behavior.drop_item_for": _gavor}
        # HUNGERN SKA SYNAS I BETEENDET. En hungrig katt söker matskålen, men
        # gruppen läggs ovanpå mjau:fri med en egen prioritet så följa-, bära-
        # och ridmekaniken aldrig stängs av av ett behov.
        g["mjau:hunger_sok"] = {"minecraft:behavior.move_to_block": {
            "priority": 21, "tick_interval": 20, "start_chance": 0.9,
            "search_range": 16, "search_height": 4, "goal_radius": 1.2,
            "stay_duration": 80, "target_selection_method": "nearest",
            "target_offset": [0, 1, 0], "target_blocks": ["mjau:matskal"]}}
        # EN GÅNG, inte en gång per körning. Utan kontrollen växer listan med
        # en kopia varje bygge — den stod på nio när felet upptäcktes. Motorn
        # bryr sig inte (att lägga till en grupp som redan lagts till är en
        # nulloperation), men det är exakt samma ackumulering som en gång gjorde
        # "ibland född med rosett" till 100 %, och den gången var den inte
        # ofarlig. Skriptet ska vara idempotent, punkt.
        _tame_add = ev["mjau:on_tame"].setdefault("add", {}).setdefault(
            "component_groups", [])
        if "mjau:gavor" not in _tame_add:
            _tame_add.append("mjau:gavor")
        # mjau:packad rörs ALDRIG av hungern: den bär lastrummet, och att ta bort
        # minecraft:inventory är att slänga kattens last.
        ev["mjau:hungrig_pa"] = {"set_property": {"mjau:hungrig": 1},
                                 "add": {"component_groups": ["mjau:hunger_sok"]},
                                 "remove": {"component_groups":
                                            ["mjau:gavor", "mjau:skattletare"]}}
        # SET_PROPERTY BREDVID EN SEQUENCE IGNORERAS TYST. Först stod den som
        # syskon till "sequence" och hände helt enkelt inte — eventet kördes,
        # grupperna lades på, men egenskapen stod kvar. Det syntes inte i någon
        # logg; det upptäcktes genom att köra eventet DIREKT från konsolen och
        # se att testfor ändå inte matchade. Åtgärden är att lägga den i första
        # steget INNE i sekvensen. (mjau:hungrig_pa har ingen sequence och
        # fungerade därför hela tiden — vilket gjorde felet ännu mer förvirrande.)
        ev["mjau:matt_igen"] = {"sequence": [
            # Removing even an inactive group can clear a shared component.
            # Initial fed-state synchronisation must not erase furniture navigation.
            {"filters":{"test":"int_property","domain":"mjau:hungrig","value":1},
             "remove":{"component_groups":["mjau:hunger_sok"]}},
            {"set_property": {"mjau:hungrig": 0},
             "add": {"component_groups": ["mjau:gavor"]}},
            # skattletaren tillbaka BARA om katten faktiskt bär ryggsäck —
            # annars börjar en katt utan väska spotta ur sig tråd och fjädrar
            {"filters": {"test": "int_property", "domain": "mjau:ryggsack",
                         "operator": ">", "value": 0},
             "add": {"component_groups": ["mjau:skattletare"]}}]}
        # TIMERN FÖRLÄNGS. Två steg à 3-6 minuter betyder mätt till hungrig på
        # sex till tolv minuter. Blir hungern mekanisk är katterna hungriga
        # nästan jämt, och då är det ett gnat och inte en omsorgsslinga. Tio till
        # tjugo minuter per steg ger tjugo till fyrtio minuter från full skål.
        e["components"]["minecraft:timer"]["time"] = [600, 1200]
        g["mjau:tamed"]["minecraft:interact"]={"interactions":inter}
        json.dump(d,open(f,"w"),indent=2)

    # Bedrock läser INTE en .lang-fil utan texts/languages.json som deklarerar
    # vilka språk paketet har. Saknas den faller allt tillbaka på råa nycklar —
    # och våra identifierare är svenska (sadel_brun, keps_cyan, ryggsack...), så
    # spelaren fick svenska namn och råa hint-nycklar trots engelsk lang-fil.
    # sv_SE finns med och innehåller SAMMA engelska text, så en svenskspråkig
    # konsol inte hamnar i fallback igen.
    for pack in ("PurrfectCompanions_BP","PurrfectCompanions_RP"):
        json.dump(["en_US","sv_SE"],open(f"{BASE}/{pack}/texts/languages.json","w"))
    # SÄKERHETSFIX 2026-08-13: sv_SE.lang KOPIERADES tidigare rakt av från
    # en_US, vilket raderade ALLA svenska rader skriptet inte äger — hela
    # achievement-listan (Trippelskatten, Kattbanemästaren ...) blev engelsk.
    # Nu behandlas filerna var för sig: bara plagg-/hint-raderna byts ut,
    # allt annat står kvar som det är. (Plaggnamnen är engelska även i
    # sv_SE — familjevarianten döper om dem via variants.private.json.)
    for pack in ("PurrfectCompanions_BP","PurrfectCompanions_RP"):
        for spr in ("en_US","sv_SE"):
            lp=f"{BASE}/{pack}/texts/{spr}.lang"
            if not os.path.exists(lp): shutil.copyfile(f"{BASE}/{pack}/texts/en_US.lang", lp)
            keep=[l for l in open(lp).read().rstrip("\n").split("\n")
                  if not l.startswith(("item.mjau:","action."))]
            open(lp,"w").write("\n".join(dict.fromkeys(keep+lang))+"\n")
    # ---------------------------------------------------------------- Kattboken
    # BOKENS DATA GENERERAS, den skrivs inte. En handskriven guide till 96
    # föremål ruttnar inom två släpp: någon lägger till ett plagg, glömmer
    # boken, och boken börjar ljuga. Allt som går att HÄRLEDA ur tabellerna
    # härleds — vilka plagg som finns, vad de heter, vilka färger de har och
    # vilken effekt de ger.
    #
    # Det som INTE går att härleda (att sadeln betyder ridning, att ryggsäcken
    # har femton fack) står som en valfri språknyckel per plagg,
    # mjau.bok.plagg.<id>. Saknas nyckeln visar boken bara den genererade
    # delen — ett nytt plagg gör alltså boken tunnare, aldrig trasig.
    plagg = []
    for a, cfg in ACC.items():
        plagg.append({
            "id": a,
            "namn": cfg["label"],
            "farger": [cfg["names"][i] for i in sorted(cfg["colors"])],
            "effekt": _EXTRA_POWERS[a][2] if a in _EXTRA_POWERS else None,
            "prosa": a in _BOKPROSA,
        })
    # KATTERNA med sitt biom, läst ur spawnreglerna i stället för ur en lista
    # här. Flyttas en ras till ett annat biom följer boken med av sig själv.
    katter = []
    for c in KATTER:
        biom = None
        sr = f"{BP}/spawn_rules/{c}.json"
        if os.path.exists(sr):
            for v in json.load(open(sr))["minecraft:spawn_rules"]["conditions"]:
                biom = (v.get("minecraft:biome_filter") or {}).get("value") or biom
        katter.append({"id": f"mjau:{c}", "biom": biom,
                       "personlighet": PERSONLIGHETER.get(c, {}).get("namn")})
    mobler = []
    for f in sorted(glob.glob(f"{BP}/blocks/*.json")):
        mobler.append(json.load(open(f))["minecraft:block"]["description"]["identifier"])
    open(f"{BP}/scripts/bokdata.js", "w", encoding="utf-8").write(
        "// GENERERAD AV build_accessories.py — ändra i ACC/_EXTRA_POWERS, inte här.\n"
        "export const PLAGG = " + json.dumps(plagg, indent=1, ensure_ascii=False) + ";\n"
        "export const KATTER = " + json.dumps(katter, indent=1, ensure_ascii=False) + ";\n"
        "export const MOBLER = " + json.dumps(mobler, indent=1, ensure_ascii=False) + ";\n")

    return len(lang), len(inter)

if __name__ == "__main__":
    n = build_geometry()
    paint_accessories()
    items, inters = build_rest()
    from make_cat_pals import main as build_coats
    build_coats()
    print(f"{len(ACC)} plagg · {n} geometrier · {items} föremål · {inters} interaktioner")
    for a,cfg in ACC.items():
        print(f"  {a:9s} {len(cfg['colors'])} färger  ({cfg['label']})")
