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
