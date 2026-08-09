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

let catHavenWorld = null;   // fyrljuset på känd plats = vi är i Cat Haven

system.runInterval(() => {
  const d = world.getDimension("overworld");
  let cats;
  try { cats = d.getEntities({ families: ["mjaukatt"] }); } catch { return; }
  if (catHavenWorld === null) {
    try { catHavenWorld = d.getBlock({ x: 0, y: -42, z: 56 })?.typeId === "minecraft:glowstone"; }
    catch { catHavenWorld = null; }   // chunk oladdad — fråga igen nästa varv
  }
  const tamed = cats.filter(c => { try { return c.getProperty("mjau:tam") === 1; } catch { return false; } });

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
  }
}, 40);
