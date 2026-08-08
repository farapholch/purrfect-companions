#!/usr/bin/env python3
"""Bygger tests/vanilla-recipes.json — facit över vanillas hantverksrecept.

BDS levererar NOLL shaped/shapeless-recept (de ligger inbyggda i motorn), så
den här datan går inte att få lokalt. Mojang publicerar den dock själva i sitt
officiella bedrock-samples-repo; därifrån hämtas alla receptfiler och kokas
ner till kanoniska signaturer (se recipe_canon.py).

Kör om när Minecraft fått nya recept:  python3 tools/snapshot_vanilla_recipes.py
Kräver internet. Själva snapshoten är incheckad, så audit.py behöver det inte.
"""
import json, os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from recipe_canon import canon

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f"{BASE}/tests/vanilla-recipes.json"
RAW = "https://raw.githubusercontent.com/Mojang/bedrock-samples/main/"
TREE = "https://api.github.com/repos/Mojang/bedrock-samples/git/trees/main?recursive=1"

with tempfile.TemporaryDirectory() as tmp:
    tree = json.loads(subprocess.run(["curl", "-sf", TREE], capture_output=True,
                                     check=True).stdout)
    paths = [e["path"] for e in tree["tree"]
             if e["path"].startswith("behavior_pack/recipes/") and e["path"].endswith(".json")]
    print(f"{len(paths)} receptfiler i Mojang/bedrock-samples")
    lst = f"{tmp}/urls.txt"
    open(lst, "w").write("\n".join(RAW + p for p in paths))
    subprocess.run(f"cd {tmp} && xargs -P 12 -n 1 curl -sf -O < urls.txt", shell=True, check=True)

    sigs = {}
    for p in paths:
        f = f"{tmp}/{os.path.basename(p)}"
        if not os.path.exists(f):
            continue
        try:
            d = json.load(open(f))
        except ValueError:
            continue
        body = next((v for k, v in d.items() if k.startswith("minecraft:recipe")), {})
        if not isinstance(body, dict):
            continue
        sig = canon(body)
        if sig:
            # crafting_table-recept är de enda som kan krocka med våra
            tags = body.get("tags", [])
            if tags and "crafting_table" not in tags:
                continue
            sigs.setdefault(sig, os.path.basename(p)[:-5])

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(sigs, open(OUT, "w"), indent=0, sort_keys=True)
print(f"{len(sigs)} kanoniska signaturer -> {OUT} "
      f"({os.path.getsize(OUT)//1024} kB)")
