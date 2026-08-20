## 3.31.7 — Dress like your cat, and two new neighbours in Cat Haven

The kids asked for it: *you* should be able to wear cat gear, not just the cat.

**A four-piece cat suit.** Hood with ears and pink insides, a vest with a pale
chest, darker trousers, and paws with pink pads. Leather and wool, the same
materials the cats' own outfits are made of. It protects like iron — 2, 6, 5
and 2 — so wearing it is a real choice rather than only dress-up, and it takes
enchantments and mending like any other armour.

**Two legs, two arms, one body.** Armour pieces bulge outward a little so they
sit outside your skin — but the player's legs touch, and so did the paws, which
turned two feet into one pale block. Both pairs are slimmer now and edged with a
darker line, so the suit reads as a person wearing something rather than a
figure carved from one piece.

**The vest has arms you can see.** The first version wrapped the whole arm in
the same colour as the chest and sat flush against it, so the two grew into one
wide slab — reported from an Xbox as "you have basically no arms". The sleeves
are full length, a shade darker than the chest, and they end in a pale cuff at
the wrist — so you can tell where the body stops and the arm starts without the
suit having to be bulky about it. It sits about one and a half units wider than
a bare player, where the first attempt at making the arms visible sat at two
and a half.

**The suit comes in four tiers.** Leather, iron, diamond and netherite. You do
not re-craft it — you upgrade the piece you already wear by combining it with
the metal, so the hood you made on day one is the hood you still have in
netherite. Protection climbs from 2/6/5/2 to 4/8/7/4, and each tier adds a
stronger power: jump strength in iron paws, resistance II and speed II in
diamond, fire resistance in a netherite hood. A full suit is only as strong as
its weakest piece — mix leather with netherite and you get the leather bonus,
which is a rule a seven-year-old can hold in their head.

**The hood has a face.** Amber eyes with mirrored highlights, a pink nose and whiskers — and ears that
actually clear the helmet. Reported from an Xbox: "no eyes and no ears". Both
were true. The ears were three quarters buried inside the helmet, which is
inflated a unit larger than the head; and the face only ever existed in the
16×16 inventory icon, never on the model you wear.

**And the suit does something.** One power per piece, so each is worth wearing
on its own — the hood gives night vision, because cats see in the dark; the
vest gives resistance; the trousers give speed; and the paws give a soft
landing, so you take no fall damage. Wear all four and you get speed II and a
higher jump on top, and every cat around you purrs and heals.

Until now everything in this pack was worn by a cat. Nothing had ever been
drawn on a player, and the pack had no attachables at all — the parts that put
something on your own body. All four pieces come out of one table in
`tools/make_player_gear.py`: geometry, textures, attachables, items, recipes.

**Ginger and Domino have moved into both worlds.** Star Harbour now wakes six
cats instead of four — the ginger one drifted in with a supply run and never
left, the black-and-white one was born aboard. The logbook says so on its
first page.

**In Cat Haven they have quests of their own.** They were added to the add-on after the
world was built, so until now they only existed out in the wild. Ginger keeps
to the grove in the north-west, where the third key lies. Domino
sits by the lighthouse and watches the sea. Find them, bring cod, and there are
two more quests on the list: *The Grove Keeper* and *The Lighthouse Shadow*.
The caretaker's handbook has a new page about both of them — he wrote it after
the rest of the book, which is why it is last.

**The fighters stop now.** Reported from play: you just kept flying forever.
The ship has no physics of its own — no gravity, no drag — and the code did
nothing at all when you were not holding a button, so whatever speed you had
stayed with you until the world ran out of sky. Let go and it now glides to a
stop in about a second. **And the sky is bigger than it was.** The leash was measured from the station
alone — but the crater, the relay mast and the probe sit 90, 95 and 96 blocks
out, so the warning started nagging fifteen blocks after you arrived at the
very place the logbook sent you to. It now reaches 150 blocks, and it does not
speak at all while you are near an outpost. The void beyond still has no ground
to land on and no way back, so the net stays — but it is there to catch someone
flying away, not someone flying there.

**Also in this release**
- The trousers recipe was, letter for letter, vanilla's leather leggings. You
  would have crafted vanilla trousers and wondered where the ears went. Caught
  before shipping by the recipe check that compares every recipe against a
  snapshot of vanilla's.
- New checks for anything worn on a player: the geometry and texture have to
  exist, the declared texture size has to match the actual image, and the bones
  have to be the player skeleton's. Wrong bone names put the clothes in the
  ground, and no server test can see that.
- The pack now has a hero image with all six cats in a meadow, a shorter
  gallery gif, and an outfit picture where every cat wears something different
  and one is fully kitted out.
- Icon cleanup only deletes icons it made itself now. The old rule was "keep a
  list, delete the rest", and that list was forgotten three times — Ginger's
  spawn egg, the guard dog's face and the secret cats' icons were each deleted
  on the next build.

## 3.27.2 — Two more cats, and one who carries your loot

Everything since 3.24.0, gathered into one release.

**Ginger.** A Norwegian Forest Cat: a big warm ginger tabby, a head taller than
the others, with the deepest voice after Snow. She lives in forests.

**Domino.** A tuxedo shorthair — charcoal with a white bib and four white paws,
small and quick, the highest voice after Mocha. She lives in taiga.

Both tame, ride, breed and wear all twenty outfits like everyone else, and they
breed true: two ginger cats make ginger kittens. Neither coat was drawn by
hand. Ginger comes out of Misty and Domino out of Hazel, through a
transformation that leaves the face alone — the two green eye tones, the pink
nose, the white spot of gloss. Change a base coat and the cats descended from
it follow along instead of quietly drifting apart.

**The backpack was a picture of a backpack.** It sat on her back, it counted
towards one achievement, and it held nothing. It holds fifteen slots now — the
same hold the cart has always had.

**She fills it herself.** A cat wearing a backpack picks up what is lying within
four blocks of her: the ore you mined, the drops you could not carry, the
string and feathers she digs up on her own. She waits two seconds before
touching anything, so what you drop on purpose stays dropped, and she never
takes cod, salmon or a cat treat — that is taming food, and one of those fish
on a bed at midnight is somebody's secret.

**Sneak up and tap her to open the pack.** Fifteen slots, the same way you
open a donkey's chest — so you can pack her as easily as you empty her.

**She warns you.** A tamed cat beside you bristles and calls out when something
hostile is *coming for you* — she measures whether it is closing the distance,
between eight and sixteen blocks away, and she says it once per creature rather
than once per zombie that happens to exist. A standing zombie twelve blocks
off is not worth interrupting you for. Half a minute between warnings at most.
Creepers she does not bother with; they already run from her.

**The guard dog has been rebuilt.** Reported from an Xbox: her head and body had
come apart, and she sat in the hotbar as a plain egg among the cats' faces. She
was never ours — the pack borrowed vanilla's wolf model and then animated a
bone that vanilla keeps inside a body hierarchy we neither owned nor could
read, so her head ended up somewhere else entirely. Nothing in the game
complains about that; it only shows on a screen. She is ours now: dark guard
coat, pale chest and paws, amber eyes, upright tail — and a face in the hotbar
instead of an egg.

**Also in this release**
- The Treasure Hunter award follows the finds into the bag. She picks her own
  diggings up faster than the old check could see them lying on the ground.
- "The Whole Clowder" now says *four cats trust you* rather than *all four*. It
  was always four tamed cats, and with six breeds "all" had stopped being true.
- Every image in the pack is rendered and looked at before a release leaves the
  building. That is how the dog's head was checked this time, and how two
  mistakes in her face were caught before you saw them.
- A release can no longer ship a client definition that animates a bone the
  model does not have. That is precisely what broke the dog, and it was
  invisible to every test we had.
- Midnight, Aurora, Nova and the ghost cat have faces in the creative menu.
  All four had no spawn egg icon at all, so the game drew four plain black
  eggs among the cats. Their rituals are exactly as secret as before.
- Domino's icon was a black square. Dark coats are now lifted to something
  you can actually see — in the icon only, never on the cat.

## 3.24.0 — Blades of light, icons you can tell apart, and an add-on that stands on its own

**Energy blades.** A hilt that wakes into a humming bar of light, in four
colours — blue, green, red and violet. Two dyes and an iron ingot make one.
It hits as hard as netherite, holds 800 swings, takes enchantments, and
throws sparks in its own colour while you carry it.

**A cat that fights beside you.** Give a blade to a tamed cat and she wears
it. Her attack goes from 3 to 7, and — this is the new part — she actually
uses it: she strikes back at whatever hurts you, and joins in on whatever
you swing at. Saddle her and she goes back to being your mount, because you
should always be the one steering.

**The star cloak.** Dark weave, a drift of stars across the back. It is a
cape, and it does what capes here do.

**Every outfit finally looks like itself.** The icons were the weak point in
two ways. Only four accessory types had their own shape — the other sixteen
were drawn as the same coloured rectangle. And then the redrawn ones shipped
broken: written a byte short per pixel, so the game refused them and showed
the missing-texture pattern instead. Both are fixed, and every image in the
pack is now decoded and verified before a release can leave the building. Saddle, cap, scarf, backpack, collar,
bow, wings, horn, armor, hats, coat, crown and blade now each have their own
silhouette. You can tell what a thing is before you notice what colour it is.

**The add-on plays on its own now.** It was built alongside Cat Haven, and it
showed: ten of the sixteen quests were tied to that world's landmarks, and
the Cat Master celebration needed all sixteen — so it was unreachable for
anyone playing in their own world. The celebration now asks only for the six
that work anywhere: your first friend, all four cats, riding, fishing,
digging up treasure, and the one at midnight. Play in Cat Haven and you still
see the full list.

**And it tells you where to start.** Tame your first cat and she lets you know
what the two of you can do — the saddle, the cart, the twenty outfits, and
that sneaking beside a cat gets you a progress report. She does not tell you
everything.

**Also in this release**
- The add-on no longer reaches into worlds it was not built for. Two secrets
  used to trigger on bare coordinates and could fire in your own world by
  accident; both now check where they are first.
- The spear fighter that briefly lived here has moved out to Star Harbour,
  where it belongs. This is a cat add-on.
- Cats spawn on plains in daylight, so every quest that counts can be
  finished in a fresh survival world.

## 3.12.2 — The gates became walls

The quest gates were fences, and a fence is two blocks of stone wearing a
disguise — the kids simply jumped them and walked into the parkour course
before finding a single key. They are proper stone brick walls now, five
blocks tall, and they come down the same way: finish the quest on the sign.

## 3.12.0 — Superpowers, kittens, cuter cats, and a world that opens as you play

Everything from a dozen smaller releases, gathered into one.

**Every outfit does something now.** All eighteen. The cape makes a ridden
cat faster and higher-jumping, and leaves a trail of stars behind it in the
air. Wings cancel fall damage and glitter as you drop. The crown glows
through walls. The doctor's coat heals, with little hearts to prove it. The
unicorn horn sparkles. Fourteen more besides — dress your cat for the job.

**Kittens come in litters** of two or three, each named after its parent,
each inheriting a little of it, and now and then one is born already wearing
a collar.

**The cats got cuter.** Bigger ears, a glint in the eye, pink paw pads.

**The Cat Parkour.** A lantern-lit wooden course you ride a cat through —
up the ramp, then platform to platform, ending in wide gaps and single-block
landings. Golden wings in a chest at the finish. It was too easy at first;
it is not any more.

**The world opens as you play.** Paths start walled off, each with a sign
naming the quest that opens it. Light the lighthouse and the meadow road
opens. Find the three keys and the parkour path opens. Beat the parkour and
the lake lifts its grate. The story finally has an order.

**Rewards on nearly every quest** — experience and items, not just a line of
text.

**A deep lake** far east with a tunnel at the bottom and a trident in the
dark, **an attic** in the old house holding a full set of netherite for you
and for your cat, **a trading post** that takes what a backpack cat digs up,
and **a forest all the way around the map** with rabbits, foxes and sheep
among the trees.

**And a world template**, so you can start a fresh Cat Haven whenever you
like without importing anything again.

## 3.12.1 — The rider on the head, for the last time

A saddled cat no longer plays its sitting or sleeping pose. Those poses
tilt the body back sixteen degrees and drop it — the sleeping one flattens
the cat completely — while the rider stays on a fixed seat point. The cat
sank away, the head swung up, and you ended up perched on it.

It only happened **sometimes** because the cat had to be nearly stationary
and still carrying its sitting flag from before it was saddled. Mount a cat
that has been walking around and you would never see it.

2.6.2 fixed this same symptom once before, but that was a different cause
(the seat's forward axis pointed the wrong way). This time the seat was
innocent: a simulated rider measured the seat height on all three cat sizes,
and Bedrock scales it correctly with the cat — 0.078, 0.162 and 0.246 blocks
on a 0.85, 1.0 and 1.15 scale cat, proportional to the last decimal. That
measurement now runs on every build, so if the seat ever drifts apart
between the small, normal and large cats, the tests will say so.

## 3.0.0 — The big one: night arrival, real achievements, and THE floor fix

A major release that gathers everything since 2.8.1 — thank you for the
patience between updates, this is why they come less often now.

**You arrive at night, in the rain.** The valley greets its new
caretaker dark and dripping. Light the lanterns, meet the cats at dawn.

**The forest got scarier.** Podzol and dead bushes under a thicker
canopy, more cobwebs, bats flapping between the trunks — and the things
that glow in there are not all lanterns.

**Nine in-game achievements** now celebrate your progress through the
quests, from your first friend to the very last secret. And speaking of
achievements: **this add-on is Xbox-achievement friendly** — it uses
only stable APIs, no experimental toggles required, so your worlds keep
earning achievements as long as cheats stay off.

**The "sunken furniture" bug is dead — for real this time.** It was
never the furniture: the shelter had an entire extra floor layer hiding
in plain sight, one block above the real one. It is gone, the room is a
block taller, and the chandeliers finally hang visible from the ridge.

**Also in this release:**
- Riding a cat now seats you in the saddle, and the cat no longer
  steers on its own
- Cat armor gives real protection worth crafting
- No more "Unknown" names in the inventory
- Animations settle cleanly when a cat stops (no more leg flutter)
- The lighthouse has a proper entrance, a safe ladder, and headroom at
  the top
- Something happens at midnight. That is all we will say.

## 2.8.1 — A river to cross, a roof worth having

The dark forest moved farther west — and now a river runs the length
of the valley between you and it, with a single plank bridge as the
only way across. The fur tufts know the way; a soul lantern marks the
crossing. The shelter finally looks like a home: a real pitched spruce
roof, lanterns hung from the ridge beam, and a cat's face — ears, eyes
and a pink nose — built into each gable in wool.

Under the hood, the stubborn "furniture sunk in pits" rendering bug is
finally, definitively fixed (furniture is placed the way that provably
renders right), and the lighthouse lamp moved up a block so nobody
bumps their head stepping onto the platform.

## 2.8.0 — The dark forest, and the ghosts of the old cats

The search for the missing cat got teeth. She is no longer resting
somewhere pleasant: the white fur tufts now lead west, into a dark
oak forest where the canopy swallows the daylight, cobwebs catch at
your sleeves, and soul lanterns burn cold and blue along the trail.

Three GHOST CATS drift between the trunks — pale, half-transparent,
nameless. The handbook says not to fear them: they are the old cats
of the shelter, and they only miss their caretaker. Whether one of
them can still be won over with a cod... we leave to you.

And: ACHIEVEMENTS. Nine of them, with a proper on-screen fanfare —
from First Friend (your first tamed cat) to Lighthouse Keeper, What
the Boxes Hid, and one we will not name here. They are per-player,
they persist, and six of them work in any world you bring the cats to.

Also in this release: the world tells you where to start (a sign by
the spawn, a sign on the chest), sign lines no longer clip, and the
world name carries its version so re-imports stay tidy. Every release
is now playtested by a simulated player who completes all the quests
before anything ships.

## 2.7.2 — A fourth task, and a proper face

- **Cat Haven grew a fourth task.** The old caretaker never trusted
  banks - what he saved, the cats buried. A cat wearing a backpack
  remembers where. The handbook explains; the digging is up to you.
- **The shelter keeps one more secret.** The handbook puts it plainly:
  mind the boxes. Some hide more than dust.
- **The pack finally has a face:** all four cats look out of the new
  pack icon instead of a lone grey render.
- The world builder learned two hard lessons about world bottoms and
  lock inheritance; both now have tests standing guard.

## 2.7.1 — The furniture rises from the floor

Found within hours by an Xbox playtest of Cat Haven: every piece of
furniture — beds, bowls, the scratching post, the cardboard box, even
the fish pond — appeared to sink into a pit in the floor. A custom
block that does not fill its whole cube must not claim to; the game
believes the claim and culls the faces of every neighbouring block.
The cat door learned this exact lesson in 2.6.1 — now it covers every
sparse model, and a test makes sure the lesson stays learned.

Cat Haven also gained proper double doors on the shelter and a
lighthouse entrance at ground level. The climb is still yours.

## 2.7.0 — The old cats tell of a fifth

These notes will not explain this update. The caretaker's handbook in
Cat Haven says a little more, on its last page — and the rest is
between you and the cats, at midnight.

(For the record: whatever this is, it is machine-tested like
everything else. We are just not going to tell you what the test
proves.)

## Cat Haven — a world to move into

Not a version of the add-on, but a new way to start it: a ready-made
world. You arrive as the new caretaker of a cat shelter. A handbook in
the starter chest sets three tasks — find the four cats hiding in the
hills, let a saddled cat fish in the pond, and ride to the top of the
lighthouse for a reward. Beds with the cats' names, a stocked chest, a
gravel road and six oak trees are already in place.

One file, one tap: the `.mcworld` carries both packs inside it, so
nothing needs enabling by hand. The world is generated by script and
machine-verified like everything else — the build boots a real server
and proves the chest, the pond, the lighthouse light and all four cats
are where the handbook says they are.

## 2.6.3 — No cat is "Unknown"

Two safety nets for the name that shows above a cat and in its
inventory screen:

- Cats that were wearing armor in a world saved before 2.6.2 referenced
  an armor definition that 2.6.2 renamed away, which could make the
  game treat them as an unknown creature. The old definition is back,
  and swapping armor migrates the cat cleanly to the new tiers.
- Entity names are now declared in both forms Bedrock looks them up —
  with and without the add-on namespace — so UI screens that use the
  short form find the right name instead of "Unknown".

Also: **putting armor on a cat now heals it to its new maximum.** It
turned out the extra hearts arrived empty — the armor raised the
ceiling but not the health itself. The test suite now proves it by
dealing 45 damage to a netherite-armored cat and requiring it to
survive; an unarmored cat would not.

## 2.6.2 — The cat truly obeys, the rider truly sits

- **Ridden cats no longer wander on their own.** The free-will urges —
  strolling, following a fish, seeking out furniture — were meant to
  switch off when the cat is tacked up, but never actually did; every so
  often the stroll urge fired mid-ride and tugged the cat a few blocks
  sideways. Saddling or hitching now genuinely switches free will off.
- **The rider finally sits on the cat's back, not its head.** The seat
  coordinate's forward axis points the opposite way from what 2.6.1
  assumed, so that fix moved the rider *onto* the head. A simulated
  rider now measures where it actually sits, in the cat's own frame,
  every test run — no more guessing at signs.
- **Better armor is worth more.** Cat Armor now scales with the
  material: iron 20 hearts, gold 22, diamond 25, netherite 30 — up from
  a flat 15. Swapping armor applies the new tier cleanly.

## 2.6.1 — Riding smoothed out, and a door that opens

Six fixes, all found by playing 2.6.0:

- **You can walk through the Cat Door now.** It was defined as a solid,
  opaque block, so it looked broken next to other blocks and neither cat
  nor player could pass. It is now a thin frame with no collision — step
  right through.
- **No more fall damage while riding.** The mount takes the fall in
  Minecraft, so a jump off a hill could kill the cat under you. Ridden
  cats now shrug off falls entirely.
- **The rider sits behind the neck,** not on the cat's head.
- **Ridden cats stay on task.** A saddled cat would still lunge at every
  chicken it passed. Hunting now switches off the moment someone sits up,
  and returns when the tack comes off.
- **Cats no longer nap the day away.** The nap urge from 2.6.0 was far too
  strong — cats lay down the moment they spawned and just stayed there.
  The constant napping is gone; sitting cats still purr.
- **Animations blend.** Switching between standing, walking, sitting and
  sleeping used to snap instantly; poses now ease into each other.

## 2.6.0 — Moods, naps, purring, fishing and treasure

The cats got an inner life:

- **Moods.** A happy cat walks with its tail high; a hungry one lets it droop.
  Feed a Cat Treat to cheer them up — hunger creeps back over time.
- **Naps.** Cats curl up flat and doze off, purring, and wake the moment they
  move.
- **Purring.** A sitting cat purrs, with the occasional heart.
- **Cat fishing.** A saddled or harnessed cat in water catches cod for you.
- **Treasure hunting.** Cats wearing a backpack dig up string and feathers —
  and once in a long while, a diamond.
- **Kittens** are sometimes born wearing a little bow.

New furniture: **Cardboard Box** (cats love boxes), **Fish Pond**, **Cat Door**.
New outfits: **Witch Hat**, **Santa Hat**, **Doctor Coat**, **Bat Wings**.

## 2.5.2 — Cat Armor

Four tiers — iron, gold, diamond, netherite — crafted from five of the
material, worn like horse armor with a back plate, side plates and a neck
guard. It is not just for looks: an armored cat has fifteen hearts instead
of five.

## 2.5.1 — Litter Box and Cat Tower

Two more things for the home: a **Litter Box** (planks around sand) and a
**Cat Tower** with a sisal post and a viewing platform (wool, string and
planks). Cats seek both out on their own, along with the bed, the yarn ball
and the food bowl.

## 2.5.0 — The cart you can sit in, the cat that obeys

Found by playing on Xbox, fixed and now machine-tested:

- **Cats no longer wander while ridden.** Their free-will behaviours — strolling,
  chasing, seeking out beds — switch off the moment a rider sits up, and return
  when the saddle comes off the agenda. A simulated rider now verifies the cat
  drifts 0.00 blocks with no input.
- **The Cat Cart is bigger, and you can finally sit in it.** The cart seat is now
  the first seat: interact and you sit IN the cart, steering like a sled, with
  the back seat free for a friend. A simulated player boards it and drives it
  eighteen blocks in every test run.

New things:

- **Food Bowl** — craft it from a bowl, planks and a cod; cats seek it out.
- **Unicorn Horn** — white, gold or pink, crafted around quartz, gold or
  amethyst. Combine with the wings.

## 2.4.1 — A tail that looks like a tail

The tail was a solid pillar — three blocks wide, three deep, straight up. It
is now slim and curves up and back the way a content cat carries it, and it
still sways. Every breed keeps its own tail colour.

Taming is also now visible to the server side, which tightens our automated
tests.

## 2.4.0 — Names, storage and a proper jump

**Item names were showing as raw ids.** A pack has to declare its languages in
`texts/languages.json`, and ours did not exist — so Minecraft ignored the
translations entirely and fell back to internal identifiers. Every name, and
every button prompt, now reads the way it was written.

- **The Cat Cart carries things.** Fifteen slots, donkey style. Sneak and
  interact to open it.
- **Cats jump higher.** Hold the jump button to charge it.

## 2.3.4 — Steering

Saddled cats carried two control systems at once: the player's own stick input,
and an AI goal that steered the cat towards where the rider was looking. The AI
goal ran at the highest possible priority, so it overrode the player every tick
and the reins felt dead. The AI goal is gone; you steer the cat directly.

## 2.3.3 — Things that sit where they should

Three fixes, all found by playing:

- **Outfits swung away from the cat.** Every accessory rotated around its own
  pivot point instead of the body part it belongs to, so the crown flew off to
  the side whenever the cat turned its head. Hats, saddles, capes and backpacks
  were all affected.
- **The tail was stubby.** It had been seated one unit too far into the body,
  hiding half its length. It now meets the body flush.
- **Cats could glide without moving their legs.** The sitting pose could only be
  left when the sit flag cleared. Movement now always breaks it.

## 2.3.2 — Readable button prompts

Standing next to a cat, or riding one, showed a raw translation key instead of a
word. Minecraft builds the dismount prompt from the entity id, and there is no
built-in text behind it for custom creatures. Every prompt the add-on can
produce is now spelled out: *Put on*, *Ride*, *Mount*, *Dismount*.

## 2.3.1 — Snow's ears

Snow is a white cat, so her ears disappeared into the rest of her coat. They are
now grey with a pink inner, clearly separated from the fur.

Includes everything from 2.3.0, where outfits finally became visible on the cat.
