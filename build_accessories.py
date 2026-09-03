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
_BOKPROSA = {"sadel", "ryggsack", "vagn", "vingar", "rustning", "energisvard",
             "gruvlampa", "regnrock", "rymdmantel", "krona", "doktorsrock"}

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

ACC = {
 "sadel": dict(label="Cat Saddle", bone="body", sound="saddle", rideable=True,
   uv={1:(24,26),2:(56,26),3:(88,26)},
   colors={1:("brun",(122,79,45)),2:("svart",(58,52,48)),3:("ljus",(206,190,160))},
   names={1:"Brown",2:"Black",3:"Light"},
   cubes=[([-3.25,9,-3],[6.5,1,6],(0,0)), ([-1.5,10,-3],[3,1,1],(0,8))],
   recipe=lambda mat: dict(pattern=["LLL","S S"] if not mat else ["LLL","SDS"],
       key={"L":{"item":"minecraft:leather"},"S":{"item":"minecraft:string"}} if not mat
           else {"L":{"item":"minecraft:leather"},"S":{"item":"minecraft:string"},"D":{"item":mat}},
       unlock=[{"item":"minecraft:leather"}]+([{"item":mat}] if mat else [])),
   mats={1:None,2:"minecraft:black_dye",3:"minecraft:white_dye"}),

 "keps": dict(label="Cat Cap", bone="head", sound="armor.equip_leather",
   uv={1:(24,40),2:(56,40),3:(24,56),4:(56,56)},
   colors={1:("cyan",(0,168,214)),2:("rod",(198,62,55)),3:("gron",(76,168,84)),4:("gul",(238,196,62))},
   names={1:"Cyan",2:"Red",3:"Green",4:"Yellow"},
   cubes=[([-3.25,9.8,-9.25],[6.5,2,4.5],(0,0)), ([-2.5,9.9,-11.5],[5,0.5,2.5],(0,8))],
   recipe=lambda mat: dict(pattern=["WWW"," L "],
       key={"W":{"item":mat},"L":{"item":"minecraft:leather"}},
       unlock=[{"item":mat},{"item":"minecraft:leather"}]),
   mats={1:"minecraft:cyan_wool",2:"minecraft:red_wool",3:"minecraft:green_wool",4:"minecraft:yellow_wool"}),

 "halsduk": dict(label="Cat Scarf", bone="body", sound="armor.equip_leather",
   uv={1:(0,72),2:(24,72),3:(48,72),4:(72,72),5:(96,72),6:(120,72)},
   colors={1:("rod",(198,62,55)),2:("bla",(64,116,200)),3:("gron",(76,168,84)),4:("gul",(238,196,62)),
           5:("rosa",(238,138,186)),6:("lila",(134,66,186))},
   names={1:"Red",2:"Blue",3:"Green",4:"Yellow",5:"Pink",6:"Purple"},
   cubes=[([-3.4,7.5,-5.6],[6.8,2,1.6],(0,0)), ([-1,5,-5.7],[2,2.5,1],(0,6))],
   recipe=lambda mat: dict(pattern=["WW","WW"], key={"W":{"item":mat}}, unlock=[{"item":mat}]),
   mats={1:"minecraft:red_wool",2:"minecraft:blue_wool",3:"minecraft:green_wool",4:"minecraft:yellow_wool",
         5:"minecraft:pink_wool",6:"minecraft:purple_wool"}),

 "ryggsack": dict(label="Cat Backpack", bone="body", sound="armor.equip_leather",
   uv={1:(0,88),2:(24,88),3:(48,88)},
   colors={1:("brun",(122,79,45)),2:("gron",(76,140,84)),3:("bla",(64,104,168))},
   names={1:"Brown",2:"Green",3:"Blue"},
   cubes=[([-3.25,9,1],[6.5,2.5,3],(0,0)), ([-3.4,9.5,1.5],[6.9,0.5,2],(0,8))],
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

 "vagn": dict(label="Cat Cart", bone="body", sound="armor.equip_leather",
   uv={1:(0,128),2:(32,128),3:(64,128)},
   colors={1:("tra",(150,108,64)),2:("rod",(178,58,52)),3:("bla",(58,102,172))},
   names={1:"Wood",2:"Red",3:"Blue"},
   # uppskalad ~35 % efter Xbox-test ("för liten") — flaket rymmer en spelare
   cubes=[([-4,2,8],[8,5,7],(0,0)),          # flaket
          ([-4.9,0,10],[1,4,4],(0,13)),      # hjul vänster
          ([3.9,0,10],[1,4,4],(0,13)),       # hjul höger
          ([-0.5,4.5,5],[1,1,3],(12,13))],   # dragstång till katten
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
   cubes=[([-3.4,7.6,-5.5],[6.8,1.2,1.4],(0,0)), ([-0.5,6.9,-5.6],[1,1,1],(0,4))],
   recipe=lambda mat: dict(pattern=["LLL"," I "],
       key={"L":{"item":mat},"I":{"item":"minecraft:iron_nugget"}},
       unlock=[{"item":mat},{"item":"minecraft:iron_nugget"}]),
   mats={1:"minecraft:red_wool",2:"minecraft:blue_wool",3:"minecraft:green_wool"}),

 "rosett": dict(label="Cat Bow", bone="head", sound="armor.equip_leather",
   uv={1:(0,186),2:(16,186),3:(32,186),4:(48,186)},
   colors={1:("pink",(238,138,186)),2:("red",(198,62,55)),3:("blue",(64,116,200)),4:("yellow",(238,196,62))},
   names={1:"Pink",2:"Red",3:"Blue",4:"Yellow"},
   cubes=[([-1.5,10.2,-7.6],[3,1.6,1],(0,0))],
   recipe=lambda mat: dict(pattern=["WWW"], key={"W":{"item":mat}}, unlock=[{"item":mat}]),
   mats={1:"minecraft:pink_wool",2:"minecraft:red_wool",3:"minecraft:blue_wool",4:"minecraft:yellow_wool"}),

 "vingar": dict(label="Cat Wings", bone="body", sound="armor.equip_leather",
   uv={1:(0,192),2:(20,192),3:(40,192)},
   colors={1:("white",(242,242,240)),2:("black",(48,46,54)),3:("gold",(226,190,84))},
   names={1:"White",2:"Black",3:"Gold"},
   cubes=[([-4.4,7,0],[0.6,5,5],(0,0)), ([3.8,7,0],[0.6,5,5],(0,0))],
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
   cubes=[([-3.6,8.8,-5.2],[7.2,1,10.4],(0,0)),
          ([-3.7,4.5,-4.5],[0.7,4.5,9],(0,13)),
          ([3.0,4.5,-4.5],[0.7,4.5,9],(0,13)),
          ([-2.5,6.5,-6.2],[5,3,1],(22,13))],
   recipe=lambda mat: dict(pattern=["I I","III","I I"],
       key={"I":{"item":mat}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:iron_ingot",2:"minecraft:gold_ingot",
         3:"minecraft:diamond",4:"minecraft:netherite_ingot"}),

 "haxhatt": dict(label="Witch Hat", bone="head", sound="armor.equip_leather",
   uv={1:(176,30),2:(216,30)},
   colors={1:("svart",(38,34,44)),2:("lila",(96,56,140))},
   names={1:"Black",2:"Purple"},
   cubes=[([-3,11.5,-8.5],[6,0.8,6],(0,0)),        # brätte
          ([-1.8,12.3,-7.3],[3.6,2.2,3.6],(0,8)),  # kupa
          ([-1,14.5,-6.5],[2,2,2],(0,15))],        # topp
   recipe=lambda mat: dict(pattern=[" W ","WWW"],
       key={"W":{"item":mat}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:black_wool",2:"minecraft:purple_wool"}),

 "tomteluva": dict(label="Santa Hat", bone="head", sound="armor.equip_leather",
   uv={1:(176,60),2:(216,60)},
   colors={1:("rod",(196,44,44)),2:("gron",(46,128,62))},
   names={1:"Red",2:"Green"},
   cubes=[([-2.6,11.4,-8.1],[5.2,1,5.2],(0,0)),    # vit kant
          ([-1.8,12.4,-7.3],[3.6,2.4,3.6],(0,7)),  # luva
          ([-0.8,14.8,-6.3],[1.6,1.6,1.6],(0,14))],# tofs
   recipe=lambda mat: dict(pattern=[" S ","WWW"],
       key={"W":{"item":mat},"S":{"item":"minecraft:snowball"}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:red_wool",2:"minecraft:green_wool"}),

 "doktorsrock": dict(label="Doctor Coat", bone="body", sound="armor.equip_leather",
   uv={1:(176,90)},
   colors={1:("vit",(238,240,242))},
   names={1:"White"},
   cubes=[([-3.5,4.2,-4.8],[0.6,4.6,9.4],(0,0)),
          ([2.9,4.2,-4.8],[0.6,4.6,9.4],(0,0)),
          ([-3.5,8.8,-4.8],[7,0.8,9.4],(0,15))],
   recipe=lambda mat: dict(pattern=["W W","WWW","W W"],
       key={"W":{"item":mat}},
       unlock=[{"item":mat}]),
   mats={1:"minecraft:white_wool"}),

 "batvingar": dict(label="Bat Wings", bone="body", sound="armor.equip_leather",
   uv={1:(176,110),2:(216,110)},
   colors={1:("svart",(30,28,34)),2:("lila",(74,44,104))},
   names={1:"Black",2:"Purple"},
   cubes=[([-8.5,8.6,-1],[5,0.7,6],(0,0)),
          ([3.5,8.6,-1],[5,0.7,6],(0,0)),
          ([-9.5,8.4,1],[1.6,3,1.6],(0,8)),
          ([7.9,8.4,1],[1.6,3,1.6],(0,8))],
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
   cubes=[([-3.3,9.6,-5.6],[6.6,1,0.6],(0,0)),      # krage vid halsen
          ([-3.4,9.9,-5.5],[6.8,0.5,11],(0,3)),      # drapering över ryggen
          ([-3.4,4,5.2],[6.8,6,0.6],(0,16))],        # hängande bakstycke
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
   cubes=[([-0.5,7,2.1],[1,2,1],(0,0)),          # grepp
          ([-1.5,9,2.1],[3,0.8,1],(5,0)),        # parerstång
          ([-0.4,9.8,2.25],[0.8,8,0.7],(14,0)),  # blad
          ([-0.25,17.8,2.32],[0.5,1.2,0.45],(18,0))],   # spets
   recipe=lambda mat: dict(pattern=["G","G","I"],
       key={"G":{"item":mat},"I":{"item":"minecraft:iron_ingot"}},
       unlock=[{"item":mat},{"item":"minecraft:iron_ingot"}]),
   mats={1:"minecraft:lapis_lazuli",2:"minecraft:emerald",
         3:"minecraft:redstone",4:"minecraft:amethyst_shard"}),

 "rymdmantel": dict(label="Star Cloak", bone="body", sound="armor.equip_leather",
   uv={1:(88,211),2:(120,211)},
   colors={1:("stjarna",(110,150,235)),2:("tomrum",(38,34,58))},
   names={1:"Starlight",2:"Void"},
   cubes=[([-3.4,4,5.2],[6.8,6,0.6],(0,0)),
          ([-3.3,9.6,-5.6],[6.6,1,0.6],(16,0))],
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
          ([-1.0,9.0,-10.3],[2.0,1.4,1.3],(0,6))],     # lampan i pannan, ovanför ögonen
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
   cubes=[([-3.5,4.2,-4.8],[0.6,4.6,9.4],(0,0)),
          ([2.9,4.2,-4.8],[0.6,4.6,9.4],(0,0)),
          ([-3.5,8.8,-4.8],[7,0.8,9.4],(0,15)),
          ([-3.4,8.4,-6.0],[6.8,1.4,1.4],(33,15))],    # huvan, nedfälld i nacken
   recipe=lambda mat: dict(pattern=["W W","WWW","WSW"],
       key={"W":{"item":mat},"S":{"item":"minecraft:slime_ball"}},
       unlock=[{"item":mat},{"item":"minecraft:slime_ball"}]),
   mats={1:"minecraft:yellow_wool",2:"minecraft:green_wool"}),
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
    for a,cfg in ACC.items():
        for i in cfg["colors"]:
            u,v=cfg["uv"][i]
            cubes=[{"origin":list(o),"size":list(s),"uv":[u+du,v+dv]} for o,s,(du,dv) in cfg["cubes"]]
            geos.append({"description":desc(f"geometry.katt.{a}{i}"),
                         "bones":[{"name":cfg["bone"],
                                   "pivot":PIVOTS[cfg["bone"]],"cubes":cubes}]})
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
        for x in range(1,15): sp(x,7,mork); sp(x,8,col); sp(x,9,mork)
        for y in range(6,11):
            for x in (2,3,4,11,12,13): sp(x,y,col)
        for y in range(7,10):
            for x in (3,12): sp(x,y,(150,200,230,255))
    elif a=="sadel":
        rect(2,6,13,9,col); rect(3,6,12,6,ljus)
        rect(2,4,4,6,ljus); rect(11,4,13,6,ljus)
        rect(6,10,9,13,mork); rect(6,13,9,13,djup)
    elif a=="keps":
        rect(4,5,11,9,col); rect(5,4,10,4,ljus)
        rect(3,10,14,11,mork)
    elif a=="gruvlampa":
        rect(2,4,13,6,mork); rect(2,4,13,4,col)                 # remmen
        rect(5,6,10,11,col); rect(6,7,9,10,(255,244,170,255))   # lampan med lins
        rect(7,8,8,9,(255,255,255,255))
    elif a=="flytvast":
        rect(3,3,12,13,col); rect(6,3,9,13,mork)                # väst med öppning
        rect(3,6,12,6,(220,220,220,255)); rect(3,10,12,10,(220,220,220,255))   # reflexband
        rect(6,5,9,5,djup); rect(6,9,9,9,djup)                  # spännen
    elif a=="regnrock":
        rect(4,1,11,3,mork); rect(5,0,10,1,mork)                # huvan
        rect(3,4,12,14,col); rect(3,4,12,4,ljus); rect(7,5,8,14,mork)   # rocken med knäppning
        sp(5,7,ljus); sp(10,9,ljus); sp(4,11,ljus)              # regndroppar
    elif a=="halsduk":
        # band runt halsen med TVÅ hängande ändar — ett rakt streck med en
        # snibb under läste som ett T, inte som en halsduk
        rect(2,5,13,5,ljus); rect(2,6,13,6,col)
        rect(2,7,4,12,col); rect(11,7,13,12,col)
        rect(2,13,4,13,djup); rect(11,13,13,13,djup)  # fransar
    elif a=="ryggsack":
        rect(4,5,11,13,col); rect(4,5,11,7,ljus)
        rect(2,6,3,11,djup); rect(12,6,13,11,djup)
        sp(7,8,(214,182,86,255)); sp(8,8,(214,182,86,255))
    elif a=="halsband":
        for x in range(4,12): sp(x,4,col); sp(x,10,col)
        for y in range(5,10): sp(3,y,col); sp(12,y,col)
        rect(7,11,8,13,(214,182,86,255))
    elif a=="rosett":
        for y in range(6,11):
            d=abs(y-8)
            rect(1+d,y,6,y,col); rect(9,y,14-d,y,col)
        rect(6,7,9,9,mork)
    elif a=="vingar":
        for i,ln in enumerate((3,5,6,6,5,4,3,2)):
            y=4+i; c=col if i%2 else sh(col,0.88)
            rect(7-ln,y,6,y,c); rect(9,y,8+ln,y,c)
    elif a=="batvingar":
        for i,ln in enumerate((2,4,5,6,6,5,3,1)):
            y=4+i; c=col if i%2 else sh(col,0.8)
            rect(7-ln,y,6,y,c); rect(9,y,8+ln,y,c)
        for x in (2,4,11,13): sp(x,12,djup)
    elif a=="horn":
        for i in range(8):
            y=13-i; w=(8-i)//2
            rect(8-w,y,8+w,y,ljus if i%2 else col)
    elif a=="krona":
        rect(2,9,13,12,col); rect(2,9,13,9,ljus)
        for x0 in (2,7,12):
            rect(x0,6,x0+1,8,col); rect(x0,5,x0+1,5,ljus)
        for x0 in (3,8,12): sp(x0,11,(220,90,120,255))
    elif a=="haxhatt":
        for i in range(9):
            y=3+i; w=i//2
            rect(8-w,y,8+w,y,col)
        rect(1,12,14,13,mork); rect(5,10,11,11,(214,182,86,255))
    elif a=="tomteluva":
        for i in range(7):
            y=4+i; w=i//2; lut=i//3
            rect(9-w-lut,y,10+w-lut,y,col)
        rect(2,11,13,13,(240,240,240,255)); rect(10,3,12,5,(240,240,240,255))
    elif a=="doktorsrock":
        rect(3,4,12,13,col); rect(7,4,8,13,mork)
        sp(4,4,mork); sp(5,5,mork); sp(11,4,mork); sp(10,5,mork)
        rect(9,7,11,7,(210,60,60,255)); rect(10,6,10,8,(210,60,60,255))
    elif a=="rustning":
        rect(3,5,12,12,col); rect(2,5,4,7,col); rect(11,5,13,7,col)
        rect(6,5,9,5,T)                               # halsurtag ur plåten
        rect(4,6,11,6,ljus); rect(3,11,12,12,mork)
    elif a=="energisvard":
        rect(7,1,8,10,ljus); rect(6,2,6,9,col); rect(9,2,9,9,col)
        rect(5,11,10,11,(96,96,108,255)); rect(7,12,8,15,(58,58,68,255))
    elif a=="rymdmantel":
        for y in range(3,14): rect(4,y,11,y,col)
        rect(4,3,11,3,ljus)
        for sx,sy in ((5,5),(9,6),(7,9),(10,11),(5,12)):
            sp(sx,sy,(235,235,255,255))
    elif a=="mantel":
        for y in range(3,14):
            wsp=1 if y<5 else 0
            rect(3+wsp,y,12-wsp,y,col)
        rect(4,3,11,3,ljus)
        for y in range(3,14): sp(3,y,mork); sp(12,y,mork)
        for x in range(3,13):
            if x%3==0: rect(x,5,x,13,sh(col,0.86))
    elif a=="vagn":
        rect(2,5,13,10,col); rect(2,5,13,5,ljus); rect(2,10,13,10,mork)
        for x in range(3,13):
            if x%3==0: rect(x,6,x,9,sh(col,0.86))
        for wx in (4,11):
            rect(wx-1,11,wx+1,14,(72,60,48,255))
            sp(wx,12,(140,124,100,255)); sp(wx,13,(140,124,100,255))
    elif a=="tossor":
        for (bx,by) in ((2,4),(9,4),(2,10),(9,10)):
            for y in range(by,by+4):
                for x in range(bx,bx+5):
                    if y==by and x in (bx,bx+4): continue
                    sp(x,y,col)
            rect(bx+1,by,bx+3,by,ljus); rect(bx,by+3,bx+4,by+3,mork)
    else:
        rect(3,5,12,11,col); rect(3,5,12,5,ljus); rect(3,11,12,11,mork)
    write_png(path,S,S,px)

def icon_treat():
    """Kattgodis: liten fiskformad godbit."""
    S=16; T=(0,0,0,0); px=[[T]*S for _ in range(S)]
    BODY=(226,150,92,255); DARK=(186,116,66,255); LIGHT=(242,190,140,255)
    def sp(x,y,c):
        if 0<=x<S and 0<=y<S: px[y][x]=c
    for y in range(6,11):
        for x in range(4,12): sp(x,y,BODY)
    for x in range(4,12): sp(x,6,LIGHT); sp(x,10,DARK)
    for k in range(3):                      # stjärtfena
        for y in range(6+k,11-k): sp(12+k,y,BODY)
    sp(6,8,DARK)                            # öga
    for x in range(5,11):
        if x%2==0: sp(x,8,DARK)             # mönster
    write_png(f"{RP}/textures/items/pc_godis.png",S,S,px)

def icon_bok():
    """Kattboken: en uppslagen bok med ett kattöra över kanten.

    En vanlig bokikon drunknar bland vaniljas böcker och skrivbordsböcker.
    Örat sticker upp ovanför pärmen och gör att man ser VILKEN bok det är i en
    full hotbar, vilket är hela poängen med en guide man ska hitta."""
    S=16; T=(0,0,0,0); px=[[T]*S for _ in range(S)]
    PARM=(150,62,58,255); PARM_M=(108,42,40,255)
    SIDA=(238,232,214,255); SIDA_M=(196,188,168,255); TEXT=(120,112,98,255)
    ORA=(196,150,120,255); ORA_IN=(232,178,166,255)
    def sp(x,y,c):
        if 0<=x<S and 0<=y<S: px[y][x]=c
    def rect(x0,y0,w,h,c):
        for y in range(y0,y0+h):
            for x in range(x0,x0+w): sp(x,y,c)
    # ÖRONEN FÖRST, så pärmen målar över deras nederkant och de sitter BAKOM
    # boken i stället för att sväva ovanför den.
    for ox in (3,10):
        # SMALNAR AV UPPÅT. Två raka 3x4-rutor läste som skorstenar på ett tak,
        # inte som öron — och örat är det enda som skiljer den här boken från
        # vaniljas i en full hotbar.
        rect(ox,3,3,3,ORA); rect(ox+1,2,1,1,ORA)
        rect(ox+1,4,1,2,ORA_IN)
    rect(1,5,14,10,PARM_M)                  # pärm
    rect(2,6,12,8,PARM)
    rect(2,6,5,8,SIDA); rect(9,6,5,8,SIDA)  # två uppslagna sidor
    rect(2,13,5,1,SIDA_M); rect(9,13,5,1,SIDA_M)
    rect(7,5,2,10,PARM_M)                   # ryggen
    for y in (8,10):                        # textrader
        rect(3,y,3,1,TEXT); rect(10,y,3,1,TEXT)
    write_png(f"{RP}/textures/items/pc_kattbok.png",S,S,px)


# ---------------------------------------------------------------- allt övrigt
def build_rest():
    # render controllers
    # Katten ritas ur pälsarket (Texture.pals), plaggen ur atlaset (Texture.default).
    rcs={"controller.render.katt":{"geometry":"Geometry.default",
         "materials":[{"*":"Material.default"}],"textures":["Texture.pals"]}}
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
        desc["textures"]={"default":"textures/entity/plagg","pals":f"textures/entity/{_kort}_pals"}
        desc["render_controllers"]=["controller.render.katt"]+[f"controller.render.katt_{a}" for a in ACC]
        # animationer: gångcykel, svanssvaj, huvudet följer spelaren, hopkurad sittpose
        desc["animations"]={
            "walk":"animation.katt.walk", "look":"animation.katt.look",
            "tail":"animation.katt.tail", "sit":"animation.katt.sit",
            "ctrl":"controller.animation.katt.move"}
        desc["animations"]["sova"]="animation.katt.sova"
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
                    ev[evn]["remove"]={"component_groups":["mjau:sittable","mjau:carted","mjau:jagar","mjau:fri","mjau:sovdags","mjau:bladbararen"]}
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
                    ev[evn].setdefault("remove",{}).setdefault("component_groups",[]).extend(["mjau:sittable","mjau:saddled","mjau:jagar","mjau:fri","mjau:sovdags","mjau:bladbararen"])
                inter.append(entry(f"mjau:{a}_{slug}",evn,cfg["sound"]))   # namnrymd krävs för EGNA föremål
        inter.append(entry("saddle","mjau:on_sadel_1","saddle"))
        # SPINNA/MATA: godis på tam katt höjer humöret
        inter.append(entry("mjau:godis","mjau:on_matad","eat"))
        ev["mjau:on_matad"]={"set_property":{"mjau:humor":2}}
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
        katter.append({"id": f"mjau:{c}", "biom": biom})
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
    print(f"{len(ACC)} plagg · {n} geometrier · {items} föremål · {inters} interaktioner")
    for a,cfg in ACC.items():
        print(f"  {a:9s} {len(cfg['colors'])} färger  ({cfg['label']})")
