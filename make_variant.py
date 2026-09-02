#!/usr/bin/env python3
"""Bygger en variant av Mjau Mods som en transformerad KOPIA av källan.

Källan (/opt/purrfect-companions) är alltid den PUBLIKA/generiska versionen — Misty, Hazel,
Mocha, Snow. Den privata varianten (familjens riktiga kattnamn) genereras vid
paketering så att källan aldrig innehåller privata namn.

VIKTIGT: varianterna har olika pack-UUID:n. Två paket med samma UUID krockar i
Minecraft — den ena skriver över den andra i paketlistan.

    python3 make_variant.py private /tmp/bygge     # → /tmp/bygge/{BP,RP}
    python3 make_variant.py public  /tmp/bygge
"""
import json, os, re, shutil, sys, glob

BASE = "/opt/purrfect-companions"

def build(variant, outdir):
    # Publika varianten ligger i variants.json (versionshanterad).
    # Den privata (familjens riktiga kattnamn) ligger i variants.private.json som
    # är gitignore:ad — privata namn ska aldrig hamna i repot.
    cfgs = json.load(open(f"{BASE}/variants.json"))
    pf = f"{BASE}/variants.private.json"
    if os.path.exists(pf): cfgs.update(json.load(open(pf, encoding="utf-8")))
    if variant not in cfgs:
        raise SystemExit(f"varianten '{variant}' saknas (privat konfig i variants.private.json?)")
    cfg = cfgs[variant]
    if os.path.exists(outdir): shutil.rmtree(outdir)
    os.makedirs(outdir)
    for pack in ("PurrfectCompanions_BP", "PurrfectCompanions_RP"):
        shutil.copytree(f"{BASE}/{pack}", f"{outdir}/{pack}")

    names = cfg.get("names") or {}
    # 1) byt namn i filinnehåll
    if names:
        targets = glob.glob(f"{outdir}/**/*.json", recursive=True) + \
                  glob.glob(f"{outdir}/**/*.lang", recursive=True)
        for f in targets:
            s = open(f, encoding="utf-8").read(); o = s
            for src, (slug, disp) in names.items():
                # OBS: ta pc_-prefixade texturnamn FÖRST. \b matchar inte inuti
                # "pc_misty" (understreck är ett ordtecken), så utan den här raden
                # döps filerna om medan item_texture.json pekar kvar på gamla
                # namnet → spawn-äggen blir rutiga "saknad textur" i spelet.
                s = s.replace(f"pc_{src}", f"pc_{slug}")
                s = s.replace(f"{src}_pals", f"{slug}_pals")     # pälsarket, samma fälla
                s = re.sub(rf"\b{src}\b", slug, s)
                s = re.sub(rf"\b{src.capitalize()}\b", disp, s)
            if s != o: open(f, "w", encoding="utf-8").write(s)
        # 2) döp om filer
        for src, (slug, disp) in names.items():
            for p in (f"{outdir}/PurrfectCompanions_BP/entities/{src}.json",
                      f"{outdir}/PurrfectCompanions_BP/spawn_rules/{src}.json",
                      f"{outdir}/PurrfectCompanions_RP/entity/{src}.json",
                      f"{outdir}/PurrfectCompanions_RP/textures/entity/{src}.png",
                      f"{outdir}/PurrfectCompanions_RP/textures/entity/{src}_pals.png",
                      f"{outdir}/PurrfectCompanions_RP/textures/items/pc_{src}.png"):
                if os.path.exists(p):
                    d = os.path.dirname(p); b = os.path.basename(p).replace(src, slug)
                    shutil.move(p, f"{d}/{b}")
        # 3) visningsnamn med rasbeteckning
        breeds = cfg.get("breeds", {})
        for pack in ("PurrfectCompanions_BP", "PurrfectCompanions_RP"):
            lp = f"{outdir}/{pack}/texts/en_US.lang"
            # stryk bara raderna för de OMDÖPTA katterna — hemliga katter
            # (t.ex. midnight) behåller sina rader orörda
            slugs = "|".join(s for s, _ in names.values())
            lines = [l for l in open(lp, encoding="utf-8").read().rstrip("\n").split("\n")
                     if not re.match(rf"^(entity|item\.spawn_egg\.entity)\.(mjau:)?({slugs})\.name=", l)]
            for src, (slug, disp) in names.items():
                lines.insert(0, f"item.spawn_egg.entity.mjau:{slug}.name=Spawna {disp}")
                lines.insert(0, f"entity.mjau:{slug}.name={disp} ({breeds.get(slug,'')})".replace(" ()", ""))
                # UI-titlar (t.ex. lastutrymmet) kan slå upp namnet utan namespace
                lines.insert(0, f"entity.{slug}.name={disp} ({breeds.get(slug,'')})".replace(" ()", ""))
            open(lp, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # 3b) föremålsnamn på svenska i privata varianten (källan är engelsk)
    item_names = cfg.get("item_names") or {}
    if item_names:
        for f in glob.glob(f"{outdir}/PurrfectCompanions_BP/items/*.json"):
            d = json.load(open(f, encoding="utf-8"))
            ident = d["minecraft:item"]["description"]["identifier"]
            if ident in item_names:
                d["minecraft:item"]["components"]["minecraft:display_name"]["value"] = item_names[ident]
                json.dump(d, open(f, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        for pack in ("PurrfectCompanions_BP", "PurrfectCompanions_RP"):
            lp = f"{outdir}/{pack}/texts/en_US.lang"
            lines = [l for l in open(lp, encoding="utf-8").read().rstrip("\n").split("\n")
                     if not l.startswith("item.mjau:")]
            lines += [f"item.{k}={v}" for k, v in item_names.items()]
            open(lp, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # 4) paketnamn, beskrivning, skapare och (för privat) egna UUID:n
    bp = json.load(open(f"{outdir}/PurrfectCompanions_BP/manifest.json"))
    rp = json.load(open(f"{outdir}/PurrfectCompanions_RP/manifest.json"))
    bp["header"]["name"] = cfg["pack_bp"]; bp["header"]["description"] = cfg["desc_bp"]
    rp["header"]["name"] = cfg["pack_rp"]
    for m in (bp, rp): m["metadata"] = {"authors": ["Pellzor"]}
    u = cfg.get("uuids")
    if u:
        bp["header"]["uuid"] = u["bp_header"]; bp["modules"][0]["uuid"] = u["bp_module"]
        rp["header"]["uuid"] = u["rp_header"]; rp["modules"][0]["uuid"] = u["rp_module"]
        for mod in bp["modules"]:
            if mod.get("type") == "script" and "bp_script" in u:
                mod["uuid"] = u["bp_script"]
        for dep in bp.get("dependencies", []):
            if "uuid" in dep: dep["uuid"] = u["rp_header"]
    json.dump(bp, open(f"{outdir}/PurrfectCompanions_BP/manifest.json", "w"), indent=2)
    json.dump(rp, open(f"{outdir}/PurrfectCompanions_RP/manifest.json", "w"), indent=2)

    ver = ".".join(map(str, bp["header"]["version"]))
    return ver, bp["header"]["uuid"], rp["header"]["uuid"]

if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "public"
    outdir = sys.argv[2] if len(sys.argv) > 2 else f"/tmp/purrfect-{variant}"
    ver, bpu, rpu = build(variant, outdir)
    print(f"{variant}: v{ver} → {outdir}")
    print(f"  BP uuid {bpu}")
    print(f"  RP uuid {rpu}")
