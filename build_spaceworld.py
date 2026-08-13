#!/usr/bin/env python3
"""Bygger STJÄRNHAMNEN — den andra världen, i rymdtema.

Samma recept som Cat Haven (build_world.py): servern bygger världen via
stdin-kommandon, block-entiteter (bok, skyltar, kistor) läggs som
.mcstructure, och resultatet packas som .mcworld + .mctemplate med paketen
inbäddade. Allt tungt maskineri IMPORTERAS från build_world.py i stället för
att kopieras — en bugfix där ska gälla båda världarna.

Temat är EGET, inte lånat från någon film: projektet ligger publikt på
CurseForge och ska inte luta sig mot någon annans varumärke.

    python3 build_spaceworld.py public /tmp/ut
    python3 build_spaceworld.py private /tmp/ut
"""
import json, os, shutil, subprocess, sys, uuid, zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import build_world as bw
sys.path.insert(0, f"{BASE}/tools/gametest")
import nbt

# återanvänt maskineri
Struct, item, chest_entity, sign_entity = bw.Struct, bw.item, bw.chest_entity, bw.sign_entity
S, C, I, L, V = bw.S, bw.C, bw.I, bw.L, bw.V
G, F, SRV = bw.GROUND, bw.FLOOR, bw.SRV

# Stationen ligger på FLAT-markens nivå. Golvet är byggt, inte gräs — därför
# refereras allt mot F (fötterna) och inte mot G som i Cat Haven.
TEXTS = {
    "public": {
        "world": "Star Harbour",
        "book_title": "The Harbourmaster's Log",
        "book_author": "The Harbourmaster",
        "welcome_sign": "STAR HARBOUR\nCat station\nneeds a new\nharbourmaster",
        "dome_sign": "THE DOME\nRead the log\nin the chest\ninside ->",
        "hangar_sign": "HANGAR\nThe shuttle\nnever flew\nagain",
        "deck_sign": "OBSERVATION\nThe stars are\nclosest here.\nLook up.",
        "book_pages": [
            "Welcome to Star Harbour!\n\nThe station has been dark a long time. Its cats are still aboard - they know the corridors better than I ever did.\n\nEverything you need is in this chest.",
            "TASK 1 - WAKE THE STATION\n\nFour cats sleep aboard: one in the dome, one in the corridor, one in the hangar, one on the observation deck.\n\nTame them with the cod from this chest.",
            "TASK 2 - THE BLADES\n\nThe harbour kept four energy blades, one of each colour, locked in different bays.\n\nThey cut, and they light your way. Find them all.",
            "TASK 3 - THE HANGAR\n\nThe shuttle in the hangar never flew again. Something worth keeping is still strapped in the hold.\n\nThe two spear-fighters beside it are older still. Nobody remembers who flew them.",
            "TASK 4 - THE OBSERVATION DECK\n\nClimb to the top of the station and look out at the dark.\n\nStanding there is its own reward - but not the only one.",
            "The beds carry the cats' names. Cat treats cheer them up when their tails droop - sugar, wheat and cod.\n\nMind the bays. The harbour kept more than blades.\n\n- The Harbourmaster",
            "One more thing, before the lights went out.\n\nThe cats spoke of one who was not born here - fur like the space between stars, and light caught in it.\n\nShe answers only to someone who carries all four colours at once.",
        ],
    },
    "private": {
        "world": "Stjärnhamnen",
        "book_title": "Hamnmästarens loggbok",
        "book_author": "Hamnmästaren",
        "welcome_sign": "STJÄRNHAMNEN\nStationen\nbehöver en ny\nhamnmästare",
        "dome_sign": "KUPOLEN\nLäs loggboken\ni kistan\ndärinne ->",
        "hangar_sign": "HANGAREN\nSkytteln\nflög aldrig\nmer",
        "deck_sign": "UTKIKEN\nStjärnorna är\nnärmast här.\nTitta upp.",
        "book_pages": [
            "Välkommen till Stjärnhamnen!\n\nStationen har varit mörk länge. Katterna är kvar ombord - de kan korridorerna bättre än jag någonsin gjorde.\n\nAllt du behöver ligger i den här kistan.",
            "UPPDRAG 1 - VÄCK STATIONEN\n\nFyra katter sover ombord: en i kupolen, en i korridoren, en i hangaren, en på utkiken.\n\nTämj dem med torsken ur kistan.",
            "UPPDRAG 2 - BLADEN\n\nHamnen förvarade fyra energisvärd, ett i varje färg, inlåsta i olika fack.\n\nDe skär, och de lyser upp vägen. Hitta alla.",
            "UPPDRAG 3 - HANGAREN\n\nSkytteln i hangaren flög aldrig mer. Något värt att behålla sitter fastspänt i lastrummet.\n\nDe två spjutjaktarna bredvid är ännu äldre. Ingen minns vem som flög dem.",
            "UPPDRAG 4 - UTKIKEN\n\nKlättra högst upp i stationen och se ut i mörkret.\n\nAtt stå där är belöning nog - men inte den enda.",
            "Bäddarna bär katternas namn. Kattgodis piggar upp dem när svansen hänger - socker, vete och torsk.\n\nSe upp med facken. Hamnen förvarade mer än blad.\n\n- Hamnmästaren",
            "En sak till, innan ljuset slocknade.\n\nKatterna talade om en som inte föddes här - päls som mellanrummet mellan stjärnorna, och ljus fångat i den.\n\nHon svarar bara den som bär alla fyra färgerna samtidigt.",
        ],
    },
}


def build_structures(outdir, t, disp, cats):
    st = f"{outdir}/structures/hamn"
    os.makedirs(st, exist_ok=True)

    # LOGGBOKEN + startkistan
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:chest", {"facing_direction": 3})
    s.entity_at(0, 0, 0, chest_entity([
        item(0, "minecraft:cod", 8),
        item(1, "mjau:godis", 4),
        item(2, "mjau:sadel_brun", 1),
        item(3, "minecraft:written_book", 1, {
            "title": S(t["book_title"]), "author": S(t["book_author"]),
            "generation": I(0),
            "pages": L(nbt.TAG_COMPOUND, [C({"photoname": S(""), "text": S(p)})
                                          for p in t["book_pages"]])}),
    ]))
    s.emit(f"{st}/startchest.mcstructure")

    for namn, txt, riktning in (("welcome", t["welcome_sign"], 8),
                                ("dome", t["dome_sign"], 8),
                                ("hangar", t["hangar_sign"], 4),
                                ("deck", t["deck_sign"], 12)):
        s = Struct(1, 1, 1)
        s.set(0, 0, 0, "minecraft:standing_sign", {"ground_sign_direction": riktning})
        s.entity_at(0, 0, 0, sign_entity(txt))
        s.emit(f"{st}/{namn}sign.mcstructure")

    # DE FYRA BLADFACKEN — ett svärd per kista, en färg var
    for farg in ("bla", "gron", "rod", "lila"):
        s = Struct(1, 1, 1)
        s.set(0, 0, 0, "minecraft:chest", {"facing_direction": 3})
        s.entity_at(0, 0, 0, chest_entity([item(0, f"mjau:energisvard_{farg}", 1)]))
        s.emit(f"{st}/blade_{farg}.mcstructure")

    # SKYTTELNS LASTRUM: rymdmanteln + proviant
    s = Struct(1, 1, 1)
    s.set(0, 0, 0, "minecraft:chest", {"facing_direction": 3})
    s.entity_at(0, 0, 0, chest_entity([
        item(0, "mjau:rymdmantel_stjarna", 1),
        item(1, "minecraft:diamond", 3),
        item(2, "minecraft:golden_apple", 1),
    ]))
    s.emit(f"{st}/shuttlechest.mcstructure")

    # KATTBÄDDARNA med namn (block entities kräver struktur)
    for src in ("misty", "hazel", "mocha", "snow"):
        s = Struct(1, 1, 1)
        s.set(0, 0, 0, "minecraft:wall_sign", {"facing_direction": 2})
        s.entity_at(0, 0, 0, sign_entity(disp[src]))
        s.emit(f"{st}/namn_{src}.mcstructure")


def build_commands(cats, disp):
    c = []
    c.append("gamerule commandblockoutput false")
    c.append("gamerule domobspawning false")
    c.append("gamerule keepinventory true")
    c.append("gamerule sendcommandfeedback true")
    c.append(f"tickingarea add -40 {G-4} -40 60 {G+40} 60 bygge")
    c.append(("sleep", 4))
    c.append(f"testforblock 0 {G} 0 grass_block")     # marknivån

    # ---------------------------------------------------------------- KUPOLEN
    # Stationens hjärta: rund glaskupol över ett quartzgolv. Kupolen byggs som
    # terrasserade ringar (samma teknik som berget i Cat Haven) — Bedrock har
    # inget "fill sphere", och handlagda ringar ger full kontroll på höjden.
    c.append(f"fill -12 {G} -12 12 {G} 12 quartz_block")           # golvplattan
    for i, r in enumerate((12, 11, 9, 6)):
        y = F + 5 + i
        c.append(f"fill {-r} {y} {-r} {r} {y} {r} glass hollow")
    c.append(f"fill -6 {F+9} -6 6 {F+9} 6 glass")                  # kupoltak
    c.append(("sleep", 2))
    # golvmönster: ljusa gångar i mörkare däck
    for dz in range(-10, 11, 5):
        c.append(f"fill -10 {G} {dz} 10 {G} {dz} light_gray_concrete")
    c.append(f"setblock 0 {G} 0 sea_lantern")                      # navet lyser
    c.append(("sleep", 2))
    c.append(f"testforblock 0 {F+9} 0 glass")                      # kupolen står

    # startkistan + skyltar
    c.append(f"structure load hamn:startchest -3 {F} 3")
    c.append(f"structure load hamn:welcomesign 0 {F} 6")
    c.append(f"structure load hamn:domesign -3 {F} 5")
    c.append(("sleep", 1))
    c.append(f"testforblock -3 {F} 3 chest")

    # kattbäddar + möbler i kupolen
    for i, (src, bx) in enumerate((("misty", -8), ("hazel", -4), ("mocha", 4), ("snow", 8))):
        c.append(f"setblock {bx} {F} -8 mjau:kattbadd")
        c.append(f"structure load hamn:namn_{src} {bx} {F+1} -9")
    c.append(f"setblock -6 {F} -5 mjau:matskal")
    c.append(f"setblock 6 {F} -5 mjau:kattoa")
    c.append(f"setblock 0 {F} -6 mjau:stallning")
    c.append(f"setblock 3 {F} 8 mjau:garnnystan")
    c.append(("sleep", 2))
    c.append(f"testforblock -8 {F} -8 mjau:kattbadd")

    # -------------------------------------------------------------- KORRIDOR
    # Sluten gång österut till hangaren — järnväggar, ljusribbor i taket.
    c.append(f"fill 12 {G} -3 34 {G} 3 light_gray_concrete")
    c.append(f"fill 12 {F} -3 34 {F+4} 3 iron_block hollow")
    c.append(f"fill 13 {F} -2 33 {F+3} 2 air")     # skalets botten bort
    c.append(("sleep", 2))
    for lx in range(15, 34, 6):
        c.append(f"setblock {lx} {F+3} 0 sea_lantern")
    for wx in range(16, 33, 8):                                    # fönsterrutor
        c.append(f"fill {wx} {F+1} -3 {wx+1} {F+2} -3 glass")
        c.append(f"fill {wx} {F+1} 3 {wx+1} {F+2} 3 glass")
    c.append(("sleep", 1))
    c.append(f"testforblock 21 {F+3} 0 sea_lantern")

    # bladfack 1 och 2 längs korridoren
    c.append(f"structure load hamn:blade_bla 14 {F} -2")
    c.append(f"structure load hamn:blade_gron 32 {F} 2")
    c.append(("sleep", 1))

    # --------------------------------------------------------------- HANGAREN
    c.append(f"fill 34 {G} -14 56 {G} 14 light_gray_concrete")
    c.append(f"fill 34 {F} -14 56 {F+9} 14 iron_block hollow")
    c.append(f"fill 35 {F} -13 55 {F+8} 13 air")
    c.append(("sleep", 2))
    c.append(f"fill 40 {F+8} -8 52 {F+8} 8 glass")                 # hangartak i glas
    for lz in (-10, 0, 10):
        c.append(f"setblock 45 {F+8} {lz} sea_lantern")
    c.append(("sleep", 2))
    # SKYTTELN: skrov av quartz, motorer, öppen ramp
    c.append(f"fill 42 {F} -4 52 {F+3} 4 quartz_block")
    c.append(f"fill 43 {F+1} -3 51 {F+2} 3 air")
    c.append(f"fill 40 {F+1} -2 42 {F+2} 2 quartz_stairs")         # nos
    c.append(f"fill 52 {F+1} -3 53 {F+2} -2 blackstone")           # motorer
    c.append(f"fill 52 {F+1} 2 53 {F+2} 3 blackstone")
    c.append(f"fill 44 {F+3} -3 50 {F+3} 3 glass")                 # cockpitfönster
    c.append(("sleep", 2))

    # SPJUTJAKTARNA: två små jaktplan parkerade på var sin sida om skytteln.
    # Klassisk sci-fi-siluett — klotformad kabin mellan två höga, platta
    # vingpaneler — men EGEN design och eget namn, av samma skäl som resten av
    # temat: världen ligger publikt och ska inte låna någon annans varumärke.
    for cz in (-9, 9):
        cx = 39
        # kabinen: liten kub med avfasade hörn + fönsterband
        c.append(f"fill {cx-1} {F+2} {cz-1} {cx+1} {F+4} {cz+1} blackstone")
        c.append(f"fill {cx-1} {F+3} {cz-1} {cx-1} {F+3} {cz+1} gray_stained_glass")
        # vingpanelerna: 5 breda, 7 höga, en ruta tjocka — hörnen borttagna
        # så rektangeln läser som en sexkant
        for dz in (-3, 3):
            pz = cz + dz
            c.append(f"fill {cx-2} {F} {pz} {cx+2} {F+6} {pz} blackstone")
            for corner_y, corner_x in ((F, cx-2), (F, cx+2), (F+6, cx-2), (F+6, cx+2)):
                c.append(f"setblock {corner_x} {corner_y} {pz} air")
        # bommarna som håller vingarna
        for dz in (-2, 2):
            c.append(f"setblock {cx} {F+3} {cz+dz} polished_blackstone")
    c.append(("sleep", 2))
    c.append(f"testforblock 39 {F+3} -12 blackstone")   # vingpanel, jaktplan 1
    c.append(f"testforblock 39 {F+3} 12 blackstone")    # vingpanel, jaktplan 2
    c.append(f"testforblock 38 {F+3} -9 gray_stained_glass")   # kabinfönster
    c.append(("sleep", 1))

    c.append(f"structure load hamn:shuttlechest 47 {F+1} 0")
    c.append(f"structure load hamn:hangarsign 38 {F} 6")
    c.append(f"structure load hamn:blade_rod 36 {F} -12")
    c.append(("sleep", 1))
    c.append(f"testforblock 47 {F+1} 0 chest")
    c.append(f"testforblock 45 {F+3} 0 glass")

    # -------------------------------------------------------------- UTKIKEN
    # Torn upp från kupolen med servicestege i schaktet.
    # BUGFIX: första försöket la "trappsteg" på SAMMA z-spann varje nivå —
    # en solid stapel, inte en trappa. Schaktet saknade dessutom stege och
    # däcksgolvet förseglade toppen, så utkiken gick inte att nå alls trots
    # att loggboken ber en klättra dit. Bygget verifierade bara att blocken
    # FANNS, aldrig att man kom fram — samma klass av fel som Cat Havens
    # genomspelningstest finns till för att fånga.
    c.append(f"fill -2 {F} 14 2 {F+14} 18 iron_block")
    c.append(f"fill -1 {F} 15 1 {F+14} 17 air")
    c.append(f'fill 0 {F} 17 0 {F+15} 17 ladder ["facing_direction"=2]')
    c.append(("sleep", 3))
    c.append(f"fill -6 {F+15} 12 6 {F+15} 20 quartz_block")        # däcket
    c.append(f"setblock 0 {F+15} 17 air")                          # lucka upp ur schaktet
    c.append(f"fill -6 {F+16} 12 6 {F+18} 20 glass hollow")
    c.append(f"fill -5 {F+16} 13 5 {F+18} 19 air")
    c.append(f"setblock 0 {F+18} 16 sea_lantern")
    c.append(("sleep", 2))
    c.append(f"structure load hamn:decksign -4 {F+16} 13")
    c.append(f"structure load hamn:blade_lila 4 {F+16} 19")
    c.append(("sleep", 1))
    c.append(f"testforblock 0 {F+15} 16 quartz_block")
    c.append(f"testforblock 0 {F+8} 17 ladder")                    # stegen i schaktet
    c.append(f"testforblock 0 {F+15} 17 air")                      # luckan är öppen
    c.append(f"testforblock 4 {F+16} 19 chest")

    # ---------------------------------------------------------------- KATTERNA
    spots = {"misty": (-6, 6), "hazel": (24, 0), "mocha": (46, 8), "snow": (0, 16)}
    ytor = {"misty": F, "hazel": F, "mocha": F, "snow": F + 16}
    for src, (x, z) in spots.items():
        c.append(f'summon mjau:{cats[src]} "{disp[src]}" {x} {ytor[src]} {z}')
        c.append(("sleep", 1))
        c.append(f"event entity @e[type=mjau:{cats[src]}] mjau:grow_up")
    c.append(("sleep", 1))
    for src, (x, z) in spots.items():
        c.append(f"testfor @e[type=mjau:{cats[src]},x={x},y={ytor[src]},z={z},r=60]")
        c.append(("sleep", 1))

    c.append(f"setworldspawn 0 {F} 4")
    c.append(("sleep", 1))
    c.append("tickingarea remove bygge")
    c.append(("sleep", 2))
    return c


def postprocess_level_dat(world_dir, world_name):
    version, root = nbt.read_level_dat(f"{world_dir}/level.dat")
    d = root.v
    d["LevelName"] = S(world_name)
    d["Time"] = V(nbt.TAG_LONG, 18000)        # djup natt: stjärnorna syns
    d["rainLevel"] = V(nbt.TAG_FLOAT, 0.0)    # ingen väderlek i rymden
    d["rainTime"] = I(999999)
    d["Difficulty"] = I(1)
    d["commandsEnabled"] = bw.B(0)
    d["GameType"] = I(0)
    nbt.write_level_dat(f"{world_dir}/level.dat", version, root)
    open(f"{world_dir}/levelname.txt", "w").write(world_name)


def build(variant, outdir):
    t = TEXTS[variant]
    cfgs = json.load(open(f"{BASE}/variants.json"))
    pf = f"{BASE}/variants.private.json"
    if os.path.exists(pf):
        cfgs.update(json.load(open(pf, encoding="utf-8")))
    names = cfgs[variant].get("names") or {}
    cats = {s_: names.get(s_, (s_, s_.capitalize()))[0] for s_ in ("misty", "hazel", "mocha", "snow")}
    disp = {s_: names.get(s_, (s_, s_.capitalize()))[1] for s_ in ("misty", "hazel", "mocha", "snow")}

    packdir = f"/tmp/hamn-packs-{variant}"
    subprocess.run([sys.executable, f"{BASE}/make_variant.py", variant, packdir],
                   check=True, capture_output=True)
    builddir = f"/tmp/hamn-buildbp-{variant}"
    if os.path.exists(builddir): shutil.rmtree(builddir)
    shutil.copytree(f"{packdir}/PurrfectCompanions_BP", builddir)
    build_structures(builddir, t, disp, cats)

    world_name = "StarHarbourBuild"
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

    log = bw.run_server_build(world_name, build_commands(cats, disp), f"/tmp/hamn-build-{variant}.log")
    problems = []
    hittade = log.count("found the block")
    katter = log.count("Found ")
    fel = [l.strip() for l in log.splitlines()
           if "Syntax error" in l or "Unknown block" in l or "ERROR" in l][:8]
    if hittade < 14: problems.append(f"bara {hittade}/14 kontrollblock hittades")
    if katter < 4: problems.append(f"bara {katter}/4 katter verifierade")
    for e in fel: problems.append(f"serverfel: {e}")

    shutil.rmtree(f"{wdir}/behavior_packs/PurrfectCompanions_BP")
    shutil.copytree(f"{packdir}/PurrfectCompanions_BP", f"{wdir}/behavior_packs/PurrfectCompanions_BP")
    ver = ".".join(map(str, bp["version"]))
    postprocess_level_dat(wdir, f'{t["world"]} {ver}')
    os.makedirs(outdir, exist_ok=True)
    suffix = "-familj" if variant == "private" else ""
    slug = "stjarnhamnen" if variant == "private" else "star-harbour"
    # EGEN ikon — Stjärnhamnen ärvde Cat Havens och båda världarna såg
    # likadana ut i världslistan
    icon = "/tmp/starharbour-world-icon.jpeg"
    if not os.path.exists(icon):
        subprocess.run([sys.executable, f"{BASE}/tools/promo/make_harbour_art.py"],
                       check=True, capture_output=True)

    for kind in ("mcworld", "mctemplate"):
        out = f"{outdir}/purrfect-{slug}-v{ver}{suffix}.{kind}"
        if os.path.exists(out): os.remove(out)
        zf = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)
        for dirpath, _, files in os.walk(wdir):
            for fn in files:
                p = os.path.join(dirpath, fn)
                zf.write(p, os.path.relpath(p, wdir))
        zf.write(icon, "world_icon.jpeg")
        if kind == "mctemplate":
            zf.writestr("manifest.json", json.dumps({
                "format_version": 2,
                "header": {"name": t["world"], "description": f'{t["world"]} v{ver}',
                           "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, f"mjau:hamn:{variant}:header")),
                           "version": bp["version"], "base_game_version": [1, 26, 40],
                           "lock_template_options": False},
                "modules": [{"type": "world_template",
                             "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, f"mjau:hamn:{variant}:module")),
                             "version": bp["version"]}],
            }, indent=2))
        zf.close()
        print(f"{'värld' if kind == 'mcworld' else 'mall'}: {out} ({os.path.getsize(out)//1024} KB)")
    for p in problems: print(f"PROBLEM: {p}")
    return problems


if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "public"
    outdir = sys.argv[2] if len(sys.argv) > 2 else "/tmp"
    sys.exit(1 if build(variant, outdir) else 0)
