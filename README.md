# Purrfect Companions

_Av **Pellzor**. Fri att använda — se `publish/LICENSE.txt`._

Minecraft **Bedrock**-add-on med fyra egna katter. Körs på Xbox via Mod Mate.

## Katterna

| Entitet | Namn | Ras | Utseende | Storlek |
|---|---|---|---|---|
| `mjau:misty` | Misty | Sibirisk | grå tabby, gröna ögon | 1.0 |
| `mjau:hazel` | Hazel | Sibirisk | brun-vit tabby, vit bringa/tassar, gröna ögon | 1.0 |
| `mjau:mocha` | Mocha | Helig birma | vit med bruna points, vita handskar, magränder, blå ögon | 0.85 |
| `mjau:snow` | Snow | Ragdoll | helvit, blå ögon | 1.15 |

## Funktioner

- **Tämjs** med torsk/lax → följer dig
- **Sitter** på tryck när tam (tom hand)
- **Rids** när sadlad: sadel i handen → tryck → tryck igen. +56 % fart, laddat hopp. **Sadeln syns på ryggen.**
### Tillbehör (craftas, sätts på tam katt — alla kan bäras samtidigt)

| Plagg | Färger | Recept |
|---|---|---|
| **Kattsadel** | brun, svart, ljus | 3 läder + 2 snöre (+ färg). Vanlig hästsadel ger brun |
| **Kattkeps** | cyan, röd, grön, gul | 3 ull i färgen + 1 läder |
| **Katthalsduk** | röd, blå, grön, gul | 4 ull i färgen |
| **Kattryggsäck** | brun, grön, blå | 5 läder + 2 snöre + färg |
| **Kattglasögon** | svarta, guld, rosa | 2 glasrutor + färg/guldklimp |
| **Kattmantel** | röd, blå, lila, svart | 6 ull i färgen + 2 snöre |
| **Kattossor** | vita, svarta, röda, gula | 4 ull i färgen (i hörnen) — en på varje tass |
| **Cat Collar** | röd, blå, grön | 3 ull + 1 järnklimp (bjällra) |
| **Cat Bow** | rosa, röd, blå, gul | 3 ull i färgen |
| **Cat Wings** | vit, svart, guld | 4 fjädrar + färgmaterial |
| **Cat Crown** | guld, silver | 5 tackor + 1 smaragd |
| **Kattvagn** | trä, röd, blå | 3 plankor + 2 pinnar + 2 träplattor. Ger en **andra sittplats** — kompis åker i vagnen |

**Lägg till fler plagg:** redigera `ACC` överst i `build_accessories.py` och kör `python3 build_accessories.py`. Skriptet genererar geometri, textur, render controller, entity-property, event, interaktion, föremål, ikon, recept och språksträng. Kör sedan `purrfect-test`.
- **Parar sig** med fisk → kattunge av **samma ras**, halva storleken, växer upp
- **Jamar** med eget tonläge per katt (vanilla-ljud, inga egna .ogg)
- **Creepers & phantoms flyr** (familjen `cat`)
- **Jagar** kaniner och höns (smyg + språng)
- **Spawnar naturligt** i slättbiom
- **Spawn-ikoner är kattansikten**, inte ägg

## Två varianter

Källan är den **publika** versionen (generiska namn: Misty, Hazel, Mocha, Snow).
Den **privata** versionen (familjens riktiga kattnamn) genereras vid paketering av
`make_variant.py` — privata namn hamnar alltså aldrig i källkoden eller på GitHub.

| Variant | Namn | Pack-namn | UUID |
|---|---|---|---|
| `private` (standard) | (privat namn), (privat namn), (privat namn), (privat namn) | Purrfect Companions (familj) | egna |
| `public` | Misty, Hazel, Mocha, Snow | Purrfect Companions | källans |

**Varianterna har olika pack-UUID:n med flit** — annars skriver de över varandra i
Minecrafts paketlista. Båda kan installeras samtidigt.

## Arbetsflöde

```bash
purrfect-test --quick             # snabb validering (~2 s)
purrfect-test                     # + live-test i Bedrock-server (~1 min)
purrfect-ship                     # privat variant → Mod Mate (till Xbox)
purrfect-ship --public            # publik variant
purrfect-ship --bump minor        # höj version först (major|minor|patch)
purrfect-ship --public --no-upload  # bygg publik för CurseForge utan att skicka
python3 render_preview.py     # marknadsföringsbilder → publish/
```

Filnamnet härleds ur paketnamnet i manifestet: `purrfect-companions-v<VER>.mcaddon`
(publik) och `...-familj.mcaddon` (privat) — byter man paketnamn följer filnamnet med.

`purrfect-ship` **vägrar skicka om testet failar**, och verifierar checksumman efter uppladdning.

## Struktur

```
/opt/purrfect-companions/
├── PurrfectCompanions_BP/          beteendepaket (entiteter, loot, spawn-regler, events)
│   ├── entities/         en fil per katt
│   ├── spawn_rules/      naturlig spawn
│   └── loot_tables/
├── PurrfectCompanions_RP/          resurspaket (modell, texturer, ljud, ikoner)
│   ├── entity/           client_entity per katt
│   ├── models/entity/    katt.geo.json (delad modell)
│   ├── textures/entity/  64×64 per katt
│   ├── textures/items/   16×16 spawn-ikoner
│   └── sounds.json       mappning till vanilla kattljud
├── .modmate-code         Mod Mate transfer-kod (600)
└── README.md
```

Testservern (Bedrock Dedicated Server) ligger i `/opt/bds/server` och startas **bara** under test.

## Animationer

`PurrfectCompanions_RP/animations/katt.animation.json` + `animation_controllers/`.
Fyra animationer: **walk** (diagonala benpar via Molang `query.modified_distance_moved`),
**tail** (svaj på `query.life_time`), **look** (huvudet följer med `query.target_*_rotation`)
och **sit** (hopkurad pose). Controllern växlar mellan standing / walking / sitting.

Kopplas in av `build_accessories.py` (`description.animations` + `scripts.animate`) —
lägg till där, inte för hand, annars försvinner det vid nästa bygge.

## Fallgropar (dyrköpta)

1. **Unika `priority` på alla behaviors** — kolla även i `component_groups`.
2. **`minecraft:scale` får inte ligga i både bas och grupp.**
3. **Sadelns `seats.position` måste följa modellen** — kroppens ovansida y9 → `0.562`.
4. **UV-layouten måste ritas om när kubstorlekar ändras.**
5. **Versioner:** `header.version` + `modules[].version` i BÅDA manifesten, och BP:s `dependencies[].version` måste matcha RP:s header.
6. **`follow_owner` kräver ägare** → bara i tamed-gruppen.
7. **`sittable` + `rideable` krockar** (samma interaktion) → `sittable` i egen grupp som tas bort vid sadling.
8. **`server.properties` måste ha `level-name=Kattest`**, annars startar testservern en tom värld utan paket.
9. **Recept i 1.20+ kräver `unlock`-data** — utan den laddas receptet inte alls (fångas bara i ContentLog, inte av JSON-validering).
10. **Synlig utrustning — en geometri PER TILLBEHÖR, inte per kombination.** Att baka in tillbehör i kattmodellen ger kombinatorisk explosion (4 plagg × färger ≈ 400 modeller). Lösningen: varje plagg är en egen liten geometri (`geometry.katt.keps2` osv) + en **egen render controller** som väljer färg eller `geometry.katt.empty`. `client_entity.render_controllers` listar alla fem (kropp + 4 plagg). Resultat: **16 geometrier i stället för 400**.
11. **Bara EN component group får definiera `minecraft:rideable`.** Två grupper som båda gör det ger odefinierat beteende (vilken vinner?). Vagnens andra sittplats ligger därför i `mjau:saddled`, inte i en egen grupp. `purrfect-test` kontrollerar detta.
12. **Ett kraschande kontrollskript får inte se ut som godkänt.** Sadelhöjds-kontrollen antog att `seats` är ett objekt; med två platser blev det en lista → skriptet dog tyst med stderr dolt, och HELA strukturkontrollen hoppades över medan testet visade grönt. `purrfect-test` larmar nu explicit om kontrollen inte producerar resultat, och visar felet.
13. **Tillbehörens läge styrs av entity properties**, inte variant/mark_variant (som bara räcker till två oberoende värden). `description.properties` definierar `mjau:sadel|keps|halsduk|ryggsack` (int med range), events sätter dem med `"set_property"`, och Molang läser med `query.property('mjau:keps')`. Så är plaggen helt oberoende av varandra.
11. **Texturen är 128×128** sedan färgvarianterna tillkom. UV:er är absoluta pixelkoordinater, så befintliga regioner kunde behållas när texturen växte — men `texture_width`/`texture_height` i varje geometris `description` MÅSTE uppdateras, annars mappas allt fel.

`purrfect-test` kontrollerar 1, 2, 3, 5, 6 och 8 automatiskt.

14. **Recept kan krocka med VANILLA.** `[GGG,G G]` med guld = gyllene hjälm, `[G G,GGG]` med järn = vagn. Egna recept med samma ingredienser blir dessutom dubbletter (alla tre vingfärger hade identiskt recept). Fångas bara i ContentLog som warning — kör alltid `purrfect-test` efter nya recept.
