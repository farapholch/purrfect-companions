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
        "dog_name": "The Guard Dog",
        "silverfish_name": "§bThe Silver Fish",
        "start_sign": "Start here:\nread the book\nin the chest\ninside ->",
        "chest_sign": "The handbook\nis in here!",
        "diary_title": "The Old Caretaker's Diary",
        "diary_author": "The Old Caretaker",
        "diary_pages": [
            "Day 214.\n\nThe backpack cat dug up a diamond today. I laughed until I cried.\n\nI buried nothing. They have their own economy down there.",
            "Day 388.\n\nA fifth cat came with the frost. Black as the space between the stars. She never let me feed her by hand.\n\nMidnight, I called her. The others speak of her still.",
            "Day 401.\n\nCold night. I left a silver fish on a cat bed, and by morning it was gone - and there were two sets of pawprints in the snow.\n\nIf you are reading this: she is still here. Somewhere.",
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
            "The beds inside carry the cats' names. Cat treats cheer them up when their tails droop - the recipe is sugar, wheat and cod.\n\nTake good care of them.\n\nAnd mind the boxes. Some hide more than dust.\n\n- The Old Caretaker",
            "One more thing, if you will believe an old man.\n\nThe cats used to tell of a FIFTH - black as the gap between the stars, with eyes of amber.\n\nShe shows herself only to those who leave the SILVER FISH from the lighthouse chest on a cat's bed while the moon stands at its highest.",
        ],
    },
    "private": {
        "world": "Kattgården",
        "welcome_sign": "Kattgården\nKatthemmet\nbehöver en ny\nföreståndare!",
        "den_clue": "Ännu varm...\ntassavtryck mot\nsydväst, djupt\nin i skogen",
        "pool_sign": "KATTPOOLEN\n/\\_/\\ ~\u2248~\n( ^.^ ) plask!\ninga hundar!",
        "dog_name": "Vakthunden",
        "silverfish_name": "§bSilverfisken",
        "start_sign": "Börja här:\nläs handboken\ni kistan\ndärinne ->",
        "chest_sign": "Handboken\nligger häri!",
        "diary_title": "Gamla föreståndarens dagbok",
        "diary_author": "Gamla föreståndaren",
        "diary_pages": [
            "Dag 214.\n\nRyggsäckskatten grävde upp en diamant i dag. Jag skrattade tills jag grät.\n\nJag grävde aldrig ner något. De har sin egen ekonomi där nere.",
            "Dag 388.\n\nEn femte katt kom med frosten. Svart som mellanrummet mellan stjärnorna. Hon lät mig aldrig mata henne ur handen.\n\nMidnight kallade jag henne. De andra talar om henne än.",
            "Dag 401.\n\nKall natt. Jag lämnade en silverfisk på en kattbädd, och på morgonen var den borta - och det fanns två rader tassavtryck i snön.\n\nLäser du det här: hon är kvar. Någonstans.",
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
            "Sängarna därinne bär katternas namn. Kattgodis piggar upp dem när svansen hänger - receptet är socker, vete och torsk.\n\nTa väl hand om dem.\n\nOch se upp med lådorna. Vissa gömmer mer än damm.\n\n- Gamla föreståndaren",
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

# ------------------------------------------------------ serverkommandona ----
def build_commands(cats, disp, dog_name):
    g, f = GROUND, FLOOR
    c = []
    c.append("gamerule commandblockoutput false")
    c.append("gamerule domobspawning false")
    c.append("gamerule keepinventory true")
    c.append("gamerule sendcommandfeedback true")
    c.append(f"tickingarea add -58 {g-4} -20 40 {g+30} 92 bygge")
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
    c.append(("sleep", 1))
    # dekor längs fyrvägen: lyktstolpar + blommor + två extra ekar
    for lx, lz in ((10, 12), (7, 20), (10, 28), (7, 36), (10, 44)):
        c.append(f"setblock {lx} {f} {lz} oak_fence")
        c.append(f'setblock {lx} {f+1} {lz} lantern ["hanging"=false]')
    for px, pz in ((11, 10), (11, 18), (6, 26), (11, 34), (5, 44)):   # (6,10) satt i husväggen
        c.append(f"setblock {px} {f} {pz} poppy")
    for dx, dz in ((10, 15), (7, 31), (12, 41)):
        c.append(f"setblock {dx} {f} {dz} dandelion")
    c.append(("sleep", 2))
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
    c.append(f"structure load haven:welcome 1 {f} 1")
    c.append(("sleep", 1))
    c.append(f"structure load haven:startsign -2 {f} 1")
    c.append(("sleep", 1))
    c.append(f"structure load haven:pond 12 {g-2} 2")
    c.append(("sleep", 1))
    c.append(f"structure load haven:lighthouse -3 {g+5} 53")
    c.append(("sleep", 2))
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
    out = f"{outdir}/purrfect-{slug}-v{ver}{suffix}.mcworld"
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
    for p in problems: print(f"PROBLEM: {p}")
    return out, problems

if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "public"
    outdir = sys.argv[2] if len(sys.argv) > 2 else "/tmp"
    _, probs = build(variant, outdir)
    sys.exit(1 if probs else 0)
