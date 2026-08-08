#!/usr/bin/env python3
"""Referensintegritet i hela add-onet.

Till skillnad från kontrollerna i purrfect-test, som var för sig kodar EN bugg
som redan träffat en spelare, ställer den här filen generella krav: allt som
refereras måste finnas, och allt som finns måste gå att nå. Sådana regler
fångar buggar vi ännu inte gjort.

Skriver ett fynd per rad på stdout. Tyst = allt hänger ihop.
"""
import json, glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from recipe_canon import canon

BASE = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
BP, RP = f"{BASE}/PurrfectCompanions_BP", f"{BASE}/PurrfectCompanions_RP"
found = []


def J(p):
    return json.load(open(p, encoding="utf-8"))


def ids(pattern, kind):
    return {J(p)[kind]["description"]["identifier"] for p in glob.glob(pattern)}


ITEMS = ids(f"{BP}/items/*.json", "minecraft:item")
BLOCKS = ids(f"{BP}/blocks/*.json", "minecraft:block")
PLACEABLE = ITEMS | BLOCKS

for f in sorted(glob.glob(f"{BP}/entities/*.json")):
    cid = os.path.basename(f)[:-5]
    e = J(f)["minecraft:entity"]
    groups = set(e.get("component_groups", {}))
    events = e.get("events", {})
    blob = json.dumps(e)

    for en, ev in events.items():
        for act in ("add", "remove"):
            for g in ev.get(act, {}).get("component_groups", []):
                if g not in groups:
                    found.append(f"{cid}: event {en} {act}:ar okänd grupp '{g}'")

    for r in set(re.findall(r'"event"\s*:\s*"([^"]+)"', blob)):
        if r.startswith("mjau:") and r not in events:
            found.append(f"{cid}: refererar okänt event '{r}'")

    # En grupp inget event lägger till kan aldrig aktiveras — antingen död kod
    # eller en glömd koppling.
    added = {g for ev in events.values() for g in ev.get("add", {}).get("component_groups", [])}
    for g in groups - added:
        found.append(f"{cid}: grupp '{g}' läggs aldrig till av något event")

    # Egna föremål måste anges med namnrymd, annars matchar filtret aldrig.
    short = {i.split(":", 1)[1] for i in ITEMS}
    for v in re.findall(r'"(?:item|value)"\s*:\s*"([^"]+)"', blob):
        if ":" not in v and v in short:
            found.append(f"{cid}: '{v}' saknar namnrymd — ska vara 'mjau:{v}'")

# Render controllers: varje geometri de kan välja måste finnas, och en
# egenskaps intervall får inte peka utanför arrayen.
ent = J(sorted(glob.glob(f"{RP}/entity/*.json"))[0])["minecraft:client_entity"]["description"]
props = J(sorted(glob.glob(f"{BP}/entities/*.json"))[0])["minecraft:entity"]["description"].get("properties", {})
for name, ctrl in J(f"{RP}/render_controllers/katt.render_controllers.json")["render_controllers"].items():
    blob = json.dumps(ctrl)
    for key, arr in ctrl.get("arrays", {}).get("geometries", {}).items():
        for g in arr:
            short = g.replace("Geometry.", "")
            if short not in ent["geometry"]:
                found.append(f"render controller {name}: {key} pekar på '{g}' "
                             f"som inte finns i client_entity.geometry")
    for arrname, prop in re.findall(r"Array\.(\w+)\[query\.property\('([^']+)'\)\]", blob):
        arr = ctrl.get("arrays", {}).get("geometries", {}).get(f"Array.{arrname}")
        rng = props.get(prop, {}).get("range")
        if arr is not None and rng and rng[1] >= len(arr):
            found.append(f"render controller {name}: Array.{arrname} har {len(arr)} poster "
                         f"men '{prop}' kan bli {rng[1]} — index utanför arrayen")

# En animation som riktar sig mot ett ben som inte finns gör tyst ingenting.
geo = {g["description"]["identifier"]: {b["name"] for b in g.get("bones", [])}
       for g in J(f"{RP}/models/entity/katt.geo.json")["minecraft:geometry"]}
for an, av in J(f"{RP}/animations/katt.animation.json")["animations"].items():
    for bone in av.get("bones", {}):
        if bone not in geo["geometry.katt"]:
            found.append(f"animation {an}: rör benet '{bone}' som inte finns i geometry.katt")

# Recept jämförs KANONISKT (rutnät av föremåls-id, trimmat + speglat — se
# recipe_canon.py): två recept som ser olika ut i JSON men är samma i
# hantverksrutan krockar ändå. Kronan blev en gång en guldhjälm och
# garnnystanet blev ull; alla tre vingfärger hade identiskt recept.
# Vanilla-facit kommer från Mojangs officiella bedrock-samples
# (tools/snapshot_vanilla_recipes.py) — BDS levererar inga hantverksrecept.
VAN = J(f"{BASE}/tests/vanilla-recipes.json") if os.path.exists(f"{BASE}/tests/vanilla-recipes.json") else {}
if not VAN:
    found.append("tests/vanilla-recipes.json saknas — vanilla-krockar kontrolleras INTE "
                 "(kör tools/snapshot_vanilla_recipes.py)")
sigs = {}
for rf in sorted(glob.glob(f"{BP}/recipes/*.json")):
    body = next((v for k, v in J(rf).items() if k.startswith("minecraft:recipe")), {})
    sig = canon(body)
    if not sig:
        continue
    if sig in VAN:
        found.append(f"recept {os.path.basename(rf)}: krockar med vanillas '{VAN[sig]}' "
                     f"— spelaren får vanilla-föremålet, inte vårt")
    sigs.setdefault(sig, []).append(os.path.basename(rf))
for sig, files in sigs.items():
    if len(files) > 1:
        found.append(f"recept med identiskt mönster och ingredienser: {', '.join(files)} "
                     f"— bara ett av dem går att tillverka")

# Uppladdat hopp utan laddning, eller tvärtom, gör att den ena halvan inte märks.
for f in sorted(glob.glob(f"{BP}/entities/*.json")):
    cid = os.path.basename(f)[:-5]
    for gname, grp in J(f)["minecraft:entity"].get("component_groups", {}).items():
        if "minecraft:can_power_jump" in grp and "minecraft:horse.jump_strength" not in grp:
            found.append(f"{cid}: {gname} har can_power_jump men ingen jump_strength "
                         f"— laddat hopp utan höjd")

# Recept måste ge något som faktiskt går att få — föremål ELLER block.
for rf in glob.glob(f"{BP}/recipes/*.json"):
    body = next((v for k, v in J(rf).items() if k.startswith("minecraft:recipe")), {})
    res = body.get("result", {})
    item = res.get("item") if isinstance(res, dict) else (res[0].get("item") if res else None)
    if item and item.startswith("mjau:") and item not in PLACEABLE:
        found.append(f"recept {os.path.basename(rf)}: resultat '{item}' finns varken "
                     f"som föremål eller block")

print("\n".join(found))
