#!/usr/bin/env python3
"""Genererar Purrfect Companions block: kattbädd och garnnystan.

Som build_accessories.py: en definition nedan → geometri, textur, block-JSON,
blocks.json, terrain_texture.json, recept och språksträng.

Katterna söker sig till blocken via minecraft:behavior.move_to_block (sätts på
entiteterna av det här skriptet, med entydig prioritet).
"""
import json, os, zlib, struct, glob

BASE = "/opt/purrfect-companions"; BP = f"{BASE}/PurrfectCompanions_BP"; RP = f"{BASE}/PurrfectCompanions_RP"

TV_SCREEN = (
    "............",
    ".......YY...",
    "......YEK...",
    "...YYYYYO...",
    "..YYYYYY....",
    ".Y..WWW.....",
    "ggggLLgggggg",
    "GGGGGGGGGGGG",
)
TV_COLORS = {
    ".": (103, 194, 220, 255), "Y": (255, 214, 71, 255),
    "E": (27, 31, 34, 255), "K": (255, 243, 171, 255),
    "O": (237, 117, 50, 255), "W": (224, 157, 39, 255),
    "L": (100, 74, 49, 255), "g": (109, 178, 89, 255),
    "G": (55, 117, 75, 255),
}


def tv_screen_pixel(x, y):
    # The front face starts after the one-pixel depth in the box UV layout.
    return TV_COLORS[TV_SCREEN[(y - 1) % 8][(x - 1) % 12]]


# Octagonal tube cross-section, shared by the cloth body and both end hoops.
TUNNEL_PROFILE = [(-4,0,8,1), (-6,1,2,2), (4,1,2,2),
                  (-7,3,1,5), (6,3,1,5), (-6,8,2,2), (4,8,2,2), (-4,10,8,1)]


BLOCKS = {
 "fonsterbadd": dict(
   name="Window Perch",name_sv="Fönsterbädd",
   # Raised cushion with a wooden frame, four legs and a low back rail.
   cubes=[([-12,13,-16],[24,1,24],"tra"),([-11,14,-15],[22,2,22],"kudde"),
          ([-12,14,6],[24,5,2],"tra"),
          ([-12,14,-16],[1,3,22],"tra"),([11,14,-16],[1,3,22],"tra")]
         + [([x,0,z],[3,13,3],"tra") for x in (-11,8) for z in (-15,4)]
         + [([-8,4,4],[16,2,2],"tra"),([-8,4,-14],[16,2,2],"tra")],
   material={
     "tra":lambda x,y:(157,106,65,255) if (y+x//5)%5 else (112,72,44,255),
     "kudde":lambda x,y:(131,187,199,255) if (x+y)%7 else (177,217,221,255)},
   base=(157,106,65),accent=(131,187,199),sound="wood",height=19,
   collision_height=16,selection_height=16,atlas=(128,128),
   recipe=dict(pattern=["WWW","PPP","S S"],key={
     "W":{"item":"minecraft:light_blue_wool"},"P":{"item":"minecraft:planks"},
     "S":{"item":"minecraft:stick"}},unlock=[{"item":"minecraft:light_blue_wool"}])),
 "sovkorg": dict(
   name="Basket for Two",
   cubes=[([-14,0,-13],[28,1,26],"flata"),
          ([-14,1,-13],[2,5,26],"flata"),([12,1,-13],[2,5,26],"flata"),
          ([-12,1,11],[24,5,2],"flata"),([-12,1,-13],[24,1,2],"flata"),
          ([-12,1,-11],[12,2,22],"rosa"),([0,1,-11],[12,2,22],"bla")],
   material={
     "flata": lambda x,y: (174,122,69,255) if (x+(y//2)%2*3)%6<4 and y%3 else (124,81,45,255),
     "rosa": lambda x,y: (219,154,167,255) if y%4 else (234,182,190,255),
     "bla": lambda x,y: (122,177,183,255) if y%4 else (159,206,207,255)},
   base=(174,122,69),accent=(234,182,190),sound="wood",height=6,collision_height=3,atlas=(128,128),
   recipe=dict(pattern=["S S","WRW","PPP"],key={
     "S":{"item":"minecraft:stick"},"W":{"item":"minecraft:white_wool"},
     "R":{"item":"minecraft:pink_wool"},"P":{"item":"minecraft:planks"}},
     unlock=[{"item":"minecraft:white_wool"}])),
 "kattspa": dict(
   name="Cat Spa",
   # White bath with visible water, folded towel and a separate soap dispenser.
   cubes=[([-7,0,-7],[14,1,14],"keramik"),
          ([-7,1,-7],[14,3,2],"keramik"), ([-7,1,5],[14,3,2],"keramik"),
          ([-7,1,-5],[2,3,10],"keramik"), ([5,1,-5],[2,3,10],"keramik"),
          ([-5,1,-5],[10,1,10],"vatten"),
          ([-5,4,-7],[5,1,4],"handduk"), ([-5,2,-7.5],[5,2,0.5],"handduk"),
          ([3,4,4],[2,3,2],"tval"), ([3.5,7,4.5],[1,1,1],"metall"),
          ([2.5,8,4.5],[2,0.5,1],"metall"),
          ([-3,2,1],[2,1,2],"skum"), ([-2,2,3],[1,1,1],"skum")],
   material={
     "keramik": lambda x,y: (232,238,235,255),
     "vatten": lambda x,y: (83,187,214,255) if (x+2*y)%11 else (165,229,236,255),
     "handduk": lambda x,y: (169,120,190,255) if y%4 else (213,181,224,255),
     "tval": lambda x,y: (103,186,149,255),
     "metall": lambda x,y: (111,122,129,255),
     "skum": lambda x,y: (248,252,250,255),
   },
   base=(92,142,154), accent=(160,222,222), sound="water",
   recipe=dict(pattern=["BWB","SPS","PPP"],
     key={"B":{"item":"minecraft:bowl"},"W":{"item":"minecraft:water_bucket"},
          "S":{"item":"minecraft:white_wool"},"P":{"item":"minecraft:planks"}},
     unlock=[{"item":"minecraft:water_bucket"}]),
   height=9,collision_height=1),
 "katt_tv": dict(
   name="Cat TV",
   # Wide dark television with a bird channel and separate physical controls.
   cubes=[([-6,0,-3],[12,1,6],"ram"), ([-2,1,-1],[4,2,2],"ram"),
          ([-8,3,-1],[16,10,3],"ram"),
          ([-7,4,-2],[12,8,1],"skarm"),
          ([6,9,-2],[1,1,1],"knapp"), ([6,7,-2],[1,1,1],"knapp"),
          ([6,4,-2],[1,1,1],"lampa")],
   material={
     "ram": lambda x,y: (40,43,48,255),
     "skarm": tv_screen_pixel,
     "knapp": lambda x,y: (190,198,205,255),
     "lampa": lambda x,y: (105,231,117,255),
   },
   base=(78,88,104), accent=(92,180,196), sound="stone",
   recipe=dict(pattern=["GIG","IRI","PPP"],
     key={"G":{"item":"minecraft:glass_pane"},"I":{"item":"minecraft:iron_ingot"},
          "R":{"item":"minecraft:redstone"},"P":{"item":"minecraft:planks"}},
     unlock=[{"item":"minecraft:glass_pane"}]),
   height=13,collision_origin=[-8,0,-3],collision_size=[16,13,6]),
 "gomstalle": dict(
   name="Cat Hideaway",
   # Soft enclosed den with a broad entrance, stepped roof and a pink cushion.
   cubes=[([-7,0,-7],[14,1,14],"kant"),
          ([-7,1,-7],[2,7,14],"tyg"), ([5,1,-7],[2,7,14],"tyg"),
          ([-5,1,5],[10,7,2],"insida"),
          ([-6,8,-7],[12,2,14],"tyg"), ([-4,10,-7],[8,1,14],"tyg"),
          ([-7,1,-7.5],[2,7,0.5],"kant"), ([5,1,-7.5],[2,7,0.5],"kant"),
          ([-5,8,-7.5],[10,1,0.5],"kant"),
          ([-5,1,-6],[10,1,10],"kudde"), ([-4,2,1],[8,1,3],"kudde")],
   material={
     "tyg": lambda x,y: (107,161,139,255) if y%8 else (118,172,150,255),
     "kant": lambda x,y: (224,231,219,255),
     "insida": lambda x,y: (63,95,83,255),
     "kudde": lambda x,y: (219,137,154,255),
   },
   base=(126,100,148), accent=(190,148,190), sound="wood",
   recipe=dict(pattern=["W W","W W","PPP"],
     key={"W":{"item":"minecraft:white_wool"},"P":{"item":"minecraft:planks"}},
     unlock=[{"item":"minecraft:white_wool"}]),
   height=11),
 "leksakslada": dict(
   name="Toy Box",
   # Open wooden box with two rounded voxel balls and a yellow toy fish.
   cubes=[([-7,0,-6],[14,1,12],"insida"),
          ([-7,1,-6],[14,3,1],"tra"), ([-7,1,5],[14,3,1],"tra"),
          ([-7,1,-5],[1,3,10],"tra"), ([6,1,-5],[1,3,10],"tra"),
          ([-7,4,-6],[14,1,1],"kant"), ([-7,4,5],[14,1,1],"kant"),
          ([-7,4,-5],[1,1,10],"kant"), ([6,4,-5],[1,1,10],"kant"),
          ([-5,3,-3],[4,4,4],"rod"), ([-4,2,-2],[2,6,2],"rod"),
          ([-4,4,-4],[2,2,6],"rod"), ([-6,4,-2],[6,2,2],"rod"),
          ([1,3,0],[4,4,4],"bla"), ([2,2,1],[2,6,2],"bla"),
          ([2,4,-1],[2,2,6],"bla"), ([0,4,1],[6,2,2],"bla"),
          ([1,5,-4],[4,2,1],"gul"), ([0,4,-4],[1,4,1],"gul"),
          ([4,6,-4.25],[0.5,0.5,0.25],"oga")],
   material={
     "tra": lambda x,y: (166,113,71,255) if y%3 else (136,87,54,255),
     "kant": lambda x,y: (225,209,174,255),
     "insida": lambda x,y: (98,72,52,255),
     "rod": lambda x,y: (222,80,104,255) if y%3 else (255,162,169,255),
     "bla": lambda x,y: (52,160,196,255) if y%3 else (139,221,232,255),
     "gul": lambda x,y: (251,210,75,255),
     "oga": lambda x,y: (31,34,39,255),
   },
   base=(196,138,96), accent=(244,188,104), sound="wood",
   recipe=dict(pattern=["PPP","PBP","PPP"],
     key={"P":{"item":"minecraft:planks"},"B":{"item":"minecraft:slime_ball"}},
     unlock=[{"item":"minecraft:slime_ball"}]),
   height=8),
 "kattfontan": dict(
   name="Cat Fountain",
   # låg piedestal med skål och vattenyta i mitten
   cubes=[([-7,0,-7],[14,1,14],"keramik"),
          ([-7,1,-7],[14,3,1],"keramik"), ([-7,1,6],[14,3,1],"keramik"),
          ([-7,1,-6],[1,3,12],"keramik"), ([6,1,-6],[1,3,12],"keramik"),
          ([-6,1,-6],[12,1,12],"vatten"),
          ([-2,2,1],[4,5,4],"keramik"), ([-2,7,-1],[4,1,6],"keramik"),
          ([-1,7,-1.25],[2,0.5,0.25],"metall"),
          ([-1,2,-1],[2,5,1],"flode")],
   material={
     "keramik": lambda x,y: (220,232,234,255),
     "vatten": lambda x,y: (48,174,214,255) if (x+2*y)%11 else (144,234,244,255),
     "flode": lambda x,y: (84,197,229,255) if x%2 else (172,237,244,255),
     "metall": lambda x,y: (117,135,144,255),
   },
   base=(116,132,146), accent=(82,174,214), sound="stone",
   recipe=dict(pattern=[" I ","SBS","PPP"],
     key={"I":{"item":"minecraft:iron_ingot"},"S":{"item":"minecraft:stone"},
          "B":{"item":"minecraft:bowl"},"P":{"item":"minecraft:planks"}},
     unlock=[{"item":"minecraft:bowl"}]),
   height=8),
 "klosbrada": dict(
   name="Scratching Board",
   # A low voxel ramp: pale ribbed sisal bordered by wood, with rear supports.
   cubes=[([-7,0,-7],[14,1,14],"tra"),
          ([-6,1,5],[2,5,2],"tra"), ([4,1,5],[2,5,2],"tra")]
         + [([x,1+i,-6+2*i],[2,1,2],"tra") for i in range(6) for x in (-7,5)]
         + [([-5,1+i,-6+2*i],[10,1,2],"sisal") for i in range(6)],
   material={
     "tra": lambda x,y: (130,83,54,255) if y%4 else (155,105,67,255),
     "sisal": lambda x,y: (231,220,183,255) if x%3 else (172,158,121,255),
   },
   base=(174,126,104), accent=(214,176,126), sound="wood",
   recipe=dict(pattern=["SWS","SWS","PPP"],
     key={"S":{"item":"minecraft:string"},"W":{"item":"minecraft:white_wool"},
          "P":{"item":"minecraft:planks"}},
     unlock=[{"item":"minecraft:string"}]),
   height=8,collision_width=14),
 "kattunnel": dict(
   name="Cat Tunnel",
   genomgang=True,
   # Enclosed fabric tube with octagonal openings and contrasting end hoops.
   cubes=[([x,y,-6],[w,h,12],"tyg") for x,y,w,h in TUNNEL_PROFILE]
         + [([x,y,z],[w,h,1],"ring") for z in (-7,6) for x,y,w,h in TUNNEL_PROFILE],
   material={
     "tyg": lambda x,y: (49,144,165,255) if x%6 else (68,167,183,255),
     "ring": lambda x,y: (228,220,183,255),
   },
   base=(104,128,156), accent=(164,192,214), sound="cloth",
   recipe=dict(pattern=["W W","WPW","PPP"],
     key={"W":{"item":"minecraft:white_wool"},"P":{"item":"minecraft:planks"}},
     unlock=[{"item":"minecraft:white_wool"}]),
   height=11),
 "hangmatta": dict(
   name="Cat Hammock",
   # två stolpar, övre fästen och en tydligt nedsjunken tygslinga
   cubes=[([-8,0,-6],[3,1,12],"tra"), ([5,0,-6],[3,1,12],"tra"),
          ([-7,1,-1],[2,9,2],"tra"), ([5,1,-1],[2,9,2],"tra"),
          ([-5,7,-5],[1,1,10],"tyg"), ([4,7,-5],[1,1,10],"tyg"),
          ([-4,6,-5],[1,1,10],"tyg"), ([3,6,-5],[1,1,10],"tyg"),
          ([-3,5,-5],[1,1,10],"tyg"), ([2,5,-5],[1,1,10],"tyg"),
          ([-2,4,-5],[4,1,10],"tyg"),
          ([-6,8,-5],[1,1,10],"rep"), ([5,8,-5],[1,1,10],"rep"),
          ([-2,5,1],[4,1,3],"kudde")],
   material={
     "tra": lambda x,y: (208,184,144,255),
     "tyg": lambda x,y: (198,78,120,255) if y%5 else (233,151,175,255),
     "rep": lambda x,y: (236,226,197,255),
     "kudde": lambda x,y: (241,224,226,255),
   },
   base=(126,82,112), accent=(204,132,166), sound="cloth",
   recipe=dict(pattern=["W W","WWW","L L"],
     key={"W":{"item":"minecraft:white_wool"},"L":{"item":"minecraft:leather"}},
     unlock=[{"item":"minecraft:white_wool"}]),
   height=10),
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
   # LJUS BJÖRK, inte mörkt trä. Skålens kantfärg härleds som bas*0,72 och
   # blev (135,106,69) — fyra enheter från vanillas jordblock, och kanten är
   # 43 % av duken. Samma jordmoln som kattluckan hade när man slog sönder den.
   base=(214,190,150), accent=(120,78,52), sound="wood",
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
 "podium": dict(
   name="Show Podium",
   # UTSTÄLLNINGSPODIET (3.50.0): en låg scen med röd matta, en rosettstolpe
   # och två skyltpelare. Katten ställs på podiet och domaren (interaktionen)
   # ger poäng för ras, plagg, humör, hälsa och ålder.
   cubes=[([-8,0,-8],[16,2,16],"tra"),            # scengolv
          ([-7,2,-7],[14,1,14],"matta"),          # röda mattan
          ([-8,2,-8],[1,3,1],"stolpe"),           # fyra hörnstolpar
          ([7,2,-8],[1,3,1],"stolpe"),
          ([-8,2,7],[1,3,1],"stolpe"),
          ([7,2,7],[1,3,1],"stolpe"),
          ([-2,3,-8],[4,3,1],"rosett"),           # rosetten på framkanten
          ([-1,6,-8],[2,2,1],"guld")],            # guldknoppen över den
   material={
     "tra":     lambda x,y: (108,78,50,255) if y % 5 == 0 else (146,110,72,255),
     "matta":   lambda x,y: (176,44,40,255) if (x + y) % 3 else (204,58,54,255),
     "stolpe":  lambda x,y: (226,198,120,255) if y % 3 else (186,156,84,255),
     "rosett":  lambda x,y: (238,208,110,255) if (x + y) % 4 else (204,166,70,255),
     "guld":    lambda x,y: (246,222,140,255) if (x + y) % 2 else (214,180,86,255),
   },
   base=(146,110,72), accent=(204,58,54), sound="wood",
   recipe=dict(pattern=["WWW","PPP","PPP"],
     key={"W":{"item":"minecraft:red_wool"},"P":{"item":"minecraft:planks"}},
     unlock=[{"item":"minecraft:red_wool"}]),
   height=8),
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
   # FÄRGEN VAR PROBLEMET, inte modellen. (142,104,66) ligger åtta enheter från
   # vanillas jordblock, och HELA texturen var den tonen — så när man slog
   # sönder luckan blev partikelmolnet ett brunt jordmoln. Ungarna sa "den har
   # jord-effekt när man tar bort den" och hade helt rätt.
   #
   # Karmen är nu mörkare och kallare än jord, och SJÄLVA LUCKAN är nästan vit.
   # Partiklarna plockas ur hela duken, så en ljus lucka ger ett ljust moln som
   # ingen förväxlar med jord.
   base=(120,92,74), accent=(232,226,214), sound="wood",
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

def packa_kuber(kuber, duk=DUK):
    rutor = [(i, 2 * (k[1][2] + k[1][0]), k[1][2] + k[1][1]) for i, k in enumerate(kuber)]
    x = y = radhojd = 0
    uv = {}
    for i, w, h in sorted(rutor, key=lambda r: -r[2]):
        w, h = int(w + 0.999), int(h + 0.999)
        if x + w > duk[0]:
            x, y, radhojd = 0, y + radhojd, 0
        if y + h > duk[1]:
            raise SystemExit(f"blockets UV-yta räcker inte till ({DUK[0]}x{DUK[1]})")
        uv[i] = [x, y]
        x += w
        radhojd = max(radhojd, h)
    return uv


def mala_ytor(bid, cfg, uv):
    """Målar en duk där varje kub får sitt materials mönster i sin egen ruta."""
    W, H = cfg.get("atlas", DUK)
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

def animated_texture(bid, cfg):
    """Square flipbook frames; only water or screen pixels change."""
    frames = []
    for phase in range(4):
        animated = dict(cfg, material=dict(cfg["material"]))
        if bid == "katt_tv":
            def screen(x, y, phase=phase):
                x, y = (x - 1) % 12, (y - 1) % 8
                # The bird flaps its wing and blinks; scenery stays still.
                if phase in (1, 2) and (x, y) in ((5, 3), (6, 3)):
                    return TV_COLORS["W"]
                if phase == 2 and TV_SCREEN[y][x] == "E":
                    return TV_COLORS["W"]
                return TV_COLORS[TV_SCREEN[y][x]]
            animated["material"]["skarm"] = screen
        else:
            animated["material"]["vatten"] = lambda x,y,p=phase: (
                (165,229,236,255) if (x+2*y+p*3)%11 == 0 else (83,187,214,255))
        w, h, pixels = mala_ytor(bid, animated, packa_kuber(cfg["cubes"], cfg.get("atlas", DUK)))
        pixels += [[(0,0,0,0)] * w for _ in range(w-h)]
        frames.extend(pixels)
        if phase == 0:
            write_png(f"{RP}/textures/blocks/pc_{bid}.png", w, w, pixels)
    write_png(f"{RP}/textures/blocks/pc_{bid}_animated.png", w, w*4, frames)


def texture(bid, cfg):
    """16x16 blocktextur: bas med vävt/nystat mönster.

    Block som anger MATERIAL per kub målas i stället på den packade duken, där
    varje kub får sin egen ruta — det är enda sättet att låta ett rep och en
    matta se olika ut på samma block."""
    if bid in ("kattspa", "katt_tv"):
        animated_texture(bid, cfg)
        return
    if "material" in cfg:
        w, h, px = mala_ytor(bid, cfg, packa_kuber(cfg["cubes"], cfg.get("atlas", DUK)))
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
        # KARM RUNT OM, LUCKA I MITTEN. Den gamla varianten strök bara vartannat
        # streck i accentfärgen över en brun platta — det läste som en planka,
        # inte som en lucka man kan gå igenom.
        for y in range(S):
            for x in range(S):
                if x < 2 or x > 13 or y < 2 or y > 14:
                    px[y][x] = dark                               # karm
                else:
                    px[y][x] = acc                                # själva luckan
        # GÅNGJÄRNET ÖVERST är det som gör att luckan läser som en LUCKA: utan
        # det är den ljusa ytan bara ett hål i en brun ram.
        for x in range(3, 13):
            px[2][x] = dark
        # KATTHÅLET. En mörk båge nedtill i luckan — samma silhuett som spelaren
        # just jagat en katt igenom. Formen ritas RAD FÖR RAD i stället för med
        # ett avståndsuttryck: uttrycket gav en oregelbunden klump som såg ut som
        # en fläck, inte som ett hål, och på 16x16 texlar syns skillnaden direkt.
        hal = tuple(int(c * 0.55) for c in cfg["base"]) + (255,)
        for y, (x0, x1) in zip(range(8, 14),
                               [(6, 9), (5, 10), (5, 10), (5, 10), (5, 10), (5, 10)]):
            for x in range(x0, x1 + 1):
                px[y][x] = hal
    if bid == "kattoa":
        for y in range(S):
            for x in range(S):
                d2 = max(abs(x - 7.5), abs(y - 7.5))
                if d2 > 6: px[y][x] = dark                        # kant
                # STRÖT SKA VARA KORN, inte ränder. (x*7+y*3)%5 ger diagonala
                # linjer; det såg ut som strö bara så länge garnets felaktiga
                # brus låg ovanpå och bröt upp dem. En hash av båda koordinaterna
                # sprider kornen utan mönster.
                elif (x * 37 + y * 101 + x * y * 7) % 11 < 4: px[y][x] = acc
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
    if bid == "garnnystan":
        # DET HÄR VAR ETT else PÅ KATTBÄDDEN, inte ett eget block. Garnets
        # trådmönster målades alltså över SJU av åtta block: matskålen, lådan,
        # kattlådan, klösträdet, dammen och kattluckan fick alla samma
        # slumpmässiga prickar ovanpå sitt eget mönster. Det syntes som "brus"
        # och togs för stil, men luckans katthål försvann i det, och en enfärgad
        # brun lucka full av prickar är precis vad barnen kallade jord.
        for y in range(S):                       # garntrådar på tvären
            for x in range(S):
                if (x * 2 + y) % 5 == 0: px[y][x] = acc
                if (y * 2 - x) % 7 == 0: px[y][x] = dark
    if bid == "klosbrada":
        for y in range(S):
            for x in range(S):
                if (x * 3 + y) % 4 == 0: px[y][x] = acc
                elif y % 5 == 0: px[y][x] = dark
    if bid == "kattunnel":
        for y in range(S):
            for x in range(S):
                if (x + y) % 4 == 0: px[y][x] = acc
                elif y % 6 == 0: px[y][x] = dark
    if bid == "katt_tv":
        for y in range(S):
            for x in range(S):
                if 3 <= x <= 12 and 3 <= y <= 11:
                    px[y][x] = (52, 124 + (x * 7) % 50, 156 + (y * 5) % 45, 255)
                elif (x + y) % 5 == 0:
                    px[y][x] = dark
    if bid == "gomstalle":
        for y in range(S):
            for x in range(S):
                if (x * 2 + y) % 4 == 0: px[y][x] = acc
                elif y % 5 == 0: px[y][x] = dark
    if bid == "leksakslada":
        for y in range(S):
            for x in range(S):
                if y in (3, 12) or x in (3, 12): px[y][x] = dark
                elif (x + y) % 5 == 0: px[y][x] = acc
    if bid == "kattspa":
        for y in range(S):
            for x in range(S):
                if 3 <= x <= 12 and 3 <= y <= 12:
                    px[y][x] = (112, 196 + (x % 3) * 8, 218, 255)
                elif (x + y) % 4 == 0:
                    px[y][x] = acc
    write_png(f"{RP}/textures/blocks/pc_{bid}.png", S, S, px)


def build():
    for d in ("blocks", "recipes"): os.makedirs(f"{BP}/{d}", exist_ok=True)
    for d in ("textures/blocks", "models/blocks"): os.makedirs(f"{RP}/{d}", exist_ok=True)

    flipbook_path = f"{RP}/textures/flipbook_textures.json"
    flipbooks = json.load(open(flipbook_path)) if os.path.exists(flipbook_path) else []
    flipbooks = [entry for entry in flipbooks if entry.get("atlas_tile") not in ("pc_kattspa", "pc_katt_tv")]
    for bid in ("kattspa", "katt_tv"):
        flipbooks.append({"flipbook_texture": f"textures/blocks/pc_{bid}_animated",
                          "atlas_tile": f"pc_{bid}", "ticks_per_frame": 8,
                          "frames": [0,1,2,3], "blend_frames": False})
    json.dump(flipbooks, open(flipbook_path, "w"), indent=2)

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
        _uv = packa_kuber(cfg["cubes"], cfg.get("atlas", DUK)) if _flera else None
        json.dump({"format_version": "1.16.0", "minecraft:geometry": [{
            "description": {"identifier": f"geometry.{bid}",
                            "texture_width": DUK[0] if _flera else 16,
                            "texture_height": (DUK[0] if bid in ("kattspa", "katt_tv") else cfg.get("atlas", DUK)[1]) if _flera else 16},
            "bones": [{"name": bid, "pivot": [0, 0, 0],
                       "cubes": [{"origin": k[0], "size": k[1],
                                  "uv": _uv[i] if _flera else [0, 0]}
                                 for i, k in enumerate(cfg["cubes"])]}]}]},
            open(f"{RP}/models/blocks/{bid}.geo.json", "w"), indent=2)

        h = cfg["height"]
        json.dump({"format_version": "1.20.50", "minecraft:block": {
            "description": {"identifier": f"mjau:{bid}", "menu_category": {"category": "nature"},
                **({"traits":{"minecraft:placement_direction":{
                    "enabled_states":["minecraft:cardinal_direction"],"y_rotation_offset":0}}}
                   if bid in ("sovkorg","kattspa","katt_tv","klosbrada","fonsterbadd","kattfontan") else {})},
            **({"permutations":[{"condition":f"q.block_state('minecraft:cardinal_direction') == '{direction}'",
                "components":{"minecraft:transformation":{"rotation":[0,angle,0]}}}
                for direction,angle in (("south",0),("west",-90),("north",180),("east",90))]}
               if bid in ("sovkorg","kattspa","katt_tv","klosbrada","fonsterbadd","kattfontan") else {}),
            "components": {
                "minecraft:geometry": f"geometry.{bid}",
                # opaque på gles modell cullar grannblockens ytor -> "grop i golvet"
                # (2.6.1-läxan för kattluckan, gällde förstås ALLA glesa modeller)
                "minecraft:material_instances": {"*": {"texture": f"pc_{bid}", "render_method": "alpha_test"}},
                # KATTLUCKAN SKA GÅ ATT GÅ IGENOM — den är en lucka. Filen stod
                # handrättad till false och generatorn hade skrivit över den vid
                # nästa körning; nu säger blocket det själv.
                "minecraft:collision_box": (False if cfg.get("genomgang")
                                            else {"origin": cfg.get("collision_origin",[-cfg.get("collision_width",16)//2, 0, -cfg.get("collision_width",16)//2]), "size": cfg.get("collision_size",[cfg.get("collision_width",16), cfg.get("collision_height", h), cfg.get("collision_width",16)])}),
                "minecraft:selection_box": {"origin": [-8, 0, -8], "size": [16, cfg.get("selection_height",h), 16]},
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

    # Explicit translations for new blocks; preserve existing Swedish entries.
    for pack in ("PurrfectCompanions_BP", "PurrfectCompanions_RP"):
        lp=f"{BASE}/{pack}/texts/sv_SE.lang"
        translations={f"tile.mjau:{bid}.name":cfg["name_sv"] for bid,cfg in BLOCKS.items() if "name_sv" in cfg}
        lines=open(lp,encoding="utf-8").read().splitlines()
        lines=[line for line in lines if line.split("=",1)[0] not in translations]
        open(lp,"w",encoding="utf-8").write("\n".join(lines+[f"{key}={value}" for key,value in translations.items()])+"\n")

    # katterna söker sig till bädd, nystan och matskål — men bara av FRI VILJA:
    # beteendet bor i mjau:fri, som tas bort medan en spelare rider (annars
    # "styr katten sig själv", sett på Xbox).
    targets = [f"mjau:{b}" for b in BLOCKS if b not in ("sovkorg","kattspa","katt_tv","klosbrada","fonsterbadd","kattfontan")]
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
            if namn in SKYDDADE or namn.startswith("mjau:mobel_"):
                continue
            for k, v in bucket.items():
                if k in P and isinstance(v, dict): v["priority"] = P[k]
        json.dump(d, open(f, "w"), indent=2)

    return len(BLOCKS), targets


if __name__ == "__main__":
    n, t = build()
    print(f"{n} block byggda: {', '.join(t)}")
    print("katterna söker sig till dem via behavior.move_to_block (prio 12)")
