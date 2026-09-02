# Purrfect Companions

Minecraft **Bedrock** add-on: six hand-made cats you can tame, ride, breed and dress up.

[CurseForge](https://www.curseforge.com/minecraft-bedrock/addons/purrfect-companions) · [MCPEDL](https://mcpedl.com/purrfect-companions/) · [purrfect.pelleops.se](https://purrfect.pelleops.se)

![Trailer](publish/purrfect-trailer.gif)
---

## The cats

| Entity | Name | Breed | Look | Scale |
|---|---|---|---|---|
| `mjau:misty` | Misty | Siberian | Grey tabby, green eyes | 1.0 |
| `mjau:hazel` | Hazel | Siberian | Brown-and-white tabby, white bib and paws | 1.0 |
| `mjau:mocha` | Mocha | Sacred Birman | White with brown points, white gloves, belly stripes, blue eyes | 0.85 |
| `mjau:snow` | Snow | Ragdoll | All white, blue eyes | 1.15 |
| `mjau:ginger` | Ginger | Norwegian Forest Cat | Warm ginger tabby, green eyes | 1.10 |
| `mjau:domino` | Domino | European Shorthair | Tuxedo — charcoal with white bib and paws | 0.95 |

Each meows in its own pitch — Mocha highest, Snow deepest.

Misty, Hazel, Mocha and Snow spawn on plains; Ginger in forests, Domino in
taiga. None of the coats are drawn by hand: `tools/make_cat_pals.py` paints
every cat from one table of colours and traits (tabby stripes, points, bib,
paws, gloves) onto its own fur sheet at **four texels per model unit** — the
body's side is 40x20 texels instead of 10x5, which is what makes real stripes,
shading and fur grain possible. The outfits stay in the 256x256 atlas; they are
separate geometries with their own render controller. Change a colour in the
table and the cat, its spawn-egg icon and the preview images follow.

## Features

- **Tame** with cod, salmon or a crafted Cat Treat → they follow you
- **Sit** on interact once tamed (empty hand)
- **Ride** when saddled: hold a saddle → interact → interact again. ~56 % faster, charged jump. The saddle is visible on their back
- **Breed** with fish → a kitten of the **same breed**, half size, which grows up
- **Gifts** — tamed cats bring presents in the morning
- **Carries for you** — a cat in a backpack has a real 15-slot hold, picks up
  what you drop or mine within 4 blocks, and hands the load over when you
  sneak up beside her
- **Live together** — cats groom each other when they stand close, and at night
  the flock gathers on cat beds and boxes and curls up in a sleeping pile
  instead of wandering off one by one. Kittens play with each other
- **Warns you** — she bristles and calls out when something hostile closes in
  from 8–16 blocks away
- **Creepers and phantoms flee** from them (they carry the `cat` family)
- They **stalk and pounce** on rabbits and chickens
- **Spawn naturally** in plains biomes
- **Spawn eggs show cat faces**, not eggs
- **Animated**: walk cycle with legs in diagonal pairs, swaying tail, head tracking, curled-up sitting pose

## The Cat Care Book

Craft it from a book and a Cat Treat. It opens a menu that explains the cats,
what they can do, every outfit and what it grants, the four suit tiers and the
weakest-piece rule, the furniture, and how many achievements you have left.

**Its contents are generated.** `build_accessories.py` writes
`scripts/bokdata.js` from the same tables the outfits themselves are built
from, so the book cannot promise a garment that does not exist or miss one that
was added. What cannot be derived — that a saddle means riding — is an optional
language key per garment; if it is missing the book shows only the generated
part. A new garment makes the book thinner, never wrong.

## Blocks

| Block | Recipe |
|---|---|
| **Cat Bed** | 3 wool + 3 leather |
| **Yarn Ball** | 8 string + 1 wool |

Cats seek both out on their own (`minecraft:behavior.move_to_block`).

## Outfits

Craftable, applied to a tamed cat, and all wearable at the same time.

| Outfit | Colours | Recipe |
|---|---|---|
| **Cat Saddle** | brown, black, light | 3 leather + 2 string (+ dye). A vanilla saddle gives brown |
| **Cat Cap** | cyan, red, green, yellow | 3 wool + 1 leather |
| **Cat Scarf** | red, blue, green, yellow, pink, purple | 4 wool |
| **Cat Backpack** | brown, green, blue | 5 leather + 2 string + dye. **Holds 15 slots**, auto-collects nearby drops, gives them back when you sneak beside her |
| **Cat Glasses** | black, gold, pink | 2 glass panes + dye or gold nugget |
| **Cat Cape** | red, blue, purple, black | 6 wool + 2 string |
| **Cat Booties** | white, black, red, yellow | 4 wool in the corners — one on each paw |
| **Cat Collar** | red, blue, green | 3 wool + 1 iron nugget (bell) |
| **Cat Bow** | pink, red, blue, yellow | 3 wool |
| **Cat Wings** | white, black, gold | 4 feathers + colour material |
| **Cat Crown** | gold, silver | 5 ingots + 1 emerald |
| **Cat Cart** | wood, red, blue | 3 planks + 2 sticks + 2 slabs. Adds a **second seat** — a friend rides along |
| **Mining Lamp** | brass, iron | 1 glowstone dust + 2 nuggets + 1 leather. **Lights up the cave** around her: the script keeps an invisible light block at her head |
| **Life Vest** | orange, yellow, blue | 4 wool + 3 leather. Conduit power: she swims fast and sees underwater |
| **Raincoat** | yellow, green | 6 wool + 1 slime ball. Keeps her dry and content: she gets hungry three times slower |

**Cat Treat** — cod + wheat, works as a taming treat.

## What the player wears

Four pieces of armour so you can look like a cat next to your cat — in four
tiers. The leather suit protects like iron (2/6/5/2); each tier above adds
protection, durability and a stronger power. You upgrade a piece by combining
it with the metal, so the suit grows with you instead of being re-crafted.

| Tier | Made from | Powers on top of the tier below |
|---|---|---|
| **Leather** | leather + wool | Night vision · resistance · speed · soft landing |
| **Iron** | + 5 iron ingots | Jump strength in the paws; strength while a tamed cat is near |
| **Diamond** | + 5 diamonds | Resistance II, speed II, and regeneration in a full suit |
| **Netherite** | + 1 netherite ingot | Fire resistance in the hood; strength always, and your cats get resistance |

A full suit is only as strong as its weakest piece — mix leather with netherite
and you get the leather bonus.

| Piece | Slot | Look |
|---|---|---|
| **Cat Hood** | head | Ears with pink insides |
| **Cat Vest** | chest | Fur with a pale chest |
| **Cat Trousers** | legs | Darker fur |
| **Cat Paws** | feet | Pale paws with pink pads |

Every piece keeps the ears and pads across all four tiers. The leather suit
is a tabby — rings round the body, arms and legs, an M on the forehead, a
face with the same almond eyes as the cats — and the metal tiers keep the fur
in their own colour and add plates on top: a brow band, a chest plate,
shoulder caps, a belt, knee guards and toe caps. The suit is drawn on its own
256x256 sheet at four texels per model unit, like the cats.

These are the pack's first **attachables** — the parts that draw on the player
body rather than on a cat. `tools/make_player_gear.py` emits the geometry,
textures, attachables, items and recipes from one table.

---

## How it is built

Almost nothing in the two packs is written by hand. Three generators emit the
JSON, the geometry and the textures from small tables at the top of each file,
so adding an outfit colour is a one-line change rather than a dozen edits kept
manually in sync.

| Script | Owns |
|---|---|
| `build_accessories.py` | Outfits: geometry, render controllers, entity properties and events, interactions, items, icons, recipes, language keys |
| `tools/plaggmaterial.py` | The outfits' textures: one shared 1024x1024 sheet at four texels per unit, one material painter per outfit (leather, knit, metal, planks, feathers, glass, glow) |
| `build_blocks.py` | Cat Bed and Yarn Ball, plus the behaviour that makes cats seek them out |
| `tools/make_cat_pals.py` | The coats: every cat's fur sheet (`<cat>_pals.png`, 512x128), painted from a per-cat table onto the UV layout read from the geometry |
| `tools/make_cat_textures.py` | The spawn-egg icons of the derived and secret breeds |
| `tools/make_player_gear.py` | The player's cat suit: geometry, textures, attachables, items, recipes |
| `tools/make_dog.py` | The guard dog: geometry, coat and spawn-egg face |
| `render_preview.py` | The preview images, with a small z-buffered renderer — no image library required |
| `make_variant.py` | Rewrites the pack into its public naming, with its own pack UUIDs |

Textures are written by a short pure-`zlib` PNG writer, so the whole toolchain
runs on a stock Python install.

## Testing

`tools/purrfect-uthallighet` proves the two things the normal chain cannot,
because it tears the world down on every run: that state survives a world
restart, and what the twelve script loops cost together with a full clowder.

The measurement pays for itself. The first run put the colony loop at 3.10 ms of
the pack's 4.30 ms — 72 % of all script cost, for a loop that mostly compares
numbers. `entity.location` is a native getter that builds a new object on every
read, and the distance helper read it six times per pair: 1 656 native calls a
second with 24 cats. Reading each position once per tick took the pack from
4.30 ms to under 2 ms.

`purrfect-test` validates the packs and then runs them for real: it boots a
Bedrock dedicated server, spawns every cat, fires every outfit event and checks
with `has_property` that the cat's state actually changed — not merely that the
command was accepted.

The static half encodes the mistakes this add-on has already made, so none of
them can come back:

- an outfit atlas whose declared size no longer matches the actual PNG, or a
  fur sheet that is not a whole multiple of the geometry's UV size
- a cat whose eyes lost their gloss or pupil, whose nose lost its pink or its
  mouth, whose body is a single flat tone, or whose points stop at the ears
- `has_equipment` filters missing the `mjau:` namespace, which silently makes an
  outfit impossible to equip
- an entity property read by a render controller but missing `client_sync`, so
  the server knows about the outfit and the client never draws it
- a translation key referenced but never defined, which shows the player the raw
  key instead of a word
- icons or textures a variant renamed but forgot to re-register
- duplicate behaviour priorities, conflicting scales, wrong saddle seat height

On top of the static half sit three live layers: a real Bedrock Dedicated
Server run (spawns, events, block placement, cart cargo via `replaceitem`),
a real network client (`bedrock-protocol`) that joins as a player and checks
the item registry, `/give`, entity streaming and property syncs — and a
**simulated player** (Mojang's GameTest framework) that tames a cat by feeding
it cod, saddles it through the ownership and held-item filters, mounts it and
steers it, measuring that the cat actually moves.

What the suite deliberately does **not** claim: whether a player can open the
built-in container window. A real client failed to open one — and failed on a
chest-carrying vanilla donkey in the same run, which is why the backpack hands
its load over on a sneak instead of relying on that window. The gesture is the
same one the progress report uses, proven on real Xbox; neither the network bot
nor a simulated player can raise `isSneaking`, so `tools/testbot/container-test.js`
reports *inconclusive* (exit 2) rather than a false failure.

`purrfect-ship` packages and uploads, refuses to run if the test is red, and
keeps a ledger so the same version can never ship twice with different
content.
