#!/usr/bin/env python3
"""Bygger Cat Haven — en färdig startvärld (.mcworld) för Purrfect Companions.

Världen genereras deterministiskt: byggnaderna författas som .mcstructure-filer
(NBT via tools/gametest/nbt.py — skyltar, kistinnehåll och välkomstboken kräver
block entities som kommandon inte kan skapa), varefter Bedrock-servern bygger
terräng, laddar strukturerna och placerar katterna via kommandon på stdin —
samma mekanik som purrfect-test steg 4. Resultatet packas som .mcworld med
paketen inbäddade: en fil, ett tryck, inga paket att aktivera för hand.

    python3 build_world.py public /tmp/ut     # engelsk källa ("Cat Haven")
    python3 build_world.py private /tmp/ut    # familjens ("Kattgården")

Källtexterna är ENGELSKA. Familjevarianten får svenska texter och familjens
kattnamn här — samma regel som make_variant: svenska/privata namn hamnar
aldrig i det publika bygget.
"""
import json, os, shutil, subprocess, sys, time, zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{BASE}/tools/gametest")
import nbt

V = nbt.Val
def B(v):  return V(nbt.TAG_BYTE, v)
def SH(v): return V(nbt.TAG_SHORT, v)
def I(v):  return V(nbt.TAG_INT, v)
def S(v):  return V(nbt.TAG_STRING, v)
def C(d):  return V(nbt.TAG_COMPOUND, d)
def L(tag, items): return V(nbt.TAG_LIST, (tag, items))

# Blockpalettens version MÅSTE matcha serverns riktiga (1.26.40 = 18491392).
# Med gametest-arenans gamla 1.21-stämpel renderade CUSTOM-block placerade via
# structure load nedsjunkna ("groparna") — vanilla-block uppgraderas av spelets
# schemakedja, custom-block har ingen och lämnas i odefinierat läge. Bevisat på
# Xbox 2026-08-09: samma kattbädd — perfekt via spelarplacering, grop via
# struktur. setblock/spelare stämplar aktuell version, därav skillnaden.
BLOCK_VERSION = 18491392
SRV = "/opt/bds/server"
GROUND = -61               # översta solida blocket i FLAT (verifieras i bygget)
FLOOR = GROUND + 1         # fötterna/golvnivån

# ---------------------------------------------------------------- texter ----
TEXTS = {
    "public": {
        "world": "Cat Haven",
        "welcome_sign": "Cat Haven\nThe shelter\nneeds a new\ncaretaker!",
        "den_clue": "Still warm...\npaw prints go\ndeeper into the\nsouthwest woods",
        "pool_sign": "CAT POOL\n/\\_/\\ ~\u2248~\n( ^.^ ) splash!\nno dogs allowed",
        "island_sign": "That dry patch\nin the pond...\ntake the boat\nand look closer",
        "parkour_sign": "CAT PARKOUR\nRide and jump\nplatform to\nplatform!",
        "lake_sign": "THE LAKE\nSomething\nglints below.\nDive down.",
        "trade_sign": "TRADING POST\nBring string,\nfeathers and\na diamond.",
        "gate_meadow_sign": "CLOSED\nFinish Task 4\nand this path\nwill open",
        "gate_parkour_sign": "CLOSED\nFinish Task 6\nand this path\nwill open",
        "gate_lake_sign": "CLOSED\nFinish Task 7\nand the grate\nwill open",
        "dog_name": "The Guard Dog",
        "silverfish_name": "§bThe Silver Fish",
        "meadow_sign": "THE MEADOW\n& beyond:\ncave, wood\nand a mountain",
        "start_sign": "Start here:\nread the book\nin the chest\ninside ->",
        "chest_sign": "The handbook\nis in here!",
        "diary_title": "The Old Caretaker's Diary",
        "diary_author": "The Old Caretaker",
        "diary_pages": [
            "Day 214.\n\nThe backpack cat dug up a diamond today. I laughed until I cried.\n\nI buried nothing. They have their own economy down there.",
            "Day 388.\n\nA fifth cat came with the frost. Black as the space between the stars. She never let me feed her by hand.\n\nMidnight, I called her. The others speak of her still.",
            "Day 401.\n\nCold night. I left a silver fish on a cat bed, and by morning it was gone - and there were two sets of pawprints in the snow.\n\nIf you are reading this: she is still here. Somewhere.",
            "Day 452.\n\nMy knees no longer like the climb, so my best gear stays where I left it - up under the roof, where the dust settles.\n\nThe cats know the way. Their tower was always the first step.",
        ],
        "book_title": "The Caretaker's Handbook",
        "book_author": "The Old Caretaker",
        "book_pages": [
            "Welcome to Cat Haven!\n\nI am too old to care for the shelter now. The four cats still live in these hills - they just need someone to trust again.\n\nEverything you need is in this chest.",
            "TASK 1 - MEET THE CATS\n\n%MOCHA% never left the shelter. %HAZEL% fishes by the pond. %MISTY% hides among the trees.\n\nTame them with the cod from this chest.",
            "TASK 2 - %SNOW% IS MISSING\n\nGone since the storm. The others will not go near the DARK FOREST in the west. They say the ghosts of the old cats walk there.\n\nFollow the white tufts from the pond. Do not fear the ghosts - they only miss their caretaker.",
            "TASK 3 - A CATCH FROM THE POND\n\nPut the saddle on a cat and wade into the pond together.\n\nA saddled cat catches cod all by itself. Let it fish your next meal!",
            "TASK 4 - RIDE TO THE LIGHTHOUSE\n\nFollow the gravel road south and ride to the top of the lighthouse hill.\n\nSomething useful waits in the chest at the top of the tower.",
            "TASK 5 - THE BURIED SAVINGS\n\nI never trusted banks. What I saved, the cats buried - they bury better than I ever did.\n\nA cat wearing a BACKPACK remembers where. Give one a backpack and let it dig.",
            "TASK 6 - THREE KEYS, ONE TREASURE\n\nA path leaves the road and runs east, past a meadow loud with bees, into a cave that glitters, and on to a wood hiding one more secret. A key waits in each.\n\nBut look again at the pond behind the house - there is a small dry island in it, and something waits there too. That is your third key.\n\nThree keys, three places. Carry all three at once and see what happens.\n\nAnd past the meadow, a mountain rises with snow on its head. Whatever is waiting at the top is worth the climb.",
            "TASK 7 - THE CAT PARKOUR\n\nPast the crystal cave, a gravel path keeps going east to a little wooden course lit by lanterns, floating platform to platform.\n\nRide and jump all the way to the far end. The last few jumps are wide and the platforms are narrow - take a run-up. Something is waiting for you there.",
            "TASK 8 - THE DEEP LAKE\n\nEast of everything else, past the meadow and the mountain, a lake hides more than fish. Dive to the bottom and swim through the tunnel - hold your breath.\n\nSomething waits in the dark at the far end.",
            "TASK 9 - THE TRADING POST\n\nA backpack cat's finds pile up fast. There is a barrel behind the house, east of the garden, that will take three string, three feathers and a diamond off your hands - and give something back.\n\nThe first trade brings out my old CAPE. Put it on a cat and go for a ride - you will see why I kept it.",
            "The beds inside carry the cats' names. Cat treats cheer them up when their tails droop - the recipe is sugar, wheat and cod.\n\nTake good care of them.\n\nAnd mind the boxes. Some hide more than dust.\n\nKeep your eyes open as you go, too - six coloured ribbons are hiding in places you already visit. Carry all six at once for a surprise.\n\n- The Old Caretaker",
            "One more thing, if you will believe an old man.\n\nThe cats used to tell of a FIFTH - black as the gap between the stars, with eyes of amber.\n\nShe shows herself only to those who leave the SILVER FISH from the lighthouse chest on a cat's bed while the moon stands at its highest.",
        ],
    },
    "private": {
        "world": "Kattgården",
        "welcome_sign": "Kattgården\nKatthemmet\nbehöver en ny\nföreståndare!",
        "den_clue": "Ännu varm...\ntassavtryck mot\nsydväst, djupt\nin i skogen",
        "pool_sign": "KATTPOOLEN\n/\\_/\\ ~\u2248~\n( ^.^ ) plask!\ninga hundar!",
        "island_sign": "Den torra \u00f6n\ni dammen...\nta b\u00e5ten och\ntitta n\u00e4rmare",
        "parkour_sign": "KATTBANAN\nRid och hoppa\nplattform till\nplattform!",
        "lake_sign": "SJÖN\nNågot glimmar\ndär nere.\nDyk ner.",
        "trade_sign": "HANDELSPOST\nTa med snöre,\nfjädrar och\nen diamant.",
        "gate_meadow_sign": "STÄNGT\nKlara uppdrag 4\nså öppnas\nstigen",
        "gate_parkour_sign": "STÄNGT\nKlara uppdrag 6\nså öppnas\nstigen",
        "gate_lake_sign": "STÄNGT\nKlara uppdrag 7\nså öppnas\ngallret",
        "dog_name": "Vakthunden",
        "silverfish_name": "§bSilverfisken",
        "meadow_sign": "ÄNGEN\n& bortom:\ngrotta, skog\noch ett berg",
        "start_sign": "Börja här:\nläs handboken\ni kistan\ndärinne ->",
        "chest_sign": "Handboken\nligger häri!",
        "diary_title": "Gamla föreståndarens dagbok",
        "diary_author": "Gamla föreståndaren",
        "diary_pages": [
            "Dag 214.\n\nRyggsäckskatten grävde upp en diamant i dag. Jag skrattade tills jag grät.\n\nJag grävde aldrig ner något. De har sin egen ekonomi där nere.",
            "Dag 388.\n\nEn femte katt kom med frosten. Svart som mellanrummet mellan stjärnorna. Hon lät mig aldrig mata henne ur handen.\n\nMidnight kallade jag henne. De andra talar om henne än.",
            "Dag 401.\n\nKall natt. Jag lämnade en silverfisk på en kattbädd, och på morgonen var den borta - och det fanns två rader tassavtryck i snön.\n\nLäser du det här: hon är kvar. Någonstans.",
            "Dag 452.\n\nMina knän gillar inte klättringen längre, så mina bästa saker ligger kvar där jag lämnade dem - uppe under taket, där dammet samlas.\n\nKatterna kan vägen. Deras torn var alltid första steget.",
        ],
        "book_title": "Föreståndarens handbok",
        "book_author": "Gamla föreståndaren",
        "book_pages": [
            "Välkommen till Kattgården!\n\nJag är för gammal för att sköta katthemmet nu. De fyra katterna bor kvar i kullarna - de behöver bara någon att lita på igen.\n\nAllt du behöver ligger i den här kistan.",
            "UPPDRAG 1 - MÖT KATTERNA\n\n%MOCHA% lämnade aldrig katthemmet. %HAZEL% fiskar vid dammen. %MISTY% gömmer sig bland träden.\n\nTämj dem med torsken ur kistan.",
            "UPPDRAG 2 - %SNOW% ÄR FÖRSVUNNEN\n\nBorta sedan stormen. De andra vägrar gå nära MÖRKA SKOGEN i väster. De säger att de gamla katternas spöken går där.\n\nFölj de vita tussarna från dammen. Var inte rädd för spökena - de saknar bara sin föreståndare.",
            "UPPDRAG 3 - EN FÅNGST UR DAMMEN\n\nSätt sadeln på en katt och vada ut i dammen tillsammans.\n\nEn sadlad katt fångar torsk alldeles själv. Låt den fiska din nästa måltid!",
            "UPPDRAG 4 - RID TILL FYREN\n\nFölj grusvägen söderut och rid upp för fyrkullen.\n\nNågot användbart väntar i kistan högst upp i tornet.",
            "UPPDRAG 5 - DET NEDGRÄVDA SPARANDET\n\nJag litade aldrig på banker. Det jag sparade grävde katterna ner - de gräver bättre än jag någonsin gjorde.\n\nEn katt med RYGGSÄCK minns var. Ge en katt en ryggsäck och låt den gräva.",
            "UPPDRAG 6 - TRE NYCKLAR, EN SKATT\n\nEn stig lämnar vägen österut, förbi en äng full av surrande bin, in i en glittrande grotta, och vidare till en skog som gömmer en sak till. En nyckel väntar i var och en.\n\nMen titta en gång till på dammen bakom huset - där finns en liten torr ö, och något väntar där också. Det är din tredje nyckel.\n\nTre nycklar, tre platser. Bär alla tre samtidigt och se vad som händer.\n\nOch bortom ängen reser sig ett berg med snö på huvudet. Vad som än väntar på toppen är värt klättringen.",
            "UPPDRAG 7 - KATTBANAN\n\nBortom kristallgrottan fortsätter en grusstig österut till en liten lyktbelyst bana av trä, med plattformar som flyter i luften.\n\nRid och hoppa hela vägen till andra änden. De sista hoppen är breda och plattformarna smala - ta sats. Något väntar på dig där.",
            "UPPDRAG 8 - DEN DJUPA SJÖN\n\nÖster om allt annat, förbi ängen och berget, gömmer en sjö mer än fisk. Dyk till botten och simma genom tunneln - håll andan.\n\nNågot väntar i mörkret vid andra änden.",
            "UPPDRAG 9 - HANDELSPOSTEN\n\nEn ryggsäckskatts fynd hopar sig fort. Det finns en tunna bakom huset, öster om täppan, som tar emot tre snören, tre fjädrar och en diamant - och ger något tillbaka.\n\nFörsta bytet plockar fram min gamla MANTEL. Sätt den på en katt och rid ut - då förstår du varför jag behöll den.",
            "Sängarna därinne bär katternas namn. Kattgodis piggar upp dem när svansen hänger - receptet är socker, vete och torsk.\n\nTa väl hand om dem.\n\nOch se upp med lådorna. Vissa gömmer mer än damm.\n\nHåll ögonen öppna medan du utforskar också - sex färgade band gömmer sig på platser du redan besökt. Bär alla sex samtidigt för en överraskning.\n\n- Gamla föreståndaren",
            "En sak till, om du tror en gammal man.\n\nKatterna berättade om en FEMTE - svart som mellanrummet mellan stjärnorna, med ögon av bärnsten.\n\nHon visar sig bara för den som lämnar SILVERFISKEN ur fyrens kista på en kattbädd när månen står som högst.",
        ],
    },
}

# ------------------------------------------------------- strukturbyggare ----
class Struct:
    """Bygger en .mcstructure ur (x,y,z)->(blocknamn, states) + block entities."""
    def __init__(self, sx, sy, sz):
        self.sx, self.sy, self.sz = sx, sy, sz
        self.blocks = {}   # (x,y,z) -> (name, states-dict)
        self.bents = {}    # (x,y,z) -> compound-dict (block entity)

    def set(self, x, y, z, name, states=None):
        self.blocks[(x, y, z)] = (name, states or {})

    def box(self, x0, y0, z0, x1, y1, z1, name, states=None, hollow=False):
        if hollow and (x0 == x1 or y0 == y1 or z0 == z1):
            # höjd/bredd 1 gör VARJE cell till kant — hela lagret fylls.
            # Har bitit tre gånger (dammen, fyrräcket). Bygg kanter explicit.
            raise ValueError("hollow-box med platt axel fyller allt — bygg kanterna explicit")
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    edge = x in (x0, x1) or y in (y0, y1) or z in (z0, z1)
                    if hollow and not edge: continue
                    self.set(x, y, z, name, states)

    def entity_at(self, x, y, z, data):
        self.bents[(x, y, z)] = data

    def emit(self, path):
        palette, pindex = [], {}
        def pid(name, states):
            key = (name, tuple(sorted(states.items())))
            if key not in pindex:
                st = {}
                for k, v in states.items():
                    st[k] = B(int(v)) if isinstance(v, bool) else (I(v) if isinstance(v, int) else S(v))
                pindex[key] = len(palette)
                palette.append(C({"name": S(name), "states": C(st),
                                  "version": I(BLOCK_VERSION)}))
            return pindex[key]
        # osatta celler = -1 (rör inte världen) — explicit satt "air" hugger hål
        idx, posdata = [], {}
        flat = 0
        for x in range(self.sx):
            for y in range(self.sy):
                for z in range(self.sz):
                    b = self.blocks.get((x, y, z))
                    idx.append(V(nbt.TAG_INT, pid(*b) if b else -1))
                    if (x, y, z) in self.bents:
                        d = dict(self.bents[(x, y, z)])
                        d.update({"x": I(x), "y": I(y), "z": I(z)})
                        posdata[str(flat)] = C({"block_entity_data": C(d)})
                    flat += 1
        n = self.sx * self.sy * self.sz
        root = C({
            "format_version": I(1),
            "size": L(nbt.TAG_INT, [I(self.sx), I(self.sy), I(self.sz)]),
            "structure": C({
                "block_indices": L(nbt.TAG_LIST, [
                    L(nbt.TAG_INT, idx),
                    L(nbt.TAG_INT, [V(nbt.TAG_INT, -1)] * n),
                ]),
                "entities": L(nbt.TAG_END, []),
                "palette": C({"default": C({
                    "block_palette": L(nbt.TAG_COMPOUND, palette),
                    "block_position_data": C(posdata),
                })}),
            }),
            "structure_world_origin": L(nbt.TAG_INT, [I(0), I(0), I(0)]),
        })
        os.makedirs(os.path.dirname(path), exist_ok=True)
        nbt.write_mcstructure(path, root)

def item(slot, name, count=1, tag=None):
    d = {"Count": B(count), "Damage": SH(0), "Name": S(name),
         "Slot": B(slot), "WasPickedUp": B(0)}
    if tag: d["tag"] = C(tag)
    return C(d)

def chest_entity(items):
    return {"id": S("Chest"), "isMovable": B(1), "Findable": B(0),
            "Items": L(nbt.TAG_COMPOUND, items)}

def book_tag(t):
    pages = [C({"photoname": S(""), "text": S(p)}) for p in t["book_pages"]]
    return {"title": S(t["book_title"]), "author": S(t["book_author"]),
            "generation": I(0), "pages": L(nbt.TAG_COMPOUND, pages)}

def sign_entity(text):
    # Både modern (FrontText) och legacy (Text) — laddaren tar den den förstår.
    side = lambda s: C({"HideGlowOutline": B(0), "IgnoreLighting": B(0),
                        "PersistFormatting": B(1), "SignTextColor": I(-16777216),
                        "Text": S(s), "TextOwner": S("")})
    return {"id": S("Sign"), "isMovable": B(1), "IsWaxed": B(1),
            "Text": S(text), "FrontText": side(text), "BackText": side("")}

# ----------------------------------------------------------- byggnaderna ----
def build_structures(outdir, t, disp, cats):
    st = f"{outdir}/structures/haven"

    # KATTHEMMET: 13 bred (x), 7 hög, 10 djup (z). Dörröppning mot söder (z=0).
    s = Struct(13, 10, 10)
    s.box(0, 0, 0, 12, 0, 9, "minecraft:spruce_planks")                       # golv
    s.box(0, 1, 0, 12, 4, 9, "minecraft:oak_planks", hollow=True)             # väggar
    for cx, cz in ((0, 0), (0, 9), (12, 0), (12, 9)):                          # knutar
        s.box(cx, 1, cz, cx, 4, cz, "minecraft:oak_log", {"pillar_axis": "y"})
    # URGRÖPNING: hollow-boxen har SEX sidor — bottenplanet la ett extra golv
    # på y1 (världens -59: möblerna sattes där och omringades av plank i samma
    # nivå = "GROPARNA") och topplanet ett innertak på y4 som gömde ljus-
    # kronorna. Xbox-rapport: "en extra rad av golv i huset".
    s.box(1, 1, 1, 11, 4, 8, "minecraft:air")
    # SADELTAK av grantrappor: nock längs huslängden, lutning mot fram- och
    # baksida (speltest-önskemål: "riktigt lutande tak")
    for i in range(4):
        s.box(0, 5 + i, i, 12, 5 + i, i, "minecraft:spruce_stairs",
              {"upside_down_bit": False, "weirdo_direction": 2})               # framsluttning
        s.box(0, 5 + i, 9 - i, 12, 5 + i, 9 - i, "minecraft:spruce_stairs",
              {"upside_down_bit": False, "weirdo_direction": 3})               # baksluttning
    s.box(0, 9, 4, 12, 9, 5, "minecraft:spruce_planks")                        # nock
    # gavlarna fylls med plank...
    for i in range(4):
        for gx in (0, 12):
            s.box(gx, 5 + i, i + 1, gx, 5 + i, 8 - i, "minecraft:oak_planks")
    # ...och får varsitt KATTANSIKTE i ull (öron, ögon, rosa nos) — kattloggan
    for gx in (0, 12):
        for z in range(1, 9):  s.set(gx, 5, z, "minecraft:light_gray_wool")
        s.set(gx, 5, 4, "minecraft:pink_wool"); s.set(gx, 5, 5, "minecraft:pink_wool")
        for z in range(2, 8):  s.set(gx, 6, z, "minecraft:light_gray_wool")
        s.set(gx, 6, 3, "minecraft:black_wool"); s.set(gx, 6, 6, "minecraft:black_wool")
        s.set(gx, 7, 3, "minecraft:black_wool"); s.set(gx, 7, 4, "minecraft:light_gray_wool")
        s.set(gx, 7, 5, "minecraft:light_gray_wool"); s.set(gx, 7, 6, "minecraft:black_wool")
    for wx in (2, 4, 8, 10):                                                   # fönster
        s.set(wx, 2, 0, "minecraft:glass_pane"); s.set(wx, 3, 0, "minecraft:glass_pane")
        s.set(wx, 2, 9, "minecraft:glass_pane"); s.set(wx, 3, 9, "minecraft:glass_pane")
    for wz in (3, 6):
        s.set(0, 2, wz, "minecraft:glass_pane"); s.set(0, 3, wz, "minecraft:glass_pane")
        s.set(12, 2, wz, "minecraft:glass_pane"); s.set(12, 3, wz, "minecraft:glass_pane")
    for dx in (5, 6):                                                          # dörröppning
        s.set(dx, 1, 0, "minecraft:air"); s.set(dx, 2, 0, "minecraft:air")
    s.set(8, 1, 0, "mjau:kattlucka")                                           # kattdörr i väggen
    for lx, lz in ((3, 4), (9, 4)):                                            # ljuskronor från nocken
        s.set(lx, 8, lz, "minecraft:lantern", {"hanging": True})
    beds = ((2, disp["misty"]), (4, disp["hazel"]), (8, disp["mocha"]), (10, disp["snow"]))
    for bx, name in beds:                                                      # namnskyltarna (block
        s.set(bx, 2, 8, "minecraft:wall_sign", {"facing_direction": 2})        # entities kräver struktur)
        s.entity_at(bx, 2, 8, sign_entity(name))
    # INREDNINGEN placeras via setblock i build_commands. OBS: "groparna" var
    # aldrig ett klientrenderingsfel — det var hollow-boxens extra golvplan
    # (urgröpningen ovan). Kommandoplacering behålls: bevisat felfri.
    # skylten sitter på väggens INSIDA (cell z1) — i väggplanet (z0) åt den
    # upp fönstrets nedre glasruta ("fönster verkar saknas", Xbox-rapport)
    s.set(2, 2, 1, "minecraft:wall_sign", {"facing_direction": 3})             # "handboken häri!"
    s.entity_at(2, 2, 1, sign_entity(t["chest_sign"]))
    s.set(2, 1, 1, "minecraft:chest", {"facing_direction": 5})                 # startkistan
    s.entity_at(2, 1, 1, chest_entity([
        item(0, "minecraft:written_book", 1, book_tag(t)),
        item(1, "minecraft:cod", 16),
        item(2, "mjau:godis", 4),
        item(3, "mjau:sadel_brun", 1),
    ]))
    s.emit(f"{st}/shelter.mcstructure")

    # HEMLIGA KÄLLAREN: under katthemmet, nås via schaktet som kartongen döljer
    # ("mind the boxes"). Dagboken därnere fördjupar femte katt-mytologin och
    # ryggsäcken låser upp uppdrag 4 (skattletandet).
    # Världsbotten är bedrock på -64 — källaren får plats exakt ovanpå:
    # golv -64, rum -63..-62 (två högt), tak -61 (markskiktet).
    s = Struct(7, 4, 6)
    s.box(0, 0, 0, 6, 3, 5, "minecraft:cobblestone")
    s.box(1, 1, 1, 5, 2, 4, "minecraft:air")
    s.set(4, 3, 1, "minecraft:air")                                # schaktmynningen i taket
    for y in (1, 2):                                               # stege upp mot schaktet
        s.set(4, y, 1, "minecraft:ladder", {"facing_direction": 2})
    s.set(3, 1, 3, "minecraft:lantern", {"hanging": False})
    s.set(1, 1, 4, "minecraft:chest", {"facing_direction": 5})
    s.entity_at(1, 1, 4, chest_entity([
        item(0, "minecraft:written_book", 1, {
            "title": S(t["diary_title"]), "author": S(t["diary_author"]),
            "generation": I(0),
            "pages": L(nbt.TAG_COMPOUND, [C({"photoname": S(""), "text": S(p)})
                                          for p in t["diary_pages"]])}),
        item(1, "mjau:ryggsack_brun", 1),
        item(2, "mjau:haxhatt_svart", 1),
        item(3, "minecraft:emerald", 5),
    ]))
    s.emit(f"{st}/cellar.mcstructure")

    # KATTSKYLTEN vid entrén: ASCII-katt ("rolig kattskylt", önskemål från Xbox)
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:standing_sign", {"ground_sign_direction": 8})
    s.entity_at(0, 0, 0, sign_entity("/\\_/\\\n( o.o )\n > ^ <\nmjau!"))
    s.emit(f"{st}/catsign.mcstructure")

    # VÄLKOMSTSKYLT vid spawn (egen liten struktur, vänd mot norr=spelaren)
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:standing_sign", {"ground_sign_direction": 8})
    s.entity_at(0, 0, 0, sign_entity(t["welcome_sign"]))
    s.emit(f"{st}/welcome.mcstructure")

    # POOLSKYLTEN vid dammens västra strand (vänd mot huset i väster)
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:standing_sign", {"ground_sign_direction": 4})
    s.entity_at(0, 0, 0, sign_entity(t["pool_sign"]))
    s.emit(f"{st}/poolsign.mcstructure")

    # ÖSKYLTEN bredvid poolskylten: speltest visade att ön/nyckeln missas
    # helt utan en direkt pekpinne (handboken nämnde bara grotta+skog som
    # "tre platser", dammen saknades helt i alla ledtrådar)
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:standing_sign", {"ground_sign_direction": 4})
    s.entity_at(0, 0, 0, sign_entity(t["island_sign"]))
    s.emit(f"{st}/islandsign.mcstructure")

    # KATTBANAN: skylt vid stegens fot + prisskista på målplattformen
    # (speltest-önskemål: "belöningar för de flesta uppdrag")
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:standing_sign", {"ground_sign_direction": 8})
    s.entity_at(0, 0, 0, sign_entity(t["parkour_sign"]))
    s.emit(f"{st}/parkoursign.mcstructure")

    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:chest", {"facing_direction": 3})
    s.entity_at(0, 0, 0, chest_entity([
        item(0, "mjau:vingar_gold", 1),
        item(1, "minecraft:diamond", 2),
    ]))
    s.emit(f"{st}/parkourchest.mcstructure")

    # SJÖN: skylt på ytan + skattkista i luftfickan under vattnet
    # (speltest-önskemål: "underwater cave zone")
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:standing_sign", {"ground_sign_direction": 8})
    s.entity_at(0, 0, 0, sign_entity(t["lake_sign"]))
    s.emit(f"{st}/lakesign.mcstructure")

    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:chest", {"facing_direction": 3})
    s.entity_at(0, 0, 0, chest_entity([
        item(0, "minecraft:trident", 1),
        item(1, "minecraft:diamond", 2),
    ]))
    s.emit(f"{st}/lakechest.mcstructure")

    # HANDELSPOSTEN: skylt vid tunnan (speltest-önskemål: "treasure trading
    # post" — skattletarnas fynd bara samlades på hög, nu finns ett ställe
    # att lämna in dem)
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:standing_sign", {"ground_sign_direction": 4})
    s.entity_at(0, 0, 0, sign_entity(t["trade_sign"]))
    s.emit(f"{st}/tradesign.mcstructure")

    # GRINDSKYLTARNA: en per grind, säger vilket uppdrag som låser upp
    # (speltest-önskemål: "låsa ner delar av världen och öppna stegvis")
    for gname in ("gate_meadow_sign", "gate_parkour_sign", "gate_lake_sign"):
        s = Struct(1, 1, 1)
        s.set(0, 0, 0, "minecraft:standing_sign", {"ground_sign_direction": 4})
        s.entity_at(0, 0, 0, sign_entity(t[gname]))
        s.emit(f"{st}/{gname}.mcstructure")

    # VINDSKISTAN: fullt netherite-set åt spelaren OCH katten (speltest-
    # önskemål: "en vind på huset ... full set netherite åt katten och åt
    # en själv, lite svåråtkomlig men inte omöjlig")
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:chest", {"facing_direction": 2})
    s.entity_at(0, 0, 0, chest_entity([
        item(0, "minecraft:netherite_helmet", 1),
        item(1, "minecraft:netherite_chestplate", 1),
        item(2, "minecraft:netherite_leggings", 1),
        item(3, "minecraft:netherite_boots", 1),
        item(4, "minecraft:netherite_sword", 1),
        item(5, "mjau:rustning_netherit", 1),
    ]))
    s.emit(f"{st}/atticchest.mcstructure")

    # LEDTRÅDSSKYLTEN i gamla kulan: Maja har flyttat (vänd mot ingången i öster)
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:standing_sign", {"ground_sign_direction": 12})
    s.entity_at(0, 0, 0, sign_entity(t["den_clue"]))
    s.emit(f"{st}/denclue.mcstructure")

    # BÖRJA HÄR-skylten: spelaren ska aldrig behöva undra vad nästa steg är
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:standing_sign", {"ground_sign_direction": 8})
    s.entity_at(0, 0, 0, sign_entity(t["start_sign"]))
    s.emit(f"{st}/startsign.mcstructure")

    # DE TRE NYCKELKISTORNA (speltest-önskemål: "större värld, fler saker att
    # göra") — grottan, ön i dammen, den nya skogslunden. Kommandoplacerade
    # kistor kan inte få innehåll via /setblock, därför egna småstrukturer
    # (samma mönster som katt-/poolskylten).
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:chest", {"facing_direction": 3})
    s.entity_at(0, 0, 0, chest_entity([item(0, "minecraft:amethyst_shard", 1)]))
    s.emit(f"{st}/cavechest.mcstructure")

    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:chest", {"facing_direction": 3})
    s.entity_at(0, 0, 0, chest_entity([item(0, "minecraft:nautilus_shell", 1)]))
    s.emit(f"{st}/islandchest.mcstructure")

    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:chest", {"facing_direction": 3})
    s.entity_at(0, 0, 0, chest_entity([item(0, "minecraft:rabbit_foot", 1)]))
    s.emit(f"{st}/forestchest.mcstructure")

    # TOPPKISTAN på det höga berget: kikare (utsiktstema) + diamanter
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:chest", {"facing_direction": 3})
    s.entity_at(0, 0, 0, chest_entity([
        item(0, "minecraft:spyglass", 1),
        item(1, "minecraft:diamond", 2),
    ]))
    s.emit(f"{st}/mountainchest.mcstructure")

    # REGNBÅGSNÖKEN (speltest-önskemål: "samla saker"-uppdrag): sex färgade
    # band gömda i platser man redan besöker. Alla sex samtidigt i väskan
    # ger utmärkelsen Regnbågssamlaren.
    for colour in ("red", "orange", "yellow", "green", "blue", "purple"):
        s = Struct(1, 1, 1)
        s.set(0, 0, 0, "minecraft:chest", {"facing_direction": 3})
        s.entity_at(0, 0, 0, chest_entity([item(0, f"minecraft:{colour}_dye", 1)]))
        s.emit(f"{st}/bowchest_{colour}.mcstructure")

    # ÄNGSSKYLTEN vid stigens avfart österut (vänd mot vägen i väster)
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:standing_sign", {"ground_sign_direction": 4})
    s.entity_at(0, 0, 0, sign_entity(t["meadow_sign"]))
    s.emit(f"{st}/meadowsign.mcstructure")

    # DAMMEN: 11×11, 2 djup så katten kan simma — stenbotten, ram, vatten.
    # OBS: box(hollow=True) med höjd 1 gör ALLA block till kant (y träffar
    # alltid y0/y1) — därför läggs vattnet EFTER ramen, aldrig tvärtom.
    s = Struct(11, 4, 11)
    s.box(0, 0, 0, 10, 0, 10, "minecraft:stone_bricks")            # botten
    for y in (1, 2):
        s.box(0, y, 0, 10, y, 10, "minecraft:stone_bricks")        # ram...
        s.box(1, y, 1, 9, y, 9, "minecraft:water", {"liquid_depth": 0})  # ...vatten
    s.emit(f"{st}/pond.mcstructure")   # fiskdammsblocket sätts via kommando

    # FYREN: 7×7-bas, 5×5-torn med röda band, stege upp, belönings­kista i topp.
    # Ingången går i MARKNIVÅ genom sockeln (buggrapport från Xbox: öppningen
    # satt två block upp utan trapp) — sockelns inre är urgröpt så man kliver
    # rakt in på kullens nivå, och stegen börjar på golvet.
    s = Struct(7, 17, 7)
    s.box(0, 0, 0, 6, 1, 6, "minecraft:cobblestone")
    s.box(2, 0, 2, 4, 1, 4, "minecraft:air")                                   # urgröpt sockel
    # RINGVÄGGAR per våning — flat hollow-box fyllde hela lagret, så tornet
    # var i praktiken MASSIVT med en begravd stegschakt (spärren avslöjade det)
    for y in range(2, 13):
        band = "minecraft:red_concrete" if y in (5, 9) else "minecraft:white_concrete"
        for wx in range(1, 6):
            s.set(wx, y, 1, band); s.set(wx, y, 5, band)
        for wz in range(2, 5):
            s.set(1, y, wz, band); s.set(5, y, wz, band)
    # INGÅNGEN VETTER MOT NORR — det är därifrån vägen kommer (Xbox-rapport:
    # spelaren möttes av en blank sockel; söderöppningen satt på baksidan).
    for z in (0, 1):                                                           # tunnel genom sockeln
        s.set(3, 0, z, "minecraft:air"); s.set(3, 1, z, "minecraft:air")
    s.set(3, 2, 1, "minecraft:air"); s.set(3, 3, 1, "minecraft:air")           # valv i tornväggen
    for y in (0, 1, 2, 3):                                                     # bakdörren (söder) kvar
        s.set(3, y, 5, "minecraft:air")
    s.box(3, 2, 3, 3, 3, 3, "minecraft:air")
    # STEGEN PÅ ÖSTRA innerväggen — norringången carvade bort stegens gamla
    # stödvägg och stegar utan block bakom poppar av (genomspelningen fann det)
    for y in range(0, 13):
        s.set(4, y, 3, "minecraft:ladder", {"facing_direction": 4})
    s.box(0, 13, 0, 6, 13, 6, "minecraft:spruce_planks")                       # plattform
    s.set(4, 13, 3, "minecraft:air")                                           # stegluckan
    # översta stegpinnen SIST — plattformsboxen skrev annars över den och man
    # slog i huvudet strax under luckan (Xbox-rapport #2)
    s.set(4, 13, 3, "minecraft:ladder", {"facing_direction": 4})
    for rx in range(0, 7):                                                     # räcke: bara KANTEN
        s.set(rx, 14, 0, "minecraft:oak_fence"); s.set(rx, 14, 6, "minecraft:oak_fence")
    for rz in range(1, 6):
        s.set(0, 14, rz, "minecraft:oak_fence"); s.set(6, 14, rz, "minecraft:oak_fence")
    # ljuset ETT steg högre — glowstone på y14 satt i huvudhöjd bredvid
    # takluckan och man slog i skallen när man klev upp (Xbox-rapport)
    s.set(3, 15, 3, "minecraft:glowstone")                                     # ljuset
    s.set(3, 16, 3, "minecraft:lantern", {"hanging": False})
    s.set(1, 14, 3, "minecraft:chest", {"facing_direction": 5})                # belöningen
    s.entity_at(1, 14, 3, chest_entity([
        item(0, "mjau:rustning_netherit", 1),
        item(1, "minecraft:diamond", 3),
        item(2, "minecraft:golden_apple", 1),
        item(3, "minecraft:salmon", 1,       # nyckeln till gåtan, nu med NAMN —
             {"display": C({"Name": S(t["silverfish_name"])})}),  # laxen är ju rosa
    ]))
    s.emit(f"{st}/lighthouse.mcstructure")

    # MÖRKEKEN: hög stam, bred tät krona — skogens byggsten
    s = Struct(7, 9, 7)
    for y in range(0, 6):
        s.set(3, y, 3, "minecraft:dark_oak_log", {"pillar_axis": "y"})
    s.box(0, 4, 0, 6, 6, 6, "minecraft:dark_oak_leaves", {"persistent_bit": True, "update_bit": False})
    s.box(1, 7, 1, 5, 7, 5, "minecraft:dark_oak_leaves", {"persistent_bit": True, "update_bit": False})
    s.emit(f"{st}/darktree.mcstructure")

    # EKEN: stam + lövkrona (persistent så den inte vissnar)
    s = Struct(5, 8, 5)
    for y in range(0, 5):
        s.set(2, y, 2, "minecraft:oak_log", {"pillar_axis": "y"})
    s.box(0, 3, 0, 4, 5, 4, "minecraft:oak_leaves", {"persistent_bit": True, "update_bit": False})
    s.box(1, 6, 1, 3, 6, 3, "minecraft:oak_leaves", {"persistent_bit": True, "update_bit": False})
    s.set(2, 7, 2, "minecraft:oak_leaves", {"persistent_bit": True, "update_bit": False})
    s.emit(f"{st}/tree.mcstructure")

    # GRANEN: hög smal stam, avsmalnande koniska lövringar
    s = Struct(7, 11, 7)
    for y in range(0, 9):
        s.set(3, y, 3, "minecraft:spruce_log", {"pillar_axis": "y"})
    for i, r in enumerate((3, 3, 2, 2, 2, 1, 1)):
        y = 3 + i
        s.box(3 - r, y, 3 - r, 3 + r, y, 3 + r, "minecraft:spruce_leaves", {"persistent_bit": True, "update_bit": False})
    s.set(3, 10, 3, "minecraft:spruce_leaves", {"persistent_bit": True, "update_bit": False})
    s.emit(f"{st}/sprucetree.mcstructure")

    # BJÖRKEN: ljusare stam, rundare krona — samma grundform som eken men
    # egen art för variation i skogsramen
    s = Struct(5, 7, 5)
    for y in range(0, 5):
        s.set(2, y, 2, "minecraft:birch_log", {"pillar_axis": "y"})
    s.box(1, 3, 1, 3, 4, 3, "minecraft:birch_leaves", {"persistent_bit": True, "update_bit": False})
    s.box(0, 4, 0, 4, 5, 4, "minecraft:birch_leaves", {"persistent_bit": True, "update_bit": False})
    s.set(2, 6, 2, "minecraft:birch_leaves", {"persistent_bit": True, "update_bit": False})
    s.emit(f"{st}/birchtree.mcstructure")

# ------------------------------------------------------ serverkommandona ----
def build_commands(cats, disp, dog_name):
    g, f = GROUND, FLOOR
    c = []
    c.append("gamerule commandblockoutput false")
    c.append("gamerule domobspawning false")
    c.append("gamerule keepinventory true")
    c.append("gamerule sendcommandfeedback true")
    # BUGFIX: 128 gav 13 x-chunk (floor(-58/16)=-4 till floor(128/16)=8) x
    # 8 z-chunk = 104 - över 100-taket igen (skogsramen har egna remsor,
    # den här behöver bara nå kattbanans nya mål, inte hela ramen).
    c.append(f"tickingarea add -58 {g-4} -20 120 {g+30} 92 bygge")   # 120: kattbanan når x=113
    c.append(("sleep", 4))
    c.append(f"testforblock 0 {g} 0 grass_block")      # verifiera marknivån
    # kullar för fyren: terrasser en katt kan kliva upp för
    for i, r in enumerate((10, 8, 6, 4)):
        y = g + 1 + i
        c.append(f"fill {-r} {y} {56-r} {r} {y} {56+r} dirt")
    for i, r in enumerate((10, 8, 6, 4)):
        c.append(f"fill {-r} {g+1+i} {56-r} {r} {g+1+i} {56+r} grass_block replace dirt")
    c.append(("sleep", 2))
    # grusvägen: spawn -> katthemmet, sedan runt om och söderut till fyrkullen
    c.append(f"fill -1 {g} 3 0 {g} 7 gravel")
    c.append(f"fill 8 {g} 4 9 {g} 46 gravel")
    c.append(f"fill 0 {g} 45 9 {g} 46 gravel")
    c.append(("sleep", 2))
    # stigen österut: bygden -> ängen -> berget. Utan den var de nya
    # områdena helt bortkopplade från resten av världen (speltest-önskemål:
    # "bygga ihop mer av världen så den blir komplett").
    c.append(f"fill 9 {g} 15 24 {g} 16 gravel")
    c.append(f"fill 25 {g} 15 26 {g} 66 gravel")
    c.append(("sleep", 2))
    c.append(f"structure load haven:meadowsign 24 {f} 15")
    c.append(("sleep", 1))
    c.append(f"testforblock 24 {f} 15 standing_sign")
    # lyktstolpar längs ängs-/bergsstigen (samma stil som fyrvägen — speltest-
    # önskemål: "ännu mer mysig"), den långa sträckan mot berget var mörk
    for lx, lz in ((27, 25), (27, 40), (27, 55)):
        c.append(f"setblock {lx} {f} {lz} oak_fence")
        c.append(f'setblock {lx} {f+1} {lz} lantern ["hanging"=false]')
    # strukturerna (origins = sydvästra hörnet)
    c.append(f"structure load haven:shelter -6 {f} 8")
    c.append(("sleep", 2))
    # PARDÖRR i dörröppningen (lokal x5,x6 → värld -1,0). setblock sätter båda
    # dörrhalvorna korrekt — .mcstructure-vägen kräver handbyggda halvor med
    # gångjärns-states och gick inte att verifiera visuellt härifrån.
    # Katterna öppnar inga dörrar — kattluckan bredvid är deras väg.
    c.append(f'setblock -1 {f+1} 8 wooden_door ["direction"=3,"door_hinge_bit"=false]')
    c.append(f'setblock 0 {f+1} 8 wooden_door ["direction"=3,"door_hinge_bit"=true]')
    c.append(("sleep", 1))
    # trappsteg framför pardörren — golvet ligger ett block över marken
    # ("dörren sitter i fel höjd", Xbox-rapport)
    # trappsteget PÅ marken ({f}), inte I marklagret ({g}) — Xbox-rapport:
    # "trappen är i marken"
    c.append(f'setblock -1 {f} 7 oak_stairs ["upside_down_bit"=false,"weirdo_direction"=2]')
    c.append(f'setblock 0 {f} 7 oak_stairs ["upside_down_bit"=false,"weirdo_direction"=2]')
    # kattskylten vid entrén
    c.append(f"structure load haven:catsign 2 {f} 6")
    # poolskylten på dammens västra strand
    c.append(f"structure load haven:poolsign 11 {f} 5")
    # öskylten bredvid: pekar ut ön i dammen som en av de tre nyckelplatserna
    c.append(f"structure load haven:islandsign 11 {f} 4")
    c.append(("sleep", 1))
    c.append(f"testforblock 11 {f} 4 standing_sign")
    # dekor längs fyrvägen: lyktstolpar + blommor + två extra ekar
    for lx, lz in ((10, 12), (7, 20), (10, 28), (7, 36), (10, 44)):
        c.append(f"setblock {lx} {f} {lz} oak_fence")
        c.append(f'setblock {lx} {f+1} {lz} lantern ["hanging"=false]')
    for px, pz in ((11, 10), (11, 18), (6, 26), (11, 34), (5, 44)):   # (6,10) satt i husväggen
        c.append(f"setblock {px} {f} {pz} poppy")
    for dx, dz in ((10, 15), (7, 31), (12, 41)):
        c.append(f"setblock {dx} {f} {dz} dandelion")
    c.append(("sleep", 2))
    # MYSFAKTORN (speltest-önskemål: "fylligare och mysigare"): blomsterrabatt
    # vid entrén, en bänk, en lägereldsplats väster om huset, damm-grönska och
    # en välkomstmatta — allt med redan bevisade blocktyper (inga nya NBT-risker).
    for fx, fz, fl in ((-3, 7, "oxeye_daisy"), (3, 7, "cornflower"),
                       (-4, 6, "azure_bluet"), (4, 6, "blue_orchid")):
        c.append(f"setblock {fx} {f} {fz} {fl}")
    # bänken vid entrén (samma trappsteg-orientering som redan sitter fint)
    c.append(f'setblock -4 {f} 5 oak_stairs ["upside_down_bit"=false,"weirdo_direction"=2]')
    c.append(f'setblock -3 {f} 5 oak_stairs ["upside_down_bit"=false,"weirdo_direction"=2]')
    # lägereldsplatsen: värme och ljus i mörkret, stubbar att sitta på
    c.append(f"setblock -4 {f} 3 campfire")
    for sx, sz in ((-5, 3), (-3, 3), (-4, 2)):
        c.append(f'setblock {sx} {f} {sz} oak_log ["pillar_axis"="y"]')
    c.append(("sleep", 1))
    # dammens gröna kant: sockerrör och fler blommor, plus en fiskebänk
    # OBS: kommandonamnet är "reeds", inte "sugar_cane" (spelnamnet) — det
    # senare gav "Syntax error: Unexpected 'sugar_cane'" och fällde bygget.
    for cx, cz in ((11, 3), (11, 7), (11, 11)):
        c.append(f"setblock {cx} {f} {cz} reeds")
    for fx, fz, fl in ((13, 2, "azure_bluet"), (14, 11, "cornflower")):
        c.append(f"setblock {fx} {f} {fz} {fl}")
    c.append(f'setblock 9 {f} 4 oak_stairs ["upside_down_bit"=false,"weirdo_direction"=1]')
    c.append(f'setblock 9 {f} 5 oak_stairs ["upside_down_bit"=false,"weirdo_direction"=1]')
    c.append(("sleep", 1))
    # välkomstmattan strax innanför dörren
    c.append(f"setblock -1 {f+1} 9 red_carpet")
    c.append(f"setblock 0 {f+1} 9 red_carpet")
    c.append(("sleep", 1))
    c.append(f"testforblock -4 {f} 3 campfire")           # lägerelden brinner
    c.append(f"testforblock 0 {f+1} 9 red_carpet")         # välkomstmattan ligger
    for tx, tz in ((13, 32), (-12, 36)):
        c.append(f"structure load haven:tree {tx} {g+1} {tz}")
        c.append(("sleep", 1))
    # MAJA/SNOW ÄR FÖRSVUNNEN: mörk skog LÅNGT i väster, bakom en flod med
    # en enda bro — svårare att nå (speltest-önskemål). Spökkatter vaktar.
    # floden: 4 bred, 2 djup, rinner N-S mellan byn och skogen
    c.append(f"fill -22 {g-1} -6 -19 {g} 92 air")
    c.append(("sleep", 2))
    c.append(f"fill -22 {g-1} -6 -19 {g} 92 water")
    c.append(("sleep", 2))
    # bron: enda överfarten, i liv med gräset
    c.append(f"fill -22 {g} 45 -19 {g} 45 oak_planks")
    c.append(("sleep", 1))
    for tx, tz in ((-52, 32), (-46, 31), (-39, 33), (-33, 34), (-53, 40),
                   (-47, 39), (-40, 40), (-34, 42), (-51, 47), (-38, 47),
                   (-33, 50), (-49, 54), (-43, 55), (-36, 56), (-52, 60),
                   (-45, 61), (-39, 60)):
        c.append(f"structure load haven:darktree {tx} {g+1} {tz}")
        c.append(("sleep", 1))
    # vävarna får INTE dela cell med trädstammar (origin+3) — en väv ersatte
    # en stambas och trädet svävade ("träd står på spindelväv", Xbox-rapport)
    for wx, wz in ((-41, 36), (-47, 45), (-33, 48), (-38, 54), (-45, 59)):
        c.append(f"setblock {wx} {f} {wz} web")
    # jordkulan i gläntan, mynning mot öster (dit spåret leder)
    c.append(f"fill -47 {g+1} 45 -42 {g+4} 49 dirt")
    c.append(f"fill -47 {g+4} 45 -42 {g+4} 49 grass_block")
    c.append(f"fill -46 {g+1} 46 -44 {g+2} 48 air")
    c.append(f"fill -43 {g+1} 47 -42 {g+2} 47 air")
    c.append(f"setblock -46 {g+1} 46 hay_block")
    c.append(f'setblock -44 {g+1} 46 soul_lantern ["hanging"=false]')
    c.append(f"setblock -45 {g+1} 46 white_carpet")     # varm sovgrop, nyss lämnad
    c.append(f"structure load haven:denclue -45 {g+1} 47")
    c.append(("sleep", 2))
    # NYA KULAN: Maja har flyttat djupt åt SYDVÄST — lövtäckt, smal ingång i
    # söder (bortvänd från spåret), ingen lykta utanför. Barnen hittade den
    # gamla för lätt (Xbox-rapport 2026-08-09) — nu krävs riktigt letande.
    c.append(f"fill -54 {g+1} 64 -49 {g+4} 68 dirt")
    c.append(f"fill -54 {g+4} 64 -49 {g+4} 68 grass_block")
    c.append(f'fill -54 {g+5} 64 -49 {g+5} 68 oak_leaves ["persistent_bit"=true]')
    c.append(f"fill -53 {g+1} 65 -50 {g+2} 67 air")
    c.append(f"fill -52 {g+1} 68 -52 {g+2} 68 air")
    c.append(f"setblock -53 {g+1} 65 hay_block")
    c.append(f'setblock -50 {g+1} 67 soul_lantern ["hanging"=false]')
    c.append(f"setblock -52 {g+1} 66 mjau:kattbadd")
    # BUREN: Maja hålls fången bakom mörk ek — vakthundens verk. Staketet
    # bryts snabbt för hand, men hunden har andra åsikter om saken.
    for cx, cz in ((-53, 66), (-51, 66), (-52, 65), (-52, 67)):
        c.append(f"fill {cx} {g+1} {cz} {cx} {g+2} {cz} dark_oak_fence")
    c.append(("sleep", 2))
    # VAKTHUNDEN utanför ingången (persistent, hemma-radie håller den vid kulan)
    c.append(f'summon mjau:vakthund "{dog_name}" -52 {f} 69')
    c.append(("sleep", 1))
    c.append(f"testfor @e[type=mjau:vakthund,x=-52,y={f},z=69,r=15]")
    c.append(("sleep", 2))
    # ETT enda tassavtryck halvvägs — resten är upp till letaren
    c.append(f"setblock -49 {f} 58 white_carpet")
    # FALSKT spår åt nordost, slutar vid en spökkatt-glänta
    for wx, wz in ((-38, 52), (-36, 56), (-35, 60)):
        c.append(f"setblock {wx} {f} {wz} white_carpet")
    c.append(("sleep", 2))
    # vita pälstussar: dammen -> västerut -> BRON -> in i skogen -> mynningen
    for wx, wz in ((14, 14), (8, 20), (0, 26), (-8, 32), (-14, 38),
                   (-17, 43), (-24, 46), (-30, 47), (-35, 48), (-40, 48)):
        c.append(f"setblock {wx} {f} {wz} white_carpet")
    # själslyktor som kusliga vägmärken: en vid bron, en i skogsbrynet
    c.append(f'setblock -17 {f} 45 soul_lantern ["hanging"=false]')
    c.append(f'setblock -31 {f} 46 soul_lantern ["hanging"=false]')
    c.append(("sleep", 2))
    # läskig skogsbotten: podsol i sjok + döda buskar + extra vävar + tätare
    for px1, pz1, px2, pz2 in ((-50, 33, -44, 39), (-42, 44, -35, 52),
                               (-48, 55, -42, 60), (-34, 36, -30, 42)):
        c.append(f"fill {px1} {g} {pz1} {px2} {g} {pz2} podzol replace grass_block")
    for dx, dz in ((-47, 37), (-39, 45), (-34, 53), (-44, 53), (-31, 41)):
        c.append(f"setblock {dx} {f} {dz} deadbush")
    for wx, wz in ((-49, 41), (-36, 44), (-42, 58)):
        c.append(f"setblock {wx} {f} {wz} web")
    for tx, tz in ((-55, 44), (-31, 57), (-44, 36), (-58, 63), (-57, 58), (-50, 70)):
        c.append(f"structure load haven:darktree {tx} {g+1} {tz}")
        c.append(("sleep", 1))
    # fladdermöss mellan stammarna
    for bx, bz in ((-40, 45), (-35, 52), (-52, 70)):
        c.append(f"summon minecraft:bat {bx} {f+2} {bz}")
    c.append(("sleep", 2))
    # spökkatterna: de gamla katternas andar, namnlösa ("???"), ofarliga
    for sx, sz in ((-38, 40), (-48, 52), (-34, 55)):
        c.append(f'summon mjau:spokkatt "???" {sx} {f} {sz}')
        c.append(("sleep", 1))
        c.append(f"event entity @e[type=mjau:spokkatt,x={sx},y={f},z={sz},r=8] mjau:grow_up")
    c.append(f"testfor @e[type=mjau:spokkatt,x=-38,y={f},z=40,r=40]")
    c.append(f"testforblock -20 {g} 45 oak_planks")     # bron finns
    c.append(("sleep", 1))
    c.append(f"structure load haven:bowchest_green -46 {f} 44")   # skogens band
    c.append(f"setblock -45 {f} 44 green_wool")                    # syns på håll
    c.append(("sleep", 1))
    # ===================================================================
    # UTÖKNINGEN (speltest-önskemål: "större värld och fler saker att
    # göra"): äng, grotta, ö i dammen, ny skogslund — knutna ihop av tre
    # nycklar som tillsammans låser upp utmärkelsen "Trippelskatten".
    # ===================================================================

    # ÄNGEN öster om huset: vildblommor, bikupor med bin, kaniner
    # (ingen markfyllning behövs — flat-marken är redan gräs här. Ett
    # onödigt "fill grass_block->grass_block" gav "0 blocks filled", vilket
    # build_world.py:s ERROR-grep flaggar som byggfel trots att inget var fel.)
    _mf = ["poppy", "dandelion", "cornflower", "oxeye_daisy",
           "azure_bluet", "blue_orchid", "allium", "red_tulip"]
    # (31-39,13-21) är grottkullens fotavtryck (byggs strax nedan) — inga
    # blommor/kaniner får hamna där, de skulle begravas i sten.
    # (25,18) och (24,16) undvikna — de hamnar på den nya stigen österut
    _mspots = [(26, 7), (28, 10), (31, 6), (33, 12), (35, 8), (27, 15),
               (30, 18), (37, 10), (29, 22), (23, 20), (32, 23), (28, 21)]
    for i, (mx, mz) in enumerate(_mspots):
        c.append(f"setblock {mx} {f} {mz} {_mf[i % len(_mf)]}")
    for hx, hz in ((27, 9), (37, 8)):
        c.append(f'setblock {hx} {f} {hz} beehive ["direction"=0]')
        c.append(("sleep", 1))
        c.append(f"summon minecraft:bee {hx} {f+1} {hz}")
        c.append(f"summon minecraft:bee {hx} {f+1} {hz}")
    for rx, rz in ((25, 12), (30, 8), (24, 20)):
        c.append(f"summon minecraft:rabbit {rx} {f} {rz}")
    c.append(("sleep", 2))
    c.append(f"testforblock 27 {f} 9 beehive")
    c.append(f"structure load haven:bowchest_blue 34 {f} 9")   # ängens band
    c.append(f"setblock 35 {f} 9 blue_wool")                    # syns på håll
    c.append(("sleep", 1))

    # GROTTAN: stenkulle med tunnel in till en kristallkammare + nyckelkista
    c.append(f"fill 31 {f} 13 39 {f+4} 21 stone")
    c.append(f"fill 35 {f} 17 35 {f+1} 21 air")            # tunnelingång
    c.append(f"fill 33 {f} 13 37 {f+2} 16 air")             # kammaren
    c.append(f"fill 33 {f+2} 13 37 {f+2} 13 budding_amethyst")
    c.append(f"fill 33 {f} 13 33 {f+1} 13 amethyst_block")
    c.append(f"fill 37 {f} 13 37 {f+1} 13 amethyst_block")
    c.append(f'setblock 35 {f} 14 soul_lantern ["hanging"=false]')
    c.append(("sleep", 2))
    c.append(f"structure load haven:cavechest 35 {f} 13")
    c.append(("sleep", 1))
    c.append(f"testforblock 35 {f} 13 chest")

    # NY SKOGSLUND: pälsspår längre in i skogen till en gömd glänta + kista
    for wx, wz in ((-44, 62), (-42, 68), (-40, 74)):
        c.append(f"setblock {wx} {f} {wz} white_carpet")
    c.append(f"setblock -39 {f} 78 hay_block")
    c.append(f'setblock -38 {f} 78 soul_lantern ["hanging"=false]')
    c.append(("sleep", 1))
    c.append(f"structure load haven:forestchest -39 {f} 79")
    c.append(("sleep", 1))
    c.append(f"testforblock -39 {f} 79 chest")
    c.append(("sleep", 1))

    # HÖGA BERGET: klättringsbar, terrasserad bergstopp (samma teknik som
    # fyrkullen, bara mycket högre) söder om ängen — snötäckt topp med en
    # utsiktskista. Centrum (26,80), radie 12->1 ger 12 nivåer (höjd 12).
    # Fotavtryck x14-38,z68-92 — klart av äng/grotta (x24-40,z4-23, annan
    # z), fyrkullen (x-10-10,z46-66, annan x/z) och skogslunden (x<-38).
    _mtx, _mtz = 26, 80
    _mradii = list(range(12, 0, -1))
    for i, r in enumerate(_mradii):
        y = f + i
        mat = "snow" if i >= len(_mradii) - 3 else "stone"
        c.append(f"fill {_mtx-r} {y} {_mtz-r} {_mtx+r} {y} {_mtz+r} {mat}")
    c.append(("sleep", 2))
    c.append(f"structure load haven:bowchest_purple {_mtx+4} {f} {_mtz-12}")   # bergsfotens band
    c.append(f"setblock {_mtx+5} {f} {_mtz-12} purple_wool")                    # syns på håll
    c.append(("sleep", 1))
    c.append(f"structure load haven:mountainchest {_mtx} {f+len(_mradii)} {_mtz}")
    c.append(("sleep", 1))
    c.append(f"testforblock {_mtx} {f} {_mtz-12} stone")               # basen är berg
    c.append(f"testforblock {_mtx} {f+len(_mradii)-1} {_mtz} snow")  # toppens snötäcke
    c.append(f"testforblock {_mtx} {f+len(_mradii)} {_mtz} chest")         # utsiktskistan
    c.append(("sleep", 1))

    # KATTBANAN: hinderbana av flytande plattformar öster om ängen/grottan
    # — rid katten och hoppa (charged jump, samma mekanik som redan bär upp
    # fyrkullen) plattform till plattform. jump_strength=1.2 ger gott om
    # marginal för dessa ~4-block-hopp. Stegen upp är kommandoplacerad utan
    # väggstöd — samma bevisade knep som källarschaktets stege (ladder-block
    # kräver inget grannstöd när det placeras via kommando).
    # Xbox-önskemål: "längre bort" (flyttad från x42 till x56, en egen
    # grusstig knyter an den till grottan/ängen i stället för att bara stå
    # där) + "mysigare" (varmt granträ + lyktor + grönska i stället för bar
    # vit quartz — samma soul_lantern-stil som grottan/skogslunden).
    # stigen NEDSÄNKT i marken ({g}, inte {f}) som alla andra stigar — den
    # låg en ruta ovanpå gräset och läste som en kant, inte en stig
    c.append(f"fill 41 {g} 10 46 {g} 10 gravel")
    c.append(f"setblock 45 {f} 11 oak_fence")
    c.append(f'setblock 45 {f+1} 11 lantern ["hanging"=false]')
    c.append(("sleep", 1))
    _pkx0, _pkz0 = 56, 10
    # Xbox-rapport: "fortfarande högt upp i luften ... måste manuellt bygga
    # en stege" — hela banan sänkt (max f+8 i stället för f+11, snart f+14)
    # så stegen upp blir kort och känns som en trappa, inte en byggarbets-
    # plats. Svårigheten i förlängningen kommer från större hopp och
    # smalare plattformar i stället för mer höjd.
    _pk_platforms = [
        (0, 4, 0), (4, 4, 3), (8, 5, 0), (12, 5, 3),
        (16, 6, 0), (20, 6, 3), (24, 7, 0), (28, 7, 3),
        (32, 7, 0),
        # SVÅRARE FORTSÄTTNING (speltest-önskemål: "utöka och gör svårare") -
        # större hopp (5 rutor i stället för 4) och smalare plattformar
        # (radie 0 = en enda ruta i stället för 3x3, se radie-logiken nedan)
        # för de fem sista. Höjden guppar i stället för att fortsätta stiga.
        # Gamla målet (index 8) är nu bara en vanlig mellanplattform.
        (37, 8, 3), (42, 6, -3), (47, 8, 3), (52, 6, -3), (57, 7, 0),
    ]
    _PK_HARD_FROM = 9   # index där de smalare plattformarna börjar
    # INGÅNGEN: bred ridbar ramp av terrasserade steg i stället för stege
    # (speltest-önskemål: "gör en bättre ingång"). En stege var fel redan i
    # grunden — banan RIDS, och en katt kan inte klättra stege, så spelaren
    # tvingades kliva av och lämna katten på marken. Terrass-stegen är samma
    # bevisade teknik som fyrkullen/berget (katter kliver upp ett block i
    # taget medan man rider). Solid kil av granplankor, 3 bred (matchar
    # plattformarna), ett steg per ruta västerifrån där grusstigen anländer.
    for si, sx in enumerate((47, 49, 51, 53)):
        c.append(f"fill {sx} {f} 9 {sx+1} {f+si} 11 spruce_planks")
    for lz in (8, 12):   # lyktstolpar som flankerar rampfoten
        c.append(f"setblock 46 {f} {lz} oak_fence")
        c.append(f'setblock 46 {f+1} {lz} lantern ["hanging"=false]')
    for i, (dx, dy, dz) in enumerate(_pk_platforms):
        px, py, pz = _pkx0 + dx, f + dy, _pkz0 + dz
        if i == len(_pk_platforms) - 1:
            r = 2
        elif i >= _PK_HARD_FROM:
            r = 0   # smalast möjliga - en enda ruta, ingen marginal vid landning
        else:
            r = 1
        c.append(f"fill {px-r} {py} {pz-r} {px+r} {py} {pz+r} spruce_planks")
        if r >= 1:   # ingen plats för hörndekor på en 1x1-ruta
            c.append(f'setblock {px-r} {py+1} {pz-r} soul_lantern ["hanging"=false]')
            c.append(f"setblock {px+r} {py+1} {pz+r} azalea_leaves_flowered")
        # stödpelare ner till marken (Xbox-rapport: "plattformarna flyger i
        # luften" — bara luft under dem läste som ett fel, inte som en bana).
        # Även startplattformen: stegen som tidigare agerade pelare är borta.
        c.append(f"fill {px} {f} {pz} {px} {py - 1} {pz} stripped_spruce_log")
    c.append(("sleep", 2))
    # skylten vid rampfoten (gamla platsen x=54 ligger numera INUTI rampen)
    c.append(f"structure load haven:parkoursign 45 {f} 9")
    c.append(("sleep", 1))
    _pkfx = _pkx0 + _pk_platforms[-1][0]
    _pkfy = f + _pk_platforms[-1][1]
    _pkfz = _pkz0 + _pk_platforms[-1][2]
    c.append(f"structure load haven:parkourchest {_pkfx} {_pkfy + 1} {_pkfz}")
    c.append(("sleep", 1))
    c.append(f"testforblock {_pkx0} {f + 4} {_pkz0} spruce_planks")    # startplattformen
    c.append(f"testforblock 53 {f + 3} 10 spruce_planks")              # rampens översta steg
    c.append(f"testforblock {_pkfx} {_pkfy} {_pkfz} spruce_planks")    # målplattformen
    c.append(f"testforblock {_pkfx} {_pkfy + 1} {_pkfz} chest")        # prisskistan
    c.append(("sleep", 1))

    # hemliga källaren: rum under huset, schakt upp till golvcellen under
    # kartongen (världs-x5,z9) — kartongen laddas ovanpå och döljer hålet
    c.append(f"structure load haven:cellar 1 {g-3} 8")   # helt under huset, ovanpå bedrock
    c.append(("sleep", 2))
    c.append(f"fill 5 {g-1} 9 5 {f} 9 air")            # genom golvet upp till kartongcellen
    c.append(f'fill 5 {g-1} 9 5 {f} 9 ladder ["facing_direction"=2]')
    c.append(("sleep", 1))
    c.append(f"testforblock 2 {g-2} 12 chest")          # källarkistan
    # INREDNINGEN (plan B mot groparna): kommandoplacerade custom-block —
    # strukturvägen ger nedsjunken klientrendering, kommandovägen är felfri
    for bx in (2, 4, 8, 10):
        c.append(f"setblock {bx-6} {f+1} 16 mjau:kattbadd")
    c.append(f"setblock -4 {f+1} 13 mjau:matskal")
    c.append(f"setblock -3 {f+1} 13 mjau:matskal")
    c.append(f"setblock -5 {f+1} 14 mjau:kattoa")
    c.append(f"setblock 5 {f+1} 14 mjau:stallning")
    c.append(f"setblock 0 {f+1} 13 mjau:garnnystan")
    c.append(f"setblock 5 {f+1} 9 mjau:kartong")
    c.append(f"setblock 12 {g+1} 7 mjau:fiskdamm")
    c.append(("sleep", 2))
    c.append(f"testforblock -4 {f+1} 16 mjau:kattbadd")  # sängraden på plats
    c.append(f"testforblock 6 {f+5} 12 pink_wool")       # kattnosen på gaveln
    c.append(f"testforblock 0 {f+9} 12 spruce_planks")   # taknocken

    # VINDEN (speltest-önskemål: "mer hemliga saker och fler byggnader"):
    # husets inre är öppet ända upp till nocken — ett loftgolv på f+5 över
    # BAKRE halvan (z13-16) lämnar entréhalvan katedralöppen med ljuskronorna
    # synliga (z12). Vägen upp: hoppa på kattornet (5,f+1,14), klättra
    # gavelstegen (f+2..f+4) och upp genom luckhålet i loftet — hittbart men
    # inte uppenbart; dagboken i källaren fick en ledtrådssida. OBS takgeometrin:
    # baksluttningens trappor ligger på y6@z16, y7@z15, y8@z14 — därför står
    # man bara upprätt på z13-14, möblerna på z15 är låg dekor, och kistan
    # ligger på z13 (en kista under en trappa på y7 kan inte öppnas).
    # OBS stegen på z15, INTE z14: östväggens fönster sitter i just z14-
    # kolumnen (glasrutor på de två nedre höjderna) och stegar fäster inte
    # i glas — de poppade av vid första blockuppdateringen. z15 är massiv ek.
    c.append(f"fill -5 {f+5} 13 5 {f+5} 16 spruce_planks")
    c.append(f"setblock 5 {f+5} 15 air")                     # luckhålet över stegen
    c.append(f'fill 5 {f+2} 15 5 {f+4} 15 ladder ["facing_direction"=4]')
    c.append(("sleep", 1))
    # Xbox-rapport: "man kunde ta kistan på vinden från golvet" — kistan låg
    # på z13, loftets YTTERSTA rad mot den öppna entréhalvan (z9-12 saknar
    # golv hela vägen upp till nocken). Flyttad till z14, en rad längre in,
    # så det inte går att nå den från den öppna halvan. z15+ går inte:
    # baksluttningens trappa på f+7 skulle ligga direkt ovanpå kistan och
    # då går den inte att öppna alls.
    c.append(f"structure load haven:atticchest 0 {f+6} 14")
    c.append(f"setblock -3 {f+6} 15 mjau:kattbadd")
    c.append(f"setblock 0 {f+6} 15 mjau:garnnystan")
    c.append(f'setblock -5 {f+6} 14 soul_lantern ["hanging"=false]')
    c.append(f"setblock 2 {f+6} 15 web")                     # vindsdamm
    c.append(f"setblock -5 {f+6} 15 web")
    c.append(("sleep", 1))
    c.append(f"testforblock 0 {f+5} 14 spruce_planks")   # loftgolvet
    c.append(f"testforblock 5 {f+3} 15 ladder")          # gavelstegen
    c.append(f"testforblock 0 {f+6} 14 chest")           # vindskistan
    c.append(("sleep", 1))
    c.append(f"structure load haven:welcome 1 {f} 1")
    c.append(("sleep", 1))
    c.append(f"structure load haven:startsign -2 {f} 1")
    c.append(("sleep", 1))
    # GAMLA FÖRESTÅNDARENS TÄPPA: bakom skyltarna (norr om spawn) var det
    # bara tom gräsmatta (speltest-önskemål: "väldigt tomt bakom där man
    # startat"). En köksträdgård + redskapsskjul knyter an till dagbokens
    # gamle föreståndare som "grävde och odlade" i stället för att spara i bank.
    c.append(f"fill -6 {g} -13 0 {g} -9 farmland")
    # vattnet MÅSTE ligga en nivå UNDER grödorna (samma knep som dammen) —
    # på samma nivå ({g+1}) sprider det sig sidledes rakt in i grannodlingarna
    # och tvättar bort dem (bevisat: "-3,-13 blev vatten, inte gröda").
    c.append(f"setblock -3 {g} -11 water")
    c.append(("sleep", 3))
    for cx in range(-6, 1):
        for cz in (-13, -12, -10, -9):
            crop = "wheat" if cz in (-13, -9) else ("carrots" if (cx + cz) % 2 == 0 else "potatoes")
            c.append(f'setblock {cx} {g+1} {cz} {crop} ["growth"=7]')
    c.append(("sleep", 2))
    c.append(f'setblock -2 {g+1} -11 hay_block')                     # fågelskrämman
    c.append(f'setblock -2 {g+2} -11 carved_pumpkin ["direction"=2]')
    # redskapsskjulet: enkel bänk under tak, öster om täppan
    # BUGFIX (Xbox-rapport: "ett lager som ligger uppe på grejerna"): stolparna
    # låg på {g} (marknivån själv, ersatte gräset) i stället för {f} (en ruta
    # ovanpå marken, samma konvention som all annan dekor i filen) — taket satt
    # då en hel ruta för högt och svävade löst ovanför stolptopparna.
    for fx, fz in ((4, -13), (7, -13), (4, -11), (7, -11)):
        c.append(f"setblock {fx} {f} {fz} oak_fence")
    c.append(f"fill 3 {f+1} -14 8 {f+1} -10 oak_slab")
    c.append(f'setblock 5 {g+1} -12 crafting_table')
    c.append(f'setblock 6 {g+1} -12 barrel ["facing_direction"=1]')
    c.append(f'setblock 6 {g+1} -13 barrel ["facing_direction"=1]')
    c.append(("sleep", 1))
    c.append(f"testforblock -3 {g+1} -13 wheat")
    c.append(f"testforblock 5 {g+1} -12 crafting_table")
    c.append(("sleep", 1))
    c.append(f"structure load haven:bowchest_red 8 {f} -11")   # täppans band
    c.append(f"setblock 8 {f} -10 red_wool")                    # syns på håll
    c.append(("sleep", 1))
    # HANDELSPOSTEN: en tunna öster om täppan där skattletarnas fynd kan
    # lämnas in (speltest-önskemål: "treasure trading post")
    c.append(f'setblock 10 {f} -11 barrel ["facing_direction"=1]')
    c.append(f"structure load haven:tradesign 10 {f} -10")
    c.append(("sleep", 1))
    c.append(f"testforblock 10 {f} -11 barrel")
    c.append(f"testforblock 10 {f} -10 standing_sign")
    c.append(("sleep", 1))
    c.append(f"structure load haven:pond 12 {g-2} 2")
    c.append(("sleep", 1))
    # ÖN I DAMMEN: torr ö i dammens nordvästra hörn — MÅSTE läggas EFTER
    # pond-strukturen (annars laddar dammen sin egen sten/vatten ovanpå och
    # begraver ön). Hörnet, INTE mitten (17,7): (17,-61,7) är fiskekattens
    # fasta plats och den befintliga vattenkontrollen — en ö där hade
    # begravt fiskeuppdraget.
    c.append(f"fill 13 {g-1} 3 15 {g-1} 5 dirt")
    c.append(f"fill 13 {g} 3 15 {g} 5 grass_block")
    c.append(("sleep", 1))
    c.append(f"structure load haven:islandchest 14 {f} 4")
    c.append(("sleep", 1))
    c.append(f"summon minecraft:boat 19 {f} 9")
    c.append(f"testforblock 14 {g} 4 grass_block")
    c.append(f"testforblock 17 {g} 7 water")            # dammens fiskeplats orörd
    c.append(f"structure load haven:bowchest_orange 23 {f} 8")   # dammens band
    c.append(f"setblock 24 {f} 8 orange_wool")                    # syns på håll
    c.append(("sleep", 1))
    c.append(f"structure load haven:lighthouse -3 {g+5} 53")
    c.append(("sleep", 2))
    c.append(f"structure load haven:bowchest_yellow -6 {f} 50")   # fyrkullens band
    c.append(f"setblock -5 {f} 50 yellow_wool")                    # syns på håll
    c.append(("sleep", 1))
    for tx, tz in ((-16, 20), (-12, 27), (-19, 30), (14, 24), (-13, 44), (16, 40)):
        c.append(f"structure load haven:tree {tx} {g+1} {tz}")
        c.append(("sleep", 1))
    # verifiera att nyckelblock faktiskt finns där de ska
    c.append(f"testforblock -4 {f+1} 9 chest")         # startkistan (världskoord)
    c.append(f"testforblock -1 {f+1} 8 wooden_door")   # pardörren
    c.append(f"testforblock 12 {g+1} 7 mjau:fiskdamm") # dammen (ramkanten)
    c.append(f"testforblock 17 {g} 7 water")           # vattnet i dammen
    c.append(f"testforblock 0 {g+20} 56 glowstone")    # fyrljuset (höjt ur huvudhöjd)
    c.append(("sleep", 2))
    # katterna: namngivna (persistenta), vuxna, otama — att hitta dem är uppdraget
    # mocha z=16 (INTE 13): 13 var samma cell som garnnystanet ("mjau:garnnystan"
    # i samma rad nedan) — katten spawnade bokstavligen INUTI bollen
    # (Xbox-rapport). z=16 är luckan mellan de mittersta sängarna, tomt golv.
    spots = {"misty": (-9, f), "hazel": (16, f), "mocha": (0, f + 1), "snow": (-52, f)}
    zs = {"misty": 33, "hazel": 8, "mocha": 16, "snow": 66}
    # VAKT: en katt fick en gång exakt samma (x,z) som en möbel och spawnade
    # inuti den. Möblernas fotavtryck (från setblocken ovan) — inga katt-spots
    # får träffa någon av dem.
    FURNITURE_XZ = {(-4, 13), (-3, 13), (-5, 14), (5, 14), (0, 13), (5, 9),
                    (-4, 16), (-2, 16), (2, 16), (4, 16), (12, 7)}
    for src, (x, y) in spots.items():
        assert (x, zs[src]) not in FURNITURE_XZ, f"{src} spawnar i en möbel vid ({x},{zs[src]})"
    for src, (x, y) in spots.items():
        c.append(f'summon mjau:{cats[src]} "{disp[src]}" {x} {y} {zs[src]}')
        c.append(("sleep", 1))
        c.append(f"event entity @e[type=mjau:{cats[src]}] mjau:grow_up")
    c.append(("sleep", 1))
    # konsol-testfor behöver positionsbundna selektorer (samma som purrfect-test)
    for src, (x, y) in spots.items():
        c.append(f"testfor @e[type=mjau:{cats[src]},x={x},y={y},z={zs[src]},r=60]")
        c.append(("sleep", 1))

    # SJÖN: en ny sjö med undervattensgrotta, öster om allt annat byggt
    # (speltest-önskemål: "underwater cave zone" — katterna simmar/fiskar
    # redan, men det fanns bara EN damm, och den är redan full av
    # testkoordinater/ön/fiskeplatsen — för skör att gräva i). Fast stenskal
    # byggs FÖRST, vatten/luft urholkas EFTER (samma "recessed water"-läxa
    # som den gamla dammen — vi vet inte att marken under g är solid utan
    # att bygga det själva).
    # BUGFIX: g-4 (=-65) ligger UNDER Bedrocks faktiska världsgolv (-64,
    # samma gräns källaren redan respekterar på g-3) — "Cannot place blocks
    # outside of the world". Tunneln/rummet ligger därför i SIDLED från
    # sjöbottnen (samma djup, g-2/g-1) i stället för ännu djupare ner.
    _lx, _lz = 65, 40
    c.append(f"fill {_lx-5} {g-3} {_lz-5} {_lx+5} {g} {_lz+11} stone")
    c.append(("sleep", 2))
    c.append(f"fill {_lx-4} {g-2} {_lz-4} {_lx+4} {g-1} {_lz+4} water")
    c.append(f"fill {_lx} {g-2} {_lz+5} {_lx} {g-1} {_lz+7} air")
    c.append(f"fill {_lx-1} {g-2} {_lz+8} {_lx+1} {g-1} {_lz+9} air")
    c.append(("sleep", 2))
    c.append(f"structure load haven:lakesign {_lx-4} {f} {_lz-5}")
    c.append(("sleep", 1))
    c.append(f"structure load haven:lakechest {_lx} {g-2} {_lz+9}")
    c.append(("sleep", 1))
    c.append(f"testforblock {_lx-4} {g-1} {_lz} water")     # sjön finns
    c.append(f"testforblock {_lx} {g-1} {_lz+6} air")       # tunneln är genomgrävd
    c.append(f"testforblock {_lx} {g-2} {_lz+9} chest")     # kistan i luftfickan
    c.append(("sleep", 1))

    # GRINDARNA (speltest-önskemål: "låsa ner delar av världen och öppna
    # stegvis när man klarar quests, så storyn blir tydligare"). Tre grindar
    # i story-kedja: ängsstigen (öppnas av fyrvaktaren/uppdrag 4), kattbanans
    # stig (trippelskatten/uppdrag 6) och sjötunnelns galler (hinderbanan/
    # uppdrag 7). Skriptet i main.js river dem när NÅGON spelare har klarat
    # förkravet. Koordinaterna här MÅSTE matcha GATES-listan i main.js.
    # Byn, dammen, mörka skogen och fyrvägen är alltid öppna.
    # Xbox-önskemål: staketen på 2 block gick att hoppa över med en katts
    # laddade hopp. Nu MURAR på 5 block (laddat hopp ger ~2-3), breda nog att
    # läsa som en riktig grindmur i stället för ett hopphinder: stenram med
    # stockportstolpar, lykta på krönet. Höjd/bredd MÅSTE matcha GATES-listan
    # i main.js — den river exakt de här blocken.
    for gx0, gx1, gz0, gz1, namn in ((20, 20, 12, 19, "A"), (44, 44, 5, 15, "B")):
        c.append(f"fill {gx0} {f} {gz0} {gx1} {f+4} {gz1} stone_bricks")
        # portstolpar i stock ger muren en tydlig mitt = "här ska man igenom"
        cz = (gz0 + gz1) // 2
        for dz in (-1, 1):
            c.append(f'fill {gx0} {f} {cz+dz} {gx1} {f+4} {cz+dz} stripped_spruce_log ["pillar_axis"="y"]')
        c.append(f'setblock {gx0} {f+5} {cz} lantern ["hanging"=false]')
    c.append(f"structure load haven:gate_meadow_sign 19 {f} 20")
    c.append(f"structure load haven:gate_parkour_sign 43 {f} 16")
    c.append(f"fill {_lx} {g-2} {_lz+5} {_lx} {g-1} {_lz+5} iron_bars")  # grind C: sjögallret
    c.append(f"structure load haven:gate_lake_sign {_lx-2} {f} {_lz-5}")
    c.append(("sleep", 2))
    c.append(f"testforblock 20 {f+4} 15 stone_bricks")     # murkrönet, grind A
    c.append(f"testforblock 44 {f+4} 10 stone_bricks")     # murkrönet, grind B
    c.append(f"testforblock {_lx} {g-2} {_lz+5} iron_bars")
    c.append(("sleep", 1))

    # SKOGSRAM: en trädrand runt hela den utforskade ytan (speltest-önskemål:
    # "mer skog runt om alltihopa i olika former") — ramar in kartan och
    # döljer var det byggda tar slut. Fyra trädslag varvas för variation,
    # lagd UTANFÖR allt annat byggt (marginal 3-5 rutor, ingen kollision).
    # BUGFIX: en enda tickingarea runt HELA ramen (171×130 rutor) slog i
    # Bedrocks hårda 100-chunks-tak ("ticking area is too large") och fick
    # kommandot att vägra köras — vilket i sin tur strök ALLA efterföljande
    # placeringar ("Cannot place blocks outside of the world") för resten
    # av bygget. Fyra smala remsor (en per kant) istället för en stor ruta
    # håller varje enskild tickingarea gott under gränsen.
    _forest_kinds = ["tree", "darktree", "sprucetree", "birchtree"]
    _fx0, _fx1, _fz0, _fz1 = -63, 125, -24, 96   # ram runt hela kartan (125: kattbanan når x=113)
    c.append(f"tickingarea add -65 {g-4} -26 -61 {g+30} 98 ramvast")
    c.append(("sleep", 4))
    c.append(f"tickingarea add 123 {g-4} -26 127 {g+30} 98 ramost")
    c.append(("sleep", 4))
    c.append(f"tickingarea add -65 {g-4} -26 127 {g+30} -22 ramnord")
    c.append(("sleep", 4))
    c.append(f"tickingarea add -65 {g-4} 94 127 {g+30} 98 ramsyd")
    c.append(("sleep", 4))
    _ring = []
    for rx in range(_fx0, _fx1 + 1, 5):
        _ring.append((rx, _fz0)); _ring.append((rx, _fz1))
    for rz in range(_fz0, _fz1 + 1, 5):
        _ring.append((_fx0, rz)); _ring.append((_fx1, rz))
    _animal_kinds = ["rabbit", "fox", "sheep"]
    for i, (tx, tz) in enumerate(_ring):
        kind = _forest_kinds[i % len(_forest_kinds)]
        jx = (i * 7) % 5 - 2    # deterministisk "slump": olika offset per träd, samma varje bygge
        jz = (i * 13) % 5 - 2
        c.append(f"structure load haven:{kind} {tx + jx} {g + 1} {tz + jz}")
        # djurliv (speltest-önskemål: "mer kaniner och andra djur som
        # springer runt längst ut i skogen") — glesare än träden
        if i % 4 == 0:
            akind = _animal_kinds[(i // 4) % len(_animal_kinds)]
            c.append(f"summon minecraft:{akind} {tx + jx} {f} {tz + jz}")
    c.append(f"structure load haven:sprucetree {_fx0} {g + 1} {_fz0}")   # ojitrad kontrollgran
    c.append(("sleep", 3))
    c.append(f"testforblock {_fx0 + 3} {g + 1} {_fz0 + 3} spruce_log")   # stammen sitter lokalt (3,*,3) i strukturen
    c.append(("sleep", 1))
    c.append("tickingarea remove ramvast")
    c.append("tickingarea remove ramost")
    c.append("tickingarea remove ramnord")
    c.append("tickingarea remove ramsyd")
    c.append(("sleep", 2))

    c.append(f"setworldspawn 0 {f} 0")
    c.append(("sleep", 1))
    c.append("tickingarea remove bygge")
    c.append(("sleep", 2))
    return c

# ------------------------------------------------------------- huvudflöde ----
def run_server_build(world_name, cmds, log_path):
    # EN Bedrock-server åt gången på maskinen — portarna är exklusiva och en
    # parallell purrfect-test/gametest får inte skjutas ner av vår pkill.
    import fcntl
    _lock = None
    if os.environ.get("BDS_LOCK_HELD") != "1":   # annars ärvt från cathaven-test
        _lock = open("/tmp/bds.lock", "w")
        fcntl.flock(_lock, fcntl.LOCK_EX)
    props = f"{SRV}/server.properties"
    orig = open(props).read()
    open(props, "w").write(orig.replace("level-name=Kattest", f"level-name={world_name}")
                               .replace("level-type=DEFAULT", "level-type=FLAT")
                           + ("" if "level-type=" in orig else "level-type=FLAT\n"))
    try:
        subprocess.run(["pkill", "-9", "-x", "bedrock_server"], capture_output=True)
        time.sleep(2)
        proc = subprocess.Popen(["./bedrock_server"], cwd=SRV, stdin=subprocess.PIPE,
                                stdout=open(log_path, "w"), stderr=subprocess.STDOUT,
                                env={**os.environ, "LD_LIBRARY_PATH": "."}, text=True)
        time.sleep(30)
        for cmd in cmds:
            if isinstance(cmd, tuple): time.sleep(cmd[1])
            else:
                proc.stdin.write(cmd + "\n"); proc.stdin.flush()
        proc.stdin.write("stop\n"); proc.stdin.flush()
        try: proc.wait(timeout=40)
        except subprocess.TimeoutExpired: proc.kill()
    finally:
        open(props, "w").write(orig)
        subprocess.run(["pkill", "-9", "-x", "bedrock_server"], capture_output=True)
        if _lock:
            fcntl.flock(_lock, fcntl.LOCK_UN); _lock.close()
    return open(log_path).read()

def postprocess_level_dat(world_dir, world_name):
    version, root = nbt.read_level_dat(f"{world_dir}/level.dat")
    d = root.v
    d["LevelName"] = S(world_name)
    d["Time"] = V(nbt.TAG_LONG, 14500)      # ankomst i skymningsmörker
    d["rainLevel"] = V(nbt.TAG_FLOAT, 1.0)  # ...och regn. Dystert.
    d["rainTime"] = I(9000)
    d["Difficulty"] = I(1)              # easy — familjevänligt men levande
    d["commandsEnabled"] = B(0)         # fusk av i den skeppade världen
    d["GameType"] = I(0)                # survival
    nbt.write_level_dat(f"{world_dir}/level.dat", version, root)
    open(f"{world_dir}/levelname.txt", "w").write(world_name)

def build(variant, outdir):
    t = TEXTS[variant]
    cfgs = json.load(open(f"{BASE}/variants.json"))
    pf = f"{BASE}/variants.private.json"
    if os.path.exists(pf): cfgs.update(json.load(open(pf, encoding="utf-8")))
    names = cfgs[variant].get("names") or {}
    cats = {src: names.get(src, (src, src.capitalize()))[0] for src in ("misty", "hazel", "mocha", "snow")}
    disp = {src: names.get(src, (src, src.capitalize()))[1] for src in ("misty", "hazel", "mocha", "snow")}
    for src in disp:                     # boktexten refererar katterna med namn
        t = {**t, "book_pages": [p.replace(f"%{src.upper()}%", disp[src]) for p in t["book_pages"]]}

    # 1) paketvarianten (rena paket att bädda in) + byggkopia med strukturerna
    packdir = f"/tmp/cathaven-packs-{variant}"
    subprocess.run([sys.executable, f"{BASE}/make_variant.py", variant, packdir],
                   check=True, capture_output=True)
    builddir = f"/tmp/cathaven-buildbp-{variant}"
    if os.path.exists(builddir): shutil.rmtree(builddir)
    shutil.copytree(f"{packdir}/PurrfectCompanions_BP", builddir)
    build_structures(builddir, t, disp, cats)

    # 2) koppla byggpaketet till servern och låt den bygga världen
    world_name = "CatHavenBuild"
    wdir = f"{SRV}/worlds/{world_name}"
    if os.path.exists(wdir): shutil.rmtree(wdir)
    os.makedirs(f"{wdir}/behavior_packs", exist_ok=True)
    os.makedirs(f"{wdir}/resource_packs", exist_ok=True)
    shutil.copytree(builddir, f"{wdir}/behavior_packs/PurrfectCompanions_BP")
    shutil.copytree(f"{packdir}/PurrfectCompanions_RP", f"{wdir}/resource_packs/PurrfectCompanions_RP")
    bp = json.load(open(f"{builddir}/manifest.json"))["header"]
    rp = json.load(open(f"{packdir}/PurrfectCompanions_RP/manifest.json"))["header"]
    json.dump([{"pack_id": bp["uuid"], "version": bp["version"]}],
              open(f"{wdir}/world_behavior_packs.json", "w"))
    json.dump([{"pack_id": rp["uuid"], "version": rp["version"]}],
              open(f"{wdir}/world_resource_packs.json", "w"))

    log = run_server_build(world_name, build_commands(cats, disp, t["dog_name"]), f"/tmp/cathaven-build-{variant}.log")
    problems = []
    found_blocks = log.count("found the block")   # 4 testforblock: mark, kista, damm, fyrljus
    found_cats = log.count("Found ")
    errors = [l.strip() for l in log.splitlines()
              if "Syntax error" in l or "Unknown block" in l or "ERROR" in l][:8]
    if found_blocks < 4: problems.append(f"bara {found_blocks}/4 kontrollblock hittades (mark+kista+damm+fyrljus)")
    if found_cats < 4: problems.append(f"bara {found_cats}/4 katter verifierade (testfor)")
    for e in errors: problems.append(f"serverfel: {e}")

    # 3) städa världen och packa .mcworld med RENA paket (utan strukturerna)
    shutil.rmtree(f"{wdir}/behavior_packs/PurrfectCompanions_BP")
    shutil.copytree(f"{packdir}/PurrfectCompanions_BP", f"{wdir}/behavior_packs/PurrfectCompanions_BP")
    ver = ".".join(map(str, bp["version"]))
    postprocess_level_dat(wdir, f'{t["world"]} {ver}')
    os.makedirs(outdir, exist_ok=True)
    suffix = "-familj" if variant == "private" else ""
    slug = "kattgarden" if variant == "private" else "cat-haven"
    out = f"{outdir}/{slug}-v{ver}{suffix}.mcworld"
    if os.path.exists(out): os.remove(out)
    icon = "/tmp/cathaven-world-icon.jpeg"                # världslistans bild
    if not os.path.exists(icon):
        subprocess.run([sys.executable, f"{BASE}/tools/promo/make_cathaven_art.py", "icon"],
                       check=True, capture_output=True)
    zf = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)
    for dirpath, _, files in os.walk(wdir):
        for fn in files:
            p = os.path.join(dirpath, fn)
            zf.write(p, os.path.relpath(p, wdir))
    zf.write(icon, "world_icon.jpeg")
    zf.close()
    print(f"värld: {out} ({os.path.getsize(out)//1024} KB)")

    # VÄRLDSMALL (.mctemplate) — speltest-önskemål: "att man kan återskapa
    # världen". En .mcworld importeras som EN spelbar kopia; en mall dyker
    # i stället upp under "Skapa ny värld" och kan återskapas färsk hur
    # många gånger som helst utan att filen behöver skickas om. Samma
    # zip-innehåll + template-manifest i roten. UUID:erna är deterministiska
    # (uuid5 av variantnamnet) så en ny version ERSÄTTER den gamla mallen i
    # spelet i stället för att lägga en dublett bredvid.
    import uuid as _uuid
    tman = {
        "format_version": 2,
        "header": {
            "name": t["world"],
            "description": f'{t["world"]} v{ver}',
            "uuid": str(_uuid.uuid5(_uuid.NAMESPACE_URL, f"mjau:worldtemplate:{variant}:header")),
            "version": bp["version"],
            "base_game_version": [1, 26, 40],
            "lock_template_options": False,
        },
        "modules": [{
            "type": "world_template",
            "uuid": str(_uuid.uuid5(_uuid.NAMESPACE_URL, f"mjau:worldtemplate:{variant}:module")),
            "version": bp["version"],
        }],
    }
    tout = f"{outdir}/{slug}-v{ver}{suffix}.mctemplate"
    if os.path.exists(tout): os.remove(tout)
    zf = zipfile.ZipFile(tout, "w", zipfile.ZIP_DEFLATED)
    for dirpath, _, files in os.walk(wdir):
        for fn in files:
            p = os.path.join(dirpath, fn)
            zf.write(p, os.path.relpath(p, wdir))
    zf.write(icon, "world_icon.jpeg")
    zf.writestr("manifest.json", json.dumps(tman, indent=2))
    zf.close()
    print(f"mall: {tout} ({os.path.getsize(tout)//1024} KB)")
    for p in problems: print(f"PROBLEM: {p}")
    return out, problems

if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "public"
    outdir = sys.argv[2] if len(sys.argv) > 2 else "/tmp"
    _, probs = build(variant, outdir)
    sys.exit(1 if probs else 0)
