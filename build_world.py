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

BLOCK_VERSION = 18168865   # samma som gametest-arenan (laddaren uppgraderar)
SRV = "/opt/bds/server"
GROUND = -61               # översta solida blocket i FLAT (verifieras i bygget)
FLOOR = GROUND + 1         # fötterna/golvnivån

# ---------------------------------------------------------------- texter ----
TEXTS = {
    "public": {
        "world": "Cat Haven",
        "welcome_sign": "Cat Haven\nThe shelter needs\na new caretaker!",
        "book_title": "The Caretaker's Handbook",
        "book_author": "The Old Caretaker",
        "book_pages": [
            "Welcome to Cat Haven!\n\nI am too old to care for the shelter now. The four cats still live in these hills - they just need someone to trust again.\n\nEverything you need is in this chest.",
            "TASK 1 - FIND THE CATS\n\n%MOCHA% never left the shelter. %HAZEL% fishes by the pond. %MISTY% hides among the trees. %SNOW% wanders the lighthouse road.\n\nTame them with the cod from this chest.",
            "TASK 2 - A CATCH FROM THE POND\n\nPut the saddle on a cat and wade into the pond together.\n\nA saddled cat catches cod all by itself. Let it fish your next meal!",
            "TASK 3 - RIDE TO THE LIGHTHOUSE\n\nFollow the gravel road south and ride to the top of the lighthouse hill.\n\nSomething useful waits in the chest at the top of the tower.",
            "The beds inside carry the cats' names. Cat treats cheer them up when their tails droop - the recipe is sugar, wheat and cod.\n\nTake good care of them.\n\n- The Old Caretaker",
            "One more thing, if you will believe an old man.\n\nThe cats used to tell of a FIFTH - black as the gap between the stars, with eyes of amber.\n\nShe shows herself only to those who leave a silver fish on a cat's bed while the moon stands at its highest.",
        ],
    },
    "private": {
        "world": "Kattgården",
        "welcome_sign": "Kattgården\nKatthemmet behöver\nen ny föreståndare!",
        "book_title": "Föreståndarens handbok",
        "book_author": "Gamla föreståndaren",
        "book_pages": [
            "Välkommen till Kattgården!\n\nJag är för gammal för att sköta katthemmet nu. De fyra katterna bor kvar i kullarna - de behöver bara någon att lita på igen.\n\nAllt du behöver ligger i den här kistan.",
            "UPPDRAG 1 - HITTA KATTERNA\n\n%MOCHA% lämnade aldrig katthemmet. %HAZEL% fiskar vid dammen. %MISTY% gömmer sig bland träden. %SNOW% strövar på fyrvägen.\n\nTämj dem med torsken ur kistan.",
            "UPPDRAG 2 - EN FÅNGST UR DAMMEN\n\nSätt sadeln på en katt och vada ut i dammen tillsammans.\n\nEn sadlad katt fångar torsk alldeles själv. Låt den fiska din nästa måltid!",
            "UPPDRAG 3 - RID TILL FYREN\n\nFölj grusvägen söderut och rid upp för fyrkullen.\n\nNågot användbart väntar i kistan högst upp i tornet.",
            "Sängarna därinne bär katternas namn. Kattgodis piggar upp dem när svansen hänger - receptet är socker, vete och torsk.\n\nTa väl hand om dem.\n\n- Gamla föreståndaren",
            "En sak till, om du tror en gammal man.\n\nKatterna berättade om en FEMTE - svart som mellanrummet mellan stjärnorna, med ögon av bärnsten.\n\nHon visar sig bara för den som lämnar en silverfisk på en kattbädd när månen står som högst.",
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
    s = Struct(13, 7, 10)
    s.box(0, 0, 0, 12, 0, 9, "minecraft:spruce_planks")                       # golv
    s.box(0, 1, 0, 12, 4, 9, "minecraft:oak_planks", hollow=True)             # väggar
    for cx, cz in ((0, 0), (0, 9), (12, 0), (12, 9)):                          # knutar
        s.box(cx, 1, cz, cx, 4, cz, "minecraft:oak_log", {"pillar_axis": "y"})
    s.box(0, 5, 0, 12, 5, 9, "minecraft:spruce_planks")                       # tak
    for wx in (2, 4, 8, 10):                                                   # fönster
        s.set(wx, 2, 0, "minecraft:glass_pane"); s.set(wx, 3, 0, "minecraft:glass_pane")
        s.set(wx, 2, 9, "minecraft:glass_pane"); s.set(wx, 3, 9, "minecraft:glass_pane")
    for wz in (3, 6):
        s.set(0, 2, wz, "minecraft:glass_pane"); s.set(0, 3, wz, "minecraft:glass_pane")
        s.set(12, 2, wz, "minecraft:glass_pane"); s.set(12, 3, wz, "minecraft:glass_pane")
    for dx in (5, 6):                                                          # dörröppning
        s.set(dx, 1, 0, "minecraft:air"); s.set(dx, 2, 0, "minecraft:air")
    s.set(8, 1, 0, "mjau:kattlucka")                                           # kattdörr i väggen
    for lx, lz in ((3, 4), (9, 4)):                                            # lyktor i taket
        s.set(lx, 4, lz, "minecraft:lantern", {"hanging": True})
    beds = ((2, disp["misty"]), (4, disp["hazel"]), (8, disp["mocha"]), (10, disp["snow"]))
    for bx, name in beds:                                                      # sängar + namnskylt
        s.set(bx, 1, 8, "mjau:kattbadd")
        s.set(bx, 2, 8, "minecraft:wall_sign", {"facing_direction": 2})
        s.entity_at(bx, 2, 8, sign_entity(name))
    s.set(2, 1, 5, "mjau:matskal"); s.set(3, 1, 5, "mjau:matskal")             # matskålar
    s.set(1, 1, 6, "mjau:kattoa")                                              # kattlåda
    s.set(11, 1, 6, "mjau:stallning")                                          # klösställning
    s.set(6, 1, 5, "mjau:garnnystan")                                          # garnnystan
    s.set(11, 1, 1, "mjau:kartong")                                            # kartongen
    s.set(2, 1, 1, "minecraft:chest", {"facing_direction": 5})                 # startkistan
    s.entity_at(2, 1, 1, chest_entity([
        item(0, "minecraft:written_book", 1, book_tag(t)),
        item(1, "minecraft:cod", 16),
        item(2, "mjau:godis", 4),
        item(3, "mjau:sadel_brun", 1),
    ]))
    s.emit(f"{st}/shelter.mcstructure")

    # VÄLKOMSTSKYLT vid spawn (egen liten struktur, vänd mot norr=spelaren)
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:standing_sign", {"ground_sign_direction": 8})
    s.entity_at(0, 0, 0, sign_entity(t["welcome_sign"]))
    s.emit(f"{st}/welcome.mcstructure")

    # DAMMEN: 11×11, 2 djup så katten kan simma — stenbotten, ram, vatten.
    # OBS: box(hollow=True) med höjd 1 gör ALLA block till kant (y träffar
    # alltid y0/y1) — därför läggs vattnet EFTER ramen, aldrig tvärtom.
    s = Struct(11, 4, 11)
    s.box(0, 0, 0, 10, 0, 10, "minecraft:stone_bricks")            # botten
    for y in (1, 2):
        s.box(0, y, 0, 10, y, 10, "minecraft:stone_bricks")        # ram...
        s.box(1, y, 1, 9, y, 9, "minecraft:water", {"liquid_depth": 0})  # ...vatten
    s.set(0, 3, 5, "mjau:fiskdamm")
    s.emit(f"{st}/pond.mcstructure")

    # FYREN: 7×7-bas, 5×5-torn med röda band, stege upp, belönings­kista i topp
    s = Struct(7, 17, 7)
    s.box(0, 0, 0, 6, 1, 6, "minecraft:cobblestone")
    for y in range(2, 13):
        band = "minecraft:red_concrete" if y in (5, 9) else "minecraft:white_concrete"
        s.box(1, y, 1, 5, y, 5, band, hollow=True)
    s.set(3, 2, 5, "minecraft:air"); s.set(3, 3, 5, "minecraft:air")           # ingång (söder)
    s.box(3, 2, 3, 3, 3, 3, "minecraft:air")
    for y in range(2, 14):                                                     # stege mot norrväggen
        s.set(3, y, 2, "minecraft:ladder", {"facing_direction": 3})
    s.box(0, 13, 0, 6, 13, 6, "minecraft:spruce_planks")                       # plattform
    s.set(3, 13, 2, "minecraft:air")                                           # stegluckan
    s.box(0, 14, 0, 6, 14, 6, "minecraft:oak_fence", hollow=True)              # räcke
    s.set(3, 14, 3, "minecraft:glowstone")                                     # ljuset
    s.set(3, 15, 3, "minecraft:lantern", {"hanging": False})
    s.set(1, 14, 3, "minecraft:chest", {"facing_direction": 5})                # belöningen
    s.entity_at(1, 14, 3, chest_entity([
        item(0, "mjau:rustning_netherit", 1),
        item(1, "minecraft:diamond", 3),
        item(2, "minecraft:golden_apple", 1),
        item(3, "minecraft:salmon", 1),      # "en silverfisk" — nyckeln till gåtan
    ]))
    s.emit(f"{st}/lighthouse.mcstructure")

    # EKEN: stam + lövkrona (persistent så den inte vissnar)
    s = Struct(5, 8, 5)
    for y in range(0, 5):
        s.set(2, y, 2, "minecraft:oak_log", {"pillar_axis": "y"})
    s.box(0, 3, 0, 4, 5, 4, "minecraft:oak_leaves", {"persistent_bit": True, "update_bit": False})
    s.box(1, 6, 1, 3, 6, 3, "minecraft:oak_leaves", {"persistent_bit": True, "update_bit": False})
    s.set(2, 7, 2, "minecraft:oak_leaves", {"persistent_bit": True, "update_bit": False})
    s.emit(f"{st}/tree.mcstructure")

# ------------------------------------------------------ serverkommandona ----
def build_commands(cats, disp):
    g, f = GROUND, FLOOR
    c = []
    c.append("gamerule commandblockoutput false")
    c.append("gamerule domobspawning false")
    c.append("gamerule keepinventory true")
    c.append("gamerule sendcommandfeedback true")
    c.append(f"tickingarea add -40 {g-4} -20 40 {g+30} 90 bygge")
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
    c.append(f"structure load haven:welcome 1 {f} 1")
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
    c.append(f"testforblock 12 {g+1} 7 mjau:fiskdamm") # dammen (ramkanten)
    c.append(f"testforblock 17 {g} 7 water")           # vattnet i dammen
    c.append(f"testforblock 0 {g+19} 56 glowstone")    # fyrljuset
    c.append(("sleep", 2))
    # katterna: namngivna (persistenta), vuxna, otama — att hitta dem är uppdraget
    spots = {"misty": (-9, f), "hazel": (16, f), "mocha": (0, f + 1), "snow": (5, f)}
    zs = {"misty": 33, "hazel": 8, "mocha": 13, "snow": 42}
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
    return open(log_path).read()

def postprocess_level_dat(world_dir, world_name):
    version, root = nbt.read_level_dat(f"{world_dir}/level.dat")
    d = root.v
    d["LevelName"] = S(world_name)
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

    log = run_server_build(world_name, build_commands(cats, disp), f"/tmp/cathaven-build-{variant}.log")
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
    postprocess_level_dat(wdir, t["world"])

    ver = ".".join(map(str, bp["version"]))
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
