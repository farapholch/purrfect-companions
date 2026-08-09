// Den hemliga femte katten. Ingen hittar den här filen av misstag —
// och den som gör det har förtjänat hemligheten.
//
// Ritualen: lägg en LAX på en KATTBÄDD medan månen står som högst
// (midnatt, tick 17000–19000). Då kommer Midnight — kolsvart, med ögon
// av bärnsten. En Midnight inom 48 block räcker: ritualen är en
// hälsning, inte en fabrik.
import { world, system } from "@minecraft/server";

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

// ---------------------------------------------------------------------------
// UPPDRAGS-UTMÄRKELSER: titel + fanfar när milstolpar nås. Plattforms-
// achievements går inte att ge från paket — det här är vårt eget system.
// Texterna är translate-nycklar (mjau.achv.*) i språkfilerna, så familje-
// varianten blir svensk av sig själv. Per-spelare-minne i dynamic properties
// med Map-reserv om API-nivån saknar dem.
const awarded = new Map();

function hasAward(pl, id) {
  try { if (pl.getDynamicProperty("mjau_achv_" + id)) return true; } catch { }
  return awarded.get(pl.id + ":" + id) === true;
}

function give(pl, id) {
  if (hasAward(pl, id)) return;
  try { pl.setDynamicProperty("mjau_achv_" + id, true); } catch { }
  awarded.set(pl.id + ":" + id, true);
  try {
    pl.onScreenDisplay.setTitle(
      { rawtext: [{ text: "🏆 " }, { translate: "mjau.achv." + id }] },
      { subtitleText: { rawtext: [{ translate: "mjau.achv." + id + ".sub" }] },
        fadeInDuration: 10, stayDuration: 70, fadeOutDuration: 20 });
  } catch { }
  try { pl.playSound("random.levelup"); } catch { }
}

// PROGRESS-RAPPORTEN: smyg intill en tämjd katt så "berättar" den i chatten
// vilka uppdrag som är klara. Den hemliga nian visas som ??? tills den tagits.
const ACHV_ORDER = ["forsta_vannen", "befriaren", "hela_flocken", "ryttaren", "fiskarkatten",
                    "fyrvaktaren", "skattgravaren", "lados_hemlighet",
                    "ur_morkret", "alla_hemma"];
const rapportTyst = new Map();   // spelar-id -> tick då nästa rapport tillåts

function rapportera(pl) {
  const rt = [{ translate: "mjau.progress.title" }];
  let n = 0;
  for (const id of ACHV_ORDER) {
    const har = hasAward(pl, id);
    if (har) n++;
    rt.push({ text: "\n" + (har ? "§a✔ §r" : "§8◻ §7") });
    rt.push(har || id !== "ur_morkret" ? { translate: "mjau.achv." + id }
                                       : { text: "???" });
  }
  rt.push({ text: "\n§e" + n + "/" + ACHV_ORDER.length });
  try { pl.sendMessage({ rawtext: rt }); pl.playSound("mob.cat.meow"); } catch { }
}

// VAKTHUNDEN: den som fäller hunden vid Majas kula befriar henne
try {
  world.afterEvents.entityDie.subscribe(ev => {
    if (ev.deadEntity?.typeId !== "mjau:vakthund") return;
    const p = ev.deadEntity.location;
    for (const pl of world.getAllPlayers()) {
      const dx = pl.location.x - p.x, dz = pl.location.z - p.z;
      if (dx * dx + dz * dz < 24 * 24) give(pl, "befriaren");
    }
  });
} catch { }

let hundSedd = false, hundPlats = null;   // vakthunds-vakans minne

let catHavenWorld = null;   // fyrljuset på känd plats = vi är i Cat Haven

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
    }
    catch { catHavenWorld = null; }   // chunk oladdad — fråga igen nästa varv
  }
  const tamed = cats.filter(c => { try { return c.getProperty("mjau:tam") === 1; } catch { return false; } });
  // vakthunds-vakan: syns hunden en tick och är borta nästa har någon fällt den
  try {
    const hundar = d.getEntities({ type: "mjau:vakthund" });
    if (hundar.length > 0) {
      hundSedd = true; hundPlats = hundar[0].location;
    } else if (hundSedd && hundPlats) {
      hundSedd = false;
      for (const pl of world.getAllPlayers()) {
        const dx = pl.location.x - hundPlats.x, dz = pl.location.z - hundPlats.z;
        if (dx * dx + dz * dz < 32 * 32) give(pl, "befriaren");
      }
      hundPlats = null;
    }
  } catch { }

  for (const pl of world.getAllPlayers()) {
    if (tamed.length >= 1) give(pl, "forsta_vannen");
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
  [-52, -60, 66],                                              // Majas bädd i nya kulan
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
