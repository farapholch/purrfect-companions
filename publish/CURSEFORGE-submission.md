# Inskickning — Purrfect Companions

**OBS: uppladdningar sker numera via CurseForge**, inte MCPEDL:s eget formulär.
MCPEDL flyttade all uppladdning och alla uppdateringar till CurseForge (från 30 april),
vilket också ger tillgång till **Author Rewards** — betalt per nedladdning.

Gå till **curseforge.com** → skapa/logga in → *Start a Project* → **Minecraft Bedrock**.
Kopiera fälten nedan. Bilderna ligger i samma mapp.

---

## Project name
`Purrfect Companions`
*(inga klassord — "Mods"/"Addon"/"Pack" är förbjudna i titeln)*

## Logo
`logo.png` (512×512) — renderad katt mot vinjett, uppfyller kravet på motiv

## Summary (en mening, engelska)
`Tame, ride and breed four hand-made cats, then dress them in eight craftable outfits.`

## Class
`Bedrock Addons`

## Main category
`Addons` — lägg till **Mobs** och **Cosmetic** som additional categories om de finns

## Övriga val
- **Allow Comments:** ja
- **Unlisted:** nej (den ska synas i sök)
- **Social Links:** valfritt — lämna tomt om ni inte har kanal

## Skapare
`Pellzor`

## Kategori
**Minecraft Bedrock → Addons** — det här är ett Bedrock Add-On
(beteendepaket + resurspaket), inte en Java-mod och inte ett texturpaket.

## Licens (CurseForge kräver ett val ur lista)
Välj en permissiv licens som matchar "free to use", t.ex. **MIT** — eller
**Custom License** och klistra in texten ur `LICENSE.txt`.
Custom ger exakt formulering; MIT är enklare och välkänd.

## Author Rewards
Anmäl projektet till **Author Rewards** i CurseForge-panelen efter att det
godkänts. Utbetalning bygger på nedladdningar; kräver att du fyller i
skatte-/utbetalningsuppgifter.

## Taggar
`cats` `mobs` `rideable` `pets` `tameable` `breeding` `armor` `cosmetics` `family friendly`

## Kort sammanfattning (visas i listningen)
> Four hand-made cats you can tame, ride, breed — and dress up in 8 craftable
> outfits, from saddles and caps to scarves, backpacks, glasses, capes, booties
> and a pull-along cart with a passenger seat.

---

## Beskrivning (Markdown — klistra in i editorn)

**Purrfect Companions** adds four distinct cats to Minecraft Bedrock — each a real cat,
modelled after breed: two Siberians, a Sacred Birman and a Ragdoll.

They are not reskins. Each has its own colouring, size, temperament and voice.

### The cats

| Cat | Breed | Look |
|---|---|---|
| **Misty** | Siberian | Grey tabby, green eyes |
| **Hazel** | Siberian | Brown-and-white tabby, white bib and paws, green eyes |
| **Mocha** | Sacred Birman | White with brown points, white gloves, faint belly stripes, blue eyes. Smallest and quickest |
| **Snow** | Ragdoll | All white, blue eyes. Largest and calmest |

Each cat meows in its own pitch — Mocha highest, Snow deepest.

### What they do

- **Tame** them with cod or salmon; they follow you and sit on command
- **Ride** them once saddled — about 55 % faster, with a charged jump like a horse
- **Breed** two of the same cat with fish → a kitten of that same breed, half size,
  which follows its parents and grows up
- **Creepers and phantoms flee** from them, just like vanilla cats
- They **stalk and pounce** on rabbits and chickens
- They **spawn naturally** in plains, or use the spawn eggs (which show cat faces,
  not eggs)

### Eight craftable outfits

All can be worn at the same time, in any combination.

| Outfit | Colours | Recipe |
|---|---|---|
| Saddle | brown, black, light | 3 leather + 2 string (+ dye) |
| Cap | cyan, red, green, yellow | 3 wool + 1 leather |
| Scarf | red, blue, green, yellow | 4 wool |
| Backpack | brown, green, blue | 5 leather + 2 string + dye |
| Glasses | black, gold, pink | 2 glass panes + dye or gold nugget |
| Cape | red, blue, purple, black | 6 wool + 2 string |
| Booties | white, black, red, yellow | 4 wool — one on each paw |
| Cart | wood, red, blue | 3 planks + 2 sticks + 2 slabs |

The **cart adds a second seat** — you ride the cat while a friend rides along
behind.

### How to use

1. Enable **both** packs (behaviour + resources) in your world
2. Find a cat, or use a spawn egg in Creative
3. Feed it fish to tame it
4. Craft an outfit and use it on your tamed cat
5. With a saddle on, interact with an empty hand to mount

### Notes

- Works on Minecraft Bedrock 1.20+
- Tested on a Bedrock Dedicated Server (1.26): packs load clean, no content errors
- No experimental toggles required

---

## Bilder att ladda upp
1. `01-katterna.png` — the four cats
2. `02-tillbehor.png` — outfits in use
3. `03-fullt-utrustad.png` — one cat wearing everything

## Fil att ladda upp
`purrfect-companions-v<VERSION>.mcaddon` — bygg med `purrfect-ship --public --no-upload`

---

## Licens (klistra in i beskrivningen)

> **Free to use.** Use it in any world or server, record videos with it, take it
> apart to learn from it. Please link to this page rather than re-uploading the
> file, and credit Pellzor if you build on it.

Fullständig text: `LICENSE.txt`

---

## Uppdatera efter publicering

CurseForge: gå till projektet → *Files* → *Upload File*. Rutinen:

```bash
# 1. gör ändringen i källan
# 2. höj version + bygg + testa:
purrfect-ship --public --bump minor --no-upload
# 3. ladda upp /tmp/purrfect-companions-v<NY>.mcaddon som ny fil på CurseForge
# 4. skicka samma ändring till Xbox:
purrfect-ship --bump patch
```

**Kritiskt: ändra ALDRIG pack-UUID:na.** Minecraft känner igen en uppdatering på
att UUID:t är detsamma och versionen är högre. Byter du UUID blir det ett nytt,
separat paket — spelares befintliga världar tappar då kopplingen till katterna.
`purrfect-ship --bump` sköter versionshöjningen i båda manifesten och beroendet.

---

## Att bestämma före publicering

- [x] **Namnen** — publika varianten använder Misty, Hazel, Mocha, Snow
- [x] **Namnrymden** — `mjau:`
- [x] **Licens/kredit** — Free to use, skapare: Pellzor
- [x] **Ingen länkförkortare** — filen laddas upp direkt till CurseForge.
