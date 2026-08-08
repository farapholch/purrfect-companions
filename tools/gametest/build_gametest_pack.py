#!/usr/bin/env python3
"""Genererar GameTest-paketet — det TESTENDA behavior pack som kör simulerade
spelare inne i servern. Skickas ALDRIG till spelare; det installeras bara i
testvärlden av purrfect-gametest.

Simulerade spelare (SimulatedPlayer) är Mojangs egna verktyg för add-on-test:
de håller föremål, interagerar och rider på riktigt, inne i servern — hela
protokollproblemet från bot-försöket (tools/testbot/) existerar inte här.

Kräver beta-API:er (experimentet 'gametest' i level.dat).
Modulversionerna upptäcks av purrfect-gametest: fel version får servern att
lista de giltiga i ContentLog.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/purrfect-gametest-pack"
SERVER_VER = sys.argv[2] if len(sys.argv) > 2 else "2.4.0-beta"
GAMETEST_VER = sys.argv[3] if len(sys.argv) > 3 else "1.0.0-beta"

os.makedirs(f"{OUT}/scripts", exist_ok=True)
os.makedirs(f"{OUT}/structures/mjau", exist_ok=True)

json.dump({
    "format_version": 2,
    "header": {
        "name": "Purrfect GameTest (endast test)",
        "description": "Simulerade spelare - ingår aldrig i leveransen",
        "uuid": "7c1e9f10-31a2-4a3b-9c58-b5c9d2f4a601",
        "version": [1, 0, 0],
        "min_engine_version": [1, 20, 0],
    },
    "modules": [{
        "type": "script", "language": "javascript",
        "uuid": "8d2f0a21-42b3-4b4c-8d69-c6dae3a5b712",
        "version": [1, 0, 0], "entry": "scripts/main.js",
    }],
    "dependencies": [
        {"module_name": "@minecraft/server", "version": SERVER_VER},
        {"module_name": "@minecraft/server-gametest", "version": GAMETEST_VER},
    ],
}, open(f"{OUT}/manifest.json", "w"), indent=2)

open(f"{OUT}/scripts/main.js", "w").write('''\
// Sista milen: en simulerad spelare gar SPELARENS vag genom interaktionerna.
// Event-testerna hoppar over has_equipment/is_owner-filtren; natverksboten
// stoppades av serverns klienthandslag. SimulatedPlayer har inga av de hindren.
import * as gt from "@minecraft/server-gametest";
import { ItemStack, world } from "@minecraft/server";

function done(test, msg, ok) {
  // Egen tydlig loggrad — gametest-ramverkets egna utskrifter varierar mellan
  // versioner, den har raden ar stabil att grep:a efter.
  world.sendMessage(`[MJAU-GT] ${ok ? "PASS" : "FAIL"} ${msg}`);
  console.warn(`[MJAU-GT] ${ok ? "PASS" : "FAIL"} ${msg}`);
  if (ok) test.succeed(); else test.fail(msg);
}

gt.registerAsync("mjau", "interakt", async (test) => {
  const p = test.spawnSimulatedPlayer({ x: 1, y: 2, z: 1 }, "GTKatt");
  const cat = test.spawn("mjau:misty", { x: 3, y: 2, z: 3 });
  await test.idle(20);

  // 1) TAMJA som spelare: torsk i handen, interagera. 0.4 chans/forsok,
  //    tameable satter agare + mjau:tam=1. 30 forsok ~ 99.998 %.
  let tamed = false;
  for (let i = 0; i < 30 && !tamed; i++) {
    p.setItem(new ItemStack("minecraft:cod", 1), 0, true);
    await test.idle(5);
    p.interactWithEntity(cat);
    await test.idle(10);
    tamed = cat.getProperty("mjau:tam") === 1;
  }
  if (!tamed) return done(test, "tamjning: 30 torskar utan resultat", false);
  console.warn("[MJAU-GT] tam efter riktig matning — agare satt");

  // 2) SADLA: filtret kraver is_owner + has_equipment(mjau:sadel_brun).
  p.setItem(new ItemStack("mjau:sadel_brun", 1), 0, true);
  await test.idle(5);
  p.interactWithEntity(cat);
  await test.idle(10);
  if (cat.getProperty("mjau:sadel") !== 1)
    return done(test, "sadeln fastnade inte (has_equipment/is_owner-kedjan)", false);
  console.warn("[MJAU-GT] sadeln PA via riktig interaktion");

  // 3) RIDA: interagera igen (sadlad katt + rideable) och kontrollera att
  //    spelaren faktiskt sitter pa NAGOT.
  await test.idle(10);
  p.interactWithEntity(cat);
  await test.idle(20);
  const riding = p.getComponent("minecraft:riding");
  if (!riding || !riding.entityRidingOn)
    return done(test, "kunde inte sitta upp pa sadlad katt", false);
  console.warn("[MJAU-GT] rider pa " + riding.entityRidingOn.typeId);

  done(test, "tamja+sadla+rida via simulerad spelare", true);
})
  .structureName("mjau:arena")
  .maxTicks(2400);
''')

# Arena: 7x5x7-struktur, stengolv, resten luft. GameTest kräver en struktur
# att placera testet i. NBT skriven för hand — inga bibliotek på maskinen.
V = nbt.Val
SX, SY, SZ = 7, 5, 7
idx = []
for x in range(SX):
    for y in range(SY):
        for z in range(SZ):
            idx.append(V(nbt.TAG_INT, 0 if y == 0 else 1))   # 0=sten, 1=luft
layer2 = [V(nbt.TAG_INT, -1)] * (SX * SY * SZ)
block = lambda name: V(nbt.TAG_COMPOUND, {
    "name": V(nbt.TAG_STRING, name),
    "states": V(nbt.TAG_COMPOUND, {}),
    "version": V(nbt.TAG_INT, 18168865),
})
root = V(nbt.TAG_COMPOUND, {
    "format_version": V(nbt.TAG_INT, 1),
    "size": V(nbt.TAG_LIST, (nbt.TAG_INT, [V(nbt.TAG_INT, SX), V(nbt.TAG_INT, SY), V(nbt.TAG_INT, SZ)])),
    "structure": V(nbt.TAG_COMPOUND, {
        "block_indices": V(nbt.TAG_LIST, (nbt.TAG_LIST, [
            V(nbt.TAG_LIST, (nbt.TAG_INT, idx)),
            V(nbt.TAG_LIST, (nbt.TAG_INT, layer2)),
        ])),
        "entities": V(nbt.TAG_LIST, (nbt.TAG_END, [])),
        "palette": V(nbt.TAG_COMPOUND, {
            "default": V(nbt.TAG_COMPOUND, {
                "block_palette": V(nbt.TAG_LIST, (nbt.TAG_COMPOUND, [
                    block("minecraft:stone"), block("minecraft:air"),
                ])),
                "block_position_data": V(nbt.TAG_COMPOUND, {}),
            }),
        }),
    }),
    "structure_world_origin": V(nbt.TAG_LIST, (nbt.TAG_INT, [V(nbt.TAG_INT, 0)] * 3)),
})
nbt.write_mcstructure(f"{OUT}/structures/mjau/arena.mcstructure", root)
print(f"gametest-paket -> {OUT} (server {SERVER_VER}, gametest {GAMETEST_VER})")
