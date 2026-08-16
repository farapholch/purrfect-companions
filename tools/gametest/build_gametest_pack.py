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
  const p = test.spawnSimulatedPlayer({ x: 20, y: 2, z: 18 }, "GTKatt");
  const cat = test.spawn("mjau:misty", { x: 20, y: 2, z: 21 });
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

  // 3a) SATESLAGE: mat var ryttaren FAKTISKT sitter i kattens eget koordinat-
  //     system. Sadelns z-tecken har gissats fel forr — matningen ar facit.
  //     forward > 0 = mot huvudet, forward < 0 = mot svansen.
  {
    const dx = p.location.x - cat.location.x;
    const dz = p.location.z - cat.location.z;
    const yaw = cat.getRotation().y * Math.PI / 180;
    const fx = -Math.sin(yaw), fz = Math.cos(yaw);
    const forward = dx * fx + dz * fz;
    const up = p.location.y - cat.location.y;
    console.warn(`[MJAU-GT] sate: forward=${forward.toFixed(2)} up=${up.toFixed(2)} (forward>0 = mot huvudet)`);
    if (forward > -0.05)
      return done(test, `ryttaren sitter pa/framfor kattens mitt (forward=${forward.toFixed(2)}, ska vara bakre halvan)`, false);
  }

  // 3b) NEGATIV KONTROLL: sitt still utan inmatning — katten far INTE vandra.
  //     Precis den har saknades nar "katten styr sig sjalv" slank till Xbox:
  //     vi matte att den ror sig MED gas, aldrig att den star still UTAN.
  const idle0 = cat.location;
  await test.idle(60);
  const drift = Math.hypot(cat.location.x - idle0.x, cat.location.z - idle0.z);
  console.warn(`[MJAU-GT] stillastaende utan gas: drev ${drift.toFixed(2)} block`);
  if (drift > 1.5)
    return done(test, `katten vandrar sjalv under ryttaren (${drift.toFixed(2)} block)`, false);

  // 4) STYRNING: hall spaken framat och mat om KATTEN flyttar sig.
  //    input_ground_controlled ska omsatta ryttarens rorelseinmatning i
  //    kattens rorelse — det har ar kedjan 2.3.4-fixen gallde.
  const before = cat.location;
  p.moveRelative(0, 1);          // full spak framat
  await test.idle(25);           // ~1,25 s — arenan ar 40 bred, katten ska stanna INNE
  p.stopMoving();
  const after = cat.location;
  const dist = Math.hypot(after.x - before.x, after.z - before.z);
  console.warn(`[MJAU-GT] styrning: katten flyttade ${dist.toFixed(2)} block pa 1,25 s`);
  if (dist < 1.5)
    return done(test, `styrningen svarar inte (${dist.toFixed(2)} block)`, false);

  // 5) HOPP: krafthoppet (can_power_jump) kravs ladda-och-slapp som en
  //    simulerad spelare inte kan gora — men sjalva jump_strength anvands
  //    aven av ett direkt hopp fran ryttaren. Mat kattens hojdvinst.
  await test.idle(20);
  const baseY = cat.location.y;
  let peak = baseY;
  p.jump();
  for (let i = 0; i < 30; i++) { await test.idle(1); if (cat.location.y > peak) peak = cat.location.y; }
  const gain = peak - baseY;
  console.warn(`[MJAU-GT] hopp fran ryttaren: +${gain.toFixed(2)} block`);
  // Ingen FAIL har: kan spelaren inte trigga ridhopp ar det API-begransning,
  // inte ett fel i paketet. Raden ger anda matvarde nar det fungerar.

  done(test, "tamja+sadla+rida+styra via simulerad spelare", true);
})
  .structureName("mjau:arena")
  .maxTicks(2400);

// RYGGSACKEN HAR INGET GAMETEST — medvetet. Ett forsok las har och togs bort:
// overlamningen sker i huvudpaketets 20-tick-loop pa villkoret pl.isSneaking,
// och p.isSneaking pa en SimulatedPlayer far inte det villkoret att bli sant
// (samma sak i natverksboten: dar loste inte ens den beprovade
// framstegsrapporten ut, som anvander EXAKT samma gest). Testet matte alltsa
// simulatorns granser, inte paketet, och ett rott prov som alltid ar rott ar
// samre an inget. Villkoret ar detsamma som framstegsrapportens, och den ar
// bevisad pa riktig Xbox. Se tools/testbot/container-test.js.

gt.registerAsync("mjau", "vagn", async (test) => {
  const p = test.spawnSimulatedPlayer({ x: 20, y: 2, z: 18 }, "GTVagn");
  const cat = test.spawn("mjau:misty", { x: 20, y: 2, z: 21 });
  await test.idle(20);
  let tamed = false;
  for (let i = 0; i < 30 && !tamed; i++) {
    p.setItem(new ItemStack("minecraft:cod", 1), 0, true);
    await test.idle(5);
    p.interactWithEntity(cat);
    await test.idle(10);
    tamed = cat.getProperty("mjau:tam") === 1;
  }
  if (!tamed) return done(test, "vagn: tamjning misslyckades", false);
  p.setItem(new ItemStack("mjau:vagn_tra", 1), 0, true);
  await test.idle(5);
  p.interactWithEntity(cat);
  await test.idle(10);
  if (cat.getProperty("mjau:vagn") !== 1)
    return done(test, "vagnen gick inte att spanna for", false);
  console.warn("[MJAU-GT] vagnen PA");
  await test.idle(10);
  p.interactWithEntity(cat);
  await test.idle(20);
  const riding = p.getComponent("minecraft:riding");
  if (!riding || !riding.entityRidingOn)
    return done(test, "gick inte att SITTA I vagnen", false);
  console.warn("[MJAU-GT] sitter i vagnen");
  const b = cat.location;
  p.moveRelative(0, 1);
  await test.idle(25);
  p.stopMoving();
  const d = Math.hypot(cat.location.x - b.x, cat.location.z - b.z);
  console.warn(`[MJAU-GT] drar vagnen: ${d.toFixed(2)} block`);
  if (d < 1.5) return done(test, "vagnen gar inte att kora", false);
  done(test, "vagn: spanna for + sitta i + kora", true);
})
  .structureName("mjau:arena")
  .maxTicks(2400);

// SATESHOJD PER KATTSTORLEK. Xbox-rapport: "man sitter pa huvudet ibland,
// Maja verkar ha det problemet". Katterna har OLIKA skala (mocha 0.85,
// misty/hazel 1.0, snow/Maja 1.15) men sitspositionen ar hardkodad till
// samma varde i alla. Fragan matningen svarar pa: skalar Bedrock sjalv
// sitspositionen med minecraft:scale, eller ligger den fast i block?
// Ryggens topp i modellen ar y=9 enheter = 0.5625 block vid skala 1.0.
gt.registerAsync("mjau", "sate", async (test) => {
  const p = test.spawnSimulatedPlayer({ x: 20, y: 2, z: 18 }, "GTSate");
  await test.idle(20);
  const rader = [];
  // Ginger (1.10) och Domino (0.95) ar EGNA storlekar. Xbox-rapporten "man
  // sitter pa huvudet ibland" gallde just en oprovad skala, sa varje ny
  // kattstorlek ska matas har innan den lamnar huset.
  for (const [typ, skala] of [["mjau:mocha", 0.85], ["mjau:domino", 0.95],
                              ["mjau:misty", 1.0], ["mjau:ginger", 1.10],
                              ["mjau:snow", 1.15]]) {
    const cat = test.spawn(typ, { x: 20, y: 2, z: 21 });
    await test.idle(10);
    // genvag forbi filterkedjan: den testas redan av "interakt"-testet
    cat.triggerEvent("mjau:on_tame");
    await test.idle(5);
    cat.triggerEvent("mjau:on_sadel_1");
    await test.idle(10);
    for (let i = 0; i < 8; i++) {
      p.teleport({ x: cat.location.x + 1, y: cat.location.y, z: cat.location.z });
      await test.idle(5);
      p.interactWithEntity(cat);
      await test.idle(10);
      if (p.getComponent("minecraft:riding")?.entityRidingOn) break;
    }
    if (!p.getComponent("minecraft:riding")?.entityRidingOn)
      return done(test, `kunde inte sitta upp pa ${typ}`, false);
    const up = p.location.y - cat.location.y;
    const rygg = 0.5625 * skala;          // ryggens topp vid den har skalan
    rader.push(`${typ} skala=${skala} up=${up.toFixed(3)} rygg=${rygg.toFixed(3)} diff=${(up - rygg).toFixed(3)}`);
    console.warn(`[MJAU-GT] sate ${typ}: skala=${skala} up=${up.toFixed(3)} ryggtopp=${rygg.toFixed(3)} diff=${(up - rygg).toFixed(3)}`);
    try { p.stopRiding(); } catch { }
    await test.idle(5);
    try { cat.remove(); } catch { }
    await test.idle(5);
  }
  // Ingen FAIL an: forsta korningen ar en MATNING som avgor om sitsen maste
  // skalas per katt. Assertion sats nar facit finns (se raderna ovan).
  // Antalet lases ur listan: raden sa "alla tre kattstorlekar" medan den
  // mätte fem, och en testutskrift som räknar fel är inte värd att lita på.
  done(test, `sateshojd matt for alla ${rader.length} kattstorlekar: ` + rader.join(" | "), true);
})
  .structureName("mjau:arena")
  .maxTicks(2400);

gt.registerAsync("mjau", "ritual", async (test) => {
  // DEN HEMLIGA FEMTE KATTEN: en lax pa en kattbadd vid midnatt => Midnight.
  // Skriptet i skeppade BP:t skannar var 40:e tick — vanta in det.
  world.setTimeOfDay(18000);
  test.setBlockType("mjau:kattbadd", { x: 10, y: 2, z: 10 });
  await test.idle(10);
  test.spawnItem(new ItemStack("minecraft:salmon", 1), { x: 10.5, y: 3.5, z: 10.5 });
  let found = null;
  for (let i = 0; i < 30 && !found; i++) {
    await test.idle(20);
    const near = test.getDimension().getEntities({ type: "mjau:midnight" });
    if (near.length > 0) found = near[0];
  }
  world.setTimeOfDay(6000);
  if (!found) return done(test, "ritualen: ingen Midnight kom (lax+kattbadd+midnatt)", false);
  console.warn("[MJAU-GT] MIDNIGHT KOM — ritualen fungerar");
  try { found.remove(); } catch { }   // stada: narhetsvakten far inte blockera nasta korning
  done(test, "ritual: lax pa kattbadd vid midnatt gav den hemliga katten", true);
})
  .structureName("mjau:arena")
  .maxTicks(2400);

// SPJUTJAKTAREN GAR ATT FLYGA. "Kan man kora rymdskeppen?" var nej — de var
// byggda av block. Nu ar de en entitet, och just den fragan gar bara att
// besvara genom att faktiskt satta sig i och gasa: komponentlistan ser
// rimlig ut aven nar den inte fungerar. Testet mater de tva sakerna som
// skiljer ett fordon fran en staty — att man kommer OMBORD, och att skeppet
// FLYTTAR SIG nar ryttaren gasar.
gt.registerAsync("mjau", "skepp", async (test) => {
  // stada bort skepp som blivit kvar fran en tidigare (fallen) korning —
  // annars vaxer de i antal och stor bade matningar och skriptets loop
  try {
    for (const g of test.getDimension().getEntities({ type: "mjau:spjutjaktare" })) g.remove();
  } catch { }
  await test.idle(5);
  const skepp = test.spawn("mjau:spjutjaktare", { x: 20, y: 2, z: 20 });
  await test.idle(10);
  const p = test.spawnSimulatedPlayer({ x: 21, y: 2, z: 20 }, "GTSkepp");
  await test.idle(20);

  // NAVIGATORSSTOLEN. Kravet "ingen katt, ingen flygning" gar INTE att prova
  // harifran: en simulerad spelare syns som undefined i world.getAllPlayers()
  // sett fran ett vanligt skriptpaket, sa skriptets kattkontroll ser aldrig
  // vare sig piloten eller att den satt sig. Det testet kan bevisa ar att
  // stolen finns och att en katt gar att satta i den — utan det spelar regeln
  // ingen roll. Sjalva utkastningen maste provas pa riktig konsol.
  const katt = test.spawn("mjau:misty", { x: 22, y: 2, z: 20 });
  await test.idle(5);
  katt.triggerEvent("mjau:on_tame");
  await test.idle(10);
  let kattIStol = false;
  try {
    skepp.getComponent("minecraft:rideable").addRider(katt);
    await test.idle(10);
    kattIStol = katt.getComponent("minecraft:riding")?.entityRidingOn?.id === skepp.id;
  } catch (e) { console.warn("[MJAU-GT] skepp: addRider kastade " + e); }
  console.warn(`[MJAU-GT] skepp: katt i navigatorsstolen = ${kattIStol}`);
  if (!kattIStol) return done(test, "katten gick inte att satta i navigatorsstolen", false);

  let ombord = false;
  for (let i = 0; i < 10 && !ombord; i++) {
    p.teleport({ x: skepp.location.x + 1, y: skepp.location.y, z: skepp.location.z });
    await test.idle(5);
    p.interactWithEntity(skepp);
    await test.idle(10);
    ombord = !!p.getComponent("minecraft:riding")?.entityRidingOn;
  }
  if (!ombord) return done(test, "skeppet gick inte att sitta i (rideable/seats?)", false);
  await test.idle(20);
  if (!p.getComponent("minecraft:riding")?.entityRidingOn)
    return done(test, "piloten satt inte kvar", false);

  // FRAMAT. Korta pass med hemflytt emellan: forsta forsoket lat skeppet gasa
  // i 2,5 s — det flog 45 block, alltsa RAKT UT ur arenan (40x40), och nasta
  // avlasning small med "Entity being invalid".
  try { skepp.teleport({ x: 20, y: 4, z: 20 }); } catch { }
  await test.idle(5);
  const a0 = { ...skepp.location };
  p.moveRelative(0, 1);
  await test.idle(15);
  const b0 = { ...skepp.location };
  try { p.stopMoving(); } catch { }
  await test.idle(5);
  const sidled = Math.hypot(b0.x - a0.x, b0.z - a0.z);
  console.warn(`[MJAU-GT] skepp: ${sidled.toFixed(2)} block sidled pa 0,75 s`);

  // HOJDMEKANIKEN. Skriptets hojdroder lyfter skeppet med applyImpulse nar
  // ryttaren hoppar respektive smyger. Sjalva knapptrycken gar INTE att
  // simulera: en ridande SimulatedPlayer rapporterar varken isJumping,
  // isSneaking eller blickvinkel — allt lag kvar pa 0/false hur vi an satte
  // dem (setRotation, lookAtLocation, isSneaking=true). Det testet DAREMOT
  // kan bevisa ar att sjalva lyftet biter pa den har entiteten; utan det
  // spelar knapparna ingen roll. Aterstoden maste provas pa riktig konsol.
  let lyft = 0;
  try {
    skepp.teleport({ x: 20, y: 8, z: 20 });
    await test.idle(5);
    const y0 = skepp.location.y;
    skepp.applyImpulse({ x: 0, y: 1.0, z: 0 });
    await test.idle(10);
    lyft = skepp.location.y - y0;
  } catch (e) { console.warn("[MJAU-GT] skepp: applyImpulse kastade " + e); }
  console.warn(`[MJAU-GT] skepp: lyft av impuls 1.0 = ${lyft.toFixed(2)} block`);

  try { p.stopMoving(); p.stopRiding(); } catch { }
  await test.idle(5);
  try { skepp.remove(); } catch { }
  if (sidled < 3)
    return done(test, `skeppet ror sig inte: bara ${sidled.toFixed(2)} block pa 0,75 s`, false);
  if (lyft < 1)
    return done(test, `hojdrodret biter inte: impuls 1.0 gav ${lyft.toFixed(2)} block`, false);
  done(test, `skepp: katt i navigatorsstolen, ${sidled.toFixed(2)} block sidled, impuls lyfter ${lyft.toFixed(2)} block (knapparna gar ej att simulera)`, true);
})
  .structureName("mjau:arena")
  .maxTicks(2400);
''')

# Arena: 7x5x7-struktur, stengolv, resten luft. GameTest kräver en struktur
# att placera testet i. NBT skriven för hand — inga bibliotek på maskinen.
V = nbt.Val
SX, SY, SZ = 40, 6, 40
idx = []
for x in range(SX):
    for y in range(SY):
        for z in range(SZ):
            edge = x in (0, SX - 1) or z in (0, SZ - 1)
            solid = y == 0 or (edge and y <= 2)   # golv + 2 hog kantvagg
            idx.append(V(nbt.TAG_INT, 0 if solid else 1))   # 0=sten, 1=luft
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
