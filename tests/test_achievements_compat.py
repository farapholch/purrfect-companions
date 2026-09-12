#!/usr/bin/env python3
"""Statisk spärr mot sådant som kan göra en Bedrock-värld experimentell.

Detta ersätter inte ett verkligt Xbox-achievement-test, men verifierar att
releasekällan inte kräver Beta APIs, GameTest eller experimentella entiteter.
"""
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
BP = ROOT / "PurrfectCompanions_BP"
RP = ROOT / "PurrfectCompanions_RP"

def fail(msg):
    raise SystemExit(f"ACHIEVEMENTS FAIL: {msg}")

bp = json.loads((BP / "manifest.json").read_text())
rp = json.loads((RP / "manifest.json").read_text())
for pack, name in ((bp, "BP"), (rp, "RP")):
    if pack.get("header", {}).get("min_engine_version", [0]) < [1, 20, 0]:
        fail(f"{name} har ogiltig min_engine_version")
    for dep in pack.get("dependencies", []):
        module = dep.get("module_name", "")
        if module.startswith("@minecraft/") and "beta" in str(dep.get("version", "")).lower():
            fail(f"{name} kräver Beta API {module} {dep['version']}")
    if pack.get("capabilities"):
        fail(f"{name} deklarerar capabilities: {pack['capabilities']}")

for path in (BP / "entities").glob("*.json"):
    data = json.loads(path.read_text())
    desc = data.get("minecraft:entity", {}).get("description", {})
    if desc.get("is_experimental") is True:
        fail(f"{path.name} är markerad is_experimental=true")

print("ACHIEVEMENTS OK: inga Beta APIs, experimentella entiteter eller GameTest-referenser i releasekällan")

# Om ett paket anges granskas även arkivet, inklusive att testpaketet saknas.
if len(sys.argv) > 2:
    package = Path(sys.argv[2])
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        if any("PurrfectGameTest" in n or "gametest" in n.lower() for n in names):
            fail("mcaddon innehåller GameTest-filer")
    print(f"ACHIEVEMENTS OK: {package.name} innehåller inget testpaket")
