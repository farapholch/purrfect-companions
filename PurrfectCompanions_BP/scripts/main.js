// Den hemliga femte katten. Ingen hittar den här filen av misstag —
// och den som gör det har förtjänat hemligheten.
//
// Ritualen: lägg en LAX på en KATTBÄDD medan månen står som högst
// (midnatt, tick 17000–19000). Då kommer Midnight — kolsvart, med ögon
// av bärnsten. En Midnight inom 48 block räcker: ritualen är en
// hälsning, inte en fabrik.
import { world, system, ItemStack } from "@minecraft/server";

const MIDNIGHT = "mjau:midnight";

system.runInterval(() => {
  const t = world.getTimeOfDay();
  if (t < 17000 || t > 19000) return;
  const d = world.getDimension("overworld");
  let items;
  try { items = d.getEntities({ type: "minecraft:item" }); } catch { return; }
  for (const it of items) {
    let stack;
    try { stack = it.getComponent("minecraft:item")?.itemStack; } catch { continue; }
    if (!stack || stack.typeId !== "minecraft:salmon") continue;
    const p = it.location;
    let onBed = false;
    for (const dy of [0, -1]) {
      try {
        const b = d.getBlock({ x: Math.floor(p.x), y: Math.floor(p.y) + dy, z: Math.floor(p.z) });
        if (b && b.typeId === "mjau:kattbadd") onBed = true;
      } catch { }
    }
    if (!onBed) continue;
    try {
      if (d.getEntities({ type: MIDNIGHT, location: p, maxDistance: 48 }).length > 0) continue;
    } catch { }
    it.remove();                                   // laxen tas emot
    const cat = d.spawnEntity(MIDNIGHT, { x: p.x, y: Math.floor(p.y) + 1, z: p.z });
    try { cat.triggerEvent("mjau:grow_up"); } catch { }
    try {
      for (const pl of world.getAllPlayers()) {
        const dx = pl.location.x - p.x, dz = pl.location.z - p.z;
        if (dx * dx + dz * dz < 32 * 32) give(pl, "ur_morkret");
      }
    } catch { }
    try { d.playSound("mob.cat.straymeow", p); } catch { }
    try { d.playSound("random.levelup", p); } catch { }
    try {
      for (let i = 0; i < 12; i++)
        d.spawnParticle("minecraft:campfire_smoke_particle", {
          x: p.x + (Math.random() - 0.5) * 1.5,
          y: p.y + Math.random() * 1.2,
          z: p.z + (Math.random() - 0.5) * 1.5,
        });
    } catch { }
  }
}, 40);

// Den andra hemliga katten. Samma regel som Midnight — ingen förklaring i
// handboken, ingen ledtråd i dialogen. Barnen ska hitta henne genom att
// bara vara någonstans, inte genom att läsa en instruktion.
//
// Ritualen: stå vid bergets topp (samma plats som Bergsbestigaren) mitt i
// natten. Aurora kommer till dem som klättrar högt när mörkret är som
// djupast. Till skillnad från Midnight kostar det ingen gåva — bara att
// vara där. Ett Aurora-fynd inom 48 block räcker.
const AURORA = "mjau:aurora";
system.runInterval(() => {
  const t = world.getTimeOfDay();
  if (t < 13000 || t > 23000) return;
  const d = world.getDimension("overworld");
  let players;
  try { players = world.getAllPlayers(); } catch { return; }
  // Bergets topp ligger på en KOORDINAT, inte på ett landmärke — utan den här
  // vakten kom Aurora till den som råkade stå på (26, 80) i sin egen värld.
  // Bergsbestigaren-utmärkelsen på samma plats var redan vaktad; ritualen var
  // det inte.
  if (catHavenWorld !== true) return;
  for (const pl of players) {
    if (!pl) continue;                 // getAllPlayers kan ge tomma platser
    const L = pl.location;
    if (Math.hypot(L.x - 26, L.z - 80) > 6 || L.y < -50) continue;
    try {
      if (d.getEntities({ type: AURORA, location: L, maxDistance: 48 }).length > 0) continue;
    } catch { continue; }
    const cat = d.spawnEntity(AURORA, { x: L.x, y: L.y + 1, z: L.z });
    try { cat.triggerEvent("mjau:grow_up"); } catch { }
    try { give(pl, "norrsken"); } catch { }
    try { d.playSound("mob.cat.purreow", L); } catch { }
    try { d.playSound("random.levelup", L); } catch { }
    try {
      for (let i = 0; i < 12; i++)
        d.spawnParticle("minecraft:end_rod", {
          x: L.x + (Math.random() - 0.5) * 2,
          y: L.y + Math.random() * 1.5,
          z: L.z + (Math.random() - 0.5) * 2,
        });
    } catch { }
  }
}, 40);

// Den TREDJE hemliga katten — Nova. Samma tystnadsregel som Midnight och
// Aurora: ingen förklaring i handboken, ingen ledtråd i dialogen.
//
// Ritualen är en ANNAN sorts gåta än de tidigare: inte en plats och inte en
// gåva, utan att SAMLA. Bär alla fyra energisvärdsfärgerna samtidigt så kommer
// hon. Loggboken i Stjärnhamnen antyder det på sista sidan ("hon svarar bara
// den som bär alla fyra färgerna samtidigt") utan att säga vad som händer.
const NOVA = "mjau:nova";
const BLAD = ["mjau:energisvard_bla", "mjau:energisvard_gron",
              "mjau:energisvard_rod", "mjau:energisvard_lila"];
system.runInterval(() => {
  const d = world.getDimension("overworld");
  let players;
  try { players = world.getAllPlayers(); } catch { return; }
  for (const pl of players) {
    if (!BLAD.every(b => hasItem(pl, b))) continue;
    const L = pl.location;
    try {
      if (d.getEntities({ type: NOVA, location: L, maxDistance: 64 }).length > 0) continue;
    } catch { continue; }
    const cat = d.spawnEntity(NOVA, { x: L.x, y: L.y + 1, z: L.z });
    try { cat.triggerEvent("mjau:grow_up"); } catch { }
    try { give(pl, "stjarnfodd"); } catch { }
    try { d.playSound("mob.cat.purreow", L); } catch { }
    try { d.playSound("random.levelup", L); } catch { }
    try {
      for (let i = 0; i < 16; i++)
        d.spawnParticle("minecraft:end_rod", {
          x: L.x + (Math.random() - 0.5) * 2.5,
          y: L.y + Math.random() * 2,
          z: L.z + (Math.random() - 0.5) * 2.5,
        });
    } catch { }
  }
}, 40);

// ---------------------------------------------------------------------------
// ENERGISVÄRDENS EFFEKTER. Bladet var bara ett föremål med ett skadevärde:
// "jag vet inte hur de funkar mer än att de sitter fast på kattens rygg".
// Nu syns det att det lever. Gnistorna är EGNA partiklar (mjau:blad_*) i
// resurspaketet, en per färg, så ett blått blad gnistrar blått.
//
// Två bärare, två uttryck:
//   spelaren — gnistor kring handen medan bladet hålls fram
//   katten   — ett glesare spår kring ryggen
// Katten läses via entitetsegenskapen mjau:energisvard (0 = inget blad,
// 1-4 = färgen) — samma egenskap som geometrin styrs av, så det finns inget
// eget register att hålla synkat.
const BLAD_PARTIKEL = {
  "mjau:energisvard_bla": "mjau:blad_bla",
  "mjau:energisvard_gron": "mjau:blad_gron",
  "mjau:energisvard_rod": "mjau:blad_rod",
  "mjau:energisvard_lila": "mjau:blad_lila",
};
const BLAD_FARG_NR = ["", "mjau:blad_bla", "mjau:blad_gron",
                      "mjau:blad_rod", "mjau:blad_lila"];

function heldItem(pl) {
  try {
    const inv = pl.getComponent("minecraft:inventory")?.container;
    return inv ? inv.getItem(pl.selectedSlotIndex) : undefined;
  } catch { return undefined; }
}

function gnistra(d, partikel, x, y, z, spridning, antal) {
  for (let i = 0; i < antal; i++) {
    try {
      d.spawnParticle(partikel, {
        x: x + (Math.random() - 0.5) * spridning,
        y: y + (Math.random() - 0.5) * spridning,
        z: z + (Math.random() - 0.5) * spridning,
      });
    } catch { }
  }
}

system.runInterval(() => {
  const d = world.getDimension("overworld");
  try {
    for (const pl of world.getAllPlayers()) {
      const it = heldItem(pl);
      const p = it && BLAD_PARTIKEL[it.typeId];
      if (!p) continue;
      const L = pl.location;
      gnistra(d, p, L.x, L.y + 1.3, L.z, 1.1, 3);
    }
  } catch { }
  try {
    for (const c of d.getEntities({ families: ["mjaukatt"] })) {
      let nr = 0;
      try { nr = c.getProperty("mjau:energisvard") ?? 0; } catch { continue; }
      if (!nr) continue;
      const L = c.location;
      gnistra(d, BLAD_FARG_NR[nr], L.x, L.y + 0.6, L.z, 0.7, 1);
    }
  } catch { }
}, 5);

// ---------------------------------------------------------------------------
// UPPDRAGS-UTMÄRKELSER: titel + fanfar när milstolpar nås. Plattforms-
// achievements går inte att ge från paket — det här är vårt eget system.
// Texterna är translate-nycklar (mjau.achv.*) i språkfilerna, så familje-
// varianten blir svensk av sig själv. Per-spelare-minne i dynamic properties
// med Map-reserv om API-nivån saknar dem.
const awarded = new Map();

// TRIPPELSKATTEN: tre nycklar gömda i äng/grotta/damm-ö/skogslund —
// har spelaren alla tre samtidigt i väskan är skatten hennes.
function hasItem(pl, typeId) {
  try {
    const inv = pl.getComponent("minecraft:inventory")?.container;
    if (!inv) return false;
    for (let i = 0; i < inv.size; i++) {
      const it = inv.getItem(i);
      if (it && it.typeId === typeId) return true;
    }
  } catch { }
  return false;
}

function countItem(pl, typeId) {
  try {
    const inv = pl.getComponent("minecraft:inventory")?.container;
    if (!inv) return 0;
    let n = 0;
    for (let i = 0; i < inv.size; i++) {
      const it = inv.getItem(i);
      if (it && it.typeId === typeId) n += it.amount;
    }
    return n;
  } catch { return 0; }
}

// HANDELSPOSTEN: tar bort N st av ett föremål ur spelarens inventarie.
// Anropas bara efter countItem() redan bekräftat att det finns tillräckligt.
function consumeItem(pl, typeId, count) {
  try {
    const inv = pl.getComponent("minecraft:inventory")?.container;
    if (!inv) return;
    let remaining = count;
    for (let i = 0; i < inv.size && remaining > 0; i++) {
      const it = inv.getItem(i);
      if (!it || it.typeId !== typeId) continue;
      const take = Math.min(remaining, it.amount);
      remaining -= take;
      if (take >= it.amount) inv.setItem(i, undefined);
      else { it.amount -= take; inv.setItem(i, it); }
    }
  } catch { }
}

function hasAward(pl, id) {
  try { if (pl.getDynamicProperty("mjau_achv_" + id)) return true; } catch { }
  try { return awarded.get(pl.id + ":" + id) === true; } catch { return false; }
}

// Speltest-önskemål ("belöningar för de flesta uppdrag så de blir roligare"):
// give() gav bara en titel-popup, inget spelaren faktiskt fick i handen.
// XP åt alla, plus ett fåtal riktiga föremål där uppdraget annars gick
// tomhänt (trippelskatten hade inget föremål alls kopplat till SJÄLVA
// utmärkelsen - bara till de tre nyckelkistorna som redan plockats).
const XP_REWARD = {
  forsta_vannen: 10, ryttaren: 10, fiskarkatten: 10, ur_morkret: 15,
  befriaren: 15, fyrvaktaren: 15, skattgravaren: 15, lados_hemlighet: 15,
  hela_flocken: 20, alla_hemma: 20,
  trippelskatten: 30, bergsbestigaren: 25, regnbagssamlaren: 25, hinderbanan: 30,
  djuphavsdykaren: 30, handelsman: 20, vindskatten: 25,
  kattmastare: 50, norrsken: 40, stjarnfodd: 40, manlandaren: 35,
};
const ITEM_REWARD = {
  ur_morkret: [{ id: "minecraft:phantom_membrane", n: 2 }],
  trippelskatten: [{ id: "minecraft:diamond", n: 2 }],
  manlandaren: [{ id: "minecraft:diamond", n: 3 }],
};

function give(pl, id) {
  if (hasAward(pl, id)) return;
  try { pl.setDynamicProperty("mjau_achv_" + id, true); } catch { }
  try { pl.addTag("mjau_achv_" + id); } catch { }   // taggar syns ÖVER paketgränser
  try { awarded.set(pl.id + ":" + id, true); } catch { }
  try {
    pl.onScreenDisplay.setTitle(
      { rawtext: [{ text: "🏆 " }, { translate: "mjau.achv." + id }] },
      { subtitleText: { rawtext: [{ translate: "mjau.achv." + id + ".sub" }] },
        fadeInDuration: 10, stayDuration: 70, fadeOutDuration: 20 });
  } catch { }
  try { pl.playSound("random.levelup"); } catch { }
  try { if (XP_REWARD[id]) pl.addExperience(XP_REWARD[id]); } catch { }
  try {
    const inv = pl.getComponent("minecraft:inventory")?.container;
    for (const { id: itemId, n } of ITEM_REWARD[id] ?? []) {
      inv?.addItem(new ItemStack(itemId, n));
    }
  } catch { }
}

// PROGRESS-RAPPORTEN: smyg intill en tämjd katt så "berättar" den i chatten
// vilka uppdrag som är klara. Den hemliga nian visas som ??? tills den tagits.
// TVÅ LISTOR, inte en. Addonet ska gå att spela fristående, och tio av de
// sexton utmärkelserna hänger på Kattgårdens koordinater — fyren, berget,
// hinderbanan, sjön, nycklarna. En spelare som laddat ner paketet till sin
// egen värld kunde alltså aldrig göra listan färdig, och kattmästarfesten låg
// bakom just den omöjliga listan.
//
// KATT_ORDER är det som fungerar VAR SOM HELST (katterna spawnar naturligt på
// slätter, så de går att hitta i vilken värld som helst). Festen kräver bara
// den. KATTGARDEN_ORDER visas bara för den som faktiskt är i Kattgården.
const KATT_ORDER = ["forsta_vannen", "hela_flocken", "ryttaren", "fiskarkatten",
                    "skattgravaren", "ur_morkret"];
const KATTGARDEN_ORDER = ["befriaren", "fyrvaktaren", "lados_hemlighet", "alla_hemma",
                          "trippelskatten", "bergsbestigaren", "regnbagssamlaren",
                          "hinderbanan", "djuphavsdykaren", "handelsman"];
const ACHV_ORDER = [...KATT_ORDER, ...KATTGARDEN_ORDER];
const rapportTyst = new Map();   // spelar-id -> tick då nästa rapport tillåts

// VÄLKOMSTEN. Den som spelar i Kattgården har en handbok i startkistan; den
// som laddat ner addonet till sin egen värld har ingenting alls och vet inte
// att katten kan sadlas, fiska, bära plagg eller att det finns hemligheter.
// Tre rader vid första tämjda katten, en gång per spelare — resten hittar de
// själva genom att smyga intill en katt (framstegsrapporten).
function valkomna(pl) {
  try { if (pl.getDynamicProperty("mjau_valkomnad")) return; } catch { }
  try { pl.setDynamicProperty("mjau_valkomnad", true); } catch { }
  try {
    pl.sendMessage({ rawtext: [
      { text: "\n" }, { translate: "mjau.valkommen.rad1" },
      { text: "\n" }, { translate: "mjau.valkommen.rad2" },
      { text: "\n" }, { translate: "mjau.valkommen.rad3" },
      { text: "\n" }, { translate: "mjau.valkommen.rad4" },
    ] });
    pl.playSound("mob.cat.purr");
  } catch { }
}

function rapportera(pl) {
  const rt = [{ translate: "mjau.progress.title" }];
  let n = 0;
  // i en främmande värld listas bara det som går att ta där — annars fylls
  // rapporten av uppdrag spelaren aldrig kan bli klar med
  const lista = catHavenWorld === true ? ACHV_ORDER : KATT_ORDER;
  for (const id of lista) {
    const har = hasAward(pl, id);
    if (har) n++;
    rt.push({ text: "\n" + (har ? "§a✔ §r" : "§8◻ §7") });
    rt.push(har || id !== "ur_morkret" ? { translate: "mjau.achv." + id }
                                       : { text: "???" });
  }
  rt.push({ text: "\n§e" + n + "/" + lista.length });
  try { pl.sendMessage({ rawtext: rt }); pl.playSound("mob.cat.meow"); } catch { }
}

// KATTMÄSTAR-FESTEN: alla tio utmärkelser -> engångsfest med fyrverkeri,
// guldkronan i handen och hjärtan över alla tämjda katter i närheten.
function fest(pl) {
  give(pl, "kattmastare");
  const d = world.getDimension("overworld");
  try { pl.getComponent("minecraft:inventory").container.addItem(new ItemStack("mjau:krona_gold", 1)); } catch { }
  let L = { x: 0, y: -60, z: 12 };
  try { L = pl.location; } catch { }
  let skott = 0;
  const kanon = system.runInterval(() => {
    skott++;
    if (skott > 6) { system.clearRun(kanon); return; }
    try {
      d.spawnEntity("minecraft:fireworks_rocket", {
        x: L.x + (Math.random() - 0.5) * 10, y: L.y, z: L.z + (Math.random() - 0.5) * 10 });
    } catch { }
    try { d.playSound("mob.cat.meow", L); } catch { }
  }, 15);
  try {
    for (const c of d.getEntities({ families: ["mjaukatt"], location: L, maxDistance: 16 }))
      d.spawnParticle("minecraft:heart_particle", { x: c.location.x, y: c.location.y + 0.8, z: c.location.z });
  } catch { }
  console.warn("[mjau] KATTMASTARE-festen firad");
}

// testkrok: /scriptevent mjau:test_fest fran konsolen avfyrar festen (röktestet)
try {
  system.afterEvents.scriptEventReceive.subscribe(ev => {
    if (ev.id !== "mjau:test_fest") return;
    try { fest(world.getAllPlayers()[0]); } catch { console.warn("[mjau] fest-test föll"); }
  });
} catch { }

// ---------------------------------------------------------------------------
// GRINDARNA: världen öppnas stegvis (speltest-önskemål: "låsa ner delar av
// världen och öppna stegvis när man klarar quests, så storyn blir tydligare").
// En grind rivs för ALLA så fort NÅGON spelare har klarat förkravet —
// familjen spelar ihop, ingen grind per person. Redan intjänade uppdrag
// öppnar grindarna automatiskt vid nästa världstart (kollen går mot
// dynamic properties som redan ligger i världssparningen). Blocken måste
// matcha grindfyllningarna i build_world.py.
// Boxar i stället for handlistade block: murarna ar 5 block hoga och upp
// till 11 breda sedan staketen (2 block) visade sig ga att hoppa over med en
// katts laddade hopp. y-toppen tar aven med lyktan pa kronet, sa den inte
// blir hangande i luften nar muren rivs. MASTE matcha fill-kommandona i
// build_world.py.
const GATES = [
  { prereq: "fyrvaktaren",    x: 20, y0: -60, y1: -55, z0: 12, z1: 19 },
  { prereq: "trippelskatten", x: 44, y0: -60, y1: -55, z0: 5,  z1: 15 },
  { prereq: "hinderbanan",    x: 65, y0: -62, y1: -61, z0: 45, z1: 45 },
];

function gateBlocks(gt) {
  const out = [];
  for (let y = gt.y0; y <= gt.y1; y++)
    for (let z = gt.z0; z <= gt.z1; z++) out.push([gt.x, y, z]);
  return out;
}

function oppnaGrind(d, gt) {
  const rutor = gateBlocks(gt);
  for (const [x, y, z] of rutor) {
    try { d.getBlock({ x, y, z })?.setType("minecraft:air"); } catch { }
  }
  // partiklar bara på murens mitt — en per ruta blev en vägg av gnistor när
  // muren växte från 4 till upp till 66 block
  const mz = Math.floor((gt.z0 + gt.z1) / 2);
  for (let y = gt.y0; y <= gt.y1; y++) {
    try { d.spawnParticle("minecraft:end_rod", { x: gt.x + 0.5, y: y + 0.5, z: mz + 0.5 }); } catch { }
  }
  const [sx, sy, sz] = rutor[0];
  try { d.playSound("random.levelup", { x: sx, y: sy, z: sz }); } catch { }
  for (const pl of world.getAllPlayers()) {
    try { pl.onScreenDisplay.setActionBar({ rawtext: [{ translate: "mjau.gate.open" }] }); } catch { }
  }
  console.warn("[mjau] grind öppnad: " + gt.prereq);
}

// testkrok: /scriptevent mjau:test_grind river alla grindar (röktestet)
try {
  system.afterEvents.scriptEventReceive.subscribe(ev => {
    if (ev.id !== "mjau:test_grind") return;
    try {
      const d = world.getDimension("overworld");
      for (const gt of GATES) oppnaGrind(d, gt);
    } catch { console.warn("[mjau] grind-test föll"); }
  });
} catch { }

// VAKTHUNDEN: den som fäller hunden vid kulan befriar katten därinne
try {
  world.afterEvents.entityDie.subscribe(ev => {
    if (ev.deadEntity?.typeId !== "mjau:vakthund") return;
    const p = ev.deadEntity.location;
    let fick = 0;
    for (const pl of world.getAllPlayers()) {
      try {
        const dx = pl.location.x - p.x, dz = pl.location.z - p.z;
        if (dx * dx + dz * dz < 24 * 24) { give(pl, "befriaren"); fick++; }
      } catch { }
    }
    console.warn("[mjau] vakthunden fälld — Befriaren till " + fick + " spelare");
  });
} catch { }

let hundSedd = false, hundPlats = null;   // vakthunds-vakans minne

let catHavenWorld = null;   // fyrljuset på känd plats = vi är i Cat Haven
let starHarbourWorld = null;  // navlyktan i kupolen = vi är i Stjärnhamnen

system.runInterval(() => {
  const d = world.getDimension("overworld");
  let cats;
  try { cats = d.getEntities({ families: ["mjaukatt"] }); } catch { return; }
  if (catHavenWorld === null) {
    // signaturen måste ligga vid SPAWN (laddad från sekund ett) — fyrljuset
    // var 55 block bort och doktorn väntade tills någon råkade gå dit
    try {
      catHavenWorld = d.getBlock({ x: 2, y: -59, z: 8 })?.typeId === "mjau:kattlucka" ||
                      d.getBlock({ x: 0, y: -41, z: 56 })?.typeId === "minecraft:glowstone" ||
                      d.getBlock({ x: 0, y: -42, z: 56 })?.typeId === "minecraft:glowstone";
      // Stjärnhamnens signatur: navlyktan mitt i kupolgolvet, två steg från
      // spawn och därmed laddad från första sekunden
      starHarbourWorld = d.getBlock({ x: 0, y: -61, z: 0 })?.typeId === "minecraft:sea_lantern";
    }
    catch { catHavenWorld = null; starHarbourWorld = null; }   // chunk oladdad — fråga igen
  }
  // grindkollen: sentinel-rutan (murens nedre hörn) kvar + någon spelare har
  // förkravet → riv muren. Billigt: ett getBlock per grind, inte per ruta.
  if (catHavenWorld) {
    try {
      const alla = world.getAllPlayers();
      for (const gt of GATES) {
        const sb = d.getBlock({ x: gt.x, y: gt.y0, z: gt.z0 });
        if (!sb || sb.typeId === "minecraft:air") continue;
        if (alla.some(pl => hasAward(pl, gt.prereq))) oppnaGrind(d, gt);
      }
    } catch { }
  }
  const tamed = cats.filter(c => { try { return c.getProperty("mjau:tam") === 1; } catch { return false; } });
  // vakthunds-vakan: syns hunden en tick och är borta nästa har någon fällt den
  try {
    const hundar = d.getEntities({ type: "mjau:vakthund" });
    if (hundar.length > 0) {
      hundSedd = true; hundPlats = hundar[0].location;
    } else if (hundSedd && hundPlats) {
      hundSedd = false;
      console.warn("[mjau] vakan: hunden borta — delar ut Befriaren");
      for (const pl of world.getAllPlayers()) {
        try {
          const dx = pl.location.x - hundPlats.x, dz = pl.location.z - hundPlats.z;
          if (dx * dx + dz * dz < 32 * 32) give(pl, "befriaren");
        } catch { }
      }
      hundPlats = null;
    }
  } catch { }

  for (const pl of world.getAllPlayers()) {
    if (!pl) continue;   // gametest-miljön kan lämna trasiga spelarposter
    try {
    if (tamed.length >= 1) { give(pl, "forsta_vannen"); valkomna(pl); }
    if (tamed.length >= 4) give(pl, "hela_flocken");
    try {
      const r = pl.getComponent("minecraft:riding")?.entityRidingOn;
      if (r && r.typeId.startsWith("mjau:")) give(pl, "ryttaren");
    } catch { }
    for (const c of cats) {
      try {
        if (c.getProperty("mjau:sadel") > 0 &&
            d.getBlock({ x: Math.floor(c.location.x), y: Math.floor(c.location.y), z: Math.floor(c.location.z) })?.typeId === "minecraft:water")
          give(pl, "fiskarkatten");
        if (c.getProperty("mjau:ryggsack") > 0) {
          for (const it of d.getEntities({ type: "minecraft:item", location: c.location, maxDistance: 5 })) {
            const t = it.getComponent("minecraft:item")?.itemStack?.typeId;
            if (t === "minecraft:string" || t === "minecraft:feather" || t === "minecraft:diamond")
              give(pl, "skattgravaren");
          }
        }
      } catch { }
    }
    if (catHavenWorld) {
      const L = pl.location;
      if (L.y > -46 && Math.hypot(L.x - 0, L.z - 56) < 7) give(pl, "fyrvaktaren");
      if (L.y > -52 && Math.hypot(L.x - 26, L.z - 80) < 5) give(pl, "bergsbestigaren");
      if (L.y > -58 && Math.hypot(L.x - 113, L.z - 10) < 4) give(pl, "hinderbanan");
      if (Math.hypot(L.x - 65, L.z - 49) < 3 && L.y < -60) give(pl, "djuphavsdykaren");
      // VINDEN: hemlig (utanför ACHV_ORDER, samma tanke som norrsken —
      // hemligheter ska inte höja kravet för Kattmästare-finalen)
      if (L.y > -56 && L.y < -50 && L.x > -6 && L.x < 6 && L.z > 12 && L.z < 17)
        give(pl, "vindskatten");
      // HANDELSPOSTEN: lämna in skattletarnas fynd mot en belöning
      // (speltest-önskemål: "treasure trading post") — sköter sig själv,
      // ingen separat nedräkning behövs: när varorna är förbrukade sjunker
      // countItem() under kravet av sig självt tills nästa fynd.
      if (Math.hypot(L.x - 10, L.z + 11) < 3 && L.y > -62 && L.y < -58 &&
          countItem(pl, "minecraft:string") >= 3 && countItem(pl, "minecraft:feather") >= 3 &&
          countItem(pl, "minecraft:diamond") >= 1) {
        // FÖRSTA bytet ger MANTELN (speltest-fråga: "finns det en supermantel
        // i världen?" — nej, den var enda superkraften som bara gick att
        // crafta). Efterföljande byten ger smaragder som förut, så posten
        // förblir användbar när skattletarna gräver upp mer.
        const forstaBytet = !hasAward(pl, "handelsman");
        consumeItem(pl, "minecraft:string", 3);
        consumeItem(pl, "minecraft:feather", 3);
        consumeItem(pl, "minecraft:diamond", 1);
        try {
          const inv = pl.getComponent("minecraft:inventory")?.container;
          inv?.addItem(new ItemStack(forstaBytet ? "mjau:mantel_lila" : "minecraft:emerald", forstaBytet ? 1 : 5));
        } catch { }
        try { pl.playSound("random.levelup"); } catch { }
        try {
          pl.onScreenDisplay.setActionBar({
            rawtext: [{ translate: forstaBytet ? "mjau.trade.mantel" : "mjau.trade.done" }]
          });
        } catch { }
        give(pl, "handelsman");
      }
      // FANFAR per band: en liten stund vid varje NY färg, skild från de
      // "riktiga" achievement-titlarna (actionbar i stället för setTitle)
      // — speltest-önskemål: "lite mer belönande".
      for (const c2 of ["red", "orange", "yellow", "green", "blue", "purple"]) {
        const seenKey = "mjau_bow_seen_" + c2;
        let seen = false;
        try { seen = !!pl.getDynamicProperty(seenKey); } catch { }
        if (!seen && hasItem(pl, "minecraft:" + c2 + "_dye")) {
          try { pl.setDynamicProperty(seenKey, true); } catch { }
          try {
            pl.onScreenDisplay.setActionBar({
              rawtext: [{ text: "🎀 " }, { translate: "mjau.bow." + c2 }]
            });
          } catch { }
          try { pl.playSound("random.levelup", { pitch: 1.6 }); } catch { }
          try {
            const L2 = pl.location;
            for (let i = 0; i < 8; i++)
              d.spawnParticle("minecraft:totem_particle", {
                x: L2.x + (Math.random() - 0.5) * 1.2,
                y: L2.y + 1 + Math.random() * 0.8,
                z: L2.z + (Math.random() - 0.5) * 1.2,
              });
          } catch { }
        }
      }
      if (!hasAward(pl, "regnbagssamlaren") &&
          ["red", "orange", "yellow", "green", "blue", "purple"].every(c => hasItem(pl, "minecraft:" + c + "_dye"))) {
        give(pl, "regnbagssamlaren");
        console.warn("[mjau] Regnbagssamlaren utdelad — alla sex band hittade");
      }
      if (L.y < -60.5 && L.x > 0 && L.x < 8 && L.z > 7 && L.z < 14) give(pl, "lados_hemlighet");
      if (tamed.length >= 4) {
        const hemma = tamed.filter(c => c.location.x > -7 && c.location.x < 7 &&
                                        c.location.z > 7 && c.location.z < 18).length;
        if (hemma >= 4) give(pl, "alla_hemma");
      }
    }
    if (pl.isSneaking && (rapportTyst.get(pl.id) || 0) <= system.currentTick) {
      const L = pl.location;
      const nara = tamed.some(c => Math.hypot(c.location.x - L.x,
        c.location.y - L.y, c.location.z - L.z) < 2.5);
      if (nara) { rapportTyst.set(pl.id, system.currentTick + 600); rapportera(pl); }
    }
    // OBS (genomspelning): kvittot syns inte i sim-testet — samma kända
    // begränsning som Befriaren ursprungligen (sim-spelaren är strukturellt
    // onåbar för give() i huvudpaketets loop). Beprövad kod, samma mönster
    // som redan bevisat funkar på riktig Xbox (First Friend-achievementet).
    if (!hasAward(pl, "trippelskatten") && hasItem(pl, "minecraft:amethyst_shard") &&
        hasItem(pl, "minecraft:nautilus_shell") && hasItem(pl, "minecraft:rabbit_foot")) {
      give(pl, "trippelskatten");
      console.warn("[mjau] Trippelskatten utdelad — alla tre nycklar samlade");
    }
    // MÅNKARTLÄGGAREN: de tre fynden från utposterna i Stjärnhamnen, burna
    // samtidigt. Ligger MEDVETET utanför ACHV_ORDER — den listan är grinden
    // till kattmästarfesten, och föremålen finns bara i rymdvärlden. Hade den
    // legat med hade festen blivit omöjlig att nå i Cat Haven.
    // ...och bara i Stjärnhamnen: de tre fynden är vanliga vanilla-föremål, så
    // utan vakten kunde en spelare som bara har kattpaketet plötsligt få
    // "Moon Surveyor" för att hen råkade bära ekoskärva, åskledare och
    // havshjärta samtidigt.
    if (starHarbourWorld === true &&
        !hasAward(pl, "manlandaren") && hasItem(pl, "minecraft:echo_shard") &&
        hasItem(pl, "minecraft:lightning_rod") && hasItem(pl, "minecraft:heart_of_the_sea")) {
      give(pl, "manlandaren");
      console.warn("[mjau] Manlandaren utdelad — alla tre fynd hemma");
    }
    if (!hasAward(pl, "kattmastare") && KATT_ORDER.every(id => hasAward(pl, id))) fest(pl);
    } catch { }
  }
}, 40);

// ---------------------------------------------------------------------------
// MÖBELDOKTORN: block sparade av byggservern renderas nedsjunkna på klienten
// ("groparna") — spelarplacerade renderas rätt. Bevisat på Xbox 2026-08-09:
// samma block, olika stämpel i chunkpaletten. Botemedlet: skriv om möblerna
// EN gång inne i spel-sessionen (klientens placeringsväg), sedan är chunken
// klientstämplad för alltid. Körs tills alla celler kunnat behandlas (kräver
// att spelaren laddat både byn och kulan) och markerar sedan världen läkt.
const MOBLER = [
  [-4, -59, 16], [-2, -59, 16], [2, -59, 16], [4, -59, 16],   // sängraden
  [-4, -59, 13], [-3, -59, 13],                                // matskålarna
  [-5, -59, 14], [5, -59, 14], [0, -59, 13], [5, -59, 9],      // låda/ställning/nystan/kartong
  [12, -60, 7],                                                // fiskdammen
  [-52, -60, 66],                                              // den fångna kattens bädd i nya kulan
];
let moblerLagda = false;

system.runInterval(() => {
  if (moblerLagda || catHavenWorld !== true) return;
  try { if (world.getDynamicProperty("mjau_mobler_lagda")) { moblerLagda = true; return; } } catch { }
  const d = world.getDimension("overworld");
  let alla = true;
  for (const [x, y, z] of MOBLER) {
    try {
      const b = d.getBlock({ x, y, z });
      if (!b) { alla = false; continue; }
      if (b.typeId.startsWith("mjau:")) b.setType(b.typeId);
    } catch { alla = false; }
  }
  if (alla) {
    moblerLagda = true;
    try { world.setDynamicProperty("mjau_mobler_lagda", true); } catch { }
    console.warn("[mjau] möblerna omlagda i session — groparna läkta");
  }
}, 100);

// ---------------------------------------------------------------------------
// SUPERKRAFTS-EFFEKTER I LUFTEN: speltest-fråga ("kommer det stjärnor när
// man flyger?", "får vi animeringar med de andra superkrafterna också?").
// Skiljer på STIGANDE (mantelns laddade hopp — stjärnor, "jag hoppar högt!")
// och FALLANDE (vingar/batvingar/horn — glitter, "jag landar mjukt!") via
// lodrät hastighet. Egen snabb loop (var 3:e tick) — huvudloopen (40 tick)
// är för gles för att fånga ett hopp, som är över på under en sekund.
system.runInterval(() => {
  const d = world.getDimension("overworld");
  let cats;
  try { cats = d.getEntities({ families: ["mjaukatt"] }); } catch { return; }
  for (const c of cats) {
    try {
      if (c.isOnGround) continue;
      let vy = 0;
      try { vy = c.getVelocity().y; } catch { }
      if (vy > 0 && (c.getProperty("mjau:mantel") > 0 || c.getProperty("mjau:rymdmantel") > 0)) {
        d.spawnParticle("minecraft:end_rod", { x: c.location.x, y: c.location.y + 0.3, z: c.location.z });
      }
      if (vy < 0 && (c.getProperty("mjau:vingar") > 0 || c.getProperty("mjau:batvingar") > 0 || c.getProperty("mjau:horn") > 0)) {
        d.spawnParticle("minecraft:totem_particle", { x: c.location.x, y: c.location.y + 0.5, z: c.location.z });
      }
    } catch { }
  }
}, 3);

// LÄKARROCKENS HJÄRTAN: samma fråga som ovan — konstant läkning hade inget
// att se. Långsammare loop (var 60:e tick / 3s) eftersom effekten är
// permanent, inte ett kort ögonblick som hoppet — ett hjärta då och då
// räcker för att visa att det pågår utan att spamma.
system.runInterval(() => {
  const d = world.getDimension("overworld");
  let cats;
  try { cats = d.getEntities({ families: ["mjaukatt"] }); } catch { return; }
  for (const c of cats) {
    try {
      if (c.getProperty("mjau:doktorsrock") > 0) {
        d.spawnParticle("minecraft:heart_particle", { x: c.location.x, y: c.location.y + 0.8, z: c.location.z });
      }
    } catch { }
  }
}, 60);

// ---------------------------------------------------------------------------
// RYGGSÄCKEN BÄR PÅ RIKTIGT. Lastrummet sitter i entiteten (mjau:packad, samma
// horse-container som vagnen) — det här är den andra halvan: katten PLOCKAR
// UPP. En ryggsäckskatt som går bredvid dig i gruvan dammsuger upp det som
// ligger på marken innan det hinner försvinna, och du öppnar henne som en
// åsna för att hämta ut det.
//
// Tre vakter, alla tre av misstag inlärda:
//   * MOGNADSTID — utan den snappar hon det du precis släppte för att sortera
//     väskan. 2 sekunder räcker: det du kastar bort hinner du ångra.
//   * FISKUNDANTAGET — torsk, lax och godis är tämjnings- och parningsmat.
//     Att hon åt upp fisken du skulle tämja nästa katt med vore rent sabotage.
//     Undantaget skyddar dessutom Midnight-ritualen, som ÄR en lax på en bädd.
//   * LEDIG PLATS — bara i tom ficka. Då får hela högen plats och det finns
//     ingen rest att lägga tillbaka i världen.
const VAKUUM_RADIE = 4;
const VAKUUM_MOGEN = 40;                 // ticks på marken innan hon rör det
const VAKUUM_EJ = new Set(["minecraft:cod", "minecraft:salmon", "mjau:godis"]);
const FYND = new Set(["minecraft:string", "minecraft:feather", "minecraft:diamond"]);
const itemSedd = new Map();              // föremåls-id -> tick vi först såg det
const packadSedd = new Set();            // katt-id vi redan tipsat om

function tamKatt(c) {
  try { return c.getProperty("mjau:tam") === 1; } catch { return false; }
}

system.runInterval(() => {
  const d = world.getDimension("overworld");
  let cats;
  try { cats = d.getEntities({ families: ["mjaukatt"] }); } catch { return; }
  if (itemSedd.size > 400) itemSedd.clear();   // minnestak: hellre glömma än växa
  for (const c of cats) {
    let ryggsack = 0;
    try { ryggsack = c.getProperty("mjau:ryggsack") ?? 0; } catch { continue; }
    if (!ryggsack || !tamKatt(c)) continue;

    // TIPSET: ingen läser en changelog. Första gången en katt får ryggsäcken
    // på sig får den som står bredvid veta vad den nu duger till.
    if (!packadSedd.has(c.id)) {
      packadSedd.add(c.id);
      try {
        for (const pl of world.getAllPlayers()) {
          if (Math.hypot(pl.location.x - c.location.x, pl.location.z - c.location.z) > 8) continue;
          if (pl.getDynamicProperty("mjau_packtips")) continue;
          pl.setDynamicProperty("mjau_packtips", true);
          pl.onScreenDisplay.setActionBar({ rawtext: [{ translate: "mjau.packad.tips" }] });
        }
      } catch { }
    }

    // ÖVERLÄMNINGEN: den som smyger intill henne får lasten i handen.
    try {
      for (const pl of world.getAllPlayers()) {
        if (!pl.isSneaking) continue;
        if ((lamnaTyst.get(pl.id) || 0) > system.currentTick) continue;
        if (Math.hypot(pl.location.x - c.location.x, pl.location.y - c.location.y,
                       pl.location.z - c.location.z) > 2.5) continue;
        const n = lamnaOver(pl, c);
        if (!n) continue;                    // tom väska: ingen text, ingen paus
        lamnaTyst.set(pl.id, system.currentTick + 100);
        pl.onScreenDisplay.setActionBar({
          rawtext: [{ translate: "mjau.packad.lamnar", with: [String(n)] }] });
        pl.playSound("random.pop");
        // Framstegsrapporten hänger på samma gest. Utan pausen får du
        // uppdragslistan i chatten varje gång du hämtar lasten.
        rapportTyst.set(pl.id, system.currentTick + 200);
      }
    } catch { }

    let box;
    try { box = c.getComponent("minecraft:inventory")?.container; } catch { }
    if (!box || box.emptySlotsCount === 0) continue;

    let items;
    try { items = d.getEntities({ type: "minecraft:item", location: c.location, maxDistance: VAKUUM_RADIE }); }
    catch { continue; }
    for (const it of items) {
      let stack;
      try { stack = it.getComponent("minecraft:item")?.itemStack; } catch { continue; }
      if (!stack || VAKUUM_EJ.has(stack.typeId)) continue;
      const forst = itemSedd.get(it.id);
      if (forst === undefined) { itemSedd.set(it.id, system.currentTick); continue; }
      if (system.currentTick - forst < VAKUUM_MOGEN) continue;
      if (box.emptySlotsCount === 0) break;
      try { box.addItem(stack); } catch { continue; }
      itemSedd.delete(it.id);
      try { it.remove(); } catch { }
      try { d.playSound("random.pop", c.location); } catch { }
      try {
        d.spawnParticle("minecraft:villager_happy", {
          x: c.location.x, y: c.location.y + 0.7, z: c.location.z });
      } catch { }
      // SKATTGRÄVAREN utdelades genom att leta efter fynden PÅ MARKEN intill
      // katten — och nu hinner hon plocka upp dem innan den kollen vaknar
      // (40 ticks). Utmärkelsen följer därför med i väskan i stället.
      if (FYND.has(stack.typeId)) {
        for (const pl of world.getAllPlayers()) {
          try {
            if (Math.hypot(pl.location.x - c.location.x, pl.location.z - c.location.z) < 16)
              give(pl, "skattgravaren");
          } catch { }
        }
      }
    }
  }
}, 20);

// ÖVERLÄMNINGEN — och varför den inte är en lucka som öppnas.
//
// Lastrummet finns: replaceitem mot slot.inventory fyller det, både för vagnen
// och för ryggsäcken. Att en SPELARE kommer åt det gick däremot inte att
// bevisa. En riktig klient i testservern fick inte upp väskan vare sig med
// vanligt tryck eller smygtryck — och inte heller en kistförsedd VANILJAÅSNAS
// inventarie med samma paket. Kontrollen visar att provet inte kan avgöra
// frågan, inte att luckan är trasig; men att lova en lucka i hjälptexten som
// ingen bevisat går att öppna vore att gissa åt spelaren.
//
// Alltså en väg som inte hänger på den luckan alls: SMYG INTILL HENNE, så
// lämnar hon över allt hon bär. Öppnas den inbyggda luckan också för någon,
// är det en bonus — inte förutsättningen.
//
// Gesten är MEDVETET densamma som framstegsrapportens (smyga intill en tämjd
// katt). Den är beprövad på riktig Xbox, till skillnad från
// playerInteractWithEntity, som i den simulerade spelaren aldrig löste ut.
// Bara när det finns något att lämna över säger hon till — annars vore varje
// smygsteg förbi katten ett meddelande.
const lamnaTyst = new Map();             // spelar-id -> tick då nästa överlämning tillåts

function lamnaOver(pl, c) {
  const box = c.getComponent("minecraft:inventory")?.container;
  const inv = pl.getComponent("minecraft:inventory")?.container;
  if (!box || !inv) return 0;
  let n = 0;
  for (let i = 0; i < box.size; i++) {
    const it = box.getItem(i);
    if (!it) continue;
    if (inv.emptySlotsCount === 0) break;   // dina egna fickor fulla: resten stannar hos henne
    inv.addItem(it);
    box.setItem(i, undefined);
    n += it.amount;
  }
  return n;
}

// testkrok: /scriptevent mjau:test_vakuum lägger en tråd vid en ryggsäckskatt
// och rapporterar om den hamnat i väskan (röktestet — hela kedjan grupp ->
// container -> mognadstid -> upplockning i ett svep). Samma mönster som
// mjau:test_fest och mjau:test_grind.
try {
  system.afterEvents.scriptEventReceive.subscribe(ev => {
    if (ev.id !== "mjau:test_vakuum") return;
    try {
      const d = world.getDimension("overworld");
      const c = d.getEntities({ families: ["mjaukatt"] })
        .find(k => { try { return (k.getProperty("mjau:ryggsack") ?? 0) > 0; } catch { return false; } });
      if (!c) { console.warn("[mjau] VAKUUM-TEST FEL: ingen ryggsackskatt att prova pa"); return; }
      if (!c.getComponent("minecraft:inventory")?.container) {
        console.warn("[mjau] VAKUUM-TEST FEL: ryggsackskatten har inget lastrum"); return;
      }
      const katt_id = c.id;
      d.spawnItem(new ItemStack("minecraft:string", 1), c.location);
      // Katten letas upp PÅ NYTT efter väntan i stället för att återanvända
      // handtaget: första försöket dog i "cannot read property 'size' of
      // undefined", vilket såg ut som en trasig container men var en katt som
      // hunnit dö i testvärlden. Fel ska säga vilket fel det är.
      system.runTimeout(() => {
        try {
          const k = d.getEntities({ families: ["mjaukatt"] }).find(x => x.id === katt_id);
          if (!k) { console.warn("[mjau] VAKUUM-TEST FEL: katten forsvann under testet"); return; }
          const box = k.getComponent("minecraft:inventory")?.container;
          if (!box) { console.warn("[mjau] VAKUUM-TEST FEL: lastrummet borta"); return; }
          let n = 0;
          for (let i = 0; i < box.size; i++)
            if (box.getItem(i)?.typeId === "minecraft:string") n++;
          // OK-raden går via console.log, inte console.warn: warn hamnar i
          // ContentLog, och testet räknar varje rad där som ett innehållsfel —
          // ett grönt delprov ska inte färga hela körningen röd. FEL-raderna
          // ska däremot ligga kvar i ContentLog.
          if (n > 0) console.log("[mjau] VAKUUM-TEST OK: traden ligger i vaskan");
          else console.warn("[mjau] VAKUUM-TEST FEL: traden ligger kvar pa marken");
        } catch (e) { console.warn("[mjau] VAKUUM-TEST FEL: " + e); }
      }, 100);
    } catch (e) { console.warn("[mjau] VAKUUM-TEST FEL: " + e); }
  });
} catch { }

// ---------------------------------------------------------------------------
// KATTENS VARNING: hon hör det du inte hör. En tämjd katt intill dig reser
// ragg när något fientligt närmar sig, och du hinner vända dig om.
//
// RINGEN 8-16 block är hela poängen: står monstret redan framför dig är
// varningen brus, och en gruvgång full av mobs skulle annars göra henne till
// en brandlarmsklocka. Hon varnar för det som är PÅ VÄG, en gång per kvart
// minut. (Creepers behöver hon inte varna för — de flyr redan från katter.)
const varningTyst = new Map();           // spelar-id -> tick då nästa varning tillåts
const VARNING_PAUS = 300;                // 15 s

system.runInterval(() => {
  const d = world.getDimension("overworld");
  let cats;
  try { cats = d.getEntities({ families: ["mjaukatt"] }); } catch { return; }
  const tamda = cats.filter(tamKatt);
  if (!tamda.length) return;
  for (const pl of world.getAllPlayers()) {
    if (!pl) continue;
    try {
      if ((varningTyst.get(pl.id) || 0) > system.currentTick) continue;
      const L = pl.location;
      const vakt = tamda.find(c => Math.hypot(c.location.x - L.x, c.location.y - L.y,
                                              c.location.z - L.z) < 10);
      if (!vakt) continue;
      const fiender = d.getEntities({ families: ["monster"], location: L, maxDistance: 16 });
      const pavag = fiender.some(m => {
        const a = Math.hypot(m.location.x - L.x, m.location.y - L.y, m.location.z - L.z);
        return a >= 8;
      });
      const nara = fiender.some(m =>
        Math.hypot(m.location.x - L.x, m.location.y - L.y, m.location.z - L.z) < 8);
      if (!pavag || nara) continue;
      varningTyst.set(pl.id, system.currentTick + VARNING_PAUS);
      pl.onScreenDisplay.setActionBar({ rawtext: [{ translate: "mjau.varning" }] });
      pl.playSound("mob.cat.straymeow", { pitch: 0.7 });
      d.spawnParticle("minecraft:critical_hit_emitter", {
        x: vakt.location.x, y: vakt.location.y + 0.9, z: vakt.location.z });
    } catch { }
  }
}, 20);

// ---------------------------------------------------------------------------
// KATTUNGAR: en nyfödd kattunge ärver ett namn efter sin förälder
// ("Baby " + förälderns namn) i stället för att vara namnlös, och kommer i
// en hel kull (2-3 ungar) i stället för bara en — speltest-önskemål ("kör
// kittens!" / "det ska vara kattungar"), inspirerat av Better
// Cats-paketets idé om individuella ungar, fast här via namn/antal
// snarare än nya texturer.
const CAT_TYPES = ["mjau:misty", "mjau:hazel", "mjau:mocha", "mjau:snow",
                  "mjau:ginger", "mjau:domino"];
let spawningLitter = false;   // spärr: kullsyskonen ska bara namnges, inte multipliceras igen
world.afterEvents.entitySpawn.subscribe(ev => {
  const baby = ev.entity;
  try {
    if (!CAT_TYPES.includes(baby.typeId)) return;
    if (!baby.getComponent("minecraft:is_baby")) return;
    if (baby.nameTag) return;   // redan namngiven (t.ex. spelaren hann före)
    let parentName = null;
    for (const e of baby.dimension.getEntities({ type: baby.typeId, location: baby.location, maxDistance: 3 })) {
      if (e.id === baby.id || e.getComponent("minecraft:is_baby")) continue;   // inte en annan unge
      if (e.nameTag) { parentName = e.nameTag; break; }
    }
    if (!parentName) return;
    baby.nameTag = "Baby " + parentName;
    if (spawningLitter) return;   // det här ÄR redan ett kullsyskon
    spawningLitter = true;
    try {
      const extra = 1 + Math.floor(Math.random() * 2);   // 1-2 syskon till -> kull på 2-3
      for (let i = 0; i < extra; i++) {
        const loc = {
          x: baby.location.x + (Math.random() - 0.5) * 1.5,
          y: baby.location.y,
          z: baby.location.z + (Math.random() - 0.5) * 1.5,
        };
        const sib = baby.dimension.spawnEntity(baby.typeId, loc);
        sib.triggerEvent("minecraft:entity_born");   // samma mekanik som riktig avel (bl.a. slumpad rosett)
        sib.nameTag = "Baby " + parentName;
      }
    } finally { spawningLitter = false; }
  } catch { }
});
