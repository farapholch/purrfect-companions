# Ej publicerat på CurseForge ännu

## 3.27.0 — The guard dog was never ours

Reported from an Xbox: the dog's head and body had come apart, and she sat in
the hotbar as a plain egg among the cats' faces.

**She was a borrowed wolf.** The pack pointed at vanilla's `geometry.wolf` and
the vanilla wolf texture, then animated the bone named `head` — but vanilla's
wolf keeps its head inside a body hierarchy we neither owned nor could read,
so the rotation put the head somewhere else entirely. Nothing in the game
complains about that. It only shows up on a screen.

**Now she is ours.** Her cubes, her coat and her spawn-egg face all come out of
`tools/make_dog.py`, the same way everything else in this pack is made — so she
can be rendered and looked at before she leaves the house, which is exactly how
the head was checked this time. Dark guard coat, pale chest and paws, amber
eyes, upright tail.

**And she has a face in the hotbar.** The client definition had no spawn egg at
all, which is why Minecraft drew its default one.

**Also in this release**
- A new static check: if a client definition animates a bone, the geometry has
  to have that bone. That is precisely the fault that broke her, and it was
  invisible to every existing test.
- The test suite no longer turns red over receipts. Deliberate informational
  output — "the vacuum found the string", "the guard dog fell" — was being
  counted as a content error, one grep exception at a time. Warnings and
  errors still fail the run.

## 3.26.0 — Two more cats, and a forest to find them in

**Ginger.** A Norwegian Forest Cat: a big warm ginger tabby, a head taller than
the others, with the deepest voice after Snow. She lives in forests.

**Domino.** A tuxedo shorthair — charcoal with a white bib and four white
paws, small and quick, the highest voice after Mocha. She lives in taiga.

Both tame, ride, breed, wear all twenty outfits and carry a backpack like
everyone else. They breed true: two ginger cats make ginger kittens.

Neither coat was drawn by hand. `tools/make_cat_textures.py` transforms a cat
that already exists — Ginger out of Misty, Domino out of Hazel — keeping the
face untouched: the two green eye tones, the pink nose, the white spot of
gloss. Change a base coat and the breeds descended from it follow along
instead of quietly drifting apart.

**Also in this release**
- "The Whole Clowder" now says *four cats trust you* rather than *all four*.
  It was always four tamed cats, and with six breeds "all" had stopped being
  true.
- The list of ordinary cats lived hard-coded in three places in the build
  script. The icon cleanup used one of them, so a new cat's spawn egg was
  deleted on every build until all three were found. There is one list now.

## 3.25.0 — The cat earns her keep

**The backpack was a picture of a backpack.** It sat on her back, it counted
towards one achievement, and it held nothing. It holds fifteen slots now — the
same hold the cart has always had.

**She fills it herself.** A cat wearing a backpack picks up what is lying
within four blocks of her: the ore you mined, the drops you could not carry,
the string and feathers she digs up on her own. She waits two seconds before
touching anything, so what you drop on purpose stays dropped, and she never
takes cod, salmon or a cat treat — that is taming food, and one of those fish
on a bed at midnight is somebody's secret.

**Sneak up beside her and she hands it over.** The whole load, into your hands,
with a count of what came out. It is the same gesture that already shows you
the quest report.

**She warns you.** A tamed cat beside you bristles and calls out when something
hostile closes in — between eight and sixteen blocks, so it is a warning and
not a bell that rings every time a zombie exists. Once every fifteen seconds at
most. Creepers she does not bother with; they already run from her.

**Also in this release**
- The Treasure Hunter award now follows the finds into the bag. She picks her
  own diggings up faster than the old check could see them lying on the ground.
- The test suite proves the new hold for real: a live Bedrock server fills it,
  and a script hook drops a piece of string beside a backpacked cat and reports
  whether it ended up in the bag.
- `purrfect-gametest` copies the main pack into the test world instead of
  testing whatever copy happened to be left there. Three green runs in a row
  had been testing old code.
