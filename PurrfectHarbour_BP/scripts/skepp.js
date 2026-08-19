import { world, system } from "@minecraft/server";

// ---------------------------------------------------------------------------
// SPJUTJAKTARENS HEMVÄNDNING. Stjärnhamnen svävar i tomrum: flyger man rakt
// ut finns ingen mark att landa på och ingen väg tillbaka. Skeppet hålls
// därför i koppel — en varning vid 60 block från stationen, och vid 85 (eller
// under y=-110) sätts det tillbaka på landningsplattan utanför hangaren.
//
// Kontrollen bryr sig inte om VARFÖR skeppet hamnade utanför, bara att det
// gjorde det, så den räddar lika bra ett barn som flög fel som ett skepp
// någon knuffat. Ryttaren följer med i teleporten.
// HÖJDRODRET. Mätning med simulerad spelare: input_ground_controlled styr
// BARA i sidled — skeppet flög 12,8 block på 0,75 s men rörde sig 0,00 block
// i höjd. Ett skepp som varken stiger eller sjunker är en hiss utan knappar,
// så höjden läggs på här i stället.
//
// Styrningen är HOPPA = upp, SMYGA = ner. Första försöket lät nosens vinkel
// styra, men en ryttares blickriktning gick inte att läsa alls i testet
// (pitch=0 oavsett setRotation och lookAtLocation) — en kontroll som inte går
// att mäta går heller inte att lova att den fungerar.
//
// Farten begränsas till ±0.6 block/tick: applyImpulse ADDERAR, så utan tak
// hade två sekunders hopp skickat skeppet ut i rymden. Uppmätt: impuls 1.0
// lyfter skeppet 10 block, så 0.10 är ungefär ett block per knapptryck.
system.runInterval(() => {
  const d = world.getDimension("overworld");
  let skepp;
  try { skepp = d.getEntities({ families: ["spjutjaktare"] }); } catch { return; }
  for (const s of skepp) try {
    let ryttare = [];
    try { ryttare = s.getComponent("minecraft:rideable")?.getRiders() ?? []; } catch { continue; }
    let upp = false, ner = false;
    if (ryttare.length) {
      try { upp = !!ryttare[0].isJumping; ner = !!ryttare[0].isSneaking; } catch { }
    }
    let vy = 0;
    try { vy = s.getVelocity().y; } catch { }
    if (upp !== ner) {
      if (upp && vy > 0.6) continue;
      if (ner && vy < -0.6) continue;
      try { s.applyImpulse({ x: 0, y: upp ? 0.10 : -0.10, z: 0 }); } catch { }
      continue;
    }
    // BROMSEN. Spelrapport: "man bara fortsätter flyga oändligt". Skeppet har
    // INGEN minecraft:physics — alltså varken tyngdkraft eller friktion — och
    // koden gjorde tidigare ingenting alls när ingen knapp hölls. Farten satt
    // därför kvar för evigt: släppte man hoppknappen mitt i en stigning
    // fortsatte skeppet uppåt tills världstaket tog emot.
    //
    // Nu bromsas den lodräta farten mot noll när ingen styr. Motimpulsen är
    // en TREDJEDEL av farten per varv (var 2:a tick), så skeppet glider ut
    // mjukt på ungefär en sekund i stället för att tvärnita — en tvärnit i
    // luften läser som att spelet hängt sig.
    //
    // Bromsen gäller ÄVEN utan ryttare, till skillnad från styrningen: ett
    // skepp som knuffats i väg ska också stanna, och det är den varianten
    // speltestet kan mäta (simulerade spelare syns inte härifrån).
    if (Math.abs(vy) > 0.02) {
      try { s.applyImpulse({ x: 0, y: -vy * 0.34, z: 0 }); } catch { }
    }
  } catch { }
}, 2);

// INGEN KATT, INGEN FLYGNING. Stjärnhamnen är en kattstation, och skeppen
// ska inte gå att köra ensam. Kravet är inte ett osynligt villkor utan en
// STOL: kliver du i utan katt letar skeppet upp en TAM katt inom 10 block och
// sätter den i navigatörsstolen. Finns ingen sådan får du två sekunder på
// dig, sedan står du på plattan igen.
//
// Kontrollen utgår från SPELAREN, inte från skeppet: vägen via skeppets
// getRiders() gav en åkande vars typeId inte matchade "minecraft:player".
//
// EJ TÄCKT AV TESTERNA, och det går inte att åtgärda härifrån: en simulerad
// spelare syns som `undefined` i world.getAllPlayers() sett från ett vanligt
// skriptpaket (samma sak som fick Aurora-loopen att krascha). Speltestet kan
// alltså aldrig bevisa varken utkastningen eller att katten sätter sig — bara
// att stolarna finns och att addRider fungerar. Resten måste provas på konsol.
const SKEPP_ID = "mjau:spjutjaktare";
const KATTLOS = new Map();          // spelarnamn -> antal varv utan katt

system.runInterval(() => {
  const d = world.getDimension("overworld");
  let spelare;
  try { spelare = world.getAllPlayers(); } catch { return; }
  for (const pl of spelare) try {
    if (!pl) continue;
    let fordon;
    try { fordon = pl.getComponent("minecraft:riding")?.entityRidingOn; } catch { continue; }
    if (!fordon || fordon.typeId !== SKEPP_ID) { KATTLOS.delete(pl.name); continue; }

    // Sitter det redan en katt i skeppet? Frågan ställs från kattens håll:
    // katten vet vad den åker på.
    let narliggande = [];
    try {
      narliggande = d.getEntities({ families: ["mjaukatt"], location: fordon.location,
                                    maxDistance: 12 });
    } catch { }
    const ombord = narliggande.some(c => {
      try { return c.getComponent("minecraft:riding")?.entityRidingOn?.id === fordon.id; }
      catch { return false; }
    });
    if (ombord) { KATTLOS.delete(pl.name); continue; }

    const tam = narliggande.find(c => {
      try { return c.getProperty("mjau:tam") === 1; } catch { return false; }
    });
    if (tam) {
      try {
        fordon.getComponent("minecraft:rideable")?.addRider(tam);
        KATTLOS.delete(pl.name);
        continue;
      } catch { }
    }

    // Egen räknare: varvet körs var 5:e tick, så 8 varv = 2 sekunder. Nåden
    // finns för att katten ska hinna ifatt innan man kastas av.
    const varv = (KATTLOS.get(pl.name) ?? 0) + 1;
    KATTLOS.set(pl.name, varv);
    if (varv === 1) {
      try { pl.onScreenDisplay.setActionBar({ translate: "mjau.skepp.behovkatt" }); } catch { }
    } else if (varv >= 8) {
      try { fordon.getComponent("minecraft:rideable")?.ejectRiders(); } catch { }
      try { pl.onScreenDisplay.setActionBar({ translate: "mjau.skepp.utankatt" }); } catch { }
      try { d.playSound("note.bass", fordon.location); } catch { }
      KATTLOS.delete(pl.name);
    }
  } catch { }
}, 5);

const STATION = { x: 20, z: 0 };      // mitt på stationen
const PLATTAN = { x: 65, y: -60, z: 0 };
const VARNA = 110, HEM = 150, BOTTEN = -110;   // 45 block/2,5 s uppmätt
// TAKET saknades helt: kopplet fångade sidledes och nedåt, men den som flög
// RAKT UPP möttes aldrig av något. Stationen ligger kring y=-60, så 20 är
// åttio block ovanför plattan (varning) och 60 är hundratjugo (hemhämtning) —
// samma proportion som det vågräta kopplet.
const TAKVARNA = 20, TAK = 60;
// => ~8 s från stationen till varningen. Kortare koppel blev en tvärnit.

system.runInterval(() => {
  const d = world.getDimension("overworld");
  let skepp;
  try { skepp = d.getEntities({ families: ["spjutjaktare"] }); } catch { return; }
  for (const s of skepp) try {
    let L;
    try { L = s.location; } catch { continue; }
    const dx = L.x - STATION.x, dz = L.z - STATION.z;
    const avstand = Math.sqrt(dx * dx + dz * dz);
    if (avstand < VARNA && L.y > BOTTEN && L.y < TAKVARNA) continue;

    let ryttare = [];
    try { ryttare = s.getComponent("minecraft:rideable")?.getRiders() ?? []; } catch { }
    if (avstand >= HEM || L.y <= BOTTEN || L.y >= TAK) {
      try { s.teleport(PLATTAN); } catch { }
      // NOLLA FARTEN vid hemhämtningen. Utan den behåller skeppet sin
      // hastighet genom teleporten och skjuter i väg igen direkt — det ser ut
      // som att kopplet inte fungerar alls.
      try { s.clearVelocity(); } catch { }
      for (const r of ryttare) {
        try { r.onScreenDisplay.setActionBar({ translate: "mjau.skepp.hem" }); } catch { }
      }
      try { d.playSound("beacon.deactivate", PLATTAN); } catch { }
    } else {
      for (const r of ryttare) {
        try { r.onScreenDisplay.setActionBar({ translate: "mjau.skepp.varning" }); } catch { }
      }
    }
  } catch { }
}, 20);
